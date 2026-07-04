from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from astrbot_plugin_dida_improved.main import DidaImprovedPlugin
from astrbot_plugin_dida_improved.models import DidaPluginSettings
from astrbot_plugin_dida_improved.service import DidaService


class MockContext:
    def __init__(self, timezone: str = "Asia/Shanghai") -> None:
        self._mock_config = {"timezone": timezone}

    def get_config(self):
        return self._mock_config


class MockConfig(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@pytest.fixture
def plugin():
    context = MockContext()
    config = MockConfig(
        {
            "access_token": "test_token",
            "api_base_url": "https://api.dida365.com/open/v1",
            "default_project": "",
            "timezone": "Asia/Shanghai",
            "request_timeout_seconds": 15,
        }
    )
    return DidaImprovedPlugin(context, config)


class TestBuildSettings:
    def test_returns_dida_plugin_settings(self, plugin):
        settings = plugin._build_settings()
        assert isinstance(settings, DidaPluginSettings)
        assert settings.access_token == "test_token"
        assert settings.timezone == "Asia/Shanghai"

    def test_fallback_timezone_from_context(self):
        context = MockContext(timezone="America/New_York")
        config = MockConfig(
            {
                "access_token": "token",
                "api_base_url": "https://api.dida365.com/open/v1",
                "default_project": "",
                "request_timeout_seconds": 15,
            }
        )
        plugin = DidaImprovedPlugin(context, config)
        settings = plugin._build_settings()
        assert settings.timezone == "America/New_York"

    def test_no_timezone_anywhere(self):
        context = MockContext(timezone="")
        config = MockConfig(
            {
                "access_token": "token",
                "api_base_url": "https://api.dida365.com/open/v1",
                "default_project": "",
                "request_timeout_seconds": 15,
            }
        )
        plugin = DidaImprovedPlugin(context, config)
        settings = plugin._build_settings()
        assert settings.timezone == "Asia/Shanghai"


class TestBuildService:
    def test_returns_dida_service(self, plugin):
        service = plugin._build_service()
        assert isinstance(service, DidaService)


class TestRunService:
    async def test_success(self, plugin):
        result = await plugin._run_service(
            lambda service: service.probe_read_access()
        )
        assert isinstance(result, str)

    async def test_exception_handling(self, plugin):
        result = await plugin._run_service(
            lambda service: (_ for _ in ()).throw(RuntimeError("test error"))
        )
        assert "Unexpected" in result


class TestDidaPing:
    async def test_returns_status_summary(self, plugin):
        mock_event = MagicMock()
        mock_event.plain_result.return_value = "ping_result"
        gen = plugin.dida_ping(mock_event)
        result = await anext(gen)
        assert result == "ping_result"


class TestDidaProbe:
    async def test_returns_probe_result(self, plugin):
        gen = plugin.dida_probe(MagicMock())
        result = await anext(gen)
        assert result is not None


class TestListDidaProjectsLlm:
    async def test_returns_projects(self, plugin):
        result = await plugin.list_dida_projects_llm(MagicMock())
        assert isinstance(result, str)


class TestListDidaTasksLlm:
    async def test_today_filter(self, plugin):
        result = await plugin.list_dida_tasks_llm(MagicMock(), filter="today")
        assert isinstance(result, str)

    async def test_default_filter(self, plugin):
        result = await plugin.list_dida_tasks_llm(MagicMock())
        assert isinstance(result, str)

    async def test_unfinished_filter(self, plugin):
        result = await plugin.list_dida_tasks_llm(
            MagicMock(), filter="unfinished"
        )
        assert isinstance(result, str)


class TestUpdateDidaTaskLlm:
    async def test_valid_json(self, plugin):
        mock_event = MagicMock()
        result = await plugin.update_dida_task_llm(
            mock_event,
            task_id="t1",
            updates_json='{"title": "New title"}',
        )
        assert isinstance(result, str)

    async def test_malformed_json(self, plugin):
        mock_event = MagicMock()
        result = await plugin.update_dida_task_llm(
            mock_event,
            task_id="t1",
            updates_json="{bad json}",
        )
        assert "Invalid JSON" in result

    async def test_empty_updates(self, plugin):
        mock_event = MagicMock()
        result = await plugin.update_dida_task_llm(
            mock_event,
            task_id="t1",
            updates_json="",
        )
        assert "No updates" in result

    async def test_non_dict_json(self, plugin):
        mock_event = MagicMock()
        result = await plugin.update_dida_task_llm(
            mock_event,
            task_id="t1",
            updates_json='["not", "a", "dict"]',
        )
        assert "must be a JSON object" in result
