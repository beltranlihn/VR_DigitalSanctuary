# BP_ValleyLife_SC — la CAPA DE VIDA del valle de Entering (polvo + ráfagas)

**Ruta:** `/Game/SoulCharger/Mechanics/Breath/Life/BP_ValleyLife_SC` (construido y guardado 2026-09-29) · malla `SM_ValleyDust_SC` · material `M_ValleyDust_SC` / `MI_ValleyDust_SC` · sonidos `Life/Audio/SND_VidaGustA/B/C`, `SND_VidaSoplo` · + 1 Custom (`GustLeanVS`) y 5 parámetros (`Gust*`) en `M_BreathValley_SC`.
**Se coloca en:** `/Game/Test_Entering` como **`Entering_Vida`** (carpeta `Entering`), en (0, 0, 120) sin rotar = los ojos del usuario sentado.
**Estado (2026-09-29):** 🟢 **construido** (receta §13 fases P/M/A hechas antes; **B1-B13 hechos**, B14 no hizo falta) · compile `warnings_as_errors` **0 errores / 0 warnings** · guardado (`is_dirty` false) · ⬜ C (colocar `Entering_Vida` + vista previa) · ⬜ PIE (T) · ⬜ APK, banco, visor · ⬜ sin commitear.
**Receta que funcionó (de corrido, ~25 min):** `VR_Test/Saved/ClaudeScripts/vida/receta_bp_rapida.md` + los scripts `vida/bp/*.py`.
**Plan (fuente de verdad):** [`docs/PLAN-VIDA-VALLE-2026-09-28.md`](../../../../docs/PLAN-VIDA-VALLE-2026-09-28.md) — §3 arquitectura, §4 ráfagas, §5 polvo (tablas 5.2, 5.3 juegos visible/sutil, 5.4, 5.5, 5.6), §6 la franja del valle (tabla 6.3), §7 sonido, §13 receta, §16 qué cambió en la rev. 2.

## Qué es
Pedido de Beltrán: *"le falta algo para que se sienta un poco más vivo… partículas muy pequeñas tipo polvo o ráfagas como un poco de viento"*.
- **UN solo reloj de ráfagas** (`VidaSchedule`): el frente `s`, la trayectoria, la envolvente y la deriva `Hold` alimentan en el mismo cuadro el polvo, la franja del valle y la fuente de sonido.
- **Polvo:** 2048 quads en su lugar (1536 de base **1,3-36 m** + 512 que solo levanta la ráfaga), meandro integrado (más amplio lejos), dispersión hacia adelante contra el resplandor (dorado / blanco lavanda: **no** la paleta del aliento), lazo al paso del frente + **deriva a favor del viento que vuelve** en `DriftRelax` s. Nada a < 1,2 m de los ojos (el volumen del aliento es suyo). El alfa se decide desde el **punto ciclópeo** (la cámara del rig): igual en los dos ojos.
- **Ráfagas laterales** (autorales) cada ~40-70 s y **soplos** (con respiración detectada, uno de cada dos: salen del usuario con el inicio de la exhalación; el sonido del soplo va arriba del tono del pacer).
- Lee `MPC_Breath` y `BP_BreathRig_SC.CamRef`; busca (opcionales, `IsValid`) `BP_BreathValley_SC` (para la franja), `BP_BreathBlob_SC` (despejar su disco) y `BP_BreathRig_SC` (tickear después de él, punto ciclópeo). No toca el rig, el aliento, el metaball ni el BP del valle.
- **Default = juego VISIBLE**; el sutil (la rev. 1) en la tabla 5.3 del plan, para bajar mirando en el visor.

