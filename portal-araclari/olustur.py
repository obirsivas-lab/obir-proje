"""
Obir veli portalı · veri üretici
--------------------------------
Öğrenci listesi (Excel) + deneme sonuç PDF'leri  ->  portal-veri/portal.json

  python -I portal-araclari/olustur.py

* Çıktı yalnızca bu bilgisayarda (portal-veri/, .gitignore'da) oluşur; GitHub'a gitmez.
* portal.json içinde T.C. kimlik numarası ve doğum tarihi YOKTUR: her öğrenci, T.C. + doğum
  tarihinden rastgele "tuz" ile üretilmiş bir özetle (SHA-256) saklanır.
* Sunucuya elle yüklenir: public_html'in YANINDAKİ  obir-veri/portal.json
* Eşleşme raporu: portal-veri/eslesme-raporu.txt (yalnızca bu bilgisayarda)
"""
import glob, hashlib, json, os, re, secrets, subprocess, datetime
from collections import Counter
import openpyxl

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_KLASOR = os.path.join(KOK, 'deneme sonuçları')
CIKTI = os.path.join(KOK, 'portal-veri')
LISTE_DESEN = os.path.join(KOK, 'Öğrenci_Listesi*.xlsx')

# Hangi PDF hangi yayın / tarih? Yeni bir deneme PDF'i eklenince buraya bir satır ekleyin.
SINAVLAR = [
    # (dosya adında aranacak desen,  yayın,                tarih,        görünen ad)
    (r'MADALYON 18 KASIM',          'Madalyon Yayınları',  '2026-11-18', 'Madalyon 1. Deneme'),
    (r'MAX.MAL',                    'Maximal Yayınları',   '2026-10-17', 'Maximal Kurumsal Deneme 1'),
    (r'Art.bir Rota',               'Artıbir Yayınları',   '2026-10-17', 'Artıbir Rota İzleme 1'),
    (r'L.DERLER KARMASI',           'Liderler Karması',    '2026-10-01', 'Liderler Karması LGS 1'),
    (r'3d yay',                     '3D Yayınları',        '2026-10-30', '3D Türkiye Geneli 1'),
]

DERS_TANIM = [  # (özet sayfası başlığında desen, karne sayfasında satır başı deseni, kod, ad)
    (r'T.rk.e',    r'^T.rk.e\b',                 'TÜR', 'Türkçe'),
    (r'SOSYAL',    r'^SOSYAL',                   'SOS', 'Sosyal Bilgiler'),
    (r'Tarih',     r'^(T\.\s*C\.|.nk|INK|Tarih)', 'İNK', 'T.C. İnkılap Tarihi'),
    (r'K\.ve',     r'^Din',                      'DİN', 'Din Kültürü'),
    (r'.ngilizce', r'^.ngilizce',                'İNG', 'İngilizce'),
    (r'Matematik', r'^Matematik',                'MAT', 'Matematik'),
    (r'Fen',       r'^Fen',                      'FEN', 'Fen Bilimleri'),
]
SORU_ADIM = [5, 10, 15, 20, 25, 30, 40]
BOZUK = '�'  # PDF'te Türkçe harflerin yerine çıkan karakter

def anahtar_ad(s):
    """Türkçe büyük harfe çevir; Türkçe özel harfleri ve bozuk karakteri '?' yap."""
    s = (s or '').replace('i', 'İ').replace('ı', 'I').upper()
    for c in 'ÇĞİÖŞÜ' + BOZUK:
        s = s.replace(c, '?')
    return re.sub(r'\s+', ' ', s).strip()

def kelime_uyar(a, b):
    """İki kelime aynı mı? '?' her iki tarafta da tek harf yerine geçer."""
    return len(a) == len(b) and all(x == y or x == '?' or y == '?' for x, y in zip(a, b))

def ad_uyar(pdf_ad, liste_ad):
    """PDF adının her kelimesi liste adında aynı sırayla var mı? (ikinci ad eksik olabilir)"""
    l = liste_ad.split(); k = 0
    for w in pdf_ad.split():
        while k < len(l) and not kelime_uyar(w, l[k]):
            k += 1
        if k == len(l):
            return False
        k += 1
    return True

def sayi(x):
    return float(x.replace('.', '').replace(',', '.')) if ',' in x else float(x)

