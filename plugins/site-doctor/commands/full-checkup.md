---
description: Full-stack checkup - audit the website AND its database, one combined report
argument-hint: "[site url] [db connection or file]"
---
Run a complete health check on: $ARGUMENTS

1. Use the website-audit skill on the site.
2. Use the database-audit skill on the database.
3. Merge both into one combined report with a single prioritized fix list
   across the whole stack (Critical security first, regardless of layer).
4. Offer to execute the fix list with the website-fix and database-fix skills.

## Output — evidence-based, scored
Never just "good" or "bad" — every finding names its proof (file, config, page, command output, screenshot, or connector data). After the audit, always write:
- **Status** — PASS / WARNING / FAIL
- **Site health score** — n/100 with a per-area breakdown (site, database, security, SEO, performance, accessibility, mobile, forms, analytics)
- **Evidence checked** — what was actually inspected, per area; "not checked" where nothing was
- **Critical findings**
- **High findings**
- **Medium findings**
- **Low findings**
- **Fix order**
- **Owner role** (which team-role/plugin owns each fix)
- **Suggested `.solo/tasks.md` entries** (stable T-IDs)
- **Whether release is blocked**
- **Next command** — the exact next slash command
