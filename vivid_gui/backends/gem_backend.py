"""
gem_backend.py — Backend for RubyGems (Cross-platform).
"""
import subprocess
import shutil

BACKEND_ID = "gem"
DISPLAY_NAME = "RubyGems"

def is_available():
    return shutil.which("gem") is not None

def get_installed():
    try:
        cmd = ["gem", "list", "--local"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: return []
        apps = []
        for line in res.stdout.split("\n"):
            line = line.strip()
            # gem list output: rails (7.0.4, 6.1.7)
            if line and " (" in line and line.endswith(")"):
                name = line.split(" (")[0]
                version = line.split(" (")[1].strip(")")
                apps.append({
                    "Name": name,
                    "ID": name,
                    "Version": version,
                    "Description": "Installed via RubyGems",
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
        cmd = ["gem", "search", query, "--remote"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: return []
        apps = []
        for line in res.stdout.split("\n"):
            line = line.strip()
            if line and " (" in line and line.endswith(")"):
                name = line.split(" (")[0]
                version = line.split(" (")[1].strip(")")
                apps.append({
                    "Name": name,
                    "ID": name,
                    "Version": version,
                    "Description": "Available via RubyGems",
                    "is_installed": False,
                    "is_app": False,
                    "backend": BACKEND_ID
                })
        return apps
    except Exception as e:
        print(f"[{BACKEND_ID}] search error: {e}")
        return []

def get_info(pkg_id):
    return {"Type": "Ruby Gem", "AppID": pkg_id}
