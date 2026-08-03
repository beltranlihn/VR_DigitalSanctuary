# Stage Movement — "Surrounding" (etapa de dibujo 3D) · brief + plan de construcción

> Fuente autoritativa de la mecánica y del **orden de construcción**. Consolida y **supera** el research disperso: `.claude/skills/unreal-vr/references/movement-3d-drawing.md` (los 4 proyectos analizados + el algoritmo `PincelA_AddPoint`) y la §4.5 del `Soul-Charger-Design.md`.
> Antes de tocar: materiales/color → `materials-vr.md` · input → `input.md` + `motion-controller-data.md` · filtros de señal → `motion-detection-thresholds.md` · widgets → `widgets-vr.md` · audio → `audio-quest.md` · construcción de grafos → `bp-lean-construction.md` + `dsl.md`.

Carpeta: `VR_Test/Content/SoulCharger/Stages/Movement/` · Nivel: `Maps/Tests/L_Test_Movement` (duplicar de `L_Test_Breath` para heredar pawn + fade). Color de etapa: **verde**. Rama: `stage/movement`.

---

## 1. La mecánica (qué construimos)

El usuario está sentado en el vacío oscuro. **Toma el pincel** que aparece frente a él — con la mano que prefiera, y esa elección define todo lo demás: esa mano dibuja, en la otra le aparece la paleta. **Aprieta el gatillo y dibuja luz en el aire, a su alrededor.** No hay consigna, ni figura a copiar, ni puntaje.

**El ancho lo decide la mano** (la presión del gatillo, como en Open Brush) **y la calma decide la luz:**
- Movimiento **brusco** → el trazo se apaga y el color se enfría.
- Movimiento **suave y sostenido** → el trazo se enciende.

**La calma se vuelve bella, no puntuada.** La herramienta está diseñada para que **no exista el trazo feo**: el suavizado de la punta, el afinado de tres tiempos y la cinta cuya cara sigue el trazo garantizan que cualquier cosa que dibuje se vea bien.

**Flujo del stage (formato Breath):** negro → fade in → widget de instrucciones (páginas, la última con gate de acción) → aparece el pincel y arranca la experiencia → **~2 minutos de dibujo libre** → se guarda el dibujo → fade a negro → reinicia el nivel.

*(A futuro, fuera de este hito: en vez de reiniciar, el dibujo **colapsa y se miniaturiza hacia adentro de la ameba** y queda como escultura interior. Toda la arquitectura de abajo está pensada para que eso sea un solo `SetActorScale` + un `SaveGame` ya escrito.)*

## 2. Decisiones cerradas (no re-preguntar)

| # | Decisión | Detalle |
|---|---|---|
| D1 | **Cierre por timer de ~2 min** | El design doc ya lo fija ("más allá hay demasiados trazos"). El manager arranca el reloj al terminar las instrucciones y cierra solo. Sin UI de "listo", sin decisión para el usuario. |
| D2 | **Paleta de 9 celdas (3 color · 3 grosor · 3 pincel)** | 🔄 **Actualizado 2026-07-30.** Todo se elige tocando una paleta plana en la mano no hábil (§5.3): 3 colores fijos (sin picker HSV), 3 grosores discretos, 3 pinceles. El color lo define la celda elegida; la calma **no** toca el color (ver D10). |
| D3 | **Persistencia desde el día 1** | El modelo de datos (`F_Stroke`/`F_StrokePoint`) define cómo se escribe el motor de geometría. Se construye ahora, no después. |
| D4 | **`r.MobileHDR=True`** | Se activa (Fase 0.5). Devuelve tonemapper filmico + bloom + color grading por ~600 µs de 13.9 ms. Es la palanca #1 para que los trazos emisivos se vean bien. ⚠ Config **compartido** → avisar al otro dev, rebuild de shaders, revisar cómo quedan Breath/Heart. |
| D5 | **Procedural Mesh, NO Niagara** | Confirmado en el research: partículas = geometría efímera en GPU, no serializable → no cumple el requisito duro de guardar el dibujo por usuario. |
| D6 | **El pincel es un prop que se toma, y esa toma define la mano hábil** | Patrón idéntico al sensor de Breath y de Calibration: el pincel se spawnea en un `TargetPoint` durante las instrucciones y **se auto-adjunta por proximidad** a la mano que lo toca (sin botón de grab). Esa mano dibuja; **la paleta aparece en la otra** (§5.0). Zurdos y diestros quedan resueltos sin preguntar nada. |
| D7 | **Un solo actor lienzo, no un actor por trazo** | 🔴 Cambio respecto del proyecto de referencia. Ver §4. |
| D8 | **Umbral de calma absoluto, no calibrado** | Regla del proyecto (design §2): el umbral **es la instrucción**. Se afina una vez en visor y queda igual para todos. |
| D9 | **Cinta plana, no tubo** | La cara de la cinta **sigue el trazo** vía frame por transporte paralelo (§4.3), con espesor mínimo para que de canto sea un filamento y no un plano de área cero. |
| D10 | **El ancho lo decide el usuario, DISCRETO desde la paleta** | 🔄 **Actualizado 2026-07-30: la presión del gatillo se descartó** (no confiable). El ancho es uno de **3 grosores fijos** elegidos en la paleta (× taper de tres tiempos). La **calma modula un parámetro del MATERIAL** (emissive/luz por el alpha del vértice), nunca el ancho. |

## 3. Arquitectura de Blueprints (1 responsabilidad por BP, pawn liviano)

| BP / Asset | Responsabilidad |
|---|---|
| **`BP_DrawCanvas`** | **El motor de geometría.** Dueño del `ProceduralMeshComponent` y de los datos del dibujo. API: `BeginStroke(brushId, color)` · `AddPoint(loc, up, width, calm)` · `EndStroke()` · `SerializeToSave()` / `RebuildFromSave()`. No sabe nada de input ni de mandos. |
| **`BP_BrushTool`** | **La herramienta.** Prop agarrable que se **auto-adjunta por proximidad** a la mano que lo toca (§5.0) y queda dueño de `AttachedController` / `bIsRightHand`. Lee el gatillo de **su** mano, calcula la **métrica de calma**, decide **cuándo** emitir un punto (decimación) y con qué ancho/color, y se lo pasa al canvas. Dueño del audio y el háptico del pincel. |
| **`BP_BrushPalette`** | **La paleta**, sobre la **mano no hábil** (la que quedó libre, se decide en runtime — §5.0). Aparece al girar la muñeca hacia uno. Dos controles que se tocan con la punta del pincel: **arco de tamaño** (define el ancho máximo) y **celdas de pincel** (2-4 presets). Muestra un preview vivo del trazo resultante. Mientras la punta está sobre la paleta, **suprime el dibujo**. |
| **`DA_Brush`** (DataAsset) | Un asset por pincel: material · tipo de sección (cinta con espesor / cinta pura / estampado) · **ancho base y curva de presión** · peso del roll de muñeca (0-1) · colores apagado/luminoso para el gradiente de calma · **modo de UV (Tile / Stretch)** y escala de textura · velocidad del panner · sonido. **Agregar un pincel = crear un DataAsset, no tocar código.** |
| **`BP_MovementInstructions`** + **`WBP_MovementInstructions`** | Máquina de páginas world-space (patrón Breath, fondo verde). La última página **gatea con acción**: no avanza hasta que el usuario dibuje un trazo suave. Spawnea `BP_BrushTool` y `BP_DrawCanvas`. |
| **`BP_MovementStageManager`** | Cierre: arranca el timer de 2 min al terminar las instrucciones, al vencer manda guardar, apaga el pincel, funde a negro y reinicia el nivel. Patrón calcado de `BP_BreathStageManager`. |
| **`SG_Drawing`** (SaveGame) | Persistencia: `array<F_Stroke>` + metadata de usuario/versión. Patrón de `Calibration/SG_CalibSession`. |
| **`F_Stroke`** / **`F_StrokePoint`** (structs) | El modelo de datos. Ver §6. |
| **`M_Brush_Light`** / **`M_Brush_Ribbon`** / **`M_Brush_Dust`** | Los tres materiales de pincel. Ver §7. |
| **`IA_Draw_Left`** / **`IA_Draw_Right`** / **`IMC_Movement`** | Input propio del stage, en `Stages/Movement/Input/`. 🔴 **Axis1D** (presión analógica), no Digital. **Dos acciones, una por mano** (mismo patrón que `IA_Shoot_Left/Right`): el pincel consume solo la de su mano según `bIsRightHand`. **No hace falta un `IA_BrushCycle`**: el mismo gatillo, cuando la punta está sobre la paleta, opera la paleta en vez de dibujar. |

