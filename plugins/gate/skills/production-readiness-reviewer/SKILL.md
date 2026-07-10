---
name: production-readiness-reviewer
description: Score whether an app is actually ready for real users across product, design, backend, frontend, security, testing, performance, SEO, analytics, deployment, monitoring, and docs. Use when the user says production ready, launch readiness, "is it ready to ship", go-live checklist, or preflight. Produces per-section scores and an overall BLOCKED / SAFE TO LAUNCH / LAUNCH WITH WARNINGS verdict where any critical failure forces BLOCKED.
---

# Production Readiness Reviewer

Answers one question honestly: **is this safe to put in front of real users?** It runs a fixed checklist, scores each section, and gives an overall verdict — but a **critical failure overrides the average**: secrets committed, no auth where auth is required, Supabase RLS off where it's needed, or no backup/rollback each force **BLOCKED** no matter how good everything else looks. Pull real signals from `.solo/` and the specialist plugins (don't assume an item passes just because it exists in the plan).

## The checklist

### Product
- PRD exists
- MVP scope is clear
- User stories have acceptance criteria
- Non-goals are listed

### Design
- Core user flows documented
- Mobile states designed
- Empty/loading/error states handled
- Component system exists

### Backend
- API validation exists
- Auth required where needed
- Authorization enforced server-side
- Database constraints exist
- Errors are handled safely

### Frontend
- Responsive layout works
- Forms have validation
- Loading/error/empty states exist
- No console errors
- Accessibility basics pass

### Security
- No secrets committed
- Env vars separated by environment
- Supabase RLS enabled where needed
- Dependencies audited
- OWASP Top 10 reviewed

### Testing
- Unit tests for business logic
- Integration tests for API/database
- E2E tests for core flows
- Edge cases reviewed

### Performance
- Core Web Vitals measured or estimated against targets (LCP/INP/CLS) — `/site-doctor:perf`
- Images optimized and sized correctly
- Compression and caching headers on
- No obvious N+1 or unindexed hot queries

### SEO
- Pages indexable (no stray noindex; robots.txt sane) — `/site-doctor:seo`
- Titles and meta descriptions on key pages
- Sitemap exists and is reachable
- Canonical and social/OG tags on shareable pages

### Analytics
- Analytics firing once per page view (no double-count) — `/stack:audit-tags`
- Core funnel conversions tracked end-to-end — `/site-doctor:audit-analytics`
- Consent gating verified where required
- No PII in analytics parameters

### Deployment
- Vercel env vars checked
- Preview and production separated
- Cloudflare SSL/DNS checked
- Rollback plan exists
- Backup/restore plan exists

### Monitoring
- Error tracking exists
- Uptime check exists
- Logs are searchable
- Alerts are not too noisy

### Docs
- README updated
- Setup guide works
- API docs exist
- Env vars documented

## Scoring
Score twelve categories, each **0–10**, judged from the checklist evidence above (never from vibes — every score cites what was checked):

Product · Architecture · Frontend · Backend · Database · Security · Performance · SEO · Analytics · Deployment · Monitoring · Docs

**Overall score = round(sum ÷ 120 × 100) out of 100.** Present it exactly like:

```
Production Readiness Score: 86/100

Product: 9/10
Architecture: 8/10
Frontend: 8/10
Backend: 9/10
Database: 7/10
Security: 8/10
Performance: 8/10
SEO: 9/10
Analytics: 6/10
Deployment: 9/10
Monitoring: 7/10
Docs: 8/10

Launch Status: LAUNCH WITH WARNINGS
```

## Launch status & hard blockers

**Launch is BLOCKED — regardless of score — if ANY of these is true:**
- SEO basics missing (indexable, titles/descriptions, sitemap/robots)
- analytics missing (no measurement of the core funnel)
- error tracking missing
- mobile broken (fails `/browser:mobile-test` at 320/375/768)
- serious accessibility issues (blocking WCAG failures on core flows)
- auth, Supabase RLS, payments, or transactional email **not verified** (claimed ≠ verified — each needs test evidence)
- plus the structural criticals: secrets committed · no auth where needed · RLS off where needed · no backup/rollback

Otherwise: **SAFE TO LAUNCH** when score ≥ 85 and no category below 7; **LAUNCH WITH WARNINGS** when score ≥ 70 with every warning listed and accepted. Below 70 → **BLOCKED** with the ordered must-fix list to get out.

## Working with other skills
Powers `/gate:production-ready` (the full gate) and `/gate:score-project` (checklist + scoring only, no launch verdict), and feeds `/release:preflight`. Delegates evidence-gathering to `security`, `test`, `browser`, `docs`, `release`, `site-doctor`, and the `/stack:audit-*` skills.

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
