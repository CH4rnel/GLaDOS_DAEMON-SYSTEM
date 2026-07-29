from pathlib import Path
import yaml


BASE_DIR = Path(__file__).resolve().parents[2]


class ConfigLoader:
    """
    Loading configuration GLaDOS.
    """

    def __init__(self):
        self.config_dir = BASE_DIR / "configs"


    def load_identity(self) -> dict:
        """
        loading identity.yaml
        """

        identity_file = self.config_dir / "identity.yaml"

        with open(
            identity_file,
            "r",
            encoding="utf-8"
        ) as file:

            return yaml.safe_load(file)

