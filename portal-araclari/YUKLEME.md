# Veli portalı: sonuçları sunucuya yükleme

Sonuç verisi (öğrenci adları ve deneme sonuçları) **GitHub'a gitmez**. Sunucuya cPanel üzerinden elle yüklenir.
Bu dosyada T.C. kimlik numarası ve doğum tarihi yoktur.

## İlk kurulum (bir kez)

1. cPanel'e girin → **Dosya Yöneticisi**.
2. Sol üstteki **ev simgesine** (ana dizin) tıklayın. Bu klasörde `public_html` klasörünü görmelisiniz.
   **`public_html`'in içine girmeyin.**
3. Üstteki **+ Klasör** → ad: `obir-veri` → Oluştur.
   (Sonuç: `public_html` ile `obir-veri` yan yana durur. Bu klasör internetten açılamaz.)

## Her güncellemede

1. Yeni deneme PDF'ini `deneme sonuçları` klasörüne koyun. Claude'a "portalı güncelle" deyin.
   Claude `portal-veri/portal.json` dosyasını yeniden üretir.
2. cPanel → Dosya Yöneticisi → `obir-veri` klasörüne girin → **Yükle**.
3. Bilgisayardan `Desktop/video atölyesi/portal-veri/portal.json` dosyasını seçin. Eskisinin üzerine yazmayı onaylayın.
4. Yükleme biter bitmez obirkurs.com.tr/sonuc.html güncel sonuçları gösterir.

## Kontrol

`portal-veri/eslesme-raporu.txt` dosyası yalnızca bu bilgisayarda durur. İçinde şunlar listelenir:
- PDF'teki adı listedeki adla birebir tutmayan, **yaklaşık eşleştirilmiş** öğrenciler (bir göz atın)
- PDF'te olup listede bulunamayan öğrenciler (dışarıdan katılanlar ya da yazım farkı)
- Listede olup henüz sonucu olmayan öğrenciler
