import unittest

from . import rules


class TestRules(unittest.TestCase):
    def test_consecutive_rule(self):
        xs = [70, 81, 82, 79, 81, 82, 83, 84, 75]
        ev = rules.consecutive_rule(xs, hi=80, n=3, name="temp_high")
        self.assertEqual(len(ev), 1)
        e = ev[0]
        self.assertEqual((e["alert_index"], e["start"], e["end"], e["length"]), (6, 4, 7, 4))
        self.assertIn("temp_high", e["reason"])

    def test_boundary_and_missing_break_run(self):
        self.assertEqual(rules.consecutive_rule([80, 80, 80], hi=80, n=1), [])
        self.assertEqual(rules.consecutive_rule([90, None, 90, "x", 90], hi=80, n=2), [])
        self.assertEqual(len(rules.consecutive_rule([1, 2], lo=5, n=1)), 1)
        with self.assertRaises(ValueError):
            rules.consecutive_rule([1])

    def test_events_from_flags(self):
        f = [False, True, True, False, True, False, False, True]
        self.assertEqual([(e["start"], e["end"]) for e in rules.events_from_flags(f)], [(1, 2), (4, 4), (7, 7)])
        self.assertEqual([(e["start"], e["end"]) for e in rules.events_from_flags(f, max_gap=1)], [(1, 4), (7, 7)])
        self.assertEqual(len(rules.events_from_flags(f, min_len=2)), 1)

    def test_evaluate_rows(self):
        rows = [{"t": 90, "p": 1}, {"t": 91, "p": 1}, {"t": 70, "p": 9}, {"t": "", "p": 1}]
        spec = [{"name": "t_hi", "col": "t", "hi": 80, "n": 2}, {"name": "p_hi", "col": "p", "hi": 5}]
        out = rules.evaluate_rows(rows, spec)
        self.assertEqual([o["alert"] for o in out], [False, True, True, False])
        self.assertTrue(out[1]["reasons"][0].startswith("t_hi"))
        self.assertTrue(out[2]["reasons"][0].startswith("p_hi"))


if __name__ == "__main__":
    unittest.main()
