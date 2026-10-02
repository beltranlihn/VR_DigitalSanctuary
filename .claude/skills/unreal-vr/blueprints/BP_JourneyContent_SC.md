# BP_JourneyContent_SC — el CONTENIDO del cuadro de resultados

- **refPath**: `/Game/SoulCharger/Shared/Results/Blueprints/BP_JourneyContent_SC.BP_JourneyContent_SC` · parent Actor · creado 2026-09-30 (noche del director general, turno Drawing T2).
- **Material**: `/Game/SoulCharger/Shared/Results/Materials/M_JourneyCard_SC` (Unlit, Additive, TwoSided).
- **El MARCO es de Mesh 3D**: `BP_ResultsArt_SC` (misma carpeta): vidrio, ventanas, franja de título, cajita del tip y los fundidos `KTitle/KCalm/KHeart/KBreath/KMelody/KTip`. Este BP solo **dibuja el contenido** y va colgado del marco.
- **Nivel de prueba**: `/Game/SoulCharger/Shared/Results/Maps/Test_Results` (lo creó Mesh 3D). Instancia `BP_JourneyContent_SC_C_0`, **AttachToActor a `BP_ResultsArt_SC_C_0` con transform identidad** (9 → 10 actores). Instancia: `bBuildOnPlay` true, `bPreviewInEditor` false.
- **Diseño aprobado que copia**: `web/prototipo-narrativo/world.js`, sección RESULTADOS (`drawGraphCard`, `drawBreathCard`, `drawMelodyCard`, `drawResHeader`, `drawResTip`, `RES_ITEMS`).
- **Fuente del código**: [`scripts/journey_content.dsl`](../scripts/journey_content.dsl) (diseño, API, layout en mm, textos) y [`scripts/journey_content_body.dsl`](../scripts/journey_content_body.dsl) (los cuerpos, = lo que hay en el editor). El partidor para escribir por tandas: `VR_Test/Saved/ClaudeScripts/journey/split_journey.py` (su `rep{}` traduce los nombres `;;?` a los reales).

## Status
🟢 **Se ve en la Obra (2026-09-30, 13:09, turno pedido por Narrativa).** En `L_SoulCharger_Obra` las 6 ventanas salían vacías.
- **Causa: los mips.** Los RT tenían `bAutoGenerateMipMaps` y el Canvas dibuja solo el mip 0. A 1,9 m se lee el mip 1, que es negro (gotcha 546).
- **Arreglo:** RT sin mips.
- **Verificado con la prueba rápida de la Obra** (`bDebugEnding` + `bPhotos` en `BP_Obra_SC_C_0`, destildados antes de guardar):
  - `HighresScreenshot00030`: con mips, vacío;
  - `00034`: sin mips, se ve;
  - `00038`: con prioridad 7, se lee todo, también el tip.
  - 0 errores en el log.
- En la misma pasada:
  - prioridad de orden de `Cards` 0 → **7**;
  - `JcBreathOne` sin división por cero con 1 ciclo;
  - `SetBreathScores` con un arreglo vacío deja la muestra.

🟢 **Construido y verificado (2026-09-30):**
- captura del editor de las 6 tarjetas;
- PIE con `Build` (StN 180, MinShown 14, ritmo 65,5–88,9, K del marco leídos);
- PIE con `SetTip("breath")`: cruce completo, TipK 1, texto envuelto.

Todo con 0 errores (Accessed None / Runtime Error / Script Msg).

⬜ **Falta:**
- ✅ ya integrado en la Obra: Narrativa lo llama desde `BP_Obra_SC.ResultsShow` (SnapToTarget → `SetBreathScores` → `SetMinutes` → `Build` → `ResultsAppear`). Falta el hover real → `SetTip`;
- oír el click;
- visor y APK (costo: 6 RT dibujados una vez y 6 escalares por cuadro);
- Michroma (decide Beltrán: es una descarga).

## API
| Llamada | Qué hace |
|---|---|
| `SetBreathScores(Scores: float[])` | Guarda los puntajes 0..1 de cada ciclo de Entering (un anillo por ciclo). **Solo guarda: llamar ANTES de `Build`.** Un arreglo **vacío no borra**: queda la muestra del CDO (4 anillos). Sin eso, la tarjeta quedaba en "0 cycles" y la ventana vacía. |
| `SetMinutes(M: float)` | Minutos del título. 0 = los calcula del `BP_BioHub` (casillas × `BinSeconds` / 60). **Antes de `Build`.** |
| `Build()` | `JcEnsure` (malla, RT y MIDs, una sola vez) → `JcData` (BioHub o muestra de la web) → dibuja las 6 tarjetas → tip en None → prende el Tick. |
| `SetTip(Key: Name)` | `calm · heart · breath · melody · soul · drawing · None`. Si cambia: `VR_click1` (con None no suena) y el texto se funde como la web (baja a 6/s, redibuja, sube a 5/s). Para el hover. |

