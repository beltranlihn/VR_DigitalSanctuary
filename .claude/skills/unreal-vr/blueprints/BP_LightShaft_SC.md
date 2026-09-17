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

## 🆕 2026-09-04 (v8.3) — el pozo ORIENTADO con el haz + la nube sin costuras
Los dos arreglos que pidió Beltrán tras mirar la composición ("con el formato rectangular la iluminación de piso está girada respecto a la forma" / "en el shader de nubes se ven como píxeles o recortes").

### 1. El pozo giraba porque vivía en el marco de la PENDIENTE, no en el del haz
`ApplyFloorGlow` orienta el plano del pozo con `MakeRotFromX(cuesta-abajo)` — necesario para elongarlo 1/cosθ en la dirección correcta. Pero la SECCIÓN del haz está orientada por el **yaw del propio haz**, y ambos marcos difieren: con `roll` puro la cuesta cae a ±90° del eje largo de la rendija → el pozo se ve **cruzado**. Ese es exactamente el caso de la rendija `1.7/0.16` de la composición (yaw 20, roll 8).
**Solución (afín y exacta):** el plano se sigue orientando por la cuesta (así el estirón de perspectiva es correcto), y la FORMA se rota y se proporciona **dentro del material**:
- `M_ApertureGlow_SC` — 3 params nuevos: **`BoxAngle`** (radianes; rota la coordenada centrada antes del SDF: `x' = x·cos−y·sin`, `y' = x·sin+y·cos`) y **`AspectX`/`AspectY`** (dividen la coordenada YA rotada → la caja se vuelve rectángulo y el círculo se vuelve elipse, con la misma cadena). Orden obligatorio: **centrar → rotar → dividir por aspecto → abs → −BoxHalf**. ⚠ Los `Sine`/`Cosine` van con `period = 6.283185` (si no, entrada ×2π).
- **`ApplyGlowAspect`** (función nueva, última de la cadena del UCS): `aspect = (ShapeWidth, ShapeDepth) / max(ambos)` a pozo Y disco fuente; `BoxAngle = −(azimut del ForwardVector del Beam − azimut de la cuesta) · π/180` solo al pozo (el disco fuente ya vive en el marco del haz → 0). Con `bFloorFollowsBeam` el plano es relativo al haz → `BoxAngle = 0`.
- Verificado con un actor de prueba desechable (pitch 30 + roll 30 → Δ real de 49°): el pozo queda alineado con la sección del haz y no con la cuesta. El signo está comprobado, no supuesto.
- 🔴🔴 **La trampa que costó media sesión: un MID creado ANTES de que el material ganara un parámetro nunca lo honra.** `SetScalarParameterValueOnMaterials` guarda el valor en el array del MID (¡se lee de vuelta perfecto!) pero el render proxy lo ignora, porque su set de expresiones cacheado es el que tenía el padre al crearse. Síntoma: "el BP empuja bien, el MID tiene el número, y en pantalla no cambia nada" — y un actor recién colocado SÍ funciona. **Fix: recargar el nivel** (`SceneTools.load_level`) o reabrir el editor; los MIDs se rehacen. Hecho en esta sesión.

### 2. La nube: el color se evaluaba en la posición YA DESPLAZADA
En el pixel shader `WorldPosition` devuelve la posición **post-WPO**; el vertex shader desplazó con `noise(P₀)`. Resultado: el color se calculaba con `noise(P₀ + desplazamiento)` — un campo plegado sobre sí mismo que genera **parches y pliegues con borde duro** justo donde la ola es empinada (con `CloudHeight` ~310 es enorme). Es la firma de los "píxeles o recortes".
**Fix: `VertexInterpolator`** entre `Noise_0` y el `Alpha` del lerp de color — el píxel recibe EXACTAMENTE el mismo noise que desplazó el vértice, interpolado suave. Bonus grande para Quest: el nodo Noise pasa de por-píxel a **por-vértice** (16k evaluaciones en vez de millones) → baja muchísimo el riesgo del "Noise sin verificar en el APK". El `DepthFade` de la opacidad sigue por píxel (tiene que serlo). + `bUseAsOccluder = False` en el componente `Cloud` (un plano translúcido no debe ocluir).
🟡 Ambos arreglos juzgados en el editor. **Falta el veredicto de Beltrán y el visor.**

