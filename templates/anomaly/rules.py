"""rules — 설명 가능한 임계값·연속 n회 규칙 판정 (stdlib only).

언제 쓰나: 담당자가 기준을 말로 줄 때("온도 80 넘는 게 3번 연속이면 경보").
  consecutive_rule  값이 [lo, hi] 밖인 상태가 n회 연속되면 그 시점에 경보 1건(근거 문자열 포함).
  events_from_flags True 구간을 사건(start, end, length)으로 묶는다(max_gap 이하 끊김은 한 사건).
  evaluate_rows     행(dict) 목록에 규칙 여러 개를 적용해 행별 판정·근거를 만든다(열별 연속 카운트).
가정: 입력은 시간순. 결측(None/숫자 아님)은 연속을 끊는다(보수적). 경계값과 같으면 정상(>, < 비교).
한계: 경보 = 조사 후보이지 원인 판정이 아니다. 임계값·n·결측 처리 방식은 담당자와 합의해 DECISIONS에 적는다.
출처: 차용 없음(직접 작성). wildrage98/hackathon-kit kitlib/rules.py의 "근거 문자열 반환" 아이디어만 참고.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence


def _num(v) -> Optional[float]:
    if isinstance(v, bool):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _out_of_range(x: float, lo: Optional[float], hi: Optional[float]) -> str:
    if hi is not None and x > hi:
        return "> %g" % hi
    if lo is not None and x < lo:
        return "< %g" % lo
    return ""


def consecutive_rule(values: Sequence, lo: Optional[float] = None, hi: Optional[float] = None,
                     n: int = 1, name: str = "rule") -> List[Dict]:
    """n회 연속 범위 밖이면 경보. 반환: [{rule, alert_index, start, end, length, reason}] (구간당 1건)."""
    if lo is None and hi is None:
        raise ValueError("lo 또는 hi 중 하나는 필요")
    events: List[Dict] = []
    run_start, cur = None, None
    for i, raw in enumerate(values):
        x = _num(raw)
        why = _out_of_range(x, lo, hi) if x is not None else ""
        if why:
            if run_start is None:
                run_start = i
            if i - run_start + 1 == n:
                cur = {"rule": name, "alert_index": i, "start": run_start, "end": i, "length": n,
                       "reason": "%s: value %s for %d consecutive (first at %d)" % (name, why, n, run_start)}
                events.append(cur)
            elif cur is not None and cur["start"] == run_start:
                cur["end"], cur["length"] = i, i - run_start + 1
        else:
            run_start, cur = None, None
    return events


def events_from_flags(flags: Sequence[bool], min_len: int = 1, max_gap: int = 0) -> List[Dict]:
    """[True, True, False, True] → 사건 목록. max_gap개 이하의 False는 같은 사건으로 잇는다."""
    events: List[Dict] = []
    for i, f in enumerate(flags):
        if not f:
            continue
        if events and i - events[-1]["end"] - 1 <= max_gap:
            events[-1]["end"] = i
        else:
            events.append({"start": i, "end": i})
    out = []
    for e in events:
        e["length"] = e["end"] - e["start"] + 1
        if e["length"] >= min_len:
            out.append(e)
    return out


def evaluate_rows(rows: Sequence[Dict], rules: Sequence[Dict]) -> List[Dict]:
    """rules: [{"name","col","lo"?,"hi"?,"n"?}] → 행별 {"index","alert": bool,"reasons": [...]}.

    같은 열의 연속 카운트는 행을 따라 누적되고 범위 안/결측이면 0으로 돌아간다.
    """
    counts = {r["name"]: 0 for r in rules}
    out = []
    for i, row in enumerate(rows):
        reasons = []
        for r in rules:
            x = _num(row.get(r["col"]))
            why = _out_of_range(x, r.get("lo"), r.get("hi")) if x is not None else ""
            counts[r["name"]] = counts[r["name"]] + 1 if why else 0
            n = r.get("n", 1)
            if why and counts[r["name"]] >= n:
                reasons.append("%s: %s=%g %s (x%d, need %d)" % (r["name"], r["col"], x, why, counts[r["name"]], n))
        out.append({"index": i, "alert": bool(reasons), "reasons": reasons})
    return out
