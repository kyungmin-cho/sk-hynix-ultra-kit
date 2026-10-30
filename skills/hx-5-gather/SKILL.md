---
name: hx-5-gather
description: Stage 5 gather — collect trial results, logs and test outputs into DECISIONS verification table, merge the adopted approach into one final run path, draft HANDOFF.
---
# hx-5-gather — 5단계 정보 수합

| 입력 | 출력 | 끝 신호 | 시간 예산 |
|---|---|---|---|
| `exp/*/RESULT.md`, DECISIONS §2, 테스트·실행 출력 | 제출 폴더의 단일 실행 경로, DECISIONS §3 검증 표, `notes/HANDOFF.md` 초안 | 실행 명령 하나 + TASK 완료 조건 전부 PASS/FAIL/NOT_RUN 표기 | T+110~D−30 |

## 절차

1. `exp/*/RESULT.md`를 모아 시행 표(TRIALS, 없으면 DECISIONS §2)가 빠짐없는지 확인한다(채택 1개, 나머지 폐기 이유).
2. 채택안을 제출 폴더로 옮겨 **실행 경로 하나**로 만든다(`exp/`는 기록으로 남기고 제출 코드가 import하지 않게).
3. TASK §5 완료 조건마다 검사를 하나씩 붙인다. 모두 한 번에 돌린다:
   `python3 ${H:-/tmp/_harness}/scripts/verdict.py --check "<조건1>:<명령>" --check "<조건2>:<명령>" --md`
4. 출력 표를 `notes/VERIFICATION.md`(있으면, 없으면 DECISIONS §3)에 붙인다. 아직 못 돌린 조건은 명령을 비워 `NOT_RUN`으로 남기고(지우지 않는다) STATE 미검증 목록에 적는다.
5. FAIL은 고칠지(시간 남으면) 한계로 적을지 정해 DECISIONS에 한 줄. 한 줄 형식·`[부채]` 표기는 `skills/hx-5-gather/references/decision-log.md`.
6. 증거 규칙: 표에 없는 "통과"는 말하지 않는다. 검사 0건이면 실패다.
7. `notes/HANDOFF.md` §1~§4 초안: 실행 방법(복붙 명령), 현재 상태(통과/실패/NOT_RUN 수), 한계·가정, 다음 단계.
8. 사람에게 경로 지정 커밋을 제안한다(형식은 `$H/AGENTS.md` §4). D−30이면 hx-6-final로.
