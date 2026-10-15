// fixture_test.mjs — the score is never written by a tool, and the tests never depend on it (audit A13, D2; lote 5 design B §4).
//   1. extract_v1.mjs refuses every spelling of obra/score/score.json (exit 2) and the frozen fixture outside --refreeze;
//      score.json is byte for byte and mtime the same afterwards.
//      Nor into a folder someone else owns (obra/unreal, the prototype, obra/score, the fixture, VR_Test), nor over an existing
//      file that is not an earlier extraction (probed with new names and temp copies: the real files are never at risk).
//   2. An edit to a COPY of the live score does not change golden_test's exit code; --live on that copy only informs.
// Everything it writes goes to a temp folder that it removes. Exit 1 if any case fails.
//   node tools/score/fixture_test.mjs
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { ROOT, FIXTURE, EXPECT, LIVE, readFixture } from './test_score.mjs';

const EXTRACT = path.join(ROOT, 'tools/score/extract_v1.mjs'), GOLDEN = path.join(ROOT, 'tools/score/golden_test.mjs');
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'vvr-fixture-'));
let fails = 0;
const check = (name, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + name + (info ? '  · ' + info : '')); if (!ok) fails++; };
const run = (script, args, cwd = ROOT) => { const r = spawnSync(process.execPath, [script, ...args], { cwd, encoding: 'utf8' }); return { code: r.status, out: (r.stdout || '') + (r.stderr || '') }; };
const print = f => { const b = fs.readFileSync(f), st = fs.statSync(f); return `${st.mtimeMs}|${st.size}|${crypto.createHash('sha1').update(b).digest('hex')}`; };
const live0 = print(LIVE), fix0 = print(FIXTURE), exp0 = print(EXPECT);
const OWNED = ['obra/unreal/partitura.json', 'obra/unreal/perillas.json', 'web/prototipo-narrativo/guion.js'].map(f => path.join(ROOT, f)).filter(f => fs.existsSync(f));
const owned0 = OWNED.map(print);

