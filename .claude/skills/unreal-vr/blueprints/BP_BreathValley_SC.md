# BP_BreathValley_SC — el valle de colinas de Entering

**Ruta:** `/Game/SoulCharger/Mechanics/Breath/Blueprints/BP_BreathValley_SC`
**Estado (2026-09-28): v2 APLICADA** en `/Game/SoulCharger/Mechanics/Breath/Maps/Test_Breath` (`Entering_Valle`, carpeta `Entering`) · 🟢 PIE (sombra sigue al metaball, cero errores) · 🟢 movimiento medido en el editor · 🟢 **capa viva aplicada** (fases V del plan de respiración) y **verificada en PIE** (`LiveS` sigue a la respiración, ver la sección 🫁) · ⬜ visor · ⬜ medido en la Quest · ⬜ sin commitear (la carpeta `Valley/` y el nivel están sin versionar).
**Spec completa (v2: geometría, altura, oleaje, sombreado, niebla, cielo, 71 parámetros, valores de control, costo, riesgos):** [`docs/PLAN-VALLE-ENTERING-2026-09-27.md`](../../../../docs/PLAN-VALLE-ENTERING-2026-09-27.md) — la sección "v2" de arriba tiene la devolución de Beltrán y las decisiones.

## Qué es
El entorno de la etapa de respiración: un gran llano mate donde el usuario está sentado, el metaball enfrente con una **sombra falsa** en el piso (para que se lea flotando), y colinas en dos capas lejanas (45-260 m y 280-590 m, siluetas a ~90-520 m) que se pierden en una niebla por distancia + de altura hacia el color del cielo. Cielo analítico con resplandor rosa y luna tenue. **Movimiento:** un oleaje de 4 ondas largas (100-225 m, períodos de 31-46 s) que mueve la GEOMETRÍA solo de la capa lejana (desde 280 m) y en el llano viaja solo como LUZ (`SwellShade`: la normal se inclina, la altura no cambia, así el llano no puede ocultarse a sí mismo ni dibujar líneas); las colinas medias respiran suave (`MorphAmt` 0,15). El piso es exactamente 0 y quieto hasta 15 m. Reemplaza al `Entering_Fondo` (Ganzfeld liso), que quedó **oculto, no eliminado**.

### Historia
- **v1 (2026-09-27):** valle elíptico de 19×12 m, lomas de 5 m, malla de 44 m, morph solo de amplitud (41-83 s). Beltrán: *"debe ondular, no lo veo moverse; es muy chico, que las colinas estén lejanas, algo de fog; se ve muy marcada la línea donde se acaba el plano"*. La línea era el borde de la elipse del piso plano, donde nacían las colinas (quiebre de pendiente). Respaldo en `Saved/ClaudeScripts/valle_v1_backup/`.
- **v2 (2026-09-28):** workflow `valle-v2` (3 diagnósticos → construcción → 4 verificadores → corrección). La primera versión movía el llano con el oleaje y creaba bordes de autooclusión rectos (otra "línea"): se corrigió pasando el oleaje del llano al sombreado. Respaldo de la v2 sin corregir en `valle_v2_backup_pre_correccion/`.

## Assets (carpeta `Mechanics/Breath/Valley/`)
| Asset | Qué |
|---|---|
| `SM_BreathValleyV2_SC` | **La malla en uso.** Disco polar de `gen_breath_valley.py` v2: 144 sectores × 150 anillos = 21.601 vértices / 43.056 triángulos, radio 640 m (60 cm hasta 10,8 m, celdas cuadradas hasta 60 m, aspecto 0,6 hasta 590 m). `PositiveBoundsExtension` (0,0,19000), `NegativeBoundsExtension` (0,0,4000). Se importó con nombre nuevo para no sobrescribir |
| `SM_BreathValley_SC` | Malla v1 (15.169 vértices, 44 m). **Ya no se usa**; borrarla solo con permiso |
| `M_BreathValley_SC` | Unlit, opaco, two-sided, `MFPM_Full_MaterialExpressionOnly` (no se puede bajar: `Dist` del cielo pasa de 100.000 cm). Tres Custom: `ValleyHeightVS` (29 entradas → Transform Local→World → WPO), `ValleyGradVS` (31 → `VertexInterpolator_0`), `ValleyPS` (44 → Emissive; `Part` 0 suelo / 1 cielo). 71 parámetros. Fuente en `scripts/hlsl/Valley*.hlsl`, modelo `scripts/valley_model.py`, verificador `scripts/hlsl/Valley_check.py`, cableado `Valley_CABLEADO.md`; plan con `scripts/plan_valley_material.py` → `Saved/ClaudeScripts/valley_build.json` |
| `MI_BreathValley_SC` | Base, **sin overrides** (se limpiaron el 2026-09-28 16:10: el look ahora se ajusta en las **perillas del BP**, ver abajo). Historia: la niebla se subió primero acá (pedido "le falta más humo, fog") y pasó tal cual a las perillas. Tocarlo se ve en vivo: los MIDs del actor heredan todo salvo `Part`, `ShadowCenter`, `ShadowRadius` y `ShadowStrength` |

