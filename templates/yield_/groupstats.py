"""groupstats — 요인별 불량률·카이제곱 독립성 검정·요인 순위 (stdlib only, scipy 없이).

언제 쓰나: 양품/불량 같은 이진 결과와 요인 열(설비·챔버·로트·레시피·시간대)이 있고
"어디에 불량이 몰리나"를 근거 숫자와 함께 말해야 할 때.
  defect_rate_by  요인 수준별 n·불량 수·불량률·lift(전체 대비 배수)·불량 점유율.
  contingency     수준 × (양품, 불량) 분할표.
  chi_square      r×c 분할표 카이제곱, 자유도, p값(정규화 불완전 감마로 직접 계산), Cramér's V,
                  기대도수 < 5 셀 비율 경고, 기대도수 < 1 셀이 하나라도 있으면 경고. 2×2(dof=1)는 Yates 보정 p값도
                  p_value_yates로 함께 준다(scipy chi2_contingency 기본값과 같은 보정; 0.05 근처면 둘 다 보고).
  yield_summary   tested/passed 수량 열을 그룹별 수율로 집계하기 전에 키 중복·결측·passed>tested를 오류로 센다.
  rank_factors    여러 요인을 p값·Cramér's V로 정렬. min_n 기본 5(표본 1~4건 그룹이 top_group이 되지 않게). 검정할 수 없는 요인도 p_value=None·warnings로 남긴다
                  (빠진 요인을 "무관"으로 오해하지 않도록).
가정: 한 행 = 한 검사 단위. flag는 열 이름 또는 row → True(불량)/False(양품)/None(판단 불가) 함수.
  문자열 판정은 BAD/GOOD 토큰 표를 쓰고, 표에 없는 값은 None(집계 제외, n_unknown으로 보고).
한계: 상관 ≠ 인과. 작은 그룹은 lift가 커도 불안정(min_n으로 거른다). 여러 요인을 동시에 검정하면
  우연히 유의한 요인이 나온다(요인 수만큼 유의수준을 나눠 보는 등 보수적으로 해석).
  교란(예: 특정 설비가 특정 레시피만 돌림)은 두 요인 교차 집계로 따로 확인한다.
출처: 차용 없음(직접 작성). wildrage98/hackathon-kit kitlib/groupstats.py의 lift·share_of_bad 지표 아이디어만 참고.
"""
from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

BAD = {"1", "y", "yes", "true", "fail", "ng", "bad", "defect", "reject", "불량", "실패", "부적합"}
GOOD = {"0", "n", "no", "false", "pass", "ok", "good", "양품", "정상", "적합"}
Flag = Union[str, Callable[[Dict], Optional[bool]]]


def _is_bad(flag: Flag, row: Dict) -> Optional[bool]:
    v = flag(row) if callable(flag) else row.get(flag)
    if v is None or isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v) if v in (0, 1) else None
    s = str(v).strip().lower()
    if s in BAD or s in GOOD:
        return s in BAD
    try:  # pandas가 결측 섞인 0/1 열을 "1.0"/"0.0"으로 쓰는 경우
        x = float(s)
    except ValueError:
        return None
    return bool(x) if x in (0.0, 1.0) else None


def contingency(rows: Sequence[Dict], factor: str, flag: Flag) -> Tuple[List, List[List[int]], int]:
    """(수준 목록, [[양품, 불량], ...], 판단 불가 행 수). 수준은 문자열 정렬."""
    counts: Dict = {}
    unknown = 0
    for r in rows:
        bad = _is_bad(flag, r)
        if bad is None:
            unknown += 1
            continue
        c = counts.setdefault(r.get(factor), [0, 0])
        c[int(bad)] += 1
    levels = sorted(counts, key=lambda x: str(x))
    return levels, [counts[k] for k in levels], unknown


def defect_rate_by(rows: Sequence[Dict], factor: str, flag: Flag, min_n: int = 1) -> List[Dict]:
    """불량률 내림차순(같으면 n 큰 순)."""
    levels, table, _ = contingency(rows, factor, flag)
    tot_n = sum(g + b for g, b in table)
    tot_b = sum(b for _, b in table)
    overall = tot_b / tot_n if tot_n else 0.0
    out = []
    for lv, (g, b) in zip(levels, table):
        n = g + b
        if n < min_n:
            continue
        rate = b / n
        out.append({"group": lv, "n": n, "bad": b, "rate": rate,
                    "lift": rate / overall if overall > 0 else None,
                    "share_of_bad": b / tot_b if tot_b else 0.0})
    out.sort(key=lambda d: (-d["rate"], -d["n"]))
    return out


def _gammaincc(a: float, x: float) -> float:
    """정규화 상부 불완전 감마 Q(a, x). x < a+1이면 급수, 아니면 연분수."""
    if x <= 0:
        return 1.0
    lg = math.lgamma(a)
    if x < a + 1:
        term = total = 1.0 / a
        ap = a
        for _ in range(1000):
            ap += 1
            term *= x / ap
            total += term
            if abs(term) < abs(total) * 1e-15:
                break
        return max(0.0, 1.0 - total * math.exp(-x + a * math.log(x) - lg))
    tiny = 1e-300
    b = x + 1 - a
    c, d = 1 / tiny, 1 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = tiny if abs(d) < tiny else d
        c = b + an / c
        c = tiny if abs(c) < tiny else c
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return min(1.0, math.exp(-x + a * math.log(x) - lg) * h)


