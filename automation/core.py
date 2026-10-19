"""Pure screen parser and state machine; no mouse, network or credentials."""
from dataclasses import dataclass
import re
import unicodedata


def norm(value):
    value = value.lower().replace('ı', 'i')
    return ''.join(c for c in unicodedata.normalize('NFKD', value)
                   if not unicodedata.combining(c))


TAB = re.compile(r'1-50|51-100|101-150|151-200')


def tab_text(text):
    return text.replace('–', '-').strip('[]|() ')


def sequence(candidates):
    """Assign list indices from row order. Rows are consecutive, so one index read
    fixes the rest; a misread ("41" for 11) is outvoted instead of being trusted."""
    candidates = sorted(candidates, key=lambda c: c['button'].cy)
    reads = [c for c in candidates if c['read'] is not None]
    if len(candidates) < 2:
        positions = [0] * len(candidates)
    else:
        gaps = sorted(b['button'].cy - a['button'].cy for a, b in zip(candidates, candidates[1:]))
        pitch = gaps[len(gaps) // 2]
        if pitch <= 0:
            return []
        steps = [(c['button'].cy - candidates[0]['button'].cy) / pitch for c in candidates]
        if any(abs(s - round(s)) > .25 for s in steps) or len({round(s) for s in steps}) != len(steps):
            # Irregular layout: only trust rows whose own reads agree with each other.
            return [dict(c, index=c['read']) for c in reads] if len({c['read'] for c in reads}) == len(reads) else []
        positions = [round(s) for s in steps]
    votes = {}
    for c, position in zip(candidates, positions):
        if c['read'] is not None:
            votes[c['read'] - position] = votes.get(c['read'] - position, 0) + 1
    if not votes:
        return []
    base, count = max(votes.items(), key=lambda item: item[1])
    if len(votes) > 1 and (count < 2 or count <= len(reads) - count):
        return []  # No clear majority: no row number is trustworthy.
    if count < 2:
        # A single read is not enough to number its neighbours.
        return [{'index': c['read'], 'coords': c['coords'], 'moving': c['moving'],
                 'button': c['button']} for c in reads]
    rows = []
    for c, position in zip(candidates, positions):
        index = base + position
        if 1 <= index <= 200:
            rows.append({'index': index, 'coords': c['coords'],
                         'moving': c['moving'], 'button': c['button']})
    return rows


@dataclass
class Word:
    text: str
    x: float
    y: float
    w: float
    h: float
    confidence: float = 1.0

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2


class Screen:
    def __init__(self, words):
        self.words = [Word(**w) for w in words]
        self.text = norm(' '.join(w.text for w in self.words))

    def find(self, text):
        return [w for w in self.words if norm(w.text).strip('.,:[]|() ') == norm(text)
                and w.confidence >= .45]

    def unique(self, text):
        matches = self.find(text)
        return matches[0] if len(matches) == 1 else None

    def line(self, word):
        return sorted([w for w in self.words if abs(w.cy - word.cy) < max(.006, word.h * .65)],
                      key=lambda w: w.x)

    @property
    def captcha(self):
        # Require the game's modal heading. Generic mentions in logs/help aren't a challenge.
        for first in self.find('insan'):
            nearby = [w for w in self.line(first)
                      if first.x <= w.x < first.x + .45]
            heading = norm(' '.join(w.text for w in nearby)).strip(' .:;!')
            if heading == 'insan dogrulamasi':
                return True
            title = any(norm(w.text).strip(':') == 'dogrulamasi' for w in nearby)
            instruction = any(norm(w.text).strip('.,:;') in ('parcayi', 'resimdeki', 'kaydir')
                              and first.cy < w.cy < first.cy + .55 for w in self.words)
            if title and instruction:
                return True
        return False

    @property
    def kind(self):
        if self.captcha:
            return 'captcha'
        if 'yulaonline.com' not in self.text:
            return 'unknown'
        # Tesseract may glue the heading into ASKERGÖNDER.
        if (('asker gonder' in self.text or 'askergonder' in self.text or 'askerler neden' in self.text)
                and 'gonderilecek' in self.text):
            return 'selection'
        if 'favorileri' in self.text and self.rows():
            return 'favorites'
        return 'unknown'

    def raids(self):
        """Row Yağma buttons. A weak read counts only beside a confident Git button."""
        gits = self.find('git')
        return [w for w in self.words if norm(w.text).strip('.,:') == 'yagma'
                and (w.confidence >= .45 or any(
                    abs(g.cy - w.cy) < max(.006, w.h * .65) and 0 < w.x - g.x < w.w * 2.5
                    for g in gits))]

    def tabs(self):
        return [w for w in self.words if TAB.fullmatch(tab_text(w.text))]

    def rows(self):
        candidates = []
        for raid in self.raids():
            words = self.line(raid)
            left = [w for w in words if w.x < raid.x]
            # Parse the explicit X | Y pair, never numbers inside a username. The
            # coordinates sit last before the buttons; OCR noise from the row's
            # delete button can also look like a pair, so take the rightmost one.
            line = norm(' '.join(w.text for w in left))
            pair = ([None] + list(re.finditer(r'\b(\d{1,3})\s*[|/]\s*(\d{1,3})\b', line)))[-1]
            tabs = self.tabs()
            headers = [w for w in self.find('yagma') if w.y < raid.y - .05
                       and any(norm(t.text) == 'favorileri' for t in self.line(w))]
            if not pair or not (tabs or headers):
                continue
            edge = min(w.x for w in tabs + headers)
            span = raid.x - edge
            numbers = [w for w in left if w.text.isdigit()
                       and edge + span * .025 < w.x < edge + span * .24]
            read = None
            if numbers:
                first = min(numbers, key=lambda w: w.x)
                same_column = [w for w in numbers if abs(w.x-first.x) < max(w.w, first.w)*.6]
                # Conflicting OCR reads are not evidence for any index.
                if len({w.text for w in same_column}) == 1 and 1 <= int(first.text) <= 200:
                    read = int(first.text)
            # "yolda N": the nearest number right of the label (OCR may add noise between).
            moving = 0
            for glued in [re.fullmatch(r'yolda(\d+)', norm(w.text).strip('.,:')) for w in left]:
                if glued:  # Tesseract may read "yolda1" as one word.
                    moving = max(moving, int(glued.group(1)))
            for label in [w for w in left if norm(w.text).strip('.,:') == 'yolda']:
                counts = [w for w in left if w.text.isdigit() and 0 < w.x - label.x < label.w * 2.5]
                if counts:
                    moving = max(moving, int(min(counts, key=lambda w: w.x).text))
            candidates.append({'read': read, 'coords': list(map(int, pair.groups())),
                               'moving': moving, 'button': raid})
        return sorted(sequence(candidates), key=lambda row: row['index'])

    def target(self):
        label = self.unique('Konum')
        if not label:
            return None
        nums = re.findall(r'\b\d+\b', ' '.join(w.text for w in self.line(label) if w.x > label.x))
        return list(map(int, nums[:2])) if len(nums) >= 2 else None

    def plus_below(self, label):
        plus = [w for w in self.find('+100') if abs(w.cx - label.cx) < .025
                and label.cy < w.cy < label.cy + .12]
        return plus[0] if len(plus) == 1 else None

    def troop(self, name):
        label = self.unique(name)
        if not label:
            # Short card labels often get low OCR confidence. Accept one only when
            # it is the single match and sits directly above exactly one +100.
            weak = [w for w in self.words if norm(w.text).strip('.,:') == norm(name)]
            weak = [w for w in weak if self.plus_below(w)] if len(weak) == 1 else []
            if not weak:
                return None
            label = weak[0]
        plus = self.plus_below(label)
        quantities = [w for w in self.words if w.text.isdigit()
                      and abs(w.cx - label.cx) < .02
                      and label.cy + .025 < w.cy < (plus.y if plus else label.cy + .055)]  # never the button itself
        # HEPSI stock labels contain parentheses; the lowest plain integer is selection.
        if not quantities:
            if plus and 'gonderilecek birlik sec' in self.text:
                return 0, plus
            if plus:
                return None, plus
            return None
        amount = max(quantities, key=lambda w: w.cy)
        return int(amount.text), plus

    def total(self):
        # Match on word geometry: joined text can glue a sidebar counter to the BİRLİK menu.
        totals = set()
        for label in self.words:
            if norm(label.text).strip('.,:') != 'birlik':
                continue
            left = [w for w in self.line(label) if w.x < label.x
                    and label.x - (w.x + w.w) < label.w * .6]
            number = max(left, key=lambda w: w.x, default=None)
            if number and number.text.isdigit():
                totals.add(int(number.text))
        return totals.pop() if len(totals) == 1 else None

    def fingerprint(self, troop_name, desired=None):
        """Only actionable values; exclude clocks, chat, stock and countdowns."""
        if self.kind == 'favorites':
            rows = self.rows()
            if desired is not None:
                target = next((r for r in rows if r['index'] == desired), None)
                if target:
                    return ('favorites-target', desired, tuple(target['coords']), target['moving'])
                # Edge rows can enter/leave OCR while scrolling. Only compare the
                # direction here; the current frame still supplies all coordinates.
                return ('favorites-search', desired,
                        'up' if desired < rows[0]['index'] else
                        'down' if desired > rows[-1]['index'] else 'hole')
            return ('favorites', tuple((r['index'], tuple(r['coords']), r['moving']) for r in rows))
        if self.kind == 'selection':
            troop = self.troop(troop_name)
            confirm = self.unique('Tamam')
            return ('selection', self.target(), troop[0] if troop else None, self.total(),
                    (round(confirm.cx, 2), round(confirm.cy, 2)) if confirm else None)
        return (self.kind,)


@dataclass
class Action:
    kind: str
    reason: str
    x: float = 0
    y: float = 0
    scroll: int = 0


def click(word, reason):
    return Action('click', reason, word.cx, word.cy)


class Engine:
    def __init__(self, start=1, end=200, troop='Okçu', state=None):
        self.state = state or {'next': start, 'end': end, 'troop': troop,
                               'phase': 'list', 'target': None, 'completed': [],
                               'skipped': [], 'captcha': False}
        self.clear_frames = 0
        self.unknown_frames = 0
        self.search_steps = 0
        self.search_history = []
        self.missing_frames = 0
        self.hole_nudges = 0
        self.troop_frames = 0
        self.pending_frames = 0

    def stop(self, why):
        return Action('stop', why)

    def advance(self, skipped=False):
        s = self.state
        s['skipped' if skipped else 'completed'].append(s['next'])
        s['next'] += 1
        s['phase'], s['target'] = 'list', None
        self.search_steps = 0
        self.search_history = []
        self.missing_frames = 0
        self.hole_nudges = 0
        self.troop_frames = 0
        self.pending_frames = 0

    def step(self, screen):
        s = self.state
        if screen.captcha:
            s['captcha'] = True
            self.clear_frames = 0
            return Action('wait', 'İnsan doğrulaması açık; sen çözene kadar hiçbir tıklama yok.')
        if screen.kind == 'unknown':
            self.clear_frames = 0
            self.unknown_frames += 1
            if self.unknown_frames >= 15:
                return self.stop('Oyun ekranı güvenle tanınamadı. Yerleşimi kontrol et.')
            return Action('wait', 'Tanınan oyun ekranı bekleniyor.')
        self.unknown_frames = 0
        if s['captcha']:
            self.clear_frames += 1
            if self.clear_frames < 3:
                return Action('wait', 'Doğrulama kapandı; oyun ekranının kararlılığı kontrol ediliyor.')
            s['captcha'] = False
            self.clear_frames = 0
        if s['next'] > s['end']:
            return Action('done', 'Tur tamamlandı.')
        if s['phase'] == 'pending':
            # Never re-submit after a crash, CAPTCHA or lost response.
            rows = screen.rows() if screen.kind == 'favorites' else []
            row = next((r for r in rows if r['index'] == s['next']
                        and r['coords'] == s['target']['coords']), None)
            if row and row['moving'] > s['target']['moving']:
                self.advance()
                return Action('wait', 'Gönderim hedef satırındaki yolda sayacıyla doğrulandı.')
            # The list may still be closing the dialog, or one read may miss the
            # counter. Re-read a few frames; nothing is ever pressed again here.
            self.pending_frames += 1
            if self.pending_frames < 4:
                return Action('wait', 'Gönderim sonucu bekleniyor; tekrar basılmıyor.')
            return self.stop('Gönderim sonucu belirsiz. Çift gönderimi önlemek için tekrar basılmadı; hedefi kontrol et.')
        if s['phase'] == 'cancel':
            if screen.kind == 'favorites':
                self.advance(skipped=True)
                return Action('wait', 'Ganimet bekleme süresi olan hedef atlandı.')
            return self.stop('Vazgeç sonrası listeye dönülmedi.')
        if screen.kind == 'favorites':
            # Returning from CAPTCHA before submit is safe: re-open the same row.
            if s['phase'] != 'list':
                s['phase'] = 'list'
            rows = screen.rows()
            indices = [r['index'] for r in rows]
            if len(indices) != len(set(indices)):
                return self.stop('Aynı sıra numarası birden fazla okundu; liste belirsiz.')
            desired = s['next']
            found = next((r for r in rows if r['index'] == desired), None)
            if found:
                if s['target'] and found['coords'] != s['target']['coords']:
                    return self.stop('Favori sırası/koordinatı değişmiş; yanlış hedefe işlem yapılmadı.')
                s['target'] = {k: v for k, v in found.items() if k != 'button'}
                s['phase'] = 'select'
                self.search_steps = 0
                self.search_history = []
                self.missing_frames = 0
                self.hole_nudges = 0
                return click(found['button'], f"Favori {desired}: Yağma ekranını aç.")
            # A hole within visible indices is OCR failure, not a reason to scroll.
            if rows[0]['index'] < desired < rows[-1]['index']:
                self.missing_frames += 1
                if self.missing_frames < 3:
                    return Action('wait', 'Hedef satır tekrar okunuyor; liste kaydırılmıyor.')
                if self.hole_nudges >= 2:
                    return self.stop('Hedef görünür satırlar arasında ama okunamıyor; işlem durdu.')
                # Moving the row to another spot re-renders it; nothing is clicked.
                self.hole_nudges += 1
                self.missing_frames = 0
                anchor = rows[len(rows) // 2]['button']
                return Action('scroll', f'Favori {desired} okunamadı; liste bir adım kaydırılıyor.',
                              anchor.cx, anchor.cy, -1)
            self.search_steps += 1
            if self.search_steps > 45:
                return self.stop('Hedef liste içinde bulunamadı; kaydırma sınırına ulaşıldı.')
            group = (desired - 1) // 50
            if any((r['index'] - 1) // 50 != group for r in rows):
                label = f'{group * 50 + 1}-{group * 50 + 50}'
                tab = screen.unique(label)
                if not tab:
                    return self.stop(f'{label} sekmesi güvenle bulunamadı.')
                return click(tab, f'{label} grubuna geç.')
            anchor = rows[len(rows) // 2]['button']
            signature = tuple((r['index'], tuple(r['coords'])) for r in rows)
            self.search_history.append(signature)
            if self.search_history.count(signature) >= 3:
                return self.stop('Kaydırma ilerlemiyor veya aynı satırlara dönüyor; işlem durdu.')
            return Action('scroll', f'Favori {desired} için listeyi kaydır.',
                          anchor.cx, anchor.cy,
                          -1 if desired > rows[-1]['index'] else 1)
        if s['phase'] == 'list' or not s['target']:
            return self.stop('Başlangıçta favoriler listesi açık olmalı.')
        if screen.target() != s['target']['coords']:
            return self.stop('Asker ekranındaki hedef koordinatı eşleşmiyor veya okunamıyor.')
        troop = screen.troop(s['troop'])
        if not troop:
            # A single bad frame (fading modal, toast, OCR miss) is not a reason to stop.
            self.troop_frames += 1
            if self.troop_frames >= 3:
                return self.stop('Birlik adı, miktar veya +100 güvenle okunamadı.')
            return Action('wait', 'Birlik kartı tekrar okunuyor; tıklama yapılmadı.')
        self.troop_frames = 0
        amount, plus = troop
        if amount is None and s['phase'] == 'select':
            clear = screen.unique('Temizle')
            if not clear:
                return self.stop('Miktar okunamadı; Temizle kontrolü de bulunamadı.')
            s['phase'] = 'cleared'
            return click(clear, 'Miktar alanı okunamadı; önce seçimi Temizle ile sıfırla.')
        if (amount == 0 and s['phase'] in ('select', 'cleared')) or (amount is None and s['phase'] == 'cleared'):
            s['phase'] = 'selected'
            return click(plus, f"{s['troop']} +100 seç.")
        if amount != 100 or screen.total() != 100:
            return self.stop('Tam olarak 100 birlik seçimi doğrulanamadı; tekrar +100 basılmadı.')
        if 'ganimet alinmaz' in screen.text or 'ganimet alinamaz' in screen.text:
            cancel = screen.unique('Vazgeç')
            if not cancel:
                return self.stop('Ganimet bekleme uyarısı var, Vazgeç bulunamadı.')
            s['phase'] = 'cancel'
            return click(cancel, 'Bekleme süresi dolmamış hedefi atla.')
        confirm = screen.unique('Tamam')
        if not confirm:
            return self.stop('Tamam düğmesi tekil olarak bulunamadı.')
        s['phase'] = 'pending'
        return click(confirm, f"Favori {s['next']}: doğrulanan 100 birliği gönder.")
