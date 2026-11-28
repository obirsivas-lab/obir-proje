"""
Karne sayfası okuyucu: öğrenci adı + "Derslere göre analiz" (kazanım bazında S D Y B%) tablosu.
Metin parçaları sayfa koordinatlarıyla okunur (pypdf), sayılar S / D / Y / B% sütun
başlıklarının konumuna göre eşlenir.
"""
import re, subprocess
import pypdf

DERS_BASLIK = [  # sağ sütundaki ders başlığı -> kod
    (r'^T.rk.e$', 'TÜR'), (r'^SOSYAL', 'SOS'), (r'^(Tarih|T\.\s*C\.|.nk)', 'İNK'),
    (r'^Din\b', 'DİN'), (r'^.ngilizce', 'İNG'), (r'^Matematik', 'MAT'), (r'^Fen', 'FEN'),
]

_okuyucular = {}


def _sayfa(yol, sayfa):
    if yol not in _okuyucular:
        _okuyucular[yol] = pypdf.PdfReader(yol)
    return _okuyucular[yol].pages[sayfa - 1]


def parcalar(yol, sayfa):
    p = _sayfa(yol, sayfa)
    genislik = float(p.mediabox.width)
    fr = []

    def v(t, cm, tm, fd, fs):
        if t and t.strip():
            x = cm[0] * tm[4] + cm[2] * tm[5] + cm[4]
            y = cm[1] * tm[4] + cm[3] * tm[5] + cm[5]
            fr.append((x, y, t.strip()))
    p.extract_text(visitor_text=v)
    return genislik, fr


def karne_oku(yol, sayfa):
    genislik, fr = parcalar(yol, sayfa)
    sag = [f for f in fr if f[0] >= genislik * 0.48]
    # satırlara ayır (aynı y)
    satirlar = {}
    for x, y, t in sag:
        anahtar = next((k for k in satirlar if abs(k - y) < 1.2), y)
        satirlar.setdefault(anahtar, []).append((x, t))
    kazanim, ders, sutun = [], None, None
    for y in sorted(satirlar, reverse=True):
        satir = sorted(satirlar[y])
        metinler = [t for _, t in satir]
        if metinler[-4:] == ['S', 'D', 'Y', 'B%']:
            bas = ' '.join(metinler[:-4]).strip()
            ders = next((kod for desen, kod in DERS_BASLIK if re.search(desen, bas)), None)
            sutun = [x for x, _ in satir[-4:]]
            continue
        if not ders or not sutun:
            continue
        degerler = [None] * 4
        ad = []
        for x, t in satir:
            if x >= sutun[0] - 3 and re.fullmatch(r'\d+', t):
                i = min(range(4), key=lambda i: abs(sutun[i] - x))
                if abs(sutun[i] - x) < 5 and degerler[i] is None:
                    degerler[i] = int(t)
                    continue
            if x < sutun[0] - 3:
                ad.append(t)
        ad = re.sub(r'\s+', ' ', ' '.join(ad)).strip()
        if re.match(r'^(Sözel|Sayısal)\s*\(', ad) or any(re.search(d, ad) and len(ad) < 25 for d, _ in DERS_BASLIK):
            continue
        if degerler[0] is None or degerler[1] is None:
            if ad and kazanim and kazanim[-1][0] == ders:   # alt satıra kaymış devam metni
                kazanim[-1][1] += ' ' + ad
            continue
        s, d = degerler[0], degerler[1]
        yy = degerler[2] if degerler[2] is not None else 0
        if not ad or s <= 0 or d + yy > s:
            continue
        kazanim.append([ders, ad, s, d, yy])
    return kazanim


