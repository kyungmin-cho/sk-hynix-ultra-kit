"""_common — 시각 파싱·CSV 스트리밍·선택 import·작은 통계 헬퍼 (stdlib only, Python 3.9+).

언제 쓰나: 타임스탬프 형식이 섞였거나('Z', '+09:00', 공백 구분, epoch), CSV 구분자·인코딩을
모를 때, 큰 CSV를 통째로 올리지 않고 한 줄씩 읽고 싶을 때.
  infer_interval  시각 목록의 정렬 여부·중앙 간격·큰 공백(중앙 간격의 k배 초과)·중복 시각을 센다.
  md_table        dict 행 → 마크다운 표(RESULT·HANDOFF·리포트에 붙이기).
가정: parse_ts는 날짜·시각을 직접 정규식으로 해석한다(파이썬 버전마다 다른 fromisoformat에 기대지 않음).
  - 정수(int·numpy 정수)와 숫자 문자열: 9~13자리 = epoch(1e11 이상이면 밀리초), 8자리 = YYYYMMDD,
    14자리 = YYYYMMDDHHMMSS(pandas가 20261031을 int64로 읽어도 날짜로 해석). float는 항상 epoch 초/밀리초.
  - 오프셋 없는 시각은 naive로 돌려준다. tz를 주면 naive에는 tz를 붙이고, aware는 tz로 변환한다.
  - naive와 aware를 섞어 비교하면 TypeError가 난다 → 한 열은 tz=KST처럼 한 기준으로 통일한다.
한계: 월 이름('Oct 31')·12시간제(AM/PM)는 지원하지 않는다. 인코딩 추정은 앞부분만 보므로
  파일 중간에 다른 인코딩이 섞이면 UnicodeDecodeError가 난다 → encoding을 명시한다.
출처: 차용 없음(직접 작성).
"""
from __future__ import annotations

import codecs
import csv
import importlib
import math
import numbers
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterator, Optional, Sequence, Tuple

KST = timezone(timedelta(hours=9), "KST")

_TS = re.compile(
    r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})"
    r"(?:[T ](\d{1,2}):(\d{2})(?::(\d{2})(?:[.,](\d+))?)?)?"
    r"\s*(Z|UTC|[+-]\d{2}(?::?\d{2})?)?$",
    re.IGNORECASE,
)


def _epoch(v: float) -> datetime:
    if abs(v) >= 1e11:
        v = v / 1000.0
    return datetime.fromtimestamp(v, tz=timezone.utc)


def _parse(s) -> datetime:
    if isinstance(s, datetime):
        return s
    if isinstance(s, numbers.Integral) and not isinstance(s, bool):
        s = str(int(s))  # 정수는 자릿수 규칙(문자열과 같음)으로 해석
    elif isinstance(s, numbers.Real) and not isinstance(s, bool):
        if not math.isfinite(s):
            raise ValueError("non-finite epoch")
        return _epoch(float(s))
    if not isinstance(s, str):
        raise ValueError("unsupported type %r" % type(s).__name__)
    t = s.strip()
    if re.fullmatch(r"\d{8}", t):
        return datetime(int(t[:4]), int(t[4:6]), int(t[6:8]))
    if re.fullmatch(r"\d{14}", t):
        return datetime(*(int(t[i:j]) for i, j in ((0, 4), (4, 6), (6, 8), (8, 10), (10, 12), (12, 14))))
    if re.fullmatch(r"-?\d{9,13}(\.\d+)?", t):
        return _epoch(float(t))
    m = _TS.match(t)
    if not m:
        raise ValueError("unrecognized timestamp %r" % s)
    y, mo, d, hh, mi, ss, frac, off = m.groups()
    us = int((frac or "0")[:6].ljust(6, "0"))
    tz = None
    if off:
        o = off.upper()
        if o in ("Z", "UTC"):
            tz = timezone.utc
        else:
            sign = -1 if o[0] == "-" else 1
            digits = o[1:].replace(":", "")
            mins = int(digits[:2]) * 60 + (int(digits[2:4]) if len(digits) >= 4 else 0)
            tz = timezone(sign * timedelta(minutes=mins))
    return datetime(int(y), int(mo), int(d), int(hh or 0), int(mi or 0), int(ss or 0), us, tzinfo=tz)


def parse_ts(s, tz: Optional[timezone] = None, errors: str = "none") -> Optional[datetime]:
    """문자열/숫자 → datetime. 실패 시 errors='none'이면 None, 'raise'면 ValueError."""
    if s is None or (isinstance(s, str) and not s.strip()):
        if errors == "raise":
            raise ValueError("empty timestamp")
        return None
    try:
        dt = _parse(s)
    except (ValueError, OverflowError, OSError) as e:
        if errors == "raise":
            raise ValueError(str(e)) from None
        return None
    if tz is not None:
        dt = dt.replace(tzinfo=tz) if dt.tzinfo is None else dt.astimezone(tz)
    return dt


