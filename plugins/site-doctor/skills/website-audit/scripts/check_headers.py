#!/usr/bin/env python3
"""check_headers.py — audit security/caching headers, HTTPS redirect,
compression, cookie flags, and exposed sensitive paths for one or more URLs.

Stdlib only. Outbound requests go through lib/url_guard.py (SSRF guard) —
private/internal/metadata targets and unsafe redirects are refused with a
BLOCKED result. Usage:
    python3 check_headers.py https://example.com [https://example.com/app ...]

Exit code: 0 = no FAILs, 1 = at least one FAIL, 2 = could not connect.
"""
import os
import sys
from urllib.parse import urlparse, urlunparse

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib")))
try:
    from url_guard import safe_get, check_url, BlockedUrlError
except ImportError:
    sys.exit("url_guard.py not found — run from an intact site-doctor plugin")

UA = "site-doctor-audit/1.0 (+https://github.com/site-doctor)"
TIMEOUT = 15

SECURITY_HEADERS = {
    "strict-transport-security": "FAIL",
    "content-security-policy": "WARN",
    "x-content-type-options": "FAIL",
    "x-frame-options": "WARN",  # OK if CSP frame-ancestors present
    "referrer-policy": "WARN",
    "permissions-policy": "WARN",
}
LEAKY_HEADERS = ("server", "x-powered-by", "x-aspnet-version")
SENSITIVE_PATHS = ("/.env", "/.git/HEAD", "/.git/config", "/wp-config.php.bak")

results = {"PASS": 0, "WARN": 0, "FAIL": 0}


def report(level, msg):
    results[level] += 1
    print(f"  [{level}] {msg}")


def fetch(url, follow_redirects=True, method="GET"):
    try:
        r = safe_get(url, method=method, follow_redirects=follow_redirects,
                     timeout=TIMEOUT, allow_http=True, read_body=False,
                     headers={"User-Agent": UA, "Accept-Encoding": "gzip, br"})
        return r.status, dict(
            (k.lower(), v) for k, v in r.headers.items()
        ), r.headers.get_all("Set-Cookie") or []
    except BlockedUrlError as e:
        return None, {"_error": "BLOCKED unsafe target: %s" % e}, []
    except Exception as e:
        return None, {"_error": str(e)}, []


def check_https_redirect(url):
    p = urlparse(url)
    if p.scheme != "https":
        report("FAIL", f"Target is not HTTPS: {url}")
        return
    http_url = urlunparse(("http",) + p[1:])
    status, headers, _ = fetch(http_url, follow_redirects=False)
    if status is None:
        report("WARN", f"Port 80 unreachable ({headers.get('_error')}) — "
                       "fine if HTTP is blocked at the edge")
    elif status in (301, 308) and headers.get("location", "").startswith("https://"):
        report("PASS", "HTTP redirects permanently to HTTPS")
    elif status in (302, 307):
        report("WARN", f"HTTP redirects with {status}; use 301/308 for HTTPS upgrade")
    else:
        report("FAIL", f"HTTP does not redirect to HTTPS (got {status})")


def check_security_headers(headers):
    for name, miss_level in SECURITY_HEADERS.items():
        if name in headers:
            report("PASS", f"{name}: {headers[name][:90]}")
        else:
            if name == "x-frame-options" and \
                    "frame-ancestors" in headers.get("content-security-policy", ""):
                report("PASS", "frame-ancestors set via CSP (x-frame-options not needed)")
            else:
                report(miss_level, f"Missing header: {name}")
    hsts = headers.get("strict-transport-security", "")
    if hsts and "max-age" in hsts:
        try:
            age = int(hsts.split("max-age=")[1].split(";")[0])
            if age < 15552000:
                report("WARN", f"HSTS max-age is short ({age}s); recommend >= 15552000")
        except (ValueError, IndexError):
            pass
    for name in LEAKY_HEADERS:
        val = headers.get(name, "")
        if any(ch.isdigit() for ch in val):
            report("WARN", f"Version leakage: {name}: {val}")


def check_caching_and_compression(headers):
    enc = headers.get("content-encoding", "")
    if enc in ("gzip", "br", "zstd"):
        report("PASS", f"Compression enabled ({enc})")
    else:
        report("WARN", "No compression on this response (gzip/brotli)")
    cc = headers.get("cache-control")
    if cc:
        report("PASS", f"cache-control: {cc}")
    else:
        report("WARN", "No cache-control header")


def check_cookies(cookies):
    for c in cookies:
        low = c.lower()
        name = c.split("=", 1)[0]
        missing = [f for f in ("secure", "httponly", "samesite") if f not in low]
        if missing:
            report("WARN", f"Cookie '{name}' missing flags: {', '.join(missing)}")
        else:
            report("PASS", f"Cookie '{name}' has Secure/HttpOnly/SameSite")


def check_sensitive_paths(url):
    base = "{0.scheme}://{0.netloc}".format(urlparse(url))
    for path in SENSITIVE_PATHS:
        status, headers, _ = fetch(base + path)
        if status == 200:
            ct = headers.get("content-type", "")
            if "html" in ct and path != "/.env":
                report("WARN", f"{path} returns 200 with HTML — likely a soft-404, verify manually")
            else:
                report("FAIL", f"EXPOSED: {base}{path} returns 200")
        elif status in (401, 403, 404, None):
            report("PASS", f"{path} not exposed ({status})")
        else:
            report("WARN", f"{path} returned {status} — verify manually")


def main(urls):
    exit_code = 0
    for url in urls:
        print(f"\n=== {url} ===")
        try:
            check_url(url, allow_http=True)
        except BlockedUrlError as e:
            print(f"  [BLOCKED] unsafe target: {e}")
            exit_code = max(exit_code, 2)
            continue
        status, headers, cookies = fetch(url)
        if status is None:
            print(f"  [ERROR] Could not connect: {headers.get('_error')}")
            exit_code = max(exit_code, 2)
            continue
        print(f"  Status: {status}")
        check_https_redirect(url)
        check_security_headers(headers)
        check_caching_and_compression(headers)
        check_cookies(cookies)
        check_sensitive_paths(url)
    print(f"\nTotals: {results['PASS']} pass, {results['WARN']} warn, {results['FAIL']} fail")
    if results["FAIL"]:
        exit_code = max(exit_code, 1)
    return exit_code


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