try {
  console.log('extract_v1 never writes the score');
  const spellings = [
    ['relative', ['--out', 'obra/score/score.json']],
    ['absolute', ['--out', LIVE]],
    ['with ..', ['--out', './obra/score/../score/score.json']],
    ['--out=', ['--out=obra/score/score.json']],
  ];
  if (process.platform === 'win32' || process.platform === 'darwin') spellings.push(['other case', ['--out', 'OBRA/Score/SCORE.json']]);
  if (process.platform === 'win32') spellings.push(['trailing dot', ['--out', 'obra/score/score.json.']], ['a :stream', ['--out', 'obra/score/score.json::$DATA']], ['trailing space', ['--out', 'obra/score/score.json ']]);
  for (const [what, args] of spellings) {
    const r = run(EXTRACT, args);
    check(`--out score.json (${what}): exit 2 with the reason`, r.code === 2 && /only written by the editor/.test(r.out) && /File ▸ Import score/.test(r.out), `exit ${r.code}`);
  }
  { const r = run(EXTRACT, ['--out', 'score.json'], path.join(ROOT, 'obra/score'));
    check('from inside obra/score, --out score.json: exit 2', r.code === 2, `exit ${r.code}`); }
  // through a junction (Windows, no admin needed) or a directory symlink: the real path is what counts
  // (its own folder, removed without recursion: nothing ever walks into obra/score through the link)
  { const jdir = fs.mkdtempSync(path.join(os.tmpdir(), 'vvr-link-')), j = path.join(jdir, 'via');
    let made = false; try { fs.symlinkSync(path.join(ROOT, 'obra/score'), j, process.platform === 'win32' ? 'junction' : 'dir'); made = true; } catch (e) { console.log('  info  no junction/symlink here: ' + e.code); }
    try { if (made) { const r = run(EXTRACT, ['--out', path.join(j, 'score.json')]); check('through a junction to obra/score: exit 2', r.code === 2, `exit ${r.code}`); } }
    finally {
      try { if (made) fs.unlinkSync(j); } catch (_) { /* reported below */ }
      let gone = true; try { fs.lstatSync(j); gone = false; } catch (_) {}
      if (gone) fs.rmdirSync(jdir); else console.log(`  info  could not remove the link ${j}: remove it by hand (rmdir, never a recursive delete)`);
    } }
  { const r = run(EXTRACT, ['--force', '--out', 'obra/score/score.json']); check('there is no --force (unknown option, nothing written)', r.code === 1 && /unknown option --force/.test(r.out), `exit ${r.code}`); }
  check('score.json: same bytes and same mtime after all of that', print(LIVE) === live0);

  console.log('extract_v1 never writes what someone else owns');
  // folders owned by others: probed with NEW file names only, so a regression could at most leave a stray file (removed here),
  // never overwrite Unreal's, the prototype's or the editor's files
  for (const d of ['obra/unreal', 'web/prototipo-narrativo', 'obra/score', 'tools/score/fixtures', 'VR_Test']) {
    const probe = path.join(ROOT, d, `zz-extract-probe-${process.pid}.json`), r = run(EXTRACT, ['--out', path.relative(ROOT, probe)]);
    const made = fs.existsSync(probe); if (made) fs.unlinkSync(probe);
    check(`--out into ${d}/: exit 2 with the reason, nothing written`, r.code === 2 && /Not written to/.test(r.out) && !made, `exit ${r.code}`);
  }
  { const r = run(EXTRACT, ['--out', 'OBRA/Unreal/zz-extract-probe.json']), p = path.join(ROOT, 'obra/unreal/zz-extract-probe.json'), made = fs.existsSync(p); if (made) fs.unlinkSync(p);
    check('  also spelled in another case or through ..', r.code === 2 && !made && run(EXTRACT, ['--out', 'tools/../obra/unreal/zz-extract-probe.json']).code === 2 && !fs.existsSync(p), `exit ${r.code}`); }
  // an existing file that is not an earlier extraction (copies in the temp folder stand in for partitura.json and guion.js)
  for (const [what, src] of [['a copy of partitura.json', 'obra/unreal/partitura.json'], ['a copy of guion.js', 'web/prototipo-narrativo/guion.js'], ['a copy of the live score', 'obra/score/score.json']]) {
    if (!fs.existsSync(path.join(ROOT, src))) { console.log(`  info  ${src} missing: case skipped`); continue; }
    const f = path.join(TMP, 'own-' + path.basename(src)); fs.copyFileSync(path.join(ROOT, src), f); const p0 = print(f);
    const r = run(EXTRACT, ['--out', f]);
    check(`over ${what}: exit 2, the file untouched`, r.code === 2 && /is not an earlier extraction/.test(r.out) && print(f) === p0, `exit ${r.code}`);
  }
  { const f = path.join(TMP, 'own-partitura.json'), l = path.join(TMP, 'hardlink.json');
    let linked = false; try { if (fs.existsSync(f)) { fs.linkSync(f, l); linked = true; } } catch (e) { console.log('  info  no hard link here: ' + e.code); }
    if (linked) { const p0 = print(f), r = run(EXTRACT, ['--out', l]); check('  through a hard link to it: exit 2, untouched', r.code === 2 && print(f) === p0, `exit ${r.code}`); } }
  { const r = run(EXTRACT, ['--out', TMP]); check('--out a folder: exit 2', r.code === 2 && /is a folder/.test(r.out), `exit ${r.code}`); }

  console.log('the frozen fixture');
  { const r = run(EXTRACT, ['--fixture']); check('--fixture when it is already frozen: refused, nothing written', r.code === 1 && /frozen/.test(r.out) && print(FIXTURE) === fix0 && print(EXPECT) === exp0, `exit ${r.code}`); }
  { const r = run(EXTRACT, ['--out', path.relative(ROOT, FIXTURE)]); check('--out onto the fixture: exit 2 (only --refreeze rewrites it)', r.code === 2 && print(FIXTURE) === fix0, `exit ${r.code}`); }
  { const r = run(EXTRACT, ['--fixture', '--out', path.join(TMP, 'x.json')]); check('--out with --fixture: refused', r.code === 1 && !fs.existsSync(path.join(TMP, 'x.json')), `exit ${r.code}`); }
  { const out = path.join(TMP, 'fresh.json'), r = run(EXTRACT, ['--out', out]), ok = r.code === 0 && fs.existsSync(out);
    check('a fresh extraction goes where --out says', ok, `exit ${r.code}`);
    if (ok) { const r2 = run(EXTRACT, ['--out', out]); check('  and an earlier extraction can be written over', r2.code === 0, `exit ${r2.code}`); }
    if (ok) { const a = JSON.parse(fs.readFileSync(out, 'utf8')), f = readFixture(), same = JSON.stringify(a.elements) === JSON.stringify(f.elements) && JSON.stringify(a.golden) === JSON.stringify(f.golden);
      console.log(`  info  today's guion.js extracts ${same ? 'exactly the fixture (elements and golden)' : 'something different from the fixture: guion.js changed since F0 (expected over time)'}`); } }
  { const g = spawnSync('git', ['check-ignore', '-q', 'obra/score/score.extracted.json'], { cwd: ROOT });
    if (g.error) console.log('  info  git not available: .gitignore not checked');
    else check('obra/score/score.extracted.json is ignored by git', g.status === 0); }

  console.log('golden_test does not depend on the live score');
  { const g0 = run(GOLDEN, []);
    check('golden_test passes on the fixture', g0.code === 0 && /665\/665/.test(g0.out), `exit ${g0.code}`);
    // an edit to a COPY of the live score (never the real one): a voice 5 s later and a wait 3 s longer
    const copy = path.join(TMP, 'score-edited.json'), s = JSON.parse(fs.readFileSync(LIVE, 'utf8'));
    const vo = Object.keys(s.elements).find(id => s.elements[id].type === 'vo' && s.elements[id].at), wait = Object.keys(s.elements).find(id => s.elements[id].gate);
    s.elements[vo].at.off += 5; s.elements[wait].gate.expected += 3; s.rev = (s.rev || 1) + 1;
    fs.writeFileSync(copy, JSON.stringify(s));
    const g1 = run(GOLDEN, ['--live', copy]);
    check('with an edited copy as the live score: same exit code', g1.code === g0.code, `exit ${g1.code}`);
    check('  and --live says it is information, with how many times differ', /times differ from F0 \(the score was edited\)/.test(g1.out) && /information, not a failure/.test(g1.out), (g1.out.match(/live \(.*$/m) || [''])[0].slice(0, 140)); }

  check('score.json is untouched at the end (bytes and mtime)', print(LIVE) === live0);
  check("Unreal's and the prototype's files are untouched at the end", OWNED.every((f, i) => print(f) === owned0[i]), OWNED.length + ' files');
} finally {
  fs.rmSync(TMP, { recursive: true, force: true });
}
console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
