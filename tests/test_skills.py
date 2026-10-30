"""스킬·참조·색인·기능 지도(CAPABILITIES.md)·docs의 경로가 실제와 맞는지 검사. 차용 없음.

- SKILL.md 파일명(대소문자)·프런트매터 name=폴더명·description(영어 키워드)
- 각 references 파일이 부모 SKILL.md에서 "언제 읽나"와 함께 가리켜지는지
- skills/README.md·CAPABILITIES.md·docs/*.md 안의 하네스 경로와 마크다운 상대 링크가 실제로 있는지
- CAPABILITIES.md가 스킬·참조·docs·상태 양식·scripts·templates 폴더를 빠짐없이 담는지
- 담당자 메신저 문구에 GitHub·MCP 등 도구 이름이 없는지
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("hx-next", "hx-1-env", "hx-2-problem", "hx-3-capability", "hx-4-trials", "hx-5-gather", "hx-6-final")
DOCS = ("RULES", "TIMELINE", "PROMPTS", "PLAYBOOKS", "ENV_FACTS", "EXCLUDED")
STATE = ("TASK", "STATE", "DECISIONS", "HANDOFF", "TRIALS", "VERIFICATION", "ESSAY_PREP")
SCRIPTS = ("env_check.sh", "init_state.sh", "run_and_log.sh", "verdict.py", "profile_data.py", "presubmit.py")
# 백틱 안의 하네스 상대 경로(앞에 $H/·/tmp/_harness/·<H>/가 붙어도 됨)
PATH_RE = re.compile(r"`(?:\$H/|\$\{H:-/tmp/_harness\}/|/tmp/_harness/|<H>/)?((?:skills|scripts|state|templates|docs|tests)/[A-Za-z0-9_./-]*"
                     r"|[A-Z_]+\.md)")
WORKSPACE_FILES = {"ENVIRONMENT.md", "RESULT.md"}  # 워크스페이스 루트·exp/<n>/ 파일
LINK_RE = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    return {k.strip(): v.strip() for k, _, v in (ln.partition(":") for ln in m.group(1).splitlines())}


def ref_files():
    return sorted(p for p in (ROOT / "skills").glob("*/references/**/*") if p.is_file())


def md_files():
    return [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "CAPABILITIES.md"] + \
        sorted((ROOT / "docs").glob("*.md")) + sorted((ROOT / "skills").rglob("*.md"))


def missing_paths(md):
    out = []
    for m in PATH_RE.finditer(md.read_text(encoding="utf-8")):
        rel = m.group(1).rstrip(".")
        if "<" in rel or "*" in rel:          # 자리표시자(<n>, <폴더>)·글롭은 건너뜀
            continue
        if rel.endswith(".md") and "/" not in rel:   # 루트 문서 이름(STATE.md 등)은 워크스페이스 notes/일 수 있음
            if (ROOT / rel).exists() or (ROOT / "state" / rel).exists() or rel in WORKSPACE_FILES:
                continue
            out.append(rel)
            continue
        if not (ROOT / rel).exists():
            out.append(rel)
    return out


class SkillFilesTest(unittest.TestCase):
    def test_skill_md_exact_name_and_frontmatter(self):
        for s in SKILLS:
            d = ROOT / "skills" / s
            self.assertIn("SKILL.md", [p.name for p in d.iterdir()], s)   # 소문자 skill.md 불가
            fm = frontmatter((d / "SKILL.md").read_text(encoding="utf-8"))
            self.assertIsNotNone(fm, s)
            self.assertEqual(set(fm), {"name", "description"}, s)
            self.assertEqual(fm["name"], s)
            self.assertRegex(fm["description"], r"\b[A-Za-z]{4,}\b.*\b[A-Za-z]{4,}\b", s)

    def test_every_reference_is_pointed_by_its_skill(self):
        self.assertGreaterEqual(len(ref_files()), 11)
        for p in ref_files():
            skill = p.relative_to(ROOT / "skills").parts[0]
            rel = p.relative_to(ROOT).as_posix()
            text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(rel, text, "{} not pointed by {}/SKILL.md".format(rel, skill))

    def test_index_lists_every_reference(self):
        idx = (ROOT / "skills" / "README.md").read_text(encoding="utf-8")
        for p in ref_files():
            self.assertIn("`{}`".format(p.relative_to(ROOT).as_posix()), idx)


class PathsExistTest(unittest.TestCase):
    def test_backtick_paths_exist(self):
        bad = []
        for md in md_files():
            bad += ["{} -> {}".format(md.relative_to(ROOT), r) for r in missing_paths(md)]
        self.assertEqual(bad, [])

    def test_markdown_relative_links_exist(self):
        bad = []
        for md in md_files():
            for m in LINK_RE.finditer(md.read_text(encoding="utf-8")):
                target = m.group(1)
                if re.match(r"[a-z]+:", target):
                    continue
                if not (md.parent / target).exists():
                    bad.append("{} -> {}".format(md.relative_to(ROOT), target))
        self.assertEqual(bad, [])


class CapabilitiesTest(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / "CAPABILITIES.md").read_text(encoding="utf-8")

    def test_covers_everything(self):
        want = ["skills/{}/SKILL.md".format(s) for s in SKILLS]
        want += [p.relative_to(ROOT).as_posix() for p in ref_files()]
        want += ["docs/{}.md".format(d) for d in DOCS]
        want += ["state/{}.md".format(f) for f in STATE]
        want += ["scripts/{}".format(s) for s in SCRIPTS]
        want += ["templates/{}/".format(p.name) for p in sorted((ROOT / "templates").iterdir())
                 if p.is_dir() and not p.name.startswith("__")]
        want += ["templates/_common.py", "tests/"]
        missing = [w for w in want if w not in self.text]
        self.assertEqual(missing, [])

    def test_table_has_where_and_when_columns(self):
        self.assertGreaterEqual(self.text.count("| 기능/상황 | 어디 | 언제 |"), 6)
        self.assertLessEqual(len(self.text.splitlines()), 110)

    def test_entry_points_point_to_capabilities(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()
        self.assertTrue(any("CAPABILITIES.md" in ln for ln in agents[:20]), "AGENTS.md 상단에 포인터 없음")
        self.assertIn("CAPABILITIES.md", (ROOT / "skills/hx-next/SKILL.md").read_text(encoding="utf-8"))


class DocsTest(unittest.TestCase):
    def test_docs_exist(self):
        for d in DOCS:
            self.assertTrue((ROOT / "docs" / "{}.md".format(d)).is_file(), d)

    def test_rules_marked_unofficial_with_date(self):
        text = (ROOT / "docs/RULES.md").read_text(encoding="utf-8")
        self.assertIn("공식 원문 아님", text)
        self.assertRegex(text, r"확인일: 2026-\d\d-\d\d")

    def test_messenger_lines_have_no_tool_names(self):
        text = (ROOT / "docs/PROMPTS.md").read_text(encoding="utf-8")
        section = text.split("## 6. 담당자 메신저", 1)[1]
        blocks = re.findall(r"```text\n(.*?)```", section, re.S)
        self.assertGreaterEqual(len(blocks), 3)
        for b in blocks:
            self.assertNotRegex(b, r"(?i)github|mcp|codex|\bAI\b|에이전트|하네스")

    def test_prompts_fallback_block_matches_agents(self):
        def block(path):
            t = (ROOT / path).read_text(encoding="utf-8")
            i = t.index("하네스 없이 쓰는 4줄")
            return t[i:].split("```text\n", 1)[1].split("```", 1)[0]
        self.assertEqual(block("docs/PROMPTS.md"), block("AGENTS.md"))

    def test_playbooks_cover_types_with_template_paths(self):
        text = (ROOT / "docs/PLAYBOOKS.md").read_text(encoding="utf-8")
        sections = re.findall(r"^## \d+\. ", text, re.M)
        self.assertGreaterEqual(len(sections), 8)
        for folder in ("anomaly", "spc", "yield_", "ml", "web", "contract"):
            self.assertIn("templates/{}/".format(folder), text)


if __name__ == "__main__":
    unittest.main()
