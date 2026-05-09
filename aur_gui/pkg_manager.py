"""
pkg_manager.py — Dispatcher that auto-detects and routes to available backends.
"""
import os
import threading
import shutil

from aur_gui.backends import (
    pacman_backend, flatpak_backend, snap_backend, pip_backend,
    apt_backend, dnf_backend, zypper_backend,
    portage_backend, xbps_backend, apk_backend,
)

# Ordered list of all supported backends
_ALL_BACKENDS = [
    pacman_backend, apt_backend, dnf_backend, zypper_backend,
    portage_backend, xbps_backend, apk_backend,
    flatpak_backend, snap_backend, pip_backend,
]
# Cache of currently active backends — call reload_backends() to refresh
_active_backends = None
_os_family = None  # Cached OS family string


def detect_os_family():
    """
    Detect the current Linux distribution family by reading /etc/os-release.
    Returns a set of lowercase ID strings (e.g. {"arch", "ubuntu", "debian"}).
    Includes both ID and ID_LIKE values so derivative distros match their parents.
    """
    global _os_family
    if _os_family is not None:
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
            cmd = [terminal, "-e", "yay", "-S", pkg_id]
        elif backend_id == "flatpak":
            cmd = [terminal, "-e", "flatpak", "install", "flathub", pkg_id]
        elif backend_id == "snap":
            cmd = [terminal, "-e", "sudo", "snap", "install", pkg_id]
        elif backend_id == "pip":
            pip = "pip" if shutil.which("pip") else "pip3"
            cmd = [terminal, "-e", "sudo", pip, "install", "--break-system-packages", pkg_id]
        else:
            return
        try:
            proc = subprocess.Popen(cmd)
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
            cmd = [terminal, "-e", "sudo", "pacman", "-Rns", pkg_id]
        elif backend_id == "flatpak":
            cmd = [terminal, "-e", "flatpak", "uninstall", pkg_id]
        elif backend_id == "snap":
            cmd = [terminal, "-e", "sudo", "snap", "remove", pkg_id]
        elif backend_id == "pip":
            pip = "pip" if shutil.which("pip") else "pip3"
            cmd = [terminal, "-e", "sudo", pip, "uninstall", "-y", pkg_id]
        else:
            return
        try:
            proc = subprocess.Popen(cmd)
            proc.wait()
            time.sleep(0.5)
            if on_finish:
                on_finish()
        except Exception as e:
            print(f"[pkg_manager] remove error: {e}")

    threading.Thread(target=worker, daemon=True).start()
