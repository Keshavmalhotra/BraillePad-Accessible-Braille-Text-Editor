# Six-Dot Numeric Braille Input

This keyboard-first application lets the user type Braille dot numbers
directly. Keys `1` through `6` activate dots; Space commits the current cell,
while Space with an empty cell inserts a word separator. Dot order is normalized, so `1245` and `5421`
are the same cell. Duplicate dots are ignored and `7`–`9` are rejected.

Read the complete [User Guide](USER_GUIDE.md) for the editor workflow,
keyboard controls, Braille entry, accessibility behavior, and file formats.

The first translation table is English Grade 1-style literary Braille with
basic punctuation and numeric mode. The original dot cells remain in the
document and are saved, not just the interpreted text.

Alphabetic and ordinary punctuation keys do not directly insert text in Braille
mode. Navigation, editing commands, clipboard operations, and shortcuts remain
native text-editor behavior. `Ctrl+B` toggles between numeric Braille input and
normal numeric keyboard input. Tab is left to the normal text editor and is
never interpreted as a
Braille dot. Full UEB requires the optional Liblouis runtime; when it is not
available, the application clearly uses its limited basic fallback.

Run `VirtualBraille.pyw` on Windows or `python -m braille_input` from the
repository root. Install dependencies with `python -m pip install -r
requirements.txt` from `virtual_abacus` (the projects share those dependencies).

Braille output remains available through the reused AO2 adapter, but a real
Braille display has not been tested.
