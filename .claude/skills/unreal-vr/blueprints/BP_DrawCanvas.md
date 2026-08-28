# BP_DrawCanvas — progress tracker

- **refPath**: `/Game/SoulCharger/Stages/Movement/BP_DrawCanvas.BP_DrawCanvas` · **parent**: Actor · **en nivel**: sí, en `L_Test_Movement` en el origen (🔴 **debe quedar en transform IDENTIDAD**, ver restricciones).
- **Propósito**: el **motor de geometría** del stage Movement. Único dueño del `ProceduralMeshComponent` y de los datos del dibujo. No sabe nada de mandos ni de input: recibe puntos y los convierte en cinta. Plan completo: [`docs/stages/movement-surrounding.md`](../../../../docs/stages/movement-surrounding.md).
- **Estado**: 🟡 **Fases 1 y 2 construidas, compila limpio (`warnings_as_errors`) y guardado**. Fase 1 **probada en visor y funcionando**; Fase 2 (taper + continuación de sección) **sin probar todavía**.

## Componente
- **`StrokeMesh`** — `ProceduralMeshComponent` en el CDO. `BodyInstance.CollisionEnabled=NoCollision`, `CastShadow=false`, `bCastDynamicShadow=false`, `bAffectDistanceFieldLighting=false`, `bUseAsyncCooking=false`.

## Material (reescrito 2026-08-03 tras la auditoría del Tilt Brush)
`Materials/M_Brush_Light` — 🔄 **Unlit · `BLEND_Additive` · TwoSided** (antes era Opaco).
- `Emissive = VertexColor.RGB × (Brightness + Fresnel(2.5) × EdgeBoost) × lerp(CalmMin, CalmMax, VertexColor.A)`
- 🔴 **`Opacity` = borde suave procedural a lo ancho de la cinta:** `pow( 1 − |UV0.U×2 − 1| , EdgeFalloff )`. UV0.U va 0→1 de un canto al otro, así que la cinta **se desvanece hacia sus bordes** y nunca se ve el canto del polígono. **Ésta es la razón por la que el trazo dejaba de verse "geométrico"** — copiado del `M_Brush` del proyecto de Tilt Brush, que lo hace con el alfa de una textura (acá procedural, sin textura; se puede cambiar a textura después).
- **Parámetros:** `Brightness` (1.0) · `EdgeBoost` (1.5) · `EdgeFalloff` (0.7 — más alto = más plumeado) · `CalmMin` (0.22) · `CalmMax` (1.0).
- ⚠ **Aditivo = fill-rate.** El §7 del plan lo presupuestaba sólo para el Pincel B; se extendió a los tres con la evidencia del proyecto de referencia. **Medir en APK** (`profiling-quest.md`); si duele, el Pincel A puede volver a Opaco conservando el `EdgeFalloff` en el alfa (con Masked).

### Los 3 pinceles = 1 shader (clave de perf en Quest)
`M_Brush_Light` es la **master**; B y C son **Material Instances** que sólo cambian escalares → **no generan permutación de shader** (verificado en `packaging-pso.md`: escalares/vectores/texturas nunca crean shader nuevo).
| # | Asset | `EdgeFalloff` | `Brightness` | `EdgeBoost` | Look |
|---|---|---|---|---|---|
| A "Luz" | `M_Brush_Light` (master) | 0.7 | 1.0 | 1.5 | cinta sólida de luz con cantos suaves |
| B "Velo" | `MI_Brush_Veil` | 2.8 | 0.55 | 0.4 | plumeado, tenue, humo |
| C "Neón" | `MI_Brush_Neon` | 4.5 | 2.8 | 0.2 | núcleo fino e intenso, filamento |
Se asigna en `OpenSection` con `SetMaterial(StrokeMesh, SectionIndex, …)` — una vez por sección.
🎚️ **Modulación por calma (Fase 3):** el emissive se multiplica por `lerp(CalmMin=0.22, CalmMax=1.0, VertexColor.A)`, y **VertexColor.A = calma del punto** (la escribe `WriteRing`, la calcula `BP_BrushTool.ComputeCalm`). Gesto brusco → tenue pero sobre el piso de 13/255; gesto suave → pleno. Parámetros del material: `Brightness`, `EdgeBoost`, `CalmMin`, `CalmMax`.
🔴 **Sin esto el PMC sale con el gris lit por defecto y el trazo se lee como plástico facetado** (fue el síntoma del primer test en visor). El Fresnel es lo que hace brillar el canto. Comparación con el `M_Brush` **aditivo** del proyecto original: `references/movement-3d-drawing.md`.

