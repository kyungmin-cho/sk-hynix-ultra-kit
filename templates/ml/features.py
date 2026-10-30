"""features — 누수 없는 lag·rolling 피처 (shift-then-roll). stdlib 경로 + pandas 경로(같은 결과).

언제 쓰나: 시계열·설비별 측정에서 "직전 값들"로 피처를 만들 때.
  shift_then_roll  out[i] = func(values[i-window : i]) — 현재 값 i는 절대 포함하지 않는다.
  add_lag_roll     행(dict) 목록: 엔터티별로 시간 정렬 → lag k·rolling(w) 피처 추가(원래 행 순서 유지).
  pandas_lag_roll  DataFrame 버전. groupby(entity)[col].transform(lambda s: s.shift(1).rolling(w)...).
함정: df.groupby(k)[v].shift(1).rolling(w)처럼 groupby 밖에서 rolling하면 그룹 경계를 넘어
  다른 설비 값이 섞인다. 정렬 전에 shift하면 '직전'이 시간상 직전이 아니다.
  현재 값을 포함한 rolling(shift 없음)은 타깃 누수다.
가정: 값은 숫자 또는 숫자 문자열(CSV·DictReader는 전부 문자열을 준다 → to_float로 변환, '1,234' 허용).
  결측(None/NaN/''/NA)은 창 안에서 제외하고 개수만 min_periods와 비교(pandas와 같은 규칙).
  시각 열이 문자열이면 parse_ts로 파싱한 뒤 정렬한다('2026-1-9' < '2026-1-10'을 사전순으로 뒤집지 않도록).
  파싱할 수 없는 시각이 하나라도 있으면 ValueError(조용히 사전순 정렬하면 미래 값이 lag에 들어간다).
  std는 표본 표준편차(ddof=1), 관측 2개 미만이면 None.
한계: 시간 간격이 불규칙해도 '행 개수' 창이다(시간 창이 필요하면 따로 만든다).
출처: 차용 없음(직접 작성). PKJthecreator/probe-kit의 "대상별 시간정렬 후 shift" 아이디어만 참고.
"""
from __future__ import annotations

import math
import statistics
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Sequence

try:  # 하네스 안에서는 공용 헬퍼. 결과물로 옮길 때는 두 함수를 같이 옮기거나 아래 폴백만 남긴다.
    from .._common import parse_ts, to_float
except ImportError:
    def to_float(v):
        if v is None or isinstance(v, bool):
            return None
        try:
            x = float(str(v).strip().replace(",", ""))
        except ValueError:
            return None
        return x if math.isfinite(x) else None

    def parse_ts(s, tz=None, errors="none"):
        """폴백: datetime 또는 'YYYY-MM-DD[ T]HH:MM[:SS]'(오프셋 없음)만."""
        if isinstance(s, datetime):
            return s
        try:
            return datetime.fromisoformat(str(s).strip().replace("/", "-"))
        except ValueError:
            if errors == "raise":
                raise
            return None


def _time_key(v):
    """정렬 키. 숫자(epoch·순번)는 그대로, 그 밖에는 parse_ts로 datetime. 실패하면 ValueError."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v
    if isinstance(v, datetime):
        return v
    t = parse_ts(v)
    if t is None:
        raise ValueError("unparseable time %r (형식을 먼저 정규화할 것)" % (v,))
    return t


def _agg(xs: List[float], func: str) -> Optional[float]:
    if func == "mean":
        return statistics.fmean(xs)
    if func == "std":
        return statistics.stdev(xs) if len(xs) >= 2 else None
    if func in ("min", "max", "sum"):
        return {"min": min, "max": max, "sum": math.fsum}[func](xs)
    raise ValueError("func must be mean|std|min|max|sum")


def shift_then_roll(values: Sequence, window: int, func: str = "mean", min_periods: int = 1) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    for i in range(len(values)):
        xs = [x for x in (to_float(v) for v in values[max(0, i - window):i]) if x is not None]
        out.append(_agg(xs, func) if len(xs) >= min_periods and xs else None)
    return out


def _lag(values: Sequence, k: int) -> List[Optional[float]]:
    return [(to_float(values[i - k]) if i >= k else None) for i in range(len(values))]


def add_lag_roll(rows: Sequence[Dict], entity: Optional[str], time: str, value: str,
                 lags: Sequence[int] = (1,), windows: Sequence[int] = (3,),
                 funcs: Sequence[str] = ("mean",), min_periods: int = 1) -> List[Dict]:
    """새 dict 목록(입력 불변). 피처 이름: {value}_lag{k}, {value}_roll{w}_{func}."""
    out = [dict(r) for r in rows]
    groups: Dict = defaultdict(list)
    for i, r in enumerate(rows):
        groups[r.get(entity) if entity else None].append(i)
    keys = [_time_key(r[time]) for r in rows]  # 문자열 시각은 파싱 후 비교(사전순 정렬 = 누수)
    for idx in groups.values():
        idx.sort(key=lambda i: keys[i])  # 안정 정렬: 같은 시각은 원래 순서
        vals = [rows[i].get(value) for i in idx]
        feats = {}
        for k in lags:
            feats["%s_lag%d" % (value, k)] = _lag(vals, k)
        for w in windows:
            for fn in funcs:
                feats["%s_roll%d_%s" % (value, w, fn)] = shift_then_roll(vals, w, fn, min_periods)
        for name, col in feats.items():
            for pos, i in enumerate(idx):
                out[i][name] = col[pos]
    return out


def pandas_lag_roll(df, entity: Optional[str], time: str, value: str, lags: Sequence[int] = (1,),
                    windows: Sequence[int] = (3,), funcs: Sequence[str] = ("mean",), min_periods: int = 1):
    """pandas DataFrame 사본에 같은 이름의 피처를 붙여 돌려준다(원래 행 순서·인덱스 유지)."""
    keys = [entity, time] if entity else [time]
    # 문자열 시각 열은 사전순이 아니라 파싱한 시각으로 정렬(stdlib 경로와 같은 규칙, pandas>=1.1)
    d = df.sort_values(keys, kind="mergesort",
                       key=lambda s: s.map(_time_key) if s.name == time and s.dtype.kind not in "biufcmM" else s)
    g = d.groupby(entity, sort=False)[value] if entity else None
    out = df.copy()
    for k in lags:
        col = g.shift(k) if g is not None else d[value].shift(k)
        out["%s_lag%d" % (value, k)] = col
    for w in windows:
        for fn in funcs:
            f = (lambda s, w=w, fn=fn: getattr(s.shift(1).rolling(w, min_periods=min_periods), fn)())
            col = g.transform(f) if g is not None else f(d[value])
            out["%s_roll%d_%s" % (value, w, fn)] = col  # 인덱스 정렬로 원래 행에 맞춰 들어간다
    return out
