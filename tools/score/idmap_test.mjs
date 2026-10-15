// idmap_test.mjs — tools/score/idmap.mjs (lote 5 design A §4) on a synthetic Unreal tree made in a temp folder: the class sniff
// (SoundWave, SoundCue, attenuation, redirector), duplicate names, the plugin mounts, referencedBy from a deps graph, the aliases,
// the writing (one asset per line, a re-run changes nothing), --check, and the refusals of --out. VR_Test is never touched: the
// real tree is only checked for shape (Content is moving, so its counts are not pinned here).
//   node tools/score/idmap_test.mjs
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { classify, scan, build, referencedBy, readAliases, resolveSound, fmt, outProblem, diff, contentRoots } from './idmap.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
let fails = 0;
const check = (n, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + n + (info ? '  · ' + info : '')); if (!ok) fails++; };
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// ---- the synthetic project -------------------------------------------------------------------------------------------------
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'idmap-test-'));
const put = (rel, body, size) => {
  const p = path.join(tmp, rel); fs.mkdirSync(path.dirname(p), { recursive: true });
  const head = Buffer.from('Á\u0083*\u009eùÿÿÿ' + body, 'latin1');
  fs.writeFileSync(p, size && size > head.length ? Buffer.concat([head, Buffer.alloc(size - head.length, 7)]) : head);
  return p;
};
const WAVE = '/Script/Engine SoundWave NumChannels TotalSamples ImportedSampleRate Duration';
const WAVE_ATT = '/Script/Engine SoundAttenuation SoundWave NumChannels AttenuationSettings';   // a wave that imports an attenuation (Bell, Charge1)
const CUE = '/Script/Engine SoundCue SoundNodeWavePlayer SoundWave FirstNode AllNodes';           // a cue imports the waves it plays
const CUE_BARE = '/Script/Engine SoundCue';
const ATT = '/Script/Engine SoundAttenuation AttenuationSettings';
const REDIR = '/Script/CoreUObject ObjectRedirector SoundWave';                                    // a redirector may name the class it forwards to
const GHOST = '/Script/Engine DataAsset DA_Ghost';
const C = 'VR_Test/Content/SoulCharger', P = 'VR_Test/Plugins';
put(`${C}/Obra/Audio/VO_10.uasset`, WAVE, 70000);                       // > 64 KB: only the head is read for the class, the hash is of all of it
put(`${C}/Obra/Audio/VO_10.wav`, 'RIFF');                               // the source recording next to it
put(`${C}/Obra/Audio/VO_11.uasset`, WAVE);
put(`${C}/Obra/Audio/VO_12c.uasset`, WAVE + ' obra');                  // the same name in two live folders...
put(`${C}/Mechanics/Breath/Audio/VO_12c.uasset`, WAVE + ' breath');    // ...is ambiguous
put(`${C}/Obra/Audio/VO_99.uasset`, WAVE);
put(`${C}/_Deprecated/Audio/VO_99.uasset`, WAVE + ' old');             // a duplicate in _Deprecated does not count
put(`${C}/Core/Audio/Sounds/Bell.uasset`, WAVE_ATT);                   // a wave that imports an attenuation is a wave
put(`${C}/Core/Audio/Sounds/ATT_Only.uasset`, ATT);                    // an attenuation alone is not a sound
put(`${C}/Core/Audio/Sounds/CueA.uasset`, CUE);                        // a cue that imports a wave is a cue
put(`${C}/Core/Audio/Sounds/CueBare.uasset`, CUE_BARE);
put(`${C}/Core/Audio/Sounds/Old_Pad.uasset`, REDIR);                   // a redirector is not an asset
put(`${C}/Core/Audio/Sounds/Thing.uasset`, '/Script/Engine StaticMesh');
put(`${C}/Core/Meshes/NotAudio.uasset`, WAVE);                         // a wave outside an Audio folder is not listed
put(`${C}/Core/audio_lower/NotAudio2.uasset`, WAVE);                   // "audio_lower" is not an Audio folder
put(`${C}/Shared/Ghost/Data/DA_Ghost_Bell.uasset`, GHOST);
put(`${C}/Shared/Ghost/Data/DA_Other.uasset`, GHOST);                  // not a ghost take by name
put(`${C}/Core/Data/DA_Ghost_Stray.uasset`, GHOST);                    // DA_Ghost_* outside a Ghost folder
put(`${C}/Core/Audio/Ambient_Clip_1_-_Intro.uasset`, WAVE);            // a name with dashes
put(`${C}/Core/Audio/Voice_Over_7_.uasset`, WAVE);
put(`${C}/Obra/Audio/Placeholder/FX_SOULJOIN.uasset`, WAVE);
put(`${P}/SC_Base/Content/Audio/Charge1.uasset`, WAVE_ATT);            // a plugin: mounted at /SC_Base
put(`${P}/SC_Base/Content/Audio/VO_10.uasset`, WAVE + ' plugin');      // the same name as a /Game asset: ambiguous across mounts
put(`${P}/SC_Breath/Content/Audio/SND_PacerPulse.uasset`, WAVE);
put(`${P}/SC_Breath/Content/Deep/Audio/SND_Deep.uasset`, WAVE);
put(`${P}/SC_Draw/Resources/Audio/NotContent.uasset`, WAVE);           // outside the plugin's Content folder
put(`${P}/SC_Empty/SC_Empty.uplugin`, '{}');                           // a plugin with no Content folder
const treeHash = () => {   // every file under the tree: path and bytes
  const h = crypto.createHash('sha1'), walk = d => { for (const e of fs.readdirSync(d, { withFileTypes: true }).sort((a, b) => (a.name < b.name ? -1 : 1))) { const p = path.join(d, e.name); if (e.isDirectory()) walk(p); else h.update(path.relative(tmp, p) + '\0').update(fs.readFileSync(p)); } };
  walk(path.join(tmp, 'VR_Test')); return h.digest('hex');
};
const before = treeHash();

