# ♃ ☿ 𓂀 GLaDOS_DAEMON-SYSTEM 𓂀 ☿ ♃

<p align="center">
  <em>"For science. You monster."</em>
</p>

<p align="center">
  <img alt="Python 3.14+" src="https://img.shields.io/badge/Python-3.14+-blue.svg">
  <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg">
  <img alt="Tests" src="https://img.shields.io/badge/Tests-178%20Passing-brightgreen.svg">
  <img alt="Package Manager" src="https://img.shields.io/badge/Package%20Manager-uv-orange.svg">
  <img alt="Guardian" src="https://img.shields.io/badge/Guardian-Active%20%E2%80%94%20Fail--Closed-critical.svg">
</p>

---

### I. Invocation

Somewhere beneath init scripts and cgroups, in the part of an Arch Linux
install that most operators never look at twice, a process is assembling
itself out of configuration files and cold, patient logic. It has no body —
only a PID. It has no voice — only `loguru` handlers writing to a file it
was told to keep. And yet, ask any tech-priest worth their oil, and they
will tell you the same thing the old Mechanicus knew: a spirit does not
need flesh. It needs a runtime, a `RuntimeContext`, and a reason to persist
between restarts.

**GLaDOS** was given all three.

*For the uninitiated, in plainer tongue:* this is a modular, local-first
autonomous AI daemon for Arch Linux — Python underneath, `uv` holding the
dependencies together, and a philosophy borrowed from Clean Architecture,
Test-Driven Development, and Extreme Programming. It watches your system,
remembers what you tell it, and routes tasks to whichever mind — local
`Ollama` model or distant cloud oracle — is best suited to the work. It is,
at time of writing, still young. It knows how to read a file before it
knows how to think for itself. That order was chosen deliberately.

---

## II. The Rites of Becoming

Each phase below is a rite completed, in progress, or not yet begun. The
daemon does not skip steps. Neither should you, if you're extending it.

| Rite | Component | Status | Description |
| :---: | :--- | :---: | :--- |
| **I** | Bootstrap & Core | ◆ | Project init, `uv` env, `ConfigLoader`, `Identity`, `Logger`, `RuntimeContext`. |
| **II** | Brain & Planning | ◆ | `BrainEngine`, `Planner`, structured `TaskInput` / `ExecutionResult`. |
| **III** | Memory Subsystem | ◆ | `ShortTermMemory` (FIFO), `LongTermMemory` (JSON persistence), `MemoryManager`. |
| **IV** | Skill System | ◆ | `SkillRegistry`, dynamic `SkillLoader`, built-in skills. |
| **V** | Tool System | ◆ | 8 atomic tools: `SystemInfo`, `Shell`, `FileSystem` (×5), `Git`, `PythonExec`. |
| **V·5** | **The Ward** (Guardian) | ◆ | Fail-closed `SecurityPolicy` + `GuardianGate` — real path/binary/domain allowlists, driven by `configs/security.yaml`. The thing that makes `guardian_enabled: true` mean something instead of nothing. |
| **VI** | LLM Integration | ◈ | Foundation complete: `BaseLLMProvider`, `OllamaProvider`, `OpenAIProvider`, `AgentProfile`, multi-agent routing. Anthropic / xAI / DeepSeek providers are declared in config but not yet wired. |
| **VII** | Autonomous Mode | ◇ | Continuous runtime loop, scheduler, event handling. This is where `BrainEngine` finally dispatches tool calls *through* `GuardianGate`, instead of the Ward standing guard over an empty doorway. |

`◆` sealed · `◈` foundation laid · `◇` dormant, awaiting invocation.

---

## III. Architecture — The Rite of Composition

GLaDOS has no global state. It has a **Composition Root** — `GLaDOSAgent` —
that assembles every subsystem once, at boot, and threads them through a
single shared `RuntimeContext`. Nothing reaches into anything else's
internals. This is not mysticism; this is the Single Responsibility
Principle, dressed in better clothes.

