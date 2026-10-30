import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from . import _common as c


class TestParseTs(unittest.TestCase):
    def test_z_and_offsets(self):
        utc = c.parse_ts("2026-10-31T01:00:00Z")
        self.assertEqual(utc, datetime(2026, 10, 31, 1, tzinfo=timezone.utc))
        self.assertEqual(c.parse_ts("2026-10-31T10:00:00+09:00"), utc)
        self.assertEqual(c.parse_ts("2026-10-31 10:00:00+0900"), utc)
        self.assertEqual(c.parse_ts("2026-10-31T10:00:00 +09"), utc)

    def test_space_fraction_and_slash(self):
        dt = c.parse_ts("2026/10/31 10:00:05.123456789")
        self.assertEqual(dt, datetime(2026, 10, 31, 10, 0, 5, 123456))
        self.assertIsNone(dt.tzinfo)
        self.assertEqual(c.parse_ts("2026-10-31"), datetime(2026, 10, 31))
        self.assertEqual(c.parse_ts("2026-10-31 9:05"), datetime(2026, 10, 31, 9, 5))

    def test_epoch_and_compact(self):
        self.assertEqual(c.parse_ts(1793404800), datetime(2026, 10, 31, tzinfo=timezone.utc))
        self.assertEqual(c.parse_ts("1793404800000"), datetime(2026, 10, 31, tzinfo=timezone.utc))
        self.assertEqual(c.parse_ts("20261031"), datetime(2026, 10, 31))
        self.assertEqual(c.parse_ts("20261031100000"), datetime(2026, 10, 31, 10))
        self.assertEqual(c.parse_ts(20261031), datetime(2026, 10, 31))  # int로 읽힌 날짜 열
        self.assertEqual(c.parse_ts(20261031100000), datetime(2026, 10, 31, 10))
        self.assertEqual(c.parse_ts(1793404800.0), datetime(2026, 10, 31, tzinfo=timezone.utc))
        self.assertIsNone(c.parse_ts(5))

    def test_tz_attach_and_convert(self):
        self.assertEqual(c.parse_ts("2026-10-31 10:00", tz=c.KST).utcoffset(), timedelta(hours=9))
        self.assertEqual(c.parse_ts("2026-10-31T01:00:00Z", tz=c.KST).hour, 10)

    def test_errors(self):
        self.assertIsNone(c.parse_ts("not a date"))
        self.assertIsNone(c.parse_ts(""))
        self.assertIsNone(c.parse_ts("2026-13-01"))
        with self.assertRaises(ValueError):
            c.parse_ts("garbage", errors="raise")


class TestCsv(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, name, text, encoding):
        p = os.path.join(self.tmp.name, name)
        with open(p, "w", encoding=encoding, newline="") as f:
            f.write(text)
        return p

    def test_cp949_semicolon(self):
        p = self._write("a.csv", "설비;값\nA호기;1.5\nB호기;2\n", "cp949")
        self.assertEqual(c.sniff_csv(p), ("cp949", ";"))
        rows = list(c.stream_csv(p))
        self.assertEqual(rows, [{"설비": "A호기", "값": "1.5"}, {"설비": "B호기", "값": "2"}])

    def test_large_utf8_cut_multibyte(self):
        # sniff 경계에서 한글이 잘려도 utf-8로 판정해야 한다
        body = "id,이름\n" + "".join("%d,가나다라마바사\n" % i for i in range(20000))
        p = self._write("b.csv", body, "utf-8")
        for n in (65536, 65537, 65538):
            self.assertEqual(c.sniff_csv(p, sniff_bytes=n)[0], "utf-8-sig")
        rows = c.stream_csv(p)
        self.assertEqual(next(rows), {"id": "0", "이름": "가나다라마바사"})
        self.assertEqual(sum(1 for _ in rows), 19999)

    def test_tab_bom_limit(self):
        p = self._write("c.tsv", "﻿a\tb\n1\t2\n3\t4\n", "utf-8")
        self.assertEqual(list(c.stream_csv(p, limit=1)), [{"a": "1", "b": "2"}])


class TestSmall(unittest.TestCase):
    def test_optional_import(self):
        self.assertIsNotNone(c.optional_import("json"))
        self.assertIsNone(c.optional_import("no_such_module_xyz"))

    def test_to_float(self):
        self.assertEqual(c.to_float("1,234.5"), 1234.5)
        self.assertEqual(c.to_float(" 3 "), 3.0)
        for v in ("", "NA", "nan", None, "abc", float("inf"), True):
            self.assertIsNone(c.to_float(v))

    def test_quantile(self):
        xs = [1, 2, 3, 4]
        self.assertEqual(c.quantile(xs, 0.5), 2.5)
        self.assertAlmostEqual(c.quantile(xs, 0.25), 1.75)
        self.assertEqual(c.quantile(xs, 1.0), 4)
        with self.assertRaises(ValueError):
            c.quantile([], 0.5)


class TestIntervalAndTable(unittest.TestCase):
    def test_infer_interval(self):
        ts = [c.parse_ts("2026-10-31T10:%02d:00+09:00" % m) for m in (0, 1, 2, 3, 10, 11, 11)]
        r = c.infer_interval(ts)
        self.assertTrue(r["sorted"])
        self.assertEqual(r["median_sec"], 60.0)
        self.assertEqual(r["gaps"], [(4, 420.0)])
        self.assertEqual(r["duplicates"], 1)
        self.assertEqual(c.infer_interval([0, 10, 5])["unsorted_at"], 2)
        self.assertIsNone(c.infer_interval([1])["median_sec"])

    def test_md_table(self):
        t = c.md_table([{"a": 1.23456, "b": "x|y"}, {"a": None, "b": "z\nw"}])
        self.assertEqual(t.splitlines(), ["| a | b |", "|---|---|", "| 1.235 | x/y |", "|  | z w |"])
        self.assertEqual(c.md_table([]), "(no rows)")


if __name__ == "__main__":
    unittest.main()
