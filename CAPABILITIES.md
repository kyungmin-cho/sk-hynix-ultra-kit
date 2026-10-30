# CAPABILITIES — 하네스 기능 지도 (한 번 읽고 필요한 파일만 연다)

경로는 하네스 루트 기준(`H` = `notes/STATE.md`의 하네스 경로). 상태 파일·`exp/`·`logs/`·`ENVIRONMENT.md`는 워크스페이스 기준. 표에 없는 파일은 읽지 않는다.

## 진입 스킬 (경로로 읽는다)

| 기능/상황 | 어디 | 언제 |
|---|---|---|
| 진행자: 현재 단계·남은 시간·다음 행동 1개·칠 문장 | `skills/hx-next/SKILL.md` | 단계 전후, 막힐 때, 압축 후 |
| 1 환경 판독 → [ACTIVE] 규칙·자원 확정 | `skills/hx-1-env/SKILL.md` | T+0~5 |
| 2 문제 분석 → TASK·담당자 질문 | `skills/hx-2-problem/SKILL.md` | T+5~15 |
| 3 접근법·모듈·병렬 수 → 최소 E2E | `skills/hx-3-capability/SKILL.md` | T+15~40 |
| 4 병렬 시행 `exp/<n>/` | `skills/hx-4-trials/SKILL.md` | T+40~110 |
| 5 수합 → 실행 경로 하나·검증 표 | `skills/hx-5-gather/SKILL.md` | T+110~D−30 |
| 6 최종 검수·제출 체크 | `skills/hx-6-final/SKILL.md` | D−30~D |
| 스킬 색인 | `skills/README.md` | 경로를 잊었을 때 |

## 참조 (필요할 때만)

| 기능/상황 | 어디 | 언제 |
|---|---|---|
| 담당자 질문 틀 | `skills/hx-2-problem/references/interview.md` | 질문 만들 때 |
| 누수·분할·정직한 평가 | `skills/hx-3-capability/references/data-audit.md` | 분할·평가가 있을 때 |
| 서버·미리보기·정적 HTML 폴백 | `skills/hx-3-capability/references/web-preview.md` | 화면이 있을 때 |
| 반도체 용어 | `skills/hx-3-capability/references/semiconductor/glossary.md` | 용어가 낯설 때 |
| 데이터 형태·분석 패턴·신호≠원인 | `skills/hx-3-capability/references/semiconductor/patterns.md` | 반도체 데이터 분석 전 |
| 관리도·WE·Cpk·수율 해석 | `skills/hx-3-capability/references/semiconductor/spc.md` | SPC·수율 과제 |
| 병렬 방법·상한·격리·토큰 | `skills/hx-4-trials/references/parallel.md` | 병렬 시작 전 |
| 10분 막힘·전환표·부분 제출·세션 복원 | `skills/hx-4-trials/references/rescue.md` | 막혔을 때 |
| 결정 한 줄 형식·반입·[부채] | `skills/hx-5-gather/references/decision-log.md` | 결정할 때마다 |
| 증거 규칙·NOT_RUN·멈추고 물을 때 | `skills/hx-6-final/references/verify.md` | "통과"라고 말하기 전 |
| 제출 체크리스트·서술형 재료 | `skills/hx-6-final/references/checklist.md` | D−30부터 |

## 문서 (온디맨드)

| 기능/상황 | 어디 | 언제 |
|---|---|---|
| 시험 규칙 요약(출처 등급, 공식 원문 아님) | `docs/RULES.md` | 규칙이 헷갈릴 때 |
| 180분 운영표·D 계산·잔여 분 규칙 | `docs/TIMELINE.md` | 시간 계획 |
| 복사용 문장(첫 프롬프트·단계 호출·복구·담당자 메신저) | `docs/PROMPTS.md` | 무엇을 칠지 모를 때 |
| 문제 유형별 절차 10개 + 출력 계약 | `docs/PLAYBOOKS.md` | 유형을 고른 뒤 |
| 환경 사실 vs 미확인·사전 체험 순서 | `docs/ENV_FACTS.md` | 사전 체험, 환경이 이상할 때 |
| 넣지 않은 것과 이유 | `docs/EXCLUDED.md` | "왜 이건 없지?" |
| 조사한 강점 477행 ↔ 이 레포 파일·함수(구현/참조/제외) | `docs/STRENGTHS_MAP.md` | "그 기능 어디 있지?", 하네스 수정 후 |

## 상태 양식 (`init_state.sh`가 워크스페이스 `notes/`에 없는 것만 만든다)

