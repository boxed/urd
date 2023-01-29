import sys
import traceback
from datetime import timedelta
from importlib import import_module
from queue import (
    Empty,
    Queue,
)
from threading import Thread

from django.http.response import StreamingHttpResponse
from django.utils.html import escape


class Printer:
    def __init__(self):
        self.queue = Queue()
        self._prev_stdout = None

    def write(self, value):
        self.queue.put(value)
        self._prev_stdout.write(value)

    def flush(self):
        self._prev_stdout.flush()

    def __enter__(self):
        self._prev_stdout = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(traceback.format_exc())
        self.flush()
        if self._prev_stdout and sys.stdout is self:
            sys.stdout = self._prev_stdout


class Streamer:
    def __init__(self, name, *args, **kwargs):
        module_name, _, function_name = name.rpartition('.')
        module = import_module(module_name)
        function = getattr(module, function_name)
        assert function._is_task
        from urd.worker import Logger
        from urd.models import Task
        t, _ = Task.objects.get_or_create(function=name, defaults=dict(disabled=True, interval=timedelta(days=9999)))

        def run():
            try:
                with Logger(t):
                    function(*args, **kwargs)
            finally:
                self.done = True
        self.done = False
        self.thread = Thread(target=run)

    def start(self):
        with Printer() as printer:
            self.thread.start()
            yield '<style>html { white-space: pre-wrap; } </style>'
            while not self.done:

                try:
                    yield escape(printer.queue.get_nowait())
                except Empty:
                    pass


def stream_stdout(name, *args, **kwargs):
    streamer = Streamer(name, *args, **kwargs)
    return StreamingHttpResponse(streamer.start())
