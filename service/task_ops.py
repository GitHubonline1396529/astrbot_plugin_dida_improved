"""Task CRUD and query operations.

Each function in this module accepts a :class:`DidaClient` as the first
argument and delegates the actual HTTP request to the client layer.
These are the building blocks that :class:`DidaService` composes into
user-facing command handlers.

See Also:
    - :class:`service.service.DidaService` — primary consumer.
"""

from __future__ import annotations

from typing import Any

from ..client import DidaClient
from ..exceptions import DidaValidationError
from ..models import DidaTask


async def create_task(
    client: DidaClient,
    *,
    title: str,
    project_id: str | None = None,
    content: str | None = None,
    priority: int | None = None,
    tags: str | None = None,
    due_date: str | None = None,
) -> DidaTask:
    """Create a new Dida365 task.

    Validates that the title is non-empty, then builds the API payload and
    delegates to :meth:`DidaClient.create_task`.

    Args:
        client: The Dida365 API client.
        title: Task title (required, must not be blank).
        project_id: Target project ID. If omitted the task lands in the inbox.
        content: Optional rich-text content / description.
        priority: Priority level (0=none, 1=low, 3=medium, 5=high).
        tags: Comma-separated tag string, will be split into a list.
        due_date: ISO-8601 due date string (e.g. ``"2026-07-10"`` or
            ``"2026-07-10T15:00:00Z"``).

    Returns:
        The created :class:`DidaTask`.

    Raises:
        DidaValidationError: If the title is empty or whitespace-only.
    """
    if not title.strip():
        raise DidaValidationError("Task title cannot be empty.")

    pid = project_id or ""
    payload: dict[str, Any] = {"title": title.strip()}
    if pid:
        payload["projectId"] = pid
    if content:
        payload["content"] = content
    if priority is not None:
        payload["priority"] = priority
    if due_date:
        payload["dueDate"] = due_date
    if tags:
        payload["tags"] = [t.strip() for t in tags.split(",") if t.strip()]

    return await client.create_task(payload)


async def update_task(
    client: DidaClient,
    task_id: str,
    raw: dict[str, Any],
) -> DidaTask:
    """Update an existing task (full-object replacement).

    .. note::
       The Dida365 API performs a full-object replacement when updating a
        task. Clients should obtain the current task representation via
        :func:`task_to_raw`, merge desired changes, and pass the complete
        dict here. The ``reminders`` field must be stripped beforehand to
        avoid HTTP 500 (see :meth:`DidaService.update_task_details`).

    Args:
        client: The Dida365 API client.
        task_id: ID of the task to update.
        raw: Full task representation dict.

    Returns:
        The updated :class:`DidaTask`.
    """
    return await client.update_task(task_id, raw)


async def complete_task(
    client: DidaClient,
    project_id: str,
    task_id: str,
) -> None:
    """Mark a task as completed.

    Args:
        client: The Dida365 API client.
        project_id: Project the task belongs to.
        task_id: ID of the task to complete.
    """
    await client.complete_task(project_id, task_id)


async def delete_task(
    client: DidaClient,
    project_id: str,
    task_id: str,
) -> None:
    """Delete a task permanently.

    Args:
        client: The Dida365 API client.
        project_id: Project the task belongs to.
        task_id: ID of the task to delete.
    """
    await client.delete_task(project_id, task_id)


async def move_task(
    client: DidaClient,
    from_project_id: str,
    to_project_id: str,
    task_id: str,
) -> dict[str, str]:
    """Move a task from one project to another.

    Args:
        client: The Dida365 API client.
        from_project_id: Source project ID.
        to_project_id: Destination project ID.
        task_id: ID of the task to move.

    Returns:
        Dict with ``"id"`` and ``"etag"`` keys from the API response.
    """
    return await client.move_task(from_project_id, to_project_id, task_id)


async def filter_tasks(
    client: DidaClient,
    *,
    project_ids: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    priority: list[int] | None = None,
    tag: list[str] | None = None,
    status: list[int] | None = None,
) -> list[DidaTask]:
    """Query tasks with optional filters.

    All filter parameters are optional; providing none returns all tasks
    accessible to the current user.

    Args:
        client: The Dida365 API client.
        project_ids: Only include tasks from these project IDs.
        start_date: ISO-8601 start date (inclusive).
        end_date: ISO-8601 end date (inclusive).
        priority: Only include tasks with these priority values.
        tag: Only include tasks matching any of these tags.
        status: Only include tasks with these status codes.

    Returns:
        List of matching :class:`DidaTask`.
    """
    return await client.filter_tasks(
        project_ids=project_ids,
        start_date=start_date,
        end_date=end_date,
        priority=priority,
        tag=tag,
        status=status,
    )


async def list_completed_tasks(
    client: DidaClient,
    *,
    project_ids: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[DidaTask]:
    """List completed tasks, optionally filtered by project and date range.

    Args:
        client: The Dida365 API client.
        project_ids: Only include tasks from these project IDs.
        start_date: ISO-8601 start date (inclusive).
        end_date: ISO-8601 end date (inclusive).

    Returns:
        List of completed :class:`DidaTask` instances.
    """
    return await client.list_completed_tasks(
        project_ids=project_ids,
        start_date=start_date,
        end_date=end_date,
    )


async def get_task_by_id(
    client: DidaClient,
    project_id: str,
    task_id: str,
) -> DidaTask:
    """Fetch a single task by its project ID and task ID.

    Args:
        client: The Dida365 API client.
        project_id: Project the task belongs to.
        task_id: ID of the task to fetch.

    Returns:
        The :class:`DidaTask` instance.
    """
    return await client.get_task(project_id, task_id)
