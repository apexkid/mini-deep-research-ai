# Deep Research Agent — Architecture & Design Document

## 1. Overview

A CLI-based deep research agent that takes a user query, autonomously plans research, searches the web in iterative loops, extracts findings, identifies knowledge gaps, and synthesizes everything into a citation-backed Markdown report.

### Core Behavior

```
Input:  A natural language research question
Output: A 2000-5000 word Markdown report with inline citations and a source list
Time:   2-5 minutes of autonomous research (no human in the loop after initial query)
```

### Design Principles

- **Autonomous loop**: Plan → Search → Extract → Evaluate gaps → Repeat until satisfied or budget exhausted.
- **Depth over breadth**: Follow promising threads with follow-up searches rather than skimming many topics once.
- **Transparent progress**: Stream every decision to stdout so the user sees what's happening.
- **Citation-backed**: Every claim traces to a source URL.

---

## 2. Tech Stack & Dependencies

| Layer | Choice | Why |
|-------|--------|-----|
| Language | Python >= 3.11 | asyncio, type unions, Pydantic ecosystem |
| LLM | Gemini 2.5 Flash via `google-genai` SDK | Native structured JSON output, 1M context, $0.02-0.05/run |
| Web Search | Tavily (default), Serper, or SearXNG | Tavily built for AI agents; Serper as Google SERP fallback |
| Content Extraction | `trafilatura` | Best Python library for extracting article text from HTML |
| HTTP | `aiohttp` | Async concurrent fetching |
| Data Models | `pydantic` | Validation + JSON schema generation for Gemini structured output |
| CLI | `click` | Argument parsing |
| Terminal Output | `rich` | Colored progress logs |
| Config | `python-dotenv` | API key management |

### Key Gemini Features Used

- **Structured Output**: `response_mime_type="application/json"` + `response_schema` from Pydantic models. Every LLM call returns validated JSON — no regex parsing or retry-on-bad-JSON needed.
- **Long Context (1M tokens)**: Allows batching multiple pages into a single extraction call.
- **Async SDK**: `client.aio.models.generate_content()` fits naturally into the asyncio orchestrator.
- **Thinking Mode** (optional): Enable `thinking_config` for planning/gap analysis to improve reasoning quality.

---

## 3. Project Structure

```
deep-research/
├── pyproject.toml
├── .env.example
├── src/deep_research/
│   ├── __init__.py
│   ├── __main__.py          # python -m deep_research
│   ├── cli.py               # click CLI: parse args, run orchestrator
│   ├── config.py            # load .env + CLI overrides → Config
│   ├── models.py            # all Pydantic data models
│   ├── llm_client.py        # GeminiClient (LLMClient ABC)
│   ├── planner.py           # Step 1: query → ResearchPlan
│   ├── searcher.py          # Step 2a: query → SearchResults
│   ├── fetcher.py           # Step 2b: URL → extracted text
│   ├── extractor.py         # Step 2c: page text → Findings
│   ├── gap_analyzer.py      # Step 3: findings → GapAnalysis
│   ├── synthesizer.py       # Step 4: findings → final report
│   ├── orchestrator.py      # Main loop: wires all steps together
│   ├── logger.py            # rich-based progress output
│   └── utils/
│       ├── token_counter.py
│       └── markdown.py
├── output/
├── tests/
└── README.md
```

---

## 4. Data Models

All data flows between steps as Pydantic models. These also generate the `response_schema` passed to Gemini for structured output.

### ResearchPlan
```
ResearchPlan:
  original_query: str
  approach: str                         # 1-2 sentence strategy
  sub_questions: list[SubQuestion]      # 3-7 items

SubQuestion:
  id: str                               # "sq-1", "sq-2", ...
  question: str
  priority: "high" | "medium" | "low"
  search_queries: list[str]             # 1-3 search strings
  parent_id: str | None                 # set if this is a follow-up
```

### SearchResult
```
SearchResult:
  url: str
  title: str
  snippet: str
  source: str                           # domain name
```

### PageContent
```
PageContent:
  url: str
  title: str
  text: str                             # cleaned article text
  token_count: int                      # approximate
```

### Finding
```
Finding:
  id: str                               # "f-1", "f-2", ...
  claim: str                            # factual statement
  evidence: str                         # supporting detail from the page
  source_url: str
  source_title: str
  sub_question_id: str
  confidence: "high" | "medium" | "low"
```

### GapAnalysis
```
GapAnalysis:
  answered_aspects: list[str]
  remaining_gaps: list[str]
  follow_up_queries: list[str]          # new searches to fill gaps
  should_continue: bool                 # false = move to next sub-question
```

