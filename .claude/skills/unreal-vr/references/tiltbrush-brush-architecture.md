# Arquitectura de pinceles de Tilt Brush / Open Brush — leída del código fuente

> **Estado: verificado contra el código.** El repo está clonado local en
> `C:\Users\beltr\Desktop\Alma Digital Studio\Projects\open-brush` (fuera del git de Soul Charger,
> a propósito). Clon *sparse* de 16 MB: `Assets/Scripts/Brushes`, `Assets/Shaders`,
> `Assets/Resources/Brushes`, `Assets/Resources/BrushPrefabs`.
>
> Reconstruirlo:
> ```bash
> git clone --filter=blob:none --sparse --depth 1 https://github.com/icosa-foundation/open-brush.git
> cd open-brush && git sparse-checkout set Assets/Scripts/Brushes Assets/Shaders Assets/Resources/Brushes Assets/Resources/BrushPrefabs
> ```
>
> ⚠ Una versión previa de este archivo se escribió leyendo archivos sueltos por HTTP y
> **afirmaba cosas incompletas** (decía ~20 generadores; son 30 clases, 15 en uso real).
> Esta versión la reemplaza.

## 0. Qué repo mirar

| Repo | Estado | Para qué |
|---|---|---|
| `icosa-foundation/open-brush` | vivo | **El principal.** Fork mantenido por la Icosa Foundation, todo el código de pinceles. |
| `googlevr/tilt-brush` | archivado 2021-01 | El original de Google. Control histórico: los pinceles de las referencias que circulan son de esta época. |
| `icosa-foundation/open-brush-toolkit` | vivo | Documenta cómo cada pincel se dibuja **fuera de Unity** (export a otros motores, catálogo con GUID, shaders traducidos). Directamente pertinente para replicar en Unreal. |
| `icosa-foundation/open-blocks` | vivo | Es *Blocks* (modelado poligonal), no aplica. |

## 0.b Licencia

**Apache 2.0 sobre todo el repo, incluidos los assets** (las 72 texturas de pincel en
`Assets/Resources/Brushes/*/`). Uso comercial permitido conservando el aviso de licencia.
Lo restringido es solo la **marca**: no se puede usar el nombre "Tilt Brush" ni su logo
(ver `TILT_BRUSH_BRAND_GUIDELINES.md`). Nota: algunos assets de terceros fueron retirados del
repo (post-procesado de Unity Standard Assets, Photon) — las texturas de pincel no están entre esos.

## 1. Las dos familias de geometría (el hallazgo principal)

```
BaseBrushScript (abstracto)  -- puntero, espaciado, presion, el contrato
|
+-- QuadStripBrush (abstracto) ....... CINTA PLANA
|     +-- QuadStripBrushDistanceUV      UV por distancia recorrida
|     +-- QuadStripBrushStretchUV       UV estirada 0..1 sobre el trazo entero
|     +-- QuadStripUnitizedUVBrush
|
+-- GeometryBrush (abstracto) ........ VOLUMEN 3D por sistema de nudos
      +-- TubeBrush ---- BubbleWandBrush, QuillTubeBrush
      +-- HullBrush, ConcaveHullBrush
      +-- TetraBrush, SquareBrush, MembraneBrush, SliceBrush
      +-- ThickGeometryBrush, FlatGeometryBrush -- QuillFlatBrush
      +-- SprayBrush, MidpointPlusLifetimeSprayBrush, GeniusParticlesBrush
      +-- PrintableBrush, Square3DPrintBrush
```

Fuera del árbol de geometría: `BlocksBrushScript`, `EnvironmentBrushScript`, `PbrBrushScript`,
`SvgBrushScript` (casos especiales, no pinceles de mano alzada).

## 2. Los 83 pinceles y su generador

Mapa resuelto por GUID (descriptor `.asset` → `m_BrushPrefab` → prefab → `m_Script`):

