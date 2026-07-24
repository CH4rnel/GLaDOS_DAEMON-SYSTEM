from arch4n.core.config import ConfigLoader
from arch4n.core.logger import setup_logger


class ARCH4NAgent:

    def __init__(self):

        self.logger = setup_logger()

        self.config = ConfigLoader()

        self.identity = (
            self.config.load_identity()
        )


    def introduce(self):

        name = (
            self.identity["name"]
        )

        purpose = (
            self.identity["purpose"]
        )

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
