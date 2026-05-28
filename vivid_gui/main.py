import customtkinter as ctk
import tkinter as tk
from vivid_gui.pkg_manager import PackageManager
from vivid_gui.ui_components import SearchBar, BackendFilterBar, PackageListFrame, PackageDetailFrame, SettingsWindow
from vivid_gui.installer import PackageInstaller
from vivid_gui.config_manager import config_manager
from vivid_gui.action_runner import ActionRunner
import threading
import os
import sys
import time
from vivid_gui import utils

# Application Version
VERSION = "2.1.0"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"Vivid Package Manager v{VERSION}")
        self.geometry("1100x700")
        
        # Apply theme from configuration
        self._apply_theme_config(config_manager.get("theme", "System"), config_manager.get("accent_color", "blue"))
        
        # Ensure the app starts with a modern aesthetic
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Initialize core components
        self.pkg_manager = PackageManager()
        self.installer = PackageInstaller()
        self.action_runner = ActionRunner()

        # Build UI
        self._setup_ui()
        
        # Start background scan for installed apps
        self.after(500, self._initial_scan)
        self.after(1000, self._check_missing_backends)

    def _setup_ui(self):
        # Main PanedWindow for resizable/scalable layout
        self.paned_window = tk.PanedWindow(
            self, 
            orient="horizontal", 
            bd=0, 
            sashwidth=4, 
            sashpad=0, 
            bg="#161616", 
            relief="flat"
        )
        self.paned_window.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # Left Panel: Sidebar + Search
        self.left_panel = ctk.CTkFrame(self.paned_window, width=320, corner_radius=0)
        self.left_panel.grid_propagate(False)

        # App Logo/Title
        self.logo_label = ctk.CTkLabel(
            self.left_panel, 
            text="VIVID", 
            font=ctk.CTkFont(size=24, weight="bold", family="Outfit")
        )
        self.logo_label.pack(pady=(20, 10))

        # Search Bar
        self.search_bar = SearchBar(self.left_panel, self.handle_search)
        self.search_bar.pack(fill="x", padx=10, pady=5)

        # Filter Bar (Backends)
        self.filter_bar = BackendFilterBar(
            self.left_panel, 
            self.pkg_manager.backends, 
            self.handle_filter_change
        )
        self.filter_bar.pack(fill="x", padx=10, pady=5)

        # Package List
        self.package_list = PackageListFrame(self.left_panel, self.handle_package_select)
        self.package_list.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Right Panel: Details
        self.right_panel = ctk.CTkFrame(self.paned_window, corner_radius=0, fg_color=("white", "#1e1e1e"))
        
        # Add panels to PanedWindow. Left panel is resizable/scalable, right panel preserves width on shrink.
        self.paned_window.add(self.left_panel, width=320, minsize=200, stretch="always")
        self.paned_window.add(self.right_panel, minsize=400, stretch="never")
        
        self.detail_view = PackageDetailFrame(
            self.right_panel, 
            on_install=self.install_package,
            on_remove=self.remove_package,
            on_run=self.run_package,
            fetch_extended_info=self.fetch_extended_info,
            fg_color="transparent"
        )
        self.detail_view.pack(fill="both", expand=True)

        # Status Bar / Top Action Bar
        self.top_bar = ctk.CTkFrame(self.right_panel, height=50, fg_color="transparent")
        self.top_bar.pack(fill="x", side="top", padx=20, pady=(15, 0))
        
        self.status_label = ctk.CTkLabel(self.top_bar, text="Ready", text_color="gray")
        self.status_label.pack(side="left")

        self.update_all_btn = ctk.CTkButton(
            self.top_bar, text="Update All", width=100, 
            fg_color="#8e24aa", hover_color="#6a1b9a",
            command=self.update_all
        )
        self.update_all_btn.pack(side="right", padx=5)

        self.build_local_btn = ctk.CTkButton(
            self.top_bar, text="Build Local", width=100,
            fg_color="#fbc02d", hover_color="#f9a825", text_color="black",
            command=self.handle_build_local
        )
        self.build_local_btn.pack(side="right", padx=5)
        
        self.settings_btn = ctk.CTkButton(
            self.top_bar, text="⚙️ Settings", width=40,
            fg_color="transparent", hover_color=("gray85", "#2e2e2e"),
            text_color=("black", "white"), command=self.open_settings
        )
        self.settings_btn.pack(side="right", padx=5)

    def _apply_theme_config(self, theme, accent):
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme(accent)
        
    def open_settings(self):
        SettingsWindow(self, config_manager, self._apply_theme_config)

    def _initial_scan(self):
        self.update_status("Loading installed apps...")
        self.package_list.clear()
        
        # Determine total backends for the loading indicator
        backends = self.pkg_manager.backends
        self.package_list.start_loading(len(backends))

        for backend in backends:
            threading.Thread(
                target=self._run_backend_installed_scan,
                args=(backend,),
                daemon=True
            ).start()

    def _run_backend_installed_scan(self, backend):
        try:
            results = backend.get_installed()
            self.after(0, self._append_installed_results, results)
        except Exception as e:
            print(f"Error loading installed apps from {backend.BACKEND_ID}: {e}")
        finally:
            self.after(0, self.package_list.stop_one_backend)

    def _append_installed_results(self, results):
        self.package_list.add_packages(results)
        self.update_status(f"Loaded {len(self.package_list.item_frames)} installed apps")

    def update_status(self, text):
        self.status_label.configure(text=text)

    def handle_search(self, query):
        if not query: return
        query = query.strip().lower()
        
        self.search_start_time = time.time()
        self.search_session_id = object()
        self.active_search_backends = {b.BACKEND_ID for b in self.pkg_manager.backends}
        self.package_list.clear()
        self.package_list.start_loading(len(self.pkg_manager.backends))
        self.update_status(f"Searching for '{query}'...")
        
        self._update_search_timer(query, self.search_session_id)

        for backend in self.pkg_manager.backends:
            threading.Thread(
                target=self._run_backend_search, 
                args=(backend, query), 
                daemon=True
            ).start()

    def _update_search_timer(self, query, session_id):
        if getattr(self, "search_session_id", None) != session_id:
            return
            
        if self.package_list._loading_backends > 0:
            elapsed = time.time() - self.search_start_time
            count = len(self.package_list.item_frames)
            
            backends_list = ", ".join(sorted(getattr(self, "active_search_backends", [])))
            backends_str = f" in {backends_list}" if backends_list else ""
            
            if count > 0:
                self.update_status(f"Searching{backends_str}... Found {count} results ({elapsed:.1f}s)")
            else:
                self.update_status(f"Searching for '{query}'{backends_str}... ({elapsed:.1f}s)")
            self.after(100, self._update_search_timer, query, session_id)

    def _remove_active_search_backend(self, backend_id):
        if hasattr(self, "active_search_backends"):
            self.active_search_backends.discard(backend_id)

    def _run_backend_search(self, backend, query):
        try:
            start_time = time.time()
            results = backend.search(query)
            elapsed = time.time() - start_time
            print(f"[{backend.BACKEND_ID}] Search took {elapsed:.4f}s")
            self.after(0, self._append_search_results, results)
        except Exception as e:
            print(f"Error searching backend {backend.BACKEND_ID}: {e}")
        finally:
            self.after(0, self._remove_active_search_backend, backend.BACKEND_ID)
            self.after(0, self.package_list.stop_one_backend)

    def _append_search_results(self, results):
        self.package_list.add_packages(results)
        elapsed = time.time() - self.search_start_time
        self.update_status(f"Found {len(self.package_list.item_frames)} results in {elapsed:.2f}s")

    def handle_filter_change(self, active_backends):
        self.package_list.apply_filter(active_backends)

    def handle_package_select(self, pkg_data):
        self.detail_view.display_package(pkg_data)

    def fetch_extended_info(self, pkg, callback):
        threading.Thread(
            target=self._do_fetch_extended_info,
            args=(pkg, callback),
            daemon=True
        ).start()

    def _do_fetch_extended_info(self, pkg, callback):
        backend_id = pkg.get("backend")
        backend = self.pkg_manager.get_backend(backend_id)
        if backend:
            info = backend.get_info(pkg.get("Name"))
            callback(info)

    def install_package(self, pkg):
        self.update_status(f"Installing {pkg['Name']}...")
        threading.Thread(
            target=self._do_install,
            args=(pkg,),
            daemon=True
        ).start()

    def _do_install(self, pkg):
        backend = self.pkg_manager.get_backend(pkg['backend'])
        success = self.installer.install(pkg, backend, on_finish=self._initial_scan)
        if success:
            pkg["is_installed"] = True
            self.after(0, lambda: self.update_status(f"Successfully installed {pkg['Name']}"))
            self.after(0, lambda: self.detail_view.display_package(pkg))
        else:
            self.after(0, lambda: self.update_status(f"Failed to install {pkg['Name']}"))

    def remove_package(self, pkg):
        self.update_status(f"Removing {pkg['Name']}...")
        threading.Thread(
            target=self._do_remove,
            args=(pkg,),
            daemon=True
        ).start()

    def _do_remove(self, pkg):
        backend = self.pkg_manager.get_backend(pkg['backend'])
        success = self.installer.remove(pkg, backend, on_finish=self._initial_scan)
        if success:
            pkg["is_installed"] = False
            self.after(0, lambda: self.update_status(f"Successfully removed {pkg['Name']}"))
            self.after(0, lambda: self.detail_view.display_package(pkg))
        else:
            self.after(0, lambda: self.update_status(f"Failed to remove {pkg['Name']}"))

    def run_package(self, exec_cmd):
        self.action_runner.run(exec_cmd)

    def update_all(self):
        self.action_runner.update_system(on_finish=self._initial_scan)

    def handle_build_local(self):
        path = utils.get_native_file_picker("Select PKGBUILD or Project Folder")
        if path:
            self.action_runner.build_local_package(path, on_finish=self._initial_scan)

    def _check_missing_backends(self):
        """Show a dialog if optional package managers are not installed."""
        missing = self.installer.get_missing_backends()
        if not missing:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Optional Package Managers")
        dialog.geometry("500x380")
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

        # We'll use a scrollable frame for custom backends list
        scroll_frame = ctk.CTkScrollableFrame(dialog, width=440, height=220, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=24, pady=4)

        from vivid_gui.installer import INSTALLABLE_BACKENDS

        # List missing backends with descriptions
        for bid in missing:
            info = INSTALLABLE_BACKENDS[bid]
            row = ctk.CTkFrame(scroll_frame, fg_color=("gray85", "gray20"), corner_radius=8)
            row.pack(fill="x", padx=4, pady=4)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=12, pady=8)

            ctk.CTkLabel(
                left, text=info["display_name"], font=ctk.CTkFont(weight="bold"), anchor="w"
            ).pack(anchor="w")
            ctk.CTkLabel(
                left, text=info["description"], text_color="gray", anchor="w", font=ctk.CTkFont(size=11),
                wraplength=260, justify="left"
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

        from vivid_gui.installer import INSTALLABLE_BACKENDS
        info = INSTALLABLE_BACKENDS[backend_id]
        self.update_status(f"Installing {info['display_name']}...")

        def on_done():
            # Trigger UI update on the main thread
            self.after(0, self._on_backend_installed, backend_id, button)

        self.installer.install_backend(backend_id, on_finish=on_done)

    def _on_backend_installed(self, backend_id, button):
        """Rebuild the filter bar and update the button state. Runs on main thread."""
        self.pkg_manager.reload_backends()
        new_backends = self.pkg_manager.backends
        
        # Check if backend was actually installed (binary found)
        is_installed = any(b.BACKEND_ID == backend_id for b in new_backends)
        
        if button.winfo_exists():
            if is_installed:
                button.configure(text="Installed", fg_color="gray", state="disabled")
            else:
                button.configure(text="Retry", fg_color="red", state="normal")
        
        # Rebuild filter bar to include the new backend
        if hasattr(self, "filter_bar") and self.filter_bar.winfo_exists():
            self.filter_bar.rebuild(new_backends)
        
        # Refresh the package list
        self._initial_scan()


def main():
    try:
        scaling = utils.get_scaling_factor()
        ctk.set_widget_scaling(scaling)
        ctk.set_window_scaling(scaling)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        app = App()
        try:
            app.tk.call('tk', 'scaling', scaling * 1.333)
        except: pass
        app.mainloop()
    except Exception as e:
        import tkinter.messagebox as mb
        mb.showerror("Startup Error", f"The application failed to start:\n\n{e}")

if __name__ == "__main__":
    main()
