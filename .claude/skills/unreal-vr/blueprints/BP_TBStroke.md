# BP_TBStroke — el trazo hecho como lo hace Tilt Brush

> **Proyecto:** Neural Canvas (`TiltBrush.uproject`), MCP `unreal-canvas` (8001).
> **Carpeta:** `/Game/Drawing/TB/` — **aislada**. No toca `BP_Stroke` ni `BPC_DrawTool_NC`,
> que quedan como están (la cinta aprobada en visor el 2026-09-24).
>
> Pedido de Beltrán (2026-09-25): *"dejemos de lado el blueprint que nosotros construimos y
> construye uno nuevo de cero exactamente como lo haría Tilt Brush… me interesa que probemos
> un sistema que ya está testeado."*
>
> Fuente: `open-brush/Assets/Scripts/Brushes/{BaseBrushScript,GeometryBrush,FlatGeometryBrush}.cs`,
> leídos del repo clonado. Arquitectura general en
> [`references/tiltbrush-brush-architecture.md`](../references/tiltbrush-brush-architecture.md).

## Qué se replica y de dónde

`FlatGeometryBrush` es el generador de `DoubleTaperedMarker`, `TaperedMarker_Flat`,
`DoubleTaperedFlat` y `Electricity`. Es un `GeometryBrush`, o sea usa el **sistema de nudos**,
que es la base de 10 de los 15 generadores en uso. Elegido a propósito: da una cinta plana
(familia visual ya aprobada) sobre la arquitectura correcta, y desde acá Tube / Hull / Spray
son incrementales.

## 🔴 Las 9 cosas que hace Tilt Brush y nuestra cinta no

| | Tilt Brush | `BP_Stroke` (el nuestro) |
|---|---|---|
| Lado de la cinta | `ComputeSurfaceFrameNew`: **dos** candidatos mezclados + transporte paralelo | un solo `cross(dir, ControllerUp)` |
| Presión | tamaño, opacidad **y** espaciado | no se lee |
| Suavizado de presión | por **distancia**: `k = 0.1^(d/20cm)` | `SpeedTau`, por tiempo |
| Suavizado de posición | kernel (1,2,1)/4, retroactivo al nudo de atrás | ninguno |
| Tangente | diferencia central `(next − prev)` | segmento crudo `(new − last)` |
| Auto-intersección | recorta el ancho cuando la cinta gira cerrado | ninguna → arrugas |
| Crecimiento de ancho | limitado: `size ≤ sizePrev + moveLength` | libre → bultos |
| Verts finales | segundo suavizado (0.3, 0.4, 0.3) de centro **y** semiancho | posición cruda |
| UV a lo largo | `u += TileRate * (length / size)` → **en anchos de pincel** | `V = TotalDistance` → distancia cruda = textura estirada |

Más: rompe la tira cuando el movimiento es < 0,5 mm o cuando **se devuelve**
(`dot(vMove, next − cur) < 0`), en vez de hacer un moño.

## La fórmula del marco (el corazón, `BaseBrushScript.ComputeSurfaceFrameNew`)

```
nPointerF = orient * forward
nPointerU = orient * up
vRight1 = InDirectionOf(preferredR, cross(nPointerF, nMove))
vRight2 = InDirectionOf(preferredR, cross(nPointerU, nMove)) * abs(dot(nPointerF, nMove))
nRight  = normalize(vRight1 + vRight2)
nNormal = cross(nMove, nRight)
```

`vRight2` existe para cuando **tiras el pincel hacia ti**: ahí `nPointerF ≈ nMove` y el primer
cross degenera. Se pesa justo por `abs(dot(F, move))`, que es 1 exactamente en el caso malo.
`InDirectionOf(pref, v)` = `v` o `-v`, el que apunte hacia `pref`; con `pref = prev.nRight` es
**transporte paralelo** y es lo que impide que la cinta se dé vuelta 180°.

## Las UV (`OnChanged_DistanceUVs`)

- **u a lo LARGO, v a lo ANCHO** (al revés que lo nuestro; el material se escribe acorde).
- `u1 = u0 + TileRate * (length / size)` ← **la clave**: la textura se mide en anchos de pincel.
- Al empezar la tira: `u0 = rand01`, y **fila del atlas al azar**:
  `iAtlas = int(rand01 * 3331) % TextureAtlasV`, `v0 = iAtlas/numV`, `v1 = (iAtlas+1)/numV`.
  Mismo pincel, textura distinta en cada trazo.

## Desviaciones conscientes (y por qué)

1. **Sin structs.** El MCP no puede crear ni editar UStructs
   ([[soul-charger-struct-portrait-pendiente]]), así que `Knot` es un juego de **arrays
   paralelos**, no un array de structs. Mismos datos, indexados igual.
2. **Sin bookkeeping `iVert/nVert/iTri/nTri`.** En vez de la maquinaria de invariantes de
   tajadas, se **regenera el trozo actual completo** desde sus nudos. El costo queda igual de
   acotado (un trozo tiene tope de `ChunkKnots`), que es lo que importa: **O(N) total en vez de
   O(N²)**, sin la parte más frágil de portar. TB corta el trazo a los 9000 vértices; acá se
   corta a `ChunkKnots` nudos y cada trozo es una `MeshSection` propia que **no se vuelve a
   tocar**.
3. **Doble cara por material two-sided**, no duplicando vértices. TB los duplica por
   iluminación y por `m_BackfaceHueShift`; acá es Unlit. Se anota: si algún día se quiere el
   corrimiento de tono en la cara de atrás, hay que duplicar de verdad.
4. **Una rotura termina el trozo** (nueva sección), en vez de un hueco dentro de la misma tira.
   Una rotura ES un fin de tira en TB, así que el comportamiento coincide.

## Registro de variables

**El descriptor (instance-editable, categoría `01 PINCEL`):**
`BrushSize` (2.0 — ancho TOTAL en cm a presión 1) · `PressureSizeMin` (0.10) ·
`Opacity` (1.0) · `PressureOpacityRange` (Vector2D, (0.35, 1.0)) ·
`SolidMinLengthCm` (0.2 — el `m_SolidMinLengthMeters_PS` de TB, 0.002 m) ·
`SolidAspectRatio` (0.2 — `kSolidAspectRatio`) · `TileRate` (1.0) · `TextureAtlasV` (1) ·
`SizeVariance` (0.0) · `PressureSmoothWindowCm` (20.0) · `bDisableWidthSmoothing` (false) ·
`ChunkKnots` (64) · `PaintMaterial` · `BaseColor`

**Los nudos (arrays paralelos, categoría `02 NUDOS`):**
`K_Pos` · `K_SmoothPos` (Vector[]) · `K_Press` · `K_SmoothPress` (float[]) ·
`K_Fwd` · `K_Up` (Vector[], la orientación del mando) · `K_Right` · `K_Surface` (Vector[]) ·
`K_Len` · `K_Size` (float[]) · `K_HasGeo` (bool[])

**La geometría del trozo (categoría `03 TROZO`):**
`V_Pos` · `V_Normal` (Vector[]) · `V_UV` (Vector2D[]) · `V_Color` (LinearColor[]) ·
`V_Tri` (int[]) · `SectionIdx` (int) · `ChunkStart` (int, índice del primer nudo del trozo)

**Estado del trazo (categoría `04 ESTADO`):**
`MID` · `UBase` (float) · `AtlasV0` · `AtlasV1` (float) · `Seed` (int) · `UCursor` (float)

## Funciones

| Función | Origen en el código |
|---|---|
| `StartStroke(Pos, Fwd, Up, Pressure)` | `InitBrush` + siembra de los nudos 0 y 1 |
| `UpdatePosition(Pos, Fwd, Up, Pressure)` | `GeometryBrush.UpdatePositionImpl` |
| `FrameKnots(iKnot0)` | `OnChanged_FrameKnots` |
| `MakeVerts(iKnot0)` | `OnChanged_MakeVertsAndNormals` (las dos pasadas) |
| `DistanceUVs(iKnot0)` | `OnChanged_DistanceUVs` |
| `ComputeSurfaceFrame(PrefR, Move, Fwd, Up)` → `Right`, `Surface` | `ComputeSurfaceFrameNew` |
| `InDirectionOf(Pref, V)` → Vector | helper del mismo archivo |
| `PressuredSize(p)` / `PressuredOpacity(p)` / `GetSpawnInterval(p)` | `BaseBrushScript` |
| `PushSection()` | el corte a los 9000 verts, adaptado a `ChunkKnots` |
| `EndStroke()` | `FinalizeSolitaryBrush` (sin el `TrimShortStrokeAfterBreak` por ahora) |


## Estado construido (2026-09-25) — compila limpio, guardado

**15 funciones**, conteo de nodos (sin basura huerfana):

| Funcion | Nodos | Origen |
|---|---|---|
| `InDirectionOf` | 8 | helper de `BaseBrushScript` |
| `ComputeSurfaceFrame` | 13 | `ComputeSurfaceFrameNew` — devuelve `OutRight` **y** `OutSurface` |
| `PressuredSize` | 7 | `BaseBrushScript.PressuredSize` |
| `PressuredOpacity` | 9 | `BaseBrushScript.PressuredOpacity` |
| `GetSpawnInterval` | 8 | `FlatGeometryBrush.GetSpawnInterval` |
| `ClearArrays` | 35 | — |
| `AddKnot` | 27 | el nudo vivo que se agrega al confirmar |
| `StartStroke` | 16 | `InitBrush` + siembra de los nudos 0 y 1 |
| `UpdatePosition` | 28 | `GeometryBrush.UpdatePositionImpl` |
| `CommitKnot` | 12 | la decision de confirmar o cortar el trozo |
| `PushSection` | 11 | el corte a los 9000 verts, adaptado a `ChunkKnots` |
| `FramePass` | 108 | `OnChanged_FrameKnots` + el tamano + las UV |
| `EmitPass` | 120 | `OnChanged_MakeVertsAndNormals` (las dos pasadas) |
| `RebuildChunk` | 12 | llama a las dos pasadas + `CreateMeshSection` |
| `EndStroke` | 3 | `FinalizeSolitaryBrush` |

**Material:** `/Game/Drawing/TB/M_TBRibbon_NC` — Unlit · Translucent · TwoSided.
`Emissive = VertexColor.RGB * Brightness`, `Opacity = VertexColor.A`.
🔴 **El color y la opacidad viajan en los VERTICES, no en parametros** — que es como lo hace
Tilt Brush. Consecuencia buena: **no hace falta un MID por trazo**, asi que desaparece el
problema de draw calls que tiene `BP_Stroke` (ver los riesgos en `BPC_DrawTool_NC.md`).
Sin textura a proposito en v1: la geometria se ve desnuda, que es lo que se esta probando.

### 🔴 Dos trampas nuevas, pagadas en esta sesion

1. **La CATEGORIA de una variable entra en el `type_id` del DSL, con los espacios comidos.**
   `BrushSize` en la categoria `01 PINCEL - el descriptor` se lee
   `Variables|01PINCEL-eldescriptor|GetBrushSize`, **no** `Variables|Default|GetBrushSize`
   (que da *"does not exist"*). El guion bajo tambien se cae: `K_Pos` → `GetKPos`.
   Y hay **colision con el BP viejo**: existe `Class|BPStroke|GetSectionIdx`, asi que la forma
   calificada no es opcional.
2. **Todo el pipeline se escribio SIN RAMAS, solo con `select`.** El parser permite un solo
   nodo multi-exec por funcion y tiene que ir al final, lo que hace imposible meter varios
   `if` en el cuerpo de un `for`. Pero resulta que casi todo en este pipeline es una
   **eleccion de VALOR**, no de ejecucion: primer nudo vs medio, el recorte por
   auto-interseccion, el limite de crecimiento, el no-suavizado en las puntas. Con `select` y
   con los indices acotados por `Math|Integer|{Max,Min}(Integer)` el bucle queda plano y
   no hay un solo branch. Salio mas corto que la version con ramas.

### Lo que falta para probarlo
La capa de input. El motor no tiene dueno del input a proposito
([[mecanicas-exportables-mandato]]). Hallazgo util: **`IA_Hand_IndexCurl_Left` ya es `Axis1D`**
(`IA_Shoot_Left` es `Boolean`), o sea la presion analogica esta disponible sin crear ningun
asset de input — es la curvatura del indice, que en un mando es el gatillo.


## El banco de pruebas (2026-09-25)

**Nivel: `/Game/Drawing/Maps/L_TBTest`** — duplicado de `L_DrawTest`, con el pawn viejo
(`BP_DrawPawn_Solo`) sacado y `BP_TBPawn` en su lugar (-315, 0, 106). Aislado a pedido de
Beltran: ahi **solo corre el pincel nuevo**, para juzgarlo sin nada mas encima.
`L_DrawTest` queda intacto con la cinta aprobada.

**`BPC_TBTool_NC`** (ActorComponent, `/Game/Drawing/TB/`) — la herramienta, **sin dueno del
input** ([[mecanicas-exportables-mandato]]). API: `Setup(TipComp)` · `Press()` · `Release()` ·
`SetPressure(V)`. Guarda `Current`, `bDrawing`, `Pressure`, `StrokeHistory`, y
`BrushColor`/`bCanDraw` instance-editables. En Tick, si dibuja, empuja la pose de la punta.

**`BP_TBPawn`** — pawn minimo (`Camera`, `MC_Right`=RightAim, `MC_Left`=LeftAim, `TBTool`),
`AutoPossessPlayer=Player0`. En `Event Possessed` agrega `IMC_Weapon_Right` e `IMC_Hands`
con **Priority 1000** y llama `Setup(MC_Right)`. Ruteo:

| Input | Evento | Va a |
|---|---|---|
| `IA_Shoot_Right` (Boolean) | Started / Completed | `Press()` / `Release()` |
| `IA_Hand_IndexCurl_Right` (**Axis1D**) | Triggered | `SetPressure(ActionValue)` |

🔴 **La presion sale de `IA_Hand_IndexCurl_Right`, que ya existia y ya es `Axis1D`** — no se
creo ningun asset de input. Es la curvatura del indice, que en un mando es el gatillo.
⚠ **Sin verificar en visor**: si el grosor no varia con la fuerza del apriete, el sospechoso
es que ese IA no reciba valor con mandos (podria estar pensado para hand tracking). El
fallback es que `Pressure` se queda en su default 1.0, o sea el trazo funciona igual pero parejo.

### Tres asimetrias del DSL descubiertas acá
1. **Setter de variable cruzado: `self` es el ULTIMO pin.** `Class|BPTBStroke|SetBaseColor`
   tiene `BaseColor`(1) y **`self`(2)**. En una **llamada a funcion** cruzada, en cambio, `self`
   va primero (`Class|BPTBStroke|StartStroke` → `self`(1), `Pos`(2)...). Positional puro falla
   en el primer caso; conviene keyword (`:self` / `:BaseColor`).
2. **El cast CONSERVA el guion bajo**: `Utilities|Casting|CastToBP_TBStroke`, mientras que
   `Class|BPTBStroke|...` lo come. (Y `find_node_types` sin filtrar casts devuelve **6180**
   entradas: filtrar siempre.)
3. **Los eventos de Enhanced Input NO se escriben con `(event ...)`**: el DSL prefija
   `AddEvent|` y `Input|EnhancedActionEvents|IA_X` no vive ahi. ✅ Receta que funciona:
   escribir funciones chicas por DSL (`OnTriggerStart`, `OnCurl`...) y enganchar el evento por
   **cirugia** (`create_node` del evento + `create_node` de `CallFunction|OnX` + `connect_pins`).
   El `ActionValue` de un `Axis1D` es un pin Float del mismo nodo de evento.

⚠ **`SpawnActorFromClass` tiene `SpawnTransform` por REFERENCIA**: sin nada conectado no
compila (*"by ref params expect a valid input"*). Hay que cablearle un
`Math|Transform|MakeTransform`, que por suerte ya trae identidad por defecto
(Location 0, Rotation 0, Scale 1).


## 🟢 PRIMERA PASADA DE VISOR (2026-09-25) — aprobada

Beltrán: *"El dibujo se siente muy fluido. Se pasó … se sintió de una como una mecánica mejor."*
La mecánica de Tilt Brush **se siente mejor que la nuestra en la primera pasada**, sin ningún
afinado y sin textura. Se valida la apuesta: la arquitectura era el problema, no la estética.

### El bug que encontró: el trazo se ponía NEGRO después de cierto largo — ARREGLADO

**Causa:** cada trozo es una `MeshSection` nueva, y `StartStroke` solo asignaba el material a la
sección **0**. Al pasar los `ChunkKnots` (64), `PushSection` creaba la sección 1, 2, 3… **sin
material** → material por defecto → negro en esta escena. Por eso el corte era limpio y siempre
a la misma distancia.

**Arreglo (cirugía, no reescritura):** `PushSection` ahora captura el índice nuevo desde el
`Output_Get` del propio `SetSectionIdx` y llama
`Rendering|Material|SetMaterial(Mesh, <idx nuevo>, PaintMaterial)`. Funciona aunque la sección
todavía no exista: `SetMaterial` escribe en `OverrideMaterials`, que se consulta cuando el
proxy se reconstruye.

💡 **La lección general: un trozo nuevo NO es un trazo nuevo.** Todo lo que se inicializa
por trazo hay que revisarlo en el corte de trozo. Lo cual lleva a…

### 🟢 Segunda pasada: el CORTE en la costura — ARREGLADO (y con él, otros tres)

Beltrán: *"ya no se ve negro pero se ve un corte en el trazo"*. Foto: un hueco de ~3-4 mm en
una cinta de 2 cm, a intervalos regulares.

**Causa medida:** el centro de cada fila de vértices se suaviza con `0.3·prev + 0.4·cur + 0.3·next`,
y en el nudo de la costura eso salía **distinto de cada lado**. El trozo viejo lo veía como su
último nudo (`inx` se clampea a sí mismo → tira hacia atrás: `0.3·p[E-1] + 0.7·p[E]`) y el
nuevo como su primero (`ip` se clampeaba a `_c0` → tira hacia adelante: `0.7·p[E] + 0.3·p[E+1]`).
Diferencia = `0.3·(p[E+1] − p[E-1])` ≈ 0,3 × 2 × espaciado ≈ **3,6 mm**. Coincide con la foto.

💡 **La raíz, otra vez la misma:** el trozo es una **ventana de dibujo, no una frontera
lógica**. La matemática debe mirar el trazo ENTERO; lo único acotado al trozo es *qué nudos se
emiten*.

**El arreglo, en dos mitades:**
1. **Los topes miran el trazo entero.** En `FramePass` y `EmitPass`, `_ip = Max(i-1, _c0)` y la
   comparación de `_first`/`_ends` pasaron de `_c0` a **literal `0`** (4 nodos: se les corto el
   enlace desde `GetChunkStart` y se les puso el valor).
2. **El trozo viejo se cierra cuando su costura YA es interior.** `CommitKnot` reordenado a
   `AddKnot → RebuildChunk → PushSection` (antes era `PushSection → AddKnot`), y `PushSection`
   ahora arranca en `Length - 2` en vez de `Length - 1`. El quad extra que dibuja el trozo viejo
   es **degenerado** (el nudo nuevo nace en la misma posición), o sea invisible.

✅ **Con eso se arreglaron CUATRO continuidades que se reiniciaban por trozo**, todas del mismo
`_c0`: el suavizado de posición (el corte visible), la **coordenada U** (la deuda anotada abajo
— ya no existe), el límite de crecimiento del ancho, y el suavizado de presión por distancia.


### 🔴 Tercera pasada: el corte seguía — la causa era EL TROCEADO ENTERO

La simulación offline (`scratchpad/seam.py`, modelo del algoritmo fuera de Unreal) midió
**desfase 0,0000 cm en el instante del corte** — o sea el arreglo anterior sí funcionaba ahí.
El corte apareció **después**: el trozo viejo queda congelado con la tangente del nudo costura
calculada contra un vecino degenerado, y el trozo nuevo lo sigue recalculando mientras el
trazo crece.

Beltrán: *"Arreglalo como lo solucionan en TiltBrush, no inventando"*. Y ahí está la respuesta:
**Tilt Brush no trocea.** Una malla por trazo, regenerada desde el primer nudo cambiado; el
límite de 9000 verts **termina el trazo**, no lo parte. El troceado cada 64 nudos era
invención mía y fabricó los tres bugs.

✅ **`ChunkKnots` 64 → 4500** (= 9000 verts ÷ 2 por nudo, el número exacto de ellos).
Sin trozos no hay costura. Ver gotcha 386.

⚠ **Deuda que deja:** ahora cada cuadro regenera el trazo entero. TB evita eso con
`m_FirstChangedControlPoint` (solo los últimos ~3 nudos pueden cambiar de geometría). Si los
trazos largos tironean, el arreglo fiel es hacer `EmitPass` incremental — arrays de vértices
persistentes escritos con `SetArrayElem` en vez de `Clear` + `Add` —, **no volver a trocear**.


### 🟢 Cuarta pasada: el gatillo se colgaba — ARREGLADO. **MECÁNICA APROBADA**

Beltrán: *"A veces no reconoce que solté el botón… sigue con una línea suave"*, y después
**"Funciona bien"**.

**Causa:** gate por eventos (`Started`/`Completed`) en vez de por estado. Tilt Brush consulta
`GetCommand(Activate)` **cada cuadro**. Ver gotcha 387.

**Arreglo, en dos mitades:**
1. **`BP_TBPawn` EventTick** → consulta `Input|EnhancedActionValues|IA_Hand_IndexCurl_Right`
   (nodo puro, sin entradas, Float) y lo empuja con `SetPressure`. La presión ya no se congela.
2. **`BPC_TBTool_NC.GateStop()`**, primero en el Tick: si `Pressure < 0.08` y está dibujando,
   `Release()`. Tick final: `GateStop → if(bDrawing) → FeedStroke`.

⚠ **El umbral 0.08 es NUESTRO, no de Tilt Brush** (el suyo vive en su capa de SDK de mandos,
no bajada). Si corta antes de tiempo al aflojar el dedo, se baja.

🔴 **Y un error propio que la lectura post-cirugía atrapó:** los dos `AddMappingContext`
estaban con los **defaults del motor**. Van `bIgnoreAllPressedKeysUntilRelease=False` +
`bForceImmediately=True` (`CLAUDE.md` §7.b). Corregidos. Ver gotcha 388.

ℹ El camino viejo por eventos quedó conectado a propósito como red (`Press`/`Release` están
guardados, no molestan). Se puede sacar cuando se confirme que la consulta basta.

## 📍 Estado al cierre del 2026-09-25

🟢 **Mecánica aprobada en visor.** Un pincel (cinta plana), un color, sin textura, sin paleta.
Deudas y pendientes, por orden de lo que conviene atacar:
1. 🔴 **Sin respaldo.** El backup manual es del 2026-09-24; todo `TB/` es posterior.
2. ⬜ **Sin medición en device.** Al sacar el troceado, cada cuadro regenera el trazo ENTERO.
   TB lo evita con `m_FirstChangedControlPoint` (solo los últimos ~3 nudos cambian). Si un trazo
   largo tironea, **ese** es el arreglo — no volver a trocear (gotcha 386).
3. Texturas reales + los 6 pinceles planos; después `HullBrush`; después paleta con los 83 iconos.


## 🎨 Stretch UV + los 3 primeros presets (2026-09-25, pedido de Beltrán)

Beltrán eligió 9 pinceles de la version de Quest: OilPaint, WetPaint, TaperedMarker_Flat,
"Pinhead Flat" (→ candidato `DoubleTaperedFlat`, sin confirmar), Light, CelVinyl, Petal,
Spikes, SoftHighlighter. **Los 9 usan `Stretch`** — por eso notó que "la textura se va
estirando hasta que termina el trazo".

🔴 **Hallazgo que cambió el plan: de los 9, SOLO OilPaint trae textura** (`main.png` +
`normal.png`). Los otros 8 solo traen `buttonimage` (el icono). **Su look es shader + numeros
del descriptor + geometria, no textura.** Cada pincel guarda sus PNG en su propia carpeta
(`Assets/Resources/Brushes/<Basic|X>/<Nombre>/`).

### `Stretch` UV — implementado

```csharp
OnChanged_StretchUVs():  u = distancia_acumulada / totalLength   // sin TileRate
```
`totalLength` crece cada cuadro → la U **se renormaliza sobre el trazo entero** mientras
dibujas. No es animacion de shader: es el mapeo rehaciendose.

**Como se hizo, sin tocar `FramePass`** (el grafo grande): `NormalizeU()` → si `UVStyle == 1`
llama `StretchAccum()` (acumula `K_Len` dentro de `K_U`) y `StretchNorm()` (divide por el
total). `RebuildChunk` ahora es `FramePass → NormalizeU → EmitPass → CreateMeshSection`.
Con `UVStyle = 0` (Distance) `NormalizeU` no hace nada: **el look aprobado no se toca.**

### Presets — `Preset` + `ApplyPreset()`

`ApplyPreset()` es un `switch` llamado como **primer** statement de `StartStroke`.
⚠ El nodo Switch nace con pines 0-2 y el DSL **no los agrega solo**, asi que el mapeo es:

| `Preset` / `BrushIndex` | Pincel | PressureSizeMin | BrushSize | TileRate |
|---|---|---|---|---|
| **-1** | **el look aprobado** (rama Default, no toca nada) | 0.10 | 2.0 | 1.0 |
| 0 | `TaperedMarker_Flat` | **0.0** — afina hasta la punta real | 2.0 | 0.15 |
| 1 | `DoubleTaperedFlat` | 0.1 | 6.0 (3×) | 0.10 |
| 2 | `SoftHighlighter` | **0.0** | 4.0 (2×) | 1.0 |

Los tres con `UVStyle = 1` y `OpacityAtP0 = 1` (en TB la opacidad **no** varia con la presion
en estos: `m_PressureOpacityRange = {1,1}`; solo varia el TAMAÑO).

🔴 **Que se copio y que no:** se copia el afinado **adimensional** (respuesta a la presion,
estilo de UV, opacidad, TileRate) porque es portable. **NO se copian los tamaños absolutos**:
`m_BrushSizeRange` esta en unidades de Tilt Brush, no en cm. Se mantuvo nuestra escala (2 cm
de base) y se aplicaron **sus proporciones relativas** (DoubleTaperedFlat es 3× el
TaperedMarker; SoftHighlighter 2×).

⚠ **`SoftHighlighter` hoy es solo su GEOMETRIA.** Su suavidad vive en un shader propio que
no esta portado: se vera como una cinta ancha que afina hasta la punta, no como un resaltador.
Para hacerlo bien hace falta `EdgeSoftness` en el material **con default 0** (neutro, regla de
[[funcion-nueva-no-degrada-aprobada]]) + un MaterialInstance propio por pincel — que es
justo como lo hace TB (un material por pincel, y por eso pueden batchear).

**Donde se elige:** `BrushIndex` en el componente `TBTool` de `BP_TBPawn` (instance-editable).


## 2026-09-25 (tarde) - LOS 9 PINCELES DE BELTRAN + AUDITORIA + PALETA

Lista pedida: OilPaint, WetPaint, TaperedMarker_Flat, "Pinhead Flat" (-> DoubleTaperedFlat,
sin confirmar), Light, CelVinyl, Petal, Spikes, SoftHighlighter. **Los 9 usan `Stretch`.**

### Los 4 materiales MAESTROS (+ 3 instancias)

Agrupados por modo de mezcla, no uno por pincel - asi cada pincel nuevo es una INSTANCIA
(escritura de propiedades, sin riesgo) en vez de un grafo nuevo:

