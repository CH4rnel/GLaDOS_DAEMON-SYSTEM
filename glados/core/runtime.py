# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

from dataclasses import dataclass

from glados.core.identity import Identity
from loguru import Logger


@dataclass(slots=True)
class RuntimeContext:
    """
    Global runtime context of GLaDOS.

    Every subsystem receives only RuntimeContext.
    """

    identity: Identity
    logger: Logger
