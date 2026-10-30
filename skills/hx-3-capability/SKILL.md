---
name: hx-3-capability
description: Stage 3 capability check — match task type x environment to approach, templates module, dependencies, server feasibility and parallel count; record in DECISIONS, then build the minimal end-to-end path by T+40.
---
# hx-3-capability — 3단계 다룰 수 있는 것 점검

| 입력 | 출력 | 끝 신호 | 시간 예산 |
|---|---|---|---|
| `notes/TASK.md`, `ENVIRONMENT.md` 꼬리표(STATE 요지 3줄), `templates/README.md` | `notes/DECISIONS.md` §1 접근법·모듈·의존성·서버·병렬 수, §2 시행 가설 목록 | 고른 모듈과 폴백이 DECISIONS에 1줄씩 → 최소 E2E 완주 | 결정 3분(T+15~18), E2E ~T+40 |

## 절차

1. 과제 유형을 아래 표에서 고른다(여럿이면 핵심 하나만 먼저).
2. 환경과 맞춘다: pandas/sklearn 없으면 stdlib 열, PIP_NET 막힘이면 설치 없음, GPU 없음이면 딥러닝 제외, SOCKET 거부면 서버는 사람이 실행.
3. DECISIONS §1에 한 줄씩: 접근법 / templates 모듈(또는 "직접 작성") / 의존성 / 서버 여부 / 병렬 수(min(2, PAR_MAX)).
4. templates를 쓰면 **필요한 함수만** 제출 폴더 파일로 옮기고 DECISIONS에 "가져온 함수·원본 파일·무엇을 바꿨나·왜"를 적는다. 하네스 경로 import·폴더 통째 복사 금지(제출물이 하네스 없이 돌아야 한다).
5. 시행 가설 2~3개를 `notes/TRIALS.md`(있으면, 없으면 DECISIONS §2)에 적는다(n=0은 기준선).
6. **최소 E2E**: 입력 읽기 → 가장 단순한 판정/모델 → 출력 파일 한 번 완주. 실행은 `bash ${H:-/tmp/_harness}/scripts/run_and_log.sh e2e -- <명령>`(로그 = 증거), 검사 1개를 `python3 ${H:-/tmp/_harness}/scripts/verdict.py --check "e2e:<명령>"`로 확인하고 VERIFICATION(없으면 DECISIONS §3)에 한 행. T+40까지 못 하면 범위를 줄인다(`skills/hx-4-trials/references/rescue.md`).
7. 필요할 때만 읽는다: 데이터 분할·평가 → `skills/hx-3-capability/references/data-audit.md` / 반도체 용어 → `skills/hx-3-capability/references/semiconductor/glossary.md`, 데이터 형태·분석 패턴·신호≠원인 → `skills/hx-3-capability/references/semiconductor/patterns.md`, 관리도·Cpk·수율 해석 → `skills/hx-3-capability/references/semiconductor/spc.md` / 화면·서버 → `skills/hx-3-capability/references/web-preview.md` / 유형별 절차 → `docs/PLAYBOOKS.md`.

## 유형 → 모듈 (모듈 목록·함수는 `templates/README.md`)

| 과제 유형 | templates | 필요 패키지 | 없을 때 |
|---|---|---|---|
| 센서 이상탐지·FDC·규칙 판정 | `templates/anomaly/` | 없음 | — |
| SPC·관리도·Cpk | `templates/spc/` | 없음 | — |
| 수율·불량 요인 | `templates/yield_/` | 없음 | — |
| 분류·회귀·예측 | `templates/ml/` | sklearn(있으면 HGB) | stdlib 기준선 |
| 대시보드·화면 | `templates/web/` | 없음(http.server) | 정적 HTML 파일 |
| 출력 형식이 정해진 과제 | `templates/contract/` | 없음 | — |
| 로그 파싱·알람 집계 | `templates/logparse/` | 없음 | — |
| 대용량 CSV 집계·샘플 | `templates/bigdata/` | 없음 | `profile_data.py --sample` |
| 두 자료 대사·누락 찾기 | `templates/reconcile/` | 없음 | — |
| 설비 배정·스케줄링 | `templates/schedule/` | 없음 | — |
| 날짜·CSV 읽기 공통 | `templates/_common.py` (`parse_ts`, `stream_csv`) | 없음 | — |
| 이미지·웨이퍼맵 딥러닝 | 없음 | GPU | 규칙·통계 특징 + 기준선 |
