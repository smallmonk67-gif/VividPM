"""
icon_resolver.py — Utility to find and load Linux application icons.
"""
import os
import shutil
from PIL import Image, ImageTk
import customtkinter as ctk

import platform
import threading

ICON_CACHE = {}

# Global index: icon_name (lower case, no extension) -> absolute path
_ICON_INDEX = {}
_INDEX_LOCK = threading.Lock()

def _get_size_rank(path):
    # Higher rank = better icon size (scalable > large > small)
    ranks = {
        "scalable": 1000,
        "512x512": 512,
        "256x256": 256,
        "128x128": 128,
        "64x64": 64,
        "48x48": 48,
        "32x32": 32,
        "24x24": 24,
        "22x22": 22,
        "16x16": 16
    }
    path_lower = path.lower()
    base_rank = 0
    for key, rank in ranks.items():
        if key in path_lower:
            base_rank = rank
            break
            
    if base_rank == 0:
        # Try parsing sizes like "48" in "48/apps" or "512" in "512/apps"
        for part in path_lower.split(os.sep):
            if 'x' in part:
                try:
                    w, h = part.split('x', 1)
                    base_rank = int(w)
                    break
                except ValueError:
                    pass
            try:
                base_rank = int(part)
                break
            except ValueError:
                pass
                
    # If it's a pixmap (usually a large, high-quality fallback icon)
    if "pixmaps" in path_lower:
        base_rank = max(base_rank, 256)
        
    # Category adjustments:
    # Use split parts to match exact category names in the path to avoid false positives.
    path_parts = path_lower.split(os.sep)
    penalized_categories = {
        "actions", "animations", "categories", "devices", "emblems", 
        "emotes", "mimetypes", "places", "status"
    }
    
    category_bonus = 0
    if any(part in penalized_categories for part in path_parts):
        category_bonus = -50000
    elif "apps" in path_parts:
        category_bonus = 1000
    elif "pixmaps" in path_parts:
        category_bonus = 1000
        
    return base_rank + category_bonus

def _index_icons_worker():
    try:
        roots = [
            os.path.expanduser("~/.icons"),
            os.path.expanduser("~/.local/share/icons"),
            "/usr/share/icons",
            "/usr/local/share/icons",
            "/usr/share/pixmaps",
            "/var/lib/flatpak/exports/share/icons",
            os.path.expanduser("~/.local/share/flatpak/exports/share/icons"),
            "/var/lib/snapd/desktop/icons",
        ]
        
        temp_index = {}
        
        for root in roots:
            if not os.path.exists(root):
                continue
            for dirpath, _, filenames in os.walk(root):
                for fname in filenames:
                    name, ext = os.path.splitext(fname)
                    if ext.lower() in (".png", ".svg", ".xpm"):
                        name_lower = name.lower()
                        path = os.path.join(dirpath, fname)
                        rank = _get_size_rank(path)
                        
                        existing = temp_index.get(name_lower)
                        if not existing or rank > existing[0]:
                            temp_index[name_lower] = (rank, path)
                            
        with _INDEX_LOCK:
            for name_lower, (_, path) in temp_index.items():
                _ICON_INDEX[name_lower] = path
    except Exception as e:
        print(f"[icon_resolver] Background icon indexing failed: {e}")

def start_background_indexing():
    if platform.system() != "Windows":
        threading.Thread(target=_index_icons_worker, daemon=True).start()

# Common Linux icon search paths - Empty on Windows to avoid performance hits
if platform.system() == "Windows":
    SEARCH_PATHS = []
else:
    SEARCH_PATHS = [
        os.path.expanduser("~/.local/share/icons"),
        "/usr/share/pixmaps",
        "/var/lib/snapd/desktop/icons",
    ]
    
    # Priority order for icon sizes: scalable -> largest raster -> smallest raster
    for size in ["scalable", "512x512", "256x256", "128x128", "64x64", "48x48", "32x32", "24x24", "22x22", "16x16"]:
        SEARCH_PATHS.append(f"/usr/share/icons/hicolor/{size}/apps")
        SEARCH_PATHS.append(os.path.expanduser(f"~/.local/share/icons/hicolor/{size}/apps"))
        SEARCH_PATHS.append(f"/var/lib/flatpak/exports/share/icons/hicolor/{size}/apps")
        SEARCH_PATHS.append(os.path.expanduser(f"~/.local/share/flatpak/exports/share/icons/hicolor/{size}/apps"))

