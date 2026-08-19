# BP_SoulRing_SC + M_SoulRibbon_SC — el anillo como TRAZO DIBUJADO

> `/Game/SoulCharger/Core/ProtoSoul/` · creado 2026-08-19 · **una instancia de prueba** en `MapsV2/L_SoulCharger` (persistente) en `(0, 0, 150)`, que es **el interior del Hall** — puesta ahí para poder mirarla en contexto.
> 🔴 **2026-08-19 — LA OBRA YA NO USA ESTE BLUEPRINT.** Los 4 anillos de la ameba se migraron a **`ProceduralMeshComponent` nativos dentro de [BP_ProtoSoul_SC](BP_ProtoSoul_SC.md)**, con el mismo material y el mismo algoritmo. Esto queda como **banco de pruebas suelto** (la instancia del Hall) para iterar el trazo aislado, y como documentación del diseño del material.
> **Estado: 🟢 el diseño del trazo está aprobado por Beltrán. Falta el visor.**

## 🧭 Por qué se migró a componentes nativos
El `ChildActorComponent` causó **cinco bugs en una tarde**, todos de la misma indirección (componente → template → actor hijo): `ChildActorClass` nulo en las instancias · variables nuevas nacidas en cero · `ChildActorTemplate` nulo — **y que vuelve a nulo en cada compile del BP hijo** · actores hijos rancios ya spawneados en el editor que PIE duplica tal cual · el MID del Construction Script perdido al duplicar.
👉 **Ninguno de esos modos de falla existe con un componente nativo.** El costo de la migración fue mecánico porque para entonces la forma ya vivía en un CDO y los colores en un array del padre — exactamente la estructura que quedó después.

---

## Qué es
La exploración del **anillo de carga** de [[BP_ProtoSoul_SC]] (uno por etapa: entering azul · recognizing rojo · loving morado · attracting naranja; el de surrounding lo pinta el usuario). Pedido de Beltrán: *"como un ribbon alrededor del mesh, orgánico, ojalá vivo con algo de movimiento; tiene que partir en 0 e ir construyéndose hasta envolver al mesh"* y *"se tiene que ver como mi refe, como si fuera un trazo dibujado que va respirando"*.

**Decisiones que fijó Beltrán antes de construir:** el anillo **orbita** (no envuelve, eso queda para después) · **comparte el flotar de la ameba** y algo de su deriva · **uno por etapa, acumulando**.
🗑️ **Los `Ring0..Ring4` de `BP_ProtoSoul` (esqueleto viejo) están DESCARTADOS** — eran planos con un aro procedural y Beltrán los rechazó de plano. De `M_SoulRing` no se reusó nada.

## 🧭 Por qué NO es un ribbon de Niagara
Se evaluó y se descartó con razones concretas, no por gusto:
- **Los bounds del ribbon renderer sólo consideran el ANCHO de la cinta, no el largo** (bug documentado de Epic) → el sistema queda con bounds minúsculos y el culling **lo destruye al primer frame**. Ya nos costó una sesión en [[BP_AimBeam]].
- **El ribbon renderer no admite GPU sim** → 4-5 sistemas simulando en CPU todo el tiempo.
- **`fx.Niagara.QualityLevel` está capado a [0,1] en Android**: un emitter autorado en High/Epic anda en PIE y **está muerto en el APK, sin error**.
- Y el que decide: **no se ve en el editor sin darle Play**. Toda la arquitectura de Alma y la proto ameba existe para poder autorar mirando.

💡 **Dónde SÍ entra Niagara más adelante:** motas soltándose en la punta que dibuja. Acento, no anillo.

## La geometría: cinta plana con torsión, generada en el Construction Script
`ProceduralMeshComponent` (`Ribbon`) construido por el CS → **se ve y se re-genera en el viewport al tocar cualquier perilla**, sin Play.

