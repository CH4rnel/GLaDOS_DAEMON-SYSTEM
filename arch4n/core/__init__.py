from pathlib import Path
import yaml


BASE_DIR = Path(__file__).resolve().parents[2]


class ConfigLoader:
    """
    Загружает конфигурацию ARCH4N.

    Отвечает только за чтение настроек.
    Не содержит бизнес-логики.
    """

    def __init__(self):
        self.config_dir = BASE_DIR / "configs"


    def load_identity(self) -> dict:
        """
        Загружает identity.yaml
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
