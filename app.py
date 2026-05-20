"""
FiveM Map Collision Finder - Desktop Application

Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)
Copyright (c) 2024 Joshua R <https://p.utty.dev/>

A graphical front-end for the map collision checker. Add one or more folders
with the system file browser, scan them, and review collisions without ever
touching a terminal. Designed to be packaged into a standalone .exe (see
build.ps1) so it runs on any computer with no Python installed.
"""

import os
import hashlib
import threading
import queue
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from checker import scan_directory

APP_TITLE = "FiveM Map Collision Finder"

# A folder containing one of these is a FiveM resource ("map").
RESOURCE_MANIFESTS = ("fxmanifest.lua", "__resource.lua")


def hash_file(path, chunk_size=1 << 20):
    """Return the SHA-1 of a file's contents, or None if it can't be read."""
    digest = hashlib.sha1()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(chunk_size), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def find_resource(path):
    """Walk up from *path* to the nearest FiveM resource folder; return its name."""
    folder = os.path.dirname(path)
    while True:
        for manifest in RESOURCE_MANIFESTS:
            if os.path.isfile(os.path.join(folder, manifest)):
                return os.path.basename(folder)
        parent = os.path.dirname(folder)
        if parent == folder:            # reached the drive root
            return None
        folder = parent


def map_name(path, root):
    """Best-effort name of the map a file belongs to.

    Prefers the nearest FiveM resource folder (one with an fxmanifest.lua);
    falls back to the top-level folder under the scanned *root*.
    """
    resource = find_resource(path)
    if resource:
        return resource
    rel = os.path.relpath(path, root)
    parts = rel.split(os.sep)
    if len(parts) > 1:
        return parts[0]
    return os.path.basename(os.path.normpath(root)) or root


def analyse(directories, ignored):
    """Scan every folder in *directories* and return sorted collision records.

    Each record is a dict::

        {"name": str, "conflict": bool,
         "paths": [{"path", "map", "hash"}]}

    ``conflict`` is True when files share a name but differ in content -- the
    case that actually breaks FiveM streaming. Identical copies are reported
    too, but flagged as harmless. Scanning multiple folders also catches
    collisions *between* them (e.g. a new map vs. your live server).
    """
    groups = defaultdict(list)
    seen = set()                        # de-dupe paths across overlapping roots

    for root in directories:
        if not os.path.isdir(root):
            continue
        for name, paths in scan_directory(root, ignored).items():
            for path in paths:
                key = os.path.normcase(os.path.abspath(path))
                if key in seen:
                    continue
                seen.add(key)
                groups[name].append({"path": path, "root": root})

    results = []
    for name, entries in groups.items():
        if len(entries) < 2:
            continue
        for entry in entries:
            entry["map"] = map_name(entry["path"], entry["root"])
            entry["hash"] = hash_file(entry["path"])
        hashes = {entry["hash"] for entry in entries}
        # Different content (or an unreadable file) = a real, breaking conflict.
        conflict = len(hashes) > 1 or None in hashes
        results.append({"name": name, "conflict": conflict, "paths": entries})

    # Real conflicts first, then identical-copy groups, each alphabetical.
    results.sort(key=lambda record: (not record["conflict"], record["name"]))
    return results


