#!/usr/bin/env bash
# env_check.sh — 시험 환경을 읽기 전용으로 점검해 ENVIRONMENT.md 하나를 만든다.
# 사람이 워크스페이스 루트(IDE 터미널)에서 실행: bash <H>/scripts/env_check.sh
# 원칙: 읽기 전용(쓰는 파일은 --out 하나), 명령마다 timeout, stdin 차단,
#       설치·설정 변경 없음, 비밀값 마스킹, 경고만 하고 고치지 않음.
# 차용 없음(설계: 2차_조사 harness_structure_v1.md §1.2·§1.3, AR·CE 노트를 보고 새로 씀).
# 대상: Linux + bash 4+. macOS bash 3.2에서도 --help, --stdout --quick 정도는 돈다.

exec </dev/null
export LC_ALL=C GIT_OPTIONAL_LOCKS=0 GIT_TERMINAL_PROMPT=0 PIP_NO_INPUT=1 PYTHONDONTWRITEBYTECODE=1

H="$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)"
VERSION="v1"

usage() {
  cat <<'EOF'
사용법: bash <H>/scripts/env_check.sh [옵션]

  --out PATH       출력 파일(기본 ./ENVIRONMENT.md). 이 파일 하나만 쓴다
  --stdout         파일을 만들지 않고 표준 출력으로만
  --quick          네트워크·깊은 데이터 탐색·패키지 일괄 조회 생략(≤3초)
  --no-network     네트워크 점검 끔(기본은 켬: 도메인당 HEAD 1회)
  --data-dir DIR   데이터 탐색 경로 추가(반복 가능). 기본 . ./data /data /dataset ~/data
  --diff OLD.md    이전 결과의 꼬리표와 비교해 "바뀐 항목" 절 추가
  --pip-probe      pip 설치 가능성 조회(--dry-run, 설치 없음)까지 실행. 기본 끔:
                   기본 PyPI 판정은 HEAD 응답 + EXTERNALLY-MANAGED 확인만
  --timeout SEC    네트워크 점검 시간 한도(기본 2초)
  -h, --help       이 도움말

환경변수(선택): HX_DISPLAY_MEM=16G(화면 표시 메모리), HX_DISPLAY_CPU=4,
                HX_PAR_CAP=2(병렬 상한, 기본 2)
EOF
}

OUT="./ENVIRONMENT.md"; TO_STDOUT=0; QUICK=0; NET=1; PIP_PROBE=0; NET_T=2; DIFF_FILE=""
DATA_DIRS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --out) [ $# -ge 2 ] || { echo "--out에 경로가 필요" >&2; exit 2; }; OUT="$2"; shift 2 ;;
    --out=*) OUT="${1#--out=}"; shift ;;
    --stdout) TO_STDOUT=1; shift ;;
    --quick) QUICK=1; shift ;;
    --no-network) NET=0; shift ;;
    --pip-probe) PIP_PROBE=1; shift ;;
    --data-dir) [ $# -ge 2 ] || { echo "--data-dir에 경로가 필요" >&2; exit 2; }; DATA_DIRS+=("$2"); shift 2 ;;
    --diff) [ $# -ge 2 ] || { echo "--diff에 파일이 필요" >&2; exit 2; }; DIFF_FILE="$2"; shift 2 ;;
    --timeout) [ $# -ge 2 ] || { echo "--timeout에 초가 필요" >&2; exit 2; }; NET_T="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "알 수 없는 옵션: $1 (--help 참고)" >&2; exit 2 ;;
  esac
done
case "$NET_T" in ''|*[!0-9]*) NET_T=2 ;; esac
[ "$NET_T" -lt 1 ] && NET_T=1
[ "$QUICK" = 1 ] && NET=0

# ---------- 공통 도구 ----------
now_ms() {
  if [ -n "${EPOCHREALTIME:-}" ]; then local e="${EPOCHREALTIME/./}"; echo "${e:0:13}"; else echo "$(( $(date +%s) * 1000 ))"; fi
}
T_START="$(now_ms)"

have() { command -v "$1" >/dev/null 2>&1; }
if have timeout; then TMO=timeout; elif have gtimeout; then TMO=gtimeout; else TMO=""; fi
# tmo SEC cmd... : 외부 명령에 시간 한도. timeout이 없으면 perl alarm, 그것도 없으면 그냥 실행
tmo() {
  local s="$1"; shift
  if [ -n "$TMO" ]; then "$TMO" -k 1 "$s" "$@"
  elif have perl; then perl -e 'alarm shift; exec @ARGV' "$s" "$@"
  else "$@"; fi
}
SECRET_RE='KEY|TOKEN|SECRET|PASS|AUTH|COOKIE|SESSION|CREDENTIAL'
# 대소문자 무시(BSD sed에 I 플래그가 없어 글자별 [Kk] 꼴로 쓴다)
SECRET_NAME_RE='([Kk][Ee][Yy]|[Tt][Oo][Kk][Ee][Nn]|[Ss][Ee][Cc][Rr][Ee][Tt]|[Pp][Aa][Ss][Ss]|[Aa][Uu][Tt][Hh]|[Cc][Oo][Oo][Kk][Ii][Ee]|[Ss][Ee][Ss][Ss][Ii][Oo][Nn]|[Cc][Rr][Ee][Dd][Ee][Nn][Tt][Ii][Aa][Ll])'
# URL 자격증명(scheme://user:pw@), key=value 꼴(키 이름 대소문자 무시), 키 이름 없는 토큰 값(sk-…, ghp_…, AKIA…)을 ***로.
# sk-는 숫자·대문자·_가 섞인 값만(sk-hynix-hackathon 같은 이름은 그대로)
mask() {
  sed -E -e 's#(://)[^/@[:space:]]+@#\1***@#g' \
         -e "s#([A-Za-z0-9_.-]*${SECRET_NAME_RE}[A-Za-z0-9_.-]*[\"']?[[:space:]]*[=:][[:space:]]*)[^[:space:],}]+#\\1***#g" \
         -e 's#(^|[^A-Za-z0-9])(sk-[a-z-]*[0-9A-Z_][A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9]{12,}|github_pat_[A-Za-z0-9_]{12,}|AKIA[0-9A-Z]{12,}|xox[abprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{20,})#\1***#g'
}
# 표 칸용: 탭·줄바꿈 제거, | 이스케이프, n바이트 제한(잘린 UTF-8 글자는 통째로 뺀다)
mdcell() {
  tr '\t\r\n' '   ' | sed -e 's/|/\\|/g' -e 's/[[:space:]]*$//' | awk -v n="${1:-160}" '
    length($0) <= n { print; next }
    { s = substr($0, 1, n); i = length(s); k = 0
      while (i > 0 && substr(s, i, 1) ~ /[\200-\277]/) { i--; k++ }
      if (i > 0) { c = substr(s, i, 1)
        need = (c ~ /[\360-\367]/) ? 3 : (c ~ /[\340-\357]/) ? 2 : (c ~ /[\300-\337]/) ? 1 : 0
        if (need > k) s = substr(s, 1, i - 1) }
      print s "…" }'
}
gb_from_kb() { awk -v k="$1" 'BEGIN{ if (k=="" || k<0) print ""; else printf "%.1f", k/1048576 }'; }
gb_from_b()  { awk -v b="$1" 'BEGIN{ if (b=="" ) print ""; else printf "%.1f", b/1073741824 }'; }
# "16G", "16GB", "16GiB", "16384M", "16" → GB(소수 1자리)
parse_gb() {
  echo "$1" | awk '{ s=toupper($0); gsub(/[[:space:]]|I?B$/,"",s); u=substr(s,length(s)); n=s;
    if (u ~ /[KMGT]/) n=substr(s,1,length(s)-1); else u="G";
    if (n !~ /^[0-9.]+$/) { print ""; exit }
    f=(u=="K")?1/1048576:(u=="M")?1/1024:(u=="T")?1024:1; printf "%.1f", n*f }'
}
minnum() { awk 'BEGIN{m=""} { for(i=1;i<=NF;i++) if ($i!="" && $i!="max" && (m=="" || $i+0<m+0)) m=$i } END{print m}' <<<"$*"; }
firstline() { head -n 1 | mdcell 100; }

# KST: 계약은 TZ=Asia/Seoul. tzdata가 없으면 POSIX TZ 문자열 KST-9로 대체
KST_TZ="Asia/Seoul"
[ "$(TZ=Asia/Seoul date +%z 2>/dev/null)" = "+0900" ] || KST_TZ="KST-9"
KST_NOW="$(TZ=$KST_TZ date '+%Y-%m-%d %H:%M:%S') KST"
UTC_NOW="$(date -u '+%Y-%m-%d %H:%M:%S') UTC"
TZ_OFF="$(date +%z 2>/dev/null)"; case "$TZ_OFF" in [+-][0-9][0-9][0-9][0-9]) ;; *) TZ_OFF="+0000" ;; esac
LOCAL_NOW="$(date '+%Y-%m-%d %H:%M:%S %Z %z' 2>/dev/null)"

CWD="$(pwd -P)"
PYBIN=""
if have python3; then PYBIN=python3
elif have python && python -c 'import sys; sys.exit(0 if sys.version_info[0]==3 else 1)' 2>/dev/null; then PYBIN=python; fi

