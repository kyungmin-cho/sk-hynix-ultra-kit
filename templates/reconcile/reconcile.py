"""reconcile — 두 자료(CSV·레코드 목록)의 키 대사: 양쪽 존재/한쪽만/값 불일치/중복 키 (stdlib only).

언제 쓰나: "A 시스템과 B 시스템 자료가 맞나", "마스터 대비 누락·불일치", "전일 vs 금일 차이",
  "내 출력이 정답 예시와 같은가"를 키 기준으로 확인할 때.
  normalize_key  키 표기 정규화(앞뒤·내부 공백, 대문자, 선택: 선행 0 제거). 대사 실패 1위 원인이 키 표기 차이다.
  compare        키 대사 → {"summary", "only_in_a", "only_in_b", "mismatch", "dup_a", "dup_b"}.
                 값 비교: 양쪽이 숫자로 읽히면 숫자로(tol 절대 오차, rel_tol 상대 오차), 아니면 문자열 그대로
                 (대소문자 구분, 앞뒤 공백만 제거). 키 정규화와 값 비교는 따로 한다.
  summary_text   사람이 읽는 요약 몇 줄(DECISIONS 검증 표에 붙이기 좋게).
실행: python3 reconcile.py A.csv B.csv --key lot_id[,step] [--cols qty,status] [--tol 0.01] [--rel-tol 1e-6]
  [--exact-cols step,recipe] [--json]
  종료 코드 0 = 비교한 키가 있고 차이 없음, 1 = 한쪽만 있는 키·값 불일치·중복 키 중 하나라도 있음,
  2 = 파일 없음·읽기 실패·0행·키 열이 헤더에 없음·비교한 키 0개(= 아무것도 검사 안 함 → 실패로 취급).
참고 출력: CLI·함수 결과는 참고 구현의 출력이다. 결론은 근거(행 수·실패 수·입력 검증)로 확인하고, 결과물에는 필요한 함수만 자기 코드로 옮긴다.
가정: 결측 표기('', NA, null 등)는 양쪽 모두 결측이면 같다고 본다. 한쪽만 결측이면 불일치.
  숫자로 읽히는 값은 숫자로 비교하므로 "010"=="10", "1e3"=="1000"이 일치로 나온다 → step·recipe 같은 코드 열은
  exact_cols(--exact-cols)로 문자열 그대로 비교한다.
  중복 키는 첫 행으로 비교하고 dup 목록과 종료 코드 1로 따로 알린다.
한계: 양쪽을 메모리에 인덱싱한다 → 수백만 행이면 bigdata/stream_agg.py의 sqlite 경로로 키별 집계 후 대사.
  열 이름이 다르면 미리 바꿔서 넣는다(자동 매핑 없음). 이 결과는 "자료가 같은가"이지 어느 쪽이 옳은지가 아니다.
출처: wildrage98/hackathon-kit (MIT, Copyright (c) 2026 wildrage98, commit 1728cafc4b568fdc860c34b6512a8c5921627f0b)
  kitlib/reconcile.py의 compare/normalize_key/summary 구조를 참고해 새로 씀. 원본과 달리 문자열 숫자에도 허용 오차를
  적용하고, 값 비교에서 대문자화를 빼고, CLI 종료 코드 0/1/2를 더함.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:  # 하네스 안에서는 공용 CSV 리더. 결과물로 옮길 때는 아래 폴백만 남긴다.
    from .._common import stream_csv as _stream_csv
except ImportError:
    _stream_csv = None

_NA = {"", "na", "n/a", "nan", "null", "none"}


def normalize_key(v, upper: bool = True, strip_zeros: bool = False) -> str:
    s = " ".join(("" if v is None else str(v)).split())
    if upper:
        s = s.upper()
    if strip_zeros and s.isdigit():
        s = s.lstrip("0") or "0"
    return s


def _missing(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v)) or str(v).strip().lower() in _NA


def _num(v) -> Optional[float]:
    if isinstance(v, bool):
        return None
    try:
        x = float(str(v).strip().replace(",", "")) if not isinstance(v, (int, float)) else float(v)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def values_equal(a, b, tol: float = 0.0, rel_tol: float = 0.0, exact: bool = False) -> bool:
    if _missing(a) or _missing(b):
        return _missing(a) and _missing(b)
    x, y = (None, None) if exact else (_num(a), _num(b))
    if x is not None and y is not None:
        return abs(x - y) <= max(tol, rel_tol * max(abs(x), abs(y)))
    return str(a).strip() == str(b).strip()


def compare(rows_a: Iterable[Dict], rows_b: Iterable[Dict], keys: Sequence[str], cols: Optional[Sequence[str]] = None,
            tol=0.0, rel_tol: float = 0.0, upper: bool = True, strip_zeros: bool = False,
            exact_cols: Sequence[str] = ()) -> Dict:
    """tol은 숫자(모든 열) 또는 {열: 허용 오차}. cols=None이면 양쪽 공통 열 전부(키 제외)."""
    def index(rows) -> Tuple[Dict[Tuple, Dict], List[Tuple], int, set]:
        idx, cnt, n, seen_cols = {}, Counter(), 0, set()
        for r in rows:
            n += 1
            if n == 1:
                seen_cols = set(r)
            k = tuple(normalize_key(r.get(c), upper, strip_zeros) for c in keys)
            cnt[k] += 1
            idx.setdefault(k, r)
        return idx, [k for k, c in cnt.items() if c > 1], n, seen_cols

    ia, dup_a, n_a, cols_a = index(rows_a)
    ib, dup_b, n_b, cols_b = index(rows_b)
    if cols is None:
        cols = sorted((cols_a & cols_b) - set(keys))
    only_a = [dict(zip(keys, k)) for k in ia if k not in ib]
    only_b = [dict(zip(keys, k)) for k in ib if k not in ia]
    mismatch, matched = [], 0
    for k, ra in ia.items():
        rb = ib.get(k)
        if rb is None:
            continue
        matched += 1
        for c in cols:
            t = tol.get(c, 0.0) if isinstance(tol, dict) else tol
            if not values_equal(ra.get(c), rb.get(c), t, rel_tol, c in exact_cols):
                mismatch.append(dict(zip(keys, k), column=c, a=ra.get(c), b=rb.get(c)))
    summary = {
        "n_a": n_a, "n_b": n_b, "keys_a": len(ia), "keys_b": len(ib), "matched_keys": matched,
        "only_in_a": len(only_a), "only_in_b": len(only_b), "dup_a": len(dup_a), "dup_b": len(dup_b),
        "mismatch_keys": len({tuple(m[c] for c in keys) for m in mismatch}), "mismatch_cells": len(mismatch),
        "mismatch_by_column": dict(Counter(m["column"] for m in mismatch)), "compared_cols": list(cols),
        "key_normalization": "collapse_ws" + ("+upper" if upper else "") + ("+strip_zeros" if strip_zeros else ""),
        "tol": tol, "rel_tol": rel_tol, "exact_cols": list(exact_cols),
    }
    summary["ok"] = matched > 0 and not (only_a or only_b or mismatch or dup_a or dup_b)
    return {"summary": summary, "only_in_a": only_a, "only_in_b": only_b, "mismatch": mismatch,
            "dup_a": [dict(zip(keys, k)) for k in dup_a], "dup_b": [dict(zip(keys, k)) for k in dup_b]}


def summary_text(res: Dict, max_detail: int = 5) -> str:
    s = res["summary"]
    lines = ["대사: A %d행/%d키, B %d행/%d키, 양쪽 키 %d" % (s["n_a"], s["keys_a"], s["n_b"], s["keys_b"], s["matched_keys"]),
             "A만 %d, B만 %d, 불일치 키 %d(셀 %d), 중복 키 A %d·B %d" % (
                 s["only_in_a"], s["only_in_b"], s["mismatch_keys"], s["mismatch_cells"], s["dup_a"], s["dup_b"]),
             "비교 열 %s, 키 정규화 %s, tol=%s rel_tol=%s" % (s["compared_cols"], s["key_normalization"], s["tol"], s["rel_tol"])]
    if s["mismatch_by_column"]:
        lines.append("열별 불일치: " + ", ".join("%s=%d" % kv for kv in sorted(s["mismatch_by_column"].items(), key=lambda x: -x[1])))
    for name in ("only_in_a", "only_in_b", "mismatch"):
        for d in res[name][:max_detail]:
            lines.append("  %s: %s" % (name, d))
    return "\n".join(lines)


def _read(path: str) -> Tuple[List[Dict], List[str]]:
    if _stream_csv is not None:
        rows = list(_stream_csv(path))
    else:
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows = [{k.strip(): v for k, v in r.items() if k is not None} for r in csv.DictReader(f)]
    return rows, (list(rows[0]) if rows else [])


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="두 CSV의 키 대사(참고 출력, 결론은 근거로 검증). exit 0=일치, 1=차이, 2=입력 없음/검사 0건")
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--key", required=True, help="키 열, 쉼표 구분")
    ap.add_argument("--cols", help="비교할 열, 쉼표 구분(기본: 공통 열 전부)")
    ap.add_argument("--tol", type=float, default=0.0)
    ap.add_argument("--rel-tol", type=float, default=0.0)
    ap.add_argument("--strip-zeros", action="store_true")
    ap.add_argument("--exact-cols", default="", help="숫자 변환 없이 문자열로 비교할 열(코드 열), 쉼표 구분")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    keys = [k.strip() for k in args.key.split(",") if k.strip()]
    data = []
    for p in (args.a, args.b):
        if not os.path.isfile(p):
            print("EXIT2: 파일 없음 %s" % p, file=sys.stderr)
            return 2
        try:
            rows, header = _read(p)
        except (OSError, UnicodeDecodeError, csv.Error) as e:
            print("EXIT2: 읽기 실패 %s: %s" % (p, e), file=sys.stderr)
            return 2
        missing = [k for k in keys if k not in header]
        if not rows or missing:
            print("EXIT2: %s %s" % (p, "0행" if not rows else "키 열 없음 %s" % missing), file=sys.stderr)
            return 2
        data.append(rows)
    cols = [c.strip() for c in args.cols.split(",")] if args.cols else None
    exact = [c.strip() for c in args.exact_cols.split(",") if c.strip()]
    res = compare(data[0], data[1], keys, cols, tol=args.tol, rel_tol=args.rel_tol, strip_zeros=args.strip_zeros,
                  exact_cols=exact)
    print(json.dumps(res, ensure_ascii=False, default=str) if args.json else summary_text(res))
    if res["summary"]["matched_keys"] == 0:
        print("EXIT2: 양쪽에 같은 키가 하나도 없음(키 열·정규화 확인)", file=sys.stderr)
        return 2
    return 0 if res["summary"]["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
