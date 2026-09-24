# BPC_DrawTool_NC — el dibujo de Neural Canvas, portable

**Ruta destino (Neural Canvas):** `/Game/Drawing/BP/BPC_DrawTool_NC`
**Ruta destino (Soul Charger, tras migrate):** `/Game/SoulCharger/Stages/Movement/BPC_DrawTool_NC`
**Clase padre:** `ActorComponent`
**Estado:** 🟢 **verificado en PIE** sobre el estado vivo de la instancia (2026-09-24). ⬜ Falta VISOR (el trazo real necesita mandos trackeados y gatillo).
**Origen:** extracción del sistema de dibujo de **Neural Canvas** (`TiltBrush.uproject`), repartido hoy entre `VRPawn` y `BP_Stroke`.

## Purpose
Traer a Soul Charger **el dibujo que ya funciona y se ve bien en Neural Canvas**, en un solo punto de instalación. Convive con [[BPC_DrawTool]] (el nuestro, extraído el 2026-09-04) bajo otro nombre, y **expone la misma API pública** (`Setup` / `Press` / `Release`) para que cambiar uno por otro sea cambiar el componente, no recablear al anfitrión.

🔴 **No reemplaza a `BPC_DrawTool` todavía.** Los dos coexisten hasta compararlos en visor.

## Por qué la réplica anterior no salió — la causa medida (2026-09-24)
Dos cosas, ninguna de ellas la geometría:

1. **`BP_Stroke` se ata al pawn por clase.** En su `BeginPlay` hace `GetActorOfClass("/Game/VRTemplate/Blueprints/VRPawn.VRPawn_C")` y guarda el resultado en la variable `VRPawn`. Con otro pawn eso devuelve `null` y todo lo que cuelga se vuelve `Accessed None` **silencioso** — no rompe con error visible, solo deja de hacer parte del trabajo.
2. **El look es del MATERIAL, no del mesh.** El taper de las puntas lo hace el **shader** vía un MID por trazo (`StrokeLength` y `ShrinkAmount`), con la geometría siempre a ancho pleno.

### 🔴 CORRECCIÓN al repo: la cinta NO usa `M_Brush`
[`references/movement-3d-drawing.md`](../references/movement-3d-drawing.md) §"SEGUNDA AUDITORÍA" atribuye el look fluido de la cinta al `BLEND_Additive` de `M_Brush`. **Es incorrecto.** Leído del `UserConstructionScript` de `BP_Stroke` y de los materiales en vivo (2026-09-24):

| Pieza | Material efectivo | Blend | Shading |
|---|---|---|---|
| **Cinta (Pincel A)** — `StrokeMesh` | MID de `M_Emissive_Inst` → padre `M_Emissive` | **`BLEND_Translucent`** | `MSM_Unlit`, TwoSided (override en la instancia) |
| **Estampado (Pinceles B y C)** — `InstancedPincel2/3` | MID de `M_Spray` | `BLEND_Additive` | `MSM_Unlit`, TwoSided |
| Paleta `BP_PincelSelect` | `M_Brush` | `BLEND_Additive` | `MSM_Unlit` |

`M_Brush` es de la **paleta**. El UCS crea **tres MIDs** y les pasa `SeleccionColor` a `EmissiveColor` — por eso `SeleccionColor` tiene que ir **exposed-on-spawn**: el UCS corre durante el `SpawnActor`.

## Los acoplamientos con el pawn — la lista completa
Medidos nodo a nodo en `BP_Stroke`. Es todo lo que hay que cortar:

| # | Dónde | Qué hace hoy | Cómo se corta |
|---|---|---|---|
| 1 | `EventGraph:BeginPlay` (`K2Node_CallFunction_11` → `K2Node_VariableSet_0`) | `GetActorOfClass(VRPawn_C)` → `SetVRPawn` | El componente **inyecta** la referencia; el nodo se borra |
| 2 | `EventGraph:EventTick` | `SetUbicacionMano(GetWorldTransform(VRPawn.Sphere))` — lee el componente `Sphere` **del pawn, cada frame** | El componente **empuja** la posición de la punta; el Tick de `BP_Stroke` desaparece |
| 3 | `EventGraph` pinceles B y C | `PlayHapticEffect(GetPlayerController 0, …, "Right")` — mano cableada a derecha | Pasa a la config `bRight` del componente |
| 4 | `EventGraph:BeginPlay` | `GetAllActorsOfClassWithTag(TargetPoint, "SceneCapture")` → posiciona el `SceneCaptureComponent2D` | Es el **photo booth**, propio de Neural Canvas. Se guarda con `IsValid` para que degrade sin error donde no exista |
| 5 | `BP_PincelSelect` (la paleta) | Depende de `VRPawn` y llama `CambiarPincel` / `CambiarColor`, que son setters triviales de `Pincel In` / `Color In` | Apuntan al componente |

