# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Fedora Platform Adapter.
Provides dnf package management and systemd init system integration.
"""

import shutil
from typing import List

from glados.platform.base import PlatformAdapter, PackageManagerAdapter, InitSystemAdapter


class DnfPackageManager(PackageManagerAdapter):
    """Package manager adapter for Fedora's dnf."""

    def install_command(self, packages: List[str]) -> List[str]:
        """Returns dnf install command with -y for automation."""
        return ["sudo", "dnf", "install", "-y"] + packages

    def remove_command(self, packages: List[str]) -> List[str]:
        """Returns dnf remove command."""
        return ["sudo", "dnf", "remove", "-y"] + packages


class SystemdInitSystem(InitSystemAdapter):
    """Init system adapter for systemd."""

    def start_service_command(self, service_name: str) -> List[str]:
        """Returns systemctl start command."""
        return ["sudo", "systemctl", "start", service_name]

    def stop_service_command(self, service_name: str) -> List[str]:
        """Returns systemctl stop command."""
        return ["sudo", "systemctl", "stop", service_name]


class FedoraAdapter(PlatformAdapter):
    """Platform adapter for Fedora and Fedora-based distributions."""

    def detect(self) -> bool:
        """Checks if dnf is available on the system."""
        return shutil.which("dnf") is not None

    def package_manager(self) -> PackageManagerAdapter:
        """Returns dnf-based package manager."""
        return DnfPackageManager()

    def init_system(self) -> InitSystemAdapter:
        """Returns systemd init system (Fedora default)."""
        return SystemdInitSystem()