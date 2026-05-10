"""
apk_backend.py — Backend for APK packages (Alpine Linux)
"""
import shutil
import subprocess

BACKEND_ID = "apk"
DISPLAY_NAME = "APK"
COLOR = "#0D597F"  # Alpine blue


def is_available():
    return shutil.which("apk") is not None


def search(query: str):
    """Search Alpine APK repositories."""
    try:
        res = subprocess.run(
            ["apk", "search", "--description", query],
            capture_output=True, text=True, timeout=15
        )
        if res.returncode != 0:
            return []

        installed_ids = {p["ID"] for p in get_installed()}
        out = []
        for line in res.stdout.strip().split("\n"):
            if not line.strip():
                continue
            # Format: pkgname-version description
            parts = line.split(None, 1)
            pkg_full = parts[0]
            desc = parts[1] if len(parts) > 1 else ""
            # Strip version: split from last hyphen-digit
            import re
            m = re.match(r'^(.+?)-(\d[\w.]*)(?:-r\d+)?$', pkg_full)
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
                "is_installed": pkg_id in installed_ids,
                "is_app": False,
                "Exec": "",
                "backend": BACKEND_ID,
                "PackageName": pkg_id,
                "Icon": pkg_id,
            })
        return out[:100]
    except Exception as e:
        print(f"[apk] search error: {e}")
        return []


def get_installed():
    """Return all installed APK packages."""
    try:
        res = subprocess.run(
            ["apk", "list", "--installed"],
            capture_output=True, text=True, timeout=15
        )
        if res.returncode != 0:
            return []

        import re
        out = []
        for line in res.stdout.strip().split("\n"):
            if not line.strip():
                continue
            # Format: pkgname-version-r0 {origin} [installed]
            # or: pkgname-version-r0 arch {repo} [installed]
            pkg_full = line.split()[0]
            m = re.match(r'^(.+?)-(\d[\w.]*)(?:-r\d+)?$', pkg_full)
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
        print(f"[apk] get_installed error: {e}")
        return []


def install(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "apk", "add", pkg_id])


def remove(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "apk", "del", pkg_id])


def get_info(pkg_id):
    """Return extended info from apk info."""
    info = {}
    try:
        res = subprocess.run(
            ["apk", "info", "-a", pkg_id],
            capture_output=True, text=True, timeout=10
        )
        if res.returncode == 0:
            for line in res.stdout.split("\n"):
                if line.startswith(pkg_id) and " is owned by " in line:
                    continue
                if "depends on:" in line.lower():
                    info["Depends On"] = line.split(":", 1)[1].strip()
                elif "required by:" in line.lower():
                    info["Required By"] = line.split(":", 1)[1].strip()
                elif ": " in line:
                    k, v = line.split(": ", 1)
                    info[k.strip()] = v.strip()
            info.setdefault("Depends On", "None")
            info.setdefault("Required By", "None")
    except Exception as e:
        print(f"[apk] get_info error: {e}")
    return info