## Los valores que hacen que se vea así (leídos del CDO, no son los defaults de fábrica)
- `StrokeWidth = 1` — 🔴 es **semi-ancho**: la cinta mide **2 cm** de ancho total.
- `MinDistance = 2` — decimación de 2 cm. **Con el material aditivo no se ve facetado**; bajar la densidad es pelear el problema por el lado equivocado.
- `MinDistanceMesh = 2` — umbral aparte para el estampado ISM de los pinceles B y C.
- `StrokeColor` con **alfa = 11** (el alfa se usa como multiplicador de brillo, no como opacidad).

## Geometría del Pincel A (`PincelA_AddPoint`, verificada en vivo)
```
side = normalize(cross(normalize(new - last), ControllerUp)) * StrokeWidth
Vertices += (new + side), (new - side)        ← 2 vértices por punto, cinta plana sin espesor
Normals  += side, -side                        ← da igual, es Unlit
UVs      += (0, TotalDistance), (1, TotalDistance)
Triangles: (b, b+2, b+1) y (b+1, b+2, b+3)
CreateMeshSection(0, …)                        ← recrea la sección ENTERA en cada punto
MID.StrokeLength  = TotalDistance
MID.ShrinkAmount  = StrokeWidth * -1
```
API actual, ya libre de pawn: `PincelA_StartStroke(StartLocation)` · `PincelA_AddPoint(NewLocation, ControllerUp, OverrideWidth)` · `PincelA_EndStroke()`.

## Arquitectura propuesta
Dos assets, **un solo punto de instalación**:

- **`BPC_DrawTool_NC`** (ActorComponent) — la herramienta. Dueña del estado (pincel activo, color, ancho), del ciclo del trazo, del spawn de `BP_Stroke` y del historial. Empuja la posición de la punta por Tick.
- **`BP_Stroke`** (el de siempre, **refactorizado en su lugar, no duplicado**) — queda como motor puro: geometría + audio + ISM, manejado desde afuera.

🔴 **Refactor en su lugar, sin duplicar.** Duplicar deja decenas de perillas muertas heredadas, que es justo lo que se rechaza al autorar mirando el panel ([[variante-por-duplicado-deja-basura]]).

### API pública (idéntica a [[BPC_DrawTool]] para que sean intercambiables)
- `Setup(Tip, Hand, Right, Width, Color, Mat, HapAmp)`
- `Press()` / `Release()`
- Extra de esta versión: `SetBrush(Index)` · `SetColor(LinearColor)` (los que hoy son `CambiarPincel` / `CambiarColor` en el pawn).
- `bOwnsInput` (bool) — si es `true` el componente trae su propio IMC/IA y se ata solo; si es `false` el anfitrión llama `Press`/`Release`. Decisión de Beltrán, 2026-09-24.

