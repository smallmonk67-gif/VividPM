import customtkinter as ctk
import datetime
from vivid_gui import icon_resolver

# Premium color palette
BACKEND_COLORS = {
    "pacman":  "#0099ff",  # Brighter Arch blue
    "flatpak": "#4180d4",  # Deep Flatpak blue
    "snap":    "#e95420",  # Vibrant Snap orange
    "pip":     "#3775a9",  # Python blue
    "apt":     "#dd4814",  # Ubuntu/Debian orange
    "dnf":     "#3C6EB4",  # Fedora blue
    "zypper":  "#73BA25",  # openSUSE green
    "portage": "#54487A",  # Gentoo purple
    "xbps":    "#478061",  # Void Linux teal
    "apk":     "#0D597F",  # Alpine blue
    "winget":  "#00a4ef",  # Windows blue
    "choco":   "#8b4513",  # SaddleBrown
    "scoop":   "#ff8c00",  # DarkOrange
    "windows_native": "#0078d4", # Windows Native blue
    "brew":    "#f2b144",  # Homebrew brown/orange
    "macports":"#2a5078",  # MacPorts blue
    "nix":     "#5277c3",  # Nix blue
    "fink":    "#8b0000",  # Fink dark red
    "npm":     "#cb3837",  # npm red
    "cargo":   "#f46623",  # Rust cargo orange
    "gem":     "#701516",  # Ruby gem dark red
}

# Modern, crisp font stack
MODERN_FONT = ("Inter", "Roboto", "Segoe UI", "Ubuntu", "Cantarell", "sans-serif")

BACKEND_LABELS = {
    "pacman":  "pacman",
    "flatpak": "Flatpak",
    "snap":    "Snap",
    "pip":     "pip",
    "apt":     "APT",
    "dnf":     "DNF",
    "zypper":  "Zypper",
    "portage": "Portage",
    "xbps":    "XBPS",
    "apk":     "APK",
    "winget":  "Winget",
    "choco":   "Choco",
    "scoop":   "Scoop",
    "windows_native": "Windows",
    "brew":    "Brew",
    "macports":"MacPorts",
    "nix":     "Nix",
    "fink":    "Fink",
    "npm":     "npm",
    "cargo":   "Cargo",
    "gem":     "Gem",
}


