from urd import schedulable_task


@schedulable_task
def test_task():
    print('test task line 1')
    print('test task line 2')
