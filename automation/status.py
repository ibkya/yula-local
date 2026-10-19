"""Local, read-only run status. Contains no account information."""
import json
import os
from pathlib import Path
import time

PATH = Path(__file__).resolve().parent.parent / 'automation-status.json'
CONTROL = PATH.with_name('automation-control.json')


class Reporter:
    def __init__(self):
        self.data = {'pid': os.getpid(), 'started': time.time()}

    def update(self, phase, message, state=None, sends=None):
        self.data.update(phase=phase, message=message, updated=time.time())
        if state is not None:
            self.data.update(village=state['next'], end=state['end'],
                             completed=len(state['completed']), skipped=len(state['skipped']))
        if sends is not None:
            self.data['sends'] = sends
        temporary = PATH.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.data, ensure_ascii=False), encoding='utf-8')
        temporary.replace(PATH)


def display_status(data, now=None):
    now = time.time() if now is None else now
    if data['phase'] not in ('stopped', 'error') and now - data['updated'] > 60:
        return 'GÜNCEL BİLGİ YOK', '#a65d00', '60 saniyedir haber alınamadı; çalıştığı doğrulanamıyor.'
    labels = {'running': ('ÇALIŞIYOR', '#167344'),
              'waiting': ('BEKLİYOR', '#a65d00'),
              'captcha': ('İNSAN DOĞRULAMASI BEKLENİYOR', '#a65d00'),
              'stopped': ('DURDU', '#555555'), 'error': ('HATA — DURDU', '#b02323')}
    title, color = labels.get(data['phase'], ('HAZIRLANIYOR', '#245e9c'))
    return title, color, data['message']
