"""
choco_backend.py — Backend for Chocolatey.
"""
import shutil
import subprocess

BACKEND_ID = "choco"
DISPLAY_NAME = "Chocolatey"
COLOR = "#8b4513"  # SaddleBrown

def is_available():
    return shutil.which("choco") is not None

def get_installed():
    try:
        res = subprocess.run(
            ["choco", "list", "-l", "-r"],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        if res.returncode != 0:
            return []
        
        apps = []
        for line in res.stdout.split("\n"):
            line = line.strip()
            if not line or "|" not in line: continue
            
            name, version = line.split("|", 1)
            apps.append({
                "Name": name,
                "ID": name,
                "Version": version,
                "Description": "Chocolatey Package",
                "is_installed": True,
                "is_app": True,
                "Exec": "",
                "backend": BACKEND_ID,
                "PackageName": name,
            })
        return apps
    except Exception as e:
        print(f"[choco] get_installed error: {e}")
        return []

def search(query: str):
    try:
        res = subprocess.run(
            ["choco", "search", query, "-r"],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        if res.returncode != 0:
            return []

        apps = []
        for line in res.stdout.split("\n"):
            line = line.strip()
            if not line or "|" not in line: continue
            
            name, version = line.split("|", 1)
            apps.append({
                "Name": name,
                "ID": name,
                "Version": version,
                "Description": "Chocolatey Package",
                "is_installed": False,
                "is_app": False,
                "Exec": "",
                "backend": BACKEND_ID,
                "PackageName": name,
            })
        return apps
    except Exception as e:
        print(f"[choco] search error: {e}")
        return []

def get_info(pkg_id):
    try:
        res = subprocess.run(
            ["choco", "info", pkg_id],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        if res.returncode == 0:
            return {"Info": res.stdout.strip()}
    except Exception:
        pass
    return {}

def install(pkg_id, terminal=None): pass
def remove(pkg_id, terminal=None): pass
