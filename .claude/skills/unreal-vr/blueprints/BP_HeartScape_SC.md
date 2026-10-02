# BP_HeartScape_SC — la membrana del latido

`/Game/SoulCharger/Mechanics/Heart/Scape/` · plan: [`docs/PLAN-MEMBRANA-DEL-LATIDO-2026-09-27.md`](../../../../docs/PLAN-MEMBRANA-DEL-LATIDO-2026-09-27.md) · lookdev en navegador: https://claude.ai/artifact/En9CRj53wBDrJfGLcB4LBK

## Propósito
El paisaje del latido: una membrana mate enorme donde **cada latido** hace latir la esfera central, **nace una onda** en el borde del hoyuelo donde se asienta la esfera y viaja hacia afuera con colinas que cambian de lugar en cada latido. Reemplaza en aspecto al océano de `BP_PulseField_SC`, que **no se tocó** y queda como referencia. Diferencia clave con aquel: aquí la ola se lee **por la luz sobre la geometría** (normal analítica), no por un degradado de color según la altura.

## Estado (2026-09-27, fases 1 a 3 del plan)
| Pieza | Estado | Evidencia |
|---|---|---|
| Malla polar `SM_HeartMembrane_SC` (v1) → **`SM_HeartMembraneLite_SC` (v3, la que usa el actor)** | 🟢 | v1: 78.849 vértices, el 43 % dentro del metro central. v3: `gen_heart_membrane.py -- lite` → 192 sectores, 5 anillos uniformes hasta 30 cm y geométrico desde 36 cm: **32.641 vértices**, 65.088 triángulos. ⚠ El cambio de malla en el template NO llegó a la instancia colocada: se asignó a mano en `Test_Heart` |
| Material `M_HeartScape_SC` + `MI_HeartScape_SC` | 🟢 compila · 🟡 aspecto solo en miniatura | 117 shaders (PC SM6 y **ES31**) sin un error en el log; miniatura del disco de prueba con relieve; esfera (`Part` 1) reducida a 22 cm con núcleo y borde |
| Blueprint | 🟡 compila, **sin PIE** | 0 errores y 0 advertencias; los cuatro grafos releídos con `read_graph_dsl` |
| Nivel de prueba `/Game/SoulCharger/Mechanics/Heart/Maps/Test_Heart` | 🟢 creado | Duplicado de `Test_Breath` (GameMode `BP_XRGameMode`, PlayerStart en el origen) sin los 6 actores de respiración. `HeartScape` en **(600, 0, −20)**: esfera a 6 m al frente, ojos sentados (~120 cm, tracking Stage) a 1,4 m sobre la superficie |
| PIE | 🟢 verificado (2026-09-27) | A los ~15 s: `WaveDist` 6.461 (420 cm/s ✓), 15 latidos → `WaveSlot` 7 ✓, `LastI` 0,91 (variación ✓), `WaveSpeed`/`DemoBPM` leídos de la MI ✓. En el MID de la membrana: `Part` 0, `Live` 1, `Beat` y `Wave0..7` rotando (nacimientos separados 420 cm). 0 `Accessed None`, 0 errores de runtime |
| Viewport del editor | 🟢 visto por captura | Anillos con colinas, líneas de cresta, charco azul, cielo con resplandor. ⚠ A distancia apareció un arco oscuro corrido junto a la esfera que NO está de cerca: probable fantasma del AA temporal del editor sobre un objeto que se mueve por WPO (la Quest no tiene TAA). Mirar en visor |
| APK en la Quest | 🟢 instalado (21:02) | `com.almadigital.heart`: monta el OBB y carga `Test_Heart` en 0,47 s; sin caída al material por defecto en logcat |
| Rendimiento | 🟢 **v3: 72-73 fps, App ≈ 10,4 ms** (7,3-11,1; GPU 73-85 %) con el visor puesto, 2026-09-27 21:35 | Historia medida en la Quest: **v1** 58-66 fps, App 13-15,6 ms · **v2** (Customs separados + gradiente analítico + línea interpolada) 56-58 fps, App 14,6-18: **no mejoró** · **banco sobre la v2** (ida y vuelta, 10 s por modo): todo 15,3-16,5 · vértices baratos **10,5** · píxeles baratos 13,7-14,3 · ambos 10,2 → **los VÉRTICES costaban ~5,4 ms, los píxeles ~2** · **v3** = malla liviana (`SM_HeartMembraneLite_SC`, 192 sectores, 32.641 vértices, −59 %) + corte por onda en los tres VS (cada vértice evalúa solo las ondas con cresta a < ~2,5 anchos) → **72 fps**. Quedan ~3,5 ms para la fase 4 · **v4** (+24 esferas por ISM, esfera central más grande y ameba): **72-73 fps, App ≈ 10,6 ms** (9,3-11,1), 2026-09-27 21:57: las esferas cuestan ~0,2 ms, dentro del ruido · **v5** (esfera que flota + resorte, pulso con la cola del latido anterior, esferas ameba más grandes con subida continua, 36 perillas): **72-73 fps sostenidos, App 9,1-11,9 ms (mediana ≈ 10,9)**, GPU 75-91 %, 2026-09-27 22:21, 40 s con el visor puesto. +0,3 ms contra la v4: dentro del ruido de una sola pasada. Margen ≈ 2-3 ms |

## Qué se toca dónde (para Beltrán)
🆕 **2026-09-27 (noche), por pedido de Beltrán: las perillas de la estética viven en el ACTOR** (panel Details del `HeartScape` colocado). El Construction Script las lleva a los cuatro materiales (`ApplyLook` → `LookTo` ×4), así que **cambiar una se ve al instante en el viewport**, animado, sin Play. Pisan el valor de la MI para esos parámetros; todo lo demás sigue en la MI.

