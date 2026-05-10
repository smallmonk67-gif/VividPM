"""
snap_backend.py — Backend for Snap packages.
"""
import shutil
import subprocess

BACKEND_ID = "snap"
DISPLAY_NAME = "Snap"
COLOR = "#e95420"  # Snapcraft orange


def is_available():
    return shutil.which("snap") is not None


def search(query: str):
    """Search Snap store for packages."""
    try:
        res = subprocess.run(
            ["snap", "find", query],
            capture_output=True, text=True, timeout=15
        )
        if res.returncode != 0:
            return []
        installed_ids = {a["ID"] for a in get_installed()}
        out = []
        lines = res.stdout.strip().split("\n")
        # Skip header line
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 2:
                continue
            pkg_id = parts[0]
            version = parts[1] if len(parts) > 1 else ""
            desc = " ".join(parts[3:]) if len(parts) > 3 else ""
            out.append({
                "Name": pkg_id,
                "ID": pkg_id,
                "Version": version,
                "Description": desc,
                "is_installed": pkg_id in installed_ids,
                "is_app": True,
                "Exec": pkg_id,
                "backend": BACKEND_ID,
                "PackageName": pkg_id,
                "Icon": pkg_id,
            })
        return out
    except Exception as e:
        print(f"[snap] search error: {e}")
        return []


def get_installed():
    """Return all installed Snap packages."""
    try:
        res = subprocess.run(
            ["snap", "list"],
            capture_output=True, text=True, timeout=10
        )
        if res.returncode != 0:
            return []
        out = []
        lines = res.stdout.strip().split("\n")
        for line in lines[1:]:  # skip header
            parts = line.split()
            if len(parts) < 2:
                continue
            pkg_id = parts[0]
            version = parts[1]
            out.append({
                "Name": pkg_id,
                "ID": pkg_id,
                "Version": version,
                "Description": "Snap Package",
                "is_installed": True,
                "is_app": True,
                "Exec": pkg_id,
                "backend": BACKEND_ID,
                "PackageName": pkg_id,
                "Icon": pkg_id,
            })
        out.sort(key=lambda x: x["Name"].lower())
        return out
    except Exception as e:
        print(f"[snap] get_installed error: {e}")
        return []


def install(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "snap", "install", pkg_id])


def remove(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "snap", "remove", pkg_id])


def get_info(pkg_id):
    info = {}
    try:
        res = subprocess.run(["snap", "info", pkg_id], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            for line in res.stdout.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    info[k.strip()] = v.strip()
        info.setdefault("Depends On", "None (sandboxed)")
        info.setdefault("Required By", "None")
    except Exception as e:
        print(f"[snap] get_info error: {e}")
    return info