## ⏸️ RETOMAR ACÁ (pausa 2026-08-03, sin batería en el visor)
**Todo compila y está guardado. Falta UNA cosa: probar en visor el cambio a cinta plana.**
Lo último que se hizo (sin testear): 🔴 **la cinta pasó de CAJA de 4 vértices a PLANA de 2** (como el proyecto de Tilt Brush) + material aditivo con borde suave + escala de grosores más chica.
- **Qué mirar en el test:** ¿desaparecieron las **esquirlas triangulares** que salían del trazo (se veían sobre todo en zigzags con esquinas agudas)?
- **Si SÍ desaparecieron** → cerrado, seguir con lo que falta del stage (audio/háptico, instrucciones, cierre, persistencia).
- **Si QUEDAN puntas en las esquinas muy agudas** → es el pellizco inherente del ribbon en giros cerrados. Dos cartas sin jugar, en este orden:
  1. **Orientar la cinta con `ControllerUp` en cada punto** en vez del transporte paralelo (`FrameUp`). **Es lo que hace Neural Canvas** (`side = normalize(cross(dir, controllerUp))`, sin frame propagado) y su trazo se veía bien. La cara la controla la muñeca del usuario = predecible; el transporte paralelo la decide la curva y termina de canto en tramos.
  2. **Suavizar el camino con subdivisión spline** (Catmull-Rom) antes de generar geometría, para que no existan esquinas duras. Es refactor del motor — sólo si (1) no alcanza.

## Registro de variables

### Buffers de geometría (se suben al PMC)
- `Vertices` (Vector[]) — 🔄 **2 vértices por punto** (cinta PLANA; antes eran 4 con espesor, cambiado 2026-08-03).
- `Triangles` (int[]) — 🔴 **constante**: se construye UNA vez en `BuildTriangles` (BeginPlay). `UpdateMeshSection` no acepta triángulos.
- `Normals` (Vector[]) — bisectriz de esquina hacia afuera del eje (no `dir`), para que el Fresnel funcione.
- `UV0` (Vector2D[]) — U = 0/1 a lo ancho · V = `Arc / TexScale`.
- `UV1` (Vector2D[]) — X = arco en metros (`Arc*0.01`) · Y = `StrokeSeed`.
- `VertexColors` (LinearColor[]) — RGB = `StrokeColor` · **A = `Calm`**.

### Arrays de puntos — el taper Y el modelo de persistencia
`PtLoc` (Vector[]) · `PtDir` (Vector[]) · `PtUp` (Vector[]) · `PtWidth` (float[]) · `PtCalm` (float[]) · `PtArc` (float[]) — **una entrada por anillo**, mismo índice que `PointCount`. Dimensionados a `Capacity` en `OpenSection`.
🔴 No son sólo para el taper: `PtLoc`/`PtWidth`/`PtCalm` **son el `F_StrokePoint`** de la §6 del plan. La Fase 8 ya tiene sus datos.

### Estado del trazo activo
- `bDrawing` (bool) — hay trazo en curso. ⚠ En DSL se escribe `SetDrawing`/`GetDrawing` (la `b` se cae).
- `SectionIndex` (int) — sección del PMC que se está escribiendo.
- `PointCount` (int) — anillos reales escritos **en la sección activa**.
- `ArcLength` (float) — longitud acumulada del trazo. **No se resetea al cambiar de sección** (UV y taper continuos).
- `LastLoc` / `LastDir` (Vector) — último punto y dirección **emitidos** (base de la decimación).
- `LastTime` (float) — `GetGameTimeInSeconds` del último punto emitido.
- `FrameUp` (Vector) — 🔴 el frame transportado; define la cara de la cinta.
- `StrokeColor` (LinearColor) · `StrokeSeed` (float, random por trazo) · `CurrentBrushId` (int, todavía sin uso).

### Palancas de ajuste (defaults en el CDO)
| Variable | Default | Qué ajusta |
|---|---|---|
| `Capacity` | **128** | Anillos por sección. Al agotarse, `ContinueSection` abre otra sin corte visible. |
| `MinDist` | **1.0** cm | Decimación por distancia. |
| `MaxAngleCos` | **0.9945** | Decimación por ángulo — es **cos(6°)**; se guarda el coseno para no pagar un `Acos` por punto. |
| `MinStep` | **0.3** cm | Piso duro: por debajo no se emite. Evita normalizar un delta ~0. |
| `MinTime` | **0.0** (apagado) | Tope de tasa. Ver "decimación por tiempo" abajo. |
| `TaperIn` / `TaperOut` | **3.0** / **3.0** cm | Largo de las rampas de entrada y salida del taper. |
| `TailRefresh` | **6** | Cuántos anillos de la cola se reescriben por punto. |
| `ThicknessRatio` / `MinThickness` | **0.12** / **0.08** cm | Espesor = `Width × ratio`, con piso. El piso evita el plano de área cero que titila con MSAA. |
| `TexScale` | **20** cm | Cada cuánto tilea la textura en V. |