| 기능/상황 | 어디 | 언제 |
|---|---|---|
| 현재 커서·시간·PAR_NOW·미검증 | `state/STATE.md` → `notes/STATE.md` | 모든 스킬이 가장 먼저 |
| 과제 계약(사실·가정·질문·안 할 일·완료 조건) | `state/TASK.md` → `notes/TASK.md` | 2단계, 담당자 답마다 |
| 합의·결정·시행·검증(append-only) | `state/DECISIONS.md` → `notes/DECISIONS.md` | 결정마다 |
| 인계·서술형 6문항 재료 | `state/HANDOFF.md` → `notes/HANDOFF.md` | 5·6단계, 세션 교체 전 |
| (추가) 시행 등록부 | `state/TRIALS.md` → `notes/TRIALS.md` | `--extra`, 4단계 |
| (추가) 완료 조건↔검사↔결과 | `state/VERIFICATION.md` → `notes/VERIFICATION.md` | `--extra`, E2E부터 |
| (추가) 서술형 재료·약점→답 | `state/ESSAY_PREP.md` → `notes/ESSAY_PREP.md` | `--extra`, 단계 끝마다 |

추가 양식이 없으면 DECISIONS §2(시행)·§3(검증)·HANDOFF §5(서술형)에 쓴다.

## 스크립트 (git 쓰기·설치 없음)

| 기능/상황 | 어디 | 언제 |
|---|---|---|
| 환경 진단 → `ENVIRONMENT.md`(STATUS·[ACTIVE]·꼬리표) | `bash scripts/env_check.sh [--stdout] [--quick] [--no-network] [--diff OLD] [--pip-probe]`(pip dry-run은 `--pip-probe` 줄 때만) | 시작 직후(사람, IDE 터미널) |
| 상태 파일 생성(덮어쓰기 0) | `bash scripts/init_state.sh [.] --remaining-min N [--t0 HH:MM] [--extra \| --with trials,verification,essay]`(화면 잔여 분 1순위, 13:20은 D′ 칸) | env_check 뒤 |
| 실행 증거 로그 `logs/<KST>_<태그>.log` | `bash scripts/run_and_log.sh <태그> -- [VAR=값] <명령>` | E2E·시행·검증 실행 |
| 판정기(0건=exit 2, FAIL/NOT_RUN=1) | `python3 scripts/verdict.py --check "이름:명령" ... --md` | 검증할 때 |
| 데이터 첫 점검(스트리밍·인코딩 추정·키/개인정보 후보·담당자 질문 후보) | `python3 scripts/profile_data.py <파일> --md [--sample N]` | 2단계 |
| 제출 전 점검(시크릿·TODO·NOT_RUN·하네스 의존·복사) | `python3 scripts/presubmit.py . --src <제출 폴더> [--base <STATE의 BASE 커밋>]` | 6단계 |

## 템플릿 (필요한 함수만 옮기고 DECISIONS에 기록, 직접 import·통째 복사 금지, 표는 `templates/README.md`)

| 기능/상황 | 어디 | 언제 |
|---|---|---|
| 시각 파싱·간격 추정·CSV 스트리밍·선택 import·마크다운 표 | `templates/_common.py` | 날짜·CSV 공통(R9) |
| 센서 이상 후보·규칙 판정·경보 상태·사건 단위 P/R/F·합성 정답 | `templates/anomaly/` | 이상탐지·FDC |
| 고정 기준선 I-MR·WE·Xbar-R·Cpk | `templates/spc/` | SPC |
| 수율 집계 오류 검사·요인별 불량률·카이제곱·순위 | `templates/yield_/` | 수율·불량 요인 |
| 분할·누수 없는 피처·정제·기준 모델·지표·순열 중요도·롤링 원점 백테스트 | `templates/ml/` | 분류·회귀·예측 |
| 0.0.0.0 서버(+JSON 입력 판정) + SVG 선·막대 + 정적 HTML 폴백 | `templates/web/` | 대시보드 |
| 출력 계약 검사기·픽스처 | `templates/contract/` | 출력 형식이 정해진 과제 |
| 로그 파싱·집계·사건 묶음 | `templates/logparse/` | 로그 분석 |
| 디스패칭 규칙 비교·텍스트 간트 | `templates/schedule/` | 배정·스케줄링 |
| 두 자료 키 대사 | `templates/reconcile/` | 대사·비교 |
| 큰 CSV 스트리밍 집계·샘플·외부 정렬 | `templates/bigdata/` | 대용량(R10) |

## 하네스 자체 검사 (과제 테스트 아님)

| 기능/상황 | 어디 | 언제 |
|---|---|---|
| 금지 패턴·스킬·상태·스크립트·경로 검사 | `python3 -m unittest discover -s tests -v` (`tests/`) | 하네스 수정 후 |
| 템플릿 단위 테스트 | `python3 -m unittest discover -s templates -t .` | 템플릿 수정 후 |
