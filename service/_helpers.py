"""Low-level helper predicates and serialization utilities.

This module provides pure functions that operate on `DidaTask` objects.
None of these functions perform I/O; they are used by the service layer to
query task state (completed, overdue, due-today) and to build sort keys and
serialization dicts.

See Also:
    - `DidaService` — primary consumer of these helpers.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from ..models import DidaTask
from ..time_utils import (
    parse_api_datetime,
    today_in_timezone,
)


def is_completed(task: DidaTask) -> bool:
    """Check whether a task has been completed.

    Note:
        `status` is the **only reliable source** for completion state.
        `completed_time` may retain a stale timestamp when a task is
        **reopened** (uncompleted) -- in that case `status` is reset to `0` but
        `completed_time` remains non-empty.  Never rely on `completed_time`
        alone.

    Priority:
        1. If `status` is not `None`: `status in (1, 2)` means completed.
        2. If `status` is `None` (unlikely): fall back to `completed_time`.

    Values:
        - `status=0` = not completed
        - `status=1` = completed (used by some endpoints e.g. inbox)
        - `status=2` = completed (standard Open API value)

    Args:
        task: The task to check.

    Returns:
        `True` if the task is completed, `False` otherwise.
    """
    if task.status is not None:
        return task.status in (1, 2)
    # Fallback: status is None (unlikely), use completed_time as hint.
    return bool(task.completed_time)


def parse_datetime(
    value: str,
    *,
    task: DidaTask | None = None,
    timezone: str,
) -> datetime | None:
    """Parse an API datetime string, respecting the task's timezone.

    If the task has an explicit `time_zone` field it is used as the assumed
    source timezone; otherwise the caller-provided `timezone` is used. The
    result is converted to the target `timezone`.

    Args:
        value: ISO-8601 datetime string from the API.
        task: Optional task whose `time_zone` field may override the assumed
            source timezone.
        timezone: IANA timezone name for the target conversion.

    Returns:
        A timezone-aware `datetime.datetime`, or `None` if the
        value could not be parsed.
    """
    assume_tz = task.time_zone if task and task.time_zone else timezone
    return parse_api_datetime(
        value,
        assume_timezone_name=assume_tz,
        target_timezone_name=timezone,
    )


def effective_due_datetime(
    task: DidaTask,
    *,
    timezone: str,
) -> datetime | None:
    """Get the effective due datetime for a task.

    For all-day tasks the API stores the end date as `due_date`; this function
    subtracts one day so that date comparisons (due-today, overdue) behave
    intuitively. For timed tasks the raw `due_date` is returned.

    Args:
        task: The task to evaluate.
        timezone: IANA timezone name.

    Returns:
        A timezone-aware `datetime.datetime`, or `None` if the task has no due
        date.
    """
    if task.is_all_day:
        # All-day tasks store the end date as due_date.
        # Subtracting 1 day yields the effective "due at end of day" so that
        # date comparisons (e.g. is_task_due_today) behave intuitively.
        start_dt = parse_datetime(task.start_date, task=task, timezone=timezone)
        if start_dt:
            return start_dt
        due_dt = parse_datetime(task.due_date, task=task, timezone=timezone)
        if due_dt:
            return due_dt - timedelta(days=1)
        return None
    return parse_datetime(task.due_date, task=task, timezone=timezone)


def is_task_due_today(
    task: DidaTask,
    *,
    today: date,
    timezone: str,
) -> bool:
    """Check whether a task's effective due date falls on `today`.

    Args:
        task: The task to check.
        today: Reference date (obtained via `today_in_timezone`).
        timezone: IANA timezone name.

    Returns:
        `True` if the task's effective due date matches `today`.
    """
    dt = effective_due_datetime(task, timezone=timezone)
    if not dt:
        return False
    return dt.date() == today


def is_overdue(
    task: DidaTask,
    *,
    today: date | None = None,
    timezone: str,
) -> bool:
    """Check whether a task is overdue.

    Completed tasks are never considered overdue. A task without a due date is
    also not overdue.

    Args:
        task: The task to check.
        today: Reference date. Defaults to `today_in_timezone`.
        timezone: IANA timezone name.

    Returns:
        `True` if the task is not completed and its effective due date is 
        before `today`.
    """
    if is_completed(task):
        return False
    dt = effective_due_datetime(task, timezone=timezone)
    if not dt:
        return False
    ref = today or today_in_timezone(timezone)
    return dt.date() < ref


def sort_due_value(
    task: DidaTask,
    *,
    timezone: str,
) -> tuple[int, str]:
    """Get a sort key tuple for due-date ordering.

    Tasks with a due date sort before those without. Among tasks with a due 
    date, ordering is by ISO datetime.

    Args:
        task: The task to evaluate.
        timezone: IANA timezone name.

    Returns:
        Tuple `(0, isoformat)` if the task has a due date, or `(1, "")` if it
        does not.
    """
    # Sort key tuple: (has_due, iso_datetime).
    # (0, isoformat) sorts before (1, "") — tasks with a due date come first.
    dt = effective_due_datetime(task, timezone=timezone)
    if not dt:
        return (1, "")
    return (0, dt.isoformat())


def unfinished_sort_key(
    task: DidaTask,
    *,
    today: date,
    timezone: str,
) -> int:
    """Get a sort priority integer for unfinished task ordering.

    Args:
        task: The task to evaluate.
        today: Reference date.
        timezone: IANA timezone name.

    Returns:
        `0` if overdue (sorts highest), `1` if it has a due date, `2` if it has
        no due date (sorts lowest).
    """
    # Sort priority: 0 = overdue (top), 1 = has due date (middle),
    # 2 = no due date (bottom).
    if is_overdue(task, today=today, timezone=timezone):
        return 0
    if effective_due_datetime(task, timezone=timezone):
        return 1
    return 2


def task_to_raw(task: DidaTask) -> dict[str, Any]:
    """Serialize a `DidaTask` to the raw dict format expected by the API.

    Only non-None / non-empty optional fields are included in the output,
    matching the API's partial-update expectations.

    Note:
        The `reminders` field is intentionally omitted (see
        `DidaService.update_task_details`).

    Args:
        task: The task to serialize.

    Returns:
        Dict suitable for passing to the Dida365 API update endpoint.
    """
    raw: dict[str, Any] = {
        "id": task.id,
        "projectId": task.project_id,
        "title": task.title,
        "content": task.content,
    }
    if task.status is not None:
        raw["status"] = task.status
    if task.priority is not None:
        raw["priority"] = task.priority
    if task.due_date:
        raw["dueDate"] = task.due_date
    if task.start_date:
        raw["startDate"] = task.start_date
    if task.completed_time:
        raw["completedTime"] = task.completed_time
    raw["isAllDay"] = task.is_all_day
    if task.time_zone:
        raw["timeZone"] = task.time_zone
    if task.tags:
        raw["tags"] = list(task.tags)
    raw["sortOrder"] = task.sort_order
    return raw
