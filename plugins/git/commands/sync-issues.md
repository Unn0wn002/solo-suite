---
description: Convert .solo/tasks.md into GitHub issues, or sync issue status back.
argument-hint: [optional: push | pull]
---
Use the **git-workflow-manager** skill in sync-issues mode with **connector-auditor** for GitHub. $ARGUMENTS

Map `.solo/tasks.md` T-IDs to GitHub issues (one issue per T-ID, T-ID kept in the title/body for idempotency) and/or pull issue status back. Show a would-create / would-update / would-close diff and confirm before writing anything.

## Output
End with the 7-part contract: **Summary · Findings/Work done · Risks · Required fixes · Suggested tasks** (→ `.solo/tasks.md`, stable T-IDs) **· Verification · Next command** (exact slash command).
