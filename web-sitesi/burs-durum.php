<?php
// Obir Kurs Merkezi · bursluluk kontenjan durumu (kişisel veri içermez)
// Google E-Tablo'daki başvuru sayısını sorar; sonucu 60 sn önbellekte tutar.
header('Content-Type: application/json; charset=utf-8');
header('X-Robots-Tag: noindex');
header('Cache-Control: no-store');
require __DIR__ . '/_form-ortak.php';

$onbellek = sys_get_temp_dir() . '/obir_burs_durum.json';
if (is_file($onbellek) && filemtime($onbellek) > time() - 60) {
    echo file_get_contents($onbellek);
    exit;
}
$sonuc = ['ok' => false];
$adres = form_adresi('burs-adresi.txt');
if ($adres) {
    [$kod, $yer, $icerik] = istek($adres . '?islem=durum');
    if ($kod === 302 && $yer) [, , $icerik] = istek($yer);
    $j = json_decode((string)$icerik, true);
    if (is_array($j) && isset($j['kalan'])) {
        $sonuc = ['ok' => true, 'kontenjan' => (int)$j['kontenjan'], 'kalan' => (int)$j['kalan'], 'dolu' => (int)$j['kalan'] <= 0];
    }
}
$json = json_encode($sonuc, JSON_UNESCAPED_UNICODE);
if ($sonuc['ok']) @file_put_contents($onbellek, $json);
echo $json;
