from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from astrbot_plugin_dida_improved.client import DidaClient
from astrbot_plugin_dida_improved.exceptions import (
    DidaApiError,
    DidaValidationError,
)
from astrbot_plugin_dida_improved.models import (
    DidaPluginSettings,
    DidaProject,
    DidaProjectData,
    DidaTask,
    DidaTaskWithProject,
)
from astrbot_plugin_dida_improved.service import DidaService


@pytest.fixture
def settings() -> DidaPluginSettings:
    return DidaPluginSettings(
        access_token="token",
        api_base_url="https://api.dida365.com/open/v1",
        default_project="",
        request_timeout_seconds=15,
        timezone="Asia/Shanghai",
    )


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock(spec=DidaClient)


@pytest.fixture
def service(settings, mock_client) -> DidaService:
    return DidaService(settings, client=mock_client)


@pytest.fixture
def sample_dida_projects() -> list[DidaProject]:
    return [
        DidaProject(id="p1", name="Work"),
        DidaProject(id="p2", name="Personal"),
    ]


@pytest.fixture
def sample_dida_tasks() -> list[DidaTask]:
    return [
        DidaTask(
            id="t1",
            project_id="p1",
            title="Overdue task",
            status=0,
            priority=3,
            due_date="2026-07-01T10:00:00+08:00",
            start_date="",
            completed_time="",
            is_all_day=False,
            time_zone="Asia/Shanghai",
            tags=[],
            sort_order=0,
        ),
        DidaTask(
            id="t2",
            project_id="p1",
            title="Due today task",
            status=0,
            priority=5,
            due_date="2026-07-04T10:00:00+08:00",
            start_date="",
            completed_time="",
            is_all_day=False,
            time_zone="Asia/Shanghai",
            tags=[],
            sort_order=0,
        ),
        DidaTask(
            id="t3",
            project_id="p2",
            title="No due date",
            status=0,
            priority=1,
            due_date="",
            start_date="",
            completed_time="",
            is_all_day=False,
            time_zone="",
            tags=[],
            sort_order=0,
        ),
        DidaTask(
            id="t4",
            project_id="p1",
            title="Completed task",
            status=1,
            priority=0,
            due_date="2026-07-04T10:00:00+08:00",
            start_date="",
            completed_time="2026-07-03T15:00:00Z",
            is_all_day=False,
            time_zone="Asia/Shanghai",
            tags=[],
            sort_order=0,
        ),
    ]


@pytest.fixture
def sample_project_data_list(
    sample_dida_projects, sample_dida_tasks
) -> list[DidaProjectData]:
    p1_tasks = [t for t in sample_dida_tasks if t.project_id == "p1"]
    p2_tasks = [t for t in sample_dida_tasks if t.project_id == "p2"]
    return [
        DidaProjectData(
            project=DidaProject(id="p1", name="Work"),
            tasks=p1_tasks,
        ),
        DidaProjectData(
            project=DidaProject(id="p2", name="Personal"),
            tasks=p2_tasks,
        ),
    ]


class TestBuildStatusSummary:
    def test_with_token(self, service):
        result = service.build_status_summary()
        assert "Access token configured: True" in result

    def test_without_token(self, settings):
        s = DidaPluginSettings(
            access_token="",
            api_base_url="https://api.dida365.com/open/v1",
            default_project="",
            request_timeout_seconds=15,
            timezone="Asia/Shanghai",
        )
        svc = DidaService(s, client=MagicMock(spec=DidaClient))
        result = svc.build_status_summary()
        assert "Access token configured: False" in result


class TestProbeReadAccess:
    async def test_no_projects(self, service, mock_client):
        mock_client.list_projects = AsyncMock(return_value=[])
        result = await service.probe_read_access()
        assert "returned no projects" in result

    async def test_with_projects(
        self, service, mock_client, sample_dida_projects
    ):
        mock_client.list_projects = AsyncMock(return_value=sample_dida_projects)
        result = await service.probe_read_access()
        assert "successful" in result
        assert "Project count: 2" in result

    async def test_many_projects(self, service, mock_client):
        many = [DidaProject(id=str(i), name=f"Project {i}") for i in range(10)]
        mock_client.list_projects = AsyncMock(return_value=many)
        result = await service.probe_read_access()
        assert "..." in result


