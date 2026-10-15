// simple_test.mjs — the Simple view of the editor (the plain-words default; Advanced is "Show technical details" in Window):
// the status line in plain words, what "to review" counts (the comparison with the last Unreal run is ONE item), the Problems
// list folded the same way, the filters of each mode, the groups that start collapsed, the plain words for where an element
// stands with Unreal, and that every rule code the editor can raise has a plain title. Presentation only: pure, nothing is written.
// Logic: web/editor-obra/app/js/simple.js. Exit 1 if any case fails.
//   node tools/score/simple_test.mjs
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const APP = path.join(ROOT, 'web/editor-obra/app/js');
const S = require(path.join(APP, 'simple.js'));
let fails = 0;
const check = (name, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + name + (info ? '  · ' + info : '')); if (!ok) fails++; };
const P = (rule, sv, st, extra) => Object.assign({ rule, sv, st, msg: rule }, extra || {});

console.log('the status line');
{
  const p = S.statusParts({ persona: 'Typical', side: 'SHARE', total: '18:10', review: 12, dirty: false });
  check('reads in plain words: user · side · total (goal) / to review / Saved', p.who === 'Typical user · SHARE · 18:10 (goal 15:00)' && p.review === '12 to review' && p.save === 'Saved', JSON.stringify(p));
  const q = S.statusParts({ persona: 'Idle', side: '', total: '21:00', review: 0, dirty: true });
  check('no side, nothing to review, unsaved', q.who === 'Idle user · 21:00 (goal 15:00)' && q.review === 'Nothing to review' && q.save === 'Unsaved · Ctrl+S', JSON.stringify(q));
  const reach = { counts: { knob: 66, wired: 74, cue: 12, preview: 428, bindable: 3, unsure: 2 }, schema: 3 };
  const tip = S.statusTip({ side: 'SHARE', review: 6, reach, edited: 4, diverged: 2, accepted: 8, rev: 4, run: 'Unreal run · +48.4 s' });
  check('the technical counters live in the tooltip', ['66 reach Unreal (timing)', '74 set by Unreal', '12 can become an Unreal cue', '428 only in the preview', '4 edited', '2 differ from what the headset build does today', '8 accepted', 'revision 4', 'Unreal run · +48.4 s', 'Nothing reaches Unreal until Send to Unreal'].every(s => tip.includes(s)), tip.split('\n').length + ' lines');
  check('and the status line itself carries none of them', !/wired|cue-ready|preview|APK|rev \d|accepted|edited/.test(Object.values(p).join(' ')));
}

console.log('plain words for where an element stands with Unreal');
{
  const R = require(path.join(APP, 'reach.js'));
  check('wired → set by Unreal, cue → can become an Unreal cue, preview → only in the preview', S.REACH_WORD.wired === 'Set by Unreal' && S.REACH_WORD.cue === 'Can become an Unreal cue' && S.REACH_WORD.preview === 'Only in the preview');
  check('one plain word for every reach the engine can answer (the keys are never renamed)', Object.keys(R.REACH_WORD).every(k => S.REACH_WORD[k]), Object.keys(R.REACH_WORD).join(' '));
  const a = { counts: { knob: 1, wired: 2, cue: 3, preview: 4, bindable: 0, unsure: 0 }, schema: 2 };
  check('schema 2 says no cue-ready part, like the technical text', !/cue/.test(S.reachText(a)) && /cue/.test(S.reachText({ ...a, schema: 3 })) && !/wired|cue-ready|preview\b(?! )/.test(S.reachText({ ...a, schema: 3 }).replace(/only in the preview/g, '')));
  check('the same counts, in both texts', [1, 2, 4].every(n => S.reachText(a).includes(n + ' ')) && [1, 2, 4].every(n => R.statusText(a).includes(n + ' ')));
  check('the "why" of a reach says the kind in plain words too, and leaves the rest alone', S.plainWhy('Wired in Unreal: BP_Obra_SC › AlmaSpeak.') === 'Set by Unreal: BP_Obra_SC › AlmaSpeak.'
    && S.plainWhy('Hardwired in Unreal: BP_X.') === 'Fixed inside Unreal: BP_X.' && S.plainWhy('A knob in Unreal: BP_X.') === 'A knob in Unreal: BP_X.' && S.plainWhy('Made in the editor: Unreal does not know it.') === 'Made in the editor: Unreal does not know it.' && S.plainWhy(null) === '');
  check('kinds of the contract have a plain word too', ['literal', 'wired', 'knob', 'partitura', 'not-blocking', 'not-in-unreal'].every(k => S.KIND_WORD[k]));
}

