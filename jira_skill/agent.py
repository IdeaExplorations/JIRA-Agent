"""Jira Requirements & Planning Agent v2 — reads epics AND creates issues.

The original read-only agent is preserved in agent_v1.py for rollback.
"""

from google.adk.agents import Agent

from .prompts.system_prompt_v2 import SYSTEM_PROMPT_V2
from .tools.jira_tools_v2 import (
    get_epic_details,
    get_epic_children,
    get_issue_details,
    get_issue_comments,
    list_projects,
    get_project_issue_types,
    create_epic,
    create_story,
    create_task,
)

root_agent = Agent(
    name="jira_planning_agent",
    model="gemini-2.5-flash",
    description=(
        "An agent that reads Jira epics to generate requirements documents, "
        "and creates epics, stories, and tasks from objectives."
    ),
    instruction=SYSTEM_PROMPT_V2,
    tools=[
        # Read tools
        get_epic_details,
        get_epic_children,
        get_issue_details,
        get_issue_comments,
        # Discovery tools
        list_projects,
        get_project_issue_types,
        # Creation tools
        create_epic,
        create_story,
        create_task,
    ],
)
