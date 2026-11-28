<?php
// Obir Kurs Merkezi · veli portalı karne indirme
// sonuc-karne.php?t=<oturum anahtarı>&s=<sınav kimliği>
// Oturum anahtarı, başarılı girişte sonuc-api.php tarafından verilir (2 saat geçerli, imzalı).
// Karneler web'den erişilemeyen obir-veri/karneler/ klasöründe, tahmin edilemez adlarla durur.

header('X-Robots-Tag: noindex, nofollow');
header('Cache-Control: private, no-store, max-age=0');
header('X-Content-Type-Options: nosniff');

function hata($mesaj, $kod) {
    http_response_code($kod);
    header('Content-Type: text/html; charset=utf-8');
    echo '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
       . '<body style="font-family:system-ui,sans-serif;background:#1D1D20;color:#F7F5EE;display:grid;place-items:center;min-height:100vh;margin:0;padding:20px;text-align:center">'
       . '<div><p style="font-size:18px;font-weight:700;max-width:420px">' . htmlspecialchars($mesaj) . '</p>'
       . '<a href="sonuc.html" style="color:#F6D70C;font-weight:800">Sonuç portalına dön</a></div></body>';
    exit;
}

$t = (string)($_GET['t'] ?? '');
$s = (string)($_GET['s'] ?? '');
if (!preg_match('/^([a-f0-9]{64})\.(\d{10})\.([a-f0-9]{64})$/', $t, $m) || !preg_match('/^[a-f0-9]{10}$/', $s)) {
    hata('Geçersiz bağlantı. Lütfen portala yeniden giriş yapın.', 400);
}
[, $anahtar, $bitis, $imza] = $m;
if ((int)$bitis < time()) hata('Oturum süresi doldu. Lütfen portala yeniden giriş yapın.', 403);

$adaylar = [];
if (!empty($_SERVER['DOCUMENT_ROOT'])) $adaylar[] = dirname(rtrim($_SERVER['DOCUMENT_ROOT'], '/')) . '/obir-veri';
$adaylar[] = dirname(__DIR__) . '/obir-veri';
$klasor = null;
foreach ($adaylar as $a) { if (is_file($a . '/portal.json')) { $klasor = $a; break; } }
if (!$klasor) hata('Sonuç portalı şu an güncelleniyor. Lütfen biraz sonra tekrar deneyin.', 503);
$veri = json_decode((string)file_get_contents($klasor . '/portal.json'), true);
if (!is_array($veri) || empty($veri['tuz'])) hata('Sonuç portalı şu an güncelleniyor.', 503);

$beklenen = hash_hmac('sha256', $anahtar . '|' . $bitis, $veri['tuz'] . '|karne');
if (!hash_equals($beklenen, $imza)) hata('Oturum geçersiz. Lütfen portala yeniden giriş yapın.', 403);
if (!isset($veri['ogrenciler'][$anahtar])) hata('Kayıt bulunamadı. Lütfen portala yeniden giriş yapın.', 404);

$ogr = $veri['ogrenciler'][$anahtar];
$kayit = null;
foreach ($ogr['sonuclar'] as $r) { if ($r['s'] === $s) { $kayit = $r; break; } }
if (!$kayit || empty($kayit['karne']) || !preg_match('/^[a-f0-9]{24}$/', $kayit['karne'])) {
    hata('Bu deneme için karne bulunamadı.', 404);
}
$dosya = $klasor . '/karneler/' . $kayit['karne'] . '.pdf';
if (!is_file($dosya)) hata('Bu deneme için karne bulunamadı.', 404);

// dosya adı: Ad-Soyad_Sinav_Tarih.pdf
$sinav = $veri['sinavlar'][$s] ?? ['ad' => 'Deneme', 'tarih' => ''];
$ad = $ogr['ad'] . ' ' . $sinav['ad'] . ' ' . $sinav['tarih'];
$tr = ['ç'=>'c','Ç'=>'C','ğ'=>'g','Ğ'=>'G','ı'=>'i','İ'=>'I','ö'=>'o','Ö'=>'O','ş'=>'s','Ş'=>'S','ü'=>'u','Ü'=>'U'];
$ascii = trim(preg_replace('/[^A-Za-z0-9.]+/', '-', strtr($ad, $tr)), '-') . '.pdf';
header('Content-Type: application/pdf');
header('Content-Length: ' . filesize($dosya));
header("Content-Disposition: attachment; filename=\"$ascii\"; filename*=UTF-8''" . rawurlencode(trim($ad) . '.pdf'));
readfile($dosya);
