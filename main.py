import tkinter as tk
from tkinter import messagebox
import json
import os
import re

ROWS = 6
COLS = 6
COL_NAMES = [chr(65 + i) for i in range(COLS)]  # A-F
DATA_FILE = os.path.join(os.path.expanduser("~"), ".minisheet_data.json")

CELL_W = 12
CELL_H = 1
HEADER_BG = "#c8d4e8"
SHEET_BAR_BG = "#d8d8d8"
SELECT_BG = "#fff8c5"
NORMAL_BG = "white"
ERROR_COLOR = "#cc0000"


class SpreadsheetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MiniSheet")
        self.root.geometry("780x480")
        self.root.minsize(600, 380)
        self.root.configure(bg="#f2f2f2")

        self.data = {}          # {sheet: {"r,c": raw_str}}
        self.sheets = []
        self.current_sheet = None
        self.selected_cell = None
        self.cells = {}         # (r,c) -> StringVar (display value)
        self.cell_widgets = {}  # (r,c) -> Entry
        self._updating = False

        self._build_ui()
        self._load_data()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        # Formula bar
        fbar = tk.Frame(self.root, bg="#f2f2f2", pady=5)
        fbar.pack(fill=tk.X, padx=10)

        self.cell_name_var = tk.StringVar(value="")
        cell_name = tk.Label(fbar, textvariable=self.cell_name_var, width=5,
                             font=("Arial", 11, "bold"), bg="#e0e6f0",
                             relief=tk.GROOVE, anchor="center")
        cell_name.pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(fbar, text="fx", bg="#f2f2f2", font=("Arial", 11, "italic"),
                 fg="#555").pack(side=tk.LEFT, padx=(0, 4))

        self.formula_var = tk.StringVar()
        self.formula_entry = tk.Entry(fbar, textvariable=self.formula_var,
                                      font=("Courier", 11), relief=tk.SOLID, bd=1)
        self.formula_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.formula_entry.bind("<Return>", self._fbar_commit)
        self.formula_entry.bind("<Escape>", self._fbar_cancel)

        # Grid
        grid_outer = tk.Frame(self.root, bg="#f2f2f2")
        grid_outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))

        # Corner
        tk.Label(grid_outer, text="", width=4, bg=HEADER_BG,
                 relief=tk.GROOVE).grid(row=0, column=0, sticky="nsew",
                                        padx=1, pady=1)

        # Column headers
        for c in range(COLS):
            tk.Label(grid_outer, text=COL_NAMES[c], bg=HEADER_BG,
                     font=("Arial", 10, "bold"), relief=tk.GROOVE,
                     width=CELL_W, pady=3).grid(row=0, column=c + 1,
                                                 sticky="nsew", padx=1, pady=1)

        # Rows
        for r in range(ROWS):
            tk.Label(grid_outer, text=str(r + 1), bg=HEADER_BG,
                     font=("Arial", 10, "bold"), relief=tk.GROOVE,
                     width=4, anchor="center").grid(row=r + 1, column=0,
                                                     sticky="nsew", padx=1, pady=1)
            for c in range(COLS):
                var = tk.StringVar()
                ent = tk.Entry(grid_outer, textvariable=var,
                               font=("Courier", 11), width=CELL_W,
                               height=CELL_H, relief=tk.SOLID, bd=1,
                               bg=NORMAL_BG, justify=tk.LEFT)
                ent.grid(row=r + 1, column=c + 1, sticky="nsew", padx=1, pady=1)

                ent.bind("<FocusIn>",  lambda e, r=r, c=c: self._cell_focus(r, c))
                ent.bind("<FocusOut>", lambda e, r=r, c=c: self._cell_blur(r, c))
                ent.bind("<Return>",   lambda e, r=r, c=c: self._cell_enter(r, c))
                ent.bind("<Tab>",      lambda e, r=r, c=c: self._cell_tab(r, c))
                ent.bind("<Shift-Tab>",lambda e, r=r, c=c: self._cell_shift_tab(r, c))
                ent.bind("<Up>",       lambda e, r=r, c=c: self._cell_arrow(r, c, -1, 0))
                ent.bind("<Down>",     lambda e, r=r, c=c: self._cell_arrow(r, c,  1, 0))
                ent.bind("<Left>",     lambda e, r=r, c=c: self._cell_arrow_lr(e, r, c, -1))
                ent.bind("<Right>",    lambda e, r=r, c=c: self._cell_arrow_lr(e, r, c,  1))

                self.cells[(r, c)] = var
                self.cell_widgets[(r, c)] = ent

        for col in range(COLS + 1):
            grid_outer.columnconfigure(col, weight=1)
        for row in range(ROWS + 1):
            grid_outer.rowconfigure(row, weight=1)

        # Sheet bar
        sbar = tk.Frame(self.root, bg=SHEET_BAR_BG, pady=4)
        sbar.pack(fill=tk.X, side=tk.BOTTOM)

        btns = tk.Frame(sbar, bg=SHEET_BAR_BG)
        btns.pack(side=tk.LEFT, padx=6)
        tk.Button(btns, text="+", command=self._add_sheet,
                  font=("Arial", 11, "bold"), bg="#4caf50", fg="white",
                  relief=tk.FLAT, padx=6).pack(side=tk.LEFT, padx=(0, 3))
        tk.Button(btns, text="−", command=self._remove_sheet,
                  font=("Arial", 11, "bold"), bg="#e53935", fg="white",
                  relief=tk.FLAT, padx=6).pack(side=tk.LEFT)

        self.tabs_frame = tk.Frame(sbar, bg=SHEET_BAR_BG)
        self.tabs_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

    # ------------------------------------------------------------------ Cell events

    def _cell_focus(self, r, c):
        self.selected_cell = (r, c)
        raw = self.data.get(self.current_sheet, {}).get(f"{r},{c}", "")
        self._updating = True
        self.cells[(r, c)].set(raw)
        self._updating = False
        self.formula_var.set(raw)
        self.cell_name_var.set(f"{COL_NAMES[c]}{r + 1}")
        self.cell_widgets[(r, c)].configure(bg=SELECT_BG)

    def _cell_blur(self, r, c):
        self.cell_widgets[(r, c)].configure(bg=NORMAL_BG)
        self._commit(r, c, self.cells[(r, c)].get())

    def _cell_enter(self, r, c):
        self._commit(r, c, self.cells[(r, c)].get())
        self._focus_cell((r + 1) % ROWS, c)
        return "break"

    def _cell_tab(self, r, c):
        self._commit(r, c, self.cells[(r, c)].get())
        self._focus_cell(r, (c + 1) % COLS)
        return "break"

    def _cell_shift_tab(self, r, c):
        self._commit(r, c, self.cells[(r, c)].get())
        self._focus_cell(r, (c - 1) % COLS)
        return "break"

    def _cell_arrow(self, r, c, dr, dc):
        self._commit(r, c, self.cells[(r, c)].get())
        nr = max(0, min(ROWS - 1, r + dr))
        nc = max(0, min(COLS - 1, c + dc))
        self._focus_cell(nr, nc)
        return "break"

    def _cell_arrow_lr(self, event, r, c, dc):
        # Only navigate if cursor is at boundary
        ent = self.cell_widgets[(r, c)]
        pos = ent.index(tk.INSERT)
        length = len(ent.get())
        if (dc == -1 and pos == 0) or (dc == 1 and pos == length):
            self._commit(r, c, self.cells[(r, c)].get())
            nc = max(0, min(COLS - 1, c + dc))
            self._focus_cell(r, nc)
            return "break"

    def _focus_cell(self, r, c):
        self.cell_widgets[(r, c)].focus_set()
        self.cell_widgets[(r, c)].icursor(tk.END)

    def _fbar_commit(self, _=None):
        if self.selected_cell:
            r, c = self.selected_cell
            val = self.formula_var.get()
            self._updating = True
            self.cells[(r, c)].set(val)
            self._updating = False
            self._commit(r, c, val)
            self._focus_cell(r, c)

    def _fbar_cancel(self, _=None):
        if self.selected_cell:
            r, c = self.selected_cell
            self._focus_cell(r, c)

    # ------------------------------------------------------------------ Data

    def _commit(self, r, c, val):
        sheet = self.current_sheet
        if sheet is None:
            return
        key = f"{r},{c}"
        if val:
            self.data[sheet][key] = val
        else:
            self.data[sheet].pop(key, None)
        self._refresh_display()

    def _refresh_display(self):
        for r in range(ROWS):
            for c in range(COLS):
                if self.selected_cell == (r, c):
                    continue  # leave raw value visible while editing
                raw = self.data.get(self.current_sheet, {}).get(f"{r},{c}", "")
                display = self._evaluate(raw) if raw.startswith("=") else raw
                self.cells[(r, c)].set(str(display) if display != "" else "")

                # Color errors red
                fg = ERROR_COLOR if str(display).startswith("#") else "black"
                self.cell_widgets[(r, c)].configure(fg=fg)

    # ------------------------------------------------------------------ Formula engine

    def _ref_to_rc(self, ref):
        m = re.fullmatch(r"([A-Fa-f])([1-6])", ref.strip())
        if m:
            return int(m.group(2)) - 1, ord(m.group(1).upper()) - 65
        return None

    def _cell_num(self, ref):
        rc = self._ref_to_rc(ref)
        if rc is None:
            return 0
        raw = self.data.get(self.current_sheet, {}).get(f"{rc[0]},{rc[1]}", "")
        if raw.startswith("="):
            v = self._evaluate(raw)
        else:
            v = raw
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0

    def _range_nums(self, rng):
        m = re.fullmatch(r"([A-Fa-f][1-6]):([A-Fa-f][1-6])", rng.strip())
        if not m:
            return []
        s = self._ref_to_rc(m.group(1))
        e = self._ref_to_rc(m.group(2))
        if not s or not e:
            return []
        vals = []
        for r in range(min(s[0], e[0]), max(s[0], e[0]) + 1):
            for c in range(min(s[1], e[1]), max(s[1], e[1]) + 1):
                raw = self.data.get(self.current_sheet, {}).get(f"{r},{c}", "")
                try:
                    vals.append(float(self._evaluate(raw) if raw.startswith("=") else raw))
                except (ValueError, TypeError):
                    pass
        return vals

    def _parse_args(self, args_str):
        """Return list of numeric values from comma-sep args or a range."""
        args_str = args_str.strip()
        if re.search(r"[A-Fa-f][1-6]:[A-Fa-f][1-6]", args_str):
            return self._range_nums(args_str)
        parts = [p.strip() for p in args_str.split(",")]
        vals = []
        for p in parts:
            if re.fullmatch(r"[A-Fa-f][1-6]", p):
                vals.append(self._cell_num(p))
            else:
                try:
                    vals.append(float(p))
                except ValueError:
                    pass
        return vals

    def _evaluate(self, raw):
        if not raw.startswith("="):
            return raw
        expr = raw[1:].strip()
        try:
            return self._eval_expr(expr)
        except Exception:
            return "#ERR"

    def _eval_expr(self, expr):
        expr = expr.strip()

        # SUM
        m = re.fullmatch(r"SUM\((.+)\)", expr, re.IGNORECASE)
        if m:
            vals = self._parse_args(m.group(1))
            result = sum(vals)
            return int(result) if result == int(result) else round(result, 10)

        # AVG / AVERAGE
        m = re.fullmatch(r"(?:AVG|AVERAGE)\((.+)\)", expr, re.IGNORECASE)
        if m:
            vals = self._parse_args(m.group(1))
            if not vals:
                return "#DIV/0"
            result = sum(vals) / len(vals)
            return int(result) if result == int(result) else round(result, 10)

        # MIN
        m = re.fullmatch(r"MIN\((.+)\)", expr, re.IGNORECASE)
        if m:
            vals = self._parse_args(m.group(1))
            return min(vals) if vals else "#ERR"

        # MAX
        m = re.fullmatch(r"MAX\((.+)\)", expr, re.IGNORECASE)
        if m:
            vals = self._parse_args(m.group(1))
            return max(vals) if vals else "#ERR"

        # COUNT
        m = re.fullmatch(r"COUNT\((.+)\)", expr, re.IGNORECASE)
        if m:
            vals = self._parse_args(m.group(1))
            return len(vals)

        # Replace cell refs with numeric values for arithmetic
        def sub_ref(match):
            return str(self._cell_num(match.group(0)))

        expr_sub = re.sub(r"[A-Fa-f][1-6]", sub_ref, expr)

        # Allow only safe arithmetic characters
        if not re.fullmatch(r"[\d\s\+\-\*\/\(\)\.]+", expr_sub):
            return "#ERR"

        result = eval(expr_sub, {"__builtins__": {}})  # noqa: S307
        if isinstance(result, float) and result == int(result):
            return int(result)
        return round(result, 10)

    # ------------------------------------------------------------------ Sheets

    def _add_sheet(self):
        n = 1
        while f"Sheet{n}" in self.sheets:
            n += 1
        name = f"Sheet{n}"
        self.sheets.append(name)
        self.data[name] = {}
        self._refresh_tabs()
        self._switch_sheet(name)

    def _remove_sheet(self):
        if len(self.sheets) <= 1:
            messagebox.showwarning("MiniSheet", "At least one sheet must remain.")
            return
        old = self.current_sheet
        idx = self.sheets.index(old)
        self.sheets.remove(old)
        del self.data[old]
        new_idx = min(idx, len(self.sheets) - 1)
        self._refresh_tabs()
        self._switch_sheet(self.sheets[new_idx])

    def _refresh_tabs(self):
        for w in self.tabs_frame.winfo_children():
            w.destroy()
        for name in self.sheets:
            active = name == self.current_sheet
            btn = tk.Button(
                self.tabs_frame, text=name,
                command=lambda n=name: self._switch_sheet(n),
                font=("Arial", 10),
                bg="white" if active else "#b0bac8",
                relief=tk.SOLID if active else tk.FLAT,
                padx=10, pady=2, bd=1
            )
            btn.pack(side=tk.LEFT, padx=(0, 2))

    def _switch_sheet(self, name):
        self.selected_cell = None
        self.formula_var.set("")
        self.cell_name_var.set("")
        self.current_sheet = name
        self._refresh_tabs()
        self._refresh_display()

    # ------------------------------------------------------------------ Persistence

    def _load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self.data = saved.get("data", {})
                self.sheets = saved.get("sheets", list(self.data.keys()))
                if not self.sheets:
                    raise ValueError
                current = saved.get("current_sheet", self.sheets[0])
                if current not in self.sheets:
                    current = self.sheets[0]
                self.current_sheet = current
            except Exception:
                self._reset_data()
        else:
            self._reset_data()
        self._refresh_tabs()
        self._refresh_display()

    def _reset_data(self):
        self.sheets = ["Sheet1"]
        self.data = {"Sheet1": {}}
        self.current_sheet = "Sheet1"

    def _save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "sheets": self.sheets,
                "data": self.data,
                "current_sheet": self.current_sheet,
            }, f, indent=2)

    def _on_close(self):
        self._save_data()
        self.root.destroy()


def main():
    root = tk.Tk()
    SpreadsheetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
