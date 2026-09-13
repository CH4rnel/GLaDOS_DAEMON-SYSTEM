# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
LLM Router for GLaDOS_DAEMON-SYSTEM.
Responsible for routing tasks to appropriate agents based on strategies.
"""

import asyncio
from enum import Enum
from typing import Any

from loguru import logger

from glados.llm.base import BaseLLMProvider
from glados.llm.models import AgentProfile, LLMMessage, LLMResponse, ProviderType
from glados.llm.registry import LLMRegistry


class RoutingStrategy(str, Enum):
    """
    Enumeration of routing strategies.
    """
    SINGLE = "single"           # Route to one agent
    PARALLEL = "parallel"       # Route to multiple agents in parallel
    CONSENSUS = "consensus"     # Route to multiple agents and reach consensus


class LLMRouter:
    """
    Routes tasks to appropriate LLM agents based on strategies.
    Supports Single, Parallel, and Consensus routing patterns.
    """

    def __init__(self, registry: LLMRegistry) -> None:
        """
        Initialize the router with an agent registry.
        
        :param registry: Registry containing agent profiles.
        """
        self.registry = registry
        self.providers: dict[ProviderType, BaseLLMProvider] = {}
        self.logger = logger.bind(component="LLMRouter")

    def register_provider(self, provider_type: ProviderType, provider: BaseLLMProvider) -> None:
        """
        Register a provider implementation for a provider type.
        
        :param provider_type: The type of provider (e.g., OLLAMA, OPENAI).
        :param provider: The provider implementation.
        """
        self.providers[provider_type] = provider
        self.logger.info(f"Registered provider for {provider_type.value}")

    def get_provider(self, provider_type: ProviderType) -> BaseLLMProvider:
        """
        Get the provider implementation for a provider type.
        
        :param provider_type: The type of provider.
        :return: The provider implementation.
        :raises ValueError: If no provider is registered for the type.
        """
        if provider_type not in self.providers:
            raise ValueError(f"No provider registered for {provider_type.value}")
        return self.providers[provider_type]

    async def route(
        self,
        messages: list[LLMMessage],
        strategy: RoutingStrategy = RoutingStrategy.SINGLE,
        agent_id: str | None = None,
        agent_ids: list[str] | None = None,
        tag: str | None = None,
        **kwargs: Any
    ) -> LLMResponse | list[LLMResponse]:
        """
        Route messages to agents based on the specified strategy.
        
        :param messages: List of conversation messages.
        :param strategy: Routing strategy (SINGLE, PARALLEL, CONSENSUS).
        :param agent_id: Specific agent ID to route to (for SINGLE strategy).
        :param agent_ids: List of agent IDs to route to (for PARALLEL/CONSENSUS).
        :param tag: Tag to filter agents by (alternative to agent_id/agent_ids).
        :param kwargs: Additional strategy-specific parameters.
        :return: Single LLMResponse or list of LLMResponses.
        :raises ValueError: If no agents found or invalid parameters.
        """
        # Determine target agents
        agents = self._resolve_agents(agent_id, agent_ids, tag)
        
        if not agents:
            raise ValueError("No agents found matching the criteria")
        
        # Route based on strategy
        if strategy == RoutingStrategy.SINGLE:
            return await self._route_single(messages, agents[0])
        elif strategy == RoutingStrategy.PARALLEL:
            return await self._route_parallel(messages, agents)
        elif strategy == RoutingStrategy.CONSENSUS:
            return await self._route_consensus(messages, agents, **kwargs)
        else:
            raise ValueError(f"Unknown routing strategy: {strategy}")

    async def route_by_tag(
        self,
        messages: list[LLMMessage],
        tag: str,
        strategy: RoutingStrategy = RoutingStrategy.PARALLEL,
        **kwargs: Any
    ) -> list[LLMResponse]:
        """
        Convenience method to route to agents by tag.
        
        :param messages: List of conversation messages.
        :param tag: Tag to filter agents by.
        :param strategy: Routing strategy.
        :param kwargs: Additional strategy-specific parameters.
        :return: List of LLMResponses.
        """
        result = await self.route(
            messages=messages,
            strategy=strategy,
            tag=tag,
            **kwargs
        )
        
        # Ensure we always return a list
        if isinstance(result, LLMResponse):
            return [result]
        return result

    def _resolve_agents(
        self,
        agent_id: str | None,
        agent_ids: list[str] | None,
        tag: str | None
    ) -> list[AgentProfile]:
        """
        Resolve target agents based on provided criteria.
        
        :param agent_id: Specific agent ID.
        :param agent_ids: List of agent IDs.
        :param tag: Tag to filter by.
        :return: List of matching agent profiles.
        """
        agents = []
        
        if agent_id:
            try:
                agents.append(self.registry.get(agent_id))
            except Exception as e:
                self.logger.warning(f"Failed to get agent {agent_id}: {e}")
        elif agent_ids:
            for aid in agent_ids:
                try:
                    agents.append(self.registry.get(aid))
                except Exception as e:
                    self.logger.warning(f"Failed to get agent {aid}: {e}")
        elif tag:
            agents = self.registry.get_by_tag(tag)
        else:
            # Default to all active agents
            agents = self.registry.get_active()
        
        # Filter to only active agents
        agents = [a for a in agents if a.is_active]
        
        return agents

    async def _route_single(
        self,
        messages: list[LLMMessage],
        agent: AgentProfile
    ) -> LLMResponse:
        """
        Route to a single agent.
        
        :param messages: List of conversation messages.
        :param agent: Target agent profile.
        :return: LLMResponse from the agent.
        """
        self.logger.debug(f"Routing SINGLE to agent: {agent.agent_id}")
        
        # Enrich messages with system prompt
        enriched_messages = self._enrich_with_system_prompt(messages, agent)
        
        # Get provider and execute
        provider = self.get_provider(agent.provider)
        return await provider.complete(enriched_messages, agent)

    async def _route_parallel(
        self,
        messages: list[LLMMessage],
        agents: list[AgentProfile]
    ) -> list[LLMResponse]:
        """
        Route to multiple agents in parallel.
        
        :param messages: List of conversation messages.
        :param agents: List of target agent profiles.
        :return: List of LLMResponses from all agents.
        """
        self.logger.debug(f"Routing PARALLEL to {len(agents)} agents")
        
        # Create tasks for all agents
        tasks = [
            self._route_single(messages, agent)
            for agent in agents
        ]
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Agent {agents[i].agent_id} failed: {result}")
            else:
                valid_results.append(result)
        
        return valid_results

    async def _route_consensus(
        self,
        messages: list[LLMMessage],
        agents: list[AgentProfile],
        **kwargs: Any
    ) -> LLMResponse:
        """
        Route to multiple agents and reach consensus.
        Currently returns the first successful response.
        Future: Implement voting/consensus algorithm.
        
        :param messages: List of conversation messages.
        :param agents: List of target agent profiles.
        :param kwargs: Additional parameters for consensus algorithm.
        :return: Consensus LLMResponse.
        """
        self.logger.debug(f"Routing CONSENSUS to {len(agents)} agents")
        
        # Get responses from all agents
        responses = await self._route_parallel(messages, agents)
        
        if not responses:
            raise ValueError("No successful responses from agents")
        
        # Simple consensus: return first response
        # TODO: Implement sophisticated consensus algorithm
        return responses[0]

    def _enrich_with_system_prompt(
        self,
        messages: list[LLMMessage],
        agent: AgentProfile
    ) -> list[LLMMessage]:
        """
        Enrich messages with system prompt from agent profile.
        
        :param messages: Original messages.
        :param agent: Agent profile with system prompt.
        :return: Enriched messages with system prompt prepended.
        """
        if not agent.system_prompt:
            return messages
        
        # Prepend system prompt
        system_message = LLMMessage(
            role="system",
            content=agent.system_prompt
        )
        
        return [system_message] + list(messages)