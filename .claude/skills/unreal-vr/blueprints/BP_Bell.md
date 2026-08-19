# BP_Bell — el timbre que abre la puerta (Core/Doors/)

## Purpose
El **botón de llamada** de la obra: un cilindro de 35 cm que se apoya con la mano y, **sosteniendo 3 segundos**, abre la puerta. Un anillo de carga sube de 0 a 100 mientras se sostiene; si se retira la mano antes, vuelve a 0 y hay que empezar de nuevo.

Pedido de Beltrán (2026-08-18). 💡 Ya estaba anticipado en el diseño: `BP_Sensor.md` decía *"el timbre del Center tiene que PARECERSE a esto (§3): apoyar la mano para que te escanee es la misma gramática que tomar el sensor"*.

## Status
🟡 **Compila limpio y arranca sin errores** (cero `Accessed None`, cero warnings de compilación). **Se coloca a mano en el sublevel** — ver abajo por qué se descartó el spawn.
🟢 **La detección de la mano ya tiene causa y arreglo** — era el nodo podado, ver abajo. **Falta confirmarlo en visor.**
🟢 **La háptica ya NO pasa por `BP_HapticHub`** — decisión de Beltrán, ver abajo.

## 🔴🔴 El bug del hover: un nodo PODADO, no un problema de distancias
Durante horas `bTouching` no se prendía nunca, con el grafo auditado nodo por nodo y bien cableado. Lo cazó **Beltrán leyendo el warning del compilador**:

> *AnyHandClose was pruned because its Exec pin is not connected, the connected value is not available and will instead be read as default*

`HandNear` llamaba a `AnyHandClose` **como expresión adentro de un `(return …)`**. Una función propia usada como expresión **no cablea su pin `execute`** → el compilador la **poda** y devuelve el default (`false`) para siempre. **Es un warning, no un error: compila "bien" y miente.**

**El arreglo:** la llamada pasa a ser una **sentencia con exec cableado** que alimenta un `Set bHandsNear`, y `RunBell` lee la variable. Regla general en `references/gotchas.md`.

## El anillo es un `RadialSlider` (widget) — 2026-08-18
Primero se probó con el material `M_SoulRing` sobre un `Plane`. Beltrán lo rechazó: *"no me gusta que sea un material, prefiero que sea un widget con ring slider. Es mas clean."* Y después, viendo el widget: *"veo que en el widget no hay ningun radial slider. Ese es el compotente que hay que usar para el anillo."*

Hoy `WBP_BellRing` es **un solo `RadialSlider`** (`/Script/AdvancedWidgets.RadialSlider`, categoría Common de la paleta) dentro del `Root`:
- `SliderHandleStartAngle` 0 / `SliderHandleEndAngle` **360** → anillo completo, no medidor.
- `ShowSliderHandle` y `ShowSliderHand` en **false**, `Locked` en true, `Visibility` **HitTestInvisible** → es puro dibujo, no se puede arrastrar ni roba input.
- `WidgetStyle.BarThickness` 22 px, slot anclado full con 20 px de margen sobre un `DrawSize` de 400×400.
- `SliderProgressColor` blanco y `SliderBarColor` gris oscuro.

🔴 **Los colores del `RadialSlider` son READ-ONLY desde Blueprint** (`SetSliderProgressColor` no existe; sólo el getter). Por eso **el color y el brillo se aplican tintando el `WidgetComponent`**, no el widget: `PushRingLook` hace `SetTintColorAndOpacity(RingW, RingColor × MakeLinearColor(RingBrightness,·,·,1))`. El alfa se deja en 1 a propósito — multiplicarlo por el brillo apagaría el anillo en vez de encenderlo.

Lo único que quedó en el grafo del widget es **`SetProgressW(P)` → `Ring.Value = Clamp(P,0,1)`**. Se borraron `BuildRing` (los 36 `Border` sobre un círculo) y sus variables (`Segments`, `RingRadius`, `SegW`, `SegH`, `OnColor`, `OffColor`, `Bars`).

