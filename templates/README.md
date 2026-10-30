# templates — 문제 유형별 얇은 참고 구현

**참고 구현이다. 결과를 대신 써 주는 코드가 아니다.** 결과물에 파일·폴더째 넣지 않는다. 필요한 함수만 읽고
과제에 맞게 자기 코드로 다시 쓴 뒤(의존은 최소로) 무엇을 바꿨는지 `notes/DECISIONS.md`에 기록한다.
전부 Python 3.9+ 표준 라이브러리로 동작한다. pandas·scikit-learn이 있으면 그 경로를 쓰고, 없으면 stdlib 경로로 간다.
각 모듈 머리말에 언제 쓰나, 가정, 한계, 출처를 적어 두었다.

## 유형 → 모듈

| 문제 유형 | 폴더/모듈 | 핵심 함수 | 필요 패키지 | 없을 때 |
|---|---|---|---|---|
| 공통(시각·CSV·표) | `_common.py` | `parse_ts`, `stream_csv`, `sniff_csv`, `optional_import`, `to_float`, `quantile`, `infer_interval`(정렬·간격·공백), `md_table` | 없음 | — |
| 센서 이상 후보 | `anomaly/stats_detect.py` | `rolling_zscore`(직전 창), `ewma_detect`, `cusum`, `iqr_bounds`, `stuck` | 없음 | — |
| 임계값·연속 n회 규칙 | `anomaly/rules.py` | `consecutive_rule`, `events_from_flags`, `evaluate_rows` | 없음 | — |
| 경보 상태·사건 평가·합성 정답 | `anomaly/events.py` | `alert_lifecycle`(열기·닫기 히스테리시스), `point_prf`, `event_prf`(같은 설비끼리·허용 오차), `synth_series`(이상 주입+정답표) | 없음 | — |
| SPC·관리도·공정능력 | `spc/spc.py` | `imr_fit`/`imr_apply`(고정 기준선), `western_electric`, `xbar_r_fit`, `cp_cpk` | 없음 | — |
| 수율·불량 요인 | `yield_/groupstats.py` | `yield_summary`(키 중복·결측·passed>tested = 오류), `defect_rate_by`, `chi_square`(p값 직접 계산), `rank_factors` | 없음(scipy 불필요) | — |
| 학습/평가 분할 | `ml/split.py` | `time_split`, `group_split`, `stratified_split`, `assert_no_leak` | 없음 | — |
| 누수 없는 피처 | `ml/features.py` | `shift_then_roll`, `add_lag_roll`, `pandas_lag_roll` | pandas(선택) | `add_lag_roll`(stdlib, 같은 결과) |
| 정제(fit/apply 분리) | `ml/clean.py` | `fit_cleaner`, `apply_cleaner` | 없음 | — |
| 기준 모델 | `ml/baseline.py` | `dummy_model`, `fit_model(prefer="auto"\|"stdlib"\|"sklearn")` | scikit-learn(선택) | stdlib 로지스틱/선형 회귀 |
| 지표·임계값 | `ml/metrics.py` | `classification_metrics`, `regression_metrics`, `roc_auc`, `cost_threshold`, `permutation_importance` | 없음 | — |
| 시계열 예측 평가 | `ml/forecast.py` | `rolling_origin`, `naive`·`seasonal_naive`, `backtest`, `baseline_gate`, `tracking_signal` | 없음 | — |
| 대시보드 | `web/server.py` | `serve`(0.0.0.0:$PORT, `post_routes`로 JSON 입력→판정, 검증 실패 400), `write_static`, `svg_line`, `svg_bar`, `page` | 없음 | 바인드 실패 시 `dashboard.html` 자동 생성 |
| 출력 계약 검사 | `contract/check_output.py` | `check`, `load_rows`, `gen_fixture`, CLI(exit 0/1/2) | 없음 | — |
| 로그 파싱·집계 | `logparse/logparse.py` | `make_parser`(정규식·구분자·고정폭), `parse_lines`(+`ParseStats` 실패 수), `count_by`, `group_events`(세션·버스트) | 없음 | `_common` 없으면 내장 `parse_ts` 폴백 |
| 디스패칭·일정 | `schedule/dispatch.py` | `dispatch`(FIFO·SPT·EDD·PRIORITY·CR), `metrics`, `compare_rules`+`table_text`, `gantt_text` | 없음 | — |
| 두 자료 대사 | `reconcile/reconcile.py` | `compare`(한쪽만·불일치·중복, tol/rel_tol), `summary_text`, CLI(exit 0/1/2) | 없음 | `_common` 없으면 내장 CSV 리더 폴백 |
| 대용량 CSV | `bigdata/stream_agg.py` | `profile`, `group_agg`(넘치면 sqlite3 디스크), `reservoir_sample`, `external_sort` | 없음 | `_common` 없으면 내장 `stream_csv`·`to_float` 폴백 |

