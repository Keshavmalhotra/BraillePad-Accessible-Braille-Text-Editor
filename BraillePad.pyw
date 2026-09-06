"""Launch the wxPython Braille editor without opening a console window."""
from pathlib import Path
import os
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from braille_input.__main__ import BrailleApp
    BrailleApp(False).MainLoop()
except ModuleNotFoundError as error:
    # Windows may associate .pyw with a different Python installation than
    # the one used by run.bat. Relaunch through the Python 3.13 launcher when
    # that interpreter is missing wxPython.
    if error.name == "wx" and os.environ.get("BRAILLEPAD_RELAUNCHED") != "1":
        environment = os.environ.copy()
        environment["BRAILLEPAD_RELAUNCHED"] = "1"
        subprocess.Popen(["py", "-3.13", str(Path(__file__).resolve())], cwd=str(ROOT), env=environment)
    else:
        (ROOT / "BraillePad-startup-error.log").write_text(traceback.format_exc(), encoding="utf-8")
        raise
except Exception:
    (ROOT / "BraillePad-startup-error.log").write_text(traceback.format_exc(), encoding="utf-8")
    raise
