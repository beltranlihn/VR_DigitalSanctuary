# PLAN — La galería de efectos (Core/Light) · 2026-09-04

> **Qué es esto.** El plan detallado para construir los efectos de material que le faltan a la obra, cada uno como un Blueprint con perillas, y una galería recorrible para verlos todos juntos.
>
> 🔴 **ALCANCE (fijado por Beltrán, 2026-09-04): esto es LOOK-DEV, no interacción.** El objetivo es *mirar* qué se puede lograr. **Ningún efecto se conecta al cuerpo del usuario todavía** — nada de manos, respiración ni latido. Todo se anima por reloj o reacciona a la distancia de la CÁMARA (que sale gratis en el material, sin cañería). Conectar las señales del cuerpo es una etapa posterior, cuando ya sepamos qué efectos valen la pena. Está escrito para **repartir trabajo entre Beltrán y Nico**, así que cada tarea dice qué assets toca, qué hay que construir exactamente y cuándo está terminada.
>
> **Contexto previo:** el mapa de lo posible está en el artifact *"Luz sin luces"* (12 palancas + las 6 paredes del renderer móvil) y la revisión de Content Examples en [`references/materials-vr.md`](../.claude/skills/unreal-vr/references/materials-vr.md). Lo que ya existe está en [`assets-existentes.md`](../.claude/skills/unreal-vr/references/assets-existentes.md).
>
> **Regla de oro de este plan:** `.uasset` son binarios y no se mergean. **Cada asset tiene UN dueño.** Nunca dos personas en el mismo archivo.

---

## Lo que ya existe (no se toca salvo donde se indique)

`BP_LightShaft_SC` + `M_LightShaft` (haces) · `BP_CloudPlane_SC` + `M_CloudPlane_SC` (océano) · `BP_FogSlab_SC` + `M_FogSlab_SC` (niebla con espesor) · `M_ApertureGlow_SC` (SDF de caja/círculo) · `M_BeamReceiver_SC` + `MPC_LightShaft` (meshes bañados) · `M_FogVeil_SC` (velo simple) · `NS_VoidDust` (polvo).

Cubre **luz en el aire**. Lo que falta es **el espacio**: las salas, el vacío, y los objetos que viven ahí.

---

# FASE 0 — Cimientos compartidos

🔴 **Lo hace UNA sola persona y termina ANTES de repartir.** Son archivos que después toca todo el mundo.

## 0.A · ✅ HECHO — el APK de verificación (2026-09-04)

Se empaquetó `leveltestmesh` (`com.almadigital.leveltestmesh`, para no pisar Soul Charger en el visor) con el nivel `/Game/TestMeshes` ordenado: mar, banco de niebla vertical, siete haces, velos y polvo, todo visible desde el PlayerStart.

**Veredicto de Beltrán: «los efectos se veían bien».** Eso da por buenos los tres riesgos que bloqueaban el plan:
- ✅ **`DepthFade` funciona en el APK** — era el que más dolía: cuatro de los siete efectos dependen de él.
- ✅ **El nodo `Noise` procedural corre en mobile forward** — no hace falta el plan B con `T_smoothCloudsNoise`.
- ✅ **El fill aguanta** el peor caso que tenemos (mar + niebla + siete haces + velos apilados).

⚠ Quedan dos cosas por revertir cuando termine la etapa de pruebas, ambas comentadas en su archivo: el `PackageName` en `DefaultEngine.ini` y la línea de `TestMeshes` en `MapsToCook`.

## 0.B · ✅ HECHO — dos arreglos que salieron de mirar

- **`M_CloudPlane_SC`**: el fade de cámara eran dos constantes fijas de 100/400 cm, o sea **cinco metros de transparencia alrededor de la cabeza** — por eso cerca se veía todo lo que había debajo del mar. Ahora son parámetros (`CamFadeNear` 60 / `CamFadeRange` 120) con sus perillas en el BP.
- **`M_FogSlab_SC` en vertical**: el ruido y la ola tomaban su coordenada de `WorldPosition.XY`, y en una losa vertical el plano se extiende en X y **Z** — como Z no entraba, salían rayas. Ahora la coordenada es **`UV × SlabSize`**, que recorre el plano sea cual sea su orientación y mantiene la densidad en centímetros. La regla `WaveScale ≲ 100/SlabSizeX` sigue valiendo.

## 0.C · Tres funciones de material compartidas

