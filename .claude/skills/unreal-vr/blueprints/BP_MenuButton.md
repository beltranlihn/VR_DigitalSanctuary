# BP_MenuButton — botón por CONTACTO + trigger (Core/UI/)

## Purpose
Los botones del menú de la intro (**START** / **ABOUT US**) y, más adelante, el **timbre** del Center. Se acercan con la mano y se confirman con el gatillo.

## Status
🟡 **Construido y compilando** (2026-08-12), con la cadena de input verificada nodo por nodo. ⬜ **Falta colocarlo, armarlo desde la intro y suscribirse a `OnPressed`** (ver TODO).

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
| `Plate` | Cubo escalado a **3 × 28 × 10 cm**, material `M_IntroLogo` (unlit emisivo). Es lo que crece con el hover. |
| `Label` | `TextRenderComponent`, `yaw 180`, worldSize 6. 🔴 Con **`M_TextUnlit`** desde el día uno: el material de fábrica es *lit* y en esta obra **no hay luces**, así que se vería negro (ver `materials-vr.md`). |

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

## 🔴🔴 BLOQUEADO: colocar actores por MCP no está quedando en el nivel
**Estado al cierre del 2026-08-12.** Toda la lógica está construida, compilada y guardada — **lo que falla es que los actores no quedan en el nivel.** Síntomas, en orden de descubrimiento:

1. `BP_IntroSequence_C_0` desapareció del nivel después del crash del Material Editor. Se repuso como `_C_1`, **corrió bien** (log completo a las 11:59 y 12:02) y **volvió a desaparecer** sin ningún crash en el medio.
2. 🔴 **`SceneTools.find_actors` MIENTE**: no lista actores que sí existen. `find_actors(name:'IntroSequence')` devolvió vacío mientras `get_properties` sobre `…PersistentLevel.BP_IntroSequence_C_1` **leía sus propiedades sin problema**. No usarlo como prueba de existencia.
3. Pero la prueba que vale es **desde el juego**: `BP_SelfTest` hace `GetActorOfClass(BP_IntroSequence_C)` y da **`TEST SKIP: no hay BP_IntroSequence en el nivel`**. O sea que en el mundo de PIE el actor **no está**, aunque su ruta resuelva en el editor.
4. `save_assets(['/Game/SoulCharger/Maps/L_Persistent'])` **sí escribe el `.umap`** (verificado por `git status` y por la fecha del archivo), así que el guardado del mapa no es el problema evidente.

**👉 Lo más rápido para desbloquear: colocar los tres actores A MANO** desde el Content Browser (arrastrar al viewport) y setear los valores de abajo. Son dos minutos y esquiva lo que sea que esté pasando con la colocación por MCP.

| Actor | Posición | Valores a setear **en la instancia** |
|---|---|---|
| `BP_IntroSequence` | origen | `bAutoStartAfterTitle` **false** · `ClearFadeTime` 0.6 · `TitleFadeOut` 1.0 · `BlackTime` 2 · `LogoTime` 1 · `FadeRate` 3 · `PanelDistance` 200 · `ButtonDistance` 45 · `ButtonSpread` 17 · `ButtonDrop` 28 |
| `BP_MenuButton` #1 | cualquiera (la intro lo reubica) | `LabelText` **START** · `HoverRadius` 18 · `HoldTime` 0 · `HoverScale` 1.18 |
| `BP_MenuButton` #2 | cualquiera | `LabelText` **ABOUT US** · ídem |

🔴🔴 **Y el patrón de siempre, que ya va SEIS veces: toda variable instance-editable nueva nace en 0 / false en la instancia.** `ButtonDistance` apareció en **0** recién colocado. **Setear todos los valores de la tabla a mano y verificarlos**, no confiar en el default de la clase. El arnés ya tiene aserciones para los tiempos de la intro; faltan para las de los botones.

## TODO
- [x] ~~Colocar las dos instancias~~ → **bloqueado, ver arriba: hacerlo a mano.**
- [ ] 🔴 **Ubicarlas al alcance del brazo.** Van **a ~45 cm**, no en el panel del título (que está a 200 cm): sentado, el brazo llega a 50-60 cm. Lo más limpio es que la intro las reposicione en runtime con la misma receta de `PlaceStep` (cámara + forward por yaw), a ±15 cm del centro.
- [ ] 🔴 **Que la intro las arme al mostrar el título** (`Arm()`) y se suscriba a `OnPressed`: START → `HideTitleAndGo()` (que ya existe y hace el fundido); ABOUT US → el panel de texto.
- [ ] **Desarmar el que no se apretó** cuando se elige uno.
- [ ] Aserciones en [[BP_SelfTest]]: que haya exactamente 2, con textos distintos, y que **nazcan desarmados**.
- [ ] Material propio con acento de color (hoy usa `M_IntroLogo`, que es el del logo).
- [ ] Test en visor: si 18 cm es cómodo o si conviene más grande, y si el crecimiento se lee.

## Relacionados
- [[BP_IntroSequence]] (quien los arma y los consume) · [[BP_Sensor]] (la receta de proximidad por mano) · `BP_SaveButton` (hover + hold + la trampa de la escala) · `references/assets-existentes.md` (por qué `IA_Shoot_*`)

---

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
