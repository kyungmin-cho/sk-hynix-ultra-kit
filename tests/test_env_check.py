"""scripts/env_check.sh 검사 (python3 표준 라이브러리 unittest).

실행: python3 -m unittest discover -s tests -v
- 기본은 --quick --no-network 위주라 네트워크 없이 돈다.
- HX_TEST_NETWORK=1 이면 네트워크를 켠 표준 모드도 한 번 돌려 쓰기 0건을 확인한다.
차용 없음.
"""
import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "env_check.sh"
BASH = shutil.which("bash") or "/bin/bash"
GIT = shutil.which("git")

TAIL_RE = re.compile(
    r"^<!-- hx-env v1: STATUS=(READY|PARTIAL|BLOCKED) PY=\S+ PIP_NET=(ok|blocked|unknown) "
    r"PANDAS=\S+ SKLEARN=\S+ GPU=\d+ NPROC=\d+ MEM_EFF_GB=\d+(\.\d+)? PIDS_MAX=(\d+|max) "
    r"PAR_MAX=\d+ SOCKET=(ok|denied) CODEX_EXEC=(yes|no) GIT_REMOTE=[01] DATA_MB=\d+ "
    r"TZ_OFF=[+-]\d{4} CGROUP=(v2|v1|none) -->$"
)
SECTIONS = ["## 1. 종합 판정", "## 2. 판정 규칙", "## 3. 표시값 vs 실측", "## 4. 서술형용 환경 사실 3줄",
            "## 5. 상세", "### 5.1", "### 5.2", "### 5.3", "### 5.4", "### 5.5", "### 5.6", "### 5.7",
            "### 5.8", "## 7. 사람 전용 체크리스트"]


def tail_of(out):
    lines = [l for l in out.splitlines() if l.strip()]
    return lines[-1] if lines else ""


def tail_fields(out):
    body = tail_of(out)[len("<!-- hx-env v1: "):-len(" -->")]
    return dict(kv.split("=", 1) for kv in body.split())


def snapshot(*dirs):
    seen = set()
    for d in dirs:
        for base, subdirs, files in os.walk(d):
            if os.sep + ".config" + os.sep + "go" in base + os.sep or base.endswith(os.sep + ".config"):
                continue          # go 툴체인이 `go version`만으로 쓰는 텔레메트리 파일은 환경 점검 탓이 아니다
            for name in subdirs + files:
                if name == "go" and base.endswith(os.sep + ".config"):
                    continue
                if name == ".config" and os.listdir(os.path.join(base, name)) == ["go"]:
                    continue
                seen.add(os.path.join(base, name))
    return seen


class EnvCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hx-envtest-"))
        self.ws = self.tmp / "workspace"
        self.home = self.tmp / "home"
        self.ws.mkdir()
        self.home.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_env(self, *args, extra_env=None, path=None, timeout=60):
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        for k in ("HX_DISPLAY_MEM", "HX_DISPLAY_CPU", "HX_PAR_CAP", "CODEX_HOME"):
            env.pop(k, None)
        if path is not None:
            env["PATH"] = path
        env.update(extra_env or {})
        t0 = time.time()
        p = subprocess.run([BASH, str(SCRIPT), *args], cwd=str(self.ws), env=env,
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
        p.elapsed = time.time() - t0
        return p

    def quick(self, *args, **kw):
        return self.run_env("--stdout", "--quick", "--no-network", *args, **kw)

    # --- 형식 ---
    def test_required_sections_status_and_tail(self):
        p = self.quick()
        self.assertEqual(p.returncode, 0, p.stderr)
        out = p.stdout
        self.assertRegex(out, re.compile(r"^STATUS: (READY|PARTIAL|BLOCKED)$", re.M))
        self.assertIn("STATUS:", "\n".join(out.splitlines()[:8]))  # 첫 부분에 STATUS
        for s in SECTIONS:
            self.assertIn(s, out)
        for r in ("R0", "R7", "R12", "R16"):  # 항상 ACTIVE인 규칙
            self.assertRegex(out, re.compile(r"^\[ACTIVE\] %s " % r, re.M))
        ids = re.findall(r"^\[(?:ACTIVE|INACTIVE)\] (R\d+) ", out, re.M)
        self.assertEqual(sorted(set(ids), key=lambda x: int(x[1:])), ["R%d" % i for i in range(18)])
        self.assertRegex(tail_of(out), TAIL_RE)
        self.assertEqual(tail_fields(out)["PIP_NET"], "unknown")  # --no-network
        self.assertNotEqual(tail_fields(out)["STATUS"], "READY")  # PyPI 미측정·차단 → PARTIAL 이하

    def test_active_lines_come_before_inactive(self):
        lines = self.quick().stdout.splitlines()
        act = [i for i, l in enumerate(lines) if l.startswith("[ACTIVE] ")]
        ina = [i for i, l in enumerate(lines) if l.startswith("[INACTIVE] ")]
        self.assertTrue(act)
        if ina:
            self.assertLess(max(act), min(ina))

    def test_quick_is_fast(self):
        p = self.quick()
        self.assertEqual(p.returncode, 0)
        self.assertLess(p.elapsed, 5.0, "quick 모드는 3초 목표(여유 5초)")

    def test_help_and_bad_option(self):
        h = self.run_env("--help")
        self.assertEqual(h.returncode, 0)
        for opt in ("--out", "--stdout", "--quick", "--no-network", "--data-dir", "--diff", "--pip-probe", "--timeout"):
            self.assertIn(opt, h.stdout)
        self.assertNotIn("--net-extra", h.stdout)   # 금지 API 호스트로 가는 옵션은 없앴다
        self.assertEqual(self.run_env("--nope").returncode, 2)
        self.assertEqual(self.run_env("--net-extra").returncode, 2)

    def fake_python_logging(self):
        """PATH 앞에 python3 래퍼: 받은 인자를 기록하고 진짜 python3를 실행한다."""
        real = shutil.which("python3")
        if real is None:
            self.skipTest("python3 없음")
        b = self.tmp / "fakebin"
        b.mkdir()
        log = self.tmp / "py-args.log"
        (b / "python3").write_text('#!/bin/sh\nprintf "%%s\\n" "$*" >> "%s"\nexec "%s" "$@"\n' % (log, real))
        (b / "python3").chmod(0o755)
        return str(b) + os.pathsep + os.environ.get("PATH", ""), log

    def test_pip_dry_run_only_with_pip_probe(self):
        path, log = self.fake_python_logging()
        p = self.run_env("--stdout", "--timeout", "1", path=path)       # 기본: 네트워크 켬
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("pip install", log.read_text() if log.exists() else "")
        self.assertIn("pip dry-run: 실행 안 함(기본)", p.stdout)
        log.unlink()
        p = self.run_env("--stdout", "--timeout", "1", "--pip-probe", path=path)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("pip install --dry-run", log.read_text())
        self.assertIn("pip-probe", p.stdout)                              # 모드 표시

    def test_data_preview_masks_secret_values(self):
        (self.ws / "data").mkdir()
        (self.ws / "data" / "x.csv").write_text(
            "id,Api_Key,note\n1,Api_Key=sk-abcdefABCDEF1234567,ghp_ABCDEFGHIJKL1234 Credential: hunter2xx\n")
        p = self.run_env("--stdout", "--no-network")
        self.assertEqual(p.returncode, 0, p.stderr)
        for leak in ("sk-abcdef", "ghp_ABCD", "hunter2xx"):
            self.assertNotIn(leak, p.stdout)
        (self.ws / "data" / "x.csv").write_text("contest\nsk-hynix-hackathon\n")   # 대회 이름은 가리지 않는다
        self.assertIn("sk-hynix-hackathon", self.run_env("--stdout", "--no-network").stdout)
        self.assertIn("./data/x.csv", p.stdout)

    # --- 비밀값 ---
    def test_secrets_are_masked(self):
        codex = self.home / ".codex"
        codex.mkdir()
        (codex / "config.toml").write_text(
            'model = "test-model"\napi_key = "hxsecret_cfg_111"\n'
            '[mcp_servers.demo]\ncommand = "x"\nenv = { GITHUB_TOKEN = "hxsecret_mcp_222" }\n')
        (self.home / ".npmrc").write_text("//registry.npmjs.org/:_authToken=hxsecret_npm_333\n")
        env = {
            "HX_FAKE_TOKEN": "hxsecret_env_444",
            "PIP_FAKE_TOKEN": "hxsecret_pip_555",
            "HTTPS_PROXY": "http://user:hxsecret_proxy_666@proxy.invalid:3128",
            "PIP_INDEX_URL": "https://u:hxsecret_index_777@mirror.invalid/simple",
        }
        out = self.quick(extra_env=env).stdout
        self.assertNotIn("hxsecret", out)
        self.assertIn("***@proxy.invalid", out)
        self.assertIn("PIP_FAKE_TOKEN=***", out)
        self.assertIn('model = "test-model"', out)  # 비밀 아닌 키는 보고
        self.assertIn("demo", out)  # mcp 서버 이름만

    @unittest.skipIf(GIT is None, "git 없음")
    def test_git_remote_warning_and_masking(self):
        g = self.ws / ".git"  # 저장소를 손으로 구성(스크립트·테스트가 저장소를 만드는 명령을 쓰지 않음)
        (g / "objects").mkdir(parents=True)
        (g / "refs" / "heads").mkdir(parents=True)
        (g / "HEAD").write_text("ref: refs/heads/main\n")
        (g / "config").write_text(
            "[core]\n\trepositoryformatversion = 0\n\tbare = false\n"
            '[remote "origin"]\n\turl = https://u:hxsecret_git_888@github.com/x/y.git\n'
            "\tfetch = +refs/heads/*:refs/remotes/origin/*\n")
        before = (g / "config").read_text()
        out = self.quick().stdout
        self.assertNotIn("hxsecret", out)
        self.assertIn("***@github.com", out)
        self.assertEqual(tail_fields(out)["GIT_REMOTE"], "1")
        self.assertRegex(out, re.compile(r"^\[ACTIVE\] R2 ", re.M))
        self.assertEqual((g / "config").read_text(), before)  # 경고만, remote 불변

    # --- 쓰기 최소 ---
    def test_stdout_mode_writes_nothing(self):
        (self.ws / "data").mkdir()
        (self.ws / "data" / "a.csv").write_text("x,y\n1,2\n")
        before = snapshot(self.ws, self.home)
        self.assertEqual(self.quick().returncode, 0)
        self.assertEqual(snapshot(self.ws, self.home), before)

    def test_standard_no_network_writes_nothing(self):
        before = snapshot(self.ws, self.home)
        p = self.run_env("--stdout", "--no-network")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertRegex(tail_of(p.stdout), TAIL_RE)
        self.assertLess(p.elapsed, 15.0)
        self.assertEqual(snapshot(self.ws, self.home), before)

    @unittest.skipUnless(os.environ.get("HX_TEST_NETWORK") == "1", "HX_TEST_NETWORK=1일 때만")
    def test_standard_with_network_writes_nothing(self):
        before = snapshot(self.ws, self.home)
        p = self.run_env("--stdout")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertRegex(tail_of(p.stdout), TAIL_RE)
        self.assertIn(tail_fields(p.stdout)["PIP_NET"], ("ok", "blocked"))
        self.assertLess(p.elapsed, 15.0)
        self.assertEqual(snapshot(self.ws, self.home), before)

    def test_out_creates_only_that_file(self):
        before = snapshot(self.ws, self.home)
        p = self.run_env("--quick", "--no-network", "--out", "env.md")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("STATUS:", p.stdout)
        self.assertEqual(snapshot(self.ws, self.home) - before, {str(self.ws / "env.md")})
        text = (self.ws / "env.md").read_text()
        self.assertRegex(tail_of(text), TAIL_RE)

    def test_default_out_is_environment_md(self):
        self.assertEqual(self.run_env("--quick", "--no-network").returncode, 0)
        self.assertTrue((self.ws / "ENVIRONMENT.md").is_file())

    # --- diff ---
    def test_diff_reports_changed_keys(self):
        self.assertEqual(self.run_env("--quick", "--no-network", "--out", "old.md").returncode, 0)
        old = self.ws / "old.md"
        old.write_text(re.sub(r"NPROC=\d+", "NPROC=9999", old.read_text()))
        out = self.quick("--diff", "old.md").stdout
        self.assertIn("## 6. 바뀐 항목", out)
        self.assertIn("NPROC: 9999 →", out)
        same = self.quick("--diff", "ENVIRONMENT.md").stdout  # 없는 파일
        self.assertIn("읽을 수 없음", same)

    # --- python 없음 ---
    def test_runs_without_python_on_path(self):
        nopy = self.tmp / "nopy-bin"
        nopy.mkdir()
        for d in os.environ.get("PATH", "").split(os.pathsep):
            if not os.path.isdir(d):
                continue
            for name in os.listdir(d):
                if name.startswith(("python", "pip", "pydoc", "idle")) or (nopy / name).exists():
                    continue
                src = os.path.join(d, name)
                if os.path.isfile(src) and os.access(src, os.X_OK):
                    os.symlink(src, nopy / name)
        p = self.quick(path=str(nopy))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("N/A(python 없음)", p.stdout)
        self.assertRegex(tail_of(p.stdout), TAIL_RE)
        self.assertEqual(tail_fields(p.stdout)["PY"], "none")
        # python 없음: Python 도구를 못 쓴다고 명시(R17), parse_ts 안내(R9)는 끈다
        self.assertRegex(p.stdout, re.compile(r"^\[ACTIVE\] R17 python3 없음", re.M))
        self.assertRegex(p.stdout, re.compile(r"^\[INACTIVE\] R9 ", re.M))

    # --- 데이터·자원·시간 ---
    def test_data_inventory_and_extra_dir(self):
        (self.ws / "data").mkdir()
        (self.ws / "data" / "train.csv").write_text("a,b\n1,2\n")
        extra = self.tmp / "extra"
        extra.mkdir()
        (extra / "log.jsonl").write_text('{"t": 1}\n')
        out = self.quick("--data-dir", str(extra)).stdout
        self.assertIn("./data/train.csv", out)
        self.assertIn("log.jsonl", out)
        self.assertEqual(tail_fields(out)["DATA_MB"], "0")

    def test_display_memory_lowers_effective_value(self):
        out = self.quick(extra_env={"HX_DISPLAY_MEM": "1G"}).stdout
        f = tail_fields(out)
        self.assertEqual(f["MEM_EFF_GB"], "1.0")
        self.assertEqual(f["PAR_MAX"], "1")
        self.assertNotEqual(f["STATUS"], "READY")  # 유효 메모리 < 2GB

    def test_non_kst_container_clock_is_flagged(self):
        out = self.quick(extra_env={"TZ": "UTC"}).stdout
        self.assertEqual(tail_fields(out)["TZ_OFF"], "+0000")
        self.assertRegex(out, re.compile(r"^\[ACTIVE\] R16 .*\+0000 ≠ \+0900", re.M))
        self.assertRegex(out, r"생성 \d{4}-\d\d-\d\d \d\d:\d\d:\d\d KST")

    # --- 금지 문자열 ---
    def test_no_state_changing_commands_in_script(self):
        lines = SCRIPT.read_text(encoding="utf-8").splitlines()
        dry = [l for l in lines if "install" in l.lower()]
        self.assertLessEqual(len(dry), 1)
        for l in dry:  # 허용: 설치 가능성 조회(dry-run) 한 곳
            self.assertIn("--dry-run", l)
        for i, l in enumerate(lines, 1):
            self.assertNotRegex(l.lower(), r"\b(update|upgrade)\b", "line %d" % i)


if __name__ == "__main__":
    unittest.main()
