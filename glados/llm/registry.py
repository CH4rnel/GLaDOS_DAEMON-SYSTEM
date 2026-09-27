# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
LLM Registry for GLaDOS_DAEMON-SYSTEM.
Centralized storage and retrieval of agent profiles and their providers.
"""

from loguru import logger

from glados.llm.base import BaseLLMProvider
from glados.llm.models import AgentProfile, ProviderType


class AgentNotFoundError(Exception):
    """Raised when a requested agent is not found in the registry."""
    pass


class LLMRegistry:
    """
    Central registry for managing and retrieving agent profiles and providers.
    Provides O(1) access by agent_id and supports filtering by tags and providers.
    """

    def __init__(self) -> None:
        """Initializes the empty agent registry."""
        self._agents: dict[str, AgentProfile] = {}
        self._providers: dict[str, BaseLLMProvider] = {}
        self.logger = logger.bind(component="LLMRegistry")
        self.logger.debug("LLMRegistry initialized.")

    def register(self, profile: AgentProfile, provider: BaseLLMProvider) -> None:
        """
        Registers a new agent profile and its provider in the registry.
        
        :param profile: The agent profile to register.
        :param provider: The instantiated LLM provider for this agent.
        :raises ValueError: If an agent with the same ID is already registered.
        """
        agent_id = profile.agent_id
        
        if agent_id in self._agents:
            raise ValueError(f"Agent with ID '{agent_id}' is already registered.")
        
        self._agents[agent_id] = profile
        self._providers[agent_id] = provider
        self.logger.info(f"Registered agent: {agent_id} ({profile.display_name})")

    def unregister(self, agent_id: str) -> None:
        """
        Removes an agent profile and its provider from the registry.
        
        :param agent_id: The ID of the agent to remove.
        :raises AgentNotFoundError: If the agent is not registered.
        """
        if agent_id not in self._agents:
            raise AgentNotFoundError(f"Agent '{agent_id}' not found in registry.")
        
        del self._agents[agent_id]
        del self._providers[agent_id]
        self.logger.info(f"Unregistered agent: {agent_id}")

    def get(self, agent_id: str) -> AgentProfile:
        """Retrieves an agent profile by its unique ID."""
        if agent_id not in self._agents:
            raise AgentNotFoundError(f"Agent '{agent_id}' not found in registry.")
        return self._agents[agent_id]

    def get_provider(self, agent_id: str) -> BaseLLMProvider:
        """
        Retrieves the LLM provider for a specific agent.
        
        :param agent_id: The ID of the agent.
        :return: The BaseLLMProvider instance.
        :raises AgentNotFoundError: If the agent is not registered.
        """
        if agent_id not in self._providers:
            raise AgentNotFoundError(f"Provider for agent '{agent_id}' not found in registry.")
        return self._providers[agent_id]

    def get_by_tag(self, tag: str) -> list[AgentProfile]:
        """Retrieves all agents that have the specified tag."""
        return [profile for profile in self._agents.values() if tag in profile.tags]

    def get_by_provider(self, provider: ProviderType) -> list[AgentProfile]:
        """Retrieves all agents that use the specified provider."""
        return [profile for profile in self._agents.values() if profile.provider == provider]

    def get_active(self) -> list[AgentProfile]:
        """Retrieves all active agents."""
        return [profile for profile in self._agents.values() if profile.is_active]

    def list_all(self) -> list[AgentProfile]:
        """Returns a list of all registered agent profiles."""
        return list(self._agents.values())