"""AgentRooms validator tests — the four bundled templates must pass, and each
rule must catch a synthetic violation."""
import copy
import glob
import importlib.util
import os
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VPATH = os.path.join(REPO, "plugins", "ai", "skills", "agent-room-templates",
                     "scripts", "validate_rooms.py")
spec = importlib.util.spec_from_file_location("validate_rooms", VPATH)
vr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vr)


def seat(sid, handoff, writes):
    return {"id": sid, "role": "r", "reads": [], "writes": writes,
            "commands": ["/gate:before-code"], "deliverable": "d",
            "handoff_to": handoff, "handoff_check": "/ai:handoff-check"}


def base_room():
    return {
        "schema": "solo-suite/agentroom-v1", "name": "t",
        "stages": [["a"], ["b"]],
        "seats": [seat("a", "b", ["x.md"]), seat("b", None, ["y.md"])],
        "exit_gate": "/gate:before-code",
        "exit_criteria": "done",
    }


class BundledTemplates(unittest.TestCase):
    def test_all_bundled_templates_valid(self):
        rooms = sorted(glob.glob(os.path.join(
            REPO, "plugins", "*", "skills", "*", "agentsrooms", "*.json")))
        self.assertEqual(len(rooms), 4)
        self.assertEqual(vr.validate_files(rooms, suite_root=REPO), [])


class Rules(unittest.TestCase):
    def check(self, room, fragment):
        problems = vr.validate_room(room, "t.json")
        self.assertTrue(any(fragment in p for p in problems),
                        "expected %r in %r" % (fragment, problems))

    def test_valid_base(self):
        self.assertEqual(vr.validate_room(base_room(), "t.json"), [])

    def test_same_stage_handoff(self):
        r = base_room()
        r["stages"] = [["a", "b"]]
        self.check(r, "SAME stage")

    def test_backward_handoff(self):
        r = base_room()
        r["seats"][0]["handoff_to"] = None
        r["seats"][1]["handoff_to"] = "a"
        self.check(r, "BACKWARD")

    def test_seat_in_two_stages(self):
        r = base_room()
        r["stages"] = [["a"], ["b", "a"]]
        self.check(r, "exactly one stage")

    def test_seat_in_no_stage(self):
        r = base_room()
        r["seats"].append(seat("c", None, ["z.md"]))
        self.check(r, "not placed in any stage")

    def test_unknown_stage_member(self):
        r = base_room()
        r["stages"][0] = ["a", "ghost"]
        self.check(r, "unknown seat 'ghost'")

    def test_handoff_target_missing(self):
        r = base_room()
        r["seats"][0]["handoff_to"] = "ghost"
        self.check(r, "unknown seat 'ghost'")

    def test_duplicate_writer_same_stage(self):
        r = base_room()
        r["stages"] = [["a", "b"], ["c"]]
        r["seats"] = [seat("a", "c", ["same.md"]), seat("b", "c", ["same.md"]),
                      seat("c", None, ["z.md"])]
        self.check(r, "one writer per artifact")

    def test_null_gate_needs_note(self):
        r = base_room()
        r["exit_gate"] = None
        self.check(r, "exit_gate_note")

    def test_null_gate_with_note_ok(self):
        r = base_room()
        r["exit_gate"] = None
        r["exit_gate_note"] = "advisory room; no blocking gate by design"
        self.assertEqual(vr.validate_room(r, "t.json"), [])

    def test_missing_exit_criteria(self):
        r = base_room()
        r["exit_criteria"] = "  "
        self.check(r, "exit_criteria")

    def test_missing_gate_key(self):
        r = base_room()
        del r["exit_gate"]
        self.check(r, "missing 'exit_gate' key")

    def test_loop_unknown_seat(self):
        r = base_room()
        r["loop"] = {"repeat_stages": [["ghost"]], "until": "fixed"}
        self.check(r, "loop repeats unknown seat")

    def test_loop_needs_until(self):
        r = base_room()
        r["loop"] = {"repeat_stages": [["a"]], "until": " "}
        self.check(r, "loop.until")

    def test_command_existence_with_suite(self):
        r = base_room()
        r["seats"][0]["commands"] = ["/nope:not-a-command"]
        problems = vr.validate_room(r, "t.json", known=vr.known_commands(REPO))
        self.assertTrue(any("does not exist" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
