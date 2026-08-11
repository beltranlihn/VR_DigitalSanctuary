# BP_StageDirector — el ciclo de transición (Core/Flow/)

## Purpose
El orquestador del §9.4: lleva la lista ordenada de etapas, mueve el pawn por el spline y maneja las compuertas. Vive en el **nivel persistente**. Implementa el ciclo de transición del §9.2 completo:

```
precarga del sublevel siguiente (invisible)
la luz de la sala baja + se traza el marco + se enciende el cartel
negro completo -> swap: oculta A, muestra B, reposiciona el pawn
la puerta abre -> la nueva sala sube de luz
```

**Reemplaza a `BP_FlowDirector`**, que era un smoke test con delays hardcodeados (su actor ya se quitó de `L_Persistent`).

## Status
🟡 **Ciclo completo funcionando y loopeando, verificado por log en PIE (2026-08-11).** Falta el test en visor y quedan 2 bugs conocidos (abajo).

## Cómo está encadenado
🔴 **Los saltos entre tramos van por `SetTimerByFunctionName`, no por `Delay`.** Un `Delay` no es válido dentro de una función, y el ciclo necesita esperas entre pasos; los timers por nombre funcionan sobre **custom events** igual que sobre funciones, así que cada tramo es un evento aparte y el anterior lo agenda. Ventaja lateral: cada tramo es un punto de entrada nombrado, así que `BP_DebugDirector` va a poder saltar a cualquiera.

| Evento | Qué hace | Agenda |
|---|---|---|
| `BeginPlay` | Cachea fade y walker · **negro instantáneo** · `PreloadNext(0)` | `ShowAndEnter` a 1.5 s |
| `ShowAndEnter` | `SwapRooms()` | `EnterRoom` a `BlackHold` |
| `EnterRoom` | Cachea room y door de la sala nueva · `ConfigureRoom()` · fade **from** black · `Walk(0→500)` = entra desde el umbral al centro | `EndStage` a `StageDuration` |
| `EndStage` | `StageIndex++` · `WrapIndex()` · `PreloadNext(i)` · `DimAndReveal()` · `RevealDoor()` | `WalkOut` a `RevealHold` |
| `WalkOut` | `Walk(500→1000)` = del centro al umbral · `OpenDoor()` | `GoBlack` a `FadeOutDelay` |
| `GoBlack` | fade **to** black | `ShowAndEnter` a `LegTime` |

El loop cierra en `ShowAndEnter`, así que con el placeholder recorre las 3 etapas de prueba y vuelve a empezar indefinidamente.

🔴 **El reposicionamiento del pawn NO es un teleport aparte**: lo hace `Walk(0, 500, ...)` de `EnterRoom`, porque `StartWalk` fija `Dist = FromDist` y el primer tick coloca al pawn en `spline(0)` = X −500. Un solo mecanismo para mover y para reposicionar, y ocurre bajo negro.

## Registro de variables

### Referencias (se cachean con `GetActorOfClass` + cast)
| Variable | Cuándo se cachea |
|---|---|
| `FadeRef` / `WalkerRef` | `BeginPlay` — viven en el persistente |
| `RoomRef` / `DoorRef` | **cada `EnterRoom`** — son de la sala nueva, así que hay que re-buscarlas después de cada swap |

⚠ Funciona buscar con `GetActorOfClass` (que devuelve el primero) **sólo porque se oculta A antes de mostrar B**: en el instante del swap hay una sola sala en el mundo. Los actores de un sublevel precargado-invisible **no están en el mundo** (no corrió `AddToWorld`), así que no aparecen en la búsqueda. Si alguna vez se muestran dos salas a la vez, esto se rompe.

### Flujo
| Variable | Default | Rol |
|---|---|---|
| `RoomMap` | `/Game/.../L_Room_Placeholder` | El mapa que se instancia. Placeholder: siempre el mismo, cambia sólo el nombre de la instancia. |
| `StageNames` | ENTERING / RECOGNIZING / SURROUNDING | Placeholder de 3 etapas. **Su largo define cuántas hay** (`WrapIndex` cierra el loop). |
| `StageColors` | azul / rojo / verde | El acento de cada sala y de su puerta. Es lo que hace que las transiciones se **vean** distintas siendo el mismo asset. |
| `StageIndex` | 0 | Etapa actual. |
| `CurLevel` / `NextLevel` | — | Los `LevelStreamingDynamic` que devuelve `LoadLevelInstance`. |

