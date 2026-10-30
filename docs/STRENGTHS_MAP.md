# STRENGTHS_MAP — 조사한 강점 477행 ↔ 이 레포 위치

> 근거: 설계 `2차_조사/harness_structure_v1.md` §4(4.1 SR 168 · 4.2 DK 171 · 4.3 AR 71 + CE 52 · 4.4 AC 15). ID는 설계 문서와 같다.
> 설계 문서의 "반영 위치"는 옛 트리 기준이라 쓰지 않고, 지금 레포의 실제 파일로 다시 매핑했다(2026-10-31).
> 레포 경로 칸: `경로`, `경로::함수`(그 파일에 def/class가 있다), `경로#문자열`(그 파일에 그 문자열이 있다). `tests/test_strengths_map.py`가 전부 확인한다.
> 상태: **구현** = 실행되는 코드·규칙·양식이 있다 / **참조문서** = docs·references·NOTICE에 필요할 때 읽는 글로 있다 /
> **의도적 제외** = 위험하거나 범위 밖이라 넣지 않았고, 그 이유가 `docs/EXCLUDED.md` 또는 금지 검사(`tests/test_guardrails.py`·`tests/test_skills.py`)에 있다.
> 쓰는 법: "그 기능 어디 있지?"면 ID나 낱말로 검색한다. 하네스를 고치면 `python3 -m unittest discover -s tests`로 이 표가 아직 맞는지 본다.


상태별: 구현 302 · 참조문서 70 · 의도적 제외 105 · 합계 477

