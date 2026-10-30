---
name: hx-1-env
description: Stage 1 environment analysis — read ENVIRONMENT.md (STATUS, [ACTIVE] rules, hx-env v1 tail), fix the active rules and resources (PAR_MAX, pandas/sklearn, pip, socket) into notes/STATE.md.
---
# hx-1-env — 1단계 환경 이해·분석

| 입력 | 출력 | 끝 신호 | 시간 예산 |
|---|---|---|---|
| 워크스페이스 `ENVIRONMENT.md`(사람이 IDE 터미널에서 `bash ${H:-/tmp/_harness}/scripts/env_check.sh`로 생성) | `notes/STATE.md` 환경 요지 3줄·PAR_NOW, `notes/DECISIONS.md` 환경 결정 | [ACTIVE] 규칙이 STATE에 3줄 이하로 고정 | T+0~5 (5분) |

## 절차

0. (사람, 시험 전) README의 clone 줄(`HX_REPO_URL`)이 공개 레포 URL로 돼 있는지부터 확인한다. 하네스 커밋은 `git -C "${H:-/tmp/_harness}" rev-parse HEAD`로 STATE에 적는다.
1. `grep -nE '^STATUS:|^판정 기준|^\[ACTIVE\]|hx-env v1' ENVIRONMENT.md`로 필요한 줄만 읽는다(통째 읽기 금지, 근거가 더 필요하면 해당 절만 `sed -n`). 파일이 없으면 사람에게 env_check 실행을 요청하고, 기다리는 동안 hx-2-problem을 시작한다.
2. `STATUS:` 줄을 본다. `BLOCKED`면 하네스 스크립트를 쓰지 않고 `$H/AGENTS.md` 맨 위 4줄 규칙으로만 진행한다고 사람에게 알린다. `PARTIAL`이면 바로 아래 "판정 기준" 줄의 이유(PyPI 차단·메모리 부족 등)를 요지에 넣고 `[ACTIVE]` 규칙대로 진행한다. 이유가 PyPI·소켓·메모리면 하네스는 그대로 쓴다. **python3 없음**이면 `[ACTIVE] R17`: Python 도구(verdict·presubmit·profile_data·templates)는 못 쓰고 bash 스크립트와 문서·스킬만 남는다.
3. `[ACTIVE] R<n>` 줄을 모두 모은다. 각 줄의 행동 지침이 이 세션의 규칙이다(`[INACTIVE]`는 무시).
4. 꼬리표 `<!-- hx-env v1: ... -->`에서 값을 읽는다: `PY PIP_NET PANDAS SKLEARN GPU NPROC MEM_EFF_GB PAR_MAX SOCKET DATA_MB TZ_OFF`.
5. STATE "ENVIRONMENT 요지 3줄"을 채운다: ① 자원(NPROC·MEM_EFF_GB·GPU) ② 패키지·설치(PY·pandas·sklearn·PIP_NET) ③ 서버·병렬(SOCKET·PAR_MAX). STATE `PAR_NOW` = min(2, PAR_MAX), E2E 전에는 1.
6. 결정이 생기는 것만 DECISIONS §1에 한 줄씩 적는다(예: `10:04|1|stdlib 경로|pandas 경로|PANDAS=none|ENVIRONMENT.md 꼬리표`). `notes/ESSAY_PREP.md`가 있으면 1단계 행에 환경 수치 3줄을 옮긴다(ENVIRONMENT.md 4절 문장 활용, 없으면 HANDOFF §5 Q2 재료로).
7. 사람에게 3줄로 보고하고 hx-2-problem으로 넘어간다.

## 자주 걸리는 규칙 해석

| 규칙 | 뜻 |
|---|---|
| R0 | 서버는 `0.0.0.0`에 바인딩. 장시간 작업은 재시작 가능하게, 결과는 파일로 |
| R3 / R4 | PyPI 막힘 → 설치 시도 금지, 있는 패키지로만 / 열림 → 꼭 필요할 때만 사람 승인 후 워크스페이스 venv |
| R5 / R6 | pandas·sklearn 없으면 stdlib 경로 / GPU 없음 → 딥러닝 학습 제외 |
| R7 | 병렬 상한 PAR_MAX. 시행마다 `OMP_NUM_THREADS` = max(1, NPROC // 병렬 수) |
| R8 | 소켓 거부 → 서버는 사람이 IDE 터미널에서 실행, 결과는 파일로도 검증 (`skills/hx-3-capability/references/web-preview.md`) |
| R9 | 날짜 파싱 함정(`fromisoformat('…Z')`) → `templates/_common.py`의 `parse_ts`를 옮겨 쓴다 |
| R10 | 대용량 → 통째 로드 금지, `python3 ${H:-/tmp/_harness}/scripts/profile_data.py --sample N`과 스트리밍 우선 |
| R16 | 시각은 전부 `TZ=Asia/Seoul`. 컨테이너 TZ가 +0900이 아니면 특히 주의 |
| R17 | python3 없음 → Python 도구·templates 사용 불가. 판정은 명령+출력+exit code를 DECISIONS §3에 직접 기록 |

- SOCKET·PIP_NET은 사람의 IDE 터미널에서 잰 값이다. Codex 샌드박스 안에서는 소켓·네트워크가 더 막힐 수 있다(`docs/ENV_FACTS.md`). 에이전트 안에서 서버·설치가 실패하면 R8처럼 사람이 IDE 터미널에서 실행한다.

- 사전 체험에서 잰 값·아직 모르는 값은 `docs/ENV_FACTS.md`. 규칙 원문 요약은 `docs/RULES.md`.
