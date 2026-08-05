# BP_SaveButton — progress tracker

Botón **"FINISH MELODY"** del stage Touch (fase **R5** del brief [`docs/stages/touch-attracting.md`](../../../../docs/stages/touch-attracting.md)). Cierra la etapa: cuando los 5 slots están llenos, el usuario lo apunta con el láser y **sostiene el gatillo 3 segundos** para guardar la melodía.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_SaveButton.BP_SaveButton` · **parent**: Actor
- **in level**: `FinishMelodyButton` (`BP_SaveButton_C_0`) en `L_Touch`, en **(55, 0, 55)** con pitch 90 — o sea **al centro de la fila de slots (que están en X=55, Z=75) y 20 cm por debajo**.
- **Status**: 🟡 **Compila y guardado. FALTA TEST EN VISOR.**

## 🔴 Las dos decisiones de diseño (dadas por el usuario, 2026-08-05)
1. **El botón SIEMPRE está presente.** No aparece ni desaparece. Vive fijo al centro de la mesa, justo abajo. Lo que cambia al llenarse los 5 slots es que **se "activa"**: crece un poco (y más adelante, color). La disponibilidad se comunica, no se revela.
2. **Se confirma con un HOLD de 3 segundos**, no con un click: apuntarlo con el láser y **sostener el gatillo**. Un click sería demasiado fácil de disparar sin querer para una acción que cierra la etapa.

## Componentes (CDO)
- `DefaultSceneRoot`.
- `Mesh` (cilindro r=8, alto 3 → un disco). 🔴 **CON colisión** (`QueryAndPhysics`, el default) — al revés que `BP_TouchSensor`: este objeto **tiene que ser golpeado por el line trace** para poder apuntarse. `CastShadow` off (Quest).
- 🔴 El **actor** lleva el tag **`Aimable`**. Sin eso, `BP_AimBeam.ResolveHover` lo ignora y nunca hay hover. El tag va en el ACTOR, no en el componente.

## Variables
- `Director : BP_AttractDirector` — cacheado en BeginPlay; de ahí sale el array `Slots`.
- `bAvailable : bool` — los 5 slots ocupados.
- `bHolding : bool` · `HoldingBeam : BP_AimBeam` — quién está sosteniendo el gatillo sobre mí.
- `HoldDuration : float = 3` · **instance-editable** — la palanca del tiempo de confirmación.
- `HoldT : float` — segundos acumulados del hold actual.
- `AvailT : float` — 0→1 interpolado, el "cuánto se ve disponible". Separa el estado lógico (`bAvailable`, binario) de la lectura visual (suave).
- `BaseScale : **Vector**` — 🔴 **la escala AUTORAL del componente, capturada en BeginPlay** con `Class|SceneComponent|GetRelativeScale3D`. NO es un float ni un 1.0 fijo. Ver la trampa de abajo.
- `AvailScale`(1.25, instance-editable) · `AvailSpeed`(6) — palancas del feedback.
- `MID : MaterialInstanceDynamic` — creado en `CacheDirector`, **listo para el color**, todavía sin usar (ver TODO).
- **Dispatcher `OnConfirmed`** — lo que R6 va a escuchar para guardar y cerrar la etapa.

## Grafos
- **EventBeginPlay**: `CacheDirector()`.
- **EventTick**: `RefreshAvailable()` → `UpdateHold(Delta)` → `UpdateVisual(Delta)`.
- **`CacheDirector()`**: `GetAllActorsOfClass(BP_AttractDirector_C)` → `Director`; crea el `MID` sobre `Mesh`.
- **`RefreshAvailable()`**: pone `bAvailable = true` y recorre `Director.Slots`; **cualquier slot con `Occupant` inválido lo baja a false**. Sin early-exit y sin contador: setear-true-y-desmentir es más corto y no necesita salir del bucle.
- **`BeginHold(Beam)`**: solo si `bAvailable` → guarda el beam, `bHolding=true`, `HoldT=0`.
- **`EndHold()`**: limpia las tres.
- **`UpdateHold(Delta)`**: si `bHolding` → `IsValid(HoldingBeam)` → `TickHold(Delta)`; si el beam murió, `EndHold()`.
- **`TickHold(Delta)`**: si **dejó de estar disponible** o **el beam ya no me apunta** (`beam.CurrentHovered != self`) → `EndHold()`. Si no, acumula `HoldT` y al pasar `HoldDuration` llama `Confirm()`.
- **`Confirm()`**: `EndHold()` → `bAvailable=false` → log → **`CallOnConfirmed`**.
- **`UpdateVisual(Delta)`**: `AvailT` con `FInterpTo` hacia 0/1, y escala = `BaseScale × (1 + AvailT×(AvailScale−1)) × (1 + progreso×0.35)`. **La misma escala comunica las dos cosas**: disponible (crece y se queda) y progreso del hold (sigue creciendo mientras sostenés).

## Cómo recibe el input (vive en `BP_AimBeam`)
El botón **no lee el gatillo**: se lo avisa el beam, que ya es el dueño del input.
- `TryGrab` (en `Started`): el pin **`CastFailed`** del cast a `BP_SoundBubble` → **`TryGrabButton()`** → castea `CurrentHovered` a `BP_SaveButton`, guarda `HeldButton` y llama `BeginHold(self)`. Si ese cast también falla, la cadena muere sola (el `CastFailed` del segundo cast queda sin conectar) → no hay `Accessed None`.
- `TryRelease` (en `Completed`): arranca con **`ReleaseButton()`** → si hay `HeldButton` válido, `EndHold()` y lo limpia. Soltar el gatillo **siempre** cancela, aunque hayas dejado de apuntar.
- Var nueva en el beam: `HeldButton : BP_SaveButton`.

## ⚠ Trampas ya mordidas al construirlo
- 🔴🔴 **`SetRelativeScale3D` con un escalar uniforme PISA la escala autoral del componente.** Mordió en visor: el botón apareció **gigante** (un cilindro de 1 m que tapaba toda la vista). Causa: `PrimitiveTools.add_cylinder(radius=8, height=3)` no crea un mesh de ese tamaño — usa `/Engine/BasicShapes/Cylinder` (100 u) y **codifica el tamaño pedido en `RelativeScale3D` = (0.16, 0.16, 0.03)**, que además es **NO uniforme**. Escribir `scale = 1.0` lo devolvía a 100 u.
  **Regla:** cualquier animación de escala tiene que **partir de la escala autoral, no de 1**. Guardarla en una var **Vector** en BeginPlay (`Class|SceneComponent|GetRelativeScale3D`) y multiplicar por un factor escalar. Sirve para cualquier componente con escala no uniforme, y sobrevive a que después se cambie el tamaño en el editor.
- 🔴 **`(bind _s ...)` usado 3 veces dentro de un `MakeVector` NO deduplica**: el DSL lo **inlineó las 3 veces** (3× toda la cadena de multiplicaciones). Fix: `(* (Math|Vector|VectorOne) _s)` → una sola evaluación. **Verificar siempre releyendo el grafo**, es el §1 de `bp-lean-construction.md` y muerde en silencio.
- 🔴 **`Rendering|Material|SetScalarParameterValue` está DUPLICADO** (uno para `MaterialParameterCollection`, otro para `MID`) y `write_graph_dsl` **agarra el equivocado** ("Could not connect pin MID to Collection"). El DSL no sabe desambiguar → hay que crear ese nodo por **cirugía con `declaring_class`**. Por eso el color quedó pendiente.
- **Llamar una función propia con parámetros desde el DSL**: el primer pin posicional es **`self`**, no el primer argumento. Usar keyword: `(CallFunction|TickHold :DeltaSeconds DeltaSeconds)`.
- **El dispatcher se llama con `Default|CallOnConfirmed`**, no `|CallOnConfirmed`.
- **Igualdad de objetos**: `(== a b)` resuelve a `Utilities|Equal(Object)`. No existe `Math|Object|Equal`.
- ⚠ **`bAvailable` genera los accesores `GetAvailable`/`SetAvailable`** (sin la `b`).

## TODO / next
1. 🔴 **Test en visor**: con 4 slots el botón está chico y el hold no hace nada; al llenar el 5º **crece**; lo apuntás + gatillo 3s → crece progresivamente y confirma (log `TCH|FINISH MELODY confirmed`). Soltar antes, o dejar de apuntarlo, **cancela y vuelve a cero**. Sacar una burbuja lo desactiva.
2. **Material unlit emisivo** con parámetros escalares `Available` y `Progress`; el `MID` ya está creado esperándolo. Agregar los `SetScalarParameterValue` **por cirugía** (ver trampa arriba).
3. **Texto "FINISH MELODY"** — en **inglés** (regla del proyecto). Falta decidir si va como widget world-space o textura en el material.
4. **R6**: suscribirse a `OnConfirmed` desde el Director → `SG_Melody` + `SaveGameToSlot` + vuelta final + fade + `OpenLevel`.
5. Ajustar altura/posición sentado — hoy a 20 cm bajo la fila de slots, a ojo.

## Session log
- **2026-08-05:** creado desde el stub vacío. Mesh, tag `Aimable`, 11 variables, dispatcher, 8 funciones y el EventGraph. Hook de input en `BP_AimBeam` (`TryGrabButton`/`ReleaseButton` + var `HeldButton`). Instancia colocada en `L_Touch`. Compila y guardado.
