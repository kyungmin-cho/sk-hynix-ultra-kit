import csv
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from . import reconcile as rc

A = [{"lot": "L001", "qty": "10", "status": "OK"},
     {"lot": "L002", "qty": "20.0", "status": "OK"},
     {"lot": "L003", "qty": "30", "status": "NG"},
     {"lot": "L004", "qty": "", "status": "OK"}]
B = [{"lot": " l001 ", "qty": "10.004", "status": "OK"},   # 키 표기 차이 + 작은 수치 차
     {"lot": "L002", "qty": "20", "status": "ok"},          # 값 대소문자 차 → 불일치
     {"lot": "L004", "qty": "NA", "status": "OK"},          # 결측 표기만 다름 → 같음
     {"lot": "L005", "qty": "50", "status": "OK"}]


class TestReconcile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def _csv(self, name, rows):
        p = os.path.join(self.tmp.name, name)
        with open(p, "w", newline="", encoding="utf-8") as f:
            if rows:
                w = csv.DictWriter(f, fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)
        return p

    def _main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = rc.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_compare_categories(self):
        res = rc.compare(A, B, ["lot"], tol=0.01)
        s = res["summary"]
        self.assertEqual((s["matched_keys"], s["only_in_a"], s["only_in_b"]), (3, 1, 1))
        self.assertEqual(res["only_in_a"], [{"lot": "L003"}])
        self.assertEqual(res["only_in_b"], [{"lot": "L005"}])
        self.assertEqual([(m["lot"], m["column"]) for m in res["mismatch"]], [("L002", "status")])
        self.assertFalse(s["ok"])

    def test_tolerance_applies_to_string_numbers(self):
        strict = rc.compare(A, B, ["lot"], cols=["qty"])
        self.assertEqual([m["lot"] for m in strict["mismatch"]], ["L001"])  # 10 vs 10.004
        loose = rc.compare(A, B, ["lot"], cols=["qty"], tol={"qty": 0.01})
        self.assertEqual(loose["mismatch"], [])
        rel = rc.compare(A, B, ["lot"], cols=["qty"], rel_tol=1e-3)
        self.assertEqual(rel["mismatch"], [])
        self.assertTrue(rc.values_equal("1,234.5", 1234.5))
        self.assertFalse(rc.values_equal("", "0"))
        codes_a, codes_b = [{"id": "1", "step": "010"}], [{"id": "1", "step": "10"}]
        self.assertEqual(rc.compare(codes_a, codes_b, ["id"])["mismatch"], [])           # 숫자로 보면 같음
        self.assertEqual(len(rc.compare(codes_a, codes_b, ["id"], exact_cols=["step"])["mismatch"]), 1)

    def test_duplicates_and_strip_zeros(self):
        a = [{"id": "007", "v": "1"}, {"id": "7", "v": "1"}]
        b = [{"id": "7", "v": "1"}]
        res = rc.compare(a, b, ["id"], strip_zeros=True)
        self.assertEqual(res["summary"]["dup_a"], 1)
        self.assertFalse(res["summary"]["ok"])
        self.assertTrue(rc.compare(b, b, ["id"])["summary"]["ok"])

    def test_cli_exit_codes(self):
        pa, pb = self._csv("a.csv", A), self._csv("b.csv", B)
        self.assertEqual(self._main(pa, pa, "--key", "lot")[0], 0)
        code, out, _ = self._main(pa, pb, "--key", "lot", "--tol", "0.01")
        self.assertEqual(code, 1)
        self.assertIn("A만 1, B만 1", out)
        self.assertEqual(self._main(pa, os.path.join(self.tmp.name, "none.csv"), "--key", "lot")[0], 2)
        self.assertEqual(self._main(pa, pb, "--key", "wafer")[0], 2)          # 키 열 없음
        self.assertEqual(self._main(pa, self._csv("e.csv", []), "--key", "lot")[0], 2)  # 0행
        disjoint = self._csv("d.csv", [{"lot": "X9", "qty": "1", "status": "OK"}])
        self.assertEqual(self._main(pa, disjoint, "--key", "lot")[0], 2)     # 비교한 키 0개

    def test_standalone_script_fallback(self):
        # 스크립트로 직접 실행하면 상대 import가 실패해 내장 CSV 폴백 경로를 탄다.
        pa, pb = self._csv("a.csv", A), self._csv("b.csv", B)
        path = os.path.join(os.path.dirname(os.path.abspath(rc.__file__)), "reconcile.py")
        p = subprocess.run([sys.executable, path, pa, pb, "--key", "lot", "--json"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1, p.stderr)
        self.assertIn('"only_in_b": 1', p.stdout)


if __name__ == "__main__":
    unittest.main()
