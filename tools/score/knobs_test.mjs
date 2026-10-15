// knobs_test.mjs — tools/score/knobs.mjs and js/knobs.js (lote 5 design A §8.1): the catalog of Unreal's knobs a machine can read.
// A small synthetic project covers every rule (da values, instance rows, hardwired rows, class defaults, internal state left out,
// truncated dumps, elements frozen by role, the writing, --check, where --out may go); then the real catalog is held against the
// real files it was made from (60 Partitura knobs with their live values, every role drawn the same as roles.json, no internal
// variables). Nothing here writes the real files.
//   node tools/score/knobs_test.mjs
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { build, fmt, diff, outProblem, roleOf, readInputs } from './knobs.mjs';

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const Knobs = require(path.join(ROOT, 'web/editor-obra/app/js/knobs.js'));
const rd = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const clone = o => JSON.parse(JSON.stringify(o)), same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
let fails = 0;
const check = (n, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + n + (info ? '  · ' + info : '')); if (!ok) fails++; };

// ---- the helpers of js/knobs.js -----------------------------------------------------------------------------------------------
console.log('reading a row of roles.json');
{
  const pv = Knobs.parseVar;
  check('the variable is the identifier in front, the note what follows', same(pv('FW_Bell · after it, the bell fills by itself in 3 s'), { var: 'FW_Bell', note: 'after it, the bell fills by itself in 3 s' }));
  check('a dotted path stays whole (Appear.Duration); a bare name has no note', pv('Appear.Duration · light first').var === 'Appear.Duration' && same(pv('IntroTime'), { var: 'IntroTime', note: '' }));
  check('"Size = diameter..." and "BellPressTime (verify...)" both give the variable', pv('Size = diameter in m').var === 'Size' && pv('BellPressTime (verify live: may be 0)').var === 'BellPressTime');
  check('a text that starts with words, not a variable, has none (the hardwired rows)', pv('charge drains when released · literal in HallTickSteps').var === null && pv('literal in AlmaSpeak').var === null);
  check('values: numbers read ("1.5", "−2", "+1.5"), a sentence stays a text', Knobs.parseValue('1.5') === 1.5 && Knobs.parseValue('−2') === -2 && Knobs.parseValue('+1.5') === 1.5 && Knobs.parseValue('VO + 3.5 s') === 'VO + 3.5 s' && Knobs.parseValue('AmbPick') === 'AmbPick');
  check('keys: a level in front, a component stays out; hardwired by owner and label', Knobs.instKey('HallDirector · Test_Hall', 'FW_Bell') === 'inst:Test_Hall/HallDirector.FW_Bell' && Knobs.instKey('Timbre · Appear component', 'Appear.Duration') === 'inst:Timbre.Appear.Duration'
    && Knobs.instKey('BP_Alma_SC_C_0 · Obra', 'Size') === 'inst:Obra/BP_Alma_SC_C_0.Size' && Knobs.litKey('BP_Obra_SC graph', 'Speaks at') === 'lit:BP_Obra_SC.speaks_at');
  check('internal state: Interno and the Z- state categories; not Z-Ghost, Default, Debug', ['Interno', 'Z - Estado', 'Z-Estado', 'Z-Interno', 'Z - Estado interno'].every(Knobs.isInternal) && !['Etapas', 'Z-Ghost', 'Default', 'Debug', 'Partitura', ''].some(Knobs.isInternal));
  check('the signature is the same for the same JSON, and changes with a character', Knobs.sig({ a: [1, 2] }) === Knobs.sig(JSON.parse('{"a":[1,2]}')) && Knobs.sig({ a: [1, 2] }) !== Knobs.sig({ a: [1, 3] }) && /^[0-9a-f]{16}$/.test(Knobs.sig('x')));
}

