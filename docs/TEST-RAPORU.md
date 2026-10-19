# Yula 0.2.0-rc1 — Doğrulama raporu

Tarih: 19 Ekim 2026. Durum: teslim onayı verilmemiş sürüm adayı.

## Geçen kontroller

- 45 otomatik test: satır numarası çoğunluk oylaması, kenar sayaç/BİRLİK menüsü karışması, 4100 okuması, düşük güvenli birlik etiketi ve okunamayan birlik kartında tekrar okuma, 200 hedeflik sentetik durum akışı, gönderim sayacı, belirsiz gönderimde tekrar yapmama, hedef/100 birlik kontrolü, CAPTCHA durma/devam, scroll ilerlememesi, görünür satır aralığındaki OCR boşluğu, sekme geçişi, yerleşim dönüşümü ve pencere kırpma.
- Gerçek liste görüntüsünün 1366, 1920 ve 2560 piksel genişlikte ölçeklenmiş kopyaları: 1–7 numaraları ve koordinatları doğru.
- Gerçek kaydırılmış liste görüntüsünün aynı üç boyutta kopyaları: 11–17 numaraları ve koordinatları doğru.
- Asker seçimi kayıtları 1366 ve 1920 genişlikte: boş seçim 0; seçili miktar 100 ve toplam 100 doğru.
- Önceki Mac/Chrome canlı sürümünde toplam 5 gönderim hedef satırındaki yolda sayacıyla doğrulandı. Bunlar son sürümün kesintisiz tur testi değildir.

## Düzeltmeler

Sabit ekran pikseli yerine o anki pencere, metin ve düğme konumu kullanılır. Liste satırları ve numara sütunu ayrı okunur; açık/koyu görüntü geçişleri birleştirilir. İlk sekme OCR'de kaybolduğunda başlık da liste sınırını belirler. Aynı sütundaki çelişkili numara kullanılmaz. Eksik sıra numarası scroll komutu sayılmaz. Kaydırma küçük adımlarla yapılır; aynı satırlara üç kez dönülürse durur. Tıklama öncesinde ilgili değerlerin iki ardışık okumada aynı olması gerekir. Birlik kartı tek karede okunamazsa hemen durmaz; tıklamadan üç kareye kadar yeniden okur (6. köyde canlı turu durduran hata). Pencere taşınırken bekler. Durum penceresinde durdurma isteği vardır.

## 19 Ekim 2026 — Windows OCR (Tesseract) düzeltmeleri

Windows yolu ilk kez gerçek oyun görüntüleriyle, Mac'e kurulan Tesseract 5.5.3 ve paketin indirdiği aynı tur/eng dil dosyalarıyla denendi. Önceki sürüm favoriler ekranını neredeyse hiç tanımıyordu (Windows'ta ilk ekranda dururdu). Düzeltmeler:

- Tesseract'a gri-tersine çevrilmiş görüntü verilir; yazı yüksekliği ölçülüp ~11 px ve ~16 px harf boyunda iki ek okuma paralel yapılır (DPI/Retina/pencere boyutundan bağımsız).
- Satır numarası hücreleri tek tek, yalnızca rakam modunda okunur. Satır numaraları sıradan çıkarılır: en az iki uyumlu okuma çoğunluk oluşturmazsa hiçbir satır kullanılmaz; tek hatalı okuma ("11" yerine "41") oylamada elenir.
- Satırdaki silme düğmesinin "3 | 5" gibi okunması koordinat sayılmaz (en sağdaki X | Y alınır).
- +100 düğmesinin "4100" okunması miktar sayılmaz; "Konum"/"Konum:" çift okuması birleştirilir; "ASKERGÖNDER" bitişik başlık tanınır; sekmelerde köşeli parantez yok sayılır.
- Windows'ta fare tekerleği 1/120 çentik gönderiyordu (liste hiç kaymazdı); artık bir çentik (120) gönderilir.
- Görünür ama okunamayan hedef satırda iki kez bir çentik kaydırıp yeniden okur, sonra durur.
- Ekran testi (panelde "Ekranı test et") okuduğu kareyi data/kontrol-ekran.png olarak kaydeder.

