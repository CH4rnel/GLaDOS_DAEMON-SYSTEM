# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Bootstrap loader for GLaDOS agent configuration.
Reads configs/agents.yaml, resolves API keys from environment variables,
constructs AgentProfile objects, and registers providers in LLMRegistry.

This module is the single entry point for wiring up the multi-agent fleet
at daemon startup. It keeps the composition root clean and testable.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from loguru import logger
from pydantic import SecretStr

from glados.llm.factory import LLMProviderFactory
from glados.llm.models import AgentProfile, ProviderType
from glados.llm.registry import LLMRegistry


class AgentsBootstrap:
    """
    Handles loading and registration of agent profiles from YAML configuration.
    Follows the principle of explicit configuration over implicit defaults.
    """

    @staticmethod
    def load_profiles(config_path: Path) -> list[AgentProfile]:
        """
        Loads agent profiles from a YAML configuration file.
        Resolves api_key_env references to actual SecretStr values from environment.

        :param config_path: Path to the agents.yaml configuration file.
        :return: List of validated AgentProfile objects.
        :raises ValueError: If a required API key environment variable is missing.
        :raises FileNotFoundError: If the configuration file does not exist.
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

        logger.info(f"Loaded {len(profiles)} agent profiles from {config_path}")
        return profiles

    @staticmethod
    def _build_profile(agent_data: dict[str, Any]) -> AgentProfile:
        """
        Builds a single AgentProfile from raw YAML data.
        Resolves api_key_env to SecretStr from environment variables.

        :param agent_data: Raw dictionary from YAML.
        :return: Validated AgentProfile.
        :raises ValueError: If required api_key_env variable is not set.
        """
        api_key: SecretStr | None = None
        api_key_env = agent_data.get("api_key_env")

        if api_key_env:
            env_value = os.environ.get(api_key_env)
            if not env_value:
                raise ValueError(
                    f"Agent '{agent_data.get('agent_id')}' requires environment "
                    f"variable '{api_key_env}', but it is not set."
                )
            api_key = SecretStr(env_value)

        return AgentProfile(
            agent_id=agent_data["agent_id"],
            display_name=agent_data.get("display_name", agent_data["agent_id"]),
            provider=ProviderType(agent_data["provider"]),
            model=agent_data["model"],
            base_url=agent_data.get("base_url"),
            api_key=api_key,
            system_prompt=agent_data.get("system_prompt", ""),
            temperature=agent_data.get("temperature", 0.7),
            max_tokens=agent_data.get("max_tokens"),
            tags=agent_data.get("tags", []),
            is_active=agent_data.get("is_active", True),
        )

    @staticmethod
    def register_profiles(config_path: Path, registry: LLMRegistry) -> None:
        """
        Loads profiles from config and registers each with its corresponding
        LLM provider in the LLMRegistry.

        :param config_path: Path to the agents.yaml configuration file.
        :param registry: The LLMRegistry instance to populate.
        """
        profiles = AgentsBootstrap.load_profiles(config_path)

        for profile in profiles:
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