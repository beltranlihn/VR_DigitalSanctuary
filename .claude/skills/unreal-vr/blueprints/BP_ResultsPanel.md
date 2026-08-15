# BP_ResultsPanel + WBP_Results — el gráfico de resultados del exterior (Core/UI/)

## Purpose
El beat del guión que decía *"gráficos de resultados bajo la ameba (promedios por etapa: calma, ritmo, respiración) + VO 26"*, en el exterior, justo antes de que el usuario decida llevarse la ameba al corazón. Es lo que le devuelve al usuario **su propio recorrido medido** — la "capa viva" de la obra hecha visible.

## Status
🟢 **Cadena completa verificada por log** (2026-08-15): el panel nace oculto, el widget registra sus 5 barras, el final lo despliega, las etapas se revelan **una por una** y el panel se oculta solo. Cero `Accessed None`.
🟡 **Los números todavía son 0** en la prueba aislada porque no corrió ninguna etapa: el registro por etapa se llena durante la obra. La **marca de etapa sí está probada** (`BIO: etapa marcada = 3` con `DebugStartStage=3`).
⬜ Falta el visor: tamaño, distancia, si se lee bien a esa altura, y si el ritmo de 0,9 s por fila acompaña al VO.

## La cadena, de punta a punta
```
BP_StageDirector.SpawnStage
   └─ MarkBioStage  →  BP_BioHub.SetCurrentStage(StageIndex)     ← 🆕 esto FALTABA: BinStage nunca se escribía
BP_BioHub  (por muestra recibida)  →  BinCalm*/BinHeart* + BinStage
BP_Finale.FinaleReady
   └─ FinalResultsBeat → ShowFinalResults (panel) + ResultsVo (VO 26)
BP_ResultsPanel.ShowResults → BindResultsW → StartRows
   └─ NextResultRow (timer, cada RevealTime) → FillResultRow(i)
        calma  = BioHub.GetStageCalmAvg(i+1)
        ritmo  = MapRangeClamped(BioHub.GetStageHeartAvg(i+1), HeartMin, HeartMax, 0, 1)
        → WBP_Results.SetResultRow(i, calma, ritmo)
   └─ al terminar las 5: timer HoldTime → HideResults
```
🔴 **`StageIndex n` ↔ **fila `n−1`**: el director numera Hall=0, Entering=1 … Surrounding=5; el panel tiene 5 filas 0..4. Por eso `FillResultRow` consulta `Index + 1`.

## Los promedios por etapa (nuevo en [[BP_BioHub]])
Seis funciones nuevas, calcadas del patrón ya probado de `GetCalmAvgAll`:
`AccumStageCalmBin` / `AccumStageCalmAll` / **`GetStageCalmAvg(StageId)`** y sus tres gemelas de ritmo, más `StageHasData(StageId)`.
El filtro es una sola línea: la casilla suma **sólo si `BinStage[i] == StageId`**, reusando el `AccumCalmBin` que ya existía. `Count == 0` → devuelve 0 (el hueco, no un promedio falso).
⚠ El `for` es multi-exec y **tiene que ir último**, así que el acumulado vive en su propia función y el promedio se calcula después. Es la misma restricción de siempre.

## WBP_Results (Core/UI/)
`Root`(CanvasPanel, anclado full) → `Rows`(VerticalBox) → `Title` · `Legend` · `Row0..4`(HorizontalBox) → `Name{i}`(TextBlock) + `Calm{i}` + `Heart{i}` (ProgressBar).
- **Título** YOUR JOURNEY 46 px · **leyenda** "thick bar = calm / thin bar = rhythm" 22 px al 50 %.
- **Nombres en inglés** y **con el color de su etapa** (la paleta de la lámina, la misma de [[BP_StageIntro]]): ENTERING azul · RECOGNIZING rojo · LOVING morado · ATTRACTING ámbar · SURROUNDING verde.
- **La barra de calma lleva el color de la etapa**; la de ritmo es blanca al 75 % y **más fina** (más padding vertical) — así se distinguen sin leer la leyenda.
- API: **`InitBars()`** (la llama su propio `Event Construct`) · `ResetBars()` · **`SetResultRow(Index, Calm, Rhythm)`** (con guard contra el array) · `ApplyRow` (el que escribe los `SetPercent`).
- 🔴 Se borraron el `Event Tick` y el `Event PreConstruct` vacíos que deja `write_graph_dsl`.

## El actor
`Panel` (WidgetComponent · WBP_Results · Space=World · DrawSize **820×620** · TickMode Automatic · escala 0.1 → **82 cm de ancho** · blendMode Transparent). Colocado en `L_Persistent` en **(6045, 0, 62) yaw 180**, o sea **justo debajo** del `SoulHandSpot` (6045, 0, 128) donde queda la ameba. Se autora moviendo el actor, no tocando el grafo.

| Variable | Default | Rol |
|---|---|---|
| `RevealTime` | 0,9 s | Cada cuánto aparece la fila siguiente. **La palanca del ritmo**, para calzar con el VO 26. |
| `HoldTime` | 16 s | Cuánto queda el gráfico después de la última fila, antes de ocultarse solo. |
| `HeartMin` / `HeartMax` | 50 / 110 BPM | El rango con el que se normaliza el ritmo a la barra 0–1. |

## Decisiones que conviene recordar
- **Se oculta solo** (`HoldTime`) en vez de engancharse a `CommitToHeart`. Razón concreta: `CommitToHeart` **no se puede reescribir** — su `read_graph_dsl` devuelve `(|SetbCommitted true)` y esa forma **no se puede volver a escribir** (el DSL no la reconoce). Reescribir esa función habría requerido cirugía de nodos sobre una cadena que ya funciona, y el auto-ocultado da el mismo resultado sin riesgo. `HideResults` queda pública por si más adelante conviene el enganche.
- **`EnsureFinaleAudio`**: `ResultsVo` recachea el AudioHub antes de hablar, porque en el camino de debug el `AudioRef` puede no estar cacheado todavía.

## TODO
- [ ] 🔴 **Visor** y una **corrida completa** que llene los promedios de verdad (hoy sólo está probado el cableado).
- [ ] La **respiración** como tercera barra: el guión pide calma, ritmo **y respiración**; hoy hay dos. Falta que el sensor de respiración registre en el BioHub como las otras dos señales.
- [ ] Que suene **NUESTRA melodía** junto con el gráfico (está guardada como string en `SG_Melody`; falta reproducirla).
- [ ] Arte: hoy son ProgressBars de motor. Cuando haya lámina, cambiar los brushes.

## Relacionados
- [[BP_BioHub]] (de dónde salen los promedios) · [[BP_Finale]] (quién lo dispara) · [[BP_StageDirector]] (`MarkBioStage`) · [[BP_StageIntro]] (la paleta y el patrón de widget world-space) · `references/widgets-vr.md`
