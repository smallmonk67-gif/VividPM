import sys
import os
from unittest.mock import patch, MagicMock

# Mock out heavy GUI libraries in sys.modules before importing vivid_gui
sys.modules['customtkinter'] = MagicMock()
sys.modules['darkdetect'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageTk'] = MagicMock()

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vivid_gui import installer

def test_installer_mocking():
    print("Testing PackageInstaller dynamic backend command override...")
    
    # 1. Test get_system_package_manager detection
    with patch("shutil.which") as mock_which:
        # Simulate an Arch Linux environment
        mock_which.side_effect = lambda x: "/usr/bin/pacman" if x == "pacman" else None
        print("Detected PM on Arch:", installer.get_system_package_manager())
        assert installer.get_system_package_manager() == "pacman"
        
        # Simulate a Debian/Ubuntu environment
        mock_which.side_effect = lambda x: "/usr/bin/apt-get" if x == "apt-get" else None
        print("Detected PM on Debian/Ubuntu:", installer.get_system_package_manager())
        assert installer.get_system_package_manager() == "apt"

        # Simulate a Fedora environment
        mock_which.side_effect = lambda x: "/usr/bin/dnf" if x == "dnf" else None
        print("Detected PM on Fedora:", installer.get_system_package_manager())
        assert installer.get_system_package_manager() == "dnf"

        # Simulate an openSUSE environment
        mock_which.side_effect = lambda x: "/usr/bin/zypper" if x == "zypper" else None
        print("Detected PM on openSUSE:", installer.get_system_package_manager())
        assert installer.get_system_package_manager() == "zypper"

    # 2. Test install_backend dynamic command selection
    pi = installer.PackageInstaller()
    
    # Setup test run_in_terminal mock
    run_mock = MagicMock()
    pi._run_in_terminal = run_mock
    
    with patch("shutil.which") as mock_which:
        # Test Flatpak install on Debian/Ubuntu
        mock_which.side_effect = lambda x: "/usr/bin/apt-get" if x == "apt-get" else None
        
        # Run worker directly
        pi.install_backend("flatpak")
        
        # Give threads a tiny bit of time to run
        import time
        time.sleep(0.1)
        
        assert run_mock.call_count == 1
        cmd_arg = run_mock.call_args[0][0]
        print("Flatpak install command on Debian/Ubuntu:", cmd_arg)
        assert cmd_arg == ["sudo", "apt-get", "install", "-y", "flatpak"]
        
        # Reset mock
        run_mock.reset_mock()
        
        # Test Snap install on Fedora
        mock_which.side_effect = lambda x: "/usr/bin/dnf" if x == "dnf" else None
        pi.install_backend("snap")
        time.sleep(0.1)
        
        assert run_mock.call_count == 1
        cmd_arg2 = run_mock.call_args[0][0]
        print("Snap install command on Fedora:", cmd_arg2)
        assert cmd_arg2[0] == "bash" # It chains systemctl enablement
        assert "dnf install -y snapd" in cmd_arg2[2]
        
    print("All installer mock tests passed successfully!")

if __name__ == "__main__":
    test_installer_mocking()
