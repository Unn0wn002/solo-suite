---
description: Deep OWASP Top 10 security review of a web app (injection, auth, access control, XSS, SSRF, secrets, CVEs)
argument-hint: [url or project path]
---
Use the security-review skill to perform a deep security assessment of: $ARGUMENTS

If no target was provided, ask for the site URL and/or codebase path, and
confirm the user is authorized to test it. Run the secret scanner, walk the
full OWASP Top 10, and produce the report with OWASP category + non-destructive
repro per finding. Only test systems the user owns or is authorized to test.

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