## Componentes
| Componente | Qué es |
|---|---|
| `Body` | Cilindro del motor a escala (0.35, 0.35, 0.08) = **35 cm de diámetro × 8 de alto**. Es el que **se hunde** al apoyar la mano. `NoCollision` explícito, sin sombras. Material **`MI_Bell`**, instancia de **`M_RoomInterior`** — el mismo maestro que los muros y pisos, así que **obedece a `MPC_Room.RoomLight`** y se apaga con la sala en cada transición. |
| `RingW` | `WidgetComponent` con `WBP_BellRing`, **World space**, `Transparent`, tick `Automatic`, pitch −90, `z = 4,5` (justo sobre la tapa), `NoCollision`. **`DrawSize` 800×800 con escala 0,05 → 40 cm de quad a 20 px/cm.** 🔴 **Cuelga del root, NO del `Body`** — por eso el botón baja y **el anillo se queda en su posición**, que es exactamente lo pedido. |

## 🔴🔴 El anillo invisible en el nivel: `WidgetClass = None` en la INSTANCIA
Síntoma (2026-08-18): **en el viewport del Blueprint el anillo se veía perfecto; en el nivel y en PIE no existía.** Causa: el `RingW` del actor colocado tenía **`widgetClass` vacío**, porque el actor se colocó antes de que el componente estuviera configurado y el *component instance data* le gana al Blueprint (§117). Un `WidgetComponent` sin clase **no dibuja nada y no avisa**.

Lo mismo se había comido `DrawSize` (500×500 en vez de 800) y la escala (1,0 → quad de 5 m). 👉 **Al tocar un componente en el CDO, diffear siempre la instancia contra él** — `gotchas.md` §129.
Extra por las dudas: `bIsTwoSided` pasó a **true** en CDO e instancia, para que el anillo no desaparezca segun de qué lado se lo mire.

## 🔍 Nitidez del anillo: `DrawSize` ÷ escala del componente
**La resolución del anillo NO se configura en el widget** — se configura en el `WidgetComponent` que lo hospeda, con **dos perillas que se mueven al revés una de otra**:
- **`Draw Size`** (píxeles) = la resolución del render target donde Slate dibuja.
- **`Scale`** del componente = cuánto mide eso en el mundo. Verificado en `WidgetComponent.cpp` `CalcBounds()`: **1 px de DrawSize = 1 unidad (cm) con escala 1** — ver [widgets-vr.md](../references/widgets-vr.md) §c.

👉 **Tamaño físico = DrawSize × Scale. Densidad = DrawSize ÷ tamaño físico.** Para ganar nitidez **sin cambiar el tamaño**: subir `DrawSize` y bajar `Scale` en la misma proporción.

| | DrawSize | Scale | Tamaño | Densidad | Render target |
|---|---|---|---|---|---|
| Antes | 400×400 | 0,1 | 40 cm | 10 px/cm | 640 KB |
| **Hoy** | **800×800** | **0,05** | **40 cm** | **20 px/cm** | 2,5 MB |
| Si hace falta más | 1024×1024 | 0,039 | 40 cm | 25,6 px/cm | 4 MB |

🔴 **Y el cambio que más se nota no son los píxeles: es `BlendMode`.** Estaba en **`Masked`** (alfa de 1 bit) — con eso el borde curvo del anillo sale escalonado por más píxeles que le tires. Pasado a **`Transparent`**, que sí antialiasea la curva. Cuesta translucidez (overdraw), pero es un quad chico.

## Registro de variables
### A - Timbre (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `BellTag` | `bell` | 🔴 **Abre todas las `BP_Door_SC` que lleven este ACTOR TAG.** El vínculo timbre↔puerta es por tag, así un timbre puede abrir varias puertas. |
| `HoldDuration` | 3 s | Cuánto hay que sostener. |
| `TouchRadius` | 25 cm | A qué distancia de la mano se considera apoyado. Se mide **al actor**, igual que `BP_MenuButton.CheckHand`, que es el que ya andaba. |

