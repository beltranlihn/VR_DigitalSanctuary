# BP_PerfEntering_SC — el banco de medición de la etapa Entering (Core/Debug/)

> Creado el 2026-09-27. **Herramienta de medición, no es parte de la obra.**
> Colocado en `/Game/Test_Entering` como **`Perf_Entering`** (carpeta `Debug`, en 0, 60, 0).
> Estado: 🟢 efecto verificado en PIE (`PerfStartMode` 3 → `Volume` y `Panel` con `bVisible = false`, 0 `Accessed None`) · ⬜ **primera sesión en visor pendiente**.

## Qué contesta
Pedido de Beltrán: *"ver qué tanto peso le está dando el metaball a la experiencia"*. Apaga y prende por consola el metaball y el pacer en el APK instalado, para que [`quest_entering_perf.ps1`](../scripts/quest_entering_perf.ps1) mida el tiempo de GPU de cada combinación en UNA sesión.

## Por qué un actor aparte y no eventos en la etapa
[[BP_BreathRig_SC]], [[BP_BreathBlob_SC]], [[BP_BreathStage_SC]] y [[BP_Pacer_SC]] son **portables**: no cargan nada de medición. Este actor los encuentra solo por clase (`GetActorOfClass`) y toca **la visibilidad del componente** (`Volume` del metaball, `Panel` del pacer), que ninguno de los cuatro escribe en runtime: el metaball usa `SetActorHiddenInGame` y el pacer la escala del actor (se revisaron `BlobApplyEnv` y `PacerApplyEnvelope`). Por eso el apagado no se pisa con la lógica propia.
🔴 **Ocultar el componente es el único apagado válido de un translúcido**: con opacidad 0 el pixel shader igual corre (misma regla que el banco de Attracting).

## Estructura
| Grafo | Qué hace |
|---|---|
| `PerfSet(bBlob, bPacer, Label)` | `SetVisibility(Volume, bBlob, propagar)` + `SetVisibility(Panel, bPacer, propagar)` + log `Label` |
| `PerfApplyStart()` | si `PerfStartMode ≥ 0` → `PerfSet` según el modo (existe para verificar el efecto en PIE sin consola) |
| `BeginPlay` | log `PERF: entering listo` → `PerfApplyStart` |
| `Custom|PerfE0..PerfE3` | `PerfSet` + eco `PERF: entering modo N - …` |
| `Custom|PerfELoop` | guarda `Pacer.Cycles` en `SavedCycles` (solo si es > 0, así un segundo envío no lo pisa) y pone `Cycles = 0` (infinito) → la etapa no termina en medio de la medición |
| `Custom|PerfEEnd` | todo visible + `Cycles = max(SavedCycles, 1)` → el pacer termina en el ciclo siguiente (`PacerWrap` compara con `>=`) y la etapa cierra sola |

🆕 2026-09-27 (noche): **modo 4 "sin fondo"** para el cascarón líquido (`BP_Ganzfeld_SC`, `Entering_Fondo`). Función **`PerfFondo(bShow)`** → `SetVisibility(Ganzfeld.Shell)`; **`PerfSet` ahora arranca con `PerfFondo(true)`**, así los modos 0-3 miden igual que antes pero con el fondo encima; **`Custom|PerfE4`** = `PerfSet(true, true)` + `PerfFondo(false)`. `PerfApplyStart` acepta 4. Verificado en PIE (`PerfStartMode` 4 → `Shell.bVisible` false, `Volume`/`Panel` true). `quest_entering_perf.ps1` y `resumen_entering.py` aceptan el modo 4 (default `0,1,2,3,4`; **fondo = m0 − m4**).

🔁 2026-09-27 (tarde-noche): **el fondo ahora es el valle.** `PerfFondo(bShow)` = `GetActorOfClass(BP_BreathValley_SC)` → `SetActorHiddenInGame(not bShow)` (se borraron los 3 nodos del Shell del Ganzfeld y se reescribió la función). El Ganzfeld quedó oculto a mano en el nivel (actor `bHidden` + `Shell.bVisible` false) y el banco ya no lo toca. **Modo 4 = sin valle.** El valle trae además su propio banco interno (`PerfValley0..3`, ver [`BP_BreathValley_SC.md`](BP_BreathValley_SC.md)).

