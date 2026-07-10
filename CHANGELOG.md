# Changelog

## 1.0.10 — 2026-07-10

### Hardening batch (H1–H3)
- **H1** AgentRooms: `full-team-website.json` no longer mixes parallel stages with same-stage handoffs — the three flagged pairs (tester/browser_qa, security/auditor, release/docs) are truly parallel now, each seat handing off to a next-stage seat (joins at git_manager and gatekeeper). `site-doctor-audit.json`: `exit_gate` null → `/gate:score-project`. New stdlib validator `agent-room-templates/scripts/validate_rooms.py` — seat/stage placement, forward-only handoffs (loops only via the explicit `loop` block), one writer per artifact per stage, explicit gates/criteria, command existence — wired into `self_check.py` as check 10 of 12.
- **H2** SSRF guard: new shared `plugins/site-doctor/lib/url_guard.py` — https-first schemes; loopback/RFC1918/link-local/CGNAT/benchmarking/multicast/reserved and cloud-metadata addresses (169.254.169.254, 168.63.129.16, metadata.google.internal, NAT64/Teredo/IPv4-mapped v6) refused after resolving every DNS answer; every redirect hop re-validated with a hop cap; hard response-size caps; refused targets print `BLOCKED unsafe target` instead of being fetched. All six network scripts route through it; timeouts, crawl limits, and rate limits retained. DoH endpoint overridable via `SITE_DOCTOR_DOH` (privacy note documented). The loopback test allowlist (`URL_GUARD_EXTRA_ALLOWED`) is honored only together with `URL_GUARD_TEST_MODE=1` and is otherwise ignored with a RuntimeWarning — a stray production environment variable cannot re-admit private addresses.
- **H3** tests + CI: new root `tests/` (stdlib unittest, fully offline — loopback fixture server only) covering self_check (current-platform run, Windows-separator regression, broken-suite detection), url_guard policy (schemes, private/metadata IPs, redirect-to-blocked, redirect loops, oversized responses), BLOCKED behavior and fixture-served happy paths of all six scripts, AgentRooms validation (bundled templates + synthetic violations), and README/marketplace inventory consistency. `.github/workflows/ci.yml` runs it all on ubuntu-latest + windows-latest × Python 3.9/3.12. Fixture server swallows expected client-abort errors; test/validator file I/O uses context managers (clean under `python -X dev`).

### Versions
- ai 1.2.4 → 1.3.0, site-doctor 3.2.2 → 3.3.0, solo 1.5.1 → 1.5.2 (self-check 11 → 12 checks), suite metadata 1.0.9 → 1.0.10; cheatsheet docx v3.2.2 → v3.3.0.

## 1.0.9 — 2026-07-10

### Windows fix
- **W1** `self_check.py`: normalize `glob` results to forward slashes before deriving plugin names. On Windows, `glob` joins with `os.sep`, returning `plugins\solo\commands\x.md`, so `f.split("/")[1]` raised IndexError (check 6, line 102; same defect at check 7, line 110) and the self-check died with a raw traceback before printing any results. One-line fix at the `cmds` glob covers both sites; POSIX behavior unchanged (11 pass / 0 warn / 0 fail post-patch).

### Versions
- solo 1.5.0 → 1.5.1 (Windows self-check fix), suite metadata 1.0.8 → 1.0.9.

## 1.0.8 — 2026-07-09

### Polish batch (N1–N9)
- **N1** repo trio (`/repo:map`, `dependency-map`, `onboarding`): each now states its expected output, so the commands stand alone without the skill open.
- **N2** `site-doctor-cheatsheet.docx`: version string v3.0.0 → v3.2.2 (content verified current — its command list matches disk both ways).
- **N3** `LICENSE` added (MIT, © 2026 Sakura Yukihira).
- **N4** `self_check.py` hardened: dead `ok = lambda` removed; unbolded "use the X skill" references checked; marketplace metadata + per-plugin descriptions' command references verified; new version-agreement checks (CHANGELOG top entry == metadata.version; cheatsheet docx == site-doctor version). 8 → 11 checks. Docs updated in `/solo:self-check` and suite-integrity.
- **N5** browser-qa-engineer: evidence-per-finding standard (screenshot / console-network paste / exact repro; manual scripts say what to capture).
- **N6** `/solo:full-team-dev`: every flow line now sits under an explicit `# n/15 — phase` label; the prose chain updated to the same 15 phases in actual flow order (Backend/Frontend merged into Build — they were one command; Review, Merge & release, Launch & handoff named). README's chain synced too (it claimed 15 phases but listed 14).
- **N7** flow additions: `/browser:form-submit-test` + `/browser:visual-check` (Browser QA), `/security:authz-matrix` (Security), `/security:secrets-fix` immediately before the merge path. Flow is now 47 steps. Room seats deliberately unchanged.
- **N8** project-memory-manager: the contract is explicitly "16 standard files plus optional `config.md` (not counted)".
- **N9** README: "same 7-part contract" → "one of three fixed contracts (7-part work, evidence-based audit, gate verdict)".

