// index.html, compositions/bg.html ve compositions/captions.html dosyalarını
// assets/vo/vo-words-fast.json kelime zamanlarından üretir. Sahneler (s1–s4) elle yazılır.
// Kullanım: node tools/build.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const W = JSON.parse(fs.readFileSync(path.join(root, "assets/vo/vo-words-fast.json"), "utf8"));

const scenes = [
  { id: "s1", vo: "l1", start: 0.0, dur: 3.9, off: 0.15 },
  { id: "s2", vo: "l2", start: 3.9, dur: 3.5, off: 0.1 },
  { id: "s3", vo: "l3", start: 7.4, dur: 5.7, off: 0.1 },
  { id: "s4", vo: "l4", start: 13.1, dur: 4.4, off: 0.1 },
];
const TOTAL = 17.5;
const f = (n) => n.toFixed(2);

const sfx = [
  ["pop", 0.89], ["pop", 1.48], ["pop", 1.95], ["pop", 2.51],
  ["whoosh-short", 3.9], ["click-soft", 4.6], ["click-soft", 4.9], ["click-soft", 5.2], ["click-soft", 5.5], ["pop", 6.65],
  ["whoosh-short", 7.4], ["pop", 8.9], ["pop", 9.9], ["pop", 11.3],
  ["whoosh-short", 13.1], ["sparkle", 13.5], ["click-soft", 16.15],
];
const sfxDur = { "click-soft": 0.28, pop: 0.72, "whoosh-short": 0.57, sparkle: 1.8 };
const sfxTrack = { "click-soft": 5, pop: 7, "whoosh-short": 8, sparkle: 6 };

let idx = `<!doctype html>
<html lang="tr">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html, body { margin:0; width:1080px; height:1920px; overflow:hidden; background:#1D1D20; }
#root { position:relative; width:100%; height:100%; }
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="${TOTAL}" data-width="1080" data-height="1920">
<div id="bg" data-composition-id="bg" data-composition-src="compositions/bg.html" data-start="0" data-duration="${TOTAL}" data-track-index="0" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:0"></div>
`;
for (const s of scenes)
  idx += `<div id="${s.id}" data-composition-id="${s.id}" data-composition-src="compositions/${s.id}.html" data-start="${s.start}" data-duration="${s.dur}" data-track-index="1" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:1"></div>\n`;
idx += `<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="${TOTAL}" data-track-index="2" data-track-kind="captions" data-width="1080" data-height="1920" style="z-index:6"></div>\n`;
scenes.forEach((s, i) => {
  idx += `<audio id="vo${i + 1}" class="clip" src="assets/vo/${s.vo}f.wav" data-start="${f(s.start + s.off)}" data-duration="${W[s.vo].duration.toFixed(3)}" data-track-index="4" data-volume="0.8"></audio>\n`;
});
sfx.forEach(([n, t], i) => {
  idx += `<audio id="sfx${i + 1}" class="clip" src="assets/sfx/${n}.mp3" data-start="${f(t)}" data-duration="${sfxDur[n]}" data-track-index="${sfxTrack[n]}" data-volume="0.28"></audio>\n`;
});
idx += `</div>
<script>
const tl = gsap.timeline({ paused: true });
window.__timelines["main"] = tl;
</script>
</body>
</html>
`;
fs.writeFileSync(path.join(root, "index.html"), idx);