### Cómo re-aplicar el material desde el plan (receta probada 2026-09-28)
1. `python scripts/plan_valley_material.py` → `valley_build.json`.
2. Script A (parámetros: crea los que faltan y **actualiza default y grupo de TODOS**; reporta sobrantes; arma los helpers `V_*`, `D_*`, `C_MoonCosR`) y script B (código, vaciado y recarga de `Inputs`, cableado de cada Custom, `GradVS→VI0`, `LP→VI1`, `HeightVS→WPO`). Están en **`scripts/apply_valley_material_A.py`** y **`scripts/apply_valley_material_B.py`** (se pegan enteros como `script` de `execute_tool_script`; la versión v1 en `valle_v1_backup/stageB_*.py` solo ponía default a los parámetros NUEVOS). Los dos son idempotentes (el plugin a veces los corre dos veces).
3. Borrar los parámetros sobrantes con `delete_expression`.
4. `recompile` y leer el log **solo después** de la línea del `recompile` (gotcha 479).

## Componentes
- `Ground` — `SM_BreathValleyV2_SC`, `[MI_BreathValley_SC]`, sin sombra, sin colisión. 🔴 Escala del actor = 1 (el shader asume cm locales); se puede rotar en yaw.
- `Sky` — `/Engine/BasicShapes/Sphere` **escala 2000** (radio 1000 m: más chica queda dentro del terreno y tapa las colinas), **`bTreatAsBackgroundForOcclusion` true** (se dibuja después del suelo: sin eso, el ~60 % de los píxeles de suelo pagaría también el cielo). Mismo MI, sin sombra. Puesto en la plantilla Y en la instancia (gotchas 325, 478).

## 🎛️ Perillas de estética (2026-09-28, pedido de Beltrán "dale perillas al blueprint del valle para poder ajustar estética")
36 variables **instance-editable** con el mismo nombre que el parámetro del material; `ApplyLook()` (función nueva, llamada al final del Construction Script después de `PushShadow`) las empuja a los MIDs → **se ven en vivo al moverlas en Details**. Defaults del CDO = el look aprobado + la niebla subida; **`MorphAmt` 0,15 → 0,3** (pedido "dale animación de ondulación a las colinas": las colinas medias respiran el doble; es el tope de confort de la spec, `MorphAmt ≤ 0,3/MorphSpeed`).
| Categoría | Perillas (default) |
|---|---|
| `1-Colinas` | `HillAmp` 2200 · `HillScale` 8 · `HillSeed` 63 · `HillNear` 4500 |
| `2-Lejos` | `FarBase` 2600 · `FarAmp` 5500 · `FarScale` 22 · `FarSeed` 151 |
| `3-Movimiento` | `SwellAmp` 1880 · `SwellSpeed` 1 · `SwellShade` 1000 · `MorphAmt` **0,3** · `MorphSpeed` 1 |
| `4-LuzColor` | `LightAz` 20 · `LightEl` 25 · `ColLit` · `ColShadow` · `ColSheen` · `Sheen` 0,28 · `SlopeDark` 1,2 |
| `5-Cielo` | `SkyZenith` · `SkyHorizon` · `SkyGlow` · `GlowAz` 20 · `GlowEl` 2 · `GlowAmt` 0,8 |
| `6-Luna` | `MoonAz` −40 · `MoonEl` 7 · `MoonRadius` 9 · `MoonOpacity` 0,55 · `MoonColor` |
| `7-Niebla` | `FogStart` 800 · `FogDist` 20000 · `FogMax` 0,93 · `HFogDist` 15000 · `HFogFall` 2500 |
| `8-Sombra` | `bShadow` · `ShadowCenterManual` · `ShadowRadius` · `ShadowStrength` · `ShadowScaleRef` (ahora instance-editable) |
- Suelo recibe colinas/lejos/movimiento/luz/niebla + cielo y resplandor (la niebla tiende al color del cielo); el cielo recibe cielo, resplandor y luna.
- ⚠ Confort (spec §9): subir `SwellAmp`/`SwellSpeed`/`MorphAmt` por encima de los defaults pasa los topes de velocidad vertical (≤ 0,5°/s) → juzgar en visor. No cambiar `SwellSpeed`/`MorphSpeed` con el visor puesto (la fase salta).
- ⚠ Categorías sin espacios a propósito (gotcha 466). Si un DSL futuro necesita leerlas: `Variables|1-Colinas|GetHillAmp`.
- 🔴 Colisión de nombre: `ApplyLook` también existe en `BP_OrbDirector_SC`; `create_node('CallFunction|ApplyLook')` agarró la del otro BP. Se creó con `declaring_class` = `BP_BreathValley_SC_C` y `read_graph_dsl` lo sigue ROTULANDO `Class|BPOrbDirectorSC|ApplyLook` (mentira del lector: el nodo es `self` y empuja, verificado en los MIDs).
- Verificado: CDO = instancia en las 41; MID del suelo con 35 parámetros empujados, del cielo 12; 15 actores.

