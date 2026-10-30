import json
import unittest

from . import clean


class TestClean(unittest.TestCase):
    def setUp(self):
        self.train = [{"x": float(i), "c": "A" if i % 2 else "B"} for i in range(1, 101)]
        self.train[0]["x"] = None
        self.train[1]["c"] = "rare"

    def test_fit_uses_train_only(self):
        p = clean.fit_cleaner(self.train, numeric=["x"], categorical=["c"], clip=(0.05, 0.95), min_count=2)
        test = [{"x": 1e9, "c": "A"}]
        p_all = clean.fit_cleaner(self.train + test * 50, numeric=["x"], clip=(0.05, 0.95))
        self.assertNotEqual(p["numeric"]["x"]["hi"], p_all["numeric"]["x"]["hi"])  # test가 섞이면 규칙이 바뀐다
        self.assertEqual(p["categorical"]["c"]["levels"], ["A", "B"])
        json.dumps(p)  # 저장 가능

    def test_apply(self):
        p = clean.fit_cleaner(self.train, numeric=["x"], categorical=["c"], clip=(0.05, 0.95), min_count=2)
        rows = [{"x": None, "c": None}, {"x": 1e9, "c": "Z"}, {"x": "bad", "c": "A"}, {"x": 50, "c": "rare", "k": 1}]
        out = clean.apply_cleaner(rows, p)
        med = p["numeric"]["x"]["median"]
        self.assertEqual([o["x"] for o in out], [med, p["numeric"]["x"]["hi"], med, 50.0])
        self.assertEqual([o["x_missing"] for o in out], [1, 0, 1, 0])
        self.assertEqual([o["c"] for o in out], ["__missing__", "__other__", "A", "__other__"])
        self.assertEqual(out[3]["k"], 1)
        self.assertIsNone(rows[0]["x"])  # 입력 불변

    def test_no_clip_and_empty_column(self):
        p = clean.fit_cleaner([{"x": 1}, {"x": 2}, {"y": 3}], numeric=["x", "y", "z"], clip=None)
        self.assertEqual(clean.apply_cleaner([{"x": 100}], p, missing_flag=False)[0]["x"], 100.0)
        self.assertTrue(p["numeric"]["z"]["constant"])


if __name__ == "__main__":
    unittest.main()
