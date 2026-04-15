---
name: ralph-prompt-builder
description: >
  Plan 문서를 입력받아 ralph-loop 실행용 프롬프트를 자동 생성한다.
  Plan 모드에서 작성된 구현 계획 문서(@mention)를 분석하여 완료 조건을 추출하고,
  <promise></promise> 태그를 포함한 /ralph-loop 명령어를 포맷팅하여 출력한다.
  "ralph 프롬프트 만들어줘", "ralph-loop 돌릴 프롬프트", "plan을 ralph로",
  "이 플랜으로 ralph 돌리자", "ralph prompt", "ralph-loop prompt",
  "/ralph-prompt-builder", "플랜 문서 ralph", "구현 계획 ralph-loop으로",
  "이거 ralph에 넣어줘", "ralph 명령어 생성", "plan to ralph" 등의 요청에 사용.
  Plan 문서 없이 일반 구현 요청만 하는 경우에는 사용하지 않는다.
---

# Ralph Prompt Builder

Plan 문서를 분석하여 `/ralph-loop` 실행 명령어를 생성하는 스킬.

Ralph Loop은 Claude가 동일한 프롬프트를 반복 수행하면서 이전 작업 결과(파일, git 히스토리)를 보고 점진적으로 개선하는 자기참조 반복 루프다. 이 스킬은 구조화된 Plan 문서에서 핵심 지시사항과 완료 조건을 추출하여, ralph-loop이 효과적으로 동작할 수 있는 프롬프트를 생성한다.

---

## Input

유저는 Plan 모드에서 작성된 구현 계획 문서를 `@{filename}.md` 형태로 mention하여 제공한다.

Plan 문서가 없는 경우, 유저에게 먼저 Plan 모드(`/plan`)로 구현 계획을 작성하도록 안내한다.

---

## Workflow

### Step 1: Plan 문서 분석

Plan 문서에서 다음 요소들을 추출한다:

| 추출 대상 | 설명 | 예시 |
|-----------|------|------|
| **구현 목표** | 최종적으로 무엇을 만드는지 | "REST API with CRUD operations" |
| **단계/페이즈** | 구현 순서가 있는 작업 단위 | Phase 1: Auth, Phase 2: API |
| **완료 조건** | 각 단계 또는 전체의 성공 기준 | "모든 테스트 통과", "빌드 성공" |
| **기술적 제약** | 사용할 기술, 피해야 할 것 | "TypeScript strict mode" |

### Step 2: 완료 조건 정제

Plan에서 추출한 완료 조건들을 ralph-loop의 completion-promise와 호환되는 형태로 정제한다.

**좋은 완료 조건의 특성:**
- 객관적으로 검증 가능 (테스트 통과, 빌드 성공, 린트 에러 0)
- 구체적이고 명확함 (모호한 "잘 동작함" 대신 "모든 엔드포인트가 200 응답")
- Claude가 스스로 확인할 수 있음 (외부 승인 불필요)

**완료 조건 추출 우선순위:**
1. Plan에 명시적으로 적힌 성공 기준 / acceptance criteria
2. 테스트 관련 조건 (test pass, coverage 등)
3. 빌드/린트 관련 조건
4. 각 단계의 산출물 존재 여부

### Step 3: 프롬프트 조립

추출한 정보를 다음 구조로 조립한다:

```
/ralph-loop "Implement plan @{plan-document}.md.

When complete, verify ALL of the following:
- [완료 조건 1]
- [완료 조건 2]
- [완료 조건 3]
...

Output: <promise>ALL_CRITERIA_MET</promise>" --max-iterations 10 --completion-promise "ALL_CRITERIA_MET"
```

**프롬프트 조립 규칙:**

