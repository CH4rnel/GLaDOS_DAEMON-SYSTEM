# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Bootstrap loader for GLaDOS agent configuration.
Reads configs/agents.yaml, resolves environment variables (${VAR_NAME}),
constructs AgentProfile objects, and registers providers in LLMRegistry.
"""

import os
import re
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv
from loguru import logger
from pydantic import SecretStr

from glados.llm.base import BaseLLMProvider
from glados.llm.factory import LLMProviderFactory
from glados.llm.models import AgentProfile, ProviderType
from glados.llm.registry import LLMRegistry


# Load .env file at module import time
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class AgentsBootstrap:
    """
    Handles loading and registration of agent profiles from YAML configuration.
    """

    @staticmethod
    def _resolve_env_var(value: str | None) -> str | None:
        """Resolves ${VAR_NAME} syntax from environment variables."""
        if not value:
            return None
        match = re.match(r"^\$\{(.+)\}$", str(value).strip())
        if match:
            env_var = match.group(1)
            resolved = os.environ.get(env_var)
            if resolved is None:
                logger.warning(f"Environment variable '{env_var}' is not set. Value will be None.")
            return resolved
        return str(value)

    @staticmethod
    def load_profiles(config_path: Path) -> list[AgentProfile]:
        """
        Loads agent profiles from a YAML configuration file.
        Resolves ${VAR} references. Marks agents as inactive if required API keys are missing.
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Agent configuration not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        agents_data = data.get("agents", [])
        profiles: list[AgentProfile] = []

        for agent_data in agents_data:
            profile = AgentsBootstrap._build_profile(agent_data)
            profiles.append(profile)

        active_count = sum(1 for p in profiles if p.is_active)
        logger.info(f"Loaded {len(profiles)} agent profiles ({active_count} active) from {config_path}")
        return profiles

    @staticmethod
    def _build_profile(agent_data: dict[str, Any]) -> AgentProfile:
        """Builds a single AgentProfile from raw YAML data."""
        api_key_raw = agent_data.get("api_key")
        api_key: Optional[SecretStr] = None
        is_active = True
        
        if api_key_raw:
            resolved_key = AgentsBootstrap._resolve_env_var(api_key_raw)
            if resolved_key:
                api_key = SecretStr(resolved_key)
            else:
                logger.warning(f"Agent '{agent_data.get('agent_id')}' will be loaded as INACTIVE: required env var is missing.")
                is_active = False
        
        base_url_raw = agent_data.get("base_url")
        base_url = AgentsBootstrap._resolve_env_var(base_url_raw) if base_url_raw else None

        return AgentProfile(
            agent_id=agent_data["agent_id"],
            display_name=agent_data.get("display_name", agent_data["agent_id"]),
            provider=ProviderType(agent_data["provider"]),
            model=agent_data["model"],
            base_url=base_url,
            api_key=api_key,
            system_prompt=agent_data.get("system_prompt", ""),
            temperature=agent_data.get("temperature", 0.7),
            max_tokens=agent_data.get("max_tokens"),
            tags=agent_data.get("tags", []),
            is_active=is_active,
        )

    @staticmethod
    def register_profiles(config_path: Path, registry: LLMRegistry) -> None:
        """
        Loads profiles from config and registers each with its corresponding
        LLM provider in the LLMRegistry. Inactive agents are registered without a provider.
        """
        profiles = AgentsBootstrap.load_profiles(config_path)

        for profile in profiles:
            if not profile.is_active:
                registry.register(profile, provider=None)
                continue
            
            try:
                provider = LLMProviderFactory.create_provider(profile)
                registry.register(profile, provider)
                logger.info(
                    f"Registered agent '{profile.agent_id}' "
                    f"(provider={profile.provider.value}, model={profile.model})"
                )
            except ValueError as e:
                logger.error(f"Failed to register agent '{profile.agent_id}': {e}")
                raise