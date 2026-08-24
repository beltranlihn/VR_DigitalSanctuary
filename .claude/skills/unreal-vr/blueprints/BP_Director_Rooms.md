# BP_Director_Rooms — la carga y descarga de salas (Core/Flow/)

## Purpose
El actor del nivel persistente que corre **la transición entre salas**: fundido a negro de todo el mundo, descarga del sublevel actual, carga del siguiente, **encendido de las luces del interior** y, si corresponde, el aviso al recorrido para que avance.

Pedido de Beltrán (2026-08-17): *"Level actual donde estamos, el material pasa a emissive 0 y color totalmente negro. Justo cuando llega a negro, se descarga ese sublevel y se carga el siguiente. Apenas se carga, los materiales de su BP Door y de su interior suben desde negro hasta sus valores definidos. Al terminar de subir, en no más de un segundo, se gatilla el avanzar."* Y la intención: *"generar la sensación de que cuando se acabó la etapa, nos vamos a negro y se ilumina un espacio que revela un portal como si siempre hubiera existido"* · *"es lograr el efecto como si se encendieran las luces de un interior"*.

## Status
🟢 **Ciclo completo verificado en PIE por log (2026-08-17)**: las 6 salas en orden (0→1→2→3→4→5), **una sola sala cargada a la vez** (medido por `find_actors` en el mundo de PIE: un único actor `Muro`), y **cero `Accessed None`**. **Falta el test en visor** — el ritmo del fundido y si el encendido se siente como luces prendiéndose sólo se juzga ahí.

---

## 🔴 La pieza central: el fundido NO es una esfera negra, es una perilla de material

**`MPC_Room`** (`Asset/RoomBase/MPC_Room`) es una **Material Parameter Collection** con un solo escalar, **`RoomLight`** (0 = negro, 1 = valores de autor). Está metido como **multiplicador del `BaseColor` y del `Emissive`** en los tres maestros que pinta la obra:

| Maestro | Quién lo usa | Qué multiplica |
|---|---|---|
| **`M_DoorSolid`** (`Asset/Door/`) | las puertas **y** `M_InteriorMuro` / `M_InteriorPiso` / `M_FueraMuro`, que son instancias suyas | `BaseColor` y `Emissive` |
| **`M_DoorGlass`** (`Asset/Door/`) | el vidrio de las hojas (unlit translúcido) | el emisivo de salida |
| 🆕 **`M_RoomInterior`** (`Asset/RoomBase/`) | el interior de las salas | `BaseColor` y `Emissive` |

**Por qué una MPC y no materiales dinámicos por actor** (la decisión que hace que todo lo demás sea corto):
- **Una sola llamada mueve el mundo entero.** Cero enumerar actores, cero MID, cero BP por sala.
- 🔴 **Cruza el borde del streaming gratis.** La sala entra al mundo con `RoomLight = 0`, así que **nace negra**: no hay carrera ni destello en el primer frame, que es el bug clásico de este efecto.
- En Quest cuesta **una lectura de uniform buffer**, más barato que N materiales dinámicos.
- ⚠ **Limitación aceptada: es global.** No se puede tener una sala encendida y otra apagada. En esta secuencia nunca hace falta (es serial), pero si algún día dos salas tienen que convivir con luces distintas, hay que partir en dos escalares.

⚠ **El exterior no participa**: `M_RoomExterior` es **unlit y sin parámetros** → negro puro siempre, y es el shader más barato posible para una superficie grande. Es lo que se ve al caminar entre salas.

### 🔴🔴 El título de la puerta NO puede leer la colección — hay que EMPUJARLE el valor
El `WidgetComponent` del título ([[BP_Door_SC]]) es UMG: no lo pinta ningún material nuestro, así que la perilla global no le llega sola. Se resolvió con **`ApplyTitleLight(L)`** en la puerta, que hace `SetTintColorAndOpacity(Title, (L,L,L,L))` — a 0 el texto queda negro **y transparente**, a 1 a pleno; y **`ApplyLight(V)` del director recorre todas las `BP_Door_SC` del mundo y se lo pasa**. Como sólo hay una sala cargada, el `GetAllActorsOfClass` toca 1-2 actores y sólo durante los fundidos.

