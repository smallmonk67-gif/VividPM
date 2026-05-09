"""
utils.py — Helper utilities for native system interactions.
"""
import subprocess
import shutil
import customtkinter as ctk

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

