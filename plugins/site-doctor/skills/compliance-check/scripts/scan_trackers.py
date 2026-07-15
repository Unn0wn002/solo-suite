#!/usr/bin/env python3
"""scan_trackers.py — fetch a page and surface cookies set and third-party
tracker/script origins, to support a privacy/consent compliance review.

Stdlib only. Outbound requests go through lib/url_guard.py (SSRF guard) —
private/internal/metadata targets and unsafe redirects are refused with a
BLOCKED result. Usage:
    python3 scan_trackers.py https://example.com

This is a FLOOR, not a ceiling: it sees server-set cookies and static
third-party references in the initial HTML. Client-set cookies and tags
injected by JavaScript need a real browser (or consent-mode testing) to
catch fully.

Exit codes: 0 = no known trackers statically; 1 = trackers fire with no
consent tool detected (FAIL); 2 = usage/unreachable/HTTP error; 3 = coverage
UNVERIFIED (non-HTML, empty, truncated, unparsable, or trackers plus a CMP
whose consent gating needs a real browser).
"""
import os
import sys
import re
from urllib.parse import urlparse
from html.parser import HTMLParser

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib")))
try:
    from url_guard import safe_get, BlockedUrlError
except ImportError:
    sys.exit("url_guard.py not found — run from an intact site-doctor plugin")

UA = "Mozilla/5.0 (compatible; site-doctor-privacy/1.0)"
TIMEOUT = 15
MAX_BYTES = 2 * 1024 * 1024  # response read cap

# Known tracker/ad/analytics host fragments -> friendly label
KNOWN_TRACKERS = {
    "google-analytics.com": "Google Analytics",
    "googletagmanager.com": "Google Tag Manager",
    "analytics.google.com": "Google Analytics 4",
    "doubleclick.net": "Google Ads / DoubleClick",
    "googlesyndication.com": "Google AdSense",
    "googleadservices.com": "Google Ads",
    "connect.facebook.net": "Meta (Facebook) Pixel",
    "facebook.com/tr": "Meta Pixel",
    "hotjar.com": "Hotjar",
    "clarity.ms": "Microsoft Clarity",
    "segment.com": "Segment",
    "segment.io": "Segment",
    "mixpanel.com": "Mixpanel",
    "amplitude.com": "Amplitude",
    "fullstory.com": "FullStory",
    "mouseflow.com": "Mouseflow",
    "linkedin.com/px": "LinkedIn Insight",
    "snap.licdn.com": "LinkedIn Insight",
    "ads-twitter.com": "X (Twitter) Ads",
    "static.ads-twitter.com": "X Ads",
    "tiktok.com": "TikTok Pixel",
    "bing.com": "Microsoft/Bing Ads",
    "bat.bing.com": "Bing Ads",
    "cdn.segment": "Segment",
    "intercom.io": "Intercom",
    "hs-scripts.com": "HubSpot",
    "hubspot.com": "HubSpot",
    "cookiebot.com": "Cookiebot (CMP)",
    "onetrust.com": "OneTrust (CMP)",
    "cookielaw.org": "OneTrust (CMP)",
    "usercentrics": "Usercentrics (CMP)",
    "klaviyo.com": "Klaviyo",
    "matomo": "Matomo",
    "plausible.io": "Plausible (privacy-friendly)",
    "cloudflareinsights.com": "Cloudflare Web Analytics",
}


class SrcParser(HTMLParser):
    """Collects each referenced resource URL exactly once (deduplicated) —
    an <img> src is not counted twice, and repeated references to the same
    URL don't inflate tracker counts."""
    def __init__(self):
        super().__init__()
        self.srcs = []
        self._seen = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for attr in ("src", "href"):
            u = a.get(attr)
            if u and u not in self._seen:
                self._seen.add(u)
                self.srcs.append(u)


