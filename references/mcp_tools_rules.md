# MCP Connector Reference

This file contains only supplementary guidance that the connector itself does not provide.

---

## JQL Patterns

### Fetch children of an epic (try `parent` first, fall back to `Epic Link`)

```
parent = EPIC-KEY ORDER BY created ASC
```

```
"Epic Link" = EPIC-KEY ORDER BY created ASC
```

### Search by project and issue type

```
project = PROJ AND issuetype = Story ORDER BY priority DESC
```

### Search unassigned issues in an epic

```
parent = EPIC-KEY AND assignee is EMPTY
```

---

## Issue Type Mapping

| Logical Role | Jira Issue Type | Notes |
|---|---|---|
| Epic | `Epic` | Parent container for stories and tasks |
| Story | `Story` or `User Story` | Use whichever is available in the project |
| Task | `Task` | For technical/non-user-facing work |

Always verify available types via the connector before creating issues.

---

## Field Notes

- **Acceptance Criteria**: May be a dedicated field or embedded in `description` under headings like "Acceptance Criteria", "AC", or "Definition of Done".
- **Priority values**: Use Jira's exact labels — `Highest`, `High`, `Medium`, `Low`, `Lowest`.
- **Summary length**: Keep under 100 characters. Put details in `description`.
- **Epic linking**: Pass the epic key as `parentKey` when creating a Story or Task. If this fails with a linking error, create the issue unlinked and note it in the summary.
