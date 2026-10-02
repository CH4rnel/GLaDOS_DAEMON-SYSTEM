# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Main FastAPI application entry point for the GLaDOS Web Interface.
Serves the HEV-HUD console and API endpoints.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from glados.llm.registry import LLMRegistry
from glados.core.bootstrap import AgentsBootstrap
from glados.security.guardian import GuardianGate
from glados.tools.registry import ToolRegistry

# Router imports
from glados.api.routers import chat, agents, audit

STATIC_DIR = Path(__file__).parent / "static"
CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    logger.info("GLaDOS API Core initializing shared state...")
    
    app.state.tool_registry = ToolRegistry()
    app.state.guardian = GuardianGate(registry=app.state.tool_registry)
    app.state.llm_registry = LLMRegistry()
    
    agents_config = CONFIG_DIR / "agents.yaml"
    if agents_config.exists():
        try:
            AgentsBootstrap.register_profiles(agents_config, app.state.llm_registry)
            logger.info("Agent profiles successfully bootstrapped into shared registry.")
        except Exception as e:
            logger.error(f"Failed to bootstrap agent profiles: {e}")
    else:
        logger.warning(f"Agents config not found at {agents_config}")
        
    logger.info("GLaDOS API Core initialized and ready to serve.")
    yield
    logger.info("GLaDOS API Core shutting down.")


app = FastAPI(
    title="GLaDOS Daemon API",
    version="2.0.0",
    description="Backend API for GLaDOS Daemon Console (HEV-HUD)",
    lifespan=lifespan,
)

# Explicitly allowed sources to prevent 403 Forbidden errors in the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Router registration
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(audit.router)


@app.get("/")
async def serve_index():
    """Serve the HEV-HUD console index page."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return {"status": "GLaDOS API running", "console": "not built yet"}