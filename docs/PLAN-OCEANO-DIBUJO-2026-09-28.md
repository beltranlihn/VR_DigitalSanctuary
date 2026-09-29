# Plan: el océano del dibujo (etapa de dibujo, sistema TB) — 2026-09-28

> Pedido de Beltrán: un entorno para la etapa de dibujo, de la misma familia que los otros (océano del latido, líquido del EEG, desierto del secuenciador, lomas de la respiración): abstracto, onírico, minimal, con una malla que se transforma suave. Tiene que ser **más oscuro** para que el dibujo resalte: un océano **mate, sin reflexiones**, de oleaje orgánico, medio aleatorio, con una sensación **muy sutil de avanzar**, más niebla que borre el horizonte y un polvo muy fino que dé profundidad. **Meta: 72 fps en la Quest 3, como el latido.**
>
> **Lookdev aprobado (navegador):** https://claude.ai/artifact/RnA3HA811ReMdLXW8NH7KP · fuente: [`docs/prototipos/oceano-dibujo.html`](prototipos/oceano-dibujo.html) (v3). Beltrán: *"Perfecto"*. Las fórmulas de este plan son las del prototipo; los defaults de la §7 son los suyos (si ajustó perillas antes de aprobar, se pega el JSON de "Copiar valores" antes de la fase 3).

## 0. Veredicto

**Se puede, con la receta del latido y más barato que él.** Todo es desplazamiento de vértices en el vertex shader (fp32) con normal analítica, sombreado **mate unlit** y niebla dentro del shader. Sin raymarch, sin luces, sin posproceso, sin Niagara. Lo único caro de la familia (el raymarch de las gotas, 12,28 ms medidos) no aparece.

El riesgo es el mismo que tuvo el latido: **el costo de vértices**. El latido midió ~5,4 ms de vértices en su v1 y llegó a 72 fps con malla liviana y corte por onda. Este plan nace con las dos cosas puestas.

## 1. Lo aprobado, en mecanismos

| Lo que se ve | Mecanismo |
|---|---|
| Mar oscuro que se lee solo por su relieve | Normal **analítica** del campo, calculada en el VS; en el PS solo luz difusa envolvente (wrap / half-lambert) entre `DeepColor` y `SurfColor`, más un tinte de cresta por altura. **Sin Fresnel, sin especular, sin reflejo del cielo** |
| Oleaje que sube y baja en el lugar (no "en bloque") | **Mar cruzado**: 6 oleajes con direcciones repartidas en un abanico de ±95° (`OFFS` fijos) alrededor de la dirección principal |
| El gesto del oleaje: olas que nacen, crecen y mueren | **Grupos de olas**: la amplitud de cada oleaje se modula con una mancha alargada que viaja a la **velocidad de grupo** (= mitad de la de fase, mar profundo). Las crestas atraviesan el grupo |
| Crestas orgánicas, que nunca se repiten | Warp lento del dominio (`Warp`, `WarpScale`), con el gradiente corregido por la regla de la cadena |
| Sensación sutil de avanzar | El campo entero se desliza hacia el usuario a `Advance` (5 cm/s) |
| Horizonte que se pierde | Niebla exponencial por **distancia real** a la cámara hacia el color del cielo en esa dirección; el mar se funde antes de su borde |
| Profundidad | **Polvo**: 1.200 motas en una sola malla, animadas en el VS en una caja que se repite alrededor de los ojos, aditivas, que se funden con la misma niebla |
| Titileo lejano (Quest) | Cada oleaje se **apaga por distancia** antes de ser más chico que un píxel (`LodNear`/`LodFar` = 4 / 6,5 largos de onda: es donde la malla deja de tener 4 vértices por largo). El polvo bajo 1,5 px baja su brillo en vez de titilar |

## 2. El campo (una sola definición, en cm y s)

`p` = posición **local** del vértice respecto del centro del actor (nodo `LocalPosition`, gotcha 398). `t` = `View.GameTime` leído **dentro** del Custom (gotchas 185 / 382).

### 2.1 Constantes por oleaje — las calcula el Blueprint, no el shader
El prototipo las calcula una vez por cuadro en la CPU; en Unreal las calcula **`ApplyLook` del actor** (Construction Script) y las escribe como **vectores con nombre** en el MID: `W0..W5`, `V0..V5`, `E0..E5`. Sin arreglos en el shader (gotcha 399).

