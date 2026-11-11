// Voice + word timings in one ElevenLabs call (/with-timestamps). Run in the video's work dir:  node <tools>/tts.mjs
// in:  script.json { lines: [{ id, vo }] }
// out: out/voice.mp3 + out/timing.json { duration, lines: [{ id, text, start, end, words: [{ w, t }] }] }  (seconds, 0.3 s lead-in)
// env: VOICE (default Ninh Đôn, the studio's Vietnamese narrator), SPEED (0.7–1.2, default 1.0), MODEL (eleven_v3), LANG_CODE (vi)
// Exit 3 = ElevenLabs refused (no characters left / bad key): use the VClip twin voice instead (skill vclip-tts) and write the same timing.json.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
const KEY = readFileSync(join(process.env.HOME, '.config/elevenlabs/key'), 'utf8').trim();
const VOICE = process.env.VOICE || 'aN7cv9yXNrfIR87bDmyD';
const S = JSON.parse(readFileSync('script.json', 'utf8')).lines;
const LEAD = 0.3, text = S.map((l) => l.vo).join(' ');
const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE}/with-timestamps?output_format=mp3_44100_128`, {
  method: 'POST', headers: { 'xi-api-key': KEY, 'Content-Type': 'application/json' },
  body: JSON.stringify({ text, model_id: process.env.MODEL || 'eleven_v3', language_code: process.env.LANG_CODE || 'vi', voice_settings: { stability: 0.5, similarity_boost: 0.75, speed: Number(process.env.SPEED || 1.0) } }) });
if (!r.ok) { console.error('ElevenLabs', r.status, (await r.text()).slice(0, 200)); process.exit(r.status === 401 || r.status === 402 || r.status === 429 ? 3 : 1); }
const j = await r.json();
mkdirSync('out', { recursive: true });
writeFileSync('out/voice_raw.mp3', Buffer.from(j.audio_base64, 'base64'));
const st = j.alignment.character_start_times_seconds, en = j.alignment.character_end_times_seconds;
let pos = 0; const lines = [];
for (const l of S) {
  const i0 = text.indexOf(l.vo, pos), i1 = i0 + l.vo.length; pos = i1;
  const words = []; let k = i0;
  for (const w of l.vo.split(' ')) { const wi = text.indexOf(w, k); words.push({ w, t: +(st[wi] + LEAD).toFixed(3) }); k = wi + w.length; }
  lines.push({ id: l.id, text: l.vo, start: +(st[i0] + LEAD).toFixed(3), end: +(en[i1 - 1] + LEAD).toFixed(3), words });
}
const duration = +(en[en.length - 1] + LEAD + 0.9).toFixed(3);
writeFileSync('out/timing.json', JSON.stringify({ duration, lines }, null, 1));
// the lead-in is baked into the file, so the voice simply starts at 0 in the mix
const { spawnSync } = await import('node:child_process');
const f = spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', 'out/voice_raw.mp3', '-af', `adelay=${LEAD * 1000}:all=1,apad=pad_dur=0.9`, '-ar', '44100', 'out/voice.mp3']);
if (f.status) { console.error(String(f.stderr)); process.exit(1); }
console.log(lines.map((l) => `${l.id}: ${l.start.toFixed(2)}–${l.end.toFixed(2)}  frame ${Math.round(l.start * 24)}  ${l.text}`).join('\n'), `\nlength ${duration} s = ${Math.ceil(duration * 24)} frames at 24 fps (cut each shot a few frames before its first line starts)`);