## 🆕 2026-09-03 (v8.2) — pozo/fuente RECTANGULARES + BP_CloudPlane_SC + composición
- **`M_ApertureGlow_SC` ahora es un SDF de caja redondeada** (params `BoxHalfX/BoxHalfY`; en 0,0 = el círculo de siempre → retrocompatible). `ApplyFloorGlow` y `ApplySourceGlow` empujan 0.42 cuando `ShapeIndex==2` → pozo y disco fuente RECTANGULARES para el haz de caja, elípticos para el resto.\n- 🆕🔴 **v4 nube (2026-09-04): LA RECETA REAL DEL TUTORIAL** — tras la llamada de atención de Beltrán ("¿revisaste el tutorial de verdad o asumiste?"): **asumí**; v1-v3 eran adaptaciones con texturas. La transcripción real (oEmbed de YouTube confirmó: *"How To Make A Stylized Cloud Effect — UE5 Materials Tutorial"*, Pitchfork Academy; transcript vía notegpt) dice: **nodo Noise procedural** (función *Gradient texture-based*, turbulence OFF, levels 1, output 0–1) muestreando **WorldPosition + Time×(SpeedX,SpeedY,SpeedZ)** — la deriva por Z del campo 3D es lo que hace que las olas CAMBIEN de forma orgánicamente (SpeedZ ~0.2); **WPO = noise × normal × 250**; **opacidad = sólida × DepthFade(400) × camera fade**; **color = lerp(color-valle, blanco-cresta) por el MISMO noise**; plano 256×256 subdivisiones (mín 64), translúcido unlit. Implementado fiel en `M_CloudPlane_SC` (params: SpeedX/Y/Z/NoiseScale nuevos; Time con period 600). `SM_CloudPlane` ahora 129×129 (32k tris). Escena: `CloudOcean` (z=20, NoiseScale 5 para el cuarto de 60 m) + **`CloudSky`** (el mismo océano con roll 180 pegado al techo) — el sándwich cielo/mar con los haces puenteando es LA imagen. ⚠ **El nodo Noise en el APK de Quest está SIN VERIFICAR** (mobile forward; gradient-tex es la variante barata, pero probar — fallback: volver a `T_smoothCloudsNoise`, v3 documentada). ⚠ Speeds/ValleyColor son params del MATERIAL, no variables del BP (el BP no los pushea).\n- 🆕 **v3 nube (2026-09-04): la pasada de SUAVIDAD.** Dos causas del look "geométrico": (a) malla gruesa para el desplazamiento (41×41 sobre 65 m con olas de 1,7 m = crestas facetadas) → **`SM_CloudPlane` 101×101 / 20k tris** (regalados: la app es fill-bound); (b) **el noise importa MÁS que la matemática**: `T_ShaftNoise` (fBm filoso, hecho para humo de haz) daba picos; con **`T_smoothCloudsNoise_01_D` de EasyFog** las mismas cadenas dan lomos esponjosos. + **sombreado por PENDIENTE** (2 muestras offset del heightfield → luz fija baña crestas, `SlopeShade`) — el tinte por altura solo no esculpe. + **el tragado necesita METROS**: `DepthFadeDist` 300 en el océano (25 daba línea de corte). ⚠ Reimportar `SM_CloudPlane` re-rompe referencias: re-apuntar CDO del BP de nube + instancias + material default del asset (hecho).\n- 🆕 **v2 del material de nube (2026-09-04): EL OCÉANO** — tras ver la refe real (Pitchfork Academy): manto continuo casi opaco, oleaje de 2 octavas con **sombreado por altura** (`ValleyColor`→`CloudColor` por lerp del height + fresnel de seda), y la firma del efecto: **halo de contacto** — `1−DepthFade(EdgeFadeDist)` sumado al emisivo, brilla donde toca cualquier objeto. Params nuevos: `ValleyColor · EdgeFadeDist` (140) · `EdgeGlow` (1.3). La instancia `CloudOcean` colocada cubre todo el cuarto a z=120 (Density 1 · NoiseScale 2.2 · CloudHeight 70 · Erode 0 · DepthFadeDist 25) — los haces se hunden en el mar con resplandor sumergido. ⚠ El tiling manda: NoiseScale chico sobre un plano gigante = superficie lisa; ~2-3 para ver oleaje cercano.\n- **`BP_CloudPlane_SC` + `M_CloudPlane_SC` + `SM_CloudPlane`** (Core/Light): el plano-nube del tutorial — malla 41×41 (3200 tris), material unlit translúcido con 2 noises panneados (T_ShaftNoise), erosión (`Erode`), máscara radial, **DepthFade** (se funde contra geometría), CamFade y **WPO** por noise (`CloudHeight`) para silueta esponjosa. Perillas (cat A - Nube): `CloudColor · Density · NoiseScale · Erode · CloudHeight · DepthFadeDist`. Full precision + panners lentos. 🟡 sin visor.\n- **Composición de referencia en `/Game/TestMeshes`** (carpeta LightShaftTest): 7 haces (óculo héroe cono 2.6×9 · cono LÁSER pálido con taper 1.6 · ventana box con gradiente roll 16° · columna junto al PlayerStart · cilindro de ritmo · rendija lejana 1.7/0.16 · +1 de Beltrán) + 3 nubes + 2 velos + 2 polvos. Fotos enviadas al móvil (comp_wide/diag/laser/inside en Saved/).\n\n## 🆕 2026-09-03 (v8.1) — el box de verdad: literal muerto, normales radiales y proporción
- 🔴 **Trampa pagada: borrar+reimportar un asset MATA los literales de pin que lo referencian.** `ApplyShape` quedó apuntando al `SM_ShaftBox` borrado → con ShapeIndex 2 `Mesh`=None → el `IsValid` cortaba TODA la cadena (mesh viejo + material en defaults azules, "no respeta parámetros"). Fix: rehacer la función (el literal re-resuelve). **Regla: tras borrar+reimportar un asset, rehacer/reconectar todo pin que lo tenía como literal.** Los 3 SM_Shaft* ahora llevan `M_LightShaft` como material DEFAULT del asset (robustez extra).\n- **`SM_ShaftBox` v3 — normales RADIALES mezcladas (65% radial desde el eje / 35% plana de cara)**: un volumen brilla por espesor, no por ángulo — con normales planas puras las caras no-frontales morían (N·V→0). Con la mezcla, las 4 caras son siempre visibles con degradado suave y un facetado sutil que delata el cuadrado (pedido exacto de Beltrán). El generador vive en el historial del scratchpad (`gen_shaftbox` + variantes); parámetro `BLEND`.\n- **`ShapeWidth` / `ShapeDepth`** (A - Forma, default 1): proporción de la sección — cuadrado, alargado, rendija — aplicada como escala relativa del componente Beam en `ApplyShape` (pozo y fuente la heredan por ser hijos). ⚠ Instancias pre-existentes nacen con 0 → colapso a escala cero; las 3 del nivel ya se corrigieron a 1.\n\n## 🆕 2026-09-03 (v8) — la pasada de feedback: categorías, taper, gradiente, apertura con forma, suelo ficticio
Todo el feedback de Beltrán de la tarde, aplicado y compilado:
- **Categorías reorganizadas**: `A - Forma` (ShapeIndex/Mesh/Spread) · `B - Luz` (BeamColor/Intensity/EdgeSoft/LengthFade/TipSoft/bGradient/GradientColor/GradientAmount) · `C - Vida` (Smoke*/Wobble* ×5 +Taper) · `D - Piso` (bAutoFloor/FloorZ/bFloorFollowsBeam/bShowFloorGlow/FloorGlow*) · `E - Laser` · `F - Fuente` (SourceGlow*/bShapedAperture/ApertureBoost) · `G - Sistema` (bDriveMPC). ⚠ Los type_ids de getters en DSL ahora llevan estas categorías (`Variables|D-Piso|GetFloorZ`).
- **Bug del FloorZ pisado, arreglado**: el trace escribe **`EffectiveFloorZ`** (interna, no editable); el `FloorZ` manual NUNCA se toca — destildar `bAutoFloor` vuelve al valor autorado. Todos los consumidores (pozo, láser, kill-fade, MPC) leen la efectiva.\n- **`WobbleTaper`** (C-Vida, default 1): el wobble crece hacia el FINAL del cono (pow(1−t, taper)) — arriba recto, abajo ondulado, como las refes de láser. 0 = uniforme (comportamiento viejo).\n- **Pozo con corrimiento**: al inclinar, además de elongarse 1/cosθ, el pozo se DESPLAZA colina abajo `R·(1/cosθ−1)` — el centro del elipse ya no queda clavado en el eje.\n- **`bFloorFollowsBeam`** (D-Piso): suelo FICTICIO pegado a la luz — el pozo queda como tapa perpendicular al haz en su extremo (relativo, rota con la luz) y el láser/kill-fade de plano mundial se desactivan. Off = comportamiento mundo (default).\n- **`bShapedAperture` + `ApertureBoost`** (F-Fuente): banda de emisivo en el tope DEL PROPIO HAZ = la apertura brilla con la FORMA real (rendija→línea, caja→rectángulo, wobble/spread incluidos). Complementa o reemplaza al disco `SourceGlow`.\n- **`bGradient` + `GradientColor` + `GradientAmount`** (B-Luz): tinte hacia el final del haz (lerp por t). Default: ámbar profundo, apagado.\n- **`SM_ShaftBox` v2**: malla densa (sección 48 pts con flats subdivididos ×31 anillos, 2880 tris) y **normales compensadas por el espejo Y del importador OBJ** — la v1 tenía caras negras porque el Fresnel SATURA el dot antes del 1−x (dot<0 → 0 exacto, el Abs no rescata). "Delgado o cuadrado" = escala X/Y del actor.\n- ⚠ **Rangos min/max de sliders: el MCP no expone la metadata UIMin/UIMax de variables BP.** Rangos recomendados (fijarlos en el editor si se quieren duros): Spread 0–40 · Intensity 0–4 · EdgeSoft 0.5–8 · LengthFade 0.3–4 · TipSoft 0–0.4 · Smoke/WobbleAmount 0–1 y 0–0.15 · WobbleFreq 0.01–0.2 · WobbleTaper 0–3 · WobbleStretch 0.2–3 · FloorGlowScale 0.2–4 · FloorGlowIntensity 0–2 · LaserAmount 0–6 · LaserWidth 1–12 · SourceGlowScale 0.5–3 · SourceGlowIntensity 0–0.8 · ApertureBoost 0–8 · GradientAmount 0–1.\n\n## 🆕 2026-09-03 (v7) — LA VERSIÓN VERSÁTIL: two-sided, Spread, láser, pozo/fuente, selector de forma y meshes bañados
Sesión larga con Beltrán iterando en vivo sobre `/Game/TestMeshes` (su cuarto oscuro grande envuelve el PlayerStart; carpeta outliner `LightShaftTest`). El BP quedó como el "EasyFog de haces" que pidió. **Todo compilado y guardado; sin visor.**

