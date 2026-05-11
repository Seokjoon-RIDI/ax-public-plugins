---
name: web-crawl-script-builder
description: Build a reusable Python crawler from one exploratory browser session, with safe 10→100→1000 scale-up gates. Use when user wants to collect structured data from a website repeatedly — "크롤링 스크립트", "사이트 데이터 수집", "작품 1000개 정보 뽑아줘", "scrape", "scraper", "crawler", "extract data from website", "bulk data collection", "/web-crawl-script-builder", or any [target site] + [structured fields] + [repetition/volume] task. Also trigger when user describes manual one-by-one gathering that should be automated. NOT for single-page lookups, auth-walled/paywalled data without approval, or non-web sources.
---

# web-crawl-script-builder

Turn one exploratory browser session into a reusable, validated crawler script,
with safe scale-up gates that prevent IP bans and silent data corruption.

## Core message

> Don't make the agent browse 1000 pages. Make the agent browse 10 pages and
> produce a script that runs 1000 times.

The agent's role is to **learn the site cheaply, then lock the learning into code**.
Browser exploration is a one-shot expense; the script is the durable artifact the
user can re-run weekly, hand to a teammate, or extend when fields change.

## Core principles

1. **Browse to learn, script to scale.** Direct agent browsing is for 5–20 sample
   pages — enough to find the URL pattern, the right selector, the network call,
   the pagination scheme. After that, the agent stops browsing and writes Python.
   Re-browsing the 21st page through the agent is almost always wrong.

2. **Cheap mistakes early, irreversible mistakes never.** Every jump in scale
   (10 → 100 → 1000) requires explicit user approval. The reason this is non-
   negotiable: a buggy script at 10 rows is a 30-second debugging exercise.
   The same bug at 1000 rows can already be enough to trip IP-level rate
   limiting on the target site — and that block may persist for hours or days
   beyond this session, on a server the user can't control. Going slow at the
   start is the only way to go fast overall.

3. **Prefer HTTP over browser, prefer API over HTML.** The extraction stack,
   from most reliable to least:
   1. Public/official API or documented JSON endpoint
   2. HTTP fetch + HTML parsing (BeautifulSoup / lxml / selectolax)
   3. Embedded JSON (Next.js `__NEXT_DATA__`, Nuxt `__NUXT__`, inline `<script>` JSON)
   4. Headless browser DOM extraction (Playwright)
   5. Vision / coordinate-based clicking (last resort, brittle)
   Move up the stack only when the layer above genuinely doesn't work — not
   because browser-rendering "feels safer." See `references/extraction_strategies.md`.

4. **Evidence over confidence.** Selectors that look right in DevTools often
   silently miss edge cases (sold-out items, premium-only fields, A/B-tested
   layouts). Before declaring an extraction strategy "done," lay 3–5 sample
   outputs next to the visible page content and check by eye.

5. **Communicate in Korean to the user.** Internal reasoning, code, and file
   contents stay in English where natural, but every question, status update,
   and approval request to the user is in Korean. The primary user is on the
   AX team and will be giving approvals throughout.

---

## Phase 1 — Scope clarification

**Purpose**: Get the minimum context needed to build the right thing. The user
typically gives a one-liner like "A사이트에서 작품 정보 1000개 뽑고 싶어".
That's enough to start the conversation, not to start coding.

Ask the user (one question per turn or grouped 2–3 max — don't dump 8 questions
at once):

1. **대상 사이트**: 도메인, 그리고 가능하면 샘플 URL 2–3개 (검색 결과 페이지 1개 + 상세 페이지 2개 정도).
2. **수집 필드**: 어떤 항목을 어떤 이름/형식으로 뽑을지. 모르면 "샘플 페이지 보고 제안할까요?"로 enter.
3. **입력 단위**: URL 리스트인지 / 검색어 리스트인지 / ID 범위인지 / 카테고리 시작점인지.
4. **예상 규모**: 10건? 1,000건? 10,000건? 정확하지 않아도 자릿수만 잡으면 됨.
5. **결과 포맷**: CSV / JSONL / Google Sheet / DB. 기본은 CSV.
6. **로그인 / 유료 / 지역 제한 여부**: 로그인이나 결제가 필요한 콘텐츠인가? 한국에서만 보이는가?
7. **재실행 주기**: 한 번만? 매주? 매일? — 이 답이 cron/스케줄러 설계 여부를 결정.

