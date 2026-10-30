# PLAYBOOKS — 문제 유형별 절차

> 과제 유형을 고른 뒤(hx-3-capability) 해당 절만 읽는다. 템플릿은 **필요한 함수만** 제출 폴더로 옮기고 DECISIONS에 "가져온 함수·무엇을 바꿨나"를 적는다.
> 공통 순서: 프로파일(`python3 <H>/scripts/profile_data.py <파일> --md`) → 기준선 → 최소 E2E(T+40) → 개선 시행 → 검증 표. 결과는 조사 후보, 원인 판정은 담당자.

## 한눈에

| # | 유형(과제 문구 신호) | 템플릿 | 핵심 산출 |
|---|---|---|---|
| 1 | 센서 이상탐지("이상 시점", "센서 값 튐", "드리프트") | `templates/anomaly/stats_detect.py` | 시점·설비·점수·근거 |
| 2 | 규칙·알림 판정 FDC("n회 연속 초과면 경보", "인터록") | `templates/anomaly/rules.py` | 규칙별 판정 + 근거 문자열 |
| 3 | SPC·관리도("관리 한계", "Cpk", "WE 룰") | `templates/spc/spc.py` | 고정 한계·위반 목록·Cpk |
| 4 | 수율·불량 요인("어느 장비 탓", "불량률 차이") | `templates/yield_/groupstats.py` | 요인별 불량률·순위·검정 |
| 5 | 분류·회귀 ML("불량 예측", "합불 분류") | `templates/ml/` | 분할 계약·기준선 대비 지표·임계값 |
| 6 | 시계열 예측("다음 값", "수요·소모 예측") | `templates/ml/split.py`, `templates/ml/features.py`, `templates/ml/baseline.py` | 롤링 원점 백테스트·기준선 게이트 |
| 7 | 대용량·로그("GB 단위 로그", "알람 로그 분석") | `templates/bigdata/stream_agg.py`, `templates/logparse/logparse.py` | 스트리밍 집계·코드별 빈도·사건 묶음 |
| 8 | 대사·비교("두 시스템 값 맞추기", "누락 찾기") | `templates/reconcile/reconcile.py` | 양쪽/한쪽만/불일치/중복 키 |
| 9 | 스케줄링·배정("설비 배정", "대기 시간 줄이기") | `templates/schedule/dispatch.py` | 규칙별 지표 비교·텍스트 간트 |
| 10 | 웹 대시보드·화면("보여주는 화면", "조회") | `templates/web/server.py` | 0.0.0.0 서버 + 정적 HTML 폴백 |
| 공통 | 출력 형식이 정해짐("CSV 열 순서", "JSON 스키마") | `templates/contract/check_output.py` | 계약 검사기(exit 0/1/2) |

## 1. 센서 이상탐지

1. 장비·챔버·센서별로 나눠 시간 정렬(`templates/_common.py` `parse_ts`). 섞어서 한 시계열로 보지 않는다.
2. 기준선: 직전 창 z(`rolling_zscore`, 현재 값 제외) → 느린 변화는 `ewma_detect`·`cusum`(기준 구간 고정), 값 고착은 `stuck`.
3. 임계값은 담당자 기준 우선. 없으면 기준 구간 분포로 정하고 TASK §2 가정에.
4. 출력: 시점·설비·센서·점수·규칙·근거 수치. 평가 라벨이 있으면 `templates/anomaly/events.py`의 `event_prf`(사건 단위, 같은 설비끼리·허용 오차)와 `point_prf`. 라벨이 없으면 `synth_series`로 이상을 주입한 합성 데이터에서 코드가 잡는지만 확인(성능 주장 아님).
- 기록: 기준 구간(기간·점 수), 창 크기·k, 임계값 출처.
- 함정: 미래 값을 포함한 이동평균(누수), 설비 혼합, PM 직후 구간을 이상으로 보고.

## 2. 규칙·알림 판정 (FDC)

