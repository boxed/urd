import os
import signal
import time

from urd.forked_process import ForkedProcess


def test_the_child_exits_with_the_code_its_target_returns():
    assert ForkedProcess(target=lambda: 7).wait() == 7


def test_a_target_that_returns_something_other_than_an_int_exits_with_0():
    assert ForkedProcess(target=lambda: None).wait() == 0


def test_a_target_that_raises_exits_with_1(capfd):
    def target():
        raise ValueError('boom')

    assert ForkedProcess(target=target).wait() == 1
    assert 'ValueError: boom' in capfd.readouterr().err


def test_the_target_runs_in_another_process(tmp_path):
    pid_file = tmp_path / 'pid'

    def target():
        pid_file.write_text(str(os.getpid()))

    forked_process = ForkedProcess(target=target)
    assert forked_process.wait() == 0
    assert int(pid_file.read_text()) == forked_process.pid != os.getpid()


def test_poll_is_none_while_the_child_runs_and_terminate_stops_it():
    forked_process = ForkedProcess(target=lambda: time.sleep(60))
    assert forked_process.poll() is None

    forked_process.terminate()

    assert forked_process.wait() == -signal.SIGTERM
    assert forked_process.poll() == -signal.SIGTERM


def test_the_child_does_not_inherit_the_parents_sigterm_handler():
    called_in_parent = []
    previous_handler = signal.signal(signal.SIGTERM, lambda signum, frame: called_in_parent.append(signum))
    try:
        forked_process = ForkedProcess(target=lambda: time.sleep(60))
        forked_process.terminate()
        assert forked_process.wait() == -signal.SIGTERM
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
    assert called_in_parent == []
