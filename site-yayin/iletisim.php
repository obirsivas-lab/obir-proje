<?php
// Obir Kurs Merkezi - bilgi formu.
// Gelen başvuruyu kurumun Google E-Tablosuna iletir (Google bildirim e-postası da gönderir);
// sitenin sunucusunda hiçbir kişisel veri SAKLANMAZ.
// (Yalnızca kötüye kullanımı önlemek için IP'nin tek yönlü özeti 1 saat geçici tutulur.)

header('Content-Type: application/json; charset=utf-8');
header('X-Robots-Tag: noindex');


function cevap($ok, $mesaj, $kod = 200) {
    http_response_code($kod);
    echo json_encode(['ok' => $ok, 'mesaj' => $mesaj], JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') cevap(false, 'Geçersiz istek.', 405);

// Bot tuzağı: görünmez alan doluysa ya da form 3 saniyeden kısa sürede gönderildiyse sessizce "tamam" de.
if (!empty($_POST['web_sitesi'])) cevap(true, 'Teşekkürler.');
$baslangic = (int)($_POST['t'] ?? 0);
if ($baslangic > 0 && (time() * 1000 - $baslangic) < 3000) cevap(true, 'Teşekkürler.');

// Basit hız sınırı: aynı IP'den saatte en fazla 5 gönderim.
$ip = $_SERVER['HTTP_CF_CONNECTING_IP'] ?? $_SERVER['REMOTE_ADDR'] ?? '';
$iz = sys_get_temp_dir() . '/obir_form_' . hash('sha256', 'obir' . $ip);
$kayitlar = [];
if (is_file($iz)) {
    $kayitlar = array_filter(explode(',', (string)@file_get_contents($iz)), function ($z) {
        return (int)$z > time() - 3600;
    });
}
if (count($kayitlar) >= 5) cevap(false, 'Çok fazla deneme yapıldı. Lütfen bizi telefonla arayın: 0533 229 80 58', 429);
$kayitlar[] = time();
@file_put_contents($iz, implode(',', $kayitlar));

function temiz($anahtar, $uzunluk) {
    $d = trim((string)($_POST[$anahtar] ?? ''));
    $d = str_replace(["\r", "\0"], '', $d);
    return mb_substr($d, 0, $uzunluk, 'UTF-8');
}

$ad     = temiz('ad', 80);
$tel    = temiz('tel', 30);
$prog   = temiz('program', 20);
$sinif  = temiz('sinif', 5);
$mesaj  = temiz('mesaj', 1000);
$kvkk   = !empty($_POST['kvkk']);
$kaynak = temiz('kaynak', 30);

$programlar = ['genel' => 'Genel Program', 'kulup' => 'Matematik Kulübü', 'lgs' => 'LGS Hazırlık', 'odev' => 'Ödev Yardımı', 'burs' => 'Bursluluk'];

$telRakam = preg_replace('/\D/', '', $tel);
if (mb_strlen($ad, 'UTF-8') < 3 || strpos($ad, "\n") !== false) cevap(false, 'Lütfen adınızı ve soyadınızı yazın.', 422);
if (strlen($telRakam) < 10 || strlen($telRakam) > 12) cevap(false, 'Lütfen geçerli bir telefon numarası yazın.', 422);
if (!$kvkk) cevap(false, 'Lütfen KVKK onay kutusunu işaretleyin.', 422);
if (!isset($programlar[$prog])) $prog = 'genel';
if (!in_array($sinif, ['4', '5', '6', '7', '8'], true)) $sinif = '-';

// WhatsApp'tan tek tıkla yazabilmek için numarayı 90 ile başlat.
$wa = $telRakam;
if (strlen($wa) === 10) $wa = '90' . $wa;
elseif (strlen($wa) === 11 && $wa[0] === '0') $wa = '9' . $wa;

// ---- Google E-Tablo'ya ilet ----
require __DIR__ . '/_form-ortak.php';

[$gitti, $neden] = tabloya_gonder([
    'ad' => $ad, 'tel' => $tel, 'program' => $programlar[$prog],
    'sinif' => $sinif === '-' ? '' : $sinif, 'mesaj' => $mesaj, 'kaynak' => $kaynak ?: 'site',
]);
if (!$gitti) header('X-Obir-Neden: ' . $neden);
if (!$gitti) cevap(false, 'Şu an gönderilemedi. Lütfen bizi arayın ya da WhatsApp\'tan yazın: 0533 229 80 58', 500);
cevap(true, 'Teşekkürler! En kısa sürede sizi arayacağız.');
