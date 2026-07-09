from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from astrbot.api import AstrBotConfig


@dataclass(slots=True)
class DidaPluginSettings:
    """Plugin configuration settings.

    This class represents the configuration settings for the Dida365 plugin. The
    user can assign the following configuration values in the AstrBot config
    through the Web UI plugin settings page or by directly editing the config:

    - access_token: The Dida365 API access token.
    - api_base_url: The base URL for the Dida365 API.
    - default_project: The default project ID to use for tasks.
    - request_timeout_seconds: Timeout for API requests in seconds.
    - timezone: The timezone for task scheduling.
    """

    access_token: str
    api_base_url: str
    default_project: str
    request_timeout_seconds: int
    timezone: str

    @classmethod
    def from_config(
        cls,
        config: AstrBotConfig,
        *,
        fallback_timezone: str = "Asia/Shanghai",
    ) -> DidaPluginSettings:
        """Build settings from AstrBot config.

        This function initializes the plugin configuration from the AstrBot
        config and constructs a DidaPluginSettings instance.

        Args:
            config: Plugin configuration provided by AstrBot.
            fallback_timezone: Default timezone if not configured.

        Returns:
            DidaPluginSettings instance.
        """
        return cls(
            access_token=str(config.get("access_token", "") or ""),
            api_base_url=str(config.get("api_base_url", "") or ""),
            default_project=str(config.get("default_project", "") or ""),
            request_timeout_seconds=max(
                1, int(config.get("request_timeout_seconds", 15) or 15)
            ),
            timezone=str(
                config.get("timezone", fallback_timezone) or fallback_timezone
            ),
        )


@dataclass(slots=True)
class DidaProject:
    """A Dida365 project.

    This class represents a project in Dida365, including its ID, name, kind,
    color, view mode, closed status, group ID, sort order, permission, and raw
    API response data. It provides a class method `from_api` to construct an
    instance from API response data.
    """

    id: str
    name: str
    kind: str = ""
    color: str = ""
    view_mode: str = ""
    closed: bool = False
    group_id: str = ""
    sort_order: int = 0
    permission: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DidaProject:
        """Build a DidaProject from API response data.

        Args:
            data: The API response dict containing project fields
                (``id``, ``name``, ``kind``, ``color``, etc.).

        Returns:
            A ``DidaProject`` instance.
        """
        return cls(
            id=str(data.get("id", "") or ""),
            name=str(data.get("name", "") or ""),
            kind=str(data.get("kind", "") or ""),
            color=str(data.get("color", "") or ""),
            view_mode=str(data.get("viewMode", "") or ""),
            closed=bool(data.get("closed", False)),
            group_id=str(data.get("groupId", "") or ""),
            sort_order=int(data.get("sortOrder", 0) or 0),
            permission=str(data.get("permission", "") or ""),
            raw=data,
        )


@dataclass(slots=True)
class ChecklistItem:
    """A subtask / checklist item within a Dida365 task.

    Checklist items (also known as subtasks) are individual items within a
    task that can be independently completed. Each item has its own status,
    sort order, optional start date and timezone, mirroring the structure of
    the parent task.

    Attributes:
        id: Unique identifier for the checklist item.
        title: The text content of the checklist item.
        status: Completion status (0 = unchecked, 1 = checked).
        sort_order: Ordering position within the parent task.
        start_date: Optional ISO-8601 start date.
        is_all_day: Whether the start date is an all-day event.
        time_zone: IANA timezone string.
        completed_time: ISO-8601 timestamp of when the item was completed.
    """

    id: str
    title: str
    status: int = 0
    sort_order: int = 0
    start_date: str = ""
    is_all_day: bool = False
    time_zone: str = ""
    completed_time: str = ""

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> ChecklistItem:
        """Build a ChecklistItem from API response data.

        Args:
            data: The API response dict containing checklist item fields
                (``id``, ``title``, ``status``, etc.).

        Returns:
            A ``ChecklistItem`` instance.
        """
        return cls(
            id=str(data.get("id", "") or ""),
            title=str(data.get("title", "") or ""),
            status=int(data.get("status", 0) or 0),
            sort_order=int(data.get("sortOrder", 0) or 0),
            start_date=str(data.get("startDate", "") or ""),
            is_all_day=bool(data.get("isAllDay", False)),
            time_zone=str(data.get("timeZone", "") or ""),
            completed_time=str(data.get("completedTime", "") or ""),
        )