// ---- a small project ----------------------------------------------------------------------------------------------------------
const def = { synced: '2026-10-02T00:00:00', sourceSha1: 'abc', asset: '/Game/Obra/Partitura/DA_Partitura_Obra', stages: ['A', 'B', 'C', 'D', 'E'], knobs: [
  { name: 'Aviso_Dur', type: 'f', initial: 19, category: '1 Hall', doc: 'aviso' },
  { name: 'Etapa_Tope', type: 'a5', initial: [240, 180, 120, 240, 205], category: '2 Etapas', doc: 'tope' },
  { name: 'Sin_Enlace', type: 'f', initial: 1, category: '2 Etapas', doc: 'sin elemento' }] };
const live = { exportado: '2026-10-02T18:06:10', hash: 'deadbeef0000', valores: { Aviso_Dur: 21, Etapa_Tope: [250, 180, 120, 240, 205] } };   // Sin_Enlace has no live value
const binding = { binds: [{ knob: 'Aviso_Dur', ids: { '*': 'el_aviso' } }, { knob: 'Etapa_Tope', ids: { '0': 'el_t0', '1': 'el_t1', '2': ['el_t2', 'el_t1'] } }] };
const ROW = (label, v, u, f, c, vr, lock) => lock === undefined ? [label, v, u, f, c, vr] : [label, v, u, f, c, vr, lock];
const roles = { verified: '2026-10-01', roles: {
  Bell: { match: { key: '^(BELL_|G_BELL$)' }, groups: [
    { owner: 'Timbre · Appear component', scope: 'instance', rows: [ROW('Appear', '1.5', 's', 30, '#7FB2E8', 'Appear.Duration · light first', 1)] },
    { owner: 'HallDirector · Test_Hall', scope: 'instance', rows: [ROW('Timeout', '25', 's', 90, '#E06C6C', 'FW_Bell · after it, the bell fills by itself in 3 s', 1), ROW('Hold', '3.0', 's', 30, '#D8C24B', 'BellHold', 0)] },
    { owner: 'HallDirector graph', scope: 'literal', rows: [ROW('Release', '−2 /s', '', null, null, 'charge drains when released · literal in HallTickSteps')] }] },
  Pacer: { match: { key: '^PACER' }, groups: [
    { owner: 'Entering_Pacer · Test_Breath', scope: 'instance', rows: [ROW('Hold', '3', 's', 30, '#fff', 'Hold1Time', 1), ROW('Hold', '3', 's', 30, '#fff', 'Hold1Time', 1)] },   // the same variable twice: the 2nd key gets #2
    { owner: 'BP_Pacer_SC', scope: 'class default', rows: [ROW('Intro', '0.6', 's', 12, '#7FB2E8', 'IntroTime'), ROW('Ghost', '9', 's', 1, '#fff', 'NotInPerillas')] }] },
  Ambiences: { match: { group: 'amb' }, groups: [{ owner: 'BP_Obra_SC_C_0 · Obra', scope: 'instance', rows: [ROW('Volume', '0.8', '', 80, '#fff', 'AmbVolumes', 1)] }] } } };
const perillas = { exportado: '2026-10-02T18:06:10', bps: {
  BP_Pacer_SC: [['IntroTime', 'Default', '{"IntroTime":0.59999999999999998}'], ['State', 'Interno', '{"State":1}'], ['Mode', 'Z - Estado', '{"Mode":2}'], ['Etapa', 'Z-Ghost', '{"Etapa":"x"}']],
  BP_Obra_SC: [['AmbVolumes', 'Ambientes', '{"AmbVolumes":[0.80000000000000004,0.80000000000000004,0.80000000000000004,0.8000000000000000'], ['AmbFadeIn', 'Ambientes', '{"AmbFadeIn":3}'], ['Names', 'Config', '{"Names":["a","b"]}'], ['On', 'Debug', '{"On":true}']],
  BP_Twin_SC: [['Speed', 'Config', '{"Speed":2}']] } };
const score = { rev: 7, elements: {
  el_bell1: { key: 'BELL_IN', group: 'obj' }, el_bell2: { key: 'G_BELL', group: 'int' }, el_belln: { key: 'BELL_COPY', group: 'obj', isNew: true },
  el_p: { key: 'PACER', group: 'obj' }, el_a: { key: 'AMB_01', group: 'amb' }, el_x: { key: 'OTHER', group: 'world' } } };
