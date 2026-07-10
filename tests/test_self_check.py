"""self_check.py regression tests — POSIX/Windows separator handling, a full
run against this repo, and breakage detection against a synthetic mini-suite.
On windows-latest CI the full-run test exercises real backslash glob results;
on POSIX the separator logic is regression-tested directly."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELF = os.path.join(REPO, "plugins", "solo", "skills", "suite-integrity",
                    "scripts", "self_check.py")
VALIDATOR = os.path.join(REPO, "plugins", "ai", "skills",
                         "agent-room-templates", "scripts", "validate_rooms.py")


def run_self_check(root):
    return subprocess.run(
        [sys.executable, SELF, root, "-"], capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=120,
        env=dict(os.environ, PYTHONIOENCODING="utf-8"))


class SeparatorRegression(unittest.TestCase):
    def test_normalization_fix_present(self):
        with open(SELF, encoding="utf-8") as f:
            src = f.read()
        self.assertIn('p.replace(os.sep, "/") for p in '
                      'glob.glob("plugins/*/commands/*.md")', src,
                      "W1 Windows fix (v1.0.9) must stay in place")

    def test_windows_separator_logic(self):
        # glob on Windows returns os.sep-joined paths; the fixed expression
        # must still derive plugin names, the raw split must not.
        paths = ["plugins\\solo\\commands\\x.md", "plugins\\ai\\commands\\y.md"]
        fixed = sorted(p.replace("\\", "/") for p in paths)
        self.assertEqual([p.split("/")[1] for p in fixed], ["ai", "solo"])
        with self.assertRaises(IndexError):
            [p.split("/")[1] for p in paths]


class FullRun(unittest.TestCase):
    def test_repo_passes_all_checks(self):
        r = run_self_check(REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("12 pass", r.stdout)
        self.assertIn("0 fail", r.stdout)


class BreakageDetection(unittest.TestCase):
    def _mini_suite(self, root):
        def w(rel, content):
            p = os.path.join(root, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(content)
        w(".claude-plugin/marketplace.json", json.dumps({
            "name": "t", "owner": {"name": "t"},
            "metadata": {"description": "d", "version": "0.0.1",
                         "plugins": 2, "skills": 2, "commands": 1, "scripts": 1},
            "plugins": [
                {"name": "foo", "source": "./plugins/foo", "description": "foo"},
                {"name": "ai", "source": "./plugins/ai", "description": "rooms"},
            ]}))
        w("README.md", "- **2 plugins** · **2 skills** · "
                       "**1 slash commands** · **1 stdlib helper scripts**\n")
        w("CHANGELOG.md", "# Changelog\n\n## 0.0.1 — test\n")
        w("plugins/foo/.claude-plugin/plugin.json", json.dumps(
            {"name": "foo", "version": "0.0.1", "description": "d"}))
        w("plugins/foo/commands/go.md",
          "---\ndescription: run\nargument-hint: [x]\n---\nBody\n\n## Output\nDone\n")
        w("plugins/foo/skills/s1/SKILL.md",
          "---\nname: s1\ndescription: d\n---\nBody\n")
        w("plugins/ai/.claude-plugin/plugin.json", json.dumps(
            {"name": "ai", "version": "0.0.1", "description": "d"}))
        w("plugins/ai/skills/agent-room-templates/SKILL.md",
          "---\nname: agent-room-templates\ndescription: d\n---\nBody\n")
        os.makedirs(os.path.join(root, "plugins/ai/skills/agent-room-templates/scripts"),
                    exist_ok=True)
        shutil.copy(VALIDATOR, os.path.join(
            root, "plugins/ai/skills/agent-room-templates/scripts/validate_rooms.py"))

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="selfcheck-fixture-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self._mini_suite(self.tmp)

    def test_control_fixture_passes(self):
        r = run_self_check(self.tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("0 fail", r.stdout)

    def test_readme_count_drift_fails(self):
        p = os.path.join(self.tmp, "README.md")
        with open(p, encoding="utf-8") as f:
            s = f.read().replace("**2 plugins**", "**9 plugins**")
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(s)
        r = run_self_check(self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("README counts mismatch", r.stdout)

    def test_bad_agentroom_fails_via_validator(self):
        room = {
            "schema": "solo-suite/agentroom-v1", "name": "bad",
            "stages": [["a", "b"]],
            "seats": [
                {"id": "a", "role": "r", "reads": [], "writes": ["w.md"],
                 "commands": [], "deliverable": "d",
                 "handoff_to": "b", "handoff_check": "/ai:handoff-check"},
                {"id": "b", "role": "r", "reads": [], "writes": ["v.md"],
                 "commands": [], "deliverable": "d",
                 "handoff_to": None, "handoff_check": "/ai:handoff-check"},
            ],
            "exit_gate": None, "exit_criteria": "done",
        }
        p = os.path.join(self.tmp,
                         "plugins/ai/skills/agent-room-templates/agentsrooms/bad.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(room, f)
        r = run_self_check(self.tmp)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("SAME stage", r.stdout)
        self.assertIn("exit_gate_note", r.stdout)


if __name__ == "__main__":
    unittest.main()
