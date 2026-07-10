---
name: agent-room-templates
description: Ready-made multi-agent "room" templates for running a phase of work with several AI coding agents in parallel or sequence — who's in the room, what context each agent gets from .solo/, what each produces, and how the handoff works. Use when the user says agent rooms, AgentRooms, multi-agent workflow, "set up a room", parallel agents, or wants to split a phase across Claude/Codex/Gemini-style agents cleanly.
---

# Agent Room Templates

A "room" is a small, purpose-built team of AI agents working one phase together: each seat has a role, a context package (the exact `.solo/` files it reads), a deliverable, and a handoff target. Rooms keep multi-agent work from turning into contradictory edits — one writer per artifact, everything flowing through `.solo/`.

> Interpretation note: this implements "AgentRooms" as reusable multi-agent workflow templates. If AgentRooms is a specific product/tool you use, say so — the templates port to it directly.

## Room rules (all templates)
- **One writer per artifact** — two agents never edit the same `.solo/` file or code area in the same room.
- **Context is explicit** — each seat is handed named `.solo/` files, not "the whole repo, good luck".
- **Every seat ends with a handoff** — checked by `/ai:handoff-check` before the next seat starts.
- **Model routing** — pick who sits where with `/ai:compare-models`; audit anything produced with `/ai:review-output`.

## The templates

### 1. Planning Room
Seats: **PM agent** (reads `project.md`, writes `prd.md` — `/project:prd`, `/spec:feature-brief`) → **Architect agent** (reads `prd.md`, writes `architecture.md`, `api-contract.md`, `data-contract.md`, `env-contract.md` — `/project:architecture`, `/spec:*`) → **Criteria agent** (writes acceptance criteria into the PRD — `/spec:acceptance`). Exit gate: `/gate:before-code`.

### 2. Build Room
Seats: **Implementer** (reads `tasks.md` + contracts, builds one task — `/dev:implement-feature`, logs to `decisions.md`) → **Reviewer** (independent agent, ideally a different model — `/dev:code-review`, `/ai:review-output`). Sequence per task: implement → review → fix. Exit gate: `/gate:before-merge`.

### 3. QA Room
Seats: **Test writer** (writes/executes `/test:unit`, `/test:integration`, `/test:e2e` → `tests.md`) ∥ **Browser QA** (`/browser:smoke-test`, `/browser:console-errors`, `/browser:mobile-test` → `bugs.md`). Runs in parallel; both feed `bugs.md`/`tasks.md`.

### 4. Hardening Room
Seats: **Security agent** (`/security:threat-model`, `/security:authz-matrix`, `/security:rls-test` → `risks.md`) ∥ **Auditor agent** (`/site-doctor:full-checkup`, `/stack:audit-*` → `tasks.md`). Exit: findings triaged, criticals fixed.

### 5. Launch Room
Seats: **Release agent** (`/release:preflight`, `/release:deploy-plan`, `/release:rollback-plan`, `/site-doctor:monitoring`, then `/gate:before-deploy` → `release.md` + `monitoring.md`) → **Docs agent** (`/docs:update`, `/docs:setup-guide`, `/docs:runbook`, `/git:release-notes`) → **Gatekeeper** (`/gate:production-ready`, then `/solo:handoff-memory`). Nothing ships on a NO-GO.

## Ready-made JSON templates (`agentsrooms/`)
Four machine-readable room files ship with this skill, one per common job — hand a file to an orchestrator, or paste a seat's entry as that agent's work order:

- `agentsrooms/full-team-website.json` — idea → launch, 13 seats across 10 stages (the /solo:full-team-dev flow, staffed)
- `agentsrooms/site-doctor-audit.json` — parallel site + vendor audit, then triage into a fix order (exit gate: `/gate:score-project`)
- `agentsrooms/production-release.json` — preflight + plans + monitoring → deploy gate → docs → launch gate
- `agentsrooms/bug-fix-loop.json` — reproduce → fix → verify, **looping** until the repro dies (with an /ai:repair-cycle escape hatch)

Schema (`solo-suite/agentroom-v1`): `stages` (arrays of seat ids; seats sharing a stage run in parallel), `seats[]` each with `role`, `model_hint`, `reads`/`writes` (exact `.solo/` files), `commands`, `deliverable`, `handoff_to` + `handoff_check`, plus room `rules`, an `exit_gate`/`exit_criteria`, and optional `loop`. Handoff semantics: seats sharing a stage run in parallel and never hand off to each other — every `handoff_to` targets a seat in a strictly later stage; repetition is declared only via the explicit `loop` block; a null `exit_gate` requires an `exit_gate_note`. To customize: copy a file, edit seats/stages, keep one-writer-per-artifact true, then re-run `scripts/validate_rooms.py` (stdlib) — it checks seat/stage placement, the handoff graph, per-stage writers, gates, and that every referenced command exists.

## Output of this skill
When asked for a room, output: the template name, each seat with (role, model suggestion, exact `.solo/` context files, commands to run, deliverable), the sequence/parallelism, and the exit gate — ready to paste into each agent's first prompt.

## Output
End every run with these seven sections:
1. **Summary** — what was checked or created.
2. **Findings / Work done** — what was found, changed, or decided.
3. **Risks** — anything uncertain, dangerous, incomplete, or blocked.
4. **Required fixes** — must-fix items before moving forward.
5. **Suggested tasks** — concrete entries for `.solo/tasks.md`, each with a stable T-ID.
6. **Verification** — how to prove the result works.
7. **Next command** — the exact next slash command to run.

## Session lifecycle
Runs inside a session the solo plugin bookends: `/solo:start-session` restores `.solo/` context at the start and `/solo:end-session` saves it at the end. Read `.solo/` before acting; write findings, decisions, and tasks back (stable T-IDs) so the next command — or the next agent — picks up cleanly.
