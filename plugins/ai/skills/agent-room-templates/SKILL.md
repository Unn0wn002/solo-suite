---
name: agent-room-templates
description: Ready-made multi-agent "room" templates for running a phase of work with several AI coding agents in parallel or sequence — who's in the room, what context each agent gets from .solo/, what each produces, and how the handoff works. Use when the user says agent rooms, AgentRooms, multi-agent workflow, "set up a room", parallel agents, or wants to split a phase across Claude/Codex/Gemini-style agents cleanly.
---

# Agent Room Templates

A "room" is a small, purpose-built team of AI agents working one phase together: each seat has a role, a context package (the exact `.solo/` files it reads), a deliverable, and a handoff target. Rooms keep multi-agent work from turning into contradictory edits — one writer per artifact per stage, everything flowing through `.solo/`.

> Interpretation note: this implements "AgentRooms" as reusable multi-agent workflow templates. If AgentRooms is a specific product/tool you use, say so — the templates port to it directly.

## Room rules (all templates)
- **One writer per artifact per stage** — two seats never edit the same `.solo/` file or code area concurrently in one stage. A declared later stage may update the same artifact sequentially.
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
Seats: **Security agent** runs static `/security:threat-model` and
`/security:authz-matrix` → `risks.md`. Live `/security:rls-test` is manual-only:
the agent may prepare a disposable-test-tenant plan but must hand invocation
to the human; it never runs automatically in the room. **Auditor agent** runs
`/site-doctor:full-checkup`, `/stack:audit-*` → `tasks.md`. Exit: findings
triaged, criticals fixed.

### 5. Launch Room
Seats: **Release agent** (`/release:preflight`, `/release:deploy-plan`, `/release:rollback-plan`, `/site-doctor:monitoring`, then `/gate:before-deploy` → `release.md` + `monitoring.md`) → **Docs agent** (`/docs:update`, `/docs:setup-guide`, `/docs:runbook`, `/git:release-notes`, and `/solo:handoff-memory` BEFORE the freeze) → *orchestrator freeze: commit everything, record FINAL_SHA in untracked `.solo/run-state/`* → **Evidence Finalizer** (`/gate:finalize-evidence` — mints all 14 records at FINAL_SHA) → **Gatekeeper** (`/gate:production-ready`, OUTPUT-ONLY: zero tracked writes after the freeze; handoff-memory belongs BEFORE the freeze, never after the gate). Nothing ships on a BLOCKED verdict.

## Ready-made JSON templates (`agentsrooms/`)
Four machine-readable room files ship with this skill, one per common job. **They are validated work-order specifications, not an executable runtime** — execution is documented in `references/runner.md`: drive them with the shipped Claude Code agent definitions (`plugins/ai/agents/room-*.md`, one per seat role) or any external orchestrator, pasting a seat's entry as that agent's work order:

- `agentsrooms/full-team-website.json` — idea → launch, 21 staged seats across 14 stages (discovery → architecture → design → build → **integrate** → review → qa → hardening → growth → merge → release → docs → **finalize** → launch-gate) plus the stage-independent memory steward — 22 seat definitions total; the /solo:full-team-dev flow's 17 specialist roles plus the mechanical integrator, code-review, evidence-finalizer and output-only gatekeeper seats; every staged seat maps to a shipped `room-*` agent and the steward's structured cutoff is `active_through_stage: "docs"`
- `agentsrooms/site-doctor-audit.json` — parallel site + vendor audit, then triage into a fix order (exit gate: `/gate:score-project`)
- `agentsrooms/production-release.json` — preflight + plans + monitoring → deploy gate → docs → orchestrator freeze (structured `evidence.freeze` contract) → evidence finalizer → OUTPUT-ONLY launch gate
- `agentsrooms/bug-fix-loop.json` — reproduce → fix → verify, **looping** until the repro dies (with an /ai:repair-cycle escape hatch)

Schema (`solo-suite/agentroom-v1`, formal contract in `schema/agentroom-v1.schema.json` — applied FIRST by the validator, so malformed root/seat/stage/run/profile/gate-map/loop types come back as validation errors, never crashes): `stages` (objects `{id, seats[]}` with unique ids; seats sharing a stage run in parallel; legacy list-of-lists still accepted), `seats[]` each with `role`, `model_hint`, `reads`/`writes` (exact `.solo/` files), optional `proposes` (shared-memory proposals for the steward), optional `workspace` (owned worktree — `worktree:*` values activate the room-level `worktrees` contract), optional `applies_to` (recognized project profiles only), `commands`, `deliverable`, `handoff_to` (seat id, LIST of seat ids for fan-out into a parallel stage, or null — permitted only on the exit-gate executor) + `handoff_check`; room-level `memory_steward` (the single seat that owns `.solo/tasks.md`/`decisions.md`/`handoff.md`, merges proposals, allocates unique T-IDs, and flags conflicts), `locks` (artifact -> sole writer), **required** `run` (run-id policy: `id_prefix` + `id_required: true`), `profiles`, `rules`, an `exit_gate`/`exit_criteria` with `gate_requires` (evidence artifacts the gate executor must read) and `gate_evidence_map`, an optional **bounded** `loop` (`max_iterations` required), and — mandatory for rooms with worktree seats — the `worktrees` execution contract.

