# Yula Otomatik Yağma — Kullanım Rehberi (Windows)

## Bu program ne yapar?

- Chrome'da açık olan Yula Online hesabında, **Yağma Favorileri** listesindeki köylere sırayla **100'er asker** gönderir (varsayılan: Okçu, 1'den 200'e kadar).
- Tur bitince 25–35 dakika bekler ve yeni tura başlar (istersen kapatabilirsin).
- Ekranı okuyarak ve fareyle tıklayarak çalışır. **Şifreni istemez, hiçbir yere kaydetmez.** Oyuna sen giriş yaparsın.
- **İnsan doğrulamasını (CAPTCHA) çözmez.** Çıktığında bekler, sen çözersin, sonra kendisi devam eder.
- Her gönderimden sonra köyün satırındaki **"yolda" sayacına bakarak** gönderimin gittiğini kontrol eder. Emin olamazsa **tekrar basmaz**, durur. Böylece aynı köye yanlışlıkla iki kez asker gitmez.

## Gerekenler

- Windows 10 veya 11
- İnternet (sadece ilk kurulumda)
- Google Chrome ve oyuna giriş yapılmış hesap
- İlk kurulum için yaklaşık 10 dakika

---

## 1. Kurulum (sadece bir kez)

1. Zip dosyasına sağ tıkla → **Tümünü ayıkla** → kalıcı bir klasör seç (örneğin `Belgeler\Yula`).
   Zip'in içinden çalıştırma; klasörü sonradan taşıma.
2. Açılan klasörde **`Kurulum.bat`** dosyasına çift tıkla.
    - "Windows bilgisayarınızı korudu" uyarısı çıkarsa: **Ek bilgi** → **Yine de çalıştır**.
3. Siyah bir pencere açılır; Python ve Tesseract (ekran okuma programı) kurulur.
    - "Do you agree to all the source agreements terms? [Y]" sorarsa **Y** yazıp Enter'a bas.
    - "Bu uygulamanın cihazınızda değişiklik yapmasına izin vermek istiyor musunuz?" sorarsa **Evet**.
4. **"KURULUM TAMAMLANDI"** yazısını görünce bir tuşa bas. Masaüstünde **Yula** kısayolu oluşur.

> Kurulum yarıda kalırsa `Kurulum.bat`'ı tekrar çalıştırman yeterli; kalan kısmı tamamlar.

## 2. Chrome'u hazırla (her seferinde)

1. Chrome'da **yulaonline.com**'a gir, hesabına giriş yap.
2. Chrome penceresini **tam ekran yap** (sağ üstteki büyüt düğmesi).
3. Yakınlaştırma **%100** olsun: Chrome'da **Ctrl + 0**.
4. Birden fazla monitör varsa Chrome **ana ekranda** olsun.
5. Oyunda **göndereceğin şehri seç** (bot kaynak şehri değiştirmez, oyunda seçili olanı kullanır).
6. Sol menüden **Favoriler**'e tıkla. **Yağma Favorileri** listesi açık kalsın.

## 3. İlk seferde: Ekranı test et (hiçbir yere tıklamaz)

1. Masaüstündeki **Yula** kısayoluna çift tıkla → **Yula Paneli** açılır.
   Alttaki "Kayıt" kısmında **"Kurulum kontrolü: hazır."** yazmalı.
2. **"1) Ekranı test et (tıklamaz)"** düğmesine bas → **Tamam** → **8 saniye içinde Chrome'a tıkla.**
3. Panel küçülür, birkaç saniye sonra geri gelir ve sonucu gösterir. Örnek:
   *"Favoriler okundu: 1–7 arası 7 köy. 1 (599|188), 2 (600|201), …"*
4. Bu numaraları ve koordinatları oyundaki listeyle karşılaştır.
    - **Aynıysa:** hazırsın.
    - **Farklıysa veya "tanınamadı" diyorsa:** turu başlatma, 9. bölüme bak.

## 4. Turu başlat

1. Paneldeki ayarları kontrol et:
    - **Başlangıç / Bitiş köyü:** hangi favorilere gönderilecek (1–200)
    - **Birlik:** Okçu, Toygun, Tarık veya Tunga (her köye 100)
    - **Adımlar arası saniye:** tıklamalar arası bekleme (en az 2)
    - **Tur bitince bekleyip yeniden başla:** işaretliyse sürekli tur atar
