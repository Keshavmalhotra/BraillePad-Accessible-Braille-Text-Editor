from braille_input.engine import BrailleDocument
from braille_input.tables import available_tables


def test_hindi_matras_are_translated_as_a_sequence():
    # These cells are obtained from the bundled Bharati/Liblouis table's
    # forward translation of "केशव": 13 15 146 1236.
    d = BrailleDocument(available_tables()["hi"])
    for dots in ("13", "15", "146", "1236"):
        d.commit(dots)
    assert d.text == "केशव"
    assert [f"U+{ord(c):04X}" for c in d.text] == ["U+0915", "U+0947", "U+0936", "U+0935"]


def test_hindi_word_boundary_does_not_split_sequences():
    d = BrailleDocument(available_tables()["hi"])
    for dots in ("13", "15", "146", "1236"):
        d.commit(dots)
    d.space()
    assert d.text == "केशव "


def test_indian_tables_produce_script_unicode_not_latin():
    expected = {"hi": "अ", "pa": "ਅ", "bn": "অ", "gu": "અ", "ta": "அ", "te": "అ", "kn": "ಅ", "ml": "അ", "or": "ଅ", "ur": "ا"}
    tables = available_tables()
    for key, character in expected.items():
        assert tables[key].translate("1").text == character
