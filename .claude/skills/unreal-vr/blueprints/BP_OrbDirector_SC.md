# BP_OrbDirector_SC — el director de la repartija de amebas

**Ruta:** `/Game/SoulCharger/Core/Attracting/BP_OrbDirector_SC`
**Colocado en:** `/Game/TestMeshes` como `GAL_12_OrbDirector` (estación 12 de la galería)
**Nació:** 2026-09-23
**Estado:** 🟢 previa viva en el editor y esferas de juego enganchadas · ⬜ sin visor · 🔴 nivel sin guardar

---

## Por qué existe
Pedido textual de Beltrán: *"Armalo de forma de que yo pueda controlar el total de las esferas para
crear la composición… Es como un director de la repartija de amebas… puedo editar variables que se
actualicen en tiempo real en el editor para jugar con la estética y definirlo como arte"*.

Antes, el color de las esferas salía de un array del `BP_Sequencer_SC` y sólo se veía **dando play**.
Ahora hay **un solo actor** que decide el look de todas las esferas y lo **dibuja en el viewport**.

---

## Las dos caras del mismo look
| | Quién lo dibuja | Cuándo |
|---|---|---|
| **Vista previa** | el propio director, en su Construction Script | en el editor, al tocar cualquier perilla |
| **Las esferas reales** | `BP_SoundOrb_SC.Setup` le pide `ApplyLook` al director | al arrancar la mecánica |

🔴 **La única función que define el look es `ApplyLook`** — la llaman las dos caras. Si algo se ve
distinto entre la previa y el juego, es que alguien hizo el push por fuera de `ApplyLook`.

---

## Estructura de grafos (ningún Tick)

```
Hash01 (Index, Salt) → float 0..1
  abs(frac(sin((Index+Salt) · 12.9898) · 43758.5453))
  🔴 el abs() NO es decorativo: Math|Float|Fraction CONSERVA EL SIGNO → sin él
     salían tamaños por debajo de ScaleMin (gotcha del proyecto).
  🔴 el 12.9898 hay que forzarlo a float (ToFloat(Integer) + recrear el multiply):
     el operador promotable se quedaba en int y lo truncaba a 0.

LookColor (Index)      → BuildPalette() ; ActivePalette[ trunc(Hash01(Index, Seed)·4) % max(Len,1) ]
  🔴 el reparto de color es **azaroso, no ciclico**: con un indice lineal (i·3+s) mod 4
     el color se repite cada 4 esferas y se LEE como patron. Hash01 lo dispersa y `Seed` re-sortea.
BuildPalette ()        → ActivePalette = [Color1, Color2, Color3, Color4]
LookScale (Index)      → Lerp(ScaleMin,      ScaleMax,      Hash01(Index, 11))
LookFloatAmp (Index)   → Lerp(FloatAmpMin,   FloatAmpMax,   Hash01(Index, 23))
LookFloatSpeed (Index) → Lerp(FloatSpeedMin, FloatSpeedMax, Hash01(Index, 37))
  (sales distintas por variable ⇒ tamaño, deriva y ritmo NO están correlacionados)

ApplyLook (Comp: StaticMeshComponent, Index: int)
  SetStaticMesh(Comp, PreviewMesh) · SetMaterial(Comp, 0, PreviewMaterial)
  SetWorldScale3D(Comp, LookScale(Index))
  MID ← CoreColor = RimColor = GradColorA = GradColorB = EdgeColor = LookColor(Index)
        🔴 los CINCO, no solo CoreColor: con `M_ProtoSoul` los grad-colors vienen BLANCOS y el
           `EdgeColor` NARANJA, y tapan el color propio — las 20 amebas se veían casi iguales
           (blancas con borde naranja). Empujar la familia entera es lo que hace legible el color.
        FloatAmount = (LookFloatAmp, ×3)   FloatSpeed = LookFloatSpeed
        PhaseSeed = Index                  ← cada ameba se deforma en otra fase
        FloatScale · WobbleAmount · WobbleFreq · WobbleSpeed · Brightness  ← perillas globales

ApplyAnchorVisibility ()   ← la llama el Construction Script SIEMPRE (fuera del bShowPreview)
  for cada actor con AnchorTag → ShowAnchor(actor)
ShowAnchor (A: Actor)
  cast A a BP_Anchor → SetCollisionEnabled(Preview, NoCollision)  ← SIEMPRE, no depende de la perilla
                       SetHiddenInGame(Preview/TagLabel, true)
                       SetVisibility(Preview/TagLabel, bShowAnchors)
  💡 esconde la esfera verde (`MI_Ghost`) y el TextRender del tag SIN tocar `BP_Anchor`,
     que es compartido por toda la galeria. El CS de `BP_Anchor` solo escribe el texto,
     no la visibilidad, asi que no pelea con esto.

RebuildPreview ()
  for i in range(len(GetAllActorsOfClassWithTag(Actor, AnchorTag)))
     comp = AddStaticMeshComponent()     ; SetWorldLocation(comp, ancla[i])
     SetCollisionEnabled(comp, NoCollision)   ← 🔴 si no, la previa SE COME EL RAYO
     SetHiddenInGame(comp, true)              ← 🔴 si no, en PIE se ven DOBLES
     ApplyLook(comp, i)

ConstructionScript: if bShowPreview → RebuildPreview
```

