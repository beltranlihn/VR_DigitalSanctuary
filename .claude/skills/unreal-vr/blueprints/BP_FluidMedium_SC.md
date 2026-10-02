# BP_FluidMedium_SC — el FLUIDO CEREBRAL (Mechanics/Mind/)

> Creado 2026-09-28. Plan: `docs/PLAN-FLUIDO-CEREBRAL.md`. Referencia visual y matemática:
> `docs/prototipos/fluido-cerebral.html` (publicado como artifact). Pedido de Beltrán: *"sumergidos en un entorno
> líquido, como el líquido del cerebro; 3D, amplio, etéreo"*, sin latido ni respiración, movimiento curl de fluido,
> **única entrada: EEG 0-1** (0 activo, 1 calma — la misma convención que `GlobalState` de la célula).
> **Estado: 🟢 F1 construida (fondo + 3 capas de partículas + MPC + BP) · 🟢 F2 (células medias AMEBA + siluetas lejanas) y
> F3 (haces, velos, cáusticas en las células) construidas el 2026-09-28: compilan (DXC + log), BP con `warnings_as_errors`,
> se ven en el editor (`Test_Mind`, capturas en `Saved/ClaudeScripts/Fluid/shots/fluido_f2f3_vistas.png`, `fd_close_crop.png`),
> diagnóstico de NaN/piezas: 0 · 🟢 PIE con `bFakeEEG` (integración exacta) · ⬜ visor · ⬜ medir (F6) · 🟢 cáusticas sobre la célula de Loving (F5, `WaterLight`).**

## Arquitectura
El BP integra el TIEMPO; los shaders calculan todo lo demás (sin estado por partícula, sin CPU por partícula).
- `Tick`: `FluidStep(DT)` (EEG suavizado → perillas moduladas `Eff*`; rumbo de la corriente con `Meander`; integrales
  `Drift`, `FlowPhase`, `CausticPhase` envuelta en 20·π) → `UpdateHead(true)` (cámara del jugador en espacio LOCAL) →
  `PushFluid(true)` (13 vectores a `MPC_Fluid_SC`).
- `BeginPlay`: igual con `Snap` + `ApplyLayers`. **Construction Script**: `FluidStep(0, Snap)` → `ApplyLayers` →
  `UpdateHead(false)` (ojos en (0,0,120)) → `PushFluid(false)`.
- **`Phase.w = Live`**: 1 en juego (fases integradas por el BP); **0 en el editor = el material usa su propio reloj**
  (`T × velocidad`, `DriftVel × T`) → el fluido se mueve en el viewport sin Play (la lección "la instancia anima sola"
  de Heart). Verificado: dos capturas a 5 s cambian el 5 % de los píxeles.
- `ApplyLayers`: `LayerA/LayerB` por componente (MID) + `SetTranslucentSortPriority` (1 lejos, 2 media, 50 cerca) como
  red de seguridad (gotcha 478).

## Componentes (actor en el origen del usuario, rotación identidad — todo en espacio local)
| Componente | Malla | Material | Notas |
|---|---|---|---|
| `Background` | `SM_GanzShell` (reusada, Core/Light) ×200 = radio 100 m | `M_FluidBackground_SC` (opaco unlit two-sided) | dirección desde la cámara (`CameraVectorWS`): siempre "en el infinito"; dither R2 en el espacio codificado |
| `MotesFar` | `SM_FluidMotesFar_SC` (4000 quads) | `M_FluidMotes_SC` (translucent unlit two-sided) | cubo 40 m, sort 1, bounds ×400 |
| `MotesMid` | `SM_FluidMotesMid_SC` (2400) | idem | cubo 12 m, sort 2 |
| `MotesNear` | `SM_FluidMotesNear_SC` (600) | idem | cubo 3,6 m, sort 50 (delante de la célula), desenfoque |
| `MidCells` (F2) | `SM_FluidMidCells_SC` (16 × [núcleo 642 + 5 satélites 42] = 18 624 v en UE) | `M_FluidMidCells_SC` (OPACO unlit) | bounds ×400. Cada vértice: célula en UV1.x, pieza en UV2.x (0 núcleo, 1-5 satélites); la posición es solo la dirección |
| `FarCells` (F2) | `SM_FluidFarCells_SC` (64 quads, `polvo` semilla 71) | `M_FluidFarCells_SC` (MASKED + **alpha-to-coverage**, two-sided) | bounds ×400; `Dith` (dither R2) cableable si el A2C fallara en el visor |
| `Veils` (F3) | `SM_FluidVeils_SC` (6 quads; UV1.x = velo) | `M_FluidVeils_SC` (translucent) | sort −2, bounds ×600; la capa de más RELLENO |
| `Shafts` (F3) | `SM_FluidShafts8_SC` (8 tiras × 8 quads; UV0.x ancho, UV1.x largo, UV2.x haz; antes `SM_FluidShafts_SC`, 4) | `M_FluidShafts_SC` (ADDITIVE, two-sided) | sort −1, bounds ×600. Propios: `BP_LightShaft_SC` trae pulso y respiración |
Mallas: `scripts/gen_fluid_canvases.py` (Blender headless, reusa `polvo()` de Loving): UV0 esquina, UV1/UV2 semillas.

