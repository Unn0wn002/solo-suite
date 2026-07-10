---
description: Run a full website health audit (security, performance, SEO, accessibility, links)
argument-hint: [url or project path]
---
Use the website-audit skill to run a complete audit of: $ARGUMENTS

If no target was provided, first ask for the site URL and/or local project path.
Run the bundled scripts, work through all six categories, and produce the
standard severity-ranked report. Finish by offering to apply fixes with the
website-fix skill.

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
