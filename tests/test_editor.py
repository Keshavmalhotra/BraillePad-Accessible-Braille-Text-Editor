import os
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
from braille_input.ui import BrailleWindow
from braille_input.ui import PHYSICAL_DOTS
from braille_input.tables import PROFILES

app = QApplication.instance() or QApplication([])

def test_braille_inserts_at_cursor_and_tab_is_not_a_dot():
    window=BrailleWindow(); editor=window.editor; editor.setFocus()
    QTest.keyClicks(editor, "fdjk"); QTest.keyClick(editor, Qt.Key_Space)
    assert editor.toPlainText() == "g"
    editor.setCursorPosition(0, 0) if False else None
    editor.moveCursor(editor.textCursor().MoveOperation.Start)
    QTest.keyClick(editor, Qt.Key_Tab)
    assert editor.toPlainText().startswith("\t")
    assert editor.composer.dots == ""
    window.close()


def test_fds_jkl_maps_to_internal_dot_numbers():
    assert PHYSICAL_DOTS == {"f": "1", "d": "2", "s": "3", "j": "4", "k": "5", "l": "6"}
    for physical in ("fdjk", "kjdf"):
        window = BrailleWindow(); editor = window.editor; editor.setFocus()
        QTest.keyClicks(editor, physical); QTest.keyClick(editor, Qt.Key_Space)
        assert window.document.cells[0].dots == "1245"
        assert editor.toPlainText() == "g"
        window.close()


def test_numeric_keys_are_not_braille_dot_input():
    window = BrailleWindow(); editor = window.editor; editor.setFocus()
    QTest.keyClicks(editor, "123456")
    assert editor.composer.dots == ""
    assert editor.toPlainText() == ""
    window.close()

def test_arrow_navigation_announces_destination_line():
    window=BrailleWindow(); window.editor.setPlainText("first line\nsecond line"); window.editor.moveCursor(window.editor.textCursor().MoveOperation.End)
    window.editor.setFocus(); QTest.keyClick(window.editor, Qt.Key_Up)
    assert window.editor.textCursor().blockNumber() == 0
    window.close()

def test_selection_braille_replaces_text_and_undo_redo():
    window=BrailleWindow(); editor=window.editor; editor.setPlainText("old text")
    cursor=editor.textCursor(); cursor.setPosition(0); cursor.setPosition(3, cursor.MoveMode.KeepAnchor); editor.setTextCursor(cursor)
    editor.setFocus(); QTest.keyClicks(editor, "fdjk"); QTest.keyClick(editor, Qt.Key_Space)
    assert editor.toPlainText() == "g text"
    editor.undo(); assert editor.toPlainText() == "old text"
    editor.redo(); assert editor.toPlainText() == "g text"
    window.close()

def test_tab_does_not_commit_composition():
    window=BrailleWindow(); editor=window.editor; editor.setFocus()
    QTest.keyClick(editor, Qt.Key_F); QTest.keyClick(editor, Qt.Key_Tab)
    assert editor.composer.dots == "1" and editor.toPlainText() == "\t"
    window.close()


def test_space_commit_and_real_space_are_language_independent():
    for language in PROFILES:
        window = BrailleWindow(); window.set_language(language)
        editor = window.editor; editor.setFocus()
        QTest.keyClicks(editor, "fs"); QTest.keyClick(editor, Qt.Key_Space)
        assert editor.toPlainText() == ("k" if language == "en" else
                                        window.document.table.translate_sequence(("13",)))
        assert editor.composer.dots == ""
        QTest.keyClick(editor, Qt.Key_Space)
        assert editor.toPlainText()[-1] == " "
        assert ord(editor.toPlainText()[-1]) == 0x20
        assert window.document.cells[-1].dots == ""
        window.close()


