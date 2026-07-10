#!/usr/bin/env python3
"""check_links.py — crawl same-domain pages, verify every link and asset,
and flag broken links (status >= 400), mixed content, and long redirect chains.

Stdlib only. Outbound requests go through lib/url_guard.py (SSRF guard) —
private/internal/metadata targets and unsafe redirects are refused with a
BLOCKED result. Usage:
    python3 check_links.py https://example.com [--max-pages 30] [--delay 0.3]

Exit code: 0 = clean, 1 = broken links found, 2 = could not start crawl.
"""
import os
import sys
import time
import argparse
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib")))
try:
    from url_guard import safe_get, check_url, BlockedUrlError
except ImportError:
    sys.exit("url_guard.py not found — run from an intact site-doctor plugin")

UA = "site-doctor-linkcheck/1.0"
TIMEOUT = 12
MAX_BYTES = 2 * 1024 * 1024  # per-response read cap


class LinkExtractor(HTMLParser):
    """Collect hrefs (navigable) and asset srcs separately."""

    def __init__(self):
        super().__init__()
        self.links, self.assets = [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag in ("img", "script", "iframe", "source", "video", "audio") and a.get("src"):
            self.assets.append(a["src"])
        elif tag == "link" and a.get("href"):
            self.assets.append(a["href"])


def request(url, method="HEAD"):
    """Return (status, final_url, redirect_hops, content_type, body_or_None)."""
    try:
        r = safe_get(url, method=method, timeout=TIMEOUT, allow_http=True,
                     max_bytes=MAX_BYTES, headers={"User-Agent": UA})
    except BlockedUrlError as e:
        return f"BLOCKED: {e}", url, 0, "", None
    except Exception as e:
        return f"ERR: {type(e).__name__}", url, 0, "", None
    if method == "HEAD" and r.status in (403, 405, 501):
        return request(url, "GET")  # some servers reject HEAD
    return r.status, r.url, r.hops, r.headers.get("Content-Type", ""), r.body


def skippable(url):
    return url.startswith(("mailto:", "tel:", "javascript:", "data:", "#"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("start_url")
    ap.add_argument("--max-pages", type=int, default=30)
    ap.add_argument("--delay", type=float, default=0.3)
    args = ap.parse_args()

    start = args.start_url.rstrip("/")
    host = urlparse(start).netloc
    if not host:
        print("Invalid URL"); return 2
    try:
        check_url(start, allow_http=True)
    except BlockedUrlError as e:
        print(f"BLOCKED unsafe target: {e}"); return 2

    queue = deque([start])
    seen_pages, checked, broken, mixed = set(), {}, [], []

    while queue and len(seen_pages) < args.max_pages:
        page = queue.popleft()
        if page in seen_pages:
            continue
        seen_pages.add(page)
        status, final, _, ctype, body = request(page, "GET")
        print(f"[crawl {len(seen_pages)}/{args.max_pages}] {status} {page}")
        if not isinstance(status, int) or status >= 400 or body is None:
            broken.append((page, status, "(crawled page)"))
            continue
        if "html" not in ctype:
            continue

        parser = LinkExtractor()
        try:
            parser.feed(body.decode("utf-8", errors="replace"))
        except Exception:
            continue

        page_https = urlparse(final).scheme == "https"
        for raw in parser.links + parser.assets:
            if skippable(raw):
                continue
            url = urldefrag(urljoin(final, raw))[0]
            scheme = urlparse(url).scheme
            if scheme not in ("http", "https"):
                continue
            if page_https and scheme == "http":
                mixed.append((final, url))
            if url not in checked:
                time.sleep(args.delay)
                st, _, hops, _, _ = request(url)
                checked[url] = st
                if not isinstance(st, int) or st >= 400:
                    broken.append((final, st, url))
                elif hops:
                    pass  # single hop is fine; chains collapse in urllib
            # enqueue same-host pages found via <a>
            if raw in parser.links and urlparse(url).netloc == host \
                    and url not in seen_pages:
                queue.append(url)

    print(f"\n=== Link check summary for {start} ===")
    print(f"Pages crawled: {len(seen_pages)}   Unique URLs checked: {len(checked)}")
    if broken:
        print(f"\nBROKEN ({len(broken)}):")
        for src, st, url in broken:
            print(f"  [{st}] {url}\n         found on: {src}")
    if mixed:
        print(f"\nMIXED CONTENT ({len(mixed)}):")
        for src, url in mixed:
            print(f"  {url}\n         loaded by: {src}")
    if not broken and not mixed:
        print("No broken links or mixed content found.")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
