// obra/unreal/knobs.json: the knobs of Unreal in a form a machine can read (lote 5 design A §8.1, audit D13). Made from files only,
// never from Unreal itself, and never writing anything but --out:
//   da:*    the 60 knobs of DA_Partitura_Obra: obra/unreal/partitura_def.json (names, types, initial values) + the live values of
//           obra/unreal/partitura.json. The only ones a change can be PROPOSED for (Send to Unreal).
//   inst:*  the knobs of instances (FW_Bell, ExploreTime...) parsed from the rows of obra/unreal/roles.json: read-only, since their
//           values are written down by a person, not harvested from Unreal (an instance harvest does not exist yet).
//   lit:*   what the graphs hardwire (roles.json rows of scope "literal").
//   cdo:*   the class defaults of the Blueprints, from obra/unreal/perillas.json (the Director's dump of the CDOs), without the
//           variables a Blueprint keeps for its own state (category "Interno" and the Z- state categories: js/knobs.js). Compact:
//           read-only by their scope; the asset path of each Blueprint is in `blueprints`; a value the dump cut short is
//           `truncated` with its `raw` text.
// The roles' rows travel verbatim in their entries (`role.row`), so the Knobs inspector draws the same from here as from roles.json
// (js/knobs.js groupsOf); `sources.roles.sig` says which roles.json it was made from. The elements of a role are frozen by id from the
// score (read only), like contract.json: a rename never loses them.
//
//   node tools/score/knobs.mjs                      → write obra/unreal/knobs.json
//   node tools/score/knobs.mjs --check              → exit 1 if the file on disk differs from a fresh one (nothing written)
//   [--score <score.json>]  [--out <file>]  [--root <repo>]
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { scanAssets } from './bind_ids.mjs';

const require = createRequire(import.meta.url);
export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const Knobs = require(path.join(ROOT, 'web/editor-obra/app/js/knobs.js'));
const clone = o => JSON.parse(JSON.stringify(o));
const own = (o, k) => !!o && Object.prototype.hasOwnProperty.call(o, k);

/* the role an element belongs to: the first whose `match` fits (as the Knobs inspector does, ui.js roleFor) */
export function roleOf(e, roles) {
  for (const [name, r] of Object.entries(roles.roles)) { const m = r.match || {}; if ((m.group && m.group === e.group) || (m.key && new RegExp(m.key).test(e.key))) return name; }
  return null;
}

/* every id a binding names (per stage, one for all, or a pair for a gap), once, in order */
function idsOf(bind) {
  const out = [], add = v => { if (typeof v === 'string') { if (!out.includes(v)) out.push(v); } else if (Array.isArray(v)) v.forEach(add); else if (v && typeof v === 'object') Object.values(v).forEach(add); };
  add(bind && bind.ids); return out;
}

/* the catalog, pure on its inputs:
   in = { def, live, binding, roles, perillas, score, assets (Map name → [paths], optional), generated } → the document */
