#!/usr/bin/env bash
# init_state.sh — 워크스페이스에 notes/ 상태 파일을 "없는 것만" 만든다. 기존 파일은 절대 덮어쓰지 않는다.
# 차용 없음.
#
# 사용: bash <H>/scripts/init_state.sh [워크스페이스(기본 .)] [--dest notes] [--remaining-min N] [--start|--t0 HH:MM] [--extra | --with LIST]
#   --dest DIR          상태 폴더(기본 notes, 워크스페이스 기준)
#   --remaining-min N   화면 타이머 잔여 분(1순위). D = 지금 + N(화면 값 그대로), T0 = D - 180
#   --start HH:MM       과제 시작 시각 KST(2순위, --t0 같음). D = min(T0 + 180, 13:20)
#   (둘 다 없으면 T0 = 지금)
#   13:20 = 서술형 여유를 둔 권장 마감 D'(하네스 해석, 공식 아님). 화면 기준 D가 더 늦으면 깎지 않고 경고만
#   기본은 핵심 4개(TASK STATE DECISIONS HANDOFF). 추가 양식은 선택:
#   --extra             TRIALS VERIFICATION ESSAY_PREP 모두 추가
#   --with LIST         쉼표 목록 중 골라 추가: trials,verification,essay
#   (다시 실행해도 있는 파일은 skip. 추가 양식만 나중에 더해도 된다)
# 시각은 전부 TZ=Asia/Seoul. git 쓰기·설치·네트워크 없음.
set -u

H="$(cd "$(dirname "$0")/.." && pwd)"
DEST="notes"
REMAIN=""
START=""
WITH=""

usage() { awk 'NR>1 && /^#/ { sub(/^# ?/, ""); print; next } NR>1 { exit }' "$0"; }

WS=""
# 값이 필요한 옵션: 값이 없거나 다음 옵션이면 바로 오류(shift 2 실패로 무한 반복하지 않게)
need() { if [ "$2" -lt 2 ] || [ -z "$3" ] || [ "${3#--}" != "$3" ]; then echo "$1 needs a value" >&2; usage >&2; exit 2; fi; }
while [ $# -gt 0 ]; do
  case "$1" in
    --dest) need "$1" $# "${2:-}"; DEST="$2"; shift 2 ;;
    --remaining-min) need "$1" $# "${2:-}"; REMAIN="$2"; shift 2 ;;
    --start|--t0) need "$1" $# "${2:-}"; START="$2"; shift 2 ;;
    --extra) WITH="trials,verification,essay"; shift ;;
    --with) need "$1" $# "${2:-}"; WITH="${WITH:+$WITH,}$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) [ -z "$WS" ] || { echo "only one workspace path: $1" >&2; exit 2; }; WS="$1"; shift ;;
  esac
done
if [ -n "$WS" ]; then cd "$WS" 2>/dev/null || { echo "cannot cd to workspace: $WS" >&2; exit 2; }; fi

if [ -n "$REMAIN" ] && ! printf '%s' "$REMAIN" | grep -Eq '^[0-9]+$'; then
  echo "--remaining-min must be an integer" >&2; exit 2
fi
if [ -n "$REMAIN" ] && [ "$((10#$REMAIN))" -gt 180 ]; then
  echo "--remaining-min must be <= 180 (screen timer minutes)" >&2; exit 2
fi
if [ -n "$START" ] && ! printf '%s' "$START" | grep -Eq '^([01]?[0-9]|2[0-3]):[0-5][0-9]$'; then
  echo "--start must be HH:MM (KST, 00:00-23:59)" >&2; exit 2
fi

EXTRA=""
for w in $(printf '%s' "$WITH" | tr ',' ' '); do
  case "$w" in
    trials) n=TRIALS ;; verification) n=VERIFICATION ;; essay) n=ESSAY_PREP ;;
    *) echo "--with: unknown '$w' (trials,verification,essay)" >&2; exit 2 ;;
  esac
  case " $EXTRA " in *" $n "*) ;; *) EXTRA="$EXTRA $n" ;; esac
done

