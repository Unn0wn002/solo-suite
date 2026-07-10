#!/usr/bin/env python3
"""validate_rooms.py — static validator for solo-suite/agentroom-v1 templates.

Checks per room file:
  * schema/name present; stages is a non-empty list of non-empty seat-id lists
  * every seat belongs to exactly one stage (and every stage id is a real seat)
  * every handoff target exists
  * handoffs point only to LATER stages — same-stage (parallel) or backward
    handoffs fail; repetition must use the explicit top-level `loop` block
  * no two seats write the same artifact within one stage
  * exit_criteria present; exit_gate is a /plugin:command ref, or null only
    with an exit_gate_note documenting why
  * seat commands / handoff_check / exit_gate resolve to commands that exist
    in the suite (when a suite root with plugins/ is found)

Usage: python3 validate_rooms.py [room.json ...] [--suite ROOT]
Defaults: the agentsrooms/*.json shipped next to this script; suite root is
auto-detected by walking up to .claude-plugin/marketplace.json.
Exit 0 = all valid, 1 = problems. Stdlib only."""
import argparse
import glob
import json
import os
import re
import sys

CMD_RE = re.compile(r"^/[a-z][a-z0-9-]*:[a-z][a-z0-9-]*$")
SEAT_KEYS = ("id", "role", "reads", "writes", "commands", "deliverable",
             "handoff_check")


def find_suite(start):
    d = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(d, ".claude-plugin", "marketplace.json")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def known_commands(suite_root):
    if not suite_root:
        return None
    cmds = set()
    for p in glob.glob(os.path.join(suite_root, "plugins", "*", "commands", "*.md")):
        p = p.replace(os.sep, "/")
        cmds.add("/%s:%s" % (p.split("/")[-3], os.path.basename(p)[:-3]))
    return cmds or None


def validate_room(data, label, known=None):
    problems = []

    def bad(msg):
        problems.append("%s: %s" % (label, msg))

    if data.get("schema") != "solo-suite/agentroom-v1":
        bad("schema must be 'solo-suite/agentroom-v1' (got %r)" % data.get("schema"))
    if not (isinstance(data.get("name"), str) and data.get("name").strip()):
        bad("missing non-empty 'name'")
    stages, seats = data.get("stages"), data.get("seats")
    if not (isinstance(stages, list) and stages
            and all(isinstance(g, list) and g for g in stages)):
        bad("'stages' must be a non-empty list of non-empty seat-id lists")
        return problems
    if not (isinstance(seats, list) and seats):
        bad("'seats' must be a non-empty list")
        return problems

    ids = [s.get("id") for s in seats]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        bad("duplicate seat id %r" % dup)
    idset = set(ids)

    stage_of = {}
    for i, group in enumerate(stages):
        for sid in group:
            if sid not in idset:
                bad("stage %d lists unknown seat %r" % (i + 1, sid))
            if sid in stage_of:
                bad("seat %r appears in stage %d AND stage %d — a seat belongs to "
                    "exactly one stage" % (sid, stage_of[sid] + 1, i + 1))
            else:
                stage_of[sid] = i
    for sid in sorted(idset - set(stage_of)):
        bad("seat %r is not placed in any stage" % sid)

    for s in seats:
        sid = s.get("id", "?")
        for k in SEAT_KEYS:
            if k not in s:
                bad("seat %r missing key %r" % (sid, k))
        tgt = s.get("handoff_to")
        if tgt is not None:
            if tgt not in idset:
                bad("seat %r hands off to unknown seat %r" % (sid, tgt))
            elif sid in stage_of and tgt in stage_of:
                if stage_of[tgt] == stage_of[sid]:
                    bad("seat %r hands off to %r in the SAME stage — parallel seats "
                        "must hand off to a later stage (or split the stage)"
                        % (sid, tgt))
                elif stage_of[tgt] < stage_of[sid]:
                    bad("seat %r hands off BACKWARD to %r (stage %d -> %d) — loops "
                        "must use the explicit 'loop' block"
                        % (sid, tgt, stage_of[sid] + 1, stage_of[tgt] + 1))

    for i, group in enumerate(stages):
        writers = {}
        for s in seats:
            if s.get("id") in group:
                for w in s.get("writes") or []:
                    writers.setdefault(w, []).append(s["id"])
        for w, who in sorted(writers.items()):
            if len(who) > 1:
                bad("stage %d: artifact %r written by %s — one writer per artifact "
                    "per stage" % (i + 1, w, " and ".join(who)))

    if not (isinstance(data.get("exit_criteria"), str)
            and data.get("exit_criteria").strip()):
        bad("missing non-empty 'exit_criteria'")
    gate = data.get("exit_gate", "__MISSING__")
    if gate == "__MISSING__":
        bad("missing 'exit_gate' key (use null plus 'exit_gate_note' if a room is "
            "deliberately gateless)")
    elif gate is None:
        if not (isinstance(data.get("exit_gate_note"), str)
                and data.get("exit_gate_note").strip()):
            bad("'exit_gate' is null with no 'exit_gate_note' documenting why")
    elif not (isinstance(gate, str) and CMD_RE.match(gate)):
        bad("'exit_gate' %r is not a /plugin:command reference" % gate)

    refs = []
    for s in seats:
        refs += [(s.get("id", "?"), c) for c in (s.get("commands") or [])]
        if s.get("handoff_check") is not None:
            refs.append((s.get("id", "?"), s.get("handoff_check")))
    if isinstance(gate, str) and gate != "__MISSING__":
        refs.append(("exit_gate", gate))
    for who, c in refs:
        if not (isinstance(c, str) and CMD_RE.match(c)):
            bad("%s: %r is not a /plugin:command reference" % (who, c))
        elif known is not None and c not in known:
            bad("%s: command %s does not exist in this suite" % (who, c))

    loop = data.get("loop")
    if loop is not None:
        rep = loop.get("repeat_stages")
        if not (isinstance(rep, list) and rep
                and all(isinstance(g, list) and g for g in rep)):
            bad("'loop.repeat_stages' must be a non-empty list of seat-id lists")
        else:
            for g in rep:
                for sid in g:
                    if sid not in idset:
                        bad("loop repeats unknown seat %r" % sid)
        if not (isinstance(loop.get("until"), str) and loop.get("until").strip()):
            bad("'loop.until' must state the loop exit condition")
    return problems


def validate_files(paths, suite_root=None):
    known = known_commands(suite_root)
    problems = []
    for path in paths:
        label = os.path.basename(path)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            problems.append("%s: invalid JSON (%s)" % (label, e))
            continue
        problems += validate_room(data, label, known)
    return problems


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rooms", nargs="*",
                    help="room JSON files (default: bundled agentsrooms/*.json)")
    ap.add_argument("--suite", default=None,
                    help="suite root for command-existence checks (default: auto)")
    args = ap.parse_args(argv)
    rooms = args.rooms or sorted(glob.glob(os.path.join(here, "..", "agentsrooms", "*.json")))
    if not rooms:
        print("no room templates found")
        return 1
    suite = args.suite or find_suite(here)
    if not suite:
        print("note: suite root not found — command existence not checked")
    problems = validate_files(rooms, suite_root=suite)
    print("== agentroom validation ==")
    for r in rooms:
        name = os.path.basename(r)
        mine = [p for p in problems if p.startswith(name + ":")]
        if not mine:
            print("PASS  %s" % name)
    for p in problems:
        print("FAIL  %s" % p)
    print("== %d template(s), %d problem(s) ==" % (len(rooms), len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
