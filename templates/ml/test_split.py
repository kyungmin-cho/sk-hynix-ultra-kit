import unittest

from . import split


class TestSplit(unittest.TestCase):
    def test_time_split_no_overlap_with_ties(self):
        times = [5, 1, 3, 3, 2, 4, 4, 4, 0, 6]
        tr, te = split.time_split(times, test_frac=0.3)
        self.assertEqual(sorted(tr + te), list(range(10)))
        self.assertLess(max(times[i] for i in tr), min(times[i] for i in te))
        split.assert_no_leak(tr, te, times=times)
        tr2, te2 = split.time_split(times, cutoff=4)
        self.assertEqual({times[i] for i in te2}, {4, 5, 6})

    def test_group_split_keeps_groups_apart(self):
        groups = ["W%d" % (i // 10) for i in range(100)]
        tr, te = split.group_split(groups, test_frac=0.3, seed=1)
        self.assertEqual(len(tr) + len(te), 100)
        self.assertEqual(len(te), 30)
        split.assert_no_leak(tr, te, groups=groups)
        self.assertEqual(split.group_split(groups, 0.3, seed=1), (tr, te))  # 결정적

    def test_stratified_keeps_ratio(self):
        labels = [1] * 20 + [0] * 80
        tr, te = split.stratified_split(labels, test_frac=0.25, seed=0)
        self.assertEqual(sum(labels[i] for i in te), 5)
        self.assertEqual(len(te), 25)
        self.assertEqual(split.check_leak(tr, te), [])

    def test_leak_detection(self):
        times = [1, 2, 3, 4]
        groups = ["a", "a", "b", "b"]
        probs = split.check_leak([0, 2], [1, 2], times=times, groups=groups)
        self.assertEqual(len(probs), 3)
        with self.assertRaises(AssertionError):
            split.assert_no_leak([0, 2], [1, 3], groups=groups)


    def test_string_times_parsed_not_lexical(self):
        # 회귀: 예전엔 사전순 정렬이라 '2026-1-9'(가장 이른 날)가 test에 들어갔다
        times = ["2026-1-9", "2026-1-10", "2026-1-11", "2026-1-12", "2026-1-13"]
        tr, te = split.time_split(times, test_frac=0.4)
        self.assertEqual((tr, te), ([0, 1, 2], [3, 4]))
        self.assertEqual(split.check_leak(tr, te, times=times), [])
        self.assertEqual(split.time_split(times, cutoff="2026-01-12")[1], [3, 4])

    def test_empty_side_is_an_error(self):
        # 회귀: 동률 시각이 많으면 train 0행인데 check_leak는 [] (통과)였다
        with self.assertRaises(ValueError):
            split.time_split([1] * 9 + [2], test_frac=0.2)
        self.assertTrue(split.check_leak([], [0, 1], times=[1, 1]))
        with self.assertRaises(ValueError):
            split.group_split(["a"] * 5)

    def test_group_split_skips_oversized_group(self):
        # 회귀: 섞은 첫 그룹이 80%여도 test로 넣어 train/test 비율이 뒤집혔다
        groups = ["a"] * 8 + ["b", "c"]
        for seed in range(5):
            tr, te = split.group_split(groups, test_frac=0.2, seed=seed)
            self.assertEqual((len(tr), len(te)), (8, 2), seed)
        tr, te = split.group_split(["a"] * 6 + ["b"] * 4, test_frac=0.2)  # 둘 다 목표보다 크면 작은 쪽
        self.assertEqual(len(te), 4)


if __name__ == "__main__":
    unittest.main()
