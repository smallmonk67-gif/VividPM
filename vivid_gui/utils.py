"""
utils.py — Helper utilities for native system interactions.
"""
import subprocess
import shutil
import customtkinter as ctk

def get_scaling_factor():
    """
    Attempts to detect the system scaling factor (HiDPI) on Linux.
    Uses environment variables, xrdb, and xrandr.
    """
    import os
    import subprocess
    
    # 1. Check environment variables
    for env in ["GDK_SCALE", "QT_SCALE_FACTOR", "PLASMA_USE_QT_SCALING"]:
        val = os.environ.get(env)
        if val:
            try: return float(val)
            except: pass

    # 2. Check Xft.dpi via xrdb
    try:
        xrdb_res = subprocess.run(["xrdb", "-query"], capture_output=True, text=True, timeout=1)
        if xrdb_res.returncode == 0:
            for line in xrdb_res.stdout.splitlines():
                if "Xft.dpi" in line:
                    dpi = float(line.split(":")[1].strip())
                    return dpi / 96.0
    except: pass

    # 3. Check xrandr
    try:
        xrandr_res = subprocess.run(["xrandr", "--verbose"], capture_output=True, text=True, timeout=1)
        if xrandr_res.returncode == 0:
            if "EDID" in xrandr_res.stdout: # Rough check for high-res
                return 1.5 # Safe bet for modern Linux desktops if unsure
    except: pass
    
    return 1.0

def get_native_file_picker(title="Select File"):
    """
    Attempts to open the native system file explorer (Zenity or KDialog)
    with filters for all supported package formats.
    """
    import platform
    is_windows = platform.system() == "Windows"
    
    if is_windows:
        # Fallback to standard Tkinter dialog for Windows with Windows extensions
        return ctk.filedialog.askopenfilename(
            title=title,
            filetypes=[
                ("Windows Installers", "*.exe *.msi"),
                ("All Files", "*.*"),
            ]
        )

    # Filters covering all supported Linux package managers
    filter_label = "All Packages (*.pkg.tar.*, *.deb, *.rpm, PKGBUILD)"
    filter_patterns = "*.pkg.tar.zst *.pkg.tar.xz *.deb *.rpm PKGBUILD"

    # Try Zenity (GNOME/GTK)
    if shutil.which("zenity"):
        try:
            cmd = [
                "zenity", "--file-selection", 
                f"--title={title}",
                f"--file-filter={filter_label} | {filter_patterns}",
                "--file-filter=All Files | *"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                return res.stdout.strip()
            return None
        except Exception:
            pass
            
    # Try KDialog (KDE/Qt)
    if shutil.which("kdialog"):
        try:
            res = subprocess.run(
                ["kdialog", "--getopenfilename", ".", f"{filter_patterns} | {filter_label}", "--title", title],
                capture_output=True, text=True, timeout=60
            )
            if res.returncode == 0:
                return res.stdout.strip()
            return None
        except Exception:
            pass

    # Fallback to standard Tkinter dialog with strict filters
    return ctk.filedialog.askopenfilename(
        title=title,
        filetypes=[
            ("Linux Packages", "*.pkg.tar.zst *.pkg.tar.xz *.deb *.rpm"),
            ("PKGBUILD", "PKGBUILD"),
            ("All Files", "*.*"),
        ]
    )


def show_error(title, message):
    """Display a standard error popup."""
    from tkinter import messagebox
    messagebox.showerror(title, message)