# ---------- 병렬 점검 작업(각 줄 TAG<TAB>값...) ----------
RUNTIMES="python3 python pip pip3 uv conda mamba poetry pipenv node npm pnpm yarn bun git sqlite3 duckdb jq make gcc cmake java go rustc curl wget codex claude"
QUICK_VER="python3 node git codex"
# 버전 조회가 홈에 파일을 만들거나(rustup·corepack·JVM) 내려받을 수 있는 것: 실행하지 않고 경로만
NO_EXEC="claude pnpm yarn rustc java poetry conda mamba pipenv"

ver_of() {
  case "$1" in
    go) tmo 2 go version 2>&1 | firstline ;;
    node|npm) tmo 3 "$1" -v 2>&1 | firstline ;;
    python|python3) tmo 2 "$1" -V 2>&1 | firstline ;;
    *) tmo 2 "$1" --version 2>&1 | firstline ;;
  esac
}
job_versions() {
  local n p
  for n in $RUNTIMES; do
    p="$(command -v "$n" 2>/dev/null)"
    if [ -z "$p" ]; then printf 'VER\t%s\t-\t-\n' "$n"; continue; fi
    if [ "$n" = claude ]; then printf 'VER\t%s\t%s\t(존재만 점검, 이번 회차 사용 금지)\n' "$n" "$p"; continue; fi
    if [[ " $NO_EXEC " == *" $n "* ]]; then printf 'VER\t%s\t%s\t(실행 안 함: 버전 조회가 홈에 파일을 만들 수 있음)\n' "$n" "$p"; continue; fi
    if [ "$QUICK" = 1 ] && ! [[ " $QUICK_VER " == *" $n "* ]]; then printf 'VER\t%s\t%s\t(--quick: 버전 생략)\n' "$n" "$p"; continue; fi
    ( printf 'VER\t%s\t%s\t%s\n' "$n" "$p" "$(ver_of "$n" | mask)" ) &
  done
  wait
}

PY_SNIPPET='
import sys
sys.path[:] = [p for p in sys.path if p not in ("", ".")]  # 작업 폴더의 같은 이름 모듈이 가리지 않게
import os, socket, importlib.util, sysconfig
quick = len(sys.argv) > 1 and sys.argv[1] == "quick"
try:
    from importlib import metadata as md
except Exception:
    md = None
def out(k, v): print("PY\t%s\t%s" % (k, v))
out("VER", "%d.%d.%d" % sys.version_info[:3])
out("EXE", sys.executable)
out("IN_VENV", "yes" if sys.prefix != getattr(sys, "base_prefix", sys.prefix) else "no")
out("VENV_MOD", "yes" if importlib.util.find_spec("venv") else "no")
out("ENSUREPIP", "yes" if importlib.util.find_spec("ensurepip") else "no")
try:
    em = os.path.exists(os.path.join(sysconfig.get_path("stdlib"), "EXTERNALLY-MANAGED"))
except Exception:
    em = False
out("EXT_MANAGED", "yes" if em else "no")
from datetime import datetime
try:
    datetime.fromisoformat("2026-10-31T01:00:00Z"); out("ISO_Z", "ok")
except Exception:
    out("ISO_Z", "fail")
for host in ("127.0.0.1", "0.0.0.0"):
    s = socket.socket()
    try:
        s.bind((host, 0)); s.listen(1); out("BIND_" + host, "ok:%d" % s.getsockname()[1])
    except Exception as e:
        out("BIND_" + host, "denied:" + type(e).__name__)
    finally:
        s.close()
pk = [("numpy","numpy"),("pandas","pandas"),("scikit-learn","sklearn"),("pip","pip")]
if not quick:
    pk += [("scipy","scipy"),("lightgbm","lightgbm"),("xgboost","xgboost"),("catboost","catboost"),
           ("statsmodels","statsmodels"),("torch","torch"),("fastapi","fastapi"),("uvicorn","uvicorn"),
           ("pydantic","pydantic"),("flask","flask"),("streamlit","streamlit"),("matplotlib","matplotlib"),
           ("plotly","plotly"),("openpyxl","openpyxl"),("pypdf","pypdf"),("pdfplumber","pdfplumber"),
           ("pytest","pytest"),("duckdb","duckdb"),("pyarrow","pyarrow"),("polars","polars")]
for dist, mod in pk:
    v = "none"
    try:
        if importlib.util.find_spec(mod) is not None:
            v = "yes"
            if md is not None:
                try: v = md.version(dist)
                except Exception: pass
    except Exception:
        v = "none"
    print("PKG\t%s\t%s" % (mod, v))
'
job_python() {
  if [ -z "$PYBIN" ]; then echo "PY	NONE	1"; return; fi
  tmo 6 "$PYBIN" -c "$PY_SNIPPET" "$([ "$QUICK" = 1 ] && echo quick)" 2>/dev/null
}

job_socket_node() {  # python이 없을 때만: node로 0.0.0.0 바인드 시험
  have node || return
  local r
  r="$(tmo 3 node -e "const s=require('net').createServer();s.on('error',e=>{console.log('denied:'+e.code)});s.listen(0,'0.0.0.0',()=>{console.log('ok:'+s.address().port);s.close()})" 2>/dev/null)"
  [ -n "$r" ] && printf 'PY\tBIND_0.0.0.0\t%s\n' "$r"
}

NET_HOSTS="https://github.com https://raw.githubusercontent.com https://pypi.org/simple/ https://files.pythonhosted.org https://registry.npmjs.org"
NET_PY='
import sys
sys.path[:] = [p for p in sys.path if p not in ("", ".")]
import time, urllib.request, urllib.error, concurrent.futures as cf
t = float(sys.argv[1]); urls = sys.argv[2:]
def head(u):
    s = time.time()
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, method="HEAD"), timeout=t); c = r.status
    except urllib.error.HTTPError as e: c = e.code
    except Exception: c = 0
    return u, c, int((time.time() - s) * 1000)
with cf.ThreadPoolExecutor(len(urls) or 1) as ex:
    for u, c, ms in ex.map(head, urls): print("NET\t%s\t%03d\t%d" % (u, c, ms))
'
job_network() {
  local urls="$NET_HOSTS" u
  if have curl; then
    for u in $urls; do
      ( r="$(tmo $((NET_T + 2)) curl -sS -I -o /dev/null --connect-timeout "$NET_T" -m "$NET_T" -w '%{http_code} %{time_total}' "$u" 2>/dev/null)"
        set -- $r; printf 'NET\t%s\t%s\t%s\n' "$u" "${1:-000}" "$(awk -v s="${2:-0}" 'BEGIN{printf "%d", s*1000}')" ) &
    done
  elif [ -n "$PYBIN" ]; then
    # shellcheck disable=SC2086
    ( tmo $((NET_T + 3)) "$PYBIN" -c "$NET_PY" "$NET_T" $urls 2>/dev/null ) &
  elif have wget; then
    for u in $urls; do
      ( if tmo $((NET_T + 2)) wget -q --spider -T "$NET_T" -t 1 "$u" 2>/dev/null; then c=200; else c=000; fi
        printf 'NET\t%s\t%s\t-\n' "$u" "$c" ) &
    done
  else
    echo "NETTOOL	none"
  fi
  if have getent; then
    for u in github.com pypi.org registry.npmjs.org; do
      ( a="$(tmo 2 getent hosts "$u" 2>/dev/null | awk '{print $1; exit}')"; printf 'DNS\t%s\t%s\n' "$u" "${a:-실패}" ) &
    done
  fi
  # 설치 가능성 조회(실제 설치 없음, 캐시 없음): --pip-probe를 줬을 때만. 허용된 단 한 곳
  if [ -n "$PYBIN" ] && [ "$PIP_PROBE" = 1 ]; then
    ( r="$(tmo $((NET_T * 3 + 2)) "$PYBIN" -m pip install --dry-run --no-deps --ignore-installed --no-cache-dir --disable-pip-version-check --retries 0 --timeout "$NET_T" -q six 2>&1)"; rc=$? # hx-allow: pip-dry-run
      em=no; printf '%s' "$r" | grep -qiE 'externally-managed|PEP 668' && em=yes
      printf 'PIPDRY\t%s\t%s\t%s\n' "$rc" "$(printf '%s' "$r" | tail -n 1 | mask | mdcell 120)" "$em" ) &
  fi
  wait
}

job_codex() {
  local p v help sub
  p="$(command -v codex 2>/dev/null)" || { echo "CODEX	PATH	-"; return; }
  printf 'CODEX\tPATH\t%s\n' "$p"
  ( v="$(tmo 2 codex --version 2>&1 | firstline | mask)"; printf 'CODEX\tVER\t%s\n' "${v:--}" ) &
  ( help="$(tmo 2 codex --help 2>&1)"
    # 도움말 원문은 출력하지 않는다(옵션 이름이 문서에 들어가지 않게). 정해 둔 서브커맨드 존재만
    for sub in exec resume mcp review apply completion; do
      if printf '%s\n' "$help" | grep -Eq "^[[:space:]]+$sub([[:space:]]|,|$)"; then printf 'CODEX\tSUB\t%s\tyes\n' "$sub"; else printf 'CODEX\tSUB\t%s\tno\n' "$sub"; fi
    done ) &
  wait
}