console.log('the class of a file, from its first bytes');
check('a SoundWave', classify(WAVE) === 'SoundWave');
check('a wave that imports an attenuation is still a wave', classify(WAVE_ATT) === 'SoundWave');
check('a cue that imports the waves it plays is a cue (its nodes tell)', classify(CUE) === 'SoundCue');
check('a bare cue (no wave data) is a cue', classify(CUE_BARE) === 'SoundCue');
check('an attenuation alone, a mesh, nothing: not a sound', classify(ATT) === null && classify('/Script/Engine StaticMesh') === null && classify('') === null);
check('a redirector is a redirector even if it names SoundWave', classify(REDIR) === 'redirector');

console.log('\nthe scan of the synthetic project');
const roots = contentRoots(tmp);
check('the roots: /Game and one mount per plugin that has a Content folder, in order', same(roots.map(r => r.mount), ['/Game', '/SC_Base', '/SC_Breath']), roots.map(r => r.mount).join(' '));
const s = scan(tmp);
const names = Object.keys(s.assets);
check('assets: the waves, the cue, the ghost take; sorted by name', same(names, names.slice().sort()) && same(names, ['Ambient_Clip_1_-_Intro', 'Bell', 'Charge1', 'CueA', 'CueBare', 'DA_Ghost_Bell', 'FX_SOULJOIN', 'SND_Deep', 'SND_PacerPulse', 'VO_11', 'VO_99', 'Voice_Over_7_']), names.join(' '));
check('classes: Bell is a SoundWave, CueA a SoundCue, the ghost take a GhostTake', s.assets.Bell.cls === 'SoundWave' && s.assets.CueA.cls === 'SoundCue' && s.assets.CueBare.cls === 'SoundCue' && s.assets.DA_Ghost_Bell.cls === 'GhostTake');
check('the object path is the mount + the folder + name.name', s.assets.VO_11.path === '/Game/SoulCharger/Obra/Audio/VO_11.VO_11' && s.assets.FX_SOULJOIN.path === '/Game/SoulCharger/Obra/Audio/Placeholder/FX_SOULJOIN.FX_SOULJOIN');
check('a plugin asset is mounted at the plugin: /SC_Base/Audio/Charge1, /SC_Breath/Content/Deep stays under the mount', s.assets.Charge1.path === '/SC_Base/Audio/Charge1.Charge1' && s.assets.SND_Deep.path === '/SC_Breath/Deep/Audio/SND_Deep.SND_Deep');
check('the same name in two live folders is ambiguous, with every candidate, and leaves assets', same(Object.keys(s.ambiguous).sort(), ['VO_10', 'VO_12c']) && !('VO_12c' in s.assets) && s.ambiguous.VO_12c.length === 2
  && s.ambiguous.VO_12c[0].path.endsWith('/Mechanics/Breath/Audio/VO_12c.VO_12c') && s.ambiguous.VO_12c[1].path.endsWith('/Obra/Audio/VO_12c.VO_12c'));
