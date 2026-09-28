# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Linux Mint Platform Adapter.
Provides apt package management and systemd init system integration.
Based on Ubuntu/Debian but with Mint-specific optimizations.
"""

import shutil
from typing import List

from glados.platform.base import PlatformAdapter, PackageManagerAdapter, InitSystemAdapter
from glados.platform.debian import AptPackageManager, SystemdInitSystem


class MintPackageManager(AptPackageManager):
    """Package manager adapter for Linux Mint."""

    def install_command(self, packages: List[str]) -> List[str]:
        """Returns apt-get install command (Mint-optimized)."""
        return super().install_command(packages)


class MintAdapter(PlatformAdapter):
    """Platform adapter for Linux Mint."""

    def detect(self) -> bool:
        """Checks if apt-get is available on the system."""
        return shutil.which("apt-get") is not None

    def package_manager(self) -> PackageManagerAdapter:
        """Returns apt-based package manager (Mint-optimized)."""
        return MintPackageManager()

    def init_system(self) -> InitSystemAdapter:
        """Returns systemd init system (Mint default)."""
        return SystemdInitSystem()