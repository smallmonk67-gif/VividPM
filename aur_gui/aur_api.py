import urllib.request
import urllib.parse
import json
import subprocess
import threading
import os

AUR_RPC_BASE_URL = "https://aur.archlinux.org/rpc/v5"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "apps_cache.json")

def _load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def _save_cache(cache):
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except:
        pass

def search_packages(query: str):
    """Search for packages using the AUR RPC API."""
    try:
        url = f"{AUR_RPC_BASE_URL}/search/{urllib.parse.quote(query)}"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            results = data.get("results", [])
            
            # Sort by popularity or exact match
            results.sort(key=lambda x: (-x.get("Popularity", 0)))
            return results
    except Exception as e:
        print(f"Error searching AUR: {e}")
        return []

def get_installed_packages():
    """Returns a set of installed package names."""
    try:
        result = subprocess.run(
            ["pacman", "-Qq"],
            capture_output=True, text=True, check=True
        )
        return set(result.stdout.strip().split("\n"))
    except Exception:
        return set()

def fetch_package_info(package_names):
    """Fetch detailed info for multiple packages."""
    if not package_names:
        return []
    
    # AUR RPC handles multiple info args via ?arg[]=pkg1&arg[]=pkg2
    query_string = "&".join([f"arg[]={urllib.parse.quote(pkg)}" for pkg in package_names])
    url = f"{AUR_RPC_BASE_URL}/info/?{query_string}"
    
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get("results", [])
    except Exception as e:
        print(f"Error fetching package info: {e}")
        return []

def async_search(query, callback):
    """Run search in a background thread so UI doesn't freeze."""
    def worker():
        results = search_packages(query)
        installed = get_installed_packages()
        
        # Mark installed status
        for r in results:
            r['is_installed'] = r.get('Name') in installed
            
        callback(results)
        
    threading.Thread(target=worker, daemon=True).start()

def get_local_apps():
    """Parse .desktop files to get a list of runnable installed apps."""
    import os
    apps = []
    seen_names = set()
    cache = _load_cache()
    cache_updated = False
    
    dirs = ['/usr/share/applications', os.path.expanduser('~/.local/share/applications')]
    for d in dirs:
        if not os.path.exists(d): continue
        for f in os.listdir(d):
            if not f.endswith('.desktop'): continue
            path = os.path.join(d, f)
            if not os.path.isfile(path): continue
            
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                    name, exec_cmd, desc = '', '', ''
                    in_desktop_entry = False
                    for line in file:
                        line = line.strip()
                        if line == '[Desktop Entry]': 
                            in_desktop_entry = True
                        elif line.startswith('['): 
                            in_desktop_entry = False
                        
                        if in_desktop_entry:
                            if line.startswith('Name=') and not name: name = line[5:]
                            elif line.startswith('Exec=') and not exec_cmd: exec_cmd = line[5:]
                            elif line.startswith('Comment=') and not desc: desc = line[8:]
                            elif line.startswith('NoDisplay=true') or line.startswith('NoDisplay=True'):
                                name = ''
                                break # Skip hidden apps
                    
                    if name and exec_cmd and name not in seen_names:
                        seen_names.add(name)
                        # Clean up exec_cmd by removing %U, %f etc.
                        import re
                        exec_clean = re.sub(r'%[a-zA-Z]', '', exec_cmd).strip()
                        
                        # Check if the executable actually exists
                        import shutil
                        binary = exec_clean.split()[0] if exec_clean else ""
                        binary_exists = False
                        if binary:
                            if os.path.isabs(binary):
                                binary_exists = os.path.exists(binary)
                            else:
                                binary_exists = shutil.which(binary) is not None

                        if not binary_exists:
                            name = ''
                            continue
                        
                        # Try to find the package owner for removal (use cache)
                        pkg_name = cache.get(path)
                        if pkg_name is None:
                            if path.startswith('/usr/share/applications'):
                                try:
                                    res = subprocess.run(["pacman", "-Qoq", path], capture_output=True, text=True)
                                    if res.returncode == 0:
                                        pkg_name = res.stdout.strip()
                                        cache[path] = pkg_name
                                        cache_updated = True
                                except Exception:
                                    pass

                        apps.append({
                            'Name': name,
                            'PackageName': pkg_name or name, # Fallback to name if not found
                            'Version': '',
                            'Description': desc or 'Installed Application',
                            'is_installed': True,
                            'is_app': True,
                            'Exec': exec_clean,
                            'Path': path
                        })
            except Exception:
                pass
    
    if cache_updated:
        _save_cache(cache)
                
    apps.sort(key=lambda x: x['Name'].lower())
    return apps

def get_extended_info(package_name):
    """Fetch extended info using pacman or AUR helper."""
    # We need to know which helper is used. Since action_runner uses AUR_HELPER
    # we'll just use 'yay' or 'paru' directly or assume it's set.
    # For now, let's just use 'yay' as a default if it's there.
    helper = 'yay'
    try:
        # Try pacman -Qi (for installed)
        res = subprocess.run(["pacman", "-Qi", package_name], capture_output=True, text=True)
        if res.returncode != 0:
            # Not installed, try AUR helper
            res = subprocess.run([helper, "-Si", package_name], capture_output=True, text=True)
        
        if res.returncode == 0:
            info = {}
            for line in res.stdout.split('\n'):
                if ':' in line:
                    parts = line.split(':', 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                    info[key] = val
            return info
    except Exception:
        pass
    return {}

def async_fetch_extended_info(package_name, callback):
    """Run extended info fetch in a background thread."""
    def worker():
        info = get_extended_info(package_name)
        callback(info)
        
    threading.Thread(target=worker, daemon=True).start()
