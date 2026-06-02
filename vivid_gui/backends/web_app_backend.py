"""
web_app_backend.py — Backend for Progressive Web Apps (PWAs) and Chrome/Brave Web Apps.
These are typically launched via chrome/brave with --app-id or --app parameters.
"""
import platform

BACKEND_ID = "web_app"
DISPLAY_NAME = "Web Apps"
COLOR = "#06b6d4" # Modern Cyan

def is_available():
    # Available on any platform, since PWAs can run anywhere
    return True

def get_installed():
    return []

def search(query: str):
    return []

def get_info(pkg_id):
    return {"Type": "Progressive Web Application (PWA)", "AppID": pkg_id}

def install(pkg_id, terminal=None): pass
def remove(pkg_id, terminal=None): pass
