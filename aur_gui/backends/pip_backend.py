"""
pip_backend.py — Backend for Python/pip packages.

Note: PyPI has no public search API. Search performs a direct package
lookup via the PyPI JSON API (https://pypi.org/pypi/<name>/json).
This means searching for an exact or close package name works best.
"""
import shutil
import subprocess
import json
import urllib.request
import urllib.parse

BACKEND_ID = "pip"
DISPLAY_NAME = "pip"
COLOR = "#3775a9"  # PyPI blue

PYPI_JSON_URL = "https://pypi.org/pypi/{}/json"


def is_available():
    return shutil.which("pip") is not None or shutil.which("pip3") is not None


def _pip_cmd():
    """Return the available pip executable."""
    return "pip" if shutil.which("pip") else "pip3"


def _fetch_pypi_info(package_name: str):
    """Fetch package metadata from the PyPI JSON API."""
    try:
        url = PYPI_JSON_URL.format(urllib.parse.quote(package_name))
        req = urllib.request.Request(url, headers={"User-Agent": "package-manager-gui/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.load(resp)
    except Exception:
        return None


def search(query: str):
    """
    Search PyPI by looking up the query as a package name via the JSON API.
    Since PyPI removed their search API, we resolve the exact name + common variants.
    """
    installed = {p["ID"] for p in get_installed()}
    results = []
    seen = set()

    # Try the query directly plus some common normalizations
    candidates = [query, query.lower(), query.replace(" ", "-"), query.replace(" ", "_")]

    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        data = _fetch_pypi_info(candidate)
        if not data:
            continue
        info = data.get("info", {})
        name = info.get("name", candidate)
        pkg_id = name.lower()
        # Process downloads (PyPI often returns a dict of counts)
        downloads = info.get("downloads", {})
        num_votes = 0
        if isinstance(downloads, dict):
            monthly = downloads.get("last_month", -1)
            num_votes = monthly if monthly != -1 else 0
        elif isinstance(downloads, (int, float)):
            num_votes = int(downloads)

        results.append({
            "Name": name,
            "ID": pkg_id,
            "Version": info.get("version", ""),
            "Description": info.get("summary", ""),
            "is_installed": pkg_id in installed,
            "is_app": False,
            "Exec": "",
            "backend": BACKEND_ID,
            "PackageName": name,
            "NumVotes": num_votes,
            "Maintainer": info.get("author", ""),
            "Homepage": info.get("home_page", ""),
            "_pypi_info": data,
        })

    return results


def get_installed():
    """Return all pip-installed packages."""
    try:
        res = subprocess.run(
            [_pip_cmd(), "list", "--format=json"],
            capture_output=True, text=True, timeout=15
        )
        if res.returncode != 0:
            return []
        pkgs = json.loads(res.stdout)
        out = []
        for p in pkgs:
            name = p.get("name", "")
            pkg_id = name.lower()
            out.append({
                "Name": name,
                "ID": pkg_id,
                "Version": p.get("version", ""),
                "Description": "Python package",
                "is_installed": True,
                "is_app": False,
                "Exec": "",
                "backend": BACKEND_ID,
                "PackageName": name,
            })
        out.sort(key=lambda x: x["Name"].lower())
        return out
    except Exception as e:
        print(f"[pip] get_installed error: {e}")
        return []


def install(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", _pip_cmd(), "install", "--break-system-packages", pkg_id])


def remove(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", _pip_cmd(), "uninstall", "-y", pkg_id])


def get_info(pkg_id):
    """Return extended info from pip show + PyPI JSON API."""
    info = {}
    try:
        # pip show gives local installed info
        res = subprocess.run(
            [_pip_cmd(), "show", pkg_id],
            capture_output=True, text=True, timeout=10
        )
        if res.returncode == 0:
            for line in res.stdout.split("\n"):
                if ": " in line:
                    k, v = line.split(": ", 1)
                    info[k.strip()] = v.strip()
            # Map pip show fields to our schema
            requires = info.pop("Requires", "")
            required_by = info.pop("Required-by", "")
            info["Depends On"] = requires or "None"
            info["Required By"] = required_by or "None"
            return info
    except Exception as e:
        print(f"[pip] get_info error: {e}")

    # Fallback: PyPI JSON API
    data = _fetch_pypi_info(pkg_id)
    if data:
        pi = data.get("info", {})
        deps = pi.get("requires_dist") or []
        info["Depends On"] = ", ".join(deps) if deps else "None"
        info["Required By"] = "None"
        info["Home-page"] = pi.get("home_page", "")
        info["Author"] = pi.get("author", "")
        info["License"] = pi.get("license", "")
    return info
