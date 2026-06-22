# BOXROOM Game Cover Downloader for Linux

A native Linux, Tkinter-based utility designed to scrape Steam library box art capsules and screenshots. It dynamically populates assets for public Steam profiles or API keys, with dedicated structural compatibility for the **BOXROOM** custom cache directory layout (`steam_cache_v2`).

---

## Features

* **No-Key Scraper Fallback:** Pulls public game libraries using the Steam Community XML endpoint if an API Key isn't provided.
* **BOXROOM Cache Mode:** Automatically places and names assets exactly how the game expects them (`boxart.jpg`, `screen_0.jpg`, etc.) under designated AppID folder IDs.
* **Local Directory Scanner:** Scans your local `steam_cache_v2` directory for existing numeric game folders to automatically refresh or sync missing assets.
* **Dynamic Configuration Sliders:** Real-time interactive tuning for thumbnail resolution scaling, grid column count constraints, and horizontal/vertical layout pitch padding.
* **Native Scrolling Performance:** Smooth window rendering complete with scrollbar implementation and multi-platform mousewheel/trackpad event mapping support.
* **Persistent Cache Tracking:** Automatically reads and saves key credentials securely into a local `details.ini` file.

---

# Prerequisites & Installation

Ensure you have Python 3 and the necessary GUI/Image management tools installed on your Linux configuration.

## 1. System Dependencies

**For Arch Linux setups (using pacman or paru):**

### Using native pacman
    
    sudo pacman -S python python-pillow tk

### Or using paru AUR helper
    
    paru -S python python-pillow tk

**For Debian / Ubuntu / Mint systems:**

    sudo apt update && sudo apt install -y python3 python3-tk python3-pil python3-pil.imagetk

## 2. Python Package Setup (Alternative)

If you manage Python assets independently or require specific local environment scopes:

    pip install pillow --break-system-packages

---

## Quick Start

1. Clone or download this repository onto your machine:

    ```
    git clone [https://github.com/VerTiCal-HorIZoNs/BOXROOM-Game-Cover-Downloader-for-Linux.git](https://github.com/VerTiCal-HorIZoNs/BOXROOM-Game-Cover-Downloader-for-Linux.git)
    cd BOXROOM-Game-Cover-Downloader-for-Linux
    ```

2. Mark the script executable and launch it:

    ```
    chmod +x boxart_fetcher.py
    ./boxart_fetcher.py
    ```
    
3. Enter your SteamID64 configuration.
4. Select your target path directory mode (**BOXROOM Cache** or generic **Downloads Folder**) and click **Fetch Library**.

---

## Folder Layout Structures

### BOXROOM Mode (`boxroom`)
Saves images straight into your Proton prefix compatibility file target structure using raw Steam application codes:

    steam_cache_v2/
    └── 4335460/
        ├── boxart.jpg
        ├── screen_0.jpg
        ├── screen_1.jpg
        └── screen_2.jpg

### Standard Downloads Mode (`downloads`)
Organizes your desktop media library cleanly categorized by sanitized application display names:

    Downloads/
    └── Half-Life 2/
        ├── Boxart/
        │   └── library_600x900.jpg
        └── Screenshots/
            ├── screenshot_0.jpg
            └── screenshot_1.jpg

---

## License

This project is open-source and licensed under the **MIT License** — feel free to modify, distribute, or fork it as needed to enhance your custom setups.
