# BP_ChladniFloor_SC — el salar de Chladni (entorno de Attracting)

`/Game/SoulCharger/Mechanics/Sequencer/Chladni/` · plan: [`docs/PLAN-SALAR-CHLADNI-2026-09-28.md`](../../../../docs/PLAN-SALAR-CHLADNI-2026-09-28.md) · lookdev en navegador (v6, la aprobada para portar): `docs/prototipos/placa-chladni.html` · https://claude.ai/artifact/EUUZzbNmfxfHsZhrcE1C2P

## Propósito
El piso y el cielo de la etapa del secuenciador. Un salar de Uyuni pastel al ocaso (estética Six N. Five), con polígonos de sal y grano de granito. **Al empezar cada vuelta del secuenciador**, lo que se agregó o sacó en la mesa entra al patrón de una vez: la membrana hace **una ola** con la forma de las figuras de Chladni nuevas (la curva de Heart) y deja el mandala en **relieve de geometría**, como las ondas de Heart. Cada slot tiene su figura; todas comparten la simetría 5. Centro calmo alrededor del usuario (los pétalos nacen a un radio), deformación orgánica fija.

## Estado (2026-09-28)
| Pieza | Estado | Evidencia |
|---|---|---|
| Material `M_ChladniFloor_SC` | 🟢 compila | 69 expresiones (52 parámetros + 15 helpers + 2 Custom); 29/29 y 54/54 entradas conectadas; log sin errores después del último recompile (ES31 y SM6) |
| Textura `T_SaltCells_SC` | 🟢 | 1024², 8×8 celdas, periódica; lineal, `TC_Grayscale`, sin mips, wrap |
| Blueprint | 🟢 compila con warnings como errores | grafos releídos; tipos de `CommitSlot` confirmados con `get_node_infos` (el read los rotula mal por nombres compartidos) |
| Nivel `/Game/Test_Sequencer` | 🟢 colocado | `GAL_12_ChladniFloor` en la PlayerStart (362700, 100000, 0); 25 actores; **`BP_Ganzfeld_SC` oculto** (Shell `bVisible` false + actor `bHidden`, pedido de Beltrán "para que no consuma") |
| Viewport | 🟢 visto por captura | cielo pastel con sol, polígonos hacia el horizonte, mandala en relieve (previa de 3 notas), granito |
| PIE | 🟡 | encuentra solo al secuenciador, sigue `CurrentStep`, corre `Commit` en cada paso 0 sin errores, mesa vacía = polígonos; 0 `Accessed None`. ⬜ **colocar una esfera real no se pudo simular** (`Occupant` no es editable por MCP): lo prueba Beltrán |
| Visor / medición | 🟢 | 2026-09-29: **11,43 ms, 72 fps** en el peor caso (8 figuras) con el banco `quest_chladni_perf.ps1`; ver la sección del banco al final |