export function build(inp) {
  const { def, live, binding, roles, perillas, score } = inp, K = {}, skippedCats = {};
  const put = (key, entry) => { let k = key, n = 2; while (own(K, k)) k = key + '#' + n++; K[k] = entry; return k; };

  // the elements of each role, frozen by id (what is made in the editor is not in Unreal)
  const elsOf = {};
  for (const [id, e] of Object.entries((score && score.elements) || {})) { if (e.isNew) continue; const r = roleOf(e, roles); if (r) (elsOf[r] = elsOf[r] || []).push(id); }

  // da:* — the Partitura
  const liveVals = live && (live.valores || live.values) ? (live.valores || live.values) : {}, hash = live && live.hash ? live.hash : null;
  for (const d of def.knobs) {
    const bind = (binding.binds || []).find(b => b.knob === d.name), has = own(liveVals, d.name);
    K['da:' + d.name] = { scope: 'da', owner: def.asset, var: d.name, type: d.type, unit: 's', value: has ? liveVals[d.name] : d.initial, initial: d.initial,
      valueFrom: has ? 'partitura.json' : 'partitura_def.json (initial; no live export)', base: hash ? { hash } : null, proposable: true, lock: false,
      category: d.category, doc: d.doc, binding: bind ? d.name : null, elements: idsOf(bind) };
  }

  // inst:* and lit:* — the rows of roles.json; the class-default rows enrich the cdo entries below
  const classRows = {};   // 'BP_Pacer_SC.IntroTime' → { role, ... }
  for (const [rname, R] of Object.entries(roles.roles)) {
    (R.groups || []).forEach((g, gi) => (g.rows || []).forEach((row, ri) => {
      const link = { name: rname, group: gi, order: ri, owner: g.owner, scope: g.scope, row: clone(row) };
      const label = row[0], pv = Knobs.parseVar(row[5]), lock = !!row[6], elements = elsOf[rname] || [];
      if (g.scope === 'literal') {
        put(Knobs.litKey(g.owner, label), { scope: 'literal', owner: g.owner, var: null, label, value: Knobs.parseValue(row[1]), unit: row[2] || '', note: pv.note, valueFrom: 'roles.json (text; read from the graph by a person)',
          base: null, proposable: false, lock: false, role: link, elements });
      } else if (g.scope === 'class default') {
        classRows[g.owner + '.' + pv.var] = { role: link, label, unit: row[2] || '', lock, note: pv.note, value: Knobs.parseValue(row[1]), elements };
      } else {
        put(Knobs.instKey(g.owner, pv.var || Knobs.slug(label)), { scope: 'instance', owner: g.owner, var: pv.var, label, value: Knobs.parseValue(row[1]), unit: row[2] || '', note: pv.note,
          valueFrom: 'roles.json (text; not harvested from Unreal)', base: null, proposable: false, lock, role: link, elements });
      }
    }));
  }

  // cdo:* — the class defaults of the Blueprints (perillas.json). Compact on purpose (1200 of them): the scope says it is read-only, a
  // Blueprint's asset path is said once in `blueprints`, and `lock`/`valueFrom` appear only when they are not the default
  const seen = new Set(), bps = {};
  const assetOf = bp => { const a = inp.assets && inp.assets.get(bp); if (a && a.length === 1) bps[bp] = a[0]; };
  for (const bp of Object.keys((perillas && perillas.bps) || {})) {
    for (const row of perillas.bps[bp]) {
      if (!Array.isArray(row)) continue;
      const [name, cat, raw] = row;
      if (Knobs.isInternal(cat)) { skippedCats[cat] = (skippedCats[cat] || 0) + 1; continue; }
      let value = null, truncated = false;
      try { const o = JSON.parse(raw); value = o && own(o, name) ? o[name] : null; } catch (_) { truncated = true; }
      assetOf(bp);
      const e = { scope: 'cdo', owner: bp, var: name, category: cat, value };
      if (truncated) { e.truncated = true; e.raw = raw; }
      const cr = classRows[bp + '.' + name];
      if (cr) { e.label = cr.label; e.unit = cr.unit; if (cr.lock) e.lock = true; e.role = cr.role; e.elements = cr.elements; seen.add(bp + '.' + name); }
      put('cdo:' + bp + '.' + name, e);
    }
  }
  // a role row of a class default that perillas.json does not list (or lists as internal): still a knob, from the row
  for (const [k, cr] of Object.entries(classRows)) {
    if (seen.has(k)) continue;
    const i = k.lastIndexOf('.'), bp = k.slice(0, i), name = k.slice(i + 1);
    assetOf(bp);
    const e = { scope: 'cdo', owner: bp, var: name, label: cr.label, value: cr.value, unit: cr.unit, valueFrom: 'roles.json (text; not in perillas.json)', role: cr.role, elements: cr.elements };
    if (cr.lock) e.lock = true;
    put('cdo:' + k, e);
  }

  // a stable order: da (as the def lists them), inst, lit, cdo (by Blueprint, as the dump lists them)
  const ord = { da: 0, instance: 1, literal: 2, cdo: 3 }, keys = Object.keys(K).sort((a, b) => ord[K[a].scope] - ord[K[b].scope]);
  const out = {}; for (const k of keys) out[k] = K[k];
  return {
    generated: inp.generated,
    note: 'Unreal\'s knobs in a form a machine can read, made by tools/score/knobs.mjs from partitura_def.json, partitura.json, roles.json and perillas.json (the Director\'s files): nothing here is read from Unreal. Only da:* can be proposed (Send to Unreal); the rest is read-only.',
    sources: {
      partitura: live ? { hash, exported: live.exportado || null } : null,
      def: { synced: def.synced || null, sourceSha1: def.sourceSha1 || null },
      perillas: perillas ? (perillas.exportado || null) : null,
      roles: { verified: roles.verified || null, sig: Knobs.sig(roles.roles) },
      score: score ? { file: 'obra/score/score.json', rev: score.rev == null ? null : score.rev, note: 'only to freeze the elements of each role by id' } : null,
    },
    counts: Object.assign(Knobs.counts({ knobs: out }), { skipped: skippedCats }),
    blueprints: Object.fromEntries(Object.keys(bps).sort().map(k => [k, bps[k]])),
    knobs: out,
  };
}

/* ---------- writing: one knob per line, so a diff reads ---------- */
export function fmt(doc) {
  const rows = Object.keys(doc).map(k => {
    if (k === 'knobs') return ' "knobs": {\n' + Object.keys(doc.knobs).map(n => '  ' + JSON.stringify(n) + ': ' + JSON.stringify(doc.knobs[n])).join(',\n') + '\n }';
    return ' ' + JSON.stringify(k) + ': ' + JSON.stringify(doc[k]);
  });
  return '{\n' + rows.join(',\n') + '\n}\n';
}

