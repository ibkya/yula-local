#!/usr/bin/env python3
"""Windows/Chrome and macOS desktop runner. Never solves CAPTCHA."""
import argparse
import atexit
import json
import os
from pathlib import Path
import random
import sys
import time

from core import Engine
from status import Reporter
from desktop import enable_dpi, foreground_window, is_browser, crop_window, lock_file, tesseract_setup
import ocr as ocr_module
from ocr import ocr
from paths import CHECK_IMAGE, CONTROL, LOCK, STATE, VISION


def check_stop():
    if active_reporter is None:
        return
    try:
        command = json.loads(CONTROL.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return
    if command.get('run') == active_reporter.data['run'] and command.get('action') == 'stop':
        raise KeyboardInterrupt


def save(state):
    temporary = STATE.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(STATE)


def main():
    parser = argparse.ArgumentParser(description='Yula görsel tur aracı (Windows/Chrome, macOS). Varsayılan: yalnızca incele.')
    parser.add_argument('--browser', choices=['chrome', 'safari'], default='chrome' if sys.platform == 'win32' else 'safari')
    parser.add_argument('--live', action='store_true', help='Gerçek tıklama ve asker gönderimi yap.')
    parser.add_argument('--resume', action='store_true', help='Kaydedilmiş turdan devam et.')
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--end', type=int, default=200)
    parser.add_argument('--troop', choices=['Okçu', 'Toygun', 'Tarık', 'Tunga'], default='Okçu')
    parser.add_argument('--interval', type=float, default=2.5, help='Adımlar arası saniye, en az 2.')
    parser.add_argument('--repeat', action='store_true', help='Tur bitince 25–35 dakika bekleyip yeni tur başlat.')
    parser.add_argument('--max-sends', type=int, help='Bu çalıştırmada doğrulanan gönderim sayısına sınır koy.')
    parser.add_argument('--image', type=Path, help='Kaydedilmiş görüntüyü incele, masaüstüne dokunma.')
    parser.add_argument('--run-id', help=argparse.SUPPRESS)  # Set by the panel to match status and stop requests.
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
    # Vision also finds the foreground window on macOS; only a Tesseract image read can do without it.
    if sys.platform == 'darwin' and not VISION.exists() and not (args.image and args.ocr == 'tesseract'):
        parser.error('Önce mac/setup.sh çalıştır.')
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
    with LOCK.open('a+b') as lock:
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
        reporter = Reporter(args.run_id)
        reporter.update('starting', 'Tarayıcıya geçmek için 8 saniye.', engine.state, sends)
        def finish_status():
            if reporter.data['phase'] not in ('stopped', 'error'):
                reporter.update('stopped', 'İşlem sonlandı; ayrıntı için terminali kontrol et.')
        atexit.register(finish_status)
        global active_reporter
        active_reporter = reporter
        ocr_module.checkpoint = check_stop
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
                image.save(CHECK_IMAGE)
                print(f'Okunan ekran kaydedildi: {CHECK_IMAGE} (yalnızca bu bilgisayarda).')
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
