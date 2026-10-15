/* Veation VR Studio · SIMPLE: the plain-words view (Simple, the default) next to the technical one (Advanced, "Show technical
   details" in Window). Pure (no DOM): it runs in the browser and in Node (tools/score/simple_test.mjs). It is presentation only:
   nothing here changes the score, what is checked or what a verb does; identifiers (element keys, rule codes, Unreal knob names)
   are never renamed, they just move to tooltips and to the Details of the inspector. */
(function (root) {
  'use strict';
  const GOAL = '15:00';

  /* ---- timeline: the groups that start collapsed in Simple (Haptics, Path) until the user opens them; what the user chose wins ---- */
  const COLLAPSED = new Set(['hap', 'pawn']);
  const own = (o, k) => !!o && Object.prototype.hasOwnProperty.call(o, k);
  const collapsedFor = (saved, gid, adv) => own(saved, gid) ? !!saved[gid] : !adv && COLLAPSED.has(gid);

  /* ---- plain words for where an element stands with Unreal (the keys knob / wired / cue / preview never change) ---- */
  const REACH_WORD = { knob: 'Reaches Unreal', wired: 'Set by Unreal', cue: 'Can become an Unreal cue', preview: 'Only in the preview' };
  const KIND_WORD = { literal: 'Fixed inside Unreal', wired: 'Set by Unreal', knob: 'A knob in Unreal', partitura: 'Unreal timing knob', 'not-blocking': 'Different in Unreal', 'not-in-unreal': 'Not in Unreal yet' };
  // the "why" of a reach starts with the kind in the technical words ("Wired in Unreal: BP_… › …"): the same kind in the plain ones
  const plainWhy = w => String(w == null ? '' : w).replace(/^Hardwired in Unreal/, KIND_WORD.literal).replace(/^Wired in Unreal/, KIND_WORD.wired);
  const REACH_HELP = 'Reaches Unreal: a timing knob of Unreal sets its time, so Send to Unreal can change it · Set by Unreal: Unreal decides it · Can become an Unreal cue: tied to an Unreal mark and asset · Only in the preview: just the editor and the 3D know it';
  /* "66 reach Unreal (timing) · 74 set by Unreal · 12 can become an Unreal cue · 428 only in the preview" (the cue part only for a schema 3 score, like Reach.statusText) */
  function reachText(a) {
    const c = a.counts, p = [`${c.knob} reach Unreal (timing)`, `${c.wired} set by Unreal`];
    if (a.schema >= 3) p.push(`${c.cue} can become an Unreal cue`);
    p.push(`${c.preview} only in the preview`);
    return p.join(' · ');
  }
  function reachTitle(a) {
    const c = a.counts, t = [
      `${c.knob}: their time is a knob of Unreal's timing, so Send to Unreal can change it.`,
      `${c.wired}: set by Unreal itself${c.unsure ? `; for ${c.unsure} of them that is a best guess` : ''}.`];
    if (a.schema >= 3) t.push(`${c.cue}: tied to an Unreal mark and asset, so they could become cues (there is no cue player in Unreal yet).`);
    t.push(`${c.preview}: only in the preview (the editor and the 3D)` + (c.bindable ? `; ${c.bindable} of them could become cues once the score is bound to Unreal.` : '.'));
    t.push('Nothing reaches Unreal until Send to Unreal.');
    return t.join('\n');
  }

  /* ---- the status bar: "Typical user · SHARE · 18:10 (goal 15:00) · 6 to review · Saved" ----
     o = { persona: 'Typical', side: 'SHARE' | '', total: '18:10', goal?, review: n, blocks: n, dirty } → three parts; the technical
     counters go to the tooltip (statusTip) in Simple, and are drawn as before in Advanced */
  function statusParts(o) {
    const n = o.review | 0;
    return {
      who: `${o.persona} user${o.side ? ' · ' + o.side : ''} · ${o.total} (goal ${o.goal || GOAL})`,
      review: n ? `${n} to review` : 'Nothing to review',
      save: o.dirty ? 'Unsaved · Ctrl+S' : 'Saved',
    };
  }
  /* the tooltip of that text: what each part means, and the counters the status bar showed before (o: sideWord, reach, edited, diverged, accepted, rev, run) */
  function statusTip(o) {
    const t = [o.side ? 'The simulated user, the side of the decision on screen, and how long the piece runs that way. Change the side in the transport (Branch).' : 'The simulated user and how long the piece runs.'];
    t.push(`${o.review | 0} to review: what the Problems list shows by default (blocking items and warnings that are still open). Click to open it.`);
    if (o.reach) t.push('Where the elements stand with Unreal: ' + reachText(o.reach));
    t.push(`${o.edited | 0} edited since the last save · ${o.diverged | 0} differ from what the headset build does today · ${o.accepted | 0} accepted`);
    if (o.run) t.push(o.run);
    t.push(`Score revision ${o.rev}`);
    t.push('Nothing reaches Unreal until Send to Unreal.');
    return t.join('\n');
  }

  /* ---- Problems ---- */
  // a plain headline per rule; the rule codes (C1 / C2 / C3.*) stay in the tooltip. A rule with none (the C3.<contract> ones) shows its message alone
  const TITLE = {
    'C1.ANCHOR.CYCLE': 'Anchor loop', 'C1.ANCHOR.MISSING': 'Anchor lost', 'C1.BRANCH.ANCHOR': 'Anchor across branches', 'C1.BRANCH.FIELD': 'Malformed branch',
    'C1.SCHEMA': 'The score format can be upgraded',
    'C2.TOTAL.GOAL': 'Longer than the goal', 'C2.WAIT.NOHELP': 'A wait with no help line', 'C2.WAIT.FW': 'Timeout not longer than expected', 'C2.WAIT.WHERE': 'A wait where Unreal does not wait',
    'C2.HELP.LATE': 'Help would never play', 'C2.ALMA.EARLY': 'Alma speaks before she appears', 'C2.VO.OVERLAP': 'Two voices at once', 'C2.VO.REAL': 'Voices last differently in the final mix',
    'C2.FLASH': 'Too short to see', 'C2.LANG': 'Not in English',
    'C3.DRIFT': 'Timeout differs from Unreal', 'C3.BLOCKING': 'Waits differently from Unreal', 'C3.NOTBLOCKING': 'Different in Unreal', 'C3.KNOB.OFFSET': 'Starts at another time than in Unreal',
    'C3.DIVERGE': 'Differs from the headset build', 'C3.PARTITURA': 'Timing differs from Unreal', 'C3.BINDING.STALE': 'The link to Unreal is out of date',
    'C3.CONTRACT.ORPHAN': 'Gone here, still in Unreal', 'C3.CONTRACT.RULE': 'Not what Unreal expects', 'C3.SCOPE': 'What is checked against Unreal', 'C3.UNREADABLE': 'A file could not be read',
    'C3.TRACE.STAGE': 'Stage length differs from the last run', 'C3.TRACE.SEG': 'Step differs from the last run', 'C3.TRACE.MISSING': 'A mark is missing in the score or the run',
    'C3.TRACE.MARK': 'A mark is not placed', 'C3.TRACE.STALE': 'The last run cannot be compared fully',
  };
  const titleOf = p => (p && TITLE[p.rule]) || '';
  const SEV = { block: 'Blocking', warn: 'Warning', info: 'Note' };
  const sevWord = p => p.st === 'accepted' ? 'Accepted' : SEV[p.sv === 'inv' ? 'block' : p.sv] || '';
  const isTrace = p => /^C3\.TRACE\./.test((p && p.rule) || '');
  const needsLook = p => !!p && p.st === 'open' && (p.sv === 'block' || p.sv === 'warn');
  /* what "to review" counts: the open blocks and warnings, with everything the last Unreal run says folded into ONE item (a run that
     differs in 7 stages is one thing to look at, not 7 warnings) → { rows, trace, count, blocks, stages } */
  function review(P) {
    const open = (P || []).filter(needsLook), trace = open.filter(isTrace), rows = open.filter(p => !isTrace(p));
    return { rows, trace, count: rows.length + (trace.length ? 1 : 0), blocks: open.filter(p => p.sv === 'block').length, stages: trace.filter(p => p.rule === 'C3.TRACE.STAGE').length };
  }
  /* a list of problems (already filtered and sorted) as items: { row } or { group: [the run's problems] } at the place of the first of them */
  function fold(list) {
    const out = []; let grp = null;
    for (const p of list || []) {
      if (!isTrace(p)) { out.push({ row: p }); continue; }
      if (!grp) { grp = []; out.push({ group: grp }); }
      grp.push(p);
    }
    return out;
  }
  /* "Compared with the last Unreal run · 7 stages differ" */
  function groupLabel(members) {
    const n = members.filter(p => p.rule === 'C3.TRACE.STAGE' && p.st === 'open').length, m = members.length;
    const tail = n ? `${n} stage${n === 1 ? '' : 's'} differ${n === 1 ? 's' : ''}` : members.every(p => p.st === 'accepted') ? `${m} accepted` : `${m} note${m === 1 ? '' : 's'}`;
    return 'Compared with the last Unreal run · ' + tail;
  }
  // the filters of the list: Simple opens on what needs attention; Advanced is as it always was
  const FILTERS_SIMPLE = [['attn', 'To review'], ['open', 'All open'], ['apk', 'Affects the headset'], ['accepted', 'Accepted'], ['all', 'All']];
  const FILTERS_ADV = [['open', 'Open'], ['apk', 'Affects APK'], ['accepted', 'Accepted'], ['all', 'All']];
  const RUN_FILTER = { simple: ['run', 'Last Unreal run'], adv: ['run', 'Unreal run'] };
  function filters(adv, hasRun) { return (adv ? FILTERS_ADV : FILTERS_SIMPLE).concat(hasRun ? [RUN_FILTER[adv ? 'adv' : 'simple']] : []); }
  /* the filter on screen: the one picked when this mode has it, else the mode's own first one */
  function filterFor(pick, adv, hasRun) { const ok = filters(adv, hasRun).map(f => f[0]); return ok.includes(pick) ? pick : ok[0]; }

  /* ---- Help ▸ Quick start: six steps in plain English; [Key] is drawn as a key cap ---- */
  const QUICK_START = [
    ['Play and move around', 'Press [Space] to play or pause. Click the ruler to jump there, or press [←] and [→] to step the playhead. The 3D preview plays what the timeline says.'],
    ['Select and move a clip', 'Click a clip to see it in the Inspector. Drag it to move it: whatever hangs from it follows. Hold [Ctrl] while you drag to move only that clip, or use [Alt+←] and [Alt+→] for small steps.'],
    ['Undo anything', '[Ctrl+Z] undoes and [Ctrl+Shift+Z] redoes. Every edit is one step, so it is safe to try things.'],
    ['What Problems means', 'The Problems button ([F8]) lists what needs a look: a wait with no help line, two voices at once, a stage that runs longer than in the last Unreal run. The status bar counts them as "to review". Nothing stops your work: use Show or the suggested fix, or go ahead anyway and say why.'],
    ['Save', 'Press [Ctrl+S] to save the score. The status bar says Saved or Unsaved. Until you save, your changes live only in this browser.'],
    ['Send to Unreal', 'Saving changes the score only. Send to Unreal (top bar, when timing changes are waiting) shows every change and asks you to confirm. Nothing reaches Unreal without it, and Unreal applies it only when someone asks.'],
  ];

  /* Simple mode speaks of the headset, never of the "APK" (the Android package): every text on screen passes through this.
     Order matters: the longer phrases first. Advanced keeps the original words. */
  const PLAIN = [
    [/≠\s?APK\b/g, '≠ headset'],
    [/\bthe APK baseline\b/gi, 'the reference of what the headset does'],
    [/\bAPK baseline\b/gi, 'reference of what the headset does'],
    [/\bAffects (the )?APK\b/g, 'Affects the headset'],
    [/\bthe APK\b/g, 'the headset build'], [/\bThe APK\b/g, 'The headset build'],
    [/\ban APK\b/gi, 'a headset build'],
    [/\bAPK\b/g, 'headset build'],
  ];
  const plainWords = s => typeof s !== 'string' || s.indexOf('APK') < 0 ? s : PLAIN.reduce((t, [re, w]) => t.replace(re, w), s);

  const api = { plainWords, GOAL, COLLAPSED, collapsedFor, REACH_WORD, KIND_WORD, plainWhy, REACH_HELP, reachText, reachTitle, statusParts, statusTip, TITLE, titleOf, sevWord, isTrace, needsLook, review, fold, groupLabel, filters, filterFor, QUICK_START };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Simple = api;
})(typeof window !== 'undefined' ? window : globalThis);
