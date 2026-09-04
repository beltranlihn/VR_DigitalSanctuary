# BP_FogSlab_SC + M_FogSlab_SC — el exponential fog FALSO en una losa (Core/Light/)

> Creado 2026-09-04, pedido de Beltrán: *"un plano con un material que, donde lo pongamos, genere un depth sobre todos los elementos que toca. Sería un falso exponential fog, donde podamos manipular parámetros."*
> **Estado: 🟡 material compilado, BP compilado, maqueta vista en el viewport. Falta el juicio de Beltrán y el visor.**

## Qué es y por qué no es el `M_FogVeil_SC` de antes
`M_FogVeil_SC` (el velo que ya existía) es un plano translúcido con máscara radial y un `DepthFade`: **tapa el fondo**, nada más — tres perillas (`Density`/`DepthFadeDist`/`FogColor`). Sigue sirviendo para eso y no se tocó.

`M_FogSlab_SC` hace lo otro: **acumula niebla según cuánta profundidad hay DETRÁS de la losa**. La idea clave es que **el mismo nodo `DepthFade` sirve para dos cosas distintas según la distancia que se le dé**:
- con una distancia CHICA (`ContactFade`, ~90 cm) → **intersección blanda**: donde la losa corta un objeto no queda línea dura, se disuelve. Es el rayado del croquis de Beltrán.
- con una distancia GRANDE (`ThicknessDist`, ~2500 cm) → **espesor**: donde hay mucho aire detrás la losa se pone opaca, donde hay una pared pegada se pone transparente. **Eso ES la niebla**: lo lejano se lecha, lo cercano queda limpio, sin Exponential Height Fog y sin volumétricos (que en Quest no corren).

Se multiplican los dos, y encima va la forma exponencial: `1 − (1 − x)^ThicknessPow`.

## El material `M_FogSlab_SC` — unlit · translúcido · **two-sided** · Full Precision (expresiones)
La opacidad es un producto de siete términos, y aparte hay un WPO de ola, cada uno una perilla independiente:

| Término | Cómo | Perillas |
|---|---|---|
| **Espesor** | `1 − (1 − DepthFade(ThicknessDist))^ThicknessPow` — la niebla que se acumula detrás de la losa | `ThicknessDist` (2500) · `ThicknessPow` (1,6) |
| **Contacto** | `DepthFade(ContactFade)` — la losa se disuelve donde toca geometría | `ContactFade` (90) |
| **Bruma por distancia** | `lerp(1, 1 − e^(−HazeDensity · (distCámara − HazeStart)), HazeAmount)` — la fórmula literal del fog exponencial, aplicada a la distancia a la cámara. **Apagada por defecto** (`HazeAmount` 0) porque el término de espesor ya hace casi todo | `HazeAmount` (0) · `HazeStart` (300) · `HazeDensity` (0,0006) |
| **Caída por altura** | `lerp(1, saturate(e^(−HeightFalloff · (z − HeightTop))), HeightAmount)` — niebla baja: densa abajo, se afina hacia arriba. `HeightTop` lo calcula el BP como *Z de la losa + `HeightOffset`* (o sea, siempre relativo al plano, no a coordenadas del mundo) | `HeightAmount` (0) · `HeightOffset` (0) · `HeightFalloff` (0,004) |
| **Fade de cámara** | `saturate((distCámara − CamFadeNear)/CamFadeRange)` — no te tapa la cara al atravesarla | `CamFadeNear` (60) · `CamFadeRange` (120) |
| **Borde del plano** | máscara sobre la UV, **rectangular por defecto**: `d = lerp(max(|u|,|v|), dist(uv,centro), EdgeRound)` y `m = saturate((1 − d) · EdgeSoft)`, y al final `lerp(1, m, EdgeAmount)`. Con `EdgeRound` en 0 el difuminado sigue el rectángulo del plano (lo que pidió Beltrán); en 1 vuelve al círculo. `EdgeSoft` bajo = borde muy difuso, alto = borde duro (14 ya es un rectángulo neto). `EdgeAmount` en 0 apaga el difuminado por completo | `EdgeRound` (0 = rectángulo) · `EdgeSoft` (2,5) · `EdgeAmount` (1) |
| **Vida** | 2 muestras de `T_ShaftNoise` panneadas en direcciones opuestas, mezcladas 65/35, en **espacio de MUNDO** (escalar el actor no estira el ruido, y varias losas se ven coherentes entre sí) | `NoiseAmount` (0,35) · `NoiseScale` (0,0025) · `NoiseSpeed` (0,5) |
| **Ola** (WPO) | `VertexNormalWS × (0,6·sin(x·WaveScale + t·WaveSpeed) + 0,4·sin(0,73·y·WaveScale − 1,37·t·WaveSpeed)) × WaveAmount` — dos senos de razones no enteras, sin textura y sin muestreo en el vertex shader. Ondula la SUPERFICIE, así que **exige una malla subdividida**: el default es **`SM_FogSlab`** (257×257 = 131k tris, mide 100×100 como el `Plane` del motor, así que la cuenta de `SlabSize÷100` no cambia). Alternativas más livianas en la variable `Mesh`: `SM_CloudPlane` (129×129, 32k tris) o el `Plane` del motor (2 tris, sin ola). ⚠ `Sine`/`Cosine` con `period = 6.283185` o la entrada se multiplica por 2π | `WaveAmount` (25 cm; 0 = plano) · `WaveScale` (0,004; más chico = olas más grandes) · `WaveSpeed` (0,4) |

