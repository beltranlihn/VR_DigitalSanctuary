# BP_Card — la carta física de resultados (Core/Card/)

> **El cierre de la obra rehecho como un OBJETO** (2026-09-02). Reemplaza al modelo en que los gráficos,
> las esferas y el dibujo colgaban de la ameba. Plan: [`docs/PLAN-CARTA-2026-09-02.md`](../../../../docs/PLAN-CARTA-2026-09-02.md).
>
> Decisión de Beltrán: *"nos conviene armar un BP especifico de la carta de resultados, literalmente que
> sea una carta fisica"*. **La carta es el contenedor; la ameba pasa a ser uno de sus seis contenidos.**

- **Actor**: `/Game/SoulCharger/Core/Card/BP_Card` (movido desde la raíz de `Content/` el 2026-09-02).
- **Mesh**: `/Game/SoulCharger/Core/Card/SM_Card` — 122 verts · **200 × 178 × 10 cm** · modelado por
  Beltrán, con **seis huecos pasantes**.

## Status
🟢 **Construida entera y enganchada a la obra (2026-09-02)**. Verificado en PIE, log:
```
CARTA: feed calm=1067  →  graficos alimentados  →  ameba encajada  →  dibujo encajado  →  melodia sembrada
```
y **confirmado en captura**: las curvas de CALM y RHYTHM dibujando, los anillos de BREATH y las
esferas de la melodía, **cada cosa en su ranura**. Cero `Accessed None` propios.

🟢 **LOS SEIS HUECOS LLENOS, confirmado en captura (2026-09-02, 2ª tanda)**: ameba · dibujo · calma ·
ritmo · respiración · melodía, cada uno en su ranura, sin textos encimados.

🟢 **Primera pasada en visor OK** (*"va super"*), y los **cinco arreglos de ritmo** que salieron de ella
ya están aplicados (ver la 5ª tanda al final).

⬜ **Lo que falta**: el ajuste visual de las anclas (es el ojo de Beltrán) · retirar `BP_Portrait_SC` ·
la composición carta-vs-constelación · visor de los arreglos.

---

## 🧭 El sistema de coordenadas (medido, no supuesto — leerlo antes de tocar posiciones)

El `Card` (StaticMeshComponent) cuelga del `DefaultSceneRoot` con **`roll = 90`**, que es lo que pone la
carta **de pie**. De ahí salen tres hechos que gobiernan todas las cuentas:

| Hecho | Valor |
|---|---|
| Ancho de la carta | **200 cm**, sobre el eje **X** del actor |
| Alto de la carta | **178 cm**, sobre el eje **Z** del actor |
| Espesor | 10 cm, sobre el eje **Y** |
| **El frente** | la cara **+Y** del actor |
| Conversión desde el espacio del mesh | `X_actor = X_local` · **`Z_actor = −Y_local`** |

🔑 **Cómo se determinó el frente** (sirve de plantilla para el próximo mesh): Beltrán dijo *"si miro de
frente la carta, veo la ameba arriba a la izquierda"*. La ameba está en `X = −58`. Un observador que
mira hacia **−Y** tiene su izquierda en −X ⇒ ve la ameba a la izquierda ✓. Si mirara hacia +Y la vería a
la derecha ✗. **El frente es +Y.** Lo confirma la vertical por otro camino: con roll +90, `+Y_local`
cae en `−Z`, así que los huecos de arriba (que están en `Y_local` negativo) quedan **arriba** ✓.
Dos deducciones independientes que dan lo mismo.

---

## 🎛️ Cómo se autora (esto es lo que hay que saber para mover algo)

**Las seis anclas son componentes visibles y arrastrables.** Cada una es un cubo delgado (2 cm) con
`MI_Ghost`, `bHiddenInGame` y sin colisión: **se ve en el viewport del Blueprint y no existe en juego.**

🔴 **La convención: el ancla no marca sólo el centro, también el TAMAÑO del hueco.**
`RelativeScale3D.X = ancho/100` y `RelativeScale3D.Z = alto/100`. Se mueve con el gizmo de posición y se
escala con el de escala, hasta que el rectángulo tape el hueco. **La lógica de las fases F3-F5 LEE esa
transform** para colocar y dimensionar el contenido — igual que `BP_ProtoSoul_SC` lee la escala de su
`TargetPoint`. Cambiar el mesh no obliga a tocar ni un nodo: se re-arrastran seis rectángulos.

### Las seis anclas (valores de arranque, en cm)

| Ancla | X | Z | Ancho | Alto | Qué se encaja |
|---|---|---|---|---|---|
| `SlotAmoeba` | −58 | +48 | 71 | 67 | la `BP_ProtoSoul_SC` real |
| `SlotDraw` | +38 | +48 | 110 | 67 | el `BP_DrawCanvas` real |
| `SlotCalm` | 0 | 0 | 185 | 22 | curva de calma (widget) |
| `SlotHeart` | 0 | −25 | 185 | 22 | curva de ritmo (widget) |
| `SlotBreath` | 0 | −50 | 185 | 22 | anillos de respiración (widget) |
| `SlotMelody` | 0 | −75 | 185 | 22 | las 8 `BP_SoundOrb_SC` reales |

🔴 **Las seis van en `Y = +5,6`, no en 0.** La carta tiene 10 cm de espesor (`Y ±5`), así que un ancla en
`Y = 0` queda **enterrada dentro del mesh y no se ve** — se colocaron ahí primero y fue justamente lo que
impidió autorarlas. En `+5,6` flotan 6 mm por delante de la cara frontal: se ven enteras y se puede
juzgar el encaje contra el borde del hueco. **La Y del ancla no es la Y del contenido**: la lógica lee
`X` y `Z`, y cada contenido pone su propia profundidad (la ameba sobresale, los widgets van detrás).

⚠ **Son valores de arranque, no medidas finales.** Los centros vienen de los seis `TextRender` que
Beltrán colocó dentro de cada hueco; los anchos y altos, de la proporción de su captura (±2 cm). El
número definitivo lo pone él arrastrando. Dos rasgos del diseño que conviene no perder: el hueco del
**dibujo es bastante más ancho que el de la ameba** (110 vs 71) y los cuatro de abajo son **la misma
ranura repetida cada 24,5 cm**.

