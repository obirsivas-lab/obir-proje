#!/bin/sh
# Kullanım: sh render.sh  → cikti/ klasörüne tüm varyantları PNG olarak üretir
CH="/c/Program Files/Google/Chrome/Application/chrome.exe"
D="$(cd "$(dirname "$0")" && pwd -W)"
for v in ana foto karne son; do
  for f in 45 916; do
    if [ "$f" = 45 ]; then H=1350; else H=1920; fi
    "$CH" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 --window-size=1080,$H \
      --virtual-time-budget=4000 --screenshot="$D/cikti/bursluluk-$v-$f.png" "file:///$D/tasarim/afis.html?v=$v&f=$f" >/dev/null 2>&1
    echo "cikti/bursluluk-$v-$f.png"
  done
done
