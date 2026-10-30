#!/usr/bin/env python3
"""presubmit.py — 제출 전 점검(stdlib, 읽기 전용). 차용 없음(점검 항목 아이디어만 참고).

사용: python3 <H>/scripts/presubmit.py [ROOT] [--src DIR] [--notes DIR] [--require FILE]... [--base REV]
                                     [--copy-threshold 0.5] [--no-git] [--strict]
  ROOT   워크스페이스 루트(기본 .). notes/ 와 git 저장소가 여기에 있다고 본다.
  --src  제출 코드 폴더(기본 ROOT, 상대 경로는 ROOT 기준). README 실행 명령·TODO·하네스 의존·복사 검사 대상.
         README.md·--require 파일이 --src에 없으면 ROOT에서 찾는다.

점검(결과 OK / WARN / FAIL / INFO):
  required   필수 파일 존재(README.md + --require, --src → ROOT 순)      없으면 FAIL
  readme     README에 실행 명령(python3·bash·make·npm run 등)이 있나      없으면 FAIL
  notes      notes/ TASK·STATE·DECISIONS·HANDOFF 존재·채움                없으면 WARN
  not_run    notes/*.md의 NOT_RUN 개수                                    있으면 WARN
  todo       TODO/FIXME/XXX                                               있으면 WARN
  secrets    시크릿 패턴(ROOT 워킹트리 notes/·logs/·exp/ 포함 + git log -p 이력, 값은 가림) 있으면 FAIL
             .env·*.env는 따옴표 없는 KEY=VALUE(이름에 PASSWORD·SECRET·TOKEN·KEY·CREDENTIAL)도 본다
             git log 실패·--base 오류는 WARN(이력 스캔 못 함)
  harness    하네스 import(templates.·spc.spc 같은 템플릿 모듈·import_module) 있으면 FAIL
             하네스 경로 문자열(_harness·이 하네스 실제 경로·STATE의 하네스 경로·
             os.environ["H"]·sys.path에 외부 절대경로)                      있으면 WARN
  copy       하네스 templates/와 줄 단위 과다 복사(비율 ≥ 임계값)           있으면 WARN
  env_file   ENVIRONMENT.md·_harness/가 워크스페이스 안에 있나(추적 여부 무관) 있으면 WARN
exit: 0 = FAIL 없음(WARN은 출력만) / 1 = FAIL 있음(--strict면 WARN도 1) / 2 = 사용 오류·검사 대상 없음.
git은 읽기만(ls-files, log -p). 파일을 고치거나 지우지 않는다. 네트워크 없음.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
# 시크릿은 커밋될 수 있는 notes/·logs/·exp/까지 본다. TODO·하네스 의존·복사 검사는 제출 코드만.
SECRET_SKIP = {".git", "_harness", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache"}
SKIP_DIRS = SECRET_SKIP | {"exp", "logs", "notes", "notes-hx"}
TEXT_EXT = {".py", ".sh", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".cfg", ".ini", ".env", ".js",
            ".ts", ".tsx", ".jsx", ".html", ".css", ".sql", ".csv", ".ipynb", ".log", ""}
MAX_BYTES = 2_000_000
GIT_LOG_MAX = 20_000_000
SECRETS = {
    "openai-style key": r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}",
    "aws access key": r"\bAKIA[0-9A-Z]{16}\b",
    "github token": r"\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{30,}",
    "slack token": r"\bxox[abprs]-[A-Za-z0-9-]{10,}",
    "google api key": r"\bAIza[0-9A-Za-z_-]{30,}",
    "private key": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    "assigned secret": r"(?i)\b[\w-]*(?:api[_-]?key|secret|token|passw(?:or)?d|credential)[\w-]*\s*[:=]\s*"
                       r"['\"][^'\"\s]{8,}['\"]",
}
SECRET_RX = {k: re.compile(v) for k, v in SECRETS.items()}
# .env 파일: 따옴표 없는 KEY=VALUE. $VAR·<자리표시자>는 값으로 보지 않는다.
ENV_SECRET_RX = re.compile(r"(?i)^\s*(?:export\s+)?[A-Za-z_]\w*(?:passw(?:or)?d|secret|token|key|credential)\w*"
                           r"\s*=\s*['\"]?(?![$<])[^'\"\s#]{8,}")
TODO_RX = re.compile(r"\b(?:TODO|FIXME|XXX)\b")
RUN_RX = re.compile(r"^\s*(?:\$\s*)?(?:PORT=\S+\s+)?(?:python3?|bash|sh|make|node|npm\s+run|uv\s+run|pytest|\./)\b.*$",
                    re.M)
# 하네스 경로 문자열(WARN): 고정 패턴. 실제 하네스 경로·STATE의 하네스 경로는 harness_rx()가 덧붙인다.
HARNESS_PATH_PAT = (r"_harness|\bharness/(?:templates|scripts)\b|os\.environ(?:\.get)?\s*[\[(]\s*['\"]H['\"]"
                    r"|getenv\(\s*['\"]H['\"]|\$\{?H\b"
                    r"|sys\.path\.(?:append|insert)\([^)]*(?:harness|['\"]/)")
# 하네스 import(FAIL): templates 패키지 또는 import_module("templates…")/__import__("templates…")
HARNESS_IMPORT_PAT = (r"^\s*(?:from|import)\s+templates\b|(?:import_module|__import__)\(\s*['\"]templates\b")
TRIVIAL_RX = re.compile(r"^(?:return|pass|break|continue|else:|try:|finally:|[\]\)\}\[\(\{,:;\s]*|"
                        r"(?:from\s+\S+\s+)?import\s.*|@\w+|#.*|\"\"\"|''')$")
NOTE_FILES = ("TASK", "STATE", "DECISIONS", "HANDOFF")


class Report:
    def __init__(self):
        self.rows = []

    def add(self, check, level, msg):
        self.rows.append((check, level, msg))

    def count(self, level):
        return sum(1 for r in self.rows if r[1] == level)


TIMEOUT = "\0timeout"


def run_git(root, *args, limit=None, timeout=20):
    try:
        p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return TIMEOUT
    except OSError:
        return None
    if p.returncode != 0:
        return None
    out = p.stdout[:limit] if limit else p.stdout
    return out.decode("utf-8", "replace")


def is_text(p):
    if p.suffix.lower() not in TEXT_EXT:
        return False
    try:
        if p.stat().st_size > MAX_BYTES:
            return False
        with open(p, "rb") as fh:
            return b"\0" not in fh.read(4096)
    except OSError:
        return False


def list_files(root, use_git, skip=SKIP_DIRS):
    """제출될 파일 목록. git이면 추적+미추적(ignore 제외), 아니면 숨김·skip 폴더를 빼고 걷는다."""
    files = []
    out = run_git(root, "ls-files", "-co", "--exclude-standard", "-z") if use_git else None
    if out not in (None, TIMEOUT):
        for rel in out.split("\0"):
            if rel and not any(part in skip or part.startswith(".") for part in Path(rel).parts[:-1]):
                files.append(root / rel)
    else:
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d not in skip and not d.startswith(".")]
            files += [Path(dp) / f for f in fns]
    return [f for f in files if f.is_file() and is_text(f)]


def mask(s):
    s = s.strip()
    return s[:4] + "…" + "*" * 4 if len(s) > 8 else "****"


def read_lines(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def find_file(name, src, root):
    """--src에 없으면 ROOT에서 찾는다(README가 루트에만 있는 흔한 구조)."""
    for d in (src, root):
        if (d / name).exists():
            return d / name
    return None


def check_required(src, root, req, rep):
    for name in ["README.md"] + list(req):
        p = find_file(name, src, root)
        rep.add("required", "OK" if p else "FAIL",
                name if not p or p.parent == src else "{} (ROOT에서 찾음)".format(name))


def check_readme(src, root, rep):
    readme = find_file("README.md", src, root)
    if not readme or not readme.is_file():
        rep.add("readme", "FAIL", "README.md 없음 → 실행 명령을 확인할 수 없다")
        return
    cmds = [m.group(0).strip() for m in RUN_RX.finditer(readme.read_text(encoding="utf-8", errors="replace"))]
    if cmds:
        rep.add("readme", "OK", "실행 명령 {}개, 첫 줄: {}".format(len(cmds), cmds[0][:80]))
    else:
        rep.add("readme", "FAIL", "README.md에 실행 명령(python3·bash·make·npm run 등으로 시작하는 줄)이 없다")


def check_notes(notes, rep):
    if not notes.is_dir():
        rep.add("notes", "WARN", "{} 없음(init_state.sh)".format(notes))
        return
    for f in NOTE_FILES:
        p = notes / (f + ".md")
        if not p.is_file():
            rep.add("notes", "WARN", "{} 없음".format(p.name))
        elif f == "TASK" and "나는 ___" in p.read_text(encoding="utf-8", errors="replace"):
            rep.add("notes", "WARN", "TASK.md 한 문장이 아직 빈칸")
        elif f == "HANDOFF" and re.search(r"```bash\n# 예:", p.read_text(encoding="utf-8", errors="replace")):
            rep.add("notes", "WARN", "HANDOFF.md §1 실행 방법이 아직 예시 그대로")
        else:
            rep.add("notes", "OK", p.name)
    n, where = 0, []
    for p in sorted(notes.glob("*.md")):
        c = sum(1 for ln in read_lines(p) if ln.lstrip().startswith("|")
                for cell in ln.split("|") if cell.strip() == "NOT_RUN")  # 표 칸 값이 정확히 NOT_RUN인 것만
        if c:
            n += c
            where.append("{}={}".format(p.name, c))
    rep.add("not_run", "WARN" if n else "OK",
            "표 안 NOT_RUN {}개 ({}) → 돌리거나 HANDOFF §3에 미검증으로 명시".format(n, ", ".join(where)) if n
            else "표 안 NOT_RUN 0")


def check_todo(files, root, rep):
    hits = []
    for p in files:
        for i, ln in enumerate(read_lines(p), 1):
            if TODO_RX.search(ln):
                hits.append("{}:{}".format(p.relative_to(root), i))
    rep.add("todo", "WARN" if hits else "OK",
            "{}건: {}".format(len(hits), ", ".join(hits[:10])) if hits else "0건")


def is_env_file(p):
    n = p.name.lower()
    return (n == ".env" or n.endswith(".env") or n.startswith(".env.")) and not re.search(r"example|sample|template", n)


def check_secrets(files, root, use_git, base, rep):
    hits = []
    for p in files:
        env = is_env_file(p)
        for i, ln in enumerate(read_lines(p), 1):
            found = False
            for name, rx in SECRET_RX.items():
                m = rx.search(ln)
                if m:
                    found = True
                    hits.append("{}:{} [{}] {}".format(p.relative_to(root), i, name, mask(m.group(0))))
            m = ENV_SECRET_RX.search(ln) if env and not found else None
            if m:
                hits.append("{}:{} [env secret] {}".format(p.relative_to(root), i, mask(m.group(0))))
    for h in hits[:20]:
        rep.add("secrets", "FAIL", "worktree " + h)
    if not hits:
        rep.add("secrets", "OK", "워킹트리 {}개 파일에서 0건".format(len(files)))
    if not use_git:
        rep.add("secrets", "INFO", "git 저장소 아님/--no-git → 이력 스캔 건너뜀")
        return
    head = run_git(root, "rev-parse", "--verify", "-q", "HEAD")
    if head in (None, TIMEOUT):
        rep.add("secrets", "INFO", "커밋 없음 → 이력 스캔 대상 없음")
        return
    rng = ["--all"]
    if base:
        b = run_git(root, "rev-parse", "--verify", "-q", base + "^{commit}")
        if b in (None, TIMEOUT):
            rep.add("secrets", "WARN", "--base {} 를 찾을 수 없음 → 전체 이력(--all)으로 스캔".format(base))
        elif b.strip() == head.strip():
            rep.add("secrets", "INFO", "--base == HEAD(새 커밋 없음) → 전체 이력(--all)으로 스캔")
        else:
            rng = ["{}..HEAD".format(base)]
    log = run_git(root, "log", "-p", "--no-color", "--no-ext-diff", *rng, limit=GIT_LOG_MAX, timeout=60)
    if log == TIMEOUT:
        rep.add("secrets", "WARN", "git log -p 60초 초과 → 이력 스캔 못 함. --base REV로 범위를 줄여 다시")
        return
    if log is None:
        rep.add("secrets", "WARN", "git log -p 실패 → 이력 스캔 못 함. 직접 확인: git log -p | grep -nE 'sk-|ghp_|AKIA'")
        return
    commit, found = "?", []
    for ln in log.splitlines():
        if ln.startswith("commit "):
            commit = ln.split()[1][:10]
        elif ln.startswith("+") and not ln.startswith("+++"):
            for name, rx in SECRET_RX.items():
                m = rx.search(ln)
                if m:
                    found.append("history {} [{}] {}".format(commit, name, mask(m.group(0))))
    for h in found[:20]:
        rep.add("secrets", "FAIL", h + " → 이력에 남아 있다. 사람에게 알리고 값은 무효화")
    if not found:
        rep.add("secrets", "OK", "git log -p {}에서 0건".format(rng[0]))


def state_harness_path(notes):
    """notes/STATE.md의 '하네스 경로' 칸 값(절대경로일 때만)."""
    for ln in read_lines(notes / "STATE.md"):
        m = re.match(r"^\|\s*하네스 경로\s*\|\s*([^|]+?)\s*\|", ln)
        if m and m.group(1).startswith("/"):
            return m.group(1).rstrip("/")
    return None


def harness_rx(src, root, notes):
    """(경로 WARN 정규식, import FAIL 정규식). 실제 하네스 경로·STATE 값과, 워크스페이스에 없는 템플릿 모듈
    (예: from spc.spc import, import ml.features)을 덧붙인다."""
    paths = []
    for h in (str(HARNESS), state_harness_path(notes)):
        if h and len(h) > 4 and not str(src).startswith(h) and not str(root).startswith(h):
            paths.append(re.escape(h))
    mods = []
    tdir = HARNESS / "templates"
    for d in sorted(tdir.iterdir()) if tdir.is_dir() else []:
        if d.name.startswith("_") and d.suffix == ".py" and not any((x / d.name).exists() for x in (src, root)):
            mods.append(re.escape(d.stem))                                        # _common
        elif d.is_dir() and (d / "__init__.py").exists() and not any((x / d.name).exists() for x in (src, root)):
            subs = [re.escape(m.stem) for m in d.glob("*.py") if not m.name.startswith(("test_", "__"))]
            if subs:
                mods.append(r"{}\.(?:{})".format(re.escape(d.name), "|".join(subs)))  # spc.spc, ml.features
    imp = HARNESS_IMPORT_PAT
    if mods:
        imp += r"|^\s*(?:from|import)\s+(?:{})\b".format("|".join(mods))
    path = HARNESS_PATH_PAT + "".join("|" + p for p in paths)
    return re.compile(path), re.compile(imp)


def check_harness(files, src, root, notes, rep):
    path_rx, imp_rx = harness_rx(src, root, notes)
    imports, paths = [], []
    for p in files:
        if p.suffix not in (".py", ".sh", ".js", ".ts", ".ipynb"):
            continue
        for i, ln in enumerate(read_lines(p), 1):
            if ln.lstrip().startswith("#"):
                continue
            where = "{}:{}".format(p.relative_to(src), i)
            if imp_rx.search(ln):
                imports.append(where)
            elif path_rx.search(ln):
                paths.append(where)
    if imports:
        rep.add("harness", "FAIL", "하네스 import {}건: {} → 하네스 없는 채점 환경에서 안 돈다. 필요한 함수만 "
                "자기 코드로 옮기고 DECISIONS에 기록".format(len(imports), ", ".join(imports[:10])))
    if paths:
        rep.add("harness", "WARN", "하네스 경로 참조 {}건: {} → 제출물이 하네스 없이 도는지 확인".format(
            len(paths), ", ".join(paths[:10])))
    if not imports and not paths:
        rep.add("harness", "OK", "0건")


def norm_lines(lines):
    out = []
    for ln in lines:
        s = re.sub(r"\s+", " ", ln.strip())
        if len(s) >= 12 and not TRIVIAL_RX.match(s):
            out.append(s)
    return out


def check_copy(files, src, threshold, rep):
    tdir = HARNESS / "templates"
    if not tdir.is_dir():
        rep.add("copy", "INFO", "하네스 templates/ 없음 → 건너뜀")
        return
    tmpl = {}
    for p in tdir.rglob("*.py"):
        if p.name.startswith("test_") or p.name == "__init__.py" or "__pycache__" in p.parts:
            continue
        tmpl[p.relative_to(HARNESS).as_posix()] = set(norm_lines(read_lines(p)))
    flagged = 0
    for p in files:
        if p.suffix != ".py" or HARNESS in p.resolve().parents:
            continue
        mine = norm_lines(read_lines(p))
        if len(mine) < 10:
            continue
        best = max(((sum(1 for s in mine if s in t), name) for name, t in tmpl.items()), default=(0, ""))
        ratio = best[0] / len(mine)
        if ratio >= threshold and best[0] >= 15:
            flagged += 1
            rep.add("copy", "WARN", "{}: {}/{}줄({:.0%})이 {}와 같음 → 통째 복사 의심. 고친 부분과 출처를 DECISIONS에".format(
                p.relative_to(src), best[0], len(mine), ratio, best[1]))
    if not flagged:
        rep.add("copy", "OK", "임계값 {:.0%} 이상 복사 파일 0".format(threshold))


def check_env_file(root, use_git, rep):
    """추적 여부와 상관없이 워크스페이스 안에 있으면 제출 스냅샷에 섞일 수 있다."""
    here = [n for n in ("ENVIRONMENT.md", "_harness") if (root / n).exists()]
    tracked = run_git(root, "ls-files", "--", "ENVIRONMENT.md", "_harness") if use_git else None
    tracked = tracked.split() if tracked and tracked != TIMEOUT else []
    if tracked:
        rep.add("env_file", "WARN", "git에 추적됨: {} → 커밋 대상에서 빼기(사람이 판단)".format(", ".join(tracked[:5])))
    if here:
        rep.add("env_file", "WARN", "워크스페이스 안에 있음: {} → 제출 전 워크스페이스 밖으로 이동"
                "(예: mv ENVIRONMENT.md /tmp/)".format(", ".join(here)))
    if not tracked and not here:
        rep.add("env_file", "OK", "ENVIRONMENT.md·_harness 없음")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0],
                                 epilog=__doc__.split("\n", 2)[2], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--src")
    ap.add_argument("--notes")
    ap.add_argument("--require", action="append", default=[])
    ap.add_argument("--base", help="이력 스캔 시작 커밋(기본: 전체 이력)")
    ap.add_argument("--copy-threshold", type=float, default=0.5)
    ap.add_argument("--no-git", action="store_true")
    ap.add_argument("--strict", action="store_true", help="WARN도 exit 1")
    a = ap.parse_args(argv)

    root = Path(a.root).resolve()
    src = root
    if a.src:  # 상대 경로는 ROOT 기준을 먼저(cwd가 ROOT가 아니어도 동작)
        src = (root / a.src).resolve() if (root / a.src).is_dir() else Path(a.src).resolve()
    notes = Path(a.notes).resolve() if a.notes else root / "notes"
    if not root.is_dir() or not src.is_dir():
        print("presubmit: 폴더 없음: {}".format(src if root.is_dir() else root), file=sys.stderr)
        return 2
    use_git = not a.no_git and run_git(root, "rev-parse", "--git-dir") not in (None, TIMEOUT)
    files = list_files(src, use_git and src == root)
    secret_files = list_files(root, use_git, SECRET_SKIP)

    rep = Report()
    check_required(src, root, a.require, rep)
    check_readme(src, root, rep)
    check_notes(notes, rep)
    check_todo(files, src, rep)
    check_secrets(secret_files, root, use_git, a.base, rep)
    check_harness(files, src, root, notes, rep)
    check_copy(files, src, a.copy_threshold, rep)
    check_env_file(root, use_git, rep)

    print("# presubmit — {} (파일 {}개, git {})".format(src, len(files), "yes" if use_git else "no"))
    print("| 검사 | 결과 | 내용 |\n|---|---|---|")
    for c, lv, msg in rep.rows:
        print("| {} | {} | {} |".format(c, lv, msg.replace("|", "\\|")))
    fail, warn = rep.count("FAIL"), rep.count("WARN")
    print("\nFAIL {} · WARN {} · OK {} · INFO {}".format(fail, warn, rep.count("OK"), rep.count("INFO")))
    if not rep.rows:
        return 2
    return 1 if fail or (a.strict and warn) else 0


if __name__ == "__main__":
    sys.exit(main())
