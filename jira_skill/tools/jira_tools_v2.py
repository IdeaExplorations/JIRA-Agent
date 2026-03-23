"""Jira REST API tool functions v2 — read + create capabilities for the ADK agent."""

import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _get_jira_auth() -> tuple[str, str]:
    """Returns (email, api_token) tuple for Jira Basic Auth."""
    return (
        os.getenv("JIRA_USER_EMAIL", ""),
        os.getenv("JIRA_API_TOKEN", ""),
    )


def _get_base_url() -> str:
    """Returns the Jira base URL with trailing slash stripped."""
    return os.getenv("JIRA_BASE_URL", "").rstrip("/")


def _jira_request(endpoint: str, params: Optional[dict] = None) -> dict:
    """Makes an authenticated GET request to the Jira REST API.

    Args:
        endpoint: The API path (e.g. '/rest/api/2/issue/PROJ-1').
        params: Optional query parameters.

    Returns:
        A dict with 'status' ('success' or 'error') and either 'data' or 'error_message'.
    """
    base_url = _get_base_url()
    if not base_url:
        return {"status": "error", "error_message": "JIRA_BASE_URL is not configured in .env"}

    auth = _get_jira_auth()
    if not auth[0] or not auth[1]:
        return {"status": "error", "error_message": "JIRA_USER_EMAIL or JIRA_API_TOKEN is not configured in .env"}

    url = f"{base_url}{endpoint}"
    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, auth=auth, params=params, timeout=30)
        response.raise_for_status()
        return {"status": "success", "data": response.json()}
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        body = e.response.text[:500] if e.response.text else "No response body"
        if status_code == 401:
            return {"status": "error", "error_message": "Authentication failed. Check JIRA_USER_EMAIL and JIRA_API_TOKEN."}
        if status_code == 403:
            return {"status": "error", "error_message": f"Permission denied for {endpoint}. Check your Jira permissions."}
        if status_code == 404:
            return {"status": "error", "error_message": f"Not found: {endpoint}. Verify the issue key exists."}
        return {"status": "error", "error_message": f"HTTP {status_code}: {body}"}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "error_message": f"Cannot connect to Jira at {base_url}. Check JIRA_BASE_URL."}
    except requests.exceptions.Timeout:
        return {"status": "error", "error_message": "Jira request timed out after 30 seconds."}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def _jira_post_request(endpoint: str, payload: dict) -> dict:
    """Makes an authenticated POST request to the Jira REST API.

    Args:
        endpoint: The API path (e.g. '/rest/api/2/issue').
        payload: The JSON body to send.

    Returns:
        A dict with 'status' ('success' or 'error') and either 'data' or 'error_message'.
    """
    base_url = _get_base_url()
    if not base_url:
        return {"status": "error", "error_message": "JIRA_BASE_URL is not configured in .env"}

    auth = _get_jira_auth()
    if not auth[0] or not auth[1]:
        return {"status": "error", "error_message": "JIRA_USER_EMAIL or JIRA_API_TOKEN is not configured in .env"}

    url = f"{base_url}{endpoint}"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, auth=auth, json=payload, timeout=30)
        response.raise_for_status()
        return {"status": "success", "data": response.json()}
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        body = e.response.text[:500] if e.response.text else "No response body"
        if status_code == 400:
            return {"status": "error", "error_message": f"Bad request — check required fields. Details: {body}"}
        if status_code == 401:
            return {"status": "error", "error_message": "Authentication failed. Check JIRA_USER_EMAIL and JIRA_API_TOKEN."}
        if status_code == 403:
            return {"status": "error", "error_message": f"Permission denied for {endpoint}. Check your Jira permissions to create issues."}
        if status_code == 404:
            return {"status": "error", "error_message": f"Not found: {endpoint}. Verify the project key and issue type exist."}
        return {"status": "error", "error_message": f"HTTP {status_code}: {body}"}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "error_message": f"Cannot connect to Jira at {base_url}. Check JIRA_BASE_URL."}
    except requests.exceptions.Timeout:
        return {"status": "error", "error_message": "Jira request timed out after 30 seconds."}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


