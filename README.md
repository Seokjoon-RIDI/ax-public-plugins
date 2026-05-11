# ax-public-plugins

AX팀 공개 Claude Code 플러그인 — 요구사항 정리(PRD), ralph-loop 프롬프트 생성, 웹 크롤링 스크립트 빌더 등 실무 도구 모음.

## Installation

```
/install-plugin https://github.com/Seokjoon-RIDI/ax-public-plugins
```

## Skills

### requirement-builder

vibe coding 전에 "무엇을 만들 것인지"를 정의하는 스킬. 비개발자가 막연한 아이디어를 명확한 요구사항 문서로 정리하도록 돕습니다.

**트리거 예시**
- "요구사항 정리해줘"
- "뭘 만들고 싶어"
- "기획 도와줘"
- "PRD 작성"
- `/requirement-builder`

**워크플로우**
1. **아이디어 캡처** — 사용자의 초기 아이디어를 있는 그대로 기록
2. **반복 질문** — AskUserQuestion으로 모호한 부분을 하나씩 해소
3. **문서 구조화** — 수집된 정보를 요구사항 문서로 정리
4. **리뷰 & 저장** — Before/After 비교 후 `docs/requirements/`에 저장

**핵심 원칙**
- What only, never How — 기술 스택/구현 방식/아키텍처는 다루지 않음
- 비개발자도 이해할 수 있는 쉬운 언어 사용
- 사용자의 의도를 보존하고, 절대 대신 판단하지 않음

---

### ralph-prompt-builder

Plan 모드에서 작성된 구현 계획 문서를 입력받아 `ralph-loop` 실행용 프롬프트를 자동 생성하는 스킬. 완료 조건을 추출하고 `<promise></promise>` 태그를 포함한 명령어로 포맷팅합니다.

**트리거 예시**
- "ralph 프롬프트 만들어줘"
- "이 플랜으로 ralph 돌리자"
- "plan을 ralph로"
- `/ralph-prompt-builder`

**입력/출력**
- 입력: Plan 문서(@mention)
- 출력: `/ralph-loop:ralph-loop` 명령어 (promise 포함)

---

### web-crawl-script-builder

웹사이트에서 반복적으로 데이터를 수집해야 할 때, agent가 (1) 샘플 페이지를 직접 탐색해 URL 패턴·selector·API endpoint를 학습하고, (2) 이를 재사용 가능한 Python crawler로 고정한 뒤, (3) 단계적 scale-up(10 → 100 → 1000)을 사용자 승인 게이트로 진행하는 스킬.

**트리거 예시**
- "크롤링 스크립트 만들어줘"
- "작품 1000개 정보 뽑아줘"
- "사이트 데이터 수집"
- `/web-crawl-script-builder`

**핵심 메시지**
> agent가 1000 페이지를 직접 브라우징하지 않는다. agent가 10 페이지를 브라우징하고, 1000번 돌릴 스크립트를 만든다.

**번들 자원**
- `scripts/crawler_template.py` — rate limit, exponential backoff with jitter, checkpoint/resume, 429/Retry-After, schema validation, evidence dump, 헤더 redact 로거 포함
- `references/extraction_strategies.md` — 6단계 추출 전략(Public API → Internal JSON XHR → Embedded JSON → HTML parse → Playwright → Vision) 가이드

---

## License

MIT