| Categoría del actor | Perilla → parámetro del material | Qué hace |
|---|---|---|
| **1 - Latido** | `bDemo` | En Play, latidos automáticos |
| | `DemoBPM` → `PreviewBPM` | **Ritmo CARDÍACO** simulado (editor **y** Play) |
| | `BeatDivider` (**1** desde 2026-09-30; antes 2) | Uno de cada N latidos se ve. Con 1, un pulso visual por cada sonido del manager (pedido de Beltrán 2026-09-30). El material divide el preview igual |
| | `PulseRise` (0,45) | Segundos hasta la cima del pulso (tamaño/brillo). Curva suave `x²·e^(2(1−x))`, **un** pulso por latido visual |
| **2 - Ola** | `WaveSpeed` → `Speed` | Velocidad de la onda (cm/s) |
| | `WaveHeight` → `HeightStart` · `WaveHeightFar` → `HeightEnd` | Altura de la ola al nacer y al final de su viaje (cm) |
| | `WaveWidth` → `Width` · `WaveReach` → `Reach` · `WaveHills` → `Hills` | Ancho de la cresta · hasta dónde llega · irregularidad de la cresta |
| **3 - Esfera central** | `HeartSize` → `HeartRadius` · `HeartHeight` → `HeartZ` | Radio · altura sobre la membrana (cm) |
| | `HeartFloat` / `HeartFloatSpeed` | Vaivén lento: amplitud (cm) y ciclos por segundo |
| | `HeartPush` → `HeartSink` (14) | Cuánto baja en el empuje (cm reales: la curva tiene cima 1). **Un** empuje, sin resorte |
| | `PushSpeed` (1) | Velocidad del empuje: 1 = llega al fondo en 0,5 s; 2 = el doble de rápido. **La onda nace en el fondo** |
| | `HeartSquash` (0,06) · `WellRest` → `WellDepth` (3) · `WellPush` → `WellBeat` (10) | Achatado al empujar · hoyuelo en reposo (cm) · cuánto hunde el empuje al agua (cm) |
| | `HeartAmoeba` → `HeartMorph` · `HeartGrow` → `PulseScale` | Deformación ameba · cuánto crece en el latido |
| | `EntryTime` (2,5) | Segundos que tarda la esfera en brotar del agua (`StageIntro`) o en hundirse (`StageOutro`). Solo BP |
| **4 - Esferas que emergen** | `SizeMin` / `SizeMax` (8 / 60) | Radio de las esferas (cm, sorteo `rand^2,2`: muchas chicas, pocas grandes); solo BP |
| | `SpawnMin` / `SpawnMax` (300 / 1500) · `OrbClearance` (500) | Anillo de nacimiento alrededor de la esfera central (cm) · distancia mínima al espectador: si caen más cerca o detrás de él, se reflejan al otro lado de la esfera |
| | `AmebaMix` | Fracción de esferas ameba (1 = todas) |
| | `OrbRise` → `RiseHeight` (700) · `OrbRiseRamp` → `RiseTime` (2,5) | Altura al final de su vida · segundos hasta tomar velocidad de globo (después sube constante) |
| | `OrbLife` (20) · `OrbFade` (0,45) | Vida FIJA desde que nace (s) · fracción final en que se va desvaneciendo |
| | `OrbPulse` → `OrbKick` (0,15) · `OrbAmoeba` → `OrbMorph` (0,3) · `OrbDrift` → `OrbSway` | **Un** pulso suave cuando la onda pasa por debajo · ameba del secuenciador + estirón propio · deriva lateral (cm) |
| **5 - Colores de la membrana** | `ColorLight`/`ColorShadow`/`ColorSheen`/`ColorGlow` → `ColLit`/`ColShadow`/`ColSheen`/`ColGlow` | Luz, sombra, brillo rasante, resplandor del charco |
| | `ColorCrest` → `ColLine` · `CrestLine` → `LineGlow` · `CrestLineWidth` → `LineWidth` · `CrestGlow` | Color, intensidad y grosor de la línea de cresta · brillo de la cara de la cresta |
| **6 - Colores de la esfera** | `HeartColor`/`HeartColorShadow`/`HeartColorCore`/`HeartColorRim` → `HeartLit`/`HeartShadow`/`HeartCore`/`HeartRimColor` | (también tiñen las esferas que emergen) |
| **7 - Horizonte y niebla** | `SkyColorTop`/`SkyColorHorizon`/`SkyColorGlow` → `SkyZenith`/`SkyHorizon`/`SkyHorizonGlow` | Cielo arriba, en el horizonte y su resplandor |
| | `HorizonGlow` · `FogStart` · `FogDistance` → `FogDist` | Intensidad del resplandor · dónde empieza la niebla · en cuánto se cierra (cm) |
| **8 - Material base** | `LookMI` | La MI de la que parten los MIDs (el resto de los parámetros) |

⚠ **Sin rangos de slider ni descripciones en el panel** (no hay tool para la metadata de variables BP, gotcha 463): los rangos útiles están en la tabla de la MI (cada parámetro tiene `sliderMin/Max` y `desc`).
- Otra forma fina (pozo, oleaje, luz rasante, tiempos del latido…) → **`MI_HeartScape_SC`**, grupos `1` a `8`.
- Grupo `9 - Interno` de la instancia → **no se toca**: lo escribe el actor en Play.

En el editor, sin Play, **la instancia anima sola** con su reloj de preview (`Live` = 0): los latidos salen a `DemoBPM`. En Play el actor pone `Live` = 1 y los latidos pasan a ser los suyos.
⚠ `PreviewIntensity`, `DemoVariation`, `WellRadius` y `OrbMax` los sigue **leyendo el actor** de `LookMI` (BeginPlay / BootOrbs / SeedOrbs). Sin uso desde la v6: `Attack`, `Decay`, `Dub`, `DubDelay`, `PrevBeat` (escalar) de la MI.
🔌 **Entrada para el sensor real: `OnHeartBeat(Intensity)`** — llamarla en CADA latido cardíaco (el actor descarta rebotes < 0,3 s y muestra uno de cada `BeatDivider`). `Intensity ≤ 0` = la del demo.

## Assets
| Asset | Qué es |
|---|---|
| `SM_HeartMembrane_SC` | Disco polar plano, 256 sectores, radios `r_j = 4 cm · q^j` con `q = 1 + 2π/256` (celdas casi cuadradas) hasta 60 m + faldón (80/120/200/350/600 m). Generador **versionado**: `scripts/gen_heart_membrane.py` (Blender headless) |
| `M_HeartScape_SC` | Master único: membrana, esfera y cielo, elegidos por `Part`. Unlit, **opaco**, two-sided, `MFPM_Full_MaterialExpressionOnly`, `bUsedWithInstancedStaticMeshes` (para las esferas de la fase 4) |
| `MI_HeartScape_SC` | La superficie de autoría (paleta azul de la referencia) |
| `Debug/SM_HeartMembranePreview_SC` | Disco de 8 m (`gen_heart_membrane.py -- preview`) **solo para verificar por miniatura**: la malla real encuadra 1,2 km y las ondas no se ven |
| `Debug/MI_HeartPreviewCore_SC` | Hija de la MI con `Part` = 1, solo para la miniatura de la esfera |
| Esfera: `/SC_Base/Meshes/SM_AlmaSphere` (radio 50, 2.665 vért.) · Cielo: `/Engine/BasicShapes/Sphere` a escala 1400 (700 m, más allá del faldón) | referenciados, no modificados |