console.log('Problems: what needs a look, and the run folded into one');
{
  const list = [P('C2.WAIT.NOHELP', 'warn', 'open'), P('C2.WAIT.NOHELP', 'warn', 'open'), P('C1.ANCHOR.MISSING', 'block', 'open'), P('C2.TOTAL.GOAL', 'warn', 'open'),
    ...Array.from({ length: 7 }, () => P('C3.TRACE.STAGE', 'warn', 'open', { grp: 'run' })), P('C3.TRACE.STALE', 'info', 'open', { grp: 'run' }),
    P('C3.SCOPE', 'info', 'open'), P('C3.VO.WIRED', 'warn', 'accepted'), P('C2.FLASH', 'warn', 'accepted')];
  const r = S.review(list);
  check('7 stages that differ are ONE item, not 7 warnings', r.rows.length === 4 && r.trace.length === 7 && r.count === 5 && r.stages === 7, JSON.stringify({ rows: r.rows.length, trace: r.trace.length, count: r.count, stages: r.stages }));
  check('blocks are counted apart; notes and accepted ones are not "to review"', r.blocks === 1 && !r.rows.some(p => p.sv === 'info' || p.st === 'accepted'));
  check('no comparison, no group item', S.review(list.filter(p => !S.isTrace(p))).count === 4 && S.review([]).count === 0 && S.review(null).count === 0);
  check('only informative run rows (STALE) do not make an item', S.review([P('C3.TRACE.STALE', 'info', 'open'), P('C3.TRACE.STAGE', 'warn', 'accepted')]).count === 0);
  const items = S.fold(list.filter(p => S.needsLook(p) || p.rule === 'C3.TRACE.STALE'));
  check('the list folds the run at the place of its first row, in order', items.length === 5 && items[4].group && items[4].group.length === 8 && items[0].row && items.filter(i => i.group).length === 1, items.map(i => i.group ? 'group' + i.group.length : i.row.rule).join(' '));
  check('nothing is lost when folding', items.reduce((n, i) => n + (i.group ? i.group.length : 1), 0) === list.filter(p => S.needsLook(p) || p.rule === 'C3.TRACE.STALE').length);
  const g = S.groupLabel(list.filter(S.isTrace));
  check('the group says how many stages differ', g === 'Compared with the last Unreal run · 7 stages differ', g);
  check('one stage: singular; only notes; only accepted', S.groupLabel([P('C3.TRACE.STAGE', 'warn', 'open')]) === 'Compared with the last Unreal run · 1 stage differs'
    && S.groupLabel([P('C3.TRACE.STALE', 'info', 'open'), P('C3.TRACE.MISSING', 'info', 'open')]) === 'Compared with the last Unreal run · 2 notes'
    && S.groupLabel([P('C3.TRACE.STAGE', 'warn', 'accepted')]) === 'Compared with the last Unreal run · 1 accepted');
}

console.log('Problems: the filters of each mode');
{
  check('Simple opens on To review; Advanced keeps Open first, as always', S.filters(false, false)[0][0] === 'attn' && S.filters(true, false)[0][0] === 'open' && S.filterFor(undefined, false, false) === 'attn' && S.filterFor(undefined, true, false) === 'open');
  check('every filter Advanced has, Simple has (no capability lost)', S.filters(true, true).every(([k]) => S.filters(false, true).some(([k2]) => k2 === k)), S.filters(false, true).map(f => f[0]).join(' '));
  check('a filter the mode does not have falls back (attn in Advanced; run with no run)', S.filterFor('attn', true, false) === 'open' && S.filterFor('run', false, false) === 'attn' && S.filterFor('run', false, true) === 'run' && S.filterFor('accepted', false, false) === 'accepted');
  check('the run filter is there only with a run', !S.filters(false, false).some(f => f[0] === 'run') && S.filters(false, true).some(f => f[0] === 'run') && S.filters(true, true).some(f => f[0] === 'run'));
}

