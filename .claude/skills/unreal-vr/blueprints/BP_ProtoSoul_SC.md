# BP_ProtoSoul_SC — el alma personal del usuario

> `/Game/SoulCharger/Core/ProtoSoul/` · creado 2026-08-18 · **duplicado de [BP_Alma_SC](BP_Alma_SC.md)**, con material propio `M_ProtoSoul` (también duplicado, para que tocarlo no afecte a Alma).
> 🔴 **Hay 5 instancias COLOCADAS a mano en el persistente** (`L_SoulCharger`), tagueadas `soul_pick`, que son las candidatas de la elección (2026-08-19; antes se spawneaban, ver [BP_SoulPicker_SC](BP_SoulPicker_SC.md)). **La malla, el color y el tamaño de cada una son datos de autor EN LA INSTANCIA**, no en el CDO.
> **Estado: 🟡 malla intercambiable + giro + hover + sistema de puntos completos y probados en Play; sembrado por el picker verificado en PIE. Falta el visor.**

---

## Qué es
El alma personal de cada usuario: la elige al principio entre 5 opciones (distinta malla y color cada una), lo acompaña toda la experiencia, y se va cargando y transformando. Alterna entre **puntos fijos del mundo** y **anclada frente a la cara**, con cambio suave de posición **y tamaño**. Lleva 4 anillos (entering azul, recognizing rojo, loving morado, attracting naranja); el de surrounding lo dibuja el usuario.

## Lo que ya funciona
| Pieza | Detalle |
|---|---|
| **Malla intercambiable** | Variable `Mesh` + `ApplyMesh()` en el Construction Script. 🔴 Corre **antes** de `CreateDynamicMaterialInstance`: cambiar la malla después se lleva puesto el MID y se pierden todos los parámetros. Con guarda de `IsValid` para que un `Mesh` vacío no deje una ameba invisible. |
| **Giro lento y errático** | `StepSpin(DT)` sobre el **`Body`**, no sobre el actor (decisión de Beltrán: *"los anillos los moveremos de manera distinta"*). Tres ángulos que se acumulan a velocidades que oscilan con senos de frecuencias coprimas y fases distintas → nunca se repite y va cambiando de eje solo. `SpinSpeed` 50 · `SpinDrift` 0.4. Arranca desde quieto porque los senos empiezan en 0. |
| **Hover** | Detección de mano copiada de [BP_Bell](BP_Bell.md). Todo cuelga de un único `HoverT` suavizado, así que escala, giro, color y sonido entran y salen juntos. |

### El hover en detalle
- **Escala** ×`HoverScale` · **giro** hacia `HoverSpinSpeed` (interpolado, no salta) · **sonido + háptica** sólo en el flanco.
- **Color:** 🔴 lo que se mapea NO es el brillo. `EdgeIntensity` (×`HoverEdgeBoost`) enciende el contorno, y **`FresnelPower`** (hacia `HoverFresnelPower`) mueve **dónde vive el color** — barre entre "todo el cuerpo teñido" y "un filo en la silueta". Eso se lee como que el objeto *se define* al mirarlo. El tinte del `RimColor` va con **`LerpUsingHSV`**, no lerp RGB: el RGB hacia un color claro **desatura** y sale blanco (error real de esta sesión), el HSV hace que el tono **viaje**.
- 🔴 **`CoreColor` NO se toca a propósito.** Las 5 amebas se distinguen por su color, que es justo lo que el usuario está comparando: el hover debe **intensificar lo que ya es**, no cambiar lo que es.
- **`HoverHysteresis`** (1.25): el radio de salida es mayor que el de entrada. Sin esto el hover **parpadea** con la mano quieta — el mando tiembla milímetros y cruza un umbral único.
- **`HoverGizmo`**: esfera de alambre naranja con el radio real, sincronizada desde el Construction Script. Invisible en juego.
- **`bHoverEnabled`**: se apaga cuando termina la selección inicial (el hover sólo existe en esa etapa).

### 📏 El flotar también escala con `Size` (2026-08-19)
Beltrán: *"cuando la ameba se achica … se ve que se mueve demasiado de su punto"*. Misma raíz que en los anillos: **`FloatAmount` está en centímetros de MUNDO** y el WPO se suma después de la escala, así que la ameba de 5 cm seguía derivando los mismos 4-6 cm.
✅ **Arreglo: un `FloatScale` en `M_ProtoSoul` que multiplica el `FloatAmount` ANTES de las tres máscaras X/Y/Z** (2 nodos, insertados entre el parámetro y sus consumidores — sin tocar el resto del grafo ni el Construction Script, que es intocable por el §142). Lo empuja `ApplyRingScale` con el mismo `k = Size / RingSizeRef` que ya calculaba para los anillos, y **sólo cuando cambia**.
💡 **Lo que NO hubo que tocar, y es mérito del diseño original:** la **deformación** ya era proporcional (`WobbleAmount` es fracción del `ObjectRadius`, no centímetros) y la **rotación** del flotar también (producto cruz contra la posición relativa, que ya viene escalada). El único término absoluto era la traslación.
✅ **Medido en PIE:** con `Size = 0,3` → `FloatScale = 1`; forzando `Size = 0,05` → **`FloatScale = 0,1667`**, igual que el `RingRoot`. Cero `Accessed None`.
🔧 La perilla de referencia es **`RingSizeRef`** (0,3) — la comparten cuerpo y anillos: es "a qué tamaño de ameba está autorado todo".

