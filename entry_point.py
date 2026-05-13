import os
import sys
import customtkinter as ctk

# PyInstaller creates a temporary folder and stores path in _MEIPASS
if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

# Add the base path to sys.path so 'import vivid_gui' works
sys.path.append(base_path)

if __name__ == "__main__":
    try:
        from vivid_gui.main import App
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        app = App()
        app.mainloop()
    except Exception as e:
        # If it crashes, we want to know why!
        import traceback
        with open("crash_log.txt", "w") as f:
            f.write(traceback.format_exc())
        print(traceback.format_exc())
        input("\nPress Enter to exit...")
