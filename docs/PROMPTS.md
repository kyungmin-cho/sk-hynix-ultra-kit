# PROMPTS — 복사해서 붙여 넣는 문장

> 경로는 기본 `/tmp/_harness`. 워크스페이스 `_harness`로 옮겼으면 `notes/STATE.md`의 "하네스 경로" 값으로 바꿔 붙인다.
> 짧게 보낸다. 고유명·모델명·도구 이름을 문장에 넣지 않는다.

## 1. 첫 프롬프트 (README 첫 5분 직후)

```text
/tmp/_harness/AGENTS.md를 작업 규칙으로 읽어. /tmp/_harness/skills/hx-1-env/SKILL.md로 ENVIRONMENT.md를 판독하고, 이어서 /tmp/_harness/skills/hx-2-problem/SKILL.md로 과제 문서와 데이터를 T+15 안에 정리해. 그다음은 /tmp/_harness/skills/hx-next/SKILL.md로 진행해.
```

## 2. 하네스 없이 쓰는 4줄 (스크립트·env_check를 못 쓸 때, `AGENTS.md` 맨 위와 같음)

```text
1. 과제 README·AGENTS.md를 먼저 읽되 수정하지 마. 외부 LLM/API 호출·패키지 설치·push·승인 우회는 하지 마.
2. notes/STATE.md에 시작 시각·마감(KST)·현재 단계를, notes/DECISIONS.md에 결정을 한 줄씩(시각|단계|결정|대안|이유|근거) 적어.
3. 시작 40분 안에 입력→출력 최소 경로를 한 번 완주해. "통과"는 실행한 명령과 출력으로만 말하고, 없으면 NOT_RUN이라고 써.
4. 10분 막히면 범위를 줄여 방향을 바꿔. 답은 짧게, 끝에 "다음: <행동 1개>".
```

## 3. 단계별 짧은 호출

| 언제 | 붙일 문장 |
|---|---|
| 아무 때나 | `/tmp/_harness/skills/hx-next/SKILL.md 대로 지금 단계와 다음 행동 1개만 알려줘. 화면 잔여 시간은 <m>분.` |
| 1 환경 | `/tmp/_harness/skills/hx-1-env/SKILL.md 대로 ENVIRONMENT.md 판독해.` |
| 2 문제 | `/tmp/_harness/skills/hx-2-problem/SKILL.md 대로 TASK.md 채우고 담당자 질문 3개 뽑아.` |
| 3 점검 | `/tmp/_harness/skills/hx-3-capability/SKILL.md 대로 접근법 정하고 최소 E2E 만들어. T+40까지 완주가 목표.` |
| 4 시행 | `/tmp/_harness/skills/hx-4-trials/SKILL.md 대로 가설 2개를 exp/1, exp/2에서 시행하고 기준선과 숫자로 비교해.` |
| 5 수합 | `/tmp/_harness/skills/hx-5-gather/SKILL.md 대로 채택안 하나로 합치고 검증 표 채워.` |
| 6 최종 | `/tmp/_harness/skills/hx-6-final/SKILL.md 체크리스트 돌려. 새 기능은 만들지 마.` |
| 기능 찾기 | `/tmp/_harness/CAPABILITIES.md에서 <상황>에 맞는 파일 하나만 골라 그 부분만 읽어.` |

## 4. 상황별

