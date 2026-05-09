"""
apt_backend.py — Backend for APT packages (Debian, Ubuntu, Mint, Pop!_OS, etc.)
"""
import shutil
import subprocess
import re

BACKEND_ID = "apt"
DISPLAY_NAME = "APT"
COLOR = "#E95420"  # Ubuntu orange


def is_available():
    return shutil.which("apt") is not None or shutil.which("apt-cache") is not None


def search(query: str):
    """Search available APT packages using apt-cache (fast, local)."""
    try:
        res = subprocess.run(
            ["apt-cache", "search", "--names-only", query],
            capture_output=True, text=True, timeout=15
        )
        if res.returncode != 0:
            return []

        installed = {p["ID"] for p in get_installed()}
        out = []
        for line in res.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(" - ", 1)
            pkg_id = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""
            out.append({
                "Name": pkg_id,
                "ID": pkg_id,
                "Version": "",
                "Description": desc,
                "is_installed": pkg_id in installed,
                "is_app": False,
                "Exec": "",
                "backend": BACKEND_ID,
                "PackageName": pkg_id,
                "Icon": pkg_id,
            })
        return out[:100]  # Cap at 100 to avoid flooding the UI
    except Exception as e:
        print(f"[apt] search error: {e}")
        return []


def get_installed():
    """Return all installed APT packages using dpkg-query."""
    try:
        res = subprocess.run(
            ["dpkg-query", "-W", "-f=${Package}\t${Version}\t${binary:Summary}\n"],
            capture_output=True, text=True, timeout=20
        )
        if res.returncode != 0:
            return []
        out = []
        for line in res.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            pkg_id = parts[0].strip()
            version = parts[1].strip() if len(parts) > 1 else ""
            desc = parts[2].strip() if len(parts) > 2 else ""
            out.append({
                "Name": pkg_id,
                "ID": pkg_id,
                "Version": version,
                "Description": desc,
                "is_installed": True,
                "is_app": False,
                "Exec": "",
                "backend": BACKEND_ID,
                "PackageName": pkg_id,
                "Icon": pkg_id,
            })
        out.sort(key=lambda x: x["Name"].lower())
        return out
    except Exception as e:
        print(f"[apt] get_installed error: {e}")
        return []


def install(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "apt", "install", "-y", pkg_id])


def remove(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "apt", "remove", "-y", pkg_id])


def get_info(pkg_id):
    """Return extended info from apt-cache show."""
    info = {}
    try:
        res = subprocess.run(
            ["apt-cache", "show", pkg_id],
            capture_output=True, text=True, timeout=10
        )
        if res.returncode == 0:
            for line in res.stdout.split("\n"):
                if ": " in line:
                    k, v = line.split(": ", 1)
                    k = k.strip()
                    if k in ("Depends", "Recommends", "Conflicts", "Maintainer",
                             "Homepage", "Section", "Priority", "Installed-Size"):
                        info[k] = v.strip()
            info["Depends On"] = info.pop("Depends", "None")
            # Reverse deps
            rdep_res = subprocess.run(
                ["apt-cache", "rdepends", "--installed", pkg_id],
                capture_output=True, text=True, timeout=10
            )
            if rdep_res.returncode == 0:
                rdeps = [l.strip() for l in rdep_res.stdout.split("\n")
                         if l.strip() and not l.strip().startswith(pkg_id)]
                info["Required By"] = ", ".join(rdeps[:10]) or "None"
            else:
                info["Required By"] = "None"
    except Exception as e:
        print(f"[apt] get_info error: {e}")
    return info
