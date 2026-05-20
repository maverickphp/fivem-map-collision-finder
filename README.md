# FiveM Map Collision Finder

A tool for map developers and server owners to find **streaming-name conflicts** across their FiveM resources.

When two map resources ship a file with the same name (e.g. `prop_table.ydr`), FiveM's engine loads only one and silently ignores the other — causing missing textures, floating props, and broken collision. This tool finds every case of that before it becomes a problem in-game.

---

## Desktop App

A full GUI — no Python required on the machine you run it on.

![Desktop App](https://i.imgur.com/placeholder.png)

### Features

- **Multi-folder scanning** — add as many folders as you want. Scans them all and catches collisions inside each folder *and* between them. Useful for checking a new map pack against your live server before installing it.
- **Content hashing** — goes beyond filename matching. Each collision is classified:
  - 🔴 **CONFLICT – different content** — same filename, different files. This is the real, game-breaking collision. The fix is to rename the asset (and its `.ytyp` / `.ymap` references) in one of the maps — do **not** just delete it.
  - 🟠 **Identical copies** — same filename, identical content. Harmless; safe to delete the spare copy.
- **Map name in results** — each result heading shows the duplicate filename and the FiveM resources / maps it was found in.
- **Live search** — type in the search box to filter results by filename or map name instantly. Shows a `X / Y shown` counter while filtered.
- **Double-click to open** — double-click any row to open its folder in Explorer.
- **Save Report** — export the full findings to a `.log` file.

### Usage

1. Double-click `FiveM Map Collision Finder.exe`.
2. Press **Add Folder...** and pick your `resources` or `[maps]` folder. Repeat for any additional folders.
3. Optionally enter ignore patterns (e.g. `*.ydd`).
4. Press **Scan**.
5. Review results — red rows need fixing, orange are safe to clean up.

### Building the exe

On any machine with Python installed:

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

or just double-click `build.bat`.

This produces `dist\FiveM Map Collision Finder.exe` — a single self-contained file that runs on any Windows PC with nothing else installed.

To run from source without building:

```bash
python app.py
```

---

## Command Line

The original `checker.py` script — useful for terminals and CI pipelines.

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

### Example

```bash
python checker.py /resources/[maps] --ignore *.ydd --output report.log
```

If `--output` is omitted the results print to the terminal. The script exits with code `1` when collisions are found and `0` when none are, making it suitable as a pre-deploy check in CI.

---

## License

[Creative Commons Attribution-NonCommercial 4.0 International](LICENSE)
