---
name: security-review
description: Deep application security review going well beyond header checks — OWASP Top 10 coverage — injection (SQL/NoSQL/command), broken auth and session handling, access control and IDOR, XSS, SSRF, insecure deserialization, secrets exposure, dependency CVEs, CSRF, and security misconfiguration. Use whenever the user wants a real security audit, pentest-style review, vulnerability assessment, "is my site secure", pre-launch security sign-off, or asks about a specific vuln class (XSS, SQLi, SSRF, auth bypass). Complements the lighter checks in website-audit.
---

# Security Review

This is a code-and-behavior security review, not a checklist skim. Findings must be **exploitable-specific**: name the file/line or request, describe the attack, and give the fix. "Consider validating input" is not a finding — "line 42 concatenates `req.query.id` into a SQL string, so `?id=1 OR 1=1` dumps the table" is.

## Scope and rules of engagement

- **Only test systems the user owns or is explicitly authorized to test.** Active exploitation of third-party systems is off-limits — decline and offer a code review instead.
- Prefer reading the codebase for causes; use safe, non-destructive probes against the running app to confirm. Never run destructive payloads (no `DROP`, no data exfil beyond proof, no DoS).
- Static analysis first (grep the patterns below), then targeted dynamic confirmation of anything static analysis flags.

## Run the secret scanner first

```bash
python3 scripts/scan_secrets.py /path/to/repo
```
Stdlib-only. Flags likely hardcoded credentials, API keys, private keys, and tokens across the tree. Manually verify each hit (some are placeholders/tests) before reporting.

## OWASP Top 10 walkthrough

Work these in order. For each, the pattern to grep, what confirms it, and the fix direction.

### A01 Broken Access Control (usually the highest-impact class)
- **IDOR**: does an endpoint take an object ID and return it without checking the ID belongs to the caller? Grep routes for `params.id`/`req.params` feeding a DB fetch with no ownership `WHERE user_id = session.user`. Confirm by requesting another user's object ID with your own session.
- **Missing function-level auth**: admin routes reachable without a role check; auth enforced in the UI but not the API. Test admin endpoints directly with a normal-user token.
- **Path traversal**: user input in file paths (`../../etc/passwd`) — grep for `readFile`/`open`/`sendFile` with concatenated user input.
- Fix direction: enforce authorization server-side on every request, deny-by-default, check ownership not just authentication.

### A02 Cryptographic Failures
- Passwords hashed with bcrypt/argon2/scrypt — **not** MD5/SHA1/SHA256-plain. Grep for `md5(`, `sha1(`, `createHash`.
- Sensitive data (PII, tokens) encrypted at rest; TLS enforced in transit; no secrets in logs.
- No hardcoded keys (the scanner covers this); keys support rotation (envelope encryption with a versioned KEK — matches a KMS-backed design).

### A03 Injection
- **SQL/NoSQL**: string-built queries. Grep `"SELECT ... " +`, f-strings/template literals inside `query(...)`, Mongo `$where` with user input. Fix: parameterized queries / prepared statements everywhere — no exceptions for "internal" values.
- **Command injection**: `exec`, `execSync`, `os.system`, `subprocess` with `shell=True` and user input. Fix: avoid the shell, pass argument arrays, allowlist.
- **Template injection (SSTI)**: user input rendered as a template. **XSS**: covered in A03's client cousin below.