| Generador | # | Pinceles |
|---|---|---|
| `QuadStripBrushStretchUV` | 19 | CelVinyl, Fire, Hypercolor, Ink, Light, OilPaint, SoftHighlighter, Taffy, TaperedFlat, TaperedMarker, VelvetInk, Waveform, WaveformFFT, WetPaint (+ variantes SingleSided) |
| `QuadStripBrushDistanceUV` | 16 | DuctTape, Flat, Highlighter, Marker, Paper, Plasma, Rainbow, Streamers, ThickPaint, WigglyGraphite (+ SingleSided) |
| `TubeBrush` | 14 | ChromaticWave, Comet, Disco, FacetedTube, Icing, LightWire, Lofted, NeonPulse, Petal, Spikes, Toon, TubeToonInverted, WaveformTube, Wire |
| `GeniusParticlesBrush` | 6 | Bubbles, Dots, Embers, Smoke, Snow, Stars |
| `SprayBrush` | 6 | CoarseBristles, DotMarker, LeavesSingleSided, Splatter (+ SingleSided) |
| `HullBrush` | 4 | DiamondHull, MatteHull, ShinyHull, UnlitHull |
| `FlatGeometryBrush` | 4 | DoubleTaperedFlat, DoubleTaperedMarker, Electricity, TaperedMarker_Flat |
| `MidpointPlusLifetimeSprayBrush` | 3 | DanceFloor, HyperGrid, WaveformParticles |
| `ConcaveHullBrush` / `Square3DPrintBrush` / `QuadStripUnitizedUVBrush` | 1 c/u | ConcaveHull, Square3DPrintBrush, Wireframe |
| `BlocksBrushScript` / `EnvironmentBrushScript` / `PbrBrushScript` / `SvgBrushScript` | 8 | plantillas y casos especiales |

**Lecturas de esta tabla:**
1. La variedad viene de **6 familias de generador**, no de texturas sobre un generador.
2. Pero **36 de 83 (43%) siguen siendo cinta plana texturizada**. La cinta es el caballo de
   batalla, no un atajo: Marker, Ink, OilPaint, Flat, Paper, WetPaint, ThickPaint son todos cinta.
3. Las que "se ven pro" en las referencias son **Hull** (DiamondHull), **Tube**
   (Icing, FacetedTube, Spikes) y **Particles** (Bubbles, Embers).
4. Casi todos existen en par doble-cara / `SingleSided`. Single-sided = mitad de vértices, para rendimiento.


## 2.b La lista canónica: `Assets/Manifest.asset` (62 pinceles)

En disco hay **83 descriptores**, pero incluyen experimentales y los duplicados `SingleSided`.
El que manda es **`Assets/Manifest.asset`**, que declara los **62 que se shippean**:

> OilPaint, Ink, ThickPaint, WetPaint, Marker, TaperedMarker, DoubleTaperedMarker, Highlighter,
> Flat, TaperedFlat, DoubleTaperedFlat, SoftHighlighter, Light, Fire, Embers, Smoke, Snow,
> Rainbow, Stars, VelvetInk, Waveform, Splatter, DuctTape, Paper, CoarseBristles, WigglyGraphite,
> Electricity, Streamers, Hypercolor, Bubbles, NeonPulse, CelVinyl, HyperGrid, LightWire,
> ChromaticWave, Dots, Petal, Icing, Toon, Wire, Spikes, Lofted, Disco, Comet, ShinyHull,
> MatteHull, UnlitHull, DiamondHull, LeavesSingleSided, DotMarker, Plasma, Taffy,
> FlatDeprecated, TaperedMarker_Flat, BlocksGem, BlocksGlass, BlocksPaper, PbrTemplate,
> PbrTransparentTemplate, EnvironmentDiffuse, EnvironmentDiffuseLightMap, SvgTemplate

⚠ **No hay lista de pinceles "de Quest" en los DATOS.** Se busco y no existe: ni tag de
plataforma en los descriptores, ni en `Scripts/Brushes`, ni un `Manifest_Mobile` (hay
`Manifest`, `Manifest_Experimental`, `Manifest_Zapbox`). El filtro vive en el codigo de la UI
(`Scripts/GUI`, 193 archivos). Como Tilt Brush shippeo en Quest, las familias son viables ahi;
si alguna vez hace falta la lista exacta, hay que bajarse `Scripts/GUI` y leer quien llena la
grilla del `BrushesPanel_Mobile`.

## 2.c La UI NO conviene portarla

`Scripts/Brushes` = 30 archivos (geometria, **matematica pura, viaja**).
`Scripts/GUI` = **193 archivos** (`BasePanel`, `BaseButton`, `BaseSlider`, `BrushGrid`,
`BrushSettingsTray`...) = un framework de interfaz propio, pegado al scene graph de Unity.
Portar eso es reimplementar un framework, con UMG ya disponible y una paleta fisica ya
validada en visor de nuestro lado.
✅ De ahi se toman **los 83 iconos de pincel** (`m_ButtonTexture` en cada descriptor, Apache 2.0,
se importan directo), los **rangos de tamano** (`m_BrushSizeRange`, el slider nace calibrado) y
las **decisiones de diseno mirando** (cuantos por fila, donde queda el panel respecto de la
muneca, como arman el color picker). Codigo, nada.