⚠ **El flotar vive en el MATERIAL (WPO), así que se mueve el dibujo y NO el actor.** La zona táctil queda fija en el centro real. Con `HoverRadius` chico (10-15 cm) los 4-6 cm de `FloatAmount` son un tercio del radio: **ves la ameba en un lado y la tocás en otro**.

---

## ⚠️🔴 SECCIÓN HISTÓRICA — el sistema `VInterpTo` de abajo YA NO ES EL QUE CORRE (nota 2026-08-21)
Lo que sigue describe el diseño del 2026-08-18. **El código vigente es otro**: `TrackTarget` ramifica en `TravelStep` (viaje con ease, usando `bTraveling`/`TravelT`/`TravelFrom`, que esta sección da por eliminados) o en **`AnchorStep`, que es un SNAP DURO**, no un `VInterpTo`. Y desde el 2026-08-21 el anclaje a la cabeza va por **attach real a la cámara** (ver la tabla de verbos arriba).
👉 **Esta doc desactualizada costó tiempo real**: al buscar el "lazy follow" que reportaba Beltrán, la frase de abajo *"queda orgánico, con un leve retraso"* apuntaba a una interpolación que no existía. Se conserva como historia del diseño, pero **no describe el comportamiento actual**.

## ✅ El sistema de puntos, rediseñado (2026-08-18) — verificado en Play
**Se dejó de guardar una coordenada y se guarda la REFERENCIA al actor del punto** (`TargetRef`). `TrackTarget(DT)` lee su transform **cada frame** e interpola con `VInterpTo` / `RInterpTo` / `FInterpTo`:
```
SetActorLocation(VInterpTo(actual, target.location, DT, TravelSpeed))
SetActorRotation(RInterpTo(actual, target.rotation, DT, TravelSpeed))
SetSize(         FInterpTo(Size,   target.scale.X,  DT, TravelSpeed))
```
Eso resuelve las dos cosas con un solo cambio y **elimina los casos especiales**:
- **Sigue un ancla en movimiento** (la cara) sin ningún attach, porque relee el target cada cuadro.
- **El tamaño viaja**, y sale de la **escala del TargetPoint** — lo que pidió Beltrán.
- **El mismo código sirve para puntos fijos y móviles**: un punto quieto simplemente no se mueve.

💡 Desapareció todo el estado `TravelT` / `bTraveling` / `TravelFrom`: con `InterpTo` la aceleración y el frenado son gratis y nunca sobrepasa. `MoveTo(tag)` quedó en **una línea** (sólo `FindPoint`).
⚠ **`InterpTo` es asintótico**: se acerca y frena pero nunca "llega" del todo. Para un alma que sigue la cabeza queda orgánico, con un leve retraso. Si hace falta que clave exacto → `VInterpToConstant`.
⚠ **`Size` es la variable que consume `ApplyHoverScale` cada frame.** El viaje escribe `Size` y deja que esa función aplique la escala al `Body` — si el viaje tocara el `Body` directo, los dos se pelearían.
🔧 `TravelSpeed` (4) es la única perilla del movimiento. 6-8 si se quiere más pegado.

### 🔎 El falso bug que costó tres rondas de prueba
Beltrán reportó *"se desprende de mi cabeza y se pone enorme, no vuelve al target anterior"*. **No había ningún bug**: `TP_SoulStart` estaba a **69 cm de su cara** (casi encima del punto de cara) y con **escala 1,0 contra 0,05**. O sea que "volver al mundo" se veía como "quedarse adelante, gigante".
👉 **Al probar un sistema de puntos, separarlos de verdad antes de juzgarlo.** Quedaron a 2,4 m y con escalas 0,05 / 0,35.

## Historia: por qué se rediseñó
Diagnosticado el 2026-08-18 probando en Play. **Dos síntomas, una sola raíz.**

`FindPoint(tag)` guarda **sólo `GetActorLocation`** del punto, y `MoveTo` **lo lee UNA VEZ** al arrancar el viaje y después interpola hacia esa coordenada fija.

| Síntoma | Causa |
|---|---|
| La ameba viaja a la cara pero **no cambia de tamaño** | se descartan escala y rotación del punto |
| Al mover la cabeza, **se queda donde estaba el target** | el destino se congela al inicio del viaje; nunca se vuelve a mirar el punto |

👉 **No alcanza con agregar un attach.** El sistema de Alma fue diseñado para puntos **quietos**; la proto ameba necesita **seguir** un ancla en movimiento.

