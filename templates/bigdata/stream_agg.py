"""stream_agg — 큰 CSV를 통째로 올리지 않고 프로파일·그룹 집계·샘플링·외부 정렬 (stdlib only, 메모리 일정).

언제 쓰나: 파일이 유효 메모리의 1/4 이상이거나 총량 1GB 이상(R10)이라 pandas.read_csv 한 번에 올리면 위험할 때,
  또는 pandas가 없을 때. 행은 _common.stream_csv로 한 줄씩 읽는다.
  profile          열마다 n·결측·숫자 수·비숫자 수·min/max/mean/std(Welford)·고유값 수(상한까지)·상위 값.
  group_agg        by 열 기준 value의 n·mean·min·max·std. 그룹 수가 max_groups를 넘으면 그 시점부터
                   임시 sqlite3(디스크)로 넘겨 GROUP BY 한다(engine 필드로 보고). method="sqlite"로 강제 가능.
                   std는 첫 값을 기준값 K로 뺀 이동 합(Σ(x-K), Σ(x-K)²)으로 계산해 평균이 크고 분산이 작아도 정밀하다.
                   임시 폴더(기본 /tmp)를 못 쓰면 RuntimeError → tmpdir=(CLI --tmpdir)로 쓸 수 있는 폴더를 준다.
  reservoir_sample 한 번 훑어 k행 균등 표본(Algorithm R, seed 고정 = 재현 가능). 탐색·그림·모델 시험용.
  external_sort    chunk 행씩 정렬해 임시 파일로 쓰고 heapq.merge로 합친다(시간순 정렬이 필요한 로그·센서).
  chunked          이터러블 → size개씩 list(배치 처리·executemany용).
실행: python3 stream_agg.py data.csv [--by tool,step --value thk] [--sample 1000 --out sample.csv] [--limit N]
  [--tmpdir DIR]. 출력 JSON. 0행이면 exit 2. 출력은 참고 집계다 — 결론은 근거(행 수·결측·n_bad)와 함께 검증한다.
가정: 숫자 판정은 _common.to_float(천 단위 쉼표 허용, NA/null/inf는 결측). 숫자가 아닌 값은 n_bad로 따로 센다
  (sqlite에 TEXT로 넣으면 SUM이 0으로 취급해 조용히 틀리므로 REAL만 넣는다).
한계: 분위수·중앙값은 계산하지 않는다 → 그룹별 reservoir_sample로 근사하거나 sqlite에서 ORDER BY.
  고유값 수는 max_distinct에서 멈춘다("distinct_capped": true). 순수 파이썬 루프라 수백만 행은 분 단위가 걸린다
  → --limit·표본으로 먼저 시험하고 전체 실행은 시간을 재서 결정한다. 합계는 float라 마지막 자리 오차가 있다.
출처: 차용 없음(직접 작성). HyeongiJeon/CodexHarness harness/large_data.py의 "스트리밍 프로파일 + sqlite 디스크 집계"
  아이디어만 참고(허용 목록 밖 레포라 코드 복사 없음).
"""
from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
import os
import pickle
import random
import sqlite3
import sys
import tempfile
from collections import Counter
from itertools import islice
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Sequence

try:  # 하네스 안에서는 공용 헬퍼. 결과물로 옮길 때는 아래 폴백만 남긴다.
    from .._common import stream_csv, to_float
except ImportError:
    def stream_csv(path, delimiter=None, encoding=None, limit=None):
        """폴백: 앞 64KB로 인코딩(utf-8-sig → cp949)·구분자(, \t ; |)를 고른다."""
        with open(path, "rb") as f:
            head = f.read(65536)
        if encoding is None:
            try:
                head.decode("utf-8-sig")
                encoding = "utf-8-sig"
            except UnicodeDecodeError:
                encoding = "cp949"
        if delimiter is None:
            first = head.decode(encoding, errors="replace").splitlines()[:1] or [""]
            delimiter = max(",\t;|", key=first[0].count)
        with open(path, encoding=encoding, newline="") as f:
            for i, r in enumerate(csv.DictReader(f, delimiter=delimiter)):
                if limit is not None and i >= limit:
                    return
                yield {k.strip(): v for k, v in r.items() if k is not None}

    def to_float(v):
        s = "" if v is None else str(v).strip().replace(",", "")
        try:
            x = float(s)
        except ValueError:
            return None
        return x if math.isfinite(x) else None

_MISSING = {"", "na", "n/a", "nan", "null", "none"}


def _is_missing(v) -> bool:
    return v is None or str(v).strip().lower() in _MISSING