class TestListProjectsSummary:
    async def test_no_projects(self, service, mock_client):
        mock_client.list_projects = AsyncMock(return_value=[])
        result = await service.list_projects_summary()
        assert result == "No Dida365 projects found."

    async def test_with_projects(
        self, service, mock_client, sample_dida_projects
    ):
        mock_client.list_projects = AsyncMock(return_value=sample_dida_projects)
        result = await service.list_projects_summary()
        assert "Work" in result
        assert "Inbox" in result
        assert "Dida365 projects: 2" in result


class TestCollectAllTasks:
    async def test_all_tasks_collected(
        self,
        service,
        mock_client,
        sample_dida_projects,
        sample_project_data_list,
    ):
        mock_client.list_projects = AsyncMock(return_value=sample_dida_projects)
        mock_client.get_project_data = AsyncMock(
            side_effect=sample_project_data_list
        )
        mock_client.get_inbox_tasks = AsyncMock(return_value=[])

        items = await service._collect_all_tasks()
        assert len(items) == 4
        assert items[0].task.id == "t1"
        assert items[0].project_name == "Work"

    async def test_no_projects(self, service, mock_client):
        mock_client.list_projects = AsyncMock(return_value=[])
        items = await service._collect_all_tasks()
        assert items == []

    async def test_project_failure_continues(
        self,
        service,
        mock_client,
        sample_dida_projects,
        sample_project_data_list,
    ):
        mock_client.list_projects = AsyncMock(return_value=sample_dida_projects)
        mock_client.get_project_data = AsyncMock(
            side_effect=[Exception("boom"), sample_project_data_list[1]]
        )
        mock_client.get_inbox_tasks = AsyncMock(return_value=[])

        items = await service._collect_all_tasks()
        assert len(items) == 1
        assert items[0].project_name == "Personal"

    async def test_inbox_failure_continues(
        self,
        service,
        mock_client,
        sample_dida_projects,
        sample_project_data_list,
    ):
        mock_client.list_projects = AsyncMock(return_value=sample_dida_projects)
        mock_client.get_project_data = AsyncMock(
            side_effect=sample_project_data_list
        )
        mock_client.get_inbox_tasks = AsyncMock(
            side_effect=Exception("inbox boom")
        )

        items = await service._collect_all_tasks()
        assert len(items) == 4  # inbox failure silently ignored


class TestListTodayTasks:
    async def test_no_tasks_due_today(
        self,
        service,
        mock_client,
        sample_dida_projects,
        sample_project_data_list,
    ):
        mock_client.list_projects = AsyncMock(return_value=sample_dida_projects)
        mock_client.get_project_data = AsyncMock(
            side_effect=sample_project_data_list
        )
        mock_client.get_inbox_tasks = AsyncMock(return_value=[])

        today = date(2026, 7, 5)
        items = await service.list_today_tasks(today=today)
        overdue = [i for i in items if service._is_overdue(i.task)]
        assert len(overdue) == 0  # no tasks due today

    async def test_tasks_due_today(
        self,
        service,
        mock_client,
        sample_dida_projects,
        sample_project_data_list,
    ):
        mock_client.list_projects = AsyncMock(return_value=sample_dida_projects)
        mock_client.get_project_data = AsyncMock(
            side_effect=sample_project_data_list
        )
        mock_client.get_inbox_tasks = AsyncMock(return_value=[])

        today = date(2026, 7, 4)
        items = await service.list_today_tasks(today=today)
        task_ids = [i.task.id for i in items]
        assert "t2" in task_ids  # due today
        assert "t4" not in task_ids  # completed

    async def test_today_tasks_summary_no_tasks(self, service, mock_client):
        mock_client.list_projects = AsyncMock(return_value=[])
        result = await service.list_today_tasks_summary()
        assert "No tasks due today" in result