def _jira_put_request(endpoint: str, payload: dict) -> dict:
    """Makes an authenticated PUT request to the Jira REST API.

    Args:
        endpoint: The API path (e.g. '/rest/api/2/issue/PROJ-1').
        payload: The JSON body to send.

    Returns:
        A dict with 'status' ('success' or 'error') and either 'data' or 'error_message'.
    """
    base_url = _get_base_url()
    if not base_url:
        return {"status": "error", "error_message": "JIRA_BASE_URL is not configured in .env"}

    auth = _get_jira_auth()
    if not auth[0] or not auth[1]:
        return {"status": "error", "error_message": "JIRA_USER_EMAIL or JIRA_API_TOKEN is not configured in .env"}

    url = f"{base_url}{endpoint}"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    try:
        response = requests.put(url, headers=headers, auth=auth, json=payload, timeout=30)
        response.raise_for_status()
        # PUT /rest/api/2/issue returns 204 No Content on success
        if response.status_code == 204:
            return {"status": "success", "data": {}}
        return {"status": "success", "data": response.json()}
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        body = e.response.text[:500] if e.response.text else "No response body"
        return {"status": "error", "error_message": f"HTTP {status_code}: {body}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Unexpected error: {str(e)}"}


# ---------------------------------------------------------------------------
# Read tools (carried forward from v1)
# ---------------------------------------------------------------------------

def get_epic_details(epic_key: str) -> dict:
    """Retrieves the details of a Jira epic by its issue key.

    Returns the epic's summary, description, status, priority, labels,
    fix versions, components, and reporter information.

    Args:
        epic_key: The Jira issue key of the epic (e.g. 'PROJ-123').

    Returns:
        A dictionary with status and epic details or error message.
    """
    fields = "summary,description,status,priority,labels,fixVersions,components,reporter,created,updated,issuetype"
    result = _jira_request(f"/rest/api/2/issue/{epic_key}", params={"fields": fields})

    if result["status"] == "error":
        return result

    issue = result["data"]
    f = issue.get("fields", {})

    return {
        "status": "success",
        "epic": {
            "key": issue.get("key"),
            "summary": f.get("summary"),
            "description": f.get("description"),
            "status": f.get("status", {}).get("name"),
            "priority": f.get("priority", {}).get("name"),
            "labels": f.get("labels", []),
            "fix_versions": [v.get("name") for v in f.get("fixVersions", [])],
            "components": [c.get("name") for c in f.get("components", [])],
            "reporter": f.get("reporter", {}).get("displayName"),
            "created": f.get("created"),
            "updated": f.get("updated"),
            "issue_type": f.get("issuetype", {}).get("name"),
        },
    }


def get_epic_children(epic_key: str) -> dict:
    """Retrieves all child issues (stories, tasks, bugs) linked to a Jira epic.

    Uses JQL with 'Epic Link' for classic projects, falling back to 'parent'
    for next-gen/team-managed projects. Handles pagination automatically.

    Args:
        epic_key: The Jira issue key of the parent epic (e.g. 'PROJ-123').

    Returns:
        A dictionary with status, total_count, and a list of child issues.
    """
    fields = "summary,status,issuetype,priority,labels,assignee,story_points,customfield_10028,customfield_10016"

    # Try "parent" first (next-gen / team-managed), then fall back to "Epic Link" (classic)
    jql_queries = [
        f"parent = {epic_key}",
        f'"Epic Link" = {epic_key}',
    ]

    for jql in jql_queries:
        all_issues = []
        start_at = 0
        max_results = 50
        fetch_failed = False

        while True:
            params = {
                "jql": jql,
                "fields": fields,
                "startAt": start_at,
                "maxResults": max_results,
            }
            # Atlassian Cloud deprecated /rest/api/2/search — use v3 endpoint
            result = _jira_request("/rest/api/3/search/jql", params=params)

            if result["status"] == "error":
                fetch_failed = True
                break

            data = result["data"]
            issues = data.get("issues", [])

            for issue in issues:
                issue_fields = issue.get("fields", {})
                story_points = (
                    issue_fields.get("story_points")
                    or issue_fields.get("customfield_10028")
                    or issue_fields.get("customfield_10016")
                )
                all_issues.append({
                    "key": issue.get("key"),
                    "summary": issue_fields.get("summary"),
                    "issue_type": issue_fields.get("issuetype", {}).get("name"),
                    "status": issue_fields.get("status", {}).get("name"),
                    "priority": issue_fields.get("priority", {}).get("name"),
                    "labels": issue_fields.get("labels", []),
                    "story_points": story_points,
                    "assignee": (
                        issue_fields.get("assignee", {}).get("displayName")
                        if issue_fields.get("assignee")
                        else None
                    ),
                })

            # v3 API uses "isLast" flag; fall back to total-based pagination
            is_last = data.get("isLast", True)
            total = data.get("total", len(all_issues))
            start_at += max_results
            if is_last or start_at >= total:
                break

        if not fetch_failed and len(all_issues) > 0:
            return {
                "status": "success",
                "total_count": len(all_issues),
                "children": all_issues,
            }

    # All queries tried — either all failed or all returned 0 results
    return {
        "status": "success",
        "total_count": 0,
        "children": [],
        "note": f"No child issues found for epic {epic_key}. Tried both 'parent' and 'Epic Link' JQL queries.",
    }


