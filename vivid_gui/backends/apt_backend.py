"""
apt_backend.py — Backend for APT packages (Debian, Ubuntu, Mint, Pop!_OS, etc.)
"""
import shutil
import subprocess
import re

BACKEND_ID = "apt"
DISPLAY_NAME = "APT"
COLOR = "#E95420"  # Ubuntu orange

import time

_installed_cache = None
_cache_time = 0


def is_available():
    return shutil.which("apt") is not None or shutil.which("apt-cache") is not None


def get_installed_names(use_cache=True):
    """Return a set of all installed APT package names quickly using dpkg-query."""
    global _installed_cache, _cache_time
    now = time.time()
    if use_cache and _installed_cache is not None and (now - _cache_time) < 10:
        return _installed_cache

    try:
        res = subprocess.run(
            ["dpkg-query", "-W", "-f=${db:Status-Status}\t${Package}\n"],
            capture_output=True, text=True, timeout=5
        )
        if res.returncode == 0:
            names = set()
            for line in res.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split("\t")
                if len(parts) >= 2 and parts[0].strip() == "installed":
                    names.add(parts[1].strip())
            _installed_cache = names
            _cache_time = now
            return _installed_cache
    except Exception as e:
        print(f"[apt] get_installed_names error: {e}")
    return _installed_cache if _installed_cache is not None else set()


def search(query: str):
    """Search available APT packages using apt-cache (fast, local)."""
    try:
        res = subprocess.run(
            ["apt-cache", "search", "--names-only", query],
            capture_output=True, text=True, timeout=15
        )
        if res.returncode != 0:
            return []

        installed = get_installed_names()
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
            ["dpkg-query", "-W", "-f=${db:Status-Status}\t${Package}\t${Version}\t${binary:Summary}\n"],
            capture_output=True, text=True, timeout=20
        )
        if res.returncode != 0:
            return []
        out = []
        for line in res.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            status = parts[0].strip()
            if status != "installed":
                continue
            pkg_id = parts[1].strip()
            version = parts[2].strip()
            desc = parts[3].strip()
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
