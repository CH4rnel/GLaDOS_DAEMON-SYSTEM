from dataclasses import dataclass


@dataclass(slots=True)
class Identity:
    """
    Runtime representation of GLaDOS identity.
    """

    name: str
    codename: str
    version: str

    owner: dict
    system: dict

    purpose: str

    personality: dict

    principles: list[str]
