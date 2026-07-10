---
description: Audit web forms - usability, validation, accessibility, conversion, security, spam protection
argument-hint: [url or form markup]
---
Use the forms-audit skill on: $ARGUMENTS

If no target was provided, ask which forms matter and what each is for. Walk
through completing each form, then review friction/design, validation & error
handling, accessibility, submission feedback, security & spam protection, and
mobile. Rank by conversion and access impact.

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