### Los 6 `TextRender`
*Ameba · Dibujo · Grafico Calm · Grafico Heart · Grafico Breath · Melody*. Son de Beltrán y **cuelgan del
`Card`** (o sea, están en el espacio local pre-roll: ojo con sus coordenadas, hay que convertirlas).
**No se borran**: son la referencia de la que salió el mapa. ⬜ Falta ponerlos detrás de un
`bShowSlotLabels` (default `false`) para que no salgan en juego.

---

---

## 🧩 Cómo está armado (F2-F5)

### Variables
| Grupo | Variables | Rol |
|---|---|---|
| Datos | `SCalm` `SHeart` `SBreath` `SMelody` `SDraw` | los 5 CSV de la entrada que se está mostrando |
| Refs | `ArchRef` `SoulRef` `CanvasRef` `SensRef` | cacheadas al vuelo |
| Diagramación | `SoulSize` (**0,12**) · `MelodySpacing` (23) · `MelodyScale` (0,5) · `DrawMargin` (0,92) | 🎛️ instance-editable |
| Datos de melodía | `MelodySounds` (array de `SoundBase`) | los **20 clips** del Módulo 1 |
| Debug | `bDebugShowOnPlay` · `DebugShowDelay` (8 s) · `FeedIdx` (−1) | mostrar la carta sin jugar la obra |

🔴 **`SoulSize = 0,12`** (ver la 5ª tanda). La fórmula real es `radio visible = 83 cm × (Size / 0,3)`
= **277 × Size**, así que para un hueco de 67 cm: `Size = 67 / (2 × 277) ≈ 0,12`. Los valores 0,78 y 0,40
que pasaron por acá eran cuentas mal hechas: la primera confundía radio con diámetro y la segunda
olvidaba dividir por `RingSizeRef`.

### Funciones
| Función | Qué hace |
|---|---|
| **`Show()`** | La única puerta: `Feed` → `FeedGraphs` → `PlaceSoul` → `PlaceDraw` → `PlaceMelody`. |
| `Feed(Index)` | Busca el [[BP_SoulArchive_SC]] y despacha: **`Index < 0` → `FeedNow()`** (la corrida actual, vía `CollectOnly`), **`Index >= 0` → `FeedIndex()`** (esa entrada guardada, para la constelación). |
| `FeedGraphs()` | `GetUserWidgetObject(Panel)` → cast → **`SetSeries(calm, heart, breath)`**. |
| `PlaceSoul()` | Attach de la ameba + `SetSize`. |
| `PlaceDraw()` | `RebuildFrom(SDraw)` y encaje por bounds (abajo). |
| `PlaceMelody()` / `OneOrb(Tok)` | Parte `SMelody` por comas y siembra un `BP_SoundOrb_SC` por nota. |
| `MaybeShowOnPlay()` | El gate de debug: timer a `Show` por `SetTimerByFunctionName`. Lo llama `BeginPlay`. |

### 🔴 Regla de oro del encaje: **NO attachear al ancla**
Las anclas tienen **escala no uniforme** (p. ej. 1,85 × 0,02 × 0,22), y en Unreal la escala del padre
**siempre** se hereda: colgar la ameba de su ancla la aplastaría. Por eso todo se attachea al
**`DefaultSceneRoot`** (identidad) y se posiciona **en coordenadas de mundo** leyendo
`GetWorldLocation(<ancla>)`. El ancla se **lee**, no se usa como padre.

### El encaje del dibujo
`PlaceDraw` mide con `GetActorBounds` (el `.sav` guarda la forma, no el encuadre), centra con
`loc = ancla − origen × escala`, y **`FitDraw()` calcula la escala por el lado que topa primero**
(ver la 5ª tanda). ⚠ `ShowSignatureAt` **no servía**: ancla el dibujo a la ameba, no a un punto.

### El panel de gráficos
Un `WidgetComponent` **`Panel`** con **`WBP_Portrait_SC` reusado tal cual** (1600×900 a escala 0,1156 =
185 × 104 cm, centrado en Z −25, `blendMode` Transparent). Se decidió **no construir widgets nuevos**:
el de retrato ya tiene resueltos el parseo, la normalización por mín/máx del usuario, las curvas por
`OnPaint` y los anillos — incluida la trampa del `MinOfFloatArray` que aplanaba la curva. Lo que falta
es **rediagramarlo** para la carta.

---

---

## 🔬 Las tres causas de "el log dice OK pero no se ve" (2026-09-02, 2ª tanda)

Las tres dieron el **mismo síntoma** — `CARTA: ... encajado` en el log y el hueco vacío en pantalla — y
ninguna se habría encontrado sin mirar la captura. Es el caso de libro de **verificar el estado estable,
no el spawn**.

### 1. La ameba: su propio Tick deshacía la colocación
`FitSoul` hacía `AttachActorToComponent` + `SetActorLocation`, y **cada frame `AnchorStep` la devolvía a
su `TargetRef`**. El log decía "encajada" porque la función corrió; el actor volvía un frame después.
✅ **Arreglo: no pelearle al Tick, usarlo.** Se spawnea un `TargetPoint` en la posición del ancla con
**escala uniforme = `SoulSize`**, se attachea al `DefaultSceneRoot` y se le pasa a la ameba con
**`SetTargetRef`**. Su propia maquinaria la lleva (posición **y** tamaño, porque `AnchorStep` lee el
`Scale3D` del destino) y **el viaje sale suave de regalo**.
🔴 **`MoveToActor` NO se puede usar desde el DSL**: colisiona con **`AI|Navigation|MoveToActor`** y el
escritor cablea el de IA **en silencio y compilando** (verificado en el read). `SetTargetRef`, al ser un
setter de variable, no tiene homónimo.

