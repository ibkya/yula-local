"""Build a source distribution without credentials, captures or run state."""
from pathlib import Path
import hashlib
import zipfile
root = Path(__file__).resolve().parent.parent
files = ['Windows-Kur.bat', 'Windows-Baslat.bat', 'Windows-Kontrol.bat', 'Windows-Durum.bat', 'WINDOWS-KURULUM.md', 'TEST-RAPORU.md', 'automation/core.py', 'automation/desktop.py', 'automation/run.py', 'automation/status.py', 'automation/status_window.py', 'automation/windows_setup.py', 'automation/requirements-windows.txt', 'automation/build_package.py', 'tests/test_automation.py']
output = root / 'dist/Yula-Windows-Chrome.zip'
output.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name in files:
        archive.write(root / name, 'yula-windows/' + name)
print(output)
print('SHA256', hashlib.sha256(output.read_bytes()).hexdigest())
