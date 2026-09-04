# BRIEF para Nico — tres efectos de material para Soul Charger

> **Cómo usar este documento:** abrí Claude Code en la raíz del repo y pedile que lea este archivo. Está escrito para que sea autosuficiente: tiene el contexto, las reglas, los materiales que hay que leer como modelo y la especificación completa de tus tres efectos. No hace falta que preguntes nada para empezar.
>
> Creado 2026-09-04 por Beltrán. El plan completo (los siete efectos y la galería) está en [`PLAN-GALERIA-EFECTOS.md`](PLAN-GALERIA-EFECTOS.md).

---

## 1. Qué estamos haciendo y por qué

**Soul Charger** es una obra de VR de meditación para **Meta Quest 3 standalone** (APK Android, renderer **móvil forward**). Estética tipo James Turrell: luz de color en el aire, vacíos oscuros, casi nada de geometría.

🔴 **La obra no tiene NI UNA luz.** Ni direccional, ni sky, ni niebla, ni volumétricos. **Todo el color sale de materiales emisivos unlit.** Esto no es una limitación que aguantamos: es lo que la hace parecerse a Turrell, y encima es lo más barato en móvil.

⚠ **La consecuencia práctica que ya nos costó una sesión:** sin luces, **cualquier material *lit* renderiza negro sobre negro**. Si traés un asset del motor o de un template, lo primero es mirarle el *shading model*.

**Lo que estamos construyendo ahora** es una **galería de efectos**: siete estaciones para *mirar* qué se puede lograr con materiales, y decidir después qué entra en la obra. Es look-dev puro.

🔴 **Nada se conecta al cuerpo del usuario todavía.** Ni manos, ni respiración, ni latido. Todo se anima **por reloj** o reacciona a la **distancia de la cámara** (que sale gratis en el material, sin cañería). Si se te ocurre atarlo a una señal del cuerpo: buena idea, pero es una etapa posterior.

**Tus tres efectos son los que siguen patrones que ya funcionan** en el proyecto. Vas a poder leer materiales nuestros y copiar la estructura en vez de inventarla. Los otros cuatro los hace Beltrán porque necesitan mallas generadas por script.

---

## 2. Cómo trabajás para que no nos pisemos

🔴 **`.uasset` y `.umap` son binarios: git no los mergea.** Si dos personas editan el mismo archivo, uno de los dos pierde el trabajo entero. Por eso:

- **Tu propio nivel de pruebas:** creá `/Game/SoulCharger/Maps/Tests/L_EffectTest_Nico` y trabajá SIEMPRE ahí. No abras ni toques `/Game/TestMeshes` (es el de Beltrán) ni los niveles de la obra.
- **Tu propia rama**, salida de la última de Beltrán.
- **Assets que creás vos y que son solo tuyos** (la lista exacta está en cada efecto). Nadie más los toca.
- 🔴 **NO toques:** `VR_Test/Config/` (cualquier `.ini`), `Core/Pawn/`, ni ningún BP o material que no esté en tu lista. Si creés que necesitás cambiar algo compartido, **pedilo** — no lo hagas.
- **Save All en Unreal ANTES de commitear.** Git ve el disco, no el editor sin guardar.
- **Cerrá Unreal antes de mergear o cambiar de rama** — con el editor abierto los `.uasset` quedan bloqueados y git falla a medias.
- Commiteá **hitos**, no micro-cambios (los binarios pesan).

**Los nombres de los assets son parte del contrato.** Usá exactamente los que dice cada ficha: cuando armemos la galería, el nivel va a buscarlos por nombre.

---

## 3. Convenciones obligatorias

Todo lo que construyas sigue el patrón probado de `BP_LightShaft_SC`: **componentes + variables instance-editable agrupadas por categoría + un Construction Script que empuja todo al material**, para que se vea en el viewport sin darle Play.

