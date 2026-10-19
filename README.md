# Yula — Mac ve Windows için yerel ekran inceleme aracı

## Windows + Chrome paketi

Windows için **[WINDOWS-KURULUM.md](WINDOWS-KURULUM.md)** dosyasını kullan.
Sıra: `Windows-Kur.bat` → `Windows-Kontrol.bat` → `Windows-Baslat.bat`.
Bu sürüm normal, giriş yapılmış Chrome penceresiyle çalışır. Windows'ta Tesseract
Türkçe ve İngilizce dil verileri gerekir; Swift/Apple Vision gerekmez.
Windows masaüstünde canlı doğrulama henüz yapılmadı. Aşağıdaki Safari bölümü Mac içindir.

Paket iki ayrı araç içerir: ilk Chrome/Edge inceleme aracı ve aşağıdaki yeni **macOS/Safari görsel tur scripti**.
İlk inceleme aracı otomatik gönderim yapmaz. Yeni script canlı modda asker gönderir.

## Yeni: Safari’de sırayla köy dolaşma scripti

Giriş yaptığın normal Safari penceresiyle çalışır. Google oturumunu veya şifreni almaz.
Oyunun ekranını Apple Vision ile bilgisayarında okur; OCR için görüntü yüklemez.
Bu bölüm **macOS ve ana ekran üzerindeki Safari** içindir. Windows için yukarıdaki ayrı kurulum kullanılır.

### Çalıştırma

Bu bilgisayarda kurulum tamamlandı. **Finder’da `Yula-Baslat.command` dosyasına çift tıkla**;
ardından 8 saniye içinde Safari’de favoriler listesine geç. Bu başlatıcı canlı modda çalışır,
varsa önceki tur kaydını kullanır ve tur bitince 25–35 dakika bekleyerek tekrarlar.
İlk denemeyi küçük bir aralıkla yapmak için aşağıdaki terminal komutunu kullan.

İlk kurulum (Python 3 ve Apple komut satırı geliştirme araçları gerekir):

```sh
npm run bot:setup
```

Önce Safari’de oyuna gir, **Favoriler** listesini aç. Safari’yi ana ekranda tam görünür tut.
Terminal’e macOS **Sistem Ayarları → Gizlilik ve Güvenlik → Erişilebilirlik** ve
**Ekran ve Sistem Sesi Kaydı** (bazı sürümlerde Ekran Kaydı) izinleri gerekebilir.
İzinleri macOS istediğinde kendin ver; script bunları değiştirmez.

Sadece ekran okumasını kontrol et (tıklama yapmaz; 8 saniye içinde Safari’ye geç):

```sh
npm run bot
```

Canlı tur: 1–200 favori, her hedefe 100 Okçu:

```sh
npm run bot -- --live
```

İlk deneme için küçük aralık:

```sh
npm run bot -- --live --start 2 --end 3
```

Tur bittikten sonra 25–35 dakika bekleyip tekrarlamak için `--repeat` ekle.
Varsayılan yalnızca bir turdur. Birlik seçimi `--troop Okçu`, `--troop Toygun`,
`--troop Tarık` veya `--troop Tunga`; adımlar arası süre `--interval 3` ile ayarlanabilir.
Her hedefte oyunun seçili kaynak köyü kullanılır; script kaynak köy seçimini değiştirmez.

### CAPTCHA ve devam davranışı

- İnsan doğrulaması görünürken **hiçbir tıklama veya kaydırma yapılmaz**. Doğrulamayı sen çözersin.
- Doğrulama kapandıktan sonra üç ardışık okumada oyun ekranı tanınırsa otomatik devam eder.
- Miktar zaten 100 ise tekrar +100 basmaz. Gönderim sonrasında aynı hedefin “yolda” sayacının artmasını kontrol eder.
- Gönderim sırasında CAPTCHA çıktıysa ve sonuç doğrulanamıyorsa tekrar göndermez; güvenli biçimde durur. Bu belirsiz durumda otomatik devam garantisi yoktur.
- 11 dakika ganimet bekleme uyarısı olan hedefi atlar; sonraki turda yeniden değerlendirebilir.
- Safari ön planda değilken bekler. Script çalışırken başka pencerede iş yapmak turu bekletir.
- Fareyi ekranın bir köşesine götürmek sonraki fare işlemini durdurur; terminalde **Ctrl+C** hemen keser.

Tur durumu `automation-state.json` dosyasında tutulur. Yeniden başlatma:

```sh
npm run bot -- --live --resume
```

