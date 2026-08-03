# Sistema de dibujo 3D — stage Movement (research + arquitectura)

El stage **Movement** de Soul Charger es un **sistema de dibujo 3D**: el usuario dibuja el **interior de su ameba**, y el dibujo debe **guardarse por usuario** para mostrar las amebas de distintas personas. Requisito duro: geometría **bakeable + persistible**. Inspiración: Tilt Brush / Open Brush (ambos Unity; en Unreal se construye).

> Research de 4 proyectos VR (2026-07-22) + decisión de arquitectura. La memoria local `movement-drawing-system.md` es el resumen; ESTE archivo es la versión completa y versionada (viaja con el repo).

## 🧭 La receta (síntesis de los 4 proyectos)
```
Arquitectura de 3D Draw  (componente de dibujo + manager + decimación por distancia)
  × Geometría ribbon ProceduralMesh  (del TiltBrush propio — BAKEABLE)
  × Color picker HSV  (del Drawing Toolkit)
  × Grab con C_GrabComponent  (de GDXR — tomar herramienta/paleta)
  × Persistencia SaveGame PROPIA  (ninguno de los descargados la trae)
  × Todo unlit emisivo + buenas texturas  (Quest 3 standalone)
```
**Insight clave:** ninguno de los proyectos descargados resuelve los dos requisitos duros juntos (mesh bakeable + guardado por usuario). El motor de geometría bakeable sale del proyecto propio; la persistencia la construimos nosotros. Los descargados aportan piezas de apoyo (arquitectura, color picker, grab), no el core.

## Decisión: Procedural Mesh, NO Niagara/partículas
Niagara y los ParticleSystems generan geometría **efímera en GPU** que no se puede extraer ni serializar → no se puede bakear ni guardar. Con **ProceduralMesh** (o RealtimeMeshComponent) sos **dueño de los vértices** → serializás y reconstruís. Confirmado por experiencia del usuario ("lo que mejor funcionaba era el procedural"). Nota de bake: `CopyMeshToStaticMesh` (Geometry Script) es **editor-only**; en runtime se **serializan los datos** (arrays de puntos o vértices) y se reconstruye el mesh al cargar. `RealtimeMeshComponent` > `ProceduralMeshComponent` en perf.

---

## 🎯 Algoritmo de referencia — ribbon plano incremental (`PincelA_AddPoint`)
Del TiltBrush propio del usuario (`/Game/Drawing/BP/BP_Stroke` en el proyecto "Neural Canvas"). **Rearmar limpio** en Soul Charger (NO migrar el .uasset — arrastra todo el VRTemplate).

**Estado:** arrays `Points`, `Vertices`, `Triangles`, `Normals`, `UVs`/`UV_Array` (buffers del ProceduralMesh) + `TotalDistance`, `LastLocation`, `LastControllerUp`, `LastDirection`, `IsDrawing`, `StrokeWidth`, `MinDistance`.

**`StartStroke(startLoc)`:** limpia arrays, `IsDrawing=true`, `AddPoint(startLoc)`, play + fadeIn audio del pincel.

**`AddPoint(newLoc, controllerUp, overrideWidth)`** — el corazón:
1. `dir = normalize(newLoc − lastPoint)`.
2. `side = normalize(cross(dir, controllerUp)) * StrokeWidth` → la cinta se orienta con el **up del mando** (pinceles planos tipo Tilt Brush).
3. **Decimación:** si `distance(newLoc, lastPoint) < MinDistance` → no agrega punto.
4. Agrega **2 vértices**: `newLoc + side` y `newLoc − side`.
5. Agrega **2 normales** (dir, y la invertida `*-1` para doble cara).
6. Agrega **2 UVs**: U=0 y U=1 (ancho), **V = TotalDistance** → textura fluye a lo largo del trazo (clave para pinceles texturados).
7. `TotalDistance += longitud del segmento`.
8. Cose **triángulos** con el par de vértices anterior (2 tris por quad).
9. `CreateMeshSection(StrokeMesh, 0, Vertices, Triangles, Normals, UVs)` incremental.
10. Material dinámico: `SetScalarParameterValue("StrokeLength", TotalDistance)` y `("ShrinkAmount", -StrokeWidth)` → revelado + taper.
11. Actualiza `LastControllerUp / LastDirection / LastLocation`.

