import wx
from .ui import BrailleWindow


class BrailleApp(wx.App):
    def OnInit(self):
        self.window = BrailleWindow()
        self.window.Show()
        return True


if __name__ == "__main__":
    BrailleApp(False).MainLoop()
