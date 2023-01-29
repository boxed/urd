import sqlite3
from uuid import UUID

from django.apps import AppConfig


class TestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tests'

    def ready(self):
        sqlite3.register_adapter(UUID, lambda u: str(u))
