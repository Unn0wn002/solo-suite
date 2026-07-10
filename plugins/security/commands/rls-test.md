---
description: Test Supabase RLS policies with realistic user roles.
argument-hint: [optional table]
---
Use the **authz-security-reviewer** skill in rls-test mode, with **connector-auditor** for the live Supabase schema/policies when available. $ARGUMENTS

For each table: confirm RLS is enabled, then test anon / owner / non-owner / admin against SELECT/INSERT/UPDATE/DELETE and confirm owner/tenant isolation. Give pass/fail per policy and the SQL to fix gaps.

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
