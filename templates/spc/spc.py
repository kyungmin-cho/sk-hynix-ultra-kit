"""spc — 고정 기준선 I-MR 관리도·Western Electric 규칙·Xbar-R·Cp/Cpk (stdlib only).

언제 쓰나: 과제나 담당자가 "관리도", "관리 한계", "UCL/LCL", "Cpk", "WE 룰"을 말할 때.
  imr_fit / imr_apply  기준 구간으로 한계를 한 번 추정해 고정(freeze) → 이후 구간에 적용.
                       평가 구간을 한계 추정에 섞으면 이상점이 한계를 넓혀 스스로를 숨긴다(순환 판정).
  western_electric     규칙 1~4: 1) 3σ 밖 1점 2) 같은 쪽 2σ 밖 3점 중 2점 3) 같은 쪽 1σ 밖 5점 중 4점
                       4) 중심선 한쪽 8점 연속. 위반은 '완성된 지점'의 인덱스로 보고한다.
                       규칙 2·3은 현재 점도 같은 쪽 한계 밖일 때만 위반(창 안 다른 점만 밖이면 아님).
                       한 번의 긴 런은 런이 이어지는 동안 매 점 위반으로 잡힌다(첫 인덱스만 셀지 DECISIONS에).
  xbar_r_fit           부분군 크기 2~10, 크기가 모두 같을 때의 Xbar/R 한계(A2·D3·D4 상수).
  cp_cpk               규격(LSL/USL) 대비 공정능력. sigma 없음 = 표본 표준편차(전체 변동, 엄밀히는 Pp/Ppk),
                       sigma="imr" = MRbar/1.128(군내 변동, Cp/Cpk), 숫자 = 그 값. LSL > USL이면 ValueError.
가정: 한 설비·제품·레시피·측정 항목의 단일 시계열, 시간순 정렬. I-MR sigma = MRbar/1.128.
한계: 신호는 조사 후보이지 불량·원인 판정이 아니다. 기준 구간 20점 미만이면 탐색용(warnings).
  관리 한계(공정의 목소리)와 규격 한계(고객 요구)는 다르다. Cpk 기준(1.33 등)은 업계 관행이며 담당자 기준 우선.
출처: ripplelover/cofa-ready-kit cofa_kit/semiconductor.py (MIT, Copyright (c) 2026 Cofa Ready Kit
  contributors, commit 1bf4ba4f681f58cb2976189af63a805cf538fa67)의 "기준선 고정 I-MR" 개념과 경고 문구,
  wildrage98/hackathon-kit kitlib/spc.py (MIT, Copyright (c) 2026 wildrage98,
  commit 1728cafc4b568fdc860c34b6512a8c5921627f0b)의 WE 규칙 판정 방식·Xbar-R 상수표를 참고해 다시 씀.
  바꾼 점: fit/apply 분리, 위반 결과를 {index, rule, name} 목록과 규칙별 묶음으로 반환.
"""
from __future__ import annotations

import math
import statistics
from typing import Dict, List, Optional, Sequence

# n: (A2, D3, D4)
XBAR_R_CONST = {2: (1.880, 0.0, 3.267), 3: (1.023, 0.0, 2.574), 4: (0.729, 0.0, 2.282), 5: (0.577, 0.0, 2.114),
                6: (0.483, 0.0, 2.004), 7: (0.419, 0.076, 1.924), 8: (0.373, 0.136, 1.864),
                9: (0.337, 0.184, 1.816), 10: (0.308, 0.223, 1.777)}
WE_NAMES = {1: "WE1_beyond_3sigma", 2: "WE2_2of3_beyond_2sigma", 3: "WE3_4of5_beyond_1sigma", 4: "WE4_8_same_side"}


def _nums(values: Sequence) -> List[float]:
    out = []
    for v in values:
        try:  # 결측을 조용히 빼면 이동범위가 왜곡된다 → 숫자가 아니면 여기서 실패시킨다
            x = float(v)
        except (TypeError, ValueError):
            raise ValueError("non-numeric value %r (결측 처리 방식을 먼저 정할 것)" % (v,)) from None
        if not math.isfinite(x):
            raise ValueError("non-finite value %r" % v)
        out.append(x)
    return out


def imr_fit(baseline: Sequence) -> Dict:
    """기준 구간 → 고정 한계. center ± 3·sigma (= ±2.66·MRbar), MR UCL = 3.267·MRbar."""
    xs = _nums(baseline)
    if len(xs) < 3:
        raise ValueError("need >= 3 baseline values")
    mr_bar = statistics.fmean(abs(b - a) for a, b in zip(xs, xs[1:]))
    center, sigma = statistics.fmean(xs), mr_bar / 1.128
    warnings = []
    if len(xs) < 20:
        warnings.append("baseline < 20 points: exploratory only")
    if mr_bar == 0:
        warnings.append("baseline moving range is 0: limits are degenerate, signals are not meaningful")
    return {"center": center, "sigma": sigma, "mr_bar": mr_bar, "ucl": center + 3 * sigma, "lcl": center - 3 * sigma,
            "mr_ucl": 3.267 * mr_bar, "n": len(xs), "last": xs[-1], "warnings": warnings}


