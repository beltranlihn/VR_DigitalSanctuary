# BP_RingTunnel_SC — el túnel infinito de anillos tipo Turrell (Core/Light/)

> Creado 2026-09-07, pedido de Beltrán: *"un túnel infinito tipo James Turrell: un portal con anillos que se van achicando hacia el fondo hasta desaparecer, con una gradiente de color mutando hacia el final. Debe sentirse 3D."* Referencias: sus dibujos, el Aten Reign del Guggenheim y dos capturas violeta de anillos anidados.
> **Estado: 🟡 v3 TRANSLÚCIDA iterada EN VIVO con Beltrán, estación GAL_9 colocada y verificada en PIE (teleport + show/hide + timer de orden ✓). Falta su aprobación final y el visor.**

## 🔄 v3 (2026-09-07, tarde) — TRANSLÚCIDO + marco Ganzfeld; qué cambió sobre lo de abajo
Cinco ajustes de Beltrán en vivo:
1. **Backdrop ELIMINADO** (componente y perillas `bShowBackdrop`/`BackRadius`/`BackColor` fuera). El fondo del túnel es el cascarón.
2. **Los anillos animados son TRANSLÚCIDOS** (*"el dither se ve horripilante en VR"* — el intento Masked+dither R2 murió). `Opacity` = fade de nacimiento: **`FadeInTime`** (cat E, 0.1 = opaco al 10% del viaje; el material lo desactiva con ≤0). 
   🔴 **El precio: 16 translúcidos en el MISMO origen no se ordenan solos** → sistema de prioridades: el CS asigna `TranslucentSortPriority = 20000 − i`, y en Play **`EventBeginPlay → StartWrap`** arma un **timer** (`WrapTick`, período `1/(Speed·RingCount)` ≈ 1.4 s) que llama **`StepSort`**: al anillo que acaba de renacer (índice `(N − m mod N) mod N`) le da prioridad `20000 + m` (m = `WrapCount`). El instante del cambio es invisible (el anillo está en tamaño 0 / alpha 0). ⚠ **En el viewport del editor el orden puede verse mal a ratos** (no hay timer sin Play) — juzgar composición en PIE. ⚠ Cambiar `Speed` en la instancia requiere reiniciar PIE (el período del timer se fija en BeginPlay).
3. **`TwistStart`** (cat B, 0.15): a qué profundidad t empieza la deformación (rampa `(t−TwistStart)/(1−TwistStart)` sobre estiramiento y deriva).
4. **El aro fijo es OPACO con `M_Ganzfeld_SC`** (el material de la esfera de la estación — es parte de la SALA, y al escribir profundidad tapa los nacimientos gratis). Malla propia **`SM_RingFrame_SC`** (annulus 25→50 = agujero 50% horneado en geometría, porque ese material no tiene el WPO del agujero). El CS le apaga `BreathAmount` y `VeilAmount` y le empuja **`FrameColor`** (cat F, única perilla del marco junto a `ContainerScale`) como ColorTop/Mid/Bottom. `ContainerWidth`/`ContainerColor`/`ContainerBrightness` **eliminadas**.
5. El degradado de 3 colores (`ColorNear/Mid/Far`) queda SOLO en los anillos animados.
🔴 **La trampa del getter puro mordió por TERCERA vez** en `StepSort`: el `+1` que alimentaba el target se re-evaluaba tras escribir `WrapCount` (target = m+1). Fix por cirugía: un **getter fresco leído DESPUÉS del Set** (estable porque la variable ya no cambia en la función). Regla: para usar "el valor recién escrito", releerlo con un getter nuevo post-escritura, no reusar la expresión que lo produjo.
🔴 `remove_function_graph`+`add_function_graph` del MISMO nombre cuando otro grafo lo llama devuelve `Nombre_0` incluso en llamadas separadas: el flush es **remover el zombie → compilar (falla por la función faltante, no importa) → add** (§308 ampliado).

