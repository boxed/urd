import os
from datetime import timedelta
from unittest import mock
from uuid import uuid4

import pytest
import time_machine
from django.utils import timezone
from django.utils.timezone import now

import urd
from urd import (
    KEEP_LOGS,
    SHUTDOWN_EXIT_CODE,
    SHUTDOWN_TIMEOUT,
    ShuttingDown,
)
from urd.models import (
    Log,
    Task,
)
from urd.worker import worker

pytestmark = pytest.mark.django_db(transaction=True)

counter = 0


@pytest.fixture(autouse=True)
def warp_sleeps():
    with mock.patch.object(urd.models, "sleep", new=lambda seconds: None):
        yield


def function_to_run_basic(heartbeat):
    global counter
    print('should show up in log', counter)
    counter += 1
    heartbeat()

    if counter > KEEP_LOGS + 2:
        raise ShuttingDown()


def test_basic():
    global counter
    counter = 0

    unrelated = Task.objects.create(
        name='test',
        function='unrelated',
        interval=timedelta(seconds=0.001),
        disabled=True,
    )

    for x in range(5):
        Log.objects.create(task=unrelated, execution_time=now(), run_id=uuid4())

    task = Task.objects.create(
        name='test',
        function='urd.worker__tests.function_to_run_basic',
        interval=timedelta(seconds=0.001),
    )

    for x in range(5):
        Log.objects.create(task=unrelated, execution_time=now(), run_id=uuid4())

    old_count = Log.objects.exclude(task=task).count()

    assert worker(task) == SHUTDOWN_EXIT_CODE

    assert Log.objects.filter(task=task).count() == KEEP_LOGS

    # Make sure tasks only clean up their own logs
    assert old_count == Log.objects.exclude(task=task).count()

    for i, log in enumerate(task.logs.all(), start=counter - KEEP_LOGS):
        assert [x.data for x in log.items.all()] == [f'should show up in log {i}']


def function_to_run_crash(heartbeat):
    heartbeat()
    print('should show up in log')
    raise Exception('exception')


def test_worker_crash():
    task = Task.objects.create(
        name='test',
        function='urd.worker__tests.function_to_run_crash',
        interval=timedelta(seconds=0.001),
    )

    assert worker(task) == SHUTDOWN_EXIT_CODE

    assert Log.objects.count() == 1

    logs = [x.data for x in task.logs.get().items.all()]
    assert logs[:2] == [
        'should show up in log',
        'ERROR exception',
    ]
    print(repr(logs))
    assert "    raise Exception('exception')" in logs


def test_calculate_next_execution_time():
    with time_machine.travel('2001-01-01 01:02:03', tick=False) as traveller:
        t = Task.objects.create(
            next_execution_time=timezone.now(),
            interval=timedelta(days=1),
        )
        t.calculate_next_execution_time()

        assert t.time_to_next_execution() == timedelta(days=1)

        traveller.shift(timedelta(days=6))

        assert t.calculate_next_execution_time() == 6


def test_error_on_invalid_function_name():
    with pytest.raises(ShuttingDown) as e:
        t = Task(
            function='does_not_exist.function',
        )
        t.execute()

    assert str(e.value) == 'Failed to execute function'


def test_shut_down_on_none_pid():
    with pytest.raises(ShuttingDown) as e:
        t = Task.objects.create(
            function='urd.worker__tests.function_to_run_basic',
            interval=timedelta(seconds=1),
        )
        t.check_lock()

    assert str(e.value) == 'PID changed'


def test_shut_down_command():
    with pytest.raises(ShuttingDown) as e:
        t = Task.objects.create(
            function='urd.worker__tests.function_to_run_basic',
            pid=os.getpid(),
            shutdown_command=timezone.now(),
            interval=timedelta(seconds=1),
        )
        t.check_lock()

    assert str(e.value) == 'Got shutdown command'


def test_wait_for_previous_shutdown_timeout(capsys):
    t = Task.objects.create(
        next_execution_time=timezone.now(),
        interval=timedelta(days=1),
        pid=123,
        shutdown_command=timezone.now() - SHUTDOWN_TIMEOUT + timedelta(seconds=0.1),
    )
    t.calculate_next_execution_time()

    t.wait_for_previous_shutdown()

    assert capsys.readouterr().out == 'Shutdown timeout hit\n'
