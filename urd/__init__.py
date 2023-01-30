from dataclasses import dataclass
from datetime import timedelta
from importlib import import_module

from django.conf import settings

__version__ = '1.0.3'

INTERVAL_WARNING_THRESHOLD = timedelta(seconds=5)
KEEP_LOGS = 10
SHUTDOWN_TIMEOUT = timedelta(seconds=10)
SHUTDOWN_EXIT_CODE = 7


class ShuttingDown(Exception):
    pass


@dataclass
class Task:
    app_name: str
    function: str
    name: str


def get_env():
    return getattr(settings, 'ENV', 'unknown ENV')


def schedulable_task(f):
    f._is_task = True
    return f


def get_tasks():
    from django.apps import apps

    task_list = []
    for app_name, app in apps.app_configs.items():
        try:
            task_module_name = f'{app.module.__name__}.tasks'
            for name, variable in import_module(task_module_name).__dict__.items():
                if not name.startswith('_') and getattr(variable, '_is_task', False):
                    task_list.append(
                        Task(
                            app_name=app_name,
                            function=f'{task_module_name}.{name}',
                            name=name.replace('_', ' ').capitalize(),
                        )
                    )
        except ImportError:
            pass

    return task_list
