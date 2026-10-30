"""하네스 자체 가드레일 검사. 차용 없음(금지 패턴 자체 테스트 아이디어만 참고).

- 금지 패턴이 scripts/·templates/·skills/·state/·docs/·README.md·CAPABILITIES.md에 0건인지 grep한다.
  금지를 "설명하는" 언급은 AGENTS.md, docs/RULES.md, docs/EXCLUDED.md와 이 파일에서만 허용한다(검사 대상이 아님).
  예외는 ALLOW에 파일·패턴·줄 조건으로 명시한다.
- 스킬 프런트매터, skills/README.md 색인과 실제 폴더, 스킬이 가리키는 하네스 경로 존재.
- AGENTS.md 길이·4줄 블록, README 고지, LICENSE, .gitignore, 보조 스크립트 동작.
"""
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("hx-next", "hx-1-env", "hx-2-problem", "hx-3-capability", "hx-4-trials", "hx-5-gather", "hx-6-final")
SCAN_DIRS = ("scripts", "templates", "skills", "state", "docs")
SCAN_FILES = ("README.md", "CAPABILITIES.md")
EXPLAIN_FILES = {"docs/RULES.md", "docs/EXCLUDED.md"}  # 금지를 설명하는 문서(AGENTS.md와 같은 취급)
TEXT_EXT = {".py", ".sh", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".html", ".js", ".css", ".cfg", ""}

G = r"\bgit\s+(?:-C\s+\S+\s+)?"
PATTERNS = {
    "git-push": G + r"push\b",
    "git-init": G + r"init\b",
    "git-add-all": G + r"add\s+(?:-A|--all)\b",
    "git-commit": G + r"commit\b",
    "git-remote-change": G + r"remote\s+(?:add|remove|rm|set-url|rename)\b",
    "break-system-packages": r"--break-system-packages",
    "pip-install": r"\bpip3?\s+install\b",
    "npm-global": r"\bnpm\s+(?:i|install)\b[^\n]*\s(?:-g|--global)\b",
    "npx": r"\bnpx\b",
    "sudo": r"\bsudo\b",
    "apt": r"\bapt-get\b|\bapt\s+(?:install|update|upgrade)\b",
    "codex-update-login": r"\bcodex\s+(?:update|login)\b",
    "codex-exec": r"\bcodex\s+exec\b",
    "approval-bypass": r"--dangerously-bypass-approvals-and-sandbox|--full-auto|--yolo|danger-full-access"
                       r"|--ask-for-approval|--sandbox\b",
    "codex-flags": r"\bcodex\b[^\n]*\s(?:-s|-a|-m|-c|--model|--config)\s",
    "model-pin": r"-m\s+['\"]?gpt-|\bgpt-[0-9]|\bclaude-(?:opus|sonnet|haiku|fable|instant|[0-9])|\bgemini\b"
                 r"|\bmodel\s*=\s*['\"]?(?:gpt|claude|gemini)",
    "external-llm-api": r"api\.openai\.com|api\.anthropic\.com|generativelanguage\.googleapis\.com|openrouter"
                        r"|api\.x\.ai|api\.groq\.com|api\.mistral\.ai|api\.cohere",
    "browser-automation": r"\bplaywright\b|\bselenium\b|\bpuppeteer\b|\bwebdriver\b|\bpyautogui\b",
    "curl-pipe-sh": r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:ba|z)?sh\b",
    "find-root": r"\bfind\s+/(?:\s|$)",
    "secret-print": r"\bprintenv\b|\bcat\s+\S*(?:auth\.json|\.netrc|credentials)"
                    r"|\becho\s+\"?\$\{?\w*(?:KEY|TOKEN|SECRET|PASSWORD)",
    # docs/EXCLUDED.md §1이 "테스트가 막는다"고 쓴 나머지 항목
    "git-identity": G + r"config\s+(?:--global\s+)?user\.(?:email|name)\s+(?!2>)['\"]?\w|\bgit\s+config\s+--global\b",
    "git-add-dot": G + r"add\s+\.(?:\s|$)",
    "add-dir-git": r"--add-dir\s+\S*\.git\b",
    "approval-never": r"approval_policy\s*=\s*['\"]?never|\s-a\s+never\b",
    "local-llm": r"\bollama\s+(?:run|pull|serve)\b|(?:localhost|127\.0\.0\.1):11434",
    "download": r"\bpip3?\s+download\b|\bcurl\b[^\n]*\s(?:(?-i:-O)\b|--remote-name\b|-o\s+(?!/dev/null)\S)"
                r"|\bwget\s+(?:-\S+\s+)*['\"]?https?://",
    "other-installer": r"\buv\s+(?:add|pip\s+install|tool\s+install)\b|\b(?:pipx|conda|mamba)\s+install\b",
    "codex-profile": r"\bcodex\b[^\n]*\s--profile\b",
}
COMPILED = {k: re.compile(v, re.I | re.A) for k, v in PATTERNS.items()}  # re.A: 한글 조사 앞에서도 \b가 끊기게