## Componentes
`DefaultSceneRoot` · `Membrane` (`SM_HeartMembrane_SC`) · `Heart` (`SM_AlmaSphere`, `boundsScale` 1,5) · `Sky` (esfera del motor, escala 1400). Los tres con `castShadow` falso, `overrideMaterials` = `MI_HeartScape_SC` en el template y colisión apagada en el Construction Script.
🔴 **Escala del actor = 1.** Se puede rotar en yaw (todo se calcula en espacio local: la cámara se lleva a local y el WPO vuelve a mundo), pero la esfera asume cm locales.

## Registro de variables
| Variable | Tipo | Cat. | Rol |
|---|---|---|---|
| `LookMI` | MaterialInstanceConstant, editable | Latido | La instancia de la que salen los tres MIDs y de la que se leen `Speed`/`PreviewBPM`/`PreviewIntensity`/`DemoVariation`. Default `MI_HeartScape_SC` |
| `bDemo` | bool, editable | Latido | En Play, latidos automáticos cada `60 / PreviewBPM` s (intervalo fijo) con intensidad `PreviewIntensity · (1 ± DemoVariation)` |
| `WaveDist` | float | Z - Interno | Distancia recorrida por la onda desde BeginPlay (se **integra**: `+= WaveSpeed·DT`). Cambiar la velocidad no hace saltar las ondas |
| `WaveSlot` | int | Z - Interno | Siguiente casillero del ring buffer `Wave0..Wave7` |
| `LastBeat` / `LastI` | float | Z - Interno | Momento e intensidad del último latido (arranca en −1000 = sin pulso) |
| `NextBeat` | float | Z - Interno | Próximo latido del modo demo |
| `DemoI`, `DemoVar` | float | Z - Interno | Copias leídas de `LookMI` en BeginPlay |
| `WaveSpeed`, `DemoBPM`, `SizeMin`, `SizeMax`, `AmebaMix` | float, **editables** | 1/2/4 | Eran copias internas leídas de la MI; desde 2026-09-27 son **perillas** (ya no las pisa BeginPlay/BootEchoes) |
| 31 perillas nuevas (24 float + 12 `LinearColor`… ver tabla de arriba) | editables | 2 a 7 | Solo las lee `LookTo`. Valores iniciales = los de la MI de ese día |
| v6: `BeatDivider` (int), `PulseRise`, `PushSpeed`, `HeartSquash`, `WellRest`, `WellPush`, `OrbFade`, `OrbClearance`; `SpawnMin/Max` pasan a editables | editables | 1/3/4 | Ver la tabla de perillas |
| v6: `BeatCount` (int), `LastHeart`, `PrevBeat`, `PrevI`, `PrevBeat2`, `PrevI2`, `LastSpawn`, `SpacingS`, `ViewerX`, `ViewerY` | float | Z-Interno | Historia de 3 latidos, antirrebote, anti-reciclado, espaciado suavizado, espectador en local |

## Estructura de grafos (v6, 2026-09-27 noche — una función por responsabilidad)
- **Construction Script**: `SetMaterial(LookMI)` en los tres → `Part` 0/1/2 (crea los MIDs) → colisión apagada ×3 → **`SeedOrbs`** → **`ApplyLook`**.
- **BeginPlay**: lee `PreviewIntensity`/`DemoVariation` de `LookMI` → `LastBeat` −1000 → `NextBeat` = ahora + 0,5 → `Live` = 1 en membrana y esfera → **`BootOrbs`**.
- **Tick**: **`DemoBeat(DT)`** → **`PushBeat()`**.
- **`OnHeartBeat(Intensity)`** 🔌 **la entrada pública**: un latido CARDÍACO. Antirrebote (< 0,3 s se descarta) → `BeatCount++` → si `BeatCount % BeatDivider == 0` → `EmitPulse`.
- **`EmitPulse(Intensity)`**: corre la historia (`PrevBeat2/PrevI2 ← PrevBeat/PrevI ← LastBeat/LastI`) → `LastI`, `LastBeat` → `SpacingS` suavizado y acotado (`lerp(S, clamp(raw, 0,6·S, 2·S), 0,3)`: un latido doble no apaga las ondas) → `Spacing` a membrana y ecos → `Wave<slot>` → **`PushBeat`** (en el MISMO cuadro: sin él, el material veía el latido viejo contado dos veces = el "chispazo") → **`SpawnOrb(LastI)`**.
- **`PushBeat()`**: `Beat = (LastBeat, LastI, WaveDist, ahora)` y `BeatP = (PrevBeat, PrevI, PrevBeat2, PrevI2)` a membrana, esfera y ecos, siempre juntos.
- **`DemoBeat(DT)`**: integra `WaveDist` → si `bDemo` y toca: agenda el siguiente a `60/DemoBPM` y llama `OnHeartBeat(−1)` (el demo pasa por el mismo camino que el sensor).
- **`SpawnOrb(I)`**: solo si pasó `(OrbLife + SpawnMax/Speed + PushT + 1) / OrbCount` desde la última (así **nunca se recicla una esfera viva**) → ángulo áureo ± ruido, radio `lerp(SpawnMin, SpawnMax, √rand)`, tamaño `lerp(SizeMin, SizeMax, rand^2,2)·(0,85 + 0,15·I)` → **regla del espectador**: si cae a menos de `OrbClearance` o detrás de él, se refleja `(x, y) → (−x, −y)` → custom data 0-5 + `Bump<slot>`.
- **`BootOrbs()`** (BeginPlay): `Live` = 1 en ecos, `WellR`, `OrbCount`, `OrbTheta` al azar, inicializa la historia (−1000), `LastSpawn`, `LastHeart`, `BeatCount`, `SpacingS = WaveSpeed·60·BeatDivider/DemoBPM`, `PrevBirth = −SpacingS` → `PushBeat` → oculta las 24 instancias.
- **`SeedOrbs()`** (Construction Script, preview del editor): **`FindViewer`** → material/`Part` 3 de ecos → 24 instancias por ángulo áureo con la misma regla del espectador y la misma distribución de tamaños.
- **`FindViewer()`**: `GetActorOfClass(PlayerStart)` → **`IsValid`** → `ViewerX/Y` en local. Sin PlayerStart (mundo de la miniatura al guardar) no toca nada: queda el default (−600, 0).
- **`ApplyLook()`** → `LookTo(C)` ×4 (`Membrane`, `Heart`, `Sky`, `Echoes`); **`LookTo`** = 38 perillas y al final **`LookExtra(C)`** = las 7 de la v6 (`PulseRise`, `PushSpeed`, `HeartSquash`, `WellDepth`, `WellBeat`, `OrbFade`, `BeatDivider`).
- Borradas en la v6: `StepField`, `TriggerHeartbeat`, `SpawnEcho`, `SeedEchoes`, `BootEchoes`.

