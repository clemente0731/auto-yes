"""Cross-platform PTY proxy runner.

Spawns a child process inside a pseudo-terminal, transparently forwards I/O
between the user's real terminal and the child, and injects auto-responses
whenever the output matches a known prompt pattern.

Unix  : built-in ``pty`` + ``select`` (zero external deps)
Windows: optional ``pywinpty`` -> fallback to subprocess pipes + threading
"""

import contextlib
import errno
import os
import signal
import sys
import time

from auto_yes.detector import PromptDetector

_BUFFER_LIMIT = 8192
_BUFFER_TRIM = 4096


class Runner:
    """PTY proxy that intercepts prompts and auto-responds."""

    def __init__(
        self,
        response="y",
        cooldown=0.5,
        verbose=False,
        categories=None,
        extra_patterns=None,
    ):
        self.response = response
        self.cooldown = cooldown
        self.verbose = verbose
        self.detector = PromptDetector(
            categories=categories,
            extra_patterns=extra_patterns,
        )
        self._last_response_time = 0.0

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def run_command(self, command):
        """Run *command* (list or str) with auto-yes.  Returns exit code."""
        if sys.platform == "win32":
            return self._run_windows(command)
        return self._run_unix(command)

    def run_shell(self):
        """Launch an interactive shell session with auto-yes.  Returns exit code."""
        if sys.platform == "win32":
            shell = os.environ.get("COMSPEC", "cmd.exe")
            return self._run_windows([shell])

        shell = os.environ.get("SHELL", "/bin/sh")
        return self._run_unix([shell])

    # ==================================================================
    # Unix implementation
    # ==================================================================

    def _run_unix(self, command):
        import fcntl
        import pty
        import select
        import termios
        import tty

        env = os.environ.copy()
        env["AUTO_YES_ACTIVE"] = "1"

        stdin_fd = sys.stdin.fileno()
        stdout_fd = sys.stdout.fileno()

        stdin_is_tty = os.isatty(stdin_fd)
        old_tty_attrs = None
        if stdin_is_tty:
            old_tty_attrs = termios.tcgetattr(stdin_fd)

        master_fd, slave_fd = pty.openpty()

        # propagate current window size to the child PTY
        if stdin_is_tty:
            try:
                winsz = fcntl.ioctl(stdout_fd, termios.TIOCGWINSZ, b"\x00" * 8)
                fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsz)
            except OSError:
                pass

        pid = os.fork()

        if pid == 0:
            # ---- child process ----
            os.close(master_fd)
            os.setsid()
            fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)

            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            if slave_fd > 2:
                os.close(slave_fd)

            if isinstance(command, (list, tuple)):
                os.execvpe(command[0], command, env)
            else:
                os.execvpe("/bin/sh", ["/bin/sh", "-c", command], env)
            # unreachable

        # ---- parent process ----
        os.close(slave_fd)

        # forward SIGWINCH so the child PTY tracks terminal resizes
        prev_winch = signal.getsignal(signal.SIGWINCH)

        def _on_winch(_sig, _frame):
            try:
                ws = fcntl.ioctl(stdout_fd, termios.TIOCGWINSZ, b"\x00" * 8)
                fcntl.ioctl(master_fd, termios.TIOCSWINSZ, ws)
                os.kill(pid, signal.SIGWINCH)
            except (OSError, ProcessLookupError):
                pass

        signal.signal(signal.SIGWINCH, _on_winch)

        if stdin_is_tty:
            tty.setraw(stdin_fd)

        output_buf = b""
        exit_code = 0

        try:
            while True:
                watch_fds = [master_fd]
                if stdin_is_tty:
                    watch_fds.append(stdin_fd)

                try:
                    readable, _, _ = select.select(watch_fds, [], [], 0.05)
                except (OSError, InterruptedError):
                    continue

                # ---- user input -> child ----
                if stdin_fd in readable:
                    try:
                        data = os.read(stdin_fd, 4096)
                        if not data:
                            break
                        os.write(master_fd, data)
                    except OSError:
                        break

                # ---- child output -> user (with interception) ----
                if master_fd in readable:
                    try:
                        data = os.read(master_fd, 4096)
                        if not data:
                            break
                    except OSError as exc:
                        if exc.errno == errno.EIO:
                            break
                        raise

                    os.write(stdout_fd, data)

                    output_buf += data
                    if len(output_buf) > _BUFFER_LIMIT:
                        output_buf = output_buf[-_BUFFER_TRIM:]

                # re-check the buffer on every iteration (including timeouts)
                # so a prompt that arrived during cooldown is not missed
                if output_buf:
                    responded = self._maybe_respond_unix(output_buf, master_fd, stdout_fd)
                    if responded:
                        output_buf = b""

                # ---- check child status (non-blocking) ----
                exit_code = self._reap_child(pid)
                if exit_code is not None:
                    self._drain_pty(master_fd, stdout_fd)
                    break

            # if loop exited without reaping, wait for child
            if exit_code is None:
                exit_code = self._wait_child(pid)

        finally:
            if old_tty_attrs is not None:
                termios.tcsetattr(stdin_fd, termios.TCSAFLUSH, old_tty_attrs)
            signal.signal(signal.SIGWINCH, prev_winch)
            with contextlib.suppress(OSError):
                os.close(master_fd)

        return exit_code

    # ------------------------------------------------------------------

    def _maybe_respond_unix(self, buf, master_fd, stdout_fd):
        """Check *buf* for a prompt.  If found, write the response to *master_fd*.

        Returns ``True`` when a response was sent.
        """
        now = time.time()
        if (now - self._last_response_time) < self.cooldown:
            return False

        text = buf.decode("utf-8", errors="replace")
        result = self.detector.detect(text)
        if result is None:
            return False

        response = result.suggested_response
        if response is None:
            response = self.response

        try:
            os.write(master_fd, (response + "\n").encode())
        except OSError:
            return False

        self._last_response_time = time.time()

        if self.verbose:
            msg = (
                f"\r\n\x1b[33m[auto-yes] responded '{response}'"
                f" (matched: {result.pattern})\x1b[0m\r\n"
            )
            with contextlib.suppress(OSError):
                os.write(stdout_fd, msg.encode())

        return True

    # ------------------------------------------------------------------

    @staticmethod
    def _reap_child(pid):
        """Non-blocking waitpid.  Returns exit code or ``None``."""
        try:
            wpid, wstatus = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            return 0

        if wpid == 0:
            return None

        if os.WIFEXITED(wstatus):
            return os.WEXITSTATUS(wstatus)
        if os.WIFSIGNALED(wstatus):
            return 128 + os.WTERMSIG(wstatus)
        return 1

    @staticmethod
    def _wait_child(pid):
        """Blocking waitpid.  Returns exit code."""
        try:
            _, wstatus = os.waitpid(pid, 0)
        except ChildProcessError:
            return 0
        if os.WIFEXITED(wstatus):
            return os.WEXITSTATUS(wstatus)
        if os.WIFSIGNALED(wstatus):
            return 128 + os.WTERMSIG(wstatus)
        return 1

    @staticmethod
    def _drain_pty(master_fd, stdout_fd):
        """Flush any remaining bytes in the master PTY buffer."""
        import select as _sel

        try:
            while True:
                rlist, _, _ = _sel.select([master_fd], [], [], 0.1)
                if not rlist:
                    break
                data = os.read(master_fd, 4096)
                if not data:
                    break
                os.write(stdout_fd, data)
        except OSError:
            pass

    # ==================================================================
    # Windows implementation
    # ==================================================================

    def _run_windows(self, command):
        """Try ``pywinpty`` first; fall back to subprocess + pipes."""
        try:
            return self._run_windows_pty(command)
        except ImportError:
            return self._run_windows_pipe(command)

    def _run_windows_pty(self, command):
        """Windows PTY implementation via *pywinpty*."""
        from winpty import PtyProcess  # type: ignore[import-untyped]

        env = os.environ.copy()
        env["AUTO_YES_ACTIVE"] = "1"

        if isinstance(command, (list, tuple)):
            cmd_str = " ".join(command)
        else:
            cmd_str = command

        proc = PtyProcess.spawn(cmd_str, env=env)

        output_buf = b""
        try:
            while proc.isalive():
                try:
                    data = proc.read(4096)
                except EOFError:
                    break
                if not data:
                    continue

                raw = data.encode("utf-8") if isinstance(data, str) else data
                sys.stdout.buffer.write(raw)
                sys.stdout.buffer.flush()

                output_buf += raw
                if len(output_buf) > _BUFFER_LIMIT:
                    output_buf = output_buf[-_BUFFER_TRIM:]

                responded = self._maybe_respond_winpty(output_buf, proc)
                if responded:
                    output_buf = b""
        finally:
            if proc.isalive():
                proc.terminate()

        return proc.exitstatus or 0

    def _maybe_respond_winpty(self, buf, proc):
        now = time.time()
        if (now - self._last_response_time) < self.cooldown:
            return False

        text = buf.decode("utf-8", errors="replace")
        result = self.detector.detect(text)
        if result is None:
            return False

        response = result.suggested_response
        if response is None:
            response = self.response

        try:
            proc.write(response + "\n")
        except Exception:
            return False

        self._last_response_time = time.time()

        if self.verbose:
            msg = f"[auto-yes] responded '{response}'\n"
            sys.stderr.write(msg)

        return True

    def _run_windows_pipe(self, command):
        """Minimal fallback using ``subprocess`` + threads (no PTY)."""
        import subprocess
        import threading

        env = os.environ.copy()
        env["AUTO_YES_ACTIVE"] = "1"

        use_shell = isinstance(command, str)
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            shell=use_shell,
        )

        output_buf = bytearray()
        lock = threading.Lock()

        def _reader():
            assert proc.stdout is not None
            while True:
                byte = proc.stdout.read(1)
                if not byte:
                    break
                sys.stdout.buffer.write(byte)
                sys.stdout.buffer.flush()

                with lock:
                    output_buf.extend(byte)
                    if len(output_buf) > _BUFFER_LIMIT:
                        del output_buf[: len(output_buf) - _BUFFER_TRIM]

                    now = time.time()
                    if (now - self._last_response_time) >= self.cooldown:
                        text = output_buf.decode("utf-8", errors="replace")
                        result = self.detector.detect(text)
                        if result is not None:
                            resp = result.suggested_response
                            if resp is None:
                                resp = self.response
                            try:
                                assert proc.stdin is not None
                                proc.stdin.write((resp + "\n").encode())
                                proc.stdin.flush()
                            except (OSError, BrokenPipeError):
                                pass
                            self._last_response_time = time.time()
                            output_buf.clear()

        reader_thread = threading.Thread(target=_reader, daemon=True)
        reader_thread.start()
        proc.wait()
        reader_thread.join(timeout=2)

        return proc.returncode or 0