def test_hindi_k_plus_e_is_a_matra_sequence_in_editor():
    window = BrailleWindow(); window.set_language("hi")
    editor = window.editor; editor.setFocus()
    for dots in ("13", "15"):
        QTest.keyClicks(editor, {"13": "fs", "15": "fk"}[dots]); QTest.keyClick(editor, Qt.Key_Space)
    assert editor.toPlainText() == "\u0915\u0947"
    assert [f"U+{ord(c):04X}" for c in editor.toPlainText()] == ["U+0915", "U+0947"]
    window.close()


def test_punjabi_consonant_plus_vowel_is_a_sequence_in_editor():
    window = BrailleWindow(); window.set_language("pa")
    editor = window.editor; editor.setFocus()
    for dots in ("13", "15"):
        QTest.keyClicks(editor, {"13": "fs", "15": "fk"}[dots]); QTest.keyClick(editor, Qt.Key_Space)
    assert editor.toPlainText() == "\u0a15\u0a47"  # ਕੇ
    assert [f"U+{ord(c):04X}" for c in editor.toPlainText()] == ["U+0A15", "U+0A47"]
    window.close()


def test_enter_creates_native_newline_and_commits_unfinished_cell():
    window = BrailleWindow(); editor = window.editor; editor.setFocus()
    QTest.keyClicks(editor, "f"); QTest.keyClick(editor, Qt.Key_Return)
    assert editor.toPlainText() == "a\n"
    assert editor.textCursor().position() == 2
    assert editor.toPlainText().encode("unicode_escape") == b"a\\n"
    window.close()


def test_enter_on_empty_editor_creates_blank_lines():
    window = BrailleWindow(); editor = window.editor; editor.setFocus()
    QTest.keyClick(editor, Qt.Key_Return)
    QTest.keyClick(editor, Qt.Key_Return)
    assert editor.toPlainText() == "\n\n"
    assert editor.document().blockCount() == 3
    assert editor.textCursor().position() == 2
    window.close()


def test_enter_moves_caret_to_a_new_native_empty_block():
    window = BrailleWindow(); editor = window.editor; editor.setPlainText("A\nB")
    cursor = editor.textCursor(); cursor.setPosition(1); editor.setTextCursor(cursor); editor.setFocus()
    QTest.keyClick(editor, Qt.Key_Return)
    assert editor.toPlainText() == "A\n\nB"
    assert editor.textCursor().position() == 2
    assert editor.textCursor().blockNumber() == 1
    assert editor.textCursor().block().text() == ""
    assert [block.text() for block in iter_blocks(editor)] == ["A", "", "B"]
    QTest.keyClick(editor, Qt.Key_Return)
    assert editor.toPlainText() == "A\n\n\nB"
    assert editor.textCursor().blockNumber() == 2
    window.close()


def test_native_navigation_visits_each_empty_block():
    window = BrailleWindow(); editor = window.editor; editor.setPlainText("A\n\nB"); editor.moveCursor(editor.textCursor().MoveOperation.Start); editor.setFocus()
    QTest.keyClick(editor, Qt.Key_Down)
    assert editor.textCursor().blockNumber() == 1 and editor.textCursor().block().text() == ""
    QTest.keyClick(editor, Qt.Key_Down)
    assert editor.textCursor().blockNumber() == 2 and editor.textCursor().block().text() == "B"
    QTest.keyClick(editor, Qt.Key_Up)
    assert editor.textCursor().blockNumber() == 1 and editor.textCursor().block().text() == ""
    window.close()


def test_many_enters_are_not_collapsed():
    window = BrailleWindow(); editor = window.editor; editor.setFocus()
    for _ in range(100): QTest.keyClick(editor, Qt.Key_Return)
    assert editor.toPlainText() == "\n" * 100
    assert editor.document().blockCount() == 101
    window.close()


