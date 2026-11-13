import gc
import signal
from time import sleep

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import (
    close_old_connections,
    connections,
)
from django.utils.module_loading import import_string
from setproctitle import setproctitle

from urd import (
    get_env,
    get_tasks,
)
from urd.forked_process import ForkedProcess
from urd.models import Task
from urd.worker import worker


def start_worker(task):
    # The child must open its own database connections, never use the parent's sockets.
    connections.close_all()
    return ForkedProcess(target=lambda: worker(task))


def prepare_for_forking():
    """Workers are forked from the monitor, so import everything they need once, here, and freeze
    it: the workers then share these pages instead of each importing the project anew. Without the
    freeze, the workers' garbage collectors write to every inherited object, and the pages are
    unshared.

    `settings.URD_BEFORE_FORK`, the dotted path of a function, loads what the tasks would
    otherwise load lazily, after the fork, each worker its own copy: libraries a task imports
    inside a function, caches it fills on first use."""
    get_tasks()
    before_fork = getattr(settings, 'URD_BEFORE_FORK', None)
    if before_fork:
        import_string(before_fork)()
    gc.collect()
    gc.freeze()


class Command(BaseCommand):
    help = 'Scheduler monitor. This task will start the workers and make sure they are all running.'

    def handle(self, *args, **options):
        env = get_env().lower()
        print('Monitor started')
        setproctitle(f'{env} monitor')

        running = True

        # noinspection PyUnusedLocal
        def sigterm_handler(signum, frame):
            nonlocal running
            running = False

        signal.signal(signal.SIGTERM, sigterm_handler)

        prepare_for_forking()

        process_by_task = {}

        try:
            while running:
                # Clean out dead processes
                process_by_task = {
                    task: process
                    for task, process in process_by_task.items()
                    if process and process.poll() is None
                }

                # Create processes for all tasks that need it
                current_tasks = {x for x in Task.objects.filter(disabled=False) if env in map(str.strip, x.environment.lower().split(','))}

                for task in current_tasks:
                    if task not in process_by_task and task.time_to_next_execution().total_seconds() < 10:
                        process_by_task[task] = start_worker(task)
                        print('Starting', task)

                # Clean out tasks that have been disabled/deleted, and kill the processes
                for task in list(process_by_task.keys()):
                    if task not in current_tasks:
                        print('Removed', task, process_by_task[task].pid)
                        process_by_task[task].terminate()
                        process_by_task[task] = None

                close_old_connections()
                sleep(0.1)
        except KeyboardInterrupt:
            pass

        print('Shutting down')
        for task, process in process_by_task.items():
            print('Killed', task, process_by_task[task].pid)
            process.terminate()
