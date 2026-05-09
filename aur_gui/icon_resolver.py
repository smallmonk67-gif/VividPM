"""
icon_resolver.py — Utility to find and load Linux application icons.
"""
import os
import shutil
from PIL import Image, ImageTk
import customtkinter as ctk

ICON_CACHE = {}

# Common Linux icon search paths
SEARCH_PATHS = [
    os.path.expanduser("~/.local/share/icons"),
    "/usr/share/icons/hicolor/48x48/apps",
    "/usr/share/icons/hicolor/scalable/apps",
    "/usr/share/icons/hicolor/64x64/apps",
    "/usr/share/pixmaps",
    # Flatpak system and user paths
    "/var/lib/flatpak/exports/share/icons/hicolor/48x48/apps",
    "/var/lib/flatpak/exports/share/icons/hicolor/64x64/apps",
    "/var/lib/flatpak/exports/share/icons/hicolor/scalable/apps",
    os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor/48x48/apps"),
    os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor/64x64/apps"),
    # Snap paths
    "/var/lib/snapd/desktop/icons",
]

def resolve_icon_path(icon_name):
    """Try to find the absolute path for an icon name."""
    if not icon_name:
        return None
    
    # If it's already a path
    if os.path.isabs(icon_name) and os.path.exists(icon_name):
        return icon_name
    
    # Common extensions to try
    extensions = ["", ".png", ".svg", ".jpg", ".xpm"]
    
    # Search in common paths
    for base_path in SEARCH_PATHS:
        if not os.path.exists(base_path):
            continue
        for ext in extensions:
            full_path = os.path.join(base_path, icon_name + ext)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                return full_path
                
    return None

def get_icon_image(icon_name, size=(48, 48)):
    """Resolve, load and return a CTkImage for the given icon."""
    if not icon_name:
        return None
        
    cache_key = (icon_name, size)
    if cache_key in ICON_CACHE:
        return ICON_CACHE[cache_key]
    
    path = resolve_icon_path(icon_name)
    
    if path:
        try:
            img = Image.open(path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
            ICON_CACHE[cache_key] = ctk_img
            return ctk_img
        except Exception as e:
            print(f"[icon_resolver] Failed to load icon {icon_name}: {e}")
    
    return None

def get_placeholder_icon(size=(48, 48)):
    """Create a fully transparent image to clear 'ghost' icons while showing nothing."""
    cache_key = ("_transparent_", size)
    if cache_key in ICON_CACHE:
        return ICON_CACHE[cache_key]
    
    # Create 1x1 transparent image and resize it to 'size' for CTk
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
    ICON_CACHE[cache_key] = ctk_img
    return ctk_img
