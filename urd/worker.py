import contextlib
import sys
import traceback
from logging import getLogger
from time import sleep
from uuid import uuid4

from django.conf import settings
from django.db import (
    connections,
    transaction,
)
from django.utils import timezone
from setproctitle import setproctitle

from urd import (
    get_env,
    INTERVAL_WARNING_THRESHOLD,
    KEEP_LOGS,
    SHUTDOWN_EXIT_CODE,
    ShuttingDown,
)
from urd.models import Task

log = getLogger(__name__)


# NOTE: The raw sql to a different cursor is to make sure that we can log even though the worker task has a transaction

class Logger:
    def __init__(self, task):
        self.log_id = None
        self.task = task
        self.current = ''
        self.connection = connections.create_connection('default')
        self.cursor = self.connection.cursor()
        self._prev_stdout = None

        if self.task and self.task.pk:
            # Purge old logs
            self.cursor.execute('SELECT id from urd_log WHERE task_id = %s ORDER BY id DESC LIMIT 1000 OFFSET %s', (self.task.pk, KEEP_LOGS-1, ))
            ids = ",".join([str(x[0]) for x in self.cursor.fetchall()])
            if ids:
                self.cursor.execute(f'DELETE FROM urd_logitem WHERE log_id in ({ids})')
                self.cursor.execute(f'DELETE FROM urd_log WHERE id in ({ids})')

            self.cursor.execute('INSERT INTO urd_log (execution_time, task_id, run_id) values (%s, %s, %s) RETURNING id', (timezone.now(), self.task.pk, uuid4()))
            self.log_id = self.cursor.fetchone()[0]

    def write(self, value):
        self.current += value
        if self.current.endswith('\n'):
            self.current = self.current[:-1]
            self.flush()
        self._prev_stdout.write(value)

    def close(self):
        self.cursor.close()
        self.connection.close()

    def flush(self):
        if self.task and self.task.pk:
            for line in self.current.split('\n'):
                if line.strip():
                    self.cursor.execute('INSERT INTO urd_logitem (log_id, data) values (%s, %s)', (self.log_id, line))
        self.current = ''

    def __enter__(self):
        self._prev_stdout = sys.stdout
        sys.stdout = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(traceback.format_exc())
        self.flush()
        if self._prev_stdout and sys.stdout is self:
            sys.stdout = self._prev_stdout
        self.cursor.close()
        self.connection.close()

    def __repr__(self):
        return f'<Logger log_id={self.log_id} task={self.task}>'


def worker(task: Task):
    env = get_env()

    # SQLite will fail if you try to write to the database outside the current transaction, if you have one. So for sqlite we have to not use a transaction atomic block.
    atomic = transaction.atomic if 'sqlite' not in settings.DATABASES['default']['ENGINE'] else contextlib.nullcontext
    
    setproctitle(f'{env} worker: {task.name}')
    task.refresh_from_db()

    task.wait_for_previous_shutdown()
    task.start()

    while True:
        try:
            task.heartbeat()
        except ShuttingDown:
            return SHUTDOWN_EXIT_CODE

        time_to_next_execution = task.time_to_next_execution()
        if time_to_next_execution.total_seconds() <= 0:
            with Logger(task):

                # noinspection PyBroadException
                try:
                    count = task.calculate_next_execution_time()
                    assert count > 0
                    if count != 1 and task.interval > INTERVAL_WARNING_THRESHOLD:
                        print('WARNING', f'Missed {count - 1} execution windows')

                    setproctitle(f'{env} worker: {task.name}. Executing since {timezone.now()}')
                    with atomic():
                        task.execute()
                    setproctitle(f'{env} worker: {task.name}')
                except ShuttingDown:
                    return SHUTDOWN_EXIT_CODE
                except Exception as e:
                    msg = str(e) or str(type(e))
                    print('ERROR', msg)
                    # noinspection PyTypeChecker
                    traceback.print_exc(file=sys.stdout)
                    sys.stdout = sys.__stdout__
                    log.exception('Scheduler worker crashed')
                    return SHUTDOWN_EXIT_CODE

        to_sleep = (task.next_execution_time - timezone.now()).total_seconds()
        if to_sleep > 0:
            sleep(to_sleep)