## 4. 🔴 El motor de geometría — decisiones que definen la calidad

Esta sección es el corazón del stage. El algoritmo de referencia (`PincelA_AddPoint`, extraído del TiltBrush propio) queda como base conceptual, con **seis cambios deliberados** que lo mejoran.

### 4.1 Un actor lienzo con secciones, no un actor por trazo
El proyecto de referencia spawneaba **un actor por trazo**. Se cambia a **un solo `BP_DrawCanvas`** con un `ProceduralMeshComponent` y **secciones** dentro. Razones:
1. **Miniaturizar el dibujo entero** (el requisito narrativo: colapsa dentro de la ameba) es un `SetActorScale3D` sobre un actor, no un baile de 100 attachments.
2. **Persistencia trivial**: los datos ya viven todos en un lugar.
3. Menos overhead de actor/componente y de culling.

**Sección activa vs secciones selladas:** la sección del trazo en curso se **pre-aloca** y se actualiza; al soltar el gatillo se **sella**. Objetivo de perf: agrupar trazos sellados por familia de pincel en pocas secciones (§9), para terminar con **≤4 draw calls de dibujo**.

### 4.2 Pre-alocar + `UpdateMeshSection`, no `CreateMeshSection` por punto
El original llamaba `CreateMeshSection` completo en **cada punto** → recrea el recurso de render del trazo entero, cada vez. Se reemplaza por:

1. Al empezar el trazo: `CreateMeshSection` **una vez** con capacidad para **128 puntos**, todos los vértices colapsados en el punto inicial y **la lista de triángulos ya construida**.

   🔴 **Corregido al implementarlo (2026-07-29): colapsar en el punto inicial NO alcanza.** El segmento entre el último anillo real y el primero sin escribir queda como un **cono visible** que apunta al inicio del trazo (o al origen del mundo, si los anillos quedaron en `(0,0,0)` tras un `Resize`). Lo que sí funciona: **un anillo con sus 4 vértices idénticos tiene ancho cero, y el segmento entre dos anillos así es de área cero por lejos que estén.** Entonces, además del colapso inicial, cada punto nuevo **colapsa el anillo siguiente en su propia posición** — el cono se degrada a la tapa del trazo (área ≈ ancho × espesor, invisible) y todo lo que viene después no dibuja. Cuesta 4 `SetArrayElem` extra por punto, en vez de recorrer la cola entera. Detalle en el tracker de `BP_DrawCanvas`.
2. Cada punto nuevo: escribir solo sus vértices en los índices que le tocan y llamar **`UpdateMeshSection`** (la variante **sin triángulos** — el índice buffer no cambia nunca).
3. Al agotar la capacidad: sellar la sección y abrir otra continuando desde el último punto (el trazo se ve continuo).

**Por qué 128 y no 1000:** `UpdateMeshSection` recibe los arrays completos por valor → sube todo el buffer de la sección cada vez. Con capacidad chica el costo por actualización queda acotado. Y como la **decimación** gatea las actualizaciones (§4.4), a velocidad de dibujo normal esto corre ~7 veces por segundo, no 72.

> ⚠ Verificar con el MCP los nombres/pines exactos de los nodos de PMC en 5.8 antes de construir (`Create Mesh Section`, `Update Mesh Section`, `Set Material`, `Clear All Mesh Sections`) y **agregarlos a `references/nodes.md`** — hoy no están en el catálogo verificado. El plugin **Procedural Mesh Component está habilitado por defecto** en UE 5.8 (verificado en su `.uplugin`), no hace falta tocar el `.uproject`.

### 4.3 🔴 Cinta plana cuya cara sigue el trazo (frame por transporte paralelo)
**Decisión: cinta plana, no tubo.** La cara de la cinta **sigue el trazo** y se retuerce con él — eso le da la cualidad escultórica en 3D, y además hace que el ancho modulado por la calma **se lea mucho mejor** que en un tubo (el tubo esconde el grosor; la cara plana lo muestra).

**El problema real del original no era ser plana: era de dónde sacaba la orientación.** Usaba el *up* del mando como referencia (`side = cross(dir, controllerUp)`). Eso **degenera** cuando la dirección del trazo se alinea con el up del mando: el producto cruz tiende a cero y la cinta gira sobre sí misma sin control. Es lo que produce los retorcimientos feos y aleatorios.

**Solución: frame por transporte paralelo** (*rotation-minimizing frame*, la técnica estándar para geometría a lo largo de una curva). Cada punto **hereda el frame del punto anterior**, rotado exactamente por el mismo giro que sufrió la dirección del trazo:

```
axis  = cross(dirPrev, dirNew)
if |axis| ≈ 0          → Up se mantiene igual (tramo recto)
else                   → Up = RotateAngleAxis(Up, ánguloEntre(dirPrev,dirNew), normalize(axis))
Side  = cross(dirNew, Up)
```
La cinta se retuerce **siguiendo la curva, de forma suave y continua, sin flips**. No usar el frame de Frenet (basado en curvatura): en los tramos rectos la curvatura es cero y el frame se vuelve loco.

🔴 **Implementado con 2 nodos y sin trigonometría (2026-07-29):** `GetUpVector(MakeRotFromXZ(dirNueva, UpAnterior))`. `MakeRotFromXZ` arma la base ortonormal con X = dirección y Z lo más cerca posible del up dado — que **es** exactamente la ortogonalización de Gram-Schmidt (el método de proyección del rotation-minimizing frame), con su propio fallback para el caso paralelo. Reemplaza al `Cross`+`Acos`+`RotateAngleAxis`+guard de arriba, y la **siembra** del frame es la misma expresión pasándole el up del mando. Bonus obligado: `Math|Trig|Acos(Degrees)` tiene paréntesis en el `type_id` y el parser del DSL no lo acepta, así que la versión con ángulo explícito no era escribible igual.