## 🔄 v3.4 (2026-09-07) — FadeOutTime + el ordenador AUTOCORRECTIVO por tiempo
- **`FadeOutTime`** (cat. E, 0.15): opacidad 1→0 en el último tramo del viaje, simétrico a `FadeInTime` (≤0 = apagado; el marco no lo empuja → nunca se desvanece).
- 🔴 **El ordenador de translucidez se reescribió: ya NO es un contador de vueltas** (se desfasaba con el reloj del material — "a veces hay anillos por encima de todo" — y en editor ni corría). Ahora `StepSort` **recalcula la prioridad de TODOS los anillos desde el tiempo real**: `prio = 29000 − round(frac(I/N + GetGameTimeInSeconds·Speed)·9000)` — autocorrectivo en cada tick del timer, sin estado (`WrapCount` quedó huérfano-privado, se escribe y no se lee). **El CS también llama a `StepSort` al final** → el viewport del editor queda bien ordenado en cada construcción (deriva entre construcciones, se re-sincroniza al tocar cualquier perilla). El marco opaco sigue en 30000, siempre al frente.
- ⚠ Supuesto medible: `GetGameTimeInSeconds` y el nodo `Time` del material corren el mismo reloj del mundo (PIE ✓; en editor, cerca). Si en visor aparece un anillo mal ordenado, ese supuesto es lo primero a revisar.

## 🔄 v3.3 (2026-09-07) — el backdrop VOLVIÓ, por pedido
Beltrán lo pidió de vuelta con perillas: componente `Backdrop` recreado (cilindro del motor aplastado al 98% del túnel, `M_GalleryProp_SC`, opaco) con **`BackRadius`** (1400) y **`BackColor`** (violeta casi negro), cat. *G - Fondo*. Sin toggle de visibilidad esta vez — si sobra, se esconde el componente. (Historial: nació en v1, se eliminó en v3 punto 1, volvió en v3.3 — el péndulo del autor, el BP lo aguanta porque el bloque es autocontenido en `Build`.)

## 🔄 v3.2 (2026-09-07) — ley GEOMÉTRICA + la sombra en la zona VISIBLE
Dos correcciones de Beltrán sobre la v3.1 (vista lateral suya como evidencia):
- **`TunnelCurve` cambió de ley OTRA VEZ, ahora sí la correcta: `λ = 1 − e^(−K·t)`** (K = TunnelCurve, default **3.0** → cada anillo queda al ~78% del anterior con 12 anillos). La potencia `1−(1−t)^k` comprimía en METROS pero no relativo al TAMAÑO (los anillos también se achican → al fondo se veían MÁS separados respecto a su diámetro). La geométrica da separación ∝ tamaño = contigua hasta el fondo, la proporción de las refes. ⚠ Con esta ley el anillo nunca LLEGA al punto de fuga: al wrap mide `e^(−K)` (~5%) y desaparece de golpe — invisible porque a esa altura ya es `ColorFar` y diminuto.
- **La sombra estaba en el contorno EXTERIOR, que por diseño nunca se ve** (lo tapa el anillo de adelante). Fix: `sh = smoothstep(saturate((1−UV.y)·ShadowSoft))` — el oscurecimiento arranca EN el borde interior y crece hacia afuera, así la franja visible de cada anillo muestra el degradado sombra→luz como sombra proyectada por el anillo del frente. `ShadowSoft` ahora = qué tan rápido crece desde el borde (3.0); `ShadowAmount` 0.5.

## 🔄 v3.1 (2026-09-07, cierre) — frenada al fondo + sombra de papel (Beltrán: "se ve super bien")
- **`TunnelCurve` CAMBIÓ DE LEY**: ahora `λ = 1 − (1−t)^TunnelCurve` (default **2.0**): los anillos pierden velocidad al alejarse y **se apilan hacia el punto de fuga sin huecos** (su dibujo del embudo con barrotes compactándose). 1 = lineal; <1 = acelera al fondo. Para que la frenada no abriera un hueco entre el marco y el primer anillo, `ContainerScale` bajó a **0.92** (achica el agujero del marco).
- **Sombra de paper-cut**: cada anillo se oscurece hacia su borde EXTERIOR (la zona que queda "debajo" del anillo de adelante) — refs de papel cortado en capas. Perillas `ShadowAmount` (0.45) y `ShadowSoft` (2.5, más alto = sombra más pegada al borde), cat. D - Anillos, en el pixel shader (`1 − ShadowAmount·pow(1−UV.y, ShadowSoft)`).
- ✅ **Las "esferas grises" del eje eran el ÍCONO DE BLUEPRINT del editor** (billboard de gizmo) — lo confirmó Beltrán de un vistazo. Cero en el visor. Moraleja: preguntarle antes de perseguir un artefacto visual del EDITOR por MCP.

*(Lo de abajo describe la v2 — sigue válido para geometría, WPO, colores y estación salvo lo corregido arriba.)*

## La arquitectura (v2 — después del rechazo de la v1)
**NO es Niagara** (evaluado contra su Niagara viejo de anillos: acá son ~12 anillos deterministas, no miles de partículas; las perillas viven en el panel y el material se previsualiza en viewport) y **NO es additive con bandas de glow** — la v1 así construida la rechazó: *"se ven como anillos de láser"*. La referencia Turrell son **discos de color plano con canto firme**:

- **17 `StaticMeshComponent`** (16 anillos pool con tag de componente **`TUNRING`** + `ContainerRing`), todos ubicados EN el plano del portal, más `Backdrop` (cilindro del motor aplastado, disco opaco al 98% del túnel con `M_GalleryProp_SC` en `ColorFar` — el agujero oscuro del final).
- **Material OPACO unlit two-sided** (`M_RingTunnel_SC`): el canto duro es el del mesh (el MSAA del Quest lo alisa), **la profundidad ordena sola** (17 translúcidos apilados en el mismo origen flickean: el sorting usa el origen del bounds, no el WPO), y el fill es el barato.
- **El truco central (WPO, custom `RingWPO`)**: `WPO = (VanishPoint − vértice) · λ` con `λ = pow(frac(Phase + Time·Speed), CurveExp)` — lerpear hacia el punto de fuga traslada y encoge con perspectiva exacta; el `frac` da el loop infinito sin spawn/destroy ni Tick.
- 🔴 **Regla de composición que fijó Beltrán: solo se ve el borde INTERIOR de cada anillo** — el disco de adelante tapa el canto exterior del de atrás ("capas superpuestas"). Con ~12 anillos en 30 m la relación de tamaños proyectados entre vecinos ronda 0.6–0.75 → **el agujero (1−RingWidth) tiene que ser ≤ ~0.5** para que el solapamiento nunca se rompa.
- 🔴 **La deformación es FÍSICA y crece con la profundidad** (pedido textual: *"parten siempre exactamente igual y luego se les va deformando el x o y"*): estiramiento del anillo ENTERO a lo largo de un eje por-anillo (`u(RandOff·2π + Time·SpiralSpeed + t·SpiralTwist)`), magnitud `WidthVariation·t`; deriva del centro `WobbleAmount·t`. En t=0 todos idénticos al contenedor.
- **Nacimiento**: geométrico, sin alpha — el anillo nace coincidente con el `ContainerRing` (mismo material, `Phase 0 / Speed 0 / WidthVar 0 / WobAmt 0`, offset −40 cm hacia el usuario contra el z-fight, `ContainerScale` 1.08) y emerge por su agujero.
- **Muerte**: el gradiente llega a `ColorFar` = el color del backdrop → se funde y el wrap ocurre invisible.
- **Sombreado por banda** (custom `RingPix`): color por profundidad (`ColorNear`→`ColorMid` en t 0–0.33, →`ColorFar` hacia t 1) por-anillo casi plano, con `BandGlow`/`BandCurve` aclarando suavemente hacia el borde visible.

## Assets
| Asset | Qué es |
|---|---|
| `SM_RingTunnel_SC` | annulus plano XY por OBJ (§305): r 10→50, 192 tris, UV u=ángulo v=radial, sin colisión |
| `M_RingTunnel_SC` | unlit · **Opaque** · two-sided · `MFPM_Full_MaterialExpressionOnly`. 2 `MaterialExpressionCustom` (RingPix / RingWPO), 18 parámetros |
| `BP_RingTunnel_SC` | los 18 componentes en el CDO; `boundsScale 40` en los anillos (el WPO los lleva 30 m) |

## Registro de variables (instance-editable)
| Cat | Variable | Default | Rol |
|---|---|---|---|
| A - Forma | `PortalRadius` | 300 | radio del portal (escala = r/50) |
| | `TunnelLength` | 3000 | profundidad al punto de fuga |
| | `RingCount` | 12 | anillos visibles (máx 16, el pool) |
| | `TunnelCurve` | 1.0 | exponente de λ |
| B - Movimiento | `Speed` | 0.06 | ciclos/seg del viaje |
| | `SpiralSpeed` / `SpiralTwist` | 0.15 / 2.0 | giro del EJE de estiramiento en el tiempo / con la profundidad |
| | `WobbleAmount` / `WobbleSpeed` | 30 / 0.4 | deriva del centro (crece con t) y su giro |
| C - Color | `ColorNear/Mid/Far` | lavanda / violeta / violeta oscuro | gradiente por profundidad; **`ColorFar` es también el color del backdrop** |
| | `Brightness` | 1.2 | multiplicador |
| D - Anillos | `RingWidth` | 0.5 | proporción de banda (agujero = 1−esto). **0.5 = las proporciones que aprobó Beltrán** |
| | `WidthVariation` | 0.35 | 🔴 renombrada de facto: es el ESTIRAMIENTO físico máximo (a t=1) |
| | `WidthFreq` | 2.0 | ⚠ SIN EFECTO desde el estiramiento físico — sacarla en la limpieza |
| | `BandGlow` / `BandCurve` | 0.35 / 1.6 | lavado suave dentro de cada banda |
| F - Contenedor | `ContainerWidth/Brightness/Scale` | 0.5 / 1.5 / 1.08 | el aro fijo que tapa los nacimientos |
| G - Fondo | `BackRadius` | 1400 | radio del disco del fondo (≥ ~1400 tapa el cono desde el anchor; más grande asoma como aro oscuro) |
| | `bShowBackdrop` | true | |
| (interna) | `Idx` | 0 | contador del loop del CS |