def test_four_empty_lines_are_real_immediately_and_navigable():
    """Enter creates model lines even when no character follows it."""
    window = BrailleWindow(); editor = window.editor; editor.setFocus()
    editor.setPlainText("A")
    editor.moveCursor(editor.textCursor().MoveOperation.End)

    for _ in range(4):
        QTest.keyClick(editor, Qt.Key_Return)

    assert editor.toPlainText() == "A\n\n\n\n"
    assert editor.document().blockCount() == 5
    assert editor.textCursor().position() == len("A\n\n\n\n")
    assert editor.textCursor().blockNumber() == 4
    assert editor.textCursor().block().text() == ""

    # The native document, rather than a visual placeholder, owns the lines.
    assert [block.text() for block in iter_blocks(editor)] == ["A", "", "", "", ""]

    for expected in (3, 2, 1, 0):
        QTest.keyClick(editor, Qt.Key_Up)
        assert editor.textCursor().blockNumber() == expected
        assert editor.textCursor().block().text() == ("" if expected else "A")
    for expected in (1, 2, 3, 4):
        QTest.keyClick(editor, Qt.Key_Down)
        assert editor.textCursor().blockNumber() == expected

    # Saving the text preserves all four line boundaries, including trailing
    # empty blocks; no later character is needed to make them persistent.
    path = Path("four_empty_lines.txt").resolve()
    window.path = path; window.save_document()
    assert path.read_text(encoding="utf-8") == "A\n\n\n\n"
    path.unlink(missing_ok=True)
    window.close()


def test_enter_space_backspace_and_delete_are_native_editor_operations():
    window = BrailleWindow(); editor = window.editor; editor.setFocus()
    QTest.keyClicks(editor, "f"); QTest.keyClick(editor, Qt.Key_Space)
    QTest.keyClick(editor, Qt.Key_Space)
    QTest.keyClicks(editor, "f"); QTest.keyClick(editor, Qt.Key_Return)
    QTest.keyClicks(editor, "f")
    QTest.keyClick(editor, Qt.Key_Space)
    assert editor.toPlainText() == "a a\na"

    editor.moveCursor(editor.textCursor().MoveOperation.StartOfLine)
    QTest.keyClick(editor, Qt.Key_Backspace)
    assert editor.toPlainText() == "a aa"

    editor.setPlainText("a\nb")
    cursor = editor.textCursor(); cursor.movePosition(cursor.MoveOperation.StartOfLine); cursor.movePosition(cursor.MoveOperation.EndOfLine); editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key_Delete)
    assert editor.toPlainText() == "ab"
    window.close()


def test_multiline_navigation_and_text_save_preserve_real_lines():
    window = BrailleWindow(); editor = window.editor
    editor.setPlainText("Line 1\nLine 2\nLine 3")
    editor.moveCursor(editor.textCursor().MoveOperation.End)
    QTest.keyClick(editor, Qt.Key_Up)
    assert editor.textCursor().blockNumber() == 1
    QTest.keyClick(editor, Qt.Key_Home)
    assert editor.textCursor().positionInBlock() == 0
    QTest.keyClick(editor, Qt.Key_Down)
    assert editor.textCursor().blockNumber() == 2

    path = Path("multiline_test_output.txt").resolve()
    window.path = path
    window.save_document()
    saved = path.read_bytes()
    assert saved.count(b"\n") == 2
    assert saved.replace(b"\r\n", b"\n") == b"Line 1\nLine 2\nLine 3"
    path.unlink(missing_ok=True)
    window.close()


def test_enter_has_identical_editor_structure_for_all_languages():
    for language in PROFILES:
        window = BrailleWindow(); window.set_language(language)
        editor = window.editor; editor.setFocus()
        QTest.keyClicks(editor, "f"); QTest.keyClick(editor, Qt.Key_Return)
        QTest.keyClicks(editor, "d"); QTest.keyClick(editor, Qt.Key_Return)
        assert editor.toPlainText().count("\n") == 2
        assert [block.text() for block in iter_blocks(editor)] == [
            window.document.table.translate_sequence(("1",)),
            window.document.table.translate_sequence(("2",)),
            "",
        ]
        window.close()