Emisivo = `FogColor × Brightness` (unlit, así que el color es literal — salvo el grade del post-process de la escena, que en `/Game/TestMeshes` es muy cálido y lo vira a naranja).

⚠ **Two-sided a propósito**: la losa se ve desde los dos lados y se puede atravesar. Duplica fill — es lo caro de esto en Quest.

## El BP
**El tamaño se autora en centímetros, no con la escala del actor**: `SlabSizeX` / `SlabSizeY` (cat. *A - Forma*, default 2000 = 20 m) que la función `ApplyEdges` traduce a escala del componente (÷100). El actor va en escala 1. ⚠ Si el actor tiene escala ≠ 1, se multiplica con la del componente.

Un solo componente `Fog` (StaticMeshComponent, `SM_FogSlab` por default, sin sombras, sin colisión, `bUseAsOccluder` off, **`boundsScale` 2** porque el WPO saca vértices de los bounds y si no hay pop de culling). El Construction Script encadena tres funciones: **`ApplyFog`** (las perillas de niebla) → **`ApplyEdges`** (tamaño y borde) → **`ApplyWave`** (la ola). La malla es una variable (`Mesh`, cat. *A - Forma*): plano para una capa, **`Cube` para una CAJA de niebla que se puede recorrer por dentro** (el material es two-sided).

Categorías de variables: `A - Forma` (Mesh/SlabSizeX/SlabSizeY) · `A - Color` (FogColor/Brightness) · `B - Niebla` (Density/ThicknessDist/ThicknessPow) · `C - Bruma` (HazeAmount/Start/Density) · `D - Contacto` (ContactFade/CamFadeNear/CamFadeRange) · `E - Altura` (HeightAmount/HeightOffset/HeightFalloff) · `F - Borde` (EdgeRound/EdgeSoft/EdgeAmount) · `G - Vida` (Noise*) · `H - Ola` (WaveAmount/WaveScale/WaveSpeed).

## 🔴🔴🔴 LA LOSA NO PUEDE VER UN TRANSLUCIDO. Nunca. Y no es orden de dibujo
Beltran quiso que el oceano de nubes se perdiera en la niebla de una losa, y el resultado fue que **la losa se dibujaba opaca encima del oceano**. Se probo con `SortPriority` y no cambio nada — con razon.

**La causa:** el espesor de esta losa sale de dos nodos **`DepthFade`**, que leen el **buffer de profundidad**. Un material `BLEND_Translucent` **no escribe profundidad**. Entonces, donde esta el oceano, la losa lee "no hay nada atras hasta el infinito" → acumula espesor maximo → se pone **completamente opaca**. No esta tapando al oceano por orden: esta reaccionando a un vacio.

🚩 **La regla general, que vale para todo el toolkit:** `DepthFade`, `SceneDepth` y cualquier efecto que "reaccione a lo que hay detras" **solo ve geometria OPACA**. Los velos, la nube, los haces y la propia losa son invisibles entre si. Si un efecto tiene que responder a un translucido, **la cuenta hay que hacerla dentro del material de ESE translucido** — no hay truco de orden que lo arregle.

✅ Para el oceano se eligio la via directa: `M_CloudPlane_SC` tiene ahora **su propia niebla por distancia** (cat. *C - Niebla* en `BP_CloudPlane_SC`). La losa y el oceano siguen siendo objetos separados y combinables; simplemente cada uno calcula su niebla. (La alternativa evaluada y descartada por ahora era una MPC donde la losa publica sus parametros y el oceano los lee — el patron de `MPC_LightShaft` + `M_BeamReceiver_SC`.)

