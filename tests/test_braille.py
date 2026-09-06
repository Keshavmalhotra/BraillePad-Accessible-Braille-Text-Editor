from braille_input.engine import CellComposer, BrailleDocument

def test_order_and_duplicates():
    c=CellComposer()
    for x in "54211": assert c.add(x)
    assert c.dots=="1245"
def test_translation_and_preservation():
    d=BrailleDocument(); cell=d.commit("5421")
    assert cell.dots=="1245" and cell.meaning=="g" and d.text=="g"
def test_invalid_and_backspace():
    c=CellComposer(); assert not c.add("7")
    for dot in "1245": c.add(dot)
    c.remove_last(); assert c.dots=="124"
def test_words_and_round_trip():
    d=BrailleDocument(); d.commit("1"); d.space(); d.commit("12"); restored=BrailleDocument.from_snapshot(d.snapshot())
    assert restored.text=="a b" and [c.dots for c in restored.cells]==["1","","12"]
def test_accessibility_capture():
    from virtual_abacus.accessibility import CaptureOutput
    from braille_input.accessibility import Announcer
    cap=CaptureOutput(); Announcer(cap).committed(BrailleDocument().commit("1245")); assert "g" in cap.messages[-1]

def test_ueb_indicators_are_not_printed_and_are_stateful():
    d=BrailleDocument(); d.commit("6"); d.commit("1")
    assert d.text == "A"
    d=BrailleDocument(); d.commit("3456"); d.commit("1"); d.space(); d.commit("12")
    assert d.text == "1 b"
