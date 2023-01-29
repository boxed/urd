import pytest
from django.http import Http404
from iommi import render_if_needed

from tests.helpers import (
    req,
    staff_req,
)
from urd.views import (
    task,
    tasks,
)


def test_list_view():
    with pytest.raises(Http404):
        render_if_needed(request=req('get'), response=tasks(request=req('get'))).content.decode()

    assert 'tests.tasks.test_task' in render_if_needed(request=req('get'), response=tasks(request=staff_req('get'))).content.decode()


@pytest.mark.django_db(transaction=True)
def test_run_view():
    with pytest.raises(Http404):
        render_if_needed(request=req('get'), response=task(request=req('get'), name='tests.tasks.test_task')).content.decode()

    assert 'Run ' in render_if_needed(request=req('get'), response=task(request=staff_req('get'), name='tests.tasks.test_task')).content.decode()

    request = staff_req('post', **{'-submit': ''})
    response = render_if_needed(request=request, response=task(request=request, name='tests.tasks.test_task'))
    result = b''.join([x for x in response.streaming_content]).decode()
    assert result == '<style>html { white-space: pre-wrap; } </style>test task line 1\ntest task line 2\n'
