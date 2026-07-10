---
name: project-memory-manager
description: Maintain persistent project memory for a solo developer across sessions — start-session resume, end-session save, session handoffs, task state, decision log, project status, and running a full development cycle. Owns the shared .solo/ directory convention that every other skill in the suite (and any other plugin) reads and writes. Use when the user says start session, end session, resume, handoff, "save context", "where were we", "what's next", "next step", "project status", "run a cycle", run-cycle, or wants to initialize project memory. Also use at the start of any session on an existing project to restore context.
---

# Project Memory Manager

A solo developer's biggest tax is re-loading context: every session starts with "where was I?" This skill makes that cost near zero by keeping project state in plain markdown files that any session — and **any other skill or plugin** — can read and update. This file layout is the interop contract for the whole solo-team suite.

## The `.solo/` contract (shared memory)

All files live in `.solo/` at the project root, are plain markdown, and are committed to git (history lives in git, so files stay current-state only). The contract is **16 standard files plus an optional `config.md`** — everywhere the suite says "the 16-file contract", config.md is not counted:

| File | Owner (primary writer) | Contents |
|---|---|---|
| `project.md` | this skill (initialize) | Project identity one-pager: what it is, who it's for, current phase, links |
| `stack.md` | stack-advisor (`/stack:intake`) | The project's tools: hosting, DNS/CDN/WAF, database, auth, storage, analytics/tags, email, payments, repo/CI |
| `prd.md` | product-manager (`/project:prd`) | Problem, users, stories, scope, non-goals, success metrics |
| `architecture.md` | software-architect (`/project:architecture`) | Components, boundaries, data-flow — reads `prd.md` first |
| `api-contract.md` | api-contract-designer (`/spec:api-contract`) | Endpoint/operation contract — reads `architecture.md` first |
| `data-contract.md` | software-architect (`/spec:data-contract`) | Entities, constraints, relationships, indexes |
| `env-contract.md` | software-architect (`/spec:env-contract`) | Required env vars & secrets by environment — names only, never values |
| `design.md` | ui-ux-designer | UX flows, component system, design decisions |
| `tasks.md` | everyone | The single source of truth for work status (stable T-IDs) |
| `decisions.md` | everyone (append-only) | Dated decision log with reasoning — `/dev:implement-feature` logs here |
| `risks.md` | gates, security & audit skills | Open risks with severity and owner; gates read this before verdicts |
| `bugs.md` | `/dev:fix-bug`, browser & site-doctor findings | Known bugs: repro, severity, status |
| `tests.md` | qa-engineer (`/test:*`) | What's tested, how, results, coverage gaps |
| `release.md` | devops-engineer (`/release:preflight`) | Release state: preflight results, deploy & rollback plans, history |
| `monitoring.md` | observability (`/site-doctor:monitoring`) | Error tracking, uptime, logs, alerts — what exists and where |
| `handoff.md` | this skill | Latest session state — overwritten each handoff |
| `config.md` | memory-sync (optional) | Local settings such as sync targets (Obsidian vault path, Grafana URL) — gitignore if sensitive |

**Read→write flow (the standard):** `/project:prd` writes `prd.md` → `/project:architecture` reads `prd.md`, writes `architecture.md` → `/spec:api-contract` reads `architecture.md`, writes `api-contract.md` → `/dev:implement-feature` reads `tasks.md` + contracts, logs to `decisions.md` → `/test:*` writes `tests.md` → `/release:preflight` writes `release.md` → this skill writes `handoff.md`. A file that doesn't exist yet is created on first write; missing files are never an error, just a gap `/solo:self-check` reports.

**Rules every skill follows** (including third-party skills that want to integrate):
1. **Read before working**: at minimum `handoff.md` + `tasks.md`; plus whichever artifact is relevant (prd/architecture/design). **Any skill that audits or builds also reads `stack.md`** so its advice fits the project's real tools instead of guessing.
2. **Update after working**: move tasks between sections in `tasks.md`; append (never edit) `decisions.md` for anything a future session would ask "why?" about.
3. **Never delete memory** — mark superseded, don't erase.