### C - Aparicion (instance-editable)
🔴 **El timbre nace en escala 0 y crece al acercarse el pawn**, con un sonido de burbuja. Pedido de Beltrán: *"así aparece cuando estamos llegando"* — no está ahí desde siempre, te recibe.

| Variable | Default | Rol |
|---|---|---|
| `AppearDistance` | 700 cm | A qué distancia **del pawn** (no de la mano) empieza a crecer. |
| `AppearTime` | **1,0 s** | Cuánto tarda en ir de escala 0 a su escala completa. **Son segundos de verdad.** |
| `LeaveTime` | **0,5 s** | Cuánto tarda en encogerse a 0 al dispararse. Separada de la anterior a pedido de Beltrán: *"ahora se demoró muchísimo en achicarse"*. |
| `AppearVolume` | 1.0 | Volumen del sonido de aparición. |

🔴 **Por qué murió `AppearSpeed` y por qué el nodo cambió.** Estaba con **`FInterpTo`**, que es **asintótico**: su pin se llama *speed*, no dura nada concreto y **nunca llega al destino** — pedirle "1 segundo" no tiene traducción. Ahora usa **`FInterpTo Constant`**, que avanza a **ritmo constante y SÍ llega exacto**, con el ritmo calculado como **`1 / Max(Tiempo, 0.05)`**. Con eso `AppearTime = 1.0` son exactamente 1,000 s de 0 a 1, y `LeaveTime = 0.5` medio segundo.
⚠ El `Max(·, 0.05)` no es decorativo: **protege de la división por cero**, que es exactamente lo que pasa cuando una instancia colocada nace con la variable en 0 (ver abajo).
⚠ Se pierde el ease-out que daba `FInterpTo`: el crecimiento ahora es **lineal**. Si se quiere la curva de vuelta, es **un nodo** (`Ease` con `EaseOut`) entre `AppearT` y la multiplicación de escala.
🔴 **La instancia colocada tenía las dos en 0** (instance-editable nace en cero, gotcha §119): sin sembrarlas, `Max` las lleva a 0,05 s y el timbre **aparece de golpe**. Sembradas y verificadas en `Bell_Hall`.

🔴 **Se escala el ACTOR, no los componentes.** `BaseActorScale` guarda la escala autoral en el `Boot` y después se multiplica por `AppearT`. Es lo que esquiva la trampa de [[BP_SaveButton]]: el `Body` tiene escala **no uniforme** (0.35, 0.35, 0.08) y escribirle un escalar la habría pisado.

⚠ **No se puede apretar mientras aparece**: `bTouching` exige `AppearT > 0.9`.

### B - Feedback (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `PressDepth` | 3 cm | Cuánto se hunde el cuerpo. |
| `PressSpeed` | 12 | Velocidad del hundido (`FInterpTo`). |
| `BodyColor` | cálido | 🎨 **Color del cuerpo** (param `BaseColor` de `M_RoomInterior`). |
| `BodyEmissive` | 0.25 | 🎨 **Emisividad del cuerpo**. Se aplica en `Boot` vía `ApplyBodyLook`, sin variable MID. |
| `RingColor` | cálido | Color del anillo — **tinte del `WidgetComponent`**. |
| `RingBrightness` | 1.5 | Multiplicador de ese tinte. Con el anillo como widget (unlit) 1,0 ya se ve encendido; subilo para que queme más. |

### D - Audio (instance-editable)
`AppearSound` (`SBubbleHoverOn`) · `ChargeSound` (`Charge1`, loop mientras se sostiene) · `DisappearSound` (`SBubbleHoverOut`).

## 🟢 Háptica: `PlayHapticEffect` directo, NO el hub (2026-08-18)
Beltrán: *"¿es necesario el haptic hub? ¿no basta con definir un play haptic effect mucho mas simple? y crear un haptic que podamos reusar. Es la forma correcta según yo."* — y tenía razón, con una ventaja concreta: **el hub es un ACTOR que hay que colocar en el nivel y cachear**, y por eso no vibraba (vive sólo en el `L_Persistent` viejo). `PlayHapticEffect` va al PlayerController: no depende de nada colocado.

