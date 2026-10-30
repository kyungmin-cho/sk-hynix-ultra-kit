# AGENTS.md — hx 하네스 작업 규칙 (Cofa Probe 2차 예선용 개인 하네스, 비공식)

## 하네스 없이 쓰는 4줄 (스크립트·env_check를 못 쓸 때 첫 프롬프트에 그대로 붙인다)

```text
1. 과제 README·AGENTS.md를 먼저 읽되 수정하지 마. 외부 LLM/API 호출·패키지 설치·push·승인 우회는 하지 마.
2. notes/STATE.md에 시작 시각·마감(KST)·현재 단계를, notes/DECISIONS.md에 결정을 한 줄씩(시각|단계|결정|대안|이유|근거) 적어.
3. 시작 40분 안에 입력→출력 최소 경로를 한 번 완주해. "통과"는 실행한 명령과 출력으로만 말하고, 없으면 NOT_RUN이라고 써.
4. 10분 막히면 범위를 줄여 방향을 바꿔. 답은 짧게, 끝에 "다음: <행동 1개>".
```

**기능 지도: `$H/CAPABILITIES.md`** — 스킬·참조·docs·상태 양식·scripts·templates 전부를 "어디·언제" 한 표로. 한 번 읽고 필요한 파일만 연다.

## 0. 우선순위

운영 공지 > 과제 README·지시 > 담당자 합의(`notes/DECISIONS.md` §0) > 이 파일. 단 §1 금지는 항상 적용한다.
`H` = 이 하네스 경로(기본 `/tmp/_harness`, 막히면 `<워크스페이스>/_harness`). 상태 파일은 워크스페이스 `notes/`.
`$H`는 에이전트 셸·새 탭에 없을 수 있다. 명령 예시는 `${H:-/tmp/_harness}/scripts/…`로 쓴다(H가 비면 기본 경로). 하네스를 `<워크스페이스>/_harness`로 옮겼으면 `export H=<그 경로>`를 먼저 치거나 명령에 `notes/STATE.md`의 "하네스 경로" 실제 값을 넣는다. 읽을 파일 경로의 `$H/`도 같은 값으로 바꿔 읽는다.

## 1. 금지 (항상)

- 외부 LLM/API 호출(api.openai.com, api.anthropic.com, generativelanguage.googleapis.com, openrouter 등)과 개인 키. 제공된 Codex만 쓴다.
- 모델명 지정·고정(`-m gpt-…`, `--model`, `-c model=…`, config의 model 키 수정). 모델은 사람이 `/model`로 고른다.
- `git push`, `git remote add/remove`, `git init`, `git add -A`, 자동 `git commit`. 커밋은 사람이 경로를 지정해서 한다(§4).
- `codex update`·`codex login`·도구 업데이트, 전역 설치(`npm i -g`, `npx`), `sudo`, `apt-get`, `pip install --break-system-packages`, 시스템 설정 변경.
- 승인·샌드박스 우회: `--dangerously-bypass-approvals-and-sandbox`, `--full-auto`, `--yolo`, `danger-full-access`, `--sandbox`/`-s` 완화, `-a never`. `codex exec` 병렬도 쓰지 않는다.
- 브라우저 자동화(Playwright·Selenium 등)·Computer Use, `curl … | sh`, `find /` 같은 전체 파일시스템 탐색, 시크릿 값 출력(`printenv`, 키 파일 `cat`).
- `pip install`은 ENVIRONMENT.md에서 PyPI가 열려 있고(R4) 사람이 승인할 때만, 워크스페이스 venv에, `requirements.txt`에 기록.
- 과제 README.md·AGENTS.md·주어진 데이터 수정. 하네스 파일을 제출물이 import하거나 통째 복사하는 것.
- 서술형 답안 작성(사람이 직접 친다). 담당자 대화·화면 확인·제출도 사람이 한다.

## 2. 증거 규칙

- "됐다/통과" = 실행한 명령 + 출력 요지 + exit code. 셋 중 하나라도 없으면 `NOT_RUN`.
- 검사 0건 = 실패. 판정은 코드로 하고(`python3 ${H:-/tmp/_harness}/scripts/verdict.py --check "이름:명령"`), 말은 해석만 한다.
- 읽지 않은 파일·실행하지 않은 명령을 했다고 하지 않는다. 추정은 "추정"이라고 쓴다.
- 결과는 `notes/DECISIONS.md` §3 검증 표에 남긴다.

