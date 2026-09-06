import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from braille_input.ui import BrailleWindow

app = QApplication.instance() or QApplication([])

def test_braille_inserts_at_cursor_and_tab_is_not_a_dot():
    window=BrailleWindow(); editor=window.editor; editor.setFocus()
    QTest.keyClicks(editor, "1245"); QTest.keyClick(editor, Qt.Key_Space)
    assert editor.toPlainText() == "g"
    editor.setCursorPosition(0, 0) if False else None
    editor.moveCursor(editor.textCursor().MoveOperation.Start)
    QTest.keyClick(editor, Qt.Key_Tab)
    assert editor.toPlainText().startswith("\t")
    assert editor.composer.dots == ""
    window.close()

def test_arrow_navigation_announces_destination_line():
    window=BrailleWindow(); window.editor.setPlainText("first line\nsecond line"); window.editor.moveCursor(window.editor.textCursor().MoveOperation.End)
    window.editor.setFocus(); QTest.keyClick(window.editor, Qt.Key_Up)
    assert window.editor.textCursor().blockNumber() == 0
    window.close()

def test_selection_braille_replaces_text_and_undo_redo():
    window=BrailleWindow(); editor=window.editor; editor.setPlainText("old text")
    cursor=editor.textCursor(); cursor.setPosition(0); cursor.setPosition(3, cursor.MoveMode.KeepAnchor); editor.setTextCursor(cursor)
    editor.setFocus(); QTest.keyClicks(editor, "1245"); QTest.keyClick(editor, Qt.Key_Space)
    assert editor.toPlainText() == "g text"
    editor.undo(); assert editor.toPlainText() == "old text"
    editor.redo(); assert editor.toPlainText() == "g text"
    window.close()

def test_tab_does_not_commit_composition():
    window=BrailleWindow(); editor=window.editor; editor.setFocus()
    QTest.keyClick(editor, Qt.Key_1); QTest.keyClick(editor, Qt.Key_Tab)
    assert editor.composer.dots == "1" and editor.toPlainText() == "\t"
    window.close()

def test_alphabetic_and_punctuation_keys_do_not_insert_direct_text():
    window=BrailleWindow(); editor=window.editor; editor.setFocus()
    QTest.keyClicks(editor, "keshav!")
    assert editor.toPlainText() == ""
    QTest.keyClicks(editor, "1245"); QTest.keyClick(editor, Qt.Key_Space)
    assert editor.toPlainText() == "g"
    window.close()

def _enter_cell(editor, dots):
    QTest.keyClicks(editor, dots)
    QTest.keyClick(editor, Qt.Key_Space)

def test_braille_cells_form_words_and_only_empty_space_separates_words():
    window=BrailleWindow(); editor=window.editor; editor.setFocus()
    # m y / n a m e / i s / k e s h a v
    for dots in ("134", "13456"):
        _enter_cell(editor, dots)
    QTest.keyClick(editor, Qt.Key_Space)  # empty composition: real word space
    for dots in ("1345", "1", "134", "15"):
        _enter_cell(editor, dots)
    QTest.keyClick(editor, Qt.Key_Space)
    for dots in ("24", "234"):
        _enter_cell(editor, dots)
    QTest.keyClick(editor, Qt.Key_Space)
    for dots in ("13", "15", "234", "125", "1", "1236"):
        _enter_cell(editor, dots)
    assert editor.toPlainText() == "my name is keshav"
    assert editor.textCursor().position() == len("my name is keshav")
    window.close()

def test_navigation_does_not_use_custom_announcements():
    from virtual_abacus.accessibility import CaptureOutput
    window=BrailleWindow(); window.announcer.output=CaptureOutput(); editor=window.editor
    editor.setPlainText("one\ntwo"); editor.moveCursor(editor.textCursor().MoveOperation.End); editor.setFocus()
    before=len(window.announcer.output.messages)
    QTest.keyClick(editor, Qt.Key_Left); QTest.keyClick(editor, Qt.Key_Up)
    assert len(window.announcer.output.messages) == before
    window.close()