## Estructura de grafos

```
EventBeginPlay → BuildTriangles

BeginStroke(BrushId, StartLoc, ControllerUp, BaseColor) → OpenSection
AddPoint(NewLoc, ControllerUp, Width, Calm) → StorePoint · RefreshTail(→RefreshRing→WriteRing) · CollapseRing · PushMesh · [ContinueSection]
EndStroke()
```

### `BuildTriangles()` — una vez, en BeginPlay
🔄 **Reescrito 2026-08-03 para cinta PLANA (2 verts).** `Capacity-1` segmentos × 1 quad × 2 triángulos = **6 índices por segmento** (antes 24). El patrón no depende del contenido del trazo.
- Anillo de **2 vértices**: `b=Index*2` → `b=(+side)`, `b+1=(−side)`. El siguiente anillo suma 2.
- Winding: `tri1 = (b, b+3, b+1)` · `tri2 = (b, b+2, b+3)`. El material es TwoSided así que no es crítico.
- **Costo vs la versión de caja:** mitad de vértices, **cuarta parte de triángulos**. Y con aditivo desaparecen las caras laterales/inferior que sumaban luz encima de la principal (eran la causa sospechada de las esquirlas brillantes).

### `OpenSection(P)`
Dimensiona los 5 buffers de vértices a `Capacity*4` y los 6 de puntos a `Capacity`, **colapsa todos los vértices en `P`**, hace `CreateMeshSection` (`bCreateCollision=false`, `bSRGBConversion=false`) y asigna `M_Brush_Light`. Lo llaman `BeginStroke` y `ContinueSection`.

### `BeginStroke(BrushId, StartLoc, ControllerUp, BaseColor)`
Guarda `CurrentBrushId`/`StrokeColor`/`StrokeSeed` (random), resetea `ArcLength=0`, `PointCount=0`, `bDrawing=true`, `LastLoc`, `LastDir=0`, `LastTime`, siembra `FrameUp` desde `MakeRotFromZ(ControllerUp)`, y llama `OpenSection(StartLoc)`.

### `AddPoint(NewLoc, ControllerUp, Width, Calm)` — el corazón
```
si bDrawing:
    delta = NewLoc − LastLoc ;  dist = |delta| ;  now = GetGameTimeInSeconds
    si PointCount == 0:                          ← siembra del trazo
        si dist > MinDist:
            dir     = normalize(delta)
            FrameUp = GetUpVector(MakeRotFromXZ(dir, ControllerUp))
            StorePoint(0, LastLoc, dir, FrameUp, Width, Calm, 0)
            StorePoint(1, NewLoc,  dir, FrameUp, Width, Calm, dist)
            ArcLength = dist ; PointCount = 2 ; LastLoc = NewLoc ; LastTime = now
            RefreshTail() ; CollapseRing(2, NewLoc) ; PushMesh()
    si no:                                        ← punto normal
        dirNew = normalize(delta)
        si dist > MinStep  y  (now − LastTime) >= MinTime
           y  (dist > MinDist  o  dot(dirNew, LastDir) < MaxAngleCos):
            FrameUp    = GetUpVector(MakeRotFromXZ(dirNew, FrameUp))   ← transporte del frame
            ArcLength += dist
            StorePoint(PointCount, NewLoc, dirNew, FrameUp, Width, Calm, ArcLength)
            PointCount += 1 ; LastLoc = NewLoc ; LastTime = now
            RefreshTail() ; CollapseRing(PointCount, NewLoc) ; PushMesh()
            si PointCount >= Capacity:  ContinueSection(NewLoc, dirNew, FrameUp, Width, Calm)
```
🔴 **`LastLoc` sólo se actualiza cuando el punto SÍ se emite** — así el delta acumula entre llamadas descartadas.