```
(fn PulseHover ()
  GetPlayerController(0) + HapticEffect
  if bTouchRight → PlayHapticEffect(… Hand=Right)
             else → PlayHapticEffect(… Hand=Left))
```
- Variable **`HapticEffect`** (instance-editable, `B - Feedback`), default **`/Game/XRFramework/Haptics/GrabHapticEffect`** — el del VRTemplate, que ya está probado. Se cambia desde el panel sin tocar el grafo.
- La mano sale de **`bTouchRight`**, que `AnyHandClose` ya calculaba (marca la más cercana de las dos). ⚠ El pin `Hand` es un **enum literal**: no entra por cable, por eso son dos nodos con un `Branch` y no uno solo.
- Se borraron `CacheHub`, la variable `HubRef` y el `PrintString` del hub.

⚠ Al borrar el nodo `CacheHub` **se cortó la cadena de exec de `CacheRefs`** y el cacheo de `MoveRef` quedó huérfano — `delete_node` no cose la cadena. Reconectado y verificado.

### Z - Estado interno
`HoldT` · `bTouching` · `bHandsNear` · `bWasTouching` · `bTouchRight` · `bDone` · `bLeaving` · `BaseBodyZ` · `PawnSC` · `AppearT` · `BaseActorScale` · `bAppearPlayed` · **`bBooted`** · `ChargeComp` · `MoveRef`.

🔴 **`bBooted` es el guard que faltaba**: el `Tick` corre desde el frame 0 pero `Boot` llega por timer a los 0,3 s, así que todo lo que dependiera de `PawnSC` reventaba con `Accessed None` ese ratito. Ahora `TickBell` no hace nada hasta que `Boot` terminó.

## Estructura de grafos
- **`BeginPlay`** → **captura `BaseActorScale` y pone el actor en escala 0 AHÍ MISMO** → timer 0,3 s → **`Boot`**: captura `BaseBodyZ`, pinta cuerpo y anillo, deja el anillo en 0 y cachea las referencias.
  🔴 **Lo de esconderlo tiene que pasar en `BeginPlay`, no en `Boot`.** Estaba dentro de `Boot` y por eso el timbre y su anillo **parpadeaban a tamaño real durante los 0,3 s del timer**, antes de encogerse a cero y volver a crecer con la animación de entrada (reportado por Beltrán). El timer existe porque `CachePawn` necesita que el pawn ya esté; **esconderse no necesita esperar a nadie**.
  ⚠ **Por qué NO va en el Construction Script**, que sería aún más temprano: el CS **re-corre en cada cambio de propiedad**, así que la segunda pasada capturaría la escala **ya puesta en 0** y el timbre no volvería a crecer nunca. `BeginPlay` corre una sola vez y con la escala autoral intacta.
- `Tick` → **`TickBell(DT)`** → si `bBooted` y no `bDone` → **`RunBell(DT)`**: `TickAppear` → `HandNear` → `bTouching` → `HoverEdge` → `UpdateHold` → `UpdatePress`.
- **`TickAppear(DT)`** — 🔴 **desde 2026-08-18 es sólo un guard**: `IsValid(PawnSC)` → si vale llama `AppearStep(DT)`, si no **vuelve a llamar `CachePawn`**. Ver abajo.
- **`AppearStep(DT)` / `PlayAppear()`** — la aparición: mide la distancia al pawn, lleva `AppearT` hacia 1 o 0 **a ritmo constante (`1/AppearTime`)** y escala el actor; la primera vez que entra en rango suena `AppearSound`.

## 🔴 El `PawnSC` nulo (arreglado 2026-08-18)
`Boot` cachea el pawn **una sola vez**, a los 0,3 s, y `CachePawn` castea `GetPlayerPawn(0)` a `BP_VRPawn_SC`. Si en ese instante el pawn no existe, **la variable queda nula para siempre** y el timbre nunca aparece — con un *"Accessed None trying to read property PawnSC"* por frame.