// ---- zemin: antrasit + marka kavisleri + logo
const bg = `<template>
<style>
#root { position:absolute; inset:0; overflow:hidden; background:radial-gradient(ellipse at 70% 22%, #3A3A41 0%, #2E2E33 30%, #1D1D20 75%); }
#root svg.deco { position:absolute; left:0; top:0; width:1080px; height:1920px; }
#bg-logo { position:absolute; left:400px; top:150px; width:280px; height:auto; }
</style>
<div id="root" data-composition-id="bg" data-width="1080" data-height="1920" data-duration="${TOTAL}" data-layout-ignore>
<svg class="deco" viewBox="0 0 1080 1920">
  <path id="bg-k1" d="M-40 250 C 120 120, 260 40, 420 -40" stroke="#F6D70C" stroke-width="30" fill="none" stroke-linecap="round"/>
  <path d="M-40 330 C 140 190, 320 90, 520 -40" stroke="#F6D70C" stroke-width="6" fill="none" stroke-linecap="round" opacity="0.6"/>
  <path id="bg-k2" d="M640 1980 C 820 1870, 980 1780, 1140 1660" stroke="#F6D70C" stroke-width="30" fill="none" stroke-linecap="round"/>
  <path d="M560 1980 C 760 1840, 940 1740, 1140 1600" stroke="#F6D70C" stroke-width="6" fill="none" stroke-linecap="round" opacity="0.5"/>
</svg>
<img id="bg-logo" src="assets/logo-obir.png" alt="Obir Kurs Merkezi"/>
</div>
<script>
const tl = gsap.timeline({ paused: true });
tl.to("#bg-logo", { scale: 1.04, duration: 0.5, yoyo: true, repeat: 1, ease: "sine.inOut" }, 13.2);
window.__timelines["bg"] = tl;
</script>
</template>
`;
fs.writeFileSync(path.join(root, "compositions/bg.html"), bg);

// ---- altyazı: 2–4 kelimelik gruplar, konuşulan kelime sarı
let groups = [];
for (const s of scenes) {
  const ws = W[s.vo].words.map((w) => ({ ...w, start: w.start + s.start + s.off, end: w.end + s.start + s.off }));
  let g = [];
  for (const w of ws) {
    g.push(w);
    const len = g.map((x) => x.text).join(" ").length;
    if (g.length >= 4 || len > 20 || /[.,!?]$/.test(w.text)) { groups.push(g); g = []; }
  }
  if (g.length) groups.push(g);
}
let html = "", js = "";
groups.forEach((g, gi) => {
  const next = groups[gi + 1];
  const st = g[0].start - 0.05;
  const en = next ? Math.min(next[0].start - 0.05, g[g.length - 1].end + 0.6) : g[g.length - 1].end + 0.8;
  html += `<div class="cg" id="cap${gi}">${g.map((w, wi) => `<span class="cw" id="cap${gi}-${wi}">${w.text}</span>`).join(" ")}</div>\n`;
  js += `tl.set("#cap${gi}",{opacity:1},${f(st)});tl.set("#cap${gi}",{opacity:0},${f(en)});\n`;
  g.forEach((w, wi) => {
    js += `tl.set("#cap${gi}-${wi}",{backgroundColor:"#F6D70C",color:"#1D1D20"},${f(w.start)});tl.set("#cap${gi}-${wi}",{backgroundColor:"rgba(0,0,0,0)",color:"#F7F5EE"},${f(Math.min(w.end + 0.05, en))});\n`;
  });
});
const cap = `<template>
<style>
#root { position:absolute; inset:0; pointer-events:none; }
#root .cg { position:absolute; left:110px; width:860px; top:1238px; text-align:center; font-family:'Nunito',sans-serif;
  font-weight:900; font-size:52px; line-height:1.25; color:#F7F5EE; opacity:0; text-shadow:0 3px 12px rgba(0,0,0,0.55); }
#root .cw { display:inline-block; padding:0 10px; border-radius:12px; }
</style>
<div id="root" data-composition-id="captions" data-width="1080" data-height="1920" data-duration="${TOTAL}">
${html}</div>
<script>
const tl = gsap.timeline({ paused: true });
${js}window.__timelines["captions"] = tl;
</script>
</template>
`;
fs.writeFileSync(path.join(root, "compositions/captions.html"), cap);
console.log("index, bg, captions yazıldı;", groups.length, "altyazı grubu");