### El taper de tres tiempos, resuelto sin tocar el material
`RefreshRing(Index)` recalcula el ancho del anillo desde dónde está la punta **ahora**:
```
fIn  = clamp01( PtArc[i] / TaperIn )                 ← rampa de entrada, no cambia nunca
fOut = clamp01( (ArcLength − PtArc[i]) / TaperOut )  ← rampa de salida, cambia al avanzar
W    = PtWidth[i] × min(fIn, fOut)
```
y llama `WriteRing` con los datos guardados. `RefreshTail()` lo corre sobre los últimos `TailRefresh` anillos.
- **Punta viva:** como `ArcLength` crece con cada punto, los anillos de atrás **engordan solos** al quedar rezagados. Eso es el gesto de Open Brush, sin lógica especial.
- **Salida congelada:** al soltar, `ArcLength` deja de crecer → los últimos anillos quedan finos para siempre. `EndStroke` no hace nada especial.
- `TailRefresh × MinDist` (6 cm) > `TaperOut` (3 cm) → un anillo siempre sale de la ventana de refresco con su `fOut` ya en 1; nunca queda uno a medio engordar.
- Es gratis por el pre-alocado: `UpdateMeshSection` sube el buffer entero igual.

### `ContinueSection(P, Dir, Up, W, Calm)` — al agotar `Capacity`
1. **Infla `ArcLength` en `+TaperOut`, hace `RefreshTail` + `PushMesh`, y lo desinfla.** 🔑 Fuerza `fOut = 1` en la cola de la sección que se va a sellar — **sin esto quedaría un pellizco permanente cada ~1.3 m de trazo**. ⚠ El desinflado se escribe `Set(Get − TaperOut)`, **no** con un getter bindeado antes (ver la trampa de re-evaluación de puros).
2. `SectionIndex += 1` → `OpenSection(P)` → anillo 0 en la misma posición del último de la sección vieja → `PointCount = 1`.
`ArcLength` no se resetea: UV y taper siguen continuos a través del corte.

### `WriteRing(Index, P, Dir, Up, W, Calm, Arc)`
🔄 **Reescrito 2026-08-03 para cinta PLANA.** Escribe los **2 vértices** del anillo en los 5 buffers (base = `Index*2`).
- `side = normalize(cross(Dir, Up))` · `sw = side × (W/2)`.
- `p0 = P + sw` · `p1 = P − sw`. **Sin espesor** → `ThicknessRatio`/`MinThickness` quedaron **sin uso** (se pueden borrar).
- **Normales = `Up`** (la normal real del plano de la cinta). 🔑 Antes eran bisectrices de esquina, un compromiso de la caja; ahora el **Fresnel funciona bien** — de frente casi no aporta, de canto se enciende → conserva el "filamento brillante" que se perdía al sacar el espesor.
- `UV0 = (1|0, Arc/TexScale)` — la **U = 0→1 a lo ancho** es la que alimenta el borde suave del material. `UV1 = (Arc·0.01, StrokeSeed)` · color = `MakeColor(StrokeColor.rgb, Calm)`.

### `StorePoint` / `CollapseRing` / `PushMesh` / `EndStroke`
- **`StorePoint(Index, P, Dir, Up, W, Calm, Arc)`** — escribe los 6 arrays de puntos.
- **`CollapseRing(Index, P)`** — los 4 vértices del anillo, todos en `P` (ancho cero). Guarda contra `Index >= Capacity`.
- **`PushMesh()`** — `UpdateMeshSection` de la sección activa. 🔴 `bSRGBConversion=false` **explícito** (su default es `true`, al revés que en `CreateMeshSection`).
- **`EndStroke()`** — `bDrawing=false`; si `PointCount > 1` sella (`SectionIndex += 1`), si no `ClearMeshSection` (el usuario apretó y soltó sin moverse). `PointCount = 0`.

### Decimación por tiempo — presente pero **apagada** (`MinTime = 0.0`)
El Pincel A original tenía decimación por tiempo (`LastPointTime`). **Se dejó en 0 a propósito:** `MinStep` (0.3 cm) ya cubre el racimo de puntos con la mano casi quieta, y un tope de tasa real castiga los trazos rápidos (a 120 cm/s con `MinDist` 1 cm querés ~120 puntos/s, y a 72 fps ya sólo podés dar 72). Queda como palanca si en el visor aparece agrupamiento.

## Decisiones de arquitectura y por qué (no re-derivar)

- **Pre-alocar + `UpdateMeshSection`**, no `CreateMeshSection` por punto: `UpdateMeshSection` **no tiene pin `Triangles`** → el index buffer no puede crecer.
- **`Triangles` una sola vez en BeginPlay**: el patrón de índices no depende del contenido.
- **Un solo actor lienzo con secciones**, no un actor por trazo (miniaturizar = un `SetActorScale3D`; persistencia en un solo lugar).
- **Todo horneado en el vértice** → un material estático por familia, sin MID por trazo, trazos fusionables. 🔴 El proyecto original hacía el taper con **un MID por trazo** (`ShrinkAmount`); acá va en la geometría justamente para no romper esto.

