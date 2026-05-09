#!/usr/bin/env python3
"""
launcher.py — Portable entry point for the Package Manager.
Ensures the application can be moved anywhere and still find its components.
"""
import os
import sys

# Get the directory where launcher.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add this directory to the Python path so 'import aur_gui' works
sys.path.insert(0, BASE_DIR)

if __name__ == "__main__":
    # Check if a local virtual environment exists and we aren't using it
    venv_python = os.path.join(BASE_DIR, ".venv", "bin", "python")
    if os.path.exists(venv_python) and sys.executable != venv_python:
        print(f"Tip: A local virtual environment was found. You might want to run:")
        print(f"  {venv_python} {__file__}")
        print("-" * 40)

    try:
        import customtkinter as ctk
        from PIL import Image, ImageTk
        from aur_gui.main import App
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        app = App()
        app.mainloop()
    except ImportError as e:
        print(f"Error: Missing dependencies! ({e})")
        print(f"Please install them using:")
        print(f"  pip install customtkinter Pillow")
        print(f"\nOr use the local virtual environment if available.")
        sys.exit(1)
