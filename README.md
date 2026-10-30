# ultra-kit

Codex 에이전트용 개인 작업 하네스(Cofa Probe 환경 대상). **비공식**이며 주최 측 자료가 아니다. 사람이 읽는 퀵스타트다.

- 규칙: [AGENTS.md](AGENTS.md) · 기능 지도: [CAPABILITIES.md](CAPABILITIES.md) · 스킬 색인: [skills/README.md](skills/README.md) · 상태 양식: `state/`
- 시간표 [docs/TIMELINE.md](docs/TIMELINE.md) · 복사용 문장 [docs/PROMPTS.md](docs/PROMPTS.md) · 규칙 요약(공식 원문 아님) [docs/RULES.md](docs/RULES.md) · 사전 체험 확인 목록 [docs/ENV_FACTS.md](docs/ENV_FACTS.md)
- 하네스 테스트 통과 ≠ 과제 성공. `tests/`는 이 레포 자체만 검사한다.

## 첫 5분 (IDE 터미널, 워크스페이스 루트에서)

> clone 줄은 공개 레포 `kyungmin-cho/ultra-kit`로 확정돼 있다. 시험 전에 사전 체험과 같은 경로로 clone을 1회 리허설하고, 받은 커밋 해시를 메모한다.

```bash
# 0:00 clone — 과제 워크스페이스 밖에 둔다. 실패하면 export H="$(pwd -P)/_harness"로 바꿔 다시.
export H=/tmp/_harness
HX_REPO_URL='https://github.com/kyungmin-cho/ultra-kit.git'
git clone --depth 1 "$HX_REPO_URL" "$H"
git -C "$H" rev-parse HEAD            # 커밋 해시를 메모(STATE에도 자동 기록)

# 0:40 하네스 폴더의 origin만 제거(워크스페이스 remote는 건드리지 않는다)
git -C "$H" remote remove origin

# 1:00 환경 점검 → ./ENVIRONMENT.md (커밋하지 않음, 제출 전 워크스페이스 밖으로 옮긴다). pip 설치 가능성까지 보려면 --pip-probe(사람 판단)
bash "$H/scripts/env_check.sh"
grep -nE '^STATUS:|^판정 기준|^\[ACTIVE\]' ENVIRONMENT.md   # BLOCKED면 AGENTS.md 맨 위 4줄만 쓴다. PARTIAL은 이유를 본다: PyPI 차단 등은 그대로 진행, python3 없음은 R17(bash 스크립트만)

# 2:30 상태 파일 → ./notes/ (있는 파일은 건너뜀, --extra를 붙이면 TRIALS·VERIFICATION·ESSAY_PREP도)
bash "$H/scripts/init_state.sh" --remaining-min <화면 타이머 잔여 분>

# 3:00 codex 실행 → /status, /model 로 모델·승인 모드 확인(모델은 사람이 고른다)
codex
```

`/tmp/_harness` 파일을 Codex가 읽을 때 승인 창이 반복되거나 거부되면 1분 안에 `<워크스페이스>/_harness`로 다시 clone하고, 아래 문장의 경로와 `notes/STATE.md`의 하네스 경로를 바꾼다. 이 경우 커밋할 때 `_harness`를 넣지 않는다(경로를 지정해 add).

## 첫 프롬프트 (복붙)

```text
/tmp/_harness/AGENTS.md를 작업 규칙으로 읽어. /tmp/_harness/skills/hx-1-env/SKILL.md로 ENVIRONMENT.md를 판독하고, 이어서 /tmp/_harness/skills/hx-2-problem/SKILL.md로 과제 문서와 데이터를 T+15 안에 정리해. 그다음은 /tmp/_harness/skills/hx-next/SKILL.md로 진행해.
```

단계 중간에는 `hx-next` 한 줄이면 된다: `/tmp/_harness/skills/hx-next/SKILL.md 대로 지금 단계와 다음 행동 1개만 알려줘. 화면 잔여 시간은 <m>분.`

## 금지 (자세히는 AGENTS.md §1)

외부 LLM/API 호출·개인 키, 모델 고정, push·remote 추가, 자동 커밋, 도구 업데이트·전역 설치·시스템 패키지 설치, 승인·샌드박스 우회 옵션, 브라우저 자동화, 과제 README·AGENTS.md 수정, 서술형에 AI·복붙 사용. 담당자 대화·화면 확인·제출은 사람이 한다.

## 복구

| 상황 | 할 일 |
|---|---|
| 컨텍스트 압축 뒤 / 새 세션 | `notes/STATE.md와 /tmp/_harness/AGENTS.md, notes/TASK.md, notes/HANDOFF.md를 다시 읽고 hx-next로 다음 행동 1개만 말해.` |
| 작업 환경 pause·재연결 뒤 | 파일은 남아 있다. 서버·장시간 프로세스만 다시 띄우고 위 문장을 보낸다 |
| 10분 넘게 막힘 | `hx-next`에 "막힘"이라고 말한다 → 범위 축소 순서(화면 → 부가 기능 → 품질 케이스) |
| 하네스를 못 쓰는 환경 | AGENTS.md 맨 위 "하네스 없이 쓰는 4줄"만 첫 프롬프트로 보낸다 |

## 이 레포 자체 검사 (시험 전에만, 시험 중에는 돌리지 않는다 — 테스트가 임시 폴더에서 git 저장소를 만든다)

```bash
python3 -m unittest discover -s tests -v
```

MIT License, Copyright (c) 2026 Kyungmin Cho. 차용 출처는 NOTICE.md.
