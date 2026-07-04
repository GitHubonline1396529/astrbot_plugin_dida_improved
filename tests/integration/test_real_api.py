from __future__ import annotations

import os

import pytest
from astrbot_plugin_dida_improved.client import DidaClient
from astrbot_plugin_dida_improved.models import DidaPluginSettings
from astrbot_plugin_dida_improved.service import DidaService
from dotenv import load_dotenv

load_dotenv()

_DIDA_TOKEN = os.environ.get("DIDA_ACCESS_TOKEN")
_DIDA_BASE_URL = os.environ.get(
    "DIDA_BASE_URL", "https://api.dida365.com/open/v1"
)

requires_dida_token = pytest.mark.skipif(
    not _DIDA_TOKEN,
    reason="DIDA_ACCESS_TOKEN environment variable not set",
)


@requires_dida_token
async def test_list_projects():
    settings = DidaPluginSettings(
        access_token=_DIDA_TOKEN,
        api_base_url=_DIDA_BASE_URL,
        default_project="",
        request_timeout_seconds=30,
        timezone="Asia/Shanghai",
    )
    client = DidaClient(settings)
    projects = await client.list_projects()
    assert len(projects) >= 1
    assert all(p.id for p in projects)


@requires_dida_token
async def test_get_inbox_tasks():
    settings = DidaPluginSettings(
        access_token=_DIDA_TOKEN,
        api_base_url=_DIDA_BASE_URL,
        default_project="",
        request_timeout_seconds=30,
        timezone="Asia/Shanghai",
    )
    client = DidaClient(settings)
    tasks = await client.get_inbox_tasks()
    assert isinstance(tasks, list)


@requires_dida_token
async def test_probe_read_access():
    settings = DidaPluginSettings(
        access_token=_DIDA_TOKEN,
        api_base_url=_DIDA_BASE_URL,
        default_project="",
        request_timeout_seconds=30,
        timezone="Asia/Shanghai",
    )
    service = DidaService(settings)
    result = await service.probe_read_access()
    assert "successful" in result
