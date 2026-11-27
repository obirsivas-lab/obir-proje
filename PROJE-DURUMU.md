# Obir Kurs Merkezi · Proje Durumu

Son güncelleme: 27 Kasım 2026

Bu dosya, çalışmayı yeni bir bilgisayarda ya da yeni bir Claude oturumunda kaldığı yerden sürdürmek için yazıldı.
**Yeni bilgisayarda:** bu klasörü açın ve Claude'a şunu söyleyin: *"PROJE-DURUMU.md ve _claude-notlar klasörünü oku, kaldığımız yerden devam edelim."*

---

## 1. Klasörler

| Klasör / dosya | İçerik |
|---|---|
| `web-sitesi/` | Site taslakları: `index.html` (ana sayfa), `sonuc-ekrani-taslak.html` (veli sonuç portalı), `bursluluk.html` (başvuru), `bursluluk-belge-taslak.html` (WhatsApp mesajı + QR giriş belgesi). Logolar `assets/yayinlar/` içinde. |
| `kampanya-2027/` | Bursluluk reklam görselleri. `tasarim/afis.html` şablonu, `render.sh` ile `cikti/*.png` üretilir. Geçmiş reklam analizi: `gecmis-bursluluk-reklamlari.html`. |
| `bursluluk-reels/` | Bursluluk animasyon Reels'i (HyperFrames). Elif Hoca ses kaydı metni: `ELIF-HOCA-SES-METNI.md`. |
| `kesirler-reels/`, `okudugunu-anlama-reels/` | Onaylı ilk iki Reels projesi ve videoları |
| `_claude-notlar/` | Claude'un hafıza notları (kararlar, tercihler). Yeni bilgisayarda Claude'a okutun. |
| **Kişisel veriler** (GitHub'a ve buluta KONMAZ) | `Öğrenci_Listesi_*.xlsx`, `BURSLULUK SINAVI 2026 .csv`, `bursluluk-2026-veri/`, `deneme sonuçları/` |

Önizleme için: `.claude/launch.json` içinde `web-sitesi` (port 8123) ve `kampanya` (port 8124) sunucuları tanımlı.

## 2. Alınan kararlar

- **Kapsam:** LGS (8. sınıf) + 5-6-7. sınıf. 8-10 kişilik butik sınıflar. Asıl fark: Maarif Modeli.
- **Programlar:** Genel Program (5-7, haftada 13 ders), Matematik Kulübü (5-7, 6 ders, İngilizce Kulübü hediye), LGS Hazırlık (8, haftada 16 ders), Ödev Yardımı (hafta içi her gün 2+ saat; sitede ilkokul olduğu belirtilmez).
- **Fiyat sitede yazmaz**, "Bilgi Al" kullanılır.
- **Denemeler:** 5. ve 6. sınıf 10, 7. sınıf 15, 8. sınıf 30.
- **Ücretsiz kaynaklar (2026-27):** LGS: Fenomen A, Maximal Modüler Sistem, Bloom Soru Bankası, Combo Team. 5-7: Fenomen A, Combo Team.
- **Deneme sonuç sistemi:** Yayınevi PDF'i öğrenci bazında ayrılır. Eşleştirme önce TC ile, yoksa kurum öğrenci numarasıyla yapılır (öğrenciler optiğe numarasını kodlar). Listede olmayan öğrenci = misafir, karnesi yayınlanmaz. Veli girişi: TC + doğum tarihi.
- **Hosting:** Türkiye'de (öğrenci verisi nedeniyle). Cloudflare yalnızca DNS ve e-posta yönlendirmesi için.
- **Reklamlar:** Hepsi web sitesinden geçecek. Gerçek öğrenci fotoğrafı kullanılmaz, lisanslı stok fotoğraf kullanılır (9-13 yaş).

## 3. 2027 Bursluluk Sınavı

- **Aday tarih: 7 Şubat 2027 Pazar** (İl MEM şartnamesi kurum tarafından gönderiliyor). Sınıflar: 4-5-6-7 (4. sınıflar iç öncelik, sitede belirtilmez).
- Geçen yıl: 215 başvuru, yaklaşık yarısı katıldı, yalnızca 14'ü kayda dönüştü. Başvuruların %52'si karne haftasında geldi.
- **Reklam planı:** Aralık %15 (test), 4-17 Ocak %25, **karne haftası 18-24 Ocak %40**, son çağrı %20. Önerilen bütçe yaklaşık 15.000 TL (karar verilmedi).
- Elle WhatsApp gönderimi: giriş belgesi linki sınavdan 1 hafta önce, hatırlatma 1 gün önce.
- Veli bilgilendirme buluşması sınav günü yapılacak.
- Görseller hazır: `kampanya-2027/cikti/` (8 PNG).
- Animasyon Reels: Adam sesi yapay bulundu, **Elif Hoca'nın ses kaydı bekleniyor**. Kayıt Mono + Kayıpsız ayarıyla, iPhone Ses Kayıtları uygulamasında yapılacak.

## 4. Alan adı ve hesaplar

- **obirkurs.com.tr:** Natro'dan alındı, **27 Kasım 2026'da aktif oldu.** Bitiş tarihi 26 Kasım 2027 (1 yıllık). **Otomatik yenilemeyi açın.**
- Ad sunucuları şu an Natro'da (ns1/ns2.natrohost.com).
- Kurumsal hesaplar için kurum Gmail adresi kullanılıyor.
- Meta reklam hesabı: "Obir" reklam hesabı.

## 5. Sıradaki işler

1. Türkiye'de hosting paketinin seçilmesi (paket sayfasını Claude'a gönderin, kontrol etsin)
2. Alan adının hosting/DNS'e bağlanması
3. Elif Hoca ses kaydı → animasyon Reels'in yeniden kurulması
4. Kaynak kitap kapaklarının bulunup "Ücretsiz kaynaklar" kartına eklenmesi
5. Eksik bilgiler: telefon/WhatsApp, adres, kadro, burs oranları, deneme paketi öğrenci listesi
6. Meta reklam bütçesinin kararı ve kampanyanın kurulması (7 Aralık başlangıç hedefi)
