"""
dnf_backend.py — Backend for DNF packages (Fedora, RHEL, AlmaLinux, Rocky Linux, etc.)
"""
import shutil
import subprocess

BACKEND_ID = "dnf"
DISPLAY_NAME = "DNF"
COLOR = "#3C6EB4"  # Fedora blue


def is_available():
    return shutil.which("dnf") is not None


def search(query: str):
    """Search DNF repository for packages."""
    try:
        res = subprocess.run(
            ["dnf", "search", "--quiet", query],
            capture_output=True, text=True, timeout=30
        )
        if res.returncode != 0:
            return []

        installed = {p["ID"] for p in get_installed()}
        out = []
        for line in res.stdout.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("=") or line.startswith("Last"):
                continue
            # Format: "name.arch : description"
            if " : " not in line:
                continue
            pkg_full, desc = line.split(" : ", 1)
            # Strip architecture suffix (e.g. ".x86_64")
            pkg_id = pkg_full.split(".")[0].strip()
            out.append({
                "Name": pkg_id,
                "ID": pkg_id,
                "Version": "",
                "Description": desc.strip(),
                "is_installed": pkg_id in installed,
                "is_app": False,
                "Exec": "",
                "backend": BACKEND_ID,
                "PackageName": pkg_id,
                "Icon": pkg_id,
            })
        return out[:100]
    except Exception as e:
        print(f"[dnf] search error: {e}")
        return []


def get_installed():
    """Return all installed DNF/RPM packages."""
    try:
        res = subprocess.run(
            ["dnf", "list", "installed", "--quiet"],
            capture_output=True, text=True, timeout=20
        )
        if res.returncode != 0:
            return []

        out = []
        for line in res.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) < 2:
                continue
            # Format: name.arch  version  repo
            pkg_full = parts[0]
            version = parts[1] if len(parts) > 1 else ""
            pkg_id = pkg_full.split(".")[0]  # strip .arch
            out.append({
                "Name": pkg_id,
                "ID": pkg_id,
                "Version": version,
                "Description": "",
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
        print(f"[dnf] get_installed error: {e}")
        return []


def install(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "dnf", "install", "-y", pkg_id])


def remove(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "dnf", "remove", "-y", pkg_id])


def get_info(pkg_id):
    """Return extended info from dnf info."""
    info = {}
    try:
        res = subprocess.run(
            ["dnf", "info", pkg_id],
            capture_output=True, text=True, timeout=15
        )
        if res.returncode == 0:
            for line in res.stdout.split("\n"):
                if " : " in line:
                    k, v = line.split(" : ", 1)
                    k = k.strip()
                    if k in ("Name", "Version", "Release", "Architecture", "Size",
                             "Source", "Repository", "Summary", "URL", "License",
                             "Description", "Requires"):
                        info[k] = v.strip()
            info["Depends On"] = info.pop("Requires", "None")
            info["Required By"] = "None"
    except Exception as e:
        print(f"[dnf] get_info error: {e}")
    return info