모듈끼리 서로 import하지 않는다(`_common`만 try/except로 쓰고 없으면 내장 폴백). 그래서 하네스 안에서 모듈 하나만
따로 실행해 볼 수 있다(`python3 templates/web/server.py --static`, `python3 templates/contract/check_output.py out.csv --spec spec.json`).
이것은 시험 삼아 돌려 보거나 함수 하나를 떼어 읽기 쉽게 하려는 것이지, 파일을 결과물로 복사하라는 뜻이 아니다(아래 반입 규칙 1).
CLI가 내는 JSON·표·HTML은 **참고 출력**이다. 결론은 근거(행 수·실패 수·입력 검증)로 다시 확인하고 결과물 코드로 재현한다.

규모: stdlib 경로는 행 단위 파이썬 루프다. 수십만 행까지는 CPU로 충분하고, 수백만 행이면 `bigdata/stream_agg.py`(청크·sqlite3)나 `profile_data.py --sample`로 줄인 뒤 쓴다. GPU 전제 모델(이미지 딥러닝)은 없다.

## 제출물 진입점 예시 (옮겨 쓸 골격, 하네스를 import하지 않는다)

```python
# main.py — 입력 → 판정 → 출력 파일 한 경로. 실행: python3 main.py --input data/x.csv --out out/
import argparse, csv, os, sys

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    with open(a.input, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("no input rows", file=sys.stderr)
        return 2                       # 검사 대상 없음 = 실패로 본다
    os.makedirs(a.out, exist_ok=True)
    # ... 옮겨 온 함수로 판정(무엇을 바꿨는지 DECISIONS에 기록) ...
    print("rows=%d -> %s" % (len(rows), a.out))
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## 테스트

```bash
python3 -m unittest discover -s templates -t .
```

하네스 루트에서 실행한다. pandas·scikit-learn 전용 비교 테스트는 패키지가 없으면 skip된다. stdlib 경로 테스트는 패키지가 있든 없든 항상 돈다.
템플릿 테스트가 통과했다는 것은 이 참고 코드가 돈다는 뜻일 뿐이다. 과제 결과물의 정답을 보장하지 않는다.

## 반입 규칙

1. **필요한 함수만 옮겨 자기 코드로 다시 쓴다.** 폴더째나 파일째 복사하지 않는다. 옮긴 함수가 `_common`을 쓰면 그 헬퍼(또는 모듈 안 폴백)만 같이 옮긴다. 하네스 경로를 직접 import하는 코드(`sys.path`에 하네스 추가, `templates` 패키지 import)는 결과물에 넣지 않는다. 하네스는 시험이 끝나면 없어지는 경로다.
2. 옮긴 함수는 과제 데이터와 기준(임계값, 결측 처리, 분할 방식)에 맞게 고치고, 설명할 수 있는 범위만 남긴다.
3. 반입할 때마다 `notes/DECISIONS.md`에 한 줄을 남긴다. 형식: `가져온 함수 · 원본 파일 · 무엇을 바꿨나 · 왜`.
4. 옮긴 코드 머리 주석에 출처를 적는다. 예: `# 참고: harness templates/spc/spc.py imr_fit (수정: 결측 행 제외 정책 추가)`. 모듈 머리말에 MIT 원저작자 고지가 있으면 그 줄도 함께 옮긴다.
5. "복사만 한 변경"과 "고친 변경"은 나눠 기록한다. 그래야 어디부터 직접 판단했는지 설명할 수 있다.
6. 신호·순위·p값은 조사 후보다. 원인이나 불량을 판정한 것이 아니다. 결론에는 근거 수치와 한계를 함께 적는다.