## Qué se toca dónde (panel Details del actor)
| Categoría | Perilla → parámetro | Qué hace |
|---|---|---|
| **1 - Figura** | `Symmetry`→`Sym` 5 · `RadialFreq`→`Kr` 3,5 · `BaseRings`→`BaseW` 0,3 | simetría, anillos, peso de los anillos base |
| | `PlateRadius`→`PlateR` 720 · `PlateCenterX`→`CenterX` 0 | radio y centro del mandala (cm, local) |
| | `CenterCalm`→`Calm` 160 · `Organic`→`Warp` 0,5 | centro calmo (cm) · irregularidad orgánica |
| | `ReliefHeight`→`ReliefH` 7 · `ReliefWidth`→`ReliefW` 0,22 | alto (cm) y ancho de las lomas del mandala |
| **2 - Cambio** | `bChangeOnLoop` ✅ | cambia al empezar cada vuelta (apagado: con cada paso en que cambió la mesa) |
| | `WaveHeight`→`VibAmp` 8 · `FormTime` 1,6 · `FormDecay` 5 | alto de la ola (cm) · tiempo de formación (s) · erosión al sacar la esfera (s) |
| | `PolygonsFade` 1 · `PreviewNotes` 3 | cuánto borra el mandala a los polígonos · figuras que muestra la previa del editor |
| **3 - Salar** | `SaltLit`/`SaltShade` · `FlatTone` 0,7 · `LightGain` 1,6 | colores de la sal · tono del plano · contraste de la luz rasante |
| | `PolygonRidges`→`PolyH` 0,55 · `PolygonWidth`→`PolyW` 5 · `CellSize` 150 | polígonos (0 = desierto liso) |
| | `SaltNoise` 0,3 · `Wetness`→`Wet` 0,45 | manchas · agua que refleja el cielo |
| **4 - Grano** | `Grain` 0,6 · `GrainSize` 0,3 · `Granite` 0,6 | grano fino y motas de granito (redondas) |
| **5 - Cielo** | `SkyTop`/`SkyMid`/`SkyHorizon`/`SunColor` · `SunAzimuth` −24 · `SunElevation` 2,5 · `SunSize` 7 · `SunGlow` · `Haze` · `FogDistance` 2600 | cielo pastel, sol, bruma |
| **6 - Enlace** | `Sequencer` | vacío = lo busca solo (`GetActorOfClass`) |

`Dither` (1) y el grupo `9 - Interno` (`Part`, `Order`, `W0..W7`, `V0..V7`) viven solo en el material: los escribe el actor.

## Componentes
`DefaultSceneRoot` · `Floor` (`SM_HeartMembraneLite_SC`, la malla de Heart: 192 sectores, 32.641 vértices, detalle hasta 60 m) · `Sky` (`/Engine/BasicShapes/Sphere` × 240 = radio 120 m: queda **dentro** del Ganzfeld de 135 m). Los dos sin sombra, material `M_ChladniFloor_SC`, colisión apagada en el Construction Script. Escala del actor = 1.

## Registro de variables internas (`Z - Interno`)
| Variable | Rol |
|---|---|
| `Shown[8]` bool | qué slots forman parte del patrón que SE VE; se actualiza solo en `Commit` |
| `FormT[8]` | objetivo de talla: 1 al entrar al patrón; se erosiona con `FormDecay` cuando el slot sale |
| `FormW[8]` | la talla suavizada (sube con la ola) → `W0..W7` |
| `PulseAge[8]` | segundos desde la última ola de cada slot → `V0..V7 = g(PulseAge/rise)`, `g(x) = x²·e^(2(1−x))`, `rise = FormTime/2` |
| `LastStep` int | último `CurrentStep` visto (detecta el cambio de paso) |
| `FormSum`, `bChanged` | acumulador del `Order` · si `Commit` cambió algo |

## Estructura de grafos (una función por responsabilidad)
- **Construction Script**: colisión off ×2 → `Part` 0 (piso) / 1 (cielo) → `LookTo(Floor)` → `LookTo(Sky)` → `PushPreview`.
- **BeginPlay**: `Resize` ×4 a 8 → `PulseAge` = 99 → `LastStep` = −1 → `FindSequencer`.
- **Tick**: `StepFloor(DeltaSeconds)`.
- `LookTo(C)`: las 32 perillas de look al material del componente (`Set{Scalar,Color}ParameterValueOnMaterials`).
- `PushPreview()`: `W0..W(PreviewNotes−1)` = 1, `V` = 0, `Order` por fórmula. Así el mandala se ve en el viewport sin Play; en Play lo pisa `StepFloor` desde el primer cuadro.
- `StepFloor(DT)`: `Sense` → por slot: edad, erosión (`select`, sin rama), talla, `W<i>`, `V<i>`, suma → `Order = min(1, 1 − e^(−Σ·1,4·PolygonsFade))`.
- `Sense()` → si `Sequencer` es válido → `SenseStep()`: si `CurrentStep` cambió → `LastStep` → si es 0 (o `bChangeOnLoop` apagado) → `Commit()`.
- `Commit()`: `bChanged` = false → si hay 8 slots: `CommitSlot(s)` ×8 → si cambió: `PulseAge` = 0 de los slots que se muestran (UNA ola para toda la figura nueva).
- `CommitSlot(S)`: `IsValid(Sequencer.Slots[S].Occupant)` → `SetShownSlot(S, Want)`.
- `SetShownSlot(S, Want)`: si difiere → `Shown[S]`, `bChanged`, `FormT[S]` = 1 si entra.
- `FindSequencer()`: si no hay referencia, `GetActorOfClass(BP_Sequencer_SC)`.

