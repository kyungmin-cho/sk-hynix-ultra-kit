"""stats_detect — 설명 가능한 단변량 이상 '후보' 탐지 (stdlib only).

언제 쓰나: 정상 범위를 숫자로 받지 못했을 때 "평소와 다른 지점"을 근거(숫자)와 함께 뽑는다.
  rolling_zscore  급격한 스파이크. 직전 window개(현재값 제외)의 평균·표준편차 기준 z.
  ewma_detect     느린 드리프트. 앞 baseline_n개로 기준을 한 번 정하고 EWMA가 한계를 넘으면.
  cusum           작은 평균 이동의 누적. 양/음 누적합이 h를 넘으면(알람 후 0으로 리셋).
  iqr_bounds      정상 구간(학습 구간) 데이터로 고정 경계 (Q1-k·IQR, Q3+k·IQR)를 구한다.
  stuck           센서 고착(같은 값 n회 연속).
가정: 값은 시간순으로 정렬돼 있다. 값은 숫자 또는 숫자 문자열(CSV의 "10.5"는 to_float로 숫자로 바꾼다).
  None/NaN/''/NA/숫자 아닌 문자열은 건너뛴다(score None).
미래 정보 없음(보장 범위를 정확히): rolling_zscore·stuck은 모든 k에서 f(xs)[:k] == f(xs[:k]).
  ewma_detect·cusum은 기준(mu·sd)을 앞 baseline_n개로 정하므로 k >= baseline_n일 때만 같다
  (k < baseline_n이면 기준 자체가 달라진다). 두 함수는 기준 구간 안(i < baseline_n)에서는 flag하지 않는다
  — 기준 구간의 값이 자기 자신을 판정하는 순환을 피하려고. ewma 시작값은 mu, cusum 누적은 baseline_n부터.
한계: 신호는 '조사할 후보'이지 원인·불량 판정이 아니다. 계절성·다변량 상관은 보지 않는다.
  rolling_zscore는 기본적으로 이상값도 창에 넣으므로 큰 스파이크 직후 window 동안 sd가 커져 다음 이상을
  가릴 수 있다 → exclude_flagged=True면 flag된 값은 창에 넣지 않는다(대신 수준 이동 뒤 계속 flag될 수 있음).
  임계값(threshold·k·h)은 담당자 기준이 있으면 그것을 쓰고, DECISIONS에 근거를 적는다.
출처: wildrage98/hackathon-kit kitlib/stats_detect.py (MIT, Copyright (c) 2026 wildrage98,
  commit 1728cafc4b568fdc860c34b6512a8c5921627f0b)의 탐지기 구성·EWMA 한계식·CUSUM 리셋 방식을 참고해 다시 씀.
  바꾼 점: 결과 dict 단순화, iqr_bounds 분위수 방식 고정, prefix 불변(누수 안전) 테스트 추가,
  기준 구간 안 flag 금지·문자열 숫자 변환.
"""
from __future__ import annotations

import math
import statistics
from collections import deque
from typing import Dict, List, Optional, Sequence, Tuple

try:  # 하네스 안에서는 공용 to_float. 결과물로 옮길 때는 아래 폴백만 남긴다.
    from .._common import to_float
except ImportError:
    def to_float(v):
        if v is None or isinstance(v, bool):
            return None
        try:
            x = float(str(v).strip().replace(",", ""))
        except ValueError:
            return None
        return x if math.isfinite(x) else None


def _num(v) -> Optional[float]:
    return to_float(v)  # 숫자·numpy·Fraction·숫자 문자열 → float, 나머지 None


def _row(i, v, score=None, flag=False, reason=""):
    return {"index": i, "value": v, "score": score, "flag": flag, "reason": reason}


def rolling_zscore(values: Sequence, window: int = 30, threshold: float = 3.0, min_periods: int = 10,
                   exclude_flagged: bool = False) -> List[Dict]:
    """직전 window개(현재 제외) 기준 z-score(표본 표준편차 ddof=1, pandas rolling과 같음). |z| > threshold면 flag."""
    buf: deque = deque(maxlen=window)
    out = []
    for i, raw in enumerate(values):
        v = _num(raw)
        r = _row(i, v)
        if v is not None and len(buf) >= min_periods:
            m = statistics.fmean(buf)
            sd = statistics.stdev(buf) if len(buf) >= 2 else 0.0
            z = (v - m) / sd if sd > 0 else (0.0 if v == m else math.copysign(math.inf, v - m))
            r["score"] = z
            if abs(z) > threshold:
                r["flag"], r["reason"] = True, "z=%.2f (prev %d: mean=%.4g sd=%.4g)" % (z, len(buf), m, sd)
        if v is not None and not (exclude_flagged and r["flag"]):
            buf.append(v)
        out.append(r)
    return out