Son gönderim belirsizse oyun içindeki hedefi kontrol etmeden kayıt dosyasını silip yeni tur başlatma.
OCR bir numarayı, hedef koordinatını, birliği veya düğmeyi güvenle okuyamazsa script durur.
Pencere örtülürse, görüntü ölçeği değişirse veya oyun arayüzü güncellenirse yeniden inceleme gerekebilir.
Bu bir ilk görsel otomasyon sürümüdür; 200 köylük kesintisiz tur ve gerçek CAPTCHA sonrası devam canlı olarak henüz doğrulanmadı.
21 otomatik test geçti. Kurulu çalıştırıcı ile kaydedilmiş favoriler ekranındaki 1–7 numaralı
köyler ve koordinatları, ayrıca sağlanan CAPTCHA görüntüsü doğru tanındı.
Yanlış CAPTCHA algısı için genel anahtar kelime kontrolü kaldırıldı. Yalnızca ön plandaki
tarayıcı penceresi okunur; masaüstündeki Terminal veya sohbet yazıları OCR'a dahil edilmez.
Bu güncellemeden önce açık olan scripti Ctrl+C ile durdurup yeniden başlat.

### Chrome canlı test sonucu

19 Ekim 2026'da bu Mac'in normal Chrome penceresinde çalıştırıcının kendisiyle
`--browser chrome --live --resume --max-sends 2` testi yapıldı. İlk iki favoriye
sırayla 100'er Okçu gönderildi; her hedefin `yolda` sayacıyla sonuç doğrulandı.
İki gönderim sınırında script kendisi durdu ve ilerleme 3. favoriye kaydedildi.
Test sırasında büyük pencere OCR okuması, asker kartlarının ayrı okunması ve
Mac'teki küçük ipucu penceresinin ana pencere sanılması düzeltildi.
Sıfır miktarı okunamazsa önce Temizle ile seçim sıfırlanır; gönderimden önce
seçilen birlik miktarı ve toplamın 100 olduğu yine zorunlu olarak doğrulanır.
Bu testte CAPTCHA çıkmadı. Windows masaüstü katmanı ve 200 köylük tam tur henüz canlı test edilmedi.

Testler:

```sh
npm run bot:test
```

## Eski Chrome/Edge inceleme aracı

Uzak tarayıcı WebGL2 hatası verdiği için oyun içi kontroller doğrulanamadı.
Araç kendi bilgisayarındaki Chrome'u görünür bir pencerede açar ve seçtiğin
ekranların görüntüsünü / görünür HTML kontrol bilgilerini kaydeder.
Canvas içindeki butonlar HTML olarak görünmüyorsa ekran görüntülerinden anlaşılır.

## Kurulum

1. Chrome kurulu olsun. Node.js LTS'yi https://nodejs.org/ üzerinden kur.
2. ZIP'i aç. Terminal veya Windows PowerShell'de `yula-local` klasörüne gir.
   Mac'te `cd ` yazıp klasörü Terminal'e sürükleyerek yolunu ekleyebilirsin.
3. Aynı klasörde çalıştır:

```sh
npm install
npm start
```

Mac ve Windows'ta komutlar aynıdır. Windows PowerShell `npm.ps1` engeli verirse
güvenlik politikasını değiştirmeden `npm.cmd install` ve `npm.cmd start` kullan.
Edge kuruluysa `npm start -- --edge` ile seçilebilir. Bu paket Firefox başlatmaz.

## Hangi ekranlar gerekli?

Chrome'da giriş işlemini kendin yap. Terminale şifre yazma.
Ekranı açtıktan sonra terminalde numarasını yazıp Enter'a bas:

| Numara | Chrome'da açık olacak ekran |
|---|---|
| 1 | Favorilerin ilk sayfası |
| 2 | Bir köyün Yağma / asker seçimi ekranı |
| 3 | İstediğin birlikte +100'e bastıktan sonraki ekran; henüz Gönder'e basma |
| 4 | Gönderim sonucu, isteğe bağlı. Gönderimi kendin yaparsın. |
| 5 | Favorilerin ikinci sayfası veya aşağı kaydırılmış devamı |
| 6 | Başka gerekli bir oyun ekranı |
| 7 | Asker seçimi sonrası çıkan Tamam düğmesi, basmadan önce. Solda ve diğer konumlarda çıktığında ayrı kayıt al. |
| q | Kaydı bitir ve Chrome'u kapat |

Araç kendi başına tıklama, gönderim veya CAPTCHA çözümü yapmaz.
Bir insan doğrulaması çıkarsa otomasyon yoktur; o noktada kaydı sonlandırabilirsin.

`captures/<tarih>/yula-inceleme.zip` oluşur. İçindeki PNG'leri gözden geçirip
bu ZIP'i konuşmaya yükle. Üçüncü ekran hangi birliğe +100 gönderileceğini de netleştirir.
Çerezler, şifreler, oturum dosyaları, ağ istekleri ve oyun kaynak kodu dışa aktarılmaz.
Görünür hesap/köy bilgileri ekran görüntüsünde bulunabilir. Giriş veya özel mesaj
ekranını kaydetme; canvas içindeki yazılar otomatik maskelenemez.
Normal HTML giriş alanları ekran görüntüsünde maskelenir, değerleri JSON'a alınmaz.
Program hiçbir dosyayı otomatik yüklemez. Oturum diske kalıcı olarak kaydedilmez.

