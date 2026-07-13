# Changelog

## 1.0.21 — 2026-07-13

Emergency repair for the canonical release workflow. The reviewed `v1.0.20`
tag was created from the intended 268-file tree, but GitHub rejected
`.github/workflows/ci.yml` before scheduling any job because two job-level
environment expressions referenced `runner.temp`, where the `runner` context
is unavailable. No GitHub Release or canonical signed assets were published
for v1.0.20; that public tag remains immutable.

The bytecode cache now uses the job-level-safe `github.workspace` context while
remaining outside the checked-out source tree. Publication-policy regressions
reject `runner` references in job headers, and command substitutions are split
from `export` so failures from `mktemp`, Node, or Claude CLI version discovery
cannot be masked. The repaired workflow passes actionlint 1.7.12 locally; the
tagged workflow remains the authority for canonical build, test, signing, and
publication evidence.

Release-delta reporting now handles the suite's intentionally unmerged release
branches by selecting the highest lower strict-semver tag numerically across
all tags, then requiring that tag to be annotated. The component-version drift
snapshot is refreshed from the verified v1.0.20 tree and a regression binds
that baseline to the marketplace transition recorded here.

### Versions

- all 18 component plugins: unchanged (no plugin tree changed from v1.0.20)
- marketplace 1.0.20 -> 1.0.21

## 1.0.20 — 2026-07-13

Security and release-integrity hardening after the standalone v1.0.19 audit.
The release builder now packages only regular blobs from one resolved Git
commit, never mutable working-tree bytes, and records the exact tree/blob
identity in provenance. It disables Git replacement objects and inherited Git
repository/config overrides, validates the release version before constructing
paths, and rejects symlinks, gitlinks, special files, and archive paths that
exceed bounded extraction limits. The SBOM now derives license data from a
complete, reviewed dependency metadata file, binds both Python and npm lock
files by digest, and inventories the locked Claude CLI/Node toolchain.

Tag CI is split across least-privilege build, OIDC signing, and publication
jobs. The Claude CLI is installed from a repository-owned lock file with
lifecycle scripts disabled; checkout credentials are not persisted; signed
artifacts cross explicit digest-checked boundaries; and publication verifies
the bytes returned by the remote release before declaring success. GitHub
environment protection and approval policy remain repository settings and
therefore cannot be proved from this source tree alone.

AgentRooms now share `UNTRUSTED_CONTENT_CONTRACT_V1`, receive source-labelled
task envelopes, and declare supported tool allowlists. Dynamic RLS checks and
side-effecting browser/form operations are manual-only; automated full-team
runs use static, local checks. Gate command execution is bounded to approved
local commands and endpoints, contains descendants in a POSIX process group or
Windows Job Object, and refuses evidence unless capture readers reach EOF.
Authenticated `gh run view` requires an explicit external GitHub CLI config
reference instead of ambient tokens. Run-state/evidence writes are constrained
to their canonical project directories, and secret/history scanning streams
Git output through hard caps and emits redacted findings rather than matching
source lines.

Additional defensive fixes enforce the link crawler's remaining URL, request,
byte, time, and output budgets per operation and mark truncated responses
`UNVERIFIED`; disable ambient HTTP proxies for guarded requests; require
explicit database credential references instead of pasted DSNs; require Gate
dependency evidence to name a committed recognized requirements target;
constrain PowerShell publication remotes and ZIP expansion; and reject
generated inventory races and non-regular files.
This release was validated only against local fixtures and disposable
repositories—no live website, database, cloud account, or production target was
scanned.

### Versions

Component versions move with their trees (drift-guarded by
`tests/test_release_versioning.py`):

- ai 2.5.2 -> 2.5.3 (AgentRooms trust contract and tool boundaries)
- gate 2.5.1 -> 2.5.2 (bounded execution, paths, evidence, and redaction)
- security 1.1.1 -> 1.1.2 (manual-only live RLS and safe secret history guidance)
- site-doctor 3.6.1 -> 3.6.2 (bounded scanners/crawler, URL and input hardening)
- solo 1.9.2 -> 1.9.3 (safe full-team orchestration and task-envelope contract)
- stack 1.4.2 -> 1.4.3 (sensitive analytics-export handling)
- every other plugin: unchanged and unbumped
- marketplace 1.0.19 -> 1.0.20

## 1.0.19 — 2026-07-13

Strict-audit repair of v1.0.18. Windows now exercises the real default
encoding path instead of relying on `PYTHONUTF8=1`: `record_evidence.py`
normalizes captured child output to UTF-8 before joining its header,
`validate_rooms.py --help` is CP1252-safe, and the scanner excludes only the
two exact generated runtime trees (`.solo/gate-evidence/` and
`.solo/run-state/`) while retaining coverage of lookalike directories.
Fixture-only encoding/scanner regressions cover these paths; no standalone
security scan or live probing was performed in this repair.

The evidence contract now describes what it can actually prove.
`record_evidence.py` remains the canonical writer for the supported workflow,
and the checker still validates schema, command policy, checkout binding,
digests, freshness, and matrix rules, but the unsigned `recorder` value is a
copyable format label—not cryptographic proof of process origin. Gate commands,
the Gate skill/schema/checker, the AgentRooms finalizer, README, and regression
tests use the same self-attested trust language.

Release engineering is fail-closed: reviewed-package PowerShell helpers use
fresh GUID workspaces, checked Git exit codes, an expected remote HEAD, exact
ZIP/checksum/provenance/tree verification, an explicit review branch, and exact
approved-commit tag binding. Tag CI rebuilds the canonical bundle, validates it
under the ordinary Windows encoding as well as UTF-8 environments, signs and
verifies the complete release manifest and canonical artifacts with Sigstore,
and publishes durable GitHub Release assets. Local builds are labelled unsigned
release candidates. The builder now derives metadata time from the source
epoch, emits LF-stable text metadata, and reports actual build tools in its SBOM
instead of claiming unrecorded validation tools. Superseded root patch notes no
longer ship. The site-doctor cheatsheet now matches site-doctor 3.6.1,
solo-suite 1.0.19, and the current `unn0wn002/solo-suite` install slug.

### Versions

Component versions move with their trees (drift-guarded by
`tests/test_release_versioning.py`):

- ai 2.5.1 -> 2.5.2 (AgentRooms Windows help and finalizer trust contract)
- gate 2.5.0 -> 2.5.1 (UTF-8 capture and honest evidence contract)
- site-doctor 3.6.0 -> 3.6.1 (exact generated-runtime exclusions)
- solo 1.9.1 -> 1.9.2 (master-workflow evidence trust contract)
- every other plugin: unchanged and unbumped
- marketplace 1.0.18 -> 1.0.19