## Riesgos anotados (no resueltos — para medir en device)
- 🔴 **Fill-rate.** Soul Charger se apartó **a propósito** de tres cosas de este sistema: material aditivo, un MID por trazo, un actor por trazo. Las tres se revierten al traerlo igual. En Quest el aditivo es fill-rate y el MID por trazo impide fusionar trazos → draw calls. **Medir en el APK antes de darlo por cerrado.** Ver `references/movement-3d-drawing.md` §"Dónde divergimos a propósito".
- ⚠ `OverrideWidth` es un parámetro de `PincelA_AddPoint` que el cuerpo de la función **no lee** — el ancho sale siempre de la variable `StrokeWidth`. Perilla latente, no un bug activo.
- ⚠ En `StopPincelB` / `StopPincelC`, el `ClearAndInvalidateTimerByHandle` toma el handle de un nodo `SetTimerByEvent` que vive en el evento de arranque. Funciona, pero es frágil: si alguien toca ese nodo, el timer queda huérfano girando a 10 Hz.
- ⚠ El proyecto Neural Canvas **no está bajo control de versiones**. Backup manual previo a esta tanda: `Neural Canvas\_BACKUP_Content_2026-09-24\` (312 archivos, 421,8 MB, 2026-09-24).

## Registro de variables (14, verificadas en el CDO)
**Config:** `TipComp` (SceneComponent — la punta; sin ella el Tick no corre) · `NiagComp` (NiagaraComponent, VFX de punta, opcional) · `bRight` (def `true`, canal háptico) · `DrawWidth` (def `1.0`) · `Colors` (LinearColor[3], **la paleta**: naranja `(1, 0.2636, 0.0324)` · durazno `(1, 0.7074, 0.5156)` · azul `(0.021, 0, 1)`, alfa 1.0) · `bOwnsInput` (def `false`).
**Estado:** `CurrentStroke` (BP_Stroke) · `bIsDrawing` · `StrokeHistory` (BP_Stroke[], la lista de la escultura en curso — la consume el game flow) · `BrushIn` · `ColorIn` · `BrushAtStart` (latch del pincel al iniciar el trazo) · `bCanDraw` (def `true`, era `CompuertaDibujo`) · `TipLocation` (cache, era `UbiucacionEsfera`).

⚠ Trampas de nombre ya pagadas: `BrushAtStart` normaliza a **`SetBrushatStart`** (`a` minúscula) y los bools pierden la `b` inicial (`bCanDraw` → `SetCanDraw`). Por esa última colisión la función pública se llama **`EnableDraw`**, no `SetCanDraw`.

## Estructura de grafos (construida)
- **`Setup(Tip, Niag, Right)`** — escribe las tres referencias de config.
- **`Press()`** — `if (bCanDraw && !bIsDrawing)` → `BrushAtStart = BrushIn` → `SpawnActor(BP_Stroke_C)` en transform identidad, `AlwaysSpawn`, con **`SeleccionColor = Colors[ColorIn]`** → `CurrentStroke` → `bIsDrawing = true` → `StrokeHistory.Add` → `switch BrushAtStart` (0 `PincelA_StartStroke(tip)` · 1 `StartPincelB(tip)` · 2 `StartPincelC(tip)`).
- **`Release()`** — `if (bIsDrawing)` → `bIsDrawing = false` → `switch BrushAtStart` (0 `PincelA_EndStroke` · 1 `StopPincelB` · 2 `StopPincelC`).
- **`EventTick`** — `IsValid(TipComp)` → cachea `TipLocation` → si `bIsDrawing`: empuja `CurrentStroke.UbicacionMano = tip` (lo que alimenta el estampado de B y C) y, si `BrushAtStart == 0`, `PincelA_AddPoint(tip, TipComp.RightVector, 0)`.
- **`SetBrush(Index)` / `SetColor(Index)` / `EnableDraw(Enabled)`** — setters de una línea (los que eran `CambiarPincel` / `CambiarColor` / `CompuertaDibujo`).

🔴 **El `ControllerUp` del trazo es el RIGHT vector de la punta, no el up.** El original hacía `GetRightVector(BreakTransform(GetWorldTransform(MotionControllerRightAim)).Rotation)`; acá es `Transformation|GetRightVector(TipComp)`, que es equivalente con menos nodos.

## 🔴 Cómo se destrabó `BP_Stroke` — con GUARDAS, no borrando
Decisión del 2026-09-24, a mitad de la tanda: borrar el `GetActorOfClass` y el Tick **rompía los pinceles B y C de Neural Canvas** hasta reescribir el `VRPawn`, o sea dejaba el proyecto del usuario roto en el medio. En su lugar, dos guardas:

1. **`EventTick`** envuelto en `IsValid(VRPawn)` (`K2Node_MacroInstance_0`). Con el pawn viejo se comporta **idéntico a hoy**; sin pawn (nivel de prueba, Soul Charger) no corre y gana el `UbicacionMano` que empuja el componente.
2. **`EventBeginPlay`**: el `GetAllActorsOfClassWithTag(TargetPoint, "SceneCapture")` del photo booth pasa por un `IsValidIndex` (`K2Node_CallArrayFunction_0` + `K2Node_IfThenElse_2`) antes del `Array Get(0)` — si no hay TargetPoint no tira error de índice fuera de rango.

El `GetActorOfClass(VRPawn_C)` **se deja**: devolver null no rompe nada por sí solo; lo que rompía era *usar* el null, y eso ahora está guardado. Cambio no destructivo y reversible.

## 📦 El contrato de instalación (una sola llamada)
```
Setup(Tip, Niag, Right, PaletteAnchor)
```
- `Tip` — el SceneComponent desde cuyo `WorldLocation` nace el trazo (en Neural Canvas: `MotionControllerRightAim`).
- `Niag` — NiagaraComponent del VFX de punta; puede ir null.
- `Right` — mano hábil (canal háptico).
- `PaletteAnchor` — dónde se cuelga la paleta física. Si `bSpawnPalette` (def `true`) y el ancla es válida, **el componente spawnea `BP_PincelSelect` y lo attachea solo**.

Con `bOwnsInput = true` el componente además **se trae su propio mapeo**: agrega `InputMapping` (def `IMC_Weapon_Right`, instance-editable) y hostea los eventos de `IA_Shoot_Right` → `Press` / `Release`. Con `false` (el default) el anfitrión rutea el gatillo, que es lo que corresponde en Soul Charger.

🔴 **El `AddMappingContext` va con `Priority=1000` y `bIgnoreAllPressedKeysUntilRelease=False` + `bForceImmediately=True`**, no con los defaults — los defaults suprimen el input y ya nos costó un día (`CLAUDE.md` §7.b). Escrito por `set_pin_value` sobre el pin `Options`.

⚠ `EnsureInput` se llama desde `Setup`, **no desde BeginPlay**: el BeginPlay de un componente corre antes de la posesión y el subsistema de input todavía no existe (`references/vr-pawn.md`).

## 🧪 El banco de pruebas — `L_DrawTest`
**Nivel:** `/Game/Drawing/Maps/L_DrawTest` · **Pawn:** `/Game/Drawing/BP/BP_DrawPawn_Test`

Pedido de Beltrán: un nivel limpio con **solo lo que toca al dibujo**, para validar antes de migrar. Neural Canvas tenía **un único mapa** (`VRTemplateMap`), así que se duplicó y se despojó: fuera `BP_HUD_Carga`, `BP_Sphere`, `BP_OSCRECIEVER`, `BP_Title` y el `NiagaraActor`. Quedan piso, cielo, luz, reflection capture y `PlayerStart`. Los 25 `TargetPoint` se dejaron a propósito: son invisibles y sin lógica, y borrarlos eran 25 llamadas de riesgo por cero beneficio.

`BP_DrawPawn_Test` es un **Pawn mínimo hecho de cero** (no un `VRPawn` despojado): `Camera` + `MC_Right` (`MotionSource=RightAim`) + `MC_Left` (`LeftAim`) + el componente. `AutoPossessPlayer=Player0`. Todo su grafo es **una línea** en `Event Possessed`:
```
Setup(Tip=MC_Right, Niag=null, Right=true, PaletteAnchor=MC_Left)
```
Que sea un pawn de cero es parte de la prueba: demuestra que el componente se instala en **cualquier** pawn, no solo en el de Neural Canvas.

⚠ El nivel duplicado hereda del original un `LogGameMode: Error: Mixing AGameStateBase with AGameMode is not compatible`. No afecta al dibujo; si molesta, se arregla en World Settings.

## ✅ Verificación en PIE (2026-09-24) — sobre el estado VIVO, no la declaración
`Event Possessed` disparó, `Setup` corrió, **cero `Accessed None`**. Leído de las instancias en el mundo PIE:

| Qué | Valor efectivo | Qué prueba |
|---|---|---|
| `DrawTool.TipComp` | `BP_DrawPawn_Test_C_0.MC_Right` | la punta se inyecta bien; la guarda `IsValid` no está tapando un null |
| `DrawTool.PaletteRef` | `BP_PincelSelect_C_0` | 🔴 **el componente spawneó y attacheó la paleta él solo** |
| `DrawTool.TipLocation` | `(-315, 0, 106)` | el **Tick corre** y escribe la posición de la punta |
| `BP_PincelSelect.AsTool` | `BP_DrawPawn_Test_C_0.DrawTool` | 🔴 **la paleta resolvió el componente por `GetComponentByClass`, sin castear a ninguna clase de pawn** — el desacople está probado en runtime |
| `bRight` · `bCanDraw` · `bOwnsInput` · `bSpawnPalette` | true · true · true · true | la config llega |

⬜ **Lo que PIE NO puede probar**: el trazo real. Sin mandos trackeados no hay posición que varíe ni gatillo, así que `Press`/`AddPoint` no se ejercitan. Eso **solo se juzga en visor**.

## 🔴 Pasada de visor 1 (2026-09-24) — "Funciona" + 3 ajustes
Beltrán probó en gafas: **el dibujo anda**. Tres defectos, con sus causas medidas:

### 1. El tamaño de la paleta NO vivía en la paleta
La paleta se veía gigante. La causa: en el `VRPawn` el ancla es `Sphere1`, **con escala 0.05**, hijo de `Controllerleft`, **con escala 1.0875**. O sea que la paleta estaba encogida al **5,4%** por la cadena de padres, no por su propia autoría. Mi ancla (`MC_Left`, escala 1) la mostraba 20× más grande. Sospecha del propio Beltrán, y era correcta: *"quizás yo había ajustado los tamaños a la mala"*.

**Arreglo — el tamaño pasa a ser PERILLA del componente** (pedido explícito suyo). Tres variables instance-editable, aplicadas con `SetActorRelativeTransform` después del attach:
| Perilla | Default | De dónde sale |
|---|---|---|
| `PaletteScale` | `0.054375` | `1.0875 × 0.05` (composición de la cadena original) |
| `PaletteOffset` | `(4.5769, -1.0050, 3.0863)` | composición `Controllerleft ∘ Sphere1` |
| `PaletteRotation` | `(P 69.7722, Y 102.0758, R -74.4188)` | ídem |

⚠ Las composiciones se calcularon **con un script** (`scratchpad/compose.py`), no a mano: componer dos transformadas con rotación mentalmente es exactamente donde se cuela un error que después parece un bug de otra cosa.

### 2. 🔴 Los meshes de los mandos cuelgan de los GRIP, no de los Aim
El pawn de prueba no mostraba mandos. Dos hallazgos:
- Los `XRDeviceVisualizationLeft/Right` del `VRPawn` **están DESACTIVADOS** (`bIsVisualizationActive=false`, `DisplayModelSource=None`). No son los que dibujan los mandos.
- Los mandos son **static meshes propios**: `/Game/Drawing/Mesh/Controller` (derecho) y `/Game/Drawing/Mesh/Controllerleft` (izquierdo).

🔴 **Y la jerarquía importa**: `MotionControllerRightGrip → HandRight → Controller1` y `MotionControllerLeftGrip → Controllerleft → Sphere1 → paleta`. **La punta de dibujo usa `RightAim`, pero los meshes y la paleta cuelgan de los `Grip`.** Mi ancla de paleta estaba en `LeftAim`, el hueso equivocado — por eso los offsets no habrían cerrado nunca.

**Arreglo en `BP_DrawPawn_Test`**: `MC_Left` pasó a `MotionSource=LeftGrip`, se agregó `MC_RightGrip`, y dos StaticMesh (`Controller_R` / `Controller_L`) con las transformadas compuestas.

### 3. Los textos de la paleta
El `Widget` de la paleta usa `/Game/HUD/Mark.Mark_C`, en `Space=World`, `DrawSize 1364×1000`, con `RelativeLocation (0, 123, 131)`. **A escala 1 ese widget queda a 1,2 m del origen de la paleta** — fuera de vista. Al volver a 0.054 debería reaparecer en su sitio. ⚠ Hipótesis alternativa a descartar si sigue sin verse: el log trae `LoadErrors: While trying to load package /Game/HUD/Mark, a dependent package /Engine/EngineFonts/Recoleta-RegularDEMO_Font was not available` — **falta una fuente del engine**, y eso es previo a este trabajo.

## 🔴🔴 Pasada de visor 2 — "ya no se ve nada": LA PLANTILLA DEL COMPONENTE, no el CDO
Tras los arreglos de la pasada 1 **desapareció todo** (mandos y paleta); el dibujo seguía saliendo. Causa raíz, medida sobre la instancia:

**Un componente agregado a un Blueprint por MCP crea un NODO SCS con su PROPIA plantilla (`<Nombre>_GEN_VARIABLE`), y esa plantilla —no el CDO de la clase del componente— es lo que hereda la instancia colocada.** Las variables que se agregan DESPUÉS quedan en la plantilla con su valor cero, aunque el CDO de la clase tenga el default correcto.

Lo que se leyó, que es la prueba:
| Objeto | `PaletteScale` |
|---|---|
| CDO de `BPC_DrawTool_NC` | `0.054375` ✅ |
| Plantilla `BP_DrawPawn_Test_C:DrawTool_GEN_VARIABLE` | `(0,0,0)` ❌ |
| Instancia en el nivel | `(0,0,0)` ❌ |

Con escala 0 la paleta **existe pero es invisible**. Lo mismo con los mandos: sus `StaticMesh` llegaban en `None` y los `MotionSource` con el default `Left` (gotcha 341 del proyecto, en su forma general).

**Receta que sí funciona, en este orden:**
1. Escribir los valores en la **plantilla del componente dentro del pawn** (`..._GEN_VARIABLE`), no solo en el CDO de la clase.
2. Compilar el pawn.
3. 🔴 **Volver a colocar el actor en el nivel.** Una instancia ya colocada **no** recoge cambios posteriores de la plantilla — se verificó: tras compilar seguía en `(0,0,0)`, y solo al re-colocarla tomó `0.054375`.
4. Verificar **en la instancia**, nunca en el CDO.

👉 Corolario para el migrate a Soul Charger: al agregar `BPC_DrawTool_NC` al pawn de la obra, **hay que setear las perillas en la plantilla del componente de ESE pawn**. Los defaults del CDO no alcanzan.

### Bug secundario que PIE atrapó: carrera de arranque de la paleta
La paleta resolvía el componente "tirando" (`GetComponentByClass(GetPlayerPawn 0)`) en su `BeginPlay` — que corre **dentro del `SpawnActor`**, cuando el pawn todavía no sirve como `GetPlayerPawn`. Resultado: `Accessed None trying to read property AsTool`, seis veces.

**Arreglo: invertir la dirección.** `EnsurePalette` ahora **empuja** `(Class|BPPincelSelect|SetAsTool :self _pal :AsTool self)` inmediatamente después del spawn. El "pull" del BeginPlay se deja como camino para una paleta colocada a mano. Verificado: `AsTool` resuelto y **cero `Accessed None` nuevos**.

### Estado verificado en PIE tras los arreglos
| Qué | Valor |
|---|---|
| Paleta: escala | `0.054375` ✅ |
| Paleta: posición/rotación | los offsets compuestos, aplicados relativos al ancla ✅ |
| `BP_PincelSelect.AsTool` | el `DrawTool` del pawn ✅ |
| `Controller_R` / `Controller_L` | mallas y escala `1.0875` en la instancia ✅ |
| `MC_Left` / `MC_RightGrip` | `LeftGrip` / `RightGrip` en la instancia ✅ |

## 🔴 Pasada de visor 3 — "el control derecho está a 30 cm de mi mano"
Mandos y paleta ya aparecían. El mando **izquierdo** estaba bien; el **derecho**, a ~30 cm.

**La diferencia entre los dos era el método**, y eso señala la causa sin ambigüedad:
- Izquierdo: `Controllerleft` cuelga directo de `MotionControllerLeftGrip` → **copié su transformada tal cual** → bien.
- Derecho: `Controller1` cuelga de `HandRight`, que cuelga de `MotionControllerRightGrip` → **compuse las dos transformadas con un script** → mal.

🔴 **Lección: no componer transformadas con rotación a mano (ni por script propio). Replicar la jerarquía y dejar que Unreal haga la cuenta.** La convención de rotación de Unreal (vector-fila) no es la del producto de matrices ingenuo, y el error entra por la rotación del padre que a su vez rota el offset del hijo — sale un desplazamiento grande a partir de offsets chicos.

**Arreglo:** se agregó un `SceneComponent` **`HandRight`** al pawn de prueba, bajo `MC_RightGrip`, con la transformada **exacta** del `HandRight` del `VRPawn`; y `Controller_R` se re-parentó a él con la transformada **exacta** de `Controller1`. Cero composición.

⚠ **Queda pendiente de mirar**: `PaletteOffset`/`PaletteRotation` salieron del **mismo método de composición** (`Controllerleft ∘ Sphere1`), así que pueden tener el mismo sesgo. Beltrán no se quejó de la paleta, pero si aparece corrida, la solución correcta es la misma: replicar la cadena con un `SceneComponent` intermedio y pasar ESE como `PaletteAnchor`, con las perillas en neutro (offset 0, rot 0, escala 1).

## 📦 Autosuficiencia: `BP_HandRig_NC` (2026-09-24, pedido de Beltrán)
Pregunta suya: *"¿esto está en un BP fuera del VR Pawn, para poder migrarlo?"*. **Medido**: `get_dependencies` de `BPC_DrawTool_NC` = `BP_Stroke` · `BP_PincelSelect` · `IA_Shoot_Right` · `IMC_Weapon_Right` + módulos de engine. **Ni `VRPawn` ni ningún pawn.** El dibujo ya era portable; lo que seguía en el pawn era el **rig de manos**.

**`/Game/Drawing/BP/BP_HandRig_NC`** — el rig empacado como actor, con la jerarquía del `VRPawn` **replicada exactamente** (sin componer nada):
```
MC_RightGrip (RightGrip) → HandRight → Controller_R (mesh Controller)  → TipSpot   ← de acá nace el trazo
MC_LeftGrip  (LeftGrip)  → Controller_L (mesh Controllerleft)          → PaletteSpot ← acá se cuelga la paleta
MC_TipAim    (RightAim)  — pose de aim disponible, hoy sin uso
```
🔑 **Con el rig, las perillas de paleta van en NEUTRO** (offset 0, rot 0, escala 1): la transformada correcta ya está horneada en la jerarquía y **la compone Unreal**. Verificado en PIE: la paleta sale con escala mundial `0.054375` y la rotación exacta, sin que nadie calcule nada.

### Palancas nuevas en el componente
| Perilla / API | Default | Para qué |
|---|---|---|
| `bSpawnHandRig` | `false` | spawnea el rig, lo attachea al owner y **toma de él la punta y el ancla de paleta** |
| `bShowControllers` | `true` | si los mandos se ven |
| **`ShowControllers(Show)`** | — | 🔴 **en vivo**: prende/apaga los mandos en cualquier momento. Pedido de Beltrán: *"estos controles aparecerán solo en esta etapa"* |
| `HandRigRef` / `AnchorComp` | — | estado interno |

`EnsureRig` corre dentro de `Setup`, antes de `EnsureInput` y `EnsurePalette`, y **pisa** `TipComp`/`AnchorComp` cuando el rig existe. Por eso `Setup` puede llamarse con `Tip` y `PaletteAnchor` en null.

### 🎯 `TipSpot` — de dónde nace el trazo
Pedido de Beltrán: *"que el dibujo salga de la punta"*, y después *"posicionalo tomando de referencia de dónde nacía antes el trazo"*.

🔴 **No se puede hornear un offset estático hacia el pose de aim.** El trazo nacía de `MotionControllerRightAim`, y la diferencia entre el pose de **aim** y el de **grip** la reporta el runtime de OpenXR: en el editor ambos motion controllers están en el origen del actor. Calcular un offset ahí habría sido inventar un número.

**Solución exacta y sin aritmética:** `TipSpot` cuelga de **`MC_TipAim` (RightAim) con transformada identidad**. Así el trazo nace **exactamente** donde nacía antes. Bonus: el `ControllerUp` de la cinta es `GetRightVector(TipComp)`, y con rotación relativa cero el right vector también es idéntico → la orientación de la cinta no cambia.

⚠ **Si más adelante se quiere mover la punta al extremo visible del modelo**: se arrastra `TipSpot` (sigue siendo un punto movible), pero **en el viewport del editor no se ve alineado con el mesh**, porque el mesh cuelga del grip y en el editor aim y grip coinciden en el origen. Ese ajuste se juzga **en visor**, no en el viewport.

### `BP_DrawPawn_Solo` — la prueba de que alcanza con el componente
Pawn de **cámara + componente, nada más**. Todo su grafo:
```
Event Possessed → Setup(self.DrawTool, Right=true)     // Tip y PaletteAnchor en null
```
✅ **Verificado en PIE**: el rig se spawnea y attachea solo, `TipComp` = `TipSpot` del rig, `AnchorComp` = `PaletteSpot`, la paleta nace a escala `0.054375`, cero `Accessed None` nuevos.

📌 **Receta para Soul Charger** (decisiones de Beltrán 2026-09-24): agregar `BPC_DrawTool_NC` al pawn de la obra con `bSpawnHandRig=true` y `bShowControllers=false`; en la etapa Surrounding llamar `ShowControllers(true)` + `EnableDraw(true)`, y al cerrar los dos en `false`. ⚠ Recordar la regla de la plantilla: **setear las perillas en el `DrawTool_GEN_VARIABLE` de ESE pawn y colocar el actor después**.

⚠ Nota de honestidad sobre la composición: la del **mando derecho** estaba mal (30 cm), pero la de la **paleta** resultó correcta — el rig la reprodujo con los mismos números. O sea que el método falla de forma intermitente, que es la peor. Por eso ahora se replica siempre.

## 🔴🔴🔴 Un MotionController en un actor SIN Owner no trackea jamás
Síntoma en visor: *"los controles se ven abajo y no están attached a mis manos, están quietos"*. Los mandos del rig aparecían **congelados en el origen del rig** (a la altura de los pies del jugador).

**Causa, leída del código del motor** (`Engine/Source/Runtime/HeadMountedDisplay/Private/MotionControllerComponent.cpp`):
```cpp
bHasAuthority = MyOwner->HasLocalNetOwner();
if (bHasAuthority) { ...recién acá consulta la pose XR... }
```
🔴 **`HasLocalNetOwner()` recorre la cadena de `Owner` (la de RED), no la de attachment.** El rig estaba **attacheado** al pawn pero su `Owner` era **null**, así que `bHasAuthority` daba `false` y el componente **nunca consultaba la pose**: se quedaba en su transformada de diseño.

**Arreglo: conectar el pin `Owner` del `SpawnActorFromClass` al owner del componente.** Un pin.

👉 **Regla general para cualquier mecánica portable que spawnee actores con MotionControllers**: *attachear no alcanza; hay que setear el Owner.* Esto aplica igual en Soul Charger.

⚠ **PIE no puede validar este arreglo**: sin visor `CurrentTrackingStatus` es `NotTracked` en cualquier caso. La corrección se apoya en el código del motor, pero **solo el visor la confirma**.

## 🌿 Trazo vivo: vaivén tipo vegetación al soltar (2026-09-24, exploración)
Pedido: *"que una vez que suelte el trazo quede animado como vegetación, con noise como si fuera viento, manteniendo fijo el lugar desde donde nace. Como un alga."*

🔑 **El dato ya estaba en la malla.** `PincelA_AddPoint` escribe `UV.Y = TotalDistance` — la **distancia acumulada desde el nacimiento del trazo**. Es exactamente la máscara que hace falta: 0 en la base, creciente hacia la punta. No hubo que agregar nada a la geometría.

### Dónde se hizo
En **`M_Emissive`** (el material de la cinta), que `get_referencers` confirmó que **solo usa el dibujo** (`M_Emissive_Inst` → `BP_Stroke`) → tocarlo no afecta nada más.

🔴 **El WPO ya estaba ocupado**: el **taper de las puntas es geométrico**, mueve los vértices a lo largo de `VertexNormalWS` (que en esta cinta es la dirección del ancho). Por eso el vaivén **se SUMA** con un `Add`, no reemplaza. Pisarlo habría matado el afinado de las puntas.

### El grafo agregado
```
mask  = saturate(UV.Y / SwaySpan)                    ← base quieta, punta suelta
phase = dot(WorldPos.xy, (1, 0.7)) * SwayScale + Time * SwaySpeed
sway  = SwayDir * sin(phase) * SwayStrength * mask * SwayOn
WPO   = taper + sway
```
El término espacial (`dot(WorldPos.xy, …)`) es lo que da el aire de ruido: cada punto del trazo, y cada trazo en distinto lugar, entra con **fase distinta**. Sin él todo se movería al unísono. Es **un solo seno, sin textura de ruido** — decisión deliberada por el presupuesto de Quest.

| Parámetro | Default | Qué hace |
|---|---|---|
| `SwaySpan` | 25 cm | en cuántos cm pasa de rígido a suelto. Más chico = se mueve casi desde la base |
| `SwayStrength` | 4 cm | amplitud |
| `SwaySpeed` | 1.2 | velocidad |
| `SwayScale` | 0.03 | frecuencia espacial: cuánto difieren las fases entre zonas |
| `SwayDir` | (1, 0.6, 0.15) | dirección del vaivén; Z bajo = se mueve más en horizontal |
| `SwayOn` | 0 | **lo pone el código** |

### El encendido
`PincelA_EndStroke` ahora cierra con `SetScalarParameterValue(DynamicMaterial, "SwayOn", 1.0)`. Mientras se dibuja el trazo está quieto; al soltar, empieza a moverse. Como hay **un MID por trazo**, cada trazo enciende el suyo.

⚠ **El punto fijo es donde el trazo EMPIEZA** (UV.Y = 0), no el extremo más bajo. Si se dibuja de la punta hacia la base, el ancla queda arriba.
⬜ Sin visor. Para afinar: los defaults se tocan en **`M_Emissive_Inst`** y aplican a los trazos **nuevos**.

## Session log
- **2026-09-24** — Auditoría. Proyecto abierto por un **segundo MCP** (`unreal-canvas`, puerto 8001, registrado a nivel usuario). Medido: sin C++ ni plugins propios, `ProceduralMeshComponent` es plugin de engine con `EnabledByDefault=true` → disponible en VR_Test sin tocar nada; ambos proyectos en renderer móvil. Acoplamientos enumerados (tabla de arriba). Diseño escrito. **Sin construir todavía.**

## TODO
- ✅ Mapeo de la capa de dibujo dentro de `VRPawn` (solo **`IA_Shoot_Right`** dibuja, de 18 eventos de input).
- ✅ Construir `BPC_DrawTool_NC` (14 variables, 6 funciones + Tick; compila estricto).
- ✅ Guardas en `BP_Stroke` (acoplamientos 1, 2 y 4 de la tabla neutralizados sin romper Neural Canvas).
- ✅ **Nivel de prueba limpio** `L_DrawTest` + **pawn mínimo** `BP_DrawPawn_Test` (ver sección del banco de pruebas).
- ⬜ 🔴 **VISOR — lo único que falta para cerrar**: que el trazo salga, que los 3 pinceles se sientan bien y que la paleta de la mano izquierda responda al tocarla. Nada de esto se puede juzgar en PIE.
- ⬜ **Verificar `bOwnsInput` en visor.** El componente hostea los eventos de `IA_Shoot_Right` y en PIE no dio error, **pero sin gatillo real no se probó que se ate**. Si no dibuja en visor, la primera sospecha es ésta: poner `bOwnsInput=false` en la instancia y rutear `Press`/`Release` desde el pawn, que es el camino garantizado.
- ✅ **`BP_PincelSelect` desatado del `VRPawn`** (2026-09-24, verificado en PIE). Cómo se hizo, que fue mucho más barato de lo estimado:
  - 🔑 **`retarget_node_class(node, old_class, new_class)` re-resuelve la función POR NOMBRE y preserva las conexiones de datos.** Por eso al componente se le pusieron alias `CambiarPincel(PincelIn)` / `CambiarColor(ColorIn)` con la **firma exacta** de las del `VRPawn` — incluido el **valor de retorno `NewParam`**, que la paleta consume y cuya ausencia hacía fallar el compile con *"In use pin New Param no longer exists"*.
  - `retarget_node_class` **no soporta `K2Node_VariableGet`** → el `GetColorIn` del Tick se borró y se recreó a mano.
  - La variable `AsVRPawn` se borró y se creó `AsTool`; sus 7 getters se recrearon.
  - BeginPlay: `CastToVRPawn(GetPlayerPawn 0)` → **`GetComponentByClass(GetPlayerPawn 0, BPC_DrawTool_NC_C)`**, que es lo que la vuelve agnóstica del pawn.
  - ⚠ `get_dependencies` **siguió listando `VRPawn` después del cambio** (caché del asset registry). No creerle: el test real es correrla en un nivel sin `VRPawn`, y ahí resolvió bien.
- ⬜ ~~Desatar la paleta~~ — *estimación original, conservada como referencia de cuánto se sobreestimó*: se creía ~35 operaciones por estos puntos:
  - La variable `AsVRPawn` está **tipada `VRPawn`** y el MCP **no cambia el tipo de una variable** → hay que `remove_variable` + `add_object_variable AsTool` (tipo `BPC_DrawTool_NC_C`), lo que rompe sus **8 getters** (`K2Node_VariableGet_0, _66..._71` + `VariableSet_0`) y obliga a recrearlos.
  - **6 puntos de llamada** (⚠ el `read_graph_dsl` los muestra ~24 veces porque inlinea los subgrafos compartidos bajo cada evento; los nodos reales son 6): `CambiarPincel` = `K2Node_CallFunction_59/60/61`, `CambiarColor` = `K2Node_CallFunction_64/65/66`.
  - `retarget_node_class(node, old_class, new_class)` **existe** y re-resuelve por nombre → conviene que el componente exponga alias `CambiarPincel`/`CambiarColor`, o retargetear y recablear a mano.
  - BeginPlay: `CastToVRPawn(GetPlayerPawn 0)` → `GetComponentByClass(GetPlayerPawn 0, BPC_DrawTool_NC_C)`. Tick: `Class|VRPawn|GetColorIn` → el `ColorIn` del componente.
- ⬜ Verificar `bOwnsInput`: el nodo `Input|EnhancedActionEvents|IA_Shoot_Right` **se ofrece** en el grafo del componente, pero que se ofrezca no prueba que se ate en runtime. Probar en PIE antes de prometerlo.
- ⬜ Acoplamientos 3 y 5 (háptica cableada a `"Right"`, paleta) y el VFX `SpawnNiag` — segunda pasada.
- ⬜ Solo después: reescribir el `VRPawn` real para que delegue en el componente (y llamar `EnableDraw(false)` en su BeginPlay, porque el componente arranca en `true` y el original arrancaba cerrado).
- ⬜ Migrate a Soul Charger + instalación en el pawn.
- ⬜ Medir fill-rate en device.