Salió en **Simulate** (donde directamente no hay pawn VR poseído) probando `BP_InstrButton_SC`, pero **el riesgo real es en Play**: cualquier demora de streaming o cambio en el orden de carga lo reproduce. Por eso se aplicó también acá, no sólo en el botón.

✅ **Ahora se auto-repara**: el Tick reintenta el cacheo hasta que el pawn existe. El cuerpo viejo se extrajo a `AppearStep(DT)` porque **`IsValid` corta la lista de statements del DSL** y no puede ir en el medio.
⚠ **Y ojo con la forma**: `(if (Utilities|IsValid x) A (else B))` **compila y borra las dos ramas** — hay que escribir `(Utilities|IsValid x (:"Is Valid" A) (:"Is Not Valid" B))`. Ver `gotchas.md` §150-151.
- **`HandNear()` / `AnyHandClose(Pawn)`** — 🔴 **por DISTANCIA AL CUADRADO contra radio al cuadrado**, contra las dos manos, usando los accesores que **ya existen** en el pawn (`GetMotionController{Left,Right}Grip`): no se toca `Core/Pawn/`. `HandNear` **escribe `bHandsNear`**; no devuelve — ver el bug del nodo podado arriba.
- **`UpdateHold(DT)`** — acumula si toca, **cae a 0 de golpe si se suelta**, y a 1,0 llama `Fire`.
- **`UpdatePress(DT)`** — interpola la Z del `Body` entre `BaseBodyZ` y `BaseBodyZ − PressDepth`.
- **`HoverEdge()`** — el **flanco** del apoyo: al entrar dispara `StartCharge` (sonido de carga + `PulseHover` en la mano que tocó); al salir, `StopCharge`.
- **`ApplyRing(P)`** — castea el user widget del `RingW` y le pasa `SetProgressW(P)`.
- **`PushRingLook()`** — tinta el `RingW` con `RingColor × RingBrightness` (alfa 1).
- **`Fire()`** — a los 3 s: **sólo feedback.** Anillo a 1, corta la carga, **háptica** (`PulseHover`), suena `DisappearSound`, y prende `bLeaving` para que empiece a encogerse. 🔴 **No abre puertas ni avanza** — ver abajo.
- **`TickLeave(DT)`** — la salida: encoge a ritmo **`1/LeaveTime`** y, **recién cuando `AppearT < 0.02`**, clava la escala en **(0,0,0) exacto** → **`OpenDoors`** → **`Advance`** (`GotoNext` de [[BP_Director_Movement]]) → **`DestroyActor`**.

### 🔴 El orden lo pidió Beltrán así (2026-08-18) — y no es un detalle
> *"Al terminar los tres segundos: háptica, sonido de salida, animación. Recién cuando la escala llega a 0,0,0 debe triggear la apertura de puertas y luego la caminata. Recién ahí hace auto destroy."*

Antes `Fire` mandaba las acciones **de una** y la animación de salida corría encima: la puerta se abría y el pawn empezaba a caminar **mientras el timbre seguía ahí encogiéndose**. Ahora el gesto termina primero y el mundo responde después — el botón se apaga, y *entonces* se abre la puerta.

⚠ **`FInterpTo` nunca llega exactamente a 0**, por eso el umbral `< 0.02` y el `SetActorScale3D(0,0,0)` explícito antes de disparar nada. Sin eso el timbre quedaría visible en un tamaño ínfimo.
✅ **La duración de la salida la manda `LeaveTime`** (0,5 s), independiente de `AppearTime` (1,0 s).