const assets = new Map([['BP_Pacer_SC', ['/SC_Breath/Blueprints/BP_Pacer_SC']], ['BP_Obra_SC', ['/Game/Obra/BP_Obra_SC']], ['BP_Twin_SC', ['/Game/A/BP_Twin_SC', '/Game/B/BP_Twin_SC']]]);
const inp = { def, live, binding, roles, perillas, score, assets, generated: '2026-10-08T00:00:00.000Z' };
const before = JSON.stringify(inp.roles) + JSON.stringify(inp.perillas) + JSON.stringify(inp.score);
const doc = build(inp), K = doc.knobs;

console.log('\nthe Partitura (da:*)');
check('every knob of the def, in its order, first', Object.keys(K).slice(0, 3).join() === 'da:Aviso_Dur,da:Etapa_Tope,da:Sin_Enlace');
check('the live value wins; an array stays an array; the def initial is kept apart', K['da:Aviso_Dur'].value === 21 && K['da:Aviso_Dur'].initial === 19 && same(K['da:Etapa_Tope'].value, [250, 180, 120, 240, 205]) && K['da:Etapa_Tope'].type === 'a5');
check('without a live value: the initial one, and it says so', K['da:Sin_Enlace'].value === 1 && /initial/.test(K['da:Sin_Enlace'].valueFrom) && K['da:Aviso_Dur'].valueFrom === 'partitura.json');
check('the base is the export the values come from (hash); the owner is the DA', same(K['da:Aviso_Dur'].base, { hash: 'deadbeef0000' }) && K['da:Aviso_Dur'].owner === def.asset);
check('the only proposable ones: unit s, not locked, with their category and doc', ['da:Aviso_Dur', 'da:Etapa_Tope', 'da:Sin_Enlace'].every(k => Knobs.proposable(K[k]) && K[k].unit === 's' && K[k].lock === false && K[k].category && K[k].doc));
check('binding: the knob name when bound, null when not; elements = every id the bind names, once', K['da:Aviso_Dur'].binding === 'Aviso_Dur' && K['da:Sin_Enlace'].binding === null && same(K['da:Aviso_Dur'].elements, ['el_aviso']) && same(K['da:Etapa_Tope'].elements, ['el_t0', 'el_t1', 'el_t2']) && same(K['da:Sin_Enlace'].elements, []));

console.log('\ninstance knobs, hardwired rows and class defaults from roles.json');
const fw = K['inst:Test_Hall/HallDirector.FW_Bell'];
check('FW_Bell: 25 s, locked, read-only, not harvested, its note', fw && fw.scope === 'instance' && fw.value === 25 && fw.unit === 's' && fw.lock === true && fw.proposable === false && fw.base === null && /not harvested/.test(fw.valueFrom) && fw.note.startsWith('after it') && fw.var === 'FW_Bell' && fw.label === 'Timeout');
check('a row with lock 0 is not locked; one with no lock cell is not either', K['inst:Test_Hall/HallDirector.BellHold'].lock === false);
check('a component as owner stays out of the key', 'inst:Timbre.Appear.Duration' in K && K['inst:Timbre.Appear.Duration'].owner === 'Timbre · Appear component');
check('the same variable twice: the second key is suffixed, nothing is lost', 'inst:Test_Breath/Entering_Pacer.Hold1Time' in K && 'inst:Test_Breath/Entering_Pacer.Hold1Time#2' in K);
check('the row travels verbatim with its group and place (role.row)', same(fw.role, { name: 'Bell', group: 1, order: 0, owner: 'HallDirector · Test_Hall', scope: 'instance', row: roles.roles.Bell.groups[1].rows[0] }));
const lit = K['lit:HallDirector.release'];
check('a hardwired row: no variable, its value as the text says it, never proposable', lit && lit.scope === 'literal' && lit.var === null && lit.proposable === false && lit.value === '−2 /s' && lit.role.scope === 'literal');
check('the elements of a role are frozen by id from its match, what is made in the editor left out', same(fw.elements, ['el_bell1', 'el_bell2']) && same(K['inst:Obra/BP_Obra_SC_C_0.AmbVolumes'].elements, ['el_a']));
check('roleOf: the first role that fits (key, or group)', roleOf(score.elements.el_bell1, roles) === 'Bell' && roleOf(score.elements.el_a, roles) === 'Ambiences' && roleOf(score.elements.el_x, roles) === null);

