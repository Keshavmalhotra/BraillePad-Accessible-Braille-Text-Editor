@echo off
cd /d "%~dp0"
py -3.13 -c "import wx" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
  echo wxPython is not installed in Python 3.13.
  echo Install it with: py -3.13 -m pip install wxPython
  pause
  exit /b 1
)
start "" py -3.13 "%~dp0BraillePad.pyw"
