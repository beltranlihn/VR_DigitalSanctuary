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
6. Perf: `UpdateMeshSection`, cap de presupuesto, merge al finalizar, profiling en device.

Alineado con la preferencia de arquitectura: **cada mecánica en su BP, pawn liviano** (el `BP_Stroke` hace la geometría; el pawn solo dispara y provee la mano).
