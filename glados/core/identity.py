# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

from dataclasses import dataclass


@dataclass(slots=True)
class Identity:
    name: str
    codename: str
    version: str

    owner: dict
    system: dict

    purpose: str

    personality: dict

    principles: list[str]
