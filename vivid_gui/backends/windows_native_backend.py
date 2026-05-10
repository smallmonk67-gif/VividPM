"""
windows_native_backend.py — Backend for Windows Start Menu apps.
Provides launchable shortcuts for installed software.
"""
import subprocess
import platform
import shutil

BACKEND_ID = "windows_native"
DISPLAY_NAME = "Windows Apps"
COLOR = "#0078d4" # Microsoft Blue

def is_available():
    return platform.system() == "Windows" and shutil.which("powershell") is not None

def get_installed():
    """Return installed apps from Windows Start Menu via PowerShell."""
    try:
        # Get-StartApps returns Name and AppID
        cmd = ["powershell", "-NoProfile", "-Command", "Get-StartApps | ConvertTo-Json"]
        res = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        if res.returncode != 0:
            return []
            
        import json
        data = json.loads(res.stdout)
        
        # PowerShell might return a single object or a list
        if isinstance(data, dict):
            data = [data]
            
        apps = []
        for item in data:
            name = item.get("Name", "Unknown")
            app_id = item.get("AppID", "")
            
            if not name or not app_id: continue
            
            apps.append({
                "Name": name,
                "ID": app_id,
                "Version": "",
                "Description": "Windows Application",
                "is_installed": True,
                "is_app": True,
                "Exec": f"shell:AppsFolder\\{app_id}",
                "backend": BACKEND_ID,
                "PackageName": app_id,
            })
        return apps
    except Exception as e:
        print(f"[windows_native] get_installed error: {e}")
        return []

def search(query: str):
    # This backend only shows installed apps, doesn't search a store
    return []

def get_info(pkg_id):
    return {"Type": "Windows Native Application", "AppID": pkg_id}

def install(pkg_id, terminal=None): pass
def remove(pkg_id, terminal=None): pass