## El material
Generado desde una fuente: **`scripts/gen_chladni_material.py`** escribe `scripts/hlsl/ChladniHeightVS.hlsl`, `ChladniPS.hlsl` y `VR_Test/Saved/ClaudeScripts/chladni_build.json`; **`scripts/apply_chladni_material.py`** (idempotente) arma el material en Unreal por `execute_tool_script`. Para cambiar el shader: editar el generador, correrlo, y volver a aplicar (o solo actualizar `Code` de los dos Custom si las entradas no cambian).
| Nodo | Salida | Qué calcula |
|---|---|---|
| `ChladniHeightVS` (29 entradas) | → Transform Local→World → **WPO** | la altura: relieve `ReliefH·orden·e^(−(F/ReliefW)²)` + ola `VibAmp·Σ V_i·modo_i`. Sale en 0 si no hay nada activo o fuera de la placa (ramas coherentes) |
| `LocalPosition` → `VertexInterpolator` | `LPi` | posición local para el PS |
| `ChladniPS` (54 entradas) | → **Emissive** | cielo (`Part` 1) · piso: la misma altura con su pendiente por diferencias finitas, polígonos (3 lecturas de `T_SaltCells_SC`), luz rasante, manchas, grano y granito, agua (Fresnel), bruma por distancia real, dither |
Los 8 modos van **desplegados** (gotcha 399), hash sin seno (gotcha 481). Unlit, opaco, two-sided, `MFPM_Full_MaterialExpressionOnly`.

## Trampas de esta construcción
- 🔴 **`execute_tool_script` corre el script DOS veces** (gotcha 489): el `add_variable` duplicó las 43 variables con sufijo `_0`. Todo script tiene que ser idempotente.
- `read_graph_dsl` rotuló `Slots`/`Occupant` como de `BP_AttractDirector`/`BP_SeqSlot` (clases viejas con los mismos nombres): los pines reales son de `BP_Sequencer_SC`/`BP_SeqSlot_SC`.
- En el HLSL generado, `r0` chocaba entre el radio sin deformar y el de la evaluación "0": los sufijos de evaluación son `A/B/C` y el radio sin deformar es `rp`.

## TODO
- [ ] Beltrán: colocar esferas en PIE/visor y ver que el patrón cambie al empezar la vuelta.
- [x] Medir en la Quest: 25,5 → 11,43 ms (2026-09-29, banco + gradiente analítico + ángulos múltiples).
- [ ] Paleta pastel para esferas y gusano (Beltrán la autorizó; no se tocaron sus valores).

