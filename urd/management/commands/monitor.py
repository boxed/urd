import signal
import subprocess
import sys
from time import sleep

from django.core.management.base import BaseCommand
from setproctitle import setproctitle

from urd import get_env
from urd.models import Task


class Command(BaseCommand):
    help = 'Scheduler monitor. This task will start the workers and make sure they are all running.'

    def handle(self, *args, **options):
        env = get_env()
        print('Monitor started')
        setproctitle(f'{env} monitor')

        running = True

        # noinspection PyUnusedLocal
        def sigterm_handler(signum, frame):
            nonlocal running
            running = False

        signal.signal(signal.SIGTERM, sigterm_handler)

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
                current_tasks = set(Task.objects.filter(disabled=False, environment=env))
                for task in current_tasks:
                    if task not in process_by_task:
                        process_by_task[task] = subprocess.Popen([sys.executable, 'manage.py', 'worker', str(task.pk)])
                        print('Starting', task)

                # Clean out tasks that have been disabled/deleted, and kill the processes
                for task in list(process_by_task.keys()):
                    if task not in current_tasks:
                        print('Removed', task, process_by_task[task].pid)
                        process_by_task[task].terminate()
                        process_by_task[task] = None

                sleep(0.1)
        except KeyboardInterrupt:
            pass

        print('Shutting down')
        for task, process in process_by_task.items():
            print('Killed', task, process_by_task[task].pid)
            process.terminate()
