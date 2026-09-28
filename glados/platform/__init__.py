# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
GLaDOS Platform Adapter subsystem.
Provides distro-agnostic abstraction for package management and init systems.
"""

from glados.platform.base import PlatformAdapter, PackageManagerAdapter, InitSystemAdapter
from glados.platform.arch import ArchAdapter
from glados.platform.debian import DebianAdapter
from glados.platform.ubuntu import UbuntuAdapter
from glados.platform.pop_os import PopOSAdapter
from glados.platform.fedora import FedoraAdapter
from glados.platform.mint import MintAdapter
from glados.platform.generic import GenericAdapter

__all__ = [
    "PlatformAdapter",
    "PackageManagerAdapter",
    "InitSystemAdapter",
    "ArchAdapter",
    "DebianAdapter",
    "UbuntuAdapter",
    "PopOSAdapter",
    "FedoraAdapter",
    "MintAdapter",
    "GenericAdapter",
]