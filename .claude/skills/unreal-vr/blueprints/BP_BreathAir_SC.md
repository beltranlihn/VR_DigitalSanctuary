# BP_BreathAir_SC — el ALIENTO VISIBLE de Entering

**Ruta:** `/Game/SoulCharger/Mechanics/Breath/Air/BP_BreathAir_SC` · malla `SM_BreathAir_SC` · material `M_BreathAir_SC` / `MI_BreathAir_SC` (misma carpeta)
**Colocado en:** `/Game/Test_Entering` como **`Entering_Aire`** (carpeta `Entering`), en (0, 0, 120) sin rotar = los ojos del usuario sentado sobre el `PlayerStart`.
**Estado (2026-09-28):** 🟢 construido (receta E1-E14 del plan) · 🟢 **PIE verificado** (T1-T8, abajo) · 🟢 Simulate limpio · ⬜ banco del aire en PIE (`PerfMode` no se puede forzar desde el MCP, ver "Trampas del instrumento") · ⬜ APK, banco en la Quest y visor (fase S: con Beltrán) · ⬜ sin commitear (la carpeta `Mechanics/Breath/Air/` y el nivel están **sin versionar**).
**Plan (fuente de verdad):** [`docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md`](../../../../docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md) — §2 arquitectura, §3 señales, §4 el efecto, §5 assets/parámetros/grafos (tablas 5.3, 5.4, 5.5, 5.6), §11 receta del editor, §15 qué cambió en la rev. 2.

## Qué es
Pedido de Beltrán (directiva): *"cuando inhalas entren partículas muy pequeñitas y suaves y cuando exhales que salgan partículas de tu boca… attached a la cabeza del pawn para que si muevo la cabeza sigan entrando a mi boca"*.
- 2048 quads (768 inhalar, 1280 exhalar) en UNA malla, un draw call, cero CPU por mota (receta de `SM_LovingDust_SC`, gotcha 477). El vertex shader calcula cada mota sin estado a partir de sus semillas (UV1-UV3) y de 8 vectores que empuja el BP.
- Inhalar: las motas se juntan de costado hacia un **foco** (~40 cm, ~25° bajo la mirada; Bézier con `InFocus`) y de ahí bajan a la boca ya apagadas. Exhalar: la pluma sale de la boca y pasa **por debajo** del metaball (`OutTilt` 18).
- **Actor propio colocado en el nivel** (no dentro del rig: el rig está validado en visor y no se toca). Toma la cámara del pawn de `BP_BreathRig_SC.CamRef` (el único que conoce al pawn) y cuelga `AirMesh` de ella con `SnapToTarget`: el local de `AirMesh` = el de la cámara.
- Lee **solo `MPC_Breath`** (`Signed`, `On`): la velocidad de la respiración es `dS/dt` de `Signed`, con tope y solo con detección, filtrada (`VelTau`); el modo inhalar/exhalar/pausa tiene **histéresis** (`VelEnter`/`VelStay`). El ritmo cuenta un inicio de exhalación solo después de una inhalación sostenida (`InhMin`). La presencia se suaviza (`GlobTau`): el `Retire` del rig no apaga el aire en un cuadro. Al **girar la cabeza** el aire se apaga (`TurnFade0/1`) y reaparece en su lugar.
- En el editor, sin Play: el actor colocado a la altura de los ojos ES la cabeza; `PreviewBreath`/`PreviewAirT` muestran la inhalación o la pluma. `HeadGhost`/`MouthGhost` = cabeza de referencia (ocultos en juego; **no** `bIsEditorOnly`, porque `AirReset` los toca en el APK).

## Componentes
| Componente | Qué | Notas |
|---|---|---|
| `DefaultSceneRoot` | raíz | el actor queda en (0,0,120); `AirMesh` se despega de él al montar |
| `AirMesh` | `SM_BreathAir_SC` + `MI_BreathAir_SC` | sin colisión (`BodyInstance` NoCollision los dos campos), sin sombra, `translucencySortPriority` **20** (verificado 20 en la instancia de PIE). En PIE cuelga de `BP_VRPawn_SC_C_0.Camera` (verificado con `get_parent_component`) |
| `HeadGhost` | esfera (−8,5, 0, 2,5), escala (0,21, 0,19, 0,23) | `bHiddenInGame`; solo referencia de autoría |
| `MouthGhost` | esfera en (6, 0, −9), escala 0,02 | idem; marca la boca por defecto |

