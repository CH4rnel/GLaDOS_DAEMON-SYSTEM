# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Base interfaces for the GLaDOS Platform Adapter subsystem.
Abstracts distro-specific package management and init systems.
"""

from abc import ABC, abstractmethod
from typing import List


class PackageManagerAdapter(ABC):
    """Abstract base class for package manager operations."""

    @abstractmethod
    def install_command(self, packages: List[str]) -> List[str]:
        """Returns the command list to install the given packages."""
        pass

    @abstractmethod
    def remove_command(self, packages: List[str]) -> List[str]:
        """Returns the command list to remove the given packages."""
        pass


class InitSystemAdapter(ABC):
    """Abstract base class for init system operations."""

    @abstractmethod
    def start_service_command(self, service_name: str) -> List[str]:
        """Returns the command list to start a service."""
        pass

    @abstractmethod
    def stop_service_command(self, service_name: str) -> List[str]:
        """Returns the command list to stop a service."""
        pass


class PlatformAdapter(ABC):
    """
    Abstract base class for platform-specific adaptations.
    Pushes all distro-specific assumptions behind this boundary.
    """

    @abstractmethod
    def detect(self) -> bool:
        """
        Checks if this adapter is suitable for the current host environment.
        """
        pass

    @abstractmethod
    def package_manager(self) -> PackageManagerAdapter:
        """Returns the package manager adapter for this platform."""
        pass

    @abstractmethod
    def init_system(self) -> InitSystemAdapter:
        """Returns the init system adapter for this platform."""
        pass