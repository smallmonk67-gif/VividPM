"""
macports_backend.py — Backend for MacPorts (macOS).
"""
import subprocess
import shutil

BACKEND_ID = "macports"
DISPLAY_NAME = "MacPorts"

def is_available():
    return shutil.which("port") is not None

def get_installed():
    try:
        cmd = ["port", "installed"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: return []
        apps = []
        for line in res.stdout.split("\n"):
            line = line.strip()
            if not line or line.startswith("The following ports"): continue
            # Format: appname @version_variant (active)
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                version = parts[1].lstrip("@")
                apps.append({
                    "Name": name,
                    "ID": name,
                    "Version": version,
                    "Description": "Installed via MacPorts",
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
        cmd = ["port", "search", query]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: return []
        apps = []
        for line in res.stdout.split("\n"):
            line = line.strip()
            if not line or line.startswith("Warning:") or "@" in line: continue
            # Very basic parse, first word is usually the port name in search
            parts = line.split()
            if parts:
                name = parts[0]
                apps.append({
                    "Name": name,
                    "ID": name,
                    "Version": "",
                    "Description": "Available on MacPorts",
                    "is_installed": False,
                    "is_app": False,
                    "backend": BACKEND_ID
                })
        return apps
    except Exception as e:
        print(f"[{BACKEND_ID}] search error: {e}")
        return []

def get_info(pkg_id):
    return {"Type": "MacPorts Package", "AppID": pkg_id}