def get_issue_details(issue_key: str) -> dict:
    """Retrieves the full details of a single Jira issue.

    Fetches the complete description, acceptance criteria, subtasks,
    linked issues, and all standard fields for a story, task, or bug.

    Args:
        issue_key: The Jira issue key (e.g. 'PROJ-456').

    Returns:
        A dictionary with status and full issue details or error message.
    """
    result = _jira_request(f"/rest/api/2/issue/{issue_key}")

    if result["status"] == "error":
        return result

    issue = result["data"]
    f = issue.get("fields", {})

    # Acceptance criteria can live in various custom fields
    acceptance_criteria = (
        f.get("customfield_10035")
        or f.get("customfield_10024")
    )

    story_points = (
        f.get("story_points")
        or f.get("customfield_10028")
        or f.get("customfield_10016")
    )

    return {
        "status": "success",
        "issue": {
            "key": issue.get("key"),
            "summary": f.get("summary"),
            "description": f.get("description"),
            "acceptance_criteria": acceptance_criteria,
            "status": f.get("status", {}).get("name"),
            "priority": f.get("priority", {}).get("name"),
            "issue_type": f.get("issuetype", {}).get("name"),
            "labels": f.get("labels", []),
            "story_points": story_points,
            "assignee": (
                f.get("assignee", {}).get("displayName")
                if f.get("assignee")
                else None
            ),
            "reporter": f.get("reporter", {}).get("displayName"),
            "components": [c.get("name") for c in f.get("components", [])],
            "fix_versions": [v.get("name") for v in f.get("fixVersions", [])],
            "created": f.get("created"),
            "updated": f.get("updated"),
            "subtasks": [
                {
                    "key": st.get("key"),
                    "summary": st.get("fields", {}).get("summary"),
                }
                for st in f.get("subtasks", [])
            ],
            "linked_issues": [
                {
                    "type": link.get("type", {}).get("name"),
                    "direction": "outward" if "outwardIssue" in link else "inward",
                    "key": (link.get("outwardIssue") or link.get("inwardIssue", {})).get("key"),
                    "summary": (link.get("outwardIssue") or link.get("inwardIssue", {})).get("fields", {}).get("summary"),
                }
                for link in f.get("issuelinks", [])
            ],
        },
    }


def get_issue_comments(issue_key: str) -> dict:
    """Retrieves all comments on a Jira issue.

    Comments often contain important context, decisions, and clarifications
    about requirements that should be captured in the requirements document.

    Args:
        issue_key: The Jira issue key (e.g. 'PROJ-456').

    Returns:
        A dictionary with status and a list of comments or error message.
    """
    result = _jira_request(f"/rest/api/2/issue/{issue_key}/comment")

    if result["status"] == "error":
        return result

    data = result["data"]
    comments = [
        {
            "author": comment.get("author", {}).get("displayName"),
            "body": comment.get("body"),
            "created": comment.get("created"),
        }
        for comment in data.get("comments", [])
    ]

    return {
        "status": "success",
        "total_comments": len(comments),
        "comments": comments,
    }


