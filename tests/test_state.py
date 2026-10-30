"""init_state.sh 검사: 없는 파일만 만들고, 기존 파일은 덮어쓰지 않으며, STATE 필드를 채운다.
추가 양식(--extra / --with)도 같은 규칙. 차용 없음."""
import hashlib
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "init_state.sh"
FILES = ("TASK", "STATE", "DECISIONS", "HANDOFF")
EXTRA = ("TRIALS", "VERIFICATION", "ESSAY_PREP")


def run(cwd, *args, tz="UTC"):
    env = dict(os.environ, TZ=tz)
    return subprocess.run(["bash", str(SCRIPT), *args], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=30)


def digest(d, files=FILES):
    return {f: hashlib.sha256((Path(d) / f"{f}.md").read_bytes()).hexdigest() for f in files}


class InitStateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ws = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_creates_all_and_fills_state(self):
        r = run(self.ws, "--start", "10:30")
        self.assertEqual(r.returncode, 0, r.stderr)
        for f in FILES:
            self.assertTrue((Path(self.ws) / "notes" / f"{f}.md").is_file())
            self.assertIn(f"created notes/{f}.md", r.stdout)
        state = (Path(self.ws) / "notes" / "STATE.md").read_text(encoding="utf-8")
        self.assertNotIn("{{", state, "placeholder left in STATE.md")
        self.assertRegex(state, r"시작 시각 T0 \(KST\) \| 10:30")
        self.assertRegex(state, r"\| 13:20 \|")          # D = min(13:30, 13:20)
        self.assertIn("T+15 10:45", state)
        self.assertIn("D−30 12:50", state)
        self.assertIn(str(ROOT), state)                  # 하네스 경로
        self.assertRegex(state, r"하네스 커밋 \| ([0-9a-f]{40}|unknown) \|")
        self.assertRegex(state, r"워크스페이스 BASE 커밋 \| ([0-9a-f]{40}|none)")  # presubmit --base 값

    def test_deadline_before_cap(self):
        r = run(self.ws, "--start", "10:00")
        self.assertEqual(r.returncode, 0, r.stderr)
        state = (Path(self.ws) / "notes" / "STATE.md").read_text(encoding="utf-8")
        self.assertRegex(state, r"\| 13:00 \|")

    def test_remaining_min_sets_left(self):
        r = run(self.ws, "--remaining-min", "120")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"잔여 -?\d+분")

    def test_first_line_is_lifecycle_comment(self):
        for f in FILES + EXTRA:
            first = (ROOT / "state" / f"{f}.md").read_text(encoding="utf-8").splitlines()[0]
            self.assertTrue(re.match(r"<!-- 생성: .*갱신: .*읽기: .*-->", first), f)

    def test_never_overwrites(self):
        notes = Path(self.ws) / "notes"
        notes.mkdir()
        (notes / "TASK.md").write_text("my own task\n", encoding="utf-8")
        r = run(self.ws, "--start", "10:00")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("skip    notes/TASK.md", r.stdout)
        self.assertEqual((notes / "TASK.md").read_text(encoding="utf-8"), "my own task\n")
        before = digest(notes)
        r2 = run(self.ws, "--start", "11:11")
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertEqual(r2.stdout.count("skip"), 4)
        self.assertNotIn("created", r2.stdout)
        self.assertEqual(digest(notes), before)

    def test_dest_option(self):
        r = run(self.ws, "--dest", "notes-hx")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((Path(self.ws) / "notes-hx" / "STATE.md").is_file())
        self.assertFalse((Path(self.ws) / "notes").exists())

    def test_bad_args(self):
        self.assertEqual(run(self.ws, "--start", "9am").returncode, 2)
        self.assertEqual(run(self.ws, "--remaining-min", "x").returncode, 2)
        self.assertEqual(run(self.ws, "--remaining-min", "1800").returncode, 2)
        self.assertFalse((Path(self.ws) / "notes").exists())

    def test_default_makes_only_core_four(self):
        r = run(self.ws)
        self.assertEqual(r.returncode, 0, r.stderr)
        made = sorted(p.stem for p in (Path(self.ws) / "notes").glob("*.md"))
        self.assertEqual(made, sorted(FILES))

    def test_extra_makes_seven(self):
        r = run(self.ws, "--extra", "--start", "10:00")
        self.assertEqual(r.returncode, 0, r.stderr)
        for f in FILES + EXTRA:
            self.assertIn(f"created notes/{f}.md", r.stdout)
            self.assertEqual((Path(self.ws) / "notes" / f"{f}.md").read_bytes()[:4], b"<!--")
        self.assertEqual((Path(self.ws) / "notes" / "TRIALS.md").read_text(encoding="utf-8"),
                         (ROOT / "state" / "TRIALS.md").read_text(encoding="utf-8"))

    def test_with_subset_and_dedup(self):
        r = run(self.ws, "--with", "essay,trials", "--with", "essay")
        self.assertEqual(r.returncode, 0, r.stderr)
        notes = Path(self.ws) / "notes"
        self.assertTrue((notes / "ESSAY_PREP.md").is_file())
        self.assertTrue((notes / "TRIALS.md").is_file())
        self.assertFalse((notes / "VERIFICATION.md").exists())
        self.assertEqual(r.stdout.count("created notes/ESSAY_PREP.md"), 1)

    def test_extra_later_never_overwrites(self):
        self.assertEqual(run(self.ws, "--start", "10:00").returncode, 0)
        notes = Path(self.ws) / "notes"
        (notes / "DECISIONS.md").write_text("my decisions\n", encoding="utf-8")
        before = digest(notes)
        r = run(self.ws, "--extra", "--start", "11:00")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.count("skip"), 4)
        self.assertEqual(r.stdout.count("created"), 3)
        self.assertEqual(digest(notes), before)
        self.assertEqual((notes / "DECISIONS.md").read_text(encoding="utf-8"), "my decisions\n")
        before7 = digest(notes, FILES + EXTRA)
        r = run(self.ws, "--extra")
        self.assertEqual(r.stdout.count("skip"), 7)
        self.assertEqual(digest(notes, FILES + EXTRA), before7)

    def test_with_unknown_name_rejected_before_writing(self):
        r = run(self.ws, "--with", "trials,bogus")
        self.assertEqual(r.returncode, 2)
        self.assertIn("bogus", r.stderr)
        self.assertFalse((Path(self.ws) / "notes").exists())

    def test_extra_templates_point_to_fallback(self):
        for f, fallback in (("TRIALS", "DECISIONS.md` §2"), ("VERIFICATION", "DECISIONS.md` §3"),
                            ("ESSAY_PREP", "HANDOFF.md` §5")):
            self.assertIn(fallback, (ROOT / "state" / f"{f}.md").read_text(encoding="utf-8"), f)


if __name__ == "__main__":
    unittest.main()
