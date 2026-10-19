# Yula otomatik yağma

Yula Online'da Yağma Favorileri listesindeki köylere sırayla 100 asker gönderen masaüstü botu.
Ekranı OCR ile okur, fareyle tıklar; CAPTCHA çözmez, şifre kullanmaz.
Kullanıcı rehberi: [docs/TESLIM.md](docs/TESLIM.md). Test geçmişi: [docs/TEST-RAPORU.md](docs/TEST-RAPORU.md).

## Klasörler

| Klasör | İçerik |
|---|---|
| `app/` | Botun kendisi (Windows ve macOS ortak) |
| `windows/` | `Kurulum.bat`, `Yula.bat`, Windows Python paketleri. Bu dosyalar **paket düzenine göre** yazıldı (zip kökünde çalışır). |
| `mac/` | Apple Vision OCR kaynağı, kurulum, `Yula-Panel.command` |
| `tests/` | Otomatik testler |
| `tools/` | Teslim paketini oluşturan script |
| `docs/` | Teslim rehberi ve test raporu |
| `data/` | Çalışma dosyaları: tur kaydı, durum, ekran testi (git'e girmez) |

`app/` içindekiler:

| Dosya | Görevi |
|---|---|
| `panel.py` | Kullanıcının açtığı pencere: kurulum kontrolü, ekran testi, başlat/durdur, canlı durum |
| `runner.py` | Ana döngü: pencereyi bulur, ekranı okur, `core.Engine`'e sorar, tıklar. Panel bunu alt işlem olarak çalıştırır. |
| `core.py` | Saf mantık: ekranın ne olduğu, satır/numara/koordinat çıkarımı, durum makinesi. Fare veya ağ yok. |
| `ocr.py` | Ekran okuma: macOS'ta Apple Vision, Windows'ta Tesseract (çok ölçekli okuma, rakam hücreleri, düğme satırı) |
| `desktop.py` | İşletim sistemi katmanı: ön plandaki pencere, DPI, pencere kırpma, Tesseract bulma |
| `status.py` | Panelin okuduğu durum dosyası |
| `paths.py` | Bütün dosya yolları |
| `windows_setup.py` | Windows'ta OCR dil dosyalarını indirir |

## Güvenlik kuralları (kodda zorunlu)

- CAPTCHA görünürken tıklama ve kaydırma yok.
- Her tıklamadan önce aynı değerler iki ardışık okumada aynı olmalı.
- Satır numaraları sıradan çıkarılır; en az iki uyumlu okuma çoğunluk oluşturmazsa hiçbir satır kullanılmaz.
- Asker ekranında hedef koordinat, seçili 100 birlik ve toplam 100 birlik doğrulanmadan Tamam'a basılmaz.
- Tamam'dan önce `pending` durumu diske yazılır. Gönderim "yolda" sayacıyla doğrulanamazsa tekrar basılmaz.

## Geliştirme

macOS'ta ilk kurulum (Python 3.11 + Tk 8.6 gerekir; Homebrew: `brew install python@3.11 python-tk@3.11`):

```sh
sh mac/setup.sh            # Vision aracını derler, .venv'i kurar
mac/Yula-Panel.command     # paneli açar
```

Komut satırı (panelsiz):

```sh
.venv/bin/python app/runner.py --browser chrome                 # ekran testi, tıklamaz
.venv/bin/python app/runner.py --browser chrome --live --resume # canlı, kayıttan devam
.venv/bin/python app/runner.py --browser chrome --ocr tesseract # Windows OCR yolunu Mac'te dene
.venv/bin/python app/runner.py --image ekran.png                # kayıtlı görüntüyü oku
```

Testler:

```sh
.venv/bin/python -m unittest discover -s tests
```

Özel ekran kayıtları (hesap bilgisi görünür) projede tutulmaz. `YULA_CAPTURES` ortam değişkeniyle
veya varsayılan `~/Desktop/yula-arsiv/test-captures` klasöründen okunur; yoksa ilgili testler atlanır.

## Teslim paketi

```sh
.venv/bin/python tools/build_package.py
```

`dist/Yula-Windows.zip` oluşur. Pakete yalnızca Windows'ta gereken dosyalar, `TESLIM.md` ve `TESLIM.pdf` girer.
Tur kaydı, ekran görüntüleri ve Mac dosyaları girmez.
