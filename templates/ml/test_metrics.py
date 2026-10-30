import math
import random
import time
import unittest

from . import metrics as m


class TestMetrics(unittest.TestCase):
    def test_csv_string_labels_and_scores(self):
        # 회귀: "1"/"0" 문자열 라벨 + positive=1 → 예전엔 accuracy 1.0·tp 0·recall 0, AUC None
        res = m.classification_metrics(["1", "0", "1"], ["1", "0", "0"])
        self.assertEqual((res["tp"], res["fn"], res["tn"]), (1, 1, 1))
        self.assertEqual(m.classification_metrics(["true", "False"], [True, 0])["recall"], 1.0)
        self.assertEqual(m.roc_auc(["1", "0", "0", "1"], ["10", "0.2", "2.5", "0.5"]), 0.75)  # 사전순이면 0.5
        self.assertEqual(m.cost_threshold(["1", "0"], ["0.9", "0.1"])["fn"], 0)

    def test_label_and_length_mismatch_raise(self):
        with self.assertRaises(ValueError):
            m.classification_metrics(["OK", "NG"], ["OK", "NG"])  # positive=1이 라벨에 없음
        with self.assertRaises(ValueError):
            m.roc_auc([1, 0, 1], [0.1, 0.2])
        with self.assertRaises(ValueError):
            m.cost_threshold([1, 0], [0.5])
        self.assertIsNone(m.roc_auc([0, 0], [0.1, 0.2]))  # 0/1 라벨인데 양성이 없을 뿐 → None

    def test_classification(self):
        r = m.classification_metrics([1, 1, 0, 0, 1], [1, 0, 0, 1, 1])
        self.assertEqual((r["tp"], r["fp"], r["fn"], r["tn"]), (2, 1, 1, 1))
        self.assertAlmostEqual(r["precision"], 2 / 3)
        self.assertAlmostEqual(r["recall"], 2 / 3)
        self.assertAlmostEqual(r["f1"], 2 / 3)
        self.assertEqual(m.classification_metrics(["OK", "NG"], ["OK", "OK"], positive="NG")["recall"], 0.0)

    def test_regression(self):
        r = m.regression_metrics([1, 2, 3, 0], [2, 2, 1, 0])
        self.assertAlmostEqual(r["mae"], 0.75)
        self.assertAlmostEqual(r["rmse"], math.sqrt(5 / 4))
        self.assertEqual(r["n_mape"], 3)
        self.assertAlmostEqual(r["mape"], (1 + 0 + 2 / 3) / 3)
        self.assertAlmostEqual(r["r2"], 1 - 5 / 5)

    def test_auc(self):
        self.assertEqual(m.roc_auc([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]), 0.75)
        self.assertEqual(m.roc_auc([0, 1], [0.5, 0.5]), 0.5)
        self.assertIsNone(m.roc_auc([1, 1], [0.1, 0.2]))

    def test_cost_threshold(self):
        y = [0, 0, 0, 1, 0, 1, 1]
        s = [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.9]
        r = m.cost_threshold(y, s, cost_fp=1, cost_fn=5)
        self.assertEqual((r["threshold"], r["fp"], r["fn"]), (0.4, 1, 0))
        r = m.cost_threshold(y, s, cost_fp=10, cost_fn=1)
        self.assertEqual(r["threshold"], 0.7)  # 오경보가 비싸면 임계값이 올라간다

    def test_cost_threshold_matches_bruteforce_and_is_fast(self):
        rng = random.Random(2)
        y = [int(rng.random() < 0.2) for _ in range(300)]
        s = [round(rng.random(), 2) for _ in range(300)]  # 동점 많음
        got = m.cost_threshold(y, s, cost_fp=1, cost_fn=4)["table"]
        for row in got:
            t = row["threshold"]
            self.assertEqual(row["fp"], sum(1 for a, b in zip(y, s) if b >= t and a != 1))
            self.assertEqual(row["fn"], sum(1 for a, b in zip(y, s) if b < t and a == 1))
        y = [int(rng.random() < 0.1) for _ in range(50000)]
        s = [rng.random() for _ in range(50000)]
        t0 = time.time()
        m.cost_threshold(y, s)
        self.assertLess(time.time() - t0, 10.0)


class TestPermutationImportance(unittest.TestCase):
    def test_informative_column_ranks_first(self):
        rng = random.Random(0)
        rows = [{"a": rng.random(), "noise": rng.random()} for _ in range(200)]
        y = [1 if r["a"] > 0.5 else 0 for r in rows]
        predict = lambda rs: [1 if r["a"] > 0.5 else 0 for r in rs]
        acc = lambda t, p: sum(1 for x, z in zip(t, p) if x == z) / len(t)
        imp = m.permutation_importance(predict, rows, y, acc, ["noise", "a"], repeats=2)
        self.assertEqual(imp[0]["col"], "a")
        self.assertGreater(imp[0]["drop"], 0.3)
        self.assertEqual(imp[1]["drop"], 0.0)
        self.assertEqual(rows[0].keys(), {"a", "noise"})   # 원본 행은 바뀌지 않는다


if __name__ == "__main__":
    unittest.main()
