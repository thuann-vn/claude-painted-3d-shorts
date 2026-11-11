// Flow repaints blockout stills / edits paintings. node restyle.mjs jobs.json outDir   (jobs: [{name, aspect, refs:[abs paths], prompt}]) → outDir/<name>.jpg; prints 'xong <name>' or 'LỖI <name> <why>'. All ready Flow accounts draw in parallel.
import { readFileSync, copyFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const F = await import('/Users/admin/Projects/video-studio/flow.mjs');
const HERE = dirname(fileURLToPath(import.meta.url));
const jobs = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const OUT = process.argv[3] || join(HERE, 'out/paint'); mkdirSync(OUT, { recursive: true });
await F.flowLock('painted-3d restyle', async (got) => {
  const use = got.slice(0, Math.max(1, Math.min(got.length, jobs.length)));
  await Promise.all(use.map((i) => F.newProject('painted 3d', i))); // each account's Chrome opens at the same time
  const res = await F.drawSplit(join(OUT, '_flow'), jobs.map((j) => ({ prompt: j.prompt, aspect_ratio: j.aspect || '16:9', reference_images: j.refs })),
    (t) => console.log(t), use, (k, r) => { if (r.files?.[0]) { copyFileSync(r.files[0], join(OUT, jobs[k].name + '.jpg')); console.log('xong', jobs[k].name); } else console.log('LỖI', jobs[k].name, r.error); });
}, { want: Math.min(4, jobs.length) }); // take only the accounts this batch uses, so another video's batch can draw beside it
process.exit(0);
