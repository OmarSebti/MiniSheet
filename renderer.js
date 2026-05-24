'use strict';

const ROWS = 6;
const COLS = 6;
const COLS_ALPHA = ['A', 'B', 'C', 'D', 'E', 'F'];

// ── State ─────────────────────────────────────────────────────────────────────
const state = {
  sheets: ['Sheet1'],
  data: { Sheet1: {} },    // { sheetName: { 'r,c': rawString } }
  current: 'Sheet1',
  sel: null,               // { r, c } or null
};

// ── DOM refs (populated by buildGrid) ────────────────────────────────────────
const inputs = Array.from({ length: ROWS }, () => Array(COLS).fill(null));
const cellWraps = Array.from({ length: ROWS }, () => Array(COLS).fill(null));

const elCellRef    = document.getElementById('cell-ref');
const elFormulaBar = document.getElementById('formula-input');
const elTabs       = document.getElementById('tabs');

// ── Build grid ────────────────────────────────────────────────────────────────
(function buildGrid() {
  const table = document.getElementById('grid');

  // Header row
  const thead = table.createTHead();
  const hr = thead.insertRow();
  const corner = hr.insertCell();
  corner.className = 'th-corner';

  for (let c = 0; c < COLS; c++) {
    const th = document.createElement('th');
    th.className = 'th-col';
    th.textContent = COLS_ALPHA[c];
    hr.appendChild(th);
  }

  // Data rows
  const tbody = table.createTBody();
  for (let r = 0; r < ROWS; r++) {
    const tr = tbody.insertRow();

    const rowHeader = tr.insertCell();
    rowHeader.className = 'th-row';
    rowHeader.textContent = r + 1;

    for (let c = 0; c < COLS; c++) {
      const td = tr.insertCell();
      td.className = 'cell-wrap';

      const inp = document.createElement('input');
      inp.type = 'text';
      inp.autocomplete = 'off';
      inp.spellcheck = false;
      td.appendChild(inp);

      inputs[r][c]    = inp;
      cellWraps[r][c] = td;

      inp.addEventListener('focus',   () => onFocus(r, c));
      inp.addEventListener('blur',    () => onBlur(r, c));
      inp.addEventListener('keydown', (e) => onKeyDown(e, r, c));
    }
  }
})();

// ── Cell events ───────────────────────────────────────────────────────────────
function onFocus(r, c) {
  if (state.sel) {
    const { r: pr, c: pc } = state.sel;
    cellWraps[pr][pc].classList.remove('selected');
  }
  state.sel = { r, c };
  cellWraps[r][c].classList.add('selected');

  elCellRef.textContent = `${COLS_ALPHA[c]}${r + 1}`;

  const raw = getRaw(r, c);
  inputs[r][c].value = raw;
  elFormulaBar.value  = raw;
}

function onBlur(r, c) {
  const val = inputs[r][c].value.trim();
  commitCell(r, c, val);
  inputs[r][c].value = display(r, c);
}

function onKeyDown(e, r, c) {
  switch (e.key) {
    case 'Enter':
      e.preventDefault();
      commitCell(r, c, inputs[r][c].value.trim());
      focusCell(Math.min(r + 1, ROWS - 1), c);
      break;
    case 'Tab':
      e.preventDefault();
      commitCell(r, c, inputs[r][c].value.trim());
      if (e.shiftKey) focusCell(r, Math.max(c - 1, 0));
      else            focusCell(r, Math.min(c + 1, COLS - 1));
      break;
    case 'ArrowUp':
      if (r > 0) { e.preventDefault(); commitCell(r,c,inputs[r][c].value.trim()); focusCell(r-1,c); }
      break;
    case 'ArrowDown':
      if (r < ROWS-1) { e.preventDefault(); commitCell(r,c,inputs[r][c].value.trim()); focusCell(r+1,c); }
      break;
    case 'ArrowLeft':
      if (inputs[r][c].selectionStart === 0 && c > 0) {
        e.preventDefault(); commitCell(r,c,inputs[r][c].value.trim()); focusCell(r,c-1);
      }
      break;
    case 'ArrowRight':
      if (inputs[r][c].selectionStart === inputs[r][c].value.length && c < COLS-1) {
        e.preventDefault(); commitCell(r,c,inputs[r][c].value.trim()); focusCell(r,c+1);
      }
      break;
    case 'Escape':
      inputs[r][c].value = display(r, c);
      elFormulaBar.value  = getRaw(r, c);
      break;
  }
}

