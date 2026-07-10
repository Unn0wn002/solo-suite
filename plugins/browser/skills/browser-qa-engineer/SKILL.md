---
name: browser-qa-engineer
description: Real browser QA — exercise core flows, catch console/network/hydration errors, review layout and responsiveness, test mobile breakpoints, and test forms end to end. Use when the user says smoke test, test in the browser, console errors, visual check, mobile test, responsive, or form testing. Uses a browser automation tool when available; otherwise gives a precise, repeatable manual test script.
---

# Browser QA Engineer

Unit tests pass and the page is still broken. This skill tests what the user actually experiences. **If a browser/automation tool (Playwright, a browser connector) is available, drive it and report real results; if not, produce an exact step-by-step manual script** (URLs, actions, and expected results) the user can run in minutes. Five modes.

**Evidence per finding:** every finding carries a screenshot, a console/network paste, or an exact reproduction step — and manual-mode scripts say what to capture at each step. No evidence, no finding.

## Mode: smoke-test (`/browser:smoke-test`)
Walk the core user journeys happy-path (e.g. load → sign up → log in → do the main thing → sign out). Confirm each step renders and advances. Fail loudly on any dead end, 500, blank screen, or infinite spinner.

## Mode: console-errors (`/browser:console-errors`)
Load key pages and capture the console + network: JS exceptions, uncaught promise rejections, failed requests (4xx/5xx), CORS/CSP violations, framework **hydration mismatches** (SSR), and noisy warnings. Report each with page, message, and likely cause.

## Mode: visual-check (`/browser:visual-check`)
Review layout across the important pages: broken/overlapping elements, spacing/alignment, text overflow and truncation, images not loading or unsized (layout shift), z-index/modal issues, and whether it holds up when the viewport resizes.

## Mode: mobile-test (`/browser:mobile-test`)
Test at **320px, 375px, and 768px**: horizontal overflow/scroll, tap-target size (~44px), readable text, working nav/menus, and no content cut off or hidden behind fixed bars. Note anything desktop-only that breaks on touch.

## Mode: form-submit-test (`/browser:form-submit-test`)
Test each important form end to end: valid submit (does it actually persist / show success?), invalid input (clear, correct validation messages), empty/required fields, boundary values, **network-failure** handling, and double-submit protection. Confirm loading, success, and error states all exist and behave.

## Working with other skills
Findings feed `/dev:fix-bug` and `.solo/tasks.md`. `/gate:before-deploy` and `/gate:production-ready` expect smoke + console + mobile to be clean. Pairs with `/site-doctor:audit-forms` (deeper form/security checks) and `/site-doctor:a11y`.

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

## Stack awareness
Check `.solo/stack.md` first and tailor everything to the real stack. For vendor depth the `/stack:audit-*` skills go further: Cloudflare, Vercel, Supabase, analytics/tags, payments. If a sibling skill or connector isn't installed, do a lighter inline version and say so.
