# BP_MenuButton — botón por CONTACTO + trigger (Core/UI/)

## Purpose
Los botones del menú de la intro (**START** / **ABOUT US**) y el **timbre** del Center. Se acercan con la mano y se confirman con el gatillo — o, en modo timbre, **solo con sostener la mano cerca**.

## 🆕 Modo TIMBRE (2026-08-12): `bHoldByHover`
Nueva bool instance-editable. En `true`, `UpdateHold` acumula con `(bTrigHeld OR bHoldByHover)` — como `UpdateHold` solo corre cuando hay hover, el resultado es **"apoyar la mano y esperar `HoldTime`"** sin gatillo, que es exactamente lo que Beltrán definió para el timbre. El timbre lo spawnea `BP_StageDirector.SpawnBell` al final del corredor de la intro (label "PLACE YOUR HAND", `HoldTime = BellHoldTime` 1.5 s, destruido tras usarse).
⚠ Detalle conocido: si la mano se aleja a mitad del hold, `HoldT` queda congelado (no se resetea, porque `UpdateHold` deja de correr) y al volver retoma desde ahí. Para un timbre es tolerable; si molesta en visor, el reset va en el else de `TickStep`.

## Status
🟢 **Funcionando end-to-end en PIE** (2026-08-12): se spawnean en sus TargetPoints con su etiqueta, se arman, y al apretar START se destruyen los dos. ⬜ Falta el test en visor (si 45 cm y 18 de radio son cómodos sentado) y el panel de About.

## 🔴 Por qué por CONTACTO y no por beam — decisión de Beltrán
Se lo consultó explícitamente y la respuesta fue **tocando + trigger**, y la razón es el **arco de gestos de la obra**:
```
menú (tocar)  →  timbre (apoyar la mano)  →  sensor (tomar)  →  beam (recién en Attracting)
```
El menú es la **primera** interacción. Si arrancara con beam, se enseñaría el puntero para abandonarlo durante cuatro etapas y recuperarlo al final. Tocando, **rima con el timbre que viene tres segundos después** y con tomar el sensor, y el beam queda como **capacidad nueva** que aparece en *Attracting*. Además enseña "tus manos son reales acá", que es la tesis de la obra.

💡 **`HoldTime` hace que el mismo Blueprint sirva para el timbre.** En **0** confirma al apretar el gatillo (los botones del menú). En **> 0** hay que sostener — que es lo que Beltrán definió para el timbre: *"el timbre que sea con esperar, los otros botones con hover más trigger"*.

## Componentes
| Componente | Qué es |
|---|---|
| `Plate` | Cubo escalado a **3 × 28 × 10 cm**, material **`M_Plate`** (unlit, con `PlateColor` y `Brightness`). Es lo que crece con el hover. ⚠ Antes usaba `M_IntroLogo`, cuyo parámetro `Op` **nace en 0** → el plato era negro sobre negro y no se veía. |
| `Label` | `TextRenderComponent`, worldSize 6. ⚠ Su `yaw 180` obligó a que la intro rote el botón a **yaw del panel + 180**; si no, el texto mira para el lado contrario al usuario. 🔴 Con **`M_TextUnlit`** desde el día uno: el material de fábrica es *lit* y en esta obra **no hay luces**, así que se vería negro (ver `materials-vr.md`). |

## Registro de variables
| Variable | Default | Rol |
|---|---|---|
| `LabelText` | "START" | El texto. Instance-editable: dos instancias, dos textos, un solo BP. |
| `HoverRadius` | 18 cm | Qué tan cerca tiene que estar la mano. |
| `HoldTime` | **0** | 0 = confirma al apretar. > 0 = hay que sostener (el timbre). |
| `HoverScale` / `HoverSpeed` | 1.18 / 8 | Cuánto crece al hover y qué tan rápido. |
| `bArmed` | false | 🔴 **Nace desarmado**: el botón no existe para el usuario hasta que la intro lo arma. Sin esto, apretar el gatillo en cualquier momento de la obra dispararía el menú. |
| `bDone` | false | Ya se apretó; no vuelve a disparar. |
| `BaseScale` | — | 🔴 **Vector, capturado en BeginPlay.** Ver la trampa de abajo. |
| `HandL` / `HandR` | — | Los motion controllers (pose **Grip**), del pawn. |
| `bTrigHeld` · `HoverT` · `HoldT` | — | Estado. |
| **`OnPressed`** | dispatcher | Lo que consume la intro. |

