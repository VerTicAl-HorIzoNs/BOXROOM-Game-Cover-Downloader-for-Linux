# BOXROOM Game Cover Downloader for Linux

A native Linux, Tkinter-based utility designed to scrape Steam library box art capsules and screenshots. It dynamically populates assets for public Steam profiles or API keys, with dedicated structural compatibility for the **BOXROOM** custom cache directory layout (`steam_cache_v2`).

## Features

- **No-Key Scraper Fallback**: Pulls public game libraries using the Steam Community XML endpoint if an API Key isn't provided.
- **BOXROOM Cache Mode**: Automatically places and names assets exactly how the game expects them (`boxart.jpg`, `screen_0.jpg`, etc.) under designated AppID folder IDs.
- **Local Directory Scanner**: Scans your local `steam_cache_v2` directory for existing numeric game folders to automatically refresh or sync missing assets.
- **Dynamic Configuration Sliders**: Real-time interactive tuning for thumbnail resolution scaling, grid column count constraints, and horizontal/vertical layout pitch padding.
- **Native Scrolling Performance**: Smooth window rendering complete with scrollbar implementation and multi-platform mousewheel/trackpad event mapping support.
- **Persistent Cache Tracking**: Automatically reads and saves key credentials securely into a local `details.ini` file.

## Prerequisites & Installation

Ensure you have Python 3 and the necessary GUI/Image management tools installed on your Linux configuration.

### 1. System Dependencies

For Arch Linux setups utilizing `paru` or `pacman`:
```bash
paru -S python python-pillow tk