1. **첫 줄은 핵심 지시**: `Implement plan @{plan-document}.md.` — Plan 문서를 @mention으로 참조하여 Claude가 전체 맥락을 가지도록 한다.
2. **완료 조건 목록**: "When complete, verify ALL of the following:" 아래에 불릿 리스트로 나열한다.
3. **promise 태그**: 프롬프트 마지막에 반드시 `Output: <promise>COMPLETION_WORD</promise>` 형태로 포함한다. completion-promise 플래그 값과 태그 안의 값이 정확히 일치해야 한다.
4. **max-iterations**: 기본값 10회. Plan의 복잡도에 따라 조정을 제안할 수 있다.

---

## Output Format

최종 결과물은 유저가 바로 복사-붙여넣기 할 수 있는 단일 명령어 블록이다.

**출력 예시 1 — API 구현 Plan:**

```
/ralph-loop "Implement plan @api-implementation-plan.md.

When complete, verify ALL of the following:
- All CRUD endpoints return correct status codes (200, 201, 404)
- Input validation rejects malformed requests with 400
- All unit tests pass (npm test exits 0)
- No TypeScript compilation errors (tsc --noEmit exits 0)

Output: <promise>ALL_CRITERIA_MET</promise>" --max-iterations 10 --completion-promise "ALL_CRITERIA_MET"
```

**출력 예시 2 — 리팩토링 Plan:**

```
/ralph-loop "Implement plan @refactor-auth-module.md.

When complete, verify ALL of the following:
- Legacy AuthMiddleware replaced with new JWTAuthService
- All existing tests still pass (no regressions)
- No unused imports or dead code remain (lint clean)
- Migration guide document created at docs/auth-migration.md

Output: <promise>ALL_CRITERIA_MET</promise>" --max-iterations 10 --completion-promise "ALL_CRITERIA_MET"
```

**출력 예시 3 — 멀티페이즈 Plan:**

```
/ralph-loop "Implement plan @e-commerce-mvp.md.

When complete, verify ALL of the following:
- Phase 1: User auth with JWT — login/register/logout working, tests pass
- Phase 2: Product catalog — list/search endpoints working, pagination correct
- Phase 3: Shopping cart — add/remove/update items, cart total calculated correctly
- All phases integrated and full test suite passes
- Application starts without errors (npm start exits cleanly)

Output: <promise>ALL_CRITERIA_MET</promise>" --max-iterations 15 --completion-promise "ALL_CRITERIA_MET"
```

---

## Iteration 수 가이드

Plan의 복잡도에 따라 적절한 iteration 수를 제안한다:

| Plan 복잡도 | 기준 | 권장 iterations |
|------------|------|----------------|
| **단순** | 단일 기능, 파일 1-3개 변경 | 5-7 |
| **보통** | 2-3개 기능, 테스트 포함 | 10 (기본값) |
| **복잡** | 멀티페이즈, 통합 테스트 필요 | 15-20 |

기본값은 10이며, 복잡도에 따라 다른 값을 제안하되 유저가 최종 결정한다.

---

## Rules

1. **Plan 문서 필수**: Plan 문서 없이는 프롬프트를 생성하지 않는다. Plan 없이 요청 시, Plan 모드 사용을 안내한다.
2. **promise 태그 필수**: 생성하는 모든 프롬프트에는 반드시 `<promise></promise>` 태그가 포함되어야 한다.
3. **completion-promise 일치**: `--completion-promise` 플래그 값과 `<promise>` 태그 내부 텍스트가 정확히 동일해야 한다.
4. **복사 가능한 단일 블록**: 결과물은 코드 블록 하나로 출력하여 유저가 바로 붙여넣기 할 수 있어야 한다.
5. **검증 가능한 조건만**: Claude가 스스로 확인할 수 없는 조건(유저 승인, 외부 서비스 확인 등)은 포함하지 않는다.
6. **한국어 소통**: 유저와의 대화는 한국어로 진행한다. 프롬프트 본문(ralph-loop에 들어가는 영어 프롬프트)은 영어로 작성한다.
7. **Plan 요약 제시**: 프롬프트 생성 전에, 추출한 완료 조건 목록을 유저에게 보여주고 확인받은 후 최종 명령어를 출력한다.