| ID | 강점(한 줄) | 레포 경로 | 상태 |
|---|---|---|---|
| SR1-1 | 일정 10:00~14:00·과제 180분·서술형 6×5분 | `docs/TIMELINE.md`, `docs/RULES.md` | 참조문서 |
| SR1-2 | 제공 Codex만·권장 모델·Astra 제한·업데이트·개인 키 금지 | `AGENTS.md#1. 금지`, `scripts/env_check.sh`, `docs/RULES.md` | 구현 |
| SR1-3 | 공개 레포 clone 허용·결과 통지까지 공개 유지·push·CU 금지·통째 대체 금지 | `AGENTS.md#1. 금지`, `docs/RULES.md`, `NOTICE.md` | 구현 |
| SR1-4 | 수집 기록(대화·터미널·설정·git log/diff·테스트·토큰) | `AGENTS.md#6. 응답 방식`, `skills/hx-next/SKILL.md`, `state/`, `docs/RULES.md` | 구현 |
| SR1-5 | 웹 IDE·0.0.0.0 미리보기·.git/.codex/.agents 쓰기 차단·소켓 승인·pip 미검증 | `scripts/env_check.sh#R8`, `scripts/env_check.sh#R15`, `scripts/env_check.sh#R3`, `skills/hx-3-capability/references/web-preview.md`, `docs/ENV_FACTS.md` | 구현 |
| SR1-6 | 평가 축 기술/의도/인지(+소통), handoff 고득점 후기 | `state/HANDOFF.md`, `state/DECISIONS.md`, `docs/RULES.md` | 참조문서 |
| SR2-01 | 경로 명시 skills/ 직접 읽기, 시험 우선 규칙 | `AGENTS.md#0. 우선순위`, `skills/README.md` | 구현 |
| SR2-02 | 인터뷰→합의→검증→인계 4스킬+assets, STATE 생성, tests | `scripts/init_state.sh`, `tests/test_state.py`, `skills/hx-2-problem/references/interview.md` | 구현 |
| SR2-03 | 13스킬+오케스트레이터, 덮어쓰기 없는 설치 | `skills/hx-next/SKILL.md`, `scripts/init_state.sh` | 구현 |
| SR2-04 | 숨은 담당자 요구 전제, data-audit·honest-eval, NOTICE | `skills/hx-3-capability/references/data-audit.md`, `NOTICE.md` | 참조문서 |
| SR2-05 | 2차 안내·평가 분석·당일 플레이북 문서 | `docs/RULES.md`, `docs/TIMELINE.md` | 참조문서 |
| SR2-06 | TASK/DECISIONS/RUN, preflight, verdict_engine, 서술형 대비 | `state/TASK.md`, `state/DECISIONS.md`, `scripts/verdict.py::run_check`, `state/HANDOFF.md#5. 서술형 대비`, `skills/hx-6-final/references/checklist.md#서술형 대비` | 구현 |
| SR2-06b | 출처 표기 없는 완전 사본 → 원본만 인용 | `NOTICE.md`, `docs/EXCLUDED.md` | 의도적 제외 |
| SR2-07 | 시험 안내 가이드 스킬(규칙·플랫폼·출처 판본) | `docs/RULES.md`, `docs/ENV_FACTS.md` | 참조문서 |
| SR2-08 | 공급망 lock·dry-run doctor | `NOTICE.md`, `docs/EXCLUDED.md#의존성 lock` | 의도적 제외 |
| SR2-09 | 코치 스킬+rubric 레퍼런스 / 원격 패키지 실행기 설치 위험 | `skills/hx-2-problem/references/interview.md`, `docs/EXCLUDED.md` | 참조문서 |
| SR2-10 | 번들 전부 설치 유도, graphify 외부 LLM 가능 | `docs/EXCLUDED.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR2-11 | RUNBOOK·ESSAY_PREP·VALIDATION·출처표 | `state/ESSAY_PREP.md`, `docs/RULES.md`, `NOTICE.md` | 구현 |
| SR2-12 | PreToolUse hook 가드·서브에이전트 정의 | `docs/EXCLUDED.md#PreToolUse hook`, `tests/test_guardrails.py#PATTERNS` | 의도적 제외 |
| SR2-13 | cofa-next·qna-prep·RUNBOOK·QNA_BANK | `skills/hx-next/SKILL.md`, `skills/hx-6-final/references/checklist.md#서술형 대비` | 구현 |
| SR2-14 | stdlib kitlib·플레이북·preflight / 통째 대체 위험 | `templates/README.md`, `docs/PLAYBOOKS.md` | 구현 |
| SR2-15 | 승인/샌드박스 완화 명령 안내 | `docs/EXCLUDED.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR2-16 | config 모델 고정·9 서브에이전트·포크 전역 설치 | `docs/EXCLUDED.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR2-17 | 단일 스킬·규칙 우선·우회 금지 문구 | `AGENTS.md#0. 우선순위` | 구현 |
| SR2-18 | clone 후 rev-parse로 출처 기록, idea-partner | `skills/hx-2-problem/SKILL.md`, `scripts/init_state.sh` | 구현 |
| SR2-19 | .agents 심볼릭 링크, CODEX_SETUP, evaluation/ | `skills/README.md`, `docs/EXCLUDED.md` | 구현 |
| SR2-20 | READY/PARTIAL/BLOCKED 보고 / MCP config 수정 | `scripts/env_check.sh`, `docs/EXCLUDED.md` | 구현 |
| SR2-21 | data_audit·mapping_check, dry-run 기본 | `scripts/profile_data.py::profile`, `skills/hx-3-capability/references/data-audit.md`, `docs/EXCLUDED.md#hooks` | 구현 |
| SR2-22 | doctor·보일러플레이트·gstack-upgrade | `docs/EXCLUDED.md#보일러플레이트` | 의도적 제외 |
| SR2-23 | setup.sh 시스템 패키지 보호 무시·저장소 초기화/commit | `docs/EXCLUDED.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR2-24 | 서브에이전트 1개 제한 / 설치 시 자동 커밋 | `skills/hx-4-trials/references/parallel.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR2-25 | PLAYBOOK·PROMPTS, ~/.codex·~/.agents 설치 | `docs/PROMPTS.md` | 참조문서 |
| SR2-26 | tools/profile.py 데이터 프로파일 | `scripts/profile_data.py` | 구현 |
| SR2-27 | lenses/, bin/check.py 기록 점검 | `scripts/presubmit.py::check_notes` | 구현 |
| SR2-28 | PLAYBOOK·QUICKSTART·setup --apply·tests | `tests/`, `README.md` | 구현 |
| SR2-29 | deep-interview·verification-before-completion | `skills/hx-2-problem/SKILL.md`, `skills/hx-6-final/references/verify.md` | 구현 |
| SR2-30 | prompts 00~07 단계별 | `docs/PROMPTS.md` | 참조문서 |
| SR2-31 | check_project.py, 비공식 명시 | `scripts/presubmit.py::main`, `README.md#비공식` | 구현 |
| SR2-32 | pytest runner·요구사항 추적 CSV | `state/VERIFICATION.md`, `scripts/run_and_log.sh` | 구현 |
| SR2-33 | exam-boundaries·반입 미확인 사항 정리 | `docs/ENV_FACTS.md`, `docs/RULES.md` | 참조문서 |
| SR2-34 | KIT-INDEX·playbooks·tests / curl tarball 대체 안내 | `skills/README.md`, `docs/EXCLUDED.md` | 구현 |
| SR2-35 | 문제유형별 templates / 사전 작성 코드 위험 | `templates/README.md`, `templates/ml/` | 구현 |
| SR2-36 | node-http·fastapi scaffold | `templates/web/`, `docs/EXCLUDED.md` | 구현 |
| SR2-37 | tmux 병렬 Codex(team) | `skills/hx-4-trials/references/parallel.md`, `docs/EXCLUDED.md` | 의도적 제외 |
| SR2-38 | 한 단어 명령 AGENTS | `docs/PROMPTS.md` | 참조문서 |
| SR2-39 | timed 프로필·check.sh | `docs/TIMELINE.md` | 참조문서 |
| SR2-40 | 결과 발표 전까지 공개 유지 명시 | `README.md`, `NOTICE.md` | 구현 |
| SR2-41 | WORKFLOW·WORKLOG·HANDOFF 템플릿 | `state/HANDOFF.md` | 구현 |
| SR2-42 | handoff 단일 스킬 | `state/HANDOFF.md`, `skills/hx-4-trials/references/rescue.md` | 구현 |
| SR2-43 | templates 3, setup.sh | `state/` | 구현 |
| SR2-44 | analysis-plan·experiment-log / 원격 MCP | `state/TRIALS.md`, `docs/EXCLUDED.md` | 구현 |
| SR2-45 | Cofa 워크플로 스킬 / 브라우저 자동화 도구 자동 조작·OCR | `docs/EXCLUDED.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR2-46 | cofa 스킬 4 + ZIP(미검사) | `docs/EXCLUDED.md#juhun7777` | 의도적 제외 |
| SR2-47 | 소문자 skill.md(자동 인식 불가) | `docs/EXCLUDED.md#소문자`, `tests/test_skills.py::test_skill_md_exact_name_and_frontmatter` | 의도적 제외 |
| SR2-48 | prompt_plan.md 1개 | `docs/PROMPTS.md` | 참조문서 |
| SR2-49 | 고정 커밋 설치 / 외부 레포 추가 clone | `NOTICE.md`, `docs/EXCLUDED.md` | 참조문서 |
| SR2x-01 | 담당자 요청형 웹 과제 스킬 13 | `skills/hx-2-problem/SKILL.md` | 구현 |
| SR2x-02 | 범용 스킬 4 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-03 | ponytail-review 벤더 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-04 | 범용 스킬 4 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-05 | context7 MCP 원격 패키지 실행기 | `docs/EXCLUDED.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR2x-06 | 범용 스킬 3 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-07 | 단일 스킬 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-08 | 디자인·React·윤문, 경로 명시 읽기 | `skills/README.md` | 구현 |
| SR2x-09 | 개인 범용 31 스킬 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-10 | --search·--add-dir .git·hook 4 | `docs/EXCLUDED.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR2x-11 | 2차 예선 학습 저장소 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-12 | npm 전역 설치 codex 문서 | `tests/test_guardrails.py` | 의도적 제외 |
| SR2x-13 | 1차 안내·점검 스크립트 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-14 | 1차 모의고사 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-15 | 학습 가이드 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-16 | 1차 자료 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-17 | 학습 자료 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-18 | 연습 과제 결과물 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-19 | README·AGENTS.md만 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-20 | 빈 레포 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-21 | 9월 포트폴리오 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-22 | 하네스 벤치마크 PDF | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-23 | preflight·빈 결과≠통과 원조 | `scripts/verdict.py::main`, `templates/contract/check_output.py::check`, `NOTICE.md#exit 2` | 구현 |
| SR2x-24 | CLAUDE.md 중심, Probe 업로드 설명 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-25 | conductor 멀티에이전트·curl/npm | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-26 | Ollama 연구 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-27 | 의사결정 하네스 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-28 | 다른 대회 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR2x-29 | 무관: ThinkEnigmatic/cofahub, isopink/hynix-298f, namojo/aihck, App-Legend/Skills-GUI, bigbulgogiburger/codex-basic-skills, Seongwonp/AIDA, rignore/skills, 기타 cofactor·주가 레포 | `docs/EXCLUDED.md#ThinkEnigmatic` | 의도적 제외 |
| SR2x-30 | 범용 요구사항 면담 스킬 | `skills/hx-2-problem/references/interview.md` | 참조문서 |
| SR2x-31 | 대화 기록 외부 전송 MCP bridge(@latest) | `docs/EXCLUDED.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR3.1-a | AGENTS 시험 우선 규칙(push·자동커밋·CU·서술형 AI 금지), skills 9(원본 트리 `tree.txt`의 `skills/*/SKILL.md` 실측 9개. SR 노트 §2·§3.1의 "8"은 오기)(상당수 mattpocock/skills·superpowers 계열 재작성 → 원본 라이선스 확인 필요) | `AGENTS.md#1. 금지` | 구현 |
| SR3.1-b | .agents 대신 skills/<이름> 직접 읽기, 인터뷰 기반 3부채 관점 | `AGENTS.md#3. 단계와 스킬`, `skills/README.md` | 구현 |
| SR3.1-c | README가 에이전트 대상 설치 지시문·라이선스 없음·계속 갱신 | `README.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR3.1-d | Bash·git만, root 불필요, 명시적 읽기로 경로 문제에 강함 | `skills/README.md` | 구현 |
| SR3.1-e | docs/debt/ 기술 부채 기록 폴더 | `state/HANDOFF.md`, `state/TASK.md` | 구현 |
| SR3.2-a | 4스킬+assets 템플릿, setup이 체크포인트 계산·STATE.md 생성, tests | `state/STATE.md`, `scripts/init_state.sh`, `tests/test_state.py` | 구현 |
| SR3.2-b | 운영 공지>필수조건>하네스, 최신 메일 우선, npm -g·도구 업데이트 금지 | `AGENTS.md#0. 우선순위` | 구현 |
| SR3.2-c | setup의 저장소 초기화/config 가능성 | `tests/test_guardrails.py` | 의도적 제외 |
| SR3.2-d | .agents 쓰기 차단 시 설치 실패 가능 | `scripts/env_check.sh#R15`, `skills/README.md`, `docs/EXCLUDED.md#~/.agents/skills` | 의도적 제외 |
| SR3.3-a | hackathon 오케스트레이터+13스킬, 덮어쓰기 없음, work/ ignore | `skills/hx-next/SKILL.md`, `scripts/init_state.sh` | 구현 |
| SR3.3-b | 40분 최소 흐름·10분 멈춤·마지막 30분, 화면·메신저·제출은 사람 | `AGENTS.md#5. 시간`, `skills/hx-4-trials/references/rescue.md`, `docs/TIMELINE.md` | 구현 |
| SR3.3-c | 라이선스 없음(일부 원본 LICENSE 동봉) | `NOTICE.md` | 참조문서 |
| SR3.3-d | /tmp 불가 시 work/ 대체 경로 | `scripts/env_check.sh#R11`, `README.md` | 구현 |
| SR3.4-a | 8스킬, 짧은 AGENTS, ~/.agents 사용자 범위 설치, recon 프롬프트, NOTICE | `skills/hx-3-capability/references/data-audit.md`, `skills/hx-5-gather/references/decision-log.md`, `docs/PROMPTS.md`, `NOTICE.md` | 참조문서 |
| SR3.4-b | 누수·시간순 분할·정직한 평가, 작업 공간 밖 설치 | `README.md`, `skills/hx-3-capability/references/data-audit.md` | 구현 |
| SR3.4-c | --with-pstack 추가 clone | `docs/EXCLUDED.md` | 의도적 제외 |
| SR3.5-a | 7스킬·templates 7·docs 3·setup(config 미수정·AGENTS 보존) | `state/`, `docs/RULES.md`, `docs/TIMELINE.md` | 구현 |
| SR3.5-b | 일정·감독·수집 기록 정리, 반도체 도메인, 0.0.0.0·포트·Host 헤더 | `skills/hx-3-capability/references/web-preview.md`, `skills/hx-3-capability/references/semiconductor/`, `docs/RULES.md` | 참조문서 |
| SR3.5-c | 메일 재서술 공개(원문 대조 필요) | `docs/RULES.md` | 참조문서 |
| SR3.6-a | 역할·절대규칙·증거규칙, TASK/DECISIONS/RUN, preflight, verdict, eda, test_template | `AGENTS.md#2. 증거 규칙`, `state/TASK.md`, `scripts/verdict.py::run_check`, `scripts/env_check.sh`, `scripts/profile_data.py::profile` | 구현 |
| SR3.6-b | "환경이 배신/초록불이 거짓말"을 180분·서술형 6문항에 맞춤 | `skills/hx-6-final/references/verify.md`, `skills/hx-6-final/references/checklist.md#서술형 대비` | 참조문서 |
| SR3.6-c | ubinoqe 무단 사본 → 원본만 참고 | `NOTICE.md` | 참조문서 |
| SR3.6-d | Python3만, AGENTS 기반이라 자동 발견 무관 | `AGENTS.md#3. 단계와 스킬` | 구현 |
| SR3.7-a | .agents 18스킬, templates/SESSION.md, Node helper | `state/HANDOFF.md`, `docs/EXCLUDED.md` | 구현 |
| SR3.7-b | rules·platform·sources 출처 판본 구분, 개인 워크플로는 무거움 | `docs/RULES.md`, `docs/ENV_FACTS.md` | 참조문서 |
| SR3.7-c | 위험 낮음(타사 모델는 언급뿐) | `docs/RULES.md` | 참조문서 |
| SR3.7-d | 가이드 스킬만 단독 참고 가치 | `docs/RULES.md` | 참조문서 |
| SR3.8-a | upstream 벤더링 커밋 보관, kit.py verify-bundle/doctor, lock json, EXAM_RULES | `docs/RULES.md`, `NOTICE.md` | 참조문서 |
| SR3.8-b | 공급망 고정·dry-run, pip/npm 제거(미검증) | `scripts/env_check.sh#R3`, `docs/ENV_FACTS.md` | 구현 |
| SR3.8-c | 라이선스 혼재·190파일 무거움 | `docs/EXCLUDED.md#arcturus0637-rgb` | 의도적 제외 |
| SR3.9-a | coach 스킬+references(discovery·explainback·rubric 등), install.py 백업 | `skills/hx-6-final/references/checklist.md#서술형 대비`, `skills/hx-2-problem/references/interview.md` | 참조문서 |
| SR3.9-b | rubric 배점(비공식), Codex 대화 자체가 평가 대상 | `AGENTS.md#6. 응답 방식`, `docs/RULES.md` | 참조문서 |
| SR3.9-c | 원격 패키지 실행기 skills 설치·graphify 외부 LLM·전부 설치 유도 | `docs/EXCLUDED.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR3.10-a | task-evidence-check·RUNBOOK·ESSAY_PREP·VALIDATION·cofa-core 출처표·뷰어 | `state/ESSAY_PREP.md`, `skills/hx-6-final/references/verify.md`, `docs/RULES.md`, `docs/EXCLUDED.md` | 구현 |
| SR3.10-b | 출처 교차 확인 신중(독립 증언 중복 계산 안 함) | `docs/RULES.md` | 참조문서 |
| SR3.10-c | 첫 프롬프트 특정 인물명 혼선 | `docs/PROMPTS.md#1. 첫 프롬프트`, `docs/EXCLUDED.md#특정 인물·팀 이름` | 의도적 제외 |
| SR3.11-a | verify·SK CI 스킬, .codex config·agents·hooks 가드, 6칸 지시 형식 | `docs/PROMPTS.md`, `tests/test_guardrails.py` | 참조문서 |
| SR3.11-b | hook·신뢰 필요, .codex 쓰기 막히면 무력화 | `docs/EXCLUDED.md#PreToolUse hook` | 의도적 제외 |
| SR3.12-a | 계획 먼저·stdlib 우선·0.0.0.0·로그 없는 통과 금지, kitlib 18, playbook, preflight | `AGENTS.md#2. 증거 규칙`, `scripts/run_and_log.sh`, `docs/PLAYBOOKS.md` | 구현 |
| SR3.12-b | 사전 작성 코드 통째 대체 충돌, 세 곳 스킬 복사 | `templates/README.md`, `docs/EXCLUDED.md` | 의도적 제외 |
| SR3.13-a | 2차 안내 기준 AGENTS, mock-followup 서술형 연습(mattpocock/skills 9개 원본 그대로 동봉은 회피) | `skills/hx-6-final/references/checklist.md#서술형 대비` | 참조문서 |
| SR3.13-b | -a never·network·dangerously-bypass 안내, .git/info/exclude 수정 | `docs/EXCLUDED.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR3.14-a | 21스킬·.codex/agents 9·config·omx | `docs/EXCLUDED.md` | 의도적 제외 |
| SR3.14-b | 모델 고정·npm -g 포크·9 병렬 토큰 부담 | `skills/hx-4-trials/references/parallel.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR3.15-a | 코테형 스킬, bootstrap READY/PARTIAL/BLOCKED, 금지 패턴 자체 테스트 | `scripts/env_check.sh`, `tests/test_guardrails.py` | 구현 |
| SR3.15-b | .codex config MCP 블록 추가·원격 패키지 실행기 MCP | `docs/EXCLUDED.md` | 의도적 제외 |
| SR3.16-a | 단일 스킬·MIT·규칙 우선 문구 | `AGENTS.md#0. 우선순위` | 구현 |
| SR3.16-b | rev-parse 출처 기록, idea-partner(사용자가 아이디어 소유) | `skills/hx-2-problem/SKILL.md`, `scripts/init_state.sh` | 구현 |
| SR3.16-c | $cofa-next(단계·남은 시간·다음 문장), QNA_BANK | `skills/hx-next/SKILL.md`, `skills/hx-6-final/references/checklist.md#서술형 대비` | 구현 |
| SR3.16-d | 시스템 패키지 보호 무시 플래그 조용히 설치 | `tests/test_guardrails.py` | 의도적 제외 |
| SR3.16-e | --search·--add-dir .git·hook·라이브러리 스킬 | `docs/EXCLUDED.md` | 의도적 제외 |
| SR3.16-f | 사전 작성 에이전트/ML/MCP/웹 코드 반입 위험 | `templates/README.md`, `docs/EXCLUDED.md` | 의도적 제외 |
| SR4-1 | curl/bash 0건, curl tarball 대체 안내 | `tests/test_guardrails.py#curl-pipe-sh`, `docs/EXCLUDED.md#외부 다운로드` | 의도적 제외 |
| SR4-2 | 텔레메트리 없음, MCP bridge만 전송 | `tests/test_guardrails.py#test_no_outbound_network_in_code`, `docs/EXCLUDED.md#텔레메트리` | 의도적 제외 |
| SR4-3 | Codex 업데이트·전역 설치 | `AGENTS.md#1. 금지`, `tests/test_guardrails.py` | 의도적 제외 |
| SR4-4 | 승인/샌드박스 완화 | `AGENTS.md#1. 금지`, `tests/test_guardrails.py` | 의도적 제외 |
| SR4-5 | 다른 모델·외부 LLM, 과제 제공 키만 | `AGENTS.md#1. 금지`, `tests/test_guardrails.py` | 의도적 제외 |
| SR4-6 | Computer Use·브라우저 자동 조작 | `AGENTS.md#1. 금지`, `docs/EXCLUDED.md` | 의도적 제외 |
| SR4-7 | push 0건, 설치기 저장소 초기화/commit 자동 | `AGENTS.md#1. 금지`, `AGENTS.md#4. 상태 파일`, `tests/test_guardrails.py` | 의도적 제외 |
| SR4-8 | 에이전트 대상 설치 지시문 | `README.md`, `tests/test_guardrails.py` | 의도적 제외 |
| SR4-9 | 무단 사본 | `NOTICE.md`, `docs/EXCLUDED.md#ubinoqe` | 의도적 제외 |
| SR4-10 | 대부분 라이선스 없음, MIT 목록 | `LICENSE`, `NOTICE.md` | 참조문서 |
| SR5-1 | SKILL.md 프런트매터 name/description, 소문자 skill.md 불가 | `tests/test_skills.py::test_skill_md_exact_name_and_frontmatter`, `tests/test_guardrails.py::test_frontmatter_and_head_table` | 의도적 제외 |
| SR5-2 | 배치 경로 쟁점 → 경로 명시 읽기가 가장 안전 | `AGENTS.md#3. 단계와 스킬`, `scripts/env_check.sh#R15`, `skills/README.md` | 구현 |
| SR5-3 | 의존성 Bash·Git·Python3, root 불필요 | `scripts/env_check.sh#5.2 런타임`, `templates/_common.py::optional_import` | 구현 |
| SR5-4 | 공개 유지 필요·삭제 위험·커밋 해시 기록 | `scripts/init_state.sh#rev-parse`, `README.md`, `NOTICE.md`, `docs/RULES.md#공개` | 구현 |
| SR6-1 | 검증 0건=실패 판정기 | `scripts/verdict.py::main`, `templates/contract/check_output.py::check`, `tests/test_guardrails.py::test_verdict_exit_codes` | 구현 |
| SR6-2 | 3분 환경 preflight(파이썬·Z 함정·포트) | `scripts/env_check.sh#5.3 Python 패키지`, `scripts/env_check.sh#R9`, `scripts/env_check.sh#5.8 한도`, `templates/_common.py::parse_ts` | 구현 |
| SR6-3 | DECISIONS(조건→처리→이유→대안)·handoff | `state/DECISIONS.md`, `state/HANDOFF.md`, `skills/hx-5-gather/references/decision-log.md` | 구현 |
| SR6-4 | 작업 기록에서 예상 질문 6개 생성 | `state/ESSAY_PREP.md`, `skills/hx-6-final/references/checklist.md#서술형 대비` | 구현 |
| SR6-5 | $next 진행자(단계·남은 시간·다음 문장) | `skills/hx-next/SKILL.md` | 구현 |
| SR6-6 | 출처 커밋 해시 기록 | `scripts/init_state.sh#rev-parse`, `NOTICE.md` | 구현 |
| SR6-7 | 질문 틀(정상·예외·우선순위·금지·성공 기준) | `skills/hx-2-problem/references/interview.md` | 참조문서 |
| SR8-1 | 공식 배포 하네스 없음 | `docs/RULES.md` | 참조문서 |
| SR8-2 | 검증된 커뮤니티 표준 키트 없음 | `NOTICE.md` | 참조문서 |
| SR8-3 | 소셜 공유 레포 미발견 | `docs/EXCLUDED.md#소셜 공유` | 의도적 제외 |
| SR8-4 | 이슈·토픽 미수행 | `docs/EXCLUDED.md#이슈/토픽` | 의도적 제외 |
| SR8-5 | 대형 레포 부분 검사·ZIP 미검사 | `docs/EXCLUDED.md#ZIP` | 의도적 제외 |
| SR8-6 | 실행 미검증(정적 판독) | `docs/ENV_FACTS.md` | 참조문서 |
| SR8-7 | 규칙 서술은 2차 재서술 | `docs/RULES.md` | 참조문서 |
| SR8-8 | 이후 새 레포 미포함 → 당일 해시 재확인 | `README.md`, `NOTICE.md` | 참조문서 |
| DK1-1 | 응시 환경 사실: 루트=홈=git, Py3.11·Node22·Codex0.163, 샌드박스 소켓 차단, 0.0.0.0 미리보기, "GitHub/MCP 언급 시 경고문 자동 삽입"(미검증) | `AGENTS.md#1. 금지`, `scripts/env_check.sh#5.6 워크스페이스`, `scripts/env_check.sh#5.8 한도`, `skills/hx-2-problem/references/interview.md`, `docs/ENV_FACTS.md` | 구현 |
| DK1-2 | pip 설치 가능 여부 미기록 → 사전 체험 핵심 미지수, 막히면 stdlib | `scripts/env_check.sh#5.4 네트워크`, `scripts/env_check.sh#R3`, `scripts/env_check.sh#R4`, `docs/ENV_FACTS.md` | 구현 |
| DK1-3 | 레포 삭제·재생성 위험 실재 → 커밋 해시 기록·대안 준비 | `scripts/init_state.sh#rev-parse`, `README.md`, `NOTICE.md` | 구현 |
| DK2-1 | A등급 3개(wildrage98·PKJ·ripplelover)가 도메인 코드 핵심 → 상세는 DK3.x | `templates/README.md` | 구현 |
| DK2-2 | B등급(보조 코드) 목록 → 레포별은 DK4 | `templates/README.md#유형 → 모듈`, `scripts/profile_data.py`, `scripts/presubmit.py` | 구현 |
| DK2-3 | C등급(문서형 도메인 지식) → DK5 | `skills/hx-3-capability/references/data-audit.md`, `skills/hx-3-capability/references/semiconductor/` | 참조문서 |
| DK2-4 | D등급(대회 키트 아닌 도메인 참고) → DK6 | `docs/PLAYBOOKS.md`, `docs/EXCLUDED.md` | 참조문서 |
| DK2-5 | E등급: 도메인 코드 없음 확인(templates 후보 아님) — JongMoKoo/ai-native-cli-kit, Hantastic-02/h-kit, DonghaeSuh/codex-sprint-kit·codex-timebox-kit, Malrangbbobbi/hynix-harness-kit("no solution code"), zittenyetten/cofa-probe-kit, jin-castle/sk-ai-exam-operator, jyn0e923-maker/hynix-kit(빈 레포), sj-park-kr/codex-exam-harness, ytm220/hackathon-harness, Shinick-Han/agent-exam-kit, peussd55/codex-exam-kit, ChangYeongJeong1103/codex-kit, combe4259/hy-codex-kit, bjun7595-ops/my-codex-kit, suhyun14/jshch13-harness, moon-gi-jeon/moonskill2, Chiman2937/probe-harness, orichardev/ai-task-workflow-kit + 코드 0개 후보 31개 | `docs/EXCLUDED.md#도메인 코드 없음` | 의도적 제외 |
| DK2-6 | DonghaeSuh `practice/grade_csv.py` = 계약 테스트 러너(DK §7) → 출력 계약 검증 아이디어 | `templates/contract/` | 구현 |
| DK7-1 | 코드 검색 유효 신호 중 대회 무관: kitae104/Semiconductor_Data_Analysis(.claude 강의 스킬), kennedym-ds/python-for-semiconductors-(학습 모듈, MIT) | `docs/EXCLUDED.md#kitae104` | 의도적 제외 |
| DK7-2 | 신규 레포 검색 156질의·페이지네이션·코드 검색 53질의(방법 기록) | `docs/EXCLUDED.md#조사 한계` | 의도적 제외 |
| DK7-3 | 20:46 이후 도메인 코드 있는 신규·갱신 레포 목록 → 레포별 행은 DK3.3·DK4·DK5 | `templates/README.md#유형 → 모듈`, `docs/EXCLUDED.md#5. 조사했지만` | 참조문서 |
| DK7-4 | 도메인 코드 없음 확인 목록·일반 도메인 레포 → DK2-5·DK6 행 참조 | `docs/EXCLUDED.md#도메인 코드 없음` | 의도적 제외 |
| DK3.1-01 | csvio: 구분자·인코딩 추정, 타입 변환 | `templates/_common.py::sniff_csv`, `templates/_common.py::stream_csv`, `templates/_common.py::to_float` | 구현 |
| DK3.1-02 | timeparse: 혼합 타임스탬프 파싱·정렬·간격 추정 | `templates/_common.py::parse_ts`, `templates/_common.py::infer_interval` | 구현 |
| DK3.1-03 | profile: 3분 데이터 요약 + 담당자 질문 후보 | `scripts/profile_data.py::profile`, `scripts/profile_data.py::questions` | 구현 |
| DK3.1-04 | quality: 결측·중복·범위 점검과 처리 정책 | `scripts/profile_data.py::profile`, `templates/contract/check_output.py::check`, `templates/ml/clean.py::fit_cleaner`, `skills/hx-3-capability/references/data-audit.md` | 구현 |
| DK3.1-05 | stats_detect: 직전 창 z·EWMA·CUSUM·IQR·stuck | `templates/anomaly/stats_detect.py::rolling_zscore`, `templates/anomaly/stats_detect.py::ewma_detect`, `templates/anomaly/stats_detect.py::cusum`, `templates/anomaly/stats_detect.py::iqr_bounds`, `templates/anomaly/stats_detect.py::stuck` | 구현 |
| DK3.1-06 | spc: I-MR·Xbar-R·WE 규칙·Cp/Cpk | `templates/spc/spc.py::imr_fit`, `templates/spc/spc.py::xbar_r_fit`, `templates/spc/spc.py::western_electric`, `templates/spc/spc.py::cp_cpk` | 구현 |
| DK3.1-07 | rules: 설명 가능한 임계치 판정(연속 n회·조건부) | `templates/anomaly/rules.py::consecutive_rule`, `templates/anomaly/rules.py::evaluate_rows` | 구현 |
| DK3.1-08 | alerts: 경보 생명주기 상태머신 | `templates/anomaly/events.py::alert_lifecycle` | 구현 |
| DK3.1-09 | evalmetrics: 이벤트/포인트 P·R·F, 같은 설비끼리 매칭 | `templates/anomaly/events.py::event_prf`, `templates/anomaly/events.py::point_prf` | 구현 |
| DK3.1-10 | groupstats: 요인별 불량률·카이제곱·순위·교차표 | `templates/yield_/groupstats.py::defect_rate_by`, `templates/yield_/groupstats.py::chi_square`, `templates/yield_/groupstats.py::rank_factors`, `templates/yield_/groupstats.py::contingency` | 구현 |
| DK3.1-11 | logparse: 로그 패턴 파싱·분류·집계 | `templates/logparse/logparse.py::make_parser`, `templates/logparse/logparse.py::parse_lines`, `templates/logparse/logparse.py::count_by` | 구현 |
| DK3.1-12 | reconcile: 두 자료 키 대사 | `templates/reconcile/reconcile.py::compare`, `templates/reconcile/reconcile.py::normalize_key` | 구현 |
| DK3.1-13 | schedule: 디스패칭 규칙 비교·간트 | `templates/schedule/dispatch.py::compare_rules`, `templates/schedule/dispatch.py::gantt_text` | 구현 |
| DK3.1-14 | report: 마크다운/HTML 리포트 빌더 | `templates/_common.py::md_table`, `templates/web/server.py::page`, `templates/web/server.py::write_static`, `scripts/verdict.py#--md` | 구현 |
| DK3.1-15 | svgchart: 의존성 없는 SVG 선/막대 차트 | `templates/web/server.py::svg_line`, `templates/web/server.py::svg_bar` | 구현 |
| DK3.1-16 | webapp: http.server 0.0.0.0, 소켓 차단 시 HTML 폴백 | `templates/web/server.py::serve`, `templates/web/server.py::write_static`, `skills/hx-3-capability/references/web-preview.md` | 구현 |
| DK3.1-17 | synth: 합성 센서 데이터+이상 주입+정답표 | `templates/anomaly/events.py::synth_series`, `templates/contract/check_output.py::gen_fixture` | 구현 |
| DK3.1-18 | cli: 제출물 CLI 진입점 골격 | `templates/README.md#제출물 진입점 예시` | 구현 |
| DK3.1-19 | sensor_pipeline: 합성→정제→규칙→판정→리포트→서빙 E2E 배선 | `templates/anomaly/events.py::synth_series`, `docs/PLAYBOOKS.md#1. 센서 이상탐지` | 참조문서 |
| DK3.1-20 | yield_rootcause: 수율 요인 분석 배선 | `templates/yield_/groupstats.py::yield_summary`, `docs/PLAYBOOKS.md#4. 수율·불량 요인` | 참조문서 |
| DK3.1-21 | preflight: 파이썬·pip 네트워크·소켓·쓰기·git + 제출 전 점검 | `scripts/env_check.sh`, `scripts/presubmit.py::main` | 구현 |
| DK3.1-22 | profile_csv: CSV 하나→MD 요약+질문 후보 | `scripts/profile_data.py::render`, `scripts/profile_data.py::questions` | 구현 |
| DK3.1-23 | test_kitlib: 모듈별 unittest 회귀 | `templates/anomaly/test_stats_detect.py`, `templates/spc/test_spc.py`, `templates/README.md#테스트` | 구현 |
| DK3.1-24 | playbook 9개: 문제 유형별 절차·Codex 전술 | `docs/PLAYBOOKS.md` | 참조문서 |
| DK3.1-b1 | 전 모듈 stdlib 전용(서드파티 0, Py3.8+) | `templates/README.md#표준 라이브러리`, `templates/_common.py::optional_import` | 구현 |
| DK3.1-b2 | rolling z 현재값 제외·I-MR 표준식, Cpk σ·propose_rules 정렬 가정 주의 | `templates/anomaly/stats_detect.py::rolling_zscore`, `templates/spc/spc.py::cp_cpk`, `templates/_common.py::infer_interval` | 구현 |
| DK3.1-b3 | CPU 상, 행 단위 루프라 수백만 행은 느림 | `templates/README.md#규모:`, `templates/bigdata/` | 구현 |
| DK3.1-b4 | 떼어 쓰기 쉬우나 "통째 대체" 위험 최대 → 알고리즘만 재작성 | `templates/README.md#반입 규칙`, `docs/EXCLUDED.md#풍부한 완성 코드` | 의도적 제외 |
| DK3.1-b5 | setup.sh 세 곳 스킬 복사·AGENTS 병합·pip download 시도 | `docs/EXCLUDED.md#~/.agents/skills`, `docs/EXCLUDED.md#pip download` | 의도적 제외 |
| DK3.2-01 | check_data: 결측·타깃 분포·상관·시간 간격·학습/테스트 비교·민감열 마스킹 | `scripts/profile_data.py::profile`, `scripts/profile_data.py::questions`, `skills/hx-3-capability/references/data-audit.md#학습/평가` | 구현 |
| DK3.2-02 | features: 대상별 시간정렬 후 shift lag/rolling, fit/transform 분리 | `templates/ml/features.py::shift_then_roll`, `templates/ml/features.py::add_lag_roll`, `templates/ml/clean.py::fit_cleaner`, `templates/ml/clean.py::apply_cleaner` | 구현 |
| DK3.2-03 | train: 분할→기준선→후보→CV→비용 임계값→permutation importance | `templates/ml/split.py::time_split`, `templates/ml/baseline.py::dummy_model`, `templates/ml/baseline.py::fit_model`, `templates/ml/metrics.py::cost_threshold`, `templates/ml/metrics.py::permutation_importance` | 구현 |
| DK3.2-04 | analyze: 집계·그룹 비교·SQLite 교차검증·검정 | `templates/yield_/groupstats.py::defect_rate_by`, `templates/yield_/groupstats.py::chi_square`, `templates/bigdata/stream_agg.py::group_agg` | 구현 |
| DK3.2-05 | spc(numpy): I-MR·WE·Cp/Cpk·tracking signal | `templates/spc/spc.py::imr_fit`, `templates/spc/spc.py::western_electric`, `templates/spc/spc.py::cp_cpk`, `templates/ml/forecast.py::tracking_signal` | 구현 |
| DK3.2-06 | forecast: 수요 유형 분류→lag HGB→롤링 원점 백테스트→기준선 게이트 | `templates/ml/forecast.py::rolling_origin`, `templates/ml/forecast.py::backtest`, `templates/ml/forecast.py::baseline_gate`, `templates/ml/features.py::shift_then_roll`, `templates/ml/baseline.py::fit_model` | 구현 |
| DK3.2-07 | mlops/registry: 파일 기반 모델 등록·게이트·롤백 | `docs/EXCLUDED.md#MLOps` | 의도적 제외 |
| DK3.2-08 | mlops/serve: FastAPI 예측·드리프트 API | `docs/EXCLUDED.md#MLOps` | 의도적 제외 |
| DK3.2-09 | web-api: 입력 검증→규칙 판정→SQLite→조회 | `templates/web/server.py::serve`, `templates/web/server.py#post_routes`, `docs/PLAYBOOKS.md#10. 웹 대시보드` | 구현 |
| DK3.2-10 | static-tool: 빌드 없는 단일 HTML 도구 + node --test | `templates/web/server.py::write_static` | 구현 |
| DK3.2-11 | agent: 도구=순수함수, FakeLLM 기본, BM25 RAG | `docs/EXCLUDED.md#LLM 에이전트` | 의도적 제외 |
| DK3.2-12 | mcp/server: 읽기 전용 MCP 골격(pip mcp 필요) | `docs/EXCLUDED.md#LLM 에이전트` | 의도적 제외 |
| DK3.2-13 | harness: 비밀값 스캔(git 이력)·제출 형식 대조 | `scripts/presubmit.py::check_secrets`, `templates/contract/check_output.py::check` | 구현 |
| DK3.2-14 | ops: Dockerfile·compose·k8s·Jenkins | `docs/EXCLUDED.md#MLOps` | 의도적 제외 |
| DK3.2-b1 | 의존성 numpy·pandas·sklearn, lightgbm/xgboost 선택 import | `templates/ml/baseline.py::fit_model`, `templates/_common.py::optional_import`, `scripts/env_check.sh#5.3 Python 패키지` | 구현 |
| DK3.2-b2 | 데이터 계약별 분할 명시·shift(1) 누수 차단·"원인 아님" 주석, 시간 열 없으면 무작위 위험 | `templates/ml/split.py::assert_no_leak`, `templates/ml/features.py::shift_then_roll`, `skills/hx-3-capability/references/data-audit.md#분할 기준` | 구현 |
| DK3.2-b3 | CPU 상(HGB 중간 규모 표 데이터) | `skills/hx-3-capability/SKILL.md#유형 → 모듈`, `templates/ml/baseline.py::fit_model` | 구현 |
| DK3.2-b4 | 구조 완성도 최상이나 라이선스 없음 → 코드 복사 금지 | `templates/README.md#반입 규칙`, `NOTICE.md#PKJthecreator` | 구현 |
| DK3.2-b5 | 필요 파일만 복사·"복사만 한 commit" 분리, OpenAI는 키 있을 때만 | `templates/README.md#반입 규칙`, `docs/EXCLUDED.md#외부 LLM` | 구현 |
| DK3.3-01 | 수율 집계(키 중복·결측 검사)·고정 기준선 I-MR·"신호≠원인" 반환 | `templates/yield_/groupstats.py::yield_summary`, `templates/spc/spc.py::imr_fit`, `templates/spc/spc.py::imr_apply` | 구현 |
| DK3.3-02 | core: 요구사항 추적·검증 기록 헬퍼 | `state/VERIFICATION.md`, `scripts/verdict.py::main` | 구현 |
| DK3.3-03 | `python -m cofa_kit` CLI | `templates/README.md#제출물 진입점 예시` | 구현 |
| DK3.3-04 | 선택형 로컬 stdio MCP 어댑터 | `docs/EXCLUDED.md#LLM 에이전트` | 의도적 제외 |
| DK3.3-05 | install.py: 스킬만 복사·설정 미수정·심링크·충돌 거부 | `scripts/init_state.sh`, `tests/test_state.py::test_never_overwrites`, `docs/EXCLUDED.md#~/.agents/skills` | 구현 |
| DK3.3-06 | package.py: 허용 목록 기반 소스 ZIP | `docs/EXCLUDED.md#소스 ZIP` | 의도적 제외 |
| DK3.3-07 | 단위·통합·반도체 테스트 3종 | `templates/spc/test_spc.py`, `templates/yield_/test_groupstats.py` | 구현 |
| DK3.3-08 | 스킬 5개(semiconductor refs: data-contract·investigation·spc) | `skills/hx-3-capability/references/semiconductor/patterns.md`, `skills/hx-3-capability/references/semiconductor/spc.md`, `skills/hx-3-capability/references/semiconductor/glossary.md` | 참조문서 |
| DK3.3-09 | 예제 데이터(clean/dirty, expected.json) | `templates/spc/test_spc.py`, `templates/yield_/test_groupstats.py`, `templates/contract/check_output.py::gen_fixture` | 구현 |
| DK3.3-b1 | stdlib 전용(Py3.10+) | `templates/README.md#표준 라이브러리` | 구현 |
| DK3.3-b2 | 순환 판정 회피(기준선 고정)·결측/키 중복=오류 | `templates/spc/spc.py::imr_fit`, `templates/yield_/groupstats.py::yield_summary`, `skills/hx-3-capability/references/semiconductor/spc.md#기준선` | 구현 |
| DK3.3-b3 | CPU 상·적응 상·생성 직후라 당일 커밋 재확인 | `NOTICE.md` | 참조문서 |
| DK4-01 | verdict_engine(검증 0건=실패)·eda_bootstrap·test_template·preflight(Z 함정); ubinoqe 사본은 인용 안 함 | `scripts/verdict.py::main`, `scripts/profile_data.py::profile`, `scripts/env_check.sh#R9`, `templates/_common.py::parse_ts` | 구현 |
| DK4-02 | profile_data(다형식·nrows 상한) / setup.sh 시스템 패키지 보호 무시·저장소 초기화·자동 커밋 | `scripts/profile_data.py#--max-rows`, `docs/EXCLUDED.md#조용한 설치`, `tests/test_guardrails.py#PATTERNS` | 구현 |
| DK4-03 | data_audit·mapping_check·pdf_read·check_handoff / bootstrap --apply hook 생성 | `scripts/presubmit.py::check_notes`, `skills/hx-3-capability/references/data-audit.md`, `docs/EXCLUDED.md#hooks` | 구현 |
| DK4-04 | profile: 키 후보·개인정보 의심 열 / 파일 통째 read 주의 | `scripts/profile_data.py::questions`, `scripts/profile_data.py#PII_NAME` | 구현 |
| DK4-05 | profile·FastAPI/Next 스타터 / 브라우저 자동화 도구·LLM 키 경로·자동 커밋 | `scripts/profile_data.py::profile`, `docs/EXCLUDED.md#FastAPI`, `docs/EXCLUDED.md#브라우저 자동화` | 구현 |
| DK4-06 | profile_csv·compare_csv(종료코드 0/1/2)·조용한 누락 테스트 | `scripts/profile_data.py::profile`, `templates/reconcile/reconcile.py::main`, `templates/reconcile/reconcile.py::compare` | 구현 |
| DK4-07 | 대용량 스트리밍 프로파일+SQLite 디스크 집계 | `templates/bigdata/stream_agg.py::profile`, `templates/bigdata/stream_agg.py::group_agg` | 구현 |
| DK4-08 | node-http·fastapi 스캐폴드(도메인 없음) | `templates/web/server.py::serve`, `docs/EXCLUDED.md#FastAPI` | 구현 |
| DK4-09 | Node 내장 web-workbench / install-plugins·gstack-upgrade | `docs/EXCLUDED.md#Node helper`, `docs/EXCLUDED.md#보일러플레이트` | 의도적 제외 |
| DK4-10 | stdlib JSON API+SQLite, csv_check(값 미출력)·compare_json·security_check | `templates/web/server.py::serve`, `scripts/presubmit.py::check_secrets`, `scripts/profile_data.py#--no-values`, `templates/reconcile/reconcile.py::compare` | 구현 |
| DK4-11 | CSV→표 Node 서버 | `docs/EXCLUDED.md#Node` | 의도적 제외 |
| DK4-12 | stdlib JSON 저장 서버(도메인 없음) | `templates/web/server.py#post_routes` | 구현 |
| DK4-13 | Flask 앱 팩토리(flask·dotenv 필요) | `docs/EXCLUDED.md#Flask` | 의도적 제외 |
| DK4-14 | duckdb·ortools·pydantic-ai 런타임, 네트워크 research.py | `docs/EXCLUDED.md#ortools` | 의도적 제외 |
| DK4-15 | run_tests(증거 기록)·check_traceability(요구 추적) | `scripts/run_and_log.sh`, `state/VERIFICATION.md` | 구현 |
| DK4-16 | 노트북 템플릿·OCR·브라우저 자동화 도구 capture | `docs/EXCLUDED.md#OCR` | 의도적 제외 |
| DK4-17 | timer·handoff 도구 / hooks·`--search`·`--add-dir .git` | `skills/hx-next/SKILL.md`, `docs/EXCLUDED.md#--add-dir .git`, `tests/test_guardrails.py#PATTERNS` | 구현 |
| DK5-1 | 반도체 용어·분석 패턴·0.0.0.0 웹 스택 문서 | `skills/hx-3-capability/references/web-preview.md`, `skills/hx-3-capability/references/semiconductor/` | 참조문서 |
| DK5-2 | data-audit·honest-eval 체크리스트 | `skills/hx-3-capability/references/data-audit.md` | 참조문서 |
| DK5-3 | 분석 계획(분할·누수 칸)·실험 로그 양식 / 원격 OpenAI MCP | `state/TRIALS.md`, `docs/EXCLUDED.md#원격 MCP` | 구현 |
| DK5-4 | algorithm-optimizer 문서 | `templates/schedule/dispatch.py::compare_rules`, `docs/PLAYBOOKS.md#9. 스케줄링` | 구현 |
| DK5-5 | 담당자 요청형 웹 과제 스킬 13개 | `skills/hx-2-problem/references/interview.md` | 참조문서 |
| DK5-6 | ML 판단 문서(분할·누수·시계열 백테스트) | `templates/ml/split.py::time_split`, `templates/ml/forecast.py::rolling_origin`, `skills/hx-3-capability/references/data-audit.md` | 구현 |
| DK6-01 | SECOM XGBoost+SMOTE+SHAP 대시보드(무작위 분할 주의) | `skills/hx-3-capability/references/data-audit.md#무작위 분할`, `docs/EXCLUDED.md#SHAP` | 참조문서 |
| DK6-02 | 정제 규칙 학습 구간 fit/apply 분리 / UCI curl 다운로드 | `templates/ml/clean.py::fit_cleaner`, `templates/ml/clean.py::apply_cleaner`, `docs/EXCLUDED.md#UCI` | 구현 |
| DK6-03 | 그룹 누수 방지 평가 설계(대형) | `templates/ml/split.py::group_split`, `templates/ml/split.py::check_leak` | 구현 |
| DK6-04 | "Python이 결정, LLM은 설명"·데이터 부족이면 보류 / 외부 API 필수 | `AGENTS.md#판정은 코드`, `docs/EXCLUDED.md#외부 LLM` | 구현 |
| DK6-05 | WM-811K 웨이퍼맵(torch·대용량) | `docs/EXCLUDED.md#웨이퍼맵` | 의도적 제외 |
| DK6-06 | YOLO 웨이퍼 결함(GPU) | `docs/EXCLUDED.md#YOLO` | 의도적 제외 |
| DK6-07 | OpenCV 기준선 + U-Net, "기준선부터" | `docs/PLAYBOOKS.md`, `docs/EXCLUDED.md#U-Net` | 참조문서 |
| DK6-08 | 결정적 합성 데이터+정답 재계산 구조 | `templates/anomaly/events.py::synth_series`, `templates/contract/check_output.py::gen_fixture` | 구현 |
| DK6-09 | 독립 출력 계약 검증기(exit 0/1/2)·fixture 생성기 | `templates/contract/check_output.py::main`, `templates/contract/check_output.py::gen_fixture`, `scripts/verdict.py::main` | 구현 |
| DK6-10 | 학습용 EDA 예제 | `scripts/profile_data.py::profile`, `docs/PLAYBOOKS.md` | 참조문서 |
| DK6-11 | Decimal 냉각 조건 비교 CLI+테스트 | `templates/reconcile/reconcile.py::values_equal`, `docs/PLAYBOOKS.md#decimal.Decimal` | 참조문서 |
| DK6-12 | 1차 대비 합성 데이터 연습·WM-811K 출처 목록 | `docs/EXCLUDED.md#웨이퍼맵` | 의도적 제외 |
| DK8.1-01 | 표형 GBDT 분류·회귀 | `templates/ml/baseline.py::fit_model`, `skills/hx-3-capability/SKILL.md#유형 → 모듈` | 구현 |
| DK8.1-02 | 누수 방지 피처(lag/rolling) | `templates/ml/features.py::shift_then_roll`, `templates/ml/features.py::add_lag_roll`, `skills/hx-3-capability/SKILL.md#유형 → 모듈` | 구현 |
| DK8.1-03 | 센서 이상탐지(설명 가능 통계) | `templates/anomaly/stats_detect.py::rolling_zscore`, `templates/anomaly/rules.py::consecutive_rule`, `skills/hx-3-capability/SKILL.md#유형 → 모듈` | 구현 |
| DK8.1-04 | 지도학습·불균형 이상탐지 | `templates/ml/metrics.py::cost_threshold`, `templates/ml/metrics.py::roc_auc`, `templates/ml/split.py::stratified_split`, `skills/hx-3-capability/SKILL.md#유형 → 모듈` | 구현 |
| DK8.1-05 | SPC·관리도·Cp/Cpk | `templates/spc/spc.py::imr_fit`, `templates/spc/spc.py::cp_cpk`, `skills/hx-3-capability/SKILL.md#유형 → 모듈` | 구현 |
| DK8.1-06 | FDC·규칙 판정·경보 | `templates/anomaly/rules.py::evaluate_rows`, `templates/anomaly/events.py::alert_lifecycle`, `scripts/verdict.py::main` | 구현 |
| DK8.1-07 | 수율·불량 요인 분석 | `templates/yield_/groupstats.py::rank_factors`, `templates/yield_/groupstats.py::yield_summary`, `skills/hx-3-capability/SKILL.md#유형 → 모듈` | 구현 |
| DK8.1-08 | 시계열 예측 | `templates/ml/forecast.py::backtest`, `templates/ml/forecast.py::baseline_gate`, `docs/PLAYBOOKS.md#6. 시계열 예측` | 구현 |
| DK8.1-09 | 웨이퍼맵/이미지 분류 — CPU 적합 키트 없음 | `skills/hx-3-capability/SKILL.md#유형 → 모듈`, `docs/EXCLUDED.md#웨이퍼맵` | 의도적 제외 |
| DK8.1-10 | 평가·누수 검증 | `templates/ml/split.py::assert_no_leak`, `templates/anomaly/events.py::event_prf`, `skills/hx-3-capability/references/data-audit.md` | 구현 |
| DK8.1-11 | 데이터 프로파일·품질 | `scripts/profile_data.py::profile`, `scripts/profile_data.py::questions`, `templates/_common.py::infer_interval` | 구현 |
| DK8.1-12 | 대용량 데이터(16G 내) | `templates/bigdata/stream_agg.py::group_agg`, `templates/bigdata/stream_agg.py::reservoir_sample`, `templates/bigdata/stream_agg.py::external_sort` | 구현 |
| DK8.1-13 | 자료 대사·정합성 | `templates/reconcile/reconcile.py::compare` | 구현 |
| DK8.1-14 | 로그 파싱 | `templates/logparse/logparse.py::parse_lines`, `templates/logparse/logparse.py::group_events` | 구현 |
| DK8.1-15 | 스케줄링·최적화 | `templates/schedule/dispatch.py::dispatch`, `templates/schedule/dispatch.py::compare_rules`, `docs/EXCLUDED.md#ortools` | 구현 |
| DK8.1-16 | 시각화(의존성 0) | `templates/web/server.py::svg_line`, `templates/web/server.py::svg_bar` | 구현 |
| DK8.1-17 | 대시보드/웹앱 | `templates/web/server.py::serve`, `skills/hx-3-capability/references/web-preview.md` | 구현 |
| DK8.1-18 | 모델 운영(MLOps) | `docs/EXCLUDED.md#MLOps` | 의도적 제외 |
| DK8.1-19 | LLM 에이전트·RAG(키 없으면 대체) | `docs/EXCLUDED.md#LLM 에이전트` | 의도적 제외 |
| DK8.1-20 | 반도체 도메인 지식 | `skills/hx-3-capability/references/semiconductor/glossary.md`, `skills/hx-3-capability/references/semiconductor/patterns.md`, `skills/hx-3-capability/references/semiconductor/spc.md` | 참조문서 |
| DK8.2-1 | 센서 이상/FDC형: 규칙 엔진 판정, 임계값은 담당자 확정 | `templates/anomaly/rules.py::evaluate_rows`, `docs/PLAYBOOKS.md#2. 규칙·알림 판정`, `skills/hx-2-problem/references/interview.md` | 참조문서 |
| DK8.2-2 | 수율·불량 원인형: groupstats+yield_summary(키 중복·결측=오류) | `templates/yield_/groupstats.py::yield_summary`, `templates/yield_/groupstats.py::rank_factors`, `docs/PLAYBOOKS.md#4. 수율·불량 요인` | 구현 |
| DK8.2-3 | SPC형: 고정 기준선 I-MR + WE·Cpk | `templates/spc/spc.py::imr_fit`, `templates/spc/spc.py::western_electric`, `templates/spc/spc.py::cp_cpk`, `docs/PLAYBOOKS.md#3. SPC` | 구현 |
| DK8.2-4 | 예측형: 분할 계약·기준선 대비 게이트 | `templates/ml/split.py::time_split`, `templates/ml/forecast.py::baseline_gate`, `docs/PLAYBOOKS.md#5. 분류·회귀` | 구현 |
| DK8.2-5 | 웹 대시보드형: stdlib webapp 또는 FastAPI 있을 때 | `templates/web/server.py::serve`, `docs/PLAYBOOKS.md#10. 웹 대시보드` | 구현 |
| DK8.2-6 | 데이터 첫 점검: pandas/stdlib/대용량 3경로 | `scripts/profile_data.py::profile`, `templates/_common.py::optional_import`, `templates/bigdata/stream_agg.py::profile` | 구현 |
| DK8.3-01 | stdlib 이상탐지·SPC·규칙·이벤트 평가 함수(함수 단위 최소 반입) | `templates/anomaly/stats_detect.py::rolling_zscore`, `templates/spc/spc.py::imr_fit`, `templates/anomaly/rules.py::consecutive_rule`, `templates/anomaly/events.py::event_prf`, `NOTICE.md` | 구현 |
| DK8.3-02 | 고정 기준선 I-MR·수율 집계 | `templates/spc/spc.py::imr_fit`, `templates/yield_/groupstats.py::yield_summary`, `NOTICE.md` | 구현 |
| DK8.3-03 | 검증 0건=실패 판정기 | `scripts/verdict.py::main`, `NOTICE.md` | 구현 |
| DK8.3-04 | CSV 프로파일·키 대조 | `scripts/profile_data.py::profile`, `templates/reconcile/reconcile.py::compare`, `NOTICE.md` | 구현 |
| DK8.3-05 | 정직한 평가·데이터 감사 체크리스트(pstack 출처 동반) | `skills/hx-3-capability/references/data-audit.md`, `NOTICE.md` | 참조문서 |
| DK8.3-06 | ML 판단 문서 요약 | `skills/hx-3-capability/references/data-audit.md`, `NOTICE.md` | 참조문서 |
| DK8.3-07 | 분할 계약·누수 방지 피처·롤링 백테스트·비용 임계값 | `templates/ml/split.py::time_split`, `templates/ml/features.py::shift_then_roll`, `templates/ml/forecast.py::backtest`, `templates/ml/metrics.py::cost_threshold`, `NOTICE.md` | 구현 |
| DK8.3-08 | 스트리밍 프로파일·디스크 집계 | `templates/bigdata/stream_agg.py::profile`, `templates/bigdata/stream_agg.py::group_agg`, `NOTICE.md#HyeongiJeon` | 구현 |
| DK8.3-09 | 정제 규칙 학습/적용 분리 | `templates/ml/clean.py::fit_cleaner`, `templates/ml/clean.py::apply_cleaner`, `NOTICE.md#NE0NMIKE` | 구현 |
| DK8.3-10 | 출력 계약 독립 검증기 | `templates/contract/check_output.py::check`, `NOTICE.md` | 구현 |
| DK8.3-11 | 반도체 용어·분석 패턴 | `skills/hx-3-capability/references/semiconductor/`, `NOTICE.md` | 참조문서 |
| DK8.3-12 | 데이터 프로파일러(pandas, 행 상한) — setup.sh는 쓰지 않음 | `scripts/profile_data.py#--max-rows`, `docs/EXCLUDED.md#setup` | 구현 |
| DK8.4-1 | pandas(8) 존재 확인 | `scripts/env_check.sh#5.3 Python 패키지`, `templates/_common.py::optional_import`, `templates/ml/features.py::pandas_lag_roll` | 구현 |
| DK8.4-2 | fastapi(5)·uvicorn·pydantic → 없으면 http.server | `scripts/env_check.sh#5.3 Python 패키지`, `templates/web/server.py::serve` | 구현 |
| DK8.4-3 | numpy·scikit-learn(3) → 없으면 stdlib 통계 | `scripts/env_check.sh#5.3 Python 패키지`, `scripts/env_check.sh#R5`, `templates/ml/baseline.py::fit_model` | 구현 |
| DK8.4-4 | 브라우저 자동화 도구(3): 브라우저 다운로드 필요 → 쓰지 않음 | `docs/EXCLUDED.md#브라우저 자동화`, `tests/test_guardrails.py#browser-automation` | 의도적 제외 |
| DK8.4-5 | pypdf·pdfplumber·openpyxl: 문서·엑셀 입력 과제 대비 | `scripts/env_check.sh#5.3 Python 패키지`, `scripts/profile_data.py` | 구현 |
| DK8.4-6 | xgboost·lightgbm 선택 import | `scripts/env_check.sh#5.3 Python 패키지`, `templates/_common.py::optional_import` | 구현 |
| DK8.4-7 | matplotlib·joblib·pytest·mcp·starlette | `scripts/env_check.sh#5.3 Python 패키지` | 구현 |
| DK8.4-8 | 단발 의존성(scipy·shap·streamlit·duckdb·torch 등) | `scripts/env_check.sh#5.3 Python 패키지`, `docs/EXCLUDED.md#SHAP` | 구현 |
| DK8.4-9 | 함께 확인: pip 가능·시스템 패키지 보호 무시 필요 여부·Py/Node 버전·소켓·clone·루트 경로 | `scripts/env_check.sh#5.2 런타임`, `scripts/env_check.sh#5.4 네트워크`, `scripts/env_check.sh#5.6 워크스페이스`, `docs/ENV_FACTS.md` | 구현 |
| DK8.4-10 | stdlib 전용 레포 목록(wildrage98·ripplelover·hamjoon2003 등 9) | `templates/README.md#표준 라이브러리`, `NOTICE.md` | 참조문서 |
| DK8.5-1 | 당일 clone 후보1 wildrage98: setup.sh 실행 금지, 읽기·재작성 참고 | `templates/README.md#반입 규칙`, `NOTICE.md#wildrage98`, `docs/EXCLUDED.md#pip download` | 구현 |
| DK8.5-2 | 후보2 PKJ: ML 기준서, 코드 복사 금지 | `templates/ml/split.py::time_split`, `NOTICE.md#PKJthecreator` | 구현 |
| DK8.5-3 | 후보3 ripplelover: 작고 설명 쉬움, 커밋 재확인 | `templates/spc/spc.py::imr_fit`, `NOTICE.md#ripplelover` | 구현 |
| DK8.5-4 | 공통: clone 직후 rev-parse HEAD를 결정 기록, 대안 1개 준비 | `scripts/init_state.sh#rev-parse`, `state/DECISIONS.md`, `README.md` | 구현 |
| DK9-1 | curl/bash 0건, 외부 다운로드(UCI curl·pip download·브라우저 자동화 도구 설치) 회피 | `tests/test_guardrails.py#curl-pipe-sh`, `docs/EXCLUDED.md#외부 다운로드` | 의도적 제외 |
| DK9-2 | 시스템 패키지 보호 무시 플래그 금지 | `AGENTS.md#1. 금지`, `scripts/env_check.sh#R4`, `tests/test_guardrails.py` | 의도적 제외 |
| DK9-3 | 외부 LLM/API 호출 경로 금지(OpenAI·Nemotron·원격 MCP) | `AGENTS.md#1. 금지`, `docs/EXCLUDED.md`, `tests/test_guardrails.py` | 의도적 제외 |
| DK9-4 | 텔레메트리 없음 유지 | `tests/test_guardrails.py#test_no_outbound_network_in_code`, `docs/EXCLUDED.md#텔레메트리` | 의도적 제외 |
| DK9-5 | 자동 git 조작(init·자동 커밋·AGENTS 병합) 금지 | `AGENTS.md#1. 금지`, `scripts/init_state.sh`, `AGENTS.md#4. 상태 파일`, `tests/test_guardrails.py` | 의도적 제외 |
| DK9-6 | 브라우저 자동 조작(Computer Use 회색지대) 금지 | `AGENTS.md#1. 금지`, `docs/EXCLUDED.md#브라우저 자동화`, `tests/test_guardrails.py#browser-automation` | 의도적 제외 |
| DK9-7 | 무단 사본(ubinoqe)은 인용하지 않고 원본만 | `NOTICE.md`, `docs/EXCLUDED.md#ubinoqe` | 의도적 제외 |
| DK10-1 | 정적 판독 한계 → 반입 모듈은 하네스 테스트로 재검증 | `tests/`, `templates/README.md#테스트` | 구현 |
| DK10-2 | 대용량·바이너리 미수집 범위 있음 | `NOTICE.md` | 참조문서 |
| DK10-3 | 검색 누락·지연 가능 → 당일 커밋 해시 재확인 | `README.md`, `NOTICE.md` | 참조문서 |
| DK10-4 | 환경 사실은 2차 기록 → 실측 우선 | `scripts/env_check.sh`, `docs/ENV_FACTS.md` | 구현 |
| AR1A-1 | OS·커널·아키텍처(`uname -srm`, os-release) | `scripts/env_check.sh#5.1 OS` | 구현 |
| AR1A-2 | CPU 코어와 cgroup 할당량(cpu.max / cfs_quota) | `scripts/env_check.sh#3. 표시값 vs 실측`, `scripts/env_check.sh#cfs_quota`, `scripts/env_check.sh#cpu.max` | 구현 |
| AR1A-3 | 메모리 총량·가용·cgroup 한도 | `scripts/env_check.sh#3. 표시값 vs 실측`, `scripts/env_check.sh#memory.limit_in_bytes`, `scripts/env_check.sh#R13` | 구현 |
| AR1A-4 | GPU 유무·VRAM(`nvidia-smi`, /dev/nvidia*) | `scripts/env_check.sh#5.1 OS`, `scripts/env_check.sh#R6` | 구현 |
| AR1A-5 | 디스크 여유(`.`·/tmp)와 inode | `scripts/env_check.sh#inode`, `scripts/env_check.sh#R11` | 구현 |
| AR1A-6 | 가상화·컨테이너 식별(.dockerenv, /proc/1/environ) | `scripts/env_check.sh#dockerenv` | 구현 |
| AR1B-1 | Python 런타임·venv·uv/conda/poetry | `scripts/env_check.sh#5.2 런타임`, `scripts/env_check.sh#R4` | 구현 |
| AR1B-2 | pip 버전·캐시 디렉터리·로컬 wheel 탐색 | `scripts/env_check.sh#pip cache dir` | 구현 |
| AR1B-3 | 핵심 ML 패키지 개별 import·버전 | `scripts/env_check.sh#5.3 Python 패키지`, `scripts/env_check.sh#R5` | 구현 |
| AR1B-4 | Node·npm·pnpm/yarn/bun/원격 패키지 실행기 | `scripts/env_check.sh#5.2 런타임` | 구현 |
| AR1B-5 | 컴파일러·CLI 도구(gcc, make, jq, sqlite3, duckdb, java/go/rustc) | `scripts/env_check.sh#5.2 런타임` | 구현 |
| AR1C-1 | 프록시·인증서 환경변수(값 마스킹) | `scripts/env_check.sh#5.4 네트워크` | 구현 |
| AR1C-2 | pip.conf·.npmrc·.condarc 미러 설정 | `scripts/env_check.sh#5.4 네트워크` | 구현 |
| AR1C-3 | 레지스트리별 HEAD 응답 코드(2초) | `scripts/env_check.sh#5.4 네트워크`, `scripts/env_check.sh#R3`, `scripts/env_check.sh#R4` | 구현 |
| AR1C-4 | DNS 해석(`getent hosts`) | `scripts/env_check.sh#getent` | 구현 |
| AR1D-1 | Codex 경로·버전 | `scripts/env_check.sh#5.5 Codex` | 구현 |
| AR1D-2 | `codex --help` 플래그·서브커맨드 파싱 | `scripts/env_check.sh#5.5 Codex`, `scripts/env_check.sh#R12` | 구현 |
| AR1D-3 | config 모델·provider·approval·mcp(키 마스킹), Astra 기본값 확인 | `scripts/env_check.sh#5.5 Codex`, `scripts/env_check.sh#R14` | 구현 |
| AR1D-4 | 비대화형(서브에이전트) 호출 가능 여부 | `scripts/env_check.sh#CODEX_EXEC`, `scripts/env_check.sh#R12` | 구현 |
| AR1D-5 | skills·AGENTS·MCP 인식 구조 탐색 | `scripts/env_check.sh#5.5 Codex`, `scripts/env_check.sh#R15` | 구현 |
| AR1E-1 | 워크스페이스 경로·쓰기 권한·인접 데이터 폴더 | `scripts/env_check.sh#5.6 워크스페이스`, `scripts/env_check.sh#R1` | 구현 |
| AR1E-2 | 데이터 파일 인벤토리·크기(maxdepth 3) | `scripts/env_check.sh#5.7 데이터 후보`, `scripts/env_check.sh#--data-dir` | 구현 |
| AR1E-3 | 데이터 샘플 요약(크기 확인 후 head/wc) | `scripts/env_check.sh#5.7 데이터 후보` | 구현 |
| AR1E-4 | 문제지·가이드 문서 탐지 | `scripts/env_check.sh#5.6 워크스페이스` | 구현 |
| AR1E-5 | git status·remote·hooks | `scripts/env_check.sh#5.6 워크스페이스`, `scripts/env_check.sh#R2`, `tests/test_env_check.py::test_git_remote_warning_and_masking` | 구현 |
| AR1F-1 | ulimit·pids.max | `scripts/env_check.sh#5.8 한도`, `scripts/env_check.sh#R7` | 구현 |
| AR1F-2 | 로컬 바인딩 시험(socket bind 0) | `scripts/env_check.sh#5.8 한도`, `scripts/env_check.sh#R8` | 구현 |
| AR1F-3 | 웹 IDE 미리보기 관련 env 키 | `scripts/env_check.sh#5.8 한도` | 구현 |
| AR1G-1 | 스크립트 감지 가능 제약(root, ro 마운트, 외부 통신, remote) | `scripts/env_check.sh#5.1 OS`, `scripts/env_check.sh#5.4 네트워크`, `scripts/env_check.sh#5.6 워크스페이스` | 구현 |
| AR1G-2 | 스크립트 감지 불가 5종(전체화면, 클립보드, 단축키, Astra 차단 방식, 업·다운로드 UI) | `scripts/env_check.sh#7. 사람 전용 체크리스트`, `docs/ENV_FACTS.md` | 구현 |
| AR2-01 | PyPI/npm·미러 접속 가능 여부로 설치 전략 분기 | `scripts/env_check.sh#R3`, `scripts/env_check.sh#R4` | 구현 |
| AR2-02 | 사전 설치 ML 패키지로 모델 노선 결정 | `scripts/env_check.sh#R5`, `skills/hx-3-capability/SKILL.md#유형 → 모듈` | 구현 |
| AR2-03 | 비대화형 Codex 지원 시 백그라운드 병렬 서브에이전트 | `scripts/env_check.sh#R12`, `skills/hx-4-trials/references/parallel.md` | 구현 |
| AR2-04 | 기본 모델이 Astra면 `-m` 강제 지정하도록 스킬 수정 | `AGENTS.md#1. 금지`, `scripts/env_check.sh#R14`, `docs/EXCLUDED.md#모델 고정`, `tests/test_guardrails.py#model-pin` | 의도적 제외 |
| AR2-05 | GPU 유무로 딥러닝/GBDT 노선 | `scripts/env_check.sh#R6` | 구현 |
| AR2-06 | cgroup 메모리 작으면 다운캐스팅·청크·sqlite | `scripts/env_check.sh#R10`, `scripts/env_check.sh#R13`, `templates/bigdata/` | 구현 |
| AR2-07 | pids.max 낮으면 OMP/n_jobs 상한 | `scripts/env_check.sh#R7` | 구현 |
| AR2-08 | 데이터 규모별 반복 실험 전략 | `scripts/env_check.sh#R10`, `skills/hx-3-capability/references/data-audit.md` | 구현 |
| AR2-09 | 디스크 부족 시 중간 산출물 최소화 | `scripts/env_check.sh#R11` | 구현 |
| AR2-10 | clone 직후 origin 살아 있으면 하네스 clone의 origin 제거 | `scripts/env_check.sh#R2`, `README.md#첫 5분` | 구현 |
| AR3-1 | 포트 스캔·과도한 요청·ps 전체 스캔·Codex 업데이트 오탐 회피 | `scripts/env_check.sh`, `tests/test_guardrails.py` | 구현 |
| AR3-2 | env·config 덤프로 비밀값 유출 방지(마스킹) | `scripts/env_check.sh`, `tests/test_env_check.py::test_secrets_are_masked` | 구현 |
| AR3-3 | 멈춤 방지(명령별 timeout, stdin 차단, maxdepth, 크기 제한, 10초 목표) | `scripts/env_check.sh`, `tests/test_env_check.py::test_quick_is_fast` | 구현 |
| AR3-4 | 읽기 전용 원칙(출력 파일 하나, 쓰기 시험은 `-w`) | `scripts/env_check.sh`, `tests/test_env_check.py::test_out_creates_only_that_file` | 구현 |
| AR3-5 | ENVIRONMENT.md 공개 레포 커밋 방지·push 경고 | `.gitignore`, `scripts/env_check.sh#R2`, `scripts/presubmit.py::check_env_file` | 구현 |
| AR4-1 | 후보: 순수 POSIX sh | `scripts/env_check.sh`, `tests/test_env_check.py::test_runs_without_python_on_path` | 구현 |
| AR4-2 | 후보: 순수 python3 | `tests/test_env_check.py::test_runs_without_python_on_path`, `docs/EXCLUDED.md#순수 python3` | 의도적 제외 |
| AR4-3 | 후보: sh + 조건부 python 스니펫 | `scripts/env_check.sh`, `tests/test_env_check.py::test_runs_without_python_on_path` | 구현 |
| AR4-4 | 최종 추천: 하이브리드 단일 `scripts/env_check.sh` | `scripts/env_check.sh` | 구현 |
| AR5o-1 | `--out PATH`(기본 ./ENVIRONMENT.md) | `scripts/env_check.sh#--out`, `tests/test_env_check.py::test_default_out_is_environment_md` | 구현 |
| AR5o-2 | `--stdout` | `scripts/env_check.sh#--stdout`, `tests/test_env_check.py::test_stdout_mode_writes_nothing` | 구현 |
| AR5o-3 | `--quick` | `scripts/env_check.sh#--quick`, `tests/test_env_check.py::test_quick_is_fast` | 구현 |
| AR5o-4 | `--no-network` | `scripts/env_check.sh#--no-network`, `tests/test_env_check.py::test_standard_no_network_writes_nothing` | 구현 |
| AR5o-5 | `--data-dir` | `scripts/env_check.sh#--data-dir`, `tests/test_env_check.py::test_data_inventory_and_extra_dir` | 구현 |
| AR5s-1 | TL;DR 신호등 요약 표 | `scripts/env_check.sh#1. 종합 판정` | 구현 |
| AR5s-2 | 판정 규칙 `[ACTIVE]` 강제 행동 표 | `scripts/env_check.sh#R0`, `scripts/env_check.sh#R16`, `scripts/env_check.sh#2. 판정 규칙` | 구현 |
| AR5s-3 | 서술형용 환경 근거 자동 문장 | `scripts/env_check.sh#4. 서술형용 환경 사실`, `state/ESSAY_PREP.md` | 구현 |
| AR5s-4 | 상세 4.1 하드웨어·한도 | `scripts/env_check.sh#5.1 OS`, `scripts/env_check.sh#5.8 한도` | 구현 |
| AR5s-5 | 상세 4.2 런타임·라이브러리 버전 표 | `scripts/env_check.sh#5.2 런타임`, `scripts/env_check.sh#5.3 Python 패키지` | 구현 |
| AR5s-6 | 상세 4.3 네트워크·미러 | `scripts/env_check.sh#5.4 네트워크` | 구현 |
| AR5s-7 | 상세 4.4 Codex 플래그·스킬 경로 | `scripts/env_check.sh#5.5 Codex` | 구현 |
| AR5s-8 | 상세 4.5 데이터 인벤토리(헤더 샘플) | `scripts/env_check.sh#5.7 데이터 후보` | 구현 |
| AR5s-9 | 사람 전용 수동 체크리스트 | `scripts/env_check.sh#7. 사람 전용 체크리스트` | 구현 |
| AR5s-10 | 수치 나열보다 명령형 지침이 에이전트 준수율을 높인다는 평가 | `scripts/env_check.sh#2. 판정 규칙`, `skills/hx-1-env/SKILL.md` | 구현 |
| AR6-1 | clone 후 remote 미제거 위험 | `scripts/env_check.sh#R2`, `README.md#첫 5분` | 구현 |
| AR6-2 | 워크스페이스 위 clone 충돌 → 하위 폴더 clone | `README.md#첫 5분` | 구현 |
| AR6-3 | 병렬 레이스·자원 고갈 → `exp/<n>` 격리·스레드 주입 | `skills/hx-4-trials/SKILL.md`, `scripts/env_check.sh#R7`, `skills/hx-4-trials/references/parallel.md#격리 규칙` | 구현 |
| AR6-4 | 서술형 대비 수치 포함 3줄 상시 갱신·확정 전 숙독 | `skills/hx-6-final/SKILL.md`, `state/ESSAY_PREP.md` | 구현 |
| AR6-5 | 사전 체험≠본 시험 → 시작 시 재실행·diff | `scripts/env_check.sh#--diff`, `tests/test_env_check.py::test_diff_reports_changed_keys`, `README.md#첫 5분` | 구현 |
| AR6s-A | 사전 체험 15분 순서(--stdout, codex --help, 수동 확인) | `scripts/env_check.sh#--stdout`, `docs/ENV_FACTS.md#5. 사전 체험` | 구현 |
| AR6s-B | 본 시험 첫 3분 순서(clone→remote 제거→env_check→판독→첫 지시) | `README.md#첫 5분` | 구현 |
| CE-F1 | 터미널 `~/workspace`, 탐색기 루트 Workspace(예시 화면) | `scripts/env_check.sh#5.6 워크스페이스`, `docs/ENV_FACTS.md` | 구현 |
| CE-F2 | 상단 `450M/16G` 표시, 자원 부족 시 강제 종료 | `scripts/env_check.sh#R13`, `scripts/env_check.sh#3. 표시값 vs 실측` | 구현 |
| CE-F3 | 미리보기 `*-local-only.e2b.app`, 0.0.0.0 바인딩, 포트 입력식 | `scripts/env_check.sh#R8`, `templates/web/`, `skills/hx-3-capability/references/web-preview.md` | 구현 |
| CE-F4 | 비활성 pause·재연결, 타이머 계속, 중복 접속 90초 | `scripts/env_check.sh#R0`, `scripts/run_and_log.sh#trap`, `skills/hx-4-trials/references/rescue.md#세션 복원`, `skills/hx-3-capability/references/web-preview.md` | 구현 |
| CE-F5 | PC 업로드 불가, Git clone 허용, push 불가·외부 전송 금지 | `AGENTS.md#1. 금지`, `docs/RULES.md` | 구현 |
| CE-F6 | `codex` 실행, `/status`·`/model`, 기본 승인 요청, 권장 모델·Astra 제한 | `scripts/env_check.sh#7. 사람 전용 체크리스트`, `README.md#첫 5분` | 구현 |
| CE-F7 | MCP 탭 JSON 설정이 Codex 설정에 반영 | `scripts/env_check.sh#5.5 Codex` | 구현 |
| CE-F8 | 터미널 탭 분할, Ctrl+Shift+V | `scripts/env_check.sh#7. 사람 전용 체크리스트` | 구현 |
| CE-F9 | 회차별 도구 상이, 이번 SK는 Codex만 | `AGENTS.md#1. 금지`, `scripts/env_check.sh#5.2 런타임` | 구현 |
| CE-F10 | 7월 후기: E2B 웹 IDE·bash | `docs/ENV_FACTS.md` | 참조문서 |
| CE-F11 | 정책 페이지: AWS 미국, 보유 14일 | `scripts/env_check.sh#5.4 네트워크`, `scripts/env_check.sh#R16`, `tests/test_env_check.py::test_non_kst_container_clock_is_flagged` | 구현 |
| CE-F12 | 업로드 한도 문자열, 이번 회차 업로드 불가 | `docs/ENV_FACTS.md` | 참조문서 |
| CE-F13 | 제출 시 git 로그+diff가 평가 입력 | `scripts/env_check.sh#5.6 워크스페이스`, `AGENTS.md#4. 상태 파일` | 구현 |
| CE-F14 | 크래프톤 공개 템플릿 없음 | `docs/ENV_FACTS.md` | 참조문서 |
| CE-E1 | E2B는 Firecracker microVM, GPU 없음 | `scripts/env_check.sh#R6` | 구현 |
| CE-E2 | base 템플릿 Debian, Python/Node/git, 기본 2vCPU·512MiB | `docs/ENV_FACTS.md` | 참조문서 |
| CE-E3 | 기본 사용자 user, 홈 /home/user, bash | `scripts/env_check.sh#5.1 OS` | 구현 |
| CE-E4 | 아웃바운드 기본 허용·도메인 필터, TCP 성공≠허용 | `scripts/env_check.sh#5.4 네트워크` | 구현 |
| CE-E5 | 포트별 공개 URL, 0.0.0.0 | `skills/hx-3-capability/references/web-preview.md` | 참조문서 |
| CE-E6 | pause 시 파일·메모리 보존, 재연결 필요 | `state/HANDOFF.md`, `skills/hx-4-trials/references/rescue.md` | 구현 |
| CE-E7 | Codex 예제 Codex 비대화형 실행+승인 완화 플래그, 세션 `~/.codex/sessions` | `scripts/env_check.sh#R12`, `docs/EXCLUDED.md#백그라운드 병렬` | 의도적 제외 |
| CE-I1 | OS는 Linux | `scripts/env_check.sh#5.1 OS` | 구현 |
| CE-I2 | Debian/Ubuntu, 관리자 권한 없을 수 있음 | `scripts/env_check.sh#5.1 OS`, `scripts/env_check.sh#dpkg` | 구현 |
| CE-I3 | 셸 bash | `scripts/env_check.sh` | 구현 |
| CE-I4 | 비 root `user`, 작업 폴더 미확정 | `scripts/env_check.sh#5.1 OS`, `scripts/env_check.sh#5.6 워크스페이스` | 구현 |
| CE-I5 | 16GB 표시, vCPU·디스크 미상 | `scripts/env_check.sh#R7`, `scripts/env_check.sh#3. 표시값 vs 실측` | 구현 |
| CE-I6 | GPU 없음 | `scripts/env_check.sh#R6` | 구현 |
| CE-I7 | 인터넷 일부 허용, PyPI/npm 미확인 | `scripts/env_check.sh#5.4 네트워크`, `scripts/env_check.sh#R3`, `scripts/env_check.sh#R4` | 구현 |
| CE-I8 | Python·Node 사전 설치 가능성, 버전 미상 | `scripts/env_check.sh#5.2 런타임` | 구현 |
| CE-I9 | Codex PATH 존재, 인증은 플랫폼 주입, 업데이트 금지 | `scripts/env_check.sh#5.5 Codex`, `tests/test_guardrails.py` | 구현 |
| CE-I10 | 사전 체험·본 시험 템플릿 차이 가능 | `scripts/env_check.sh#--diff` | 구현 |
| CE-I11 | 프로세스·FD 한도 미상 | `scripts/env_check.sh#5.8 한도` | 구현 |
| CE3-1 | 미확인: 배포판·커널·CPU·디스크 | `scripts/env_check.sh#5.1 OS`, `scripts/env_check.sh#3. 표시값 vs 실측` | 구현 |
| CE3-2 | 미확인: 런타임 버전·install 성공 여부 | `scripts/env_check.sh#5.2 런타임`, `scripts/env_check.sh#5.4 네트워크` | 구현 |
| CE3-3 | 미확인: 허용 도메인·DNS·프록시 | `scripts/env_check.sh#5.4 네트워크` | 구현 |
| CE3-4 | 미확인: Codex 버전·config·모델·스킬 인식 | `scripts/env_check.sh#5.5 Codex`, `scripts/env_check.sh#7. 사람 전용 체크리스트` | 구현 |
| CE3-5 | 미확인: 미리보기 포트 범위·WebSocket | `scripts/env_check.sh#7. 사람 전용 체크리스트` | 구현 |
| CE3-6 | 미확인: 다운로드 기능·용량 | `scripts/env_check.sh#7. 사람 전용 체크리스트` | 구현 |
| CE3-7 | 미확인: pause 임계·세션 최대 시간 | `docs/ENV_FACTS.md` | 참조문서 |
| CE3-8 | 이전 SK 회차 후기 부재 | `docs/ENV_FACTS.md` | 참조문서 |
| CE3-9 | cofa.krafton.ai NXDOMAIN, 개인 링크 미접속 | `docs/ENV_FACTS.md` | 참조문서 |
| CE3-10 | mcp-bridge·hoonjet 증거 불사용 | `docs/EXCLUDED.md#hoonjet` | 의도적 제외 |
| CE4-1 | POSIX 호환 bash 하나, python 없이도 MD | `scripts/env_check.sh` | 구현 |
| CE4-2 | 비 root·관리자 권한 없음 가정, 시스템 변경 없음 | `scripts/env_check.sh`, `tests/test_env_check.py::test_no_state_changing_commands_in_script` | 구현 |
| CE4-3 | 표시값과 실측 둘 다, 병렬 수 메모리 기준 | `scripts/env_check.sh#R7`, `scripts/env_check.sh#3. 표시값 vs 실측` | 구현 |
| CE4-4 | 네트워크는 도메인별 HTTP 코드+ms | `scripts/env_check.sh#5.4 네트워크` | 구현 |
| CE4-5 | 서버 0.0.0.0, localhost 금지 한 줄 | `scripts/env_check.sh#R0`, `scripts/env_check.sh#R8`, `skills/hx-3-capability/references/web-preview.md` | 구현 |
| CE4-6 | 장시간 프로세스 재시작 가능, 산출물 파일로 | `templates/web/`, `skills/hx-4-trials/references/rescue.md` | 구현 |
| CE4-7 | Codex 점검 읽기 전용, 업데이트 금지 명시 | `AGENTS.md#1. 금지`, `scripts/env_check.sh` | 구현 |
| CE4-8 | git 저장소·로그 확인, remote 경고만 | `scripts/env_check.sh#5.6 워크스페이스`, `scripts/env_check.sh#R2` | 구현 |
| CE4-9 | GPU 없음 전제, nvidia-smi 존재만 | `scripts/env_check.sh#R6` | 구현 |
| CE4-10 | 사전 체험 실측 질문 목록(os-release…ss -ltn, 수동 서버 확인) | `scripts/env_check.sh#7. 사람 전용 체크리스트`, `scripts/env_check.sh#ss -ltn`, `docs/ENV_FACTS.md#5. 사전 체험` | 구현 |
| AC-01 | 13스킬·8상태 파일 과설계 → 스킬 7·상태 3~4 축소안 | `skills/README.md`, `scripts/init_state.sh#--extra`, `CAPABILITIES.md`, `docs/EXCLUDED.md#13개 스킬` | 구현 |
| AC-02 | 60여 파일 구현 분해의 시간 초과 → P0 필수/P1 선택 | `CAPABILITIES.md` | 참조문서 |
| AC-03 | `/tmp/_harness` 읽기 차단 시 즉시 워크스페이스로 이동 | `README.md#첫 5분` | 구현 |
| AC-04 | 컨테이너 시계 UTC 가능성 → 시각 KST 강제·화면 잔여 분 입력 기본 | `scripts/env_check.sh#5.1 OS`, `scripts/env_check.sh#R16`, `skills/hx-next/SKILL.md`, `README.md#첫 5분` | 구현 |
| AC-05 | 제출 폴더의 templates 직접 import·행 단위 과다 복사 경고, 반입 시 "무엇을 바꿨나" 기록 | `scripts/presubmit.py::check_harness`, `scripts/presubmit.py::check_copy`, `templates/README.md#반입 규칙`, `state/DECISIONS.md` | 구현 |
| AC-06 | K7과 R12·§2.3·O8의 Codex 비대화형 실행 조건부 허용 모순 → exec 병렬 배제 단일 기준 | `scripts/env_check.sh#R12`, `docs/EXCLUDED.md#백그라운드 병렬` | 구현 |
| AC-07 | 과제 AGENTS 불변(K1·§3.3)과 O13 추천 모순 → 수정 금지 기본 | `AGENTS.md#1. 금지`, `docs/EXCLUDED.md#과제 AGENTS.md 병합` | 구현 |
| AC-08 | 첫 30분 문서화 편중 → 환경·문제·프로파일 T+15, E2E T+15~40 | `skills/hx-next/SKILL.md#체크포인트`, `AGENTS.md#5. 시간`, `docs/TIMELINE.md` | 구현 |
| AC-09 | git 이력(`git log -p`) 비밀값 스캔, GitHub/MCP 언급 주의 | `scripts/presubmit.py::check_secrets`, `skills/hx-2-problem/references/interview.md`, `docs/PROMPTS.md#6. 담당자 메신저`, `tests/test_guardrails.py::test_secret_in_git_history` | 구현 |
| AC-10 | cgroup v1 폴백, run_and_log 무버퍼·시그널 트랩 | `scripts/env_check.sh#CGROUP`, `scripts/run_and_log.sh#trap`, `tests/test_guardrails.py::test_signals_recorded` | 구현 |
| AC-11 | ENVIRONMENT.md 워크스페이스 커밋 시 환경 정보 노출 → 기본 비커밋 | `.gitignore`, `scripts/presubmit.py::check_env_file` | 구현 |
| AC-12 | §4.3 비고 "추가 필요·미기재" 9건이 이미 반영된 내용 | `scripts/env_check.sh#5.1 OS`, `scripts/env_check.sh#5.2 런타임`, `scripts/env_check.sh#R0` | 구현 |
| AC-13 | 근거 문서 경로 표기 불일치 | `docs/EXCLUDED.md#근거:` | 참조문서 |
| AC-14 | answndud 스킬 개수 8/9 불일치 | `NOTICE.md#answndud` | 참조문서 |
| AC-15 | 토큰 사용 간접 평가 대응이 선언뿐 → `/status` 점검·병렬 1 축소 | `skills/hx-next/SKILL.md#토큰 점검`, `state/STATE.md#토큰 점검 기록` | 구현 |

## 이번에 채운 누락

매핑하다가 대응이 없던 강점을 그 자리에서 채운 것(2026-10-31, 차용 없음, 각 함수에 unittest).

| ID | 채운 것 | 파일 |
|---|---|---|
| DK3.1-08, DK8.1-06 | 경보 생명주기 상태머신 `alert_lifecycle`(열기 n회·닫기 m회) | `templates/anomaly/events.py` |
| DK3.1-09, DK8.1-10, DK8.3-01 | 사건/시점 단위 P·R·F `event_prf`(같은 설비끼리·허용 오차)·`point_prf` | `templates/anomaly/events.py` |
| DK3.1-17, DK6-08, DK3.1-19 | 결정적 합성 센서 + 이상 주입 + 정답표 `synth_series` | `templates/anomaly/events.py` |
| DK3.2-06, DK8.1-08, DK8.2-4, DK8.3-07, DK5-6 | 롤링 원점 백테스트·기준선 게이트 `rolling_origin`·`backtest`·`baseline_gate`·`naive`·`seasonal_naive` | `templates/ml/forecast.py` |
| DK3.2-05 | `tracking_signal`(예측 편향) | `templates/ml/forecast.py` |
| DK3.2-03 | `permutation_importance` | `templates/ml/metrics.py` |
| DK3.3-01, DK8.2-2, DK8.3-02 | `yield_summary`(키 중복·결측·passed>tested = 오류, 가중 수율, 원인 아님) | `templates/yield_/groupstats.py` |
| DK3.1-02, DK3.1-b2 | `infer_interval`(정렬 여부·중앙 간격·공백·중복 시각) | `templates/_common.py` |
| DK3.1-14 | `md_table`(리포트용 마크다운 표) | `templates/_common.py` |
| DK3.1-15, DK8.1-16 | `svg_bar`(의존성 없는 막대 차트) | `templates/web/server.py` |
| DK3.2-09, DK4-12 | `post_routes`(JSON 입력 검증 → 판정, 실패 400) | `templates/web/server.py` |
| DK3.1-03, DK3.1-22, DK4-04, DK3.2-01 | 키 후보·개인정보 의심 열·담당자 질문 후보 `questions` | `scripts/profile_data.py`, `tests/test_guardrails.py` |
| DK3.2-01 | 학습/평가 파일 분포 비교 한 줄 | `skills/hx-3-capability/references/data-audit.md` |
| DK3.1-18, DK3.3-03 | 제출물 CLI 진입점 골격 | `templates/README.md` |
| DK3.1-b3, DK3.2-b3 | stdlib 경로 규모 한계 안내 | `templates/README.md` |
| DK6-11 | 정확 비교(Decimal)·허용 오차 함정 | `docs/PLAYBOOKS.md` |
| SR4-2, DK9-4 | 외부 통신 코드 0건 검사(텔레메트리 없음)·EXCLUDED 행 | `tests/test_guardrails.py`, `docs/EXCLUDED.md` |
| SR2-08, SR2-12, SR2-22, SR2-46, SR2-47, SR3.8-c, SR3.11-b, SR2x-29, DK2-5, AR4-2, SR3.10-c | 제외 이유·레포 이름 행 보충 | `docs/EXCLUDED.md` |
| (전체) | 이 표 자체와 검사 | `docs/STRENGTHS_MAP.md`, `tests/test_strengths_map.py`, `CAPABILITIES.md` |
