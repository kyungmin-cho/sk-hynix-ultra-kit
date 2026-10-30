"""check_output — 출력 파일이 약속한 형식(계약)을 지키는지 독립적으로 검사 (stdlib only).

언제 쓰나: 제출 CSV/JSON의 열·타입·행 수·키 유일성·값 범위를 '만든 코드와 별개로' 확인할 때.
실행: python3 check_output.py OUTPUT.csv --spec spec.json [--json]
참고 출력: CLI·함수 결과는 참고 구현의 출력이다. 결론은 근거(행 수·실패 수·입력 검증)로 확인하고, 결과물에는 필요한 함수만 자기 코드로 옮긴다.
  종료 코드 0 = 모든 검사 통과, 1 = 하나 이상 실패, 2 = 검사 0건·입력 없음·0행·읽기 실패(= 실패로 취급).
spec 예:
  {"rows": {"min": 1, "max": 100000},
   "columns": {"wafer_id": {"type": "str", "nullable": false},
               "score": {"type": "float", "min": 0, "max": 1},
               "label": {"type": "str", "allowed": ["OK", "NG"]},
               "ts": {"type": "datetime", "required": false}},
   "unique": [["wafer_id"]], "exact_columns": false}
  type: int | float | str | bool | datetime(ISO 형식: YYYY-MM-DD[ T]HH:MM[:SS[.f]][Z|±HH:MM]).
  required(기본 true): 열 존재. nullable(기본 true): 빈 값 허용. 빈 값('', None)은 타입·범위 검사에서 뺀다.
입력: .csv(utf-8-sig, 구분자 추정), .json(객체 목록 또는 {"rows": [...]}) , .jsonl.
  함수로 쓰려면 check(rows, spec) → 보고 dict, gen_fixture(spec, n)로 계약을 만족하는 합성 행을 만든다.
한계: 행 간 업무 규칙(합계 일치 등)은 검사하지 않는다 → 필요하면 check() 결과에 직접 검사를 더한다.
  이 검사 통과 = 형식이 맞다는 뜻이지 내용이 옳다는 뜻이 아니다.
출처: 차용 없음(직접 작성). hongkevin/cofathon-prep probe-starter/scripts/check_output.py의
  "exit 2 = 아무것도 검사하지 않음" 아이디어만 참고(로컬 사본에 LICENSE 파일이 없어 코드 복사 없음).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import sys
from typing import Dict, List, Optional, Sequence

_DT = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?)?\s*(Z|[+-]\d{2}:?\d{2})?$")
_BOOL = {"true", "false", "1", "0", "yes", "no", "y", "n"}


def _empty(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def _typed(v, t: str):
    """타입에 맞으면 비교 가능한 값, 아니면 ValueError."""
    if t == "str":
        return str(v)
    if t == "bool":
        if isinstance(v, bool) or str(v).strip().lower() in _BOOL:
            return v
        raise ValueError
    if t == "datetime":
        if _DT.match(str(v).strip()):
            return str(v).strip()
        raise ValueError
    if isinstance(v, bool):
        raise ValueError
    if t == "int":
        if isinstance(v, int) or re.fullmatch(r"[+-]?\d+", str(v).strip()):
            return int(v)
        raise ValueError
    if t == "float":
        x = float(v)
        if not math.isfinite(x):
            raise ValueError
        return x
    raise ValueError("unknown type %r" % t)


def _bad(rows: Sequence[Dict], col: str, pred) -> List[int]:
    """조건을 어기는(또는 검사 중 예외가 나는) 행 번호(1부터). 빈 값은 건너뛴다."""
    def fails(v):
        try:
            return not pred(v)
        except (TypeError, ValueError):
            return True
    return [i + 1 for i, r in enumerate(rows) if not _empty(r.get(col)) and fails(r.get(col))]


def check(rows: Optional[Sequence[Dict]], spec: Dict) -> Dict:
    checks: List[Dict] = []

    def add(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    if rows is None or not rows:
        return {"checks": [], "n_checks": 0, "n_failed": 0, "exit_code": 2,
                "error": "no input rows (file missing, empty, or header only)"}
    header = list(rows[0].keys())
    cols = spec.get("columns", {})
    if "rows" in spec:
        lo, hi = spec["rows"].get("min", 0), spec["rows"].get("max", math.inf)
        add("rows in [%s, %s]" % (lo, hi), lo <= len(rows) <= hi, "rows=%d" % len(rows))
    if spec.get("exact_columns"):
        extra = [c for c in header if c not in cols]
        add("no extra columns", not extra, "extra=%s" % extra if extra else "")
    for col, c in cols.items():
        present = all(col in r for r in rows)
        if c.get("required", True):
            add("%s: present" % col, present, "" if present else "missing in some/all rows")
        if not present:
            continue
        if not c.get("nullable", True):
            bad = [i + 1 for i, r in enumerate(rows) if _empty(r.get(col))]
            add("%s: not null" % col, not bad, "rows %s" % bad[:5] if bad else "")
        if "type" in c:
            def ok_type(v, t=c["type"]):
                try:
                    _typed(v, t)
                    return True
                except (TypeError, ValueError):
                    return False
            bad = _bad(rows, col, ok_type)
            add("%s: type %s" % (col, c["type"]), not bad, "rows %s" % bad[:5] if bad else "")
            if bad:
                continue
        if "min" in c or "max" in c:
            lo, hi = c.get("min", -math.inf), c.get("max", math.inf)
            bad = _bad(rows, col, lambda v: lo <= float(v) <= hi)
            add("%s: in [%s, %s]" % (col, lo, hi), not bad, "rows %s" % bad[:5] if bad else "")
        if "allowed" in c:
            allowed = {str(a) for a in c["allowed"]}
            bad = _bad(rows, col, lambda v: str(v) in allowed)
            add("%s: allowed %s" % (col, sorted(allowed)), not bad, "rows %s" % bad[:5] if bad else "")
    for key in spec.get("unique", []):
        key = [key] if isinstance(key, str) else list(key)
        seen, dup = set(), []
        for i, r in enumerate(rows):
            k = tuple(str(r.get(c)) for c in key)
            if k in seen:
                dup.append(i + 1)
            seen.add(k)
        add("unique %s" % key, not dup, "duplicate rows %s" % dup[:5] if dup else "")
    n_failed = sum(1 for x in checks if not x["ok"])
    code = 2 if not checks else (1 if n_failed else 0)
    return {"checks": checks, "n_checks": len(checks), "n_failed": n_failed, "exit_code": code}


def load_rows(path: str) -> Optional[List[Dict]]:
    """파일 → 행 목록. 없으면 None."""
    try:
        if path.endswith(".jsonl"):
            with open(path, encoding="utf-8-sig") as f:
                return [json.loads(ln) for ln in f if ln.strip()]
        if path.endswith(".json"):
            with open(path, encoding="utf-8-sig") as f:
                data = json.load(f)
            return data.get("rows") if isinstance(data, dict) else data
        with open(path, encoding="utf-8-sig", newline="") as f:
            sample = f.read(65536)
            f.seek(0)
            first = sample.splitlines()[0] if sample else ""
            delim = max(",\t;|", key=first.count) if first else ","
            return list(csv.DictReader(f, delimiter=delim if first.count(delim) else ","))
    except FileNotFoundError:
        return None


def gen_fixture(spec: Dict, n: int = 10, seed: int = 0) -> List[Dict]:
    """계약을 만족하는 합성 행(검사기 자체 시험용). unique 키 열은 행 번호로 유일하게 만든다."""
    rng = random.Random(seed)
    key_cols = {c for k in spec.get("unique", []) for c in ([k] if isinstance(k, str) else k)}
    rows = []
    for i in range(n):
        r = {}
        for col, c in spec.get("columns", {}).items():
            t, lo, hi = c.get("type", "str"), c.get("min", 0), c.get("max", 100)
            if "allowed" in c:
                v = rng.choice(list(c["allowed"]))
            elif t == "int":
                v = i + int(lo) if col in key_cols else rng.randint(int(lo), int(hi))
            elif t == "float":
                v = round(rng.uniform(lo, hi), 6)
            elif t == "bool":
                v = rng.choice([True, False])
            elif t == "datetime":
                v = "2026-10-31T%02d:%02d:00+09:00" % (10 + i // 60 % 4, i % 60)
            else:
                v = "%s_%04d" % (col, i)
            r[col] = v
        rows.append(r)
    return rows


def _print(report: Dict, out=None) -> None:
    out = out or sys.stdout
    for c in report["checks"]:
        print("%s  %s%s" % ("PASS" if c["ok"] else "FAIL", c["name"], ("  (%s)" % c["detail"]) if c["detail"] else ""),
              file=out)
    if report.get("error"):
        print("ERROR  %s" % report["error"], file=out)
    print("== %d checks, %d failed, exit %d" % (report["n_checks"], report["n_failed"], report["exit_code"]), file=out)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="output contract checker, reference only (exit 0 pass / 1 fail / 2 nothing checked)")
    ap.add_argument("output")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--json", action="store_true", help="print report as JSON")
    a = ap.parse_args(argv)
    try:
        with open(a.spec, encoding="utf-8") as f:
            spec = json.load(f)
        report = check(load_rows(a.output), spec)
    except (OSError, ValueError) as e:
        report = {"checks": [], "n_checks": 0, "n_failed": 0, "exit_code": 2, "error": "%s: %s" % (type(e).__name__, e)}
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        _print(report)
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