Record answers internally; you'll reuse them in Phase 5 to fill the README.

**Exit condition**: 대상 사이트가 정해졌고, 핵심 필드가 최소 2–3개 합의됐고,
샘플 URL이 최소 2개 손에 있다.

If the user can't answer any of 1–4, do **not** start exploring — pause and
ask. Crawling without a target is just clicking around.

---

## Phase 2 — Light compliance check

**Purpose**: Surface a few decision-relevant facts to the user. This is **not**
a legal review — just a quick sniff so the user can make an informed call.

Do these in parallel and report back in 4–6 lines:

1. **robots.txt 확인**: `https://<domain>/robots.txt`를 가져와서 대상 경로가
   `Disallow`되어 있는지 본다. 발견하면 그대로 인용해서 사용자에게 보여준다.
2. **로그인/유료 영역 여부**: 사용자가 준 샘플 URL을 익명으로 열었을 때
   같은 콘텐츠가 보이는가? 로그인 벽이나 paywall이 보이면 알린다.
3. **개인정보 포함 여부**: 수집 필드에 사용자 식별자(이메일, 전화번호, 실명,
   리뷰 작성자명 등)가 포함되는가? 포함되면 명시적으로 짚는다.
4. **명시적 ToS 금지 단서**: 페이지 푸터나 robots.txt 코멘트에 "automated
   access" / "scraping" 명시 금지가 있는가? (없으면 "확인된 명시 금지 없음"으로 보고)

이 결과를 사용자에게 보여주고 진행 여부를 물어본다. **자동으로 거절하지 않는다** —
판단은 사용자 몫. 단, 위 4개 중 하나라도 걸리면 진행 전에 명시적 "ok" 한 번을
받는다.

---

## Phase 3 — Browser exploration (5–20 samples)

**Purpose**: Find the cheapest, most reliable extraction layer. This is the
only phase where the agent itself drives a browser.

Use whatever browser-control mechanism is available in the current environment.
In rough order of preference: a Playwright MCP, Claude-in-Chrome / browser
automation MCPs, a browser-harness setup, or `playwright` invoked from a quick
Python script. If none of these are available, ask the user to install
Playwright (`uv pip install playwright && playwright install chromium`).

Do, in this order:

1. **Open one list / search-result page.** Note the URL pattern, pagination
   mechanism (page numbers? cursor? infinite scroll?), and how detail pages
   are linked.
2. **Open 2–3 detail pages.** Locate each target field in (a) the visible HTML,
   (b) `view-source:` HTML, (c) inline `<script>` JSON, (d) Network tab XHR
   responses. **Record where each field lives** — this decides the strategy.
3. **Vary edge cases on purpose.** Open: a sold-out / discontinued item, a
   premium-only item, a item with the longest title you can find, an item
   missing optional fields. Sites often render these differently.
4. **Watch the Network tab while browsing.** Many sites have an internal JSON
   API the page itself calls. If you find one (`/api/...`, `_next/data/...`,
   GraphQL endpoint), it's almost always a better extraction target than HTML.
5. **Note anti-bot signals.** Cloudflare challenge, Akamai cookies, captchas,
   rate-limit headers (`X-RateLimit-*`), 429 responses. Surface anything you see.

Stop at 20 pages. If you haven't figured out the structure by then, the
problem is the strategy, not more samples — go back to Phase 1 and clarify.

**Exit condition**: 한 줄로 "필드 X는 Y에서 가져온다"가 모든 필드에 대해 채워져 있다.
예: `title은 detail HTML의 <h1.product-name>에서, price는 /api/products/{id} JSON의 .price.amount에서`.

---

## Phase 4 — Extraction strategy decision

**Purpose**: Lock in the strategy *before* writing code. This avoids the
common failure mode of "I started writing Playwright code and now I'm stuck
making it work" when an HTTP fetch would have done the job.

Pick one **primary strategy** per field group, in this priority order:

| Priority | Strategy | When to use |
|----------|----------|-------------|
| 1 | Public / documented API | Site advertises an API or you found a clean JSON endpoint with no auth |
| 2 | Internal JSON endpoint (XHR) | Found via Network tab; same-origin, returns clean JSON |
| 3 | Embedded JSON (`__NEXT_DATA__` etc.) | Page is server-rendered with full state in a `<script>` tag |
| 4 | HTTP fetch + HTML parse | Fully server-rendered HTML with stable selectors |
| 5 | Headless browser DOM | Page is heavily client-rendered, no JSON layer reachable |
| 6 | Vision / coordinate clicks | Last resort — site is hostile or canvas-rendered |