### ResearchReport
```
ResearchReport:
  title: str
  query: str
  summary: str                          # 2-3 sentence executive summary
  sections: list[{heading, content}]    # markdown with [1], [2] citations
  sources: list[{id, url, title}]       # numbered source list
  metadata: {total_searches, total_pages, total_findings, duration_s, model}
```

---

## 5. Agent Pipeline — Step by Step

### Step 1: PLAN — Query Decomposition

**Goal**: Break the user's query into 3-7 researachable sub-questions, each with concrete search queries.

**Input**: Raw user query string.

**Output**: `ResearchPlan`

**Prompt**:
```
SYSTEM:
You are a research planning agent. Your job is to take a user's research
question and decompose it into a structured research plan.

Rules:
- Generate 3-7 sub-questions that together fully answer the original query.
- Order sub-questions so foundational/definitional questions come first,
  analysis/comparison questions come later.
- For each sub-question, write 1-3 specific web search queries that would
  find relevant information. Search queries should be short (3-8 words),
  specific, and varied (don't repeat the same phrasing).
- Assign priority: "high" for core questions, "medium" for supporting
  context, "low" for nice-to-have depth.
- Write a 1-2 sentence "approach" describing your overall research strategy.

USER:
Research question: {user_query}
```

**LLM Config**: Structured output with `ResearchPlan` schema. Temperature 0.7.

**Example I/O**:
```
Input:  "What are the economics of vertical farming in 2025?"

Output:
  approach: "Start with market size and growth, then examine cost structure
             and unit economics, compare with traditional farming, and
             assess investor sentiment and profitability outlook."
  sub_questions:
    - id: sq-1, priority: high
      question: "What is the current market size of vertical farming?"
      search_queries: ["vertical farming market size 2025", "indoor farming industry revenue"]

    - id: sq-2, priority: high
      question: "What are the major cost components of vertical farming?"
      search_queries: ["vertical farming cost breakdown", "indoor farming energy costs per kg"]

    - id: sq-3, priority: high
      question: "How does vertical farming unit economics compare to traditional agriculture?"
      search_queries: ["vertical farming vs traditional farming cost", "vertical farm profitability"]

    - id: sq-4, priority: medium
      question: "Which crops are economically viable for vertical farming?"
      search_queries: ["most profitable vertical farming crops", "vertical farm crop yield economics"]

    - id: sq-5, priority: medium
      question: "What is the current state of venture capital investment?"
      search_queries: ["vertical farming funding 2024 2025", "indoor agriculture investment trends"]

    - id: sq-6, priority: low
      question: "What technological advances are reducing costs?"
      search_queries: ["vertical farming technology cost reduction", "LED efficiency indoor farming"]
```

---

### Step 2: RESEARCH LOOP — Search, Fetch, Extract (per sub-question)

This is the core iterative loop. For each sub-question, we cycle through search → fetch → extract → gap analysis, going deeper until the sub-question is sufficiently answered or budget is exhausted.

#### Step 2a: SEARCH — Web Search

**Goal**: Execute search queries and collect ranked results.

**Input**: 1-3 search query strings from the current sub-question (or from gap analysis follow-ups).

**Output**: `list[SearchResult]` — top 5-10 results per query, deduplicated.

**Behavior**:
- Call the search API (Tavily/Serper/SearXNG) for each query.
- Deduplicate by URL across queries.
- Filter out low-quality domains (configurable blocklist: pinterest, quora, reddit, etc.).
- Skip URLs already visited in previous iterations.

No LLM call — this is pure API + filtering logic.

#### Step 2b: FETCH — Page Content Extraction

**Goal**: Download web pages and extract readable article text.

**Input**: URLs from search results (filtered to new/unvisited only).

**Output**: `list[PageContent]` — cleaned text for each successfully fetched page.

**Behavior**:
- Fetch pages concurrently (asyncio semaphore, max 5 parallel).
- Use `trafilatura` to strip navigation, ads, boilerplate — extract only the main article content.
- Truncate each page to ~4000 tokens (to fit within LLM context for extraction).
- Gracefully handle failures (timeouts, 403s, paywalls) — return None, log, skip.

No LLM call — this is HTTP fetching + content extraction.

#### Step 2c: EXTRACT — Finding Extraction

**Goal**: Use the LLM to pull structured findings from each page, relative to the current sub-question.

**Input**: A page's extracted text + the sub-question being researched.

**Output**: `list[Finding]` — 0-5 findings per page.