Los tres materiales que tenemos reimplementan lo mismo. Antes de escribir siete materiales más, extraer:

- **`MF_EdgeMask`** — la máscara de borde de `M_FogSlab_SC`: `d = lerp(max(|u|,|v|), length(uv−0.5)·2, Round)` → `saturate((1−d)·Soft)` → `lerp(1, m, Amount)`. Entradas: `UV`, `Round`, `Soft`, `Amount`.
- **`MF_SurfaceNoise`** — dos muestras de `T_ShaftNoise` panneadas en direcciones opuestas, mezcladas 65/35, sobre **coordenada de superficie** (`UV × Size`), no de mundo. Entradas: `UV`, `Size`, `Scale`, `Speed`, `Amount`.
- **`MF_DitherGradient`** — gradiente con dither ordenado para matar el banding en 8 bits. Entradas: `ColorA`, `ColorB`, `Position`, `Sharpness`, `DitherAmount`.

**Terminado cuando:** las tres compilan y `M_FogSlab_SC` fue migrado a usarlas (es el conejillo de indias: si algo se rompe, se ve enseguida).

## 0.D · Dos cambios en `DefaultEngine.ini` — 🟡 requieren OK de Beltrán

- `r.MobileNumDynamicPointLights=0` — la obra tiene cero luces y cada una soportada multiplica permutaciones de shader.
- `r.DefaultFeature.Bloom=False` y `r.DefaultFeature.AutoExposure=False` — no cambian nada en el visor (ahí no hay post) pero **hacen que el viewport del editor deje de mentir**: se autoraría viendo lo que el APK muestra.

## 0.E · ⏸ APARCADO — las señales del cuerpo

Se llegó a crear `MPC_Body_SC` y `BP_BodySignal_SC` y **se borraron** al fijar el alcance: la galería es para mirar, no para interactuar. Cuando llegue el momento de conectar manos, respiración y latido, esto es lo primero que se construye: una colección de parámetros que publica `HeadPos`, `HandLPos/RPos`, `BreathValue` y `HeartPulse`, más un actor con Tick que la llena buscando las manos por `GetObjectName == "HandRight"/"HandLeft"` (el patrón probado de `BP_ControllerRig`, con `Delay 0.2` en BeginPlay porque el PlayerController todavía no existe).

💡 **Lo que NO necesita nada de eso:** reaccionar a la **distancia de la cámara**. `CameraPositionWS` está disponible en cualquier material sin cañería, así que «la forma aparece cuando te acercás» se puede hacer hoy mismo — y en una galería es justo lo que querés demostrar.

# FASE 1 — Los siete efectos

Cada uno es **un BP + un material + (a veces) una malla**. Todos siguen el patrón probado de `BP_LightShaft_SC`: componente(s), variables instance-editable agrupadas por categoría, y un Construction Script que empuja todo al MID para que se vea en el viewport sin darle Play.

**Convenciones obligatorias para los siete:**
- Carpeta `Core/Light/`. Nombres `BP_*_SC`, `M_*_SC`, `SM_*`.
- Material **unlit**; translúcido o aditivo según el caso; `Full Precision (expresiones)`.
- Nada de luces, nada de post-proceso, nada de las seis paredes.
- Tamaños en **centímetros** por variable, no con la escala del actor (lección de `BP_FogSlab_SC`).
- ⚠ `Sine`/`Cosine` con `period = 6.283185` o la entrada se multiplica por 2π.
- ⚠ Si el material usa WPO, subir el `boundsScale` del componente a 2.
- **Tracker en `blueprints/` desde el día 1**, y fila en `_INDEX.md` y en `assets-existentes.md` al terminar.

---

## 1.1 · `BP_Ganzfeld_SC` — el cascarón sin borde

**Qué es.** Una superficie grande y curva con un gradiente emisivo continuo: sin esquina, sin borde, sin textura que dé escala. El ojo pierde la referencia de profundidad y el cuarto deja de leerse como cuarto. Es la sección 6 del documento maestro escrita como material.

**Assets:** `SM_GanzShell` (esfera invertida suave, ~5k tris, sin costura visible, normales hacia adentro) · `M_Ganzfeld_SC` · `BP_Ganzfeld_SC`.