---

## 🗂️ Grupos del panel (2026-09-24)
Beltran: *"hay demasiadas y a veces me pierdo para que son"*. Las 36 variables salieron de la bolsa unica
`0-Config` y se repartieron en grupos con prefijo numerico, que es lo que ordena el panel de detalles:

| Grupo | Que hay adentro |
|---|---|
| `0-General` | `Seed` — la semilla maestra del azar |
| `1-Color` | `Color1..4` (la paleta) + `ShadeColor` (el color bajo, el `ChainColorLow`) |
| `2-Esfera` | `ScaleMin`/`ScaleMax` y `OrbSort` (orden de dibujo entre translucidos) |
| `3-Forma` | la deformacion de la gota: `WobbleAmp`/`WobbleFreq`/`WobbleSpeed`, `FloatSpeedMin`/`Max`, `SeedSpread` |
| `4-Giro` | `SpinSlow` · `SpinFast` · `SpinAccel` |
| `5-Constelacion` | `Spread` · `SpreadSeed` · `GroupOffset` |
| `6-Particulas` | el cono del attracting: `AttractOn`, `AttractRate`, `AttractSpeed`, `AttractStop`, `AttractSizeMin`/`Max`, `AttractAlpha` |
| `7-Movimiento` | `ReturnSpeed` |
| `8-Editor` | andamiaje de la previa: `bShowPreview`, `bShowAnchors`, `PreviewMesh`, `PreviewMaterial`, `AnchorTag`, `AnchorScale` |
| `Z-Interno` | `ActivePalette` — no editable, la arma `BuildPalette` |

🔴 **Categorias SIN espacios, SIN acentos y SIN parentesis.** El id del DSL es
`Variables|<Categoria>|Get<Nombre>` con la categoria tal cual: `Variables|6-Particulas|GetAttractRate`. Los
espacios se comen (gotcha 1089) y los parentesis **rompen el parser** (gotcha 100).
⚠ **Recategorizar NO rompe los grafos ya compilados** (los nodos apuntan a la variable, no a la categoria),
pero **cambia el id del DSL**: cualquier `write_graph_dsl` futuro tiene que usar el grupo nuevo. Verificado
releyendo `ApplyLook` despues del cambio y con `find_node_types`.

💡 Ojo con dos nombres que se parecen y NO son lo mismo: **`SeedSpread`** (semilla por esfera de la forma,
en `3-Forma`) y **`SpreadSeed`** (semilla del desorden de la constelacion, en `5-Constelacion`).