```
OFFS = [0, 0.85, -0.7, 0.35, -1.0, 0.55]
hash(n) = frac(sin(n · 127.1) · 43758.5453)          // la misma en BP y en el prototipo
para i = 0..5:
  f   = i / 5
  lam = LenMax · (LenMin / LenMax)^f                 // largo de onda (cm)
  k   = 2π / lam
  ang = (Dir + Spread · OFFS[i]) en radianes
  d   = (cos ang, sin ang)
  om  = sqrt(981 · k) · Tempo                        // dispersión de mar profundo, en cámara lenta
  A   = Amp · (lam / LenMax)^0.6
  ph  = 2π · hash(i + 1)
  cg  = 0.5 · om / k                                 // velocidad de grupo
  ea  = ang + (i impar ? +0.5 : −0.5)                // dirección de la mancha del grupo
  md  = (cos ea, sin ea)
  W_i = (d.x, d.y, k, om)
  V_i = (A, ph, cg · dot(md, d), 2π · hash(i + 3))
  E_i = (md.x, md.y, lam · LodNear, lam · max(LodFar, LodNear + 1))
```

### 2.2 `DrawSeaGradVS` (Custom → `VertexInterpolator` → PS): altura y gradiente exactos
El bloque de cada oleaje va **escrito 6 veces** (W0/V0/E0 … W5/V5/E5), sin bucle ni índice. Con el **corte por oleaje**: si el vértice está más allá de `E.w`, ese oleaje ya vale 0 y se salta (es lo que llevó al latido a 72 fps).

```hlsl
// entradas: P (float2, LocalPosition.xy), W0..W5, V0..V5, E0..E5 (float4),
//           GroupAmt, GroupLen, Warp, WarpScale, Advance, CalmR, CalmMin
// salida float4: (h, dh/dx, dh/dy, 0)
const float TAU = 6.2831853;
float T  = View.GameTime;
float kw = TAU / WarpScale;
float ax = P.y * kw + T * 0.071;
float ay = P.x * kw * 1.31 + T * 0.053 + 1.7;
float2 q  = P + Warp * float2(sin(ax), sin(ay));
float dwx_dy = Warp * kw * cos(ax);
float dwy_dx = Warp * kw * 1.31 * cos(ay);
float2 qa = q + float2(Advance * T, 0);
float r  = max(length(P), 1.0);
float kg = TAU / GroupLen;
float S = 0; float2 gq = 0; float gl = 0;

// ---- oleaje 0 (repetir con W1/V1/E1 … W5/V5/E5) ----
if (r < E0.w) {
  float ea = kg * (dot(qa, E0.xy) - V0.z * T) + V0.w;
  float se, ce; sincos(ea, se, ce);
  float m  = 1 + GroupAmt * se;
  float2 gm = GroupAmt * ce * kg * E0.xy;
  float x   = saturate((r - E0.z) / (E0.w - E0.z));
  float lod = 1 - x * x * (3 - 2 * x);
  float dlod = -6 * x * (1 - x) / (E0.w - E0.z);
  float s, c; sincos(W0.z * dot(W0.xy, qa) - W0.w * T + V0.y, s, c);
  S  += V0.x * lod * m * s;
  gq += V0.x * lod * (m * W0.z * c * W0.xy + s * gm);
  gl += V0.x * dlod * m * s;
}
// ---- … ----

float2 gS = float2(gq.x + dwy_dx * gq.y, dwx_dy * gq.x + gq.y) + gl * P / r;   // J^T del warp
float xc = saturate(r / CalmR);
float fade  = lerp(CalmMin, 1, xc * xc * (3 - 2 * xc));
float dfade = (1 - CalmMin) * 6 * xc * (1 - xc) / CalmR;
return float4(fade * S, fade * gS + S * dfade * P / r, 0);
```

### 2.3 `DrawSeaHeightVS` (Custom → `Transform` Local→World → **WPO**): solo la altura
🔴 Lección del latido: **Unreal compila el WPO y cada `VertexInterpolator` como funciones separadas; cada salida vuelve a ejecutar su Custom.** Por eso la altura va en un Custom propio, sin las derivadas: el mismo código de 2.2 sin `gm`, `dlod`, `gq`, `gl` ni `J`, devolviendo `float3(0, 0, fade * S)`.

### 2.4 `DrawSeaPS` (Custom → **Emissive**), `Part` 0 = mar, 1 = cielo
Recibe del VS solo `(h, ∇h)` por interpolador; la dirección de vista viene del grafo como **`WorldPosition − CameraPositionWS`** (LWC resuelto en nodos, gotcha de la niebla que "nadaba" con `PixelDepth`).

