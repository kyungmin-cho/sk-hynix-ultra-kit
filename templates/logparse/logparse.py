"""logparse — 텍스트 로그를 줄 단위로 파싱(정규식·구분자·고정폭) → 레벨/코드별 집계·시간순 이벤트 묶음 (stdlib only).

언제 쓰나: 설비 로그·알람 로그·이벤트 로그처럼 줄 단위 텍스트가 입력이고 "에러 코드별 건수", "설비별 알람 빈도",
  "에러가 몰린 구간(버스트)", "작업 세션 길이"를 근거 숫자와 함께 말해야 할 때.
  make_parser    regex(이름 그룹 ?P<ts> 등) | delimiter+fields | widths+fields → line → dict 또는 None.
  parse_lines    줄 이터러블(열린 파일 그대로) → 레코드 제너레이터. 파일 크기와 무관하게 한 줄씩 처리.
                 ParseStats에 줄 수·성공·실패·시각 파싱 실패·역순 건수·실패 샘플을 계속 쌓는다.
  count_by       레코드를 (level, code) 등으로 센다. 반환값에 항상 "parse" 통계가 같이 실린다.
  group_events   시간순 레코드를 간격(gap_s) 기준으로 묶는다(세션). min_count·pred를 주면 에러 버스트.
실행: python3 logparse.py app.log --pattern bracket --by level,code [--bursts 60:5]  (JSON 출력, 파싱 0건이면 exit 2)
참고 출력: CLI·함수 결과는 참고 구현의 출력이다. 결론은 근거(행 수·실패 수·입력 검증)로 확인하고, 결과물에는 필요한 함수만 자기 코드로 옮긴다.
가정: 시각 필드 이름은 ts. 시각은 _common.parse_ts로 해석(오프셋 없는 시각은 naive, tz를 주면 붙임).
  group_events는 시간순 입력을 가정한다. 역순 줄은 out_of_order로 세서 보고만 하고 정렬하지 않는다(정렬이 필요하면
  레코드를 먼저 sorted(..., key=lambda r: r["_ts"])로, 너무 크면 bigdata/stream_agg.py의
  external_sort(recs, key=lambda r: r["_ts"])로. _ts가 None인 레코드는 먼저 거른다).
한계: 여러 줄에 걸친 스택트레이스는 첫 줄만 매칭되고 나머지는 실패로 센다(필요하면 직전 레코드에 붙이는 전처리).
  'Oct 31 10:00:00' 같은 월 이름 시각은 parse_ts가 못 읽는다 → n_bad_ts로 드러난다. 실패율이 높으면 패턴부터 고친다.
출처: wildrage98/hackathon-kit (MIT, Copyright (c) 2026 wildrage98, commit 1728cafc4b568fdc860c34b6512a8c5921627f0b)
  kitlib/logparse.py의 "이름 있는 그룹 정규식 + 매칭 안 된 줄 반드시 보고" 구조와 bracket 패턴을 참고해 새로 씀.
  원본과 달리 스트리밍 제너레이터, 구분자·고정폭 파서, 시각 파싱 실패 집계, 세션·버스트 묶기를 더함.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Sequence

try:  # 하네스 안에서는 공용 parse_ts. 결과물로 옮길 때는 parse_ts를 같이 옮기거나 아래 폴백만 남긴다.
    from .._common import parse_ts
except ImportError:
    def parse_ts(s, tz=None, errors="none"):
        """폴백: 'YYYY-MM-DD[ T]HH:MM:SS[.,]f*[Z|±HH:MM]'만. fromisoformat의 'Z'·쉼표·소수 자릿수 함정을 피한다."""
        m = re.match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})(?:[.,](\d+))?\s*(Z|[+-]\d{2}:?\d{2})?$", str(s).strip())
        if not m:
            return None
        off = (m.group(4) or "").replace("Z", "+00:00")
        if off and ":" not in off:
            off = off[:3] + ":" + off[3:]
        try:
            dt = datetime.fromisoformat("%sT%s.%s%s" % (m.group(1), m.group(2), (m.group(3) or "0")[:6].ljust(6, "0"), off))
        except ValueError:  # 13월 같은 범위 밖 값
            return None
        if tz is not None:
            dt = dt.replace(tzinfo=tz) if dt.tzinfo is None else dt.astimezone(tz)
        return dt

PATTERNS = {
    # 2026-10-31 10:00:00,123 [ERROR] EQP01 E1234 message
    "bracket": r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+\[?(?P<level>[A-Z]+)\]?\s+"
               r"(?P<source>\S+)(?:\s+(?P<code>[A-Z]{0,3}\d{3,6})(?=\s|$))?\s*(?P<msg>.*)$",
    # 2026-10-31T10:00:00Z level=WARN eqp=EQP01 code=W200 msg="..."  → kv 파서로 따로(parse_kv)
}


def make_parser(regex: Optional[str] = None, delimiter: Optional[str] = None, widths: Optional[Sequence[int]] = None,
                fields: Optional[Sequence[str]] = None, flags: int = 0) -> Callable[[str], Optional[Dict]]:
    """셋 중 하나: regex(이름 그룹 → 필드), delimiter+fields(열 수가 다르면 실패), widths+fields(고정폭)."""
    if regex is not None:
        rx = re.compile(PATTERNS.get(regex, regex), flags)
        return lambda line: (lambda m: m.groupdict() if m else None)(rx.search(line))
    if not fields:
        raise ValueError("delimiter/widths 파서는 fields가 필요하다")
    if delimiter is not None:
        def by_delim(line: str):
            parts = [p.strip() for p in line.split(delimiter, len(fields) - 1)]
            return dict(zip(fields, parts)) if len(parts) == len(fields) else None
        return by_delim
    if widths is not None:
        def by_width(line: str):
            if len(line) < sum(widths[:-1]):
                return None
            out, pos = {}, 0
            for f, w in zip(fields, widths):
                out[f], pos = line[pos:pos + w].strip(), pos + w
            return out
        return by_width
    raise ValueError("regex, delimiter, widths 중 하나를 준다")


def parse_kv(line: str) -> Dict[str, str]:
    """'a=1 b="x y"' → {'a': '1', 'b': 'x y'}"""
    return {m.group(1): m.group(2).strip('"') for m in re.finditer(r'(\w+)=("[^"]*"|\S+)', line)}


class ParseStats(dict):
    """n_lines·n_ok·n_failed·n_bad_ts·out_of_order·mixed_tz·fail_samples. dict라 그대로 JSON·DECISIONS에 붙인다."""
    def __init__(self, keep: int = 5):
        super().__init__(n_lines=0, n_blank=0, n_ok=0, n_failed=0, n_bad_ts=0, out_of_order=0, mixed_tz=0,
                         fail_samples=[])
        self.keep = keep

    def finish(self) -> "ParseStats":
        tried = self["n_lines"] - self["n_blank"]
        self["fail_rate"] = round(self["n_failed"] / tried, 4) if tried else None
        return self


def parse_lines(lines: Iterable[str], parser: Callable[[str], Optional[Dict]], stats: Optional[ParseStats] = None,
                ts_field: str = "ts", tz=None) -> Iterator[Dict]:
    """레코드마다 _line(1부터), _ts(datetime 또는 None)를 붙여 내보낸다. 실패 줄은 stats에만 남긴다."""
    st = stats if stats is not None else ParseStats()
    last = None
    for i, raw in enumerate(lines, 1):
        st["n_lines"] += 1
        line = raw.rstrip("\r\n")
        if not line.strip():
            st["n_blank"] += 1
            continue
        rec = parser(line)
        if rec is None:
            st["n_failed"] += 1
            if len(st["fail_samples"]) < st.keep:
                st["fail_samples"].append([i, line[:200]])
            continue
        st["n_ok"] += 1
        rec["_line"] = i
        ts = rec.get(ts_field)
        rec["_ts"] = parse_ts(ts, tz=tz) if ts else None
        if ts and rec["_ts"] is None:
            st["n_bad_ts"] += 1
        elif rec["_ts"] is not None:
            try:  # naive와 aware가 섞이면 비교 불가 → tz=KST처럼 한 기준을 준다
                if last is not None and rec["_ts"] < last:
                    st["out_of_order"] += 1
                last = rec["_ts"] if last is None else max(last, rec["_ts"])
            except TypeError:
                st["mixed_tz"] += 1
        yield rec
    st.finish()


def count_by(records: Iterable[Dict], by: Sequence[str], stats: Optional[ParseStats] = None, top: Optional[int] = None) -> Dict:
    cnt = Counter(tuple(r.get(b) for b in by) for r in records)
    return {"by": list(by), "counts": [dict(zip(by, k), count=v) for k, v in cnt.most_common(top)],
            "parse": stats.finish() if stats is not None else "NOT_REPORTED"}


def group_events(records: Iterable[Dict], gap_s: float, pred: Optional[Callable[[Dict], bool]] = None,
                 min_count: int = 1, key: Optional[str] = None) -> List[Dict]:
    """gap_s 넘게 비면 새 묶음. pred로 거른 뒤(예: level == 'ERROR') min_count 이상인 묶음만 = 버스트.
    key(예: 'source')를 주면 설비별로 따로 묶는다. _ts가 None인 레코드는 건너뛴다."""
    open_: Dict = {}
    done: List[Dict] = []

    def close(g):
        if g["count"] >= min_count:
            g["duration_s"] = (g["end"] - g["start"]).total_seconds()
            done.append(g)

    for r in records:
        t = r.get("_ts")
        if t is None or (pred is not None and not pred(r)):
            continue
        k = r.get(key) if key else None
        g = open_.get(k)
        if g is not None and (t - g["end"]).total_seconds() > gap_s:
            close(g)
            g = None
        if g is None:
            g = open_[k] = {"key": k, "start": t, "end": t, "count": 0, "first_line": r["_line"]}
        g["start"], g["end"] = min(g["start"], t), max(g["end"], t)  # 조금 역순인 줄은 열린 묶음에 합친다
        g["count"], g["last_line"] = g["count"] + 1, r["_line"]
    for g in open_.values():
        close(g)
    return sorted(done, key=lambda g: (g["start"], str(g["key"])))


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="로그 파싱·집계(참고 출력, 결론은 근거로 검증). 파싱 성공 0건이면 exit 2")
    ap.add_argument("log")
    ap.add_argument("--pattern", default="bracket", help="PATTERNS 이름 또는 정규식(이름 그룹)")
    ap.add_argument("--by", default="level,code")
    ap.add_argument("--bursts", help="GAP_S:MIN_COUNT, level이 ERROR/FATAL/ALARM인 줄의 버스트")
    args = ap.parse_args(argv)
    st, by = ParseStats(), [b.strip() for b in args.by.split(",")]
    with open(args.log, encoding="utf-8", errors="replace") as f:
        recs = parse_lines(f, make_parser(regex=args.pattern), st)
        if args.bursts:  # 한 번 훑으면서 세기와 버스트 묶기를 같이 한다(레코드를 메모리에 모으지 않음)
            cnt = Counter()

            def tap(it):
                for r in it:
                    cnt[tuple(r.get(b) for b in by)] += 1
                    yield r
            gap, n = args.bursts.split(":")
            bursts = group_events(tap(recs), float(gap),
                                  lambda r: (r.get("level") or "").upper() in ("ERROR", "FATAL", "ALARM"), int(n), key="source")
            out = {"by": by, "counts": [dict(zip(by, k), count=v) for k, v in cnt.most_common()],
                   "parse": st.finish(), "bursts": bursts}
        else:
            out = count_by(recs, by, st)
    print(json.dumps(out, ensure_ascii=False, default=str, indent=1))
    print("parse: ok=%d failed=%d bad_ts=%d out_of_order=%d" % (st["n_ok"], st["n_failed"], st["n_bad_ts"], st["out_of_order"]),
          file=sys.stderr)
    return 0 if st["n_ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
