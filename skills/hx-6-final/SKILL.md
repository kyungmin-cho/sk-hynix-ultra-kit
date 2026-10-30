---
name: hx-6-final
description: Stage 6 final review — feature freeze, submission checklist (required files, reproduce command, zero NOT_RUN, secrets, TODO, unverified items), verdict.py run, finalize HANDOFF with the six essay-prep questions; human checks the screen and submits.
---
# hx-6-final — 6단계 최종 검수·결론

| 입력 | 출력 | 끝 신호 | 시간 예산 |
|---|---|---|---|
| 전부(TASK·DECISIONS·HANDOFF·제출 폴더) | 체크리스트 결과, verdict 표, `notes/HANDOFF.md` 확정(서술형 재료 6문항) | verdict exit 0 또는 남은 FAIL·NOT_RUN이 HANDOFF 한계에 명시, D−10에 사람이 제출 시작 | D−30~D (30분, 줄이지 않음) |

## 절차

1. **기능 동결.** 새 기능 금지. Must 우선순위·통합·문서·이해도만.
2. `skills/hx-6-final/references/checklist.md`의 제출 체크리스트를 위에서부터 돈다. 항목마다 명령과 결과를 적는다. 자동 점검은 `python3 ${H:-/tmp/_harness}/scripts/presubmit.py . --src <제출 폴더> --base <STATE의 BASE 커밋>`(BASE가 none이면 `--base` 생략. FAIL 0이 목표. 하네스 import는 FAIL, 하네스 경로 문자열·복사 의심·워크스페이스 안 `ENVIRONMENT.md`/`_harness/`는 WARN이지만 제출 전에 해소한다 — 하네스 의존을 없애고 두 파일은 워크스페이스 밖으로 옮긴다. `harness`·`copy`·`env_file` 행이 OK가 될 때까지 해소한다. 남은 NOT_RUN·notes WARN은 HANDOFF §3에 미검증으로 적으면 된다). 증거 규칙은 `skills/hx-6-final/references/verify.md`.
3. 최종 판정: `python3 ${H:-/tmp/_harness}/scripts/verdict.py --check "<이름>:<명령>" ... --md` → VERIFICATION(없으면 DECISIONS §3)에 붙인다.
4. HANDOFF §1~§4 확정. 실행 방법은 깨끗한 셸에서 그대로 복붙해 돌려 본다.
5. 서술형 6문항 재료를 채운다(`notes/ESSAY_PREP.md`가 있으면 거기에, 없으면 HANDOFF §5, 절차는 checklist.md 아래). 답 문장은 쓰지 않고 **재료(수치·결정·근거 경로)만**.
6. 사람에게: ① 화면·미리보기로 결과를 직접 확인 ② 경로 지정 커밋(`$H/AGENTS.md` §4 형식) ③ D−10에 제출 ④ 확정 전 2~3분 HANDOFF §5 숙독.

## verdict.py 사용법

```bash
python3 ${H:-/tmp/_harness}/scripts/verdict.py --check "unit:python3 -m unittest discover -s tests -v" --check "run:python3 main.py --input data/x.csv"
python3 ${H:-/tmp/_harness}/scripts/verdict.py --spec checks.json --md      # [{"name": "...", "cmd": "...", "timeout": 60}]
```

- exit 0 = 전부 PASS / 1 = FAIL 또는 NOT_RUN 하나 이상 / 2 = 검사 0건(실패로 취급).
- 테스트 0건도 FAIL: 출력에 `Ran 0 tests`·`NO TESTS RAN`·`collected 0 items`가 있으면 exit 0이어도 `0 tests ran`으로 FAIL. 테스트 폴더를 `-s`로 정확히 지정하고 증거 칸의 `Ran N`(N>0)을 확인한다.
- 명령이 빈 검사(`"name:"`)는 NOT_RUN으로 표시된다. 출력 끝 몇 줄이 증거 칸에 남는다(`--tail N`).