🔴 **El primer intento fue al revés y NO FUNCIONA: que la puerta LEA `RoomLight` con `GetScalarParameterValue`.** Medido por log: el nodo devuelve **0.0 en todos los frames** mientras las salas se encienden perfecto — o sea `SetScalarParameterValue` escribe y ese `Get` no lo ve, sin ningún warning en el log (la rama de error del motor sólo avisa por nombre de parámetro inválido, y `Collection` nulo devuelve 0 **en silencio**). El pin `Collection` tenía el path correcto y no hubo warning de world context, así que la causa quedó sin identificar: **la conclusión práctica es no usar ese getter desde Blueprint en este proyecto**.
👉 Regla que queda: **la colección es un canal de ESCRITURA hacia los materiales, no un lugar donde guardar estado para leer.** El estado vive en el director, que lo empuja.

**Y la trampa que lo hizo visible:** los `WidgetComponent` de las puertas ya colocadas nacían con su tint serializado en blanco, así que aparecían **en blanco durante el negro**. Por eso el CDO del `Title` quedó en `(0,0,0,0)` y **`PhaseWait` llama `ApplyLight(0)` en cada tick del negro**: la puerta que entra por streaming se apaga antes de que nadie la vea.

---

## Registro de variables

### A - Salas (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `RoomLevels` | `[L_Hall_SC, L_Entering_SC, L_Recognizing_SC, L_Loving_SC, L_Attracting_SC, L_Surrounding_SC]` | 🔴 **El orden de las salas.** Son los nombres de los sublevels **registrados** en el persistente. Reordenar la obra es reordenar este array; no se toca ningún nodo. |
| ~~`HallStop`~~ | 1 | 🗑️ **En desuso desde 2026-08-17.** Era la parada del spline que encendía el Hall. Ahora el Hall entra **cuando arranca el efecto de caminata** — ver abajo. Queda la variable por si hace falta volver atrás. |

### B - Tiempos (instance-editable) — las palancas del ritmo
| Variable | Default | Rol |
|---|---|---|
| `FadeOutTime` | 1.2 s | Cuánto tarda el mundo en irse a negro. |
| `FadeOutPower` | 2.5 | 🔴 **La forma del apagón, y la palanca contra el "mucho rato en negro"** (pedido de Beltrán, 2026-08-17). La luz baja como `L = 1 − tᵖ`: **1 = lineal · 2-3 = la sala se mantiene encendida y se apaga de golpe al final**. Con p=2,5 la luz recién cae bajo 0,1 al **96 %** del tiempo, así que el negro percibido dura ~0,2 s en vez de ~1 s. **Bajarlo alarga el negro; subirlo lo acorta.** ⚠ **NO es smootherstep**: esa curva (la del fade in, que sí queda) llega a cero con velocidad cero y por eso se quedaba mucho rato casi negra. |
| `BlackHold` | 0.15 s | 🔴 **El MÍNIMO de negro.** El negro real dura `max(BlackHold, lo que tarde la carga)`; la carga mide ~0,11 s, así que 0,15 es un margen ajustado pero seguro. |
| `FadeInTime` | 2.5 s | Cuánto tardan en **encenderse las luces** de la sala nueva. |
| `HoldAfterLight` | 0.8 s | Cuánto se queda quieto con la sala encendida antes de gatillar el avance. El pedido era "no más de un segundo". |

### C - Test (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `bDebugKey` | **true** | 🧪 **La tecla `2` dispara `EndStage()`** — el "término de nivel" provisorio. Igual que la tecla `1` de [[BP_Director_Movement]]: `WasInputKeyJustPressed` en el Tick, **sin Enhanced Input, sin IMC**. Apagar para la obra final. |
| `bAutoDemo` | false | 🧪 **Recorre las 6 salas solo**, disparando `EndStage` cada `AutoDemoGap` segundos de reposo. Es como se verificó el ciclo por log sin tocar ninguna tecla. |
| `AutoDemoGap` | 4 s | La pausa del modo automático. |

### Z - Estado interno (no tocar)
`RoomIndex` (sala cargada; **−1 = ninguna**) · `PendingIndex` · `OldIndex` (la que hay que descargar) · `Phase` · `Elapsed` · `IdleTime` · `bLoadDone` · `bAdvanceAfter` · `bHallDone` · `MoveRef`.

---

