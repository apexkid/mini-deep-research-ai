# SimpleDeepResearch

A deep research agent that takes a query, plans its research, searches the web, extracts findings, and synthesizes a comprehensive Markdown report with citations.

## Quick Start

### 1. Setup Environment

This project uses a Python virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
pip install -e .
```

## Configuration

Create a `.env` file in the root directory and add your API keys:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key

# Optional: Langfuse Observability
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Optional: Model Overrides (defaults to gemini-2.5-flash)
GEMINI_MODEL=gemini-2.5-flash
PLANNER_MODEL=gemini-2.5-pro
EXTRACTOR_MODEL=gemini-2.5-flash
GAP_ANALYZER_MODEL=gemini-2.5-pro
SYNTHESIZER_MODEL=gemini-2.5-pro
```

You can use `.env.example` as a template.

## Run Research

You can run the agent using the `deep_research` command or via `python -m deep_research`.

```bash
deep_research "What are the economics of vertical farming in 2025?" --searches 10 --depth 2
```

## Features

- [x] **Intelligent Planning**: Decomposes complex queries into logical sub-questions.
- [x] **Autonomous Search**: Uses Tavily API to find high-quality web sources.
- [x] **Factual Extraction**: Specifically targets data, numbers, and evidence using Gemini.
- [x] **Iterative Research**: Gap analysis loops identify missing info and run follow-up searches.
- [x] **Budget Management**: Set strict limits on total searches and research depth.
- [x] **Observability**: Full trace grouping and LLM input/output tracking via Langfuse.
- [x] **Deduplication**: Filters out redundant findings across multiple sources.
- [x] **Professional Output**: Synthesizes a structured Markdown report with numbered citations.

## CLI Reference

### `deep_research QUERY [OPTIONS]`

**Arguments:**
- `QUERY`: The research question or topic you want to investigate.

**Options:**
- `--searches INTEGER`: Maximum total number of searches allowed (default: 30).
- `--depth INTEGER`: Maximum depth of research iterations per sub-question (default: 2).
- `--help`: Show this message and exit.

## Advanced Configuration

The agent allows fine-grained control over which model handles each step of the pipeline. This is useful for using larger models (like Pro) for complex reasoning tasks while keeping extraction fast and cost-effective with smaller models (like Flash).

| Environment Variable | Purpose | Default |
|---------------------|---------|---------|
| `PLANNER_MODEL` | Decomposing the query into a research plan. | `GEMINI_MODEL` |
| `GAP_ANALYZER_MODEL`| Analyzing findings to identify knowledge gaps. | `GEMINI_MODEL` |
| `SYNTHESIZER_MODEL` | Writing the final comprehensive report. | `GEMINI_MODEL` |
| `EXTRACTOR_MODEL` | Extracting specific findings from page text. | `GEMINI_MODEL` |
| `GEMINI_MODEL` | Fallback model for all steps. | `gemini-2.5-flash` |