## 1.0.18 — 2026-07-12

Post-audit polish of v1.0.17 (independent re-audit: zero failed checks;
the two remaining recommendations are implemented here): CI now
keyless-signs release artifacts on version tags — a `sign` job (Sigstore
cosign 3.0.6 via GitHub OIDC, actions pinned by commit SHA) rebuilds the
zip deterministically from the tagged commit, signs zip + SHA256SUMS +
provenance.json + sbom.json into `.sigstore.json` bundles, verifies each
signature fail-closed against the exact workflow identity at the exact
tag, and publishes the bundle. No key material exists to manage; every
signature lands in the Rekor transparency log. Locally built releases
remain unsigned self-attested evidence — the trust model is otherwise
unchanged, and the gate-evidence JSON contract is untouched. Also:
the run-state schema reference in the AgentRooms runner notes is now
plugin-rooted (`<gate plugin>/skills/production-readiness-reviewer/
schema/run-state-v1.schema.json` — was ambiguously relative), and the
release inventory snapshot now tracks the pristine v1.0.17 tree.
Release-process note: on a fresh tree the source-mode self-check reports
1 expected WARN (`.solo/` absent until `/solo:start-session`). Doc
refresh for the GitHub launch: the README install command now uses the
real repository slug (`unn0wn002/solo-suite` — was a placeholder),
README/SECURITY.md document the tag-signing model and its verification
command, and CONTRIBUTING.md documents the sign job and the
post-release inventory-snapshot step.

### Versions

Component versions move with their trees (drift-guarded by
tests/test_release_versioning.py):

- ai 2.5.0 -> 2.5.1 (runner.md run-state schema path made plugin-rooted)
- every other plugin: unchanged and unbumped
- marketplace 1.0.17 -> 1.0.18

## 1.0.17 — 2026-07-12

Repairs after the independent strict audit of v1.0.16: honest component
versions with a mechanical drift guard, trusted N/A evidence, a formal
run-state contract, endpoint-bound deployment/monitoring evidence,
category-specific document checks, and hash-locked CI dependencies.
Secret/header scanner implementations untouched this pass; no standalone
security scanning was performed (out of scope by request).

### Versions

Component versions now move with their trees (audit blocker 1):

- ai 2.4.0 -> 2.5.0
- gate 2.4.0 -> 2.5.0
- solo 1.9.0 -> 1.9.1

Marketplace release: 1.0.16 -> 1.0.17. NEW
`release/previous-release-inventory.json` (written by
`release/gen_release_inventory.py` against the pristine previous
release) plus `tests/test_release_versioning.py` fail any future release
where a materially changed plugin tree keeps its old version — generated
files (`__pycache__`, `*.pyc`, coverage output, `dist/`, test caches)
never count as changes, and byte-identical plugins must NOT be bumped.

### Counts (blocker 2)

- The AI marketplace entry and `plugins/ai/.claude-plugin/plugin.json`
  claimed "Ships 20 room-* agent definitions"; the filesystem has 24.
  Both now say 24.
- `tests/test_semantic_regressions.py` and the suite self-check now
  verify EVERY count-bearing description — the root metadata, every
  marketplace entry, and every `plugins/*/.claude-plugin/plugin.json` —
  against the actual inventory (room-* agents, plugins/component
  plugins, skills, commands, stdlib scripts, agentsrooms templates, gate
  categories, `.solo` memory files), never only the root description.
- Stdlib helper scripts: 13 (update_run_state.py ships; README,
  marketplace metadata, and the pinned inventory literals all agree).

### Trusted N/A evidence (blocker 3)

- `record_evidence.py --not-applicable` is the ONLY way to produce an
  N/A record: it derives the commit from git itself, validates HEAD and
  tree state, confirms the category/profile cell against the matrix,
  REJECTS the seven mandatory categories, generates timestamps, writes
  atomically under `.solo/gate-evidence/`, and validates the completed
  record against `gate-evidence-v1.schema.json`. There is no flag to
  supply a commit, tree digest, exit code, or timestamp.
- The schema's `notApplicable` branch now REQUIRES
  `recorder: record_evidence.py/v1`, so hand-written N/A JSON fails
  outright. finalize-evidence.md, the finalizer agent, the gate SKILL,
  and the lifecycle/recorder tests all route N/A minting through the
  trusted operation — no workflow or test constructs a final N/A file by
  hand any more.

### Formal run-state contract (blocker 4)

- NEW `schema/run-state-v1.schema.json` and
  `scripts/update_run_state.py` under the production-readiness-reviewer
  skill: the canonical `{schema, run_id, base_sha, integration_sha,
  final_sha}` object (exact lowercase keys; optional 40-lowercase-hex
  SHAs), atomic replacement, run_id/SHA format validation, SHAs read
  from git BY THE HELPER when advancing (never caller-supplied),
  monotonic base -> integration -> final transitions, a FROZEN final_sha
  that can never be rewritten, and schema validation of every read and
  write.
- Both production room templates, runner.md, the evidence-finalizer
  agent, /solo:full-team-dev, /gate:production-ready, and the lifecycle
  tests now record and verify run SHAs exclusively through the helper
  (`advance base|integration|final`, `verify final`). NEW
  tests/test_run_state.py covers the whole helper contract.

### Runtime-directory documentation (blocker 5)

- Every cleanliness instruction now states that ONLY the two generated
  runtime paths are excluded: `.solo/gate-evidence/` and
  `.solo/run-state/` — corrected in finalize-evidence.md,
  gate_policy.py, the production-readiness SKILL, check_evidence.py,
  record_evidence.py, and the tree-digest docstrings/messages.

### Stronger production checks (blocker 6)

- verify-artifact's generic "200 bytes and two headings" check is
  REPLACED by category-specific requirements: required headings per
  category, substantive-content floors (bytes, words, distinct
  vocabulary — repeated filler fails), placeholder/filler rejection
  (TBD/TODO/FIXME/lorem ipsum/coming soon/...), and required
  identifier/decision fields (three concrete bullets for product, an
  ADR-n/DEC-n/'Decision:' for architecture, a concrete breakpoint for
  design, a runnable example for documentation).
- Deployment curl evidence binds the DEPLOYED RESULT to FINAL_SHA: the
  target must be the COMMITTED `version-endpoint:` from .solo/stack.md,
  the timeout is bounded and mandatory, and the captured response must
  contain the derived HEAD (recorder-side and re-checked by the checker
  from the hashed artifact).
- Monitoring curl evidence must hit the COMMITTED `health-endpoint:`
  with a bounded timeout and answer an EXPLICIT health contract (JSON
  status/state/health in the OK set, or the committed `health-expect:`
  marker); a generic homepage response is refused and `gh run view` is
  no longer monitoring evidence (a green CI run is not a monitor).
