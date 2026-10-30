"""scripts/ 회귀 테스트: presubmit 하네스 의존·.env·--src 폴백·이력 범위, profile_data 인코딩·중복 열·표본 뒤 줄 수,
run_and_log env 접두·한글 태그·손자 정리. 차용 없음.
실행: python3 -m unittest discover -s tests -v
"""
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESUBMIT = ROOT / "scripts" / "presubmit.py"
PROFILE = ROOT / "scripts" / "profile_data.py"
RUN_AND_LOG = ROOT / "scripts" / "run_and_log.sh"


class PresubmitHardeningTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self._tmp.name)
        (self.ws / "README.md").write_text("```\npython3 src/main.py\n```\n", encoding="utf-8")
        (self.ws / "src").mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def run_ps(self, *args):
        return subprocess.run([sys.executable, str(PRESUBMIT), str(self.ws), *args],
                              capture_output=True, text=True, timeout=60)

    def test_harness_import_fails_and_path_warns(self):
        (self.ws / "src" / "main.py").write_text(
            "import sys, importlib, os\n"
            "sys.path.append('/home/user/hx')\n"                         # 2 경로 WARN
            "m = importlib.import_module('templates.ml.features')\n"     # 3 import FAIL
            "p = os.path.join(os.environ['H'], 'x')\n"                   # 4 경로 WARN
            "from spc.spc import cp_cpk\n"                                # 5 템플릿 모듈 FAIL
            "DATA = '/opt/hx2/data.csv'\n", encoding="utf-8")             # 6 STATE의 하네스 경로 → WARN
        (self.ws / "notes").mkdir()
        (self.ws / "notes" / "STATE.md").write_text("| 하네스 경로 | /opt/hx2 |\n", encoding="utf-8")
        r = self.run_ps("--no-git", "--src", "src")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertRegex(r.stdout, r"\| harness \| FAIL \| 하네스 import 2건: main\.py:3, main\.py:5")
        self.assertRegex(r.stdout, r"\| harness \| WARN \| 하네스 경로 참조 3건: main\.py:2, main\.py:4, main\.py:6")

    def test_own_package_with_template_name_is_not_harness(self):
        (self.ws / "src" / "ml").mkdir()
        (self.ws / "src" / "ml" / "__init__.py").write_text("", encoding="utf-8")
        (self.ws / "src" / "ml" / "features.py").write_text("X = 1\n", encoding="utf-8")
        (self.ws / "src" / "main.py").write_text("from ml.features import X\nimport schedule\nprint(X)\n",
                                                  encoding="utf-8")
        r = self.run_ps("--no-git", "--src", "src")
        self.assertIn("| harness | OK | 0건 |", r.stdout)

    def test_src_falls_back_to_root_readme(self):
        (self.ws / "src" / "main.py").write_text("print(1)\n", encoding="utf-8")
        r = self.run_ps("--no-git", "--src", "src", "--require", "README.md")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("| required | OK | README.md (ROOT에서 찾음) |", r.stdout)
        self.assertRegex(r.stdout, r"\| readme \| OK \| 실행 명령 1개")
        r = self.run_ps("--no-git", "--src", "src", "--require", "nope.txt")
        self.assertIn("| required | FAIL | nope.txt |", r.stdout)

    def test_unquoted_env_secret(self):
        (self.ws / ".env").write_text("DB_PASSWORD=hunter2hunter2\nexport OPENAI_KEY=abcdEFGHijklMNOP\n"
                                      "API_TOKEN=$FROM_ENV_VAR\nDEBUG=1\n", encoding="utf-8")
        (self.ws / ".env.example").write_text("DB_PASSWORD=your-password-here\n", encoding="utf-8")
        (self.ws / "prod.env").write_text("SERVICE_CREDENTIAL=zzzzYYYYxxxx\n", encoding="utf-8")
        r = self.run_ps("--no-git")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("worktree .env:1 [env secret]", r.stdout)
        self.assertIn("worktree .env:2 [env secret]", r.stdout)
        self.assertIn("worktree prod.env:1 [env secret]", r.stdout)
        self.assertNotIn(".env:3", r.stdout)                        # $VAR 참조는 값 아님
        self.assertNotIn(".env.example", r.stdout)                  # 예시 파일은 자리표시자
        for v in ("hunter2hunter2", "abcdEFGHijklMNOP", "zzzzYYYYxxxx"):
            self.assertNotIn(v, r.stdout)

    def test_environment_md_and_fallback_harness_present(self):
        (self.ws / "ENVIRONMENT.md").write_text("STATUS: READY\n", encoding="utf-8")
        (self.ws / "_harness").mkdir()
        r = self.run_ps("--no-git")
        self.assertRegex(r.stdout, r"\| env_file \| WARN \| 워크스페이스 안에 있음: ENVIRONMENT\.md, _harness")
        self.assertEqual(self.run_ps("--no-git", "--strict").returncode, 1)
        os.remove(self.ws / "ENVIRONMENT.md")
        os.rmdir(self.ws / "_harness")
        self.assertIn("| env_file | OK |", self.run_ps("--no-git").stdout)

    @unittest.skipUnless(shutil.which("git"), "git 없음")
    def test_base_errors_are_warned_and_empty_range_scans_all(self):
        g = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "init.defaultBranch=main"]
        env = dict(os.environ, HOME=str(self.ws), GIT_CONFIG_NOSYSTEM="1")
        (self.ws / "cfg.py").write_text("token = 'ghp_" + "c" * 36 + "'\n", encoding="utf-8")
        for cmd in (["init", "-q"], ["add", "README.md", "cfg.py"], ["commit", "-qm", "x"], ["rm", "-q", "cfg.py"],
                    ["commit", "-qm", "rm"]):
            subprocess.run(g + cmd, cwd=self.ws, check=True, capture_output=True, env=env)
        r = self.run_ps("--base", "no-such-rev")
        self.assertRegex(r.stdout, r"\| secrets \| WARN \| --base no-such-rev 를 찾을 수 없음")
        self.assertRegex(r.stdout, r"\| secrets \| FAIL \| history [0-9a-f]+ \[github token\]")  # --all로 대신 스캔
        r = self.run_ps("--base", "HEAD")
        self.assertRegex(r.stdout, r"\| secrets \| INFO \| --base == HEAD")
        self.assertRegex(r.stdout, r"\| secrets \| FAIL \| history ")
        self.assertNotIn("c" * 36, r.stdout)


class ProfileDataTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def prof(self, path, *args):
        r = subprocess.run([sys.executable, str(PROFILE), str(path), "--top", "0", *args],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def test_cp949_after_first_64kb_is_detected(self):
        p = self.d / "late.csv"
        with open(p, "wb") as fh:
            fh.write(b"id,status\n" + b"".join(b"%d,OK\n" % i for i in range(9000)))
            fh.write("9000,이상\n".encode("cp949"))
        self.assertGreater(p.stat().st_size, 65536)
        out = self.prof(p)
        self.assertIn("encoding=cp949", out)
        self.assertIn("WARN: utf-8로 읽으니 깨진 글자", out)
        self.assertIn("rows=9001", out)

    def test_duplicate_header_names_are_split(self):
        p = self.d / "dup.csv"
        p.write_text("id,val,val\n1,10,999\n2,11,998\n", encoding="utf-8")
        out = self.prof(p)
        self.assertIn("- val [int] missing=0 (0.0%) unique=2 range=10 .. 11", out)
        self.assertIn("- val.1 [int] missing=0 (0.0%) unique=2 range=998 .. 999", out)

    def test_rows_after_sample_counted_without_parsing(self):
        p = self.d / "s.csv"
        p.write_text("a,b\n" + "".join("{},{}\n".format(i, i * 2) for i in range(500)) + "\n\n", encoding="utf-8")
        out = self.prof(p, "--sample", "50")
        self.assertIn("rows=500 sampled=50", out)
        self.assertIn("rows_after_sample=raw_lines", out)
        out = self.prof(p, "--max-rows", "100")
        self.assertIn("rows=100+ (stopped at --max-rows)", out)
        out = self.prof(p, "--sample", "50", "--max-rows", "120")
        self.assertIn("rows=120+ (stopped at --max-rows)", out)

    def test_quoted_newlines_keep_exact_count(self):
        p = self.d / "q.csv"
        p.write_text('id,txt\n1,"a\nb"\n2,c\n3,"d\ne"\n', encoding="utf-8")
        out = self.prof(p, "--sample", "1")
        self.assertIn("rows=3 sampled=1", out)
        self.assertNotIn("raw_lines", out)


def wait_end_line(path, timeout=5.0):
    deadline = time.time() + timeout
    text = ""
    while time.time() < deadline:
        text = Path(path).read_text(encoding="utf-8")
        if "# end:" in text:
            break
        time.sleep(0.1)
    return text


class RunAndLogMoreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ws = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def logs(self):
        return sorted((Path(self.ws) / "logs").glob("*.log"))

    def test_env_prefix_and_korean_tag(self):
        r = subprocess.run(["bash", str(RUN_AND_LOG), "한글 태그/x", "--", "OMP_NUM_THREADS=2", "sh", "-c",
                            "echo omp=$OMP_NUM_THREADS unbuf=$PYTHONUNBUFFERED"],
                           cwd=self.ws, capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("omp=2 unbuf=1", r.stdout)
        (log,) = self.logs()
        self.assertRegex(log.name, r"^\d{8}-\d{6}_한글_태그_x\.log$")
        self.assertIn("exit=0", wait_end_line(log))

    def test_signal_with_grandchild_ends_quickly(self):
        p = subprocess.Popen(["bash", str(RUN_AND_LOG), "gc", "--", "sh", "-c", "sleep 30 & sleep 30"], cwd=self.ws,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.0)
        t = time.time()
        p.send_signal(signal.SIGTERM)
        self.assertEqual(p.wait(timeout=10), 143)
        self.assertLess(time.time() - t, 6.0)                 # 손자가 파이프를 잡아도 최대 약 3초 뒤 끝난다
        (log,) = self.logs()
        self.assertIn("signal TERM", wait_end_line(log))


if __name__ == "__main__":
    unittest.main()
