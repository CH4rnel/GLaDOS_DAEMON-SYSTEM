from glados.config.loader import ConfigLoader
from glados.utils.logger import setup_logger
from glados.core.identity import Identity

from glados.config.loader import ConfigLoader
from glados.utils.logger import setup_logger
from glados.core.identity import Identity


class GLaDOSAgent:
    """
    Core runtime object of the GLaDOS system.
    Responsible only for orchestration.
    """

    def __init__(self):
        self.logger = setup_logger()

        self.config = ConfigLoader()

        self.identity: Identity = (
            self.config.load_identity()
        )

    def introduce(self) -> None:
        """
        Displays startup banner.
        """

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

    def status(self) -> None:
        """
        Prints current runtime information.
        """

        print(
            f"""
Agent:
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

Mode:
{self.identity.system["mode"]}
"""
        )