## 2026-09-28 (noche, 2a pasada) — pedidos de Beltrán al verlo en el editor
*"El patrón con relieve debe ser más delgado · hay un cambio de patrón muy notorio y feo · la textura es muy matemática, debe ser más como arena"*; después: *"se sigue viendo pintado más que con relieve; si el relieve es más puntoso se nota mejor · los patrones de Chladni se ven mejor un poquito más geométricos, un entremedio con la geometría del salar"*.
- **Líneas finas y con filo**: la línea va **por pixel** con perfil **triangular** elevado a `Sharp` (filo en la cresta: parte la luz en lado al sol / lado en sombra → se lee como relieve). La geometría solo lleva una loma suave (`SwellH` 1,5 cm, `SwellW` 0,3): una línea de ~5 cm por vértices saldría facetada. Los polígonos también con filo. `LightGain` 2,2.
- **Sin costura mandala/polígonos**: borde del mandala ancho e irregular (`EdgeIn` 0,5 → 1,08 del radio, con ondulación angular) y los polígonos quedan tenues adentro (`PolyKeep` 0,15).
- **Centro calmo sin anillo**: el relieve del mandala se apaga dentro del centro calmo (`ordL *= smoothstep(calm·0,8, calm·1,6, rp)`): bajo el usuario queda el salar natural. (Poner `F` constante adentro NO sirve: crea un anillo nodal justo en el borde del centro calmo.)
- **Más geométrico**: cada modo mezcla (`Geo` 0,8) la onda de placa redonda con **5 ondas triangulares** (lineales a tramos → líneas nodales RECTAS con esquinas) y los anillos con un **radio pentagonal**. `GeoFreq` 1,8 = celdas de ~2,5 m, cerca de los polígonos. `Warp` bajó a 0,15.
- **Arena**: `T_SandGrain_SC` (`scripts/gen_sand_texture.py`: ruido a 4 escalas + granos sueltos oscuros/claros, periódica, con mipmaps; R = arena, G = granos oscuros, B = claros; `TC_Masks`, sin sRGB). Dos lecturas (parche de `GrainSize` 80 cm y 190 cm girada). Reemplaza las motas calculadas (se veían "matemáticas" y cuadradas).
- **Perillas nuevas en el actor** (agregadas a `LookTo` por cirugía de nodos): `SwellHeight`, `EdgeStart`, `PolygonsInside`, `Geometric`, `GeoFrequency`, `CrestSharpness`. Defaults nuevos: `ReliefHeight` 4, `ReliefWidth` 0,06, `GrainSize` 80, `Organic` 0,15, `LightGain` 2,2 (CDO e instancia).
- Material: 60 parámetros; `ChladniHeightVS` 35 entradas, `ChladniPS` 62; compila limpio (ES31 y SM6).
- **3a pasada** (*"ahora quedó como pixelado, debe ser un entremedio"*): las ondas triangulares puras dejaban esquinas vivas y mesetas planas donde se cruzaban. Ahora son **triangulares redondeadas** `asin(k·cos x)/asin(k)` con `k = 1 − Round` (rectas en el medio, esquinas redondas; `Round` 0,25, solo en el material) y `Geometric` bajó a **0,55**. ⚠ Costo: con `Geo` > 0 cada modo activo evalúa 5 `asin` por evaluación y el PS hace 3 evaluaciones → medir en la Quest; si pesa, hornear el campo o bajar a 1 evaluación con gradiente analítico.
- **4a pasada — Beltrán eligió "Recto (Chladni geométrico)"** (*"se están mezclando dos patrones, uno recto y otro ondulado; hay que decidirse por uno"*). (1) **Ancho de cresta por DISTANCIA real** a la línea nodal (`dcm = F/|∇F|`, `ReliefW` ahora en cm, 3): todas las crestas iguales, sin manchones donde la figura es plana (eso era el "pixelado"). (2) **Mandala recto como UNIÓN de líneas** (`geo_eval` del generador): cada nota agrega **pentágonos concéntricos** (su espaciado `Kr·GeoFreq·MK`, girados 0/36°) y **rayos** (`Sym·MA`); distancia exacta a cada recta → crestas rectas y uniformes; `G = max` sobre las notas. La pendiente sale de diferencias finitas de medio cm. La ola de formación sigue usando el campo Chladni (`V`). `Geometric` 1 = solo el recto; 0 = el Chladni curvo de antes. (3) `PolygonsInside` 0: dentro del mandala no quedan polígonos del salar; afuera sí (mismo vocabulario recto). (4) Loma de geometría mínima (`SwellHeight` 0,5; en el VS la loma sigue al patrón recto con ancho ×4).
- 🔴 `AssetTools.read_file` **no lee más de 80 KB**: el plan con el código adentro ya pesaba 85 KB y el script falló. Ahora el código va en `VR_Test/Saved/ClaudeScripts/chladni_code_<Custom>.txt` y el plan lo referencia (`code_file`). (El script fallido no se llevó nada: canario 25 actores y valores releídos.)
- **5a pasada — el recto NO** (*"qué horripilancia es eso. Todavía hay dos patrones. Mejor volvamos al ondulado"*). `Geometric` = **0** (Chladni curvo; el camino recto `geo_eval` queda en el shader, apagado, por si alguna vez se quiere) y `Organic` 0,4. **Un solo patrón adentro**: los polígonos se apagan en TODO el mandala, centro calmo incluido (`ordP`, sin el factor del centro calmo); bajo el usuario queda arena lisa. Se conservan de la 4a: ancho de cresta por distancia real (`ReliefWidth` 3 cm) y filo (`CrestSharpness`). Lección: el "entremedio" pedido no era mezclar dos vocabularios en el mismo lugar; cada zona tiene UNO (adentro ondulado, afuera polígonos).

