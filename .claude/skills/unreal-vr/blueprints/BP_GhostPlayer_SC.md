# Fantasmas de instrucciones: `BP_GhostPlayer_SC` + `BP_GhostRecorder_SC` + `BP_GhostTake_SC`

Carpeta: `/Game/SoulCharger/Mechanics/Ghost/`. Encargo de Beltrán vía Narrativa (2026-09-30, noche), guion V5.
Plan completo: [`docs/PLAN-FANTASMAS-2026-09-30.md`](../../../../docs/PLAN-FANTASMAS-2026-09-30.md).
Fuentes: `scripts/ghost/`. La hoja del turno es `TURNO.md`; los grafos están en `ghost_player.dsl` / `ghost_recorder.dsl` y las variables en `make_spec.py` -> `ghost_spec.json`.

**Qué es:** Beltrán graba cada gesto de instrucción con los mandos. La obra lo reproduce como un "fantasma" translúcido, dos manos que hacen el gesto, en bucle hasta que el usuario lo hace.

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

## API del reproductor (para la Obra)
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