**Material `M_LightShaft` (nuevo en v7):**
- **TwoSided + `Abs` en la silueta** (`OneMinus_0 → Abs_0 → Power_1`): el haz se ve DESDE ADENTRO (pedido: vivir dentro del haz). Sin el Abs las caras traseras daban emisivo 0. ⚠ two-sided = ×2 fill — vigilar en APK.
- **`Spread`** (0 = tubo): apertura de cono por WPO — desplaza vértices radialmente según (1−t) en espacio local→world. CUALQUIER malla (cilindro, caja) se abre como cono. El bloque cuelga de `Add_12` → WPO (sumado al wobble).
- **Modo LÁSER** (`LaserAmount`/`LaserWidth`/`LaserFloorZ`): banda de emisivo reforzado donde la superficie cruza la altura del piso → línea brillante en el contorno de contacto que **hereda wobble y spread gratis** (se evalúa sobre la superficie ya desplazada). No pasa por el DepthFade (se sumó después de `Multiply_41`, en `Add_13`).
- `SourceGlowIntensity` alto satura el tonemapper y VIRA A ROSA (medido: 1.5×color×CoreBr 5). Rango sano ≤0.8.

**BP — perillas nuevas (cat. A - Haz):** `ShapeIndex` (−1 = respetar `Mesh` manual · 0 cono · 1 cilindro · 2 rectángulo) · `Spread` · `bLaserMode` + `LaserAmount` (2) + `LaserWidth` (4) · `bShowFloorGlow` + `FloorGlowScale` + `FloorGlowIntensity` + `FloorZ` · `bShowSourceGlow` + `SourceGlowScale` (1.15) + `SourceGlowIntensity` (0.8) · `bDriveMPC`.
**Componentes nuevos:** `FloorGlow` (Plane bajo Beam, `MI_FloorGlow`) = el pozo de luz: aterriza solo en `FloorZ`, **se orienta hacia donde cae el haz y se elonga 1/cosθ** (+ aporte del Spread) — la corrección de perspectiva que pidió Beltrán al inclinar el cono. `SourceGlow` (Plane en el tope, `M_ApertureGlow_SC`) = el disco fuente, hereda la inclinación como luminaria real.
**UCS:** `ApplyShape → IsValid(Mesh) → ApplyLook → ApplyFloorGlow → ApplyLaser → ApplySourceGlow → ComputeMPC → PushMPC`.