### A03/Client XSS
- Reflected/stored/DOM. Grep for `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `document.write`, `eval`, jQuery `.html()` with dynamic data.
- Fix: contextual output encoding, framework auto-escaping (don't bypass it), a strict `Content-Security-Policy` as defense-in-depth (see the CSP recipe in website-fix). Sanitize rich HTML with a vetted library (DOMPurify), never a regex.

### A04 Insecure Design
Threat-model the sensitive flows: is there rate limiting on login/password-reset/OTP? Account enumeration via different error messages or timing? Business-logic abuse (negative quantities, price tampering, replaying idempotent operations)? These aren't single lines — they're missing controls.

### A05 Security Misconfiguration
- Debug mode / verbose errors in production; default credentials; directory listing enabled; unnecessary services exposed.
- Security headers and exposed `.env`/`.git` — the `website-audit` header script covers these; fold its results in here.
- CORS: `Access-Control-Allow-Origin` reflecting arbitrary origins, or `*` combined with credentials.

### A06 Vulnerable & Outdated Components
```bash
npm audit --production        # or: yarn npm audit
pip-audit                     # Python
```
Triage by reachability and severity — a critical CVE in a transitively-included-but-unused package is lower priority than a high in your request path. Check the lockfile is committed and majors aren't years behind.

### A07 Identification & Authentication Failures
- Session tokens: httpOnly + Secure + SameSite cookies, or properly stored JWTs (not in localStorage if XSS is a risk). Session fixation (rotate session ID on login). Logout actually invalidates server-side.
- Password policy sane; credential stuffing defended (rate limit + lockout/backoff); MFA available for sensitive accounts; reset tokens single-use, expiring, and unguessable.

### A08 Software & Data Integrity Failures
- Insecure deserialization: `pickle.loads`, PHP `unserialize`, Java native deserialization on untrusted input. Grep and fix by using safe formats (JSON) or signed payloads.
- Unsigned/unverified auto-update or CI artifacts; dependency confusion risk (private packages resolvable from public registries).

### A09 Security Logging & Monitoring Failures
- Are auth events, access-control failures, and input-validation failures logged? Are secrets/PII kept **out** of logs? Is there anything that would detect an attack in progress? (Hands off to the **observability** skill for building this out.)

### A10 Server-Side Request Forgery (SSRF)
- User-controlled URLs passed to server-side fetchers (webhooks, "import from URL", image proxies, PDF renderers). Grep for `fetch`/`requests.get`/`curl` with user input in the URL.
- Confirm it can reach internal addresses (cloud metadata `169.254.169.254`, `localhost`, private ranges). Fix: allowlist destinations, block private/link-local IPs after DNS resolution, disable redirects to internal hosts.

## Report format

Use the shared audit report structure (Summary → Scorecard → Findings → Fix order), with two additions per finding: **OWASP category** (A01–A10) and a **proof/repro** line (the request or code path that demonstrates it, kept non-destructive). Rank strictly by real exploitability and blast radius. Route remediation through **website-fix** / **database-fix**; rotate any exposed secret immediately (blocking a path doesn't unleak a key).

## Project memory integration (solo-team)

If a `.solo/` directory exists at the project root — the solo-team suite's shared memory — read `handoff.md` and `tasks.md` for context before starting, so the work is grounded in the project's actual state. Afterward, persist the results: capture the prioritized fix list as tasks in `.solo/tasks.md` (stable T-IDs, Doing/Todo/Blocked/Done sections, per project-memory-manager's conventions), append significant findings, decisions, or accepted risks to `.solo/decisions.md`, and note what was run in `handoff.md`. This keeps results in persistent project memory instead of dying with the session, and lets `/solo:next-step` and `/release:preflight` see them. If `.solo/` doesn't exist, proceed normally (and optionally mention the solo plugin can add cross-session memory).

## Session lifecycle

This skill works inside a session that the solo plugin bookends: `/solo:start-session` restores project context at the start (reading `.solo/`), and `/solo:end-session` saves progress, blockers, decisions, and the next task at the end. `/solo:run-cycle` may invoke this skill as one step of a complete task cycle (select → design → implement → review → test → audit → document → save). The read-before / update-after memory behavior described above is exactly what makes those session boundaries work — keep `.solo/` current as you go so start-session and end-session stay accurate.

## Stack awareness

Before auditing or building, read `.solo/stack.md` if it exists — it records the project's actual tools (hosting, DNS/CDN/WAF, database, auth, storage, analytics/tags, email, payments, repo/CI), captured by `/stack:intake`. Tailor the work to the real stack instead of giving generic advice (e.g. don't suggest an S3 lifecycle rule to a Cloudinary project, or a generic WAF to a site already on Cloudflare). If `stack.md` is missing and the stack matters here, suggest running `/stack:intake` first. For vendor-specific depth, the stack plugin adds `/stack:audit-cloudflare`, `-vercel`, `-supabase`, `-tags`, and `-payments`.