**Cadena del material:**
```
h        = saturate((LocalPosition.Z / ShellHeight) + 0.5)      // 0 abajo, 1 arriba
h        = pow(h, GradientBias)                                  // corre el punto medio
color    = MF_DitherGradient(ColorBottom, ColorTop, h, Sharpness, Dither)
horizon  = lerp(1, HorizonGlow, exp(-|h − HorizonPos| · HorizonWidth))   // banda opcional
Emissive = color × horizon × Brightness
WPO      = VertexNormalWS × BreathAmount × sin(t · BreathSpeed)   // por RELOJ; atarlo a la respiracion real es etapa posterior
```

**Perillas:**

| Categoría | Variables | Default | Rango |
|---|---|---|---|
| A - Forma | `ShellRadius` (cm) · `ShellHeight` (cm) · `Mesh` | 1500 · 900 · `SM_GanzShell` | 300–8000 |
| B - Color | `ColorTop` · `ColorBottom` · `Brightness` | azul profundo · casi negro · 1.0 | — · — · 0–3 |
| C - Gradiente | `GradientBias` · `Sharpness` · `DitherAmount` | 1.0 · 1.0 · 0.6 | 0.2–4 · 0.2–4 · 0–2 |
| D - Horizonte | `HorizonPos` · `HorizonWidth` · `HorizonGlow` | 0.5 · 8 · 1.0 (apagado) | 0–1 · 1–40 · 1–3 |
| E - Respiración | `BreathAmount` (cm) · `BreathSpeed` | 40 · 0.15 | 0–200 · 0–1 |

**Riesgo Quest:** el banding del gradiente es el enemigo real y por eso el dither no es opcional. Es una superficie enorme en pantalla: **medir el fill**.

**Terminado cuando:** puesto alrededor del PlayerStart, no se distingue dónde termina el suelo y empieza el muro, y la sala se expande y contrae sola con un ritmo lento.

---

## 1.2 · `BP_VoidField_SC` — profundidad sin geometría

**Qué es.** Dos o tres cascarones concéntricos a radios distintos con puntos resueltos en el material. Al mover la cabeza las capas se desplazan a velocidades distintas, y ese paralaje es lo único que vende una escala infinita. Sustituye al campo de partículas del exterior con 3 draw calls.

**Assets:** `M_VoidDots_SC` · `BP_VoidField_SC` (reusa `SM_GanzShell` invertida).

**Cadena del material** — la parte difícil son los puntos procedurales sin textura:
```
uv    = TexCoord × Tiling
cell  = floor(uv) ; f = frac(uv) − 0.5
rnd   = hash(cell)                      // ruido de 2 canales por celda
jitter= (rnd − 0.5) × 0.7               // que no se vea la grilla
d     = length(f − jitter)
size  = DotSize × lerp(0.4, 1, rnd.x)   // tamaños variados
dot   = 1 − smoothstep(size, size × 1.6, d)
twink = lerp(1, 0.5 + 0.5·sin(t·TwinkleSpeed + rnd.y·6.28), TwinkleAmount)
Emissive = DotColor × dot × twink × Brightness × lerp(0.3, 1, rnd.y)
```
🔴 **El jitter por celda es lo que hace o rompe el efecto**: sin él se ve una grilla y el paralaje deja de leerse como estrellas.

**Perillas:**

| Categoría | Variables | Default | Rango |
|---|---|---|---|
| A - Capas | `LayerCount` (1–3) · `Radius0/1/2` (cm) | 3 · 1200 / 2600 / 5200 | 1–3 · 300–20000 |
| B - Puntos | `Tiling` · `DotSize` · `Brightness` | 40 · 0.05 · 1.0 | 8–200 · 0.01–0.3 · 0–4 |
| C - Color | `DotColor` · `FarDim` | blanco frío · 0.35 | — · 0–1 |
| D - Vida | `TwinkleAmount` · `TwinkleSpeed` · `DriftSpeed` | 0.3 · 0.4 · 0.02 | 0–1 · 0–2 · 0–0.2 |

**Riesgo Quest:** tres cascarones grandes translúcidos = fill. Mitigación: los de más lejos, más tenues y con menos densidad.

**Terminado cuando:** moviendo la cabeza en PIE se siente profundidad, y no se ve ninguna grilla.

---

## 1.3 · `BP_LightPanel_SC` — la superficie que hace cosas

**Qué es.** Un panel (plano, o la malla que se le ponga) con un selector de **modo**. Agrupa cuatro palancas que comparten toda la cañería, en vez de cuatro BPs casi idénticos. Mismo patrón que el `ShapeIndex` del haz.

