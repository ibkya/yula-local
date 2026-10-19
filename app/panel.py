"""Yula control panel: setup check, screen test, start/stop and live status.

The panel never clicks in the game itself; it starts runner.py and reads its status.
"""
from datetime import datetime
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
import uuid
from tkinter import messagebox, ttk

from paths import APP, CHECK_IMAGE, CONTROL, DATA, STATE, STATUS, VISION
from status import display_status

TROOPS = ('Okçu', 'Toygun', 'Tarık', 'Tunga')
FONT = 'Segoe UI' if sys.platform == 'win32' else 'Helvetica'


def load_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def tour_choice(state):
    """What the Start button may do with a saved tour: 'new', 'resume' or 'pending'."""
    if not state or state.get('next', 0) > state.get('end', 200):
        return 'new'
    return 'pending' if state.get('phase') == 'pending' else 'resume'


def check_summary(output):
    """Turn the screen-check JSON printed by runner.py into one sentence and a verdict."""
    match = re.search(r'\{.*\}', output, re.S)
    try:
        result = json.loads(match.group(0)) if match else None
    except ValueError:
        result = None
    if not result:
        return False, 'Ekran okunamadı. Chrome öndeydi mi? Kayıttaki mesajlara bak.'
    if result.get('captcha'):
        return False, 'Ekranda insan doğrulaması (CAPTCHA) var. Önce onu çöz, sonra tekrar test et.'
    kind = result.get('screen')
    if kind == 'favorites':
        rows = result.get('rows', [])
        if not rows:
            return False, 'Favoriler görünüyor ama köy satırları okunamadı.'
        indices = [row['index'] for row in rows]
        listed = ', '.join(f"{row['index']} ({row['coords'][0]}|{row['coords'][1]})" for row in rows)
        return True, (f'Favoriler okundu: {min(indices)}–{max(indices)} arası {len(rows)} köy.\n{listed}\n'
                      'Numaralar ve koordinatlar oyundakiyle aynıysa her şey hazır.')
    if kind == 'selection':
        return True, (f"Asker gönderme ekranı okundu. Hedef: {result.get('target')}. "
                      'Turu başlatmadan önce bu pencereyi kapatıp Favoriler listesini aç.')
    return False, 'Oyun ekranı tanınamadı. Chrome tam ekran mı, yakınlaştırma %100 mü, Favoriler açık mı?'


def setup_problem():
    """None when OCR is ready, otherwise a sentence for the user."""
    if sys.platform == 'darwin':
        return None if VISION.exists() else 'Mac OCR aracı yok. Önce mac/setup.sh çalıştır.'
    try:
        from desktop import tesseract_setup
        tesseract_setup()
    except Exception as error:  # Shown to the user verbatim; setup can be re-run.
        return f'{error} Kurulum.bat dosyasını tekrar çalıştır.'
    return None


def kill(process):
    if sys.platform == 'win32':
        # Also ends the real interpreter that the venv launcher started.
        subprocess.run(['taskkill', '/T', '/F', '/PID', str(process.pid)], capture_output=True)
    else:
        process.terminate()