## Registro de variables
**`A-Aliento` (instance-editable; defaults = tabla 5.4 del plan):**
| Variable | Default | Rol / qué palanca es |
|---|---|---|
| `bAir` | true | apaga el aliento entero (la presencia cae con `GlobTau`; con `Glob` < 0,0005 el componente se oculta: **medido en PIE, 3,8 s**) |
| `AirAmount` | 1 | intensidad global; 0 = apagado (A/B, botón de pánico) |
| `MouthFwd` / `MouthDown` | 6 / 9 cm | la boca en el local de la cámara (mover `MouthGhost` a mano si se cambian) |
| `InTravel` / `OutTravel` | 0,9 / 0,8 | cuánto del camino recorre una inhalación / exhalación completa (sea rápida o lenta) |
| `FrontLead` | 1,6 | qué tan rápido se despliega la pluma desde la boca |
| `LagPos` / `LagRot` | 0,3 / 0,8 s | retardo del marco del aire (posición / giro) |
| `HoldLagMul` | 3 | en las pausas el marco sigue a la cabeza 3× más lento |
| `PitchFollow` / `PitchMin` / `PitchMax` | 0,75 / −35 / 10 | cuánto sigue el aire al cabeceo y sus topes (decisión 7) |
| `RiseTau` / `HoldTau` / `CrossTau` | 0,3 / 2,5 / 0,5 s | envolventes: aparece / queda suspendida en la pausa / se apaga cuando empieza la otra corriente |
| `VelTau` | 0,15 s | pasabajos de la velocidad (más = pausas más quietas con ruido, más latencia) |
| `VelEnter` / `VelStay` | 0,10 / 0,04 1/s | histéresis del modo. **Regla del visor (S3):** `VelEnter` ≥ 3 × std(v en la pausa real), `VelStay` ≈ 0,4 × `VelEnter` |
| `VelMax` | 2 1/s | tope de la velocidad (un escalón de la señal no dispara la cinta) |
| `InhMin` | 0,6 s | latch del ritmo |
| `FastFloor` / `CalmRate` / `FastRate` | 0,5 / 10 / 16 resp/min | atenuación por respiración rápida (`RateCalm`) |
| `GlobTau` | 0,5 s | cómo sigue la presencia a la detección y al ritmo |
| `TurnFade0` / `TurnFade1` | 6 / 20 °/s | apagado por giro de cabeza |
| `TurnBack` | 0,6 s | cómo reaparece después del giro |
| `TurnCatch` | 0,25 | mientras está apagado por el giro, el marco alcanza a la cabeza 4× más rápido |

**`B-Prueba` (instance-editable):** `PreviewBreath` 0 (−1…1; > 0 inhalar, < 0 la pluma, **0 = no dibuja nada**) · `PreviewAirT` 0,35 (arrastra la cinta). 🔴 Antes del cook: `PreviewBreath` 0 en el CDO **y** en la instancia (hoy: 0 y 0).

**`Z-Aliento` (estado, NO editable — 🔴 `set_properties` no los puede escribir ni en PIE):** `Tin`/`Tout`/`Fout` (fases integradas y frente de la pluma) · `Ein`/`Eout` (envolventes) · `InRate`/`OutRate` · `Vel`/`VelF`/`Sprev`/`bPrimed` · `Flow` (+1/0/−1) · `InhHold` · `Clock`/`bOnset`/`Per`/`LastOnset`/`RateBpm`/`RateCalm` (ritmo; `Clock` = segundos de juego, sirve de sello de tiempo para las lecturas) · `MouthW` · `YawLag`/`PitchLag`/`YawPrev`/`PitchPrev`/`bLagInit` · `TurnRate`/`MoveFade` · `GlobBase`/`Glob` · `CamXf` (transform de `AirMesh` del cuadro: **es la forma de leer desde afuera dónde está montado el aire**) · `bMounted`/`Rig` · `PerfMode` (0 normal · 1 oculto · 2 lleno) · `AirSig`/`AirGate` (lo leído de `MPC_Breath` este cuadro).
Nombres de propiedad para `get_properties`: camelCase (`glob`, `moveFade`, `rateBpm`, `camXf`, `airSig`…), los bool con su `b` (`bMounted`).