## El material (v2, 2026-09-27 noche: optimizado sin cambiar el aspecto)
🔴 **Unreal compila el WPO y cada `VertexInterpolator` en funciones SEPARADAS: cada salida vuelve a llamar a su Custom.** En la v1, un solo Custom con 3 salidas (VI1, WPO, VI2) y 3 evaluaciones del campo por diferencias finitas se ejecutaba varias veces por vértice. La v2 reparte el trabajo en Customs que calculan solo lo que su salida necesita:

| Nodo | Shader | Entradas | Salida → destino | Qué calcula |
|---|---|---|---|---|
| `Custom_2` **HeartHeightVS** | VS | 51 | float3 → `Transform_1` (Local→World) → **WPO** | Solo la altura `h` (una evaluación). Esfera: su desplazamiento |
| `Custom_0` **HeartGradVS** | VS | 51 | float4 → `VertexInterpolator_0` → `VI1` | Membrana: **gradiente ANALÍTICO** en una pasada (`sincos`, derivada del perfil, del pozo Ricker, del oleaje y de los bultos) + `h` + cresta. Esfera: normal |
| `Custom_3` / `Custom_4` **HeartXA/XB_VS** | VS | 18 | float4 → `VertexInterpolator_2/3` → `XA`/`XB` | La coordenada de cresta `x` de las ondas 0-3 y 4-7 (única diferencia en el código: `KO` 0 o 4) |
| `LocalPosition_0` | VS | — | → `VertexInterpolator_1` → `LPi` | posición local para el PS |
| `Custom_1` **HeartScapePS** | PS | 68 | float3 → **Emissive** | Sombreado, niebla por **distancia real** (`Distance(WorldPosition, CameraPositionWS)`; antes `PixelDepth`, que en VR "nadaba" al girar la cabeza), línea de cresta con `x` **interpolada** (sin trigonometría por píxel; `fwidth` fuera de ramas), charco, luz de la esfera, dither |

Interpoladores usados: 4 + 3 + 4 + 4 = 15 de 16. Fuente versionada: `scripts/hlsl/HeartHeightVS.hlsl`, `HeartGradVS.hlsl`, `HeartXVS.hlsl`, `HeartScapePS.hlsl` (la v1 de un solo Custom queda en `HeartScapeVS.hlsl` como referencia). Para recargar: copiar a `VR_Test/Saved/ClaudeScripts/*.txt` y `read_file` + `set_properties({"code":...})` dentro de un script.
- **Casillero reciclado sin salto** (hallazgo de la revisión): con 8 casilleros, a 60 lpm una onda se pisaba a los 8 s todavía al ~55 %. Ahora `life *= 1 − smoothstep(0.8·Dmx, Dmx, d)` con `Dmx = 7,7 · Spacing` (distancia entre los dos últimos latidos; en preview `período · Speed`). La evolución de la onda (ancho, altura, desvanecido por `Reach`) es la misma de la v1.
- **Banco**: parámetro `PerfMode` (grupo 9): 1 = vértices baratos (sin ondas), 2 = píxeles baratos (color plano), 3 = ambos. Eventos `Perf0..Perf3` del actor (`ke * PerfN`, eco `PERF: heart modo N`). Script: `scripts/quest_heart_perf.ps1` → `resumen_heart.py`.
- Parámetros nuevos: `PerfMode` y `Spacing` (grupo 9, los escribe el actor). `PixelDepth_0` quedó sin uso.
- Adreno (gotcha 399): todos los bucles con tope constante; los arreglos se leen solo dentro de bucles desenrollados.

## Fase 4 — esferas que emergen (2026-09-27, en visor)
- **`Echoes`** = `InstancedStaticMeshComponent` con `SM_HeartOrb_SC` (icoesfera de 642 vértices, radio 50; `gen_heart_orb.py`; **límites de la malla ampliados** ±3200 en XY y +1600/−200 en Z para que el WPO no las cullee), `NumCustomDataFloats` 6, `Part` = 3.
- **Datos por instancia**: `OA` = (x, y, salida) · `OB` = (radio, semilla, ameba), leídos con `PerInstanceCustomData3Vector` (índices 0 y 3). Salida: en vivo = tiempo del mundo en que la cresta llega a ese radio; en preview = índice de fase (una esfera por latido, ciclo de `OrbMax` latidos: **se ven animadas en el editor**).
- Toda la vida en el material (`HeartHeightVS`/`HeartGradVS`, rama `Part > 2.5`): espera sumergida → sale con el bulto (`BumpAmp`) → sube (`RiseHeight`, `RiseTime`, easing cúbico) con deriva (`OrbSway`) → empujón y brillo cuando pasa otra onda (`OrbKick`, `OrbGlint`) → ameba (`AmebaMix`, `OrbMorph`) → se encoge al final de `OrbLife` (acortada sola si el pool se recicla antes).
- BP: `SeedEchoes` (desde el Construction Script: 24 instancias con datos de preview por ángulo áureo), `BootEchoes` (BeginPlay: `Live` = 1, lee perillas, oculta todas), `SpawnEcho(I)` (en cada latido: siguiente casillero + `Bump0..3` en la membrana). Las ondas (`Wave0..7`), `Beat` y `Spacing` se empujan también al MID de `Echoes`; la semilla de la onda va por la variable `WaveSeed` (un `RandomFloat` puro usado dos veces daba dos valores distintos).
- ⚠ **Componente agregado después de colocar el actor → llega vacío a la instancia** (sin malla, 0 datos, con sombra; gotcha 341). Se volvió a colocar `HeartScape` en `Test_Heart` (ahora `BP_HeartScape_SC_C_1`).
- Esfera central ajustada por pedido de Beltrán (*"muy circular, el golpe muy duro"*): `HeartRadius` 30, `HeartZ` 38 (flota), `HeartMorph` 0,09, `Attack` 0,18, `Decay` 0,7, `HeartSink` 3, `WellBeat` 7, `BirthDistance` 160.
- El "arco oscuro" junto a la esfera en las capturas del editor era el **sprite del actor** (BillboardComponent), no un artefacto de render.