### `tasks.md` format
```markdown
# Tasks
## Doing
- [ ] T14: Wire signup form to /api/auth/register  (feature: auth)
## Todo
- [ ] T15: Password reset flow  (feature: auth)
## Blocked
- [ ] T09: Stripe webhooks  (blocked on: prod keys)
## Done
- [x] T13: users table + migration  (2026-07-07)
```
IDs are stable (T1, T2…) so any skill can reference "T14" unambiguously.

### `decisions.md` entry format
```markdown
## 2026-07-07 — Postgres over MySQL
Why: PITR + jsonb; team knows it. Alternatives: MySQL, SQLite.
Consequence: use TEXT+CHECK not ENUM to keep portability.
```

### `handoff.md` format (latest session only)
```markdown
# Handoff — 2026-07-07
## Done this session
## Current state (branch, what runs, what's broken)
## Next steps, in order
## Gotchas / open questions
```

## Mode: initialize

If `.solo/` doesn't exist on a real project: create the directory, seed `tasks.md`, `decisions.md`, `handoff.md` with the templates above (leave prd/architecture/design for their skills, and `stack.md` for `/stack:intake` — running it early is recommended so every command is stack-aware), and **add one line to the project's `CLAUDE.md`** (create it if absent):

```
Project memory lives in .solo/ — read handoff.md and tasks.md at session start; update them when work state changes.
```

That line makes every future Claude Code session in this repo memory-aware automatically, with or without slash commands.

## Mode: handoff (`/solo:handoff-memory`)

Run before context gets long, or any time you want to checkpoint mid-work. Look at what actually happened this session — files changed, tasks progressed, decisions made — then: rewrite `handoff.md` fresh, update `tasks.md` statuses, append any unlogged decisions to `decisions.md`. Be concrete in "Next steps" (commands to run, files to open), because the reader is a cold-start future session. Ten minutes of handoff saves an hour of re-discovery. (To *close out* a session specifically, use end-session, which does this plus an explicit blockers/next-task pass.)

## Mode: next step (`/solo:next-step`)

Read `handoff.md`, `tasks.md`, `prd.md`, `architecture.md`. Recommend the **single** highest-leverage next action with reasoning: prefer unblocking blocked work, then finishing Doing before starting Todo, then the task that de-risks the project most (riskiest assumption first, per the PRD). Name the exact task ID, the first concrete step, and which skill/command to use for it (e.g. "T15 → `/dev:implement-feature` T15").

## Mode: project status (`/solo:project-status`)

