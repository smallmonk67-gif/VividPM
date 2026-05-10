"""
action_runner.py — Wrappers for launching terminal commands.
Non-package actions (system update, local build, run app) live here.
Package install/remove is now handled by pkg_manager.py.
"""
import subprocess
import threading
import time
from vivid_gui import utils

TERMINAL = "alacritty"
AUR_HELPER = "yay"


def _run_in_terminal(cmd, on_finish=None, cwd=None):
    """Run a command in a terminal, call on_finish when the terminal closes."""
    import platform
    def worker():
        try:
            if platform.system() == "Windows":
                # For Windows, wrap the command in start cmd /k
                full_cmd = f"start cmd /k \"{' '.join(cmd)}\""
                subprocess.Popen(full_cmd, shell=True, cwd=cwd)
                time.sleep(1) # Command spawn delay, wait() doesn't work well with start cmd
                if on_finish:
                    on_finish()
            else:
                proc = subprocess.Popen(cmd, cwd=cwd)
                proc.wait()
                time.sleep(0.5)
                if on_finish:
                    on_finish()
        except Exception as e:
            print(f"[action_runner] error: {e}")
            utils.show_error("Execution Error", f"Failed to run command:\n{e}")

    threading.Thread(target=worker, daemon=True).start()


def update_system(on_finish=None):
    """Launch terminal to update the whole system (yay -Syu + flatpak update)."""
    # Run yay first, then flatpak update if available
    import shutil
    import platform
    cmds = []
    
    if platform.system() == "Windows":
        if shutil.which("winget"):
            cmds.append(["winget", "upgrade", "--all"])
        if shutil.which("choco"):
            cmds.append(["choco", "upgrade", "all", "-y"])
        if shutil.which("scoop"):
            cmds.append(["scoop", "update", "*"])
    else:
        if shutil.which(AUR_HELPER):
            cmds.append([TERMINAL, "-e", AUR_HELPER, "-Syu"])
        if shutil.which("flatpak"):
            cmds.append([TERMINAL, "-e", "flatpak", "update"])

    if not cmds:
        return

    def worker():
        for cmd in cmds:
            try:
                if platform.system() == "Windows":
                    full_cmd = f"start /wait cmd /c \"{' '.join(cmd)}\""
                    subprocess.call(full_cmd, shell=True)
                else:
                    proc = subprocess.Popen(cmd)
                    proc.wait()
            except Exception as e:
                print(f"[action_runner] update error: {e}")
                utils.show_error("Update Error", f"Failed to update system:\n{e}")
        time.sleep(0.5)
        if on_finish:
            on_finish()

    threading.Thread(target=worker, daemon=True).start()


def build_local_package(file_path, on_finish=None):
    """Launch terminal to build or install a local package file."""
    import os
    basename = os.path.basename(file_path)

    if basename == "PKGBUILD":
        # Arch: build from source
        dir_path = os.path.dirname(file_path)
        cmd = [TERMINAL, "--working-directory", dir_path, "-e", "makepkg", "-si"]
        _run_in_terminal(cmd, on_finish, cwd=dir_path)
    elif file_path.endswith((".pkg.tar.zst", ".pkg.tar.xz")):
        # Arch: install pre-built package
        cmd = [TERMINAL, "-e", "sudo", "pacman", "-U", file_path]
        _run_in_terminal(cmd, on_finish)
    elif file_path.endswith(".deb"):
        # Debian/Ubuntu
        cmd = [TERMINAL, "-e", "sudo", "dpkg", "-i", file_path]
        _run_in_terminal(cmd, on_finish)
    elif file_path.endswith(".rpm"):
        # Fedora/openSUSE — prefer dnf if available, fall back to rpm
        import shutil
        if shutil.which("dnf"):
            cmd = [TERMINAL, "-e", "sudo", "dnf", "install", "-y", file_path]
        elif shutil.which("zypper"):
            cmd = [TERMINAL, "-e", "sudo", "zypper", "install", file_path]
        else:
            cmd = [TERMINAL, "-e", "sudo", "rpm", "-i", file_path]
        _run_in_terminal(cmd, on_finish)
    elif file_path.endswith(".msi"):
        # Windows Installer
        cmd = ["msiexec", "/i", file_path]
        _run_in_terminal(cmd, on_finish)
    elif file_path.endswith(".exe"):
        # Windows Executable
        cmd = [file_path]
        _run_in_terminal(cmd, on_finish)
    else:
        print(f"[action_runner] Unknown package format: {file_path}")


def run_app(exec_cmd):
    """Launch a desktop application in the background."""
    import shlex
    import platform
    import os
    try:
        if platform.system() == "Windows":
            # On Windows, we can use 'start' to launch by name or path
            # shell=True is needed for the 'start' command
            subprocess.Popen(f'start "" "{exec_cmd}"', shell=True)
        else:
            cmd = shlex.split(exec_cmd)
            subprocess.Popen(cmd, start_new_session=True)
    except Exception as e:
        print(f"[action_runner] run_app error: {e}")
        utils.show_error("Launch Error", f"Failed to launch application:\n{e}")
