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

    It's vitally important to be able to stop a runaway process. With the `heartbeat`, and with the worker reading the database state before executing, it's easy and fast to disable a job.


Setup
=====

- Install urd `pip install urd`
- Add `urd` to `INSTALLED_APPS`
- Run `manage.py migrate`
- Start the scheduler with `manage.py monitor`


Usage
=====

- Define a `tasks.py` module in the app that should have tasks.
- Create a function like this:

.. code-block:: python

    @schedulable_task
    def my_task(heartbeat):
        for foo in bar:
            heartbeat()
            do_some_task()


Calling `heartbeat()` regularly is important to make the task cancellable in a timely manner.

Now define a task in the iommi admin. It will be enabled pretty much as soon as you save.


Administration
==============

Urd ships with integration for the `iommi <https://docs.iommi.rocks>`_ admin.


What does urd mean?
===================

Urd (or Urðr, or Wyrd) is one of the Norns, the goddesses who weave the destiny of gods and humans.