- gate_policy/gate-evidence/lifecycle tests now prove filler documents
  and generic curl output FAIL (and the loopback fixture server serves
  real /version and /health endpoints for the offline suite).

### Release dependency integrity (blocker 7)

- NEW hash-locked `requirements-dev.lock` pinning the CI test/build
  dependencies INCLUDING transitive dependencies (jsonschema with attrs,
  jsonschema-specifications, referencing, rpds-py, typing-extensions,
  tomli; coverage; PyYAML), every requirement carrying `--hash=sha256:`
  artifact digests. CI installs it with
  `python -m pip install --require-hashes -r requirements-dev.lock`
  (both the initial install and the post-uninstall reinstall).
- The lockfile ships in the release ZIP and sbom.json now carries the
  FULL dependency graph (solo-suite -> direct optional deps ->
  transitive deps) with per-component pins.

### Release engineering

- CHANGELOG gains this explicit Versions section; the self-check
  cross-checks its component bumps against plugin.json reality.

## 1.0.16 — 2026-07-12

One SHA carrier, one evidence lifecycle, executable rooms, and canonical
executable identity. Secret/header scanner implementations untouched this
pass (their checks are reported NOT RUN BY REQUEST in the validation
report).

### SHA carrier + evidence lifecycle (Phase 1)
- The ONLY run-SHA carrier is untracked `.solo/run-state/<run_id>.json`.
  Every remaining instruction claiming BASE_SHA/INTEGRATION_SHA/FINAL_SHA
  lives in `.solo/handoff.md` (or any tracked file) was removed:
  `full-team-website.json` + `production-release.json` finalizer
  deliverables, `/solo:full-team-dev`'s lifecycle paragraph, and the gate
  skill docs now all name run-state exclusively.
- ONE supported lifecycle everywhere: specialists produce raw artifacts
  and N/A candidates only; all tracked code/docs/project memory is
  committed; the ORCHESTRATOR records FINAL_SHA in untracked run-state;
  only the evidence finalizer mints all 14 records at FINAL_SHA; the
  gatekeeper is output-only; the steward never runs at or after
  finalization.
- Every specialist deliverable claiming a final gate-evidence JSON record
  was written early ("<category> gate-evidence record written") was
  removed from both production rooms; the gate skill's "each specialist
  phase writes its own category record" contradiction is gone.
- STRUCTURED steward cutoff: `memory_steward.active_through_stage`
  ("docs" in the full-team room) added to the agentroom schema, enforced
  by validate_rooms.py (required with an evidence lifecycle; must be
  strictly before the finalize stage), documented in the runner, and
  regression-tested — a runner can no longer invoke the steward at or
  after finalize.

### Executable rooms (Phase 2)
- NEW shipped agent `plugins/ai/agents/room-evidence-finalizer.md`: reads
  FINAL_SHA from untracked run-state, requires HEAD == FINAL_SHA, runs
  only /gate:finalize-evidence, writes only untracked .solo/gate-evidence
  outputs, refuses tracked changes, hands off to the output-only
  gatekeeper. BOTH production rooms now map their finalizer seats to it
  (`"agent": "room-evidence-finalizer"` — no more agent_note-only seats),
  and validate_rooms.py rejects any evidence finalizer without a real
  agent.
- STRUCTURED freeze contract `evidence.freeze` (producer: orchestrator;
  after docs, before finalize; commits all tracked release/docs/memory
  changes; verifies a clean tree; writes FINAL_SHA to untracked
  run-state) added to the schema, REQUIRED for production-ready rooms,
  validated (stage adjacency, finalizer stage, carrier equality) and
  present in both production rooms.
- Conditional Run-SHA contract: the ten reusable room agents
  (release-manager, documentation-writer, site-doctor, devops, qa,
  security, git-pr-manager, code-reviewer, browser-qa, ai-agent-reviewer)
  no longer demand an INTEGRATION_SHA unconditionally — verification is
  keyed to the room's `verify_at_integration_sha` /
  `verify_at_final_sha` lists, and a non-worktree room (production-
  release) that never creates an INTEGRATION_SHA no longer implies one.
  New `worktrees.verify_at_final_sha` (finalizer + gatekeeper) replaces
  their incorrect membership in `verify_at_integration_sha`.
- READ PROVENANCE enforced by validate_rooms.py: every concrete `.solo/`
  read needs an earlier-stage producer, an `assumes_preexisting` entry,
  or a structured run-state contract. All four bundled rooms gained the
  missing entries (production-release: project.md, env-contract.md,
  api-contract.md; full-team: project.md; bug-fix-loop: bugs.md,
  architecture.md; site-doctor-audit: stack.md, monitoring.md,
  env-contract.md).

### Gate identity + evidence strength (Phase 3)
- finalize-evidence.md and the production-readiness SKILL never show
  `gate_policy.py verify-artifact` as a standalone finalization command —
  document-backed evidence is always wrapped through record_evidence.py
  (regression-tested against every bash block in both files).
- CANONICAL EXECUTABLE IDENTITY for EVERY accepted family
  (`gate_policy.resolve_executable`): argv[0] resolves through PATH
  (shutil.which) or must be absolute; unresolved executables and
  executables resolving inside the project/runtime dirs are rejected;
  the recorder EXECUTES the resolved absolute path (never the bare
  token) and RECORDS it (`resolved_executable`, now schema-required);
  check_evidence.py re-resolves and re-validates the identity. Inert
  PATH-resolution regression fixtures cover python/python3, pytest, gh,
  npm/npx, curl, cargo, make, go, alembic, pip-audit, govulncheck —
  proving project-local resolution is rejected, not silently replaced.
- `--out`/`--artifact` are RE-VALIDATED after the evidence command and
  immediately before the atomic writes; a command that swaps the
  (gitignored) evidence directory for a symlink mid-run now refuses the
  record (new regression test).
- Production evidence strengthened: deployment/monitoring can NEVER pass
  on release.md/monitoring.md bytes/headings (verify-artifact removed
  from those categories and from ARTIFACT_REQUIREMENTS); GitHub workflow
  evidence must be `gh run view <id> --exit-status --json
  headSha,conclusion,status` and BOTH the recorder and the checker parse
  the captured JSON, requiring headSha == derived HEAD and conclusion ==
  "success" (an arbitrary old run can no longer prove the current
  commit; `gh release view` removed for the same reason); live URL and
  domain evidence is bound to hosts recorded in the COMMITTED
  .solo/stack.md at HEAD (fail-closed when absent); unavailable live
  evidence stays explicitly UNVERIFIED and the gate is BLOCKED.

