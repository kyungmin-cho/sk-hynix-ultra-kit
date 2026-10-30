"""forecast — 롤링 원점 백테스트·기준선 게이트·tracking signal (stdlib only).

언제 쓰나: "다음 n스텝을 예측하라" 과제. 한 번의 분할 점수 대신 원점을 옮겨 가며 여러 번 평가할 때.
  rolling_origin  (train 인덱스, test 인덱스) 목록. 원점을 step씩 앞으로, test는 원점 다음 horizon개.
  naive / seasonal_naive  기준선 예측(직전 값 / season 전 같은 위치 값).
  backtest        fit_predict(train_values, horizon) → 예측 목록을 원점마다 돌려 MAE를 원점별·평균·최악으로.
  baseline_gate   모델 평균 MAE가 기준선보다 min_gain 이상 좋아야 통과. 못 이기면 기준선을 제출.
  tracking_signal 누적 오차 / MAD. |값| > 4 정도면 예측이 한쪽으로 치우침(편향) 신호.
가정: series는 시간순 숫자 목록(결측은 미리 처리). 외생 피처가 있으면 피처 행을 같은 인덱스로 잘라 쓴다.
한계: 원점이 적으면(<3) 결과가 불안정하다. 지평·원점 수·기준선 종류를 DECISIONS에 적는다.
출처: 차용 없음(직접 작성). PKJthecreator/probe-kit의 "롤링 원점 백테스트 → 기준선 게이트" 아이디어만 참고.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Sequence, Tuple

Pair = Tuple[List[int], List[int]]


def rolling_origin(n: int, initial: int, horizon: int = 1, step: int = 1, expanding: bool = True) -> List[Pair]:
    """expanding=False면 train 길이를 initial로 고정(슬라이딩 창)."""
    if initial < 1 or horizon < 1 or step < 1:
        raise ValueError("initial, horizon, step must be >= 1")
    out, origin = [], initial
    while origin + horizon <= n:
        lo = 0 if expanding else origin - initial
        out.append((list(range(lo, origin)), list(range(origin, origin + horizon))))
        origin += step
    return out


def naive(train: Sequence[float], horizon: int) -> List[float]:
    return [train[-1]] * horizon


def seasonal_naive(season: int) -> Callable[[Sequence[float], int], List[float]]:
    def f(train: Sequence[float], horizon: int) -> List[float]:
        if len(train) < season:
            return naive(train, horizon)
        return [train[len(train) - season + (h % season)] for h in range(horizon)]
    return f


def backtest(series: Sequence[float], fit_predict: Callable[[Sequence[float], int], Sequence[float]],
             initial: int, horizon: int = 1, step: int = 1) -> Dict:
    folds = []
    for tr, te in rolling_origin(len(series), initial, horizon, step):
        pred = list(fit_predict([series[i] for i in tr], horizon))
        err = [abs(series[i] - p) for i, p in zip(te, pred)]
        folds.append({"origin": te[0], "mae": sum(err) / len(err)})
    if not folds:
        raise ValueError("no origin: series too short for initial+horizon")
    maes = [f["mae"] for f in folds]
    return {"folds": folds, "mae_mean": sum(maes) / len(maes), "mae_worst": max(maes), "n_origins": len(folds)}


def baseline_gate(model: Dict, baseline: Dict, min_gain: float = 0.0) -> Dict:
    """min_gain=0.05면 기준선 대비 5% 이상 MAE 감소해야 통과."""
    gain = (baseline["mae_mean"] - model["mae_mean"]) / baseline["mae_mean"] if baseline["mae_mean"] else 0.0
    return {"pass": gain > min_gain, "gain": gain, "model_mae": model["mae_mean"], "baseline_mae": baseline["mae_mean"]}


def tracking_signal(actual: Sequence[float], forecast: Sequence[float]) -> List[float]:
    """시점별 누적(실제-예측) / 지금까지의 평균 절대 오차. MAD가 0이면 0.0."""
    out, cum, abs_sum = [], 0.0, 0.0
    for k, (a, f) in enumerate(zip(actual, forecast), 1):
        e = a - f
        cum += e
        abs_sum += abs(e)
        mad = abs_sum / k
        out.append(cum / mad if mad else 0.0)
    return out