Sonuç: 13 gerçek kaydın tamamında Tesseract doğru ekran türü, satır numarası, koordinat, hedef, birlik miktarı, toplam ve CAPTCHA verdi (Retina 2x kayıt dahil). Aynı kayıtların 1280–3840 piksel genişliğe ölçeklenmiş 43 kopyasında 36'sı doğru; hataların hepsi 1280/1366 genişliğe küçültülmüş (yazı ~6 px) kopyalarda. Bu küçültme gerçek 1366 ekrandan daha kötümserdir; gerçek cihazda doğrulanmadı. Yanlış okunan koordinat gönderime yol açmaz: asker ekranındaki hedef eşleşmezse script durur.

### Canlı test: Windows OCR yolu (Tesseract) macOS/Chrome üzerinde

19 Ekim 2026, `--ocr tesseract` ile bu Mac'te gerçek oyunda, sıfırdan tur (1. köyden):

- İlk denemede Tamam/Vazgeç düğmeleri okunamadı → gönderim yapılmadan güvenli duruş. Düzeltme: düğme satırı siyah-beyaz eşiklerle ayrıca okunur.
- İkinci denemede 1 ve 2 gönderildi, doğrulandı; 3'te "yolda 1" sayacı okunamadı → tekrar basmadan durdu (gönderim gerçekte gitmişti, ekran görüntüsüyle doğrulandı). Düzeltme: yolda hücresi ayrıca okunur, "yolda1" bitişik okuması ve araya giren gürültü tolere edilir; Tamam sonrası tıklamadan 4 kareye kadar yeniden okunur.
- Üçüncü denemede 4, 5, 6 gönderildi ve yolda sayacıyla doğrulandı. 6. gönderimden hemen sonra CAPTCHA çıktı; script tıklamadan bekledi, kullanıcı çözdükten sonra ekranın kararlılığını kontrol edip gönderimi doğruladı. 3 gönderim sınırında kendisi durdu.

Bu test Windows'un OCR katmanını doğrular; Windows'un pencere/fare/DPI katmanını doğrulamaz.

## 20 Ekim 2026 — Düzenleme ve panel

Proje klasörlere ayrıldı (app, windows, mac, tests, tools, docs); ekran okuma `app/ocr.py`'ye taşındı. Düzenleme öncesi ve sonrası 17 gerçek kayıt × 2 OCR motoru (34 sonuç) birebir aynı. Komut dosyalarının yerini Tkinter paneli aldı: kurulum kontrolü, gönderimsiz ekran testi, başlat/devam/durdur, belirsiz gönderimi kullanıcıya sorma, canlı durum, CAPTCHA sesi. Panel botu alt işlem olarak çalıştırır; durum ve durdurma isteği çalıştırma kimliğiyle eşleşir (Windows'ta venv python.exe gerçek yorumlayıcıyı ayrı PID ile başlatır). Panel macOS'ta açılıp görüntülendi; Windows'ta henüz açılmadı.

## Henüz doğrulanmayanlar — teslimden önce gerekli

- Temiz Windows 10/11 üzerinde Kurulum.bat ve Yula.bat (panel) ile ilk kurulum; panelin Windows'ta görünümü, küçülme ve CAPTCHA sesi. WinGet/UAC/lisans etkileşimleri.
- Windows Tesseract OCR motorunun gerçek oyun çıktısı; bu Mac'te Apple Vision kullanıldı.
- Gerçek 100/125/150 yüzde Windows DPI ve farklı laptop ekranları. Ölçeklenmiş görüntü testi gerçek cihaz testi değildir.
- Son sürümde gerçek wheel-scroll ile 7 → 8, 50 → 51 ve 200'e kadar kesintisiz tur.
- Gerçek CAPTCHA elle çözüldükten sonra devam, bağlantı kopması ve uygulama yeniden açılması senaryolarının cihaz üzerindeki kabul testi.

Bu maddeler tamamlanmadan "her laptopta iki tıkla garantili çalışır" iddiası yapılamaz.

## Tekrar çalıştırma

`python -m unittest discover -s tests -v`

Özel ekran kayıtları pakete eklenmez; yerel kayıt testleri başka bilgisayarda atlanır. Yeni cihazda önce paneldeki "Ekranı test et" ile gönderimsiz ekran okuması yapılmalıdır. Kaydedilmiş tur ilerlemesi ve hesap bilgileri dağıtım ZIP'ine konmaz.
