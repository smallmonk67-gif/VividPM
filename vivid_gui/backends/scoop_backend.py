"""
scoop_backend.py — Backend for Scoop.
"""
import shutil
import subprocess

BACKEND_ID = "scoop"
DISPLAY_NAME = "Scoop"
COLOR = "#ff8c00"  # DarkOrange

def is_available():
    return shutil.which("scoop") is not None

def get_installed():
    try:
        res = subprocess.run(
            ["scoop", "list"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if res.returncode != 0:
            return []
        
        apps = []
        lines = res.stdout.split("\n")
        # scoop list output: Name Version Source Updated Info
        if len(lines) < 3: return []
        
        for line in lines[2:]:
            line = line.strip()
            if not line: continue
            
            parts = [p.strip() for p in line.split("  ") if p.strip()]
            if len(parts) >= 2:
                name = parts[0]
                version = parts[1]
                
                apps.append({
                    "Name": name,
                    "ID": name,
                    "Version": version,
                    "Description": "Scoop Package",
                    "is_installed": True,
                    "is_app": True,
                    "Exec": "",
                    "backend": BACKEND_ID,
                    "PackageName": name,
                })
        return apps
    except Exception as e:
        print(f"[scoop] get_installed error: {e}")
        return []

def search(query: str):
    try:
        res = subprocess.run(
            ["scoop", "search", query],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if res.returncode != 0:
            return []

        apps = []
        lines = res.stdout.split("\n")
        
        # scoop search output format is varied, often shows bucket then list
        for line in lines:
            line = line.strip()
            if not line or "Results from" in line or line.startswith("'"): continue
            
            parts = [p.strip() for p in line.split("  ") if p.strip()]
            if len(parts) >= 2:
                name = parts[0]
                version = parts[1]
                
                # Cleanup name if it has bucket prefix like main/python -> python
                clean_name = name.split("/")[-1] if "/" in name else name

                apps.append({
                    "Name": clean_name,
                    "ID": clean_name,
                    "Version": version,
                    "Description": "Scoop Package",
                    "is_installed": False,
                    "is_app": False,
                    "Exec": "",
                    "backend": BACKEND_ID,
                    "PackageName": clean_name,
                })
        return apps
    except Exception as e:
        print(f"[scoop] search error: {e}")
        return []

def get_info(pkg_id):
    try:
        res = subprocess.run(
            ["scoop", "info", pkg_id],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
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

def install(pkg_id, terminal=None): pass
def remove(pkg_id, terminal=None): pass