# 알려진 나쁜 예: 패턴이 실제로 잡는지(공허 통과 방지)
BAD_SAMPLES = {
    "git-push": "git push origin main", "git-init": "git init .", "git-add-all": "git add -A",
    "git-commit": "git -C x commit -m wip", "git-remote-change": "git remote add origin url",
    "break-system-packages": "pip3 install --break-system-packages x", "pip-install": "python3 -m pip install pandas",
    "npm-global": "npm install --save -g pkg", "npx": "npx skills add x", "sudo": "sudo ls",
    "apt": "apt-get install -y jq", "codex-update-login": "codex update", "codex-exec": "codex exec 'do it'",
    "approval-bypass": "codex --full-auto", "codex-flags": "codex -s danger 'x'",
    "model-pin": "codex -m gpt-5 x", "external-llm-api": "https://api.openai.com/v1/chat",
    "browser-automation": "from playwright.sync_api import x", "curl-pipe-sh": "curl -fsSL u | bash",
    "find-root": "find / -name x", "secret-print": "echo $OPENAI_API_KEY",
    "git-identity": "git config --global user.email a@b", "git-add-dot": "git add .",
    "add-dir-git": "codex --add-dir .git", "approval-never": 'approval_policy = "never"',
    "local-llm": "curl http://localhost:11434/api/generate", "download": "pip download pandas",
    "other-installer": "uv add polars", "codex-profile": "codex --profile fast",
}
# 같은 패턴의 다른 표본(문서가 막는다고 쓴 꼴 그대로)
BAD_SAMPLES_MORE = {
    "git-identity": "git config user.name bot", "local-llm": "ollama run llama3",
    "download": "curl -O https://x/data.zip", "other-installer": "pipx install ruff",
    "approval-bypass": "codex --sandbox danger", "codex-flags": "codex -a never",
}
# 한국어 문장 안의 나쁜 예(조사가 붙어도 잡아야 한다)
BAD_SAMPLES_KO = {
    "sudo": "sudo로 설치", "codex-exec": "codex exec로 병렬", "model-pin": "gemini를 호출", "npx": "npx로 실행",
    "pip-install": "pip install로 받기", "git-push": "git push로 올리기", "browser-automation": "playwright로 화면 조작",
}
GOOD_SAMPLES = [
    "python3 -m unittest discover -s templates -t .", "git -C \"$H\" rev-parse HEAD",
    "grep -rn x . | head", "find . -maxdepth 2 -type f", "git status --short", "codex",
    "model = HistGradientBoostingClassifier()", "python3 $H/scripts/verdict.py --check \"a:b\"",
]