**Modos:**
- **0 · Barrido** — una franja de claridad recorre el panel a lo largo de un eje. *Proyección de luz sin proyector.*
- **1 · Anillos SDF** — anillos, arcos y halos concéntricos, nítidos a cualquier escala, sin textura.
- **2 · Mandala** — coordenadas polares con `Segments` ejes de simetría, girando lento.
- **3 · Cercanía** — el panel se enciende donde está **la cámara**, o sea donde te acercás vos. Sale gratis con `CameraPositionWS`, sin cañería.

**Assets:** `M_LightPanel_SC` · `BP_LightPanel_SC`.

**Cadena por modo** (todos terminan en `Emissive = PanelColor × mask × Brightness`, opacidad = `mask × MF_EdgeMask`):
```
0: p = dot(LocalPos.xy, dir(SweepAngle)) / PanelSize
   mask = exp(−pow(frac(p − t·SweepSpeed) − 0.5, 2) / SweepWidth)
1: r = length(uv − 0.5) · 2
   mask = Σ_i  1 − smoothstep(0, RingSoft, |r − RingPos_i|)      // 3 anillos autorables
2: a = atan2(uv.y−0.5, uv.x−0.5) ; a = frac(a/(2π)·Segments + t·SpinSpeed)
   mask = pattern(a, r)                                          // el mismo SDF de anillos, en polar
3: mask = SphereMask(WorldPosition, CameraPositionWS, TouchRadius, TouchHardness)
```

**Perillas:** `A - Forma` (`Mode`, `PanelSizeX/Y`, `Mesh`) · `B - Color` (`PanelColor`, `Brightness`) · `C - Barrido` (`SweepAngle` 0–360, `SweepSpeed` 0–2, `SweepWidth` 0.005–0.3) · `D - Anillos` (`RingPos1/2/3` 0–1, `RingSoft` 0.002–0.2, `RingCount` 1–3) · `E - Mandala` (`Segments` 3–24, `SpinSpeed` −1–1) · `F - Cercanía` (`TouchRadius` 20–600 cm, `TouchHardness` 0–1) · `G - Borde` (los tres de `MF_EdgeMask`).

**Riesgo Quest:** ninguno serio; es el más barato de los siete. Los modos se resuelven con un **static switch**, no con branches por píxel, así cada instancia compila solo su rama.

**Terminado cuando:** los cuatro modos se ven, y en el modo 3 el panel se enciende al acercarte en PIE.

---

## 1.4 · `BP_RimShape_SC` — aparecer y desaparecer

**Qué es.** Geometría invisible salvo por su silueta, que además puede revelarse al acercarse y disolverse por ruido. Presencia sin masa. Lo piden dos momentos ya escritos del guión: el cascarón de Surrounding («el borde brilla suave al acercarse») y la sala final, que tiene que abrirse para devolver el exterior.

**Assets:** `M_RimOnly_SC` · `BP_RimShape_SC` (malla intercambiable: esfera, cubo, cilindro, o la que se le ponga).

**Cadena del material:**
```
rim     = pow(1 − |dot(N, V)|, RimPower) × RimWidth        // Fresnel con Abs -> sirve two-sided
reveal  = lerp(1, SphereMask(WorldPosition, CameraPositionWS, RevealRadius, RevealHard), RevealAmount)
diss    = MF_SurfaceNoise(...) > DissolveThreshold ? 1 : 0   // borde del disuelto encendido
contact = DepthFade(ContactFade)
Emissive= RimColor × rim × reveal × Brightness
Opacity = rim × reveal × diss × contact
```
⚠ **El `Abs` en el Fresnel no es opcional** — sin él las caras traseras dan 0 exacto y el objeto desaparece desde adentro (lección ya pagada en `M_LightShaft`).

**Perillas:** `A - Forma` (`Mesh`, `SizeCM`) · `B - Borde` (`RimColor`, `RimPower` 0.5–8, `RimWidth` 0–3, `Brightness` 0–4) · `C - Revelado` (`RevealAmount` 0–1, `RevealRadius` 50–800 cm, `RevealHard` 0–1) · `D - Disolución` (`DissolveThreshold` 0–1, `DissolveEdge` 0–0.3, `DissolveEdgeColor`) · `E - Contacto` (`ContactFade` 0–400).

