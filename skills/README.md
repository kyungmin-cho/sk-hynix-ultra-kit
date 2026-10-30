# skills 색인

자동 발견에 기대지 않는다. Codex에게 **경로로** 읽게 한다: `$H/skills/<이름>/SKILL.md` (`H` 기본 `/tmp/_harness`).
입력·출력의 `notes/`, `exp/`, `ENVIRONMENT.md`는 워크스페이스 루트 기준이다.

| 단계 | 스킬 | 경로 | 언제 | 입력 | 출력 |
|---|---|---|---|---|---|
| 0 | hx-next | `skills/hx-next/SKILL.md` | 단계 전후·막힐 때·압축 후 | `notes/STATE.md`, 화면 잔여 분 | STATE 커서, 3줄 안내 |
| 1 | hx-1-env | `skills/hx-1-env/SKILL.md` | T+0~5 | `ENVIRONMENT.md` | STATE 환경 요지 3줄, DECISIONS 환경 결정 |
| 2 | hx-2-problem | `skills/hx-2-problem/SKILL.md` | T+5~15 | 과제 문서, 데이터, `profile_data.py` 출력 | `notes/TASK.md`, 담당자 질문 |
| 3 | hx-3-capability | `skills/hx-3-capability/SKILL.md` | T+15~18 (+최소 E2E ~T+40) | TASK, ENVIRONMENT 꼬리표, `templates/README.md` | DECISIONS 접근법·모듈·병렬 수, 시행 가설 |
| 4 | hx-4-trials | `skills/hx-4-trials/SKILL.md` | T+40~110 | DECISIONS 시행 표, PAR_NOW | `exp/<n>/`, 시행 표 행, 채택/폐기 |
| 5 | hx-5-gather | `skills/hx-5-gather/SKILL.md` | T+110~D−30 | 시행 결과, 로그, 테스트 | 단일 실행 경로, 검증 표, HANDOFF 초안 |
| 6 | hx-6-final | `skills/hx-6-final/SKILL.md` | D−30~D | 전부 | 제출 체크 통과, HANDOFF 확정(서술형 재료) |

references(필요할 때만 읽는다, 언제 읽나는 각 SKILL.md에 한 줄씩):

| 파일 | 내용 | 언제 |
|---|---|---|
| `skills/hx-2-problem/references/interview.md` | 담당자 질문 틀(normal/exception/priority/prohibited/success) | 2단계 질문 만들 때 |
| `skills/hx-3-capability/references/data-audit.md` | 누수·분할·정직한 평가 | 데이터 분할·평가가 있을 때 |
| `skills/hx-3-capability/references/web-preview.md` | 서버·미리보기·정적 HTML 폴백 | 화면·서버가 있을 때 |
| `skills/hx-3-capability/references/semiconductor/glossary.md` | 반도체 용어(제품·공정·통계) | 과제 용어가 낯설 때 |
| `skills/hx-3-capability/references/semiconductor/patterns.md` | 데이터 형태·분석 패턴·신호≠원인 원칙 | 반도체 데이터 분석 시작 전 |
| `skills/hx-3-capability/references/semiconductor/spc.md` | 관리도·WE 규칙·Cpk·수율 해석 | SPC·수율 과제 |
| `skills/hx-4-trials/references/parallel.md` | 병렬 3방법·상한·exp/<n> 격리·토큰 체크포인트 | 병렬 시행 전 |
| `skills/hx-4-trials/references/rescue.md` | 10분 막힘·전환표·범위 축소·부분 제출·세션 복원 | 막혔을 때, T+40/T+100 미달 |
| `skills/hx-5-gather/references/decision-log.md` | 결정 한 줄 형식·예시·반입·[부채] 기록 | 결정할 때마다 |
| `skills/hx-6-final/references/verify.md` | 증거 규칙·0 checks=fail·NOT_RUN·멈추고 물을 때 | "통과"라고 말하기 전 |
| `skills/hx-6-final/references/checklist.md` | 제출 체크리스트·서술형 대비 절차 | D−30부터 |

전체 기능 표(docs·scripts·templates 포함): 루트 `CAPABILITIES.md`.
