#!/usr/bin/env python3
"""scan_secrets.py — scan a codebase for likely hardcoded secrets:
API keys, private keys, tokens, passwords, and cloud credentials.

Stdlib only. Usage:
    python3 scan_secrets.py /path/to/repo [--max-bytes 2000000]

Findings are HEURISTIC. Every hit must be verified by a human — test
fixtures, examples, and placeholders will match. Exit 1 if any hits.
"""
import sys
import os
import re
import argparse

# Directories and files never worth scanning
SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", ".next",
             "__pycache__", ".venv", "venv", "coverage", ".cache"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
            ".pdf", ".zip", ".gz", ".tar", ".mp4", ".woff", ".woff2",
            ".ttf", ".eot", ".lock", ".min.js", ".map"}

# (label, compiled regex). Ordered specific -> generic.
PATTERNS = [
    ("AWS Access Key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS Secret Access Key", re.compile(r"(?i)aws.{0,20}?['\"][0-9a-zA-Z/+]{40}['\"]")),
    ("Private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"gh[pousr]_[0-9A-Za-z]{36,}")),
    ("Slack token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("Stripe live key", re.compile(r"sk_live_[0-9a-zA-Z]{20,}")),
    ("Xendit secret key", re.compile(r"xnd_(?:development|production)_[0-9A-Za-z]{20,}")),
    ("Midtrans server key", re.compile(r"(?:SB-)?Mid-server-[0-9A-Za-z_\-]{16,}")),
    ("SendGrid key", re.compile(r"SG\.[0-9A-Za-z_\-]{20,}\.[0-9A-Za-z_\-]{20,}")),
    ("Resend key", re.compile(r"\bre_[0-9A-Za-z]{16,}")),
    ("Supabase access token", re.compile(r"sbp_[0-9a-f]{40}")),
    ("Supabase secret key", re.compile(r"sb_secret_[0-9A-Za-z_\-]{20,}")),
    ("Vercel token assignment", re.compile(r"(?i)vercel.{0,15}['\"][0-9A-Za-z]{24}['\"]")),
    ("Cloudflare API token assignment", re.compile(r"(?i)cloudflare.{0,20}['\"][0-9A-Za-z_\-]{40}['\"]")),
    ("OpenAI key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("Generic API key assignment", re.compile(
        r"(?i)(api[_-]?key|apikey|access[_-]?token|auth[_-]?token|client[_-]?secret)"
        r"\s*[:=]\s*['\"][0-9a-zA-Z_\-]{16,}['\"]")),
    ("Hardcoded password assignment", re.compile(
        r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{6,}['\"]")),
    ("Connection string with creds", re.compile(
        r"(?i)(postgres|postgresql|mysql|mongodb(?:\+srv)?|redis|amqp)://"
        r"[^:@\s'\"]+:[^@\s'\"]+@")),
    ("Private key file ref", re.compile(r"(?i)-----BEGIN")),
]

# Lines that look like placeholders — downgrade to a note, don't suppress
PLACEHOLDER = re.compile(
    r"(?i)(your[_-]?|example|placeholder|dummy|test|sample|xxxx|<[^>]+>|"
    r"changeme|redacted|\bfoo\b|\bbar\b|000000000000|1234567890)")

hits = []


def scan_file(path):
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            for lineno, line in enumerate(fh, 1):
                if len(line) > 2000:
                    continue  # minified / data line
                for label, rx in PATTERNS:
                    if rx.search(line):
                        snippet = line.strip()[:120]
                        note = "  (looks like a placeholder — verify)" \
                            if PLACEHOLDER.search(snippet) else ""
                        hits.append((path, lineno, label, snippet, note))
                        break  # one label per line is enough
    except (OSError, UnicodeError):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--max-bytes", type=int, default=2_000_000)
    args = ap.parse_args()
    global MAX_BYTES
    MAX_BYTES = args.max_bytes

    if not os.path.exists(args.root):
        print(f"Path not found: {args.root}"); return 2

    scanned = 0
    for dirpath, dirnames, filenames in os.walk(args.root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if any(name.endswith(e) for e in SKIP_EXT):
                continue
            scan_file(os.path.join(dirpath, name))
            scanned += 1

    print(f"Scanned {scanned} files under {args.root}\n")
    if not hits:
        print("No obvious hardcoded secrets found.")
        print("(Absence of matches is not proof of safety — review auth "
              "and config handling manually too.)")
        return 0

    print(f"POTENTIAL SECRETS ({len(hits)}) — verify each before acting:\n")
    for path, lineno, label, snippet, note in hits:
        rel = os.path.relpath(path, args.root)
        print(f"  [{label}]{note}")
        print(f"    {rel}:{lineno}")
        print(f"    {snippet}\n")
    print("If any real secret was ever committed, ROTATE it — git history "
          "keeps it even after deletion.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