**Prompt**:
```
SYSTEM:
You are a research extraction agent. Given the text content of a web page
and a specific research question, extract key findings.

Rules:
- Extract 0-5 findings. Each finding must be a specific, factual claim.
- Include supporting evidence (a key data point, statistic, or detail).
- Assign confidence: "high" if the source is authoritative and the data is
  specific, "medium" if plausible but from a secondary source, "low" if
  vague or potentially outdated.
- If the page is irrelevant to the research question, return an empty list.
- Do NOT invent or extrapolate. Only extract what is explicitly stated.

USER:
Research question: {sub_question.question}

Page title: {page.title}
Page URL: {page.url}
Page content:
---
{page.text}
---

Extract findings relevant to the research question.
```

**LLM Config**: Structured output with `list[Finding]` schema. Temperature 0.3 (factual extraction, low creativity).

**Example I/O**:
```
Input:
  sub_question: "What is the current market size of vertical farming?"
  page: AgFunder article about vertical farming market

Output:
  - claim: "The global vertical farming market was valued at $5.8B in 2024"
    evidence: "According to Grand View Research, the market reached $5.8 billion
               in 2024 with a projected CAGR of 24.3% through 2030"
    confidence: high

  - claim: "North America accounts for ~35% of global vertical farming revenue"
    evidence: "The report cites North America as the largest regional market
               driven by high labor costs and consumer demand for local produce"
    confidence: medium
```

---

### Step 3: GAP ANALYSIS — Evaluate and Decide

**Goal**: After each search-fetch-extract cycle, evaluate what we've learned vs. what's still missing. Decide whether to search more or move on.

**Input**: The sub-question + all findings collected so far for that sub-question.

**Output**: `GapAnalysis`

**Prompt**:
```
SYSTEM:
You are a research evaluation agent. Given a research question and the
findings collected so far, determine if the question has been adequately
answered or if more research is needed.

Rules:
- List what aspects of the question have been answered.
- List what important aspects remain unanswered (gaps).
- If gaps exist AND are likely findable via web search, set should_continue
  to true and generate 1-3 new, DIFFERENT search queries targeting the gaps.
  Do not repeat previous search queries.
- If the question is sufficiently answered, OR the remaining gaps are too
  niche to find via web search, set should_continue to false.
- Be pragmatic: don't chase perfection. 3-4 solid findings with good
  evidence is enough for most sub-questions.

USER:
Research question: {sub_question.question}

Previous search queries used: {list of all queries used so far for this sub-question}

Findings collected ({n} total):
{for each finding: "- [{confidence}] {claim} (source: {source_url})"}

Evaluate the completeness of research on this question.
```

**LLM Config**: Structured output with `GapAnalysis` schema. Temperature 0.5.

**Example I/O**:
```
Input:
  sub_question: "What are the major cost components of vertical farming?"
  findings: [
    "Energy costs account for 25-30% of operating expenses",
    "Labor represents 20-25% of costs in most facilities"
  ]

Output:
  answered_aspects: ["energy costs", "labor costs"]
  remaining_gaps: ["capital expenditure / startup costs", "cost of growing media and nutrients"]
  follow_up_queries: ["vertical farming startup capital cost", "hydroponic nutrient supply cost"]
  should_continue: true
```

---

### Step 4: SYNTHESIZE — Report Generation

**Goal**: Combine all findings across all sub-questions into a coherent, well-structured Markdown report.

**Input**: Original query + ResearchPlan + all collected findings.

**Output**: `ResearchReport` (Markdown string with citations)

**Prompt**:
```
SYSTEM:
You are a research report writer. Given a research query, a research plan,
and a collection of findings with sources, write a comprehensive report.

Rules:
- Write in Markdown with ## section headings.
- Start with a 2-3 sentence executive summary.
- Structure sections THEMATICALLY, not by sub-question. Combine related
  findings from different sub-questions into coherent sections.
- Cite sources inline using [1], [2], etc. Every factual claim must have
  a citation.
- Include a ## Sources section at the end with numbered URLs.
- Be specific and data-driven. Use actual numbers, dates, and names from
  the findings.
- Target 2000-5000 words depending on topic complexity.
- If certain aspects could not be fully researched, note this briefly
  rather than speculating.
- Write in a professional, analytical tone. Avoid marketing language.

USER:
Original research question: {query}

Research approach: {plan.approach}

Collected findings ({n} total from {m} sources):
{for each finding:
  "[F{id}] {claim}
   Evidence: {evidence}
   Source: {source_title} ({source_url})
   Confidence: {confidence}
   Related to: {sub_question.question}
  "
}

Write a comprehensive research report.
```

