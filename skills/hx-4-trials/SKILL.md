---
name: hx-4-trials
description: Stage 4 parallel trials — run up to min(2, PAR_MAX) hypotheses isolated in exp/<n>/, compare against baseline with numbers, record in DECISIONS trials table, adopt or drop; parallel via built-in subagents, a human-opened extra codex tab, or a python experiment script.
---
# hx-4-trials — 4단계 병렬 시행착오

| 입력 | 출력 | 끝 신호 | 시간 예산 |
|---|---|---|---|
| `notes/DECISIONS.md` §2 가설, STATE `PAR_NOW`, 최소 E2E 결과(기준선) | `exp/<n>/`(코드·`RESULT.md`), DECISIONS §2 행, 채택/폐기 한 줄 | 기준선 대비 개선 여부가 숫자로 나옴 | T+40~110 |

## 절차

1. 동시 시행 수 N = min(2, PAR_MAX, STATE `PAR_NOW`). 토큰 점검에서 줄였으면 1(순차).
2. 시행마다 폴더 하나: `exp/<n>/`. 그 시행은 자기 폴더에만 쓴다. 제출 코드는 건드리지 않는다.
3. 각 `exp/<n>/RESULT.md`에 4줄: 가설 / 실행 명령 / 지표 수치(기준선 n=0과 같은 평가 구간) / 결론.
4. 자원: 시행마다 `OMP_NUM_THREADS` = max(1, NPROC // N), sklearn이면 `n_jobs`도 같게. 메모리는 MEM_EFF_GB ÷ N 안에서.
5. `notes/TRIALS.md`(있으면, 없으면 DECISIONS §2)에 한 행씩, 끝나면 `채택`/`폐기`와 이유. 숫자 없이 채택하지 않는다. 실행은 `bash ${H:-/tmp/_harness}/scripts/run_and_log.sh trial<n> -- <명령>`.
6. 한 시행이 10분 넘게 막히면 폐기하고 다음 가설로(이유 한 줄). 전환표·부분 제출은 `skills/hx-4-trials/references/rescue.md`.
7. T+100 체크포인트에서 "지금 채택안으로 제출해도 되나"를 hx-next로 확인하고, T+110에는 새 시행을 멈추고 hx-5-gather로 간다.

## 병렬 방법 (이 셋만)

| 방법 | 언제 | 하는 법 |
|---|---|---|
| A. 기본 서브에이전트 | 코드 수정이 필요한 가설 2개 | Codex에게 "가설 1은 exp/1/, 가설 2는 exp/2/에서 각각 서브에이전트로, 자기 폴더만 수정" 요청. 결과는 RESULT.md로 받는다 |
| B. 사람이 연 추가 탭 | 긴 작업을 따로 돌릴 때 | 사람이 IDE 터미널 탭을 하나 더 열어 **격리 폴더에서** 대화형 실행: `mkdir -p exp/2 && cd exp/2 && codex` → `docs/PROMPTS.md` "병렬 탭 시작" 문장. 루트에서 띄우지 않는다(notes·제출 코드 덮어쓰기 위험). 기록은 메인 세션이 DECISIONS에 합친다 |
| C. 파이썬 실험 스크립트 | 파라미터·모델만 바꾸는 비교 | `exp/<n>/run.py` 하나가 설정 목록을 돌며 지표를 CSV로 쓴다. 한 세션, 토큰 적게 |

- 백그라운드 비대화형 codex 실행을 여러 개 띄우는 방식은 쓰지 않는다(승인 대기에서 멈추거나 우회 플래그가 필요해짐).
- 분할·누수 규칙은 `skills/hx-3-capability/references/data-audit.md`를 따른다.
- 병렬을 시작하기 전에 `skills/hx-4-trials/references/parallel.md`(상한·격리·토큰 체크포인트)를 읽는다.
