# BraillePad — Accessible Braille Text Editor

BraillePad is a Windows desktop text editor for entering Unicode text through
six-dot Braille. It is built with Python, PySide6, and the bundled Liblouis
translation engine. The editor is keyboard-first and exposes its document
through Qt's accessibility interfaces.

## How it works

BraillePad treats Braille as an input method, not as a separate document
format. While Braille input is enabled, compose a cell by pressing the dot
keys, then commit it with `Space`. The translated character is inserted at the
current text cursor. Pressing `Space` with no composed cell inserts a normal
word space.

The default physical-key layout is `F`=1, `D`=2, `S`=3, `J`=4, `K`=5, and
`L`=6. The number keys `1`–`6` are also accepted as dot input. Dots are
deduplicated and normalized, so `FDSK` and `1245` describe the same cell.
`Backspace` removes the most recently entered dot. `Enter` commits a pending
cell and starts a new native editor line.

`Ctrl+B` toggles Braille input. When it is off, the editor accepts ordinary
printable keyboard input. Navigation, selection, clipboard commands, undo,
redo, and editing remain standard Qt text-editor operations.

## Translation profiles

The **Braille language** menu selects the active Liblouis table. The bundled
profiles are English (UEB), Hindi, Sanskrit, Marathi, Nepali, Assamese,
Bengali, Gujarati, Punjabi, Kannada, Malayalam, Odia, Tamil, Telugu, and
Urdu. Urdu uses right-to-left layout. Indian-language profiles use the bundled
Bharati-target tables; their conformance should be validated independently
for production use.

English supports letters, punctuation, capital and number indicators, and
numeric-mode handling. Other profiles are translated through their bundled
Liblouis tables. The `vendor` directory contains the Liblouis 3.38.0 Windows
runtime and tables required by the application.

## Running on Windows

Install Python 3.10 or newer and PySide6, then run from the repository root:

```text
python -m pip install PySide6 pytest
python -m braille_input
```

You can also double-click `BraillePad.pyw` or `run.bat`. The `.pyw` launcher
starts without opening a console window.

## Documents

- `.txt` files contain ordinary UTF-8 Unicode text and are portable.
- `.json` files contain the text plus Braille metadata: language, canonical
  cells, translation state, cursor information, and document version.

Use **File → Open**, **File → Save**, and **File → Save As** to work with
documents. JSON preserves Braille input history; TXT is best for
interoperability.

## Accessibility

The editor uses a `QPlainTextEdit` as the authoritative accessible text
document. It reports the real caret, logical lines, selections, and empty
lines through Qt accessibility APIs. AO2 output is used for Braille input and
status announcements when an AO2-compatible driver is available. NVDA/JAWS
and physical Braille-display behavior still require testing on the target
machine.

## Tests

Run the test suite from the repository root:

```text
python -m pytest
```

The tests cover composition, translation, language profiles, numeric handling,
editing at the cursor, native line behavior, metadata persistence, and
accessibility diagnostics. See [USER_GUIDE.md](USER_GUIDE.md) for the complete
keyboard reference and workflow.
