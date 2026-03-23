---
name: jira-agent
description: |
  Manage and operate the Jira Requirements & Planning Agent built on Google ADK + Gemini.
  Use this skill whenever the user wants to: start/stop/restart the ADK web server,
  test Jira API connectivity, run the agent in web or CLI mode, troubleshoot agent errors
  (HTTP 410, bidiGenerateContent, authentication failures, missing children issues),
  add new Jira tools or modify existing ones, update the system prompt, switch between
  agent versions (v1 read-only vs v2 read+create), or deploy/push the agent code.
  Also use when the user mentions "jira agent", "ADK server", "jira skill", "requirements
  document", "create epic", "create stories", or asks about the agent's capabilities.
---

# Jira Requirements & Planning Agent — Operations Skill

This skill helps you operate, debug, and extend the Jira agent located at `C:/agents/JIRA Skill`.

## Project Overview

The agent has two modes:
- **READ MODE**: Given a Jira epic key, fetches all child stories/tasks and generates a comprehensive Markdown requirements document.
- **CREATE MODE**: Given a high-level objective, breaks it down into an epic + stories + tasks and creates them in Jira.

**Tech Stack**: Google ADK (Agent Development Kit) + Gemini 2.5 Flash + Jira REST API (v2/v3)

## Project Structure

```
C:/agents/JIRA Skill/
├── .env                              # Credentials (Gemini API key + Jira auth)
├── requirements.txt                  # google-adk, requests, python-dotenv
├── jira_skill/
│   ├── agent.py                      # ACTIVE agent (v2 — read + create)
│   ├── agent_v1.py                   # Backup: read-only agent (rollback target)
│   ├── agent_v2.py                   # Archive: original v2 draft
│   ├── prompts/
│   │   ├── system_prompt.py          # v1 prompt (read-only)
│   │   └── system_prompt_v2.py       # v2 prompt (read + create) — ACTIVE
│   └── tools/
│       ├── jira_tools.py             # v1 tools (read-only)
│       └── jira_tools_v2.py          # v2 tools (read + create) — ACTIVE
```

**Key point**: ADK discovers the agent from `jira_skill/agent.py` → `root_agent`. The file `agent_v2.py` is NOT auto-discovered — it's an archive. To change which agent is active, update `agent.py`.

## Available Tools (in jira_tools_v2.py)

| Tool | Purpose |
|------|---------|
| `list_projects` | Lists all accessible Jira projects (used when no project key provided) |
| `get_project_issue_types` | Discovers available issue types for a project |
| `get_epic_details` | Fetches epic summary, description, status, priority |
| `get_epic_children` | Retrieves all child stories/tasks under an epic |
| `get_issue_details` | Fetches full details for any single issue |
| `get_issue_comments` | Retrieves comments on an issue |
| `create_epic` | Creates a new Epic in Jira |
| `create_story` | Creates a Story linked to an epic |
| `create_task` | Creates a Task linked to an epic |

## Common Operations

### Starting the ADK Server

```bash
cd "C:/agents/JIRA Skill" && adk web
```

Opens at http://localhost:8000. Select `jira_skill` from the dropdown. Use the text input (not microphone — live audio mode isn't supported for this model).

To restart after code changes, kill the existing server first:

```bash
# Find the PID
netstat -ano | findstr :8000 | findstr LISTENING
# Kill it (replace PID)
powershell -Command "Stop-Process -Id <PID> -Force"
# Restart
cd "C:/agents/JIRA Skill" && adk web
```

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

### Testing Specific Tools

```bash
cd "C:/agents/JIRA Skill" && python -c "
from jira_skill.tools.jira_tools_v2 import get_epic_children
result = get_epic_children('AA-1')
print(f'Found {result[\"total_count\"]} children')
for c in result.get('children', []):
    print(f'  {c[\"key\"]}: {c[\"summary\"]}')
"
```

### Running via CLI (no browser)

```bash
cd "C:/agents/JIRA Skill" && adk run jira_skill
```

### Verifying Agent Loads Correctly

```bash
cd "C:/agents/JIRA Skill" && python -c "
from jira_skill.agent import root_agent
print('Agent:', root_agent.name)
print('Tools:', [t.__name__ for t in root_agent.tools])
"
```

## Rollback

To revert to the read-only v1 agent:

```bash
cp "C:/agents/JIRA Skill/jira_skill/agent_v1.py" "C:/agents/JIRA Skill/jira_skill/agent.py"
```

To restore v2:

```bash
# Restore from agent_v2.py or re-apply the v2 imports in agent.py
```

## Troubleshooting

### "HTTP 410 Gone" on search queries
Atlassian deprecated `/rest/api/2/search`. The fix is to use `/rest/api/3/search/jql` instead. This has already been applied in `jira_tools_v2.py` — if you see this error, check that `get_epic_children` uses the v3 endpoint.

### "No child issues found" but children exist
The `get_epic_children` function tries two JQL strategies:
1. `parent = {epic_key}` (next-gen / team-managed projects)
2. `"Epic Link" = {epic_key}` (classic projects)

If the first query succeeds with 0 results, it must try the second. Check the fallback logic — it should only return empty when ALL queries return 0 results (check for `len(all_issues) > 0` before returning success).

### "bidiGenerateContent" / "gemini-2.5-flash not found for v1alpha"
This is harmless — it's the live/audio WebSocket mode failing. The agent falls back to standard HTTP POST mode automatically. Use text input in the ADK web UI, not the microphone.

### "Authentication failed"
Check `.env` values: `JIRA_USER_EMAIL` and `JIRA_API_TOKEN`. The API token is generated at https://id.atlassian.com/manage-profile/security/api-tokens.

### "Permission denied" when creating issues
The Jira user needs project-level write permissions. Check the user's role in the target Jira project.

### Agent not updating after code changes
ADK caches the agent module. Kill the server process and restart `adk web`. Also start a **new session** in the web UI (old sessions may cache the previous agent state).

### Git push permission denied
The local git credential may be cached for the wrong account. Clear it:
```bash
powershell -Command "cmdkey /delete:git:https://github.com"
```
Then push again — it will prompt for fresh credentials.

## Environment Variables (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini API key from Google AI Studio |
| `GOOGLE_GENAI_USE_VERTEXAI` | Yes | `FALSE` for direct API, `TRUE` for Vertex AI |
| `JIRA_BASE_URL` | Yes | e.g., `https://your-org.atlassian.net` |
| `JIRA_USER_EMAIL` | Yes | Jira account email |
| `JIRA_API_TOKEN` | Yes | Jira API token |

## Adding New Tools

To add a new Jira tool:

1. Add the function to `jira_skill/tools/jira_tools_v2.py` — use `_jira_request` for GET, `_jira_post_request` for POST, `_jira_put_request` for PUT.
2. Import it in `jira_skill/agent.py` and add to the `tools=[]` list.
3. If the agent needs instructions on when/how to use the tool, update the prompt in `jira_skill/prompts/system_prompt_v2.py`.
4. Restart the ADK server.

## GitHub Repository

The code is hosted at: https://github.com/IdeaExplorations/JIRA-Agent

Push via HTTPS (authenticate as `appcloud1`):
```bash
cd "C:/agents/JIRA Skill" && git push origin main
```
