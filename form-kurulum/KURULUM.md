# Bilgi formunu Google E-Tablo'ya bağlama (10 dakika)

Her yerde **obirsivas@gmail.com** hesabıyla giriş yapmış olun.

1. **sheets.new** adresini açın. Yeni boş bir E-Tablo açılır. Adını **"Obir Web Başvuruları"** yapın.
2. Üst menüde **Uzantılar → Apps Script**'e tıklayın.
3. Açılan kod sayfasındaki her şeyi silin. `form-kurulum/google-apps-script.gs` dosyasının tamamını kopyalayıp yapıştırın. **Kaydet** (disket simgesi).
4. Sağ üstte **Dağıt → Yeni dağıtım**'a basın.
   - Tür seçin (çark simgesi) → **Web uygulaması**
   - Açıklama: `site formu`
   - Şu kullanıcı olarak yürüt: **Ben (obirsivas@gmail.com)**
   - Erişimi olanlar: **Herkes**
   - **Dağıt**'a basın.
5. Google izin isteyecek: **Erişimi yetkilendir** → hesabınızı seçin → "Google bu uygulamayı doğrulamadı" çıkarsa **Gelişmiş → Obir... (güvenli değil) sayfasına git** → **İzin ver**.
   (Bu uyarı, betiği sizin yazdığınız için çıkıyor. Betik yalnızca bu tabloya yazar ve size e-posta atar.)
6. Ekranda **Web uygulaması URL'si** çıkacak (`https://script.google.com/macros/s/.../exec`). **Bu linki Claude'a gönderin.** Gerisini o bağlar.
