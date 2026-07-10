---
description: Run a full database audit (schema, indexes, queries, security, integrity) for PostgreSQL, MySQL, or SQLite
argument-hint: [connection string, db file path, or schema dump]
---
Use the database-audit skill to audit: $ARGUMENTS

If no target was provided, first ask for the engine and how to access it
(connection string, SQLite file path, or schema dump). Use the read-only
queries from the skill's references/audit-queries.md, work through all six
categories, and produce the standard severity-ranked report. Finish by
offering to apply fixes with the database-fix skill.

## Output — evidence-based audit format
Never just "good" or "bad" — every claim names its proof. If nothing was actually inspected for an area, say "not checked", don't guess. End with exactly:

```
## Status
PASS / WARNING / FAIL

## Evidence Checked
- File: …
- Config: …
- Page: …
- Command output: …
- Screenshot: …
- Connector data: …
(only the lines that apply — but at least one; no evidence, no finding)

## Findings
1. …
2. …

## Risk Level
Low / Medium / High / Critical

## Required Fixes
1. …

## Suggested Tasks
→ `.solo/tasks.md` entries with stable T-IDs

## Verification Steps
1. …

## Next Recommended Command
/…
```