def ogrenci_adi(yol, sayfa):
    """Karne sayfasının sol üstündeki öğrenci adı (Öğrenci / Numara / Sınıf satırının altı)."""
    r = subprocess.run(['pdftotext', '-enc', 'UTF-8', '-layout', '-f', str(sayfa), '-l', str(sayfa), yol, '-'],
                       capture_output=True)
    satirlar = r.stdout.decode('utf-8', 'replace').splitlines()
    for i, l in enumerate(satirlar):
        if re.search(r'.ğrenci\s+Numara\s+S.n.f', l):
            for l2 in satirlar[i + 1:i + 3]:
                m = re.match(r'^\s*(.+?)\s{2,}(\d+)\s+(\d{1,2}[-/]?\S*)\s*$', l2[:75].rstrip())
                if m:
                    return m.group(1).strip()
    # yedek yol: şube parçası (ör. "8-A") ile aynı satırdaki sol sütun metni
    genislik, fr = parcalar(yol, sayfa)
    if not any('DERSLERE' in t for _, _, t in fr):
        return None
    for x, y, t in fr:
        if re.fullmatch(r'\d{1,2}[-/]\S{1,4}', t) and genislik * 0.35 < x < genislik * 0.5 and y > 700:
            sol = [(x2, t2) for x2, y2, t2 in fr if abs(y2 - y) < 1.5 and x2 < genislik * 0.35 and not re.fullmatch(r'\d+', t2)]
            if sol:
                return ' '.join(t2 for _, t2 in sorted(sol)).strip()
    return None


def _sayi(t):
    return float(t.replace(',', '.'))


def karne_sonuc(yol, sayfa):
    """Karne sayfasının sol sütunundan öğrencinin tam sonucu. Okunamazsa None."""
    genislik, fr = parcalar(yol, sayfa)
    if not any('SONUÇ BELGESİ' in t for _, _, t in fr):
        return None
    sol = [f for f in fr if f[0] < genislik * 0.48]

    def satir(y0, tol=1.6):
        return sorted((x, t) for x, y, t in sol if abs(y - y0) < tol)
    # şube ve ad
    sube = next(((x, y, t) for x, y, t in sol if re.fullmatch(r'\d{1,2}[-/]\S{1,4}', t) and x > genislik * 0.4 and y > 700), None)
    if not sube:
        return None
    ad = ' '.join(t for x, t in satir(sube[1]) if x < genislik * 0.33 and not re.fullmatch(r'\d+', t)).strip()
    sonuc = {'ad': ad, 'sube': sube[2]}
    # puan satırı (LGS) ve katılımlar
    lgs = next(((x, y) for x, y, t in sol if t == 'LGS' and x < 60), None)
    kat = next(((x, y) for x, y, t in sol if t.startswith('Katılım')), None)
    if not lgs or not kat:
        return None
    sayilar = [_sayi(t) for x, t in satir(lgs[1]) if re.fullmatch(r'-?[\d.,]+', t)]
    # sıra: puan(x≈78) genelOrt(≈129) snf kurum ilçe il genel  -> x'e göre sıralı
    if len(sayilar) < 7:
        return None
    sonuc.update(puan=sayilar[0], genelPuan=sayilar[1], sd=int(sayilar[2]), kd=int(sayilar[3]), gd=int(sayilar[6]))
    k = [int(_sayi(t)) for x, t in satir(kat[1]) if re.fullmatch(r'\d+', t)]
    if len(k) < 5:
        return None
    sonuc['katilim'] = k[:5]  # sınıf, kurum, ilçe, il, genel
    # ders satırları
    dersler = []
    for x, y, t in sorted(sol, key=lambda f: -f[1]):
        if x > 40 or y > kat[1]:
            continue
        kod = next((kd for desen, kd in DERS_BASLIK if re.search(desen, t)), None)
        if not kod or any(d[0] == kod for d in dersler):
            continue
        r = [(x2, t2) for x2, t2 in satir(y) if re.fullmatch(r'-?[\d.,]+', t2)]
        sol_say = [t2 for x2, t2 in r if x2 < 215]     # soru, doğru, yanlış, net, %
        ort = [_sayi(t2) for x2, t2 in r if x2 >= 215]  # sınıf, kurum, genel ort.
        if len(sol_say) < 3:
            continue
        dersler.append([kod, int(sol_say[0]), int(sol_say[1]), int(sol_say[2])] + (ort[-3:] if len(ort) >= 3 else [None, None, None]))
    if not dersler:
        return None
    sonuc['dersler'] = dersler
    return sonuc