### Versions
- solo 1.4.5 → 1.5.0 (flow restructure + checker features), site-doctor 3.2.1 → 3.2.2, repo 1.0.1 → 1.0.2, browser 1.0.1 → 1.0.2, suite metadata 1.0.7 → 1.0.8.

## 1.0.7 — 2026-07-09

### Added (H6 — DevOps authors CI instead of only reviewing it)
- `/release:ci-setup` + a `ci-setup` mode in devops-engineer: proposes one minimal GitHub Actions workflow (PR + default branch: install → lint → typecheck → tests, fail fast) reusing the project's own scripts, env-var names from `.solo/env-contract.md`, secrets by reference only. Propose-don't-push; suggests the branch-protection rule that makes `/gate:before-merge`'s types/lint/tests blockers CI-enforced. No deploy step — deploys stay with `/release:deploy-plan`.
- Deliberately not inserted into `/solo:full-team-dev`: CI setup is a one-time project task, not a per-cycle step.
- Command count 99 → 100 (README + marketplace counts and release rows updated).

### Fixed (H7 — connector-auditor claims only what it does)
- connector-auditor: explicit scope principle — exactly Vercel/Supabase/GitHub/Cloudflare; payments and tag platforms belong to their own audits.
- payments-audit + tag-audit Connector-mode intros no longer say "via connector-auditor"; they name the provider's own API/MCP (Stripe/PayPal/Xendit/Midtrans; GTM/GA4) and state connector-auditor's actual scope.

### Versions
- release 1.0.1 → 1.1.0, stack 1.4.0 → 1.4.1, suite metadata 1.0.6 → 1.0.7.

## 1.0.6 — 2026-07-09

### Fixed (H5 — secret scanner covers the providers the suite itself names)
- `scan_secrets.py`: new patterns for Xendit (`xnd_development_`/`xnd_production_`), Midtrans server keys (`(SB-)Mid-server-`), SendGrid (`SG.x.y`), Resend (`re_`, word-boundary guarded), Supabase access + secret tokens (`sbp_`, `sb_secret_`), and Vercel/Cloudflare token assignments. Inserted in the specific-before-generic block after Stripe. This makes payments-audit's existing claim ("scan_secrets.py catches payment keys") true — previously only Stripe matched.

### Fixed (H8 — room doc matches the patched room JSONs)
- `agent-room-templates/SKILL.md` Launch Room: Release agent now listed with `/site-doctor:monitoring` + `/gate:before-deploy` (writing `release.md` + `monitoring.md`); Docs agent gains `/git:release-notes`; Gatekeeper is `/gate:production-ready` + `/solo:handoff-memory` (before-deploy moved out — it lives in the release seat, as in the JSON since 1.0.1).
- production-release one-liner: "preflight + plans + monitoring → deploy gate → docs → launch gate".

### Versions
- site-doctor 3.2.0 → 3.2.1, ai 1.2.3 → 1.2.4, suite metadata 1.0.5 → 1.0.6.

## 1.0.5 — 2026-07-09

