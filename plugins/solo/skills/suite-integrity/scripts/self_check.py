#!/usr/bin/env python3
"""solo-suite self-check: verify the installed suite and project memory are healthy.
Usage: python3 self_check.py [suite_root] [project_root]
  suite_root   = folder containing .claude-plugin/marketplace.json + plugins/ (default: cwd or auto-walk up)
  project_root = folder that should contain .solo/ (default: cwd). Pass "-" to skip memory checks.
Exit code 0 = all pass, 1 = failures found. Stdlib only."""
import json, os, re, sys, glob, zipfile

def find_suite(start):
    d = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(d, ".claude-plugin", "marketplace.json")):
            return d
        parent = os.path.dirname(d)
        if parent == d: return None
        d = parent

def frontmatter(path):
    s = open(path, encoding="utf-8").read()
    if not s.startswith("---"): return None, s
    parts = s.split("---", 2)
    return (parts[1], parts[2]) if len(parts) >= 3 else (None, s)

MEMORY_FILES = ["project.md","stack.md","prd.md","architecture.md","api-contract.md",
 "data-contract.md","env-contract.md","design.md","tasks.md","decisions.md","risks.md",
 "bugs.md","tests.md","release.md","monitoring.md","handoff.md"]

def main():
    suite = find_suite(sys.argv[1] if len(sys.argv) > 1 else ".")
    proj  = sys.argv[2] if len(sys.argv) > 2 else "."
    fails, warns, passes = [], [], []
    def fail(m): fails.append(m)
    def warn(m): warns.append(m)

    if not suite:
        fail("suite root not found (no .claude-plugin/marketplace.json walking up)"); suite = "."
    os.chdir(suite)

    # 1) plugin.json all valid
    pjs = sorted(glob.glob("plugins/*/.claude-plugin/plugin.json"))
    bad = 0
    for f in pjs:
        try:
            d = json.load(open(f, encoding="utf-8"))
            for k in ("name","version","description"):
                if k not in d: fail("%s missing key %s" % (f,k)); bad += 1
        except Exception as e:
            fail("invalid JSON %s: %s" % (f,e)); bad += 1
    if not bad: passes.append("all %d plugin.json valid" % len(pjs))

    # 2) commands have title, purpose, inputs, output format
    cmds = sorted(p.replace(os.sep, "/") for p in glob.glob("plugins/*/commands/*.md")); bad = 0
    for f in cmds:
        fm, body = frontmatter(f)
        if fm is None: fail("%s: no frontmatter (title/purpose)" % f); bad += 1; continue
        if not re.search(r"^description:", fm, re.M): fail("%s: no description (purpose)" % f); bad += 1
        if not (re.search(r"^argument-hint:", fm, re.M) or "$ARGUMENTS" in body):
            fail("%s: no inputs (argument-hint or $ARGUMENTS)" % f); bad += 1
        if "## Output" not in body and "## Status" not in body:
            fail("%s: no output format section" % f); bad += 1
    if not bad: passes.append("all %d commands have title/purpose/inputs/output" % len(cmds))

    # 3) every skill dir has SKILL.md with name+description
    sdirs = sorted(d for d in glob.glob("plugins/*/skills/*") if os.path.isdir(d)); bad = 0
    for d in sdirs:
        sm = os.path.join(d, "SKILL.md")
        if not os.path.isfile(sm): fail("%s: SKILL.md missing" % d); bad += 1; continue
        fm, _ = frontmatter(sm)
        keys = re.findall(r"^([A-Za-z0-9_-]+):", fm or "", re.M)
        if sorted(keys) != ["description","name"]:
            fail("%s: frontmatter keys %s (need exactly name+description)" % (sm, keys)); bad += 1
    if not bad: passes.append("all %d skill dirs have valid SKILL.md" % len(sdirs))

    # 4+5) README + marketplace counts match reality
    real = dict(plugins=len(glob.glob("plugins/*/.claude-plugin/plugin.json")),
                skills=len(glob.glob("plugins/*/skills/*/SKILL.md")),
                commands=len(cmds),
                scripts=len(glob.glob("plugins/*/skills/*/scripts/*.py")))
    if os.path.isfile("README.md"):
        rd = open("README.md", encoding="utf-8").read()
        m = re.search(r"\*\*(\d+) plugins\*\*.*?\*\*(\d+) skills\*\*.*?\*\*(\d+) slash commands\*\*.*?\*\*(\d+) stdlib", rd, re.S)
        if not m: warn("README: counts line not found to verify")
        else:
            claimed = dict(zip(("plugins","skills","commands","scripts"), map(int, m.groups())))
            diff = {k: (claimed[k], real[k]) for k in real if claimed[k] != real[k]}
            if diff: fail("README counts mismatch (claimed, real): %s" % diff)
            else: passes.append("README counts match reality %s" % real)
    mk = json.load(open(".claude-plugin/marketplace.json", encoding="utf-8"))
    if len(mk.get("plugins", [])) != real["plugins"]:
        fail("marketplace lists %d plugins, filesystem has %d" % (len(mk.get("plugins",[])), real["plugins"]))
    else: passes.append("marketplace lists all %d plugins" % real["plugins"])
    md = mk.get("metadata", {})
    for k in ("plugins","skills","commands","scripts"):
        if k in md and md[k] != real[k]:
            fail("marketplace metadata.%s=%s but real=%s" % (k, md[k], real[k]))
    missing_src = [p.get("source") for p in mk.get("plugins",[]) if not os.path.isdir(p.get("source","").lstrip("./"))]
    if missing_src: fail("marketplace sources missing on disk: %s" % missing_src)

    # 6) duplicate command names (same plugin = error; cross-plugin is fine, namespaced)
    seen = {}
    for f in cmds:
        plug = f.split("/")[1]; name = os.path.basename(f)
        seen.setdefault((plug,name), []).append(f)
    dups = {k:v for k,v in seen.items() if len(v) > 1}
    if dups: fail("duplicate command names: %s" % dups)
    else: passes.append("no duplicate command names")

    # 7) no broken references between commands (slash refs + **skill** refs)
    skills = {os.path.basename(os.path.dirname(p)) for p in glob.glob("plugins/*/skills/*/SKILL.md")}
    cmdset = {"/%s:%s" % (f.split("/")[1], os.path.basename(f)[:-3]) for f in cmds}
    bad = 0
    for f in cmds + sorted(glob.glob("plugins/*/skills/*/SKILL.md")):
        body = open(f, encoding="utf-8").read()
        # exact refs and wildcard refs (/plug:cmd, /plug:prefix-*, /plug:*) are both first-class:
        for ref in set(re.findall(r"(?<![A-Za-z0-9])(/[a-z][a-z0-9-]*:(?:[a-z][a-z0-9-]*\*?|\*))", body)):
            if re.search(re.escape(ref) + r"[a-z0-9-]", body): continue  # part of a longer token elsewhere
            plug, rest = ref[1:].split(":", 1)
            if rest.endswith("*"):
                prefix = rest[:-1]
                if not any(c.startswith("/%s:%s" % (plug, prefix)) for c in cmdset):
                    fail("%s: wildcard %s matches no existing command" % (f, ref)); bad += 1
            elif ref not in cmdset:
                fail("%s references missing command %s" % (f, ref)); bad += 1
        for m in re.findall(r"\*\*([a-z][a-z0-9-]+)\*\* skill", body):
            if m not in skills: fail("%s references missing skill %s" % (f, m)); bad += 1
        for m in re.findall(r"[Uu]se the `?([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`? skill", body):
            if m not in skills: fail("%s references missing skill %s (unbolded)" % (f, m)); bad += 1
    if not bad: passes.append("no broken command/skill references (wildcards resolved)")

    # 7b) marketplace descriptions (metadata + per-plugin) reference only existing commands
    bad = 0
    descs = [("metadata", md.get("description",""))] + \
            [(p.get("name"), p.get("description","")) for p in mk.get("plugins", [])]
    for name, desc in descs:
        for ref in set(re.findall(r"(?<![A-Za-z0-9])(/[a-z][a-z0-9-]*:(?:[a-z][a-z0-9-]*\*?|\*))", desc)):
            plug, rest = ref[1:].split(":", 1)
            if rest.endswith("*"):
                if not any(c.startswith("/%s:%s" % (plug, rest[:-1])) for c in cmdset):
                    fail("marketplace %s description: wildcard %s matches nothing" % (name, ref)); bad += 1
            elif ref not in cmdset:
                fail("marketplace %s description references missing command %s" % (name, ref)); bad += 1
    if not bad: passes.append("marketplace descriptions reference only existing commands")

    # 7c) versions agree: CHANGELOG top entry == metadata.version; cheatsheet docx == site-doctor
    mv = md.get("version")
    if os.path.isfile("CHANGELOG.md"):
        top = re.search(r"^## (\d+\.\d+\.\d+)", open("CHANGELOG.md", encoding="utf-8").read(), re.M)
        if not top: warn("CHANGELOG.md has no '## x.y.z' entry to verify")
        elif mv and top.group(1) != mv:
            fail("CHANGELOG top entry %s != marketplace metadata.version %s" % (top.group(1), mv))
        else: passes.append("CHANGELOG top entry matches metadata.version (%s)" % mv)
    else: warn("CHANGELOG.md missing — version bumps are undocumented")
    for dx in glob.glob("*.docx"):
        if "site-doctor" not in dx: continue
        try:
            x = zipfile.ZipFile(dx).read("word/document.xml").decode("utf-8", "ignore")
            got = re.search(r"v(\d+\.\d+\.\d+)", x)
            sd = json.load(open("plugins/site-doctor/.claude-plugin/plugin.json", encoding="utf-8")).get("version")
            if got and sd:
                if got.group(1) != sd: warn("%s says v%s but site-doctor is %s" % (dx, got.group(1), sd))
                else: passes.append("%s version matches site-doctor (%s)" % (dx, sd))
        except Exception as e: warn("could not read %s: %s" % (dx, e))

    # bundled JSON resources (e.g. agentsrooms templates) all parse
    bundled = [j for j in glob.glob("plugins/*/skills/*/**/*.json", recursive=True)]
    badj = 0
    for j in bundled:
        try: json.load(open(j, encoding="utf-8"))
        except Exception as e: fail("bundled JSON invalid %s: %s" % (j, e)); badj += 1
    if bundled and not badj: passes.append("all %d bundled JSON resources parse" % len(bundled))

    # 7d) agentroom templates pass the static room validator (ships with the ai plugin)
    rooms = sorted(p.replace(os.sep, "/") for p in glob.glob("plugins/*/skills/*/agentsrooms/*.json"))
    vpath = os.path.join("plugins", "ai", "skills", "agent-room-templates", "scripts", "validate_rooms.py")
    if rooms and os.path.isfile(vpath):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("validate_rooms", vpath)
            vr = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(vr)
            problems = vr.validate_files(rooms, suite_root=".")
            for m in problems:
                fail("agentroom %s" % m)
            if not problems:
                passes.append("all %d agentroom templates pass validate_rooms (graph + gates)" % len(rooms))
        except Exception as e:
            warn("could not run validate_rooms.py: %s" % e)
    elif rooms:
        warn("agentroom templates present but validate_rooms.py not found")

    # 8) .solo memory files
    if proj != "-":
        solo = os.path.join(os.path.abspath(proj), ".solo")
        if not os.path.isdir(solo):
            warn(".solo/ not found at %s — run /solo:start-session to initialize (skip with '-')" % proj)
        else:
            missing = [f for f in MEMORY_FILES if not os.path.isfile(os.path.join(solo, f))]
            if missing: warn(".solo/ missing files (created on first write): %s" % ", ".join(missing))
            else: passes.append(".solo/ has all %d standard memory files" % len(MEMORY_FILES))

    print("== solo-suite self-check ==")
    for m in passes: print("PASS  " + m)
    for m in warns:  print("WARN  " + m)
    for m in fails:  print("FAIL  " + m)
    print("== %d pass, %d warn, %d fail ==" % (len(passes), len(warns), len(fails)))
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
