# Tools Overview

## Infantry Asset Generator

`tools/generate_infantry_assets.py` clones an existing country's infantry `.gfx`/`.asset` pair and retargets them to a new tag. It now ships with a prebuilt executable so non-technical contributors can run it without setting up Python.

### Zero-Setup Interactive EXE
1. Keep `dist/generate_infantry_assets.exe` inside the mod root (the tool now auto-detects the parent folder that contains `gfx/`, even when launched from inside `dist/`).
2. Double-click the EXE or run it from PowerShell/Command Prompt with no arguments.
3. Fill in the prompts:
   - New 3-letter country tag (required).
   - Template tag (defaults to `BLR`).
   - Mod root path (defaults to the folder you launched from).
   - Mesh prefix (`MI_<NEW>` by default; enter `MI_BLR` to keep Belarus meshes).
   - Optional literal replacements, then choose whether to dry-run or overwrite existing files.
4. The tool creates/updates `gfx/entities/zzz_<TAG>_infantry.gfx` and `.asset`. When dry-run is enabled it only prints what would change.

### Command-Line Usage
```
# Python version
python tools/generate_infantry_assets.py LIT --template-tag BLR --mesh-prefix MI_BLR

# Standalone EXE version
./dist/generate_infantry_assets.exe LIT --template-tag BLR --mesh-prefix MI_BLR --dry-run
```
All CLI flags from the Python script work identically in the EXE (`--mod-root`, `--extra-replace`, `--dry-run`, `--force`).

### Rebuilding the EXE
1. Install PyInstaller once: `python -m pip install --user pyinstaller`.
2. From the mod root run:
```
python -m PyInstaller --onefile --name generate_infantry_assets tools/generate_infantry_assets.py
```
3. The executable lives in `dist/generate_infantry_assets.exe`. Share that file with teammates who do not have Python installed.
4. If you want to keep the `dist/` folder clean, delete `build/` and `generate_infantry_assets.spec` after packaging; they can be regenerated anytime.
