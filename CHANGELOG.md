# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.3.0] - 2026-05-07

### Added
- `web-crawl-script-builder` skill: 웹 사이트 데이터를 반복적으로 수집해야 할 때 agent가 (1) 5~20개 샘플을 직접 브라우저로 탐색해 URL 패턴/selector/API endpoint를 학습하고, (2) 이를 재사용 가능한 Python crawler 스크립트로 고정한 뒤, (3) 단계적 scale-up(10 → 100 → 1000)을 사용자 승인 게이트로 진행하는 워크플로우.
  - 9-Phase 워크플로우 (Scope → Compliance → Exploration → Strategy → Script gen → Smoke/Pilot/Prod gates → Handoff)
  - Hard gate를 rote MUST 대신 cost-asymmetry 설명으로 framing — IP 차단 등 비가역적 사고 방지
  - Tool-agnostic 표현으로 Claude Code / Codex 양쪽에서 동작
  - 한국어 사용자 커뮤니케이션
- `scripts/crawler_template.py` 번들 — rate limit, exponential backoff with jitter, checkpoint/resume, 429/Retry-After 처리, schema validation, evidence dump, Authorization/Cookie 헤더 redact 로거 포함. Agent는 `fetch_one`/`parse_one`/`iter_inputs` 3개 함수만 사이트별로 채움.
- `references/extraction_strategies.md` — 6단계 추출 전략(Public API → Internal JSON XHR → Embedded JSON → HTML parse → Playwright → Vision) deep-dive와 layer별 실패 모드 가이드.

### Changed
- 플러그인 description에 "웹 크롤링 스크립트 빌더" 추가 (plugin.json, marketplace.json).
- keywords에 `web-scraping`, `crawler`, `data-collection` 추가.

## [1.0.0] - 2026-03-23

### Added
- Initial public release of pragmatic-tools plugin
- `requirement-builder` skill: 비개발자를 위한 요구사항 정의 워크플로우
  - 4-Phase workflow (Capture → Clarify → Structure → Review)
  - AskUserQuestion 기반 반복 질문으로 모호함 해소
  - Before/After 비교 제공
  - `docs/requirements/` 경로에 자동 저장 (디렉토리 없으면 생성)
  - 한국어 커뮤니케이션 지원
