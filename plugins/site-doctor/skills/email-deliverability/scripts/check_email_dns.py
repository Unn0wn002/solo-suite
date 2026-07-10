#!/usr/bin/env python3
"""check_email_dns.py — query public DNS for a domain's MX, SPF, DMARC, and
(optionally) DKIM records and parse them for common misconfigurations that
hurt email deliverability.

Stdlib only — uses DNS-over-HTTPS so no dnspython needed. Queried names go
to the DoH endpoint (Cloudflare by default; SITE_DOCTOR_DOH overrides it).
Outbound requests are SSRF-guarded by lib/url_guard.py.
Usage:
    python3 check_email_dns.py example.com [--dkim-selector google]

Exit 0 always (informational).
"""
import os
import sys
import json
import argparse
import urllib.parse

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib")))
try:
    from url_guard import safe_get, BlockedUrlError
except ImportError:
    sys.exit("url_guard.py not found — run from an intact site-doctor plugin")

# http is only accepted for an explicit SITE_DOCTOR_DOH override (tests use a
# loopback fixture); the default endpoint stays https-only.
DOH = os.environ.get("SITE_DOCTOR_DOH", "https://cloudflare-dns.com/dns-query")
TIMEOUT = 12
MAX_BYTES = 512 * 1024  # DoH response cap
results = {"PASS": 0, "WARN": 0, "FAIL": 0}


def report(level, msg):
    results[level] += 1
    print(f"  [{level}] {msg}")


def dns_query(name, rrtype):
    """Return list of record strings for name/type via DoH, or []."""
    q = urllib.parse.urlencode({"name": name, "type": rrtype})
    try:
        r = safe_get(DOH + "?" + q, timeout=TIMEOUT, max_bytes=MAX_BYTES,
                     allow_http=bool(os.environ.get("SITE_DOCTOR_DOH")),
                     headers={"accept": "application/dns-json"})
        data = json.loads((r.body or b"").decode())
    except BlockedUrlError as e:
        print(f"    (BLOCKED unsafe DoH endpoint for {rrtype} {name}: {e})")
        return []
    except Exception as e:
        print(f"    (DNS query failed for {rrtype} {name}: {e})")
        return []
    out = []
    for ans in data.get("Answer", []):
        val = ans.get("data", "")
        # TXT records come wrapped in quotes; strip and join chunks
        if rrtype == "TXT":
            val = val.strip()
            if val.startswith('"'):
                val = "".join(p.strip('"') for p in val.split('" "'))
                val = val.strip('"')
        out.append(val)
    return out


def check_mx(domain):
    print("MX (mail servers):")
    mx = dns_query(domain, "MX")
    if mx:
        report("PASS", f"{len(mx)} MX record(s): " + "; ".join(mx[:4]))
    else:
        report("WARN", "no MX records — domain can't RECEIVE mail "
                       "(fine if send-only)")
    print()


def check_spf(domain):
    print("SPF:")
    txts = dns_query(domain, "TXT")
    spfs = [t for t in txts if t.lower().startswith("v=spf1")]
    if not spfs:
        report("FAIL", "no SPF record — sending mail will likely be filtered. "
                       "Add a v=spf1 TXT record listing your senders.")
        print()
        return
    if len(spfs) > 1:
        report("FAIL", f"{len(spfs)} SPF records found — MUST be exactly one "
                       "(multiple SPF records is a hard failure)")
    spf = spfs[0]
    report("PASS", f"SPF present: {spf[:120]}")
    # all mechanism
    if "+all" in spf:
        report("FAIL", "'+all' permits ANYONE to send as you — remove it")
    elif "-all" in spf:
        report("PASS", "ends in '-all' (hardfail) — strongest")
    elif "~all" in spf:
        report("WARN", "ends in '~all' (softfail) — OK; move to '-all' once "
                       "your sender list is confirmed complete")
    else:
        report("WARN", "no 'all' mechanism — add ~all or -all")
    # DNS lookup count (rough): count include/a/mx/ptr/exists/redirect
    import re
    lookups = len(re.findall(r"\b(include|a|mx|ptr|exists|redirect)[:=]", spf))
    if lookups > 10:
        report("FAIL", f"~{lookups} DNS-lookup mechanisms — exceeds the SPF "
                       "10-lookup limit and will break; flatten includes")
    elif lookups >= 8:
        report("WARN", f"~{lookups} DNS-lookup mechanisms — close to the "
                       "10-lookup limit")
    print()


def check_dmarc(domain):
    print("DMARC:")
    recs = dns_query("_dmarc." + domain, "TXT")
    dmarc = [t for t in recs if t.lower().startswith("v=dmarc1")]
    if not dmarc:
        report("FAIL", "no DMARC record at _dmarc." + domain +
               " — add v=DMARC1; start with p=none;rua=... to monitor")
        print()
        return
    d = dmarc[0]
    report("PASS", f"DMARC present: {d}")
    low = d.lower()
    if "p=reject" in low:
        report("PASS", "policy p=reject — strongest (failures blocked)")
    elif "p=quarantine" in low:
        report("WARN", "policy p=quarantine — good; consider p=reject when ready")
    elif "p=none" in low:
        report("WARN", "policy p=none — MONITOR ONLY, no protection. "
                       "Progress to quarantine then reject.")
    if "rua=" not in low:
        report("WARN", "no 'rua=' reporting address — you won't receive "
                       "aggregate reports; add one to see what's failing")
    print()


def check_dkim(domain, selector):
    print("DKIM:")
    if not selector:
        report("WARN", "no --dkim-selector provided — DKIM can't be checked "
                       "without knowing the selector (each ESP uses its own, "
                       "e.g. 'google', 's1', 'k1'). Provide one to verify.")
        print()
        return
    name = f"{selector}._domainkey.{domain}"
    recs = dns_query(name, "TXT")
    dkim = [t for t in recs if "v=dkim1" in t.lower() or "p=" in t.lower()]
    if dkim:
        has_key = any("p=" in t and t.split("p=")[1].strip(' ";')
                      for t in dkim)
        if has_key:
            report("PASS", f"DKIM key found at {name}")
        else:
            report("FAIL", f"DKIM record at {name} has an empty key (p=) — "
                           "the selector may be revoked")
    else:
        report("FAIL", f"no DKIM record at {name} — verify the selector, or "
                       "DKIM isn't set up for this sender")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("domain")
    ap.add_argument("--dkim-selector", default=None)
    args = ap.parse_args()
    d = args.domain.strip().lower().lstrip("@")
    print(f"=== Email DNS check: {d} ===\n")
    check_mx(d)
    check_spf(d)
    check_dmarc(d)
    check_dkim(d, args.dkim_selector)
    print(f"Totals: {results['PASS']} pass, {results['WARN']} warn, "
          f"{results['FAIL']} fail")
    print("\nAuthentication (SPF/DKIM/DMARC) is ~80% of deliverability. Fix "
          "FAILs first. DKIM needs the right selector to verify — check your "
          "ESP's docs for it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