def fetch(url):
    try:
        r = safe_get(url, timeout=TIMEOUT, allow_http=True, max_bytes=MAX_BYTES,
                     headers={"User-Agent": UA})
        get_all = getattr(r.headers, "get_all", None)
        cookies = get_all("Set-Cookie") or [] if callable(get_all) else []
        final_url = getattr(r, "url", url)
        if not same_audit_origin(url, final_url, allow_http_upgrade=True):
            return (r.status, cookies, "",
                    "redirected to unrelated origin %s" % final_url,
                    final_url)
        if not 200 <= r.status < 300:
            return r.status, cookies, "", "HTTP %s" % r.status, final_url
        if r.truncated:
            return (r.status, cookies, "",
                    "response exceeded the %d-byte scan limit" % MAX_BYTES,
                    final_url)
        content_type = r.headers.get("Content-Type", "")
        ctype = content_type.split(";", 1)[0].strip().lower()
        if ctype not in ("text/html", "application/xhtml+xml"):
            return (r.status, cookies, "",
                    "response Content-Type %r is not HTML" %
                    (ctype or "(missing)"), final_url)
        body = r.body or b""
        if not body.strip():
            return (r.status, cookies, "", "HTML response body is empty",
                    final_url)
        charset = "utf-8"
        for parameter in content_type.split(";")[1:]:
            key, separator, value = parameter.partition("=")
            if separator and key.strip().lower() == "charset":
                charset = value.strip().strip('"\'').lower()
                break
        aliases = {"utf-8": "utf-8", "utf8": "utf-8",
                   "us-ascii": "ascii", "ascii": "ascii"}
        codec = aliases.get(charset)
        if codec is None:
            return (r.status, cookies, "",
                    "unsupported HTML charset %r" % charset, final_url)
        try:
            html = body.decode(codec, "strict")
        except UnicodeDecodeError:
            return (r.status, cookies, "",
                    "HTML body is not valid %s" % charset, final_url)
        return r.status, cookies, html, None, final_url
    except BlockedUrlError as e:
        print(f"BLOCKED unsafe target: {e}")
        return None, [], "", "blocked unsafe target", None
    except Exception as e:
        print(f"Could not fetch {url}: {e}")
        return None, [], "", "request failed", None


def normalized_hostname(value):
    """Return a structural lower-case hostname for a URL or netloc."""
    try:
        parsed = urlparse(value if "://" in value else "//" + value)
        host = parsed.hostname
        if not host:
            return None
        return host.rstrip(".").encode("idna").decode("ascii").lower()
    except (UnicodeError, ValueError):
        return None


def same_site_url(left, right):
    """Accept only the same hostname or its explicit www variant."""
    a, b = normalized_hostname(left), normalized_hostname(right)
    if not a or not b:
        return False
    strip_www = lambda host: host[4:] if host.startswith("www.") else host
    return strip_www(a) == strip_www(b)


def same_audit_origin(left, right, allow_http_upgrade=False):
    """Bind evidence to a host and effective port, with optional HTTPS upgrade."""
    try:
        a, b = urlparse(left), urlparse(right)
        a_port = a.port or (443 if a.scheme.lower() == "https" else 80)
        b_port = b.port or (443 if b.scheme.lower() == "https" else 80)
    except ValueError:
        return False
    if not same_site_url(left, right):
        return False
    if a.scheme.lower() == b.scheme.lower():
        return a_port == b_port
    return bool(allow_http_upgrade and a.scheme.lower() == "http" and
                b.scheme.lower() == "https" and a_port == 80 and b_port == 443)


