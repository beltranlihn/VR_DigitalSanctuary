# Fantasmas de instrucciones: `BP_GhostPlayer_SC` + `BP_GhostRecorder_SC` + `BP_GhostTake_SC`

Carpeta: `/Game/SoulCharger/Shared/Ghost/`. Encargo de Beltrán vía Narrativa (2026-09-30, noche), guion V5.
Plan completo: [`docs/PLAN-FANTASMAS-2026-09-30.md`](../../../../docs/PLAN-FANTASMAS-2026-09-30.md).
Fuentes: `scripts/ghost/`. La hoja del turno es `TURNO.md`; los grafos están en `ghost_player.dsl` / `ghost_recorder.dsl` y las variables en `make_spec.py` -> `ghost_spec.json`.

**Qué es:** Beltrán graba cada gesto de instrucción con los mandos. La obra lo reproduce como un "fantasma" translúcido, dos manos que hacen el gesto, en bucle hasta que el usuario lo hace.


## 🆕 v2 (2026-10-01): ✅ APROBADA por Beltrán en PIE, en integración (Narrativa)
- **Estado 2026-10-01 tarde:**
  - Las 7 tomas usadas, grabadas por Beltrán en `L_GhostRec_SC` y **suavizadas**: `ghost_smooth.py`, gaussiano σ 2,5 cuadros; posiciones promediadas; rotaciones como cuaterniones; gatillos sin tocar. La toma cruda queda en `Saved/ClaudeScripts/ghost/<DA>_crudo.json`.
  - Las tomas usadas son Bell, Take, Pick, Breath, Heart, Attract y Draw. Loving, Save y Share están vacías.
  - CDO: `StepHz` 30 y `EchoAlpha` [1] (sin ecos; antes 11 poses/s con 4 ecos, que se superponían y no se leían).
  - Beltrán lo vio en PIE: "se ve bien".
  - Integración encargada a Narrativa, con prioridad sobre los subtítulos y **con el texto oculto en la experiencia** (`bShowText` false en cada instancia). Plan: `docs/PLAN-FANTASMAS-V2-2026-10-01.md` §9.
  - 📍 **Colocados en las celdas de la Obra (2026-10-01 tarde, sesión Animaciones)**. Todos con yaw 0, `bShowText` false, `bAutoPlay` false, `bPreview` true y carpeta `Fantasmas`. Encendido: `BP_Obra_SC.GhostTick` (Narrativa).

    | Nivel | Fantasma | Posición | `FollowTag` |
    |---|---|---|---|
    | `Test_Hall` | `Ghost_BELL` | sobre `Timbre` | `hall_bell` |
    | `Test_Hall` | `Ghost_TAKE` | sobre `Sensor` | `hall_sensor` |
    | `Test_Hall` | `Ghost_PICK` | sobre `HallSoul_0` | `soul_idx_0` |
    | `Test_Breath` | `Ghost_BREATH` | (0, 0, 120) | — (va a la cabeza) |
    | `Test_Heart` | `Ghost_HEART` | (0, 0, 120) | — (va a la cabeza) |
    | `Test_Sequencer` | `Ghost_ATTRACT` | PlayerStart + 120 (ojos); `OrbRest` (350, 120, 80) | — |
    | `Test_Draw` | `Ghost_DRAW` | PlayerStart + 120 | — |

    - En la toma de Attract la esfera se suelta a 75-90 cm bajo los ojos: coincide con los slots reales (−76,6).
    - ⚠ El timbre real del Hall tiene escala 0,667; el del estudio, 1.
  - ⏩ **Segunda vuelta de Beltrán en la Obra (2026-10-01):**
    - **Texto:** `GhText` escribe el texto **VACÍO** si `bShowText` es false. Antes solo ponía el color en 0, y `M_TextUnlit` dibuja las letras negras, que igual se veían.
    - **Más rápido:** perilla nueva `PlayRate` (CDO **1,25**) que multiplica el avance en `GhRun`; si vale ≤ 0 cuenta como 1. `LoopGap` (la pausa entre vueltas, en segundos reales) bajó de 1 a **0,4**.
    - Escrito y releído en las 7 instancias, con los ISM en orden y los 6 paquetes guardados.
    - Para ajustar todo a la vez: el CDO. Las instancias tienen el mismo valor, así que no quedan como override (gotcha 580).
  - 🔁 **Bucle de solo el acercamiento (Breath/Heart, 2026-10-01):** Beltrán quiere que se repita "llevá el sensor a la panza / al pecho", para que el usuario entienda mirando al frente.
    - Perilla nueva `LoopEnd`: fin del bucle en segundos de la TOMA; ≤ 0 = la toma entera, que es el default.
    - `GhRun`: duración = min(`LoopEnd`, toma).
    - Valores medidos en la toma, donde el sensor se asienta:

      | Fantasma | Se asienta | `LoopEnd` |
      |---|---|---|
      | `Ghost_BREATH` | 4,87 s | **4,9** |
      | `Ghost_HEART` | 4,13 s | **4,2** |

    - Escrito y releído; guardado.
  - 🔇 **SIN SONIDO** (Beltrán, vía Narrativa): suenan junto con la voz en off que da la instrucción. `AppearSound`/`VanishSound` = None en el CDO y en las 7 instancias (leído). `GhSound` solo suena si el sonido es válido; el gatillo no tiene sonido. **No asignar** FX_GHOSTAPPEAR/OUT.
