"""
flatpak_backend.py — Backend for Flatpak packages.
"""
import shutil
import subprocess
import threading

BACKEND_ID = "flatpak"
DISPLAY_NAME = "Flatpak"
COLOR = "#4a86cf"  # Flatpak blue


def is_available():
    return shutil.which("flatpak") is not None


def _parse_columns(output, cols):
    """Parse tab-separated flatpak output into list of dicts."""
    results = []
    for line in output.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        row = {}
        for i, col in enumerate(cols):
            row[col] = parts[i].strip() if i < len(parts) else ""
        results.append(row)
    return results


def search(query: str):
    """Search Flathub for packages matching query."""
    try:
        res = subprocess.run(
            ["flatpak", "search", "--columns=application,name,description,version,remotes", query],
            capture_output=True, text=True, timeout=15
        )
        if res.returncode != 0:
            return []
        if "No matches found" in res.stdout:
            return []
        rows = _parse_columns(res.stdout, ["app_id", "name", "description", "version", "remote"])
        installed_ids = {a["ID"] for a in get_installed()}
        out = []
        for r in rows:
            app_id = r.get("app_id", "")
            out.append({
                "Name": r.get("name") or app_id,
                "ID": app_id,
                "Version": r.get("version", ""),
                "Description": r.get("description", ""),
                "is_installed": app_id in installed_ids,
                "is_app": True,
                "Exec": f"flatpak run {app_id}",
                "backend": BACKEND_ID,
                "PackageName": app_id,
                "Remote": r.get("remote", "flathub"),
                "Icon": app_id,
            })
        return out
    except Exception as e:
        print(f"[flatpak] search error: {e}")
        return []


def get_installed():
    """Return all installed Flatpak apps."""
    try:
        res = subprocess.run(
            ["flatpak", "list", "--app", "--columns=application,name,description,version"],
            capture_output=True, text=True, timeout=10
        )
        if res.returncode != 0:
            return []
        rows = _parse_columns(res.stdout, ["app_id", "name", "description", "version"])
        out = []
        for r in rows:
            app_id = r.get("app_id", "")
            out.append({
                "Name": r.get("name") or app_id,
                "ID": app_id,
                "Version": r.get("version", ""),
                "Description": r.get("description", "Flatpak Application"),
                "is_installed": True,
                "is_app": True,
                "Exec": f"flatpak run {app_id}",
                "backend": BACKEND_ID,
                "PackageName": app_id,
                "Icon": app_id,
            })
        out.sort(key=lambda x: x["Name"].lower())
        return out
    except Exception as e:
        print(f"[flatpak] get_installed error: {e}")
        return []


def install(app_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "flatpak", "install", "flathub", app_id])


def remove(app_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "flatpak", "uninstall", app_id])


def get_info(app_id):
    """Return extended info dict from flatpak info (installed) or flatpak search."""
    info = {}
    try:
        # Try installed first
        res = subprocess.run(
            ["flatpak", "info", app_id], capture_output=True, text=True, timeout=10
        )
        if res.returncode == 0:
            for line in res.stdout.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    info[k.strip()] = v.strip()
            # Map to common keys
            info.setdefault("Depends On", "None (sandboxed)")
            info.setdefault("Required By", "None")
        return info
    except Exception as e:
        print(f"[flatpak] get_info error: {e}")
    return info