## 2026-09-28 (noche) — paleta pastel para esferas y gusano en `Test_Sequencer` (autorizada por Beltrán)
Se conservó el TONO de cada color que él eligió; solo se bajó la saturación y se subió la luminosidad (HSV en sRGB, sat ×0,42, valor ≥ 0,93). Valores ANTERIORES de las instancias, para volver:
- `GAL_12_OrbDirector` (`BP_OrbDirector_SC_C_0`): `Color1` (0.0717, 0.1254, 0.5990) · `Color2` (0.8229, 0.6055, 0.1534) · `Color3` (0.8500, 0.2424, 0.1114) · `Color4` (0.3413, 0.0479, 1.0) · `ShadeColor` (0.4271, 0.6458, 0.4626) · `ShadowColor` (0, 0.2105, 0.3) · `Brightness` 1.317836.
- `GAL_12_BlobChain` (`BP_BlobChain_SC_C_2`): `ColorLow` (0.2865, 0.1461, 0.0716) · `ColorHigh` (0.5775, 0.6, 0.5219) · `ChainBrightness` 1.538552.
Nuevos: `Color1` (0.4267, 0.4920, 0.8481) #afbaed · `Color2` (0.8481, 0.7490, 0.4794) #ede0b8 · `Color3` (0.85, 0.5420, 0.4401) #edc2b1 · `Color4` (0.6739, 0.4225, 1.0) #d6aeff · `ShadeColor` (0.5409, 0.6458, 0.5590) · `ShadowColor` (0.342, 0.479, 0.604) · `Brightness` 1.0 · gusano `ColorLow` (0.456, 0.386, 0.672) #b4a7d6 · `ColorHigh` (0.965, 0.807, 0.737) #fbe8df · `ChainBrightness` 1.1. (`OrbColors` del secuenciador no se tocó: es el respaldo cuando no hay director.)
- 2a vuelta de color (la primera dejaba las esferas grisáceas y el gusano perdido sobre la sal): director `ShadeColor` (0.485, 0.393, 0.694) lavanda tibia · `ShadowTint` 0,3 (era 0.517923) · `Brightness` 1,15 · gusano `ColorLow` (0.33, 0.26, 0.54) · `ColorHigh` (0.92, 0.69, 0.60) · `ChainBrightness` 1,25. Nivel guardado, 25 actores.
- 3a vuelta (esferas grises): la causa estaba en el material de la esfera, no en la paleta — ver `BP_OrbDirector_SC.md` §"por qué las esferas se veían GRISES". Instancia del director: `OwnShade` 1, `OwnShadeDepth` 0,7, `ShadeFloor` 0,45 (era 0.03626), `ShadowTint` 0,15.