| Maestro | Modo | Formula | Lo usan |
|---|---|---|---|
| `M_TB_Additive` | Unlit Additive 2S | `tex.RGB * VC * (tex.A * VC.A) * Gain` | SoftHighlighter (Gain 0.617), `MI_TB_Light` (Gain **180.03**) |
| `M_TB_Masked` | Unlit Masked 2S, clip 0.554 | `tex.RGB * VC`, mask `tex.A * VC.A` | CelVinyl, `MI_TB_TaperedMarker` |
| `M_TB_Solid` | Unlit Opaque 2S | `VC` | DoubleTaperedFlat, Petal, Spikes |
| `M_TB_Paint` | Unlit Masked 2S | `Albedo.RGB * VC * (Bump.R*ReliefAmt + 0.45)` | OilPaint, `MI_TB_WetPaint` |

8 texturas + 9 iconos importados del paquete `ob-tools`. Los normal maps en **sRGB=false**.

### Seleccion de fila del ATLAS - `PickAtlasRow()`

OilPaint y WetPaint tienen `m_TextureAtlasV = 4`: su textura son **4 filas apiladas** y cada
trazo elige una al azar. Portado igual que ellos, y **sin operador modulo** (el DSL no lo
tiene): `row = i - (i/n)*n` aprovechando que la division entera trunca.
`i = trunc(UBase * 3331)`, igual que su `m_rng.In01 * 3331`. Corre en `StartStroke` **despues**
de `ApplyPreset` (necesita el `TextureAtlasV` del preset ya puesto).

### AUDITORIA contra los valores reales de Tilt Brush

Leidos de sus descriptores. **Coinciden**: `PressureSizeRange.x` (los 9), `TileRate` (los 9),
`PressureOpacityRange`, `UVStyle`, `TextureAtlasV`, modo de mezcla y textura.

3 desviaciones encontradas y **corregidas**: Light tenia opacidad 1.0 y le corresponde **0.5**
(`{0.5,1}`); OilPaint y WetPaint no declaraban `TextureAtlasV = 4`.

**Desviaciones que quedan, con su razon:**

| # | Que | Por que |
|---|---|---|
| 🔴 1 | **Petal y Spikes usan `TubeBrush`**, no cinta | El generador de tubo NO esta portado. Hoy se dibujan como cinta plana: sus numeros son correctos, su **forma no**. Es lo unico grande que falta de la lista. |
| 🟡 2 | OilPaint/WetPaint: TB es **Lit** con normal map real; nosotros Unlit con relieve falso | 🔴 Nuestras "normales" de `ProceduralMesh` son **la direccion de ensanchamiento, no la normal de superficie** - iluminarlas de verdad daria sombreado incorrecto. El relieve se finge con el canal R del normal map. Deliberado. |
| 🟡 3 | WetPaint `m_SizeVariance = 1` sin portar | No existe sistema de varianza en el pipeline (ver `HashFloat01` en la referencia). |
| 🟡 4 | WetPaint `m_BackfaceHueShift = 0.25` sin portar | Pide **doble cara REAL** (vertices duplicados); usamos material two-sided. |
| 🟡 5 | Spikes `m_RenderBackfaces = 0` (single-sided) y quedo two-sided | Como CINTA, single-sided desapareceria al mirarla por detras - que es justo lo que Beltran reporto en su dia. Corregir **cuando exista el tubo**, no antes. |
| 🟡 6 | `pow(color, 2.2)` de `bloomColor` omitido | Es la conversion sRGB->lineal de Unity; en Unreal los vertex colors **ya son lineales**. Portarlo convertiria dos veces. |

### La paleta - `BP_TBPalette`

Simple a proposito: **un solo `ProceduralMeshComponent` con 9 secciones** (una por pincel) en
rejilla 3x3, cada una con su MID de `M_TB_Icon` y el icono real del pincel. **Seleccion por
PROXIMIDAD**: se acerca la punta derecha a un slot y se elige - sin botones, sin trazas, sin
disputarse el gatillo con el dibujo. El elegido queda al 100% de brillo y el resto al 30%.

Cadena: `BP_TBPawn.SpawnPalette()` (en `Event Possessed`) spawnea y attachea a `MC_Left`, y le
pasa `Setup(TBTool, MC_Right)`. La paleta escribe `BrushIndex` en la herramienta; `BeginStroke`
lo copia a `Preset`; `ApplyPreset` lo aplica al empezar cada trazo.
Posicion editable en el componente `Mesh` de `BP_TBPalette` (hoy `(6,0,6)`, Pitch -35, Yaw 180).

⬜ **Nada de esto esta probado en visor.**


## El GENERADOR DE TUBO (2026-09-25, cierre) - Petal y Spikes

Portado de `TubeBrush.cs`. Confirmado por Beltran: **"Pinhead Flat" = `DoubleTaperedFlat`**.

### Su configuracion real (leida de los prefabs)

| | lados | tapas | ShapeModifier | TaperScalar | Petal |
|---|---|---|---|---|---|
| **Petal** | **5** | no | `Petal` (5) | 1.0 | Amt 1.5, Exp 3 |
| **Spikes** | **3** (tubo triangular) | si | `Taper` (4) | **1.1** | - |

### Las dos curvas de forma, literales

```csharp
case ShapeModifier.Taper:  curve = m_TaperScalar * (1 - t);
case ShapeModifier.Petal:  curve = abs(sin(t * PI));
                           offset = normal * pow(t, PetalExp) * PetalAmt * smoothedPressure;
radius = PressuredSize(smoothedPressure) * 0.5 * RadiusMultiplier * curve;
```

🔑 **`t = distance / totalLength`** - que con `UVStyle = Stretch` **es exactamente nuestro
`K_U` ya normalizado**. `NormalizeU` corre antes que la emision, asi que `ShapeCurve(i)` lo lee
directo. Las piezas encajaron solas.

### Como se implemento

- `ShapeCurve(I) -> float`: 0 = ninguna, 1 = Taper, 2 = Petal. Solo `select`, sin ramas.
- `EmitPassTube()` (106 nodos): anillos de N lados. `dir = Right*cos(a) + Surface*sin(a)` con
  `a = 2pi*j/N` - el marco perpendicular ya lo calcula `FramePass`.
- 🔴 **Bucles PLANOS, sin anidar.** El parser no garantiza un `for` dentro de otro, asi que
  se recorre `k in range(n*N)` y se despeja `i = k/N`, `j = k - i*N`. Igual para los triangulos
  sobre `(n-1)*N`. El cierre del anillo sin modulo: `j2 = select(j == N-1, 0, j+1)`.
- `EmitDispatch()`: `TubeSides >= 3` -> tubo, si no -> cinta. `RebuildChunk` pasa a llamarlo a el.
  **Las 7 cintas ponen `TubeSides = 0` explicito**, asi que un preset no contamina al siguiente.

### Desviaciones del tubo, anotadas

- **Sin tapas.** Spikes las tiene (`m_EndCaps: 1`), pero su `Taper` lleva el radio a 0 al final,
  asi que la tapa que se veria es la del ARRANQUE. Con material opaco two-sided se ve el
  interior. Pendiente si molesta.
- **Sin aristas duras.** TB duplica vertices por cara (`m_HardEdges: 1`); aca el anillo es de N
  vertices compartidos. Con 3 y 5 lados y material sin textura la diferencia es el sombreado de
  la arista, que siendo Unlit no se nota.
- **El empuje de Petal** va sumado al radio en vez de a lo largo de la normal suave; en un tubo
  la normal del vertice **es** su direccion radial, asi que es equivalente salvo en las tapas.
- **Devanado de triangulos sin verificar** - si el tubo sale invertido no se nota (two-sided),
  pero corregir antes de migrar a Soul Charger.

### `DoubleTaperedFlat` - verificado, no necesita nada especial
Su shadergraph **no tiene ningun nodo de taper** (es lit estandar) y no tiene prefab propio: usa
el compartido de `FlatGeometryBrush`. **Su afinado doble sale de la PRESION**, igual que el
nuestro. Somos fieles.


## 2026-09-26 - REARQUITECTURA: `BP_TBDrawRig`, el actor AUTOINSTALABLE

🔴 **Correccion de Beltran, y es de arquitectura, no de detalle:**
*"En Soul Charger estamos intentando no tocar nada dentro del VRPawn. Sino construir BP con
cada mecanica que llamen al PAWN. Pero no tocamos el event graph del pawn, esa es la idea de
mantenerlo clean."*

Yo habia construido `BP_TBPawn` a medida y le habia cableado input, paleta y herramienta. Eso
**no migra**: en Soul Charger el destino es su VRPawn (duplicado del de VRTemplate) y no se
toca. Tambien probe duplicar el VRPawn y lo **descarte**: un pawn paralelo tampoco es la forma.

### La forma correcta: una mecanica = un actor que se instala solo

**`BP_TBDrawRig`** se COLOCA EN EL NIVEL y no pide nada al pawn:

| Funcion | Que hace |
|---|---|
| `CheckController` | en BeginPlay y en Tick, si no esta listo reintenta (el pawn puede no estar poseido aun) |
| `FindControllers` | `GetPlayerPawn` -> `Actor|GetComponentsByClass(MotionControllerComponent)` |
| `SortController` / `SortLeft` | 🔑 clasifica **por su `MotionSource`**, no por nombre: `RightAim` y `LeftGrip` |
| `InstallInput` | `Input|EnableInput` sobre el PlayerController + sus propios IMC (con las opciones correctas, gotcha 388) |
| `TryInstall` | `FindControllers` -> `IsValid(RightAim)` -> `DoInstall`. **Solo exige la mano derecha** (ver abajo) |
| `DoInstall` | `InstallInput` -> `TBTool.Setup(RightAim)` -> `MountPalette` -> `bReady = true` |
| `MountPalette` | spawnea `BP_TBPalette`, la attachea al `LeftGrip` y le pasa `Setup(TBTool, RightAim)`. Se protege sola con `IsValid(LeftGrip)`. Tambien cuelga y enciende `SM_LHand` |
| `MountHands` | cuelga `SM_RHand` del `RightGrip` con `KeepRelative` y lo enciende. Protegida con `IsValid(RightGrip)` |
| `SortRGrip` | tercer paso de clasificacion: captura el `RightGrip` (la malla del mando va en el GRIP, no en el Aim) |
| `TB_Press` / `TB_Release` / `TB_Pressure` | rutean el input a la herramienta |
| EventTick | ademas de reintentar la instalacion, **consulta el gatillo cada cuadro** y se lo pasa a `TBTool.GateStop(Held)` |

El actor **hostea sus propios eventos de Enhanced Input** (`IA_Shoot_Right` Started/Completed,
`IA_Hand_IndexCurl_Right` Triggered), lo cual es posible en un Actor gracias a `EnableInput`.

💡 **Clasificar por `MotionSource` en vez de por nombre de componente** es mas robusto que el
patron `[[BP_BreathManager_SC]]` de buscar por nombre: sobrevive a que alguien renombre el
componente, y es semantico. El nombre solo lo sabe quien escribio ese pawn; el `MotionSource`
lo define el runtime de XR.

### Lo que quedo del pawn de prueba
`BP_TBPawn` se **limpio**: se le desconectaron (no borraron) `Setup`, `OnTriggerStart`,
`OnTriggerEnd`, `OnCurl`, `SetPressure` y `SpawnPalette`. Queda como un pawn VR pelado con
camara, mandos y los meshes (`SetupHands`, que se reconecto a proposito). Asi el rig es el
unico que dibuja y se prueba el camino de instalacion real.

⚠ Al desconectar `SpawnPalette` quedo huerfano `SetupHands` (colgaba de el). **Cortar un
nodo de una cadena deja sin exec a todo lo que venia despues** - la lectura post-cirugia lo
atrapo. Reconectado al ultimo `AddMappingContext`.

### 2026-09-26 - Por que no funcionaba en visor, y los dos arreglos

Beltran probo el rig y no pasaba **nada**: ni paleta ni dibujo. Pregunto si estaba mal el
GameMode o la referencia al pawn. **No era eso** (queda verificado, para no volver a mirar ahi):
`WorldSettings.DefaultGameMode = GM_VR`, el `BP_TBPawn_C_0` colocado tiene
`AutoPossessPlayer = Player0` y por eso gana la posesion — el `DefaultPawnClass` de `GM_VR`
(`VRPawn`) **nunca se llega a spawnear**, porque `RestartPlayerAtPlayerStart` solo crea el pawn
por defecto en el `else` de "el controller ya tiene pawn". Y `DefaultInput.ini` tiene
`DefaultInputComponentClass=EnhancedInputComponent`, requisito para que un **Actor** reciba
eventos de Enhanced Input via `EnableInput`.

🔴 **La causa real: los dos grips del pawn tenian `MotionSource = "Left"`.** Los cree con el
nombre `MC_RGrip` / `MC_LGrip` y nunca les escribi el `MotionSource`, que **nace en `Left`**.
`SortLeft` busca `LeftGrip` -> nunca lo encontraba -> el gate no pasaba -> no se instalaba nada.
Arreglado en la plantilla **y en la instancia del nivel** (la instancia lo tenia como override
propio y no heredo el cambio del CDO). Detalle en gotcha 392.

🔴 **Y una fragilidad de diseno, arreglada:** el gate era `IsValid(RightAim)` **y**
`IsValid(LeftGrip)` antes de instalar, asi que faltando un mando se perdia tambien el dibujo y
el sintoma no señalaba nada. Ahora `TryInstall` solo exige `RightAim` y `MountPalette` se
protege sola. Una mano izquierda mal configurada cuesta **solo la paleta**. `CheckLeft` quedo
sin uso y **se borro**. Gotcha 393.

✅ **Verificado sin casco**: dos `PrintString` temporales al final de `DoInstall` y de
`MountPalette`, `StartPIE` en viewport, `GetLogEntries(category:"LogBlueprintUserMessages")` ->
`TBRIG install OK` + `TBRIG palette OK`. Prints borrados, todo compilado y guardado.
⬜ **Falta la prueba en visor** (que el trazo salga de la mano y que la paleta se pueda apuntar).

### 2026-09-26 (2a) - La sesion de visor: cuatro bugs, cuatro causas distintas

Beltran probo cuatro veces. Cada pasada aislo una causa; **ninguna era la misma**.

**1. No dibujaba.** El nodo `EnableInput` tenia el PlayerController en el pin **`self`** y el
parametro `PlayerController` vacio. Como un PlayerController *es* un Actor, compilo limpio y no
hizo nada: el rig nunca registro su InputComponent. Lo delataron las sondas — `PAWN hands` si
imprimia, `RIG press` y `RIG curl` nunca. Gotcha 394. 🔴 Mi verificacion en PIE de la pasada
anterior **no lo agarro porque probaba que la funcion corria, no que hiciera efecto**.

**2. No se veian los mandos.** La instancia del nivel tenia `staticMesh = None` en los
componentes, aunque el Blueprint los tenia asignados. Gotcha 396.

**3. El trazo se quedaba pegado, fino.** `IA_Hand_IndexCurl_Right` **no es el gatillo**: es la
curvatura capacitiva del dedo, y con el dedo apoyado nunca baja del umbral 0,08 donde yo habia
colgado el corte. El log lo mostro: esa accion dispara en **todos** los cuadros, incluso antes de
apretar. Reemplazado por el modelo de TB: el Tick del rig consulta `IA_Shoot_Right` y se lo pasa
a `GateStop(Held)`; el gatillo decide si el trazo vive, el dedo solo modula el grosor. Gotcha 395.
**El gate por presion era invencion mia**, puesta para tapar §387.

**4. Los mandos en mala posicion y con material que reventaba la vista.** Dos causas: mi
`SetupHands` los colgaba con `SnapToTarget` en posicion **y** rotacion, regla que **borra
cualquier offset**; y el material original es lit y brillaba. A pedido de Beltran los mandos
**pasaron del pawn al rig** (la mecanica trae sus propios visuales).

#### Las transformadas correctas (de `BP_HandRig_NC` y del `VRPawn` del VRTemplate, identicas)
El izquierdo colgaba directo del grip; el derecho colgaba de un `HandRight` intermedio (el
maniqui `B_MannequinsXR`), asi que hubo que **componer** las dos transformadas
(`scratchpad`, verificado reconvirtiendo la matriz a rotador: error 1e-16).

| | Posicion | Rotacion | Escala |
|---|---|---|---|
| `SM_RHand` sobre `RightGrip` | 5.685942, 0.540018, -1.677589 | -13.566261, -83.539335, 64.230738 | 1.0875 |
| `SM_LHand` sobre `LeftGrip` | 5.876514, -1.566667, -2.049637 | 0, -95, 65 | 1.0875 |

Se cuelgan con **`KeepRelative`** (no `SnapToTarget`), asi que lo que se ve en el panel de
detalles es lo que queda en la mano. Nacen con `bVisible = false` y se encienden al colgarse,
para que no floten en la posicion del rig durante los ~7 s que tarda la posesion del pawn.

**Material:** `M_TBHand_NC` (unlit, opaco) + `MI_TBHand_NC` con parametro `Tint` (gris 0,09).
Sin especular, no puede reventar con ninguna luz. El color se ajusta en la instancia.

🟢 **Validado en visor el 2026-09-26**: dibuja, corta limpio al soltar, paleta y mandos a la vista.

### El contrato de migracion a Soul Charger
**Colocar `BP_TBDrawRig` en el nivel. Nada mas.** No se toca el VRPawn. Si su VRPawn usa otros
IMC, se cambian los dos que agrega `InstallInput`.

⚠ **Lo unico que el rig le exige al pawn:** un `MotionControllerComponent` con
`MotionSource = RightAim` y otro con `LeftGrip`. El VRPawn del VRTemplate los tiene con esos
valores exactos (verificado), asi que en Soul Charger no hay nada que tocar — pero **si alguien
agrego mandos a mano, hay que leer su `MotionSource`, no confiar en el nombre**.

⚠ **Y si el rig gana componentes DESPUES de colocarlo, hay que volver a colocarlo**: recompilar
no actualiza una instancia ya puesta (gotcha 396). Vale tanto para este nivel como para Soul Charger.

## 2026-09-26 (3a) - PETAL: tres causas, y la tercera no era geometria

Reporte de Beltran en visor: *"el pincel de petal esta saliendo gigantesco y como que los petalos
nunca se abren... los tres tubos gordisimos todos juntos y no se ve como una flor"*.
Su descripcion del original era exacta: **parte en punta y son tres tubos que se abren como flor.**

### 1. `BrushSize` 12.0 -> 2.0 (el 6x de "gigantesco")

Auditoria de los nueve contra `m_BrushSizeRange.y` de Tilt Brush. **La regla que se uso al
portarlos es `BrushSize = maximo de TB x 2`**, y la cumplen ocho de nueve:

| # | Pincel | TB max | x2 | puesto | |
|---|---|---|---|---|---|
| 0 | TaperedMarkerFlat | 1.0 | 2.0 | 2.0 | ✓ |
| 1 | DoubleTaperedFlat | 3.0 | 6.0 | 6.0 | ✓ |
| 2 | SoftHighlighter | 2.0 | 4.0 | 4.0 | ✓ |
| 3 | Light | 0.2 | 0.4 | 0.8 | 2x, se deja (0.4 cm es un pelo invisible) |
| 4 | CelVinyl | 1.5 | 3.0 | 3.0 | ✓ |
| 5 | OilPaint | 1.5 | 3.0 | 3.0 | ✓ |
| 6 | WetPaint | 1.25 | 2.5 | 2.5 | ✓ |
| 7 | **Petal** | **1.0** | **2.0** | **12.0** | 🔴 el bug |
| 8 | Spikes | 2.0 | 4.0 | 4.0 | ✓ |

### 2. El empuje del petalo estaba a la MITAD

TB (`TubeBrush.cs:773-777, 790`):
```csharp
petalAmtCacheValue = m_PetalDisplacementAmt * POINTER_TO_LOCAL * m_BaseSize_PS;   // = 1.5 * S
curve  = abs(sin(t*PI));
offset = m_geometry.m_Normals[vert] * pow(t, exp) * petalAmtCacheValue * smoothedPressure;
vertex = offset + center + radius * dir * curve;     // radius = S * 0.5
```
✅ **Confirmado leyendo `MakeClosedCircleSoftEdges`: el normal del vertice ES `dir`, la direccion
radial** (`AppendVert(..., center + radius*dir, dir, ...)`). Asi que sumar el empuje al radio es
correcto — eso del tracker estaba bien.

🔴 Lo que estaba mal: en `EmitPassTube` el termino era `S * 0.5 * (t^exp * PetalAmt * p)`. El
`0.5` es del RADIO, el empuje **no lo lleva**. Resultado: la campana abria a 0.75·S en vez de
1.5·S, o sea **1,5x el radio medio en vez de 3x** — no se leia como apertura.
Arreglado en el `MakeLiteralFloat` exclusivo de ese termino (0.5 -> 1.0); `PetalAmt` queda en 1.5,
fiel. Silueta correcta: punta en t=0, radio maximo S·0.5 en t=0.5, y anillo abierto de radio
1.5·S en t=1.

### 3. 🔴 Lo de fondo: Petal en Tilt Brush NO es color plano

Petal vive en **`ob-tools/Runtime/Shaders/4_DiffuseSpecials/Petal/`** — familia DIFUSA, con su
propio `Petal.hlsl`:
```hlsl
float4 darker_color = vertexColor * 0.6;
finalColor = lerp(vertexColor, darker_color, 1 - uv.x);   // = vc * (0.6 + 0.4*u)
fAO = vface == -1 ? .5 * uv.x : 1;                        // cara trasera: interior mas oscuro
```
`uv.x` es la distancia normalizada = nuestro `K_U` (UVStyle Stretch). **Nuestro `M_TB_Solid` era
emisivo = vertex color: una silueta absolutamente plana, sin relieve interno.** Con la geometria
correcta igual se habria visto un bulto, porque no habia NADA que leyera la forma.

Portado literal dentro de `M_TB_Solid`, con parametro escalar **`PetalShade`, default 0 = NEUTRO**
(regla del `BeadAmp`, gotcha 375: un parametro nuevo en material compartido no puede degradar lo
aprobado — Spikes y DoubleTaperedFlat siguen exactamente igual):
```
u        = TexCoord0.x
grad     = lerp(0.6, 1.0, u)
backMask = -0.5 * TwoSidedSign + 0.5          // 0 cara frontal, 1 trasera
ao       = lerp(1.0, 0.5*u, backMask)
emissive = VertexColor * lerp(1.0, grad*ao, PetalShade)
```
`MI_TB_Petal` (nueva) pone `PetalShade = 1`, y `Brush_Petal` apunta ahi en vez de al maestro.

⬜ **Los tres arreglos estan sin ver en visor.**

### Deviacion del tubo que SIGUE abierta
`m_HardEdges: 1` en Petal (y en TB los anillos son `points*2` vertices con normal por cara).
Nuestro anillo es de N vertices compartidos. Con el sombreado por `u` no cambia nada — el
gradiente va A LO LARGO del trazo, no alrededor del anillo. Solo importaria con iluminacion real.

## 2026-09-26 (3b) - El "color rojizo" NO era color: era ancho

Reporte con fotos: *"el primer pincel de lapiz sale con un color mas rojizo que naranjo"* y
*"Light sale blanco"*.

### Lo que dijeron los pixeles (gotcha 402)

Midiendo las capturas en vez de mirarlas:

| | ancho | opacidad efectiva | a color pleno |
|---|---|---|---|
| Pincel 0 (TaperedMarker Flat) | **8 px** | mediana **0,23** | **0,1%** |
| El comparado (DoubleTaperedFlat) | 58 px | 1,00 | 95,3% |

🔑 **El nucleo de los DOS trazos es exactamente (255, 140, 50)** — el naranja elegido, exacto.
El color esta bien. Lo que pasa es que el pincel 0 sale **tan fino que casi no llega a pintar**:
naranja al 23% sobre el fondo azul marino da rosa sucio, que es lo que se ve.

✅ **Y de yapa:** que diera (255,140,50) y no (213,124,40) **prueba que el preview Android NO
aplica tonemapper** (consistente con `r.MobileHDR=False`). Toda la linea de investigacion del
tonemapper quedo descartada por medicion, no por opinion.

### El ancho: la presion

`TaperedMarker` tiene `PressureSizeMin = 0.0` (fiel a TB: `m_PressureSizeRange {0,1}`), asi que
su ancho **es** `BrushSize * presion`. Con 6 cm = 58 px, los 8 px del pincel 0 implican ~1-2 mm
de geometria real, o sea **presion del orden de 0,05-0,1**. ⬜ Sonda puesta para saber el valor
exacto (abajo) en vez de seguir infiriendo.

⚠ **Correccion de la gotcha 395, que estaba mal:** `IA_Hand_IndexCurl_Right` **SI es el gatillo**
— esta mapeada a `OculusTouch_Right_Trigger_Axis`, el eje analogico. La capacitiva es
`IA_Hand_Point_*` (`Trigger_Touch`). Confirmado por eliminacion sobre `IMC_Hands`.
`IA_Shoot_Right` (el gate) esta en `IMC_Weapon_Right` sobre `Trigger_Click` y es **Boolean**.
🔴 `ObjectTools.get_properties(<IMC>, ["Mappings"])` devuelve `[]` aunque el IMC tenga mapeos: hay
que leer las teclas con `grep -a` sobre el `.uasset`.

### `MI_TB_Light`: Gain 180.03 -> 4.0

El 180,03 era **literal de TB** (`_EmissionGain: 0.45` y `2*exp(gain*10)` en su `Bloom.shader`),
pero es un valor **HDR**: alla lo de arriba de 1 se vuelve bloom. Con `r.MobileHDR=False` no hay
rango: **todo pixel con alfa > 1/180 clipea a blanco** → el pincel entero sale blanco.
Con ganancia `G` se quema la parte del trazo donde `alfa > 1/G`; **`G = 4`** quema el cuarto mas
denso y deja el resto como caida de color (nucleo blanco, halo naranja). `Gain` es la perilla.
Ver gotcha 401.

### Sonda temporal puesta
`BPC_TBTool_NC:EventTick`, dentro de `if bDrawing`, despues de `FeedStroke`:
`PrintString(ToString(Pressure))` con **Key = "PRESION"** (reescribe la misma linea en vez de
apilar). 🔴 **Sacarla cuando se sepa el valor.** De paso se borro la sonda vieja
`"TOOL gate release"` de `GateStop`, que ya estaba validada.

## 2026-09-26 (3c) - Segunda pasada de visor: tres sintomas, tres causas de Tilt Brush

Presion **medida en visor: llega a 1**. Eso mato mi hipotesis de "sale fino por presion baja".
Pedido de Beltran, y va como regla: **"Procura revisar siempre desde lo que tiltbrush tiene"**.

### El "pincel de lapiz mas rojizo" es un pincel ADITIVO

Descartados por medicion, en este orden: el valor del color (nucleo = (255,140,50) exacto),
el material, la textura (RGB blanco puro), el tonemapper (no se aplica) y el **encogimiento de
alfa por mipmap** (cobertura sobre el clip: 65,9% en mip0 y 65-75% en todos los demas → no
encoge).

Lo que si dio: ajustando los pixeles a dos modelos, **gana el ADITIVO** — error mediano 27
contra 46 del modelo "se mezcla con el fondo". Nucleo medido **(208, 116, 116)**, ganancia ~0,6
(SoftHighlighter tiene `Gain 0.617`). El `Bloom.shader` de TB confirma `Blend One One`.

🔑 **Sumar naranja sobre un fondo azul (B=112) deja el azul abajo: el B final nunca baja de
~110 y el tono queda rosa. No es del pincel, es del fondo.** En Tilt Brush el entorno es oscuro
y por eso los aditivos conservan su tono. Se comprueba en un segundo: dibujar contra una zona
oscura de la escena.

