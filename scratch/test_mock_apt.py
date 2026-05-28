import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vivid_gui.backends import apt_backend

def test_apt_mocking():
    print("Testing APT Backend mock parsing and caching...")
    
    mock_dpkg_output = (
        "installed\tpython3\n"
        "installed\tcurl\n"
        "config-files\tlegacy-package\n"
        "installed\tgit\n"
    )
    
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = mock_dpkg_output
    
    with patch("subprocess.run", return_value=mock_run) as mock_sub:
        # First call should invoke subprocess.run
        names1 = apt_backend.get_installed_names(use_cache=False)
        print("Names found (no cache):", names1)
        assert "python3" in names1
        assert "curl" in names1
        assert "git" in names1
        assert "legacy-package" not in names1, "Should filter out config-files status"
        assert mock_sub.call_count == 1
        
        # Reset mock call count
        mock_sub.reset_mock()
        
        # Second call with use_cache=True should use the cache (call count remains 0)
        names2 = apt_backend.get_installed_names(use_cache=True)
        print("Names found (cached):", names2)
        assert mock_sub.call_count == 0
        assert names1 == names2
        
    print("All tests passed successfully!")

if __name__ == "__main__":
    test_apt_mocking()