**Terminado cuando:** acercándote en PIE la forma aparece; y con `DissolveThreshold` animado, se deshace desde el borde.

---

## 1.5 · `BP_Orb_SC` — el objeto que se ve hecho de algo

**Qué es.** Un selector de **look** para objetos sólidos, que es lo que hoy no tenemos: todo lo nuestro es superficie plana. La obra está llena de orbes (respiración, sonido, la ameba, las burbujas de Attracting).

**Looks:**
- **0 · Volumen falso** — la opacidad cae desde el centro en espacio de vista: se lee como volumen de luz, no como cáscara.
- **1 · Iridiscente** — el tono se corre según el ángulo de vista, como una película de aceite.
- **2 · Matcap** — una textura muestreada por la normal en espacio de vista da vidrio, seda, metal o perla **sin una sola luz**. Es la respuesta honesta al «cristal».

**Assets:** `M_Orb_SC` · `BP_Orb_SC` · `T_Matcap_01..03` (tres matcaps generadas por script: perla, vidrio frío, seda cálida).

**Cadena:**
```
0: v = 1 − length(ScreenAlignedUV(sphere))          // 1 en el centro, 0 en el borde
   Opacity = pow(v, VolumePower) × Density
1: f = 1 − |dot(N, V)|
   Emissive = lerp(ColorA, ColorB, frac(f × HueCycles + HueOffset)) × Brightness
2: uvm = normalize(TransformVector(N, world→view)).xy × 0.5 + 0.5
   Emissive = TextureSample(Matcap, uvm) × Tint × Brightness
```

**Perillas:** `A - Forma` (`Look`, `Mesh`, `SizeCM`) · `B - Color` (`ColorA`, `ColorB`, `Tint`, `Brightness`) · `C - Volumen` (`VolumePower` 0.5–6, `Density` 0–1) · `D - Iridiscencia` (`HueCycles` 0.5–4, `HueOffset` 0–1) · `E - Matcap` (`Matcap`, `MatcapStrength` 0–2) · `F - Vida` (`PulseAmount` 0–1, `PulseSpeed` 0–3 — por reloj).

**Terminado cuando:** los tres looks se ven distintos y el orbe late solo.

---

## 1.6 · `BP_LineField_SC` — la luz dibujada con líneas

**Qué es.** En vez de una superficie llena, una malla de cientos de líneas finas emisivas. El volumen aparece por acumulación, no por relleno. Sale de la referencia de la instalación de hilos que trajo Beltrán.

**Assets:** `SM_LineGrid` (generada por script: N tiras finas paralelas, cada una un quad largo subdividido; ~200 líneas × 128 segmentos) · `M_LineGlow_SC` · `BP_LineField_SC`.

**Cadena:** emisivo plano × `DepthFade` para que no corte duro × `SphereMask` sobre la UV longitudinal para afinar las puntas (la receta que confirmamos en `PlexusLine_Mat` de Content Examples) + la **misma ola por WPO** de `M_FogSlab_SC`, que ya está escrita y probada.

**Perillas:** `A - Forma` (`LineCount`, `FieldSizeX/Y`, `LineWidth`) · `B - Color` (`LineColor`, `Brightness`) · `C - Ola` (`WaveAmount`, `WaveScale`, `WaveSpeed` — mismos rangos que la niebla, y la misma regla `WaveScale ≲ 100/FieldSizeX`) · `D - Puntas` (`TipFade` 0–0.5) · `E - Contacto` (`ContactFade`).

**Riesgo Quest:** es el más incierto de los siete. Muchas tiras finas translúcidas = overdraw en el peor caso (líneas casi de canto). **Empezar con 100 líneas y medir antes de subir.**

**Terminado cuando:** se ve el oleaje de hilos de la referencia y hay una medición de fill anotada.

---

## 1.7 · `BP_ShadowStudy_SC` — la sombra falsa del video

**Qué es.** Lo que trajo Beltrán en el video del 2026-09-04: una esfera mate sobre un fondo pálido, proyectando una **sombra larga y suave que rota**. Abre un registro visual que la obra hoy no puede hacer: **oscuridad sobre claro**, en vez de luz sobre negro.

🔴 **Autocontenido a propósito.** En vez de un caster y un receptor comunicándose por una colección de parámetros, es **un solo BP con las dos piezas adentro**: la esfera y el suelo. Así el Construction Script conoce la posición de la esfera y se la empuja al material del suelo sin cañería entre actores. Para una estación de galería es exactamente lo que hace falta, y es mucho menos frágil.

