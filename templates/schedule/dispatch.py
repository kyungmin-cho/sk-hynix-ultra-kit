"""dispatch — 규칙 기반 디스패칭(FIFO·SPT·EDD·PRIORITY·CR)으로 작업을 설비에 배정하고 지표·텍스트 간트로 비교 (stdlib only).

언제 쓰나: "로트·정비·검사 작업을 설비에 배정", "처리 순서 결정", "납기 지연 최소화"처럼 운영 과제에서
  솔버 없이 설명 가능한 기준선이 필요할 때. 규칙 여러 개를 같은 입력으로 돌려 지표표로 고르고,
  "지연 최소 vs 처리량 최대 중 무엇이 목표인가"를 담당자에게 확인받는 근거로 쓴다.
  dispatch       리스트 스케줄링(규칙으로 작업 선택 → 가장 빨리 끝나는 설비) → [{job, machine, start, end, due, tardiness, rule}]
  metrics        makespan, 평균 흐름시간(end−ready), 평균 대기, 지연 건수·합·최대, 설비별 가동률
  compare_rules  규칙별 metrics 목록 + table_text로 나란히 비교
  gantt_text     설비별 ASCII 막대 간트(폭 고정, 터미널·DECISIONS에 그대로 붙인다)
  jobs_from_rows CSV dict 행 → Job (열: id, duration, ready, due, priority, eligible="M1;M2", setup)
규칙: FIFO=도착 순, SPT=처리시간 짧은 것, EDD=납기 빠른 것, PRIORITY=priority 큰 것(동률 EDD), CR=(납기−지금)/처리시간 작은 것.
  동률은 항상 job id로 깬다(결정적).
참고 출력: CLI·함수 결과는 참고 구현의 출력이다. 결론은 근거(행 수·실패 수·입력 검증)로 확인하고, 결과물에는 필요한 함수만 자기 코드로 옮긴다.
가정: 작업은 한 번에 한 설비에서 끊김 없이 처리. 설비는 한 번에 한 작업. 시간 단위는 자유(분 권장).
  처리시간 = duration / speed + setup. down=[(start, end)] 구간에는 작업이 걸치지 않게 시작을 미룬다.
한계: 규칙 기반은 최적해가 아니다(작은 문제에서도 최적보다 나쁠 수 있음). 작업 간 선후 관계·다단계 공정·
  순서 의존 셋업은 없다 → 필요하면 dispatch 루프의 ready 조건에 선행 작업 완료를 더한다. ortools 같은 솔버는 docs/EXCLUDED.md.
출처: wildrage98/hackathon-kit (MIT, Copyright (c) 2026 wildrage98, commit 1728cafc4b568fdc860c34b6512a8c5921627f0b)
  kitlib/schedule.py의 Job/Machine 데이터클래스, 규칙 표, 다운타임 회피(_earliest_start) 구조를 참고해 새로 씀.
  원본과 달리 흐름시간을 end−ready로 바로잡고, 설비 선택을 "가장 빨리 끝나는 설비"로 바꾸고, ASCII 간트를 더함.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

RULES = ("FIFO", "SPT", "EDD", "PRIORITY", "CR")
INF = float("inf")


@dataclass
class Job:
    id: str
    duration: float
    ready: float = 0.0
    due: Optional[float] = None
    priority: float = 0.0
    eligible: Optional[Sequence[str]] = None  # 처리 가능한 설비 id(None = 전부)
    setup: float = 0.0


@dataclass
class Machine:
    id: str
    available_at: float = 0.0
    speed: float = 1.0
    down: List[Tuple[float, float]] = field(default_factory=list)


def _key(rule: str, now: float):
    def k(j: Job):
        due = INF if j.due is None else j.due
        if rule == "FIFO":
            return (j.ready, j.id)
        if rule == "SPT":
            return (j.duration, j.id)
        if rule == "EDD":
            return (due, j.id)
        if rule == "PRIORITY":
            return (-j.priority, due, j.id)
        if rule == "CR":
            return ((due - now) / j.duration if j.duration > 0 else INF, j.id)
        raise ValueError("unknown rule %r (RULES=%s)" % (rule, RULES))
    return k


def _start_after_down(m: Machine, t: float, dur: float) -> float:
    start, moved = t, True
    while moved:
        moved = False
        for s, e in m.down:
            if start < e and start + dur > s:
                start, moved = e, True
    return start


def dispatch(jobs: Sequence[Job], machines: Sequence[Machine], rule: str = "EDD") -> List[Dict]:
    """결정 시각 '지금' = 어떤 설비가 비어 있고 할 일이 도착한 가장 이른 시각. 그때 도착한 작업 중 규칙 1순위를 고르고,
    할 수 있는 설비 중 가장 빨리 끝나는 곳(속도·다운타임 반영, 동률은 설비 id)에 배정한다."""
    _key(rule, 0.0)(Job("_", 1.0))  # 규칙 이름 검사
    ms = {m.id: Machine(m.id, m.available_at, m.speed, sorted(m.down)) for m in machines}
    pending = sorted(jobs, key=lambda j: j.id)
    for j in pending:
        if j.eligible is not None and not set(j.eligible) & set(ms):
            raise ValueError("job %s: eligible 설비 %s가 없다" % (j.id, list(j.eligible)))
    can = lambda m, j: j.eligible is None or m.id in j.eligible
    out: List[Dict] = []
    while pending:
        now = min(max(m.available_at, min(j.ready for j in pending if can(m, j)))
                  for m in ms.values() if any(can(m, j) for j in pending))
        ready = [j for j in pending if j.ready <= now and any(can(m, j) and m.available_at <= now for m in ms.values())]
        j = min(ready, key=_key(rule, now))
        best = None
        for m in sorted(ms.values(), key=lambda x: x.id):
            if can(m, j):
                dur = j.duration / m.speed + j.setup
                st = _start_after_down(m, max(m.available_at, j.ready), dur)
                if best is None or st + dur < best[1]:
                    best = (st, st + dur, m)
        start, end, m = best
        out.append({"job": j.id, "machine": m.id, "start": start, "end": end, "ready": j.ready, "due": j.due,
                    "tardiness": max(0.0, end - j.due) if j.due is not None else 0.0, "rule": rule})
        m.available_at = end
        pending.remove(j)
    return sorted(out, key=lambda d: (d["start"], d["machine"]))


def metrics(sched: List[Dict]) -> Dict:
    if not sched:
        return {"n_jobs": 0}
    t0 = min(min(d["ready"] for d in sched), min(d["start"] for d in sched))
    makespan = max(d["end"] for d in sched) - t0
    busy: Dict[str, float] = {}
    for d in sched:
        busy[d["machine"]] = busy.get(d["machine"], 0.0) + d["end"] - d["start"]
    n = len(sched)
    r = lambda x: round(x, 3)
    return {"rule": sched[0]["rule"], "n_jobs": n, "makespan": r(makespan),
            "mean_flow": r(sum(d["end"] - d["ready"] for d in sched) / n),
            "mean_wait": r(sum(d["start"] - d["ready"] for d in sched) / n),
            "n_late": sum(1 for d in sched if d["tardiness"] > 0),
            "total_tardiness": r(sum(d["tardiness"] for d in sched)),
            "max_tardiness": r(max(d["tardiness"] for d in sched)),
            "utilization": {k: r(v / makespan) if makespan else 0.0 for k, v in sorted(busy.items())}}


def compare_rules(jobs: Sequence[Job], machines: Sequence[Machine], rules: Sequence[str] = RULES) -> List[Dict]:
    return [metrics(dispatch(jobs, machines, rule)) for rule in rules]


def table_text(rows: List[Dict], cols=("rule", "makespan", "mean_flow", "mean_wait", "n_late", "total_tardiness", "max_tardiness")) -> str:
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows]
    return "\n".join(lines)


def gantt_text(sched: List[Dict], width: int = 60) -> str:
    """설비 한 줄씩. 작업 구간은 job id 마지막 글자, 빈 시간은 '.', 지연 작업은 목록에 '!'."""
    if not sched:
        return "(빈 일정)"
    t0, t1 = min(d["start"] for d in sched), max(d["end"] for d in sched)
    scale = width / (t1 - t0) if t1 > t0 else 1.0
    lines = ["t=%g..%g, 한 칸=%.3g" % (t0, t1, 1 / scale)]
    for mid in sorted({d["machine"] for d in sched}):
        bar = ["."] * width
        mine = sorted((d for d in sched if d["machine"] == mid), key=lambda d: d["start"])
        for d in mine:
            a, b = int((d["start"] - t0) * scale), max(int((d["start"] - t0) * scale) + 1, int(round((d["end"] - t0) * scale)))
            for i in range(a, min(b, width)):
                bar[i] = str(d["job"])[-1]
        jobs = " ".join("%s%s" % (d["job"], "!" if d["tardiness"] > 0 else "") for d in mine)
        lines.append("%-6s|%s| %s" % (mid, "".join(bar), jobs))
    return "\n".join(lines)


def jobs_from_rows(rows) -> List[Job]:
    f = lambda v, default=None: default if v in (None, "") else float(v)
    out = []
    for r in rows:
        el = r.get("eligible")
        out.append(Job(str(r["id"]), float(r["duration"]), f(r.get("ready"), 0.0), f(r.get("due")),
                       f(r.get("priority"), 0.0), [e.strip() for e in el.split(";") if e.strip()] if el else None,
                       f(r.get("setup"), 0.0)))
    return out
