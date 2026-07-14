---
description: Run the complete full-team development cycle from idea to production readiness — 17 roles across 16 phases, profile-aware, gates enforced.
argument-hint: [optional feature or project focus, optionally a profile like "profile: saas-application"]
---
Use the **project-memory-manager** skill in full-team-dev mode. $ARGUMENTS

Guide the user through the complete cycle — **Intake → PRD → Architecture → Contracts → UX/UI → Tasks → Build → Review → Tests → Browser QA → Security → Stack audit → Growth → Merge & release → Docs → Launch & handoff** — running each phase's commands in order, carrying `.solo/` memory between them, and **stopping at every gate**: a NO-GO halts the flow until its blockers are fixed.

**Project profile first.** Classify the project as one of: `public-marketing-site`, `saas-application`, `e-commerce`, `internal-application`, `api-service`, `library-package` (ask if unclear). Record exactly one standalone canonical line in `.solo/project.md`: `Project profile: <recognized-slug>`, and commit it before final evidence is minted. The evidence recorder/checker read that field from `HEAD:.solo/project.md`, not mutable working-tree text; missing, malformed, ambiguous, symlink-backed, or CLI-mismatched profile sources block N/A evidence. Phases marked with a profile condition run only when the profile (or `.solo/stack.md`) calls for them — and **every skipped phase/command must be reported as N/A with the evidence for why** (e.g. "skipped /stack:audit-supabase — stack.md records no Supabase", "skipped /growth:conversion-audit — internal admin tool, no public funnel"). Silent skips are not allowed.

