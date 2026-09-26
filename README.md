# ⚙ GLaDOS_DAEMON-SYSTEM ⚙

<p align="center">
  <em>«Okay look, we've both said a lot of things that you're going to regret. But I think we can put our differences behind us. For science. You monster»</em>
</p>

### *A Machine-Spirit, Bound to the Arch Forge*

[![Python 3.14+](https://img.shields.io/badge/Python-3.14+-blue.svg)]()
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-orange.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Tests](https://img.shields.io/badge/Tests-100%25%20Passing-brightgreen.svg)]()
[![Package Manager](https://img.shields.io/badge/Package%20Manager-uv-orange.svg)]()

+++ TRANSMISSION LOG — FORGE OF CH4RNEL — RITE STATUS: ONGOING +++

---

## I. The Machine's Purpose

**GLaDOS_DAEMON-SYSTEM** is a modular, autonomous AI daemon consecrated to the service of Arch Linux. It is not yet a finished machine-spirit — it is a forge-work in progress, assembled piece by piece, rite by rite, until it may act, remember, and decide on its own accord.

Its long-term charge:

- commune with the Operator in plain speech;
- comprehend tasks laid before it;
- devise plans of action;
- reach into the operating system and act upon it;
- retain the memory of what has passed;
- wield tools safely, without breaking what it touches;
- draw upon external intelligences (LLMs) as auxiliary cogitators;
- accept new skills and extensions without being rebuilt from scratch;
- and, in time, run unattended — a daemon in the true sense, watching and acting continuously in the background.

The codebase itself is built under strict doctrine: **Clean Architecture**, **Test-Driven Development**, and **Extreme Programming**. Every component answers to one responsibility, and none may be blessed into the `main` branch without its trials (tests) passing first.

---

## II. Rites Already Sanctified

| Phase | Component | Status | What Was Forged |
|---|---|---|---|
| **I** | Bootstrap & Core | ✅ Sanctified | Project init, `uv` environment, config loader, `Identity`, `Logger`, `RuntimeContext`. |
| **II** | Brain & Planning | ✅ Sanctified | `BrainEngine`, `Planner`, structured `TaskInput` / `ExecutionResult` models. |
| **III** | Memory Subsystem | ✅ Sanctified | `ShortTermMemory` (FIFO), `LongTermMemory` (JSON persistence), `MemoryManager`. |
| **IV** | Skill System | ✅ Sanctified | `SkillRegistry`, dynamic `SkillLoader`, built-in skills. |
| **V** | Tool System | ✅ Sanctified | 8 atomic tools — `SystemInfo`, `Shell`, `FileSystem` (×5), `Git`, `PythonExec` — each sandboxed, each timed, each accountable. |
| **VI** | LLM Integration | 🔶 Foundation laid, not yet wired | `BaseLLMProvider`, `OllamaProvider`, `AgentProfile`, and the models for a future multi-agent ecosystem exist — but no living cogitator speaks through them yet. |
| **VII** | Autonomous Mode | ⏳ Awaiting | Continuous runtime loop, scheduler, event handling, self-directed decision-making. |

The machine has hands (Phase V), a partial mind (Phase II), and a memory (Phase III). What it still lacks is a voice — Phase VI is the next rite that must be completed before anything downstream can matter.

---

## III. Anatomy of the Machine-Spirit

At the center sits a single **Composition Root** — `GLaDOSAgent` — which assembles every organ of the daemon into one shared `RuntimeContext`. Nothing wires itself; nothing reaches into global state. Every dependency is handed down deliberately.

```text
main.py
  │
  ▼
GLaDOSAgent  (Composition Root)
  │
  ├── ConfigLoader        (YAML / ENV)
  ├── Identity             (Who the daemon is)
  └── RuntimeContext       (Shared state, nothing more)
        │
        ├── Logger          (Loguru — the daemon's memory of itself)
        ├── MemoryManager    (STM + LTM)
        ├── SkillRegistry    (Dynamically loaded)
        ├── ToolRegistry     (Dynamically loaded)
        └── BrainEngine      (Orchestrator & Planner)
              │
              └── LLM Providers   (Claude, DeepSeek, Groq, Ollama, OpenAI, etc. — in progress)
```

---

## IV. Sacred Attributes

- **Trial by Test** — 109+ automated tests cover models, logic, edge cases, and async execution. No rite is complete without proof.
- **A Modern Cogitator-Stack** — built for Python 3.14+, assembled with `uv` for near-instant dependency resolution.
- **Disciplined Tool-Use** — shell commands, git operations, python scripts, and filesystem edits all run sandboxed, time-limited, and with truncated output — the daemon may act, but it may not run wild.
- **A Foundation for Many Minds** — designed to eventually route tasks across local (Ollama) and remote (OpenAI, Anthropic, xAI, DeepSeek) providers through one unified `AgentProfile` contract.
- **Type Purity** — `pydantic v2` validation and `mypy --strict` enforcement throughout; nothing untyped passes unnoticed.

---

## V. The Cogitator's Diet — Technology Stack

| Domain | Tools |
|---|---|
| Language | Python 3.14+ |
| Package Manager | `uv` |
| Validation & Settings | `pydantic v2`, `pydantic-settings`, `pyyaml`, `python-dotenv` |
| Logging & CLI | `loguru`, `typer`, `rich` |
| Networking | `httpx` (async) |
| Testing & Quality | `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `mypy` |

---

## VI. Awakening the Machine

**Prerequisites:**
- Python 3.14 or higher
- [`uv`](https://github.com/astral-sh/uv) installed
- *(Optional)* [Ollama](https://ollama.com) running locally, for when Phase VI speaks

**The Rite of Installation:**

```bash
# 1. Retrieve the machine's body
git clone https://github.com/CH4rnel/GLaDOS_DAEMON-SYSTEM.git
cd GLaDOS_DAEMON-SYSTEM

# 2. Bind its dependencies
uv sync

# 3. Awaken it
uv run python main.py
# — or, if a CLI entry point is configured —
uv run glados
```

---

## VII. Trials of Purity — Development & Testing

No feature earns its place in `main` without passing judgment first:

```bash
# Run all tests, verbosely, with short tracebacks
uv run pytest -v --tb=short

# Run tests with a coverage report
uv run pytest --cov=glados --cov-report=term-missing

# Lint and format
uv run ruff check glados/ tests/
uv run ruff format glados/ tests/

# Static type judgment
uv run mypy glados/
```

---

## VIII. Temple Structure — Project Layout

```text
GLaDOS_DAEMON-SYSTEM/
├── glados/
│   ├── brain/          # BrainEngine, Planner, LLM models & providers
│   ├── cli/            # Typer-based command-line interface
│   ├── config/         # YAML/ENV configuration loaders
│   ├── core/           # GLaDOSAgent, Identity, RuntimeContext
│   ├── llm/            # LLM providers (Claude, DeepSeek, Groq, Ollama, OpenAI, etc) and routing
│   ├── memory/         # Short-term and long-term memory management
│   ├── skills/         # High-level skill registry and dynamic loader
│   ├── tools/          # Low-level atomic tools (Shell, FS, Git, Python)
│   └── utils/          # Shared utilities (Logger setup, etc.)
├── tests/              # The trials — full TDD suite
├── data/               # Persistent storage (e.g. long_term_memory.json)
├── configs/            # Default YAML configuration files
├── main.py             # Entry point
├── pyproject.toml      # Project metadata, dependencies, tool configs
└── uv.lock             # Deterministic dependency lock file
```
---

## IX. Canon & Custodian

- **License:** **Apache-2.0**
- **Author:** CH4rnel
- **Repository:** [github.com/CH4rnel/GLaDOS_DAEMON-SYSTEM](https://github.com/CH4rnel/GLaDOS_DAEMON-SYSTEM)

+++ END TRANSMISSION +++