## 2.d LOS SHADERS Y TEXTURAS NO ESTAN EN open-brush - estan en otro paquete

Buscarlos en `open-brush` es perder el tiempo: el `m_Material` de cada descriptor apunta a un
GUID que **no resuelve en ese repo**. Viven en un paquete de Unity aparte, declarado en
`Packages/manifest.json`:

```
com.icosa.open-brush-unity-tools  ->  https://github.com/icosa-foundation/open-brush-unity-tools.git#upm
```

Clonado en `Projects/ob-tools` (rama `upm`, sparse de `Runtime/Shaders`, 45 MB). Ahi estan
**el .mat con sus valores, el shader y las texturas** de cada pincel, agrupados por familia:
`1_UnlitCommon`, `2_UnlitSpecials`, `3_DiffuseCommon`, `4_DiffuseSpecials`, `5_StandardCommon`,
`7_Particles`, `8_Experimental`, mas `Include/` (los `.cginc` compartidos) y `0_Subgraphs/`.

**El atajo para no buscar a mano:** `Assets/Generated/ShaderWarmup/open-brush-brush-variant-inventory.json`
(en open-brush) lista **865 estados de material** con `brushDurableName`, `materialPath`,
`shaderPath` y `keywords`. Es el mapa pincel -> material -> shader, ya resuelto.

Parte de los shaders son **Shader Graph** (`.shadergraph`, JSON) y no `.shader` - por eso un
`find` de `*.shader` no los encuentra.

### La formula del brillo HDR (`Include/Brush.cginc`)
```
bloomColor(color, gain):
  cmin = length(color.rgb) * 0.05        // piso en los 3 canales: los saturados
  color.rgb = max(color.rgb, cmin)       // recortan a BLANCO, no a un secundario
  color = pow(color, 2.2)
  color.rgb *= 2 * exp(gain * 10)
```
Con `_EmissionGain = 0.45` (el de Light) eso es **2*exp(4.5) = 180,03**.
El `pow(2.2)` es la conversion sRGB->lineal de Unity. **En Unreal nuestros vertex colors ya son
lineales**, asi que portarlo tal cual seria convertir dos veces: se omite a proposito.

## 3. El contrato: `Knot` y la actualización incremental

Esto vale más que cualquier pincel. `GeometryBrush.Knot` (struct por punto de control):

```csharp
PointerManager.ControlPoint point;   // pos, orient, presion, timestamp
Vector3    smoothedPos;              // suavizada con kernel (.25, .5, .25)
float      smoothedPressure;
Color32    color;
float      length;                   // distancia al nudo anterior
Quaternion qFrame;                   // marco de referencia (reemplaza nRight/nSurface)
Vector3    nRight, nSurface;         // direccion de ancho / normal de superficie
int        iTri;   ushort iVert;     // <- DONDE EMPIEZA su geometria en el pool
ushort     nTri,   nVert;            // <- CUANTA geometria le pertenece
bool       startsGeometry, endsGeometry;
```

Los invariantes documentados en el código (`CheckKnotInvariants`) existen para una sola cosa:
**cada nudo es dueño de una tajada contigua del buffer de vértices, y solo esa tajada se
reescribe cuando llega un punto nuevo.** `m_FirstChangedControlPoint` marca desde dónde
regenerar. **Tilt Brush nunca reconstruye la malla entera.**

Contraste con lo nuestro: `BP_Stroke` llama `CreateMeshSection` por cada punto, que recrea el
buffer de GPU completo, o sea trabajo cuadrático a lo largo del trazo. Ver §7.

**`m_SoftVertexLimit = 9000`**: al pasarlo, el trazo se **corta** y empieza uno nuevo
(`ShouldCurrentLineEnd`). El troceado no es un truco, es la respuesta oficial.

### El bucle central (`GeometryBrush.UpdatePositionImpl`)

1. El **último nudo siempre es "vivo"**: sigue al mando en cada tick, sin geometría propia.
2. El suavizado de posición se aplica **retroactivamente al nudo de atrás**:
   `smoothedPos = (v0 + 2*v1 + v2) / 4`. Un nudo de latencia, suavidad gratis.
3. Presión suavizada **por distancia, no por tiempo**:
   ```
   window = 0.20 m
   k = 0.1 ^ (distancia / window)
   smoothedPressure = k * anterior + (1-k) * actual
   ```
   Independiente del framerate y de la velocidad de la mano.
