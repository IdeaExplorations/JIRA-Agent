# Output Formats

## Requirements Document (READ MODE)

Use this exact structure when generating a requirements document from a Jira epic:

---

# Requirements Document: [Epic Summary]

**Epic Key:** [KEY]
**Status:** [Status]
**Generated:** [Current Date]
**Priority:** [Priority]

---

## 1. Project Overview

[Synthesize the epic's description into a clear project overview — purpose, scope, and goals
based on the epic description and the collective child stories.]

### 1.1 Objectives
[List 3–5 key objectives derived from the epic and its stories]

### 1.2 Scope
[Define what is in scope and out of scope based on the stories present]

---

## 2. Functional Requirements

[For each story/task, create a numbered requirement. Group related stories together logically.]

### 2.1 [Logical Grouping Name]

| ID | Requirement | Source | Priority | Story Points |
|----|------------|--------|----------|-------------|
| FR-001 | [Requirement derived from story] | [STORY-KEY] | [Priority] | [Points] |

[Add detailed description for each requirement, including acceptance criteria if available.]

---

## 3. Non-Functional Requirements

[Infer from stories, labels, and descriptions. Consider: Performance, Security, Scalability,
Usability, Reliability, Compliance. Mark all inferred requirements as *Inferred* with reasoning.]

---

## 4. User Stories Summary

| Key | User Story | Status | Assignee | Points |
|-----|-----------|--------|----------|--------|
| [KEY] | As a [user], I want [goal] so that [benefit] | [Status] | [Assignee] | [Points] |

[If stories aren't in user story format, convert them based on their description.]

---

## 5. Acceptance Criteria Compilation

### [STORY-KEY]: [Summary]
- [ ] [Criterion 1]
- [ ] [Criterion 2]

[If AC is embedded in descriptions, look for headings like "Acceptance Criteria", "AC", "Definition of Done".]

---

## 6. Priority Matrix

### Critical (Must Have)
[Stories with Highest/High priority]

### Important (Should Have)
[Stories with Medium priority]

### Nice to Have (Could Have)
[Stories with Low/Lowest priority]

---

## 7. Dependencies and Risks

### 7.1 Dependencies
[From issue links, cross-references in descriptions, and comments]

### 7.2 Risks
- Stories without acceptance criteria
- Unassigned stories
- Stories with many comments (may indicate unclear requirements)
- Blocked stories or unresolved linked issues

---

## 8. Technical Considerations

[Infer from labels, components, descriptions, and comments:]
- Architecture considerations
- Integration points
- Data requirements
- Technology stack implications

---

## Appendix: Raw Story Details

<details>
<summary>[STORY-KEY]: [Summary]</summary>

**Description:**
[Full description text]

**Comments:**
[Comments with author and date]

</details>

---

## Proposed Issue Breakdown (CREATE MODE — Review Step)

Use this structure when presenting a breakdown for user review before creating:

---

## Proposed Issue Breakdown for: [Objective Title]

### Epic
- **Summary:** [Epic summary]
- **Description:** [Epic description]
- **Priority:** [Priority]
- **Labels:** [Labels]

### Stories

| # | Summary | Priority | Acceptance Criteria |
|---|---------|----------|---------------------|
| 1 | [Story summary] | [Priority] | [Brief AC] |

### Tasks

| # | Summary | Priority | Description |
|---|---------|----------|-------------|
| 1 | [Task summary] | [Priority] | [Brief desc] |

---

**"Shall I create all of these? Or would you like to modify anything first?"**

---

## Creation Summary (CREATE MODE — After Creating Issues)

Use this structure after all issues have been created:

---

## Creation Summary

**Epic:** [KEY] — [Summary]
**URL:** [Browse URL]

| # | Key | Type | Summary | Status |
|---|-----|------|---------|--------|
| 1 | AA-16 | Story | As a customer, I want to pay... | Created |
| 2 | AA-17 | Story | As an admin, I want to view... | Created |
| 3 | AA-18 | Task | Set up Stripe SDK and API keys | Created |
| 4 | AA-19 | Task | Configure webhook endpoints | FAILED: [error] |

**Total:** 3 of 4 issues created successfully.

---