## La máquina de fases (`Phase`)

| Fase | Qué hace | Sale cuando |
|---|---|---|
| **0 — reposo** | `TickIdle`: cuenta `IdleTime`, mira si toca encender el Hall (`CheckHall`) y atiende el modo automático | alguien llama `EndStage()` o `CheckHall` dispara |
| **1 — fundido a negro** | `RoomLight` va de 1 a 0 por smootherstep en `FadeOutTime` | al llegar a 0 → llama a `DoSwap` |
| **2 — negro** | espera | `Elapsed ≥ BlackHold` **Y** `bLoadDone` |
| **3 — encendido** | `RoomLight` va de 0 a 1 por smootherstep en `FadeInTime` | al llegar a 1 |
| **4 — sostén** | espera con la sala encendida | `Elapsed ≥ HoldAfterLight` → `CallGotoNext` y vuelve a 0 |

🔴 **La espera de la fase 2 es por evento, no por delay.** `LoadStreamLevel` **nunca bloquea** (está hardcodeado en el motor), así que "esperar medio segundo" a veces alcanza y a veces no. Acá el negro dura **lo que sea más largo** entre `BlackHold` y la carga real: el `then` del nodo latente es el completado, y prende `bLoadDone`. Así nunca se ve aparecer geometría.

**Medido en PIE:** de "transicion hacia sala N" a "sala visible" pasaron **1,31 s** con `FadeOutTime = 1,2` → la descarga + carga costó **~0,11 s**. La primera carga (sin sala previa, sin fundido) tardó **18 ms**. O sea: **el negro lo gobierna el fundido, no el streaming** — y por eso la palanca contra "mucho rato en negro" es `FadeOutPower`, no el streaming.

**Ciclo completo medido:** 8,66 s por sala (era 9,41 s antes del ajuste de 2026-08-17).

## Estructura de grafos

**`EventGraph`**
- `BeginPlay` → `ApplyLight(0)` (el mundo arranca negro) + timer 0,25 s → `Boot`. El retraso es el mismo motivo de siempre: `BeginPlay` corre antes del `Possess`.
- `Tick` → `TickDebugKey()` + `TickPhase(DeltaSeconds)`.
- 🔴 **`DoSwap` y `LoadNew` son EVENTOS CUSTOM, no funciones** — `LoadStreamLevel`/`UnloadStreamLevel` son nodos **latentes** y no se pueden poner en un grafo de función.
  - **`DoSwap`**: guarda `OldIndex`, adelanta `RoomIndex`, apaga `bLoadDone` y, **si había sala previa**, la descarga; después llama a `LoadNew` (los dos caminos terminan ahí).
  - **`LoadNew`**: `LoadStreamLevel(nombre, bMakeVisibleAfterLoad=true, bShouldBlockOnLoad=false)` → al completar, `bLoadDone = true` y loguea.

**Funciones**
- **`ApplyLight(V)`** — 🔴 el corazón: `SetScalarParameterValue(MPC_Room, "RoomLight", V)` **+ el barrido de puertas** (`GetAllActorsOfClass(BP_Door_SC)` → `ApplyTitleLight(V)` en cada una), porque el título es UMG y no lo alcanza la colección (ver arriba).
- **`Smoother(T)`** — smootherstep `6t⁵ − 15t⁴ + 10t³` (velocidad **y** aceleración cero en los extremos), la misma curva que usa el recorrido.
- **`BeginTransition(Index, Advance)`** — el único punto de entrada. Si **no hay sala cargada** (`RoomIndex < 0`) se saltea el fundido de salida y va directo a la fase 2: ya estamos en negro.
- **`TickPhase(DT)` / `TickIdle(DT)` / `RunPhase()`** — el reparto por fase (cadena `if/elif`, no `switch`: el `SwitchOnInt` del DSL sólo expone los pines 0-3).
- **`PhaseFadeOut` / `PhaseWait` / `PhaseFadeIn` / `PhaseHold`** — una función por fase.
- **`CheckHall()`** — el disparo del Hall. Guarda triple: `!bHallDone` **y** `RoomIndex < 0` **y** `WalkFXStarted()`. 🔴 **Desde 2026-08-17 el Hall entra cuando arranca el efecto de caminata**, no al llegar a una parada: el primer tramo es continuo hasta la boca del Hall y el momento lo fija `WalkStartFrac` de [[BP_Director_Movement]] — un solo número para las luces y el paso.
- **`WalkFXStarted()`** — lee `bFXStarted` del director de movimiento con guarda de validez (gemela de `LegIndexSafe`).
- **`EndStage()`** — 🔴 **la API pública, el "término de nivel"**. Sólo corre si `Phase == 0` y queda sala por delante.
- **`CallGotoNext()`** — si `bAdvanceAfter`, llama `GotoNext()` de [[BP_Director_Movement]]; si no, loguea y se queda.
- **`LevelNameAt(Index)` / `LegIndexSafe()` / `Boot()` / `CacheMove()` / `TickDebugKey()`** — auxiliares. `CacheMove` busca el director de movimiento por `GetAllActorsOfClass` + cast, así no hay que asignar nada a mano en el nivel.