## Archivos (en disco)
| Archivo | Qué |
|---|---|
| `scripts/vida_model.py` | modelo de referencia (VS, PS, GustLeanVS, `VidaBP`, `PRESET_SUTIL*`) |
| `scripts/hlsl/DustVS.hlsl` (38 entradas), `DustPS.hlsl`, `GustLeanVS.hlsl` + `Vida_check.py` | los Custom y su verificador (69/69) |
| `scripts/gen_valley_dust.py` | la malla → `Saved/ClaudeScripts/vida/SM_ValleyDust_SC.fbx` |
| `scripts/plan_vida_materials.py` → `apply_vida_dust_material.py`, `apply_vida_gust_valley.py`, `rollback_vida_gust_valley.py` | armado por MCP (idempotentes) · `vida_dryrun.py` (27/27) |
| `scripts/vida.dsl` (37 funciones + CS + EventGraph) + `vida_dsl_sim.py` | los grafos y su simulación (36/36) |
| `scripts/make_vida_sounds.py` | los WAV (28 s / 18 s) → `Saved/ClaudeScripts/vida/audio/` |
| `scripts/sim_vida.py`, `render_vida_valle.py`, `vida_legibilidad.py` | mediciones, previsualizaciones, cuántas motas se distinguen en la foto |

## Trampas que el diseño ya esquiva (no deshacer)
- La esquina del quad va en la **U** de UV0 (con la V invertida los 4 vértices recuperan el mismo centro); los enteros en U (las UV son fp16).
- El frente arranca en `e0 − 2W` y termina en `e1 + 2W`; el lazo es polinómico: 0 exacto en las puntas.
- **`Amp` NO se apaga al terminar el frente**: se apaga cuando la deriva (`Hold`) llegó a 0 en `VidaRelaxStep`. Apagarla antes hace saltar las motas hasta 1,8 m (control negativo de `vida_dsl_sim.py`).
- La franja recibe `GustK` = 0 fuera del paso del frente (`select bGusting`), también durante la relajación.
- `VidaMaybe` exige `bVida` y `VidaAmount` > 0: el pánico corta las ráfagas nuevas.
- `bGusting`, no `bGustOn` (el getter sería `GetGuston`); `bForce` → `GetForce`.
- `GetActorOfClass` con `bind` y después `Set`; `if`/`IsValid` al final de cada lista (por eso las funciones chicas: `VidaCamRig` → `VidaCamC`, `VidaRelax` → `VidaRelaxStep`).
- `AddTickPrerequisiteActor(rig)` solo en `BeginPlay` (`VidaAfterRig`), nunca en el Construction Script.
- `VidaSnd` se arma **por cirugía** (los nodos de audio resuelven al homónimo de `SynthComponent`, `BP_Sequencer_SC.md`).
- La franja NO toca `ValleyGradVS`: si alguien re-pega `apply_valley_material_B.py` la franja se apaga (neutro) → volver a pegar `apply_vida_gust_valley.py`; los `Gust*` que `apply_valley_material_A.py` lista como sobrantes NO se borran.
- Banco: `PerfE0..E4` = sin ráfagas (modo 3), `PerfEEnd` = normal; antes de `PerfValley1/3`, `ke * PerfV1`.
- Si `GustLife`/`BreathLife` cambian más de ~15 %: regenerar los WAV (el pitch cambia el timbre).