## ⏳ PREPARADO (2026-09-29), falta aplicar en Unreal — ideas 1 y 2 de Beltrán ("Adelante. Arma cuando termine Breath")
El editor lo tiene la sesión Breath. Lo que NO necesita editor ya está hecho:
- **Generador** (`gen_chladni_material.py`, respaldo previo en `%TEMP%/gen_chladni_v13.py`): grupo `5 - Gusano` → `WormShadow` 0,35 · `ShadowElev` 22° · `ShadowSoft` 1 · `WormGlow` 0,2 · `WormR` 14 cm · `WormCol` #f0c9d6, y `WS0..WS7` (posición local de cada slot; z < 0 = no hay). En el PS: por slot, **sombra elíptica larga** hacia el lado contrario al sol (largo = altura / tan(`ShadowElev`)) teñida al tono de sombra de la sal, y **reflejo** suave de `WormCol` justo debajo. 8 gotas desplegadas (gotcha 399). PS: 77 entradas; 75 parámetros.
Pasos al soltar el editor:
1. `apply_chladni_material.py` completo (hay parámetros nuevos) → recompile limpio (log por línea).
2. **BP del piso**: variable `WormSlots` (array de `BP_SeqSlot_SC`) llenada por `GetAllActorsOfClass` en el Construction Script (previa en el editor) y en BeginPlay; función `PushWorm()` (Construction + Tick): por slot `SetVectorParameterValueOnMaterials(Floor, "WS"+i, slot.GetActorLocation − ActorLocation)`. Perillas en el actor: `WormShadow`, `ShadowElevation`, `WormGlow` (cirugía en `LookTo`).
3. **Idea 1 — la misma luz**: en `M_BlobOrb_SC`, un `Transform` (vector, World→Local) entre `VectorParameter_19[LightDir]` y la entrada `LDir` de `Custom_3 BlobOrbNormalPS` → `LightDir` pasa a ser de MUNDO (hoy es local: si la esfera gira, la luz gira con ella). En la instancia del director: `LightDir` = dirección del sol del piso (az −24°, el 2,5° → (0,913, −0,406, 0,044)); probar además subir un poco la elevación para que no quede media esfera a oscuras. Revisar si `M_BlobMesh_SC` (gusano) tiene `LightDir` y hacer lo mismo.
4. Capturas sentado + cerca de la mesa; tracker.

