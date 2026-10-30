---
name: hx-next
description: Progress driver — read notes/STATE.md, compute remaining time in KST against deadline D, and output current stage, next single action and the next prompt to type; checkpoints, token check, stuck rescue.
---
# hx-next — 진행자

> 기능·참조를 찾을 때는 `CAPABILITIES.md`(하네스 루트) 한 표만 본다. 시간표 상세는 `docs/TIMELINE.md`, 붙여 넣을 문장은 `docs/PROMPTS.md`.

| 입력 | 출력 | 끝 신호 | 시간 예산 |
|---|---|---|---|
| `notes/STATE.md`, 사람이 말한 화면 잔여 분, `TZ=Asia/Seoul date +%H:%M` | STATE 커서(단계·다음 행동·PAR_NOW) 갱신, 사람에게 3줄 | 아래 출력 형식 한 번 | 1분 |

## 절차

1. `notes/STATE.md`를 읽는다(없으면 사람에게 `init_state.sh` 실행을 요청하고 멈춘다).
2. 지금 시각: `TZ=Asia/Seoul date +%H:%M%z` (끝이 `+0900`이 아니면 tzdata가 없는 것 → `TZ=KST-9 date +%H:%M`). 남은 분 = D − 지금. 사람이 화면 잔여 분을 말했으면 그 값이 우선(D = 지금 + 잔여 분, 13:20으로 깎지 않음)이고, 5분 넘게 다르면 STATE에 차이를 적는다. D가 STATE의 권장 마감 D′(13:20)보다 늦으면 한 번만 알린다.
3. 아래 표에서 현재 단계를 고른다. 시간이 단계보다 앞서 있으면 단계를 줄이고 다음 단계로 넘긴다. 6단계(D−30~D)는 줄이지 않는다.
4. 지나간 체크포인트가 있으면 경고 한 줄을 붙인다.
5. STATE의 현재 단계·다음 행동·막힘 타이머를 고친다.
6. 출력한다(그 외 말은 붙이지 않는다). 칠 문장의 `$H`는 STATE의 실제 하네스 경로로 바꿔 쓴다:

```text
단계 n/6 <이름> | 남은 m분 (D HH:MM KST) | 다음: <행동 1개> | 칠 문장: "<사람이 다음에 붙여 넣을 문장>"
```

| 단계 | 스킬 | 시간 | 다음에 칠 문장 예 |
|---|---|---|---|
| 1 | hx-1-env | T+0~5 | `$H/skills/hx-1-env/SKILL.md 대로 ENVIRONMENT.md 판독해.` |
| 2 | hx-2-problem | T+5~15 | `$H/skills/hx-2-problem/SKILL.md 대로 TASK.md 채우고 담당자 질문 3개 뽑아.` |
| 3 | hx-3-capability | T+15~18 → E2E ~T+40 | `$H/skills/hx-3-capability/SKILL.md 대로 접근법 정하고 최소 E2E 만들어.` |
| 4 | hx-4-trials | T+40~110 | `$H/skills/hx-4-trials/SKILL.md 대로 가설 2개 exp/로 시행해.` |
| 5 | hx-5-gather | T+110~D−30 | `$H/skills/hx-5-gather/SKILL.md 대로 채택안 하나로 합치고 검증 표 채워.` |
| 6 | hx-6-final | D−30~D | `$H/skills/hx-6-final/SKILL.md 체크리스트 돌려.` |

## 체크포인트 (지나면 경고, 매번 사람에게 화면 잔여 분을 한 번 묻는다)

| 시점 | 확인 |
|---|---|
| T+15 | TASK 한 문장이 있나, 담당자 질문을 사람이 보냈나 |
| T+40 | 입력→출력 한 번 완주했나. 아니면 범위를 줄여 지금 완주. **토큰 점검** |
| T+100 | "지금 제출해도 되나?" 실행 방법·검증 1개가 있나. **토큰 점검** |
| D−30 | 기능 동결 → hx-6-final. **토큰 점검** |
| D−10 | 사람이 제출 시작 |

- **토큰 점검**: "화면·`/status`의 토큰 사용 표시를 확인해 주세요. 남은 시간에 비해 빠르면 병렬을 1로 줄입니다." 사람이 줄이라고 하면 STATE `PAR_NOW=1`, 토큰 점검 표에 한 줄.
- **막힘 10분**: 같은 문제로 10분이 넘으면(막힘 타이머) 방향 전환을 제안한다(전환표·부분 제출·세션 복원은 `skills/hx-4-trials/references/rescue.md`). 범위 축소 순서: 화면 → 부가 기능 → 품질 케이스(정책만 문서화). 버리지 않는 것: 실행 가능성·핵심 판정+근거 출력·검증 기록 1개·실행 방법. 전환 결정은 DECISIONS에 한 줄.