## Construido (fase B, 2026-09-29): lo que difiere del plan
**Componentes (plantillas `<Comp>_GEN_VARIABLE`, verificado con `get_properties`):** `DustMesh` = `SM_ValleyDust_SC` + `MI_ValleyDust_SC`, `BodyInstance` NoCollision/NoCollision, `castShadow` false, `translucencySortPriority` 5, `bReceivesDecals` false · `GustAudio` `bAutoActivate` false, `bOverrideAttenuation` true, **`AttenuationOverrides` escrito como texto** (`bAttenuate` false, `bSpatialize` true) → **B14 NO hizo falta**, `bAllowSpatialization` true.
**Variables:** 90 (45 editables en `A-Vida` 5 · `B-Rafagas` 21 · `C-Soplo` 10 · `D-Sonido` 6 con los 2 arrays · `E-Prueba` 3; 45 de estado en `Z-Vida`). Creadas SIN categoría y categorizadas después (gotcha 296). Defaults del CDO = tabla 5.4, verificados uno por uno (claves camelCase: `vidaAmount`, `gustSounds`…; bools con `b`). `GustSounds` = A, B, C; `BreathSounds` = Soplo.
**type_ids (B9):** todos los de la lista existen exactamente una vez; **ninguno cambió de nombre**. `Utilities|IsValid` aparece 3 veces (normal).
**Cambios en `scripts/vida.dsl`** (la semántica es la misma; `vida_dsl_sim.py` TODO OK, y ahora con `lint_editor`, gotcha 490):
- `VidaStartLat`: `OrgW` y `SndOffW` **por componentes** con `_cy`/`_sy` = cos/sin del yaw (antes `(* _F _m)` y `(* _F (- SndFwd _m))`: *"Could not connect pin ReturnValue to B"*).
- `VidaState`: el punto 2 m delante por componentes (`_rx`/`_ry` directos), sin `(* vector 200.0)`.
- `VidaPushValley`: la inclinación `_ln` por componentes (`_gl` × cos/sin de `LeanAz`).
- `VidaAudio`: la ubicación de la fuente por componentes (`_o`, `_q`, `_d`, `_f`), sin cadenas de `+` vectoriales.
- `VidaDue`: **un solo `elif` por `if`** → `(if (not _quiere) Lat (else (if ExhOnset Breath (elif (< Wait −BreathWait) Lat))))`.
**Cirugías:** B11 `VidaMPC` (dos `GetScalarParameterValue` de `KismetMaterialLibrary` → `K2Node_CallMaterialParameterCollectionFunction`, `Signed`/`On`, entrada → Get → Get → SetVSig → SetVGate) · B12 `VidaSnd` (4 nodos de `AudioComponent` + `GetGustAudio` + `GetGustVolume` + `CallFunction|VidaAudio`; exec entrada → SetSound → SetPitch → SetVolume → VidaAudio → Play; `StartTime` 0) · EventGraph: borrados los 3 eventos fantasma antes del write.
**Verificado tras escribir** (`get_node_infos` de todo el BP, 1021 nodos): cada `|VidaX` con argumentos tiene el argumento conectado o su literal y `self` = Self; `SetValley/SetBlob/SetRig` con el valor conectado; `GetGround.self` ← `GetValley`; `GetCamRef.self` ← `GetRig`; `AddTickPrerequisiteActor.PrerequisiteActor` ← `GetRig`; 15 eventos en el EventGraph sin duplicados; ningún `ToString` intruso ni nodo de `SynthComponent`. Log del compile final: solo `Compiling Blueprint`, ningún error ni warning; ningún `Undo` en el log de toda la sesión; canario `Test_Entering` 16 en todas las tandas.
**Nodos por grafo:** `VidaState` 147, `VidaBreath` 83, `VidaStartLat` 82, `VidaPushValley` 65, `EventGraph` 49, `VidaZero` 48, `VidaPushDust` 45, `VidaRelaxStep` 44, `VidaStartBreath` 43; el resto < 32.

### 🔴 El crash de las 00:22 (2026-09-29)
La primera construcción (B1-B4 completos + 5 grafos escritos) **se perdió entera**: el editor cayó con un crash de GPU (`DXGI_ERROR_DEVICE_REMOVED`) mientras compilaba, y el BP **nunca se había guardado** (la receta del plan solo guardaba en B13). Lo que cambió en la reconstrucción: `save_assets` con la ruta del BP justo después de crearlo, después de componentes+variables, después de cada compile limpio y después de cada tanda de grafos (8 guardados); compilar solo cuando hace falta (3 `compile_blueprint` explícitos: tras las variables, tras las funciones y el final; los `write_graph_dsl` compilan solos). No se sabe si el compile causó el crash o solo coincidió (la GPU también dibuja el viewport); no hubo otro crash en la reconstrucción.

## TODO
- [x] Fase B (B1-B13; B14 no hizo falta).
- [ ] Fase C (colocar `Entering_Vida`, diff instancia vs plantilla en `DustMesh`/`GustAudio`, gotcha 478; vista previa) y T (PIE), con Breath.
- [ ] Actualizar `_INDEX.md`, `BP_BreathValley_SC.md`, `Valley_CABLEADO.md`, `assets-existentes.md`, `MECANICAS-PORTABLES.md` al cerrar C/T.
- [ ] Visor con Beltrán (§13 S3: visible → bajar mirando; el soplo con el pacer sonando) y banco (`PerfV0/1/2`).
- [ ] Decisiones §15 del plan.
