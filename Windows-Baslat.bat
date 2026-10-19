@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv-win\Scripts\python.exe" (
  call Windows-Kur.bat auto
  if errorlevel 1 exit /b 1
)
".venv-win\Scripts\python.exe" automation\windows_setup.py
if errorlevel 1 (
  echo Kurulum kontrolu basarisiz. Windows-Kur.bat dosyasini calistirin.
  pause
  exit /b 1
)
echo CANLI MOD: Her hedefe 100 Okcu. Durdurmak icin Ctrl+C.
echo 8 saniye icinde Chrome'da Favoriler ekranina gec.
if exist automation-state.json (
  ".venv-win\Scripts\python.exe" automation\run.py --browser chrome --live --repeat --status-window --resume
) else (
  ".venv-win\Scripts\python.exe" automation\run.py --browser chrome --live --repeat --status-window
)
pause