console.log('\nBlueprint defaults (cdo:*)');
const ip = K['cdo:BP_Pacer_SC.IntroTime'];
check('a class default joins the role row that names it: the label, the unit and the role link', ip && ip.value === 0.6 && ip.label === 'Intro' && ip.unit === 's' && ip.role.name === 'Pacer' && ip.role.scope === 'class default' && ip.elements[0] === 'el_p');
check('internal state is left out and counted (Interno, Z - Estado); Z-Ghost, Config and Debug stay', !('cdo:BP_Pacer_SC.State' in K) && !('cdo:BP_Pacer_SC.Mode' in K) && 'cdo:BP_Pacer_SC.Etapa' in K && 'cdo:BP_Obra_SC.On' in K && same(doc.counts.skipped, { Interno: 1, 'Z - Estado': 1 }));
check('values: numbers, arrays, booleans read from the dump', K['cdo:BP_Obra_SC.AmbFadeIn'].value === 3 && same(K['cdo:BP_Obra_SC.Names'].value, ['a', 'b']) && K['cdo:BP_Obra_SC.On'].value === true);
check('a value the dump cut short is marked truncated with its raw text, never guessed', K['cdo:BP_Obra_SC.AmbVolumes'].truncated === true && K['cdo:BP_Obra_SC.AmbVolumes'].value === null && K['cdo:BP_Obra_SC.AmbVolumes'].raw.startsWith('{"AmbVolumes":[0.8'));
check('a role row whose class default the dump does not list is still a knob, from the row', K['cdo:BP_Pacer_SC.NotInPerillas'] && K['cdo:BP_Pacer_SC.NotInPerillas'].value === 9 && /not in perillas/.test(K['cdo:BP_Pacer_SC.NotInPerillas'].valueFrom));
check('read-only by scope: no flag on a cdo entry says otherwise', Object.values(K).filter(k => k.scope === 'cdo').every(k => !Knobs.proposable(k)));
check('the asset path of each Blueprint once, in blueprints (a name two folders carry is left out)', same(doc.blueprints, { BP_Obra_SC: '/Game/Obra/BP_Obra_SC', BP_Pacer_SC: '/SC_Breath/Blueprints/BP_Pacer_SC' }));

console.log('\nthe document');
check('order: Partitura, instance, hardwired, then the Blueprints', (() => { const o = { da: 0, instance: 1, literal: 2, cdo: 3 }, s = Object.values(K).map(k => o[k.scope]); return s.every((v, i) => !i || v >= s[i - 1]); })());
check('counts by scope, with what was left out', same({ da: doc.counts.da, instance: doc.counts.instance, literal: doc.counts.literal }, { da: 3, instance: 6, literal: 1 }) && doc.counts.cdo === Object.values(K).filter(k => k.scope === 'cdo').length);
check('sources: the Partitura hash and export, the roles (verified + signature), perillas; the score only to freeze elements', doc.sources.partitura.hash === 'deadbeef0000' && doc.sources.roles.verified === '2026-10-01' && doc.sources.roles.sig === Knobs.sig(roles.roles) && doc.sources.perillas === '2026-10-02T18:06:10' && doc.sources.score.rev === 7);
check('the inputs were not touched', before === JSON.stringify(inp.roles) + JSON.stringify(inp.perillas) + JSON.stringify(inp.score));
check('the same inputs give the same bytes (but the time)', fmt(build(Object.assign({}, inp, { generated: 'x' }))) === fmt(Object.assign(clone(doc), { generated: 'x' })));
check('written one knob per line; it reads back to the same document', same(JSON.parse(fmt(doc)), doc) && fmt(doc).split('\n').filter(l => /^ {2}"da:Aviso_Dur":/.test(l)).length === 1);
{ const d2 = clone(doc); d2.generated = 'other'; d2.sources.score.rev = 9;
  check('diff ignores the time and the score\'s revision; sees a changed, added and removed knob', !diff(doc, d2).length && (() => { d2.knobs['da:Aviso_Dur'].value = 5; d2.knobs['cdo:Z.New'] = {}; delete d2.knobs['lit:HallDirector.release']; const d = diff(doc, d2); return d.includes('~ da:Aviso_Dur') && d.includes('+ cdo:Z.New') && d.includes('− lit:HallDirector.release'); })()); }

