Urd
---

Urd is a scheduler for Django projects. Some features:

- schedule < 1m time slots
- single concurrent execution [#single]_
- fast enable/disable [#fastdisable]_
- simple deployment
- no extra dependencies beyond Django

.. [#single]

    If tasks take longer to execute than the time to the next execution slot, you get a warning on the next execution. But not simultaneous execution or wild buildup of queues. There is no queue.

.. [#fastdisable]

    It's vitally important to be able to stop a runaway process. With the ``heartbeat``, and with the worker reading the database state before executing, it's easy and fast to disable a job.


Setup
=====

- Install urd ``pip install urd``
- Add ``urd`` to ``INSTALLED_APPS``
- Run ``manage.py migrate``
- Start the scheduler with ``manage.py monitor``


Usage
=====

- Define a ``tasks.py`` module in the app that should have tasks.
- Create a function like this:

.. code-block:: python

    @schedulable_task
    def my_task(heartbeat):
        for foo in bar:
            heartbeat()
            do_some_task()


Calling ``heartbeat()`` regularly is important to make the task cancellable in a timely manner.

Now define a task in the iommi admin. It will be enabled pretty much as soon as you save.


Administration
==============

Urd ships with integration for the `iommi <https://docs.iommi.rocks>`_ admin.


Why not cron/celery/django-q
============================

- Cron didn't work for me because I need to execute a function more often than once a minute
- Cron also doesn't work for me because if you do once per minute, and the task takes two minutes, you get TWO executing processes of that task for a while. This can be disastrous for a few reasons, and can cause things to spiral out of control.
- Celery/django-q are task queues, not schedulers. They have scheduler components, but they don't have a way to ensure only one process at a time runs a specific task.
- Django-q doesn't allow schedules that execute more often than once per minute
- Django-q caused me a lot of problems where the schedule seemed to put future items in the queue, and I couldn't make it stop trying to execute them.


What does urd mean?
===================

Urd (or Urðr, or Wyrd) is one of the Norns, the goddesses who weave the destiny of gods and humans.
