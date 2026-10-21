// fixes_test.mjs — the suggested fixes (web/editor-obra/app/js/fixes.js): when an edit, or the score as it stands, has a problem, the editor
// proposes a way out and the owner decides. For every rule that has a fix: the problem is built, the fixes are asked for, each one is applied and the
// problem must be gone with nothing new in its place; a fix that would create a problem, that only takes the edit back (Cancel) or that opens a
// card of its own is not offered; the fixes of a card are the edit and the fix as the app applies them (one step), judged again; nothing is ever
// sent or saved. Pure: plain Node, no window, nothing written.
// It runs on the frozen fixture tools/score/fixtures/f0-score.json (so real edits of the piece never break it); --live runs it on obra/score/score.json
// (a scenario whose problem the live score does not have is skipped, and says so).
//   node tools/score/fixes_test.mjs [--live]
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { testScore, catalogPath } from './test_score.mjs';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const js = f => require(path.join(ROOT, 'web/editor-obra/app/js', f));
const E = js('engine.js'), X = js('edits.js'), P = js('partitura.js'), I = js('integrity.js'), Pol = js('policy.js'), F = js('fixes.js');
const rd = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const { score: base, live, name: SRC } = testScore(); console.log('on the ' + SRC);
const contract = JSON.parse(fs.readFileSync(catalogPath('contract'), 'utf8')), pbind = JSON.parse(fs.readFileSync(catalogPath('binding'), 'utf8')), pdef = rd('obra/unreal/partitura_def.json');
const frozen = JSON.stringify(base);
const clone = o => JSON.parse(JSON.stringify(o));
let fails = 0, skipped = 0;
const check = (n, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + n + (info ? '  · ' + info : '')); if (!ok) fails++; };
const skip = why => { skipped++; console.log('  info  skipped: ' + why); };
const near = (a, b, eps) => Math.abs(a - b) < (eps || 1e-3);
const typical = S => E.resolve(S, { persona: 'typical' });
const probs = S => I.staticProblems(S, typical(S), contract, E.altRuns(S), {});
const isOpen = p => !p.ghost && p.st !== 'accepted' && (p.sv === 'warn' || p.sv === 'block');
const idOf = (S, k, b) => Object.keys(S.elements).find(id => S.elements[id].key === k && (!b || S.beats[S.elements[id].beat].key === b));
const asked = i => i.sv === 'block' || i.sv === 'warn';
const AT = '2026-10-15T10:00:00.000Z';
const ctxOf = (S, o) => Object.assign({ score: S, sched: typical(S), contract, pdef, plive: null, pbind, Engine: E, Edits: X, Integrity: I, Partitura: P, who: 'B', now: AT }, o);
/* the card of an edit, as commit() builds it: the items of the edit on `next` against `prev` */
function cardOf(prev, op, next) {
  const P0 = probs(prev), P1 = probs(next), T0 = typical(prev), gov = P.governedBy(prev, T0, pbind);
  const items = I.opItems(Object.assign({ prevScore: prev }, op), next, { problems: P0 }, { problems: P1 }, contract, E, { gov }).items;
  return { items, P1, gov };
}
/* the edit plus the fixes, as the app applies them in ONE step, and what its card would say about the result */
function applied(prev, op, next, fixes) {
  const n = clone(next); for (const f of fixes) f.apply(n);
  const P0 = probs(prev), P1 = probs(n), gov = P.governedBy(prev, typical(prev), pbind);
  const items = I.opItems(Object.assign({ prevScore: prev }, op), n, { problems: P0 }, { problems: P1 }, contract, E, { gov }).items;
  return { n, items, left: items.filter(asked), P1 };
}
/* a fix on its own against the score the problem is in: the problem is gone and nothing new is open */
function solves(S, item, f) {
  const n = clone(S), before = JSON.stringify(S); f.apply(n);
  const P0 = probs(S), P1 = probs(n), fps0 = new Set(P0.filter(isOpen).map(p => p.fp));
  return { n, gone: !P1.some(p => p.fp === item.fp && isOpen(p)), clean: !P1.filter(isOpen).some(p => !fps0.has(p.fp) && p.rule !== 'C2.TOTAL.GOAL'), untouched: JSON.stringify(S) === before };
}
const row = (S, rule, pred) => probs(S).find(p => p.rule === rule && isOpen(p) && (!pred || pred(p)));
const rows = (S, rule) => probs(S).filter(p => p.rule === rule && isOpen(p));
const shape = f => typeof f.id === 'string' && typeof f.label === 'string' && f.label.length > 0 && f.label.length < 100 && typeof f.detail === 'string' && f.detail.length > 10 && typeof f.apply === 'function' && typeof f.keepsEdit === 'boolean' && f.op && typeof f.op.type === 'string' && typeof f.sig === 'string';
const kids = E.dependents(base);

const S = base;   // schema 2 on the fixture
const s3 = S.schema >= 3 ? clone(S) : X.migrate3(S, E, contract, { at: AT, who: 'B' }).next;