def chunked(it: Iterable, size: int) -> Iterator[list]:
    it = iter(it)
    while True:
        block = list(islice(it, size))
        if not block:
            return
        yield block


def profile(rows: Iterable[Dict], max_distinct: int = 1000, top: int = 5) -> Dict:
    cols: Dict[str, Dict] = {}
    n_rows = 0
    for r in rows:
        n_rows += 1
        for c, v in r.items():
            s = cols.get(c)
            if s is None:
                s = cols[c] = {"n": 0, "missing": 0, "n_num": 0, "n_bad": 0, "mean": 0.0, "_m2": 0.0,
                               "min": None, "max": None, "_cnt": Counter(), "distinct_capped": False}
            s["n"] += 1
            if _is_missing(v):
                s["missing"] += 1
                continue
            x = to_float(v)
            if x is None:
                s["n_bad"] += 1
            else:
                s["n_num"] += 1
                d = x - s["mean"]
                s["mean"] += d / s["n_num"]
                s["_m2"] += d * (x - s["mean"])
                s["min"] = x if s["min"] is None else min(s["min"], x)
                s["max"] = x if s["max"] is None else max(s["max"], x)
            cnt = s["_cnt"]
            if v in cnt or len(cnt) < max_distinct:
                cnt[v] += 1
            else:
                s["distinct_capped"] = True
    for s in cols.values():
        cnt, m2 = s.pop("_cnt"), s.pop("_m2")
        s["std"] = math.sqrt(m2 / (s["n_num"] - 1)) if s["n_num"] > 1 else None
        s["mean"] = s["mean"] if s["n_num"] else None
        s["distinct"] = len(cnt)
        s["top"] = cnt.most_common(top)
    return {"n_rows": n_rows, "columns": cols}


def _finish(key, n, nv, sk, mn, mx, ssk, K=0.0) -> Dict:
    """sk = Σ(x-K), ssk = Σ(x-K)². 기준값 K를 뺀 합이라 sumsq 공식의 자릿수 손실이 없다."""
    mean = K + sk / nv if nv else None
    var = (ssk - sk * sk / nv) / (nv - 1) if nv > 1 else None
    return {"key": key, "n": n, "n_value": nv, "sum": sk + nv * K if nv else None, "mean": mean, "min": mn, "max": mx,
            "std": math.sqrt(max(var, 0.0)) if var is not None else None}


def _spill_db(tmpdir: Optional[str]):
    try:
        tmp = tempfile.TemporaryDirectory(dir=tmpdir)
        con = sqlite3.connect(os.path.join(tmp.name, "agg.sqlite3"))
        con.execute("PRAGMA journal_mode=OFF")
    except (OSError, sqlite3.Error) as e:
        raise RuntimeError("sqlite 스필 폴더를 쓸 수 없음(%s): tmpdir=(CLI --tmpdir)로 쓰기 가능한 폴더를 줄 것"
                           % (tmpdir or tempfile.gettempdir())) from e
    con.execute("PRAGMA synchronous=OFF")
    return tmp, con


def group_agg(rows: Iterable[Dict], by: Sequence[str], value: str, max_groups: int = 200_000,
              method: str = "auto", chunk: int = 50_000, tmpdir: Optional[str] = None) -> Dict:
    """반환 {"groups": [{key(tuple), n, n_value, sum, mean, min, max, std}], "meta": {engine, n_rows, n_missing, n_bad, ...}}."""
    acc: Dict[tuple, list] = {}
    K = None  # 이동 기준값 = 처음 본 숫자 값
    meta = {"engine": "memory", "n_rows": 0, "n_missing": 0, "n_bad": 0, "spilled_at_row": None}
    it = iter(rows)
    con = tmp = None
    q = ",".join("?" * (len(by) + 6))
    for r in it:
        meta["n_rows"] += 1
        k = tuple(r.get(b) for b in by)
        raw = r.get(value)
        x = None
        if _is_missing(raw):
            meta["n_missing"] += 1
        else:
            x = to_float(raw)
            meta["n_bad"] += x is None
        if x is not None:
            if K is None:
                K = x
            d = x - K
        if con is None:
            a = acc.get(k)
            if a is None:
                if method == "sqlite" or (method == "auto" and len(acc) >= max_groups):
                    tmp, con = _spill_db(tmpdir)
                    con.execute("CREATE TABLE acc(%s, n INT, nv INT, s REAL, mn REAL, mx REAL, ss REAL)"
                                % ",".join("k%d" % i for i in range(len(by))))
                    con.executemany("INSERT INTO acc VALUES(%s)" % q, (list(kk) + v for kk, v in acc.items()))
                    acc.clear()
                    meta["engine"], meta["spilled_at_row"] = "sqlite", meta["n_rows"]
                    buf = []
                else:
                    a = acc[k] = [0, 0, 0.0, None, None, 0.0]
            if a is not None:
                a[0] += 1
                if x is not None:
                    a[1] += 1
                    a[2] += d
                    a[3] = x if a[3] is None else min(a[3], x)
                    a[4] = x if a[4] is None else max(a[4], x)
                    a[5] += d * d
                continue
        buf.append(list(k) + [1, 0 if x is None else 1, None if x is None else d, x, x, None if x is None else d * d])
        if len(buf) >= chunk:
            con.executemany("INSERT INTO acc VALUES(%s)" % q, buf)
            buf = []
    if con is None:
        groups = [_finish(k, *a, K=K or 0.0) for k, a in acc.items()]
    else:
        con.executemany("INSERT INTO acc VALUES(%s)" % q, buf)
        ks = ",".join("k%d" % i for i in range(len(by)))
        cur = con.execute("SELECT %s, SUM(n), SUM(nv), TOTAL(s), MIN(mn), MAX(mx), TOTAL(ss) FROM acc GROUP BY %s" % (ks, ks))
        groups = [_finish(tuple(row[:len(by)]), *row[len(by):], K=K or 0.0) for row in cur]
        con.close()
        tmp.cleanup()
    groups.sort(key=lambda g: tuple("" if v is None else str(v) for v in g["key"]))
    meta["n_groups"] = len(groups)
    return {"groups": groups, "meta": meta}