### 2. El dibujo: se reconstruía **sin material**
`StrokeMat` del canvas estaba en **`None`** (tanto en el CDO como en la instancia), así que el trazo se
generaba pero salía negro sobre fondo negro. Sólo se lo veía recortado contra el marco claro de la carta
cuando la escala era 1,0 — lo que hacía parecer un problema de tamaño y no de material.
✅ **Arreglo: `SetStrokeMat(M_Brush_Light)` antes de `RebuildFrom`.**
⚠ **Esto probablemente afecta también a [[BP_Constellation_SC]]**: reconstruir la firma de un vecino en
un canvas que nunca dibujó deja el mismo `StrokeMat` nulo. En la obra funciona porque la paleta ya lo
puso durante Surrounding. **Vale revisarlo.**
🔴 `MPC_Draw.DrawFade` **no era el problema**: su default ya es 1. Se dejó el `SetScalarParameterValue`
igual, como seguro barato para cuando el sensor lo haya bajado a 0.

### 3. El auto-fit del dibujo quedó en escala CERO
`(bind (_o _e) (Collision|GetActorBounds ...))` — **el bind múltiple no funciona sobre un nodo PURO**: el
DSL lo inlinea y el `read` mostró `MakeVector 0.0` y un `vector/vector`. La escala salía 0.
✅ **Arreglo: nada de auto-fit.** `DrawScale` es una **variable instance-editable** (0,30 calibrado
mirando) y el centrado usa sólo el **primer** output de `GetActorBounds` (el Origin), guardado en
`DrawOrigin` **antes** de escalar. Menos nodos, y el tamaño lo autora Beltrán.

---

---

## 🎵 La melodía suena (2026-09-02, 3ª tanda)

`MelodySounds` tiene los **20 clips** (copiados del CDO de [[BP_Portrait_SC]]), y el orbe recibe el clip
además del id. El pulso es un **timer looping** de `MelodyStep` (0,6667 s = el compás de 5,33 s del
`PadM1` dividido en 8) que recorre `Orbs` con wrap y llama `PulseonBeat`.

| Pieza | Rol |
|---|---|
| `Orbs` (array de `BP_SoundOrb_SC`, tamaño `MelodySteps`) | **una ranura por paso del compás**, con huecos donde no hay nota |
| `MelIdx` | el paso actual |
| `MelodyStep` / `MelodySteps` | 🎛️ 0,6667 s · 8 — instance-editable |
| `MelodyTick()` | avanza con `Math\|Integer\|%(Integer)` y pulsa el orbe del paso |

🔴 **Tres trampas del DSL que costaron round-trips acá:**
1. **El `bind` múltiple NO funciona sobre un nodo PURO.** `(bind (_l _r _ok) (Utilities|String|Split …))`
   compila pero **las tres variables reciben el PRIMER output**: el `clipId` estaba tomando el número de
   slot. ✅ La salida es `ParseIntoArray` + **`Utilities|Array|Get(acopy)`** con índice 0 y 1.
2. **`Utilities|Array|Get(acopy)` SÍ se puede escribir en el DSL** pese a los paréntesis en el `type_id`
   — pero **un `bind` que no se usa se poda**, así que probarlo "en seco" da la falsa impresión de que
   el nodo no se creó.
3. **El operador `%` no existe**; es `Math|Integer|%(Integer)`.

⚠ `MelIdx` arranca en **0, no en −1**: el `Array|Get` se evalúa **antes** del incremento, así que con −1
se indexaría fuera de rango en el primer tick.

## 🔌 F6 — enganchado a la obra (2026-09-02)

**`BP_Director_Story.ShowPortrait()`** (sub 6 de `RunEnding`, con el VO 31) ahora llama a
**`BP_Card.Show()`** en vez de `BP_Portrait_SC.Show(WinnerRef)`. El timer de `PortraitHold` no se tocó, y
**se conserva el seteo de `PortraitRef`** por si otra parte del director lo usa.
✅ Verificado: el nodo `Show` tiene `self = BP Card Object Reference` (el read lo rotula como
`Class|BPSeqSlotSC|Show`, colisión de nombres).
🔑 **La carta no recibe la ameba por parámetro**: la resuelve sola con `SoulFromPicker` (la ganadora) y
`SoulFallback`. Menos acoplamiento que el panel viejo.

## 🌌 La constelación usa la carta (2026-09-02, 4ª tanda)

**`ShowFor(Soul, Index)`** es la puerta para un vecino: fija `SoulRef` con **esa** ameba y corre la misma
cadena que `Show()`, pero alimentando desde la entrada `Index` del archivo. `Show()` queda para el
retrato propio (resuelve la ganadora por su cuenta).

En [[BP_Constellation_SC]] la cirugía fue **de tres funciones, sin tocar `Focus`**:

| Función | Antes | Ahora |
|---|---|---|
| `CardFrom(ArchIdx, Soul)` | `Soul.ShowCard(calma, ritmo, respiración, título)` | `Card.ShowFor(Soul, ArchIdx)` |
| `DrawNeighbour(ArchIdx)` | `DrawNow` → reconstruía y colocaba el dibujo al lado de la ameba | **vaciada** (lo coloca la carta, en su hueco) |
| `BP_Portrait_SC.FeedMelody` | sembraba las esferas del vecino | **vaciada** (las siembra la carta) |

🔑 **`Focus` no se tocó a propósito.** Reescribirlo desde el `read` era el riesgo real: contiene un
`AI|Navigation|MovetoActor` que **puede ser el rótulo equivocado** del `MoveToActor` de la ameba, y
reescribirlo tal como lo imprime el read habría cambiado la llamada. Cirugía en las hojas, no en el tronco.

✅ **Verificado en PIE**: 12 vecinos sembrados, la constelación construye **19 estrellas**, y el ciclo de
debug recorre `datos del vecino 0 → 1 → 2 → 3 → 4 → 5…` con la carta re-alimentándose en cada uno.

### 🪤 El widget se recreaba y perdía la diagramación
Las etiquetas (`YOUR TRACE`, `CALM`…) **reaparecían** en la constelación aunque `CardLayout` las
colapsara: el `WidgetComponent` **crea su widget más de una vez**, y el segundo nacía sin diagramar
(gotcha §34 del proyecto). Un `CacheWidget` por Tick **no alcanzó**.
✅ **El arreglo definitivo: `CardLayout()` cuelga del `PreConstruct` del propio `WBP_Card`.** El widget
se diagrama **a sí mismo**, así que da igual quién lo cree o cuántas veces.

