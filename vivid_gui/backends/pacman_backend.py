"""
pacman_backend.py — Backend for pacman/yay/AUR packages.
"""
import os
import re
import json
import shutil
import subprocess
import threading
import urllib.request
import urllib.parse

CACHE_FILE = "/tmp/vividpm_apps_cache.json"
AUR_RPC_BASE_URL = "https://aur.archlinux.org/rpc/v5"

BACKEND_ID = "pacman"
DISPLAY_NAME = "pacman"
COLOR = "#1793d1"  # Arch blue


def is_available():
    return shutil.which("pacman") is not None


def _load_cache():
    path = os.path.realpath(CACHE_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_cache(cache):
    path = os.path.realpath(CACHE_FILE)
    try:
        with open(path, "w") as f:
            json.dump(cache, f)
    except Exception:
        pass


def get_installed_package_names():
    """Returns a set of installed pacman package names."""
    try:
        res = subprocess.run(["pacman", "-Qq"], capture_output=True, text=True, check=True)
        return set(res.stdout.strip().split("\n"))
    except Exception:
        return set()


def search(query: str):
    """Search official repos and AUR for packages matching query."""
    out = []
    installed = get_installed_package_names()
    
    # 1. Search Official Repos (pacman -Ss)
    try:
        res = subprocess.run(["pacman", "-Ss", query], capture_output=True, text=True)
        if res.returncode == 0:
            lines = res.stdout.strip().split("\n")
            # pacman -Ss output comes in pairs: "repo/name version [installed]" followed by "desc"
            for i in range(0, len(lines), 2):
                header = lines[i]
                desc = lines[i+1] if i+1 < len(lines) else ""
                
                # Parse "extra/firefox 125.0.3-1 [installed]"
                parts = header.split()
                if not parts: continue
                
                repo_name = parts[0] # "extra/firefox"
                repo, _, name = repo_name.partition("/")
                if not name: # sometimes just "name"
                    name = repo
                
                version = parts[1] if len(parts) > 1 else ""
                is_installed = "[installed]" in header or name in installed
                
                out.append({
                    "Name": name,
                    "ID": name,
                    "Version": version,
                    "Description": desc.strip(),
                    "is_installed": is_installed,
                    "is_app": False,
                    "Exec": "",
                    "backend": BACKEND_ID,
                    "PackageName": name,
                    "Repository": repo,
                })
    except Exception as e:
        print(f"[pacman] repo search error: {e}")

    return out


def get_installed():
    apps = []
    seen_names = set()
    cache = _load_cache()
    cache_updated = False
    
    foreign_pkgs = set()
    try:
        res = subprocess.run(["pacman", "-Qmq"], capture_output=True, text=True, check=True)
        foreign_pkgs = set(res.stdout.strip().split("\n"))
    except Exception:
        pass

    dirs = ["/usr/share/applications", os.path.expanduser("~/.local/share/applications")]
    for d in dirs:
        if not os.path.exists(d):
            continue
        for fname in os.listdir(d):
            if not fname.endswith(".desktop"):
                continue
            path = os.path.join(d, fname)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    name, exec_cmd, desc, icon = "", "", "", ""
                    in_entry = False
                    for line in f:
                        line = line.strip()
                        if line == "[Desktop Entry]":
                            in_entry = True
                        elif line.startswith("["):
                            in_entry = False
                        if in_entry:
                            if line.startswith("Name=") and not name:
                                name = line[5:]
                            elif line.startswith("Exec=") and not exec_cmd:
                                exec_cmd = line[5:]
                            elif line.startswith("Comment=") and not desc:
                                desc = line[8:]
                            elif line.startswith("Icon=") and not icon:
                                icon = line[5:]
                            elif line.lower().startswith("nodisplay=true"):
                                name = ""
                                break

                if not name or not exec_cmd or name in seen_names:
                    continue

                exec_clean = re.sub(r"%[a-zA-Z]", "", exec_cmd).strip()
                binary = exec_clean.split()[0] if exec_clean else ""
                if not binary:
                    continue
                if os.path.isabs(binary):
                    if not os.path.exists(binary):
                        continue
                else:
                    if shutil.which(binary) is None:
                        continue

                seen_names.add(name)

                pkg_name = cache.get(path)
                if pkg_name is None:
                    if path.startswith("/usr/share/applications"):
                        try:
                            res = subprocess.run(
                                ["pacman", "-Qoq", path], capture_output=True, text=True
                            )
                            if res.returncode == 0:
                                pkg_name = res.stdout.strip()
                                cache[path] = pkg_name
                                cache_updated = True
                        except Exception:
                            pass

                pkg_name_final = pkg_name or name
                is_aur = pkg_name_final in foreign_pkgs

                apps.append({
                    "Name": name,
                    "ID": pkg_name_final,
                    "Version": "",
                    "Description": desc or "Installed Application",
                    "is_installed": True,
                    "is_app": True,
                    "Exec": exec_clean,
                    "backend": "aur" if is_aur else BACKEND_ID,
                    "PackageName": pkg_name_final,
                    "Path": path,
                    "Icon": icon,
                })
            except Exception:
                pass

    if cache_updated:
        _save_cache(cache)

    apps.sort(key=lambda x: x["Name"].lower())
    return apps


def install(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "pacman", "-S", pkg_id])


def remove(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "pacman", "-Rns", pkg_id])


def get_info(pkg_id):
    """Return extended info dict from pacman -Qi."""
    try:
        res = subprocess.run(["pacman", "-Qi", pkg_id], capture_output=True, text=True)
        if res.returncode == 0:
            info = {}
            for line in res.stdout.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    info[k.strip()] = v.strip()
            return info
    except Exception:
        pass
    return {}
