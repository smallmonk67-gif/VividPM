"""
pkg_manager.py — Dispatcher that auto-detects and routes to available backends.
"""
import threading

from aur_gui.backends import pacman_backend, flatpak_backend, snap_backend, pip_backend

# Ordered list of all supported backends (APT removed — not applicable on Arch)
_ALL_BACKENDS = [pacman_backend, flatpak_backend, snap_backend, pip_backend]
# Cache of currently active backends — call reload_backends() to refresh
_active_backends = None


def reload_backends():
    """Re-detect which backends are available. Call after installing a new one."""
    global _active_backends
    _active_backends = [b for b in _ALL_BACKENDS if b.is_available()]
    return _active_backends


def get_available_backends():
    """Return list of backend modules that are available on this system."""
    global _active_backends
    if _active_backends is None:
        _active_backends = [b for b in _ALL_BACKENDS if b.is_available()]
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
    """Fetch installed packages from all backends in a background thread."""
    def worker():
        results = get_installed_all()
        callback(results)

    threading.Thread(target=worker, daemon=True).start()


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
            cmd = [terminal, "-e", pip, "install", "--break-system-packages", pkg_id]
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
            cmd = [terminal, "-e", pip, "uninstall", "-y", pkg_id]
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