### QA, counts, consistency (Phase 4)
- Windows: the fail-closed test no longer `shutil.rmtree`s `.git`
  (read-only object files raise PermissionError on Windows) — it RENAMES
  `.git` to `.git-disabled` via the shared `tests/exe_fixtures.py`
  helper, which also provides a read-only-clearing force_rmtree used for
  git-fixture cleanup.
- NEW tests/test_semantic_regressions.py: tripwires for tracked-file SHA
  carrier language, early specialist record claims, standalone
  verify-artifact finalization docs, post-freeze gatekeeper/steward
  work, a finalizer without a real agent, unconditional room-agent SHA
  prerequisites, and narrative count drift.
- Canonical room-agent count is 24 (room-evidence-finalizer added):
  README headline + narrative, marketplace description, AgentRooms
  SKILL.md, tests/test_inventory.py (pinned count AND the exact 24-name
  list), and this changelog all agree with the filesystem.
- Full-team description corrected everywhere: 21 staged seats plus the
  stage-independent steward; 22 seat definitions total; 14 stages
  including finalize; every staged seat mapped to a shipped agent
  (SKILL.md previously claimed 13 stages and omitted finalize).
- The rooms SKILL's Launch Room no longer has the gatekeeper running
  /solo:handoff-memory AFTER the gate — handoff memory lands before the
  freeze; the gatekeeper is output-only.

## 1.0.15 — 2026-07-11

Canonical command identity, fail-closed repository cleanliness, contained
evidence outputs, and a run-state SHA lifecycle that removes the
self-referential-commit defect. Secret/header scanners untouched this pass.

### Gate — canonical command identity (gate_policy.py)
- Executable and helper BASENAMES are never trusted. Interpreters are
  accepted only as bare `python`/`python3` (PATH-resolved) or absolute
  paths OUTSIDE the project; `.solo/gate-evidence/python -m unittest` and
  `./python` are refused.
- Bundled helpers must BE the installed helper: exact canonical path or
  byte-identical (sha256) copy OUTSIDE the project. `python
  .solo/gate-evidence/scan_secrets.py .` and `python
  .solo/gate-evidence/gate_policy.py verify-artifact product` are refused;
  a missing reference copy refuses (fail closed).
- Zero-test escape flags denied for all supported runners
  (--passWithNoTests / --pass-with-no-tests / --allow-no-tests /
  --no-tests=pass / --if-present / --ignore-scripts, case- and
  `=`-suffix-insensitive).
- `gh run list` is no longer deployment or monitoring evidence; the policy
  requires an exact run with a status-sensitive command:
  `gh run view <ID> --exit-status`.
- `command_id` is REQUIRED in the schema; the checker recomputes it from
  command_argv and requires equality, and requires `command` to equal the
  canonical joined argv.

### Gate — fail-closed cleanliness + contained outputs
- The porcelain parser is replaced by three explicit checks: index vs HEAD
  (`git diff --cached -M -C`, EVERY staged entry is dirt — additions,
  deletions, renames and copies with BOTH sides evaluated; a staged rename
  of app.txt into .solo/gate-evidence/ fails), working tree vs index, and
  non-ignored untracked files. Git failures return None and every caller
  REFUSES — an unrunnable check never means clean.
- IGNORED-FILE POLICY (documented in repo_state): gitignored paths are
  exempt BY DESIGN — .gitignore is tracked, reviewed content; the docs no
  longer claim "ANY untracked file".
- The recorder RE-CHECKS HEAD, the committed-tree digest, and cleanliness
  AFTER the evidence command executes; a command that mutates the
  repository produces no record.
- `--out` and `--artifact` must realpath-resolve inside
  `<root>/.solo/gate-evidence/`: absolute outside paths, `..`, symlink
  escapes (deepest-existing-ancestor resolution), and tracked files are
  refused; the checker refuses input records outside the evidence dir.

### Run-state SHA lifecycle (BASE / INTEGRATION / FINAL)
- A commit cannot contain its own SHA: run SHAs now travel in UNTRACKED
  `.solo/run-state/<run_id>.json` (gitignored, like the evidence dir; both
  are refused if tracked). Planning memory is committed FIRST, then
  BASE_SHA is computed and passed to builders through runtime state; same
  for INTEGRATION_SHA (integrator) and FINAL_SHA (freeze).
- The release freeze commit contains ALL tracked code, docs, release plans
  and project memory; /solo:handoff-memory and tasks/decisions/risks
  updates moved BEFORE the freeze. After it, the production gatekeeper is
  OUTPUT-ONLY (no tracked writes, no proposals, /solo:handoff-memory
  removed from the gate stage) and the memory steward never runs again.
- validate_rooms.py: post-finalizer exemptions REMOVED — any declared or
  implicit tracked write (or proposal, or /solo:handoff-memory) after the
  finalizer is rejected for every seat including the exit gate;
  /gate:production-ready no longer implies a risks.md write; SHA transport
  is validated structurally (stored_in/final_sha_recorded_in must be
  .solo/run-state/ paths; every builder and every verify seat must READ
  the runtime-state file). Templates, agents, runner.md, full-team-dev.md,
  finalize-evidence.md and the gate skill updated.

### Metadata & delivery
- Marketplace metadata: unsupported count fields REMOVED (the CLI warned
  on plugins/skills/commands/scripts/agents/license) — root validation now
  passes with ZERO warnings; canonical counts live in the README line and
  tests/test_inventory.py pinned literals (18/56/102/12 scripts/23 room
  agents). self_check now FAILS if the fields reappear.
- ci-requirements.txt pins PyYAML==6.0.2; the SBOM carries its version and
  a build/validation tool inventory (Python, git, Claude CLI, Node).
- 50 new regression tests (345 total): fake helpers/interpreters, zero-test
  flags, gh run list, staged renames, ignored-file policy, git fail-closed,
  path escapes, worktree BASE_SHA runtime transport, FINAL_SHA
  non-self-reference, post-final zero writes, flow-leaves-HEAD-unchanged.

### Versions
- ai 2.3.0 -> 2.4.0
- gate 2.3.0 -> 2.4.0
- solo 1.8.0 -> 1.9.0

## 1.0.14 — 2026-07-11

Evidence-gate rearchitecture and honesty release: shared command policy with
full-argv validators (git no-ops are dead), git-object-derived source identity,
a FINAL_SHA evidence lifecycle with a dedicated finalizer, chunked long-line
secret scanning, real Permissions-Policy/CSP quality validation, nine new
AgentRooms rejections + a dedicated bug reproducer, accurate pinned counts,
pinned CI dependencies, and reproducible archives.

