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


## Session log
- **2026-09-25** — Completo y compilando: motor + herramienta + pawn + nivel de prueba.
  Diseno escrito desde el codigo fuente clonado. Motor construido entero,
  compila limpio y guardado. Un crash de Unreal en el medio (Material Editor, null deref tras
  el Undo de un script fallido) costo la primera pasada de variables: **se reconstruyo guardando
  despues de cada tanda**. **Dos** crashes de Unreal, los dos por el Undo de un
  script fallido (gotchas 383-384). 🟢 **Visor OK, mecánica aprobada.** Un bug (secciones sin material) arreglado.

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
- Petal: `m_HardEdges` sin portar (irrelevante sin iluminacion real).
