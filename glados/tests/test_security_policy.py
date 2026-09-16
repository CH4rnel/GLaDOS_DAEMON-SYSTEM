# glados/tests/test_security_policy.py
# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Tests for the Guardian security policy engine (glados/security/).
Follows TDD methodology to define the contract for fail-closed enforcement.
"""

import tempfile
from pathlib import Path
from typing import Any

import pytest

from glados.security.policy import PolicyViolation, SecurityPolicy, get_policy


class MockRuntimeContext:
    """Minimal mock for RuntimeContext — mirrors the one used in test_shell_tool.py etc."""

    class MockLogger:
        def debug(self, *args: Any, **kwargs: Any) -> None: pass
        def info(self, *args: Any, **kwargs: Any) -> None: pass
        def warning(self, *args: Any, **kwargs: Any) -> None: pass
        def error(self, *args: Any, **kwargs: Any) -> None: pass

    logger = MockLogger()


class TestGetPolicy:
    """get_policy() must never raise on contexts that don't define `.security` at all."""

    def test_returns_none_for_mock_without_security_attr(self):
        ctx = MockRuntimeContext()
        assert get_policy(ctx) is None

    def test_returns_policy_when_attached(self):
        ctx = MockRuntimeContext()
        policy = SecurityPolicy()
        ctx.security = policy
        assert get_policy(ctx) is policy


class TestSecurityPolicyDefaults:
    """A bare SecurityPolicy() must be maximally restrictive, not permissive."""

    def test_no_allowed_fs_roots_by_default(self):
        policy = SecurityPolicy()
        assert policy.allowed_fs_roots == ()

    def test_python_exec_disabled_by_default(self):
        policy = SecurityPolicy()
        assert policy.python_exec_enabled is False

    def test_shell_safe_mode_enabled_by_default(self):
        policy = SecurityPolicy()
        assert policy.shell_safe_mode is True


class TestResolveWithinFsRoots:
    def test_denies_when_no_roots_configured(self):
        policy = SecurityPolicy(allowed_fs_roots=())
        with pytest.raises(PolicyViolation):
            policy.resolve_within_fs_roots("/etc/passwd")

    def test_allows_path_inside_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy = SecurityPolicy(allowed_fs_roots=(root,))
            target = root / "sub" / "file.txt"
            resolved = policy.resolve_within_fs_roots(str(target))
            assert resolved.is_relative_to(root)

    def test_denies_path_traversal_out_of_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workdir"
            root.mkdir()
            policy = SecurityPolicy(allowed_fs_roots=(root,))
            with pytest.raises(PolicyViolation):
                policy.resolve_within_fs_roots(str(root / ".." / ".." / "etc" / "passwd"))

    def test_denies_absolute_path_outside_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy = SecurityPolicy(allowed_fs_roots=(root,))
            with pytest.raises(PolicyViolation):
                policy.resolve_within_fs_roots("/etc/passwd")


class TestCheckShellCommand:
    def test_allows_allowlisted_binary(self):
        policy = SecurityPolicy(allowed_shell_binaries=frozenset({"git"}))
        policy.check_shell_command(["git", "status"])  # should not raise

    def test_denies_non_allowlisted_binary(self):
        policy = SecurityPolicy(allowed_shell_binaries=frozenset({"git"}))
        with pytest.raises(PolicyViolation):
            policy.check_shell_command(["curl", "http://evil.example"])

    def test_denies_empty_command(self):
        policy = SecurityPolicy()
        with pytest.raises(PolicyViolation):
            policy.check_shell_command([])


class TestCheckGitArgs:
    def test_allows_allowlisted_subcommand(self):
        policy = SecurityPolicy(allowed_git_subcommands=frozenset({"status"}))
        policy.check_git_args(["status"])  # should not raise

    def test_denies_non_allowlisted_subcommand(self):
        policy = SecurityPolicy(allowed_git_subcommands=frozenset({"status"}))
        with pytest.raises(PolicyViolation):
            policy.check_git_args(["push", "origin", "main"])

    def test_denies_remote_outside_allowed_domains(self):
        policy = SecurityPolicy(
            allowed_git_subcommands=frozenset({"clone"}),
            allowed_git_remote_domains=frozenset({"github.com"}),
        )
        with pytest.raises(PolicyViolation):
            policy.check_git_args(["clone", "https://attacker.example/repo.git"])

    def test_allows_remote_inside_allowed_domains(self):
        policy = SecurityPolicy(
            allowed_git_subcommands=frozenset({"clone"}),
            allowed_git_remote_domains=frozenset({"github.com"}),
        )
        policy.check_git_args(["clone", "https://github.com/foo/bar.git"])  # should not raise


class TestCheckPythonExec:
    def test_denies_by_default(self):
        policy = SecurityPolicy()
        with pytest.raises(PolicyViolation):
            policy.check_python_exec()

    def test_allows_when_explicitly_enabled(self):
        policy = SecurityPolicy(python_exec_enabled=True)
        policy.check_python_exec()  # should not raise