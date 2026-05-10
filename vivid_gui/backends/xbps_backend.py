"""
xbps_backend.py — Backend for XBPS packages (Void Linux)
"""
import shutil
import subprocess

BACKEND_ID = "xbps"
DISPLAY_NAME = "XBPS"
COLOR = "#478061"  # Void Linux teal


def is_available():
    return shutil.which("xbps-query") is not None


def search(query: str):
    """Search XBPS repository for packages."""
    try:
        res = subprocess.run(
            ["xbps-query", "-Rs", query],
            capture_output=True, text=True, timeout=20
        )
        # xbps returns exit 1 when nothing found, treat as empty
        installed_ids = {p["ID"] for p in get_installed()}
        out = []
        for line in res.stdout.strip().split("\n"):
            if not line.strip():
                continue
            # Format: "[*] pkgname-ver_rev  description"  (* = installed)
            is_inst = line.startswith("[*]")
            line = line.lstrip("[*] ").lstrip("[-] ").strip()
            parts = line.split(None, 1)
            if not parts:
                continue
            pkg_full = parts[0]  # pkgname-version_revision
            desc = parts[1] if len(parts) > 1 else ""
            # Strip version from name: split from last hyphen-digit
            import re
            m = re.match(r'^(.+?)-(\d.*)$', pkg_full)
            if m:
                pkg_id = m.group(1)
                version = m.group(2)
            else:
                pkg_id = pkg_full
                version = ""
            out.append({
                "Name": pkg_id,
                "ID": pkg_id,
                "Version": version,
                "Description": desc.strip(),
                "is_installed": is_inst or pkg_id in installed_ids,
                "is_app": False,
                "Exec": "",
                "backend": BACKEND_ID,
                "PackageName": pkg_id,
                "Icon": pkg_id,
            })
        return out[:100]
    except Exception as e:
        print(f"[xbps] search error: {e}")
        return []


def get_installed():
    """Return all installed XBPS packages."""
    try:
        res = subprocess.run(
            ["xbps-query", "-l"],
            capture_output=True, text=True, timeout=20
        )
        if res.returncode != 0:
            return []

        import re
        out = []
        for line in res.stdout.strip().split("\n"):
            if not line.strip():
                continue
            # Format: "ii pkgname-version_revision  description"
            parts = line.split(None, 2)
            if len(parts) < 2:
                continue
            pkg_full = parts[1]
            desc = parts[2] if len(parts) > 2 else ""
            m = re.match(r'^(.+?)-(\d.*)$', pkg_full)
            if m:
                pkg_id = m.group(1)
                version = m.group(2)
            else:
                pkg_id = pkg_full
                version = ""
            out.append({
                "Name": pkg_id,
                "ID": pkg_id,
                "Version": version,
                "Description": desc.strip(),
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
        print(f"[xbps] get_installed error: {e}")
        return []


def install(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "xbps-install", "-Sy", pkg_id])


def remove(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "xbps-remove", "-R", pkg_id])


def get_info(pkg_id):
    """Return extended info from xbps-query -RS."""
    info = {}
    try:
        res = subprocess.run(
            ["xbps-query", "-RS", pkg_id],
            capture_output=True, text=True, timeout=10
        )
        if res.returncode == 0:
            for line in res.stdout.split("\n"):
                if ": " in line:
                    k, v = line.split(": ", 1)
                    k = k.strip()
                    if k in ("pkgname", "version", "revision", "short_desc",
                             "maintainer", "homepage", "license", "run_depends"):
                        info[k] = v.strip()
            info["Depends On"] = info.pop("run_depends", "None")
            info["Required By"] = "None"
    except Exception as e:
        print(f"[xbps] get_info error: {e}")
    return info
