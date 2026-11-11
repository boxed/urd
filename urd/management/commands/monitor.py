import gc
import signal
from time import sleep

from django.core.management.base import BaseCommand
from django.db import (
    close_old_connections,
    connections,
)
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

        # Workers are forked from this process, so import everything they need once, here, and
        # freeze it: the workers then share these pages instead of each importing the project
        # anew. Without the freeze, the workers' garbage collectors write to every inherited
        # object, and the pages are unshared.
        get_tasks()
        gc.collect()
        gc.freeze()

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
