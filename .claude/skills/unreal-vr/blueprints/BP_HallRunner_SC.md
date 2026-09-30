# BP_HallRunner_SC — el ENSAYO del Hall en Test_Hall

- **refPath**: `/Game/SoulCharger/Obra/BP_HallRunner_SC.BP_HallRunner_SC` · parent Actor · creado 2026-10-01 (Narrativa, pedido de Beltrán: "la del hall debería contener desde el inicio con el título hasta salir del hall" + un debug director).
- **Instancia**: `HallRunner` en `Test_Hall` (origen), tag **`TestOnly`** → la Obra la destruye al arrancar. En la Obra no hace nada (`IsObra`) y su velo nace oculto.
- Fuentes: `VR_Test/Saved/ClaudeScripts/Obra/hallrunner.json` (DSL), `hallrunner_build.py`; los 6 `HRIn*/HROut*` se armaron por cirugía (ver trampa 1).

## Qué hace (el papel de la Obra en su fase 9)
| RT (s) | Qué |
|---|---|
| 0 | velo negro pegado a la cámara (`Veil`, esfera 60 cm, `M_TourVeil_SC`, sort 32600) · `HUDHideNow` · BioHub `bFakeSignal` si `FakeBio` · spawnea un `BP_Credits_SC` oculto para el título · destruye `BP_ChargeTest_SC` (salvo `KeepChargeTest`) |
| 1 | `HallIntro` del director |
| 2,5 → 13 | título SOUL CHARGER (`HRTitle`, igual a `BP_Obra_SC.IntroTitle`; si existe `Mark_TituloInicio` lo pone en su marca) |
| 3,2 | EEG del HUD de vuelta a 0 (en Test_Hall el HUD nace solo a los 3 s: `bBirthOnStart`) |
| 3,5 → 5,5 | abre el velo |
| — | música como la Obra: Intro (hasta el fin del título) → Start → Hall (`DoorW` > 0,3) → silencio (`DoorE` > 0,05); fundidos de 3 s a 0,8 |
| `bHudBorn` del Hall | `HUDAppear` + colores del alma elegida en `RingSoul`/`Sister`; EEG `Birth` 1 s después |
| `bHallDone` | el velo cierra en 2 s; a los 3 s `OpenLevel(LevelName)` si `Loop` |

## Variables (categoría **Ensayo**, instance-editable)
`DebugStart` (−1) · `DebugSoul` (0) · `Loop` (true) · `LevelName` (`Test_Hall`) · `FakeBio` (true) · `KeepChargeTest` (false). Internas: `IsObra`, `RT`, `Called`, `TitleSt`, `AmbNow`, `HudDone`, `HudAt`, `EEGDone`, `EndT`, `Ended`, `JumpStep`, `HudReset`. Componentes: `Veil`, `AmbIntro`/`AmbStart`/`AmbHall` (AudioComponent con Ambient_Clip_1/2/3, sin autoactivar).

## Arranque de debug (`DebugStart`)
| Valor | Paso del Hall | Qué deja hecho antes (`HRPrep`) |
|---|---|---|
| −1 / 0 / 1 | desde el inicio, con título | — |
| 2 | 4 · el portal se enciende | — |
| 3 | 6 · timbre | — |
| 4 | 10 · Alma aparece | pawn en `StopInside` |
| 5 | 12 · sensor | + Alma en el centro |
| 6 | 14 · elección del alma | + Alma al costado + sensor tomado con la derecha (`HallGrab`) |
| 7 | 16 · baldosas / etapas | + almas (`soul_pick`) ocultas y `ChosenSoul` = `DebugSoul` |
| 8 | 24 · nace el HUD | ídem |
| 9 | 26 · Alma a la puerta (salida) | + `bHudBorn` (el HUD nace con esos colores) |
Usa el salto propio del director (`bTestIntro` + `TestFromStep`, fijados en runtime antes de `HallIntro`); el título se salta y el velo abre en 1,2 → 2,4 s.

## Probado en PIE (2026-10-01), 0 errores
Desde el inicio (título a 2,5 s, ambiente 1 → 2 a los 13 s, pasos 0-4) · `DebugStart` 3 (timbre en su marca) · 6 (sensor en su marca, paso 14 en 0,03 s, almas despiertan) · 8 (HUD con el alma 0, pasos 24-26).

## Arreglos tras la primera prueba de Beltrán (2026-10-01)
- **No sonaba la música**: los `Amb*` eran 3D (`bAllowSpatialization`) sobre el actor en el origen y el usuario parte a 36 m. Ahora son 2D. ⚠ Cambiarlo en la plantilla del BP NO llegó a la instancia colocada: hubo que ponerlo también en los componentes de `HallRunner` en Test_Hall.
- **El EEG del HUD se veía desde el inicio**: la instancia del HUD en Test_Hall tenía `bBirthOnStart` true (`BirthDelay` 4, andamio de otra prueba). Quedó en **false**, como en la Obra; el HUD nace cuando lo pide el Hall.
- **Bandas en la niebla** (Beltrán: "el degradé hacia negro se ve horripilante"). Causas:
  - el azul casi negro (0,004–0,045 lineal) da ~20 niveles de 8 bits en toda la esfera;
  - `Floor` 0,02, heredado del velo, dejaba la parte de arriba en gris plano;
  - el fundido por alpha de 12 s vuelve a cuantizar el rango oscuro.

  Cura, **solo en `M_HallFog_SC`**:
  - dither triangular (TPDF) de ±1 nivel en sRGB sobre `col × Alpha`, que es lo que llega a la pantalla sobre negro, y después se divide por `Alpha`;
  - `Floor` con default 0.

  Un primer dither de ±½ nivel no alcanzó. `M_TourVeil_SC` (velo de las transiciones, aprobado) quedó con su código original, sin dither.

## 🔴 Trampas
1. `Audio|Components|Audio|FadeIn/FadeOut` en el DSL resuelve al de **SynthComponent** ("Could not connect pin X to self"), y `add_variable`/`add_object_variable` no dan una variable AudioComponent usable. Solución: 3 componentes de audio + 6 funciones `HRInIntro`… cuyo nodo se creó con `create_node` + **`declaring_class: /Script/Engine.AudioComponent`** (como `BP_BreathProbe`).
2. `Math|Vector|vector+vector` (etiqueta del read) no se puede escribir: usar `(+ a b)`.
3. El salto del director deja al pawn en `TP_hall_pawn` (la puerta) aunque el paso sea adentro: `HRPrep` lo pasa a `StopInside` desde el paso 10.
4. Si se crea el sensor sin tomarlo, el Hall espera su cortafuegos `FW_Tool` (20 s): por eso `HallGrab`.