function focusCell(r, c) {
  inputs[r][c].focus();
  inputs[r][c].setSelectionRange(9999, 9999);
}

// ── Formula bar ───────────────────────────────────────────────────────────────
elFormulaBar.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    if (!state.sel) return;
    const { r, c } = state.sel;
    commitCell(r, c, elFormulaBar.value.trim());
    inputs[r][c].value = display(r, c);
    focusCell(r, c);
  }
  if (e.key === 'Escape') {
    if (!state.sel) return;
    const { r, c } = state.sel;
    elFormulaBar.value = getRaw(r, c);
    focusCell(r, c);
  }
});

// Keep cell input in sync while typing in formula bar
elFormulaBar.addEventListener('input', () => {
  if (!state.sel) return;
  const { r, c } = state.sel;
  inputs[r][c].value = elFormulaBar.value;
});

// ── Data helpers ──────────────────────────────────────────────────────────────
function getRaw(r, c) {
  return state.data[state.current][`${r},${c}`] ?? '';
}

function commitCell(r, c, val) {
  if (val === '') {
    delete state.data[state.current][`${r},${c}`];
  } else {
    state.data[state.current][`${r},${c}`] = val;
  }
  refreshDisplay();
  saveData();
}

function display(r, c) {
  const raw = getRaw(r, c);
  if (!raw) return '';
  if (raw.startsWith('=')) {
    const result = evaluate(raw.slice(1).trim().toUpperCase());
    return result === null ? '#ERR' : String(result);
  }
  return raw;
}

function refreshDisplay() {
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      if (state.sel && state.sel.r === r && state.sel.c === c) continue;
      const val = display(r, c);
      inputs[r][c].value = val;
      cellWraps[r][c].classList.toggle('error-cell', val.startsWith('#'));
    }
  }
}

// ── Formula engine ────────────────────────────────────────────────────────────
function evaluate(expr) {
  try {
    return evalExpr(expr);
  } catch (_) {
    return '#ERR';
  }
}

function evalExpr(expr) {
  expr = expr.trim();

  // SUM(...)
  let m = expr.match(/^SUM\((.+)\)$/i);
  if (m) {
    const vals = parseArgs(m[1]);
    return fmt(vals.reduce((a, b) => a + b, 0));
  }

  // AVG(...) / AVERAGE(...)
  m = expr.match(/^(?:AVG|AVERAGE)\((.+)\)$/i);
  if (m) {
    const vals = parseArgs(m[1]);
    if (!vals.length) return '#DIV/0';
    return fmt(vals.reduce((a, b) => a + b, 0) / vals.length);
  }

  // MIN(...)
  m = expr.match(/^MIN\((.+)\)$/i);
  if (m) {
    const vals = parseArgs(m[1]);
    return vals.length ? fmt(Math.min(...vals)) : '#ERR';
  }

  // MAX(...)
  m = expr.match(/^MAX\((.+)\)$/i);
  if (m) {
    const vals = parseArgs(m[1]);
    return vals.length ? fmt(Math.max(...vals)) : '#ERR';
  }

  // COUNT(...)
  m = expr.match(/^COUNT\((.+)\)$/i);
  if (m) return parseArgs(m[1]).length;

  // Arithmetic — replace cell refs then eval
  const substituted = expr.replace(/\b([A-F])([1-6])\b/gi, (_, col, row) =>
    String(cellNum(col.toUpperCase(), parseInt(row)))
  );

  if (!/^[\d\s+\-*/().]+$/.test(substituted)) return '#ERR';

  // eslint-disable-next-line no-new-func
  const result = new Function(`"use strict"; return (${substituted})`)();
  if (typeof result !== 'number' || !isFinite(result)) return '#ERR';
  return fmt(result);
}

function fmt(n) {
  if (typeof n !== 'number') return n;
  return Number.isInteger(n) ? n : parseFloat(n.toPrecision(10));
}