DATA_EXT='csv tsv parquet json jsonl ndjson db sqlite sqlite3 h5 hdf5 npz npy pkl pickle zip gz xlsx xls pdf feather arrow log'
job_data() {
  local depth=3 d ad names="" e f sz n=0 lines head2
  [ "$QUICK" = 1 ] && depth=1
  for e in $DATA_EXT; do names="$names -o -iname *.$e"; done
  names="${names# -o }"
  for d in "$@"; do [ -d "$d" ] && printf 'DDIR\t%s\n' "$(cd "$d" 2>/dev/null && pwd -P)"; done
  for d in "$@"; do
    [ -d "$d" ] || continue
    ad="$(cd "$d" 2>/dev/null && pwd -P)" || continue
    # shellcheck disable=SC2086
    set -f
    tmo 3 find "$ad" -maxdepth "$depth" \( -path "$ad/*" -name '.*' -o -name node_modules -o -name __pycache__ -o -name _harness -o -name venv -o -name notes -o -name exp \) -prune -o -type f \( $names \) -print 2>/dev/null | head -n 400
    set +f
  done | sort -u | while IFS= read -r f; do
    sz="$(wc -c <"$f" 2>/dev/null | tr -d ' ')"; [ -n "$sz" ] || continue
    n=$((n + 1)); lines="-"; head2="-"
    if [ "$QUICK" = 0 ] && [ "$n" -le 10 ] && [ "$sz" -le 52428800 ]; then
      case "$f" in *.csv|*.CSV|*.tsv|*.TSV|*.json|*.jsonl|*.ndjson|*.log|*.LOG)
        lines="$(tmo 2 wc -l <"$f" 2>/dev/null | tr -d ' ')"
        head2="$(head -c 400 "$f" 2>/dev/null | head -n 2 | mask | mdcell 160)" ;;
      esac
    fi
    printf 'DATA\t%s\t%s\t%s\t%s\n' "$sz" "$f" "${lines:--}" "$head2"
  done
}

job_wheels() {  # 오프라인 대비 로컬 wheel 단서(홈·/opt 한정, 얕게)
  [ -n "$PYBIN" ] && printf 'WHEEL\tCACHE\t%s\n' "$(tmo 3 "$PYBIN" -m pip cache dir --disable-pip-version-check 2>/dev/null | firstline)"
  local c
  c="$(tmo 2 find "$HOME" /opt -maxdepth 4 -name '*.whl' -type f 2>/dev/null | head -n 50 | wc -l | tr -d ' ')"
  printf 'WHEEL\tCOUNT\t%s\n' "${c:-0}"
}

job_git() {
  have git || { echo "GIT	TOOL	none"; return; }
  local r top gd
  r="$(tmo 2 git -C "$CWD" rev-parse --is-inside-work-tree 2>&1)"
  if [ "$r" = "true" ]; then
    top="$(tmo 2 git -C "$CWD" rev-parse --show-toplevel 2>/dev/null)"
    gd="$(cd "$CWD" && tmo 2 git rev-parse --absolute-git-dir 2>/dev/null)"
    printf 'GIT\tREPO\tyes\nGIT\tTOP\t%s\nGIT\tGITDIR\t%s\n' "$top" "$gd"
    printf 'GIT\tBRANCH\t%s\n' "$(tmo 2 git -C "$CWD" rev-parse --abbrev-ref HEAD 2>/dev/null)"
    printf 'GIT\tHEAD\t%s\n' "$(tmo 2 git -C "$CWD" log -1 --format='%h %cd' --date=iso 2>/dev/null | mdcell 60)"
    printf 'GIT\tDIRTY\t%s\n' "$(tmo 3 git -C "$CWD" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
    tmo 2 git -C "$CWD" remote -v 2>/dev/null | awk '$3=="(fetch)"{print $1"\t"$2}' | mask | while IFS="	" read -r a b; do printf 'GITREMOTE\t%s\t%s\n' "$a" "$b"; done
    printf 'GIT\tHOOKS\t%s\n' "$(ls "$gd/hooks" 2>/dev/null | grep -v '\.sample$' | tr '\n' ' ')"
    printf 'GIT\tUSER\t%s\n' "$( [ -n "$(tmo 2 git -C "$CWD" config user.name 2>/dev/null)" ] && echo set || echo unset)"
  elif printf '%s' "$r" | grep -qi 'dubious ownership'; then
    echo "GIT	REPO	dubious"
  else
    echo "GIT	REPO	no"
  fi
}

job_harness() {
  local c=""
  if have git; then c="$(tmo 2 git -C "$H" rev-parse --short=12 HEAD 2>/dev/null)"; fi
  if [ -z "$c" ] && [ -f "$H/.git/HEAD" ]; then
    local ref; ref="$(sed -n 's/^ref: //p' "$H/.git/HEAD")"
    if [ -n "$ref" ] && [ -f "$H/.git/$ref" ]; then c="$(cut -c1-12 "$H/.git/$ref")"; elif [ -z "$ref" ]; then c="$(cut -c1-12 "$H/.git/HEAD")"; fi
  fi
  printf 'HX\tCOMMIT\t%s\n' "${c:-unknown}"
  if have git; then printf 'HX\tREMOTES\t%s\n' "$(tmo 2 git -C "$H" remote 2>/dev/null | tr '\n' ' ')"; fi
}

job_ports() {
  if have ss; then tmo 2 ss -ltnH 2>/dev/null | awk '{print "PORT\t"$4}' | head -n 15
  elif [ -r /proc/net/tcp ]; then
    awk 'function h(x,  i,n){n=0; for(i=1;i<=length(x);i++) n=n*16+index("0123456789ABCDEF",substr(toupper(x),i,1))-1; return n}
         NR>1 && $4=="0A"{split($2,a,":"); print "PORT\t:" h(a[2])}' /proc/net/tcp /proc/net/tcp6 2>/dev/null | sort -u | head -n 15
  fi
}

DEFAULT_DATA=(. ./data /data /dataset "$HOME/data")
PROBE="$(
  job_versions &
  job_python &
  job_codex &
  job_git &
  job_harness &
  job_ports &
  job_data "${DEFAULT_DATA[@]}" ${DATA_DIRS[@]+"${DATA_DIRS[@]}"} &
  [ -z "$PYBIN" ] && job_socket_node &
  [ "$NET" = 1 ] && job_network &
  [ "$QUICK" = 0 ] && job_wheels &
  wait
)"
pget() { printf '%s\n' "$PROBE" | awk -F'\t' -v t="$1" -v k="$2" '$1==t && $2==k {sub(/^[^\t]*\t[^\t]*\t/,""); print; exit}'; }
pall() { printf '%s\n' "$PROBE" | awk -F'\t' -v t="$1" '$1==t'; }

# ---------- 순차 수집(가벼운 것) ----------
OS_KERNEL="$(uname -srm 2>/dev/null)"
OS_NAME="$( (. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-}") )"; [ -n "$OS_NAME" ] || OS_NAME="$(uname -s)"
IS_LINUX=0; [ "$(uname -s)" = "Linux" ] && IS_LINUX=1
USER_NAME="$(id -un 2>/dev/null)"; USER_ID="$(id -u 2>/dev/null)"
USER_GROUPS="$(id -Gn 2>/dev/null | mdcell 120)"
SUDO_BIN="$(command -v sudo 2>/dev/null)"; ADMIN_GRP=no; case " $USER_GROUPS " in *" sudo "*|*" wheel "*|*" admin "*) ADMIN_GRP=yes ;; esac # hx-allow: sudo-probe (존재·그룹만 확인, 실행하지 않음)
HOSTHASH="$( (hostname 2>/dev/null || cat /proc/sys/kernel/hostname 2>/dev/null) | cksum | cut -d' ' -f1)"
CONTAINER=""
[ -f /.dockerenv ] && CONTAINER="$CONTAINER docker(/.dockerenv)"
[ -f /run/.containerenv ] && CONTAINER="$CONTAINER podman"
grep -qs hypervisor /proc/cpuinfo && CONTAINER="$CONTAINER VM(hypervisor 플래그)"
[ -n "$(env | cut -d= -f1 | grep -E '^E2B' | head -n 1)" ] && CONTAINER="$CONTAINER E2B(env)"
CONTAINER="${CONTAINER# }"; [ -n "$CONTAINER" ] || CONTAINER="단서 없음"
TZ_FILE="$(cat /etc/timezone 2>/dev/null | head -n 1)"
LOCALTIME="$(readlink /etc/localtime 2>/dev/null)"; [ -z "$LOCALTIME" ] && [ -e /etc/localtime ] && LOCALTIME="(파일)"
APT_PRESENT="$(for c in apt dpkg apk yum dnf; do have "$c" && printf '%s ' "$c"; done)"
RO_MOUNTS="$(awk '$4 ~ /(^|,)ro(,|$)/ && $2 !~ /^\/(proc|sys|dev)(\/|$)/ {print $2}' /proc/mounts 2>/dev/null | head -n 8 | tr '\n' ' ')"

# GPU
GPU=0; GPU_INFO="없음"
if have nvidia-smi; then
  GPU_INFO="$(tmo 3 nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | head -n 4 | tr '\n' ';' | mdcell 120)"
  GPU="$(tmo 3 nvidia-smi -L 2>/dev/null | grep -c '^GPU')"
  [ -n "$GPU_INFO" ] || GPU_INFO="nvidia-smi 있음, 응답 없음"
elif ls /dev/nvidia0 >/dev/null 2>&1; then GPU=1; GPU_INFO="/dev/nvidia0 있음(nvidia-smi 없음)"; fi