**La muñeca aporta un delta de roll, no el frame entero.** Se mide cuánto rotó el mando alrededor de su propio eje entre punto y punto y se aplica como rotación adicional de `Up` **alrededor de `dir`**, con un peso configurable en el `DA_Brush` (0 = la cinta solo sigue el trazo · 1 = control calígrafico total). Así se conserva la expresividad de girar la muñeca **sin heredar la degeneración**.

**Espesor mínimo, no plano de área cero.** Sección rectangular achatada: **4 vértices por punto**, `espesor = max(ancho × 0.12, 0.08 cm)`. Mantiene el carácter completamente plano, pero evita que visto de canto sea un plano de área nula, que **titila con MSAA**. Visto de canto se lee como un **filamento brillante** — con el material adecuado (§7) eso es una virtud del pincel, no un defecto a esconder: la cinta pasa de velo ancho a hilo de luz según cómo la mires.

**Normales:** hacia afuera desde el eje de la cinta (no `dir`, como hacía el original — con `dir` el Fresnel del material no funciona y el canto no brilla).

*Variante disponible si se quiere planitud absoluta:* 2 vértices por punto y material Two Sided. Se pierde el filamento del canto y aparece el titileo. Queda como opción del `DA_Brush`, no como default.

**Curvas cerradas:** la decimación por ángulo (§4.4) evita que la cinta se pellizque en un giro brusco. Si aparece el pellizco, bajar `MaxAngle`.

### 4.4 Decimación por distancia **y** por ángulo
El original decimaba solo por distancia (`MinDistance`). Con eso, las curvas rápidas salen facetadas y las rectas largas gastan vértices de más. Se agrega el criterio angular:

```
emitirPunto = (distancia(nuevo, último) > MinDist)  OR  (ángulo(dirNueva, dirÚltima) > MaxAngle)
```
Arranque: `MinDist ≈ 1.5 cm`, `MaxAngle ≈ 10°`. Es práctica estándar de ribbon brushes y es lo que hace que una curva cerrada se vea curva sin inflar el conteo de vértices en las rectas.

### 4.5 Suavizado de la punta con One-Euro (aquí sí sirve)
El jitter del tracking y el temblor de la mano se ven **directamente** en la geometría. Se filtra la posición de la punta **antes** de emitir puntos con un **One-Euro Filter** (Casiez et al., CHI 2012 — fórmulas verificadas en `motion-detection-thresholds.md`).

🔴 Nota importante: en el detector de **respiración** descartamos One-Euro porque su diseño (seguir más rápido cuanto más rápido se mueve el sensor) era exactamente lo contrario de lo que necesitábamos. **Aquí es exactamente lo que queremos**: filtrar fuerte el temblor cuando la mano está casi quieta, y no meter lag cuando el usuario hace un trazo rápido a propósito. Es su caso de uso de diseño original (un puntero).

Arranque: `mincutoff ≈ 1.0 Hz`, `beta ≈ 0.007`, `dcutoff = 1.0`. Se afinan en visor: bajar `mincutoff` quita más temblor; subir `beta` quita lag.

### 4.6 🔴 Taper de tres tiempos — el gesto de Open Brush
El comportamiento a replicar: **el trazo nace delgado, se ensancha a medida que se dibuja, y termina delgado.** No es un detalle cosmético — es lo que hace que un trazo se lea como un gesto y no como un cable cortado con tijera.

Son **tres rampas distintas**, todas en la geometría (el original lo simulaba con un parámetro de material `ShrinkAmount`; hacerlo en la geometría es más barato, más robusto y funciona igual en los tres pinceles):

1. **Entrada** — los primeros ~3 cm del trazo suben de 0 al ancho pedido.
2. **Punta viva** — mientras se dibuja, los **últimos ~3 cm siempre están afinados**: la punta que avanza es siempre fina. Y cuando el usuario sigue avanzando, **esa punta se reabsorbe y engorda al ancho pleno** al quedar atrás. Ese "el trazo se va ensanchando detrás de la punta" es exactamente la sensación de Open Brush.
3. **Salida** — al soltar el gatillo, la rampa final se congela: los últimos ~3 cm quedan afinados de forma definitiva.

🔴 **Por qué esto es gratis en nuestro diseño:** la sección está **pre-alocada** y `UpdateMeshSection` sube el buffer completo igual (§4.2) → **reescribir los últimos K puntos en cada actualización no cuesta nada extra**. La punta viva es literalmente recalcular el ancho de esos K vértices que ya se estaban subiendo. Un diseño que hiciera *append* incremental real no podría hacer esto sin pagar de más.

Además: **rate-limit del ancho entre puntos consecutivos** (máximo ±X% por punto). Sin esto, un cambio brusco de presión produce un escalón visible en vez de una transición.

### 4.7 Canales de vértice y textura viva
El segundo efecto de Open Brush: **la textura del material se mueve y se transforma mientras se dibuja.** Se resuelve enteramente con canales de vértice y el nodo `Time` — **sin un Material Instance Dinámico por trazo** (lo que mantiene un material estático por familia y hace posible la fusión de trazos, §9).

| Canal | Contenido | Para qué |
|---|---|---|
| **Vertex Color RGB** | color del punto (preset × calma) | el color queda grabado en el momento del gesto |
| **Vertex Color A** | calma 0..1 en ese punto | el material modula emisivo/alfa sin ningún parámetro |
| **UV0.U** | 0..1 a lo ancho de la cinta | mapeo transversal |
| **UV0.V** | según el **modo de UV** del `DA_Brush` (abajo) | la textura fluye a lo largo del trazo |
| **UV1.X** | longitud de arco absoluta, en metros | efectos que necesitan distancia real |
| **UV1.Y** | **semilla aleatoria por trazo** (0..1) | desfasa la animación: los trazos no pulsan todos en sincronía |

**Dos modos de UV0.V, por pincel:**
- **Tile** — `V = arcLength / EscalaDeTextura` (p. ej. tilear cada 20 cm). La textura se **deposita** a lo largo del trazo. Para patrones continuos.
- **Stretch** — `V = arcLength / longitudTotalDelTrazo` (0..1). Una textura entera mapeada al trazo completo, de punta a punta. Requiere **reescribir las V de todos los puntos anteriores en cada actualización** — otra vez **gratis** por el pre-alocado. Es el modo que da trazos con carácter propio (una veta, un degradado, un desvanecido) en vez de un patrón repetido.

**La animación:** un **Panner alimentado por el nodo `Time`**, con `UV1.Y` como offset de fase. Todos los trazos comparten un material estático y aun así cada uno respira distinto. Si hiciera falta un control global de la etapa (intensidad general, un pulso compartido) → **Material Parameter Collection**, nunca un MID por trazo. Coste: un Panner + un sampler; barato incluso en Quest.

### 4.8 Todo horneado en el vértice, nada en parámetros de material
🔴 **La decisión que mantiene el conteo de draw calls bajo.** El ancho (del gatillo), el color y la calma de cada punto se calculan en el momento de emitirlo y se hornean en **geometría + vertex color + UVs**. Consecuencia: **todos los trazos de un mismo pincel comparten un material estático** — sin un Material Instance Dinámico por trazo, y por lo tanto **se pueden fusionar en una sola sección**.

