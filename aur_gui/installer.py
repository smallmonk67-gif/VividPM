"""
installer.py — Auto-detection and installation of missing package manager backends.
On Arch Linux, missing backends (Flatpak, Snap) can be installed via pacman/yay.
"""
import shutil
import subprocess

# Describes how to install each optional backend on Arch Linux
INSTALLABLE_BACKENDS = {
    "flatpak": {
        "display_name": "Flatpak",
        "binary": "flatpak",
        "install_cmd": ["sudo", "pacman", "-S", "--noconfirm", "flatpak"],
        "post_install": [],  # No extra steps needed for flatpak
        "description": "Universal Linux app sandboxing platform (Flathub)",
    },
    "snap": {
        "display_name": "Snap",
        "binary": "snap",
        "install_cmd": ["yay", "-S", "--noconfirm", "snapd"],
        "post_install": [
            ["sudo", "systemctl", "enable", "--now", "snapd.socket"],
            ["sudo", "ln", "-sf", "/var/lib/snapd/snap", "/snap"],
        ],
        "description": "Snap package manager by Canonical",
    },
}


def get_missing_backends():
    """Return a list of backend IDs that are installable but not currently available."""
    missing = []
    for backend_id, info in INSTALLABLE_BACKENDS.items():
        if shutil.which(info["binary"]) is None:
            missing.append(backend_id)
    return missing


def install_backend(backend_id, terminal="alacritty", on_finish=None):
    """
    Install a missing backend in a terminal window.
    Runs the install command and any post-install steps sequentially.
    """
    import threading
    import time

    info = INSTALLABLE_BACKENDS.get(backend_id)
    if not info:
        return

    def worker():
        try:
            # Main install command
            proc = subprocess.Popen([terminal, "-e"] + info["install_cmd"])
            proc.wait()

            # Post-install steps (run silently in background, no terminal needed)
            for cmd in info["post_install"]:
                try:
                    subprocess.run(cmd, check=False)
                except Exception as e:
                    print(f"[installer] post-install step failed: {e}")

            time.sleep(1.0)
            if on_finish:
                on_finish()
        except Exception as e:
            print(f"[installer] install error for {backend_id}: {e}")

    threading.Thread(target=worker, daemon=True).start()
