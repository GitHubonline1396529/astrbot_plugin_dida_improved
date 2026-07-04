from __future__ import annotations

from astrbot_plugin_dida_improved.models import (
    DidaPluginSettings,
    DidaProject,
    DidaProjectData,
    DidaTask,
    DidaTaskWithProject,
    _to_optional_int,
)


class TestToOptionalInt:
    def test_none(self):
        assert _to_optional_int(None) is None

    def test_empty_string(self):
        assert _to_optional_int("") is None

    def test_valid_int(self):
        assert _to_optional_int(3) == 3

    def test_valid_string(self):
        assert _to_optional_int("5") == 5

    def test_zero(self):
        assert _to_optional_int(0) == 0

    def test_invalid_string(self):
        assert _to_optional_int("abc") is None


class TestDidaProjectFromApi:
    def test_full_fields(self, sample_projects_raw):
        raw = sample_projects_raw[0]
        proj = DidaProject.from_api(raw)
        assert proj.id == "proj1"
        assert proj.name == "Work"
        assert proj.kind == "TASK"
        assert proj.color == "#1890ff"
        assert proj.view_mode == "list"
        assert proj.closed is False
        assert proj.group_id == ""

    def test_missing_fields(self):
        raw = {"id": "proj3"}
        proj = DidaProject.from_api(raw)
        assert proj.id == "proj3"
        assert proj.name == ""
        assert proj.closed is False

    def test_empty_dict(self):
        proj = DidaProject.from_api({})
        assert proj.id == ""
        assert proj.name == ""


class TestDidaTaskFromApi:
    def test_full_fields(self, sample_tasks_raw):
        raw = sample_tasks_raw[0]
        task = DidaTask.from_api(raw)
        assert task.id == "task1"
        assert task.project_id == "proj1"
        assert task.title == "Buy groceries"
        assert task.content == "Milk, eggs, bread"
        assert task.status == 0
        assert task.priority == 3
        assert task.due_date == "2026-07-04T10:00:00+08:00"
        assert task.is_all_day is False
        assert task.time_zone == "Asia/Shanghai"
        assert task.tags == ["shopping"]
        assert task.sort_order == 0

    def test_completed_task(self, sample_tasks_raw):
        raw = sample_tasks_raw[2]
        task = DidaTask.from_api(raw)
        assert task.status == 2
        assert task.priority == 1

    def test_no_status(self):
        raw = {"id": "t1", "projectId": "p1", "title": "No status"}
        task = DidaTask.from_api(raw)
        assert task.status is None
        assert task.priority is None

    def test_status_zero(self):
        raw = {"id": "t1", "projectId": "p1", "title": "T", "status": 0}
        task = DidaTask.from_api(raw)
        assert task.status == 0

    def test_empty_tags(self):
        raw = {"id": "t1", "projectId": "p1", "title": "T", "tags": None}
        task = DidaTask.from_api(raw)
        assert task.tags == []

    def test_non_list_tags(self):
        raw = {"id": "t1", "projectId": "p1", "title": "T", "tags": "invalid"}
        task = DidaTask.from_api(raw)
        assert task.tags == []

    def test_all_day_flag(self):
        raw = {"id": "t1", "projectId": "p1", "title": "T", "isAllDay": True}
        task = DidaTask.from_api(raw)
        assert task.is_all_day is True


class TestDidaProjectDataFromApi:
    def test_with_project(self, sample_project_data_raw):
        data = DidaProjectData.from_api(sample_project_data_raw)
        assert data.project is not None
        assert data.project.id == "proj1"
        assert len(data.tasks) == 3

    def test_no_project(self, empty_project_data_raw):
        data = DidaProjectData.from_api(empty_project_data_raw)
        assert data.project is None
        assert data.tasks == []


class TestDidaTaskWithProject:
    def test_creation(self, sample_tasks):
        twp = DidaTaskWithProject(
            project_id="proj1",
            project_name="Work",
            task=sample_tasks[0],
        )
        assert twp.project_id == "proj1"
        assert twp.project_name == "Work"
        assert twp.task.id == "task1"


class TestDidaPluginSettingsFromConfig:
    def test_full_config(self, mock_config):
        settings = DidaPluginSettings.from_config(mock_config)
        assert settings.access_token == "test_token_123"
        assert settings.api_base_url == "https://api.dida365.com/open/v1"
        assert settings.default_project == ""
        assert settings.request_timeout_seconds == 15
        assert settings.timezone == "Asia/Shanghai"

    def test_empty_token(self):
        settings = DidaPluginSettings.from_config({"access_token": None})
        assert settings.access_token == ""

    def test_timeout_minimum_clamps_low_values(self):
        settings = DidaPluginSettings.from_config(
            {"request_timeout_seconds": 0}
        )
        # 0 is falsy, so the default 15 kicks in first
        assert settings.request_timeout_seconds == 15

        settings = DidaPluginSettings.from_config(
            {"request_timeout_seconds": -5}
        )
        assert settings.request_timeout_seconds == 1

    def test_timeout_negative(self):
        settings = DidaPluginSettings.from_config(
            {"request_timeout_seconds": -5}
        )
        assert settings.request_timeout_seconds == 1

    def test_fallback_timezone(self):
        settings = DidaPluginSettings.from_config({})
        assert settings.timezone == "Asia/Shanghai"

    def test_custom_fallback_timezone(self):
        settings = DidaPluginSettings.from_config(
            {}, fallback_timezone="America/New_York"
        )
        assert settings.timezone == "America/New_York"