También es más honesto con la mecánica: el gesto queda **grabado en el trazo** en el momento en que ocurrió, como un registro, en vez de ser un parámetro global que cambia el dibujo entero retroactivamente.

## 5. El ancho lo decide el usuario · la calma decide la luz

🔴 **Esto supera a la §4.5 del design doc**, que decía "brusco = fino, apagado; suave = grueso, luminoso". Vigente: **el ancho es decisión del usuario**; la calma solo modula **luz y color**.

### 5.0 La toma del pincel define la mano hábil
**Patrón ya probado en el proyecto** — es exactamente cómo se toma el sensor en Breath (`BP_BreathSensor_V2`) y en Calibration (`BP_CalibProbe`). No inventamos nada nuevo:

1. `BP_MovementInstructions` **spawnea** `BP_BrushTool` sobre un `TargetPoint` con tag **`BrushSpawn`**, en la página correspondiente (como `SpawnSensor` en la página 2 de Breath).
2. El pincel se **auto-adjunta por proximidad** a la mano que lo toca (`TouchRadius`), **sin botón de grab**. Cachea `AttachedController`, `bAttached` y `bIsRightHand` — mismas variables y misma función `AcquireControllers` que cachea `LeftGrip`/`RightGrip`.
3. **Esa mano es la mano hábil.** El pincel avisa (evento o polling, como ya hace el resto del proyecto) y `BP_BrushPalette` **se adjunta al grip contrario**.
4. `bIsRightHand` decide además de qué mano sale el **háptico** y **cuál de las dos `IA_Draw_*`** se consume.

**Zurdos y diestros quedan resueltos sin preguntar nada** — la mano hábil la declara el cuerpo del usuario al estirarse a tomar el pincel, que es la misma lógica diegética del sensor de respiración. Nada queda hardcodeado a "derecha".

*Caso borde a cubrir:* si el usuario suelta el pincel a mitad de la etapa, se vuelve a auto-adjuntar a la mano que lo toque. Si esa es la otra mano, **la paleta se muda** al grip que queda libre. Es una consecuencia de la regla, no un caso especial.

### 5.1 Ancho = techo de la paleta × presión del gatillo × taper
```
ancho = lerp(AnchoMin, AnchoMax_paleta, presiónSuavizada) × taperDeTresTiempos
```
Tres capas con roles distintos y que no se pisan: **la paleta fija el techo** (decisión deliberada, se cambia pocas veces), **la presión modula dentro de ese techo** (expresión continua, momento a momento, como en Open Brush), y **el taper siempre gobierna las puntas** (el trazo nace y muere fino, con cualquier techo y cualquier presión).

`AnchoMin` es un piso pequeño pero **no cero** (~10% del techo): un toque suave tiene que dejar un trazo visible, no un trazo de ancho nulo que desaparece.

- 🔴 **Consecuencia de input:** `IA_Draw` es **Axis1D**, no Digital. Se empieza a dibujar al superar un umbral (~0.1) y la presión por encima de eso mapea el ancho. (Con un IA Digital el gatillo se lee 0/1 y se pierde la presión — ver `input.md` §1.)
- Suavizar la presión con un EMA corto (tau ≈ 0.08 s) y aplicarle el **rate-limit** de §4.6, o el trazo tiene escalones.
- El **taper de tres tiempos** (§4.6) multiplica este ancho, no lo reemplaza: el trazo sigue naciendo y terminando fino aunque el gatillo esté a fondo.
- *Alternativa si en visor la presión resulta incómoda:* stick vertical ajusta un ancho persistente. Queda como campo del `DA_Brush`, se decide con el casco puesto.

### 5.2 Calma → luz y color (el biofeedback que sí se conserva)
**Fuente de datos:** `GetLinearVelocity` del `MotionControllerComponent` (cm/s, world space, BlueprintPure, verificado disponible en Quest 3/OpenXR). No hay aceleración disponible (falta la extensión `XR_EPIC_space_acceleration` en el runtime de Meta) → **el "jerk" se estima por diferencias de velocidad ya filtrada**, nunca derivando la señal cruda.

**Pipeline (barato, 3 variables de estado):**
1. `speed = |LinearVelocity|` → `speedEMA = EMA(speed, tau ≈ 0.15 s)`.
2. `turn = ángulo entre la dirección de trazo actual y la anterior, por segundo` (sobre la dirección ya suavizada, no la cruda).
3. `calmRaw = clamp01( 1 − speedEMA/vMax ) × clamp01( 1 − turn/turnMax )`.
4. `calm = EMA(calmRaw)` con **ataque más rápido que la caída** — que el tirón se note enseguida pero que la recuperación sea generosa (nunca castigar de más).
5. `emissive = lerp(EmissiveMin, EmissiveMax, calm)` · `color = lerp(ColorApagado, ColorLuminoso, calm)` — ambos del `DA_Brush`, horneados en el vertex color del punto (§4.8).

**Valores de arranque (a calibrar en visor, no son datos medidos):** `vMax ≈ 120 cm/s`, `turnMax ≈ 180 °/s`. Un trazo contemplativo ronda los 15-40 cm/s.

**Recordatorio de diseño:** nunca mostrar esto como número ni barra. El trazo **es** el indicador.

### 5.3 La paleta de configuración en la mano contraria (`BP_BrushPalette`)

🔴 **Rediseño 2026-07-30 (pedido del usuario):** el ancho ya **no** viene de la presión del gatillo (no fue confiable — el curl del índice no llegaba parejo en modo mandos). **Todo se elige tocando la paleta**, en opciones discretas. La paleta es una **grilla plana de 9 celdas** sobre la mano no hábil (la que quedó libre al tomar el pincel, §5.0), que se seleccionan **tocándolas con la punta del pincel**.

**3 parámetros × 3 opciones = 9 celdas** (3 filas):
- **Fila COLOR** — 3 muestras de color (las define el usuario, no hay picker HSV). Selecciona el color base del trazo.
- **Fila GROSOR** — 3 tamaños (fino / medio / grueso), cada celda con un punto del grosor correspondiente. Selecciona el ancho **fijo** del trazo (× taper de tres tiempos; la calma ya **no** toca el ancho).
- **Fila PINCEL** — 3 presets, cada celda con una muestra del look de ese pincel. Selecciona qué **material** usa el trazo.

*(Confirmado 2026-07-30: **9 celdas, 3×3**.)*

**Implementación: mallas 3D, no UMG.** Un panel plano con 9 celdas-mesh; la selección es un **chequeo de proximidad** de la punta del pincel contra el centro de cada celda. Más barato y más robusto que un widget UMG con `WidgetInteractionComponent` (que además hace un trace y agrega piezas móviles). UMG queda sólo para las páginas de instrucciones.

**Selección (por celda, con debounce de ENTER):** cuando la punta **entra** en el radio de una celda (estaba afuera, ahora adentro) → se selecciona esa opción en su fila, **pulso háptico** + la celda **se enciende** (highlight del emissive). No se re-dispara hasta que la punta sale y vuelve. Estado en la paleta: `SelColor`/`SelWidth`/`SelBrush` (int 0-2).

