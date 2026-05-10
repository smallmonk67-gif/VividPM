"""
pkg_manager.py — Dispatcher that auto-detects and routes to available backends.
"""
import os
import threading
import shutil
import platform

from aur_gui.backends import (
    pacman_backend, flatpak_backend, snap_backend, pip_backend,
    apt_backend, dnf_backend, zypper_backend,
    portage_backend, xbps_backend, apk_backend,
    winget_backend, choco_backend, scoop_backend,
)
from aur_gui import utils

# Ordered list of all supported backends
_ALL_BACKENDS = [
    pacman_backend, apt_backend, dnf_backend, zypper_backend,
    portage_backend, xbps_backend, apk_backend,
    winget_backend, choco_backend, scoop_backend,
    flatpak_backend, snap_backend, pip_backend,
]
# Cache of currently active backends — call reload_backends() to refresh
_active_backends = None
_os_family = None  # Cached OS family string


def detect_os_family():
    """
    Detect the current OS. Returns a set of lowercase ID strings.
    For Linux, reads /etc/os-release. For Windows, returns {"windows"}.
    """
    global _os_family
    if _os_family is not None:
        return _os_family

    if platform.system() == "Windows":
        _os_family = {"windows"}
        return _os_family

    ids = set()
    try:
        with open("/etc/os-release") as f:
            for line in f:
                line = line.strip()
                if line.startswith("ID=") or line.startswith("ID_LIKE="):
                    _, _, val = line.partition("=")
                    val = val.strip().strip('"').lower()
                    # ID_LIKE can be space-separated
                    ids.update(val.split())
    except Exception:
        pass

    _os_family = ids
    return _os_family


# Map backend IDs → the OS families they support.
# None means the backend works on any OS (cross-distro tools).
_BACKEND_COMPAT = {
    "pacman":  {"arch", "manjaro", "endeavouros", "garuda", "arcolinux", "artix"},
    "apt":     {"debian", "ubuntu", "linuxmint", "mint", "pop", "elementary",
                "zorin", "kali", "raspbian", "armbian"},
    "dnf":     {"fedora", "rhel", "centos", "almalinux", "rocky", "nobara",
                "ultramarine", "mageia", "oracle"},
    "zypper":  {"opensuse", "suse", "sles", "tumbleweed", "leap"},
    "portage": {"gentoo", "funtoo", "chromeos"},
    "xbps":    {"void"},
    "apk":     {"alpine"},
    "apk":     {"alpine"},
    "winget":  {"windows"},
    "choco":   {"windows"},
    "scoop":   {"windows"},
    "flatpak": None,  # universal
    "snap":    None,  # universal
    "pip":     None,  # universal
}


def _is_os_compatible(backend):
    """Return True if the backend is compatible with the current OS."""
    compat = _BACKEND_COMPAT.get(getattr(backend, "BACKEND_ID", ""), None)
    if compat is None:
        return True  # cross-distro backend
    os_ids = detect_os_family()
    return bool(os_ids & compat)


def reload_backends():
    """Re-detect which backends are available. Call after installing a new one."""
    global _active_backends
    _active_backends = [
        b for b in _ALL_BACKENDS
        if _is_os_compatible(b) and b.is_available()
    ]
    return _active_backends


def get_available_backends():
    """Return list of backend modules that are available on this system."""
    global _active_backends
    if _active_backends is None:
        _active_backends = [
            b for b in _ALL_BACKENDS
            if _is_os_compatible(b) and b.is_available()
        ]
    return _active_backends


def get_installed_all():
    """Return combined installed packages from all available backends."""
    results = []
    for backend in get_available_backends():
        try:
            results.extend(backend.get_installed())
        except Exception as e:
            print(f"[pkg_manager] error getting installed from {backend.BACKEND_ID}: {e}")
    return results


def search_all(query: str, callback):
    """
    Search all available backends in parallel, streaming results as they arrive.
    callback is called multiple times, once per backend, with a list of packages.
    """
    backends = get_available_backends()

    def worker(backend):
        try:
            results = backend.search(query)
            callback(results, backend.BACKEND_ID)
        except Exception as e:
            print(f"[pkg_manager] search error in {backend.BACKEND_ID}: {e}")
            utils.show_error("Search Error", f"Backend {backend.DISPLAY_NAME} failed:\n{e}")
            callback([], backend.BACKEND_ID)

    for backend in backends:
        threading.Thread(target=worker, args=(backend,), daemon=True).start()


def async_get_installed(callback):
    """Fetch installed packages from all backends in background threads, streaming results."""
    backends = get_available_backends()

    def worker(backend):
        try:
            results = backend.get_installed()
            callback(results, backend.BACKEND_ID)
        except Exception as e:
            print(f"[pkg_manager] get_installed error in {backend.BACKEND_ID}: {e}")
            utils.show_error("Load Error", f"Failed to fetch installed apps from {backend.DISPLAY_NAME}:\n{e}")
            callback([], backend.BACKEND_ID)

    for backend in backends:
        threading.Thread(target=worker, args=(backend,), daemon=True).start()


