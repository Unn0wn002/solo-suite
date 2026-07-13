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


# SPF mechanisms that each cost one DNS lookup (RFC 7208 §4.6.4); bare `a`
# and `mx` count too. `include:` and `redirect=` recurse into the referenced
# domain's OWN SPF record, so nested lookups are counted, with cycle
# protection and a hard recursion cap.
SPF_LOOKUP_RE = __import__("re").compile(
    r"(?:^|\s)[+\-~?]?(include|redirect|exists|ptr|a|mx)(?=[:=/]|\s|$)",
    __import__("re").I)


def spf_record_for(domain):
    txts = dns_query(domain, "TXT")
    recs = [t for t in txts if t.lower().startswith("v=spf1")]
    return recs[0] if recs else None


def count_spf_lookups(domain, spf, _stack=None, _depth=0, _memo=None):
    """Return (total_lookups, capped). RFC 7208 counts every EVALUATION of a
    lookup-costing mechanism — so a branch referenced from two different
    includes counts BOTH times (only a true cycle, i.e. a domain already on
    the current recursion STACK, stops). capped=True means some part could
    not be resolved (cycle/depth/missing record/macro), so the count is a
    floor, never a proof of compliance."""
    if _stack is None:
        _stack = []
    if _memo is None:
        _memo = {}
    if _depth > 20:
        return 0, True
    total, capped = 0, False
    for m in SPF_LOOKUP_RE.finditer(spf or ""):
        mech = m.group(1).lower()
        total += 1
        if mech in ("include", "redirect"):
            rest = spf[m.end():]
            target = rest[1:].split()[0].strip() if rest[:1] in (":", "=") else ""
            target = target.strip('"')
            if not target or "%" in target:   # macros — cannot resolve statically
                capped = True
                continue
            key = target.lower()
            if key in _stack:
                capped = True                  # true cycle — floor only
                continue
            if key in _memo:                   # repeated branch: SAME cost again
                sub, sub_capped = _memo[key]
            else:
                nested = spf_record_for(target)
                if nested is None:
                    capped = True
                    continue
                sub, sub_capped = count_spf_lookups(
                    target, nested, _stack + [key], _depth + 1, _memo)
                _memo[key] = (sub, sub_capped)
            total += sub
            capped = capped or sub_capped
    return total, capped


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
    lookups, capped = count_spf_lookups(domain, spf)
    approx = "at least " if capped else ""
    if lookups > 10:
        report("FAIL", f"{approx}{lookups} DNS-lookup mechanisms including "
                       "nested includes — exceeds the SPF 10-lookup limit "
                       "and will break; flatten includes")
    elif lookups >= 8:
        report("WARN", f"{approx}{lookups} DNS-lookup mechanisms including "
                       "nested includes — close to the 10-lookup limit")
    elif capped:
        report("WARN", f"at least {lookups} DNS-lookup mechanisms, but the "
                       "count is INCOMPLETE (unresolvable include/redirect, "
                       "macro, or cycle) — cannot confirm the 10-lookup "
                       "limit; never treat this as a pass")
    else:
        report("PASS", f"{lookups} DNS-lookup mechanism(s) incl. nested "
                       "includes (limit 10)")
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
    # Exact tag=value parsing (RFC 7489): sp= must never masquerade as p=.
    tags = {}
    for part in d.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        tags.setdefault(k.strip().lower(), v.strip())
    policy = tags.get("p", "").lower()
    if policy == "reject":
        report("PASS", "policy p=reject — strongest (failures blocked)")
    elif policy == "quarantine":
        report("WARN", "policy p=quarantine — good; consider p=reject when ready")
    elif policy == "none":
        report("WARN", "policy p=none — MONITOR ONLY, no protection. "
                       "Progress to quarantine then reject.")
    elif not policy:
        report("FAIL", "DMARC record has no base 'p=' policy tag — receivers "
                       "treat it as invalid")
    else:
        report("FAIL", f"DMARC 'p={policy}' is not a valid policy "
                       "(none/quarantine/reject)")
    sp = tags.get("sp", "").lower()
    if sp:
        report("PASS" if sp == "reject" else "WARN",
               f"subdomain policy sp={sp} (applies to SUBDOMAINS only — "
               "it does not strengthen the base p= policy)")
    if "rua" not in tags:
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