class CollisionFinderApp:
    """The tkinter application window."""

    def __init__(self, root):
        self.root = root
        self.queue = queue.Queue()
        self.results = []
        self.scanning = False

        root.title(APP_TITLE)
        root.geometry("1000x700")
        root.minsize(800, 540)

        self._init_style()
        self._build_ui()

    # --------------------------------------------------------------- style --
    def _init_style(self):
        style = ttk.Style()
        if "clam" in style.theme_names():       # consistent look everywhere
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Sub.TLabel", foreground="#666666")
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=24)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    # ------------------------------------------------------------------ UI --
    def _build_ui(self):
        # --- Header ------------------------------------------------------
        header = ttk.Frame(self.root, padding=(16, 14, 16, 4))
        header.pack(fill="x")
        ttk.Label(header, text="FiveM Map Collision Finder",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(header,
                  text="Find map files that share a name across your "
                       "resources — the cause of missing textures, "
                       "floating props and broken collision.",
                  style="Sub.TLabel", wraplength=950).pack(anchor="w")

        # --- Folders section --------------------------------------------
        folders = ttk.LabelFrame(self.root, text=" Folders to scan ",
                                 padding=10)
        folders.pack(fill="x", padx=16, pady=8)

        list_wrap = ttk.Frame(folders)
        list_wrap.pack(side="left", fill="both", expand=True)
        self.folder_list = tk.Listbox(list_wrap, height=4, activestyle="none",
                                      selectmode="extended",
                                      highlightthickness=0, borderwidth=1,
                                      relief="solid")
        fsb = ttk.Scrollbar(list_wrap, orient="vertical",
                            command=self.folder_list.yview)
        self.folder_list.configure(yscrollcommand=fsb.set)
        self.folder_list.pack(side="left", fill="both", expand=True)
        fsb.pack(side="right", fill="y")
        self.folder_list.bind("<Delete>", lambda _e: self.remove_folders())

        btns = ttk.Frame(folders)
        btns.pack(side="left", fill="y", padx=(10, 0))
        ttk.Button(btns, text="Add Folder...", command=self.add_folder
                   ).pack(fill="x", pady=2)
        ttk.Button(btns, text="Remove Selected", command=self.remove_folders
                   ).pack(fill="x", pady=2)
        ttk.Button(btns, text="Clear All", command=self.clear_folders
                   ).pack(fill="x", pady=2)

        # --- Options -----------------------------------------------------
        opts = ttk.Frame(self.root)
        opts.pack(fill="x", padx=16)
        ttk.Label(opts, text="Ignore patterns:").pack(side="left")
        self.ignore_var = tk.StringVar()
        ttk.Entry(opts, textvariable=self.ignore_var, width=32).pack(
            side="left", padx=6)
        ttk.Label(opts, text="optional — e.g.  *.ydd  *.ytd",
                  style="Sub.TLabel").pack(side="left")

        # --- Action row --------------------------------------------------
        action = ttk.Frame(self.root)
        action.pack(fill="x", padx=16, pady=10)
        self.scan_btn = ttk.Button(action, text="Scan",
                                   style="Accent.TButton",
                                   command=self.start_scan)
        self.scan_btn.pack(side="left", ipadx=12, ipady=2)
        self.progress = ttk.Progressbar(action, mode="indeterminate")
        self.progress.pack(side="left", fill="x", expand=True, padx=10)
        self.save_btn = ttk.Button(action, text="Save Report...",
                                   command=self.save_report, state="disabled")
        self.save_btn.pack(side="left")

        # --- Search bar --------------------------------------------------
        search = ttk.Frame(self.root)
        search.pack(fill="x", padx=16, pady=(0, 6))
        ttk.Label(search, text="Search results:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_search())
        ttk.Entry(search, textvariable=self.search_var, width=36).pack(
            side="left", padx=6)
        ttk.Button(search, text="✕", width=2,
                   command=lambda: self.search_var.set("")).pack(side="left")
        ttk.Label(search, text="filters by filename or map name",
                  style="Sub.TLabel").pack(side="left", padx=8)
        self.search_count = tk.StringVar()
        ttk.Label(search, textvariable=self.search_count,
                  style="Sub.TLabel").pack(side="right")

        # --- Results tree ------------------------------------------------
        results = ttk.LabelFrame(self.root, text=" Results ", padding=8)
        results.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        self.tree = ttk.Treeview(results, columns=("maps", "status"),
                                 show="tree headings")
        self.tree.heading("#0", text="Duplicate file  /  location")
        self.tree.heading("maps", text="Map / Resource")
        self.tree.heading("status", text="Status")
        self.tree.column("#0", width=480, anchor="w")
        self.tree.column("maps", width=260, anchor="w")
        self.tree.column("status", width=210, anchor="w")

        vsb = ttk.Scrollbar(results, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("conflict", foreground="#c0392b")
        self.tree.tag_configure("duplicate", foreground="#b9770e")
        self.tree.tag_configure("group", font=("Segoe UI", 9, "bold"))
        self.tree.bind("<Double-1>", self.open_location)

        # --- Legend ------------------------------------------------------
        legend = ttk.Frame(self.root)
        legend.pack(fill="x", padx=16)
        ttk.Label(legend, text="●  CONFLICT – different content",
                  foreground="#c0392b").pack(side="left", padx=(0, 18))
        ttk.Label(legend, text="●  Identical copies – harmless",
                  foreground="#b9770e").pack(side="left")
        ttk.Label(legend, text="Double-click a row to open its folder.",
                  style="Sub.TLabel").pack(side="right")

        # --- Status bar --------------------------------------------------
        self.status_var = tk.StringVar(
            value="Add one or more folders, then press Scan.")
        ttk.Label(self.root, textvariable=self.status_var, anchor="w",
                  relief="sunken", padding=(8, 4)).pack(fill="x", side="bottom")

    # -------------------------------------------------------------- folders --
    def add_folder(self):
        folder = filedialog.askdirectory(title="Select a folder to scan")
        if not folder:
            return
        folder = os.path.normpath(folder)
        if folder in self.folder_list.get(0, "end"):
            return                                   # already in the list
        self.folder_list.insert("end", folder)

    def remove_folders(self):
        for index in reversed(self.folder_list.curselection()):
            self.folder_list.delete(index)

    def clear_folders(self):
        self.folder_list.delete(0, "end")

    def open_location(self, event):
        """Double-click handler: open a result row's folder in the file browser."""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        text = self.tree.item(item, "text")
        if os.path.isabs(text) and os.path.exists(text):
            folder = os.path.dirname(text)
        elif os.path.isdir(text):
            folder = text
        else:
            return                                   # group/heading row
        try:
            if hasattr(os, "startfile"):
                os.startfile(folder)                 # Windows file browser
        except OSError:
            pass

    # -------------------------------------------------------------- scanning --
    def start_scan(self):
        if self.scanning:
            return
        directories = list(self.folder_list.get(0, "end"))
        if not directories:
            messagebox.showerror(APP_TITLE, "Add at least one folder to scan.")
            return
        missing = [d for d in directories if not os.path.isdir(d)]
        if missing:
            messagebox.showerror(
                APP_TITLE,
                "These folders no longer exist:\n\n" + "\n".join(missing))
            return

        # Accept ignore patterns separated by spaces and/or commas.
        ignored = self.ignore_var.get().replace(",", " ").split()

        self.scanning = True
        self.scan_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self.tree.delete(*self.tree.get_children())
        self.search_var.set("")          # reset search on each new scan
        self.search_count.set("")
        self.progress.start(12)
        self.status_var.set(
            f"Scanning {len(directories)} folder(s)... please wait.")

        threading.Thread(target=self._worker, args=(directories, ignored),
                         daemon=True).start()
        self.root.after(100, self._poll)

    def _worker(self, directories, ignored):
        """Runs off the UI thread so the window stays responsive."""
        try:
            self.queue.put(("done", analyse(directories, ignored)))
        except Exception as exc:                     # surfaced to the user
            self.queue.put(("error", str(exc)))

    def _poll(self):
        """Check the worker queue without blocking the UI."""
        try:
            kind, payload = self.queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll)
            return

        self.progress.stop()
        self.scanning = False
        self.scan_btn.config(state="normal")

        if kind == "error":
            self.status_var.set("Scan failed.")
            messagebox.showerror(APP_TITLE, f"Scan failed:\n{payload}")
            return

        self.results = payload
        self._populate(payload)

    # --------------------------------------------------------------- search --
    def _apply_search(self):
        """Re-filter the tree against whatever is in the search box."""
        if not self.results:
            return
        query = self.search_var.get().strip().lower()
        if not query:
            filtered = self.results
        else:
            filtered = [
                r for r in self.results
                if query in r["name"].lower()
                or any(query in e["map"].lower() for e in r["paths"])
            ]
        self.tree.delete(*self.tree.get_children())
        self._populate(filtered, update_status=False)
        total = len(self.results)
        shown = len(filtered)
        if query:
            self.search_count.set(f"{shown} / {total} shown")
        else:
            self.search_count.set("")

    # ---------------------------------------------------------------- views --
    def _populate(self, results, update_status=True):
        conflicts = sum(1 for r in results if r["conflict"])
        dupes = len(results) - conflicts

        for record in results:
            # Unique map names involved -- shown right on the heading row.
            maps = []
            for entry in record["paths"]:
                if entry["map"] not in maps:
                    maps.append(entry["map"])

            tag = "conflict" if record["conflict"] else "duplicate"
            status = ("CONFLICT – different content"
                      if record["conflict"] else "Identical copies")

            parent = self.tree.insert(
                "", "end", text=record["name"],
                values=(", ".join(maps), status),
                tags=(tag, "group"), open=True)
            for entry in record["paths"]:
                self.tree.insert(parent, "end", text=entry["path"],
                                 values=(entry["map"], ""), tags=(tag,))

        if not update_status:
            return

        if not results:
            self.status_var.set("Done. No duplicate map files found. ✔")
            return

        self.save_btn.config(state="normal")
        self.status_var.set(
            f"Done. {conflicts} real conflict(s), "
            f"{dupes} identical-copy group(s), "
            f"{len(results)} duplicated filename(s) total.")

    def save_report(self):
        if not self.results:
            return
        path = filedialog.asksaveasfilename(
            title="Save report", defaultextension=".log",
            filetypes=[("Log file", "*.log"), ("Text file", "*.txt"),
                       ("All files", "*.*")])
        if not path:
            return

        conflicts = sum(1 for r in self.results if r["conflict"])
        try:
            with open(path, "w", encoding="utf-8") as report:
                report.write("FiveM Map Collision Finder - report\n")
                report.write("=" * 44 + "\n\n")
                for record in self.results:
                    label = ("CONFLICT - different content"
                             if record["conflict"] else "Identical copies")
                    maps = sorted({e["map"] for e in record["paths"]})
                    report.write(f"Duplicate file: {record['name']}   "
                                 f"[{label}]\n")
                    report.write(f"  Maps involved: {', '.join(maps)}\n")
                    for entry in record["paths"]:
                        report.write(f"   - [{entry['map']}]  "
                                     f"{entry['path']}\n")
                    report.write("\n")
                report.write(f"Total duplicated filenames: {len(self.results)}\n")
                report.write(f"Real conflicts (different content): {conflicts}\n")
            self.status_var.set(f"Report saved to {path}")
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"Could not save report:\n{exc}")


def main():
    root = tk.Tk()
    CollisionFinderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