### El rediseño acordado
Guardar la **referencia al actor** del punto (`TargetRef`), no una coordenada, y en `StepTravel` leer su **transform actual cada frame**:
- **viajando** → interpolar posición **y tamaño** desde el origen hacia los valores actuales del target, con `TravelT` eased;
- **llegado** → seguir copiando el transform del target cada frame.

Así **el mismo código sirve para puntos fijos y para el ancla de cara**, sin attach ni casos especiales. El tamaño sale de la **escala del TargetPoint**, que es lo que Beltrán pidió: *"los target point no sólo deben definir la ubicación, sino también el tamaño"*.
⚠ `Size` es la variable que ya consume `ApplyHoverScale` cada frame, así que el viaje debe escribir `Size` y dejar que esa función aplique la escala — **si no, los dos se pelean por el `Body`**.

---

## El ancla de cara: `BP_FaceAnchor_SC`
Malla **`/Engine/VREditor/Devices/Generic/GenericHMD`** (la misma que usa el pawn), `bHiddenInGame`. En `BeginPlay` se engancha al **`HeadMountedDisplayMesh`** del pawn con `SnapToTarget` en posición y rotación y **`KeepWorld` en escala** — si se snapea la escala hereda el 1.5 del padre y se duplica. Por eso su malla va en `(0,0,0)`: **el componente del pawn ya lleva el offset de 8 cm**.

🔴 **El truco de fondo: en el editor no existe el pawn**, así que no hay a qué attachear. El ancla es un **doble** que permite autorar, y el enganche al HMD real sólo ocurre en runtime. El `TargetPoint` con tag `soul_face` se hace **hijo del ancla en el Outliner**, y así se puede agarrar y mover libremente en el viewport para calibrar dónde y de qué tamaño va la ameba frente al ojo.

## Rig de prueba (heredado de Alma)
`DebugPoints = ["soul_start", "soul_face"]`, `bDebugKeys` on. **Tecla 3** = viaja al siguiente punto (ciclan) · **4** = desaparece · **5** = aparece de golpe. ⚠ **Sólo en Play, no en Simulate.**

---

## 🆕 La API que consume el picker (2026-08-19)
Dos funciones nuevas, las dos **sin tocar el Construction Script** (intocable por el §142 de `gotchas.md`: el DSL agarra el `SetScalarParameterValue` del *Material Parameter Collection* y el write falla con un error que culpa a la variable `MID`).

| Función | Qué hace |
|---|---|
| **`Configure(NewMesh, NewColor)`** | Escribe `Mesh` y `CoreColor`, llama `ApplyMesh` (cambia la malla) y re-empuja el color con **`SetColorParameterValueOnMaterials` sobre el `Body`** — ese nodo **reusa el MID que ya existe**, así que no hace falta ni la variable `MID` ni `CreateDynamicMaterialInstance`, y no hay ambigüedad de nombre. Loguea el material del slot 0 como **control positivo**. |
| **`Select(FaceTag)`** | El cierre de la elección: apaga `bHoverEnabled`, reproduce `SelectSound` vía `PlayHoverFx` (que ya trae sonido **+ háptica**) y `MoveTo(FaceTag)`. `bHovering` se auto-apaga solo, porque `HandNear` lo calcula como `bHoverEnabled AND bHandsNear`. |
| 🆕 **`Sleep()`** | **El estado dormido: invisible, quieto e inseleccionable.** Escribe el estado terminal **de una** (sin animación): `bHoverEnabled=false`, `bHovering=false`, `HoverT=0`, `bLeaving=true`, `bAppearing=false`, `AppearT=0`, escala del `Body` en 0. ⚠ **Sólo se sostiene gracias al arreglo de los dos dueños de la escala** — antes, `ApplyHoverScale` la habría vuelto a inflar al frame siguiente. |
| 🆕 **`Reveal()`** | Enciende `bHoverEnabled` y dispara `Appear` — entra con su animación y **recién ahí** es hovereable. |

🆕 **`bStartAsleep`** (cat. *F - Aparicion*, CDO en **true**): el `BeginPlay` ramifica a `Sleep()` en vez de `Appear`. 🔴 **No es un lujo: el orden de `BeginPlay` entre actores no está garantizado**, así que si el picker durmiera a las almas desde su propio `BeginPlay`, alguna podría haber arrancado a crecer un par de frames antes. Con el flag en el alma, el sueño es determinista.

🔬 **La advertencia de "cambiar la malla se lleva puesto el MID" quedó ACOTADA, medida en PIE:** el log dio `MID_M_ProtoSoul_0` en las 5 almas **después** del cambio de malla. `SetStaticMesh` sólo **recorta** los override materials cuando la malla nueva tiene MENOS slots; con una malla de un solo material el slot 0 (donde el CS dejó el MID) sobrevive. 👉 La regla precisa es: **el orden importa dentro del Construction Script**; en runtime, sobre un componente ya construido, el MID aguanta el swap.