check('...also across mounts (/Game and a plugin)', s.ambiguous.VO_10.map(r => r.path.split('/')[1]).join() === 'Game,SC_Base');
check('a duplicate inside _Deprecated is not a duplicate', 'VO_99' in s.assets && s.assets.VO_99.path.includes('/Obra/Audio/'));
check('the redirector is listed apart, never an asset', same(s.redirectors, ['/Game/SoulCharger/Core/Audio/Sounds/Old_Pad.Old_Pad']) && !('Old_Pad' in s.assets));
check('what is under Audio but not a sound is counted: the attenuation and the mesh', s.skipped.SoundAttenuation === 1 && s.skipped.other === 1, JSON.stringify(s.skipped));
check('not listed: outside an Audio folder, "audio_lower", DA_Ghost_ outside Ghost, DA_Other, outside a plugin\'s Content, a plugin with no Content',
  !['NotAudio', 'NotAudio2', 'DA_Ghost_Stray', 'DA_Other', 'NotContent'].some(n => n in s.assets));
check('scanned counts the candidates it opened', s.scanned === 19, String(s.scanned));
{ const big = s.ambiguous.VO_10.find(r => r.path.startsWith('/Game')), bytes = fs.readFileSync(path.join(tmp, C, 'Obra/Audio/VO_10.uasset'));
  check('a big file: its size and the sha1 of ALL of it (12 chars), the class from its head', big.bytes === 70000 && big.sha1 === crypto.createHash('sha1').update(bytes).digest('hex').slice(0, 12) && big.cls === 'SoundWave'); }
check('wav: a .wav next to the asset is flagged', s.ambiguous.VO_10.find(r => r.path.startsWith('/Game')).wav === true && s.assets.VO_11.wav === false);
check('the scan did not touch the project (every byte of VR_Test is as it was)', treeHash() === before);

console.log('\nreferencedBy, from the dependency graph of tools/unreal/deps.py');
const deps = {
  '/Game/SoulCharger/Obra/Blueprints/BP_Obra_SC': ['/Game/SoulCharger/Obra/Audio/VO_11', '/Game/SoulCharger/Core/Audio/Sounds/Bell'],
  '/Game/SoulCharger/Obra/Blueprints/BP_Other': ['/Game/SoulCharger/Core/Audio/Sounds/Bell', '/Game/SoulCharger/Obra/Blueprints/BP_Other'],
  '/Game/SoulCharger/Obra/Audio/VO_11': [], '/Game/SoulCharger/Obra/Audio/VO_99': [], '/Game/SoulCharger/Core/Audio/Sounds/Bell': [],
};
check('referencedBy: the packages that point at it, sorted, never itself', same(referencedBy(deps, '/Game/SoulCharger/Core/Audio/Sounds/Bell'), ['/Game/SoulCharger/Obra/Blueprints/BP_Obra_SC', '/Game/SoulCharger/Obra/Blueprints/BP_Other']));
check('a package nothing points at: [] (a fact), not null', same(referencedBy(deps, '/Game/SoulCharger/Obra/Audio/VO_99'), []));
check('a package the graph does not list (a plugin asset): null = unknown', referencedBy(deps, '/SC_Base/Audio/Charge1') === null && referencedBy(null, '/Game/x') === null);