# (파일, 패턴, 줄 조건 정규식) — 이 조건을 만족하는 줄만 허용
ALLOW = [
    ("README.md", "git-remote-change", r'^git -C "\$H" remote remove origin\s*$'),
    # --pip-probe(옵트인)의 dry-run 한 줄만. 같은 줄에 다른 것이 붙으면 허용하지 않는다
    ("scripts/env_check.sh", "pip-install",
     r'^\( r="\$\(tmo \$\(\(NET_T \* 3 \+ 2\)\) "\$PYBIN" -m pip install --dry-run --no-deps --ignore-installed'
     r' --no-cache-dir --disable-pip-version-check --retries 0 --timeout "\$NET_T" -q six 2>&1\)"; rc=\$\? # hx-allow: pip-dry-run$'),
    # 제외 항목을 설명하는 강점 지도 행(EXCLUDED를 가리키는 줄만)
    ("docs/STRENGTHS_MAP.md", "add-dir-git", r"docs/EXCLUDED\.md"),
    ("docs/STRENGTHS_MAP.md", "approval-never", r"docs/EXCLUDED\.md"),
    ("docs/STRENGTHS_MAP.md", "download", r"docs/EXCLUDED\.md"),
    ("scripts/env_check.sh", "sudo", r"sudo\s+-n\b|command\s+-v\s+sudo|\|sudo\)"),  # 존재·그룹만 확인
    ("scripts/env_check.sh", "apt", r"command\s+-v|type\s+-p|which\s"),
    ("scripts/env_check.sh", "codex-exec", r"--help|\bexec\b[^\n]*(?:help|grep)|CODEX_EXEC"),
]
PATH_RE = re.compile(r"(?<![A-Za-z0-9_.<>/-])(?:\$H/|\$\{H:-/tmp/_harness\}/|/tmp/_harness/)?((?:skills|scripts|state|templates)/[A-Za-z0-9_./-]*)")


def scanned_files():
    out = [ROOT / f for f in SCAN_FILES if (ROOT / f).is_file()]
    for d in SCAN_DIRS:
        for p in sorted((ROOT / d).rglob("*")) if (ROOT / d).is_dir() else []:
            if p.is_file() and "__pycache__" not in p.parts and p.suffix in TEXT_EXT \
                    and p.relative_to(ROOT).as_posix() not in EXPLAIN_FILES:
                out.append(p)
    return out


def allowed(rel, name, line):
    return any(rel == f and name == n and re.search(cond, line.strip(), re.I) for f, n, cond in ALLOW)


def violations():
    found = []
    for p in scanned_files():
        rel = p.relative_to(ROOT).as_posix()
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(lines, 1):
            for name, rx in COMPILED.items():
                if rx.search(line) and not allowed(rel, name, line):
                    found.append("{}:{} [{}] {}".format(rel, i, name, line.strip()[:120]))
    return found


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm


class PatternSelfTest(unittest.TestCase):
    def test_every_pattern_catches_its_bad_sample(self):
        self.assertEqual(set(BAD_SAMPLES), set(PATTERNS))
        for name, sample in BAD_SAMPLES.items():
            self.assertTrue(COMPILED[name].search(sample), "{} misses {!r}".format(name, sample))
        for name, sample in list(BAD_SAMPLES_KO.items()) + list(BAD_SAMPLES_MORE.items()):
            self.assertTrue(COMPILED[name].search(sample), "{} misses {!r}".format(name, sample))

    def test_good_samples_pass(self):
        for s in GOOD_SAMPLES:
            hits = [n for n, rx in COMPILED.items() if rx.search(s)]
            self.assertEqual(hits, [], s)

    def test_allow_list_is_line_scoped(self):
        self.assertTrue(allowed("README.md", "git-remote-change", 'git -C "$H" remote remove origin'))
        self.assertFalse(allowed("README.md", "git-remote-change", "git remote remove origin"))
        self.assertFalse(allowed("skills/x.md", "pip-install", "pip install --dry-run x"))