## 🆕 El QUINTO anillo — Surrounding sí lleva anillo (2026-08-24)
🔴 **Se revirtió la decisión de "en Surrounding no hay anillo".** Beltrán lo pidió de vuelta: *"vuelve a agregarlo… en el mismo formato y parámetros en el que están los otros… alrededor del que está amarillo"*. Ahora son **cinco**.

- **`Ring4`** — `ProceduralMeshComponent` colgado de `RingRoot`, como los otros cuatro. Transform continuando la serie que autoró Beltrán en las instancias: **roll 90 (igual en los cinco), pitch 26, escala 1,72** (los otros: pitch 12 / 34 / −18 / −30 y escalas 1,00 / 1,18 / 1,36 / 1,54 — el paso es +0,18).
- **`RingColors[4]`** = verde `(0.145, 1, 0.28)`, el color de Surrounding.
- Extendidas a índice 4: **`CollectRingComps`**, **`BuildAllRings`**, **`HideRings`** y **`ApplyRingScale`**. `SeedRings`, `DrawRing`, `StepRings` y `TickRingKey` ya eran genéricas (`TickRingKey` topea con `Length(RingComps)`, así que la tecla 6 ahora llega hasta el quinto sola).
- ⚠ **Los cinco actores colocados necesitaron mano**: el componente nuevo llegó con la transform de FÁBRICA y `RingColors` tenía **override propio de 4 entradas** en cada instancia. Es la §164 otra vez. Hubo que escribir en los cinco, **campo por campo** (`roll`, `y`, `z` por separado: en una instancia `set_properties` aplica sólo el primer campo de un struct).

### ⏱ Cuándo aparece
Lo dispara **`BP_Director_Story.BeginEnding`**, o sea **al cerrar Surrounding**, con el mismo `DrawRing` que los otros cuatro.
🔴 **No se tocó el flujo de subs del director.** `RingIndex` sigue siendo `[-1,0,1,2,3,-1]`: el −1 de Surrounding es lo que enruta la sala 5 a `BeginEnding`, y **`RunEnding` arranca en el sub 6** — meter el anillo por el camino normal habría corrido la numeración y roto el final. En cambio `BeginEnding` ahora: dibuja el anillo → espera **`FinalRingHold`** (2,8 s; el anillo tarda `RingDrawTime` 2,5) → recién ahí `CloseRoomNow` cierra la sala, y el timer del final se corre el mismo tanto. **Sin ese retraso el fundido (1,2 s) se comía el anillo a la mitad.**
Palancas nuevas en el director, categoría *C - Tiempos y tags*: **`FinalRingIndex`** (4) y **`FinalRingHold`** (2,8).
✅ Verificado: los cinco componentes presentes con su transform, `RingColors` de 5 en el CDO y en las 5 instancias, compila y corre sin `Accessed None`. ⬜ **Falta el juicio visual** — los anillos son aditivos y sobre el fondo claro del Hall se lavan, así que en captura no se distingue el verde.

## 💍 Los 4 anillos — componentes NATIVOS (migrado 2026-08-19)
Los anillos son **4 `ProceduralMeshComponent`** (`Ring0..Ring3`) colgando de `RingRoot`, con la generación del trazo, el material y la animación **adentro de este Blueprint**. [[BP_SoulRing_SC]] sigue existiendo sólo como **banco de pruebas suelto** en el Hall; la obra ya no lo usa.

🔴 **Se migró desde `ChildActorComponent` después de que esa indirección causara CINCO bugs en una tarde** (`ChildActorClass` nulo · variables nuevas en cero · template nulo · actores hijos rancios en el editor · el MID perdido al duplicar). Todos tenían la misma raíz: **componente → template → actor hijo** son tres saltos, y cada uno se rompe cuando el Blueprint cambia después de poblar el nivel. Con componentes nativos **ninguno de esos modos de falla existe**.