- El recorrido es un **rollo**: el ángulo va de 0 a `Turns × 360°`, así que con `Turns = 2.5` son **2 vueltas y media que se superponen** — de ahí sale el look de trazos cruzados de la referencia. No es un aro perfecto y no debe serlo.
- Por muestra se emiten **2 vértices** (los dos bordes de la cinta), con `UV0.x = t` (0→1 a lo largo del trazo) y `UV0.y` = 0/1 (a lo ancho). **Esa UV es lo que hace que todo lo demás sea un nodo.**
- **La torsión** (`Twist`) rota la dirección del ancho entre "acostada en el plano" y "de canto" a lo largo del recorrido: es lo que hace que se lea 3D y como pincelada, y no como una manguera.
- 🔴 **En `Norms` no va la normal real, va la DIRECCIÓN DEL ANCHO.** El material es unlit, así que la normal no se usa para sombrear y queda libre como almacenamiento. El material la lee con `VertexNormalWS` para saber hacia dónde engordar o adelgazar el trazo. **Es el truco que permite que el grosor viva en el shader.**
- Costo medido: `Segments = 220` → **442 vértices y 440 triángulos** por anillo. Somos fill-rate bound, no geometry bound: 5 anillos son ruido.

## El material `M_SoulRibbon_SC` — 77 expresiones, cero texturas
**Unlit · Additive · TwoSided · `FloatPrecisionMode = Full`** (por la trampa de fp16 en degradados animados).

🔴 **Additive por una razón estética, no sólo por barato:** en la referencia, **donde los trazos se cruzan brilla más**. Eso lo da el additive y no lo puede dar un opaco. Y de yapa el additive es **order-independent**, así que la trampa de los parches triangulares que mordió a `M_Alma` (translucidez a dos caras ordenada por índice) **no aplica** — por eso acá `TwoSided` es seguro.

| Capa | Cómo |
|---|---|
| **Crecimiento** | `reveal = saturate((Reveal − U) / RevealSoft)`. `Reveal` 0→1,05 y el trazo **se dibuja solo**. ⚠ El 1,05 no es un error: con 1,0 exacto el último gajo no se enciende. |
| **Punta que ilumina** | `tip = saturate(1 − |Reveal − U| / TipWidth)`, sumada al emisivo. **Ahí vive lo elegante**: la punta brilla mientras traza. |
| **Respiración** | `breath = 1 + BreathAmount · sin(U·BreathFreq + Time·BreathSpeed + PhaseSeed)` → el grosor engorda y adelgaza a lo largo del trazo. |
| **Pincelada** | `taper = sin(U · 0,5)` → **el trazo nace y muere en punta**, como una pincelada con presión. |
| **Serpenteo** | otra suma de senos desplazando sobre la dirección del ancho → el trazo ondula, no es un círculo perfecto. |
| **Flotar** | **3 senos de `Time` con razones no enteras (1 : 0,73 : 1,37)** × `FloatAmount`. Misma receta y mismos nombres de parámetro que la ameba. |
| **Borde suave** | `saturate((1 − |side|) / EdgeSoft)` a lo ancho → el trazo se difumina en los bordes en vez de cortarse. |

**El grosor se aplica por WPO**, no por máscara: `offset = Normal · side · HalfWidthBaked · (widthFactor − 1)`. Con `widthFactor = 0` los dos bordes colapsan sobre la línea central → **la parte no dibujada son triángulos degenerados**, sin alpha test.
⚠ **`HalfWidthBaked` tiene que valer `Width / 2`** — el CS lo empuja solo, pero si alguien toca el material a mano y los desalinea, el trazo nace con el grosor equivocado.

## Perillas (todas instance-editable, categoría *A - Trazo*)
| Variable | Default | Qué mueve |
|---|---|---|
| `Radius` | 30 cm | Radio de la órbita. |
| `Turns` | 2,5 | **Cuántas vueltas superpuestas.** La perilla del look "varios trazos". |
| `Segments` | 220 | Resolución del trazo. |
| `Width` | 2,2 cm | Ancho de la cinta. |
| `RadiusJitter` / `JitterFreq` | 0,10 / 3,0 | Que el radio no sea constante → el aro deja de ser perfecto. |
| `Rise` / `RiseFreq` | 4 cm / 2,0 | Desviación fuera del plano de la órbita. |
| `Twist` | 1,5 | Vueltas de torsión a lo largo del trazo. **La palanca de la tridimensionalidad.** |
| `Reveal` | 1,05 | 🔴 **Scrubbeable en el panel de detalles: se ve dibujarse en el viewport, sin Play.** |
| `Color` · `PhaseSeed` | azul · 0 | Color del trazo · corrimiento de fase (dos anillos nunca sincronizados). |
| 🆕 **`FloatScale`** | 0,35 | 🔴 **Cuánto del flotar de la ameba toma el anillo.** 0 = quieto · 1 = igual que el cuerpo. |
| 🆕 `WobbleAmount` | 2,0 cm | Cuánto serpentea el trazo sobre sí mismo. **Es un movimiento distinto del flotar** — ver abajo. |