### Gate (production evidence)
- **Shared policy module `plugins/gate/lib/gate_policy.py`** used by BOTH
  record_evidence.py and check_evidence.py: per-category FULL-ARGV validators
  (no prefixes). `git log`/`git ls-files` qualify as evidence of NOTHING, in no
  category; --help/--version/dry-run/list-only tokens, unrelated paths, and
  arbitrary suffixes are rejected. Document-backed categories use the new
  executable `gate_policy.py verify-artifact <category>` content check.
- **--allow-dirty removed.** Any modified, deleted, or untracked path outside
  .solo/gate-evidence/ refuses recording and fails checking. Byproducts must be
  gitignored.
- **Source identity from git objects**: commit = `git rev-parse HEAD`;
  tree_digest = SHA-256 over `git ls-tree -r HEAD` (path + blob sha, evidence
  dir excluded) — mutating working-tree bytes cannot forge it.
- **check_evidence.py derives HEAD itself**; --commit is optional and must
  EXACTLY equal derived HEAD (usage error otherwise). Records must match HEAD
  exactly (full 40-hex) and the recomputed committed-tree digest.
- **Strict bundled-schema validation without jsonschema**: a built-in draft-07
  evaluator (with $ref) always runs. Verified records now REQUIRE status,
  recorder, command_argv (+ command/command_id), tree_digest, project, exact
  HEAD, environment, timestamps, reviewer, exit_code, contained artifact, and
  recomputed artifact hash; the checker RE-VALIDATES command_argv against the
  category policy.
- **Honest trust model**: records are SELF-ATTESTED LOCAL EVIDENCE, not
  cryptographic attestations (docs corrected everywhere); a trusted CI
  signature/identity is the documented upgrade path.
- **Single supported workflow**: .solo/gate-evidence/ stays untracked/
  gitignored. Tracked evidence is an unsupported state both tools refuse; the
  former "option B" (commit-the-evidence tree-digest binding) is removed.

### Evidence lifecycle
- Specialists produce raw artifacts only — final category records against
  intermediate commits are invalid by construction (validator-enforced).
- New **`/gate:finalize-evidence`** command + **evidence_finalizer** seat:
  after code, CI, release plans, docs, and project memory are committed as
  FINAL_SHA, the finalizer verifies HEAD == FINAL_SHA and re-runs every
  applicable category command, minting all 14 records (verified or
  matrix-permitted N/A). After FINAL_SHA no tracked writes are permitted.
- Planning memory is committed BEFORE BASE_SHA is recorded.
- full-team-website.json, production-release.json, full-team-dev.md,
  runner.md, the gate skill/commands, and the gatekeeper agent all updated;
  rooms gated by /gate:production-ready must declare the `evidence` block.

### Secret scanner (site-doctor)
- Lines over 2,000 chars are SCANNED in bounded overlapping chunks (4096/512)
  — never skipped-yet-reported-complete; boundary-straddling secrets found;
  redaction guarantees unchanged (coverage.long_lines_chunked).
- Strict UTF-8 decoding (no errors='ignore' masking) + UTF-16-with-BOM
  support; undecodable or extensionless-binary content makes
  coverage.complete=false and exits 3. Known binary formats (.docx, .xlsx,
  .pptx, .jar, ...) are policy-excluded by extension.

### Header validation (site-doctor)
- Real Permissions-Policy syntax/directive validation (feature registry +
  structured allowlists): `permissions-policy: banana` can never PASS.
- CSP quality rules: `default-src *` (or any wildcard/scheme-wide script
  source) FAILS; missing default-src AND script-src FAILS (materially
  incomplete); 'unsafe-eval' warns.

### AgentRooms (ai)
- New **room-bug-reproducer** agent: verifies and records BASE_SHA only,
  runs before any fixer exists, never requests a fixer commit; only the
  verifier checks out the fixer's exact commit.
- validate_rooms.py/schema now reject: garbage gate_evidence_map values,
  evidence producers with no commands, evidence from unmerged proposals,
  unreachable/missing producers, wrong integration modes (checkout-exact-sha
  with multiple builders; integrator == sole builder), worktree seats mapped
  to agents without `isolation: worktree`, empty applies_to, conditional
  seats without room profiles / unrecognized profiles, and loop groups that
  match no stage. All rejections tested on the jsonschema AND
  builtin-evaluator paths.

### Metadata & compatibility
- README scoring states the exact formulas: `applicable_max =
  applicable_category_count * 10`; `normalized_score = round(total /
  applicable_max * 100)`; the production-readiness skill example is now
  internally consistent (100/120 -> 83/100 with SEO/Analytics N/A).
- marketplace metadata carries accurate counts (18 plugins, 56 skills,
  102 commands, 12 helper scripts, 23 room-* agents) enforced by pinned
  drift tests. (Spec note: with the mandated new reproducer agent the real
  room-agent count is 23, not 22.)
- self_check.py: `when_to_use` allowed; `shell` accepts bash|powershell and
  REJECTS none; hooks/mcpServers/permissionMode are REJECTED on
  plugin-shipped agents (the platform ignores them there). Windows `py -3`
  recommendations removed (unverifiable here).

### CI & release
- Pinned CI dependencies via committed `ci-requirements.txt`
  (jsonschema==4.23.0, coverage==7.6.1); all adversarial suites are
  mandatory CI steps, including a no-jsonschema builtin-evaluator run and a
  reproducible-archive double-build check.
- SBOM: component versions, valid bom-refs, purls, and dependency links.
- Reproducible ZIP: commit-time (SOURCE_DATE_EPOCH-convention) timestamps,
  normalized 0644/0755 permissions, sorted members, fixed compression.

### Versions
- ai 2.2.0 -> 2.3.0
- gate 2.2.0 -> 2.3.0
- site-doctor 3.5.0 -> 3.6.0
- solo 1.7.0 -> 1.8.0

## 1.0.13 — 2026-07-11

Hardening release: executed evidence attestations, matrix-governed N/A, schema-first
room validation, an explicit worktree execution contract, honest scanner coverage,
value-validating header checks, and packaged-ZIP (not source-checkout) marketplace CI.

### Gate (production evidence)
- **Applicability matrix (normative)** in `check_evidence.py`/SKILL/schema: product,
  architecture, security, testing, deployment, monitoring, documentation may NEVER be
  N/A; the other seven only for the documented profiles. All-14-N/A now fails for
  every profile.
- N/A records now require a non-empty reviewer, a substantive reason (>= 20 chars,
  >= 4 words — one character fails), and a structured `applicability` object
  (matrix cell, profile_source, checked list).
- `gate-evidence-v1.schema.json` rewritten as a strict `oneOf` (verified evidence |
  not-applicable), both branches typed with `additionalProperties: false`.
