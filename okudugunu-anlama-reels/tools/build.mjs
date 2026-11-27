// index.html, compositions/bg.html ve compositions/captions.html dosyalarını
// assets/vo/vo-words-fast.json kelime zamanlarından üretir. Sahneler (s1–s7) elle yazılır.
// Kullanım: node tools/build.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const W = JSON.parse(fs.readFileSync(path.join(root, "assets/vo/vo-words-fast.json"), "utf8"));

// sahne: başlangıç, süre, ses gecikmesi
const scenes = [
  { id: "s1", vo: "l1", start: 0.0, dur: 4.2, off: 0.15 },
  { id: "s2", vo: "l2", start: 4.2, dur: 7.7, off: 0.1 },
  { id: "s3", vo: "l3", start: 11.9, dur: 7.3, off: 0.1 },
  { id: "s4", vo: "l4", start: 19.2, dur: 2.8, off: 0.1 },
  { id: "s5", vo: "l5", start: 22.0, dur: 9.5, off: 0.1 },
  { id: "s6", vo: "l6", start: 31.5, dur: 9.3, off: 0.1 },
  { id: "s7", vo: "l7", start: 40.8, dur: 6.7, off: 0.1 },
];
const TOTAL = 47.5;
const f = (n) => n.toFixed(2);

// ses efektleri: [dosya, mutlak saniye]
const sfx = [
  ["click-soft", 2.0], ["click-soft", 2.3], ["click-soft", 2.6], ["pop", 2.95],
  ["whoosh-short", 4.2], ["pop", 4.75], ["click-soft", 5.95], ["pop", 7.03],
  ["whoosh-short", 11.9], ["pop", 12.05], ["pop", 15.1], ["click-soft", 17.5],
  ["whoosh-short", 19.2], ["sparkle", 21.15],
  ["whoosh-short", 22.0], ["pop", 26.7], ["click-soft", 29.35],
  ["whoosh-short", 31.5], ["pop", 35.85], ["pop", 37.6], ["pop", 38.95],
  ["whoosh-short", 40.8], ["click-soft", 44.65], ["sparkle", 44.8],
];
const sfxDur = { "click-soft": 0.28, pop: 0.72, "whoosh-short": 0.57, sparkle: 1.8 };

let idx = `<!doctype html>
<html lang="tr">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html, body { margin:0; width:1080px; height:1920px; overflow:hidden; background:#FBF6E9; }
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
  idx += `<audio id="vo${i + 1}" class="clip" src="assets/vo/${s.vo}f.wav" data-start="${f(s.start + s.off)}" data-duration="${W[s.vo].duration.toFixed(3)}" data-track-index="4" data-volume="1"></audio>\n`;
});
sfx.forEach(([n, t], i) => {
  idx += `<audio id="sfx${i + 1}" class="clip" src="assets/sfx/${n}.mp3" data-start="${f(t)}" data-duration="${sfxDur[n]}" data-track-index="${{ "click-soft": 5, pop: 7, "whoosh-short": 8, sparkle: 6 }[n]}" data-volume="0.3"></audio>\n`;
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

// ---- zemin: defter kâğıdı + logo rozeti (s7'de büyük logo geldiği için rozet kaybolur)
let lines = "";
for (let y = 360; y < 1920; y += 76) lines += `<line x1="0" y1="${y}" x2="1080" y2="${y}" stroke="#D9E4F1" stroke-width="2"/>`;
const bg = `<template>
<style>
#root { position:absolute; inset:0; background:#FBF6E9; }
#root svg.paper { position:absolute; left:0; top:0; width:1080px; height:1920px; }
#bg-badge { position:absolute; left:405px; top:196px; width:270px; height:108px; border-radius:26px; background:#1E2B4A;
  display:flex; align-items:center; justify-content:center; box-shadow:0 6px 0 rgba(30,43,74,0.18); }
#bg-badge img { width:226px; height:auto; display:block; }
</style>
<div id="root" data-composition-id="bg" data-width="1080" data-height="1920" data-duration="${TOTAL}" data-layout-ignore>
<svg class="paper" viewBox="0 0 1080 1920">${lines}
<line x1="44" y1="0" x2="44" y2="1920" stroke="#F0B8B2" stroke-width="3"/>
<line x1="1036" y1="0" x2="1036" y2="1920" stroke="#F0B8B2" stroke-width="3"/>
</svg>
<div id="bg-badge"><img id="bg-logo" src="assets/logo-obir.png" alt="Obir Kurs Merkezi"/></div>
</div>
<script>
const tl = gsap.timeline({ paused: true });
tl.to("#bg-badge",{opacity:0,y:-20,duration:0.3,ease:"power2.in"},40.8);
window.__timelines["bg"] = tl;
</script>
</template>
`;
fs.writeFileSync(path.join(root, "compositions/bg.html"), bg);

// ---- altyazı: kelime grupları (en çok 4 kelime / ~22 harf, noktalamada kır)
let groups = [];
for (const s of scenes) {
  const ws = W[s.vo].words.map((w) => ({ t: w.text.replace(/"/g, ""), a: s.start + s.off + w.start, b: s.start + s.off + w.end }));
  let g = [];
  const flush = () => { if (g.length) groups.push(g); g = []; };
  for (const w of ws) {
    const len = g.reduce((n, x) => n + x.t.length + 1, 0) + w.t.length;
    if (g.length >= 4 || len > 24) flush();
    g.push(w);
    if (/[.,:?!]$/.test(w.t)) flush();
  }
  flush();
}
let cap = `<template>
<style>
#root { position:absolute; inset:0; pointer-events:none; }
#root .cg { position:absolute; left:100px; width:800px; top:1282px; text-align:center; font-family:'Nunito',sans-serif;
  font-weight:900; font-size:54px; line-height:1.2; color:#1E2B4A; opacity:0; }
#root .cw { display:inline-block; padding:0 8px; border-radius:10px; }
</style>
<div id="root" data-composition-id="captions" data-width="1080" data-height="1920" data-duration="${TOTAL}">
`;
let js = "";
groups.forEach((g, gi) => {
  cap += `<div class="cg" id="cap${gi}">${g.map((w, wi) => `<span class="cw" id="cap${gi}-${wi}">${w.t}</span>`).join(" ")}</div>\n`;
  const next = groups[gi + 1];
  const a = g[0].a - 0.05;
  let b = g[g.length - 1].b + 0.25;
  if (next) b = Math.min(b, next[0].a - 0.07);
  g.forEach((w, wi) => {
    js += `tl.fromTo("#cap${gi}-${wi}",{backgroundColor:"rgba(246,215,12,0)"},{backgroundColor:"rgba(246,215,12,1)",duration:0.06},${f(w.a)});\n`;
    js += `tl.to("#cap${gi}-${wi}",{backgroundColor:"rgba(246,215,12,0)",duration:0.08},${f(Math.max(w.b, w.a + 0.1))});\n`;
  });
  js += `tl.fromTo("#cap${gi}",{opacity:0,y:10},{opacity:1,y:0,duration:0.1,ease:"power2.out"},${f(a)});\n`;
  js += `tl.to("#cap${gi}",{opacity:0,duration:0.06},${f(b)});\n`;
});
cap += `</div>
<script>
const tl = gsap.timeline({ paused: true });
${js}window.__timelines["captions"] = tl;
</script>
</template>
`;
fs.writeFileSync(path.join(root, "compositions/captions.html"), cap);
console.log("index, bg, captions yazıldı;", groups.length, "altyazı grubu");