```hlsl
// entradas: G (float4 del VI), Vv (float3 = WorldPosition - CameraPositionWS), Part,
//           DeepColor, SurfColor, CrestColor, CrestAmt, WrapPow, LightAz, LightEl, Amp,
//           ZenithColor, HorizonColor, SkyPow, GlowColor, GlowAmt, GlowPow,
//           FogStart, FogDensity, Dither, SvPos (Parameters.SvPosition.xy)
float3 L = float3(cos(LightEl) * cos(LightAz), cos(LightEl) * sin(LightAz), sin(LightEl));
float  dist = length(Vv);
float3 V = Vv / dist;                                   // de la cámara al punto
#define SKY(dir) (lerp(HorizonColor, ZenithColor, pow(saturate((dir).z), SkyPow)) \
                  + GlowColor * GlowAmt * pow(saturate(dot((dir), L)), GlowPow))
float3 col;
if (Part < 0.5) {
  float3 N = normalize(float3(-G.y, -G.z, 1));
  float diff = pow(saturate(dot(N, L) * 0.5 + 0.5), WrapPow);          // MATE
  col = lerp(DeepColor, SurfColor, diff);
  float crest = saturate(G.x / (Amp * 2) + 0.5);
  col += CrestColor * CrestAmt * crest * crest;
  float fog = 1 - exp(-max(dist - FogStart, 0) * FogDensity);
  float3 fdir = normalize(float3(V.xy, 0.015));                         // el horizonte en esa dirección
  col = lerp(col, SKY(fdir), fog);
} else {
  col = SKY(V);
}
// dither estático contra el banding: el MISMO de HeartScapePS.hlsl (aprobado en visor)
float3 p3 = frac(float3(SvPos.xyx) * 0.1031);
p3 += dot(p3, p3.yzx + 33.33);
return col + (frac((p3.x + p3.y) * p3.z) - 0.5) / 255.0 * Dither;
```
⚠ En el prototipo el dither se suma **después** de la OETF sRGB (en el navegador); en Unreal se suma en lineal, como en el latido. Si en los azules más oscuros aparece banding en el visor, se sube `Dither`.

### 2.5 `DrawDustVS` (Custom → WPO), material aparte
El polvo va en un **material translúcido aditivo** (no puede compartir master con el mar opaco). La malla `SM_DrawDust_SC` guarda en cada quad su semilla **en las UV**, igual en las 4 esquinas: **UV1 = (x, y), UV2 = (z, w)**; UV0 = esquina (0…1). La posición de la malla (quads de 1 mm en semilla × 1 m) solo sirve para los bounds: Unreal borra los quads degenerados al importar, por eso no son de tamaño 0. Todo se calcula **relativo a la cámara** (`VtxRel = WorldPosition − CameraPositionWS`). Fuente real: `scripts/hlsl/DrawDustVS.hlsl` (WPO), `DrawDustAlphaVS.hlsl` (alpha por `VertexInterpolator`) y `DrawDustPS.hlsl`; el bloque de abajo es el esquema.

```hlsl
// entradas: Seed (float3 = UV1.xy, UV2.x), SeedW (UV2.y), Corner (UV0 * 2 - 1),
//           Cam (CameraPositionWS), Right/Up (fila 0 y 1 de ResolvedView.ViewToTranslatedWorld),
//           DustBox, DustFollow, Advance, DustRise, DustWobble, DustSize, SeaZ(mundo), VtxWS (posición del vértice)
float T = View.GameTime;
float3 drift = float3(-Advance * DustFollow, 0, DustRise) * T;
float3 wob = DustWobble * float3(sin(T*0.21 + SeedW*6.28), sin(T*0.17 + SeedW*9.1), sin(T*0.13 + SeedW*4.3));
float3 C = Cam + float3(0, 0, -0.25 * DustBox);
float3 f = frac((Seed * DustBox + drift - C) / DustBox);
float3 p = C + (f - 0.5) * DustBox + wob;               // centro de la mota, en mundo
float  dist = length(p - Cam);
float  projScale = 0.5 * View.ViewSizeAndInvSize.y * ResolvedView.ViewToClip[1][1];
float  px  = DustSize * projScale / max(dist, 1);
float  px2 = max(px, 1.5);                              // nunca menos de 1,5 px...
float  size = DustSize * px2 / max(px, 1e-4);           // ...agrandando el quad
float3 world = p + (Right * Corner.x + Up * Corner.y) * size;
return world - VtxWS;                                    // WPO = destino - posición original
// y por interpolador al PS: alpha = borde de caja · cerca · (1 - niebla) · titilar · (px²/px2²) · (p.z > SeaZ)
```
El PS del polvo: disco suave `1 − smoothstep(0.35, 1, |UV|)` × alpha × `DustColor · DustAmt`, **sumado en sRGB codificado contra `DustBG`** y devuelto como diferencia lineal (gotcha 485), para que las motas tenues se vean como en el prototipo. Aditivo, sin escritura de profundidad, unlit.
⚠ La posición absoluta en el VS asume el nivel cerca del origen (lo está: `L_TBTest_SC`). Si algún día va lejos del origen, pasar todo a relativo a la cámara (gotcha 398).

