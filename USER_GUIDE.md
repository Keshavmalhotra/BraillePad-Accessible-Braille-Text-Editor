# BraillePad User Guide

## Project attribution

This project was created entirely using OpenAI Codex. Keshav Malhotra, the
project creator, did not write a single line of code manually; the source code
was generated and developed through Codex.

## 1. Start BraillePad

On Windows, double-click `BraillePad.pyw` or `run.bat`. From PowerShell or a
Command Prompt, run this command from the repository root:

```text
python -m braille_input
```

The application requires Python, PySide6, and the bundled `vendor` directory.
The vendor directory must remain beside the `braille_input` package because it
contains `lou_translate.exe` and the translation tables.

## 2. The editor

The central area is a normal multiline Qt text editor. The cursor can be moved
through the document, text can be selected, and text can be inserted at the
cursor or used to replace a selection. Long lines are not wrapped; they can be
scrolled horizontally.

The menus are **File** (New, Open, Save, Save As), **Edit** (Undo, Redo, Cut,
Copy, Paste), and **Braille language** (translation-profile selection). The
status bar shows the current logical line and column. Empty lines are retained
during navigation and saving.

### Why the editor uses Qt

The text area is PySide6's native `QPlainTextEdit`, backed by Qt's
`QTextDocument`, `QTextBlock`, and `QTextCursor`. Braille key handling is the
only custom editor-subclass behavior; document lines, caret movement,
selection, clipboard, undo/redo, accessibility text, and no-wrap scrolling
remain native Qt behavior. This preserves real empty lines and avoids a second
custom current-line or current-caret model. Empty lines receive no custom
speech announcement; native accessibility is allowed to handle their actual
zero-length text range naturally.

## 3. Enter Braille cells

Braille input is mandatory. Compose every printable character through a Braille
cell using this layout:

| Keyboard key | Dot |
|---|---:|
| `F` or `1` | 1 |
| `D` or `2` | 2 |
| `S` or `3` | 3 |
| `J` or `4` | 4 |
| `K` or `5` | 5 |
| `L` or `6` | 6 |

Press `Space` to translate and insert the composed cell. The space is consumed
as the commit key; it does not add a word separator. Press `Space` again after
the cell has been committed to insert a normal space.

Dot order does not matter and duplicate dots are ignored. For example, `FDSK`,
`1245`, and `5421` all produce the canonical cell `1245`.

| Key | Behavior |
|---|---|
| `Backspace` | Remove the last dot while composing; otherwise delete text normally. |
| `Enter` | Commit a pending cell, then create a new line; with no pending cell, just create a line. |
| `Space` | Commit a pending cell, or insert an ordinary space when empty. |
| `Ctrl+B` | No longer changes input mode; Braille input is always enabled. |

Ordinary printable letters and punctuation are not inserted directly. Use their
Braille cells. `Tab` remains a normal editor key, and command shortcuts and
navigation continue to work normally.

## 4. Language and number handling

Choose a profile from **Braille language** before entering text. Available
profiles are English, Hindi, Sanskrit, Marathi, Nepali, Assamese, Bengali,
Gujarati, Punjabi, Kannada, Malayalam, Odia, Tamil, Telugu, and Urdu.

English uses UEB tables. The English number sign is dot `3456`; after it,
letters `a` through `j` can represent digits in numeric mode. The capital sign
is dot `6`. For Indian scripts, some dependent-vowel and multi-cell sequences
are translated together, so keep cells in the same word and use a real space
as the word boundary.

Changing profiles does not rewrite text already present in the editor.

## 5. Normal editing and shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+N` | New document |
| `Ctrl+O` | Open document |
| `Ctrl+S` | Save document |
| `Ctrl+Shift+S` | Save As |
| `Ctrl+Z` / `Ctrl+Y` | Undo / redo |
| `Ctrl+X` / `Ctrl+C` / `Ctrl+V` | Cut / copy / paste |
| Arrow, Home, End | Move the caret |
| `Ctrl` + Arrow | Move by word where supported by Qt |
| `Shift` + navigation | Select text |

Clicking in the document places the real Qt text cursor. Braille output is
inserted at that position, not automatically at the end of the file.

## 6. Open and save files

Use **File → Open** to open either a UTF-8 `.txt` file or a BraillePad `.json`
file. Text files contain only visible Unicode text. JSON files contain a
`text` field and a `braille` snapshot preserving the selected language,
canonical committed cells, cursor state, number mode, capital state, and
document version. The visible `text` remains the document content.

## 7. Accessibility behavior

BraillePad exposes the central editor through Qt's accessible text interface.
Assistive technology can inspect the actual document, caret, logical lines,
selections, and empty lines. The status bar also reports line and column.

AO2 announcements may report composed dots, committed translations, language
and mode changes. Empty lines do not produce a custom announcement, and
neighboring line text is never used as a fallback. Exact speech or Braille
output depends on the active AO2-compatible driver. Live NVDA/JAWS and
physical Braille-display coverage is not yet verified.

## 8. Troubleshooting

### The program does not start

Run it from a terminal to see the error:

```text
python -m braille_input
```

Confirm that PySide6 is installed and that
`vendor\\bin\\lou_translate.exe` exists. Do not move or rename `vendor`.

### Letters or punctuation do not appear

Braille input is mandatory. Enter the character using its Braille cell.

### A number key does not type a number

Keys `1`–`6` are always Braille dot keys. Use the English number sign and
numeric mode, or paste the number.

### Translation fails

Check that the selected table exists under
`vendor\\share\\liblouis\\tables`. The bundled profiles depend on Liblouis
3.38.0. Unsupported or invalid cells may be reported as untranslated.

## 9. Known limitations

- Indian-language profiles are Bharati 2.1 targets and need external
  conformance validation.
- Braille metadata is most complete for cells entered through BraillePad;
  ordinary typed or pasted text does not create corresponding cell metadata.
- Full live screen-reader and physical Braille-display coverage is not yet
  verified.
- The current UI does not include the old documented Read menu or F6–F8 read
  shortcuts; use the active screen reader's normal reading commands.