## 2026-09-30 — BANCO DE MEDICIÓN + gradiente analítico (Attracting a 36 fps en el recorrido)
Medido por Narrativa en el visor (APK del recorrido): **Attracting 36 fps los 60 s, App 25,6 ms, GPU 98 %**; las otras etapas van a 72 fps con 10-11 ms. Beltrán: *"importante que en este packaging logremos 72fps"*, **sin tocar FFR, resolución, PixelDensity ni MSAA** y sin cambiar el look.
- **Banco** (patrón de Heart): parámetros `PerfMode` y `PerfForce` (grupo 9) en los dos Custom. Función **`SetPerf(M, F)`** (escribe los dos en `Floor` y `Sky` + eco `PERF: chladni modo M`) y eventos **`ChladniPerf0..6`** (`F` = 1: las **8 figuras forzadas**, peor caso fijo) y **`ChladniPerfOff`** (vuelve a la obra). Script `scripts/quest_chladni_perf.ps1` → `resumen_chladni.py`. APK `com.almadigital.sequencer` ("Soul Charger Sequencer"), archive `VR_Test/Saved/Packaged/Android_Sequencer/`.
- Modos: 0 actual · **1 ANALÍTICO** · 2 sin mandala en píxeles · 3 sin WPO · 4 piso plano · 5 cielo plano · 6 piso sin acabado.
- **Modo 1 = el candidato**: el campo se evalúa **UNA vez** con su gradiente **analítico** (cadena p → q0 → warp con jacobiano → (r, θ) → modos con `sincos`) en vez de 3 evaluaciones con diferencias finitas de 2 cm. Solo cuando `Geo` < 0,001 (el look aprobado: `Geometric` 0); con `Geo` > 0 sigue el camino viejo. Verificado en Python (`grad_check`): error 1e-8 contra la derivada exacta; **las diferencias finitas viejas tenían 3 %**. Captura del editor modo 0 vs 1 con las 8 figuras: diferencia del mismo orden que dos capturas del modo 0 (ruido).
- 🔑 Dato de lectura: con la mesa **vacía** el mandala no corre (`act` = 0: sale el PS y el VS). Si el recorrido dio 36 fps todo el minuto, parte del costo es la **base** del piso: por eso el banco separa mandala / WPO / piso / cielo / acabado.
- El generador tiene ahora `CON_GUSANO = False`: la sombra y el reflejo del gusano (preparados el 29) no entran ni en parámetros ni en código hasta encenderlos con Beltrán mirando.
- Para ver un modo en el EDITOR sin tocar el BP: escribir `ScalarParameterValues` del MID del componente (`...BP_ChladniFloor_SC_C_0.Floor.MID_M_ChladniFloor_SC_0`) con `ObjectTools.set_properties` (agregar las entradas `PerfMode`/`PerfForce`) y capturar; después sacarlas. `MaterialInstanceTools.set_scalar_parameter` NO acepta MIDs (solo `MaterialInstanceConstant`).
- **RONDA 1 MEDIDA en el visor** (2026-09-29 11:30, `perf/chladni_20260929_113030/`, resolución 0,05 ms, 8 figuras forzadas): viejo **25,48 ms** (36 fps) · analítico **17,98** · sin mandala PS 14,26 · sin WPO 24,91 · piso plano **9,71** · cielo plano 24,91 · sin acabado 20,62. → **piso PS 15,8 ms = mandala 11,2 + acabado 4,9**; cielo 0,6; WPO 0,6; el resto de la escena 9,7. El analítico gana **7,5 ms** y no alcanza.
- **RONDA 2** (generador): (1) **ángulos múltiples**: los anillos de los 8 modos son múltiplos de `PI·Kr·r/4` (MK·4 = 4..12) y las simetrías de `Sym·θ` (MA 1..3) → un `sincos` de cada uno y el resto por recurrencia (suma de ángulos / Chebyshev): 2 sincos por píxel en vez de 17. (2) El mandala no se evalúa donde `ordL` = 0 y no hay ola. (3) Acabado: los polígonos (3 lecturas) solo si `keep·PolyH` > 0,002; las manchas solo si `fp` < 12 (afuera pesan 0); el agua solo si el Fresnel > 0,002; la bruma con elevación fija 0 (el gradiente del cielo se pliega a constantes). (4) **Sin el camino recto ni el viejo de 3 evaluaciones** (`CON_GEO = False`: `Geometric` sin efecto; el recto está en git `1c36d03`). PS: 5.732 → 1.870 líneas DXIL, 241 → 14 sin/cos. Captura del editor (8 figuras, piso recortado sin esferas): idéntico al analítico de la ronda 1 (0,001 % de píxeles > 2 niveles); contra el viejo, 0,24 % en el borde de las crestas (la corrección del 3 %).
- Banco ronda 2: **0 = la obra optimizada**; 1 sin arena · 2 sin mandala · 3 sin WPO · 4 piso plano · 5 cielo plano · 6 sin acabado · 7 sin polígonos · 8 sin agua · 9 sin bruma (eventos `ChladniPerf0..9`).
- ✅ **RONDA 2 MEDIDA en el visor** (2026-09-29 11:45, `perf/chladni_<fecha>/`, resolución 0,01 ms, 8 figuras forzadas): **obra 11,43 ms, 72 fps** (era 25,48). Piso entero **2,55 ms** (era 15,8): mandala **0,48** (era 11,2) · acabado 1,79 (agua 0,61 · bruma 0,61 · arena 0,45 · polígonos 0,09) · cielo 0,39 · WPO 0,04. El resto de la escena (esferas, gusano) ~8,9 ms. Sin tocar FFR, resolución, PixelDensity ni MSAA.
- El banco queda en el BP y en el material (en la obra `PerfMode` 0 y `PerfForce` 0). Para volver a medir: empaquetar `Test_Sequencer` como `com.almadigital.sequencer` (receta en `docs/WORKFLOW-EQUIPO.md`) y correr `scripts/quest_chladni_perf.ps1`.


