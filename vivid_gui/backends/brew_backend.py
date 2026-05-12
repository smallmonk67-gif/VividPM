"""
brew_backend.py — Backend for Homebrew (macOS and Linux).
"""
import subprocess
import shutil

BACKEND_ID = "brew"
DISPLAY_NAME = "Homebrew"

def is_available():
    return shutil.which("brew") is not None

def get_installed():
    try:
        cmd = ["brew", "list", "--versions"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: return []
        apps = []
        for line in res.stdout.split("\n"):
            parts = line.strip().split()
            if len(parts) >= 2:
                name = parts[0]
                version = " ".join(parts[1:])
                apps.append({
                    "Name": name,
                    "ID": name,
                    "Version": version,
                    "Description": "Installed via Homebrew",
                    "is_installed": True,
                    "is_app": False,
                    "backend": BACKEND_ID
                })
        return apps
    except Exception as e:
        print(f"[{BACKEND_ID}] get_installed error: {e}")
        return []

def search(query: str):
    try:
        cmd = ["brew", "search", query]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: return []
        apps = []
        for line in res.stdout.split("\n"):
            name = line.strip()
            if name and "==>" not in name:
                apps.append({
                    "Name": name,
                    "ID": name,
                    "Version": "",
                    "Description": "Available on Homebrew",
                    "is_installed": False,
                    "is_app": False,
                    "backend": BACKEND_ID
                })
        return apps
    except Exception as e:
        print(f"[{BACKEND_ID}] search error: {e}")
        return []

def get_info(pkg_id):
    return {"Type": "Homebrew Package", "AppID": pkg_id}
