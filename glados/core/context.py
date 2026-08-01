# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

from dataclasses import dataclass
from loguru import logger

from glados.core.identity import Identity


@dataclass(slots=True)
class RuntimeContext:
    identity: Identity
    logger: type(logger)