def reservoir_sample(it: Iterable, k: int, seed: int = 0) -> List:
    rng, out = random.Random(seed), []
    for i, x in enumerate(it):
        if i < k:
            out.append(x)
        else:
            j = rng.randint(0, i)
            if j < k:
                out[j] = x
    return out


def external_sort(rows: Iterable[Dict], key: Callable[[Dict], object], chunk: int = 100_000,
                  tmpdir: Optional[str] = None) -> Iterator[Dict]:
    """메모리에는 chunk행만. 정렬 안정(같은 key는 입력 순서 유지). key 값은 서로 비교 가능해야 한다(None 섞이면 변환)."""
    def runs(path):  # 이 함수가 자기 임시 폴더에 쓴 파일만 읽는다(외부 pickle은 절대 load하지 않는다)
        with open(path, "rb") as f:
            while True:
                try:
                    yield pickle.load(f)
                except EOFError:
                    return

    with tempfile.TemporaryDirectory(dir=tmpdir) as d:
        paths = []
        for i, block in enumerate(chunked(rows, chunk)):
            block.sort(key=key)
            p = os.path.join(d, "run%05d.pkl" % i)
            with open(p, "wb") as f:  # pickle이라 datetime·None·tuple이 그대로 보존된다
                for r in block:
                    pickle.dump(r, f, protocol=pickle.HIGHEST_PROTOCOL)
            paths.append(p)
        yield from heapq.merge(*(runs(p) for p in paths), key=key)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="큰 CSV 스트리밍 프로파일·그룹 집계·표본(참고 집계, 결론은 근거로 검증). 0행이면 exit 2")
    ap.add_argument("csv")
    ap.add_argument("--by", help="그룹 열, 쉼표 구분(--value와 함께)")
    ap.add_argument("--value")
    ap.add_argument("--sample", type=int, help="k행 균등 표본을 --out에 쓴다")
    ap.add_argument("--out")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--tmpdir", help="sqlite 스필·임시 파일 폴더(기본 /tmp를 못 쓸 때)")
    args = ap.parse_args(argv)
    if not os.path.isfile(args.csv):
        print("EXIT2: 파일 없음 %s" % args.csv, file=sys.stderr)
        return 2
    rows = stream_csv(args.csv, limit=args.limit)
    if args.sample:
        res = reservoir_sample(rows, args.sample)
        if res and args.out:
            with open(args.out, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(res[0]))
                w.writeheader()
                w.writerows(res)
        out, n = {"sample_rows": len(res), "out": args.out}, len(res)
    elif args.by and args.value:
        try:
            out = group_agg(rows, [b.strip() for b in args.by.split(",")], args.value, tmpdir=args.tmpdir)
        except RuntimeError as e:
            print("EXIT2: %s" % e, file=sys.stderr)
            return 2
        n = out["meta"]["n_rows"]
    else:
        out = profile(rows)
        n = out["n_rows"]
    print(json.dumps(out, ensure_ascii=False, default=str, indent=1))
    return 0 if n else 2


if __name__ == "__main__":
    sys.exit(main())
