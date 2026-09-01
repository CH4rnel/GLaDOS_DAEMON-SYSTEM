<img width="965" height="575" alt="ascii-art-text" src="https://github.com/user-attachments/assets/a2b161d2-4995-452b-90f8-25b7a73b8ddf" />
# GLaDOS_DAEMON-SYSTEM

> **Personal Autonomous AI Daemon** for Arch Linux focused on system management, knowledge processing and future autonomous operation.

---

# Overview

**GLaDOS_DAEMON-SYSTEM** is a modular Python project whose long-term goal is to become a local AI daemon capable of assisting the operator, interacting with the operating system, managing knowledge, and orchestrating intelligent workflows.

The project follows a clean layered architecture, where each subsystem has a single responsibility and can evolve independently.

Current development status: **v0.1.0 (Bootstrap Architecture)**

---

# Project Goals

## Primary Goal

Build a reliable autonomous AI assistant running locally on the user's machine.

## Long-Term Vision

The daemon should eventually be able to:

* communicate with the user;
* understand tasks;
* plan actions;
* interact with the operating system;
* remember previous interactions;
* execute tools safely;
* integrate with external LLMs;
* support plugins and extensions;
* operate continuously as a background service.

---

# Current Architecture

```text
main.py
    │
    ▼
GLaDOSAgent
    │
    ▼
RuntimeContext
    │
 ┌──┴───────────────┐
 │                  │
Identity        Logger
 │
ConfigLoader
```

---

# Project Structure

```text
glados/
│
├── brain/
├── cli/
├── config/
├── core/
├── memory/
├── skills/
├── tools/
└── utils/
```

---

# Implemented Components

## Core

Contains the main runtime logic.

Current modules:

* `GLaDOSAgent`
* `Identity`
* `RuntimeContext`

---

## Config

Responsible only for reading configuration files.

Implemented:

* YAML configuration loader
* Identity loading

---

## Identity

Runtime representation of the assistant.

Current fields include:

* name
* codename
* version
* owner
* system
* purpose
* personality
* principles

---

## Runtime Context

Provides shared runtime state across the application.

Contains:

* Identity
* Logger

This object will later be expanded with memory, brain, tools and skills.

---

## Logger

Centralized logging using **Loguru**.

Responsibilities:

* runtime logs;
* diagnostics;
* debugging;
* future audit trail.

---

# Development Milestones

## Phase 1 — Bootstrap ✅

Completed:

* project initialization;
* package structure;
* uv environment;
* pyproject configuration;
* logging;
* configuration loading;
* runtime identity;
* startup banner;
* RuntimeContext.

---

## Phase 2 — In Progress

Planned:

* Brain Engine;
* planning system;
* runtime state.

---

## Phase 3

Memory subsystem.

Planned:

* short-term memory;
* persistent storage;
* semantic search.

---

## Phase 4

Skill System.

Planned:

* skill registry;
* built-in skills;
* dynamic loading.

---

## Phase 5

Tool System.

Planned:

* shell execution;
* filesystem access;
* Git integration;
* Python execution;
* system information.

---

## Phase 6

LLM Integration.

Planned support:

* OpenAI;
* Ollama;
* local models;
* configurable providers.

---

## Phase 7

Autonomous Mode.

Planned:

* continuous runtime loop;
* scheduler;
* event handling;
* autonomous decision making.

---

# Development History

During the bootstrap stage several issues were resolved.

## Configuration

* invalid `pyproject.toml`;
* dependency resolution issues.

Resolved by correcting the TOML syntax and rebuilding the environment.

---

## Python Environment

Encountered conflicts between:

* system Python;
* pyenv;
* uv virtual environment.

Resolved by activating and consistently using the project `.venv`.

---

## Dependency Issues

Resolved:

* `ModuleNotFoundError: yaml`
* package installation inconsistencies.

---

## Runtime Issues

Resolved:

* dataclass import errors;
* missing Identity fields;
* duplicate imports;
* runtime context initialization;
* BrainEngine import scaffolding;
* logger typing issues;
* indentation errors.

---

# Design Principles

The project follows:

* Clean Architecture;
* Single Responsibility Principle;
* modular design;
* explicit dependency injection;
* typed Python;
* configuration-first approach;
* minimal global state.

---

# Technology Stack

* Python 3.14
* uv
* PyYAML
* Loguru
* Pydantic
* Typer
* Rich

---

# Current Status

Current version:

**v0.1.0**

Implemented:

* project bootstrap;
* configuration layer;
* identity layer;
* runtime context;
* logging;
* startup sequence.

The project is now ready for implementation of the **Brain Engine**, which will become the central orchestration component of the system.

---

# Next Steps

1. Implement `BrainEngine`.
2. Add planning subsystem.
3. Introduce memory manager.
4. Build skill registry.
5. Build tool registry.
6. Add CLI commands.
7. Integrate LLM providers.
8. Implement autonomous runtime loop.

---

# License

Apache License

---

# Author

**CH4rnel**

Project: **GLaDOS_DAEMON-SYSTEM**
