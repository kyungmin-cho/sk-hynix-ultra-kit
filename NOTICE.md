# NOTICE

이 레포(hx-harness)는 MIT License, Copyright (c) 2026 Kyungmin Cho 이다(LICENSE).
아래 파일은 MIT 레포의 코드 일부를 참고·차용해 다시 썼다. 각 파일 머리 주석에도 같은 출처를 적었다.
커밋은 내려받을 때 기록한 메타의 sha(40자)이고, LICENSE 원문은 그 시점 사본에서 직접 확인했다(2026-10-30).

## 1. 코드 차용 (MIT)

| 이 레포 파일 | 출처 레포 · 커밋 | 원본 파일 | 차용한 것 / 바꾼 것 |
|---|---|---|---|
| templates/anomaly/stats_detect.py | wildrage98/hackathon-kit · 1728cafc4b568fdc860c34b6512a8c5921627f0b | kitlib/stats_detect.py | 탐지기 구성(직전 창 z, EWMA 한계식 k·σ·√(α/(2−α)), CUSUM 알람 후 리셋). 결과 dict 단순화, IQR을 학습 구간 고정 경계로, prefix 불변(누수 안전) 테스트 추가 |
| templates/spc/spc.py | wildrage98/hackathon-kit · 1728cafc4b568fdc860c34b6512a8c5921627f0b | kitlib/spc.py | Western Electric 규칙 1~4 판정 방식, Xbar-R 상수표(A2·D3·D4). 위반을 {index, rule, name} 목록과 규칙별 묶음으로 반환 |
| templates/spc/spc.py | ripplelover/cofa-ready-kit · 1bf4ba4f681f58cb2976189af63a805cf538fa67 | cofa_kit/semiconductor.py (spc_summary) | "기준 구간으로 I-MR 한계를 한 번 정해 고정" 개념, 기준 20점 미만·MR=0 경고. CSV 처리를 빼고 imr_fit/imr_apply로 분리 |
| templates/web/server.py | wildrage98/hackathon-kit · 1728cafc4b568fdc860c34b6512a8c5921627f0b | kitlib/webapp.py | "라우트 dict + 바인드 실패 시 정적 HTML 폴백" 구조. 폴백을 serve 안에서 자동 수행, 결과 dict 반환, SVG 차트 함수 추가, 외부 CSS 의존 제거 |
| templates/logparse/logparse.py | wildrage98/hackathon-kit · 1728cafc4b568fdc860c34b6512a8c5921627f0b | kitlib/logparse.py | 이름 있는 그룹 정규식 필드 추출, 매칭 실패 줄 보고 구조, bracket 패턴, parse_kv 정규식. 스트리밍 제너레이터·ParseStats·구분자/고정폭 파서·세션/버스트 묶기 추가, bracket 패턴이 시각 오프셋(Z·±HH:MM)을 받게 수정 |
| templates/reconcile/reconcile.py | wildrage98/hackathon-kit · 1728cafc4b568fdc860c34b6512a8c5921627f0b | kitlib/reconcile.py | normalize_key(공백 축약·대문자·선행 0 제거), compare 결과 구성(only_in_a/only_in_b/mismatch/dup/summary). 문자열 숫자에도 허용 오차 적용, 값 비교에서 대문자화 제거, 상대 오차·CLI 종료 코드 0/1/2 추가 |
| templates/schedule/dispatch.py | wildrage98/hackathon-kit · 1728cafc4b568fdc860c34b6512a8c5921627f0b | kitlib/schedule.py | Job/Machine 필드, 규칙(FIFO·SPT·EDD·PRIORITY·CR) 정렬 키, 다운타임 회피 루프. 설비 선택을 "가장 빨리 끝나는 설비"로, 평균 흐름시간을 end−ready로 바로잡음, 평균 대기·ASCII 간트·CSV 로더 추가 |

출처 URL: https://github.com/wildrage98/hackathon-kit , https://github.com/ripplelover/cofa-ready-kit

그 밖의 파일(scripts/, skills/, state/, docs/, tests/, 나머지 templates/, README·AGENTS·CAPABILITIES)은 외부 코드·문구를 복사하지 않고 새로 썼다.

## 2. 아이디어만 참고 (코드·문구 복사 없음)

구조·절차·점검 항목 아이디어만 보고 새로 쓴 레포다. 라이선스가 없거나 불분명한 레포(PKJthecreator/probe-kit 등)와 로컬 사본에 LICENSE 파일이 없는 레포(hongkevin/cofathon-prep)는 이 목록에만 있다.

