# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
WebSocket router for streaming chat interactions with the BrainEngine.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from glados.api.schemas import ChatRequest, ChatChunk
from glados.llm.brain import BrainEngine

router = APIRouter()

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established for /ws/chat")
    
    try:
        while True:
            data = await websocket.receive_json()
            request = ChatRequest(**data)
            
            logger.info(f"Processing chat request for agent: {request.agent_id}")
            
            engine = BrainEngine(agent_id=request.agent_id)
            async for chunk in engine.process_stream(request.message):
                response = ChatChunk(type="chunk", content=chunk)
                await websocket.send_json(response.model_dump())
            
            await websocket.send_json({"type": "end", "content": ""})
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))