- **Flags**:
  - `bBuildOnPlay`: en el CDO es false. En la Obra, `Build` lo llama el director.
  - `bPreviewInEditor`: false. En true, el Construction Script llama a `Build` y el contenido se ve en el viewport sin PIE, para autorar mirando. Volverlo a false antes de guardar.
- **Datos**: `JcData` busca el `BP_BioHub` (GetActorOfClass).
  - Si no lo encuentra, o tiene menos de 20 casillas: `JcSample`, la serie de muestra de la web (180 casillas, 14 min).
  - Con hub: calma y latido por casilla, saltando huecos.
- **Hover** (lo arma quien tenga el puntero): bandas en **Z local del marco (cm)**, con ancho ±51,5 en Y.
  - calma 26 ± 10,5
  - ritmo 3 ± 10,5
  - respiración −18 ± 8,5
  - melodía −38 ± 9,5
  - `soul` y `drawing` son las zonas del alma y del dibujo, fuera de este BP.
  - `Cards` no está pensada para el haz (plan: sin colisión): el impacto se toma sobre el panel de Mesh 3D y se pasa a coordenadas locales.

## Arquitectura (barata en Quest: se dibuja UNA vez)
- **`Cards`**: ProceduralMeshComponent del SCS, porque el Construction Script no puede `AddComponentByClass`.
  - **`TranslucencySortPriority` 7** (leído 2026-09-30, en la plantilla y en la instancia de la Obra).
    - El marco usa: vidrio 1, ventanas 2, borde 4, cajita del tip 5, trazo 6.
    - Con 0, el contenido quedaba debajo de todo el vidrio y se veía apagado.
    - Con 3, el texto del tip seguía tapado por el vidrio de la cajita (5).
    - ⚠ Con 7 queda por encima de cualquier translúcido de prioridad menor: si Alma pasa por delante, el contenido se ve a través de ella.
  - `CastShadow` false en la plantilla. En la instancia de la Obra quedó true porque el set no se aplica; da igual, un translúcido no proyecta sombra.
  - La plantilla nació con prioridad 0 y sombra: el paso 3 del plan no se había aplicado.
- **6 secciones = 6 quads** en el plano YZ a x = +0,6 cm, delante de las ventanas:

  | # | Sección | Centro z (cm) | Tamaño (cm) | RT (px) |
  |---|---|---|---|---|
  | 0 | título | 43,25 | 103 × 9,5 | 1030×95 |
  | 1 | calma | 26 | 103 × 21 | 1030×210 |
  | 2 | ritmo | 3 | 103 × 21 | 1030×210 |
  | 3 | respiración | −18 | 103 × 17 | 1030×170 |
  | 4 | melodía | −38 | 103 × 19 | 1030×190 |
  | 5 | tip | 62,5 | 92 × 17 | 920×170 |
- **Un RT por sección** (`CreateRenderTarget2D` RGBA8, **SIN mips**: con mips salían negros a distancia, gotcha 546). Se dibuja con `BeginDrawCanvastoRenderTarget`. 1 px = 1 mm, así que las coordenadas en mm de la web se copian tal cual. A 1,9 m se ve a ~2:1; en el visor hay que mirar si titila.
- **Una MID por sección**: `CreateDynamicMaterialInstance` en su sobrecarga de componente (`ElementIndex`, `SourceMaterial`), que además la asigna (gotcha 406).
  - `Card` = su RT, vía el wrapper `JcSetTex`.
  - `Fade`, vía el wrapper `JcSetFade`, armado por cirugía con `declaring_class` MID porque el DSL elige el overload de MPC.
- **`M_JourneyCard_SC`**: Emissive = pow(`Card`.rgb, `Gamma`) × `Fade` × `Gain`. **`Gain` 1,6 es la perilla de brillo**, con `Gamma` al lado. Sin alfa: el fondo oscuro lo pone el vidrio del marco, y los colores de la web van premultiplicados por su alfa.
- **Tick**: `JcFadeStep` y después `JcTipStep(min(Dt, 1/30))`.
  - `JcFadeStep` castea el padre (`GetAttachParentActor` → `BP_ResultsArt_SC`) y copia sus K a los `Fade`. El tip va además × smooth(`TipK`).
  - Sin padre, todo va a 1.
- **Construction Script**: si `bPreviewInEditor`, llama a `Build`.
- **EventBeginPlay**: si `bBuildOnPlay`, llama a `Build`.
- **Fuente**: `/Engine/EngineFonts/Roboto`, escalada a `Px / FontPx` (24). Roboto no trae la corchea: en la melodía va dibujada (disco, plica y bandera).

