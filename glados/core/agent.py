from glados.core.config import ConfigLoader
from glados.core.logger import setup_logger


class GLaDOSAgent:

    def __init__(self):
        self.logger = setup_logger()

        self.config = ConfigLoader()

        self.identity = (
            self.config.load_identity()
        )


    def introduce(self):

        name = self.identity["name"]

        purpose = self.identity["purpose"]

        self.logger.info(
            f"{name} initialized"
        )

        print(
            f"""
================================

{name}

Purpose:
{purpose}

Status:
ONLINE

================================
"""
        )
