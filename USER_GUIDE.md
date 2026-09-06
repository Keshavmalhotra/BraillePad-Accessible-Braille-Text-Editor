# BraillePad: Accessible Braille Text Editor — User Guide

## What this application is

BraillePad is a normal text editor with an additional
input method. You can write ordinary documents containing letters, numbers,
punctuation, words, sentences, paragraphs, and multiple lines.

Instead of pressing virtual Braille buttons, you type the numbers of the active
Braille dots directly on the keyboard. For example, typing `1245` and then
pressing Space inserts the English Braille letter `g` into the document. An
uppercase `G` requires the UEB capital indicator `6` before `1245`.

The result is ordinary Unicode text. You can copy it into Notepad, email,
websites, chat applications, or other documents.

The application does not treat the document as a list of isolated Braille
cells. Braille is an input method; the document itself is a normal editable
text document.

## Starting the application

### Windows

Double-click:

```text
BraillePad.pyw
```

This starts the application without leaving a terminal window open. You can
also double-click `run.bat`.

### Command line

From the `braille_input` folder, run:

```text
python -m braille_input
```

If dependencies are missing, install the shared project requirements from the
Virtual Abacus folder:

```text
python -m pip install -r ..\virtual_abacus\requirements.txt
```

## The editor window

The main window contains a large multiline editing area, like Windows
Notepad. The text cursor can be moved anywhere in the document. You can type
text through numeric Braille. Alphabetic and ordinary punctuation keys do not
directly insert text in Braille mode; clipboard, selection, navigation, and
editing commands remain available.

The menus are:

- **File** — New, Open, Save, and Save As.
- **Edit** — Undo, Redo, Cut, Copy, and Paste.
- **Read** — Read the current line, paragraph, or complete document.

The status bar reports the current line and column.

## Keyboard controls

### Braille input

| Key | Action |
|---|---|
| `1` through `6` | Add the corresponding Braille dot to the current cell |
| `Backspace` | Remove the highest-numbered dot currently entered |
| `Space` | Commit the current Braille cell; with no cell, insert a normal space |
| `Enter` | Commit a current cell, then create a new line |
| `7`, `8`, `9`, `0` | Announce that the dot is invalid |

The six dot keys are interpreted as Braille input while composing a cell. To
insert ordinary numeric characters, use the appropriate Braille number sign
and numeric Braille mode, or paste/type them through an input method that does
not use the six-dot keys.

### Normal text editing

| Key | Action |
|---|---|
| Letter and punctuation keys | Ignored as direct text input in Braille mode |
| Left / Right Arrow | Move by character using the standard text editor |
| Up / Down Arrow | Move through real document lines using the standard text editor |
| Home / End | Move to the beginning or end of the current line |
| Ctrl+Left / Ctrl+Right | Move by word using the standard text editor |
| Backspace / Delete | Delete text normally when no Braille cell is being composed |
| Shift with navigation keys | Select text normally |
| Ctrl+C | Copy selected Unicode text |
| Ctrl+X | Cut selected text |
| Ctrl+V | Paste text |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |

### Documents and reading

| Key | Action |
|---|---|
| Ctrl+N | New document |
| Ctrl+O | Open document |
| Ctrl+S | Save document |
| Ctrl+Shift+S | Save As |
| F6 | Read the current line |
| F7 | Read the current paragraph |
| F8 | Read the complete document |

## Entering Braille

Each Braille cell can contain any combination of dots 1 through 6. The order
does not matter.

For example, both sequences create the same cell:

```text
1245
5421
```

They are normalized internally to:

```text
1245
```

When the cell is committed, it is translated and inserted at the text cursor.

### Example: entering a letter

To enter lowercase `g`:

1. Press `1`.
2. Press `2`.
3. Press `4`.
4. Press `5`.
5. Press `Space`.

The document receives `g`. No space is inserted by this commit. To insert a
word space, press Space when no Braille cell is being composed. Consecutive
cells therefore form a word: commit `m`, commit `y`, then press Space with an
empty composition to produce `my `.

### Example: entering a word

Using English Grade 1-style Braille:

```text
H = 125
E = 15
L = 123
L = 123
O = 135
```

Enter each pattern and press Space after each cell. The document becomes:

```text
HELLO
```

The editor places every translated character at the current cursor position,
not automatically at the end of the document.

### Duplicate dots

Repeated dot numbers do not create duplicate dots. For example:

```text
11245
```

is treated as:

```text
1245
```

This keeps the input predictable and prevents invalid duplicate-dot cells.

### Invalid dots

Only `1`, `2`, `3`, `4`, `5`, and `6` are Braille dot keys. If you press
`7`, `8`, `9`, or `0` during Braille entry, the application announces:

> Invalid Braille dot. Use dots 1 through 6.

The invalid key is not inserted into the document.

## Writing normal documents

The editor supports ordinary document structure.

### New lines

Press Enter to begin a new line. If a Braille cell is being composed, Enter
first commits that cell and then starts the new line.

### Paragraphs

Press Enter twice to leave a blank line between paragraphs. F7 reads the
paragraph containing the cursor and identifies its paragraph number.

### Editing in the middle

Move the cursor with the arrow keys or click inside the text area. Compose a
Braille cell and press Space. The translated character is inserted exactly at
that position. If text is selected, the inserted character replaces the
selection, just like normal typing.

## Accessible output

The application reuses the existing Accessible Output 2 automatic output
integration from the previous accessible projects. It does not hard-code a
single screen reader.

Examples of output include:

- During entry: `Dots 1 2 4 5.`
- After committing: `Dots 1 2 4 5. g.`
- Normal caret movement and selection are exposed through the standard editable-text accessibility model for AO2/NVDA.
- Reading a line: the complete current line
- Reading the document: the complete document text

Output is semantic. It describes the character, word, line, or document state
rather than announcing raw key presses such as “Left Arrow pressed”.

AO2 output is also sent through its Braille-capable interface when the active
AO2 driver supports it. A physical Braille display has not been tested in the
current development environment, so physical Braille hardware support must be
considered unverified.

## Saving and opening

### Text files

Use `.txt` when you want a normal portable text document. The saved content is
ordinary Unicode text and can be opened by Notepad or another editor.

### Braille-preserving JSON files

Use `.json` when you also want to preserve the Braille metadata currently
available to the application. The file contains:

- the normal document text;
- the original canonical dot patterns for committed cells;
- translated meanings;
- translation mode information;
- document version information;
- cursor-related document state where available.

The text remains the primary document. Braille metadata is supplementary and
does not prevent the text from being used elsewhere.

## Translation support

The input engine and translation table are separate components. This means a
future table can support another code without rewriting keyboard composition.

The current implementation includes English Grade 1-style letter mappings,
basic punctuation, a number sign, and the beginning of numeric handling.
Literary, mathematical, computer, and other Braille codes should not be
assumed to be fully implemented yet.

## Troubleshooting

### The application does not start

Run `BraillePad.pyw` by double-clicking it. If it still fails, launch it
from a terminal once with:

```text
python -m braille_input
```

This can reveal a missing Python dependency. Install the requirements and try
again.

### Arrow keys appear silent

The editor sends cursor feedback through AO2. Verify that an AO2-supported
output driver or screen-reader output system is available. The visual status
bar still shows the line and column, but this is not a substitute for live
screen-reader testing.

### A number key does not insert a normal number

Keys `1`–`6` are reserved for Braille dot composition. Use Braille numeric
mode, paste the number, or use another normal text input method.

## Current limitations

- Live NVDA and JAWS testing has not been completed.
- A physical Braille display has not been tested.
- The current numeric Braille implementation is an initial English table, not
  a complete literary, mathematical, or computer Braille implementation.
- Braille metadata alignment is strongest for cells entered through this
  application; ordinary text typed directly does not create Braille metadata.
- The editor currently uses standard Qt editing behavior for clipboard and
  selection operations.

## Recommended workflow

1. Open the application and begin in the editor.
2. Use keys `1` through `6` to compose Braille cells.
3. Use keys `1`–`6` to compose Braille cells.
4. Press Space to commit each cell; press Space again with an empty cell to insert a word space.
5. Use arrows and Ctrl+Arrow to review the document.
6. Use F6, F7, or F8 to hear larger portions of the document.
7. Save as `.txt` for maximum compatibility or `.json` to retain Braille
   metadata.
