# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Ubuntu Platform Adapter.
Provides apt package management with snap support and systemd init system integration.
"""

import shutil
from typing import List

from glados.platform.base import PlatformAdapter, PackageManagerAdapter, InitSystemAdapter
from glados.platform.debian import AptPackageManager, SystemdInitSystem


class UbuntuPackageManager(AptPackageManager):
    """Package manager adapter for Ubuntu with snap support."""

    def install_command(self, packages: List[str]) -> List[str]:
        """Returns apt-get install command (snap handled separately if needed)."""
        return super().install_command(packages)

    def install_snap_command(self, packages: List[str]) -> List[str]:
        """Returns snap install command for Ubuntu-specific packages."""
        return ["sudo", "snap", "install"] + packages


class UbuntuAdapter(PlatformAdapter):
    """Platform adapter for Ubuntu and Ubuntu-based distributions."""

    def detect(self) -> bool:
        """Checks if apt-get is available on the system."""
        return shutil.which("apt-get") is not None

    def package_manager(self) -> PackageManagerAdapter:
        """Returns apt-based package manager with snap support."""
        return UbuntuPackageManager()

    def init_system(self) -> InitSystemAdapter:
        """Returns systemd init system (Ubuntu default)."""
        return SystemdInitSystem()

    def has_snap_support(self) -> bool:
        """Checks if snap is available on the system."""
        return shutil.which("snap") is not None