### 🔴 La cola degenerada — corrige al plan (§4.2 decía "colapsados en StartLoc" y no alcanzaba)
Con el índice buffer fijo, los anillos no escritos todavía siguen teniendo triángulos. Si quedan en `(0,0,0)` o en `StartLoc`, el segmento entre el último anillo real y el primero sin escribir es un **cono visible**. Lo que sí funciona: **un anillo con sus 4 vértices idénticos tiene ancho cero, y cualquier segmento entre dos anillos así es de área cero por lejos que estén.** Entonces `OpenSection` colapsa todos en `P`, y cada `AddPoint` colapsa además el anillo siguiente en el punto nuevo. Coste: 4 `SetArrayElem` extra por punto en vez de recorrer la cola entera.

### 🔴 Transporte de frame: `MakeRotFromXZ`, no `RotateAngleAxis`
`GetUpVector(MakeRotFromXZ(dirNueva, UpAnterior))` — 2 nodos, sin trigonometría. `MakeRotFromXZ` arma la base ortonormal con X = dirección y Z lo más cerca posible del up dado: **es** la ortogonalización de Gram-Schmidt del rotation-minimizing frame, con fallback propio para el caso paralelo. La misma expresión siembra el frame (con el up del mando) y lo transporta (con el frame anterior).

### 🔴 El bug de re-evaluación de puros que hay que no repetir
Un nodo puro se **re-evalúa en cada consumidor**. `(bind _arc (+ (GetArcLength) _dist))` consumido por `SetArcLength` **y** por otro nodo corre la suma dos veces, y la segunda ya lee el valor actualizado → `old + 2·dist`. **Regla:** primero el `Set`, después **leer la variable de nuevo** (getter aparte, sin `bind`). Verificar con `get_node_infos` qué nodo alimenta cada pin — el `read_graph_dsl` no lo muestra.

### 🔴 El lienzo tiene que estar en transform IDENTIDAD
El pincel manda la punta en **coordenadas de mundo** y el PMC interpreta sus vértices en **espacio local**. Si el actor se mueve o rota, el dibujo aparece desplazado. Cuando llegue la miniaturización dentro de la ameba habrá que resolverlo (o el canvas convierte world→local al escribir, o la escala va en un actor padre).

## TODO
- [ ] **Probar la Fase 2 en visor**: que el trazo nazca fino, se ensanche detrás de la punta y muera fino; y que al pasar los 128 puntos no se vea ningún corte ni pellizco.
- [ ] **Fase 3**: `Calm` real (hoy el pincel manda 1.0 fijo) → color y emisivo por vértice.
- [ ] **Fase 4**: `DA_Brush`, los 3 materiales, textura viva (Panner + `Time` + `UV1.Y`), modos Tile/Stretch de `UV0.V`.
- [ ] Roll de muñeca como delta de rotación de `FrameUp` alrededor de `Dir`.
- [ ] **Fase 8**: `SerializeToSave`/`RebuildFromSave` — los arrays `Pt*` ya son los datos.
- [ ] **Fase 9**: fusión de trazos sellados por familia de pincel.

## Valores actuales del CDO (ajustados 2026-08-03)
`MinDist` 0.5 · `MinStep` **0.6** · `MaxAngleCos` **0.985 (10°)** · `TaperIn/Out` 3.0 · `TailRefresh` 20 · `Capacity` 192 · `TexScale` 20.
🔑 **Contraintuitivo, anotado para no repetirlo:** habíamos bajado la decimación a 0.5 cm / **2°** peleando el facetado. **Era el lado equivocado** — el facetado venía del material opaco, no de la densidad. Y con 2° los puntos salían casi encima, sacando direcciones de deltas mínimos = ruido = pellizcos en las esquinas. Neural Canvas usa **2 cm** de decimación y no facetea. Se aflojó a 10° / 0.6 cm.
Grosores de la paleta (en `BP_BrushPalette.PaletteWidths`): **0.8 / 1.8 / 3.5 cm** (la referencia de Neural Canvas es ~2 cm de ancho total).