## Variables
| Variable | Default | Qué hace |
|---|---|---|
| `bShadow` | true | Apaga la sombra falsa (empuja fuerza 0) |
| `ShadowCenterManual` | (380, 0, 125) | Centro LOCAL cuando no hay metaball (y en el editor, sin Play) |
| `ShadowRadius` | 85 | Radio en cm locales |
| `ShadowStrength` | 1,5 | Oscuridad |
| `ShadowScaleRef` | **1,0** | Escala del metaball que corresponde a sombra plena (`BlobApplyEnv` escribe una escala **0..1**) |
| `ShadowTarget` | — | Se llena en BeginPlay con `GetActorOfClass(BP_BreathBlob_SC_C)` |
⚠ Ninguna es instance-editable: para cambiarlas hay que tocar el CDO.

## Grafos (5 de la v2 + `ApplyLook` + 4 de la capa viva, ver la sección 🫁)
- **Construction Script:** `NoCollision` ×2 → `Part` 0 en Ground / 1 en Sky → `PushShadow(ShadowCenterManual, ShadowRadius, bShadow ? ShadowStrength : 0)` → `ApplyLook` → **`PreviewLive`** (capa viva, al final). Sin `GetActorOfClass` acá (gotcha 467).
- **Tick:** … → `StepShadow` → **`StepLive`** (capa viva).
- **`PushShadow(Center, Radius, Strength)`:** tres `Set…ParameterValueOnMaterials` sobre `Ground`.
- **`StepShadow`** (Tick): sin `bShadow` → fuerza 0; con metaball válido → centro = `InverseTransformLocation(self, blob)`, `ratio = blob.Scale.X / max(ShadowScaleRef, 0,01)`, radio × ratio, fuerza × clamp(ratio) → la sombra **nace y se va con el metaball**; sin metaball → manual.
- **`PerfValleySet(Mode)`** + eventos **`PerfValley0..3`** (banco: 1 = vértices baratos, 2 = píxeles baratos, 3 = los dos). ⚠ Lectura v2: **píxeles = m0 − m2, vértices = m2 − m3** (m1 − m3 es solo cota inferior: el disco plano cambia la cobertura).
- **BeginPlay:** busca el metaball y loguea `VALLE: sombra sigue a <label>`.

## Banco
`BP_PerfEntering_SC.PerfFondo(bShow)` hace `SetActorHiddenInGame` **sobre el valle**. El modo "sin fondo" del banco = sin valle.