# 메모리·CPU·PIDs: /proc + cgroup v2, 없으면 v1
MEM_TOTAL_KB="$(awk '/^MemTotal:/{print $2}' /proc/meminfo 2>/dev/null)"
MEM_AVAIL_KB="$(awk '/^MemAvailable:/{print $2}' /proc/meminfo 2>/dev/null)"
if [ -z "$MEM_TOTAL_KB" ] && have sysctl; then  # macOS 등(대상 아님, 표시만)
  b="$(sysctl -n hw.memsize 2>/dev/null)"; [ -n "$b" ] && MEM_TOTAL_KB=$((b / 1024))
fi
CGROUP=none; CG_MEM=""; CG_CPU=""; CG_PIDS=""; CG_DIR=""
if [ -f /sys/fs/cgroup/cgroup.controllers ]; then
  CGROUP=v2
  rel="$(awk -F: '$1=="0"{print $3; exit}' /proc/self/cgroup 2>/dev/null)"
  # 리프에서 루트까지 올라가며 유효 최솟값(리프가 max여도 상위 한도가 걸릴 수 있다)
  d="/sys/fs/cgroup${rel%/}"; mems=""; cpus=""; pidv=""
  while :; do
    if [ -r "$d/memory.max" ] || [ -r "$d/pids.max" ] || [ -r "$d/cpu.max" ]; then
      [ -n "$CG_DIR" ] || CG_DIR="$d"
      mems="$mems $(cat "$d/memory.max" 2>/dev/null)"; pidv="$pidv $(cat "$d/pids.max" 2>/dev/null)"
      cpus="$cpus $(awk '$1!="max" && $2>0 {printf "%.2f", $1/$2}' "$d/cpu.max" 2>/dev/null)"
    fi
    [ "$d" = /sys/fs/cgroup ] || [ "$d" = /sys/fs ] && break
    d="$(dirname "$d")"
  done
  [ -n "$CG_DIR" ] || CG_DIR=/sys/fs/cgroup
  CG_MEM="$(minnum $mems)"; CG_CPU="$(minnum $cpus)"; CG_PIDS="$(minnum $pidv)"
  [ -n "$CG_MEM" ] || CG_MEM=max; [ -n "$CG_PIDS" ] || CG_PIDS=max
elif [ -d /sys/fs/cgroup/memory ] || [ -d /sys/fs/cgroup/pids ]; then
  CGROUP=v1
  CG_MEM="$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null)"
  q="$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null)"; p="$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null)"
  [ -n "$q" ] && [ "$q" != "-1" ] && [ -n "$p" ] && CG_CPU="$(awk -v q="$q" -v p="$p" 'BEGIN{printf "%.2f", q/p}')"
  CG_PIDS="$(cat /sys/fs/cgroup/pids/pids.max 2>/dev/null)"
fi
# v1 "무제한"은 9223372036854771712 같은 19자리 값 → 제한 없음으로 표시
case "$CG_MEM" in ''|max) ;; *) [ "${#CG_MEM}" -ge 19 ] && CG_MEM="제한 없음" ;; esac
case "$CG_PIDS" in ''|max) ;; *[!0-9]*) ;; *) [ "${#CG_PIDS}" -ge 19 ] && CG_PIDS=max ;; esac
CG_MEM_GB=""; case "$CG_MEM" in ''|max|*[!0-9]*) ;; *) CG_MEM_GB="$(gb_from_b "$CG_MEM")" ;; esac
MEM_TOTAL_GB="$(gb_from_kb "$MEM_TOTAL_KB")"; MEM_AVAIL_GB="$(gb_from_kb "$MEM_AVAIL_KB")"
DISP_MEM_GB=""; [ -n "${HX_DISPLAY_MEM:-}" ] && DISP_MEM_GB="$(parse_gb "$HX_DISPLAY_MEM")"
MEM_EFF_GB="$(minnum "$MEM_TOTAL_GB" "$CG_MEM_GB" "$DISP_MEM_GB")"; [ -n "$MEM_EFF_GB" ] || MEM_EFF_GB="0"
NPROC_RAW="$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)"
CG_CPU_CEIL=""; [ -n "$CG_CPU" ] && CG_CPU_CEIL="$(awk -v c="$CG_CPU" 'BEGIN{n=int(c); if (n<c) n++; if (n<1) n=1; print n}')"
DISP_CPU=""; case "${HX_DISPLAY_CPU:-}" in ''|*[!0-9]*) ;; *) DISP_CPU="$HX_DISPLAY_CPU" ;; esac
NPROC="$(minnum "$NPROC_RAW" "$CG_CPU_CEIL" "$DISP_CPU")"; [ -n "$NPROC" ] || NPROC=1
ULIM_U="$(ulimit -u 2>/dev/null)"; ULIM_N="$(ulimit -n 2>/dev/null)"; ULIM_V="$(ulimit -v 2>/dev/null)"; ULIM_S="$(ulimit -s 2>/dev/null)"
PIDS_MAX="$(minnum "$CG_PIDS" "$( [ "$ULIM_U" = unlimited ] || echo "$ULIM_U")")"; [ -n "$PIDS_MAX" ] || PIDS_MAX=max

# 디스크
df_avail_kb() { tmo 3 df -Pk "$1" 2>/dev/null | awk 'NR==2{print $4}'; }
DISK_KB="$(df_avail_kb .)"; TMP_KB="$(df_avail_kb /tmp)"
DISK_GB="$(gb_from_kb "$DISK_KB")"; TMP_GB="$(gb_from_kb "$TMP_KB")"
INODE="$(tmo 3 df -Pi . 2>/dev/null | awk 'NR==2{print $4" 남음("$5" 사용)"}')"

# 쓰기 가능 경로(실제 파일을 만들지 않고 test -w)
wstate() {
  if [ -e "$1" ]; then [ -w "$1" ] && echo "쓰기 가능" || echo "쓰기 불가"
  else local par; par="$(dirname "$1")"; [ -w "$par" ] && echo "없음(만들 수 있음)" || echo "없음(만들 수 없음)"; fi
}
W_CWD=no; [ -w "$CWD" ] && W_CWD=yes
W_TMP=no; [ -w /tmp ] && W_TMP=yes

# 파이썬 결과
PY_VER="$(pget PY VER)"
if [ -n "$PY_VER" ]; then PY="$(echo "$PY_VER" | cut -d. -f1-2)"; else PY=none; fi
pkg() { local v; v="$(printf '%s\n' "$PROBE" | awk -F'\t' -v m="$1" '$1=="PKG" && $2==m {print $3; exit}')"; echo "${v:-none}"; }
PANDAS="$(pkg pandas)"; SKLEARN="$(pkg sklearn)"; NUMPY="$(pkg numpy)"
B0="$(pget PY BIND_0.0.0.0)"; B1="$(pget PY BIND_127.0.0.1)"
case "$B0" in ok*) SOCKET=ok; SOCKET_NOTE="0.0.0.0 바인드 성공" ;;
  denied*) SOCKET=denied; SOCKET_NOTE="0.0.0.0 바인드 거부($B0)" ;;
  *) SOCKET=denied; SOCKET_NOTE="미측정(python·node 없음) → 꼬리표는 보수적으로 denied" ;; esac

# 네트워크 결과
NET_ROWS="$(pall NET)"
net_code() { printf '%s\n' "$NET_ROWS" | awk -F'\t' -v u="$1" '$2==u{print $3; exit}'; }
reach() { case "$1" in ''|000|403|407) return 1 ;; *) return 0 ;; esac; }
PIPDRY_RC="$(pall PIPDRY | cut -f2)"; PIPDRY_RC_RAW="$PIPDRY_RC"; PIPDRY_MSG="$(pall PIPDRY | cut -f3)"; PIPDRY_EM="$(pall PIPDRY | cut -f4)"
PIP_NOTE=""; PIP_EM_NOTE=""
# 기본 경로(dry-run 없음)에서도 EXTERNALLY-MANAGED 표식 파일로 PEP 668을 판정
[ "$(pget PY EXT_MANAGED)" = yes ] && PIP_EM_NOTE=" · 전역 pip은 PEP 668로 막힘(설치는 venv에서만)"
# PEP 668(EXTERNALLY-MANAGED)이면 dry-run도 거부된다 → 네트워크 판단은 HEAD로, 설치는 venv에서만
[ "$PIPDRY_EM" = yes ] && { PIPDRY_RC=""; PIPDRY_MSG="전역 pip은 PEP 668로 막힘(설치는 venv에서만)"; PIP_EM_NOTE=" · 전역 pip은 PEP 668로 막힘"; }
if [ "$NET" = 0 ]; then PIP_NET=unknown; PIP_NOTE="네트워크 점검 생략(--no-network/--quick)"
else
  if [ "$PIPDRY_RC" = 0 ]; then PIP_NET=ok; PIP_NOTE="pip 설치 가능성 조회(dry-run) 성공"
  elif [ -n "$PIPDRY_RC" ] && ! printf '%s' "$PIPDRY_MSG" | grep -qiE 'no such option|No module named pip'; then
    PIP_NET=blocked; PIP_NOTE="pip dry-run 실패: $PIPDRY_MSG"
  elif reach "$(net_code https://pypi.org/simple/)" && reach "$(net_code https://files.pythonhosted.org)"; then
    PIP_NET=ok; PIP_NOTE="pypi.org·files.pythonhosted.org HTTP 응답$PIP_EM_NOTE"
  elif [ -z "$NET_ROWS" ]; then PIP_NET=unknown; PIP_NOTE="HTTP 점검 도구 없음(curl·python·wget)"
  else PIP_NET=blocked; PIP_NOTE="PyPI HTTP 응답 없음/차단$PIP_EM_NOTE"; fi