2. **"2) Başlat"**'a bas → onayla → **8 saniye içinde Chrome'a tıkla.**
3. Panel kendini küçültür (Chrome'un üstünü kapatmasın diye) ve bot çalışmaya başlar.

**Bot çalışırken:**
- **Fareye ve klavyeye dokunma**, başka pencere açma. Dokunursan bot güvenli şekilde bekler; Chrome'a tekrar tıklayınca devam eder.
- Bilgisayar **uykuya geçmesin**: Ayarlar → Sistem → Güç → ekran ve uyku süresini tur boyunca **"Hiçbir zaman"** yap. Laptop kapağını kapatma.
- Durumu görmek için görev çubuğundaki panel simgesine tıklayabilirsin. Bu sırada bot bekler; Chrome'a geri tıklayınca devam eder.
- Her köy yaklaşık 40–60 saniye sürer; 200 köylük tur birkaç saat sürebilir.

**Daha önce yarıda kalmış bir tur varsa** Başlat'a basınca panel sorar:
**Evet** = kaldığı köyden devam · **Hayır** = eski kaydı yedekleyip yeni tur.

## 5. İnsan doğrulaması (CAPTCHA) çıkınca

- Panel **bip** sesi çıkarır. Bot hiçbir şeye tıklamaz.
- Parçayı kaydırarak doğrulamayı **sen çöz**.
- Bot ekranın düzeldiğini birkaç kez kontrol eder ve **kendisi devam eder**.

## 6. Durdurmak

- **Normal:** görev çubuğundan paneli aç → **Durdur**. Bot o anki işini bitirip durur.
- **Acil:** fareyi **ekranın herhangi bir köşesine** götür → bot bir sonraki hareketten önce durur.
- Paneli kapatmak da botu durdurur (önce sorar).
- Durdurunca ilerleme kaybolmaz. Sonra Başlat'a basınca kaldığı yerden devam etmeyi önerir.

## 7. Paneldeki durumlar

| Panelde yazan | Anlamı |
|---|---|
| **ÇALIŞIYOR** | Normal çalışıyor. |
| **BEKLİYOR** | Genelde Chrome önde değil, ya da ekranı ikinci kez doğruluyor. Chrome'a tıkla. |
| **İNSAN DOĞRULAMASI BEKLENİYOR** | CAPTCHA'yı çöz. |
| **DURDU** | Bot durdu; altında nedeni yazar (aşağıdaki tablo). |
| **HATA — DURDU** | Beklenmeyen bir sorun. Kayıt kısmının ekran görüntüsünü gönder. |

**Durma nedenleri ve ne yapmalı:**

| Mesaj | Ne yap |
|---|---|
| Gönderim sonucu belirsiz | Oyunda o köyün satırına bak. Başlat'a basınca panel "yolda görünüyor mu?" diye sorar. **Emin değilsen Hayır de**; köy atlanır, iki kez gönderilmez. |
| Oyun ekranı güvenle tanınamadı | Favoriler açık mı, Chrome tam ekran mı, yakınlaştırma %100 mü? Düzelt, Başlat → devam. |
| Tarayıcı penceresini tamamen ana ekrana taşı ve büyüt | Chrome'u tam ekran yap, ana monitöre al. |
| Asker ekranındaki hedef koordinatı eşleşmiyor | Oyundaki asker penceresinde **Vazgeç**'e bas, listeye dön, Başlat → devam. |
| Tam olarak 100 birlik seçimi doğrulanamadı | Asker penceresinde **Vazgeç**'e bas, Başlat → devam. |
| Kaydırma ilerlemiyor / Hedef görünür ama okunamıyor | Listeyi elle o köyün satırına kaydır, Başlat → devam. |
| … sekmesi güvenle bulunamadı | Oyunda doğru gruba (1-50, 51-100 …) elle tıkla, Başlat → devam. |

## 8. Asla yapma

- `data` klasöründeki **`tur-kaydi.json`** dosyasını silme. Özellikle "gönderim sonucu belirsiz" durumundan sonra silersen aynı köye iki kez asker gidebilir.
- Bot çalışırken Chrome'u küçültme, taşıma veya yakınlaştırmayı değiştirme.
- Aynı anda iki panel açıp iki tur başlatma (program zaten engeller).

## 9. Sorun çıkarsa: ne göndermelisin?

1. Panelde **"1) Ekranı test et"** yap.
2. Şunları gönder:
    - `data` klasöründeki **`kontrol-ekran.png`** (botun gördüğü ekran),
    - panelin **Kayıt** kısmının ekran görüntüsü.
3. Kurulum hatasıysa siyah pencerenin fotoğrafını gönder.

> `kontrol-ekran.png` oyun ekranını gösterir; hesap adın ve köy isimleri görünebilir. Sadece güvendiğin kişiye gönder.

## 10. Bilmen gerekenler

- Bu sürüm Windows'ta **gerçek bir bilgisayarda henüz denenmedi**. Windows'un ekran okuma motoru Mac üzerinde canlı oyunda denendi ve çalıştı. Bu yüzden ilk kullanımda mutlaka 3. bölümdeki testi yap.
- Küçük ekranlarda (örneğin 1366×768) oyun yazıları küçülür ve okuma zorlaşabilir. Test doğru çıkıyorsa sorun yok.
- Oyunun görünümü güncellenirse programın da güncellenmesi gerekebilir.
- Rastgele bekleme insan doğrulamasının hiç çıkmayacağını garanti etmez.
- Otomasyon araçları oyunun kurallarına aykırı olabilir; hesap riski kullanana aittir.
