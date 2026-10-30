import importlib.util
import math
import random
import unittest
from fractions import Fraction

from . import features as ft

HAS_PANDAS = importlib.util.find_spec("pandas") is not None


def _rows():
    rng = random.Random(5)
    rows = []
    for eq in ("E1", "E2", "E3"):
        for t in range(12):
            v = None if (eq == "E2" and t == 4) else round(rng.uniform(0, 10), 3)
            rows.append({"eq": eq, "t": t, "v": v})
    rng.shuffle(rows)  # 엔터티·시간 순서를 섞어 정렬·그룹 경계 버그를 드러낸다
    return rows


class TestFeatures(unittest.TestCase):
    def test_csv_string_input(self):
        # 회귀: DictReader는 전부 문자열 → 예전엔 lag·rolling이 전부 None, 시각은 사전순 정렬(1-11이 1-9보다 앞)
        self.assertEqual(ft.shift_then_roll(["1", "2", " 3 ", "", "NA"], 2), [None, 1.0, 1.5, 2.5, 3.0])
        rows = [{"t": "2026-1-9", "v": "1"}, {"t": "2026-1-10", "v": "2"}, {"t": "2026-1-11", "v": "3"}]
        out = ft.add_lag_roll(rows, None, "t", "v")
        self.assertEqual([r["v_lag1"] for r in out], [None, 1.0, 2.0])  # 1-9 행에 미래 값 없음

    @unittest.skipUnless(HAS_PANDAS, "pandas not installed")
    def test_pandas_string_times_sorted_by_time(self):
        import pandas as pd
        df = pd.DataFrame({"t": ["2026-1-11", "2026-1-9", "2026-1-10"], "v": [3.0, 1.0, 2.0]})
        out = ft.pandas_lag_roll(df, None, "t", "v")
        self.assertTrue(math.isnan(out["v_lag1"][1]))  # 1-9 행에 미래 값 없음
        self.assertEqual((out["v_lag1"][2], out["v_lag1"][0]), (1.0, 2.0))

    def test_unparseable_time_raises(self):
        with self.assertRaises(ValueError):
            ft.add_lag_roll([{"t": "어제", "v": "1"}, {"t": "2026-01-01", "v": "2"}], None, "t", "v")

    def test_shift_then_roll_excludes_current(self):
        xs = [1, 2, 3, 4, 100]
        self.assertEqual(ft.shift_then_roll(xs, 2), [None, 1.0, 1.5, 2.5, 3.5])
        self.assertEqual(ft.shift_then_roll(xs, 3, "max", min_periods=3), [None, None, None, 3.0, 4.0])
        self.assertEqual(ft.shift_then_roll([1, None, 3, 5], 2, "sum"), [None, 1.0, 1.0, 3.0])

    def test_other_number_types(self):
        self.assertEqual(ft.shift_then_roll([Fraction(1), Fraction(3), 5], 2), [None, 1.0, 2.0])
        if importlib.util.find_spec("numpy"):
            import numpy as np
            self.assertEqual(ft.shift_then_roll(list(np.array([1, 3, 5], dtype=np.int64)), 2), [None, 1.0, 2.0])

    def test_prefix_invariant(self):
        xs = [float(i % 7) for i in range(50)]
        alt = xs[:30] + [1e9] * 20
        for fn in ("mean", "std", "max"):
            self.assertEqual(ft.shift_then_roll(xs, 5, fn)[:30], ft.shift_then_roll(alt, 5, fn)[:30])

    def test_add_lag_roll_per_entity(self):
        rows = _rows()
        out = ft.add_lag_roll(rows, "eq", "t", "v", lags=(1,), windows=(3,), funcs=("mean", "std"))
        self.assertEqual([r["t"] for r in out], [r["t"] for r in rows])  # 원래 순서 유지
        self.assertNotIn("v_lag1", rows[0])  # 입력 불변
        e1 = sorted((r for r in out if r["eq"] == "E1"), key=lambda r: r["t"])
        self.assertIsNone(e1[0]["v_lag1"])  # 엔터티 첫 행은 이전 값 없음(다른 설비 값이 넘어오지 않음)
        self.assertIsNone(e1[0]["v_roll3_mean"])
        self.assertEqual(e1[5]["v_lag1"], e1[4]["v"])
        self.assertAlmostEqual(e1[5]["v_roll3_mean"], (e1[2]["v"] + e1[3]["v"] + e1[4]["v"]) / 3)
        e2 = sorted((r for r in out if r["eq"] == "E2"), key=lambda r: r["t"])
        self.assertIsNone(e2[5]["v_lag1"])  # 결측의 lag는 결측

    @unittest.skipUnless(HAS_PANDAS, "pandas not installed (stdlib path tested above)")
    def test_pandas_path_matches_stdlib(self):
        import pandas as pd
        rows = _rows()
        args = dict(entity="eq", time="t", value="v", lags=(1, 2), windows=(3, 5), funcs=("mean", "std", "max"))
        ref = ft.add_lag_roll(rows, **args)
        got = ft.pandas_lag_roll(pd.DataFrame(rows), **args).to_dict("records")
        for a, b in zip(ref, got):
            for k, va in a.items():
                vb = b[k]
                if va is None:
                    self.assertTrue(vb is None or (isinstance(vb, float) and math.isnan(vb)), (k, a, b))
                elif isinstance(va, float):
                    self.assertAlmostEqual(va, vb, places=9, msg=k)


if __name__ == "__main__":
    unittest.main()