## 🔴 `SortPriority` — mezclar la losa con OTRO translucido (el oceano, un velo, un haz)
Pedido de Beltran (2026-09-04): *"quiero poner un fog slab para que el oceano se pierda en un fog etereo, pero la textura del oceano se renderiza por arriba"*.

**Dos translucidos no se ordenan por profundidad de pixel, se ordenan por ACTOR**, y con la misma prioridad el motor decide por la distancia al origen de los bounds. El oceano tiene bounds enormes centrados cerca de la camara, asi que le gana siempre a la losa — **por mas lejos que este la losa**.

✅ El unico lever es **`TranslucencySortPriority`**, ahora expuesto como variable **`SortPriority`** (cat. *I - Orden*, instance-editable) que el UCS empuja al componente con `ApplyFogSort`. **Mas alto = se dibuja despues = va encima.** `BP_CloudPlane_SC` tiene la misma perilla (cat. *B - Orden*).

Receta para el oceano que se pierde en niebla: oceano en **0**, losa en **1**. Verificado A/B en el viewport: con 0 las crestas lejanas del oceano cortan la banda de niebla; con 1 la niebla las vela.

🚩 **Vale para cualquier par de translucidos de la obra** — velos, haces, nube y losa. Si algo translucido "aparece delante de lo que no corresponde", esta es la perilla, no el material.

## Cómo se usa
- **Capa de niebla baja** (el croquis de la derecha): losa horizontal, `HeightAmount` ~0,85 y `HeightFalloff` ~0,006 → densa abajo, se afina hacia arriba; los objetos emergen disolviéndose.
- **Bruma de distancia** (el croquis de la izquierda): losa vertical grande delante de la escena. Lo que está pegado detrás sale limpio, lo lejano se lecha. Es el sustituto directo del Exponential Height Fog.
- **Volumen recorrible**: `Mesh` = `Cube`, escala la que haga falta.
- 🔴 **La densidad que importa es por METRO, no por malla.** Los 256 segmentos se reparten sobre `SlabSizeX`, así que una losa grande factea con la misma `WaveScale` que una chica resuelve limpia. Regla verificada A/B: hacen falta ~16 segmentos por longitud de onda → **`WaveScale` ≲ 100 / `SlabSizeX`** con `SM_FogSlab` (y la mitad, ≲50/`SlabSizeX`, con `SM_CloudPlane`). Medido: losa de 12.000 cm con `WaveScale` 0,006 → con la malla de 129 el horizonte sale DENTADO, con la de 257 sale en lomas redondeadas.
- **Ondulación suave**: `WaveAmount` 60-90 con `WaveScale` ~0,0015 da olas grandes y lentas (banco de niebla que respira); `WaveScale` ~0,006 da rizado fino. En 0 la losa es un plano perfecto.
- Apilar 2-3 losas paralelas da sensación de volumen al moverse — pero **cada una es una capa translúcida a pantalla completa**: es LA cuenta de fill-rate en Quest. Medir antes de pasar de dos.

## TODO
- [ ] Juicio de Beltrán y prueba en visor (fill-rate del two-sided, `DepthFade` en el APK — el mismo riesgo que arrastran el haz y la nube).
- [ ] Rangos UIMin/UIMax a mano en el editor (el MCP no expone esa metadata). Sugeridos: Density 0–1 · ThicknessDist 200–8000 · ThicknessPow 0,5–4 · ContactFade 0–400 · HazeAmount 0–1 · HazeDensity 0–0,003 · HeightAmount 0–1 · HeightFalloff 0–0,02 · CamFadeNear 0–300 · CamFadeRange 20–400 · EdgeRound 0–1 · EdgeSoft 0,5–16 · EdgeAmount 0–1 · SlabSizeX/Y 100–20000 · NoiseAmount 0–1 · NoiseScale 0,0005–0,01 · NoiseSpeed 0–2 · WaveAmount 0–300 · WaveScale 0,0002–0,02 · WaveSpeed 0–2.
- [ ] `SM_FogSlab` son 131k triángulos por losa. La app es fill-bound (no vertex-bound) y el shader es unlit, así que se paga barato para una o dos losas — pero **no está medido en visor**: si el vertex shader apretara, bajar a `SM_CloudPlane` es un cambio de dropdown. Sin ola, `Mesh` = `Plane` del motor (2 tris).
- [ ] Si hace falta apilar capas, se puede agregar un `Layers`/`LayerSpacing` con 3-4 componentes fijos (se descartó en la v1 por la regla de BP mínimo).
