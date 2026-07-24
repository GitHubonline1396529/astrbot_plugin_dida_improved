from __future__ import annotations

import asyncio
from datetime import date, datetime
from typing import Any

from ..client import DidaClient
from ..exceptions import DidaError, DidaValidationError
from ..models import DidaPluginSettings, DidaTask, DidaTaskWithProject
from ..time_utils import get_timezone, today_in_timezone
from . import _helpers, formatting, task_ops
from . import comments as _comments_mod

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
        """Initialize the service.

        Args:
            settings: Plugin configuration settings.
            client: Optional pre-configured :class:`DidaClient`. If omitted
                a new client is created from *settings*.
        """
        self.settings = settings
        self.client = client or DidaClient(settings)

    def build_status_summary(self) -> str:
        """Build a plugin status summary string.

        Returns:
            Multi-line string describing the current plugin configuration
            (token configured, API base URL, timezone, token expiry notice).
        """
        # Dida365 access tokens are typically valid for ~180 days.
        # No API endpoint exposes the exact expiry, so we advise manual refresh.
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
        """Probe the Dida365 API by listing projects.

        A lightweight read-only check that returns a success message with
        project count and sample names, or an error indicator.

        Returns:
            Human-readable probe result string.
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

    async def list_projects_summary(self, limit: int | None = None) -> str:
        """List all Dida365 projects as a formatted summary string.

        Args:
            limit: Maximum number of projects to show. Uses
                ``display_limit`` from settings when not set. Use 0
                for no limit.

        Returns:
            Multi-line string with project names and IDs.
        """
        projects = await self.client.list_projects()
        if not projects:
            return "No Dida365 projects found."
        _limit = limit if limit is not None else self.settings.display_limit
        if _limit <= 0 or _limit >= len(projects):
            _limit = len(projects)
        lines = [f"Dida365 projects: {len(projects)}"]
        for p in projects[:_limit]:
            lines.append(f"- {p.name or '(unnamed)'} [{p.id}]")
        if len(projects) > _limit:
            lines.append("- ...")
        lines.append(f"- {_INBOX_PROJECT_NAME} [{_INBOX_PROJECT_ID}]")
        return "\n".join(lines)

    async def list_today_tasks_summary(self, limit: int | None = None) -> str:
        """List tasks due today as a formatted summary string.

        Args:
            limit: Maximum number of tasks to show. Uses
                ``display_limit`` from settings when not set. Use 0
                for no limit.

        Returns:
            Multi-line string with due-today task details or a
            "no tasks" message.
        """
        today = self._today()
        items = await self.list_today_tasks(today=today)
        if not items:
            return f"No tasks due today ({today.isoformat()})."
        _limit = limit if limit is not None else self.settings.display_limit
        if _limit <= 0 or _limit >= len(items):
            _limit = len(items)
        lines = [f"Tasks due today ({today.isoformat()}): {len(items)}"]
        for item in items[:_limit]:
            lines.append(self._format_single_task(item))
        if len(items) > _limit:
            lines.append(f"... and {len(items) - _limit} more")
        return "\n".join(lines)

    async def list_today_tasks(
        self, *, today: date
    ) -> list[DidaTaskWithProject]:
        """Return all uncompleted tasks due today.

        Args:
            today: Reference date (typically obtained via :meth:`_today`).

        Returns:
            List of :class:`DidaTaskWithProject` whose effective due date
            matches *today* and that are not yet completed.
        """
        all_items = await self._collect_all_tasks()
        return [
            item
            for item in all_items
            if _helpers.is_task_due_today(
                item.task, today=today, timezone=self.settings.timezone
            )
            and not _helpers.is_completed(item.task)
        ]

    async def list_unfinished_tasks_summary(
        self, limit: int | None = None
    ) -> str:
        """List all unfinished tasks as a formatted summary string.

        Args:
            limit: Maximum number of tasks to show. Uses
                ``display_limit`` from settings when not set. Use 0
                for no limit.

        Returns:
            Multi-line string with unfinished task count, overdue count,
            and task details or a "no tasks" message.
        """
        items = await self.list_unfinished_tasks()
        if not items:
            return "No unfinished tasks."
        overdue_count = sum(
            1
            for item in items
            if _helpers.is_overdue(item.task, timezone=self.settings.timezone)
        )
        _limit = limit if limit is not None else self.settings.display_limit
        if _limit <= 0 or _limit >= len(items):
            _limit = len(items)
        lines = [
            f"Unfinished tasks: {len(items)}",
            f"- Overdue: {overdue_count}",
        ]
        for item in items[:_limit]:
            lines.append(
                formatting.format_single_task(
                    item,
                    timezone=self.settings.timezone,
                    include_overdue=True,
                )
            )
        if len(items) > _limit:
            lines.append(f"... and {len(items) - _limit} more")
        return "\n".join(lines)

    async def list_unfinished_tasks(
        self,
    ) -> list[DidaTaskWithProject]:
        """Return all unfinished tasks, sorted by urgency.

        Sorting priority (highest to lowest):
        1. Overdue tasks come first.
        2. Tasks with a due date before tasks without.
        3. Higher-priority tasks (by Dida365 priority value) before lower.
        4. Alphabetically by project name.
        5. Alphabetically by title.

        Returns:
            Sorted list of unfinished :class:`DidaTaskWithProject`.
        """
        all_items = await self._collect_all_tasks()
        unfinished = [
            item for item in all_items if not _helpers.is_completed(item.task)
        ]
        # Sort by: (1) overdue/duesoon/nodue, (2) due datetime,
        # (3) priority descending, (4) project name, (5) title.
        # Overdue tasks bubble to the top.
        unfinished.sort(
            key=lambda item: (
                _helpers.unfinished_sort_key(
                    item.task,
                    today=self._today(),
                    timezone=self.settings.timezone,
                ),
                _helpers.sort_due_value(
                    item.task, timezone=self.settings.timezone
                ),
                -(item.task.priority or 0),
                item.project_name,
                item.task.title,
            )
        )
        return unfinished

    async def _collect_all_tasks(self) -> list[DidaTaskWithProject]:
        """Collect all tasks from all projects and the inbox.

        Fetches project data in parallel via :func:`asyncio.gather`.
        A single project failure is silently skipped so that data from
        other projects is still available. The inbox is fetched via its
        dedicated endpoint as a best-effort operation.

        Returns:
            List of :class:`DidaTaskWithProject` across all accessible
            projects and the inbox.
        """
        projects = await self.client.list_projects()
        active_projects = [p for p in projects if p.id]
        # Fetch project data in parallel; a single project failure is tolerated
        # so that data from other projects is still returned.
        results = await asyncio.gather(
            *[self.client.get_project_data(p.id) for p in active_projects],
            return_exceptions=True,
        )

        items: list[DidaTaskWithProject] = []
        for project, result in zip(active_projects, results):
            if isinstance(result, Exception):
                # Silently skip projects whose data failed to load.
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

        # The inbox is not a real project; fetch it via the dedicated endpoint.
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
            # Inbox fetch is best-effort; ignore failures silently.
            pass

        return items

    def _is_completed(self, task: DidaTask) -> bool:
        """Check whether a task is completed.

        See Also:
            :func:`_helpers.is_completed`
        """
        return _helpers.is_completed(task)

    async def _resolve_project_name(self, project_id: str) -> str:
        """Resolve a project ID to a human-readable project name.

        Inbox-style virtual IDs (beginning with ``"inbox"``) are mapped to
        the constant ``"Inbox"``.  Other IDs are looked up via the project
        list.  Falls back to the raw *project_id* when the lookup fails.

        Args:
            project_id: The project identifier to resolve.

        Returns:
            The project name, or *project_id* if it cannot be resolved.
        """
        if project_id.lower().startswith("inbox"):
            return _INBOX_PROJECT_NAME
        try:
            projects = await self.client.list_projects()
            for p in projects:
                if p.id == project_id:
                    return p.name
        except Exception:
            pass
        return project_id

    def _tz(self):
        """Get the configured timezone object.

        See Also:
            :func:`time_utils.get_timezone`
        """
        return get_timezone(self.settings.timezone)

    def _today(self) -> date:
        """Get today's date in the configured timezone.

        See Also:
            :func:`time_utils.today_in_timezone`
        """
        return today_in_timezone(self.settings.timezone)

    def _parse_datetime(
        self, value: str, *, task: DidaTask | None = None
    ) -> datetime | None:
        """Parse an API datetime string.

        See Also:
            :func:`_helpers.parse_datetime`
        """
        return _helpers.parse_datetime(
            value, task=task, timezone=self.settings.timezone
        )

    def _effective_due_datetime(self, task: DidaTask) -> datetime | None:
        """Get the effective due datetime for a task.

        See Also:
            :func:`_helpers.effective_due_datetime`
        """
        return _helpers.effective_due_datetime(
            task, timezone=self.settings.timezone
        )

    def _is_task_due_today(self, task: DidaTask, *, today: date) -> bool:
        """Check whether a task is due on a given date.

        See Also:
            :func:`_helpers.is_task_due_today`
        """
        return _helpers.is_task_due_today(
            task, today=today, timezone=self.settings.timezone
        )

    def _is_overdue(
        self,
        task: DidaTask,
        *,
        today: date | None = None,
    ) -> bool:
        """Check whether a task is overdue.

        See Also:
            :func:`_helpers.is_overdue`
        """
        return _helpers.is_overdue(
            task, today=today, timezone=self.settings.timezone
        )

    def _sort_due_value(self, task: DidaTask) -> tuple[int, str]:
        """Get a sort key tuple for due-date ordering.

        See Also:
            :func:`_helpers.sort_due_value`
        """
        return _helpers.sort_due_value(task, timezone=self.settings.timezone)

    def _unfinished_sort_key(self, task: DidaTask) -> int:
        """Get a sort priority for unfinished task ordering.

        See Also:
            :func:`_helpers.unfinished_sort_key`
        """
        return _helpers.unfinished_sort_key(
            task,
            today=self._today(),
            timezone=self.settings.timezone,
        )

    @staticmethod
    def _task_to_raw(task: DidaTask) -> dict[str, Any]:
        """Serialize a task to the API raw dict format.

        See Also:
            :func:`_helpers.task_to_raw`
        """
        return _helpers.task_to_raw(task)

    def _format_due(self, task: DidaTask) -> str:
        """Format a task's due date as a human-readable string.

        See Also:
            :func:`formatting.format_due`
        """
        return formatting.format_due(task, timezone=self.settings.timezone)

    @staticmethod
    def _format_priority(task: DidaTask) -> str:
        """Format a task's priority as a human-readable label.

        See Also:
            :func:`formatting.format_priority`
        """
        return formatting.format_priority(task)

    @staticmethod
    def _format_status(task: DidaTask) -> str:
        """Format a task's status as a human-readable string.

        See Also:
            :func:`formatting.format_status`
        """
        return formatting.format_status(task)

    def _format_single_task(
        self,
        item: DidaTaskWithProject,
        *,
        include_overdue: bool = False,
        index: int | None = None,
    ) -> str:
        """Format a task-with-project item as a multi-line summary.

        See Also:
            :func:`formatting.format_single_task`
        """
        return formatting.format_single_task(
            item,
            timezone=self.settings.timezone,
            include_overdue=include_overdue,
            index=index,
        )

    @staticmethod
    def explain_error(error: Exception) -> str:
        """Convert an exception to a user-facing error message.

        Args:
            error: The exception to explain.

        Returns:
            A human-readable error string.
        """
        if isinstance(error, DidaError):
            return str(error)
        return f"Unexpected Dida365 plugin error: {error!s}"

    async def find_task_by_id(self, task_id: str) -> DidaTaskWithProject | None:
        """Find a task by its ID across all projects, inbox, and completed tasks.

        First searches uncompleted tasks (via project data + inbox). If not
        found, falls back to searching completed tasks via the dedicated
        ``/task/completed`` endpoint.

        Args:
            task_id: The task ID to search for.

        Returns:
            The matching :class:`DidaTaskWithProject`, or ``None``.
        """
        all_items = await self._collect_all_tasks()
        for item in all_items:
            if item.task.id == task_id:
                return item
        # Fallback: search completed tasks.
        try:
            completed_tasks = await task_ops.list_completed_tasks(self.client)
            for task in completed_tasks:
                if task.id == task_id:
                    project_name = await self._resolve_project_name(
                        task.project_id
                    )
                    return DidaTaskWithProject(
                        project_id=task.project_id,
                        project_name=project_name,
                        task=task,
                    )
        except Exception:
            pass
        return None

    async def update_task_details(
        self, task_id: str, updates: dict[str, Any]
    ) -> str:
        """Update one or more fields of a task.

        Fetches the current task representation, applies *updates*, strips
        the problematic ``reminders`` field, and performs a full-object
        replacement via the API.

        Args:
            task_id: ID of the task to update.
            updates: Dict of field names to new values.

        Returns:
            Success message listing the changed fields.

        Raises:
            DidaValidationError: If *task_id* is not found.
        """
        found = await self.find_task_by_id(task_id)
        if not found:
            raise DidaValidationError(f"Task {task_id} not found.")

        raw = (
            dict(found.task.raw)
            if found.task.raw
            else _helpers.task_to_raw(found.task)
        )
        raw.update(updates)
        # The Dida365 API returns HTTP 500 when `reminders` is included on
        # task update (full-object replacement). Strip it unconditionally.
        raw.pop("reminders", None)

        updated = await task_ops.update_task(self.client, task_id, raw)

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
        """Create a new task.

        If *project_id* is not specified, falls back to the default project
        configured in plugin settings. If that is also empty, the task is
        created in the inbox.

        Args:
            title: Task title.
            project_id: Target project ID.
            content: Optional description / rich-text content.
            priority: Priority level (0=none, 1=low, 3=medium, 5=high).
            tags: Comma-separated tag string.
            due_date: ISO-8601 due date string.

        Returns:
            Success message with task ID, title, and project.
        """
        pid = project_id or self.settings.default_project or ""
        created = await task_ops.create_task(
            self.client,
            title=title,
            project_id=pid or None,
            content=content,
            priority=priority,
            tags=tags,
            due_date=due_date,
        )
        return (
            f"Task [{created.id}] {created.title} created successfully.\n"
            f"Project: {created.project_id or '(Inbox)'}"
        )

    async def complete_task(self, task_id: str) -> str:
        """Mark a task as completed.

        Args:
            task_id: ID of the task to complete.

        Returns:
            Success message.

        Raises:
            DidaValidationError: If *task_id* is not found.
        """
        found = await self.find_task_by_id(task_id)
        if not found:
            raise DidaValidationError(f"Task {task_id} not found.")
        if _helpers.is_completed(found.task):
            return (
                f"Task [{task_id}] {found.task.title} is already completed."
            )
        await task_ops.complete_task(self.client, found.project_id, task_id)
        return f"Task [{task_id}] {found.task.title} marked as completed."

    async def reopen_task(self, task_id: str) -> str:
        """Reopen (uncomplete) a completed task by setting status to 0.

        Fetches the current task representation, applies ``status=0``, strips
        the problematic ``reminders`` field, and performs a full-object
        replacement via the API.

        Args:
            task_id: ID of the task to reopen.

        Returns:
            Success message.

        Raises:
            DidaValidationError: If *task_id* is not found or the task is
                not completed.
        """
        found = await self.find_task_by_id(task_id)
        if not found:
            raise DidaValidationError(f"Task {task_id} not found.")
        if not _helpers.is_completed(found.task):
            return (
                f"Task [{task_id}] {found.task.title} is not completed, "
                "no need to reopen."
            )

        raw = (
            dict(found.task.raw)
            if found.task.raw
            else _helpers.task_to_raw(found.task)
        )
        raw["status"] = 0
        raw.pop("reminders", None)

        updated = await task_ops.update_task(self.client, task_id, raw)
        return (
            f"Task [{updated.id}] {updated.title} has been reopened "
            "(status set to 0)."
        )

    async def delete_task(self, task_id: str) -> str:
        """Delete a task permanently.

        Args:
            task_id: ID of the task to delete.

        Returns:
            Success message.

        Raises:
            DidaValidationError: If *task_id* is not found.
        """
        found = await self.find_task_by_id(task_id)
        if not found:
            raise DidaValidationError(f"Task {task_id} not found.")
        await task_ops.delete_task(self.client, found.project_id, task_id)
        return f"Task [{task_id}] {found.task.title} deleted."

    async def move_task(
        self,
        from_project_id: str,
        to_project_id: str,
        task_id: str,
    ) -> str:
        """Move a task from one project to another.

        Args:
            from_project_id: Source project ID.
            to_project_id: Destination project ID.
            task_id: ID of the task to move.

        Returns:
            Success message with task ID and etag.
        """
        result = await task_ops.move_task(
            self.client, from_project_id, to_project_id, task_id
        )
        return (
            f"Task [{result['id']}] moved successfully.\nEtag: {result['etag']}"
        )

    async def filter_tasks(
        self,
        *,
        project_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        priority: list[int] | None = None,
        tag: list[str] | None = None,
        status: list[int] | None = None,
        limit: int | None = None,
    ) -> str:
        """Query tasks with optional filters.

        Args:
            project_ids: Only include tasks from these project IDs.
            start_date: ISO-8601 start date (inclusive).
            end_date: ISO-8601 end date (inclusive).
            priority: Only include tasks with these priority values.
            tag: Only include tasks matching any of these tags.
            status: Only include tasks with these status codes.
            limit: Maximum number of tasks to show. Uses
                ``display_limit`` from settings when not set. Use 0
                for no limit.

        Returns:
            Formatted result string.
        """
        tasks = await task_ops.filter_tasks(
            self.client,
            project_ids=project_ids,
            start_date=start_date,
            end_date=end_date,
            priority=priority,
            tag=tag,
            status=status,
        )
        if not tasks:
            return "No tasks match the filter criteria."
        _limit = limit if limit is not None else self.settings.display_limit
        if _limit <= 0 or _limit >= len(tasks):
            _limit = len(tasks)
        lines = [f"Matching tasks: {len(tasks)}"]
        for t in tasks[:_limit]:
            lines.append(f"- [{t.id}] {t.title}")
        if len(tasks) > _limit:
            lines.append(f"... and {len(tasks) - _limit} more")
        return "\n".join(lines)

    async def list_completed_tasks(
        self,
        *,
        project_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
    ) -> str:
        """List completed tasks, optionally filtered by project and date range.

        Args:
            project_ids: Only include tasks from these project IDs.
            start_date: ISO-8601 start date (inclusive).
            end_date: ISO-8601 end date (inclusive).
            limit: Maximum number of tasks to show. Uses
                ``display_limit`` from settings when not set. Use 0
                for no limit.

        Returns:
            Formatted result string.
        """
        tasks = await task_ops.list_completed_tasks(
            self.client,
            project_ids=project_ids,
            start_date=start_date,
            end_date=end_date,
        )
        if not tasks:
            return "No completed tasks found in the given range."
        _limit = limit if limit is not None else self.settings.display_limit
        if _limit <= 0 or _limit >= len(tasks):
            _limit = len(tasks)
        lines = [f"Completed tasks: {len(tasks)}"]
        for t in tasks[:_limit]:
            completed = t.completed_time or "(unknown)"
            lines.append(f"- [{t.id}] {t.title} (completed: {completed})")
        if len(tasks) > _limit:
            lines.append(f"... and {len(tasks) - _limit} more")
        return "\n".join(lines)

    async def get_task_by_id(self, project_id: str, task_id: str) -> str:
        """Fetch a single task by project ID and task ID, formatted for display.

        Args:
            project_id: Project the task belongs to.
            task_id: ID of the task to fetch.

        Returns:
            Multi-line string with task details (title, project, content,
            due date, priority, status).
        """
        task = await task_ops.get_task_by_id(self.client, project_id, task_id)
        due_str = formatting.format_due(task, timezone=self.settings.timezone)
        return (
            f"Task [{task.id}] {task.title}\n"
            f"Project: {task.project_id}\n"
            f"Content: {task.content or '(empty)'}\n"
            f"Due: {due_str}\n"
            f"Priority: {formatting.format_priority(task)}\n"
            f"Status: {formatting.format_status(task)}"
        )

    async def get_task_comments(self, project_id: str, task_id: str) -> str:
        """Fetch and format all comments for a task.

        Args:
            project_id: Project the task belongs to.
            task_id: Task to fetch comments for.

        Returns:
            Formatted comment list string.
        """
        comments_list = await _comments_mod.get_task_comments(
            self.client, project_id, task_id
        )
        if not comments_list:
            return f"No comments for task [{task_id}]."
        lines = [f"Comments for task [{task_id}]: {len(comments_list)}"]
        for c in comments_list:
            cid = c.get("id", "?")
            title = c.get("title", "")
            created = c.get("createdTime", "")
            lines.append(f"- [{cid}] {title} ({created})")
        return "\n".join(lines)

    async def add_task_comment(
        self, project_id: str, task_id: str, title: str
    ) -> str:
        """Add a comment to a task.

        Args:
            project_id: Project the task belongs to.
            task_id: Task to comment on.
            title: Comment text content.

        Returns:
            Success message with comment ID.
        """
        comment = await _comments_mod.add_task_comment(
            self.client, project_id, task_id, title
        )
        cid = comment.get("id", "?")
        return f"Comment [{cid}] added to task [{task_id}] successfully."

    async def delete_task_comment(
        self, project_id: str, task_id: str, comment_id: str
    ) -> str:
        """Delete a comment from a task.

        Args:
            project_id: Project the task belongs to.
            task_id: Task the comment belongs to.
            comment_id: ID of the comment to delete.

        Returns:
            Success message.
        """
        await _comments_mod.delete_task_comment(
            self.client, project_id, task_id, comment_id
        )
        return (
            f"Comment [{comment_id}] deleted from task [{task_id}] "
            f"successfully."
        )
