# Deep Research Agent — Sprint Implementation Plan

## Planning Philosophy

This plan follows three rules:

1. **MVP first**: The earliest possible end-to-end working pipeline, even if naive. A bad report from a working system beats a perfect architecture that doesn't run.
2. **Always shippable**: After every task, `python -m deep_research "any query"` runs without errors and produces output. No task leaves the system broken.
3. **Each task adds visible value**: Every task either makes the agent produce better results, handle more edge cases, or become easier to use. No pure refactors without user-facing improvement.

---

## Sprint Overview

| Sprint | Theme | Outcome |
|--------|-------|---------|
| Sprint 1 | **Straight-line MVP** | Single query → search → fetch → extract → report. No loops, no planning. Works end-to-end. |
| Sprint 2 | **Add the Brain** | Query planning + research loop with gap analysis. Agent now iterates. |
| Sprint 3 | **Quality & Resilience** | Better prompts, error handling, citations, output formatting. Reports are actually good. |
| Sprint 4 | **Features & Polish** | Multiple search providers, configurable models, verbose mode, README. Ready for users. |

---

## Sprint 1: Straight-Line MVP

**Goal**: The simplest possible pipeline that takes a query and produces a Markdown report. No planning step, no loops, no gap analysis. Just: search → fetch → extract → write.

### Task 1.1 — Project Scaffold & CLI Shell
**Time**: 0.5 day

**What to build**:
- Initialize project: `pyproject.toml` with all dependencies, `src/deep_research/` package structure.
- `models.py` with the core Pydantic models: `Config`, `SearchResult`, `PageContent`, `Finding`, `ResearchReport`.
- `config.py` that loads `GEMINI_API_KEY` and `TAVILY_API_KEY` from `.env`.
- `cli.py` with a click command that accepts a query string, loads config, and prints "Starting research on: {query}".
- `__main__.py` so `python -m deep_research "test"` works.
- `.env.example` with placeholder keys.

**Acceptance criteria**:
```bash
pip install -e .
python -m deep_research "test query"
# Output: "Starting research on: test query"
# Exit code 0, no errors
```

**Definition of done**: The project installs, the CLI runs, config loads from `.env`. No research happens yet — just the skeleton.

---

### Task 1.2 — Tavily Search Integration
**Time**: 1 day

**What to build**:
- `searcher.py` with an async function: takes a query string → calls Tavily API → returns `list[SearchResult]`.
- Wire it into the CLI: after parsing the query, run a search and print results to stdout.
- Handle basic errors: missing API key raises a clear error, Tavily returning 4xx/5xx logs a warning.

**Acceptance criteria**:
```bash
python -m deep_research "vertical farming economics"
# Output:
# Searching: "vertical farming economics"
# Found 8 results:
#   1. https://agfunder.com/... - "Vertical Farming Market Report..."
#   2. https://... - "..."
#   ...
```

**Definition of done**: Real web search results are fetched and printed. The system still doesn't do anything with them — just proves search works.

---

### Task 1.3 — Page Fetching & Content Extraction
**Time**: 1 day

**What to build**:
- `fetcher.py` with an async function: takes a URL → fetches HTML via `aiohttp` → extracts article text via `trafilatura` → returns `PageContent`.
- Add concurrent fetching: take the top 5 URLs from search results, fetch them in parallel with `asyncio.Semaphore(5)`.
- Wire into CLI: after search, fetch pages and print extracted text (first 500 chars per page).
- Handle failures: timeout after 10s, skip 403/404/5xx, skip pages where trafilatura extracts nothing.

**Acceptance criteria**:
```bash
python -m deep_research "vertical farming economics"
# Output:
# Searching: "vertical farming economics" → 8 results
# Fetching top 5 pages...
#   ✓ agfunder.com (2,847 chars)
#   ✓ bloomberg.com (3,102 chars)
#   ✗ wsj.com (paywall/failed)
#   ✓ sciencedirect.com (4,521 chars)
#   ✓ mordorintelligence.com (1,983 chars)
```

