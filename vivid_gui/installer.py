"""
installer.py — Auto-detection and installation of missing package manager backends.
"""
import shutil
import subprocess
import os
import stat
import shlex
import threading
import time
import platform
import sys
from vivid_gui import utils

# Describes how to install each optional backend
INSTALLABLE_BACKENDS = {
    "flatpak": {
        "display_name": "Flatpak",
        "binary": "flatpak",
        "install_cmd": ["sudo", "pacman", "-S", "--noconfirm", "flatpak"],
        "post_install": [],
        "description": "Universal Linux app sandboxing platform",
        "os": "Linux",
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
        "os": "Linux",
    },
    "scoop": {
        "display_name": "Scoop",
        "binary": "scoop",
        "install_cmd": ["powershell", "-NoExit", "-ExecutionPolicy", "RemoteSigned", "-Command", "Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression"],
        "post_install": [],
        "description": "A command-line installer for Windows (User-level)",
        "os": "Windows",
    },
    "choco": {
        "display_name": "Chocolatey",
        "binary": "choco",
        "install_cmd": ["powershell", "-NoProfile", "-Command", "Start-Process powershell -Wait -Verb RunAs -ArgumentList '-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', 'iex ((New-Object System.Net.WebClient).DownloadString(''https://community.chocolatey.org/install.ps1''))'"],
        "post_install": [],
        "description": "The Package Manager for Windows (Requires Admin)",
        "os": "Windows",
    },
    "brew": {
        "display_name": "Homebrew",
        "binary": "brew",
        "install_cmd": ["bash", "-c", 'bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'],
        "post_install": [],
        "description": "The Missing Package Manager for macOS (and Linux)",
        "os": ["Darwin", "Linux"],
    },
    "nix": {
        "display_name": "Nix",
        "binary": "nix-env",
        "install_cmd": ["sh", "-c", "curl -L https://nixos.org/nix/install | sh -s -- --daemon"],
        "post_install": [],
        "description": "Powerful package manager for Linux and macOS",
        "os": ["Darwin", "Linux"],
    },
}

class PackageInstaller:
    def get_missing_backends(self):
        system_os = platform.system()
        missing = []
        for backend_id, info in INSTALLABLE_BACKENDS.items():
            os_req = info.get("os", "Linux")
            if system_os not in (os_req if isinstance(os_req, list) else [os_req]) and "Universal" not in os_req:
                continue
            if shutil.which(info["binary"]) is None:
                missing.append(backend_id)
        return missing

    def install(self, pkg, backend_obj, terminal="alacritty", on_finish=None):
        backend_id = pkg.get("backend")
        pkg_id = pkg.get("PackageName") or pkg.get("ID") or pkg.get("Name")
        cmd = self._get_install_cmd(backend_id, pkg_id)
        if not cmd: return False
        self._run_in_terminal(cmd, terminal, on_finish)
        return True

    def remove(self, pkg, backend_obj, terminal="alacritty", on_finish=None):
        backend_id = pkg.get("backend")
        pkg_id = pkg.get("PackageName") or pkg.get("ID") or pkg.get("Name")
        cmd = self._get_remove_cmd(backend_id, pkg_id)
        if not cmd: return False
        self._run_in_terminal(cmd, terminal, on_finish)
        return True

    def _get_install_cmd(self, backend_id, pkg_id):
        if backend_id == "pacman": return ["sudo", "pacman", "-S", "--needed", pkg_id]
        if backend_id == "apt": return ["sudo", "apt", "install", "-y", pkg_id]
        if backend_id == "dnf": return ["sudo", "dnf", "install", "-y", pkg_id]
        if backend_id == "zypper": return ["sudo", "zypper", "install", "-y", pkg_id]
        if backend_id == "winget": return ["winget", "install", "-e", "--id", pkg_id]
        if backend_id == "flatpak": return ["flatpak", "install", "flathub", "-y", pkg_id]
        if backend_id == "pip": return [sys.executable, "-m", "pip", "install", pkg_id]
        return None

    def _get_remove_cmd(self, backend_id, pkg_id):
        if backend_id == "pacman": return ["sudo", "pacman", "-Rns", pkg_id]
        if backend_id == "apt": return ["sudo", "apt", "remove", "-y", pkg_id]
        if backend_id == "dnf": return ["sudo", "dnf", "remove", "-y", pkg_id]
        if backend_id == "winget": return ["winget", "uninstall", "-e", "--id", pkg_id]
        if backend_id == "flatpak": return ["flatpak", "uninstall", "-y", pkg_id]
        return None

    def _run_in_terminal(self, cmd, terminal, on_finish):
        def worker():
            try:
                if platform.system() == "Windows":
                    full_cmd = f"start cmd /k \"{' '.join(cmd)}\""
                    subprocess.Popen(full_cmd, shell=True).wait()
                else:
                    cmd_str = " ".join(cmd)
                    bash_cmd = f"{cmd_str} || (echo; echo 'Press Enter to close...'; read)"
                    subprocess.Popen([terminal, "-e", "bash", "-c", bash_cmd]).wait()
                if on_finish: on_finish()
            except Exception as e: print(f"[installer] error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def install_backend(self, backend_id, terminal="alacritty", on_finish=None):
        info = INSTALLABLE_BACKENDS.get(backend_id)
        if not info: return
        def worker():
            try:
                cmd = info["install_cmd"]
                self._run_in_terminal(cmd, terminal, None)
                for post in info["post_install"]:
                    try: subprocess.run(post, check=False)
                    except: pass
                if on_finish: on_finish()
            except: pass
        threading.Thread(target=worker, daemon=True).start()