| Función | Qué hace |
|---|---|
| **`BuildAllRings()`** (Construction Script) | `CollectRingComps` + `BuildOneRing` × 4. **Se ven y se regeneran en el viewport al tocar cualquier perilla.** |
| **`BuildOneRing(Index)`** | `ResetRingArrays` → `BuildRingSamples` → `BuildRingTris` → `CreateMeshSection` → `PushRingMat`. Los 4 comparten los mismos arrays de trabajo: se llenan y se vacían por anillo. |
| **`AddRingSample(I)`** | La cinta con torsión: 2 vértices por muestra, `UV0.x` a lo largo, y 🔴 **la dirección del ancho guardada en la NORMAL** (el material es unlit, la normal queda libre). |
| **`PushRingMat(Index)`** | `SetMaterial` + todos los parámetros, incluido `Color = RingColors[Index]` y `ScaleComp = Size / RingSizeRef`. **Es el único lugar que habla con el material.** |
| **`HideRings()`** (BeginPlay) | `DrawIndex = -1` y los 4 `RingReveal` a 0. Los anillos **nacen visibles en el editor y ocultos en juego**. |
| **`DrawRing(Index)`** | 🔴 **El punto de entrada público.** Arranca la animación de ese anillo. Lo llamará la ceremonia al cerrar cada etapa. ⚠ **Es un REPRODUCTOR, no un setter: tiene UN SOLO slot** (`DrawIndex`). Llamarlo dos veces en el mismo frame hace que la segunda llamada **pise** a la primera, y el anillo abandonado queda en `Reveal = 0` (invisible) para siempre. **No sirve para sembrar varios** → usar `SeedRings`. |
| 🆕 **`ApplyOnTop(OnTop)`** (2026-08-21, prueba HUD) | 🧪 **Hace que la ameba se comporte como el HUD de OVR Metrics: las manos NO la tapan.** Cambia el material del `Body` entre `M_ProtoSoul` y **`M_ProtoSoul_HUD`** (duplicado con **Disable Depth Test**, que en el renderer movil pone el test en `Always` — [SRC] `MobileBasePass.cpp:647`). Se llama con `bHudOnTop` desde `AnchorToHead` y con `false` desde `AnchorRelease`, o sea **solo mientras esta anclada a la cabeza**. 🔴 Hizo falta duplicar el maestro porque `DisableDepthTest` **no** es sobrescribible por instancia de material. ⚠️🔴 **Al cambiar el material se pierde el MID con TODOS sus parametros.** Primera version repuso solo `CoreColor` y Beltran lo cazó en el visor: *"debe tomar los parametros que ya tienen mis amebas en el editor, tanto del material como del efecto flotar"*. ✅ Fix: **`PushBodyMat()`**, que repone los **22 parametros que empuja el Construction Script** (Wobble×3, Fresnel, Brightness, Opacity×2, CoreColor, RimColor, Grad×5, Edge×3, Float/Rot×5) **+ `FloatScale`**, y despues `PushHoverLook`.
🔎 **`FloatScale` era el que se escapaba**: no está en el Construction Script sino en `ApplyRingScale`, que **solo lo empuja cuando el valor CAMBIA** (guarda `RingScaleLast`) — asi que tras un swap no se reponia nunca y el flotar quedaba a escala de mundo. `PushBodyMat` lo recalcula (`Size / max(RingSizeRef, 0.01)`).
🔧 **Usa `Set*ParameterValueOnMaterials`** (apunta al COMPONENTE, crea y reusa el MID solo) en vez de la variable `MID` — es lo que manda el §142 y evita la colision de nombres con el nodo de Material Parameter Collection.
⚠️ **Mantenimiento:** si se agrega un parametro al Construction Script, **agregarlo tambien a `PushBodyMat`** o el HUD lo perdera. Se duplico la lista a proposito para no tocar el Construction Script, que ademas construye los anillos.
✅ Verificado en PIE parametro por parametro contra la instancia: Wobble 0.096, GradAmount 0.468641, PhaseSeed 0.344, FloatAmount (1.513265, 1.45165, 1.596094) y **FloatScale 0.1** (= 0.03/0.3), todos identicos. Verificado: el MID nuevo cuelga de `M_ProtoSoul_HUD` y conserva CoreColor/RimColor/EdgeIntensity/FresnelPower. **Los anillos van por otra via**: `M_SoulRibbon_SC` tiene Disable Depth Test **siempre** (son exclusivos del alma del usuario, y evitarlo exigia cirugia en `PushRingMat`). **Para volver atras:** `bHudOnTop=false` en el CDO (cuerpo) y destildar Disable Depth Test en `M_SoulRibbon_SC` (anillos). |
| 🆕 **`AnchorToHead()`** (2026-08-21, 2ª pasada) | 🔴🔴 **El anclaje a la cabeza va a la CÁMARA DEL PAWN, no al TargetPoint.** Medido con `find_actors(root=pawn)`: bajo el pawn cuelgan `BP_Director_Movement` (su viñeta) y `BP_FaceAnchor_SC`, **pero `TP_soul_face` NO** — ese punto nunca estuvo attacheado a la cabeza, así que attachearse a él heredaba el retraso de lo que sea que lo mueva. Ahora: se coloca en la pose autoral del punto (`SetActorLocation/Rotation`) y **acto seguido se attachea a la `CameraComponent` con `KeepWorld`**, que congela ese offset y lo vuelve rígido contra la pose del visor ya actualizada. Se elige este camino cuando `NextTag == HeadTag` (`soul_face`, variable **no** instance-editable para evitar que nazca en `None`); para cualquier otro punto sigue el attach normal al TargetPoint. `FindPoint` ahora guarda el tag pedido en `NextTag` (antes no lo hacía). |
| 🆕 **`AnchorAttach()` / `AnchorRelease()`** (2026-08-21) | 🔴 **Matan el frame de retraso del anclaje a la cabeza.** `AnchorStep` copiaba la transform del punto en el Tick de la ameba; en VR eso la deja **un frame atrás** de la cabeza y se lee como lazy follow. Ahora, al terminar de viajar, la ameba **se ATTACHEA** al TargetPoint (`SnapToTarget` en loc/rot, `KeepWorld` en escala para no pisar `Size`) y hereda la pose ya actualizada, sin retraso. `AnchorAttach` se llama al final de `AnchorStep`; `AnchorRelease` al final de **`StartTravel`** y de **`StartCarry`** (viajar o ser agarrada requieren soltar el ancla). 🔴 **La guarda no es "¿estoy attacheada?" sino "¿mi padre es el TargetRef VIGENTE?"** — si fuera lo primero, `AppearAt` (que cambia `TargetRef` **sin** pasar por `StartTravel`) dejaría la ameba pegada al punto anterior. Sin variable de estado propia: la fuente de verdad es `GetAttachParentActor`. |
| 🆕 **`SeedRings(Count)`** (2026-08-21) | **Muestra los primeros `Count` anillos YA COMPLETOS, sin animación.** Escribe `RingReveal[i] = 1.05` (el valor final del ease de `StepRings`) y llama `PushRingMat(i)`, **sin tocar `DrawIndex`** — por eso no compite con la animación en curso ni la cancela. La usa el salto de debug de [[BP_Director_Story]] para que una sala saltada arranque con los anillos de las etapas ya vividas. Nace del bug de arriba. |
| **`StepRings(DT)`** (Tick) | Avanza **sólo el que se está dibujando** (`DrawIndex`), con `Ease(EaseOut, 0→1,05)` en `RingDrawTime` segundos. |
| **`ApplyRingScale()`** (Tick) | `RingRoot.escala = Size / RingSizeRef` y, **sólo cuando cambia**, re-empuja `ScaleComp` a los 4. |

