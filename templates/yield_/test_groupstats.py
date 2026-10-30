import random
import unittest

from . import groupstats as gs


def _rows(seed=3, n=600):
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        tool = rng.choice(["T1", "T2", "T3"])
        shift = rng.choice(["D", "N"])
        p = 0.25 if tool == "T3" else 0.05  # T3에 불량이 몰림, shift는 무관
        rows.append({"tool": tool, "shift": shift, "result": "FAIL" if rng.random() < p else "PASS"})
    return rows


class TestGroupStats(unittest.TestCase):
    def test_chi2_sf_reference_values(self):
        self.assertAlmostEqual(gs.chi2_sf(3.841, 1), 0.05, places=3)
        self.assertAlmostEqual(gs.chi2_sf(9.488, 4), 0.05, places=3)
        self.assertAlmostEqual(gs.chi2_sf(6.635, 1), 0.01, places=3)
        self.assertAlmostEqual(gs.chi2_sf(2.0, 2), 0.36787944, places=6)  # exp(-1)
        self.assertEqual(gs.chi2_sf(0.0, 3), 1.0)

    def test_chi_square_known_table(self):
        res = gs.chi_square([[10, 20], [30, 40]])
        self.assertAlmostEqual(res["chi2"], 0.7937, places=3)
        self.assertEqual(res["dof"], 1)
        self.assertAlmostEqual(res["p_value"], 0.373, places=2)

    def test_low_expected_warning_and_dof0(self):
        self.assertTrue(gs.chi_square([[1, 2], [3, 1]])["warnings"])
        self.assertIsNone(gs.chi_square([[5, 0], [7, 0]])["p_value"])

    def test_yates_and_expected_lt1(self):
        # 2×2에서 보정 전후로 0.05 판정이 뒤집히는 예: 보정 없음 p≈0.048, Yates p≈0.075
        res = gs.chi_square([[90, 10], [80, 20]])
        self.assertLess(res["p_value"], 0.05)
        self.assertAlmostEqual(res["p_value_yates"], 0.075, places=2)
        self.assertIsNone(gs.chi_square([[1, 2, 3], [4, 5, 6]])["p_value_yates"])
        self.assertTrue(any("기대도수<1" in w for w in gs.chi_square([[0, 1], [30, 40]])["warnings"]))

    def test_rank_factors_ignores_tiny_group_by_default(self):
        # 회귀: 예전 min_n=1 기본값이면 불량 1건뿐인 그룹 A(n=1, 100%)가 top_group
        rows = [{"f": "A", "r": "FAIL"}] + [{"f": g, "r": "FAIL" if i % 10 == 0 else "PASS"}
                                            for g in "BC" for i in range(50)]
        self.assertNotEqual(gs.rank_factors(rows, ["f"], "r")[0]["top_group"], "A")

    def test_defect_rate_by(self):
        rows = [{"t": "A", "r": "NG"}, {"t": "A", "r": "OK"}, {"t": "B", "r": "OK"}, {"t": "B", "r": "?"}]
        out = gs.defect_rate_by(rows, "t", "r")
        self.assertEqual(out[0]["group"], "A")
        self.assertEqual((out[0]["n"], out[0]["bad"]), (2, 1))
        self.assertAlmostEqual(out[0]["lift"], 1.5)
        self.assertEqual(out[1]["n"], 1)  # '?'는 판단 불가로 제외
        self.assertEqual(gs.contingency(rows, "t", "r")[2], 1)

    def test_rank_factors_finds_tool(self):
        ranked = gs.rank_factors(_rows(), ["shift", "tool"], "result", min_n=30)
        self.assertEqual(ranked[0]["factor"], "tool")
        self.assertEqual(ranked[0]["top_group"], "T3")
        self.assertLess(ranked[0]["p_value"], 0.001)
        self.assertGreater(ranked[1]["p_value"], 0.01)

    def test_untestable_factor_is_kept(self):
        rows = _rows(n=100)
        ranked = gs.rank_factors(rows, ["tool", "nothing"], "result", min_n=1)
        last = ranked[-1]
        self.assertEqual((last["factor"], last["p_value"]), ("nothing", None))  # 모든 행이 한 수준(None)
        ranked = gs.rank_factors(rows, ["tool"], "result", min_n=10000)
        self.assertIsNone(ranked[0]["p_value"])
        self.assertTrue(ranked[0]["warnings"])

    def test_float_string_labels(self):
        rows = [{"g": "A", "r": "1.0"}, {"g": "A", "r": "0.0"}, {"g": "B", "r": "0"}, {"g": "B", "r": "2.0"}]
        _, table, unknown = gs.contingency(rows, "g", "r")
        self.assertEqual((table, unknown), ([[1, 1], [1, 0]], 1))

    def test_callable_flag(self):
        rows = [{"g": 1, "v": 9.5}, {"g": 1, "v": 1.0}, {"g": 2, "v": 0.5}]
        out = gs.defect_rate_by(rows, "g", lambda r: r["v"] > 5)
        self.assertEqual(out[0]["group"], 1)


class TestYieldSummary(unittest.TestCase):
    def test_errors_counted_and_weighted_yield(self):
        rows = [
            {"lot": "L1", "wafer": 1, "tool": "A", "tested": 100, "passed": 90},
            {"lot": "L1", "wafer": 2, "tool": "A", "tested": 300, "passed": 150},
            {"lot": "L1", "wafer": 2, "tool": "A", "tested": 100, "passed": 100},   # 키 중복
            {"lot": "L2", "wafer": 1, "tool": "B", "tested": "", "passed": 5},       # 결측
            {"lot": "L2", "wafer": 2, "tool": "B", "tested": 10, "passed": 11},      # passed > tested
            {"lot": "L2", "wafer": 3, "tool": "B", "tested": 50, "passed": 45},
        ]
        r = gs.yield_summary(rows, key=["lot", "wafer"], tested="tested", passed="passed", group="tool")
        self.assertFalse(r["ok"])
        self.assertEqual(r["errors"], {"duplicate_key": 1, "missing": 1, "passed_gt_tested": 1})
        self.assertEqual(r["error_rows"]["duplicate_key"], [2])
        a = r["groups"][0]
        self.assertEqual((a["group"], a["tested"], a["passed"]), ("A", 400, 240))
        self.assertAlmostEqual(a["yield"], 0.6)                 # 가중(240/400), 단순 평균(0.7) 아님
        self.assertIn("원인 아님", r["note"])
        self.assertTrue(gs.yield_summary(rows[:2], ["lot", "wafer"], "tested", "passed")["ok"])


if __name__ == "__main__":
    unittest.main()