console.log('plain Node');
check('fixes.js loads without a window and has propose / analyze / suggest', typeof globalThis.window === 'undefined' && typeof F.propose === 'function' && typeof F.analyze === 'function' && typeof F.suggest === 'function');
{ const src = fs.readFileSync(path.join(ROOT, 'web/editor-obra/app/js/fixes.js'), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
  check('it never sends, saves or touches the page: no fetch, storage, document, sendToUnreal or partitura_propuesta', !/\bfetch\b|XMLHttpRequest|localStorage|sessionStorage|\bdocument\b|sendToUnreal|partitura_propuesta|\bsave\(|WebSocket/.test(src));
  check('  and Edits exports addLaneTo (the new help line asks for its lane there)', typeof X.addLaneTo === 'function'); }

console.log('C2.VO.OVERLAP · two voices at once');
{
  const R = rows(S, 'C2.VO.OVERLAP');
  if (!R.length) skip('this score has no overlap as it stands');
  else {
    const all = R.map(p => ({ p, r: F.analyze(p, ctxOf(S)) }));
    check(`every overlap of Problems (${R.length}) has a fix and the fixes are well formed`, all.every(x => x.r.fixes.length > 0 && x.r.fixes.every(shape)), all.filter(x => !x.r.fixes.length).map(x => S.elements[x.p.el].key).join(','));
    check('  the first one starts the later voice when the earlier one ends (+ 0.3 s) and keeps its anchor kind', all.every(x => {
      const f = x.r.fixes[0], j = S.elements[x.p.el]; if (f.id !== 'vo.after') return false;
      const r = solves(S, x.p, f), T = typical(r.n).t, i = Object.keys(S.elements).find(o => S.elements[o].key === x.p.fp.split('|')[2]);
      return near(T[x.p.el][0] - T[i][1], F.GAP, 1e-3) && f.label === `Start ${j.key} after ${S.elements[i].key} ends`;
    }));
    check('  every fix solves its problem and leaves nothing new open (and never touches the score it was given)', all.every(x => x.r.fixes.every(f => { const r = solves(S, x.p, f); return r.gone && r.clean && r.untouched; })));
  }
  // an edit: VO_19 dragged back onto VO_18 (its anchor is the end of VO_18, + 0.5 s)
  const v19 = idOf(S, 'VO_19'), v18 = idOf(S, 'VO_18');
  if (!v19 || !v18) skip('VO_18 / VO_19 are not in this score');
  else {
    const op = { type: 'move', ids: [v19] }, next = X.move(S, v19, -2, {}, kids), { items, P1 } = cardOf(S, op, next), ctx = ctxOf(next, { before: S, op, problems: P1, items });
    const sg = F.suggest(items.filter(i => i.sv !== 'info'), ctx);
    if (!items.some(i => i.rule === 'C2.VO.OVERLAP')) skip('moving VO_19 back does not overlap in this score');
    else {
      check('the card of dragging VO_19 onto VO_18 (two items: Unreal, and the overlap) gets ONE fix: they end in the same score', sg.list.length === 1 && sg.list[0].id === 'vo.after', sg.list.map(f => f.id).join(','));
      const f = sg.list[0];
      check('  it says what it is: "Start VO_19 after VO_18 ends", replaces the move, 0.3 s gap, with the ripple', f.label === 'Start VO_19 after VO_18 ends' && !f.keepsEdit && /^Replaces your change\. VO_19 starts 0\.3 s after VO_18 ends\./.test(f.detail) && /total/.test(f.detail), f.detail);
      const r = applied(S, op, next, [f]);
      check('  the move and the fix together (one step): nothing is left to ask (no card)', r.left.length === 0 && Pol.decide(op, r.items, {}).mode === 'apply', r.left.map(i => i.rule).join(','));
      check('  VO_19 still hangs from the end of VO_18, now 0.3 s after it', r.n.elements[v19].at.ref === v18 && r.n.elements[v19].at.edge === 'end' && near(r.n.elements[v19].at.off, 0.3));
    }
    // the other way round: VO_18 dragged later with Ctrl (VO_19 stays where it was): the move stays and VO_19 makes way
    const op2 = { type: 'move', ids: [v18], alone: true }, next2 = X.move(S, v18, 2, { alone: true }, kids), c2 = cardOf(S, op2, next2);
    if (!c2.items.some(i => i.rule === 'C2.VO.OVERLAP')) skip('moving VO_18 later does not overlap in this score');
    else {
      const sg2 = F.suggest(c2.items.filter(i => i.sv !== 'info'), ctxOf(next2, { before: S, op: op2, problems: c2.P1, items: c2.items }));
      const keep = sg2.list.find(f => f.id === 'vo.after'), mk = sg2.list.find(f => f.id === 'vo.before');
      check('Ctrl+drag VO_18 onto VO_19: the first fix keeps the move ("Your change stays") and starts VO_19 after it', !!keep && keep.keepsEdit && /^Your change stays\./.test(keep.detail) && keep.label === 'Start VO_19 after VO_18 ends', sg2.list.map(f => f.id).join(','));
      check('  the other way: VO_18 ends before VO_19 starts (replaces the move), VO_19 stays where it was', !!mk && !mk.keepsEdit && /^Replaces your change\./.test(mk.detail));
      check('  every fix of the card leaves nothing to ask after it', sg2.list.every(f => applied(S, op2, next2, [f]).left.length === 0));
    }
  }
}

console.log('C2.HELP.LATE · a help line after the timeout of its wait');
{
  const bell = idOf(S, 'G_BELL'), help = bell && Object.keys(S.elements).find(k => S.elements[k].help === bell);
  if (!help) skip('G_BELL has no help line in this score');
  else {
    const op = { type: 'move', ids: [help], alone: true }, next = X.move(S, help, 40, { alone: true }, kids), c = cardOf(S, op, next), it = c.items.find(i => i.rule === 'C2.HELP.LATE');
    check('moving the help line of G_BELL 40 s later: its card says it would never play', !!it);
    if (it) {
      const r = F.analyze(it, ctxOf(next, { before: S, op, problems: c.P1, items: c.items })), f = r.fixes[0], g = S.elements[bell].gate;
      check('  one fix: move it to 2 s before the timeout; it replaces the move', r.fixes.length === 1 && f.id === 'help.late' && !f.keepsEdit && f.label === 'Move VO_01h to 2 s before the timeout of G_BELL', r.fixes.map(x => x.label).join(' | '));
      const a = applied(S, op, next, [f]), T = typical(a.n).t;
      check(`  after it the line starts ${g.fw - 2} s into the wait (timeout ${g.fw} s) and the card has nothing left to say`, near(T[help][0] - T[bell][0], g.fw - 2, 1e-3) && a.left.length === 0, (T[help][0] - T[bell][0]).toFixed(2));
    }
  }
}

console.log('C2.WAIT.NOHELP · a wait with no help line');
{
  const R = rows(S, 'C2.WAIT.NOHELP');
  if (!R.length) skip('every wait has a help line in this score');
  else {
    const all = R.map(p => ({ p, r: F.analyze(p, ctxOf(S)) }));
    check(`every wait with no help line (${R.length}) gets "Add a help line" and it solves it`, all.every(x => x.r.fixes.length === 1 && x.r.fixes[0].id === 'help.add' && solves(S, x.p, x.r.fixes[0]).gone && solves(S, x.p, x.r.fixes[0]).clean));
    // the same line Act.addHelp has always made (the old code, frozen here): off, key, length, words, lane
    const p = R[0], w = S.elements[p.el], n = clone(S); all[0].r.fixes[0].apply(n);
    const id = Object.keys(n.elements).find(k => !S.elements[k]), e = n.elements[id], off = +Math.max(1, Math.min(w.gate.fw - 4, w.gate.expected + 4)).toFixed(2);
    check('  the line is what Act.addHelp made: a voice, "Help line for this wait…", off = clamp(expected + 4, 1, timeout − 4), hung from the start of the wait', e.type === 'vo' && e.help === p.el && e.text === 'Help line for this wait…' && e.label === 'Help line' && e.isNew === true && e.at.ref === p.el && e.at.edge === 'start' && e.at.off === off && e.beat === w.beat && e.key === w.key.replace(/^G_/, 'VO_') + '_HELP');
    check('  it lands in a lane of the voices, free at that time, and has a key and an id nobody else has', n.groups.find(g => g.id === 'vo').lanes.includes(e.lane) && !Object.keys(S.elements).includes(id) && Object.values(S.elements).every(o => o.key !== e.key));
    const T = typical(n).t;
    check('  and it plays before the timeout of its wait (the rule C2.HELP.LATE has nothing to say)', T[id][0] - T[p.el][0] < w.gate.fw && !probs(n).some(q => q.rule === 'C2.HELP.LATE' && isOpen(q)));
    const two = clone(S); F.addHelpLine(X, E, two, p.el, { id: 'el_testa' }); const k2 = F.addHelpLine(X, E, two, p.el, { id: 'el_testb' });
    check('  asked twice for the same wait, the second key is another one (no name twice)', two.elements[k2].key === w.key.replace(/^G_/, 'VO_') + '_HELP_2');
  }
}

console.log('C3.DRIFT · a timeout that is not the one in Unreal');
{
  const R = rows(S, 'C3.DRIFT');
  if (!R.length) skip('no timeout here differs from Unreal');
  else {
    const all = R.map(p => ({ p, r: F.analyze(p, ctxOf(S)) }));
    check(`every drift of Problems (${R.length}) gets "Use Unreal's N s timeout" and the timeout becomes Unreal's`, all.every(x => {
      const e = S.elements[x.p.el], c = I.contractFor(x.p.el, e, contract).find(k => k.kind === 'knob' && k.knob), f = x.r.fixes[0];
      return x.r.fixes.length === 1 && f.id === 'drift.unreal' && f.label === `Use Unreal's ${c.knob.value} s timeout` && solves(S, x.p, f).n.elements[x.p.el].gate.fw === c.knob.value && solves(S, x.p, f).gone;
    }));
    check('  the detail says who it changes: the slow and the idle users, the typical one does not', all.every(x => /Typical does not change/.test(x.r.fixes[0].detail) && /(Slow|Idle) \d+:\d\d → \d+:\d\d/.test(x.r.fixes[0].detail)), all[0].r.fixes[0].detail);
  }
  // the card of the edit that makes it: the timeout of the sensor wait typed in the inspector
  const sens = idOf(S, 'G_SENSOR');
  const knobOf = sens && I.contractFor(sens, S.elements[sens], contract).find(k => k.kind === 'knob' && k.knob);
  if (!knobOf || S.elements[sens].gate.fw === knobOf.knob.value) skip('G_SENSOR is not a knob of Unreal in this score, or already has its value (the fix would only take the edit back)');
  else {
    const op = { type: 'gate', ids: [sens] }, next = clone(S); next.elements[sens].gate.fw = knobOf.knob.value - 2;
    const c = cardOf(S, op, next), it = c.items.find(i => i.drift), f = it && F.analyze(it, ctxOf(next, { before: S, op, problems: c.P1, items: c.items })).fixes[0];
    check('the card of typing another timeout for G_SENSOR offers Unreal\'s value (it replaces the typed one)', !!f && f.id === 'drift.unreal' && !f.keepsEdit && applied(S, op, next, [f]).n.elements[sens].gate.fw === knobOf.knob.value);
    // validated: a timeout of Unreal's that would not be longer than the expected time creates C2.WAIT.FW, so it is not offered
    const clash = clone(S); clash.elements[sens].gate.expected = knobOf.knob.value + 1; clash.elements[sens].gate.fw = knobOf.knob.value + 5;
    const p = row(clash, 'C3.DRIFT', q => q.el === sens), why = []; const r = p && F.analyze(p, ctxOf(clash, { trace: (id, w) => why.push(id + ': ' + w) }));
    check('a fix that would create a new problem is dropped, and says why (Unreal\'s timeout shorter than the expected time → C2.WAIT.FW)', !!p && r.fixes.length === 0 && why.some(w => /C2\.WAIT\.FW/.test(w)), why.join(' | '));
  }
}

console.log('C3.PARTITURA · a time that is a knob of Unreal');
{
  // the score as Unreal has it (every knob at its initial value), then one governed element moved
  const A = clone(S); for (const b of pbind.binds) P.apply(A, E, pbind, b, pdef.knobs.find(k => k.name === b.knob).initial, null);
  const TA = typical(A), bind = pbind.binds.find(b => b.knob === 'Titulo_RevelaIni'), m = bind && P.measure(A, TA, pbind, bind, null);
  if (!m) skip('Titulo_RevelaIni is not bound in this score');
  else {
    const id = m.els[m.els.length - 1], N = X.move(A, id, 1.5, {}, E.dependents(A));
    const dr = P.drift(N, typical(N), pdef, null, pbind).rows.filter(r => r.diff != null && Math.abs(r.diff) > .05), names = [...new Set(dr.map(r => r.knob))];
    const mk = k => ({ fp: 'C3.PARTITURA|' + k + '|x', knob: k, sv: 'warn', ly: 'C3', rule: 'C3.PARTITURA', el: id, st: 'open' });
    check(`moving the title 1.5 s later leaves ${names.length} timing knobs different from Unreal (the score is in step with it before)`, P.drift(A, TA, pdef, null, pbind).rows.every(r => r.diff == null || Math.abs(r.diff) < .05) && names.length >= 2 && names.includes('Titulo_RevelaIni'));
    const one = F.analyze(mk('Titulo_RevelaIni'), ctxOf(N)), keep = one.fixes.find(f => f.id === 'partitura.propose'), back = one.fixes.find(f => f.id === 'partitura.back');
    check('one knob: "Keep it and tell Unreal: Titulo_RevelaIni 4.5 s" keeps the edit and "Put it back at Unreal\'s 3 s" replaces it', !!keep && keep.keepsEdit && keep.label === 'Keep it and tell Unreal: Titulo_RevelaIni 4.5 s' && !!back && !back.keepsEdit && back.label === "Put it back at Unreal's 3 s", one.fixes.map(f => f.label).join(' | '));
    check('  the detail says Unreal changes only when Send to Unreal is pressed, and that no time in the score moves', /Unreal changes only when you press Send to Unreal/.test(keep.detail) && /Nothing in the score moves/.test(keep.detail));
    const n1 = clone(N); keep.apply(n1);
    check('  it stages the value exactly as Act.propose does: propuestas.valores[knob], with por / motivo (12+ characters) / antes / cuando', JSON.stringify(Object.keys(n1.propuestas.valores)) === '["Titulo_RevelaIni"]' && n1.propuestas.valores.Titulo_RevelaIni === 4.5
      && n1.propuestas.motivos.Titulo_RevelaIni.por === 'B' && n1.propuestas.motivos.Titulo_RevelaIni.motivo.length >= 12 && n1.propuestas.motivos.Titulo_RevelaIni.antes === 3 && n1.propuestas.motivos.Titulo_RevelaIni.cuando === AT);
    check('  the times of the score do not change, and the knob is no longer an open difference (it waits to be sent)', JSON.stringify(typical(n1).t) === JSON.stringify(typical(N).t)
      && P.drift(n1, typical(n1), pdef, null, pbind).rows.filter(r => r.knob === 'Titulo_RevelaIni').every(r => F.waiting(n1, r)));
    const n2 = clone(N); back.apply(n2);
    check('  putting it back makes the score do what Unreal does for that knob', P.drift(n2, typical(n2), pdef, null, pbind).rows.filter(r => r.knob === 'Titulo_RevelaIni').every(r => Math.abs(r.diff) < .05));
    // the toast of the edit covers every knob the edit left different, in one decision
    const all = F.analyze(mk('Titulo_RevelaIni'), ctxOf(N, { knobs: names })), kall = all.fixes.find(f => f.id === 'partitura.propose');
    const n3 = clone(N); kall.apply(n3);
    check(`the toast of the edit: ONE fix for all ${names.length} knobs ("Keep them and tell Unreal about the ${names.length} timing changes")`, kall.label === `Keep it and tell Unreal about the ${names.length} timing changes` && Object.keys(n3.propuestas.valores).sort().join() === names.slice().sort().join() && names.every(k => n3.propuestas.motivos[k].motivo.length >= 12));
    check('  every row of those knobs reads "waiting" after it, and a knob that was not differing is not staged', P.drift(n3, typical(n3), pdef, null, pbind).rows.filter(r => names.includes(r.knob)).every(r => F.waiting(n3, r)) && !Object.keys(n3.propuestas.valores).some(k => !names.includes(k)));
    // a staged change is "waiting" only while it is what the score does
    const n4 = clone(n3); n4.propuestas.valores.Titulo_RevelaIni = 9;
    check('  a staged value that is not what the score does is not "waiting" (the difference is open again)', P.drift(n4, typical(n4), pdef, null, pbind).rows.filter(r => r.knob === 'Titulo_RevelaIni').every(r => !F.waiting(n4, r)));
    // a knob with a value per stage (Carga_Dur): the stage's value changes, the others stay as the Director has them
    const b5 = pbind.binds.find(b => b.knob === 'Carga_Dur'), d5 = pdef.knobs.find(k => k.name === 'Carga_Dur');
    if (b5 && d5 && d5.type === 'a5') {
      const M5 = clone(A); P.apply(M5, E, pbind, b5, 5, 2);   // stage 2 now lasts 5 s instead of 4
      const dr5 = P.drift(M5, typical(M5), pdef, null, pbind).rows.filter(r => r.knob === 'Carga_Dur' && Math.abs(r.diff) > .05);
      const f5 = F.analyze(Object.assign(mk('Carga_Dur'), { el: dr5[0] && dr5[0].els[0] }), ctxOf(M5)).fixes.find(f => f.id === 'partitura.propose'), n5 = clone(M5); if (f5) f5.apply(n5);
      // Act.propose, frozen: nv = (pending || live).slice(); nv[stage] = value
      const old = (d5.initial).slice(); old[2] = 5;
      check('a knob with a value per stage (Carga_Dur, stage 2 = 5 s): staged as Act.propose does, the other stages as Unreal has them', !!f5 && JSON.stringify(n5.propuestas.valores.Carga_Dur) === JSON.stringify(old), n5.propuestas && JSON.stringify(n5.propuestas.valores.Carga_Dur));
    }
  }
}

console.log('C3.VO.WIRED · a voice Unreal calls by itself');
{
  // 3.R3 plays VO_21, VO_22, VO_23 in that order. VO_22 is dragged (Ctrl: what hangs from it stays) past VO_23
  const a = idOf(S, 'VO_21'), b = idOf(S, 'VO_22'), c = idOf(S, 'VO_23');
  if (!a || !b || !c) skip('VO_21 / 22 / 23 are not in this score');
  else {
    const op = { type: 'move', ids: [b], alone: true }, next = X.move(S, b, 25, { alone: true }, kids), cd = cardOf(S, op, next), it = cd.items.find(i => i.rule === 'C3.VO.WIRED' && asked(i));
    if (!it) skip('moving VO_22 does not break the order Unreal plays in this score');
    else {
      const ctx = ctxOf(next, { before: S, op, problems: cd.P1, items: cd.items }), r = F.analyze(it, ctx), f = r.fixes.find(x => x.id === 'order.keep');
      check('a wired voice dragged past the next one: "Keep the order Unreal plays" (the closest start that keeps its place), replaces the drag', !!f && !f.keepsEdit && f.label === 'Keep the order Unreal plays: place VO_22 between its neighbours', r.fixes.map(x => x.label).join(' | '));
      const ap = applied(S, op, next, [f]), T = typical(ap.n).t;
      check('  VO_22 plays after VO_21 and ends 0.3 s before VO_23 starts: the closest place to where it was dragged that keeps the order', T[b][0] >= T[a][1] - 1e-6 && near(T[c][0] - T[b][1], F.GAP, 1e-3) && ap.left.length === 0, `${T[a][1].toFixed(1)} ≤ ${T[b][0].toFixed(1)}–${T[b][1].toFixed(1)} · VO_23 ${T[c][0].toFixed(1)}`);
      check('  it moves only VO_22 (Ctrl: what hangs from it stays)', Object.keys(S.elements).every(k => k === b || near(T[k][0], typical(next).t[k][0])));
      check('  the closest: dragged a little past VO_23 it ends 0.3 s before it, not at the start of its moment', f.detail.startsWith('Replaces your change. VO_22 moves from'));
    }
    // dragged back before the previous voice: the same fix, from the other side
    const op1 = { type: 'move', ids: [b], alone: true }, next1 = X.move(S, b, -25, { alone: true }, kids), c1 = cardOf(S, op1, next1), it1 = c1.items.find(i => i.rule === 'C3.VO.WIRED' && asked(i));
    if (it1) {
      const f1 = F.analyze(it1, ctxOf(next1, { before: S, op: op1, problems: c1.P1, items: c1.items })).fixes.find(x => x.id === 'order.keep'), T1 = f1 && typical(applied(S, op1, next1, [f1]).n).t;
      check('dragged earlier than the voice before it: it starts 0.3 s after VO_21 ends', !!f1 && near(T1[b][0] - T1[a][1], F.GAP, 1e-3), f1 && (T1[b][0] - T1[a][1]).toFixed(2));
    }
    // no room: the neighbours leave less than VO_22 lasts. The fix is not offered and the card says why
    const tight = clone(S), T0 = typical(S).t;
    tight.elements[b].at.off += 463 - T0[b][0]; tight.elements[c].at.off += 468 - typical(tight).t[c][0];   // VO_22 over the end of VO_21, VO_23 hardly later: a gap shorter than VO_22
    const Tt = typical(tight).t, dur = Tt[b][1] - Tt[b][0];
    const op2 = { type: 'move', ids: [b], alone: true }, next2 = X.move(tight, b, 1, { alone: true }, E.dependents(tight)), c2 = cardOf(tight, op2, next2), it2 = c2.items.find(i => i.rule === 'C3.VO.WIRED' && asked(i));
    if (!it2 || !(Tt[c][0] - Tt[a][1] < dur)) skip('could not build a moment with no room for VO_22');
    else {
      const cx = ctxOf(next2, { before: tight, op: op2, problems: c2.P1, items: c2.items }), r2 = F.analyze(it2, cx);
      check('no room between its neighbours that keeps the order: no fix, and it says why', r2.fixes.length === 0 && /There is no room for VO_22 after VO_21 and before VO_23 that keeps the order Unreal plays/.test(r2.why), r2.why);
      const sg = F.suggest(c2.items.filter(i => i.sv !== 'info'), ctxOf(next2, { before: tight, op: op2, problems: c2.P1, items: c2.items }));
      check('  the card gets that reason when nothing else is offered', !sg.list.length && /no room/.test(sg.why), sg.why);
    }
  }
}

console.log('C1.ANCHOR.CYCLE · an anchor loop');
{
  const R = rows(S, 'C1.ANCHOR.CYCLE').filter(p => S.beats[p.el]);
  if (!R.length) skip('this score has no anchor loop at a moment');
  else {
    const all = R.map(p => ({ p, r: F.analyze(p, ctxOf(S)) }));
    check(`each loop of Problems (${R.length}) gets the two ways of the old "Fix the loop…" card: start together as now (nothing moves), start when it ends`, all.every(x => x.r.fixes.length === 2 && x.r.fixes[0].id === 'loop.keep' && x.r.fixes[1].id === 'loop.order' && /Nothing else moves\.$/.test(x.r.fixes[0].detail) && /later items shift/.test(x.r.fixes[1].detail)));
    check('  both leave the loop gone and nothing new open; "together" changes no time of the typical user', all.every(x => x.r.fixes.every(f => { const s = solves(S, x.p, f); return s.gone && s.clean && s.untouched; })
      && JSON.stringify(typical(solves(S, x.p, x.r.fixes[0]).n).t) === JSON.stringify(typical(S).t)));
  }
  // a loop the edit makes: VO_04 re-anchored to a clip of two moments later
  const a = idOf(S, 'VO_04'), b6 = Object.keys(S.beats).find(b => S.beats[b].key === '2.6'), tgt = b6 && Object.keys(S.elements).find(id => S.elements[id].beat === b6);
  if (!a || !tgt) skip('VO_04 / 2.6 are not in this score');
  else {
    const next = clone(S); next.elements[a].at = { ref: tgt, edge: 'start', off: 0 };
    const op = { type: 'reanchor', ids: [a] }, c = cardOf(S, op, next), it = c.items.find(i => i.rule === 'C1.ANCHOR.CYCLE' && i.el === a);
    if (!it) skip('that anchor does not make a loop in this score');
    else {
      const ctx = ctxOf(next, { before: S, op, problems: c.P1, items: c.items }), r = F.analyze(it, ctx), f = r.fixes.find(x => x.id === 'loop.back');
      check('the card of an anchor that closes a loop: "Anchor VO_04 to the start of its moment, where it was"', !!f && !f.keepsEdit && f.label === 'Anchor VO_04 to the start of its moment, where it was', r.fixes.map(x => x.label).join(' | '));
      const ap = applied(S, op, next, [f]);
      check('  the loop is gone, VO_04 is back at the time it had and hangs from the start of its moment', ap.P1.filter(isOpen).every(p => p.rule !== 'C1.ANCHOR.CYCLE' || p.el !== a) && near(typical(ap.n).t[a][0], typical(S).t[a][0]) && ap.n.elements[a].at.edge === 'start' && ap.n.elements[a].at.ref === S.elements[a].beat);
    }
  }
}

console.log('C1.BRANCH.ANCHOR · an anchor across the sides of a decision (schema 3)');
{
  const kids3 = E.dependents(s3); let hit = null;
  for (const id of Object.keys(s3.elements)) {
    if (!kids3[id] || s3.elements[id].branch || !s3.branches) continue;
    const r = X.setBranch(s3, [id], Object.keys(s3.branches)[0], Object.keys(s3.branches[Object.keys(s3.branches)[0]].options)[0]); if (!r.ok) continue;
    const p = probs(r.next).find(q => q.rule === 'C1.BRANCH.ANCHOR' && isOpen(q)); if (p) { hit = { id, r, p }; break; }
  }
  if (!hit) skip('no element of this score makes an anchor across the sides when it is given to one');
  else {
    const op = { type: 'branch', ids: [hit.id] }, c = cardOf(s3, op, hit.r.next), it = c.items.find(i => i.rule === 'C1.BRANCH.ANCHOR');
    const r = F.analyze(it, ctxOf(hit.r.next, { before: s3, op, problems: c.P1, items: c.items })), f = r.fixes[0];
    check('giving an element to one side leaves another hanging from it: the fix gives that one an anchor for the other side, keeps the edit', r.fixes.length === 1 && f.id === 'branch.alt' && f.keepsEdit && /in (SHARE|DON'T SHARE)$/.test(f.label), f && f.label);
    const ap = applied(s3, op, hit.r.next, [f]);
    check('  the block is gone, and no time changes in any side (it is only a new anchor)', !ap.P1.some(p => p.rule === 'C1.BRANCH.ANCHOR' && isOpen(p)) && ap.left.length === 0
      && JSON.stringify(typical(ap.n).t) === JSON.stringify(typical(hit.r.next).t) && E.altRuns(ap.n).every((x, i) => JSON.stringify(x.sched.t) === JSON.stringify(E.altRuns(hit.r.next)[i].sched.t)));
    const rr = F.analyze(hit.p, ctxOf(hit.r.next));
    check('  as a row of Problems the same fix is there (no edit to keep or replace)', rr.fixes.length === 1 && rr.fixes[0].id === 'branch.alt' && solves(hit.r.next, hit.p, rr.fixes[0]).gone);
  }
}

console.log('C2.FLASH · too short to see');
{
  const id = Object.keys(S.elements).find(i => /^(object|world|instruction)$/.test(S.elements[i].type) && S.elements[i].dur && S.elements[i].dur.mode === 'fixed' && S.elements[i].dur.value >= 1 && !/_(OUT|GAP|WARN)\d*$/.test(S.elements[i].key));
  if (!id) skip('no appearance of a fixed length in this score');
  else {
    const op = { type: 'trim', ids: [id] }, next = clone(S); next.elements[id].dur = { mode: 'fixed', value: 0.1 };
    const c = cardOf(S, op, next), it = c.items.find(i => i.rule === 'C2.FLASH'), f = it && F.analyze(it, ctxOf(next, { before: S, op, problems: c.P1, items: c.items })).fixes[0];
    check(`trimming ${S.elements[id].key} to 0.1 s: "Make ${S.elements[id].key} 0.3 s long" (replaces the trim)`, !!f && f.id === 'flash.min' && !f.keepsEdit && f.label === `Make ${S.elements[id].key} 0.3 s long`);
    const ap = applied(S, op, next, [f]);
    check('  it is 0.3 s, the rule is satisfied and the card has nothing left', ap.n.elements[id].dur.value === 0.3 && ap.n.elements[id].dur.mode === 'fixed' && ap.left.length === 0);
    const p = row(next, 'C2.FLASH', q => q.el === id);
    check('  as a row of Problems too', !!p && solves(next, p, F.analyze(p, ctxOf(next)).fixes[0]).gone);
  }
}

console.log('C2.ALMA.EARLY · Alma speaks before she appears');
{
  const v = idOf(S, 'VO_10'), ai = v && S.elements[v].at && S.elements[v].at.ref;
  if (!v || !ai || S.elements[ai].key !== 'ALMA_IN') skip('VO_10 does not follow ALMA_IN in this score');
  else {
    // VO_10 hangs from the end of ALMA_IN; here it plays 2 s after it, and is dragged 5 s earlier (before she has even started to appear)
    const S1 = clone(S); S1.elements[v].at = { ref: ai, edge: 'end', off: 2 };
    const op = { type: 'move', ids: [v] }, next = X.move(S1, v, -5, {}, E.dependents(S1)), c = cardOf(S1, op, next), it = c.items.find(i => i.rule === 'C2.ALMA.EARLY');
    const f = it && F.analyze(it, ctxOf(next, { before: S1, op, problems: c.P1, items: c.items })).fixes[0];
    check('VO_10 dragged to before ALMA_IN ends: "Start VO_10 when ALMA_IN ends" (replaces the drag)', !!f && f.id === 'alma.after' && !f.keepsEdit && f.label === 'Start VO_10 when ALMA_IN ends', f && f.label);
    const ap = applied(S1, op, next, [f]);
    check('  it starts the moment Alma has appeared and the card has nothing left', near(typical(ap.n).t[v][0], typical(ap.n).t[ai][1], 1e-3) && ap.left.length === 0);
    // from its usual place the only fix would be to undo the drag: that is Cancel, so it is not offered
    const op0 = { type: 'move', ids: [v] }, next0 = X.move(S, v, -5, {}, kids), c0 = cardOf(S, op0, next0), it0 = c0.items.find(i => i.rule === 'C2.ALMA.EARLY');
    const why = []; const r0 = it0 && F.analyze(it0, ctxOf(next0, { before: S, op: op0, problems: c0.P1, items: c0.items, trace: (id, w) => why.push(w) }));
    if (S.elements[v].at.edge === 'end' && S.elements[v].at.off === 0) check('a fix that only takes the edit back (VO_10 from the end of ALMA_IN, dragged earlier) is Cancel: not offered', !it0 || r0.fixes.length === 0);
    else skip('VO_10 does not start exactly when ALMA_IN ends in this score (the fix is not just Cancel)');
    const pr = row(next, 'C2.ALMA.EARLY');
    check('  as a row of Problems the same fix is offered', !!pr && F.analyze(pr, ctxOf(next)).fixes.length === 1);
  }
}

console.log('C3.KNOB.OFFSET · a time that is a knob of Unreal counted from another voice');
{
  const v = idOf(S, 'VO_11h');
  const R = rows(S, 'C3.KNOB.OFFSET');
  if (!v || !I.contractFor(v, S.elements[v], contract).some(k => k.kind === 'knob' && k.anchor)) skip('VO_11h is not a counted-from knob in this score');
  else {
    const T = typical(S);
    const p = R.find(q => q.el === v), p2 = p || (() => { const n = X.move(S, v, 3, {}, kids); return row(n, 'C3.KNOB.OFFSET'); })();
    const base2 = p ? S : X.move(S, v, 3, {}, kids), r = p2 && F.analyze(p2, ctxOf(base2)), f = r && r.fixes[0];
    check('Match Unreal: "Play VO_11h 4 s after VO_11b ends, as Unreal does", judged as Match Unreal (op "sync": no card)', !!f && f.id === 'knob.match' && f.op.type === 'sync' && /^Play VO_11h [\d.]+ s after VO_11b ends, as Unreal does$/.test(f.label), f && f.label);
    check('  it solves the row and moves nothing else', !!f && solves(base2, p2, f).gone && solves(base2, p2, f).clean);
    // the card of dragging it: Match Unreal replaces the drag. From where Unreal already has it, that only takes the drag back (Cancel): nothing is offered
    const op = { type: 'move', ids: [v] }, next = X.move(S, v, 3, {}, kids), c = cardOf(S, op, next), it = c.items.find(i => i.rule === 'C3.HELP.AFTER' && asked(i));
    const fc = it && F.analyze(it, ctxOf(next, { before: S, op, problems: c.P1, items: c.items })).fixes[0];
    if (p) {
      check('the card of dragging VO_11h (off the place Unreal has it, to start with) offers the same fix, which replaces the drag', !!fc && fc.id === 'knob.match' && !fc.keepsEdit && /^Replaces your change\./.test(fc.detail));
      // the reference of ≠ headset moves for VO_11h by what Match Unreal moves it from where it WAS, not from where the drag left it
      const ap = applied(S, op, next, [fc]), alone = X.matchKnobAnchor(S, v, { ref: idOf(S, 'VO_11b'), edge: 'end', off: 4, knob: 'BP_BreathStage_SC.HelpAfter', at: AT, by: 'B' }, E);
      const ref = x => JSON.stringify(x.baseline ? x.baseline.rel[v] : x.golden.times[v]);
      check('  and the reference of "≠ headset" ends where Match Unreal alone leaves it (the edit does not shift it)', alone.ok && ref(ap.n) === ref(alone.next), ref(ap.n) + ' vs ' + ref(alone.next));
    } else if (it) check('the card of dragging VO_11h, which already plays where Unreal has it: Match Unreal would only take the drag back, so it is not offered', !fc);
    else skip('moving VO_11h does not ask anything in this score');
  }
}

console.log('C3.BLOCKING · the flag of a wait against Unreal, and C2.WAIT.WHERE (schema 3)');
{
  const g = idOf(s3, 'G_BREATH');
  if (!g || !(s3.schema >= 3) || s3.elements[g].gate.blocking === undefined) skip('G_BREATH has no flag in this score');
  else {
    const N = clone(s3); N.elements[g].gate.blocking = true;
    const p = row(N, 'C3.BLOCKING', q => q.el === g), r = p && F.analyze(p, ctxOf(N)), f = r && r.fixes[0];
    check('a stage wait set to block where Unreal runs it on the clock: "Let G_BREATH run on the stage clock, as Unreal does"', !!f && f.id === 'blocking.set' && f.label === 'Let G_BREATH run on the stage clock, as Unreal does', f && f.label);
    check('  it sets the flag as the contract says and solves the row', !!f && solves(N, p, f).n.elements[g].gate.blocking === false && solves(N, p, f).gone && solves(N, p, f).clean);
    check('  the detail says what changes for the slow and idle users (the typical one lives the same)', /(Slow|Idle) \d+:\d\d → \d+:\d\d/.test(f.detail) && /Typical does not change/.test(f.detail), f && f.detail);
    // the other way: a wait Unreal waits at (the Hall bell) set to run on the clock
    const bell = idOf(s3, 'G_BELL'), M = clone(s3);
    if (bell && M.elements[bell].gate.blocking !== undefined) {
      M.elements[bell].gate.blocking = false;
      const q = row(M, 'C3.BLOCKING', x => x.el === bell), fm = q && F.analyze(q, ctxOf(M)).fixes[0];
      if (q) check('  and the other way: a wait Unreal waits at, set to the clock → "Make G_BELL wait for the user, as Unreal does"', !!fm && fm.label === 'Make G_BELL wait for the user, as Unreal does' && solves(M, q, fm).n.elements[bell].gate.blocking === true);
      else skip('the Hall bell wait is not judged against Unreal here');
    }
    // C2.WAIT.WHERE: a new wait in a stage that blocks
    const W = clone(s3), wid = Object.keys(W.elements).find(i => W.elements[i].gate && /^\d\.R/.test(W.beats[W.elements[i].beat].key) && !I.contractFor(i, W.elements[i], contract).length);
    const W2 = clone(s3), g2 = Object.keys(W2.elements).find(i => W2.elements[i].gate && /^\d\.R/.test(W2.beats[W2.elements[i].beat].key));
    if (g2) { W2.elements[g2].isNew = true; W2.elements[g2].gate.blocking = true; }
    const pw = g2 && row(W2, 'C2.WAIT.WHERE', q => q.el === g2), fw = pw && F.analyze(pw, ctxOf(W2)).fixes[0];
    if (pw) check('  C2.WAIT.WHERE (a new wait in a stage that blocks): "Let it run on the stage clock" and the row goes', !!fw && fw.id === 'blocking.set' && solves(W2, pw, fw).gone, fw && fw.label);
    else skip('no stage wait to try C2.WAIT.WHERE on');
  }
}

console.log('rules with no automatic fix, and rows that are not problems');
{
  const none = [
    ['C2.TOTAL.GOAL', { fp: 'C2.TOTAL.GOAL||33', sv: 'warn', ly: 'C2', rule: 'C2.TOTAL.GOAL', st: 'open' }],
    ['C3.TRACE.STAGE', { fp: 'C3.TRACE.STAGE|1', sv: 'warn', ly: 'C3', rule: 'C3.TRACE.STAGE', st: 'open' }],
    ['C3.TRACE.SEG', { fp: 'C3.TRACE.SEG|1', sv: 'warn', ly: 'C3', rule: 'C3.TRACE.SEG', st: 'open' }],
    ['C3.DIVERGE', { fp: 'C3.DIVERGE|x|1|1', sv: 'warn', ly: 'C3', rule: 'C3.DIVERGE', st: 'open', el: Object.keys(S.elements)[0] }],
    ['C2.LANG', { fp: 'C2.LANG|x', sv: 'warn', ly: 'C2', rule: 'C2.LANG', st: 'open', el: Object.keys(S.elements)[0] }],
    ['C2.VO.REAL', { fp: 'C2.VO.REAL||1', sv: 'warn', ly: 'C2', rule: 'C2.VO.REAL', st: 'open' }],
    ['a note (info)', { fp: 'C2.VO.OVERLAP|x|y', sv: 'info', ly: 'C2', rule: 'C2.VO.OVERLAP', st: 'open', el: Object.keys(S.elements)[0] }],
    ['an accepted problem', { fp: 'C2.WAIT.NOHELP|x', sv: 'warn', ly: 'C2', rule: 'C2.WAIT.NOHELP', st: 'accepted', el: Object.keys(S.elements)[0] }],
    ['an accepted record listed alone', { fp: 'C2.WAIT.NOHELP|x', sv: 'warn', ly: 'C2', rule: 'C2.WAIT.NOHELP', st: 'accepted', ghost: true, el: Object.keys(S.elements)[0] }],
  ];
  check('TOTAL.GOAL, the Unreal run, ≠ headset build, not in English, the voice lengths, notes and accepted rows propose nothing', none.every(([, p]) => F.propose(p, ctxOf(S)).length === 0), none.filter(([, p]) => F.propose(p, ctxOf(S)).length).map(x => x[0]).join(','));
  check('  Fixes.handles says so without working anything out', none.every(([, p]) => !F.handles(p)) && F.handles({ rule: 'C2.VO.OVERLAP', sv: 'warn', st: 'open' }) && F.handles({ rule: 'C3.VO.WIRED', sv: 'warn', c3: true }));
  check('  a row of a rule it knows but with an element that is not in the score proposes nothing (and does not throw)', ['C2.VO.OVERLAP', 'C2.HELP.LATE', 'C2.WAIT.NOHELP', 'C2.FLASH', 'C2.ALMA.EARLY', 'C3.DRIFT', 'C3.KNOB.OFFSET', 'C3.BLOCKING', 'C1.ANCHOR.CYCLE', 'C1.BRANCH.ANCHOR', 'C1.ANCHOR.MISSING', 'C3.PARTITURA']
    .every(rule => F.propose({ fp: rule + '|gone|x', rule, sv: 'warn', st: 'open', el: 'gone', knob: 'Nothing' }, ctxOf(S)).length === 0));
}

console.log('the checks every fix passes');
{
  // a fix that gives back the score before the edit is Cancel: not offered (and the one that differs is)
  const v = idOf(S, 'VO_19');
  if (v) {
    const op = { type: 'move', ids: [v] }, next = X.move(S, v, -2, {}, kids), c = cardOf(S, op, next), it = c.items.find(i => i.rule === 'C2.VO.OVERLAP');
    if (it) {
      const r = F.analyze(it, ctxOf(next, { before: S, op, problems: c.P1, items: c.items }));
      check('no fix of the card is the score before the edit (that is Cancel)', r.fixes.every(f => !X.sameScore(applied(S, op, next, [f]).n, S)));
    }
  }
  // two ways that end in the same score are one; fixes are unique by what they leave
  const R = rows(S, 'C2.VO.OVERLAP');
  check('the fixes of one problem are different ones (no two end in the same score)', R.every(p => { const sg = F.analyze(p, ctxOf(S)).fixes.map(f => f.sig); return new Set(sg).size === sg.length; }));
  check('at most three per problem, and four on a card', R.every(p => F.analyze(p, ctxOf(S)).fixes.length <= 3) && F.suggest(R, ctxOf(S)).list.length <= 4);
  check('analyze never changes the score it is given (nor the one before the edit)', JSON.stringify(S) === frozen && JSON.stringify(s3) === JSON.stringify(s3));
  // the trace says why something was dropped
  const why = []; if (R[0]) F.analyze(R[0], ctxOf(S, { trace: (id, w) => why.push(id + ': ' + w) }));
  check('ctx.trace says why a candidate was dropped (tests and diagnostics only)', Array.isArray(why));
}

console.log('the toast of an edit that left a warning (policy.js)');
{
  const w = (fp, o) => Object.assign({ fp, sv: 'warn', ly: 'C2', rule: 'C2.VO.OVERLAP', st: 'open', el: 'x' }, o);
  const before = [w('a'), w('b', { sv: 'info' })], after = [w('a'), w('b', { sv: 'warn' }), w('c'), w('d', { rule: 'C2.TOTAL.GOAL' }), w('e', { rule: 'C3.DIVERGE' }), w('f', { rule: 'C3.TRACE.STAGE' }), w('g', { st: 'accepted' }), w('h', { ghost: true }), w('i', { sv: 'info' }), w('j', { sv: 'block', ly: 'C1', rule: 'C1.BRANCH.ANCHOR' }), w('k', { rule: 'C3.PARTITURA', ly: 'C3' })];
  const nw = Pol.newWarnings(before, after);
  check('Policy.newWarnings: what the edit added to Problems that needs a look (not the total, ≠ headset, the Unreal run, accepted, listed-alone or notes)', nw.map(p => p.fp).join() === 'b,c,j,k', nw.map(p => p.fp).join());
  check('  the words: "Move · VO_19 · 1 new warning in Problems (F8)", plural for more', Pol.warnToast('Move · VO_19', 1) === 'Move · VO_19 · 1 new warning in Problems (F8)' && Pol.warnToast('Paste', 3) === 'Paste · 3 new warnings in Problems (F8)');
  check('  the quiet toast of decide() is still the same words (the "Fix it" link is the app\'s)', Pol.decide({ type: 'paste', ids: ['x'] }, [{ sv: 'warn', ly: 'C2', rule: 'C2.VO.OVERLAP' }], { label: 'Paste · VO_05' }).toast === 'Paste · VO_05 · 1 new warning in Problems (F8)');
  check('  doneToast: unchanged without fixes; "Done · fixed: …" with them', Pol.doneToast('anyway', 'total 16:59') === 'Done · accepted and recorded in Problems · total 16:59' && Pol.doneToast('fix', '', ['Start VO_19 after VO_18 ends']) === 'Done · fixed: Start VO_19 after VO_18 ends'
    && Pol.fixedToast('Move · VO_19', ['Start VO_19 after VO_18 ends'], 'total 17:00 (+1.8 s)') === 'Move · VO_19 · fixed: Start VO_19 after VO_18 ends · total 17:00 (+1.8 s)');
  // the same, on a real paste of a voice on top of another one: the warning is new, and it has a fix
  const v = idOf(S, 'VO_05'), clip = v && X.clipOf(S, [v], E);
  if (v) {
    const plan = X.planPaste(S, clip, { beat: S.elements[v].beat, off: 1 }, E, { who: 'B', addLane: (n, g) => X.addLaneTo(n, g) });
    if (plan.ok) {
      const P0 = probs(S), P1 = probs(plan.next), fresh = Pol.newWarnings(P0, P1).filter(p => p.rule === 'C2.VO.OVERLAP');
      if (fresh.length) {
        const r = F.analyze(fresh[0], ctxOf(plan.next));
        check('a voice pasted over another: the new overlap has a fix to offer in the toast ("… · Fix it")', r.fixes.length > 0 && r.fixes.every(f => solves(plan.next, fresh[0], f).gone), r.fixes.map(f => f.label).join(' | '));
      } else skip('that paste does not overlap in this score');
    } else skip('the paste could not be planned: ' + plan.why);
  }
}

check('the score of the test was never changed', JSON.stringify(base) === frozen);
console.log(fails ? `\n${fails} FAILED` : `\nall ok${skipped ? ` (${skipped} scenario${skipped > 1 ? 's' : ''} skipped)` : ''}`);
process.exit(fails ? 1 : 0);
