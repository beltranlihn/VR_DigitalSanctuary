# BP_DrawSea_SC — el océano de la etapa de dibujo

`/Game/SoulCharger/Mechanics/Draw/Scape/` · construido el 2026-09-29 · plan: [`docs/PLAN-OCEANO-DIBUJO-2026-09-28.md`](../../../../docs/PLAN-OCEANO-DIBUJO-2026-09-28.md) · lookdev aprobado: `docs/prototipos/oceano-dibujo.html`.

| Estado | |
|---|---|
| Materiales | 🟢 `M_DrawSea_SC` / `M_DrawDust_SC` + MI, recompile sin errores, 132 entradas cableadas |
| BP | 🟢 compila; W/V/E del MID = modelo a 5e-8 (float32) |
| Nivel | 🟢 colocado en `Test_Draw` (label `DrawSea`) en (−315, 0, −120); PIE limpio |
| Viewport | 🟢 oleaje mate cruzado + niebla (el brillo del editor no es el del visor) |
| Visor / APK / 72 fps | ⬜ |

## Qué es
Mar oscuro y mate que morfea y avanza hacia el usuario, con niebla que borra el horizonte y polvo fino. Todo en los shaders (`View.GameTime`): **el actor no tiene Tick**. Solo escribe los parámetros de sus perillas en los materiales (Construction Script y BeginPlay).

## Componentes
`DefaultSceneRoot` · `Sea` (`SM_DrawSea_SC`, 18.721 vért, `BoundsScale` 1,5) · `Sky` (`/Engine/BasicShapes/Sphere` × 600 = 300 m, mismo material con `Part` 1) · `Dust` (`SM_DrawDust_SC`, 1.200 quads, `BoundsScale` 50). Los tres sin sombra ni colisión, MI en `OverrideMaterials` de la plantilla.

## Variables (tabla fuente: `scripts/draw_sea_sim.py` → `VARS`)
Perillas (instance editable): `1-Oleaje` SwellAmp 22 · SwellLenMax 2600 · SwellLenMin 420 · SwellDir 180 · SwellSpread 95 · Tempo 0,28 — `2-Grupos` GroupAmt 0,75 · GroupLen 9000 · Warp 120 · WarpScale 4500 — `3-Avance` Advance 5 — `4-CercaLejos` CalmR 600 · CalmMin 0,7 · LodNear 4 · LodFar 6,5 — `5-Superficie` Deep/Surf/CrestColor · CrestAmt · LightAz 40 · LightEl 22 · WrapPow 1,6 — `6-CieloNiebla` Zenith/HorizonColor · SkyPow · GlowColor/Amt/Pow · FogStart 500 · FogDensity 0,00017 · Dither 1 — `7-Polvo` bShowDust · DustColor · DustAmt 0,45 · DustSize 0,9 · DustBox 1400 · DustFollow 1 · DustRise 0,6 · DustWobble 8 · DustNear 35 · DustBG — `8-Material` SeaMI · DustMI.
Internas (`Z-Interno`): `Wc`/`Vc`/`Ec` (LinearColor, salida de `Wave`), `PerfMode`, `bPerfNoDust`.

## Grafos (fuente: `scripts/draw_sea.dsl`, simulado por `scripts/draw_sea_sim.py`)
- **ConstructionScript**: `SetMaterial` ×3 (MI de las perillas) → sin colisión ×3 → `ApplyLook`.
- **ApplyLook**: `LookSea(C)` mar y cielo → `Part` 0/1 → `WaveConstants` → `LookDust`.
- **WaveConstants**: `Wave(I, Off)` ×6 con OFFS [0, 0,85, −0,7, 0,35, −1, 0,55] → `W0..5`/`V0..5`/`E0..5` en el mar.
- **Wave(I, Off)**: largo, número de onda, dispersión de mar profundo, amplitud, hash de fases con **el `frac` de GLSL** (el `Fraction` de UE conserva el signo: gotcha 491), dirección del grupo, LOD 4/6,5 largos.
- **LookDust**: parámetros del polvo + `SeaZ` = Z del actor + visibilidad (`bShowDust` y el banco).
- **ApplyPerf** + EventGraph: `PerfDS0..4` (0 todo · 1 vértices baratos · 2 píxeles baratos · 3 los dos · 4 sin polvo; eco `PERF: drawsea modo N`). `EventBeginPlay` → `ApplyLook`.

## Materiales (fuente: `scripts/gen_draw_sea_hlsl.py` → `scripts/hlsl/DrawSea*.hlsl`, `DrawDust*.hlsl`)
- `M_DrawSea_SC`: unlit opaco two-sided, fp32 en expresiones. `DrawSeaHeightVS` → Transform Local→World → WPO; `DrawSeaGradVS` → VI → `DrawSeaPS` → Emissive. 44 parámetros.
- `M_DrawDust_SC`: unlit **aditivo** two-sided. `DrawDustVS` → WPO (mundo); `DrawDustAlphaVS` → VI → `DrawDustPS` (suma en sRGB codificado contra `DustBG`, gotcha 485). 13 parámetros.
- Verificador: `scripts/hlsl/DrawSea_check.py` (correr con `scripts/memcap.py`). Armado: `plan_draw_sea_material.py` → `apply_draw_sea_material.py` (ensayo `dryrun_draw_sea.py`).

## Para instalarlo en otro nivel
Arrastrar `BP_DrawSea_SC` con el centro bajo los ojos del usuario, **226 cm por debajo** del punto del usuario sentado (en `Test_Draw`: PlayerStart z 106 → actor z −120). Escala 1; se puede girar en yaw (el avance va hacia −X local). Con un `BP_Sky_Sphere` en el nivel, el cielo del actor lo tapa (radio 300 m).

## Pendiente
APK + banco (`ke * PerfDS0..4`, dos pasadas) → 72 fps · visor con Beltrán (oscuridad, polvo, vección, banding) · decisiones §8 del plan.
