import os
import sys
import subprocess
import shutil
import zipapp
from pathlib import Path

def create_bundle():
    print("🚀 Starting VividPM Universal Bundler...")
    
    # 1. Setup temporary directory
    bundle_dir = Path("bundle_temp")
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir()

    # 2. Copy source files
    print("📂 Copying source files...")
    # Copy the package
    shutil.copytree("vivid_gui", bundle_dir / "vivid_gui", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # Copy icon
    shutil.copy("icon.png", bundle_dir / "icon.png")

    # 3. Create __main__.py (The Bootstrapper)
    print("📝 Creating smarter bootstrapper...")
    main_content = """
import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def get_venv_path():
    # Store venv in user's home directory to avoid permission issues in app folder
    return Path.home() / ".vividpm_venv"

def is_venv():
    return hasattr(sys, 'real_prefix') or (sys.base_prefix != sys.prefix)

def install_dependencies(python_exe):
    dependencies = ['customtkinter', 'Pillow', 'darkdetect', 'packaging', 'requests']
    print(f"📦 Checking dependencies using {python_exe}...")
    
    # Use the target python to check and install
    try:
        subprocess.check_call([python_exe, "-m", "pip", "install"] + dependencies)
        return True
    except subprocess.CalledProcessError:
        # If it fails (like PEP 668), we might need to try --break-system-packages 
        # or just fail if venv creation also fails.
        try:
            print("⚠️ Standard install failed. Trying with --break-system-packages (PEP 668 workaround)...")
            subprocess.check_call([python_exe, "-m", "pip", "install"] + dependencies + ["--break-system-packages"])
            return True
        except:
            return False

def setup_and_run():
    venv_dir = get_venv_path()
    venv_python = venv_dir / "bin" / "python" if os.name != 'nt' else venv_dir / "Scripts" / "python.exe"
    
    # 1. Check if we are already running in our venv
    if is_venv() and str(sys.executable).startswith(str(venv_dir)):
        # We are in the venv, just run the app
        from vivid_gui.main import main
        main()
        return

    # 2. Try to import dependencies in current environment
    try:
        import customtkinter
        import PIL
        import darkdetect
        from vivid_gui.main import main
        main()
    except ImportError:
        # 3. If not present, check if our venv exists
        if not venv_dir.exists():
            print(f"🌟 First-time setup: Creating virtual environment in {venv_dir}...")
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
        
        # 4. Install dependencies into the venv
        if install_dependencies(str(venv_python)):
            # 5. Re-launch ourselves using the venv python
            print("🚀 Launching VividPM...")
            os.execv(str(venv_python), [str(venv_python)] + sys.argv)
        else:
            print("❌ Critical Error: Could not setup dependencies.")
            input("Press Enter to exit...")

if __name__ == "__main__":
    setup_and_run()
"""
    with open(bundle_dir / "__main__.py", "w") as f:
        f.write(main_content)

    # 4. Create the ZipApp
    print("📦 Packing into VividPM_Universal.pyw...")
    zipapp.create_archive(bundle_dir, "VividPM_Universal.pyw", interpreter="/usr/bin/env python3")

    # 5. Cleanup
    shutil.rmtree(bundle_dir)
    print("✨ DONE! Created VividPM_Universal.pyw")

if __name__ == "__main__":
    create_bundle()
