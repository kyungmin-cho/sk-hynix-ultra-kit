import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime

from . import logparse as lp

LOG = """2026-10-31 10:00:00,120 [INFO] EQP01 run started
2026-10-31 10:00:05 [ERROR] EQP01 E1234 chamber pressure high
2026-10-31 10:00:20 [ERROR] EQP01 E1234 chamber pressure high

    at module.step(foo.py:12)
2026-10-31 10:00:40 [ERROR] EQP02 E2001 vacuum fault
2026-10-31 10:05:00 [ERROR] EQP01 E1234 chamber pressure high
2026-13-31 10:06:00 [WARN] EQP02 W100 bad month
2026-10-31 10:04:00 [INFO] EQP02 out of order line
"""


class TestLogParse(unittest.TestCase):
    def _parse(self, text=LOG):
        st = lp.ParseStats()
        recs = list(lp.parse_lines(io.StringIO(text), lp.make_parser(regex="bracket"), st))
        return recs, st

    def test_regex_fields_and_stats(self):
        recs, st = self._parse()
        self.assertEqual(recs[0]["level"], "INFO")
        self.assertIsNone(recs[0]["code"])
        self.assertEqual((recs[1]["source"], recs[1]["code"], recs[1]["msg"]), ("EQP01", "E1234", "chamber pressure high"))
        self.assertEqual(recs[0]["_ts"], datetime(2026, 10, 31, 10, 0, 0, 120000))
        self.assertEqual((st["n_lines"], st["n_blank"], st["n_ok"], st["n_failed"]), (9, 1, 7, 1))
        self.assertEqual(st["fail_samples"][0][0], 5)          # 실패 줄 번호가 남는다
        self.assertEqual((st["n_bad_ts"], st["out_of_order"]), (1, 1))
        self.assertAlmostEqual(st["fail_rate"], 1 / 8, places=4)

    def test_count_by_carries_parse_stats(self):
        st = lp.ParseStats()
        out = lp.count_by(lp.parse_lines(io.StringIO(LOG), lp.make_parser(regex="bracket"), st), ["level", "code"], st)
        self.assertEqual(out["counts"][0], {"level": "ERROR", "code": "E1234", "count": 3})
        self.assertEqual(out["parse"]["n_failed"], 1)            # 실패 수가 결과와 같이 다닌다
        self.assertEqual(lp.count_by([], ["level"])["parse"], "NOT_REPORTED")

    def test_group_events_bursts_and_sessions(self):
        recs, _ = self._parse()
        is_err = lambda r: r["level"] == "ERROR"
        bursts = lp.group_events(recs, gap_s=60, pred=is_err, min_count=2, key="source")
        self.assertEqual(len(bursts), 1)
        self.assertEqual((bursts[0]["key"], bursts[0]["count"], bursts[0]["duration_s"]), ("EQP01", 2, 15.0))
        sessions = lp.group_events(recs, gap_s=60)
        self.assertEqual([g["count"] for g in sessions], [4, 2])  # 10:00 묶음, 10:05 + 역순 10:04
        self.assertEqual(sessions[1]["start"], datetime(2026, 10, 31, 10, 4))

    def test_delimiter_and_fixed_width(self):
        p = lp.make_parser(delimiter="|", fields=["ts", "eqp", "code", "msg"])
        r = p("2026-10-31T10:00:00Z| EQP1 |A10| msg | with pipe")
        self.assertEqual((r["eqp"], r["msg"]), ("EQP1", "msg | with pipe"))
        self.assertIsNone(p("only|two"))
        fw = lp.make_parser(widths=[19, 6, 5, 40], fields=["ts", "eqp", "code", "msg"])
        r = fw("2026-10-31 10:00:00EQP01 A123 free text")
        self.assertEqual((r["eqp"], r["code"], r["msg"]), ("EQP01", "A123", "free text"))
        self.assertIsNone(fw("short"))
        self.assertEqual(lp.parse_kv('lvl=WARN eqp=E1 msg="x y"'), {"lvl": "WARN", "eqp": "E1", "msg": "x y"})

    def test_mixed_tz_does_not_crash(self):
        text = "2026-10-31 10:00:00 [INFO] A x\n2026-10-31 01:00:01Z [INFO] A y\n"
        recs, st = self._parse(text)
        self.assertEqual((len(recs), st["mixed_tz"]), (2, 1))

    def test_main_and_standalone_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.log")
            with open(p, "w", encoding="utf-8") as f:
                f.write(LOG)
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                self.assertEqual(lp.main([p, "--bursts", "60:2"]), 0)
            self.assertIn("failed=1", err.getvalue())
            empty = os.path.join(d, "e.log")
            open(empty, "w").close()
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(lp.main([empty]), 2)
            script = os.path.join(os.path.dirname(os.path.abspath(lp.__file__)), "logparse.py")
            r = subprocess.run([sys.executable, script, p, "--bursts", "60:2"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("bad_ts=1", r.stderr)                   # 폴백 parse_ts도 13월을 거부
            self.assertIn('"count": 2', r.stdout)


if __name__ == "__main__":
    unittest.main()
