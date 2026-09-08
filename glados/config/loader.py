# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Configuration loader for GLaDOS_DAEMON-SYSTEM.
Responsible for reading YAML configuration files and environment variables.
"""

import os
import re
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

from glados.core.identity import Identity
from glados.llm.models import AgentProfile


class ConfigLoader:
    """
    Loads configuration from YAML files and environment variables.
    Supports environment variable substitution using ${VAR_NAME} syntax.
    """

    def __init__(self, config_dir: Path | str = "configs") -> None:
        """
        Initialize the configuration loader.
        
        :param config_dir: Directory containing configuration files.
        """
        self.config_dir = Path(config_dir)
        self.logger = logger.bind(component="ConfigLoader")

    def load_identity(self) -> Identity:
        """
        Load the Identity configuration from configs/identity.yaml.
        
        :return: Identity object.
        :raises FileNotFoundError: If identity.yaml is missing.
        """
        identity_path = self.config_dir / "identity.yaml"
        
        if not identity_path.exists():
            raise FileNotFoundError(f"Identity configuration not found: {identity_path}")
        
        data = self._load_yaml(identity_path)
        return Identity(**data)

    def load_agent_profiles(self) -> list[AgentProfile]:
        """
        Load agent profiles from configs/agents.yaml.
        Supports environment variable substitution using ${VAR_NAME} syntax.
        
        :return: List of AgentProfile objects.
        :raises ValueError: If required environment variables are missing.
        """
        agents_path = self.config_dir / "agents.yaml"
        
        if not agents_path.exists():
            self.logger.warning(f"Agent profiles file not found: {agents_path}. Returning empty list.")
            return []
        
        data = self._load_yaml(agents_path)
        agents_data = data.get("agents", [])
        
        profiles = []
        for agent_data in agents_data:
            # Substitute environment variables
            substituted_data = self._substitute_env_vars(agent_data)
            
            # Validate and create AgentProfile
            try:
                profile = AgentProfile(**substituted_data)
                profiles.append(profile)
                self.logger.debug(f"Loaded agent profile: {profile.agent_id}")
            except Exception as e:
                self.logger.error(f"Failed to validate agent profile: {e}")
                raise
        
        self.logger.info(f"Loaded {len(profiles)} agent profiles from {agents_path}")
        return profiles

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """
        Load and parse a YAML file.
        
        :param path: Path to the YAML file.
        :return: Parsed dictionary.
        :raises yaml.YAMLError: If YAML is invalid.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse YAML file {path}: {e}")
            raise

    def _substitute_env_vars(self, data: Any) -> Any:
        """
        Recursively substitute environment variables in the data structure.
        Looks for patterns like ${VAR_NAME} and replaces them with os.environ[VAR_NAME].
        
        :param data: Data structure (dict, list, str, etc.).
        :return: Data with substituted values.
        :raises ValueError: If a referenced environment variable is not found.
        """
        if isinstance(data, dict):
            return {k: self._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        elif isinstance(data, str):
            # Find all ${VAR_NAME} patterns
            pattern = r"\$\{([^}]+)\}"
            matches = re.findall(pattern, data)
            
            result = data
            for var_name in matches:
                if var_name not in os.environ:
                    raise ValueError(f"Environment variable '{var_name}' not found. "
                                   f"Please set it in your .env file or system environment.")
                result = result.replace(f"${{{var_name}}}", os.environ[var_name])
            
            return result
        else:
            return data