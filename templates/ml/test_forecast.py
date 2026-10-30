import unittest

from . import forecast as fc


class TestForecast(unittest.TestCase):
    def test_rolling_origin_no_overlap_and_order(self):
        folds = fc.rolling_origin(10, initial=6, horizon=2, step=1)
        self.assertEqual(len(folds), 3)
        for tr, te in folds:
            self.assertLess(max(tr), min(te))
        self.assertEqual(folds[0], (list(range(6)), [6, 7]))
        self.assertEqual(fc.rolling_origin(10, 6, 2, expanding=False)[2][0], [2, 3, 4, 5, 6, 7])
        with self.assertRaises(ValueError):
            fc.rolling_origin(10, 0)

    def test_seasonal_beats_naive_on_periodic_series_and_gate(self):
        s = [10, 20, 30, 40] * 6
        base = fc.backtest(s, fc.naive, initial=8, horizon=4, step=4)
        seas = fc.backtest(s, fc.seasonal_naive(4), initial=8, horizon=4, step=4)
        self.assertEqual(seas["mae_mean"], 0.0)
        self.assertGreater(base["mae_mean"], 0)
        self.assertEqual(base["n_origins"], 4)
        self.assertTrue(fc.baseline_gate(seas, base, min_gain=0.1)["pass"])
        self.assertFalse(fc.baseline_gate(base, seas)["pass"])
        with self.assertRaises(ValueError):
            fc.backtest([1, 2], fc.naive, initial=5)

    def test_tracking_signal_detects_bias(self):
        ts = fc.tracking_signal([10] * 8, [9] * 8)       # 계속 낮게 예측
        self.assertAlmostEqual(ts[-1], 8.0)
        flat = fc.tracking_signal([1, -1, 1, -1], [0, 0, 0, 0])
        self.assertLessEqual(abs(flat[-1]), 1.0)
        self.assertEqual(fc.tracking_signal([1], [1]), [0.0])


if __name__ == "__main__":
    unittest.main()
