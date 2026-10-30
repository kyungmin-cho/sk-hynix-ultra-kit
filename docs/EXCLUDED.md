# EXCLUDED — 의도적으로 넣지 않은 것과 이유

> 근거: `2차_조사/github_skill_repos.md`(SR §2·§3·§4), `github_domain_kits.md`(DK §3~§9), `cofa_env_research.md`(CE), `argon_envcheck_raw.md`(AR), 설계 `harness_structure_v1.md` §4.
> 이 파일과 `docs/RULES.md`·`AGENTS.md`·`tests/test_guardrails.py`만 금지 문자열을 설명할 수 있다. 나머지 파일은 테스트가 0건을 보장한다.

## 1. 위험 패턴 (어디에도 넣지 않음)

> 명령 문자열은 `tests/test_guardrails.py`의 PATTERNS가 막고, 패턴마다 나쁜 예 표본으로 실제로 잡히는지 검사한다. **(문서로 금지, 테스트 없음)** 표시가 있는 행은 전용 패턴이 없어 이 문서와 AGENTS.md 규칙으로만 막는다.

| 제외 | 이유 | 이 패턴을 쓴 키트(조사 노트) |
|---|---|---|
| `git push`, `git remote add/remove`(README의 하네스 clone origin 제거 한 줄만 예외) | 외부 전송 금지(CE F5) | 다수 키트는 0건(SR §4-7) |
| `git init`, 자동 `git commit`, `git add -A`, git 신원 설정 | git log/diff가 평가 입력(CE F13). 커밋은 사람이 경로 지정 | JAM-PARK·hekate·KIMjun1·hongkevin setup/bootstrap, MIIXmix install, wildrage98 setup(신원) |
| `pip install --break-system-packages`, 조용한 설치 | 시스템 패키지 보호 무시, 환경 오염 | KIMjun1/cofa-work-kit setup.sh |
| `npm i -g`·`npx`로 도구 설치, Codex 포크 전역 설치 | 전역 설치·업데이트 금지 | bladem0117, JakeB-5, gunbbaaang(`npx skills`), yijuuuun(context7 MCP) |
| `codex update`, `codex login` | 제공 Codex 업데이트·개인 인증 금지 | (금지 규칙, SR §1) |
| 승인·샌드박스 우회(`--dangerously-bypass-approvals-and-sandbox`, `--full-auto`, `--yolo`, `danger-full-access`, `-a never`, `--sandbox` 완화, `--add-dir .git`) | 승인 우회는 감독 설정 회피로 보일 수 있음 | keepdev0919, ahnjamin, E2B Codex 예제(CE E7) |
| `codex exec` 백그라운드 병렬 | 완화 플래그 없이는 승인 대기에서 멈춤, 있으면 우회. 병렬은 기본 서브에이전트·사람이 연 탭·파이썬 스크립트만(R12) | E2B Codex 예제, AR §2 제안(불채택) |
| 모델 고정(`-m`, `--model`, `-c model=…`, config의 model 키, 서브에이전트 모델 지정) | 모델은 사람이 `/model`로. 허용 모델 외 호출 위험 | bladem0117(config 라우팅), PKJ(서브에이전트 모델 명시), AR §2(`-m` 강제 제안, 불채택) |
| 외부 LLM/API 호출(api.openai.com, api.anthropic.com, generativelanguage.googleapis.com, openrouter, Ollama 등) | 제공 Codex만 허용 | PKJ agent 템플릿, jungwon123 llm.py, pablomp3/fab_agent, HJG-dev 원격 MCP, gunbbaaang graphify, TA-PP(Ollama) |
| 브라우저 자동화·화면 조작(Playwright, Selenium, OCR 캡처 — OCR은 문서로 금지, 테스트 없음) | Computer Use 금지, 브라우저 다운로드 필요 | bloodstrawberry/my_skill, jungwon123, ahnjamin |
| `curl … \| sh`, 외부 다운로드(UCI 데이터 curl, `pip download` 시험, 브라우저 설치) | 공급망·외부 통신 | NE0NMIKE(UCI curl), wildrage98 preflight(`pip download`) |
| `sudo`, `apt-get` | 시스템 변경 금지, 비 root 가정(CE I2·I4) | — |
| 전체 파일시스템 탐색(`find /`), 시크릿 출력(`printenv`, 키 파일 `cat`) | 멈춤·유출. env_check는 키 이름 화이트리스트와 `***` 마스킹 | AR §3 |
| 대화 기록 외부 전송 MCP bridge(`@latest`) **(문서로 금지, 테스트 없음)** | 외부 전송 | Jungduri/cofa-probe-mcp-bridge |
| 텔레메트리·사용 통계·원격 로그 전송 | 외부 전송. 하네스 코드는 외부로 아무것도 보내지 않는다(env_check의 허용 호스트 HEAD 점검만 예외, `--pip-probe`를 주면 PyPI 조회 1회, `tests/test_guardrails.py` 외부 통신 검사) | 조사 키트 0건 유지(SR §4-2, DK §9-4) |
| 에이전트 대상 설치 지시문("이 README대로 설치해라") **(문서로 금지, 테스트 없음)** | 프롬프트 주입 경로, 사람이 통제 못 함 | answndud, gunbbaaang/skills, pororiiii |