def main(url):
    status, cookies, html, problem, final_url = fetch(url)
    if status is None:
        print("RESULT: pass=0 warn=0 fail=0 unverified=1")
        return 2
    print(f"=== Privacy/tracker scan: {url} (status {status}) ===\n")
    if problem:
        http_error = not 200 <= status < 300
        level = "ERROR" if http_error else "UNVERIFIED"
        print(f"[{level}] {problem}; tracker coverage is not a pass")
        print("RESULT: pass=0 warn=0 fail=0 unverified=1")
        return 2 if http_error else 3

    # --- cookies set on initial load ---
    print("Cookies set by the server on load "
          "(these fire BEFORE any consent interaction):")
    if not cookies:
        print("  (none set via response headers — client JS may still set some)")
    for c in cookies:
        # Structural parse: first segment is name=value; the rest are
        # attributes. Substring matching would false-positive on cookie
        # VALUES containing e.g. "secure".
        segments = [seg.strip() for seg in c.split(";")]
        name = segments[0].split("=", 1)[0].strip()
        attrs = {}
        for seg in segments[1:]:
            k, _, v = seg.partition("=")
            attrs[k.strip().lower()] = v.strip()
        flags = [f for f in ("secure", "httponly", "samesite") if f in attrs]
        if "samesite" in attrs and attrs["samesite"]:
            flags[flags.index("samesite")] = f"samesite={attrs['samesite'].lower()}"
        if "max-age" in attrs and attrs["max-age"].lstrip("-").isdigit():
            life = f"max-age={attrs['max-age']}s"
        elif "expires" in attrs:
            life = f"expires={attrs['expires']}"
        else:
            life = "session"
        print(f"  - {name}  [{', '.join(flags) or 'no flags'}]  {life}")
    print()

    # --- third-party origins & known trackers ---
    p = SrcParser()
    try:
        p.feed(html)
        p.close()
    except Exception as e:
        print(f"[UNVERIFIED] HTML parser failed: {e}; tracker coverage is "
              "not a pass")
        print("RESULT: pass=0 warn=0 fail=0 unverified=1")
        return 3

    third_party = {}
    trackers_found = {}
    for src in p.srcs:
        if src.startswith("//"):
            src = "https:" + src
        netloc = urlparse(src).netloc
        src_host = normalized_hostname(netloc) if netloc else None
        if not src_host or same_audit_origin(final_url, src):
            continue
        third_party.setdefault(netloc, 0)
        third_party[netloc] += 1
        for frag, label in KNOWN_TRACKERS.items():
            if frag in src.lower():
                trackers_found[label] = trackers_found.get(label, 0) + 1

    print("Known trackers / analytics / ad tech detected in initial HTML:")
    if not trackers_found:
        print("  (none detected statically — JS-injected tags need a browser to confirm)")
    for label, n in sorted(trackers_found.items(), key=lambda x: -x[1]):
        cmp_note = "  <- consent tool (good sign)" if "CMP" in label else ""
        print(f"  - {label}  (x{n}){cmp_note}")
    print()

    print("All third-party origins referenced on load "
          "(each may receive user data such as IP/behavior):")
    for netloc, n in sorted(third_party.items(), key=lambda x: -x[1])[:30]:
        print(f"  - {netloc}  (x{n})")
    print()

    # ---- structured verdict -------------------------------------------------
    cmp_present = any("CMP" in label for label in trackers_found)
    hard_trackers = {l: n for l, n in trackers_found.items() if "CMP" not in l}
    if hard_trackers and not cmp_present:
        print(f"[FAIL] {len(hard_trackers)} tracker(s) load in the initial "
              "HTML with NO consent tool detected - classic GDPR/ePrivacy gap")
        verdict = 1
    elif hard_trackers:
        print(f"[UNVERIFIED] {len(hard_trackers)} tracker(s) plus a consent "
              "tool detected - whether the CMP actually GATES them needs a "
              "real browser with consent unaccepted")
        verdict = 3
    else:
        print("[PASS] no known trackers in the initial HTML "
              "(JS-injected tags still need a browser check)")
        verdict = 0
    print(f"RESULT: pass={0 if hard_trackers else 1} warn={len(third_party)} "
          f"fail={1 if (hard_trackers and not cmp_present) else 0} "
          f"unverified={1 if (hard_trackers and cmp_present) else 0}")
    print()
    print("REVIEW GUIDANCE:")
    print("  * Any analytics/ad tracker firing on load without prior consent is")
    print("    the classic GDPR/ePrivacy gap. Confirm whether a consent tool")
    print("    gates them, or whether they fire regardless.")
    print("  * Third-party origins loading before consent can leak user data to")
    print("    those parties (IP, page, behavior). Verify each is disclosed and")
    print("    consent-gated where required.")
    print("  * This is a static floor — run a real browser with the consent")
    print("    banner UNaccepted to see what actually fires pre-consent.")
    return verdict


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
