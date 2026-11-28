"""
Yerel test sunucusu: web-sitesi/ klasörünü sunar ve sonuc-api.php'yi taklit eder.
Gerçek öğrenci adları/T.C. KULLANILMAZ: portal.json'daki sınav bilgileri ve isimsiz sonuçlarla
üç sahte test öğrencisi oluşturur:
  10000000146 / 14.03.2015  -> en çok denemesi olan kayıt (isim: Test Öğrenci A)
  10000000078 / 01.01.2014  -> tek denemesi olan kayıt   (isim: Test Öğrenci B)
  10000000214 / 02.02.2013  -> hiç sonucu olmayan kayıt  (isim: Test Öğrenci C)
  python -I portal-araclari/test_sunucu.py   ->  http://localhost:8125/sonuc.html
"""
import json, os, http.server, urllib.parse

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI_KLASOR = os.path.join(KOK, 'portal-veri', 'obir-veri')
veri = json.load(open(os.path.join(VERI_KLASOR, 'portal.json'), encoding='utf-8'))
kayitlar = sorted(veri['ogrenciler'].values(), key=lambda o: -len(o['sonuclar']))
tek = next(o for o in kayitlar if len(o['sonuclar']) == 1)
TEST = {
    ('10000000146', '14.03.2015'): {'ad': 'Test Öğrenci A', 'sube': kayitlar[0]['sube'], 'sonuclar': kayitlar[0]['sonuclar']},
    ('10000000078', '01.01.2014'): {'ad': 'Test Öğrenci B', 'sube': tek['sube'], 'sonuclar': tek['sonuclar']},
    ('10000000214', '02.02.2013'): {'ad': 'Test Öğrenci C', 'sube': '7-A', 'sonuclar': []},
}

class Isleyici(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=os.path.join(KOK, 'web-sitesi'), **k)
    def do_GET(self):
        if self.path.startswith('/sonuc-karne.php'):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            ogr = {'testA': ('10000000146', '14.03.2015'), 'testB': ('10000000078', '01.01.2014')}.get(q.get('t', [''])[0])
            o = TEST.get(ogr) if ogr else None
            kayit = next((x for x in (o or {}).get('sonuclar', []) if x['s'] == q.get('s', [''])[0]), None)
            if not kayit or not kayit.get('karne'):
                self.send_error(404); return
            b = open(os.path.join(VERI_KLASOR, 'karneler', kayit['karne'] + '.pdf'), 'rb').read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Disposition', 'attachment; filename="karne.pdf"')
            self.send_header('Content-Length', str(len(b)))
            self.end_headers(); self.wfile.write(b); return
        return super().do_GET()
    def do_POST(self):
        if not self.path.startswith('/sonuc-api.php'):
            self.send_error(404); return
        n = int(self.headers.get('Content-Length', 0))
        govde = self.rfile.read(n)
        tip = self.headers.get('Content-Type', '')
        alan = {}
        if 'multipart' in tip:
            sinir = tip.split('boundary=')[1].encode()
            for parca in govde.split(b'--' + sinir):
                if b'name="' in parca:
                    ad = parca.split(b'name="')[1].split(b'"')[0].decode()
                    alan[ad] = parca.split(b'\r\n\r\n', 1)[1].rsplit(b'\r\n', 1)[0].decode()
        else:
            alan = {k: v[0] for k, v in urllib.parse.parse_qs(govde.decode()).items()}
        o = TEST.get((alan.get('tc', ''), alan.get('dt', '')))
        if not o:
            c, kod = {'ok': False, 'mesaj': 'Bu bilgilerle kayıtlı öğrenci bulunamadı. T.C. kimlik numarasını ve doğum tarihini kontrol edin. (4 deneme hakkınız kaldı.)'}, 404
        else:
            sonuclar = [dict(x, karne=bool(x.get('karne'))) for x in o['sonuclar']]
            c = {'ok': True, 'ogrenci': {'ad': o['ad'], 'sube': o['sube']}, 'sonuclar': sonuclar, 'oturum': 'test' + o['ad'][-1],
                 'sinavlar': {s['s']: veri['sinavlar'][s['s']] for s in o['sonuclar']}, 'guncelleme': veri['olusturma']}
            kod = 200
        b = json.dumps(c, ensure_ascii=False).encode()
        self.send_response(kod)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

if __name__ == '__main__':
    print('http://localhost:8125/sonuc.html')
    http.server.ThreadingHTTPServer(('127.0.0.1', 8125), Isleyici).serve_forever()