/* what differs between two catalogs, leaving the time (and the score's revision: it says nothing about a knob) out */
export function diff(a, b) {
  const lines = [], strip = o => { const c = clone(o); delete c.generated; if (c.sources) delete c.sources.score; return c; };
  const A = strip(a), B = strip(b);
  for (const k of Object.keys(B.knobs)) if (!own(A.knobs, k)) lines.push('+ ' + k);
  for (const k of Object.keys(A.knobs)) if (!own(B.knobs, k)) lines.push('− ' + k);
  for (const k of Object.keys(B.knobs)) if (own(A.knobs, k) && JSON.stringify(A.knobs[k]) !== JSON.stringify(B.knobs[k])) lines.push('~ ' + k);
  for (const k of ['sources', 'counts', 'note', 'blueprints']) if (JSON.stringify(A[k]) !== JSON.stringify(B[k])) lines.push(k + ' differs');
  return lines;
}

/* where --out may be: not in the Unreal project, not a score file, not a file of the Director or of another tool; if it exists, a
   previous knobs.json */
export function outProblem(root, out) {
  const rel = path.relative(root, out).replace(/\\/g, '/');
  if (rel.startsWith('..')) return null;
  if (/^VR_Test(\/|$)/.test(rel)) return `${rel} is inside the Unreal project: this tool never writes there`;
  if (/^obra\/score\//.test(rel)) return `${rel} is a score file: this tool never writes the score`;
  if (/^obra\/unreal\/(partitura|perillas|traza|LEEME|roles|contract|idmap)/.test(rel) && !/knobs/.test(path.basename(rel))) return `${rel} belongs to the Director or to another tool`;
  if (fs.existsSync(out)) { try { const d = JSON.parse(fs.readFileSync(out, 'utf8')); if (!d || typeof d.knobs !== 'object' || !d.sources) return `${rel} exists and is not a knobs catalog`; } catch (_) { return `${rel} exists and is not a knobs catalog`; } }
  return null;
}

/* the files of a repo, read */
export function readInputs(root, scorePath) {
  const rd = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));
  const opt = p => { try { return rd(p); } catch (_) { return null; } };
  return { def: rd('obra/unreal/partitura_def.json'), live: opt('obra/unreal/partitura.json'), binding: opt('obra/unreal/partitura_binding.json') || { binds: [] }, roles: rd('obra/unreal/roles.json'),
    perillas: opt('obra/unreal/perillas.json'), score: scorePath ? JSON.parse(fs.readFileSync(scorePath, 'utf8')) : null };
}

/* ---------- CLI ---------- */
if (process.argv[1] && import.meta.url.toLowerCase() === pathToFileURL(path.resolve(process.argv[1])).href.toLowerCase()) {
  const argv = process.argv.slice(2), has = f => argv.includes(f), arg = f => { const i = argv.indexOf(f); return i >= 0 ? argv[i + 1] : null; };
  const root = path.resolve(arg('--root') || ROOT), out = path.resolve(root, arg('--out') || 'obra/unreal/knobs.json');
  const log = s => console.log(s), die = s => { console.error(s); process.exit(1); };
  const bad = outProblem(root, out); if (bad) die('refused: ' + bad);
  const scorePath = path.resolve(root, arg('--score') || 'obra/score/score.json');
  let inp; try { inp = readInputs(root, fs.existsSync(scorePath) ? scorePath : null); } catch (e) { die('could not read the inputs: ' + e.message); }
  const assets = fs.existsSync(path.join(root, 'VR_Test')) ? scanAssets(root) : new Map();
  const doc = build(Object.assign(inp, { assets, generated: new Date().toISOString() }));
  const c = doc.counts;
  log(`${Object.keys(doc.knobs).length} knobs: ${c.da} Partitura (da), ${c.instance} instance (inst), ${c.literal} hardwired (lit), ${c.cdo} Blueprint defaults (cdo)`
    + (Object.keys(c.skipped).length ? ` · left out as internal state: ${Object.values(c.skipped).reduce((a, b) => a + b, 0)} variables (${Object.keys(c.skipped).join(', ')})` : ''));
  log(inp.live ? `live values: DA_Partitura_Obra ${doc.sources.partitura.hash}, exported ${doc.sources.partitura.exported}` : 'no obra/unreal/partitura.json: the da values are the initial ones');
  if (has('--check')) {
    let disk = null; try { disk = JSON.parse(fs.readFileSync(out, 'utf8')); } catch (_) {}
    if (!disk) { log(`${path.relative(root, out)} is missing or unreadable`); process.exit(1); }
    const d = diff(disk, doc);
    log(d.length ? `${path.relative(root, out)} is out of date:\n  ` + d.slice(0, 40).join('\n  ') + (d.length > 40 ? `\n  … ${d.length - 40} more` : '') : `${path.relative(root, out)} is up to date`);
    process.exit(d.length ? 1 : 0);
  }
  let keep = null; try { keep = JSON.parse(fs.readFileSync(out, 'utf8')); } catch (_) {}
  if (keep && !diff(keep, doc).length) { log(`${path.relative(root, out)}: nothing changed, not rewritten`); process.exit(0); }
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, fmt(doc));
  log(`written: ${path.relative(root, out)}`);
}