- Carpeta: `Content/SoulCharger/Core/Light/`. Nombres: `BP_*_SC`, `M_*_SC`, `SM_*`, `T_*`.
- Material **unlit**, translúcido o aditivo, con **Float Precision Mode = Full (expresiones)**.
- **Los tamaños se autoran en centímetros como variables**, y el Construction Script los traduce a escala del componente (`cm ÷ 100`). El actor queda en escala 1. *Lección pagada: usar la escala del actor hace que todo lo demás se estire con ella.*
- **Categorías de variables** con prefijo de letra para que salgan ordenadas en el panel: `A - Forma`, `B - Color`, etc.
- **Tracker desde el día 1** en `.claude/skills/unreal-vr/blueprints/<BP>.md`, y fila en `_INDEX.md` y en `references/assets-existentes.md` al terminar. No es burocracia: es cómo el Claude del otro sabe qué hiciste.

### Las trampas que te van a morder

Están todas documentadas en `.claude/skills/unreal-vr/references/gotchas.md`, pero estas cuatro son las que vas a pisar seguro:

1. 🔴 **`Sine` y `Cosine` multiplican la entrada por 2π.** Su `period` por defecto es 1, que significa "un ciclo por unidad de entrada", NO radianes. Toda frecuencia calculada sale ~6,28× más rápida. **Poné `period = 6.283185` en el nodo** y las entradas quedan en radianes. El síntoma engaña: parece un problema de precisión o de aliasing.
2. 🔴 **Un MID creado ANTES de que el material gane un parámetro nunca lo honra.** Si agregás un parámetro a un material y una instancia ya colocada no reacciona —aunque leas el valor y esté bien puesto—, es esto. **Se arregla recargando el nivel.** Un actor recién colocado sí funciona: ese es el síntoma que lo delata.
3. 🔴 **Si el material usa WPO, subí el `boundsScale` del componente a 2.** El WPO saca vértices fuera de los bounds y aparece *pop* de culling al girar la cabeza.
4. 🔴 **El `Fresnel` SATURA el producto punto antes del `1−x`.** Con una normal mirando para el otro lado el resultado es 0 exacto y un `Abs` posterior no rescata nada. Si necesitás que se vea desde los dos lados, el `Abs` va **dentro**, sobre el dot.

---

## 4. Leé estos tres materiales antes de escribir nada

Son los modelos. Están todos en `Core/Light/` y todos funcionan y están probados en visor:

| Material | Qué copiarle |
|---|---|
| **`M_ApertureGlow_SC`** | El **SDF de caja redondeada y círculo** con rotación (`BoxAngle`) y proporción (`AspectX/Y`). Es el modelo directo para tus anillos y tu mandala. Orden de la cadena: centrar la UV → rotar → dividir por aspecto → `abs` → restar el medio-extenso → `max(0)` → `length`. |
| **`M_LightShaft`** | El **Fresnel two-sided** (con el `Abs` bien puesto) y cómo se arma un emisivo que se lee como volumen. Modelo para tu efecto de borde. |
| **`M_FogSlab_SC`** | El más completo: **máscara de borde** (rectangular o circular, dura o difusa), **ruido de superficie** en coordenada `UV × Size`, **`DepthFade`** para las intersecciones blandas, **fade de cámara** y **ola por WPO**. Su tracker en `blueprints/BP_FogSlab_SC.md` explica cada término. |

⚠ **Y la regla que más tiempo nos ha ahorrado:** antes de construir cualquier interacción o pieza, mirá si ya existe. `references/assets-existentes.md` es el inventario y `blueprints/_INDEX.md` el mapa de todos los Blueprints. Ya nos pasó varias veces construir desde cero algo que estaba resuelto y probado.

---

## 5. Tus tres efectos

### 5.1 · `BP_LightPanel_SC` — la superficie que hace cosas

**Qué es.** Un panel plano con un **selector de modo**. Agrupa cuatro efectos que comparten toda la cañería, en vez de cuatro Blueprints casi idénticos. Es el mismo patrón que el `ShapeIndex` de `BP_LightShaft_SC`.

**Para qué sirve en la obra.** Es el vocabulario de una obra de luz mínima: una franja que recorre un muro, un halo que respira, un rosetón que gira, una pared que se enciende cuando te acercás.

**Assets tuyos:** `M_LightPanel_SC` · `BP_LightPanel_SC`.

**Los cuatro modos** (resolvelos con un **static switch**, no con branches por píxel: así cada instancia compila solo su rama y no pagás las cuatro):