def resolve_icon_path(icon_name):
    """Try to find the absolute path for an icon name."""
    if not icon_name:
        return None
    
    # If it's already a path
    if os.path.isabs(icon_name) and os.path.exists(icon_name):
        return icon_name
        
    # Strip extension if provided to search by base name
    base_name, _ = os.path.splitext(icon_name)
    icon_name_lower = base_name.lower()
    
    # 1. Check indexed icons first
    with _INDEX_LOCK:
        if icon_name_lower in _ICON_INDEX:
            return _ICON_INDEX[icon_name_lower]
    
    # 2. Fallback to quick search if not in index yet
    extensions = ["", ".png", ".svg", ".jpg", ".xpm"]
    for base_path in SEARCH_PATHS:
        if not os.path.exists(base_path):
            continue
        for ext in extensions:
            full_path = os.path.join(base_path, icon_name + ext)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                return full_path
                
    return None

def is_generic_icon(icon_name):
    if not icon_name: return True
    generic_names = [
        "application-x-executable", "system-run", "unknown",
        "application-default-icon", "exec", "default", "package"
    ]
    return icon_name.lower() in generic_names

def _fetch_web_icon_async(icon_name, size, cache_key, on_ready):
    import urllib.request
    import urllib.error
    import json
    from io import BytesIO
    try:
        icon_url = None
        
        # 1. Search Flathub API (most accurate for desktop apps)
        try:
            search_url = "https://flathub.org/api/v2/search"
            # Use the full icon_name for Flathub to prevent losing context (e.g. org.cachyos.hello)
            data = json.dumps({"query": icon_name}).encode('utf-8')
            req = urllib.request.Request(search_url, data=data, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    hits = json.loads(resp.read().decode('utf-8')).get("hits", [])
                    if hits:
                        best_hit = hits[0]
                        hit_id = best_hit.get("app_id", "").lower()
                        hit_name = best_hit.get("name", "").lower()
                        query_lower = icon_name.lower()
                        # Strict validation: Only accept if the search hit loosely matches the query
                        if (query_lower in hit_id or query_lower in hit_name or 
                            hit_name in query_lower or hit_id in query_lower):
                            icon_url = best_hit.get("icon")
        except Exception:
            pass
            
        img_data = None
        
        # 2. Download from Flathub if found
        if icon_url:
            try:
                if icon_url.startswith("/"):
                    icon_url = "https://flathub.org" + icon_url
                req_icon = urllib.request.Request(icon_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_icon, timeout=4) as resp:
                    if resp.status == 200:
                        img_data = resp.read()
            except Exception:
                pass
                
        # 3. Fallback to Google Favicon guessing if Flathub failed
        if not img_data:
            base_name = icon_name.lower().split('.')[-1]
            domains_to_try = [f"{base_name}.com", f"{base_name}.org", f"{base_name}.io", f"{base_name}.net"]
            for domain in domains_to_try:
                url = f"https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://{domain}&size=128"
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        if resp.status == 200:
                            data = resp.read()
                            if len(data) > 1000:
                                img_data = data
                                break
                except Exception:
                    continue
                    
        # 4. Render and cache
        if img_data:
            img = Image.open(BytesIO(img_data))
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
            ICON_CACHE[cache_key] = ctk_img
            if on_ready:
                on_ready(ctk_img)
    except Exception as e:
        print(f"[icon_resolver] Web fetch failed for {icon_name}: {e}")
    finally:
        if hasattr(get_icon_image, "fetching") and cache_key in get_icon_image.fetching:
            get_icon_image.fetching.remove(cache_key)

def get_icon_image(icon_name, size=(48, 48), on_ready=None):
    """Resolve, load and return a CTkImage for the given icon."""
    if not icon_name:
        return None
        
    cache_key = (icon_name, size)
    if cache_key in ICON_CACHE:
        return ICON_CACHE[cache_key]
    
    path = resolve_icon_path(icon_name)
    
    if path:
        try:
            if path.lower().endswith('.svg'):
                import subprocess
                from io import BytesIO
                res = subprocess.run(["rsvg-convert", "-w", str(size[0]), "-h", str(size[1]), path], capture_output=True)
                if res.returncode == 0 and res.stdout:
                    img = Image.open(BytesIO(res.stdout))
                else:
                    raise Exception(f"rsvg-convert failed or not found for {path}")
            else:
                img = Image.open(path)
                
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
            ICON_CACHE[cache_key] = ctk_img
            return ctk_img
        except Exception as e:
            print(f"[icon_resolver] Failed to load icon {icon_name}: {e}")
            
    # Local failed, try web if enabled and valid
    from vivid_gui.config_manager import config_manager
    import threading
    if config_manager.get("fetch_web_icons", True) and not is_generic_icon(icon_name) and on_ready:
        if getattr(get_icon_image, "fetching", None) is None:
            get_icon_image.fetching = set()
            
        if cache_key not in get_icon_image.fetching:
            get_icon_image.fetching.add(cache_key)
            threading.Thread(
                target=_fetch_web_icon_async, 
                args=(icon_name, size, cache_key, on_ready), 
                daemon=True
            ).start()
    
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

# Start indexing all system icons in a background thread on startup
start_background_indexing()
