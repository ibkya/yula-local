@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv-win\Scripts\python.exe" (
  echo Once Windows-Kur.bat calistir.
  pause
  exit /b 1
)
echo Chrome'da oyunun Favoriler ekranini ac, 8 saniye icinde Chrome'a gec.
echo Bu kontrol tiklamaz veya asker gondermez.
echo Sonucu ve olusan kontrol-ekran.png dosyasini gelistiriciye gonderebilirsin.
".venv-win\Scripts\python.exe" automation\run.py --browser chrome
pause