### 🎚️ Los tres movimientos son independientes — no confundirlos al bajar "el movimiento"
Beltrán reportó *"la flotación está muy intensa en los anillos"*. Hay **tres** fuentes y se bajan con perillas distintas:

| Se ve como | Perilla |
|---|---|
| El anillo **entero deriva** como un bloque (compartido con la ameba) | **`FloatScale`** |
| El **trazo serpentea** sobre sí mismo, como agua | `WobbleAmount` |
| El **grosor** engorda y adelgaza | `BreathAmount` (por ahora sólo en el material) |

💡 **Por qué el mismo flotar se ve MÁS intenso en el anillo que en el cuerpo:** son los mismos 4-6 cm, pero desplazar un **trazo fino** se lee muchísimo más que desplazar un blob de 30 cm. La intensidad percibida no escala con el tamaño del objeto sino con lo delgado que sea. Por eso el default de `FloatScale` es 0,35 y no 1.

🔴 **`FloatScale` en vez de un `FloatAmount` propio, a propósito:** el pedido era *"comparten el valor de flotar y un poco su deriva"*. Con un multiplicador el anillo mantiene **la misma dirección, la misma fase y el mismo ritmo** que el cuerpo — sólo se mueve menos. Con un `FloatAmount` independiente se podrían desincronizar y dejarían de leerse como un solo objeto.

La inclinación del anillo **es la rotación del actor** (hoy roll 28°, pitch 12°), no una variable.

## 📐 `ScaleComp` — el trazo tiene que ser una MINIATURA, no un trazo gordo achicado
Beltrán, cuando el alma se va a la cabeza: *"los bordes son gruesos y duros … debería verse exactamente como una miniatura del que vemos en tamaño normal"*.

🔴 **La causa: el WPO se suma en ESPACIO DE MUNDO, o sea DESPUÉS de la escala del objeto.** Escalar el actor achica la **geometría**, pero `HalfWidthBaked`, `WobbleAmount` y `FloatAmount` siguen siendo centímetros absolutos. A escala 0,167 el trazo queda **6× más ancho de lo que corresponde** → grueso, duro, y el serpenteo desproporcionado.
✅ **Arreglo: multiplicar TODO el WPO por `ScaleComp`** (parámetro escalar, default 1) justo antes de la salida. Un nodo.

**Y el anillo calcula su propio `ScaleComp`, no se lo pasa nadie** — `SyncScale()` en el Tick:
```
ScaleComp = WorldScale.x / ScaleRef        (ScaleRef = la WorldScale capturada la 1a vez)
```
🔴 **Por qué dividido por `ScaleRef` y no la escala de mundo pelada** (que fue el primer intento, y estaba mal): cada anillo tiene **su propia escala de componente** (1,0 / 1,18 / 1,36 / 1,54) para diferenciar radios. Con la escala pelada, el anillo 3 habría nacido con el trazo 1,54× más ancho que el 0 — cambiando el look que Beltrán ya había aprobado. Normalizando contra la escala **autorada**, `ScaleComp = 1` para los cuatro en tamaño normal y sólo baja cuando el `RingRoot` los achica de verdad.
💡 Ser el anillo quien se compensa solo lo hace **inmune a quién lo escale**: sirve igual dentro de la ameba, suelto en el nivel, o adentro de cualquier cosa futura.
⚡ Y sólo empuja al material **cuando el valor cambia** (`ScaleLast`), no cada frame.

✅ **Medido en PIE:** en tamaño normal `ScaleRef` = 1,0/1,18/1,36/1,54 y `ScaleLast = 1` en los cuatro (look intacto). Forzando `Size = 0,05`, el `RingRoot` cae a 0,1667 y los cuatro `ScaleLast` van a **0,1667** — el trazo se achica en la misma proporción que la geometría.

## 🎬 El dibujado en runtime (2026-08-19)
En el editor `Reveal` se scrubbea a mano; **en Play lo anima el BP**. Beltrán: *"al ponerle play ya aparece completo"* — faltaba justamente esto.