def async_fetch_extended_info(pkg, callback):
    """
    Fetch extended dependency info for a package, routing to the right backend.
    pkg is a package dict with a 'backend' key.
    """
    backend_id = pkg.get("backend", "pacman")
    pkg_id = pkg.get("PackageName") or pkg.get("ID") or pkg.get("Name")

    backend_map = {b.BACKEND_ID: b for b in get_available_backends()}
    backend = backend_map.get(backend_id)

    def worker():
        try:
            info = backend.get_info(pkg_id) if backend else {}
        except Exception as e:
            print(f"[pkg_manager] get_info error: {e}")
            info = {}
        callback(info)

    threading.Thread(target=worker, daemon=True).start()


def install_package(pkg, terminal="alacritty", on_finish=None):
    """Launch install for the package using the correct backend."""
    import subprocess, time

    backend_id = pkg.get("backend", "pacman")
    pkg_id = pkg.get("PackageName") or pkg.get("ID") or pkg.get("Name")
    backend_map = {b.BACKEND_ID: b for b in get_available_backends()}
    backend = backend_map.get(backend_id, pacman_backend)

    def worker():
        # Build command based on backend
        if backend_id == "pacman":
            helper = "yay" if shutil.which("yay") else "paru" if shutil.which("paru") else "pacman"
            # If we are using pacman but trying to install from AUR, it will fail.
            # We can detect this if 'aur' is in the pkg data (though we don't always have it here)
            cmd = [helper, "-S", "--needed", pkg_id]
        elif backend_id == "flatpak":
            cmd = ["flatpak", "install", "flathub", pkg_id]
        elif backend_id == "snap":
            cmd = ["sudo", "snap", "install", pkg_id]
        elif backend_id == "pip":
            pip = "pip" if shutil.which("pip") else "pip3"
            if platform.system() == "Windows":
                cmd = [pip, "install", pkg_id]
            else:
                cmd = ["sudo", pip, "install", "--break-system-packages", pkg_id]
        elif backend_id == "winget":
            cmd = ["winget", "install", "-e", "--id", pkg_id]
        elif backend_id == "choco":
            cmd = ["choco", "install", pkg_id, "-y"]
        elif backend_id == "scoop":
            cmd = ["scoop", "install", pkg_id]
        else:
            return

        # Wrap command in terminal spawn logic
        if platform.system() == "Windows":
            # On Windows, 'start cmd /k' opens a new terminal window that stays open
            full_cmd = f"start cmd /k \"{' '.join(cmd)}\""
            try:
                subprocess.Popen(full_cmd, shell=True)
                time.sleep(1) # Give it time to spawn
                if on_finish:
                    on_finish()
                return
            except Exception as e:
                print(f"[pkg_manager] install error: {e}")
                utils.show_error("Installation Failed", f"Could not start installation process:\n{e}")
                return
        else:
            # On Linux, wrap in bash to ensure we can pause on failure
            cmd_str = " ".join(cmd)
            bash_cmd = f"{cmd_str} || (echo; echo 'Process failed. Press Enter to close...'; read)"
            full_cmd = [terminal, "-e", "bash", "-c", bash_cmd]

        try:
            proc = subprocess.Popen(full_cmd)
            proc.wait()
            time.sleep(0.5)
            if on_finish:
                on_finish()
        except Exception as e:
            print(f"[pkg_manager] install error: {e}")

    threading.Thread(target=worker, daemon=True).start()


def remove_package(pkg, terminal="alacritty", on_finish=None):
    """Launch removal for the package using the correct backend."""
    import subprocess, time, shutil

    backend_id = pkg.get("backend", "pacman")
    pkg_id = pkg.get("PackageName") or pkg.get("ID") or pkg.get("Name")

    def worker():
        if backend_id == "pacman":
            cmd = ["sudo", "pacman", "-Rns", pkg_id]
        elif backend_id == "flatpak":
            cmd = ["flatpak", "uninstall", pkg_id]
        elif backend_id == "snap":
            cmd = ["sudo", "snap", "remove", pkg_id]
        elif backend_id == "pip":
            pip = "pip" if shutil.which("pip") else "pip3"
            if platform.system() == "Windows":
                cmd = [pip, "uninstall", "-y", pkg_id]
            else:
                cmd = ["sudo", pip, "uninstall", "-y", pkg_id]
        elif backend_id == "winget":
            cmd = ["winget", "uninstall", "-e", "--id", pkg_id]
        elif backend_id == "choco":
            cmd = ["choco", "uninstall", pkg_id, "-y"]
        elif backend_id == "scoop":
            cmd = ["scoop", "uninstall", pkg_id]
        else:
            return

        # Wrap command in terminal spawn logic
        if platform.system() == "Windows":
            full_cmd = f"start cmd /k \"{' '.join(cmd)}\""
            try:
                subprocess.Popen(full_cmd, shell=True)
                time.sleep(1)
                if on_finish:
                    on_finish()
                return
            except Exception as e:
                print(f"[pkg_manager] remove error: {e}")
                utils.show_error("Removal Failed", f"Could not start removal process:\n{e}")
                return
        else:
            # On Linux, wrap in bash to ensure we can pause on failure
            cmd_str = " ".join(cmd)
            bash_cmd = f"{cmd_str} || (echo; echo 'Process failed. Press Enter to close...'; read)"
            full_cmd = [terminal, "-e", "bash", "-c", bash_cmd]

        try:
            proc = subprocess.Popen(full_cmd)
            proc.wait()
            time.sleep(0.5)
            if on_finish:
                on_finish()
        except Exception as e:
            print(f"[pkg_manager] remove error: {e}")

    threading.Thread(target=worker, daemon=True).start()
