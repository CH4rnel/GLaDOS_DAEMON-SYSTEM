# glados/core/agent.py
# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Core runtime object for GLaDOS_DAEMON-SYSTEM.
Orchestrates initialization of all major subsystems.
"""

from pathlib import Path

from dotenv import load_dotenv

from glados.brain.engine import BrainEngine
from glados.config.loader import ConfigLoader
from glados.core.context import RuntimeContext
from glados.core.identity import Identity
from glados.memory.manager import MemoryManager
from glados.skills.registry import SkillRegistry
from glados.skills.loader import SkillLoader
from glados.tools.registry import ToolRegistry
from glados.tools.loader import ToolLoader
from glados.llm.registry import LLMRegistry
from glados.llm.router import LLMRouter
from glados.llm.models import ProviderType
from glados.llm.providers.ollama import OllamaProvider
from glados.llm.providers.openai import OpenAIProvider
from glados.security import GuardianGate, SecurityPolicy
from glados.utils.logger import setup_logger


class GLaDOSAgent:
    """
    Core runtime object.
    Acts as the root composition container for the GLaDOS daemon.
    """

    def __init__(self) -> None:
        # 0. Load .env into the process environment before anything reads
        #    from it — configs/agents.yaml's ${OPENAI_API_KEY} substitution
        #    and SecurityPolicy's egress_proxy both depend on this having
        #    already run. Previously nothing called load_dotenv() at all,
        #    so .env was silently ignored outside a shell that exported it.
        load_dotenv()

        # 1. Initialize logging
        self.logger = setup_logger()

        # 2. Load configuration and identity
        self.config = ConfigLoader()
        self.identity: Identity = self.config.load_identity()

        # 2b. Load the Guardian security policy (fail-closed by default —
        #     see glados/security/policy.py and configs/security.yaml).
        #     This is what makes configs/identity.yaml's
        #     system.guardian_enabled flag actually do something.
        self.security: SecurityPolicy = self.config.load_security_policy()

        # 3. Initialize Memory Subsystem (Phase 3)
        memory_path = Path("data/omnissiah_memory.json")
        self.memory = MemoryManager(
            stm_max_size=50,
            ltm_path=memory_path
        )

        # 4. Initialize Skill Subsystem (Phase 4)
        self.skills = SkillRegistry()
        skill_loader = SkillLoader(skills_dir=Path("glados/skills/builtin"))
        skill_loader.load_all(self.skills)

        # 5. Initialize Tool Subsystem (Phase 5)
        self.tools = ToolRegistry()
        tool_loader = ToolLoader(search_path=Path("glados/tools/builtin"))
        tool_loader.load_all(self.tools)

        # 5b. GuardianGate — the single choke point Phase 7's BrainEngine
        #     should dispatch tool calls through (audit logging; actual
        #     policy enforcement happens inside each tool via ctx.security,
        #     see glados/security/policy.py for why it's not centralized
        #     only here).
        self.guardian = GuardianGate(self.tools)

        # 6. Initialize LLM Agent Registry (Phase 6)
        self.llm_agents = LLMRegistry()
        agent_profiles = self.config.load_agent_profiles()
        for profile in agent_profiles:
            try:
                self.llm_agents.register(profile)
            except ValueError as e:
                self.logger.warning(f"Failed to register agent profile: {e}")

        # 7. Initialize LLM Router (Phase 6)
        self.llm_router = LLMRouter(self.llm_agents)

        # Register providers for different provider types
        # In production, these would be configured via config
        self.llm_router.register_provider(
            ProviderType.OLLAMA,
            OllamaProvider()
        )
        self.llm_router.register_provider(
            ProviderType.OPENAI,
            OpenAIProvider()
        )

        # 8. Build Runtime Context with all core dependencies
        self.ctx = RuntimeContext(
            identity=self.identity,
            logger=self.logger,
            memory=self.memory,
            skills=self.skills,
            tools=self.tools,
            llm_agents=self.llm_agents,
            llm_router=self.llm_router,
            security=self.security,
        )

        # 9. Initialize Brain Engine (Phase 2)
        self.brain = BrainEngine(self.ctx)

        self.logger.debug("GLaDOSAgent core subsystems initialized successfully.")

    def introduce(self) -> None:
        """
        Prints the startup banner and logs the initialization.
        """
        self.logger.info(f"{self.identity.name} initialized")

        owner_user = self.identity.owner.get("username", "Unknown")
        owner_env = self.identity.owner.get("environment", "Unknown")

        skills_count = len(self.skills.list_all()) if self.skills else 0
        tools_count = len(self.tools.list_all()) if self.tools else 0
        agents_count = len(self.llm_agents.list_all()) if self.llm_agents else 0
        active_agents_count = len(self.llm_agents.get_active()) if self.llm_agents else 0

        print(
            f"""
========================================

{self.identity.name}

Codename:
{self.identity.codename}

Version:
{self.identity.version}

Owner:
{owner_user}

Environment:
{owner_env}

Purpose:
{self.identity.purpose}

Loaded Skills:
{skills_count}

Loaded Tools:
{tools_count}

Loaded LLM Agents:
{agents_count} ({active_agents_count} active)

Status:
ONLINE

========================================
"""
        )