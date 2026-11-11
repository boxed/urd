import os
import signal
import sys
import traceback


class ForkedProcess:
    """Runs `target` in a child forked from this process.

    The child shares the parent's memory copy-on-write, so it starts without importing anything,
    and the parent's already imported modules cost it next to nothing. Call `gc.freeze()` in the
    parent before forking, or the child's garbage collector writes to every inherited object and
    unshares the pages.

    It has the subset of `subprocess.Popen`'s interface the monitor uses: `pid`, `poll()` and
    `terminate()`. The child exits with the int `target` returns, 0 if it returns something else,
    and 1 if it raises.
    """

    def __init__(self, target):
        sys.stdout.flush()
        sys.stderr.flush()
        # A SIGTERM sent to the child before it has dropped the parent's handler would run that
        # handler and leave the child running, so hold SIGTERM until the child has the default.
        previous_signal_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM})
        pid = os.fork()
        if pid == 0:
            exit_code = 1
            try:
                # The parent's handlers are for the parent. A worker is stopped with SIGTERM.
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                signal.pthread_sigmask(signal.SIG_SETMASK, previous_signal_mask)
                result = target()
                exit_code = result if isinstance(result, int) else 0
            except BaseException:
                traceback.print_exc()
            finally:
                sys.stdout.flush()
                sys.stderr.flush()
                # Never return into the parent's code, and skip the parent's atexit handlers.
                os._exit(exit_code)

        signal.pthread_sigmask(signal.SIG_SETMASK, previous_signal_mask)
        self.pid = pid
        self.returncode = None

    def poll(self):
        if self.returncode is None:
            pid, wait_status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                self.returncode = os.waitstatus_to_exitcode(wait_status)
        return self.returncode

    def wait(self):
        if self.returncode is None:
            _, wait_status = os.waitpid(self.pid, 0)
            self.returncode = os.waitstatus_to_exitcode(wait_status)
        return self.returncode

    def terminate(self):
        if self.returncode is None:
            os.kill(self.pid, signal.SIGTERM)