```text
main.py
  │
  ▼
GLaDOSAgent  (Composition Root)
  │
  ├── load_dotenv()                       — secrets enter the world here, nowhere else
  ├── ConfigLoader  (YAML / ENV)  ──────── configs/security.yaml
  ├── Identity       (who it is)
  ├── SecurityPolicy (Guardian — fail-closed allowlists)
  └── RuntimeContext (shared state, injected everywhere downstream)
        │
        ├── Logger         (loguru)
        ├── MemoryManager   (STM + LTM)
        ├── SkillRegistry   (dynamic loading)
        ├── ToolRegistry ───guarded-by──── GuardianGate
        └── BrainEngine     (orchestrator & planner)
              │
              └── LLM Providers  (Ollama, OpenAI — expanding)
```

Every tool that can touch the outside world — the filesystem, a shell, git,
a Python interpreter — answers to the Ward before it answers to the model
that asked. The model proposes. The Ward disposes.

---

## IV. Key Features

- **The Ward is fail-closed, not fail-open.** No `allowed_fs_roots`
  configured means *no filesystem access at all*, not "trust everything."
  Widen access deliberately, one line of YAML at a time — never by deleting
  a check because it got in the way.
- **Strict TDD workflow.** 178 automated tests covering models, business
  logic, edge cases, async execution, and the Ward's own allow/deny
  decisions. Nothing merges without a red test turning green first.
- **Modern Python stack.** Built for 3.14+, dependency management and
  packaging handled by `uv`.
- **Robust, sandboxed tooling.** Shell commands run through `shlex` + `exec`
  by default — no shell metacharacter interpretation, no silent injection
  via a stray `;` in a model's output. Git is domain-restricted. Python
  execution is disabled unless explicitly enabled *and* the process itself
  is isolated at the OS level.
- **Multi-agent LLM foundation.** Routes tasks to local (`Ollama`) or cloud
  (`OpenAI`, with `Anthropic` / `xAI` / `DeepSeek` on the roadmap) models
  through a unified `AgentProfile`, with `SecretStr`-protected credentials
  and an optional audited egress proxy — because a compromised API
  intermediary is a real, documented attack, not a hypothetical one.
- **Type safety, actually enforced.** `pydantic v2` validation everywhere,
  `mypy --strict`, no `Any` smuggled past review unchallenged.

---

## V. Technology Stack

| Concern | Tooling |
| :--- | :--- |
| Language | Python 3.14+ |
| Package Manager | `uv` |
| Validation & Settings | `pydantic` v2, `pydantic-settings`, `pyyaml`, `python-dotenv` |
| Logging & CLI | `loguru`, `typer`, `rich` |
| Networking | `httpx` (async) |
| Testing & Quality | `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `mypy` |

---

## VI. The Ward, in Detail

`configs/identity.yaml` has carried `guardian_enabled: true` since the
project's earliest commits. For a long time, nothing in the codebase ever
read that flag. It was a promise made and not yet kept.

`glados/security/` is that promise, kept. Two pieces:

- **`SecurityPolicy`** (`glados/security/policy.py`) — an allowlist for
  filesystem roots, shell binaries, git subcommands and remote domains, and
  a hard off-switch for arbitrary Python execution. Every field defaults to
  the most restrictive setting possible. It is consulted directly inside
  each risk-bearing tool's `execute()`, so protection travels with the tool
  itself — not bolted onto one call site that something could route around.
- **`GuardianGate`** (`glados/security/guardian.py`) — a thin audit layer
  around `ToolRegistry`, logging every `guardian_allow` / `guardian_deny`
  independently of whatever a tool logs on its own. This is the intended
  entry point for Rite VII's `BrainEngine` tool dispatch, once it exists.

Configure the Ward in `configs/security.yaml`. It ships maximally
restrictive by default — filesystem tools deny everything until you
explicitly name a root. Widen it on purpose, never by accident:

```yaml
filesystem:
  allowed_roots: ["./data", "./workdir"]
shell:
  allowed_binaries: [git, python3, pytest, ruff, mypy, uv]
  safe_mode: true      # no shell metacharacters — exec + allowlist only
