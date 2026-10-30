#!/usr/bin/env python3
"""profile_data.py — CSV/TSV/JSONL 첫 점검 (stdlib, pandas 불필요, 메모리 일정).

차용 없음(스트리밍 프로파일 아이디어는 여러 공개 키트 참고, 코드 새로 작성).

사용:
  python3 profile_data.py data/train.csv data/events.jsonl [--md] [--sample 100000] [--max-rows N]
          [--top 5] [--no-values] [--delimiter ','] [--encoding cp949]
  - 행 수는 파일 끝까지 스트리밍으로 센다(--max-rows N이면 N행에서 읽기를 멈추고 "N+"로 표시).
  - 컬럼 통계·중복 추정은 앞쪽 --sample 행만 쓴다(고유값·해시 집합 상한으로 메모리 일정).
    표본 뒤는 파싱하지 않고 빈 줄이 아닌 원시 줄 수만 센다(표본에 따옴표 안 줄바꿈이 있으면 끝까지 파싱).
  - 인코딩은 앞 64KB로 추정한다. 뒤에서 깨진 글자(U+FFFD)가 나오면 cp949로 다시 읽고 WARN을 붙인다.
  - 같은 이름의 열은 val, val.1, val.2로 나눠 센다.
  - .gz도 읽는다. xlsx/parquet는 대상 아님(설치된 도구가 있을 때 따로).
출력: stdout(기본 텍스트, --md면 마크다운). 파일을 쓰지 않는다.
  끝에 키 후보·개인정보 의심 열과 "담당자 질문 후보"(결측·중복·시각·타입 혼합·키·개인정보)를 붙인다.
  질문 후보는 초안이다. 사람이 골라 TASK §3에 옮기고 직접 보낸다.
"""
import argparse
import codecs
import csv
import gzip
import hashlib
import io
import json
import math
import re
import sys
from collections import Counter

ENCODINGS = ("utf-8-sig", "utf-8", "cp949", "latin-1")
MISSING = {"", "na", "n/a", "nan", "null", "none", "-", "?"}
UNIQUE_CAP = 1000
TOP_CAP = 5000
DUP_CAP = 200000
TS_RE = re.compile(r"^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}([ T]\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?)?(Z|[+-]\d{2}:?\d{2})?$"
                   r"|^\d{1,2}:\d{2}(:\d{2})?$|^\d{8}([ T]?\d{6})?$")
PII_NAME = re.compile(r"(^name$|operator|user|worker|employee|person|e-?mail|phone|mobile|^tel$|addr|ssn|birth"
                      r"|이름|성명|작업자|전화|휴대|주소|주민|생년|사번|이메일)", re.I)  # tool_name·recipe_name은 제외
TS_NAME = re.compile(r"(time|date|ts$|^ts|dt$|stamp|시각|시간|일자|날짜)", re.I)

csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))
DECODE_ERRORS = [0]


def _count_replace(e):
    DECODE_ERRORS[0] += 1
    return "\ufffd", e.end


codecs.register_error("hx_count", _count_replace)


def open_bin(path):
    return gzip.open(path, "rb") if path.endswith(".gz") else open(path, "rb")


def guess_encoding(head):
    for enc in ENCODINGS:
        for cut in range(4):  # 표본 끝에서 잘린 멀티바이트 문자 허용
            try:
                (head[:len(head) - cut] if cut else head).decode(enc)
                return enc
            except UnicodeDecodeError:
                continue
    return "latin-1"


def guess_kind(path, text_head):
    base = path[:-3] if path.endswith(".gz") else path
    if base.endswith((".jsonl", ".ndjson")):
        return "jsonl"
    first = text_head.lstrip()[:1]
    if base.endswith(".json") and first in "{[":
        return "jsonl" if first == "{" else "json"
    return "csv"


def guess_delimiter(path, text_head):
    base = path[:-3] if path.endswith(".gz") else path
    lines = "\n".join(text_head.splitlines()[:50])
    try:
        return csv.Sniffer().sniff(lines, delimiters=",\t;|").delimiter
    except csv.Error:
        return "\t" if base.endswith(".tsv") else ","


def classify(v):
    s = v.strip()
    if s.lower() in MISSING:
        return "missing", None
    if s.lower() in ("true", "false"):
        return "bool", None
    try:
        f = float(s.replace(",", "")) if re.match(r"^-?[\d,]+(\.\d+)?$", s) else float(s)
        if math.isnan(f) or math.isinf(f):
            return "missing", None
        return ("int" if re.match(r"^-?\d+$", s) else "float"), f
    except ValueError:
        pass
    if TS_RE.match(s):
        return "datetime", None
    return "str", None