console.log('\nthe Knobs inspector reads it, roles.json is the fallback');
{
  const rows = n => roles.roles[n].groups.map(g => ({ owner: g.owner, scope: g.scope, rows: g.rows }));
  const strip = gs => gs.map(g => ({ owner: g.owner, scope: g.scope, rows: g.rows }));
  check('every role is drawn the same from here as from roles.json: owners, scopes and rows, in order', Object.keys(roles.roles).every(n => same(strip(Knobs.groupsOf(doc, n)), rows(n))), Object.keys(roles.roles).filter(n => !same(strip(Knobs.groupsOf(doc, n) || []), rows(n))).join());
  check('...each row with the key of its knob, in step', (() => { const g = Knobs.groupsOf(doc, 'Bell'); return g[1].ids[0] === 'inst:Test_Hall/HallDirector.FW_Bell' && g.every(x => x.ids.length === x.rows.length); })());
  check('a role the catalog does not know → null (the fallback)', Knobs.groupsOf(doc, 'Nobody') === null && Knobs.groupsOf(null, 'Bell') === null && Knobs.groupsOf({}, 'Bell') === null);
  check('fresh: made from this roles.json; a changed row or a missing file → not fresh', Knobs.fresh(doc, roles) && (() => { const r2 = clone(roles); r2.roles.Bell.groups[1].rows[0][1] = '26'; return !Knobs.fresh(doc, r2); })() && !Knobs.fresh(null, roles) && !Knobs.fresh({}, roles) && !Knobs.fresh(doc, null));
}

// ---- the CLI, on a temp project -----------------------------------------------------------------------------------------------
console.log('\nthe CLI');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'knobs-test-'));
const w = (rel, v) => { const p = path.join(tmp, rel); fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(p, typeof v === 'string' ? v : JSON.stringify(v)); return p; };
w('obra/unreal/partitura_def.json', def); w('obra/unreal/partitura.json', live); w('obra/unreal/partitura_binding.json', binding); w('obra/unreal/roles.json', roles); w('obra/unreal/perillas.json', perillas);
w('obra/score/score.json', score); w('VR_Test/Content/x.txt', 'x');
const hashOf = f => crypto.createHash('sha1').update(fs.readFileSync(path.join(tmp, f))).digest('hex');
const protectedFiles = ['obra/score/score.json', 'obra/unreal/partitura.json', 'obra/unreal/perillas.json', 'obra/unreal/roles.json', 'obra/unreal/partitura_def.json', 'obra/unreal/partitura_binding.json'];
const prot0 = protectedFiles.map(hashOf);
const CLI = path.join(ROOT, 'tools/score/knobs.mjs'), run = args => spawnSync(process.execPath, [CLI, '--root', tmp, ...args], { encoding: 'utf8' });
const OUT = path.join(tmp, 'obra/unreal/knobs.json');
let r = run([]);
check('it writes obra/unreal/knobs.json', r.status === 0 && fs.existsSync(OUT) && /written/.test(r.stdout), (r.stderr || r.stdout).split('\n')[0]);
const w1 = fs.readFileSync(OUT, 'utf8'), m1 = fs.statSync(OUT).mtimeMs, d1 = JSON.parse(w1);
check('the file is the catalog: da, instance, hardwired, Blueprint defaults', d1.counts.da === 3 && d1.counts.instance === 6 && d1.knobs['da:Aviso_Dur'].value === 21 && d1.knobs['inst:Test_Hall/HallDirector.FW_Bell'].value === 25);
r = run([]);
check('a re-run that changes nothing leaves the file alone', r.status === 0 && /nothing changed/.test(r.stdout) && fs.readFileSync(OUT, 'utf8') === w1 && fs.statSync(OUT).mtimeMs === m1);
check('--check: up to date → exit 0', run(['--check']).status === 0);
{ const p2 = clone(perillas); p2.bps.BP_Obra_SC[1][2] = '{"AmbFadeIn":4}'; w('obra/unreal/perillas.json', p2);
  r = run(['--check']);
  check('--check: a value that changed in perillas → exit 1, it says which', r.status === 1 && /~ cdo:BP_Obra_SC.AmbFadeIn/.test(r.stdout));
  w('obra/unreal/perillas.json', perillas); }
{ const l2 = clone(live); l2.valores.Aviso_Dur = 22; l2.hash = 'newhash'; w('obra/unreal/partitura.json', l2);
  r = run(['--check']);
  check('--check: a new Partitura export → exit 1', r.status === 1 && /~ da:Aviso_Dur/.test(r.stdout));
  w('obra/unreal/partitura.json', live); }
{ const s2 = clone(score); s2.rev = 8; w('obra/score/score.json', s2);
  check('a new revision of the score alone is not a change', run(['--check']).status === 0);
  s2.elements.el_new = { key: 'BELL_NEW', group: 'obj' }; w('obra/score/score.json', s2);
  r = run(['--check']);
  check('an element that joins a role is (its id is frozen into the catalog)', r.status === 1 && /~ inst:Test_Hall\/HallDirector\.FW_Bell/.test(r.stdout));
  w('obra/score/score.json', score); }