---

## Perillas (instance-editable; el grupo de cada una, en la tabla de arriba)
| Perilla | Default | Qué mueve |
|---|---|---|
| `Color1` · `Color2` · `Color3` · `Color4` | rojo · ámbar · turquesa · azul | los 4 colores, cada uno con su selector — **así los pidió Beltrán, "tal como me has dejado en otros BP"**, no un array |
| `Seed` | 0 | vuelve a sortear qué color le toca a cada esfera |
| `ScaleMin` / `ScaleMax` | 0,12 / 0,26 | rango de tamaños por esfera |
| `FloatAmpMin` / `FloatAmpMax` | 0,8 / 2,5 cm | cuánto flota cada una |
| `FloatSpeedMin` / `FloatSpeedMax` | 0,4 / 1 | el ritmo de ese flotar |
| `WobbleAmount` | 0,12 | deformación de la ameba (**fracción del radio**, escala sola) |
| `WobbleFreq` | 0,06 | **escala del ruido** de la deformación: bajo = ondas grandes; alto = arrugas finas |
| `WobbleSpeed` | 0,8 | velocidad de esa deformación; 0 = ameba congelada |
| `Brightness` | 1 | brillo |
| `FloatScale` | 1 | multiplica el flotar **después** de la escala |
| `AnchorScale` | 0,13 | 🎯 el tamaño de anclaje, **absoluto e igual para todas**; la esfera viaja hacia él desde que se agarra |
| `PreviewMesh` / `PreviewMaterial` | `SM_AlmaSphere` / `MI_OrbBlob_SC` | malla y material de todas |
| `bShowPreview` | true | apaga sólo la previa del editor |
| `bShowAnchors` | false | esconde la esfera verde y el texto de los `BP_Anchor` de este director |
| `AnchorTag` | `orb_attracting` | el tag de las anclas |
| `SeedSpread` | 10 | la **semilla por esfera**: va a `COrb` y de ahi salen su forma, su fase de ondulacion y su fase de flotar. En 0 todas quedan identicas |
| `WobbleAmp` / `WobbleFreq` / `WobbleSpeed` | 0,09 / 4 / 0,35 | el wobble del material nuevo (`WobbleAFS`); no confundir con `WobbleAmount`/`WobbleFreq`/`WobbleSpeed`, que son de la ameba vieja |
| `OrbSort` | 20 | 🎯 **`TranslucencySortPriority` de cada esfera.** Mas alto = se dibuja despues = va por delante del metaball. La pila de la estacion es **0 = cadena · 10 = nucleos blancos · 20 = esferas**. En 0 vuelven a lavarse debajo de la gota |
| `Spread` | (0,0,0) | 🌟 **Desorden de constelacion**: maximo desplazamiento al azar por eje, en cm, sobre la posicion del ancla. En (0,0,0) queda la grilla ordenada de siempre |
| `SpreadSeed` | 0 | vuelve a sortear el desorden sin cambiar su magnitud |
| `GroupOffset` | (0,0,0) | 📦 **mueve TODO el conjunto en bloque**, sin tocar las anclas. Mover el actor del director NO hace esto |
| `SpinSlow` / `SpinFast` | 22 / 150 °/s | 🔄 la rotacion propia de cada esfera: suave en reposo, rapida **mientras la sostienes**. Vuelve sola a `SpinSlow` al anclarla |
| `SpinAccel` | 4 | que tan rapido pasa de una velocidad a la otra (`FInterpTo`); alto = casi instantaneo |
| `AttractOn` | ✅ true | ☑️ **la casilla del efecto**: en false no nace ni una particula y el emisor se completa solo. Es la forma de dejar el attracting fuera sin desarmar nada |
| `AttractRate` | ~120 /s | ✨ **el cono de particulas** (`NS_OrbAttract_SC`): cuantas nacen por segundo mientras sostenes la esfera. 0 = efecto apagado |
| `AttractSpeed` | 25 cm/s | la rapidez **constante** con que viajan hacia la mano. Tambien fija la vida de cada particula (vida = recorrido / esta velocidad), asi que subirla acorta el rastro |
| `AttractStop` | ~20 cm | cuantos cm **antes** de la mano termina el cono. Mas alto = cono mas corto, muere mas lejos de la mano |
| `AttractAlpha` | ~1 | opacidad del color de la esfera que se le pasa a las particulas |
| `AttractSizeMin` / `AttractSizeMax` | ~0,36 / 0,47 cm | tamano del sprite, sorteado por particula |
| `ReturnSpeed` | 1,5 | 🏠 **que tan rapido vuelve una esfera a su sitio** al soltarla fuera de un slot o al ser desalojada del secuenciador. Es la velocidad de un `VInterpTo`, no cm/s: mas alto = llega antes. Vivia escondida en el CDO de la esfera (estaba en 3) |

