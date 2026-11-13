import gc

import pytest
from django.test import override_settings

from urd.management.commands.monitor import prepare_for_forking

loaded_before_fork = []


def load_before_fork():
    loaded_before_fork.append(gc.get_freeze_count())


@pytest.fixture(autouse=True)
def unfreeze():
    gc.unfreeze()
    loaded_before_fork.clear()
    yield
    gc.unfreeze()


def test_before_fork_runs_before_the_freeze():
    with override_settings(URD_BEFORE_FORK='urd.monitor__tests.load_before_fork'):
        prepare_for_forking()

    assert loaded_before_fork == [0]
    assert gc.get_freeze_count() > 0


def test_no_before_fork_still_freezes():
    prepare_for_forking()

    assert loaded_before_fork == []
    assert gc.get_freeze_count() > 0
