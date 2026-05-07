# Extraction strategies — when to use which

This is a deeper reference for Phase 4 of the skill workflow. SKILL.md gives the
priority list; this file explains the *why* and the failure modes of each layer.

The core idea: each layer up this list is faster, cheaper, and less brittle than
the one below. You drop down only when the layer above genuinely doesn't work
for the target site — not because rendering a full browser "feels safer."

---

## 1. Public / official API

**Signal**: site has a developer portal, documented endpoints, API key signup
flow, or there's a third-party SDK that wraps the same data.

**Why prefer**: legally and technically the cleanest path. Schemas are stable,
rate limits are explicit, errors are structured.

**Watch out for**:
- Free-tier rate limits may be lower than what an HTML scrape would tolerate
- API responses sometimes return a *different* projection of the data than the
  website does (different field names, currency conversion already applied,
  premium fields hidden behind a higher tier). Spot-check by comparing one
  API response to the same item's web page.

**Decision rule**: if an API exists and covers your fields, use it even if the
HTML scrape would be faster — long-term durability beats short-term speed.

---

## 2. Internal JSON endpoint (XHR discovered via Network tab)

**Signal**: the website itself calls something like `/api/v2/products/123` or
GraphQL `/graphql` while you browse, and the response is clean JSON containing
your target fields.

**Why prefer over HTML parsing**: structured data, no selector brittleness, no
JS rendering needed. Often 5–10× faster than fetching the rendered HTML page.

**Watch out for**:
- Anti-CSRF tokens or signed timestamps in the request — sometimes the server
  rejects requests that don't come from the page's JS. Replay the request from
  curl/httpx with the same headers (minus `Cookie` if you can) to verify.
- Hidden auth: check whether the endpoint actually requires the session cookie
  or just an `X-Client-ID` header. The latter is much simpler to script.
- Schema drift: internal endpoints have no contract with you; they can change
  without notice. Document the endpoint in the README so future-you knows
  where to look when it breaks.

**Decision rule**: if you find a clean JSON endpoint, default to it over HTML
parsing unless it requires significant auth gymnastics.

---

## 3. Embedded JSON (`__NEXT_DATA__`, `__NUXT__`, inline `<script>` JSON)

**Signal**: page source contains a `<script id="__NEXT_DATA__" type="application/json">`
tag (Next.js apps), or a `window.__NUXT__ = {...}` assignment (Nuxt), or a
plain inline `<script type="application/ld+json">` (schema.org markup).

**Why prefer over selector-based HTML parsing**: the JSON contains the
*pre-render* data, often with more fields than the visible page (timestamps,
internal IDs, draft flags). It's also resilient to layout/CSS changes — the
page can be redesigned and the JSON usually stays the same.

**Watch out for**:
- `__NEXT_DATA__` can be huge; navigate to the right path
  (`props.pageProps.product` is a common shape) instead of dumping it all.
- JSON-LD (schema.org) often has only a subset of fields and may be wrong
  about prices in promotion-heavy sites. Use it as a hint, not as truth.

**Decision rule**: extract once with a quick `re.search()` for the JSON blob
boundaries, parse with `json.loads`, then traverse like any dict.

---

## 4. HTTP fetch + HTML parse

**Signal**: page is server-rendered with all visible content present in the
HTTP response (you can `view-source:` and find your target text). No JS needed.

**Tooling**: `httpx` for fetch + `selectolax` (fast) or `BeautifulSoup` + `lxml`
(more permissive). Avoid `requests` for new code — `httpx` has a better client
abstraction and async support if you ever need it.

**Watch out for**:
- **Selector brittleness**. Target stable attributes: `data-*` attributes,
  `itemprop` (microdata), or text-based anchors ("가격" label + sibling).
  Avoid CSS classes that look auto-generated (`._3kxYp`).
- **Encoding**. Some Korean sites still serve EUC-KR. `httpx` will guess from
  headers; if you get mojibake, set `response.encoding` manually.
