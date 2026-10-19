"""Platform adapters; screen coordinates are always relative to the foreground window."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from paths import TESSDATA, VISION


def enable_dpi():
    if sys.platform == 'win32':
        # Must precede PyAutoGUI import so screenshot pixels and input coordinates agree.
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))


def foreground_window():
    if sys.platform == 'darwin':
        data = subprocess.check_output([str(VISION), '--window'], text=True, timeout=5)
        return json.loads(data)
    if sys.platform != 'win32':
        raise RuntimeError('Yalnızca Windows ve macOS destekleniyor.')
    user = ctypes.windll.user32
    kernel = ctypes.windll.kernel32
    user.GetForegroundWindow.restype = wintypes.HWND
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    hwnd = user.GetForegroundWindow()
    pid = wintypes.DWORD()
    user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    process = kernel.OpenProcess(0x1000, False, pid.value)
    if not process:
        return None
    try:
        size = wintypes.DWORD(32768)
        name = ctypes.create_unicode_buffer(size.value)
        if not kernel.QueryFullProcessImageNameW(process, 0, name, ctypes.byref(size)):
            return None
    finally:
        kernel.CloseHandle(process)
    rect = wintypes.RECT()
    if not user.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    # GetWindowRect includes invisible resize borders; DWM gives the visible frame.
    dwm = ctypes.windll.dwmapi
    dwm.DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    dwm.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect))
    return {'app': Path(name.value).name.lower(), 'id': int(hwnd),
            'x': rect.left, 'y': rect.top,
            'width': rect.right - rect.left, 'height': rect.bottom - rect.top}


def is_browser(window, browser):
    expected = {'chrome': 'chrome.exe', 'safari': ''} if sys.platform == 'win32' else {
        'chrome': 'com.google.Chrome', 'safari': 'com.apple.Safari'}
    return bool(window and window['app'] == expected[browser])


def crop_window(image, window, screen_size):
    width, height = screen_size
    x, y, w, h = (window[k] for k in ('x', 'y', 'width', 'height'))
    if x < 0 or y < 0 or x + w > width + 1 or y + h > height + 1 or w < 700 or h < 500:
        raise RuntimeError('Tarayıcı penceresini tamamen ana ekrana taşı ve büyüt.')
    sx, sy = image.width / width, image.height / height
    return image.crop((round(x * sx), round(y * sy), round((x + w) * sx), round((y + h) * sy)))


def lock_file(file):
    if sys.platform == 'win32':
        import msvcrt
        file.seek(0)
        if not file.read(1):
            file.write(b'0')
            file.flush()
        file.seek(0)
        msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)


def tesseract_setup():
    import pytesseract
    local_data = TESSDATA
    if all((local_data / (lang + '.traineddata')).exists() for lang in ('tur', 'eng')):
        os.environ['TESSDATA_PREFIX'] = str(local_data)
    executable = shutil.which('tesseract')
    candidates = [Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Tesseract-OCR/tesseract.exe',
                  Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/Tesseract-OCR/tesseract.exe']
    if not executable:
        executable = next((str(p) for p in candidates if p.is_file()), None)
    if not executable:
        raise RuntimeError('Tesseract OCR bulunamadı. WINDOWS-KURULUM.md dosyasındaki kurulumu tamamla.')
    pytesseract.pytesseract.tesseract_cmd = executable
    languages = pytesseract.get_languages(config='')
    if 'tur' not in languages or 'eng' not in languages:
        raise RuntimeError('Tesseract Türkçe (tur) ve İngilizce (eng) dil dosyaları gerekli.')
    return pytesseract


def tesseract_words(data, width, height):
    words = []
    for i, text in enumerate(data['text']):
        confidence = float(data['conf'][i])
        if text.strip() and confidence >= 0:
            words.append({'text': text.strip(), 'confidence': confidence / 100,
                          'x': data['left'][i] / width, 'y': data['top'][i] / height,
                          'w': data['width'][i] / width, 'h': data['height'][i] / height})
    return words
