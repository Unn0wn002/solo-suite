# solo-suite patch — C1–C3 (2026-07-09)

## C1 — Deploy-gate ordering (flow)
`plugins/solo/commands/full-team-dev.md`
Before: preflight → **before-deploy** → deploy-plan → rollback-plan
After:  preflight → deploy-plan → rollback-plan → site-doctor:monitoring → **before-deploy**
Why: /gate:before-deploy blocks on a rollback plan in .solo/release.md and live
monitoring in .solo/monitoring.md; the old order guaranteed NO-GO on a clean first pass.

## C2 — Same ordering in the room templates
`plugins/ai/skills/agent-room-templates/agentsrooms/production-release.json`
`plugins/ai/skills/agent-room-templates/agentsrooms/full-team-website.json`
Release seat command order fixed identically; deliverables updated to name the
monitoring record and the GO verdict. NOTE: /gate:before-merge intentionally left
in the full-team-website release seat — relocating it to the reviewer stage is C4.

## C3 — Monitoring wired in
/site-doctor:monitoring inserted before the deploy gate in the flow and in both
rooms' release seats; `.solo/monitoring.md` added to those seats' `writes`
(previously the gatekeeper read a file no seat produced). One writer, one reader.

## Version bumps
solo 1.4.0 → 1.4.1 · ai 1.2.0 → 1.2.1

## Verified after patch
- Both room JSONs parse; gate is the last deploy-phase command in each
- monitoring.md: exactly one writer (release), gatekeeper still reads it
- One-writer-per-artifact-per-stage invariant holds in both rooms
- All slash refs in edited files resolve
- self_check.py: 8 pass / 0 warn / 0 fail

## Still open (from the audit)
C4 git wiring + before-merge seat move · C5 missing commands · C6 security
fallbacks · C7 script paths · H1–H7 · N1–N9