## ⚠ Pendientes
- ⬜ **`BP_Portrait_SC` quedó sin llamador** (sólo lo referencia `PortraitRef` del director, y su
  `FeedMelody` está vacía). Retirarlo, junto con los componentes `Card` y `OrbAnchor` de
  [[BP_ProtoSoul_SC]], **cuando Beltrán dé el visto**.
- ⬜ **Composición**: la carta (en 7640) queda **dentro de la nube de estrellas** (radio 983 alrededor
  del ojo), así que varias amebas se le cruzan por delante. Es decisión de autor: mover la carta,
  alejarla, o achicar el radio.
- ⬜ La ameba queda un poco corrida a la izquierda dentro de su hueco (ajuste de ancla).
- ⬜ Visor.

## 🧹 Higiene
Barrido de huérfanos con `scripts/clean_orphans.py` **tal cual**: **236 nodos borrados** con
`identical: true` en todos los grafos (130 en `OneOrb`, 38 en `CardFrom`, y los preexistentes de
`SpawnStar`/`DressStar`/`ForceHover`/`DrawNow`/`ShowIndex`).
🔴 **Confirmado: `write_graph_dsl` sobre una función que YA tiene cuerpo NO lo limpia** — deja el viejo
como isla huérfana, y el `read` no la muestra. Cada reescritura de una función hay que barrerla.

## ✅ Resuelto: el material
🟢 **`M_Card`** (`Core/Card/`) — unlit, opaco, two-sided, gris 0,55/0,57/0,60 por emisivo. Reemplaza a
`M_DoorSolid`, que estaba gobernado por `MPC_Room.RoomLight`: **la primera corrida salió toda negra**
porque la carta se apagaba con el fundido de sala. Era el riesgo #1 del plan y se confirmó en la práctica.

## 🪤 Dos trampas del MCP que costaron round-trips acá
1. **El nombre de la propiedad de visibilidad es `bHiddenInGame`, no `hiddenInGame`** (conserva la `b`),
   mientras que `castShadow` sí la pierde. No hay regla: se prueba y se verifica.
2. **La colisión de un componente NO se setea con `collisionEnabled` al tope**, sino por el subobjeto:
   `{"bodyInstance": {"collisionEnabled": "NoCollision"}}`. Y **`collisionProfileName` no es legible**
   desde `get_properties` al tope, pero sí adentro de `bodyInstance`.
3. 🔴 **Un error de `set_properties`/`get_properties` escapa del `try/except BaseException` del script**:
   el plugin lo agrega y lo devuelve como error del `call_tool` aunque el `run()` lo haya capturado. O
   sea que **el patrón `safe_script` no protege de esto** — el script igual corre entero, pero el
   resultado se pierde. Conviene pedir una sola propiedad dudosa por llamada.
4. 🔴🔴 **En una INSTANCIA del nivel, `set_properties` sobre un struct escribe SÓLO EL PRIMER CAMPO.**
   Medido: `drawSize {1600,900}` quedó **{1600, 500}**; `relativeScale3D {0.1156, 0.1156, 0.1156}` quedó
   **{0.1156, 1, 1}**; `relativeRotation` yaw 90 no entró. En el **CDO** el mismo `set_properties`
   escribe el struct **entero**. 👉 **La salida limpia es configurar el CDO y RECOLOCAR el actor**, para
   que la instancia nazca ya completa — no pelearse campo por campo.
   ⚠ Corolario: **un componente agregado al CDO después de colocar el actor nace con los defaults en esa
   instancia**, no con lo que dice el Blueprint (es la variante de "lo de la instancia le gana al BP").
5. ⚠ **Un `execute_tool_script` que falla NO siempre revierte lo que alcanzó a hacer.** Un intento con un
   tipo inválido creó igual 13 variables; el reintento las **duplicó con sufijo `_0`**. 👉 Antes de
   reintentar una tanda que falló, **listar el estado real** y limpiar.
6. ⚠ **`remove_function_graph` no libera el nombre en el acto**: recrear `Show` justo después devolvió
   **`Show_0`** (y el timer de `SetTimerByFunctionName("Show")` habría quedado colgado). Hay que borrar,
   **compilar**, y recién entonces volver a crear.
7. ⚠ **El `read_graph_dsl` rotula las llamadas a funciones propias con la clase equivocada** cuando otro
   BP tiene una función homónima: mostraba `Class|BPPortraitSC|Feed` para nodos que en realidad son míos.
   Se confirma con `get_node_infos`: si el pin `self` es **`Self Object Reference`**, es propio.

## Relacionados
[[BP_Portrait_SC]] (de donde se portan el widget y el motor de melodía; se retira en F6) ·
[[BP_Constellation_SC]] (el consumidor del final) · [[BP_ProtoSoul_SC]] (pierde el `Card` y el
`OrbAnchor`) · [[BP_SoulArchive_SC]] (la única fuente de datos)


---

## 2026-09-02 (5ª tanda) — los cinco arreglos de ritmo que pidió Beltrán

Tras la primera prueba en visor: *"va super, pero vamos a hacer un par de arreglos"*. Los cinco son de
**cuándo aparece y desaparece cada cosa** — la mecánica ya estaba.

| # | Pedido | Dónde se resolvió |
|---|---|---|
| 1 | *"el dibujo debe desaparecer antes de la carga de la ameba"* | **`BP_Director_Story.StashMyDraw`** → nueva `FadeMyDraw()` (`Sensor.FadeTo(0)`). Se apaga **en el mismo acto en que se archiva**, que es el instante exacto antes de la ceremonia. |
| 2 | *"el card está visible desde el inicio del nivel"* | **`Conceal()` en el boot** (`MaybeShowOnPlay`) + **`Reveal()`** al principio de `Show()` y `ShowFor()`. |
| 3 | *"tras el resultado debe desaparecer el card, y recién ahí la instrucción del corazón"* | **`ShowPortrait`** arma un 2º timer a **`HideCardNow`** en `max(0,2 ; PortraitHold − 1)`, o sea **1 s antes** de que el sub 7 diga el VO del gesto. |
| 4 | *"en la constelación el card no debe estar visible; solo con hover, y la ameba no se acerca, solo se agranda"* | `FocusPull` → **0** (dato, no código: el ancla queda sobre la estrella) + nueva **`GrowHovered()`** que escala el `FocusPoint` a `escala_del_spot × HoverGrow` (1,35). La carta la enciende `CardFrom` (`ShowFor`) y la apaga **`FadeDrawOut` → `HideCardPanel()`**, que ya corría en `Unfocus`. |
| 5 | *"el dibujo debe encajar completo, por el lado que tope primero"* | **`FitDraw()`** (abajo). |