**🔦 MESHES BAÑADOS POR EL HAZ (`MPC_LightShaft` + `M_BeamReceiver_SC`):** el BP con `bDriveMPC=true` publica pos/dir/color/radio/spread/rango/láser/floorZ del haz en el MPC (`ComputeMPC` calcula a variables, `PushMPC` empuja — construido por cirugía con `declaring_class=KismetMaterialLibrary` para clavar el overload de Collection). Cualquier mesh con `M_BeamReceiver_SC` (o un material que copie su bloque) se tiñe según qué tan dentro del cono está + recibe la banda del láser. **Un solo slot Beam0** — un `bDriveMPC` a la vez; multi-haz = pendiente. Verificado en editor con cubo de prueba (`LS_ProbeCube`).

**Extras del cuarto:** `M_FogVeil_SC` (velo translúcido con `T_smoothRadial_mask` de EasyFog + DepthFade; 2 planos colocados tapan el fondo) · **`NS_VoidDust` reusado** para el polvo (2 instancias — se ve, sprites CPU) · `SM_ShaftBox` = **tubo recto de sección rectangular con esquinas redondeadas** (28×21, normales suaves, generado por `gen_shaftbox.py` → OBJ → import; el Spread le pone el cono). El disco/línea de apertura sueltos se retiraron (los reemplaza `SourceGlow`).

