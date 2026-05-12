"""
fink_backend.py — Backend for Fink (macOS).
"""
import subprocess
import shutil

BACKEND_ID = "fink"
DISPLAY_NAME = "Fink"

def is_available():
    return shutil.which("fink") is not None

def get_installed():
    try:
        cmd = ["fink", "list", "-i"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: return []
        apps = []
        for line in res.stdout.split("\n"):
            parts = line.strip().split()
            # Fink list format typically: [flag] package_name version description
            if len(parts) >= 3 and parts[0] == "i":
                name = parts[1]
                version = parts[2]
                apps.append({
                    "Name": name,
                    "ID": name,
                    "Version": version,
                    "Description": "Installed via Fink",
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
        cmd = ["fink", "list", query]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: return []
        apps = []
        for line in res.stdout.split("\n"):
            parts = line.strip().split()
            if len(parts) >= 3:
                # If it's not installed, the first column might be empty or 'p' or something else
                # We skip lines that don't look like package lines
                if len(parts[0]) <= 1:
                    name = parts[1]
                    version = parts[2]
                    apps.append({
                        "Name": name,
                        "ID": name,
                        "Version": version,
                        "Description": "Available on Fink",
                        "is_installed": parts[0] == "i",
                        "is_app": False,
                        "backend": BACKEND_ID
                    })
        return apps
    except Exception as e:
        print(f"[{BACKEND_ID}] search error: {e}")
        return []

def get_info(pkg_id):
    return {"Type": "Fink Package", "AppID": pkg_id}