🔑 **`ShowFor` ya NO mueve la ameba** (se le sacó `FitSoul`): en la constelación la estrella se queda en
su sitio y sólo crece. `Show()` (retrato propio) sí la mete en el hueco.
🔑 **Ni `RunEnding` ni `Focus` se tocaron.** Los dos tienen llamadas que el `read` rotula mal
(`Class|BPAlmaSC|MoveTo`, `AI|Navigation|MovetoActor`); reescribirlos desde el read habría cambiado la
llamada real. Todo se enganchó en funciones **hoja**: `StashMyDraw`, `ShowPortrait`, `CardFrom`,
`FadeDrawOut`.

### `FitDraw()` — el encaje proporcional
```
s = DrawMargin × min( anchoHueco / anchoDibujo , altoHueco / altoDibujo )
      anchoHueco = SlotDraw.scale.X × 100      anchoDibujo = 2 × max(extent.X, extent.Y)
      altoHueco  = SlotDraw.scale.Z × 100      altoDibujo  = 2 × extent.Z
```
Toma **el lado que topa primero**: dibujo más alto que ancho → manda el alto; más ancho que alto → manda
el ancho. `DrawMargin` (0,92) es el aire que queda contra el borde. ✅ Medido: escala **0,837** contra el
0,30 fijo de antes. 🗑️ `DrawScale` quedó sin uso.

🔴 **El extent hubo que cablearlo A MANO.** `Collision|GetActorBounds` tiene dos salidas y **el DSL sólo
sabe tomar la primera** (`Origin`) — por eso el primer intento daba escala 0. La segunda (`BoxExtent`) se
conectó por **cirugía** (`create_node` de `SetDrawExtent` + `connect_pins` al pin de salida 1), insertada
en la cadena exec entre `SetDrawOrigin` y `FitDraw`.

### ⚠ Ajuste que apareció al medir: `SoulSize` 0,40 → **0,12**
La ameba **desbordaba su hueco** en la captura. La fórmula del tracker de [[BP_ProtoSoul_SC]] es
`radio visible = 83 cm × (Size / RingSizeRef)` con `RingSizeRef` 0,3 — o sea **277 × Size**, no 83.
Con 0,40 los anillos medían **2,2 m** de diámetro. Para un hueco de 67 cm: `Size = 67 / (2 × 277) ≈ 0,12`.


---

## 2026-09-02 (6ª tanda) — 🔴 el bug que hizo fallar los tres arreglos anteriores

Beltrán probó y **nada funcionó**: la carta seguía visible desde el inicio, el dibujo no se iba, y **no
pudo atraer la ameba al corazón** — lo que lo dejó sin poder seguir la obra. Una sola causa raíz explica
los dos primeros, y es un error de escritura de DSL:

### 🔴🔴 `(Rendering|SetActorHiddenInGame true)` escribió **`false`**
El pin `self` de una función de Actor **existe aunque se omita el target**, y **se come el primer
argumento posicional**. Al pasar `true` como posicional, fue a parar al pin `self` (de tipo objeto, que lo
descartó) y **`bNewHidden` quedó en su default `false`**. Resultado: `Conceal()` **mostraba** la carta en
vez de ocultarla — y como `Hide()` termina en `Conceal()`, la carta tampoco desaparecía nunca.

👉 **Regla: en funciones de Actor sobre `self`, los argumentos van por KEYWORD** (`:bNewHidden true`),
nunca posicionales. Y **después de escribir, leer el grafo**: el `read` lo mostraba clarísimo
(`SetActorHiddenInGame false`) y no se miró.
✅ Arreglado por cirugía (`set_pin_value` del pin 2 a `true`) y **verificado en captura**: con PIE de 8 s,
la carta ya no aparece.
✅ Se auditaron **todos** los literales booleanos de las funciones de este BP (`PlaceMelody`, `OneOrb`,
`Show`, `ShowFor`, `Hide`, `FitDraw`, `PlaceDraw`, `ShowLabels`, `FeedNow`): **el resto estaba bien** —
el fallo sólo ocurre cuando se omite el target y el valor va posicional.

### 🔴 La ameba quedaba PRESA de la carta
`FitSoul` le escribe a la ameba su `TargetRef` apuntando a un `TargetPoint` que **cuelga de la carta**, y
`AnchorStep` la **re-attachea cada frame**. `StartCarry` sí llama a `AnchorRelease()`, pero eso sólo hace
`DetachFromActor` — **no limpia `TargetRef`**, así que la ameba volvía al hueco al frame siguiente y el
gesto de llevarla al corazón era imposible.

✅ **`ReleaseSoul()`** (nueva, la llama `Hide()`): guarda en `SoulHome` de dónde venía la ameba (leído con
`GetTargetRef` **antes** de pisarlo, en `FitSoul`), y al ocultar la carta le **devuelve su ancla
original**, llama `AnchorRelease()` y **destruye el `TargetPoint`** que había creado (`SoulAnchorTP`).

### El dibujo: estaba enganchado demasiado tarde
`StashMyDraw` lo llama **`BeginEnding`**, que corre **después** de la carga. Y el cierre de etapa
(`StepTimeDone` → `Sensor.SetStage(-1)` → `DrawOff`) **deja el canvas a propósito** (era la firma).
✅ `FadeMyDraw()` se insertó **por cirugía dentro de `StepTimeDone`**, entre `SetStage(-1)` y
`CloseStageFX` — o sea en el cierre de la etapa, **antes** de la ceremonia de carga.

### Lección de proceso
Los tres arreglos se entregaron **sin correr una sola vez**. El `read_graph_dsl` posterior habría cazado
el `false` en dos segundos. **Verificar el valor efectivo, no la declaración** — la regla ya estaba
escrita en este mismo repo.


---

