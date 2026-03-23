"""Jira Requirements Agent - reads epics and generates requirement documents."""

from google.adk.agents import Agent

from .prompts.system_prompt import SYSTEM_PROMPT
from .tools.jira_tools import (
    get_epic_details,
    get_epic_children,
    get_issue_details,
    get_issue_comments,
)

root_agent = Agent(
    name="jira_requirements_agent",
    model="gemini-2.5-flash",
    description=(
        "An agent that reads Jira epics and their child stories, "
        "then generates a comprehensive requirements document in Markdown format."
    ),
    instruction=SYSTEM_PROMPT,
    tools=[
        get_epic_details,
        get_epic_children,
        get_issue_details,
        get_issue_comments,
    ],
)
