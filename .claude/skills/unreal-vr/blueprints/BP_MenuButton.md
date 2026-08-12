# BP_MenuButton — botón por CONTACTO + trigger (Core/UI/)

## Purpose
Los botones del menú de la intro (**START** / **ABOUT US**) y, más adelante, el **timbre** del Center. Se acercan con la mano y se confirman con el gatillo.

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

### El input, por cirugía
El DSL **no puede crear eventos de input**. Van con `create_node` + `connect_pins`:
- type_id **`Input|EnhancedActionEvents|IA_Shoot_{Right,Left}`** (⚠ **no** `AddEvent|Input|EnhancedInputAction|…`, que no existe).
- **`Triggered` = pin 0 → `bTrigHeld = true`** · **`Completed` = pin 4 → false**.
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

**Cómo se autora:** mover los dos `TargetPoint` con tag **`MenuSpawn`** en el viewport. Hoy están en `(45, ±17, 112)`. Para agregar un tercer botón: un punto más y una entrada más en `MenuLabels`. **Sin tocar Blueprints.**

⚠ **El label va por un setter con nombre ÚNICO (`SetButtonLabel`), no por `SetLabelText`.** `Class|BPMenuButton|SetLabelText` **colisiona con un nodo de Niagara** (`Niagara|Preview|SetLabelText`) y el DSL agarra el equivocado, invirtiendo los argumentos. Se detecta releyendo el grafo.

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
