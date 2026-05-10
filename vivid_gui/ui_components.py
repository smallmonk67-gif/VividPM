import customtkinter as ctk
import datetime
from vivid_gui import icon_resolver

# Premium color palette
BACKEND_COLORS = {
    "pacman":  "#0099ff",  # Brighter Arch blue
    "flatpak": "#4180d4",  # Deep Flatpak blue
    "snap":    "#e95420",  # Vibrant Snap orange
    "pip":     "#3775a9",  # Python blue
    # New distro backends
    "apt":     "#dd4814",  # Ubuntu/Debian orange
    "dnf":     "#3C6EB4",  # Fedora blue
    "zypper":  "#73BA25",  # openSUSE green
    "portage": "#54487A",  # Gentoo purple
    "xbps":    "#478061",  # Void Linux teal
    "apk":     "#0D597F",  # Alpine blue
    # Windows backends
    "winget":  "#00a4ef",  # Windows blue
    "choco":   "#8b4513",  # SaddleBrown
    "scoop":   "#ff8c00",  # DarkOrange
    "windows_native": "#0078d4", # Windows Native blue
}

BACKEND_LABELS = {
    "pacman":  "pacman",
    "flatpak": "Flatpak",
    "snap":    "Snap",
    "pip":     "pip",
    # New distro backends
    "apt":     "APT",
    "dnf":     "DNF",
    "zypper":  "Zypper",
    "portage": "Portage",
    "xbps":    "XBPS",
    "apk":     "APK",
    # Windows backends
    "winget":  "Winget",
    "choco":   "Choco",
    "scoop":   "Scoop",
    "windows_native": "Windows",
}


