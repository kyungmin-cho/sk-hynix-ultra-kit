<!-- 생성: init_state.sh --extra 또는 --with verification | 갱신: 최소 E2E 첫 행, 테스트·실행마다 | 읽기: 5·6단계, presubmit.py(NOT_RUN 집계) -->
# VERIFICATION — 완료 조건 ↔ 검사 ↔ 결과

> 이 파일이 있으면 검증은 여기에 적는다(없으면 `notes/DECISIONS.md` §3).
> 명령 + 출력 요지 + exit code가 없으면 `NOT_RUN`. 검사 0건 = 실패. 판정은 `verdict.py`가 하고 사람 말은 해석만.

| 완료 조건 #(TASK §5) | 조건 | 검사(테스트 이름) | 명령 | 결과 PASS/FAIL/NOT_RUN | 로그·출력 요지 | 시각 |
|---|---|---|---|---|---|---|
| 1 | | | | NOT_RUN | | |

## 한 번에 돌리기

```bash
python3 <H>/scripts/verdict.py --check "<조건1>:<명령>" --check "<조건2>:<명령>" --md
```

- 출력 표를 위 표에 옮긴다. 아직 못 돌린 조건은 `"<이름>:"`(명령 비움)으로 넣어 `NOT_RUN`으로 남긴다.
- FAIL은 지우지 않는다. 고쳤으면 새 행을 추가하고, 못 고쳤으면 HANDOFF §3 한계로 옮긴다.

## 독립 기대값 (자기 코드로 자기 답을 맞추지 않기)

| 검사 | 기대값의 출처(손 계산·문서 예시·다른 방법) | 경계 사례 |
|---|---|---|
| | | |