**LLM Config**: Free-form text output (NOT structured JSON — this is the one step where we want natural prose). Temperature 0.7. Max output tokens 8192+.

**Post-processing**:
- Parse the Markdown to extract citation numbers [1], [2], etc.
- Build the sources list by mapping citation numbers to finding source URLs.
- Validate all citation numbers reference real sources; remove orphaned citations.
- Count words for the progress log.

---

## 6. Orchestrator Pseudo Code

This is the main loop that wires all steps together.

```
function run_research(query, config):
    start_timer()

    # ── STEP 1: PLAN ──
    plan = llm_call_structured(PLANNING_PROMPT, query, schema=ResearchPlan)
    log("[PLAN] Decomposed into {n} sub-questions")

    findings = []
    search_count = 0
    visited_urls = set()

    # ── STEP 2-3: RESEARCH LOOP ──
    for sub_question in plan.sub_questions (sorted by priority):
        depth = 0
        current_queries = sub_question.search_queries

        while depth < MAX_SEARCH_DEPTH and search_count < MAX_TOTAL_SEARCHES:

            # 2a: SEARCH
            results = []
            for query in current_queries:
                results += web_search(query)
                search_count += 1
                log("[SEARCH] {sq_id}: '{query}' → {n} results")

            # 2b: FETCH (parallel, skip visited)
            new_urls = [r.url for r in results if r.url not in visited_urls]
            pages = parallel_fetch_and_extract(new_urls, concurrency=5)
            visited_urls.add_all(new_urls)
            log("[FETCH] Fetched {n} pages")

            # 2c: EXTRACT
            for page in pages:
                new_findings = llm_call_structured(
                    EXTRACTION_PROMPT, page, sub_question,
                    schema=list[Finding]
                )
                findings += new_findings
                log("[EXTRACT] Found {n} findings from {page.source}")

            # 3: GAP ANALYSIS
            gap = llm_call_structured(
                GAP_ANALYSIS_PROMPT, sub_question, findings,
                schema=GapAnalysis
            )

            if not gap.should_continue:
                log("[GAP] {sq_id}: complete")
                break

            log("[GAP] {sq_id}: {n} gaps, generating follow-ups")
            current_queries = gap.follow_up_queries
            depth += 1

        # Budget check
        if search_count >= MAX_TOTAL_SEARCHES:
            log("[BUDGET] Search budget exhausted, synthesizing with current findings")
            break

    # ── STEP 4: SYNTHESIZE ──
    log("[SYNTH] Generating report from {n} findings across {m} sources...")
    report = llm_call_freeform(SYNTHESIS_PROMPT, query, plan, findings, max_tokens=8192)
    report = post_process_citations(report, findings)

    # ── OUTPUT ──
    write_to_file(report, config.output_dir)
    log("[DONE] Report saved to {path} ({word_count} words)")

    return report
```

### Budget & Termination Rules

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `MAX_SEARCH_DEPTH` | 3 | Max search→extract→gap iterations per sub-question |
| `MAX_TOTAL_SEARCHES` | 30 | Hard cap on total search API calls across all sub-questions |

The agent terminates the research loop when ANY of these conditions is met:
1. All sub-questions have been researched and gap analysis returns `should_continue: false`.
2. `MAX_TOTAL_SEARCHES` is reached (budget exhausted).
3. `MAX_SEARCH_DEPTH` is reached for the current sub-question (move to next).

In all cases, the agent proceeds to synthesis with whatever findings have been collected.

---

## 7. LLM Call Summary

| Step | Prompt | Input | Output | JSON Mode | Temperature | Tokens (est.) |
|------|--------|-------|--------|-----------|-------------|---------------|
| Plan | Planning prompt | User query (~50 tokens) | ResearchPlan | Yes (structured) | 0.7 | ~1,000 out |
| Extract | Extraction prompt | Page text (~4,000 tokens) + sub-question | list[Finding] | Yes (structured) | 0.3 | ~500 out |
| Gap Analysis | Gap analysis prompt | Sub-question + findings (~2,000 tokens) | GapAnalysis | Yes (structured) | 0.5 | ~300 out |
| Synthesize | Synthesis prompt | All findings (~8,000 tokens) | Markdown report | No (free text) | 0.7 | ~8,000 out |

**Total per run**: ~20-30 LLM calls, ~80K input tokens, ~15K output tokens.

**Cost**: ~$0.02-0.05 with Gemini 2.5 Flash, ~$0.15-0.30 with Gemini 2.5 Pro.

---

## 8. Error Handling Philosophy

The agent is designed to be **resilient and graceful** — never crash, always produce a report even if partial.

