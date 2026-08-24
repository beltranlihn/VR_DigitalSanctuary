# BP_LightShaft_SC + M_LightShaft — el haz de luz FALSO (Core/Light/)

> Creado 2026-08-20, pedido de Beltrán con refes tipo Turrell (luz sobre humo, negro pleno). **Una instancia de prueba** en el persistente, detrás del PlayerStart (`LightShaft_Test`, −5650/0/255, escala 3×3×5,2 = haz de 3 m de boca y 5,2 m de alto).
> **Estado: 🟡 material compilado y BP colocado; falta que Beltrán lo juzgue en editor y visor.**

## Qué es
El efecto "haz de luz en el aire" **sin luces, sin Exponential Fog y sin Volumetric Fog** (que en Quest directamente no corre): una **geometría** (cono o cilindro) con un material **unlit · aditivo** que finge el humo iluminado. Es el mismo principio de todo el toolkit Turrell del proyecto: la atmósfera vive en el shader.

## El material `M_LightShaft` — 4 capas
| Capa | Cómo | Perilla |
|---|---|---|
| **Silueta blanda** | 🆕 v2: **`pow(N·V, EdgeSoft)`** (Fresnel fijo en exp 1 = N·V puro, y la potencia va afuera). La v1 usaba `EdgeSoft` como exponente del Fresnel y el fade quedaba en una franja finísima que en la malla facetada del cono nunca llegaba a 0 → **borde cortado** (screenshot de Beltrán). | `EdgeSoft` (3,0; más alto = borde más blando y núcleo más angosto) |
| **Degradado del haz** | `LocalPosition.Z` normalizado (−50..+50 del shape del motor) elevado a `LengthFade` → brillante arriba (la fuente), se apaga hacia abajo | `LengthFade` (1,5; más alto = se apaga antes) |
| **Humo animado** | 🆕 v3 (pedido de Beltrán: "que sea noise, no matemático"): **2 muestras de `T_ShaftNoise`** — una textura de value-noise fBm de 3 octavas, 256², **tileable, generada por script e importada** (grayscale, sin sRGB, wrap) — a escalas ×1 y ×2,7, panneando en direcciones opuestas, mezcladas 65/35. Dos lecturas de textura por píxel, más barato que el nodo `Noise` (16-80 instr/octava). La v2 de senos quedó desconectada (las expresiones sin conectar no compilan al shader). | `SmokeAmount` (0,35) · `SmokeScale` (0,004 — UV por cm: más chico = manchas más grandes) · `SmokeSpeed` (0,5) |
| **Fundido al tocar** | `DepthFade`: donde el haz corta piso/muro se funde en vez de hacer línea dura | `DepthFadeDist` (80 cm) |
| Color y fuerza | `BeamColor` × `Intensity` | `BeamColor` (azul 0,35/0,6/1) · `Intensity` (1,2) |
| 🆕 **Punta suave** | `saturate((1−t)/TipSoft)`: el último tramo del cono se desvanece — mata el pico duro del apex | `TipSoft` (0,12 = el 12% final) |

- **Unlit · Additive · one-sided · Full Precision (expresiones)**: aditivo = brilla sobre negro y es independiente del orden (sin la trampa de parches de `M_Alma`); full precision + senos = sin el movimiento cortado de fp16 (lección de `M_TurrellPanel`).
- ⚠ **One-sided**: visto desde ADENTRO el haz desaparece. Si un haz debe cruzarse caminando, ese caso se decide aparte (two-sided duplica fill-rate).
- ⚠ `DepthFade` en móvil requiere la scene depth de translucidez — **verificar en el APK**; si en Quest no funde, `DepthFadeDist` alto lo disimula.

## El BP
`Beam` (StaticMeshComponent, `NoCollision`, sin sombras) + **todas las perillas del material como variables instance-editable** (cat. *A - Haz*) que el **Construction Script empuja al MID** → se tunea en el panel de detalles **viendo el resultado en el viewport**, sin abrir el material (el criterio "Beltrán autora mirando"). `Mesh` intercambiable: cono (default) o `/Engine/BasicShapes/Cylinder` para un haz paralelo tipo ventana.

## Cómo autorar
1. Duplicar la instancia, moverla/rotarla/escalarla (la escala del actor ES el tamaño del haz; el degradado y el humo se adaptan solos porque van en espacio local).
2. Color/intensidad/humo en el panel de detalles.
3. Cono apex arriba = foco de techo (ref 2); cilindro inclinado = ventana (refs 1 y 3).

## TODO
- [ ] Juicio de Beltrán en editor y visor (fill-rate: es translúcido grande en pantalla — no apilar muchos de frente).
- [ ] Verificar `DepthFade` en el APK.
- [ ] Si hace falta el "disco fuente" brillante de las refes (el óvalo de la ventana), es un segundo material trivial o un `EdgeColor` más.

## 🆕 2026-08-20 (v4) — mallas propias densas + WOBBLE
- 🔴 **"En VR se ven los triángulos"**: el cono del motor es low-poly y sus normales interpoladas facetan el degradado `N·V` (en estéreo canta). Fix: **`SM_ShaftCone` y `SM_ShaftCylinder`** generados por script (128 segmentos × 21 anillos = 5.120 tris, **sin tapas, sin punta singular** — el cono termina en un anillo de r=2 que `TipSoft` ya desvanece), con normales suaves y **UVs cilíndricas** (la 1ª importación sin UVs disparó los warnings de tangentes/MikkTSpace que pegó Beltrán — inofensivos en unlit, pero se reimportó limpio). Sin colisión. `Mesh` default → `SM_ShaftCone`.
- **Wobble tipo ameba** (WPO): `VertexNormalWS × ObjectRadius × WobbleAmount × ½(sin(z·f + T·s) + sin(x·0,73f − …1,37s))` — fracción del radio, razones no enteras, anima en el editor. Perillas: `WobbleAmount` (0,05) · `WobbleFreq` (0,05) · `WobbleSpeed` (0,6). Los 21 anillos verticales son los que le dan vértices al WPO para ondular a lo largo. ⚠ `boundsScale = 1,5` en el componente (CDO e instancia) — WPO sin bounds extra = culling pop (§ Alma).

## 🆕 2026-08-20 (v5) — el reporte de VR: banding + noise lavado
Captura de Beltrán desde el visor: **franjas horizontales** y el noise casi desaparecido.
- **Franjas = banding de 8 bits** (sin HDR móvil, el degradado aditivo se cuantiza — la MISMA queja que `M_TurrellGradient`). Fix igual: **dither R2 en espacio de pantalla** (`frac(dot(pixel, (0.7549, 0.5698))) − 0.5`) multiplicando el emisivo. Perilla **`DitherAmt`** (0,08); `DitherTemporalAA` NO sirve (no hay TAA en Quest).
- **Noise lavado = los MIPS**: a distancia/ángulo VR la textura cae a mips chicos y las octavas finas mueren. Fix: **mip 0 forzado en las dos muestras** (`mipValueMode = TMVM_MipLevel, constMipValue = 0` — `mipGenSettings` de la textura no se puede escribir por MCP). 256² suave → el aliasing es imperceptible.
⚠ `DitherAmt` es la palanca si el grano se nota: 0,05 fino · 0,12 grueso. El dither NO se aprecia en el editor (ahí no hay banding): se juzga en el visor.