## Estructura de grafos
- **`BeginPlay`** — captura `BaseScale` · `CacheHands` · `ApplyLabel`.
- **`Tick`** — **sólo si `bArmed`** → `TickStep(Δ)`.
- **`TickStep`** — `RefreshHover` · `UpdateVisual` · y sólo si hay hover, `UpdateHold`.
- **`RefreshHover`** — pone `bHovered = false` y llama `CheckHand` **una vez por mano**. Setear-false-y-desmentir es más corto que contar.
- **`CheckHand(H)`** — **distancia al cuadrado contra radio al cuadrado** (receta de [[BP_Sensor]]: evita la raíz y esquiva `Math|Vector|Distance`).
- **`UpdateHold`** — si el gatillo está sostenido acumula, si no resetea a 0. **Soltar cancela siempre.**
- **`TickHold`** — al pasar `HoldTime` llama `Fire()`. Con `HoldTime = 0` eso es el primer frame con gatillo + mano cerca.
- **`Fire`** — `bDone = true`, se desarma, loguea y **hace el broadcast al final**, con el estado ya consistente.
- **`UpdateVisual`** — move-toward de `HoverT` y `escala = BaseScale × (1 + HoverT×(HoverScale−1))`.
- **`Arm` / `Disarm`** — la API que usa la intro.

### 🔴🔴 FIX (2026-08-12 visor): el gatillo NO llegaba — faltaba LA RECETA DE INPUT completa
Reportado por Beltrán: *"aparecen los botones pero solo funciona el hover, no el trigger"*. Causa: este BP tenía los **eventos** `IA_Shoot_*` pero **nadie hacía `EnableInput` + `AddMappingContext` EN ESTE actor** — el punto 1 y 2 de la receta de `assets-existentes.md` §INPUT. Sin eso, los eventos existen y jamás disparan, sin error ni warning.
**Aplicado (copiado EXACTO de `BP_Instructions.InitRefs` de Breath, el que anda en visor):**
- `IMCRef` (var objeto, default **`Core/UI/Input/IMC_MenuTrigger`** — duplicado de `IMC_Continue` con sus 4 mapeos de trigger).
- `EnsureInput()`: `GetPlayerController(0)` → `EnableInput(self, pc)` → `AddMappingContext(subsys, IMCRef, 1000, bIgnoreAllPressedKeysUntilRelease=False, bForceImmediately=True)` → `bInputReady = HasMappingContext(...)` → log `BTN: input listo - IMC activo`.
- `MaybeInput()` llamada **desde el Tick** (antes del gate de `bArmed`), reintenta hasta que `bInputReady`. En BeginPlay el PC puede no existir y falla en silencio.
**Verificado en PIE:** los 2 botones spawneados loguean `BTN: input listo - IMC activo`. La confirmación del gatillo real es del visor.

