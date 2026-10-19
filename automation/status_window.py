"""Separate status window: opening or closing it does not start/stop raids."""
import json
import time
import tkinter as tk
from status import PATH, CONTROL, display_status


def main():
    root = tk.Tk()
    root.title('Yula — Canlı durum')
    root.geometry('440x350+30+70')
    root.minsize(360, 330)
    heading = tk.Label(root, text='Durum okunuyor…', font=('Arial', 16, 'bold'), wraplength=400)
    heading.pack(padx=16, pady=(18, 8))
    counts = tk.Label(root, font=('Arial', 12), justify='left')
    counts.pack(padx=16, pady=8)
    reason = tk.Label(root, wraplength=400, justify='left', font=('Arial', 12))
    reason.pack(padx=16, pady=8)
    stamp = tk.Label(root, fg='#666666')
    stamp.pack(pady=5)
    def stop():
        try:
            data = json.loads(PATH.read_text(encoding='utf-8'))
            command = {'pid': data['pid'], 'started': data['started'], 'action': 'stop'}
            temporary = CONTROL.with_suffix('.tmp')
            temporary.write_text(json.dumps(command), encoding='utf-8')
            temporary.replace(CONTROL)
            reason.configure(text='Durdurma istendi; devam eden ekran okuması bitince duracak.')
        except (OSError, ValueError, KeyError):
            reason.configure(text='Durdurma isteği yazılamadı; terminalde Ctrl+C kullan.')
    tk.Button(root, text='SCRIPTİ DURDUR', command=stop).pack(pady=5)
    tk.Label(root, text='Chrome ile yan yana tut. Chrome ön planda olmalı.\nBu pencereyi kapatmak scripti durdurmaz.\nScripti durdurmak için terminalde Ctrl+C.',
             fg='#666666', wraplength=400).pack(padx=12, pady=8)

    def refresh():
        try:
            data = json.loads(PATH.read_text(encoding='utf-8'))
            title, color, message = display_status(data)
            heading.configure(text=title, fg=color)
            counts.configure(text=f"Sıradaki köy: {data.get('village', '—')} / {data.get('end', '—')}\n"
                             f"Bu çalıştırmada doğrulanan: {data.get('sends', 0)}\n"
                             f"Turda doğrulanan: {data.get('completed', 0)} • Atlanan: {data.get('skipped', 0)}")
            reason.configure(text=message)
            stamp.configure(text='Son haber: ' + time.strftime('%H:%M:%S', time.localtime(data['updated'])))
        except (OSError, ValueError, KeyError):
            heading.configure(text='ÇALIŞMA BİLGİSİ YOK', fg='#666666')
            reason.configure(text='Script başlatılınca durum burada görünecek.')
        root.after(500, refresh)

    refresh()
    root.mainloop()


if __name__ == '__main__':
    main()
