import customtkinter as ctk
import datetime
from vivid_gui import icon_resolver

# Premium color palette
BACKEND_COLORS = {
    "pacman":  "#0099ff",  # Brighter Arch blue
    "aur":     "#209fb5",  # Teal/Blue for AUR
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
    "aur":     "AUR",
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
        
        self._label = ctk.CTkLabel(self, text="Filter:", text_color="gray", font=ctk.CTkFont(family=MODERN_FONT[0], size=13))
        self._all_btn = ctk.CTkButton(self, text="All", width=60, height=26, fg_color=("gray70", "gray30"), corner_radius=13, command=self._select_all)
        
        for backend in backends:
            bid = backend.BACKEND_ID
            color = BACKEND_COLORS.get(bid, "gray")
            btn = ctk.CTkButton(self, text=BACKEND_LABELS.get(bid, bid), width=70, height=26, fg_color=color, corner_radius=13, font=ctk.CTkFont(family=MODERN_FONT[0], size=11, weight="bold"), command=lambda b=bid: self._toggle(b))
            self._buttons[bid] = btn
            
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event):
        width = event.width
        if getattr(self, "_last_width", 0) == width:
            return
        self._last_width = width
        self.arrange_buttons(width)

    def arrange_buttons(self, width=None):
        if width is None:
            width = self.winfo_width()
        
        # Deduct padding/margin to trigger wrapping before container edge compression starts.
        # This keeps the button widths from being squished down to squares.
        width -= 24
        if width <= 10:
            width = 296
            
        widgets = []
        if hasattr(self, "_label") and self._label.winfo_exists():
            widgets.append((self._label, 50))
        if hasattr(self, "_all_btn") and self._all_btn.winfo_exists():
            widgets.append((self._all_btn, 60))
            
        for bid in sorted(self._buttons.keys()):
            btn = self._buttons[bid]
            if btn.winfo_exists():
                widgets.append((btn, 72))
                
        padx = 4
        pady = 4
        current_x = 0
        current_row = 0
        current_col = 0
        
        for w, _ in widgets:
            w.grid_forget()
            
        for w, w_width in widgets:
            if current_x + w_width + padx > width and current_x > 0:
                current_row += 1
                current_x = 0
                current_col = 0
            w.grid(row=current_row, column=current_col, padx=padx//2, pady=pady//2, sticky="w")
            current_x += w_width + padx
            current_col += 1

    def rebuild(self, backends):
        for btn in self._buttons.values():
            btn.destroy()
        self._buttons.clear()
        self.active_backends = set(b.BACKEND_ID for b in backends)
        for backend in backends:
            bid = backend.BACKEND_ID
            color = BACKEND_COLORS.get(bid, "gray")
            btn = ctk.CTkButton(self, text=BACKEND_LABELS.get(bid, bid), width=70, height=26, fg_color=color, corner_radius=13, font=ctk.CTkFont(family=MODERN_FONT[0], size=11, weight="bold"), command=lambda b=bid: self._toggle(b))
            self._buttons[bid] = btn
        self.arrange_buttons()

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


class PackageListFrame(ctk.CTkFrame):
    def __init__(self, master, on_select_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_select_callback = on_select_callback
        self.selected_item = None
        self.selected_pkg_id = None
        self._all_packages = []
        self._filtered_packages = []
        self._active_backends = None
        
        self._spinner_idx = 0
        self._spinner_job = None
        self._loading_backends = 0
        
        # Virtual Scrolling State
        self._start_index = 0
        self.pool_size = 20
        self._pool = []
        
        # Layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Spinner
        self._spinner_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._spinner_label = ctk.CTkLabel(self._spinner_frame, text="", font=ctk.CTkFont(family=MODERN_FONT[0], size=16))
        self._spinner_label.pack(side="left", padx=(8, 4))
        self._spinner_text = ctk.CTkLabel(self._spinner_frame, text="Searching…", font=ctk.CTkFont(family=MODERN_FONT[0], size=13))
        self._spinner_text.pack(side="left")
        self._spinner_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=6)
        self._spinner_frame.grid_remove()
        
        # Items container
        self.items_container = ctk.CTkFrame(self, fg_color="transparent")
        self.items_container.grid(row=1, column=0, sticky="nsew")
        self.items_container.grid_columnconfigure(0, weight=1)
        
        # Scrollbar
        self.scrollbar = ctk.CTkScrollbar(self, command=self._on_scrollbar)
        self.scrollbar.grid(row=1, column=1, sticky="ns")
        
        # Initialize Pool
        for _ in range(self.pool_size):
            item = PackageListItem(self.items_container, self.on_item_click)
            self._pool.append(item)
            
        # Bind Mouse Wheel
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Button-4>", self._on_mousewheel)
        self.bind("<Button-5>", self._on_mousewheel)
        self.items_container.bind("<MouseWheel>", self._on_mousewheel)
        for child in self.winfo_children():
            self._bind_mousewheel_recursive(child)

    def _bind_mousewheel_recursive(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_mousewheel, add="+")
        widget.bind("<Button-5>", self._on_mousewheel, add="+")
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child)

    def _on_scrollbar(self, *args):
        if len(args) == 2 and args[0] == "moveto":
            fraction = float(args[1])
            max_idx = max(0, len(self._filtered_packages) - self.pool_size)
            self._start_index = int(fraction * max_idx)
            self._update_visible_items()
        elif len(args) == 3 and args[0] == "scroll":
            delta = int(args[1])
            self._scroll_by(delta)

    def _on_mousewheel(self, event):
        delta = 0
        if event.num == 4: delta = -1
        elif event.num == 5: delta = 1
        elif hasattr(event, "delta") and event.delta != 0: delta = -1 if event.delta > 0 else 1
        if delta != 0:
            self._scroll_by(delta * 2)

    def _scroll_by(self, delta):
        max_idx = max(0, len(self._filtered_packages) - self.pool_size)
        self._start_index = max(0, min(max_idx, self._start_index + delta))
        self._update_visible_items()

    def _update_visible_items(self):
        total = len(self._filtered_packages)
        if total <= self.pool_size:
            self.scrollbar.set(0.0, 1.0)
        else:
            fraction_visible = self.pool_size / total
            first = self._start_index / total
            last = min(1.0, first + fraction_visible)
            self.scrollbar.set(first, last)
            
        for i, item in enumerate(self._pool):
            idx = self._start_index + i
            if idx < total:
                pkg = self._filtered_packages[idx]
                item.update_data(pkg)
                
                pkg_id = f"{pkg.get('backend')}:{pkg.get('Name')}"
                if self.selected_pkg_id == pkg_id:
                    item.set_selected(True)
                    self.selected_item = item
                else:
                    item.set_selected(False)
                    if self.selected_item == item:
                        self.selected_item = None
                        
                if not item.winfo_ismapped():
                    item.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            else:
                if item.winfo_ismapped():
                    item.grid_remove()

    def start_loading(self, count=1):
        self._loading_backends += count
        if self._spinner_job is None:
            self._spinner_frame.grid()
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
        self._spinner_frame.grid_remove()

    def add_packages(self, packages, from_filter=False):
        if not from_filter: 
            self._all_packages.extend(packages)
        if self._spinner_job is not None: 
            self._spinner_frame.grid_remove()
            
        self._apply_current_filter()
        
        if self._spinner_job is not None: 
            self._spinner_frame.grid()

    def apply_filter(self, active_backends):
        self._active_backends = active_backends
        self._apply_current_filter()

    def _apply_current_filter(self):
        if self._active_backends is not None:
            self._filtered_packages = [p for p in self._all_packages if p.get("backend") in self._active_backends]
        else:
            self._filtered_packages = list(self._all_packages)
        
        max_idx = max(0, len(self._filtered_packages) - self.pool_size)
        if self._start_index > max_idx:
            self._start_index = max_idx
            
        self._update_visible_items()

    def clear(self, keep_cache=False):
        self._start_index = 0
        self.selected_item = None
        self.selected_pkg_id = None
        for item in self._pool:
            if item.winfo_ismapped():
                item.grid_remove()
        if not keep_cache:
            self._all_packages.clear()
            self._filtered_packages.clear()
        self.scrollbar.set(0.0, 1.0)

    def on_item_click(self, item_frame, pkg_data):
        if self.selected_item: self.selected_item.set_selected(False)
        self.selected_item = item_frame
        self.selected_pkg_id = f"{pkg_data.get('backend')}:{pkg_data.get('Name')}"
        item_frame.set_selected(True)
        self.on_select_callback(pkg_data)


