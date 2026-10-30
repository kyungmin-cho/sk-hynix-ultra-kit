import random
import unittest

from . import spc


class TestImr(unittest.TestCase):
    def test_fit_known_values(self):
        lim = spc.imr_fit([10, 12, 11, 13, 12])
        self.assertAlmostEqual(lim["mr_bar"], 1.5)
        self.assertAlmostEqual(lim["center"], 11.6)
        self.assertAlmostEqual(lim["ucl"], 11.6 + 3 * 1.5 / 1.128)
        self.assertAlmostEqual(lim["mr_ucl"], 3.267 * 1.5)
        self.assertTrue(lim["warnings"])  # 20점 미만 경고

    def test_frozen_baseline_not_widened_by_outlier(self):
        rng = random.Random(1)
        base = [50 + rng.gauss(0, 1) for _ in range(30)]
        lim = spc.imr_fit(base)
        res = spc.imr_apply([50.2, 49.8, 70.0, 50.1], lim, start_index=30)
        names = [(v["index"], v["name"]) for v in res["violations"]]
        self.assertIn((32, "I_beyond_limits"), names)
        self.assertIn((32, "MR_beyond_ucl"), names)
        self.assertEqual(spc.imr_fit(base)["ucl"], lim["ucl"])  # 평가 구간이 한계를 바꾸지 않음
        self.assertIsNotNone(res["points"][0]["mr"])
        self.assertIsNone(spc.imr_apply([1.0], lim, chain=False)["points"][0]["mr"])

    def test_rejects_missing(self):
        with self.assertRaises(ValueError):
            spc.imr_fit([1, 2, None, 4])


class TestWesternElectric(unittest.TestCase):
    def test_each_rule(self):
        we = spc.western_electric
        self.assertEqual(we([0, 0, 3.5, 0], 0, 1)["by_rule"]["WE1_beyond_3sigma"], [2])
        self.assertEqual(we([2.5, 0, 2.5], 0, 1, rules=(2,))["by_rule"]["WE2_2of3_beyond_2sigma"], [2])
        self.assertEqual(we([2.5, 0, -2.5], 0, 1, rules=(2,))["violations"], [])  # 반대쪽은 세지 않음
        self.assertEqual(we([1.5, 1.5, 0, 1.5, 1.5], 0, 1, rules=(3,))["by_rule"]["WE3_4of5_beyond_1sigma"], [4])
        r4 = we([0.1] * 9, 0, 1, rules=(4,))["by_rule"]["WE4_8_same_side"]
        self.assertEqual(r4, [7, 8])

    def test_result_shape_and_sigma(self):
        res = spc.western_electric([0, 4], 0, 1)
        self.assertEqual(res["violations"], [{"index": 1, "rule": 1, "name": "WE1_beyond_3sigma"}])
        self.assertEqual(res["n"], 2)
        with self.assertRaises(ValueError):
            spc.western_electric([1, 2], 0, 0)


class TestXbarCpk(unittest.TestCase):
    def test_xbar_r(self):
        lim = spc.xbar_r_fit([[1, 3], [2, 4], [3, 5]])
        self.assertAlmostEqual(lim["xbar_center"], 3.0)
        self.assertAlmostEqual(lim["r_center"], 2.0)
        self.assertAlmostEqual(lim["x_ucl"], 3.0 + 1.880 * 2.0)
        with self.assertRaises(ValueError):
            spc.xbar_r_fit([[1, 2], [1, 2, 3]])

    def test_cp_cpk(self):
        r = spc.cp_cpk([9, 10, 11], lsl=4, usl=16, sigma=1.0)
        self.assertAlmostEqual(r["cp"], 2.0)
        self.assertAlmostEqual(r["cpk"], 2.0)
        r = spc.cp_cpk([9, 10, 11], usl=13, sigma=1.0)
        self.assertIsNone(r["cp"])
        self.assertAlmostEqual(r["cpk"], 1.0)
        self.assertEqual(spc.cp_cpk([9, 10, 11])["sigma_basis"], "sample_stdev")


    def test_we2_we3_need_current_point_beyond(self):
        # 회귀: 예전엔 2σ 밖 2점 뒤의 정상 점(0.1)도 WE2 위반으로 보고([3, 4])
        self.assertEqual(spc.western_electric([0, 0, 2.5, 2.5, 0.1], 0, 1, rules=(2,))["by_rule"],
                         {"WE2_2of3_beyond_2sigma": [3]})
        self.assertEqual(spc.western_electric([2.5, 2.5, -2.5], 0, 1, rules=(2,))["by_rule"]["WE2_2of3_beyond_2sigma"], [])  # 반대쪽 현재 점
        self.assertEqual(spc.western_electric([1.5] * 4 + [0.2], 0, 1, rules=(3,))["by_rule"]["WE3_4of5_beyond_1sigma"], [])

    def test_cp_cpk_spec_order_and_imr_sigma(self):
        with self.assertRaises(ValueError):
            spc.cp_cpk([1, 2, 3], lsl=5, usl=1)  # 회귀: 예전엔 cpk -1.0을 그냥 냈다
        r = spc.cp_cpk([1, 2, 3, 2, 1], lsl=0, usl=4, sigma="imr")
        self.assertEqual(r["sigma_basis"], "imr_mrbar")
        self.assertAlmostEqual(r["sigma"], 1 / 1.128)
        self.assertAlmostEqual(r["cp"], 4 / (6 / 1.128))


if __name__ == "__main__":
    unittest.main()
