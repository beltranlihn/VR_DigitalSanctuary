/* Veation VR Studio · KNOBS: the catalog of Unreal's knobs a machine can read (obra/unreal/knobs.json, lote 5 design A §8.1). Pure
   (no DOM): it runs in the browser (the Knobs inspector), in Node (tools/score/knobs.mjs, the generator) and in the tests
   (tools/score/knobs_test.mjs). The catalog is made from three files the Director publishes and one the editor keeps, never from
   Unreal itself:
     da:*    the knobs of DA_Partitura_Obra (partitura_def.json + the live values of partitura.json): the only ones a change can be
             proposed for ("Send to Unreal")
     inst:*  the knobs of an instance placed in a level or in the Obra (FW_Bell, ExploreTime...), parsed from the rows of roles.json:
             read-only until the Director harvests instances (their values are the ones a person wrote down, not read from Unreal)
     lit:*   what the graphs hardwire (roles.json rows with scope "literal"): shown, never changeable from here
     cdo:*   the class defaults of the Blueprints (perillas.json), without the ones a BP only uses to remember its state
   The Knobs inspector draws a role from its rows here (groupsOf) and falls back to roles.json whenever this file is missing or older
   than roles.json (fresh). */
(function (root) {
  'use strict';
  const num = v => (typeof v === 'number' && Number.isFinite(v)) ? v : null;

  /* a variable the Blueprint keeps for itself, not a knob: perillas.json files them under "Interno" and the Z- state categories */
  const INTERNAL = /^(interno|z ?- ?(estado|interno)( interno)?)$/i;
  const isInternal = cat => INTERNAL.test(String(cat == null ? '' : cat).trim());

  /* a short signature of any JSON value (two 32-bit FNV-1a hashes over its text): roles.json read by the generator and by the
     browser gives the same one, so the editor can tell a knobs.json made from another roles.json. Not cryptographic */
  function sig(v) {
    const s = JSON.stringify(v);
    let a = 0x811c9dc5, b = 0x01000193 ^ 0x9e3779b9;
    for (let i = 0; i < s.length; i++) { const c = s.charCodeAt(i); a = Math.imul(a ^ c, 0x01000193) >>> 0; b = Math.imul(b ^ c, 0x85ebca6b) >>> 0; b ^= b >>> 13; }
    return a.toString(16).padStart(8, '0') + (b >>> 0).toString(16).padStart(8, '0');
  }

  /* "FW_Bell · after it, the bell fills by itself in 3 s" → { var: 'FW_Bell', note: 'after it, ...' }; "Appear.Duration · light first"
     keeps the dotted path; "BellPressTime (verify live: may be 0)" → note '(verify live: may be 0)'. A text with no identifier
     in front ("charge drains when released · literal in HallTickSteps") has no variable */
  function parseVar(text) {
    const t = String(text == null ? '' : text).trim(), m = /^([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)(?=\s*(?:·|\(|=|$))\s*(?:[·=]\s*)?(.*)$/.exec(t);
    return m ? { var: m[1], note: m[2].trim() } : { var: null, note: t };
  }
  /* the value text of a row: a number when it is one ("1.5", "−2", "+1.5"), else the text as written */
  function parseValue(text) {
    const t = String(text == null ? '' : text).trim().replace(/^[−–]/, '-').replace(/^\+/, '');
    return /^-?\d+(\.\d+)?$/.test(t) ? +t : String(text == null ? '' : text).trim();
  }
  /* an entry's key from the owner of its group ("HallDirector · Test_Hall") and its variable: inst:Test_Hall/HallDirector.FW_Bell.
     A place that is not a level (a component: "Timbre · Appear component") stays out of the key */
  function instKey(owner, v) {
    const [actor, where] = String(owner).split(' · ').map(s => s.trim());
    return 'inst:' + (where && /^(Test_\w+|Obra)$/.test(where) ? where + '/' : '') + actor + '.' + v;
  }
  const slug = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
  const litKey = (owner, label) => 'lit:' + String(owner).replace(/ graph$/, '') + '.' + slug(label);

  /* the groups of a role as roles.json writes them ({ owner, scope, rows }) rebuilt from the catalog, each with the keys of its
     rows (`ids`, parallel to `rows`); null when the catalog has nothing for the role. A row travels verbatim in the entry
     (`role.row`), so the drawing is the same as from roles.json */
  function groupsOf(knobs, roleName) {
    if (!knobs || !knobs.knobs) return null;
    const by = [];
    for (const [id, k] of Object.entries(knobs.knobs)) if (k.role && k.role.name === roleName) by.push({ id, r: k.role });
    if (!by.length) return null;
    by.sort((x, y) => x.r.group - y.r.group || x.r.order - y.r.order);
    const out = [], at = {};
    for (const { id, r } of by) {
      if (!(r.group in at)) { at[r.group] = out.length; out.push({ owner: r.owner, scope: r.scope, rows: [], ids: [] }); }
      const g = out[at[r.group]]; g.rows.push(r.row); g.ids.push(id);
    }
    return out;
  }
  /* is the catalog made from this roles.json? (else the inspector reads roles.json) */
  function fresh(knobs, roles) {
    return !!(knobs && knobs.sources && knobs.sources.roles && roles && roles.roles && knobs.sources.roles.sig === sig(roles.roles));
  }
  /* can a change of this knob be proposed (Send to Unreal)? only the Partitura's: everything else is read-only (an absent flag is false) */
  const proposable = k => !!k && k.scope === 'da' && k.proposable !== false;
  /* counts by scope, for the inspector's footer and the status of the generator */
  function counts(knobs) {
    const c = { da: 0, instance: 0, literal: 0, cdo: 0 };
    for (const k of Object.values((knobs && knobs.knobs) || {})) if (k.scope in c) c[k.scope]++;
    return c;
  }

  const api = { isInternal, sig, slug, parseVar, parseValue, instKey, litKey, groupsOf, fresh, proposable, counts };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Knobs = api;
})(typeof window !== 'undefined' ? window : globalThis);