## Estructura de grafos
`ConstructionScript` → `Build` → for-each de `GetComponentsByTag(TUNRING)` → cast → **`SetupRing(Comp, I, VP, ScaleV)`** (visibilidad `I<RingCount`, escala, ~18 params al MID vía `Set{Scalar,Vector}ParameterValueonMaterials` — sin variable MID). `Phase = I/RingCount`, `RandOff = frac(I·0.618034)`.
🔴 **El incremento de `Idx` va DESPUÉS del `CallFunction`** (dentro del `:then` del cast): un getter puro se re-evalúa en cada nodo exec consumidor — el `(bind)` del DSL no congela el valor. Con el orden call→increment, init 0 da fases 0..N−1 (gotchas §307).
🔴 **Getters del DSL por CATEGORÍA**: `Variables|A-Forma|GetPortalRadius` (espacios comidos), no `Variables|Default|…` (gotchas §306).
🔴 **Regenerar funciones**: `remove_function_graph` de una función LLAMADA deja el nombre reservado (devuelve `Nombre_0`) — sacar primero la función que la llama, y el call del CS re-resuelve solo al recompilar con el mismo nombre.

## La estación en la galería (fila 10, tag `GAL_9`)
⚠ Los arrays vivos del director tenían 9 filas GAL_0..GAL_8 (no coincide con el tracker del director — creerle al nivel). Actores en carpeta `Galeria`:
- `GAL_9_Anchor` (269100, 100000, 0) — **SIN tags**: taguearlo hizo que `GalShow` des-escondiera su marcador (esfera gris en medio del túnel).
- `GAL_9_RingTunnel` (269900, 100000, 170) yaw 0 → recula hacia +X; `GAL_9_Ganzfeld` (270000, 100000, 0) `ShellRadius/Height` 4000 (**tiene que contener el punto de fuga** — es opaco), **`Mode 1` (la textura Turrell existente)**.
- Fila agregada a `Anchors`/`StationTags`/`Names` ("10  Ring Tunnel") con la receta de crecer arrays replicando el último elemento.
- ⚠ **`StartAt` del director quedó en 9** para iterar esta estación — volver a 0 antes de empaquetar (regla `DebugStartRoom`).

## Lecciones de la iteración en vivo (2026-09-07)
1. 🔴 **"Lo de la instancia le gana al Blueprint", otra vez**: la instancia congeló los valores del spawn; cambiar el CDO no la tocó. Perillas de look → escribirlas EN LA INSTANCIA (+ `load_level` para re-correr el CS).
2. 🔴 **Un `set_properties` al CDO sin `compile_blueprint` no llega a las instancias** (declarado ≠ aplicado).
3. 🔴 **La orientación de la V del UV NO se deduce en el escritorio**: §302 dice que el import invierte la V, pero acá la configuración que Beltrán aprobó es `step(0.5, UV.y)` para el borde interior y `pow(UV.y)` para el lavado; mi "corrección" teórica la rompió dos veces (*"agujero demasiado pequeño"*). Un cambio por pasada y que juzgue el autor.
4. Los `MaterialExpressionCustom`: crecer `inputs` **replicando el elemento existente tal cual** y renombrar en una segunda llamada (receta §~1296); el código se re-escribe entero por `set_properties` sin tocar los cables.

## Pendientes / preguntas a Beltrán
- [ ] Su pasada de perillas (colores, velocidad, estiramiento) y el visor (paralaje + fill del centro).
- [ ] **¿Qué es la esfera gris con sombra en el eje del túnel?** Aparece en editor Y en PIE (¿la protoalma del pawn? ¿un marcador?). Un click suyo en el viewport lo resuelve.
- [ ] `GAL_10_Shell` (cascarón huérfano del fur en x=299100) sigue en el nivel — ¿se borra?
- [ ] Sacar `WidthFreq` (sin efecto) — panel honesto.
- [ ] Nada commiteado.
