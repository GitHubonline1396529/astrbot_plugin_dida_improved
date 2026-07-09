from __future__ import annotations

import logging
import sys
import types
from enum import Enum
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root.parent))


def _install_astrbot_stubs() -> None:
    """Install minimal AstrBot module stubs for testing.

    Covers the imports used by the plugin:
    - astrbot.api (AstrBotConfig, logger)
    - astrbot.api.event (AstrMessageEvent, filter)
    - astrbot.api.star (Context, Star, register)
    """

    def _identity_decorator(*args, **kwargs):
        return lambda func: func

    # --- astrbot ---
    astrbot = types.ModuleType("astrbot")
    astrbot.__path__ = []

    # --- astrbot.api ---
    api = types.ModuleType("astrbot.api")

    logger = logging.getLogger("astrbot-plugin-test")

    class AstrBotConfig:
        def __init__(self, data: dict | None = None) -> None:
            self._data = data or {}

        def get(self, key: str, default=None):
            return self._data.get(key, default)

    api.logger = logger
    api.AstrBotConfig = AstrBotConfig

    # --- astrbot.api.event ---
    event = types.ModuleType("astrbot.api.event")

    class AstrMessageEvent:
        def plain_result(self, message):
            return message

    event.AstrMessageEvent = AstrMessageEvent

    # --- astrbot.api.event.filter ---
    event_filter = types.ModuleType("astrbot.api.event.filter")

    class PermissionType(Enum):
        ADMIN = "admin"

    event_filter.PermissionType = PermissionType
    event_filter.permission_type = _identity_decorator
    event_filter.command = _identity_decorator
    event_filter.llm_tool = _identity_decorator

    event.filter = event_filter

    # --- astrbot.api.star ---
    star = types.ModuleType("astrbot.api.star")

    class Context:
        def get_config(self):
            return {}

    class Star:
        def __init__(self, context=None, config=None):
            self.context = context
            self.config = config

    def register(*args, **kwargs):
        return lambda cls: cls

    star.Context = Context
    star.Star = Star
    star.register = register

    # Register all modules in sys.modules
    sys.modules["astrbot"] = astrbot
    sys.modules["astrbot.api"] = api
    sys.modules["astrbot.api.event"] = event
    sys.modules["astrbot.api.event.filter"] = event_filter
    sys.modules["astrbot.api.star"] = star


_install_astrbot_stubs()

from astrbot_plugin_dida_improved.models import (  # noqa: E402
    DidaPluginSettings,
    DidaProject,
    DidaProjectData,
    DidaTask,
)


@pytest.fixture
def mock_config() -> dict:
    return {
        "access_token": "test_token_123",
        "api_base_url": "https://api.dida365.com/open/v1",
        "default_project": "",
        "timezone": "Asia/Shanghai",
        "request_timeout_seconds": 15,
    }


@pytest.fixture
def sample_projects_raw() -> list[dict]:
    return [
        {
            "id": "proj1",
            "name": "Work",
            "kind": "TASK",
            "color": "#1890ff",
            "viewMode": "list",
            "closed": False,
            "groupId": "",
        },
        {
            "id": "proj2",
            "name": "Personal",
            "kind": "TASK",
            "color": "#52c41a",
            "viewMode": "list",
            "closed": False,
            "groupId": "",
        },
    ]


@pytest.fixture
def sample_projects(sample_projects_raw) -> list[DidaProject]:
    return [DidaProject.from_api(p) for p in sample_projects_raw]


@pytest.fixture
def sample_tasks_raw() -> list[dict]:
    return [
        {
            "id": "task1",
            "projectId": "proj1",
            "title": "Buy groceries",
            "content": "Milk, eggs, bread",
            "desc": "",
            "status": 0,
            "priority": 3,
            "dueDate": "2026-07-04T10:00:00+08:00",
            "startDate": "",
            "completedTime": "",
            "isAllDay": False,
            "timeZone": "Asia/Shanghai",
            "tags": ["shopping"],
            "sortOrder": 0,
        },
        {
            "id": "task2",
            "projectId": "proj1",
            "title": "Write report",
            "content": "",
            "desc": "",
            "status": 0,
            "priority": 5,
            "dueDate": "2026-07-03T18:00:00+08:00",
            "startDate": "",
            "completedTime": "",
            "isAllDay": False,
            "timeZone": "Asia/Shanghai",
            "tags": [],
            "sortOrder": 0,
        },
        {
            "id": "task3",
            "projectId": "proj2",
            "title": "Read book",
            "content": "",
            "desc": "",
            "status": 2,
            "priority": 1,
            "dueDate": "",
            "startDate": "",
            "completedTime": "",
            "isAllDay": False,
            "timeZone": "",
            "tags": [],
            "sortOrder": 0,
        },
    ]


@pytest.fixture
def sample_tasks(sample_tasks_raw) -> list[DidaTask]:
    return [DidaTask.from_api(t) for t in sample_tasks_raw]


@pytest.fixture
def sample_project_data_raw(sample_projects_raw, sample_tasks_raw) -> dict:
    return {
        "project": sample_projects_raw[0],
        "tasks": sample_tasks_raw,
    }


@pytest.fixture
def sample_project_data(sample_project_data_raw) -> DidaProjectData:
    return DidaProjectData.from_api(sample_project_data_raw)


@pytest.fixture
def empty_project_data_raw() -> dict:
    return {
        "project": None,
        "tasks": [],
    }


@pytest.fixture
def dida_settings(mock_config) -> DidaPluginSettings:
    return DidaPluginSettings.from_config(mock_config)