fi
HAS_PIP=no; { [ "$(pkg pip)" != none ] || have pip || have pip3; } && HAS_PIP=yes
VENV_OK=no; { [ "$(pget PY VENV_MOD)" = yes ] && [ "$(pget PY ENSUREPIP)" = yes ]; } && VENV_OK=yes
have uv && VENV_OK=yes UV_NOTE="(uv 있음)"

# Codex
CODEX_PATH="$(pget CODEX PATH)"; [ "$CODEX_PATH" = "-" ] && CODEX_PATH=""
CODEX_VER="$(pget CODEX VER)"
CODEX_EXEC=no; printf '%s\n' "$PROBE" | awk -F'\t' '$1=="CODEX" && $2=="SUB" && $3=="exec" && $4=="yes"{f=1} END{exit !f}' && CODEX_EXEC=yes
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
CFG_KEYS=""; MCP_NAMES=""
for cfg in "$CODEX_DIR/config.toml" "$CWD/.codex/config.toml"; do
  [ -r "$cfg" ] || continue
  k="$(awk -v f="$cfg" '
    /^[[:space:]]*\[/ { sec=$0; gsub(/[][[:space:]]/,"",sec); next }
    sec=="" && /^[[:space:]]*(model|model_provider|model_reasoning_effort|approval_policy|sandbox_mode|profile)[[:space:]]*=/ {
      line=$0; sub(/^[[:space:]]+/,"",line); print f": "line }' "$cfg" 2>/dev/null | mask | head -n 10)"
  [ -n "$k" ] && CFG_KEYS="$CFG_KEYS$k"$'\n'
  m="$(awk '/^[[:space:]]*\[mcp_servers\./{ s=$0; sub(/^[[:space:]]*\[mcp_servers\./,"",s); sub(/[].].*$/,"",s); print s }' "$cfg" 2>/dev/null | sort -u | tr '\n' ' ')"
  MCP_NAMES="$MCP_NAMES$m"
done
CFG_POLICY=no; printf '%s' "$CFG_KEYS" | grep -Eq ': (model|approval_policy|sandbox_mode)[[:space:]]*=' && CFG_POLICY=yes
CODEX_LS="$(ls "$CODEX_DIR" 2>/dev/null | grep -vE '\.(tmp|bak)|^tmp' | head -n 15 | tr '\n' ' ')"
SESS_N="-"; [ -d "$CODEX_DIR/sessions" ] && SESS_N="$(tmo 2 find "$CODEX_DIR/sessions" -maxdepth 4 -type f 2>/dev/null | head -n 1000 | wc -l | tr -d ' ')개 파일(목록 생략)"

# 에이전트 디렉터리 쓰기
W_AGENTS_HOME="$(wstate "$HOME/.agents")"; W_AGENTS_WS="$(wstate "$CWD/.agents")"
AGENTS_BLOCKED=yes
case "$W_AGENTS_HOME$W_AGENTS_WS" in *"쓰기 가능"*|*"만들 수 있음"*) AGENTS_BLOCKED=no ;; esac

# Git
GIT_REPO="$(pget GIT REPO)"; GIT_GD="$(pget GIT GITDIR)"
GIT_REMOTES="$(pall GITREMOTE | cut -f2- | tr '\t' ' ')"
GIT_REMOTE=0; [ -n "$GIT_REMOTES" ] && GIT_REMOTE=1
GIT_W="-"; [ -n "$GIT_GD" ] && { [ -w "$GIT_GD" ] && [ -w "$GIT_GD/objects" ] && GIT_W=yes || GIT_W=no; }
HX_COMMIT="$(pget HX COMMIT)"; HX_REMOTES="$(pget HX REMOTES)"; HX_REMOTES="${HX_REMOTES% }"

# 데이터
DATA_ROWS="$(pall DATA)"
DATA_N="$(printf '%s\n' "$DATA_ROWS" | grep -c .)"
DATA_BYTES="$(printf '%s\n' "$DATA_ROWS" | awk -F'\t' '{s+=$2} END{printf "%.0f", s+0}')"
DATA_MB="$(awk -v b="$DATA_BYTES" 'BEGIN{printf "%d", b/1048576}')"
DATA_MAX_MB="$(printf '%s\n' "$DATA_ROWS" | awk -F'\t' '$2>m{m=$2} END{printf "%d", (m+0)/1048576}')"

# 병렬 상한 R7
PAR_CAP="${HX_PAR_CAP:-2}"; case "$PAR_CAP" in ''|*[!0-9]*) PAR_CAP=2 ;; esac
PAR_MAX="$(awk -v cap="$PAR_CAP" -v mem="$MEM_EFF_GB" -v np="$NPROC" -v pid="$PIDS_MAX" 'BEGIN{
  m=cap; a=int(mem/3); if (a<m) m=a; b=np-1; if (b<1) b=1; if (b<m) m=b;
  if (pid!="max") { c=int(pid/128); if (c<m) m=c } if (m<1) m=1; print m }')"
THREADS="$(awk -v np="$NPROC" -v p="$PAR_MAX" 'BEGIN{t=int(np/p); if (t<1) t=1; print t}')"

# ---------- 판정 ----------
BLOCK_REASONS=""; PART_REASONS=""
[ "$W_CWD" = no ] && BLOCK_REASONS="${BLOCK_REASONS}작업 폴더 쓰기 불가; "
[ -z "$PYBIN" ] && ! have node && BLOCK_REASONS="${BLOCK_REASONS}python3·node 모두 없음; "
[ -z "$PYBIN" ] && PART_REASONS="${PART_REASONS}python3 없음(Python 스크립트·templates 사용 불가, bash 스크립트만); "
awk -v g="$DISK_GB" 'BEGIN{exit !(g!="" && g<2)}' && PART_REASONS="${PART_REASONS}디스크 여유 ${DISK_GB}GB<2; "
awk -v g="$MEM_EFF_GB" 'BEGIN{exit !(g<2)}' && PART_REASONS="${PART_REASONS}유효 메모리 ${MEM_EFF_GB}GB<2; "
[ "$W_TMP" = no ] && PART_REASONS="${PART_REASONS}/tmp 쓰기 불가; "
[ "$SOCKET" = denied ] && PART_REASONS="${PART_REASONS}0.0.0.0 소켓 불가·미측정; "
[ "$IS_LINUX" = 0 ] && PART_REASONS="${PART_REASONS}Linux 아님; "
[ -n "$PYBIN" ] && [ "$PIP_NET" != ok ] && PART_REASONS="${PART_REASONS}PyPI ${PIP_NET}(패키지 설치 불가·미측정 → stdlib 경로); "
BLOCK_REASONS="${BLOCK_REASONS%; }"; PART_REASONS="${PART_REASONS%; }"
if [ -n "$BLOCK_REASONS" ]; then STATUS=BLOCKED; elif [ -n "$PART_REASONS" ]; then STATUS=PARTIAL; else STATUS=READY; fi

light() { case "$1" in g) printf '🟢' ;; y) printf '🟡' ;; r) printf '🔴' ;; *) printf '⚪' ;; esac; }
if awk -v d="$DISK_GB" -v m="$MEM_EFF_GB" 'BEGIN{exit !((d!="" && d<2) || m<2)}'; then L_RES=r
elif awk -v m="$MEM_EFF_GB" 'BEGIN{exit !(m<4)}'; then L_RES=y; else L_RES=g; fi
if [ -z "$PYBIN" ]; then L_PY=r; elif awk -v v="$PY" 'BEGIN{split(v,a,"."); exit !(a[1]==3 && a[2]<9)}'; then L_PY=y; else L_PY=g; fi
case "$PIP_NET" in ok) L_NET=g ;; blocked) L_NET=r ;; *) L_NET=w ;; esac
[ -n "$CODEX_PATH" ] && L_CODEX=g || L_CODEX=y
if [ "$GIT_REMOTE" = 1 ] || [ -n "$HX_REMOTES" ]; then L_GIT=r; elif [ "$GIT_W" = no ] || [ "$GIT_REPO" != yes ]; then L_GIT=y; else L_GIT=g; fi
[ "${DATA_N:-0}" -gt 0 ] && L_DATA=g || L_DATA=y
case "$SOCKET" in ok) L_SRV=g ;; *) L_SRV=r ;; esac
[ "$TZ_OFF" = "+0900" ] && L_TZ=g || L_TZ=y

GIT_SUMMARY=""
case "$GIT_REPO" in
  yes) GIT_SUMMARY="저장소 · remote $(printf '%s\n' "$GIT_REMOTES" | grep -c .)개 · .git 쓰기 $GIT_W · 미커밋 변경 $(pget GIT DIRTY)건" ;;
  dubious) GIT_SUMMARY="저장소이나 소유자 불일치(dubious ownership) — 설정은 바꾸지 말고 담당자 확인" ;;
  no) GIT_SUMMARY="git 저장소 아님(평가가 git 기록을 쓸 수 있음 → 화면·담당자 확인)" ;;
  *) GIT_SUMMARY="git 명령 없음" ;;
esac
[ -n "$HX_REMOTES" ] && GIT_SUMMARY="$GIT_SUMMARY · 하네스 clone에 remote 남음($HX_REMOTES)"

