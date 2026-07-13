# Contributing to solo-suite

## Ground rules

- **Stdlib only** for helper scripts — no runtime dependencies, ever.
- **Evidence over claims**: README/marketplace counts and workflow claims are
  validated by `self_check.py` and `tests/test_inventory.py`; if you change
  reality, change the claims in the same commit.
- **Safety contracts are not optional**: anything that can write externally,
  mutate production, migrate data, submit forms, or touch secrets is
  `disable-model-invocation: true` and confirms before acting. New commands
  in those categories must follow `SECURITY.md`.
- Windows, macOS, and Linux all matter: use `${CLAUDE_PLUGIN_ROOT}` for
  helper paths, forward-slash-normalize glob output, and keep the test suite
  green on ubuntu-latest and windows-latest.

## Layout

- `plugins/<name>/.claude-plugin/plugin.json` — manifest ($schema,
  displayName, version, license, repository, homepage required)
- `plugins/<name>/commands/*.md` — slash commands (frontmatter: description,
  argument-hint, optional disable-model-invocation)
- `plugins/<name>/skills/<skill>/SKILL.md` — skills (official frontmatter
  keys only: name, description, argument-hint, disable-model-invocation,
  user-invocable, allowed-tools, model)
- `plugins/ai/skills/agent-room-templates/` — AgentRooms schema, validator,
  templates; `plugins/ai/agents/` — room agent definitions
- `tests/` — offline stdlib unittest suite (loopback fixtures only)

## Before you open a PR

```
python -m unittest discover -s tests -t . -v
python plugins/solo/skills/suite-integrity/scripts/self_check.py . -
python plugins/ai/skills/agent-room-templates/scripts/validate_rooms.py
claude plugin validate .            # when the Claude CLI is available
```

All four must pass. Bump the touched plugin versions, the marketplace
metadata version, and add a CHANGELOG entry (top section, `## x.y.z — date`).

## Releases

`release/build_release.py` (see CI) produces a local, unsigned release
candidate with one enclosing top-level folder, `SHA256SUMS`, `sbom.json`, and
`provenance.json`. Candidates are tested by installing the packaged ZIP into a
disposable project outside the repository and running helpers from a foreign
working directory. Do not publish a local candidate as canonical. Pushing the
reviewed `v<version>` tag triggers three isolated CI stages: a read-only build,
an OIDC-only signer, and a contents-write-only publisher. Checksums are
revalidated at every artifact boundary; the publisher creates a draft, downloads
every remote asset again, byte-compares and signature-verifies it, and only then
promotes the release.

Repository administrators must configure the `release-signing` and
`release-publishing` GitHub environments with the intended branch/tag and
required-reviewer protection rules. Workflow YAML can name those environments,
but it cannot prove their repository-side settings. Treat an unprotected or
unverified environment as a release-process blocker.

For v1.0.21, publish in two reviewed stages from PowerShell. Supply the remote
HEAD OID you independently checked; the first helper refuses a changed remote,
verifies the complete candidate inventory/provenance, and pushes only
`release/v1.0.21` (never `main`):

```powershell
$remote = "https://github.com/unn0wn002/solo-suite.git"
$expectedRemoteHead = "<reviewed 40-hex remote HEAD OID>"
$result = & .\release\prepare-release-branch-v1.0.21.ps1 `
  -RemoteUrl $remote `
  -ExpectedRemoteHead $expectedRemoteHead `
  -ReleaseZip .\dist\solo-suite-plugin-v1.0.21.zip `
  -Sha256Sums .\dist\SHA256SUMS `
  -Provenance .\dist\provenance.json
$result
```

Review the pushed branch and its PR. Only after approving the exact
`APPROVED_COMMIT_OID=<40-hex>` printed above, create the annotated tag with the
second helper:

```powershell
& .\release\publish-approved-tag-v1.0.21.ps1 `
  -RemoteUrl $remote `
  -ApprovedCommitOid "<approved 40-hex OID>"
```

That helper requires `release/v1.0.21` still to equal the approved OID and
refuses an existing tag. The tag triggers the canonical CI rebuild; the local
candidate is not the canonical published artifact. Neither helper merges or
pushes `main`.

Right after cutting a release, regenerate the drift-guard snapshot from the
pristine canonical release tree:

```
python3 release/gen_release_inventory.py --root <extracted-release> \
    --out release/previous-release-inventory.json
```