## 3. Arquitectura en Unreal

Carpeta nueva **`/Game/SoulCharger/Mechanics/Drawing/Scape/`** (misma convención que `Heart/Scape`). El paquete de dibujo `/Game/NeuralCanvas/` **no se toca**: el entorno es arte de Soul Charger, no parte de la mecánica portable.

| Asset | Qué es |
|---|---|
| `SM_DrawSea_SC` | Disco **polar** geométrico, generado con Blender headless: **copia** de `.claude/skills/unreal-vr/scripts/gen_heart_membrane.py` → `…/scripts/gen_draw_sea.py` (versionado). **Híbrido, 160 sectores**: anillos **uniformes cada 30 cm hasta 7,64 m** (la ola más corta, 4,2 m, no necesita más) y desde ahí **geométricos** (paso ≈ 0,0393·r, celdas casi cuadradas) hasta 250 m, donde la niebla ya es total. Sin faldón: **117 anillos, 18.721 vértices, 37.280 triángulos** (el latido liviano usa 32,6k y va a 72 fps). Generador: `scripts/gen_draw_sea.py`; `-- preview` hace el disco chico de 8 m (`SM_DrawSeaPreview_SC`, 6.401 vért) para la miniatura del material |
| `SM_DrawDust_SC` | 1.200 quads de 1 mm (4.800 vértices, 2.400 triángulos) con la semilla en UV1/UV2 (el mismo generador LCG que el prototipo), del mismo script (`-- dust`) |
| `M_DrawSea_SC` | Master **unlit opaco two-sided**, `Part` 0 mar / 1 cielo. Customs: `DrawSeaHeightVS` (WPO), `DrawSeaGradVS` (VI, 4 escalares), `DrawSeaPS` (Emissive). `PerfMode` para el banco |
| `M_DrawDust_SC` | Unlit **translúcido aditivo**, sin escritura de profundidad, `DrawDustVS` en WPO + alpha por interpolador |
| `MI_DrawSea_SC`, `MI_DrawDust_SC` | La autoría fina, con grupos iguales a los del prototipo; animan solas en el viewport (todo sale de `View.GameTime`) |
| `BP_DrawSea_SC` | **Un solo actor.** Componentes: `Sea` (`SM_DrawSea_SC`), `Sky` (`/Engine/BasicShapes/Sphere` a escala 600 = 300 m, más allá del borde del mar), `Dust` (`SM_DrawDust_SC`). Sin sombras, sin colisión |

**El actor no necesita Tick.** El tiempo, el avance y el polvo salen de `View.GameTime` y de la cámara dentro del shader; el Blueprint solo trabaja en el Construction Script (y al cambiar una perilla). Costo de CPU: cero por cuadro.

### Funciones de `BP_DrawSea_SC` (una por responsabilidad)
- **Construction Script**: `SetMaterial` + MIDs en los tres componentes → `Part` 0/1 → colisión y sombras apagadas → **`ApplyLook`**.
- **`ApplyLook()`**: perillas del actor → parámetros de los MIDs (`LookTo(C)` por componente, como el latido) → **`WaveConstants()`**.
- **`WaveConstants()`**: el bucle de la §2.1 → `SetVectorParameterValue("W"+i / "V"+i / "E"+i)` en el MID del mar. Seis vueltas, con el nombre armado por texto.
- **`PerfDS0..4`** (eventos de consola `ke * PerfDS<N>`) para el banco: nombres propios para no chocar con los `Perf0..3` del latido en `Test_Recorrido`. 0 todo · 1 vértices baratos · 2 píxeles baratos · 3 los dos · 4 sin polvo.
- **`BeginPlay` → `ApplyLook`** también: en el juego cocinado no se depende de los MIDs del Construction Script.

