# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS CLI commands.
Follows TDD methodology to define the contract for command-line interface.
"""

import pytest
from typer.testing import CliRunner
from unittest.mock import AsyncMock, MagicMock, patch

from glados.cli.main import app


class TestCLI:
    """Tests for CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_app_exists(self):
        """Test that CLI app is defined."""
        assert app is not None

    def test_cli_help_command(self):
        """Test that --help flag works."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "GLaDOS" in result.stdout or "glados" in result.stdout.lower()

    @patch('glados.cli.main.GLaDOSAgent')
    def test_cli_status_command(self, mock_agent_class):
        """Test status command displays system information."""
        mock_agent = MagicMock()
        mock_agent.identity.name = "GLaDOS"
        mock_agent.identity.codename = "Test"
        mock_agent.identity.version = "0.1.0"
        mock_agent.identity.owner = {"username": "test", "environment": "test"}
        mock_agent.skills.list_all.return_value = []
        mock_agent.tools.list_all.return_value = []
        mock_agent.llm_agents.list_all.return_value = []
        mock_agent.llm_agents.get_active.return_value = []
        mock_agent_class.return_value = mock_agent

        result = self.runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "GLaDOS" in result.stdout

    @patch('glados.cli.main.GLaDOSAgent')
    def test_cli_agents_command(self, mock_agent_class):
        """Test agents command lists registered agents."""
        mock_agent = MagicMock()
        mock_agent.llm_agents.list_all.return_value = []
        mock_agent_class.return_value = mock_agent

        result = self.runner.invoke(app, ["agents"])

        assert result.exit_code == 0

    @patch('glados.cli.main.GLaDOSAgent')
    def test_cli_task_command(self, mock_agent_class):
        """Test task command processes a task."""
        mock_agent = MagicMock()
        mock_brain = MagicMock()

        # Create a result mock using the actual `data` dictionary.
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.message = "Task completed"
        mock_result.data = {"status": "planned", "plan_steps_count": 3}

        # KEY FIX: process_task is an async method,
        # That's why we use AsyncMock instead of the standard MagicMock.s
        mock_brain.process_task = AsyncMock(return_value=mock_result)
        mock_agent.brain = mock_brain
        mock_agent_class.return_value = mock_agent

        result = self.runner.invoke(app, ["task", "Test task description"])

        assert result.exit_code == 0
        assert "Processing task" in result.stdout or "Success" in result.stdout

    @patch('glados.cli.main.GLaDOSAgent')
    def test_cli_task_command_with_priority(self, mock_agent_class):
        """Test task command with custom priority."""
        mock_agent = MagicMock()
        mock_brain = MagicMock()

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.message = "High priority task done"
        mock_result.data = {}

        mock_brain.process_task = AsyncMock(return_value=mock_result)
        mock_agent.brain = mock_brain
        mock_agent_class.return_value = mock_agent

        result = self.runner.invoke(app, ["task", "Urgent task", "--priority", "5"])

        assert result.exit_code == 0

    @patch('glados.cli.main.GLaDOSAgent')
    def test_cli_task_command_with_agent_id(self, mock_agent_class):
        """Test task command with preferred agent ID."""
        mock_agent = MagicMock()
        mock_brain = MagicMock()

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.message = "Routed to specific agent"
        mock_result.data = {}

        mock_brain.process_task = AsyncMock(return_value=mock_result)
        mock_agent.brain = mock_brain
        mock_agent_class.return_value = mock_agent

        result = self.runner.invoke(app, [
            "task", "Code review", "--agent-id", "qwen_coder"
        ])

        assert result.exit_code == 0

    @patch('glados.cli.main.GLaDOSAgent')
    def test_cli_task_command_failure(self, mock_agent_class):
        """Test task command handles failure gracefully."""
        mock_agent = MagicMock()
        mock_brain = MagicMock()

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.message = "Task failed: LLM unavailable"
        mock_result.data = {"error_type": "ConnectionError"}

        mock_brain.process_task = AsyncMock(return_value=mock_result)
        mock_agent.brain = mock_brain
        mock_agent_class.return_value = mock_agent

        result = self.runner.invoke(app, ["task", "Impossible task"])

        # The command must complete successfully (exit_code 0).,
        # дEven if the task is not completed, an error is displayed to the user.
        assert result.exit_code == 0
        assert "Failed" in result.stdout or "failed" in result.stdout.lower()

    @patch('glados.cli.main.GLaDOSAgent')
    def test_cli_memory_command(self, mock_agent_class):
        """Test memory command displays memory information."""
        mock_agent = MagicMock()
        mock_memory = MagicMock()
        mock_memory.get_short_term_context.return_value = []
        mock_memory.search_long_term.return_value = []
        mock_agent.ctx.memory = mock_memory
        mock_agent_class.return_value = mock_agent

        result = self.runner.invoke(app, ["memory"])

        assert result.exit_code == 0

    @patch('glados.cli.main.GLaDOSAgent')
    def test_cli_memory_command_with_search(self, mock_agent_class):
        """Test memory command with search term."""
        mock_agent = MagicMock()
        mock_memory = MagicMock()
        mock_memory.get_short_term_context.return_value = []
        mock_memory.search_long_term.return_value = []
        mock_agent.ctx.memory = mock_memory
        mock_agent_class.return_value = mock_agent

        result = self.runner.invoke(app, ["memory", "--search", "Python"])

        assert result.exit_code == 0

    @patch('glados.cli.main.GLaDOSAgent')
    def test_cli_logs_command(self, mock_agent_class):
        """Test logs command displays recent logs."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        result = self.runner.invoke(app, ["logs"])

        assert result.exit_code == 0