4. Un nudo se **confirma** solo si `distancia > GetSpawnInterval(smoothedPressure)`.
5. Al confirmar, se agrega un nudo vivo nuevo apuntando al final de la geometría actual.

El único método abstracto que implementa cada pincel es
**`ControlPointsChanged(int iKnot0)`**: rellenar la geometría de los nudos desde `iKnot0`.
Contrato minúsculo.

## 4. El espaciado es por pincel y depende de la presión

`GetSpawnInterval(pressure01)`:

| Familia | Fórmula |
|---|---|
| `TubeBrush` | `SolidMinLengthMeters + PressuredSize(p) * kSolidAspectRatio` |
| `HullBrush` | `SolidMinLengthMeters` (constante, independiente de presión) |
| `SprayBrush` | `PressuredSize(p) / SprayRateMultiplier` |

Nosotros usamos `MinDistance` constante y **no leemos la presión del gatillo en absoluto**.

## 5. Presión a tamaño, opacidad y varianza

```csharp
PressuredSize(p)            = BaseSize * lerp(PressureSizeMin, 1, p)
PressuredRandomSize(p,salt) = PressuredSize(p) * (1 + rng.In01(salt) * m_SizeVariance)
PressuredOpacity(p)         = clamp01( m_Opacity * lerp(PressureOpacityRange.x, .y, p) )
```

`HashFloat01` es un hash determinista (método multiplicativo, K = (raiz(5)-1)/2) — la varianza es
**reproducible**, no aleatoria por frame. Importante: un trazo se ve igual al recargarlo.

## 6. `BrushDescriptor` — la superficie de ajuste por pincel

Campos serializados que **no cuestan geometría nueva** (variedad barata):

```
m_BrushSizeRange        m_SizeVariance          m_SizeRatio
m_Opacity               m_PressureOpacityRange  m_PreviewPressureSizeMin
m_ColorLuminanceMin     m_ColorSaturationMax    <- restricciones de color por pincel
m_PositionVariance      m_RotationVariance      m_ParticleInitialRotationRange
m_TextureAtlasV         m_TileRate              <- fila del atlas + repeticion
m_RenderBackfaces       m_BackIsInvisible       m_BackfaceHueShift
m_EmissiveFactor        m_RandomizeAlpha        m_SolidMinLengthMeters_PS
m_ParticleSpeed         m_ParticleRate          m_SprayRateMultiplier
m_TubeStoreRadiusInTexcoord0Z                   m_BoundsPadding
m_HeadMinPoints m_HeadPointStep m_TailMinPoints m_TailPointStep m_MiddlePointStep
```

Los últimos cinco son **simplificación**: cuántos puntos conservar en cabeza, cola y medio.

## 7. Qué aplicar a Neural Canvas, por relación valor/costo

| # | Cambio | Costo | Por qué |
|---|---|---|---|
| 1 | **Presión del gatillo a tamaño y opacidad** | bajo | Es la dimensión entera que nos falta. El gatillo ya da un float analógico; hoy lo ignoramos. |
| 2 | **Suavizado de presión/ancho por distancia** (`k = 0.1^(d/0.20m)`) | bajo | Reemplaza `SpeedTau`, que es por tiempo, o sea hoy el trazo cambia de carácter según la velocidad de la mano y el framerate. |
| 3 | **Espaciado dependiente de presión** en vez de `MinDistance` fijo | bajo | Trazo suave al apretar poco, denso al apretar fuerte. |
| 4 | **Suavizado de posición (1,2,1)/4 retroactivo** | bajo | Un nudo de latencia, suavidad gratis. |
| 5 | **Varianza determinista** (`SizeVariance`, `PositionVariance`, `RotationVariance` con hash) | bajo | Rompe la uniformidad que se notó como "todos iguales". |
| 6 | **`ColorLuminanceMin` / `ColorSaturationMax` por pincel** | bajo | Un pincel de brillo no acepta colores oscuros: parte de su identidad. |
| 7 | **Buffer persistente por tajadas** en vez de `CreateMeshSection` por punto | medio | El arreglo de rendimiento de fondo. En Unreal: preasignar la sección y usar `UpdateMeshSection`, o trocear cada N vértices (el límite de ellos es 9000). |
| 8 | **Una segunda familia de generador**: `HullBrush` | alto | Lo más distinto que existe a una cinta. Es DiamondHull, el pincel estrella. |
| 9 | Las 72 texturas reales del repo (Apache 2.0) | bajo | Mejores que las generadas con PIL. Conservar el aviso de licencia. |

Los puntos 1-6 son ajustes a lo que ya tenemos y **no rompen la cinta aprobada**.
