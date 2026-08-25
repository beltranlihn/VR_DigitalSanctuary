# BP_Elevator_SC — el ascensor de Recognizing (Core/Rooms/)

> `/Game/SoulCharger/Core/Rooms/BP_Elevator_SC` · creado 2026-08-25 · **una instancia** en `MapsV2/RoomsV2/L_Recognizing_SC` (`Elevator_Recognizing`, en 3000/0/100).
> **Estado: 🟢 cadena completa verificada en PIE por log y medición (beats reales del sensor → kicks → subida 1:1 → cierre por distancia → `StepTimeDone`); falta visor.**

## Qué es
La ilusión de descenso de Recognizing: **el pawn queda quieto y los objetos tagueados suben**. Cada
medio latido del usuario (el `OnBeatPulse` de [[BP_Sensor_Soul]] en modo 2) da un **impulso de
velocidad que decae** hasta el siguiente; si el usuario sale del umbral con el viaje ya iniciado, los
objetos siguen a una **velocidad constante lenta** (`CoastSpeed`). Al acumular la distancia total, el
muro de abajo queda **exactamente** donde estaba el de arriba y el ascensor **cierra la etapa**
llamando `BP_Director_Story.StepTimeDone()` (que ya trae la guarda `WaitFor=="time"`, así el
cortafuegos por tiempo convive sin doble cierre — mismo patrón que [[BP_BreathRing_SC]]).

## 🔴 El sistema de autoría: TAGS, no spline
- **`rise`** — todo actor del sublevel con este tag SUBE (mismo `AddActorWorldOffset` en Z para todos).
  Agregar/quitar/cambiar meshes = taguear actores en el editor, cero código.
- **`rise_top`** / **`rise_bottom`** — los dos marcadores de distancia: `TravelDist = Z(top) − Z(bottom)`,
  medido en el boot. **Cambiar el recorrido = arrastrar el muro de abajo.** El bottom lleva también
  `rise`, así termina ocupando el lugar del top.
- Tagueado hoy en `L_Recognizing_SC`: piso de la sala (`StaticMeshActor_0`), muro de la sala
  (`_1`, top), muro duplicado abajo (`_2`, bottom), y 3 muros intermedios de referencia
  (`Muro_Rise_A/B/C`, en Z −1400/−2900/−4300, mismo `MI_Recognizing_Muro`). **La puerta y el panel NO
  llevan tag** (decisión de Beltrán: sube muro y piso, puerta no).
- 🔴 **El fade entre niveles ya está cubierto**: los meshes usan `MI_Recognizing_Muro` (deriva de
  `M_RoomInterior` → multiplica por `MPC_Room.RoomLight`). Todo mesh nuevo del nivel debe usar un
  material de esa familia para fundir con la sala.

## La física del pulso
`Velocity` (cm/s), una sola variable:
- **Beat** (`ElvBeat`, bindeado a `OnBeatPulse`): si `bArmed && !bDone` → `bStarted=true` y
  `Velocity = PulseKick`.
- **Tick** (`ElvStep`): si `bStarted && !bDone` → `Velocity = FInterpTo(Velocity, CoastSpeed, DT,
  DecaySpeed)` (decae exponencial hacia el piso), paso = `min( min(Velocity, vLand)·DT, restante )`
  (el **clamp** que deja el muro exacto), mueve todo, acumula `Traveled`, y al llegar → `ElvFinish`.
- 🆕 **Aterrizaje suave (2026-08-25, v2)**: `vLand = max( LandRate·√restante, 35 )` — el perfil de
  **frenada física** (desaceleración constante, como un ascensor real): llega en tiempo finito.
  🔴 La v1 era exponencial (`restante/LandTime`, asintótica) y Beltrán la rechazó en visor:
  *"el tiempo cuando estoy cada vez más cerca se hace eterno, como que no llega nunca"* — una
  exponencial nunca llega y el piso de 5 cm/s arrastraba el último tramo. Con la √: el freno engancha
  a `restante = (Velocity/LandRate)²` (~3.4 m con kicks de 110), decrece como raíz, y el piso de
  **35 cm/s** (literal en el Max) cierra los últimos ~35 cm en un segundo. Verificado en PIE:
  el último medio metro pasó en ~2 s y `Traveled == TravelDist` exacto.
  👉 Lección: **"llegada suave" = desaceleración perceptible que TERMINA; un cap exponencial se
  siente como no llegar nunca.** El perfil correcto para frenar hacia un punto es `v ∝ √distancia`.
- Sin umbral nunca alcanzado → `bStarted=false` → nada se mueve. Fuera del umbral con viaje iniciado
  → no llegan beats → `Velocity` decae hasta `CoastSpeed` y queda constante. El feedback (zumbido,
  audio, círculo) lo gobierna el sensor, no este BP.

