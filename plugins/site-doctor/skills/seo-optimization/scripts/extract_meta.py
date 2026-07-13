#!/usr/bin/env python3
"""extract_meta.py — crawl same-domain pages and extract SEO-relevant
metadata per page: title, meta description, canonical, robots directives,
H1s, Open Graph tags, and structured-data presence. Flags duplicates and gaps.

Stdlib only. Outbound requests go through lib/url_guard.py (SSRF guard) —
private/internal/metadata targets and unsafe redirects are refused with a
BLOCKED result. Usage:
    python3 extract_meta.py https://example.com [--max-pages 25] [--delay 0.3]

Exit codes: 0 = crawl complete, no missing titles/descriptions or
duplicate titles; 1 = SEO failures found; 2 = usage/blocked; 3 = nothing
failed but coverage is UNVERIFIED (crawl truncated or nothing parsed).
"""
import os
import sys
import time
import argparse
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque, defaultdict

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib")))
try:
    from url_guard import safe_get, check_url, BlockedUrlError
except ImportError:
    sys.exit("url_guard.py not found — run from an intact site-doctor plugin")

UA = "site-doctor-seo/1.0"
TIMEOUT = 12
MAX_BYTES = 2 * 1024 * 1024  # per-response read cap


class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = None
        self._in_title = False
        self.description = None
        self.canonical = None
        self.robots = None
        self.h1s = []
        self._h1_depth = 0
        self._h1_buf = []
        self.og = {}
        self.jsonld = 0
        self._in_jsonld = False
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = (a.get("name") or "").lower()
            prop = (a.get("property") or "").lower()
            content = a.get("content", "")
            if name == "description":
                self.description = content
            elif name == "robots":
                self.robots = content
            elif prop.startswith("og:"):
                self.og[prop] = content
        elif tag == "link" and (a.get("rel") or "").lower() == "canonical":
            self.canonical = a.get("href")
        elif tag == "h1":
            if self._h1_depth == 0:
                self._h1_buf = []
            self._h1_depth += 1
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self._in_jsonld = True
            self.jsonld += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            if self._h1_depth > 0:
                self._h1_depth -= 1
                if self._h1_depth == 0:
                    # one H1 element = ONE entry, even with nested spans/nodes
                    text = " ".join("".join(self._h1_buf).split())
                    self.h1s.append(text)
                    self._h1_buf = []
        elif tag == "script":
            self._in_jsonld = False

    def handle_data(self, data):
        if self._in_title:
            self.title = (self.title or "") + data.strip()
        elif self._h1_depth > 0:
            self._h1_buf.append(data)


def fetch(url):
    try:
        r = safe_get(url, timeout=TIMEOUT, allow_http=True, max_bytes=MAX_BYTES,
                     headers={"User-Agent": UA})
    except BlockedUrlError as e:
        return f"BLOCKED: {e}", None, ""
    except Exception:
        return None, None, ""
    if r.status >= 400:
        return r.status, None, ""
    ctype = r.headers.get("Content-Type", "")
    xrobots = r.headers.get("X-Robots-Tag", "")
    if "html" not in ctype:
        return None, None, xrobots
    return r.status, (r.body or b"").decode("utf-8", "replace"), xrobots


def positive_int(value):
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return n


def non_negative_float(value):
    import math
    f = float(value)
    if not math.isfinite(f) or f < 0:
        raise argparse.ArgumentTypeError(
            "must be a finite number >= 0 (got %r)" % value)
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("start_url")
    ap.add_argument("--max-pages", type=positive_int, default=25)
    ap.add_argument("--delay", type=non_negative_float, default=0.3)
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
    seen = set()
    pages = []
    inbound = defaultdict(int)  # internal link target -> count

    while queue and len(seen) < args.max_pages:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        status, html, xrobots = fetch(url)
        if not html:
            print(f"[skip] {status} {url}")
            continue
        p = MetaParser()
        try:
            p.feed(html)
        except Exception:
            pass
        pages.append({
            "url": url, "title": p.title, "desc": p.description,
            "canonical": p.canonical,
            "robots": (p.robots or "") + (" " + xrobots if xrobots else ""),
            "h1s": p.h1s, "og": len(p.og), "jsonld": p.jsonld,
        })
        for raw in p.links:
            u = urldefrag(urljoin(url, raw))[0]
            if urlparse(u).netloc == host:
                inbound[u] += 1
                if u not in seen:
                    queue.append(u)
        print(f"[crawl {len(seen)}/{args.max_pages}] {url}")
        time.sleep(args.delay)

    # ---- report ----
    print(f"\n=== SEO metadata: {start} ({len(pages)} pages) ===\n")
    titles = defaultdict(list)
    descs = defaultdict(list)
    for pg in pages:
        u = pg["url"]
        print(f"URL: {u}")
        t = pg["title"] or ""
        print(f"  title  ({len(t)}): {t or '*** MISSING ***'}")
        if t:
            titles[t].append(u)
        d = pg["desc"] or ""
        print(f"  desc   ({len(d)}): {d[:100] or '*** MISSING ***'}")
        if d:
            descs[d].append(u)
        print(f"  canonical: {pg['canonical'] or '(none)'}")
        if pg["robots"].strip():
            print(f"  robots: {pg['robots'].strip()}")
            if "noindex" in pg["robots"].lower():
                print("    !! NOINDEX present — verify this page should be excluded")
        n = len(pg["h1s"])
        flag = "" if n == 1 else "  !! expected exactly 1"
        print(f"  h1 count: {n}{flag}")
        print(f"  og tags: {pg['og']}   json-ld blocks: {pg['jsonld']}"
              f"{'   !! no structured data' if pg['jsonld'] == 0 else ''}")
        print(f"  internal inbound links: {inbound.get(u, 0)}"
              f"{'   !! orphan candidate' if inbound.get(u, 0) == 0 and u != start else ''}")
        print()

    dup_t = {k: v for k, v in titles.items() if len(v) > 1}
    dup_d = {k: v for k, v in descs.items() if len(v) > 1}
    if dup_t:
        print("DUPLICATE TITLES:")
        for t, urls in dup_t.items():
            print(f"  {t!r} on {len(urls)} pages: {', '.join(urls[:4])}")
    if dup_d:
        print("DUPLICATE DESCRIPTIONS:")
        for d, urls in dup_d.items():
            print(f"  {d[:60]!r}... on {len(urls)} pages")
    if not dup_t and not dup_d:
        print("No duplicate titles or descriptions found.")

    # ---- structured verdict -------------------------------------------------
    fails = warns = unverified = 0
    for pg in pages:
        if not pg["title"]:
            fails += 1
        if not pg["desc"]:
            fails += 1
        if len(pg["h1s"]) != 1:
            warns += 1
        if not pg["canonical"]:
            warns += 1
    fails += len(dup_t)
    warns += len(dup_d)
    if len(seen) >= args.max_pages and queue:
        unverified += 1
        print(f"[UNVERIFIED] crawl stopped at --max-pages {args.max_pages} "
              f"with {len(queue)} URL(s) still queued - coverage incomplete")
    if not pages:
        unverified += 1
        print("[UNVERIFIED] no pages could be parsed - nothing was checked")
    passes = max(len(pages) * 2 - fails, 0)
    print(f"\nRESULT: pass={passes} warn={warns} fail={fails} "
          f"unverified={unverified}")
    if fails:
        return 1
    if unverified:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