## v5 — flotación y perillas (2026-09-27 noche, pedido de Beltrán en visor)
*"La esfera central tiene que sentirse flotando y en cada pulso empujar hacia abajo… las esferas que salen también ameba, un poco más grandes… la subida se ve entrecortada."*
- **Esfera central**: `dz = −HeartSink · I · Σ resorte amortiguado (latido y dub, actual y anterior) + HeartFloat · sin(2π · HeartFloatSpeed · t)`. El resorte (`cos(wq·t)·e^(−t/Decay)` con arranque suave `1 − e^(−t/0,35·Attack)`) baja, rebota y se asienta; `HeartSink` 3 → **9**, vaivén **4 cm a 0,12 Hz**. Parámetros nuevos `HeartFloat`, `HeartFloatSpeed` (grupo 3).
- **Pulso sin corte**: `Pulse` suma la cola del latido anterior (`PrevBeat`, grupo 9, lo escribe `TriggerHeartbeat`). Antes caía ~45 % en un cuadro con cada latido nuevo (gotcha 464b).
- **Subida de las esferas**: ya no siguen la superficie ni reciben el empujón por onda (causa de los escalones). Salen a la altura de la cresta que las suelta (`launch`) y suben con velocidad que crece en smoothstep durante `RiseTime` y después **constante** hasta `RiseHeight` al final de la vida. `OrbKick` cambió de sentido: ahora es cuánto **crecen** cuando pasa la onda (0,15). `AmebaMix` 1 (todas ameba), `OrbMorph` 0,14, tamaños 6-26 → **10-36**, `RiseHeight` 420 → **800**, `RiseTime` 7 → **5**.
- **Perillas en el actor** (tabla de arriba): `ApplyLook`/`LookTo` nuevas; BeginPlay, BootEchoes y SeedEchoes dejaron de leer `Speed`/`PreviewBPM`/`SizeMin`/`SizeMax`/`AmebaMix` de la MI.
- **Verificado**: 0 errores de shader; viewport (esferas ameba repartidas en altura, esfera central sobre su hoyuelo); **PIE**: los tres MIDs con las perillas, `Live` 1, `PrevBeat` = latido anterior (24,5 contra `LastBeat` 25,5), `WaveDist` a 420 cm/s, 0 `Accessed None`. CDO **e instancia colocada** con los 41 valores releídos (instance-editable nace en cero).

## v6 — un solo "pum" suave, a la mitad del ritmo (2026-09-27 noche, dibujo de Beltrán)
✅ **APROBADA en visor por Beltrán (23:17): *"Super. Estamos."***
🎛️ **Después Beltrán afinó a mano en el actor de `Test_Heart` (ya guardado): `HeartPush` 14 → 24,4 y `OrbAmoeba` 0,3 → 0,08.** Son SUS valores: no pisarlos. El APK instalado todavía tiene 14 / 0,3; el próximo empaquetado lleva los suyos.
*"La ameba central pulsa rapidísimo, como si cambiara de tamaño de un frame a otro y volviera… tiene que ser un pulso suave, orgánico, con filtro… la pulsación visual es la MITAD del ritmo cardíaco… un impulso hacia abajo para generar la onda."* Después: *"un solo pulso, no doble; un solo push; perilla para la velocidad del push"*. El dibujo: (1) flota sobre agua plana → (2) baja y hunde el agua → (3) sube y salen las dos crestas.
Investigación de solo lectura con simulación cuadro a cuadro (workflow de 3 auditores + el pulso del secuenciador). **Las causas, en orden de peso:**
1. 🔴 **Cuadro doble (bug mío de la v5):** `StepField` empujaba `Beat` ANTES de `TriggerHeartbeat`, que escribía `PrevBeat` en ese cuadro → durante 1 cuadro el material veía `Beat.x == PrevBeat` y sumaba dos veces el latido anterior: +1,3 cm de radio y +3,6 cm de altura y vuelta al cuadro siguiente. **Es exactamente "cambia de tamaño de un frame a otro y vuelve".** En el editor no se ve (el preview usa un solo reloj). Arreglo: `EmitPulse` llama a `PushBeat` en el mismo cuadro, y la historia viaja en un solo `float4` (`BeatP`).
2. El resorte arrancaba con un **escalón de velocidad** (`1 − e^(−t/0,063)`: de 0 a −130 cm/s en un cuadro) + el dub repetía el golpe a 0,28 s.
3. Solo 2 latidos de memoria: al llegar uno nuevo se descartaba de golpe la cola del n−2.
4. Esferas: vida atada a `Spacing` (cada latido reescalaba la subida de TODAS: saltos de 12 cm), casillero reciclado con la esfera viva (89 de 95 a 60 lpm, desapariciones a 7 m y teletransportes), aparición a tamaño completo 1 s antes de su cresta, dos rampas en serie (salía a 61 cm/s y quedaba ~1 s a 2 cm/s mientras la cresta siguiente la atravesaba = "pegadas"), y pulso por la estela de la onda (2-3 pulsos por onda).

**La v6:**
- **Una sola curva** `g(x) = x²·e^(2(1−x))` (arranca en 0 con pendiente 0, cima 1, sin quiebres; es la forma medida del cuerpo de `BP_SoundOrb_SC` del secuenciador: RMS 1,8 %) para el pulso (`PulseRise` 0,45 s) y para el empuje (`0,5/PushSpeed` s). Suma del latido actual + los 2 anteriores, cada uno con su intensidad. Sin dub, sin resorte.
- **Mitad del ritmo**: `OnHeartBeat` cuenta latidos cardíacos y emite uno de cada `BeatDivider` (2). `DemoBPM` = ritmo cardíaco; `PreviewBPM` idem y el material divide el período (`BeatDivider` también es parámetro).
- **El empuje hunde el agua**: pozo `WellDepth + WellBeat·Push` (3 + 10 cm), la esfera baja `HeartSink` 14 cm y se achata `HeartSquash` 6 % → queda a ~4-6 cm del agua en el fondo. **La onda nace en el fondo del empuje**: `wd = PushT·Speed` restado a la distancia de TODAS las ondas (VS de altura, gradiente, XA/XB, PS, pulso de las esferas) y `PushT` restado a la edad de las esferas y de los bultos.
- **Esfera central**: ameba del secuenciador (forma grumosa + onda lenta + giro de 8 °/s; la v5 "hervía" 6-10× más rápido), con frecuencias más bajas que en las esferas chicas (con las mismas quedaba "coliflor").
- **Esferas que emergen**: vida fija (`OrbLife` 20), una sola curva de subida (impulso suave desde sumergida + globo constante), crecen invisibles bajo el agua, se desvanecen encogiendo el último 45 %, **un** pulso `g` por onda cuando la cresta pasa bajo su punto de salida, ameba del secuenciador por esfera (`OrbMorph` 0,3, giro 20 °/s, respiración lenta) + estirón propio (elipsoide 1,3:1 orientado por la semilla), tamaños 8-60 (`rand^2,2`), anti-reciclado en `SpawnOrb`, nunca a menos de 500 cm del espectador ni detrás de él.
- **Verificado**: 0 errores de shader; preview (amebas de tamaños distintos, la onda sale del hoyuelo); **PIE 33 s**: 25 latidos cardíacos → pulsos cada 2,0 s exactos (19,5 / 21,5 / 23,5), `Beat` y `BeatP` coherentes en los tres MIDs, 12 esferas (una por pulso), `SpacingS` 844 (= 2 s · 420), espectador (−600, 0), 0 `Accessed None`. APK instalado 23:11. **Medido en visor (23:15, 45 s): 72-73 fps sostenidos, App 9,1-11,8 ms (mediana ≈ 11,0), GPU 76-87 %** — igual que la v5 (el preludio de 3 latidos y el pulso por esfera no se notan; la rama de esferas perdió atan2 y colinas).
- ⚠ `GetActorOfClass` en el Construction Script **falla en el mundo de la miniatura** que arma `save_assets` (no hay PlayerStart): "Accessed None" que la tool devuelve como error aunque el guardado se haga. Arreglo: función aparte con `IsValid` (`FindViewer`).