**`EndStroke()`:** `IsDrawing=false`, fadeOut + stop audio.

**Driver:** el pawn llama `AddPoint` cada tick mientras el trigger está apretado. El punto de dibujo = una **"Sphere"** en el pawn (la punta del pincel). El pawn spawnea **un stroke por pincel** y le pasa el **color al spawnear**.

**Optimizaciones sobre el original:** `UpdateMeshSection` en vez de `CreateMeshSection` completo por punto; evaluar RealtimeMeshComponent; materiales **unlit emisivos** para Quest; **buenas texturas** (el UV-a-lo-largo ya lo soporta); merge de trazos al finalizar; el material dinámico (StrokeLength/ShrinkAmount) rehacerlo unlit.

## Segunda familia (opcional) — ISM stamping
Timer 0.1s + gate `MinDistanceMesh` → `AddInstance` en un **InstancedStaticMesh** con rotación/escala random. Ideal para pinceles de **confeti/partícula/estrellas**; ISM = 1 draw call; las transforms también se serializan.

## Extras del proyecto propio
- **Audio + háptico por pincel** mientras dibujás (play/fadeIn al empezar, fadeOut/stop al soltar; háptico por punto).
- **`SceneCapture2D`** que fotografía el dibujo (en un TargetPoint "SceneCapture", ShowOnlyActor = el stroke) → **thumbnails para mostrar las amebas de distintos usuarios**.

---

## ⭐ Color picker (rueda HSV) — del Drawing Toolkit
Patrón para elegir color apuntando. Mecánica (`BP_BrushSetting`):
- Rueda de color **circular** (widget/quad con textura de color wheel). Se apunta con el mando → la **colisión da UV (X,Y) ∈ [0,1]** (`FindCollisionUV`, requiere "Support UV From Hit Results" en Project Settings).
- `ClampX = map(X, 0..1, -1..1)`, `ClampY = map(Y, 0..1, -1..1)` (coords de disco centrado).
- **Hue = Atan2(ClampY, ClampX)** (→ 0-360). **Saturación = length(ClampX, ClampY)** (0..1). **Value/brillo = slider aparte**.
- **Color = `HSVtoRGB(Hue, Sat, Value)`** → param vector "Brush Color" del material + preview UI. Un **"DotPoint"** se mueve a la posición apuntada (feedback).
- Bonus: sliders Size/Opacity/Rotation (`MapRangeClamped`) + selector de forma de punta (cicla texturas vía param "BrushTipShape").
- La matemática es idéntica en 5.8. En VR: rueda = widget/quad world-space; apuntar = laser del mando o tocar con la otra mano si la paleta va en la muñeca.

## Persistencia (la construimos nosotros — ninguno la trae)
Fuente de verdad = **serializar los datos del trazo** (`{brushId, puntos[], anchos[], color}` por stroke) a un `USaveGame` (o JSON/binario). Compacto, determinístico, compartible entre usuarios. Al cargar una ameba → reconstruir el mesh desde los datos. "Bake" en runtime = mergear trazos en una malla + guardar los datos. Para thumbnails, el `SceneCapture2D`.

---

## Comparación de los 4 proyectos revisados (2026-07-22)
⚠ Vienen de versiones viejas → interesa la **lógica/elementos y cómo se harían en 5.8**, no copiar nodos.