class SearchBar(ctk.CTkFrame):
    def __init__(self, master, search_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.search_callback = search_callback

        self.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(self, placeholder_text="Search packages (e.g. firefox, vlc)...")
        self.entry.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        
        # Bindings for productivity
        self.entry.bind("<Return>", self.on_search)
        self.entry.bind("<Control-a>", self._select_all)
        self.entry.bind("<Control-BackSpace>", self._delete_word)

        self.search_btn = ctk.CTkButton(self, text="Search", width=80, command=self.on_search)
        self.search_btn.grid(row=0, column=1, padx=(5, 10), pady=10)

    def _select_all(self, event=None):
        self.entry.select_range(0, 'end')
        self.entry.icursor('end')
        return "break"

    def _delete_word(self, event=None):
        # Basic implementation of delete word for CTkEntry
        self.entry.delete("insert -1c wordstart", "insert")
        return "break"

    def on_search(self, event=None):
        query = self.entry.get().strip()
        self.search_callback(query)


class BackendFilterBar(ctk.CTkFrame):
    """A row of toggle buttons to filter packages by backend."""
    def __init__(self, master, backends, on_filter_change, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_filter_change = on_filter_change
        self.active_backends = set(b.BACKEND_ID for b in backends)
        self._buttons = {}

        label = ctk.CTkLabel(self, text="Filter:", text_color="gray")
        label.pack(side="left", padx=(8, 4))

        all_btn = ctk.CTkButton(
            self, text="All", width=60, height=26,
            fg_color=("gray70", "gray30"), hover_color=("gray60", "gray40"),
            command=self._select_all
        )
        all_btn.pack(side="left", padx=2)
        self._all_btn = all_btn

        for backend in backends:
            bid = backend.BACKEND_ID
            color = BACKEND_COLORS.get(bid, "gray")
            btn = ctk.CTkButton(
                self,
                text=BACKEND_LABELS.get(bid, bid),
                width=70, height=26,
                fg_color=color,
                hover_color=color,
                command=lambda b=bid: self._toggle(b)
            )
            btn.pack(side="left", padx=2)
            self._buttons[bid] = btn

    def _toggle(self, backend_id):
        if backend_id in self.active_backends:
            self.active_backends.discard(backend_id)
            self._buttons[backend_id].configure(fg_color=("gray60", "gray35"))
        else:
            self.active_backends.add(backend_id)
            color = BACKEND_COLORS.get(backend_id, "gray")
            self._buttons[backend_id].configure(fg_color=color)
        self.on_filter_change(self.active_backends)

    def _select_all(self):
        for bid, btn in self._buttons.items():
            color = BACKEND_COLORS.get(bid, "gray")
            btn.configure(fg_color=color)
        self.active_backends = set(self._buttons.keys())
        self.on_filter_change(self.active_backends)


class PackageListFrame(ctk.CTkScrollableFrame):
    # Braille spinner frames for loading animation
    _SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, master, on_select_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_select_callback = on_select_callback
        self.item_frames = []
        self.selected_item = None
        self._all_packages = []
        self._active_backends = None  # None = show all
        self._spinner_idx = 0
        self._spinner_job = None
        self._loading_backends = 0  # count of in-flight backend searches

        # Spinner row — shown at bottom of list when loading
        self._spinner_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._spinner_label = ctk.CTkLabel(
            self._spinner_frame,
            text="",
            font=ctk.CTkFont(size=16),
            text_color=("gray40", "gray60"),
        )
        self._spinner_label.pack(side="left", padx=(8, 4))
        self._spinner_text = ctk.CTkLabel(
            self._spinner_frame,
            text="Searching…",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray60"),
        )
        self._spinner_text.pack(side="left")

        self._bind_scroll(self)

    # ── Spinner control ──────────────────────────────────────────
    def start_loading(self, count=1):
        """Call once per in-flight backend. Shows spinner."""
        self._loading_backends += count
        if self._spinner_job is None:
            self._spinner_frame.pack(fill="x", padx=10, pady=6)
            self._animate_spinner()

    def stop_one_backend(self):
        """Call when one backend finishes. Hides spinner when all done."""
        self._loading_backends = max(0, self._loading_backends - 1)
        if self._loading_backends == 0:
            self._hide_spinner()

    def stop_loading(self):
        """Force-stop the spinner immediately."""
        self._loading_backends = 0
        self._hide_spinner()

    def _animate_spinner(self):
        frame = self._SPINNER_FRAMES[self._spinner_idx % len(self._SPINNER_FRAMES)]
        self._spinner_label.configure(text=frame)
        self._spinner_idx += 1
        self._spinner_job = self.after(80, self._animate_spinner)

    def _hide_spinner(self):
        if self._spinner_job:
            self.after_cancel(self._spinner_job)
            self._spinner_job = None
        self._spinner_frame.pack_forget()

    # ── Data methods ─────────────────────────────────────────────
    def populate(self, packages):
        self._all_packages = packages
        self.clear()
        self.add_packages(packages)

    def add_packages(self, packages):
        """Append new packages to the list without clearing existing ones."""
        # Temporarily unpack spinner so new items go before it
        if self._spinner_job is not None:
            self._spinner_frame.pack_forget()

        to_add = packages
        if self._active_backends is not None:
            to_add = [p for p in to_add if p.get("backend") in self._active_backends]

        for pkg in to_add:
            item = PackageListItem(self, pkg, self.on_item_click)
            item.pack(fill="x", padx=5, pady=2)
            self.item_frames.append(item)
            self._bind_scroll(item)

        # Re-pack spinner at the end if still loading
        if self._spinner_job is not None:
            self._spinner_frame.pack(fill="x", padx=10, pady=6)

    def apply_filter(self, active_backends):
        self._active_backends = active_backends
        self.clear()
        self.add_packages(self._all_packages)

    def _bind_scroll(self, widget):
        def on_mouse_scroll(event):
            # Handle Linux (Button-4/5) and Windows/macOS (MouseWheel)
            if event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
                self._parent_canvas.yview("scroll", -1, "units")
            elif event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
                self._parent_canvas.yview("scroll", 1, "units")

        widget.bind("<Button-4>", on_mouse_scroll, add="+")
        widget.bind("<Button-5>", on_mouse_scroll, add="+")
        widget.bind("<MouseWheel>", on_mouse_scroll, add="+")
        
        for child in widget.winfo_children():
            self._bind_scroll(child)

    def clear(self):
        for item in self.item_frames:
            item.pack_forget()
            item.destroy()
        self.item_frames.clear()
        self.selected_item = None

    def on_item_click(self, item_frame, pkg_data):
        if self.selected_item:
            self.selected_item.set_selected(False)
        self.selected_item = item_frame
        self.selected_item.set_selected(True)
        self.on_select_callback(pkg_data)


class PackageListItem(ctk.CTkFrame):
    def __init__(self, master, pkg_data, click_callback, **kwargs):
        # Card-like design with border and padding
        super().__init__(
            master, 
            corner_radius=15, 
            fg_color=("gray90", "#252525"), 
            border_width=1, 
            border_color=("gray80", "#333333"),
            width=300, # Fixed width for list items to prevent jumping
            **kwargs
        )
        self.pkg_data = pkg_data
        self.click_callback = click_callback

        self.grid_columnconfigure(1, weight=1)

        name = pkg_data.get("Name", "Unknown")
        is_installed = pkg_data.get("is_installed", False)
        backend = pkg_data.get("backend", "pacman")
        icon_name = pkg_data.get("Icon", "")

        # Icon Label
        icon_img = icon_resolver.get_icon_image(icon_name, size=(40, 40))
        if not icon_img:
            # Fallback based on backend
            if backend == "pip":
                icon_img = icon_resolver.get_icon_image("python", size=(40, 40))
            else:
                icon_img = icon_resolver.get_icon_image("package-x-generic", size=(40, 40))
        
        # Ultimate fallback to placeholder to prevent "ghost" icons
        if not icon_img:
            icon_img = icon_resolver.get_placeholder_icon(size=(40, 40))
        
        self.icon_label = ctk.CTkLabel(self, text="", image=icon_img)
        self.icon_label.grid(row=0, column=0, rowspan=2, padx=(15, 5), pady=10)

        # Top row: name + backend badge
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=0, column=1, padx=(5, 15), pady=(12, 0), sticky="ew")
        top_row.grid_columnconfigure(0, weight=1)

        title_display = name
        if is_installed:
            title_display = f"✓ {name}"

        self.name_label = ctk.CTkLabel(
            top_row, 
            text=title_display, 
            font=ctk.CTkFont(size=14, weight="bold"), 
            anchor="w",
            text_color=("#333333", "white")
        )
        self.name_label.grid(row=0, column=0, sticky="w")

        # Backend badge (pill style)
        badge_color = BACKEND_COLORS.get(backend, "gray")
        badge_text = BACKEND_LABELS.get(backend, backend)
        badge = ctk.CTkLabel(
            top_row, 
            text=badge_text.upper(),
            fg_color=badge_color, 
            corner_radius=20,
            text_color="white", 
            font=ctk.CTkFont(size=9, weight="bold"),
            width=65, height=20
        )
        badge.grid(row=0, column=1, padx=(10, 0), sticky="e")

        desc = pkg_data.get("Description", "No description available.")
        if len(desc) > 85: desc = desc[:82] + "..."
        
        self.desc_label = ctk.CTkLabel(
            self, 
            text=desc, 
            text_color=("gray40", "gray60"), 
            anchor="w",
            font=ctk.CTkFont(size=12),
            wraplength=280
        )
        self.desc_label.grid(row=1, column=1, padx=(5, 15), pady=(2, 12), sticky="w")

        # Bind events for hover and click
        for w in [self, self.name_label, self.desc_label, self.icon_label, top_row]:
            w.bind("<Button-1>", self.on_click)
            w.bind("<Enter>", self.on_enter)
            w.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        self.configure(fg_color=("gray85", "#2e2e2e"), border_color=("#0099ff", "#0099ff"))

    def on_leave(self, event):
        if not getattr(self, "_selected", False):
            self.configure(fg_color=("gray90", "#252525"), border_color=("gray80", "#333333"))

    def on_click(self, event):
        self.click_callback(self, self.pkg_data)

    def set_selected(self, selected: bool):
        self._selected = selected
        if selected:
            self.configure(fg_color=("#eef7ff", "#1a2a3a"), border_color=("#0099ff", "#0099ff"), border_width=2)
        else:
            self.configure(fg_color=("gray90", "#252525"), border_color=("gray80", "#333333"), border_width=1)


class PackageDetailFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, on_install, on_remove, on_run=None, fetch_extended_info=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_install = on_install
        self.on_remove = on_remove
        self.on_run = on_run
        self.fetch_extended_info = fetch_extended_info
        self.current_pkg = None

        self.grid_columnconfigure(0, weight=1)

        # Hero Banner area
        self.hero_frame = ctk.CTkFrame(self, height=120, corner_radius=15, fg_color="#333333")
        self.hero_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        self.hero_frame.grid_propagate(False)
        self.hero_frame.grid_columnconfigure(0, weight=1)
        self.hero_frame.grid_rowconfigure(0, weight=1)

        self.hero_icon = ctk.CTkLabel(self.hero_frame, text="")
        self.hero_icon.grid(row=0, column=0, padx=(25, 0), pady=20, sticky="w")
        self.hero_icon.configure(width=64, height=64) # Force size

        self.title_label = ctk.CTkLabel(
            self.hero_frame, text="Select a package", 
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white",
            wraplength=450, justify="left", anchor="w"
        )
        self.title_label.grid(row=0, column=1, padx=(15, 25), pady=20, sticky="w")

        self.backend_badge = ctk.CTkLabel(
            self, text="", corner_radius=12, padx=12, pady=4,
            font=ctk.CTkFont(size=12, weight="bold"), text_color="white"
        )
        self.backend_badge.grid(row=1, column=0, padx=20, pady=(0, 2), sticky="w")

        self.version_label = ctk.CTkLabel(self, text="", text_color="gray", wraplength=550, justify="left", anchor="w")
        self.version_label.grid(row=2, column=0, padx=20, pady=0, sticky="w")

        self.desc_textbox = ctk.CTkTextbox(self, height=70, wrap="word")
        self.desc_textbox.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.desc_textbox.insert("1.0", "")
        self.desc_textbox.configure(state="disabled")

        self.meta_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.meta_frame.grid(row=4, column=0, padx=20, pady=5, sticky="ew")

        self.votes_label = ctk.CTkLabel(self.meta_frame, text="", font=ctk.CTkFont(size=12))
        self.votes_label.pack(side="left", padx=(0, 20))

        self.maintainer_label = ctk.CTkLabel(self.meta_frame, text="", font=ctk.CTkFont(size=12))
        self.maintainer_label.pack(side="left", padx=(0, 20))

        self.updated_label = ctk.CTkLabel(self.meta_frame, text="", font=ctk.CTkFont(size=12))
        self.updated_label.pack(side="left")

        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=5, column=0, padx=20, pady=15, sticky="ew")

        self.install_btn = ctk.CTkButton(
            self.action_frame, text="Install Package", command=self.handle_install,
            fg_color="#2eb354", hover_color="#248f43", 
            height=40, corner_radius=12, font=ctk.CTkFont(weight="bold")
        )
        self.install_btn.pack(side="left", padx=(0, 10))

        self.remove_btn = ctk.CTkButton(
            self.action_frame, text="Remove", command=self.handle_remove,
            fg_color="#e53935", hover_color="#b71c1c",
            height=40, corner_radius=12, font=ctk.CTkFont(weight="bold")
        )
        self.remove_btn.pack(side="left", padx=(0, 10))

        self.run_btn = ctk.CTkButton(
            self.action_frame, text="Launch Application", command=self.handle_run,
            fg_color="#1a73e8", hover_color="#1557b0",
            height=40, corner_radius=12, font=ctk.CTkFont(weight="bold")
        )
        self.run_btn.pack(side="left")

        # Dependency section with card-like containers
        self.rel_frame = ctk.CTkFrame(self, fg_color=("gray95", "#2a2a2a"), corner_radius=15, border_width=1, border_color=("gray85", "#333333"))
        self.rel_frame.grid(row=6, column=0, padx=20, pady=10, sticky="nsew")

        self.depends_label = ctk.CTkLabel(
            self.rel_frame, text="Dependencies:", font=ctk.CTkFont(weight="bold")
        )
        self.depends_label.pack(anchor="w")
        self.depends_text = ctk.CTkTextbox(self.rel_frame, height=65, wrap="word")
        self.depends_text.pack(fill="x", pady=(0, 10))
        self.depends_text.configure(state="disabled")

        self.required_label = ctk.CTkLabel(
            self.rel_frame, text="Required By:", font=ctk.CTkFont(weight="bold")
        )
        self.required_label.pack(anchor="w")
        self.required_text = ctk.CTkTextbox(self.rel_frame, height=65, wrap="word")
        self.required_text.pack(fill="x")
        self.required_text.configure(state="disabled")

        # Set default font for textboxes to avoid invisible text on Windows
        self.desc_textbox.configure(font=ctk.CTkFont(size=13))
        self.depends_text.configure(font=ctk.CTkFont(size=12))
        self.required_text.configure(font=ctk.CTkFont(size=12))

        self.hide_content()

    def _set_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def hide_content(self):
        self.title_label.configure(text="Select a package")
        self.hero_icon.configure(image=None)
        self.hero_frame.configure(fg_color=("#dddddd", "#2a2a2a"))
        self.backend_badge.configure(text="", fg_color="transparent")
        self.version_label.configure(text="")
        self._set_text(self.desc_textbox, "")
        self.votes_label.configure(text="")
        self.maintainer_label.configure(text="")
        self.updated_label.configure(text="")
        self.install_btn.pack_forget()
        self.remove_btn.pack_forget()
        self.run_btn.pack_forget()
        self._set_text(self.depends_text, "")
        self._set_text(self.required_text, "")
        self.rel_frame.grid_remove()

    def display_package(self, pkg):
        self.current_pkg = pkg
        backend = pkg.get("backend", "pacman")
        badge_color = BACKEND_COLORS.get(backend, "gray")
        badge_text = BACKEND_LABELS.get(backend, backend)
        icon_name = pkg.get("Icon", "")

        # Icon handling
        icon_img = icon_resolver.get_icon_image(icon_name, size=(64, 64))
        if not icon_img:
            if backend == "pip":
                icon_img = icon_resolver.get_icon_image("python", size=(64, 64))
            else:
                icon_img = icon_resolver.get_icon_image("package-x-generic", size=(64, 64))
        
        # Ultimate fallback
        if not icon_img:
            icon_img = icon_resolver.get_placeholder_icon(size=(64, 64))

        self.title_label.configure(text=pkg.get("Name", "Unknown"))
        self.hero_icon.configure(image=icon_img)
        self.hero_frame.configure(fg_color=badge_color)
        self.backend_badge.configure(text=badge_text, fg_color=badge_color)
        self.version_label.configure(text=pkg.get("Version", ""))

        self._set_text(self.desc_textbox, pkg.get("Description", ""))

        vote_label = "Downloads" if backend == "pip" else "Votes"
        num_votes = pkg.get('NumVotes')
        self.votes_label.configure(text=f"{vote_label}: {num_votes}" if num_votes is not None else "")
        self.maintainer_label.configure(text=f"Maintainer: {pkg.get('Maintainer', '')}" if pkg.get("Maintainer") else "")

        last_mod = pkg.get("LastModified")
        if last_mod:
            date_str = datetime.datetime.fromtimestamp(last_mod).strftime("%Y-%m-%d")
            self.updated_label.configure(text=f"Updated: {date_str}")
        else:
            self.updated_label.configure(text="")

        # Buttons
        if pkg.get("is_installed"):
            self.remove_btn.pack(side="left", padx=(0, 8))
            self.install_btn.pack_forget()
        else:
            self.install_btn.pack(side="left", padx=(0, 8))
            self.remove_btn.pack_forget()

        if pkg.get("is_installed") and pkg.get("is_app"):
            self.run_btn.pack(side="left")
        else:
            self.run_btn.pack_forget()

        # Deps section
        self.rel_frame.grid()
        self._set_text(self.depends_text, "Loading...")
        self._set_text(self.required_text, "Loading...")
        if self.fetch_extended_info:
            self.fetch_extended_info(pkg, self._on_extended_info)

    def _on_extended_info(self, info):
        self.after(0, self._render_extended_info, info)

    def _render_extended_info(self, info):
        depends = info.get("Depends On", info.get("Depends", "None"))
        required = info.get("Required By", "None")
        self._set_text(self.depends_text, depends or "None")
        self._set_text(self.required_text, required or "None")

        # Bind scrolling to all new content
        self._bind_scroll(self)

    def _bind_scroll(self, widget):
        def on_mouse_scroll(event):
            if event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
                self._parent_canvas.yview("scroll", -1, "units")
            elif event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
                self._parent_canvas.yview("scroll", 1, "units")

        widget.bind("<Button-4>", on_mouse_scroll, add="+")
        widget.bind("<Button-5>", on_mouse_scroll, add="+")
        widget.bind("<MouseWheel>", on_mouse_scroll, add="+")
        
        for child in widget.winfo_children():
            self._bind_scroll(child)

    def handle_install(self):
        if self.current_pkg:
            self.on_install(self.current_pkg)

    def handle_remove(self):
        if self.current_pkg:
            self.on_remove(self.current_pkg)

    def handle_run(self):
        if self.current_pkg and self.on_run:
            exec_cmd = self.current_pkg.get("Exec") or self.current_pkg.get("Name", "")
            if exec_cmd:
                self.on_run(exec_cmd)
