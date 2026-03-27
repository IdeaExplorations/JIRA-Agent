---
name: jira-agent
description: |
  Read from and write to Jira using the Jira Requirements & Planning Agent built on Google ADK + Gemini.
  Use this skill whenever the user wants to: read a Jira epic and generate a requirements document,
  create epics/stories/tasks from a high-level objective, look up Jira issue details, list Jira projects,
  check what issue types a project supports, or fetch comments from Jira issues.
  Also use when the user wants to: start/stop/restart the ADK web server, test Jira API connectivity,
  troubleshoot agent errors (HTTP 410, authentication failures, missing children issues),
  add new Jira tools, or update the agent's system prompt.
  Trigger on: "jira", "epic", "story", "task", "requirements document", "create epic",
  "create stories", "break down objective", "ADK server", "jira skill", "sprint planning",
  "issue breakdown", or any mention of reading/writing Jira data.
---

# Jira Requirements & Planning Agent

This skill enables Claude to read from and write to Jira — either directly via Python tool calls or through the ADK web UI agent. The project is at `C:/agents/JIRA Skill`.

## Two Ways to Use Jira

### 1. Direct Python Calls (preferred for Claude Code)

Call the Jira tools directly via Bash. Always run from the project directory so `.env` is loaded:

```bash
cd "C:/agents/JIRA Skill" && python -c "
from jira_skill.tools.jira_tools_v2 import list_projects
result = list_projects()
print(result)
"
```

For multi-step workflows, write a temporary script or chain calls in a single `python -c` block.

Available imports from `jira_skill.tools.jira_tools_v2`:
`list_projects`, `get_project_issue_types`, `get_epic_details`, `get_epic_children`,
`get_issue_details`, `get_issue_comments`, `create_epic`, `create_story`, `create_task`

### 2. ADK Web UI (for interactive use)

Start the server and use the chat interface at http://localhost:8000:
```bash
cd "C:/agents/JIRA Skill" && adk web
```
Select `jira_skill` from the dropdown. Use text input (not microphone).

---

## READ MODE — Generate Requirements from Jira Epics

When the user provides a Jira epic key and wants a requirements document or analysis:

### Step-by-step workflow

Run via Bash from the project directory:

```bash
cd "C:/agents/JIRA Skill" && python << 'PYEOF'
from jira_skill.tools.jira_tools_v2 import (
    get_epic_details, get_epic_children, get_issue_details, get_issue_comments
)

# 1. Fetch epic details
epic = get_epic_details("AA-1")
if epic["status"] == "error":
    print(f"Error fetching epic: {epic['error_message']}")
    exit(1)
print(f"Epic: {epic['epic']['summary']}")

# 2. Get all child stories/tasks
children = get_epic_children("AA-1")
if children["status"] == "error" or children["total_count"] == 0:
    print("No children found — document will be based on epic description only")
    exit(0)
print(f"Found {children['total_count']} children")

# 3. For each child, fetch full details + comments
all_details = []
for child in children["children"]:
    details = get_issue_details(child["key"])
    comments = get_issue_comments(child["key"])
    all_details.append({
        "child": child,
        "details": details.get("issue", {}),
        "comments": comments.get("comments", []),
    })
    print(f"  {child['key']}: {child['summary']} ({child['issue_type']})")

# Use epic + all_details to generate the requirements document
PYEOF
```

### What to produce

Synthesize all the data into a structured Markdown requirements document containing:
- **Project Overview** — objectives and scope derived from the epic
- **Functional Requirements** — numbered requirements traced back to story keys
- **Non-Functional Requirements** — inferred from descriptions/labels (mark as "Inferred")
- **User Stories Summary** — table with key, story, status, assignee, points
- **Acceptance Criteria** — compiled from each story's AC field or description
- **Priority Matrix** — Must Have / Should Have / Could Have
- **Dependencies & Risks** — from issue links, unassigned stories, missing AC
- **Technical Considerations** — from labels, components, descriptions

---

## CREATE MODE — Create Epics, Stories & Tasks from Objectives

When the user describes a feature/objective and wants Jira issues created:

### Step-by-step workflow

Run via Bash from the project directory:

```bash
cd "C:/agents/JIRA Skill" && python << 'PYEOF'
from jira_skill.tools.jira_tools_v2 import (
    list_projects, get_project_issue_types, create_epic, create_story, create_task
)

# 1. Discover projects (if no project key provided)
projects = list_projects()
if projects["status"] == "error":
    print(f"Error: {projects['error_message']}")
    exit(1)
for p in projects["projects"]:
    print(f"  {p['key']}: {p['name']} ({p['project_type']})")
# Ask user to pick one if not specified

PROJECT = "AA"  # Replace with user's choice

# 2. Check available issue types
types = get_project_issue_types(PROJECT)
if types["status"] == "error":
    print(f"Error: {types['error_message']}")
    exit(1)
available = [t["name"] for t in types["issue_types"]]
print(f"Available types: {available}")
# Confirm Epic, Story, Task are in the list before proceeding

# 3. Create the epic FIRST — stop if this fails
epic = create_epic(
    project_key=PROJECT,
    summary="Stripe Payment Integration",
    description="Integrate Stripe for payment processing...",
    priority="High",
    labels=["payments", "stripe"]
)
if epic["status"] == "error":
    print(f"Epic creation failed: {epic['error_message']}")
    exit(1)
epic_key = epic["issue_key"]
print(f"Created epic: {epic_key} — {epic['browse_url']}")

# 4. Create stories under the epic
stories = [
    {"summary": "As a customer, I want to pay with credit card",
     "description": "Detailed description...", "priority": "High",
     "acceptance_criteria": "Given valid card, When checkout, Then payment succeeds"},
    # ... more stories
]
created = []
for s in stories:
    result = create_story(project_key=PROJECT, epic_key=epic_key, **s)
    if result["status"] == "success":
        created.append(result["issue_key"])
        print(f"  Story created: {result['issue_key']}")
    else:
        print(f"  Story FAILED: {result['error_message']}")

# 5. Create tasks under the epic
tasks = [
    {"summary": "Set up Stripe SDK and API keys",
     "description": "Install stripe-python, configure...", "priority": "High"},
    # ... more tasks
]
for t in tasks:
    result = create_task(project_key=PROJECT, epic_key=epic_key, **t)
    if result["status"] == "success":
        created.append(result["issue_key"])
        print(f"  Task created: {result['issue_key']}")
    else:
        print(f"  Task FAILED: {result['error_message']}")

print(f"\nDone! {len(created)} issues created under {epic_key}")
PYEOF
```

### Breakdown guidelines