If different fields need different layers, that's fine — combine. Common
pattern: list page via internal JSON endpoint (gets all detail URLs cheaply),
detail page via HTML parse.

**State the chosen strategy to the user in 2–3 lines and confirm before coding.**
This catches mismatches early ("아, 그 사이트 모바일 앱 API도 쓸 수 있어").

For deeper guidance on each strategy and their tradeoffs, see
`references/extraction_strategies.md`.

---

## Phase 5 — Script generation

**Purpose**: Produce the durable artifact. This is the whole point of the skill.

Create the output directory in the user's working directory:

```
crawler/
  README.md
  crawl_<site>.py        # main script — name after the site, e.g. crawl_ridi.py
  config.yaml             # rate limit, retry, schema, paths
  input_urls.csv          # input file (or input_queries.csv)
  outputs/
    sample_output.csv     # filled by smoke test in Phase 6
  logs/
    failed_urls.csv       # filled at runtime
  evidence/               # HTML snapshots of first N samples (Phase 6)
```

**Use `scripts/crawler_template.py` as the starting point.** It already
implements:

- Argparse-based CLI: `--input`, `--output`, `--limit`, `--resume`, `--evidence`
- Rate limiting (configurable RPS, default 1.0)
- Exponential backoff with jitter on 429 / 5xx
- Per-URL checkpointing so `--resume` continues where it left off
- Structured failure log (`failed_urls.csv` with URL + status + reason)
- Optional HTML evidence dump for the first N samples
- Schema validation (warn on missing required fields, log per-row)
- No-secrets-in-logs guard (cookie / authorization headers redacted)

The agent's job is to:

1. Copy the template into `crawler/crawl_<site>.py`.
2. Fill in three site-specific functions:
   - `fetch_one(url, session) -> response` — chooses HTTP or browser per Phase 4
   - `parse_one(response) -> dict` — extracts fields per Phase 3
   - `iter_inputs(input_path) -> Iterable[str]` — reads the input file
3. Fill in `config.yaml` with the chosen schema, rate limit, and strategy notes.
4. Write `README.md` (template below).

**README.md template** — fill in placeholders, keep all sections:

```markdown
# crawl_<site>

## What this collects
<one-line summary>

## Source
- Site: <domain>
- Strategy: <primary extraction strategy from Phase 4>
- robots.txt status: <result from Phase 2>

## Schema
| Field | Type | Source | Required |
|-------|------|--------|----------|
| ...   | ...  | ...    | ...      |

## Usage
```bash
# Smoke test (10 rows)
uv run python crawl_<site>.py --input input_urls.csv --output outputs/sample_output.csv --limit 10

# Resume after interruption
uv run python crawl_<site>.py --input input_urls.csv --output outputs/full.csv --resume
```

## Rate limit & politeness
- Default RPS: <value from config>
- Backoff: exponential, max 5 retries
- User-Agent: <value>

## Known pitfalls
<things found during exploration that future-you needs to remember>

## Re-run after schema drift
<which selector / endpoint is most likely to break, and how to spot it>
```

Do **not** hardcode credentials, cookies, or session tokens into the script.
If auth is needed, read it from an env var (`SITE_TOKEN`) and document the
required env vars in the README.

---

## Phase 6 — Smoke test (10 samples) — **HARD GATE**

**Purpose**: Catch bugs while they're still cheap.

Run the script on exactly 10 inputs. Save outputs to
`crawler/outputs/sample_output.csv` and dump HTML evidence for the first 3
into `crawler/evidence/` (the template supports this with `--evidence 3`).

Then **stop and present to the user**:

```
10건 smoke test 결과입니다:
- 성공: N/10
- 실패: M/10  (사유: <요약>)
- 필수 필드 누락 행: K
- 샘플 5행:
  <pretty-printed first 5 rows>
- evidence/ 에 HTML 3개 저장됨

다음 중 하나로 답해 주세요:
  1) 100건 pilot으로 진행
  2) 스크립트 수정 필요 (어떤 필드/케이스인지 알려주세요)
  3) 멈춤
```

**Do not proceed to Phase 7 without an explicit user response choosing option (1).**

