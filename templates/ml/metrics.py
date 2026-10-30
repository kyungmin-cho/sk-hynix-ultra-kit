"""metrics — 분류·회귀 지표, AUC, 비용 기반 임계값 탐색 (stdlib only).

언제 쓰나: 모델·규칙의 성능을 숫자로 보고할 때(sklearn 없이도 같은 정의).
  classification_metrics  accuracy·precision·recall·F1·혼동행렬(이진, positive 라벨 지정).
  regression_metrics      MAE·RMSE·R²·MAPE(실제값 0인 행은 MAPE에서 제외하고 개수 보고).
  roc_auc                 순위 기반 AUC(동점은 평균 순위).
  cost_threshold          score >= t → 양성. 비용 = cost_fp·FP + cost_fn·FN 최소인 t를 고른다.
  permutation_importance  검증 구간에서 열 하나씩 섞어 점수가 얼마나 떨어지는지(모델 종류 무관, 원인 아님).
정직한 평가: 불균형 데이터에서 accuracy는 의미가 약하다(전부 정상이라고 해도 높음) → recall·precision과
  다수 클래스 기준선을 함께 보고한다. 임계값은 반드시 검증 구간에서 고르고, test는 마지막에 한 번만 본다.
  비용 비율(놓친 불량 1건 = 오경보 몇 건?)은 담당자에게 묻고 DECISIONS에 적는다.
가정: 분모가 0이면 해당 지표는 0.0(precision: 양성 예측 없음 등) — 결과 dict의 n 값으로 판단한다.
  라벨은 _label로 정규화한다: "1"/"1.0"/"true"/"yes"/True → 1, "0"/"false"/"no"/False → 0, 그 밖의 문자열은 공백만 제거
  (CSV에서 읽은 "1"이 positive=1과 안 맞아 recall 0이 조용히 나오는 것을 막는다). positive가 라벨에 없고
  라벨이 0/1도 아니면(예: OK/NG인데 positive=1) ValueError. 길이가 다르면 ValueError.
출처: 차용 없음(직접 작성). PKJthecreator/probe-kit의 비용 임계값 아이디어만 참고.
"""
from __future__ import annotations

import math
from bisect import bisect_left
import random
from typing import Callable, Dict, Hashable, List, Optional, Sequence


def _div(a: float, b: float) -> float:
    return a / b if b else 0.0


_TRUE, _FALSE = {"1", "1.0", "true", "yes", "y"}, {"0", "0.0", "false", "no", "n"}


def _label(v):
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)) or type(v).__module__ == "numpy":
        try:
            f = float(v)
        except (TypeError, ValueError):
            return v
        return int(f) if f in (0.0, 1.0) else v
    if isinstance(v, str):
        t = v.strip()
        return 1 if t.lower() in _TRUE else 0 if t.lower() in _FALSE else t
    return v


def _labels(y_true: Sequence, other: Sequence, positive: Hashable):
    """(정규화한 y_true, 정규화한 other, 정규화한 positive). 길이·positive 불일치는 ValueError."""
    if len(y_true) != len(other):
        raise ValueError("length mismatch: %d vs %d" % (len(y_true), len(other)))
    yt, pos = [_label(v) for v in y_true], _label(positive)
    seen = set(yt)
    if pos not in seen and not seen <= {0, 1}:
        raise ValueError("positive %r not in labels %s (positive= 인자를 라벨에 맞출 것)" % (positive, sorted(map(str, seen))[:5]))
    return yt, list(other), pos


def classification_metrics(y_true: Sequence, y_pred: Sequence, positive: Hashable = 1) -> Dict:
    y_true, y_pred, positive = _labels(y_true, y_pred, positive)
    y_pred = [_label(v) for v in y_pred]
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p == positive)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != positive and p == positive)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p != positive)
    tn = len(y_true) - tp - fp - fn
    prec, rec = _div(tp, tp + fp), _div(tp, tp + fn)
    return {"n": len(y_true), "accuracy": _div(tp + tn, len(y_true)), "precision": prec, "recall": rec,
            "f1": _div(2 * prec * rec, prec + rec), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "positive_rate_true": _div(tp + fn, len(y_true))}