### El input, por cirugía
El DSL **no puede crear eventos de input**. Van con `create_node` + `connect_pins`:
- type_id **`Input|EnhancedActionEvents|IA_Shoot_{Right,Left}`** (⚠ **no** `AddEvent|Input|EnhancedInputAction|…`, que no existe).
- 🆕 **2026-08-12 (fix visor): `Started` = pin 1 → `bTrigHeld = true`** · **`Completed` = pin 4 → false**. ANTES era `Triggered` (pin 0) → `true`, y eso causaba el bug de *"si mantengo apretado cambia constantemente"*: `Triggered` dispara **cada frame** mientras se sostiene, así que un botón recién spawneado (el BACK tras apretar ABOUT, el menú tras el BACK) veía el gatillo ya apretado y se re-disparaba en cadena. Con `Started`, el apretón cuenta **una vez**: un botón nuevo no dispara hasta soltar y volver a apretar. (Mismo patrón Started/Completed que el far-grab de Touch.)
- `IA_Shoot_L/R` del XRFramework es **la única acción de trigger que se entrega de verdad** en este proyecto, y **un actor suelto del nivel la recibe** (validado en visor con el pincel de Movement).
- ⚠ El `read_graph_dsl` muestra estos eventos **vacíos** aunque estén bien cableados. Verificado con `get_node_infos`: los 4 cables están.

## ⚠ Trampas heredadas (ya pagadas en otros BP)
- 🔴🔴 **`SetRelativeScale3D` con un escalar uniforme PISA la escala autoral.** En `BP_SaveButton` apareció un cilindro de 1 m tapando la vista. La escala **parte de `BaseScale`** (Vector, capturado en BeginPlay), nunca de 1.
- 🔴 **`bArmed` genera `GetArmed`/`SetArmed`, sin la `b`.** Ídem `bHovered`, `bTrigHeld`, `bDone`.
- ⚠ Llamar una función propia con parámetros desde el DSL: el primer pin posicional es **`self`** → usar keyword (`:H`, `:Delta`).

## ✅ RESUELTO: spawn por TargetPoint y kill al terminar (2026-08-12)
Los botones **ya no se colocan a mano en el nivel**. El flujo es:

```
TitleStep → ShowMenu → SpawnMenu
     GetAllActorsOfClassWithTag(TargetPoint, "MenuSpawn")
     → uno por punto: SpawnActor → SetButtonLabel(MenuLabels[i]) → Arm() → StoreButton(i)
START apretado → KillMenu → DestroyActor de los dos → HideTitleAndGo
```

**Qué se ganó:**
- **No existen antes de su momento** (antes se veían abajo, lejos, esperando).
- **No sobreviven a su momento**: se destruyen, no se esconden. Cero residuos.
- 🔴 **El "uno más arriba que otro" se volvió imposible**: los dos salen de `TargetPoint` autorados. Si están parejos en el viewport, están parejos en la obra.
- Desaparecieron **cuatro funciones**: `CacheButtons`, `SortButton`, `PlaceButtons` y `PlaceOne`. El punto de spawn reemplazó toda la ubicación por código.

**Cómo se autora (versión FINAL, pedida por Beltrán 2026-08-12 tarde): un TargetPoint POR botón, con tag propio.**
| TargetPoint | Tag | Spawnea | Posición inicial |
|---|---|---|---|
| `TP_MenuStart` | `MenuSpawnStart` | START (`MenuLabels[0]`) | (−455, −17, 102), yaw 180 |
| `TP_MenuAbout` | `MenuSpawnAbout` | ABOUT US (`MenuLabels[1]`) | (−455, +17, 102), yaw 180 |
| `TP_MenuBack` | `MenuSpawnBack` | BACK (`MenuLabels[2]`, en el panel About) | (−455, 0, 102), yaw 180 |
| `TP_Bell` | `BellSpawn` | el timbre del Center | (405, 25, 100), yaw 180 |
- El botón toma **posición Y rotación** del punto (con yaw 180 el texto mira al usuario). Se mueve cada punto en el viewport, sin tocar código.
- `BP_IntroSequence.SpawnBtnFromTag(PointTag, LabelIdx)` es el helper (con guard: si falta el punto, loguea `FALTA` y no spawnea). El timbre va por `BP_StageDirector.SpawnBell → SpawnBellAt(Pt)`.
- ⚠ **`TP_Bell` está en coordenadas de mundo**: si se cambia `CorridorLength` (hoy 800 de test → ~7000 con la voz real), la puerta del Center se corre y **hay que mover `TP_Bell` a mano** junto a ella (X de la puerta = `CorridorLength − 500 + DoorAhead`).
- Los offsets `ButtonDistance`/`ButtonSpread`/`ButtonDrop` quedaron **sin uso** para los botones (los puntos mandan); `PanelDistance` sigue viva para el panel del título vía `MenuRoot`.