class TestListUnfinishedTasks:
    async def test_all_unfinished(
        self,
        service,
        mock_client,
        sample_dida_projects,
        sample_project_data_list,
    ):
        mock_client.list_projects = AsyncMock(return_value=sample_dida_projects)
        mock_client.get_project_data = AsyncMock(
            side_effect=sample_project_data_list
        )
        mock_client.get_inbox_tasks = AsyncMock(return_value=[])

        items = await service.list_unfinished_tasks()
        task_ids = [i.task.id for i in items]
        assert "t4" not in task_ids  # completed
        assert "t1" in task_ids  # overdue
        assert "t2" in task_ids  # due today
        assert "t3" in task_ids  # no due date

    async def test_sort_order(
        self,
        service,
        mock_client,
        sample_dida_projects,
        sample_project_data_list,
    ):
        mock_client.list_projects = AsyncMock(return_value=sample_dida_projects)
        mock_client.get_project_data = AsyncMock(
            side_effect=sample_project_data_list
        )
        mock_client.get_inbox_tasks = AsyncMock(return_value=[])

        items = await service.list_unfinished_tasks()
        ids = [i.task.id for i in items]
        # t1 (overdue) first, then t2 (due today), then t3 (no due date)
        assert ids == ["t1", "t2", "t3"]

    async def test_unfinished_summary_no_tasks(self, service, mock_client):
        mock_client.list_projects = AsyncMock(return_value=[])
        result = await service.list_unfinished_tasks_summary()
        assert result == "No unfinished tasks."


class TestIsCompleted:
    def test_status_two(self, service, sample_dida_tasks):
        t = DidaTask(
            id="t",
            project_id="p",
            title="T",
            status=2,
        )
        assert service._is_completed(t) is True

    def test_has_completed_time_but_status_zero(
        self, service, sample_dida_tasks
    ):
        """Task with status=0 and stale completed_time is NOT completed."""
        t = DidaTask(
            id="t",
            project_id="p",
            title="T",
            status=0,
            completed_time="2026-07-03T15:00:00Z",
        )
        assert service._is_completed(t) is False

    def test_not_completed(self, service, sample_dida_tasks):
        t = DidaTask(
            id="t",
            project_id="p",
            title="T",
            status=0,
            completed_time="",
        )
        assert service._is_completed(t) is False


class TestIsOverdue:
    def test_overdue_task(self, service):
        t = DidaTask(
            id="t",
            project_id="p",
            title="T",
            status=0,
            due_date="2026-07-01T10:00:00+08:00",
            completed_time="",
            is_all_day=False,
            time_zone="Asia/Shanghai",
        )
        today = date(2026, 7, 4)
        assert service._is_overdue(t, today=today) is True

    def test_future_task(self, service):
        t = DidaTask(
            id="t",
            project_id="p",
            title="T",
            status=0,
            due_date="2026-07-10T10:00:00+08:00",
            completed_time="",
            is_all_day=False,
            time_zone="Asia/Shanghai",
        )
        today = date(2026, 7, 4)
        assert service._is_overdue(t, today=today) is False

    def test_completed_task_not_overdue(self, service):
        t = DidaTask(
            id="t",
            project_id="p",
            title="T",
            status=1,
            due_date="2026-07-01T10:00:00+08:00",
            completed_time="2026-07-03T15:00:00Z",
            is_all_day=False,
            time_zone="Asia/Shanghai",
        )
        today = date(2026, 7, 4)
        assert service._is_overdue(t, today=today) is False

    def test_no_due_date(self, service):
        t = DidaTask(
            id="t",
            project_id="p",
            title="T",
            status=0,
            due_date="",
            completed_time="",
        )
        assert service._is_overdue(t) is False


