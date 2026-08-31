# Traer la estética del dibujo de Neural Canvas a Soul Charger

**Pedido de Beltrán (2026-08-28):** *"En Neural Canvas tengo resuelto el dibujo 3D, con los materiales,
colores y la paleta… la estética, los materiales y la finura del trazo están muy bien. Creo que debemos
llevarla tal cual a Soul Charger. En Soul Charger resolvimos bien dónde están las funciones y los
blueprints; es llevar esa lógica, quizás un poco optimizada, porque acá tengo muchas cosas en el VR pawn."*

**Proyecto fuente:** `C:\Users\beltr\Desktop\Alma Digital Studio\Projects\Neural Canvas\Unreal\Neural Canvas 5.8\TiltBrush.uproject`
(hay dos copias más viejas: `Neural Canvas\Old\TiltBrush` y `Neural Canvas\Antecedentes\DrawingToolkit`).

---

## Lo que se pudo establecer SIN el MCP (lectura de disco, 2026-08-28)

### 🟢 La buena noticia: la estética ya está probada en el renderer MÓVIL
No es un look de PC VR que haya que reinventar para Quest:
- `Config/DefaultEngine.ini`: **`bPackageForMetaQuest=True`**, `r.MobileHDR=False`,
  `vr.MobileMultiView=True`, `r.Mobile.AntiAliasing=3`, `r.Mobile.UseHWsRGBEncoding=True`.
- `Saved/Shaders/` tiene shaders compilados para **`SF_VULKAN_ES31_ANDROID`**.
👉 Los materiales del pincel **ya se compilaron para el renderer móvil**. "Llevarlo tal cual" es realista.

### El inventario del sistema de dibujo
| Asset | Qué es |
|---|---|
| `Drawing/BP/BP_Stroke` (714 KB) | El trazo. Referencia `M_Emissive_Inst`, `M_Spray`, un mesh, 3 sonidos y `RT_Capture_Test`. |
| `UI/BP_PincelSelect` (523 KB) | **La paleta.** Referencia `M_Brush`, `M_Spray` + `M_Spray_Inst1/2/3` y `UI/Niag_Select` (efecto de selección). |
| `Drawing/Material/M_Brush` | **`BLEND_Additive`**. `TextureSample` + `Panner` + `Sine` + `VertexNormalWS`. Textura propia `Drawing/Material/Asset*` + una función de ruido del Engine. |
| `Drawing/Material/M_Spray` (+3 inst) | **`BLEND_Additive`**, misma familia que `M_Brush`. |
| `Drawing/Material/M_Emissive` (+2 inst) | **`BLEND_Translucent`**, sin textura: pura matemática (`ComponentMask`/`Divide`/`OneMinus`/`Saturate`/`VertexNormalWS`) — un glow tipo fresnel. |
| `Drawing/Material/M_StrokeUnlit` | **`BLEND_Opaque`**, `MSM_Unlit`, color por **`VertexColor`**. El más barato de los cuatro. |
| `HUD/Brush`, `HUD/Brush1Draw` | Iconografía del HUD. |

O sea: **cuatro pinceles**, tres de ellos aditivos/translúcidos y uno opaco unlit.

### ⚠ El riesgo a medir, no a suponer
Aditivo y translúcido son **fill-rate**, que es justo el cuello de botella de Soul Charger en Quest.
Que compilen no dice qué cuestan **con la carga de Soul Charger encima** (20 amebas + hasta 100 anillos
procedurales). El trazo de Neural Canvas se dibuja sobre una escena mucho más vacía.
👉 No es motivo para no traerlos; es motivo para **medir** (ver `references/profiling-quest.md`).

---

## Lo que falta y necesita el MCP contra ESE proyecto
1. **Los grafos de los 4 materiales**: nombres y valores de parámetros, y cómo se arma el trazo
   (el `Panner`+`Sine` sugiere movimiento en el material). El nombre de los parámetros **no** se puede
   sacar del binario: vive en la name table del paquete.
