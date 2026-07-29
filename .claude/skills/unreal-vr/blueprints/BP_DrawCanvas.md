# BP_DrawCanvas — progress tracker

- **refPath**: `/Game/SoulCharger/Stages/Movement/BP_DrawCanvas.BP_DrawCanvas` · **parent**: Actor · **en nivel**: todavía no (lo spawneará `BP_MovementInstructions`)
- **Propósito**: el **motor de geometría** del stage Movement. Único dueño del `ProceduralMeshComponent` y de los datos del dibujo. No sabe nada de mandos ni de input: recibe puntos y los convierte en cinta. Plan completo: [`docs/stages/movement-surrounding.md`](../../../../docs/stages/movement-surrounding.md).
- **Estado**: 🧩 **scaffold compilado y guardado** (2026-07-29). Variables + componente + 4 grafos de función con sus parámetros. **Los cuerpos de los grafos están vacíos** — ese es el próximo paso.

## Componente
- **`StrokeMesh`** — `ProceduralMeshComponent`, agregado al CDO. Pendiente de configurar: `NoCollision`, `bCastDynamicShadow=false`.

## Registro de variables (todas creadas y verificadas en el CDO)

### Buffers de geometría (arrays, se suben al PMC)
- `Vertices` (Vector[]) — 4 vértices por punto (sección rectangular achatada: ancho × espesor).
- `Triangles` (int[]) — 🔴 **constante**: se construye UNA vez en `BuildTriangles` (BeginPlay) y no se vuelve a tocar nunca. `UpdateMeshSection` no acepta triángulos (ver `references/nodes.md`).
- `Normals` (Vector[]) — hacia afuera desde el eje de la cinta (no `dir`), para que el Fresnel del canto funcione.
- `UV0` (Vector2D[]) — U = 0..1 a lo ancho · V = longitud de arco (modo Tile o Stretch, §4.7 del plan).
- `UV1` (Vector2D[]) — X = longitud de arco absoluta (m) · Y = semilla aleatoria por trazo (desfasa el panner).
- `VertexColors` (LinearColor[]) — RGB = color del punto (preset × calma) · A = calma 0..1.

### Estado del trazo activo
- `bDrawing` (bool) — hay un trazo en curso.
- `SectionIndex` (int) — sección del PMC que se está escribiendo. Se incrementa al sellar.
- `PointCount` (int) — puntos ya escritos en la sección activa.
- `Capacity` (int, **default 128**) — puntos por sección. Al agotarse se sella y se abre otra continuando desde el último punto. Chico a propósito: `UpdateMeshSection` sube el buffer entero, así que el costo por actualización queda acotado.
- `ArcLength` (float) — longitud acumulada del trazo (alimenta UV0.V y UV1.X).
- `LastLoc` (Vector) — último punto emitido (base de la decimación).
- `LastDir` (Vector) — última dirección de trazo (base del transporte paralelo y de la decimación angular).
- `FrameUp` (Vector) — 🔴 **el frame transportado**. Es lo que hace que la cara de la cinta siga el trazo sin flips. Se rota en cada punto por el mismo giro que sufrió `LastDir` → `dirNueva`.

## Grafos de función (creados, **cuerpos vacíos** — próximo paso)
| Función | Parámetros | Qué tiene que hacer |
|---|---|---|
| **`BuildTriangles`** | — | Llamar desde `BeginPlay`. Loop `0..Capacity-2`: por cada segmento, 4 quads = **8 triángulos = 24 índices**. Se construye una sola vez para toda la sesión; el patrón de índices es idéntico en cada trazo. |
| **`BeginStroke`** | `BrushId` (int), `StartLoc` (Vector), `ControllerUp` (Vector), `BaseColor` (LinearColor) | Resetea estado (`ArcLength=0`, `PointCount=0`, `bDrawing=true`), siembra `FrameUp` desde `ControllerUp`, llena los `Capacity*4` vértices **colapsados en `StartLoc`** (para que los triángulos no usados tengan área cero), y llama `CreateMeshSection` una sola vez con `Triangles` completo. `bCreateCollision=false`, `bSRGBConversion=false`. |
| **`AddPoint`** | `NewLoc` (Vector), `ControllerUp` (Vector), `Width` (float), `Calm` (float) | El corazón. Decimación (distancia **o** ángulo) → transporte paralelo de `FrameUp` → `side = cross(dir, FrameUp)` → escribir los 4 vértices del punto → **reescribir el taper de los últimos K puntos** (la punta viva) → `UpdateMeshSection`. `bSRGBConversion=false` (⚠ su default es `true`, hay que forzarlo). |
| **`EndStroke`** | — | `bDrawing=false`, congela la rampa de salida en los últimos ~3 cm, `SectionIndex += 1` (sella la sección). |

## Decisiones de arquitectura y por qué (no re-derivar)
- **Pre-alocar + `UpdateMeshSection`**, no `CreateMeshSection` por punto. Razón dura: `UpdateMeshSection` **no tiene pin `Triangles`** → el index buffer no puede crecer. Ver `references/nodes.md`.
- **`Triangles` se construye una sola vez en BeginPlay**, no por trazo: el patrón de índices no depende del contenido del trazo. Ahorra reconstruir 3048 índices en cada apretón de gatillo.
- **Un solo actor lienzo con secciones**, no un actor por trazo (así el dibujo entero se miniaturiza dentro de la ameba con un solo `SetActorScale3D`, y la persistencia queda en un solo lugar).
- **Todo horneado en el vértice** (ancho en geometría, color/calma en vertex color): permite **un material estático por familia de pincel** → sin MID por trazo → los trazos se pueden fusionar (objetivo: ≤4 draw calls).

## Session log
- **2026-07-29** — Creado. Fase 0 + scaffold de la Fase 1 del plan. Verificado en vivo: el plugin de Procedural Mesh está activo, `add_component` acepta el PMC en el CDO, `add_variable` **sí** crea arrays con `container_type:"Array"`, y las firmas de `CreateMeshSection`/`UpdateMeshSection` (volcadas a `references/nodes.md`). Compila limpio y guardado.
- **Próximo paso:** escribir los cuerpos de los 4 grafos (empezar por `BuildTriangles`, que es autocontenido y verificable con un solo PrintString del tamaño del array), y el `BP_BrushTool` mínimo con auto-attach por proximidad copiando el patrón de `BP_BreathSensor_V2` (`AcquireControllers` / `TouchRadius` / `bIsRightHand`).