class TestFormatSingleTask:
    def test_basic(self, service):
        item = DidaTaskWithProject(
            project_id="p1",
            project_name="Work",
            task=DidaTask(
                id="t1",
                project_id="p1",
                title="Test task",
                status=0,
                priority=3,
                due_date="2026-07-04T10:00:00+08:00",
                is_all_day=False,
                time_zone="Asia/Shanghai",
            ),
        )
        result = service._format_single_task(item)
        assert "[t1]" in result
        assert "Test task" in result
        assert "Work" in result
        assert "medium" in result

    def test_with_overdue(self, service):
        item = DidaTaskWithProject(
            project_id="p1",
            project_name="Work",
            task=DidaTask(
                id="t1",
                project_id="p1",
                title="Overdue",
                status=0,
                priority=5,
                due_date="2026-07-01T10:00:00+08:00",
                is_all_day=False,
                time_zone="Asia/Shanghai",
            ),
        )
        result = service._format_single_task(item, include_overdue=True)
        assert "Overdue: Yes" in result
        assert "high" in result

    def test_with_index(self, service):
        item = DidaTaskWithProject(
            project_id="p1",
            project_name="Work",
            task=DidaTask(id="t1", project_id="p1", title="T"),
        )
        result = service._format_single_task(item, index=5)
        assert "5. " in result


class TestExplainError:
    def test_dida_error(self, service):
        error = DidaApiError("API error", status=400)
        result = service.explain_error(error)
        assert result == "API error"

    def test_generic_exception(self, service):
        error = RuntimeError("something broke")
        result = service.explain_error(error)
        assert "Unexpected" in result

    def test_configuration_error(self, service):
        from astrbot_plugin_dida_improved.exceptions import (
            DidaConfigurationError,
        )

        error = DidaConfigurationError("missing config")
        result = service.explain_error(error)
        assert result == "missing config"


class TestUpdateTaskDetails:
    async def test_success(self, service, mock_client):
        raw = {"id": "t1", "title": "Old title", "content": "Old notes"}
        task = DidaTask(
            id="t1",
            project_id="p1",
            title="Old title",
            content="Old notes",
            raw=raw,
        )
        found = DidaTaskWithProject(
            project_id="p1", project_name="Work", task=task
        )
        service.find_task_by_id = AsyncMock(return_value=found)

        updated_task = DidaTask(
            id="t1",
            project_id="p1",
            title="New title",
            content="Old notes",
        )
        mock_client.update_task = AsyncMock(return_value=updated_task)

        result = await service.update_task_details("t1", {"title": "New title"})

        assert "t1" in result
        assert "New title" in result
        assert "title" in result
        mock_client.update_task.assert_awaited_once_with(
            "t1", {"id": "t1", "title": "New title", "content": "Old notes"}
        )

    async def test_not_found_raises(self, service, mock_client):
        service.find_task_by_id = AsyncMock(return_value=None)

        with pytest.raises(DidaValidationError, match="not found"):
            await service.update_task_details("nonexistent", {"title": "X"})

    async def test_reminders_stripped(self, service, mock_client):
        raw = {
            "id": "t1",
            "title": "T",
            "reminders": [{"minutes": 30}],
        }
        task = DidaTask(id="t1", project_id="p1", title="T", raw=raw)
        found = DidaTaskWithProject(
            project_id="p1", project_name="W", task=task
        )
        service.find_task_by_id = AsyncMock(return_value=found)
        mock_client.update_task = AsyncMock(
            return_value=DidaTask(id="t1", project_id="p1", title="T")
        )

        await service.update_task_details("t1", {"title": "T"})

        call_args = mock_client.update_task.await_args
        assert call_args is not None
        payload = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
        assert "reminders" not in payload

    async def test_fields_merged(self, service, mock_client):
        raw = {
            "id": "t1",
            "title": "Old",
            "content": "Old",
            "dueDate": "2026-07-05",
        }
        task = DidaTask(id="t1", project_id="p1", title="Old", raw=raw)
        found = DidaTaskWithProject(
            project_id="p1", project_name="W", task=task
        )
        service.find_task_by_id = AsyncMock(return_value=found)
        mock_client.update_task = AsyncMock(
            return_value=DidaTask(id="t1", project_id="p1", title="New")
        )

        await service.update_task_details("t1", {"title": "New", "priority": 5})

        call_args = mock_client.update_task.await_args
        assert call_args is not None
        payload = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
        assert payload["title"] == "New"
        assert payload["content"] == "Old"
        assert payload["dueDate"] == "2026-07-05"
        assert payload["priority"] == 5

    async def test_raw_empty_fallback(self, service, mock_client):
        task = DidaTask(
            id="t1",
            project_id="p1",
            title="T",
            content="C",
            status=0,
            priority=3,
            due_date="2026-07-05",
            time_zone="Asia/Shanghai",
            tags=["a"],
            sort_order=0,
            raw={},
        )
        found = DidaTaskWithProject(
            project_id="p1", project_name="W", task=task
        )
        service.find_task_by_id = AsyncMock(return_value=found)
        mock_client.update_task = AsyncMock(
            return_value=DidaTask(id="t1", project_id="p1", title="T")
        )

        await service.update_task_details("t1", {"title": "T"})

        call_args = mock_client.update_task.await_args
        assert call_args is not None
        payload = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
        assert payload.get("title") == "T"
        assert payload.get("priority") == 3
        assert payload.get("tags") == ["a"]