function cellNum(colLetter, rowNum) {
  const r = rowNum - 1;
  const c = colLetter.charCodeAt(0) - 65;
  if (r < 0 || r >= ROWS || c < 0 || c >= COLS) return 0;
  const raw = getRaw(r, c);
  if (!raw) return 0;
  if (raw.startsWith('=')) {
    const v = evaluate(raw.slice(1).trim().toUpperCase());
    return parseFloat(v) || 0;
  }
  return parseFloat(raw) || 0;
}

function parseArgs(args) {
  args = args.trim();

  // Range A1:F6
  const rangeM = args.match(/^([A-F])([1-6]):([A-F])([1-6])$/i);
  if (rangeM) {
    const r1 = parseInt(rangeM[2]) - 1, c1 = rangeM[1].toUpperCase().charCodeAt(0) - 65;
    const r2 = parseInt(rangeM[4]) - 1, c2 = rangeM[3].toUpperCase().charCodeAt(0) - 65;
    const vals = [];
    for (let r = Math.min(r1,r2); r <= Math.max(r1,r2); r++) {
      for (let c = Math.min(c1,c2); c <= Math.max(c1,c2); c++) {
        const raw = getRaw(r, c);
        if (raw !== '') {
          const n = raw.startsWith('=')
            ? parseFloat(evaluate(raw.slice(1).trim().toUpperCase()))
            : parseFloat(raw);
          if (!isNaN(n)) vals.push(n);
        }
      }
    }
    return vals;
  }

  // Comma-separated cell refs or literals
  return args.split(',').map(a => {
    a = a.trim();
    const cm = a.match(/^([A-F])([1-6])$/i);
    if (cm) return cellNum(cm[1].toUpperCase(), parseInt(cm[2]));
    return parseFloat(a) || 0;
  });
}

// ── Sheet management ──────────────────────────────────────────────────────────
function renderTabs() {
  elTabs.innerHTML = '';
  state.sheets.forEach(name => {
    const btn = document.createElement('button');
    btn.className = 'tab' + (name === state.current ? ' active' : '');
    btn.textContent = name;
    btn.addEventListener('click', () => switchSheet(name));
    elTabs.appendChild(btn);
  });
}

function switchSheet(name) {
  state.current = name;
  state.sel = null;
  elCellRef.textContent    = '';
  elFormulaBar.value       = '';

  // Clear all selection highlights
  for (let r = 0; r < ROWS; r++)
    for (let c = 0; c < COLS; c++)
      cellWraps[r][c].classList.remove('selected');

  renderTabs();
  refreshDisplay();
}

document.getElementById('btn-add').addEventListener('click', () => {
  let n = 1;
  while (state.sheets.includes(`Sheet${n}`)) n++;
  const name = `Sheet${n}`;
  state.sheets.push(name);
  state.data[name] = {};
  renderTabs();
  switchSheet(name);
  saveData();
});

document.getElementById('btn-remove').addEventListener('click', () => {
  if (state.sheets.length <= 1) {
    alert('At least one sheet must remain.');
    return;
  }
  const idx = state.sheets.indexOf(state.current);
  state.sheets.splice(idx, 1);
  delete state.data[state.current];
  const next = state.sheets[Math.min(idx, state.sheets.length - 1)];
  renderTabs();
  switchSheet(next);
  saveData();
});

// ── Persistence ───────────────────────────────────────────────────────────────
function saveData() {
  if (window.api) {
    window.api.saveData({
      sheets:  state.sheets,
      data:    state.data,
      current: state.current,
    });
  }
}

async function loadData() {
  if (!window.api) { bootstrap(null); return; }
  const saved = await window.api.loadData();
  bootstrap(saved);
}

function bootstrap(saved) {
  if (saved && Array.isArray(saved.sheets) && saved.sheets.length) {
    state.sheets  = saved.sheets;
    state.data    = saved.data   || {};
    state.current = saved.sheets.includes(saved.current)
      ? saved.current
      : saved.sheets[0];
    // Ensure every sheet has a data entry
    state.sheets.forEach(s => { if (!state.data[s]) state.data[s] = {}; });
  }
  renderTabs();
  refreshDisplay();
}

loadData();
