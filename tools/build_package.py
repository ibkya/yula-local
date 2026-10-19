"""Build dist/Yula-Windows.zip: only what the Windows user needs, never run data or captures."""
from pathlib import Path
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'dist/Yula-Windows.zip'
TOP = 'Yula/'

# Published path inside the zip -> source in the repository.
FILES = {
    'Yula.bat': 'windows/Yula.bat',
    'Kurulum.bat': 'windows/Kurulum.bat',
    'TESLIM.pdf': 'docs/TESLIM.pdf',
    'TESLIM.md': 'docs/TESLIM.md',
    'app/requirements-windows.txt': 'windows/requirements.txt',
    **{f'app/{name}': f'app/{name}' for name in (
        'core.py', 'desktop.py', 'ocr.py', 'panel.py', 'paths.py', 'runner.py', 'status.py', 'windows_setup.py')},
}


def main():
    missing = [source for source in FILES.values() if not (ROOT / source).is_file()]
    if missing:
        raise SystemExit(f'Eksik dosya: {missing} (TESLIM.pdf için: tools/make_pdf.py)')
    if (ROOT / 'docs/TESLIM.pdf').stat().st_mtime < (ROOT / 'docs/TESLIM.md').stat().st_mtime:
        raise SystemExit('TESLIM.pdf, TESLIM.md değiştikten sonra yeniden oluşturulmadı: tools/make_pdf.py')
    OUTPUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as archive:
        for published, source in FILES.items():
            archive.write(ROOT / source, TOP + published)
    with zipfile.ZipFile(OUTPUT) as archive:
        names = archive.namelist()
    assert not any(part in name for name in names for part in ('data/', '.json', '.png', 'mac/', 'tests/')), names
    print(OUTPUT)
    for name in names:
        print('  ' + name)
    print('SHA256', hashlib.sha256(OUTPUT.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