## 2026-09-02 (7ª tanda) — la mecánica completa, dicha por Beltrán

> Termino de dibujar los metros de Surrounding → **el dibujo queda unos segundos y desaparece** →
> **recién ahí** se desprende la ameba y arranca la carga → aparece la tarjeta **con la melodía sonando**
> → **desaparece la tarjeta** y puedo apuntar mi ameba para atraerla al corazón → cuando cumple el tiempo
> se va y aparece la constelación → con los rayos, **hover sobre una ameba**: esa **crece en su sitio** y
> **frente a mí aparece su card** — la ameba **se duplica** (existe en la constelación Y en su card) →
> **sin hover**: se va la tarjeta y la ameba vuelve a su tamaño. Igual para todas.

### Los cuatro fallos de esta ronda y su causa real

| Fallo | Causa | Arreglo |
|---|---|---|
| **La melodía no sonaba** | `BP_SoundOrb_SC.PulseOnBeat` **sólo suena si `Placed`** (`if Placed → SetVolume, else → Play`), y la carta nunca lo marcaba. El panel viejo sí lo hacía. | `SetPlaced(true)` en `OneOrb`. |
| **El dibujo nunca se veía en la carta** | `DrawExtent` llegaba en **(0,0,0)** → escala **6164** → el canvas se iba a **3 km** (`quedo en X=317034`). El cableado del `BoxExtent` es **cirugía**, y **reescribir `PlaceDraw` la borró** (dos veces). | Cirugía rehecha **+ `Clamp(0,01 … 3,0)`** en `FitDraw`, para que un extent nulo no pueda volver a mandarlo lejos. ✅ Verificado: extent 121×121×60, escala 0,83. |
| **El dibujo no se iba al cerrar la etapa** | El fade dependía de `StepTimeDone`, que corre **sólo si `WaitFor == "time"`**. Si la etapa cerraba por otro camino, nunca se apagaba. | **`FadeTo(0)` insertado por cirugía en `BP_Sensor_Soul.DrawOff`**, que corre en **cualquier** `SetStage(≠5)`. Es la raíz: se apaga siempre. |
| **El dibujo seguía visible tras irse la tarjeta** | `Hide()` no tocaba el fade. | `Hide()` pone **`MPC_Draw.DrawFade = 0`**. |

### 🔴 Corrección de un diagnóstico MÍO que era falso
Sostuve que *"el `TargetRef` de la carta impedía llevarse la ameba al corazón"*. **Es falso**, y hay que
saberlo para no volver a perseguirlo: `StepTravel` está gateado por **`not bCarried`** *y* por un
**`IsValid(TargetRef)`**, así que ni el ancla bloquea el carry, ni un `TargetRef` nulo rompe nada.
👉 Dos consecuencias: (a) **poner `TargetRef` a null es seguro** y deja a la ameba **quieta donde está**
— que es justo lo que pide la mecánica; (b) si el gesto sigue fallando, **la causa está en
[[BP_SoulPicker_SC]], no en la carta**.

✅ `ReleaseSoul()` ahora **siempre** suelta: `SetTargetRef(NoAnchor)` — una variable objeto que **nunca se
asigna**, o sea null. (Antes exigía `IsValid(SoulHome)`, y si la ameba no tenía ancla previa **no soltaba
nada**.) Tampoco la manda de vuelta a su punto viejo, que podía estar en otra sala.

### La constelación: la ameba se DUPLICA
`ShowCopyFor(Index, Mesh, Col, Rings)` + **`SpawnCardSoul()`**: la carta **spawnea su propia copia** de
`BP_ProtoSoul_SC` en el hueco (con la malla del `MeshBank`, el color y los anillos de esa entrada, igual
que `DressLook`), y `ClearCardSoul()` la destruye al ocultarse. **La ameba real nunca se toca**: se queda
en la constelación y sólo crece (`FocusPull = 0`, `HoverGrow = 1,35`).

⬜ **Sin verificar en visor**: el gesto del corazón y el tramo dibujo→carga. Hay prints sembrados
(`CARTA/DRAW:`, `CARTA: ameba LIBRE…`, `STORY: el dibujo se disuelve…`) para que la próxima corrida diga
qué pasa en vez de suponerlo.


---

## 2026-09-02 (8ª tanda) — el log de Beltrán, leído

El log traía **un error repetido en bucle**, que era la punta del ovillo:
```
Attempted to access TargetPoint_43 via property SoulAnchorTP,
but TargetPoint_43 is not valid (pending kill or garbage)
```

### 🔴 Por qué spameaba: `Hide()` corría CADA FRAME
`Unfocus` de [[BP_Constellation_SC]] llama `FadeDrawOut` → `HideCardPanel` → `Card.Hide()`, y eso ocurre
**mientras no hay hover**, o sea todos los frames. `ReleaseSoul` destruía el `TargetPoint` y **dejaba la
variable apuntando al actor muerto**, así que el frame siguiente lo tocaba de nuevo.

✅ Dos arreglos, ambos necesarios:
1. **`KillAnchorTP()`**: **limpia la variable ANTES de destruir** (`SetSoulAnchorTP(NoAnchor)` y recién
   entonces `IsValid` + `DestroyActor`). Mismo patrón en `ClearCardSoul`.
2. **Candado en `Hide()`**: `if bShown → HideNow()`. Ya no repite trabajo si la carta está oculta.
👉 **Regla**: al destruir un actor guardado en una variable, **limpiar la variable en el mismo acto**;
si no, cualquier lectura posterior es un `pending kill`. Y una función de "apagar" que puede llamarse
desde un Tick necesita su propio candado.

### El desorden de la constelación: un `FocusPoint` COMPARTIDO
`Focus` hacía `MoveToActor(HoverRef, FocusPoint)` con **un único `FocusPoint` para todas**. Al pasar el
hover a otra estrella, el punto se mudaba y **la ameba anterior lo seguía hasta allá** — de ahí que
"algunas se movieron de un lado para otro".
✅ **Se eliminó el `MoveToActor` de `Focus`** (cirugía: puente `PullAnchor → CardFrom` y borrado del nodo).
Ninguna ameba viaja nunca más.
✅ **`GrowHovered` ahora escala el SPOT de esa ameba**, no un punto compartido: como `AnchorStep` saca el
`Size` del `Scale3D` de su `TargetRef`, la ameba **crece exactamente donde está**. `ShrinkPrev()` guarda
la escala original (`GrownSpot`/`GrownScale`) y la restaura — se llama al entrar (antes de crecer la
nueva) **y** al salir del hover, así que el hover es instantáneo y reversible para todas.