check('no score given and none on disk: the catalog is made without elements', (() => { fs.unlinkSync(path.join(tmp, 'obra/score/score.json')); const x = run(['--out', 'obra/unreal/knobs_noscore.json']); const ok = x.status === 0 && JSON.parse(fs.readFileSync(path.join(tmp, 'obra/unreal/knobs_noscore.json'), 'utf8')).knobs['inst:Test_Hall/HallDirector.FW_Bell'].elements.length === 0; w('obra/score/score.json', score); return ok; })());

console.log('\nwhere it may write');
check('inside the Unreal project, the score, the Director\'s files and the other tools\': refused', !!outProblem(tmp, path.join(tmp, 'VR_Test/Content/knobs.json')) && !!outProblem(tmp, path.join(tmp, 'obra/score/score.json'))
  && ['partitura.json', 'perillas.json', 'traza.json', 'LEEME.md', 'roles.json', 'contract.json', 'idmap.json'].every(f => !!outProblem(tmp, path.join(tmp, 'obra/unreal', f))));
check('the previous catalog and a new file: allowed; an existing file that is not a catalog: refused', outProblem(tmp, OUT) === null && outProblem(tmp, path.join(tmp, 'obra/unreal/knobs_new.json')) === null && (() => { w('obra/unreal/not_knobs.json', '{"a":1}'); return !!outProblem(tmp, path.join(tmp, 'obra/unreal/not_knobs.json')); })());
for (const bad of ['VR_Test/knobs.json', 'obra/score/score.json', 'obra/unreal/roles.json']) {
  const h0 = fs.existsSync(path.join(tmp, bad)) ? hashOf(bad) : null;
  r = run(['--out', bad]);
  check(`--out ${bad} → exit 1, nothing written`, r.status === 1 && /refused/.test(r.stderr) && (fs.existsSync(path.join(tmp, bad)) ? hashOf(bad) : null) === h0);
}
check('every input file is byte for byte as it was', same(protectedFiles.map(hashOf), prot0));
fs.rmSync(tmp, { recursive: true, force: true });

