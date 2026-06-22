#!/usr/bin/env python3
"""
BoxArt Fetcher - Upgraded for BOXROOM Cache Layout, Persistence, Custom Spacing,
Public Profile XML Fallback, and Local Folder AppID Scanning/Merging.
"""

import json
import os
import re
import threading
import queue
import urllib.request
import urllib.error
import configparser
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk

try:
    from PIL import Image, ImageTk
except ImportError:
    raise SystemExit(
        "This script needs Pillow for image thumbnails.\n"
        "Install it with:\n  pip install pillow --break-system-packages"
    )

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INI_PATH = os.path.join(SCRIPT_DIR, "details.ini")
TMP_DIR = os.path.join(SCRIPT_DIR, "TMP")
DEFAULT_DOWNLOADS_DIR = os.path.join(SCRIPT_DIR, "Downloads")
BOXROOM_CACHE_DIR = "/home/vertical/.steam/steam/steamapps/compatdata/4335460/pfx/drive_c/users/steamuser/AppData/LocalLow/NestedLoop/BOXROOM/steam_cache_v2"

INVALID_CHARS = r'[<>:"/\\|?*]'

def sanitize(name):
    cleaned = re.sub(INVALID_CHARS, "", name).strip()
    return cleaned or "Unknown"

def fetch_data(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()

def download(url, path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(path, "wb") as f:
                f.write(resp.read())
        return True
    except Exception:
        return False

class GameTile(tk.Frame):
    def __init__(self, parent, width, height):
        super().__init__(parent, bg="#1b1b1b")
        self.w = width
        self.h = height

        # Enforce pixel dimensions using the outer frame, preventing text character unit scaling
        self.img_container = tk.Frame(self, width=self.w, height=self.h, bg="#2a2a2a")
        self.img_container.pack_propagate(False)
        self.img_container.pack()

        self.img_label = tk.Label(self.img_container, bg="#2a2a2a", text="...", fg="#888", font=("Sans", 8))
        self.img_label.pack(fill="both", expand=True)

        self.name_label = tk.Label(self, text="", bg="#1b1b1b", fg="#ddd",
                                    font=("Sans", 8), justify="center")
        self.name_label.pack(pady=(2, 0))
        self._photo = None
        self._current_path = None
        self.update_dimensions(self.w, self.h)

    def update_dimensions(self, width, height):
        self.w = width
        self.h = height

        # Dynamically resize the layout containers using exact pixel boundaries
        self.config(width=self.w, height=self.h + 30)
        self.img_container.config(width=self.w, height=self.h)
        self.name_label.config(wraplength=self.w)

        if self._photo and self._current_path:
            self.set_image(self._current_path)

    def set_name(self, name):
        self.name_label.config(text=name)

    def set_status(self, text):
        self.img_label.config(text=text, image="")

    def set_image(self, path):
        try:
            self._current_path = path
            img = Image.open(path).convert("RGB")
            img = img.resize((self.w, self.h))
            self._photo = ImageTk.PhotoImage(img)
            self.img_label.config(image=self._photo, text="")
        except Exception:
            self.set_status("no art")

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("BoxArt Fetcher Pro")
        self.root.geometry("1000x750")
        self.root.configure(bg="#161616")

        self.q = queue.Queue()
        self.tiles = {}

        # Default layout scale setups
        self.thumb_w = tk.IntVar(value=116)
        self.thumb_h = tk.IntVar(value=174)
        self.cols = tk.IntVar(value=6)
        self.pad_x = tk.IntVar(value=6)
        self.pad_y = tk.IntVar(value=6)
        self.dest_mode = tk.StringVar(value="boxroom")

        # Config Parsing
        self.config = configparser.ConfigParser()
        self.load_ini()

        # Top Control Panel
        top = tk.Frame(root, bg="#161616")
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="API Key:", bg="#161616", fg="#ddd").grid(row=0, column=0, sticky="w")
        self.api_entry = tk.Entry(top, width=35, show="*")
        self.api_entry.grid(row=0, column=1, padx=5)
        if self.config.has_option("Steam", "api_key"):
            self.api_entry.insert(0, self.config.get("Steam", "api_key"))

        tk.Label(top, text="SteamID64:", bg="#161616", fg="#ddd").grid(row=0, column=2, sticky="w")
        self.id_entry = tk.Entry(top, width=20)
        self.id_entry.grid(row=0, column=3, padx=5)
        if self.config.has_option("Steam", "steamid"):
            self.id_entry.insert(0, self.config.get("Steam", "steamid"))

        # Destination Toggle
        tk.Label(top, text="Target Location:", bg="#161616", fg="#ddd").grid(row=0, column=4, sticky="w", padx=(10, 2))
        rb_br = tk.Radiobutton(top, text="BOXROOM Cache", variable=self.dest_mode, value="boxroom", bg="#161616", fg="#ddd", selectcolor="#222")
        rb_dl = tk.Radiobutton(top, text="Downloads Folder", variable=self.dest_mode, value="downloads", bg="#161616", fg="#ddd", selectcolor="#222")
        rb_br.grid(row=0, column=5, sticky="w")
        rb_dl.grid(row=0, column=6, sticky="w", padx=(0, 10))

        self.fetch_btn = tk.Button(top, text="Fetch Library", command=self.confirm_and_start, bg="#2a2a2a", fg="#fff")
        self.fetch_btn.grid(row=0, column=7, padx=5)

        # Layout Adjustment Sliders
        sliders_frame = tk.Frame(root, bg="#1b1b1b", bd=1, relief="sunken")
        sliders_frame.pack(fill="x", padx=10, pady=4)

        # Width
        tk.Label(sliders_frame, text="Width:", bg="#1b1b1b", fg="#bbb").grid(row=0, column=0, padx=5)
        tk.Scale(sliders_frame, from_=50, to=300, orient="horizontal", variable=self.thumb_w, command=self.update_layout, bg="#1b1b1b", fg="#bbb", highlightthickness=0).grid(row=0, column=1, padx=5)
        # Height
        tk.Label(sliders_frame, text="Height:", bg="#1b1b1b", fg="#bbb").grid(row=0, column=2, padx=5)
        tk.Scale(sliders_frame, from_=50, to=450, orient="horizontal", variable=self.thumb_h, command=self.update_layout, bg="#1b1b1b", fg="#bbb", highlightthickness=0).grid(row=0, column=3, padx=5)
        # Columns
        tk.Label(sliders_frame, text="Columns:", bg="#1b1b1b", fg="#bbb").grid(row=0, column=4, padx=5)
        tk.Scale(sliders_frame, from_=2, to=15, orient="horizontal", variable=self.cols, command=self.update_layout, bg="#1b1b1b", fg="#bbb", highlightthickness=0).grid(row=0, column=5, padx=5)
        # Pitch Horizontal
        tk.Label(sliders_frame, text="Pad X:", bg="#1b1b1b", fg="#bbb").grid(row=0, column=6, padx=5)
        tk.Scale(sliders_frame, from_=0, to=40, orient="horizontal", variable=self.pad_x, command=self.update_layout, bg="#1b1b1b", fg="#bbb", highlightthickness=0).grid(row=0, column=7, padx=5)
        # Pitch Vertical
        tk.Label(sliders_frame, text="Pad Y:", bg="#1b1b1b", fg="#bbb").grid(row=0, column=8, padx=5)
        tk.Scale(sliders_frame, from_=0, to=40, orient="horizontal", variable=self.pad_y, command=self.update_layout, bg="#1b1b1b", fg="#bbb", highlightthickness=0).grid(row=0, column=9, padx=5)

        # Grid view canvas viewport
        grid_outer = tk.Frame(root, bg="#161616")
        grid_outer.pack(fill="both", expand=True, padx=10, pady=(5, 5))

        self.canvas = tk.Canvas(grid_outer, bg="#161616", highlightthickness=0)
        vsb = tk.Scrollbar(grid_outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = tk.Frame(self.canvas, bg="#161616")
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Mouse Wheel bindings
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Log Output terminal
        self.log_widget = scrolledtext.ScrolledText(root, height=6, bg="#0d0d0d", fg="#9f9", insertbackground="#9f9")
        self.log_widget.pack(fill="x", padx=10, pady=(0, 10))

        self.root.after(150, self.poll_queue)

    def load_ini(self):
        if os.path.exists(INI_PATH):
            self.config.read(INI_PATH)

    def save_ini(self, api_key, steamid):
        if not self.config.has_section("Steam"):
            self.config.add_section("Steam")
        self.config.set("Steam", "api_key", api_key)
        self.config.set("Steam", "steamid", steamid)
        with open(INI_PATH, "w") as f:
            self.config.write(f)

    def log(self, msg):
        self.log_widget.insert(tk.END, msg + "\n")
        self.log_widget.see(tk.END)

    def update_layout(self, *args):
        w = self.thumb_w.get()
        h = self.thumb_h.get()
        c = self.cols.get()
        px = self.pad_x.get()
        py = self.pad_y.get()

        for idx, (appid, tile) in enumerate(self.tiles.items()):
            tile.grid_forget()
            tile.update_dimensions(w, h)
            tile.grid(row=idx // c, column=idx % c, padx=px, pady=py)

    def add_tile(self, appid, name):
        idx = len(self.tiles)
        w = self.thumb_w.get()
        h = self.thumb_h.get()
        c = self.cols.get()
        px = self.pad_x.get()
        py = self.pad_y.get()

        tile = GameTile(self.grid_frame, w, h)
        tile.grid(row=idx // c, column=idx % c, padx=px, pady=py)
        tile.set_name(name)
        tile.set_status("queued")
        self.tiles[appid] = tile

    def confirm_and_start(self):
        api_key = self.api_entry.get().strip()
        steamid = self.id_entry.get().strip()
        mode = self.dest_mode.get()
        target_path = BOXROOM_CACHE_DIR if mode == "boxroom" else DEFAULT_DOWNLOADS_DIR

        local_appids = []
        # Scan steam_cache_v2 folder if option selected and valid path path exists
        if mode == "boxroom" and os.path.exists(BOXROOM_CACHE_DIR):
            try:
                for entry in os.scandir(BOXROOM_CACHE_DIR):
                    if entry.is_dir() and entry.name.isdigit():
                        local_appids.append(int(entry.name))
            except Exception as e:
                self.log(f"Error scanning cache path directory: {e}")

        if not steamid and not local_appids:
            self.log("Provide a SteamID64 or populate a valid BOXROOM cache path to trace.")
            return

        include_local = False
        if local_appids:
            include_local = messagebox.askyesno("Local Cache Found",
                f"Discovered {len(local_appids)} existing AppID folders inside your BOXROOM cache.\n"
                "Would you like the script to include and pull/refresh assets for these folders as well?")

        confirm = messagebox.askyesno("Confirm Download Process",
            f"Are you sure you want to begin scraping files to:\n{target_path}?")
        if not confirm:
            return

        if api_key and steamid:
            self.save_ini(api_key, steamid)

        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.tiles.clear()
        self.log_widget.delete("1.0", tk.END)
        self.fetch_btn.config(state=tk.DISABLED)

        os.makedirs(TMP_DIR, exist_ok=True)
        os.makedirs(target_path, exist_ok=True)

        threading.Thread(target=self.worker, args=(api_key, steamid, mode, target_path, local_appids if include_local else []), daemon=True).start()

    def worker(self, api_key, steamid, mode, target_dir, local_appids):
        games_dict = {}

        # 1. Add any local appids verified from scanning
        if local_appids:
            for appid in local_appids:
                games_dict[appid] = f"Local AppID {appid}"

        # 2. Add profiles from online configuration tracking
        if steamid:
            if api_key:
                self.q.put(("log", "Using API Key to fetch owned games list..."))
                lib_url = (
                    "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
                    f"?key={api_key}&steamid={steamid}&include_appinfo=true&format=json"
                )
                try:
                    raw = fetch_data(lib_url)
                    data = json.loads(raw.decode())
                    games_list = data.get("response", {}).get("games", [])
                    for g in games_list:
                        games_dict[g["appid"]] = g.get("name", str(g["appid"]))
                except Exception as e:
                    self.q.put(("log", f"API Request Failed: {e}"))
            else:
                self.q.put(("log", "No API Key provided. Trying public profile community XML scrape parsing..."))
                xml_url = f"https://steamcommunity.com/profiles/{steamid}/games/?xml=1"
                try:
                    raw_xml = fetch_data(xml_url)
                    root_xml = ET.fromstring(raw_xml)

                    error_node = root_xml.find("error")
                    if error_node is not None:
                        self.q.put(("log", f"Steam Error: {error_node.text}"))

                    for game_node in root_xml.findall(".//game"):
                        appid_node = game_node.find("appID")
                        name_node = game_node.find("name")
                        if appid_node is not None and name_node is not None:
                            games_dict[int(appid_node.text)] = name_node.text
                except Exception as e:
                    self.q.put(("log", f"XML Public Scrape Failed: {e}"))

        if not games_dict:
            self.q.put(("log", "Zero games discovered. Verify target paths or visibility restrictions."))
            self.q.put(("done", None))
            return

        self.q.put(("log", f"Target map contains {len(games_dict)} items ready for execution."))

        for appid, name in games_dict.items():
            self.q.put(("new", (appid, name)))

        for appid, name in games_dict.items():
            if mode == "boxroom":
                game_dir = os.path.join(target_dir, str(appid))
                os.makedirs(game_dir, exist_ok=True)
                boxart_path = os.path.join(game_dir, "boxart.jpg")
            else:
                folder = sanitize(name)
                boxart_dir = os.path.join(target_dir, folder, "Boxart")
                os.makedirs(boxart_dir, exist_ok=True)
                boxart_path = os.path.join(boxart_dir, "library_600x900.jpg")

            # Perform asset resolution
            ok_library = download(f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg", boxart_path)
            if not ok_library:
                ok_library = download(f"https://cdn.steamstatic.com/steam/apps/{appid}/library_600x900.jpg", boxart_path)

            if not ok_library:
                fallback_path = os.path.join(game_dir if mode == "boxroom" else boxart_dir, "header.jpg" if mode != "boxroom" else "boxart.jpg")
                ok_library = download(f"https://cdn.steamstatic.com/steam/apps/{appid}/header.jpg", fallback_path)

            thumb_source = boxart_path if ok_library else None
            shots_saved = 0

            try:
                details = json.loads(fetch_data(f"https://store.steampowered.com/api/appdetails?appids={appid}").decode())
                entry = details.get(str(appid), {})
                if entry.get("success"):
                    # Resolve authentic name for scanned targets if missing
                    if name.startswith("Local AppID"):
                        real_name = entry["data"].get("name")
                        if real_name:
                            name = real_name

                    shots = entry["data"].get("screenshots", [])[:3 if mode == "boxroom" else 5]
                    for j, shot in enumerate(shots):
                        shot_url = shot.get("path_full")
                        if mode == "boxroom":
                            screen_file = os.path.join(game_dir, f"screen_{j}.jpg")
                        else:
                            shots_dir = os.path.join(target_dir, sanitize(name), "Screenshots")
                            os.makedirs(shots_dir, exist_ok=True)
                            screen_file = os.path.join(shots_dir, f"screenshot_{j}.jpg")

                        if shot_url and download(shot_url, screen_file):
                            shots_saved += 1
            except Exception:
                pass

            status = "ok" if thumb_source else "missing"
            self.q.put(("update", (appid, thumb_source, status)))
            self.q.put(("log", f"{name} ({appid}) - {status}, stored {shots_saved} screenshots"))

        self.q.put(("log", "Execution lifecycle completed successfully."))
        self.q.put(("done", None))

    def poll_queue(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "log":
                    self.log(payload)
                elif kind == "new":
                    appid, name = payload
                    self.add_tile(appid, name)
                elif kind == "update":
                    appid, thumb_source, status = payload
                    tile = self.tiles.get(appid)
                    if tile:
                        if thumb_source:
                            tile.set_image(thumb_source)
                        else:
                            tile.set_status("no art")
                elif kind == "done":
                    self.fetch_btn.config(state=tk.NORMAL)
        except queue.Empty:
            pass
        self.root.after(150, self.poll_queue)

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