## Variables
**Journey** (instance-editable: las perillas):
- `BreathScores` [0,62 0,83 1 0,71] · `Minutes` 0
- `StageColors` (5, lineales: Entering, Recognizing, Loving, Attracting, Surrounding) · `Cream` · `Grey` · `FontPx` 24
- `TipKeys` / `TipNames` / `TipStage` [2,1,0,3,−1,4] / `TipTexts` (los `RES_ITEMS` de la web, en inglés)
- `ClickSound` (`/SC_Base/Audio/VR_click1`) · `ClickVol` 1
- `bPreviewInEditor` · `bBuildOnPlay`
- ⚠ La variable `Gain` del BP se **borró** (2026-09-30): no la usaba ningún grafo (verificado en los 54 con control positivo). El brillo está en el material.

**Z-Journey** (internas): `RTs`, `MIDs`, series (`SerCalm`, `SerHeart`, `Ser`, `SerStage`), la geometría del quad (`QV`, `QN`, `QT`, `QUV`), las del gráfico (`Pts`, `Tris`, `Gx0`… `Ghi`), las estadísticas (`StLo`, `StHi`, `StSum`, `StN`), las bandas (`BandA`, `BandB`), el tip (`TipKey`, `TipWant`, `TipK`) y el envuelto de texto (`WrapY`, `WrapLine`, `Words`), más `MinShown`.

## Funciones (54 grafos)
- **Malla y datos**:
  - `JcQuad`, `JcTarget`, `JcEnsure`;
  - `JcData`, `JcFromHub`, `JcSample`, `JcSampleOne`;
  - `JcStats`, `JcStatOne`.
- **Primitivas del Canvas**:
  - `JcText` (escala y alineado a la derecha con TextSize), `JcRect`, `JcDash`;
  - `JcRing` (48 segmentos), `JcDisc`;
  - `JcLighten(Col, K)` → `Out` (lerp a blanco × 0,8).
- **Tarjetas**:
  - `JcCard(S)` (Clear + Begin/End), `JcPaint`, `JcTitle`;
  - gráfico: `JcGraph`, `JcGraphBody`, `JcPts`, `JcPtOne`, `JcAreaTris`, `JcTriPair`, `JcLine`;
  - banda de etapas: `JcBand`, `JcBandReset`, `JcBandScan`, `JcBandMark`, `JcBandDraw`, `JcBandOne`;
  - `JcBreath`, `JcBreathOne`, `JcBreathGlow`, `JcMelody`;
  - tip: `JcTipDraw`, `JcTipBody`, `JcWrapLoop`, `JcWrapWord`, `JcWrapFlush`.
- **API y reloj**:
  - `Build`, `SetTip`, `JcTipSound`, `SetBreathScores`, `SetMinutes`;
  - `JcTipStep`, `JcTipSwap`;
  - `JcFadeStep`, `JcFadeFrom`, `JcFadeK`;
  - `JcSetTex`, `JcSetFade`.

## Palancas (qué ajusta qué)
| Quiero… | Toco… |
|---|---|
| más o menos brillo de todo | `Gain` del material `M_JourneyCard_SC` (1,6) |
| colores lavados u oscurecidos por sRGB/lineal | `Gamma` del material |
| letra más grande o más chica | `FontPx` (menor = letra más grande: escala = px / `FontPx`) |
| colores de cada etapa | `StageColors` (lineales) en la instancia |
| textos del tip | `TipTexts` / `TipNames` en la instancia |
| volumen del click del hover | `ClickVol` |
| ver el contenido en el editor sin Play | `bPreviewInEditor` true (y volverlo a false) |

## Trampas que salieron al construirlo
- 🔴 **Mips de un RT de Canvas = negro a distancia** (gotcha 546). Se ve perfecto de cerca y desaparece a la distancia real, sin un solo error. Verificar siempre a la distancia de uso.
- 🔴 **`select` evalúa las dos ramas, y el `bind` de un nodo puro se re-evalúa en cada uso.** La división `I/(N-1)` de `_x` corría 4 veces con N = 1 → 4 "Divide by zero" por `Build`. Todo divisor que pueda ser 0 va protegido con máx(1, …), aunque la rama "no se use".
- **Canvas → RT pisa, no suma** (gotcha 540): el brillo del ciclo perfecto va PRIMERO (`JcBreathGlow`) y el anillo al final.
- **Una función con `return` "vacía" tiene 2 nodos** (gotcha 541): el escritor por tandas salteó `JcLighten` y devolvía negro.
- **`find_nodes` devuelve rutas, no títulos** (gotcha 542): verificar el uso de una variable contando `refPath`, con control positivo.
- **Nombres reales de pines**:
  - `CreateRenderTarget2D` lleva `bAutoGenerateMipMaps`.
  - El `Power` del material lleva `Exp`, y ese error escapa del try.
  - `Utilities|Array|FindItem`, no `Find`.
  - `bind` de un literal no vale (se inlinea).
- **En PIE, `set_properties` solo escribe variables instance-editable** (gotcha 424). Para probar `SetTip` se hizo `TipWant` editable, se probó y se revirtió.

## 2026-10-01 (Narrativa) — sonido en su lugar
- `JcTipSound`: `ClickSound` (`VR_click1`, con `ATT_Objeto_SC`) suena en la posición del contenido (pegado al cuadro), no en 2D.