// ---- the real catalog ---------------------------------------------------------------------------------------------------------
console.log('\nthe real obra/unreal/knobs.json against the files it was made from');
{
  const file = path.join(ROOT, 'obra/unreal/knobs.json');
  if (!fs.existsSync(file)) check('obra/unreal/knobs.json exists (node tools/score/knobs.mjs)', false);
  else {
    const real = rd('obra/unreal/knobs.json'), R = rd('obra/unreal/roles.json'), D = rd('obra/unreal/partitura_def.json'), L = rd('obra/unreal/partitura.json'), P = rd('obra/unreal/perillas.json');
    const da = Object.entries(real.knobs).filter(([k]) => k.startsWith('da:'));
    check('60 Partitura knobs, one per knob of partitura_def.json, with the live value of partitura.json', da.length === D.knobs.length && D.knobs.every(d => same(real.knobs['da:' + d.name] && real.knobs['da:' + d.name].value, L.valores[d.name])) && D.knobs.length === 60);
    check('...their type and initial value, the export they come from, all proposable', D.knobs.every(d => { const k = real.knobs['da:' + d.name]; return k.type === d.type && same(k.initial, d.initial) && k.base && k.base.hash === L.hash && Knobs.proposable(k); }));
    check('a5 knobs hold five values (one per stage)', da.filter(([, k]) => k.type === 'a5').length === 4 && da.filter(([, k]) => k.type === 'a5').every(([, k]) => Array.isArray(k.value) && k.value.length === 5));
    const fwb = real.knobs['inst:Test_Hall/HallDirector.FW_Bell'];
    check('FW_Bell: 25 s, locked, read-only, read from roles.json', fwb && fwb.value === 25 && fwb.unit === 's' && fwb.lock === true && !Knobs.proposable(fwb) && fwb.elements.length > 0);
    check('50 instance rows + 4 hardwired, every one of roles.json', Object.keys(real.knobs).filter(k => k.startsWith('inst:')).length === 50 && Object.keys(real.knobs).filter(k => k.startsWith('lit:')).length === 4
      && R && Object.values(R.roles).reduce((a, x) => a + x.groups.filter(g => g.scope === 'instance' || g.scope === 'literal').reduce((b, g) => b + g.rows.length, 0), 0) === 54);
    const cdo = Object.values(real.knobs).filter(k => k.scope === 'cdo'), internal = Object.values(P.bps).flat().filter(r => Knobs.isInternal(r[1])).length;
    check('no Blueprint default is internal state; the ones left out are counted', cdo.every(k => !Knobs.isInternal(k.category)) && Object.values(real.counts.skipped).reduce((a, b) => a + b, 0) === internal && internal > 300, `${cdo.length} kept, ${internal} left out`);
    check('...all the rest of perillas.json is there (kept + left out = every row)', cdo.length + internal === Object.values(P.bps).flat().length + Object.values(real.knobs).filter(k => k.scope === 'cdo' && /not in perillas/.test(k.valueFrom || '')).length);
    check('every role is drawn the same from the catalog as from roles.json', Object.keys(R.roles).every(n => same((Knobs.groupsOf(real, n) || []).map(g => ({ owner: g.owner, scope: g.scope, rows: g.rows })), R.roles[n].groups.map(g => ({ owner: g.owner, scope: g.scope, rows: g.rows })))), Object.keys(R.roles).filter(n => !Knobs.groupsOf(real, n)).join());
    check('it was made from this roles.json (signature): else the inspector reads roles.json — run node tools/score/knobs.mjs', Knobs.fresh(real, R));
    // the rest of the file against a fresh build of the same files (the frozen elements follow the score the owner edits: left apart)
    const fresh = build(Object.assign(readInputs(ROOT, null), { assets: new Map(), generated: 'x' })), a = clone(real), b = clone(fresh);
    for (const x of [a, b]) { delete x.blueprints; for (const k of Object.values(x.knobs)) delete k.elements; if (x.sources) delete x.sources.score; }
    const dd = diff(a, b);
    check('up to date with partitura_def.json, partitura.json, roles.json and perillas.json (node tools/score/knobs.mjs --check)', !dd.length, dd.slice(0, 5).join('; '));
    check('the frozen elements are ids', Object.values(real.knobs).every(k => !k.elements || k.elements.every(id => /^el_[A-Za-z0-9]{3,40}$/.test(id))));
  }
}

console.log(fails ? `\n${fails} FAILED` : '\nall ok');
process.exit(fails ? 1 : 0);