- 🔴 **Crash al abrir el nivel (gotcha 578):**
  - El Construction Script ya NO llama `SetNumCustomDataFloats` (`GhInstInit`).
  - No cambiar `NumCustomDataFloats` de `BodyR/L`, `Stroke` ni `Path` con instancias colocadas y guardadas en algún nivel.
  - `L_GhostRec_SC` se rehízo: el viejo, que crashea, está en `VR_Test/Saved/GhostBackup/`.
- **Plan:** `docs/PLAN-FANTASMAS-V2-2026-10-01.md`. **Hoja del turno:** `scripts/ghost/TURNO-V2.md`. **Datos:** `scripts/ghost/v2_datos.md`.
- **Diseño:**
  - Un fantasma COLOCADO por instrucción (`Take` = su DA), en su nivel de test, que es la celda de la Obra.
  - Ancla en el nivel (sigue a un objeto con `FollowTag`) o en la cabeza (Breath, Heart).
  - Componentes fijos: `BodyR/L` (ISM: pose + 4 ecos con opacidad por instancia), `TrigR/L`, `HandR/L` (la mano del pawn), `PropR/L` (SAVE o paleta), `BeamR/L`, `Orb`, `Stroke`, `Path` y `Label`.
  - Vista previa en el editor por Construction Script: la pose en `PreviewTime`, la cebolla y los puntos del recorrido.
  - Modo EN VIVO para el grabador.
  - Datos de 34 floats por cuadro (se agrega la posición del aim).
- **Estado:**
  - ✅ Armado, grafos escritos, compila.
  - ⬜ Arreglos del revisor.
  - ⬜ Grabador (sus grafos).
  - ⬜ Estudio, prueba sin visor y primera grabación.

## Piezas
| Asset | Qué es |
|---|---|
| `BP_GhostTake_SC` | Clase **PrimaryDataAsset**. Variables: `Id` (Name), `Text`, `Hz`, `Frames`, `Stride`, `Data` (float[]), `bUseRight/Left`, `bBeamRight/Left`, `Note`. |
| `Takes/DA_Ghost_<X>` × 10 | Bell, Take, Pick, Breath, Heart, Loving, Attract, Save, Draw, Share. Ids `GHOST_*`, textos en inglés. Los datos van **cocinados** en el APK (sin SaveGame). |
| `BP_GhostPlayer_SC` | El reproductor. 73 variables, 43 funciones. |
| `BP_GhostRecorder_SC` | El grabador (herramienta, tag `TestOnly`), con controles por **mirada**. 43 variables, 33 funciones. |
| `M_Ghost_SC` | Unlit + **aditivo**, borde fresnel (Custom `GhostPS`, salida `''`). Parámetros: `Color`, `Opacity`, `Pressed`, `RimPow`, `RimGain`, `Core`, `PressGain`. |
| `L_GhostRec_SC` | Nivel de grabación: duplicado de `Test_QuestCtrl` + `GhostPreview` (reproductor) + `GhostRecorder` (con `Player` = GhostPreview), los dos `TestOnly`. |

## Formato de los datos
- `float[]` con **stride 28 por cuadro a 30 Hz**, en el espacio del **ancla**: posición de la cabeza al empezar la toma + **yaw del pawn**.
  - 0-5: grip R (x y z pitch yaw roll)
  - 6-11: grip L
  - 12-14: aim R (rot)
  - 15-17: aim L (rot)
  - 18: gatillo R · 19: gatillo L · 20: grip R · 21: grip L
  - 22-27: cabeza
- **Espejo para zurdos** (`bMirror`): intercambia R/L, y → −y, yaw → −yaw, roll → −roll (`GhPose`).

## API del reproductor v2 (para la Obra) — VIGENTE
- `Play(Mirror)`: la toma es la de la instancia (`Take`, referencia directa al DA). Mirror = `not BP_Obra_SC.UserRight`.
- `Stop()`: sale con fundido.
- Lectura: `bPlaying` y `LoopCount`.
- En el juego no muestra mallas hasta `Play`.
- Perillas de instancia:
  - `Take` y `FollowTag` (acompaña a un objeto real y conserva la distancia del editor);
  - `bShowText` y `TextOffset`;
  - `bAutoPlay`/`AutoPlayDelay`/`bAutoMirror` (solo prueba);
  - `OrbRest` (Attract);
  - `bPreview`/`PreviewTime` (vista previa en el editor).
