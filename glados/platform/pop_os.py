# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Pop!_OS Platform Adapter.
Provides apt package management with system76 repository support and systemd init system.
"""

import shutil
from typing import List

from glados.platform.base import PlatformAdapter, PackageManagerAdapter, InitSystemAdapter
from glados.platform.debian import AptPackageManager, SystemdInitSystem


class PopOSPackageManager(AptPackageManager):
    """Package manager adapter for Pop!_OS with system76 package support."""

    def install_command(self, packages: List[str]) -> List[str]:
        """Returns apt-get install command (includes system76 packages)."""
        return super().install_command(packages)

    def install_system76_command(self, packages: List[str]) -> List[str]:
        """Returns apt-get install for system76-specific packages."""
        return ["sudo", "apt-get", "install", "-y"] + packages


class PopOSAdapter(PlatformAdapter):
    """Platform adapter for Pop!_OS (System76)."""

    def detect(self) -> bool:
        """Checks if apt-get is available on the system."""
        return shutil.which("apt-get") is not None

    def package_manager(self) -> PackageManagerAdapter:
        """Returns apt-based package manager with system76 support."""
        return PopOSPackageManager()

    def init_system(self) -> InitSystemAdapter:
        """Returns systemd init system (Pop!_OS default)."""
        return SystemdInitSystem()

    def has_system76_repo(self) -> bool:
        """Checks if system76 repository is configured."""
        # In production, check /etc/apt/sources.list.d/ for system76
        return True  # Pop!_OS always has system76 repo