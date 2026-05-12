import sys
import os
import threading
import tkinter as tk
import customtkinter as ctk

# Ensure vivid_gui package is importable when run as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import vivid_gui.pkg_manager as pkg_manager
import vivid_gui.action_runner as action_runner
import vivid_gui.installer as installer
import vivid_gui.utils as utils
from vivid_gui.ui_components import SearchBar, BackendFilterBar, PackageListFrame, PackageDetailFrame


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Vivid Package Manager")
        self.geometry("980x650")

        # Set icon
        try:
            from PIL import Image, ImageTk
            # Find the icon relative to this file's location
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(current_dir)
            
            # Check root folder first, then package folder
            possible_paths = [
                os.path.join(root_dir, "icon.png"),
                os.path.join(current_dir, "icon.png"),
                "icon.png" # Working directory fallback
            ]
            
            for icon_path in possible_paths:
                if os.path.exists(icon_path):
                    pil_img = Image.open(icon_path)
                    img = ImageTk.PhotoImage(pil_img)
                    self.wm_iconphoto(True, img)
                    break
        except Exception as e:
            print(f"[main] Failed to load icon: {e}")

        # Detect backends once at startup
        self._backends = pkg_manager.get_available_backends()
        print(f"[main] Active backends: {[b.BACKEND_ID for b in self._backends]}")

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Threading and search state
        self._search_lock = threading.Lock()
        self._current_request_id = 0

        # ── Top bar ──────────────────────────────────────────────
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 0))
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.search_bar = SearchBar(self.top_frame, self.handle_search)
        self.search_bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.status_label = ctk.CTkLabel(self.top_frame, text="", font=ctk.CTkFont(size=12))
        self.status_label.grid(row=0, column=1, padx=5)

        self.update_btn = ctk.CTkButton(
            self.top_frame, text="Update All", width=100, command=self.handle_update,
            fg_color="purple", hover_color="darkmagenta"
        )
        self.update_btn.grid(row=0, column=2, padx=5)

        self.build_local_btn = ctk.CTkButton(
            self.top_frame, text="Build Local", width=100, command=self.handle_build_local,
            fg_color="#b8860b", hover_color="#8b6508"
        )
        self.build_local_btn.grid(row=0, column=3, padx=(5, 10))

        # ── Filter bar ───────────────────────────────────────────
        self.filter_bar = BackendFilterBar(self, self._backends, self.handle_filter_change)
        self.filter_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(4, 0))

        # ── Left panel (List) ─────────────────────────────────────
        self.list_frame = PackageListFrame(self, on_select_callback=self.handle_select)
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        # ── Right panel (Details) ─────────────────────────────────
        self.detail_frame = PackageDetailFrame(
            self,
            on_install=self.handle_install,
            on_remove=self.handle_remove,
            on_run=action_runner.run_app,
            fetch_extended_info=pkg_manager.async_fetch_extended_info,
        )
        self.detail_frame.grid(row=2, column=1, sticky="nsew", padx=(0, 10), pady=10)

        # Load homepage
        self.load_homepage()

        # Check for missing optional backends after the UI is ready
        self.after(800, self._check_missing_backends)
        self.after(1500, self._check_pythonw)

    # ── Homepage ──────────────────────────────────────────────────
    def load_homepage(self):
        self._current_request_id += 1
        req_id = self._current_request_id
        
        self.status_label.configure(text="Loading installed apps...")
        self.list_frame.clear()
        self.list_frame.stop_loading()
        self.list_frame.start_loading(count=len(self._backends))
        self.detail_frame.hide_content()

        # Shared results accumulator
        self._homepage_results = []
        self._homepage_expected = len(self._backends)
        self._homepage_done = 0

        def on_backend_done(results, backend_id):
            if req_id != self._current_request_id:
                return
            
            with self._search_lock:
                self._homepage_results.extend(results)
                self._homepage_done += 1
                done_count = self._homepage_done

            self.after(0, self._append_homepage_results, results, done_count)

        pkg_manager.async_get_installed(on_backend_done)

    def _append_homepage_results(self, new_results, done_count):
        self.status_label.configure(text=f"{len(self._homepage_results)} packages (installed apps)")
        self.list_frame.add_packages(new_results)
        self.list_frame.stop_one_backend()

    # ── Search ────────────────────────────────────────────────────
    def handle_search(self, query):
        if not query:
            self.load_homepage()
            return

        self._current_request_id += 1
        req_id = self._current_request_id

        self.status_label.configure(text="Searching...")
        self.list_frame.clear()
        self.list_frame.stop_loading()
        self.list_frame.start_loading(count=len(self._backends))
        self.detail_frame.hide_content()

        # Accumulate results from parallel backends
        self._search_results = []
        self._search_expected = len(self._backends)
        self._search_done = 0

        def on_backend_results(results, backend_id):
            if req_id != self._current_request_id:
                return
            
            with self._search_lock:
                self._search_results.extend(results)
                self._search_done += 1
                done_count = self._search_done

            # Append results and tick down one backend from the spinner
            self.after(0, self._append_search_results, results, done_count)

        pkg_manager.search_all(query, on_backend_results)

    def _append_search_results(self, new_results, done_count):
        """Add new results to the list without clearing existing ones (faster)."""
        self.status_label.configure(
            text=f"{len(self._search_results)} packages ({done_count}/{self._search_expected} backends)"
        )
        self.list_frame.add_packages(new_results)
        self.list_frame.stop_one_backend()  # tick spinner down by one

    def _update_list(self, results, label=""):
        self.status_label.configure(text=f"{len(results)} packages" + (f" ({label})" if label else ""))
        self.list_frame.populate(results)

    # ── Filter ────────────────────────────────────────────────────
    def handle_filter_change(self, active_backends):
        self.list_frame.apply_filter(active_backends)

    # ── Selection ─────────────────────────────────────────────────
    def handle_select(self, pkg_data):
        self.detail_frame.display_package(pkg_data)

    # ── Actions ───────────────────────────────────────────────────
    def handle_install(self, pkg):
        pkg_manager.install_package(pkg, on_finish=self.trigger_refresh)

    def handle_remove(self, pkg):
        pkg_manager.remove_package(pkg, on_finish=self.trigger_refresh)

    def handle_update(self):
        action_runner.update_system(on_finish=self.trigger_refresh)

    def handle_build_local(self):
        file_path = utils.get_native_file_picker(title="Select PKGBUILD or Package")
        if file_path:
            action_runner.build_local_package(file_path, on_finish=self.trigger_refresh)

    def trigger_refresh(self):
        self.after(0, self._perform_refresh)

    def _perform_refresh(self):
        query = self.search_bar.entry.get().strip()
        if query:
            self.handle_search(query)
        else:
            self.load_homepage()


    def _check_pythonw(self):
        """Check if pythonw is being used on Windows and warn if missing."""
        import platform
        if platform.system() != "Windows":
            return
        
        import sys
        # If the current executable is not pythonw, check if it exists
        if not sys.executable.lower().endswith("pythonw.exe"):
            pythonw_path = sys.executable.lower().replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw_path):
                # Use a flag file to only show this once
                flag_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".pythonw_notified")
                if not os.path.exists(flag_path):
                    try:
                        with open(flag_path, "w") as f: f.write("1")
                    except: pass
                    
                    utils.show_error(
                        "Optimizer Tip",
                        "We noticed you're running without 'pythonw.exe'.\n\n"
                        "This causes a terminal window to stay open in the background. "
                        "For a cleaner experience, please ensure Python is installed with the 'tcl/tk' and 'IDLE' options enabled."
                    )

    def _check_missing_backends(self):
        """Show a dialog if optional package managers are not installed."""
        missing = installer.get_missing_backends()
        if not missing:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Optional Package Managers")
        dialog.geometry("460x320")
        dialog.resizable(False, False)
        dialog.grab_set()  # Modal

        ctk.CTkLabel(
            dialog,
            text="Optional Package Managers",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            dialog,
            text="The following package managers are not installed.\nWould you like to install them?",
            text_color="gray",
        ).pack(pady=(0, 12))

        # List missing backends with descriptions
        for bid in missing:
            info = installer.INSTALLABLE_BACKENDS[bid]
            row = ctk.CTkFrame(dialog, fg_color=("gray85", "gray20"), corner_radius=8)
            row.pack(fill="x", padx=24, pady=4)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=12, pady=8)

            ctk.CTkLabel(
                left, text=info["display_name"], font=ctk.CTkFont(weight="bold"), anchor="w"
            ).pack(anchor="w")
            ctk.CTkLabel(
                left, text=info["description"], text_color="gray", anchor="w", font=ctk.CTkFont(size=11)
            ).pack(anchor="w")

            btn = ctk.CTkButton(
                row, text="Install", width=80,
                fg_color="green", hover_color="darkgreen"
            )
            btn.configure(command=lambda b=bid, d=dialog, button=btn: self._install_backend(b, d, button))
            btn.pack(side="right", padx=12, pady=8)

        ctk.CTkButton(
            dialog, text="Skip", fg_color="transparent",
            border_width=1, border_color="gray",
            command=dialog.destroy
        ).pack(pady=(12, 20))

    def _install_backend(self, backend_id, dialog, button):
        """Start installing a backend and update UI."""
        button.configure(state="disabled", text="Installing...", fg_color="gray")

        info = installer.INSTALLABLE_BACKENDS[backend_id]
        self.status_label.configure(text=f"Installing {info['display_name']}...")

        def on_done():
            # Trigger UI update on the main thread
            self.after(0, self._on_backend_installed, backend_id, button)

        installer.install_backend(backend_id, on_finish=on_done)

    def _on_backend_installed(self, backend_id, button):
        """Rebuild the filter bar and update the button state. Runs on main thread."""
        pkg_manager.reload_backends()
        new_backends = pkg_manager.get_available_backends()
        
        self._backends = new_backends
        
        # Check if backend was actually installed (binary found)
        is_installed = any(b.BACKEND_ID == backend_id for b in new_backends)
        
        if button.winfo_exists():
            if is_installed:
                button.configure(text="Installed", fg_color="gray", state="disabled")
            else:
                button.configure(text="Retry", fg_color="red", state="normal")
        
        # Rebuild filter bar to include the new backend
        if hasattr(self, "filter_bar") and self.filter_bar.winfo_exists():
            self.filter_bar.destroy()
            
        self.filter_bar = BackendFilterBar(self, self._backends, self.handle_filter_change)
        self.filter_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(4, 0))
        
        # Refresh the package list
        self.load_homepage()


if __name__ == "__main__":
    try:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        app = App()
        app.mainloop()
    except Exception as e:
        import tkinter.messagebox as mb
        mb.showerror("Startup Error", f"The application failed to start:\n\n{e}")
        import traceback
        traceback.print_exc()
