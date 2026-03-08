# SimpleDeepResearch - Deep Research Agent

This project aims to build a deep research agent that takes a query, plans its research, searches the web, extracts findings, and synthesizes a comprehensive Markdown report with citations.

## Planning Philosophy

1.  **MVP first**: The earliest possible end-to-end working pipeline, even if naive. A bad report from a working system beats a perfect architecture that doesn't run.
2.  **Always shippable**: After every task, `python -m deep_research "any query"` runs without errors and produces output. No task leaves the system broken.
3.  **Each task adds visible value**: Every task either makes the agent produce better results, handle more edge cases, or become easier to use. No pure refactors without user-facing improvement.

## Technical Stack

-   **Language**: Python 3.10+
-   **CLI**: `click`
-   **Logging**: `rich`
-   **Models**: `pydantic`
-   **LLM SDK**: `google-genai` (Gemini)
-   **Search APIs**: Tavily, Serper, SearXNG
-   **Fetching**: `aiohttp`
-   **Content Extraction**: `trafilatura`
-   **Testing**: `pytest`

## Core Mandates

-   **Adhere to the Venv Environment**: This project is a `.venv` environment and all dependencies should be installed only for the local environment.
-   **Adhere to the Implementation Plan**: Refer the sprints and tasks defined in `docs/implementation_plan_v1.md`.
-   **Reference to the Design Doc**: Refer the sprints and tasks defined in `docs/design_v1.md`.
-   **Maintain CLI Interface**: Ensure `python -m deep_research "query"` always works and provides clear feedback via `rich`.
-   **Testing**:
    -   All new logic must be accompanied by unit tests.
    -   Use `pytest` with mocks for external APIs.
    -   End-to-end tests should be gated behind a `--run-e2e` flag and require real API keys.
-   **Environment Variables**:
    -   `GEMINI_API_KEY`: Required for LLM calls.
    -   `TAVILY_API_KEY`: Required for Tavily search.
    -   `SERPER_API_KEY`: Required for Serper search.
    -   `SEARXNG_URL`: Required for SearXNG search.
-   **Output**:
    -   Reports should be generated in Markdown format.
    -   Include a `Sources` section with numbered citations matching inline `[n]` references.
    -   Use YAML frontmatter for metadata in reports.

