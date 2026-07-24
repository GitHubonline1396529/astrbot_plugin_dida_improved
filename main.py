from __future__ import annotations

import json

from astrbot.api import AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from .client import DidaClient
from .models import DidaPluginSettings
from .service import DidaService


@register(
    "astrbot_plugin_dida_improved",
    "Githubonline1396529",
    "Dida365 Improved - Inbox support and full task management",
    "0.1.0-beta",
)
class DidaImprovedPlugin(Star):
    """Dida365 improved plugin for AstrBot."""

    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        """Initialize the Dida365 improved plugin.

        Args:
            context: The AstrBot context for the plugin.
            config: The AstrBot configuration for the plugin.
        """
        super().__init__(context, config)
        self.config = config

    def _build_settings(self) -> DidaPluginSettings:
        """Build plugin settings from AstrBot config.

        This function constructs a DidaPluginSettings instance using the current
        AstrBot configuration. It also retrieves the fallback timezone from the
        plugin context if not explicitly set in the config.
        """
        return DidaPluginSettings.from_config(
            self.config,
            fallback_timezone=str(
                self.context.get_config().get("timezone", "Asia/Shanghai")
                or "Asia/Shanghai"
            ),
        )

    def _build_service(self) -> DidaService:
        """Build a DidaService instance from the current config.

        Returns:
            A configured ``DidaService`` ready for use.
        """
        settings = self._build_settings()
        return DidaService(settings, client=DidaClient(settings))

    async def _run_service(self, operation) -> str:
        """Run a service operation with error handling.

        Args:
            operation: Async callable that takes a DidaService and returns
                a string.

        Returns:
            Result string, or error message on failure.
        """
        service = self._build_service()
        try:
            return await operation(service)
        except Exception as exc:
            return service.explain_error(exc)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("dida_ping")
    async def dida_ping(self, event: AstrMessageEvent):
        """Check whether the plugin is loaded and configured."""
        yield event.plain_result(self._build_service().build_status_summary())

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("dida_probe")
    async def dida_probe(self, event: AstrMessageEvent):
        """Run a minimal read-only API probe."""
        yield event.plain_result(
            await self._run_service(lambda service: service.probe_read_access())
        )

    # ----- LLM tools (replace legacy commands) -----

    @filter.llm_tool(name="list_dida_projects")
    async def list_dida_projects_llm(self, event: AstrMessageEvent):
        """List all Dida365 projects including the Inbox.

        Returns:
            Formatted project list with names and IDs.
        """
        return await self._run_service(
            lambda service: service.list_projects_summary()
        )

    @filter.llm_tool(name="list_dida_tasks")
    async def list_dida_tasks_llm(
        self,
        event: AstrMessageEvent,
        task_filter: str = "unfinished",
        limit: int = 50,
    ):
        """Query Dida365 tasks with optional filtering.

        Args:
            task_filter (string): Filter condition. "today" for tasks due today,
                "unfinished" for all incomplete tasks (default).
            limit (number): Maximum number of tasks to return. Use 0 for no
                limit. The configured ``display_limit`` is used when this is not
                set.
        """
        if task_filter == "today":
            return await self._run_service(
                lambda service: service.list_today_tasks_summary(limit=limit)
            )
        return await self._run_service(
            lambda service: service.list_unfinished_tasks_summary(limit=limit)
        )

    @filter.llm_tool(name="update_dida_task")
    async def update_dida_task_llm(
        self, event: AstrMessageEvent, task_id: str, updates_json: str = ""
    ):
        """Update a Dida365 task's fields (title, content, dueDate, priority,
        tags, etc.).

        Uses the Dida365 API fetch-merge-POST workflow to update any field of a
        task. The ``updates_json`` parameter must be a JSON **object** with
        camelCase keys matching the Dida365 API field names (e.g.
        ``{"title": "New title", "content": "New notes"}``).

        Args:
            task_id (string): The ID of the task to update.
            updates_json (string): JSON object of fields to update. Example:
                {"title": "New title", "content": "New notes"}. Use camelCase
                keys matching the Dida365 API.
        """
        if not updates_json.strip():
            return (
                "No updates provided. "
                "Pass a JSON object with fields to update, "
                'e.g. {"title": "..."}'
            )
        try:
            updates = json.loads(updates_json)
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {e}"
        if not isinstance(updates, dict):
            return "updates_json must be a JSON object, not an array or scalar."
        return await self._run_service(
            lambda service: service.update_task_details(task_id, updates)
        )

    @filter.llm_tool(name="create_dida_task")
    async def create_dida_task_llm(
        self,
        event: AstrMessageEvent,
        title: str,
        project_id: str = "",
        content: str = "",
        priority: str = "",
        tags: str = "",
        due_date: str = "",
    ):
        """Create a new task in Dida365.

        Args:
            title (string): Task title (required).
            project_id (string): Target project ID. Leave empty to use the
                configured default project or Inbox.
            content (string): Task notes or description.
            priority (string): Priority level: "none" (0), "low" (1), "medium"
                (3), or "high" (5).
            tags (string): Comma-separated tag names, e.g. "work,urgent".
            due_date (string): Due date in ISO format, e.g.
                "2026-07-10T18:00:00+08:00".
        """
        priority_map = {
            "none": 0,
            "low": 1,
            "medium": 3,
            "high": 5,
        }
        prio = None
        if priority.strip():
            lower = priority.strip().lower()
            prio = priority_map.get(lower)
            if prio is None:
                try:
                    prio = int(priority.strip())
                except ValueError:
                    return (
                        f"Invalid priority '{priority}'. "
                        f"Use 'none', 'low', 'medium', 'high', or 0/1/3/5."
                    )

        return await self._run_service(
            lambda service: service.create_task(
                title=title,
                project_id=project_id.strip() or None,
                content=content.strip() or None,
                priority=prio,
                tags=tags.strip() or None,
                due_date=due_date.strip() or None,
            )
        )

    @filter.llm_tool(name="complete_dida_task")
    async def complete_dida_task_llm(
        self, event: AstrMessageEvent, task_id: str
    ):
        """Mark a Dida365 task as completed.

        Args:
            task_id (string): The ID of the task to complete.
        """
        return await self._run_service(
            lambda service: service.complete_task(task_id)
        )

    @filter.llm_tool(name="reopen_dida_task")
    async def reopen_dida_task_llm(self, event: AstrMessageEvent, task_id: str):
        """Reopen (uncomplete) a completed Dida365 task.

        Sets the task status back to 0 so it appears in the active task list
        again.

        Args:
            task_id (string): The ID of the completed task to reopen.
        """
        return await self._run_service(
            lambda service: service.reopen_task(task_id)
        )

    @filter.llm_tool(name="delete_dida_task")
    async def delete_dida_task_llm(self, event: AstrMessageEvent, task_id: str):
        """Delete a Dida365 task permanently.

        Args:
            task_id (string): The ID of the task to delete.
        """
        return await self._run_service(
            lambda service: service.delete_task(task_id)
        )

    @filter.llm_tool(name="move_dida_task")
    async def move_dida_task_llm(
        self,
        event: AstrMessageEvent,
        task_id: str,
        from_project_id: str,
        to_project_id: str,
    ):
        """Move a Dida365 task from one project to another.

        Args:
            task_id (string): The ID of the task to move.
            from_project_id (string): The source project ID.
            to_project_id (string): The destination project ID.
        """
        return await self._run_service(
            lambda service: service.move_task(
                from_project_id, to_project_id, task_id
            )
        )

    @filter.llm_tool(name="get_dida_task_detail")
    async def get_dida_task_detail_llm(
        self,
        event: AstrMessageEvent,
        project_id: str,
        task_id: str,
    ):
        """Get detailed information for a specific Dida365 task.

        Args:
            project_id (string): The project ID containing the task.
            task_id (string): The ID of the task to retrieve.
        """
        return await self._run_service(
            lambda service: service.get_task_by_id(project_id, task_id)
        )

    @filter.llm_tool(name="list_completed_dida_tasks")
    async def list_completed_dida_tasks_llm(
        self,
        event: AstrMessageEvent,
        project_ids: str = "",
        start_date: str = "",
        end_date: str = "",
        limit: int = 50,
    ):
        """List completed Dida365 tasks within a time range.

        Args:
            project_ids (string): Comma-separated project IDs to filter by
                (optional).
            start_date (string): Start of time range in ISO format (optional,
                e.g. "2026-07-01T00:00:00+08:00").
            end_date (string): End of time range in ISO format (optional, e.g.
                "2026-07-08T00:00:00+08:00").
            limit (number): Maximum number of tasks to return. Use 0 for no
                limit. The configured ``display_limit`` is used when this is not
                set.
        """
        pids = (
            [p.strip() for p in project_ids.split(",") if p.strip()]
            if project_ids.strip()
            else None
        )
        start = start_date.strip() or None
        end = end_date.strip() or None
        return await self._run_service(
            lambda service: service.list_completed_tasks(
                project_ids=pids,
                start_date=start,
                end_date=end,
                limit=limit,
            )
        )

    @filter.llm_tool(name="get_dida_task_comments")
    async def get_dida_task_comments_llm(
        self,
        event: AstrMessageEvent,
        project_id: str,
        task_id: str,
    ):
        """Get comments for a Dida365 task.

        Args:
            project_id (string): The project ID containing the task.
            task_id (string): The ID of the task.
        """
        return await self._run_service(
            lambda service: service.get_task_comments(project_id, task_id)
        )

    @filter.llm_tool(name="add_dida_task_comment")
    async def add_dida_task_comment_llm(
        self,
        event: AstrMessageEvent,
        project_id: str,
        task_id: str,
        title: str,
    ):
        """Add a comment to a Dida365 task.

        Args:
            project_id (string): The project ID containing the task.
            task_id (string): The ID of the task.
            title (string): Comment text.
        """
        return await self._run_service(
            lambda service: service.add_task_comment(project_id, task_id, title)
        )

    @filter.llm_tool(name="delete_dida_task_comment")
    async def delete_dida_task_comment_llm(
        self,
        event: AstrMessageEvent,
        project_id: str,
        task_id: str,
        comment_id: str,
    ):
        """Delete a comment from a Dida365 task.

        Args:
            project_id (string): The project ID containing the task.
            task_id (string): The ID of the task.
            comment_id (string): The ID of the comment to delete.
        """
        return await self._run_service(
            lambda service: service.delete_task_comment(
                project_id, task_id, comment_id
            )
        )
