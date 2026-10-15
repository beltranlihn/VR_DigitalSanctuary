> Anexo 20 · Diseño del lote 5, parte B: "la partitura es segura de evolucionar y sus tiempos significan lo mismo que en Unreal" (2026-10-02, noche). Lo que manda sobre este documento es el [ADR-001](../ADR-001-partitura-y-unreal.md); lo construido y verificado está en el [anexo 18](18-auditoria-app.md), "Estado del lote 5". La parte A es el [anexo 19](19-lote5-diseno-unreal.md).

**Qué es este documento.** Es el **diseño de ingeniería** del lote 5 (parte B) y está **en inglés**, como se escribió: es un documento interno y sus cifras salen de mediciones sobre copias de la partitura. Se conserva tal cual, como registro de lo que se decidió y por qué. Lo que sigue (en español) dice qué cambió entre este diseño y lo que se construyó; el resto no se reescribe.

**Reconciliación decidida al construirlo** (con la parte A):
1. **La referencia de "≠ APK" vive dentro de la partitura** (`baseline`, §2 y §4.3), como dice este documento; es la parte A la que se ajustó a esto. Solo la mueven operaciones explícitas (`Edits.shiftBaseline`). No existe `obra/score/baselines/f0.json`.
2. **Una sola mejora a schema 3: la del §10.** No mueve ningún tiempo del usuario típico. Las marcas y los `bind` de la parte A llegan después, con la operación aparte y opcional **Bind to Unreal**.
3. **Las decisiones del §12 no se tomaron.** Donde la recomendación se podía aplicar sin riesgo y sin destruir nada (se deshace), se construyó la recomendada; cada una está en la lista del anexo 18 ("Decisiones que necesito de Beltrán") para que el dueño la confirme o la cambie.

**Otras diferencias medidas al construirlo.**
- **Motor (§1.2, §3).** Los elementos de reacción son **12**, no 16: los 4 `FX_GHOSTAPPEAR` cuelgan del inicio de un fantasma, su tiempo no sigue al usuario y no se marcan. Ningún tiempo ni total cambia por eso. Un elemento de reacción nunca alarga su momento, ni siquiera para el usuario típico.
- **Esperas (§11, paso 7).** Pasar `G_BREATH` a "espera al usuario" alarga **la espera** 19,0 s para el inactivo, pero su **total** sube 18,2 s (el momento ya corría 0,8 s más allá de los 6 s del reloj) y el del lento 8,7 s. El "+19.0" del diseño es por espera, no por total.
- **Mejora (§10).** Además de lo descrito, se niega si un momento hoy termina con un clip de DON'T SHARE (SHARE lo acortaría y se moverían tiempos), respeta los grupos con candado, y los registros aceptados pasan a la forma nueva (`fp` = `fpBase`, con su `value` y su `state`; un registro de una tarjeta, sin valor, queda con `value: null`). Después de la mejora, todo lo que una edición saca de la partitura queda como lápida (`deleted-here`) en el `uidMap` (`Edits.reconcileUidMap`, dentro de `commit()`), y las anclas `alt` cuentan como dependientes (`Engine.dependents`, `Engine.anchorsOf`).
- **Ramas (§5).** La vista por defecto es SHARE (como recomienda §12.2); **Auto** existe en el selector. Pegar, duplicar y mover varios a la vez conservan el lugar de cada clip en los dos lados, y la línea de efecto nombra el total del otro lado cuando se movió distinto.
- **Aceptado (§9).** Un registro conserva `fp` = `fpBase` y agrega `value`, `state`, `rev`, `unreal`, `verb` e `history`. El valor de un ítem de tarjeta incluye el momento (`<inicio>|<largo>|<momento>`).
- **Reglas al guardar (§8).** El trinquete de "solo lo nuevo" también se aplica a `S.UIDMAP` y `S.IDS.DUP` (lo que ya estaba mal en disco no impide guardar); se agregó `S.BIND.FIELD`. Un elemento anclado a nada lo detiene antes la comprobación rápida del servidor (`400`); los demás casos llegan como `422`. Sin `--base`, `check.mjs` trata los ciclos y los anclajes entre ramas como avisos.
- **Entering (§6.3).** **Match Unreal** funciona igual en schema 2 y en schema 3; la tarjeta calcula quién oye `VO_11h` como lo hace Unreal (la etapa corre con su reloj). En schema 2 el motor todavía hace esperar a `G_BREATH`, así que su línea de tiempo y la tarjeta difieren hasta mejorar a schema 3.
- **Importación (§7).** En una partitura de schema 2 el panel es solo un informe y se llama "Differences from guion.js"; descartar (**Dismiss**) un clip o un momento nuevo es permanente (queda como `deleted-here`); y una voz cuyo largo cambió solo porque cambiaron sus palabras nunca se toma.
- **Faltan, a propósito.** Las divergencias del final de la rama (§1.3: `VO_36c`/`VO_36d`, `VO_37`) como filas "Match Unreal", los seguimientos `VO_27h`/`VO_32h`/`SayGap` (§6.3), y una firma del servidor para el autor de las aceptaciones (§12.8).

**Lo que pide a otros.** La confirmación de `HelpAfter` (§6.3) y lo demás para el Director está en [PEDIDOS-AL-DIRECTOR.md](../PEDIDOS-AL-DIRECTOR.md).

**Los scripts de medición.** Los que cita este documento (`scratchpad/b5/`, en la carpeta temporal de la sesión de diseño) no están en el repo. Las cifras que importan quedaron fijadas en las pruebas (`tools/score/*_test.mjs`, sobre copias congeladas); para recontarlas, esas pruebas son el camino.

---

# Lote 5 · part B — the score is safe to evolve and its timing semantics match Unreal