- **Conditional rendering** for sold-out / premium / region-locked items.
  Always test against an item with each variant.
- **Server-side bot detection** that returns a different (smaller) HTML
  payload to non-browser User-Agents. If your `<title>` looks fine but the
  body is empty, suspect this and try setting a realistic UA + Accept headers.

**Decision rule**: this is the workhorse layer. Reach for it when 1–3 don't
apply.

---

## 5. Headless browser DOM (Playwright)

**Signal**: target fields are populated by JavaScript after page load and
*don't* live in any of the JSON layers above. Common in heavy SPAs, search
results that lazy-load, infinite scroll, etc.

**Why a last-resort-before-vision**: Playwright is slow (1–3s per page),
memory-hungry, and easier for sites to fingerprint as automation. Every
batch via Playwright is roughly 5–10× more expensive than HTTP fetching.

**Tooling**: `playwright` Python sync API. For 1000+ pages, use
`playwright.async_api` with bounded concurrency (5–10 pages in flight max).

**Patterns that work**:
- `page.wait_for_selector("[data-testid='price']")` — wait for the actual
  field, not just `domcontentloaded`.
- Extract via `page.locator(...).text_content()` rather than running custom
  JavaScript via `page.evaluate()` — easier to debug and audit.
- Reuse a single browser context across pages (reuses cookies, faster than
  cold-starting per page).

**Watch out for**:
- Playwright's default User-Agent says "HeadlessChrome" — many sites block this.
  Set a realistic UA via `browser.new_context(user_agent=...)`.
- Memory: contexts leak. Restart the browser every ~500 pages.
- Headful vs headless: a few sites only render correctly headful. If a field
  is mysteriously empty, try `headless=False` once for one URL to compare.

**Decision rule**: use only when 1–4 are genuinely unworkable, and even then
consider a hybrid (Playwright to get the list of detail URLs, HTTP fetch for
the detail pages).

---

## 6. Vision / coordinate-based clicking

**Signal**: page renders to canvas (some maps, some PDFs-as-canvas), or
selectors are deliberately obfuscated and shuffled per request, or the site
serves entirely different DOM trees to automated clients.

**Why genuinely last-resort**: brittle (any layout change breaks coordinates),
slow (one screenshot + LLM call per field), and a clear signal to the target
site that automation is happening. Often a sign that the user should
reconsider whether to scrape this site at all.

**Decision rule**: if you find yourself reaching for vision, stop and re-confirm
with the user that the data is worth the cost — both technical and
relationship-with-the-target-site.

---

## Hybrid patterns worth knowing

**List + detail split**: very common. Use a cheap layer (API or HTML) for the
list page to harvest detail URLs, then use the appropriate layer per detail
page. Often the list and detail need different strategies.

**Login once, fetch many**: if auth is required, do a one-time Playwright
login, dump the resulting cookies, then switch to HTTP fetching with those
cookies for the bulk run. Document the cookie refresh procedure in the
README — most sites' cookies expire in days to weeks.

**Sitemap shortcut**: many sites publish `/sitemap.xml` (or
`sitemap_index.xml`). If your input is "all products on the site," the
sitemap is usually the cleanest input source — much better than scraping
the navigation. Check this before designing the input pipeline.

---

## Field-by-field strategy

You don't have to use one strategy for everything. A typical mature crawler:

| Field group | Strategy |
|-------------|----------|
| List of detail URLs | sitemap.xml |
| Title, price, basic metadata | HTTP fetch + HTML parse via selectolax |
| Inventory / stock status | Internal JSON XHR |
| Long descriptions with rich formatting | Embedded JSON (`__NEXT_DATA__`) to preserve structure |
| Review snippets | Public API if available, else HTML parse |

Mix and match. The crawler template's `parse_one(response, url)` can call
multiple sub-fetchers internally — just be careful about counting toward
the rate limit.