### Dónde se ubica
En `L_TBTest_SC`: el actor en **(−315, 0, −120)**, con el centro del disco bajo los ojos (el PlayerStart está en x −315) y el mar a ~3,4 m bajo los ojos sentados. 🔴 **Escala del actor = 1** (todo está en cm locales); se puede girar en yaw.

## 4. Perillas en el actor (Details), agrupadas como el prototipo

| Categoría | Perillas (actor → material) |
|---|---|
| **1 - Oleaje** | `SwellAmp` 22 · `SwellLenMax` 2600 · `SwellLenMin` 420 · `SwellDir` 180 · `SwellSpread` 95 · `Tempo` 0,28 (entran solo a `WaveConstants`) |
| **2 - Grupos y morphing** | `GroupAmt` 0,75 · `GroupLen` 9000 · `Warp` 120 · `WarpScale` 4500 |
| **3 - Avance** | `Advance` 5 cm/s (mar **y** polvo) |
| **4 - Cerca y lejos** | `CalmR` 600 · `CalmMin` 0,7 · `LodNear` 4 · `LodFar` 6,5 (en largos de onda) |
| **5 - Superficie (mate)** | `DeepColor` · `SurfColor` · `CrestColor` · `CrestAmt` 1 · `LightAz` 40 · `LightEl` 22 · `WrapPow` 1,6 |
| **6 - Cielo y niebla** | `ZenithColor` · `HorizonColor` · `SkyPow` 0,45 · `GlowColor` · `GlowAmt` 0,012 · `GlowPow` 30 · `FogStart` 500 · `FogDensity` 0,00017 · `Dither` 1 |
| **7 - Polvo** | `bShowDust` · `DustAmt` 0,45 · `DustColor` · `DustSize` 0,9 · `DustBox` 1400 · `DustFollow` 1 · `DustRise` 0,6 · `DustWobble` 8 · `DustNear` 35 · `DustBG` (fondo típico detrás de las motas = `SurfColor`; gotcha 485) |
| **8 - Material base** | `LookMI` (la MI de la que salen los MIDs) |

Colores (lineales) de la paleta "Noche índigo" aprobada: `DeepColor` (0,0016; 0,0021; 0,0052) · `SurfColor` (0,0052; 0,0068; 0,0155) · `CrestColor` (0,006; 0,009; 0,017) · `ZenithColor` (0,0006; 0,0008; 0,0022) · `HorizonColor` (0,0095; 0,011; 0,024) · `GlowColor` (0,55; 0,6; 0,75) · `DustColor` (0,55; 0,62; 0,8).
🔴 Defaults en el CDO **y** leer la instancia colocada después de cada cambio de variables (gotchas 146 / 420 / 435: en esta misma sesión las perillas nuevas del director nacieron en 0 en el nivel).

## 5. Presupuesto (estimado; se mide antes de darlo por bueno)

| Pieza | Costo esperado | Por qué |
|---|---|---|
| Mar, vértices | **Lo que hay que vigilar** | ~18,7k vért × 2 vistas × (Height + Grad) × ≤ 6 oleajes con 2 `sincos` cada uno. El corte por oleaje (LOD de Nyquist) saca los cortos en los anillos lejanos, que son la mayoría de los vértices: en promedio se evalúa solo una fracción de los 6 oleajes por vértice (la mide `DrawSea_check.py`). Referencia: el latido liviano (32,6k vért) cabe en 72 fps con ~3 ms de margen |
| Mar, píxeles | Bajo | Una capa opaca; normalizar, un `pow`, un `exp`, dos `pow` del cielo para la niebla, dither. Sin reflejos ni especular |
| Cielo | Muy bajo | Solo lo que el mar no tapa, mismo PS |
| Polvo | Muy bajo | Una draw call, 4.800 vértices, motas de pocos píxeles aditivas |
| Actor | Cero por cuadro | Sin Tick |
| Draw calls | 3 | Mar, cielo, polvo |

**Si no llega a 72:** en este orden, midiendo cada paso con el banco: (1) 160 → 128 sectores; (2) `LodNear/LodFar` más cortos (p. ej. 3 / 5: el corte actúa antes, a costa de algo de aliasing lejano); (3) 6 → 4 oleajes en los anillos lejanos (rama por distancia); (4) mover el `sincos` del grupo a una sola evaluación compartida por pares de oleajes.

