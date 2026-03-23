# Jira Requirements & Planning Agent

A Google ADK-powered AI agent that integrates with Jira to **read epics and generate comprehensive requirements documents**, and **create epics, stories, and tasks from high-level objectives** — all powered by Gemini.

---

## Getting Started

### Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python** | 3.10 or higher |
| **Google API Key** | For Gemini LLM — get one at [Google AI Studio](https://aistudio.google.com/apikey) |
| **Jira Instance** | Atlassian Cloud or Server with REST API access |
| **Jira API Token** | Generate at [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |

### 1. Clone & Install

```bash
# Clone the repository
git clone <your-repo-url>
cd "JIRA Skill"

# Install dependencies
pip install -r requirements.txt
```

The agent requires three packages:
- `google-adk` — Google Agent Development Kit
- `requests` — HTTP client for Jira REST API calls
- `python-dotenv` — Environment variable management

### 2. Configure Environment Variables

Create or edit the `.env` file in the project root:

```env
# --- Google Gemini ---
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_google_api_key_here

# --- Jira ---
JIRA_BASE_URL=https://your-org.atlassian.net
JIRA_USER_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token_here
```

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Your Gemini API key from Google AI Studio |
| `GOOGLE_GENAI_USE_VERTEXAI` | Set to `FALSE` for direct Gemini API; `TRUE` for Vertex AI |
| `JIRA_BASE_URL` | Your Jira instance URL (Cloud: `https://<org>.atlassian.net`, Server: `https://jira.yourcompany.com`) |
| `JIRA_USER_EMAIL` | The email address associated with your Jira account |
| `JIRA_API_TOKEN` | API token generated from your Atlassian account settings |

> **Note:** Never commit the `.env` file to version control. It contains sensitive credentials.

### 3. Verify Jira Connectivity

Run a quick smoke test to confirm your credentials and connectivity:

```bash
python -c "
from jira_skill.tools.jira_tools_v2 import list_projects
result = list_projects()
if result['status'] == 'success':
    print(f'Connected! Found {result[\"total_count\"]} project(s):')
    for p in result['projects']:
        print(f'  - {p[\"key\"]}: {p[\"name\"]} ({p[\"project_type\"]})')
else:
    print(f'Error: {result[\"error_message\"]}')
"
```

Expected output:
```
Connected! Found 2 project(s):
  - SCRUM: AiRA (software)
  - AA: Alpha-AIRA (software)
```

### 4. Start the Agent

#### Option A: Web UI (recommended)

```bash
adk web
```

Open [http://localhost:8000](http://localhost:8000) in your browser and select **`jira_skill`** from the agent dropdown.

#### Option B: Command Line

```bash
adk run jira_skill
```

---

## Usage

The agent operates in two modes, automatically detected from your input:

### Read Mode — Generate Requirements Documents

Provide a Jira epic key to generate a structured requirements document:

```
Generate a comprehensive requirements document for epic AA-1
```

The agent will:
1. Fetch the epic details from Jira
2. Retrieve all child stories and tasks under the epic
3. Fetch detailed descriptions, acceptance criteria, and comments for each child issue
4. Synthesize everything into a structured Markdown requirements document

**Output includes:** Project Overview, Functional Requirements, Non-Functional Requirements, User Stories Summary, Acceptance Criteria, Priority Matrix, Dependencies & Risks, and Technical Considerations.

### Create Mode — Plan & Create Issues from Objectives

Describe what you want to build and the agent creates the Jira issues for you:

```
I want to add integration with Stripe payment system. Create an epic with stories and tasks.
```

The agent will:
1. Ask you to pick a project (or auto-detect from a provided key/URL)
2. Discover available issue types in the project
3. Break down your objective into an epic, stories (3-8), and tasks (2-5)
4. Optionally let you review and modify the plan before creating
5. Create all issues in Jira, linked under the epic

You can also provide a project key directly:

```
Create an epic for Stripe integration in project AA with stories and tasks
```

Or skip the review step:

```
Create an epic with stories and tasks for adding SSO login support in SCRUM. Go ahead and create them.
```

---

## Project Structure

```
JIRA Skill/
├── .env                            # Credentials (not committed)
├── requirements.txt                # Python dependencies
├── jira_skill/
│   ├── __init__.py                 # Package init
│   ├── agent.py                    # Active agent definition (v2)
│   ├── agent_v1.py                 # Backup: read-only agent (rollback)
│   ├── agent_v2.py                 # Archive: original v2 draft
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── system_prompt.py        # v1 prompt (read-only)
│   │   └── system_prompt_v2.py     # v2 prompt (read + create)
│   └── tools/
│       ├── __init__.py
│       ├── jira_tools.py           # v1 tools (read-only)
│       └── jira_tools_v2.py        # v2 tools (read + create)
```

### Available Tools

| Tool | Mode | Description |
|------|------|-------------|
| `get_epic_details` | Read | Fetches epic summary, description, status, priority, labels |
| `get_epic_children` | Read | Retrieves all child stories/tasks under an epic |
| `get_issue_details` | Read | Fetches full details for any issue (description, acceptance criteria, subtasks) |
| `get_issue_comments` | Read | Retrieves comments on an issue for additional context |
| `list_projects` | Discovery | Lists all accessible Jira projects (used when no project key is provided) |
| `get_project_issue_types` | Discovery | Discovers available issue types (Epic, Story, Task, etc.) for a project |
| `create_epic` | Create | Creates a new Epic in a Jira project |
| `create_story` | Create | Creates a new Story linked to an epic |
| `create_task` | Create | Creates a new Task linked to an epic |

---

## Customization

- **Model**: Change the `model` parameter in `jira_skill/agent.py` (e.g., `gemini-2.5-pro` for larger epics or more nuanced breakdowns)
- **Custom Fields**: If your Jira instance uses different custom field IDs for story points or acceptance criteria, update the field references in `jira_skill/tools/jira_tools_v2.py`
- **Prompt Tuning**: Modify `jira_skill/prompts/system_prompt_v2.py` to adjust the requirements document format, story breakdown strategy, or agent behavior

## Rollback to Read-Only Mode

To revert the agent to v1 (read-only, no issue creation):

```bash
cp jira_skill/agent_v1.py jira_skill/agent.py
```

Then restart the ADK server.

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Authentication failed` | Invalid credentials | Verify `JIRA_USER_EMAIL` and `JIRA_API_TOKEN` in `.env` |
| `Cannot connect to Jira` | Wrong base URL | Check `JIRA_BASE_URL` — ensure no trailing slash |
| `No child issues found` | JQL query mismatch | The agent tries both `parent` and `Epic Link` JQL strategies automatically. If issues persist, verify the epic has linked children in Jira |
| `HTTP 410 Gone` on search | Deprecated API | The agent uses `/rest/api/3/search/jql` — ensure your `google-adk` and tools are up to date |
| `gemini-2.5-flash not found for bidiGenerateContent` | Live/audio mode unsupported | This is harmless — the agent automatically falls back to standard HTTP mode. Use the text input (not microphone) in the ADK web UI |
| `Missing story points` | Different custom field ID | Your Jira instance may use a different custom field — check with your Jira admin |
| `Permission denied` | Insufficient Jira permissions | Ensure your API token's user has permission to read/create issues in the target project |
