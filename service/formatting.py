"""Task display formatting utilities.

Converts :class:`DidaTask` fields into human-readable strings suitable
for AstrBot plain-text replies.

See Also:
    - :func:`service.service.DidaService.list_today_tasks_summary`
    - :func:`service.service.DidaService.list_unfinished_tasks_summary`
"""

from __future__ import annotations

from ..models import DidaTask, DidaTaskWithProject
from ._helpers import effective_due_datetime, is_overdue


def format_due(task: DidaTask, *, timezone: str) -> str:
    """Format a task's due date as a human-readable string.

    All-day tasks are displayed as ``YYYY-MM-DD`` only; timed tasks include
    hour and minute. Tasks without a due date return ``"(No due date)"``.

    Args:
        task: The task to format.
        timezone: IANA timezone name used for datetime resolution.

    Returns:
        Formatted due date string.
    """
    dt = effective_due_datetime(task, timezone=timezone)
    if not dt:
        return "(No due date)"
    if task.is_all_day:
        return dt.date().isoformat()
    return dt.strftime("%Y-%m-%d %H:%M")


def format_priority(task: DidaTask) -> str:
    """Format the task's priority as a human-readable label.

    The Dida365 API uses integer codes: ``0`` (none), ``1`` (low),
    ``3`` (medium), ``5`` (high). ``None`` maps to ``"(unknown)"``.

    Args:
        task: The task whose priority to format.

    Returns:
        Priority label string.
    """
    mapping = {
        None: "(unknown)",
        0: "none",
        1: "low",
        3: "medium",
        5: "high",
    }
    return mapping.get(task.priority, str(task.priority))


def format_status(task: DidaTask) -> str:
    """Format the task's status as a human-readable string.

    Args:
        task: The task whose status to format.

    Returns:
        ``"completed"`` if the task has a ``completed_time`` or status code 2,
        otherwise ``"open"``.
    """
    if task.completed_time or task.status == 2:
        return "completed"
    return "open"


def format_single_task(
    item: DidaTaskWithProject,
    *,
    timezone: str,
    include_overdue: bool = False,
    index: int | None = None,
) -> str:
    """Format a single task as a multi-line summary string.

    The output includes the task ID, title, project name, due date, and
    priority. Optionally prepends a numeric index and appends an overdue flag.

    Args:
        item: The task-with-project item to format.
        timezone: IANA timezone name.
        include_overdue: Whether to append an overdue indicator line.
        index: Optional 1-based index prepended to the first line.

    Returns:
        Multi-line formatted string.
    """
    prefix = f"{index}. " if index else ""
    parts = [
        f"{prefix}[{item.task.id}] {item.task.title}",
        f"   Project: {item.project_name}",
        f"   Due: {format_due(item.task, timezone=timezone)}",
        f"   Priority: {format_priority(item.task)}",
    ]
    if include_overdue:
        overdue_flag = (
            "Yes" if is_overdue(item.task, timezone=timezone) else "No"
        )
        parts.append(f"   Overdue: {overdue_flag}")
    return "\n".join(parts)