- Colocación: las tomas que no van a la cabeza están en el espacio del ACTOR → mismo offset al objeto real que en `L_GhostRec_SC` (ver `ghost_studio.py`, `STATIONS`). Breath y Heart van a la cabeza (`bHeadAnchor` del DA).

## API del reproductor v1 (HISTÓRICO, ya no existe)
- `Play(DemoId, Color, bMirror)`: busca el DA por `Id` y arranca. Si la toma no existe o está vacía, no hace nada y lo avisa en el log.
- `Stop()`: sale con fundido.
- `LoopCount`: sirve para decidir cuándo insistir.
- `Reanchor()`.
- `PreviewData(...)`: lo usa el grabador para la vista previa.
- Estados (`State`): 0 quieto · 1 aparece · 2 bucle · 3 pausa entre vueltas (`LoopGap`) · 4 se va.
- Pasa **11 poses/s** (`StepHz`), con **4 ecos** (`EchoAlpha` 1 / 0,6 / 0,35 / 0,15 / 0,05). Los componentes se crean en runtime (`GhEnsure`) con las mallas de `BP_QuestCtrl_SC`.
- Gatillo por bisagra (`HingePivotR/AxisR`, 14°); el izquierdo se espeja. Haz opcional por mano. El texto va arriba (`bShowText`, `M_TextUnlit`).
- Perillas `Ghost`: `GhostOpacity` 0,8 · `FadeIn` 0,4 · `FadeOut` 0,6 · `LoopGap` 1 · `TextOffset/TextColor/TextSize` · `AppearSound/VanishSound` (**vacíos: los asigna Narrativa cuando importe FX_GHOSTAPPEAR/OUT**) · `AutoPlayId` (prueba: None) · `TestColor`.

## Grabador
- **Mirada:** cono de `GazeDeg` 4,5°; se sostiene `DwellTime` 1,2 s.
- Botones: 0 `<`, 1 `>`, 2 `REC`, 3 `OK`, 4 `REDO`.
- Flujo: REC -> 3-2-1 (el ancla se toma en ese momento) -> graba `DemoTimes[Idx]` s a `RecHz` 30 -> vista previa en el reproductor -> OK (escribe **directo en el DA**: en PIE es el mismo objeto) o REDO.
- Captura (`RcCapture`):
  - `GetMotionControllerState` × 4 (grip/aim × R/L, `UnrealWorldSpace`) -> `BreakXRMotionControllerState`, que tiene **9 salidas**, ver gotcha 559;
  - gatillo y grip por `IA_Hand_IndexCurl/Grasp_*` (`IMC_Hands`);
  - cabeza por `PlayerCameraManager`.
- `MarkerPos/MarkerSize` por demo: un marcador de referencia (aproximado, editable).
- Gancho de prueba sin visor: `DebugPress` (-1) "aprieta" un botón con `set_properties` en PIE.

## Estado (2026-09-30)
- ✅ Todo compila con warnings as errors y está guardado. Los 88 ids de nodo se verificaron uno por uno antes de escribir.
- ✅ **Reproductor, PIE sin visor** (toma sintética en `DA_Ghost_Bell`, `AutoPlayId`):
  - `State` 2 -> 3 -> 2, `StepIdx` 0..32, `LoopCount` sube;
  - ecos `Ages` [0,3,2,1] en la mano derecha y 99 (oculto) en la izquierda, que no se usa;
  - 0 errores de Blueprint.
- ✅ **Grabador, PIE sin visor:**
  - REC -> 3-2-1 -> `State` 2 con `N` 101 a los 3,3 s (30 Hz) -> 181 cuadros -> `State` 3, con el reproductor en vista previa (`Frames` 181) -> OK;
  - `DA_Ghost_Bell` quedó con `Frames` 181 y `Data` 5068, `Accepted[0]` y `Idx` 1;
  - `ghost_dump.py` con `SOLO_RESPALDO` escribió el JSON.
  - Después: DA restaurado (0 cuadros), `AutoPlayId` None.
- 🐛 Arreglado en PIE: `RcDebug` reseteaba `DebugPress` ANTES de llamar a `RcPress` con un `bind` del getter (puro, se reevalúa) -> siempre llegaba -1. Ahora primero llama y después resetea. En el visor no afectaba (la mirada llama directo).
- ⬜ **Sesión de grabación con Beltrán** (Quest Link, `TURNO.md` §6).
- ⬜ Integración en la Obra (Narrativa).
- ⬜ Sonidos (Narrativa).
- ⬜ Revisar en el visor que el fantasma se vea bien: sin visor solo se probaron los estados.
