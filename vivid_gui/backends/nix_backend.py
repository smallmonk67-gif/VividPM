"""
nix_backend.py — Backend for Nix package manager (macOS and Linux).
"""
import subprocess
import shutil

BACKEND_ID = "nix"
DISPLAY_NAME = "Nix"

def is_available():
    return shutil.which("nix-env") is not None

def get_installed():
    try:
        cmd = ["nix-env", "-q"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: return []
        apps = []
        for line in res.stdout.split("\n"):
            name = line.strip()
            if name:
                apps.append({
                    "Name": name,
                    "ID": name,
                    "Version": "",
                    "Description": "Installed via Nix",
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
        cmd = ["nix-env", "-qaP", query]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: return []
        apps = []
        for line in res.stdout.split("\n"):
            parts = line.strip().split()
            if len(parts) >= 2:
                name = parts[0]
                version = parts[1]
                apps.append({
                    "Name": name.split(".")[-1] if "." in name else name,
                    "ID": name,
                    "Version": version,
                    "Description": "Available on Nix",
                    "is_installed": False,
                    "is_app": False,
                    "backend": BACKEND_ID
                })
        return apps
    except Exception as e:
        print(f"[{BACKEND_ID}] search error: {e}")
        return []

def get_info(pkg_id):
    return {"Type": "Nix Package", "AppID": pkg_id}