@dataclass(slots=True)
class DidaTask:
    """A Dida365 task.

    This class represents a task in Dida365, including its:

    1. ID, project ID, title,
    2. content, description, status, priority,
    3. due date, start date, completed time,
    4. all-day flag, time zone, tags, sort order,
    5. repeat rule, task kind, subtask items,
    6. raw API response data.
    """

    id: str
    project_id: str
    title: str
    content: str = ""
    desc: str = ""
    status: int | None = None
    priority: int | None = None
    due_date: str = ""
    start_date: str = ""
    completed_time: str = ""
    is_all_day: bool = False
    time_zone: str = ""
    tags: list[str] = field(default_factory=list)
    sort_order: int = 0
    repeat_flag: str = ""
    kind: str = ""
    items: list[ChecklistItem] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DidaTask:
        """Build a DidaTask from API response data.

        This function constructs a DidaTask instance from the provided API
        response data.

        Args:
            data: The API response data.

        Returns:
            A DidaTask instance.
        """
        items_raw = data.get("items", [])
        items = (
            [
                ChecklistItem.from_api(i)
                for i in items_raw
                if isinstance(i, dict)
            ]
            if isinstance(items_raw, list)
            else []
        )
        return cls(
            id=str(data.get("id", "") or ""),
            project_id=str(data.get("projectId", "") or ""),
            title=str(data.get("title", "") or ""),
            content=str(data.get("content", "") or ""),
            desc=str(data.get("desc", "") or ""),
            status=_to_optional_int(data.get("status")),
            priority=_to_optional_int(data.get("priority")),
            due_date=str(data.get("dueDate", "") or ""),
            start_date=str(data.get("startDate", "") or ""),
            completed_time=str(data.get("completedTime", "") or ""),
            is_all_day=bool(data.get("isAllDay", False)),
            time_zone=str(data.get("timeZone", "") or ""),
            tags=data.get("tags", [])
            if isinstance(data.get("tags"), list)
            else [],
            sort_order=int(data.get("sortOrder", 0) or 0),
            repeat_flag=str(data.get("repeatFlag", "") or ""),
            kind=str(data.get("kind", "") or ""),
            items=items,
            raw=data,
        )


@dataclass(slots=True)
class DidaProjectData:
    """Project data with its tasks.

    This class represents a Dida365 project along with its associated tasks. It
    includes the project instance, a list of tasks, the project columns, and
    the raw API response data.
    """

    project: DidaProject | None
    tasks: list[DidaTask]
    columns: list[dict] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DidaProjectData:
        """Build a DidaProjectData from API response data.

        Args:
            data: The API response dict containing a ``project``
                object and a ``tasks`` array.

        Returns:
            A ``DidaProjectData`` instance.
        """
        project_data = data.get("project")
        project = (
            DidaProject.from_api(project_data)
            if isinstance(project_data, dict)
            else None
        )
        tasks_raw = data.get("tasks", [])
        tasks = [DidaTask.from_api(t) for t in tasks_raw if isinstance(t, dict)]
        columns_raw = data.get("columns", [])
        columns = [c for c in columns_raw if isinstance(c, dict)]
        return cls(
            project=project,
            tasks=tasks,
            columns=columns,
            raw=data,
        )


@dataclass(slots=True)
class DidaTaskWithProject:
    """A task with its project context.

    This class represents a Dida365 task along with its associated project
    information. It includes the project ID, project name, and the task
    instance.
    """

    project_id: str
    project_name: str
    task: DidaTask


def _to_optional_int(value: Any) -> int | None:
    """Convert a value to an optional integer.

    This function is an internal utility to convert a given value to an integer
    if possible.

    - If the value is None or an empty string, it returns None.
    - If the value cannot be converted to an integer, it also returns None.

    Args:
        value: The value to convert.

    Returns:
        Integer value, or None if the value is empty or invalid.

    See Also:
        `DidaTask.from_api`: Uses this function to parse status and priority
        fields.
    """
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
