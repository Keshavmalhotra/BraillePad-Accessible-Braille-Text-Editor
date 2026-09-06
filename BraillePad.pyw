"""Launch the wxPython Braille editor without opening a console window."""
from braille_input.__main__ import BrailleApp


BrailleApp(False).MainLoop()
