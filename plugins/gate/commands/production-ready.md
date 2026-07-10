---
description: Score launch readiness 0–100 across 12 categories and give a launch status — with hard blockers that force BLOCKED regardless of score.
argument-hint: [optional scope]
---
Use the **production-readiness-reviewer** skill. $ARGUMENTS

Run the full 12-section checklist (Product, Design, Backend, Frontend, Security, Testing, Performance, SEO, Analytics, Deployment, Monitoring, Docs) as evidence, then score **12 categories 0–10** — Product, Architecture, Frontend, Backend, Database, Security, Performance, SEO, Analytics, Deployment, Monitoring, Docs — and the overall score out of 100, in the skill's exact format.

**Launch is BLOCKED regardless of score if ANY is true:** SEO basics missing · analytics missing · error tracking missing · mobile broken · serious accessibility issues · auth/RLS/payments/email not *verified* · secrets committed · no auth where needed · RLS off where needed · no backup/rollback.

Finish with **Launch Status: BLOCKED / SAFE TO LAUNCH / LAUNCH WITH WARNINGS** and the ordered must-fix list.

## Output
End with exactly:
- **Verdict** — GO / NO-GO (one missing blocker = NO-GO; never averaged away)
- **Blockers** — each failed check, with its evidence and the command that clears it
- **Passed checks** — with the evidence for each
- **Nits** — non-blocking improvements
- **Suggested tasks** → `.solo/tasks.md` (stable T-IDs); record open blockers in `.solo/risks.md`
- **Next command** — what clears the top blocker, or the next phase command on GO
