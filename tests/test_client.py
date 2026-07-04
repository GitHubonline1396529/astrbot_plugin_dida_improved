from __future__ import annotations

import httpx
import pytest
import respx
from astrbot_plugin_dida_improved.client import DidaClient
from astrbot_plugin_dida_improved.exceptions import (
    DidaApiError,
    DidaAuthenticationError,
    DidaConfigurationError,
    DidaNetworkError,
    DidaNotFoundError,
)
from astrbot_plugin_dida_improved.models import DidaPluginSettings


@pytest.fixture
def settings() -> DidaPluginSettings:
    return DidaPluginSettings(
        access_token="test_token",
        api_base_url="https://api.dida365.com/open/v1",
        default_project="",
        request_timeout_seconds=15,
        timezone="Asia/Shanghai",
    )


@pytest.fixture
def client(settings) -> DidaClient:
    return DidaClient(settings)


class TestDidaClientInit:
    def test_empty_token_raises(self):
        settings = DidaPluginSettings(
            access_token="",
            api_base_url="https://api.dida365.com/open/v1",
            default_project="",
            request_timeout_seconds=15,
            timezone="Asia/Shanghai",
        )
        with pytest.raises(DidaConfigurationError) as exc:
            DidaClient(settings)
        assert "access_token" in str(exc.value)

    def test_whitespace_token_is_accepted(self):
        settings = DidaPluginSettings(
            access_token="   ",
            api_base_url="https://api.dida365.com/open/v1",
            default_project="",
            request_timeout_seconds=15,
            timezone="Asia/Shanghai",
        )
        client = DidaClient(settings)
        assert client._headers["Authorization"] == "Bearer    "


class TestRequest:
    @pytest.mark.parametrize("status", [401, 403])
    async def test_auth_error(self, client, status):
        with respx.mock:
            respx.get("https://api.dida365.com/open/v1/test").respond(
                status_code=status, text="unauthorized"
            )
            with pytest.raises(DidaAuthenticationError):
                await client._request("GET", "/test")

    async def test_not_found(self, client):
        with respx.mock:
            respx.get("https://api.dida365.com/open/v1/test").respond(
                status_code=404, text="not found"
            )
            with pytest.raises(DidaNotFoundError):
                await client._request("GET", "/test")

    async def test_server_error(self, client):
        with respx.mock:
            respx.get("https://api.dida365.com/open/v1/test").respond(
                status_code=500, text="internal error"
            )
            with pytest.raises(DidaApiError) as exc:
                await client._request("GET", "/test")
            assert exc.value.status == 500

    async def test_timeout(self, client):
        with respx.mock:
            respx.get("https://api.dida365.com/open/v1/test").mock(
                side_effect=httpx.TimeoutException("timeout")
            )
            with pytest.raises(DidaNetworkError):
                await client._request("GET", "/test")

    async def test_connection_error(self, client):
        with respx.mock:
            respx.get("https://api.dida365.com/open/v1/test").mock(
                side_effect=httpx.ConnectError("connection refused")
            )
            with pytest.raises(DidaNetworkError):
                await client._request("GET", "/test")

    async def test_non_json_response(self, client):
        with respx.mock:
            respx.get("https://api.dida365.com/open/v1/test").respond(
                status_code=200, text="not json"
            )
            with pytest.raises(DidaApiError):
                await client._request("GET", "/test")

    async def test_empty_body(self, client):
        with respx.mock:
            respx.get("https://api.dida365.com/open/v1/test").respond(
                status_code=200, text=""
            )
            result = await client._request("GET", "/test")
            assert result == {}

    async def test_empty_body_whitespace(self, client):
        with respx.mock:
            respx.get("https://api.dida365.com/open/v1/test").respond(
                status_code=200, text="   "
            )
            result = await client._request("GET", "/test")
            assert result == {}

    async def test_valid_json(self, client):
        with respx.mock:
            respx.get("https://api.dida365.com/open/v1/test").respond(
                status_code=200, json={"key": "value"}
            )
            result = await client._request("GET", "/test")
            assert result == {"key": "value"}

    async def test_empty_base_url_raises(self):
        settings = DidaPluginSettings(
            access_token="token",
            api_base_url="",
            default_project="",
            request_timeout_seconds=15,
            timezone="Asia/Shanghai",
        )
        c = DidaClient(settings)
        with pytest.raises(DidaConfigurationError):
            await c._request("GET", "/test")