# ---------------------------------------------------------------------------
# Discovery tools (new in v2)
# ---------------------------------------------------------------------------

def list_projects() -> dict:
    """Retrieves all Jira projects accessible to the authenticated user.

    Use this tool when the user has NOT provided a project key. Present the
    list of projects and ask the user to pick one before creating issues.

    Returns:
        A dictionary with status and a list of projects (key, name, type).
    """
    result = _jira_request("/rest/api/2/project")

    if result["status"] == "error":
        return result

    projects = result["data"]
    return {
        "status": "success",
        "total_count": len(projects),
        "projects": [
            {
                "key": p.get("key"),
                "name": p.get("name"),
                "project_type": p.get("projectTypeKey", "unknown"),
                "style": p.get("style", "unknown"),
            }
            for p in projects
        ],
    }


def get_project_issue_types(project_key: str) -> dict:
    """Retrieves the available issue types for a Jira project.

    Use this tool to discover what issue types (Epic, Story, Task, Bug, etc.)
    are available in a specific project before creating issues. The returned
    issue type names must be used exactly when creating issues.

    Args:
        project_key: The Jira project key (e.g. 'PROJ').

    Returns:
        A dictionary with status, project info, and list of issue types
        with their IDs, names, and whether they are subtask types.
    """
    result = _jira_request(f"/rest/api/2/project/{project_key}")

    if result["status"] == "error":
        return result

    project = result["data"]
    issue_types = project.get("issueTypes", [])

    return {
        "status": "success",
        "project_key": project.get("key"),
        "project_name": project.get("name"),
        "project_style": project.get("style", "unknown"),
        "issue_types": [
            {
                "id": it.get("id"),
                "name": it.get("name"),
                "subtask": it.get("subtask", False),
                "description": it.get("description", ""),
            }
            for it in issue_types
        ],
    }


# ---------------------------------------------------------------------------
# Creation tools (new in v2)
# ---------------------------------------------------------------------------

def create_epic(
    project_key: str,
    summary: str,
    description: str = "",
    priority: str = "",
    labels: list[str] = None,
) -> dict:
    """Creates a new Epic issue in the specified Jira project.

    Always call get_project_issue_types first to confirm 'Epic' is available
    in the project and to discover the correct issue type name.

    Args:
        project_key: The Jira project key (e.g. 'PROJ').
        summary: The epic summary/title.
        description: Detailed description of the epic. Defaults to empty.
        priority: Priority name (e.g. 'High', 'Medium'). Leave empty for project default.
        labels: Optional list of labels to apply to the epic.

    Returns:
        A dictionary with status, created issue key, browse URL, or error message.
    """
    if labels is None:
        labels = []

    fields: dict = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": "Epic"},
    }

    if description:
        fields["description"] = description
    if priority:
        fields["priority"] = {"name": priority}
    if labels:
        fields["labels"] = labels

    # Classic Jira projects often require the "Epic Name" custom field.
    # Set it to the summary as a safe default.
    fields["customfield_10011"] = summary

    result = _jira_post_request("/rest/api/2/issue", {"fields": fields})

    # If customfield_10011 caused an error, retry without it (modern projects)
    if result["status"] == "error" and "customfield_10011" in result.get("error_message", ""):
        del fields["customfield_10011"]
        result = _jira_post_request("/rest/api/2/issue", {"fields": fields})

    if result["status"] == "error":
        return result

    data = result["data"]
    return {
        "status": "success",
        "issue_key": data.get("key"),
        "issue_id": data.get("id"),
        "self_url": data.get("self"),
        "browse_url": f"{_get_base_url()}/browse/{data.get('key')}",
    }


