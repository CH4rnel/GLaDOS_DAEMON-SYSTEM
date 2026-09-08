# ♃ ☿ 𓂀 GLaDOS_DAEMON-SYSTEM 𓂀 ☿ ♃

![Python 3.14+](https://img.shields.io/badge/Python-3.14+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Tests](https://img.shields.io/badge/Tests-109%20Passing-brightgreen.svg)
![Package Manager](https://img.shields.io/badge/Package%20Manager-uv-orange.svg)

> *"For science. You monster."*

**GLaDOS_DAEMON-SYSTEM** is a modular, autonomous AI daemon designed for Arch Linux. Its long-term goal is to become a reliable local AI assistant capable of system management, knowledge processing, intelligent workflow orchestration, and continuous background operation.

The project strictly follows **Clean Architecture**, **Test-Driven Development (TDD)**, and **Extreme Programming (XP)** principles, ensuring a robust, extensible, and loosely coupled codebase.

---

## Current Development Status

| Phase | Component | Status | Description |
| :--- | :--- | :---: | :--- |
| **Phase 1** | Bootstrap & Core | (check!) | Project init, `uv` env, Config, Identity, Logger, `RuntimeContext`. |
| **Phase 2** | Brain & Planning | (check!) | `BrainEngine`, `Planner`, structured `TaskInput`/`ExecutionResult`. |
| **Phase 3** | Memory Subsystem | (checK!) | `ShortTermMemory` (FIFO), `LongTermMemory` (JSON persistence), `MemoryManager`. |
| **Phase 4** | Skill System | (check!) | `SkillRegistry`, dynamic `SkillLoader`, built-in skills. |
| **Phase 5** | Tool System | (check!) | 8 atomic tools: `SystemInfo`, `Shell`, `FileSystem` (5), `Git`, `PythonExec` (with sandboxing/timeouts). |
| **Phase 6** | LLM Integration | (soon) | **Foundation Complete:** `BaseLLMProvider`, `OllamaProvider`, `AgentProfile`, Multi-Agent Ecosystem models. |
| **Phase 7** | Autonomous Mode | (soon) | Continuous runtime loop, scheduler, event handling, autonomous decision making. |

---

## 🏗 Architecture

The system is built around a central **Composition Root** (`GLaDOSAgent`) that injects dependencies into a shared `RuntimeContext`. This ensures minimal global state and strict adherence to the Single Responsibility Principle (SRP).

```text
main.py
  │
  ▼
GLaDOSAgent (Composition Root)
  │
  ├── ConfigLoader (YAML/ENV)
  ├── Identity (Runtime representation)
  └── RuntimeContext (Shared State)
        │
        ├── Logger (Loguru)
        ├── MemoryManager (STM + LTM)
        ├── SkillRegistry (Dynamic loading)
        ├── ToolRegistry (Dynamic loading)
        └── BrainEngine (Orchestrator & Planner)
              │
              └── LLM Providers (Ollama, OpenAI, etc. - In Progress)


## Key Features:

    Strict TDD Workflow: 109+ automated tests covering models, business logic, edge cases, and async execution.
    Modern Python Stack: Built for Python 3.14+ using uv for lightning-fast dependency management and packaging.
    Robust Tooling: Safe, isolated execution of Shell commands, Git operations, Python scripts, and FileSystem manipulations with strict timeouts and output truncation.
    Multi-Agent LLM Foundation: Designed to route tasks to various local (Ollama) and cloud (OpenAI, Anthropic, xAI, DeepSeek) agents via unified AgentProfile configurations.
    Type Safety: Comprehensive pydantic v2 validation and mypy strict mode enforcement.

## Technology Stack:

    Language: Python 3.14+
    Package Manager: uv
    Validation & Settings: pydantic v2, pydantic-settings, pyyaml, python-dotenv
    Logging & CLI: loguru, typer, rich
    Networking: httpx (async HTTP client)
    Testing & Quality: pytest, pytest-asyncio, pytest-cov, ruff, mypy

## Getting Started:
   Prerequisites

    Python 3.14 or higher
    uv
     installed on your system
    (Optional) Ollama
     running locally for LLM features

## Installation

1 Clone the repository:
git clone https://github.com/CH4rnel/GLaDOS_DAEMON-SYSTEM.git

2 Sync dependencies and create the virtual environment:
uv sync 

3 Run the daemon:
uv run python main.py
# Or use the CLI entry point (if configured in pyproject.toml)
uv run glados

## Development & Testing
This project strictly follows TDD. No feature is merged without passing tests.
# Run all tests with verbose output and short tracebacks
uv run pytest -v --tb=short

# Run tests with coverage report
uv run pytest --cov=glados --cov-report=term-missing

# Lint and format code (Ruff)
uv run ruff check glados/ tests/
uv run ruff format glados/ tests/

# Static type checking (MyPy)
uv run mypy glados/


## Project Structure:
GLaDOS_DAEMON-SYSTEM/
├── glados/
│   ├── brain/          # BrainEngine, Planner, LLM models & providers
│   ├── cli/            # Typer-based command-line interface
│   ├── config/         # YAML/ENV configuration loaders
│   ├── core/           # GLaDOSAgent, Identity, RuntimeContext
│   ├── llm/            # LLM Providers (Ollama, OpenAI, etc.) and routing
│   ├── memory/         # Short-term and Long-term memory management
│   ├── skills/         # High-level skill registry and dynamic loader
│   ├── tools/          # Low-level atomic tools (Shell, FS, Git, Python)
│   └── utils/          # Shared utilities (Logger setup, etc.)
├── tests/              # Comprehensive TDD test suite
├── data/               # Persistent storage (e.g., long_term_memory.json)
├── configs/            # Default YAML configuration files
├── main.py             # Application entry point
├── pyproject.toml      # Project metadata, dependencies, and tool configs
└── uv.lock             # Deterministic dependency lock file


 License & Author

    License: MIT License
    Author: CH4rnel 𓂀CHAOSMASTER𓂀
    Repository: github.com/CH4rnel/GLaDOS_DAEMON-SYSTEM

