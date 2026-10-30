# 제출 체크리스트·서술형 대비

## 제출 체크리스트 (위에서부터, 항목마다 명령+결과)

1. **필수 파일·형식**: 과제 문서의 제출 요구를 `grep -n`으로 다시 읽고 파일 존재·이름·형식을 대조한다.
2. **재현 명령**: HANDOFF §1 명령을 새 셸에서 그대로 실행 → exit 0, 출력 파일 생성.
3. **NOT_RUN 0**: DECISIONS §3·TASK §5에 NOT_RUN이 없거나, 남은 것은 HANDOFF §3에 "미검증"으로 명시.
4. **시크릿**(파일명만 보고 사람이 확인, 값 출력 금지):
   ```bash
   grep -rliE 'api[_-]?key|secret|token|passw' --include='*.py' --include='*.json' --include='*.md' --include='*.env' . | grep -v '^./.git/'
   ```
5. **TODO·임시 코드**: `grep -rnE 'TODO|FIXME|XXX' <제출 폴더>` → 지우거나 한계로 기록.
6. **하네스 의존 없음**: presubmit의 `harness` 행이 OK(import는 FAIL, 경로 문자열은 WARN). 보조로 `grep -rnE '_harness|templates|sys.path' <제출 폴더>`.
7. **커밋 범위**: `git status --short` → `ENVIRONMENT.md`·`_harness`·대용량 산출물이 추적되지 않음. 제출이 미추적 파일까지 담을 수 있으니 `ENVIRONMENT.md`·`_harness/`는 사람이 워크스페이스 밖(`/tmp/`)으로 옮긴다(presubmit `env_file` WARN).
8. **미검증 명시**: STATE 미검증 목록 = HANDOFF §3 한계.
9. **화면 확인**: 사람이 결과 화면·미리보기·출력 파일을 직접 본다.
10. **제출**: 사람이 D−10에 시작. 에이전트는 제출 형식 안내만 한다.

## 서술형 대비 (HANDOFF §5 채우기)

서술형은 작업 기록(대화·터미널·git log/diff)에서 문항이 나온다. 답은 사람이 직접 친다. 여기서는 재료만 모은다.

1. 질문 6개(HANDOFF §5 표)마다 재료를 기록에서 찾는다.
   - Q1 문제 정의 → TASK 한 문장·담당자 답(DECISIONS §0)
   - Q2 접근·대안 → DECISIONS §1에서 대안 칸이 찬 결정 2개
   - Q3 AI 지시 → 이 세션에서 낸 핵심 지시 2~3개와 직접 판단한 것(뒤집은 결정)
   - Q4 검증 → DECISIONS §3 수치(PASS/FAIL 수), 실패를 본 검사 1개
   - Q5 한계·가정 → TASK §2 가정 중 틀리면 가장 큰 것, 틀리는 입력 1개
   - Q6 다시 한다면 → 폐기한 시행·막혔던 지점
2. 각 칸에 수치 1개 이상과 근거 파일 경로를 넣는다. 기록에 없는 것은 지어내지 않는다("기록 없음").
3. 답 골격(사람용): 사실 → 결정 → 근거(수치) → 한계. 약점을 먼저 짚고 → 왜 위험한지 → 다음에 무엇을 검증할지.
4. 제출 확정 전 2~3분 동안 사람이 §5를 소리 내지 않고 한 번 읽는다.
