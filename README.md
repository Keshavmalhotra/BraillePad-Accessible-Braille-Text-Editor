# BraillePad: Accessible Braille Text Editor

BraillePad is a keyboard-first Windows text editor
with direct six-dot Braille input. Type the numbers of the active dots, then
press `Space` to commit a Braille cell. For example, `1245` produces `g`.

## Features

- Direct dot-number entry using keys `1` through `6`
- Normal text-editor navigation, selection, clipboard, undo, and redo
- Accessible read-aloud actions for the current line, paragraph, or document
- English Grade 1-style Braille with basic punctuation and numeric mode
- Optional Liblouis support for broader translation coverage
- Unicode text output with Braille input preserved in saved documents

Duplicate dots are ignored and dot order is normalized, so `1245` and `5421`
represent the same cell. `Ctrl+B` switches between Braille input and ordinary
numeric keyboard input. Tab remains a normal editor key.

## Run on Windows

Double-click `VirtualBraille.pyw` or `run.bat`.

From the repository root, run:

```text
python -m braille_input
```

The bundled `vendor` directory contains the Liblouis runtime used when it is
available. If it is unavailable, the editor uses its clearly limited basic
fallback translator.

## Tests

Run the test suite from the repository root with:

```text
python -m pytest
```

See [USER_GUIDE.md](USER_GUIDE.md) for the complete editor workflow,
keyboard controls, accessibility behavior, and file formats.

Braille output remains available through the reused AO2 adapter; a physical
Braille display has not yet been tested.
