# Yula — Windows / Chrome

Bu paket henüz Windows üzerinde kabul testi tamamlanmış bir son sürüm değildir. Test kapsamı ve açık noktalar TEST-RAPORU.md dosyasındadır.

## Kullanım

1. ZIP dosyasını kalıcı bir klasöre çıkar.
2. `Windows-Baslat.bat` dosyasına çift tıkla. İlk açılışta eksik Python 3.12, Tesseract ve Türkçe/İngilizce dil dosyalarının kurulumu başlar. İnternet gerekir; Windows izin/lisans penceresi çıkarsa kullanıcı inceler ve tamamlar. Sonraki açılışlarda kurulum tekrarlanmaz.
3. Normal Chrome'da oyuna kendin giriş yap ve Favoriler'i aç. Chrome ana ekranda, tamamen görünür ve ön planda olmalı. Script ekran/pencere ölçülerini kendisi okur; kullanıcı piksel koordinatı girmez.

Durum penceresi sıradaki köyü, bu çalıştırmadaki doğrulanmış gönderimleri ve bekleme nedenini gösterir. Penceredeki **SCRIPTİ DURDUR** düğmesi işlem ister; sürmekte olan OCR çağrısından sonra durur. Terminalde Ctrl+C de kullanılabilir. Durum penceresini kapatmak scripti durdurmaz.

Varsayılan işlem 1–200 favoriye sırayla 100 Okçu göndermektir. Tur bitince 25–35 dakika bekler. Kaynak köy oyunda seçili olan köydür. Şifre kaydetmez; otomatik giriş yapmaz.

## Otomatik kontroller

- Pencere/donanım ölçüleri ve Windows DPI farkı çalışma sırasında okunur.
- Pencere taşınırsa veya başka uygulamaya geçilirse bekler.
- Eksik veya çelişkili satır numarasında körlemesine kaydırmaz.
- Kaydırma ilerlemezse veya aynı satırlara dönülürse durur.
- Hedef koordinatı, seçili 100 birlik ve toplam 100 birlik eşleşmeden göndermez.
- Gönderimi hedef satırındaki “yolda” sayacının artışıyla doğrular; sonucu belirsiz işlemi tekrar göndermez.
- CAPTCHA geldiğinde bekler. Kullanıcı çözdükten sonra üç kararlı ekran okumasıyla devam eder.
- İlerleme `automation-state.json` içinde korunur. Belirsiz bir gönderimden sonra bu dosyayı silerek tekrar başlatma; oyundaki sonucu kontrol et.

## Kurulum tamamlanmazsa

Başlatıcı hatayı gösterir ve gönderime başlamaz. `Windows-Kur.bat` tekrar çalıştırılabilir. WinGet yoksa Microsoft Store üzerinden **App Installer** gerekir. Kurumsal kısıtlar, yönetici izni veya çevrimdışı bilgisayar için tamamen etkileşimsiz kurulum garanti edilmez.

Kurulum kaynakları: [Microsoft WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/install), [Python paketi](https://github.com/microsoft/winget-pkgs/tree/master/manifests/p/Python/Python/3/12), [Tesseract paketi](https://github.com/microsoft/winget-pkgs/blob/master/manifests/t/tesseract-ocr/tesseract/5.5.0.20241111/tesseract-ocr.tesseract.yaml), [resmî dil verileri](https://github.com/tesseract-ocr/tessdata_fast/tree/4.1.0).

## Gönderimsiz kontrol

`Windows-Kontrol.bat` ekranı okur, hiçbir tıklama yapmaz. `screen: favorites` ve doğru sıra/koordinatlar beklenir. Eksik satırlar veya yanlış koordinatlar varsa teslim testi başarısız sayılmalıdır.

Bu ortamda Windows fare/pencere katmanı, Tesseract sonuçları, temiz Windows kurulumu ve farklı gerçek DPI değerleri denenemedi. Mac OCR görüntü testleri bunların yerine geçmez.
