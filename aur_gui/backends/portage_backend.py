"""
portage_backend.py — Backend for Portage/emerge packages (Gentoo Linux)

Uses `q` from portage-utils for fast search if available,
falling back to `emerge --search` (which is significantly slower).
"""
import shutil
import subprocess

BACKEND_ID = "portage"
DISPLAY_NAME = "Portage"
COLOR = "#54487A"  # Gentoo purple


def is_available():
    return shutil.which("emerge") is not None


def search(query: str):
    """
    Search Portage tree.
    Prefers `q -s` (portage-utils, fast) over `emerge --search` (slow).
    """
    try:
        if shutil.which("q"):
            return _search_with_q(query)
        else:
            return _search_with_emerge(query)
    except Exception as e:
        print(f"[portage] search error: {e}")
        return []


def _search_with_q(query: str):
    """Fast search using portage-utils `q -s`."""
    installed = {p["ID"] for p in get_installed()}
    res = subprocess.run(
        ["q", "-s", query],
        capture_output=True, text=True, timeout=15
    )
    out = []
    for line in res.stdout.strip().split("\n"):
        if not line.strip():
            continue
        # Format: category/package: description
        if ":" in line:
            pkg_full, _, desc = line.partition(":")
        else:
            pkg_full, desc = line, ""
        pkg_id = pkg_full.strip()
        name = pkg_id.split("/")[-1] if "/" in pkg_id else pkg_id
        out.append({
            "Name": name,
            "ID": pkg_id,
            "Version": "",
            "Description": desc.strip(),
            "is_installed": pkg_id in installed,
            "is_app": False,
            "Exec": "",
            "backend": BACKEND_ID,
            "PackageName": pkg_id,
            "Icon": name,
        })
    return out[:100]


def _search_with_emerge(query: str):
    """Slow fallback search using emerge --search."""
    installed = {p["ID"] for p in get_installed()}
    res = subprocess.run(
        ["emerge", "--search", query],
        capture_output=True, text=True, timeout=60
    )
    out = []
    pkg_id = name = desc = ""
    for line in res.stdout.split("\n"):
        line = line.strip()
        if line.startswith("*  "):
            # Save previous
            if pkg_id:
                n = pkg_id.split("/")[-1]
                out.append({
                    "Name": n, "ID": pkg_id, "Version": "",
                    "Description": desc, "is_installed": pkg_id in installed,
                    "is_app": False, "Exec": "", "backend": BACKEND_ID,
                    "PackageName": pkg_id, "Icon": n,
                })
            pkg_id = line[3:].strip()
            desc = ""
        elif line.startswith("Description:"):
            desc = line.split(":", 1)[1].strip()
    # Add last
    if pkg_id:
        n = pkg_id.split("/")[-1]
        out.append({
            "Name": n, "ID": pkg_id, "Version": "",
            "Description": desc, "is_installed": pkg_id in installed,
            "is_app": False, "Exec": "", "backend": BACKEND_ID,
            "PackageName": pkg_id, "Icon": n,
        })
    return out[:100]


def get_installed():
    """Return installed packages using qlist -Iv (portage-utils) or qlist fallback."""
    try:
        if shutil.which("qlist"):
            res = subprocess.run(
                ["qlist", "-Iv"],
                capture_output=True, text=True, timeout=20
            )
        else:
            res = subprocess.run(
                ["emerge", "-ep", "world"],
                capture_output=True, text=True, timeout=30
            )
        if res.returncode != 0:
            return []
        out = []
        for line in res.stdout.strip().split("\n"):
            if not line.strip():
                continue
            # Format: category/name-version
            parts = line.strip().rsplit("-", 2)
            pkg_id = line.strip()
            name = pkg_id.split("/")[-1] if "/" in pkg_id else pkg_id
            out.append({
                "Name": name,
                "ID": pkg_id,
                "Version": "",
                "Description": "",
                "is_installed": True,
                "is_app": False,
                "Exec": "",
                "backend": BACKEND_ID,
                "PackageName": pkg_id,
                "Icon": name,
            })
        out.sort(key=lambda x: x["Name"].lower())
        return out
    except Exception as e:
        print(f"[portage] get_installed error: {e}")
        return []


def install(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "emerge", pkg_id])


def remove(pkg_id, terminal="alacritty"):
    subprocess.Popen([terminal, "-e", "sudo", "emerge", "--unmerge", pkg_id])


def get_info(pkg_id):
    """Return extended info using equery (gentoolkit) or emerge -pv."""
    info = {}
    try:
        if shutil.which("equery"):
            res = subprocess.run(
                ["equery", "depends", pkg_id],
                capture_output=True, text=True, timeout=15
            )
            if res.returncode == 0:
                deps = [l.strip() for l in res.stdout.split("\n") if l.strip()]
                info["Depends On"] = ", ".join(deps) or "None"
            rdep_res = subprocess.run(
                ["equery", "depends", "--reverse", pkg_id],
                capture_output=True, text=True, timeout=15
            )
            if rdep_res.returncode == 0:
                rdeps = [l.strip() for l in rdep_res.stdout.split("\n") if l.strip()]
                info["Required By"] = ", ".join(rdeps[:10]) or "None"
        else:
            info["Depends On"] = "Install gentoolkit for dependency info"
            info["Required By"] = "None"
    except Exception as e:
        print(f"[portage] get_info error: {e}")
    return info