def iter_blocks(editor):
    block = editor.document().begin()
    while block.isValid():
        yield block
        block = block.next()

def test_alphabetic_and_punctuation_keys_do_not_insert_direct_text():
    window=BrailleWindow(); editor=window.editor; editor.setFocus()
    QTest.keyClicks(editor, "keshav!")
    assert editor.toPlainText() == ""
    editor.composer.clear()
    QTest.keyClicks(editor, "fdjk"); QTest.keyClick(editor, Qt.Key_Space)
    assert editor.toPlainText() == "g"
    window.close()

def _enter_cell(editor, dots):
    physical = str.maketrans("123456", "fdsjkl")
    QTest.keyClicks(editor, dots.translate(physical))
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


def test_blank_line_fallback_reports_actual_empty_block_only():
    from virtual_abacus.accessibility import CaptureOutput
    window = BrailleWindow(); window.announcer.output = CaptureOutput()
    editor = window.editor; editor.setPlainText("Line 1\n\nLine 2"); editor.setFocus()
    editor.moveCursor(editor.textCursor().MoveOperation.Start)
    window.announcer.output.messages.clear()

    QTest.keyClick(editor, Qt.Key_Down)
    assert editor.textCursor().blockNumber() == 1
    assert editor.textCursor().block().text() == ""
    assert [m for m in window.announcer.output.messages if "blank line" in m.lower()] == ["Blank line."]
    assert "Line 1" not in window.announcer.output.messages
    assert "Line 2" not in window.announcer.output.messages

    # Repeated cursor notifications on the same empty block do not duplicate.
    window._cursor_changed(); window._cursor_changed()
    assert [m for m in window.announcer.output.messages if "blank line" in m.lower()] == ["Blank line."]
    QTest.keyClick(editor, Qt.Key_Down)
    assert editor.textCursor().blockNumber() == 2
    assert [m for m in window.announcer.output.messages if "blank line" in m.lower()] == ["Blank line."]
    assert "blank line" not in editor.toPlainText().lower()
    window.close()


def test_accessibility_follows_caret_through_consecutive_empty_blocks():
    from virtual_abacus.accessibility import CaptureOutput
    window = BrailleWindow(); window.announcer.output = CaptureOutput()
    editor = window.editor; editor.setPlainText("FIRST\n\n\nSECOND")
    editor.moveCursor(editor.textCursor().MoveOperation.Start)
    window.announcer.output.messages.clear()

    # Each Down lands on the next native QTextBlock, including both empties.
    QTest.keyClick(editor, Qt.Key_Down)
    assert editor.textCursor().blockNumber() == 1
    assert editor.textCursor().block().text() == ""
    QTest.keyClick(editor, Qt.Key_Down)
    assert editor.textCursor().blockNumber() == 2
    assert editor.textCursor().block().text() == ""
    assert [m for m in window.announcer.output.messages if "blank line" in m.lower()] == [
        "Blank line.", "Blank line."
    ]
    assert all("FIRST" not in m and "SECOND" not in m for m in window.announcer.output.messages)

    # Reverse navigation returns through the same actual empty blocks.
    QTest.keyClick(editor, Qt.Key_Up)
    assert editor.textCursor().blockNumber() == 1
    QTest.keyClick(editor, Qt.Key_Up)
    assert editor.textCursor().blockNumber() == 0
    assert editor.textCursor().block().text() == "FIRST"
    assert [m for m in window.announcer.output.messages if "blank line" in m.lower()] == [
        "Blank line.", "Blank line.", "Blank line."
    ]
    window.close()