def create_story(
    project_key: str,
    summary: str,
    description: str = "",
    epic_key: str = "",
    priority: str = "",
    labels: list[str] = None,
    acceptance_criteria: str = "",
) -> dict:
    """Creates a new Story issue in the specified Jira project, optionally linked to an epic.

    Always call get_project_issue_types first to confirm 'Story' is available.

    Args:
        project_key: The Jira project key (e.g. 'PROJ').
        summary: The story summary/title (ideally in 'As a... I want... so that...' format).
        description: Detailed description of the story. Defaults to empty.
        epic_key: The key of the parent epic (e.g. 'PROJ-1'). If provided, the story
                  will be linked to this epic.
        priority: Priority name (e.g. 'High', 'Medium'). Leave empty for project default.
        labels: Optional list of labels to apply.
        acceptance_criteria: Optional acceptance criteria text. Will be stored in a
                             custom field if the project supports it.

    Returns:
        A dictionary with status, created issue key, browse URL, or error message.
    """
    if labels is None:
        labels = []

    fields: dict = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": "Story"},
    }

    if description:
        fields["description"] = description
    if priority:
        fields["priority"] = {"name": priority}
    if labels:
        fields["labels"] = labels

    # Link to epic: try "parent" field first (works for next-gen and modern classic)
    if epic_key:
        fields["parent"] = {"key": epic_key}

    result = _jira_post_request("/rest/api/2/issue", {"fields": fields})

    # If "parent" field failed, try the classic "Epic Link" custom field
    if result["status"] == "error" and epic_key and "parent" in result.get("error_message", ""):
        fields.pop("parent", None)
        fields["customfield_10014"] = epic_key
        result = _jira_post_request("/rest/api/2/issue", {"fields": fields})

    if result["status"] == "error":
        return result

    data = result["data"]
    created_key = data.get("key")

    # Best-effort: set acceptance criteria via a separate update
    # (many projects have this on the edit screen but not the create screen)
    ac_update_status = None
    if acceptance_criteria and created_key:
        ac_result = _jira_put_request(
            f"/rest/api/2/issue/{created_key}",
            {"fields": {"customfield_10035": acceptance_criteria}},
        )
        if ac_result["status"] == "error":
            # Try alternative custom field
            ac_result = _jira_put_request(
                f"/rest/api/2/issue/{created_key}",
                {"fields": {"customfield_10024": acceptance_criteria}},
            )
        ac_update_status = ac_result["status"]

    return {
        "status": "success",
        "issue_key": created_key,
        "issue_id": data.get("id"),
        "self_url": data.get("self"),
        "browse_url": f"{_get_base_url()}/browse/{created_key}",
        "epic_key": epic_key or None,
        "acceptance_criteria_saved": ac_update_status if acceptance_criteria else "not_provided",
    }


def create_task(
    project_key: str,
    summary: str,
    description: str = "",
    epic_key: str = "",
    priority: str = "",
    labels: list[str] = None,
) -> dict:
    """Creates a new Task issue in the specified Jira project, optionally linked to an epic.

    Always call get_project_issue_types first to confirm 'Task' is available.

    Args:
        project_key: The Jira project key (e.g. 'PROJ').
        summary: The task summary/title.
        description: Detailed description of the task. Defaults to empty.
        epic_key: The key of the parent epic (e.g. 'PROJ-1'). If provided, the task
                  will be linked to this epic.
        priority: Priority name (e.g. 'High', 'Medium'). Leave empty for project default.
        labels: Optional list of labels to apply.

    Returns:
        A dictionary with status, created issue key, browse URL, or error message.
    """
    if labels is None:
        labels = []

    fields: dict = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": "Task"},
    }

    if description:
        fields["description"] = description
    if priority:
        fields["priority"] = {"name": priority}
    if labels:
        fields["labels"] = labels

    # Link to epic: try "parent" field first (works for next-gen and modern classic)
    if epic_key:
        fields["parent"] = {"key": epic_key}

    result = _jira_post_request("/rest/api/2/issue", {"fields": fields})

    # If "parent" field failed, try the classic "Epic Link" custom field
    if result["status"] == "error" and epic_key and "parent" in result.get("error_message", ""):
        fields.pop("parent", None)
        fields["customfield_10014"] = epic_key
        result = _jira_post_request("/rest/api/2/issue", {"fields": fields})

    if result["status"] == "error":
        return result

    data = result["data"]
    return {
        "status": "success",
        "issue_key": data.get("key"),
        "issue_id": data.get("id"),
        "self_url": data.get("self"),
        "browse_url": f"{_get_base_url()}/browse/{data.get('key')}",
        "epic_key": epic_key or None,
    }
