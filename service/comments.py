"""Task comment operations.

Thin delegation wrappers over `DidaClient` comment endpoints.

See Also:
    - `DidaService.get_task_comments`
    - `DidaService.add_task_comment`
    - `DidaService.delete_task_comment`
"""

from __future__ import annotations

from ..client import DidaClient


async def get_task_comments(
    client: DidaClient,
    project_id: str,
    task_id: str,
) -> list[dict]:
    """Fetch all comments for a task.

    Args:
        client: The Dida365 API client.
        project_id: Project the task belongs to.
        task_id: Task to fetch comments for.

    Returns:
        List of comment dicts as returned by the API.

    See Also:
        `DidaService.get_task_comments`
    """
    return await client.get_task_comments(project_id, task_id)


async def add_task_comment(
    client: DidaClient,
    project_id: str,
    task_id: str,
    title: str,
) -> dict:
    """Add a comment to a task.

    Args:
        client: The Dida365 API client.
        project_id: Project the task belongs to.
        task_id: Task to comment on.
        title: Comment text content.

    Returns:
        The created comment dict from the API.

    See Also:
        `DidaService.add_task_comment`
    """
    return await client.add_task_comment(project_id, task_id, title)


async def delete_task_comment(
    client: DidaClient,
    project_id: str,
    task_id: str,
    comment_id: str,
) -> None:
    """Delete a comment from a task.

    Args:
        client: The Dida365 API client.
        project_id: Project the task belongs to.
        task_id: Task the comment belongs to.
        comment_id: ID of the comment to delete.

    See Also:
        `DidaService.delete_task_comment`
    """
    await client.delete_task_comment(project_id, task_id, comment_id)