def pdf_metin(yol, sayfa=1):
    r = subprocess.run(['pdftotext', '-enc', 'UTF-8', '-layout', '-f', str(sayfa), '-l', str(sayfa), yol, '-'],
                       capture_output=True)
    return r.stdout.decode('utf-8', 'replace').splitlines()

def sinav_bilgi(dosya):
    for desen, yayin, tarih, ad in SINAVLAR:
        if re.search(desen, dosya, re.I):
            return yayin, tarih, ad
    raise SystemExit(f'Bu PDF için yayın/tarih tanımı yok, SINAVLAR listesine ekleyin: {dosya}')

def pdf_oku(yol):
    satirlar = pdf_metin(yol)
    dosya = os.path.basename(yol)
    yayin, tarih, ad = sinav_bilgi(dosya)
    # ders sırası: özet sayfasındaki 'Sıra Ö.No İsim Sınıf ...' satırı
    bas = next(l for l in satirlar if re.search(r'S.ra\s+.\.No', l))
    kuyruk = bas[re.search(r'S.n.f', bas).end():]
    bulunan = []
    for desen, karne_desen, kod, dad in DERS_TANIM:
        m = re.search(desen, kuyruk)
        if m:
            bulunan.append((m.start(), kod, dad, karne_desen))
    dersler = [(k, d, kd) for _, k, d, kd in sorted(bulunan)][:6]
    # katılım: KATILIMLAR başlığından sonraki satırlarda, satır sonundaki 4 sayı
    katilim = None
    for i, l in enumerate(satirlar):
        if 'KATILIM' in l:
            for l2 in satirlar[i + 1:i + 4]:
                m = re.search(r'(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$', l2)
                if m:
                    katilim = list(map(int, m.groups())); break
            break
    ogrenciler, ortalama = [], None
    for l in satirlar:
        t = l.split()
        if not t:
            continue
        if l.strip().startswith('Genel Ortalama'):
            nums = [sayi(x) for x in t[2:]]
            if len(nums) >= 22:
                ortalama = nums
            continue
        if not (re.fullmatch(r'\d+', t[0]) and len(t) > 30 and re.fullmatch(r'\d+', t[1])):
            continue
        j = next((k for k in range(3, len(t)) if re.fullmatch(r'\d{1,2}([-/]\S{1,3})?', t[k])), None)
        if j is None:
            continue
        nums = t[j + 1:]
        if len(nums) != 27 or not all(re.fullmatch(r'-?[\d.,]+', x) for x in nums):
            continue
        n = [sayi(x) for x in nums]
        ogrenciler.append({
            'ad_pdf': ' '.join(t[2:j]), 'sube': t[j],
            'dy': [[int(n[3 * i]), int(n[3 * i + 1])] for i in range(6)],
            'puan': n[21], 'kd': int(n[23]), 'gd': int(n[26]),
        })
    if not ogrenciler:
        raise SystemExit(f'Öğrenci satırı okunamadı: {dosya}')
    sinif_no = int(Counter(re.match(r'\d+', o['sube']).group(0) for o in ogrenciler).most_common(1)[0][0])
    # soru sayısı: önce tahmin (en çok cevaplanan), sonra karne sayfasındaki gerçek değer
    soru = []
    for i in range(6):
        en = max(o['dy'][i][0] + o['dy'][i][1] for o in ogrenciler)
        soru.append(next((s for s in SORU_ADIM if s >= en), en))
    go = [None] * 6
    karne = [l.strip() for l in pdf_metin(yol, 2)]
    tum_bas = [kd for _, _, kd in dersler] + [r'^Toplam', r'^Soru No']
    for i, (_, _, kd) in enumerate(dersler):
        for a, l in enumerate(karne):
            if not re.match(kd, l):
                continue
            blok = l
            for l2 in karne[a + 1:a + 4]:
                if any(re.match(b, l2) for b in tum_bas):
                    break
                blok += ' ' + l2
            govde = re.sub(r'^[^\d]+', '', blok)
            tamlar = re.findall(r'(?<![\d,])\d+(?![\d,])', govde)
            ondalik = re.findall(r'\d+,\d+', govde)
            en = max(o['dy'][i][0] + o['dy'][i][1] for o in ogrenciler)
            if tamlar and en <= int(tamlar[0]) <= 60:
                soru[i] = int(tamlar[0])
            if len(ondalik) >= 4:
                go[i] = sayi(ondalik[-1])
            break
    kk = katilim[0] if katilim else len(ogrenciler)
    gk = katilim[3] if katilim else max(o['gd'] for o in ogrenciler)
    sinav = {
        'id': hashlib.sha1(dosya.encode()).hexdigest()[:10],
        'ad': ad, 'yayin': yayin, 'tarih': tarih, 'sinifSeviye': sinif_no,
        'dersler': [{'k': k, 'ad': d, 'soru': s} for (k, d, _), s in zip(dersler, soru)],
        'kk': max(kk, len(ogrenciler)), 'gk': max(gk, max(o['gd'] for o in ogrenciler)),
        # kurum ortalaması: bu PDF'teki (kurumdaki) tüm öğrencilerden hesaplanır
        'kurumPuan': round(sum(o['puan'] for o in ogrenciler) / len(ogrenciler), 3),
        'ko': [round(sum(o['dy'][i][0] - o['dy'][i][1] / 3 for o in ogrenciler) / len(ogrenciler), 2)
               for i in range(len(dersler))],
        # özet sayfasındaki "Genel Ortalama" satırı = tüm katılımcıların (genel) ortalaması
        'genelPuan': ortalama[21] if ortalama else None,
        'go': [round(ortalama[3 * i + 2], 2) for i in range(len(dersler))] if ortalama else None,
    }
    return sinav, ogrenciler