### Light: la textura esta, el halo es BLOOM

De su fuente: prefab `Line.prefab` = `QuadStripBrushStretchUV` (cinta — igual al nuestro ✓),
`m_PressureOpacityRange {0.5,1}`, `Blend One One`, y el frag termina en
`color = encodeHdr(color.rgb)`. **El halo de color que recuerda Beltran es el bloom del
pipeline HDR.** Con `r.MobileHDR=False` no hay bloom: no hay halo posible sin cambiar eso o
falsearlo con una segunda pasada mas ancha y tenue. La textura si la tenemos y es la real.

### Petal: el que faltaba era el SOMBREADO FACETADO

Su prefab es el tubo ✓ y los numeros ya estan bien (3a), pero su shader vive en
**`4_DiffuseSpecials`** — es **difuso, o sea iluminado** — y el prefab trae **`m_HardEdges: 1`**.
Las cinco caras planas reciben luz distinta: **eso** son los petalos. El nuestro era color plano
con normales suaves compartidas → jamas se iba a facetar.

Agregado a la rama de `PetalShade` en `M_TB_Solid` (sigue con default 0 = neutro):
```
P        = WorldPosition (Camera Relative)         // camara-relativa por precision movil (gotcha 398)
N_cara   = normalize(cross(ddy(P), ddx(P)))        // Custom: normal de CARA, no de vertice
lambert  = dot(N_cara, (0.5,0.6,0.62)) * 0.5 + 0.5 // medio-lambert, nada cae a negro
emissive = VertexColor * lerp(1, grad*ao*lambert, PetalShade)
```
🔑 **`ddx/ddy` da la normal de cara en el pixel shader: es el equivalente de `m_HardEdges` sin
tocar la geometria** (que en el DSL seria reescribir `EmitPassTube` con 2N vertices por anillo).
⚠ Desviacion consciente: TB usa luz real de escena; aca es una direccion fija. Precedente en el
proyecto: `M_PaintRibbon_NC` ya tiene `ShadeAmount`/`ShadeLightDir`. La direccion es la perilla.

⬜ Sin ver en visor.

## 2026-09-26 (3d) - PETAL RESUELTO: `m_HardEdges` no es sombreado, es el MECANISMO

Beltran mando un dibujo: ✗ tres hojas pegadas en un manojo; ✓ las mismas tres **abiertas en
abanico**, unidas solo en la punta de abajo. Eso obligo a leer la funcion que yo **no** habia
leido: Petal tiene `m_HardEdges: 1`, asi que usa `MakeClosedCircleHardEdges`, no la de aristas
suaves que yo si habia verificado.

```csharp
// MakeClosedCircleHardEdges: DOS vertices COINCIDENTES por angulo, con normales DISTINTAS
Vector3 nCur  = -cos(theta + dTheta)*up - sin(theta + dTheta)*rt;   // cara siguiente
Vector3 nPrev = -cos(theta - dTheta)*up - sin(theta - dTheta)*rt;   // cara anterior
AppendVert(k, center + radius*off1, nPrev, ...);   // mismo sitio
AppendVert(k, center + radius*off1, nCur,  ...);   // normal distinta
AppendDisplacement(k, off1);                       // el RADIO si es compartido

// ApplyShapeModifiers, Petal:
offset = m_geometry.m_Normals[vert] * pow(t,exp) * petalAmt * p;   // <- a lo largo de la NORMAL
vertex = offset + center + radius * dir * curve;                   // dir = m_Displacements
```

🔑 **Los dos vertices que comparten una arista se van en direcciones DIFERENTES** a medida que
crece `t^exp`: el tubo **se rasga en N petalos** unidos en el arranque (donde `t^3 ≈ 0`).
Con nuestro anillo de N vertices compartidos y normal radial, el empuje mantenia el anillo
cerrado → salia una trompeta, nunca una flor. **`m_HardEdges` es el mecanismo de la separacion,
no un detalle de sombreado**, y la nota del tracker que decia "sumarlo al radio es equivalente"
era falsa justo para Petal (era cierta solo para la version de aristas suaves).

### `EmitTubeHard` (funcion NUEVA, reemplaza a `EmitPassTube` en `EmitDispatch`)

2N vertices por anillo. Para `k` en `[0, nudos*2N)`: `i = k/2N`, `r = k-i*2N`, `j = r/2`,
`side = r-2j`.
```
th   = 2pi*j/N                      dth = pi/N
thn  = th - dth  si side==0,  th + dth  si side==1      ; normal de la cara anterior / siguiente
off  = Right*cos(th)  + Surface*sin(th)                 ; radio, compartido
nrm  = Right*cos(thn) + Surface*sin(thn)                ; NORMAL DE CARA, distinta por vertice
pos  = K_Pos[i] + off*(size*0.5*curve) + nrm*(size*petal)
UV.y = 1.0 si (side==0 y j==0), si no j/N               ; la costura de TB, sin vertice extra
```
Triangulos por cara `j`: `(cB_j, nB_j, cA_j+1)` y `(cA_j+1, nB_j, nA_j+1)`, con
`A = base+2j`, `B = base+2j+1`. **Ya no hace falta cerrar el anillo con modulo en los UV**:
cada cara tiene su propio par, asi que de paso desaparece la costura de UV que teniamos.

✅ Spikes tambien trae `m_HardEdges: 1` → el emisor nuevo es el correcto para los dos tubos.
⚠ `EmitPassTube` (el viejo, de anillo compartido) quedo en el BP sin llamadas. Borrarlo cuando
esto se valide en visor.

### El sombreado, ahora que la malla trae normales de cara de verdad
Se saco el `Custom` con `ddx/ddy` (era un parche para fabricar normales de cara desde el pixel
shader, y ademas arriesgado en movil por precision — gotcha 398) y se cambio por
**`VertexNormalWS`**, que ahora ES la normal de cara. La cadena de `PetalShade` queda:
```
emissive = VertexColor * lerp(1, grad * ao * lambert, PetalShade)
grad    = lerp(0.6, 1.0, u)                     ; literal de petalFrag
ao      = lerp(1.0, 0.5*u, caraTrasera)         ; literal de fAO
lambert = dot(VertexNormalWS, (0.5,0.6,0.62)) * 0.5 + 0.5
```

## 2026-09-26 (3e) - Light: el halo es bloom, y el ancho tambien

De su fuente: `m_BrushSizeRange {0.05, 0.2}` — **Light es fino a proposito**, diez veces mas
fino que OilPaint. Su grosor aparente **lo pone el bloom**: `Blend One One` + el frag termina en
`encodeHdr(color.rgb)`. Con `r.MobileHDR=False` no hay bloom, asi que no hay ni halo ni grosor.

**Decision tomada, y es una desviacion consciente:** si el halo no puede venir del post-proceso,
tiene que venir de la geometria. `BrushSize` 0.8 → **3.0**. El razonamiento, para que sea
revisable y no un numero al azar: el valor fiel seria 0.4 (regla `max*2`), y el bloom de TB
multiplica el ancho aparente por ~7 → 0.4*7 ≈ 3.
`Gain` 4 → **2**: con `G=4` el canal R **y** el G clipeaban (`0.2636*a*4 ≈ a`) → blanco plano
sin textura; con `G=2` solo clipea el R (nucleo caliente) y el verde nunca llega a 1, asi que
**la textura y el degradado vuelven a verse**. Regla: el canal C clipea donde `a > 1/(color_C*G)`.

⚠ **Lo que NINGUN ajuste del pincel arregla:** aditivo sobre fondo azul. El azul del fondo queda
debajo (B >= 110) y tine de rosa todo lo aditivo. En Tilt Brush el entorno es oscuro. Las salidas
son fondo oscuro, o encender `r.MobileHDR` (que ademas devolveria el bloom de verdad) — **decision
de Beltran, porque cuesta rendimiento en Quest**.

## 2026-09-26 (3f) - 🟢 PETAL SE ABRE EN VISOR. Los dos remates, con aritmetica

Beltran: *"Ahora si se abren"*. La separacion por aristas duras esta **validada en visor**.

### La punta poligonal: no se arregla con mas nudos

Medido, con S = 2 cm y separacion entre nudos `0.2 + S*0.2 = 0.6 cm`:

| t | ancho de la hoja | paso lateral por nudo (trazo 15 cm) | (trazo 30 cm) |
|---|---|---|---|
| 0.50 | 1.18 cm | 0.09 | 0.05 |
| 0.90 | 0.36 cm | 0.29 | 0.15 |
| **0.97** | **0.11 cm** | **0.34 → ESCALERA** | **0.17 → ESCALERA** |

🔑 **El paso supera al ancho solo a partir de t≈0.95, y en los dos largos de trazo.** Duplicar
los nudos no lo arregla: a esa altura la hoja ya tiene ancho ~0 (`|sin(t·pi)| → 0`) mientras la
punta sigue acelerando (`t^3`). **Es estructural de la formula, no de la teselacion.**
✅ Verificado que el espaciado es fiel: TB usa `m_SolidMinLengthMeters_PS + PressuredSize*0.2`
con `0.002` para los tres pinceles que miramos, y nosotros `SolidMinLengthCm=0.2` + `0.2`.

**Arreglo: `TipMinCurve`** — variable nueva, **default 0 = NEUTRO**, usada solo dentro de la rama
`ShapeMod == 2` de `ShapeCurve`:
```
curve = max(|sin(u*pi)|, TipMinCurve)
```
`Brush_Petal` la pone en **0.15** → la hoja nunca baja de ~0.18 cm de ancho y la punta termina
en un remate chico en vez de una aguja. **No hace falta multiplicar por `u`**: en `t=0` el empuje
es 0, asi que las 5 caras quedan en un pentagono de 1.5 mm de radio — sigue leyendose como punta.
⚠ Desviacion consciente de TB (ellos llegan a ancho 0). `TipMinCurve` es la perilla.
⚠ `DoubleTaperedFlat` tambien usa `ShapeMod 2`, pero **el trazo es un actor NUEVO por trazo**, asi
que arranca del CDO (0) y solo Petal se lo cambia. No hace falta ponerlo en los otros ocho.

### Light: ningun valor del pincel lo arregla, es el FONDO

Color de cada zona del trazo (aditivo, `Gain 2`), calculado:

| zona | sobre el azul del nivel | sobre fondo oscuro |
|---|---|---|
| centro | (255, 178, 128) | (255, 177, **67**) |
| medio | (255, 156, 124) | (255, 154, **58**) |
| halo | (164, 91, **116**) | (162, 88, **32**) |

🔑 El fondo aporta **B = 0.162 en lineal**, asi que el canal azul del trazo **nunca baja de 112**:
eso es lo que lava el naranja hacia blanco y borra el halo. Sobre oscuro con **`Gain 4`** el centro
da (255,241,93) y el borde (221,121,45) — literalmente *"quema un poco a blanco pero tiene un halo
del color alrededor"*, que es como Beltran recuerda el de TB.
⬜ **Pendiente de decision**: fondo oscuro en `L_TBTest` (gratis, y es el entorno real de TB) o
`r.MobileHDR=True` (devuelve el bloom de verdad, cuesta rendimiento). `Gain` quedo en **2** porque
es lo mejor sobre azul; **si el fondo se oscurece, subirlo a 4**.

## 2026-09-26 (3g) - PALETA REDUCIDA A 4 + RUEDA DE COLOR

Pedido de Beltran: *"dejar solo los pinceles 3, 4, 6 y 9, el resto que queden guardados"* y
*"agregar junto a la seleccion de pinceles una rueda de color... se selecciona solo tocando,
sin trigger"*.

### 🔴 La paleta se ve ESPEJADA: su numeracion NO es el indice del array

El componente `Mesh` esta con **Yaw 180**, asi que el eje Y local se invierte para el que mira:
la columna que el codigo pone a la izquierda **aparece a la derecha**. La grilla se arma
row-major desde arriba-izquierda en local, pero se LEE al reves por fila.

Dos evidencias independientes lo confirman: (1) la geometria del componente, y (2) el pincel que
Beltran llamo *"el primero"* resulto ser, por medicion de pixeles, el **aditivo** = indice 2 — que
solo cae en la posicion 1 si la fila esta invertida.

| el ve | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| indice | 2 | 1 | **0** | **5** | 4 | **3** | 8 | 7 | **6** |

Sus 3/4/6/9 = **TaperedMarker Flat, OilPaint, Light, WetPaint**.

### `BrushIds`: la paleta pasa a ser una LISTA, no los 9 fijos

Variables nuevas en `BP_TBPalette` (todas editables en el panel):
`BrushIds` (int[], **[0,5,3,6]**), `Cols` (2), `WheelOffset` ((0,-5.6,0)), `WheelRadius` (2.4).

- **`BuildUI`** (reemplaza a `BuildPalette`, que queda sin llamadas): arma `Length(BrushIds)`
  slots en grilla de `Cols` columnas, **centrada** — `Y = (col - (Cols-1)/2)*Pitch`,
  `Z = ((rows-1)/2 - row)*Pitch`, con `rows = (n + Cols - 1)/Cols`. El icono sale de
  `Icons[BrushIds[i]]`, asi que **los 9 iconos y los 9 presets siguen ahi**: cambiar la paleta es
  editar un array de enteros.
- **`SendToTool`** manda `BrushIds[Selected]`, no el indice del slot.
- `TestSlot` y `ApplyHighlight` no se tocaron: recorren `Slots`/`Mids`, que ahora tienen 4.

### La rueda de color

Una seccion mas del mismo ProceduralMesh (indice `n`), un quad con `M_TB_ColorWheel`.

`M_TB_ColorWheel` — Unlit / Masked / two-sided, un `Custom` sobre la UV:
```hlsl
float2 c = UV*2-1;  float r = length(c);
float h = atan2(c.y, c.x) * 0.15915494 + 0.5;
float3 k = frac(h + float3(0, 2.0/3, 1.0/3)) * 6 - 3;
float3 rgb = lerp(1, saturate(abs(k)-1), saturate(r));
return float4(rgb, r < 1 ? 1 : 0);      // alfa = la mascara del disco
```

`TestWheel` (llamada al final de `PickSlot`, o sea **cada tick, sin gatillo**):
```
tipL = InverseTransformLocation(Mesh.WorldTransform, Tip.WorldLocation)
d    = tipL - WheelOffset
si |d.yz| < WheelRadius y |d.x| < PickRadius:
   SetWheelColor(atan2(-d.z, d.y) + 180, clamp(|d.yz| / WheelRadius))
```
`SetWheelColor(H,S)` hace `HSVtoRGB(H, S, 1, 1)` y lo escribe en `BrushColor` de la herramienta.

🔑 **El `-d.z` del atan2 no es un capricho**: la UV del quad tiene V creciendo hacia ABAJO
(`Q_UV` pone V=1 en los vertices de abajo), asi que el `c.y` del material es el negativo del Z
local. Sin ese signo, el color que se toca no es el que se ve.
✅ El espejado de la paleta **no afecta** a la rueda: lo visible y la deteccion salen de la misma
coordenada local, asi que coinciden. Solo se ve el circulo cromatico en sentido antihorario.

⚠ La rueda escribe color mientras el dedo este adentro, pero `BeginStroke` copia `BrushColor` a
`BaseColor` **al empezar** el trazo, asi que cambiarlo a mitad no altera el trazo en curso.
⬜ Sin visor.

## 2026-09-26 (3h) - Punta visible, grosor por joystick, y la rueda corrida

### 1. `SM_Tip`: la esfera desde donde nace todo
Beltran: *"al controller le falta alguna esfera chiquitita al frente, que sea desde donde nace el
dibujo y el punto desde donde se seleccionan las cosas. Sino es muy dificil con el control tan
grande."*

Componente nuevo en `BP_TBDrawRig`: **`SM_Tip`** (esfera de motor, escala 0.012 = 1,2 cm),
material `MI_TB_Tip` (instancia de `M_TBHand_NC` con `Tint` claro), invisible en reposo.
`MountTip` la attachea a `RightAim` con `KeepRelative` y la enciende — offset **(2.5, 0, 0)**,
editable en el panel.

🔑 **Y pasa a ser el TIP de todo**: `DoInstall` le manda `SM_Tip` (no `RightAim`) al
`Setup` de la herramienta, y `MountPalette` se lo manda al `Setup` de la paleta. O sea que la
misma esfera es el origen del trazo Y el puntero de seleccion — que es justo lo que pidio.

🔴 **Hay que RECOLOCAR el rig en el nivel**: gotcha 396, una instancia ya puesta no recibe
componentes nuevos (los crea con `staticMesh: None` y transform en cero).

### 2. Grosor por el joystick derecho, con la curva de TB

De su fuente (`PointerScript.BrushSize01` + `DevOptions.BrushLerp = Default`):
```csharp
_FromRadius(x) = sqrt(x)              // BrushLerp.Default == SqrtRadius
BrushSizeAbsolute = _ToRadius( Lerp( sqrt(min), sqrt(max), Clamp01(t) ) )   // = (...)^2
```
🔑 **No es un lerp lineal: interpola en la RAIZ del tamano**, que es lo que hace que el extremo
fino tenga resolucion fina. Portado literal en `ApplySizeSlider` (llamada al final de
`ApplyPreset`, o sea despues de que el preset fijo sus valores):
```
BrushSize = ( lerp( sqrt(SizeMins[Preset]), sqrt(BrushSize), Size01 ) )^2
```
`BrushSize` del preset **ya era** el maximo de TB (regla `max*2`), asi que sirve de `max` sin
tocar los nueve `Brush_*`. Los minimos van en **un array** `SizeMins[9]` en el CDO — una sola
escritura en vez de 18 nodos, y editable en el panel:
`[0.05, 0.05, 0.05, 0.75, 0.2, 0.1, 0.02, 0.2, 0.1]` (= `m_BrushSizeRange.x * 2`; Light lleva el
mismo x7,5 que su maximo, por lo del bloom).

**El input, sin crear assets:** `IMC_Default` **no mapea** el eje X del stick derecho (solo
`Left_Thumbstick_X` y `Right_Thumbstick_Y`), asi que no habia accion que leer. En vez de fabricar
un `IA`+`IMC` se lee la tecla cruda:
```
Rig.Tick -> Tool.AdjustSize( GetInputAnalogKeyState(PC, "OculusTouch_Right_Thumbstick_X"), DeltaSeconds )
```
`AdjustSize` tiene zona muerta 0,15 y `SizeRate` 0,6 (unidades 0-1 por segundo), y clampea.
`Size01` vive en la herramienta y **`BeginStroke` lo copia al trazo** junto al color — o sea que
mover el stick a mitad de un trazo no lo altera.

⚠ **`Size01` arranca en 1.0 a proposito**: hoy los pinceles estaban dibujando en el MAXIMO de TB,
asi que el default preserva exactamente lo aprobado y el stick solo achica. Para agrandar mas hay
que subir el `BrushSize` del preset (que es el maximo) — no es una limitacion nuestra, es el rango
de TB.

### 3. La barra de grosor y la rueda corrida
`M_TB_Slider` (unlit, `Fill` escalar) pinta una barra; `BuildSlider` la crea como una seccion mas
del mismo mesh y guarda su MID en `SliderMid`; `UpdateSlider` (en `PickSlot`, cada tick) le pasa
`Tool.Size01`. Perillas: `SliderOffset` (0,0,-4.6), `SliderHalfW` 3.0, `SliderHalfH` 0.35.

🔑 **El espejado de la paleta ataca otra vez**: la U local crece hacia +Y, que se ve a la
IZQUIERDA. Sin corregir, la barra creceria de derecha a izquierda. Va un `OneMinus` sobre la U
**en el material de la barra** (no en el compartido), asi crece de izquierda a derecha como el
stick. Mismo tipo de error que el `-d.z` de la rueda: **cuando una superficie se ve espejada, todo
mapeo pantalla-a-dato hay que revisarlo de a uno.**

Rueda de color: `WheelOffset.y` −5.6 → **−7.4** (mas a la derecha para el que mira).

⬜ Sin visor. 🔴 Recolocar el rig antes de probar.

## 2026-09-26 (3i) - El rig se CONFIGURA SOLO, y el slider con marcador

### La esfera no se veia: gotcha 396 medida otra vez, y la salida definitiva

La instancia colocada tenia `SM_Tip` con `staticMesh: None`, transform en cero y sin material.
Se intento parchear la instancia y **volvio a pasar exactamente lo de la 396**: la escritura
devolvio `true` y **solo entro `staticMesh`** — location, scale y `overrideMaterials` se
rechazaron en silencio. Se revirtio para no dejar una esfera de 1 m en el viewport.

✅ **La salida no es recolocar el actor: es que el rig se configure a si mismo.** `InstallTip`
(reemplaza a `MountTip`) hace en runtime TODO lo que la instancia no hereda:
```
SetStaticMesh(SM_Tip, /Engine/BasicShapes/Sphere)
SetMaterial(SM_Tip, 0, MI_TB_Tip)
SetRelativeScale3D(SM_Tip, TipScale)          ; variable nueva, 0.012
IsValid(RightAim) -> Attach(SM_Tip, RightAim) ; KeepRelative
                     SetRelativeLocation(SM_Tip, TipOffset)   ; variable nueva, (2.5,0,0)
                     SetVisibility(SM_Tip, true)
```
🔑 **Regla general para este rig, y para la migracion a Soul Charger: un actor autoinstalable no
puede depender del estado de su instancia.** Todo lo que un componente necesite (malla, material,
escala, offset) se escribe en `BeginPlay` desde VARIABLES del BP — que si viajan bien — en vez de
dejarlo en el template del componente, que NO llega a las instancias ya puestas.
⚠ Efecto colateral bueno: `TipOffset`/`TipScale` quedan como perillas en el panel **y funcionan
en la instancia**, cosa que el transform del componente no hacia.

🔴 **Renombrar una funcion cuesta un paso extra:** `remove_function_graph("MountTip")` +
`add_function_graph("MountTip")` devuelve **`MountTip_0`** (el nombre sigue reservado), y mientras
exista un nodo de llamada a la funcion borrada **el BP no compila** y `write_graph_dsl` falla con
*"Could not find a function named X"*. Orden correcto: **borrar el nodo de llamada primero**,
despues la funcion, y usar un nombre nuevo.

### El slider: de barra llena a barra con MARCADOR

Beltran: *"que sea un slider visible que nos muestre donde estamos en la linea de grosor"*.
`M_TB_Slider` pasa de `lleno/vacio` a tres zonas, con `v = 1 - U`:
```
relleno = (v <= Fill) ? 0.45 : 0.12          ; pista oscura + parte llena
marca   = (|v - Fill| < 0.05) ? 1.0 : 0.0    ; el POMO, donde estas parado
salida  = max(relleno, marca)
```

### Y el slider se toca, igual que la rueda
Para no depender de que el stick funcione (el eje se lee crudo con `GetInputAnalogKeyState`, sin
accion de input que lo respalde), `TestSlider` lo hace arrastrable con la punta:
```
Size01 = clamp( (HalfW - dy) / (2*HalfW) )    ; dy = Y local respecto de SliderOffset
```
🔑 El `(HalfW - dy)` y no `(dy + HalfW)` **por el espejado**: local +Y se ve a la izquierda, asi
que la barra crece de la izquierda del usuario hacia la derecha, y el stick a la derecha tambien
agranda. Los dos caminos escriben el mismo `Size01`, asi que conviven.
Cadena final del tick de la paleta:
`FacePlayer -> TestSlot xN -> ApplyHighlight -> PushSelection -> TestWheel -> TestSlider -> UpdateSlider`

⬜ Sin visor.

## 2026-09-27 - UNDO, muestra de color, y la esfera que toma el pincel

### El rango del slider, remapeado
`SizeLo` = **0.25** y `SizeHi` = **1.5** (variables nuevas en `BP_TBStroke`, panel). El slider
remapea ANTES de entrar en la curva de TB:
```
t' = lerp(SizeLo, SizeHi, clamp(Size01))          ; 0 -> 0.25,  1 -> 1.5
BrushSize = ( lerp( sqrt(min), sqrt(max), t' ) )^2
```
🔑 `Math|Float|Lerp` **no clampea el alfa**, asi que `t' = 1.5` EXTRAPOLA por encima del maximo
del pincel — que es lo que faltaba para poder agrandar. El piso deja de ser el pelo invisible.

### Boton de UNDO, disparado por FLANCO
Tool: `UndoLast()` (no hace nada si `bDrawing`, para no matar el trazo en curso) →
`UndoPop(I)` (saca del `StrokeHistory` y `DestroyActor`).
Paleta: seccion `n+2` con `M_TB_Undo` (glifo de flecha curva por `Custom` sobre la UV).
```
(fn TestUndo ()  ... _in = punta dentro del cuadro ...
  (if (and _in (not bUndoWasIn)) (FireUndo)  (else (SetUndoWasIn _in))))
```
🔴 **El flanco NO es opcional**: la rueda y el slider escriben mientras el dedo este dentro, y
copiar ese patron aca **borraria un trazo por cuadro**. `FireUndo` pone `bUndoWasIn = true` y
llama a `UndoLast`.

### Muestra de color (el feedback que faltaba)
Seccion `n+3` con `M_TB_Swatch` (un `VectorParameter "Col"` al emisivo) y su MID en `SwatchMid`.
`UpdateSlider` ahora, dentro del mismo `IsValid`, setea `Fill` **y** `Col = Tool.BrushColor`.

### La esfera de punta: mitad de tamano y con el color del pincel
`TipScale` 0.012 → **0.006**. Y `UpdateTipColor` (Tick del rig) hace
`SetVectorParameterValueonMaterials(SM_Tip, "Tint", Tool.BrushColor)` — **ese nodo crea el MID
internamente**, asi que no hace falta variable ni tocar `InstallTip`.
⚠ Sirve porque `SM_Tip` tiene UNA sola ranura; sobre la paleta (8 secciones en un componente)
habria tenido que ser un MID por seccion.

### 🔴 Dos trampas del DSL pagadas aca
1. **`CreateDynamicMaterialInstance` resuelve a DOS sobrecargas distintas segun el grafo.** En
   `BuildSlider` cayo en la de Kismet (`Parent`) y quedo bien; en `BuildExtras` cayo en la de
   **PrimitiveComponent** (`self`/`ElementIndex`/`SourceMaterial`) y el path del material **no
   aterrizo en ningun pin** → *"This blueprint (self) is not a PrimitiveComponent"*. El mensaje
   no nombra el nodo: hay que ir nodo por nodo mirando los pines.
2. **`Rendering|Material|SetVectorParameterValue` esta DUPLICADO** (coleccion de parametros vs
   MID) y el parser tomo el de coleccion → *"Could not connect pin SwatchMid to Collection"*. Se
   resuelve con **`create_node` + `declaring_class`** (`/Script/Engine.MaterialInstanceDynamic`);
   por DSL no hay forma de desambiguar. `find_node_types` lo delata: el mismo nombre dos veces.

⬜ Sin visor.

## 2026-09-27 (2a) - "El undo no funciona": diagnosticado SIN visor, con PIE

Toda la cadena (`TestUndo` -> `FireUndo` -> `UndoLast` -> `UndoPop`) estaba logicamente bien al
leerla. En vez de seguir infiriendo, **se arranco PIE** (los MotionController existen como
componentes sin casco, asi que el rig se instala igual) y se leyo el estado REAL de la paleta
spawneada:

| variable | valor en PIE | que prueba |
|---|---|---|
| `SwatchMid` | MID valido | **`BuildExtras` SI corre** → el boton existe |
| `SliderMid` | MID valido | el slider tambien |
| `Tool` | `BP_TBDrawRig_C_1.TBTool` | la herramienta esta enganchada |
| `Tip` | `BP_TBDrawRig_C_1.SM_Tip` | el puntero es la esfera nueva |
| `bUndoWasIn` | false | el flanco arranca limpio |

