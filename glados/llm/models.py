# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Data models and schemas for the GLaDOS LLM subsystem.
Defines the core contracts for messages, responses, agent profiles, and provider types.
Designed to support a multi-agent ecosystem (Ollama, OpenAI, Claude, Grok, DeepSeek, etc.).
"""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    """
    Enumeration of supported LLM provider types.
    Extensible to support the entire multi-agent ecosystem.
    """
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"      # Claude
    XAI = "xai"                  # Grok
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"
    GOOGLE = "google"            # Gemini
    MISTRAL = "mistral"
    LOCAL = "local"              # Generic local models (e.g., llama.cpp, vLLM)
    CUSTOM = "custom"            # For user-defined or niche providers


class LLMMessage(BaseModel):
    """
    Represents a single message in an LLM conversation.
    Strictly validated to ensure data integrity before sending to providers.
    """
    role: Literal["system", "user", "assistant", "tool"] = Field(
        ..., 
        description="The role of the message author."
    )
    content: str = Field(
        ..., 
        min_length=1, 
        description="The textual content of the message."
    )
    name: str | None = Field(
        default=None, 
        description="Optional name of the author (useful for multi-agent tracking)."
    )
    tool_call_id: str | None = Field(
        default=None, 
        description="Optional ID if this message is a response to a tool call."
    )


class LLMResponse(BaseModel):
    """
    Represents the structured response from an LLM provider.
    Normalizes outputs from different providers into a unified format.
    """
    content: str = Field(
        ..., 
        min_length=1, 
        description="The primary textual response from the model."
    )
    model: str = Field(
        ..., 
        description="The specific model identifier that generated the response."
    )
    provider: ProviderType = Field(
        ..., 
        description="The provider type that processed the request."
    )
    usage: dict[str, int] = Field(
        default_factory=dict, 
        description="Token usage statistics (e.g., prompt_tokens, completion_tokens)."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional provider-specific metadata (finish_reason, agent_id, etc.)."
    )
    is_error: bool = Field(
        default=False, 
        description="Flag indicating if the response represents an error state."
    )


class AgentProfile(BaseModel):
    """
    Configuration profile for a specific LLM agent.
    Encapsulates connection details, model selection, and behavioral prompts.
    """
    agent_id: str = Field(
        ..., 
        min_length=1, 
        description="Unique identifier for this agent profile."
    )
    display_name: str = Field(
        ..., 
        min_length=1, 
        description="Human-readable name for the agent."
    )
    provider: ProviderType = Field(
        ..., 
        description="The type of LLM provider this agent connects to."
    )
    model: str = Field(
        ..., 
        min_length=1, 
        description="The specific model name/identifier to use."
    )
    
    # Connection details
    base_url: str | None = Field(
        default=None, 
        description="Custom API endpoint (e.g., http://localhost:11434 for Ollama)."
    )
    api_key: str | None = Field(
        default=None, 
        description="API key or token for authentication (if required)."
    )
    
    # Behavioral configuration
    system_prompt: str = Field(
        default="You are a helpful AI assistant integrated into the GLaDOS daemon.", 
        description="The foundational system prompt defining the agent's persona."
    )
    temperature: float = Field(
        default=0.7, 
        ge=0.0, 
        le=2.0, 
        description="Sampling temperature for generation."
    )
    max_tokens: int | None = Field(
        default=None, 
        gt=0, 
        description="Maximum number of tokens to generate in the response."
    )
    
    # Ecosystem routing
    tags: list[str] = Field(
        default_factory=list, 
        description="Tags for routing (e.g., 'coding', 'analysis', 'fast')."
    )
    is_active: bool = Field(
        default=True, 
        description="Whether this agent profile is currently enabled."
    )