"""split — 시간·그룹·층화 분할과 누수 점검 (stdlib only). 반환은 행 인덱스 목록.

언제 쓰나: 학습/평가를 나눌 때. 인덱스 목록을 돌려주므로 list든 DataFrame(df.iloc[idx])이든 쓸 수 있다.
  time_split        시각 기준으로 앞=train, 뒤=test. 같은 시각은 한쪽에만 들어간다(경계 겹침 없음).
  group_split       같은 그룹(설비·로트·웨이퍼)은 train/test 한쪽에만. seed 고정.
  stratified_split  라벨 비율 유지(불균형 분류). 시간·그룹 구조가 있으면 이것 대신 위 둘을 쓴다.
  check_leak / assert_no_leak  인덱스 중복·그룹 공유·시간 역전(test 시각 <= train 최대 시각)을 찾는다.
정직한 평가: 랜덤 분할은 시계열·설비 반복 측정에서 점수를 부풀린다(미래·같은 설비 정보가 train에 섞임).
  분할 방식과 그 이유를 DECISIONS에 적고, 항상 단순 기준선(다수 클래스·평균)과 비교한다.
가정: times는 숫자(epoch·순번)·datetime·시각 문자열 중 하나로 통일(datetime이면 naive/aware 혼용 금지).
  문자열은 parse_ts로 파싱해 비교한다('2026-1-9'와 '2026-1-10'을 사전순으로 비교하지 않음). 파싱 실패는 ValueError.
  분할 결과 train이나 test가 비면 ValueError(동률 시각이 많거나 그룹이 하나뿐인 경우 — cutoff·test_frac을 조정).
  group_split은 섞은 순서대로 그룹을 넣되, 넣으면 목표 행 수를 넘는 큰 그룹은 건너뛰고 다음 그룹을 본다.
한계: 시간 분할은 분포 이동(뒤 구간이 다름)을 그대로 드러낸다 — 이것은 버그가 아니라 실제 성능이다.
출처: 차용 없음(직접 작성). PKJthecreator/probe-kit의 분할 계약 아이디어만 참고(코드 복사 없음).
"""
from __future__ import annotations

import random
from collections import defaultdict
from datetime import datetime
from typing import Hashable, List, Optional, Sequence, Tuple

try:  # 하네스 안에서는 공용 parse_ts. 결과물로 옮길 때는 parse_ts를 같이 옮기거나 아래 폴백만 남긴다.
    from .._common import parse_ts
except ImportError:
    def parse_ts(s, tz=None, errors="none"):
        """폴백: 'YYYY-MM-DD[ T]HH:MM[:SS]'(오프셋 없음)만."""
        try:
            return datetime.fromisoformat(str(s).strip().replace("/", "-"))
        except ValueError:
            return None

Idx = List[int]


def _tkey(v):
    """숫자·datetime은 그대로, 문자열 등은 parse_ts. 실패하면 ValueError."""
    if isinstance(v, (int, float, datetime)) and not isinstance(v, bool):
        return v
    t = parse_ts(v)
    if t is None:
        raise ValueError("unparseable time %r" % (v,))
    return t


def _nonempty(train: Idx, test: Idx, why: str) -> Tuple[Idx, Idx]:
    if not train or not test:
        raise ValueError("empty %s (train=%d, test=%d): %s" % ("train" if not train else "test", len(train), len(test), why))
    return train, test


def time_split(times: Sequence, test_frac: float = 0.2, cutoff=None) -> Tuple[Idx, Idx]:
    """cutoff가 있으면 t < cutoff → train, t >= cutoff → test. 없으면 뒤쪽 test_frac 비율(시각 경계로 맞춤)."""
    keys = [_tkey(t) for t in times]
    order = sorted(range(len(keys)), key=lambda i: keys[i])
    if cutoff is None:
        if not order:
            raise ValueError("empty times")
        k = min(len(order) - 1, max(1, int(round(len(order) * (1 - test_frac)))))
        cutoff = keys[order[k]]
    else:
        cutoff = _tkey(cutoff)
    train = [i for i in order if keys[i] < cutoff]
    test = [i for i in order if keys[i] >= cutoff]
    return _nonempty(train, test, "cutoff %r — 같은 시각이 많으면 cutoff를 직접 지정" % (cutoff,))


def group_split(groups: Sequence[Hashable], test_frac: float = 0.2, seed: int = 0) -> Tuple[Idx, Idx]:
    """그룹 단위로 섞어 test 그룹을 고른다(행 수가 test_frac에 가까워질 때까지)."""
    members = defaultdict(list)
    for i, g in enumerate(groups):
        members[g].append(i)
    keys = sorted(members, key=str)
    random.Random(seed).shuffle(keys)
    target, test_keys, n_test = test_frac * len(groups), set(), 0
    for g in keys:
        if n_test >= target or len(test_keys) == len(keys) - 1:
            break
        if n_test + len(members[g]) > target and n_test + len(members[g]) - target > target - n_test:
            continue  # 넣으면 목표에서 더 멀어지는 큰 그룹은 건너뛴다(첫 그룹이 80%여도 test로 가지 않게)
        test_keys.add(g)
        n_test += len(members[g])
    if not test_keys and len(keys) > 1:  # 모든 그룹이 목표보다 크면 가장 작은 그룹 하나
        test_keys.add(min(keys, key=lambda g: len(members[g])))
    train = sorted(i for g in keys if g not in test_keys for i in members[g])
    test = sorted(i for g in test_keys for i in members[g])
    return _nonempty(train, test, "그룹이 %d개뿐" % len(keys))


def stratified_split(labels: Sequence[Hashable], test_frac: float = 0.2, seed: int = 0) -> Tuple[Idx, Idx]:
    """라벨별로 test_frac만큼 test로(라벨당 최소 1개는 train에 남김)."""
    rng = random.Random(seed)
    by = defaultdict(list)
    for i, y in enumerate(labels):
        by[y].append(i)
    train, test = [], []
    for y in sorted(by, key=str):
        idx = by[y][:]
        rng.shuffle(idx)
        k = min(len(idx) - 1, int(round(len(idx) * test_frac)))
        test += idx[:k]
        train += idx[k:]
    return sorted(train), sorted(test)


def check_leak(train: Idx, test: Idx, times: Optional[Sequence] = None,
               groups: Optional[Sequence[Hashable]] = None) -> List[str]:
    """누수 문제 목록(빈 목록 = 문제 없음)."""
    problems = []
    if not train or not test:
        problems.append("empty split: train=%d, test=%d rows" % (len(train), len(test)))
    both = set(train) & set(test)
    if both:
        problems.append("index in both train and test: %d rows (e.g. %s)" % (len(both), sorted(both)[:5]))
    if groups is not None:
        shared = {groups[i] for i in train} & {groups[i] for i in test}
        if shared:
            problems.append("groups in both train and test: %s" % sorted(map(str, shared))[:5])
    if times is not None and train and test:
        t_max, t_min = max(_tkey(times[i]) for i in train), min(_tkey(times[i]) for i in test)
        if t_min <= t_max:
            problems.append("time overlap: test min %r <= train max %r" % (t_min, t_max))
    return problems


def assert_no_leak(train: Idx, test: Idx, times: Optional[Sequence] = None,
                   groups: Optional[Sequence[Hashable]] = None) -> None:
    """문제가 있으면 AssertionError. 평가 스크립트 맨 앞에 둔다."""
    problems = check_leak(train, test, times, groups)
    if problems:
        raise AssertionError("; ".join(problems))
