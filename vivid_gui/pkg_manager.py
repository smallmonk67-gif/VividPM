"""
pkg_manager.py — Dispatcher that auto-detects and routes to available backends.
"""
import os
import threading
import shutil
import platform

from vivid_gui.backends import (
    pacman_backend, aur_backend, flatpak_backend, snap_backend, pip_backend,
    apt_backend, dnf_backend, zypper_backend,
    portage_backend, xbps_backend, apk_backend,
    winget_backend, choco_backend, scoop_backend,
    windows_native_backend,
    brew_backend, macports_backend, nix_backend, fink_backend,
    npm_backend, cargo_backend, gem_backend,
)
from vivid_gui import utils

# Ordered list of all supported backends
_ALL_BACKENDS = [
    pacman_backend, aur_backend, apt_backend, dnf_backend, zypper_backend,
    portage_backend, xbps_backend, apk_backend,
    winget_backend, choco_backend, scoop_backend,
    windows_native_backend,
    brew_backend, macports_backend, nix_backend, fink_backend,
    flatpak_backend, snap_backend, pip_backend,
    npm_backend, cargo_backend, gem_backend,
]

# Map backend IDs → the OS families they support.
# None means the backend works on any OS (cross-distro tools).
_BACKEND_COMPAT = {
    "pacman":  {"arch", "manjaro", "endeavouros", "garuda", "arcolinux", "artix"},
    "aur":     {"arch", "manjaro", "endeavouros", "garuda", "arcolinux", "artix"},
    "apt":     {"debian", "ubuntu", "linuxmint", "mint", "pop", "elementary",
                "zorin", "kali", "raspbian", "armbian"},
    "dnf":     {"fedora", "rhel", "centos", "almalinux", "rocky", "nobara",
                "ultramarine", "mageia", "oracle"},
    "zypper":  {"opensuse", "suse", "sles", "tumbleweed", "leap"},
    "portage": {"gentoo", "funtoo", "chromeos"},
    "xbps":    {"void"},
    "apk":     {"alpine"},
    "winget":  {"windows"},
    "choco":   {"windows"},
    "scoop":   {"windows"},
    "windows_native": {"windows"},
    "brew":    {"macos", "darwin", "linux"}, # Linuxbrew exists
    "macports":{"macos", "darwin"},
    "nix":     {"macos", "darwin", "linux"},
    "fink":    {"macos", "darwin"},
    "flatpak": None,  # universal
    "snap":    None,  # universal
    "pip":     None,  # universal
    "npm":     None,  # universal
    "cargo":   None,  # universal
    "gem":     None,  # universal
}

def refresh_path():
    """Add common non-standard package manager paths to os.environ['PATH']."""
    extra_paths = [
        "/opt/homebrew/bin",
        "/home/linuxbrew/.linuxbrew/bin",
        os.path.expanduser("~/.cargo/bin"),
        os.path.expanduser("~/.nix-profile/bin"),
        "/nix/var/nix/profiles/default/bin",
        "/usr/local/bin",
        "/opt/local/bin", # MacPorts
        "/sw/bin", # Fink
    ]
    current_path = os.environ.get("PATH", "").split(os.pathsep)
    new_paths = []
    for p in extra_paths:
        if os.path.exists(p) and p not in current_path:
            new_paths.append(p)
    
    if new_paths:
        os.environ["PATH"] = os.pathsep.join(new_paths + current_path)

class PackageManager:
    def __init__(self):
        self.backends = []
        self._os_family = None
        self._backends_lock = threading.Lock()
        self.reload_backends()

    def detect_os_family(self):
        if self._os_family is not None:
            return self._os_family

        ids = set()
        if platform.system() == "Linux":
            ids.add("linux")
        elif platform.system() == "Darwin":
            ids.update(["macos", "darwin"])
        elif platform.system() == "Windows":
            ids.add("windows")

        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("ID=") or line.startswith("ID_LIKE="):
                            _, _, val = line.partition("=")
                            val = val.strip().strip('"').lower()
                            ids.update(val.split())
        except: pass

        self._os_family = ids
        return self._os_family

    def _is_os_compatible(self, backend):
        compat = _BACKEND_COMPAT.get(getattr(backend, "BACKEND_ID", ""), None)
        if compat is None: return True
        os_ids = self.detect_os_family()
        return bool(os_ids & compat)

    def reload_backends(self):
        refresh_path()
        with self._backends_lock:
            self.backends = []
            for b in _ALL_BACKENDS:
                if self._is_os_compatible(b):
                    if b.is_available():
                        self.backends.append(b)
        return self.backends

    def get_backend(self, backend_id):
        for b in self.backends:
            if getattr(b, "BACKEND_ID", "") == backend_id:
                return b
        return None

    def refresh_installed_cache(self):
        for b in self.backends:
            if hasattr(b, "refresh_cache"):
                b.refresh_cache()