**Graph model (the one documented model).** Nodes are the seats active for the profile under evaluation (a seat with `applies_to` is skipped for other profiles; an UNSTAGED memory steward is out-of-band and excluded). Edges are `handoff_to` targets, contracted through skipped seats. Entry = the active seats of the first active stage; exit = **the single seat whose `commands` contain the `exit_gate`** (exactly one executor is required — there is no last-stage fallback). Every active seat must be reachable from an entry seat AND reach the exit seat, for the profile-free pass and for every declared profile; only the exit seat may have a null `handoff_to`. Handoffs point strictly forward; repetition is declared only via the explicit bounded `loop` block; a null `exit_gate` requires an `exit_gate_note`.

**Worktree execution contract (`worktrees`).** Claude worktree agents branch from the **default branch**, not the parent session HEAD — so any room with `workspace: "worktree:…"` seats must declare: `base_sha` (who records `git rev-parse HEAD` before spawning, and the ff/rebase rule every builder applies first), `builder_payload` (every builder returns worktree_path, branch, **clean** commit_sha, tests, proposal), `proposal_transport` (payloads are committed inside the builder branch; worktrees share the object store, so the integrator reads them via `git show <sha>:.solo/proposals/…`), `integration` (the seat, in a stage after every builder, that merges/cherry-picks the EXACT payload SHAs into ONE integration commit — or checks out the exact fixer commit in `checkout-exact-sha` rooms), and `verify_at_integration_sha` (the review→release-band seats that must prove `git rev-parse HEAD` equals the recorded integration SHA before testing — in a room WITHOUT an evidence lifecycle this list includes the gate executor). Rooms WITH an evidence lifecycle additionally declare `verify_at_final_sha`: the evidence finalizer and the gate executor verify FINAL_SHA there instead, because at their stage HEAD is the freeze commit (a descendant of the integration SHA) and an INTEGRATION_SHA requirement would be unsatisfiable. The bug-fix room's verifier tests the fixer's EXACT commit, never the unchanged main workspace.

**Gate evidence producers are category-specific — and the producer is ALWAYS the evidence finalizer.** With exit gate `/gate:production-ready`, `gate_evidence_map` must cover all 14 categories, the room must carry the `evidence` lifecycle block — a finalizer seat mapped to a REAL shipped agent (`room-evidence-finalizer`; an `agent_note` alone is not executable), a structured `evidence.freeze` contract (the ORCHESTRATOR commits everything after the freeze's `after_stage`, verifies a clean tree, and records FINAL_SHA in untracked `.solo/run-state/<run_id>.json` — the ONLY SHA carrier; tracked files structurally cannot carry their own commit's SHA), and `final_sha_recorded_in` under `.solo/run-state/` — and the finalizer must write every concrete `.solo/gate-evidence/<category>.json` (exact path/fnmatch semantics — a descriptive directory string never satisfies `*.json`). NO other seat writes records mid-flow; stewarded rooms also declare `memory_steward.active_through_stage` strictly before the finalize stage so no runner can invoke the steward at or after finalization. Per profile, skipped specialist seats fail validation unless the gate plugin's applicability matrix permits N/A for that category/profile; the seven mandatory categories always need an active backing seat. The validator also enforces READ PROVENANCE: every concrete `.solo/` read needs an earlier producer, an `assumes_preexisting` entry, or a structured run-state contract.

**Implicit writes are validated.** The validator knows which suite commands write shared memory as a side effect (site-doctor audits write tasks/decisions/handoff; `/dev:implement-feature` writes decisions; gates write risks; …) and computes each seat's *effective* writes as declared + implicit. Two effective writers of one artifact in one stage fail validation; in stewarded rooms, steward-owned files may only be `proposes`-declared by other seats. The steward's duplicate-T-ID contract is checkable with `check_tasks_file()`.

To customize: copy a file, edit seats/stages, keep one-writer-per-artifact-per-stage true, then re-run `python3 "${CLAUDE_PLUGIN_ROOT}/skills/agent-room-templates/scripts/validate_rooms.py"` (stdlib; uses the `jsonschema` library when installed, otherwise a built-in strict evaluator; use `python` if `python3` is missing) — it applies the JSON Schema first, then checks seat/stage placement, entry→exit reachability per profile, the single exit-gate executor, per-stage writers (declared + implicit), steward/proposal discipline, locks, workspaces, the worktrees execution contract, category-specific gate-evidence producers, bounded loops, and that every referenced command exists.

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
