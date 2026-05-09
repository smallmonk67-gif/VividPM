"""
zypper_backend.py — Backend for Zypper packages (openSUSE Tumbleweed, Leap, SLES)
"""
import shutil
import subprocess

BACKEND_ID = "zypper"
DISPLAY_NAME = "Zypper"
COLOR = "#73BA25"  # openSUSE green


def is_available():
    return shutil.which("zypper") is not None


def search(query: str):
    """Search Zypper repositories for packages."""
    try:
        res = subprocess.run(
            ["zypper", "--quiet", "search", query],
            capture_output=True, text=True, timeout=30
        )
        if res.returncode not in (0, 100):
            return []

        installed = {p["ID"] for p in get_installed()}
        out = []
        lines = res.stdout.strip().split("\n")
        # Skip header rows (contains "---" separator)
        past_header = False
        for line in lines:
            if line.startswith("-"):
                past_header = True
                continue
            if not past_header or not line.strip():
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 2:
                continue
            pkg_id = parts[1].strip()
            desc = parts[4].strip() if len(parts) > 4 else ""
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
        return out[:100]
    except Exception as e:
        print(f"[zypper] search error: {e}")
        return []


def get_installed():
    """Return installed Zypper packages."""
    try:
        res = subprocess.run(
            ["zypper", "--quiet", "search", "--installed-only"],
            capture_output=True, text=True, timeout=20
        )
        if res.returncode not in (0, 100):
            return []

        out = []
        past_header = False
        for line in res.stdout.strip().split("\n"):
            if line.startswith("-"):
                past_header = True
                continue
            if not past_header or not line.strip():
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 2:
                continue
            pkg_id = parts[1].strip()
            version = parts[3].strip() if len(parts) > 3 else ""
            desc = parts[4].strip() if len(parts) > 4 else ""
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
        print(f"[zypper] get_installed error: {e}")
        return []


def install(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "zypper", "install", "-y", pkg_id])


def remove(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "zypper", "remove", "-y", pkg_id])


def get_info(pkg_id):
    """Return extended info from zypper info."""
    info = {}
    try:
        res = subprocess.run(
            ["zypper", "info", pkg_id],
            capture_output=True, text=True, timeout=15
        )
        if res.returncode == 0:
            for line in res.stdout.split("\n"):
                if ":" in line:
                    k, _, v = line.partition(":")
                    k = k.strip()
                    if k in ("Name", "Version", "Arch", "Vendor", "Support Level",
                             "Installed Size", "Installed", "Status", "Source package",
                             "Summary", "Description", "Requires"):
                        info[k] = v.strip()
            info["Depends On"] = info.pop("Requires", "None")
            info["Required By"] = "None"
    except Exception as e:
        print(f"[zypper] get_info error: {e}")
    return info