⚠ Las seis `Attract*` **las copia la esfera en su `Setup`**, asi que hay que **reentrar a PIE** para verlas
cambiar. Y **no hay ninguna compuerta de distancia**: el cono aparece apenas agarras la esfera (§374 de
gotchas — `AttractMax` existio y se borro por ser una trampa).

`ActivePalette` (Z-Estado) es la paleta armada: la llena `BuildPalette` desde `Color1..4` y la lee
`LookColor`. No es editable a propósito.

---

## 🧹 2026-09-24 — `ApplyLook` limpiada: 15 de 20 pushes no hacian NADA

Beltran: *"creo que hay muchas perillas muertas en los BP que son parte del sequencer"*. Tenia razon, y la
causa estaba toda en un sitio.

`ApplyLook` era **verbatim la lista de empujes del material viejo de ameba** (`M_SoundOrb_SC`) con 4
parametros de la cadena agregados al final. Pero las esferas usan **`MI_OrbBlob_SC`** (hija de
`M_SlotChain_SC`) desde el cambio del 2026-09-24. De los 20 parametros que empujaba:

- **Llegaban 5**: `FloatSpeed` · `ChainColorHigh` · `ChainColorLow` · `COrb` · `WobbleAFS`.
- **No existen en el material (14)**: `CoreColor`, `PhaseSeed`, `FloatScale`, `WobbleAmount`, `Brightness`,
  `WobbleFreq`, `WobbleSpeed`, `RimColor`, `GradColorA`, `GradColorB`, `EdgeColor`, `GradAmount` (ademas con
  **el pin de valor sin conectar**), `FresnelPower`, `ReliefAmount`.
- **Existe pero con el TIPO equivocado (1)**: `FloatAmount` es **Scalar** en `M_SlotChain_SC` y se empujaba
  con `SetVectorParameterValueOnMaterials` → se descarta en silencio.

🔍 **Como se verifico sin adivinar:** `MaterialInstanceTools.list_parameters` sobre el **material padre**
devuelve los 38 parametros que expone compilado. Cruzar esa lista contra los nombres de `ApplyLook` cierra la
pregunta en una llamada. Un `Set*ParameterValueOnMaterials` con un nombre que no existe **no falla ni avisa**:
es el caso puro de [[soul-charger-declarado-no-aplicado]] aplicado a materiales.

✅ `ApplyLook` quedo en 9 sentencias (orden de dibujo, malla, material, escala, y los 5 empujes vivos), y de
paso **`LookColor` se llama una vez en vez de dos**. Verificado despues: el call externo desde
`BP_SoundOrb_SC::Setup` y el de `RebuildPreview` siguen cableados, y los dos BP compilan limpio.