### Fixed (H1 — money path wired into the master flow and room)
- `/solo:full-team-dev`: `/stack:audit-payments` inserted after `/stack:audit-tags` (the flow's existing skip-if-not-in-stack rule applies). Parity with `site-doctor-audit.json`, which always included it.
- `full-team-website.json`: `/stack:audit-payments` added to the auditor seat's commands.

### Fixed (H2 — implement → review is actually sequential)
- `full-team-website.json`: the implementer/reviewer stage is split into two successive stages — the reviewer now runs after the implementer, matching the skill's documented "implement → review → fix" sequence, and reviews the changed-files diff it was given read access to in 1.0.2.
- `agent-room-templates/SKILL.md`: Build-room notation changed from Implementer ∥ Reviewer to Implementer → Reviewer; room line updated to 13 seats across 10 stages. (Tester ∥ Browser-QA and Security ∥ Auditor remain deliberately parallel.)

### Versions
- solo 1.4.4 → 1.4.5, ai 1.2.2 → 1.2.3, suite metadata 1.0.4 → 1.0.5.

## 1.0.4 — 2026-07-09

### Added (C5 — spec and shipped suite agree)
- `/stack:connector-check` — pre-audit connector test: per-vendor tier (live / local config / manual) with evidence, written to `.solo/stack.md` under `## Connectors`; recommends which audits can run in Connector mode. Backed by connector-auditor.
- `/gate:score-project` — the 12-section checklist + 12-category scoring with no launch verdict; the trend metric between gate runs. Backed by production-readiness-reviewer.
- Command count 97 → 99 (README + marketplace counts and plugin rows updated).

### Removed from spec (C5)
- `/gate:strict-mode` — formally cut: a one-shot slash command cannot hold a persistent suite-wide toggle, and strictness already lives in each gate's blocker list (one fail = NO-GO).

### Fixed (C6 — security plugin truly standalone)
- `/security:threat-model`, `/security:abuse-cases`, `/security:secrets-fix` now carry the inline-fallback wording ("lighter inline version if site-doctor isn't installed, and say so"), matching the degradation promise the README makes.

### Fixed (C7 — no cwd-dependent script paths)
- `/solo:self-check` and suite-integrity SKILL.md invoke the checker via `"${CLAUDE_PLUGIN_ROOT}"` instead of a cwd-relative path.
- tag-audit no longer reaches into site-doctor via `../../../`; it delegates to `/site-doctor:compliance` (which owns `scan_trackers.py`) with a manual fallback.

### Versions
- stack 1.3.0 → 1.4.0, gate 1.2.0 → 1.3.0, security 1.0.1 → 1.0.2, solo 1.4.3 → 1.4.4, suite metadata 1.0.3 → 1.0.4.

## 1.0.3 — 2026-07-09

### Changed (H4 — gates verify evidence, not confession)
- `/gate:before-code` + quality-gatekeeper: new blocker — no UX flow/design doc (`.solo/design.md`) for user-facing work; `/design:ux-flow` added to the fix routes.
- `/gate:before-merge` + quality-gatekeeper: new blockers — code review not recorded (`/dev:code-review` / `/git:pr-review` verdict) and acceptance criteria not demonstrated passing (`.solo/tests.md`); security line now requires a security *pass* on the change, not just the absence of a confessed issue.
- `/gate:before-deploy` + quality-gatekeeper: stack-audit blocker now names tags/payments audits where `.solo/stack.md` says they're in play.

### Changed (H3 — one verdict vocabulary, full checklist coverage)
- production-readiness-reviewer: checklist grown 9 → 12 sections — new Performance (`/site-doctor:perf`), SEO (`/site-doctor:seo`), Analytics (`/stack:audit-tags`, `/site-doctor:audit-analytics`) sections, so all 12 scored categories have an evidence source.
- Verdict vocabulary unified to BLOCKED / SAFE TO LAUNCH / LAUNCH WITH WARNINGS: skill frontmatter + body (was RED/YELLOW/GREEN + NOT READY), README, `/gate:production-ready` command text, and the `/solo:full-team-dev` gate annotation.

### Versions
- gate 1.1.0 → 1.2.0, solo 1.4.2 → 1.4.3, suite metadata 1.0.2 → 1.0.3.

## 1.0.2 — 2026-07-09

### Fixed (C4 — Git/PR path wired into the master flow and room)
- `/solo:full-team-dev`: `/git:create-branch` inserted after `/gate:before-code`; `/git:commit-plan` + `/git:pr-review` inserted before `/gate:before-merge`. The merge gate now gates an actual branch/PR.
- `full-team-website.json`: new `git_manager` seat (role: Git/PR Manager, own stage between security/auditor and release/docs) owns `/git:commit-plan`, `/git:pr-review`, `/gate:before-merge`; the gate is removed from the `release` seat, which now matches `production-release.json`. Auditor hands off to `git_manager`. `reviewer` and `git_manager` read the changed-files diff.
- `agent-room-templates/SKILL.md`: full-team-website line updated to 13 seats across 9 stages.

### Versions
- solo 1.4.1 → 1.4.2, ai 1.2.1 → 1.2.2, suite metadata 1.0.0 → 1.0.2.

## 1.0.1 — 2026-07 (applied in a prior session)

### Fixed (C1–C3 — release-tail ordering and monitoring wiring)
- Release tail reordered to `preflight → deploy-plan → rollback-plan → /site-doctor:monitoring → /gate:before-deploy` in `/solo:full-team-dev`, `production-release.json`, and the `full-team-website.json` release seat.
- `.solo/monitoring.md` now written by the release seat and read by the gatekeeper — the gate no longer demands an artifact nothing produced.
- solo 1.4.0 → 1.4.1, ai 1.2.0 → 1.2.1. (Suite metadata version was not bumped in that patch; corrected as of 1.0.2.)

## 1.0.0

- Initial release: 17 plugins, 56 skills, 97 slash commands, 9 stdlib helper scripts.
