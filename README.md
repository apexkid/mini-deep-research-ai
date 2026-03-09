<div align="center">

# 🧠 MiniDeepResearch

**An autonomous AI research agent that doesn't just search—it *understands*.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Powered by Gemini](https://img.shields.io/badge/Powered%20by-Gemini-orange?style=flat&logo=google)](https://deepmind.google/technologies/gemini/)

[Features](#-key-features) • [How it Works](#-how-it-works) • [Installation](#-quick-start) • [Usage](#-usage) • [Observability](#-observability-with-langfuse)

</div>

---

**MiniDeepResearch** is a powerful CLI tool that takes a complex query, autonomously builds a research plan, scours the web, extracts factual evidence, identifies gaps in its own knowledge, and ultimately synthesizes a comprehensive, publication-ready Markdown report complete with citations. 

Stop settling for shallow AI summaries. Get deep, verifiable research on autopilot.

## ✨ Key Features

- **🧠 Intelligent Planning:** Breaks down broad, complex queries into a MECE (Mutually Exclusive, Collectively Exhaustive) tree of focused sub-questions.
- **🌐 Autonomous Search:** Leverages the Tavily API to find high-quality, relevant web sources.
- **🎯 Factual Extraction:** Uses Gemini to surgically extract specific data, numbers, and evidence. No fluff, just facts.
- **🔄 Iterative Gap Analysis:** It knows what it *doesn't* know. The agent automatically analyzes extracted findings to identify missing pieces and launches follow-up searches to fill those gaps.
- **💰 Budget Management:** Granular control over your API spend with strict limits on total searches and research iteration depth.
- **📊 Deduplication:** Intelligently filters out redundant findings across multiple sources to keep your report concise.
- **👁️ Full Observability:** Native integration with Langfuse. Track every LLM call, prompt, output, and token cost in a beautiful dashboard.
- **✍️ Professional Synthesis:** Generates a structured, easy-to-read Markdown report with numbered citations linking back to the original sources.

## ⚙️ How It Works

1. **Plan:** You provide a prompt. The agent decomposes it into a prioritized list of sub-questions.
2. **Search & Fetch:** It executes targeted searches for the highest priority questions and fetches the raw HTML content.
3. **Extract:** It reads the content and extracts highly specific, factual claims with supporting evidence.
4. **Analyze & Loop:** It reviews its findings against the original sub-question. If there are gaps, it generates *new* search queries and loops back to step 2.
5. **Synthesize:** Once all questions are answered (or the budget is exhausted), it compiles everything into a cohesive, cited Markdown report.

---

## 🚀 Quick Start

### 1. Setup Environment

This project uses a standard Python virtual environment.

```bash
# Clone the repository
git clone https://github.com/apexkid/mini-deep-research-ai.git
cd mini-deep-research-ai

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`

# Install dependencies
pip install -e .
```

### 2. Configuration

Create a `.env` file in the root directory. You will need API keys for Google Gemini and Tavily.

```env
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Optional: Langfuse Observability (Highly Recommended)
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

## 💻 Usage

Run the agent from your terminal using the `deep_research` command.

### Basic Run
```bash
deep_research "What are the projected economics of vertical farming in 2030?"
```

### Advanced Run (Control your budget!)
You can easily control how deep the rabbit hole goes using CLI flags:
```bash
deep_research "Future of Solid State Batteries" --searches 15 --depth 3
```

### Model Overrides (Pro Mode)
Want to use a heavy reasoning model for planning and synthesis, but a fast/cheap model for raw data extraction? You can override the models per-step:

```bash
deep_research "Impact of AI on global supply chains" \
  --planner-model gemini-2.5-pro \
  --gap-analyzer-model gemini-2.5-pro \
  --synthesizer-model gemini-2.5-pro \
  --extractor-model gemini-2.5-flash \
  --searches 20
```

### Full CLI Reference
```
Usage: deep_research [OPTIONS] QUERY

Options:
  --model TEXT             Default Gemini model to use (default: gemini-2.5-flash).
  --planner-model TEXT     Model override for the planning step.
  --extractor-model TEXT   Model override for the extraction step.
  --gap-analyzer-model TEXT Model override for the gap analysis step.
  --synthesizer-model TEXT Model override for the synthesis step.
  --searches INTEGER       Maximum total number of searches allowed (default: 30).
  --depth INTEGER          Maximum depth of research iterations per sub-question (default: 2).
  --rpm INTEGER            Gemini API requests per minute limit (default: 15).
  --max-chars INTEGER      Maximum characters to extract per page (default: 8000).
  --concurrent INTEGER     Maximum concurrent page fetches (default: 5).
  --timeout INTEGER        Timeout in seconds for page fetches (default: 10).
  --help                   Show this message and exit.
```

## 👁️ Observability with Langfuse

Understanding exactly what your AI agent is doing under the hood is critical. MiniDeepResearch comes pre-instrumented with [Langfuse](https://langfuse.com/). 

By adding your Langfuse keys to `.env`, every research run is automatically grouped into a single Trace. You can easily inspect:
- The exact prompts sent to the Planner, Extractor, and Synthesizer.
- The raw output from the LLM at every step.
- Total token usage and execution latency.
- Where the gap analyzer decided more research was needed.

## 🤝 Contributing

Contributions are welcome! Whether it's adding support for new search providers (like Serper or SearXNG), improving the extraction prompts, or fixing bugs, please feel free to open a PR or an Issue.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