| Proyecto | Aporta | Veredicto |
|---|---|---|
| **1. TiltBrush propio** (Neural Canvas) | 🎯 Ribbon ProceduralMesh (`PincelA_AddPoint`, bakeable) + ISM stamping + audio/háptico + SceneCapture | **El motor de geometría.** Rearmar limpio. |
| **2. Drawing Toolkit** | 🎨 Color picker HSV + brush-settings UI | Pintura **2D en panel** (render target) — no sirve el core; rescatamos el picker. La API `BeginDrawCanvasToRenderTarget`/`DrawMaterial` sigue en 5.8 (por si pintamos una superficie plana). |
| **3. 3D Draw** | 🏗️ Arquitectura: **componente** `BP_DrawComp` + `BP_DrawingsManager` + decimación (`DidCursorExceedDistanceThreshold`) + multiplayer + 6 modelos de herramienta | Mejor estructura, pero pinceles = **ParticleSystems (Cascade)** → efímero, no bakeable; **sin SaveGame**. Tomar la estructura, no el render. |
| **4. GDXR Ultimate** | 🤚 **`C_GrabComponent`** (grab por componente + `GrabType` Free/Snap/Custom) + botones/sliders/palancas/válvula/joystick/cajón + CardReader+KeyCard + menú world-space | Sin dibujo; grab moderno (Enhanced Input, UE5) para **tomar la herramienta/paleta/props**. Integrar el patrón al XR pawn propio (ver `vr-pawn`), no reemplazar el pawn. Útil para interacción GENERAL, no solo Movement. |

## Plan MVP (cuando encaremos Movement)
1. UN `BP_Stroke` limpio con el ribbon ProcMesh (Pincel A) + serialización de arrays a SaveGame por trazo.
2. Material unlit emisivo + texturas buenas.
3. Grab de la herramienta/paleta con patrón `C_GrabComponent`.
4. Paleta con color picker HSV world-space.
5. Familia ISM (confeti) como 2º pincel opcional.

---

## 🔬 Auditoría del Pincel A original (2026-07-29) — qué tenía además del algoritmo