⚠ **El label va por un setter con nombre ÚNICO (`SetButtonLabel`), no por `SetLabelText`.** `Class|BPMenuButton|SetLabelText` **colisiona con un nodo de Niagara** (`Niagara|Preview|SetLabelText`) y el DSL agarra el equivocado, invirtiendo los argumentos. Se detecta releyendo el grafo.

### ✅ RESUELTO (2026-08-12 tarde): un solo `MenuRoot`, todo relativo a él
El bug de los 5,45 m se cerró con la decisión de la revisión (plan §0 #1):
- **Un único `TargetPoint` con tag `MenuRoot`** (`TP_MenuRoot`, en (−500, 0, 130) junto al `PlayerStart`, yaw 0). Los dos `MenuSpawn` viejos **se eliminaron** del nivel.
- `BP_IntroSequence` ahora coloca **panel Y botones relativos a ese punto**: `PlaceAtRoot` (el actor a `PanelDistance` sobre el forward del root) y `SpawnMenuAtRoot`→`SpawnBtnAt(BtnPos, BtnRot, LabelIdx)` (botones a `ButtonDistance`/±`ButtonSpread`/−`ButtonDrop`). `PlacePanel`/`PlaceStep`/`SpawnMenu`/`SpawnMenuOne` y `MenuIndex` **fueron eliminados**.
- El recentrado que lo hace válido **ya existía** en `BP_VRPawn_SC` (Delay 0.5 → `ResetOrientationAndPosition`), verificado con `get_node_infos`.
- **Se autora moviendo UN punto.** Verificado por 3 aserciones espaciales nuevas en `BP_SelfTest.MenuSpatialAsserts`: ambos botones a <120 cm del root y separación 20-60 cm — **PASS en PIE**.
- 💡 El modo auto del andamiaje (`MaybeStart`) ahora dispara **`OnStartPressed`** (no `HideTitleAndGo` directo), así el camino auto ejercita el mismo kill que un START real. `INTRO: menu destruido, cero residuos` **verificado por log**.

### 🐛 CERRADO (histórico): los botones aparecen a 5,45 m — dos sistemas de referencia mezclados
Reportado en visor y **diagnosticado por Beltrán**: *"no sé si porque el player start es distinto al inicio del spline"*. Los números lo confirman:

| Cosa | Posición |
|---|---|
| **`PlayerStart_0`** | **(−500, 0, 0)** ← el pawn arranca acá |
| `BP_Walker_C_0` + `PathHalfLength` 500 | el spline va de **−500 a +500**, así que el `PlayerStart` **es el inicio del spline** |
| Los `TargetPoint` de `MenuSpawn` | **(45, ±17, 112)** ← los puse en coordenadas de mundo, como si el usuario estuviera en el origen |

🔴 **El problema de fondo no es el número: es que el menú usa DOS sistemas de referencia.** El panel del título se coloca **relativo a la cámara** en runtime (`PlaceStep`), y los botones en **puntos de mundo**. Mientras no coincidan, el menú va a estar siempre partido.
👉 **La propuesta (§0 de [`docs/PLAN-2026-08-13.md`](../../../../docs/PLAN-2026-08-13.md)):** un solo `TargetPoint` con tag **`MenuRoot`** junto al `PlayerStart`, y panel + botones **relativos a él** con los offsets que ya son variables. Se autora moviendo un punto. Requiere decidir si se **recentra la vista** en `BeginPlay`.
💡 **Atajo para probar ya:** mover los dos puntos a `x ≈ −455`.

### Verificado por log (2026-08-12)
```
INTRO: menu spawneado en sus TargetPoints
BOTON armado: START
BOTON armado: ABOUT US
TEST PASS: menu: la lista de etiquetas no quedo vacia en la instancia
TEST PASS: menu: hay exactamente 2 botones spawneados
```
🔴 **Y séptima vez del mismo patrón:** `MenuLabels` nació **vacío** en la instancia aunque el CDO tuviera `["START","ABOUT US"]` → los dos botones spawnearon **sin texto**. Por eso ahora hay una aserción que verifica el largo del array **en la instancia**, no en la clase.

## 🔴🔴 REGLA DE ARQUITECTURA (Beltrán, 2026-08-12): spawnear, matar, y ubicar con TargetPoints
*"Ojalá tooodo hagamos que se spawnee y después que se elimine. Siempre usando target points para que sean fáciles de ubicar. Por lo menos todo lo que se pueda y valga la pena. VR se trata de optimizar."*

**Aplica a TODO el proyecto, no sólo a los botones.** Tres partes:
1. **Nada existe antes de su momento.** Si el usuario todavía no lo tiene que ver, **no está spawneado**.
2. **Nada sobrevive a su momento.** Lo que ya no se va a usar se **destruye**, no se esconde. Cero residuos.
3. **La posición se autora con `TargetPoint` + tag**, nunca con coordenadas en Blueprint. Así se mueve en el viewport sin tocar código, y quedan simétricos por construcción.

💡 **El patrón ya está probado dos veces en el proyecto**: `BP_AttractDirector` con el tag `BubbleSpawn`, y [[BP_SoulChoice]] con `SoulSpawn`. Su tracker lo dice: *"para cambiar cuántas/dónde flotan se agregan o mueven TargetPoints, no se toca ningún Blueprint"*.

### Estado: a medio camino (2026-08-12)
Lo reportado en visor fue: *"los botones existen antes de aparecer al frente, los veo abajo lejos"* y *"hay uno más arriba y otro más abajo"*.

**Paliativo aplicado** (para que se pueda seguir probando): el botón **nace oculto** (`SetActorHiddenInGame(true)` al final de su `BeginPlay`), `Arm()` lo muestra y `Fire()` lo vuelve a ocultar. Eso mata el síntoma de verlos antes, pero **sigue siendo esconder, no spawnear**.
⚠ **Trampa mordida al hacerlo:** insertar el nodo "al principio del grafo" buscando el nodo de entrada **agarró el `Tick` en vez del `BeginPlay`** (un EventGraph tiene varios eventos), y quedó un `SetActorHiddenInGame(true)` **por frame** — o sea el botón invisible para siempre. **Al insertar en un EventGraph hay que elegir el evento por su `type_id`, no "el primero que aparezca", y releer el grafo después.**

### 🔴 El refactor que corresponde, y es el próximo paso
1. **Sacar las dos instancias pre-colocadas** de `L_Persistent`.
2. **Dos `TargetPoint` con tag `MenuSpawn`**, colocados a mano donde queden cómodos sentado (~45 cm al frente, simétricos, a la altura del pecho). **Ahí se resuelve el "uno más arriba que otro"**: si los dos salen del mismo par de puntos autorados, no hay asimetría posible.
3. La intro, al mostrar el título: `GetAllActorsOfClassWithTag(TargetPoint, "MenuSpawn")` → **spawnea** un `BP_MenuButton` por punto → asigna el `LabelText` **por índice** (0 = START, 1 = ABOUT US) → `Arm()`.
4. Al apretar cualquiera: **`DestroyActor` de los dos**.
5. Se pueden borrar entonces `CacheButtons`, `SortButton`, `PlaceButtons` y `PlaceOne` — el spawn en el punto reemplaza toda la ubicación por código.
6. Aserciones en [[BP_SelfTest]]: **0 botones antes del título** y **2 después**, con textos distintos. Eso verifica el spawn Y el kill sin visor.