class ForbiddenPatternTest(unittest.TestCase):
    def test_no_forbidden_patterns(self):
        v = violations()
        self.assertEqual(v, [], "forbidden patterns outside AGENTS.md/tests:\n" + "\n".join(v))

    def test_no_outbound_network_in_code(self):
        """텔레메트리·외부 전송 없음: env_check.sh(HEAD 점검)와 테스트 파일 말고는 외부 통신 코드를 두지 않는다."""
        rx = re.compile(r"urllib\.request|http\.client|^\s*(?:import|from)\s+requests\b|socket\.create_connection"
                        r"|\bsmtplib\b|\bftplib\b|\b(?:curl|wget)\s", re.M)
        for bad in ("import urllib.request", "import requests", "curl -s https://x", "smtplib.SMTP()"):
            self.assertRegex(bad, rx)
        files = [p for p in (ROOT / "templates").rglob("*.py") if not p.name.startswith("test_")]
        files += [p for p in (ROOT / "scripts").iterdir() if p.is_file() and p.name != "env_check.sh"]
        self.assertGreater(len(files), 10)
        hits = ["{}: {}".format(p.relative_to(ROOT), m.group(0)) for p in files
                for m in rx.finditer(p.read_text(encoding="utf-8"))]
        self.assertEqual(hits, [])

    def test_agents_md_mentions_the_bans(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for word in ("git push", "--break-system-packages", "--full-auto", "api.openai.com", "/model"):
            self.assertIn(word, text)


class SkillsTest(unittest.TestCase):
    def test_skill_dirs_match_expected(self):
        dirs = sorted(p.name for p in (ROOT / "skills").iterdir() if p.is_dir())
        self.assertEqual(dirs, sorted(SKILLS))

    def test_frontmatter_and_head_table(self):
        for s in SKILLS:
            p = ROOT / "skills" / s / "SKILL.md"
            self.assertTrue(p.is_file(), p)
            text = p.read_text(encoding="utf-8")
            fm = frontmatter(text)
            self.assertIsNotNone(fm, "{}: no frontmatter".format(s))
            self.assertEqual(set(fm), {"name", "description"}, s)
            self.assertEqual(fm["name"], s)
            self.assertRegex(fm["description"], r"[A-Za-z]{4,}.*[A-Za-z]{4,}", s)
            self.assertIn("| 입력 | 출력 | 끝 신호 | 시간 예산 |", text, s)
            steps = re.findall(r"^\d+\. ", text, re.M)
            self.assertTrue(5 <= len(steps) <= 12, "{}: {} procedure steps".format(s, len(steps)))

    def test_index_matches_folders(self):
        idx = (ROOT / "skills" / "README.md").read_text(encoding="utf-8")
        listed = set(re.findall(r"`skills/(hx-[\w-]+)/SKILL\.md`", idx))
        self.assertEqual(listed, set(SKILLS))
        refs_listed = set(re.findall(r"`(skills/hx-[\w-]+/references/[\w./-]+)`", idx))
        refs_actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / "skills").glob("*/references/**/*")
                       if p.is_file()}
        self.assertEqual(refs_listed, refs_actual)

    def test_referenced_harness_paths_exist(self):
        files = list((ROOT / "skills").rglob("*.md")) + list((ROOT / "docs").glob("*.md")) + \
            [ROOT / "AGENTS.md", ROOT / "README.md", ROOT / "CAPABILITIES.md"]
        missing, skipped = [], []
        for f in files:
            for m in PATH_RE.finditer(f.read_text(encoding="utf-8")):
                rel = m.group(1).rstrip(".")
                if (ROOT / rel).exists():
                    continue
                # 다른 작업(templates/, env_check.sh)의 산출물은 아직 없을 수 있다 → skip으로 보고
                if rel.startswith("templates/") or rel == "scripts/env_check.sh":
                    skipped.append(rel)
                else:
                    missing.append("{} -> {}".format(f.relative_to(ROOT), rel))
        if skipped:
            sys.stderr.write("\n[skip: not yet present] " + ", ".join(sorted(set(skipped))) + "\n")
        self.assertEqual(missing, [])

    def test_interview_warns_about_tool_mentions(self):
        head = (ROOT / "skills/hx-2-problem/references/interview.md").read_text(encoding="utf-8")[:400]
        self.assertIn("GitHub", head)
        self.assertIn("MCP", head)