### Perillas borradas (7 del director)
`WobbleAmount` · `Brightness` · `FloatScale` · `ShadeSharp` · `ReliefAmount` — las cinco alimentaban empujes
muertos. Beltran las habia estado arrastrando (`Brightness` 1,143 · `ShadeSharp` 1,4747 · `FloatScale`
0,12005): **giraba perillas que no hacian nada**.
`WobbleFreq_0` · `WobbleSpeed_0` — duplicados sin usar, en la categoria `Default`, la firma de
[[variante-por-duplicado-deja-basura]]. ⚠ Ojo al borrarlos: los **originales** `WobbleFreq`/`WobbleSpeed`
**si viven** (los lee `LookWobble` para armar `WobbleAFS`). Se verifico releyendo `list_variables` y
`LookWobble` despues del borrado.

### 🗑️ `FloatAmpMin` / `FloatAmpMax` + `LookFloatAmp`: BORRADOS
Alimentaban el empuje mistipado de `FloatAmount` (Scalar empujado con el setter Vector), que se saco al
limpiar `ApplyLook`. Habia dos salidas — revivirlas empujando `FloatAmount` como Scalar, o borrarlas —
y **Beltran eligio borrarlas**. Coherente con la cadena, donde el flotar se **mudo del shader al Blueprint**
el 2026-09-23: mantener una amplitud de flotado por shader era volver atras.

⚠ **No confundir con `FloatSpeedMin`/`FloatSpeedMax` + `LookFloatSpeed`, que SIGUEN VIVOS**: alimentan el
empuje de `FloatSpeed`, que si existe en `M_SlotChain_SC` y si llega.

El director quedo en **36 variables** (eran 45).
---

## 🔒 La obra no cambia
`BP_SoundOrb_SC.Setup` termina con `GetActorOfClass(BP_OrbDirector_SC_C)` → `Cast`. En
`L_Attracting_SC` **no hay director**, el cast falla y no se aplica nada: la esfera de la obra
conserva su malla, su material y el color del `OrbColors` del secuenciador (que quedó como
**respaldo**, no como duplicado). El enganche va *después* del bloque viejo y converge desde las
**dos** salidas del branch (`True` y `False`) — un pin de exec de **entrada** acepta varias
conexiones.

---

## Lecciones de la construcción
1. 🔴 **Las perillas nuevas nacen en CERO en el actor ya colocado, y la instancia le gana al CDO.**
   `WobbleAmount`/`Brightness`/`FloatScale` entraron en 0 y `PreviewMesh`/`PreviewMaterial` seguían
   con los valores viejos (`/Engine/BasicShapes/Sphere` + `MI_AttractOrb`) **aunque el CDO ya tenía
   los nuevos**. Ése era exactamente el *"todavía no se ve el material como el de alma"*. Se arregla
   escribiendo la **instancia** (y eso además re-corre el Construction Script).
2. **Categorías con espacios rompen los getters del DSL** ("A - Paleta"): todo a `0-Config`.
3. `write_graph_dsl` sobre un `CallFunction` de una función propia: el primer positional se mapea a
   `self` → hay que usar **keyword args** (`:Index Index`).
4. Para rehacer un function graph: `remove_function_graph` → **compile (falla, es normal)** →
   `add_function_graph` → `write_graph_dsl` → compile. El nodo que la llamaba desde el Construction
   Script **se re-resuelve solo** al recompilar, porque el nombre vuelve igual.
5. `get_node_type_pins` devuelve refPaths con ids nuevos (`K2Node_CallFunction_17`…): son **nodos
   sonda transitorios**, no quedan en el grafo.
6. 🔴 **Un getter de variable que aparece DOS veces en el `read_graph_dsl` puede ser UN solo nodo.**
   `LookColor` mostraba `GetPalette` dos veces y `GetSeed` una: eran 2 nodos, no 3. Al borrar
   `VariableGet_0` y `_1` asumiendo que eran los dos Palette, **se fue el de `Seed`** y el `+` quedó
   sumando 0. Antes de borrar por posición en la lista, confirmar **qué variable es cada nodo**.
