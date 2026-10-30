"""baseline — 비교 기준 모델: sklearn HistGradientBoosting(있으면) / stdlib 로지스틱·선형 회귀(폴백).

언제 쓰나: 표형 데이터 분류(이진)·회귀에서 "이 정도는 나와야 한다"는 기준을 빨리 세울 때.
  dummy_model  다수 클래스(분류) / train 평균(회귀). 모든 모델은 이것보다 나아야 의미가 있다.
  fit_model    prefer="auto": sklearn 있으면 HGB, 없으면 stdlib. "stdlib"/"sklearn"으로 강제 가능.
               반환 객체: .kind, .predict(X), .predict_proba(X)(분류: 양성 확률 목록), .classes.
가정: X는 숫자 목록의 목록(행 × 열), 결측은 None 또는 NaN. 분류는 라벨 2종류(classes[1] = 양성,
  라벨 정렬 순서 기준). stdlib 경로는 train 평균·표준편차로 표준화 후 결측을 0(=평균)으로 둔다.
  모든 학습은 seed·고정 반복으로 결정적이다.
정직한 평가: 이 모델을 고르기 전에 split의 누수 점검 → dummy 대비 개선 폭 → 검증 구간 임계값(metrics.cost_threshold)
  순서로 확인하고, 수치는 DECISIONS 검증 표에 적는다. HGB 기본값(min_samples_leaf=20)은 행이 적으면 상수 예측이 된다.
한계: stdlib 경로는 선형 모델이라 상호작용·비선형은 못 잡는다. 순수 파이썬 500 epoch라 느리다
  (실측: 맥 기준 1000×10 ≈ 0.7초, 5000×30 ≈ 8초 — 행·열에 비례). 그 이상은 표본을 뽑아 기준선만 잡는다.
출처: 차용 없음(직접 작성). PKJthecreator/probe-kit의 "HGB 기준선 + 선택 import" 아이디어만 참고.
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence


def _sklearn():
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
        return HistGradientBoostingClassifier, HistGradientBoostingRegressor
    except Exception:
        return None


def _f(v) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return math.nan
    return x if math.isfinite(x) else math.nan


class _Model:
    kind = "base"
    classes: Optional[list] = None

    def predict_proba(self, X) -> List[float]:
        raise NotImplementedError

    def predict(self, X) -> list:
        if self.classes is not None:
            return [self.classes[1] if p >= 0.5 else self.classes[0] for p in self.predict_proba(X)]
        return self._predict_value(X)


class _Dummy(_Model):
    kind = "dummy"

    def __init__(self, y, task):
        if task == "classification":
            self.classes = sorted(set(y), key=str)
            self.majority = max(self.classes, key=lambda c: (list(y).count(c), str(c)))
            self.rate = list(y).count(self.classes[-1]) / len(y)
        else:
            self.mean = math.fsum(y) / len(y)

    def predict(self, X):
        return [self.majority] * len(X) if self.classes is not None else [self.mean] * len(X)

    def predict_proba(self, X):
        return [self.rate] * len(X)


class _Linear(_Model):
    """표준화 + 배치 경사하강(L2). 분류=로지스틱, 회귀=선형."""

    def __init__(self, X, y, task, epochs=500, lr=0.1, l2=1e-3):
        rows = [[_f(v) for v in r] for r in X]
        d = len(rows[0])
        self.mu, self.sd = [], []
        for j in range(d):
            col = [r[j] for r in rows if not math.isnan(r[j])]
            mu = math.fsum(col) / len(col) if col else 0.0
            var = math.fsum((x - mu) ** 2 for x in col) / len(col) if col else 0.0
            self.mu.append(mu)
            self.sd.append(math.sqrt(var) or 1.0)
        Z = self._z(rows)
        if task == "classification":
            self.classes = sorted(set(y), key=str)
            if len(self.classes) != 2:
                raise ValueError("stdlib fallback supports binary classification only")
            t = [1.0 if v == self.classes[1] else 0.0 for v in y]
            self.kind = "stdlib-logistic"
        else:
            self.y_mu = math.fsum(y) / len(y)
            t = [v - self.y_mu for v in y]
            self.kind = "stdlib-linear"
        self.w, self.b, n = [0.0] * d, 0.0, len(Z)
        for _ in range(epochs):
            gw, gb = [0.0] * d, 0.0
            for z, ti in zip(Z, t):
                e = self._raw(z) - ti
                gb += e
                for j in range(d):
                    gw[j] += e * z[j]
            self.b -= lr * gb / n
            self.w = [w - lr * (g / n + l2 * w) for w, g in zip(self.w, gw)]

    def _z(self, rows):
        return [[0.0 if math.isnan(x) else (x - m) / s for x, m, s in zip(r, self.mu, self.sd)] for r in rows]

    def _lin(self, z):
        return self.b + math.fsum(w * x for w, x in zip(self.w, z))

    def _raw(self, z):
        if self.classes is None:
            return self._lin(z)
        a = max(-35.0, min(35.0, self._lin(z)))
        return 1 / (1 + math.exp(-a))

    def predict_proba(self, X):
        return [self._raw(z) for z in self._z([[_f(v) for v in r] for r in X])]

    def _predict_value(self, X):
        return [self._lin(z) + self.y_mu for z in self._z([[_f(v) for v in r] for r in X])]


class _Sk(_Model):
    def __init__(self, est, X, y, task):
        self.est = est
        self.kind = "sklearn-hgb"
        est.fit([[_f(v) for v in r] for r in X], list(y))
        if task == "classification":
            self.classes = list(est.classes_)
            if len(self.classes) != 2:
                raise ValueError("this wrapper reports binary probabilities only")

    def predict_proba(self, X):
        return [float(p[1]) for p in self.est.predict_proba([[_f(v) for v in r] for r in X])]

    def _predict_value(self, X):
        return [float(v) for v in self.est.predict([[_f(v) for v in r] for r in X])]


def dummy_model(y: Sequence, task: str = "classification") -> _Model:
    return _Dummy(y, task)


def fit_model(X: Sequence[Sequence], y: Sequence, task: str = "classification", prefer: str = "auto",
              seed: int = 0) -> _Model:
    if task not in ("classification", "regression"):
        raise ValueError("task must be classification|regression")
    if not X or len(X) != len(y):
        raise ValueError("X/y empty or length mismatch")
    sk = _sklearn() if prefer in ("auto", "sklearn") else None
    if prefer == "sklearn" and sk is None:
        raise ImportError("scikit-learn not available")
    if sk is not None:
        est = sk[0](random_state=seed) if task == "classification" else sk[1](random_state=seed)
        return _Sk(est, X, y, task)
    return _Linear(X, y, task)
