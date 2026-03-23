"""Jira REST API tool functions for the ADK requirements agent."""

import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


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