| Failure | Response |
|---------|----------|
| Search API down | Retry once with backoff. If still failing, skip that query, continue with others. |
| URL fetch fails (timeout, 403, paywall) | Skip that URL, log warning, continue with other pages. |
| LLM returns invalid JSON | Retry once. If still invalid, skip that extraction step. |
| Gemini rate limit (429) | Exponential backoff with jitter, max 3 retries. |
| Gemini safety filter blocks response | Log warning, skip that page's extraction. |
| Zero findings for a sub-question | Note the gap; the synthesis prompt handles this by acknowledging incomplete coverage. |
| Budget exhausted mid-research | Stop loop, synthesize with what we have, note incompleteness in report. |

---

## 9. CLI Interface

```bash
# Basic usage
deep-research "What are the economics of vertical farming in 2025?"

# With options
deep-research "query" --model gemini-2.5-pro --depth 5 --searches 50

# As Python module
python -m deep_research "query" --verbose
```

| Flag | Default | Description |
|------|---------|-------------|
| `<query>` | required | The research question |
| `--model` | `gemini-2.5-flash` | Gemini model |
| `--depth` | 3 | Max search rounds per sub-question |
| `--searches` | 30 | Total search API call budget |
| `--provider` | `tavily` | Search provider: tavily, serper, searxng |
| `--output` | `./output` | Output directory |
| `--verbose` | false | Show detailed logs including LLM reasoning |

### Progress Output

```
[PLAN]     Decomposed into 5 sub-questions
[SEARCH]   sq-1: "vertical farming market size 2025" → 8 results
[FETCH]    Fetching 5 pages...
[EXTRACT]  Found 3 findings from agfundernews.com
[GAP]      sq-1: 2 gaps remaining, generating follow-up queries
[SEARCH]   sq-1: "vertical farming energy costs per kg" → 6 results
[FETCH]    Fetching 4 new pages...
[EXTRACT]  Found 2 findings from sciencedirect.com
[GAP]      sq-1: complete
[SEARCH]   sq-2: "vertical farming vs traditional farming yield" → 7 results
...
[SYNTH]    Generating report from 18 findings across 12 sources...
[DONE]     Report saved to output/vertical-farming-economics-2025.md (3,847 words)
```

---

## 10. Environment & Configuration

### `.env.example`

```bash
# Required
GEMINI_API_KEY=AIza...

# Search provider (pick one)
TAVILY_API_KEY=tvly-...
# SERPER_API_KEY=...
# SEARXNG_URL=http://localhost:8080

# Optional overrides
GEMINI_MODEL=gemini-2.5-flash
SEARCH_PROVIDER=tavily
MAX_SEARCH_DEPTH=3
MAX_TOTAL_SEARCHES=30
```

---

## 11. Implementation Phases

### Phase 1: Skeleton (Day 1)
- `pyproject.toml`, `models.py`, `config.py`, `logger.py`, `cli.py`
- Verify: `python -m deep_research "test"` runs and parses args

### Phase 2: Search & Fetch (Day 1-2)
- `searcher.py` (Tavily first), `fetcher.py` (aiohttp + trafilatura)
- Verify: given a query, prints search results and extracted page text

### Phase 3: LLM + Planning + Extraction (Day 2-3)
- `llm_client.py` (GeminiClient), `planner.py`, `extractor.py`
- Verify: query → plan → search → extract → findings printed

### Phase 4: Research Loop (Day 3)
- `gap_analyzer.py`, `orchestrator.py`
- Verify: full loop runs, iterates on gaps, respects budget

### Phase 5: Report Generation (Day 3-4)
- `synthesizer.py`, citation post-processing
- Verify: end-to-end run produces a readable Markdown report with citations

### Phase 6: Polish (Day 4)
- Add Serper/SearXNG providers, retry logic, token budget warnings, README

---

## 12. Future Enhancements (Not in MVP)

- **Gemini Grounding**: Use Gemini's built-in `google_search` tool to eliminate the need for a separate search API key.
- **Parallel sub-questions**: Research multiple sub-questions concurrently via `asyncio.TaskGroup`.
- **Streaming report**: Use Gemini's streaming API to display the report as it's written.
- **PDF output**: Convert Markdown to PDF via `weasyprint` or pandoc.
- **Source caching**: Cache fetched pages to disk/sqlite to avoid re-fetching across runs.
- **Custom personas**: `--system "You are a biotech analyst..."` to inject domain expertise.
- **Resume from checkpoint**: Save findings to JSON after each sub-question, resume on failure.
- **MCP server**: Expose as an MCP tool so Claude Desktop or other agents can invoke deep research.