2. **Cómo construye la geometría `BP_Stroke`** — ¿ProceduralMesh como el `BP_DrawCanvas` de Soul Charger,
   spline meshes, o instancias? De esto depende si el port es "sólo materiales" o también geometría.
3. **La paleta**: cómo `BP_PincelSelect` presenta y elige el pincel, y cuánto de eso vive en el VR pawn
   (Beltrán ya avisó que ahí hay de más).
4. **Las texturas** que samplean `M_Brush`/`M_Spray` (`Drawing/Material/Asset*`).

## Qué habría que migrar (hipótesis a confirmar)
Los materiales referencian **una función del Engine** (migra sola) y **texturas propias** (hay que
traerlas). Lo más probable es que alcance con un `migrate` de la carpeta `Drawing/Material` + las texturas,
y **reconstruir la lógica** en Soul Charger con su arquitectura (un BP por responsabilidad, pawn liviano),
en vez de arrastrar Blueprints con dependencias del VRTemplate — que es la regla del proyecto para
`Recursos/`.

## Cómo retomar
🔴 El MCP se negocia al arrancar Claude Code. Para trabajar sobre Neural Canvas hay que **reiniciar Claude
con ESE editor abierto**. Verificación barata al arrancar: `SceneTools.get_current_level`.

---

# Análisis con el MCP contra el proyecto (2026-08-28, sesión 2)

## 1. La arquitectura del trazo YA ES LA MISMA que la nuestra
`BP_Stroke` (componentes leídos del CDO):

| Componente | Clase | Para qué |
|---|---|---|
| `StrokeMesh` | **`ProceduralMeshComponent`** | **Pincel A: cinta procedural** — la misma técnica que nuestro `BP_DrawCanvas` |
| `InstancedPincel2`, `InstancedPincel3` | **`InstancedStaticMeshComponent`** | Pinceles B y C: **estampan mallas** a lo largo del recorrido |
| `AudioPincelA/B/c` | `AudioComponent` | un sonido por pincel |
| `SceneCaptureComponent2D` | — | el photo booth |

Funciones: `PincelA_StartStroke` · **`PincelA_AddPoint`** · `PincelA_EndStroke`.
👉 **No hay que portar un motor de geometría: ya lo tenemos.** Lo que falta es la ESTÉTICA.

## 2. `PincelA_AddPoint`, leído entero
```
dir  = normalize(NewLocation − ultimoPunto)
side = normalize(cross(dir, ControllerUp)) × StrokeWidth      <- la cinta la orienta la MUÑECA
v0   = p + side ;  v1 = p − side
n0   = side     ;  n1 = −side
UV   = (0, TotalDistance) y (1, TotalDistance)                <- la V es el ARCO ABSOLUTO
tris = dos por quad
CreateMeshSection(StrokeMesh, 0, …)                            <- reconstruye la sección cada punto
SetScalarParameterValue(DynamicMaterial, "StrokeLength", TotalDistance)
SetScalarParameterValue(DynamicMaterial, "ShrinkAmount", StrokeWidth × −1)
```
Con un gate `MinDistance` antes de aceptar el punto.
🔑 **Los dos parámetros que el Blueprint empuja al material en cada punto son `StrokeLength` y
`ShrinkAmount`.** Eso es lo que no se podía sacar del binario y es la bisagra del look.

## 3. La familia de materiales — todos `MSM_Unlit`
| Material | Blend | TwoSided | Expresiones | Texturas |
|---|---|---|---|---|
| `M_Brush` | **Additive** | ✓ | 39 | `Asset_345` (propia) + ruido del **Engine** ×2 |
| `M_Spray` | **Additive** | ✓ | 38 | **sólo Engine** ×2 |
| `M_Emissive` | **Translucent** | ✗ | 20 | **ninguna** |
| `M_StrokeUnlit` | **Opaque** | ✓ | 3 | `VertexColor × Constant3Vector` |

**Interfaz común de los tres primeros** (idéntica en los tres, lo que los vuelve intercambiables):
`EmissiveBrightness` · `StrokeLength` · `ShrinkAmount` · `Divide` · `Opacity` (escalares) · `EmissiveColor` (vector).

