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
- `--model TEXT`: Default Gemini model to use (default: gemini-2.5-flash).
- `--planner-model TEXT`: Model override for the planning step.
- `--extractor-model TEXT`: Model override for the extraction step.
- `--gap-analyzer-model TEXT`: Model override for the gap analysis step.
- `--synthesizer-model TEXT`: Model override for the synthesis step.
- `--searches INTEGER`: Maximum total number of searches allowed (default: 30).
- `--depth INTEGER`: Maximum depth of research iterations per sub-question (default: 2).
- `--rpm INTEGER`: Gemini API requests per minute limit (default: 15).
- `--max-chars INTEGER`: Maximum characters to extract per page (default: 8000).
- `--concurrent INTEGER`: Maximum concurrent page fetches (default: 5).
- `--timeout INTEGER`: Timeout in seconds for page fetches (default: 10).
- `--help`: Show this message and exit.

## Advanced Model Configuration

The agent allows fine-grained control over which model handles each step of the pipeline. This is useful for using larger models (like Pro) for complex reasoning tasks while keeping extraction fast and cost-effective with smaller models (like Flash).

Example:
```bash
deep_research "Climate change impact" \
  --planner-model gemini-2.5-pro \
  --gap-analyzer-model gemini-2.5-pro \
  --synthesizer-model gemini-2.5-pro \
  --extractor-model gemini-2.5-flash
```