**🆕 v7.1 (misma jornada) — el haz REBOTA donde choca + láser real sobre receptores:**
- **`FloorFadeSoft`** (25) en `M_LightShaft`: el haz se apaga suave por debajo de `LaserFloorZ` (=`FloorZ` del BP). **Subir `FloorZ` al tope del objeto que recibe = el haz se corta ahí, el pozo aterriza arriba y el láser lo rodea a esa altura** — un solo slider hace el "rebote". El término va ANTES del add del láser, así el láser sobrevive en el plano. Pendiente: `bAutoFloor` con line-trace en el CS para detectarlo solo.\n- **Láser del receptor = distancia al casco del cono** (no banda de altura): la curva se dibuja sobre la cara que recibe (boceto de Beltrán: trepa la cara y rodea por el piso), con wobble propio (`RingWidth` 3,5 · `RingWobble` 2 · `RingFreq` 0,05, 2 senos world-space animados). 🔴 La trampa que costó 3 iteraciones: **el nodo Sine multiplica por 2π** (gotchas) — sin `period=2π` el trazo se rompe en puntitos. ⚠ El wobble del aro receptor NO es matemáticamente el mismo que el del haz (fórmulas distintas) — se parecen, no calzan pixel a pixel.\n- Boost del láser sobre receptores ×12 (el ×2 original quedaba ahogado por el baño general).\n\n**🆕 v7.2 (misma jornada) — bAutoFloor + carácter del wobble:**
- **`bAutoFloor`** (off): `ResolveFloor` en el CS traza (LineTraceByChannel, **`bTraceComplex=true`** — imprescindible: el cubo del motor es colisionador SÓLIDO y un rayo nacido adentro devuelve initial-overlap; complex lo vuelve hueco) desde 8% bajo la fuente, a lo largo del eje, y escribe `FloorZ` con el primer impacto → el haz se corta, el pozo aterriza y el láser rodea LO QUE SEA que el haz toque, sin tocar nada a mano. ⚠ Se re-evalúa al tocar cualquier perilla de la instancia (rerun del CS), NO al mover el objeto de abajo. ⚠ Si la fuente nace muy enterrada en geometría, el 8% puede no alcanzar a despejarla (ajustar el 0.08 en `ResolveFloor`).
- **`WobbleVariety`** (1): peso del 2º seno del wobble — **0 = ondulación de un solo seno, simétrica/regular**; 1 = orgánica. **`WobbleStretch`** (1): multiplica la frecuencia espacial del seno a lo largo — **<1 = ondas largas ("lineal")**, >1 = anillos apretados. Ambas se empujan desde `ApplyLaser`.
- UCS final: `ApplyShape → ResolveFloor → IsValid(Mesh) → ApplyLook → ApplyFloorGlow → ApplyLaser → ApplySourceGlow → ComputeMPC → PushMPC`.

**Pendiente:** juicio en visor (fill del two-sided, DepthFade/CamFade/aro en APK, costo MPC) · multi-haz en el receptor · estrías tipo láser en el humo (`SmokeStretch`) · si `bAutoFloor` debe seguir a un objeto que se MUEVE en runtime, llamar `ResolveFloor`+cadena desde Tick o un timer (hoy es solo construcción).

## 🆕 2026-09-03 (v6) — CamFade + disco de apertura + cuarto de look-dev
Sesión de exploración de haces (pedido de Beltrán con refes de sol cálido entrando a un interior oscuro). ⚠ La sesión ARRANCÓ reconstruyendo este sistema desde cero en `/Game/SoulCharger/Tests/LightShafts/` porque **este BP no figuraba en `assets-existentes.md`** (ya corregido); el duplicado se detectó al documentar, se consolidó acá y se borró. Lo que quedó:
- **CamFade en `M_LightShaft`**: fundido por cercanía de cámara (`distance(cam, pixel)` → `saturate((d−Near)/Range)` multiplicando el emisivo). Ataca el "visto desde adentro desaparece" de la nota one-sided: ahora el haz se funde suave ANTES de que la cabeza lo cruce. Perillas `CamFadeNear` (30) · `CamFadeRange` (80) — **solo en el material**, el BP no las expone como variables (defaults del material; agregar al BP si hace falta por instancia).
- **`M_ApertureGlow_SC`** (`Tests/LightShafts/`) — el "disco fuente" que pedía el TODO: disco + halo radial procedural en un Plane, unlit aditivo TwoSided. Perillas: `GlowColor` · `CoreRadius` (0,35) · `CoreSoft` (0,15) · `CoreBrightness` (5) · `HaloPower` (2,2) · `HaloBrightness` (0,8). Vende el óculo (refe Panteón) y la línea de la rendija.
- **Cuarto de look-dev en `/Game/TestMeshes`** (carpeta `LightShaftTest` del outliner): cubo 14×14×6,5 m con `M_DarkRoom_SC` (unlit oscuro cálido, TwoSided) en (0, 8000, 325) + 3 viñetas con instancias de ESTE BP: `BeamTest_Oculus` (cono 2,2/2,2/12, vértice enterrado sobre el techo para que el haz nazca ancho), `BeamTest_Curtain` (cilindro 2,4/0,35/6,8, roll 12° = cortina de rendija) y `BeamTest_Column` (cilindro 1,3/1,3/6,5) + discos/línea de `M_ApertureGlow_SC` en el techo.
- 🔴 **El wobble NO escala**: `WobbleAmount` 0,05 × ObjectRadius a escala 12 = ±30 cm sobre 21 anillos → silueta dentada "vela derretida". En haces grandes y quietos va **0**; el default 0,05 es para la escala ~3× de la instancia original.
- 📸 Recetas de encuadre: viñetas se juzgan con cámara en (30, 7360, 200) yaw 90 pitch 10. El techo del cuarto oculta el vértice: **enterrar siempre el extremo superior de la malla en la geometría** (el gap "haz que no toca el techo" es eso).
- Pendiente igual que antes: juicio de Beltrán en editor/visor, DepthFade en APK, y ahora también CamFade en estéreo.