### El dibujo se disolvía DURANTE la carga
El fundido dura `DrawFadeTime` (2,5 s) pero `CloseStageFX` disparaba la carga en el mismo frame.
✅ **`CloseAfterDraw()`**: en Surrounding (`Room >= 5`) arma un timer de **`DrawOutWait` = 3,5 s** hacia
`CloseStageFX`; en el resto de las salas cierra directo, sin cambiar el ritmo de la obra. `StepTimeDone`
ya no llama a `CloseStageFX` (lo hace esta función).
👉 Secuencia final: **termina el dibujo → se disuelve (2,5 s) → 3,5 s → recién ahí la carga**.

### Apuntar la ameba costaba
`BP_SoulPicker_SC`: **`AimDwell` 1 s → 0,5 s** y **`AimConeDeg` 20° → 25°** (CDO + instancia).
⚠ En el primer intento lo bajé a 18° por error, que lo hacía **más** difícil; corregido a 25°.


---

## 2026-09-02 (9ª tanda) — 🔴🔴 la obra quedó TRABADA, y el log lo dijo en una línea

```
STORY: sala 5 paso 3 espera: time
STORY: el dibujo se disuelve; la carga espera      ← y ahí termina el log
```

### La causa: un timer de CERO segundos
`CloseAfterDraw` armaba `SetTimerByFunctionName("CloseStageFX", DrawOutWait)`. **`DrawOutWait` es
instance-editable, y las instance-editable NACEN EN CERO en el actor ya colocado** — la trampa más
repetida de este repo, y la volví a pisar. **Un timer con tiempo ≤ 0 no dispara nunca**, así que
`CloseStageFX` no se llamó jamás y la obra se quedó esperando para siempre.

Y era mi cambio el que la había vuelto crítica: en la tanda anterior **saqué `CloseStageFX` de
`StepTimeDone`** y lo puse detrás de ese timer. Antes el cierre era directo; al moverlo, un valor en cero
pasó de ser cosmético a **bloquear la obra entera**.

✅ Dos arreglos, y el primero es el que importa:
1. **`Max(2.5, DrawOutWait)`** en el nodo del timer: aunque el valor esté en cero, siempre dispara.
2. `DrawOutWait = 3,5` escrito **en la instancia** del director.

👉 **Regla dura: cuando un timer decide si la obra avanza, su duración va SIEMPRE dentro de un `Max(…)`.**
Un dato en cero no puede tener permiso de frenar el guión.

### El dibujo tampoco se apagaba, con dos caminos llamando al fundido
`DrawOff` (sensor) y `DoFadeDraw` (director) hacen los dos `FadeTo(0)`, y `FadeTo`/`FadeStep` están bien
construidos — aun así el dibujo seguía visible.
✅ **Se dejó de depender del fundido**: `HideDrawNow()` (director) fuerza `MPC_Draw.DrawFade = 0` **y
oculta el actor canvas** (`SetActorHiddenInGame`), armada por `DoFadeDraw` a los 2,5 s. El fundido sigue
corriendo para que se vea bonito, pero **la desaparición ya no depende de que funcione**.
✅ `FitDraw` hace `SetActorHiddenInGame(canvas, false)` al encajarlo en la carta, así vuelve a verse.

⚠ **Ojo con `SetActorHiddenInGame`**: con el target **explícito** el literal entra bien
(`(… _canvas true)`), pero **omitiendo el target el `self` se come el valor** (ver 6ª tanda). Siempre
con target explícito y verificando el `read`.


---

## 2026-09-02 (10ª tanda) — el gesto SÍ funcionaba; el problema era a dónde volvía

El log de Beltrán, otra vez decisivo:
```
CARTA: ameba LIBRE y quieta  →  se oculta la tarjeta  →  STORY: sala 5 paso 7 espera: shared
PROTO: soltada del ancla  →  hover habilitado  →  agarrada con la IZQUIERDA  ×3
PROTO: soltada, vuelve suave a su punto
```

🟢 **El gesto de agarrar la ameba nunca estuvo roto** — el log lo dice tres veces. Lo que fallaba era el
**regreso**: `ReleaseSoul` le dejaba el `TargetRef` en **null**, y cuando el carry termina el alma
*"vuelve suave a su punto"*… que no existía. De ahí *"se movió no tengo idea dónde"*.

✅ **El punto ya no se destruye ni se anula.** `ReleaseSoul` ahora:
1. **desprende el `TargetPoint` de la carta** (`DetachFromActor KeepWorld`) → queda flotando **en el sitio
   del hueco**, que es donde el usuario está mirando la ameba;
2. lo **agranda a `FreeSize`** (0,30 = `RingSizeRef`) para que, al irse la carta, la ameba recupere su
   tamaño natural en vez de quedar en el 0,12 del hueco;
3. **conserva el `TargetRef`**, así el alma tiene a dónde volver si se la suelta.

👉 **La lección**: no alcanza con "soltar" — hay que preguntarse **a dónde vuelve** lo que se suelta.
Un `TargetRef` nulo no es neutro: es un destino inválido que el sistema igual intenta usar.

### 🔴 `FreeSize` nació blindado, no como `DrawOutWait`
`Max(0,25 ; FreeSize)` en el nodo **y** el valor escrito en la instancia. Es la tercera variable
instance-editable de esta sesión que habría nacido en cero (`MelodySteps`, `DrawOutWait`, `FreeSize`), y
la primera que no llegó a romper nada.
👉 **Regla ya sin excusas: toda variable instance-editable que participe de un cálculo va dentro de un
`Max(…)`, y se escribe en la instancia en el mismo movimiento en que se crea.**


---

## 2026-09-02 (11ª tanda) — por qué la ameba "se venía y se devolvía"

