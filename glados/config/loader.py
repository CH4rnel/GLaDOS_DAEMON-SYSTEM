from pathlib import Path

import yaml

from glados.core.identity import Identity


BASE_DIR = Path(__file__).resolve().parents[2]


class ConfigLoader:
    """
    Loads GLaDOS configuration files.

    Responsible only for reading configuration data and converting
    it into strongly typed runtime objects.
    """

    def __init__(self) -> None:
        self.config_dir = BASE_DIR / "configs"

    def load_identity(self) -> Identity:
        """
        Load the identity configuration.

        Returns:
            Identity: Runtime identity object.
        """

        identity_file = self.config_dir / "identity.yaml"

        with open(
            identity_file,
            "r",
            encoding="utf-8",
        ) as file:

            data = yaml.safe_load(file)

        return Identity(**data)