## Contrato con el resto
- **Entrada del Hall**: llegar a la parada `HallStop` del spline de [[BP_Director_Movement]] (se lee `LegIndex` por polling, no por dispatcher).
- **Entrada del resto**: `EndStage()` — hoy la tecla `2`; mañana, lo que avise que la etapa terminó.
- **Salida**: `GotoNext()` de [[BP_Director_Movement]].
- **Los 6 sublevels arrancan DESCARGADOS**: `bInitiallyLoaded` y `bInitiallyVisible` en **false** en los seis `LevelStreamingDynamic` de `L_SoulCharger`. 🔴 Son **esos** dos, no `bShouldBe*` (§107 de gotchas).

## 🐛 ✅ ARREGLADO en la verificación: el Hall se volvía a encender a mitad del recorrido
El primer log dio `0 → 1 → 0 → 1`. La causa: `CheckHall` sólo miraba `bHallDone` y el índice de parada, así que cuando el pawn llegaba a la parada 1 —ya con otra sala cargada— **volvía a pedir el Hall**. Fix: agregar `RoomIndex < 0` a la guarda. Después de eso el log da `0 → 1 → 2 → 3 → 4 → 5` monótono.

## 🧪 2026-08-21 — `DebugJumpTo(Index)`: cargar cualquier sala al arrancar
La API que usa el `DebugStartRoom` de [[BP_Director_Story]] para saltar a una etapa. Tres líneas, todas apoyadas en la máquina que ya existía:
```
DebugJumpTo(Index):
  log
  bHallDone = true                        ← 🔴 para que CheckHall NO vuelva a encender el Hall después
  if bHallPreloaded:
      if Index == 0 → HallInstant()       ← ya está cargado: no se descarga y recarga sin necesidad
      else          → RoomIndex = 0 ; BeginTransition(Index, false)
  else              → BeginTransition(Index, false)
```
🔴 **La línea que importa es `RoomIndex = 0`.** Con `bPreloadHall` (default true) el Hall entra al mundo en el arranque, pero `RoomIndex` sigue en −1 porque nadie "entró" todavía. Si se llamara `BeginTransition` así, el `DoSwap` vería que **no hay sala previa**, no descargaría nada, y quedarían **dos salas cargadas a la vez** — justo lo que esta clase existe para evitar. Diciéndole que la sala actual es el Hall (que es la verdad: está cargado), la transición normal lo descarga sola y no hace falta ningún camino nuevo.

Verificado por log: `SALTO DE DEBUG a la sala 3` → `transicion hacia sala 3` → `sala visible, indice 3` → `sala encendida`, con el Hall descargado en el mismo swap. Y con `Index = 0`, `HallInstant` (sin recarga).

