"""
npm_backend.py — Backend for Node Package Manager (npm) (Cross-platform).
"""
import subprocess
import shutil
import json

import os

BACKEND_ID = "npm"
DISPLAY_NAME = "npm"

def is_available():
    if shutil.which("npm"): return True
    return os.path.exists("/usr/local/bin/npm") or os.path.exists("/opt/homebrew/bin/npm") or os.path.exists("/home/linuxbrew/.linuxbrew/bin/npm")

def get_installed():
    try:
        # Get globally installed npm packages
        cmd = ["npm", "ls", "-g", "--depth=0", "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        # npm might return non-zero if there are extraneous packages, but output might still be valid JSON
        if not res.stdout.strip(): return []
        
        data = json.loads(res.stdout)
        dependencies = data.get("dependencies", {})
        
        apps = []
        for name, info in dependencies.items():
            version = info.get("version", "")
            apps.append({
                "Name": name,
                "ID": name,
                "Version": version,
                "Description": "Global Node.js Package",
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
        cmd = ["npm", "search", query, "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if not res.stdout.strip(): return []
        
        data = json.loads(res.stdout)
        apps = []
        for item in data:
            name = item.get("name", "")
            version = item.get("version", "")
            desc = item.get("description", "Available via npm")
            
            if name:
                apps.append({
                    "Name": name,
                    "ID": name,
                    "Version": version,
                    "Description": desc,
                    "is_installed": False,
                    "is_app": False,
                    "backend": BACKEND_ID
                })
        return apps
    except Exception as e:
        print(f"[{BACKEND_ID}] search error: {e}")
        return []

def get_info(pkg_id):
    return {"Type": "npm Package", "AppID": pkg_id}