When breaking down an objective:
- **1 Epic** capturing the overall objective
- **3-8 Stories** for user-facing capabilities (use "As a [user], I want [goal], so that [benefit]" format)
- **2-5 Tasks** for technical/non-user-facing work (infra, CI/CD, migrations, monitoring)
- Set priorities: High / Medium / Low
- Always propose the breakdown for user review before creating, unless they say "just do it"
- Create epic first — if it fails, stop (don't create orphan children)
- If a child issue fails, continue with the rest and report failures in the summary

### Creation summary format

After creating all issues, present this summary to the user:

```
## Creation Summary

**Epic:** AA-15 — Stripe Payment Integration
**URL:** https://your-org.atlassian.net/browse/AA-15

| # | Key   | Type  | Summary                              | Status  |
|---|-------|-------|--------------------------------------|---------|
| 1 | AA-16 | Story | As a customer, I want to pay...      | Created |
| 2 | AA-17 | Story | As an admin, I want to view...       | Created |
| 3 | AA-18 | Task  | Set up Stripe SDK and API keys       | Created |
| 4 | AA-19 | Task  | Configure webhook endpoints          | FAILED: [error] |

**Total:** 3 of 4 issues created successfully.
```

---

## Available Tools Reference

| Tool | Description |
|------|-------------|
| `list_projects()` | Lists all accessible Jira projects |
| `get_project_issue_types(project_key)` | Discovers available issue types for a project |
| `get_epic_details(epic_key)` | Fetches epic summary, description, status, priority, labels |
| `get_epic_children(epic_key)` | Retrieves all child stories/tasks under an epic |
| `get_issue_details(issue_key)` | Full details: description, acceptance_criteria, subtasks, linked_issues |
| `get_issue_comments(issue_key)` | All comments with author, body, created date |
| `create_epic(project_key, summary, description="", priority="", labels=[])` | Creates a new Epic |
| `create_story(project_key, summary, description="", epic_key="", priority="", labels=[], acceptance_criteria="")` | Creates a Story, optionally linked to an epic |
| `create_task(project_key, summary, description="", epic_key="", priority="", labels=[])` | Creates a Task, optionally linked to an epic |

All tools return `{"status": "success", ...}` or `{"status": "error", "error_message": "..."}`. Always check `result["status"]` before accessing other fields.

---

## Project Structure

```
C:/agents/JIRA Skill/
├── .env                              # Credentials (Gemini + Jira)
├── requirements.txt                  # google-adk, requests, python-dotenv
├── jira_skill/
│   ├── agent.py                      # ADK agent definition (root_agent)
│   ├── prompts/
│   │   └── system_prompt_v2.py       # System prompt with READ + CREATE modes
│   └── tools/
│       └── jira_tools_v2.py          # All Jira API tools
```

ADK discovers the agent from `jira_skill/agent.py` → `root_agent`. The agent uses `gemini-2.5-flash`.

---

## Operations & Troubleshooting

### Testing Jira Connectivity

```bash
cd "C:/agents/JIRA Skill" && python -c "
from jira_skill.tools.jira_tools_v2 import list_projects
result = list_projects()
if result['status'] == 'success':
    print(f'Connected! Found {result[\"total_count\"]} project(s):')
    for p in result['projects']:
        print(f'  {p[\"key\"]}: {p[\"name\"]}')
else:
    print(f'Error: {result[\"error_message\"]}')
"
```

### Restarting the ADK Server

```bash
# Find and kill existing server
netstat -ano | findstr :8000 | findstr LISTENING
powershell -Command "Stop-Process -Id <PID> -Force"
# Restart
cd "C:/agents/JIRA Skill" && adk web
```

Start a **new session** in the web UI after restarting — old sessions cache previous agent state.

### Verifying Agent Loads

```bash
cd "C:/agents/JIRA Skill" && python -c "
from jira_skill.agent import root_agent
print('Agent:', root_agent.name)
print('Tools:', [t.__name__ for t in root_agent.tools])
"
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Authentication failed` | Bad credentials | Check `JIRA_USER_EMAIL` and `JIRA_API_TOKEN` in `.env` |
| `HTTP 410 Gone` on search | Deprecated API | `get_epic_children` uses `/rest/api/3/search/jql` — verify it's not using `/rest/api/2/search` |
| `No child issues found` | Fallback logic bug | `get_epic_children` tries `parent` then `"Epic Link"` JQL. It should only return empty when BOTH queries return 0 results |
| `bidiGenerateContent` error | Live audio unsupported | Harmless — agent falls back to HTTP mode. Use text input |
| `Permission denied` creating issues | Insufficient Jira role | User needs write access in the target project |
| Agent not updating after edits | Module cache | Kill server, restart `adk web`, start new session |

### Environment Variables (.env)

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key from Google AI Studio |
| `GOOGLE_GENAI_USE_VERTEXAI` | `FALSE` for direct API, `TRUE` for Vertex AI |
| `JIRA_BASE_URL` | e.g., `https://your-org.atlassian.net` |
| `JIRA_USER_EMAIL` | Jira account email |
| `JIRA_API_TOKEN` | API token from Atlassian account settings |

### Adding New Tools

1. Add the function to `jira_skill/tools/jira_tools_v2.py` — use `_jira_request` (GET), `_jira_post_request` (POST), or `_jira_put_request` (PUT)
2. Import it in `jira_skill/agent.py` and add to the `tools=[]` list
3. Update `jira_skill/prompts/system_prompt_v2.py` if the agent needs guidance on when to use it
4. Restart the ADK server

### GitHub Repository

Code is at: https://github.com/IdeaExplorations/JIRA-Agent

```bash
cd "C:/agents/JIRA Skill" && git push origin main
```
