# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Generic Platform Adapter.
POSIX-compliant fallback for unknown or minimal distributions.
Dynamically detects init system (systemd, s6-rc, openrc) and package manager
(pacman, apt-get, dnf, zypper, apk) by probing $PATH at runtime.

Design principles:
- Never assumes a specific distro; probes the environment instead.
- Init system and package manager are independent axes (§6 of the design doc).
- Fails safe: if no real package manager is found, falls back to an echo-based
  stub that logs what *would* be installed, rather than silently doing nothing
  or invoking a wrong tool.
"""

import shutil
from typing import List

from loguru import logger

from glados.platform.base import PlatformAdapter, PackageManagerAdapter, InitSystemAdapter


# ---------------------------------------------------------------------------
# Package manager adapters
# ---------------------------------------------------------------------------

class EchoPackageManager(PackageManagerAdapter):
    """
    Safe fallback package manager.
    Emits the command that *would* be run instead of executing it.
    Used when no recognized package manager is found on $PATH.
    """

    def __init__(self) -> None:
        self.logger = logger.bind(component="EchoPackageManager")

    def install_command(self, packages: List[str]) -> List[str]:
        self.logger.warning(
            f"No recognized package manager found. "
            f"Would install: {' '.join(packages)}"
        )
        return ["echo", "[fallback] would install:", *packages]

    def remove_command(self, packages: List[str]) -> List[str]:
        self.logger.warning(
            f"No recognized package manager found. "
            f"Would remove: {' '.join(packages)}"
        )
        return ["echo", "[fallback] would remove:", *packages]


class PacmanPackageManager(PackageManagerAdapter):
    """Fallback wrapper for pacman when detected on a non-Arch system."""

    def install_command(self, packages: List[str]) -> List[str]:
        return ["sudo", "pacman", "-S", "--noconfirm"] + packages

    def remove_command(self, packages: List[str]) -> List[str]:
        return ["sudo", "pacman", "-R", "--noconfirm"] + packages


class AptPackageManager(PackageManagerAdapter):
    """Fallback wrapper for apt-get when detected on a non-Debian system."""

    def install_command(self, packages: List[str]) -> List[str]:
        return ["sudo", "apt-get", "install", "-y"] + packages

    def remove_command(self, packages: List[str]) -> List[str]:
        return ["sudo", "apt-get", "remove", "-y"] + packages


class DnfPackageManager(PackageManagerAdapter):
    """Fallback wrapper for dnf when detected on a non-Fedora system."""

    def install_command(self, packages: List[str]) -> List[str]:
        return ["sudo", "dnf", "install", "-y"] + packages

    def remove_command(self, packages: List[str]) -> List[str]:
        return ["sudo", "dnf", "remove", "-y"] + packages


class ZypperPackageManager(PackageManagerAdapter):
    """Fallback wrapper for zypper (openSUSE/SLES)."""

    def install_command(self, packages: List[str]) -> List[str]:
        return ["sudo", "zypper", "--non-interactive", "install"] + packages

    def remove_command(self, packages: List[str]) -> List[str]:
        return ["sudo", "zypper", "--non-interactive", "remove"] + packages


class ApkPackageManager(PackageManagerAdapter):
    """Fallback wrapper for apk (Alpine Linux)."""

    def install_command(self, packages: List[str]) -> List[str]:
        return ["sudo", "apk", "add"] + packages

    def remove_command(self, packages: List[str]) -> List[str]:
        return ["sudo", "apk", "del"] + packages


# ---------------------------------------------------------------------------
# Init system adapters
# ---------------------------------------------------------------------------

class SystemdInitSystem(InitSystemAdapter):
    """Init system adapter for systemd."""

    def start_service_command(self, service_name: str) -> List[str]:
        return ["sudo", "systemctl", "start", service_name]

    def stop_service_command(self, service_name: str) -> List[str]:
        return ["sudo", "systemctl", "stop", service_name]


class S6InitSystem(InitSystemAdapter):
    """Init system adapter for s6-rc (used on Artix, Chimera, some embedded targets)."""

    def start_service_command(self, service_name: str) -> List[str]:
        return ["sudo", "s6-rc", "-up", "change", service_name]

    def stop_service_command(self, service_name: str) -> List[str]:
        return ["sudo", "s6-rc", "-down", "change", service_name]


class OpenRCInitSystem(InitSystemAdapter):
    """Init system adapter for OpenRC (used on Alpine, Gentoo, Artix)."""

    def start_service_command(self, service_name: str) -> List[str]:
        return ["sudo", "rc-service", service_name, "start"]

    def stop_service_command(self, service_name: str) -> List[str]:
        return ["sudo", "rc-service", service_name, "stop"]


# ---------------------------------------------------------------------------
# Generic adapter
# ---------------------------------------------------------------------------

class GenericAdapter(PlatformAdapter):
    """
    Generic platform adapter — the last-resort fallback.
    Always reports detect() == True so the bootstrap chain has something
    to land on when no distro-specific adapter matches.

    Probes $PATH at runtime to select the most appropriate package manager
    and init system, in priority order:
      - Package managers: pacman > apt-get > dnf > zypper > apk > echo
      - Init systems:     systemd > s6-rc > openrc > systemd (harmless default)
    """

    # Ordered by specificity / likelihood on generic Linux targets
    _PACKAGE_MANAGER_PROBES: List[tuple[str, type[PackageManagerAdapter]]] = [
        ("pacman", PacmanPackageManager),
        ("apt-get", AptPackageManager),
        ("dnf", DnfPackageManager),
        ("zypper", ZypperPackageManager),
        ("apk", ApkPackageManager),
    ]

    _INIT_SYSTEM_PROBES: List[tuple[str, type[InitSystemAdapter]]] = [
        ("systemctl", SystemdInitSystem),
        ("s6-rc", S6InitSystem),
        ("rc-service", OpenRCInitSystem),
    ]

    def __init__(self) -> None:
        self.logger = logger.bind(component="GenericAdapter")

    def detect(self) -> bool:
        """Generic adapter always detects as True — it is the universal fallback."""
        return True

    def package_manager(self) -> PackageManagerAdapter:
        """
        Probes $PATH for a recognized package manager and returns the
        matching adapter. Falls back to EchoPackageManager if none is found.
        """
        for binary, adapter_cls in self._PACKAGE_MANAGER_PROBES:
            if shutil.which(binary) is not None:
                self.logger.debug(f"GenericAdapter: detected package manager '{binary}'")
                return adapter_cls()

        self.logger.warning(
            "GenericAdapter: no recognized package manager found on $PATH. "
            "Using EchoPackageManager (no-op fallback)."
        )
        return EchoPackageManager()

    def init_system(self) -> InitSystemAdapter:
        """
        Probes $PATH for a recognized init system and returns the
        matching adapter. Falls back to SystemdInitSystem as a safe default
        (its commands will simply fail with a clear error if systemd is absent).
        """
        for binary, adapter_cls in self._INIT_SYSTEM_PROBES:
            if shutil.which(binary) is not None:
                self.logger.debug(f"GenericAdapter: detected init system '{binary}'")
                return adapter_cls()

        self.logger.warning(
            "GenericAdapter: no recognized init system found on $PATH. "
            "Falling back to SystemdInitSystem."
        )
        return SystemdInitSystem()