from braille_input.engine import BrailleDocument

def test_number_sign_and_numeric_letters():
    d=BrailleDocument(); d.commit("3456"); assert d.cells[0].label=="number sign"
    cell=d.commit("1"); assert cell.meaning=="1" and cell.mode=="numeric"
