from django.http import StreamingHttpResponse
from django.utils.translation import gettext
from iommi import (
    Action,
    Form,
    Table,
)

from urd import get_tasks
from urd.stream_stdout import stream_stdout


def tasks(request):
    assert request.user.is_superuser

    return Table(
        title=gettext('Run tasks'),
        rows=get_tasks(),
        page_size=None,
        columns=dict(
            app_name=dict(
                auto_rowspan=True,
            ),
            name__cell__url=lambda row, **_: f'{row.function}/'
        ),
    )


def task(request, name):
    assert request.user.is_superuser

    def run_task(**_):
        return StreamingHttpResponse(stream_stdout(name))

    return Form(
        title=gettext('Run {}?').format(name),
        attrs__class__disable_boost=True,
        actions__submit=Action.primary(
            display_name=gettext('Run'),
            post_handler=run_task,
        ),
    )