| Pieza | Qué hace |
|---|---|
| **`Draw()`** | 🔴 **El punto de entrada público.** Pone `DrawT` y `Reveal` en 0 y arranca. Es lo que va a llamar la ceremonia al cerrar una etapa. |
| **`StepDraw(DT)`** (Tick) | Avanza `DrawT` **linealmente** en `DrawTime` segundos y de ahí saca `Reveal` con **`Ease(EaseOut, 0 → 1,05)`**. |
| **`PushReveal()`** | El único lugar que empuja `Reveal` al material. |
| **`MaybeLoop()`** | Si `LoopDelay > 0`, re-dispara `Draw` con un timer. **Es andamio de autoría**: permite mirar el trazo dibujarse una y otra vez sin reiniciar el Play. En la obra va en 0. |

🚨 **`LoopDelay` y `bDrawOnStart` viven en TRES lugares y el que manda es el template.** Beltrán reportó *"se están loopeando, el anillo vuelve a crearse constantemente"* con el CDO del anillo ya en `LoopDelay = 0`: los valores de prueba (`1,5` y `true`) habían quedado en los **`ChildActorTemplate` de la ameba**, que pisan al CDO. 👉 **Al cambiar un default de `BP_SoulRing_SC` hay que revisar también los 4 templates de `BP_ProtoSoul_SC`** — o migrar a componentes nativos y que el problema no exista.

💡 **Por qué el tiempo va lineal y la curva se aplica DESPUÉS:** así `DrawTime` significa segundos de verdad y el final es exacto (`DrawT` clampeado a 1), mientras que la curva es puramente estética y se cambia sin tocar la duración. **EaseOut** es lo que hace que el trazo salga disparado y llegue frenando — con lineal parece una barra de carga.

**Perillas nuevas** (*A - Trazo*): `DrawTime` (2,5 s) · `LoopDelay` (1,5 s; **0 = una sola vez**) · `bDrawOnStart` (true, andamio).

**Verificado en PIE:** a mitad de camino `DrawT = 0,48` con `Reveal = 0,77` — el reveal va **adelante** del tiempo, que es exactamente la firma del EaseOut. Y en la lectura siguiente `DrawT` había vuelto a 0,15: completó y **volvió a empezar**, o sea que el loop anda. Cero `Accessed None`.

## ✅ Verificado
- La malla se genera: **442 vértices · 1320 índices · 442 UVs · 442 normales**, coherentes con `Segments = 220`.
- El material queda asignado como **MID** en el componente (`MID_M_SoulRibbon_SC_0`) → los parámetros que empuja el CS llegan.
- Barrido de constantes en cero (`gotchas.md` §145): **ninguna** — las dos que la sonda marcó eran falsos positivos (0,5 y 0,73 empiezan con "0").
- Captura del viewport: **dibuja**, se ven las vueltas superpuestas y la torsión (unas pasadas anchas, otras de canto).

## ⚠ Lo que la captura ya dice
Sobre el fondo claro del Hall el trazo **se lava a blanco** — es la regla del emisivo sumado (`gotchas.md` §136) en vivo. En el vacío oscuro de la obra va a leer azul; si aun así se lava, se baja `Brightness` y se usa un color con un canal más bajo. **No subir el brillo para "verlo mejor": eso lo blanquea más.**

## Falta
- [ ] La pasada de arte de Beltrán sobre las perillas (es para eso que están todas en el viewport).
- [ ] Visor: es lo único que juzga si se siente vivo.
- [ ] **Integrarlo a [[BP_ProtoSoul_SC]]**: 4 anillos como componentes, uno por etapa. La animación ya está hecha — sólo hay que llamar **`Draw()`** desde la ceremonia y apagar `bDrawOnStart` y `LoopDelay`.
- [ ] 🔴 **Al integrar, extraer el flotar a una Material Function compartida** con `M_ProtoSoul`. Hoy los dos implementan la misma suma de senos por separado, con los mismos nombres de parámetro — **funciona sólo mientras nadie toque uno de los dos**. La función compartida lo vuelve imposible de desincronizar.
- [ ] Evaluar el modo **envolver** (el trazo cruzando por delante y por detrás), que era la otra opción y da más 3D.
- [ ] ⚠ Si alguna vez hace falta la versión no-additive: **el blend mode es estático**, o sea un material madre aparte, no un switch (`packaging-pso.md`).

## Relacionados
- [[BP_ProtoSoul_SC]] — quién va a llevar los anillos · [[BP_Alma_SC]] — de donde sale la receta de senos con razones no enteras · [[BP_DrawCanvas]] — el motor de cinta con el que el usuario pinta el 5º anillo · [[BP_TurrellPanel_SC]] — la otra pieza que aprendió lo de fp16 y el banding
