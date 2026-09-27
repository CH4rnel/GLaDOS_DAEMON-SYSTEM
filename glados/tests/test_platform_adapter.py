# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS Platform Adapter subsystem.
Ensures distro-specific operations are correctly abstracted and routed.
"""

import pytest
from unittest.mock import patch

from glados.platform.base import PlatformAdapter, PackageManagerAdapter, InitSystemAdapter
from glados.platform.arch import ArchAdapter
from glados.platform.debian import DebianAdapter
from glados.platform.ubuntu import UbuntuAdapter
from glados.platform.pop_os import PopOSAdapter
from glados.platform.fedora import FedoraAdapter
from glados.platform.mint import MintAdapter
from glados.platform.generic import GenericAdapter


class TestPlatformAdapter:
    """Tests for PlatformAdapter detection and delegation."""

    def test_arch_adapter_detects_pacman(self):
        """Test that ArchAdapter correctly identifies pacman-based systems."""
        with patch("shutil.which", return_value="/usr/bin/pacman"):
            adapter = ArchAdapter()
            assert adapter.detect() is True
            assert isinstance(adapter.package_manager(), PackageManagerAdapter)
            assert "pacman" in adapter.package_manager().install_command(["test-pkg"])

    def test_debian_adapter_detects_apt(self):
        """Test that DebianAdapter correctly identifies apt-based systems."""
        with patch("shutil.which", return_value="/usr/bin/apt-get"):
            adapter = DebianAdapter()
            assert adapter.detect() is True
            assert "apt-get" in adapter.package_manager().install_command(["test-pkg"])

    def test_ubuntu_adapter_detects_apt_and_snap(self):
        """Test that UbuntuAdapter identifies apt and snap availability."""
        with patch("shutil.which", side_effect=lambda x: "/usr/bin/apt-get" if x == "apt-get" else "/usr/bin/snap" if x == "snap" else None):
            adapter = UbuntuAdapter()
            assert adapter.detect() is True
            assert "apt-get" in adapter.package_manager().install_command(["test-pkg"])
            assert adapter.has_snap_support() is True

    def test_pop_os_adapter_detects_apt_and_system76(self):
        """Test that PopOSAdapter identifies apt and system76 repository."""
        with patch("shutil.which", return_value="/usr/bin/apt-get"):
            adapter = PopOSAdapter()
            assert adapter.detect() is True
            cmd = adapter.package_manager().install_command(["system76-driver"])
            assert "apt-get" in cmd
            # Check that system76-driver package is in the command
            assert any("system76" in arg for arg in cmd)

    def test_fedora_adapter_detects_dnf(self):
        """Test that FedoraAdapter correctly identifies dnf-based systems."""
        with patch("shutil.which", return_value="/usr/bin/dnf"):
            adapter = FedoraAdapter()
            assert adapter.detect() is True
            assert "dnf" in adapter.package_manager().install_command(["test-pkg"])

    def test_mint_adapter_detects_apt(self):
        """Test that MintAdapter correctly identifies apt-based systems."""
        with patch("shutil.which", return_value="/usr/bin/apt-get"):
            adapter = MintAdapter()
            assert adapter.detect() is True
            assert "apt-get" in adapter.package_manager().install_command(["test-pkg"])

    def test_generic_adapter_fallback(self):
        """Test that GenericAdapter acts as a safe fallback using standard POSIX tools."""
        # Mock shutil.which to return None for all package managers
        with patch("shutil.which", return_value=None):
            adapter = GenericAdapter()
            assert adapter.detect() is True
            cmd = adapter.package_manager().install_command(["test-pkg"])
            assert "echo" in cmd

    def test_init_system_detection_systemd(self):
        """Test detection of systemd as the init system."""
        with patch("shutil.which", return_value="/bin/systemctl"):
            adapter = GenericAdapter()
            init_system = adapter.init_system()
            assert "systemctl" in init_system.start_service_command("glados")

    def test_init_system_detection_s6(self):
        """Test detection of s6-rc as the init system."""
        with patch("shutil.which", side_effect=lambda x: "/bin/s6-rc" if x == "s6-rc" else None):
            adapter = GenericAdapter()
            init_system = adapter.init_system()
            assert "s6-rc" in init_system.start_service_command("glados")