1. 담당자 규칙을 표로 옮긴다: 조건·연속 횟수·우선순위·경계값 처리(같으면 이상인가).
2. `consecutive_rule`·`evaluate_rows`로 판정하고 근거 문자열을 같이 낸다. `events_from_flags`로 연속 경보를 사건 하나로 묶는다. 경보를 "열림/해제" 상태로 보여야 하면 `alert_lifecycle`(n회 연속이면 열고 m회 정상이면 닫음).
3. 규칙 충돌 시 우선순위를 코드 주석·DECISIONS에.
4. 검증: 규칙마다 경계 사례(기준값과 같음, 결측, 연속 n−1회) 테스트.
- 기록: 규칙 표의 출처(문서 절·담당자 답 번호).
- 함정: 결측을 0으로 채워 규칙이 조용히 통과·실패.

## 3. SPC·관리도

1. 관리도 고르기·기준 구간·WE 규칙·Cpk 해석은 `skills/hx-3-capability/references/semiconductor/spc.md`.
2. `imr_fit`(기준 구간) → `imr_apply`(감시 구간). 부분군이면 `xbar_r_fit`.
3. `western_electric`으로 규칙 위반, 규격이 있으면 `cp_cpk`(σ 종류 명시).
4. 출력: 고정 한계·위반 지점·규칙 번호·Cpk. "신호 = 조사 후보" 문구.
- 기록: 기준 구간, 켠 규칙, σ 종류, Cpk 기준(담당자).
- 함정: 감시 구간으로 한계 재계산(순환 판정), 관리 한계와 규격 혼동.

## 4. 수율·불량 요인

1. 집계 전 검사: 키 중복·결측·`passed > tested` → 오류로 세서 보고(`yield_summary`, 수율은 가중 합으로).
2. `defect_rate_by` → `rank_factors`로 요인별 불량률 순위, `chi_square`는 기대도수 경고와 함께.
3. 상위 요인은 교차표로 다른 요인이 섞였는지(같은 기간·같은 제품) 확인.
4. 출력: 요인·불량률·표본 수·순위·p값(참고). "공통성 신호, 원인 아님".
- 기록: 불량 정의(빈·합불 기준), 집계 방식(가중 평균인지).
- 함정: 표본 작은 그룹의 극단 비율을 1위로 보고, 다중 비교.

## 5. 분류·회귀 ML

1. 분할 계약 먼저: 시간순 `time_split` / 같은 설비·로트 `group_split` / 독립·불균형 `stratified_split`, `assert_no_leak`로 확인. 근거는 `skills/hx-3-capability/references/data-audit.md`.
2. 정제는 `fit_cleaner`(학습 구간) → `apply_cleaner`(전 구간). 피처는 `shift_then_roll`·`add_lag_roll`.
3. 기준선 `dummy_model` → `fit_model(prefer="auto")`(sklearn 있으면 HGB, 없으면 stdlib).
4. `classification_metrics`/`regression_metrics`, 불균형이면 `roc_auc`·`cost_threshold`(놓침·오경보 비용은 담당자). "무엇이 중요했나"는 검증 구간에서 `permutation_importance`(원인 아님).
- 기록: 분할 방식과 이유, 기준선 수치, 임계값과 비용 가정.
- 함정: 무작위 분할(시간·그룹 누수), 전체 데이터로 정제 기준, 평가 구간에 맞춘 반복 튜닝.

## 6. 시계열 예측

1. 시간순 분할만. 평가는 롤링 원점: `templates/ml/forecast.py`의 `rolling_origin`·`backtest`(원점별 MAE, 평균·최악).
2. 기준선 게이트: `naive`(직전 값)·`seasonal_naive`(주기) → `baseline_gate`. 모델이 기준선을 못 이기면 기준선을 제출. 운영 중 편향은 `tracking_signal`.
3. 피처는 `shift_then_roll`(현재 값이 자기 피처에 안 들어가게), 모델은 `fit_model`.
4. 지표: MAE·MAPE(0 근처 값 주의)를 원점별로, 평균과 최악을 함께.
- 기록: 예측 지평(몇 스텝 앞), 원점 수, 기준선 대비 개선.
- 함정: 한 번의 분할 결과만 보고, 미래 정보가 섞인 이동 통계.