def imr_apply(values: Sequence, limits: Dict, start_index: int = 0, chain: bool = True) -> Dict:
    """고정 한계를 새 구간에 적용. chain=True면 첫 MR을 기준 구간 마지막 값과 비교한다."""
    xs = _nums(values)
    prev = limits.get("last") if chain else None
    points, violations = [], []
    for k, x in enumerate(xs):
        i = start_index + k
        mr = abs(x - prev) if prev is not None else None
        i_sig = x > limits["ucl"] or x < limits["lcl"]
        mr_sig = mr is not None and mr > limits["mr_ucl"]
        points.append({"index": i, "value": x, "mr": mr, "i_signal": i_sig, "mr_signal": mr_sig})
        if i_sig:
            violations.append({"index": i, "rule": "I", "name": "I_beyond_limits"})
        if mr_sig:
            violations.append({"index": i, "rule": "MR", "name": "MR_beyond_ucl"})
        prev = x
    return {"points": points, "violations": violations, "limits": limits}


def western_electric(values: Sequence, center: float, sigma: float, rules: Sequence[int] = (1, 2, 3, 4)) -> Dict:
    """WE 규칙 위반 목록. 반환 {"violations": [{index, rule, name}], "by_rule": {name: [index]}, "n": 점 수}."""
    if sigma <= 0:
        raise ValueError("sigma must be > 0")
    z = [(x - center) / sigma for x in _nums(values)]
    viol: List[Dict] = []

    def side_count(win, lim):  # 현재 점(win[-1])이 lim 밖인 쪽에서만 센다
        side = 1 if win[-1] > lim else -1 if win[-1] < -lim else 0
        return sum(1 for a in win if side * a > lim) if side else 0

    for i in range(len(z)):
        hit = []
        if 1 in rules and abs(z[i]) > 3:
            hit.append(1)
        if 2 in rules and i >= 2 and side_count(z[i - 2:i + 1], 2) >= 2:
            hit.append(2)
        if 3 in rules and i >= 4 and side_count(z[i - 4:i + 1], 1) >= 4:
            hit.append(3)
        if 4 in rules and i >= 7 and (all(a > 0 for a in z[i - 7:i + 1]) or all(a < 0 for a in z[i - 7:i + 1])):
            hit.append(4)
        viol.extend({"index": i, "rule": r, "name": WE_NAMES[r]} for r in hit)
    by_rule: Dict[str, List[int]] = {WE_NAMES[r]: [] for r in rules}
    for v in viol:
        by_rule[v["name"]].append(v["index"])
    return {"violations": viol, "by_rule": by_rule, "n": len(z)}


def xbar_r_fit(subgroups: Sequence[Sequence]) -> Dict:
    """부분군 목록 → Xbar/R 중심선·한계."""
    groups = [_nums(g) for g in subgroups]
    if not groups:
        raise ValueError("no subgroups")
    n = len(groups[0])
    if n not in XBAR_R_CONST or any(len(g) != n for g in groups):
        raise ValueError("subgroup sizes must be equal and in 2..10")
    a2, d3, d4 = XBAR_R_CONST[n]
    xbars = [statistics.fmean(g) for g in groups]
    xbb = statistics.fmean(xbars)
    rbar = statistics.fmean(max(g) - min(g) for g in groups)
    return {"n": n, "k": len(groups), "xbar_center": xbb, "x_ucl": xbb + a2 * rbar, "x_lcl": xbb - a2 * rbar,
            "r_center": rbar, "r_ucl": d4 * rbar, "r_lcl": d3 * rbar, "xbars": xbars}


def cp_cpk(values: Sequence, lsl: Optional[float] = None, usl: Optional[float] = None,
           sigma=None) -> Dict:
    """Cp=(USL-LSL)/6σ, Cpk=min(USL-μ, μ-LSL)/3σ. 한쪽 규격만 있으면 Cp는 None. sigma: None|"imr"|숫자."""
    xs = _nums(values)
    if len(xs) < 2:
        raise ValueError("need >= 2 values")
    if lsl is not None and usl is not None and lsl > usl:
        raise ValueError("lsl %r > usl %r (규격을 뒤바꿔 넣지 않았는지 확인)" % (lsl, usl))
    mu = statistics.fmean(xs)
    if sigma == "imr":
        basis, s = "imr_mrbar", statistics.fmean(abs(b - a) for a, b in zip(xs, xs[1:])) / 1.128
    elif sigma is not None:
        basis, s = "given", float(sigma)
    else:
        basis, s = "sample_stdev", statistics.stdev(xs)
    res = {"mean": mu, "sigma": s, "sigma_basis": basis, "n": len(xs), "cp": None, "cpk": None}
    if s <= 0 or (lsl is None and usl is None):
        return res
    if lsl is not None and usl is not None:
        res["cp"] = (usl - lsl) / (6 * s)
    sides = [c for c in ((usl - mu) / (3 * s) if usl is not None else None,
                         (mu - lsl) / (3 * s) if lsl is not None else None) if c is not None]
    res["cpk"] = min(sides)
    return res
