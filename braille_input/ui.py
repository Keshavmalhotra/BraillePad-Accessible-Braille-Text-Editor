import json
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QTextCursor, QAccessible, QAccessibleEvent, QTextOption
from PySide6.QtWidgets import QMainWindow, QPlainTextEdit, QFileDialog, QStatusBar
from PySide6.QtGui import QActionGroup
from .tables import TABLES
from .engine import CellComposer, BrailleDocument
from .accessibility import Announcer

PHYSICAL_DOTS = {"f": "1", "d": "2", "s": "3", "j": "4", "k": "5", "l": "6"}

class BrailleTextEdit(QPlainTextEdit):
    def __init__(self, owner):
        super().__init__(); self.owner=owner; self.composer=CellComposer()
        # Keep visual lines identical to logical QTextBlocks.  Long lines are
        # horizontally scrollable instead of being split into visual rows.
        # Disable both Qt's editor line-wrap mode and the underlying document
        # word-wrap policy. This keeps every logical line a single navigation
        # row; Up/Down never moves through visual wrapped fragments.
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.setAccessibleName("Braille text document")
    def keyPressEvent(self, event):
        key, mods, text = event.key(), event.modifiers(), event.text()
        dot = PHYSICAL_DOTS.get(text.lower()) if text else None
        if dot:
            self.composer.add(dot); self.owner.announcer.composing(self.composer.dots); self.owner.statusBar().showMessage(f"Braille dots: {self.composer.dots}"); return
        if key == Qt.Key_Backspace and self.composer.dots: self.composer.remove_last(); self.owner.announcer.composing(self.composer.dots); return
        # Space has two deliberately distinct meanings.  With a composed
        # cell it is the cell-commit key and must be consumed; otherwise it is
        # an ordinary word separator.  Forwarding both cases used to insert a
        # space after every Braille cell.
        if key == Qt.Key_Space and self.composer.dots:
            self.owner.commit_cell(); return
        if key == Qt.Key_Space:
            self.owner.insert_space(); return
        if self.composer.dots and key in (Qt.Key_Return, Qt.Key_Enter):
            self.owner.commit_cell(); self.owner.insert_line_break(event); return
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.owner.insert_line_break(event); return

        # Braille mode is an input method, not a second ordinary keyboard
        # path.  Let command shortcuts (copy, paste, undo, etc.) and all
        # navigation/editing keys reach QPlainTextEdit, but consume printable
        # text that was not produced by the dot composer.  This also blocks
        # punctuation typed directly; punctuation must use its Braille cell.
        command_mods = Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier
        if text and text.isprintable() and key != Qt.Key_Space and not (mods & command_mods):
            return
        super().keyPressEvent(event)
        self.owner._cursor_changed()

    def accessibility_line_range(self):
        """Return the actual current line range and caret offset.

        The range is derived from the live Qt cursor on every call.  In
        particular, an empty QTextBlock is a real line whose range has equal
        start and end offsets; it must not be replaced with a neighbouring
        block's range.
        """
        cursor = self.textCursor()
        block = cursor.block()
        start = block.position()
        return start, start + len(block.text()), cursor.position()

    def line_diagnostics(self):
        """Return the native document/caret/accessibility state for debugging."""
        cursor = self.textCursor()
        block = cursor.block()
        start, end, caret = self.accessibility_line_range()
        accessible_text = ""
        accessible_caret = None
        interface = QAccessible.queryAccessibleInterface(self)
        text_interface = interface.textInterface() if interface else None
        if text_interface:
            accessible_caret = text_interface.cursorPosition()
            accessible_text = text_interface.text(0, text_interface.characterCount())
        return {
            "document": self.toPlainText(),
            "logical_line_count": self.document().blockCount(),
            "caret_position": cursor.position(),
            "current_block": block.blockNumber(),
            "current_block_text": block.text(),
            "line_start": start,
            "line_end": end,
            "accessibility_range": (start, end, caret),
            "accessibility_caret": accessible_caret,
            "accessibility_text": accessible_text,
            "wrap_mode": self.lineWrapMode().name,
        }

class BrailleWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("BraillePad: Accessible Braille Text Editor"); self.document=BrailleDocument(); self.editor=BrailleTextEdit(self); self.setCentralWidget(self.editor); self.setStatusBar(QStatusBar()); self.announcer=Announcer(); self.path=None; self._last_blank_range=None; self._make_actions(); self.editor.cursorPositionChanged.connect(self._cursor_changed); self.editor.textChanged.connect(self._document_changed)
    def _make_actions(self):
        menu=self.menuBar().addMenu("File")
        for name, shortcut, fn in (("New","Ctrl+N",self.new_document),("Open","Ctrl+O",self.open_document),("Save","Ctrl+S",self.save_document),("Save As","Ctrl+Shift+S",self.save_as)):
            action=QAction(name,self); action.setShortcut(QKeySequence(shortcut)); action.triggered.connect(fn); menu.addAction(action)
        edit=self.menuBar().addMenu("Edit")
        for name, shortcut, fn in (("Undo","Ctrl+Z",self.editor.undo),("Redo","Ctrl+Y",self.editor.redo),("Cut","Ctrl+X",self.editor.cut),("Copy","Ctrl+C",self.editor.copy),("Paste","Ctrl+V",self.editor.paste)):
            action=QAction(name,self); action.setShortcut(QKeySequence(shortcut)); action.triggered.connect(fn); edit.addAction(action)
        braille=self.menuBar().addMenu("Braille language"); group=QActionGroup(self); group.setExclusive(True)
        for key, info in TABLES.items():
            action=QAction(f"{info.language} — {info.standard} ({info.version})", self, checkable=True); action.setData(key); action.setChecked(key == self.document.language_key); action.triggered.connect(lambda checked, k=key: self.set_language(k)); group.addAction(action); braille.addAction(action)
        # QPlainTextEdit is the accessibility source of truth.  Do not add
        # synthetic line/caret speech that can report a neighbouring block.
    def _cursor_changed(self):
        cursor = self.editor.textCursor()
        block = cursor.block()
        start, end, caret = self.editor.accessibility_line_range()
        # Keep assistive technology synchronized with the native caret after
        # Up/Down, Enter, deletion, and edits.  Qt's text interface reads the
        # live cursor; this event makes the change observable immediately.
        # Qt/NVDA can derive the preceding paragraph as spoken context when a
        # caret-moved event targets a zero-length block.  For an empty line the
        # explicit blank announcement below is the complete announcement;
        # the live QAccessible text interface still exposes the real caret and
        # range without manufacturing a neighboring line event.
        if start != end:
            QAccessible.updateAccessibility(QAccessibleEvent(self.editor, QAccessible.Event.TextCaretMoved))
        self.statusBar().showMessage(f"Line {block.blockNumber()+1}, column {cursor.columnNumber()+1}")
        # QPlainTextEdit remains the source of truth.  This is only a small
        # AO2 fallback for stacks that expose an empty QTextBlock without a
        # usable spoken indication.  It is transition-based, so it cannot
        # repeatedly speak while the caret remains in the same blank block.
        if start == end:
            blank_range = (start, end, caret)
            if blank_range != self._last_blank_range:
                self._last_blank_range = blank_range
                self.announcer.blank_line()
        else:
            self._last_blank_range = None
    def _document_changed(self):
        # A new document can reuse the same offset. Invalidate the fallback
        # rather than identifying a line by cached text or block number.
        self._last_blank_range = None
    def set_language(self, key):
        self.document.set_table(key); self.editor.setLayoutDirection(Qt.RightToLeft if self.document.table.info.rtl else Qt.LeftToRight)
        self.announcer.send(f"Braille language: {self.document.table.info.language}.")
    def commit_cell(self):
        cursor=self.editor.textCursor()
        # Keep the metadata stream aligned with the real Qt cursor, including
        # insertion and replacement of a selection.
        self.document.cursor = cursor.position()
        cell=self.document.commit(self.editor.composer.dots)
        printable = "" if cell.dots in (self.document.table.number_sign, "6") else cell.meaning
        cursor.insertText(printable)
        self.editor.setTextCursor(cursor)
        # Indic tables need the complete contiguous Braille word.  Replace
        # only the just-entered word; spaces remain the sole word boundary.
        if self.document.language_key != "en":
            start, patterns = self.document.word_patterns_at(self.document.cursor)
            translated = self.document.table.translate_sequence(patterns, self.document.numeric)
            if translated:
                current = self.editor.textCursor(); end = current.position(); text = self.editor.toPlainText()
                word_start = end
                while word_start > 0 and not text[word_start-1].isspace(): word_start -= 1
                current.setPosition(word_start); current.setPosition(end, QTextCursor.MoveMode.KeepAnchor); current.insertText(translated)
                self.editor.setTextCursor(current)
        self.editor.composer.clear(); self.announcer.committed(cell); self._cursor_changed()
    def insert_space(self):
        """Insert a document word boundary without involving a language table."""
        cursor = self.editor.textCursor()
        self.document.cursor = cursor.position()
        self.document.space()
        cursor.insertText(" ")
        self.editor.setTextCursor(cursor)
        self._cursor_changed()
    def insert_line_break(self, event):
        """Record metadata and perform a native Notepad-style paragraph split.

        ``QPlainTextEdit`` stores lines as QTextBlocks.  Using the cursor's
        native block operation here is important: inserting a literal '\n'
        looks equivalent in plain text, but it does not preserve the same
        paragraph/undo semantics when a selection or an existing block
        boundary is involved.
        """
        # The Qt document is authoritative: create the real block and move
        # the real caret first.  Braille metadata is updated afterward and is
        # never consulted for line count or navigation.
        cursor = self.editor.textCursor()
        cursor.insertBlock()
        self.editor.setTextCursor(cursor)
        self.document.cursor = max(0, min(cursor.position() - 1, len(self.document.cells)))
        self.document.line_break()
        event.accept()
    def announce_word(self):
        text=self.editor.toPlainText(); p=self.editor.textCursor().position(); start=p
        while start>0 and not text[start-1].isspace(): start-=1
        end=p
        while end<len(text) and not text[end].isspace(): end+=1
        self.announcer.send(text[start:end] or "Blank.", False)
    def announce_line(self): self.announcer.send(self.editor.textCursor().block().text() or "Blank line.")
    def announce_paragraph(self):
        text=self.editor.toPlainText(); index=len(text[:self.editor.textCursor().position()].split("\n\n")); parts=text.split("\n\n"); self.announcer.send(f"Paragraph {index}. {parts[index-1] if index<=len(parts) else ''}")
    def announce_document(self): self.announcer.send(self.editor.toPlainText() or "Document empty.")
    def new_document(self):
        self.editor.clear(); self.editor.composer.clear(); self.document=BrailleDocument(); self.path=None; self.announcer.send("New document.")
    def open_document(self):
        p,_=QFileDialog.getOpenFileName(self,"Open document","","Text (*.txt);;Braille document (*.json)")
        if not p:return
        if p.lower().endswith(".json"):
            saved=json.loads(Path(p).read_text(encoding="utf-8")); self.document=BrailleDocument.from_snapshot(saved.get("braille", saved)); self.editor.setPlainText(saved.get("text", self.document.text)); self.editor.setLayoutDirection(Qt.RightToLeft if self.document.table.info.rtl else Qt.LeftToRight)
        else: self.editor.setPlainText(Path(p).read_text(encoding="utf-8")); self.editor.composer.clear(); self.document=BrailleDocument()
        self.path=Path(p); self.announcer.send("Document opened.")
    def save_document(self):
        if not self.path: return self.save_as()
        if self.path.suffix.lower()==".json": self.path.write_text(json.dumps({"version": 1, "text": self.editor.toPlainText(), "braille": self.document.snapshot()},indent=2), encoding="utf-8")
        else: self.path.write_text(self.editor.toPlainText(),encoding="utf-8")
    def save_as(self):
        p,_=QFileDialog.getSaveFileName(self,"Save document","document.txt","Text (*.txt);;Braille document (*.json)")
        if p:self.path=Path(p); self.save_document()
