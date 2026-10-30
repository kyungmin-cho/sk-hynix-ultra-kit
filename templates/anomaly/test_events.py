import unittest

from . import events


class TestEvents(unittest.TestCase):
    def test_lifecycle_open_and_clear_with_hysteresis(self):
        f = [0, 1, 1, 0, 1, 0, 0, 0, 1, 0]
        states, alerts = events.alert_lifecycle([bool(x) for x in f], open_after=2, clear_after=3)
        self.assertEqual(states[:3], ["NORMAL", "PENDING", "OPEN"])
        self.assertEqual(states[3], "CLEARING")      # 한 번 정상은 닫지 않는다
        self.assertEqual(states[7], "NORMAL")
        self.assertEqual(alerts, [{"start": 1, "opened": 2, "end": 4, "closed": 7}])
        self.assertEqual(states[8], "PENDING")       # 1회는 열지 않는다

    def test_lifecycle_unclosed(self):
        _, alerts = events.alert_lifecycle([True, True])
        self.assertIsNone(alerts[0]["closed"])

    def test_point_prf(self):
        r = events.point_prf([True, True, False, False], [True, False, True, False])
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (1, 1, 1))
        self.assertAlmostEqual(r["f1"], 0.5)
        with self.assertRaises(ValueError):
            events.point_prf([True], [])

    def test_event_prf_same_group_and_tolerance(self):
        truth = [{"group": "A", "start": 10, "end": 12}, {"group": "B", "start": 10, "end": 12}]
        pred = [{"group": "A", "start": 14, "end": 15}, {"group": "C", "start": 10, "end": 12}]
        r0 = events.event_prf(pred, truth, tolerance=0)
        self.assertEqual((r0["precision"], r0["recall"]), (0.0, 0.0))
        r2 = events.event_prf(pred, truth, tolerance=2)
        self.assertEqual((r2["precision"], r2["recall"]), (0.5, 0.5))   # 다른 설비 C는 B와 매칭 안 됨
        self.assertEqual(events.event_prf([], truth)["recall"], 0.0)

    def test_synth_series_deterministic_with_truth(self):
        xs, truth = events.synth_series(n=100, seed=1)
        xs2, _ = events.synth_series(n=100, seed=1)
        self.assertEqual(xs, xs2)
        self.assertEqual([t["kind"] for t in truth], ["spike", "shift", "stuck"])
        st = truth[2]
        self.assertEqual(len(set(xs[st["start"]:st["end"] + 1])), 1)
        self.assertGreater(xs[truth[0]["start"]], 54)
        with self.assertRaises(ValueError):
            events.synth_series(10, inject=[("bogus", 1, 1)])


if __name__ == "__main__":
    unittest.main()
