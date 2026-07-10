---
description: Plan a load/stress test or interpret results - scenarios, thresholds, bottlenecks, capacity
argument-hint: [plan | interpret] [target or results]
---
Use the load-testing skill for: $ARGUMENTS

Only test systems the user owns, against a staging/production-like environment.
For planning, define the question, a realistic load model, thresholds, and test
type. For interpreting, report throughput/latency-percentiles/error-onset/
breaking-point, identify the bottleneck with evidence, and give capacity/scaling
recommendations.

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