🔑 **Con eso, lo unico que quedaba era la DETECCION.** Y comparando las zonas de acierto de la
paleta salta a la vista:

| elemento | zona |
|---|---|
| ranura de pincel | **radio 3 cm (3D)** |
| rueda | radio 2,4 |
| barra | 3,0 x 1,35 |
| **undo (antes)** | **caja de ±1,2** ← el doble de exigente que todo lo demas |

**Arreglo**: la deteccion pasa a distancia 3D como las ranuras —
`inside = Distance(tipLocal, UndoOffset) < UndoPick`, con `UndoPick` = **2.0** (variable nueva).
El boton se movio a `z = 5.6` y crecio a `UndoHalf = 1.4`: con radio 2,0 la esfera de acierto
llega hasta z=3,6 y el borde de la rueda esta en 2,4 → **1,2 cm de separacion**, suficiente para
no disparar undo al tocar la rueda. Esa separacion es la que fija el techo de `UndoPick`.

⚠ **Sondas temporales puestas**: `TestUndo` imprime `inside` cada tick (key **`BTN`**) y
`FireUndo` imprime **`UNDO FIRE`**. Sacarlas cuando se valide.

🔑 **La leccion de metodo:** cuando todo el codigo se lee bien, el siguiente paso NO es releerlo —
es **medir el estado en PIE**. Aca costo 4 llamadas y descarto de una toda la mitad "el boton no
existe / no esta cableado", que era donde yo iba a seguir buscando.

## 2026-09-27 (3a) - El undo disparaba y no borraba: un nodo PURO leyendo estado ya mutado

`BTN` daba true, `UNDO FIRE` salia, la llamada a `UndoLast` estaba bien cableada (verificado por
pines) — y el trazo seguia ahi. El bug estaba en `UndoPop`:

```
(bind _s (Utilities|Array|Get(acopy) _historial I))   ; nodo PURO
(Utilities|Array|RemoveIndex _historial I)            ; <- corre PRIMERO
(Utilities|IsValid _s (:"Is Valid" (Actor|DestroyActor _s)))
```

🔴 **El `Array Get` no corre donde esta escrito.** Se inlinea justo antes del nodo impuro que lo
consume — o sea **despues** del `RemoveIndex`. Ahi el indice ya no existe, devuelve `None`,
`IsValid` falla y no se destruye nada. **El `bind` del DSL no es una asignacion: es un nombre para
la salida de un pin.**

✅ Arreglado invirtiendo el orden: `IsValid -> DestroyActor -> RemoveIndex`. Ver gotcha 409.

### El camino hasta encontrarlo (util como receta)
1. Leer las 4 funciones: todas correctas → no seguir releyendo.
2. **PIE + estado del actor spawneado**: `SwatchMid`/`SliderMid` validos, `Tool`/`Tip` apuntando
   bien, y `overrideMaterials` del ProcMesh con **8 entradas** → toda la UI existe y esta
   materializada. Descartada la mitad "no existe / no esta cableado".
3. **PIE + forzar la condicion** (`UndoPick = 500`): `UNDO FIRE` una sola vez → el flanco latea y
   la llamada se hace. Descartada la logica de deteccion.
4. Reubicado el boton (estaba fuera del campo visual) → Beltran confirma `UNDO FIRE`.
5. Con "se llama" y "esta bien cableado" en verde, el unico hueco que queda es **el orden de
   evaluacion**. Ahi aparecio.

### Sondas
Sacadas las que imprimian cada cuadro (`BTN` en `TestUndo`, `PRESION` en el Tick de la
herramienta). ⚠ **Quedan puestas** `UNDO FIRE` (en `FireUndo`) y `UL_N`/`UL_D` (en `UndoLast`),
que solo imprimen al tocar el boton. Sacarlas cuando se valide.


## 2026-09-27 (4a) - REDO, y el piso del slider mas abajo

Beltran, despues de validar el undo en visor: *"Funciona. Agrega un boton de Re Do. El valor
minimo del slider que sea .25 del actual"*.

### Contra Tilt Brush primero: el undo de TB NO destruye, ESCONDE

`SketchMemoryScript` tiene **dos pilas** (`m_OperationStack` / `m_RedoStack`) y comandos con
`Undo()`/`Redo()`:
```csharp
public void StepBack()    { var c = m_OperationStack.Pop(); c.Undo(); m_RedoStack.Push(c); }
public void StepForward() { var c = m_RedoStack.Pop();      c.Redo(); m_OperationStack.Push(c); }
```
Y el trazo se apaga con `Stroke.Uncreate()` / se rehace con `Recreate()` — hay incluso un TODO en
su fuente pidiendo que el *rewind* use "el mecanismo de ocultar de las operaciones de undo".
🔑 **O sea que nuestro undo estaba mal de raiz para soportar redo: destruia el actor.** Sin el
actor no hay nada que rehacer. El cambio de fondo de esta pasada es ese.

Tercer detalle que se copio de TB: **`MemorizeBrushStroke` arranca con `ClearRedo()`**, y
`ClearRedo` hace `Dispose()` de cada comando antes de vaciar la pila. Un trazo nuevo invalida el
futuro **y libera la geometria**.

### Lo que cambio en `BPC_TBTool_NC`

Variable nueva: **`RedoStack`** (array de `BP_TBStroke`, igual que `StrokeHistory`).

| funcion | que hace |
|---|---|
| `UndoPop(I)` | **ya no destruye**: llama a `StashStroke` y saca del historial |
| `StashStroke(S)` | `SetActorHiddenInGame(S, true)` + `Add(RedoStack, S)` |
| `RedoLast()` | espejo exacto de `UndoLast`: si no esta dibujando y hay pila, `RedoPop(n-1)` |
| `RedoPop(I)` | `SetActorHiddenInGame(false)` + `Add(StrokeHistory)` + `RemoveIndex(RedoStack)` |
| `ClearRedo()` | destruye cada actor escondido y vacia la pila; **primera linea de `BeginStroke`** |

🔴 **`RedoPop` respeta el orden que costo la gotcha 409**: todos los usos de `_output` (el `Array
Get` puro) van ANTES del `RemoveIndex`. Si el `Add` quedara despues del remove, leeria `None` y el
trazo se perderia en silencio — el mismo bug, del otro lado.

`UndoPop` se cambio por **cirugia de un nodo**: se creo `CallFunction|StashStroke`, se le paso la
salida del `Array Get` y se borro el `DestroyActor`. La logica de "sacar del historial" no se
toco.

### Lo que cambio en `BP_TBPalette`

Variables nuevas (panel): `RedoOffset` **(0, 6.5, -4.6)**, `RedoHalf` 1.6, `RedoPick` 2.2,
`bRedoWasIn`. Seccion **`n+4`** del mismo ProceduralMesh (la novena) con `M_TB_Redo`.
Funciones `BuildRedo` / `TestRedo` / `FireRedo`, calcadas de las de undo — **flanco incluido**, que
en un boton no es opcional.

Mapa final de la paleta en local (recordar el **Yaw 180**: +Y se ve a la IZQUIERDA):

| elemento | Y | Z | seccion |
|---|---|---|---|
| rueda de color | −7.4 | 0 | n |
| muestra de color | −7.4 | −4.2 | n+3 |
| 4 pinceles | ±1.7 | ±1.7 | 0..n−1 |
| barra de grosor | 0 | −4.6 | n+1 |
| **undo** | +6.5 | 0 | n+2 |
| **redo** | **+6.5** | **−4.6** | **n+4** |

Queda simetrico: rueda+muestra a la derecha del usuario, undo+redo a la izquierda. Separacion
undo↔redo = 4.6 cm contra 2.2+2.2 de radio de acierto → **0.2 cm de aire**, y el borde de la
barra (Y=3) queda a 1.1 del radio del redo. Esos dos numeros son los que fijan el techo de
`RedoPick`.

`M_TB_Redo` es un **duplicado** de `M_TB_Undo` con UNA linea mas en el `Custom`: `p.x = -p.x`.
Espeja el glifo, asi que las dos flechas se leen opuestas **sin importar como se vea el espejado
de la paleta** — que era el riesgo de dibujar un glifo nuevo a mano.

### El piso del slider - PRIMER INTENTO, MAL LEIDO (ver 4b)

`SizeLo` **0.25 -> 0.0625**. Lei *"el valor minimo del slider que sea .25 del actual"* como un
cuarto del VALOR (0.25 -> 0.0625) y era al revés de lo que queria: **queria SUBIR el minimo para
que no fuera tan delgado**. Quedo en 0.0625 y en visor salio un pelo. Corregido en 4b.

⚠ Lo que si queda aprendido de aca: **la curva es al cuadrado, asi que un cuarto del valor no es
un cuarto del grosor** — `size = ( lerp(sqrt(min), sqrt(max), t) )^2`. Y el piso de cada pincel
es su minimo real de TB (`SizeMins`), asi que por abajo hay un tope que no se puede pasar.

### Sondas: SACADAS todas
`UNDO FIRE` (de `FireUndo`) y `UL_N`/`UL_D` (de `UndoLast`). El grafo de `UndoLast` quedo
`entry → Branch` directo, sin los dos `PrintString` ni sus `ToString`.

### Verificado en PIE (no en visor)
`overrideMaterials` del ProcMesh de la paleta spawneada: **9 entradas**, la 8 = `M_TB_Redo` →
`BuildRedo` corre y la seccion existe materializada. `Tool` y `Tip` enganchados al rig,
`bRedoWasIn` en false. ⬜ Falta el visor: que el boton dispare y que el trazo reaparezca.


## 2026-09-27 (4b) - El piso del slider al revés, y la paleta sin nada seleccionado

Dos correcciones de la misma pasada de visor. 🟢 **El undo funciona** (confirmado por Beltran).

### 1. `SizeLo` 0.0625 -> 0.5: yo lo habia bajado y el lo queria SUBIR

*"Lo del slider me equivoque, quedo demasiado delgado. El minimo yo queria subirlo para que no
fuera tan delgado."* La pedida original (*"el valor minimo del slider que sea .25 del actual"*)
admitia las dos lecturas y tome la que iba en la direccion contraria.

Numeros reales, ahora con los maximos **leidos de la tabla de presets** (la vez pasada asumi
max ~1.0 para el pincel 0 y el valor real es **2.0** — el error hizo que el efecto pareciera mas
suave de lo que fue):

| pincel (slot) | min / max | t=0.0625 | t=0.25 | **t=0.5** | t=1.5 (tope) |
|---|---|---|---|---|---|
| 0 TaperedMarkerFlat | 0.05 / 2.0 | 0.089 | 0.272 | **0.671** | 4.04 |
| 5 OilPaint | 0.1 / 3.0 | 0.149 | 0.420 | **0.938** | 5.66 |
| 3 Light | 0.75 / 3.0 | 0.847 | 1.172 | **1.688** | 4.92 |
| 6 WetPaint | 0.02 / 2.5 | 0.054 | 0.251 | **0.742** | 4.76 |

`SizeLo` = **0.5** deja el extremo fino en ~2,5x el que tenia ANTES de todo esto, y el rango
completo del slider queda en ~6x de ancho. La perilla sigue siendo `SizeLo` en `BP_TBStroke`.
🔑 Light casi no se mueve porque su piso (0.75) esta muy arriba: **el mismo `SizeLo` da rangos
muy distintos segun el pincel**, y eso es de TB, no nuestro.

### 2. La paleta arrancaba sin nada seleccionado (y dibujando con otra cosa)

*"La paleta deberia mostrarnos el pincel seleccionado cuando parte la obra... igual dibuja al
principio, solo que no se con cual pincel."*

Diagnostico por defaults, sin visor:

| variable | default | consecuencia |
|---|---|---|
| `BP_TBPalette.Selected` | **-1** | `ApplyHighlight` pone 0.3 en TODAS (highlight = `Selected == i`) |
| | | `PushSelection` esta guardado con `if (>= Selected 0)` → no manda nada |
| `BPC_TBTool_NC.BrushIndex` | **-1** | y -1 es la **rama Default** del switch de `ApplyPreset`: el "look aprobado", que NO es ninguno de los 9 |

O sea que los dos sintomas que describio son **el mismo hecho**: nadie habia elegido todavia.
Dibujaba con el look viejo de la rama default.

✅ **Arreglo sin un solo nodo nuevo**: `Selected` default **0** y `BrushIndex` default **0**.
`ApplyHighlight` ilumina el slot 0 en el primer cuadro y `PushSelection` empuja `BrushIds[0]`;
el `BrushIndex` en 0 cubre el intervalo antes del primer tick, asi que no hay ni un cuadro con el
preset -1.
🔑 **`TestSlot` nunca escribe `Selected` cuando no hay nada cerca** (el `if` solo tiene rama
verdadera), asi que un default distinto de -1 **sobrevive** — eso es lo que hace que alcance con
el default. Verificado leyendo la funcion antes de tocar nada.
⚠ Por el espejado, el slot 0 se ve **arriba a la DERECHA** del usuario, no a la izquierda. Es
`BrushIds[0]` = TaperedMarkerFlat. Para arrancar con otro, cambiar el default de `Selected`.


## 2026-09-27 (4c) - EL VAIVEN PORTADO DEL PINCEL VIEJO

Pedido: *"traer el sistema de animacion que teniamos en nuestro pincel antiguo. Que hace que los
trazos se muevan manteniendo fijo su punto de partida."*

### Lo que habia, leido de su tracker (`BPC_DrawTool_NC.md`)
```
mask  = saturate(UV.Y / SwaySpan)                    ; base quieta, punta suelta
phase = dot(WorldPos.xy, (1, 0.7)) * SwayScale + Time * SwaySpeed
sway  = SwayDir * sin(phase) * SwayStrength * mask * SwayOn
WPO   = taper + sway
```
Valores **aprobados en visor** el 2026-09-24: `SwaySpan` 40 · `SwayStrength` 1.5 · `SwaySpeed` 0.5
· `SwayScale` 0.03 · `SwayDir` (1, 0.6, 0.15) · `SwayFade` 1.2 s. Se portaron **tal cual**.
🔑 El termino espacial (`dot(WorldPos.xy, …)`) es lo que da el aire de ruido con **un solo seno**:
cada trazo y cada zona entra con fase distinta. Sin el, todo se mueve al unisono.
🔴 Y el encendido **va con rampa**: en el pincel viejo poner `SwayOn = 1` de golpe hizo que
Beltran viera *"se glitchea y se reposiciona"* al soltar — el WPO salta de 0 a pleno en un cuadro.

### Lo que hubo que cambiar, y por que

**1. La mascara ya no puede salir de la UV.** En la cinta vieja `UV.Y = TotalDistance` (cm desde
el nacimiento). Acá la UV es la de Tilt Brush: `V_UV = (K_U[i], AtlasV)`, y **`K_U` cambia de
significado con `UVStyle`** — `NormalizeU` hace `StretchAccum` (acumula `K_Len`, o sea cm) cuando
`UVStyle == 1` y `StretchNorm` (0..1) cuando no. O sea que la misma cuenta daria distinto por
pincel.
✅ **Salida elegida: distancia de MUNDO al punto de nacimiento**, con el origen pasado como
parametro:
```
mask = saturate( distance(AbsoluteWorldPosition, SwayOrigin) / SwaySpan )
```
Y `SwayOrigin = K_Pos[0]`, que es el primer nudo (`StartStroke` mete dos `AddKnot` en la misma
posicion). Funciona porque el actor del trazo se spawnea en el origen: **sus vertices ya estan en
coordenadas de mundo**, asi que `K_Pos` y `AbsoluteWorldPosition` son la misma cosa.
⚠ **Desviacion consciente:** no es longitud de arco. En un trazo que se enrosca y vuelve cerca de
su nacimiento, esa vuelta queda mas rigida de lo que correspondia. Para hacerlo por arco hay que
meter la distancia acumulada en **UV1** — el pin ya existe en el `CreateMeshSection` de
`RebuildChunk` (hoy recibe 0) — y llenarlo en `EmitPass` **y** en `EmitTubeHard`. Se descarto
por ahora: toca las dos funciones mas delicadas del motor, recien validadas.

**2. No hay MID por trazo** (decision de diseño: el color va en los vertices). Y el vaivén
necesita dos datos por trazo: `SwayOrigin` y `SwayOn`.
✅ **Salida: `SetVectorParameterValueOnMaterials` / `SetScalarParameterValueOnMaterials` sobre el
componente.** Esos nodos **crean el MID adentro** (el mismo truco de `UpdateTipColor`), asi que no
hay que crear ni guardar nada — y de paso cubren **todas** las secciones si el trozeado volviera.
🔴 Ojo con lo que NO se hizo: `CreateDynamicMaterialInstance` tiene dos sobrecargas y ya costo un
bug (gotcha 406). Este camino lo esquiva por completo.

**3. El WPO estaba LIBRE** (`get_property_input(M_TB_Solid, MP_WorldPositionOffset)` = `None`),
al contrario que en la cinta vieja, donde el taper de las puntas ya lo ocupaba y el vaivén tuvo
que sumarse. Acá el taper es **geometria de verdad**, asi que el WPO es solo vaivén.

### Como quedo

**`MF_TB_Sway`** (función de material nueva, 23 expresiones) con los 7 parametros. Enchufada al
`MP_WorldPositionOffset` de los **cuatro maestros**: `M_TB_Solid`, `M_TB_Additive`,
`M_TB_Masked`, `M_TB_Paint`. Una sola copia de la cuenta en vez de cuatro.
🔴 **`SwayOn` nace en 0 = NEUTRO**, asi que los cuatro maestros siguen dando exactamente lo
aprobado hasta que el codigo enciende el vaivén. Es la regla de gotcha 375 aplicada a proposito.

En `BP_TBStroke`, variables nuevas `SwayFade` (1.2, panel, categoria **05 VAIVEN**), `SwayT`,
`bSwayRamp`, y dos funciones:
```
EndStroke:  RebuildChunk -> SwayArm
SwayArm:    SetVectorParameterValueOnMaterials(Mesh, "SwayOrigin", K_Pos[0])
            SetScalarParameterValueOnMaterials(Mesh, "SwayOn", 0)
            SwayT = 0 ; bSwayRamp = true
EventTick:  SwayStep(DeltaSeconds)
SwayStep:   if bSwayRamp:
              SwayT = min(SwayT + DT/SwayFade, 1)
              SetScalarParameterValueOnMaterials(Mesh, "SwayOn", SwayT)
              bSwayRamp = (SwayT < 1)
```
🔑 **`bSwayRamp = (SwayT < 1)` en vez de un `if` anidado**: la rampa se apaga sola, la funcion
queda plana y no hay segunda rama que revisar.
🔑 Y el `Get` de `SwayT` **despues** del `Set` lee el valor nuevo — es el mismo mecanismo de la
gotcha 409, pero acá jugando a favor: un nodo puro se re-evalua en cada uso.
⚠ El `EventTick` de `BP_TBStroke` estaba **vacio** (implementado, sin nodos), asi que no hubo que
pelear con nada existente.

### Para afinarlo
Los parametros viven en `MF_TB_Sway` y se exponen en los cuatro maestros. Para tocar **un pincel**
sin recompilar: override en su `MI_TB_*`. Para cambiar el default de todos: editar `MF_TB_Sway` y
`MaterialTools.recompile` (la funcion **y** los maestros).
💡 `BP_DrawDirector_NC` ya tiene las perillas `SwaySpan/Strength/Speed/Scale/Dir/Fade` del pincel
viejo — cuando se conecte el director a este pincel, salen de ahi.

⬜ **Sin visor.** Lo verificado: los 4 maestros compilan y exponen los 7 parametros
(`list_parameters`), el WPO de cada uno recibe la salida `Sway` de la funcion, y `BP_TBStroke`
compila con la cadena entera. Lo que falta mirar: que al soltar el trazo entre suave (la rampa),
que la base quede realmente clavada, y si 1.5 cm de amplitud sigue siendo el valor que le gusto.


## 2026-09-27 (4d) - EL VAIVEN EN VISOR: rigido y todos iguales. Las dos causas

Beltran: *"Siento que la animacion no se nota, porque todos los trazos estan adoptando la misma
oscilacion y velocidad. Debieran poder diferenciarse. Ahora senti que los trazos se movian
completos, no como un wobble suave en cada trazo."*

Las dos cosas estaban en la cuenta, y las dos se leen directo de ella.

### 1. "Se movian completos" — la fase casi no cambiaba A LO LARGO del trazo
El unico termino espacial era `dot(WorldPos.xy, (1, 0.7)) * SwayScale` con `SwayScale = 0.03`.
Eso da **0,03 rad por cm**: sobre un trazo de 20 cm la fase cambia ~0,7 rad, o sea que es
practicamente **constante**. Todos los vertices van al mismo lado en el mismo instante y la
mascara solo escala la amplitud → **traslacion rigida**, no onda. Y peor: el termino usa solo XY,
asi que **un trazo vertical no tiene ninguna variacion de fase a lo largo**.
🔑 El dato correcto ya estaba calculado: la **distancia al nacimiento** (el numerador de la
mascara). Sumandola a la fase sale una onda que **viaja** por el trazo:
```
d     = distance(WorldPos, SwayOrigin)
phase = d * SwayWave + dot(WorldPos.xy,(1,0.7)) * SwayScale + Time * speed
```
`SwayWave` = **0.18** rad/cm → longitud de onda `2π/0.18` = **35 cm**, una ondulacion completa por
cada 35 cm de trazo. Es la perilla del "cuanto se ondula"; mas alto = onda mas corta.
⚠ Que no se rompe: los nudos caen cada ~0,2 cm (`GetSpawnInterval`), asi que 35 cm de longitud de
onda se muestrean con ~175 nudos. No hay riesgo de quedar facetado.

### 2. "Todos la misma oscilacion y velocidad" — porque literalmente lo eran
`Time * SwaySpeed` es **global**: identico para todos los trazos. Y la unica diferencia entre
trazos era su posicion de mundo en ese `dot`, que para dos trazos cercanos da casi lo mismo.
✅ **Semilla por trazo.** `SwaySeed` (0..1) se escribe en `SwayArm` con un `RandomFloat`, y modula
la velocidad:
```
speed = SwaySpeed * (1 + (SwaySeed - 0.5) * SwaySpeedVar)
```
Con `SwaySpeedVar` = **0.6** las velocidades caen en `[0.35, 0.65]` (periodos de 10 a 18 s).
🔑 **No hace falta sumar tambien un desfase por semilla**: como `Time` es grande (cientos de
segundos), velocidades distintas ya dejan las fases completamente descorrelacionadas. Se evaluo y
se descarto — dos expresiones menos en un shader de Quest.

### El estado de la cuenta
```
d      = distance(AbsoluteWorldPosition, SwayOrigin)       ; SwayOrigin = K_Pos[0]
mask   = saturate(d / SwaySpan)                            ; 40 cm
speed  = SwaySpeed * (1 + (SwaySeed - 0.5) * SwaySpeedVar) ; 0.5, semilla, 0.6
phase  = d * SwayWave + dot(WorldPos.xy,(1,0.7)) * SwayScale + Time * speed
sway   = SwayDir * sin(phase) * SwayStrength * mask * SwayOn
```
10 parametros en `MF_TB_Sway`, expuestos en los 4 maestros. `SwayOn` y `SwaySeed` los pone el
codigo; los otros 8 son perillas.

### Las perillas, y que mueve cada una
| perilla | hoy | que cambia |
|---|---|---|
| `SwayWave` | 0.18 | **cuanto ondula**. Longitud de onda = 2π/valor (0.18 → 35 cm) |
| `SwaySpeedVar` | 0.6 | **cuanto se diferencian** entre si. 0 = todos iguales otra vez |
| `SwayStrength` | 1.5 | amplitud en cm |
| `SwaySpeed` | 0.5 | velocidad media (periodo medio 12,6 s) |
| `SwaySpan` | 40 | en cuantos cm pasa de rigido a suelto desde la base |
| `SwayScale` | 0.03 | diferencia de fase **entre trazos alejados** (ya no es la del wobble) |
| `SwayDir` | (1,0.6,0.15) | eje del vaivén |
| `SwayFade` | 1.2 s | la rampa de encendido (esta en `BP_TBStroke`) |

⚠ Lo que sigue igual para todos es la **direccion**: todos se inclinan sobre el mismo eje. Si con
esto todavia se ven emparentados, el siguiente paso es **rotar `SwayDir` por la semilla** en el
plano XY (~9 expresiones mas). Se dejo afuera a proposito por presupuesto de Quest.

🟢 **VALIDADO EN VISOR** (2026-09-27): *"se ve bastante bien, estamos con eso por ahora"*.
Los 8 valores quedan como estan. La direccion compartida no hizo falta diferenciarla.


## 2026-09-27 (5a) - EL DIRECTOR: el rig pasa a ser el sistema entero

Pedido de Beltran, en tres mensajes que se fueron precisando: *"quiero que lo armemos con un
director desde donde podamos controlar varios parametros"* entonces *"que el sistema sea migrable a
cualquier otro proyecto donde yo simplemente lo arrastro al world y reconoce al pawn con el que
estoy trabajando"* entonces *"este director debiera contener tanto los motion controllers como los
pinceles, los sonidos, todo"*.

### La decision de arquitectura: NO es un actor nuevo

`BP_TBDrawRig` **ya era** eso: autoinstalable, validado en visor, con el input, la paleta, las
mallas de mando, la punta y la herramienta adentro. Crear un director aparte habria dado **dos**
cosas que arrastrar, justo lo contrario de lo que pidio. Asi que el rig **se renombro a
`BP_TBDirector_NC`** y se le colgaron las perillas.
- `get_referencers` antes de renombrar: **solo `L_TBTest`**. Renombre seguro.
- Verificado despues: la instancia colocada sigue resolviendo sus valores (`TipOffset`,
  `TipScale`) y el BP compila.

### Y la portabilidad ya estaba resuelta, mejor de lo que yo creia
```
(fn FindControllers ()
  (for _c (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "MotionControllerComponent")
    (SortController self _c)))
```
**El director no trae motion controllers: usa los del pawn poseido**, sin clase hardcodeada. Eso
es exactamente *"reconoce al pawn con el que estoy trabajando"*, y de paso esquiva la gotcha del
sistema viejo (un MotionController en un actor sin Owner no trackea jamas). Si el pawn no tiene
ninguno, `bReady` queda en false y `CheckController` lo reintenta cada cuadro: degrada, no explota.

### Las 28 perillas, por categoria
`01 COLOR`: `ColorMode` (0=rueda, 1=4 colores), `SlotColorA[4]`, `SlotColorB[4]`,
`bColorGradient`, `BrushIds`
`02 ANIMACION`: `bSwayEnabled`, `SwayStrength`, `SwayWave`, `SwaySpeed`, `SwaySpan`,
`SwaySpeedVar`, `SwayScale`, `SwayDir`, `SwayFade`
`03 SKETCH`: `HideTime`, `ShowTime`, `SketchGap`, `bCenterZ`
`04 AUDIO`: `BrushLoop[]`, `BrushLoopVol[]`, `LoopFade`, `ClickSound`, `ClickVol`,
`HideSound`, `ShowSound`, `SfxVol`
`05 HAPTICA`: `DrawHapAmp`, `DrawHapFreq`, `ClickHapAmp`, `ClickHapDur`
Todas **instance-editable**, para tocarlas en el actor colocado sin abrir el BP.