class Col:
    def __init__(self, name):
        self.name = name
        self.n = 0
        self.kinds = Counter()
        self.lo = self.hi = None
        self.slo = self.shi = None
        self.uniq = set()
        self.uniq_over = False
        self.top = Counter()

    def add(self, v):
        self.n += 1
        v = "" if v is None else (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
        k, f = classify(v)
        self.kinds[k] += 1
        if k == "missing":
            return
        if f is not None:
            self.lo = f if self.lo is None else min(self.lo, f)
            self.hi = f if self.hi is None else max(self.hi, f)
        elif k == "datetime":
            s = v.strip()
            self.slo = s if self.slo is None else min(self.slo, s)
            self.shi = s if self.shi is None else max(self.shi, s)
        if not self.uniq_over:
            self.uniq.add(v)
            if len(self.uniq) > UNIQUE_CAP:
                self.uniq_over, self.uniq = True, set()
        if v in self.top or len(self.top) < TOP_CAP:
            self.top[v] += 1

    def summary(self, top_n, show_values):
        miss = self.kinds.get("missing", 0)
        present = {k: c for k, c in self.kinds.items() if k != "missing"}
        typ = max(present, key=present.get) if present else "empty"
        if len(present) > 1:
            typ += " (mixed: " + ",".join("{}={}".format(k, c) for k, c in sorted(present.items())) + ")"
        rng = ""
        if self.lo is not None:
            rng = "{:g} .. {:g}".format(self.lo, self.hi)
        elif self.slo is not None:
            rng = "{} .. {}".format(self.slo, self.shi)
        ts = bool(self.kinds.get("datetime")) or bool(TS_NAME.search(self.name))
        top = ""
        if show_values and top_n > 0:
            top = ", ".join("{}×{}".format(trunc(v), c) for v, c in self.top.most_common(top_n))
        uniq = ">{}".format(UNIQUE_CAP) if self.uniq_over else str(len(self.uniq))
        return {"col": self.name, "type": typ, "missing": "{} ({:.1%})".format(miss, miss / self.n if self.n else 0),
                "unique": uniq, "range": rng, "ts_candidate": "yes" if ts else "", "top": top}


def trunc(v, n=24):
    v = v.replace("\n", " ").replace("|", "/")
    return v if len(v) <= n else v[:n - 1] + "…"


def rows_csv(text, delim):
    reader = csv.reader(text, delimiter=delim)
    header = next(reader, None) or []
    header = [h.strip() or "col{}".format(i) for i, h in enumerate(header)]
    seen = Counter()
    for i, h in enumerate(header):  # 중복 열 이름: val, val.1, val.2
        if seen[h]:
            header[i] = "{}.{}".format(h, seen[h])
        seen[h] += 1
    return header, (r for r in reader if r)


def rows_jsonl(text, bad):
    for line in text:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            bad[0] += 1
            continue
        yield obj if isinstance(obj, dict) else {"value": obj}


def profile(path, a):
    """인코딩을 추정해 읽고, 추정이 utf-8인데 뒤에서 깨진 글자가 나오면 cp949로 한 번 다시 읽는다."""
    info = _profile(path, a, None)
    if not a.encoding and info["decode_errors"] and info["encoding"].startswith("utf-8"):
        alt = _profile(path, a, "cp949")
        if alt["decode_errors"] < info["decode_errors"]:
            alt["warn"] = "utf-8로 읽으니 깨진 글자 {}개 → cp949로 다시 읽음(--encoding으로 고정 가능)".format(
                info["decode_errors"])
            return alt
    if info["decode_errors"]:
        info["warn"] = "깨진 글자(U+FFFD) {}개 — 인코딩 추정({})이 틀렸을 수 있다. --encoding cp949 등으로 다시".format(
            info["decode_errors"], info["encoding"])
    return info


def _profile(path, a, force_enc):
    with open_bin(path) as fh:
        head = fh.read(65536)
    enc = force_enc or a.encoding or guess_encoding(head)
    text_head = head.decode(enc, errors="replace")
    kind = guess_kind(path, text_head)
    info = {"path": path, "encoding": enc, "kind": kind, "delimiter": "", "rows": 0, "sampled": 0,
            "complete": True, "dup_rows": 0, "dup_note": "", "bad_lines": 0, "ragged": 0, "cols": [],
            "decode_errors": 0, "raw_count": False}
    if kind == "json":
        info["note"] = "single JSON document: not streamed; inspect structure manually (head -c 2000)"
        return info
    cols, order = {}, []
    hashes, dup_over = set(), False
    bad = [0]
    DECODE_ERRORS[0] = 0
    multiline = False
    with open_bin(path) as fb:
        text = io.TextIOWrapper(fb, encoding=enc, errors="hx_count", newline="")
        if kind == "csv":
            delim = a.delimiter or guess_delimiter(path, text_head)
            info["delimiter"] = {"\t": "TAB"}.get(delim, delim)
            header, it = rows_csv(text, delim)
            for h in header:
                cols[h] = Col(h)
                order.append(h)
        else:
            it = rows_jsonl(text, bad)
        for row in it:
            info["rows"] += 1
            if a.max_rows and info["rows"] >= a.max_rows:
                info["complete"] = False
            if info["rows"] <= a.sample:
                info["sampled"] += 1
                if kind == "csv":
                    if len(row) != len(order):
                        info["ragged"] += 1
                    items = zip(order, row)
                    key = "\x1f".join(row)
                    multiline = multiline or any("\n" in v or "\r" in v for v in row)
                else:
                    for k in row:
                        if k not in cols:
                            cols[k] = Col(k)
                            order.append(k)
                    items = ((k, row.get(k)) for k in order)
                    key = json.dumps(row, sort_keys=True, ensure_ascii=False)
                for k, v in items:
                    cols[k].add(v)
                if not dup_over:
                    h = hashlib.blake2b(key.encode("utf-8", "replace"), digest_size=8).digest()
                    if h in hashes:
                        info["dup_rows"] += 1
                    else:
                        hashes.add(h)
                        if len(hashes) >= DUP_CAP:
                            dup_over = True
            if not info["complete"]:
                break
            if info["rows"] >= a.sample and not multiline:
                # 표본 끝: 나머지는 파싱하지 않고 빈 줄이 아닌 원시 줄만 센다(JSONL 깨진 줄도 행으로 셈)
                info["raw_count"] = True
                for line in text:
                    if line.strip():
                        info["rows"] += 1
                        if a.max_rows and info["rows"] >= a.max_rows:
                            info["complete"] = False
                            break
                break
    info["bad_lines"] = bad[0]
    info["decode_errors"] = DECODE_ERRORS[0]
    if dup_over:
        info["dup_note"] = "hash set capped at {} rows".format(DUP_CAP)
    info["cols"] = [cols[k].summary(a.top, not a.no_values) for k in order]
    return info


def _n(text):
    m = re.match(r"\d+", str(text))
    return int(m.group()) if m else 0


def questions(info, limit=8):
    """프로파일 → (키 후보, 개인정보 의심 열, 담당자 질문 후보 목록)."""
    cols, q = info["cols"], []
    keys = [c["col"] for c in cols if info["sampled"] > 1 and c["unique"] == str(info["sampled"])]
    # 고유값 집합 상한(UNIQUE_CAP)을 넘은 열은 중복 여부를 모른다 → 결측 0이면 "후보(중복 미확인)"로 둔다
    keys += [c["col"] + "(고유값 >{}, 중복 미확인)".format(UNIQUE_CAP) for c in cols
             if c["unique"].startswith(">") and _n(c["missing"]) == 0 and c["type"] in ("str", "int")]
    pii = [c["col"] for c in cols if PII_NAME.search(c["col"])]
    miss = [c for c in cols if _n(c["missing"]) > 0]
    if miss:
        q.append("결측 처리: {} 결측은 제외·보간·0 중 무엇으로 볼까요?".format(
            ", ".join("{}({})".format(c["col"], c["missing"].split(" ")[0]) for c in miss[:4])))
    if info["dup_rows"]:
        q.append("완전히 같은 행 {}건(표본 기준)은 중복 기록인가요, 실제 반복 측정인가요?".format(info["dup_rows"]))
    ts = [c["col"] for c in cols if c["ts_candidate"]]
    if ts:
        q.append("시각 열 {}: 시간대(KST/UTC)와 정렬 기준, 같은 시각 여러 행의 의미는?".format(", ".join(ts[:3])))
    mixed = [c["col"] for c in cols if "mixed" in c["type"]]
    if mixed:
        q.append("{} 에 숫자와 문자가 섞여 있습니다. 문자 값(예: 'NG', '-')은 무슨 뜻인가요?".format(", ".join(mixed[:3])))
    q.append("행 하나를 구분하는 키는 {} 인가요? 같은 키가 두 번 나오면 어떻게 처리할까요?".format(
        ", ".join(keys[:3]) if keys else "무엇인가요(표본에서 고유값 = 행 수인 열을 찾지 못함)"))
    if pii:
        q.append("{} 은 개인정보로 보입니다. 출력·화면에서 가려야 하나요?".format(", ".join(pii[:3])))
    return keys, pii, q[:limit]


def render(info, md):
    rows = "{}{}".format(info["rows"], "" if info["complete"] else "+ (stopped at --max-rows)")
    meta = ("rows={} sampled={} cols={} encoding={} kind={} delimiter={} dup_rows(sampled)={}{}"
            " ragged={} bad_jsonl={}").format(rows, info["sampled"], len(info["cols"]), info["encoding"],
                                              info["kind"], info["delimiter"] or "-", info["dup_rows"],
                                              " [" + info["dup_note"] + "]" if info["dup_note"] else "",
                                              info["ragged"], info["bad_lines"])
    if info.get("raw_count"):
        meta += " rows_after_sample=raw_lines"
    out = []
    keys = ("col", "type", "missing", "unique", "range", "ts_candidate", "top")
    if md:
        out += ["### " + info["path"], "", "`" + meta + "`", ""]
        if info.get("warn"):
            out.append("> WARN: " + info["warn"])
        if info.get("note"):
            out.append("> " + info["note"])
        if info["cols"]:
            out += ["| " + " | ".join(keys) + " |", "|" + "---|" * len(keys)]
            out += ["| " + " | ".join(str(c[k]).replace("|", "/") for k in keys) + " |" for c in info["cols"]]
        ts = [c["col"] for c in info["cols"] if c["ts_candidate"]]
        out += ["", "- timestamp candidates: " + (", ".join(ts) if ts else "none")]
        if info["cols"]:
            keys, pii, qs = questions(info)
            out += ["- key candidates (unique = sampled rows): " + (", ".join(keys) if keys else "none"),
                    "- PII-like column names: " + (", ".join(pii) if pii else "none"),
                    "", "**담당자 질문 후보(초안, 사람이 골라 보냄)**", ""] + ["{}. {}".format(i, x) for i, x in enumerate(qs, 1)]
        out.append("")
    else:
        out += ["== " + info["path"], meta]
        if info.get("warn"):
            out.append("WARN: " + info["warn"])
        if info.get("note"):
            out.append("NOTE: " + info["note"])
        for c in info["cols"]:
            out.append("  - {} [{}] missing={} unique={}{}{}{}".format(
                c["col"], c["type"], c["missing"], c["unique"],
                " range=" + c["range"] if c["range"] else "", " TS?" if c["ts_candidate"] else "",
                " top: " + c["top"] if c["top"] else ""))
        if info["cols"]:
            keys, pii, qs = questions(info)
            out.append("KEY? " + (", ".join(keys) if keys else "none") + " | PII? " + (", ".join(pii) if pii else "none"))
            out += ["Q{}: {}".format(i, x) for i, x in enumerate(qs, 1)]
        out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Stream-profile CSV/TSV/JSONL files (stdlib only).")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--md", action="store_true", help="markdown output")
    ap.add_argument("--sample", type=int, default=100000, help="rows used for column stats (default 100000)")
    ap.add_argument("--max-rows", type=int, default=0,
                    help="stop reading after N rows; row count shows 'N+' (0 = read all). Use on GB files")
    ap.add_argument("--top", type=int, default=5, help="top-N frequent values per column (default 5)")
    ap.add_argument("--no-values", action="store_true", help="do not print raw values (top list)")
    ap.add_argument("--delimiter", help="force delimiter (use $'\\t' for TAB)")
    ap.add_argument("--encoding", help="force encoding, e.g. cp949")
    a = ap.parse_args(argv)
    rc = 0
    for p in a.paths:
        try:
            print(render(profile(p, a), a.md))
        except (OSError, UnicodeError, csv.Error) as e:
            print("== {}\nERROR: {}: {}\n".format(p, type(e).__name__, e))
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