## 🆕 2026-08-20 (v5) — el reporte de VR: banding + noise lavado
Captura de Beltrán desde el visor: **franjas horizontales** y el noise casi desaparecido.
- **Franjas = banding de 8 bits** (sin HDR móvil, el degradado aditivo se cuantiza — la MISMA queja que `M_TurrellGradient`). Fix igual: **dither R2 en espacio de pantalla** (`frac(dot(pixel, (0.7549, 0.5698))) − 0.5`) multiplicando el emisivo. Perilla **`DitherAmt`** (0,08); `DitherTemporalAA` NO sirve (no hay TAA en Quest).
- **Noise lavado = los MIPS**: a distancia/ángulo VR la textura cae a mips chicos y las octavas finas mueren. Fix: **mip 0 forzado en las dos muestras** (`mipValueMode = TMVM_MipLevel, constMipValue = 0` — `mipGenSettings` de la textura no se puede escribir por MCP). 256² suave → el aliasing es imperceptible.
⚠ `DitherAmt` es la palanca si el grano se nota: 0,05 fino · 0,12 grueso. El dither NO se aprecia en el editor (ahí no hay banding): se juzga en el visor.

## 🆕 2026-09-04 — `BP_ShadowShaft_SC`: el haz NEGRO, y el barrido cónico del estudio de sombra

**El haz oscuro es un DUPLICADO del BP, no una variante por parámetro.** `BP_ShadowShaft_SC` (mismo folder) = `BP_LightShaft_SC` duplicado, con `M_ShaftDark_SC` en el `overrideMaterials` de su componente `Beam` y `bShowFloorGlow` / `bShowSourceGlow` / `bDriveMPC` en false. Funciona porque el BP **no crea un MID propio**: empuja parámetros con `SetXParameterValueOnMaterials`, que honra el material asignado al componente (ver gotcha 299).

`M_ShaftDark_SC` = duplicado de `M_LightShaft` con `BLEND_Translucent`, `Emissive = DarkColor` (negro) y `Opacity = saturate(dot(Add_14,(0.34,0.34,0.34)) × DarkStrength)` — o sea la misma cadena de densidad del haz, pero pintando oscuridad. `Intensity` sigue siendo la perilla de densidad.

**Valores que dieron la lectura de la refe** (contraluz/eclipse, negro sobre blanco, sin plano ni horizonte):
`EdgeSoft 0.55` (⚠ la perilla decisiva — arriba de ~1.5 el cono se vuelve niebla y se pierde el borde duro que hace la refe) · `Intensity 2.6` · `LengthFade 3.0` · `TipSoft 0` · `Spread 0` · `SmokeAmount 0` · escala `(3,3,9)`.

**Colocación con la punta clavada en un objeto** (fórmulas en gotcha 298): `rot = MakeRotFromZ(−u)`, `loc = punta + u·(50×escalaZ)`.

### El barrido cónico — vive en `BP_ShadowStudy_SC`, no en el haz
El haz sigue siendo un actor tonto; quien lo apunta es el estudio de sombra, que lo toma por referencia. Categoría **H - Barrido** en `BP_ShadowStudy_SC`:

| Variable | Default | Qué hace |
|---|---|---|
| `Shaft` | — | referencia al `BP_ShadowShaft_SC` del nivel |
| `SweepAxisPitch` / `SweepAxisYaw` | 38 / 0 | **la diagonal**: eje central del cono de barrido |
| `SweepAngle` | 22 | apertura del barrido (cuánto se separa del eje) |
| `SweepPhase` | — | posición en el círculo; **perilla de previsualización en el editor** |
| `SweepSpeed` | 5 | grados/s cuando corre |
| `bSweep` | true | on/off de la animación |
| `ShaftHalf` | 450 | semi-largo del haz = 50 × su escala Z (si cambiás la escala del haz, actualizar) |

- **`AimShaft`** (llamada al final del UCS **y** desde el Tick): arma el eje con `MakeRotator`, saca `eje = ForwardVector` y `perp = UpVector` (perpendicular garantizado, sin Cross ni Normalize), abre `SweepAngle` alrededor de `perp` y gira `SweepPhase` alrededor de `eje` → dirección `u`. Después coloca y orienta el haz con las dos fórmulas de arriba.
- **`StepSweep(DT)`** (Tick): avanza `SweepPhase` y llama a `AimShaft`. Se enganchó al `EventTick` con **un solo nodo** (cirugía), no re-escribiendo el EventGraph.
- Como `AimShaft` también corre en el Construction Script, **mover `SweepPhase` en el detalle mueve el haz en el viewport** — se autora mirando, sin Play.
- Verificación de que el cono es real y no un giro plano: con `SweepAxisPitch 38`, las fases 0/90/180/270 caen en `(329,169,257) (225,0,390) (329,−169,257) (433,0,124)` — las cuatro a 450 cm de la esfera, alrededor del eje inclinado, y ninguna bajo el suelo.

🟡 Sin probar en visor.

## 💓 2026-09-08 — `bPulse`: el haz se prende y se apaga, y el pozo del piso con el
Pedido de Beltran sobre su composicion de ~20 haces: *"que la intensidad vaya de 0 al valor que tiene cada actor, para que se vayan prendiendo y apagando en distintas velocidades. Que tambien afecte a la intensidad de la iluminacion del piso, asi se prende y apaga suavemente junto con el cono"*.