7. Un índice **lineal** (`i·k + s`) **mod N nunca es aleatorio**: cualquier recta mod 4 tiene periodo
   ≤4, así que el color se repite cada 4 esferas y se lee como patrón. Para repartir al azar hay que
   pasar por un hash. (Y no hay un `float*float` suelto en `Math|Float|`: `Lerp(0, N, h)` hace el
   mismo trabajo con un nodo que sí existe.)

---

## 🔴 Lo que rompió el primer PIE (y cómo se detectó)
Beltrán: *"muestra esferas dobles y además no me deja hacer collision con ninguna ni agarrarlas"*.
Dos causas distintas, las dos en el andamiaje del editor:

1. **El Construction Script TAMBIÉN corre en PIE**, así que cada ancla tenía la previa **y** la esfera
   real encima → dobles. Se arregla con `SetHiddenInGame(comp, true)`: la previa sigue viva en el
   viewport y desaparece al dar play.
2. **Un `AddStaticMeshComponent` nace CON colisión**, y además la **esfera verde del propio
   `BP_Anchor`** (`/Engine/BasicShapes/Sphere` a escala 0,18) siempre colisionó — hacerla invisible
   no alcanza. Las dos se comen el line-trace del beam justo donde está la esfera agarrable.

✅ **El instrumento que lo encontró fue `trace_world`, no mirar el grafo**: un trace de 2 m que
cruzaba el ancla devolvía **91 cm** — 9 cm antes del centro, exactamente el radio de la esfera verde.
Después del fix, **null** en dos anclas distintas. Ante "no puedo agarrar / algo tapa el rayo", el
primer paso es trazar y leer la DISTANCIA: dice qué tan grande es el bulto y dónde empieza.

## 🔴 Por qué el tamaño no llegaba a las esferas de juego
*"al poner play se ven todas del mismo tamaño"*. `ApplyLook` sí escribe la escala del `Body`, pero
en `BP_SoundOrb_SC` **el `Tick` la reescribe cada frame**:

```
EventBeginPlay : BaseScale = Body.RelativeScale3D   ← la escala del COMPONENTE, igual en las 20
                 Body.RelativeScale3D = 0           ← arranca invisible para el reveal
UpdateVisual(DT): Body.RelativeScale3D = BaseScale · reveal·(1+pulso) · (1+hover)
```

✅ La palanca correcta no es la escala del componente. Ahora:
- `Setup` escribe **`OrbScale`** = `LookScale(ClipId)`, y `GrabMul`/`PlacedMul` desde el director.
  Funciona porque **`Setup` corre DESPUÉS de `BeginPlay`** (se comprueba solo: `HomeLoc` se escribe
  en los dos y gana el de `Setup`).
- `BeginPlay` siembra `OrbScale` con la X de la escala del `Body`, así que **sin director la obra
  queda idéntica**.
- `UpdateVisual` calcula, antes que nada:
  `ScaleMul ← FInterpTo(ScaleMul, ((Grabbed||Placed) && bUseAnchor) ? AnchorSize : OrbScale, DT, ScaleSpeed)`
  `BaseScale = (ScaleMul, ScaleMul, ScaleMul)` — la línea vieja de `SetRelativeScale3D` no se tocó:
  sigue multiplicando reveal, pulso y **hover** encima, así que la esfera **crece al apuntarla** y
  eso no compite con el encogido.

🔴 **El tamaño de anclaje es ABSOLUTO, no un factor** — pedido textual: *"el tamaño objetivo de
anclaje y al que deben llegar las esferas debe ser para todas el mismo, independiente de si en el
espacio hay unas más grandes que otras"*. La primera versión lo hizo como factor sobre el tamaño
propio (para conservar la variedad) y el resultado fue el contrario del pedido: *"llegan grandes a
mi mano, y recién en el anclaje se achican"*. Como un absoluto no tiene valor neutro, el "no
aplicar" se marca con **`bUseAnchor`** (false por defecto) — así la obra, que no tiene director,
queda idéntica.

