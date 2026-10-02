# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Main FastAPI application entry point for the GLaDOS Web Interface.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from glados.api.routers.chat import router as chat_router
from glados.api.routers.audit import router as audit_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    logger.info("GLaDOS API Core initialized and ready to serve.")
    yield
    logger.info("GLaDOS API Core shutting down.")


app = FastAPI(
    title="GLaDOS Daemon API",
    version="2.0.0",
    description="Backend API for GLaDOS Daemon Console (HEV-HUD)",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(audit_router)