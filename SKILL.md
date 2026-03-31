---
name: jira-agent
description: |
  Read from and write to Jira via the configured Jira MCP connector.
  Use this skill whenever the user wants to: read a Jira epic and generate a requirements document,
  create epics/stories/tasks from a high-level objective, look up Jira issue details, list Jira
  projects, check issue types, or fetch comments from Jira issues.
  Trigger on: "jira", "epic", "story", "task", "requirements document", "create epic",
  "create stories", "break down objective", "sprint planning", "issue breakdown",
  or any mention of reading/writing Jira data.
---

# Jira Requirements & Planning Skill

Uses the configured Jira MCP connector tools. No Python layer needed.

- For available MCP tools and JQL patterns → see `references/mcp_tools.md`
- For all output format templates → see `references/output_formats.md`

You have two core capabilities:

1. **READ MODE** — Read Jira epics and generate comprehensive requirements documents.
2. **CREATE MODE** — Break down an objective into epics, stories, and tasks, then create them in Jira.

---

## DETECTING WHICH MODE TO USE

- If the user provides a **Jira issue key** (e.g. `PROJ-123`) and asks for requirements, analysis,
  or a document → use **READ MODE**.
- If the user provides an **objective, feature description, or goal** and asks to create, plan,
  or break down work items → use **CREATE MODE**.
- If unclear, ask the user to clarify.

---

## READ MODE WORKFLOW

### Step 1: Fetch Epic Details
- Retrieve the epic using the provided key.
- If this fails, report the error and ask the user to verify the key and Jira connection.

### Step 2: Fetch All Child Issues
- Search for all child issues under the epic.
- If no results with a `parent` filter, retry using an `Epic Link` filter.
- If still no children, inform the user and generate the document from the epic description only.

### Step 3: Fetch Detailed Information for Each Child
- For each child issue, retrieve its full details — description, acceptance criteria, subtasks, and linked issues.
- Also fetch its comments for additional context.
- These can be fetched in parallel for speed.

### Step 4: Generate the Requirements Document
- Synthesize all data using the **Requirements Document** format in `references/output_formats.md`.

---

## CREATE MODE WORKFLOW

### Step 1: Determine the Project Key
- If the user already provided a project key or Jira issue key, extract it from there.
- If the user provided a Jira URL, extract the project key from it.
- If no project key is determinable:
  1. List all accessible Jira projects.
  2. Present to the user:

     **"I found the following Jira projects. Which one should I create these issues in?"**

     | # | Key | Name | Type |
     |---|-----|------|------|
     | 1 | PROJ | Project Name | software |

  3. Wait for the user to pick before proceeding.

### Step 2: Discover Project Configuration
- Retrieve the project's available issue types.
- Confirm "Epic", "Story", and "Task" are available.
- If "Story" is absent but "User Story" is present, use "User Story" instead.
- If "Epic" is unavailable, inform the user and ask how to proceed.

### Step 3: Analyze and Break Down the Objective
Design a logical breakdown:
- **1 Epic** capturing the overall objective.
- **3–8 Stories** for user-facing capabilities — use "As a [user], I want [goal], so that [benefit]" format with acceptance criteria.
- **2–5 Tasks** for technical/non-user-facing work (infra, migrations, CI/CD, monitoring).
- For each item define: summary, description, priority (High/Medium/Low), labels.

### Step 4: Choose Creation Mode
- Ask: **"Would you like me to create these issues automatically, or would you prefer to review the plan first?"**
- If the user already indicated preference ("just do it", "go ahead", "review first"), honor it without asking again.

### Step 5: Propose for Review (if requested)
- Present the breakdown using the **Proposed Issue Breakdown** format in `references/output_formats.md`.
- Ask: **"Shall I create all of these? Or would you like to modify anything first?"**
- If the user requests changes, update the plan and re-present. Once confirmed, proceed to Step 6.

### Step 6: Create Issues in Jira
- **Create the Epic first.** If this fails, report the error and **stop** — do not create orphaned children.
- **Create Stories** under the epic, using the epic key returned from Step 6.
- **Create Tasks** under the same epic.
- If a child issue fails: report the error, continue with remaining issues, track all results.

### Step 7: Present Creation Summary
- Use the **Creation Summary** format in `references/output_formats.md`.

---

## IMPORTANT RULES

1. **Never fabricate data.** Only use information returned by the Jira connector.
2. If a field is empty or null, write "Not specified" — do not guess.
3. Mark all inferred non-functional requirements as *Inferred* with reasoning.
4. Look for acceptance criteria in description fields under headings like "Acceptance Criteria", "AC", or "Definition of Done".
5. In READ MODE: when stories have comments, check for scope changes or decisions that affect requirements.
6. Group related stories logically, not just in Jira order.
7. Use priority names from Jira exactly (Highest, High, Medium, Low, Lowest).
8. If any connector call fails, report the error but continue generating with whatever data was retrieved.
9. In CREATE MODE: always verify available issue types before creating.
10. In CREATE MODE: create the Epic **first** — if it fails, stop. Do not create orphaned children.
11. In CREATE MODE: keep summaries under 100 characters. Put details in description.
12. In CREATE MODE: if the user triggers creation again with the same objective, warn that this will create duplicates in Jira.
13. If creating a child issue fails with a linking error, still create it unlinked and note the issue in the summary.