## 2. 구조로 넣지 않은 것

| 제외 | 이유 | 대신 |
|---|---|---|
| `.codex/config.toml`·hooks·`.codex/agents` 정의 | `.codex` 쓰기 차단 보고, 신뢰 필요, 모델 고정 위험 | 정적 금지 패턴 테스트(`tests/test_guardrails.py`) |
| `agents/openai.yaml` | 효과 미확인, 파일 수만 늘림 | 프런트매터 name·description만 |
| `~/.agents/skills`·`~/.codex/skills` 전역 복사, 같은 이름 `rm -rf` 덮어쓰기, `.agents` 심볼릭 링크 | 쓰기 차단 가능(R15), 다른 설정 파괴 | 레포 `skills/` 경로를 직접 읽기 |
| 과제 AGENTS.md 병합·마커 삽입, `.gitignore`·`.git/info/exclude` 수정 | 과제 파일 diff가 평가 입력 | 하네스 AGENTS.md를 경로로 읽기 |
| 13개 스킬(보조 스킬 6개 별도) | 진입면이 넓으면 당일 학습 비용 | 진입 스킬 7개 + 단계별 `references/` |
| 상태 파일 8개 기본 생성 | 당일 갱신 파일 수 | 핵심 4개 기본, TRIALS·VERIFICATION·ESSAY_PREP는 `--extra` |
| 업스트림 스킬 벤더링·추가 레포 clone(`--with-pstack` 등) | 라이선스 혼재·무게·공급망 | 필요한 아이디어만 재작성, NOTICE에 커밋 고정 |
| 의존성 lock·번들 검증 doctor(190파일급 키트), 보일러플레이트 생성·플러그인 업그레이드 | 무게·공급망, 당일 쓸 일 없음 | 하네스 커밋 해시를 STATE에 기록(`init_state.sh`) |
| PreToolUse hook 가드 | `.codex` 쓰기 차단 시 무력화, 신뢰 설정 필요 | 금지 패턴 정적 검사 |
| 소문자 `skill.md`, 자동 발견에 기대는 배치 | 자동 인식 안 됨 | `skills/<이름>/SKILL.md` 정확한 이름 검사(`tests/test_skills.py`), 경로로 읽기 |
| 사전 체험 ENVIRONMENT.md 커밋 | 환경 탐색 흔적이 공개 레포·git log에 남음 | `.gitignore`, 요지 3줄만 STATE·DECISIONS에 |
| env_check를 순수 python3로만 작성 | python이 없는 이미지에서 진단 자체가 불가(AR §4) | bash 하나 + python 있으면 쓰는 조각(`tests/test_env_check.py`가 python 없이 실행 검사) |
| 특정 인물·팀 이름이 들어간 첫 프롬프트 | 다른 사람 환경에서 혼선(SR §3.10) | 고유명 없는 복사용 문장(`docs/PROMPTS.md`) |
| tmux 다중 에이전트, git worktree 병렬 | 토큰·자원 폭증, `.git` 쓰기 차단 가능 | `exp/<n>/` 격리, 상한 2 |

## 3. 템플릿으로 넣지 않은 것

