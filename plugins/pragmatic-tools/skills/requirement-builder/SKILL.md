---
name: requirement-builder
description: >
  Trigger when user wants to define or clarify requirements for a new product, feature,
  tool, or automation before building. Use when user says "requirement", "요구사항 정리",
  "뭘 만들고 싶어", "기획", "기능 정의", "PRD", "자동화 만들고 싶어", "툴 만들려고",
  "어떻게 만들어야 할지", "뭘 만들지 정해야 해", "define requirements", "what I want to build",
  "/requirement-builder", or when a non-developer needs help articulating what they want
  to create. Also trigger proactively when user describes a vague idea and seems to want
  to build something (e.g., "Slack 봇 만들고 싶은데...", "새 프로젝트 시작하려고").
  NOT for technical specs, architecture decisions, or implementation planning.
---

# Requirement Builder

Transform ideas into implementation-ready PRDs grounded in the actual codebase.

Good documents produce good implementations. A PRD should be detailed enough that a
coding agent or developer can implement from it without guesswork. The document *is*
the product of this skill — not code.

## Core Principles

1. **Implementation-ready documents**: The PRD must be precise enough to code from.
   Vague specs produce vague implementations. This is why depth matters more than breadth.
2. **Scope narrow, depth deep**: A focused PRD covering one feature slice thoroughly
   beats a broad PRD covering everything shallowly. When scope is too wide, every
   section becomes shallow — narrow first, then go deep.
3. **Codebase-grounded**: PRDs reference the actual codebase — existing models, APIs,
   and patterns. Without this, it's a generic PM document, not a development artifact.
   Codebase analysis is a default step, not optional.
4. **What + How-it-works, not How-to-build**: Define behavior, data flow, and business
   logic. Don't prescribe implementation approach or architecture decisions.
5. **Plain language for requirements, precise language for design**: Requirements should
   be accessible to non-developers. The Design section uses technical terms grounded in
   what already exists in the codebase.
6. **No assumptions**: If ambiguous, ask. Never answer on behalf of the user.
7. **Preserve intent**: Refine the user's idea, don't redirect it.

---

## Phase 1: Capture & Scope

**Purpose**: Collect the user's idea and narrow it to an implementable unit.

