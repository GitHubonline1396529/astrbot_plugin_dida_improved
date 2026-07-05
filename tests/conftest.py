from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root.parent))

# Add AstrBot core to path so the plugin can import astrbot.api.*
# The path is set via the ASTRBOT_CORE_PATH environment variable.
# Create a .env file in the project root (see .env.example) with:
#   ASTRBOT_CORE_PATH=/path/to/AstrBot/core
_astrbot_core_env = os.environ.get("ASTRBOT_CORE_PATH")
if _astrbot_core_env:
    _astrbot_core = Path(_astrbot_core_env)
    if not _astrbot_core.exists():
        raise RuntimeError(
            f"ASTRBOT_CORE_PATH={_astrbot_core_env} does not exist. "
            "Please check your .env file."
        )
    sys.path.insert(0, str(_astrbot_core))
else:
    raise RuntimeError(
        "ASTRBOT_CORE_PATH is not set. "
        "Create a .env file in the project root with:\n"
        "    ASTRBOT_CORE_PATH=/path/to/AstrBot/core\n"
        "See .env.example for a template."
    )

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
