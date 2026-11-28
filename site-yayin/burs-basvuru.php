<?php
// Obir Kurs Merkezi · Bursluluk Sınavı başvurusu
// Başvuruyu kurumun Google E-Tablosundaki "Bursluluk Başvuruları" sayfasına iletir.
// Sitenin sunucusunda hiçbir kişisel veri SAKLANMAZ.

header('Content-Type: application/json; charset=utf-8');
header('X-Robots-Tag: noindex');
header('Cache-Control: no-store');

function cevap($ok, $mesaj, $kod = 200, $ek = []) {
    http_response_code($kod);
    echo json_encode(['ok' => $ok, 'mesaj' => $mesaj] + $ek, JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') cevap(false, 'Geçersiz istek.', 405);
require __DIR__ . '/_form-ortak.php';

// Bot tuzağı ve çok hızlı gönderim
if (!empty($_POST['web_sitesi'])) cevap(true, 'Teşekkürler.', 200, ['no' => 'BS27-0000']);
$baslangic = (int)($_POST['t'] ?? 0);
if ($baslangic > 0 && (time() * 1000 - $baslangic) < 4000) cevap(true, 'Teşekkürler.', 200, ['no' => 'BS27-0000']);
if (!hiz_siniri('burs', 5)) cevap(false, 'Çok fazla başvuru denemesi yapıldı. Lütfen bizi arayın: 0533 229 80 58', 429);

function al($k, $n) {
    $d = trim(str_replace(["\r", "\n", "\0"], ' ', (string)($_POST[$k] ?? '')));
    return mb_substr($d, 0, $n, 'UTF-8');
}
$ogrenci = al('ogrenci', 80);
$okul    = al('okul', 100);
$veli    = al('veli', 80);
$tel     = al('tel', 20);
$sinif   = al('sinif', 2);
$telR    = preg_replace('/\D/', '', $tel);
$kvkk    = !empty($_POST['kvkk']);
$ticari  = !empty($_POST['ticari']) ? 'evet' : 'hayır';
$bulusma = al('bulusma', 5) === 'hayir' ? 'hayır' : 'evet';

if (!in_array($sinif, ['4', '5', '6', '7'], true)) cevap(false, 'Lütfen sınıf seçin.', 422);
if (mb_strlen($ogrenci, 'UTF-8') < 3) cevap(false, 'Lütfen öğrencinin adını soyadını yazın.', 422);
if (mb_strlen($okul, 'UTF-8') < 2) cevap(false, 'Lütfen okulu yazın.', 422);
if (mb_strlen($veli, 'UTF-8') < 3) cevap(false, 'Lütfen veli adını soyadını yazın.', 422);
if (!preg_match('/^05\d{9}$/', $telR)) cevap(false, 'Lütfen 05 ile başlayan 11 haneli cep telefonu yazın.', 422);
if (!$kvkk) cevap(false, 'Lütfen KVKK onay kutusunu işaretleyin.', 422);

$programAd = ['genel' => 'Genel Program', 'kulup' => 'Matematik Kulübü', 'odev' => 'Ödev Yardımı', 'lgs' => 'LGS Hazırlık', 'karar' => 'Henüz karar vermedi'];
$secilen = array_filter(array_map('trim', explode(',', al('program', 100))), function ($k) use ($programAd) { return isset($programAd[$k]); });
$program = implode(', ', array_map(function ($k) use ($programAd) { return $programAd[$k]; }, $secilen)) ?: '-';

$no = 'BS27-' . strtoupper(substr(bin2hex(random_bytes(3)), 0, 5));

[$gitti, $neden] = tabloya_gonder([
    'tur' => 'burs', 'no' => $no, 'ogrenci' => $ogrenci, 'sinif' => $sinif, 'okul' => $okul,
    'veli' => $veli, 'tel' => $tel, 'program' => $program, 'bulusma' => $bulusma, 'ticari' => $ticari,
], 'burs-adresi.txt');   // bursluluk ayrı tabloda: obir-veri/burs-adresi.txt
if (!$gitti) {
    header('X-Obir-Neden: ' . $neden);
    cevap(false, 'Başvuru şu an iletilemedi.', 500);
}
cevap(true, 'Başvurunuz alındı.', 200, ['no' => $no]);