**El pincel lee la paleta al empezar cada trazo** (`BeginStroke`): color = `paleta.GetColor(SelColor)`, ancho = `paleta.GetWidth(SelWidth)`, material = `paleta.GetBrushMat(SelBrush)`. Los 3 valores por fila viven en **arrays en Class Defaults** de la paleta (editables en un solo lugar, patrón `BP_CalibDirector`): `PaletteColors` (LinearColor[3]), `PaletteWidths` (float[3]), `PaletteBrushes` (Material[3]).

🔴 **Supresión del dibujo.** Mientras la punta está dentro del **volumen** de la paleta, `BP_BrushTool` **no emite puntos** — no se dibuja sobre la propia paleta. El pincel llama cada frame `paleta.UpdateTouch(TipWorld) → bSuppressDraw` y gatea el trazo con ese bool. Al salir del volumen se restablece (con debounce para que el trazo no arranque a mitad de camino).

**Aparición (confirmado 2026-07-30: MVP siempre visible):** la paleta está **siempre visible** sobre la mano no hábil. Polish (después) = se desvanece cuando la palma no mira al usuario y aparece al girar la muñeca hacia uno (producto punto up-de-la-paleta ↔ dirección a la cabeza, con histéresis). Cumple la regla de UI de la obra (design §6): nada anclado a la cabeza, display en muñeca, lenguaje visual de la obra, nunca clínico ni numérico.

**Preview vivo (polish):** un trazo de muestra corto con el material/ancho/color actuales, sobre la propia paleta. Cambiar algo se ve **en el instrumento**, no en un número.

**Implementación: mallas 3D, no UMG.** Un arco y unas celdas que se tocan se resuelven con meshes + un chequeo de proximidad de la punta, más barato y más robusto que un widget UMG con `WidgetInteractionComponent`. UMG queda reservado para las páginas de instrucciones (`widgets-vr.md`).

**Persistencia:** ninguna decisión de la paleta necesita guardarse aparte — el ancho ya viaja **por punto** en `F_StrokePoint` y el pincel por trazo en `F_Stroke.BrushId` (§6).

## 6. Persistencia — el modelo de datos

```
F_StrokePoint : Location (Vector) · Width (float) · Calm (float)
F_Stroke      : BrushId (byte) · BaseColor (LinearColor) · Points (array<F_StrokePoint>)
SG_Drawing    : Strokes (array<F_Stroke>) · UserId (string) · Timestamp (string) · Version (int)
```

- **Se guardan los puntos, no los vértices.** Los vértices se reconstruyen con el mismo `AddPoint` al cargar → el archivo es ~10x más chico, y si mañana mejoramos la geometría, **los dibujos viejos se ven mejor solos**.
- Tamaño estimado: 100 trazos × 60 puntos × 20 bytes ≈ **120 KB por usuario**. Nada.
- `bUseExternalFilesDir=True` ya está en `DefaultEngine.ini` → el `.sav` se saca por USB como en Calibration.
- **Bake en runtime:** `CopyMeshToStaticMesh` (Geometry Script) es **editor-only** — no existe en el APK. Nuestro "bake" es esto: guardar los datos y reconstruir. Es la ruta correcta y ya está resuelta.
- ⚠ **Gotcha operativo, corregido en vivo el 2026-07-29:** `add_variable` por MCP **sí crea arrays** con `container_type: "Array"` (verificado: el CDO devuelve `{"Vertices":[]}`); la nota contraria del scaffold de Touch estaba equivocada. Lo que **no** se puede crear por API son los **structs de usuario** (no existe tool de UserDefinedStruct) → `F_Stroke` y `F_StrokePoint` se crean **a mano en el editor**; el array que los contiene, una vez que el struct existe, sí se agrega por API.

## 7. Los tres pinceles (materiales para Quest)

Todos **Unlit** — es el instrumento principal en Quest y lo que hace posible el look Turrell sin luces ni post costoso.

| Pincel | Geometría | Material | Por qué |
|---|---|---|---|
| **A · "Luz"** (principal) | Cinta plana con espesor mínimo, frame por transporte paralelo | **Unlit Opaco**, emissive = vertexColor × gradiente por UV0.U, **Fresnel** para que el canto brille. ✅ **Construido: `Materials/M_Brush_Light`** — `VertexColor × (Brightness + Fresnel(2.5) × EdgeBoost)`, TwoSided. | Opaco = **cero overdraw**. De cara es un velo ancho de luz; de canto, un filamento brillante. El mismo trazo tiene dos lecturas según cómo lo mires — eso es lo que lo hace escultórico. ⚠ El Pincel A del proyecto original era **aditivo**, y eso es buena parte de por qué no se veía geométrico: si con opaco el trazo sigue duro, la variante aditiva es la siguiente palanca (pagando fill-rate). |
| **B · "Velo"** | La misma cinta, más ancha y más blanda | **Unlit Translúcido Aditivo**, textura animada (Panner + `Time`), modo de UV **Stretch** | Humo/acuarela: el trazo entero es una sola mancha con carácter, no un patrón repetido. ⚠ Presupuestado: es la única familia que paga overdraw. |
| **C · "Polvo"** | Estampado en `InstancedStaticMesh` (timer + gate de distancia, rotación/escala aleatoria) | **Unlit Masked** o opaco, emissive | Confeti/estrellas. **1 draw call para todo**, y las transforms también se serializan. |

**Restricciones de arte no negociables (de `materials-vr.md`):**
- 🔴 **El Quest no distingue nada por debajo de 13/255.** Los trazos tenues del gesto brusco **no pueden ser "casi negro"** — tienen que ser un verde apagado pero por encima del piso, o desaparecen del todo.
- ⚠ La translucidez en móvil se mezcla **en espacio gamma** → el Pincel B hay que **autorarlo mirando el APK**, no el monitor.
- ⚠ Con MSAA los bordes translúcidos hacen "bleed" → una razón más para que el pincel principal sea opaco.
- La **VR Preview por Link no sirve para juzgar color** (renderiza con el pipeline de escritorio). Usar **Preview Rendering Level → Android Vulkan** en el editor, y el APK real para la decisión final.

## 8. 🗺️ Organigrama de construcción (fase → compilar → testear → tracker → siguiente)

**Método (igual que Breath/Calibration): una fase, COMPILAR, TESTEAR, actualizar el tracker del BP, recién ahí la siguiente.**