class Panel:
    def __init__(self, root):
        self.root = root
        self.process = None
        self.run_id = None
        self.live_run_id = None     # status.json is shown only for the live run, not a screen check
        self.in_json = False
        self.setup_error = None
        self.mode = None            # 'check' or 'live' while a runner is active
        self.output = []
        self.lines = queue.Queue()
        self.last_beep = 0
        root.title('Yula Paneli')
        root.geometry('520x700')
        root.minsize(480, 640)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.build()
        threading.Thread(target=self.check_setup, daemon=True).start()
        root.lift()
        root.attributes('-topmost', True)
        root.after(400, lambda: root.attributes('-topmost', False))
        root.focus_force()
        self.refresh()

    # ---------- layout ----------
    def build(self):
        pad = {'padx': 14, 'pady': 6}
        status = ttk.LabelFrame(self.root, text='Durum')
        status.pack(fill='x', **pad)
        self.heading = tk.Label(status, text='HAZIR', font=(FONT, 18, 'bold'), fg='#245e9c')
        self.heading.pack(anchor='w', padx=10, pady=(8, 2))
        self.counts = tk.Label(status, font=(FONT, 11), justify='left', anchor='w')
        self.counts.pack(fill='x', padx=10)
        self.message = tk.Label(status, font=(FONT, 11), justify='left', anchor='w', wraplength=460)
        self.message.pack(fill='x', padx=10, pady=(4, 2))
        self.stamp = tk.Label(status, font=(FONT, 9), fg='#666666', anchor='w')
        self.stamp.pack(fill='x', padx=10, pady=(0, 8))

        settings = ttk.LabelFrame(self.root, text='Ayarlar (yeni tur için)')
        settings.pack(fill='x', **pad)
        self.start = tk.IntVar(value=1)
        self.end = tk.IntVar(value=200)
        self.troop = tk.StringVar(value='Okçu')
        self.repeat = tk.BooleanVar(value=True)
        self.interval = tk.DoubleVar(value=2.5)
        rows = [('Başlangıç köyü', ttk.Spinbox(settings, from_=1, to=200, textvariable=self.start, width=6)),
                ('Bitiş köyü', ttk.Spinbox(settings, from_=1, to=200, textvariable=self.end, width=6)),
                ('Birlik (her köye 100)', ttk.Combobox(settings, values=TROOPS, textvariable=self.troop,
                                                       state='readonly', width=10)),
                ('Adımlar arası saniye', ttk.Spinbox(settings, from_=2, to=10, increment=.5,
                                                    textvariable=self.interval, width=6))]
        for row, (label, widget) in enumerate(rows):
            ttk.Label(settings, text=label).grid(row=row, column=0, sticky='w', padx=10, pady=3)
            widget.grid(row=row, column=1, sticky='w', padx=10, pady=3)
        ttk.Checkbutton(settings, text='Tur bitince 25–35 dakika bekleyip yeniden başla',
                        variable=self.repeat).grid(row=len(rows), column=0, columnspan=2, sticky='w', padx=10, pady=(3, 8))

        buttons = ttk.Frame(self.root)
        buttons.pack(fill='x', **pad)
        self.check_button = ttk.Button(buttons, text='1) Ekranı test et (tıklamaz)', command=self.screen_check)
        self.start_button = ttk.Button(buttons, text='2) Başlat', command=self.start_tour)
        self.stop_button = ttk.Button(buttons, text='Durdur', command=self.stop, state='disabled')
        for button in (self.check_button, self.start_button, self.stop_button):
            button.pack(fill='x', pady=3, ipady=4)

        ttk.Label(self.root, text='Bot çalışırken fareye ve klavyeye dokunma. CAPTCHA çıkarsa sen çöz; '
                                  'bot bekler ve sonra kendisi devam eder. Acil durdurma: fareyi ekranın bir köşesine götür.',
                  wraplength=480, foreground='#555555').pack(fill='x', padx=14)

        log = ttk.LabelFrame(self.root, text='Kayıt')
        log.pack(fill='both', expand=True, **pad)
        self.log = tk.Text(log, height=10, font=('Consolas' if sys.platform == 'win32' else 'Menlo', 9),
                           state='disabled', wrap='word')
        self.log.pack(fill='both', expand=True, padx=6, pady=6)

    def write_log(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', text.rstrip('\n') + '\n')
        self.log.delete('1.0', 'end-300l')
        self.log.see('end')
        self.log.configure(state='disabled')

    # ---------- setup ----------
    def check_setup(self):
        problem = setup_problem()
        self.lines.put(('setup', problem))

    # ---------- running the bot ----------
    def launch(self, args, mode):
        # pythonw.exe (no console) runs the panel; the bot needs a real stdout to report back.
        python = Path(sys.executable)
        if python.name.lower() == 'pythonw.exe':
            python = python.with_name('python.exe')
        self.run_id = uuid.uuid4().hex
        command = [str(python), '-u', str(APP / 'runner.py'), '--browser', 'chrome', '--run-id', self.run_id, *args]
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        environment = dict(os.environ, PYTHONIOENCODING='utf-8')
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, encoding='utf-8', errors='replace',
                                        cwd=str(APP.parent), env=environment, creationflags=flags)
        self.mode, self.output, self.in_json = mode, [], False
        if mode == 'live':
            self.live_run_id = self.run_id
        threading.Thread(target=self.read_output, args=(self.process,), daemon=True).start()
        self.set_running(True)
        self.write_log(f"--- {datetime.now():%H:%M:%S} {'Ekran testi' if mode == 'check' else 'Tur'} başladı ---")
        # The panel must not cover Chrome: the bot reads the Chrome window from the screen.
        self.root.after(1500, self.root.iconify)

    def read_output(self, process):
        for line in process.stdout:
            self.lines.put(('line', line))
        self.lines.put(('exit', process.wait()))

    def set_running(self, running):
        self.check_button.configure(state='disabled' if running else 'normal')
        self.start_button.configure(state='disabled' if running else 'normal')
        self.stop_button.configure(state='normal' if running else 'disabled')

    def screen_check(self):
        messagebox.showinfo('Ekran testi', 'Tamam’a bastıktan sonra 8 saniye içinde Chrome’a geç '
                                           've oyunda Favoriler listesini açık tut.\nBu test hiçbir yere tıklamaz.')
        self.launch([], 'check')

    def start_tour(self):
        state = load_json(STATE)
        choice = tour_choice(state)
        if choice == 'pending':
            messagebox.showwarning(
                'Son gönderim belirsiz',
                f"Kayıtlı turda {state['next']}. köye son gönderimin sonucu doğrulanamadı.\n\n"
                'Oyunda bu köyün satırına bak: "yolda" yazıyorsa gönderim gitmiştir.\n\n'
                'Emin değilsen "Hayır" de: köy bu turda atlanır, sonraki turda yeniden denenir. '
                'Böylece aynı köye iki kez asker gitmez.')
            sent = messagebox.askyesno('Son gönderim', f"{state['next']}. köyün satırında \"yolda\" görünüyor mu?")
            state['completed' if sent else 'skipped'].append(state['next'])
            state.update(next=state['next'] + 1, phase='list', target=None)
            STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
            self.write_log(f"Belirsiz gönderim kullanıcıya soruldu: {'gitti' if sent else 'gitmedi, atlandı'}.")
            choice = 'resume'
        if choice == 'resume':
            answer = messagebox.askyesnocancel(
                'Kayıtlı tur', f"Kayıtlı tur {state['next']}. köyde kaldı ({state['next']}/{state['end']}).\n\n"
                               'Evet: kaldığı yerden devam et (kayıttaki ayarlarla)\n'
                               'Hayır: kaydı yedekleyip yeni tur başlat')
            if answer is None:
                return
            if not answer:
                STATE.replace(DATA / f'tur-kaydi-yedek-{datetime.now():%Y%m%d-%H%M%S}.json')
                choice = 'new'
        args = ['--live']
        if choice == 'resume':
            args.append('--resume')
        else:
            try:
                start, end, interval = self.start.get(), self.end.get(), self.interval.get()
            except tk.TclError:
                messagebox.showerror('Ayarlar', 'Köy numaraları ve saniye sayı olmalı.')
                return
            if not 1 <= start <= end <= 200 or interval < 2:
                messagebox.showerror('Ayarlar', 'Başlangıç 1–200 arası, bitişten küçük olmalı; saniye en az 2.')
                return
            if STATE.exists():  # Finished tour: keep it as a backup, start clean.
                STATE.replace(DATA / f'tur-kaydi-yedek-{datetime.now():%Y%m%d-%H%M%S}.json')
            args += ['--start', str(start), '--end', str(end), '--troop', self.troop.get(),
                     '--interval', str(interval)]
        if self.repeat.get():
            args.append('--repeat')
        if not messagebox.askokcancel('Başlıyor', 'Tamam’a bastıktan sonra 8 saniye içinde Chrome’a geç; '
                                                  'oyunda Favoriler listesi açık olsun.\nBot CANLI çalışacak ve asker gönderecek.'):
            return
        self.launch(args, 'live')

    def stop(self):
        if not self.process or self.process.poll() is not None:
            return
        temporary = CONTROL.with_suffix('.tmp')
        temporary.write_text(json.dumps({'run': self.run_id, 'action': 'stop'}), encoding='utf-8')
        temporary.replace(CONTROL)
        self.write_log('Durdurma istendi; bot o anki ekran okumasını bitirince duracak.')
        self.root.after(20000, self.force_stop, self.process)

    def force_stop(self, process):
        if process.poll() is None:
            kill(process)
            self.write_log('Bot 20 saniyede durmadı; kapatıldı. Tur kaydı korunur.')

    def close(self):
        if self.process and self.process.poll() is None:
            if not messagebox.askyesno('Çıkış', 'Bot çalışıyor. Paneli kapatırsan bot durdurulacak. Emin misin?'):
                return
            self.stop()
            try:
                self.process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                kill(self.process)
        self.root.destroy()

    # ---------- periodic refresh ----------
    def refresh(self):
        while not self.lines.empty():
            kind, value = self.lines.get()
            if kind == 'line':
                self.output.append(value)
                if self.mode == 'check' and value.startswith('{'):
                    self.in_json = True
                if not self.in_json:
                    self.write_log(value)
                if self.in_json and value.startswith('}'):
                    self.in_json = False
            elif kind == 'setup':
                self.setup_error = value
                if value:
                    self.heading.configure(text='KURULUM EKSİK', fg='#b02323')
                    self.message.configure(text=value)
                    self.start_button.configure(state='disabled')
                    self.check_button.configure(state='disabled')
                else:
                    self.write_log('Kurulum kontrolü: hazır.')
            elif kind == 'exit':
                self.finished(value)
        self.show_status()
        self.root.after(500, self.refresh)

    def finished(self, code):
        mode, self.process, self.mode = self.mode, None, None
        self.set_running(False)
        self.root.deiconify()
        self.root.lift()
        if mode == 'check':
            ok, text = check_summary(''.join(self.output))
            self.write_log(text)
            if CHECK_IMAGE.exists():
                self.write_log(f'Okunan ekran: {CHECK_IMAGE}')
            (messagebox.showinfo if ok else messagebox.showwarning)('Ekran testi', text)
        else:
            self.write_log(f'--- Bot durdu ({datetime.now():%H:%M:%S}) ---')

    def show_status(self):
        if self.setup_error:
            return  # Keep the setup message until the user fixes it and reopens the panel.
        data = load_json(STATUS)
        running = self.process is not None and self.process.poll() is None
        if data and data.get('run') != self.live_run_id:
            data = None  # A screen check or an older session: describe the saved tour instead.
        if not data:
            if running:
                return
            self.heading.configure(text='HAZIR', fg='#245e9c')
            self.stamp.configure(text='')
            state = load_json(STATE)
            if state and tour_choice(state) != 'new':
                self.counts.configure(text=f"Kayıtlı tur: {state['next']}. köyde kaldı ({state['next']}/{state['end']})\n"
                                           f"Bu turda tamamlanan: {len(state.get('completed', []))}"
                                           f" • atlanan: {len(state.get('skipped', []))}")
                self.message.configure(text='Başlat’a basınca kaldığı yerden devam etmeyi önerir.')
            else:
                self.counts.configure(text='Kayıtlı tur yok; Başlat yeni tur açar.')
                self.message.configure(text='')
            return
        title, color, message = display_status(data)
        if not running and data.get('phase') not in ('stopped', 'error'):
            title, color = 'DURDU', '#555555'
        self.heading.configure(text=title, fg=color)
        state = load_json(STATE) or {}
        self.counts.configure(text=f"Sıradaki köy: {data.get('village', '—')} / {data.get('end', '—')}\n"
                                   f"Bu çalıştırmada gönderilen: {data.get('sends', 0)}\n"
                                   f"Bu turda tamamlanan: {len(state.get('completed', []))}"
                                   f" • atlanan: {len(state.get('skipped', []))}")
        self.message.configure(text=message)
        self.stamp.configure(text='Son haber: ' + time.strftime('%H:%M:%S', time.localtime(data['updated'])))
        if running and data.get('phase') == 'captcha' and time.time() - self.last_beep > 10:
            self.last_beep = time.time()
            self.root.bell()  # The panel is minimized; a sound tells the user to solve it.


def main():
    root = tk.Tk()
    Panel(root)
    root.mainloop()


if __name__ == '__main__':
    main()
