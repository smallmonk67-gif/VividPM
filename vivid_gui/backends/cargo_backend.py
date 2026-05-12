"""
cargo_backend.py — Backend for Rust's Cargo package manager (Cross-platform).
"""
import subprocess
import shutil

import os

BACKEND_ID = "cargo"
DISPLAY_NAME = "Cargo"

def is_available():
    if shutil.which("cargo"): return True
    return os.path.exists(os.path.expanduser("~/.cargo/bin/cargo")) or os.path.exists("/usr/local/bin/cargo")

def get_installed():
    try:
        cmd = ["cargo", "install", "--list"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: return []
        apps = []
        # cargo install --list output:
        # package-name v1.2.3:
        #     binary1
        #     binary2
        for line in res.stdout.split("\n"):
            line = line.strip()
            if line and not line.startswith((">","<")) and ":" in line and " " in line.split(":")[0]:
                parts = line.split(":")[0].split(" ")
                if len(parts) >= 2:
                    name = parts[0]
                    version = parts[1].lstrip("v")
                    apps.append({
                        "Name": name,
                        "ID": name,
                        "Version": version,
                        "Description": "Installed via Cargo",
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
        cmd = ["cargo", "search", query, "--limit", "30"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0: return []
        apps = []
        for line in res.stdout.split("\n"):
            # format: crate_name = "version"    # description
            if "=" in line and '"' in line:
                name_part, rest = line.split("=", 1)
                name = name_part.strip()
                version = rest.split('"')[1] if '"' in rest else ""
                desc = rest.split("#")[1].strip() if "#" in rest else "Available via Cargo"
                
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
    return {"Type": "Cargo Crate", "AppID": pkg_id}
