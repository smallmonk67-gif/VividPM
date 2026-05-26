"""
aur_backend.py — Backend for yay/paru/AUR packages.
"""
import os
import json
import shutil
import subprocess
import urllib.request
import urllib.parse

AUR_RPC_BASE_URL = "https://aur.archlinux.org/rpc/v5"

BACKEND_ID = "aur"
DISPLAY_NAME = "AUR"
COLOR = "#1793d1"  # Or another color, handled in ui_components

def get_helper():
    if shutil.which("yay"): return "yay"
    if shutil.which("paru"): return "paru"
    return None

def is_available():
    return get_helper() is not None

def get_installed_foreign_packages():
    try:
        res = subprocess.run(["pacman", "-Qmq"], capture_output=True, text=True, check=True)
        return set(res.stdout.strip().split("\n"))
    except Exception:
        return set()

def search(query: str):
    out = []
    helper = get_helper()
    if not helper: return out

    installed = get_installed_foreign_packages()

    try:
        url = f"{AUR_RPC_BASE_URL}/search/{urllib.parse.quote(query)}"
        with urllib.request.urlopen(url, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
            results = data.get("results", [])
            results.sort(key=lambda x: -x.get("Popularity", 0))
            
            for r in results:
                name = r.get("Name", "")
                
                out.append({
                    "Name": name,
                    "ID": name,
                    "Version": r.get("Version", ""),
                    "Description": r.get("Description", ""),
                    "is_installed": name in installed,
                    "is_app": False,
                    "Exec": "",
                    "backend": BACKEND_ID,
                    "PackageName": name,
                    "NumVotes": r.get("NumVotes", 0),
                    "Maintainer": r.get("Maintainer", "Orphan"),
                    "LastModified": r.get("LastModified"),
                    "Repository": "aur",
                })
    except Exception as e:
        print(f"[aur] search error: {e}")
        
    return out

def get_installed():
    # Local apps from AUR are discovered by pacman_backend.py 
    # and tagged with backend="aur".
    return []

def install(pkg_id, terminal="alacritty"):
    helper = get_helper()
    if helper:
        subprocess.Popen([terminal, "-e", helper, "-S", pkg_id])

def remove(pkg_id, terminal="alacritty"):
    helper = get_helper()
    if helper:
        # Both yay and paru support pacman-like syntax
        subprocess.Popen([terminal, "-e", helper, "-Rns", pkg_id])

def get_info(pkg_id):
    helper = get_helper()
    if not helper: return {}
    try:
        res = subprocess.run([helper, "-Si", pkg_id], capture_output=True, text=True)
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
