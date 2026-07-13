"""Windows/default-encoding regressions for packaged command-line tools.

These tests use only disposable local fixtures. They deliberately force the
ordinary Windows cp1252 stream encoding instead of relying on PYTHONUTF8=1.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE_POLICY = os.path.join(REPO, "plugins", "gate", "lib",
                           "gate_policy.py")
RECORD_EVIDENCE = os.path.join(
    REPO, "plugins", "gate", "skills", "production-readiness-reviewer",
    "scripts", "record_evidence.py")
SCANNER = os.path.join(
    REPO, "plugins", "site-doctor", "skills", "security-review",
    "scripts", "scan_secrets.py")
VALIDATE_ROOMS = os.path.join(
    REPO, "plugins", "ai", "skills", "agent-room-templates", "scripts",
    "validate_rooms.py")


README = """# Demo library documentation

## Installation and setup

Create a virtual environment, activate it, and install the package from the
checked-out directory. This small library has no network service, database,
background worker, or runtime configuration. Maintainers can review every
module before installation and can reproduce the setup on a clean machine.

```bash
python -m pip install .
```

## Usage and API

Import the public function and pass two integers. The operation returns their
sum without changing either input. Callers receive normal Python type errors
for unsupported values. The command below demonstrates the complete public
interface and provides a quick smoke check for a newly installed package.

```python
from demo import add
assert add(20, 22) == 42
```

Run the standard unit-test discovery command before publishing. The suite is
offline, deterministic, dependency-free, and suitable for developer laptops
as well as continuous integration workers. Release maintainers should review
the result, package metadata, source commit, and generated evidence together.
"""


def cp1252_env():
    env = dict(os.environ)
    env["PYTHONUTF8"] = "0"
    env["PYTHONIOENCODING"] = "cp1252"
    return env


def git(root, *args):
    return subprocess.run(["git"] + list(args), cwd=root,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=30)


class WindowsDefaultEncoding(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="windows-encoding-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_validate_rooms_help_succeeds_under_cp1252(self):
        result = subprocess.run(
            [sys.executable, VALIDATE_ROOMS, "--help"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=cp1252_env(), timeout=60)
        self.assertEqual(result.returncode, 0,
                         (result.stdout + result.stderr).decode(
                             "cp1252", "replace"))
        self.assertIn(b"usage:", result.stdout.lower())

    def test_cp1252_gate_output_is_stored_as_utf8(self):
        with open(os.path.join(self.root, "README.md"), "w",
                  encoding="utf-8") as stream:
            stream.write(README)
        with open(os.path.join(self.root, "demo.py"), "w",
                  encoding="utf-8") as stream:
            stream.write("def add(a, b):\n    return a + b\n")
        with open(os.path.join(self.root, ".gitignore"), "w",
                  encoding="utf-8") as stream:
            stream.write(".solo/gate-evidence/\n.solo/run-state/\n")
        git(self.root, "init", "-q", ".")
        git(self.root, "config", "user.email", "test@example.invalid")
        git(self.root, "config", "user.name", "test")
        git(self.root, "add", "-A")
        committed = git(self.root, "commit", "-qm", "fixture")
        self.assertEqual(committed.returncode, 0, committed.stderr)

        base = [sys.executable, RECORD_EVIDENCE,
                "--category", "documentation", "--project", "demo",
                "--environment", "production", "--root", self.root,
                "--reviewer", "documentation seat"]
        command = ["--", sys.executable, GATE_POLICY, "verify-artifact",
                   "documentation"]
        preview = subprocess.run(
            base + ["--preview"] + command,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=cp1252_env(), timeout=120)
        token = re.search(rb"preview token: ([0-9a-f]{64})", preview.stdout)
        self.assertEqual(preview.returncode, 0,
                         (preview.stdout + preview.stderr).decode(
                             "cp1252", "replace"))
        self.assertIsNotNone(token)
        result = subprocess.run(
            base + ["--confirm-execution", token.group(1).decode("ascii")]
            + command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=cp1252_env(), timeout=120)
        self.assertEqual(result.returncode, 0,
                         (result.stdout + result.stderr).decode(
                             "cp1252", "replace"))

        artifact = os.path.join(self.root, ".solo", "gate-evidence",
                                "artifacts", "documentation.log")
        with open(artifact, "rb") as stream:
            captured = stream.read()
        text = captured.decode("utf-8")  # strict: mixed encodings must fail
        self.assertIn("# capture_encoding: utf-8", text)
        self.assertIn("headings \u2014 all", text)

        # The generated CP1252-origin capture is outside scanner coverage by
        # exact runtime-path policy, so it cannot poison a repository scan.
        scanned = subprocess.run(
            [sys.executable, SCANNER, self.root, "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=cp1252_env(), timeout=120)
        self.assertEqual(scanned.returncode, 0,
                         (scanned.stdout + scanned.stderr).decode(
                             "cp1252", "replace"))

    def test_scanner_includes_generated_runtime_dirs(self):
        with open(os.path.join(self.root, "clean.py"), "w",
                  encoding="utf-8") as stream:
            stream.write("print('clean fixture')\n")
        for relative in (os.path.join(".solo", "gate-evidence", "bad.log"),
                         os.path.join(".solo", "run-state", "bad.json")):
            path = os.path.join(self.root, relative)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as stream:
                stream.write(b"cp1252 punctuation: \x97\n")

        utf8_env = dict(os.environ, PYTHONUTF8="0", PYTHONIOENCODING="utf-8")
        excluded = subprocess.run(
            [sys.executable, SCANNER, self.root, "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=utf8_env, timeout=120)
        self.assertEqual(excluded.returncode, 3,
                         (excluded.stdout + excluded.stderr).decode(
                             "utf-8", "replace"))
        coverage = json.loads(excluded.stdout.decode("utf-8"))["coverage"]
        self.assertEqual(coverage["inspected"], 1, coverage)
        self.assertEqual(coverage["unsupported_encoding"], 2, coverage)

        # Similar names outside the two exact paths must remain in scope.
        for relative in (
                os.path.join(".solo", "gate-evidence-copy", "bad.log"),
                os.path.join("nested", "gate-evidence", "bad.log")):
            path = os.path.join(self.root, relative)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as stream:
                stream.write(b"cp1252 punctuation: \x97\n")
        included = subprocess.run(
            [sys.executable, SCANNER, self.root, "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=utf8_env, timeout=120)
        self.assertEqual(included.returncode, 3,
                         (included.stdout + included.stderr).decode(
                             "utf-8", "replace"))
        coverage = json.loads(included.stdout.decode("utf-8"))["coverage"]
        self.assertEqual(coverage["unsupported_encoding"], 4, coverage)


if __name__ == "__main__":
    unittest.main()