# ---------- 규칙 R0~R16 ----------
ACT=""; INACT=""
rule() { if [ "$1" = 1 ]; then ACT="$ACT[ACTIVE] $2"$'\n'; else INACT="$INACT[INACTIVE] $2"$'\n'; fi; }
rule 1 "R0 서버는 0.0.0.0에 바인딩(localhost만 바인딩 금지). 작업 환경이 일시정지·재연결될 수 있으니 장시간 프로세스는 재시작 가능하게, 결과는 파일로 남긴다"
rule "$([ "$STATUS" = BLOCKED ] && echo 1)" "R1 종합 BLOCKED(${BLOCK_REASONS:-해당 없음}) → 하네스 스크립트 사용 중지, AGENTS.md 맨 위 '하네스 없이 쓰는 4줄' 블록을 첫 프롬프트로 직접 입력"
R2_WHY=""
[ "$GIT_REMOTE" = 1 ] && R2_WHY="${R2_WHY}워크스페이스 remote 있음($(printf '%s' "$GIT_REMOTES" | head -n 3 | tr '\n' ';' | mdcell 120)); "
[ -n "$HX_REMOTES" ] && R2_WHY="${R2_WHY}하네스 clone에 remote 남음 → README 첫 5분의 하네스 remote 정리 단계를 사람이 수행; "
[ "$GIT_W" = no ] && R2_WHY="${R2_WHY}.git 쓰기 불가 → 에이전트 안에서 커밋이 막힐 수 있음, 커밋은 사람이 IDE 터미널에서 경로를 지정해 하고 작업 기록은 notes/에 파일로 남김; "
rule "$([ -n "$R2_WHY" ] && echo 1)" "R2 Git 안전: ${R2_WHY:-remote 없음·.git 쓰기 가능 → }push·remote 변경 금지, 워크스페이스 remote는 건드리지 않는다(이 스크립트는 경고만)"
R3_ON=""; { [ "$PIP_NET" != ok ] || [ "$HAS_PIP" = no ]; } && R3_ON=1
rule "$R3_ON" "R3 PyPI ${PIP_NET}(${PIP_NOTE})·pip $HAS_PIP → 패키지 설치 시도 금지(pip 포함). 설치된 패키지 안에서만 설계, 템플릿은 stdlib 경로"
R4_ON=""; [ "$PIP_NET" = ok ] && [ "$VENV_OK" = yes ] && R4_ON=1
rule "$R4_ON" "R4 PyPI $PIP_NET·venv $VENV_OK${UV_NOTE:-}${PIP_EM_NOTE} → 꼭 필요할 때만 사람 승인 후 워크스페이스 venv에 설치하고 requirements.txt에 기록. 전역·시스템 설치, 시스템 패키지 보호 무시 옵션 금지"
if [ -z "$PYBIN" ]; then
  rule 0 "R5 python3 없음 → pandas·sklearn·templates 해당 없음(R17)"
elif [ "$PANDAS" != none ] || [ "$SKLEARN" != none ]; then
  rule 1 "R5 pandas=$PANDAS sklearn=$SKLEARN → 있는 패키지 경로 허용(ml 템플릿의 sklearn 기준선), 없는 쪽은 stdlib 폴백"
else
  rule 1 "R5 pandas·sklearn 없음 → stdlib 기준선(templates의 stdlib 경로)만"
fi
rule "$([ "$GPU" = 0 ] && echo 1)" "R6 GPU=$GPU → 딥러닝 학습 제외, 규칙·통계·HGB/선형 모델"
rule 1 "R7 PAR_MAX=$PAR_MAX(=min(상한 $PAR_CAP, 메모리 ${MEM_EFF_GB}GB/3, NPROC $NPROC-1, PIDS $PIDS_MAX/128)) → 병렬 시행 최대 ${PAR_MAX}개, 시행마다 OMP_NUM_THREADS·n_jobs=$THREADS"
rule "$([ "$SOCKET" != ok ] && echo 1)" "R8 소켓: $SOCKET_NOTE → 서버는 사람이 IDE 터미널에서 0.0.0.0:\$PORT로 실행, 코드는 결과 파일로도 검증 가능하게"
ISO_Z="$(pget PY ISO_Z)"
R9_ON=""; [ "$PY" != none ] && { [ "$ISO_Z" != ok ] || awk -v v="$PY" 'BEGIN{split(v,a,"."); exit !(a[1]==3 && a[2]<11)}'; } && R9_ON=1
rule "$R9_ON" "R9 Python $PY·fromisoformat('…Z') ${ISO_Z:-N/A} → 타임스탬프 파싱은 templates/_common.py의 parse_ts 사용"
R10_ON=""; awk -v t="$DATA_MB" -v x="$DATA_MAX_MB" -v m="$MEM_EFF_GB" 'BEGIN{exit !(t>=1024 || (m>0 && x*4>=m*1024))}' && R10_ON=1
rule "$R10_ON" "R10 데이터 총 ${DATA_MB}MB·최대 파일 ${DATA_MAX_MB}MB(유효 메모리 ${MEM_EFF_GB}GB) → 통째 로드 금지, scripts/profile_data.py 스트리밍·샘플링 우선"
R11_ON=""; { [ "$W_TMP" = no ] || awk -v g="$DISK_GB" 'BEGIN{exit !(g!="" && g<2)}'; } && R11_ON=1
rule "$R11_ON" "R11 디스크 여유 ${DISK_GB:-?}GB·/tmp 쓰기 $W_TMP → 중간 산출물 최소화, 하네스는 워크스페이스 하위 경로(_harness)로"
rule 1 "R12 병렬 방법은 Codex 기본 서브에이전트·사람이 연 추가 터미널·파이썬 실험 스크립트만. codex exec 백그라운드 병렬은 쓰지 않음(CODEX_EXEC=$CODEX_EXEC는 기록만)"
R13_ON=""; R13_TXT="표시값 미입력(HX_DISPLAY_MEM=16G 처럼 주고 다시 실행 가능)"
if [ -n "$DISP_MEM_GB" ]; then
  meas="$(minnum "$MEM_TOTAL_GB" "$CG_MEM_GB")"
  R13_TXT="표시 ${DISP_MEM_GB}GB vs 실측 ${meas:-?}GB"
  awk -v d="$DISP_MEM_GB" -v m="$meas" 'BEGIN{exit !(m!="" && d>0 && ((d-m)/d>0.2 || (m-d)/d>0.2))}' && R13_ON=1
fi
rule "$R13_ON" "R13 $R13_TXT → 차이 20% 초과면 모든 계산에 유효값(작은 값) ${MEM_EFF_GB}GB 사용"
rule "$([ "$CFG_POLICY" = yes ] && echo 1)" "R14 Codex config의 model·approval·sandbox 키: $CFG_POLICY → 보고만, 수정 금지. 모델은 사람이 /model로"
rule "$([ "$AGENTS_BLOCKED" = yes ] && echo 1)" "R15 ~/.agents: $W_AGENTS_HOME, ./.agents: $W_AGENTS_WS → 쓰기 불가면 스킬 복사 생략, 하네스 경로를 직접 읽기"
R16_MARK=""; [ "$TZ_OFF" != "+0900" ] && R16_MARK="🟡 컨테이너 TZ $TZ_OFF ≠ +0900! "
rule 1 "R16 ${R16_MARK}모든 시각 계산은 TZ=$KST_TZ로. 마감은 화면 타이머 잔여 분(init_state.sh --remaining-min, hx-next에 '잔여 m분')이 1순위, 시계 계산은 확인용. 13:20 비교도 KST로"

rule "$([ -z "$PYBIN" ] && echo 1)" "R17 python3 없음 → Python 도구 사용 불가: scripts/verdict.py·presubmit.py·profile_data.py와 templates/ 전부. 남는 하네스는 bash 스크립트(env_check.sh·init_state.sh·run_and_log.sh)와 문서·스킬뿐. 판정은 실행한 명령+출력+exit code를 DECISIONS §3에 직접 적고, 구현은 설치된 언어(node 등)로. 막히면 AGENTS.md 맨 위 4줄만"

# ---------- 출력 ----------
ELAPSED_MS=$(( $(now_ms) - T_START ))
MODE="standard"; [ "$QUICK" = 1 ] && MODE="quick"; [ "$NET" = 0 ] && [ "$QUICK" = 0 ] && MODE="standard(no-network)"
[ "$PIP_PROBE" = 1 ] && [ "$NET" = 1 ] && MODE="$MODE+pip-probe"
TAIL="<!-- hx-env $VERSION: STATUS=$STATUS PY=$PY PIP_NET=$PIP_NET PANDAS=$PANDAS SKLEARN=$SKLEARN GPU=$GPU NPROC=$NPROC MEM_EFF_GB=$MEM_EFF_GB PIDS_MAX=$PIDS_MAX PAR_MAX=$PAR_MAX SOCKET=$SOCKET CODEX_EXEC=$CODEX_EXEC GIT_REMOTE=$GIT_REMOTE DATA_MB=$DATA_MB TZ_OFF=$TZ_OFF CGROUP=$CGROUP -->"