## Verificado
- v1 (2026-09-27): PIE + Simulate limpios; sombra sigue al metaball; gotas a ~45 cm del piso al exhalar a fondo.
- **v2 (2026-09-28, en Unreal):** malla 21.601 vértices, bounds ±64000; material compila limpio (los `Failed to compile` del log son de los estados intermedios del recableado, gotcha 479); PIE: `VALLE: sombra sigue a Entering_Blob`, etapa corre, cero errores; 15 actores intactos.
- **Movimiento medido en el editor** (Realtime encendido): dos capturas del frente separadas unos minutos → colinas 38,5 % de píxeles con cambio ≥ 3 niveles (máx 47), llano 4 %, **cielo y piso cercano 0 %** (control). Time-lapse de 43 s mirando atrás (10 cuadros, gotcha 480): 16-32 % de la franja de colinas cambia cada ~4,6 s, piso 0 %. GIF en `Saved/ClaudeScripts/valle_v2_timelapse.gif`.
- En el workflow: `Valley_check.py` 84/84 (dxc, fxc, SPIR-V; HLSL = modelo; §12; piso 0 exacto; velocidad vertical ≤ 0,451°/s; 8 mutaciones detectadas).

## 🫁 Capa viva (2026-09-28, rev. 2): 🟢 APLICADA en Unreal y verificada en PIE · ⬜ visor · ⬜ banco
Plan: [`docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md`](../../../../docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md) (§6 y receta V1-V13). La bruma, el resplandor y la **densidad** de la sombra respiran; **ninguna geometría** (confort §14.3), tampoco el radio de la sombra ni la altura del resplandor (la rev. 1 los movía: el borde de la sombra viajaba 4,4°/s por el piso cercano).
- **Material:** 11 parámetros nuevos (`BreathTint`, `ShadowWarm`, 9 `Live*` en `9 - Interno`) y 9 entradas de `ValleyPS` por **preshader** `Mul`/`Mix`/`Tint` (cuentas de uniformes, 0 por píxel). `Tint` = tinte **relativo** de `SkyHorizon` (sigue a la perilla de `ApplyLook`). **El HLSL no cambia** (solo la cabecera). Con los `Live*` neutros el valle es la v2 **bit a bit** (`Valley_check.py` 90/90; render neutro con el look actual = 0 píxeles distintos; `dryrun_material_script.py valle`). Se aplica con los mismos `apply_valley_material_A/B.py` (extendidos; el A lista `helpers_sobrantes`).
- **BP:** funciones nuevas `LiveMPC` (puente a `MPC_Breath`), `PushLive(S)` (9 `Live*` al suelo, 3 al cielo), `StepLive` (sigue a la respiración con `LiveTau` 1 s: el `Retire` del rig no salta el horizonte; DT de `GetWorldDeltaSeconds`), `PreviewLive` (DSL en `scripts/valley_live.dsl`, verificado con `dsl_sim.py valle`) + 2 cirugías de un nodo (Tick después de `StepShadow`; CS **al final, después de `ApplyLook`**). Variables `L-Respira` (11), **ninguna instance-editable** → la instancia `Entering_Valle` no se toca (a diferencia de las 36 perillas de look, que sí lo son).
- 🔴 Después de aplicar el material, **recargar el nivel** antes de la vista previa: los MIDs de `Ground`/`Sky` existen desde antes de que el material tuviera los `Live*` y no los honran (gotchas.md, "Un MID creado ANTES…").
- Rollback: `bLive` false (CDO) = neutros en ~5 s; o el material con `Saved/ClaudeScripts/aliento/rollback_valle_v2/apply_valley_material_{A,B}_v2.py` (plan del respaldo, probados) + borrar lo que listen como sobrante. **No** usar los scripts de dentro de `valle_v2_aplicada_backup/` (leen la ruta viva). Respaldos de los `.uasset`: `Saved/ClaudeScripts/capa_viva_backup/` (antes de la capa viva) y `capa_viva_backup/post_valle/` (con la capa viva, antes del aire).

### Registro de variables `L-Respira` (CDO, ninguna instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `bLive` | true | apaga la capa viva (el valle vuelve suave a los neutros) |
| `LiveAmount` | 1 | intensidad global (multiplica a `On`) |
| `FogBreath` / `GlowBreath` / `ShadowBreath` / `WarmBreath` | 1 | intensidad de cada familia (0 = esa familia quieta; 2 = doble). Primera palanca si en el visor "no se percibe" |
| `LiveTau` | 1 s | cómo sigue el valle a la respiración (el `Retire` no salta el horizonte) |
| `PreviewBreath` | 0 | vista previa sin Play (−1 … +1). 🔴 0 antes del cook (hoy 0) |
| `LiveS` | — | la S del valle (estado): sigue a `clamp(Signed)·clamp(On·LiveAmount)` con τ `LiveTau` |
| `LiveSig` / `LiveGate` | — | lo leído de `MPC_Breath` (`Signed`, `On`) este cuadro |
Las constantes `In`/`Out` de cada `Live*` viven como literales en `PushLive` (tabla §6.2 del plan).