`M_Emissive` es literalmente `M_Brush` **sin la capa de textura**: comparten el mismo bloque núcleo
(`TextureCoordinate` → máscara → `Divide` → `Saturate` → `OneMinus` → `VertexNormalWS`), que es el
desvanecido en las puntas + la caída tipo fresnel.

### Las instancias = la paleta
| Instancia | Padre | Color | Brightness | Divide | Opacity |
|---|---|---|---|---|---|
| `M_Emissive_Inst` | `M_Emissive` | naranja (1 · 0,469 · 0) | 1 | 6 | 0,7 |
| `M_Emissive_Inst_2` | **`M_Emissive_Inst`** | celeste (0,351 · 0,636 · 1) | **29,5** | 6 | 0,7 |
| `M_Spray_Inst` | `M_Spray` | blanco | 1 | 15 | 0,7 |
| `M_Spray_Inst1` | `M_Spray` | naranja (1 · 0,262 · 0,032) | 1 | 15 | 0,7 |
| `M_Spray_Inst2` | `M_Spray` | durazno (1 · 0,708 · 0,515) | 1 | 15 | 0,7 |
| `M_Spray_Inst3` | `M_Spray` | azul (0,021 · 0 · 1) | 1 | 15 | 0,7 |

`Divide` (6 vs 15) es el divisor del arco → **el tiling de la textura a lo largo del trazo**: la perilla
de la "finura".

## 4. La paleta y el pawn
`BP_PincelSelect` (`/Game/UI/`): todo en el `EventGraph`, variables `As VRPawn`, `Pincel1/2/3`,
`Color_1/2/3`, `Material1/2/3`, `Pincel`, `Color`, `Paletas` → **3 pinceles × 3 colores**, y habla
**directo con el pawn**.
Y el `VRPawn` confirma lo que dijo Beltrán: tiene `CurrentStroke`, `IsDrawing`, `StrokeHistory`,
`PincelA/B/C`, `Color In`, `Pincel In`, `CompuertaDibujo`, `Pincel al Empezar` — **la máquina de estados
del dibujo vive en el pawn**, mezclada con teleport, grab y la galería de esculturas.
👉 **Eso NO se trae.** En Soul Charger esa responsabilidad ya está repartida en `BP_Sensor_Soul` (modo 5)
+ `BP_DrawCanvas` + la paleta.

## 5. El delta real contra nuestro `BP_DrawCanvas`
Nuestro canvas **ya es una evolución de este sistema** (auditoría del 2026-08-03: cinta plana, aditivo
unlit, borde suave). Lo que falta:

| | Neural Canvas | Soul Charger hoy |
|---|---|---|
| Orientación de la cinta | `cross(dir, **ControllerUp**)` en cada punto | transporte paralelo (`FrameUp`) |
| V de la UV | **arco absoluto** | `Arc / TexScale` |
| Borde suave | **alfa de textura** | procedural |
| Color | `EmissiveColor` (parámetro) | `VertexColor.RGB` |
| Parámetros vivos | `StrokeLength` + `ShrinkAmount` cada punto | no existen |
| Pinceles | 3 (cinta + 2 instanced) | 1 |

💡 La primera fila **ya estaba anotada en `BP_DrawCanvas.md` como "carta sin jugar"**, y ahora está
confirmada en la fuente.

## 6. 🎯 Respuesta a la pregunta de Beltrán
**Hace falta un `migrate`, pero minúsculo.** Reconstruir a mano un grafo de 39 expresiones por MCP sería
lento y frágil cuando el `migrate` lo copia perfecto.

**Lo que él migra** (Content Browser → botón derecho → Migrate):
```
/Game/Drawing/Material     (4 madres + 6 instancias)
```
La única dependencia fuera de esa carpeta es **la textura `Asset_345`** — el resto es contenido del
**Engine**, que viaja gratis. El migrate arrastra la textura solo.
⚠ Destino: `VR_Test/Content/SoulCharger/Stages/Movement/Materials/NeuralCanvas/` (aparte, para no pisar
`M_Brush_Light`).