## 🔌 Enganche al sensor del pecho (2026-09-29)
- **`BeginPlay`**, después de `BootOrbs`: `GetActorOfClass(BP_HeartManager_SC)` → `IsValid` → `Assign OnHeartBeat` → evento `OnHeartBeat_Event` → `OnHeartBeat(-1.0)`. Hecho por cirugía de nodos: el `Assign` se creó con `declaring_class` del manager, porque este BP también tiene una función `OnHeartBeat` (gotcha 175).
- 🔴 **Se usa -1, no 1.0.** Con una intensidad ≤ 0, `EmitPulse` usa `DemoI` (el `PreviewIntensity` del MI) con su variación, que es la intensidad **aprobada en visor**. Con 1.0 empujaría más fuerte que lo aprobado.
- **Un solo divisor:** el manager emite a ritmo cardíaco (`BeatDiv` 1) y la membrana divide (`BeatDivider` 2).
- En `Test_Heart` la instancia quedó con `bDemo` = false. Sin manager en el nivel no pasa nada (el `IsValid` lo corta).
- ✅ **PIE:** manager con `bFakeBeat` y zona forzada → un latido por segundo, `LastBeat − PrevBeat` = 2,0 s en la membrana, 0 `Accessed None`.

## 🌅 Contrato de etapa: esfera que brota, pulso con cada latido, paleta blanca-rojiza (2026-09-30, noche del nivel final)
Pedido de Beltrán (audio de las 04:30, vía Narrativa):
- el pulso visual salía "uno por medio";
- paleta blanca-rojiza, surreal, nada azul (el azul es de la respiración);
- antes de las instrucciones, solo el mar;
- la esfera aparece en las instrucciones y se va animada al final.

**El bug del "uno por medio".** La membrana dividía por `BeatDivider` 2, la regla vieja del "pulso a la mitad del ritmo", superada. Además la instancia tenía `bDemo` en **true**, así que metía latidos propios sin sonido.
- Ahora `BeatDivider` = **1** (instancia y CDO) y `bDemo` = **false** en la instancia.
- Verificado en PIE: `LastBeat − PrevBeat` = 1,00 s con el manager a 60 lpm.

**La esfera brota del agua.** Se usa el parámetro `HeartZ` en los MIDs de `Heart` y `Membrane` (la membrana lo usa para la luz de la esfera). La membrana es opaca, así que debajo del agua la esfera no se ve.
- **`SphereGo(D)`** (pública): `D` = 1 sube, −1 se hunde, 0 la oculta al instante (`EntryT` 0 + `EntryApply`).
- **`EntryStep(DT)`**, en el Tick después de `PushBeat`: el `DT` entra por `Min(DeltaSeconds, 1/30)`, regla del director para que un cuadro trabado no se coma la entrada. Avanza `EntryT` a razón de `EntryDir / EntryTime` y se detiene en 0 o en 1.
- **`EntryApply()`**: `HeartZ = lerp(hide, HeartHeight, e)`.
  - `e` es easeOutBack con c1 1,2: `1 + 2,2·m³ + 1,2·m²`, con `m = EntryT − 1`. Pasa ~5 % de largo y se asienta, como algo que flota.
  - Al revés (salida), la misma curva da primero un impulso hacia arriba y después se hunde.
  - `hide = −(1,5·HeartSize + HeartFloat + 10)`.
- Variables nuevas: `EntryT` (Z - Interno, default **1** = visible, para que el modo libre no cambie), `EntryDir` (Z - Interno), `EntryTime` (perilla, 2,5).
- Quién la llama: [[BP_HeartManager_SC]] vía `ScapeGo(D)`.
  - `BeginPlay` con TOUR o `bContractTest` → 0.
  - `StageIntro` → 1.
  - `StageOutro` → −1.
  - `TourWake` → 1.

**Paleta** (perillas de la instancia en `Test_Heart`, valores lineales, antes → después):
| Perilla | Antes | Después |
|---|---|---|
| `ColorLight` | 0.896 / 0.411 / 0.331 | 0.96 / 0.84 / 0.80 |
| `ColorShadow` | 0.195 / 0.266 / 0.491 | 0.34 / 0.07 / 0.09 |
| `ColorSheen` | 0.913 / 0.930 / 1.0 | 1.0 / 0.92 / 0.88 |
| `ColorGlow` | 0.318 / 0.419 / 1.0 | 1.0 / 0.34 / 0.28 |
| `ColorCrest` | 0.760 / 0.810 / 1.0 | 1.0 / 0.78 / 0.72 |
| `HeartColorCore` | 0.939 / 0.947 / 1.0 | 1.0 / 0.62 / 0.56 |
| `HeartColorRim` | 0.479 / 0.552 / 1.0 | 1.0 / 0.52 / 0.48 |
| `SkyColorHorizon` | 0.672 / 0.716 / 0.823 | 0.95 / 0.85 / 0.83 |
| `SkyColorGlow` | 0.855 / 0.768 / 0.823 | 1.0 / 0.82 / 0.76 |

- Sin tocar: `HeartColor`, `HeartColorShadow` y `SkyColorTop` (ya eran rojizos). Tampoco los valores de Beltrán: `HeartPush` 24,4, `OrbAmoeba` 0,08, `HeartSize` 68,1 y `HeartHeight` 113, que él subió desde el 09-29.
- Captura del viewport desde el ojo del usuario: `VR_Test/Saved/ClaudeScripts/Heart/cap_palette2.png`. Mar blanco-rosado, cielo rojizo arriba, esfera roja como foco. ⬜ Visor.
- Respaldo de TODOS los valores de la instancia antes de tocar la estructura (gotcha 402): `Saved/ClaudeScripts/Heart/dump_0930_actors.json` y `dump_0930.json` (componentes).

