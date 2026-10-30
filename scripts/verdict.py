#!/usr/bin/env python3
"""verdict.py — 검사 명령을 실행해 PASS/FAIL/NOT_RUN 표를 출력하는 판정기 (stdlib, 외부 호출 없음).

차용 없음(검사 0건=실패 아이디어는 hamjoon2003/sk-hynix-2nd-harness·hongkevin/cofathon-prep 참고, 코드 새로 작성).

사용:
  python3 verdict.py --check "unit:python3 -m unittest -q" --check "smoke:python3 main.py --help"
  python3 verdict.py --spec checks.json [--md] [--timeout 120] [--tail 5]
  checks.json = [{"name": "unit", "cmd": "python3 -m unittest -q", "timeout": 60}, ...]
  cmd가 비었거나 "skip": true면 NOT_RUN(실행하지 않음).

종료 코드: 0 = 전부 PASS / 1 = FAIL 또는 NOT_RUN 하나 이상 / 2 = 검사 0건(아무것도 검사 안 함 = 실패)
테스트 0건도 실패: exit 0이어도 출력에 "Ran 0 tests"·"NO TESTS RAN"·"collected 0 items"·"no tests ran"이
있으면 FAIL(0 tests). (Python 3.11 unittest discover는 0건이어도 exit 0이다.)
"""
import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time


# 테스트 러너가 "아무것도 안 돌렸다"고 말하는 출력 (unittest·pytest)
ZERO_TESTS = re.compile(r"^Ran 0 tests?\b|NO TESTS RAN|collected 0 items|no tests ran", re.M | re.I)


def load_checks(args):
    checks = []
    for item in args.check or []:
        name, sep, cmd = item.partition(":")      # 첫 ':'에서만 나눔
        if not sep:
            name, cmd = item, ""
        checks.append({"name": name.strip(), "cmd": cmd.strip()})
    if args.spec:
        with open(args.spec, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            data = data.get("checks", [])
        for c in data:
            checks.append({"name": str(c.get("name", "?")), "cmd": str(c.get("cmd", "")).strip(),
                           "timeout": c.get("timeout"), "skip": bool(c.get("skip"))})
    return checks


def run_check(c, default_timeout, tail):
    if c.get("skip") or not c["cmd"]:
        return {"name": c["name"], "cmd": c["cmd"], "result": "NOT_RUN", "code": "-",
                "sec": 0.0, "evidence": "not executed"}
    t0 = time.time()
    # 새 세션으로 띄워 시간 초과 때 손자 프로세스까지 그룹째 종료
    p = subprocess.Popen(c["cmd"], shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, errors="replace", start_new_session=True)
    try:
        out, _ = p.communicate(timeout=c.get("timeout") or default_timeout)
        code = p.returncode
        result = "PASS" if code == 0 else "FAIL"
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            p.kill()
        try:   # 다른 세션으로 빠져나간 손자가 파이프를 잡고 있으면 2초만 기다리고 끊는다
            out, _ = p.communicate(timeout=2)
        except subprocess.TimeoutExpired as e:
            out = e.output.decode(errors="replace") if isinstance(e.output, bytes) else e.output
            p.stdout.close()
        code, result = "timeout", "FAIL"
    out = out or ""
    lines = [ln for ln in out.strip().splitlines() if ln.strip()]
    evidence = " / ".join(lines[-tail:]) if lines else "(no output)"
    if ZERO_TESTS.search(out):
        result, evidence = "FAIL", "0 tests ran / " + evidence
    return {"name": c["name"], "cmd": c["cmd"], "result": result, "code": code,
            "sec": round(time.time() - t0, 1), "evidence": evidence[:400]}


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def render(rows, md):
    if md:
        out = ["| 검사 | 명령 | 결과 | exit | 초 | 증거(출력 끝) |", "|---|---|---|---|---|---|"]
        out += ["| {} | `{}` | {} | {} | {} | {} |".format(cell(r["name"]), cell(r["cmd"]), r["result"],
                r["code"], r["sec"], cell(r["evidence"])) for r in rows]
        return "\n".join(out)
    w = max([len(r["name"]) for r in rows] + [4])
    out = ["{:<{w}}  {:<7}  {:>7}  {}".format("name", "result", "exit", "evidence", w=w)]
    out += ["{:<{w}}  {:<7}  {:>7}  {}".format(r["name"], r["result"], str(r["code"]), r["evidence"], w=w)
            for r in rows]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run checks and print a PASS/FAIL/NOT_RUN table. "
                                 "exit 0=all pass, 1=any FAIL/NOT_RUN, 2=zero checks. "
                                 "Output saying 0 tests ran (unittest/pytest) is FAIL.")
    ap.add_argument("--check", action="append", metavar="NAME:CMD", help="repeatable; empty CMD = NOT_RUN")
    ap.add_argument("--spec", metavar="JSON", help='list of {"name","cmd","timeout","skip"}')
    ap.add_argument("--timeout", type=float, default=120.0, help="seconds per check (default 120)")
    ap.add_argument("--tail", type=int, default=3, help="output lines kept as evidence (default 3)")
    ap.add_argument("--md", action="store_true", help="markdown table (paste into DECISIONS §3)")
    args = ap.parse_args(argv)

    checks = load_checks(args)
    if not checks:
        print("VERDICT: FAIL (0 checks — nothing was verified)")
        return 2
    rows = [run_check(c, args.timeout, args.tail) for c in checks]
    print(render(rows, args.md))
    n = {k: sum(r["result"] == k for r in rows) for k in ("PASS", "FAIL", "NOT_RUN")}
    ok = n["FAIL"] == 0 and n["NOT_RUN"] == 0
    print("\nVERDICT: {} (PASS {} / FAIL {} / NOT_RUN {})".format("PASS" if ok else "FAIL",
          n["PASS"], n["FAIL"], n["NOT_RUN"]))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
