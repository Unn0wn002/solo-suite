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
catch fully. Exit 0 always (informational).

Exit codes: 0 = no known trackers statically; 1 = trackers fire with no
consent tool detected (FAIL); 2 = usage/unreachable; 3 = trackers plus a
CMP found - consent gating UNVERIFIED without a real browser.
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
        cookies = r.headers.get_all("Set-Cookie") or []
        if r.status >= 400:
            return r.status, cookies, ""
        return r.status, cookies, (r.body or b"").decode("utf-8", "replace")
    except BlockedUrlError as e:
        print(f"BLOCKED unsafe target: {e}")
        return None, [], ""
    except Exception as e:
        print(f"Could not fetch {url}: {e}")
        return None, [], ""


def main(url):
    host = urlparse(url).netloc
    status, cookies, html = fetch(url)
    if status is None:
        return 2
    print(f"=== Privacy/tracker scan: {url} (status {status}) ===\n")

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
    except Exception:
        pass

    third_party = {}
    trackers_found = {}
    for src in p.srcs:
        if src.startswith("//"):
            src = "https:" + src
        netloc = urlparse(src).netloc
        if not netloc or netloc == host:
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
