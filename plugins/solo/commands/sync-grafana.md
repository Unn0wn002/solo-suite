---
description: Sync project health from .solo/ into a Grafana dashboard and annotations (interpreting "Grapify" as Grafana)
argument-hint: [optional Grafana URL or dashboard name]
---
Use the memory-sync skill in Grafana mode. $ARGUMENTS

Read .solo/ and push project HEALTH to Grafana: generate/refresh a dashboard JSON with panels
for task counts (open/done/blocked), tasks-done-over-time, open audit findings by severity
(from audit tasks written back by site-doctor / stack audits), and a blockers table; and post
annotations for releases, audits, and key decisions. If a Grafana connector/MCP or API is
available (URL+token from .solo/config.md), create/update the dashboard by UID and post
annotations directly - idempotently, no duplicates; otherwise emit the dashboard JSON and
annotation payloads to import. Report the dashboard UID/URL (or JSON) and annotations posted.
Note: this reads "Grapify" as Grafana - if a different tool was meant, the same read->transform
->write-idempotently structure ports to it; just say which.

## Output
End with the 7-part contract: **Summary · Findings/Work done · Risks · Required fixes · Suggested tasks** (→ `.solo/tasks.md`, stable T-IDs) **· Verification · Next command** (exact slash command).