💡 **Un solo estado de animación, no cuatro:** como la obra dibuja **un anillo por etapa**, alcanza con `DrawIndex` + `DrawT`. `RingReveal` (float[4]) guarda lo ya dibujado para que los anillos completos se queden puestos.

🎨 **Dónde autorar** (todo en `BP_ProtoSoul_SC`, categoría *R - Anillos*):
| Qué | Dónde |
|---|---|
| Forma del trazo | `RingRadius` 25 · `RingTurns` 2,5 · `RingWidth` 2 · `RingTwist` 3 · `RingRise` 6 · `RingJitter` / `RingJitterFreq` · `RingSegments` 220 |
| Movimiento | `RingFloatScale` 0,05 · `RingWobble` 1 · `RingPhaseSeed` 4 (⚠ se le suma el índice, así los 4 nunca van en fase) |
| Color por anillo | **`RingColors`** (LinearColor[4]) |
| Inclinación y tamaño relativo | transform de los componentes `Ring0..3` (hoy roll/pitch 28/12 · −22/34 · 46/−18 · −38/−30 y escalas 1,0 / 1,18 / 1,36 / 1,54) |
| A qué `Size` están autorados | `RingSizeRef` 0,3 |

✅ **Verificado en PIE tras la migración:** los 4 `ProceduralMeshComponent` presentes, geometría generada (`RVerts` poblado), `DrawIndex = -1`, `RingReveal = [0,0,0,0]`, `RingScaleLast = 1`, y **los 4 MID con su color correcto** (`0.031,0.089,1` · `1,0.066,0.136` · `0.846,0,1` · `1,0.48,0.076`). **Cero actores hijos** en el mundo. Cero `Accessed None`.

### 🚨 "En el BP se ven distintos y en el world todos iguales"
Reporte de Beltrán con la migración ya hecha. **Los componentes nuevos se propagaron a las 5 amebas ya colocadas, pero con la transform de FÁBRICA** (identidad): rotación 0 y escala 1 en los cuatro → los 4 anillos en el mismo plano y del mismo tamaño, indistinguibles. En el CDO estaban perfectos. Es la §164 otra vez, ahora sobre `RelativeRotation` / `RelativeScale3D`.

✅ **Se resolvió recolocando las 5 amebas por última vez**, con la regla que Beltrán fijó: *"deben quedar exactamente como yo los dejo dentro del BP"*. Procedimiento que conviene repetir tal cual:
1. **Volcar las 64 propiedades de cada ameba a un `.json` en `Saved/`** (`AssetTools.write_file`) — no a la memoria del agente.
2. Borrar y recolocar, leyendo el json de vuelta con `open()` dentro del script.
3. **Diffear propiedad por propiedad** y reportar el conteo: salió **64/64 iguales en las cinco**.
💡 Pasar por disco hace la restauración **exacta y auditable**, y funciona aunque el agente pierda contexto entre medio. ⚠ `exec`/`compile` están bloqueados en el sandbox, pero **`open()` funciona**.

⚠ **Lo que NO quedó demostrado:** que un cambio futuro en el BP se propague a las 5. La prueba que corrí (cambiar el pitch del componente en el CDO por MCP y leer la instancia) **dio negativo, pero no es válida**: `set_properties` sobre el archetype no dispara la maquinaria de propagación del editor (`PostEditChangeProperty` + `PropagateDefaultValueChange`), que es la que corre cuando se arrastra el componente en el viewport del Blueprint. **La única prueba válida es hacerlo a mano en el editor y mirar el world.**

