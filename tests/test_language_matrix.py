import pytest

from braille_input.tables import PROFILES, available_tables, canonical_cell


EXPECTED_FIRST = {
    "en": "a", "hi": "अ", "sa": "अ", "mr": "अ", "ne": "अ",
    "as": "অ", "bn": "অ", "gu": "અ", "pa": "ਅ", "kn": "ಅ",
    "ml": "അ", "or": "ଅ", "ta": "அ", "te": "అ", "ur": "ا",
}


def test_all_profiles_have_real_forward_tables_and_script_output():
    tables = available_tables()
    assert set(tables) == set(EXPECTED_FIRST) == set(PROFILES)
    for key, expected in EXPECTED_FIRST.items():
        assert tables[key].table.exists()
        assert tables[key].translate_sequence(("1",)) == expected


def test_canonical_cells_are_order_independent_and_unique():
    assert canonical_cell("1245") == "1245"
    assert canonical_cell("1425") == "1245"
    assert canonical_cell("5124") == "1245"


@pytest.mark.parametrize("value", ["7", "18", "abc", None])
def test_invalid_cells_are_rejected(value):
    with pytest.raises(ValueError):
        canonical_cell(value)


def test_hindi_matra_is_a_dependent_vowel_sign():
    table = available_tables()["hi"]
    assert table.translate_sequence(("13", "146", "1236")) == "कशव"
    assert table.translate_sequence(("13", "15", "146", "1236")) == "केशव"
    assert [f"U+{ord(c):04X}" for c in table.translate_sequence(("13", "15"))] == ["U+0915", "U+0947"]
