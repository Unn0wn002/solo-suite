---
description: Score production readiness 0–100 across 12 categories — scoring only, no launch verdict; the gate itself is /gate:production-ready.
argument-hint: [optional scope]
---
Use the **production-readiness-reviewer** skill, scoring only. $ARGUMENTS

Run the 12-section checklist as evidence and produce the skill's exact score block — 12 categories 0–10 and the overall /100 — but stop there: **no Launch Status, no GO/NO-GO**. Would-be hard blockers met along the way are listed as risks with their fix commands, not turned into a verdict. Use this as the trend metric between gate runs; when you need the enforced verdict, run `/gate:production-ready`.

Record the dated score in `.solo/project.md` so progress is visible across sessions.

## Output
End with the 7-part contract: **Summary · Findings/Work done · Risks · Required fixes · Suggested tasks** (→ `.solo/tasks.md`, stable T-IDs) **· Verification · Next command** (exact slash command).