💡 **Un solo destino para agarrado Y anclado**: la esfera empieza a encogerse en el momento del
grab y llega a la mano ya del tamaño final. `ScaleSpeed` **3** (no 6) para que ese encogido dure
todo el viaje y se lea. Y no hay un `float*float` suelto en `Math|Float|`: `Lerp(0, x, k)` = `x·k`.

💡 Regla general: antes de empujar un valor a un objeto, **buscar quién más lo escribe en el
Tick**. Si hay un consumidor por frame, el push de una sola vez no sobrevive al primer frame; hay
que escribir **la variable de la que ese Tick deriva el valor**.

⚠ **Todavía sin resolver:** la previa indexa por la **posición del ancla** en
`GetAllActorsOfClassWithTag` y la esfera real por su **`ClipId`**. Si esos dos órdenes no coinciden,
la composición del viewport no es la que suena. Comprobarlo comparando previa vs PIE.

## Pendiente
- Que la esfera suelta **deje de flotar al agarrarla** y **adopte el movimiento de su gota** al
  anclarse (hoy el flotar vive en el WPO del material, así que se mueve el dibujo y no el actor —
  misma trampa que [[BP_ProtoSoul_SC]]: con `FloatAmount` grande, ves la esfera en un lado y la
  agarrás en otro. Por eso el default bajó a 0,8-2,5 cm).
- Costo en Quest: 20 amebas translúcidas de 5.120 tris **encima** del raymarch de [[BP_SlotChain_SC]].

## 🆕 2026-09-24 — el material de la esfera: opaco, con degradé de dos colores y RELIEVE real

`M_SoundOrb_SC` pasó a **`BLEND_Opaque`**; los núcleos de las gotas usan un duplicado translúcido,
**`M_BlobCore_SC`**, porque el blend mode es del material y no de la instancia.

🔴 **Dos intentos fallidos antes de leer el grafo, y los dos por lo mismo:** empujar parámetros sin
saber qué hacían.
1. Poner los CINCO colores al mismo tono (para que el color se leyera) aplanó el volumen.
2. Meter un color oscuro en `GradColorA` para simular sombra dibujó **una grilla**: `GradColorA/B` no
   es sombreado, es el **degradé animado** de Alma — tres senos sobre la posición local. Beltrán:
   *"¿qué vergas es eso? se ve como una grilla genérica"*.

✅ **Lo que sí funciona, después de mapear el material** (169 expresiones, sin nodos Custom):

```
body = lerp(CoreColor, RimColor, alpha)          ← el degradé de dos colores YA existía
alpha = saturate( Fresnel_0 − relief · ReliefAmount )    ← lo ÚNICO que hubo que agregar
   relief = MaterialExpressionDivide_0   (el escalar del wobble, ya normalizado −1..1,
                                          que el WPO usaba sólo en el vertex shader)
```

💡 **La clave: el escalar del relieve ya estaba en el grafo.** El WPO lo usaba para abollar la
malla; reusarlo en el emisivo lo evalúa también en el pixel shader, contra la posición de cada
píxel, y da un relieve **suave y exacto** — sin recalcular normales y sin las facetas que daría un
`ddx/ddy`. El WPO **no** recalcula la normal: sin esto, el Fresnel sombrea como si la esfera
siguiera lisa.

| Perilla del director | Qué hace |
|---|---|
| `ShadeColor` | el segundo color del degradé, **compartido por todas** → `RimColor` + `EdgeColor` |
| `ReliefAmount` | cuánto marca la deformación; **negativo invierte** qué cara queda en sombra |
| `ShadeSharp` | cierre del degradé hacia el canto → `FresnelPower` |

Y `GradAmount` se empuja a **0** desde `ApplyLook`: apaga el degradé animado, que en una bola opaca
se lee como grilla.