**Definition of done**: Pages are fetched and readable text is extracted. Failures are handled gracefully (no crashes).

---

### Task 1.4 — Gemini LLM Client & Finding Extraction
**Time**: 1.5 days

**What to build**:
- `llm_client.py` with `GeminiClient`: wraps `google-genai` SDK. Two methods:
  - `complete(prompt, system, ...)` → returns raw text.
  - `complete_structured(prompt, response_model, ...)` → returns validated Pydantic model.
- `extractor.py`: takes a `PageContent` + a query string → sends the extraction prompt to Gemini → returns `list[Finding]`.
- Wire into CLI: after fetching pages, extract findings from each page and print them.
- Use the extraction prompt from the architecture doc. Use the query itself as the "research question" (no sub-questions yet).

**Acceptance criteria**:
```bash
python -m deep_research "vertical farming economics"
# Output:
# Searching → 8 results
# Fetching 5 pages...
# Extracting findings...
#   agfunder.com → 3 findings
#   bloomberg.com → 2 findings
#   sciencedirect.com → 4 findings
#   mordorintelligence.com → 1 finding
# Total: 10 findings
```

**Definition of done**: Real findings are extracted from real pages using Gemini. The system is doing actual research, just not writing a report yet.

---

### Task 1.5 — Naive Report Synthesis & File Output
**Time**: 1.5 days

**What to build**:
- `synthesizer.py`: takes the query + all findings → sends the synthesis prompt to Gemini → returns Markdown report text.
- Citation post-processing: parse the Markdown for `[1]`, `[2]` references, build a sources list from finding URLs, append to the report.
- Write the report to `output/{slugified-query}.md`.
- `logger.py`: replace all the ad-hoc print statements with structured `[SEARCH]`, `[FETCH]`, `[EXTRACT]`, `[SYNTH]`, `[DONE]` log lines using `rich`.

**Acceptance criteria**:
```bash
python -m deep_research "vertical farming economics"
# Output:
# [SEARCH]   "vertical farming economics" → 8 results
# [FETCH]    Fetching 5 pages...
# [EXTRACT]  10 findings from 4 sources
# [SYNTH]    Generating report...
# [DONE]     Report saved to output/vertical-farming-economics.md (1,247 words)
```

The generated Markdown file is readable, has sections, has inline citations `[1]`, and a Sources list at the bottom.

**Definition of done**: **MVP is complete.** A user can ask any question and get a Markdown report with citations. It's shallow (one search, no planning, no iteration), but it works end-to-end.

---

## Sprint 2: Add the Brain

**Goal**: Transform the naive straight-line pipeline into an intelligent agent that plans research and iterates to fill knowledge gaps.

### Task 2.1 — Query Planning Step
**Time**: 1.5 days

**What to build**:
- `planner.py`: takes the user query → sends the planning prompt to Gemini with structured output → returns `ResearchPlan` with 3-7 sub-questions.
- Update `orchestrator.py` (extract the pipeline from CLI into its own module): insert the planning step before search. For now, just use the first sub-question's search queries instead of the raw user query. Other sub-questions are logged but ignored.
- Add `[PLAN]` log line showing the generated sub-questions.

**Acceptance criteria**:
```bash
python -m deep_research "vertical farming economics"
# [PLAN]     Decomposed into 5 sub-questions:
#            1. [HIGH] What is the current market size? → 2 search queries
#            2. [HIGH] What are the major cost components? → 2 search queries
#            3. ...
# [SEARCH]   sq-1: "vertical farming market size 2025" → 8 results
# ... (rest of pipeline runs using sq-1's queries only)
# [DONE]     Report saved (covers only sq-1, but works)
```

**Definition of done**: The planner produces sensible sub-questions. Only the first sub-question is researched (sequential expansion comes next). The report is still generated — just from fewer findings.

---

### Task 2.2 — Sequential Sub-Question Research
**Time**: 1 day