The reason this gate is non-negotiable, not an "ALWAYS" rule but a real
tradeoff: 10건 결과를 보여주는 데 30초 걸리지만, 100건짜리 버그를 사후에
복구하려면 IP 차단 해제 대기 + 데이터 클렌징으로 며칠 단위가 든다.
사용자가 침묵하면 그것은 "go"가 아니라 "wait"다.

---

## Phase 7 — Pilot batch (100 samples) — **HARD GATE**

Run on 100 inputs with the same `--evidence 3`. Then stop and report:

```
100건 pilot 결과:
- 성공률: X%
- 평균 처리 시간: Ys/건
- rate-limit 신호: <429 횟수, Retry-After 값 등 / 없음>
- anti-bot 신호: <Cloudflare 챌린지, captcha, 갑작스런 5xx 등 / 없음>
- 필드별 누락률: <field: %>
- 예상 풀배치 소요 시간: <간단 추정>

다음 중 하나로 답해 주세요:
  1) 풀배치로 진행 (N건)
  2) rate limit 낮추고 다시 pilot
  3) 스크립트 수정
  4) 멈춤
```

If you saw any 429 or anti-bot signal during the pilot, **default-recommend
option (2)** with a slower rate (halve the RPS). Don't recommend option (1)
when you've already seen warning signs.

---

## Phase 8 — Production batch — **HARD GATE before kicking off**

Once the user approves, run the full batch with checkpointing on. Do not run
in the background and walk away on the first try — watch the first ~5 minutes
of output for:

- Sustained 429s (indicates the rate limit was wrong — pause and lower it)
- Sudden cliff in success rate (anti-bot kicked in — pause)
- Memory growth (likely a leak in the parser; restart with `--resume`)

If anything goes wrong, **stop the run, surface the issue, and ask the user**
before adjusting and resuming. Don't silently retry through a soft-ban.

For batches over ~5,000 rows, suggest the user split the run across multiple
sessions / days — this is more polite to the target server and gives natural
recovery checkpoints.

---

## Phase 9 — Knowledge handoff

After the production run completes, write `crawler/validation_report.md`:

```markdown
# Validation Report — <YYYY-MM-DD>

## Run summary
- Total inputs: N
- Successful: M (M/N %)
- Failed: K (see logs/failed_urls.csv)
- Wallclock: <duration>
- Average RPS achieved: <value>

## Field-level quality
| Field | Filled | Empty | Empty rate | Notes |
|-------|--------|-------|-----------|-------|
| ...   | ...    | ...   | ...       | ...   |

## Sampling check
Manually verified rows: <list of 5–10 row indices the user spot-checked>

## Known issues
- <e.g. "premium-only items return null for `original_price`">

## Re-run instructions
<exact command, env vars, expected runtime>
```

Then summarize the run to the user in 5–6 lines and point them at the
artifacts. The skill is done.

---

## What this skill does NOT do

Be honest about scope; don't try to expand into these without explicit user request:

- **Captcha solving / fingerprint evasion / proxy rotation.** If the site is
  actively blocking automated access, surface that to the user and stop.
  Bypassing it is a separate, policy-sensitive decision.
- **Continuous scheduling / monitoring.** This skill produces a script the
  user can wire into cron themselves; it doesn't run a service.
- **Login-walled or paywalled content** without the user explicitly providing
  credentials and confirming the legal/policy basis.
- **Personal data harvesting at scale.** If the schema starts including names,
  emails, phone numbers, or other PII, pause and flag it before continuing.

---

## Operating rules

1. **Korean to the user, code in English.** All status messages, gate prompts,
   and questions to the user are in Korean. Code, comments, log lines, and
   filenames stay in English.
2. **Hard gates are gates, not suggestions.** Phases 6, 7, and 8 require
   explicit user approval to advance. Treat silence as "wait."
3. **No credentials in artifacts.** Cookies, tokens, and passwords never get
   written to `crawler/` or to the run log. The template's logger redacts
   `Authorization` and `Cookie` headers; preserve that.
4. **Default-polite.** Default rate limit is 1 RPS. Default User-Agent
   identifies the script and includes a contact hint. Default backoff is
   exponential with jitter. Don't override these defaults without a reason
   you've stated to the user.
5. **Surface what you don't know.** "이 사이트가 GraphQL을 쓰는지 확실치 않습니다"
   is a fine answer in Phase 3. Pretending to know is the failure mode that
   leads to bad scripts.