Roll up a status report: done / doing / blocked counts and highlights, completion estimate against PRD scope, decisions made recently, risks (stale blocked tasks, drift between PRD and what's actually being built), and the recommended next step. Suitable to paste into a standup or just to re-orient after time away.

## Mode: start session (`/solo:start-session`)

The first thing to run when returning to a project — it turns cold-start back into warm-start. Read `stack.md`, `handoff.md`, `tasks.md`, `prd.md`, `architecture.md`, `design.md`, and `decisions.md`, then give a tight re-orientation:
- **Where things stand**: current branch/state, what runs, what's broken (from `handoff.md`).
- **What was in flight**: tasks in Doing, and anything Blocked (with why).
- **Worth remembering**: recent decisions that constrain today's work.
- **Do this next**: the recommended next task with its ID, first concrete step, and the command to run (same selection logic as next-step).
Keep it scannable — the point is to be productive in under a minute. If `stack.md` is missing, recommend `/stack:intake` as the first action of the session so everything downstream is stack-aware. If `.solo/` doesn't exist, offer to initialize it. This is the bookend to end-session.

## Mode: end session (`/solo:end-session`)

The session-closing ritual — a complete handoff plus explicit close-out, so nothing is lost between sessions. It's the richer sibling of handoff mode (which can be run any time mid-work); end-session is what you run to *finish*. Do all of:
- **Progress**: move each touched task in `tasks.md` — Done (with date) or back to Doing/Todo as accurate.
- **Blockers**: record anything Blocked explicitly, with the reason and what would unblock it, so it's visible to start-session and project-status.
- **Stack**: if the stack changed this session (new provider, swapped tool, new service), update `stack.md` and log the change in `decisions.md`.
- **Decisions**: append any unlogged decisions to `decisions.md` with reasoning.
- **Handoff**: rewrite `handoff.md` fresh (done this session / current state / next steps in order / gotchas), **ending with the single next task** so the next start-session resumes instantly.
Be concrete — the reader is a future cold-start session. If the user mirrors their project outward, offer to run **memory-sync** (`/solo:sync-obsidian`, `/solo:sync-grafana`) to reflect the just-saved state into their vault/dashboard. This is the bookend to start-session.

## Mode: run cycle (`/solo:run-cycle`)

Orchestrate **one complete development cycle** for a single task — selection through done — by invoking the right skill at each step and moving the task through `tasks.md` as you go. This is the suite's end-to-end loop in one command; it ties every plugin together:
1. **Select** the next task (next-step logic); confirm scope against `prd.md`. Read `stack.md` so every step fits the real stack; if it's missing and the task touches infrastructure or vendors, offer `/stack:intake` first.
2. **Design** if the task needs UX/UI → **ui-ux-designer** (skip if not applicable).
3. **Implement** end to end → **fullstack-developer** (move task to Doing).
4. **Review** the change → **code-reviewer**; resolve Must-fix items before continuing.
5. **Test** against acceptance criteria and edges → **qa-engineer**.
6. **Audit** if relevant → **site-doctor** (`security-scan`, `a11y`, `perf`, etc.) or the **vendor audits** when the task touches that vendor (`/stack:audit-cloudflare`, `/stack:audit-vercel`, `/stack:audit-supabase`, `/stack:audit-tags`, `/stack:audit-payments`); fold fixes back in.
7. **Document** if the change warrants it → **documentation-writer**.
8. **Save** (end-session logic): task → Done, decisions logged, `handoff.md` refreshed.
**Stop and ask** at any gate needing a human decision — ambiguous scope, a failing Must-fix, a risky migration. Do one cycle per invocation unless told to continue; between cycles the memory is consistent, so it's safe to stop anytime. If a step's skill isn't installed, do a lighter inline version and note it.

## Mode: full-team-dev (`/solo:full-team-dev`)
The master orchestrator: run the **complete** full-team cycle from idea to production readiness — 15 phases: Intake, PRD, Architecture, UX/UI, Task breakdown, Spec contracts, Backend, Frontend, Tests, Browser QA, Security, Stack audit, Release, Documentation, Handoff. It executes the recommended flow in the `/solo:full-team-dev` command in order, carrying `.solo/` between phases, skipping steps that don't apply to the stack (and saying so), reporting progress as phase n/15, and **hard-stopping at every gate** (`/gate:before-code`, `/gate:before-merge`, `/gate:before-deploy`, `/gate:production-ready`) — a NO-GO or RED halts until its blockers are resolved. Resume-aware: if `.solo/` shows phases already done, it continues from where the flow stopped instead of restarting. This is run-cycle's big sibling — run-cycle does one task; full-team-dev does the whole product.

## Working with other skills & plugins

Every solo-team skill reads/writes through this contract — that's how the PM's scope reaches the developer and the developer's state reaches the release checklist. Other plugins integrate the same way: e.g. after **site-doctor** runs an audit, its prioritized fix list should be captured as tasks in `tasks.md` and the audit noted in `handoff.md`. When you see valuable output from any tool or skill, offer to persist it into memory so it survives the session.