## Session log
- **2026-08-03** — Sesión grande. (a) 🐛 **Bug del ancho resuelto**: el pin `Width` de `AddPoint` estaba desconectado porque `ComputeWidth` (impura) se usaba inline como argumento → llegaba 0 y **todos los trazos salían del grosor mínimo**; también explicaba parte del "se ve geométrico". Fix: getter puro + `ComputeWidth` borrada. Validado: *"ahora sí, muy perceptible"*. Gotcha destacado en `gotchas.md`. (b) **Auditoría del proyecto de Tilt Brush abierto por MCP** → el look fluido de ellos es el **MATERIAL**, no la geometría (ver `references/movement-3d-drawing.md`). (c) `M_Brush_Light` → **Additive + borde suave procedural** (`pow(1−|U×2−1|, EdgeFalloff)`) + 2 Material Instances (`MI_Brush_Veil`, `MI_Brush_Neon`) = 3 pinceles con **un solo shader**. (d) 🔴 **Cinta de 4 verts → 2 verts (plana)**; decimación aflojada; grosores a escala de referencia. **(c) y (d) sin probar en visor** — ver "RETOMAR ACÁ" arriba.
- **2026-07-29 (tarde)** — Creado. Scaffold: variables, componente, 4 grafos de función vacíos. Verificado y volcado a `references/nodes.md`: el plugin de PMC está activo, `add_variable` **sí** crea arrays, y las firmas de `CreateMeshSection`/`UpdateMeshSection`.
- **2026-07-29 (noche)** — **Fase 1.** Cuerpos de los 7 grafos, 9 palancas nuevas, 3 auxiliares, CDO, `StrokeMesh` sin colisión ni sombras. Se corrigieron dos cosas del plan (cola degenerada, transporte de frame) y el bug de doble suma de `ArcLength`.
- **2026-07-29 (2º test)** — 🎉 **Funciona en visor.** Feedback: *"es bastante feo y geométrico el trazo"*. Causa: **no había material**. Se creó `M_Brush_Light` y se afinó la decimación (`MinDist` 1.5→1.0, ángulo 10°→6°, `MinStep` 0.4→0.3).
- **2026-07-29 (Fase 2)** — Taper de tres tiempos (6 arrays de puntos + `RefreshRing`/`RefreshTail`), continuación de sección (`OpenSection`/`ContinueSection` con el truco de inflar `ArcLength`), decimación por tiempo (apagada). `BeginStroke` y `AddPoint` **recreados** (`remove_function_graph` → `compile` → `add`) para no dejar huérfanos. Compila limpio con `warnings_as_errors`. **Sin probar en visor.**
- ✅ **Hallazgo que destrabó todo:** el DSL **sí** acepta type_ids con paréntesis (`Utilities|Array|Get(acopy)`, `Math|Float|Clamp(Float)`) y tiene `(return expr)` con output params. La nota contraria en `nodes.md` era falsa y quedó corregida.


## 🆕 2026-08-27 — la firma se persiste (F1 del plan de cierre / F5 de Surrounding V2)
Cierra el pendiente "persistencia a disco de la firma". 🔴 **El plan asumía que los arrays `Pt*` eran
el formato, y era falso**: `Pt*` son un buffer **por sección**, del tamaño de `Capacity` (2048), que
`OpenSection` redimensiona y `BeginStroke` resetea. Sólo tienen el trazo en curso. Igual pasa con
`Vertices`. O sea que **no había ningún lugar donde viviera el dibujo entero** — había que crearlo.

**Variables nuevas**: `SavePts` (Vector[], el dibujo acumulado) · `SaveBreaks` (int[], en qué índice
arranca cada trazo) · `SaveN` (contador del diezmado) · `Tmp` (String[] de andamio) ·
🎛️ **`SaveEveryNth`** (3) y **`SaveMaxPoints`** (700), instance-editable.

**Funciones nuevas**
| Función | Qué hace |
|---|---|
| `RecordPoint(Idx, P)` | Si `Idx == 0` (arranque de sección) marca el corte en `SaveBreaks` y guarda el punto sí o sí; si no, guarda **uno de cada `SaveEveryNth`**. Corta al llegar a `SaveMaxPoints`. |
| `SerializeDraw()` | `x,y,z` con 1 decimal, puntos separados por barra, trazos por punto y coma. |
| `ClearSaved()` | Vacía la memoria de la firma. |

**Cirugía**: un solo nodo al final de `StorePoint` (`CallFunction|RecordPoint Index P`). Se eligió
`StorePoint` y no `AddPoint` porque es la función chica por la que pasan **todos** los puntos, con su
índice, y se le puede colgar un nodo al final de la cadena sin recablear nada.

**Números**: con `MinStep` 0.6 cm, 10 m de dibujo son ~1600 puntos → con `SaveEveryNth=3` quedan ~550,
holgado bajo los 700. Cada punto pesa ~18 caracteres → ~10 KB por usuario.

