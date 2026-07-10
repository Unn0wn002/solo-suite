---
description: Run the complete full-team development cycle from idea to production readiness — 15 phases, every plugin, gates enforced.
argument-hint: [optional feature or project focus]
---
Use the **project-memory-manager** skill in full-team-dev mode. $ARGUMENTS

Guide the user through the complete cycle — **Intake → PRD → Architecture → Contracts → UX/UI → Tasks → Build → Review → Tests → Browser QA → Security → Stack audit → Merge & release → Docs → Launch & handoff** — running each phase's commands in order, carrying `.solo/` memory between them, and **stopping at every gate**: a NO-GO halts the flow until its blockers are fixed.

Recommended flow (skip steps that don't apply, e.g. no Supabase → skip its audit; say what was skipped and why):

```
# 1/15 — Intake
/solo:start-session
/stack:intake
/repo:map
# 2/15 — PRD
/project:prd
/spec:feature-brief
/spec:acceptance
# 3/15 — Architecture
/project:architecture
# 4/15 — Contracts
/spec:api-contract
/spec:data-contract
/spec:env-contract
# 5/15 — UX/UI
/design:ux-flow
/design:component-system
# 6/15 — Tasks
/project:task-breakdown
/gate:before-code          ← GATE: no code until GO
# 7/15 — Build
/git:create-branch
/dev:implement-feature
# 8/15 — Review
/dev:code-review
# 9/15 — Tests
/test:unit
/test:integration
/test:e2e
# 10/15 — Browser QA
/browser:smoke-test
/browser:console-errors
/browser:form-submit-test
/browser:visual-check
/browser:mobile-test
# 11/15 — Security
/security:threat-model
/security:authz-matrix
/security:rls-test
# 12/15 — Stack audit
/site-doctor:full-checkup
/stack:audit-vercel
/stack:audit-supabase
/stack:audit-cloudflare
/stack:audit-tags
/stack:audit-payments
# 13/15 — Merge & release
/security:secrets-fix
/git:commit-plan
/git:pr-review
/gate:before-merge         ← GATE
/release:preflight
/release:deploy-plan
/release:rollback-plan
/site-doctor:monitoring
/gate:before-deploy        ← GATE
# 14/15 — Docs
/docs:update
/docs:setup-guide
# 15/15 — Launch & handoff
/gate:production-ready     ← GATE: BLOCKED stops launch
/solo:handoff-memory
```

Between phases: report progress (phase n/15), what was produced, and the next command. Resume-aware — if `.solo/` shows earlier phases done, continue from where the flow stopped.

## Output
End with the 7-part contract: **Summary · Findings/Work done · Risks · Required fixes · Suggested tasks** (→ `.solo/tasks.md`, stable T-IDs) **· Verification · Next command** (exact slash command).
