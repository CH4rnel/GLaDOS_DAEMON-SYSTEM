# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Arch Linux Platform Adapter.
Provides pacman/AUR package management and systemd init system integration.
"""

import shutil
from typing import List

from glados.platform.base import PlatformAdapter, PackageManagerAdapter, InitSystemAdapter


class PacmanPackageManager(PackageManagerAdapter):
    """Package manager adapter for Arch Linux's pacman."""

    def install_command(self, packages: List[str]) -> List[str]:
        """Returns pacman install command with --noconfirm for automation."""
        return ["sudo", "pacman", "-S", "--noconfirm"] + packages

    def remove_command(self, packages: List[str]) -> List[str]:
        """Returns pacman remove command."""
        return ["sudo", "pacman", "-R", "--noconfirm"] + packages


class SystemdInitSystem(InitSystemAdapter):
    """Init system adapter for systemd."""

    def start_service_command(self, service_name: str) -> List[str]:
        """Returns systemctl start command."""
        return ["sudo", "systemctl", "start", service_name]

    def stop_service_command(self, service_name: str) -> List[str]:
        """Returns systemctl stop command."""
        return ["sudo", "systemctl", "stop", service_name]


class ArchAdapter(PlatformAdapter):
    """Platform adapter for Arch Linux and Arch-based distributions."""

    def detect(self) -> bool:
        """Checks if pacman is available on the system."""
        return shutil.which("pacman") is not None

    def package_manager(self) -> PackageManagerAdapter:
        """Returns pacman-based package manager."""
        return PacmanPackageManager()

    def init_system(self) -> InitSystemAdapter:
        """Returns systemd init system (Arch default)."""
        return SystemdInitSystem()