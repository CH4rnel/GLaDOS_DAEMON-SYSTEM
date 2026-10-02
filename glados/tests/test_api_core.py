# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS API Core.
Covers WebSocket chat streaming and GuardianGate audit log retrieval.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from glados.api.main import app


class TestAPIWebSocket:
    """Tests for the /ws/chat WebSocket endpoint."""

    def test_websocket_connection_and_streaming(self):
        """Test successful WebSocket connection and message streaming."""
        client = TestClient(app)
        
        async def mock_process_stream(message: str):
            yield "Thinking..."
            yield "Done."
        
        with patch("glados.api.routers.chat.BrainEngine") as mock_brain:
            mock_instance = AsyncMock()
            mock_instance.process_stream = mock_process_stream
            mock_brain.return_value = mock_instance
            
            with client.websocket_connect("/ws/chat") as websocket:
                websocket.send_json({"message": "Test prompt", "agent_id": "local_qwen_coder"})
                
                response_1 = websocket.receive_json()
                assert response_1["type"] == "chunk"
                assert response_1["content"] == "Thinking..."
                
                response_2 = websocket.receive_json()
                assert response_2["type"] == "chunk"
                assert response_2["content"] == "Done."
                
                response_3 = websocket.receive_json()
                assert response_3["type"] == "end"


class TestAPIAudit:
    """Tests for the /api/v1/audit REST endpoint."""

    def test_get_audit_logs_success(self):
        """Test retrieval of GuardianGate audit logs."""
        client = TestClient(app)
        
        mock_logs = [
            {"timestamp": "2026-10-02T12:00:00Z", "action": "TOOL_CALL", "status": "ALLOWED", "details": "fts5_search"},
            {"timestamp": "2026-10-02T12:05:00Z", "action": "AGENT_SPAWN", "status": "DENIED", "details": "Exceeded resource bounds"}
        ]
        
        with patch("glados.api.routers.audit.get_guardian_logs", return_value=mock_logs):
            response = client.get("/api/v1/audit?limit=2")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["action"] == "TOOL_CALL"
            assert data[1]["status"] == "DENIED"

    def test_get_audit_logs_empty(self):
        """Test retrieval when no audit logs are present."""
        client = TestClient(app)
        
        with patch("glados.api.routers.audit.get_guardian_logs", return_value=[]):
            response = client.get("/api/v1/audit")
            
            assert response.status_code == 200
            assert response.json() == []