# pragmatic-tools

비개발자가 막연한 아이디어를 명확한 요구사항 문서로 정리할 수 있도록 도와주는 Claude Code 플러그인입니다.

## Installation

```
/install-plugin https://github.com/Seokjoon-RIDI/ax-public-plugins
```

## Skills

### requirement-builder

vibe coding 전에 "무엇을 만들 것인지"를 정의하는 스킬입니다.

**트리거 예시:**
- "요구사항 정리해줘"
- "뭘 만들고 싶어"
- "기획 도와줘"
- "PRD 작성"
- `/requirement-builder`

**워크플로우:**
1. **아이디어 캡처** — 사용자의 초기 아이디어를 있는 그대로 기록
2. **반복 질문** — AskUserQuestion으로 모호한 부분을 하나씩 해소
3. **문서 구조화** — 수집된 정보를 요구사항 문서로 정리
4. **리뷰 & 저장** — Before/After 비교 후 `docs/requirements/`에 저장

**핵심 원칙:**
- What only, never How — 기술 스택이나 구현 방식은 다루지 않음
- 비개발자도 이해할 수 있는 쉬운 언어 사용
- 사용자의 의도를 보존하고, 절대 대신 판단하지 않음

## License

MIT
