import sys
from pathlib import Path
_workspace = Path(__file__).resolve().parents[2]
_abacus = _workspace / "virtual_abacus"
if _abacus.exists() and str(_abacus) not in sys.path: sys.path.insert(0, str(_abacus))
from virtual_abacus.accessibility import AO2Output, CaptureOutput

class Announcer:
    def __init__(self, output=None): self.output=output or AO2Output()
    def send(self, text, interrupt=True): self.output.send(text, interrupt)
    def blank_line(self):
        # An empty line must replace any queued speech for the line the caret
        # just left.  Non-interrupting output can otherwise let AO2/NVDA
        # finish announcing the adjacent non-empty line.
        self.send("Blank line.", True)
    def composing(self, dots): self.send(f"Dots {' '.join(dots)}." if dots else "Braille cell empty.", False)
    def committed(self, cell): self.send(f"Dots {' '.join(cell.dots)}. {cell.meaning}.")
