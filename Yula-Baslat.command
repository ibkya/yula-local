#!/bin/sh
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/python ] || [ ! -x .build/yula-vision ]; then
  sh automation/setup.sh || exit 1
fi
echo 'Yula: 100 Okçu, favoriler sırasıyla. CAPTCHA gelince durur; çözünce ekranı doğrular.'
echo 'Chrome'da Yula favorilerini aç. Turdan sonra 25–35 dakika bekleyip tekrar eder.'
echo 'Durdurmak için Ctrl+C. Fareyi ekran köşesine taşımak da sonraki fare işlemini durdurur.'
if [ -f automation-state.json ]; then
  .venv/bin/python automation/run.py --browser chrome --live --repeat --status-window --resume
else
  .venv/bin/python automation/run.py --browser chrome --live --repeat --status-window
fi
echo 'İşlem sonlandı. Yukarıdaki sonucu kontrol et.'
printf 'Pencereyi kapatmak için Enter: '
read -r reply