## 🆕 2026-09-24 — rotacion propia de cada esfera
**`LookSpinAxis(Index) -> Vector`** devuelve un **eje unitario aleatorio** por esfera, uniforme sobre la
esfera (no sesgado al cubo): `z = h(101)*2-1`, `phi = h(113)*360`, `r = sqrt(1-z*z)`,
`axis = (r*cos phi, r*sin phi, z)`. Nunca degenera — con `z = ±1` da `(0,0,±1)`, que sigue siendo unitario.
⚠ La version barata (normalizar tres hashes centrados) puede devolver el vector **cero** cuando los tres
caen cerca de 0,5, y esa esfera se quedaria quieta para siempre. Por eso la formula esferica.

Las tres perillas (`SpinSlow`/`SpinFast`/`SpinAccel`) y el eje los **copia la esfera en su `Setup`**
(ver [[BP_Sequencer_SC]]), no `ApplyLook`: `ApplyLook` recibe un *componente*, no puede escribir variables
del actor. La previa del editor **no gira** (el Construction Script no tiene tick) y esta bien: una
velocidad no se autora mirando una foto.

## 🌟 2026-09-24 — `Spread`: romper la grilla sin mover las anclas
Pedido: *"están ordenadas como dos filas en columnas — una perilla que permita desordenarlas aleatoriamente
en el espacio, para que se sienta mas como una constelacion"*.

**`LookOffset(Index) -> Vector`** devuelve `(h(211)*2-1, h(307)*2-1, h(409)*2-1) * Spread`, con los salts
corridos por `SpreadSeed`. Cada eje tiene su propio maximo, asi que se puede desparramar mucho en horizontal
y poco en vertical, o al reves.

**Se aplica en DOS lados y tiene que ser el mismo numero:**
- `RebuildPreview` → `AddWorldOffset(comp, LookOffset(indice del array))`, despues de plantar la previa
  sobre el ancla. Se ve en el viewport sin dar play.
- `BP_SoundOrb_SC.Setup` → `AddActorWorldOffset(LookOffset(ClipId))` y **recalcula `HomeLoc`** con la
  posicion nueva, para que la esfera vuelva a su lugar desparramado al soltarla lejos.

🔴 **Las anclas NO se mueven.** El desorden es un offset sobre ellas, asi que `Spread = 0` devuelve
exactamente la composicion autorada y **nada de esto es destructivo**.

⚠ **Esto vuelve VISIBLE un riesgo que estaba dormido:** la previa indexa por **posicion en el array de
anclas** y la esfera de juego por **`ClipId`**. Si esos dos indices no coinciden, el desparramo del editor y
el del juego van a ser distintos — y con `Spread` alto se nota de inmediato. Si en la proxima pasada la
constelacion en PIE no es la que se ve en el viewport, **ese es el problema**, y afecta tambien a color,
tamano y giro (que ya indexaban asi).

## 📦 `GroupOffset` — por que mover el ACTOR del director no mueve nada
`RebuildPreview` planta cada previa sobre la **posicion mundial del ancla**, no sobre el director. El
director es un panel de control, no un padre: su transformada no participa en ningun calculo, asi que
arrastrarlo en el viewport no mueve una sola esfera.

✅ Para mover el conjunto en bloque existe **`GroupOffset`** (cm, mundo). Se sumo **dentro de `LookOffset`**
— que devuelve `dispersion + GroupOffset` — para que los **dos** consumidores (la previa del editor y el
`Setup` de la esfera de juego) lo hereden sin tocar nada mas.
📏 Verificado con test de identidad sobre el actor del nivel: con `GroupOffset` en (0,0,40) las previas
subieron **exactamente 40 en Z** y no se movieron en X ni en Y.

⚠ La alternativa habria sido usar la transformada del director como offset, que es lo que uno espera al
arrastrarlo. Se descarto: obligaria a guardar una posicion "origen" de referencia y se rompe el dia que el
director se mueva por orden, no por diseno.
