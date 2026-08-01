# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

from pathlib import Path

import yaml

from glados.core.identity import Identity


BASE_DIR = Path(__file__).resolve().parents[2]


class ConfigLoader:
    """
    Loads configuration files.
    """

    def __init__(self):
        self.config_dir = BASE_DIR / "configs"

    def load_identity(self) -> Identity:
        identity_file = self.config_dir / "identity.yaml"

        with identity_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = yaml.safe_load(file)

        return Identity(**data)