class DocsTest(unittest.TestCase):
    def test_agents_md_short_with_fallback_block(self):
        lines = (ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(lines), 100)
        self.assertTrue(any("하네스 없이 쓰는 4줄" in ln for ln in lines[:5]))
        block = "\n".join(lines).split("```text", 1)[1].split("```", 1)[0]
        self.assertEqual(len(re.findall(r"^[1-4]\. ", block, re.M)), 4)

    def test_readme(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("하네스 테스트 통과 ≠ 과제 성공", text)
        self.assertIn("/tmp/_harness", text)
        self.assertNotRegex(text, r"(?im)^(?:agent|에이전트|codex)\s*[:：]")  # 에이전트 대상 지시문 금지

    def test_license_and_gitignore(self):
        lic = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", lic)
        self.assertIn("Copyright (c) 2026 Kyungmin Cho", lic)
        gi = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
        for entry in ("ENVIRONMENT.md", "notes/", "exp/", "logs/", "__pycache__/", "*.pyc", ".venv/"):
            self.assertIn(entry, gi)


class ScriptsSmokeTest(unittest.TestCase):
    def py(self, *args, cwd=None):
        return subprocess.run([sys.executable, *args], capture_output=True, text=True, timeout=60, cwd=cwd)

    def test_help(self):
        for s in ("scripts/verdict.py", "scripts/profile_data.py", "scripts/presubmit.py"):
            self.assertEqual(self.py(str(ROOT / s), "--help").returncode, 0, s)
        for s in ("scripts/init_state.sh", "scripts/run_and_log.sh"):
            r = subprocess.run(["bash", str(ROOT / s), "--help"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, s)

    def test_verdict_exit_codes(self):
        v = str(ROOT / "scripts/verdict.py")
        ok = "{} -c \"print('a:b')\"".format(sys.executable)
        bad = "{} -c \"import sys; sys.exit(3)\"".format(sys.executable)
        self.assertEqual(self.py(v).returncode, 2)                          # 0 checks = fail
        r = self.py(v, "--check", "ok:" + ok)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("a:b", r.stdout)                                      # 첫 ':'에서만 나눔, 증거 남김
        self.assertEqual(self.py(v, "--check", "ok:" + ok, "--check", "bad:" + bad).returncode, 1)
        r = self.py(v, "--check", "ok:" + ok, "--check", "todo:", "--md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("NOT_RUN", r.stdout)

    def test_verdict_zero_tests_is_fail(self):
        v = str(ROOT / "scripts/verdict.py")
        with tempfile.TemporaryDirectory() as d:     # 빈 폴더 discover: unittest는 0건이어도 rc 0
            empty = "cd {} && {} -m unittest discover -q".format(d, sys.executable)
            r = self.py(v, "--check", "unit:" + empty)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("0 tests ran", r.stdout)
        for fake in ("collected 0 items", "NO TESTS RAN", "Ran 0 tests in 0.000s"):
            r = self.py(v, "--check", "t:{} -c \"print('{}')\"".format(sys.executable, fake))
            self.assertEqual(r.returncode, 1, fake)
        r = self.py(v, "--check", "t:{} -c \"print('Ran 10 tests')\"".format(sys.executable))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_verdict_timeout_with_escaped_grandchild(self):
        # 다른 세션으로 빠져나간 손자가 stdout을 잡아도 timeout+2초 근처에서 끝나야 한다
        v = str(ROOT / "scripts/verdict.py")
        gc = "({} -c 'import os,time;os.setsid();time.sleep(20)' &); sleep 20".format(sys.executable)
        t0 = time.time()
        r = self.py(v, "--timeout", "1", "--check", "bg:" + gc)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("timeout", r.stdout)
        self.assertLess(time.time() - t0, 10)

    def test_profile_data_cp949_and_dups(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.csv")
            with open(p, "w", encoding="cp949") as fh:
                fh.write("시각,설비,값\n2026-10-31 10:00:00,EQ1,1.5\n2026-10-31 10:00:00,EQ1,1.5\n2026-10-31 10:01:00,EQ2,\n")
            r = self.py(str(ROOT / "scripts/profile_data.py"), p)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("rows=3", r.stdout)
            self.assertIn("encoding=cp949", r.stdout)
            self.assertIn("dup_rows(sampled)=1", r.stdout)
            self.assertIn("TS?", r.stdout)
            self.assertIn("Q1: 결측 처리", r.stdout)            # 담당자 질문 후보
            self.assertIn("중복 기록", r.stdout)
            md = self.py(str(ROOT / "scripts/profile_data.py"), p, "--md")
            self.assertIn("담당자 질문 후보", md.stdout)

    def test_profile_data_key_and_pii_columns(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "y.csv")
            Path(p).write_text("wafer_id,operator_name,val\nW1,kim,1\nW2,lee,2\nW3,kim,x\n", encoding="utf-8")
            r = self.py(str(ROOT / "scripts/profile_data.py"), p)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("KEY? wafer_id", r.stdout)
            self.assertIn("PII? operator_name", r.stdout)
            self.assertIn("섞여", r.stdout)

    def test_profile_data_key_over_unique_cap_and_pii_narrow(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "z.csv")
            lines = ["lot_id,tool_name,recipe_name,val"] + ["L%05d,T%d,R1,%d.5" % (i, i % 3, i) for i in range(1500)]
            Path(p).write_text("\n".join(lines) + "\n", encoding="utf-8")
            r = self.py(str(ROOT / "scripts/profile_data.py"), p)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("KEY? lot_id(고유값 >1000, 중복 미확인)", r.stdout)
            self.assertIn("PII? none", r.stdout)          # tool_name·recipe_name은 개인정보 아님
            self.assertNotIn("val(고유값", r.stdout)        # 연속 측정값은 키 후보로 올리지 않음(int도 상한 넘으면 올라감)


RUN_AND_LOG = ROOT / "scripts" / "run_and_log.sh"


def wait_end_line(path, timeout=5.0):
    """로그 끝 줄(# end:)이 쓰일 때까지 짧게 기다린다(tee가 늦게 닫힐 수 있음)."""
    deadline = time.time() + timeout
    text = ""
    while time.time() < deadline:
        text = Path(path).read_text(encoding="utf-8")
        if "# end:" in text:
            break
        time.sleep(0.1)
    return text


class RunAndLogTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ws = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def logs(self):
        return sorted((Path(self.ws) / "logs").glob("*.log"))

    def test_logs_output_and_passes_exit_code(self):
        r = subprocess.run(["bash", str(RUN_AND_LOG), "smoke test", "--", "sh", "-c", "echo hi; echo err >&2; exit 3"],
                           cwd=self.ws, capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 3)
        self.assertIn("hi", r.stdout)                                     # 화면에도 tee
        (log,) = self.logs()
        self.assertRegex(log.name, r"^\d{8}-\d{6}_smoke_test\.log$")      # KST 시각_태그(공백은 _)
        text = wait_end_line(log)
        for want in ("# cmd: sh -c", "# cwd: ", "# start: ", " KST", "hi", "err", "exit=3"):
            self.assertIn(want, text)
        self.assertLess(text.index("# start:"), text.index("\nhi\n"))         # 머리를 먼저 쓴다

    def test_signals_recorded(self):
        for sig, rc_want, name in ((signal.SIGTERM, 143, "TERM"), (signal.SIGINT, 130, "INT")):
            with self.subTest(signal=name):
                p = subprocess.Popen(["bash", str(RUN_AND_LOG), "sig" + name, "--", "sleep", "30"], cwd=self.ws,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1.0)
                p.send_signal(sig)
                self.assertEqual(p.wait(timeout=10), rc_want)
                (log,) = [x for x in self.logs() if x.name.endswith("_sig{}.log".format(name))]
                text = wait_end_line(log)
                self.assertIn("exit={}".format(rc_want), text)
                self.assertIn("signal " + name, text)

    def test_usage_errors(self):
        for args in ([], ["tag"], ["tag", "echo", "hi"], ["tag", "--"]):
            r = subprocess.run(["bash", str(RUN_AND_LOG), *args], cwd=self.ws, capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, args)
        self.assertFalse((Path(self.ws) / "logs").exists())


class PresubmitTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def run_ps(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/presubmit.py"), str(self.ws), *args],
                              capture_output=True, text=True, timeout=60)

    def test_clean_workspace_passes(self):
        (self.ws / "README.md").write_text("# x\n\n```bash\npython3 main.py --in data.csv\n```\n", encoding="utf-8")
        (self.ws / "main.py").write_text("print('ok')\n", encoding="utf-8")
        r = self.run_ps("--no-git")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("| readme | OK |", r.stdout)
        self.assertIn("| notes | WARN |", r.stdout)                         # notes 없음은 경고만
        self.assertEqual(self.run_ps("--no-git", "--strict").returncode, 1)

    def test_findings(self):
        (self.ws / "README.md").write_text("# 설명만 있고 실행 명령 없음\n", encoding="utf-8")
        (self.ws / "main.py").write_text(
            "import sys\nsys.path.insert(0, '/tmp/_harness')\nfrom templates.spc import spc  # TODO\n", encoding="utf-8")
        (self.ws / "cfg.py").write_text("API_KEY = 'sk-" + "a" * 32 + "'\n", encoding="utf-8")
        shutil.copy(ROOT / "templates/spc/spc.py", self.ws / "myspc.py")
        subprocess.run(["bash", str(ROOT / "scripts/init_state.sh"), "--extra"], cwd=self.ws, capture_output=True)
        r = self.run_ps("--no-git")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("| readme | FAIL |", r.stdout)
        self.assertRegex(r.stdout, r"\| secrets \| FAIL \| worktree cfg\.py:1")
        self.assertNotIn("a" * 32, r.stdout)                                 # 값은 가린다
        # 상태 양식(init_state --extra) 문구는 시크릿으로 오탐되지 않는다
        self.assertEqual(len(re.findall(r"\| secrets \| FAIL \|", r.stdout)), 2, r.stdout)  # cfg.py의 두 패턴
        self.assertRegex(r.stdout, r"\| harness \| WARN \| .*main\.py:2")
        self.assertRegex(r.stdout, r"\| copy \| WARN \| myspc\.py: .*templates/spc/spc\.py")
        self.assertRegex(r.stdout, r"\| todo \| WARN \|")
        self.assertRegex(r.stdout, r"\| not_run \| WARN \| 표 안 NOT_RUN [1-9]")

    def test_secrets_in_logs_and_notes(self):
        (self.ws / "README.md").write_text("```\npython3 main.py\n```\n", encoding="utf-8")
        (self.ws / "logs").mkdir()
        (self.ws / "logs" / "20261031-101500_e2e.log").write_text("key: AKIA" + "Q" * 16 + "\n", encoding="utf-8")
        (self.ws / "notes").mkdir()
        (self.ws / "notes" / "HANDOFF.md").write_text("xoxb-" + "1" * 20 + "\n", encoding="utf-8")
        r = self.run_ps("--no-git")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertRegex(r.stdout, r"worktree logs/20261031-101500_e2e\.log:1 \[aws access key\]")
        self.assertRegex(r.stdout, r"worktree notes/HANDOFF\.md:1 \[slack token\]")
        self.assertNotIn("Q" * 16, r.stdout)
        self.assertNotIn("1" * 20, r.stdout)

    @unittest.skipUnless(shutil.which("git"), "git 없음")
    def test_secret_in_git_history(self):
        g = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "init.defaultBranch=main"]
        (self.ws / "README.md").write_text("```\npython3 main.py\n```\n", encoding="utf-8")
        (self.ws / "cfg.py").write_text("token = 'ghp_" + "b" * 36 + "'\n", encoding="utf-8")
        for cmd in (["init", "-q"], ["add", "README.md", "cfg.py"], ["commit", "-qm", "x"], ["rm", "-q", "cfg.py"],
                    ["commit", "-qm", "rm"]):
            subprocess.run(g + cmd, cwd=self.ws, check=True, capture_output=True,
                           env=dict(os.environ, HOME=str(self.ws), GIT_CONFIG_NOSYSTEM="1"))
        r = self.run_ps()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertRegex(r.stdout, r"\| secrets \| OK \| 워킹트리")          # 지금 파일엔 없음
        self.assertRegex(r.stdout, r"\| secrets \| FAIL \| history [0-9a-f]+ \[github token\]")
        self.assertNotIn("b" * 36, r.stdout)

    def test_bad_root(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts/presubmit.py"), str(self.ws / "nope")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