**Assets:** `M_FakeShadow_SC` (el suelo) · `BP_ShadowStudy_SC` (esfera + suelo).

**Cómo se hace sin luces.** El material del suelo hace un test rayo-esfera por píxel:
```
L   = normalize(LightDir)
C   = CasterPos ; R = CasterRadius        // empujados por el Construction Script
w   = C − P                                // P = punto del suelo
t   = dot(w, L)                            // ¿está la esfera hacia la luz?
d   = length(w − L·t)                      // distancia del centro al rayo
pen = R × (1 + t × Penumbra)               // la sombra se ensancha con la distancia
s   = 1 − smoothstep(pen × Hard, pen, d)
s   = s × step(0, t) × exp(−t × Falloff)   // se desvanece a lo lejos
Emissive_suelo = GroundColor × lerp(1, 1 − ShadowStrength, s)
```
Son ~12 instrucciones. Con `LightDir` girando por reloj, la sombra **barre** como en el video.

**Perillas:** `A - Forma` (`SphereRadius` 10–200 cm, `SphereHeight` 0–300 cm, `GroundSize` 500–8000 cm) · `B - Color` (`GroundColor` gris claro, `SphereColor` casi blanco, `Brightness`) · `C - Sombra` (`ShadowStrength` 0–1, `Penumbra` 0–0.02, `Hard` 0–1, `Falloff` 0–0.005) · `D - Luz ficticia` (`LightDir`, `bSpinLight`, `LightSpinSpeed` 0–0.5).

⚠ **Límite honesto:** una esfera, una sombra. El costo es lineal por caster, así que no es un sistema de sombras — es *una* sombra bien hecha. Si más adelante hace falta que varios objetos proyecten, ahí sí conviene la colección de parámetros.

**Terminado cuando:** se reproduce el video — esfera pálida, fondo pálido, sombra larga que rota sola.

---

# FASE 2 — La galería

**`L_EffectGallery`** (nivel nuevo en `Content/SoulCharger/Gallery/`). No es parte de la obra: es la herramienta para mirar.

## El diseño, decidido con Beltrán el 2026-09-04

**Teletransporte entre `TargetPoints`, no caminata.** Beltrán lo propuso y es lo correcto por tres razones: cada efecto necesita su propio entorno y los entornos son **incompatibles entre sí** (el cascarón te encierra, el estudio de sombra es claro, el vacío es negro — no conviven en el mismo lugar); teletransportar es **cero riesgo vestibular**, que es regla de la obra; y permite separar las estaciones lo suficiente como para que no se contaminen.

🔴 **Agregado técnico que no estaba en la propuesta: solo la estación ACTIVA visible.** Si las siete existen a la vez, las siete se dibujan — y varias son superficies translúcidas enormes. Estando lejos no se ven, pero **sí cuestan fill si caen en el frustum**, y el cascarón y el campo de puntos son cascarones que envuelven. El director apaga todas y prende la activa. Es una línea de código y evita que la galería sea el nivel más caro del proyecto.

## Las piezas

- **`BP_Anchor` por estación** (ya existe: hereda `TargetPoint`, oculto en juego), tagueado `GALLERY_<n>`. 🔴 **Aporta su TRANSFORM entero, no solo la posición** — regla de Beltrán del 2026-08-14: rotar o escalar el anchor debe rotar o escalar la estación.
- **Dos `BP_MenuButton`** al frente del usuario: siguiente y anterior. 🔴 **Se REUSA, no se construye uno nuevo** — ya trae hover y select con háptica, y anda con `IMC_MenuTrigger` + `IA_Shoot_*`. Y la regla dura del proyecto: **no se crean ni se editan IMCs**; el mapeo de input es frágil y nadie sabe reconstruir por qué anda el que anda.
- **`BP_GalleryDirector_SC`** (nuevo, lo único que hay que construir acá): guarda el índice, recoge los anchors con `GetAllActorsOfClassWithTag`, teletransporta el pawn al transform del anchor activo, y prende/apaga las estaciones. Más una etiqueta de texto emisivo con el nombre del efecto.

## Orden

Se arma **al final y por UNA sola persona**: el `.umap` es binario y si dos colocan actores a la vez se pierde el trabajo de uno. Antes de eso, cada quien prueba lo suyo en su propio nivel de test.