- **New `record_evidence.py`**: executes an allowlisted category command itself,
  captures stdout/stderr and the REAL exit code, determines the commit SHA and a
  tracked-tree digest (excluding `.solo/gate-evidence/**`) itself, hashes the output
  artifact, and writes JSON atomically. Hand-asserted `exit_code: 0` is dead.
- Self-invalidating-commit problem solved two ways: attest AFTER the final
  integration commit with the evidence dir untracked, or bind to the tree digest —
  verified by `check_evidence.py --verify-tree`.
- Scoring denominator agrees everywhere: accepted N/A categories leave the
  denominator (normalized = round(total / (10 × applicable) × 100)); SEO/analytics
  hard blockers apply only when the category is applicable.

### AgentRooms (ai)
- `validate_rooms.py` now applies the ACTUAL `agentroom-v1` JSON Schema FIRST
  (jsonschema lib when available, strict built-in evaluator otherwise); malformed
  root/seat/stage/run/profile/gate-map/loop types return validation errors, never
  tracebacks. `run` identity is required; profiles/applies_to are enum-checked.
- EXACTLY ONE seat must execute the exit gate; the last-stage fallback is gone.
- Exact path/fnmatch semantics: a descriptive directory string no longer satisfies
  `*.json`; the executor's own writes never satisfy its own gate; every
  gate_evidence_map category needs an earlier producer of the CONCRETE
  `.solo/gate-evidence/<category>.json`, checked per profile against the matrix.
- One documented graph model: entry-stage seats → contracted handoff edges →
  exit-gate executor; every active seat must be reachable AND reach the exit for
  the profile-free pass and all six profiles. `handoff_to` may now be a list
  (fan-out); dead ends outside the exit seat fail.
- **Worktree execution contract** (`worktrees` block, schema + validator enforced):
  base SHA recorded BEFORE spawning (worktree agents branch from the DEFAULT
  branch, not the parent session HEAD), builder payload (worktree_path, branch,
  clean commit_sha, tests, proposal), proposal transport across isolated worktrees
  (committed in-branch, shared object store), integrator merges EXACT SHAs into ONE
  integration commit, and QA/browser-QA/security/site-doctor/AI-reviewer/gatekeeper
  all verify that exact SHA. The bug-fix verifier checks out the fixer's exact
  commit — templates, agents, runner.md, and /solo:full-team-dev updated.

### Site doctor
- `scan_secrets.py`: every candidate file gets an explicit outcome (inspected /
  skipped_too_large / unreadable / suppressed / binary) with a coverage block;
  `--max-bytes 1` reports incomplete coverage and exits 3 instead of lying clean;
  zero inspected files exit nonzero; single-file roots supported, other roots
  rejected; fingerprints are HMAC-SHA256 keyed (env SECRETSCAN_HMAC_KEY or per-run
  key) — no dictionary-attackable unsalted hashes of passwords.
- `check_headers.py` validates VALUES: non-'nosniff' x-content-type-options,
  unknown referrer-policy tokens, unparseable CSP, invalid x-frame-options, invalid
  SameSite, and SameSite=None-without-Secure can never PASS; adds UNVERIFIED level,
  `RESULT:` line, and exit 3 for unverified-only runs.
- `extract_meta.py`, `check_links.py`, `scan_trackers.py`, `check_deps.py`:
  structured PASS/WARN/FAIL/UNVERIFIED verdicts, `RESULT:` lines, meaningful exit
  codes (0 clean / 1 fail / 2 usage / 3 unverified).

### Suite integrity (solo)
- `self_check.py`: raw docstring fixes the invalid `\s` escape (compiles under
  `-W error::SyntaxWarning`); every `open()` context-managed (no ResourceWarnings);
  frontmatter key sets updated to the current official fields (Agent Skills spec +
  Claude Code skills/commands; camelCase subagent fields incl. permissionMode,
  maxTurns, memory, background, effort, initialPrompt); enum-like values validated
  (isolation must be `worktree`, context `fork`, documented colors/modes);
  SchemaStore `$schema` URLs verified by VALUE.

### Packaging & CI
- `build_release.py` rebuilt: stages from an explicit ALLOWLIST into a clean temp
  directory before zipping — `.coverage`, `scan.json`, `__pycache__`, `dist/`,
  test/runner artifacts can never ship; refuses to build without a real git commit
  (provenance carries the real source SHA + tree digest); SBOM records the optional
  jsonschema test dependency.
- CI: Node 22 (Claude CLI 2.1.205 requires >= 22); compileall runs with
  `-W error::SyntaxWarning`; unittest runs with ResourceWarning as error; the
  marketplace/install smoke test now runs against the EXTRACTED PACKAGED ZIP
  (validate all 18 strict, marketplace add, install solo + full-team, list +
  details) and is named accordingly — the source-checkout test remains, correctly
  labeled; the package step asserts `.coverage`/`scan.json` are absent from the ZIP.
- Metadata: SchemaStore URLs for plugin + marketplace manifests; repository URL
  moved to https://github.com/unn0wn002/solo-suite.

### Versions
- ai 2.1.0 -> 2.2.0
- browser 1.1.0 -> 1.1.1
- design 1.0.0 -> 1.0.1
- dev 1.0.1 -> 1.0.2
- docs 1.1.0 -> 1.1.1
- full-team 1.0.0 -> 1.0.1
- gate 2.1.0 -> 2.2.0
- git 1.1.0 -> 1.1.1
- growth 1.0.1 -> 1.0.2
- project 1.0.0 -> 1.0.1
- release 1.1.0 -> 1.1.1
- repo 1.0.2 -> 1.0.3
- security 1.1.0 -> 1.1.1
- site-doctor 3.4.1 -> 3.5.0
- solo 1.6.1 -> 1.7.0
- spec 1.0.1 -> 1.0.2
- stack 1.4.1 -> 1.4.2
- test 1.0.1 -> 1.0.2

## 1.0.12 — 2026-07-10

Blocker release addressing the independent audit of 1.0.11. No new features.

### Frontmatter integrity
- Repaired the six site-doctor commands whose closing `---` had been glued to the last frontmatter line (backups, email-check, full-checkup, incident, monitoring, load-test) — the closing delimiter is now a standalone line, so line-anchored loaders no longer drop their metadata at runtime.
- `self_check.parse_frontmatter` rewritten with LINE-ANCHORED delimiters (`split_frontmatter`): a `value---` glue is rejected as unterminated; regression tests prove it (`tests/test_self_check.py: FrontmatterAnchoring`). Official key sets extended to the complete current skill frontmatter (adds license, metadata, context, agent, hooks) and `plugins/*/agents/*.md` are now validated too (name/description, official agent keys incl. `isolation`, filename match).

