@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo  YULA KURULUMU
echo  Python 3.12, Tesseract OCR ve Turkce/Ingilizce dil dosyalari kurulacak.
echo  Internet gerekli. Windows izin veya lisans sorarsa "Evet" / "Y" ile devam et.
echo ============================================================
set "YULA_PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if exist "%YULA_PY%" goto python_ready
if exist "%ProgramFiles%\Python312\python.exe" (
  set "YULA_PY=%ProgramFiles%\Python312\python.exe"
  goto python_ready
)
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
  set "YULA_PY=py -3.12"
  goto python_launcher
)
where winget >nul 2>&1
if errorlevel 1 goto no_winget
winget install --id Python.Python.3.12 --exact --source winget
if errorlevel 1 goto fail
if exist "%YULA_PY%" goto python_ready
if exist "%ProgramFiles%\Python312\python.exe" (
  set "YULA_PY=%ProgramFiles%\Python312\python.exe"
  goto python_ready
)
py -3.12 --version >nul 2>&1
if errorlevel 1 goto fail
:python_launcher
py -3.12 -m venv .venv-win
if errorlevel 1 goto fail
goto packages
:python_ready
"%YULA_PY%" -m venv .venv-win
if errorlevel 1 goto fail
:packages
".venv-win\Scripts\python.exe" -m pip install -r app\requirements-windows.txt
if errorlevel 1 goto fail
if exist "%ProgramFiles%\Tesseract-OCR\tesseract.exe" goto languages
if exist "%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe" goto languages
where tesseract >nul 2>&1
if not errorlevel 1 goto languages
where winget >nul 2>&1
if errorlevel 1 goto no_winget
winget install --id tesseract-ocr.tesseract --exact --source winget
if errorlevel 1 goto fail
:languages
".venv-win\Scripts\python.exe" app\windows_setup.py
if errorlevel 1 goto fail
rem Masaustune "Yula" kisayolu: paneli acar.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Yula.lnk'); $s.TargetPath='%~dp0Yula.bat'; $s.WorkingDirectory='%~dp0'; $s.WindowStyle=7; $s.IconLocation='%~dp0.venv-win\Scripts\pythonw.exe,0'; $s.Save()" >nul 2>&1
echo.
echo KURULUM TAMAMLANDI. Masaustundeki "Yula" kisayolu ile paneli acabilirsin.
if /i not "%~1"=="auto" pause
exit /b 0
:no_winget
echo Windows App Installer / winget bulunamadi. Microsoft Store'dan App Installer kurun.
echo Sonra ayni dosyayi tekrar acin. Ayrinti: TESLIM.pdf, "Sorun cikarsa" bolumu.
:fail
echo KURULUM TAMAMLANMADI. Yukaridaki hata giderilmeden gonderim baslatilmayacak.
pause
exit /b 1