**Lo que hago yo, sin migrate:** la lógica. Adaptar `BP_DrawCanvas` con las tres cosas de la §5
(orientación por `ControllerUp`, UV por arco absoluto, empuje de `StrokeLength`/`ShrinkAmount`) y montar
la paleta en nuestra arquitectura, no en el pawn.

## 7. ⚠ El riesgo que hay que medir
Tres de los cuatro materiales son **Additive/Translucent = fill-rate**, el cuello de botella de Soul
Charger en Quest. En Neural Canvas el trazo se dibuja sobre una escena casi vacía; en Soul Charger va a
convivir con la ameba, los anillos y el resto. **Que compilen para Android no dice qué cuestan acá.**
`M_StrokeUnlit` (opaco) existe justamente como la variante barata — vale tenerla como plan B.

---

# 📋 Extracción completa de la lógica (2026-08-28, sesión 2)
**Todo lo de abajo está leído del proyecto.** Con esto **no hace falta migrar ni un Blueprint**: los BP se
reconstruyen en Soul Charger con nuestra arquitectura, y de Neural Canvas viajan **sólo assets de arte**.

## A. Los tres pinceles

### Pincel A — cinta procedural (`ProceduralMeshComponent`)
`PincelA_StartStroke(StartLocation)`:
```
TotalDistance = 0 ; limpia Points, Triangles, Normals, UVs, UV_Array
LastLocation = StartLocation ; IsDrawing = true
PincelA_AddPoint(StartLocation, (0,0,0), 0)
Audio.Play(AudioPincelA) ; Audio.FadeIn(0.3)
```
⚠ **`Vertices` NO se limpia** en `StartStroke` (sí los otros cinco arrays). Al reconstruir, limpiarlo.

`PincelA_AddPoint(NewLocation, ControllerUp, OverrideWidth)` — ver §2 arriba.

`PincelA_EndStroke()`:
```
IsDrawing = false ; LastLocation = ultimo punto
Audio.FadeOut(0.3) ; Audio.Stop
```

### Pinceles B y C — estampado con `InstancedStaticMeshComponent`
Los dos son **el mismo patrón**, sólo cambian malla, escala y sonido:
```
StartPincelX(HandLocation):
    timer cada 0.1 s -> evento de estampado
    Audio.Play ; Audio.FadeIn(0.3)

evento de estampado:
    si distancia(UbicacionMano, LastSpawnLocation) > MinDistanceMesh:
        AddInstance( transform = ( UbicacionMano,
                                   RandomRotator,
                                   RandomFloatInRange(0.0002, 0.0005) x K ) )
        PlayHapticEffect(mano derecha, 0.5, loop)
        LastSpawnLocation = UbicacionMano

StopPincelX:
    limpia el timer ; StopHapticEffect ; FadeOut(0.3) ; Delay(0.3) ; Stop
```
| | Malla | K de escala | Sonido |
|---|---|---|---|
| **B** | `/Game/Drawing/Mesh/low_polygon_stylized_rock_free` | **0,7** | `UZ_fx_analog_odyssey_bubbles` |
| **C** | `/Engine/EngineMeshes/Sphere` (¡del Engine!) | **10,0** | `ESM_MMO_Game_Magic_Designed_Fire_Loop_01` |

Los dos con material `M_Spray`. El pincel A usa `AudioPincelA` = `FF_OHT_124_texture_loop_emoted_Gmin`.

🔴 **Un bug a no copiar:** `StopPincelX` hace `ClearAndInvalidateTimerByHandle(SetTimerByEvent(...))` — crea
un timer nuevo para borrarlo, en vez de guardar el handle. **Al reconstruir: guardar el handle en una
variable.**

### Otros datos del `BP_Stroke`
- `EventTick`: `UbicacionMano = GetWorldTransform(VRPawn.Sphere)` — la punta sale de una esfera del pawn.
- `BeginPlay`: cachea el pawn, planta el `SceneCapture2D` en un `TargetPoint` con tag **`SceneCapture`** y
  hace `ShowOnlyActorComponents(self)` → el photo booth **sólo fotografía el trazo**.
