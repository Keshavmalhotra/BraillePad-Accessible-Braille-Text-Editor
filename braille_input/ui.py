"""wxPython UI for BraillePad.

The editor is wxPython's native multiline TextCtrl.  It owns the document,
lines, caret, selection, clipboard, undo/redo, and accessibility surface;
this module only intercepts Braille input keys and connects menus to the
existing translation/document layers.
"""
import json
from pathlib import Path

import wx

from .accessibility import Announcer
from .engine import BrailleDocument, CellComposer
from .tables import TABLES

PHYSICAL_DOTS = {"f": "1", "d": "2", "s": "3", "j": "4", "k": "5", "l": "6"}


class BrailleTextCtrl(wx.TextCtrl):
    def __init__(self, parent, owner):
        style = (wx.TE_MULTILINE | wx.TE_RICH2 | wx.TE_DONTWRAP |
                 wx.HSCROLL | wx.VSCROLL | wx.WANTS_CHARS)
        super().__init__(parent, style=style)
        self.owner = owner
        self.composer = CellComposer()
        self.SetName("Braille text document")
        self.Bind(wx.EVT_CHAR, self._on_char)
        self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
        self.Bind(wx.EVT_TEXT, lambda event: (self.owner._cursor_changed(), event.Skip()))
        self.Bind(wx.EVT_SET_FOCUS, lambda event: (self.owner._cursor_changed(), event.Skip()))

    def _on_char(self, event):
        key = event.GetKeyCode()
        text = event.GetUnicodeKey()
        char = chr(text) if text and text != wx.WXK_NONE else ""
        dot = PHYSICAL_DOTS.get(char.lower())
        if dot:
            self.composer.add(dot)
            self.owner.announcer.composing(self.composer.dots)
            self.owner.status.SetLabel(f"Braille dots: {self.composer.dots}")
            return
        if key == wx.WXK_SPACE and self.composer.dots:
            self.owner.commit_cell(); return
        if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and self.composer.dots:
            self.owner.commit_cell()
            self.owner.insert_line_break()
            return
        # Printable text is Braille-only.  Control/navigation keys are handled
        # by the native TextCtrl key processing below.
        if char and char.isprintable() and key != wx.WXK_SPACE:
            return
        event.Skip()

    def _on_key_down(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_BACK and self.composer.dots:
            self.composer.remove_last(); self.owner.announcer.composing(self.composer.dots); return
        if key == wx.WXK_SPACE and not self.composer.dots:
            self.owner.insert_space(); return
        if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            self.owner.insert_line_break(); return
        event.Skip()

    def accessibility_line_range(self):
        pos = self.GetInsertionPoint()
        _ok, _column, line = self.PositionToXY(pos)
        start = self.XYToPosition(0, line)
        end = self.XYToPosition(self.GetLineLength(line), line)
        return start, end, pos

    def line_diagnostics(self):
        pos = self.GetInsertionPoint(); _ok, _column, line = self.PositionToXY(pos)
        start, end, caret = self.accessibility_line_range()
        return {"document": self.GetValue(), "logical_line_count": self.GetNumberOfLines(),
                "caret_position": caret, "current_block": line,
                "current_block_text": self.GetLineText(line),
                "line_start": start, "line_end": end,
                "accessibility_range": (start, end, caret), "wrap_mode": "NoWrap"}


class BrailleWindow(wx.Frame):
    def __init__(self):
        super().__init__(None, title="BraillePad: Accessible Braille Text Editor", size=(900, 650))
        self.document = BrailleDocument(); self.path = None
        self.announcer = Announcer()
        panel = wx.Panel(self); box = wx.BoxSizer(wx.VERTICAL)
        self.editor = BrailleTextCtrl(panel, self); box.Add(self.editor, 1, wx.EXPAND)
        self.status = wx.StaticText(panel, label="Line 1, column 1")
        box.Add(self.status, 0, wx.EXPAND | wx.ALL, 3); panel.SetSizer(box)
        self._make_menu(); self.CreateStatusBar(); self.SetStatusText("Braille input: mandatory")

    def _make_menu(self):
        bar = wx.MenuBar(); file_menu = wx.Menu()
        for label, key, fn in (("New", "Ctrl+N", self.new_document), ("Open", "Ctrl+O", self.open_document),
                               ("Save", "Ctrl+S", self.save_document), ("Save As", "Ctrl+Shift+S", self.save_as)):
            item = file_menu.Append(wx.ID_ANY, label + "\t" + key); self.Bind(wx.EVT_MENU, lambda e, f=fn: f(), item)
        bar.Append(file_menu, "File")
        edit = wx.Menu()
        for label, fn in (("Undo", self.editor.Undo), ("Redo", self.editor.Redo), ("Cut", self.editor.Cut),
                          ("Copy", self.editor.Copy), ("Paste", self.editor.Paste)):
            item = edit.Append(wx.ID_ANY, label); self.Bind(wx.EVT_MENU, lambda e, f=fn: f(), item)
        bar.Append(edit, "Edit")
        lang = wx.Menu()
        for key, info in TABLES.items():
            item = lang.AppendRadioItem(wx.ID_ANY, f"{info.language} — {info.standard} ({info.version})")
            self.Bind(wx.EVT_MENU, lambda e, k=key: self.set_language(k), item)
        bar.Append(lang, "Braille language"); self.SetMenuBar(bar)

    def _cursor_changed(self):
        pos = self.editor.GetInsertionPoint(); _ok, _column, line = self.editor.PositionToXY(pos)
        column = pos - self.editor.XYToPosition(0, line)
        self.status.SetLabel(f"Line {line + 1}, column {column + 1}")

    def set_language(self, key):
        self.document.set_table(key); self.announcer.send(f"Braille language: {self.document.table.info.language}.")

    def commit_cell(self):
        start, end = self.editor.GetSelection(); self.document.cursor = start
        cell = self.document.commit(self.editor.composer.dots)
        printable = "" if cell.dots in (self.document.table.number_sign, "6") else cell.meaning
        self.editor.Replace(start, end, printable); self.editor.SetInsertionPoint(start + len(printable))
        self.editor.composer.clear(); self.announcer.committed(cell); self._cursor_changed()

    def insert_space(self):
        start, end = self.editor.GetSelection(); self.editor.Replace(start, end, " "); self.editor.SetInsertionPoint(start + 1); self._cursor_changed()

    def insert_line_break(self):
        start, end = self.editor.GetSelection(); self.editor.Replace(start, end, "\n"); self.editor.SetInsertionPoint(start + 1); self._cursor_changed()

    def new_document(self):
        self.editor.Clear(); self.editor.composer.clear(); self.document = BrailleDocument(); self.path = None

    def open_document(self):
        with wx.FileDialog(self, "Open document", wildcard="Text (*.txt)|*.txt|Braille document (*.json)|*.json", style=wx.FD_OPEN) as dialog:
            if dialog.ShowModal() != wx.ID_OK: return
            p = Path(dialog.GetPath())
        if p.suffix.lower() == ".json":
            saved = json.loads(p.read_text(encoding="utf-8")); self.document = BrailleDocument.from_snapshot(saved.get("braille", saved)); text = saved.get("text", self.document.text)
        else:
            text = p.read_text(encoding="utf-8"); self.document = BrailleDocument()
        self.editor.SetValue(text); self.editor.composer.clear(); self.path = p; self._cursor_changed()

    def save_document(self):
        if not self.path: return self.save_as()
        if self.path.suffix.lower() == ".json":
            data = {"version": 1, "text": self.editor.GetValue(), "braille": self.document.snapshot()}
            self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        else: self.path.write_text(self.editor.GetValue(), encoding="utf-8")

    def save_as(self):
        with wx.FileDialog(self, "Save document", defaultFile="document.txt", wildcard="Text (*.txt)|*.txt|Braille document (*.json)|*.json", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dialog:
            if dialog.ShowModal() == wx.ID_OK: self.path = Path(dialog.GetPath()); self.save_document()
