# 증거 규칙 — 제출 전 검증 (verify-before-submit)

> 언제: E2E 첫 완주(3단계), 시행 비교(4단계), 수합(5단계), 제출 직전(6단계). "됐다/통과"라고 말하기 전 매번.

## 규칙 (AGENTS.md §2를 풀어 쓴 것)

| 규칙 | 뜻 |
|---|---|
| 증거 3종 | "통과" = 실행한 명령 + 출력 요지 + exit code. 하나라도 없으면 `NOT_RUN` |
| 검사 0건 = 실패 | 아무것도 확인하지 않았으면 통과가 아니다. `verdict.py`는 검사 0건이면 exit 2, 출력이 테스트 0건(`Ran 0 tests` 등)이면 FAIL |
| 판정은 코드로 | PASS/FAIL은 `verdict.py`·테스트가 낸다. 에이전트 말은 해석만 |
| 읽은 것만 읽었다고 | 열지 않은 파일·돌리지 않은 명령을 했다고 쓰지 않는다. 추정은 "추정"이라고 쓴다 |
| 초록불 의심 | 테스트가 통과해도 입력이 비었거나 0행이면 의미 없다. 출력 행 수·파일 크기를 같이 본다 |
| 독립 기대값 | 기대값은 손 계산·문서 예시·다른 방법에서 가져온다. 자기 코드 출력을 정답으로 박지 않는다 |
| 경계 사례 | 빈 입력, 결측, 기준값과 같은 값, 중복 키, 시간대(Z·+09:00) 최소 1개씩 |
| 환경 의심 | "내 셸에서는 됐다"는 증거가 아니다. 깨끗한 셸에서 README 명령 그대로 다시 실행 |

## 멈추고 사람에게 물을 때 (4조건)

1. 과제 문서끼리 또는 문서와 담당자 답이 충돌한다.
2. 데이터·출력 형식이 문서 설명과 다르다(열 이름·단위·행 수).
3. 금지 목록(AGENTS.md §1)에 닿는 행동이 필요해 보인다.
4. 같은 실패가 10분 넘게 반복된다(→ `skills/hx-4-trials/references/rescue.md`).

## 명령

```bash
# 실행 증거를 로그로 남기며 돌리기(로그 경로가 증거 칸에 들어간다)
bash <H>/scripts/run_and_log.sh e2e -- python3 main.py --input data/x.csv
# 완료 조건 전부를 한 번에 판정(표를 VERIFICATION 또는 DECISIONS §3에 붙인다)
python3 <H>/scripts/verdict.py --check "출력 형식:python3 check_output.py out.csv" --check "단위 테스트:python3 -m unittest discover -s tests -v" --md   # 증거 칸에 Ran N(N>0)
# 제출 전 점검(시크릿·TODO·NOT_RUN·하네스 의존·복사 경고)
python3 <H>/scripts/presubmit.py . --src <제출 폴더> --base <STATE의 BASE 커밋>   # BASE가 none이면 --base 생략
```

## 계획 3줄 (검증을 시작하기 전에 한 번 적는다)

```text
무엇을 확인: <완료 조건 #>
어떻게: <명령> → 기대: <독립 기대값 출처>
실패하면: <고칠지 / 한계로 적을지 판단 기준>
```

## 기록 위치

- `notes/VERIFICATION.md`가 있으면 거기에, 없으면 `notes/DECISIONS.md` §3에 한 행씩.
- 못 돌린 조건은 지우지 않고 `NOT_RUN`으로 남기고 STATE 미검증 목록과 HANDOFF §3에 옮긴다.
