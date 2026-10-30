---
name: hx-2-problem
description: Stage 2 problem analysis — read task docs and data profile, fill notes/TASK.md (facts, assumptions, open questions, out of scope, done criteria as check names), draft stakeholder interview questions.
---
# hx-2-problem — 2단계 문제 분석

| 입력 | 출력 | 끝 신호 | 시간 예산 |
|---|---|---|---|
| 과제 README·지시 문서, 파일 목록, 데이터 머리, `profile_data.py` 출력 | `notes/TASK.md`, 담당자 질문 3~5개(사람이 발송) | TASK 한 문장 + 완료 조건이 검사 이름으로 | T+5~15 (10분) |

## 절차

1. 파일 목록: `ls -la` 와 `find . -maxdepth 2 -type f -not -path './.git/*' | head -50`. 과제 문서는 `head -80`·`grep -n`으로 필요한 절만 읽는다. **과제 README·AGENTS.md는 수정하지 않는다.**
2. 데이터 첫 점검: `python3 ${H:-/tmp/_harness}/scripts/profile_data.py <데이터 파일들> --md` (큰 파일은 `--sample 50000`). 결측·타입 혼합·중복·타임스탬프 후보를 TASK 사실/질문에 반영한다.
3. TASK §1 사실: 문서에 **문자로** 쓰인 것만, 출처(파일·절)와 함께.
4. TASK §2 가정: 문서에 없지만 정해야 하는 것. "틀리면 깨지는 것"을 같이 적는다.
5. TASK §3 질문: `skills/hx-2-problem/references/interview.md` 틀로 3~5개. 사람이 T+15까지 보낸다. 답은 받는 대로 TASK와 DECISIONS §0에 반영한다(답을 기다리며 멈추지 않는다).
6. TASK §4 안 할 일: 최소 2개(과설계 방지).
7. TASK §5 완료 조건: 문장마다 검사 이름(테스트 함수·명령)을 붙이고 상태는 `NOT_RUN`으로 시작.
8. 맨 위 한 문장: "나는 __를 한다. __는 하지 않는다. 이유는 __." 못 쓰면 아직 코드를 쓰지 않는다.
9. 데이터가 있으면 분할·누수 위험을 미리 한 줄 메모: `skills/hx-3-capability/references/data-audit.md`.
10. STATE를 단계 3으로 옮기고 hx-3-capability로 넘어간다.

- 담당자 메신저 문구 예시는 `docs/PROMPTS.md`, 합의 내용은 `notes/DECISIONS.md` §0(합의문 칸)에 확인 시각과 함께.
- 과제 유형 감이 오면 `docs/PLAYBOOKS.md`의 해당 절만 미리 본다.