### El hallazgo que definio como viajan los datos
**Las variables del director NO son visibles como nodos desde otros Blueprints.**
`find_node_types` con filtro `GetSwaySpeedVar` devuelve `[]` desde un grafo de `BP_TBStroke`,
mientras que las del director VIEJO (`Class|BPDrawDirectorNC|GetSwayStrength`) si aparecen. O sea
que es **cache del node database para una clase recien renombrada**, no una regla del motor, pero
en esta sesion es un hecho con el que hay que convivir.
**Conclusion: el director EMPUJA, nadie lo lee.** Los `Class|BPCTBToolNC|Set*` y
`Class|BPTBStroke|Set*` si estan registrados, asi que la direccion contraria funciona perfecto.

Cadena final de la configuracion:
```
Director.DoInstall -> PushConfig()          ; 9 Set* sobre el componente TBTool
Tool.Release       -> CloseStroke(S)        ; reemplaza la llamada directa a EndStroke
                        -> S.SwayConfig(9 valores)   ; los escribe en el MID del trazo
                        -> S.EndStroke()             ; arranca la rampa, ya con SwayFade nuevo
```
**`bSwayEnabled` no necesito una rama**: `SwayConfig` escribe `select(Enabled, Strength, 0)` en
`SwayStrength`. Apagar la animacion es amplitud 0, y el resto del shader queda igual. Cero
estructura nueva.

### Verificado con CONTROL NEGATIVO (no solo "los valores coinciden")
Primera lectura en PIE: el `TBTool` spawneado tenia `CfgWave = 0.18`, que es **tambien** el default
del componente, asi que no probaba nada. Se puso el default del componente en **99**, se relanzo
PIE y la lectura dio **0.18**: el `PushConfig` del director realmente corre y pisa el default.
Despues se restauro el 0.18.

### Lo que NO se hizo con Material Parameter Collection, y por que
Un MPC era el camino natural para los valores globales y se llego a construir. Se descarto al
descubrir que **`MaterialExpressionCollectionParameter` resuelve por `ParameterId`, y el MCP no
puede leer ni escribir ese campo** (`get_properties` lo rechaza explicitamente). Compilar no tiro
error, pero **un 0 silencioso tampoco lo tiraria**, y el vaiven ya estaba aprobado en visor: no se
deja una funcion validada apoyada en un mecanismo que no se puede verificar. El MPC queda como la
opcion limpia para cuando se pueda comprobar en visor.

### CLEAR SKETCH
`BPC_TBTool_NC.ClearAll()`: si no esta dibujando, `ClearRedo` (destruye los escondidos) + destruye
todo `StrokeHistory` + `Clear`. Boton en la **seccion n+5** de la paleta (`M_TB_Clear`, glifo de X
en tono rojizo, duplicado de `M_TB_Undo` con otro `Custom`), en `ClearOffset (0, 6.5, 4.6)`,
arriba del undo. Deteccion por distancia 3D con flanco, igual que undo/redo.
Mapa de la paleta ahora, en local (**+Y se ve a la IZQUIERDA** por el Yaw 180):

| elemento | Y | Z | seccion |
|---|---|---|---|
| rueda de color | -7.4 | 0 | n |
| muestra | -7.4 | -4.2 | n+3 |
| 4 pinceles | +-1.7 | +-1.7 | 0..n-1 |
| barra de grosor | 0 | -4.6 | n+1 |
| undo | +6.5 | 0 | n+2 |
| redo | +6.5 | -4.6 | n+4 |
| **clear** | **+6.5** | **+4.6** | **n+5** |

Verificado en PIE: el ProcMesh de la paleta spawneada tiene **10 secciones**, la 9 con
`M_TB_Clear`.

### ZUMBIDO HAPTICO AL DIBUJAR
`DrawHaptic(Held)` en el Tick del director, **por flanco** con `bHapOn`:
`SetHapticsByValue(GetPlayerController(0), select(Held, DrawHapFreq, 0), select(Held, DrawHapAmp, 0), Right)`.
Vive en el director y no en la herramienta **porque el Tick del director ya tiene el estado del
gatillo** (`IA_Shoot_Right`): cero plomeria nueva.
El type_id del getter de input es `Input|EnhancedActionValues|IA_Shoot_Right`, **sin el `Get`**
que imprime el read. Otra vuelta de la gotcha 413.

### LO QUE QUEDO SIN HACER (y por que se dejo SIN EMPEZAR, no a medias)
1. **Paleta de 4 colores + degrade por slot.** Las perillas existen (`ColorMode`, `SlotColorA/B`,
   `bColorGradient`) pero **nada las lee todavia**. El degrade exige tocar `EmitPass` y
   `EmitTubeHard` para que el color del vertice sea `lerp(A, B, t)`.
2. **Save Sketch + animacion de desaparicion/aparicion.** Diseno decidido: `K_Arc`/`K_T` por nudo
   hacia **`V_UV1`** (el pin UV1 ya existe en el `CreateMeshSection` de `RebuildChunk`, hoy recibe
   0), parametro `Reveal` por trazo, `visible = K_T <= Reveal`, undraw 1 a 0 y draw 0 a 1. El
   centro sale del bounding box de todos los nudos y los trazos se reubican sumando un delta a
   `K_Pos` y reconstruyendo **una vez** (no por cuadro: a 20 trazos por 200 nudos, rebuildear por
   cuadro en BP no entra en presupuesto).
   El boton NO se puso: un boton que no hace nada es peor que ningun boton.
3. **Audio** (loop por pincel con fade, click, sonidos de hide/show). Las perillas existen, nada
   las lee.

Las tres comparten un prerequisito: **la cirugia de `EmitPass` + `EmitTubeHard`** (arco y degrade
en la misma pasada). Son las dos funciones mas delicadas del motor y estan recien validadas; se
decidio no abrirlas al final de una tanda larga sin nadie que pueda probar en visor.


## Session log
- **2026-09-25** — Completo y compilando: motor + herramienta + pawn + nivel de prueba.
  Diseno escrito desde el codigo fuente clonado. Motor construido entero,
  compila limpio y guardado. Un crash de Unreal en el medio (Material Editor, null deref tras
  el Undo de un script fallido) costo la primera pasada de variables: **se reconstruyo guardando
  despues de cada tanda**. **Dos** crashes de Unreal, los dos por el Undo de un
  script fallido (gotchas 383-384). 🟢 **Visor OK, mecánica aprobada.** Un bug (secciones sin material) arreglado.

- **2026-09-27 (5a)** - 🎛️ **EL DIRECTOR.** El rig se renombro a `BP_TBDirector_NC` y ES el
  sistema: un actor que se arrastra, que usa **los motion controllers del pawn poseido** (ya era
  portable). 28 perillas en 6 categorias. 🔴 Las variables del director **no son legibles desde
  otros BP** en este MCP → el director **empuja** (`PushConfig` → `CfgX` del tool → `CloseStroke`
  → `SwayConfig` → MID). Verificado con **control negativo** (default 99 vs 0.18). + **Clear
  Sketch** (seccion n+5) y **zumbido haptico** al dibujar. ⬜ Sin empezar: 4 colores + degrade,
  Save Sketch y audio.
- **2026-09-27 (4d)** - 🌊 **El vaiven en visor: rigido y todos iguales.** Dos causas en la misma
  cuenta: la fase casi no cambiaba **a lo largo** del trazo (`SwayScale` 0.03 = 0,7 rad en 20 cm, y solo
  en XY) → se suma **`d * SwayWave`**, la distancia al nacimiento que ya estaba calculada; y la
  velocidad era **global** → **`SwaySeed`** por trazo modula `SwaySpeed`. 🟢 **Aprobado en visor.**
- **2026-09-27 (4c)** - 🌿 **VAIVEN portado del pincel viejo** con sus valores aprobados.
  Dos cosas no se podian copiar: la mascara ya no sale de la UV (`K_U` cambia de significado con
  `UVStyle`) → **distancia de mundo a `K_Pos[0]`**; y no hay MID por trazo →
  **`Set*ParameterValueOnMaterials`**, que lo crea adentro. `MF_TB_Sway` al WPO de los 4 maestros,
  con `SwayOn` en 0 = neutro. ⬜ Sin visor.
- **2026-09-27 (4b)** - 🔁 Dos correcciones de visor: `SizeLo` 0.0625 -> **0.5** (yo habia
  BAJADO el piso y el lo queria subir; de paso la tabla anterior usaba un maximo mal leido), y la
  paleta arrancaba **sin nada seleccionado** dibujando con el preset -1 (la rama default). Los dos
  sintomas eran el mismo hecho. Arreglado con **dos defaults**: `Selected` 0 y `BrushIndex` 0.
  🟢 El undo funciona en visor.
- **2026-09-27 (4a)** - 🔁 **REDO.** El cambio de fondo: el undo pasa de **destruir** a
  **esconder** (`SetActorHiddenInGame` + `RedoStack`), que es como lo hace TB (`StepBack`/
  `StepForward` sobre dos pilas, `Stroke.Uncreate/Recreate`). Un trazo nuevo llama a `ClearRedo`,
  que destruye los escondidos. Boton nuevo en la paleta (seccion n+4, `M_TB_Redo` = el glifo del
  undo espejado con una linea), simetrico con la rueda. `SizeLo` 0.25 -> 0.0625. **Todas las
  sondas sacadas.** Gotchas 413-414. Verificado en PIE (9 secciones); ⬜ falta visor.
- **2026-09-27 (3a)** — 🐞 **El undo disparaba y no borraba**: `bind` de un `Array Get` (nodo
  PURO) **antes** del `RemoveIndex` → se evaluaba despues de la mutacion y devolvia `None`.
  Arreglado invirtiendo el orden. Gotcha 409. La receta de caza (PIE + estado + forzar la
  condicion) quedo anotada.
- **2026-09-27 (2a)** — 🔬 **"El undo no funciona" resuelto sin visor**: PIE + leer las
  variables de la paleta spawneada probo que el boton existe y esta cableado (`SwatchMid`,
  `Tool`, `Tip` validos) → el fallo era la **zona de acierto**, una caja de ±1,2 cm contra los
  3 cm de radio de las ranuras. Pasa a distancia 3D con `UndoPick` = 2.0. ⚠ sondas `BTN` y
  `UNDO FIRE` puestas.
- **2026-09-27** — 🎨 Slider remapeado (`SizeLo` 0.25 / `SizeHi` 1.5, extrapola arriba del
  maximo), **boton de UNDO por flanco** (copiar el patron de la rueda habria borrado un trazo por
  cuadro), **muestra de color** en la paleta, y la esfera a la mitad tomando el color del pincel.
  🔴 Dos trampas: `CreateDynamicMaterialInstance` resuelve a dos sobrecargas segun el grafo, y
  `SetVectorParameterValue` esta duplicado → `declaring_class`. ⬜ Sin visor.
- **2026-09-26 (3i)** — 🔑 **El rig se configura solo**: la instancia volvio a rechazar las
  escrituras (396 otra vez, solo entro `staticMesh`), asi que `InstallTip` pone malla, material,
  escala y offset **en runtime desde variables** — ya no hace falta recolocar el actor, y las
  perillas funcionan en la instancia. Slider con **marcador de posicion** y **arrastrable con la
  punta** (no depende del stick). ⬜ Sin visor.
- **2026-09-26 (3h)** — 🎯 `SM_Tip`: esfera de 1,2 cm en `RightAim` que es **origen del trazo y
  puntero de seleccion** a la vez (🔴 recolocar el rig). 📏 Grosor por stick derecho con la curva
  real de TB (**lerp en la raiz**, `BrushLerp.Default = SqrtRadius`), minimos en un array
  `SizeMins[9]`; el eje se lee con `GetInputAnalogKeyState` porque `IMC_Default` no mapea el
  stick derecho en X. Barra de grosor en la paleta (con `OneMinus` por el espejado). ⬜ Sin visor.
- **2026-09-26 (3g)** — 🎨 **Paleta reducida a 4 + rueda de color.** La paleta se ve
  **espejada** (Yaw 180): su numeracion es la fila invertida, confirmado por dos evidencias.
  Sus 3/4/6/9 = TaperedMarker, OilPaint, Light, WetPaint. Ahora la paleta es un array
  `BrushIds` editable; los 9 presets e iconos siguen guardados. Rueda HSV por `Custom` en la UV,
  seleccion por proximidad sin gatillo. ⬜ Sin visor.
- **2026-09-26 (3f)** — 🟢 **Petal VALIDADO EN VISOR: "ahora si se abren"**. Punta poligonal
  medida: el paso lateral supera el ancho de la hoja solo en t>0.95 y **no lo arregla teselar**
  → `TipMinCurve` (default 0 neutro, 0.15 en Petal). Light: calculado que **ningun `Gain` lo
  arregla sobre fondo azul** (el B del fondo no baja de 112); sobre oscuro con Gain 4 sale
  exactamente lo que recuerda. 🔴 Pendiente de Beltran: fondo oscuro o `r.MobileHDR`.
- **2026-09-26 (3d/3e)** — 🏆 **Petal resuelto en la causa raiz**: `m_HardEdges: 1` no es
  sombreado, es **el mecanismo de la separacion** — dos vertices coincidentes con normales de
  cara distintas, y el empuje va por la normal → el tubo se rasga en petalos. Emisor nuevo
  `EmitTubeHard` (2N vertices/anillo, sin costura de UV); `EmitPassTube` queda huerfano.
  Light: el halo **y el ancho** son bloom → `BrushSize` 0.8→3.0 y `Gain` 4→2, razonados.
  ⬜ Sin visor. 🔴 Pendiente de Beltran: fondo oscuro o `r.MobileHDR`.
- **2026-09-26 (3c)** — 🔬 Presion **llega a 1** (medido en visor). El "lapiz rojizo" es un
  pincel **ADITIVO** sobre fondo azul (modelo aditivo gana 27 vs 46; nucleo (208,116,116)):
  causa el fondo, no el pincel. Light: el halo es **bloom HDR**, imposible con MobileHDR=False.
  Petal: su shader es **difuso + `m_HardEdges`** → agregado sombreado facetado con `ddx/ddy`.
- **2026-09-26 (3b)** — 🔬 **El "rojizo" no era color: era ancho.** Midiendo los pixeles de la
  captura, el nucleo de los dos trazos daba (255,140,50) exacto; el pincel 0 salia a 8 px con
  0,1% a color pleno. Light: `Gain` 180->4 (el 180 era fiel pero HDR, y aca no hay HDR).
  Corregida la gotcha 395: `IndexCurl` **si** es el eje del gatillo. ⬜ Sonda de presion puesta.
- **2026-09-26 (3a)** — 🔧 **Petal: tres causas.** `BrushSize` 12->2 (el 6x), el empuje del
  petalo estaba a la mitad (el `0.5` del radio colado en el offset), y lo de fondo: **Petal en TB
  es un shader DIFUSO con gradiente 0.6->1 a lo largo del trazo + AO en la cara trasera**, y
  nuestro `M_TB_Solid` era color plano. Portado con `PetalShade` (default 0 = neutro) +
  `MI_TB_Petal`. Y medido por que el naranja se ve rojo (3b). ⬜ Sin visor.
- **2026-09-26 (2a)** — 🟢 **Rig VALIDADO EN VISOR.** Cuatro bugs en cuatro pasadas: `EnableInput`
  mal targeteado (394), malla sin asignar en la instancia (396), el corte del trazo colgado del
  sensor del dedo en vez del gatillo (395), y los mandos con `SnapToTarget` + material lit. Los
  mandos pasaron del pawn al rig. ⬜ Sin respaldo todavia.
- **2026-09-26** — 🟢 Arreglado el rig: los grips del pawn de prueba no tenian `MotionSource`
  (default `Left`), asi que la instalacion nunca pasaba el gate. Gate reestructurado para que
  degrade por partes. Verificado en PIE por log; **pendiente visor**.

## TODO
- `m_BackfaceHueShift` necesita doble cara real (hoy two-sided por material).
- `TrimShortStrokeAfterBreak` (borra tiras de menos de 6 nudos tras una rotura).
- Varianza determinista con `HashFloat01` — el descriptor ya tiene `SizeVariance`, falta el hash.
- Las 72 texturas reales del repo (Apache 2.0) en vez de las generadas con PIL.
- 🔴 **`ApplyShapeToSize` multiplica `K_Size` EN SU LUGAR.** Hoy no acumula porque `FramePass`
  reescribe `K_Size` entero cada cuadro (verificado) — pero es una mina: cualquier cambio que
  deje de reescribirlo convierte esto en `size * curve^cuadros` -> el trazo se desvanece.
- ~~Petal: `m_HardEdges` sin portar~~ — **PORTADO** el 2026-09-26 (3d): era el mecanismo de la
  forma, no un detalle de sombreado. Ver `EmitTubeHard`.

## 2026-09-27 (5b) - LO QUE FALTABA DEL DIRECTOR: 4 colores + degradado, Save Sketch, audio, clic, Target Point

Retomado por la mañana (*"Pensé que dejarías lista toda la instrucción. Continúa"*). Todo compila, PIE limpio;
**nada de esto pasó todavía por el visor**.

### La idea que destrabó las tres cosas: UN dato nuevo por vértice
`EmitExtras()` (función nueva, llamada en `RebuildChunk` entre `EmitDispatch` y `CreateMeshSection`) **no toca los
emisores** (`EmitPass`/`EmitTubeHard` quedan como estaban). Hace una pasada aparte sobre `V_Pos`:
- `K_Arc[i]` = largo recorrido acumulado en cm (misma suma que `StretchAccum`, pero **incremental desde `ChunkStart`**).
- `V_UV1 = (arco, off.x)`, `V_UV2 = (off.y, off.z)`, con `off` = vértice − centro de su nudo. Centro: en la cinta, el
  punto medio del par (que es el centro suavizado exacto); en el tubo, `K_Pos[k]`.
- Los pines UV1/UV2 del `CreateMeshSection`, que recibían 0, ahora reciben esos arreglos.

### Degradado — `MF_TB_Grad` (nueva) en los 4 maestros
`Tint = lerp(GradA, GradB, saturate(UV1.x / StrokeLen))`, multiplicado **al final** de la cadena del emisivo
(`Multiply` nuevo antes de `MP_EmissiveColor` en Solid/Additive/Masked/Paint; las 4 cadenas terminan en un Multiply,
o sea que son lineales en el color). **Neutro por defecto**: `GradA = GradB = (1,1,1)` → multiplicar por 1 exacto.
- En modo degradado el trazo pone `BaseColor` en blanco (`SetLook`) y el color lo dan `GradA/GradB` por MID.
- `StrokeLen` se actualiza **en vivo** mientras se dibuja (`LookStep` al frente de `UpdatePosition`, solo si
  `bGradient`) y al cerrar (`PushLook` al final de `EndStroke`, siempre). Default del parámetro **10000**, no 0: con 0
  el colapso del reveal escondería todo el trazo (y 1e5 desborda fp16 en el pixel shader).
- **`bPrimaryAtTip` (default true)**: el color primario va en la PUNTA (lo que se está dibujando, igual que la esfera
  de la punta y la muestra), el secundario queda en la cola. En `false` se invierte.

### Save Sketch — el colapso por WPO, sin rebuild por cuadro
En `MF_TB_Sway` (ya estaba en los 4 maestros) se agregó un `Custom` `RevealCollapse`:
```
h   = saturate((arco - Reveal*(StrokeLen+Taper)) / Taper + 1)
WPO = lerp(vaiven, -offMundo, h)       ; offMundo = TransformVector(Local->World, (UV1.y, UV2.xy))
```
Lo no revelado **colapsa sobre el eje del trazo**: triángulos de área cero = invisibles, **también en el material
opaco** (que no puede esconderse con máscara). El borde queda como una **punta afilada** de `Taper` cm (perilla
`RevealTaper`, 6). El vaivén se apaga en lo colapsado para que el par de vértices no se separe (si no, quedaba una
astilla de ~0,5 cm). **Neutro por defecto**: `Reveal = 1`.
Máquina de estados en `BPC_TBTool_NC` (`SketchStep` desde el Tick del director): fase 1 `SketchHide` (Reveal 1→0 con
smoothstep, sonido de ocultar) → `SketchRelocate` → fase 2 `SketchWait` (`SketchGap`, sonido de mostrar) → fase 3
`SketchShow` (0→1). `SaveSketch` exige no estar dibujando y fase 0; vacía el redo (como TB) y **fotografía** el
historial en `SketchSet`, así lo que se dibuje durante la animación no entra.

### Reubicación: composición de transforms, y el TARGET POINT (pedido de Beltrán a mitad de la tanda)
*"incluir en el mundo un target point que define donde aparece nuestro dibujo guardado... si achicamos, rotamos o
movemos el target point, afecta al dibujo"*.
`SketchRelocate` arma `N` = llevar el dibujo a un marco canónico: centro del **bounding box** (ancho/alto/profundo
máximos, `GetActorBounds` de cada trazo) al origen, su **frente** (lado que miraba al usuario) hacia **+X**, escala 1.
Después compone con el destino:
- con **`SketchTarget`** asignado → el transform del actor (posición, rotación **y escala**). **La flecha +X del
  Target Point es hacia donde mira el frente del dibujo.**
- sin target → frente al usuario a `SketchDist` (90 cm), mirándolo; `bCenterZ`/`SketchUp` solo aplican acá.
Cada trazo recibe `Compose(su transform, M)` vía `SetPlacementXf`, que también reubica `SwayOrigin`. La escala es
**absoluta** (N divide por la escala actual), así guardar dos veces con el target a 0,5 no da 0,25.
En `L_TBTest` se colocó un **`TargetPoint` "SketchTarget"** en (-195, 0, 150), Yaw 180 (1,2 m frente al pawn, flecha
hacia él), asignado en la instancia del director.

### 4 colores en la paleta
`ColorMode = 1` (y `SlotColorA/B` de 4) reemplaza la sección de la rueda por **4 cuadrados 2×2** con color por vértice
(`M_TB_UIColor`, nuevo: unlit, emisivo = VertexColor) que muestran **solo el primario**. `TestColor` despacha a
`TestColors` o al `TestWheel` de siempre (cirugía en `PickSlot`: el nodo `TestWheel` se reemplazó). Elegir uno pone en
la herramienta `BrushColor = A[k]`, `GradColorB = B[k]`, `CfgGradOn = bColorGradient`. Orden visto por el usuario:
0 arriba-izq, 1 arriba-der, 2 abajo-izq, 3 abajo-der (+Y local es la IZQUIERDA por el espejo).
✅ PIE, contra el modo 0 como control: sección 4 = `M_TB_ColorWheel`/`CfgGradOn false` en modo 0;
`M_TB_UIColor`/`BrushColor = A[0]`/`GradColorB = B[0]`/`CfgGradOn true` en modo 1. **La instancia quedó en modo 1.**

### Botón SAVE
Sección n+6, `M_TB_Save` (duplicado de `M_TB_Clear`, glifo de **marco con un rombo**, dorado; simétrico en los dos
ejes para no depender de la orientación de las UV), en `SaveOffset (0, -7.4, 4.6)` = arriba a la derecha vista por el
usuario, espejo de Clear. ✅ PIE: 11 secciones, la 10 con `M_TB_Save`.

### Audio y háptica (todo en el director, `DirectorStep` reemplazó a `DrawHaptic` en el Tick)
- **Loop por pincel**: flanco de `bDrawing` de la herramienta (no del gatillo: suena solo si de verdad se dibuja).
  `SpawnSoundAttached` a la punta + `FadeIn(LoopFade, BrushLoopVol[slot])`; al soltar `FadeOut` (el componente se
  autodestruye). El slot sale de `FindItem(BrushIds, BrushIndex)`. `FadeIn/FadeOut` van en envoltorios
  (`AudioFadeIn/Out`) creados por cirugía con `declaring_class AudioComponent` (gotcha 40: el DSL agarra el de Synth).
  Defaults: los 3 loops del pincel viejo (`/Game/Drawing/Sound/`, los tres con `bLooping=true`); el slot 4 repite el
  primero hasta que Beltrán elija otro.
- **Clic**: la paleta cuenta (`ClickScan` al final de `PickSlot`: cambio de pincel, de color, flanco de entrada a la
  rueda, escalón del 10% del grosor, flanco de cualquier botón) y el director compara `ClickCount` → `PlaySound2D` +
  pulso háptico de `ClickHapDur`. `bClickArmed` evita el clic falso del primer cuadro (verificado: `ClickCount 0`).
- **Háptica unificada** (`HapticStep`): estado 2 = clic, 1 = dibujo, 0 = nada; **se reenvía cada cuadro** mientras
  hay vibración (por si el runtime de OpenXR aplica duración mínima al valor). `DrawHapPulse` (Hz, 0 = continuo)
  convierte el zumbido en pulsos.
- Sonidos por defecto del motor (one-shots, `bLooping=false` verificado): clic `VR_click1`, ocultar
  `VR_shep_scale_down_02`, mostrar `VR_shep_scale_up_02` (`/Engine/VREditor/Sounds/`).
- 🔴 La **instancia** del director tenía `BrushLoop` vacío y sonidos en `None` (valores capturados antes): se
  asignaron en la instancia, además del CDO.

### Perillas nuevas del director
`01 COLOR`: `bPrimaryAtTip` · `03 SKETCH`: `SketchTarget`, `SketchDist`, `SketchUp`, `RevealTaper` · `05 HAPTICA`:
`DrawHapPulse`. Empujadas por `PushExtras` + `PushPalette` + `PushTarget` al final de `DoInstall`.

### Sin verificar (necesita visor)
El degradado sobre un trazo real, la animación de Save (colapso, punta, sonidos, reubicación y que el target
escale/rote bien), los loops y el clic. PIE solo probó la configuración y la paleta.

## 2026-09-27 (5c) - Primera vuelta de visor de 5b: *"wwwow. Está increíble"* + cuatro ajustes de paleta

1. **Paleta fija en la mano.** Giraba porque `FacePlayer` (en `PickSlot`) le hacía `SetWorldRotation` hacia la
   cámara **cada cuadro**. Se sacó de la cadena (el nodo, no la función). La orientación ahora es la relativa del
   componente `Mesh` respecto del grip izquierdo, y pasó a perilla del director (**07 PALETA**: `PaletteOffset`
   (6,0,6), `PaletteRot` (Pitch -35, Yaw 180), aplicadas por `PlacePalette` al final de `DoInstall`). Son los valores
   de diseño originales del componente, **nunca probados en visor sin FacePlayer**: si la paleta queda mal inclinada,
   se ajusta `PaletteRot.Pitch`. ✅ PIE: la rotación relativa se mantiene en (-35,180,0) en ejecución.
2. **Zona sin dibujo.** `PaletteExtras` (nueva, al final de `PickSlot`) pone `Tool.bCanDraw = distancia(punta,
   NoDrawCenter) > NoDrawRadius` (14 cm alrededor del centro de la paleta, (0,-0.8,0) local). `Press` ya exigía
   `bCanDraw` → **no se puede EMPEZAR** un trazo con la punta cerca de la paleta. Un trazo ya empezado que pasa por la
   zona no se corta. ✅ PIE con control: radio 14 → `false` (en escritorio los dos mandos quedan juntos), radio 0 →
   `true`.
3. **Lo seleccionado se adelanta** `SelectLift` (1,2 cm) hacia el usuario (+X local del `Mesh`, el eje que usaba
   `FacePlayer` para mirar a la cámara). Pinceles: WPO nuevo en `M_TB_Icon` (`Lift`, neutro en 0, dirección =
   `TransformVector(Local->World, (1,0,0))`), fijado por slot desde `PaletteExtras` vía `MidLift` (envoltorio por
   cirugía con `declaring_class MaterialInstanceDynamic`: `SetScalarParameterValue` está duplicado MID/MPC).
   Colores: `BuildSwatches` (copia de `BuildColors` con X desplazada para `ColorSel`), llamada al final de `PickColor`.