## Registro de variables
| Cat | Variable | Default | Rol |
|---|---|---|---|
| A - Ascensor | `PulseKick` | **110** cm/s | El impulso de cada medio latido. Con BPM fake ~75 (medio latido cada ~1.6 s) da media ~65 cm/s → los 57.3 m en ~90 s (la duración pedida). |
| A - Ascensor | `CoastSpeed` | **20** cm/s | La velocidad lenta constante fuera del umbral (y el piso del decay). |
| A - Ascensor | `DecaySpeed` | **1.0** | Velocidad del `FInterpTo` del decay (mayor = el kick muere antes). |
| A - Ascensor | 🆕 `LandRate` | **6.0** | La pendiente del freno √ de llegada: **más chico = frena desde más lejos y más suave**; más grande = frena más tarde y llega más rápido. (Reemplazó a `LandTime`, eliminada con la v1.) |
| A - Ascensor | `RiseTag` / `TopTag` / `BottomTag` | rise / rise_top / rise_bottom | Los tags del sistema. |
| Z (Default) | `RiseActors` · `TravelDist` · `Traveled` · `Velocity` · `bArmed` · `bStarted` · `bDone` · `bRefsOk` · `SensorRef` · `StoryRef` | | Estado interno. `bRefsOk` guarda el `StepTimeDone` (sin IsValid — los `Utilities|IsValid` del catálogo son ambiguos). |

## Estructura (7 grafos)
- **EventGraph**: `BeginPlay → SetTimer("ElvBoot", 0.5)` · `Tick → ElvStep(DT)` ·
  `ElvBeat` (el handler del beat) · `ElvBind` (el `BindEventtoOnBeatPulse`, llamado desde `ElvBoot`
  cuando `SensorRef` ya está cacheado; **el pin Delegate se conectó por cirugía** al `OutputDelegate`
  de `ElvBeat` — el DSL no puede).
- **`ElvBoot`**: junta los `rise`, llama **`ElvMobilize`**, mide `TravelDist` de los marcadores,
  cachea sensor y director (casts), `bRefsOk`, `ElvBind`. Logs: `piezas rise = N` y `recorrido = X`.
- **`ElvMobilize`**: 🔴 fuerza **`SetMobility(Movable)`** en el root de cada pieza — los
  `StaticMeshActor` colocados nacen **Static** y `AddActorWorldOffset` falla EN SILENCIO (lo cazó la
  medición: `Traveled` avanzaba y el muro no). Gracias a esto Beltrán taguea cualquier mesh sin
  acordarse de la movilidad.
- **`ElvArm`** (API pública): la llama `BP_Director_Story.ElevatorCue()` al terminar las
  instrucciones (dentro de `StartStepTime`, solo `Room==2`).
- **`ElvStep`** / **`ElvMove(Dz)`** / **`ElvFinish`**.

## 🔴 Trampa pagada: el offset DOBLE por actores attacheados
El muro de abajo estaba **attacheado al de arriba** (Beltrán lo duplicó como hijo) → recibía el
offset del padre + el suyo = subía 2×. Se cazó midiendo la proporción muro/`Traveled` (1.8→2.0).
**Fix en `ElvMove`**: solo se mueve un actor si su `GetAttachParentActor` **no está** en
`RiseActors` (branch por `ContainsItem`, pin else). Los hijos viajan con su padre, una sola vez.
👉 Regla general: al mover una LISTA de actores, filtrar los que ya heredan el movimiento por attach.

## ✅ Verificado (2026-08-25, PIE con zona forzada)
Para probar sin visor: `HeartVDropMin=0` **en la instancia PIE o editor del sensor** (en escritorio
la mano queda a la altura de la cámara → VDrop=0 y la zona real nunca abre; la cámara y los grips
**no se dejan mover** por set_properties — algo los resetea cada tick, ni con `bLockToHmd=false`).
- Boot: `piezas rise = 6`, `recorrido = 5732.27` (= ΔZ real de los muros) ✓
- `armado - esperando el primer pulso` al terminar el panel (autotest) ✓
- Beats del sensor cada ~1.6 s → kicks → `Velocity` oscilando 110→~36 → subida de TODOS los
  tagueados **1:1 con `Traveled`** (medido bottom + intermedio) ✓
- Cierre: `recorrido completo - cierra la etapa` → **mismo timestamp** `STORY: sala 2 paso 4
  espera: vo` (la ameba viaja a `soul_pick_2` = la carga) ✓ · el cortafuegos de `StepTimes[2]`=240 s
  cerró solo la corrida sin beats, a los 240.0 s exactos ✓ · cero `Accessed None` ✓

## TODO
- [ ] 🔴 **Visor**: sentir el ritmo del kick (ajustar `PulseKick`/`DecaySpeed`/`CoastSpeed` en la
  instancia), el zumbido + pulso + audio del sensor en zona, el círculo de la página, y si los muros
  intermedios alcanzan como referencia de paso.
- [ ] El final deja al pawn sin piso a la vista (el piso tagueado se fue arriba); decidir en visor si
  el muro que llega (bottom) alcanza o si va un piso nuevo llegando con él.
- [ ] Si el intervalo del OnBeatPulse cambia (OSC real), revisar que `PulseKick` siga dando ~90 s.

## Relacionados
[[BP_Sensor_Soul]] (modo 2: zona, beats, feedback) · [[BP_Director_Story]] (`ElevatorCue`,
`StepTimeDone`, `ArmHeart`, `TickHeartFx`) · [[BP_InstructionsPanel_SC]] (el círculo del latido) ·
[[BP_BreathRing_SC]] (el patrón de cierre reusado)
