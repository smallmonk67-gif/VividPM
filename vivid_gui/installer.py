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
        "install_cmd": ["_AUR_HELPER_", "-S", "--noconfirm", "snapd"],
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
    "yay": {
        "display_name": "yay (AUR)",
        "binary": "yay",
        "install_cmd": ["bash", "-c", "sudo pacman -S --needed --noconfirm git base-devel && git clone https://aur.archlinux.org/yay-bin.git /tmp/yay-bin && cd /tmp/yay-bin && makepkg -si --noconfirm"],
        "post_install": [],
        "description": "Fast AUR helper written in Go",
        "os": "Linux",
    },
    "paru": {
        "display_name": "paru (AUR)",
        "binary": "paru",
        "install_cmd": ["bash", "-c", "sudo pacman -S --needed --noconfirm git base-devel && git clone https://aur.archlinux.org/paru-bin.git /tmp/paru-bin && cd /tmp/paru-bin && makepkg -si --noconfirm"],
        "post_install": [],
        "description": "Feature-rich AUR helper designed in Rust",
        "os": "Linux",
    },
}

class PackageInstaller:
    def get_missing_backends(self):
        system_os = platform.system()
        missing = []
        is_arch = shutil.which("pacman") is not None
        for backend_id, info in INSTALLABLE_BACKENDS.items():
            if backend_id in ["yay", "paru"] and not is_arch:
                continue
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
        if backend_id == "aur":
            helper = "yay" if shutil.which("yay") else ("paru" if shutil.which("paru") else None)
            if helper:
                return [helper, "-S", "--needed", pkg_id]
            return None
        if backend_id == "apt": return ["sudo", "apt", "install", "-y", pkg_id]
        if backend_id == "dnf": return ["sudo", "dnf", "install", "-y", pkg_id]
        if backend_id == "zypper": return ["sudo", "zypper", "install", "-y", pkg_id]
        if backend_id == "winget": return ["winget", "install", "-e", "--id", pkg_id]
        if backend_id == "flatpak": return ["flatpak", "install", "flathub", "-y", pkg_id]
        if backend_id == "pip": return [sys.executable, "-m", "pip", "install", pkg_id]
        return None

    def _get_remove_cmd(self, backend_id, pkg_id):
        if backend_id == "pacman": return ["sudo", "pacman", "-Rns", pkg_id]
        if backend_id == "aur":
            helper = "yay" if shutil.which("yay") else ("paru" if shutil.which("paru") else None)
            if helper:
                return [helper, "-Rns", pkg_id]
            return ["sudo", "pacman", "-Rns", pkg_id]
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
                # Copy the command list to avoid mutating the shared dict
                cmd = list(info["install_cmd"])
                # Resolve _AUR_HELPER_ placeholder dynamically
                if cmd and cmd[0] == "_AUR_HELPER_":
                    helper = "yay" if shutil.which("yay") else ("paru" if shutil.which("paru") else None)
                    if helper:
                        cmd[0] = helper
                    else:
                        print("[installer] No AUR helper found to install backend")
                        return

                # Chain post_install commands into the same terminal session
                # so they run AFTER the main install finishes.
                post_cmds = info.get("post_install", [])
                if post_cmds:
                    # Build a single bash command that chains all steps
                    all_cmds = [" ".join(shlex.quote(c) for c in cmd)]
                    for post in post_cmds:
                        all_cmds.append(" ".join(shlex.quote(c) for c in post))
                    chained = " && ".join(all_cmds)
                    final_cmd = ["bash", "-c", chained]
                    self._run_in_terminal(final_cmd, terminal, on_finish)
                else:
                    self._run_in_terminal(cmd, terminal, on_finish)
            except Exception as e:
                print(f"[installer] install_backend error: {e}")
        threading.Thread(target=worker, daemon=True).start()
