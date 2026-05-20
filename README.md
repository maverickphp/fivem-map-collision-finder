# FiveM Map Collision Finder

A tool designed to assist map developers and server owners with finding map collisions in their servers and projects.

It detects **streaming-name conflicts** — two map resources shipping a file with
the same name (e.g. `prop_table.ydr`). FiveM's engine loads only one of them and
silently ignores the rest, which causes missing textures, floating props and
broken collision.

The tool comes in two forms:

- **Desktop app** — a window with a folder browser, no Python required.
- **Command line** — the original `checker.py` script, for terminals and CI.

---

## Desktop App (no Python needed)

The easiest option for most users.

1. Download / build `FiveM Map Collision Finder.exe` (see *Building the app* below).
2. Double-click it on any Windows PC — nothing else to install.
3. Press **Add Folder...** and pick your `resources` (or `[maps]`) folder.
   You can add **several folders** — the app scans them all and also reports
   collisions *between* them (e.g. checking a new map against your live server).
4. Press **Scan**.

Results are grouped by filename. Each heading row shows the duplicated file,
the **maps / resources** it was found in, and its status:

| Status | Meaning |
|---|---|
| **CONFLICT – different content** (red) | Same name, *different* files — this is the real, game-breaking collision. Fix these first by renaming the asset in one map. |
| **Identical copies** (orange) | Same name and identical content — harmless; safe to delete the spare copies. |

Double-click any row to open its folder. Use **Save Report...** to export the
findings to a `.log` file.

### Building the app

On any PC that has Python installed, run one of:

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

```bat
build.bat
```

This produces `dist\FiveM Map Collision Finder.exe` — a single, self-contained
file. Copy it anywhere; the target PC does **not** need Python.

To run the app from source instead of building it:

```bash
python app.py
```

---

## Command Line

### Prerequisites

- Python 3.x

### Installation
   ```bash
   git clone https://github.com/puttydotexe/fivem-map-collision-finder.git
   ```

### Usage
   ```bash
   python checker.py <directory> [--ignore PATTERN [PATTERN ...]] [--output OUTPUT_FILE]
   ```

### Example Usage
   ```bash
   python checker.py /resources/[maps] --ignore *.ydd --output output.log
   ```
   > If an output file isn't provided, it will simply output the possible collisions in the command line.

The script exits with code `1` when collisions are found and `0` when none are,
so it can be used as a pre-deploy check in CI.

---

## License

This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International License](LICENSE).