Log de Beltrán:
```
PICKER: modo compartir - apuntar la ameba con cualquier mano, sin gatillo
PICKER: enganchada por gesto con la IZQUIERDA - viaja a la mano
PROTO:  agarrada con la IZQUIERDA
PROTO:  soltada, vuelve suave a su punto          ← acá se rompe
STORY:  sala 5 paso 7 espera: shared              ← y el guión espera para siempre
```

### 🔴 El gatillo soltaba la ameba en un modo que es SIN gatillo
`BP_SoulPicker_SC.ReleaseGrab` está cableado a los eventos **`IA_Shoot_Left/Right`** (soltar el gatillo)
en el EventGraph, y su cuerpo era:
```
if bShareMode  →  Winner.EndCarry()
```
O sea: **justo en el modo por gesto, tocar el gatillo la devolvía**. Es residuo del modo anterior
(agarrar/soltar con gatillo) que quedó vivo cuando F3 pasó el compartir a **gesto por ángulo, sin
gatillo**. El usuario apretaba el gatillo por reflejo y perdía la ameba antes de llegar al pecho.

✅ **Arreglo (una condición):** `if (bShareMode AND NOT bAimHooked) → EndCarry`. Si la enganchó el gesto,
el gatillo ya no la suelta; el único modo de completar es **sostenerla 3 s en la zona del pecho**
(`ShareHold` 3 · `ShareRadius` 30 cm, ambos correctos en el CDO).

⚠ **Nombres**: los getters de bools de este BP son **`Variables|Z-Estadointerno|GetShareMode`** y
**`Variables|Default|GetAimHooked`** — ni `GetbShareMode` (lo que imprime el read) ni
`Variables|Default|GetShareMode`. Se resolvió listando `Variables|` con `find_node_types`.

### El enganche automático
Es **por diseño** (gesto por ángulo, sin gatillo), pero venía demasiado inmediato con lo que yo había
puesto. Quedó en **`AimDwell` 0,7 s** y **`AimConeDeg` 22°** — a mitad de camino entre el original
(1 s / 20°) y lo que había dejado (0,5 s / 25°).

### 🟢 Lo que el log confirmó que YA funciona
Dibujo que desaparece antes de la carga · carta que aparece con sus datos · carta que se va ·
ameba liberada y agarrable. La cadena entera del cierre corre; faltaba sólo este candado.


---

## 2026-09-02 — 🔴 EL FINAL SE SIMPLIFICA (decisión de Beltrán)

> *"Cambié de opinión. Vamos a eliminar la mecánica de atraer al corazón y la de revisar los datos de
> las otras amebas."*

### El flujo nuevo, entero
| Paso | Qué pasa |
|---|---|
| 1 | Termina el dibujo → **desaparece** → arranca la carga |
| 2 | Al terminar la carga: **aparece la carta** y **la ameba VIAJA suave** hasta su hueco |
| 3 | La constelación aparece, pero **la carta y la ameba se quedan donde están** — la ameba **nunca** se va a la constelación |
| 4 | **Un minuto** de contemplación: la constelación es **sólo visual** (sin beam, sin apuntar, sin hover) |
| 5 | Todo se apaga → fundido a negro → **restart del nivel** |

### 🔑 El viaje, no el salto
*"No debe desaparecer y aparecer. Se debe mover, tal como sucedía con el HUD."*
`FitSoul` ya no escribe el `TargetRef` y deja que el attach la teletransporte: ahora hace
**`SetTargetRef(spot)` + `StartTravel()`**, que es lo que `MoveTo` usa por dentro — viaje con
**smoothstep** por `TravelStep` y `TravelTime`. Es el mismo viaje del HUD y de la ceremonia.
⚠ `MoveTo(tag)` no se pudo usar directo: exige que el punto tenga un **tag**, y `SetTags` sólo opera
sobre `self` (no se le pueden poner tags a un actor spawneado desde otro Blueprint). `StartTravel` va al
mismo lugar sin ese rodeo.

### `RunEnding` quedó en TRES pasos (era de 6 a 13)
```
sub 6 : Say(VOEnd1) + ShowPortrait()      → espera timer (PortraitHold 20 s)
sub 7 : SaveMyPortrait() + ShowConstellation() → espera timer (ConstHold 60 s)
sub 8 : FinaleOut()  → fundido + ReloadLevel
```
🗑 **Eliminados**: el gesto de compartir (VO32 + `Picker.Rearm` + espera `"shared"`), el viaje de la
ganadora a `soul_pick_6` (**lo que mandaba la ameba a la constelación**), `StartExplore`/`StopExplore`
y el VO33.
✅ **La carta ya no se oculta**: `ShowPortrait` dejó de armar `HideCardNow`.
✅ **La constelación queda muda**: `BeamTick` está gateado por `bExploring`, que ya nadie enciende, y las
flags de debug (`bDebugExploreOnPlay`, `bDebugCycle`) quedaron en `false`.

⚠ Queda **dormido pero intacto** todo el sistema de hover por beam de la tanda anterior
(`ScanOne` por `BeamHitActor`, `MakeHittable`, `bExploring` del sensor). Si algún día vuelve la
exploración, se enciende llamando `StartExploring` — no hay que reconstruir nada.


---

## 2026-09-02 — la ameba "renacía" antes de viajar

**El síntoma**: al aparecer la carta, la ameba *"volvía a nacer desde escala 0 y ahí se movía"*.

**La causa**: `FitSoul` llamaba **`Reveal()`** antes del viaje. `Reveal` dispara el evento `Appear` de
[[BP_ProtoSoul_SC]], y ese evento **pone `Body.RelativeScale3D` en (0,0,0)** y anima el crecimiento
(`bAppearing` + `StepAppear`). Es el nacimiento del alma — correcto cuando aparece por primera vez, y
completamente fuera de lugar cuando el alma **ya está viva y a la vista**.

✅ **Arreglo: sacar el `Reveal`.** En este punto del guión la ameba viene visible de la etapa anterior;
lo único que tiene que hacer es **viajar** (`SetTargetRef` + `StartTravel`).

👉 **Regla: `Reveal()`/`Appear` es "nacer", no "mostrarse".** Llamarlo sobre algo que ya está en escena
lo reinicia desde escala 0. Si el objeto ya existe, sólo hay que moverlo.
