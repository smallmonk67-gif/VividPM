import customtkinter as ctk
import datetime
from vivid_gui import icon_resolver
from vivid_gui.config_manager import config_manager

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
    "linux_native": "#6b6b6b", # Linux Native gray
    "web_app": "#06b6d4", # Cyan PWA color
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
    "linux_native": "Linux",
    "web_app": "Web App",
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
        
        # Load from config, default to all backends if empty
        saved_filters = config_manager.get("startup_filters")
        if saved_filters:
            self.active_backends = set(bid for bid in saved_filters if any(b.BACKEND_ID == bid for b in backends))
            # In case saved filters are all invalid/empty, fall back to all backends
            if not self.active_backends:
                self.active_backends = set(b.BACKEND_ID for b in backends)
        else:
            self.active_backends = set(b.BACKEND_ID for b in backends)
            
        self._buttons = {}
        
        self._label = ctk.CTkLabel(self, text="Filter:", text_color="gray", font=ctk.CTkFont(family=MODERN_FONT[0], size=13))
        self._all_btn = ctk.CTkButton(self, text="All", width=60, height=26, fg_color=("gray70", "gray30"), corner_radius=13, command=self._select_all)
        
        for backend in backends:
            bid = backend.BACKEND_ID
            color = BACKEND_COLORS.get(bid, "gray") if bid in self.active_backends else ("gray60", "gray35")
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
        self._scroll_y = 0.0
        self.pool_size = 0  # Will be calculated dynamically
        self._pool = []
        self._item_height = 79 # 75 height + 4 padding
        self._container_height = 100
        
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
        
        # Scrollbar
        self.scrollbar = ctk.CTkScrollbar(self, command=self._on_scrollbar)
        self.scrollbar.grid(row=1, column=1, sticky="ns")
            
        # Bindings
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Button-4>", self._on_mousewheel)
        self.bind("<Button-5>", self._on_mousewheel)
        self.items_container.bind("<MouseWheel>", self._on_mousewheel)
        self.items_container.bind("<Configure>", self._on_container_configure)
        for child in self.winfo_children():
            self._bind_mousewheel_recursive(child)

    def _on_container_configure(self, event):
        self._container_height = event.height
        # Pool size is enough to cover the screen + 2 for top/bottom partial items
        fit_count = max(1, event.height // self._item_height) + 2
        if fit_count != self.pool_size:
            self.pool_size = fit_count
            self._update_pool()
        elif hasattr(self, "_filtered_packages"):
            self._update_visible_items()

    def _update_pool(self):
        # Expand pool
        while len(self._pool) < self.pool_size:
            item = PackageListItem(self.items_container, self.on_item_click)
            self._bind_mousewheel_recursive(item)
            self._pool.append(item)
            
        # Shrink pool
        while len(self._pool) > self.pool_size:
            item = self._pool.pop()
            item.destroy()
            
        if hasattr(self, "_filtered_packages"):
            self._update_visible_items()

    def _bind_mousewheel_recursive(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_mousewheel, add="+")
        widget.bind("<Button-5>", self._on_mousewheel, add="+")
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child)

    def _on_scrollbar(self, *args):
        total_height = len(self._filtered_packages) * self._item_height
        max_scroll_y = max(0.0, total_height - self._container_height)
        
        if len(args) == 2 and args[0] == "moveto":
            fraction = float(args[1])
            self._pending_scroll_y = min(max_scroll_y, fraction * total_height)
            if not getattr(self, "_scrollbar_scheduled", False):
                self._scrollbar_scheduled = True
                self.after_idle(self._process_scrollbar_moveto)
        elif len(args) == 3 and args[0] == "scroll":
            delta = int(args[1])
            self._scroll_by(delta * 40.0)

    def _process_scrollbar_moveto(self):
        self._scrollbar_scheduled = False
        if hasattr(self, "_pending_scroll_y"):
            self._scroll_y = self._pending_scroll_y
            self._update_visible_items()

    def _on_mousewheel(self, event):
        delta = 0
        if event.num == 4: delta = -40
        elif event.num == 5: delta = 40
        elif hasattr(event, "delta") and event.delta != 0: 
            delta = -40 if event.delta > 0 else 40
        
        if delta != 0:
            if not hasattr(self, "_pending_scroll"):
                self._pending_scroll = 0.0
            self._pending_scroll += delta
            
            if not getattr(self, "_scroll_scheduled", False):
                self._scroll_scheduled = True
                self.after_idle(self._process_pending_scroll)

    def _process_pending_scroll(self):
        self._scroll_scheduled = False
        delta = getattr(self, "_pending_scroll", 0.0)
        self._pending_scroll = 0.0
        if delta != 0:
            self._scroll_by(delta)

    def _scroll_by(self, delta_pixels):
        max_scroll_y = max(0.0, len(self._filtered_packages) * self._item_height - self._container_height)
        self._scroll_y = max(0.0, min(max_scroll_y, self._scroll_y + delta_pixels))
        self._update_visible_items()

    def _update_visible_items(self):
        total_items = len(self._filtered_packages)
        total_height = total_items * self._item_height
        max_scroll_y = max(0.0, total_height - self._container_height)
        
        # Clamp scroll position
        self._scroll_y = max(0.0, min(max_scroll_y, self._scroll_y))
        
        if total_height <= self._container_height or total_height == 0:
            self.scrollbar.set(0.0, 1.0)
        else:
            first = self._scroll_y / total_height
            last = min(1.0, (self._scroll_y + self._container_height) / total_height)
            self.scrollbar.set(first, last)
            
        start_idx = int(self._scroll_y // self._item_height)
        y_offset = -(self._scroll_y % self._item_height)
        
        for i, item in enumerate(self._pool):
            idx = start_idx + i
            if idx < total_items:
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
                        
                # Use absolute placing for smooth scrolling
                item.place(relwidth=1.0, x=0, y=y_offset + i * self._item_height)
            else:
                item.place_forget()

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
        
        self._update_visible_items()

    def clear(self, keep_cache=False):
        self._scroll_y = 0.0
        self.selected_item = None
        self.selected_pkg_id = None
        for item in self._pool:
            item.pkg_data = {}  # Reset stale data so update_data early-return doesn't skip
            if item.winfo_ismapped():
                item.place_forget()
        if not keep_cache:
            self._all_packages.clear()
            self._filtered_packages.clear()
        self.scrollbar.set(0.0, 1.0)
        self._loading_backends = 0
        self._hide_spinner()

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
        pkg_id = f"{pkg_data.get('backend')}:{pkg_data.get('Name')}"
        current_id = f"{self.pkg_data.get('backend')}:{self.pkg_data.get('Name')}" if self.pkg_data else ""
        
        if pkg_id == current_id:
            return

        self.pkg_data = pkg_data
        backend = pkg_data.get("backend", "pacman")
        def _on_icon_ready(img):
            if self.winfo_exists() and getattr(self, "pkg_data", {}).get("Name") == pkg_data.get("Name"):
                self.icon_label.configure(image=img)

        icon_img = icon_resolver.get_icon_image(
            pkg_data.get("Icon", ""), 
            size=(40, 40),
            on_ready=lambda img: self.after(0, _on_icon_ready, img)
        ) or icon_resolver.get_placeholder_icon(size=(40, 40))
        self.icon_label.configure(image=icon_img)
        self.name_label.configure(text=pkg_data.get("Name", "Unknown"))
        self.badge.configure(text=BACKEND_LABELS.get(backend, backend).upper(), fg_color=BACKEND_COLORS.get(backend, "gray"))
        desc = pkg_data.get("Description", "No description available.")
        if len(desc) > 85: desc = desc[:82] + "..."
        self.desc_label.configure(text=desc)

    def on_enter(self, event): self.configure(fg_color=("gray85", "#2e2e2e"), border_color=("#0099ff", "#0099ff"))
    def on_leave(self, event):
        if not getattr(self, "_selected", False): self.configure(fg_color=("gray90", "#252525"), border_color=("gray80", "#333333"))
    def on_click(self, event): self.click_callback(self, self.pkg_data)
    def set_selected(self, selected: bool):
        if getattr(self, "_selected", None) == selected:
            return
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
        # Description Box Container with borders
        self.desc_frame = ctk.CTkFrame(self, fg_color=("white", "#222222"), border_width=1, border_color=("gray80", "#333333"), corner_radius=15)
        self.desc_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.desc_textbox = ctk.CTkTextbox(self.desc_frame, height=100, wrap="word", font=ctk.CTkFont(family=MODERN_FONT[0], size=14), fg_color="transparent")
        self.desc_textbox.pack(fill="both", expand=True, padx=10, pady=10)

        self.action_frame = ctk.CTkFrame(self, fg_color="transparent"); self.action_frame.grid(row=2, column=0, padx=20, pady=15, sticky="ew")
        self.install_btn = ctk.CTkButton(self.action_frame, text="Install", command=self.handle_install, fg_color="#2eb354", height=40, corner_radius=12, font=ctk.CTkFont(weight="bold"))
        self.remove_btn = ctk.CTkButton(self.action_frame, text="Remove", command=self.handle_remove, fg_color="#e53935", height=40, corner_radius=12, font=ctk.CTkFont(weight="bold"))
        self.run_btn = ctk.CTkButton(self.action_frame, text="Launch", command=self.handle_run, fg_color="#1a73e8", height=40, corner_radius=12, font=ctk.CTkFont(weight="bold"))
        
        # Meta Frame with borders
        self.meta_frame = ctk.CTkFrame(self, fg_color=("white", "#222222"), border_width=1, border_color=("gray80", "#333333"), corner_radius=15)
        self.meta_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.depends_text = ctk.CTkTextbox(self.meta_frame, height=80, wrap="word", font=ctk.CTkFont(size=12), fg_color="transparent"); self.depends_text.pack(fill="x", padx=15, pady=15)
        self._bind_scroll_recursive(self)

    def display_package(self, pkg):
        self.current_pkg = pkg; backend = pkg.get("backend", "pacman"); color = BACKEND_COLORS.get(backend, "gray")
        self.title_label.configure(text=pkg.get("Name", "Unknown")); self.hero_frame.configure(fg_color=color)
        def _on_hero_icon_ready(img):
            if self.winfo_exists() and self.current_pkg and self.current_pkg.get("Name") == pkg.get("Name"):
                self.hero_icon.configure(image=img)
                
        icon_img = icon_resolver.get_icon_image(
            pkg.get("Icon", ""), 
            size=(64, 64),
            on_ready=lambda img: self.after(0, _on_hero_icon_ready, img)
        ) or icon_resolver.get_placeholder_icon(size=(64, 64))
        self.hero_icon.configure(image=icon_img)
        self._set_text(self.desc_textbox, pkg.get("Description", "No description available."))
        self.install_btn.pack_forget(); self.remove_btn.pack_forget(); self.run_btn.pack_forget()
        if pkg.get("is_installed"): self.remove_btn.pack(side="left", padx=5); self.run_btn.pack(side="left", padx=5)
        else: self.install_btn.pack(side="left", padx=5)
        if self.fetch_extended_info: self._set_text(self.depends_text, "Loading details..."); self.fetch_extended_info(pkg, self._on_extended_info)

    def _on_extended_info(self, info, pkg): 
        if self.current_pkg != pkg: return
        self.after(0, lambda: self._set_text(self.depends_text, info.get("Depends On", "None")))
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
        self.geometry("400x570")
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
        
        # Active Startup Filters Setting
        self.filters_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filters_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=10)
        
        self.filters_label = ctk.CTkLabel(self.filters_frame, text="Active Backends on Startup", font=ctk.CTkFont(weight="bold"))
        self.filters_label.pack(anchor="w", pady=(0, 5))
        
        self.filters_container = ctk.CTkFrame(self.filters_frame, fg_color=("gray90", "#181818"), border_width=1, border_color=("gray80", "#333333"), corner_radius=10)
        self.filters_container.pack(fill="x", ipady=8, ipadx=10)
        
        # Grid layout for checkboxes
        self.checkbox_vars = {}
        backends = self.master.pkg_manager.backends
        saved_filters = self.config_manager.get("startup_filters", [])
        if not saved_filters:
            saved_filters = [b.BACKEND_ID for b in backends]
            
        row_idx = 0
        col_idx = 0
        for backend in backends:
            bid = backend.BACKEND_ID
            label_text = BACKEND_LABELS.get(bid, bid)
            var = ctk.BooleanVar(value=(bid in saved_filters))
            self.checkbox_vars[bid] = var
            
            cb = ctk.CTkCheckBox(self.filters_container, text=label_text, variable=var, font=ctk.CTkFont(family=MODERN_FONT[0], size=11))
            cb.grid(row=row_idx, column=col_idx, padx=12, pady=6, sticky="w")
            
            col_idx += 1
            if col_idx >= 3:
                col_idx = 0
                row_idx += 1
        
        # Web Icons Setting
        self.web_icons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.web_icons_frame.grid(row=4, column=0, sticky="ew", padx=30, pady=10)
        self.web_icons_var = ctk.BooleanVar(value=self.config_manager.get("fetch_web_icons", True))
        self.web_icons_cb = ctk.CTkSwitch(self.web_icons_frame, text="Fetch Missing Icons from Web", variable=self.web_icons_var, font=ctk.CTkFont(weight="bold"))
        self.web_icons_cb.pack(anchor="w")

        # Apply Button
        self.apply_btn = ctk.CTkButton(self, text="Apply & Save", command=self.save_and_apply, height=40, font=ctk.CTkFont(weight="bold"))
        self.apply_btn.grid(row=5, column=0, pady=(20, 10))

        # Make it modal
        self.transient(master)
        self.grab_set()

    def save_and_apply(self):
        new_theme = self.theme_var.get()
        new_accent = self.accent_var.get()
        
        self.config_manager.set("theme", new_theme)
        self.config_manager.set("accent_color", new_accent)
        self.config_manager.set("fetch_web_icons", self.web_icons_var.get())
        
        # Gather and save startup filters
        selected_filters = [bid for bid, var in self.checkbox_vars.items() if var.get()]
        self.config_manager.set("startup_filters", selected_filters)
        
        self.apply_callback(new_theme, new_accent)
        
        # Live update filter buttons and results
        if hasattr(self.master, "filter_bar"):
            self.master.filter_bar.active_backends = set(selected_filters)
            for bid, btn in self.master.filter_bar._buttons.items():
                if bid in selected_filters:
                    btn.configure(fg_color=BACKEND_COLORS.get(bid, "gray"))
                else:
                    btn.configure(fg_color=("gray60", "gray35"))
            self.master.handle_filter_change(set(selected_filters))
            
        self.destroy()
