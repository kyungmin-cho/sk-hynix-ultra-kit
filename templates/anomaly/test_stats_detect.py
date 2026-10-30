import importlib.util
import random
import unittest
from fractions import Fraction

from . import stats_detect as sd


def _series(n=200, seed=7):
    rng = random.Random(seed)
    return [10.0 + rng.gauss(0, 1) for _ in range(n)]


class TestStatsDetect(unittest.TestCase):
    def test_rolling_z_finds_spike(self):
        xs = _series()
        xs[150] = 25.0
        self.assertIn(150, sd.flagged(sd.rolling_zscore(xs, window=30)))
        self.assertLessEqual(len(sd.flagged(sd.rolling_zscore(xs, window=30))), 3)

    def test_ewma_and_cusum_find_shift(self):
        xs = _series() + [12.0 + v - 10.0 for v in _series(100, seed=8)]
        self.assertTrue(any(i >= 200 for i in sd.flagged(sd.ewma_detect(xs, baseline_n=100))))
        cs = sd.flagged(sd.cusum(xs, baseline_n=100))
        self.assertTrue(cs and min(i for i in cs if i >= 200) < 230)
        self.assertFalse(any(i < 200 for i in sd.flagged(sd.ewma_detect(xs, baseline_n=100))))

    def test_prefix_invariant_no_future_leak(self):
        # 미래 구간에 큰 스파이크를 넣어도 앞부분 판정은 바뀌지 않아야 한다
        xs = _series(300)
        future = xs[:200] + [1e6] * 100
        for fn in (lambda v: sd.rolling_zscore(v, window=20),
                   lambda v: sd.ewma_detect(v, baseline_n=50),
                   lambda v: sd.cusum(v, baseline_n=50),
                   lambda v: sd.stuck(v, n=3)):
            full, alt, part = fn(xs), fn(future), fn(xs[:200])
            self.assertEqual(full[:200], part)
            self.assertEqual(alt[:200], part)

    def test_iqr_fit_on_train_only(self):
        b = sd.iqr_bounds([1, 2, 3, 4, 5, 6, 7, 8])
        self.assertAlmostEqual(b["q1"], 2.75)
        self.assertAlmostEqual(b["hi"], 6.25 + 1.5 * 3.5)
        with self.assertRaises(ValueError):
            sd.iqr_bounds([1, 2, None])

    def test_stuck_and_missing(self):
        xs = [1, 2, 2, 2, 2, None, 2, "x", 3]
        self.assertEqual(sd.flagged(sd.stuck(xs, n=3)), [3, 4])
        r = sd.rolling_zscore([None, "a", float("nan")] + [1.0] * 12, min_periods=10)
        self.assertIsNone(r[0]["score"])
        self.assertEqual(r[-1]["score"], 0.0)

    def test_other_number_types(self):  # numpy 정수·Fraction 같은 numbers.Real도 버리지 않는다
        xs = [Fraction(10)] * 12 + [Fraction(50)]
        self.assertEqual(sd.flagged(sd.rolling_zscore(xs)), [12])
        if importlib.util.find_spec("numpy"):
            import numpy as np
            arr = list(np.array([10] * 12 + [50], dtype=np.int64))
            self.assertEqual(sd.flagged(sd.rolling_zscore(arr)), [12])

    def test_csv_string_input(self):
        # 회귀: 예전 _num은 numbers.Real만 받아 문자열 입력이면 flag [] (숫자 입력은 [40])
        xs = [10.0 + (i % 3) * 0.1 for i in range(40)] + [30.0]
        self.assertEqual(sd.flagged(sd.rolling_zscore([str(x) for x in xs], window=20)),
                         sd.flagged(sd.rolling_zscore(xs, window=20)))
        self.assertEqual(sd.flagged(sd.rolling_zscore([str(x) for x in xs], window=20)), [40])

    def test_no_flag_inside_baseline(self):
        # 회귀: 예전 cusum은 기준 구간(i < baseline_n) 안에서도 flag([2, 9] 등)
        rng = random.Random(1)
        ys = [rng.gauss(0, 1) for _ in range(60)]
        ys[2] = ys[3] = 8.0
        for fn in (sd.cusum, sd.ewma_detect):
            self.assertFalse([i for i in sd.flagged(fn(ys, baseline_n=50)) if i < 50], fn.__name__)

    def test_exclude_flagged_keeps_window_clean(self):
        xs = [10.0 + (i % 2) * 0.1 for i in range(30)] + [30.0, 10.0, 15.0]
        self.assertEqual(sd.flagged(sd.rolling_zscore(xs, window=20, exclude_flagged=True)), [30, 32])
        self.assertEqual(sd.flagged(sd.rolling_zscore(xs, window=20)), [30])  # 기본: 첫 스파이크가 둘째를 가림

    def test_short_baseline(self):
        self.assertEqual(sd.flagged(sd.cusum([1.0])), [])
        self.assertEqual(sd.ewma_detect([1.0])[0]["reason"], "baseline too short")


if __name__ == "__main__":
    unittest.main()