## Estructura de grafos (texto exacto: `scripts/breath_air.dsl`)
- **EventGraph:** `BeginPlay` → `AirReset` + `AIRE: listo, espera la camara de BP_BreathRig_SC` · `Tick` → `AirTick(DT)` · eventos de banco `PerfE0` (eco `PERF: entering modo 0`), `PerfE1..4` (normal, sin eco), `PerfE5` (lleno, eco), `PerfE6` (oculto, eco) · `AirDbg` (una línea `AIRE DBG v … modo … S …`).
- **`AirTick(DT)`:** `AirMPC` → `AirStep(DT)` → `AirPerf` → `PushAir` → `AirVisible` → si no `bMounted`: `AirMount`.
- **`AirMPC`:** dos `GetScalarParameterValue` de colección (`Signed`, `On`) → `AirSig`, `AirGate` (puente por cirugía, gotcha 291).
- **`AirStep(DT)`:** = `AirBP.step` del modelo: velocidad con tope (solo con `On` > 0,05) → `VelF` → modo con histéresis → ritmo con latch → transporte de `Tin`/`Tout` solo en su modo → frente `Fout` → envolventes → marco con retardo (los Set del marco ANTES de `SetMoveFade`: `_k` usa el `MoveFade` viejo) → `TurnRate` → `MoveFade` → `Glob`.
- **`AirPerf`:** `PerfMode` 2 → `Glob`, `Ein`, `Eout` = 1 y `Fout` = 1,5.
- **`PushAir`:** `CamXf` una vez; los 8 vectores (`AirT`, `AirE`, `MouthL`, `LagM`, `LagA`, `LagR`, `LagU`, `UpL`) en local de la cámara, en la MISMA función (gotcha 465).
- **`AirVisible`:** `SetVisibility(AirMesh, PerfMode ≠ 1 ∧ (Glob > 0,0005 ∨ PerfMode = 2))`.
- **`AirMount`:** `bind GetActorOfClass(BP_BreathRig_SC)` → `SetRig` → si válido `AirMountCam`. Corre cada cuadro hasta montar.
- **`AirMountCam`:** `GetCamRef(Rig)` → si válida: `AttachComponentToComponent(AirMesh, cam, Snap×3)` + `AddTickPrerequisiteActor(Rig)` + `bLagInit` false + `bMounted` true + `AIRE: montado en la camara del pawn (CamRef de BP_BreathRig_SC)`.
- **`AirReset`:** estado inicial en 0, oculto, sin colisión, fantasmas ocultos.
- **`PreviewAir`** (CS): con `PreviewBreath` ≠ 0 empuja una corriente llena con la cinta en `PreviewAirT`; con 0, `Glob` 0.
- **Construction Script:** sort 20 (red de seguridad, gotcha 478) + `PreviewAir`.