```
Todos terminan igual:
   Emissive = PanelColor × mask × Brightness
   Opacity  = mask × MascaraDeBorde        // copiá la de M_FogSlab_SC

0 · BARRIDO  — una franja de claridad recorre el panel
   p    = dot(uv − 0.5, dir(SweepAngle))
   mask = exp(−pow(frac(p − t·SweepSpeed) − 0.5, 2) / SweepWidth)

1 · ANILLOS  — anillos concéntricos nítidos, sin textura
   r    = length(uv − 0.5) × 2
   mask = suma de   1 − smoothstep(0, RingSoft, |r − RingPos_i|)   para 3 anillos

2 · MANDALA  — simetría radial girando lento
   a    = atan2(uv.y − 0.5, uv.x − 0.5)
   a    = frac(a / (2π) × Segments + t × SpinSpeed)
   mask = el mismo patrón de anillos, pero en (a, r)

3 · CERCANÍA — el panel se enciende donde estás vos
   mask = SphereMask(WorldPosition, CameraPositionWS, TouchRadius, TouchHardness)
```

💡 **`SphereMask` es un nodo del motor** (pines A, B, Radius, **Hardness**): caída esférica suave entre dos posiciones de mundo, en un solo nodo. Lo encontramos revisando Content Examples y reemplaza la cadena `Distance → Subtract → Divide → Saturate` que veníamos escribiendo a mano.

**Perillas:**

| Categoría | Variables | Default | Rango |
|---|---|---|---|
| A - Forma | `Mode` (0–3) · `PanelSizeX` · `PanelSizeY` (cm) · `Mesh` | 0 · 2000 · 2000 · Plane del motor | — · 100–20000 |
| B - Color | `PanelColor` · `Brightness` | ámbar cálido · 1.0 | — · 0–4 |
| C - Barrido | `SweepAngle` · `SweepSpeed` · `SweepWidth` | 0 · 0.25 · 0.04 | 0–360 · 0–2 · 0.005–0.3 |
| D - Anillos | `RingCount` · `RingPos1/2/3` · `RingSoft` | 3 · 0.3/0.55/0.8 · 0.02 | 1–3 · 0–1 · 0.002–0.2 |
| E - Mandala | `Segments` · `SpinSpeed` | 8 · 0.05 | 3–24 · −1–1 |
| F - Cercanía | `TouchRadius` (cm) · `TouchHardness` | 180 · 0.5 | 20–600 · 0–1 |
| G - Borde | `EdgeRound` · `EdgeSoft` · `EdgeAmount` | 0 · 2.5 · 1 | 0–1 · 0.5–16 · 0–1 |

**Riesgo en Quest:** ninguno serio, es el más barato de los siete.

**Terminado cuando:** los cuatro modos se ven distintos en el viewport, y en el modo 3 el panel se enciende al acercarte en PIE.

---

### 5.2 · `BP_RimShape_SC` — formas que solo existen como su resplandor

**Qué es.** Geometría invisible salvo por su silueta: relleno cero, borde encendido. Un objeto que está y no está — presencia sin masa, que es exactamente lo contrario de la arista dura que el documento de la obra descarta.

**Para qué sirve en la obra.** Dos momentos ya escritos del guión lo piden sin nombrarlo: el cascarón de la etapa *Surrounding*, donde «el borde brilla suave al acercarse, para que la regla se aprenda con el cuerpo», y la sala final, que tiene que **abrirse** —esconder su muro— para devolver el exterior.

**Assets tuyos:** `M_RimOnly_SC` · `BP_RimShape_SC`.

**Cadena del material:**
```
rim     = pow(1 − abs(dot(N, V)), RimPower) × RimWidth      // el abs va ADENTRO (trampa 4)
reveal  = lerp(1, SphereMask(WorldPosition, CameraPositionWS, RevealRadius, RevealHard), RevealAmount)
diss    = paso duro del ruido de superficie contra DissolveThreshold, con el borde encendido
contact = DepthFade(ContactFade)                             // no corta duro contra el piso
Emissive = RimColor × rim × reveal × Brightness  (+ el borde del disuelto)
Opacity  = rim × reveal × diss × contact
```

