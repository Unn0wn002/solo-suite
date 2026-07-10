"""Loopback HTTP fixture server for the offline test suite.

Binds only to 127.0.0.1 and never contacts external hosts. Pages deliberately
avoid external asset URLs except where a script only PARSES them (never
fetches), so no test can generate outbound traffic.
"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_CLIENT_ABORT = (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)
from urllib.parse import urlparse, parse_qs

OK_HTML = b"""<html><head><title>OK Page</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="fixture page">
<link rel="canonical" href="/ok">
<script src="https://www.googletagmanager.com/gtag/js?id=G-TEST"></script>
</head><body><h1>ok</h1><a href="/page2">two</a> <a href="/missing">gone</a></body></html>"""
# parse-only page above: scan_trackers/extract_meta/check_mobile never fetch
# script srcs. check_links DOES fetch everything, so it gets a local-only page:
LINK_HTML = (b"<html><head><title>Link Page</title></head><body>"
             b"<a href=\"/page2\">two</a> <a href=\"/missing\">gone</a>"
             b"<img src=\"/ok\"></body></html>")
PAGE2_HTML = (b"<html><head><title>Page Two</title>"
              b"<meta name=\"description\" content=\"p2\"></head>"
              b"<body><h1>two</h1></body></html>")
BIG_SIZE = 3 * 1024 * 1024

REDIRECTS = {
    "/redir-ok": "/ok",
    "/redir-private": "http://169.254.169.254/latest/meta-data/",
    "/redir-loop": "/redir-loop",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _respond(self, send_body):
        path = urlparse(self.path).path
        if path in REDIRECTS:
            self.send_response(302)
            self.send_header("Location", REDIRECTS[path])
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        code, ctype, body, extra = 404, "text/plain", b"not found", []
        if path in ("/", "/ok"):
            code, ctype, body = 200, "text/html; charset=utf-8", OK_HTML
            extra = [("Set-Cookie", "sid=abc123; Path=/")]
        elif path == "/linkcheck":
            code, ctype, body = 200, "text/html; charset=utf-8", LINK_HTML
        elif path == "/page2":
            code, ctype, body = 200, "text/html; charset=utf-8", PAGE2_HTML
        elif path == "/big":
            code, ctype, body = 200, "text/html; charset=utf-8", b"a" * BIG_SIZE
        elif path == "/dns-query":
            qs = parse_qs(urlparse(self.path).query)
            rrtype = (qs.get("type") or ["TXT"])[0].upper()
            name = (qs.get("name") or [""])[0]
            if rrtype == "MX":
                ans = [{"data": "10 mail.example.com."}]
            elif rrtype == "TXT" and name.startswith("_dmarc."):
                ans = [{"data": '"v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com"'}]
            elif rrtype == "TXT" and "._domainkey." in name:
                ans = [{"data": '"v=DKIM1; k=rsa; p=MIGfMA0GCSq"'}]
            elif rrtype == "TXT":
                ans = [{"data": '"v=spf1 include:_spf.example.com -all"'}]
            else:
                ans = []
            code, ctype = 200, "application/dns-json"
            body = json.dumps({"Answer": ans}).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        if send_body:
            try:
                self.wfile.write(body)
            except _CLIENT_ABORT:
                pass  # expected: e.g. the size-cap test closes mid-body

    def do_GET(self):
        self._respond(True)

    def do_HEAD(self):
        self._respond(False)


class QuietThreadingHTTPServer(ThreadingHTTPServer):
    """Client aborts are an expected part of the cap/redirect tests — keep
    successful test output free of their tracebacks."""

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], _CLIENT_ABORT):
            return
        super().handle_error(request, client_address)


def start():
    """Return (server, base_url). Caller must stop(server)."""
    srv = QuietThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d" % srv.server_port


def stop(srv):
    srv.shutdown()
    srv.server_close()