## Verificado en PIE (2026-09-28, fase T del plan) — evidencia en `VR_Test/Saved/ClaudeScripts/capa_viva/pie/`
Condiciones: `/Game/Test_Entering`, PIE en el viewport, en la instancia de PIE `bFakeBreath` = true en el rig (`FakePeriod` 6 s = 10 resp/min) y `Cycles` = 0 en el pacer (infinito, lo mismo que hace `PerfELoop`) para que la etapa no retire el rig durante la prueba. Nada de eso tocó las instancias del editor (verificado después: `bFakeBreath` false, `Cycles` 5).
- **Montaje:** `AIRE: listo` → `AIRE: montado…` **una vez** por sesión, 1,4 s después (cuando la etapa activa el rig); `bMounted` true; `AirMesh` hijo de `BP_VRPawn_SC_C_0.Camera`. Cero `Accessed None` y cero errores de runtime en las dos sesiones de PIE.
- **Modo y transporte** (traza por cuadro de 11 s, `t4_traza_12s.json`): `Flow` alterna −1 (2,6-2,9 s) → 0 (0,07-0,08 s) → +1 (2,85 s) → 0 → −1, período 6,0 s. `Tin` avanza **solo** inhalando (Δ máx fuera de inhalar 0,0003 = el cuadro del cambio) y `Tout` solo exhalando; una inhalación completa mueve `Tin` ~0,88 (≈ `InTravel` 0,9). La respiración falsa es una senoide: casi no tiene retención, así que "quieto en la pausa" se verificó como "quieto fuera de su modo"; la pausa larga con ruido real es la prueba S3 del visor.
- **Ritmo:** `RateBpm` 9,86 → 9,999 (real 10) en ~6 ciclos; `RateCalm` 1.
- **Presencia:** `Glob` = `GlobBase` = 1,0 con detección; `bAir` false → `Glob` cae con τ 0,5 s (0,0097 a los 2,35 s) y **`AirMesh.bVisible` pasa a false a los 3,84 s** (`Glob` 0,0005); `bAir` true → visible el cuadro siguiente y `Glob` 0,98 a los 1,9 s (`t6_bAir_off_on.json`).
- **Giro de cabeza** (el pawn entero girado con `ActorTools.set_actor_transform` en el mundo de PIE, un salto en un cuadro; trazas por cuadro `t5_giro_pitch20.json`, `t5_giro_yaw30.json`): cabeceo −20° → `MoveFade` 0 en el mismo cuadro (`TurnRate` 1200 °/s), 0,5 a los 0,77 s, 0,9 a los 1,73 s. **Giro de 30° en yaw** → `MoveFade` 0 en el mismo cuadro (`TurnRate` 1800 °/s), `YawLag` alcanza 29,6° a los 1,37 s, `MoveFade` **0,5 a los 0,93 s, 0,76 a los 1,37 s, 0,9 a los 1,90 s**. Es lo que da la cuenta con `TurnCatch` 0,25 y `TurnBack` 0,6 para un salto instantáneo (el "~1,1 s" del plan es para un giro de cabeza real, no un salto). `AirMesh` sigue colgado de la cámara después del giro.
- **Lo que ve el juego** (`CaptureEditorImage` del viewport de PIE, `t5_comparativa.png`): cámara 20° abajo. Inhalando (`Flow` +1, `VelF` 1,04, `Ein` 0,97): motas tenues en la franja baja, repartidas a los dos lados. Exhalando (`Flow` −1, `VelF` −1,05, `Eout` 0,97): la pluma de motas tibias centrada en la mitad baja. 1,37 s después del giro de 30°: las motas de inhalar vuelven abajo al centro. Las dos barras color crema verticales de las capturas son **los mandos/sensores del rig** (color `SensorColor` × `CtrlBrightness`: (255, 244, 213) en la captura), que en PIE sin tracking quedan en el origen del pawn, junto a la cámara; no son del aire.
- **Simulate** (sin pawn): `AIRE: listo`, **nunca** `montado`, `bMounted` false, `Glob` 0, `AirMesh` oculto, cero `Accessed None`.
- **No verificado en PIE:** `PerfE0/E5/E6` y `AirDbg` (el MCP no manda comandos de consola, gotcha 441; y `PerfMode` no es editable, así que `set_properties` lo rechaza). Se prueban en la Quest con `quest_entering_perf.ps1 -Modos 0,4,5,6` (S2) y `ke * AirDbg` por adb (S3).

## 🔴 Trampas del instrumento (aprendidas en la fase T; gotcha 488)
- **No rotar la cámara del pawn de PIE con `set_properties`** (la receta T5 original): cada escritura sobre un componente del pawn re-corre su Construction Script (el rig vuelve a loguear `BREATH: listo (camara + manos del pawn)`) y los componentes de OTROS actores colgados de la cámara se despegan: `AirMesh` quedó con padre `null` y su `CamXf` congelado, mientras la vista sí giraba. Para girar la cabeza en PIE: **`ActorTools.set_actor_transform` sobre el pawn** (`worldspace` true), que en PIE sí funciona y no re-construye nada.
- **Dentro de un `execute_tool_script`, cada `execute_tool` consume un cuadro de juego** (el `Clock` avanza 1/60 s por llamada): se pueden sacar trazas por cuadro (setear y leer 120 cuadros seguidos) sin la latencia de ~1,5 s entre llamadas sueltas.
- `set_properties` en PIE solo escribe variables instance-editable: `bMounted`, `PerfMode` y el resto de `Z-Aliento` responden *"could not be set"*.

