# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS CLI commands.
Follows TDD methodology to define the contract for command-line interface.
"""

import pytest
from typer.testing import CliRunner
from unittest.mock import MagicMock, patch

from glados.cli.main import app
from glados.core.agent import GLaDOSAgent


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
        # Mock the agent
        mock_agent = MagicMock()
        mock_agent.identity.name = "GLaDOS"
        mock_agent.identity.codename = "Test"
        mock_agent.identity.version = "0.1.0"
        mock_agent.skills.list_all.return_value = []
        mock_agent.tools.list_all.return_value = []
        mock_agent.llm_agents.list_all.return_value = []
        mock_agent.llm_agents.get_active.return_value = []
        mock_agent_class.return_value = mock_agent
        
        result = self.runner.invoke(app, ["status"])
        
        assert result.exit_code == 0
        assert "GLaDOS" in result.stdout
        assert "Status" in result.stdout or "ONLINE" in result.stdout

    @patch('glados.cli.main.GLaDOSAgent')
    def test_cli_agents_command(self, mock_agent_class):
        """Test agents command lists registered agents."""
        # Mock the agent
        mock_agent = MagicMock()
        mock_agent.llm_agents.list_all.return_value = []
        mock_agent_class.return_value = mock_agent
        
        result = self.runner.invoke(app, ["agents"])
        
        assert result.exit_code == 0
        # Should display agents list (even if empty)

    @patch('glados.cli.main.GLaDOSAgent')
    def test_cli_task_command(self, mock_agent_class):
        """Test task command processes a task."""
        # Mock the agent and brain engine
        mock_agent = MagicMock()
        mock_brain = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.message = "Task completed"
        mock_brain.process_task.return_value = mock_result
        mock_agent.brain = mock_brain
        mock_agent_class.return_value = mock_agent
        
        result = self.runner.invoke(app, ["task", "Test task description"])
        
        assert result.exit_code == 0
        # Should process the task

    @patch('glados.cli.main.GLaDOSAgent')
    def test_cli_memory_command(self, mock_agent_class):
        """Test memory command displays memory information."""
        # Mock the agent
        mock_agent = MagicMock()
        mock_memory = MagicMock()
        mock_memory.get_short_term_context.return_value = []
        mock_memory.search_long_term.return_value = []
        mock_agent.ctx.memory = mock_memory
        mock_agent_class.return_value = mock_agent
        
        result = self.runner.invoke(app, ["memory"])
        
        assert result.exit_code == 0
        # Should display memory information

    @patch('glados.cli.main.GLaDOSAgent')
    def test_cli_logs_command(self, mock_agent_class):
        """Test logs command displays recent logs."""
        # Mock the agent
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        result = self.runner.invoke(app, ["logs"])
        
        assert result.exit_code == 0
        # Should display logs or log file location