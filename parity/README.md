# Claude ↔ Codex capability parity

`capabilities.json` is the deterministic parity contract for the Solo Suite
adapter. The Claude checkout is canonical: it owns the 18 plugin IDs, 102
command definitions, 56 specialist skills, shared helper files, and AgentRoom
source files. The Codex checkout is regenerated from that source and is allowed
only the adapter differences declared in the manifest.

Generate the contract after changing the canonical source:

```text
python tools/parity.py generate --source <solo-suite-v1.0.27-release-work>
```

Then check the adapter:

```text
python tools/parity.py --check \
  --source <solo-suite-v1.0.27-release-work> \
  --target <solo-suite-codex-v1.0.11>
```

The checker is standard-library-only and fails closed. It verifies the exact
command-map IDs/paths and explicit-only policy, normalized specialist bodies,
byte hashes for helper/schema files, all 159 Codex `openai.yaml` policies, and
the byte-exact Claude AgentRoom archive under `parity/claude-rooms`.

Two skills are platform adapters rather than byte-identical copies:

* `ai:agent-room-templates` — Codex has a native runner, trust journal, and
  state machinery. The canonical Claude tree is archived for review.
* `solo:suite-integrity` — Codex validates Codex manifests and installed
  plugin metadata, so its implementation is intentionally native.

The only other permitted differences are the Codex-only
`full-team:full-team-orchestrator` skill and the six gate runtime support files
listed in `capabilities.json`. Any additional skill, helper, policy, or archive
file is a parity failure.