**Terminado cuando:** se recorren las siete estaciones con los botones, en visor, y solo se ve una por vez.

---

# Reparto del trabajo

## Propiedad de assets — la tabla que evita perder trabajo

🔴 **Cada quien en SU nivel de pruebas.** Beltrán en `/Game/TestMeshes`, Nico en `/Game/SoulCharger/Maps/Tests/L_EffectTest_Nico` (lo crea él). Nadie abre el del otro. El nivel de galería se arma al final, por una sola persona.

| Bloque | Assets | Dueño |
|---|---|---|
| Fase 0 restante | `MF_EdgeMask`, `MF_SurfaceNoise`, `MF_DitherGradient`, `DefaultEngine.ini` | **Beltrán** |
| 1.1 Cascarón sin borde | `SM_GanzShell`, `M_Ganzfeld_SC`, `BP_Ganzfeld_SC` | **Beltrán** |
| 1.2 Campo de puntos | `M_VoidDots_SC`, `BP_VoidField_SC` | **Beltrán** |
| 1.6 Luz con líneas | `SM_LineGrid`, `M_LineGlow_SC`, `BP_LineField_SC` | **Beltrán** |
| 1.7 Sombra falsa | `M_FakeShadow_SC`, `BP_ShadowStudy_SC` | **Beltrán** |
| 1.3 Panel de 4 modos | `M_LightPanel_SC`, `BP_LightPanel_SC` | **Nico** |
| 1.4 Formas de borde | `M_RimOnly_SC`, `BP_RimShape_SC` | **Nico** |
| 1.5 Orbe | `M_Orb_SC`, `BP_Orb_SC`, `T_Matcap_01/02/03` | **Nico** |
| Fase 2 galería | `L_EffectGallery`, `BP_GalleryDirector_SC` | uno solo, al final |

**Por qué ese corte, y no otro.** No es 3½ y 3½ porque los siete no pesan igual. El criterio es **quién necesita generar mallas nuevas por script**: los cuatro de Beltrán las necesitan (`SM_GanzShell`, `SM_LineGrid`) o son matemática nueva sin modelo previo, y el pipeline de Python → OBJ → import ya lo tiene armado él. Los tres de Nico **usan mallas del motor y siguen patrones ya escritos y probados**: `M_ApertureGlow_SC` es el modelo del SDF, `M_LightShaft` el del Fresnel two-sided, `M_FogSlab_SC` el del ruido, el borde y el `DepthFade`. Puede leerlos y copiar la estructura en vez de inventarla.

📄 **El brief autosuficiente para Nico está en [`BRIEF-NICO-EFECTOS.md`](BRIEF-NICO-EFECTOS.md)** — tiene el contexto de la obra, las reglas de convivencia, las trampas que le van a morder, qué materiales leer como modelo y la especificación completa de sus tres. Está escrito para que se lo pase a su Claude y arranque sin preguntar nada.

## Reglas de convivencia (ya vigentes, se repiten porque acá aplican)

- Rama por persona; **el proyecto entero en el árbol de trabajo**, nunca una rama que esconda carpetas.
- **Cerrar Unreal antes de mergear o cambiar de rama** — con el editor abierto los `.uasset` quedan bloqueados y git falla a medias.
- **Save All antes de commitear.** Commits por hito, no por micro-cambio.
- Tracker en `blueprints/` desde el día 1; fila en `_INDEX.md` y `assets-existentes.md` al terminar.
- Colocar actores sí; sacarlos o moverlos, se pregunta.

---

## Resumen de esfuerzo

| Fase | Contenido | Bloquea a |
|---|---|---|
| **0** | ✅ APK de verificación · ✅ 2 arreglos (fog vertical, fade del mar) · 3 funciones de material · 2 cvars | 0.C conviene antes de 1.x |
| **1** | 7 BPs nuevos, 7 materiales, 3 mallas, 3 texturas matcap. Todos por reloj o por distancia de cámara, **ninguno atado al cuerpo** | la galería |
| **2** | El nivel galería con 7 estaciones | — |

**Lo que queda fuera a propósito:** cáusticas (no está claro que pertenezcan al idioma de la obra) y cualquier cosa de las seis paredes. Y sigue pendiente de otra jornada: los rangos UIMin/UIMax a mano, que el MCP no expone.