## Pendiente
1. **Nivel `Test_Heart` + PIE** (normal y Simulate) cuando el editor esté libre; verificar por log que `Wave0..7` y `Beat` cambian en el MID.
2. Juicio de Beltrán en el viewport (la instancia anima sola) y en el visor.
3. **Fase 4**: esferas que emergen (ISM, `Part` 3, `PerInstanceCustomData`). Los `Bump0..3` ya están cableados en el VS y apagados (`Bump.z` = 0).
4. Medir con el banco (modos: todo / sin membrana / sin línea de cresta (`LineGlow` 0) / nada).
5. ~~Enganche al manager~~ ✅ hecho el 2026-09-29 (ver abajo).

## Session log
- **2026-09-27** — fases 1 a 3 construidas sin abrir niveles. Decisiones que cambiaron respecto del plan: (a) **un solo master con `Part`** en vez de materiales separados, para tener **una sola superficie de autoría**; (b) **MIDs en vez de `MPC_Heart_SC`** (no es global y esquiva la gotcha 416 del `ParameterId`); (c) la autoría de la forma vive en la **MI** (rangos y descripciones gratis), no en variables del actor. Gotchas nuevas: 446-452.
- **2026-09-29** — enganchado a `BP_HeartManager_SC` en `Test_Heart` (con `BP_BioHub` y el manager colocados); `bDemo` apagado en la instancia. Verificado en PIE.
- **2026-09-30** — contrato de etapa (esfera que brota/se hunde con `SphereGo`), `BeatDivider` 1 y `bDemo` false (pulso con cada sonido), paleta blanca-rojiza. PIE ok con el contrato del manager.
- **2026-09-29** — decisiones de Beltrán: **esfera central SUAVE** (lóbulos 2,6/3,4/2,0/4,2, la del disco y el commit; no la "coliflor" del APK de las 23:11), y **que se hunda un poco en el agua tras el empuje es intencional** (sale de la lista de robustez v7).

## 🌀 2026-10-01 — LA VUELTA (pedido directo de Beltrán)
*"Empezar a elevarnos y a rotar alrededor de este océano. Muy suave. Siempre mirando al centro… bajar el océano y las lunas… a la mitad de la etapa, por cantidad de pulsos… que termine de dar una vuelta completa."*
- **Por qué mover el ACTOR:** los 5 Custom (`HeartScapeVS/HeightVS/GradVS/XVS/PS`) trabajan en espacio LOCAL con centro en la esfera. Rotar el actor en su origen = orbitar el centro mirándolo; bajarlo = subir. El pawn, Alma, HUD y manos no se mueven y quedan como referencia fija (menos mareo). Root `Movable` (verificado).
- **Perillas (cat. `5 - Vuelta`, editables):** `OrbitTime` 60 s · `OrbitRise` 400 cm · `OrbitSpin` 1 (vueltas y sentido: +1 antihoraria, −1 horaria). Estado (`Z - Interno`): `OrbitT`, `OrbitOn`, `OrbitBaseLoc`, `OrbitBaseRot`.
- **`OrbitGo()`** (la llama el manager): si no empezó, guarda la base (`GetActorLocation/Rotation`, respeta el offset de LevelInstance) y prende.
- **`OrbitStep(DT)`** (Tick, después de `EntryStep`, DT del `Min` 1/30): `OrbitT += dt/OrbitTime` → **smootherstep** `e = u³(10 − 15u + 6u²)` (velocidad Y aceleración 0 en los extremos) → `SetActorLocationAndRotation(base − (0,0,OrbitRise·e), yaw base + 360·OrbitSpin·e)` → `FindViewer()` (la regla del espectador de las lunas usa el viewer en LOCAL: al rotar el actor hay que recalcularlo) → a `u = 1` apaga y loguea `HEART: termino la vuelta`.
- **`OrbitReset()`**: vuelve a la base (teleport) y `OrbitT` 0.
- Velocidades con 60 s: giro medio 6°/s, pico 11,2°/s; subida pico 12,5 cm/s. ⬜ PIE y visor.

## 🌀 2026-10-01 (2) — vuelta que se aleja y regresa + lunas que llenan el cielo + polvo
Pedido de Beltrán tras probar la vuelta (*"va bien, me gusta"*): que la vuelta se aleje del centro; que tras los 360° vuelva suave a su lugar; muchas más lunas, una por pulso, que se llene, a todas las distancias (cerca, lejos, horizonte) para sentir espacialidad; lunas low poly con menos warp; partículas y polvo que ayuden a entender el giro. Condición: **72 fps en Quest**.

### Vuelta en DOS fases con una sola variable
- `OrbitT` va de 0 a 2. Fase 1 (0..1) dura `OrbitTime` (60 s); fase 2 = regreso (1..2) dura `ReturnTime` (20 s).
- `e1 = smootherstep(min(T,1))` · `e2 = smootherstep(max(T−1,0))` · `a = e1·(1−e2)`.
- Ubicación = `base − (dir.x·OrbitAway·a, dir.y·OrbitAway·a, OrbitRise·a)`; yaw = `base + 360·OrbitSpin·e1` (el giro se queda en 360° durante el regreso).
- A `T = 2` apaga y loguea `HEART: el mar volvio a su lugar`.
- `OrbitAwayDir` (Z - Interno): en `OrbitGo` = `Normalize(TransformDirection(transform del actor, (ViewerX, ViewerY, 0)))` = dirección centro→espectador. Mover el actor en −dir aleja el centro del espectador, que lo sigue mirando de frente. `OrbitGo` llama `FindViewer` antes y loguea `HEART: el mar empieza la vuelta`.
- Perillas en `5 - Vuelta`: `OrbitTime` 60 s · `OrbitRise` 400 cm · `OrbitSpin` 1 · **`OrbitAway` 600 cm** (nueva) · **`ReturnTime` 20 s** (nueva).

### Lunas que llenan el cielo
| Qué | Antes | Ahora |
|---|---|---|
| Pool `OrbMax` en `MI_HeartScape_SC` (el actor lo lee de `LookMI`) | 24 | **120** |
| Malla del template `Echoes` del CDO | `SM_HeartOrb_SC` (642 vértices) | **`SM_HeartOrbLo_SC`** (icoesfera subdiv 3, 162 vértices / 205 con costuras; `scripts/gen_heart_orb_lo.py`) |
| Vértices totales | 24 × 642 ≈ 15,4k | 120 × 162 ≈ **19,4k** |
| Límites de la malla | — | ampliados a ±5500 XY, +1800 / −300 Z |