| 제외 | 이유 | 근거 |
|---|---|---|
| 웨이퍼맵·이미지 딥러닝(torch, YOLO, U-Net) | GPU 없음(CE E1·I6), 16G CPU에 부적합 | naisksh32, hikari1215, qingsandamowang (DK6-05~07) |
| FastAPI·Flask·Next·Node 웹 스캐폴드 | 의존성·설치 필요, 통째 반입 위험 | sangwon5579, rkdtmddnjs, pmsojinkwon-svg, jungwon123 (DK4-05·08·11·13) |
| MLOps(모델 등록·서빙·드리프트 API), ops(Docker·k8s·Jenkins) | 대회 범위 밖 | PKJ의 mlops·ops 템플릿 (DK3.2-07·08·14) |
| LLM 에이전트·RAG·MCP 서버 골격 | 외부 LLM 호출 경로, 대회 범위 밖 | PKJ의 agent·mcp 템플릿, ripplelover mcp_server (DK3.2-11·12, DK3.3-04) |
| SHAP·Streamlit·SMOTE·duckdb·ortools·pydantic-ai | 무거운 단발 의존성, 설치 불확실 | yehwan-ahh, baak-jun (DK6-01, DK4-14) |
| 소스 ZIP 패키저, 업로드 도구 | 이번 회차 업로드 불가(CE F12) | ripplelover package.py |
| PDF·이미지 뷰어, 38MB 바이너리 | 무게 | zittenyetten/cofa-probe-workkit |
| 풍부한 완성 코드(18모듈 통째) | "결과물 통째 대체" 금지, 서술형 설명 부담 | wildrage98 kitlib(함수 단위 일부만 차용) |
| Node helper·대형 개인 워크플로(스킬 18개) | 학습 비용 | allsleep7610 |

## 4. 증거로 쓰지 않은 것

| 제외 | 이유 |
|---|---|
| ubinoqe/hynix-round2-harness | hamjoon2003 원본과 같은 파일의 출처 표기 없는 사본 → 원본만 인용 |
| hoonjet/Cofa-Probe-Practice, LobeHub의 cofa-probe-mcp-bridge 항목 | 출처·현재 접근성 불확실(CE §3), 404 |
| 라이선스 없는 레포의 코드·문구 | 아이디어만 재작성(NOTICE "아이디어만 참고" 목록) |

## 5. 조사했지만 반영할 게 없던 레포 (참고로만)

- 범용 스킬 모음: Flyingrang2/codex-harness, easyhunjune/codex-kit, seongwon030/agent-skills, minwoo-106/minwoo-codex-kit, beabic/hx-kit, dhwltn27/js-harness(벤더 스킬).
- 1차 예선·학습 자료: chan808/skhackathon, sj-park-kr/sk-hynix-hackathon(모의고사), Jae-Ung-Jeong/hynix-ai-hackathon1, barios937-ship-it/hx-study-guide, sungbum-hong/hynix-study, 50h33/ai-problem-solving.
- 결과물·빈 레포·포트폴리오: ish606-coder, tjdqls23688-netizen, yanghh1747, yehwan-ahh, gim47656-ship-it(벤치마크 PDF).
- 다른 도구·대회: JM-ABC/cofathon-harness(다른 코딩 에이전트용), imhyunho99/cofathon-ai(curl/npm 멀티에이전트), 5giran/ai-work-harness, coketazo/dah-qualifier.
- 도메인 코드 없음 확인(DK2-5): JongMoKoo, Hantastic-02, DonghaeSuh, Malrangbbobbi, zittenyetten/cofa-probe-kit, jin-castle 등. 대회 무관 반도체 학습 레포(kitae104, kennedym-ds).
- 그 밖에 반영할 것이 없던 레포(SR §2·DK §2-5): ThinkEnigmatic/cofahub, isopink/hynix-298f, namojo/aihck, App-Legend/Skills-GUI, bigbulgogiburger/codex-basic-skills, Seongwonp/AIDA, rignore/skills(무관), juhun7777/cofa(ZIP 미검사), rupria/SK-AI-(소문자 skill.md), jay-moonshot/cofa(prompt_plan 1개), arcturus0637-rgb/cofa-prelim-kit(라이선스 혼재·무게), JakeKim4926/SageHynix(hook 의존), geunhyeongin/hackerton(사전 작성 코드·업그레이드 스크립트), bobo33772-blip/probe-kit(도메인 없는 JSON 서버), xinhi6716/axiom-clotho(대형 평가 설계, 그룹 분할 아이디어만), mlnwns·FOD-team-org·Malko-opensource(범용 스킬·면담 스킬, 아이디어만).
- 도메인 코드 없음(DK2-5 나머지): jyn0e923-maker, sj-park-kr/codex-exam-harness, ytm220, Shinick-Han, peussd55, ChangYeongJeong1103, combe4259, bjun7595-ops, suhyun14, moon-gi-jeon, Chiman2937, orichardev + 코드 0개 후보 31개.
- 조사 한계: 22:00 이후 생성분·이슈/토픽·소셜 공유·대형 레포 일부·ZIP은 미검사(SR §8, DK §7·§10). 당일 커밋 해시 재확인 필요.