## TODO
- [x] ✅ **Race de `MID_L`/`MID_R` en [[BP_Door_SC]] — ARREGLADO 2026-08-21.** La causa real no era el fundido sino el `Tick` de la puerta: `BeginPlay → SetTimer("Boot", 0.3)` crea los materiales dinámicos, pero `TickDoor → Apply` los lee desde el frame 1. En la obra normal se llega caminando mucho después de 0,3 s; **el salto de debug de [[BP_Director_Story]] deja al pawn pegado a la puerta en el frame 1** y lo destapó como una catarata de errores. Fix: guarda `IsValid(MID_L)` sobre los dos `SetVectorParameterValue` de `Apply`. Verificado: cero `Accessed None`.
- [ ] 🔴 **Visor**: ajustar `FadeOutTime` / `FadeInTime` / `HoldAfterLight` contra la sensación real. Lo medible ya está verificado; el ritmo no.
- [ ] Cargar los colores y las texturas de cada sala en sus `MI_<Sala>_Muro` / `MI_<Sala>_Piso` (hoy todas heredan el gris del maestro).
- [ ] Cambiar la tecla `2` por el aviso real de "término de nivel" cuando exista.
- [ ] Bajar `s.LevelStreamingActorsUpdateTimeLimit` de 5,0 a 1-2 ms (el default se come el 36 % del frame de VR — ver `streaming-arch.md` §4).
- [ ] Registrar los 7 mapas en Packaging Settings antes de empaquetar.
- [ ] ⚠ **El hueco del cielo**: mientras no hay sala cargada, nada tapa el `BP_Sky_Sphere` del persistente. Beltrán dice que el entorno final va a ser oscuro; si en visor se ve el degradado, la salida es una cáscara negra permanente en el persistente.

## Relacionados
- [[BP_Director_Movement]] — el recorrido; le pide `LegIndex` y le llama `GotoNext`.
- [[BP_Door_SC]] — la puerta de cada sala; su vidrio y su marco se encienden con la misma perilla.
- [[BP_StageDirector]] — el director del esqueleto viejo, que hacía esto con fade sphere y `LoadLevelInstance`.

## 🎬 2026-08-19 — `CloseRoom()`: fundir y descargar SIN sala siguiente
Para el final de Surrounding (*"aquí desaparece el nivel; ya no avanzamos, pero la arquitectura desaparece"*): **`CloseRoom()`** = `BeginTransition(-1, false)` si `Phase==0` y hay sala. `DoSwap` descarga la actual y llama `LoadNew`, que ahora tiene una **guarda por cirugía**: `if RoomIndex >= 0 → LoadStreamLevel` · `else → bLoadDone=true` + log `SALAS: sala cerrada, no hay siguiente (final)`. El resto de la máquina sigue igual (fase 3 sube `RoomLight` a 1 sin sala cargada — no se ve nada porque no hay nada; `CallGotoNext` con `bAdvanceAfter=false` no avanza). El que lo llama es [[BP_Director_Story]] (`BeginEnding`). `EndStage()` **no cambió**: sigue siendo el cierre normal con sala siguiente.

## ⚡ 2026-08-21 — el Hall se PRECARGA en el arranque (mata el hitch de entrada)
Beltrán seguía viendo el corte al entrar al Hall aun con el PSO precache. **Medido en el log del device**: el Hall pasa de "transicion" a "sala visible" en **94 ms repartidos en 3 frames** (~31 ms cada uno), mientras las salas 1-5 hacen lo mismo en **604 ms repartidos en 42 frames** (14,4 ms/frame = ritmo normal). O sea: **sólo el Hall concentra la carga**, porque su transición **se saltea el fundido** (`RoomIndex < 0` → directo a la fase 2) y encima ocurre **mientras el usuario camina**, no bajo un negro estático.
✅ **Solución: cargarlo cuando no cuesta nada.** `Boot()` → **`PreloadHall`** (evento; `LoadStreamLevel` es latente) trae el Hall **en el arranque de la app**, cuando todo está en negro; como `RoomLight = 0`, la sala **nace negra y no se ve** (el principio de siempre), y un `ApplyLight(0)` posterior apaga el título de la puerta que acaba de entrar. Cuando llega el momento real, **`CheckHall` ramifica**: si `bHallPreloaded` → **`HallInstant()`** (fija `RoomIndex = 0`, `bLoadDone = true` y salta **directo a la fase 3**, el encendido) en vez de `BeginTransition`. Cero streaming en el instante sensible.
- Perilla: **`bPreloadHall`** (cat. *A - Salas*, true). En false vuelve al comportamiento anterior.
- ✅ Verificado en PIE: `Hall PRECARGADO en negro` a los **17 ms** del boot, y después `arranco la caminata, enciendo el Hall` → `sala encendida` 1,5 s más tarde (el `FadeInTime`), cero `Accessed None`.
💡 Encaja con el plan de Beltrán de poner una esfera azul de intro: la precarga transcurre justo ahí.