def regression_metrics(y_true: Sequence[float], y_pred: Sequence[float]) -> Dict:
    if len(y_true) != len(y_pred) or not y_true:
        raise ValueError("length mismatch or empty")
    y_true, y_pred = [float(v) for v in y_true], [float(v) for v in y_pred]  # CSV 문자열도 숫자로, 결측이면 여기서 실패
    err = [p - t for t, p in zip(y_true, y_pred)]
    mean_t = math.fsum(y_true) / len(y_true)
    ss_res = math.fsum(e * e for e in err)
    ss_tot = math.fsum((t - mean_t) ** 2 for t in y_true)
    nz = [(t, p) for t, p in zip(y_true, y_pred) if t != 0]
    return {"n": len(err), "mae": math.fsum(abs(e) for e in err) / len(err), "rmse": math.sqrt(ss_res / len(err)),
            "r2": 1 - ss_res / ss_tot if ss_tot else None,
            "mape": math.fsum(abs((p - t) / t) for t, p in nz) / len(nz) if nz else None, "n_mape": len(nz)}


def roc_auc(y_true: Sequence, scores: Sequence[float], positive: Hashable = 1) -> Optional[float]:
    """양성·음성 중 하나가 없으면 None."""
    y_true, scores, positive = _labels(y_true, scores, positive)
    scores = [float(x) for x in scores]  # CSV 문자열 점수도 숫자로(사전순 정렬 방지). None이면 여기서 실패
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    pos = [r for r, t in zip(ranks, y_true) if t == positive]
    n_pos, n_neg = len(pos), len(y_true) - len(pos)
    if not n_pos or not n_neg:
        return None
    return (math.fsum(pos) - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def cost_threshold(y_true: Sequence, scores: Sequence[float], cost_fp: float = 1.0, cost_fn: float = 5.0,
                   positive: Hashable = 1, thresholds: Optional[Sequence[float]] = None) -> Dict:
    """비용 최소 임계값. 동률이면 더 높은 임계값(경보 적음). table에 후보별 fp·fn·cost. 정렬+이진 탐색 O(n log n)."""
    y_true, scores, positive = _labels(y_true, scores, positive)
    scores = [float(x) for x in scores]  # CSV 문자열 점수도 숫자로(사전순 정렬 방지). None이면 여기서 실패
    cands = sorted(set(thresholds if thresholds is not None else scores)) + [math.inf]
    pos = sorted(s for y, s in zip(y_true, scores) if y == positive)
    neg = sorted(s for y, s in zip(y_true, scores) if y != positive)
    table = []
    for t in cands:
        fn = bisect_left(pos, t)  # 양성인데 s < t
        fp = len(neg) - bisect_left(neg, t)  # 음성인데 s >= t
        table.append({"threshold": t, "fp": fp, "fn": fn, "cost": cost_fp * fp + cost_fn * fn})
    best = min(table, key=lambda r: (r["cost"], -r["threshold"]))
    return {"threshold": best["threshold"], "cost": best["cost"], "fp": best["fp"], "fn": best["fn"], "table": table}


def permutation_importance(predict: Callable[[List[Dict]], Sequence], rows: Sequence[Dict], y: Sequence,
                           score: Callable[[Sequence, Sequence], float], cols: Sequence[str],
                           repeats: int = 3, seed: int = 0) -> List[Dict]:
    """rows: 피처 dict 목록, score는 클수록 좋은 함수(예: lambda t, p: -MAE). → 감소량 큰 순 [{"col","drop"}].

    학습 구간이 아니라 검증 구간 rows로 계산한다. 상관된 피처는 서로 중요도를 나눠 가져 둘 다 낮게 보일 수 있다.
    """
    rng = random.Random(seed)
    base = score(y, predict(list(rows)))
    out = []
    for c in cols:
        drops = []
        for _ in range(repeats):
            vals = [r.get(c) for r in rows]
            rng.shuffle(vals)
            shuffled = [dict(r, **{c: v}) for r, v in zip(rows, vals)]
            drops.append(base - score(y, predict(shuffled)))
        out.append({"col": c, "drop": sum(drops) / len(drops)})
    return sorted(out, key=lambda d: -d["drop"])