## 🔴 Se COLOCA a mano, no se spawnea (decisión 2026-08-18)
El primer diseño lo spawneaba la puerta en un `TargetPoint` tagueado. **Se descartó, y la razón vale para cualquier objeto así:**
- El TargetPoint **también es un actor** → spawnear no ahorra nada, agrega.
- Colocado en el sublevel **se streamea con su sala gratis**: sin `BellRef`, sin `KillBell`, sin que el actor termine en el persistente.
- El spawn por TargetPoint se gana su lugar cuando hay **N cosas desde datos** (las burbujas de Attracting) o cuando el objeto no puede existir hasta runtime. Un timbre es uno por sala, estático, autorado.

**Y los tres bugs que costó** antes de sacarlo: el **Hall no tiene `BP_Door_SC`** (su puerta es otro BP pendiente) así que nadie lo spawneaba ahí; `GetAllActorsOfClassWithTag` busca **en todo el mundo** y una sala podía robarle el TargetPoint a otra; y la puerta suelta del persistente quedó con `bOpenByBell` en true (ver gotcha §119).

**El flujo hoy:** colocás un `BP_Bell` en el sublevel, lo posicionás en el viewport, y le das a la puerta el actor tag que coincida con `BellTag`.

## 🔴 PENDIENTE ACORDADO: simplificar a fondo
Beltrán, 2026-08-18: *"¿es necesario tener 20 funciones y tantas variables? … Siento que tenemos que aprender a construir BP con la menor cantidad de nodos posibles. Al grano, solo la funcionalidad correcta y necesaria."* **Acordado: primero lo prueba, después se hace el análisis de simplificación.**

Estado hoy: **22 funciones y 31 variables**. Las **16 editables son las perillas que él pidió** (3 audios, tiempos, distancias, colores, tag, háptica) — ahí no hay grasa. La grasa está en haber hecho **una función por paso** en vez de una por responsabilidad. El colapso identificado, a **11**:

| Queda | Se come |
|---|---|
| `Boot` | `CacheRefs` + `CachePawn` + `ApplyBodyLook` + `PushRingLook` |
| `TickBell` | `RunBell` |
| `TickAppear` | `PlayAppear` |
| `HandNear` | `AnyHandClose` |
| `HoverEdge` | `StartCharge` + `StopCharge` + `PulseHover` |
| `Fire` | `Advance` |
| `UpdateHold` · `UpdatePress` · `ApplyRing` · `OpenDoors` · `TickLeave` | — |

Y 3 variables internas: `bHandsNear` se funde en `bTouching`, `bDone`/`bLeaving` son una sola, `AppearVolume` se pliega en el pin del `SpawnSound`. 💡 **Fundir `HandNear` + `AnyHandClose` elimina de raíz el bug del nodo podado**: sin llamada entre funciones no hay exec que se pueda quedar suelto.

## TODO
- [ ] 🔴 **Probar el hover en visor** ahora que el nodo dejó de podarse.
- [ ] 🔴 **Hacer el colapso de arriba** después del test.
- [ ] Ver el anillo en escena (el `RadialSlider` está armado pero nunca se miró).
- [ ] Ajustar `TouchRadius` y la altura del timbre contra la postura sentada real.
- [x] Revisadas las 6 puertas. 🔴 **Dos caían en callejón sin salida:** la del **Hall** tenía `bOpenByBell` en true pero **sin actor tag** (el timbre no la encontraba y la apertura por distancia estaba apagada) → se le puso el tag `bell`; la de **Entering** tenía el tag `bell` y `bOpenByBell` en true **sin ningún timbre en su sublevel** → vuelve a apertura por distancia. Las otras 4 están en false, OK.
- [ ] Si más salas llevan timbre, **darle a cada par un tag distinto** (`bell_hall`, `bell_entering`…): `GetAllActorsOfClassWithTag` busca en TODO el mundo, y hoy sólo salva que las salas no estén cargadas a la vez.

## Relacionados
- [[BP_Door_SC]] — a quién abre · [[BP_Sensor]] y [[BP_TouchSensor]] — de donde sale el patrón de proximidad · [[BP_SaveButton]] — el otro hold de 3 s (ese sí por gatillo) · [[BP_MenuButton]] — de donde salió el `CheckHand` que sí funcionaba.
