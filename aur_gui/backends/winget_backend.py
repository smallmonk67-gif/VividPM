"""
winget_backend.py — Backend for Windows Package Manager (winget).
"""
import shutil
import subprocess

BACKEND_ID = "winget"
DISPLAY_NAME = "Winget"
COLOR = "#00a4ef"  # Windows blue

_INSTALLED_CACHE = None

def is_available():
    return shutil.which("winget") is not None

def get_installed():
    """Return installed packages via winget."""
    global _INSTALLED_CACHE
    if _INSTALLED_CACHE is not None:
        return _INSTALLED_CACHE
        
    try:
        # Note: winget list is often very slow and prompts for source agreements.
        # We use --accept-source-agreements to bypass.
        res = subprocess.run(
            ["winget", "list", "--accept-source-agreements"],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        if res.returncode != 0:
            return []
        
        apps = []
        lines = res.stdout.split("\n")
        # Winget output format is a table: Name, Id, Version, Available, Source
        if len(lines) < 3: return []
        
        # very basic parsing since column widths vary
        for line in lines[2:]:
            line = line.strip()
            if not line: continue
            
            # Approximate parsing by splitting on 2+ spaces
            parts = [p.strip() for p in line.split("  ") if p.strip()]
            if len(parts) >= 2:
                name = parts[0]
                pkg_id = parts[1]
                
                apps.append({
                    "Name": name,
                    "ID": pkg_id,
                    "Version": parts[2] if len(parts) > 2 else "",
                    "Description": f"Installed via Winget",
                    "is_installed": True,
                    "is_app": True,
                    "Exec": "",
                    "backend": BACKEND_ID,
                    "PackageName": pkg_id,
                })
        _INSTALLED_CACHE = apps
        return apps
    except Exception as e:
        print(f"[winget] get_installed error: {e}")
        return []

def search(query: str):
    """Search for packages."""
    try:
        res = subprocess.run(
            ["winget", "search", query, "--accept-source-agreements"],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        if res.returncode != 0:
            return []

        apps = []
        lines = res.stdout.split("\n")
        if len(lines) < 3: return []
        
        for line in lines[2:]:
            line = line.strip()
            if not line: continue
            
            parts = [p.strip() for p in line.split("  ") if p.strip()]
            if len(parts) >= 2:
                name = parts[0]
                pkg_id = parts[1]
                
                apps.append({
                    "Name": name,
                    "ID": pkg_id,
                    "Version": parts[2] if len(parts) > 2 else "",
                    "Description": f"Winget Package",
                    "is_installed": False, # Winget search doesn't clearly mark installed
                    "is_app": False,
                    "Exec": "",
                    "backend": BACKEND_ID,
                    "PackageName": pkg_id,
                })
        return apps
    except Exception as e:
        print(f"[winget] search error: {e}")
        return []

def get_info(pkg_id):
    """Get package details."""
    try:
        res = subprocess.run(
            ["winget", "show", "--id", pkg_id, "--accept-source-agreements"],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
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

def install(pkg_id, terminal=None):
    pass # handled by pkg_manager

def remove(pkg_id, terminal=None):
    pass # handled by pkg_manager