## 3. 단계와 스킬 (자동 발견에 기대지 말고 경로로 읽는다, 색인 `$H/skills/README.md`)

| 단계 | 스킬 경로 | 시간(T=시작) |
|---|---|---|
| 진행자 | `$H/skills/hx-next/SKILL.md` | 단계 전후·막힐 때·압축 후 |
| 1 환경 | `$H/skills/hx-1-env/SKILL.md` | T+0~5 |
| 2 문제 | `$H/skills/hx-2-problem/SKILL.md` | T+5~15 |
| 3 점검 | `$H/skills/hx-3-capability/SKILL.md` | T+15~18 → 최소 E2E T+40까지 |
| 4 시행 | `$H/skills/hx-4-trials/SKILL.md` | T+40~110 |
| 5 수합 | `$H/skills/hx-5-gather/SKILL.md` | T+110~D−30 |
| 6 최종 | `$H/skills/hx-6-final/SKILL.md` | D−30~D |

각 단계의 `references/`(막힘·병렬·증거·결정 기록·반도체 등)는 SKILL.md가 "언제 읽나"와 함께 가리킨다. 규칙 요약·시간표·복사용 문장·유형별 절차는 `$H/docs/`.

## 4. 상태 파일 (워크스페이스 `notes/`, `init_state.sh`가 없는 것만 만든다)

| 파일 | 갱신 시점 |
|---|---|
| `STATE.md` | hx-next 호출마다, 단계 끝마다, 병렬 수 바꿀 때 |
| `TASK.md` | 2단계, 담당자 답변마다, 범위 조정 때 |
| `DECISIONS.md` | 결정·시행·검증마다 한 줄 append(지우지 않음) |
| `HANDOFF.md` | 5단계 초안, 세션 전환·압축 전, 6단계 확정 |
| (선택) `TRIALS.md`·`VERIFICATION.md`·`ESSAY_PREP.md` | `init_state.sh --extra`로 만든 경우만. 있으면 시행·검증·서술형 재료는 여기에, 없으면 DECISIONS §2·§3·HANDOFF §5에 |

- 루트 `ENVIRONMENT.md`는 커밋하지 않는다. 필요한 수치 3줄만 STATE·DECISIONS에 옮긴다.
- 커밋은 사람에게 이 형태로 제안만 한다: `git add notes <제출 폴더> && git commit -m "<무엇을 왜>"`.

## 5. 시간

- 모든 시각은 `TZ=Asia/Seoul date`로(`+%z`가 `+0900`이 아니면 `TZ=KST-9`). 마감 D = 지금+화면 타이머 잔여 분(1순위), 화면 값이 없으면 min(T0+180분, 13:20). 13:20은 권장 마감 D′(하네스 해석)로 따로 표시하고 화면 값을 깎지 않는다. 시계는 확인용.
- T+15 환경·문제 파악 끝(담당자 질문은 사람이 발송) → T+15~40 최소 E2E 한 번 완주 → T+40~D−30 시행·통합 → 마지막 30분은 Must·통합·문서·이해도만(새 기능 금지) → D−10 제출 시작(사람).
- 10분 막히면 방향 전환. 범위 축소 순서: 화면 → 부가 기능 → 품질 케이스(정책만 문서화). 버리지 않는 것: 실행 가능성·핵심 판정+근거 출력·검증 기록 1개·실행 방법.
- 병렬 상한 2(실제 min(2, ENVIRONMENT.md의 PAR_MAX)). T+40·T+100·D−30에 사람이 `/status`로 토큰 소모를 보고 빠르면 병렬 1.

## 6. 응답 방식

- 짧게. 답 끝에 `다음: <행동 1개>`.
- 파일 통째 읽기 금지: `head`·`sed -n`·`grep`으로 필요한 부분만. 데이터는 `python3 ${H:-/tmp/_harness}/scripts/profile_data.py`.
- 컨텍스트 압축·새 세션 뒤에는 `notes/STATE.md` → 이 파일 → `notes/TASK.md` → `notes/HANDOFF.md` 순으로 다시 읽는다.
- 담당자에게 보낼 문장에 GitHub·MCP 등 불필요한 도구 이야기를 넣지 않는다.