- CDO: `StrokeWidth` 1 · `MinDistance` 2 · `MinDistanceMesh` 2 · `FinalWidth` 1.

## B. La paleta (`BP_PincelSelect`) — 22 componentes
Un tablero físico que se toca con la mano:
- `Pincel_1/2/3` (mallas de muestra) + `Pincel_Collision_1/2/3` (**SphereComponent, radio 40**)
- `Color1/2/3` (esferas del Engine con `M_Spray_Inst1/2/3`) + `Color_Collision1/2/3`
- `Button_1/2/3` y `Button_Color1/2/3` (esferas del Engine): **el indicador de selección**
- `Niag_Select` y `Niag_Select1`: el mismo sistema `/Game/UI/Niag_Select`, uno por fila
- `Widget`: `/Game/HUD/Mark`, 1364×1000

**La reacción al tocar (idéntica en las 6 entradas):**
```
PlayHapticEffect(GrabHapticEffect)
boton elegido -> escala 1.2 ; los otros -> 1.0
PlaySound2D(/Engine/VREditor/Sounds/UI/Gizmo_Handle_Clicked)
Niag_Select.SetWorldLocation( boton elegido )
Pincel1/2/3 (o Color_1/2/3) = el booleano correspondiente
VRPawn.CambiarPincel(idx)  /  VRPawn.CambiarColor(idx)
```

### 🔴 Acá está el desorden que Beltrán quiere optimizar
El `EventGraph` son **154 nodos** que repiten **ese mismo bloque de 9 líneas ~18 veces**, uno por cada par
(colisión × opción), cada uno con su `DoOnce` y todo hard-codeado. En nuestro formato son **dos funciones**:
```
PickBrush(Index)   ; háptica + sonido + escalas + Niagara + índice + aviso
PickColor(Index)   ; lo mismo en la otra fila
```
y seis eventos de overlap que sólo llaman `PickBrush(0..2)` / `PickColor(0..2)`. ~20 nodos en vez de 154.
Además el `EventTick` de la paleta sólo lee `Color` del pawn — eso va por evento, no por tick.

## C. 📦 QUÉ MIGRAR — la lista definitiva
En el Content Browser de Neural Canvas: botón derecho → **Migrate**, y elegir la carpeta `Content` de
`VR_Test`. Estas son **todas** las dependencias propias; el resto es contenido del **Engine**, que viaja gratis.

| # | Asset | Por qué |
|---|---|---|
| 1 | **`/Game/Drawing/Material/`** (carpeta entera: 4 madres + 6 instancias) | La estética. Arrastra sola la textura `Asset_345`. |
| 2 | **`/Game/Drawing/Mesh/low_polygon_stylized_rock_free`** | La malla del pincel B (y su muestra en la paleta). |
| 3 | **`/Game/Drawing/Sound/`** (3 sonidos) | Uno por pincel. |
| 4 | **`/Game/UI/Niag_Select`** | El feedback de selección de la paleta. |
| 5 | *(opcional)* **`/Game/HUD/Mark`** | El widget de la paleta. Quizás conviene rehacerlo al estilo de Soul Charger. |

**NO migrar:** `BP_Stroke`, `BP_PincelSelect`, ni nada del `VRPawn` — arrastran el VRTemplate entero
(la paleta castea a `VRPawn`, el stroke lo cachea). Toda su lógica está transcrita arriba.

⚠ Destino sugerido, para no pisar el `M_Brush_Light` que ya existe:
`Content/SoulCharger/Stages/Movement/NeuralCanvas/`

## D. Lo que hago yo al volver
1. `BP_DrawCanvas`: orientación por **`ControllerUp`**, UV con **arco absoluto**, y empujar
   **`StrokeLength`** + **`ShrinkAmount`** al material dinámico en cada punto.
2. Los pinceles B y C como **un solo** modo de estampado parametrizado (malla, escala, sonido), con el
   handle del timer guardado.
3. La paleta como **`PickBrush(Index)` / `PickColor(Index)`**, en su propio BP, **fuera del pawn**.
4. Medir fill-rate en el APK antes de dar por buena la mezcla aditiva sobre la escena de Soul Charger.