- `SM_HeartOrb_SC` queda intacta para volver atrás.
- `SpawnOrb`: el sorteo del radio pasó de `lerp(SpawnMin, SpawnMax, sqrt(rand))` (uniforme en área, casi todas lejos) a `lerp(SpawnMin, SpawnMax, rand^SpawnBias)` con **`SpawnBias` 2** (perilla nueva en `4 - Esferas que emergen`): más densas cerca, cada vez más raras hacia el horizonte. Cirugía: se borró el nodo Sqrt y se puso un Power.
- Instancia de `Test_Heart`, antes → después:

| Perilla | Antes | Después |
|---|---|---|
| `OrbLife` | 20 | 90 |
| `SpawnMin` | 300 | 250 |
| `SpawnMax` | 1500 | 5000 |
| `OrbClearance` | 500 | 350 |
| `OrbAmoeba` | 0,08 | 0,04 (valor de Beltrán: menos warp para que no se note el low poly) |
| `AmebaMix` | 0,489 | 0,25 |

- Con vida 90 s y pool 120, la condición de reciclado `(OrbLife + SpawnMax/Speed + PushT + 1)/OrbCount` ≈ 0,8-1 s deja nacer una luna por latido hasta ~70 lpm.

### Polvo
- **`BootDust()`** (en `BeginPlay`, después de `BootOrbs`) spawnea [`BP_HeartDust_SC`](BP_HeartDust_SC.md) con `Owner = self` y lo pega al `DefaultSceneRoot` (SnapToTarget ×3) → `DustRef`.
- `EventEndPlay` → **`DustEnd()`** lo destruye (quien spawnea destruye).
- La membrana mide ±600 m, alcanza para lunas a 50 m.

### Pendiente
- ⬜ Look y **72 fps en visor/APK** (OVR Metrics) con 120 lunas + polvo. ⬜ PIE del regreso completo.
- 🔴 **El pool estaba TOPADO a 32** en `SeedOrbs` (`Clamp(Integer)(round(OrbMax), 1, 32)`): con `OrbMax` 120 en la MI igual salían 32 y nacía una luna cada dos latidos. Tope subido a **160** (set_pin_value). ✅ PIE: `OrbCount` 120 y 14 lunas en 14 latidos; vuelta + regreso de prueba (12 + 6 s) = 18,0 s entre `el mar empieza la vuelta` y `el mar volvio a su lugar`, vuelve exacto a la base, 0 Accessed None.

## 🌙 2026-10-01 (3) — ajustes de Beltrán tras probar: vuelta más lenta, regreso más ágil, lunas grandes y blancas en el fog, polvo rojizo
- **Curvas de la vuelta: smootherstep → smoothstep** (`3u² − 2u³`), en fase 1 y en el regreso: menos "cola" lenta al final de cada tramo (Beltrán: "la vuelta muy rápida y la bajada lentísima"). CDO/instancia: `OrbitTime` 60 → **90** s (giro medio 4°/s, pico 6°/s) · `ReturnTime` 20 → **14** s.
- **Color propio de las lunas**: `OrbColor` (1, 0,95, 0,93) · `OrbColorShadow` (0,80, 0,66, 0,66) · `OrbRimColor` (1, 0,92, 0,90), editables en `4 - Esferas que emergen`. `OrbTint()` (al final de `ApplyLook`) escribe `HeartLit`/`HeartShadow`/`HeartRimColor`/`HeartCore` SOLO en el MID de `Echoes`; la esfera central sigue con sus colores.
- **Instancia de Test_Heart, antes → después**: `SizeMin` 8 → 60 · `SizeMax` 60 → 200 (lunas grandes) · `AmebaMix` 0,25 → 0 · `OrbAmoeba` 0,04 → 0 (redondas, "menos ovaladas") · `SpawnMin` 250 → 1700 (siempre por fuera del espectador, que llega a 1200 del centro) · `SpawnMax` 5000 → 6000 · `SpawnBias` 2 → 1 · `OrbClearance` 350 → 500 · `OrbRiseRamp` 2,5 → 6 (arrancan a subir más suave). El fog del mar (`FogStart` 900, `FogDistance` 5200) las envuelve: "lunas entremedio del fog".
- Límites de `SM_HeartOrbLo_SC` → ±6600 XY, +2000/−300 Z.
- Polvo (`MI_HeartDust_SC`): `DustAlpha` 0,22 → 0,45 · `DustSizeDeg` 0,10 → 0,16 · `DustColor` (1, 0,88, 0,84) → (1, 0,52, 0,46) · `SparkAlpha` 0,55 → 0,8 · `SparkSizeDeg` 0,2 → 0,3 · `SparkColor` (1, 0,72, 0,66) → (1, 0,62, 0,55) · `SizeMinDeg` 0,07 → 0,1.
- ✅ PIE: lunas a ~37 m con radio ~1,8 m, una por latido; 0 Accessed None. ⬜ visor.

## 🎛️ 2026-10-01 (4) — perillas del POLVO en el mar (pedido de Beltrán: "para poder ajustar y explorar")
- Categoría **`7 - Polvo y particulas`** (editables, en el actor del mar): `DustAlpha` 0,45 · `DustSize` 0,16° · `DustColor` (1, 0,52, 0,46) · `SparkAlpha` 0,8 · `SparkSize` 0,3° · `SparkColor` (1, 0,62, 0,55) · `SparkTwinkle` 0,6 · `DustSizeMin` 0,1° · `DustSizeVar` 0,35 · `DustDrift` 6 cm · `DustDriftSpeed` 0,18 · `DustNearFade` 60 cm · `DustFarFade` 2600 cm · `DustGlow` 1.
- **`DustLook(C: MeshComponent)`** escribe las 14 en el material de C. La usan: el polvo de Play (`BP_HeartDust_SC.DustDrive`, cada cuadro → se ajusta EN VIVO en el actor del mar del mundo PIE) y la vista previa del editor (**`DustPreview()`**, al final del Construction Script: `GetActorOfClass(BP_HeartDust_SC)` → `DustLook`; protegido con `IsValid`, gotcha 467).
- **`Polvo_Preview`** (BP_HeartDust_SC con `bPreviewOnly` true) colocado en Test_Heart, colgado del `DefaultSceneRoot` del mar en (0,0,0) relativo: se ve en el viewport sin Play y se destruye al dar Play (el polvo real lo spawnea el mar). Test_Heart: 17 → 18 actores.
- ⚠ Al colocar con `parent`, el `xform` se toma RELATIVO al padre (quedó en 1200,0,−40) → se corrigió `relativeLocation` con la forma de string `(X=..,Y=..,Z=..)` (la de dict no aplica, gotcha de toolsets).