console.log('\nthe idmap');
const ALIASES = JSON.stringify({ note: 'x', aliases: { FX_BELLRING: 'Bell', FX_CHARGE_2: 'Charge1', FX_AMBIG: 'VO_12c', FX_GONE: 'Nothing', AMB_01: 'Ambient_Clip_1_-_Intro' } });
const doc = build(s, ALIASES, deps, '2026-10-08T00:00:00.000Z');
check('the shape: source fs-scan, scanned, assets, ambiguous, redirectors, aliases copied, where they come from', doc.source === 'fs-scan' && doc.scanned === 19 && doc.aliasesFrom === 'obra/unreal/idmap_aliases.json' && /^[0-9a-f]{12}$/.test(doc.aliasesSha) && doc.aliases.FX_BELLRING === 'Bell');
check('assets carry path, cls, bytes, sha1, wav, referencedBy', Object.values(doc.assets).every(r => ['path', 'cls', 'bytes', 'sha1', 'wav', 'referencedBy'].every(k => k in r)));
check('referencedBy: a /Game asset from the graph, a plugin asset null', same(doc.assets.Bell.referencedBy, ['/Game/SoulCharger/Obra/Blueprints/BP_Obra_SC', '/Game/SoulCharger/Obra/Blueprints/BP_Other']) && same(doc.assets.VO_99.referencedBy, []) && doc.assets.Charge1.referencedBy === null);
check('deps said where they come from; without a graph, null everywhere', doc.deps.packages === 5 && build(s, ALIASES, null, 'x').deps === null && Object.values(build(s, ALIASES, null, 'x').assets).every(r => r.referencedBy === null));
check('an alias that points at no asset is listed (FX_GONE), one that points at an ambiguous name is not', same(doc.unresolvedAliases, ['FX_GONE']));
check('the same scan, the same bytes: two builds differ only in `generated`', fmt(build(s, ALIASES, deps, 'a')).replace('"a"', 'X') === fmt(build(scan(tmp), ALIASES, deps, 'b')).replace('"b"', 'X'));
check('written one asset per line; it reads back to the same document', same(JSON.parse(fmt(doc)), doc) && fmt(doc).split('\n').filter(l => /^ {2}"Bell":/.test(l)).length === 1);
check('a bad aliases file is refused, not guessed', (() => { try { readAliases('{"aliases":[]}'); return false; } catch (_) { return true; } })() && (() => { try { readAliases('{"aliases":{"A":3}}'); return false; } catch (_) { return true; } })());

console.log('\nwhere a score sound lands');
check('exact: by its own name', resolveSound(doc, 'VO_11').state === 'asset' && resolveSound(doc, 'VO_11').name === 'VO_11');
check('alias: FX_BELLRING is Bell, FX_CHARGE_2 is Charge1 (the plugin asset)', resolveSound(doc, 'FX_BELLRING').state === 'alias' && resolveSound(doc, 'FX_BELLRING').rec.path.endsWith('Bell.Bell') && resolveSound(doc, 'FX_CHARGE_2').rec.path === '/SC_Base/Audio/Charge1.Charge1');
check('ambiguous: its own name or an alias that lands on one, with the candidates', resolveSound(doc, 'VO_12c').state === 'ambiguous' && resolveSound(doc, 'VO_12c').cands.length === 2 && resolveSound(doc, 'FX_AMBIG').state === 'ambiguous');
check('missing: no asset by that name, an alias to nothing, no idmap, no id', resolveSound(doc, 'FX_NOPE').state === 'missing' && resolveSound(doc, 'FX_GONE').state === 'missing' && resolveSound(null, 'VO_11').state === 'missing' && resolveSound(doc, null).state === 'missing');
check('an id named like an Object property (toString, __proto__) is just missing', resolveSound(doc, 'toString').state === 'missing' && resolveSound(doc, '__proto__').state === 'missing' && resolveSound(doc, 'constructor').state === 'missing');