### Perillas (cat. *C - Vida*)
| Perilla | Rol | Default |
|---|---|---|
| **`bPulse`** | enciende la animacion. **Off = comportamiento anterior exacto** | false |
| **`PulseSpeed`** | **pulsos por segundo** (0,06 ≈ 16 s por ciclo · 0,22 ≈ 4,5 s) | 0,25 |
| **`PulsePhase`** | 0–1, corrimiento — es lo que evita que 20 haces respiren al unisono | 0 |

### Como esta hecho
Funcion **`StepPulse`** llamada desde `EventTick`:
```
k = MakePulsatingValue(GetGameTimeInSeconds, PulseSpeed, PulsePhase)   // 0..1
if (bPulse):
    Beam.Intensity      = Intensity * k
    FloorGlow.GlowColor = Lerp(Negro, BeamColor, FloorGlowIntensity * k)
```
💡 **`Math|Float|MakePulsatingValue` es un nodo del motor** que hace justo esto (tiempo, pulsos/seg, fase) → 0..1. Evito armar seno + escalado a mano.
💡 **El piso se apaga junto con el cono sin tocar su material**: `GlowColor` ya era `BeamColor × FloorGlowIntensity`, asi que basta con escalar ese producto por la misma `k`. `Lerp(Negro, C, x)` **es** `C·x` exactamente (el lerp extrapola, sirve tambien con x>1).
⚠ Se dejo **fuera el `SourceGlow`** (el disco de la fuente): Beltran pidio cono + piso. Si al verlo el disco queda encendido mientras el haz se apaga, es **una linea mas** en `StepPulse` con `SourceGlowIntensity`.

### 🔩 Dos trampas del MCP que costaron intentos (y quedan como receta)
1. 🔴 **El getter de un bool NO lleva la `b`**: `bPulse` se llama **`Variables|C-Vida|GetPulse`** en el `type_id` (Unreal usa el nombre de display). `GetbPulse` no existe. **Descubrirlo es `find_node_types` con filtro**, no adivinar.
2. 🔴 **`write_graph_dsl` SI puede crear operadores promotables (`*`, `+`) que `create_node` NO puede** — pero no todos: `Math|Color|LinearColor*LinearColor` fallo igual. Salida: `Math|Color|Lerp(LinearColor)`, que si es creable.
💡 **Y la leccion de metodo:** el grafo se armo con **`add_function_graph` + `write_graph_dsl` en UNA llamada**, en vez de ~45 llamadas de cirugia sobre el EventGraph. **Un grafo NUEVO es exactamente el caso donde el DSL esta permitido** (la regla de oro prohibe reescribir uno existente, no crear uno).

### Estado
Los **20 haces** de la composicion quedaron con `bPulse = true` y velocidad/fase **repartidas de forma determinista**: `speed = 0,06 + 0,16·frac(i·0,381966)` y `phase = frac(i·0,618034)` — el mismo truco de razon aurea que usa `BP_RingTunnel_SC` para desincronizar sus anillos. Rango: **4,5 a 16 segundos por ciclo**.
⚠ Los tres valores **nacieron en 0** en las instancias (la trampa de siempre) — por eso hubo que escribirlos actor por actor; con `PulseSpeed = 0` el pulso no se mueve aunque `bPulse` este en true.
✅ Canario **103 → 103** en las dos tandas de script, cero errores.


## 🌬️ 2026-09-17 — el cono RESPIRA (`StepBreath`, mecánica portable [[BP_BreathManager_SC]])
Pedido de Beltrán para la estación 1 de la galería: *"que controle apertura del cono de los haces de luz"*.

- **Perillas** (cat. *R - Respiracion*, instance-editable, **0 = apagado = comportamiento anterior exacto**): `BreathSpreadIn` · `BreathSpreadOut` = cuánto cambia el **radio del extremo** a inhalación / exhalación plena.
- **EventTick**: `StepPulse` → `GetScalarParameterValue(MPC_Breath, "Signed")` (nodo de COLECCIÓN, creado por cirugía con `declaring_class=KismetMaterialLibrary`) → `StepBreath(S)`.
- **`StepBreath(S)`**, solo si alguna ganancia ≠ 0:
```
m         = 1 + max(S,0)·In + max(−S,0)·Out
SpreadEff = max((50 + Spread)·m − 50, 0)          → "Spread" al Beam
si bFloorFollowsBeam: FloorGlow.RelativeScale = FloorGlowScale·(1 + SpreadEff·0,02)   (la fórmula de ApplyFloorGlow)
```
- **Por qué el radio y no `Spread`**: los 20 haces de la estación tienen `Spread` 5 o 54,8. Un multiplicador sobre `Spread` dejaba quietos a los angostos; escalando el radio del extremo (`50 + Spread`) se abren todos en proporción y el pozo usa el mismo `m`. El clamp en 0 hace que cerrar un cono termine en **tubo**, no en embudo invertido.
- **Instancias**: las 20 de `GAL_0` con `In 0,5` / `Out −0,45`. Las 3 de `GAL_8` quedan en 0.
- ✅ **Medido en PIE con la respiración de prueba** (S = −1 / 0 / +1): haz angosto `Spread` 5 → **0 / 5 / 32,5** · haz ancho 54,8 → **7,66 / 54,8 / 107,25** · pozo del ancho ×1,45 / autorado / ×3,96. Números idénticos a la fórmula; cero `Accessed None`.
- ⚠ Limitaciones: el pozo solo acompaña con `bFloorFollowsBeam` (el modo de toda la estación 1); en modo mundo no se reescala. `MPC_LightShaft` (receptores bañados) no se entera del spread respirado. Inhalar ensancha translúcidos aditivos → **más fill: medir en visor**. Es CPU: solo se ve en PIE o visor (la vista previa del manager no lo mueve en el editor).


