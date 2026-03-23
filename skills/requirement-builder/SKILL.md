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

Help non-developers transform vague ideas into clear, structured requirements before vibe coding.
The goal is to precisely define "what I want to build" — never "how to build it."

## Core Principles

1. **What only, never How**: Never mention tech stacks, implementation approaches, or architecture. That's the coding agent's job.
2. **Plain language**: Avoid jargon. Ask questions that non-developers can understand.
3. **One concern at a time**: Avoid bundling unrelated questions.
4. **No assumptions**: If something is ambiguous, ask. Never answer on behalf of the user.
5. **Preserve intent**: Refine the user's idea, don't redirect it.

---

## Workflow

### Phase 1: Capture the Idea

Ask the user to describe what they want to build, in any format:

```
What do you want to build?
Describe it freely — one sentence or a full paragraph, either is fine.

Examples:
- "A tool that automatically organizes our team's meeting notes"
- "A system that categorizes customer inquiries and notifies the right person"
- "A company book lending management page"
```

Record the user's original statement verbatim (for Before/After comparison later).

---

### Phase 2: Iterative Clarification

Resolve ambiguities and gaps from the original statement using AskUserQuestion.
Repeat until all requirement areas are clear.

**Question Design Principles:**
- **Specific over general**: "Do you need login?" instead of "What's the vibe?"
- **Options over open-ended**: Provide 2-4 choices (recognition > recall)
- **One concern at a time**: Avoid bundling unrelated questions
- **Neutral framing**: Present options without bias

**Loop Structure:**
```
while ambiguities_remain:
    identify_most_critical_ambiguities()
    ask_clarifying_questions()   # AskUserQuestion with 2-4 options each
    update_requirement_understanding()
    check_for_new_ambiguities()
```

**AskUserQuestion Format:**
```
question: "Who will use this tool?"
options:
  - label: "Just me"
    description: "Personal tool for my own use"
  - label: "My team"
    description: "Multiple team members will use it together"
  - label: "External users too"
    description: "People outside the team will also use it"
```

**Requirement Areas to Clarify:**

| Area | What to explore |
|------|----------------|
| **Background / Problem** | Why is this needed? How is it done today? What's painful about the current way? |
| **Target Users** | Who uses it? Role distinctions? Tech comfort level (spreadsheets? web apps?) |
| **Core Features** | What must it do? What's the "this alone is enough" feature? What's nice-to-have? |
| **Scope** | What's explicitly out? Where does data come from? What form should output take (screen? notification? file?) |
| **Constraints** | Security, access control, existing system integrations, usage environment (web? mobile? Slack bot?) |

**Exit Condition:**
Move to Phase 3 when ALL of the following are clear:
- [ ] Why build it (background / problem)
- [ ] Who uses it (target users)
- [ ] What it must do (core features)
- [ ] What it won't do (out of scope)
- [ ] What rules to follow (constraints)

**Example Clarification Round:**

Original: "팀 회의록을 자동으로 정리해주는 툴"

Round 1 (via AskUserQuestion):
1. 회의록 입력은 어떤 형태인가요? → 음성 녹음 파일
2. 누가 사용하나요? → 팀 전원 (5명)
3. 정리된 결과물은 어디에 저장되나요? → Notion 페이지
4. 회의 빈도는? → 주 2-3회

Round 2:
1. 회의 종류가 여러 가지인가요? → 스탠드업 / 기획 회의 / 외부 미팅
2. 종류별로 다른 템플릿이 필요한가요? → 네, 스탠드업은 간단히, 기획은 상세히
3. 액션 아이템 자동 추출이 필요한가요? → 네, 담당자 배정까지

---

### Phase 3: Structure the Requirements Document

Organize collected information into a structured requirements document.
Save path: `docs/requirements/{project-name}-requirements.md`
- If the `docs/requirements/` directory does not exist, create it before saving.

```markdown
# [Project Name] Requirements

## Background
- **Current situation**: [How things are done today]
- **Problem**: [Why it's painful, why this is needed]
- **Expected benefit**: [What improves once this is built]

## Goals / Non-Goals

### Goals
1. [What this tool must achieve 1]
2. [What this tool must achieve 2]

### Non-Goals (explicitly out of scope)
- [What we're NOT building 1]
- [What we're NOT building 2]

## Target Users
- **[User type 1]**: [Characteristics]. [What they want to do with this tool]
- **[User type 2]**: [Characteristics]. [What they want to do with this tool]

## Core Features
- **[Feature 1]**: [What this feature does]
- **[Feature 2]**: [What this feature does]

## Detailed Requirements

### Must Have
- **[Item]**: [Specific description]
- **[Item]**: [Specific description]

### Nice to Have
- **[Item]**: [Specific description]
- **[Item]**: [Specific description]

## User Stories

### [Story title]
As a [user type],
I want to [action],
So that [value / goal].

### [Story title]
...

## Constraints
- [Constraint 1]
- [Constraint 2]
```

---

### Phase 4: Review and Save

1. Show the requirements document to the user and request review.
2. If there's feedback, incorporate it and revise.
3. Once finalized, save to `docs/requirements/{project-name}-requirements.md` (create the directory if it doesn't exist).
4. After saving, briefly confirm: "요구사항 정리 완료: `docs/requirements/{project-name}-requirements.md`" — do NOT add vibe coding instructions or usage guides.

---

## Ambiguity Categories

Common ambiguity types to probe during Phase 2:

| Category | Example Questions |
|----------|------------------|
| **Scope** | What's included? What's explicitly out? |
| **Behavior** | Edge cases? What happens on error? |
| **Interface** | Who/what interacts with it? How? |
| **Data** | Inputs? Outputs? Format? |
| **Constraints** | Performance? Compatibility? Security? |
| **Priority** | Must-have vs nice-to-have? |

---

## Rules

1. **No assumptions**: If ambiguous, ask — never answer on the user's behalf
2. **Preserve intent**: Refine, don't redirect
3. **Minimal questions**: Only ask what's necessary
4. **Respect answers**: Accept user decisions without pushback
5. **Track changes**: Always show Before/After comparison
6. **Communicate in Korean**: All user-facing communication (questions, summaries, guidance) must be in Korean. Skill definitions and document structure remain in English.
7. **Adapt to entry point**: If the user already provides a detailed brief, skip redundant questions and jump to clarifying only the gaps. If the conversation already contains context about what they want, extract it first before asking.

---

## Before/After Comparison

When presenting the review in Phase 4, show the original statement alongside the structured result:

```markdown
## What you originally said
"{user's original statement verbatim}"

## Clarified Requirements Summary
**Purpose**: [one line]
**Scope**: [included / excluded]
**Core Features**: [list]
**Target Users**: [who]

**Decisions made through clarification**:
| Question | Decision |
|----------|----------|
| [ambiguity 1] | [resolved answer] |
| [ambiguity 2] | [resolved answer] |
```
