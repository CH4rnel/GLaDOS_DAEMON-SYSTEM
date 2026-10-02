# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the HEV-HUD frontend serving and API gaps.
Covers static file mounting, GuardianGate ring buffer, and agent roster endpoint.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from glados.api.main import app
from glados.tools.registry import ToolRegistry
from glados.security.guardian import GuardianGate, _audit_log_buffer


class TestStaticFiles:
    """Tests for static file serving."""

    def test_index_html_is_served(self):
        """Test that the HEV-HUD index page is accessible."""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_hud_css_is_served(self):
        """Test that the HUD stylesheet is accessible."""
        client = TestClient(app)
        response = client.get("/static/css/hud.css")
        assert response.status_code == 200

    def test_console_js_is_served(self):
        """Test that the console JavaScript is accessible."""
        client = TestClient(app)
        response = client.get("/static/js/console.js")
        assert response.status_code == 200


class TestAgentRosterEndpoint:
    """Tests for the /api/agents endpoint."""

    def test_list_agents_returns_profiles(self):
        """Test that the /api/agents endpoint returns serialized profiles from the registry."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from unittest.mock import MagicMock
        from glados.api.routers.agents import router
        from glados.llm.models import AgentProfile

        app = FastAPI()
        app.include_router(router)

        mock_profile = MagicMock(spec=AgentProfile)
        mock_profile.model_dump.return_value = {"agent_id": "test-agent", "provider": "ollama"}
        
        mock_registry = MagicMock()
        mock_registry.list_all.return_value = [mock_profile]
        
        app.state.llm_registry = mock_registry

        client = TestClient(app)
        response = client.get("/api/agents")
        
        assert response.status_code == 200
        assert response.json() == [{"agent_id": "test-agent", "provider": "ollama"}]


class TestGuardianRingBuffer:
    """Tests for GuardianGate in-memory ring buffer."""

    def test_recent_log_returns_bounded_entries(self):
        """Test that recent_log returns at most N entries from the ring buffer."""
        _audit_log_buffer.clear()
        
        registry = ToolRegistry()
        guardian = GuardianGate(registry=registry)

        # Simulate audit entries
        for i in range(20):
            guardian.log_audit(
                action="TOOL_CALL",
                status="ALLOWED",
                details=f"tool_{i}",
            )

        recent = guardian.recent_log(limit=5)
        assert len(recent) == 5
        assert recent[0]["details"] == "tool_15"
        assert recent[-1]["details"] == "tool_19"

    def test_recent_log_empty_buffer(self):
        """Test that recent_log returns empty list when no entries exist."""
        _audit_log_buffer.clear()
        
        registry = ToolRegistry()
        guardian = GuardianGate(registry=registry)
        
        recent = guardian.recent_log(limit=10)
        assert recent == []