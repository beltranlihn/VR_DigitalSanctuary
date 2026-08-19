# BP_Alma_SC — la guía de la obra (Core/Alma/)

## Purpose
**Alma es quien guía la experiencia**: nos recibe, nos acompaña etapa por etapa y habla por voice over. Una esfera-ameba translúcida que flota en el aire, aparece y desaparece en puntos del mundo, y viaja suavemente entre ellos.

Pedido de Beltrán (2026-08-18): *"Alma será quien guía la experiencia con voice over, nos recibe y nos acompaña en cada etapa."*

🔴 **Es la versión LIMPIA de `Core/Amoeba/BP_Alma`** (el placeholder viejo: esfera unlit cálida de 35 cm con `M_ProtoSoul`). El viejo queda intacto en `L_Persistent` como referencia.

## Status
🟢 **Verificado en PIE por Beltrán (2026-08-18)**: material, flotar, aparición, desaparición, viaje entre puntos y el rig de teclas. Compila limpio.
⬜ Falta: voice over (array de clips + memoria de en cuál iba), audio de entrada/salida, reactividad al VO, y avisos a otros BPs al terminar un clip.

## Los assets
| Asset | Qué es |
|---|---|
| `SM_AlmaSphere` | 🔴 **Icoesfera generada, NO la esfera del motor.** 5.120 tris / 2.665 verts, radio 50. La de Unreal (`/Engine/BasicShapes/Sphere`) son 960 tris **con los polos pinchados**: al deformarla se le ven las facetas y los polos. La icoesfera tiene triángulos uniformes y sin polos, que es la malla correcta para un blob. Se generó como `.obj` por script y se importó. |
| `M_Alma` | El material. Unlit · Translucent · **one-sided** · sin reflejos ni refracción. |
| `BP_Alma_SC` | El actor: un `StaticMeshComponent` `Body` + todo lo de abajo. |

## 🔴 El material: por qué NO usa el nodo `Noise`
Beltrán pidió *"algo como cuando uno le pone noise a un sphere en touchdesigner"*. **El nodo `Noise` se descartó con los números de Epic**, no por corazonada:

| Función del nodo Noise | Costo (por octava) |
|---|---|
| Fast Gradient (3D Texture) | ~16 instr. **+ 1 lectura de textura** |
| Gradient (Texture) | ~61-74 instr. + **8 lecturas** |
| Value (Computacional) | ~53 instr. |
| Gradient (Computacional) | ~80 instr. |
> — [Utility Material Expressions](https://dev.epicgames.com/documentation/en-us/unreal-engine/utility-material-expressions-in-unreal-engine)

En el vertex shader de Quest eso no se paga. **La solución es suma de senos**: mismo look orgánico, ~20 instrucciones, **cero texturas**.

### 🔑 El truco que hace que se vea aleatorio: relaciones NO enteras
Todas las capas usan senos cuyas frecuencias están en proporciones irracionales (1 : 1.37 : 0.73 · 0.61 : 0.83 : 1.19 · 1.0 : 1.7 : 2.3). **Si fueran múltiplos enteros se alinearían y se vería el eje**; al no serlo, el patrón nunca se repite de forma perceptible. Es determinista, suave, sin estado y sin generar un solo número al azar.

### Las cinco capas del material
1. **Deformación (WPO)** — 3 senos sobre la posición local, desplazando por la normal. `WobbleAmount` es **fracción del `ObjectRadius`**, no centímetros: así se puede escalar a Alma sin que la deformación se descontrole.
2. **Superficie** — `Fresnel(FresnelPower)` interpola `CoreColor` → `RimColor`, y también la opacidad `OpacityCore` → `OpacityRim`. El centro casi transparente con el borde encendido es lo que lee como burbuja hueca.
3. **Gradiente** — segunda suma de senos, independiente, más lenta y de manchas más grandes que los bultos (para que se lean como dos capas). Interpola `GradColorA` → `GradColorB` y se mezcla sobre el color base con `GradAmount`.
4. **Borde** — 🔴 **un SEGUNDO Fresnel, mucho más angosto** (`EdgePower` ~8 contra 3 del ancho). Da la idea de reflejo especular **sin una sola reflexión** — cero cubemaps, cero SSR, que es justo lo que no funciona en Quest.
5. **Flotar (WPO)** — deriva de posición + rotación por **producto cruz** entre el vector de giro y la posición relativa al centro (para ángulos chicos, eso *es* una rotación, y cuesta un nodo).

## 🔴🔴 El borde salía SIEMPRE BLANCO: era una suma, no el color
El filo se **sumaba** encima de un emisivo ya cerca de 1 en los tres canales → todo pasaba de 1 y **clipeaba a blanco**, sin importar qué color se eligiera. **Arreglo: pasarlo a interpolación** (`lerp(base, EdgeColor, Fresnel)`), y bajar `EdgeIntensity` a 1.0 (a 1.2 el color ×1.2 volvía a clipear).
👉 **Regla general:** en móvil, sin HDR ni bloom, **no existe "azul más brillante que el blanco"**. Para un color saturado y brillante hay que usar un color con al menos un canal BAJO y dejar la intensidad en 1.

## 🔴🔴 "Se ve cuadriculada": era la translucidez a DOS CARAS
Síntoma de Beltrán: *"a veces se ve la textura como cuadriculada o pixelada"* — parches con forma de triángulo y bordes rectos, intermitentes según el ángulo.

**No era la malla ni la textura.** Unreal ordena la translucidez **por objeto, no por triángulo**: dentro de una misma malla los triángulos translúcidos se dibujan en **orden de índice**, no de profundidad. Con `TwoSided` + opacidad baja se ven las dos superficies mezcladas y **cuál gana depende del índice**, no de qué esté más cerca. Por eso los parches son triangulares y aparecen/desaparecen al orbitar.

✅ **Arreglo: `TwoSided = false`.** Y de yapa **corta a la mitad los píxeles translúcidos**, que en Quest es lo caro (Meta mide ~80 % más de GPU por frame en translúcido vs masked).
⚠ `Two Sided` es **estático**: no puede ser un parámetro del material instance, cambiarla obliga a recompilar el shader.

## 🔴 El flotar vive en el MATERIAL, no en el Tick
Beltrán preguntó si se podía ver en el editor. **El Construction Script no puede animar** (corre al cambiar una propiedad, no cuadro a cuadro) y **Blueprint puro no puede tickear en el editor sin C++**. Pero **el nodo `Time` de un material SÍ anima en el viewport**.

Se movió la deriva y el giro al WPO. Resultado: **el BP quedó sin Tick para el flotar**, se ve en el editor sin darle Play, y pasó de ~30 nodos por frame en el game thread a ~25 instrucciones de vertex shader.

⚠ **El precio, y hay que tenerlo presente:** el **actor ya no se mueve, sólo su dibujo**. Si algo necesita la posición real de Alma (un sonido que deba bambolearse con ella, una distancia contra su superficie) va a leer el centro quieto. Para VO y para todo lo planeado da igual (son 4-6 cm).
🔴 **Y obliga a subir `Bounds Scale`** (está en **1.6**): el motor calcula el culling con los bounds ORIGINALES, así que sin esto Alma desaparece de golpe al mirarla de reojo cuando la deriva la saca de su caja. Error clásico y silencioso de WPO.

## Registro de variables
Todas instance-editable salvo el grupo Z, y **todas se empujan al material dinámico desde el Construction Script** → se ven en el viewport al instante.

| Grupo | Variables |
|---|---|
| **0 - Cuerpo** | `Size` (0.4) — diámetro en metros. Se aplica **primero** en el CS, antes de crear el MID, para que `ObjectRadius` ya sea el nuevo y la deformación nazca proporcional. |
| **A - Deformacion** | `WobbleAmount` (0.12, fracción del radio) · `WobbleFreq` (0.06) · `WobbleSpeed` (0.8) |
| **B - Superficie** | `CoreColor` · `RimColor` · `FresnelPower` (3) · `Brightness` (1.5) · `OpacityCore` (0.12) · `OpacityRim` (0.85) |
| **C - Gradiente** | `GradColorA` · `GradColorB` · `GradAmount` (0.5) · `GradFreq` (0.04) · `GradSpeed` (0.25) |
| **D - Borde** | `EdgeColor` · `EdgePower` (8) · `EdgeIntensity` (1.0) |
| **E - Flotar** | `FloatAmount` (4,4,6 cm) · `FloatSpeed` (0.35) · `RotAmount` (P5,Y8,R5 **grados**) · `RotSpeed` (0.25) · `PhaseSeed` (0) |
| **F - Aparicion** | `AppearTime` (1.2 s) · `DisappearTime` (0.6 s) |
| **G - Recorrido** | `TravelTime` (3 s) |
| **H - Test** | `bDebugKeys` (true) · `DebugPoints` (array de tags que cicla) |
| **Z - Estado interno** | `MID` · `AppearT` · `bAppearing` · `bLeaving` · `bTraveling` · `TravelT` · `TravelFrom` · `TravelTo` · `FoundLoc` · `bFound` · `NextTag` · `DebugIndex` |

💡 **`PhaseSeed` es para cuando haya más de una Alma**: corre el punto de partida de las seis ondas, así dos actores nunca se sincronizan.

## 🗺️ El sistema de puntos: UN registro, DOS verbos
Beltrán planteó *"dos sistemas: uno de aparición y otro de movilización"*. **Se armó como uno solo**, y la razón importa: un punto de aparición y uno de movilización son **el mismo dato** (un destino con nombre); lo que cambia es cómo se llega. Separarlos habría duplicado el registro y obligado a decidir de antemano el rol de cada punto. Así **cualquier TargetPoint sirve para las dos cosas**.

| API pública | Qué hace |
|---|---|
| **`AppearAt(PointTag)`** | Busca el TargetPoint con ese tag, **se teletransporta** y corre la entrada. Cancela cualquier viaje en curso. |
| **`MoveTo(PointTag)`** | **Viaja suave** desde donde esté, en `TravelTime`, con `EaseInOut`. |
| **`Disappear()`** | Evento (sin parámetros): encoge a 0 en `DisappearTime`, **desde donde esté** — si se llama a mitad de la entrada, se da vuelta sin saltos. |

Los puntos se identifican por **actor tag sobre `TargetPoint`**, el mismo patrón que [[BP_SoulChoice]], [[BP_Ceremony]] y [[BP_Bell]]. Se coloca el punto en el viewport, se le escribe el tag, y **no se toca ningún Blueprint**.

🔴 **NO hay spawn ni destroy** — decisión explícita. Una sola Alma que se teletransporta y aparece/desaparece es más simple, y **regala la memoria del voice over**: es el mismo actor, la variable nunca se pierde. Spawnear traería de vuelta toda la clase de bugs de instancias que nacen en cero.

💡 **El "viaje invisible" que Beltrán imaginaba como paso aparte no hace falta**: al desaparecer queda en escala 0, así que el teleport es inobservable y ocurre en el instante en que se llama a `AppearAt`. Los dos tiempos que le importaban (cuándo se va, cuándo vuelve) ya son dos llamadas distintas.

⚠ **Límite real:** `GetAllActorsOfClassWithTag` **sólo ve lo que está cargado**. Un TargetPoint dentro de un sublevel no existe hasta que ese sublevel se carga. Si hace falta llamar `AppearAt` antes de que la sala cargue, el punto tiene que estar en el **persistente**.
✅ Si el tag no existe **no hace nada y lo dice en el log** — la alternativa era teletransportarse al origen del mundo, que es el fallo silencioso clásico.

## Estructura de grafos
- `BeginPlay` → `Appear`.
- `Tick` → `StepAppear(DT)` → `StepTravel(DT)` → `TickDebugKeys()`.
- **`Appear`** (evento) — apaga `bLeaving`, `AppearT`=0, escala 0, arranca.
- **`Disappear`** (evento) — prende `bLeaving`, arranca. No resetea `AppearT`.
- **`StepAppear(DT)`** — 🔴 **bidireccional**: un solo `AppearT` y una sola curva sirven para entrada y salida; dos `Select` eligen el destino (1 ó 0) y el tiempo (`AppearTime` ó `DisappearTime`). Escala hacia `Size`, no hacia 1.
- **`FindPoint(Tag)`** — busca y **escribe `FoundLoc`/`bFound`**; no devuelve.
- **`AppearAt(Tag)` / `MoveTo(Tag)`** — leen esas variables.
- **`StepTravel(DT)`** — interpola `TravelFrom`→`TravelTo` con `Ease`.
- **`NextPoint()` / `TickDebugKeys()`** — el rig de test.

🔴 **`FindPoint` y `NextPoint` NO devuelven valor, escriben variables.** Es deliberado: una función propia usada como **expresión** no cablea su exec, el compilador **la poda** y devuelve el default (gotcha §125, el bug que costó una mañana en [[BP_Bell]]).
🔴 **`FInterpTo Constant`, no `FInterpTo`**, en las tres animaciones: el asintótico nunca llega al destino y su "speed" no es una duración. Con el constante, 1.2 son exactamente 1,2 s y el valor aterriza **exacto**, que es lo que permite apagarse con una comparación de igualdad.

## 🎮 Rig de test por teclado
| Tecla | Acción |
|---|---|
| **3** | `MoveTo` al siguiente punto de `DebugPoints` (visible) |
| **4** | `Disappear` |
| **5** | `AppearAt` el siguiente punto (teleport invisible + entrada) |

Usa 3-4-5 porque **1 y 2 ya son del director de salas y del recorrido**. `bDebugKeys` en false lo apaga entero.

🔴🔴 **NO funciona en Simulate — hay que usar Play.** Verificado midiendo el mundo de PIE: en Simulate `Tick` y `BeginPlay` **sí corren** (`AppearT` llegó a 1 y la escala creció), y hasta **existe** un `PlayerController_0` con su `SpectatorPawn_0`. Lo que no pasa es el input: **el teclado lo consume el viewport del editor** para la cámara libre y no se enruta al stack del PlayerController, así que `WasInputKeyJustPressed` devuelve false siempre. Es el mismo mecanismo de las teclas 1 y 2, que también piden Play.

## TODO
- [ ] Array de clips de VO + memoria de en cuál iba (fácil: el actor nunca se destruye).
- [ ] Audio de entrada y salida enganchado a `Appear`/`Disappear`.
- [ ] Reactividad al VO (escala, material o Niagara) — Beltrán lo dejó para el final.
- [ ] Avisos a otros BPs al terminar ciertos clips (dispatcher; aún sin definir cuáles).
- [ ] Evaluar leer también **rotación y escala** del TargetPoint (hoy sólo posición) — sería la palanca para agrandar a Alma en un punto concreto.

## Relacionados
- [[BP_Bell]] — de ahí salen `FInterpTo Constant` y la regla del nodo podado · [[BP_Director_Rooms]] — quien carga las salas donde Alma aparece · [[BP_ProtoSoul]] — la OTRA ameba (la del usuario), no confundir.
