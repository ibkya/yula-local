"""Download OCR language data from the official, versioned tessdata repository."""
import sys
import urllib.request


def main():
    if sys.platform != 'win32':
        raise RuntimeError('Bu kurulum yalnızca Windows içindir.')
    from paths import TESSDATA as target
    target.mkdir(exist_ok=True)
    for language in ('tur', 'eng'):
        file = target / (language + '.traineddata')
        if file.exists() and file.stat().st_size > 100000:
            continue
        url = f'https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0/{language}.traineddata'
        print(f'OCR dili indiriliyor: {language}', flush=True)
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read(20000000)
        if len(data) < 100000 or data.startswith(b'<'):
            raise RuntimeError('Dil verisi indirilemedi; kurulum tamamlanmadı.')
        temporary = file.with_suffix('.tmp')
        temporary.write_bytes(data)
        temporary.replace(file)
    from desktop import tesseract_setup
    tesseract_setup()
    import tkinter  # noqa: F401  (the panel needs it; fail setup early if missing)
    print('Python, OCR, Türkçe/İngilizce ve durum penceresi hazır.')


if __name__ == '__main__':
    main()
