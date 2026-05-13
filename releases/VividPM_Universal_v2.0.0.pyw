import os
import sys
import customtkinter as ctk

# Add the current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

if __name__ == "__main__":
    try:
        from vivid_gui.main import App
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        app = App()
        app.mainloop()
    except Exception as e:
        import traceback
        try:
            from tkinter import messagebox
            messagebox.showerror("VividPM Startup Error", traceback.format_exc())
        except:
            with open("vividpm_startup_error.log", "w") as f:
                f.write(traceback.format_exc())
