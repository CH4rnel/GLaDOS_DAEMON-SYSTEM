# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
LLM Registry for GLaDOS_DAEMON-SYSTEM.
Centralized storage and retrieval of agent profiles.
"""

from loguru import logger

from glados.llm.models import AgentProfile, ProviderType


class AgentNotFoundError(Exception):
    """Raised when a requested agent is not found in the registry."""
    pass


class LLMRegistry:
    """
    Central registry for managing and retrieving agent profiles.
    Provides O(1) access by agent_id and supports filtering by tags and providers.
    """

    def __init__(self) -> None:
        """Initializes the empty agent registry."""
        self._agents: dict[str, AgentProfile] = {}
        self.logger = logger.bind(component="LLMRegistry")
        self.logger.debug("LLMRegistry initialized.")

    def register(self, profile: AgentProfile) -> None:
        """
        Registers a new agent profile in the registry.
        
        :param profile: The agent profile to register.
        :raises ValueError: If an agent with the same ID is already registered.
        """
        agent_id = profile.agent_id
        
        if agent_id in self._agents:
            raise ValueError(f"Agent with ID '{agent_id}' is already registered.")
        
        self._agents[agent_id] = profile
        self.logger.info(f"Registered agent: {agent_id} ({profile.display_name})")

    def unregister(self, agent_id: str) -> None:
        """
        Removes an agent profile from the registry.
        
        :param agent_id: The ID of the agent to remove.
        :raises AgentNotFoundError: If the agent is not registered.
        """
        if agent_id not in self._agents:
            raise AgentNotFoundError(f"Agent '{agent_id}' not found in registry.")
        
        del self._agents[agent_id]
        self.logger.info(f"Unregistered agent: {agent_id}")

    def get(self, agent_id: str) -> AgentProfile:
        """
        Retrieves an agent profile by its unique ID.
        
        :param agent_id: The ID of the agent.
        :return: The agent profile.
        :raises AgentNotFoundError: If the agent is not registered.
        """
        if agent_id not in self._agents:
            raise AgentNotFoundError(f"Agent '{agent_id}' not found in registry.")
        
        return self._agents[agent_id]

    def get_by_tag(self, tag: str) -> list[AgentProfile]:
        """
        Retrieves all agents that have the specified tag.
        
        :param tag: The tag to search for.
        :return: List of matching agent profiles.
        """
        return [
            profile for profile in self._agents.values()
            if tag in profile.tags
        ]

    def get_by_provider(self, provider: ProviderType) -> list[AgentProfile]:
        """
        Retrieves all agents that use the specified provider.
        
        :param provider: The provider type to search for.
        :return: List of matching agent profiles.
        """
        return [
            profile for profile in self._agents.values()
            if profile.provider == provider
        ]

    def get_active(self) -> list[AgentProfile]:
        """
        Retrieves all active agents.
        
        :return: List of active agent profiles.
        """
        return [
            profile for profile in self._agents.values()
            if profile.is_active
        ]

    def list_all(self) -> list[AgentProfile]:
        """
        Returns a list of all registered agent profiles.
        
        :return: List of all agent profiles.
        """
        return list(self._agents.values())