Banco: el que ya existe (`ke * PerfN` + `PerfMode` + `quest_heart_perf.ps1` de la skill, adaptado). Modos: 0 = todo · 1 = vértices baratos (sin oleaje) · 2 = píxeles baratos (color plano) · 3 = sin polvo. Dos pasadas; cuidado con el instrumento saturado (si todo queda clavado en 72 Hz, las restas no dicen nada).

## 6. Riesgos conocidos y su mitigación

| Riesgo | Gotcha | Mitigación |
|---|---|---|
| Índice dinámico en el VS de Adreno (un ojo o ninguno) | 399 | Seis bloques escritos a mano con vectores con nombre; sin arreglos ni bucles con índice |
| fp16 en el PS (tiempo, coordenadas grandes) | 185, 382 | El campo entero en el VS (fp32); el PS solo recibe `h` y `∇h`. `View.GameTime` dentro del Custom |
| Custom evaluado varias veces por vértice | tracker del latido | Height y Grad en Customs separados; ninguno calcula lo que su salida no usa |
| Niebla que "nada" al girar la cabeza | tracker del latido | Distancia real `WorldPosition − CameraPositionWS`, nunca `PixelDepth` |
| `TransformPosition(WorldPosition)` en el VS móvil lejos del origen | 398 | `LocalPosition` para el mar; el polvo asume el nivel cerca del origen (lo está) |
| Culling por WPO | 134 | El mar se mueve poco en Z, pero `BoundsScale` 1,5; el polvo, `BoundsScale` alto o sin culling (vive alrededor de la cámara) |
| Instancia que nace en cero | 146, 420, 435 | Defaults en el CDO y **leer la instancia colocada** |
| Script fallido que dispara Undo en el nivel | 60, 418 | Llamadas directas, sin `execute_tool_script`; `save_assets` con rutas explícitas; avisar antes de tomar el editor (memoria "editor compartido") |
| Banding en gradientes oscuros | memoria "degradados en Quest" | Dither IGN; se juzga en el visor |
| **Vección** (todo el suelo se mueve) | — | `Advance` bajo (5 cm/s) y el polvo acompaña. **Se juzga en el visor**; con 0 el mar sigue vivo sin avanzar |
| El `BP_Sky_Sphere` de `L_TBTest_SC` tapa o compite con el cielo nuevo | — | **Decisión de Beltrán** (§8): ocultarlo o sacarlo. No se saca sin pedido |

## 7. Fases de construcción

Cada fase termina con una verificación concreta. Las fases 1 a 4 no abren ningún nivel: todo se ve en la preview del asset y en el viewport del Blueprint.

0. ✅ **Lookdev en navegador** (aprobado, v3; v4 con la malla real y el LOD 4/6,5).
1. ✅ **Fuente HLSL versionada** (2026-09-29): `scripts/gen_draw_sea_hlsl.py` escribe los 6 Customs en `scripts/hlsl/`. **`scripts/hlsl/DrawSea_check.py` = TODO OK**: compila cada uno con dxc SM6, fxc SM5 y glslc→SPIR-V + spirv-val (con -WX); traduce el HLSL a Python y lo compara con `draw_sea_model.py` (altura y gradiente con error 1e-16, PS del mar y del cielo, PS del polvo); gradiente contra diferencias finitas; `PerfMode`/`Part`; 5 controles negativos que fallan como deben. Cada vértice evalúa en promedio el **70 %** de los oleajes.
   - Arreglos que salieron de la verificación: la constante grados→radianes con precisión completa; y el **polvo suma en sRGB codificado contra un fondo conocido `DustBG`** (gotcha 485: el prototipo mezcla en codificado, la Quest en lineal; sin esto las motas tenues salían ~2 veces más apagadas).
