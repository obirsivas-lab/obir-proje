// Seslendirme üretici: ElevenLabs "Adam" (eleven_v3), kelime zamanlarıyla.
// Kullanım: node tools/vo.mjs   (ELEVENLABS_API_KEY ortam değişkeni gerekli)
// Çıktı: assets/vo/lN.mp3, lNf.wav (%10 hızlı), assets/vo/vo-words-fast.json
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const VOICE = "RXCCWbOxP7Hisa63Xsv5";
const MODEL = "eleven_v3";
const SPEED = 1.1;
import { fileURLToPath } from "node:url";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const lines = JSON.parse(fs.readFileSync(path.join(root, "tools", "script.json"), "utf8"));
const only = process.argv.slice(2);
const key = process.env.ELEVENLABS_API_KEY;
if (!key) throw new Error("ELEVENLABS_API_KEY yok");
const outDir = path.join(root, "assets", "vo");
const wordsPath = path.join(outDir, "vo-words-fast.json");
const all = fs.existsSync(wordsPath) ? JSON.parse(fs.readFileSync(wordsPath, "utf8")) : {};

for (const [id, text] of Object.entries(lines)) {
  if (only.length && !only.includes(id)) continue;
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE}/with-timestamps`, {
    method: "POST",
    headers: { "xi-api-key": key, "Content-Type": "application/json" },
    body: JSON.stringify({ text, model_id: MODEL }),
  });
  if (!res.ok) throw new Error(`${id}: ${res.status} ${await res.text()}`);
  const j = await res.json();
  const mp3 = path.join(outDir, `${id}.mp3`);
  fs.writeFileSync(mp3, Buffer.from(j.audio_base64, "base64"));
  const wav = path.join(outDir, `${id}f.wav`);
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-i", mp3, "-filter:a", `atempo=${SPEED}`, "-ar", "44100", wav]);
  // karakter zamanlarından kelime zamanları
  const a = j.alignment;
  const words = [];
  let cur = null;
  for (let i = 0; i < a.characters.length; i++) {
    const ch = a.characters[i];
    if (/\s/.test(ch)) { if (cur) { words.push(cur); cur = null; } continue; }
    if (!cur) cur = { text: "", start: a.character_start_times_seconds[i] / SPEED };
    cur.text += ch;
    cur.end = a.character_end_times_seconds[i] / SPEED;
  }
  if (cur) words.push(cur);
  const dur = parseFloat(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav]).toString());
  all[id] = { text, duration: dur, words: words.map(w => ({ ...w, start: +w.start.toFixed(3), end: +w.end.toFixed(3) })) };
  console.log(id, dur.toFixed(2), "s,", words.length, "kelime");
}
fs.writeFileSync(wordsPath, JSON.stringify(all, null, 1));
