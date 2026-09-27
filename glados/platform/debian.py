# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Debian Platform Adapter.
Provides apt/dpkg package management and systemd init system integration.
"""

import shutil
from typing import List

from glados.platform.base import PlatformAdapter, PackageManagerAdapter, InitSystemAdapter


class AptPackageManager(PackageManagerAdapter):
    """Package manager adapter for Debian's apt-get."""

    def install_command(self, packages: List[str]) -> List[str]:
        """Returns apt-get install command with -y for automation."""
        return ["sudo", "apt-get", "install", "-y"] + packages

    def remove_command(self, packages: List[str]) -> List[str]:
        """Returns apt-get remove command."""
        return ["sudo", "apt-get", "remove", "-y"] + packages


class SystemdInitSystem(InitSystemAdapter):
    """Init system adapter for systemd."""

    def start_service_command(self, service_name: str) -> List[str]:
        """Returns systemctl start command."""
        return ["sudo", "systemctl", "start", service_name]

    def stop_service_command(self, service_name: str) -> List[str]:
        """Returns systemctl stop command."""
        return ["sudo", "systemctl", "stop", service_name]


class DebianAdapter(PlatformAdapter):
    """Platform adapter for Debian and Debian-based distributions."""

    def detect(self) -> bool:
        """Checks if apt-get is available on the system."""
        return shutil.which("apt-get") is not None

    def package_manager(self) -> PackageManagerAdapter:
        """Returns apt-based package manager."""
        return AptPackageManager()

    def init_system(self) -> InitSystemAdapter:
        """Returns systemd init system (Debian default)."""
        return SystemdInitSystem()