| # | Construir | Cómo se testea |
|---|---|---|
| **0. Setup** | Carpeta `Stages/Movement/`, `L_Test_Movement` (duplicar `L_Test_Breath`), rama `stage/movement`, `IA_Draw_Left`/`IA_Draw_Right`/`IMC_Movement`. Crear los structs `F_StrokePoint`/`F_Stroke` **a mano** y el tracker `blueprints/BP_DrawCanvas.md`. | El nivel abre en VR, se ve el pawn. |
| **0.5 Config compartido** | `r.MobileHDR=True` + limpiar las líneas muertas y duplicadas del `.ini` (`LocalExposure` ×3, `ExtendDefaultLuminanceRange` ×3, `r.ForwardShading`, `r.RayTracing*`, `r.SkinCache`) + `TargetSDKVersion=34`. Reiniciar editor, recompilar shaders. **Avisar al otro dev.** | Breath y Heart siguen viéndose bien (o mejor) en Preview Android Vulkan. Nada se rompió. |
| **1. Motor de trazo** 🔴 | ✅ **Construida entera (2026-07-29), falta el test en visor.** `BP_DrawCanvas`: `BuildTriangles`/`BeginStroke`/`AddPoint`/`EndStroke` + `WriteRing`/`CollapseRing`/`PushMesh`, con pre-alocación, `UpdateMeshSection`, cinta plana con frame transportado y decimación distancia+ángulo. `BP_BrushTool`: auto-attach por proximidad (patrón de `BP_BreathSensor_V2`), `AutoReceiveInput=Player0`, gatillo de **su** mano (por ahora `IA_Shoot_*`, Boolean) → canvas con ancho fijo. Los dos colocados en `L_Test_Movement`. | En PIE/visor: el usuario toma el pincel **con cualquiera de las dos manos**, aprieta el gatillo de esa mano y dibuja una cinta verde continua que **se retuerce siguiendo la curva, sin flips ni giros locos**. **Este es EL hito técnico.** ⚠ Primer chequeo del test: si la cinta sólo se ve por el reverso, invertir el orden de los índices en `BuildTriangles`. |
| **2. Calidad del trazo** | ✅ **Construida (2026-07-29), falta el test en visor.** Decimación distancia+ángulo (afinada a 1 cm / 6°), **One-Euro** sobre la punta (`BP_BrushTool.FilterTip`), **taper de tres tiempos** en la geometría (6 arrays de puntos + `RefreshRing`/`RefreshTail` en `BP_DrawCanvas`), continuación de sección (`ContinueSection`, con el truco de inflar `ArcLength` para que no quede un pellizco en el corte), decimación por tiempo presente pero apagada. ⬜ Falta sólo el **roll de muñeca** como delta. | El trazo **nace fino, se ensancha detrás de la punta y termina fino**. Sin facetas, sin temblor, sin corte al pasar los 128 puntos. |
| **3. Calma → material** | ✅ **Construida (2026-07-30), falta test en visor.** Calma (§5.2) desde `GetLinearVelocity`+`GetAngularVelocity` → `ComputeCalm` (EMA asimétrico: ataque rápido, recuperación lenta) → vertex color alpha → el material `M_Brush_Light` modula el emissive (`lerp(CalmMin,CalmMax,alpha)`). 🔴 **La presión del gatillo se DESCARTÓ** (el curl del índice no llegaba parejo en modo mandos); `ComputeWidth` quedó devolviendo el ancho fijo hasta que la paleta (Fase 4) lo defina. | Gesto brusco = apagado, gesto suave = luminoso. |
| **4. Paleta de configuración + 3 pinceles** 🔴 (la fase que sigue) | **Reemplaza las viejas Fase 4 y 4.5.** Ver plan de construcción abajo (§8.b). `BP_BrushPalette`: grilla plana de **9 celdas** (3 color · 3 grosor · 3 pincel) en la mano no hábil, selección por toque de la punta; el pincel lee color/ancho/material de la paleta al empezar cada trazo; supresión del dibujo sobre la paleta; 3 materiales de pincel. Limpia de paso el cableado muerto de presión (curl del índice, `ComputeWidth`). | Toco un color → el trazo siguiente sale de ese color. Toco un grosor → sale de ese ancho. Toco un pincel → cambia el material. No se puede dibujar sobre la paleta. La paleta está en la mano opuesta al pincel, tome con la que tome. |
| **5. Audio + háptico** | Sonido continuo del pincel con fade-in al empezar / fade-out al soltar, **modulado por velocidad y calma**; háptico sutil por punto emitido. | Dibujar se *siente*. Sin clicks ni cortes al empezar/soltar. |
| **6. Instrucciones** | ✅ Hecho: **`WBP_MovementInstructions`** (duplicado del de Breath, Border `BG` en verde) + su material `W_MovementInstruction`, en `Stages/Movement/Widget/`. ✅ **`BP_MovementIntro`** (duplicado recortado de `BP_IntroFade`) hace sólo el fade y ya **no** spawnea nada de Breath. ⬜ Falta el **driver de páginas**: 🔴 se va por la **Opción A** del plan de Touch (§6.b) — NO reusar `BP_Instructions` de Breath (arrastra `SpawnSensor`/`SpawnBox`/`StartBreathStage` y variables tipadas a `BP_BreathSensor_V2`, que no se pueden retipar por API). Se escribe un `GotoPage` propio en un BP de Movement, que spawnea `BP_BrushTool` y gatea la última página por acción. **Bloqueado por contenido: faltan los textos (en inglés) y los íconos (§11).** | Corre la secuencia de páginas; la última no deja pasar hasta que el usuario dibuja suave de verdad. |
| **7. Cierre** | `BP_MovementStageManager`: timer 2 min → apaga el pincel → guarda → `BP_FadeSphere` a negro → `OpenLevel` del nivel actual. | End-to-end: instrucciones → 2 min de dibujo → fundido → reinicia. |
| **8. Persistencia** | `SG_Drawing` + `SerializeToSave`/`RebuildFromSave` + un comando de debug que recarga el último dibujo. | Se dibuja, se guarda, se recarga: el dibujo vuelve **idéntico**. Verificar el `.sav` por USB. |
| **9. Perf + APK** | Fusión de trazos sellados en secciones por familia (§9), cap de trazos, medición en device. | 72 fps estables con el peor caso de dibujo (2 min llenando el espacio), ≤4 draw calls de dibujo. |

## 8.b 🎛️ Fase 4 en detalle — Paleta de configuración (`BP_BrushPalette`) + 3 pinceles

Plan de construcción de la fase que sigue. Una responsabilidad por BP, misma disciplina que el resto. **Meshes, no UMG** (§5.3).

**Modelo de datos (arrays en Class Defaults de la paleta, editables en un lugar):**
- `PaletteColors` (LinearColor[3]) — los 3 colores. Arranque: verde de etapa + un cálido + un frío (a gusto del usuario). 🔴 **Todos por encima del piso 13/255.**
- `PaletteWidths` (float[3]) — 3 grosores. Arranque: `0.6 / 1.3 / 2.6` cm.
- `PaletteBrushes` (Material[3]) — A `M_Brush_Light` (hecho) · B `M_Brush_Veil` · C `M_Brush_C`.
- Estado: `SelColor` `SelWidth` `SelBrush` (int 0-2, default 0).

**API de la paleta:** `UpdateTouch(TipWorld) → bool bSuppressDraw` (hit-test + selección + highlight + háptico, devuelve si suprimir el dibujo) · `GetColor()` · `GetWidth()` · `GetBrushMat()`.