**The 17 roles this flow staffs** (mirrored by the AgentRooms template `full-team-website.json`: 21 staged seats plus the stage-independent memory steward — 22 seat definitions across 14 stages including finalize, every staged seat mapped to a shipped `room-*` agent): Product Manager, Repo Analyst, Software Architect, UI/UX Designer, Frontend Developer, Backend Developer, Database Engineer, QA Engineer, Browser QA Engineer, Security Engineer, DevOps Engineer, Release Manager, Documentation Writer, Git/PR Manager, AI Agent Reviewer, Growth/Conversion Reviewer, Site Doctor — plus the mechanical Code Reviewer, Worktree Integrator, Evidence Finalizer, and output-only Production Gatekeeper seats — coordinated through the shared `.solo/` memory (with a Memory Steward when run as a multi-agent room; the steward's structured cutoff is `active_through_stage: docs`).

Recommended flow:

```
# 1/16 — Intake (PM + Repo Analyst)
/solo:start-session
/stack:intake
/stack:connector-check
/repo:map                  ← existing repos; N/A for greenfield (say so)
# 2/16 — PRD (PM)
/project:prd
/spec:feature-brief
/spec:acceptance
# 3/16 — Architecture (Architect)
/project:architecture
# 4/16 — Contracts (Architect + Database Engineer)
/spec:api-contract
/spec:data-contract
/spec:env-contract
# 5/16 — UX/UI (Designer)
/design:ux-flow
/design:component-system
# 6/16 — Tasks (PM + Architect)
/project:task-breakdown
/gate:before-code          ← GATE: no code until GO
# 7/16 — Build (Frontend + Backend + Database Engineers)
#   WORKTREE CONTRACT: COMMIT the planning memory first (.solo/ intake, PRD,
#   architecture, contracts, design, tasks — `git add .solo && git commit`),
#   THEN record BASE_SHA with the gate plugin's update_run_state.py helper
#   (`advance base` — it derives the SHA from git itself; run-state-v1) into
#   UNTRACKED .solo/run-state/<run_id>.json — NEVER a tracked file: a commit cannot
#   contain its own SHA. Builders receive BASE_SHA through that runtime
#   state (worktree agents branch from the DEFAULT branch, not this
#   session's HEAD; each builder first `git merge --ff-only $BASE_SHA`).
#   Every builder returns: worktree_path, branch, clean commit_sha, tests,
#   proposal (committed as .solo/proposals/<seat>-<run_id>.json in its branch).
/git:create-branch
/dev:implement-feature
#   Integrate BEFORE review: merge the builders' EXACT SHAs into ONE integration
#   commit (integration/<run_id>) and record the INTEGRATION SHA with
#   update_run_state.py advance integration (run-state-v1) in untracked
#   .solo/run-state/<run_id>.json — phases 8-15 (review through docs) first
#   verify `git rev-parse HEAD` equals INTEGRATION_SHA
#   (`update_run_state.py verify integration`). Phase 16's pre-freeze review
#   and memory handoff still run on that integration band; after the freeze,
#   only the Evidence Finalizer and Gatekeeper run, and both verify FINAL_SHA
#   (`update_run_state.py verify final`).
# 8/16 — Review (Code Reviewer + AI Agent Reviewer + Designer)
/dev:code-review
/ai:review-output          ← AI-output audit between EVERY pair of major phases from here on
/design:ui-review          ← post-implementation UI review against design.md
# 9/16 — Tests (QA Engineer)
/test:unit
/test:integration
/test:e2e
/test:edge-cases
# 10/16 — Browser QA (Browser QA Engineer)
/browser:console-errors
/browser:visual-check
/browser:mobile-test
# smoke-test + form-submit-test are manual-only (state-changing): ask the user to run
# /browser:smoke-test and /browser:form-submit-test and record their results.
# 11/16 — Security (Security Engineer)
/security:threat-model
/security:authz-matrix
# Static policy/matrix review runs automatically. /security:rls-test is
# manual-only live testing: if stack.md records Supabase/RLS, hand the exact
# disposable-test-tenant plan to the user and ask them to invoke it; otherwise
# record N/A with evidence. Never invoke it from this orchestration command.
# 12/16 — Stack audit (Site Doctor)
/site-doctor:full-checkup
/stack:audit-vercel        ← each vendor audit ONLY if that provider is in stack.md;
/stack:audit-supabase      ← every skipped vendor reported as N/A with evidence
/stack:audit-cloudflare
/stack:audit-tags
/stack:audit-payments
# 13/16 — Growth (Growth/Conversion Reviewer) — public-marketing-site / e-commerce / saas only
/growth:conversion-audit   ← N/A (with profile evidence) for internal/api/library projects
# 14/16 — Merge & release (Git/PR Manager, DevOps, Release Manager)
/security:secrets-fix      ← manual-only command: run it WITH the user, not for them
/git:commit-plan
/git:pr-review
/gate:before-merge         ← GATE
/release:ci-setup
/release:preflight
/release:deploy-plan
/release:rollback-plan
/site-doctor:monitoring
/gate:before-deploy        ← GATE
# 15/16 — Docs (Documentation Writer)
/docs:update
/docs:setup-guide
/docs:runbook
/git:release-notes
# 16/16 — Launch (Evidence Finalizer + OUTPUT-ONLY Production Gatekeeper)
/ai:review-output          ← final AI-output audit before the freeze
/solo:handoff-memory       ← handoff/tasks/decisions/risks land BEFORE the freeze
#   RELEASE FREEZE: commit EVERYTHING (code, CI, release plans, docs, and the
#   just-updated project memory). That commit is FINAL_SHA — record it with
#   update_run_state.py advance final (run-state-v1: derived from git by the
#   helper, monotonic, FROZEN once set) into UNTRACKED
#   .solo/run-state/<run_id>.json (a commit cannot contain its own SHA, so
#   tracked files are structurally impossible carriers).
/gate:finalize-evidence    ← all 14 records minted at FINAL_SHA (never earlier)
#   After the freeze NOTHING tracked changes: only untracked
#   .solo/gate-evidence/ and .solo/run-state/ files are created (gitignore
#   both). The memory steward does NOT run again after the finalizer.
/gate:production-ready     ← GATE (output-only): 14 categories, BLOCKED stops
#   launch; the verdict and blockers live in the gate's OUTPUT — a BLOCKED
#   result reopens work in the NEXT cycle, before a new freeze.
```

**Evidence lifecycle (records come LAST, all at once):** specialists produce raw artifacts (`.solo/*.md`, code, tests, plans, docs) as they work — they do **not** write `.solo/gate-evidence/` records, because a record created against an intermediate commit is invalid by construction. When everything is final and committed (FINAL_SHA recorded via `update_run_state.py advance final` — the run-state-v1 contract, SHA derived from git by the helper, frozen once set — in UNTRACKED `.solo/run-state/<run_id>.json`, never in `.solo/handoff.md` or any other tracked file, since a commit cannot contain its own SHA), `/gate:finalize-evidence` re-runs every applicable category command through the canonical **`record_evidence.py`** workflow (policy-validated full argv, captured exit code, git-derived HEAD + committed-tree digest) and creates all 14 records — verified, or matrix-permitted N/A bound to the canonical profile in committed `.solo/project.md` (the seven mandatory categories are never N/A) — against FINAL_SHA. These are unsigned, self-attested local evidence records: the checker validates their content and checkout binding, but the copyable `recorder` label cannot prove which process authored conforming JSON. Phase 16's gate then runs `check_evidence.py`, which derives HEAD and the committed profile itself and rejects any record whose commit, committed-tree digest, or N/A profile binding differs, so early, stale, or caller-selected records block the launch gate, by design.

Between phases: report progress (phase n/16), what was produced, the N/A list with evidence, and the next command. Resume-aware — if `.solo/` shows earlier phases done, continue from where the flow stopped. This flow exercises **all 17 component plugins directly**: solo, stack, repo, project, spec, design, git, dev, ai (`/ai:review-output` in phases 8 and 16), test, browser, security, site-doctor, growth, release, docs, and gate.

## Output
End with the 7-part contract: **Summary · Findings/Work done · Risks · Required fixes · Suggested tasks** (→ `.solo/tasks.md`, stable T-IDs) **· Verification · Next command** (exact slash command).