## 7. 대용량 데이터·로그

1. 통째 로드 금지(ENVIRONMENT.md R10). `profile_data.py --sample 50000`으로 형태부터.
2. CSV는 `stream_agg.py`의 `chunked`·`group_agg`·`reservoir_sample`·`external_sort`로 메모리 일정하게. 결과는 중간 파일로 캐시.
3. 로그는 `logparse.py`의 `make_parser`/`parse_kv` → `parse_lines` → `count_by`(코드·레벨·장비별) → `group_events`(시간 간격으로 사건 묶음).
4. 파싱 실패 줄 수를 반드시 같이 보고(조용한 누락 방지).
- 기록: 샘플 크기와 전체 실행 시간, 파싱 규칙 출처.
- 함정: 같은 알람 반복을 별개 사건으로 세기, 파싱 실패를 버리고 0건으로 보고.

## 8. 대사·비교

1. 키 정의를 담당자와 맞춘다(대소문자·공백·자릿수 정규화 = `normalize_key`).
2. `compare`로 양쪽 존재 / 한쪽만 / 값 불일치 / 중복 키를 나누고 `summary_text`로 요약. 수치 비교 허용 오차(`values_equal`)는 문서·담당자 기준.
3. 불일치 상위 사례를 표로, 건수와 비율을 함께.
- 기록: 키 정규화 규칙, 허용 오차, 중복 키 처리.
- 함정: 중복 키를 첫 행만 남기고 조용히 버림. 금액·농도처럼 자릿수가 정확해야 하는 값은 float 대신 `decimal.Decimal`로 비교하거나 허용 오차를 명시.

## 9. 스케줄링·배정

1. 작업 표(도착·처리 시간·마감·우선순위·가능 설비)를 `jobs_from_rows`로.
2. `compare_rules`로 FIFO·SPT·EDD·PRIORITY·CR을 같은 입력에 비교 → `metrics`(평균 대기·지연·가동률) → `table_text`·`gantt_text`.
3. 담당자 목표(지연 최소인지 처리량인지)로 규칙을 고른다. 최적화 솔버는 쓰지 않는다(규칙 비교로 설명 가능하게).
- 기록: 목표 지표, 고른 규칙과 차점 규칙의 수치 차이.
- 함정: 설비 제약(가능 설비) 누락, 동률 처리 규칙 미정.

## 10. 웹 대시보드·화면

1. 핵심 결과를 먼저 파일(CSV/JSON)로. 화면은 그 파일을 읽어서 보여 준다(검사는 파일로).
2. `serve`(0.0.0.0, `PORT` 환경변수) — 사람이 IDE 터미널에서 실행, 미리보기에 같은 포트. 바인드 실패면 `write_static`으로 `dashboard.html`.
3. 차트는 `svg_line`·`svg_bar`(외부 CDN 없음). 입력을 받아 판정해야 하면 `post_routes`(JSON 입력 검증 → 판정 → 파일/sqlite3 저장 → GET으로 조회). 화면은 범위 축소 1순위다.
- 기록: 서버 실행 명령(HANDOFF §1), 소켓 결과(R8).
- 함정: localhost 바인딩, 외부 CDN 의존, 화면만 있고 파일 결과 없음.

## 공통: 출력 계약

- 출력 형식(열·타입·범위·행 수)이 정해져 있으면 `check_output.py`의 `check`로 독립 검사기를 먼저 만든다(exit 0 통과 / 1 위반 / 2 검사 대상 없음). `gen_fixture`로 경계·불량 입력을 만든다.
- 이 검사를 verdict.py 완료 조건 하나로 넣는다.
