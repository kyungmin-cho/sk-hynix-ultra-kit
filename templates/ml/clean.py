"""clean — 정제 규칙을 train에서만 학습(fit)하고 모든 구간에 같은 규칙을 적용(apply) (stdlib only).

언제 쓰나: 결측 대체·이상치 자르기·범주 정리를 할 때. 전체 데이터로 중앙값·분위수를 구하면
  test 정보가 train 정제에 새어 들어간다(누수). → fit_cleaner(train) → apply_cleaner(train/test/새 데이터).
  fit_cleaner   수치열: 중앙값·clip 분위수(lo, hi), 상수열 표시. 범주열: min_count 이상 수준 목록·최빈값.
  apply_cleaner 수치 결측 → 중앙값(+ {col}_missing 0/1), 범위 밖 → clip, 범주: 결측 → "__missing__",
                학습 때 없던/드문 수준 → "__other__".
가정: 행은 dict. params는 JSON으로 저장 가능(json.dump)해서 재현·제출 근거로 남길 수 있다.
한계: 다변량 대체·시간 보간은 하지 않는다. clip은 실제 이상(불량 신호)을 지울 수 있다 → 이상탐지
  과제라면 clip을 끄고(clip=None) 원값을 보존한다. 규칙과 이유는 DECISIONS에 적는다.
출처: 차용 없음(직접 작성). NE0NMIKE/secom-yield-analysis src/clean.py의 "규칙 학습/적용 분리" 아이디어만 참고.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple


def _num(v) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _q(xs: List[float], p: float) -> float:
    pos = (len(xs) - 1) * p
    lo = int(pos)
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (pos - lo)


def fit_cleaner(train_rows: Sequence[Dict], numeric: Sequence[str] = (), categorical: Sequence[str] = (),
                clip: Optional[Tuple[float, float]] = (0.01, 0.99), min_count: int = 1) -> Dict:
    params: Dict = {"numeric": {}, "categorical": {}, "clip": list(clip) if clip else None, "n_train": len(train_rows)}
    for c in numeric:
        xs = sorted(x for x in (_num(r.get(c)) for r in train_rows) if x is not None)
        if not xs:
            params["numeric"][c] = {"median": None, "lo": None, "hi": None, "constant": True, "missing_rate": 1.0}
            continue
        params["numeric"][c] = {
            "median": _q(xs, 0.5),
            "lo": _q(xs, clip[0]) if clip else None,
            "hi": _q(xs, clip[1]) if clip else None,
            "constant": xs[0] == xs[-1],
            "missing_rate": 1 - len(xs) / max(1, len(train_rows)),
        }
    for c in categorical:
        cnt = Counter(str(r[c]) for r in train_rows if r.get(c) not in (None, ""))
        levels = sorted(k for k, n in cnt.items() if n >= min_count)
        params["categorical"][c] = {"levels": levels, "mode": cnt.most_common(1)[0][0] if cnt else None}
    return params


def apply_cleaner(rows: Sequence[Dict], params: Dict, missing_flag: bool = True) -> List[Dict]:
    """새 dict 목록. 입력은 바꾸지 않는다. 학습 때 없던 열은 그대로 둔다."""
    out = []
    for r in rows:
        o = dict(r)
        for c, p in params["numeric"].items():
            x = _num(r.get(c))
            if missing_flag:
                o[c + "_missing"] = int(x is None)
            if x is None:
                x = p["median"]
            elif p["lo"] is not None:
                x = min(max(x, p["lo"]), p["hi"])
            o[c] = x
        for c, p in params["categorical"].items():
            v = r.get(c)
            if v in (None, ""):
                o[c] = "__missing__"
            else:
                o[c] = str(v) if str(v) in p["levels"] else "__other__"
        out.append(o)
    return out