2. ✅ **Mallas** (2026-09-29): `scripts/gen_draw_sea.py` (Blender headless) → `VR_Test/Saved/ClaudeScripts/SM_DrawSea_SC.fbx` (117 anillos, 18.721 vért, 37.280 tris), `SM_DrawDust_SC.fbx` (1.200 quads de 1 mm, 4.800 vért, semillas en UV1/UV2), `SM_DrawSeaPreview_SC.fbx` (disco de 8 m). Suavizado exportado y sin triángulos de ancho cero: las dos causas conocidas del cartel modal del import (gotcha 303).
3. ✅ **Armado de los materiales, preparado y ensayado sin editor**: `scripts/plan_draw_sea_material.py` → `oceano/draw_sea_build.json`; `scripts/apply_draw_sea_material.py` (se pega en `execute_tool_script`); **`scripts/dryrun_draw_sea.py` = TODO OK** contra el editor simulado (dos vueltas idempotentes, 76 expresiones, 132 entradas cableadas desde la fuente que dice cada cabecera, WPO/VI/Emissive, los 57 parámetros con el default del modelo, MI con su padre).
4. ✅ **Blueprint, preparado y simulado sin editor**: `scripts/draw_sea.dsl` (8 grafos) + **`scripts/draw_sea_sim.py` = TODO OK** (W/V/E contra el modelo con los defaults y 3 juegos al azar, error 0; cada parámetro llega a su componente; banco `PerfDS0..4`; categorías de cada getter; control negativo). La tabla de variables sale de ahí (`oceano/draw_sea_bp.json`) y la usan `apply_draw_sea_bp_A.py` (BP + componentes + 48 variables) y `apply_draw_sea_bp_B.py` (defaults del CDO con relectura).
   - 🔴 Trampa encontrada: **el `Fraction` de Unreal es `x − trunc(x)` (conserva el signo)**; el hash del prototipo usa `x − floor(x)`. El DSL lo corrige; sin la corrección cambian 6 de las 12 fases.

5. ✅ **Construido en Unreal (2026-09-29, turno 4 de Narrativa)**: pasos 1-12 de abajo hechos. Mallas exactas (37.280 / 2.400 tris, sin cartel modal), materiales sin error de compile, BP con los 8 grafos (compila, relectura = DSL), **W/V/E del MID = modelo a 5e-8**, actor en `L_TBTest_SC` (label `DrawSea`), captura del viewport con el oleaje y la niebla, PIE limpio. Contrato TOUR y sonidos también (ver `BP_TBStroke.md` 5s). Tracker: [`BP_DrawSea_SC.md`](../.claude/skills/unreal-vr/blueprints/BP_DrawSea_SC.md).
6. ⬜ **APK + banco** (`ke * PerfDS0..4`, dos pasadas). **Meta 72 fps.**
7. ⬜ **Visor con Beltrán.**

### 7.1 Receta del turno de editor (fases 5-7) — ✅ ejecutada el 2026-09-29
Con el editor de turno (orden de Narrativa). Guardar con **rutas explícitas** después de cada paso; nada de `save_assets([])`.
1. `SceneTools.get_current_level` (no cargar otro nivel hasta el paso 9).
2. **Import**: `StaticMeshTools.import_file` × 2 (`SM_DrawSea_SC`, `SM_DrawDust_SC`; `import_materials` false) a `/Game/SoulCharger/Mechanics/Drawing/Scape`. Verificar triángulos (37.280 / 2.400). Si el editor deja de responder con `Responding=True`, es el cartel modal (gotcha 303): cerrarlo por `WM_CLOSE` (fuera de PIE es seguro). Guardar.
3. **Materiales**: pegar `apply_draw_sea_material.py` en `execute_tool_script` → esperar `salidas_ok` 4 de 4 y 3 de 3, 0 fallos, log vacío. Después `MaterialTools.recompile` de cada uno por separado y leer el log **solo después** de esa línea (gotcha 479). Guardar los 2 materiales y las 2 MI.
4. **BP, esqueleto**: probar primero UNA llamada directa de `set_variable_category` (nombres de argumento). Pegar `apply_draw_sea_bp_A.py` → `faltan` [] y `duplicadas_0` []. `compile_blueprint`.
5. **Plantillas de componente** por llamada directa (gotcha 482: nada de nombres de propiedad sin verificar dentro de un script): `Sea` (malla, `OverrideMaterials` MI_DrawSea_SC, sin sombra, `BoundsScale` 1,5), `Sky` (`/Engine/BasicShapes/Sphere`, MI_DrawSea_SC, `RelativeScale3D` en formato texto `(X=600,Y=600,Z=600)`), `Dust` (malla, MI_DrawDust_SC, `BoundsScale` 50). Releer.
6. **Defaults**: pegar `apply_draw_sea_bp_B.py` → `no_coinciden` []. 
7. **Funciones**: `add_function_graph` × 6 + `add_function_param` (Wave: I, Off float; LookSea: C `MeshComponent`). `find_node_types` para los 3 VERIFICAR (`Math|Float|Power`, `Math|Float|%`, `Rendering|Material|SetMaterial`). Un `write_graph_dsl` por grafo en el orden del archivo; el EventGraph después de borrar sus 3 eventos fantasma. `compile_blueprint` sin errores. Guardar.
8. **Verificación en el BP**: releer `W0..E5` del MID del mar contra `python draw_sea_model.py`.
9. **`L_TBTest_SC`**: abrirlo, colocar `BP_DrawSea_SC` en **(−315, 0, −120)** y **releer la instancia** contra el CDO. Captura del viewport. Guardar el nivel con ruta explícita.
10. **Contrato TOUR en `BP_TBDirector_NC`** (pedido de Narrativa, 2026-09-29): receta y DSL en `scripts/tb_tour.dsl`, **simulado con `scripts/tb_tour_sim.py` = TODO OK** (sin TOUR igual que hoy; con TOUR dormido sin log; despertar/dormir idempotentes; dormir dibujando suelta el trazo y corta carga, loop y háptica; manos devueltas solo si las ocultó el director; con el sistema cerrado no reaparece nada; `bForceTour`). Leer ANTES los grafos que nombra el archivo; variables nuevas en CDO **e instancia**; cirugía mínima en `EventBeginPlay` (CheckController → TourBegin). PIE: sin TOUR igual que hoy; con `bForceTour` + `ke * TourWake` / `ke * TourSleep`. 🔴 **Antes de guardar: `bForceTour` = false en el CDO Y en la instancia de `L_TBTest_SC`, releído** (si queda en true, el director nace dormido para siempre ahí y en el recorrido). Guardar el BP.
11. **Sonidos fuera de `/Engine/VREditor`**: duplicar `VR_click1`, `VR_click2`, `VR_shep_scale_up_01`, `VR_shep_scale_up_02`, `VR_shep_scale_down_02` a `/Game/NeuralCanvas/Sound/` y reapuntar el CDO del director, su instancia en `L_TBTest_SC`, el CDO de `BPC_TBTool_NC` y la plantilla `TBTool` del director. Verificar al guardar: `grep -l VREditor` sobre `Content/NeuralCanvas` vacío. (Nada impide cocinar `/Engine/VREditor` —`InternalOnlyPaths` es solo del visor de clases— pero ningún APK incluyó todavía el dibujo: así se quita la duda.)
12. PIE corto: sin errores ni `Accessed None`. Cerrar editores de asset. Avisar a Narrativa: "Drawing libera el editor" + clase/label del director, labels de la etapa (con el océano), punto y orientación del usuario, flags de prueba.
Después (otro turno): APK + banco (`ke * PerfDS0..4`, dos pasadas) y visor con Beltrán.

