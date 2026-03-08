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

### 2. Configuration

Create a `.env` file in the root directory and add your API keys:

```bash
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
```

You can use `.env.example` as a template.

### 3. Run Research

You can run the agent using the `deep_research` command or via `python -m deep_research`.

```bash
deep_research "What are the economics of vertical farming in 2025?"
```

## Features (In Development)

- [x] CLI Shell & Project Scaffold
- [x] Tavily Search Integration
- [x] Page Fetching & Content Extraction
- [x] Gemini Finding Extraction
- [x] Report Synthesis & Markdown Output
- [x] Query Planning & Sequential Research
- [x] Gap Analysis & Iterative Loops
- [x] Budget Management & CLI Flags
- [x] Improved Extraction & Deduplication

## CLI Reference

### `deep_research QUERY`

Arguments:
- `QUERY`: The research question or topic you want to investigate.

*(More flags and settings will be documented here as they are implemented.)*
