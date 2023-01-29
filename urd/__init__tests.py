from urd import (
    get_tasks,
    Task,
)


def test_get_tasks():
    for t in get_tasks():
        assert isinstance(t, Task)
