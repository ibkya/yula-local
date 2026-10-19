@echo off
rem Yula panelini acar. Ilk seferde kurulumu baslatir.
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv-win\Scripts\pythonw.exe" (
  call Kurulum.bat auto
  if errorlevel 1 exit /b 1
)
start "" ".venv-win\Scripts\pythonw.exe" app\panel.py
