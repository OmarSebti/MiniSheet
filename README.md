# MiniSheet

A lightweight cross-platform spreadsheet app (Mac & Windows) built with Electron + vanilla JS.

## Features

- **6 × 6 editable grid** with column (A–F) and row (1–6) headers
- **Formula support** — start any cell with `=`:
  - Arithmetic: `=A1+B2`, `=A1-B1`, `=C3*D3`, `=A1/B1`
  - `SUM(A1:F6)` or `SUM(A1,B2,C3)`
  - `AVG(A1:F6)` / `AVERAGE(A1:F6)`
  - `MIN(A1:F6)`, `MAX(A1:F6)`, `COUNT(A1:F6)`
- **Multiple sheets** — add / remove with `+` / `−` (minimum 1 sheet)
- **Auto-save** — every change is persisted; reopening restores exact state

## Requirements

- [Node.js](https://nodejs.org/) 18+
- Electron (installed via npm)

## Setup & run

```bash
npm install
npm start
```

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| Enter | Confirm and move down |
| Tab | Confirm and move right |
| Shift+Tab | Confirm and move left |
| Arrow keys | Navigate (at cell boundary) |
| Escape | Discard edit |

## Data storage

Saved automatically to Electron's `userData` directory:
- **macOS**: `~/Library/Application Support/minisheet/minisheet_data.json`
- **Windows**: `%APPDATA%\minisheet\minisheet_data.json`
