# BP_DebugDirector — la salida de emergencia (Core/Debug/)

## Purpose
El sistema de debug del §9.9. Suelto en el nivel persistente: **se borra y listo**, y **no hay una sola línea de código de debug esparcida por las etapas**.

🔴 **El principio de §9.9, que es lo que define el diseño:** el skip **nunca** es "saltar a la etapa N", siempre es "completar ésta ahora". Teletransportar se saltea efectos colaterales y deja estados inconsistentes que después se depuran como fantasmas. Completar deja el estado bien **por definición**, porque es el mismo código que corre en la experiencia real.

## Status
🟢 **`ForceComplete` verificado por log en PIE.** 🟡 El combo de dos gatillos está cableado y compila, pero **sin probar en visor** (el input de este proyecto es un pozo documentado, ver abajo).

## Dónde vive cada mitad — y por qué
| Mitad | Dónde | Por qué |
|---|---|---|
| **`ForceComplete()`** | **`BP_StageDirector`** | Es el que sabe cerrar una etapa. Limpia el timer de `EndStage` y llama `EndStage`. |
| El **disparador** | `BP_DebugDirector` | Es lo desechable. |

🔴 **`ForceComplete` limpia el timer de `EndStage` ANTES de llamarlo** (`ClearTimerByFunctionName(self, "EndStage")`). Sin eso el timer pendiente de `StageDuration` dispararía **después** y la etapa se cerraría dos veces.

**Verificado en PIE (2026-08-11):** cuatro disparos a 5 s de intervalo, y cada uno produce la cadena `DBG: ForceComplete` → `DIR: ForceComplete` → `DIR: fin de etapa`. Entra por el camino real, no por un atajo.

## Registro de variables
| Variable | Default | Rol |
|---|---|---|
| `bDebugEnabled` | true | Gate general. §9.9 lo quiere colgado de un bool del GameInstance que se apaga en el build; hoy es local porque `GI_SoulCharger` todavía no existe. **Pendiente de migrar.** |
| `HoldTime` | 2.0 s | Cuánto hay que sostener el combo. |
| `SoakEverySeconds` | **0.0 = apagado** | Modo **soak**: dispara `ForceComplete` en loop. Es con lo que se verificó el path, y sirve para dejar el ciclo de transición corriendo solo y buscar leaks o hitches. En la instancia del persistente queda en 0. |
| `bLeftHeld` / `bRightHeld` | — | Estado de cada gatillo. |
| `HeldFor` / `bFired` | — | Acumulador del hold y el latch para que dispare **una sola vez** por sostenida. |
| `DirectorRef` | — | El `BP_StageDirector`, cacheado en `BeginPlay`. |

## Estructura de grafos
- **`BeginPlay`** — `EnableInput` · `CacheDirector()` · si `SoakEverySeconds > 0`, timer en loop a `Fire`.
- **`Tick`** — `UpdateCombo(Δt)`.
- **`UpdateCombo`** → si `bDebugEnabled` **y** los dos gatillos: `TickHold`; si no, `ResetHold`.
- **`TickHold`** → acumula; al pasar `HoldTime` y si no disparó: `bFired = true` + `Fire()`.
- **`Fire`** → `IsValid(DirectorRef)` → `DirectorRef.ForceComplete()`.
- **Eventos de input** — `IA_Shoot_Left` y `IA_Shoot_Right`: `Triggered` → `<Lado>On`, `Completed` → `<Lado>Off`.

⚠ **Los 4 setters son funciones de una línea (`LeftOn`/`LeftOff`/`RightOn`/`RightOff`) a propósito**, para que el cableado del evento de input sea **sólo exec** y no haya que conectar pines de datos por cirugía.