| # | Construir | Cómo se testea |
|---|---|---|
| **4.0 Limpieza** | ✅ **Hecho (2026-07-30).** Sacados los 2 eventos `IA_Hand_IndexCurl_*` + branches/sets y las vars `TrigPressure/PressEMA/PressTau/WidthMinFrac`. `ComputeWidth` devuelve el ancho fijo. | Compila; el trazo sigue saliendo (ancho fijo). |
| **4.1 Paleta física** | ✅ **Construida (2026-07-30), falta test en visor.** `BP_BrushPalette`: `Panel` + **9 celdas-cubo** (3×3) + material `M_PaletteCell` (unlit, color+glow). Auto-attach al **grip libre**: el pincel, al agarrarse (`DoAttach`), spawnea la paleta y llama `AttachToHand(bIsRightHand)` → se pega al grip contrario. Celdas coloreadas desde `CellColors` (fila color = los 3 colores, resto neutro). Tracker: `blueprints/BP_BrushPalette.md`. | Al tomar el pincel con una mano, la paleta aparece en la otra, con sus 9 celdas visibles. |
| **4.2 Selección por toque** | ✅ **Construida (2026-07-30), falta test en visor.** `UpdateTouch`: hit-test por distancia a cada celda, on ENTER (debounce con `LastCell`) setea la fila + `HapticPulse` (evento con Delay) + `Highlight`. Guarda `bOver` (punta dentro del `PanelRadius`). El pincel (`CheckPalette` en `UpdateStroke`) lee `bOver` y gatea el dibujo con `(bTrigHeld AND NOT bOverPalette)`. | Tocar una celda la enciende + vibra; sólo una encendida por fila; no se re-dispara si la punta se queda quieta encima; no se dibuja sobre la paleta. |
| **4.3 Pincel ↔ paleta** | ✅ **Construida (2026-07-30), falta test en visor.** La paleta expone `CurColor`/`CurWidth`/`CurBrushMat` (actualizadas en `Highlight`, vía variables + getters cross-clase — el return cross-clase no bindea en el DSL). El pincel sincroniza `BrushColor`/`BrushWidth`/`BrushMat` cada frame en `CheckPalette` y los usa en `BeginStroke`. El canvas: `BeginStroke` ganó el param `Mat` → `StrokeMat` → `OpenSection.SetMaterial` (cirugía sobre el pin del material). | Toco color/grosor/pincel → el trazo siguiente sale con esa config. No se dibuja sobre la paleta ni salta un trazo al salir de ella. |
| **4.3.5 🐛 FIX (antes de 4.4)** | En visor (2026-07-30): color funciona, **grosor no cambia** el trazo (pincel esperable, los 3 = mismo material). Sospecha #1 = **pose/alcance** de la paleta (las filas 1-2 quedan anguladas por el offset de `AttachToHand`, a ojo). Diagnóstico y plan en `blueprints/BP_BrushPalette.md`. Va **antes** de 4.4 porque si es alcance, la fila de pincel tampoco se puede tocar → no se testearían los brushes nuevos. | Tocar grosor/pincel enciende la celda y cambia el ancho. |
| **4.4 Los 3 materiales** | A `M_Brush_Light` ✅. **B `M_Brush_Veil`** — Unlit Translúcido Aditivo, más blando/ancho (la única familia que paga overdraw, presupuestada). **C `M_Brush_C`** — un tercer look (neón fino muy brillante, o estampado). Los 3 leen `VertexColor.A` = calma igual (la modulación de calma es compartida). ⚠ B/C pueden arrancar como variantes simples y refinarse. | Los 3 pinceles se ven distintos y bien en **Preview Android Vulkan** y en un APK. La calma sigue modulando los tres. |
| **4.5 Polish** | Aparición por giro de muñeca con histéresis (MVP = siempre visible); **preview vivo** de un trazo de muestra sobre la paleta; animación de selección. | La paleta aparece al girar la muñeca hacia uno y se va al girarla; el preview refleja la config actual. |

**Calma → material (confirmado):** ya está en `M_Brush_Light` (emissive × `lerp(CalmMin,CalmMax, VertexColor.A)`). Se mantiene y se replica en B/C. Opcional a futuro: que la calma además **enfríe el color** (hue shift) — necesita 2 colores por pincel, queda para después.

## 8.c 🔬 Qué rescatamos del Tilt Brush propio (auditoría en vivo 2026-08-03) — plan de aplicación

Se abrió Neural Canvas con el MCP y se leyeron `BP_Stroke` y `M_Brush` directo. Análisis completo en [`references/movement-3d-drawing.md`](../../.claude/skills/unreal-vr/references/movement-3d-drawing.md) §"Segunda auditoría". **Conclusión: lo que hace que el de ellos se vea fluido NO es la geometría — es el material.** Orden de aplicación, de mayor a menor impacto:

| # | Cambio | Por qué / detalle |
|---|---|---|
| **1** ✅ | ~~**Arreglar el pin `Width`**~~ **HECHO y validado en visor (2026-08-03)** | Confirmado: `Width` estaba `"connected_pins":[]` → llegaba **0**. `ComputeWidth` (función **impura**) inline como argumento de datos deja el pin en su default, compilando limpio. Fix: `ComputeWidth` borrada + getter puro `GetBrushWidth` al pin. **"Ahora sí, muy perceptible."** Gotcha documentado en `gotchas.md`. |
| **2** ✅ | ~~**Material: alfa suave a lo ancho + Aditivo**~~ **HECHO (2026-08-03), falta test en visor** | `M_Brush_Light` pasó a **`BLEND_Additive · Unlit · TwoSided`** y su `Opacity` es ahora un **borde suave procedural**: `pow(1 − |UV0.U×2 − 1|, EdgeFalloff)` → la cinta se desvanece hacia sus cantos. Sin textura por ahora (procedural); se puede cambiar a textura cuando el usuario las tenga. ⚠ Aditivo = fill-rate → **medir en APK**; si duele, A puede volver a Masked conservando el falloff. |
| **2b** ✅ | **Los 3 pinceles, con 1 solo shader** | `M_Brush_Light` = master; **`MI_Brush_Veil`** (falloff 2.8 / brillo 0.55 → plumeado y tenue) y **`MI_Brush_Neon`** (falloff 4.5 / brillo 2.8 → filamento intenso) son **Material Instances** que sólo cambian escalares → **cero permutaciones de shader** (`packaging-pso.md`). Ya enganchados en `PaletteBrushes` de la paleta. |
| **3** | **Taper al material, no a la geometría** | Ellos pasan por trazo `StrokeLength` y `ShrinkAmount = −StrokeWidth` al MID y afinan las puntas **en el shader**; su geometría es siempre de ancho pleno. Elimina de raíz el riesgo de nuestro `RefreshTail` (ventana de refresco / congelado a media rampa / dependencia de la densidad de puntos). ⚠ Cuesta un **MID por trazo**, que es justo lo que §4.8 evitaba para poder fusionar trazos → **decidir el trade-off**: fusión de draw calls vs robustez del taper. |
| **4** | **Volver a una densidad de puntos sana** | Ellos usan **`MinDistance = 2 cm`** (4× más grueso que nuestro 0.5) y **no se ve facetado**, porque el alfa suave lo disimula. Nosotros bajamos a 0.5 cm / 2° peleando el facetado **por el lado equivocado**. Con el material arreglado se puede volver a ~1.5-2 cm → menos vértices, mejor perf. |
| **5** | *(opcional)* Espesor: evaluar 2 verts vs 4 | La de ellos es **cinta plana pura de 2 vértices**; la nuestra es una caja de 4 con espesor, que tiene silueta propia y se lee como objeto. Con material aditivo el espesor deja de hacer falta. Probar sólo si tras 2-4 sigue leyéndose duro. |