class SearchBar(ctk.CTkFrame):
    def __init__(self, master, search_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.search_callback = search_callback
        self.grid_columnconfigure(0, weight=1)
        self.entry = ctk.CTkEntry(self, placeholder_text="Search packages (e.g. firefox, vlc)...", font=ctk.CTkFont(family=MODERN_FONT[0], size=14))
        self.entry.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.entry.bind("<Return>", self.on_search)
        self.search_btn = ctk.CTkButton(self, text="Search", width=80, command=self.on_search, font=ctk.CTkFont(family=MODERN_FONT[0], weight="bold"))
        self.search_btn.grid(row=0, column=1, padx=(5, 10), pady=10)

    def on_search(self, event=None):
        query = self.entry.get().strip()
        self.search_callback(query)


class BackendFilterBar(ctk.CTkFrame):
    def __init__(self, master, backends, on_filter_change, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_filter_change = on_filter_change
        self.active_backends = set(b.BACKEND_ID for b in backends)
        self._buttons = {}
        label = ctk.CTkLabel(self, text="Filter:", text_color="gray", font=ctk.CTkFont(family=MODERN_FONT[0], size=13))
        label.pack(side="left", padx=(8, 4))
        all_btn = ctk.CTkButton(self, text="All", width=60, height=26, fg_color=("gray70", "gray30"), command=self._select_all)
        all_btn.pack(side="left", padx=2)
        for backend in backends:
            bid = backend.BACKEND_ID
            color = BACKEND_COLORS.get(bid, "gray")
            btn = ctk.CTkButton(self, text=BACKEND_LABELS.get(bid, bid), width=70, height=26, fg_color=color, font=ctk.CTkFont(family=MODERN_FONT[0], size=11, weight="bold"), command=lambda b=bid: self._toggle(b))
            btn.pack(side="left", padx=2)
            self._buttons[bid] = btn

    def _toggle(self, backend_id):
        if backend_id in self.active_backends:
            self.active_backends.discard(backend_id)
            self._buttons[backend_id].configure(fg_color=("gray60", "gray35"))
        else:
            self.active_backends.add(backend_id)
            self._buttons[backend_id].configure(fg_color=BACKEND_COLORS.get(backend_id, "gray"))
        self.on_filter_change(self.active_backends)

    def _select_all(self):
        for bid, btn in self._buttons.items():
            btn.configure(fg_color=BACKEND_COLORS.get(bid, "gray"))
        self.active_backends = set(self._buttons.keys())
        self.on_filter_change(self.active_backends)


class PackageListFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, on_select_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_select_callback = on_select_callback
        self.item_frames = []
        self.selected_item = None
        self._all_packages = []
        self._active_backends = None
        self._spinner_idx = 0
        self._spinner_job = None
        self._loading_backends = 0
        self._spinner_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._spinner_label = ctk.CTkLabel(self._spinner_frame, text="", font=ctk.CTkFont(family=MODERN_FONT[0], size=16))
        self._spinner_label.pack(side="left", padx=(8, 4))
        self._spinner_text = ctk.CTkLabel(self._spinner_frame, text="Searching…", font=ctk.CTkFont(family=MODERN_FONT[0], size=13))
        self._spinner_text.pack(side="left")
        self._bind_scroll_recursive(self)

    def start_loading(self, count=1):
        self._loading_backends += count
        if self._spinner_job is None:
            self._spinner_frame.pack(fill="x", padx=10, pady=6)
            self._animate_spinner()

    def stop_one_backend(self):
        self._loading_backends = max(0, self._loading_backends - 1)
        if self._loading_backends == 0: self._hide_spinner()

    def _animate_spinner(self):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spinner_label.configure(text=frames[self._spinner_idx % len(frames)])
        self._spinner_idx += 1
        self._spinner_job = self.after(80, self._animate_spinner)

    def _hide_spinner(self):
        if self._spinner_job: self.after_cancel(self._spinner_job); self._spinner_job = None
        self._spinner_frame.pack_forget()

    def add_packages(self, packages, from_filter=False):
        if not from_filter: self._all_packages.extend(packages)
        if self._spinner_job is not None: self._spinner_frame.pack_forget()
        to_add = packages
        if self._active_backends is not None:
            to_add = [p for p in to_add if p.get("backend") in self._active_backends]
        for pkg in to_add[:100]:
            item = PackageListItem(self, pkg, self.on_item_click)
            item.pack(fill="x", padx=5, pady=2)
            self.item_frames.append(item)
            self._bind_scroll_recursive(item)
        if self._spinner_job is not None: self._spinner_frame.pack(fill="x", padx=10, pady=6)

    def _bind_scroll_recursive(self, widget):
        """Ironclad recursive binding for the scroll wheel."""
        def on_mouse_scroll(event):
            delta = 0
            if event.num == 4: delta = -1
            elif event.num == 5: delta = 1
            elif hasattr(event, "delta") and event.delta != 0: delta = -1 if event.delta > 0 else 1
            if delta != 0:
                try: self._canvas.yview_scroll(delta, "units")
                except: pass
        widget.bind("<MouseWheel>", on_mouse_scroll, add="+")
        widget.bind("<Button-4>", on_mouse_scroll, add="+")
        widget.bind("<Button-5>", on_mouse_scroll, add="+")
        for child in widget.winfo_children(): self._bind_scroll_recursive(child)

    def apply_filter(self, active_backends):
        self._active_backends = active_backends
        self.clear()
        self.add_packages(self._all_packages, from_filter=True)

    def clear(self):
        for item in self.item_frames: item.destroy()
        self.item_frames.clear(); self.selected_item = None

    def on_item_click(self, item_frame, pkg_data):
        if self.selected_item: self.selected_item.set_selected(False)
        self.selected_item = item_frame; self.selected_item.set_selected(True)
        self.on_select_callback(pkg_data)


class PackageListItem(ctk.CTkFrame):
    def __init__(self, master, pkg_data, click_callback, **kwargs):
        super().__init__(master, corner_radius=15, fg_color=("gray90", "#252525"), border_width=1, border_color=("gray80", "#333333"), **kwargs)
        self.pkg_data = pkg_data; self.click_callback = click_callback
        self.grid_columnconfigure(1, weight=1)
        backend = pkg_data.get("backend", "pacman")
        icon_img = icon_resolver.get_icon_image(pkg_data.get("Icon", ""), size=(40, 40)) or icon_resolver.get_placeholder_icon(size=(40, 40))
        self.icon_label = ctk.CTkLabel(self, text="", image=icon_img)
        self.icon_label.grid(row=0, column=0, rowspan=2, padx=(15, 5), pady=10)
        self.name_label = ctk.CTkLabel(self, text=pkg_data.get("Name", "Unknown"), font=ctk.CTkFont(family=MODERN_FONT[0], size=14, weight="bold"), anchor="w")
        self.name_label.grid(row=0, column=1, padx=(5, 15), pady=(12, 0), sticky="ew")
        badge = ctk.CTkLabel(self, text=BACKEND_LABELS.get(backend, backend).upper(), fg_color=BACKEND_COLORS.get(backend, "gray"), corner_radius=20, text_color="white", font=ctk.CTkFont(family=MODERN_FONT[0], size=9, weight="bold"), width=65, height=20)
        badge.place(relx=1.0, x=-15, y=15, anchor="ne")
        desc = pkg_data.get("Description", "No description available.")
        if len(desc) > 85: desc = desc[:82] + "..."
        self.desc_label = ctk.CTkLabel(self, text=desc, text_color=("gray40", "gray60"), anchor="w", font=ctk.CTkFont(family=MODERN_FONT[0], size=12), wraplength=280)
        self.desc_label.grid(row=1, column=1, padx=(5, 15), pady=(2, 12), sticky="w")
        for w in [self, self.name_label, self.desc_label, self.icon_label]:
            w.bind("<Button-1>", self.on_click); w.bind("<Enter>", self.on_enter); w.bind("<Leave>", self.on_leave)

    def on_enter(self, event): self.configure(fg_color=("gray85", "#2e2e2e"), border_color=("#0099ff", "#0099ff"))
    def on_leave(self, event):
        if not getattr(self, "_selected", False): self.configure(fg_color=("gray90", "#252525"), border_color=("gray80", "#333333"))
    def on_click(self, event): self.click_callback(self, self.pkg_data)
    def set_selected(self, selected: bool):
        self._selected = selected
        if selected: self.configure(fg_color=("#eef7ff", "#1a2a3a"), border_color=("#0099ff", "#0099ff"), border_width=2)
        else: self.configure(fg_color=("gray90", "#252525"), border_color=("gray80", "#333333"), border_width=1)


class PackageDetailFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, on_install, on_remove, on_run=None, fetch_extended_info=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_install = on_install; self.on_remove = on_remove; self.on_run = on_run; self.fetch_extended_info = fetch_extended_info; self.current_pkg = None
        self.grid_columnconfigure(0, weight=1)
        self.hero_frame = ctk.CTkFrame(self, height=120, corner_radius=15, fg_color="#333333")
        self.hero_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ew"); self.hero_frame.grid_propagate(False); self.hero_frame.grid_columnconfigure(1, weight=1)
        self.hero_icon = ctk.CTkLabel(self.hero_frame, text=""); self.hero_icon.grid(row=0, column=0, padx=25, pady=20, sticky="w")
        self.title_label = ctk.CTkLabel(self.hero_frame, text="Select a package", font=ctk.CTkFont(family=MODERN_FONT[0], size=24, weight="bold"), text_color="white", anchor="w")
        self.title_label.grid(row=0, column=1, padx=15, pady=20, sticky="w")
        self.desc_textbox = ctk.CTkTextbox(self, height=100, wrap="word", font=ctk.CTkFont(family=MODERN_FONT[0], size=14)); self.desc_textbox.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent"); self.action_frame.grid(row=2, column=0, padx=20, pady=15, sticky="ew")
        self.install_btn = ctk.CTkButton(self.action_frame, text="Install", command=self.handle_install, fg_color="#2eb354", height=40, corner_radius=12, font=ctk.CTkFont(weight="bold"))
        self.remove_btn = ctk.CTkButton(self.action_frame, text="Remove", command=self.handle_remove, fg_color="#e53935", height=40, corner_radius=12, font=ctk.CTkFont(weight="bold"))
        self.run_btn = ctk.CTkButton(self.action_frame, text="Launch", command=self.handle_run, fg_color="#1a73e8", height=40, corner_radius=12, font=ctk.CTkFont(weight="bold"))
        self.meta_frame = ctk.CTkFrame(self, fg_color=("gray95", "#2a2a2a"), corner_radius=15); self.meta_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.depends_text = ctk.CTkTextbox(self.meta_frame, height=80, wrap="word", font=ctk.CTkFont(size=12)); self.depends_text.pack(fill="x", padx=15, pady=15)
        self._bind_scroll_recursive(self)

    def display_package(self, pkg):
        self.current_pkg = pkg; backend = pkg.get("backend", "pacman"); color = BACKEND_COLORS.get(backend, "gray")
        self.title_label.configure(text=pkg.get("Name", "Unknown")); self.hero_frame.configure(fg_color=color)
        self.hero_icon.configure(image=icon_resolver.get_icon_image(pkg.get("Icon", ""), size=(64, 64)) or icon_resolver.get_placeholder_icon(size=(64, 64)))
        self._set_text(self.desc_textbox, pkg.get("Description", "No description available."))
        self.install_btn.pack_forget(); self.remove_btn.pack_forget(); self.run_btn.pack_forget()
        if pkg.get("is_installed"): self.remove_btn.pack(side="left", padx=5); self.run_btn.pack(side="left", padx=5)
        else: self.install_btn.pack(side="left", padx=5)
        if self.fetch_extended_info: self._set_text(self.depends_text, "Loading details..."); self.fetch_extended_info(pkg, self._on_extended_info)

    def _on_extended_info(self, info): self.after(0, lambda: self._set_text(self.depends_text, info.get("Depends On", "None")))
    def _set_text(self, widget, text): widget.configure(state="normal"); widget.delete("1.0", "end"); widget.insert("1.0", text); widget.configure(state="disabled")
    def _bind_scroll_recursive(self, widget):
        """Ironclad recursive binding for the scroll wheel."""
        def on_mouse_scroll(event):
            delta = 0
            if event.num == 4: delta = -1
            elif event.num == 5: delta = 1
            elif hasattr(event, "delta") and event.delta != 0: delta = -1 if event.delta > 0 else 1
            if delta != 0:
                try: self._canvas.yview_scroll(delta, "units")
                except: pass
        widget.bind("<MouseWheel>", on_mouse_scroll, add="+")
        widget.bind("<Button-4>", on_mouse_scroll, add="+")
        widget.bind("<Button-5>", on_mouse_scroll, add="+")
        for child in widget.winfo_children(): self._bind_scroll_recursive(child)
    def handle_install(self):
        if self.current_pkg: self.on_install(self.current_pkg)
    def handle_remove(self):
        if self.current_pkg: self.on_remove(self.current_pkg)
    def handle_run(self):
        if self.current_pkg and self.on_run: self.on_run(self.current_pkg.get("Exec") or self.current_pkg.get("Name"))
