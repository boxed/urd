from gettext import gettext

from iommi import (
    Field,
    MenuItem,
    Table,
)

from urd import get_tasks
from urd.models import LogItem


class Meta:
    apps__urd_task__include = True
    apps__urd_logitem__include = True

    parts__menu__sub_menu = dict(
        tasks=MenuItem(
            after=1,
            display_name=gettext('Tasks'),
            url='/system/tasks/',
            include=lambda request, **_: request.user.is_superuser,
        ),
    )

    parts__list_urd_logitem = dict(
        auto__include=['log__execution_time', 'log__task', 'data'],
        columns=dict(
            edit__include=False,
            delete__include=False,
            select__include=False,
            log_execution_time__auto_rowspan=True
        ),
        bulk__include=False,
        actions__create__include=False,
    )

    parts__edit_urd_task__fields = dict(
        last_checked__include=False,
        shutdown_command__include=False,
        pid__editable=False,

        logs=Table(
            auto__model=LogItem,
            auto__include=['log__execution_time', 'log__task', 'data'],
            rows=lambda instance, **_: LogItem.objects.filter(log__task=instance),
            columns__log_execution_time__auto_rowspan=True,
        )
    )

    parts__list_urd_task = dict(
        columns__disabled__bulk__include=True,
        columns__name__filter=dict(include=True, freetext=True),
        columns__function__filter=dict(include=True, freetext=True),
        columns__disabled__filter__include=True,
    )

    parts__create_urd_task__fields__function = Field.choice(choices=lambda **_: [x.function for x in get_tasks()])
