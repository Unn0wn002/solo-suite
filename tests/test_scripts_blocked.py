"""End-to-end script behavior: every network script refuses private/metadata
targets with a clear BLOCKED result (pre-connect, so fully offline), and runs
correctly against the loopback fixture server."""
import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_server  # noqa: E402

SD = os.path.join(REPO, "plugins", "site-doctor", "skills")
S = {
    "headers": os.path.join(SD, "website-audit", "scripts", "check_headers.py"),
    "links": os.path.join(SD, "website-audit", "scripts", "check_links.py"),
    "trackers": os.path.join(SD, "compliance-check", "scripts", "scan_trackers.py"),
    "mobile": os.path.join(SD, "mobile-audit", "scripts", "check_mobile.py"),
    "meta": os.path.join(SD, "seo-optimization", "scripts", "extract_meta.py"),
    "email": os.path.join(SD, "email-deliverability", "scripts", "check_email_dns.py"),
}
URL_GUARD_LIB = os.path.join(REPO, "plugins", "site-doctor", "lib")

# The production URL guard deliberately has no environment-variable bypass.
# Local fixture happy paths therefore run through this test-process-only
# harness, which injects the documented ``extra_allowed`` function argument
# before executing the real CLI script. Nothing in the shipped helpers reads
# this harness or admits private addresses from ambient process state.
FIXTURE_HARNESS = r"""
import runpy
import sys

lib_dir, script, *script_args = sys.argv[1:]
sys.path.insert(0, lib_dir)
import url_guard

real_check_url = url_guard.check_url

def fixture_check_url(url, allow_http=False, extra_allowed=()):
    allowed = tuple(extra_allowed) + ("127.0.0.1", "::1")
    return real_check_url(url, allow_http=allow_http, extra_allowed=allowed)

url_guard.check_url = fixture_check_url
sys.argv = [script] + script_args
runpy.run_path(script, run_name="__main__")
"""


def run(script, args, env_extra=None, allow_fixture=False):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("URL_GUARD_EXTRA_ALLOWED", None)
    env.pop("URL_GUARD_TEST_MODE", None)
    env.update(env_extra or {})
    command = ([sys.executable, "-c", FIXTURE_HARNESS,
                URL_GUARD_LIB, script] + args if allow_fixture
               else [sys.executable, script] + args)
    return subprocess.run(command, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=120, cwd=REPO, env=env)


class BlockedTargets(unittest.TestCase):
    """Private/metadata IP literals: refused before any socket operation."""

    def test_url_scripts_block_private_and_metadata(self):
        cases = [
            ("headers", ["https://10.0.0.1/"], 2),
            ("links", ["https://169.254.169.254/", "--max-pages", "2",
                       "--delay", "0"], 2),
            ("trackers", ["https://192.168.1.10/"], 2),
            ("mobile", ["https://169.254.169.254/latest/meta-data/"], 2),
            ("meta", ["https://100.100.100.200/", "--max-pages", "2",
                      "--delay", "0"], 2),
        ]
        for name, args, want_rc in cases:
            r = run(S[name], args)
            self.assertEqual(r.returncode, want_rc, (name, r.stdout, r.stderr))
            self.assertIn("BLOCKED", r.stdout, name)

    def test_email_blocks_unsafe_doh_override(self):
        r = run(S["email"], ["example.com"],
                {"SITE_DOCTOR_DOH": "https://10.0.0.99/dns-query"})
        self.assertIn("BLOCKED unsafe DoH endpoint", r.stdout, r.stderr)

    def test_scheme_refused(self):
        r = run(S["headers"], ["ftp://example.com/"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("BLOCKED", r.stdout)


class FixtureHappyPaths(unittest.TestCase):
    """The scripts still do their jobs against a loopback fixture site."""

    @classmethod
    def setUpClass(cls):
        cls.srv, cls.base = fixture_server.start()

    @classmethod
    def tearDownClass(cls):
        fixture_server.stop(cls.srv)

    def test_check_headers_reports(self):
        r = run(S["headers"], [self.base + "/ok"], allow_fixture=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)  # fixture lacks sec headers
        self.assertIn("Missing header: strict-transport-security", r.stdout)
        self.assertIn("Cookie 'sid'", r.stdout)

    def test_check_links_finds_broken(self):
        r = run(S["links"], [self.base + "/linkcheck", "--max-pages", "5",
                             "--delay", "0"], allow_fixture=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("BROKEN", r.stdout)
        self.assertIn("/missing", r.stdout)

    def test_scan_trackers_detects_gtm(self):
        r = run(S["trackers"], [self.base + "/ok"], allow_fixture=True)
        # a tracker with NO consent tool is a FAIL verdict -> exit 1
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("Google Tag Manager", r.stdout)
        self.assertIn("[FAIL]", r.stdout)
        self.assertIn("RESULT: ", r.stdout)
        self.assertIn("sid", r.stdout)

    def test_check_mobile_sees_viewport(self):
        r = run(S["mobile"], [self.base + "/ok"], allow_fixture=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("viewport meta tag", r.stdout)
        self.assertIn("[PASS]", r.stdout)

    def test_extract_meta_crawls(self):
        r = run(S["meta"], [self.base + "/ok", "--max-pages", "3",
                            "--delay", "0"], allow_fixture=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK Page", r.stdout)
        self.assertIn("Page Two", r.stdout)

    def test_check_email_dns_via_fixture_doh(self):
        env = {"SITE_DOCTOR_DOH": self.base + "/dns-query"}
        r = run(S["email"], ["example.com", "--dkim-selector", "s1"], env,
                allow_fixture=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("SPF present", r.stdout)
        self.assertIn("DMARC present", r.stdout)
        self.assertIn("DKIM key found", r.stdout)


if __name__ == "__main__":
    unittest.main()
