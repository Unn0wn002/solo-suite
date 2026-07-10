"""Inventory consistency — README bold counts, marketplace metadata, CHANGELOG
top entry, and the cheatsheet docx version must all match the filesystem."""
import glob
import json
import os
import re
import unittest
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def real_counts():
    g = lambda p: len(glob.glob(os.path.join(REPO, p)))
    return {"plugins": g("plugins/*/.claude-plugin/plugin.json"),
            "skills": g("plugins/*/skills/*/SKILL.md"),
            "commands": g("plugins/*/commands/*.md"),
            "scripts": g("plugins/*/skills/*/scripts/*.py")}


class Inventory(unittest.TestCase):
    def setUp(self):
        self.real = real_counts()
        with open(os.path.join(REPO, ".claude-plugin", "marketplace.json"),
                  encoding="utf-8") as f:
            self.mk = json.load(f)

    def test_readme_counts_match_filesystem(self):
        with open(os.path.join(REPO, "README.md"), encoding="utf-8") as f:
            rd = f.read()
        m = re.search(r"\*\*(\d+) plugins\*\*.*?\*\*(\d+) skills\*\*.*?"
                      r"\*\*(\d+) slash commands\*\*.*?\*\*(\d+) stdlib", rd, re.S)
        self.assertIsNotNone(m, "README counts line missing")
        claimed = dict(zip(("plugins", "skills", "commands", "scripts"),
                           map(int, m.groups())))
        self.assertEqual(claimed, self.real)

    def test_marketplace_metadata_matches_filesystem(self):
        md = self.mk["metadata"]
        for k, v in self.real.items():
            self.assertEqual(md.get(k), v, k)
        self.assertEqual(len(self.mk["plugins"]), self.real["plugins"])
        for p in self.mk["plugins"]:
            src = p["source"].lstrip("./")
            self.assertTrue(os.path.isdir(os.path.join(REPO, src)), src)

    def test_changelog_top_matches_metadata_version(self):
        with open(os.path.join(REPO, "CHANGELOG.md"), encoding="utf-8") as f:
            ch = f.read()
        top = re.search(r"^## (\d+\.\d+\.\d+)", ch, re.M)
        self.assertEqual(top.group(1), self.mk["metadata"]["version"])

    def test_cheatsheet_version_matches_site_doctor(self):
        docx = glob.glob(os.path.join(REPO, "*site-doctor*.docx"))
        self.assertEqual(len(docx), 1)
        with zipfile.ZipFile(docx[0]) as z:
            xml = z.read("word/document.xml").decode("utf-8", "ignore")
        text = re.sub(r"<[^>]+>", "", xml)
        got = re.search(r"v(\d+\.\d+\.\d+)", text)
        with open(os.path.join(REPO, "plugins", "site-doctor",
                               ".claude-plugin", "plugin.json"),
                  encoding="utf-8") as f:
            sd = json.load(f)["version"]
        self.assertEqual(got.group(1), sd)


if __name__ == "__main__":
    unittest.main()