**Escala de referencia:** en el de ellos `StrokeWidth` es el **semi-ancho** (ancho total = 2× ) y su default es `1` → cinta de **2 cm**. En el nuestro `W` es el ancho **total**. Sirve para calibrar los 3 grosores de la paleta.

## 9. Presupuesto de performance (Quest 3, 13.9 ms)

| Recurso | Estimación | Techo |
|---|---|---|
| Triángulos del dibujo | 100 trazos × 60 puntos × 8 tris ≈ **48k** (4 vértices por punto) | 1.3M–1.8M (Meta) — **irrelevante** |
| Draw calls del dibujo | 1 sección por trazo = hasta 100 · con fusión por familia = **≤4** | 700–1000 (Meta) |
| Fill rate | Pincel A opaco = casi gratis. **Pincel B aditivo es el único riesgo real** | 🔴 el cuello de botella de la obra |
| CPU por frame | ~7 `UpdateMeshSection` por segundo, de 512 vértices cada uno | *"Cualquier lógica que tarde más de 2 ms probablemente se puede optimizar"* (Epic) |

**Estrategia de fusión (Fase 9):** al sellar un trazo, agregarlo a la sección acumulada de su familia de pincel; cuando esa sección pasa ~8k vértices, se sella y se abre otra. Recreación amortizada (una por trazo, en el momento en que el usuario suelta el gatillo — hay margen), y termina en pocas secciones en vez de cien.

**Cap duro:** si se superan N trazos (arranque: 150), el más viejo se desvanece y se borra. Nunca dejar que el presupuesto dependa de cuánto dibuje el usuario.

## 10. Cabos técnicos (para no redescubrirlos)

- **Input por EVENTOS de Enhanced Input**, nunca por value-getters: los getters de OpenXR devuelven 0 fuera de su IMC. Lección ya pagada en el sensor de Breath. Para la presión del gatillo: `IA_Draw_*` **Axis1D** con trigger **Down** → el evento `Triggered` llega cada frame mientras esté apretado, con el valor analógico en `Action Value`. ⚠ Cuidado con el modifier **Dead Zone**: se come los valores pequeños, que aquí son justamente los trazos más finos.
- **UV0.V en modo Stretch** obliga a reescribir las V de los puntos anteriores en cada actualización. Es gratis por el pre-alocado (§4.2), pero **se rompe si un trazo cruza a una sección nueva**: en ese caso, congelar el modo Stretch a la longitud de la sección o cambiar ese pincel a modo Tile. Decidir cuando se implemente §4.7.
- 🔴 **Un actor spawneado no recibe input por defecto.** El pincel se spawnea en runtime y necesita **`AutoReceiveInput = Player0`** en su CDO para que le lleguen los eventos de Enhanced Input. Lección ya pagada en `BP_CalibProbe` (el sensor no lo tenía y el gatillo leía 0 siempre).
- 🔴 **Los FKeys legacy no sirven en OpenXR.** `GetInputAnalogKeyState("MotionController_Right_Trigger")` devuelve **0 siempre**, y los value-getters de Enhanced Input también, fuera de su IMC. Lo único que funciona son los **EVENTOS** — verificado a la mala en la instrumentación de Calibration.
- **`Add Mapping Context` en `Event Possessed`**, no en `BeginPlay` (en BeginPlay el controller puede no estar asignado todavía y falla en silencio).
- **Pose Aim vs Grip**: para la punta del pincel usar **Grip** (es la pose de "objeto sostenido en la mano", y el pincel es literalmente eso), con la punta como `SceneComponent` hijo con offset hacia adelante. Aim es para apuntar, no para empuñar.
- **Pose y velocidad leídas en el mismo Tick son consistentes** (mismo poll). `GetLinearVelocity`/`GetAngularVelocity` son BlueprintPure y **no** hace falta estar dentro de `OnMotionControllerUpdated`.
- ⚠ La pose ya viene **predicha** al `predictedDisplayTime` y filtrada por el runtime de Meta — no es la muestra IMU cruda. No sorprenderse si el jitter tiene textura rara.
- **PMC**: colisión **desactivada** (`NoCollision`), `bCastDynamicShadow=false`. El dibujo no colisiona con nada ni proyecta sombras.
- **UV**: `U` = 0..1 a lo ancho (o alrededor del tubo), `V = DistanciaTotal / EscalaDeTextura` (p. ej. tilear cada 20 cm) — el UV a lo largo del trazo es lo que hace posible cualquier pincel texturado.
- **No re-`write_graph_dsl` un grafo existente** — lo duplica. Grafo nuevo = DSL; grafo existente = cirugía de nodos.
- **`type_id` con paréntesis rompe el parser del DSL** (`Game|OpenLevel(byName)`) → ese nodo se arma con `create_node`/`connect_pins` después. Gotcha ya pagada en `BP_BreathStageManager`.
- Un `(event Custom|X ...)` tiene que declararse **antes** en el texto DSL que cualquier `CallFunction|X` que lo invoque.

## 11. Assets y contenido a proveer (usuario)

- 🖊️ **Textos de las páginas del widget de instrucciones** — por definir. 🔴 **Van en INGLÉS** (convención de la obra: todos los textos in-headset de los stages son en inglés; solo `Calibration`, que es herramienta interna, quedó en español). Placeholders propuestos, en el lenguaje de la obra — cada página **pide una acción**, no explica un concepto:
  1. *"Settle in. Let your shoulders drop."*
  2. **"Take the brush — either hand."** *(gate: tomarlo; define la mano hábil)*
  3. *"Squeeze to draw. Squeeze harder for a thicker line."*
  4. *"Turn your other wrist. Your palette is there."* *(gate: cambiar el tamaño o el pincel)*
  5. *"Move slowly. Calm becomes light."* *(gate: dibujar un trazo suave)*
  6. *"Draw anything."*
- 🖼️ **Íconos de las páginas** (mismo formato que Breath/Calibration) — por definir.
- 🎨 **Texturas de pincel** (2-3 alfas suaves para el Pincel B, tileables en V y una en modo Stretch) y la malla chica del Pincel C.
- 🖌️ **Malla del pincel** que se ve en el mando derecho.
- 🎛️ **Malla y arte de la paleta** (arco de tamaño + celdas de pincel) — en el lenguaje visual de la obra: anillo, luz, latón. Nada clínico, nada numérico.
- 🎵 **Sonido continuo de pincel** (loop suave, modulable por velocidad) + el pad ambiente de la etapa.
- 🎨 **Paleta verde de la etapa**: definir el color de gesto brusco (apagado, pero **por encima de 13/255**) y el de gesto suave (luminoso).

## 12. Naming y mantenimiento

"Movement" (carpeta/nivel) = "Surrounding" (nombre de obra) = esta etapa de dibujo. Rama: **`stage/movement`**. Al avanzar: actualizar `docs/ESTADO-STAGES.md`, el `_INDEX.md` de blueprints y el tracker de cada BP tocado. Los nodos de PMC que se verifiquen van a `references/nodes.md`.
