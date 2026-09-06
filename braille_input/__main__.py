import sys
from PySide6.QtWidgets import QApplication
from .ui import BrailleWindow
app=QApplication(sys.argv); w=BrailleWindow(); w.show(); sys.exit(app.exec())