| owner/repo | 참고한 아이디어 | 반영 위치 |
|---|---|---|
| hamjoon2003/sk-hynix-2nd-harness | TASK 계약(사실·가정·질문·안 할 일·완료 조건), 검사 0건=실패, 서술형 골격, preflight 점검 항목, NOT_RUN | state/TASK.md, scripts/verdict.py, scripts/presubmit.py, skills/hx-6-final/references/ |
| hongkevin/cofathon-prep | exit 2 = 아무것도 검사 안 함, 출력 계약 검사 | scripts/verdict.py, templates/contract/check_output.py |
| ColdTbrew/cofa-skills | 정직한 평가·데이터 점검 관점, 결정 한 줄 append | skills/hx-3-capability/references/data-audit.md, skills/hx-5-gather/references/decision-log.md, state/DECISIONS.md |
| jangabc3/cofa-kit | 진행자 스킬(단계·남은 시간·다음 문장), 긴 세션 교체, 토큰 예산 | skills/hx-next/SKILL.md, skills/hx-4-trials/references/ |
| JAM-PARK/codex-harness-kit | 체크포인트 계산·STATE 생성·덮어쓰기 금지 설치기 테스트 | scripts/init_state.sh, tests/test_state.py |
| xxxxKangxxxx/kit | 규칙 우선순위 구조, 담당자 질문 순서, 반도체 용어·분석 패턴 범주, 사전 체험 확인표 | AGENTS.md, skills/hx-2-problem/references/interview.md, skills/hx-3-capability/references/semiconductor/, docs/ENV_FACTS.md |
| PKJthecreator/probe-kit | 킷 없이 쓰는 4줄, git 이력 비밀값 스캔, 분할 계약·시간정렬 shift·HGB 기준선·비용 임계값, 롤링 원점 백테스트·기준선 게이트 | AGENTS.md, scripts/presubmit.py, templates/ml/ |
| wildrage98/hackathon-kit | 범위 축소 순서, 실행 증거 로그, 유형별 playbook, rules 근거 문자열, groupstats 지표, alerts·evalmetrics·synth 구성(경보 상태·사건 평가·합성 정답) | AGENTS.md, scripts/run_and_log.sh, docs/PLAYBOOKS.md, templates/anomaly/rules.py, templates/yield_/groupstats.py, templates/anomaly/events.py |
| ripplelover/cofa-ready-kit | RESCUE/RESUME 프롬프트, 반도체 investigation·spc 참조 구성 | skills/hx-4-trials/references/rescue.md, docs/PROMPTS.md |
| kimcheolhui9846/skill_kit_kch | 금지 패턴 자체 테스트 | tests/test_guardrails.py |
| JongMoKoo/ai-native-cli-kit | 제출 전 프로젝트 점검 스크립트 | scripts/presubmit.py |
| zittenyetten/cofa-probe-workkit | 읽지 않은 자료를 읽었다고 하지 않기, ESSAY_PREP 구성, 출처 교차 확인 | skills/hx-6-final/references/verify.md, state/ESSAY_PREP.md, docs/RULES.md |
| allsleep7610/hynix-hackathon-workflow | 규칙을 출처·확인일과 함께 정리 | docs/RULES.md |
| answndud/hackathon-harness | 독립 기대값·경계 사례 검증, 기술 부채 기록 | skills/hx-6-final/references/verify.md, skills/hx-5-gather/references/decision-log.md |
| HJG-dev/skhynix-hackathon-data-ai-kit | 실험 로그 양식 | state/TRIALS.md |
| phy0916/cofa-probe-starter | 요구사항 추적 표 | state/VERIFICATION.md |
| MIIXmix/cofa-kit, bladem0117/cofa-kit | 서브에이전트 상한(반면교사 포함) | skills/hx-4-trials/references/parallel.md |
| hekate-louise/codex-harness | 40분 E2E·10분 멈춤·마지막 30분 | docs/TIMELINE.md |
| NE0NMIKE/secom-yield-analysis | 정제 규칙 학습/적용 분리 | templates/ml/clean.py |
| HyeongiJeon/CodexHarness | 스트리밍 프로파일 + sqlite 디스크 집계 | templates/bigdata/stream_agg.py |
| gayeon9-9/skhynix-ai-hackathon-prep | CSV 비교 함수 이름만 확인 | templates/reconcile/ |

## 3. 원 라이선스 고지

### wildrage98/hackathon-kit

```text
MIT License

Copyright (c) 2026 wildrage98

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### ripplelover/cofa-ready-kit

```text
MIT License

Copyright (c) 2026 Cofa Ready Kit contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