Design document (internal, engineering). Covers audit findings **D4 + A13** (golden out of the live score), **D2** (re-extraction never overwrites the score), **D7** (SHARE / DON'T SHARE branches), **D8** (blocking vs non-blocking waits, Entering help chain), **D12** (validation outside the browser) and the rest of **D11** (accepted records carry their value). Source of the findings: `docs/editor-obra/anexos/18-auditoria-app.md`.

Everything below was measured on copies in the scratch dir (`scratchpad/b5/`), never on the repo. Prototypes that back the numbers (all runnable with `node`):

| File (scratch `b5/`) | What it is |
|---|---|
| `engine3b.cjs` | engine v3 prototype: branch filter, alternative anchors, non-blocking waits, reaction anchors |
| `engine3.cjs` | same without reaction anchors (variant A, rejected, kept for the comparison) |
| `migrate3.cjs` | schema 2 → 3 migration prototype |
| `importdiff.cjs` | guion.js import diff prototype (uid map, `#n` families, renamed keys, renamed moments) |
| `scen.cjs` + `extract_scr.mjs` | builds 4 modified copies of guion.js (audit scenarios) and extracts each one |
| `measure.cjs` … `measure5.cjs` | the measurements quoted in §1 |

Hard constraints respected by every step (from the owner and the Director, `obra/unreal/LEEME.md`):
- The web editor never writes `.uasset` and never applies anything to Unreal. Unreal changes only through **Send to Unreal** → `obra/unreal/partitura_propuesta.json`, applied by the Director on request (backup / smoke / restore).
- `obra/score/score.json` is never rewritten by a tool behind the user's back. A schema migration is an explicit, undoable in-app operation with a card that shows its effect; the user saves it.
- `web/prototipo-narrativo/` is read-only (runtime injection through the iframe is allowed).
- `DA_Partitura_Obra` (`obra/unreal/partitura.json`) rules the timing; `guion.js` is a visual reference.

---

## 1. Measurements (copies of the real score, rev 2, 592 elements, 73 moments)

### 1.1 Baseline facts
- A fresh extraction of today's `guion.js` is **identical** to the live score: 0 element diffs on 592, 0 golden diffs on 665, acts/beats/groups/lanes/markers/notes identical. Rev 2 contains no element edits.
- 45 uids carry `#n`; 0 duplicate uids; 693 ids across beats/elements/lanes, all unique; 55 keys repeat (D10 context).
- Known anchor cycles at load: `2.R4`, `5.R4` (typical). 0 dangling anchors.
- `score.accepted` is empty (0 records) → the D11 record migration is trivial today.
- Costs (node 25, this machine): `resolve` 1.1 ms · `staticProblems` 8.7 ms · 8 resolves (4 users × 2 branches) 11.5 ms · deep clone 4.6 ms · a full node process that loads the modules and checks: ~100 ms; bare `node` start 72 ms.
- `integrity.js` in node without a shim: `ReferenceError: window is not defined` (`})(window)` at the end) — confirmed.
- `App.protoDiff` (the old amber "differs from the prototype" counter) is computed in `compute()` and **read nowhere** (dead code since lote 3).

### 1.2 Engine v3: totals per simulated user

`v3` = schema 3 after the migration, with the semantics proposed in §3 (non-blocking waits + reaction anchors). Branch columns use the explicit branch.

| User | Today (schema 2) | v3, all branches | v3, SHARE | v3, DON'T SHARE | Elements moved vs today |
|---|---|---|---|---|---|
| Fast | 16:28.8 (988.80) | 16:28.8 | 988.80 | 985.55 | 0 |
| Typical | 16:58.0 (1018.00) | 16:58.0 | 1018.00 | 1014.75 | **0** |
| Slow | 18:05.3 (1085.28) | 17:56.6 | 1076.61 | 1073.36 | 466 |
| Idle | 19:36.3 (1176.28) | 19:08.6 | 1148.61 | 1145.36 | 466 |

- **Typical: golden 665/665 on the migrated score** (all branches and SHARE). Typical in SHARE vs all branches: 0 differences on 665 times. Therefore `effect()`, `divergent()`, the ripple line and everything measured with the typical user stay exactly as today.
- **Schema-2 parity of the new engine: 0 differences** on 665 times × 4 users and on `helpActive`.
- What still depends on the user (idle pushes, seconds): G_BELL 20.0 · G_SENSOR 7.0 · G_CHOOSE 23.0 · G_SAVE4 25.0 · G_SAVE5 45.0 · G_SHARE 24.0 (blocking in Unreal). G_BREATH / G_HEART / G_GRAB / G_DRAW now push **0.0 s** (they pushed 19.0 s each for Idle, 9.5 s each for Slow).
- Starts that differ between Fast and Idle: 560/592 before and after (the Hall waits are early and truly blocking, so almost everything after them still depends on the user; correct).
- Help lines that play: unchanged for every user (Slow/Idle: VO_01h, VO_03h, VO_11h, VO_16h, VO_27h, VO_32h; Fast/Typical: none).
- Reaction elements (anchored to the END of a non-blocking wait, directly or transitively): 16 — BIO_ON ×2, GHOST_BREATH/HEART/ATTRACT/DRAW and their FX_GHOSTAPPEAR/FX_GHOSTOUT, HAP_PULSE_SOFT, HAP_BREATH_HUM. All leaves. With reaction anchors they follow the simulated user (the Idle user's ghost stays 25 s) without lengthening the moment. Without reaction anchors (variant A) these 8–16 elements would sit at the typical time for every user (Fast: 8 elements wrongly moved up to 4.2 s later).
- **Evaluation-order trap (D6) reproduced:** my first reaction-anchor prototype called `tEnd(k)` for help/FX children before the usual filters; that changed the order in which the two cycles are broken and moved **2264 times** across the 4 users and 98/665 typical golden times. Fixed by calling `tEnd` in exactly the old order. Lesson: every engine change ships with the 4-user parity test on the frozen fixture (step 1 + step 3).

### 1.3 Branches (D7)
- 16 elements carry `when`: **11 SHARE** (VO_36c, FX_RINGVANISH, RING_FREE, FX_SOULSWIM, FISH_DOOR, FX_DOOROPEN 9.5b, DOOR_W_SOUL, FX_SOULSWIM#2, FISH_AWAY, FX_SOULJOIN, VO_35b) and **5 DON'T SHARE** (VO_36d, FX_SOULVANISH, SOUL_VANISH, FX_DOOROPEN 9.6, VO_35c). In the score today: `when: 'yes'|'no'` (closure names) for 12, `when: 'when'` (inline closure, unusable) for 4 — classified by uid from guion.js:609, 632-634.
- One common element anchors into a branch: **VO_37 → VO_35b.end**. The migration gives it a DON'T SHARE anchor (VO_35c.end + 0, the prototype's timing). No other cross-branch anchor (0 in each branch after migration).
- DON'T SHARE: moment 9.5b lasts 4.95 s instead of 8.20 s; **37 later items shift −3.25 s**; total −3.25 s for every user.
- `SOUL_UP` has no `when` but only shows in SHARE (its `apply` returns when `S.share === false`); it is the timing spine of 9.7 (VO_35b/c, FX_TITLE, TF_IN, QUEDA hang from it), so it stays common.
- Unreal facts (BP_Obra_SC tracker, FlowShare/FlowConst): timeout `ShareFW` 30 s = **DON'T SHARE**, with `bSimulated` = SHARE; `ShareAnswer` no longer plays VO_36c/VO_36d; DON'T SHARE plays no VO_35c and VO_37 at PT 8; SHARE plays VO_35b at PT 8 and VO_37 at 8 + VODur + 0.6. After migration the score still has the prototype's choices (VO_37 at 9.7 + 14.83 s in SHARE, + 15.33 s in DON'T SHARE vs Unreal 8 + VODur(35b) + 0.6 and 8.0). These are C3 divergences to be offered as "Match Unreal" actions, never folded into the migration (it must be timing-neutral).

### 1.4 Entering help chain (D8)
`VO_11h` today: `G_BREATH.start + 12` in moment 1.R4, help of G_BREATH. Unreal (BP_BreathStage_SC `StepStageVO`): VO_11b when free, then VO_11h `HelpAfter` (4 s, `perillas.json` › BP_BreathStage_SC) later, only if `Rig.bZone` is false. Re-anchored to `VO_11b.end + 4` and moved to VO_11b's moment (1.R5a):

| User | VO_11h before → after | Help plays before → after | Total |
|---|---|---|---|
| Fast | 230.1 → 237.1 | no → no | unchanged |
| Typical | 230.1 → 237.1 | no → no | unchanged (only VO_11h moves) |
| Slow | 241.7 → 248.7 | **yes → no** (Slow acts at 15.5 s; the help comes 19.0 s after the wait starts) | unchanged |
| Idle | 266.7 → 273.7 | yes → yes | unchanged |

Other help lines, for reference (start after their wait starts): VO_01h 8 s, VO_03h 8 s, VO_16h 14 s, VO_27h 14 s, VO_32h 14 s. contract `cues.34` says Unreal plays VO_27h at 20 s and VO_32h at 15 s: same kind of follow-up action, out of this lote's migration.

### 1.5 Re-extraction (D2), on 4 modified copies of guion.js

| Scenario | Naive re-extract (today's extract_v1) | Proposed import diff |
|---|---|---|
| Unchanged guion.js | 0 lost, 0 retargeted | 0 rows |
| Extra `fx('FX_GHOSTAPPEAR', 2, 'extra cue')` before ghostSpan in 1.8 | `el_yjvsq81bml` now names the new clip | 1 **added** (the new cue) + 1 uid-map update (`1.8/FX_GHOSTAPPEAR` → `…#2`, same id keeps naming GHOST_BELL's cue) |
| VO_11h renamed VO_11hb | 1 id lost | 1 **renamed** row (key + label), same id |
| VO_11h text edited + VO_36p `.3`→`.8` | edits silently replaced | 2 **changed** rows: VO_11h {text, dur(estimate)}, VO_36p {timing: at} |
| Moment 1.7 renumbered 1.7a | 2 ids lost | moment rename detected (`1.7`→`1.7a`), 2 uid-map updates, **0** false changes |

Seeding the uid map signatures from the score itself is exact today: signature(score element) = signature(fresh extraction) for **592/592**.

---

## 2. Schema 3 (JSON shapes)

Only additions and renames; everything else of schema 2 stays. `schema: 3` is a ratchet: a schema-2 client can never save over a schema-3 file (server rule, §8).

```jsonc
{
  "schema": 3,
  "rev": 7,
  // D7 · one entry per decision of the user that splits the piece
  "branches": {
    "share": {
      "name": "Share or not",
      "gate": "el_1e5ld7nuoe",                 // G_SHARE: the wait that decides it
      "options": { "yes": { "label": "SHARE", "mark": "SHARE.yes" },
                   "no":  { "label": "DON'T SHARE", "mark": "SHARE.no" } },
      "default": "yes",                        // what a user who chooses picks in the simulation
      "onTimeout": "no",                       // Unreal: ShareFW 30 s = DON'T SHARE (bSimulated: SHARE)
      "note": "BP_Obra_SC FlowShare"
    }
  },
  "elements": {
    "el_15plm7q1mk": {                         // VO_35b
      "branch": { "on": "share", "value": "yes" },   // replaces `when`; absent = common to every branch
      "legacy": { "uid": "9.7/VO_35b", "when": "when", "track": "vo", "behavior": false }
      // `when` is removed from the element; its old text is kept in legacy.when
    },
    "el_xxx_VO_37": {
      "at":  { "ref": "el_15plm7q1mk", "edge": "end", "off": 0 },          // SHARE / common anchor
      "alt": { "share=no": { "at": { "ref": "el_15zl7wpopi", "edge": "end", "off": 0 } } }   // C1: one anchor per branch
    },
    "el_1s52yl12kh": {                         // G_BREATH
      "gate": { "expected": 6, "fw": 25,
                "blocking": false,             // D8: the stage runs on its clock; the user only decides the help
                "cond": "breath.zone" }        // vocabulary v0 (anexo 11)
    },
    "el_1f5c8nc1p5": {                         // G_BELL
      "gate": { "expected": 5, "fw": 25, "blocking": true, "cond": "hall.bell.charged", "knob": "BP_HallDirector_SC.FW_Bell" }
    },
    "el_1kdwaubwss": {                         // VO_11h after the Entering step (§6.3), not after the migration
      "at": { "ref": "<VO_11b id>", "edge": "end", "off": 4, "knob": "BP_BreathStage_SC.HelpAfter" }
    }
  },
  // D4 · what the APK is assumed to do (replaces `golden`); typical user, relative times
  "baseline": {
    "kind": "prototype-f0",                    // later: "unreal-trace" (F3 harvest)
    "total": 1017.9967,
    "rel": { "el_…": [startInMoment, length] },   // 592 entries
    "log": [ { "op": "migrate", "at": "…", "by": "B" },
             { "op": "voices", "at": "…", "by": "B", "ids": ["…"], "src": "final mix" } ]
  },
  // D2 · frozen prototype names → ids (and moments, prefixed '@'); the importer never derives an id from a uid again
  "uidMap": {
    "1.8/FX_GHOSTAPPEAR": { "id": "el_yjvsq81bml", "sig": "1a2b3c4d5e" },   // sig = guion-side record when the score last took it
    "@1.8": { "id": "bt_1vhu9hmufz", "sig": null },
    "1.R4/VO_11x": { "id": "el_…", "state": "deleted-here" }                // tombstones: deleted in the editor / removed in guion
  },
  // D11 · one record per rule+element, never deleted
  "accepted": [
    { "fp": "C3.DRIFT|el_1f5c8nc1p5", "rule": "C3.DRIFT", "ly": "C3", "sv": "warn", "el": "el_1f5c8nc1p5",
      "value": "30|25",                        // the problem's key parameter when accepted (same string as its fingerprint param)
      "unreal": 25,                            // what Unreal has, when known (informative)
      "state": "accepted",                     // or "reopened"
      "who": "B", "reason": "…", "at": "…", "rev": 7, "msg": "…",
      "history": [ { "state": "accepted", "value": "30|25", "who": "B", "reason": "…", "at": "…" } ] }
  ]
}
```

Rules of the shapes:
- `branch.on` must be a key of `branches`; `branch.value` one of its options.
- `alt` keys are `"<on>=<value>"`, each value an object with `at` and/or `end` (same shape as `at`). Beats may carry `alt` too (same rule; none needed today).
- `gate.blocking` is a boolean in schema 3. In schema 2 it is absent and means blocking (legacy behavior, golden).
- `at.knob` / `end.knob` (optional): the offset IS this Unreal knob (`"<BP>.<var>"` from `perillas.json`, or `"DA_Partitura_Obra.<knob>"`). Integrity compares `off` with the knob (rule C3.KNOB.OFFSET, §6.3).
- `baseline.rel[id]` = `[start − start of its moment, end − start]`, typical user, default branch. Exactly the two numbers `divergent()` already compares.
- `uidMap` keys: element uids as in `legacy.uid` (`<moment>/<key>[#n]`), moments as `@<moment uid>`. `state` absent = live.
- Removed: `golden` (becomes `baseline`), `when` (becomes `branch` + `legacy.when`).

New ids (D2): `Edits.newId(score, prefix)` → `prefix + Date.now().toString(36) + 4 base-36 random chars`, retried until unused in beats/elements/lanes/uidMap. Matches the server's `el_[A-Za-z0-9]{3,40}`. Tests inject `now` and `rand`.

---

## 3. Engine v3 (`js/engine.js`)

### 3.1 API
```js
ScoreEngine.resolve(score, { persona, branch }) → {
  t, total, acts, helpActive, cycles, dangling,            // as today
  off,          // { id: true } elements outside the chosen branch (still timed: their "phantom" times)
  react,        // { waitId: absolute time when THIS user acts } (blocking: = end of the wait)
  reactive,     // [ids] reaction elements (§3.2): follow the user, never lengthen their moment
  crossBranch,  // [ids] C1 violations: anchored to an element of another branch with no alt
  branch        // the resolved selection, e.g. { share: 'yes' }
}
```
`branch` option:
- `'all'` → every element, primary anchors (the prototype's way; the golden test uses it).
- `undefined` → schema 2: `'all'`; schema ≥ 3: each branch's resolved default.
- `{ share: 'yes' | 'no' | 'auto' }` → filter. `'auto'` (and a missing key) = `onTimeout` if this user hits the deciding wait's timeout (`persona.wait(g) >= g.fw`, i.e. Idle), else `default`. No per-persona table in the data.

### 3.2 Semantics (all with the old evaluation order — see the trap in §1.2)
1. **Branch filter.** `off` = elements whose `branch.value` ≠ selection. They are still resolved (phantom times, so anchors never jump), but never count for their moment's end, the total, `helpActive` or overlaps.
2. **Alternative anchors.** `pick(x, 'at'|'end')`: if a selection is active and `x.alt["on=value"]` matches it, use that anchor; otherwise the primary one. Used for elements and beats, and inside `crossSpan`.
3. **Cross-branch anchor (C1).** An element not in `off` whose chosen anchor points to an element in `off` → `crossBranch`; the phantom time is used (no jump), the check rejects new ones.
4. **Non-blocking wait.** `gate.blocking === false` → its length is `gate.expected` for every user (the stage clock). `react[g] = start + persona.wait(gate)` for every wait.
5. **Reaction anchors.** An anchor to the `end` edge of a non-blocking wait resolves at `react[g] + off` (when this user acts). The element, and anything anchored to it, is `reactive`: it is computed after the other children in the same order as before and excluded from its moment's end (like help lines today).
6. **Help.** `helpActive[h] = t[h].start < react[g]` (for blocking waits identical to today's `< end`).

Parity guarantee: with schema 2 (no `blocking`, no `branch`, no `alt`) results are bit-identical to today (measured 0 diffs, 4 users).

### 3.3 Who passes what
- `App.sched` = resolve(persona, `App.branchView`) — what the timeline shows.
- `App.schedT` = resolve(`typical`, default branches) — what decides writes, effect, ripple, divergent (≡ today: 0 diffs).
- `App.schedAlt` = `[{ sel: {share:'no'}, sched: resolve(typical, {share:'no'}) }]` — only for branch-sensitive problems (§5.2). +1 resolve per compute/commit (~1 ms) and one extra `staticProblems` pass on branch-sensitive rules only (< 9 ms).
- Integrity's internal `typical()` passes no branch (= defaults). Golden passes `'all'`.

---

## 4. D4 + A13 · golden out of the live score; the APK baseline

### 4.1 Frozen fixtures for the engine test
- `tools/score/fixtures/f0-score.json`: the extraction output (schema 2, with `golden`), produced by `node tools/score/extract_v1.mjs --fixture` (writes only if the file does not exist; `--refreeze` to overwrite, a deliberate developer act visible in git). Today it equals the live score's elements (measured).
- `tools/score/fixtures/f0-expect.json`: `{ totals: {fast: 988.80, typical: 1017.9967, slow: 1085.28, idle: 1176.28}, help: {slow: [...], idle: [...]}, cycles: ['2.R4','5.R4'] }` (persona semantics of schema 2, regenerated with `--refreeze` only).
- `golden_test.mjs` reads the fixture, never `obra/score/score.json`:
  1. 665/665 typical, `branch: 'all'` (as today).
  2. Totals and help sets of the 4 users on the schema-2 fixture (catches evaluation-order regressions).
  3. Runs `Edits.migrate3` on the fixture in memory and checks: typical 665/665 (`'all'` and default branch), the v3 totals table of §1.2 (±1 ms), DON'T SHARE −3.25 s, 0 cross-branch anchors per branch.
  4. Optional `--live` flag: the same 665 check against the live score, as information only (exit 0, prints how many times differ: "the score was edited", never a failure).
- `edits_test.mjs` and `integrity_test.mjs` switch to the fixture by default (they assert "no blocking at load", card counts, etc., which become false after real edits or the migration), with `--live` to run them on the real score.

### 4.2 extract_v1 never writes the score
- Default output becomes `obra/score/score.extracted.json`. Flags: `--out <path>`, `--fixture`, `--refreeze`.
- It **refuses** any output path that resolves to `obra/score/score.json` (exit 2, message: "score.json is only written by the editor: import score.extracted.json with File ▸ Import, or use the Changes in guion.js panel"). There is no `--force`: replacing the score is an in-app import (commit, card, undo, the user saves).
- README "Ojo: pisa las ediciones" is replaced by the new flow.

### 4.3 What replaces `score.golden` in the app: `score.baseline`
Kept **inside** the score on purpose: the operations that move it (real voice lengths, Entering "Match Unreal", future harvest) must be in the same commit as the change they compensate, so undo, redo, drafts, the 409 conflict and saving stay atomic. A separate file would need a two-file transaction.
- Shape in §2 (relative times, typical, default branch).
- `Integrity.divergent(score, sched, contract, gov, baseline)` reads `baseline.rel` (schema 3) or derives rel from `golden.times` (schema 2 adapter, until migrated). Same comparison, same 0.05 s tolerance.
- Pure helper `Edits.shiftBaseline(baseline, A, B, ids, logEntry)` → new baseline where, for each id in `ids` (or every id when null) present in both schedules, `rel += [relB − relA, lenB − lenA]`; appends `logEntry`. Used by:
  - `Act.useRealLengths` (replaces the absolute shift of `golden.times`; log `{op:'voices', ids, src:'final mix'}`),
  - the Entering "Match Unreal" (§6.3; log `{op:'match-unreal', ids:[VO_11h], knob}`) — that new place IS what the APK does,
  - later: "Rebase on Unreal trace" (F3, from `obra/unreal/traza.json`), out of this lote.
- Status-bar tooltip: "APK baseline: prototype F0 + N corrections (baseline.log)".
- Remove the dead `App.protoDiff` block.

---

## 5. D7 · SHARE / DON'T SHARE

### 5.1 Data and default
- `branches.share` as in §2; `branch` on the 16 elements; `alt["share=no"].at` on VO_37 (VO_35c.end + 0: today's time).
- **Shown by default: SHARE** (the narrative's main path, the prototype's default and the APK's `bSimulated`). The transport gets a branch selector: `Auto · SHARE · DON'T SHARE` (Auto: Idle → DON'T SHARE, everyone else → SHARE, which is what Unreal does on a timeout). Saved in preferences, not in the score.

### 5.2 Rules
- **C1.BRANCH.ANCHOR (block):** an element may anchor only to (a) a common element, (b) an element of its own branch value, or (c) carry an `alt` for every other option of that branch. Moments follow the same rule. Engine: `crossBranch`; check.mjs rejects NEW ones.
- **C1.BRANCH.FIELD (block):** unknown branch or option, malformed `alt` key.
- Branch-sensitive C2 rules run once per branch run and are deduplicated by fingerprint; the message and the param say the branch ("… in DON'T SHARE"): C2.VO.OVERLAP, C2.ALMA.EARLY, C2.HELP.LATE, C1.ANCHOR.CYCLE, C1.BRANCH.ANCHOR. The "two voices that start together are alternatives" exception in C2.VO.OVERLAP becomes "elements of different branch values never overlap".
- `opItems`/`effect` stay on the typical default run (phantom times keep DON'T SHARE elements measurable), so editing a DON'T SHARE element still opens the right card.

### 5.3 UI
- Off-branch clips: drawn dimmed and hatched (class `.offbr` in `editor.css`), title "DON'T SHARE only"; they stay editable (an element of the other branch is still part of the score).
- Inspector, Time section: "Branch: SHARE only / DON'T SHARE only / both" (select, op `branch`, goes through `commit`) and, when an anchor crosses branches, "Anchor in DON'T SHARE" (same control as the anchor picker of lote 4, writes `alt`).
- 3D tab: when the branch view changes, inject `SC.S.share = (branch === 'no') ? false : true` into the iframe (runtime only); the prototype's own `when` closures then show the same branch.
- Status bar: `Typical · SHARE · total 16:58`.

---

## 6. D8 · waits like Unreal

### 6.1 Classification (from `contract.json` + trackers)
| Wait | blocking | cond | Unreal |
|---|---|---|---|
| G_BELL | true | hall.bell.charged | FW_Bell 25 (HallDirector) |
| G_SENSOR | true | hall.sensor.live | FW_Tool 20 |
| G_CHOOSE | true | hall.soul.live | FW_Choose 25 |
| G_SHARE | true | share.pick | Res_Cortafuegos 30 |
| G_SAVE4 | true | attract.saved | Etapa_Tope[3] + Corte_Espera (SAVE MELODY closes the stage) |
| G_SAVE5 | true | draw.saved | Etapa_Tope[4] + Corte_Espera |
| G_BREATH | false | breath.zone | stage clock; gesture decides VO_11h |
| G_HEART | false | heart.zone | stage clock |
| G_GRAB | false | attract.first | CueAttract threshold |
| G_DRAW | false | draw.ink>0 | CueDraw threshold |

`blocking` is **derived from contract.json** in the migration (an entry of kind `not-blocking` matching the key ⇒ false, otherwise true), so there is one source; `cond` and `knob` come from a small table `MIGRATE3.waits` in `edits.js`. A test asserts the table and the contract agree for all 10 waits.

### 6.2 Engine and UI
- Engine: §3.2 points 4–6.
- Timeline: a non-blocking wait draws its fixed clock length; the simulated user's reaction is a thin hatched tail from `start + expected` to `react` labeled "the slow user acts here · the stage does not wait" (not drawn for Typical). Help lines keep the existing inactive style when `helpActive` is false.
- Inspector Wait section: "Waits for the user (as in Unreal)" checkbox (op `gate`, goes through `commit`); for non-blocking waits the "Timeout" field is relabeled "Gives up at" with the note "Simulation only: in Unreal the stage runs on its clock"; the per-user table shows "acts at X s · help plays / no help".
- Rules: `C2.WAIT.WHERE` now reads the flag (a blocking wait inside a stage moment that is not a SAVE wait); new `C3.BLOCKING` (warn) when `blocking` disagrees with the contract (`not-blocking` entry vs `true`, or a knob/partitura wait set to `false`). `C3.NOTBLOCKING` (info) is retired once the flag exists.
- Changing `expected` keeps its lote-1 rule (Typical only).

### 6.3 Entering chain (separate, explicit, after the migration)
- New contract entry `help.after` (editor-owned file): `{ id: 'help.after', kind: 'knob', match: { keys: ['VO_11h'] }, anchor: { ref: 'VO_11b', edge: 'end' }, knob: { name: 'BP_BreathStage_SC.HelpAfter', value: 4, source: 'perillas.json' }, on: { move: 'warn', trim: 'info' } }`.
- Rule `C3.KNOB.OFFSET` (warn): the element's anchor is not `<anchor.ref>.<edge> + knob`; Problems action **Match Unreal**: re-anchors `VO_11h` to `VO_11b.end + 4` with `at.knob`, moves it to VO_11b's moment (1.R5a), keeps `help: G_BREATH`, and shifts the baseline for VO_11h only (`shiftBaseline` with `ids: [VO_11h]`). Card: "VO_11h now plays 4 s after VO_11b ends (HelpAfter in BP_BreathStage_SC), as in Unreal: 3:50.1 → 3:57.1. Nothing else moves. The slow user no longer hears it (they act at 15.5 s; it comes at 19.0 s)."
- The same entry shape later covers VO_27h (20 s) and VO_32h (15 s) from `cues.34` and VO_11b's `SayGap` 0.5 (which would shift 435 items +0.5 s); those are listed as follow-ups, not done here.
- To verify with the Director before shipping: that HelpAfter counts from the END of VO_11b (`SayEndAt`) and not from its start (tracker wording: "VO_11h HelpAfter s después"; annex 14:30 and the audit say end).

---

## 7. D2 · guion.js is an import source, never the truth

### 7.1 Pieces
- `js/importdiff.js` (UMD, pure, browser + node): `recordsOf(extraction)`, `recordOfScore(score, id)`, `sigOf(record)`, `diff(score, extracted) → { beatRen, rows, mapUpdates }`.
- `tools/score/extract_v1.mjs` → `obra/score/score.extracted.json` (§4.2).
- `tools/score/import_report.mjs [--json] [--extracted <path>]`: runs the extraction to `score.extracted.json` (unless given), loads the live score read-only, prints the rows (or JSON). Never writes the score. Exit 0.
- Server `POST /api/guion/scan`: runs `node tools/score/extract_v1.mjs` (output fixed to `score.extracted.json`), returns `{ ok, extracted: '/obra/score/score.extracted.json', at }`. The browser then fetches it and runs `ImportDiff.diff` itself (same module as the CLI).
- In-app panel **Changes in guion.js** (Library tab or File menu ▸ "Check guion.js for changes…").

### 7.2 Algorithm (prototype `importdiff.cjs`)
1. Records use uids for every reference (extraction ids are not stable): `{uid, beat, key, type, group, at:{ref:uid,…}, end, dur, gate:{expected,fw}, help:uid, when, text, label, hint, note}`. `sig` = 10-char hash of the record.
2. **Moments:** by uid; an unmatched old moment and an unmatched new moment with the same title → renamed (`beatRen`), uids under it are rewritten before matching.
3. **Families** = moment + key without `#n`. If a family keeps its size and uids, match by uid. Otherwise assign old ↔ new by content cost (label/note/hint/text 2 each, anchor ref/edge 2, offset 1, dur 1; accept ≤ 4), greedy on sorted costs. An old uid matched to a different new uid → `mapUpdates` (the id stays, the uid moves). Unmatched new → **added**; unmatched old → **removed in guion**.
4. **Renamed key:** an unmatched old and an unmatched new clip in the same moment and type whose records differ only by key (label compared with the key substituted) → **renamed**.
5. **Changed:** for matched pairs, compare the guion record now with the base record (the one with the stored `sig`; references normalized through `beatRen`/`mapUpdates`). Rows group fields as `text` (text, label, hint, note), `timing` (at, end, dur, gate), `structure` (type, group, help, when, beat, key). A VO whose `dur` changes only because its text changed is labeled "estimate, the recording decides" (voices last their recording, lote 3).
6. Each row also says whether the **score** changed that element since the base (`sigOf(recordOfScore) !== base sig`) → "edited here too".

### 7.3 Panel and verbs (all through `commit`, all undoable, card per batch)
| Row | Default | Verb (op type) |
|---|---|---|
| added | offered | **Add** (`import-add`): new id (`Edits.newId`), anchors through `uidMap` (or to rows added in the same batch, topological order; an unresolved anchor falls back to the moment start with the extracted offset and is flagged), free lane, `legacy.uid`, `uidMap[uid] = {id, sig}` |
| removed in guion | offered | **Delete here** → the lote-1 delete planner (its own card); **Keep** → `uidMap[uid].state = 'removed-in-guion'` (quiet) |
| renamed | offered | **Take the new name** (`import-rename`): key + label, map update |
| changed · text | offered | **Take guion's text** (`import-text`) |
| changed · timing | shown, not default | **Take guion's timing** (`import-timing`); the row says "DA_Partitura_Obra rules the timing; the score keeps its own unless you take this" |
| uid map updates | automatic with any apply | `import-map` (quiet): uids follow the clips; ids never change |
| new moment | offered | **Add moment** with its elements, after its predecessor in its act |

After any apply, the touched `uidMap` entries get the new `sig`. A row not applied keeps the old `sig`, so it keeps showing. "Dismiss" stores `uidMap[uid].seen = sig` (row hidden until guion changes it again).

### 7.4 Migration seed
`uidMap` is built from `legacy.uid` (592) plus `@<moment>` (73), each with `sig = sigOf(recordOfScore(...))`. Measured: equal to the fresh extraction's signature for 592/592, so the base is exact today. Elements created in the editor have no uid and never appear in the diff.

---

## 8. D12 · validation outside the browser

### 8.1 Node-loadable modules
- `integrity.js` ends with the same UMD footer as `engine.js`/`edits.js` (`module.exports` in node, `root.Integrity` in the browser). Tests drop `globalThis.window = globalThis`.
- **`js/policy.js`** (UMD, pure), extracted from `commit()`:
  - `Policy.QUIET` (the set now in app.js, plus `migrate`, `import-map`, `branch-view`).
  - `Policy.decide(op, items, { relocated, ripple }) → { mode: 'quiet' | 'apply' | 'card', shown, needReason, toast }` (today's branches of `commit`, unchanged behavior).
  - `Policy.acceptRecords(accepted, items, { who, reason, at, rev }) → accepted'` (the "anyway" writer, D11 shape of §2, never deletes, appends `history`).
  - `Policy.reopen(accepted, fp, { who, at }) → accepted'` (sets `state: 'reopened'`, appends history).
  - `commit()` keeps the DOM parts (cards, toasts, render) and calls these.
- **`js/check.js`** (UMD, pure): `Check.invariants(score, base, ctx) → { ok, errors, warnings, grandfathered }`, used by `tools/score/check.mjs`, by the server (through the CLI) and by `save()` in the browser before the PUT (the user sees the same message the server would give).

### 8.2 Invariants (reject only what is NEW relative to `base` = the score on disk)
| Code | Reject | What |
|---|---|---|
| S.STRUCT | yes | `Edits.validate` (schema 2 or 3) |
| S.IDS.DUP | yes | an id in more than one of acts/beats/groups/lanes/elements/markers/notes; two uidMap entries with the same live id |
| S.ANCHOR.MISSING | yes | at/end/help/alt/beat-at pointing to nothing (always, not only new: today 0) |
| S.CYCLE.NEW | yes | cycles of `next` (typical, each branch run) not in `base` — the 2 known cycles (2.R4, 5.R4) are grandfathered and listed |
| S.SCHEMA.DOWN | yes | `next.schema < base.schema` (an old tab saving over a migrated score) |
| S.BRANCH.FIELD | yes | §5.2 |
| S.BRANCH.CROSS.NEW | yes | cross-branch anchors not in base |
| S.UIDMAP | yes | live uidMap entry pointing to a missing element (schema 3) |
| S.TOTAL | yes | typical total not finite or > 3600 s |
| W.CONTRACT | no | contract entries with `keys` that match no element; knob names absent from partitura_def/perillas |
| W.ACCEPTED.ORPHAN | no | accepted records of deleted elements |
| W.BASELINE.STALE | no | baseline ids that no longer exist |

Why "new only": rejecting any cycle would block every save today (2 known cycles); the ratchet keeps old debt visible (Problems) and forbids adding more.

### 8.3 `tools/score/check.mjs`
```
node tools/score/check.mjs <score.json> [--base <score.json>] [--contract obra/unreal/contract.json] [--json]
node tools/score/check.mjs --stdin --base obra/score/score.json --json        (server mode)
exit 0 ok · 1 violations · 2 bad input/usage
stdout (--json): { ok, schema, totals: {typical: …}, errors: [{code, msg, ids}], warnings: […], grandfathered: […], ms }
```

### 8.4 Server: call node, do not port (decision)
`serve_editor.py` keeps its Python `check_score` as a fast structural pre-check (now accepting schema 2 or 3) and then runs `check.mjs --stdin --base <SCORE>` inside the existing write lock, after the 409 test and before the atomic write:
- `NODE = os.environ.get('VVR_NODE') or shutil.which('node')`; `subprocess.run(..., input=body, capture_output=True, timeout=20)`.
- exit 1 → **422** `{error: 'the score breaks a rule', errors: [...]}` and nothing is written. The client shows the errors and offers **Save a copy** (`/api/score/copy`, which does not validate) so work is never lost.
- node missing, `VVR_CHECK=off`, timeout or exit 2 → write anyway (fail open) and answer `{…, check: 'structural-only' | 'failed'}`; the client toasts "Saved without the full check (…)"; the server logs it. The browser already ran the same `Check.invariants` before the PUT.

Justification: the invariants need the engine's exact semantics (cycle detection depends on the memo evaluation order: §1.2 shows one misplaced call moves 2264 times); a Python port is a second engine to keep identical forever. node is already required by every test and present (v25.8.1); the cost is ~0.1 s per save, single user, local.

Import (`importScore`) runs `Check.invariants(file, App.score)` too; a schema-2 file imported into a schema-3 editor is migrated in the same card ("This file is schema 2: it is upgraded the same way"); its `accepted` records are kept only when their fingerprint and value match a current problem (the rest are listed as dropped).

---

## 9. D11 (rest) · accepted means "this value"

- Every problem gets `fpBase = rule|el` and `param` (string, possibly empty). Today `staticProblems` already builds `rule|el|param`; the split makes the record value explicit.
- New params where missing: `C3.DIVERGE` → `"<dRel>|<dLen>"` (0.1 s); `C2.VO.REAL` → count + hash of the gaps; C3 card items from `opItems` → `"<rel>|<len>"` of the element after the edit (0.05 s), `"deleted"` for deletions.
- Matching: a problem is accepted iff a record with its `fpBase` has `state: 'accepted'` and `value === param`. A record with a different value → the problem is **open** and carries `was: {value, who, reason}`; Problems shows "Reopened: accepted at 30 s by B ("…"), now 300 s". Today's `DIVERGE` lookup `x.el === id && x.ly === 'C3'` (any C3 acceptance hides ≠ APK forever) is replaced by this.
- `opItems` downgrades an item to info only on an exact value match. Fatigue control: when a record exists for the same `fpBase`, the card shows "You accepted this before at 3.2 s: '…'" and pre-fills the reason (still a click; Enter still never accepts).
- **Reopen** never deletes: `state: 'reopened'` + history entry. Records of deleted elements stay visible as "element deleted" until an explicit **Clean up accepted** (op `accepted-clean`).
- `rev` stored on acceptance (score rev at the time); `unreal` stored when the rule knows it (knob value, baseline rel).
- Author (`who`) stays the local B/S switch in this lote; a server `GET /api/whoami` (git `user.name`, else OS user) is a decision for the owner (§12).
- Migration of records: `fp` with three parts → `fpBase` + `value`; two parts (card records) → `value: null` (shown as "accepted before, value unknown": open). Today: 0 records.

---

## 10. The schema-3 migration as an in-app operation

### 10.1 Trigger
When `App.score.schema === 2`, Problems shows one info row `C1.SCHEMA` "This score is schema 2. Upgrade it to keep it safe to evolve" with the action **Upgrade…**. Never automatic, never on load, never in a tool.

### 10.2 What `Edits.migrate3(score, Engine, contract) → { next, report }` does (pure)
1. `schema: 3`.
2. `branches.share` (§2) with `gate` = G_SHARE's id.
3. `branch` on the 16 `when` elements (closure names `yes`/`no`; the 4 inline ones by uid); `legacy.when` keeps the old text; `when` removed. Unclassified `when` → the migration refuses (report lists them).
4. `alt` for every common element/moment anchored into a branch: the counterpart in the other branch (same moment, same type, same primary anchor) with the same edge/offset, else the branch element's own anchor. Today: VO_37 only.
5. `gate.blocking` (from the contract), `gate.cond`, `gate.knob` for the 10 waits. An unknown wait → refuse.
6. `baseline` from `golden` (rel form) + `log: [{op:'migrate'}, …golden.voices as {op:'voices'}]`; `golden` removed.
7. `uidMap` (elements + `@moments`) with seeded `sig` (§7.4).
8. `accepted` records converted (§9).
9. Postconditions, asserted inside the function (the migration aborts and reports if any fails): typical, default branches: every element and moment time equal to before (±1 ms) → **nothing moves for the typical user**; `crossBranch` empty in every branch run; no dangling; `divergent()` set equal before/after; `Check.invariants(next, score)` ok.

### 10.3 Card (`UI.chooseCard`), numbers computed live
Title: **Upgrade the score to schema 3**

Body: "The score learns three things Unreal already does. Nothing moves for the typical user (16:58.0)."

- "Waits: G_BELL, G_SENSOR, G_CHOOSE, G_SAVE4, G_SAVE5 and G_SHARE wait for the user, as in Unreal. G_BREATH, G_HEART, G_GRAB and G_DRAW run on the stage clock: a slower user only decides whether the help line plays. Slow 18:05.3 → 17:56.6 · Idle 19:36.3 → 19:08.6 · Fast stays 16:28.8."
- "SHARE and DON'T SHARE: 16 elements now belong to their branch (11 SHARE, 5 DON'T SHARE) and VO_37 gets its own anchor in DON'T SHARE (after VO_35c, as today). You see one branch at a time; DON'T SHARE runs 3.3 s shorter."
- "Stable names: the 592 prototype elements and 73 moments keep their ids for good, so a new guion.js can't rename an element or give its id to another clip."
- "APK baseline: the prototype schedule stored in the score becomes the APK baseline. ≠ APK marks: 0 → 0." (the live count)
- "Accepted problems: N records keep their value." (only when N > 0)
- Small print: "Other open editor tabs must reload after you save: an older editor can't save over a schema 3 score."

Buttons: **Upgrade (you can undo it)** (primary) · **Not now**. If the report has refusals: no primary button, the card lists what could not be classified.

### 10.4 Apply, undo, save
- `commit('Upgrade to schema 3', { type: 'migrate', ids: [] }, n => { replace n with report.next })`; `migrate` is in `Policy.QUIET` (its own card was the decision); undo/redo are the usual JSON snapshots (the whole score), so Ctrl+Z returns schema 2 exactly.
- Toast: "Upgraded to schema 3 · nothing moved for the typical user · save with Ctrl+S".
- Draft: the draft holds the schema-3 score; `restoreDraft` validates with `Edits.validate` (accepts 2 and 3).
- Save: normal PUT; server checks pass (schema up is allowed; S.SCHEMA.DOWN rejects the reverse). History keeps the schema-2 file.
- BroadcastChannel: the 3D tab receives the new score as with any edit.

---

## 11. Ordered implementation steps

Each step is independently implementable and leaves all tests green. "Tests" = new cases to add; the four existing suites must pass after every step (`node tools/score/edits_test.mjs`, `node tools/score/integrity_test.mjs`, `node tools/score/golden_test.mjs`, `python tools/editor/server_test.py`), plus `node --check` on every touched JS file. Browser checks: reload, `read_console_messages` without new errors, undo every test edit, reload at the end.

### Step 1 · Frozen fixtures; extract never writes the score (D4, A13)
- Files: `tools/score/extract_v1.mjs` (default `obra/score/score.extracted.json`, `--out`, `--fixture`, `--refreeze`, refuse score.json), `tools/score/fixtures/f0-score.json` + `f0-expect.json` (generated), `tools/score/golden_test.mjs` (fixture, 4-user totals, `--live` info), `tools/score/edits_test.mjs` + `integrity_test.mjs` (fixture by default, `--live`), `.gitignore` (ignore `obra/score/score.extracted.json`), `web/editor-obra/app/README.md` (Spanish neutro).
- Tests: golden 665/665 + totals 988.80/1017.9967/1085.28/1176.28 from the fixture; `extract_v1 --out obra/score/score.json` exits 2 and the file's mtime does not change; one edit to a copy of the live score does not change golden_test's exit code.
- Risk: low. The fixture must come from the extractor, not from copying the live score (they are equal today; later they would not be).

### Step 2 · Integrity in node + Policy extracted (D12 part 1)
- Files: `js/integrity.js` (UMD footer), new `js/policy.js`, `js/app.js` (`commit`, `reopen` call Policy; QUIET moves), `index.html` (script tag before app.js), `tools/score/integrity_test.mjs` (no window shim), new cases in `edits_test.mjs` or a `policy_test.mjs`.
- Tests: `require('integrity.js')` works in plain node; `Policy.decide` returns the same mode as today for: move VO keeping order (apply/info), move across moments (card), delete wired VO (card + reason), every QUIET op (quiet); `acceptRecords` keeps history and never deletes.
- Browser: one card edit + Accept anyway + undo behave as before.
- Risk: low-medium (central path); mitigated by a before/after replay of the integrity_test scenarios through `Policy.decide`.

### Step 3 · Engine v3 (D7, D8 core)
- Files: `js/engine.js` (`branch`, `alt`, `blocking`, `react`, reaction anchors, `off`, `crossBranch`, `reactive`; old evaluation order), `tools/score/golden_test.mjs` (4-user parity on f0), `tools/score/edits_test.mjs` (synthetic schema-3 mini scores).
- Tests: parity 0 diffs on f0 for 4 users (times + helpActive); synthetic: a non-blocking wait does not push for Idle; a reaction element follows Idle and does not extend its moment; branch filter excludes from moment end; alt anchor used only in its branch; cross-branch anchor reported; `'auto'` gives `onTimeout` for Idle.
- Risk: low if parity is enforced; the evaluation-order trap is the known danger.

### Step 4 · Schema 3 readable everywhere; baseline adapter (D4 part 2)
- Files: `js/edits.js` (`validate` 2|3 with schema-3 fields; `shiftBaseline`; `newId`), `js/integrity.js` (`divergent` reads `baseline.rel` or derives from `golden`), `js/app.js` (`compute` without `protoDiff`; `useRealLengths` uses `shiftBaseline` on `baseline` or `golden`; `importScore` accepts 3), `tools/editor/serve_editor.py` (`check_score` accepts 2|3, rejects schema down), `tools/editor/server_test.py`.
- Tests: `shiftBaseline` reproduces lote 3's claim (after real lengths, ≠ APK = 0) on a schema-2 and a migrated fixture (fake media lengths); validate rejects bad `branch`/`alt`/`blocking`; server: schema 3 PUT ok, schema-2 PUT over a schema-3 disk → 400.
- Risk: medium (two shapes coexist until the user upgrades).

### Step 5 · Migration operation (all four topics' data)
- Files: `js/edits.js` (`migrate3`, `MIGRATE3.waits`, branch classification table, postconditions), `js/importdiff.js` (only `recordOfScore`/`sigOf` needed for the seed; can land here or in step 10 with a stub), `js/app.js` (`Act.upgradeSchema`, C1.SCHEMA row), `js/ui.js` (Problems action), `README.md`.
- Tests (fixture): 665/665 typical after migration; totals table §1.2; 16 branches (11/5); VO_37 alt; `divergent` set unchanged; migrating a schema-3 score throws; an unknown `when` or wait refuses; `MIGRATE3.waits.blocking` equals the contract-derived value for the 10 waits; uidMap 592 + 73 with sig equal to the fixture extraction (592/592).
- Browser: Upgrade… card numbers match §10.3; apply; nothing moves (compare `App.schedT.t` before/after); Ctrl+Z returns schema 2; reload (draft equal to disk removed).
- Risk: medium. Needs steps 3–4 deployed first (an editor that cannot read schema 3 must never see one).

### Step 6 · Branches in the editor (D7 UI + rules)
- Files: `js/app.js` (`App.branchView`, `schedAlt`, preference, 3D `S.share` injection), `js/ui.js` (transport selector, dimmed off-branch clips, inspector Branch + "Anchor in DON'T SHARE"), `js/integrity.js` (per-branch pass, C1.BRANCH.*), `css/editor.css`, README shortcut/file tables.
- Tests (integrity_test, migrated fixture): DON'T SHARE total −3.25 s; anchoring a common element to VO_35b without alt → new block item; VO_35b/VO_35c never reported as overlapping; a DON'T SHARE overlap reported with "in DON'T SHARE".
- Risk: medium (UI). The default view (SHARE) keeps every number the user sees today.

### Step 7 · Waits UI and rules (D8 UI)
- Files: `js/ui.js` (reaction tail, inspector checkbox and labels, per-user table from `react`), `js/integrity.js` (C2.WAIT.WHERE on the flag, C3.BLOCKING, retire C3.NOTBLOCKING), `css/editor.css`.
- Tests: toggling G_BREATH to blocking → C3.BLOCKING warn + Idle total grows 19.0 s; Slow/Idle selection never changes `App.schedT`.
- Risk: low.

### Step 8 · Entering chain "Match Unreal" (D8 Entering)
- Files: `obra/unreal/contract.json` (entry `help.after`; editor-owned per LEEME), `js/integrity.js` (C3.KNOB.OFFSET reading `App.perillas`/partitura), `js/app.js` (`Act.matchKnobAnchor`), `js/ui.js` (Problems action).
- Tests: only VO_11h moves (237.1 typical), totals unchanged for 4 users, Slow help false, baseline rel of VO_11h updated so ≠ APK does not flag it; undo restores.
- Risk: low. Confirm the END-of-VO_11b reading with the Director first (§6.3).

### Step 9 · Accepted records with value (D11 rest)
- Files: `js/integrity.js` (fpBase/param, DIVERGE/VO.REAL params, matching), `js/policy.js` (records, reopen), `js/app.js` (DIVERGE lookup, card prefill data, Clean up), `js/ui.js` (Reopened text, prefill).
- Tests (audit D11 scenario): accept G_BELL drift at 30, set 300 → open with `was`; set back to 30 → accepted again; Reopen keeps the record (`state: 'reopened'`, history 2); DIVERGE accepted at one difference reopens at another; C2.TOTAL.GOAL band unchanged.
- Risk: low-medium (changes what is "accepted" for existing users; today 0 records).

### Step 10 · check.mjs and the server check (D12 part 2)
- Files: new `js/check.js`, new `tools/score/check.mjs`, `js/app.js` (`save()` runs `Check.invariants` first; 422 handling → Save a copy), `tools/editor/serve_editor.py` (node call, 422, fail-open, `VVR_NODE`, `VVR_CHECK`), `tools/editor/server_test.py`, README (Spanish neutro: how to run it, what 422 means).
- Tests (server_test on the temp copy): a new cycle → 422 and disk unchanged; the 2 known cycles → 200; dangling anchor → 422; duplicated id across beats/elements → 422; schema down → 422; `S.NODE = None` → 200 with `check: 'structural-only'`; check.mjs CLI exit codes 0/1/2.
- Risk: medium (save path). Mitigations: fail-open on infrastructure errors, `VVR_CHECK=off`, Save a copy always available.

### Step 11 · Import diff module + CLI (D2 part 1)
- Files: new `js/importdiff.js` (from the prototype, with renamed-moment ref normalization), new `tools/score/import_report.mjs`, new `tools/score/import_test.mjs`.
- Tests: generate the 4 scenario copies of `web/prototipo-narrativo` in `os.tmpdir()` (the original is only read), extract each, assert the rows of §1.5 (ghost: 1 added + 1 map update and `el_yjvsq81bml` still GHOST_BELL's cue; rename: 1 renamed; text: 2 changed; renum: beatRen + 2 map updates + 0 changes; base: 0 rows).
- Risk: medium (matching heuristics); limited by the cost threshold and by never auto-applying.

### Step 12 · "Changes in guion.js" panel (D2 part 2)
- Files: `tools/editor/serve_editor.py` (`POST /api/guion/scan`, runs the extractor to `score.extracted.json` only), `js/app.js` (verbs `import-add|rename|text|timing|map`, keep/dismiss), `js/ui.js` (panel), `css/editor.css`, README.
- Tests: server_test (scan writes only `score.extracted.json`; `score.json` mtime unchanged); edits_test for `applyImportRows` as a pure function in importdiff.js (anchors through uidMap, topological order, sig update).
- Browser: scan with today's guion.js → "No changes since the score took it"; with a scenario copy served through `VVR_PROTO`-style override (test only) → rows; apply Add → card → undo.
- Risk: medium-high (largest UI); can ship after everything else.

Dependency order: 1 → 2 → 3 → 4 → 5 → (6, 7, 8, 9 in any order) → 10 → 11 → 12. Steps 10 and 11 only need 5; 12 needs 11.

---

## 12. Decisions for the owner (Beltrán), with recommendation

1. **Reaction anchors** (§3.2.5): elements hanging from the end of a non-blocking wait (ghosts, BIO_ON, placement haptics) follow the simulated user and never lengthen the moment. *Recommend yes* (variant B): same totals as the simpler variant, and the Fast user's ghost disappears when they act instead of at the typical time.
2. **Default branch shown**: SHARE, with Auto (Idle → DON'T SHARE, as Unreal on timeout). *Recommend SHARE*; the typical numbers stay identical to today.
3. **Entering chain**: confirm with the Director that `HelpAfter` counts from the END of VO_11b, then offer it as Match Unreal (not inside the migration). *Recommend*: keep the migration timing-neutral; Entering as its own one-click change (Slow stops hearing VO_11h).
4. **Final branch divergences** (VO_36c/VO_36d no longer played by Unreal; DON'T SHARE without VO_35c, VO_37 at PT 8; SHARE VO_37 at VO_35b + 0.6): *recommend* listing them as C3 rows with Match Unreal after step 6, not in the migration.
5. **Guion timing changes**: shown in the panel but never applied by default (the DA rules timing). *Recommend*: per-row opt-in "Take guion's timing"; additions, renames and texts offered by default.
6. **Server check**: call node (no Python port), reject only NEW violations, fail open on infrastructure errors. *Recommend yes*; the 2 known cycles stay grandfathered until you pick their fix in Problems.
7. **Baseline inside the score** (not a separate file), changed only by explicit operations. *Recommend yes* (atomic undo/save).
8. **Author of acceptances**: keep the B/S switch now, or let the server sign (`git config user.name`). *Recommend* the server signature in a later lote (it matters for the F4 gate "accepted C3 need Beltrán's signature").
9. **The 17 edits of the old v78 artifact** (anexo 18 D4): never imported. *Recommend* dropping them: the score has been the timing source since F0 and nobody has asked for them; if any is remembered, it goes in as a normal edit.
10. **When to run the upgrade**: after steps 1–5 are in and with no other editor tab open. *Recommend* Beltrán presses Upgrade himself and saves; Narrativa/Director only need to know the file is schema 3 (they read `obra/unreal/`, not the score).
