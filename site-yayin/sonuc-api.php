<?php
// Obir Kurs Merkezi · veli sonuç portalı servisi
// Öğrencinin T.C. kimlik no + doğum tarihini alır, YALNIZCA o öğrencinin sonuçlarını döndürür.
//
// Veri dosyası web'den erişilemeyen bir yerde durur:  public_html'in YANINDA  obir-veri/portal.json
// Bu dosya GitHub'a gitmez; bilgisayardaki portal-araclari/olustur.py ile üretilip cPanel'den yüklenir.
// Dosyada T.C. ve doğum tarihi YOKTUR; öğrenciler tuzlu SHA-256 özetiyle bulunur.
// Sunucuda T.C. / doğum tarihi KAYDEDİLMEZ, günlüğe yazılmaz.

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, max-age=0');
header('X-Robots-Tag: noindex, nofollow');
header('X-Content-Type-Options: nosniff');

function cevap($veri, $kod = 200) {
    http_response_code($kod);
    echo json_encode($veri, JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') cevap(['ok' => false, 'mesaj' => 'Geçersiz istek.'], 405);

// ---- kaba kuvvet koruması: aynı IP'den 5 hatalı denemede 15 dakika kilit ----
const HATA_SINIRI = 5;
const KILIT_SN    = 900;
$ip = $_SERVER['HTTP_CF_CONNECTING_IP'] ?? $_SERVER['REMOTE_ADDR'] ?? '';
$iz = sys_get_temp_dir() . '/obir_portal_' . hash('sha256', 'obir-portal' . $ip);
$hatalar = [];
if (is_file($iz)) {
    $hatalar = array_values(array_filter(explode(',', (string)@file_get_contents($iz)), function ($z) {
        return (int)$z > time() - KILIT_SN;
    }));
}
if (count($hatalar) >= HATA_SINIRI) {
    $kalan = max(1, (int)ceil(((int)min($hatalar) + KILIT_SN - time()) / 60));
    cevap(['ok' => false, 'mesaj' => "Çok fazla hatalı deneme yapıldı. Güvenliğiniz için giriş $kalan dakika kapalı."], 429);
}
function hata_say($iz, $hatalar) {
    $hatalar[] = time();
    @file_put_contents($iz, implode(',', $hatalar), LOCK_EX);
    return HATA_SINIRI - count($hatalar);
}

// ---- girdi kontrolü ----
$tc = preg_replace('/\D/', '', (string)($_POST['tc'] ?? ''));
$dt = trim((string)($_POST['dt'] ?? ''));

function tc_gecerli($t) {
    if (!preg_match('/^[1-9]\d{10}$/', $t)) return false;
    $d = array_map('intval', str_split($t));
    $o = (($d[0] + $d[2] + $d[4] + $d[6] + $d[8]) * 7 - ($d[1] + $d[3] + $d[5] + $d[7])) % 10;
    if ((($o % 10) + 10) % 10 !== $d[9]) return false;
    return array_sum(array_slice($d, 0, 10)) % 10 === $d[10];
}
if (!tc_gecerli($tc)) cevap(['ok' => false, 'mesaj' => 'T.C. Kimlik Numarası geçerli görünmüyor, lütfen kontrol edin.', 'alan' => 'tc'], 422);
if (!preg_match('/^(\d{2})\.(\d{2})\.(\d{4})$/', $dt, $m) || !checkdate((int)$m[2], (int)$m[1], (int)$m[3])) {
    cevap(['ok' => false, 'mesaj' => 'Doğum tarihini GG.AA.YYYY biçiminde girin.', 'alan' => 'dt'], 422);
}

// ---- veri dosyası ----
$adaylar = [];
if (!empty($_SERVER['DOCUMENT_ROOT'])) $adaylar[] = dirname(rtrim($_SERVER['DOCUMENT_ROOT'], '/')) . '/obir-veri/portal.json';
$adaylar[] = dirname(__DIR__) . '/obir-veri/portal.json';
$dosya = null;
foreach ($adaylar as $a) { if (is_file($a)) { $dosya = $a; break; } }
if (!$dosya) cevap(['ok' => false, 'mesaj' => 'Sonuç portalı şu an güncelleniyor. Lütfen biraz sonra tekrar deneyin.'], 503);
$veri = json_decode((string)file_get_contents($dosya), true);
if (!is_array($veri) || empty($veri['tuz']) || !isset($veri['ogrenciler'])) {
    cevap(['ok' => false, 'mesaj' => 'Sonuç portalı şu an güncelleniyor. Lütfen biraz sonra tekrar deneyin.'], 503);
}

$anahtar = hash('sha256', $veri['tuz'] . '|' . $tc . '|' . $dt);
if (!isset($veri['ogrenciler'][$anahtar])) {
    usleep(400000); // deneme hızını yavaşlat
    $kalan = hata_say($iz, $hatalar);
    $ek = $kalan > 0 ? " ($kalan deneme hakkınız kaldı.)" : '';
    cevap(['ok' => false, 'mesaj' => 'Bu bilgilerle kayıtlı öğrenci bulunamadı. T.C. kimlik numarasını ve doğum tarihini kontrol edin.' . $ek], 404);
}
@unlink($iz); // başarılı girişte sayaç sıfırlanır

$ogr = $veri['ogrenciler'][$anahtar];
$sinavlar = [];
foreach ($ogr['sonuclar'] as $s) {
    if (isset($veri['sinavlar'][$s['s']])) $sinavlar[$s['s']] = $veri['sinavlar'][$s['s']];
}
cevap([
    'ok'        => true,
    'ogrenci'   => ['ad' => $ogr['ad'], 'sube' => $ogr['sube']],
    'sonuclar'  => $ogr['sonuclar'],
    'sinavlar'  => $sinavlar,
    'guncelleme'=> $veri['olusturma'] ?? null,
]);