⚠ `ContinueSection` (al pasar de 2048 puntos en un trazo) también llama a `StorePoint 0`, así que
metería un corte de trazo de más. Con 10 m no se alcanza; y aunque pasara, los puntos son contiguos,
así que el dibujo reconstruido se ve igual.

✅ **La práctica no contamina la firma, y está verificado en el grafo**: `BP_Sensor_Soul.DrawStage(5)`
hace `DrawWipe` (que **destruye el actor canvas**) y spawnea uno nuevo, así que `SavePts` nace vacío
en cada arranque del modo dibujo. `ClearSaved()` queda disponible por si alguna vez se reusa el canvas,
pero hoy no hace falta llamarlo.

🔴 **En qué espacio están los puntos guardados**: el PMC exige transform identidad mientras se
dibuja, así que `SavePts` guarda **coordenadas de mundo del momento del trazo**. `ShowSignature()` del
sensor mueve y escala **el mismo actor** después (no lo redibuja), por lo que al momento de guardar los
puntos siguen intactos. ⚠ Para **reconstruir el dibujo de un vecino** (F5) hay que re-centrar y
re-escalar a mano: el `.sav` no trae el encuadre, sólo la forma.

Lo consume [[BP_SoulArchive_SC]] (`TakeCanvas`).


---

## 2026-08-27 — `RebuildFrom(CSV)`: reconstruir la firma de OTRO usuario (F5 del cierre)

El archivo guarda el dibujo como texto (`x,y,z|x,y,z;…`, ver [[BP_SoulArchive_SC]]). Para mostrar el de
un vecino hay que **volver a dibujarlo** en el mismo canvas, en un frame.

```
RebuildFrom(CSV)
  guarda MinTime y SaveMaxPoints  →  MinTime = 0 ,  SaveMaxPoints = 0
  WipeAll()          EndStroke · ClearAllMeshSections · SectionIndex=0 · bDrawing=false
                     + transform del actor a identidad (escala 1, origen)
  StrokeLoop(CSV)    for trazo en split(CSV, ";")  → OneStroke
     OneStroke(S)    EndStroke (cierra el anterior) · PointLoop
     PointLoop(S)    for punto en split(S, "|")    → OnePoint
     OnePoint(P)     split(P, ",") → 3 floats → FeedPt(Vector)
     FeedPt(V)       si bDrawing → AddPoint(V, RebuildUp, RebuildWidth, RebuildCalm)
                     si no      → BeginStroke(CurrentBrushId, V, RebuildUp, StrokeColor, StrokeMat)
  EndStroke() · DrawAudioOff() · restaura MinTime y SaveMaxPoints
```

🔑 **`SaveMaxPoints = 0` durante la reconstrucción** es el candado que impide que `RecordPoint` (que
cuelga de `StorePoint`) **pise la firma propia** con la del vecino: con el tope en 0, el `if` de
`RecordPoint` nunca entra. Cero cambios en `RecordPoint`.
🔑 **`MinTime = 0`** es seguro aunque hoy ya valga 0 en el CDO: `AddPoint` compara
`GetGameTimeInSeconds() - LastTime >= MinTime`, y en una reconstrucción **todos los puntos llegan en el
mismo frame** → con `MinTime > 0` se caerían todos menos los dos primeros.
🔑 **`DrawAudioOff()` al final**: `OpenSection` enciende el loop de dibujo una vez por trazo.

### `R - Reconstruccion` (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `RebuildUp` | (0,0,1) | El "up del mando" que no existe al reconstruir → cinta plana horizontal. |
| `RebuildWidth` | 1,0 | Ancho fijo (el original venía de `Palette.GetCurWidth` por punto). |
| `RebuildCalm` | 0,5 | Calma fija (el original venía de `CalmVal` por punto). |

⚠ Por eso **la firma del vecino no es idéntica a la original**: conserva la *forma* (posición de cada
punto) pero no la modulación de ancho ni de calma. Es una decisión, no un bug — los tres knobs están
para afinar el look.

✅ Verificado en PIE: 12 vecinos seguidos, `DIBUJO: firma del vecino reconstruida, secciones = 3` cada
vez, seguido de `SENSOR: la firma aparece junto al alma`. La reconstrucción cuesta **~55-65 ms** (un
hitch de frame) → ⬜ pendiente medirlo en APK y, si molesta, bajar `SaveMaxPoints` o meter un debounce.


---

## 2026-08-28 — **el paquete**: ameba + dibujo + esferas viajan como una sola pieza

**El pedido de Beltrán** (con un boceto): *"el dibujo está de un tamaño, la ameba en otro, el dibujo no
está anclado a la ameba, aparece suelto muchísimo más lejos. Las esferas del sequencer tampoco están
ancladas, están siempre al medio. […] Todo eso debe ser un solo paquete."*

