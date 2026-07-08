from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from typing import Any

from .client import DidaClient
from .exceptions import DidaError, DidaValidationError
from .models import (
    DidaPluginSettings,
    DidaTask,
    DidaTaskWithProject,
)
from .time_utils import (
    get_timezone,
    parse_api_datetime,
    today_in_timezone,
)

_INBOX_PROJECT_ID = "inbox"
_INBOX_PROJECT_NAME = "Inbox"


class DidaService:
    """Application service for Dida365 operations."""

    def __init__(
        self,
        settings: DidaPluginSettings,
        *,
        client: DidaClient | None = None,
    ) -> None:
        """Initialize the DidaService.

        Args:
            settings: Plugin configuration settings.
            client: Optional ``DidaClient`` instance. If not provided,
                a new one is created from the settings.
        """
        self.settings = settings
        self.client = client or DidaClient(settings)

    def build_status_summary(self) -> str:
        """Build a summary of the current plugin status.

        Returns:
            Formatted status string.
        """
        lines = [
            "Dida365 Improved Plugin loaded",
            "- Access token configured:"
            f" {bool(self.settings.access_token.strip())}",
            f"- API base URL: {self.settings.api_base_url}",
            f"- Timezone: {self.settings.timezone}",
            "- Access token expires in ~180 days;"
            " update in plugin config if expired",
        ]
        return "\n".join(lines)

    async def probe_read_access(self) -> str:
        """Probe read access by listing projects.

        Returns:
            Formatted result string.
        """
        projects = await self.client.list_projects()
        if not projects:
            return "Dida365 API call succeeded but returned no projects."
        names = ", ".join(p.name or p.id for p in projects[:5])
        suffix = " ..." if len(projects) > 5 else ""
        return (
            f"Dida365 API read probe successful.\n"
            f"- Project count: {len(projects)}\n"
            f"- Sample projects: {names}{suffix}"
        )

    async def list_projects_summary(self) -> str:
        """List all projects as a formatted summary.

        Returns:
            Formatted project list.
        """
        projects = await self.client.list_projects()
        if not projects:
            return "No Dida365 projects found."
        lines = [f"Dida365 projects: {len(projects)}"]
        for p in projects[:10]:
            lines.append(f"- {p.name or '(unnamed)'} [{p.id}]")
        if len(projects) > 10:
            lines.append("- ...")
        lines.append(f"- {_INBOX_PROJECT_NAME} [{_INBOX_PROJECT_ID}]")
        return "\n".join(lines)

    async def list_today_tasks_summary(self) -> str:
        """List tasks due today as a formatted summary.

        Returns:
            Formatted task list.
        """
        today = self._today()
        items = await self.list_today_tasks(today=today)
        if not items:
            return f"No tasks due today ({today.isoformat()})."
        lines = [f"Tasks due today ({today.isoformat()}): {len(items)}"]
        for item in items[:20]:
            lines.append(self._format_single_task(item))
        if len(items) > 20:
            lines.append(f"... and {len(items) - 20} more")
        return "\n".join(lines)

    async def list_today_tasks(
        self, *, today: date
    ) -> list[DidaTaskWithProject]:
        """Get all tasks due today.

        Args:
            today: Today's date in the configured timezone.

        Returns:
            List of tasks due today.
        """
        all_items = await self._collect_all_tasks()
        return [
            item
            for item in all_items
            if self._is_task_due_today(item.task, today=today)
            and not self._is_completed(item.task)
        ]

    async def list_unfinished_tasks_summary(self) -> str:
        """List unfinished tasks as a formatted summary.

        Returns:
            Formatted task list.
        """
        items = await self.list_unfinished_tasks()
        if not items:
            return "No unfinished tasks."
        overdue_count = sum(1 for item in items if self._is_overdue(item.task))
        lines = [
            f"Unfinished tasks: {len(items)}",
            f"- Overdue: {overdue_count}",
        ]
        for item in items[:30]:
            lines.append(self._format_single_task(item, include_overdue=True))
        if len(items) > 30:
            lines.append(f"... and {len(items) - 30} more")
        return "\n".join(lines)

    async def list_unfinished_tasks(
        self,
    ) -> list[DidaTaskWithProject]:
        """Get all unfinished tasks.

        Returns:
            Sorted list of unfinished tasks.
        """
        all_items = await self._collect_all_tasks()
        unfinished = [
            item for item in all_items if not self._is_completed(item.task)
        ]
        unfinished.sort(
            key=lambda item: (
                self._unfinished_sort_key(item.task),
                self._sort_due_value(item.task),
                -(item.task.priority or 0),
                item.project_name,
                item.task.title,
            )
        )
        return unfinished

    async def _collect_all_tasks(self) -> list[DidaTaskWithProject]:
        """Collect tasks from all projects and inbox.

        Note:
            This method does **not** early-return when ``list_projects()``
            returns an empty list. Inbox tasks are fetched independently
            via ``get_inbox_tasks()`` and must still be collected even
            when the user has no named projects.

        Returns:
            Combined list of all tasks with project context.
        """
        projects = await self.client.list_projects()

        active_projects = [p for p in projects if p.id]
        results = await asyncio.gather(
            *[self.client.get_project_data(p.id) for p in active_projects],
            return_exceptions=True,
        )

        items: list[DidaTaskWithProject] = []
        for project, result in zip(active_projects, results):
            if isinstance(result, Exception):
                continue
            project_name = result.project.name if result.project else project.id
            for task in result.tasks:
                items.append(
                    DidaTaskWithProject(
                        project_id=project.id,
                        project_name=project_name,
                        task=task,
                    )
                )

        try:
            inbox_tasks = await self.client.get_inbox_tasks()
            for task in inbox_tasks:
                items.append(
                    DidaTaskWithProject(
                        project_id=_INBOX_PROJECT_ID,
                        project_name=_INBOX_PROJECT_NAME,
                        task=task,
                    )
                )
        except Exception:
            pass

        return items

    @staticmethod
    def _is_completed(task: DidaTask) -> bool:
        """Check whether a task is completed.

        A task is considered completed if it has a non-empty
        ``completed_time`` or its ``status`` equals 2.

        Args:
            task: The task to check.

        Returns:
            True if the task is completed, False otherwise.
        """
        if task.completed_time:
            return True
        return task.status == 2

    def _tz(self):
        """Get the configured timezone as a ZoneInfo object.

        Returns:
            ``ZoneInfo`` instance for the configured timezone.
        """
        return get_timezone(self.settings.timezone)

    def _today(self) -> date:
        """Get today's date in the configured timezone.

        Returns:
            Today's date in the configured timezone.
        """
        return today_in_timezone(self.settings.timezone)

    def _effective_due_datetime(self, task: DidaTask) -> datetime | None:
        """Get the effective due datetime for a task.

        For all-day tasks the effective due is the start date if set,
        otherwise the due date minus one day (Dida365 API convention).
        For non-all-day tasks the due date is used as-is.

        Args:
            task: The task to evaluate.

        Returns:
            Effective due datetime, or None if no due date is set.
        """
        if task.is_all_day:
            start_dt = self._parse_datetime(task.start_date, task=task)
            if start_dt:
                return start_dt
            due_dt = self._parse_datetime(task.due_date, task=task)
            if due_dt:
                return due_dt - timedelta(days=1)
            return None
        return self._parse_datetime(task.due_date, task=task)

    def _parse_datetime(
        self, value: str, *, task: DidaTask | None = None
    ) -> datetime | None:
        """Parse a datetime string from the Dida365 API.

        If the value lacks timezone information, the task's timezone
        is assumed first, falling back to the configured plugin
        timezone.

        Args:
            value: The datetime string from the API.
            task: Optional task whose ``time_zone`` is used as a
                fallback timezone assumption.

        Returns:
            Parsed datetime in the configured timezone, or None if
            parsing fails.
        """
        assume_tz = (
            task.time_zone
            if task and task.time_zone
            else self.settings.timezone
        )
        return parse_api_datetime(
            value,
            assume_timezone_name=assume_tz,
            target_timezone_name=self.settings.timezone,
        )

    def _is_task_due_today(self, task: DidaTask, *, today: date) -> bool:
        """Check whether a task is due on a specific date.

        Args:
            task: The task to check.
            today: The date to compare against.

        Returns:
            True if the task's effective due date matches ``today``.
        """
        dt = self._effective_due_datetime(task)
        if not dt:
            return False
        return dt.date() == today

    def _is_overdue(self, task: DidaTask, *, today: date | None = None) -> bool:
        """Check whether an unfinished task is overdue.

        A completed task is never overdue. A task without a due date
        is also never overdue.

        Args:
            task: The task to check.
            today: The reference date. Defaults to today in the
                configured timezone.

        Returns:
            True if the task is unfinished, has a due date, and that
            date is before ``today``.
        """
        if self._is_completed(task):
            return False
        dt = self._effective_due_datetime(task)
        if not dt:
            return False
        return dt.date() < (today or self._today())

    def _sort_due_value(self, task: DidaTask) -> tuple[int, str]:
        """Produce a sort key based on due date for task ordering.

        Tasks with a due date sort before those without. Among tasks
        with a due date, earlier dates come first.

        Args:
            task: The task to evaluate.

        Returns:
            A tuple ``(has_due, iso_datetime)`` where ``has_due`` is
            0 if a due date exists and 1 otherwise.
        """
        dt = self._effective_due_datetime(task)
        if not dt:
            return (1, "")
        return (0, dt.isoformat())

    def _unfinished_sort_key(self, task: DidaTask) -> int:
        """Produce a sort priority for ordering unfinished tasks.

        Overdue tasks come first (0), followed by tasks with a due
        date (1), then tasks without any due date (2).

        Args:
            task: The task to evaluate.

        Returns:
            Sort priority: 0 (overdue), 1 (due), or 2 (no due date).
        """
        if self._is_overdue(task):
            return 0
        if self._effective_due_datetime(task):
            return 1
        return 2

    def _format_due(self, task: DidaTask) -> str:
        """Format a task's due date for display.

        All-day tasks show only the date; time-aware tasks show both
        date and time.

        Args:
            task: The task whose due date to format.

        Returns:
            Formatted due date string, or ``"(No due date)"`` if
            unset.
        """
        dt = self._effective_due_datetime(task)
        if not dt:
            return "(No due date)"
        if task.is_all_day:
            return dt.date().isoformat()
        return dt.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _format_priority(task: DidaTask) -> str:
        """Format a task's priority level for display.

        Maps numeric priority values to labels:
        ``0=none``, ``1=low``, ``3=medium``, ``5=high``.

        Args:
            task: The task whose priority to format.

        Returns:
            Human-readable priority label.
        """
        mapping = {
            None: "(unknown)",
            0: "none",
            1: "low",
            3: "medium",
            5: "high",
        }
        return mapping.get(task.priority, str(task.priority))

    @staticmethod
    def _format_status(task: DidaTask) -> str:
        """Format a task's completion status for display.

        Args:
            task: The task whose status to format.

        Returns:
            ``"completed"`` if the task is done, ``"open"`` otherwise.
        """
        if task.completed_time or task.status == 2:
            return "completed"
        return "open"

    def _format_single_task(
        self,
        item: DidaTaskWithProject,
        *,
        include_overdue: bool = False,
        index: int | None = None,
    ) -> str:
        """Format a single task with project context for display.

        Output includes task ID, title, project name, due date, and
        priority. Optionally appends overdue status and a numeric
        index prefix.

        Args:
            item: The task with project context.
            include_overdue: Whether to append overdue status.
            index: Optional numeric prefix for numbered lists.

        Returns:
            Multi-line formatted string.
        """
        prefix = f"{index}. " if index else ""
        parts = [
            f"{prefix}[{item.task.id}] {item.task.title}",
            f"   Project: {item.project_name}",
            f"   Due: {self._format_due(item.task)}",
            f"   Priority: {self._format_priority(item.task)}",
        ]
        if include_overdue:
            parts.append(
                f"   Overdue: {'Yes' if self._is_overdue(item.task) else 'No'}"
            )
        return "\n".join(parts)

    @staticmethod
    def explain_error(error: Exception) -> str:
        """Convert a plugin exception to a user-friendly message.

        Args:
            error: The exception to explain.

        Returns:
            User-friendly error message.
        """
        if isinstance(error, DidaError):
            return str(error)
        return f"Unexpected Dida365 plugin error: {error!s}"

    async def find_task_by_id(self, task_id: str) -> DidaTaskWithProject | None:
        """Find a task by its ID across all projects and inbox.

        Args:
            task_id: The task ID to find.

        Returns:
            The task with project context, or None if not found.
        """
        all_items = await self._collect_all_tasks()
        for item in all_items:
            if item.task.id == task_id:
                return item
        return None

    async def update_task_details(
        self, task_id: str, updates: dict[str, Any]
    ) -> str:
        """Update a task's details via the fetch-merge-POST workflow.

        The Dida365 API requires the full task object on update. This method
        fetches the complete task, merges in the requested updates, removes the
        problematic ``reminders`` field, and POSTs the full object back.

        Args:
            task_id: The task ID to update.
            updates: Dict of fields to update using Dida365 API camelCase keys
                (e.g. ``{"title": "...", "content": "...", "dueDate": "..."}``).

        Returns:
            Formatted success message listing changed fields.

        Raises:
            DidaValidationError: If the task is not found.
        """
        found = await self.find_task_by_id(task_id)
        if not found:
            raise DidaValidationError(f"Task {task_id} not found.")

        raw = (
            dict(found.task.raw)
            if found.task.raw
            else self._task_to_raw(found.task)
        )

        raw.update(updates)

        raw.pop("reminders", None)

        updated = await self.client.update_task(task_id, raw)

        changed = [k for k in updates if k in raw]
        return (
            f"Task [{updated.id}] {updated.title} updated successfully.\n"
            f"Changed fields: {', '.join(changed)}"
        )

    async def create_task(
        self,
        title: str,
        project_id: str | None = None,
        content: str | None = None,
        priority: int | None = None,
        tags: str | None = None,
        due_date: str | None = None,
    ) -> str:
        """Create a new task in Dida365.

        Args:
            title: Task title (required).
            project_id: Target project ID. Defaults to the configured
                default_project if not provided.
            content: Task notes / description.
            priority: Priority level (0=none, 1=low, 3=medium, 5=high).
            tags: Comma-separated tag names (e.g. "work,urgent").
            due_date: Due date in ISO format or Dida365 API format.

        Returns:
            Formatted success message with the created task info.

        Raises:
            DidaValidationError: If title is empty.
        """
        if not title.strip():
            raise DidaValidationError("Task title cannot be empty.")

        pid = project_id or self.settings.default_project or ""
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

        created = await self.client.create_task(payload)
        return (
            f"Task [{created.id}] {created.title} created successfully.\n"
            f"Project: {created.project_id or '(Inbox)'}"
        )

    async def complete_task(self, task_id: str) -> str:
        """Mark a task as completed.

        Args:
            task_id: The task ID to complete.

        Returns:
            Formatted success message.

        Raises:
            DidaValidationError: If the task is not found.
        """
        found = await self.find_task_by_id(task_id)
        if not found:
            raise DidaValidationError(f"Task {task_id} not found.")
        await self.client.complete_task(found.project_id, task_id)
        return f"Task [{task_id}] {found.task.title} marked as completed."

    async def delete_task(self, task_id: str) -> str:
        """Delete a task permanently.

        Args:
            task_id: The task ID to delete.

        Returns:
            Formatted success message.

        Raises:
            DidaValidationError: If the task is not found.
        """
        found = await self.find_task_by_id(task_id)
        if not found:
            raise DidaValidationError(f"Task {task_id} not found.")
        await self.client.delete_task(found.project_id, task_id)
        return f"Task [{task_id}] {found.task.title} deleted."

    @staticmethod
    def _task_to_raw(task: DidaTask) -> dict[str, Any]:
        """Reconstruct an API-style dict from a DidaTask instance.

        Used as a fallback when ``task.raw`` is empty (unlikely in production).
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
