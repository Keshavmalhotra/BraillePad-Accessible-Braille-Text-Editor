import json
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QPlainTextEdit, QFileDialog, QStatusBar
from PySide6.QtGui import QActionGroup
from .tables import TABLES
from .engine import CellComposer, BrailleDocument
from .accessibility import Announcer

class BrailleTextEdit(QPlainTextEdit):
    def __init__(self, owner):
        super().__init__(); self.owner=owner; self.composer=CellComposer(); self.braille_mode=True; self.setAccessibleName("Braille text document")
    def keyPressEvent(self, event):
        key, mods, text = event.key(), event.modifiers(), event.text()
        if key == Qt.Key_B and mods & Qt.ControlModifier: self.braille_mode=not self.braille_mode; self.owner.announcer.send(f"Braille input {'on' if self.braille_mode else 'off'}."); return
        if self.braille_mode and text and text in "123456": self.composer.add(text); self.owner.announcer.composing(self.composer.dots); self.owner.statusBar().showMessage(f"Braille dots: {self.composer.dots}"); return
        if self.braille_mode and text and text in "7890": self.owner.announcer.send("Invalid Braille dot. Use dots 1 through 6."); return
        if key == Qt.Key_Backspace and self.composer.dots: self.composer.remove_last(); self.owner.announcer.composing(self.composer.dots); return
        # Space has two deliberately distinct meanings.  With a composed
        # cell it is the cell-commit key and must be consumed; otherwise it is
        # an ordinary word separator.  Forwarding both cases used to insert a
        # space after every Braille cell.
        if key == Qt.Key_Space and self.composer.dots:
            self.owner.commit_cell(); return
        if self.composer.dots and key in (Qt.Key_Return, Qt.Key_Enter): self.owner.commit_cell(); super().keyPressEvent(event); return

        # Braille mode is an input method, not a second ordinary keyboard
        # path.  Let command shortcuts (copy, paste, undo, etc.) and all
        # navigation/editing keys reach QPlainTextEdit, but consume printable
        # text that was not produced by the dot composer.  This also blocks
        # punctuation typed directly; punctuation must use its Braille cell.
        command_mods = Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier
        if self.braille_mode and text and text.isprintable() and key != Qt.Key_Space and not (mods & command_mods):
            return
        super().keyPressEvent(event)

class BrailleWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Six-Dot Braille Text Editor"); self.document=BrailleDocument(); self.editor=BrailleTextEdit(self); self.setCentralWidget(self.editor); self.setStatusBar(QStatusBar()); self.announcer=Announcer(); self.path=None; self._make_actions(); self.editor.cursorPositionChanged.connect(self._cursor_changed)
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
        read=self.menuBar().addMenu("Read")
        for name, shortcut, fn in (("Current line","F6",self.announce_line),("Current paragraph","F7",self.announce_paragraph),("Entire document","F8",self.announce_document)):
            action=QAction(name,self); action.setShortcut(QKeySequence(shortcut)); action.triggered.connect(fn); read.addAction(action)
    def _cursor_changed(self): self.statusBar().showMessage(f"Line {self.editor.textCursor().blockNumber()+1}, column {self.editor.textCursor().columnNumber()+1}")
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
                current.setPosition(word_start); current.setPosition(end, current.KeepAnchor); current.insertText(translated)
                self.editor.setTextCursor(current)
        self.editor.composer.clear(); self.announcer.committed(cell); self._cursor_changed()
    def announce_cursor(self, key=None):
        cursor=self.editor.textCursor(); block=cursor.block(); line=block.text(); pos=cursor.positionInBlock()
        if key in (Qt.Key_Up,Qt.Key_Down): self.announcer.send(f"Line {block.blockNumber()+1}. {line or 'Blank line'}.", False)
        elif line and pos < len(line): self.announcer.send(self._spoken_char(line[pos]), False)
        else: self.announcer.send("End of line.", False)
    def announce_word(self):
        text=self.editor.toPlainText(); p=self.editor.textCursor().position(); start=p
        while start>0 and not text[start-1].isspace(): start-=1
        end=p
        while end<len(text) and not text[end].isspace(): end+=1
        self.announcer.send(text[start:end] or "Blank.", False)
    def _spoken_char(self, char): return {" ":"space", "\n":"new line", ".":"period", ",":"comma"}.get(char,char)
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
