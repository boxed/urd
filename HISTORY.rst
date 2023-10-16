Changelog
=========

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