## 2026-09-30 (noche) — piso BLANCO LISO (apagado, no borrado) + paleta Uyuni
Pedido de Beltrán (audio, vía Narrativa): *"el piso blanco sin patrón ni movimiento (apagado, no borrado: se retoma)"* y paleta *"blanco-naranja-amarillo poco saturado, Uyuni al atardecer, surreal"*.
- Material: parámetro **`Plain`** (grupo `0 - Piso`) en los dos Custom: el VS devuelve 0 (quieto) y el PS devuelve el tono del plano (`lerp(SaltShade, SaltLit, FlatTone)`) + agua + bruma + dither. Sin mandala, polígonos, grano ni ola.
- BP: perilla **`FloorPattern`** (`1 - Figura`; CDO true, **instancia false**) → `PushPreview` escribe `Plain` = !FloorPattern. **Todas las perillas del patrón siguen con los valores de Beltrán**: FloorPattern true lo devuelve tal cual.
- Paleta de la instancia (antes → después, hex sRGB): SkyTop #8ea3cb→#efe0d0 · SkyMid #cbb3cc→#f6dcc2 · SkyHorizon #f2cbb2→#fce9c6 · SunColor #ffd6b0→#fff2d8 · SaltLit #fff4ea→#fffaf2 · SaltShade #b7b0d0→#efe3d4. Esferas y gusano en `BP_OrbDirector_SC.md` / `BP_Sequencer_SC.md`.

## 2026-10-01 — paleta con JERARQUÍA DE VALOR (Beltrán: "todo demasiado blanco; el gusano se pierde con el suelo y el cielo")
Familia Uyuni al atardecer conservada; solo instancias de `/Game/Test_Sequencer` (la Obra lo carga del disco). Capturas antes/después: `VR_Test/Saved/ClaudeScripts/attracting_color/hoja_antes_despues.png`. Valores lineales ANTES → DESPUÉS (para volver):
- Piso `BP_ChladniFloor_SC_C_0`: SkyTop (0.8632, 0.7454, 0.6308) → (0.521, 0.3916, 0.4678) · SkyMid (0.9216, 0.7157, 0.5395) → (0.8148, 0.552, 0.4072) · SkyHorizon (0.9734, 0.8148, 0.5647) → (0.9216, 0.6939, 0.4452) · SaltLit (1, 0.956, 0.8879) → (0.9047, 0.8388, 0.7605) · SaltShade (0.8632, 0.7682, 0.6584) → (0.7157, 0.5972, 0.4851). Sin cambio: SunColor (1, 0.8879, 0.6867), FlatTone 0,7.
- Gusano `BP_BlobChain_SC_C_2`: ColorLow (0.7835, 0.5647, 0.3663) → (0.2623, 0.0685, 0.0369) · ColorHigh (1, 0.8963, 0.7605) → (0.8879, 0.3712, 0.1441). ChainBrightness 1,25 igual.
- Esferas `BP_OrbDirector_SC_C_0`: Color1 (0.9216, 0.7605, 0.4793) → (0.8879, 0.552, 0.1441) · Color2 (0.8963, 0.6308, 0.4125) → (0.8388, 0.3231, 0.15) · Color3 (0.9647, 0.855, 0.7084) → (0.9216, 0.7913, 0.5776) · Color4 (0.855, 0.5647, 0.3515) → (0.6939, 0.2542, 0.2542) · ShadeColor (0.7682, 0.5395, 0.3467) → (0.4851, 0.2232, 0.1221). Sin cambio: ShadowColor, Brightness 1,15, OwnShade 1.
- Costo: cero (parámetros). ⬜ Visor.
