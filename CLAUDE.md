# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Urd?

Urd is a Django scheduler for sub-minute-granularity background tasks with guaranteed single concurrent execution. It replaces cron/Celery/django-q when you need tasks running more frequently than once per minute with no duplicate processes.

## Commands

- **Run tests:** `pytest` (or `make test`)
- **Run single test:** `pytest tests/test_monitor.py::test_name -x`
- **Test settings:** `tests.settings` (SQLite in-memory)
- **Tests require:** `pytest.mark.django_db(transaction=True)` for DB access

## Architecture

**Execution model:** A monitor process polls the DB every 0.1s, spawning/killing worker subprocesses as needed. Workers run tasks in a loop, calling `task.heartbeat()` to check for shutdown signals.

- `urd/__init__.py` — `@schedulable_task` decorator, `get_tasks()` discovery, constants
- `urd/models.py` — `Task`, `Log`, `LogItem` models. Task handles scheduling, locking (via PID), and execution
- `urd/worker.py` — Worker loop and `Logger` class (captures stdout to DB via raw SQL on separate connection to avoid transaction conflicts)
- `urd/management/commands/monitor.py` — Parent scheduler process
- `urd/management/commands/worker.py` — Worker subprocess entry point
- `urd/views.py` + `urd/stream_stdout.py` — iommi-based web UI with real-time output streaming
- `urd/iommi_admin.py` — Admin UI configuration

**Task registration:** Functions decorated with `@schedulable_task` in any app's `tasks.py` are discovered by `get_tasks()`.

**Environment filtering:** Monitor filters tasks by `settings.ENV` matching `Task.environment` (supports comma-separated multi-environment).

**Exit codes:** `SHUTDOWN_EXIT_CODE=7` (normal shutdown), `SHUTDOWN_WAIT_FOR_NEXT_EXECUTION_EXIT_CODE=8` (idle shutdown).
