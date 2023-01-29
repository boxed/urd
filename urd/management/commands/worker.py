from django.core.management.base import BaseCommand

from urd.models import Task
from urd.worker import worker


class Command(BaseCommand):
    help = 'Worker process for the scheduler'

    def add_arguments(self, parser):
        parser.add_argument('task_pk', type=str)

    def handle(self, *args, **options):
        task = Task.objects.get(pk=options['task_pk'])
        exit(worker(task))