## MPC_Fluid_SC (23 vectores; lo que empuja el BP hoy en negrita)
**FTop FMid FBot** (colores del medio) · **Glow** (luz desde arriba, intensidad) · **Absorb** (distancia, máximo,
pérdida de opacidad, concentración de la luz) · **Caus** (cantidad, tamaño, velocidad, destellos) · **Phase** (fase
remolinos, fase cáusticas, velocidad remolinos, Live) · **Flow** (amplitud, tamaño, -, remolinos chicos) · **Drift** ·
**DriftVel** · **Head** · **StirK** (remolino de mano, estela) · **Mote** (color, brillo) · Hand0/HandV0/Hand1/HandV1
(manos: F4, apagadas) · **CellHigh** · **CellLow** (.a = contraste) · **CellFill** · **FarA** (cubo 70 m, tamaño lejanas,
remolinos, cuántas de 64) · **Light** (dirección de la luz = la de Loving, .w = `MidCellRange`) · **Extras** (VeilAmount,
ShaftAmount, MidCellCount, MidCellScale). Los empuja **`PushCells`** (CS + BeginPlay; no en Tick).
✅ Los `CollectionParameter` creados por MCP **resolvieron** (control: los colores del fondo son los de la MPC; si el
Id no resolviera saldría negro — gotcha 416).

## Shaders (fuente única en texto)
`VR_Test/Shaders/Fluid/FluidLib.ush` (port línea por línea del prototipo: `FluidColor`, `AbsorbAt`, `Caustic`,
`SinCurl`, `RotR/RotRT`, `FlowAt`, `WrapHead`, `Stir`, `FacingBasis`, `CellShade`) + wrappers `FluidBgPS`,
`FluidMotesVS`, `FluidMotesPS`. Compuestos con `compose_loving.py --lib ... --wrappers ... --out
VR_Test/Saved/ClaudeScripts/Fluid/composed` y chequeados con `check_loving_hlsl.py --wrappers ... --comp ... --out ...`
(los dos scripts se generalizaron el 2026-09-28; sin argumentos siguen siendo Loving, verificado byte a byte).
Sprites **orientados hacia el ojo** (no alineados con la pantalla) y two-sided. Estela opcional (`StreakTime` 0).

## Variables (instance editable; nombres = perillas del prototipo)
`0-EEG`: EEG 0,3 · bFakeEEG · FakePeriod 60 · EEGSmoothing 2 s · EEGFlow 0,7 · EEGClarity 0,5 ·
`1-Movimiento`: CurrentSpeed 4 · CurrentYaw 20 · CurrentPitch 8 · Meander 35 · FlowAmp 22 · FlowScale 130 · FlowSpeed 0,14 ·
Turbulence 0,7 · StreakTime 0 · `2-Liquido`: FluidTop/Mid/Bottom · GlowColor · GlowAmount 0,45 · GlowPower 3 ·
AbsorbDist 800 · AbsorbMax 0,92 · AbsorbAlpha 0,35 · `3-Particulas`: MoteColor · MoteBright 1,25 · Near/Mid/FarSize
0,45/1,3/6 · Near/Mid/FarAlpha 0,85/0,6/0,5 · Bokeh 3 · BokehDist 60 · `5-Luz`: CausticAmount/Scale/Speed · MoteSparkle ·
`4-Celulas` (F2): MidCellCount **12** · MidCellScale **1,1** · MidCellRange **1800** (cubo de las medias; el prototipo 2600 las
dejaba a 6-10 m = 15 px) · FarCellCount 48 · FarCellSize **80** · CellFlow 0,6 · CellHigh (0,97 0,95 1) · CellLow (0,30 0,26 0,72)
· CellContrast **1** (con 0,6 el sombreado recorría solo 82-99 % de brillo en sRGB: elipses planas) · CellFill · CellLight
(−0,551 −0,401 0,732) · `5-Luz` + ShaftAmount 0,14 · VeilAmount 0,5 · `6-Manos`: bHandStir (false) · StirStrength · StirRadius · StirSwirl · `Z-Interno`: EEGS, FlowPhase, CausticPhase,
Drift, DriftVel, HeadL, Clock, Eff*.
DSL versionado: `scripts/fluid_medium.dsl`.

