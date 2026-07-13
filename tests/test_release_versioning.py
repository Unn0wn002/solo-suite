"""Release-versioning regression (v1.0.17, blocker 1): a plugin whose
tree MATERIALLY changed since the previous release must NOT keep the
previous release's component version.

The previous release is snapshotted in
release/previous-release-inventory.json (written by
release/gen_release_inventory.py against the pristine previous tree).
This test recomputes the current tree's file digests with the SAME
shared ignore rules (generated files — __pycache__, *.pyc, coverage
output, dist, test caches — never count as changes) and fails when a
changed plugin retains its old version. The exact v1.0.16 audit finding
— ai/gate/solo changed since v1.0.15 at unchanged versions — can no
longer ship."""
import importlib.util
import json
import os
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTORY = os.path.join(REPO, "release",
                         "previous-release-inventory.json")
GEN = os.path.join(REPO, "release", "gen_release_inventory.py")

_spec = importlib.util.spec_from_file_location("gen_release_inventory",
                                               GEN)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


def plugin_of(rel):
    parts = rel.split("/")
    if len(parts) >= 2 and parts[0] == "plugins":
        return parts[1]
    return None


class ReleaseVersioning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(INVENTORY, encoding="utf-8") as f:
            cls.prev = json.load(f)
        cls.now_files = gen.walk_files(REPO)
        cls.now = gen.build_inventory(REPO)

    def changed_files(self, plugin):
        """Added/removed/modified files under plugins/<plugin>/, computed
        against the previous-release inventory with the shared ignore
        rules."""
        prev = {r: h for r, h in self.prev["files"].items()
                if plugin_of(r) == plugin}
        now = {r: h for r, h in self.now_files.items()
               if plugin_of(r) == plugin}
        changed = sorted(
            set(prev) ^ set(now)
            | {r for r in set(prev) & set(now) if prev[r] != now[r]})
        return changed

    def test_inventory_snapshot_is_wellformed(self):
        self.assertEqual(self.prev["schema"],
                         "solo-suite/release-inventory-v1")
        self.assertTrue(self.prev["files"])
        self.assertTrue(self.prev["plugin_versions"])

    def test_materially_changed_plugins_carry_new_versions(self):
        offenders = []
        for name, prev_version in sorted(
                self.prev["plugin_versions"].items()):
            now_version = self.now["plugin_versions"].get(name)
            if now_version is None:
                continue                      # plugin removed: nothing to pin
            changed = self.changed_files(name)
            if changed and now_version == prev_version:
                offenders.append(
                    "plugins/%s changed since release %s but kept version "
                    "%s — bump it. Changed files (first 10): %s"
                    % (name, self.prev["release"], prev_version,
                       ", ".join(changed[:10])))
        self.assertEqual(offenders, [], "\n".join(offenders))

    def test_unchanged_plugins_keep_their_versions(self):
        """The inverse guard: an UNCHANGED plugin tree must not have been
        bumped gratuitously (version churn hides real changes)."""
        offenders = []
        for name, prev_version in sorted(
                self.prev["plugin_versions"].items()):
            now_version = self.now["plugin_versions"].get(name)
            if now_version is None:
                continue
            if not self.changed_files(name) \
                    and now_version != prev_version:
                offenders.append("plugins/%s is byte-identical to release "
                                 "%s but its version moved %s -> %s"
                                 % (name, self.prev["release"],
                                    prev_version, now_version))
        self.assertEqual(offenders, [], "\n".join(offenders))

    def test_any_tree_change_requires_a_new_release_version(self):
        prev_all = self.prev["files"]
        now_all = self.now_files
        changed = (set(prev_all) ^ set(now_all)) \
            | {r for r in set(prev_all) & set(now_all)
               if prev_all[r] != now_all[r]}
        # the snapshot file itself always differs between releases
        changed.discard("release/previous-release-inventory.json")
        if changed:
            self.assertNotEqual(
                self.now["release"], self.prev["release"],
                "the tree changed (%d files, e.g. %s) but the marketplace "
                "release version is still %s"
                % (len(changed), sorted(changed)[:5],
                   self.prev["release"]))

    def test_generated_files_never_count_as_changes(self):
        """The shared ignore rules exclude generated artifacts, so a
        __pycache__/ or .coverage left behind by a test run can never
        force a version bump."""
        for name in ("__pycache__", ".pytest_cache", "dist",
                     "node_modules"):
            self.assertIn(name, gen.IGNORED_DIRS, name)
        for name in (".coverage", "scan.json", "coverage.xml"):
            self.assertIn(name, gen.IGNORED_FILES, name)
        for ext in (".pyc", ".pyo"):
            self.assertIn(ext, gen.IGNORED_EXTS, ext)
        self.assertTrue(gen.ignored_file("x.pyc"))
        self.assertTrue(gen.ignored_file(".coverage.host.123"))
        self.assertTrue(gen.ignored_file("rec.json.tmp.42"))
        self.assertFalse(gen.ignored_file("gate_policy.py"))
        for rel in self.now_files:
            self.assertNotIn("__pycache__", rel)
            self.assertFalse(rel.endswith(".pyc"), rel)


if __name__ == "__main__":
    unittest.main()