## 🔴 Notas de construcción (input y DSL)
1. **`IA_Shoot_Left`/`IA_Shoot_Right` del XRFramework, y nada más.** Es la única acción de trigger que se entrega de verdad en este proyecto (`references/assets-existentes.md`); inventar una IA/IMC propia se probó y **no dispara nunca**. Usar los dos a la vez cumple el "con combinación" del §9.9 sin inventar assets.
2. 🔴 **Los eventos de input NO se pueden crear desde el DSL.** `(event Input|EnhancedActionEvents|IA_Shoot_Left ...)` falla con *"AddEvent|Input|EnhancedActionEvents|IA_Shoot_Left does not exist"* — el parser le prepone `AddEvent|`. Hay que crearlos con **`create_node`** (type_id `Input|EnhancedActionEvents|IA_Shoot_Left`) y cablearlos con `connect_pins`. Pines de exec: **`Triggered` = índice 0**, `Started` 1, `Ongoing` 2, `Canceled` 3, **`Completed` = índice 4**.
3. ⚠ **El `read_graph_dsl` los muestra VACÍOS** (`(event EnhancedInputActionIA_Shoot_Left (...))` sin cuerpo) aunque estén bien cableados — es el gotcha "DSL read oculta pines". **Verificar con `get_node_infos`**, que sí muestra `connected_pins` en `Triggered` y `Completed`. Confirmado así acá.
4. ⚠ `Triggered` dispara **cada frame** mientras se sostiene → el handler tiene que ser idempotente. `LeftOn` sólo setea un bool, así que lo es.

## 🆕 HUD de debug (2026-08-12) — HECHO, sin UMG
Un `TextRenderComponent` **`HudText`** (material `M_TextUnlit`, worldSize 3, verde, en (55, −16, −14) relativo con yaw 180) y el ACTOR entero **attacheado a la cámara** con la receta de `BP_FadeSphere`. Muestra: `SALA <nombre>  t=<seg>s  EEG OK/--  calm <v>  hr <v>`.
- Cadena: `BeginPlay → StartHud` (si `bShowHud`: timer loop `UpdateHud` 0.25 s; si no: esconde el texto) → `UpdateHud` = `MaybeAttachHud` (cachea BioHub + attach a cámara, una vez) + `RefreshHudText` → `HudLine` (sala + tiempo, del `DirectorRef` ya cacheado) → `HudBioLine` (solo si hay BioHub: conexión/calma/ritmo).
- **`bShowHud`** (instance-editable, true en CDO e instancia): la palanca. Para el build se apaga junto con `bDebugEnabled` (pendiente de migrar los dos al GameInstance).
- Verificado en PIE: `DBG: HUD activo` + `DBG: HUD attacheado a la camara`, cero Accessed None. **La posición/tamaño del texto se juzga en visor** (mover `HudText` en el componente si molesta).

## TODO
- [ ] 🔴 **Probar el combo en visor.** Es lo único sin verificar. Si no responde, el orden de diagnóstico está en `assets-existentes.md` §INPUT: la config del `AddMappingContext` importa más que el asset (`Priority=1000`, `bIgnoreAllPressedKeysUntilRelease=False`, `bForceImmediately=True`), y hoy este BP sólo hace `EnableInput` — que es lo que le alcanza a `BP_BrushTool` como actor suelto del nivel, pero **no está confirmado para este caso**. ⚠ Ahora `BP_MenuButton` tiene la receta completa (`EnsureInput`); si el combo no dispara, copiarla de ahí.
- [ ] Ver el HUD en visor (posición/tamaño/legibilidad del `HudText`).
- [ ] `bDebugEnabled` tiene que pasar a un bool del **GameInstance** cuando exista `GI_SoulCharger`, para poder apagarlo en el build de una sola vez.
- [ ] `ForceComplete(bFastCharge)` — el parámetro del §9.9 (acelerar la animación de carga) no existe todavía porque no hay animación de carga.
- [ ] `JumpToResults` con datos sintéticos — cuando exista el panel de resultados.

## Relacionados
- [[BP_StageDirector]] (dueño de `ForceComplete`) · `references/assets-existentes.md` §INPUT
