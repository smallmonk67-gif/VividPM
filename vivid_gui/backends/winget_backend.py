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
            capture_output=True, text=True, encoding="utf-8", errors="replace", 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if res.returncode != 0:
            return []
        
        apps = []
        lines = [line for line in res.stdout.split("\n") if line.strip()]
        if len(lines) < 2: return []
        
        header = lines[0]
        # Find column start positions
        try:
            id_start = header.index("Id")
            ver_start = header.index("Version")
        except ValueError:
            id_start, ver_start = 30, 70 # Fallback

        for line in lines:
            if len(line) < id_start: continue
            if line.strip().replace("-", "").replace(" ", "") == "": continue
            
            name = line[:id_start].strip()
            pkg_id = line[id_start:ver_start].strip() if len(line) > ver_start else line[id_start:].strip()
            
            if name == "Name" and pkg_id == "Id": continue # Skip header line
            version = line[ver_start:].split()[0] if len(line) > ver_start and line[ver_start:].strip() else ""

            if not name or not pkg_id: continue
            
            apps.append({
                "Name": name,
                "ID": pkg_id,
                "Version": version,
                "Description": f"Installed via Winget",
                "is_installed": True,
                "is_app": True,
                "Exec": "", # We'll try to launch by name
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
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if res.returncode != 0:
            return []

        apps = []
        lines = [line for line in res.stdout.split("\n") if line.strip()]
        if len(lines) < 2: return []
        
        header = lines[0]
        try:
            id_start = header.index("Id")
            ver_start = header.index("Version")
        except ValueError:
            id_start, ver_start = 30, 70

        for line in lines:
            if len(line) < id_start: continue
            if line.strip().replace("-", "").replace(" ", "") == "": continue
            
            name = line[:id_start].strip()
            pkg_id = line[id_start:ver_start].strip() if len(line) > ver_start else line[id_start:].strip()
            
            if name == "Name" and pkg_id == "Id": continue # Skip header line
            version = line[ver_start:].split()[0] if len(line) > ver_start and line[ver_start:].strip() else ""

            if not name or not pkg_id: continue
                
            apps.append({
                "Name": name,
                "ID": pkg_id,
                "Version": version,
                "Description": f"Winget Package",
                "is_installed": False,
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

def install(pkg_id, terminal=None):
    pass # handled by pkg_manager

def remove(pkg_id, terminal=None):
    pass # handled by pkg_manager
