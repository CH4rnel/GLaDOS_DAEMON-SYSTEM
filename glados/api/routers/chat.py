# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
WebSocket router for streaming chat interactions with the BrainEngine.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from glados.api.schemas import ChatRequest
from glados.llm.factory import LLMProviderFactory
from glados.llm.models import LLMMessage

router = APIRouter()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established for /ws/chat")
    
    # Access shared state
    app = websocket.scope["app"]
    registry = app.state.llm_registry

    try:
        while True:
            data = await websocket.receive_json()
            request_data = ChatRequest(**data)
            logger.info(f"Processing chat request for agent: {request_data.agent_id}")

            try:
                profile = registry.get(request_data.agent_id)
            except Exception as e:
                logger.error(f"Agent not found: {request_data.agent_id}. Error: {e}")
                await websocket.send_json({
                    "type": "error", 
                    "content": f"Agent '{request_data.agent_id}' not found. Check configs/agents.yaml and env vars."
                })
                continue

            provider = LLMProviderFactory.create_provider(profile)
            messages = [LLMMessage(role="user", content=request_data.message)]

            try:
                async for chunk in provider.complete_stream(messages, profile):
                    await websocket.send_json({"type": "chunk", "content": chunk})
            except Exception as e:
                logger.error(f"LLM streaming error: {e}")
                await websocket.send_json({"type": "error", "content": f"LLM Error: {str(e)}"})

            await websocket.send_json({"type": "end", "content": ""})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))