### Grafos nuevos (texto exacto: `scripts/valley_live.dsl`)
- **`LiveMPC`:** dos `GetScalarParameterValue` de colección → `LiveSig`, `LiveGate`.
- **`PushLive(S)`:** curva de la casa por familia → 9 `Live*` al suelo (`Ground`) y 3 al cielo (`Sky`: `LiveWarm`, `LiveGlowAmt`, `LiveGlowPow`), en la misma función.
- **`StepLive`** (Tick, **después de `StepShadow`**): `LiveMPC` → `LiveS` sigue con τ `LiveTau` (DT = `GetWorldDeltaSeconds`) → `PushLive(LiveS)`.
- **`PreviewLive`** (CS, **al final, después de `ApplyLook`**): `PushLive(PreviewBreath)`.

### Verificado (2026-09-28)
- **Editor (fase V, capturas desde el ojo (0,0,120), métricas en `Saved/ClaudeScripts/capa_viva/metricas_v1_v4_v13.txt`):** material nuevo con `Live*` neutros → cielo alto y piso cercano **0 de diferencia** contra la captura de antes (control negativo; el resto dentro del ruido del oleaje). `PreviewBreath` −1/+1 → cambios en horizonte, cielo y sombra; la sombra: pico 19,4 (reposo) / 22,0 (inhala) / 15,9 (exhala) con el contorno a media altura casi en el mismo lugar (y 772-910 / 775-908 / 765-914 px): **respira en densidad, el borde no viaja**. `PreviewBreath` 0 → cielo y piso cercano otra vez 0 de diferencia. Capturas en `capa_viva/` (`v1_*`, `v4_*`, `v13_*`, `capa_viva_comparacion.png`).
- **PIE (fase T, traza por cuadro de 11 s en `capa_viva/pie/t4_traza_12s.json`, `bFakeBreath` 6 s en el rig de PIE):** `LiveSig` = `MPC_Breath.Signed` (−0,974 … +0,974, idéntico al que lee el aire), `LiveGate` 1, **`LiveS` oscila −0,675 … +0,675 con 0,77 s de retraso**. Es exactamente la respuesta de un seguidor de τ 1 s a una senoide de 6 s (amplitud 1/√(1+(ωτ)²) = 0,69, retraso atan(ωτ)/ω = 0,77 s): con la respiración real, más lenta y con retenciones, se acerca más a ±1. Cero `Accessed None`. Simulate (sin pawn, sin respiración): `LiveS` = `LiveSig` = `LiveGate` = 0 → el valle queda en su look autoral.

