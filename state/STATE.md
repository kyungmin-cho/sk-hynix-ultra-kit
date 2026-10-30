<!-- 생성: init_state.sh | 갱신: hx-next 호출마다·단계 끝마다·병렬 수 변경 때 | 읽기: 모든 스킬이 가장 먼저, 압축·새 세션 직후 -->
# STATE — 현재 커서

> 시각은 전부 KST(`TZ=Asia/Seoul date`). 화면 타이머 잔여 분이 1순위, 시계 계산은 확인용.

## 시간

| 항목 | 값 |
|---|---|
| 시작 시각 T0 (KST) | {{START_KST}} |
| 마감 D (KST) = 지금+화면 잔여 분(1순위), 없으면 min(T0+180분, 13:20) | {{DEADLINE_KST}} |
| 권장 마감 D′ (하네스 해석, 공식 아님) | {{CAP_NOTE}} |
| 잔여 분 (사람 입력 1순위) | {{REMAINING_MIN}} (입력 시각 {{INPUT_AT}} KST) |
| 체크포인트 | T+15 {{CP_15}} · T+40 {{CP_40}} · T+100 {{CP_100}} · D−30 {{CP_D30}} · D−10 {{CP_D10}} |
| 컨테이너 원래 TZ | {{CONTAINER_TZ}} |

## 커서

| 항목 | 값 |
|---|---|
| 현재 단계 | 1/6 환경 (hx-1-env) |
| 다음 행동 1개 | ENVIRONMENT.md 판독 → [ACTIVE] 3줄을 아래에 적기 |
| 막힘 타이머 시작 | - (10분 넘으면 방향 전환) |
| 병렬 수 PAR_NOW | 1 (상한 min(2, PAR_MAX)) |
| 하네스 경로 | {{HARNESS_PATH}} |
| 하네스 커밋 | {{HARNESS_COMMIT}} |
| 워크스페이스 BASE 커밋 | {{BASE_COMMIT}} (6단계 `presubmit.py --base <이 값>`) |

## ENVIRONMENT 요지 3줄 (hx-1-env가 채움)

1. 
2. 
3. 

## 토큰 점검 기록 (T+40·T+100·D−30, 사람이 `/status` 확인)

| 시각 | 사람 판단 | PAR_NOW |
|---|---|---|

## 미검증 목록 (NOT_RUN으로 남은 것)

- 

## 압축·새 세션 후 다시 읽을 것

1. 이 파일 → 2. `{{HARNESS_PATH}}/AGENTS.md` → 3. `notes/TASK.md` → 4. `notes/HANDOFF.md` → 5. `{{HARNESS_PATH}}/skills/hx-next/SKILL.md`