4. **Clic al tocar lo ya seleccionado.** Antes solo sonaba al CAMBIAR la selección. `PaletteExtras` suma el flanco de
   "tocar" (un pincel: `BestDist < PickRadius`; un color en modo 1: dentro de la grilla). Si cambia y toca a la vez
   suman 2 al contador, pero el director compara `!=` → suena una vez.

### Actores de `L_TBTest` (pregunta de Beltrán)
`BP_TBDrawRig_C_1` = el director TB (etiqueta vieja, clase `BP_TBDirector_NC`) — necesario. `BP_TBPawn_C_0` = pawn VR
pelado de prueba — hace falta UN pawn VR, cualquiera. `BP_DrawDirector_NC_C_0` = director del **pincel viejo**
(`BPC_DrawTool_NC`/`BP_Stroke`); el sistema TB no lo referencia (`get_dependencies`) → prescindible en este nivel.
No se sacó: pendiente de su confirmación.

## 2026-09-27 (5d) - Segunda vuelta de visor: cuatro ajustes más
1. **El seleccionado se iba hacia ATRÁS.** Con la paleta fija, el +X local del `Mesh` apunta hacia afuera (con
   `FacePlayer` apuntaba a la cámara, por eso lo supuse al revés). La perilla sigue positiva ("cuánto se adelanta");
   `PlacePalette` empuja a la paleta `-SelectLift` vía `MapRangeUnclamped(0→0, 1→-1)`. Afecta pinceles (WPO) y
   colores (`BuildSwatches`) por igual. ⚠ La macro `Math|Float|NegateFloat` NO es un negado puro: es la macro que
   modifica una variable por referencia (tiene exec) — no sirve para esto.
2. **Paleta 4 cm a la izquierda**: `PaletteOffset` (6, -4, 6) en CDO e instancia (−Y del grip = izquierda).
3. **Sonido propio del slider, más sutil**: `SliderScan` (paleta, entre `ClickScan` y `PaletteExtras`) cuenta los
   escalones del 10% en `SliderCount`; `SliderStep` (director, al final de `DirectorStep`) toca `SliderSound`
   (`VR_click2`, 0,38 s) a `SliderVol` 0,3, sin háptica. El escalón se sacó del clic general **sin romper nodos**: el
   `!=` de `ClickScan` ahora compara `PrevDetent` consigo mismo (siempre falso). `SliderPrev = -1` evita un tic al
   arrancar (verificado: `SliderCount 0`).
4. **Grosor inicial 45%**: el `Size01` de la plantilla del componente `TBTool` en el director y de la instancia
   estaban en **0** (por eso arrancaba al mínimo). Perilla nueva `StartSize` (0,45, 07 PALETA), empujada por
   `PushStartSize` al final de `DoInstall`. ✅ PIE: `Size01 = 0.45`.

### 5e - `L_TBTest` limpio (pedido explícito de Beltrán: "solo los actores necesarios + la esfera de color")
Sacados: `BP_DrawDirector_NC_C_0` (director del pincel viejo, sin referencias desde el sistema TB) y `PlayerStart`
(el pawn tiene `autoPossessPlayer = Player0`, no se usaba). Conteo 14 → 12. Quedan: `BP_TBDrawRig_C_1` (director),
`BP_TBPawn_C_0`, `TargetPoint_0` (SketchTarget), `BP_Sky_Sphere_C_1` (la esfera de color) + los actores del motor
(WorldSettings, Brush, PhysicsVolume, NavData, debuggers, BuoyancyManager, LevelScript). ✅ PIE: un solo pawn,
paleta instalada, herramienta configurada.

## 2026-09-27 (5f) - MANO HÁBIL (para Soul Charger: la elige el usuario en otra etapa)
Perilla **`bLeftHanded`** (categoría **00 MANO**) + función pública **`SetHandedness(LeftHanded)`** para cambiarla en
caliente. Define: mano de la punta + gatillo de dibujo + malla del control, y la mano de la paleta (sin malla).

**Cómo está hecho (los nombres de variable quedaron por ROL, no por mano):** `RightAim` = apuntador de la mano que
dibuja, `RightGrip` = grip de la mano que dibuja, `LeftGrip` = grip de la mano de la paleta.
- `ResolveHands` (al frente de `FindControllers`) llena `SrcAim/SrcPalGrip/SrcDrawGrip` con los MotionSource que
  corresponden ("RightAim"/"LeftGrip"/"RightGrip" o "LeftAim"/"RightGrip"/"LeftGrip"); las comparaciones de
  `SortController/SortLeft/SortRGrip` leen esas variables en vez de literales. Todo lo de abajo (paleta, punta,
  sonido del loop, zona sin dibujo) sigue solo.
- **Input sin tocar eventos**: `IMC_TB_DrawLeft` (nuevo, `/Game/Drawing/TB/`) mapea el gatillo IZQUIERDO a
  `IA_Shoot_Right` y su eje a `IA_Hand_IndexCurl_Right` (presión). `AddDrawIMC` saca `IMC_Weapon_Right` y
  `IMC_TB_DrawLeft` y agrega el que toca. El evento, `GateStop` y el zumbido siguen escuchando `IA_Shoot_Right`.
  ⚠ `IMC_Hands` sigue mapeando el eje del gatillo derecho a la presión: con zurdo, apretar el gatillo de la mano de la
  paleta mientras se dibuja puede sumar presión. Menor; anotado.
- Joystick del grosor: `SizeStep` (reemplazó a `AdjustSize` en el Tick) lee el stick de la mano que dibuja.
  Háptica: `HapSend` (reemplazó al `SetHapticsByValue` fijo en "Right" dentro de `HapticStep`).
- Mallas: `FixHands` pone visible `SM_RHand` (diestro) o `SM_LHand` (zurdo, que ya trae la malla del control
  izquierdo) en el grip que dibuja y **oculta la otra**. Antes la mano de la paleta mostraba su control.
- Paleta: `MirrorPalette` espeja `PaletteOffset.Y` para la mano derecha (+4 = hacia afuera). El contenido de la
  paleta NO se espeja (la rueda sigue del mismo lado).
- `ApplyHands` = `AddDrawIMC` + `FixHands` + `MirrorPalette`, al final de `DoInstall`. `SetHandedness` =
  setear + `FindControllers` + `InstallTip` + `ReattachPalette` + `PlacePalette` + `ApplyHands`.
- La **zona sin dibujo** no necesitó cambios: se mide en el espacio local de la paleta con la punta de la mano que
  dibuja, así que viaja con la paleta.

✅ PIE, las dos manos: diestro → punta `MC_Right`, paleta `MC_LGrip`, `SM_LHand` oculta; zurdo → punta `MC_Left`,
paleta `MC_RGrip` (offset Y +4), `SM_LHand` visible en `MC_LGrip`, `SM_RHand` oculta. Log limpio. ⬜ Input zurdo no
verificable sin mandos.

**Contrato para Soul Charger**: el pawn tiene que tener MotionControllers con MotionSource `LeftAim`, `RightAim`,
`LeftGrip`, `RightGrip` (los del VRTemplate). La etapa que elige la mano llama `SetHandedness(bZurdo)` sobre el
director, o setea `bLeftHanded` antes de que se instale.

### 5g - Ajustes de paleta + prueba zurda
- **Muestra de color oculta en modo 4 colores**: `HideSwatch` (`SetMeshSectionVisible(n+3, false)`) al final de
  `BuildSwatches`. En modo rueda la muestra sigue (es la única marca del color en la paleta). La sección se crea una
  sola vez (BuildExtras) y nada la reconstruye, así que no reaparece.
- `SelectLift` 1,2 → **0,5 cm** (CDO + instancia).
- Instancia de `L_TBTest` en **`bLeftHanded = true`** para la prueba en visor (PIE: punta `MC_Left`, paleta
  `MC_RGrip`, log limpio). Volver a `false` después de probar.

### 5h - Zurdo NO dibujaba en visor → input izquierdo con acción PROPIA
Beltrán: *"No funciona el dibujo con la izquierda"*. El atajo de 5f (`IMC_TB_DrawLeft`: gatillo izquierdo →
`IA_Shoot_Right`) usaba la MISMA tecla que `IMC_Weapon_Left` (`OculusTouch_Left_Trigger_Click`), así que la tecla no
era el problema; la causa exacta quedó **sin identificar** (no hay forma de inyectar el gatillo desde MCP). Se cambió
a lo que ya está probado en el VRTemplate, sin trucos:
- `AddDrawIMC` ahora agrega **`IMC_Weapon_Left`** (zurdo) o `IMC_Weapon_Right` (diestro) y saca el otro.
- Evento nuevo **`IA_Shoot_Left`**: Started → `TB_Press`, Completed → `TB_Release` (los mismos nodos que el derecho).
  En diestro `IMC_Weapon_Left` no está cargado, así que ese evento nunca dispara.
- `GateStep` (reemplazó a `GateStop` en el Tick): corta el trazo leyendo `IA_Shoot_Left` o `IA_Shoot_Right` según la mano.
- Presión: evento nuevo `IA_Hand_IndexCurl_Left` + `PressureFrom(V, FromLeft)` en los DOS eventos de curl: solo pasa
  la presión de la mano que dibuja (antes la mano de la paleta también podía escribirla).
- `IMC_TB_DrawLeft` borrado (sin referencias).
- Sonda disponible: `TB_Press` imprime **"RIG press"** en pantalla. Si al apretar el gatillo izquierdo aparece y no se
  dibuja, el problema está después del input (zona sin dibujo, punta), no en el input.

### 5i - Zurdo pintaba PUNTITOS: `IA_Shoot_Left` tenía trigger **Pressed**
"RIG press" aparecía, pero el trazo se cerraba al instante. Las dos acciones del VRTemplate NO están configuradas igual:
`IA_Shoot_Right` → `InputTriggerHoldAndRelease` (sostiene), `IA_Shoot_Left` → `InputTriggerPressed` (Started y
Completed en el mismo golpe → `TB_Release` inmediato). Se vació `triggers` de `IA_Shoot_Left` (comportamiento
implícito "Down": empieza al apretar, sigue mientras se mantiene, termina al soltar).
⚠ **Dependencia de portabilidad**: el sistema depende de `IA_Shoot_Right`/`IA_Shoot_Left` del VRTemplate **modificados**
(no son los defaults del template). Al migrar a Soul Charger hay que llevar estos dos IA tal como están, o crear IA
propios en `/Game/Drawing/TB/`. Otro que usa `IA_Shoot_Left`: `VRTemplate/Blueprints/Pistol` (no está en el nivel;
con este cambio dispararía en ráfaga).

## 2026-09-27 (5j) - El dibujo guardado GIRA, se exhibe 5 s, se des-dibuja y avisa FIN DE ETAPA
Máquina de estados nueva `SketchStep2` (reemplazó a `SketchStep`, borrada) llamada desde `DirectorStep`:
1 `SketchHide` (des-dibuja en su lugar) → reubica → 2 `SketchWait` → 3 `SketchShow` (dibuja) → **4 `SketchHold`**
(exhibe `CfgHold` s; `SketchShow` ahora termina en 4 en vez de 0) → **5 `SketchOut`** (sonido de ocultar + des-dibujo
en `HideTime`) → 0, con `StageCount++`.
- **Giro** en fases 3-5 (`SketchSpin` → `SpinArm` la primera vez, después `SpinApply`): rota todo el `SketchSet`
  alrededor de un pivote fijo `SketchPivot` sobre el eje `SketchAxis`. Con `SketchTarget`: pivote = posición del target y
  eje = su *up* (si el target está inclinado, gira sobre su propio eje). Sin target: centro del bounding box y Z.
  Transform por cuadro: `M = MakeTransform(p - R·p, R, 1)` con `R = RotatorFromAxisAndAngle(eje, SpinSpeed·dt)`,
  aplicado con el `SketchApplyXf`/`PlaceStrokeXf` de siempre (también mueve `SwayOrigin`). `bPivotSet` se resetea en
  la fase 1.
- **Fin de etapa**: `StageStep` (director, al final de `DirectorStep`) compara `StageCount` de la herramienta → imprime
  **"Stage finished"** y dispara el **event dispatcher `OnStageFinished`** del director: es el gancho para que Soul
  Charger pase a la siguiente etapa.
- Perillas (03 SKETCH): `SpinSpeed` 20 °/s, `HoldTime` 5 s. Empuje: `PushSpin` al final de `DoInstall`.
✅ PIE: perillas empujadas, fase 0, log limpio. ⬜ La secuencia completa solo se prueba dibujando (visor).

### 5k - Nivel armado como Soul Charger + color inicial + mano derecha
- 🔑 **El director NO crea ni referencia pawns** (usa `GetPlayerPawn(0)`; `get_dependencies` no lista `BP_TBPawn`).
  El pawn era solo del nivel de prueba, colocado con auto-possess. Para probar el mismo camino que Soul Charger:
  `GM_TBTest` (duplicado de `GM_VR`, `DefaultPawnClass = BP_TBPawn`) como GameMode de `L_TBTest`, **PlayerStart** en
  (-315,0,106) Yaw 0, y el `BP_TBPawn` colocado **sacado**. ✅ PIE: el GameMode spawnea el pawn en el PlayerStart y el
  director se instala solo. (`GM_VR` spawnea el `VRPawn` del template, cuyo stick hace teleport/giro: chocaría con el
  grosor por joystick; en Soul Charger revisar qué hace el stick de su pawn.)
- **Color default hacia atrás al iniciar**: orden de instalación. `PushPalette` (dentro de `PushExtras`) construía las
  muestras con el `SelectLift` por defecto de la paleta (+1,2 = hacia atrás) ANTES de que `PlacePalette` empujara el
  valor con el signo correcto. `RefreshPalette` (vuelve a correr `ApplyColorMode`) al final de `DoInstall`.
  ✅ PIE: cuadrado 0 en X = -0,5.
- Instancia de vuelta en `bLeftHanded = false`.
- Pregunta de calidad del dibujo en el target: ver respuesta en la conversación; el código no cambia la malla ni el
  material al reubicar (mismo ProceduralMesh, mismos MIDs, `Reveal = 1` al terminar de aparecer).

### 5l - Grosor SOLO por el slider (el joystick se apaga)
Beltrán creía que el joystick ya estaba fuera; el registro dice que no (3h lo agregó, 3i hizo el slider tocable y los
dos convivían escribiendo `Size01`). Se apaga: en el Tick, `SizeStep` quedó detrás de `SizeGate`, que solo lo llama
si **`bSizeByStick`** (07 PALETA, default **false**). Resuelve de paso el choque con el stick del pawn de Soul Charger.

## 2026-09-27 (5m) - LA MESA DE DIBUJO: el ancla pasa a ser un área designada
Beltrán: el usuario dibuja sobre una **mesa** (disco ~40 cm, azulado translúcido que se desvanece al borde); al
guardar, el dibujo queda en el Target Point **tal como estaba respecto de la mesa**. Ya no se recentra por bounding box.
- **`BP_TBTable`** (nuevo): `Disc` = `/Engine/BasicShapes/Plane` a escala 0,4 con **`M_TB_Table`** (unlit,
  translúcido, two-sided; `TableColor` (0.25,0.55,1), `TableOpacity` 0,35; Custom `TableFade`: plano en el centro,
  se desvanece en el 60% exterior con smoothstep) + `Front` (ArrowComponent, oculta en juego). La colisión del plano no
  se pudo apagar por MCP (`collisionProfileName` no escribible); no afecta (el dibujo no traza).
- **Convención**: la flecha +X de la mesa apunta **hacia quien dibuja**, igual que la del target apunta hacia quien
  mira → el frente del dibujo siempre queda hacia el espectador. Colocada en `L_TBTest` en (-265,0,110) Yaw 180 (50 cm
  frente al PlayerStart) como **`DrawTable`**, asignada al director.
- **Transform**: `SketchApply2` (reemplazó a `SketchApply` en `SketchRelocate`): con mesa, `N = Invert(Mesa sin
  escala)` y después el target (o el frente-al-usuario si no hay target). Sin mesa, el comportamiento anterior.
  Mover/rotar la mesa cambia el ancla; su escala NO escala el dibujo (sí la del target).
- **Archivo al terminar la etapa**: `SketchArchive` (al final de `SketchOut`) oculta los trazos del `SketchSet` y los
  saca de `StrokeHistory` (quedan "en memoria" como actores ocultos). Sin esto, un segundo Save volvía a mover el dibujo
  anterior, que ya no está sobre la mesa.
- Director: `DrawTable` (03 SKETCH) + `PushTable` al final de `DoInstall`. ✅ PIE: mesa y target empujados, log limpio.

### 5n - La mesa viaja con el dibujo + slider abajo
- **Mesa en el Save**: `TableStep(DT)` (herramienta, al final de `DirectorStep`) lee la fase y el tiempo de la animación.
  Flancos (`TableEdges`, con `PrevPhase`): 0→1 guarda `TableHome`; 1→2 (recién reubicado) lleva la mesa al target con
  **escala = escala del target × escala original de la mesa** (`TableToTarget`, solo si hay target); 5→0 la devuelve a
  casa (`TableGoHome`) y reinicia `TableT`. Fundido (`TableFadeSet` → parámetro nuevo **`TableFade`** en `M_TB_Table`,
  neutro en 1): fase 1 y 5 = 1−smooth (junto al des-dibujo), 2 = 0, 3 = smooth (junto al dibujado), 4 = 1, 0 = rampa de
  1 s al volver a casa. La mesa no gira (es un disco simétrico).
  ✅ PIE: el Disc tiene su MID (el fundido corre cada cuadro), log limpio.
- **Slider**: `SliderOffset` (0,0,−4.6) → **(0,0,+4.6)** en el CDO de la paleta. Queda en la fila de Clear/Save, entre
  ellos, sin solaparse (Clear ocupa y 4.9..8.1, Save −9..−5.8, slider ±3).
  🔴 Diagnóstico: que Beltrán viera el slider ARRIBA cuando estaba abajo en local, y que el adelantado saliera hacia
  atrás, apuntan a lo mismo: **con la paleta fija en la mano, se ve rotada 180° sobre su eje Y local** respecto de
  cuando `FacePlayer` la orientaba (+X hacia la cámara, +Z arriba). O sea, espejada verticalmente y vista desde atrás.
  Se hizo el cambio mínimo pedido; enderezarla entera (componer 180° en Y a `PaletteRot` y quitar el signo invertido
  de `SelectLift`) queda ofrecido.

### 5o - MIGRADO A SOUL CHARGER (2026-09-27): `/Game/NeuralCanvas/`
**Cómo se hizo (sin tocar nada de SC):** en Neural Canvas se **movieron** (`AssetTools.move`, arregla referencias) los
59 assets del sistema a una carpeta raíz propia, `/Game/NeuralCanvas/{TB, TB/Icons, TB/Textures, Input, Mesh, Sound}`, y
se **copió esa carpeta** a `VR_Test/Content/NeuralCanvas` (no existía → cero sobrescrituras). SC tiene su propio
`/Game/Drawing` con `White`/`Yellow`/sonidos de igual nombre: por eso NADA del paquete quedó bajo `/Game/Drawing`.
- ✅ Grep sobre los `.uasset`: las únicas rutas `/Game/` fuera de `/Game/NeuralCanvas` son `contentImportPath` (metadato
  de importación, inofensivo). Módulos `/Script`: todos del motor (ProceduralMeshComponent viene activo por defecto).
- ✅ En SC: `find_assets` ve los 59; los 5 BP compilan limpios (Stroke → Tool → Table → Palette → Director); recompile de
  los 8 materiales maestros sin `Failed to compile` en el log.
- **Input propio** (reemplaza la dependencia de `IA_Shoot_Left/Right` del VRTemplate, que SC no tiene):
  `IA_TB_Draw_R/L` (Boolean, **sin triggers**: Started/Completed = apretar/soltar; un trigger `Pressed` los dispara
  juntos y el trazo sale en puntitos, gotcha 425) y `IA_TB_Pressure_R/L` (Axis1D), todos con `bConsumeInput=false` para
  no robarle el gatillo al pawn de SC. `IMC_TB_Draw_R/L`: `*_Trigger_Click` de Oculus/Index/Vive/WMR → Draw,
  `OculusTouch_*_Trigger_Axis` → Pressure. El director agrega **solo el IMC de la mano que dibuja** (`AddDrawIMC`,
  prioridad 1000) y lo saca en `EndPlay` (`RemoveDrawIMC`).
- **No se migró**: `BP_TBPawn`, `GM_TBTest` (referencia `BP_GameFlowManager` de NC) ni `L_TBTest` (referencia además
  `/Game/OSC/BP_OSCRECIEVER`, y SC tiene su propia `/Game/OSC` → podría engancharse a un asset de SC por nombre). El
  pincel viejo `/Game/Drawing/BP` tampoco (arrastra `VRPawn`/`BP_PincelSelect`). Los **9 presets** de TB viajan adentro
  de `BP_TBStroke` (incluidos los que la paleta de 4 no muestra).

**Receta de instalación en un nivel de SC** (nada más; el director no crea ni referencia pawns):
1. El nivel usa el GameMode de SC (`BP_XRGameMode` → `BP_VRPawn_SC`) y su PlayerStart. El pawn cumple el contrato:
   MotionControllers con `MotionSource` `LeftAim`/`RightAim`/`LeftGrip`/`RightGrip`.
2. Arrastrar **`/Game/NeuralCanvas/TB/BP_TBDirector_NC`**.
3. Arrastrar un **`TargetPoint`** donde se exhibe el dibujo guardado: su +X apunta **hacia quien mira**; mover/rotar/
   escalar el target afecta al dibujo.
4. Arrastrar **`BP_TBTable`** ~50 cm frente al usuario sentado, a la altura de la mesa: su +X apunta **hacia quien
   dibuja**.
5. En la instancia del director: `03 SKETCH > SketchTarget` = el target, `DrawTable` = la mesa. Opcional:
   `01 COLOR > ColorMode` (0 = rueda, **default del CDO**; 1 = 4 colores, como estaba la instancia de NC).
6. Integración con la obra: `SetHandedness(bLeft)` (la etapa previa decide la mano hábil) y el dispatcher
   **`OnStageFinished`** (se dispara al terminar la exhibición del dibujo guardado).

