Changelog
=========

1.5.1 (2026-11-13)
~~~~~~~~~~~~~~~~~~

* Fixed: a worker never shut down after a run to wait for its next one, as it decided by the time to the next run from before the run, when that run was due. It slept until the next run instead, so every task that had run once kept its worker, and the memory the run left it with, for good.

1.5.0 (2026-11-13)
~~~~~~~~~~~~~~~~~~

* New setting ``URD_BEFORE_FORK``: the dotted path of a function the monitor calls before it freezes and forks its workers, to load what the tasks would otherwise each load after the fork.

1.4.0 (2026-11-11)
~~~~~~~~~~~~~~~~~~

* The monitor now forks its workers instead of starting a new interpreter for each. Workers share the monitor's imported modules copy-on-write (the monitor imports every app's ``tasks`` module and calls ``gc.freeze()`` before forking), so a worker no longer pays the memory and startup time of importing the whole project. On a large project this took a worker from about 280 MB to a few MB of private memory, and removed several seconds of startup.

* The monitor must stay single-threaded, as forking a process with threads is unsafe. Python warns when that happens.

1.3.2 (2026-03-27)
~~~~~~~~~~~~~~~~~~

Interval changes are now picked up by running workers without requiring a restart

1.3.1 (2026-03-21)
~~~~~~~~~~~~~~~~~~

Close connections when waiting for next execution slot

1.3.0 (2023-11-21)
~~~~~~~~~~~~~~~~~~

* You can now specify multiple environments to run a task in with a comma separated list in the environment field

1.2.4 (2023-11-06)
~~~~~~~~~~~~~~~~~~

* `function` on `Task` should not be unique, as that prevents your from scheduling a specific job on more than one environment.

1.2.3 (2023-10-24)
~~~~~~~~~~~~~~~~~~

* heartbeat warning is still printed incorrectly :(


1.2.2 (2023-10-24)
~~~~~~~~~~~~~~~~~~

* heartbeat warning is printed incorrectly

1.2.1 (2023-10-24)
~~~~~~~~~~~~~~~~~~

* heartbeat logging warning improved to give the name of the task

1.2.0 (2023-10-16)
~~~~~~~~~~~~~~~~~~

* `@schedulable_task` now takes an optional keyword argument `use_transaction` that you can use to turn off the default transaction around a task. This is useful for tasks that work with a queue where each items should be handled by a transaction.

1.1.0 (2023-10-14)
~~~~~~~~~~~~~~~~~~

* Workers shut down if they have > 20s to next execution slot, and start up if there is < 10s to their next execution slot. This can save a lot of memory for task that don't run very often.


1.0.4 (2023-09-13)
~~~~~~~~~~~~~~~~~~

* Fixed ordering of `LogItem` by default. This will fix the ordering in the iommi admin.


1.0.3 (2023-01-28)
~~~~~~~~~~~~~~~~~~

- Cut length of name+function columns for mysql users (fixes #1)


1.0.2 (2023-01-28)
~~~~~~~~~~~~~~~~~~

- Added missing `@scheduled_task`
- Fixed iommi admin config
- Fixed bug where very rarely the last log message wasn't properly forwarded to the run view (it was still logged to the DB though)


1.0.1 (2023-01-28)
~~~~~~~~~~~~~~~~~~

- Fixed README on pypi


1.0.0 (2023-01-28)
~~~~~~~~~~~~~~~~~~

- Initial release
