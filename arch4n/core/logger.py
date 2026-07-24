from loguru import logger
import sys


def setup_logger():

    logger.remove()

    logger.add(
        sys.stdout,
        level="INFO"
    )

    logger.add(
        "logs/arch4n.log",
        rotation="10 MB",
        retention="10 days"
    )

    return logger