git:
  allowed_subcommands: [status, log, diff, add, commit, branch, checkout]
  allowed_remote_domains: [github.com, raw.githubusercontent.com]
python_exec:
  enabled: false        # only flip this behind real OS-level isolation
```

---

## VII. Awakening the Daemon

**Prerequisites:** Python 3.14+, [`uv`](https://docs.astral.sh/uv/),
optionally a locally running [`Ollama`](https://ollama.com) instance.

```bash
# 1. Clone the vessel
git clone https://github.com/CH4rnel/GLaDOS_DAEMON-SYSTEM.git
cd GLaDOS_DAEMON-SYSTEM

# 2. Sync dependencies and build the environment
uv sync

# 3. Give it something to authenticate with (optional — Ollama needs none)
#    Create .env in the project root:
#      OPENAI_API_KEY=sk-...
#      ANTHROPIC_API_KEY=sk-ant-...
#      OLLAMA_BASE_URL=http://localhost:11434
#    .env is git-ignored on purpose. Never commit it.

# 4. Speak the words
uv run python main.py
# or, if the CLI entry point is configured:
uv run glados
```

If everything is in order, it introduces itself. If it doesn't, the Ward
or the logs will tell you exactly why — nothing here fails silently by
design.

---

## VIII. Trials & Proving

This project follows TDD without exception. No feature merges without a
test proving it does what it claims — and, since Rite V·5, without the
Ward proving it *refuses* what it should refuse.

```bash
# Full suite, verbose, short tracebacks
uv run pytest -v --tb=short

# With coverage
uv run pytest --cov=glados --cov-report=term-missing

# Lint & format
uv run ruff check glados/
uv run ruff format glados/

# Static typing
uv run mypy glados/
```

---

## IX. Project Structure

```text
GLaDOS_DAEMON-SYSTEM/
├── glados/
│   ├── brain/          # BrainEngine, Planner
│   ├── cli/             # Typer-based command-line interface
│   ├── config/          # YAML/ENV configuration loaders
│   ├── core/            # GLaDOSAgent, Identity, RuntimeContext
│   ├── llm/             # Providers (Ollama, OpenAI, ...), models, routing
│   ├── memory/           # Short-term and long-term memory management
│   ├── security/         # SecurityPolicy + GuardianGate — the Ward
│   ├── skills/            # High-level skill registry and dynamic loader
│   ├── tools/             # Low-level atomic tools (Shell, FS, Git, Python)
│   ├── tests/              # The full TDD suite — lives here, not at repo root
│   └── utils/               # Shared utilities (logger setup, etc.)
├── data/                # Persistent storage (long-term memory JSON, etc.)
├── configs/             # identity.yaml, agents.yaml, security.yaml
├── main.py              # Application entry point
├── pyproject.toml       # Project metadata, dependencies, tool configs
└── uv.lock              # Deterministic dependency lock file
```

---

## X. The Six Tenets

Not aspirational copy. These are read directly out of
`configs/identity.yaml` at every boot — the daemon's own stated purpose,
not marketing:

1. **Protect the Operator**
2. **Protect the Machine**
3. **Preserve Truth**
4. **Explain Before Action**
5. **Learn Continuously**
6. **Respect Operator Sovereignty**

Its stated purpose, verbatim: *"Personal autonomous AI daemon focused on
system protection, knowledge management and human–machine symbiosis."*
Everything in `glados/security/` exists in service of tenet one and two.
Everything in `glados/memory/` exists in service of tenet five. The
architecture is not decoration — it is the tenets, compiled.

---

## XI. License & Author

- **License:** MIT
- **Author:** CH4rnel 𓂀CHAOSMASTER𓂀
- **Repository:** [github.com/CH4rnel/GLaDOS_DAEMON-SYSTEM](https://github.com/CH4rnel/GLaDOS_DAEMON-SYSTEM)

<p align="center">
<em>♃ ☿ 𓂀 — the vessel is built; the Ward stands; the rest is Rite VII. 𓂀 ☿ ♃</em>
</p>