🆕 2026-09-27 (tarde): **`Custom|PerfEdge0/1/2`** → `SetScalarParameterValueOnMaterials(Blob.Volume, "EdgeAA", 0,01 / 1,5 / 5)` + eco `PERF: borde N`. Para comparar el suavizado del borde del metaball en vivo; lo manda `scripts/quest_borde.ps1`.

Modos: **0** todo · **1** sin metaball · **2** sin pacer · **3** nada (el piso: negro + mandos).
Variables: `SavedCycles` (int) · `PerfStartMode` (int, instance-editable, **-1** = no toca nada; 0-3 = arranca en ese modo).
Los `PrintString` van **solo al log** (`bPrintToScreen` false): en Development el texto en pantalla se dibuja en el visor.

## Cómo se dispara
```
adb shell "am broadcast -a android.intent.action.RUN -e cmd 'ke * PerfE1'"
```
`ke` solo existe en **Development** (ver [[BP_PerfSwitch_SC]]). Los nombres `PerfE*` son distintos de los `Perf0..8` del banco de Attracting a propósito: `ke *` llama al evento en **todos** los actores que lo tengan.

## La medición
`quest_entering_perf.ps1` → `resumen_entering.py`. Mide **`App=` de la línea VrApi** (tiempo de GPU por cuadro, una línea por segundo en logcat), no el `FrameTime` del CsvProfiler: `App` no queda clavado en 13,9 ms por el vsync, así que las restas entre modos valen aunque todo corra a 72 fps. Cuentas: metaball = m0 − m1 (y m2 − m3) · pacer = m0 − m2 · piso = m3 · interacción = m0 − m1 − m2 + m3. Ida y vuelta (0123 3210): la separación entre las dos pasadas de un modo es la resolución. Si la GPU cambia de reloj entre modos, el resumen lo avisa y agrega la cuenta normalizada por MHz.
El parser se probó con una sesión sintética en el formato real de la línea VrApi de esta Quest (recupera 5,0 / 1,5 / 4,5 ms sembrados, descarta las ventanas de 2 s del control positivo).

## 🏁 Primera sesión en visor (2026-09-27 19:04, `perf/entering_20260927_190458`)
| modo | App (ms de GPU) | FPS |
|---|---|---|
| 0 todo | 9,43 | 72 |
| 1 sin metaball | 2,34 | 73 |
| 2 sin pacer | 9,34 | 72 |
| 3 nada | 1,68 | 72 |

Resolución 0,18 ms. **Metaball 7,09 ms (75% de la etapa, 51% del presupuesto)** · pacer 0,1-0,7 ms · piso 1,68 ms · interacción −0,58. La etapa **entra en 72 fps con 4,47 ms de sobra**, con la GPU en nivel 2 @ 456 MHz (la primera fase en nivel 3 @ 492: la Quest bajó el reloj porque sobraba). Coincide con lo que sintió Beltrán: *"súper fluido"*.
⚠ Detalle del instrumento: `Tee-Object` de PS 5.1 escribió `resumen.txt` en UTF-16 → ahora lo escribe `resumen_entering.py` en UTF-8.

## TODO
- [x] Primera sesión en visor.
- [ ] Volver a medir tras la cobertura suave del borde (debería costar ~0: una división por paso).
- [ ] Si el banco deja de servir: sacar el actor del nivel **se pregunta** (regla del proyecto).

## 🏁 Sesión con fondo líquido (2026-09-27 20:26, `perf/entering_20260927_202637`)
| modo | App | FPS | reloj |
|---|---|---|---|
| 0 todo | 23,66 | 39 | 640 MHz |
| 1 sin metaball | 18,45 | 50 | 640 |
| 2 sin pacer | 23,71 | 39 | 640 |
| 3 nada (fondo + mandos) | 18,17 | 50 | 640 |
| 4 sin fondo | 9,61 | 72 | 456 |
Fondo 14,06 ms en bruto / ~16,8 normalizado a 640 MHz; metaball 5,22 ms a 640 (≈ 7,3 a 456, coincide con las sesiones anteriores → la normalización por reloj funciona). El modo 4 es el primero que hace subir el reloj entre fases: comparar SIEMPRE con la columna normalizada.
