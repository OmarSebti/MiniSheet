# MiniSheet

A lightweight cross-platform spreadsheet app (Mac & Windows) built with Python and tkinter.

## Features

- **6 × 6 editable grid** with column (A–F) and row (1–6) headers
- **Formula support** — start any cell with `=`:
  - Arithmetic: `=A1+B2`, `=A1-B1`, `=C3*D3`, `=A1/B1`
  - `SUM(A1:F6)` or `SUM(A1,B2,C3)`
  - `AVG(A1:F6)` / `AVERAGE(A1:F6)`
  - `MIN(A1:F6)`, `MAX(A1:F6)`, `COUNT(A1:F6)`
- **Multiple sheets** — add or remove sheets with the `+` / `−` buttons (minimum 1 sheet)
- **Auto-save** — content is saved on close and restored on next launch

## Requirements

- Python 3.8 or later  
- `tkinter` (bundled with the standard Python installer on Windows and macOS)

## Running

```bash
python main.py
```

On Windows you can also double-click `main.py` if Python is associated with `.py` files,
or run `pythonw main.py` to suppress the console window.

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| Enter | Confirm and move down |
| Tab | Confirm and move right |
| Shift+Tab | Confirm and move left |
| Arrow keys | Navigate (at cell boundary) |
| Escape | Cancel formula-bar edit |

## Data storage

Data is saved to `~/.minisheet_data.json` (your home directory on both platforms).
