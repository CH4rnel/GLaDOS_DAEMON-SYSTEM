# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Core runtime object for GLaDOS_DAEMON-SYSTEM.
Orchestrates initialization of all major subsystems.
"""

from pathlib import Path

from glados.brain.engine import BrainEngine
from glados.config.loader import ConfigLoader
from glados.core.context import RuntimeContext
from glados.core.identity import Identity
from glados.memory.manager import MemoryManager
from glados.utils.logger import setup_logger


class GLaDOSAgent:
    """
    Core runtime object.
    Acts as the root composition container for the GLaDOS daemon.
    """

    def __init__(self) -> None:
        # 1. Initialize logging
        self.logger = setup_logger()

        # 2. Load configuration and identity
        self.config = ConfigLoader()
        self.identity: Identity = self.config.load_identity()

        # 3. Initialize Memory Subsystem (Phase 3)
        # Using a default path in the project root 'data' directory
        memory_path = Path("data/omnissiah_memory.json")
        self.memory = MemoryManager(
            stm_max_size=50,
            ltm_path=memory_path
        )

        # 4. Build Runtime Context with all core dependencies
        self.ctx = RuntimeContext(
            identity=self.identity,
            logger=self.logger,
            memory=self.memory,
        )

        # 5. Initialize Brain Engine (Phase 2)
        self.brain = BrainEngine(self.ctx)

        self.logger.debug("GLaDOSAgent core subsystems initialized successfully.")

    def introduce(self) -> None:
        """
        Prints the startup banner and logs the initialization.
        """
        self.logger.info(f"{self.identity.name} initialized")

        # Using .get() for safe dictionary access to prevent KeyError
        owner_user = self.identity.owner.get("username", "Unknown")
        owner_env = self.identity.owner.get("environment", "Unknown")

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

Status:
ONLINE

========================================
"""
        )