def liste_oku():
    yol = sorted(glob.glob(LISTE_DESEN), key=os.path.getmtime)[-1]
    wb = openpyxl.load_workbook(yol, data_only=True)
    ogr = {}
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        hi = next((i for i, r in enumerate(rows) if r and 'Öğrenci Adı' in r), None)
        if hi is None:
            continue
        h = list(rows[hi]); ix = {k: h.index(k) for k in h if k}
        for r in rows[hi + 1:]:
            if not r[ix['Öğrenci Adı']]:
                continue
            tc = str(r[ix['Öğrenci T.C. Kimlik Numarası']] or '').strip()
            dg = r[ix['Öğrenci Doğum Tarihi']]
            dg = dg.strftime('%d.%m.%Y') if isinstance(dg, (datetime.datetime, datetime.date)) else str(dg or '').strip()
            ad = f"{str(r[ix['Öğrenci Adı']]).strip()} {str(r[ix['Öğrenci Soyadı']]).strip()}"
            seviye = str(r[ix['Öğrenci Sınıf Seviyesi']] or '').strip().lstrip('0')
            sube = str(r[ix['Öğrenci Şube']] or '').strip() if 'Öğrenci Şube' in ix else ''
            ogr.setdefault(anahtar_ad(ad), {'ad': ad, 'tc': tc, 'dg': dg, 'seviye': seviye, 'sube': sube})
    return os.path.basename(yol), ogr


# ---------------------------------------------------------------- isim eşleştirme
def mesafe(a, b):
    """Levenshtein uzaklığı; '?' (Türkçe harf) her harfle eşleşir."""
    onceki = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        simdi = [i]
        for j, cb in enumerate(b, 1):
            ayni = ca == cb or ca == '?' or cb == '?'
            simdi.append(min(onceki[j] + 1, simdi[j - 1] + 1, onceki[j - 1] + (0 if ayni else 1)))
        onceki = simdi
    return onceki[-1]


def duzeltmeler_oku():
    """portal-veri/eslesme-duzeltme.txt: her satır  PDF'TEKİ AD -> LİSTEDEKİ AD  ya da  PDF'TEKİ AD -> YOK"""
    yol = os.path.join(CIKTI, 'eslesme-duzeltme.txt')
    d = {}
    if os.path.exists(yol):
        for satir in open(yol, encoding='utf-8'):
            if '->' in satir and not satir.lstrip().startswith('#'):
                a, b = satir.split('->', 1)
                d[anahtar_ad(a)] = None if b.strip().upper() in ('YOK', '-') else anahtar_ad(b)
    return d

DUZELTME = {}
KULLANILAN_DUZELTME = set()