## 🌊 2026-09-29 — que el movimiento de las colinas se note
Beltrán en visor (2ª vez): *"sentí que las colinas no se están moviendo; debe notarse"*. Periodos de 31-83 s y amplitudes de pocos grados a 100-500 m = por debajo de lo perceptible. Perillas del CDO (`Entering_Valle` hereda): `MorphAmt` 0,3→**0,45**, `MorphSpeed` 1→**2** (colinas medias respiran con periodos de 20-40 s), `SwellAmp` 1880→**2800**, `SwellSpeed` 1→**2** (oleaje lejano de 15-23 s).
- ⚠ **Pasa los topes de confort de la spec §9** (≤ 0,5°/s vertical): decisión de Beltrán ("debe notarse"), a juzgar en visor. Si marea: bajar primero `SwellSpeed`, después `MorphAmt`.
- Si con esto sigue sin notarse, la perilla no es el mecanismo (memoria *degradado-frecuencia-contra-tamano*): el oleaje GEOMÉTRICO solo existe desde 280 m (`SwellIn`); habría que llevarlo a las colinas medias (45-260 m) en el material.
- Rollback: `VR_Test/Saved/ClaudeScripts/vida/ajustes_0929/rollback_valores_antes.md`.
## 🌊⏩ 2026-09-30 — las lomas SIEMPRE ondulan y se ACELERAN al exhalar (pedido directo de Beltrán)
*"Las lomas deben estar siempre ondulando. Cuando exhalamos, la ondulación debe ser más rápida. En los otros steps vuelve a su velocidad normal."*
- 🔴 **La velocidad NO se cambia en vivo** (`SwellSpeed`/`MorphSpeed` multiplican al tiempo: la fase saltaría; lo advertía la spec §249). Se integra **tiempo extra**: material `Tt = View.GameTime + SwellTimeOfs` en los dos Custom VS (`ValleyHeightVS` entrada 30, `ValleyGradVS` 30, que corre `SwellShade`/`SwellShadeFull` a 31/32); acelera el oleaje lejano, su sombreado en el llano y la respiración de las colinas medias. Con 0 = la v2 exacta.
- **BP `StepSwell(DT)`** (Tick, después de `StepLive`; `dt = min(DT, 1/30)`): `v` = d(`LiveSig`)/dt filtrada 0,3 s → `k* = 1 + (ExhaleSwell − 1)·clamp(−v/SwellVelRef)·clamp(LiveGate)` → `SwellK` lo sigue en `SwellFollow` s → `SwellOfs += dt·(SwellK − 1)` → `SwellTimeOfs` al `Ground`. Guarda `SwellK ≤ 0 → 1` (instancia vieja).
- Perillas `3-Movimiento` (instance-editable): **`ExhaleSwell` 3** (cuántas veces más rápido a exhalación plena) · **`SwellVelRef` 0,3** (1/s de `Signed` desde la que acelera del todo) · **`SwellFollow` 0,6 s** (cuán suave sube y vuelve). Estado `L-Respira`: `SwellSigPrev`, `SwellVel`, `SwellK`, `SwellOfs`.
- Verificado: `Valley_check.py` TODO OK con control positivo nuevo (VS(t, ofs) = VS(t + ofs, 0) exacto; ofs mueve las colinas 448 cm); material sin errores en el log; PIE con respiración falsa de 12 s: `SwellK` 2,99 exhalando, 1,0 inhalando/sosteniendo (con la cola del fundido), `SwellOfs` crece solo al exhalar (~+6,8 s por exhalación). ⬜ visor.
- ⚠ La aceleración sigue a `MPC_Breath.Signed` (el seguidor del rig llega al extremo en ~3-4 s): en una exhalación larga, el final vuelve a la velocidad normal. Si Beltrán la quiere durante TODA la exhalación: detectar el modo exhalar con histéresis (como `BP_BreathAir_SC`).
- Respaldo previo: `VR_Test/Saved/ClaudeScripts/usertool/swell_backup/` (material y BP). DSL: `usertool/valley_swell.dsl`. Receta del material: `usertool/m1_valley_swellofs.py` (solo los dos Custom VS; no toca `ValleyPS` ni las salidas de la capa de vida).

## Pendiente
- **Visor** (lo que decide): ¿se siente grande? ¿se ve ondular? ¿el llano "pintado" se lee raro? contraste del metaball contra la bruma, crestas de las colinas medias (bordes curvos en ~10-14 % de los azimuts), confort lateral (mirar a yaw ~45° y ~180°), facetas en las siluetas lejanas.
- **Z −90,4 del actor**: la puso Beltrán (casi seguro); la v2 la tolera pero la sombra queda más débil. Pregunta abierta.
- ¿Así de llano? Si lo quiere más envolvente: `HillNear`/`HillAmp` (acerca/sube colinas, a costa de escala).
- APK + banco (`PerfValley0..3`, ida y vuelta, dos pasadas). Estimado 1,2-2,5 ms, sin medir.
- Perillas en el BP (spec §9, con sus reglas) si Beltrán las quiere fuera del MI.
- Capa viva: ✅ aplicada y verificada en PIE (arriba). Falta el visor en el orden del plan §8 (primero el aliento con `bLive` false, después la sombra, después bruma y resplandor) y el banco (`FONDO = m0 − m4` de `quest_entering_perf.ps1 -Modos 0,4,5,6`: es el único número válido del valle con la capa viva).
- ⚠ No cambiar `SwellSpeed`/`MorphSpeed` en vivo con el visor puesto: la fase salta.