**Perillas:** `A - Forma` (`Mesh` intercambiable — esfera, cubo, cilindro; `SizeCM`) · `B - Borde` (`RimColor`, `RimPower` 0.5–8, `RimWidth` 0–3, `Brightness` 0–4) · `C - Revelado` (`RevealAmount` 0–1, `RevealRadius` 50–800 cm, `RevealHard` 0–1) · `D - Disolución` (`DissolveThreshold` 0–1, `DissolveEdge` 0–0.3, `DissolveEdgeColor`) · `E - Contacto` (`ContactFade` 0–400).

**Terminado cuando:** acercándote en PIE la forma aparece desde la nada; y moviendo `DissolveThreshold` a mano, se deshace desde el borde con el filo encendido.

---

### 5.3 · `BP_Orb_SC` — el objeto que se ve hecho de algo

**Qué es.** Un selector de **look** para objetos sólidos. Es lo que hoy no tenemos: todo lo nuestro es superficie plana, y la obra está llena de orbes (respiración, sonido, la ameba, las burbujas de *Attracting*).

**Assets tuyos:** `M_Orb_SC` · `BP_Orb_SC` · `T_Matcap_01/02/03`.

**Los tres looks:**
```
0 · VOLUMEN FALSO — se lee como volumen de luz, no como cáscara
    v = 1 − (distancia al centro en pantalla, normalizada)
    Opacity = pow(v, VolumePower) × Density

1 · IRIDISCENTE — el tono se corre según el ángulo de vista, como una pompa
    f = 1 − abs(dot(N, V))
    Emissive = lerp(ColorA, ColorB, frac(f × HueCycles + HueOffset)) × Brightness

2 · MATCAP — vidrio, seda o perla SIN una sola luz
    uvm = normalize(TransformVector(N, mundo→vista)).xy × 0.5 + 0.5
    Emissive = TextureSample(Matcap, uvm) × Tint × Brightness
```

💡 **Un *matcap* es una textura que se muestrea según hacia dónde mira cada punto de la superficie.** Da la respuesta de un material iluminado sin que exista ninguna luz. Es la respuesta honesta a «que parezca de vidrio»: no refracta nada —eso en Quest no corre—, pero se ve como si lo hiciera. Las tres texturas las generás vos (perla, vidrio frío, seda cálida): son degradados radiales suaves de 256×256, y conviene generarlas por script antes que pintarlas.

**Perillas:** `A - Forma` (`Look` 0–2, `Mesh`, `SizeCM`) · `B - Color` (`ColorA`, `ColorB`, `Tint`, `Brightness` 0–4) · `C - Volumen` (`VolumePower` 0.5–6, `Density` 0–1) · `D - Iridiscencia` (`HueCycles` 0.5–4, `HueOffset` 0–1) · `E - Matcap` (`Matcap`, `MatcapStrength` 0–2) · `F - Vida` (`PulseAmount` 0–1, `PulseSpeed` 0–3 — por reloj).

**Terminado cuando:** los tres looks se ven claramente distintos y el orbe late solo.

---

## 6. Cuándo está terminado tu trabajo

Para cada uno de los tres:

1. Material y Blueprint **compilan sin warnings**.
2. Está **colocado en tu nivel** `L_EffectTest_Nico` y se ve bien en el viewport **sin darle Play** (el Construction Script empuja todo).
3. **Todas las perillas hacen algo visible** y los rangos son razonables. Los rangos de slider (UIMin/UIMax) se fijan **a mano en el editor**: el MCP no expone esa metadata.
4. **Tracker escrito** en `blueprints/`, y fila agregada en `_INDEX.md` y en `references/assets-existentes.md`.
5. **Capturas para Beltrán** de cada modo o look, para que las juzgue antes de que sigamos.
6. Commiteado en tu rama, con Unreal cerrado al mergear.

⚠ **Lo que NO se prueba todavía:** el visor. Los tres sistemas que ya existen se verificaron juntos en un APK y funcionan; los tuyos entran en el siguiente build, que arma Beltrán. Si algo tuyo depende de un truco raro, avisá antes.

---

## 7. Preguntá esto en vez de decidirlo solo

- Si te parece que hace falta tocar un archivo de `Config/` o un asset compartido.
- Si un efecto necesita una malla nueva generada por script (esas las hace Beltrán, tiene el pipeline armado).
- Si querés cambiar los nombres de los assets (rompen el contrato con la galería).
- Si algo del brief te parece que está mal pensado. Es más barato discutirlo que construirlo dos veces.