## 🔴 Trampas de construcción que la rev. 2 ya esquiva (no deshacer)
- **Semillas invariantes a la V invertida** del importador FBX (gotcha 302): la bandera de corriente va en U (UV3.x), `b` va como `(b + 1)/2` en UV2.y y el VS la decodifica.
- **`GetActorOfClass` es impuro:** `(bind _found …)` y después `SetRig _found`. Inline en el Set deja el pin desconectado sin error.
- **`_k` (el paso del marco) usa el `MoveFade` VIEJO:** en `AirStep` los Set del marco van ANTES de `SetMoveFade`.
- `Set…ParameterValueonMaterials` con "on" minúscula (gotcha 2258).

## Archivos (en disco)
| Archivo | Qué |
|---|---|
| `scripts/breath_air_model.py` | Modelo de referencia: VS, PS, `AirBP` (el BP), preview, seguidor del rig, `encode_uv`/`decode_uv`/`flip_v`, `BellyNoisy` |
| `scripts/hlsl/BreathAirVS.hlsl`, `BreathAirPS.hlsl` | Los dos Custom (VS: 45 entradas) |
| `scripts/hlsl/BreathAir_check.py` | dxc/fxc/SPIR-V, HLSL = modelo, confort, neutro, 13 mutaciones, V invertida |
| `scripts/gen_breath_air.py` | Malla (Blender headless) → `Saved/ClaudeScripts/aliento/SM_BreathAir_SC.fbx` |
| `scripts/plan_breath_air_material.py` → `apply_breath_air_material.py` | Armado del material por MCP (idempotente; 41 parámetros) |
| `scripts/breath_air.dsl` | Los grafos del BP |
| `scripts/dsl_sim.py aire` | Ejecuta el DSL y lo compara con el modelo |
| `scripts/sim_breath_air.py` | Confort, señal real, ritmo, giro, legibilidad, costo y previsualizaciones |
| `Saved/ClaudeScripts/capa_viva/aliento/e14_comparativa.png` | Vista previa del editor desde el ojo (E14): inhala / exhala / neutro |
| `Saved/ClaudeScripts/capa_viva/pie/` | Fase T: lecturas, trazas por cuadro y capturas del juego |

## Banco y depuración
`ke * PerfE5` = aire lleno · `PerfE6` = sin aire · `PerfE0` = normal (ecos `PERF: entering modo N`). `scripts/quest_entering_perf.ps1 -Modos 0,4,5,6` → **aire = m5 − m6** (medido con el valle oculto: `BP_PerfEntering_SC` no tiene `PerfE5/E6`). `ke * AirDbg` → una línea `AIRE DBG v … modo … S …` (ruido real en el visor, plan §8).

## Session log
- **2026-09-28 (rev. 2, disco):** modelo, HLSL, malla, scripts, DSL, verificadores.
- **2026-09-28 (fases E y T, editor):** assets, material, BP y actor `Entering_Aire` (E1-E14, evidencia en `capa_viva/aliento/` y `capa_viva/verif_aliento/`); PIE, giro, presencia y Simulate (T1-T8, arriba). Los BP ensuciados por `read_graph_dsl` (gotcha 487) se compilaron (`warnings_as_errors`, sin errores) y se guardaron con ruta explícita antes del PIE.

## TODO
- [ ] **S1-S3 con Beltrán:** APK Development, banco (`-Modos 0,4,5,6`: FONDO = m0 − m4, AIRE = m5 − m6), visor: primero el ruido real con `ke * AirDbg` (retención y balanceo sin respirar), después `AirAmount` 0,3 → 1.
- [ ] Si la pausa "respira" con el ruido real: `VelEnter`/`VelStay`/`VelTau` en la instancia (regla de §3 del plan).
- [ ] Decisiones de §14 del plan (dónde vive, pluma bajo el metaball, `PitchFollow`, colores).
- [ ] Commit (con permiso): `Mechanics/Breath/Air/` y `Test_Entering.umap` están sin versionar.