### 📏 La escala: `RingRoot` + `ScaleComp`
`Size` sólo escala el `Body`, así que los anillos cuelgan de un `SceneComponent` **`RingRoot`** que toma `Size / RingSizeRef`. 🔴 **No cuelgan del `Body`** aunque ya escale: el `Body` también **gira** con `StepSpin` y los anillos no deben heredar ese giro.
Y como el **WPO se suma en espacio de MUNDO** (después de la escala), achicar el actor no achica el ancho del trazo ni el serpenteo → `PushRingMat` empuja **`ScaleComp = Size / RingSizeRef`** al material, que multiplica todo el WPO. Así el anillo chico es una **miniatura exacta**, no un trazo gordo achicado.

### 🎮 La tecla 6 dibuja el siguiente anillo
`TickRingKey()` cuelga del Tick **fuera de la guarda de `bDebugKeys`** (que está en `false` porque con 5 candidatas las teclas 3/4/5 moverían a las cinco). Tiene su propia llave **`bRingKeys`** (*H - Test*). `RingsShown` lleva la cuenta; cada tecla 6 hace `DrawRing(RingsShown)` y suma uno.
⚠ Es andamio: `bRingKeys` va a `false` cuando la ceremonia tome el control.

## 🐛🔴🔴 `Disappear()` NUNCA fue un estado terminal: se desvanecía y REAPARECÍA (arreglado 2026-08-19)
Reportado por Beltrán en el primer visor del picker: *"las otras se desvanecieron, pero volvieron a aparecer nuevamente en sus target point"*.

**La causa: dos funciones escribiendo la escala del `Body`, y la guarda que las separaba se apagaba sola.**
- `ApplyHoverScale` estaba guardada por `if (not bAppearing)`.
- `StepAppear` corre **mientras** `bAppearing`… y al llegar al final hace **`SetbAppearing false`**.
- Frame siguiente: `bAppearing` es false → `ApplyHoverScale` se destraba y **reescribe la escala a `Size` completo**. La ameba vuelve.

✅ **Arreglo (cirugía de 2 nodos, sin tocar el resto):** la guarda pasa a **`if (not (bAppearing OR bLeaving))`**. La matriz de dueños queda sin huecos:

| `bAppearing` / `bLeaving` | Estado | Quién escribe la escala |
|---|---|---|
| true / false | entrando | `StepAppear` |
| **false / false** | presente | **`ApplyHoverScale`** |
| true / true | saliendo | `StepAppear` |
| **false / true** | **ida** | **nadie** → se queda en 0 ✅ |

🔴 **La lección general: cuando dos funciones escriben la misma propiedad, la guarda no puede depender de un flag que una de ellas apaga.** El bug es invisible mientras la animación corre — aparece **un frame después de terminar**, que es justo cuando uno deja de mirar. Y afecta a **cualquier** camino que use `Disappear`, no sólo al picker: el rig de la tecla 4 tenía el mismo defecto y nadie lo había visto porque no se esperaba a que terminara.
💡 Este BP hereda de `BP_Alma_SC`, que **no** tiene el bug — porque no tiene hover, o sea que no tiene un segundo dueño de la escala. El defecto nació al agregar el hover.

## 🐛 Bug latente detectado (no tocado): `AppearAt` quedó desactualizado
`AppearAt(tag)` sigue leyendo `FoundLoc` / `bFound`, pero el rediseño de puntos hizo que **`FindPoint` ya no escriba `FoundLoc`** — sólo `TargetRef` y `bFound`. O sea que `AppearAt` **teletransporta al (0,0,0)** antes de aparecer. No lo usa nadie hoy (el picker usa `MoveTo`, y el rig de teclas usa la tecla 5), por eso se dejó como está. Al usarlo, cambiar el `SetActorLocation(FoundLoc)` por la posición de `TargetRef`.

## Falta
- Selección por hover + trigger: **construida** en [[BP_SoulPicker_SC]] y verificada en PIE hasta el sembrado; **falta el visor** (el hover necesita manos).
- `SelectSound` sigue en `None` en el CDO → la elección es **muda** hasta que Beltrán ponga el clip.
- ⚠ `bDebugKeys` está en **true** en el CDO: con 5 almas sembradas, las teclas 3/4/5 mueven **a las cinco a la vez**. Apagarlo si estorba al probar el picker.
- Los 4 anillos · el pulso por OSC a 1/2 del ritmo real · persistir la elección.
- El bug de `AppearAt` de arriba, si alguna vez hace falta.