### Tiempos (todos instance-editable en el actor del persistente)
| Variable | Default | Rol |
|---|---|---|
| `StageDuration` | 8.0 s | Placeholder de la mecánica de la etapa. Lo reemplaza `BP_StageBase.RunStage()`. |
| `LightRiseTime` | 2.5 s | La sala nueva sube de luz. |
| `LightFadeTime` | 2.0 s | La sala baja al terminar la etapa. |
| `RevealHold` | 2.8 s | Cuánto se mira el marco trazado antes de empezar a caminar. |
| `FadeOutDelay` | 1.2 s | Desde que arranca la caminata hasta que empieza el negro. |
| `FadeOutTime` | 1.5 s | Duración del fundido a negro. |
| `FadeInTime` | 1.8 s | Duración del fundido de entrada. |
| `LegTime` | 4.2 s | Cuánto se deja correr el tramo de salida antes del swap. **Tiene que ser ≥ `FadeOutDelay + FadeOutTime`** o el swap se ve. |
| `BlackHold` | 0.5 s | Negro sostenido después del swap, para que `AddToWorld` termine. |

## Streaming — lo que se respetó de `references/streaming-arch.md`
- ✅ **`OptionalLevelNameOverride` en cada `LoadLevelInstance`** (`Room_0`, `Room_1`, …). Sin eso cada llamada crea un paquete nuevo y **filtra niveles**. Verificado en el log de PIE: las instancias se cargan como `Room_N`.
- ✅ **Precarga invisible**: el nodo BP de `LoadLevelInstance` **no expone `bInitiallyVisible`** y su default en el struct es `true`, así que se llama `SetShouldBeVisible(false)` inmediatamente después. Es la única forma de conseguir el "Make Visible After Load = false" del §9.2 por Blueprint.
- ✅ El swap sólo **cambia visibilidad**, que es lo instantáneo; la carga ya ocurrió segundos antes, durante el revelado de la puerta.
- ⚠ **Pendiente:** disparar por el delegate **`OnLevelShown`** en vez de por `BlackHold`. El nodo existe y está verificado (`EventDispatchers|AssignOnLevelShown`); no se usó todavía para no depender del nombre del evento autogenerado. Hoy `BlackHold` = 0.5 s alcanza porque el nivel ya está cargado, pero **es una suposición temporal y el doc pide eventos de completado**.

## 🐛 Bugs conocidos
1. 🔴 **`OnPawnPassed` de la puerta nueva dispara espurio en el swap.** Visto en el log: dos `OnPawnPassed` seguidos, uno legítimo y otro 0,7 s después, justo tras el swap. Causa: al momento del swap el pawn está en X≈500 (fin del tramo de salida) y la puerta de la sala nueva está en X=460, así que `dot(pawn−door, forward) > 0` es verdadero **antes** de que el tramo de entrada lo reposicione a −500. Como `bPassed` se pone una sola vez, el cruce real de esa puerta después **ya no dispara**.
   **Fix propuesto:** gatear `CheckPassed` a que la puerta esté revelada (`RevealProgress > 0.5`). Es semánticamente correcto además: una puerta que todavía no existe (§9.8) no se puede cruzar. Requiere borrar y recrear el grafo `CheckPassed` (reescribirlo duplicaría el cuerpo).
   **Impacto hoy: ninguno** — nadie consume el dispatcher todavía. Pero hay que arreglarlo **antes** de que el director lo use.
2. ⚠ **La puerta abre antes del negro, no después.** El §9.2 literal dice `negro completo -> swap -> la puerta abre`. Acá abre durante la aproximación, así que se camina a través de una puerta abierta hacia el negro. Se hizo así porque con todas las salas en el mismo origen, la puerta que "abre revelando la sala nueva" quedaría **detrás** del pawn tras el swap. **Es una decisión autoral pendiente de Beltrán**, no un descuido.

## TODO
- [ ] Test en visor.
- [ ] Los 2 bugs de arriba.
- [ ] `OnLevelShown` en lugar de `BlackHold`.
- [ ] Descargar la sala vieja (`SetIsRequestingUnloadAndRemoval`) — hoy quedan todas las instancias cargadas e invisibles. Con 3 salas placeholder no importa; con 9 salas reales **sí**. ⚠ Descargar fuerza un GC (`s.ForceGCAfterLevelStreamedOut` viene en 1) y ese GC **es** el hitch → hacerlo bajo negro.
- [ ] `StageDuration` sale cuando exista `BP_StageBase`: el cierre lo va a pedir la etapa, no un timer.

## Relacionados
- [[BP_Room]] (`Configure`/`SetLight`/`RampLight`) · [[BP_Door]] (`Configure`/`Reveal`/`Open`) · [[BP_Walker]] (`StartWalk`) · `BP_FadeSphere` · `BP_DebugDirector` (sin construir)
