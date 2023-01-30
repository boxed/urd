import os
from datetime import timedelta
from importlib import import_module
from time import sleep
from uuid import uuid4

from django.db.models import (
    BooleanField,
    CASCADE,
    CharField,
    DateTimeField,
    DurationField,
    ForeignKey,
    IntegerField,
    Model,
    TextField,
    UUIDField,
)
from django.utils import timezone

from urd import (
    SHUTDOWN_TIMEOUT,
    ShuttingDown,
)


class Task(Model):
    name = CharField(max_length=255)
    function = CharField(max_length=255, unique=True)
    pid = IntegerField(null=True)
    shutdown_command = DateTimeField(null=True)
    next_execution_time = DateTimeField(null=True)
    last_checked = DateTimeField(null=True)
    interval = DurationField()
    disabled = BooleanField(default=False)
    current_run_id = UUIDField(null=True)
    environment = CharField(max_length=255)

    def calculate_next_execution_time(self):
        assert self.interval.total_seconds() > 0
        count = 0
        if self.next_execution_time is None:
            self.next_execution_time = timezone.now() + self.interval
            count += 1
        else:
            while timezone.now() >= self.next_execution_time:
                self.next_execution_time = self.next_execution_time + self.interval
                count += 1
            if count:
                self.save(update_fields=['next_execution_time'])
        return count

    def heartbeat(self):
        if self.last_checked is not None and (timezone.now() - self.last_checked) > SHUTDOWN_TIMEOUT:
            print('WARNING', 'heartbeat not called often enough')
        if self.last_checked is None or (timezone.now() - self.last_checked) > timedelta(seconds=1):
            self.check_lock()
            self.last_checked = timezone.now()
            self.save(update_fields=['last_checked'])

    def check_lock(self):
        t = Task.objects.get(pk=self.pk)
        if t.pid != os.getpid() or t.pid is None:
            raise ShuttingDown('PID changed')

        if t.shutdown_command:
            t.pid = None
            t.shutdown_command = None
            t.current_run_id = None
            t.save(update_fields=['pid', 'shutdown_command', 'current_run_id'])
            raise ShuttingDown('Got shutdown command')

    def execute(self):
        if not hasattr(self, '_function'):
            m, _, f = self.function.rpartition('.')
            try:
                self._function = getattr(import_module(m), f)
            except (ImportError, AttributeError) as e:
                print('ERROR', 'Failed to execute function: ', str(e) or str(type(e)))
                sleep(1)
                raise ShuttingDown('Failed to execute function')

        self._function(heartbeat=lambda: self.heartbeat())

    def wait_for_previous_shutdown(self):
        while self.pid is not None and self.shutdown_command is not None and timezone.now() < (self.shutdown_command + SHUTDOWN_TIMEOUT):
            sleep(0.1)
            self.refresh_from_db()
        if self.pid is not None and self.shutdown_command is not None:
            print('Shutdown timeout hit')

    def start(self):
        self.pid = os.getpid()
        self.shutdown_command = None
        self.current_run_id = uuid4()
        self.save(update_fields=['pid', 'shutdown_command', 'current_run_id'])

    def time_to_next_execution(self):
        if self.next_execution_time is None:
            return timedelta()
        return self.next_execution_time - timezone.now()

    def disable(self):
        Task.objects.filter(pk=self.pk).update(disabled=True)

    def enable(self):
        Task.objects.filter(pk=self.pk).update(disabled=False)

    def __str__(self):
        return self.name


class Log(Model):
    execution_time = DateTimeField()
    task = ForeignKey(Task, related_name='logs', on_delete=CASCADE)
    run_id = UUIDField()

    class Meta:
        ordering = ('pk',)

    def __str__(self):
        return f'{self.task.name} - {self.execution_time}'


class LogItem(Model):
    log = ForeignKey(Log, related_name='items', on_delete=CASCADE)
    data = TextField()

    def __str__(self):
        return self.data
