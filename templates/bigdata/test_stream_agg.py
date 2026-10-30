import csv
import io
import math
import os
import random
import statistics
import subprocess
import sys
import tempfile
import tracemalloc
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta

from .. import _common
from . import stream_agg as sa

N_BIG = 200_000


def _write(path, n, seed=0):
    """합성 CSV: id(고유), tool(10수준), lot(2000수준), thk(실수, 2% 결측·1% 'ERR'). 기대값도 같이 돌려준다."""
    rng = random.Random(seed)
    vals, missing, bad = [], 0, 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "tool", "lot", "thk"])
        for i in range(n):
            u = rng.random()
            if u < 0.02:
                v, missing = "", missing + 1
            elif u < 0.03:
                v, bad = "ERR", bad + 1
            else:
                x = round(rng.gauss(100.0, 5.0), 3)
                v = repr(x)
                vals.append(x)
            w.writerow([i, "T%d" % rng.randrange(10), "L%04d" % rng.randrange(2000), v])
    return vals, missing, bad


class TestStreamAgg(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.big = os.path.join(cls.tmp.name, "big.csv")
        cls.vals, cls.missing, cls.bad = _write(cls.big, N_BIG)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_profile_big_file_exact(self):
        p = sa.profile(_common.stream_csv(self.big), max_distinct=500)
        self.assertEqual(p["n_rows"], N_BIG)
        thk = p["columns"]["thk"]
        self.assertEqual((thk["missing"], thk["n_bad"], thk["n_num"]), (self.missing, self.bad, len(self.vals)))
        self.assertAlmostEqual(thk["mean"], statistics.fmean(self.vals), places=6)
        self.assertAlmostEqual(thk["std"], statistics.stdev(self.vals), places=6)
        self.assertEqual((thk["min"], thk["max"]), (min(self.vals), max(self.vals)))
        self.assertEqual(p["columns"]["tool"]["distinct"], 10)
        self.assertTrue(p["columns"]["id"]["distinct_capped"])        # 고유 id는 상한에서 멈춤
        self.assertEqual(p["columns"]["id"]["distinct"], 500)

    def test_group_agg_memory_equals_sqlite_spill(self):
        mem = sa.group_agg(_common.stream_csv(self.big), ["tool", "lot"], "thk", method="memory")
        spill = sa.group_agg(_common.stream_csv(self.big), ["tool", "lot"], "thk", max_groups=300, chunk=7000)
        self.assertEqual((mem["meta"]["engine"], spill["meta"]["engine"]), ("memory", "sqlite"))
        self.assertIsNotNone(spill["meta"]["spilled_at_row"])
        for m in (mem["meta"], spill["meta"]):
            self.assertEqual((m["n_rows"], m["n_missing"], m["n_bad"]), (N_BIG, self.missing, self.bad))
        self.assertEqual(len(mem["groups"]), len(spill["groups"]))
        for a, b in zip(mem["groups"], spill["groups"]):
            self.assertEqual((a["key"], a["n"], a["n_value"], a["min"], a["max"]), (b["key"], b["n"], b["n_value"], b["min"], b["max"]))
            self.assertAlmostEqual(a["mean"], b["mean"], places=6)
            if a["std"] is not None:
                self.assertAlmostEqual(a["std"], b["std"], places=5)
        self.assertEqual(sum(g["n"] for g in mem["groups"]), N_BIG)

    def test_group_agg_small_exact(self):
        rows = [{"g": "a", "v": "1"}, {"g": "a", "v": "3"}, {"g": "b", "v": "x"}, {"g": "b", "v": ""}, {"g": "a", "v": "1,000"}]
        for method in ("memory", "sqlite"):
            res = sa.group_agg(rows, ["g"], "v", method=method)
            a, b = res["groups"]
            self.assertEqual((a["key"], a["n"], a["n_value"], a["sum"], a["min"], a["max"]), (("a",), 3, 3, 1004.0, 1.0, 1000.0))
            self.assertAlmostEqual(a["std"], statistics.stdev([1, 3, 1000]), places=6)
            self.assertEqual((b["n"], b["n_value"], b["mean"], b["sum"]), (2, 0, None, None))  # 비숫자를 0으로 세지 않음
            self.assertEqual((res["meta"]["n_bad"], res["meta"]["n_missing"]), (1, 1))

    def test_reservoir_deterministic_and_uniform(self):
        s1 = sa.reservoir_sample(range(100_000), 1000, seed=1)
        self.assertEqual(s1, sa.reservoir_sample(range(100_000), 1000, seed=1))
        self.assertEqual((len(s1), len(set(s1))), (1000, 1000))
        self.assertLess(abs(statistics.fmean(s1) - 50_000), 3_000)
        self.assertEqual(sa.reservoir_sample(range(5), 10), [0, 1, 2, 3, 4])

    def test_external_sort_matches_sorted(self):
        rng = random.Random(3)
        rows = [{"t": rng.randrange(5000), "i": i} for i in range(20_000)]
        out = list(sa.external_sort(iter(rows), key=lambda r: r["t"], chunk=1500))
        self.assertEqual(out, sorted(rows, key=lambda r: r["t"]))  # 안정 정렬까지 같음
        self.assertEqual([len(b) for b in sa.chunked(range(7), 3)], [3, 3, 1])

    def test_external_sort_keeps_datetime_records(self):
        # logparse 레코드처럼 _ts(datetime)·None·tuple이 든 dict도 그대로 정렬된다.
        rng = random.Random(5)
        base = datetime(2026, 10, 31, 10, 0)
        rows = [{"_ts": base + timedelta(seconds=rng.randrange(3600)), "_line": i, "code": None, "k": (i % 3, "a")}
                for i in range(3000)]
        out = list(sa.external_sort(rows, key=lambda r: r["_ts"], chunk=400))
        self.assertEqual(out, sorted(rows, key=lambda r: r["_ts"]))
        self.assertIsInstance(out[0]["_ts"], datetime)
        self.assertEqual(out[0]["k"].__class__, tuple)

    def test_memory_constant_in_rows(self):
        peaks = []
        for n in (10_000, 40_000):
            path = os.path.join(self.tmp.name, "m%d.csv" % n)
            _write(path, n, seed=n)
            tracemalloc.start()
            sa.profile(_common.stream_csv(path), max_distinct=200)
            sa.group_agg(_common.stream_csv(path), ["tool"], "thk")
            peaks.append(tracemalloc.get_traced_memory()[1])
            tracemalloc.stop()
        self.assertLess(peaks[1] / peaks[0], 1.5, peaks)             # 행 4배 → 최대 메모리 거의 같음

    def test_cli_and_standalone_fallback(self):
        script = os.path.join(os.path.dirname(os.path.abspath(sa.__file__)), "stream_agg.py")
        out = os.path.join(self.tmp.name, "sample.csv")
        r = subprocess.run([sys.executable, script, self.big, "--sample", "50", "--out", out, "--limit", "5000"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, encoding="utf-8") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 50)
        r = subprocess.run([sys.executable, script, self.big, "--by", "tool", "--value", "thk", "--limit", "1000"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('"n_groups": 10', r.stdout)
        empty = os.path.join(self.tmp.name, "empty.csv")
        with open(empty, "w") as f:
            f.write("a,b\n")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(sa.main([empty]), 2)
            self.assertEqual(sa.main([os.path.join(self.tmp.name, "none.csv")]), 2)


    def test_std_precise_with_large_mean(self):
        # 회귀: sumsq 공식이면 1e9+{1,2,3}의 std가 0.0(자릿수 손실). 정답 1.0
        rows = [{"k": "a", "v": str(1e9 + x)} for x in (1, 2, 3)]
        for method in ("auto", "sqlite"):
            g = sa.group_agg(iter(rows), ["k"], "v", method=method)["groups"][0]
            self.assertAlmostEqual(g["std"], 1.0, places=6, msg=method)
            self.assertAlmostEqual(g["mean"], 1e9 + 2)
            self.assertAlmostEqual(g["sum"], 3e9 + 6)

    def test_unwritable_spill_dir_is_clear_error(self):
        rows = ({"k": str(i), "v": "1"} for i in range(5))
        with self.assertRaises(RuntimeError) as cm:
            sa.group_agg(rows, ["k"], "v", max_groups=2, tmpdir=os.path.join(self.tmp.name, "no", "such"))
        self.assertIn("tmpdir", str(cm.exception))

    def test_standalone_fallback_reads_tsv_and_cp949(self):
        # 파일만 따로 옮겨 실행했을 때(_common 없음) TSV를 열 1개로 읽거나 cp949에서 예외가 나지 않아야 한다
        d = os.path.join(self.tmp.name, "alone")
        os.makedirs(d)
        script = os.path.join(d, "stream_agg.py")
        with open(os.path.join(os.path.dirname(os.path.abspath(sa.__file__)), "stream_agg.py"), encoding="utf-8") as f, \
                open(script, "w", encoding="utf-8") as g:
            g.write(f.read())
        tsv = os.path.join(d, "x.tsv")
        with open(tsv, "w", encoding="cp949") as f:
            f.write("설비\t두께\nA\t1\nA\t3\n나\t5\n")
        r = subprocess.run([sys.executable, script, tsv, "--by", "설비", "--value", "두께"],
                           capture_output=True, text=True, cwd=d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('"n_groups": 2', r.stdout)


if __name__ == "__main__":
    unittest.main()
