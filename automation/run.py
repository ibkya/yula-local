#!/usr/bin/env python3
"""Windows/Chrome and macOS desktop runner. Never solves CAPTCHA."""
import argparse
import atexit
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
import time

from core import Engine, Screen, norm
from status import Reporter, CONTROL
from desktop import enable_dpi, foreground_window, is_browser, crop_window, lock_file, tesseract_setup, tesseract_words

ROOT = Path(__file__).resolve().parent.parent
VISION = ROOT / '.build/yula-vision'
STATE = ROOT / 'automation-state.json'


def check_stop():
    if active_reporter is None:
        return
    try:
        command = json.loads(CONTROL.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return
    if (command.get('pid') == active_reporter.data['pid']
            and command.get('started') == active_reporter.data['started']
            and command.get('action') == 'stop'):
        raise KeyboardInterrupt


def save(state):
    temporary = STATE.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(STATE)


def ocr(image, tesseract=None):
    from PIL import ImageEnhance, ImageOps
    original_image = image
    # Upscale small UI lettering for Vision. Coordinates stay normalized.
    factor = 2 if image.width < 4000 and not tesseract else 1
    image = ImageEnhance.Contrast(image.resize((image.width * factor, image.height * factor))).enhance(1.25)
    words = read_words(image, tesseract)
    if tesseract:
        # Tesseract depends on letter size (DPI, Retina, window size), not on screen
        # width. Re-read with ~11 px letters (lists) and ~16 px letters (troop cards).
        heights = sorted(w['h'] * image.height for w in words
                         if w['confidence'] > .8 and len(w['text']) >= 3 and w['text'].isalpha())
        if heights:
            median = heights[len(heights) // 2]
            merge(words, read_words(image, tesseract, [s for s in (11 / median, 16 / median) if abs(s - 1) > .15]))
    screen = Screen(words)
    if 'yulaonline.com' not in screen.text:
        # On 1x monitors the small address bar text is lost; re-read the toolbar enlarged.
        strip = original_image.crop((0, 0, original_image.width, round(original_image.height * .1)))
        share = strip.height / original_image.height
        for w in read_words(strip.resize((strip.width * 3, strip.height * 3)), tesseract):
            if 'yulaonline.com' in norm(w['text']):
                words.append(dict(w, y=w['y'] * share, h=w['h'] * share))
        screen = Screen(words)
    # Whole-screen OCR drops isolated row numbers, especially near the bottom.
    # Read each visible list row separately; derive regions from current labels.
    if not screen.captcha and 'favorileri' in screen.text:
        tabs = screen.tabs()
        headers = [w for w in screen.find('yagma') if any(norm(t.text) == 'favorileri' for t in screen.line(w))]
        if tabs or headers:
            edge = min(w.x for w in tabs + headers)
            raids = [w for w in screen.raids() if w.cy > max(t.cy for t in tabs + headers)]
            for raid in raids:
                gap = min([abs(raid.cy - other.cy) for other in raids if other is not raid] or [.05])
                top, bottom = max(0, raid.cy - gap * .44), min(1, raid.cy + gap * .44)
                right = min(1, raid.x + raid.w * 1.5)
                box = (round(edge * image.width), round(top * image.height),
                       round(right * image.width), round(bottom * image.height))
                crop = image.crop(box)
                scale = max(1, min(4, 2200 / crop.width))
                detail = read_words(crop.resize((round(crop.width * scale), round(crop.height * scale))), tesseract)
                if not detail:
                    continue
                left, top, right, bottom = box[0]/image.width, box[1]/image.height, box[2]/image.width, box[3]/image.height
                for w in detail:
                    w.update(x=left+w['x']*(right-left), y=top+w['y']*(bottom-top),
                             w=w['w']*(right-left), h=w['h']*(bottom-top))
                # Retain successful whole-screen reads; fill only missing tokens.
                merge(words, detail)
            screen = Screen(words)
            if tesseract and raids:
                # Tesseract skips lone digits in a page. Read each number cell as digits
                # only; Screen.rows() outvotes the occasional misread by row order.
                span = min(r.x for r in raids) - edge
                gap = min([abs(a.cy-b.cy) for a in raids for b in raids if a is not b] or [.05])
                boxes = [(round(edge * image.width), round((r.cy - gap * .25) * image.height),
                          round((edge + span * .24) * image.width), round((r.cy + gap * .25) * image.height))
                         for r in raids]
                with ThreadPoolExecutor(4) as pool:
                    texts = list(pool.map(lambda box: read_digits(image.crop(box), tesseract), boxes))
                for raid, text in zip(raids, texts):
                    if not text or not 1 <= int(text) <= 200:
                        continue
                    known = [w for w in screen.line(raid) if w.text.isdigit()
                             and edge + span * .025 < w.x < edge + span * .24]
                    x = known[0].x if known else edge + span * .1
                    words.append({'text': text, 'x': x, 'y': raid.y, 'w': span * .03,
                                  'h': raid.h, 'confidence': .9})
                screen = Screen(words)
                # The gold "yolda N" send counter is lost in a page read. Read the cell
                # between the X | Y pair and the Git button on its own.
                cells = []
                for raid in raids:
                    line = [w for w in screen.line(raid) if w.x < raid.x]
                    ends = [b.x + b.w for a, b in zip(line, line[1:]) if a.text in ('|', '/') and b.text.isdigit()]
                    if re.search(r'yolda\s*\d+', norm(' '.join(w.text for w in line))) or not ends:
                        continue
                    gits = [w for w in line if norm(w.text) == 'git' and w.x > max(ends)]
                    right = min(w.x for w in gits) if gits else raid.x - raid.w * 1.3
                    if right - max(ends) > raid.w * .5:
                        cells.append((raid, max(ends), right))
                with ThreadPoolExecutor(4) as pool:
                    texts = list(pool.map(lambda cell: read_line(image.crop(
                        (round(cell[1] * image.width), round((cell[0].cy - cell[0].h) * image.height),
                         round(cell[2] * image.width), round((cell[0].cy + cell[0].h) * image.height))), tesseract), cells))
                for (raid, left, right), text in zip(cells, texts):
                    moving = re.search(r'yolda\s*(\d+)', norm(text))
                    if moving:
                        step = (right - left) / 4
                        words += [{'text': 'yolda', 'x': left + step * .3, 'y': raid.y, 'w': step * 1.5,
                                   'h': raid.h, 'confidence': .9},
                                  {'text': moving.group(1), 'x': left + step * 2.2, 'y': raid.y, 'w': step * .4,
                                   'h': raid.h, 'confidence': .9}]
                screen = Screen(words)
            # A narrow column pass recovers digits ignored in full-screen OCR.
            if raids:
                span = min(r.x for r in raids) - edge
                gap = min([abs(a.cy-b.cy) for a in raids for b in raids if a is not b] or [.05])
                indices = [w for w in screen.words if w.text.isdigit()
                           and edge+span*.025 < w.x < edge+span*.24
                           and min(r.cy for r in raids)-gap*.4 < w.cy < max(r.cy for r in raids)+gap*.4]
                if not indices:
                    return screen
                digit_width = max(w.w/len(w.text) for w in indices)
                column_left = min(w.x for w in indices) - digit_width*2
                column_right = max(w.x+w.w for w in indices) + digit_width*.3
                box = (round(column_left*image.width), round((min(r.cy for r in raids)-gap*.5)*image.height),
                       round(column_right*image.width), round((max(r.cy for r in raids)+gap*.5)*image.height))
                raw_box = tuple(round(v / factor) for v in box)
                crop = original_image.crop(raw_box)
                enlarged = crop.resize((crop.width*4, crop.height*4))
                column_words = read_words(enlarged, tesseract)
                column_words += read_words(ImageOps.invert(ImageOps.autocontrast(enlarged.convert('L'))), tesseract)
                for w in column_words:
                    if not w['text'].isdigit() or not 1 <= int(w['text']) <= 200:
                        continue
                    w.update(x=(box[0]+w['x']*(box[2]-box[0]))/image.width,
                             y=(box[1]+w['y']*(box[3]-box[1]))/image.height,
                             w=w['w']*(box[2]-box[0])/image.width, h=w['h']*(box[3]-box[1])/image.height)
                    if not any(old['text']==w['text'] and abs(old['x']-w['x'])<w['w']*2
                               and abs(old['y']-w['y'])<w['h'] for old in words):
                        words.append(w)
            screen = Screen(words)
    if screen.kind == 'selection':
        pluses = screen.find('+100')
        if len(pluses) >= 2:
            left = max(0, min(w.cx for w in pluses) - .045)
            right = min(1, max(w.cx for w in pluses) + .045)
            top = max(0, min(w.cy for w in pluses) - .17)
            bottom = min(1, max(w.cy for w in pluses) + .025)
            box = tuple(round(v * size) for v, size in
                        zip((left, top, right, bottom), (image.width, image.height) * 2))
            # Isolated cards keep Vision/Tesseract from dropping small zero quantities.
            detail = read_words(image.crop(box), tesseract)
            left, top, right, bottom = box[0] / image.width, box[1] / image.height, box[2] / image.width, box[3] / image.height
            for w in detail:
                w.update(x=left + w['x'] * (right - left), y=top + w['y'] * (bottom - top),
                         w=w['w'] * (right - left), h=w['h'] * (bottom - top))
            for candidate in detail:
                duplicates = [w for w in words if norm(w['text']) == norm(candidate['text'])
                              and abs(w['x']+w['w']/2-candidate['x']-candidate['w']/2) < max(w['w'],candidate['w'])
                              and abs(w['y']+w['h']/2-candidate['y']-candidate['h']/2) < max(w['h'],candidate['h'])*.8]
                if duplicates:
                    for w in duplicates:
                        w['confidence'] = max(w.get('confidence', 1), candidate.get('confidence', 1))
                else:
                    words.append(candidate)
            screen = Screen(words)
    if tesseract and screen.kind == 'selection' and screen.find('+100'):
        # Tamam/Vazgeç sit on red and dark plates that Tesseract misses in a page
        # read. Binarize the button row at several thresholds and merge the reads.
        bottom = max(w.cy for w in screen.find('+100'))
        top, low = bottom + .015, min(1, bottom + .1)
        band = image.crop((0, round(top * image.height), image.width, round(low * image.height)))
        with ThreadPoolExecutor(4) as pool:
            reads = list(pool.map(lambda threshold: read_binarized(band, tesseract, threshold), (80, 110, 140, 170)))
        for detail in reads:
            # Only the two button labels: binarized digits are less reliable than the page read.
            merge(words, [dict(w, y=top + w['y'] * (low - top), h=w['h'] * (low - top)) for w in detail
                          if norm(w['text']).strip('.,:;[]|() ') in ('tamam', 'vazgec')])
        screen = Screen(words)
    return screen


def read_line(image, tesseract):
    from PIL import Image, ImageOps
    page = ImageOps.invert(ImageOps.autocontrast(image.convert('L')))
    page = page.resize((page.width * 2, page.height * 2), Image.LANCZOS)
    return tesseract.image_to_string(page, lang='tur+eng', config='--psm 7', timeout=10)


def read_binarized(image, tesseract, threshold):
    from PIL import Image, ImageOps
    page = ImageOps.invert(ImageOps.autocontrast(image.convert('L')))
    page = page.resize((page.width * 2, page.height * 2), Image.LANCZOS).point(lambda v: 0 if v < threshold else 255)
    data = tesseract.image_to_data(page, lang='tur+eng', config='--psm 11',
                                  output_type=tesseract.Output.DICT, timeout=20)
    return tesseract_words(data, page.width, page.height)


def same_word(a, b):
    # 'Konum' and 'Konum:' from two passes are the same label.
    return (norm(a['text']).strip('.,:;[]|() ') == norm(b['text']).strip('.,:;[]|() ')
            and abs(a['x'] + a['w']/2 - b['x'] - b['w']/2) < max(a['w'], b['w'])
            and abs(a['y'] + a['h']/2 - b['y'] - b['h']/2) < max(a['h'], b['h'])*.8)


def merge(words, extra):
    for candidate in extra:
        if not any(same_word(w, candidate) for w in words):
            words.append(candidate)
    return words


def read_digits(image, tesseract):
    from PIL import Image, ImageOps
    page = ImageOps.invert(ImageOps.autocontrast(image.convert('L')))
    page = page.resize((page.width * 3, page.height * 3), Image.LANCZOS)
    text = tesseract.image_to_string(page, config='--psm 6 -c tessedit_char_whitelist=0123456789', timeout=10)
    lines = [line.replace(' ', '') for line in text.splitlines() if line.strip()]
    return lines[0] if lines else ''


def read_words(image, tesseract=None, scales=(1,)):
    check_stop()
    if tesseract:
        from PIL import Image, ImageOps
        # Tesseract expects dark text on a light page; the game draws light on dark.
        gray = ImageOps.invert(ImageOps.autocontrast(image.convert('L')))
        def page_words(scale):
            page = gray if scale == 1 else gray.resize(
                (round(gray.width * scale), round(gray.height * scale)), Image.LANCZOS)
            data = tesseract.image_to_data(page, lang='tur+eng', config='--psm 11',
                                          output_type=tesseract.Output.DICT, timeout=20)
            return tesseract_words(data, page.width, page.height)
        words = []
        with ThreadPoolExecutor(max(1, len(scales))) as pool:
            for extra in pool.map(page_words, scales):
                merge(words, extra)
        check_stop()
        return words
    with tempfile.TemporaryDirectory(prefix='yula-ocr-') as directory:
        file = Path(directory) / 'screen.png'
        image.save(file)
        result = subprocess.run([str(VISION), str(file)], capture_output=True, text=True, timeout=20)
        if result.returncode:
            raise RuntimeError('Yerel OCR başarısız: ' + result.stderr[-500:])
        return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description='Yula görsel tur aracı (Windows/Chrome, macOS). Varsayılan: yalnızca incele.')
    parser.add_argument('--browser', choices=['chrome', 'safari'], default='chrome' if sys.platform == 'win32' else 'safari')
    parser.add_argument('--status-window', action='store_true', help='Ayrı canlı durum penceresini aç.')
    parser.add_argument('--live', action='store_true', help='Gerçek tıklama ve asker gönderimi yap.')
    parser.add_argument('--resume', action='store_true', help='Kaydedilmiş turdan devam et.')
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--end', type=int, default=200)
    parser.add_argument('--troop', choices=['Okçu', 'Toygun', 'Tarık', 'Tunga'], default='Okçu')
    parser.add_argument('--interval', type=float, default=2.5, help='Adımlar arası saniye, en az 2.')
    parser.add_argument('--repeat', action='store_true', help='Tur bitince 25–35 dakika bekleyip yeni tur başlat.')
    parser.add_argument('--max-sends', type=int, help='Bu çalıştırmada doğrulanan gönderim sayısına sınır koy.')
    parser.add_argument('--image', type=Path, help='Kaydedilmiş görüntüyü incele, masaüstüne dokunma.')
    parser.add_argument('--ocr', choices=['auto', 'tesseract'], default='auto',
                        help='tesseract: Windows OCR yolunu macOS üzerinde dene.')
    args = parser.parse_args()
    if not 1 <= args.start <= args.end <= 200 or args.interval < 2:
        parser.error('1 <= başlangıç <= bitiş <= 200 ve aralık >= 2 olmalı.')
    if args.image and (args.live or args.resume):
        parser.error('--image, --live/--resume ile kullanılamaz.')
    if args.max_sends is not None and args.max_sends < 1:
        parser.error('--max-sends en az 1 olmalı.')
    if sys.platform not in ('win32', 'darwin'):
        parser.error('Windows veya macOS gerekli.')
    if sys.platform == 'darwin' and not VISION.exists():
        parser.error('Önce npm run bot:setup çalıştır.')
    if sys.platform == 'win32' and args.browser != 'chrome':
        parser.error('Windows sürümünde Chrome kullan.')
    tesseract = tesseract_setup() if sys.platform == 'win32' or args.ocr == 'tesseract' else None
    browser_name = args.browser.capitalize()
    if args.image:
        from PIL import Image
        screen = ocr(Image.open(args.image), tesseract)
        print(json.dumps({'screen': screen.kind, 'captcha': screen.captcha,
                          'rows': [{k: v for k, v in row.items() if k != 'button'} for row in screen.rows()],
                          'target': screen.target(), 'total': screen.total()}, ensure_ascii=False, indent=2))
        return

    enable_dpi()
    import pyautogui as gui
    gui.FAILSAFE = True  # Mouse to any primary-display corner stops the next action.
    gui.PAUSE = .15
    with (ROOT / 'automation-state.lock').open('a+b') as lock:
        try:
            lock_file(lock)
        except OSError:
            parser.error('Başka bir tur işlemi zaten çalışıyor.')
        state = None
        if args.resume:
            if not STATE.exists():
                parser.error('Devam edilecek kayıt yok.')
            state = json.loads(STATE.read_text(encoding='utf-8'))
        elif args.live and STATE.exists():
            previous = json.loads(STATE.read_text(encoding='utf-8'))
            if previous.get('next', 0) <= previous.get('end', 200):
                parser.error('Bitmemiş tur kaydı var. --resume kullan; belirsiz gönderim varsa önce oyun içinde kontrol et.')
        engine = Engine(args.start, args.end, args.troop, state)
        sends = 0
        reporter = Reporter()
        reporter.update('starting', 'Tarayıcıya geçmek için 8 saniye.', engine.state, sends)
        def finish_status():
            if reporter.data['phase'] not in ('stopped', 'error'):
                reporter.update('stopped', 'İşlem sonlandı; ayrıntı için terminali kontrol et.')
        atexit.register(finish_status)
        global active_reporter
        active_reporter = reporter
        if args.status_window:
            subprocess.Popen([sys.executable, str(ROOT / 'automation/status_window.py')])
        round_start = engine.state.get('start', args.start)
        engine.state['start'] = round_start
        print(f'{browser_name} içinde Yula favorilerini aç. Pencereyi tamamen ana ekranda tut.')
        print('Durdur: Ctrl+C veya fareyi ekran köşesine götür. CAPTCHA açıkken tıklama yapılmaz.')
        print('MOD:', 'CANLI — asker gönderecek' if args.live else 'İNCELEME — hiçbir tıklama yok', flush=True)
        time.sleep(8)
        previous_message = None
        previous_fingerprint = None
        unstable_frames = 0
        while True:
            check_stop()
            window = foreground_window()
            if not is_browser(window, args.browser):
                previous_fingerprint = None
                if previous_message != 'focus':
                    print(f'{browser_name} ön planda değil; bekliyor.', flush=True)
                reporter.update('waiting', f'{browser_name} ön planda değil. Oyun penceresine tıkla.', engine.state, sends)
                previous_message = 'focus'
                time.sleep(2)
                continue
            reporter.update('running', 'Oyun ekranı okunuyor.', engine.state, sends)
            # Park over browser chrome so a game-drawn cursor cannot cover row text.
            gui.moveTo(window['x'] + window['width'] * .98,
                       window['y'] + min(60, window['height'] * .07), duration=.1)
            mouse_before = gui.position()
            try:
                image = crop_window(gui.screenshot(), window, gui.size())
            except RuntimeError as error:
                previous_fingerprint = None
                # Resizing/moving a browser is temporary, not a failed raid.
                reporter.update('waiting', str(error), engine.state, sends)
                if previous_message != str(error):
                    print(str(error), flush=True)
                    previous_message = str(error)
                time.sleep(args.interval)
                continue
            screen = ocr(image, tesseract)
            # Read-only mode reports observations without consuming state transitions.
            if not args.live:
                print(json.dumps({'screen': screen.kind, 'captcha': screen.captcha,
                                  'rows': [{k: v for k, v in row.items() if k != 'button'} for row in screen.rows()],
                                  'target': screen.target(), 'total': screen.total()}, ensure_ascii=False, indent=2))
                # The exact frame lets OCR problems on another computer be reproduced.
                image.save(ROOT / 'kontrol-ekran.png')
                print('Okunan ekran kaydedildi: kontrol-ekran.png (yalnızca bu bilgisayarda).')
                return
            # Do not commit a planned action if the user changed focus or moved the mouse during OCR.
            if foreground_window() != window or gui.position() != mouse_before:
                previous_fingerprint = None
                reporter.update('waiting', 'Fare hareketi veya pencere değişikliği; ekran yeniden kontrol edilecek.')
                engine.clear_frames = 0
                time.sleep(args.interval)
                continue
            fingerprint = screen.fingerprint(engine.state['troop'], engine.state['next'])
            if screen.kind in ('favorites', 'selection') and fingerprint != previous_fingerprint:
                unstable_frames += 1
                if unstable_frames >= 10:
                    raise RuntimeError('Ekran okumaları tutarlı değil; yanlış tıklama yapılmadan durduruldu.')
                previous_fingerprint = fingerprint
                reporter.update('waiting', 'Hedef ve ekran yerleşimi ikinci okumayla doğrulanıyor.')
                time.sleep(args.interval)
                continue
            unstable_frames = 0
            previous_fingerprint = fingerprint
            completed_before = len(engine.state['completed'])
            action = engine.step(screen)
            sends += len(engine.state['completed']) - completed_before
            phase = 'captcha' if screen.captcha else ('waiting' if action.kind == 'wait' else 'running')
            reporter.update(phase, action.reason, engine.state, sends)
            save(engine.state)  # In particular persist pending BEFORE pressing Tamam.
            if action.reason != previous_message:
                print(f"[{engine.state['next']}/{engine.state['end']}] {action.reason}", flush=True)
                previous_message = action.reason
            if args.max_sends is not None and sends >= args.max_sends:
                reporter.update('stopped', f'Test tamamlandı: {sends} gönderim doğrulandı.')
                print(f'Test sınırı: {sends} gönderim doğrulandı. Durduruldu.', flush=True)
                return
            if action.kind == 'stop':
                reporter.update('stopped', action.reason)
                print('Tur kaydı korundu. Otomatik yeniden gönderim yapılmadı.', flush=True)
                return
            if action.kind == 'done':
                if not args.repeat:
                    reporter.update('stopped', 'Tur tamamlandı.')
                    return
                wait = random.randint(25 * 60, 35 * 60)
                print(f'Yeni tur {wait // 60} dakika sonra başlayacak.', flush=True)
                deadline = time.time() + wait
                while time.time() < deadline:
                    check_stop()
                    remaining = max(0, int(deadline - time.time()))
                    reporter.update('waiting', f'Yeni tura {remaining // 60} dk {remaining % 60} sn kaldı.')
                    time.sleep(min(2, max(0, deadline - time.time())))
                engine = Engine(round_start, engine.state['end'], engine.state['troop'])
                engine.state['start'] = round_start
                save(engine.state)
                continue
            if action.kind in ('click', 'scroll'):
                check_stop()
                previous_fingerprint = None
                if not (0 < action.x < 1 and 0 < action.y < 1):
                    raise RuntimeError('Geçersiz ekran koordinatı; durduruldu.')
                if foreground_window() != window:
                    raise RuntimeError('Tıklama öncesi odak değişti; güvenli duruş.')
                gui.moveTo(window['x'] + action.x * window['width'],
                           window['y'] + action.y * window['height'], duration=.2)
                if action.kind == 'click':
                    gui.click()
                else:
                    # PyAutoGUI passes raw wheel delta on Windows (120 = one notch);
                    # on macOS one unit is already a line.
                    gui.scroll(action.scroll * (120 if sys.platform == 'win32' else 1))
            time.sleep(args.interval)


active_reporter = None

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        if active_reporter:
            active_reporter.update('stopped', 'Kullanıcı durdurdu; tur kaydı korundu.')
        print('\nDurduruldu; tur kaydı korundu.')
    except Exception as error:
        if active_reporter:
            active_reporter.update('error', str(error))
        print(f'Güvenli duruş: {error}', file=sys.stderr)
        sys.exit(1)
