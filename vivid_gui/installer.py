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
        "install_cmd": ["bash", "-c", 'bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'],
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
        "install_cmd": ["sh", "-c", "curl -L https://nixos.org/nix/install | sh -s -- --daemon"],
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
        "install_cmd": ["open", "https://nodejs.org/en/download/"] if __import__("platform").system() == "Darwin" else ["sudo", "pacman", "-S", "--noconfirm", "npm"],
        "post_install": [],
        "description": "Node.js Package Manager",
        "os": "Universal",
    },
    "cargo": {
        "display_name": "Cargo (Rust)",
        "binary": "cargo",
        "install_cmd": ["sh", "-c", "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"] if __import__("platform").system() == "Darwin" else ["sudo", "pacman", "-S", "--noconfirm", "rust"],
        "post_install": [],
        "description": "Rust Package Manager",
        "os": "Universal",
    },
    "gem": {
        "display_name": "RubyGems",
        "binary": "gem",
        "install_cmd": ["open", "https://www.ruby-lang.org/en/downloads/"] if __import__("platform").system() == "Darwin" else ["sudo", "pacman", "-S", "--noconfirm", "ruby"],
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
            cmd = info["install_cmd"]
            is_gui_or_echo = cmd[0] in ["open", "xdg-open", "echo"]
            
            if platform.system() == "Windows":
                if is_gui_or_echo:
                    proc = subprocess.Popen(cmd, shell=True)
                else:
                    proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                if is_gui_or_echo:
                    if cmd[0] == "open" and platform.system() == "Linux":
                        cmd[0] = "xdg-open" # Translate open to xdg-open on Linux just in case
                    proc = subprocess.Popen(cmd)
                else:
                    # For terminal-based installs, create a temp script to ensure robust execution and TTY
                    import os
                    import stat
                    import shlex
                    
                    # Create a temporary script in the scratch directory
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    scratch_dir = os.path.join(os.path.dirname(current_dir), "scratch")
                    if not os.path.exists(scratch_dir):
                        os.makedirs(scratch_dir, exist_ok=True)
                    
                    script_path = os.path.join(scratch_dir, f"install_{backend_id}.sh")
                    
                    safe_cmd = shlex.join(cmd)
                    script_content = f"#!/bin/bash\n"
                    script_content += f"echo '--- VividPM Backend Installer ---'\n"
                    script_content += f"echo 'Target: {info['display_name']}'\n"
                    script_content += f"echo 'Command: {safe_cmd}'\n"
                    script_content += f"echo '---------------------------------'\n\n"
                    script_content += f"{safe_cmd}\n\n"
                    script_content += f"if [ $? -eq 0 ]; then\n"
                    script_content += f"    echo\n"
                    script_content += f"    echo 'SUCCESS: {info['display_name']} installed successfully.'\n"
                    script_content += f"    sleep 2\n"
                    script_content += f"else\n"
                    script_content += f"    echo\n"
                    script_content += f"    echo 'ERROR: Installation failed with exit code $?'\n"
                    script_content += f"    echo 'Press Enter to close this window...'\n"
                    script_content += f"    read\n"
                    script_content += f"fi\n"
                    
                    with open(script_path, "w") as f:
                        f.write(script_content)
                    
                    os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC)
                    
                    # Run the script in the terminal
                    proc = subprocess.Popen([terminal, "-e", script_path])
            
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
