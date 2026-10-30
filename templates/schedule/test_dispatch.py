import itertools
import random
import unittest

from . import dispatch as ds

# 설비 1대, 손계산: 처리시간 A3 B1 C2, 납기 A3 B6 C4
JOBS = [ds.Job("A", 3, due=3), ds.Job("B", 1, due=6), ds.Job("C", 2, due=4)]
ONE = [ds.Machine("M1")]


class TestDispatch(unittest.TestCase):
    def test_hand_example(self):
        spt = ds.dispatch(JOBS, ONE, "SPT")
        self.assertEqual([(d["job"], d["start"], d["end"]) for d in spt], [("B", 0, 1), ("C", 1, 3), ("A", 3, 6)])
        m = ds.metrics(spt)
        self.assertEqual((m["makespan"], m["mean_flow"], m["total_tardiness"], m["n_late"]), (6, 3.333, 3, 1))
        edd = ds.metrics(ds.dispatch(JOBS, ONE, "EDD"))  # A(0-3) C(3-5) B(5-6) → 지연 C 1
        self.assertEqual((edd["max_tardiness"], edd["total_tardiness"]), (1, 1))
        self.assertEqual(edd["utilization"], {"M1": 1.0})

    def test_single_machine_theorems(self):
        # 설비 1대·전부 ready=0: SPT는 평균 흐름시간 최소, EDD는 최대 지연 최소(모든 순열 대비).
        rng = random.Random(7)
        for _ in range(20):
            jobs = [ds.Job("J%d" % i, rng.randint(1, 9), due=rng.randint(3, 25)) for i in range(5)]
            best_flow = min(sum(itertools.accumulate(j.duration for j in p)) / 5 for p in itertools.permutations(jobs))
            best_lmax = min(max(max(0, t - j.due) for t, j in zip(itertools.accumulate(x.duration for x in p), p))
                            for p in itertools.permutations(jobs))
            res = {r["rule"]: r for r in ds.compare_rules(jobs, ONE)}
            self.assertAlmostEqual(res["SPT"]["mean_flow"], round(best_flow, 3), places=3)
            self.assertEqual(res["EDD"]["max_tardiness"], best_lmax)
            for r in res.values():
                self.assertGreaterEqual(r["mean_flow"] + 1e-9, res["SPT"]["mean_flow"])
                self.assertGreaterEqual(r["max_tardiness"], res["EDD"]["max_tardiness"])

    def test_eligibility_ready_speed_down(self):
        jobs = [ds.Job("X", 4, ready=0, eligible=["M2"]), ds.Job("Y", 2, ready=5), ds.Job("Z", 2, ready=0, setup=1)]
        ms = [ds.Machine("M1", down=[(1, 4)]), ds.Machine("M2", speed=2.0)]
        sched = {d["job"]: d for d in ds.dispatch(jobs, ms, "FIFO")}
        self.assertEqual(sched["X"]["machine"], "M2")
        self.assertEqual((sched["X"]["start"], sched["X"]["end"]), (0, 2.0))   # 4 / speed 2
        self.assertEqual(sched["Z"]["machine"], "M2")                            # M1은 다운타임 때문에 7에 끝남
        self.assertEqual((sched["Z"]["start"], sched["Z"]["end"]), (2.0, 4.0))  # 2/2 + setup 1
        self.assertEqual(sched["Y"]["start"], 5)                                 # 도착 전에는 시작 안 함
        z_m1 = ds.dispatch([ds.Job("Z", 2)], [ds.Machine("M1", down=[(1, 4)])])[0]
        self.assertEqual((z_m1["start"], z_m1["end"]), (4, 6))                  # 다운타임에 걸치지 않음
        with self.assertRaises(ValueError):
            ds.dispatch([ds.Job("Q", 1, eligible=["M9"])], ms)
        with self.assertRaises(ValueError):
            ds.dispatch(jobs, ms, "LIFO")

    def test_text_outputs_and_loader(self):
        rows = [{"id": "A", "duration": "3", "due": "3"}, {"id": "B", "duration": "1", "due": "6", "eligible": "M1;M2"},
                {"id": "C", "duration": "2", "due": "4", "priority": "5", "ready": ""}]
        jobs = ds.jobs_from_rows(rows)
        self.assertEqual((jobs[1].eligible, jobs[2].priority, jobs[2].ready, jobs[0].due), (["M1", "M2"], 5.0, 0.0, 3.0))
        sched = ds.dispatch(jobs, [ds.Machine("M1"), ds.Machine("M2")], "PRIORITY")
        g = ds.gantt_text(sched, width=12)
        self.assertEqual(len(g.splitlines()), 3)
        self.assertTrue(all(len(line.split("|")[1]) == 12 for line in g.splitlines()[1:]))
        t = ds.table_text(ds.compare_rules(jobs, [ds.Machine("M1")]))
        self.assertEqual(len(t.splitlines()), 2 + len(ds.RULES))
        self.assertEqual(ds.metrics([]), {"n_jobs": 0})


if __name__ == "__main__":
    unittest.main()
