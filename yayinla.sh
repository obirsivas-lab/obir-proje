#!/usr/bin/env bash
# web-sitesi/ klasörünü yayın klasörüne (site-yayin/) kopyalar ve GitHub'a gönderir.
# Natro'daki cron en geç 5 dakika içinde obirkurs.com.tr'ye çeker.
# Kullanım:  bash yayinla.sh "değişiklik açıklaması"
set -euo pipefail
cd "$(dirname "$0")"

KAYNAK=web-sitesi
HEDEF=site-yayin

# Yayına GİTMEYECEK dosyalar (iç taslaklar, ham kaynaklar)
HARIC=(
  "bursluluk-belge-taslak.html"
  "assets/yayinlar/_kaynak-afis-2024-2025.jpg"
)

# Güvenlik kilidi: sayfalardaki betiklerde sözdizimi hatası varsa YAYINLAMA.
for sayfa in "$KAYNAK"/*.html; do
  tmp=$(mktemp --suffix=.js)
  python -I -c "import re,sys;s=open(sys.argv[1],encoding='utf-8').read();open(sys.argv[2],'w',encoding='utf-8').write('\n;\n'.join(re.findall(r'<script>(.*?)</script>',s,re.S)))" "$sayfa" "$tmp"
  if ! node --check "$tmp" 2>/dev/null; then echo "HATA: $sayfa içindeki betikte sözdizimi hatası var, yayın durduruldu."; node --check "$tmp"; rm -f "$tmp"; exit 1; fi
  rm -f "$tmp"
done

rm -rf "$HEDEF"
mkdir -p "$HEDEF"
cp -R "$KAYNAK"/. "$HEDEF"/
for f in "${HARIC[@]}"; do rm -f "$HEDEF/$f"; done
cp yayin-ekleri/robots.txt yayin-ekleri/sitemap.xml yayin-ekleri/.htaccess "$HEDEF"/

MESAJ="${1:-Site güncellendi}"
git add -A "$HEDEF" "$KAYNAK"
if git diff --cached --quiet; then echo "Değişiklik yok."; exit 0; fi
git commit -q -m "$MESAJ

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git subtree split --prefix="$HEDEF" -b site-yayin-dal >/dev/null
git push -q site site-yayin-dal:main
git push -q proje main
echo "Gönderildi. En geç 5 dakika içinde obirkurs.com.tr'de."