A PRD that tries to cover an entire feature system (e.g., "comments") in one shot
produces shallow specs. Narrowing to a specific slice (e.g., "episode viewer comment
creation on mobile app") enables the depth needed for implementation.

**Workflow**:
1. Ask the user to describe what they want to build freely
2. Record the original statement verbatim (for Before/After comparison in Phase 4)
3. Ask if additional context exists (meeting notes, Slack threads, memos, references)
4. **Scope narrowing** — if the idea spans multiple subsystems or platforms:
   - Surface this: "이 기능은 [A], [B], [C] 영역을 포함하는데요, 이번 PRD에서 어디까지 다루면 좋을까요?"
   - Suggest a focused slice if the user isn't sure
   - Encourage specificity: "프롬프트가 구체적일수록 PRD 품질이 좋아집니다"
5. Extract key elements internally (do NOT expose to user):
   - Background / motivation / problem / expected outcome / potential users / initial features

**Exit Conditions**:
- [ ] User's original input is recorded
- [ ] Scope is narrowed to a specific, implementable unit
- [ ] Background and motivation are understood
- [ ] Additional context collected (none is fine)

**Adapt to Entry Point**:
- If user already provided a detailed, scoped brief → skip to Phase 2
- If conversation already contains context → extract first, ask about gaps

---

## Phase 2: Clarification & Codebase Analysis

**Purpose**: Resolve ambiguities through user dialogue, then ground the requirements in
the actual codebase. Codebase findings feed back into sharper follow-up questions.

This phase has three stages:

```
Stage A: 방향성 확립 (Round 1-2)
  — Goals, Non-Goals, Users, Environment 정의
  ↓
Stage B: 코드베이스 분석
  — 1차 스코프 기반으로 관련 코드 탐색
  — 기존 모델, API, 패턴, 제약사항 파악
  ↓
Stage C: 구체화 (Round 3-5)
  — 코드베이스 분석 결과를 반영한 정밀 질문
  — Features, Requirements, Constraints 확정
```

### Question Design
- **Specific over general**: "댓글 삭제는 작성자만 가능한가요?" not "삭제 정책은?"
- **Options over open-ended**: 2-4 choices (recognition > recall)
- **One concern at a time**: One question, one concern
- **Progressive depth**: Scope → Features → Requirements → Constraints

---

### Stage A: 방향성 확립

**Workflow (loop)**:
```
while ambiguities_remain in scope/goals/users:
    1. ask_clarifying_questions() — max 3 per round
    2. update_requirement_understanding()
    3. record to Decisions Log
    4. show_progress_summary() (every 2-3 rounds)
```

#### Round 1: Scope & Purpose
| Area | Example Question | Option Pattern |
|------|-----------------|----------------|
| **Motivation** | "이 기능의 가장 큰 이유는?" | 사용자 요청 / 경쟁사 대비 / 운영 효율화 |
| **Success** | "성공했다고 느끼려면?" | 참여도 증가 / 비용 절감 / 시간 단축 |
| **Scope** | "이번에 어디까지?" | MVP / 핵심+편의 / 전체 |
| **Non-Goals** | "일부러 하지 않을 것?" | (scope에서 파생) |

#### Round 2: Users & Context
| Area | Example Question | Option Pattern |
|------|-----------------|----------------|
| **Target Users** | "주로 누가 사용?" | 내부 / 외부 사용자 / 모든 사용자 |
| **Frequency** | "얼마나 자주?" | 매일 / 주1-2회 / 가끔 |
| **Environment** | "어디서?" | 웹 / 모바일 / 복수 플랫폼 |

**Stage A Exit**: Goals ≥2, Non-Goals ≥1, Target Users ≥1 defined.

---

### Stage B: 코드베이스 분석

**Purpose**: Ground the requirements in what actually exists before asking detailed
feature questions. Knowing the codebase transforms generic questions ("어떤 데이터
저장?") into precise ones ("기존 BoardComment 모델을 확장할까요, 새 모델을 만들까요?").

**Workflow**:
1. **Identify analysis targets** from Stage A results:
   - Database models/tables related to the feature domain
   - Existing API endpoints in the same domain
   - UI components that will be extended or are adjacent
   - Shared utilities, patterns, middleware
2. **Read and analyze** using Explore/Grep/Read subagents:
   - Current data models and relationships
   - API patterns (REST structure, auth, response format)
   - Frontend patterns (state management, component structure)
   - Business logic patterns (validation, error handling)
3. **Synthesize findings**:
   - Reusable components and patterns
   - Existing constraints (DB schema conventions, API conventions, auth model)
   - Gaps between current system and desired feature
4. **Present to user**:
   ```
   코드베이스 분석 결과:
   - 관련 모델: [models found]
   - 기존 API 패턴: [patterns]
   - 재사용 가능 컴포넌트: [components]
   - 발견된 제약사항: [constraints]

   이 결과를 바탕으로 기능 상세를 구체화하겠습니다.
   ```

**Stage B Exit**: Related models/APIs identified, existing patterns documented, user
has reviewed the summary.

---

### Stage C: 구체화

Continue the clarification loop, now informed by codebase findings. Questions in this
stage reference actual code structures discovered in Stage B.

#### Round 3: Core Features
| Area | Example Question | Option Pattern |
|------|-----------------|----------------|
| **Essential** | "핵심 기능은?" | (Phase 1 후보 → 우선순위) |
| **Detail** | "[기능 X] 구체적으로?" | (기능별 분해) |
| **Must/Nice** | "[기능 Y] 반드시 필요?" | Must Have / Nice to Have / 불필요 |
| **Reuse** | "기존 [컴포넌트]를 활용할까요?" | 확장 / 새로 구현 / 부분 재사용 |

#### Round 4: Detailed Requirements
| Area | Example Question | Option Pattern |
|------|-----------------|----------------|
| **Behavior** | "[동작]은 어떻게?" | (구체적 동작 선택지) |
| **Edge Cases** | "[상황] 발생 시?" | 동작1 / 동작2 / 미정 |
| **Data** | "[기존 모델] 외 추가 저장 필요?" | (데이터 항목) |
| **Operations** | "운영 관점에서 필요한 것?" | 모더레이션 / 백오피스 / 모니터링 |

#### Round 5: Constraints
| Area | Example Question | Option Pattern |
|------|-----------------|----------------|
| **Integration** | "[기존 시스템]과 어떻게 연동?" | 기존 패턴 따름 / 새 패턴 / 독립적 |
| **Security** | "로그인 필요?" | 필수 / 일부 비로그인 / 불필요 |
| **Platform** | "특정 플랫폼에서만?" | 웹만 / 모바일만 / 전체 |

### Progress Display (every 2-3 rounds)
```
현재까지 정리된 내용:
- Goals: [status]
- Non-Goals: [status]
- Target Users: [status]
- Core Features: [status]
- Requirements: Must N개 / Nice N개
- Constraints: [status]
- 코드베이스 분석: [완료/미완료]

다음으로 [영역]에 대해 질문하겠습니다.
```
Status markers: 확정 / N개 확정 / N/M 구체화됨 / 미확인

**Phase 2 Exit Conditions**:
- [ ] Goals ≥2, Non-Goals ≥1
- [ ] Target Users ≥1 type
- [ ] Codebase analysis completed and reviewed
- [ ] Core Features ≥2 with Must/Nice classified
- [ ] Must Have Requirements specified with behavior/condition detail
- [ ] Key Constraints identified

---

## Phase 3: Design & UX

**Purpose**: Define technical design grounded in codebase analysis, plus user-facing experience.

This phase produces the most implementation-critical sections. The Design section bridges
"what we want" (Phase 2 Stage A/C) with "what exists" (Phase 2 Stage B).

### 3A: Design Section

Using Stage B findings, write:

1. **Core Idea**: One paragraph summarizing the design approach
2. **Data Design**: Schema changes/additions based on existing models
   - Reference existing tables, add/modify fields
   - Specify types, constraints, relationships
3. **API Design**: Endpoints following the project's existing patterns
   - Method, auth, request/response, key business logic
4. **Fallback & Error Handling**: Failure scenarios and recovery

Ask user to review the Design section before proceeding to UX.

### 3B: UX Section

1. Draft User Stories from Phase 2 results (min 1 per Core Feature)
2. Ask user to review — missing scenarios? priorities?
3. Write User Flow (Happy Path first, then Alternative/Error)
4. Write Success Definition
5. Write UX Acceptance Criteria (Given-When-Then, min 1 per Must Have)

**Exit Conditions**:
- [ ] Design section with data + API + logic reviewed by user
- [ ] User Stories for all Core Features
- [ ] Happy Path User Flow complete
- [ ] UX Acceptance Criteria for Must Have items

---

## Phase 4: Compile, Review & Next Steps

**Purpose**: Assemble the full PRD, get final approval, and guide toward next actions.

**Workflow**:
1. Assemble full PRD from Phases 1-3 using the PRD Template below
2. Generate Before/After Comparison (original input vs structured result)
3. Finalize Decisions Log
4. Present full document for user review
5. If feedback → incorporate and re-review (repeat)
6. On approval → save to `docs/requirements/YYMMDD-PRD-by-skill-vX.XX.md`
7. **Suggest next steps**:
   ```
   PRD 작성 완료: docs/requirements/YYMMDD-PRD-by-skill-vX.XX.md

   다음 단계로 추천드리는 작업:
   1. 백엔드 API 상세 설계 — 엔드포인트별 request/response 스펙
   2. UI 화면 상세 기술 — 화면별 컴포넌트, 상태, 인터랙션
   3. 작업 분할 — 구현 단위로 태스크 나누기

   어떤 것부터 진행할까요?
   ```

**Before/After Comparison**:
```markdown
## 원래 입력
"{user's original statement verbatim}"

## 구체화된 결과 요약
**목적**: [one line]
**범위**: [included / excluded]
**핵심 기능**: [list]
**대상 사용자**: [who]

**클라리피케이션에서 내린 결정들**:
| 질문 | 결정 | 근거 |
|------|------|------|
| ... | ... | ... |
```

**Exit Conditions**:
- [ ] User approved the final document
- [ ] File saved to designated path
- [ ] Next steps communicated

---

## PRD Template

All PRDs follow this structure:

```markdown
---
title: [기능명]
date: [YYYY-MM-DD]
version: [vX.XX]
status: Draft
skill_version: [requirement-builder vX.XX]
---

# [기능명] PRD

## Background
- **현재 상황**: 현재 어떻게 하고 있는가 / 무엇이 없는가
- **문제**: 왜 이것이 필요한가, 현재의 페인 포인트
- **기대 효과**: 이것이 구현되면 무엇이 좋아지는가
- **참조**: 벤치마크, 경쟁사, 레퍼런스 (있는 경우)

## Goals / Non-Goals

### Goals
1. [구체적이고 측정 가능한 목표]

### Non-Goals (explicitly out of scope)
- [이번에 하지 않을 것]

## Target Users
- **[사용자 유형]**: [특징]. [이 도구로 하고 싶은 것]

## Core Features
- **[기능]**: [이 기능이 하는 일 1줄 설명]

## Detailed Requirements

### Must Have
#### MH-1. [항목명]
- [구체적 동작/조건 설명]

### Nice to Have
#### NH-1. [항목명]
- [구체적 설명]

## Design

### Core Idea
[설계 방향 한 문단 요약]

### Data Design
> 코드베이스 분석 기반. 기존 테이블 참조.

#### [테이블명]
| Column | Type | Description |
|--------|------|-------------|
| ... | ... | ... |

### API Design
> 기존 API 패턴 준수.

#### [METHOD] [endpoint]
- **Auth**: [인증 방식]
- **Request**: [파라미터]
- **Response**: [응답 구조]
- **Logic**: [핵심 비즈니스 로직/분기]

### Fallback & Error Handling
- [실패 시나리오] → [대응 방안]

## User Stories

### US-1. [스토리 제목]
As a [사용자 유형],
I want to [행동/기능],
So that [달성하려는 목표/가치].

**Acceptance Criteria:**
- [검증 가능한 기준]

## User Flow

### Happy Path
1. [시작점] → [행동] → [시스템 반응] → [종료점]

### Alternative / Error Path
- [조건] → [분기 설명]

## Success Definition

### 정성적 기준
- [사용자 경험 관점]

### 정량적 기준 (측정 가능한 경우)
- [지표]

## UX Acceptance Criteria

### AC-1: [시나리오명]
- **Given**: [사전 조건]
- **When**: [사용자 행동]
- **Then**: [기대 결과]

## Constraints
- [제약 조건]

## Decisions Log
| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | ... | ... | ... |
```

---

## Rules

1. **No assumptions**: If ambiguous, ask — never answer on the user's behalf
2. **Preserve intent**: Refine, don't redirect
3. **Minimal questions**: Only ask what's necessary; skip already-clear areas
4. **Respect answers**: Accept user decisions without pushback
5. **Track changes**: Record decisions in Decisions Log; show Before/After in Phase 4
6. **Communicate in Korean**: All user-facing communication in Korean
7. **Adapt to entry point**: If detailed context exists, skip redundant questions
8. **Codebase is default**: Always analyze the codebase. Without codebase grounding, the document lacks development value.