### Gate evidence (rebuilt)
- `check_evidence.py` now enforces the FULL contract: exactly one accepted record per category across all 14 (verified evidence or machine-readable N/A), duplicate categories rejected, `--project` match required, artifact SHA-256 RECOMPUTED against `--root` with missing/unreadable/outside-project artifacts rejected, and stale (wrong-commit/wrong-environment/expired) records rejected as before. N/A records carry a recognized project profile + substantive reason and must match `--profile`.
- Every specialist phase now produces its category record (declared `.solo/gate-evidence/<category>.json` writes in the templates and the full-team-dev flow); both production gatekeepers read `.solo/gate-evidence/*.json` and author N/A records for profile-skipped categories. Adversarial tests: incomplete category sets, fake digests, traversal artifacts, duplicates, wrong project, bogus N/A profiles (`tests/test_gate_evidence.py`, 27 tests).

### AgentRooms (repaired)
- validate_rooms.py: stage reachability is validated SEPARATELY FOR EVERY PROFILE with skipped-seat contraction — the conditional Growth stage can no longer disconnect internal/API/library flows; same-stage read-after-write dependencies are detected; every gate-required artifact must have an earlier in-room producer (glob-prefix aware) or an explicit `assumes_preexisting` reason; every seat must map to a real `room-*` agent (existence-checked) or carry an explicit `agent_note`.
- full-team-website v3: new `integrate` stage (worktree integrator merges the three build worktrees into ONE integration branch BEFORE review), Documentation moved to its own stage AFTER release.md is produced (the old release-stage read-after-write is exactly what the new validator rejects), gatekeeper reads `.solo/gate-evidence/*.json`. site-doctor-audit v3 routes the connector `stack.md` update through a steward proposal (same-stage RAW removed). production-release v3 declares `assumes_preexisting` for earlier-phase artifacts. Two new agents (`room-worktree-integrator`, `room-bug-fixer`); code-writing agents (`room-frontend-developer`, `room-backend-developer`, `room-database-engineer`, `room-bug-fixer`) declare `isolation: worktree`. Stale "13 seats across 10 stages" doc corrected (21 seats / 13 stages + steward).

### Helper hardening (adversarial)
- scan_secrets.py rejects `--max-bytes <= 0` (exit 2). check_headers.py parses cookie attributes STRUCTURALLY (first segment name=value, rest attributes — values containing "secure" no longer count as flags) and malformed HSTS (`max-age=banana; preload`) no longer crashes. check_email_dns.py counts repeated SPF branches per EVALUATION (memoized, stack-based cycle detection) and a capped/incomplete count is never reported PASS. check_links.py and extract_meta.py reject non-positive --max-pages and negative/NaN/infinite --delay (finite-number validators). Regression tests in `tests/test_script_fixes.py: AdversarialV1012`.

### Documentation contradictions
- `.solo/config.md` is ALWAYS local and ALWAYS gitignored (project-memory-manager now says so; it is the sole exception to "committed to git"). project-memory-manager says 16 phases with the current phase list and gate vocabulary (NO-GO for before-* gates; BLOCKED / SAFE WITH WARNINGS / SAFE TO LAUNCH for the production gate). full-team-dev exercises ALL 17 component plugins directly (README + command corrected). The url_guard dependency claim corrected from seven skills to the real FIVE network-fetching skills (dependency-audit and security-review bundle offline scripts and copy cleanly).

### CI
- CI installs a PINNED Claude CLI (`@anthropic-ai/claude-code@2.1.205` via pinned setup-node) and the official `claude plugin validate` steps now FAIL the job when the CLI cannot run (no silent fallback). New marketplace smoke test from OUTSIDE the repo with an isolated CLAUDE_CONFIG_DIR: `marketplace add` -> `install solo` -> `install full-team` (must pull all 16 dependencies) -> `marketplace list` + `plugin list` must show all 18 plugins.

### Versions
- site-doctor 3.4.0 -> 3.4.1, solo 1.6.0 -> 1.6.1, ai 2.0.0 -> 2.1.0, gate 2.0.0 -> 2.1.0; cheatsheet docx v3.4.0 -> v3.4.1; suite metadata 1.0.11 -> 1.0.12.


## 1.0.11 — 2026-07-10

### Critical runtime & security (Phase 1)
- **Helper paths**: every skill now invokes bundled scripts via `${CLAUDE_PLUGIN_ROOT}/…` instead of CWD-relative `python3 scripts/…` (8 SKILL.md files), with a documented `python3` → `python` → `py -3` fallback; new `tests/test_installed_cwd.py` proves helpers work from a foreign working directory and from a copied plugin cache. README's standalone-copy claim corrected: the seven script-bundling site-doctor skills share `lib/url_guard.py` and are not standalone (dependency documented; self-check enforces the note).
- **Secret scanner** (`scan_secrets.py`): findings now contain ONLY relative path, line, rule name, a redacted preview (4-char prefix + mask + 2-char suffix), and an irreversible SHA-256 fingerprint — never the matching line or value, in text or `--json` mode. Self-referential rule-definition hits suppressed; `secretscan:ignore` / `ignore-file` pragmas added; regression tests assert no complete fake secret ever appears in stdout/stderr/JSON (`tests/test_scan_secrets.py`).
- **Read-only DB audit**: `ANALYZE` and `PRAGMA optimize` removed from `database-audit/references/audit-queries.md` and moved to database-fix's new Maintenance section (explicit confirmation + verified backup + mutation warning + rollback guidance); policy test `tests/test_readonly_audit.py` rejects write-capable SQL in the read-only reference.
- **Token protection**: `.solo/config.md` may hold only service URLs, non-secret identifiers, and the NAME of the token's environment variable — never token values; config auto-gitignored; secrets/config excluded from sync content; logs redacted; external sync defaults to dry-run with explicit confirmation; `/solo:sync-grafana`, `/solo:sync-obsidian`, and the memory-sync skill are `disable-model-invocation: true`.
- **Browser QA safety contract**: localhost/staging/test-tenant default, synthetic data only, no real payments/emails/SMS/webhooks/destructive actions, confirmation before side-effecting submissions, record + clean up created records; `/browser:smoke-test` and `/browser:form-submit-test` are manual-only (`disable-model-invocation: true`).