console.log('plain titles for every rule');
{
  // every rule code any module of the editor can raise (a string 'C1.…' / 'C2.…' / 'C3.…' in the sources) has a headline
  const codes = new Set();
  for (const f of fs.readdirSync(APP).filter(f => f.endsWith('.js') && f !== 'simple.js')) for (const m of fs.readFileSync(path.join(APP, f), 'utf8').matchAll(/'(C[123]\.[A-Z][A-Z0-9]*(?:\.[A-Z0-9]+)*)'/g)) codes.add(m[1]);
  // C3.<contract id> rules are made from the contract entries (opItems): they show their own message
  const missing = [...codes].filter(c => !S.TITLE[c]);
  check('every rule code in the sources has a plain title', !missing.length, `${codes.size} codes` + (missing.length ? ' · missing ' + missing.join(', ') : ''));
  check('a title never shows a code', Object.values(S.TITLE).every(t => !/\bC[123]\b|\.[A-Z]{3,}/.test(t)));
  check('sentence case, no all-caps words', Object.values(S.TITLE).every(t => !/\b[A-Z]{4,}\b/.test(t) && /^[A-Z]/.test(t)));
  check('a rule with no title gives none (the row shows its message)', S.titleOf(P('C3.VO.WIRED', 'warn', 'open')) === '' && S.titleOf(null) === '' && S.titleOf(P('C2.WAIT.NOHELP', 'warn', 'open')) === 'A wait with no help line');
  check('severity words', S.sevWord(P('x', 'block', 'open')) === 'Blocking' && S.sevWord(P('x', 'warn', 'open')) === 'Warning' && S.sevWord(P('x', 'info', 'open')) === 'Note' && S.sevWord(P('x', 'warn', 'accepted')) === 'Accepted');
}

console.log('timeline: groups that start collapsed');
{
  check('Simple: Haptics and Path start collapsed, the rest open', S.collapsedFor({}, 'hap', false) && S.collapsedFor({}, 'pawn', false) && !S.collapsedFor({}, 'vo', false) && !S.collapsedFor(null, 'fx', false));
  check('Advanced: nothing starts collapsed, as today', !S.collapsedFor({}, 'hap', true) && !S.collapsedFor({}, 'pawn', true));
  check('what the user chose is remembered, in either mode', !S.collapsedFor({ hap: false }, 'hap', false) && S.collapsedFor({ vo: true }, 'vo', false) && S.collapsedFor({ vo: true }, 'vo', true) && S.collapsedFor({ hap: true }, 'hap', true));
  const score = JSON.parse(fs.readFileSync(path.join(ROOT, 'tools/score/fixtures/f0-score.json'), 'utf8'));
  check('the ids exist in the score (Haptics = hap, Path = pawn)', S.COLLAPSED.has('hap') && S.COLLAPSED.has('pawn') && [...S.COLLAPSED].every(g => score.groups.some(x => x.id === g)) && /Haptic/.test(score.groups.find(g => g.id === 'hap').name) && /Path/.test(score.groups.find(g => g.id === 'pawn').name));
}

console.log('Quick start');
{
  const Q = S.QUICK_START, all = Q.map(q => q.join(' ')).join('\n');
  check('about six steps, each with a title and words', Q.length === 6 && Q.every(q => q[0] && q[1].length > 40), Q.map(q => q[0]).join(' · '));
  check('they cover play and scrub, select and move, undo, Problems, save, Send to Unreal', [/\[Space\]/, /Drag it to move/, /Ctrl\+Z/, /Problems/, /Ctrl\+S/, /Send to Unreal/].every(r => r.test(all)));
  check('it says nothing reaches Unreal without Send to Unreal', /Nothing reaches Unreal without it/.test(all));
  check('plain English, no rule codes, no all-caps words but the keys', !/\bC[123]\.|wired|cue-ready/.test(all) && !/\b[A-Z]{4,}\b/.test(all.replace(/\[[^\]]+\]/g, '')));
}

// Simple mode never says "APK": plainWords rewrites every phrase the app uses (Advanced keeps them)
{
  const cases = [['≠ APK', '≠ headset'], ['Affects APK', 'Affects the headset'],
    ['its time here differs from what the APK does today.', 'its time here differs from what the headset build does today.'],
    ['the APK baseline moves too', 'the reference of what the headset does moves too'],
    ['(the clip shows ≠ APK)', '(the clip shows ≠ headset)'], ['nothing to change', 'nothing to change']];
  const bad = cases.filter(([a, b]) => S.plainWords(a) !== b);
  check('plainWords: the "APK" phrases become headset wording', !bad.length, bad.map(([a]) => a + ' → ' + S.plainWords(a)).join(' | '));
  // every "APK" the app can put on screen comes out without it
  const src = ['app.js', 'ui.js', 'integrity.js', 'policy.js', 'edits.js', 'check.js', 'simple.js'].map(f => fs.readFileSync(path.join(APP, f), 'utf8')).join('\n');
  const lits = [...src.matchAll(/(['`"])((?:(?!\1).)*APK(?:(?!\1).)*)\1/g)].map(m => m[2]);
  const left = lits.filter(t => /APK/.test(S.plainWords(t)));
  check('no string literal with "APK" survives plainWords (' + lits.length + ' checked)', !left.length, left.slice(0, 3).join(' | '));
}

console.log('\n' + (fails ? fails + ' FAILED' : 'all ok'));
process.exit(fails ? 1 : 0);