### 🌬️ 2026-09-17 (2ª pasada) — curva SUAVE y rango exagerado
Beltrán tras probar: *"llegó muy duro a los valores máximos y mínimos, no suave como con la esfera"* y *"un poco más exagerados"*.
- **Causa (en el manager, no acá):** `BreathSigned` era `clamp(gain·y)` → con ganancia 1,5 una respiración normal chocaba contra ±1 y quedaba plana. Ahora es `k·y/(1+(k−1)|y|)` (techo suave, `SignedGain` 2).
- **Mapeo nuevo del consumidor** (sin quiebre en 0 aunque las ganancias sean asimétricas): `m = 1 + S·lerp(−Out, In, smoothstep((S+1)/2))`. `In` = fracción a inhalación plena, `Out` = a exhalación plena, igual que antes.
- **Intensidad (pedido: "de 0 a su valor")**: perilla nueva **`BreathIntensity`** (0..1 = cuánto toma la respiración el control). `StepBreath(S, On)`: `k = lerp(k_reloj, smoothstep((S+1)/2), saturate(On·BreathIntensity))` → `Intensity·k` al Beam y `GlowColor·k` al pozo (el mismo canal que `StepPulse`, que corre antes en el mismo tick). Sin umbral sigue el pulso de siempre.
- **La apertura pasó a su propia función `BreathSpread(S)`** con piso suave (`R−50` con una rampa cuadrática de ±4 hacia 0, en vez del `max(…,0)` duro).
- **EventTick**: `StepPulse` → `MPC.Signed` → `MPC.On` → `StepBreath(S, On)`. 🔴 Trampa: agregar un parámetro a una función NO refresca el nodo de llamada existente (*"Could not find a pin for the parameter On"*): hubo que borrar la llamada y crearla de nuevo.
- **Valores (20 haces)**: `SpreadIn 0,8` · `SpreadOut −0,7` · `BreathIntensity 1`.
- ✅ **Medido en PIE** (haz ancho, respiración de prueba): Signed −0,85 ↔ +0,85 con cimas redondeadas · Intensity **0,02 ↔ 1,08** (autorado 1,1) · Spread 0 ↔ 126, llegando al tubo en rampa (5,2 → 1,0 → 0).


### 🌬️ 2026-09-17 (3ª pasada) — acompañar la respiración lenta, suavidad de resorte, más exagerado
Beltrán: *"si hago una respiración lenta deben demorarse más en llegar al máximo o mínimo, acompañando mi movimiento"* · *"sigo sintiendo que está un poco duro"* · *"los valores más exagerados, menos el metaball"*.
- **Causa (en el manager):** (1) `HorizTau` 3 s: la base del band-pass alcanzaba a una respiración lenta a mitad de la inhalación → el pico llegaba ANTES del final; (2) dos saturaciones encadenadas (`x/(1+|x|)` del nivel y el techo suave de `SignedGain`) = una sola muy comprimida: casi todo el recorrido quedaba pegado al máximo.
- **Arreglo (manager):** `HorizTau` **6**; `S` sale del band-pass CRUDO en cm (`x = (HFast−HSlow)·SignedGain`, `SignedGain` 1 = 1 cm) con codo suave `x/(1+|x|³)^(1/3)` (lineal hasta ~0,7) y pasa por un **resorte críticamente amortiguado** (`SmoothFreq` 6): velocidad continua, sin rebote.
- ✅ Medido en PIE con respiración de prueba de 10 s: el máximo llega al final de la media onda (no antes), la velocidad de `S` sube y baja suave.
- **Valores (20 haces)**: `SpreadIn 1,2` · `SpreadOut −0,85` · `BreathIntensity 1`. Intensidad medida: 0,02 → 1,08 siguiendo la curva lenta.

### 🌬️ 2026-09-17 (4ª pasada) — intensidad PROPORCIONAL
Beltrán: *"todo llega demasiado rápido a sus destinos"*. Además del arreglo en el manager (ganancia automática por usuario), la intensidad usaba `smoothstep((S+1)/2)`: la S de esa curva es empinada en el centro (de S = −0,5 a +0,5 la intensidad iba de 16 % a 84 %) → llegaba rápido. Ahora `k = (S+1)/2` **lineal**: la intensidad sigue la respiración en proporción; los extremos suaves los da `S` (codo + resorte).
