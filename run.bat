@echo off
cd /d "%~dp0"
where pythonw.exe >nul 2>nul
if %ERRORLEVEL% EQU 0 (start "" pythonw.exe "%~dp0VirtualBraille.pyw" & exit /b 0)
start "" python.exe "%~dp0VirtualBraille.pyw"