def chi2_sf(x: float, dof: int) -> float:
    """카이제곱 분포 상측 확률 P(X >= x)."""
    return _gammaincc(dof / 2.0, x / 2.0)


def chi_square(table: Sequence[Sequence[float]]) -> Dict:
    """분할표 → chi2, dof, p_value, cramers_v, n, low_expected_share, warnings. 합 0인 행·열은 뺀다."""
    t = [list(map(float, r)) for r in table if sum(r) > 0]
    if not t:
        raise ValueError("empty table")
    keep = [j for j in range(len(t[0])) if sum(r[j] for r in t) > 0]
    t = [[r[j] for j in keep] for r in t]
    R, C = len(t), len(keep)
    n = sum(map(sum, t))
    rs = [sum(r) for r in t]
    cs = [sum(t[i][j] for i in range(R)) for j in range(C)]
    chi2, chi2_y, low, low1 = 0.0, 0.0, 0, 0
    for i in range(R):
        for j in range(C):
            e = rs[i] * cs[j] / n
            low += e < 5
            low1 += e < 1
            chi2 += (t[i][j] - e) ** 2 / e
            chi2_y += max(0.0, abs(t[i][j] - e) - 0.5) ** 2 / e
    dof = (R - 1) * (C - 1)
    warnings = []
    share = low / (R * C)
    if dof == 0:
        warnings.append("dof=0: 수준 또는 결과가 하나뿐이라 검정 불가")
    if share > 0.2:
        warnings.append("기대도수<5 셀 %.0f%%: p값 신뢰 낮음(수준 병합 또는 정확 검정 고려)" % (100 * share))
    if low1:
        warnings.append("기대도수<1 셀 %d개: 카이제곱 근사 부적합(수준 병합 필요)" % low1)
    return {"chi2": chi2, "dof": dof, "p_value": chi2_sf(chi2, dof) if dof > 0 else None,
            "p_value_yates": chi2_sf(chi2_y, 1) if dof == 1 else None,
            "cramers_v": math.sqrt(chi2 / (n * min(R - 1, C - 1))) if dof > 0 else None,
            "n": int(n), "low_expected_share": share, "warnings": warnings}


def rank_factors(rows: Sequence[Dict], factors: Sequence[str], flag: Flag, min_n: int = 5) -> List[Dict]:
    """요인별 검정 결과를 p값 오름차순(같으면 Cramér's V 내림차순)으로."""
    out = []
    for f in factors:
        levels, table, unknown = contingency(rows, f, flag)
        pairs = [(lv, row) for lv, row in zip(levels, table) if sum(row) >= min_n]
        try:
            res = chi_square([row for _, row in pairs])
        except ValueError:
            out.append({"factor": f, "levels": len(pairs), "n_unknown": unknown, "chi2": None, "dof": 0,
                        "p_value": None, "p_value_yates": None, "cramers_v": None, "n": 0, "low_expected_share": None,
                        "warnings": ["검정 불가: 판정 가능한 행이 없거나 모든 수준이 min_n 미만"],
                        "top_group": None, "top_rate": None})
            continue
        top = max(pairs, key=lambda p: (p[1][1] / sum(p[1]), sum(p[1])))
        out.append({"factor": f, "levels": len(pairs), "n_unknown": unknown, **res,
                    "top_group": top[0], "top_rate": top[1][1] / sum(top[1])})
    out.sort(key=lambda d: (d["p_value"] if d["p_value"] is not None else 2.0, -(d["cramers_v"] or 0)))
    return out


def _count(v) -> Optional[float]:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x == x and x >= 0 else None


def yield_summary(rows: Sequence[Dict], key: Sequence[str], tested: str, passed: str,
                  group: Optional[str] = None) -> Dict:
    """→ {"groups": [{"group","tested","passed","yield"}], "errors": {...}, "ok": bool, "note"}.

    오류 행(키 중복의 두 번째부터·수량 결측/음수/숫자 아님·passed > tested)은 집계에서 빼고 개수와 첫 5건 위치를 보고한다.
    수율은 단순 평균이 아니라 sum(passed)/sum(tested)(가중)이다.
    """
    seen, errors, agg = set(), {"duplicate_key": [], "missing": [], "passed_gt_tested": []}, {}
    for i, r in enumerate(rows):
        k = tuple(r.get(c) for c in key)
        if k in seen:
            errors["duplicate_key"].append(i)
            continue
        seen.add(k)
        t, p = _count(r.get(tested)), _count(r.get(passed))
        if t is None or p is None or any(r.get(c) in (None, "") for c in key):
            errors["missing"].append(i)
            continue
        if p > t:
            errors["passed_gt_tested"].append(i)
            continue
        a = agg.setdefault(r.get(group) if group else "ALL", [0.0, 0.0])
        a[0] += t
        a[1] += p
    groups = [{"group": g, "tested": t, "passed": p, "yield": p / t if t else None}
              for g, (t, p) in sorted(agg.items(), key=lambda kv: str(kv[0]))]
    n_err = {k: len(v) for k, v in errors.items()}
    return {"groups": groups, "errors": n_err, "error_rows": {k: v[:5] for k, v in errors.items()},
            "ok": not any(n_err.values()), "note": "낮은 수율 그룹 = 조사 후보 신호, 원인 아님"}