## 🔔 2026-08-19 — avisos para el guión: `OnArrived`, `OnRingDone`, `EnableHover`
Para que [[BP_Director_Story]] pueda encadenar "llega a la cara → VO" y "anillo completo → vuelve a la cara":
- **`OnArrived`** (dispatcher): `MoveTo` ahora arma `bArriveArmed`; `TrackTarget` llama `CheckArrive()` cada tick y, cuando la distancia al `TargetRef` baja de **`ArriveDist`** (6 cm, cat. *G - Recorrido*), dispara una sola vez (`PROTO: llegue al punto`). Como `VInterpTo` es asintótico, "llegar" se define por umbral — 6 cm es invisible y llega ~1 s después de arrancar en distancias cortas.
- **`OnRingDone`** (dispatcher): `StepRings`, al clavar `DrawIndex=-1` (el anillo llegó a 1,05), lo dispara.
- **`EnableHover(On)`**: escribe `bHoverEnabled` desde afuera (el picker lo usa en `Rearm`, para el final de la obra).
🔴 **`Default|CallOnArrived` en el DSL resolvió al `OnArrived` de `BP_Director_Movement`** (mismo nombre de dispatcher): el compile dijo *"self is not a BP_Director_Movement_C"*. Se borró el nodo y se creó con `create_node(declaring_class=BP_ProtoSoul_SC_C)`.
⚠ `ArriveDist` se escribió **en las 5 instancias** (variable nueva en BP ya colocado = nace en 0 → con 0 nunca "llegaría").

## 🤲 2026-08-20 — clamp del lazy follow + el sistema de AGARRE para compartir
Pedidos de Beltrán tras el primer run completo en editor:
- **`MaxLag`** (cat. *G - Recorrido*, 20 cm, en CDO y las 5 instancias): `TrackTarget` termina en `ClampLag()` — si el `VInterpTo` quedó a más de `MaxLag` del target, se recoloca a exactamente `MaxLag` sobre la línea al target. El lazy follow conserva su elástico pero **nunca se queda atrás en las caminatas** (el síntoma: la ameba de la cara quedaba rezagada al cambiar de sala). `MaxLag = 0` lo desactiva (por eso las instancias se escribieron explícitas, §146: nacer en 0 lo apagaría).
- **Agarre** (cat. *J - Compartir*: `CarrySpeed` 14 · `ShareRadius` 30 · `ShareDown` 25, en CDO e instancias): `StartCarry(Right)` / `EndCarry()` / `StepCarry(DT)` (en el Tick) → mientras `bCarried`, el actor sigue el **grip de la mano que agarró** (`VInterpTo` a `CarrySpeed`) y `TrackTarget` queda gateado (`StepTravel` chequea `not bCarried`) → **al soltar vuelve solo a su TargetPoint**. Cada tick compara la distancia al punto **`ShareDown` cm bajo el HMD** (`GetPlayerCameraManager(0)` = la pose de la cabeza): dentro de `ShareRadius` → **`Shared()`**: corta el carry, apaga el hover, loguea y dispara **`OnShared`** (dispatcher). `Shared()` es público (lo usa el `ForceShare` de test del picker).

## 📉 2026-08-20 (2ª tanda) — viaje EASE + anclaje duro + achique al agarrar
- 🔴 **Se fue el `VInterpTo` del seguimiento**: `TrackTarget` ahora ramifica — **viajando** (`bTraveling`): lerp `TravelFrom→target` con **smootherstep** en **`TravelTime`** s (4; la perilla del "lento y easy" que pidió Beltrán), persiguiendo el transform ACTUAL del target (converge aunque se mueva); **anclada**: copia posición/rotación/tamaño del target **exactos cada frame** — cero lazy follow, imposible rezagarse en las caminatas (`MaxLag`/`ClampLag`/`CheckArrive` quedaron obsoletos, ya nadie los llama). `StartTravel()` arma el viaje (lo llaman `MoveTo` y `EndCarry`); `ArriveNow` dispara `OnArrived` al llegar (t=1).\n- **Achique al agarrar**: `StartCarry` fija `CarryTargetSize = Size × CarryShrink` (**0,5**, cat. *J - Compartir*, editable) y `CarryBody` interpola `Size` hacia eso (suave, interp 4). Al soltar o compartir, el viaje de vuelta restaura el tamaño del TargetPoint (viene en el lerp de `TravelStep`).\n- 🔴 Gotcha nuevo aplicado: el `FindPoint` PROPIO se escribe `CallFunction|FindPoint` — el read lo etiqueta `Class|BPAlmaSC|FindPoint` y escribir eso crea una llamada a la clase de Alma sin target (§115 del read mentiroso, ahora en su variante write).

## 🕐 2026-08-21 — ARREGLADO el bug histórico: el material se degradaba con el tiempo
Beltrán venía reportando hace semanas que *"un material animado se va glitcheando poco a poco a lo largo de la experiencia"*. Al final del recorrido veía la ameba **pixelada y moviéndose a muy bajos frames — sólo el material**. **Causa encontrada y medida**: `M_ProtoSoul` (y `M_Alma`) tenían `floatPrecisionMode = MFPM_Default` (fp16 en móvil) y el nodo `Time` **sin período**, así que tras ~15 min el tiempo era demasiado grande para la precisión disponible: los senos del WPO y del gradiente avanzaban a saltos y los degradados se cuantizaban. ✅ **Fix: precisión Full + `Time.period = 300`** (lo que `M_SoulRibbon_SC` ya tenía, y por eso los anillos nunca fallaron). Detalle en `gotchas.md` §185.
