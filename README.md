# solo-suite

**The complete solo developer system — a full product team *and* a production toolkit, unified by shared project memory.**

This is [solo-team](#the-team-plugins) (nine roles that plan, design, build, test, release, and document), [site-doctor](#the-toolkit-plugin) (26 skills that audit, debug, and fix real websites and databases), and a [stack-aware layer](#the-stack-plugin) (ask what tools you use, then audit them by vendor) in **one marketplace**. They were built for each other: everything runs through the same `.solo/` project memory, so your stack is known before anything runs, an audit finding becomes a task, a task becomes tested code, and tested code becomes a safe release — across sessions, without you re-loading context each time. On top sits a **workflow layer** — git, spec, repo intelligence, deeper security, real-browser QA, quality gates, an AI-coding co-pilot, and growth — so the same memory also drives your branches, contracts, reviews, and go/no-go gates.

- **18 plugins** · **56 skills** · **102 slash commands** · **13 stdlib helper scripts** · **24 room-* agents**
  (17 component plugins + the `full-team` meta-plugin that depends on all of them)
- Offline regression tests (`tests/`, stdlib unittest, loopback fixtures only) + hardened Linux/Windows CI (`.github/workflows/ci.yml`: least-privilege permissions, pinned actions, an integrity-locked Claude CLI whose official validation is mandatory, packaged-install and marketplace smoke tests, and separate read-only build, OIDC-only signing, and write-only publishing jobs for version tags). Signed release assets are checksum-verified at each job boundary and downloaded back from the draft GitHub Release for exact byte/signature verification before promotion. Site-doctor's network scripts are SSRF-guarded by `plugins/site-doctor/lib/url_guard.py`; the secret scanner emits only redacted, fingerprinted findings. AgentRooms templates are schema-validated (`agentroom-v1`) with a memory-steward model for parallel agents, a shared untrusted-content contract, supported tool allowlists, and source-labelled task envelopes; they ship with 24 `room-*` agent definitions. The JSON rooms are validated work orders, not an executable runtime.
- One install source, one shared memory, every command name preserved
- Covers the whole loop: **intake → spec → plan → map → design → build → review → test → browser-QA → audit → gate → release → operate → document → sync**

---

## The team plugins

| Plugin | Skills | Commands |
|---|---|---|
| **solo** (start here) | project-memory-manager, memory-sync, suite-integrity | `/solo:start-session` `/solo:end-session` `/solo:run-cycle` `/solo:full-team-dev` `/solo:handoff-memory` `/solo:next-step` `/solo:project-status` `/solo:self-check` `/solo:sync-obsidian` `/solo:sync-grafana` |
| **project** | product-manager, software-architect | `/project:prd` `/project:architecture` `/project:task-breakdown` |
| **design** | ui-ux-designer | `/design:ui-review` `/design:ux-flow` `/design:component-system` |
| **dev** | fullstack-developer, code-reviewer | `/dev:implement-feature` `/dev:fix-bug` `/dev:refactor-code` `/dev:code-review` |
| **test** | qa-engineer | `/test:unit` `/test:integration` `/test:e2e` `/test:edge-cases` |
| **release** | devops-engineer, security-reviewer | `/release:preflight` `/release:deploy-plan` `/release:rollback-plan` `/release:ci-setup` |
| **docs** | documentation-writer | `/docs:update` `/docs:api` `/docs:setup-guide` `/docs:runbook` |

## The toolkit plugin

**site-doctor** — 26 skills, 24 commands, 8 scripts:

- **Core:** `/site-doctor:audit-site` `/site-doctor:audit-db` `/site-doctor:debug` `/site-doctor:full-checkup`
- **Specialist:** `/site-doctor:security-scan` `/site-doctor:seo` `/site-doctor:perf` `/site-doctor:a11y` `/site-doctor:audit-api` `/site-doctor:monitoring`
- **Infra & ops:** `/site-doctor:audit-infra` `/site-doctor:review-deploy` `/site-doctor:cost` `/site-doctor:backups` `/site-doctor:load-test` `/site-doctor:incident`
- **Data/compliance/content:** `/site-doctor:compliance` `/site-doctor:migrate-data` `/site-doctor:audit-deps` `/site-doctor:audit-content` `/site-doctor:audit-analytics`
- **Frontend & growth:** `/site-doctor:audit-mobile` `/site-doctor:audit-forms` `/site-doctor:email-check`

(Full command reference and ready-to-paste prompts are in `site-doctor-cheatsheet.docx`.)

## The stack plugin

**stack** — ask what you run on, then audit it by vendor (7 commands, 7 skills):

- **`/stack:intake`** — interviews you across hosting, DNS/CDN/WAF, database, auth, storage, analytics/tags, email, payments, and repo/CI, and writes it to **`.solo/stack.md`**. Run it first; every other command reads it so advice fits your real tools.
- **`/stack:connector-check`** — pre-audit connector test: per vendor (Vercel, Supabase, GitHub, Cloudflare) the tier reached — live / local config / manual — with evidence, written to `.solo/stack.md` under `## Connectors`.
- **`/stack:audit-cloudflare`** — DNS, SSL/TLS mode, cache/redirect/WAF rules, bot protection, origin exposure, proxy status.
- **`/stack:audit-vercel`** — build, env vars, preview↔prod, domains, redirects, middleware, function limits, rollback, images, insights.
- **`/stack:audit-supabase`** — RLS policies, table exposure, auth, API keys, storage policies, edge functions, indexes, slow queries, backups, realtime.
- **`/stack:audit-tags`** — GTM install, GA4 firing once, conversions, consent mode, Meta/TikTok pixels, PII leakage, form & funnel tracking.
- **`/stack:audit-payments`** — webhook security, payment status handling, duplicate-payment protection, refund flow, test vs live keys, exposed secret keys, checkout success/failure pages (Stripe, PayPal, Xendit, Midtrans, …).

The four vendor audits are thin specialists: they own the vendor-specific checklist and delegate the deep mechanics to site-doctor's generic engines (`infrastructure-audit`, `deployment-review`, `security-review`, `database-audit`, `backup-recovery`, `analytics-audit`, `compliance-check`). If you have the **Cloudflare, Vercel, Supabase, or GitHub connectors**, the new **connector-auditor** skill pulls live configuration through them (read-only) so audits reflect reality instead of assumptions; without a connector it falls back to your local config files and says so.

Skills fire **automatically** on matching requests; the slash commands are explicit shortcuts.

## Run the whole team — and keep it honest

- **`/solo:full-team-dev`** — the master command: the complete cycle from idea to production readiness in 16 phases (Intake → PRD → Architecture → Contracts → UX/UI → Tasks → Build → Review → Tests → Browser QA → Security → Stack audit → Growth → Merge & release → Docs → Launch & handoff), staffing all 17 team roles, hard-stopping at every gate, and profile-aware: phases that don't apply to the project profile are skipped with an evidence-backed N/A reason. Resume-aware via `.solo/`. It exercises **all 17 component plugins directly** (the `ai` plugin via `/ai:review-output` between major phases — and it additionally drives the whole flow when run as a multi-agent room).
- **`/solo:self-check`** — verifies the suite itself: manifests valid, every command has title/purpose/inputs/output, every skill has a SKILL.md, README & marketplace counts match reality, no duplicate names, no broken cross-references, and which `.solo/` memory files are missing. Backed by a stdlib script (`suite-integrity`).
- **Strict gates** — `/gate:before-code`, `/gate:before-merge`, `/gate:before-deploy` each have an explicit blocker list; **one failed check = NO-GO**, never averaged away.
- **Scoring** — `/gate:production-ready` scores **14 categories** (Product, Architecture, Design, Frontend, Backend, Database, Security, Testing, Performance, SEO, Analytics, Deployment, Monitoring, Documentation) each 0–10. Categories with an accepted N/A record under the applicability matrix leave the denominator (the seven mandatory categories never do): `applicable_max = applicable_category_count * 10` and `normalized_score = round(total / applicable_max * 100)`. It reports that normalized score, and returns **Launch Status: BLOCKED / SAFE WITH WARNINGS / SAFE TO LAUNCH**, with hard blockers forcing BLOCKED regardless of score. Every category verdict is backed by machine-readable, self-attested local gate evidence (`gate-evidence-v1`, created at FINAL_SHA through the manual-only `/gate:finalize-evidence` workflow) that the gate **rejects when stale** — wrong HEAD, wrong committed-tree digest, wrong environment, or expired. Each command is previewed first, requires an exact confirmation token and explicit network approval when applicable, captures bounded output in a scrubbed child environment, and runs in a killable POSIX process group or Windows Job Object; surviving descendants/readers refuse evidence. Authenticated `gh run view` uses only an explicit external `--gh-config-dir` reference, never ambient token variables or the normal user HOME. Still use an OS/container sandbox for untrusted projects. The unsigned local record cannot cryptographically prove which process authored it or that a human approved it; its `recorder` field is a copyable format label. `/gate:score-project` runs the same checklist and scoring without the launch verdict — the trend metric between gate runs.
- **Evidence-based audits** — every audit command outputs Status → Evidence Checked → Findings → Risk Level → Required Fixes → Verification Steps → Next Recommended Command. No evidence, no finding.
- **Two-mode stack audits** — Connector mode (live config via connector-auditor, read-only, never prints secrets) or Manual mode (asks for screenshots, config files, env-var *names*); each audit states which mode it used.
- **Agent rooms** — `/ai:agent-rooms` sets up multi-agent workflows from five templates (Planning, Build, QA, Hardening, Launch) and ships four ready-made JSON room files (`agentsrooms/`: full-team-website, site-doctor-audit, production-release, bug-fix-loop): one writer per artifact, explicit `.solo/` context per seat, handoffs checked, exit gate enforced.

---

## The workflow plugins

Eight focused plugins that turn the same `.solo/` memory into day-to-day engineering discipline:

| Plugin | Skills | Commands |
|---|---|---|
| **git** | git-workflow-manager | `/git:create-branch` `/git:commit-plan` `/git:pr-review` `/git:release-notes` `/git:sync-issues` |
| **spec** | acceptance-criteria-writer, api-contract-designer | `/spec:feature-brief` `/spec:acceptance` `/spec:api-contract` `/spec:data-contract` `/spec:env-contract` |
| **repo** | repo-analyzer | `/repo:map` `/repo:risk-map` `/repo:dependency-map` `/repo:find-dead-code` `/repo:onboarding` |
| **security** | authz-security-reviewer | `/security:threat-model` `/security:authz-matrix` `/security:secrets-fix` `/security:rls-test` `/security:abuse-cases` |
| **browser** | browser-qa-engineer | `/browser:smoke-test` `/browser:console-errors` `/browser:visual-check` `/browser:mobile-test` `/browser:form-submit-test` |
| **gate** | quality-gatekeeper, production-readiness-reviewer | `/gate:before-code` `/gate:before-merge` `/gate:before-deploy` `/gate:production-ready` `/gate:score-project` |
| **ai** | ai-output-auditor, agent-room-templates | `/ai:prompt-improve` `/ai:handoff-check` `/ai:review-output` `/ai:compare-models` `/ai:repair-cycle` `/ai:agent-rooms` |
| **growth** | conversion-optimizer | `/growth:conversion-audit` |

**Every command ends with a fixed, self-describing output contract.** Most use one of three shared formats — the 7-part work contract (Summary · Findings/Work done · Risks · Required fixes · Suggested tasks (→ `.solo/tasks.md`, stable T-IDs) · Verification · Next command), the evidence-based audit format, or the gate verdict — and a few use richer task-specific formats built on the same principles (e.g. `/dev:implement-feature`'s files-changed contract and `/site-doctor:full-checkup`'s scored health report). Either way, each step tells you exactly what to run next and every finding becomes a tracked task.

`/gate:production-ready` runs a full 14-section launch checklist (Product, Architecture, Design, Frontend, Backend, Database, Security, Testing, Performance, SEO, Analytics, Deployment, Monitoring, Documentation) and returns BLOCKED / SAFE WITH WARNINGS / SAFE TO LAUNCH — where any critical failure (secrets committed, no auth where needed, RLS off where needed, no backup/rollback) forces **BLOCKED** regardless of the average, and stale gate evidence (wrong commit/environment, expired) is rejected.

### Where to start (priority order)

**Priority 1 — the backbone:** `/repo:map` · `/spec:acceptance` · `/git:pr-review` · `/gate:before-merge` · `/gate:production-ready`

**Priority 2 — real quality:** `/browser:smoke-test` · `/browser:visual-check` · `/security:authz-matrix` · `/security:rls-test` · `/ai:review-output`

**Priority 3 — power-ups:** `/git:sync-issues` · `/growth:conversion-audit` · `/repo:risk-map` · `/ai:repair-cycle` · `/docs:runbook`

---

## Install

From a local clone, in Claude Code:

```
/plugin marketplace add /path/to/solo-suite
/plugin install solo@solo-suite
/plugin install project@solo-suite
/plugin install design@solo-suite
/plugin install dev@solo-suite
/plugin install test@solo-suite
/plugin install release@solo-suite
/plugin install docs@solo-suite
/plugin install site-doctor@solo-suite
/plugin install stack@solo-suite
/plugin install git@solo-suite
/plugin install spec@solo-suite
/plugin install repo@solo-suite
/plugin install security@solo-suite
/plugin install browser@solo-suite
/plugin install gate@solo-suite
/plugin install ai@solo-suite
/plugin install growth@solo-suite
/reload-plugins
```

Or from GitHub:

```
/plugin marketplace add unn0wn002/solo-suite
/plugin install solo@solo-suite
```

Want everything in one step? Install the **`full-team`** meta-plugin — it depends on all 17 component plugins:

```
/plugin install full-team@solo-suite
```

### Verify a published release

A locally built bundle is an unsigned **release candidate**. Canonical release
artifacts come from the tagged CI run and are attached to the matching GitHub
Release. Download the complete asset set, including every matching
`.sigstore.json` bundle. Verify the signed payload manifest before trusting its
checksums, then verify every listed payload's own signature:

```bash
TAG=v1.0.24
CANONICAL_REPO="$(gh api repos/unn0wn002/solo-suite --jq .full_name)"
CERT_ID="https://github.com/${CANONICAL_REPO}/.github/workflows/ci.yml@refs/tags/${TAG}"
ISSUER="https://token.actions.githubusercontent.com"
printf 'Expected certificate identity: %s\n' "$CERT_ID"
cosign verify-blob RELEASE-SHA256SUMS \
  --bundle RELEASE-SHA256SUMS.sigstore.json \
  --certificate-identity "$CERT_ID" \
  --certificate-oidc-issuer "$ISSUER"
sha256sum -c RELEASE-SHA256SUMS
while read -r _digest payload; do
  test -n "$payload" || continue
  cosign verify-blob "$payload" \
    --bundle "$payload.sigstore.json" \
    --certificate-identity "$CERT_ID" \
    --certificate-oidc-issuer "$ISSUER"
done < RELEASE-SHA256SUMS
```

`gh api ... .full_name` supplies GitHub's canonical owner/repository casing;
the expected identity is derived from that trusted repository metadata, never
from the untrusted bundle being checked. `cosign` requires an exact identity
match. A missing release asset, bundle, manifest entry, or failed checksum or
signature leaves the release **UNVERIFIED**. Temporary GitHub Actions artifacts
are not the canonical distribution channel.

**Install `solo` first** (or `full-team`) — it owns the shared memory the others build on. Install only the plugins you want; each degrades gracefully if a sibling is missing.

**Prefer no plugin?** Most skill folders (`plugins/<name>/skills/<skill>/`) can be copied into `~/.claude/skills/` (global) or `.claude/skills/` (per project) — **with one documented exception**: the **five** site-doctor skills whose helper scripts make network requests (`website-audit`, `compliance-check`, `email-deliverability`, `mobile-audit`, `seo-optimization`) share the SSRF guard `plugins/site-doctor/lib/url_guard.py` and are **not standalone**. (`dependency-audit` and `security-review` also bundle scripts, but those are offline filesystem tools with no url_guard dependency — they copy cleanly.) If you copy one of the five, copy `lib/url_guard.py` alongside it (the scripts resolve it three directories up: `<skill>/../../../lib/url_guard.py`) or install the site-doctor plugin instead. Helper commands use `${CLAUDE_PLUGIN_ROOT}` so they run from any working directory once installed; if `python3` is missing, use `python`.

---

## Shared project memory — the `.solo/` contract

What makes seventeen plugins behave as one system: all state lives in plain, git-committed markdown at your project root.

| File | Written by | Contents |
|---|---|---|
| `.solo/project.md` | project-memory-manager | Project identity one-pager |
| `.solo/stack.md` | stack-advisor (`/stack:intake`) | Hosting, DNS/CDN/WAF, DB, auth, storage, tags, email, payments, CI |
| `.solo/prd.md` | product-manager | Problem, users, stories, scope, non-goals, metrics |
| `.solo/architecture.md` | software-architect | Components, data-flow (reads `prd.md`) |
| `.solo/api-contract.md` | api-contract-designer (`/spec:api-contract`) | Endpoint contract (reads `architecture.md`) |
| `.solo/data-contract.md` | software-architect (`/spec:data-contract`) | Entities, constraints, relationships |
| `.solo/env-contract.md` | software-architect (`/spec:env-contract`) | Env vars & secrets by environment — names only |
| `.solo/design.md` | ui-ux-designer | Flows, component system, tokens |
| `.solo/tasks.md` | everyone (incl. site-doctor) | Single source of truth for work status (stable T-IDs) |
| `.solo/decisions.md` | everyone (append-only) | Dated decision log with reasoning |
| `.solo/risks.md` | gates, security & audits | Open risks with severity and owner |
| `.solo/bugs.md` | `/dev:fix-bug`, browser & site-doctor | Known bugs: repro, severity, status |
| `.solo/tests.md` | qa-engineer (`/test:*`) | What's tested, results, coverage gaps |
| `.solo/release.md` | devops-engineer (`/release:preflight`) | Preflight results, deploy & rollback plans |
| `.solo/monitoring.md` | observability | Error tracking, uptime, logs, alerts |
| `.solo/handoff.md` | project-memory-manager | Latest session state, rewritten each handoff |

Every skill **reads before working** and **updates after**. `project-memory-manager` also adds one line to your repo's `CLAUDE.md`, so every future session is memory-aware even without slash commands.

### Session workflow

Three commands bookend and drive your work, and every skill in the suite is wired to them:

- **`/solo:start-session`** — run it when you sit down. Reads all of `.solo/` and re-orients you in under a minute: where things stand, what's in flight, what's blocked, and the exact next task to do.
- **`/solo:end-session`** — run it when you stop. Saves progress, records blockers, logs decisions, and rewrites the handoff ending with the next task — so the next start-session resumes instantly.
- **`/solo:run-cycle`** — runs one complete development cycle for a single task, orchestrating the core plugins in order: select → design (design) → implement (dev) → review (dev) → test (test) → audit (site-doctor) → document (docs) → save. It stops at any gate needing a human decision.

(`/solo:handoff-memory` is still there for mid-work checkpoints; `/solo:next-step` and `/solo:project-status` for a quick pointer or status roll-up.)

### Sync out to your other tools

Your `.solo/` memory can mirror outward — `.solo/` stays the source of truth, the destinations are one-way mirrors, and both syncs are idempotent (update in place, never duplicate, never delete your own content):

- **`/solo:sync-obsidian`** — writes the memory into an Obsidian vault as clean, linked notes: an Overview/MOC plus Stack, PRD, Architecture, Design, Tasks (native checkboxes), Decisions, and Handoff. Your project memory becomes part of your second brain, searchable and linkable. Managed content sits between markers so anything you hand-write in a note survives.
- **`/solo:sync-grafana`** — pushes project *health* to a Grafana dashboard: task counts (open/done/blocked), tasks-done-over-time, open audit findings by severity (from the audit fixes site-doctor and the `/stack:audit-*` skills write back into `tasks.md`), and a blockers table — plus annotations for releases, audits, and key decisions. Uses a Grafana connector/API if you have one; otherwise emits importable dashboard JSON. *(This reads "Grapify" as Grafana — if you meant a different tool, the same read→transform→write structure ports to it.)*

Sync targets (vault path, Grafana URL) are remembered in `.solo/config.md` so you configure them once. Run a sync right after `/solo:end-session` or on a release to snapshot state into your notes and dashboard.

---

## How the parts work together

The integration runs **both directions**, and the stack layer feeds them all:

- **`/release:preflight` orchestrates site-doctor** — it drives `security-review`, `dependency-audit`, `infrastructure-audit`, `backup-recovery`, and `observability` as part of the ship gate.
- **`/dev:fix-bug` routes hard bugs** to site-doctor's `website-debug` / `database-debug`; `/dev:code-review` and `security-reviewer` defer OWASP depth to `security-review` (which ships a secret scanner).
- **`ui-ux-designer` routes** deep accessibility/mobile/forms checks to `accessibility-review` / `mobile-audit` / `forms-audit`.
- **site-doctor writes back into memory** — every audit reads `.solo/` for context and turns its prioritized fix list into tasks in `tasks.md`, with findings logged to `decisions.md`. So `/site-doctor:security-scan` doesn't just report — its findings show up in `/solo:next-step` and the next `/release:preflight`.
- **Stack-aware everything** — `/stack:intake` records your tools to `.solo/stack.md`, and every audit/build skill reads it first, so recommendations fit your real stack. The vendor audits (`/stack:audit-*`) then delegate depth to site-doctor's generic engines, and their findings land in `tasks.md` like any other.
- **Shared conventions** — the architect's data-model defaults (TEXT+CHECK over ENUMs, app-generated UUIDs) match how site-doctor's `database-audit` (and `/stack:audit-supabase`) review a schema, so they never contradict each other.

Each skill still works standalone if its counterparts aren't installed — it does a lighter inline version and notes it.

---

## A full solo loop

```
/stack:intake           → record your tools                   (writes stack.md)
/project:prd            → spec it, scoped to an MVP            (writes prd.md)
/project:architecture   → design the build                    (writes architecture.md)
/design:ux-flow