**What to build**:
- Update the orchestrator to loop over ALL sub-questions (sorted by priority).
- For each sub-question: run its search queries → fetch pages → extract findings.
- Accumulate findings across all sub-questions.
- Pass all accumulated findings to the synthesizer.
- Track `visited_urls` to avoid re-fetching the same page.

**Acceptance criteria**:
```bash
python -m deep_research "vertical farming economics"
# [PLAN]     5 sub-questions
# [SEARCH]   sq-1: "vertical farming market size 2025" → 8 results
# [FETCH]    5 pages
# [EXTRACT]  8 findings
# [SEARCH]   sq-2: "vertical farming cost breakdown" → 7 results
# [FETCH]    4 new pages (3 already visited)
# [EXTRACT]  6 findings
# ... (all 5 sub-questions researched)
# [SYNTH]    Generating report from 28 findings across 15 sources...
# [DONE]     Report saved (2,891 words)
```

**Definition of done**: All sub-questions are researched. Reports are noticeably more comprehensive than Sprint 1's MVP. The agent still doesn't iterate within a sub-question (that's next).

---

### Task 2.3 — Gap Analysis & Follow-Up Loop
**Time**: 2 days

**What to build**:
- `gap_analyzer.py`: takes a sub-question + findings collected so far → sends the gap analysis prompt to Gemini → returns `GapAnalysis` with `should_continue` and `follow_up_queries`.
- Update the orchestrator: after extracting findings for a sub-question, run gap analysis. If `should_continue` is true, use the follow-up queries for another round of search → fetch → extract. Repeat up to `MAX_SEARCH_DEPTH` (default 3) rounds per sub-question.
- Add `search_count` tracking. Stop the entire loop if `MAX_TOTAL_SEARCHES` (default 30) is reached.
- Add `[GAP]` log lines.

**Acceptance criteria**:
```bash
python -m deep_research "vertical farming economics"
# [PLAN]     5 sub-questions
# [SEARCH]   sq-1: "vertical farming market size 2025" → 8 results
# [FETCH]    5 pages
# [EXTRACT]  5 findings
# [GAP]      sq-1: 2 gaps remaining → follow-up queries generated
# [SEARCH]   sq-1: "vertical farming CAGR projection 2030" → 6 results
# [FETCH]    4 new pages
# [EXTRACT]  3 findings
# [GAP]      sq-1: complete ✓
# [SEARCH]   sq-2: ...
# ...
```

**Definition of done**: **The agent now iterates.** It identifies what's missing and searches for it. Reports are significantly deeper and more complete. This is the core intelligence of the system.

---

### Task 2.4 — Budget Management & Graceful Termination
**Time**: 0.5 day

**What to build**:
- Log remaining search budget after each search: `[BUDGET] 23/30 searches used`.
- When budget is exhausted mid-loop, break cleanly and proceed to synthesis.
- When budget is exhausted, add a note to the synthesis prompt: "Note: research was cut short due to search budget limits. Some sub-questions may be incompletely covered."
- Add `--depth` and `--searches` CLI flags that override defaults.

**Acceptance criteria**:
```bash
python -m deep_research "complex query" --searches 10
# ... runs until 10 searches used ...
# [BUDGET]   10/10 searches used, stopping research
# [SYNTH]    Generating report from partial findings...
# [DONE]     Report saved (report acknowledges incomplete coverage)
```

**Definition of done**: The agent never hangs or loops forever. Budget is respected. Partial results still produce a useful report.

---

## Sprint 3: Quality & Resilience

**Goal**: Make the reports actually good and the agent robust against real-world failures.

### Task 3.1 — Improved Extraction Prompts & Finding Deduplication
**Time**: 1.5 days

**What to build**:
- Refine the extraction prompt: add examples of good vs. bad findings, emphasize specificity (numbers > vague claims), penalize duplication.
- Add a deduplication pass after extraction: before adding new findings to the master list, check if any existing finding has a very similar `claim` string (simple substring/overlap check). Skip duplicates.
- Lower extraction temperature to 0.2 for more consistent, factual output.
- Test with 5+ diverse queries and manually review finding quality.

**Acceptance criteria**:
- Run on 5 different queries. Findings should be specific (contain numbers, dates, names — not "the market is growing"). Duplicate findings across pages should be reduced by >50% compared to before this task.

**Definition of done**: Findings are higher quality and less repetitive. Reports read better because the synthesizer has better raw material.

---

### Task 3.2 — Improved Synthesis Prompts & Report Structure
**Time**: 1.5 days

**What to build**:
- Refine the synthesis prompt: add explicit instructions for thematic grouping (not just listing findings), require an executive summary, require data-driven claims, require smooth transitions between sections.
- Add word count awareness: if findings are sparse (<10), prompt for a shorter focused report; if rich (>25), prompt for a comprehensive report.
- Post-process: validate all `[N]` citation numbers reference a real source. Remove orphaned citations. Deduplicate the sources list.
- Test with 5+ queries and compare report quality before/after.

**Acceptance criteria**:
- Reports have a clear executive summary, 3-6 thematic sections (not just repeating sub-questions), and every `[N]` citation maps to a real URL in the Sources list.

**Definition of done**: Reports are publication-quality. A user could share the output without embarrassment.

---

### Task 3.3 — Robust Error Handling & Retry Logic
**Time**: 1.5 days

**What to build**:
- Search failures: retry once with 2s backoff. On second failure, skip that query, log `[ERROR]`.
- Fetch failures: already handled (returns None), but add specific handling for: connection timeout (10s), SSL errors, encoding errors, HTTP 429 (backoff).
- LLM failures: retry once on any `google.genai` exception. On rate limit (429), exponential backoff up to 3 retries. On safety filter block, log warning, skip that page's extraction.
- Pydantic validation failure (bad JSON from LLM): retry the LLM call once. On second failure, skip.
- Wrap the entire orchestrator in a top-level try/except: if anything unexpected happens, attempt to synthesize with whatever findings were collected so far.

**Acceptance criteria**:
- Simulate failures: disconnect search API mid-run → agent continues with other queries. Give it a URL that always times out → agent skips it. The agent NEVER crashes with an unhandled exception for any input.

**Definition of done**: The agent is resilient. It degrades gracefully, always produces some output, and never shows raw tracebacks to the user.

---

### Task 3.4 — Rich Progress Output & Timing
**Time**: 1 day

**What to build**:
- Add elapsed time to each log line: `[SEARCH]   sq-1: "query" → 8 results (1.2s)`.
- Add a summary block at the end: total time, searches used, pages fetched, findings extracted, report word count.
- Add a `rich` spinner/progress indicator during long operations (LLM calls, page fetching).
- In `--verbose` mode, show: each finding's claim as it's extracted, the gap analysis reasoning, the planner's approach.

**Acceptance criteria**:
```bash
python -m deep_research "query"
# ... colored log lines with timing ...
#
# ── Summary ─────────────────────────
#  Duration:    2m 34s
#  Searches:    18/30
#  Pages:       22 fetched, 19 extracted
#  Findings:    31
#  Report:      3,421 words → output/query.md
# ─────────────────────────────────────
```

**Definition of done**: The CLI experience feels polished and professional. The user knows exactly what's happening at every moment.

---

## Sprint 4: Features & Polish

**Goal**: Add configurability, additional providers, and documentation for real-world usage.

### Task 4.1 — Serper Search Provider
**Time**: 1 day

**What to build**:
- Add a Serper implementation in `searcher.py` alongside Tavily.
- Use a provider factory: `config.search_provider` → selects which implementation to use.
- Wire the `--provider serper` CLI flag.
- Both providers return the same `list[SearchResult]` — the rest of the pipeline doesn't care which was used.

**Acceptance criteria**:
```bash
python -m deep_research "query" --provider serper
# Works identically to tavily, using Serper API
```

**Definition of done**: Two working search providers. Adding a third (SearXNG) would follow the same pattern.

---

### Task 4.2 — SearXNG Search Provider (Self-Hosted)
**Time**: 0.5 day

**What to build**:
- Add a SearXNG implementation in `searcher.py`: HTTP GET to `{SEARXNG_URL}/search?q={query}&format=json`.
- Wire `--provider searxng` CLI flag.
- Document SearXNG setup in README (Docker one-liner).

**Acceptance criteria**:
```bash
docker run -p 8080:8080 searxng/searxng
python -m deep_research "query" --provider searxng
# Works using local SearXNG instance
```

**Definition of done**: Three search providers available. Users with no API keys can self-host SearXNG for free unlimited searches.

---

### Task 4.3 — Model Selection & Thinking Mode
**Time**: 1 day

**What to build**:
- Wire `--model` CLI flag to pass any Gemini model string through to the client.
- Add a `--thinking` flag that enables Gemini's thinking mode (`thinking_config`) for the planning and gap analysis steps, which benefit most from deeper reasoning.
- Log which model is being used: `[CONFIG] Model: gemini-2.5-pro, Thinking: on`.
- Document the cost tradeoffs in the README (Flash = cheap/fast, Pro = better quality/slower).

**Acceptance criteria**:
```bash
python -m deep_research "query" --model gemini-2.5-pro --thinking
# Uses Pro model with thinking enabled
# Report quality is noticeably better for complex queries
```

**Definition of done**: Users can choose their quality/cost tradeoff. Thinking mode is available for power users.

---

### Task 4.4 — Output Formatting & Report Metadata
**Time**: 1 day

**What to build**:
- Add YAML frontmatter to the report with metadata: query, date, model, duration, search count, sources count.
- Slugify the report filename from the query: `output/economics-of-vertical-farming-2025.md`.
- If file already exists, append a timestamp suffix to avoid overwriting.
- Add `--output` CLI flag for custom output directory. Create the directory if it doesn't exist.
- Print the full file path at the end for easy copy-paste.

**Acceptance criteria**:
```
---
query: "What are the economics of vertical farming in 2025?"
date: 2025-03-07
model: gemini-2.5-flash
duration: 2m 18s
searches: 22
sources: 14
---

# Economics of Vertical Farming in 2025
...
```

**Definition of done**: Reports have proper metadata, sensible filenames, and go where the user expects.

---

### Task 4.5 — Domain Blocklist & Source Quality Filtering
**Time**: 1 day

**What to build**:
- Add a default blocklist of low-quality domains: pinterest, quora (answers), reddit, youtube, facebook, instagram, tiktok, twitter/x.
- Add an allowlist concept: if the user's query is about social media, these domains should NOT be blocked. Use a simple heuristic: if the query mentions the platform name, don't block it.
- In the extraction step, give a bonus to findings from known high-quality domains: .gov, .edu, established news orgs, peer-reviewed journals.
- Rank findings by a composite score: confidence × source quality. Pass the top findings to the synthesizer if there are too many (>40).

**Acceptance criteria**:
- A query about "climate change policy" should not return Pinterest or Reddit results.
- A query about "Reddit's IPO" should still include Reddit as a source.
- High-quality sources (.gov, .edu) appear prominently in reports.

**Definition of done**: Source quality is actively managed. Reports draw from authoritative sources.

---

### Task 4.6 — README, Setup Guide & End-to-End Testing
**Time**: 1.5 days

**What to build**:
- `README.md` with: project description, quick start (3 commands: clone, install, run), configuration reference (all env vars and CLI flags), example output, architecture overview (link to design doc), cost estimates per model.
- 3-5 end-to-end test cases in `tests/test_e2e.py` that run the full pipeline against real APIs (gated behind `--run-e2e` flag). Verify: report file is created, report has >500 words, report has >3 sources, report has valid citation numbers.
- Unit tests for: config loading, URL deduplication, citation post-processing, filename slugification.

**Acceptance criteria**:
- A new developer can clone the repo, follow the README, and produce their first report in under 5 minutes.
- `pytest tests/ -v` passes (unit tests, mocked).
- `pytest tests/ -v --run-e2e` passes (real API calls, requires keys).

**Definition of done**: The project is ready for other developers to use and contribute to.

---

## Task Dependency Map

```
1.1 Scaffold
 │
 ├──► 1.2 Search
 │     │
 │     ├──► 1.3 Fetch
 │     │     │
 │     │     ├──► 1.4 LLM + Extraction
 │     │     │     │
 │     │     │     ├──► 1.5 Synthesis & Output ◄── MVP COMPLETE
 │     │     │     │     │
 │     │     │     │     ├──► 2.1 Query Planning
 │     │     │     │     │     │
 │     │     │     │     │     ├──► 2.2 Sequential Sub-Questions
 │     │     │     │     │     │     │
 │     │     │     │     │     │     ├──► 2.3 Gap Analysis Loop ◄── CORE AGENT COMPLETE
 │     │     │     │     │     │     │     │
 │     │     │     │     │     │     │     ├──► 2.4 Budget Management
 │     │     │     │     │     │     │     │
 │     │     │     │     │     │     │     ├──► 3.1 Better Extraction ──┐
 │     │     │     │     │     │     │     ├──► 3.2 Better Synthesis ──┤
 │     │     │     │     │     │     │     ├──► 3.3 Error Handling ────┤ (parallel)
 │     │     │     │     │     │     │     └──► 3.4 Rich Output ──────┘
 │     │     │     │     │     │     │                │
 │     │     │     │     │     │     │                ├──► 4.1 Serper Provider ──┐
 │     │     │     │     │     │     │                ├──► 4.2 SearXNG Provider ─┤
 │     │     │     │     │     │     │                ├──► 4.3 Model Selection ──┤ (parallel)
 │     │     │     │     │     │     │                ├──► 4.4 Output Format ────┤
 │     │     │     │     │     │     │                ├──► 4.5 Source Quality ───┘
 │     │     │     │     │     │     │                │
 │     │     │     │     │     │     │                └──► 4.6 README & Tests ◄── V1.0 COMPLETE
```

**Key milestones**:
- **After Task 1.5**: MVP — system works end-to-end, produces a report for any query.
- **After Task 2.3**: Core agent — system plans, iterates, and fills gaps autonomously.
- **After Task 4.6**: V1.0 — production-ready with docs, tests, and multiple providers.

---

## Sprint Summary

| Task | Name | Days | Running After? | Milestone |
|------|------|------|----------------|-----------|
| 1.1 | Project Scaffold & CLI | 0.5 | ✅ CLI runs | |
| 1.2 | Tavily Search | 1 | ✅ Prints search results | |
| 1.3 | Page Fetching | 1 | ✅ Prints extracted text | |
| 1.4 | LLM + Extraction | 1.5 | ✅ Prints findings | |
| 1.5 | Synthesis & Output | 1.5 | ✅ Writes report file | **MVP** |
| 2.1 | Query Planning | 1.5 | ✅ Plans then researches | |
| 2.2 | Sequential Sub-Questions | 1 | ✅ All sub-questions covered | |
| 2.3 | Gap Analysis Loop | 2 | ✅ Iterates on gaps | **Core Agent** |
| 2.4 | Budget Management | 0.5 | ✅ Respects limits | |
| 3.1 | Better Extraction | 1.5 | ✅ Higher quality findings | |
| 3.2 | Better Synthesis | 1.5 | ✅ Better reports | |
| 3.3 | Error Handling | 1.5 | ✅ Never crashes | |
| 3.4 | Rich Output | 1 | ✅ Polished CLI | |
| 4.1 | Serper Provider | 1 | ✅ 2 search providers | |
| 4.2 | SearXNG Provider | 0.5 | ✅ 3 search providers | |
| 4.3 | Model Selection | 1 | ✅ Pro + thinking mode | |
| 4.4 | Output Formatting | 1 | ✅ Metadata + filenames | |
| 4.5 | Source Quality | 1 | ✅ Better sources | |
| 4.6 | README & Tests | 1.5 | ✅ Documented + tested | **V1.0** |
| | **Total** | **~21 days** | | |