CAP=800   # 13:20 KST = 800분
# tzdata가 없으면 TZ=Asia/Seoul이 조용히 UTC가 되므로 POSIX 표기(KST-9)로 대체
KTZ=Asia/Seoul; [ "$(TZ=Asia/Seoul date +%z)" = "+0900" ] || KTZ=KST-9
now_h=$(TZ=$KTZ date +%H); now_m=$(TZ=$KTZ date +%M)
NOW=$(( 10#$now_h * 60 + 10#$now_m ))

fmt() { local v=$(( ($1 % 1440 + 1440) % 1440 )); printf '%02d:%02d' $(( v / 60 )) $(( v % 60 )); }
# 13:20 상한은 T0가 13:20 이전일 때만(본 시험). 밤 리허설 등 T0가 그 뒤면 상한 없이 T0+180.
cap() { if [ "$1" -le $CAP ] && [ "$2" -gt $CAP ]; then echo $CAP; else echo "$2"; fi; }

if [ -n "$REMAIN" ]; then
  R=$(( 10#$REMAIN ))
  D=$(( NOW + R ))          # 화면 값이 1순위: 상한으로 깎지 않는다
  T0=$(( D - 180 ))         # R <= 180이므로 T0 <= 지금(미래가 되지 않음)
  SRC="잔여 ${R}분 입력"
elif [ -n "$START" ]; then
  T0=$(( 10#${START%%:*} * 60 + 10#${START##*:} ))
  D=$(cap $T0 $(( T0 + 180 )))
  SRC="--start 입력"
else
  T0=$NOW
  D=$(cap $T0 $(( T0 + 180 )))
  SRC="입력 없음(지금=T0), 화면 잔여 분으로 다시 확인"
fi
LEFT=$(( D - NOW ))
WARN=""
if [ "$T0" -le $CAP ] && [ "$D" -gt $CAP ]; then
  CAP_NOTE="13:20 (주의: 화면 기준 D $(fmt $D)가 더 늦다. 서술형 시간을 사람이 확인)"
  WARN="WARN: D $(fmt $D)(화면 기준)가 권장 마감 13:20보다 늦다 — 그대로 기록함, 서술형 시간은 사람이 확인"
else
  CAP_NOTE="13:20 (D가 이보다 늦지 않음)"
fi
if [ "$LEFT" -le 0 ]; then
  WARN="${WARN:+$WARN
}WARN: 잔여 ${LEFT}분 — 마감이 지났다. 화면 타이머를 보고 --remaining-min으로 다시 계산(notes/STATE.md를 지우고 재실행)"
fi

COMMIT="unknown"
if command -v git >/dev/null 2>&1; then
  c=$(git -C "$H" rev-parse HEAD 2>/dev/null) && [ -n "$c" ] && COMMIT="$c"
fi
# 워크스페이스 시작 커밋(BASE): presubmit --base로 이력 스캔을 이번 작업분으로 줄인다. 읽기만 한다.
BASE="none(커밋 없음·git 없음 → presubmit은 전체 이력)"
if command -v git >/dev/null 2>&1; then
  b=$(GIT_OPTIONAL_LOCKS=0 git rev-parse HEAD 2>/dev/null) && [ -n "$b" ] && BASE="$b"
fi
CTZ="TZ=${TZ:-unset}, date=$(date +%Z%z 2>/dev/null)"

mkdir -p "$DEST" || { echo "cannot create $DEST" >&2; exit 1; }

# T+n 체크포인트가 D−30 이후로 밀리면(늦은 시작·13:20 상한) 순서가 뒤집히므로 생략 표시
cp() { if [ "$1" -ge $(( D - 30 )) ]; then printf '%s(생략: D−30 이후)' "$(fmt "$1")"; else fmt "$1"; fi; }
esc() { printf '%s' "$1" | sed -e 's/[\\&|]/\\&/g'; }

for f in TASK STATE DECISIONS HANDOFF $EXTRA; do
  src="$H/state/$f.md"; dst="$DEST/$f.md"
  if [ -e "$dst" ]; then
    echo "skip    $dst (exists)"
    continue
  fi
  if [ "$f" = "STATE" ]; then
    tmp="$dst.tmp.$$"
    sed -e "s|{{START_KST}}|$(fmt $T0) ($(esc "$SRC"))|" \
        -e "s|{{DEADLINE_KST}}|$(fmt $D)|" \
        -e "s|{{CAP_NOTE}}|$(esc "$CAP_NOTE")|" \
        -e "s|{{REMAINING_MIN}}|${LEFT}분|" \
        -e "s|{{INPUT_AT}}|$(fmt $NOW)|" \
        -e "s|{{CP_15}}|$(cp $(( T0 + 15 )))|" \
        -e "s|{{CP_40}}|$(cp $(( T0 + 40 )))|" \
        -e "s|{{CP_100}}|$(cp $(( T0 + 100 )))|" \
        -e "s|{{CP_D30}}|$(fmt $(( D - 30 )))|" \
        -e "s|{{CP_D10}}|$(fmt $(( D - 10 )))|" \
        -e "s|{{CONTAINER_TZ}}|$(esc "$CTZ")|" \
        -e "s|{{HARNESS_PATH}}|$(esc "$H")|g" \
        -e "s|{{HARNESS_COMMIT}}|$COMMIT|" \
        -e "s|{{BASE_COMMIT}}|$(esc "$BASE")|" \
        "$src" > "$tmp" && mv "$tmp" "$dst"
  else
    cat "$src" > "$dst"
  fi
  echo "created $dst"
done

echo "T0 $(fmt $T0) KST | D $(fmt $D) KST | 잔여 ${LEFT}분 | harness $COMMIT"
[ -z "$WARN" ] || echo "$WARN" >&2