class TestListProjects:
    async def test_success(self, client, sample_projects_raw):
        with respx.mock:
            respx.get("https://api.dida365.com/open/v1/project").respond(
                status_code=200, json=sample_projects_raw
            )
            projects = await client.list_projects()
            assert len(projects) == 2
            assert projects[0].id == "proj1"
            assert projects[1].name == "Personal"

    async def test_non_list_response(self, client):
        with respx.mock:
            respx.get("https://api.dida365.com/open/v1/project").respond(
                status_code=200, json={"not": "list"}
            )
            with pytest.raises(DidaApiError):
                await client.list_projects()

    async def test_empty_list(self, client):
        with respx.mock:
            respx.get("https://api.dida365.com/open/v1/project").respond(
                status_code=200, json=[]
            )
            projects = await client.list_projects()
            assert projects == []


class TestGetProjectData:
    async def test_success(self, client, sample_project_data_raw):
        with respx.mock:
            respx.get(
                "https://api.dida365.com/open/v1/project/proj1/data"
            ).respond(status_code=200, json=sample_project_data_raw)
            data = await client.get_project_data("proj1")
            assert data.project is not None
            assert data.project.id == "proj1"
            assert len(data.tasks) == 3

    async def test_non_dict_response(self, client):
        with respx.mock:
            respx.get(
                "https://api.dida365.com/open/v1/project/proj1/data"
            ).respond(status_code=200, json=[1, 2, 3])
            with pytest.raises(DidaApiError):
                await client.get_project_data("proj1")


class TestGetInboxTasks:
    async def test_success(self, client, sample_tasks_raw):
        inbox_response = {"tasks": sample_tasks_raw}
        with respx.mock:
            respx.get(
                "https://api.dida365.com/open/v1/project/inbox/data"
            ).respond(status_code=200, json=inbox_response)
            tasks = await client.get_inbox_tasks()
            assert len(tasks) == 3
            assert tasks[0].id == "task1"

    async def test_empty_tasks(self, client):
        with respx.mock:
            respx.get(
                "https://api.dida365.com/open/v1/project/inbox/data"
            ).respond(status_code=200, json={"tasks": []})
            tasks = await client.get_inbox_tasks()
            assert tasks == []


class TestCreateTask:
    async def test_success(self, client, sample_tasks_raw):
        payload = {
            "title": "New task",
            "projectId": "proj1",
        }
        expected = {**sample_tasks_raw[0], "title": "New task"}
        with respx.mock:
            respx.post("https://api.dida365.com/open/v1/task").respond(
                status_code=200, json=expected
            )
            task = await client.create_task(payload)
            assert task.title == "New task"
            assert task.project_id == "proj1"

    async def test_non_dict_response(self, client):
        with respx.mock:
            respx.post("https://api.dida365.com/open/v1/task").respond(
                status_code=200, json="not dict"
            )
            with pytest.raises(DidaApiError):
                await client.create_task({"title": "T"})


class TestUpdateTask:
    async def test_success(self, client, sample_tasks_raw):
        task_id = "task1"
        payload = {"title": "Updated"}
        expected = {**sample_tasks_raw[0], "title": "Updated"}
        with respx.mock:
            respx.post(
                f"https://api.dida365.com/open/v1/task/{task_id}"
            ).respond(status_code=200, json=expected)
            task = await client.update_task(task_id, payload)
            assert task.title == "Updated"

    async def test_non_dict_response(self, client):
        with respx.mock:
            respx.post("https://api.dida365.com/open/v1/task/task1").respond(
                status_code=200, json="not dict"
            )
            with pytest.raises(DidaApiError):
                await client.update_task("task1", {"title": "T"})


class TestCompleteTask:
    async def test_success(self, client):
        with respx.mock:
            respx.post(
                "https://api.dida365.com/open/v1/project/p1/task/t1/complete"
            ).respond(status_code=200, json={})
            await client.complete_task("p1", "t1")

    async def test_empty_response(self, client):
        with respx.mock:
            respx.post(
                "https://api.dida365.com/open/v1/project/p1/task/t1/complete"
            ).respond(status_code=200, text="")
            await client.complete_task("p1", "t1")


class TestDeleteTask:
    async def test_success(self, client):
        with respx.mock:
            respx.delete(
                "https://api.dida365.com/open/v1/project/p1/task/t1"
            ).respond(status_code=200, json={})
            await client.delete_task("p1", "t1")

    async def test_empty_response(self, client):
        with respx.mock:
            respx.delete(
                "https://api.dida365.com/open/v1/project/p1/task/t1"
            ).respond(status_code=200, text="")
            await client.delete_task("p1", "t1")