## İlk inceleme paketinin özgün hedefi

Ekran verileriyle kontrol yöntemi belirlenecek: HTML locator'ları veya canvas için
görsel doğrulamalı tıklamalar. Hedef: 1–200 favori köy, seçilen birliğe +100,
gönderim doğrulama, tıklama aralığı ayarı, tur bitiminden sonra 25–35 dakika
rastgele bekleme ve doğrulama/hata durumunda durma. Bu özellikler bu pakette
eski inceleme aracında uygulanmış değildir; yeni Safari scripti yukarıda ayrı anlatılmıştır.
Rastgele bekleme doğrulama ekranının çıkmayacağını garanti etmez.

## Doğrulama durumu

### 19 Ekim 2026 inceleme notları

- Eklenen yaklaşık 42 saniyelik videoda favoriler ve asker gönderme ekranları arasında geçiş görülüyor. Video bir monitör çekimi; birlik adları ve küçük kontroller bu kayıttan kesin belirlenemedi.
- Eklenen telefon ekran görüntüsünde “Çok hızlı işlem yapıldı” mesajıyla insan doğrulaması açık. Bu, gelecekteki akış için durma koşuludur.
- Kullanıcıya göre asker seçimi sonrasında çıkan **Tamam** düğmesi bazen solda görünüyor. Sabit koordinat kullanılmamalı; güncel ekranda düğme bulunup doğrulanmalı. Konumu belirsizse işlem durmalı.
- İnceleme aracına bu düğmenin farklı konumlarını kaydetmek için **7** seçeneği eklendi. Kontrolün HTML öğesi mi canvas içinde mi olduğu henüz doğrulanmadı.
- Safari canlı incelemesinde oyun kontrolleri erişilebilirlik ağacında ayrı düğmeler olarak görünmedi; oyun tek görüntü/canvas alanı olarak göründü. Ekran görüntüsüyle görsel doğrulama gerekiyor.
- Favoriler 200 kayıt içeriyor; gruplar 1–50, 51–100, 101–150 ve 151–200. Grup içinde ayrıca kaydırma gerekiyor.
- Kullanıcının birlik tercihini serbest bırakması üzerine merkez köyden 100 Okçu seçimi denendi. Diğer birlikler sıfır kaldı; gönderim yapılmadı.
- +100 seçiminden sonra yolculuk ve taşıma bilgileri belirdi, pencere genişledi ve sağdaki Tamam düğmesinin konumu değişti. Yalnızca düğme değil, panel boyutu da değişebiliyor; seçim öncesi koordinatlar tekrar kullanılmamalı.
- İlk hedef için “11 dk dolmadan varır, ganimet alınmaz” uyarısı görüldü. Gelecekteki akış bu uyarıyı okuyup hedefi atlamalı veya belirtilen süreyi beklemeli; başarılı gönderim varsaymamalı.
- Kullanıcının devam talebinden sonra aynı hedefe (TimurUmut, 599 | 188) 100 Okçu ile tek canlı gönderim denendi. Tamam tıklaması listeye döndürdü; “Yağma yola çıktı” bildirimi ve hedef satırında “yolda 1” görüldü. Oyun ayrıca bu seferin bekleme süresi nedeniyle ganimetsiz döneceğini bildirdi. Bu test gönderimin kabulünü doğrular; ganimet veya ordunun dönüşü doğrulanmadı. Otomatik tur henüz uygulanmadı.

JavaScript sözdizimi kontrol edildi. Burada oyuna giriş, canlı gönderim ve
Mac/Windows üzerinde çalışma testi yapılamadı. Yerel WebGL desteği de kontrol edilmeli.
Chrome normal açılışta oyunu çalıştırıyorsa bu araçla da deneyebilirsin; garanti değildir.

Kaynak: https://playwright.dev/docs/browsers (kurulu Chrome/Edge channel desteği).

## Canlı durum penceresi

Başlatıcı durum penceresini otomatik açar. Pencereyi Chrome ile yan yana yerleştir; oyun ön planda kalmalı. Çalışıyor/bekliyor/durdu, sıradaki köy, doğrulanan gönderimler ve son haber saati görünür. 60 saniye güncelleme olmazsa çalışma durumu belirsiz olarak gösterilir. Pencereyi kapatmak scripti durdurmaz; durdurmak için terminalde Ctrl+C kullan. Durum penceresini tekrar açmak için Windows-Durum.bat (Mac: Yula-Durum.command) çalıştır. Komut satırında `--status-window` seçeneği kullanılabilir.
