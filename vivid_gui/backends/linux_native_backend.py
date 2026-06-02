"""
linux_native_backend.py — Backend for standalone Linux GUI applications (e.g. Chrome Web Apps).
These apps are typically discovered by scanning .desktop files in ~/.local/share/applications/ 
or /usr/share/applications/ that are not owned by the system package manager.
"""
import platform

BACKEND_ID = "linux_native"
DISPLAY_NAME = "Linux Apps"
COLOR = "#6b6b6b" # Gray/Neutral

def is_available():
    return platform.system() == "Linux"

def get_installed():
    # Actual scraping is handled by the primary package manager backend (e.g., pacman)
    # to avoid duplicate parsing and complex ownership resolution.
    return []

def search(query: str):
    return []

def get_info(pkg_id):
    return {"Type": "Linux Native Application", "AppID": pkg_id}

def install(pkg_id, terminal=None): pass
def remove(pkg_id, terminal=None): pass
