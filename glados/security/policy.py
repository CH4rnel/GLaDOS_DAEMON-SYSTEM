# glados/security/policy.py
# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Guardian Security Policy for GLaDOS_DAEMON-SYSTEM.

Implements the `system.guardian_enabled` promise made in configs/identity.yaml.
Previously that flag was declarative only — nothing in the codebase read it.
This module is the actual enforcement layer: an allowlist-based, fail-closed
policy that every risk-bearing tool (filesystem, shell, git, python_exec)
consults before touching the host.

Design notes:
- Enforcement lives in each tool's `execute()`, not only in a central
  dispatcher. This matters because BrainEngine does not yet call tools
  (see brain/engine.py TODO) — when Phase 7 wires it up, whatever code
  path calls `tool.execute(ctx, params)` gets the same protection, with
  no risk of someone bypassing a gate that only wraps one call site.
- Policy is looked up via `getattr(ctx, "security", None)` rather than a
  required field, so the existing test suite (which uses a minimal
  MockRuntimeContext without a `.security` attribute) keeps passing
  unchanged. When no policy is attached, tools log a loud warning and
  fall back to their previous (unrestricted) behaviour — enforcement is
  opt-in for tests, mandatory once GLaDOSAgent wires a real policy in
  production (see core/agent.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger


class PolicyViolation(Exception):
    """Raised when an action would violate the active SecurityPolicy."""


@dataclass(slots=True)
class SecurityPolicy:
    """
    Central, fail-closed policy consulted by risk-bearing tools.

    Everything defaults to the most restrictive reasonable setting.
    Widen deliberately via configs/security.yaml, not by editing tool code.
    """

    # --- Filesystem ---
    allowed_fs_roots: tuple[Path, ...] = field(default_factory=tuple)

    # --- Shell ---
    allowed_shell_binaries: frozenset[str] = field(
        default_factory=lambda: frozenset({"git", "python3", "pytest", "ruff", "mypy", "uv"})
    )
    shell_safe_mode: bool = True  # True: no shell interpretation, exec+allowlist only
    max_shell_timeout: int = 60

    # --- Git ---
    allowed_git_subcommands: frozenset[str] = field(
        default_factory=lambda: frozenset({"status", "log", "diff", "add", "commit", "branch", "checkout"})
    )
    allowed_git_remote_domains: frozenset[str] = field(
        default_factory=lambda: frozenset({"github.com", "raw.githubusercontent.com"})
    )

    # --- Python exec ---
    python_exec_enabled: bool = False  # off by default — see python_exec.py docstring

    def resolve_within_fs_roots(self, path_str: str) -> Path:
        """
        Resolves `path_str` (following symlinks) and enforces that the
        result sits under one of `allowed_fs_roots`.

        :raises PolicyViolation: if the resolved path escapes every allowed root.
        """
        resolved = Path(path_str).expanduser().resolve()

        if not self.allowed_fs_roots:
            raise PolicyViolation(
                "no allowed_fs_roots configured — filesystem access denied by default"
            )

        for root in self.allowed_fs_roots:
            root_resolved = root.expanduser().resolve()
            if resolved == root_resolved or resolved.is_relative_to(root_resolved):
                return resolved

        raise PolicyViolation(
            f"path '{resolved}' is outside all allowed roots "
            f"({', '.join(str(r) for r in self.allowed_fs_roots)})"
        )

    def check_shell_command(self, argv: list[str]) -> None:
        if not argv:
            raise PolicyViolation("empty command")
        binary = Path(argv[0]).name
        if binary not in self.allowed_shell_binaries:
            raise PolicyViolation(
                f"binary '{binary}' is not in allowed_shell_binaries "
                f"({', '.join(sorted(self.allowed_shell_binaries))})"
            )

    def check_git_args(self, args: list[str]) -> None:
        if not args:
            raise PolicyViolation("empty git args")
        subcommand = args[0]
        if subcommand not in self.allowed_git_subcommands:
            raise PolicyViolation(
                f"git subcommand '{subcommand}' is not in allowed_git_subcommands "
                f"({', '.join(sorted(self.allowed_git_subcommands))})"
            )
        # Any argument that looks like a remote URL must match an allowed domain.
        for arg in args[1:]:
            if "://" in arg or arg.startswith("git@"):
                if not any(domain in arg for domain in self.allowed_git_remote_domains):
                    raise PolicyViolation(
                        f"remote '{arg}' does not match allowed_git_remote_domains "
                        f"({', '.join(sorted(self.allowed_git_remote_domains))})"
                    )

    def check_python_exec(self) -> None:
        if not self.python_exec_enabled:
            raise PolicyViolation(
                "python_exec is disabled by policy — enable only behind real OS-level "
                "isolation (separate container/VM), not as a library-level toggle"
            )


def get_policy(ctx: Any) -> SecurityPolicy | None:
    """
    Safely fetches `ctx.security` without raising on mocks/contexts that
    don't define the attribute at all (see module docstring).
    """
    return getattr(ctx, "security", None)


def log_missing_policy(component: str) -> None:
    logger.bind(component="Guardian").warning(
        f"{component}: no SecurityPolicy attached to RuntimeContext — "
        f"running WITHOUT Guardian enforcement. This is expected in unit tests, "
        f"not in a running daemon."
    )