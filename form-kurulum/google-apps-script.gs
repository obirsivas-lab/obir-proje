/**
 * Obir Kurs Merkezi · web sitesi bilgi formu
 * Gelen her başvuruyu bu E-Tablo'ya satır olarak yazar ve obirsivas@gmail.com'a bildirim gönderir.
 * Kurulum adımları: form-kurulum/KURULUM.md
 */
const BILDIRIM = 'obirsivas@gmail.com';
const SAYFA = 'Başvurular';
const BASLIKLAR = ['Tarih', 'Veli', 'Telefon', 'WhatsApp', 'Program', 'Sınıf', 'Mesaj', 'Kaynak', 'Arandı mı?', 'Not'];

function doPost(e) {
  const p = (e && e.parameter) || {};
  // Basit bot tuzağı
  if (p.web_sitesi) return cevap(true);
  const ad = String(p.ad || '').slice(0, 80).trim();
  const tel = String(p.tel || '').slice(0, 30).trim();
  const rakam = tel.replace(/\D/g, '');
  if (ad.length < 3 || rakam.length < 10) return cevap(false, 'eksik');

  const kilit = LockService.getScriptLock();
  kilit.waitLock(10000);
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sh = ss.getSheetByName(SAYFA);
    if (!sh) {
      sh = ss.insertSheet(SAYFA);
      sh.appendRow(BASLIKLAR);
      sh.getRange(1, 1, 1, BASLIKLAR.length).setFontWeight('bold').setBackground('#F6D70C');
      sh.setFrozenRows(1);
    }
    let wa = rakam;
    if (wa.length === 10) wa = '90' + wa; else if (wa.length === 11 && wa[0] === '0') wa = '9' + wa;
    const tarih = Utilities.formatDate(new Date(), 'Europe/Istanbul', 'dd.MM.yyyy HH:mm');
    // Başına ' koyarak formül enjeksiyonunu engelle
    const g = s => { s = String(s || ''); return /^[=+\-@]/.test(s) ? "'" + s : s; };
    sh.appendRow([tarih, g(ad), g(tel), 'https://wa.me/' + wa, g(p.program), g(p.sinif), g(String(p.mesaj || '').slice(0, 1000)), g(p.kaynak), '', '']);

    MailApp.sendEmail({
      to: BILDIRIM,
      subject: 'Bilgi talebi: ' + ad + ' · ' + (p.program || '-') + (p.sinif ? ' · ' + p.sinif + '. sınıf' : ''),
      body: 'Web sitesinden yeni bilgi talebi\n\n' +
            'Veli     : ' + ad + '\n' +
            'Telefon  : ' + tel + '\n' +
            'WhatsApp : https://wa.me/' + wa + '\n' +
            'Program  : ' + (p.program || '-') + '\n' +
            'Sınıf    : ' + (p.sinif ? p.sinif + '. sınıf' : '-') + '\n' +
            'Mesaj    : ' + (p.mesaj || '-') + '\n' +
            'Tarih    : ' + tarih + '\n\n' +
            'Tüm başvurular: ' + ss.getUrl()
    });
  } finally {
    kilit.releaseLock();
  }
  return cevap(true);
}

function cevap(ok, neden) {
  return ContentService.createTextOutput(JSON.stringify({ ok: ok, neden: neden || '' }))
    .setMimeType(ContentService.MimeType.JSON);
}
