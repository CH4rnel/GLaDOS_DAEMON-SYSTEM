# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

from glados.brain import BrainEngine
from glados.config.loader import ConfigLoader
from glados.core.context import RuntimeContext
from glados.core.identity import Identity
from glados.utils.logger import setup_logger


class GLaDOSAgent:
    """
    Core runtime object.
    """

    def __init__(self):
        self.logger = setup_logger()

        self.config = ConfigLoader()

        self.identity: Identity = (
            self.config.load_identity()
        )

        self.ctx = RuntimeContext(
            identity=self.identity,
            logger=self.logger,
        )

        self.brain = BrainEngine(self.ctx)

    def introduce(self):

        self.logger.info(
            f"{self.identity.name} initialized"
        )

        print(
            f"""
========================================

{self.identity.name}

Codename:
{self.identity.codename}

Version:
{self.identity.version}

Owner:
{self.identity.owner["username"]}

Environment:
{self.identity.owner["environment"]}

Purpose:
{self.identity.purpose}

Status:
ONLINE

========================================
"""
        )
