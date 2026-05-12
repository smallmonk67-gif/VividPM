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
        "install_cmd": ["bash", "-c", "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"],
        "post_install": [],
        "description": "The Missing Package Manager for macOS (and Linux)",
        "os": ["Darwin", "Linux"],
    },
    "macports": {
        "display_name": "MacPorts",
        "binary": "port",
        "install_cmd": ["open", "https://www.macports.org/install.php"],
        "post_install": [],
        "description": "macOS package management (Opens browser)",
        "os": "Darwin",
    },
    "nix": {
        "display_name": "Nix",
        "binary": "nix-env",
        "install_cmd": ["sh", "-c", "curl -L https://nixos.org/nix/install | sh"],
        "post_install": [],
        "description": "Powerful package manager for Linux and macOS",
        "os": ["Darwin", "Linux"],
    },
    "fink": {
        "display_name": "Fink",
        "binary": "fink",
        "install_cmd": ["open", "https://www.finkproject.org/download/"],
        "post_install": [],
        "description": "Debian package manager for macOS (Opens browser)",
        "os": "Darwin",
    },
    "npm": {
        "display_name": "npm (Node.js)",
        "binary": "npm",
        "install_cmd": ["open", "https://nodejs.org/en/download/"] if __import__("platform").system() == "Darwin" else ["echo", "Please install Node.js manually."],
        "post_install": [],
        "description": "Node.js Package Manager",
        "os": "Universal",
    },
    "cargo": {
        "display_name": "Cargo (Rust)",
        "binary": "cargo",
        "install_cmd": ["sh", "-c", "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"],
        "post_install": [],
        "description": "Rust Package Manager",
        "os": "Universal",
    },
    "gem": {
        "display_name": "RubyGems",
        "binary": "gem",
        "install_cmd": ["open", "https://www.ruby-lang.org/en/downloads/"] if __import__("platform").system() == "Darwin" else ["echo", "Please install Ruby manually."],
        "post_install": [],
        "description": "Ruby Package Manager",
        "os": "Universal",
    },
}


def get_missing_backends():
    """Return a list of backend IDs that are installable but not currently available."""
    import platform
    system_os = platform.system()
    missing = []
    for backend_id, info in INSTALLABLE_BACKENDS.items():
        os_req = info.get("os", "Linux")
        if isinstance(os_req, str):
            os_req = [os_req]
            
        if system_os not in os_req and "Universal" not in os_req:
            continue
            
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
            import platform
            # Main install command
            if platform.system() == "Windows":
                proc = subprocess.Popen(
                    info["install_cmd"], 
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
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
