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

def main():
    liste_ad, liste = liste_oku()
    tuz = secrets.token_hex(16)
    sinavlar, sonuc = [], {}
    eslesmeyen, esnek = [], []
    for yol in sorted(glob.glob(os.path.join(PDF_KLASOR, '*.pdf'))):
        sinav, satirlar = pdf_oku(yol)
        sinavlar.append(sinav)
        for o in satirlar:
            k = anahtar_ad(o['ad_pdf'])
            if k not in liste:
                aday = [lk for lk, lo in liste.items()
                        if lo['seviye'] == str(sinav['sinifSeviye']) and ad_uyar(k, lk)]
                if len(aday) == 1:
                    k = aday[0]
                    if liste[k]['ad'] != o['ad_pdf']:
                        esnek.append((os.path.basename(yol), o['ad_pdf'], liste[k]['ad']))
                else:
                    eslesmeyen.append((os.path.basename(yol), o['ad_pdf']))
                    continue
            sonuc.setdefault(k, []).append({'s': sinav['id'], 'dy': o['dy'], 'puan': o['puan'],
                                             'kd': o['kd'], 'gd': o['gd']})
    tarih = {s['id']: s['tarih'] for s in sinavlar}
    kayitlar, eksik_kimlik, sonucsuz = {}, [], []
    for k, o in liste.items():
        if not re.fullmatch(r'[1-9]\d{10}', o['tc']) or not re.fullmatch(r'\d{2}\.\d{2}\.\d{4}', o['dg']):
            eksik_kimlik.append(o['ad']); continue
        if k not in sonuc:
            sonucsuz.append(o['ad'])
        anahtar = hashlib.sha256(f"{tuz}|{o['tc']}|{o['dg']}".encode()).hexdigest()
        # listedeki şube alanı grup adı içeriyor ("5/4A MAT"); veliye yalnızca sınıf seviyesi gösterilir
        kayitlar[anahtar] = {'ad': o['ad'], 'sube': o['seviye'],
                             'sonuclar': sorted(sonuc.get(k, []), key=lambda x: tarih[x['s']])}
    veri = {'surum': 1, 'olusturma': datetime.datetime.now().isoformat(timespec='seconds'),
            'tuz': tuz, 'sinavlar': {s['id']: s for s in sinavlar}, 'ogrenciler': kayitlar}
    os.makedirs(CIKTI, exist_ok=True)
    with open(os.path.join(CIKTI, 'portal.json'), 'w', encoding='utf-8') as f:
        json.dump(veri, f, ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(CIKTI, 'eslesme-raporu.txt'), 'w', encoding='utf-8') as f:
        f.write(f'Liste: {liste_ad}\nOluşturma: {veri["olusturma"]}\n\nSINAVLAR\n')
        for s in sorted(sinavlar, key=lambda s: s['tarih']):
            f.write(f"  {s['tarih']}  {s['ad']} ({s['yayin']}) · {s['sinifSeviye']}. sınıf · kurumda {s['kk']} kişi\n")
        f.write(f'\nYAKLAŞIK eşleştirilenler ({len(esnek)}) — kontrol edin (PDF adı -> listedeki ad):\n')
        f.write(''.join(f'  {d[:40]:40}  {a}  ->  {b}\n' for d, a, b in esnek))
        f.write(f"\nPDF'te olup listede BULUNAMAYANLAR ({len(eslesmeyen)}) — dışarıdan katılanlar ya da yazım farkı:\n")
        f.write(''.join(f'  {d[:40]:40}  {a}\n' for d, a in eslesmeyen))
        f.write(f'\nT.C. ya da doğum tarihi eksik olduğu için portala eklenemeyenler ({len(eksik_kimlik)}):\n')
        f.write(''.join(f'  {a}\n' for a in eksik_kimlik))
        f.write(f'\nListede olup henüz hiç sonucu olmayanlar ({len(sonucsuz)}):\n')
        f.write(''.join(f'  {a}\n' for a in sonucsuz))
    # ekrana yalnızca sayılar (isim yok)
    print(f'sınav: {len(sinavlar)} | portal öğrencisi: {len(kayitlar)} | sonucu olan: '
          f'{sum(1 for v in kayitlar.values() if v["sonuclar"])} | yaklaşık eşleşme: {len(esnek)} | '
          f'eşleşmeyen PDF satırı: {len(eslesmeyen)} | kimliği eksik: {len(eksik_kimlik)}')
    for s in sorted(sinavlar, key=lambda s: s['tarih']):
        print(f"  {s['tarih']} {s['ad']:27} {s['sinifSeviye']}.sınıf kurum {s['kk']:>3} genel {s['gk']:>6} "
              f"{[d['k'] + '/' + str(d['soru']) for d in s['dersler']]} genelOrt:{'var' if s['go'] else 'YOK'}")
    sayac = Counter(d for d, _ in eslesmeyen)
    print('eşleşmeyenlerin dağılımı:', {k[:28]: v for k, v in sayac.items()})

if __name__ == '__main__':
    main()
