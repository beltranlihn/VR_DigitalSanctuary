# BP_DemoResults_SC — el cuadro de resultados de la demo (guion v2, 2026-10-19)

- **refPath**: `/Game/SoulCharger/Demo/Blueprints/BP_DemoResults_SC` · modelo curvo `SM_DemoResults_{Base,Sheet,WinEEG,WinPulse,WinBreath,WinCalm,Trace}_SC` (ficha `blender-3d/assets/demo-results.md`, `CURVE_R` 1600 mm: el centro de la curva es el ojo, a 160,95 cm del origen).
- **Colocado en**: `L_Demo_Breath` (`Exp` 0, azul) y `L_Demo_Draw` (`Exp` 1, verde), label `Results`. El director lo llama con `ResShow`/`ResHide`; `ResPlace` lo pone a `Dist` 160,95 frente a la cámara, `Drop` 8 cm más abajo.
- **Fuente**: `VR_Test/Saved/ClaudeScripts/Demo2/results_dsl.py`.
- **Estado**: 🟢 `-game` con señal simulada: gráficos, índice de calma, nota del dibujo (captura `Demo2/res_crop2.png`) · ⬜ visor (legibilidad a 1,6 m).

## Cómo dibuja
- Aparición: `AppearLuz` (luz primero, como el SHARE): `Base`, `Sheet` y las 4 ventanas con tag `AppearBody`, `Trace` con `AppearTrace`. El contenido se funde con `Fade` (AppearT 0,6→1) y los rótulos aparecen con AppearT ≥ 0,85.
- **Contenido en el vidrio**: cada ventana tiene en su slot `Pane` un MID de `M_DemoResPane_SC` (vidrio translúcido como `M_SCPanelGlass_SC` + `Card` emisivo) con un render target de Canvas de 1 px = 1 mm, **sin mips** (592 × 142, calma 272 × 482), que se llena reduciendo 2:1 un RT de trabajo de 2 px/mm (ver 2026-10-21).
- Datos: `BP_BioHub` (casillas de 5 s desde que cargó el nivel: `BinHasCalm`/`GetCalmBinAvg`, `BinHasHeart`/`GetHeartBinAvg`) → `SerCalm`, `SerHeart`, `CalmAvg`, `HeartAvg`. Breath: `BP_BreathStage_SC.CycleScores` → un círculo por ciclo (radio ∝ puntaje). Draw: trazos del historial ("N strokes of light").
- Rótulos y número grande: **en la textura** desde el 21-10 (antes TextRender): NEURAL ACTIVITY · PULSE − NN bpm · BREATH CYCLES / HEARTBEATS FELT − N / YOUR DRAWING · CALM INDEX + el índice de calma de la app (% con signo).
- 🔴 **Sin señal del Muse no se inventa nada**: "no signal" en los rótulos, "--" en el índice, ventanas vacías.

## Perillas
`Exp` · `BodyMat` / `RingMat` (marco y cinta: `MI_Demo_Body/Ring_{Entering,Surrounding}_SC`) · `Dist` · `Drop`. Brillo del contenido: `Gain` de `M_DemoResPane_SC` (1,1).

## 2026-10-19 (noche)
- Rótulos más grandes: `WorldSize` de `LblEEG`/`LblPulse`/`LblBreath` 1,7 → **2,4**, `LblCalm` 1,9 → **2,6** (a 1,6 m quedaban en ~10 px por mayúscula). ⬜ verificar en visor.
- `ResPlace` orienta el cuadro con el yaw del PlayerStart.

## 2026-10-20 — Heart (`Exp` 2)
- `ResHeart`: `NBeats` = `BeatCount × BeatDiv` del manager; `Scores` = un círculo chico por pulso (hasta 24), en rojo (`RINGH`). Tercera ventana "YOUR HEARTBEAT", nota "N heartbeats felt" (la nota se ve en `Exp` 1 y 2). En `L_Demo_Heart`: `BodyMat`/`RingMat` Recognizing.

## 2026-10-20 (noche, 2.ª tanda) — textos nítidos en el Quest
- Los 6 `TextRender` (`LblEEG`, `LblPulse`, `LblBreath`, `LblCalm`, `Big`, `Note`) usan `Demo/Materials/M_DemoTextAA_SC`: copia de `/SC_Base/M_TextUnlit` (enmascarado, campo de distancia) con **`bUseAlphaToCoverage`**. Con el material enmascarado el borde quedaba sin antialiasing en el visor ("bajísima calidad").

## 2026-10-20 (noche, 4.ª tanda) — CALM INDEX con signo
- Variable nueva `CalmIdx` (CDO −999). `ResData` la pone en −999 y `ResHub` la lee del BioHub (`select(GetCalmIdxSeen, GetCalmIdx, −999)`).
- La ventana de calma muestra **`+N%` / `−N%`** (signo decidido sobre el valor redondeado: nunca "+0%") o `--` sin índice. `DrawCalm`: barra divergente desde x 136 (cálida si ≥ 0, azul si < 0).
- Fuente `VR_Test/Saved/ClaudeScripts/Demo2/results_dsl.py`.