relpath() { case "$1" in "$CWD"/*) echo "./${1#"$CWD"/}" ;; *) echo "$1" ;; esac; }
NA_PY="N/A(python 없음)"

render() {
  echo "# ENVIRONMENT.md (env_check.sh 자동 생성 — 커밋하지 않음)"
  echo "> 생성 $KST_NOW | 컨테이너 시계 $LOCAL_NOW (TZ=${TZ:-미설정}) | 소요 $((ELAPSED_MS / 1000)).$(( (ELAPSED_MS % 1000) / 100 ))초 | 모드 $MODE | 호스트 해시 $HOSTHASH | 하네스 ${HX_COMMIT} ($H)"
  echo
  echo "STATUS: $STATUS"
  echo "판정 기준: BLOCKED=작업 폴더 쓰기 불가 또는 python3·node 모두 없음 / PARTIAL=python3 없음(R17: Python 도구 사용 불가)·디스크<2GB·유효 메모리<2GB·/tmp 쓰기 불가·0.0.0.0 소켓 불가·비 Linux·PyPI 차단/미측정 중 하나 / 그 외 READY. 이유: ${BLOCK_REASONS:+$BLOCK_REASONS; }${PART_REASONS:-없음}"
  echo
  echo "## 1. 종합 판정"
  echo "| 영역 | 상태 | 요약 |"
  echo "|---|:---:|---|"
  echo "| 자원 | $(light $L_RES) | CPU $NPROC코어(유효) · 메모리 유효 ${MEM_EFF_GB}GB · GPU $GPU · 디스크 여유 ${DISK_GB:-?}GB |"
  echo "| Python·패키지 | $(light $L_PY) | Python ${PY_VER:-없음} · numpy $NUMPY · pandas $PANDAS · sklearn $SKLEARN · pip $HAS_PIP · venv $VENV_OK${UV_NOTE:-} |"
  echo "| 네트워크 | $(light $L_NET) | PIP_NET=$PIP_NET ($(printf '%s' "$PIP_NOTE" | mdcell 120)) |"
  echo "| Codex | $(light $L_CODEX) | ${CODEX_PATH:-codex 없음} ${CODEX_VER} · exec 서브커맨드 $CODEX_EXEC(기록만) |"
  echo "| Git 안전 | $(light $L_GIT) | $(printf '%s' "$GIT_SUMMARY" | mdcell 200) |"
  echo "| 데이터 | $(light $L_DATA) | 후보 ${DATA_N:-0}개 · 총 ${DATA_MB}MB · 최대 ${DATA_MAX_MB}MB$( [ "$QUICK" = 1 ] && echo ' (--quick: 얕게 탐색)') |"
  echo "| 서버 | $(light $L_SRV) | $SOCKET_NOTE · 127.0.0.1: ${B1:-$NA_PY} |"
  echo "| 시간 | $(light $L_TZ) | 컨테이너 TZ 오프셋 $TZ_OFF · KST 계산은 TZ=$KST_TZ |"
  echo
  echo "## 2. 판정 규칙 (ACTIVE 먼저; 에이전트는 [ACTIVE] 줄을 작업 규칙으로 따른다)"
  printf '%s' "$ACT"
  printf '%s' "$INACT"
  echo
  echo "## 3. 표시값 vs 실측 (cgroup $CGROUP${CG_DIR:+, $CG_DIR})"
  echo "| 항목 | 화면 표시(사람 입력) | /proc·OS | cgroup | 유효값 |"
  echo "|---|---|---|---|---|"
  echo "| 메모리 GB | ${DISP_MEM_GB:-미입력(HX_DISPLAY_MEM)} | 총 ${MEM_TOTAL_GB:-?} / 가용 ${MEM_AVAIL_GB:-?} | ${CG_MEM_GB:-${CG_MEM:-없음}} | **$MEM_EFF_GB** |"
  echo "| CPU | ${DISP_CPU:-미입력(HX_DISPLAY_CPU)} | nproc $NPROC_RAW | ${CG_CPU:-제한 없음} | **$NPROC** |"
  echo "| 프로세스 한도 | - | ulimit -u ${ULIM_U:-?} | pids.max ${CG_PIDS:-없음} | **$PIDS_MAX** |"
  echo "| 디스크 여유 GB | - | . ${DISK_GB:-?} · /tmp ${TMP_GB:-?} | - | **${DISK_GB:-?}** |"
  echo "| inode(.) | - | ${INODE:-?} | - | - |"
  echo
  echo "## 4. 서술형용 환경 사실 3줄"
  echo "- 실행 환경은 ${OS_NAME}, CPU ${NPROC}코어(cgroup 기준)·메모리 유효 ${MEM_EFF_GB}GB${DISP_MEM_GB:+(화면 표시 ${DISP_MEM_GB}GB)}·GPU $( [ "$GPU" = 0 ] && echo 없음 || echo "${GPU}개")·디스크 여유 ${DISK_GB:-?}GB였다."
  echo "- Python ${PY_VER:-없음}, pandas ${PANDAS}·scikit-learn ${SKLEARN}, PyPI ${PIP_NET} → $( [ "$PIP_NET" = ok ] && echo '필요 시에만 워크스페이스 venv 설치' || echo '추가 설치 없이 설치된 패키지·표준 라이브러리로 구현')$( [ "$GPU" = 0 ] && echo ', 딥러닝 대신 통계·트리 모델')."
  echo "- 병렬 시행 상한 ${PAR_MAX}개(메모리·코어·프로세스 한도 기준, 시행당 스레드 ${THREADS}), 서버 0.0.0.0 바인딩 ${SOCKET}, 데이터 후보 ${DATA_N:-0}개 총 ${DATA_MB}MB."
  echo
  echo "## 5. 상세"
  echo "### 5.1 OS·시계·사용자"
  echo "- OS: $OS_NAME · 커널 $OS_KERNEL · 컨테이너 단서: $CONTAINER"
  echo "- 시계: $UTC_NOW · 로컬 $LOCAL_NOW · KST $KST_NOW · \$TZ=${TZ:-미설정} · /etc/timezone=${TZ_FILE:-없음} · /etc/localtime=${LOCALTIME:-없음} · TZ=Asia/Seoul 동작 $( [ "$KST_TZ" = Asia/Seoul ] && echo yes || echo 'no(tzdata 없음 → TZ=KST-9 사용)')"
  echo "- 사용자: ${USER_NAME:-?}(uid ${USER_ID:-?}, root $( [ "$USER_ID" = 0 ] && echo yes || echo no)) · 그룹: ${USER_GROUPS:-?} · 관리자 권한 도구 $( [ -n "$SUDO_BIN" ] && echo '있음' || echo '없음')(실행 시험 안 함, 시스템 변경 금지) · 관리자 그룹 $ADMIN_GRP · HOME=$HOME · SHELL=${SHELL:-?}"
  echo "- 패키지 관리자: ${APT_PRESENT:-없음}(존재만, 쓰지 않음) · 읽기 전용 마운트: ${RO_MOUNTS:-없음}"
  echo "- GPU: $GPU_INFO"
  echo
  echo "### 5.2 런타임"
  echo "| 이름 | 경로 | 버전 |"
  echo "|---|---|---|"
  pall VER | sort -t "	" -k2,2 | awk -F'\t' '$3!="-"{print "| "$2" | "$3" | "$4" |"}'
  echo "- 없음: $(pall VER | awk -F'\t' '$3=="-"{printf "%s ", $2}')"
  if [ -n "$PYBIN" ]; then echo "- venv 모듈 $(pget PY VENV_MOD)·ensurepip $(pget PY ENSUREPIP) · 현재 venv 안 $(pget PY IN_VENV) · EXTERNALLY-MANAGED $(pget PY EXT_MANAGED)(yes면 전역 설치 막힘 → venv만)"
  else echo "- venv·pip: $NA_PY"; fi
  [ "$QUICK" = 0 ] && echo "- pip 캐시: $(pget WHEEL CACHE) · 홈·/opt의 .whl: $(pget WHEEL COUNT)개"
  echo
  echo "### 5.3 Python 패키지"
  if [ -z "$PYBIN" ]; then echo "$NA_PY"
  else
    echo "$(pall PKG | awk -F'\t' '{printf "%s=%s · ", $2, $3}')"
    echo "- fromisoformat('…Z'): ${ISO_Z:-?} · 실행 파일 $(pget PY EXE)"
    [ "$QUICK" = 1 ] && echo "- (--quick: numpy·pandas·sklearn만 조회)"
  fi
  echo
  echo "### 5.4 네트워크"
  echo "- 프록시·미러 환경변수(비밀값 ***):"
  env | grep -E '^(HTTPS?_PROXY|NO_PROXY|ALL_PROXY|https?_proxy|no_proxy|all_proxy|PIP_[A-Z_]+|NPM_CONFIG_[A-Z_]+|npm_config_[a-z_]+|UV_[A-Z_]+|CONDA_[A-Z_]+|SSL_CERT_[A-Z_]+|REQUESTS_CA_BUNDLE|CURL_CA_BUNDLE|NODE_EXTRA_CA_CERTS|CODEX_HOME|VIRTUAL_ENV)=' 2>/dev/null \
    | sort | while IFS= read -r line; do
        n="${line%%=*}"; v="${line#*=}"
        if printf '%s' "$n" | grep -qiE "$SECRET_RE"; then v="***"; else v="$(printf '%s' "$v" | mask | mdcell 120)"; fi
        echo "  - \`$n=$v\`"
      done
  echo "- 미러 설정 파일(키 이름만): $(for f in "$HOME/.pip/pip.conf" "$HOME/.config/pip/pip.conf" /etc/pip.conf "$HOME/.npmrc" /etc/npmrc "$HOME/.condarc" "$HOME/.config/uv/uv.toml"; do [ -r "$f" ] && printf '%s[%s] ' "$f" "$(sed -n 's/^[[:space:]]*\([A-Za-z0-9_.@:/-]*\)[[:space:]]*=.*/\1/p' "$f" 2>/dev/null | head -n 8 | sed -E "s#^//.*#(registry 자격 줄)#" | tr '\n' ',')"; done)"
  if [ "$NET" = 0 ]; then echo "- HTTP 점검: 생략(--no-network/--quick)"
  else
    echo "| 대상(HEAD ${NET_T}초) | HTTP | ms |"
    echo "|---|---|---|"
    printf '%s\n' "$NET_ROWS" | awk -F'\t' 'NF>=3{print "| "$2" | "$3" | "$4" |"}'
    [ -n "$(pall NETTOOL)" ] && echo "- HTTP 점검 도구 없음(curl·python·wget)"
    echo "- DNS: $(pall DNS | awk -F'\t' '{printf "%s→%s ", $2, $3}')"
    if [ "$PIP_PROBE" = 1 ]; then echo "- pip dry-run(six, 설치 없음): rc=${PIPDRY_RC_RAW:-미실행} ${PIPDRY_MSG}"
    else echo "- pip dry-run: 실행 안 함(기본). PyPI 판정은 HEAD 응답 기준. 설치 가능성까지 보려면 사람이 --pip-probe로 다시 실행"; fi
    echo "- 판정: 000=응답 없음/차단, 403·407=프록시·필터 차단 가능. TCP 연결 성공만으로는 허용이 아님"
  fi
  echo
  echo "### 5.5 Codex"
  echo "- 경로 ${CODEX_PATH:-없음} · 버전 ${CODEX_VER:--} · 서브커맨드: $(pall CODEX | awk -F'\t' '$2=="SUB"{printf "%s=%s ", $3, $4}')"
  echo "- CODEX_HOME=${CODEX_HOME:-미설정} · $CODEX_DIR: ${CODEX_LS:-없음}"
  echo "- config 키(값 마스킹, 보고만):"
  if [ -n "$CFG_KEYS" ]; then printf '%s' "$CFG_KEYS" | sed 's/^/  - /'; else echo "  - (config.toml 없음 또는 해당 키 없음)"; fi
  echo "- mcp_servers: ${MCP_NAMES:-없음} · sessions: $SESS_N"
  echo "- 스킬·규칙 경로: ~/.codex/skills $( [ -d "$CODEX_DIR/skills" ] && echo 있음 || echo 없음) · ~/.agents/skills $( [ -d "$HOME/.agents/skills" ] && echo 있음 || echo 없음) · ./AGENTS.md $( [ -f "$CWD/AGENTS.md" ] && echo 있음 || echo 없음) · ~/.codex/AGENTS.md $( [ -f "$CODEX_DIR/AGENTS.md" ] && echo 있음 || echo 없음)"
  echo
  echo "### 5.6 워크스페이스·쓰기·git"
  echo "- pwd -P: $CWD · HOME: $HOME"
  echo "| 경로 | 상태 |"
  echo "|---|---|"
  for p in "$CWD" /tmp "$HOME" "${GIT_GD:-$CWD/.git}" "$CWD/.codex" "$CWD/.agents" "$CODEX_DIR" "$HOME/.agents"; do echo "| $p | $(wstate "$p") |"; done
  echo "- 루트 문서: $(tmo 2 find "$CWD" -maxdepth 2 \( -path "$CWD/*" -name '.*' -o -name node_modules -o -name _harness -o -name notes \) -prune -o -type f \( -iname 'README*' -o -iname 'PROBLEM*' -o -iname 'TASK*' -o -iname '*.md' \) -print 2>/dev/null | grep -v '/ENVIRONMENT.md$' | head -n 20 | while IFS= read -r f; do printf '%s ' "$(relpath "$f")"; done)"
  echo "- git: $GIT_SUMMARY"
  if [ "$GIT_REPO" = yes ]; then
    echo "  - top $(pget GIT TOP) · branch $(pget GIT BRANCH) · HEAD $(pget GIT HEAD) · user.name $(pget GIT USER) · hooks: $(pget GIT HOOKS)"
    echo "  - remote(자격 마스킹): $( [ -n "$GIT_REMOTES" ] && printf '%s' "$GIT_REMOTES" | tr '\n' ';' || echo 없음)"
  fi
  echo "- 하네스: $H · 커밋 $HX_COMMIT · remote: ${HX_REMOTES:-없음}"
  echo
  echo "### 5.7 데이터 후보 (탐색: $(pall DDIR | cut -f2 | tr '\n' ' '))"
  if [ "${DATA_N:-0}" = 0 ]; then echo "- 없음(확장자: $DATA_EXT). 다른 위치면 --data-dir로 다시 실행"
  else
    echo "| 경로 | 크기 | 줄 수 | 앞 2줄(50MB 이하·처음 10개) |"
    echo "|---|---|---|---|"
    printf '%s\n' "$DATA_ROWS" | sort -t "	" -k2,2nr | head -n 30 | while IFS="	" read -r _ sz f ln hd; do
      echo "| $(relpath "$f" | mdcell 100) | $(awk -v b="$sz" 'BEGIN{ if (b>=1048576) printf "%.1fMB", b/1048576; else printf "%.1fKB", b/1024 }') | $ln | $hd |"
    done
    [ "$DATA_N" -gt 30 ] && echo "- … 외 $((DATA_N - 30))개"
  fi
  echo
  echo "### 5.8 한도·소켓·포트"
  echo "- ulimit: -n ${ULIM_N:-?} · -u ${ULIM_U:-?} · -v ${ULIM_V:-?} · -s ${ULIM_S:-?} · pids.max ${CG_PIDS:-없음}"
  echo "- 소켓 바인드: 127.0.0.1 ${B1:-$NA_PY} · 0.0.0.0 ${B0:-미측정}"
  echo "- 열린 포트(읽기 전용 조회): $(pall PORT | cut -f2 | tr '\n' ' ')"
  echo "- 미리보기 관련 env 키(이름만): $(env | cut -d= -f1 | grep -E 'VSCODE|CODE_SERVER|OPENVSCODE|COFA|E2B|PORT|PREVIEW|WEB_HOST|JUPYTER' | sort -u | head -n 15 | tr '\n' ' ')"
  echo
  if [ -n "$DIFF_FILE" ]; then
    echo "## 6. 바뀐 항목 (--diff $DIFF_FILE)"
    if [ ! -r "$DIFF_FILE" ]; then echo "- 이전 파일을 읽을 수 없음"
    else
      old="$(grep -o '<!-- hx-env v1: .* -->' "$DIFF_FILE" | tail -n 1)"
      if [ -z "$old" ]; then echo "- 이전 파일에 hx-env 꼬리표가 없음"
      else
        changed=0
        for kv in $(printf '%s' "$TAIL" | sed -e 's/^<!-- hx-env v1: //' -e 's/ -->$//'); do
          k="${kv%%=*}"; v="${kv#*=}"
          ov="$(printf '%s' "$old" | tr ' ' '\n' | sed -n "s/^$k=//p" | head -n 1)"
          if [ "$ov" != "$v" ]; then echo "- $k: ${ov:-(없음)} → $v"; changed=$((changed + 1)); fi
        done
        [ "$changed" = 0 ] && echo "- 꼬리표 기준 바뀐 항목 없음"
      fi
    fi
    echo
  fi
  echo "## 7. 사람 전용 체크리스트 (스크립트로 알 수 없음)"
  echo "- [ ] 화면 상단 메모리 표시값(예: 16G)을 HX_DISPLAY_MEM으로 주고 다시 실행했나"
  echo "- [ ] 에디터↔터미널·외부↔IDE 복사/붙여넣기 단축키(예: Ctrl+Shift+V) 동작"
  echo "- [ ] 전체화면 이탈 시 경고·제재 여부"
  echo "- [ ] codex 안에서 /status·/model로 허용 모델·승인 모드 확인(제한 모델이 기본값이면 사람이 바꿈)"
  echo "- [ ] 0.0.0.0:PORT로 띄운 서버가 Browser 미리보기에서 열리는지, 쓸 수 있는 포트 범위"
  echo "- [ ] 제출 버튼 위치·제출 형식·경로, 다운로드/내보내기 UI"
  echo "- [ ] 담당자 메신저 위치와 질문 방법"
  echo "- [ ] 제한 모델 호출 시 차단 방식(시스템 차단인지 사후 감점인지)"
  echo "- [ ] Codex 승인 창 빈도(하네스 경로 읽기에 승인이 반복되면 _harness로 옮김)"
  echo "- [ ] 화면·/status의 토큰 사용량 표시 위치"
  echo
  echo "$TAIL"
}

DOC="$(render)"
if [ "$TO_STDOUT" = 1 ]; then
  printf '%s\n' "$DOC"
else
  if { printf '%s\n' "$DOC" >"$OUT"; } 2>/dev/null; then
    echo "STATUS: $STATUS  → $OUT ($((ELAPSED_MS / 1000)).$(( (ELAPSED_MS % 1000) / 100 ))초)"
    printf '%s' "$ACT" | while IFS= read -r l; do printf '%s\n' "$l" | mdcell 160; done
  else
    echo "출력 파일을 쓸 수 없음: $OUT — 표준 출력으로 보냄(--stdout과 같음)" >&2
    printf '%s\n' "$DOC"
    exit 1
  fi
fi
exit 0