console.log('\nthe CLI, on the synthetic project');
const CLI = path.join(ROOT, 'tools/score/idmap.mjs'), run = args => spawnSync(process.execPath, [CLI, '--root', tmp, ...args], { encoding: 'utf8' });
fs.mkdirSync(path.join(tmp, 'obra/unreal'), { recursive: true });
fs.writeFileSync(path.join(tmp, 'obra/unreal/idmap_aliases.json'), ALIASES);
fs.writeFileSync(path.join(tmp, 'deps.json'), JSON.stringify(deps));
const OUT = path.join(tmp, 'obra/unreal/idmap.json');
let r = run(['--deps', path.join(tmp, 'deps.json')]);
check('it writes obra/unreal/idmap.json', r.status === 0 && fs.existsSync(OUT) && /written: /.test(r.stdout), (r.stderr || r.stdout).split('\n')[0]);
const w1 = fs.readFileSync(OUT, 'utf8'), m1 = fs.statSync(OUT).mtimeMs;
check('what it wrote is a fresh scan with the graph', same(JSON.parse(w1).assets, doc.assets) && same(JSON.parse(w1).ambiguous, doc.ambiguous));
r = run(['--deps', path.join(tmp, 'deps.json')]);
check('a re-run that changes nothing leaves the file alone (same bytes, same time)', r.status === 0 && /nothing changed/.test(r.stdout) && fs.readFileSync(OUT, 'utf8') === w1 && fs.statSync(OUT).mtimeMs === m1);
r = run(['--check', '--deps', path.join(tmp, 'deps.json')]);
check('--check: up to date → exit 0', r.status === 0 && /up to date/.test(r.stdout));
r = run(['--check']);
check('--check without a graph does not compare referencedBy, and says so', r.status === 0 && /referencedBy not compared/.test(r.stdout));
put(`${C}/Obra/Audio/VO_NEW.uasset`, WAVE);
r = run(['--check', '--deps', path.join(tmp, 'deps.json')]);
check('--check: a new asset → exit 1, it says which', r.status === 1 && /\+ VO_NEW/.test(r.stdout));
fs.unlinkSync(path.join(tmp, C, 'Obra/Audio/VO_NEW.uasset'));
put(`${C}/Obra/Audio/VO_11.uasset`, WAVE + ' changed bytes');
r = run(['--check', '--deps', path.join(tmp, 'deps.json')]);
check('--check: an asset whose bytes changed → exit 1 (~ VO_11)', r.status === 1 && /~ VO_11/.test(r.stdout));
put(`${C}/Obra/Audio/VO_11.uasset`, WAVE);
fs.writeFileSync(path.join(tmp, 'obra/unreal/idmap_aliases.json'), ALIASES.replace('"Bell"', '"Bell2"'));
r = run(['--check', '--deps', path.join(tmp, 'deps.json')]);
check('--check: a changed alias → exit 1', r.status === 1 && /aliases differs|aliasesSha/.test(r.stdout));
fs.writeFileSync(path.join(tmp, 'obra/unreal/idmap_aliases.json'), ALIASES);