## 2026-10-21 (madrugada) — calidad del cuadro: TODO en textura (rótulos y número incluidos)
Pedido de Beltrán: "los textos y gráficos de los resultados se vean en altísima calidad, quedan pixelados", "al tener curvatura, los textos quedan cortados" y **"en Soul Charger procuramos usar texturas, no TextRender, que se ve mal"**.
- **Ahora todo se dibuja en la textura de cada ventana** (`results_dsl.py`): cada ventana se dibuja en un RT de TRABAJO a 2 px/mm (líneas del Canvas + texto con `Canvas|DrawText` en **Quicksand SemiBold**, la fuente de la obra, `Core/Font`, caché Runtime = se rasteriza al tamaño pedido) y se reduce a su RT final de 1 px/mm con `Canvas|DrawTexture` en `BLEND_Opaque` (bilineal exacto a 2:1 = promedio 2×2, un mip hecho a mano). 1 px/mm es ~1,5× la densidad del visor a 1,6 m (el cuadro mide ~0,6-0,7 px del eye buffer por mm al 100 %); sin mips, más que eso titila.
- RTs: 0-3 finales (592×142 ×3, 272×482), 4 y 5 de trabajo (1184×284, 544×964). `ResEnsure` crea los 6.
- El texto sigue la curva del vidrio porque ES el vidrio: ya no hay cortes. Rótulos a x 20 mm / y 26 mm, em 24 mm (el gráfico va de y 132 a 48 y los círculos se centran en y 84 con radio ≤ 46: nada toca el rótulo); "CALM INDEX" y la nota de Draw, em 26 mm; el número grande, em 100 mm achicado con `Canvas|ClippedTextSize` para que entre en el 80 % del ancho de la ventana.
- Los 6 `TextRender` quedan siempre ocultos (`ResLabelsOn`); `ResLabels` les sigue poniendo el texto (inofensivo).
- **Heart**: el conteo va en el título ("HEARTBEATS FELT  -  N"); la nota solo en Draw ("N strokes of light", centrada en la ventana).
- El vidrio (`M_DemoResPane_SC`) usa solo el RGB de la textura, sumado (negro = nada): el texto con antialiasing sobre negro compone bien.
- Antes de pasar a textura se probaron (visor, capturas `metacam`): `M_DemoTextAA_SC` afilado con su derivada (gotcha 592; sigue en el reloj del `BP_DemoHudKit_SC`) y los rótulos adelantados a la curva (gotcha 593). Se veía entero y sin tramado, pero seguía dentado: el TextRender recorta con el alfa del campo de distancia y a 1,6 m una letra de rótulo mide ~10 px del eye buffer.
- Subir la resolución del visor solo durante los resultados NO entra: Heart ya usa ~10,5 ms de GPU de 13,9 al 100 % (VrApi `App=`); al 125 % serían ~16 ms.
- Respaldo previo: `VR_Test/Saved/ClaudeScripts/Demo2/backup_1021a/` (BP y material) y `results_dsl_backup_1021a.py`.

## 2026-10-21 (noche) — fondo translúcido del color de cada experiencia (arreglo 7)
- `ResShow` tiñe la hoja y las cuatro ventanas según `Exp` (Breath 0,55/0,64/0,98 · Draw 0,5/0,92/0,68 · Heart 0,98/0,55/0,52): `Sheet` Color + `Base` 0,16 + `Opacity` 0,45; `WinEEG/WinPulse/WinBreath/WinCalm` Color + `Base` 0,08. Con `...onMaterials` del componente: `Rendering|Material|SetVectorParameterValue` a secas resuelve a la versión de Material Parameter Collection (falló la escritura y dejó `ResShow` vacía hasta reescribirla).
- Las páginas de instrucciones (`MI_Instr2_*`) pasaron a `M_DemoPanelPage_SC` (translúcido, `BgOpacity` 0,86, `Base` = color de su carta).

## 2026-10-22 (feria) — número de calma nítido y curvas orgánicas
- **Número grande pixelado**: Canvas rasteriza el glifo al `LegacyFontSize` de la fuente (con `DPIScale` 1: `CanvasItem.cpp`, `DrawStringInternal_RuntimeCache`) y AGRANDA el bitmap por `Scale`; con Quicksand a 9 pt el número iba ×16,7. Copia de la fuente a **120 pt**: `/Game/SoulCharger/Demo/Fonts/Quicksand-SemiBold_Big_SC` (Runtime) solo para el número (`TEXTF`/`FONT_BIG` en `results_dsl.py`): ×1,25 en el RT de trabajo y después 2:1. Las etiquetas siguen con la de 9 pt (×4).
- **Curvas poligonales**: eran rectas entre las casillas de 5 s del BioHub (datos reales del Muse, promediados). Ahora `graph()` dibuja **Catmull-Rom** (`GK` 6 tramos por intervalo, pasa por cada casilla real, recortada a la ventana) y los niveles demo usan casillas de **2 s** (`BioHub.BinSeconds` de la instancia en Breath, Draw y Heart; 180 × 2 s = 6 min). Heart -game: 107 casillas (antes 43), curva lisa, 0 errores.
