from pathlib import Path
import yaml


BASE_DIR = Path(__file__).resolve().parents[2]


class ConfigLoader:
    """
	Loads the GLaDOS configuration.
    	Responsible only for reading settings.
   	 Contains no business logic.
    """

    def __init__(self):
        self.config_dir = BASE_DIR / "configs"


    def load_identity(self) -> dict:
        """
        Loads identity.yaml
        """

        identity_file = (
            self.config_dir /
            "identity.yaml"
        )

        with open(
            identity_file,
            "r",
            encoding="utf-8"
        ) as file:

            return yaml.safe_load(file)