## 8. Decisiones abiertas (de Beltrán)

1. **El `BP_Sky_Sphere` de `L_TBTest_SC`**: con el cielo del actor sobra. ¿Se oculta, se saca o se deja?
2. **Dónde va en la obra**: la etapa de dibujo todavía no tiene lugar en el guion V4. El actor es autónomo (se arrastra al nivel de la etapa); la integración con `BP_StageBase_SC` y el velo de color se decide con el guion.
3. **Al terminar la etapa**: hoy el sistema de dibujo se cierra y no aparece nada nuevo. ¿El mar sigue igual, se calma (bajar `SwellAmp` y `Advance` con el tiempo) o se funde a negro? Es una perilla más en el actor si se quiere.
4. **Color de la etapa**: la paleta aprobada es "Noche índigo". Si la etapa tiene color propio en la obra, se ajusta con las mismas perillas.

## 9. Qué no se toca

`/Game/NeuralCanvas/` (el sistema de dibujo), `Heart/Scape` y sus scripts (se **copian**, no se referencian), `/Game/Test_Sequencer`, `Core/` y `Config/`.

## Fuentes principales

- Prototipo aprobado: `docs/prototipos/oceano-dibujo.html` (v3).
- Receta y mediciones del latido: [`PLAN-MEMBRANA-DEL-LATIDO-2026-09-27.md`](PLAN-MEMBRANA-DEL-LATIDO-2026-09-27.md) y el tracker [`BP_HeartScape_SC.md`](../.claude/skills/unreal-vr/blueprints/BP_HeartScape_SC.md) (v1 58-66 fps → v3 72 fps; vértices ~5,4 ms, píxeles ~2 ms).
- Oleaje: dispersión de aguas profundas `ω = √(g·k)` y velocidad de grupo `c_g = c/2` (Tessendorf, *Simulating Ocean Water*, 2001; GPU Gems cap. 1, ondas con normales analíticas).
- Meta, presupuesto de Quest 3 y GPUs por tiles: https://developers.meta.com/horizon/resources/device-optimization-comparison/