### AgentRooms & full-team (Phase 2)
- New enforceable schema `agent-room-templates/schema/agentroom-v1.schema.json`; `validate_rooms.py` rewritten: unique seat AND stage ids, stage reachability, bounded loops (`max_iterations` required), read/write/**proposal** declarations, gate prerequisites (`gate_requires` vs gatekeeper reads), workspace/worktree ownership for parallel code writers, artifact locks, run-id policy, and **implicit command writes** (site-doctor audits → tasks/decisions/handoff, dev commands → decisions, gates → risks, …) — declared-`writes`-only validation is gone. `check_tasks_file()` detects duplicate T-IDs. 21 new validator tests.
- **Memory steward** introduced: a single seat owns shared memory, receives proposals (`.solo/proposals/<seat>-<run_id>.md`), merges decisions/handoffs, allocates unique T-IDs, detects conflicts. Templates migrated: `full-team-website.json` rebuilt with 20 seats/11 stages staffing all 17 roles + steward, gatekeeper now reads the full 14-category evidence set (`gate_evidence_map`); `bug-fix-loop.json` gate receives review/security/test/rollback evidence and its loop is bounded (3); `site-doctor-audit.json` declares its real shared-memory effects via proposals with the triager as steward; `production-release.json` declares all implicit writes.
- **Execution honesty**: rooms are validated work orders, not a runtime — 20 Claude Code agent definitions added (`plugins/ai/agents/room-*.md`) plus `references/runner.md` documenting the adapter for Claude Code subagents or external orchestrators.
- `/solo:full-team-dev` is now genuinely full-team: 16 phases, 17 named roles, adds /stack:connector-check, /test:edge-cases, /design:ui-review after implementation, /ai:review-output between major phases, /growth:conversion-audit; **project profiles** (public marketing / SaaS / e-commerce / internal / API / library) with mandatory evidence-backed N/A reasons for every skipped step. "Uses every plugin" claim corrected (16 of 17 directly).

### Production gates (Phase 3)
- 14 fixed categories (Product, Architecture, Design, Frontend, Backend, Database, Security, Testing, Performance, SEO, Analytics, Deployment, Monitoring, Documentation), each /10, total /140, normalized `round(total/140×100)`; statuses are exactly **BLOCKED / SAFE WITH WARNINGS / SAFE TO LAUNCH** (GO/NO-GO reserved for before-code/merge/deploy); vendor checks run only for providers in `.solo/stack.md` with N/A evidence for the rest.
- Machine-readable gate evidence: `gate-evidence-v1` schema + `check_evidence.py` (project, commit SHA, environment, timestamp, category, command, exit code, artifact + sha256, reviewer, expiry); the gate **rejects stale evidence** — wrong commit, wrong environment, expired, or older than 7 days (`tests/test_gate_evidence.py`, 13 tests).

### Helper script correctness (Phase 4) — with regression tests (`tests/test_script_fixes.py`)
- `check_headers.py`: sensitive-path timeout/error no longer reported PASS; full HSTS syntax/semantics validation (missing/zero/non-numeric max-age FAIL, duplicate directives FAIL, includeSubDomains/preload guidance); HTTPS-upgrade redirects must land on the same site (www-variant allowed) and **every hop is validated** with downgrade detection.
- `check_links.py`: redirect chains beyond `--max-redirect-hops` (default 2) are reported and fail the run; `--fail-on-mixed` makes mixed content non-zero; `--max-pages`/`--delay` validated positive/non-negative.
- `check_email_dns.py`: exact DMARC tag parsing — `sp=reject` no longer masquerades as base `p=reject` (missing/invalid `p=` now FAILs; `sp=` reported separately); SPF lookup counting now recursively resolves `include:`/`redirect=` with cycle protection and counts bare `a`/`mx`.
- `extract_meta.py`: an H1 with nested spans/nodes counts once (buffered text, depth-tracked).
- `scan_trackers.py`: resources deduplicated (no double-counted `<img>`); cookie flags parsed structurally from attribute segments instead of substring matching.
- `check_deps.py`: only full versions (`1.2.3`, `v1.2.3`, pre-release/build suffixes) classify as exact pins; `1.x`, `1.2.*`, hyphen ranges, and `||` unions are ranges.

### Suite integrity, CI, metadata, docs (Phase 5)
- `self_check.py` rewritten: proper YAML frontmatter parsing (PyYAML when present, strict subset fallback), official frontmatter keys allowed (name, description, argument-hint, disable-model-invocation, user-invocable, allowed-tools, model), **installed-plugin mode** (single plugin dir, no marketplace needed), validation of `${CLAUDE_PLUGIN_ROOT}` paths + helper references + CWD-relative invocation ban + standalone-claim note + CHANGELOG-vs-plugin version agreement + agentroom schema presence; summary now states a clean run is static structure checking, not proof of runtime health.
- `disable-model-invocation: true` added to every sensitive surface: /security:secrets-fix, /site-doctor:migrate-data, /site-doctor:load-test, /git:sync-issues, /solo:sync-grafana, /solo:sync-obsidian, /browser:smoke-test, /browser:form-submit-test, and the website-fix / database-fix / data-migration / memory-sync skills.
- CI hardened: least-privilege `permissions: contents: read`, actions pinned to commit SHAs, timeout-minutes, concurrency cancellation, Python compileall, unit tests + coverage (best-effort), secret-output regression tests, AgentRooms validation, installed-CWD helper tests, per-plugin validation, `claude plugin validate` when the CLI exists, packaged-ZIP install smoke test, Ubuntu + Windows.
- Metadata: every plugin.json gains `$schema`, displayName, version, license (MIT), repository, homepage, and the aligned author identity **Sakura Yukihira (Ayaya)** (matching the LICENSE copyright; marketplace owner updated identically); placeholder repo URLs replaced with the canonical `ayaya/solo-suite` slug (confirm before publishing). New **full-team meta-plugin** depends on all 17 component plugins (individually installable as before) and adds `/full-team:verify`. Release artifacts now include SECURITY.md, CONTRIBUTING.md, SHA-256 checksums, an SBOM/dependency inventory (stdlib-only), provenance, and a single enclosing top-level folder in the ZIP.
- Docs: counts corrected to 18 plugins / 56 skills / 101 commands / 11 scripts; "every command uses one of three output contracts" corrected (most do; documented exceptions); "full-team-dev uses every plugin" corrected; "any skill folder can be copied standalone" corrected with the url_guard dependency; PATCH-NOTES-c1-c3.md marked superseded; cheatsheet docx bumped to v3.4.0 with the trailing near-blank page and empty comments part removed and document metadata updated.

### Versions
- ai 1.3.0 → 2.0.0 (schema + steward + agents), site-doctor 3.3.0 → 3.4.0, solo 1.5.2 → 1.6.0 (self-check rewrite, sync safety), gate 1.x → 2.0.0 (14-category scoring + evidence), browser 1.0.x → 1.1.0 (safety contract), git 1.0.x → 1.1.0 (sync-issues manual-only), security 1.0.x → 1.1.0 (secrets-fix manual-only), full-team 1.0.0 (new); suite metadata 1.0.10 → 1.0.11.


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
