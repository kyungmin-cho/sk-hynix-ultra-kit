"""events — 경보 생명주기·이벤트/포인트 평가·합성 정답 데이터 (stdlib only).

언제 쓰나: 이상 판정을 "경보 몇 건, 맞힌 사건 몇 건"으로 보고해야 할 때, 라벨이 없어 검증용 데이터를 만들 때.
  alert_lifecycle 행별 이상 플래그 → 경보 상태(NORMAL/PENDING/OPEN/CLEARING)와 경보 목록.
                  open_after회 연속이면 열고, clear_after회 연속 정상이면 닫는다(깜빡임 억제).
  point_prf       시점 단위 정밀도·재현율·F1.
  event_prf       사건 단위 P·R·F. 같은 그룹(설비·센서)끼리만, 구간이 tolerance 안에서 겹치면 맞힘.
  synth_series    결정적 합성 센서 값 + 이상 주입(spike·shift·stuck) + 정답 사건표.
가정: 입력은 그룹 안에서 시간순 인덱스. 사건은 {"start","end"(포함), "group"?} dict.
한계: 경보 상태는 판정 근거가 아니라 운영 표현이다. 열고 닫는 횟수·허용 오차는 담당자 기준을 DECISIONS에 적는다.
  합성 데이터 점수는 코드가 도는지 보는 용도이지 실제 성능이 아니다.
출처: 차용 없음(직접 작성). wildrage98/hackathon-kit kitlib의 alerts·evalmetrics·synth 구성 아이디어만 참고.
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional, Sequence, Tuple


def alert_lifecycle(flags: Sequence[bool], open_after: int = 1, clear_after: int = 1) -> Tuple[List[str], List[Dict]]:
    """→ (행별 상태, 경보 목록 [{"start","opened","end","closed"}]). 끝까지 안 닫히면 closed=None."""
    states, alerts = [], []
    state, run_bad, run_ok, start, cur = "NORMAL", 0, 0, None, None
    for i, f in enumerate(flags):
        run_bad, run_ok = (run_bad + 1, 0) if f else (0, run_ok + 1)
        if state in ("NORMAL", "PENDING"):
            if f and run_bad == 1:
                start = i
            if run_bad >= open_after:
                state, cur = "OPEN", {"start": start, "opened": i, "end": i, "closed": None}
                alerts.append(cur)
            else:
                state = "PENDING" if f else "NORMAL"
        else:
            if f:
                state, cur["end"] = "OPEN", i
            elif run_ok >= clear_after:
                state, cur["closed"], cur = "NORMAL", i, None
            else:
                state = "CLEARING"
        states.append(state)
    return states, alerts


def _div(a: float, b: float) -> float:
    return a / b if b else 0.0


def _prf(tp: int, fp: int, fn: int) -> Dict:
    p, r = _div(tp, tp + fp), _div(tp, tp + fn)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": _div(2 * p * r, p + r)}


def point_prf(pred: Sequence[bool], truth: Sequence[bool]) -> Dict:
    if len(pred) != len(truth):
        raise ValueError("length mismatch: %d vs %d" % (len(pred), len(truth)))
    tp = sum(1 for a, b in zip(pred, truth) if a and b)
    return _prf(tp, sum(1 for a in pred if a) - tp, sum(1 for b in truth if b) - tp)


def _hit(a: Dict, b: Dict, tol: int) -> bool:
    return a.get("group") == b.get("group") and a["start"] <= b["end"] + tol and b["start"] <= a["end"] + tol


def event_prf(pred: Sequence[Dict], truth: Sequence[Dict], tolerance: int = 0) -> Dict:
    """정밀도 = 실제 사건과 겹친 예측 비율, 재현율 = 예측에 잡힌 실제 사건 비율(그룹이 같아야 겹침)."""
    hit_pred = sum(1 for p in pred if any(_hit(p, t, tolerance) for t in truth))
    hit_true = sum(1 for t in truth if any(_hit(p, t, tolerance) for p in pred))
    out = _prf(hit_true, len(pred) - hit_pred, len(truth) - hit_true)
    out["precision"] = _div(hit_pred, len(pred))
    p, r = out["precision"], out["recall"]
    out["f1"] = _div(2 * p * r, p + r)
    return out


def synth_series(n: int = 200, seed: int = 0, base: float = 50.0, noise: float = 1.0,
                 inject: Optional[Sequence[Tuple[str, int, int]]] = None, group: str = "EQ1") -> Tuple[List[float], List[Dict]]:
    """inject: [(kind, start, length)], kind = spike(+8σ) | shift(+4σ 지속) | stuck(값 고정). → (값, 정답 사건)."""
    rng = random.Random(seed)
    xs = [base + rng.gauss(0, noise) for _ in range(n)]
    if inject is None:
        inject = [("spike", n // 4, 1), ("shift", n // 2, n // 10), ("stuck", 3 * n // 4, n // 20)]
    truth = []
    for kind, s, ln in inject:
        e = min(n, s + ln)
        for i in range(s, e):
            if kind == "spike":
                xs[i] += 8 * noise
            elif kind == "shift":
                xs[i] += 4 * noise
            elif kind == "stuck":
                xs[i] = xs[s]
            else:
                raise ValueError("unknown kind: %s" % kind)
        truth.append({"group": group, "start": s, "end": e - 1, "kind": kind})
    return xs, truth