def test_wrapping_is_disabled_and_vertical_navigation_stops_at_boundaries():
    window = BrailleWindow(); editor = window.editor; editor.setFocus()
    editor.setPlainText("A\nB\nC")
    assert editor.lineWrapMode() == editor.LineWrapMode.NoWrap

    editor.moveCursor(editor.textCursor().MoveOperation.End)
    bottom = editor.textCursor().position()
    QTest.keyClick(editor, Qt.Key_Down)
    assert editor.textCursor().position() == bottom
    assert editor.textCursor().blockNumber() == 2

    editor.moveCursor(editor.textCursor().MoveOperation.Start)
    top = editor.textCursor().position()
    QTest.keyClick(editor, Qt.Key_Up)
    assert editor.textCursor().position() == top
    assert editor.textCursor().blockNumber() == 0
    window.close()


def test_long_line_remains_one_logical_line_and_empty_lines_are_not_skipped():
    window = BrailleWindow(); editor = window.editor; editor.setFocus()
    long_line = "x" * 1000
    editor.setPlainText(f"A\n\n\n{long_line}")
    assert editor.lineWrapMode() == editor.LineWrapMode.NoWrap
    assert editor.document().blockCount() == 4

    editor.moveCursor(editor.textCursor().MoveOperation.Start)
    for expected in (1, 2, 3):
        QTest.keyClick(editor, Qt.Key_Down)
        assert editor.textCursor().blockNumber() == expected
    QTest.keyClick(editor, Qt.Key_Down)
    assert editor.textCursor().blockNumber() == 3
    assert editor.document().blockCount() == 4
    assert editor.textCursor().block().text() == long_line
    window.close()


def test_arrow_navigation_never_uses_wrapped_fragments():
    window = BrailleWindow(); editor = window.editor; editor.setFocus()
    long_line = "x" * 5000
    editor.setPlainText(long_line + "\nEND")
    assert editor.lineWrapMode() == editor.LineWrapMode.NoWrap
    assert editor.wordWrapMode() == QTextOption.WrapMode.NoWrap

    editor.moveCursor(editor.textCursor().MoveOperation.Start)
    QTest.keyClick(editor, Qt.Key_Down)
    assert editor.textCursor().blockNumber() == 1
    QTest.keyClick(editor, Qt.Key_Up)
    assert editor.textCursor().blockNumber() == 0
    assert editor.textCursor().positionInBlock() == 0
    window.close()


def test_caret_and_accessibility_range_follow_each_logical_line():
    window = BrailleWindow(); editor = window.editor; editor.setFocus()
    editor.setPlainText("Alpha\n\nBeta")
    editor.moveCursor(editor.textCursor().MoveOperation.Start)

    trace = []
    for key in (None, Qt.Key_Down, Qt.Key_Down, Qt.Key_Up, Qt.Key_Up):
        if key is not None:
            QTest.keyClick(editor, key)
        cursor = editor.textCursor()
        start, end, caret = editor.accessibility_line_range()
        trace.append((cursor.position(), cursor.blockNumber(), cursor.block().text(),
                      start, end, caret))

    assert trace == [
        (0, 0, "Alpha", 0, 5, 0),
        (6, 1, "", 6, 6, 6),
        (7, 2, "Beta", 7, 11, 7),
        (6, 1, "", 6, 6, 6),
        (0, 0, "Alpha", 0, 5, 0),
    ]
    window.close()


def test_regression_three_blank_lines_and_text_round_trip():
    """The A, Enter, Enter, Enter, B workflow keeps every line break."""
    window = BrailleWindow(); editor = window.editor; editor.setFocus()
    editor.setPlainText("A")
    editor.moveCursor(editor.textCursor().MoveOperation.End)
    for _ in range(3):
        QTest.keyClick(editor, Qt.Key_Return)
    editor.insertPlainText("B")

    assert editor.toPlainText() == "A\n\n\nB"
    assert [block.text() for block in iter_blocks(editor)] == ["A", "", "", "B"]

    path = Path("three_blank_lines.txt").resolve()
    window.path = path; window.save_document()
    assert path.read_text(encoding="utf-8") == "A\n\n\nB"
    path.unlink(missing_ok=True)
    window.close()
