"""docs/STRENGTHS_MAP.md(설계 §4 강점 477행 ↔ 레포 위치)가 실제 레포와 맞는지 검사. 차용 없음.

- 행 수 ≥ 477, 접두사별 행 수(SR 168 · DK 171 · AR 71 · CE 52 · AC 15) 이상, ID 중복 0, 빈 경로 0
- 경로 칸의 모든 항목: 파일·폴더 존재, `경로::함수`면 def/class 존재, `경로#문자열`이면 그 문자열이 파일에 있음
- 상태는 구현/참조문서/의도적 제외 중 하나, 의도적 제외는 EXCLUDED 또는 금지 검사 테스트를 가리킴
- 머리의 상태별 건수가 표와 같음, "이번에 채운 누락" 표의 파일 존재
설계 문서는 레포 밖에 있으므로 읽지 않는다(기대 행 수는 상수).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "docs" / "STRENGTHS_MAP.md"
EXPECTED = {"SR": 168, "DK": 171, "AR": 71, "CE": 52, "AC": 15}
STATUSES = ("구현", "참조문서", "의도적 제외")
EXCLUSION_TARGETS = ("docs/EXCLUDED.md", "tests/test_guardrails.py", "tests/test_skills.py")
ROW_RE = re.compile(r"^\| ((?:SR|DK|AR|CE|AC)[\w.'-]*) \| (.*) \| (.*?) \| ([^|]+) \|$")


def split_sections():
    text = MAP.read_text(encoding="utf-8")
    main, _, filled = text.partition("## 이번에 채운 누락")
    return text, main, filled


def table_rows(main):
    return [ROW_RE.match(ln).groups() for ln in main.splitlines() if ROW_RE.match(ln)]


def entries(cell):
    return re.findall(r"`([^`]+)`", cell)


def problem(entry):
    path, func, anchor = entry, None, None
    if "::" in entry:
        path, func = entry.split("::", 1)
    elif "#" in entry:
        path, anchor = entry.split("#", 1)
    p = ROOT / path
    if not p.exists():
        return "no such path"
    if func or anchor:
        if not p.is_file():
            return "anchor on a directory"
        t = p.read_text(encoding="utf-8")
        if func and not re.search(r"^\s*(?:def|class)\s+%s\b|^%s\s*=" % (re.escape(func), re.escape(func)), t, re.M):
            return "no def/class " + func
        if anchor and not re.search(re.escape(anchor) + r"(?!\d)", t):
            return "text not found"
    return None


class StrengthsMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text, cls.main, cls.filled = split_sections()
        cls.rows = table_rows(cls.main)

    def test_row_count_and_prefixes(self):
        self.assertGreaterEqual(len(self.rows), sum(EXPECTED.values()))
        for prefix, n in EXPECTED.items():
            got = sum(1 for r in self.rows if re.match(prefix + r"(?![A-Z])", r[0]))
            self.assertGreaterEqual(got, n, prefix)

    def test_ids_unique(self):
        ids = [r[0] for r in self.rows]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        self.assertEqual(dup, [])

    def test_every_row_has_text_paths_and_status(self):
        bad = []
        for rid, item, cell, status in self.rows:
            if not item.strip() or not entries(cell) or status.strip() not in STATUSES:
                bad.append(rid)
        self.assertEqual(bad, [])

    def test_every_path_function_and_anchor_exists(self):
        bad = []
        for rid, _, cell, _ in self.rows:
            for e in entries(cell):
                why = problem(e)
                if why:
                    bad.append("{} {} ({})".format(rid, e, why))
        self.assertEqual(bad, [])

    def test_exclusions_point_to_reason_or_guard(self):
        bad = [rid for rid, _, cell, st in self.rows if st.strip() == "의도적 제외"
               and not any(e.startswith(EXCLUSION_TARGETS) for e in entries(cell))]
        self.assertEqual(bad, [])

    def test_header_counts_match_table(self):
        m = re.search(r"구현 (\d+) · 참조문서 (\d+) · 의도적 제외 (\d+) · 합계 (\d+)", self.main)
        self.assertIsNotNone(m)
        counts = [sum(1 for r in self.rows if r[3].strip() == s) for s in STATUSES]
        self.assertEqual([int(x) for x in m.groups()], counts + [len(self.rows)])

    def test_filled_gaps_table_paths_exist(self):
        paths = [e for ln in self.filled.splitlines() if ln.startswith("| ") for e in entries(ln.split(" | ")[-1])]
        self.assertGreater(len(paths), 10)
        self.assertEqual([p for p in paths if problem(p)], [])

    def test_checker_catches_bad_entries(self):  # 공허 통과 방지
        self.assertIsNotNone(problem("templates/nope.py"))
        self.assertIsNotNone(problem("templates/ml/forecast.py::no_such_function"))
        self.assertIsNotNone(problem("AGENTS.md#이 문자열은 없다"))
        self.assertIsNotNone(problem("scripts/env_check.sh#R1 Z없는규칙"))
        self.assertIsNone(problem("templates/ml/forecast.py::rolling_origin"))

    def test_capabilities_points_here(self):
        self.assertIn("docs/STRENGTHS_MAP.md", (ROOT / "CAPABILITIES.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