✅ **Nivel de prueba en SC: `/Game/NeuralCanvas/Maps/L_TBTest_SC`** (2026-09-27), réplica exacta de `L_TBTest` de NC,
armado de cero (NO se copió el `.umap` de NC: arrastraba nodos viejos del Level BP con `BP_GameFlowManager`,
`/Game/OSC/BP_OSCRECIEVER`, `GM_TBTest` y un streaming del VRTemplate). Base: duplicado de `Template_Default` con la luz,
atmósfera, niebla, nubes y piso quitados (NC no tiene luces; duplicar `/Engine/Maps/Entry` **no guarda**: "Illegal
reference to private object Model2"). Transforms leídos del nivel de NC: PlayerStart (-315,0,106); `DrawTable`
(-265,0,**180**) Yaw 180; `SketchTarget` (**235,0,80**) Yaw 180 escala **4,89**; `BP_Sky_Sphere` con sus 11 valores de
instancia (colores, `Sun height` −0,139, nubes/estrellas en 0). Director con los overrides que tenía la instancia de NC
respecto del CDO: `ColorMode` 1, `SlotColorA` (los 4 colores), `SwayStrength` 2,739, + `SketchTarget`/`DrawTable`.
GameMode override = `BP_XRGameMode` (el mismo que `Test_Sequencer`; spawnea `BP_VRPawn_SC`, igual que `BP_SoulChargerGameMode`).
✅ **PIE en SC**: spawnea `BP_VRPawn_SC`; el director encuentra `MotionControllerRightAim/LeftGrip/RightGrip` del pawn
(`bReady` true), crea la paleta, empuja target y mesa a la herramienta; **log sin errores ni Accessed None**.
(`bCanDraw` = false en PIE de escritorio es esperado: sin visor las dos manos están en el mismo punto, dentro del radio
de la paleta.) ⬜ **Falta: probar en visor.**

🔴 **2026-09-27 (noche) — EN VISOR NO DIBUJABA: el input propio no llega en SC. Corregido en la copia de SC.**
Beltrán: *"No dibuja"*. Los `IA_TB_*` + `IMC_TB_*` (que reemplazaban a los `IA_Shoot_*` del VRTemplate) **nunca se
habían probado en visor** — lo validado en NC era con `IA_Shoot`. Y en SC ya estaba escrito (`assets-existentes.md` §3,
memoria `input-vr-receta`): **un IA/IMC propio no dispara nunca aunque el contexto quede registrado; el gatillo SOLO llega
por `IA_Shoot_Right/Left` del XRFramework**, que SC entrega por los *Default Mapping Contexts* de `DefaultInput.ini`
(`IMC_Weapon_*`). Descartado con datos antes de cambiar: mismas teclas (`OculusTouch_*_Trigger_Click`), mismo filtro de
input mode (`UseProjectDefaultQuery`), el pawn no limpia mapeos, `IMC_Hands` no usa `Trigger_Click`.
**Arreglo (cirugía de nodos en `BP_TBDirector_NC` de SC, cero IMC tocados):**
- Eventos `IA_TB_Draw_R/L` → **`IA_Shoot_Right/Left`** (`/Game/XRFramework/Input/Actions/`, trigger `Down`: Started al
  apretar, Completed al soltar → trazo continuo).
- Eventos `IA_TB_Pressure_R/L` → **`IA_Hand_IndexCurl_Right/Left`** (Axis1D sobre `Trigger_Axis`, `bConsumeInput` false,
  en `IMC_Hands`) → `PressureFrom(V, FromLeft)` como antes.
- `GateStepTB`: los getters pasan a `IA_Shoot_Left/Right`.
- 🆕 **`TB_PressFrom(FromLeft)` / `TB_ReleaseFrom(FromLeft)`**: con `IA_Shoot` las DOS manos disparan siempre (antes solo se
  instalaba el IMC de la mano que dibuja), así que el gatillo de la mano de la paleta tiene que ignorarse:
  `if not(FromLeft xor bLeftHanded)` → `Tool.Press/Release`. Derecha `false`, izquierda `true`. `TB_Press`/`TB_Release`
  quedan sin uso.
- `InstallInput`/`AddDrawIMC` siguen agregando `IMC_TB_Draw_*`: inofensivo (sus acciones ya no tienen evento).
✅ Compila limpio, pines verificados con `get_node_infos`, PIE sin errores. ⬜ **Falta visor.**
⚠ **La copia de Neural Canvas quedó con `IA_TB_*`** (tampoco probada en visor allá). Para portar: **el gatillo lo da el
proyecto anfitrión** — el director tiene que escuchar el IA de disparo que el host ya entrega (en SC y en el VRTemplate:
`IA_Shoot_*`). Esa es la única pieza del sistema que depende del host.
 A vigilar: (a) convivencia del gatillo con inputs de SC de prioridad 1000
que **sí** consumen (p. ej. `IA_Continue` de Breath) si están activos en el mismo nivel; (b) los sonidos de clic salen de
`/Engine/VREditor/Sounds/` → confirmar que se cocinan al empaquetar el APK; (c) la paleta sigue volteada 180° en su Y
local (parchada, no enderezada).

### 5p - Guardar sostenido 3 s + cierre del sistema + manos del pawn ocultas (2026-09-27, copia de SC)
Pedido de Beltrán: *"mantener apretado el botón de guardar 3 segundos"*, *"la paleta y el controller deben desaparecer.
Animado … Debe bloquear el seguir dibujando"*, *"esconde las manos"*.
- **Paleta**: `TestSave` (disparaba al primer toque, por flanco) se reemplazó en `PickSlot` por **`TestSaveHold`**: mientras la
  punta está en el botón acumula `SaveHold += GetWorldDeltaSeconds`, al salir vuelve a 0; dispara `FireSave` una vez al
  llegar a `SaveHoldTime` (flanco con `bSaveWasIn`). Progreso visible: **`M_TB_Save` ganó el parámetro `Progress`** (neutro
  en 0 = idéntico a antes) que llena el cuadro **desde el centro hacia afuera** (radial a propósito: la paleta se ve volteada
  en la mano y un llenado vertical podía verse al revés). MID `SaveMid` creado en `BuildSaveMid` (BeginPlay, después de
  `BuildSave`); se escribe con el wrapper **`SaveProgress(V)`** (nodo creado con `declaring_class` MID: el DSL elige el
  `SetScalarParameterValue` de MPC — *"Could not connect pin SaveMid to Collection"*).
- **Director**: perillas `03 SKETCH > SaveHoldTime` (3, empujada a la paleta cada cuadro) y `OutroTime` (1,2 s);
  `00 MANO > bHidePawnHands` (true).
  **`OutroStep(DT)`** (al final de `DirectorStep`): arranca cuando `Tool.SketchPhase > 0` (el guardado sí ocurrió; sin
  trazos `SaveSketch` no hace nada y el sistema sigue vivo). En ese cuadro captura las escalas base (`PalS0`, `RHandS0`,
  `LHandS0`, `TipS0` — no se asumen: la versión zurda espeja) y levanta `bSystemDone`. Después encoge paleta, mallas de mando
  y punta con smoothstep en `OutroTime` y al final las oculta (`SetActorHiddenInGame` / `SetVisibility`). Desde el primer
  cuadro: **Tick de la paleta apagado** (ni undo, ni clear, ni otro save) y **`Tool.bCanDraw` = false** (`Press` lo exige →
  no se puede dibujar más). Todo por `select`, sin ramas: antes de terminar escribe el valor actual (no-op).
  **`HandsStep`**: `GetComponentsByClass(GetPlayerPawn, SkeletalMeshComponent)` → `SetVisibility(visible AND NOT bHidePawnHands)`.
  Genérico (no nombra `HandLeft/HandRight`) y con la perilla en false no toca nada. Nota: el pawn de SC tiene su propio
  `HideUnhideHand` (BPI_PawnAnim); no se usó para no depender del host.
- ✅ PIE: manos del pawn ocultas (y visibles con la perilla en false = control negativo), `SaveHoldTime` 3 en la paleta,
  `SaveMid` creado, log limpio. ⬜ **El cierre (OutroStep) no se pudo ejercitar en PIE** (requiere trazos + gatillo): falta visor.
- 🔴 Otra vez la instancia: las perillas nuevas nacieron en **0/false en el director colocado** aunque el CDO tenía 3 / 1,2 /
  true (la instancia se reinstanció antes de setear el CDO). Con `SaveHoldTime` 0 el guardado habría disparado al tocar.
  Corregido en la instancia de `L_TBTest_SC` y guardado.

### 5q - El botón Guardar se selecciona como los pinceles + clic de hover + sonido de carga (2026-09-27, copia de SC)
- **`M_TB_Save`** ganó el mismo WPO que `M_TB_Icon`: `Constant3Vector(1,0,0)` → `Transform` Local→World × **`Lift`** (neutro 0).
- **`BP_TBPalette.SaveHoverStep`** (en `PickSlot` entre `TestSaveHold` y el resto, sin ramas): mientras la punta está en el
  botón, `MidLift(SaveMid, SelectLift)` (el mismo valor que realza al pincel elegido; −0,5 tras el `MapRange` del director),
  y en cada flanco de entrada/salida `ClickCount += 1` → el director reproduce el MISMO clic (`ClickStep`) + háptica.
  Estado de flanco en `bSavePrevIn`.
- **Director, sonido de carga**: `ChargeStep` (al final de `DirectorStep`) → "cargando" = `Palette.SaveHold > 0 AND NOT
  bSystemDone` → `ChargeSet` (flanco, `bCharging`) → `ChargeFlip` → `ChargePlay` (`SpawnSound2D`, **pitch =
  Duración/SaveHoldTime**, acotado 0,5–2: el sonido termina justo al guardar) / `ChargeStop` (`AudioFadeOut` 0,15 s, el
  wrapper que ya existía por la duplicación de `FadeOut`). Perillas `04 AUDIO > ChargeSound` (`VR_shep_scale_up_01`, 2,78 s:
  sube; al guardar suena `HideSound` = `VR_shep_scale_down_02`, que baja) y `ChargeVol` (0,6). Seteadas en CDO **y** en la
  instancia de `L_TBTest_SC` desde el principio.
- ⚠ `Class|SoundBase|GetDuration` se lee como `Components|GeometryCache|GetDuration`: rótulo falso, el `self` es SoundBase.
- ✅ Compila, PIE limpio en reposo (sin carga, sin clics espurios). ⬜ Hover/carga/guardado: visor.

### 5r - Al terminar la etapa no reaparece nada (2026-09-27, copia de SC)
Beltrán: al final *"volvió a aparecer la mesa frente a mí … no debe aparecer nada nuevo"*. Era `TableGoHome` + la rampa de
fundido de 1 s de la fase 0 (pensadas para seguir dibujando). Sin tocar la herramienta: **`TableEndStep`** en el director
(al final de `DirectorStep`) → `SetActorHiddenInGame(DrawTable, bSystemDone AND SketchPhase == 0)`. Durante el viaje al
target (fases 1-5) la mesa sigue visible; al volver a 0 con el sistema cerrado queda oculta. PIE: visible en reposo, log limpio.

### 5s - CONTRATO TOUR (2026-09-29, PREPARADO offline, sin construir) - pedido de Narrativa para `Test_Recorrido`
- Con un actor de tag **`TOUR`** en el nivel (o `08 TOUR > bForceTour`), el director **nace dormido**: no se autoinstala, no
  oculta las manos, sin input, sin Tick. **`TourWake()` / `TourSleep()`**: públicas, sin parámetros, idempotentes (`bAwake`).
  Sin TOUR, `L_TBTest_SC` igual que hoy (`TourBegin` → `TourWakeNow` → `CheckController`).
- `TourSleep`: suelta el trazo, corta carga del Guardar, loop del pincel y háptica; `DisableInput` + `RemoveDrawIMC`; manos
  del pawn devueltas **solo si las ocultó el director** (`bHidePawnHands`); oculta mesa, paleta (y su Tick), mallas de mando y
  punta; Tick del actor y de `TBTool` apagados. `TourWake` ya instalado: `InstallInput` + `MountHands`/`InstallTip` + paleta
  y mesa (con `bSystemDone` no reaparece nada, 5r).
- DSL: `scripts/tb_tour.dsl` (12 funciones nuevas + cirugía de `EventBeginPlay`). Simulación: `scripts/tb_tour_sim.py`
  (encontró que la mesa quedaba oculta al primer despertar). Nombres a confirmar al leer: `LoopComp`, el cast de `HandsStep`.
- ✅ **CONSTRUIDO 2026-09-29** (turno de editor): 3 variables (`bTourMode`, `bAwake`, `08 TOUR > bForceTour` false en CDO e
  instancia), 10 funciones (`TourShow/Palette/Table(On)`, `TourHands`, `TourQuiet`, `TourSleepNow`, `TourWakeNow`, `TourWake`,
  `TourSleep`, `TourBegin`), cirugía de `EventBeginPlay` (CheckController → TourBegin). Al leer el director: `TourQuiet` usa
  `LoopStop`/`ChargeStop` (ya traen IsValid) y `SetHapticsByValue` 0 en las dos manos; `TourShow` remonta con `InstallTip` +
  `ApplyHands` (FixHands elige el mando de la mano hábil). PIE sin TOUR = igual que antes; PIE con `bForceTour` = dormido
  (sin instalar a los 4 s, sin paleta, mesa oculta), log limpio. ⬜ `ke * TourWake/TourSleep` en visor.
- ⚠ `SetHandedness` llamada dormido vuelve a mostrar punta y mando (InstallTip + ApplyHands): llamarla después de `TourWake`.
- **Sonidos fuera de `/Engine/VREditor`** (mismo turno): `VR_click1/2`, `VR_shep_scale_up_01/02`, `VR_shep_scale_down_02`
  copiados a `/Game/NeuralCanvas/Sound/`; reapuntados en el CDO del director, su instancia, el CDO de `BPC_TBTool_NC` y la
  plantilla `TBTool` (la instancia del componente queda en None: el director le empuja los sonidos). `grep VREditor` = 0.

### 5t - En el recorrido el gatillo no dibujaba: el director instala `IMC_Weapon_*` (2026-09-29, copia de SC)
Beltrán, en el APK de `Test_Recorrido`: *"el trigger de dibujo no estaba funcionando"*. **Causa (medida en PIE):** el gatillo
llega por `IA_Shoot_*`, que solo mapean `IMC_Weapon_Right/Left` (el pawn los agrega al poseer). En la etapa 4,
`BP_SeqRig_SC.RigSleep` → `DropInput` hace `RemoveMappingContext(IMC_Weapon_Right/Left)`: Enhanced Input no cuenta
referencias, así que se lleva también el del pawn. Sonda `HasMappingContext` en `InstallInput` al despertar en la etapa 5:
**antes NO/NO, después SI/SI**.
**Arreglo:** `InstallInput` agrega `IMC_Weapon_Right` y `IMC_Weapon_Left` (prioridad 1000, `bIgnoreAllPressedKeysUntilRelease`
false, `bForceImmediately` true). El segundo nodo reusó el `AddMappingContext` que agregaba `IMC_TB_Draw_R` dos veces. No se
quitan en `RemoveDrawIMC`: son del pawn. Con las dos manos disparando, `TB_PressFrom` ya ignora la mano de la paleta.
Regla para cualquier mecánica portable: **el que necesita un IMC del anfitrión lo vuelve a agregar al activarse**, porque otra
mecánica puede haberlo quitado. ⬜ Visor.

### 5u - PALETA 3D (la de Mesh 3D) reemplaza a la de ProceduralMesh (2026-09-29, copia de SC)
Pedido de Beltrán: integrar `BP_DrawPalette_SC` (Ø 40 cm, hormigón, 4 colores + 4 pinceles + undo/redo + slider en arco +
casquete) con toda la interacción de la paleta vieja; **Clear y Save se esconden pero no se borran** (quizás vuelvan en otra
experiencia).
**Arquitectura:** `BP_TBPalette` sigue siendo la paleta que conoce el director (nada del director cambió). Con
**`3D > bArt3D`** (true) su Tick corre **`PaletteTick` → `PickArt`** en vez de `PickSlot`; en BeginPlay **`BuildArt`** spawnea
`BP_DrawPalette_SC`, la cuelga del componente `Mesh` (así `PlacePalette`/`MirrorPalette` del director la siguen moviendo) con
**`ArtOffset` (0,−6,−12) / `ArtRot` (0,−90,−90) / `ArtScale` 1**, y oculta el `Mesh` viejo. `ArtRot` pasa los ejes de la paleta 3D
(+X colores, +Y slider, +Z cara) al marco visto del `Mesh` (+X lejos, +Y izquierda, +Z abajo) → colores a la derecha, slider
abajo, cara al usuario. ⚠ Offset/rotación de **primera aproximación**: se ajustan en visor (perillas del CDO de la paleta).
**`PickArt`** (cada cuadro): `ArtSense` → `ArtColorAct` → `ArtBrushAct` → `ArtSliderAct` → `ArtUndoAct` → `ArtRedoAct` →
`PushSelection` → `ArtPush` → `ClickScan` → `SliderScan` → `ArtTouch`.
- **`ArtSense`**: punta (`Tip`) en el espacio local de la paleta 3D (`ArtP`) → radio `r`, ángulo `a` = atan2(y,x), altura `z`.
  Zona de toque: `z` entre −`PickDown` y `PickUp` (4 / 4 cm). Colores: `r` 5–15,5 y `a` a < `KeyHalfAng` (14°) de −60/−20/20/60;
  pinceles: igual en −120/−160/−200/−240 (`BrushIds` [0,5,3,6] en ese orden); undo: `r` 19–26,5 y `a` a < 13° de **+166**;
  redo: de **−166**; slider: `r` 18,5–25 y `a` en 41–139 → `SliderT = (133 − a)/86` (izquierda fino, derecha grueso).
  **`NearPal`**: `r` < 27 y `z` entre −6 y +10 → `bCanDraw` false (no se EMPIEZA un trazo en la paleta).
  Geometría medida con `get_bounds` (cuña r 5,7–14,8; lateral r 19,6–25; slider r 21,7 entre 46° y 134°).
- **Qué hace cada toque** (igual que la vieja: por proximidad, sin gatillo): color → `PickColor(k)` (color + degradado de
  `SlotColorA/B`); pincel → `Selected` → `PushSelection`; slider → `SetSliderValue` mientras la punta está en el arco;
  undo/redo → `FireUndo`/`FireRedo` **por flanco** (con `bUndoWasIn`/`bRedoWasIn` de siempre) + pulso visual.
- **`ArtPush`** escribe en la paleta 3D: `SelectedColor` = `ColorSel`, `SelectedBrush` = `Selected`, `Thickness` = `Size01`
  y los hover. **`ArtColors`** (al frente de `ApplyColorMode`, o sea después de que el director empuja `SlotColorA`) pinta las
  4 teclas con **los colores reales del dibujo** (`SlotColorA`), no con los de las MI de Mesh.
- Sonidos: `ClickScan`/`SliderScan` sin cambios (clic al cambiar de pincel/color y al entrar a undo/redo; tic por escalón del
  10% del grosor). `ArtTouch` suma el clic al TOCAR una tecla ya elegida (como `PaletteExtras`).
- **Clear y Save**: `TestClear`/`TestSaveHold`/`SaveHoverStep` siguen en `PickSlot` (paleta vieja, `bArt3D` false) y
  `FireClear`/`FireSave` siguen existiendo y se pueden llamar; la paleta 3D **no tiene** esas teclas, así que en modo 3D no se
  llaman. Para volver a mostrarlos: modelar sus teclas y llamar a los `Test*` con su zona.
- **Visibilidad**: la paleta 3D se esconde sola cuando la paleta lógica deja de tickear (TourSleep, fin del sistema).
- **Depuración**: `3D Debug > bDebugTip` + `DebugTipLocal` reemplazan la punta por un punto en el espacio local de la paleta 3D
  (así se probó en PIE sin mandos).
✅ **PIE en `L_TBTest_SC` con punta virtual**: arranque = color 0 y pincel 0 elevados 0,66 cm y brillo 0,5 (base 0,15); teclas
con los 4 `SlotColorA` del director; casquete = TaperedMarker, 1 fila, color 0. Pincel 2 (a 160°) → `Selected` 2,
`Tool.BrushIndex` 3 (Light), tecla 0,96 cm (0,66 + 0,3 de hover), casquete a `T_TB_Light`, `bCanDraw` false, 2 clics. Color 3
(60°) → casquete y `Tool.BrushColor` = `SlotColorA[3]`. Slider a 90° → `Size01` 0,5, disco en 90° escala 1,05; a 50° →
0,965, escala 1,56. Undo (166°) → dispara una vez (`bUndoWasIn`), hover 0,3 cm. Redo (−166°, pulso alargado) → −0,40 cm y
brillo 0,91. Lejos → sin hover, `bCanDraw` true. Log sin errores. ⬜ **Visor**: ergonomía de `ArtOffset/ArtRot`, que la
punta alcance las teclas cómodamente, lectura de los colores saturados sobre el hormigón.

### 5v - Paleta 3D v2 (2026-09-29, primera vuelta de visor): mate, casquete entero, 60 %
Beltrán: *"está todo muy brillante... el cuerpo es más mate... los botones de color brillantísimos, con grano... el círculo
central debe pintarse completo con el tipo de textura... no se notan los íconos... achicar al 60 % pero Undo y Redo del tamaño
que tienen"*. Detalle de materiales y animación en `BP_DrawPalette_SC.md` (v2).
- `BP_TBPalette`: **`ArtScale` 0,6**, `ArtOffset` (0, −3,6, −7,2) (el de antes × 0,6, para que la mano quede en el mismo lugar
  relativo), `PickUp/PickDown` 5 (locales → 3 cm reales), `NoDrawR` 31. `BuildArt` ahora ajusta la zona de deshacer/rehacer a
  su tamaño compensado: `SideRMax` = 19,6 + 5,8·S y `SideHalfAng` = atan2(5·S, 19,6 + 2,7·S) con S = 1/`ArtScale`
  (0,6 → 29,3 y 19°).
✅ PIE con punta virtual: escala 0,6, Undo/Redo a 1,667 relativos (tamaño real 1,0) y desplazados (12,68, ∓3,16, 1,14); lo
elegido brilla 0,28 y lo demás 0; teclas de color = `SlotColorA` × 0,7 (la herramienta sigue con el color completo); pincel
OilPaint → casquete con `BrushBump` = `T_TB_OilPaint_N`, `BumpAmt` 0,4, 4 filas; deshacer detectado en su nueva posición.
Log sin errores. ⬜ Visor.

### 5w - Pose de la paleta 3D con gizmo en el centro del disco + Undo/Redo al 65 % (2026-09-29)
Beltrán: *"¿desde dónde está definido el gizmo? Debiera ser desde el centro del mesh circular... estoy probando rotarla y
está muy difícil"*. Causa: la paleta 3D colgaba del `Mesh` viejo; él giraba `07 PALETA > PaletteRot` en la **instancia** del
director (−52,7 / 236,1 / 0, offset 2 / −4 / 11,9), que rota el `Mesh` alrededor de SU origen, a ~8 cm del centro del disco,
y encima se componía `ArtRot` (0/−90/−90) → cada cambio la hacía orbitar.
**Ahora:** componente **`ArtAnchor`** (ChildActorComponent, clase `BP_DrawPalette_SC`) en `BP_TBPalette`, hijo del root (= el grip
de la mano de la paleta). **Su transform ES la pose de la paleta**: se ve en el viewport del BP y el gizmo gira alrededor del
centro del disco. Arranca en la pose que tenía Beltrán (compuesta y verificada numéricamente): loc (2,19 / 2,76 / 7,51), rot
(0 / 146,12 / −37,31), escala 0,6. **`GripPreview`**: el mando izquierdo (`Controllerleft`, misma transformada que `SM_LHand`
del director) como referencia en el viewport; `bHiddenInGame` + `bIsEditorOnly`.
- `BuildArt` toma la paleta del ChildActor (`GetComponentByClass(ChildActorComponent)` → `GetChildActor` → cast); con
  `bArt3D` false lo destruye (`SetChildActorClass(None)`). Variables `ArtOffset/ArtRot/ArtScale` **borradas**.
- ⚠ `07 PALETA > PaletteOffset/PaletteRot` del director ya NO mueven la paleta 3D (solo el `Mesh` viejo, oculto).
- ⚠ **Zurdo pendiente**: `MirrorPalette` espeja el `Mesh`, no `ArtAnchor`. Para zurdos: loc (x, −y, z), rot (p, −yaw, −roll),
  escala (0,6, −0,6, 0,6) (Unreal invierte el winding solo con escala negativa).
- `BP_DrawPalette_SC.SideCheck` ahora compara escala de MUNDO propia / del padre (`ParentScale`), porque como ChildActor su
  escala relativa es 1. `SideSize` **0,65**.
✅ PIE: Art = el ChildActor, `ArtAnchor` en la pose, `SideScale` 1,083 (= 0,65/0,6), zona de deshacer 25,9 / ±13,5°, teclas con
los colores nuevos de la instancia del director, `GripPreview` oculto en juego, log limpio.
- 🔴 Trampa: `write_graph_dsl` perdió el literal de clase de `GetComponentByClass` (quedó `ActorComponent`); arreglado con
  `set_pin_value`. Leer el grafo después de escribir literales de clase.

### 5x - Mando nuevo de Mesh 3D con gatillo animado (2026-09-29)
Beltrán: *"reemplaza el motion controller por el nuevo... espejarlo para la mano izquierda"* y *"la animación del botón apretado
cuando lo estemos apretando en la experiencia real"*. Assets de Mesh 3D en `/Game/SoulCharger/Mechanics/QuestController/`
(`SM_QuestCtrl_Body/Trigger_R/L_SC`, `MI_QuestCtrl_Body_SC`, `MI_QuestCtrl_Trigger_SC` con `Pressed`), mismo marco y tamaño
que `/Game/NeuralCanvas/Mesh/Controller` (bounds iguales al mm) → transformadas de `SM_RHand/SM_LHand` sin tocar.
- **Todo en runtime** (una instancia ya colocada no recibe bien componentes nuevos, gotcha 396; y los getters de componentes
  nuevos no aparecían en el DSL, gotcha 506): **`InstallCtrl`** (al frente de `FixHands`) pone malla + MI del cuerpo nuevo en
  `SM_RHand`/`SM_LHand` y llama **`MakeTrigR/L`**: si `Z-Mando > TrigR/TrigL` no existe, `AddComponentByClass(StaticMesh)` →
  malla/MI del gatillo, `AttachComponentToComponent` al cuerpo, bisagra R (1,565, 2,432, −0,145) / L (−1,565, 2,432, −0,145),
  escala 1, sin sombra.
- **`TrigStep`** (al final de `DirectorStep`): `GetInputAnalogKeyState(OculusTouch_{Right,Left}_Trigger_Axis)` → **`TrigApply`**
  (T, Body, Axis, V): `SetRelativeRotation(RotatorFromAxisAndAngle(Axis, −14·V))` (eje R (0,976, −0,2177, −0,0083), L (0,976,
  0,2177, 0,0083), verificado por Mesh 3D), `Pressed` = V, visibilidad = la del cuerpo.
- `SetVisibility` de las manos en `FixHands` y `TourShow` ahora propagan a los hijos (dormido el director no tickea).
- Zurdo: `FixHands` ya muestra `SM_LHand` (cuerpo L espejado + su gatillo) en la mano que dibuja.
- `BP_TBPalette.GripPreview` → cuerpo L nuevo.
✅ PIE: cuerpo R nuevo, `TrigR` hijo de `SM_RHand` en la bisagra con su MID, `TrigL` oculto (diestro), log limpio. ⬜ Visor
(giro con el gatillo real).

### 5y - Perillas nuevas del director (2026-09-29)
- **`03 SKETCH > TableColor`** (0,25/0,55/1): `PushTableColor` (al final de `PushTable`) → `TableColor` del material de la mesa.
  Solo en juego (en el editor la mesa muestra el default del material).
- **`07 PALETA > SliderMinSize` / `SliderMaxSize`** (0,5 / 1,5): el rango del slider de grosor. Son FRACCIONES del rango de cada
  pincel en la curva de TB (0 = mínimo real del pincel, `SizeMins`; 1 = máximo del preset; > 1 extrapola). `PushSizeRange` (al
  final de `PushStartSize`) → herramienta `CfgSizeLo/CfgSizeHi` → **`ApplySizeRange`** en `BeginStroke` (antes de
  `StartStroke`) → `SizeLo/SizeHi` del trazo. Antes vivían solo en el CDO de `BP_TBStroke`.
- 🔴 Las tres nacieron en **0 en la instancia** de `L_TBTest_SC` (gotcha "instance editable nace en cero"): puestas a mano y nivel
  guardado.

### 5z - Pose de la paleta 3D por perillas del director, con giro en SUS ejes y ajuste en vivo (2026-09-29/30)
Beltrán: *"las perillas de rotación no funcionan"* → *"¿estás seguro? está demasiado difícil ajustarlo"*.
- `07 PALETA > PaletteOffset / PaletteRot / PaletteScale` (nueva) ahora mueven la paleta 3D (`ArtAnchor` de `BP_TBPalette`)
  con **pivote en el centro del disco**: `PlaceArt` (al final de `PlacePalette` y `MirrorPalette`, y **cada cuadro al final de
  `DirectorStep`**, con firma `Z-Paleta > PlacedSig` para no reescribir si nada cambió). El `Mesh` viejo sigue con los mismos
  valores (oculto, sin efecto). `ArtAnchor` en el viewport de `BP_TBPalette` queda como vista previa: en juego manda el director.
- **`PaletteTilt` / `PaletteBank` / `PaletteSpin`** (grados, nuevas): giros sobre los ejes PROPIOS de la paleta, compuestos
  después de `PaletteRot` como **tres rotadores encadenados**: rot = Base · Tilt · Bank · Spin, o sea
  `Combine(MR(0,0,Spin), Combine(MR(0,Bank,0), Combine(MR(Tilt,0,0), Base)))`. Spin es el más interno, así que siempre gira
  en el plano del disco.
  - 🔴 **Arreglo del 2026-09-30.** La v1 metía los tres en UN solo rotador: `Combine(MakeRotator(Tilt, Bank, Spin), Base)`.
    Dentro de un FRotator el yaw se aplica al final, respecto del padre (R = Yaw·Pitch·Roll).
    - Con `Bank` −50,9, el valor de Beltrán, `Spin` 40 daba yaw 40 alrededor de la vertical del mundo. Beltrán: *"no rota en su propio plano, hace lo mismo que el tilt"*.
    - Medido en PIE después del arreglo: normal del disco (0,776, 0, 0,631) antes y después de `Spin` 40, y el eje X gira 40,00° en el plano.
    - Regla: **perillas de giro independientes = un rotador por perilla, encadenados; nunca las tres en un `MakeRotator`.**
  - Ejes locales de la paleta:
  +X derecha (colores), +Y abajo (slider), +Z hacia el usuario → Tilt = inclinar arriba/abajo (sobre X), Bank = girar los bordes
  izquierdo/derecho (sobre Y), Spin = girar en su plano (sobre Z). `PaletteRot` de Euler desde el grip (que va inclinado en la
  mano) era lo que lo hacía "demasiado difícil".
- **`PaletteSide` / `PaletteUp` / `PaletteNear`** (cm, nuevas 2026-09-30). Beltrán: *"PaletteOffset está rarísimo de mover…
  necesito acercarlo o alejarlo de mí, subirlo o bajarlo de mi mano"*.
  - Por qué `PaletteOffset` se sentía raro: está en el marco del **grip** izquierdo, que va inclinado en la mano, así que sus X/Y/Z no son adelante/arriba para quien mira.
  - Las nuevas mueven la paleta sobre **sus propios ejes, después del giro**: `Side` a lo largo del eje de los colores (+ hacia la mano que dibuja), `Up` hacia arriba de la paleta (+ sube) y `Near` por su normal (+ hacia el usuario).
  - Fórmula: `loc = PaletteOffset + RotateVector((Side, −Up, Near), rot)`. En zurdo, `(Side, +Up, Near)` con el rotador espejado.
  - Medido en PIE: `Up` 3 + `Near` 5 → desplazamiento (4,82, −2,60, 1,99) = R·(0, −3, 5) exacto.
  - `PaletteOffset` queda como base en el marco de la mano (default del CDO, que usa el recorrido); para ajustar a ojo, dejarlo en 0 y usar las tres nuevas.
  - `PlaceArt` se reescribió entero el 2026-09-30: se borraron sus 83 nodos salvo la entrada y se escribió con el DSL. Firma y llamadas, iguales.
- **Ajuste en vivo**: cambiar esas perillas en la instancia del director DURANTE el PIE mueve la paleta al instante (verificado:
  Tilt 20 en PIE → Roll 20 en el mismo segundo). Al parar el PIE se pierden: copiar los valores a la instancia del editor.
- Zurdo: `PlaceArt` espeja posición (−Y), rotación (−yaw, −roll de la base; −Tilt, −Spin del ajuste) y escala Y (−), así que el
  contenido también se espeja.

### 5aa - Trazo INCREMENTAL + U en el material con punta de largo fijo (2026-09-30)
Beltrán: *"si mantengo el trazo más de 3 o 4 segundos empieza a dropear frames"* y *"el inicio del trazo es cada vez más
lejos de mi mano"*. Diagnóstico sobre los grafos reales: workflow `wf_e84a4d4d-1c0`, informe en el scratchpad de la sesión.

**Causa 1, los fps:** `RebuildChunk` rehacía el trazo ENTERO cada cuadro (`FramePass` + `PostFrame` + `EmitPass` + `EmitExtras`, del nudo 0 al N−1).
- Medido en PIE (PC) con el trazo sintético, camino viejo: 2,1 ms con 36 nudos → 13,4 ms con 180 → 25,1 ms con 324. Crece en línea recta.
- A 72 fps entra 1 nudo por cuadro, así que N ≈ 72·t y el codo cae siempre a los mismos segundos.
- Tilt Brush toca solo los últimos 3-4 nudos (`m_FirstChangedControlPoint`).

**Arreglo:** `RebuildChunk` → `RebuildBody`, que elige el camino.
- **Camino nuevo:** si `bIncRebuild` (03 TROZO, default **true**) y es una cinta (`TubeSides < 3`, `ShapeMod == 0`, o sea los 4 pinceles de la paleta y 3 más), va a `RebuildInc` → `MeshPush`.
- **Camino viejo:** los tubos, Petal y Spikes siguen por `FramePass…EmitExtras` → `MeshPush`, intactos.
- `RebuildInc` recalcula solo desde `IncFrom = max(ChunkStart, min(IncN, N) − 4)`:
  - nudos: `IncKnot(I)` calcula todo con nodos puros y le pasa los valores a `IncKnotSet`, que escribe. Así `ComputeSurfaceFrame` y `PressuredSize` se evalúan una vez por nudo y no hay lectura después de escritura.
  - filas: `IncRow` → `IncRowSet`.
  - quads: `IncQuad`.
  - Los arreglos `V_*` se redimensionan con `Resize`, sin `Clear`.
  - Arranque completo si cambió el trozo (`IncChunk`) o `V_Pos` está vacío.
- Misma matemática que `FramePass`/`EmitPass`, nodo por nodo: marco con tangente central, presión suavizada por distancia, límite de crecimiento y clamp xor de auto-intersección, suavizado 0,3/0,4/0,3 y filas crudas en 0 y en N−2..N−1.
- `MeshPush` = el mismo `CreateMeshSection` de antes (sin colisión, sin sRGB).
- `K_U` ya no se escribe en el camino nuevo, y `V_UV.x` = 0: la U la calcula el material (abajo).

**Causa 2, la cabeza "lejos":** con la U estirada a todo el trazo (UVStyle Stretch, fiel a Tilt Brush), la punta de la textura ocupa un porcentaje fijo del LARGO.
- Medido en las PNG de ob-tools: el marcador se afina de 0,94 en u 0,2 a 0,51 en u 0,8 y 0,15 en u 0,95; Óleo, WetPaint y Light cierran en u 0,8-1.
- En un trazo de 60 cm, los últimos ~12 cm junto a la mano quedaban finitos, y crecía con el trazo.

**Arreglo:** función de material nueva **`MF_TB_StrokeU`** (HLSL `scripts/hlsl/StrokeUVS.hlsl`).
- Se calcula en el **vertex shader** (Custom → VertexInterpolator, fp32).
- Va enchufada a los `UVs` de las texturas de `M_TB_Additive`, `M_TB_Masked` y `M_TB_Paint` (las 2 de Paint).
- `u = arco/StrokeLen`, pero la punta [UTip, 1] mide **`TipCm`** cm fijos y el arranque [0, UHead] mide `HeadCm` (0 = proporcional, como Tilt Brush).
- Parámetros (grupo *Stroke U*): `UArc` 0 = neutro (devuelve UV0, así cualquier otro uso del maestro queda igual) · `TipCm` **4** · `HeadCm` 0 · `UTip` 0,8 · `UHead` 0,2.
- Los trazos de hasta ~20 cm quedan **idénticos a Tilt Brush**, y con `TipCm` 0 todo el trazo también (verificado numéricamente).
- `RebuildInc` empuja `StrokeLen` (arco total, en el mismo cuadro, después del rebuild) y `UArc` 1 por `SetScalarParameterValueOnMaterials`.
- La normalización global O(N) (`StretchAccum`/`StretchNorm`) ya no corre en el camino nuevo.

**Instrumentos (debug, apagados):**
- `bProfile` (03 TROZO, en el CDO) cronometra `RebuildChunk` con `GetAccurateRealTime` e imprime `REBUILD inc=… N=… ms_avg=… ms_max=…` cada 36 cuadros.
- **Trazo sintético** en `BPC_TBTool_NC` (09 DEBUG): `bSynth`, `SynthSpeed` 45, `SynthR` 15, `SynthDur` 8, `SynthDelay` 3.
  - `SynthStep` (al frente del Tick) mueve `Tip` en una espiral con **paso fijo de 1/72 s por cuadro**, así la entrada es idéntica entre corridas, y dibuja con presión 0,5.
  - `GateStop` lo respeta (`bSynthOn`).
  - Al terminar, restaura la posición relativa del `Tip` y se apaga solo.
  - Se prende en la instancia del director del EDITOR antes del PIE, nunca en PIE (gotcha 509), y se apaga antes de guardar.

**Medido (PIE en PC, trazo sintético de paso fijo, 577 nudos, `bProfile`):**

| | Tiempo por cuadro |
|---|---|
| Camino viejo | 2,1 ms (36 nudos) → 13,4 (180) → 25,1 (324) → **47 ms (576)** |
| Camino nuevo | **0,47-0,51 ms plano** de 36 a 576 nudos |

- **Equivalencia:** volcado de los arreglos del mismo trazo por los dos caminos (`Saved/ClaudeScripts/tbcheck/`, `dump_stroke.py` + `compare.py`).
  - `K_Pos`, `K_Size`, `K_Right`, `K_Surface`, `K_SmoothPress`, `K_Arc`, `V_Pos`, `V_Normal`, `V_Color` y `V_Tri`: diferencia **0**. `V_UV1`/`V_UV2`: 1e-14.
  - U del material (`TipCm` 0) contra la U vieja: diferencia 0.
  - O sea, la ventana incremental da bit a bit lo mismo que reconstruir todo.
- ⬜ Falta medir en la Quest (APK Development, el mismo sintético) y verlo en el visor.

**Remate al soltar (diagnóstico 3a):** `EndStroke` = `TrimEnd` → `RebuildChunk` → `SwayArm` → `PushLook`.
- Si el último tramo mide < 0,05 cm (el nudo duplicado por `CommitKnot`), `TrimAt(N−1)` lo saca de los 12 arreglos `K_*`, con `K_Pos` al final.
- Antes la última fila caía al `K_Fwd` del mando y dejaba una punta de flecha torcida. Es el mínimo de movimiento de Tilt Brush (5e-4 m).
- Verificado: 577 → 576 nudos, últimos tramos 0,63 cm.

**Orden de tick (diagnóstico 4a):** `BPC_TBTool_NC` hace `SetTickGroup(TG_PostPhysics)` en su `BeginPlay`. `FeedStroke` lee la punta después de que el mando actualizó su pose en ese cuadro (el mando tickea en PrePhysics), así que no hay un cuadro de atraso.

**Pendiente del diagnóstico (no hecho):**
- 3b: mínimo de movimiento en `UpdatePosition` y corte por reversa.
- 3d: presión del nudo 0.
- E: `UpdateMeshSection` con capacidad por bloques en vez de `CreateMeshSection` por cuadro.
- F: `SwayStep` sin Tick en los trazos archivados, `HandsStep`.

### 5ab - Relieve sutil del marcador (2026-09-30)
Beltrán: *"el pincel 1 quedó demasiado plano, pero algo muy sutil, porque me gusta que sea el más plano de todos"*. El pincel 1 es TaperedMarker, la primera tecla.
- En `M_TB_Masked`, entre `textura × color de vértice` (Multiply_0) y el tinte del degradado (Multiply_2):
  - Custom `MarkerRelief`: `C · max(1 + ReliefAmt·R, 0)`, con R = canal R de `ReliefTex` (`T_TB_WetPaint_N`, sampler Normal, rango −1..1). Es el mismo relieve falso que usa `M_TB_Paint`.
  - Se muestrea con la UV del trazo (la salida de `MF_TB_StrokeU`) × (1; 0,25), o sea una sola fila del atlas: vetas finas a lo largo del trazo.
- Detrás de un **static switch `bRelief`** (default false): CelVinyl, que comparte el maestro, no cambia y no paga la textura extra.
- `MI_TB_TaperedMarker`: `bRelief` true y **`ReliefAmt` 0,15**. Es la perilla para subirlo o bajarlo.
- Compila limpio. ⬜ Visto por Beltrán.

### 5ac - ESTELA de previsualización (Tilt Brush) + HALO de energía en la punta (2026-09-30)
**Estela.** Beltrán: *"un pequeño trazo del pincel pegado al puntito; con la mano quieta no se ve; se alarga con la velocidad; no existe mientras dibujamos"*. Es el `RebuildPreviewLine` de Tilt Brush (`open-brush/Assets/Scripts/PointerScript.cs:447-503`; valores del prefab `Pointer_Main`: vida 0,2 s, largo ideal 1 unidad = 10 cm).
- **`BP_TBTrail_NC`**, HIJO de `BP_TBStroke`: hereda la malla, los pinceles (`ApplyPreset`, `PressuredSize/Opacity`, `PickAtlasRow`) y `IncRowSet`/`IncQuad`/`MeshPush`.
  - Constructor propio y liviano, con topología fija de `TrailMax` filas. No usa los nudos del trazo.
  - Se maneja solo: `TrailTick` (en TG_PostPhysics) → `TrailFind` (encuentra la herramienta por `GetOwner` → `GetComponentByClass`) → `TrailRun`.
  - `TrailRun` oculta y vacía mientras se dibuja, mientras la punta está sobre la paleta (`bCanDraw` false) y durante `TrailShowDelay` después de soltar. Si no, llama a `TrailFeed`.
  - `TrailFeed` = `TrailMaybeConfig` (reconfigura si cambia el pincel, el tamaño, el color o el rango) → `TrailPush` (pose de `Tip` + reloj; recorta por vida y por tope) → `TrailBuild` (arco, `lenScale = min(1, largo/TrailIdeal)`, filas con p = min(1,(i−1)/max(1,n−3))·lenScale como TB, `StrokeLen`, `MeshPush`, visible si largo > `TrailMinShow`).
- Perillas en los **defaults de la clase `BP_TBTrail_NC`** (10 ESTELA): `bTrail` true · `TrailLife` 0,2 · `TrailIdeal` 10 cm · `TrailMax` 16 · `TrailShowDelay` 0,25 · `TrailMinShow` 0,3 cm.
- La crea `BPC_TBTool_NC.SpawnTrail` en su `BeginPlay`, con el director como dueño.
- Color = `BrushColor`, el primario; no usa el degradado.
- Verificado en PIE con el sintético "seco" (`bSynthDry`, nuevo en 09 DEBUG: mueve la punta sin dibujar): 12 puntos, 6,9 cm a 45 cm/s, ancho de 0 en la cola a 2,2 cm en la cabeza, visible, 0 trazos creados, 0 errores.
- **Ajuste 1 (Beltrán: *"toma demasiado largo; un poco más delgada que el grosor elegido"*):**
  - Perilla nueva `TrailWidth` 0,7 (10 ESTELA). En `TrailRow` multiplica a `PressuredSize` antes del `0.5 ×`: la cabeza mide el 70 % del grosor elegido.
  - `TrailLife` 0,2 → 0,12 s: la estela queda un 40 % más corta.
  - `TrailIdeal` 10 → 6 cm, para que la rampa de ancho siga igual respecto del largo más corto.
  - Compilado y guardado. ⬜ Visto por Beltrán.

**Halo.** Beltrán: *"el punto desde donde se dibuja debe tener un halo, un poco más cool de que ahí sale energía"*.
- **Material `M_TB_TipHalo`** (Unlit, Additive; HLSL `scripts/hlsl/TipHaloPS.hlsl`): resplandor `pow(dot(N,V))` más fuerte en el centro, anillos que salen hacia afuera y pulso lento.
  - La fase (`WavePh`) y el pulso (`PulseV`) los calcula el BP, así el material no usa Time y se evita el fp16.
  - `Boost` (dibujando): más anillos y más brillo.
- **Director:**
  - `HaloEnsure` crea en runtime una esfera básica colgada de `SM_Tip` (`AddComponentbyClass`, sin colisión ni sombra).
  - `HaloApply` / `HaloStep(DT)`, al final de `DirectorStep`: color = `BrushColor`, visible = `bHalo` y la punta visible, `Boost` suavizado con `FInterpTo` 5. El reloj corre 2,5 veces más rápido al dibujar: la energía "sale".
  - Perillas (06 PUNTA): `bHalo` · `HaloScale` 3 (× la punta) · `HaloIntensity` 0,6 · `HaloBoost` 1 · `HaloWaveSpeed` 0,35 · `HaloPulseSpeed` 0,4.
- Verificado en PIE: creado, colgado de `SM_Tip`, visible, escala 3, material dinámico activo, 0 errores. ⬜ Visto por Beltrán.

### 5ad - Estela y punta ajustadas, TINTA que marca el largo de la etapa (2026-09-30)
- **Estela, ajuste 2.** Beltrán: *"al partir la experiencia la estela no funciona; solo se activa cuando cambio de color o pincel"*.
  - No se reproduce en PIE: con el sintético seco desde el arranque, la estela sale configurada con el marcador, el color y el grosor correctos, y visible.
  - Seguro barato: `TrailClear` ahora pone `TrailSig = −1`. Cada vez que la estela se apaga (al dibujar, sobre la paleta, tras soltar), al reaparecer se reconfigura con lo que tenga la herramienta en ese momento.
  - ⬜ Confirmar en el visor. Si sigue, sospechar del contraste: el color inicial A[0] es casi blanco y la estela del marcador es fina.
- **Punta.** Beltrán: *"el punto frente al control, que siempre esté un poco más brillante que su color, para que se note"*.
  - `UpdateTipColor`: `Tint = BrushColor·TipGain + TipLift`.
  - Perillas del director, 06 PUNTA: `TipGain` 1,5 y `TipLift` 0,06. Puestas en el CDO y en la instancia de `L_TBTest_SC`, porque nacieron en 0.
  - `M_TBHand_NC` es Unlit: el `Tint` es la emisión directa.
- **TINTA.** Beltrán: *"una variable de metros lineales que va disminuyendo a medida que dibujamos; al llegar al final activa save drawing; con eso marcamos el largo de la etapa"*.
  - Director, **10 TINTA**: `bInk` (true) y `InkMeters` (30 m). Internas en Z-Tinta: `InkUsed`, `InkPrevP`, `bInkPrev`, `bInkFired`, `InkShown`.
  - `InkStep` va al final de `DirectorStep` y llama a tres funciones:
    - `InkTrack`: mientras la herramienta dibuja (y dibujaba el cuadro anterior), suma la distancia que recorrió `SM_Tip`, en metros.
    - `InkPushArt`: calcula lo que queda (1 − usado/metros) y, si cambió en más de 0,0005, lo empuja a `Palette.Art.InkSet`.
    - `InkEnd`: al agotarse, y una sola vez, llama a `InkRelease` (suelta el trazo si estaba dibujando) y a `InkSave` (`Tool.SaveSketch`, el MISMO guardado del botón). `bInkFired` = `SketchPhase > 0`: si el guardado no ocurrió (historial vacío), reintenta.
  - Lo demás lo hace el cierre que ya existía (`OutroStep`): `bCanDraw` false, se encoge la paleta, etc.
  - No devuelve tinta al deshacer: es el reloj de la etapa.
  - ✅ PIE con el sintético DIBUJANDO y `InkMeters` 1 (temporal): `InkUsed` 1,0009 → `bInkFired`, `SketchPhase` 4, `bSystemDone`, `bCanDraw` false, `InkLevel` del arte 0. Sin errores nuevos. Se devolvió `InkMeters` 30 y `bSynth` false.
  - ⬜ Visor: si 30 m da un largo de etapa razonable. Referencia: a ~30 cm/s de trazo, 30 m son ~100 s de dibujo efectivo.
- **Gatillo animado del mando, arreglo (2026-09-30).** Beltrán: *"falta la animación del botón del motion controller cada vez que hacemos trigger"*.
  - Causa: `TrigStep` (5x) leía `GetInputAnalogKeyState(OculusTouch_*_Trigger_Axis)`. En Quest eso da 0 siempre (`assets-existentes.md`: las teclas XR solo viajan por Enhanced Input). El gatillo nunca giró.
  - Ahora: `V = max(Input|EnhancedActionValues|IA_TB_Pressure_R/L, la tecla de antes)` → `TrigApply`. Es la misma acción analógica que ya da la presión del pincel.
  - Compila; en PIE, `TrigR/L` existen y no hay errores. ⬜ Visor: el giro con el gatillo real, y si la mano de la paleta también lo mueve (solo si su `IMC_TB_Draw_*` está puesto).
  - 🔴 En el DSL, `CallFunction|<fn propia>` lleva `self` explícito como primer argumento aunque la lectura no lo muestre. Si falta: *"Could not connect pin X to self"*, y la función queda VACÍA hasta reescribirla.
- ✅ **ETAPA CERRADA (2026-09-30).** Beltrán, después de probar en VR Preview: *"Funciona. Todo correcto. Damos por guardado esta etapa."* Incluye la estela, la punta, el gatillo, la tinta y la aparición y salida de la paleta (`BP_DrawPalette_SC.md` v6/v6b). Pendientes que no bloquean: APK/Quest (medir el trazo incremental y la paleta) y la prueba zurda (`MaskFlip`).

### 5ae - CONTRATO DE ETAPA para la Obra + guardas de Tip + PlaceSketch (2026-09-30, noche; turno pedido por Narrativa)
Plan de la noche: `docs/PLAN-NOCHE-2026-09-30.md`. Borrador que se pego: `scripts/tb_contract.dsl`.
- **Guardas de Tip (el ruido de todas las sesiones).** Medido con el director dormido (`bForceTour`, = tag TOUR de la Obra): 903 `Accessed None trying to read property Tip` en 5 s, TODOS desde `BP_TBTrail_NC.TrailPush`. El mensaje nombra `BPC_TBTool_NC` porque `Tip` es variable de esa clase, pero el que lee es la estela: tickea siempre, aunque el director duerma.
  - Arreglo: `TrailTipCheck` / `TrailTipCheck2` escriben `bTipOk` = Tip valido Y visible. `TrailRun` lo exige para alimentar la estela; si no, la limpia.
  - Medido despues: dormido, 0 errores y `bTipOk` false; test normal, `bTipOk` true, la estela suma puntos, 0 errores.
- **Contrato en `BP_TBDirector_NC`** (stubs de Narrativa):
  - `StageIntro`: `bStageDone` false, candado on, `TableT` 0, `IntroTableZero` (TableFade 0 directo en el material de la mesa; la herramienta todavia no la conoce si no se instalo), `TourWake`, `IntroPalDelay`, `IntroStep`.
  - `StageBegin`: candado off, `ContractT0`, `InstallInput`.
  - `StageOutro`: `InkRelease`, `DisableInput`, `RemoveDrawIMC`. Si el cierre no ocurrio, captura las escalas y levanta `bSystemDone`; el `OutroStep` de siempre encoge mandos y punta, la paleta hace su Vanish y la mesa se funde. No borra trazos.
  - `bStageDone` (en `ContractDone`, pegajoso) = `bSystemDone` Y `SketchPhase` 0: tinta agotada o SAVE -> presentacion -> vuelta a 0.
- **Candado** entre Intro y Begin: `DisableInput` del director cada cuadro (`ContractLock`). El gatillo llega por `IMC_Weapon_*` del pawn, que `RemoveDrawIMC` no saca, y `bCanDraw` lo reescriben la paleta y `OutroStep` sin orden garantizado.
- **Entradas con curva** (estandar high end):
  - Mandos y punta crecen con smoothstep en `IntroTime` (0,8 s): `IntroArm` captura la escala cuando `bReady`; `IntroRun` escala.
  - `IntroStep` va en el EventTick DESPUES de `CheckController` (instala en ese mismo cuadro: sin un cuadro a escala llena) y tambien en `StageIntro` (ya instalado).
  - Mesa: la rampa de la fase 0 de `TableStepInner` (herramienta) paso de lineal a smoothstep.
  - Salida forzada: `TableEndStep` escribe `TableFade` = 1 - smooth(OutroT/OutroTime) y oculta recien al final (`TableEndFade`).
- **Paleta en el contrato:** `AppearDelay` = `ContractPaletteDelay` (0,6 s) en runtime, en modo tour (`PalDelayStep`, cada cuadro, e `IntroPalDelay`). Test suelto: los 3 s de la plantilla.
- **Regla 4 de la obra:** EventTick -> `DirectorStep(min(DeltaSeconds, 0,0333))`. Lo heredan la presentacion del dibujo, la mesa, el encogido, el halo y la haptica. Tambien `IntroRun`.
- **`bContractTest`** (11 CONTRATO): `TourBegin` lo trata como TOUR (nace dormido) y `ContractArm` arranca timers: `ContractIntroT` a 1 s -> `StageIntro`; + `ContractBeginDelay` (8 s) -> `StageBegin`; `ContractTestStep` -> `StageOutro` al terminar o por `ContractFirewall` (240 s).
- **`PlaceSketch(Xf, Size)`** (para el cuadro de resultados):
  - `PlaceSketchBounds` (la caja de `SketchSet` con `GrowBounds` de la herramienta) + `PlaceSketchWith`: M = Inv(transform de `SketchTarget`, o identidad) . T(-centro) . S(k) . Xf, con k = Size / lado mayor. Se aplica con `SketchApplyXf` (el mismo camino de `SketchRelocate`: `SetPlacementXf`, el vaiven sigue).
  - Convencion: el +X de `Xf` apunta hacia quien mira (igual que `SketchTarget`).
  - ⬜ Compila; NO ejercitado en PIE (hace falta un dibujo guardado; el sintetico no llego a PIE, ver abajo).
- **Probado en PIE** (valores temporales devueltos):
  - `bContractTest` + cortafuegos de 6 s. Intro a 1 s (despierto, instalado, candado; punta en su escala de reposo 0,006 tras la curva; paleta con 0,6 s). Begin a 9,02 s. Outro por cortafuegos: `bSystemDone`, `bStageDone`, `bOutroCalled`, paleta oculta tras su Vanish, punta encogida y oculta, mesa oculta. **0 errores.**
  - Test normal: igual que antes (sin tour, paleta con 3 s, mesa visible, estela ok, 0 errores).
  - ⚠ `bSynth` en true en el componente de la instancia llego en false al PIE en modo tour (en el editor seguia en true): el camino tinta -> SAVE -> `bStageDone` no se ejercito aca. Si se valido antes (5ad) y `ContractDone` es una linea.
- **Valores de la instancia de `L_TBTest_SC`** (antes -> despues). Solo variables nuevas, que nacen en 0: `ContractBeginDelay` 0 -> 8 · `ContractFirewall` 0 -> 240 · `IntroTime` 0 -> 0,8 · `ContractPaletteDelay` 0 -> 0,6 · `bContractTest` false. Los de Beltran, intactos (`InkMeters` 30, `TipGain` 1,5, `PaletteScale` 0,464...). Nivel guardado: sin esos valores, la Obra los veria en 0.

### 5af - El dibujo del CUADRO DE RESULTADOS aparece y se va con su animacion (2026-09-30, noche; encargo de Narrativa)
Antes, `PlaceSketch` lo colocaba de golpe. Borrador y notas: `scripts/ghost/sketch_fx.dsl`.
- **Lo que se leyo antes de escribir:**
  - `BPC_TBTool_NC.SketchReveal(R)`: `SetReveal(R)` + `SetTaper` en cada trazo del `SketchSet`. `SketchShow` la llama con smoothstep; `SketchWait` toca `ShowSound` con `PlaySound2D` sin `IsValid`.
  - `SketchArchive` -> `ArchiveOne` deja los trazos OCULTOS y fuera de `StrokeHistory`, pero siguen en `SketchSet`. **`PlaceSketch` no los muestra.**
- **En el director:**
  - 5 funciones: `SketchAppear`, `SketchVanish`, `SketchFxApply`, `SketchFxTick`, `SketchVis(On)`.
  - Variables `Z-SketchFx`: `FxT`, `FxDir`, `bFxBusy`. Ninguna es instance-editable: usa las perillas que ya existen (`03 SKETCH > ShowTime/HideTime`, `04 AUDIO > ShowSound/HideSound/SfxVol`).
  - `SketchAppear`: `FxDir` 1 -> `SketchFxApply` (Reveal = smoothstep(FxT), 0 al arrancar) -> `SketchVis(true)` en ESE orden (sin un cuadro dibujado entero) -> `ShowSound` -> timer `SketchFxTick` cada 0,0139 s.
  - `SketchVanish`: lo mismo con `FxDir` -1 (Reveal = 1 - smoothstep) y `HideSound`. Al terminar, `SketchVis(false)`.
  - **Reloj propio (timer), no el Tick:** en la Obra la celda del dibujo duerme durante los resultados, y despertar su Tick correria la logica de la etapa. Paso = `min(GetWorldDeltaSeconds, 0,0333) / tiempo`.
  - **Interrupcion sin salto:** si `SketchVanish` llega a mitad de `SketchAppear` (o al reves), `FxT` pasa a `1 - FxT`. smoothstep es simetrico, asi que el Reveal no cambia en ese cuadro.
- **Uso desde la Obra:** `PlaceSketch(Xf, Size)` -> `SketchAppear()` en `ResultsShow`; `SketchVanish()` en la salida de resultados.
- ✅ Compila (warnings as errors, `null`), log limpio, guardado. ⬜ Sin probar con un dibujo real: con `SketchSet` vacio no hace nada. Queda para el turno de Narrativa en la Obra.

### 5ag - El CORTE POR TIEMPO entra por el camino de la tinta (2026-10-02, Narrativa; diagnóstico de la sesión Modelado 3D)
- Bug del APK 10-01: con el corte de la Obra (`SimCut` → `StageOutro`) no había `SaveSketch`: sin presentación, carga delante del dibujo y resultados vacíos.
- **`TimeUp()`** (director): si `Tool.StrokeHistory` > 0 → `InkUsed = max(InkUsed, InkMeters)` + `InkEnd` (suelta el trazo, `InkSave` → `SaveSketch`, reintenta cada cuadro si estaba dibujando). Sin trazos (o sin herramienta) → `StageOutro` directo. `bStageDone` sale como siempre por `ContractDone` (bSystemDone Y SketchPhase 0).
- **`DbgSynth()`** (director): enciende el trazo sintético de la herramienta (Dur 8, Delay 1, Speed 45, R 15, T 0, bSynth). Solo para pruebas desde la Obra (`DbgDrawSynth`).
- Presentación nominal: Hide 2 + Gap 0,4 + Show 2,5 + Hold 5 + Out 2 ≈ 12 s (medido 12 s en PIE). Con el paso limitado a 0,033 s, en PIE a ~10 fps dura ~3x: no confundir con un cuelgue.
- ⚠ `read_graph_dsl` rotula mal las llamadas propias (`Class|BPBreathStageSC|StageOutro`, `Class|BPObraSC|SketchSpin`): `get_node_infos` da `|StageOutro` con `self` conectado. Es la función propia.