def eslestir(k, seviye, liste):
    """PDF adını listedeki öğrenciyle eşleştir. Dönüş: (liste anahtarı, yöntem) ya da (None, None)."""
    if k in DUZELTME:
        KULLANILAN_DUZELTME.add(k)
        hedef = DUZELTME[k]
        return (hedef, 'elle') if hedef in liste else (None, None)
    if k in liste:
        return k, 'birebir'
    p = k.split()
    if not p:
        return None, None
    ayni_sinif = [lk for lk, lo in liste.items() if lo['seviye'] == str(seviye)]
    # yakın sınıflar: 4. sınıf denemesine 5. sınıflar da girmiş olabilir
    yakin = [lk for lk, lo in liste.items() if lo['seviye'] in (str(seviye), str(seviye + 1))]

    def tek(adaylar):
        return adaylar[0] if len(adaylar) == 1 else None

    # 0) kısaltılmış ilk ad: "M ENES KAÇMAZ" / "ZNAZ REŞBER" -> "MUHAMMED ENES KAÇMAZ" / "ZEYNEP NAZ REŞBER"
    def kisaltmalar(lk):
        w = lk.split()
        if len(w) < 3:
            return []
        return [' '.join([w[0][0]] + w[1:]), ' '.join([w[0][0] + w[1]] + w[2:]), ' '.join([w[0][0] + '.'] + w[1:])]
    esit = lambda x, y: len(x.split()) == len(y.split()) and all(kelime_uyar(m, n) for m, n in zip(x.split(), y.split()))
    a = tek([lk for lk in yakin if any(esit(k, v) for v in kisaltmalar(lk))])
    if a:
        return a, 'kısaltılmış ad'
    # 1) kelimeler sırayla var (ikinci ad eksik / fazla)
    a = tek([lk for lk in ayni_sinif if ad_uyar(k, lk) or ad_uyar(lk, k)])
    if a:
        return a, 'ikinci ad farkı'
    # 2) soyadı aynı + ilk ad en fazla 1 harf farklı, AYNI sınıf (kardeşler karışmasın)
    a = tek([lk for lk in ayni_sinif if mesafe(lk.split()[-1], p[-1]) == 0 and mesafe(lk.split()[0], p[0]) <= 1])
    if a:
        return a, 'ilk ad yazım farkı'
    # 3) ilk ad aynı + soyadı en fazla 2 harf farklı
    a = tek([lk for lk in yakin if mesafe(lk.split()[0], p[0]) == 0 and mesafe(lk.split()[-1], p[-1]) <= 2])
    if a:
        return a, 'soyadı yazım farkı'
    # 4) soyadı sınıfta tek + ilk adın baş harfi aynı
    a = tek([lk for lk in ayni_sinif if mesafe(lk.split()[-1], p[-1]) <= 1])
    if a and (a[0] == p[0][0] or '?' in (a[0], p[0][0])):
        return a, 'soyadı (sınıfta tek)'
    # 5) ilk ad sınıfta tek + soyadının ilk 3 harfi tutuyor
    a = tek([lk for lk in ayni_sinif if mesafe(lk.split()[0], p[0]) == 0])
    if a and mesafe(a.split()[-1][:3], p[-1][:3]) == 0:
        return a, 'ilk ad (sınıfta tek)'
    return None, None


