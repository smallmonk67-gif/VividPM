import customtkinter as ctk
import datetime
from vivid_gui import icon_resolver

# Premium color palette
BACKEND_COLORS = {
    "pacman":  "#0099ff",
    "flatpak": "#4180d4",
    "snap":    "#e95420",
    "pip":     "#3775a9",
    "apt":     "#dd4814",
    "dnf":     "#3C6EB4",
    "zypper":  "#73BA25",
    "portage": "#54487A",
    "xbps":    "#478061",
    "apk":     "#0D597F",
    "winget":  "#00a4ef",
    "choco":   "#8b4513",
    "scoop":   "#106EBE",
    "windows_native": "#0078d4",
    "brew":    "#f1e05a",
    "macports":""#51697c",
    "nix":     "#7e7eff",
    "fink":    "#005a9c",
    "npm":     "#cb3837",
    "cargo":   "#dea584",
    "gem":     "#701516",
}

MODERN_FONT = ("Outfit", "Inter", "Roboto", "Segoe UI", "sans-serif")

class PackageListFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, on_select_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_select_callback = on_select_callback
        self.item_frames = []
        self._all_packages = []
        self._active_backends = None
        self._loading_backends = 0
        self._spinner_idx = 0
        self._spinner_job = None
        
        self._spinner_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._spinner_label = ctk.CTkLabel(self._spinner_frame, text="", font=ctk.CTkFont(size=16))
        self._spinner_label.pack(side="left", padx=5)
        self._spinner_text = ctk.CTkLabel(self._spinner_frame, text="Searching...", font=ctk.CTkFont(size=13))
        self._spinner_text.pack(side="left")

        self._bind_scroll_recursive(self)

    def _bind_scroll_recursive(self, widget):
        def on_mouse_scroll(event):
            delta = 0
            if event.num == 4 or (hasattr(event, "delta") and event.delta > 0): delta = -1
            elif event.num == 5 or (hasattr(event, "delta") and event.delta < 0): delta = 1
            if delta != 0:
                try: self._canvas.yview_scroll(delta, "units")
                except: pass
        widget.bind("<MouseWheel>", on_mouse_scroll, add="+")
        widget.bind("<Button-4>", on_mouse_scroll, add="+")
        widget.bind("<Button-5>", on_mouse_scroll, add="+")
        for child in widget.winfo_children():
            self._bind_scroll_recursive(child)

    def start_loading(self, count=1):
        self._loading_backends += count
        if self._spinner_job is None:
            self._spinner_frame.pack(fill="x", padx=10, pady=5)
            self._animate_spinner()

    def stop_one_backend(self):
        self._loading_backends = max(0, self._loading_backends - 1)
        if self._loading_backends == 0:
            self._hide_spinner()

    def _animate_spinner(self):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spinner_label.configure(text=frames[self._spinner_idx % len(frames)])
        self._spinner_idx += 1
        self._spinner_job = self.after(80, self._animate_spinner)

    def _hide_spinner(self):
        if self._spinner_job: self.after_cancel(self._spinner_job); self._spinner_job = None
        self._spinner_frame.pack_forget()

    def clear(self):
        for item in self.item_frames: item.destroy()
        self.item_frames = []

    def add_packages(self, packages):
        for pkg in packages[:100]:
            item = PackageListItem(self, pkg, self.on_item_click)
            item.pack(fill="x", padx=5, pady=2)
            self.item_frames.append(item)
            self._bind_scroll_recursive(item)

    def on_item_click(self, pkg_data):
        self.on_select_callback(pkg_data)

class PackageListItem(ctk.CTkFrame):
    def __init__(self, master, pkg_data, click_callback):
        super().__init__(master, fg_color="transparent", corner_radius=8, cursor="hand2")
        self.pkg_data = pkg_data
        
        # UI Elements (Title, Backend Badge, etc.)
        self.title = ctk.CTkLabel(self, text=pkg_data.get("Name", "Unknown"), font=ctk.CTkFont(weight="bold"))
        self.title.pack(side="left", padx=10, pady=10)
        
        backend = pkg_data.get("backend", "unknown")
        color = BACKEND_COLORS.get(backend, "gray")
        self.badge = ctk.CTkLabel(self, text=backend.upper(), fg_color=color, corner_radius=4, width=60)
        self.badge.pack(side="right", padx=10)

        self.bind("<Button-1>", lambda e: click_callback(pkg_data))
        self.title.bind("<Button-1>", lambda e: click_callback(pkg_data))

class SearchBar(ctk.CTkFrame):
    def __init__(self, master, on_search):
        super().__init__(master, fg_color="transparent")
        self.entry = ctk.CTkEntry(self, placeholder_text="Search packages...")
        self.entry.pack(fill="x", side="left", expand=True, padx=(0, 5))
        self.entry.bind("<Return>", lambda e: on_search(self.entry.get()))
        self.btn = ctk.CTkButton(self, text="Search", width=70, command=lambda: on_search(self.entry.get()))
        self.btn.pack(side="right")

class BackendFilterBar(ctk.CTkFrame):
    def __init__(self, master, backends, on_change):
        super().__init__(master, fg_color="transparent")
        # Horizontal scrollable list of backend toggles
        pass

class PackageDetailFrame(ctk.CTkFrame):
    def __init__(self, master, on_install, on_remove, on_run, fetch_extended_info, **kwargs):
        super().__init__(master, **kwargs)
        self.on_install = on_install
        self.on_remove = on_remove
        self.on_run = on_run
        
        self.label = ctk.CTkLabel(self, text="Select a package", font=ctk.CTkFont(size=20))
        self.label.pack(pady=100)

    def display_package(self, pkg):
        for child in self.winfo_children(): child.destroy()
        ctk.CTkLabel(self, text=pkg.get("Name"), font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)
        ctk.CTkLabel(self, text=pkg.get("Description", "No description"), wraplength=400).pack(pady=10)
        
        if pkg.get("is_installed"):
            ctk.CTkButton(self, text="Run", command=lambda: self.on_run(pkg.get("Name"))).pack(pady=5)
            ctk.CTkButton(self, text="Uninstall", fg_color="red", command=lambda: self.on_remove(pkg)).pack(pady=5)
        else:
            ctk.CTkButton(self, text="Install", command=lambda: self.on_install(pkg)).pack(pady=5)