## 🔎 Revisión adversarial de F2/F3 (2026-09-28, workflow: 4 lentes + 4 verificadores; 30 hallazgos, todos confirmados, ninguno alto)
Lentes: móvil/Adreno y doble evaluación · matemática y fidelidad al prototipo · costo en Quest · integración.
Hallazgos completos (con evidencia y verificación): `Saved/.../scratchpad/wf_review_medias.txt` de la sesión; lo que importa, aquí.
**APLICADO (código DXC "TODO COMPILA", inyectado, recompilado sin errores, BP con `warnings_as_errors`, todo guardado):**
| Id | Qué | Dónde |
|---|---|---|
| MAT-1 (media) | Los haces salían **9-12 veces más tenues** que en el prototipo: three.js suma valores CODIFICADOS; el Quest mezcla en LINEAL. Ahora el PS suma en el espacio codificado contra el fondo conocido (`BG` del VS) con la OETF sRGB EXACTA (`LinToSRGB`/`SRGBToLin`, con tramo lineal). Medido tras el cambio: +35-60 de luminancia sobre el fondo (antes 2-3 niveles) | `FluidShaftVS/PS`, `FluidLib` |
| MAT-2 / MOV-1 / INT-2 (media) | El alpha-to-coverage móvil de UE cuantiza a 4 niveles (el primero = 25 %): el fundido de las siluetas lejanas aparecía a saltos. Ahora el fundido va al COLOR, el alfa solo al borde, y la silueta se ACHICA en el último tramo (`size × smoothstep(0; 0,3; fade)`) para no tapar con profundidad lo de atrás | `FluidFarCellsVS/PS` |
| MAT-3 | Luz de las lejanas = la del MUNDO proyectada en el quad (`LQ`); antes una constante de pantalla, del lado contrario a las medias | `FluidFarCellsVS/PS` (+ CP `Light`, + interpolador) |
| MAT-4 | Cáusticas de las medias POR PÍXEL (por vértice dejaban rombos que se arrastraban); material en `MFPM_Full_MaterialExpressionOnly` | `FluidMidCellsVS/PS` (+ salida `Pw`, + CP `Caus`/`Phase` en el PS) |
| MAT-5 | Comentario de resolución corregido: arista de la icoesfera de 642 = 0,151 rad (no 0,074): 34° ≈ 4 aristas; error de teselado ≤ 0,041 radios | `FluidLib::CellLobe` |
| MAT-6 / MOV-4 | `atan2(0,0)` (indefinido en SPIR-V; el píxel central cae exacto en 0 con UV half) protegido | `FluidFarCellsPS` |
| MAT-7 / MOV-5 | Giro de las lejanas envuelto en 2π (llegaba en half y se cuantizaba con el tiempo de juego) | `FluidFarCellsVS` |
| MAT-8 / INT-4 | El DSL versionado no llamaba a `PushCells` (el grafo real sí): sincronizado | `scripts/fluid_medium.dsl` |
| INT-1 (media) | Orden de dibujo: el fluido pasaba por delante de las manos y del HUD (sort 0). Ahora velos −12, haces −11, motas lejanas −9, medias −8 (célula de Loving 4-40, motas cercanas 50) | `PushCells`, `ApplyLayers` |
| INT-3 / INT-5 / INT-6 | `PushCells` también en **Tick** (en PIE/VR Preview el CS no se re-corre: las perillas de F2/F3 no llegaban). La visibilidad salió del CS (se grababa como override y trababa el viewport) a **`ApplyVisibility`**, solo en BeginPlay, que ahora también apaga las 3 capas de motas con alfa 0 (antes no tenían interruptor de costo cero) | BP: `PushCells` (cirugía: −4 SetVisibility y 16 nodos huérfanos), `ApplyVisibility` (nueva), EventGraph |
| INT-7 | Respaldo del cubo de las medias: si `Light.w` no llega, 1800 (con el piso de 600 quedaban en puntos) | `FluidMidCellsVS` |
| COS-2 (media) | Dither del fondo con sqrt/cuadrado en vez de dos `pow` float3 (sin ruido, idéntico): −0,35..−0,46 ms estimados | `FluidBgPS` |
| COS-3 / COS-7 | Motas: velocidad y manos en ramas UNIFORMES (con StreakTime 0 y sin manos no cambiaban nada): −33 % del VS; quad invisible sin área | `FluidMotesVS` |
| COS-4 | Medias: 22 hashes PCG por vértice → 2 por célula + 1 por satélite + 1 por lóbulo (campos de bits de un mismo PCG, exactos en las dos evaluaciones). **Cambian las formas** de las amebas (nuevas semillas) | `FluidLib` (`PCG`, `Bits`), `FluidMidCellsVS` |
**PENDIENTE (con dueño):**
- 🔴 INT-1, la otra mitad: las motas CERCANAS (50) siguen por delante de manos y HUD. Hace falta subir a **100** la `TranslucencySortPriority` de las manos del pawn y del WidgetComponent del HUD (**Core/**: coordinar con Beltrán).
- COS-1 / COS-6: el presupuesto real es ~0,9-1,8 ms tras estos arreglos (estimado; la tabla §5 del plan subestimaba las medias 3-4 veces). F6 se mide con un **`BP_PerfFluid_SC`** (patrón de `BP_PerfEntering_SC`: `ke * PerfF0..N`, eco en logcat, SetVisibility por capa) y **App GPU de VrApi** (`quest_entering_perf.ps1`/`resumen_entering.py`, resolución 0,09 ms), NO FrameTime. Modos P0-P9 en el plan.
- COS-5 / MOV-3: velos = ~0,8 pantallas por ojo (hasta 2) para un cambio de ≤ 1 escalón en casi todo su área. Decisión de Beltrán (A/B en F6); si se quedan, malla octogonal (−15-20 % de área).
- MOV-2: la malla de medias tiene +37 % de vértices por las costuras de la UV0 cúbica (18 624 vs 13 632); sacarlas choca con la gotcha 303. Solo si F6 lo pide.
- MAT-1 colateral: las motas translúcidas también mezclan en lineal (no en codificado como el prototipo): ~+30 niveles en una mota brillante de alfa 0,3. Revisar mirando.
**ACEPTADO como limitación:** INT-8 (`FarCellCount` es aproximado: 48 → 53, 32 → 35 con la semilla 71) · INT-9 (~3 motas cercanas dentro del volumen de la célula de Loving se ven sobre su envoltura: recortarlas costaría más de lo que arregla).

## F2/F3 (2026-09-28) — células, haces, velos
Pedido de Beltrán: *"los rayos que vienen desde arriba como si estuvieras bajo el agua o la cáustica y las otras amebas que van a
estar flotando, desvaneciéndose por estar a la distancia"*. Wrappers `FluidMidCellsVS/PS`, `FluidFarCellsVS/PS`,
`FluidShaftVS/PS`, `FluidVeilVS/PS`; librería + `Hash1` (entero), `CellLobe`, `CellAmoeba`, `ShaftTable`, `VeilTable`.
- **Células medias**: ameba = 4 pseudópodos de Loving (`2q¹⁰ − q⁵`, cuello suave) con amplitud 0,5 que crecen y se retraen
  a destiempo; normal EXACTA por el gradiente (verificada contra diferencias finitas: 8e-10). Satélites en un anillo vertical
  a 1,9-2,3 radios (el prototipo 2,7-3,3 se leía como constelación). Nunca a menos de 2,5 m de la cabeza (se achican), se
  achican en el borde del cubo (reciclado invisible). El desvanecido es COLOR (absorción), no transparencia. Luz = la de la
  célula de Loving. Cáusticas por vértice solo en lo que mira hacia arriba (a este tamaño casi no se leen).
- **Lejanas**: silueta en un quad (núcleo con borde de ameba de 3 y 5 lóbulos + 3-5 satélites), aparecen a 7-11 m, se funden en el fondo.
- **Haces**: tiras que giran alrededor de su eje hacia la cámara, se abren hacia abajo; aditivos con el color `Glow`.
  **2026-09-28 (noche), Beltrán: "los rayos deberían animarse suavemente, algunos más anchos, como si el sol se refractara con el
  movimiento del agua de la superficie"** → **8 haces** (`SM_FluidShafts8_SC`, 144 v; `ShaftTable` de 8, anchos 40-260 cm, dos
  detrás): el punto de entrada deriva ~1,2 m, el eje ondula (±0,05), el ancho respira (±15 %), cada haz se enciende y se apaga
  a destiempo (0,15-1) y por dentro corren ESTRÍAS a lo ancho (fase envuelta en `BG.a`, en fp32 en el VS). Anchos compensados
  `sqrt(60/ancho)`. Ritmos constantes × T (periodos 50-220 s). Time-lapse: `Saved/ClaudeScripts/Fluid/shots/haces_animados.gif`.
- **Velos**: 6 manchas enormes y tenues (dos gaussianas), color del medio ±, llevadas al 60 % por la corriente; con 0,5 casi no se notan.
- ⚠ La instancia de `Test_Mind` no heredó componentes ni variables (gotcha 478): escritos de a uno.
- 🔴 El satélite negro: gotcha **481** (hash de seno en un Custom con WPO + interpoladores). Arreglado con hash entero y
  verificado con un PS de diagnóstico en 18 direcciones: 0 píxeles de pieza apagada, 0 NaN.

## Trampas de esta construcción
- Un `Custom` recién creado trae UNA entrada por defecto: cargar la lista completa de una falla ("insertion points are
  ambiguous") → primero `{"inputs": []}`, después la lista.
- El nivel duplicado (`AssetTools.duplicate`) no se puede abrir hasta guardarlo ("the level has unsaved changes").
- Un BP nuevo trae tres eventos fantasma (BeginPlay, ActorBeginOverlap, Tick): borrarlos antes de escribir el EventGraph por DSL.
- `SetColorParameterValueonMaterials` se escribe con "on" en minúscula (el DSL lo resolvió igual en Loving).

## Nivel de prueba `/Game/SoulCharger/Mechanics/Mind/Maps/Test_Mind`
Copia de `Test_Loving`: el Ganzfeld OCULTO (`Shell.bVisible` false + `bHiddenInGame`), la célula de Loving intacta
(y = −67,5), el fluido en el origen. 11 actores.

## "Noche perla" (2026-09-28, propuesta Turrell × Six N. Five) — SOLO en la instancia de `Test_Mind`
Juez del workflow `wf_c3631e33-68a`. Diagnóstico medido: la saturación del agua (0,62-0,80 HSV) y el `GlowColor` azul
eléctrico eran lo sci-fi; Six N. Five trabaja con campos de saturación 0,11-0,25 y un solo objeto con color.
Valores aplicados: `FluidTop` (0,0307 0,0437 0,0648) · `FluidMid` (0,0097 0,0152 0,0242) · `FluidBottom` (0,0048 0,0065 0,0097;
piso subido para el LCD) · `GlowColor` (0,807 0,716 0,565, luna crema) · `GlowAmount` 0,32 · `GlowPower` 4 · `AbsorbDist` 650 ·
`AbsorbMax` 0,95 (estaba en 1,39) · `MoteColor` (0,672 0,631 0,552) · `MoteBright` 0,75 · `MoteSparkle` 0,08 · alfas de motas
0,45/0,45/0,35 · `CausticAmount` 0,22 · `CausticScale` 38 · `CausticSpeed` 0,35 · `VeilAmount` **0** · `MidCellCount` 5 ·
`FarCellCount` 20 · `CellContrast` 0,7 · `CellHigh` (0,397 0,456 0,552) · `CellLow` (0,048 0,070 0,117) · `CellFill`
(0,023 0,036 0,063, 0,4) · `CurrentSpeed` 2,5 · `FlowSpeed` 0,1 · `Turbulence` 0,45 · `EEGSmoothing` 6 · `EEGClarity` 0,7.
**Desvíos del juez, a propósito:** `ShaftAmount` queda en 0,14 (el juez pedía 0,025, pero Beltrán acababa de pedir los haces
animados y visibles) y `CellBody` queda en 0,35 (el juez no sabía que existe; es la gelatina que se pidió para las medias).
Rollback: `Saved/ClaudeScripts/Fluid/paletas.json` → `antes_noche_perla`. El CDO NO se tocó.
⬜ Cambio de código propuesto y NO hecho (esperando OK): "hora de la luz" con el EEG — `GlowColorCalm` (0,831 0,708 0,540),
`GlowPowerCalm` 4,5, `ColorSmoothing` 25 s; con eso `GlowColor` pasa a ser el activo (0,584 0,651 0,738) y `GlowPower` 3.
Segundo filtro exponencial en `FluidStep`, lerp en `PushFluid` (cirugía de nodos). Costo GPU 0.
Plan listo (2026-09-29): variables `GlowColorCalm`, `GlowPowerCalm`, `ColorSmoothing`, `Z-Interno|EEGC` y un interruptor
`LightByEEG` (CDO 0 = neutro bit a bit, porque lerp(a,b,0) = a); `k = clamp(EEGC)·LightByEEG`. ⚠ Con `FakePeriod` 60 y
`ColorSmoothing` 25 s, el color solo recorre el 36 % (filtro de primer orden: 1/√(1+(2π·25/60)²)); con 8 s, el 77 %.
Narrativa (orquestador, noche 09-28/29): **esta noche no**, la estética la decide Beltrán mirando → mostrárselo en PIE.
`Test_Recorrido` carga `Test_Mind` ENTERO como instancia de nivel: no tocar `Test_Mind` ni este BP hasta que el APK esté listo.

- 🟢 **2026-09-29 (tarde): Beltrán ajustó en el editor `FluidTop`** (0,0307 0,0437 0,0648) → **(0,0125 0,0324 0,0648)** (arriba más azul) en la instancia de `Test_Mind`. Guardado por Mind a pedido de Heart (el nivel estaba sucio al cambiar de nivel).

## 🫧 AMEBAS MEDIAS = MEMBRANA + NÚCLEO PERLA (2026-09-30, pedido directo de Beltrán)
*"Las otras amebas que flotan alrededor quedaron demasiado low poly y se ven como globitos flotando; más cercanas a la estética de la
principal, sin consumir mucho recurso."* Solo `M_FluidMidCells_SC` (wrappers `FluidMidCellsVS/PS`); sin BP, sin mallas nuevas.
- **Sigue siendo UNA pasada opaca** (sin orden de translúcidos ni sobre-dibujo; lo de atrás es el color del medio, `FluidAb`).
- VS: salida nueva **`Ctr`** = (centro de la pieza, radio del núcleo interior) → **VertexInterpolator nuevo**; núcleo 0,50 del radio
  base (cota: la ameba nunca baja de 0,72 con 4 lóbulos en su mínimo −0,14), satélites 0,45 de su radio.
- PS (+ entradas `Ctr` y `CamL`): **núcleo perla ANALÍTICO** (rayo cámara → píxel contra la esfera `Ctr`: redondo y sin facetas aunque la
  malla sea de 642 / 42 vértices), borde difuso (`disc / 0,45 r²`, elegido mirando 0,12 / 0,45 / 0,8 en un render offline), opacidad
  0,85, `CellShade` perla + cáusticas · **membrana** = la superficie (la ameba): color `CellHigh`, opacidad 0,10 + 0,25·CellBody en el
  cuerpo → 0,75 en el Fresnel (`(1 − N·V)^2,5`) → **0 en el limbo** (`smoothstep(0, 0,22, N·V)`): la silueta facetada se funde en el agua.
- Aplicado con el constructor de materiales del fluido (sincroniza los dos Custom desde `Saved/ClaudeScripts/Fluid/composed`, crea el
  interpolador que falte y cablea `CamL`); `vs_ok`/`ps_ok`; compila sin errores; emisiva = `Custom_1` (PS).
- Capturas (editor, antes/después; son células distintas porque en el editor derivan con el tiempo):
  `Saved/ClaudeScripts/Loving/turno_0930/medias/recortes_medias.png`. Medido a ~8 m: núcleo #6F6473, membrana #433B49, agua #2D2733.
  Vista previa offline: `scratchpad` → `amebas_medias_antes_despues.png` (enviada a Beltrán). ⬜ visor.

## 🌪️ EL MUNDO SE ACTIVA CON LA AMEBA (2026-09-30, pedido directo de Beltrán)
*"Cuando la actividad hace que la ameba se mueva y se active, las partículas del mundo tengan más velocidad de movimiento también,
para sentir que todo el world se activa."* Fuente: `scripts/fluid_active_boost.dsl`.
- `FluidStep` REESCRITO (= `fluid_medium.dsl` + esto; verificado igual al grafo antes de vaciarlo): perilla **`0-EEG|ActiveBoost`**
  (CDO 0 = idéntico). `boost = 1 + ActiveBoost × a²` (a = actividad = 1 − EEG suavizado; al cuadrado: en calma no toca nada)
  multiplica `EffCurrent` (la corriente: traslada TODAS las motas y las medias) y `EffFlowSpeed` (remolinos); las cáusticas a la
  mitad del factor. Todo por fases/derivas integradas (cambiar la velocidad no salta posiciones). Paso = min(DT, 1/30).
- La célula (`BP_LovingCell_SC.StageCouple`) acopla SIEMPRE que vive (fases 0/2/3/4): EEG del fluido = SS(0,2; 0,9; S) = la misma
  actividad que su `AgTarget`, y apaga el falso propio del fluido (en el tour el agua y la ameba se activaban a destiempo).
- Instancia de `Test_Mind`: ActiveBoost 0 → **2** · EEGSmoothing 6 → **1,5 s**.
- ✅ PIE: activa (S 0,26) corriente **10,1 cm/s** y remolinos 0,52 (antes ~3,5 y 0,18); la ameba se contrae en la entrada → el agua se
  calma a 1,7 cm/s en ~4 s; en la mecánica vuelven a activarse juntas (10,3 cm/s, ~1,5 s de retardo). ⬜ visor.

## 🖐️ F4 — MANOS (2026-09-30, noche; "etapa sin sensor: las manos mueven las partículas y generan turbulencia")
El shader ya lo tenía (`Stir` en `FluidMotesVS`, rama uniforme por `HandV.w`); faltaba el BP. Fuente: `scripts/fluid_hands.dsl`.
`HandRefs()` toma los grips del pawn (`BP_VRPawn_SC.GetMotionController{Left,Right}Grip`; reintenta cada cuadro hasta tenerlos) ·
`HandStep(DT)` (empalmado al final del Tick, tras `PushCells`): posición local de cada mano → `Hand0/Hand1` = (pos, StirRadius);
velocidad = diferencia / DT (tope `HandMaxSpeed` 300 cm/s), suavizada con `VInterpTo` a `HandVelSpeed` 5/s → `HandV0/HandV1` = (vel,
StirStrength). Con `bHandStir` false la velocidad objetivo es 0 y el remolino se APAGA con curva; `HandV.w` = 0 recién con < 0,5 cm/s.
Paso ≤ 1/30. Variables: `6-Manos` HandVelSpeed · HandMaxSpeed · `Z-Interno` HandL/HandR (SceneComponent) · HandsReady · HandsPrimed ·
HandPL/PR · HandVL/VR. La célula de Loving la maneja en el contrato (TourWake/fin: off, StageBegin: on) y le escribe `EEG` = su S
durante la mecánica (el EEG del fluido y la célula ya son UNA entrada: pendiente del TODO de abajo, resuelto para la Obra).
Instancia de `Test_Mind`: bHandStir true · HandVelSpeed 5 · HandMaxSpeed 300 · **EEGFlow 0,7 → 1,0** (más contraste activo/calma) ·
**paleta morada** (misma luminancia): FluidTop #1D3248 → #362E3E · FluidMid #19212B → #241E2A · FluidBottom #0D1219 → #131115 ·
GlowColor #D2C7B3 → #D3C3D9 · MoteColor → #DDCAE6 · CellHigh → #C0ACCC · CellLow → #342A3E · CellFill → #3B3047 (valores lineales en
`Saved/ClaudeScripts/Loving/turno_0930/instancias_despues.json`). ✅ PIE: HandsReady true. ⬜ Visor con mandos.

## 🚀 EL VIAJE: "que el pawn y la neurona avancen" (2026-09-30, Beltrán vía Narrativa)
*"Que el vr pawn y la neurona avancen. Hazlo moviendo las partículas, para no mover el pawn. Que se sienta que vamos avanzando."*
Fuente: `scripts/fluid_travel.dsl`. Nada se mueve en la escena: **`TravelStep(DT)`** suma una velocidad de viaje a la deriva
integrada (`DriftVel += TravelVel`, `Drift += TravelVel·dt`), que ya traslada TODAS las capas por shader (motas, amebas medias,
siluetas, velos). El fondo está en el infinito: el horizonte no se mueve. Costo GPU cero.
- Curva: `TravelU` va a la meta (`bTravel`) a ritmo lineal (1/`TravelEase` al subir, 1/`TravelEaseOut` al bajar);
  velocidad = `TravelSpeed` × smootherstep(`TravelU`). Paso ≤ 1/30.
- Empalmes: Tick `FluidStep → TravelStep → UpdateHead` · BeginPlay `FluidStep → TravelBegin` (TravelU 0) · CS `FluidStep → TravelPreview`
  (TravelU 1: **en el viewport del editor el viaje se ve siempre**, para ajustar `TravelSpeed` mirando).
- Lo maneja la célula (`BP_LovingCell_SC.FluidTravel(On)`): TourWake/TourSleep off · **StageBegin on** · **StageOutro off**.
- Variables: `7-Viaje` bTravel (false; lo prende el contrato) · TravelSpeed 25 · TravelEase 4 · TravelEaseOut 2 · TravelYaw 180 · TravelPitch 0 ·
  `Z-Interno` TravelU · TravelVel. Instancia de `Test_Mind`: TravelYaw **−180** (de la célula hacia el PlayerStart, calculado), resto = CDO.
- ✅ PIE con el runner del ensayo: 0 hasta Begin → 25 cm/s en 4,0 s → en el outro 0 en ~2,0 s (antes de la fase 5); salto máximo entre
  lecturas 0,78 cm/s. **Efecto** verificado: `Drift.x` avanza −23,9 cm/s con el viaje lleno. Registro: `Saved/ClaudeScripts/Loving/turno_0930/pie_viaje.json`. ⬜ visor.

## TODO
- [x] PIE con `bFakeEEG` (2026-09-28, período 30 s): el BP integra EXACTO — `EEGS` medido en t = 8,68 / 23,30 / 32,92 s =
  0,4308 / 0,6040 / 0,0497 contra una simulación del mismo filtro 0,4314 / 0,604 / 0,0495. Activo (EEG 0,04): `EffFlowSpeed` 0,213,
  `EffTurb` 0,97, `EffAbsorb` 736 · calma (0,96): 0,096 / 0,38 / 1104. En cuadro quieto la diferencia es sutil (algo más de
  claridad en calma); está en el MOVIMIENTO. Sin visor la cámara del pawn queda en el piso (`HeadL` = 0,0,0): esperable,
  en el visor toma la altura real. Capturas: `Saved/ClaudeScripts/Fluid/shots/pie_activo_calma.png`.
- [ ] 🔴 Integración con la etapa: el EEG del fluido y el `GlobalState` de la célula de Loving son hoy DOS entradas separadas;
  el manager de la etapa tiene que alimentar las dos con el mismo valor.
- [x] F2: células medias (amebas) y lejanas (siluetas, alpha-to-coverage) — 2026-09-28.
- [x] F3: haces propios, velos, cáusticas en las medias — 2026-09-28.
- [x] F5 (cáusticas del agua sobre la célula de Loving, perilla `WaterLight`; absorción en espera): 2026-09-28, ver `BP_LovingCell_SC.md` V4c.
- [ ] Juicio de Beltrán: cantidad/tamaño de amebas, si los velos (0,5) y los haces (0,14) tienen que subir.
- [ ] F6: APK + OVR Metrics por capa.