Leído directamente de los `.uasset` de `Neural Canvas\Unreal\Neural Canvas 5.8\Content\Drawing\` (extracción de strings del name table; el proyecto no se abrió). Esto es **lo que faltaba** en la lista de la §"Algoritmo de referencia", que sólo cubría la geometría.

### `M_Brush` — el material del Pincel A
**Unlit · `BLEND_Additive` · TwoSided · `TLM_VolumetricNonDirectional`.**
- **Parámetros:** `EmissiveColor` (vector) · `EmissiveBrightness` · `ShrinkAmount` · `StrokeLength` · `SamplingScale` · `SpeedY`.
- **Expresiones:** `Panner` (velocidad `SpeedY`) sobre un `TextureSample` de la textura de ruido del motor `OffsetNoiseDistanceFields_ForNormals`, con `TextureCoordinate × SamplingScale`; más `Sine`, `Divide`, `Subtract`, `OneMinus`, `Saturate`, `ComponentMask`, `AppendVector` y `VertexNormalWS`.
- `bUsedWithInstancedStaticMeshes` (lo comparte con los pinceles de estampado).
- **Lectura:** el "no se ve geométrico" del original venía de **tres cosas juntas**: aditivo (los cruces de trazos suman luz y disuelven la silueta), textura de ruido animada por Panner, y el taper por `ShrinkAmount`.

### `M_StrokeUnlit` — la versión simple
**Unlit · `BLEND_Opaque` · TwoSided**, emissive = `VertexColor × Constant3Vector`. Nada más. Es el punto de partida barato y el que se copió para `M_Brush_Light` de Soul Charger.

### `BP_Stroke` — lo que el actor tenía y nuestro diseño todavía no
**Componentes:** `StrokeMesh` (ProceduralMesh) · `AudioPincelA` / `AudioPincelB` / `AudioPincelc` (un AudioComponent por pincel) · `InstancedPincel2` / `InstancedPincel3` (ISM para los pinceles de estampado) · `SceneCaptureComponent2D` (photo booth).

**Funciones:** `PincelA_StartStroke` / `PincelA_AddPoint` / `PincelA_EndStroke` · `StartPincelB` / `StopPincelB` · `StartPincelC` / `StopPincelC` · `CapturaFoto` / `TestCapture`.

**Variables que NO estaban en la lista del algoritmo** y son el resto de "las varias cosas":
| Variable(s) | Para qué |
|---|---|
| `DynamicMaterial` + `CreateDynamicMaterialInstance` + `SetScalarParameterValue` | **Un MID por trazo** que maneja `ShrinkAmount` y `StrokeLength` → el **taper se hacía en el material**, no en la geometría. |
| `WidthMultiplier` · `FinalWidth` · `OverrideWidth` | Ancho en tres capas (base × multiplicador × override por llamada). |
| `LastPointTime` | **Decimación por TIEMPO** además de por distancia. |
| `MinDistanceMesh` · `LastSpawnLocation` | Umbral de distancia **aparte** para el estampado ISM (más grande que el del ribbon). |
| `FadeInDuration` · `FadeOutDuration` · `FadeOutCounter` · `FadeVolumeLevel` · `IsFadingOut` | Audio del pincel con **fade in al empezar y fade out al soltar** (evita el click). |
| `HapticEffect` (`HapticFeedbackEffect_Curve`) + `PlayHapticEffect` / `StopHapticEffect` | Háptico **por curva**, no por `SetHapticsByValue`. |
| `Tangents` | Alimentaba el buffer de tangentes del PMC (nosotros no). |
| `StrokeLength` · `StrokePointCount` | Métricas del trazo que consumía el material. |

### 🔴 Dónde divergimos a propósito (que no se re-abra el debate)
1. **Sin MID por trazo.** El original creaba un Material Instance Dinámico por trazo para el `ShrinkAmount`. Nuestro §4.8 lo rechaza: un MID por trazo impide fusionar trazos en pocas secciones y hace explotar los draw calls. **El taper va en la geometría** (Fase 2) y la animación de textura por `Time` + semilla en `UV1.Y`.
2. **Pincel A opaco, no aditivo.** El original era aditivo; en Quest eso es fill-rate, que es *el* cuello de botella. Nuestro §7 presupuesta el aditivo sólo para el Pincel B ("Velo"). ⚠ **Pero el aditivo es gran parte de por qué el original no se veía geométrico** — si con opaco+Fresnel el trazo sigue leyéndose duro, la variante aditiva es la siguiente palanca, midiendo el costo.
3. **Un actor lienzo, no un actor por trazo** (§4.1).

## 🔬🔬 SEGUNDA AUDITORÍA — con el proyecto ABIERTO por MCP (2026-08-03)
El usuario abrió Neural Canvas con el MCP para comparar contra nuestro trazo ("el de allá se veía fluido, el nuestro se ve muy geométrico"). Esto es lectura directa de los grafos, no extracción de binario.

### 🔴 POR QUÉ EL DE ELLOS SE VE FLUIDO Y EL NUESTRO GEOMÉTRICO — la respuesta
**No es la geometría. Es el MATERIAL.** Verificado en vivo en `M_Brush`:
- **`BLEND_Additive` · `MSM_Unlit` · `TwoSided`.**
- **`MP_Opacity` ← el canal ALFA de una textura** (`Asset_345`), muestreada con **UV0 sin conectar** → usa UV0 directo, donde **U = 0→1 a lo ancho de la cinta**. O sea: **la cinta se desvanece hacia sus bordes con un degradé de textura.** Nunca se ve el borde del polígono.
- `MP_EmissiveColor` = `EmissiveColor.RGB × (Sine × TextureSample.RGB)` — el `Sine` le da un latido/veta a lo largo del trazo.
- **`MP_WorldPositionOffset` NO está conectado** → confirma que el taper **no** es geométrico (ver abajo).

**Nuestro `M_Brush_Light` es Opaco con Fresnel** → cada borde de la cinta es un canto de polígono nítido, y cada faceta se lee. **Ese es el "geométrico".** El aditivo + alfa suave es lo que convierte una banda en un trazo de luz.

### 🔴 EL TAPER LO HACEN EN EL MATERIAL, NOSOTROS EN LA GEOMETRÍA
`AddPoint` (de ellos) pasa por trazo dos parámetros al MID:
```
SetScalarParameterValue(DynamicMaterial, "StrokeLength",  TotalDistance)
SetScalarParameterValue(DynamicMaterial, "ShrinkAmount", StrokeWidth × -1)
```
y el material los combina (`Divide → Saturate` ×2, `Subtract`, `OneMinus`) para afinar las puntas **en el shader**. Su geometría es **siempre de ancho pleno**.
→ **Es mucho más robusto que lo nuestro**: sin ventana de refresco, sin depender de la densidad de puntos, sin poder "congelarse" a mitad de rampa. Nuestro taper geométrico (`RefreshTail`/`RefreshRing`) tiene esos tres riesgos. **Candidato fuerte a migrar al material.** (El costo: un MID por trazo, que es justo lo que §4.8 evitaba para poder fusionar trazos. Trade-off a decidir: fusión vs robustez del taper.)

### La geometría de ellos, exacta (`PincelA_AddPoint`)
```
side = normalize(cross(dir, controllerUp)) × StrokeWidth
Vertices.Add(newLoc + side)      ← SOLO 2 VÉRTICES POR PUNTO
Vertices.Add(newLoc − side)
Normals.Add(side) ; Normals.Add(−side)      ← normal = el propio side (da igual: es Unlit)
UV.Add(0, TotalDistance) ; UV.Add(1, TotalDistance)
Triangles: (b, b+2, b+1) y (b+1, b+2, b+3)
CreateMeshSection(0, …)   ← RECREA la sección entera en CADA punto
```
- **Cinta plana pura, sin espesor** (2 verts). La nuestra es una caja de 4 verts → tiene silueta propia y se lee como objeto.
- 🔴 **`StrokeWidth` es el SEMI-ancho**: el ancho total = **2 × StrokeWidth**. Con su default `StrokeWidth = 1` → **cinta de 2 cm**. La nuestra usa `W × 0.5` como semi-ancho → ancho total = `W`. **Nuestro W=6 debería ser 3× más ancha que la de ellos.**
- **Defaults de referencia:** `StrokeWidth = 1` (→2 cm de ancho) · `MinDistance = 2` (¡decimación de **2 cm**, 4× más gruesa que nuestro 0.5!) · `MinDistanceMesh = 2`.
- 🔑 **Con `MinDistance=2` NO se ve facetado** — porque el alfa suave del material disimula los quiebres. Nosotros bajamos a 0.5 cm y 2° peleando el facetado **por el lado equivocado**: el problema era el material, no la densidad. Podemos volver a una densidad sana (menos vértices, más perf).

### Lo que sí conviene copiar (y está pendiente)
- **Decimación por tiempo** además de distancia/ángulo (`LastPointTime`) — evita el racimo de puntos cuando la mano se queda casi quieta con el gatillo apretado.
- **Fade in/out del audio del pincel** (Fase 5) — el original lo tenía resuelto con 5 variables.
- **Háptico por curva** (`HapticFeedbackEffect_Curve`), no por valor plano.
- **Tangentes** en el buffer del PMC, si algún material las necesita (los unlit sin normal map no).
6. Perf: `UpdateMeshSection`, cap de presupuesto, merge al finalizar, profiling en device.

Alineado con la preferencia de arquitectura: **cada mecánica en su BP, pawn liviano** (el `BP_Stroke` hace la geometría; el pawn solo dispara y provee la mano).