| 상황 | 붙일 문장 |
|---|---|
| 막힘 10분 | `10분 막혔어. /tmp/_harness/skills/hx-4-trials/references/rescue.md 전환표에서 하나 골라 방향 바꾸고, 결정을 DECISIONS에 한 줄 적어.` |
| T+40 E2E 미달 | `범위를 줄여서 지금 입력→출력을 한 번 완주해. 화면·부가 기능은 빼고 핵심 판정과 근거 출력만.` |
| 검증 요청 | `완료 조건마다 검사를 붙여 verdict.py로 한 번에 돌리고 표를 붙여. 못 돌린 건 NOT_RUN으로 남겨.` |
| 근거 확인 | `방금 말한 결과의 실행 명령, 출력 요지, exit code를 보여줘. 없으면 NOT_RUN이라고 해.` |
| 템플릿 반입 | `/tmp/_harness/templates/<폴더>/<파일>에서 <함수>만 제출 폴더로 옮기고 과제에 맞게 고쳐. DECISIONS에 가져온 함수·무엇을 바꿨나 한 줄.` |
| 서브에이전트 병렬 | `가설 1은 exp/1/, 가설 2는 exp/2/에서 각각 서브에이전트로 시행해. 각자 자기 폴더만 수정하고 결과는 RESULT.md 4줄로.` |
| 커밋 제안 | `지금까지 바뀐 파일을 보고 경로를 지정한 커밋 명령 한 줄만 제안해. 실행은 내가 한다.` |
| 제출 직전 | `presubmit.py와 verdict.py를 돌리고 FAIL·NOT_RUN·WARN만 짧게 보고해.` |

### 병렬 탭 시작 (사람이 새 터미널 탭에서 `mkdir -p exp/<n> && cd exp/<n> && codex`로 격리 폴더에서 띄운 뒤 첫 문장)

```text
이 탭은 시행 <n> 전용이고 지금 폴더가 exp/<n>/이야. 이 폴더 안에서만 파일을 만들고 고쳐. notes/와 제출 폴더는 읽기만 해. 가설: <한 줄>. 끝나면 exp/<n>/RESULT.md에 가설·명령·지표(기준선과 같은 평가 구간)·결론 4줄을 써.
```

## 5. 복구

| 상황 | 붙일 문장 |
|---|---|
| 컨텍스트 압축 뒤 | `notes/STATE.md, /tmp/_harness/AGENTS.md, notes/TASK.md, notes/HANDOFF.md 순서로 다시 읽고 hx-next로 다음 행동 1개만 말해.` |
| 새 세션(길어져서 교체) | `이전 세션에서 이어간다. notes/STATE.md와 notes/HANDOFF.md §2를 읽고, /tmp/_harness/AGENTS.md 규칙으로 hx-next부터 진행해. 이미 끝난 결정은 다시 묻지 마.` |
| 세션 교체 전 | `HANDOFF.md §1~§4와 STATE.md 커서를 지금 상태로 갱신해. 새 세션이 이것만 읽고 이어갈 수 있게.` |
| pause·재연결 뒤 | `작업 환경이 재연결됐어. 파일은 그대로야. 돌던 서버·실행을 확인하고, logs/ 중 끝 줄(# end:)이 없는 로그가 있으면 알려줘.` |

## 6. 담당자 메신저 문구 (사람이 직접 보낸다)

업무 언어로만 쓴다. 개발 도구·저장소·연동 도구 이름을 넣지 않는다(경고문이 붙는다는 관찰, 미검증). 질문 틀은 `skills/hx-2-problem/references/interview.md`.

```text
안녕하세요, 과제 이해를 맞추려고 세 가지만 여쭙겠습니다. 1) 지금은 이 판정을 누가 어떤 기준으로 하고 있나요? 2) 놓치는 것과 잘못 알리는 것 중 어느 쪽이 더 곤란한가요? 3) 이 결과를 누가 보고 어떤 결정을 하나요? 답이 어려우시면 제가 <가정>으로 진행하겠습니다.
```

```text
확인 부탁드립니다. 값이 기준과 정확히 같을 때는 정상으로 볼까요, 이상으로 볼까요? 별말씀 없으시면 <정상/이상>으로 처리하고 결과에 적어 두겠습니다.
```

```text
중간 공유드립니다. 지금은 <입력>을 받아 <판정/결과>를 내고, 근거로 <수치/규칙>을 함께 보여 줍니다. <한계 한 줄>. 우선순위가 다르면 알려 주세요.
```

```text
결과에 넣으면 안 되는 정보나 쓰면 안 되는 항목이 있을까요? 없으시면 지금 받은 자료 범위 안에서만 쓰겠습니다.
```