def _baseline(values: Sequence, n: int) -> Optional[Tuple[float, float]]:
    base = [x for x in (_num(v) for v in values[:n]) if x is not None]
    if len(base) < 2:
        return None
    return statistics.fmean(base), statistics.pstdev(base)


def ewma_detect(values: Sequence, alpha: float = 0.2, k: float = 3.0, baseline_n: int = 50) -> List[Dict]:
    """앞 baseline_n개로 mu·sigma 고정 → EWMA가 mu ± k·sigma·sqrt(alpha/(2-alpha)) 밖이면 flag(기준 구간 이후만)."""
    base = _baseline(values, baseline_n)
    if base is None:
        return [_row(i, _num(v), reason="baseline too short") for i, v in enumerate(values)]
    mu, sd = base
    lim = k * sd * math.sqrt(alpha / (2 - alpha))
    s, out = mu, []  # 시작값 = 기준 평균(첫 값으로 시작하면 첫 값이 튈 때 한동안 끌려간다)
    for i, raw in enumerate(values):
        v = _num(raw)
        r = _row(i, v)
        if v is not None:
            s = alpha * v + (1 - alpha) * s
            r["score"] = (s - mu) / lim if lim > 0 else None
            if lim > 0 and i >= baseline_n and abs(s - mu) > lim:
                r["flag"], r["reason"] = True, "ewma=%.4g, mu=%.4g, limit=±%.4g" % (s, mu, lim)
        out.append(r)
    return out


def cusum(values: Sequence, k_sigma: float = 0.5, h_sigma: float = 5.0, baseline_n: int = 50,
          target: Optional[float] = None) -> List[Dict]:
    """양측 CUSUM. target 기본=기준 평균, 슬랙 k=k_sigma·sigma, 결정 한계 h=h_sigma·sigma. 누적·flag는 i >= baseline_n부터."""
    base = _baseline(values, baseline_n)
    if base is None:
        return [_row(i, _num(v), reason="baseline too short") for i, v in enumerate(values)]
    mu, sd = base
    sd = sd or 1e-12
    t = mu if target is None else target
    k, h = k_sigma * sd, h_sigma * sd
    sp = sn = 0.0
    out = []
    for i, raw in enumerate(values):
        v = _num(raw)
        r = _row(i, v)
        if v is not None and i >= baseline_n:
            sp, sn = max(0.0, sp + v - t - k), max(0.0, sn + t - v - k)
            r["score"] = max(sp, sn) / h
            if sp > h or sn > h:
                r["flag"] = True
                r["reason"] = "cusum %s=%.4g > h=%.4g (target=%.4g)" % ("up" if sp > h else "down", max(sp, sn), h, t)
                sp = sn = 0.0
        out.append(r)
    return out


def iqr_bounds(train_values: Sequence, k: float = 1.5) -> Dict:
    """학습(정상) 구간으로만 경계 계산 → 다른 구간에는 lo/hi를 그대로 적용한다."""
    xs = sorted(x for x in (_num(v) for v in train_values) if x is not None)
    if len(xs) < 4:
        raise ValueError("need >= 4 numeric values")

    def q(p):
        pos = (len(xs) - 1) * p
        lo = int(pos)
        return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (pos - lo)

    q1, q3 = q(0.25), q(0.75)
    return {"lo": q1 - k * (q3 - q1), "hi": q3 + k * (q3 - q1), "q1": q1, "q3": q3, "n": len(xs)}


def stuck(values: Sequence, n: int = 10) -> List[Dict]:
    """같은 값이 n회 이상 연속이면 그 지점부터 flag. score = 현재 연속 길이."""
    out, run, last = [], 0, object()
    for i, raw in enumerate(values):
        v = _num(raw)
        run = run + 1 if (v is not None and v == last) else 1
        last = v
        flag = v is not None and run >= n
        out.append(_row(i, v, run, flag, "same value %r x%d" % (v, run) if flag else ""))
    return out


def flagged(results: List[Dict]) -> List[int]:
    """flag된 인덱스 목록."""
    return [r["index"] for r in results if r["flag"]]