class TestCreateTask:
    async def test_success_with_title_only(self, service, mock_client):
        created = DidaTask(id="t1", project_id="p1", title="New task")
        mock_client.create_task = AsyncMock(return_value=created)

        result = await service.create_task(title="New task")

        assert "t1" in result
        assert "New task" in result
        mock_client.create_task.assert_awaited_once_with({"title": "New task"})

    async def test_success_with_project_id(self, service, mock_client):
        created = DidaTask(id="t1", project_id="p1", title="New task")
        mock_client.create_task = AsyncMock(return_value=created)

        result = await service.create_task(title="New task", project_id="p1")

        assert "t1" in result
        mock_client.create_task.assert_awaited_once_with(
            {"title": "New task", "projectId": "p1"}
        )

    async def test_success_with_all_fields(self, service, mock_client):
        created = DidaTask(id="t1", project_id="p1", title="New task")
        mock_client.create_task = AsyncMock(return_value=created)

        result = await service.create_task(
            title="New task",
            project_id="p1",
            content="Notes",
            priority=3,
            tags="work,urgent",
            due_date="2026-07-10T18:00:00+08:00",
        )

        assert isinstance(result, str)
        mock_client.create_task.assert_awaited_once_with(
            {
                "title": "New task",
                "projectId": "p1",
                "content": "Notes",
                "priority": 3,
                "tags": ["work", "urgent"],
                "dueDate": "2026-07-10T18:00:00+08:00",
            }
        )

    async def test_empty_title_raises(self, service, mock_client):
        with pytest.raises(DidaValidationError, match="cannot be empty"):
            await service.create_task(title="")

    async def test_whitespace_title_raises(self, service, mock_client):
        with pytest.raises(DidaValidationError, match="cannot be empty"):
            await service.create_task(title="   ")


class TestCompleteTask:
    async def test_success(self, service, mock_client):
        task = DidaTask(id="t1", project_id="p1", title="Buy milk")
        found = DidaTaskWithProject(
            project_id="p1", project_name="Work", task=task
        )
        service.find_task_by_id = AsyncMock(return_value=found)
        mock_client.complete_task = AsyncMock()

        result = await service.complete_task("t1")

        assert "t1" in result
        assert "completed" in result
        mock_client.complete_task.assert_awaited_once_with("p1", "t1")

    async def test_not_found_raises(self, service, mock_client):
        service.find_task_by_id = AsyncMock(return_value=None)

        with pytest.raises(DidaValidationError, match="not found"):
            await service.complete_task("nonexistent")


class TestDeleteTask:
    async def test_success(self, service, mock_client):
        task = DidaTask(id="t1", project_id="p1", title="Buy milk")
        found = DidaTaskWithProject(
            project_id="p1", project_name="Work", task=task
        )
        service.find_task_by_id = AsyncMock(return_value=found)
        mock_client.delete_task = AsyncMock()

        result = await service.delete_task("t1")

        assert "t1" in result
        assert "deleted" in result
        mock_client.delete_task.assert_awaited_once_with("p1", "t1")

    async def test_not_found_raises(self, service, mock_client):
        service.find_task_by_id = AsyncMock(return_value=None)

        with pytest.raises(DidaValidationError, match="not found"):
            await service.delete_task("nonexistent")
