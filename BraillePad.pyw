"""Launch the wxPython Braille editor without opening a console window."""
from pathlib import Path
import os
import sys
import traceback

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from braille_input.__main__ import BrailleApp
    BrailleApp(False).MainLoop()
except Exception:
    (ROOT / "BraillePad-startup-error.log").write_text(traceback.format_exc(), encoding="utf-8")
    raise