# ---------------------------------------------------------------- ana akış
def main():
    import shutil, sys, zipfile
    import pypdf
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import karne

    liste_ad, liste = liste_oku()
    DUZELTME.update(duzeltmeler_oku())
    tuz = secrets.token_hex(16)
    yukle = os.path.join(CIKTI, 'obir-veri')
    if os.path.isdir(yukle):
        shutil.rmtree(yukle)
    os.makedirs(os.path.join(yukle, 'karneler'))

    sinavlar, sonuc = [], {}
    eslesmeyen, esnek = [], []
    kazanim_sayisi = 0
    for yol in sorted(glob.glob(os.path.join(PDF_KLASOR, '*.pdf'))):
        sinav, _ = pdf_oku(yol)          # yalnızca sınav bilgisi (ad, yayın, tarih) için
        sinavlar.append(sinav)
        dosya = os.path.basename(yol)
        okuyucu = pypdf.PdfReader(yol)
        # tüm sonuçlar öğrencilerin kendi karne sayfalarından okunur (özet sayfası eksik olabiliyor)
        karneler, gorulen = [], set()
        for no in range(2, len(okuyucu.pages) + 1):
            r = karne.karne_sonuc(yol, no)
            if not r or not r['ad']:
                continue
            ka = anahtar_ad(r['ad'])
            if ka in gorulen:
                continue
            gorulen.add(ka)
            r['sayfa'] = no
            karneler.append(r)
        if karneler:
            ilk = karneler[0]
            sinav['dersler'] = [{'k': d[0], 'ad': next(a for _, _, k, a in DERS_TANIM if k == d[0]), 'soru': d[1]}
                                for d in ilk['dersler']]
            sinav['ko'] = [d[5] for d in ilk['dersler']]
            sinav['go'] = [d[6] for d in ilk['dersler']]
            sinav['kk'] = max(ilk['katilim'][1], len(karneler))
            sinav['gk'] = ilk['katilim'][4]
            sinav['genelPuan'] = ilk['genelPuan']
            sinav['kurumPuan'] = round(sum(r['puan'] for r in karneler) / len(karneler), 3)
            sinav['sinifSeviye'] = int(Counter(re.match(r'\d+', r['sube']).group(0) for r in karneler).most_common(1)[0][0])
        kodlar = [d['k'] for d in sinav['dersler']]
        kz_dizin, kz_liste = {}, []
        # önce elle ve birebir eşleşmeler, sonra yaklaşık eşleşmeler (boşta kalan öğrencilere)
        for r in karneler:
            r['_k'], r['_y'] = eslestir(anahtar_ad(r['ad']), sinav['sinifSeviye'], liste)
        oncelik = {'elle': 0, 'birebir': 1}
        karneler.sort(key=lambda r: oncelik.get(r['_y'], 2))
        alinan = set()
        for r in karneler:
            k, yontem = r['_k'], r['_y']
            if k in alinan and yontem not in oncelik:
                k = None
            if k:
                alinan.add(k)
            if not k:
                eslesmeyen.append((dosya, r['ad']))
                continue
            if yontem != 'birebir':
                esnek.append((dosya, r['ad'], liste[k]['ad'], yontem))
            dmap = {d[0]: d for d in r['dersler']}
            kayit = {'s': sinav['id'],
                     'dy': [[dmap[c][2], dmap[c][3]] if c in dmap else [0, 0] for c in kodlar],
                     'puan': r['puan'], 'kd': r['kd'], 'gd': r['gd']}
            ad_dosya = secrets.token_hex(12)
            w = pypdf.PdfWriter()
            w.add_page(okuyucu.pages[r['sayfa'] - 1])
            with open(os.path.join(yukle, 'karneler', ad_dosya + '.pdf'), 'wb') as fh:
                w.write(fh)
            kayit['karne'] = ad_dosya
            kz = []
            for ders, kad, s_, d_, y_ in karne.karne_oku(yol, r['sayfa']):
                anah = (ders, kad)
                if anah not in kz_dizin:
                    kz_dizin[anah] = len(kz_liste)
                    kz_liste.append([ders, kad])
                kz.append([kz_dizin[anah], s_, d_, y_])
            if kz:
                kayit['kz'] = kz
                kazanim_sayisi += 1
            if any(x['s'] == sinav['id'] for x in sonuc.get(k, [])):
                esnek.append((dosya, r['ad'], liste[k]['ad'], 'UYARI: aynı denemede ikinci kez eşleşti, atlandı'))
                continue
            sonuc.setdefault(k, []).append(kayit)
        sinav['kazanimlar'] = kz_liste

    tarih = {s['id']: s['tarih'] for s in sinavlar}
    kayitlar, eksik_kimlik, sonucsuz = {}, [], []
    for k, o in liste.items():
        if not re.fullmatch(r'[1-9]\d{10}', o['tc']) or not re.fullmatch(r'\d{2}\.\d{2}\.\d{4}', o['dg']):
            eksik_kimlik.append(o['ad'])
            continue
        if k not in sonuc:
            sonucsuz.append(o['ad'])
        anahtar = hashlib.sha256(f"{tuz}|{o['tc']}|{o['dg']}".encode()).hexdigest()
        # listedeki şube alanı grup adı içeriyor ("5/4A MAT"); veliye yalnızca sınıf seviyesi gösterilir
        kayitlar[anahtar] = {'ad': o['ad'], 'sube': o['seviye'],
                             'sonuclar': sorted(sonuc.get(k, []), key=lambda x: tarih[x['s']])}
    kullanilan = {s.get('karne') for v in kayitlar.values() for s in v['sonuclar']}
    for f in os.listdir(os.path.join(yukle, 'karneler')):
        if f[:-4] not in kullanilan:
            os.remove(os.path.join(yukle, 'karneler', f))

    veri = {'surum': 2, 'olusturma': datetime.datetime.now().isoformat(timespec='seconds'),
            'tuz': tuz, 'sinavlar': {s['id']: s for s in sinavlar}, 'ogrenciler': kayitlar}
    with open(os.path.join(yukle, 'portal.json'), 'w', encoding='utf-8') as f:
        json.dump(veri, f, ensure_ascii=False, separators=(',', ':'))
    paket = os.path.join(CIKTI, 'obir-veri-yukle.zip')
    with zipfile.ZipFile(paket, 'w', zipfile.ZIP_DEFLATED) as z:
        for kok, _, dosyalar in os.walk(yukle):
            for d in dosyalar:
                tam = os.path.join(kok, d)
                z.write(tam, os.path.relpath(tam, CIKTI))
    eski = os.path.join(CIKTI, 'portal.json')
    if os.path.exists(eski):
        os.remove(eski)

    with open(os.path.join(CIKTI, 'eslesme-raporu.txt'), 'w', encoding='utf-8') as f:
        f.write(f'Liste: {liste_ad}\nOluşturma: {veri["olusturma"]}\n\nSINAVLAR\n')
        for s in sorted(sinavlar, key=lambda s: s['tarih']):
            f.write(f"  {s['tarih']}  {s['ad']} ({s['yayin']}) · {s['sinifSeviye']}. sınıf · kurumda {s['kk']} kişi\n")
        f.write(f'\nYAKLAŞIK eşleştirilenler ({len(esnek)}) — lütfen kontrol edin (PDF adı -> listedeki ad · yöntem):\n')
        f.write(''.join(f'  {d[:40]:40}  {a}  ->  {b}   [{y}]\n' for d, a, b, y in esnek))
        f.write(f"\nPDF'te olup listede BULUNAMAYANLAR ({len(eslesmeyen)}) — büyük olasılıkla dışarıdan katılanlar:\n")
        f.write(''.join(f'  {d[:40]:40}  {a}\n' for d, a in eslesmeyen))
        bos = [a for a in DUZELTME if a not in KULLANILAN_DUZELTME]
        f.write(f"\nDüzeltme dosyasında olup PDF'lerde BULUNAMAYAN adlar ({len(bos)}) — yazımı kontrol edin:\n")
        f.write(''.join(f'  {a}\n' for a in bos))
        hedefsiz = [f'{a} -> {b}' for a, b in DUZELTME.items() if b and b not in liste]
        f.write(f'\nDüzeltme dosyasında hedefi listede BULUNAMAYANLAR ({len(hedefsiz)}):\n')
        f.write(''.join(f'  {a}\n' for a in hedefsiz))
        f.write(f'\nT.C. ya da doğum tarihi eksik olduğu için portala eklenemeyenler ({len(eksik_kimlik)}):\n')
        f.write(''.join(f'  {a}\n' for a in eksik_kimlik))
        f.write(f'\nListede olup henüz hiç sonucu olmayanlar ({len(sonucsuz)}):\n')
        f.write(''.join(f'  {a}\n' for a in sonucsuz))
    # ekrana yalnızca sayılar (isim yok)
    satirlar = [
        f'sınav: {len(sinavlar)} | portal öğrencisi: {len(kayitlar)} | sonucu olan: '
        f'{sum(1 for v in kayitlar.values() if v["sonuclar"])} | yaklaşık eşleşme: {len(esnek)} | '
        f'eşleşmeyen PDF satırı: {len(eslesmeyen)} | kimliği eksik: {len(eksik_kimlik)}',
        f'karne dosyası: {len(os.listdir(os.path.join(yukle, "karneler")))} | kazanım analizi olan sonuç: '
        f'{kazanim_sayisi} | paket: {os.path.getsize(paket) // 1024} KB',
        'yaklaşık eşleşme yöntemleri: ' + str(dict(Counter(y for *_, y in esnek))),
        'eşleşmeyenlerin dağılımı: ' + str({k[:28]: v for k, v in Counter(d for d, _ in eslesmeyen).items()}),
        'karnesi bulunamayan sonuç: ' + str(sum(1 for v in kayitlar.values() for s in v['sonuclar'] if 'karne' not in s)),
        f'elle düzeltme: {len(DUZELTME)} kayıt | PDF\'te bulunamayan: {len(set(DUZELTME) - KULLANILAN_DUZELTME)}'
        f' | hedefi listede olmayan: {sum(1 for b in DUZELTME.values() if b and b not in liste)}',
        'kazanım sayısı/sınav: ' + str({s['tarih'] + '-' + str(s['sinifSeviye']): len(s['kazanimlar']) for s in sinavlar}),
    ]
    with open(os.path.join(CIKTI, 'ozet.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(satirlar))


if __name__ == '__main__':
    main()