console.log('\nwhere it may write');
const rootless = p => path.join(tmp, p);
check('inside the Unreal project: refused', !!outProblem(tmp, rootless('VR_Test/Content/idmap.json')));
check('a score file: refused', !!outProblem(tmp, rootless('obra/score/score.json')));
check('the Director\'s and the other tools\' files: refused', ['partitura.json', 'perillas.json', 'traza.json', 'LEEME.md', 'roles.json', 'contract.json', 'knobs.json'].every(f => !!outProblem(tmp, rootless('obra/unreal/' + f))));
check('an existing file that is not an idmap: refused; the previous idmap and a new file: allowed', (() => { fs.writeFileSync(rootless('obra/unreal/other_idmap.json'), '{"a":1}'); return !!outProblem(tmp, rootless('obra/unreal/other_idmap.json')); })() && outProblem(tmp, OUT) === null && outProblem(tmp, rootless('obra/unreal/idmap_new.json')) === null);
check('outside the repo (a temp file): allowed', outProblem(tmp, path.join(os.tmpdir(), 'idmap-elsewhere.json')) === null);
for (const bad of ['VR_Test/idmap.json', 'obra/score/score.json']) {
  const target = rootless(bad), had = fs.existsSync(target);
  r = run(['--out', bad]);
  check(`--out ${bad} → exit 1, nothing written`, r.status === 1 && /refused/.test(r.stderr) && fs.existsSync(target) === had);
}
fs.writeFileSync(rootless('obra/unreal/idmap_aliases.json'), '{"aliases":{"A":1}}');
r = run(['--out', 'obra/unreal/idmap_x.json']);
check('a bad aliases file → exit 1, nothing written', r.status === 1 && !fs.existsSync(rootless('obra/unreal/idmap_x.json')));
check('after all this, every byte of VR_Test is as it was (but for the asset the test put back)', treeHash() === before);

console.log('\nthe real file (shape only: Content is moving, its counts are not pinned)');
{
  const real = path.join(ROOT, 'obra/unreal/idmap.json'), al = path.join(ROOT, 'obra/unreal/idmap_aliases.json');
  check('obra/unreal/idmap_aliases.json is valid', (() => { try { return Object.keys(readAliases(fs.readFileSync(al, 'utf8'))).length > 0; } catch (_) { return false; } })());
  if (!fs.existsSync(real)) check('obra/unreal/idmap.json exists (node tools/score/idmap.mjs --deps auto)', false);
  else {
    const d = JSON.parse(fs.readFileSync(real, 'utf8'));
    check('idmap.json: fs-scan, with assets that carry what reach.js reads', d.source === 'fs-scan' && Object.keys(d.assets).length > 100 && Object.values(d.assets).every(r => /^\/(Game|SC_\w+)\//.test(r.path) && ['SoundWave', 'SoundCue', 'GhostTake'].includes(r.cls) && r.bytes > 0 && /^[0-9a-f]{12}$/.test(r.sha1) && (r.referencedBy === null || Array.isArray(r.referencedBy))));
    check('its aliases are the aliases file (aliasesSha), and every alias points at an asset or an ambiguous name', d.aliasesSha === crypto.createHash('sha1').update(fs.readFileSync(al, 'utf8').replace(/\r\n/g, '\n')).digest('hex').slice(0, 12) && d.unresolvedAliases.length === 0, d.unresolvedAliases.join(', '));
    check('a name is either an asset or ambiguous, never both', !Object.keys(d.ambiguous).some(n => n in d.assets));
    const fresh = build(scan(ROOT), fs.readFileSync(al, 'utf8'), null, 'x'), dd = diff(d, fresh, { noRefs: true });
    console.log(dd.length ? '  note   idmap.json is out of date against VR_Test (' + dd.slice(0, 6).join('; ') + (dd.length > 6 ? '; …' : '') + '): run node tools/score/idmap.mjs --deps auto' : '  note   idmap.json matches a fresh scan of VR_Test');
  }
}

fs.rmSync(tmp, { recursive: true, force: true });
console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
