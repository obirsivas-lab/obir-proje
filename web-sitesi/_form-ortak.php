<?php
// Ortak form yardımcıları (iletisim.php ve burs-basvuru.php kullanır). Doğrudan açılmaz.
if (realpath($_SERVER['SCRIPT_FILENAME'] ?? '') === realpath(__FILE__)) { http_response_code(404); exit; }

// Apps Script adresi koda yazılmaz (site kodu herkese açık): public_html'in yanındaki obir-veri/form-adresi.txt
function form_adresi() {
    $adaylar = [];
    if (!empty($_SERVER['DOCUMENT_ROOT'])) $adaylar[] = dirname(rtrim($_SERVER['DOCUMENT_ROOT'], '/')) . '/obir-veri/form-adresi.txt';
    $adaylar[] = dirname(__DIR__) . '/obir-veri/form-adresi.txt';
    foreach ($adaylar as $a) {
        if (is_file($a)) {
            $u = trim((string)file_get_contents($a));
            if (preg_match('#^https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec$#', $u)) return $u;
        }
    }
    return null;
}

function istek($url, $govde = null) {
    // POST (govde verilirse) ya da GET; yönlendirmeyi izlemez. [kod, Location, gövde] döner.
    if (function_exists('curl_init')) {
        $c = curl_init($url);
        curl_setopt_array($c, [CURLOPT_RETURNTRANSFER => true, CURLOPT_HEADER => true, CURLOPT_TIMEOUT => 15,
                               CURLOPT_FOLLOWLOCATION => false, CURLOPT_SSL_VERIFYPEER => true]);
        if ($govde !== null) { curl_setopt($c, CURLOPT_POST, true); curl_setopt($c, CURLOPT_POSTFIELDS, $govde); }
        $yanit = curl_exec($c);
        if ($yanit === false) { curl_close($c); return [0, null, '']; }
        $bs = curl_getinfo($c, CURLINFO_HEADER_SIZE);
        $kod = curl_getinfo($c, CURLINFO_HTTP_CODE);
        curl_close($c);
        $bas = substr($yanit, 0, $bs);
        $yer = preg_match('/^Location:\s*(\S+)/mi', $bas, $m) ? $m[1] : null;
        return [$kod, $yer, substr($yanit, $bs)];
    }
    $baglam = stream_context_create(['http' => [
        'method' => $govde !== null ? 'POST' : 'GET', 'timeout' => 15, 'follow_location' => 0, 'ignore_errors' => true,
        'header' => $govde !== null ? "Content-Type: application/x-www-form-urlencoded\r\n" : '',
        'content' => $govde ?? '']]);
    $icerik = @file_get_contents($url, false, $baglam);
    $kod = 0; $yer = null;
    foreach ($http_response_header ?? [] as $h) {
        if (preg_match('#^HTTP/\S+\s+(\d+)#', $h, $m)) $kod = (int)$m[1];
        if (preg_match('/^Location:\s*(\S+)/i', $h, $m)) $yer = $m[1];
    }
    return [$kod, $yer, (string)$icerik];
}


// Veriyi Apps Script'e gönderir. Dönüş: [başarılı mı, neden, Apps Script yanıtı]
function tabloya_gonder(array $alanlar) {
    $adres = form_adresi();
    if (!$adres) return [false, 'adres-yok', null];
    [$kod, $yer, $icerik] = istek($adres, http_build_query($alanlar));
    if ($kod === 302 && $yer) {
        [, , $icerik2] = istek($yer);
        $j = json_decode($icerik2, true);
        if (!is_array($j)) return [true, '', null];   // kayıt yapıldı, yanıt okunamadı
        return [!empty($j['ok']), empty($j['ok']) ? 'script:' . ($j['neden'] ?? '?') : '', $j];
    }
    if ($kod === 200) {
        $j = json_decode($icerik, true);
        return [!empty($j['ok']), empty($j['ok']) ? 'script-200' : '', $j];
    }
    return [false, 'http-' . $kod, null];
}

// Aynı IP'den saatte en fazla $sinir gönderim
function hiz_siniri($ad, $sinir = 5) {
    $ip = $_SERVER['HTTP_CF_CONNECTING_IP'] ?? $_SERVER['REMOTE_ADDR'] ?? '';
    $iz = sys_get_temp_dir() . '/obir_' . $ad . '_' . hash('sha256', 'obir' . $ip);
    $kayitlar = [];
    if (is_file($iz)) {
        $kayitlar = array_filter(explode(',', (string)@file_get_contents($iz)), function ($z) { return (int)$z > time() - 3600; });
    }
    if (count($kayitlar) >= $sinir) return false;
    $kayitlar[] = time();
    @file_put_contents($iz, implode(',', $kayitlar));
    return true;
}
