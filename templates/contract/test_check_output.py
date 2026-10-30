import csv
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from . import check_output as co

SPEC = {"rows": {"min": 1, "max": 100},
        "columns": {"id": {"type": "int", "nullable": False},
                    "score": {"type": "float", "min": 0, "max": 1},
                    "label": {"type": "str", "allowed": ["OK", "NG"]},
                    "ts": {"type": "datetime", "required": False}},
        "unique": [["id"]]}


class TestCheckOutput(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def _csv(self, rows, name="out.csv", header=None):
        p = os.path.join(self.tmp.name, name)
        with open(p, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header or list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        return p

    def _run(self, path, spec=SPEC):
        sp = os.path.join(self.tmp.name, "spec.json")
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(spec, f)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = co.main([path, "--spec", sp])
        return code, buf.getvalue()

    def test_pass_exit0_with_fixture(self):
        rows = co.gen_fixture(SPEC, n=20)
        code, out = self._run(self._csv(rows))
        self.assertEqual(code, 0, out)
        self.assertIn("0 failed", out)

    def test_fail_exit1(self):
        rows = co.gen_fixture(SPEC, n=5)
        rows[1]["score"] = 1.5
        rows[2]["label"] = "MAYBE"
        rows[3]["id"] = rows[0]["id"]
        rows[4]["id"] = ""
        rep = co.check(co.load_rows(self._csv(rows)), SPEC)
        self.assertEqual(rep["exit_code"], 1)
        failed = {c["name"] for c in rep["checks"] if not c["ok"]}
        self.assertEqual(failed, {"score: in [0, 1]", "label: allowed ['NG', 'OK']", "unique ['id']", "id: not null"})
        self.assertEqual(self._run(self._csv(rows))[0], 1)

    def test_type_and_missing_column(self):
        rows = [{"id": "x1", "score": "abc", "label": "OK"}]
        rep = co.check(rows, SPEC)
        failed = {c["name"] for c in rep["checks"] if not c["ok"]}
        self.assertIn("id: type int", failed)
        self.assertIn("score: type float", failed)
        rep = co.check([{"id": 1}], {"columns": {"score": {}}})
        self.assertEqual((rep["exit_code"], rep["checks"][0]["name"]), (1, "score: present"))

    def test_exit2_cases(self):
        self.assertEqual(self._run(os.path.join(self.tmp.name, "missing.csv"))[0], 2)  # 파일 없음
        header_only = self._csv([], name="h.csv", header=["id", "score", "label"])
        self.assertEqual(self._run(header_only)[0], 2)  # 0행
        good = self._csv(co.gen_fixture(SPEC, n=3))
        self.assertEqual(self._run(good, spec={})[0], 2)  # 검사 0건
        bad_json = os.path.join(self.tmp.name, "bad.json")
        with open(bad_json, "w") as f:
            f.write("{not json")
        self.assertEqual(self._run(bad_json)[0], 2)  # 읽기 실패

    def test_json_inputs_and_exact_columns(self):
        rows = co.gen_fixture(SPEC, n=4)
        p = os.path.join(self.tmp.name, "o.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"rows": rows}, f)
        self.assertEqual(co.check(co.load_rows(p), SPEC)["exit_code"], 0)
        pl = os.path.join(self.tmp.name, "o.jsonl")
        with open(pl, "w", encoding="utf-8") as f:
            f.write("\n".join(json.dumps(r) for r in rows))
        rows2 = co.load_rows(pl)
        rows2[0]["extra"] = 1
        rep = co.check(rows2, dict(SPEC, exact_columns=True))
        self.assertEqual(rep["exit_code"], 1)
        self.assertEqual(co.check([{"flag": True, "n": True}], {"columns": {"n": {"type": "int"}}})["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