def sniff_csv(path: str, sniff_bytes: int = 65536) -> Tuple[str, str]:
    """(encoding, delimiter) 추정. 인코딩 utf-8-sig → cp949 → latin-1, 구분자 , \\t ; | 중 헤더에 가장 많은 것."""
    with open(path, "rb") as f:
        raw = f.read(sniff_bytes)
    encoding, text = "latin-1", raw.decode("latin-1")
    for enc in ("utf-8-sig", "cp949"):
        try:  # 잘린 멀티바이트 글자에 속지 않도록 incremental decoder 사용
            text = codecs.getincrementaldecoder(enc)().decode(raw, final=False)
            encoding = enc
            break
        except UnicodeDecodeError:
            continue
    header = next((ln for ln in text.splitlines() if ln.strip()), "")
    counts = {d: header.count(d) for d in (",", "\t", ";", "|")}
    best = max(counts, key=lambda d: counts[d])
    return encoding, (best if counts[best] > 0 else ",")


def stream_csv(path: str, delimiter: Optional[str] = None, encoding: Optional[str] = None,
               limit: Optional[int] = None) -> Iterator[Dict[str, str]]:
    """CSV를 한 행씩 dict로 내보낸다(메모리에 통째로 올리지 않음). 헤더 앞뒤 공백 제거."""
    if delimiter is None or encoding is None:
        enc, dlm = sniff_csv(path)
        encoding = encoding or enc
        delimiter = delimiter or dlm
    with open(path, encoding=encoding, newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        header = next(reader, None)
        if header is None:
            return
        header = [h.strip() for h in header]
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                return
            if not row:
                continue
            yield dict(zip(header, row))


def optional_import(name: str):
    """모듈이 있으면 모듈, 없거나 깨졌으면 None. 예: pd = optional_import('pandas')."""
    try:
        return importlib.import_module(name)
    except Exception:
        return None


_NA = {"", "na", "n/a", "nan", "null", "none", "-", "?"}


def to_float(v) -> Optional[float]:
    """숫자로 바꿀 수 없거나 결측 표기·inf면 None. '1,234.5' 같은 천 단위 쉼표는 허용."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, numbers.Real):  # int·float·numpy 숫자·Fraction·Decimal
        x = float(v)
        return x if math.isfinite(x) else None
    s = str(v).strip()
    if s.lower() in _NA:
        return None
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", s):
        s = s.replace(",", "")
    try:
        x = float(s)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def quantile(xs: Sequence[float], q: float) -> float:
    """선형 보간 분위수(numpy 기본값과 같은 방식). 빈 입력은 ValueError."""
    s = sorted(xs)
    if not s:
        raise ValueError("empty sequence")
    pos = (len(s) - 1) * q
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def infer_interval(times: Sequence, gap_factor: float = 3.0) -> Dict:
    """times: datetime 또는 숫자(초). → {"n","sorted","unsorted_at","median_sec","gaps": [(i, 초)], "duplicates"}.

    정렬은 하지 않는다(unsorted_at이 있으면 그룹별 정렬부터). 간격 통계는 정렬한 사본으로 낸다.
    """
    def sec(t):
        return t.timestamp() if isinstance(t, datetime) else float(t)
    xs = [sec(t) for t in times if t is not None]
    unsorted_at = next((i for i in range(1, len(xs)) if xs[i] < xs[i - 1]), None)
    s = sorted(xs)
    d = [b - a for a, b in zip(s, s[1:])]
    pos = [x for x in d if x > 0]
    med = quantile(pos, 0.5) if pos else None
    gaps = [(i + 1, x) for i, x in enumerate(d) if med and x > gap_factor * med]
    return {"n": len(xs), "sorted": unsorted_at is None, "unsorted_at": unsorted_at, "median_sec": med,
            "gaps": gaps[:20], "n_gaps": len(gaps), "duplicates": sum(1 for x in d if x == 0)}


def md_table(rows: Sequence[Dict], cols: Optional[Sequence[str]] = None, fmt: str = "%.4g") -> str:
    """빈 입력이면 '(no rows)'. 셀 안의 | 와 줄바꿈은 바꿔 써서 표가 깨지지 않게 한다."""
    if not rows:
        return "(no rows)"
    cols = list(cols or rows[0].keys())

    def cell(v):
        v = fmt % v if isinstance(v, float) else ("" if v is None else str(v))
        return v.replace("|", "/").replace("\n", " ")
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(cell(r.get(c)) for c in cols) + " |" for r in rows]
    return "\n".join(out)
