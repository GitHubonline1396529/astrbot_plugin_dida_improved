from __future__ import annotations

from typing import Any

import httpx
from astrbot.api import logger

from .exceptions import (
    DidaApiError,
    DidaAuthenticationError,
    DidaConfigurationError,
    DidaNetworkError,
    DidaNotFoundError,
)
from .models import DidaPluginSettings, DidaProject, DidaProjectData, DidaTask


class DidaClient:
    """HTTP client for the Dida365 Open API."""

    def __init__(self, settings: DidaPluginSettings) -> None:
        """Initialize the DidaClient.

        Args:
            settings: Plugin configuration containing the access token
                and API base URL.

        Raises:
            DidaConfigurationError: If the access token is empty.
        """
        self.settings = settings
        self._base_url = settings.api_base_url.strip().rstrip("/")
        self._headers = self._build_headers(settings)

    def _build_headers(self, settings: DidaPluginSettings) -> dict[str, str]:
        """Build the HTTP headers for API requests.

        Args:
            settings: Plugin configuration with the access token.

        Returns:
            Dict with ``Authorization`` and ``Content-Type`` headers.

        Raises:
            DidaConfigurationError: If the access token is empty.
        """
        if not settings.access_token:
            raise DidaConfigurationError(
                "Dida365 access_token is not configured."
            )
        return {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        """Build the full URL for an API request.

        Args:
            path: The API path (e.g. ``"/project"``).

        Returns:
            Full URL by joining the base URL and path.

        Raises:
            DidaConfigurationError: If the base URL is empty.
        """
        if not self._base_url:
            raise DidaConfigurationError(
                "Dida365 api_base_url is not configured."
            )
        return f"{self._base_url}/{path.lstrip('/')}"

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """Send an HTTP request to the Dida365 API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.).
            path: API path (e.g. "/project").
            json_body: Optional JSON body for POST/PUT requests.

        Returns:
            Parsed JSON response.

        Raises:
            DidaAuthenticationError: If the API returns 401 or 403.
            DidaNotFoundError: If the API returns 404.
            DidaApiError: For other API errors.
            DidaNetworkError: If the request fails.
        """
        url = self._url(path)
        timeout = httpx.Timeout(self.settings.request_timeout_seconds)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._headers,
                    json=json_body,
                    timeout=timeout,
                )
                body_text = response.text

                if response.status_code in (401, 403):
                    logger.error(
                        "Dida365 API %s %s status=%s body=%s",
                        method,
                        path,
                        response.status_code,
                        body_text[:500],
                    )
                    raise DidaAuthenticationError(
                        "Dida365 authentication failed. Token may have"
                        " expired.",
                        status=response.status_code,
                        payload=body_text[:500],
                    )

                if response.status_code == 404:
                    logger.error(
                        "Dida365 API %s %s status=%s body=%s",
                        method,
                        path,
                        response.status_code,
                        body_text[:500],
                    )
                    raise DidaNotFoundError(
                        "Dida365 resource not found.",
                        status=response.status_code,
                        payload=body_text[:500],
                    )

                if response.status_code >= 400:
                    logger.error(
                        "Dida365 API %s %s status=%s body=%s",
                        method,
                        path,
                        response.status_code,
                        body_text[:500],
                    )
                    raise DidaApiError(
                        f"Dida365 API error: {response.status_code}",
                        status=response.status_code,
                        payload=body_text[:500],
                    )

                if not body_text.strip():
                    return {}

                import json

                try:
                    return json.loads(body_text)
                except json.JSONDecodeError as exc:
                    raise DidaApiError(
                        "Dida365 API returned non-JSON response.",
                        status=response.status_code,
                        payload=body_text[:500],
                    ) from exc

        except httpx.TimeoutException as exc:
            raise DidaNetworkError("Dida365 API request timed out.") from exc
        except httpx.HTTPError as exc:
            raise DidaNetworkError(
                f"Dida365 API request failed: {exc!s}"
            ) from exc

    async def list_projects(self) -> list[DidaProject]:
        """Fetch all projects.

        Returns:
            List of DidaProject objects.
        """
        data = await self._request("GET", "/project")
        if not isinstance(data, list):
            raise DidaApiError("Unexpected project list response.")
        return [
            DidaProject.from_api(item)
            for item in data
            if isinstance(item, dict)
        ]

    async def get_project_data(self, project_id: str) -> DidaProjectData:
        """Fetch tasks for a specific project.

        Args:
            project_id: The project ID.

        Returns:
            DidaProjectData containing project info and tasks.
        """
        data = await self._request("GET", f"/project/{project_id}/data")
        if not isinstance(data, dict):
            raise DidaApiError("Unexpected project data response.")
        return DidaProjectData.from_api(data)

    async def get_inbox_tasks(self) -> list[DidaTask]:
        """Fetch tasks from the Inbox (collection).

        Returns:
            List of DidaTask objects from the Inbox.
        """
        data = await self._request("GET", "/project/inbox/data")
        if not isinstance(data, dict):
            raise DidaApiError("Unexpected inbox data response.")
        tasks_raw = data.get("tasks", [])
        return [DidaTask.from_api(t) for t in tasks_raw if isinstance(t, dict)]

    async def create_task(self, payload: dict[str, Any]) -> DidaTask:
        """Create a new task.

        Args:
            payload: Task creation payload (title, projectId, etc.).

        Returns:
            The created DidaTask.
        """
        data = await self._request("POST", "/task", json_body=payload)
        if not isinstance(data, dict):
            raise DidaApiError("Unexpected task creation response.")
        return DidaTask.from_api(data)

    async def update_task(
        self, task_id: str, payload: dict[str, Any]
    ) -> DidaTask:
        """Update an existing task.

        Args:
            task_id: The task ID to update.
            payload: Full task object with updated fields.

        Returns:
            The updated DidaTask.
        """
        data = await self._request(
            "POST", f"/task/{task_id}", json_body=payload
        )
        if not isinstance(data, dict):
            raise DidaApiError("Unexpected task update response.")
        return DidaTask.from_api(data)

    async def complete_task(self, project_id: str, task_id: str) -> None:
        """Mark a task as completed.

        Args:
            project_id: The project containing the task.
            task_id: The task ID to complete.
        """
        data = await self._request(
            "POST", f"/project/{project_id}/task/{task_id}/complete"
        )
        if data and not isinstance(data, dict):
            raise DidaApiError("Unexpected task completion response.")

    async def delete_task(self, project_id: str, task_id: str) -> None:
        """Delete a task.

        Args:
            project_id: The project containing the task.
            task_id: The task ID to delete.
        """
        data = await self._request(
            "DELETE", f"/project/{project_id}/task/{task_id}"
        )
        if data and not isinstance(data, dict):
            raise DidaApiError("Unexpected task delete response.")
