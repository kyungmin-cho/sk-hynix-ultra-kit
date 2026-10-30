#!/usr/bin/env bash
# run_and_log.sh — 명령 하나를 실행하고 그 증거(명령·cwd·시작/끝 시각·exit code·출력)를 logs/에 남긴다.
# 차용 없음(wildrage98/hackathon-kit run_and_log.sh의 "실행 증거 로그" 아이디어만 참고, 코드는 새로 씀).
#
# 사용: bash <H>/scripts/run_and_log.sh [--dir logs] <태그> -- <명령...>
#   예: bash <H>/scripts/run_and_log.sh e2e -- python3 main.py --input data/x.csv
#       환경 변수는 명령 앞에: run_and_log.sh t1 -- OMP_NUM_THREADS=2 python3 train.py
#   로그: <dir>/<YYYYmmdd-HHMMSS KST>_<태그>.log (기본 dir = 현재 디렉터리의 logs)
#   출력은 화면에도 그대로 나온다. 종료 코드는 명령의 종료 코드를 그대로 돌려준다.
#   INT/TERM/HUP을 받으면 명령(과 그 자식)을 멈추고 끝 줄에 사유를 적는다(exit 130/143/129).
#   로그에 "# end:" 줄이 없으면 비정상 종료(SIGKILL·OOM·환경 중단)로 본다.
# 머리 줄은 명령 실행 전에 먼저 쓴다. PYTHONUNBUFFERED=1. git·설치·네트워크 없음.
set -u

DIR="logs"
usage() { sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; }

case "${1:-}" in -h|--help) usage; exit 0 ;; esac
if [ "${1:-}" = "--dir" ]; then DIR="${2:-}"; shift 2 || { usage >&2; exit 2; }; fi
TAG="${1:-}"
if [ -z "$TAG" ] || [ "${2:-}" != "--" ] || [ $# -lt 3 ]; then
  echo "usage: run_and_log.sh [--dir logs] <tag> -- <command...>" >&2; exit 2
fi
shift 2
# 파일 이름에 문제 되는 문자(/·공백·제어문자·특수문자)만 _로. 한글은 그대로 둔다.
TAG=$(printf '%s' "$TAG" | LC_ALL=C sed 's#[][/[:space:][:cntrl:]\\:*?"<>|$`'"'"'&;(){}]#_#g')

# tzdata가 없으면 TZ=Asia/Seoul이 조용히 UTC가 되므로 POSIX 표기(KST-9)로 대체
KTZ=Asia/Seoul; [ "$(TZ=Asia/Seoul date +%z)" = "+0900" ] || KTZ=KST-9
kst() { TZ=$KTZ date "+%Y-%m-%d %H:%M:%S KST"; }

mkdir -p "$DIR" || { echo "cannot create $DIR" >&2; exit 2; }
LOG="$DIR/$(TZ=$KTZ date +%Y%m%d-%H%M%S)_${TAG}.log"
[ -e "$LOG" ] && LOG="${LOG%.log}_$$.log"

CMD=""; for a in "$@"; do CMD="$CMD $(printf '%q' "$a")"; done
{
  echo "# cmd:${CMD}"
  echo "# cwd: $(pwd -P)"
  echo "# start: $(kst)"
  echo "# log: $LOG"
} > "$LOG" || { echo "cannot write $LOG" >&2; exit 2; }
START_S=$(date +%s)

# 출력은 fd 3 → tee 한 줄기로만 보낸다(끝 줄도 같은 줄기로 써서 순서가 섞이지 않게).
exec 3> >(tee -i -a "$LOG")
TEE_PID=$!

CHILD=""
finish() {  # $1 = exit code, $2 = 사유
  local el=$(( $(date +%s) - START_S ))
  echo "# end: $(kst) | exit=$1 | ${el}s${2:+ | $2}" >&3
  exec 3>&-
  # tee가 마지막 줄까지 쓰고 끝날 때까지 잠깐 기다린다(최대 약 3초). 손자가 파이프를 잡고 있으면 tee를 끝낸다.
  if [ -n "$TEE_PID" ]; then
    for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
      kill -0 "$TEE_PID" 2>/dev/null || break; sleep 0.1
    done
    kill "$TEE_PID" 2>/dev/null
  fi
  exit "$1"
}
on_signal() {  # $1 = 신호 이름, $2 = exit code
  trap '' INT TERM HUP
  if [ -n "$CHILD" ]; then
    command -v pkill >/dev/null 2>&1 && pkill -TERM -P "$CHILD" 2>/dev/null  # 자식의 자식(손자)도
    kill -TERM "$CHILD" 2>/dev/null
    wait "$CHILD" 2>/dev/null
  fi
  finish "$2" "signal $1"
}
trap 'on_signal INT 130' INT
trap 'on_signal TERM 143' TERM
trap 'on_signal HUP 129' HUP

exec 4<&0   # 백그라운드 실행은 stdin이 /dev/null이 되므로 원래 stdin을 넘겨준다
env PYTHONUNBUFFERED=1 "$@" <&4 >&3 2>&3 4<&- &   # env: "VAR=값 명령" 형태도 받는다
CHILD=$!
wait "$CHILD"
RC=$?
CHILD=""
finish "$RC" ""