Su diseño: **ameba con sus anillos al centro, dibujo al costado del mismo tamaño, y la fila de esferas
abajo** — todo anclado y viajando junto.

### 🔴 La causa real del "aparece lejísimos" NO era el ancla
`RebuildFrom` reconstruía el dibujo con las **coordenadas del MUNDO** que trae el CSV (x ≈ 7600), así que
la geometría nacía a **76 metros del pivote del canvas**. El bounding box daba ~4000 cm de extent, la
escala calculada salía **0**, y el trazo aparecía en cualquier parte.
✅ `FeedPt` ahora **captura el primer punto como origen y se lo resta a todos** (`RebOrigin` /
`bRebHasOrigin`, reseteados en `RebuildFrom`). Medido: el extent pasó de miles a **(60, 60, 30)**.

### Las anclas: componentes que se arrastran en el viewport
Dos `SceneComponent` nuevos en el CDO, hijos del root — **Beltrán los diagrama moviéndolos**:

| Componente | Relativo por defecto | Qué cuelga ahí |
|---|---|---|
| `DrawAnchor` | (0, −230, 0) | El dibujo, **centrado por su bounding box** |
| `OrbAnchor` | (0, −115, −260) | La fila de esferas del secuenciador |
| `Card` (ya existía) | (0, 0, −155) | La tarjeta de datos |

### El tamaño ahora se normaliza contra los anillos
```
SoulDrawHalf()  =  DrawSizeRel × (RingRadius / RingSizeRef) × Size     ; = 83,3 × Size con DrawSizeRel 1
SoulDrawFit()   =  SoulDrawHalf / max(|BoxExtent|, 1)
SoulPlaceDrawing():  escala 1 → k → escala k → centrar el bounding box en DrawAnchor → ATTACH a la ameba
```
El **attach** es lo que hace que el dibujo viaje con ella. Medido: `escala real = 0,459`, el centro del
dibujo a 16-39 cm del ancla (la diferencia es pivote↔centro, que es justo lo que corrige el centrado).

### Las esferas
`OneOrb` ya no parte del transform del **retrato** sino de **`OrbWorld`**, una variable Vector que la
ameba escribe con la posición mundial de su `OrbAnchor`. Verificado, coincidencia exacta:
```
OrbAnchor en   (8116.5, 72.5, -122.8)
base esferas   (8116.5, 72.5, -122.8)
```

### 🔴 Tres formas del DSL que devolvieron valores vacíos y costaron una vuelta cada una
1. **`Collision|GetActorBounds` en su forma de un solo valor devuelve `Origin`, no `BoxExtent`.**
   Con `(bind (_o _e) …)` el segundo SÍ se liga (el read lo nombra `_boxextent`), pero cualquier consumidor
   que lo re-inline agarra el primero.
2. **Un `return` de struct `Transform` desde dentro de una rama de `IsValid` vuelve en IDENTIDAD.**
   `OrbFrame` devolvía (0,0,0) con el alma perfectamente válida. Con un `Vector` **también** falló.
   ✅ **La salida que funciona: no devolver — que el dueño del dato lo escriba en una VARIABLE y el otro
   la lea** (los getters de variable entre objetos sí funcionan: es como andan `GetRingsShown`, `GetMesh`).
3. **`Transformation|GetWorldTransform` sobre un componente devuelve identidad**, mientras que
   `GetWorldLocation` sobre el MISMO componente devuelve lo correcto.

💡 Y la lección de método: el print que decía `escala = 0.0` **estaba mal el print**, no la lógica.
Dos vueltas se fueron ahí. **Medir el valor EFECTIVO aplicado** (`GetActorScale3D` del canvas después de
escribirlo) es lo que destrabó el diagnóstico.

### Los otros dos ajustes del mismo pedido
- **El viaje al corazón era demasiado rápido**: `CarrySpeed` **14 → 4** (es la velocidad de un `VInterpTo`;
  a 14 converge en ~0,3 s). ⬜ Pendiente: la preferencia de Beltrán es frenada física (v ∝ √distancia),
  no exponencial — si a 4 todavía no se siente bien, ahí está el camino.
- **El salto entre vecinos**: `Resolve` y `ForceHover` ahora **desvanecen primero** (`FadeDrawOut`),
  guardan el índice en `PendingIdx` y disparan `FocusDelayed` a los **`SwapTime` = 0,35 s**. La
  reconstrucción del trazo (~60 ms de hitch) queda escondida detrás del fundido.