class PackageListItem(ctk.CTkFrame):
    def __init__(self, master, click_callback, **kwargs):
        super().__init__(master, corner_radius=15, fg_color=("gray90", "#252525"), border_width=1, border_color=("gray80", "#333333"), height=75, **kwargs)
        self.grid_propagate(False)
        self.click_callback = click_callback
        self.grid_columnconfigure(1, weight=1)
        self.pkg_data = {}
        
        self.icon_label = ctk.CTkLabel(self, text="")
        self.icon_label.grid(row=0, column=0, rowspan=2, padx=(15, 5), pady=10)
        self.name_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(family=MODERN_FONT[0], size=14, weight="bold"), anchor="w")
        self.name_label.grid(row=0, column=1, padx=(5, 15), pady=(12, 0), sticky="ew")
        self.badge = ctk.CTkLabel(self, text="", corner_radius=20, text_color="white", font=ctk.CTkFont(family=MODERN_FONT[0], size=9, weight="bold"), width=65, height=20)
        self.badge.place(relx=1.0, x=-15, y=15, anchor="ne")
        self.desc_label = ctk.CTkLabel(self, text="", text_color=("gray40", "gray60"), anchor="w", font=ctk.CTkFont(family=MODERN_FONT[0], size=12), wraplength=280)
        self.desc_label.grid(row=1, column=1, padx=(5, 15), pady=(2, 12), sticky="w")
        
        for w in [self, self.name_label, self.desc_label, self.icon_label]:
            w.bind("<Button-1>", self.on_click)
            w.bind("<Enter>", self.on_enter)
            w.bind("<Leave>", self.on_leave)

    def update_data(self, pkg_data):
        self.pkg_data = pkg_data
        backend = pkg_data.get("backend", "pacman")
        icon_img = icon_resolver.get_icon_image(pkg_data.get("Icon", ""), size=(40, 40)) or icon_resolver.get_placeholder_icon(size=(40, 40))
        self.icon_label.configure(image=icon_img)
        self.name_label.configure(text=pkg_data.get("Name", "Unknown"))
        self.badge.configure(text=BACKEND_LABELS.get(backend, backend).upper(), fg_color=BACKEND_COLORS.get(backend, "gray"))
        desc = pkg_data.get("Description", "No description available.")
        if len(desc) > 85: desc = desc[:82] + "..."
        self.desc_label.configure(text=desc)
        self.set_selected(getattr(self, "_selected", False))

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
        """Polyfill-Safe recursive binding for the scroll wheel."""
        def on_mouse_scroll(event):
            delta = 0
            if event.num == 4: delta = -1
            elif event.num == 5: delta = 1
            elif hasattr(event, "delta") and event.delta != 0: delta = -1 if event.delta > 0 else 1
            if delta != 0:
                for attr in ["_canvas", "canvas", "_parent_canvas"]:
                    if hasattr(self, attr):
                        try:
                            getattr(self, attr).yview_scroll(delta, "units")
                            break 
                        except: continue
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

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, config_manager, apply_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.config_manager = config_manager
        self.apply_callback = apply_callback
        
        self.title("Settings")
        self.geometry("400x350")
        self.resizable(False, False)
        
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        self.header = ctk.CTkLabel(self, text="Preferences", font=ctk.CTkFont(family=MODERN_FONT[0], size=20, weight="bold"))
        self.header.grid(row=0, column=0, pady=(20, 10))
        
        # Theme Setting
        self.theme_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.theme_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=10)
        
        self.theme_label = ctk.CTkLabel(self.theme_frame, text="Appearance Theme", font=ctk.CTkFont(weight="bold"))
        self.theme_label.pack(anchor="w", pady=(0, 5))
        
        self.theme_var = ctk.StringVar(value=self.config_manager.get("theme", "System"))
        self.theme_seg = ctk.CTkSegmentedButton(self.theme_frame, values=["System", "Light", "Dark"], variable=self.theme_var)
        self.theme_seg.pack(fill="x")
        
        # Accent Color Setting
        self.accent_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.accent_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=10)
        
        self.accent_label = ctk.CTkLabel(self.accent_frame, text="Accent Color", font=ctk.CTkFont(weight="bold"))
        self.accent_label.pack(anchor="w", pady=(0, 5))
        
        self.accent_var = ctk.StringVar(value=self.config_manager.get("accent_color", "blue"))
        self.accent_seg = ctk.CTkSegmentedButton(self.accent_frame, values=["blue", "green", "dark-blue"], variable=self.accent_var)
        self.accent_seg.pack(fill="x")
        
        # Apply Button
        self.apply_btn = ctk.CTkButton(self, text="Apply & Save", command=self.save_and_apply, height=40, font=ctk.CTkFont(weight="bold"))
        self.apply_btn.grid(row=3, column=0, pady=(30, 10))

        # Make it modal
        self.transient(master)
        self.grab_set()

    def save_and_apply(self):
        new_theme = self.theme_var.get()
        new_accent = self.accent_var.get()
        
        self.config_manager.set("theme", new_theme)
        self.config_manager.set("accent_color", new_accent)
        
        self.apply_callback(new_theme, new_accent)
        self.destroy()
