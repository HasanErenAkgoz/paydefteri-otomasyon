// Renders one queue item: node motor/uret.js kuyruk/<item> [--onizleme]
// Reads <item>/post.json and writes 01.jpg, 02.jpg... (photo) or video.mp4 (reel) next to it.
// --onizleme on a reel writes a few still frames (onizleme-*.jpg) instead of the video.
// A full reel render also writes kapak.jpg, the Instagram cover (designed for the grid's centre 4:5 crop).
// --kapak writes only the cover.
// Reels are never silent: <item>/ses.mp3 (one uncut voiceover take, one sentence per scene) is required,
// and scene durations are taken from the pauses in that take (written to zamanlama.json).
const { chromium } = require('playwright-core');
const ffmpeg = require('ffmpeg-static');
const { spawn, spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const [, , dir, flag] = process.argv;
if (!dir) { console.error('usage: node uret.js <item folder> [--onizleme]'); process.exit(1); }
const spec = JSON.parse(fs.readFileSync(path.join(dir, 'post.json'), 'utf8'));
const FPS = 30;
const LEAD = 0.3; // voice starts this long after the video

// Scene durations from the voice. Each scene's "metin" is its part of the take; every scene boundary
// goes to the pause nearest to where that text should end (by character share), so commas inside a
// sentence do not split scenes.
function timeVoice(file, scenes) {
  const texts = scenes.map(s => (s.metin || '').trim());
  if (texts.some(x => !x)) throw new Error('every reel scene needs "metin" (its voiceover line)');
  const r = spawnSync(ffmpeg, ['-nostdin', '-i', file, '-af', 'silencedetect=noise=-35dB:d=0.2', '-f', 'null', '-'], { encoding: 'utf8' });
  const total = +r.stderr.match(/Duration: (\d+):(\d+):([\d.]+)/).slice(1).reduce((a, v) => a * 60 + +v, 0);
  const starts = [...r.stderr.matchAll(/silence_start: ([\d.]+)/g)].map(m => +m[1]);
  const ends = [...r.stderr.matchAll(/silence_end: ([\d.]+)/g)].map(m => +m[1]);
  const sil = starts.map((s, i) => [s, ends[i] ?? total]);
  const speechStart = sil.length && sil[0][0] <= 0.1 ? sil[0][1] : 0;
  const speechEnd = sil.length && sil[sil.length - 1][1] >= total - 0.1 ? sil[sil.length - 1][0] : total;
  const gaps = sil.filter(([s, e]) => s > speechStart && e < speechEnd);
  const chars = texts.map(x => x.length), all = chars.reduce((a, b) => a + b, 0);
  const cuts = [];
  let cum = 0, after = speechStart;
  for (let k = 0; k < texts.length - 1; k++) {
    cum += chars[k];
    const want = speechStart + (speechEnd - speechStart) * cum / all;
    const free = gaps.filter(([s]) => s > after);
    if (!free.length) throw new Error(`no pause left for scene ${k + 2}; split the text differently`);
    const best = free.reduce((b, g) => Math.abs((g[0] + g[1]) / 2 - want) < Math.abs((b[0] + b[1]) / 2 - want) ? g : b);
    cuts.push(best); after = best[1];
  }
  const t = [0, ...cuts.map(([, e]) => LEAD + e - 0.2), LEAD + speechEnd + 1.4]; // switch just before each sentence
  const durs = t.slice(1).map((v, i) => +(v - t[i]).toFixed(2));
  if (durs.some(d => d < 1.2)) throw new Error('a scene would be shorter than 1.2s: ' + durs.join(', '));
  return { durs, cuts };
}

const url = f => 'file:///' + path.join(__dirname, f).replace(/\\/g, '/');

(async () => {
  const browser = await chromium.launch({ channel: 'chrome' });
  const errors = [];
  try {
    if (spec.type === 'photo') {
      const page = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
      page.on('pageerror', e => errors.push(e.message));
      const n = spec.slides.length;
      if (n < 1 || n > 10) throw new Error('photo needs 1-10 slides');
      for (let i = 0; i < n; i++) {
        await page.goto(url('post.html'));
        await page.evaluate(([s, i, n]) => build(s, { index: i, total: n }), [spec.slides[i], i, n]);
        if (errors.length) throw new Error(errors.join('; '));
        const out = path.join(dir, String(i + 1).padStart(2, '0') + '.jpg');
        await page.screenshot({ path: out, type: 'jpeg', quality: 93 });
        console.log('wrote', out);
      }
    } else if (spec.type === 'reel') {
      const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
      page.on('pageerror', e => errors.push(e.message));
      const voice = path.join(dir, 'ses.mp3');
      if (!fs.existsSync(voice)) throw new Error('reel needs ses.mp3 next to post.json (no silent videos)');
      const timing = timeVoice(voice, spec.scenes);
      spec.scenes.forEach((s, i) => { s.dur = timing.durs[i]; });
      fs.writeFileSync(path.join(dir, 'zamanlama.json'), JSON.stringify(timing.durs));
      await page.goto(url('reel.html'));
      await page.evaluate(s => build(s), spec.scenes);
      if (errors.length) throw new Error(errors.join('; '));
      const dur = await page.evaluate(() => window.DURATION);
      if (dur < 5 || dur > 60) throw new Error(`reel length ${dur}s, keep it 5-60s`);
      const writeCover = async () => {
        await page.evaluate(k => showCover(k || {}), spec.kapak);
        await page.screenshot({ path: path.join(dir, 'kapak.jpg'), type: 'jpeg', quality: 92 });
      };
      if (flag === '--kapak') {
        await writeCover();
        console.log('wrote', path.join(dir, 'kapak.jpg'));
      } else if (flag === '--onizleme') {
        let t0 = 0;
        for (const [k, s] of spec.scenes.entries()) {
          const t = Math.min(t0 + s.dur - 0.2, t0 + 2.4);
          await page.evaluate(t => seek(t), t);
          await page.screenshot({ path: path.join(dir, `onizleme-${k + 1}.jpg`), type: 'jpeg', quality: 80 });
          t0 += s.dur;
        }
      } else {
        const out = path.join(dir, 'video.mp4');
        const ms = Math.round(LEAD * 1000);
        const ff = spawn(ffmpeg, ['-nostdin', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
          '-i', voice, '-af', `adelay=${ms}|${ms},apad,atrim=0:${dur},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000`, '-ac', '2',
          '-map', '0:v', '-map', '1:a', '-shortest',
          '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
          '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out], { stdio: ['pipe', 'ignore', 'inherit'] });
        const frames = Math.round(dur * FPS);
        for (let i = 0; i < frames; i++) {
          await page.evaluate(t => seek(t), i / FPS);
          const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
          if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
        }
        ff.stdin.end();
        const code = await new Promise(r => ff.on('close', r));
        if (code !== 0) throw new Error('ffmpeg exit ' + code);
        console.log('wrote', out, dur + 's');
        await writeCover();
      }
    } else {
      throw new Error('type must be photo or reel');
    }
    if (!spec.caption || spec.caption.length > 2200) throw new Error('caption missing or over 2200 chars');
  } finally {
    await browser.close();
  }
})().catch(e => { console.error('ERROR', e.message); process.exit(1); });
