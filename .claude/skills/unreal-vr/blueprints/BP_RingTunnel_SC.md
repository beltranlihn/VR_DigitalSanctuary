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


## 🔧 2026-09-08 (v4) — material propio para el contenedor · anillos OPACOS · el fade pasa a la SOMBRA
Tres pedidos de Beltran en la misma pasada, todos sobre la misma causa raiz: **el tunel dependia de materiales que no eran suyos y de la translucidez para ordenarse.**

### 1. `M_RingFrame_SC` — el aro fijo deja de usar el material de la esfera
🔴 **El sintoma:** al agregarle WPO de olas a `M_Ganzfeld_SC` (ver `BP_Ganzfeld_SC.md`), **el aro del tunel se deformo** — Beltran lo vio de una: *"al tomar el de la esfera se deforma"*. El `Build` ya le apagaba `BreathAmount` y `VeilAmount` a mano, pero no podia conocer `WaveAmount`, que nacio despues.

🚩 **La leccion general: un material compartido con parametros "apagados a mano" desde afuera es una bomba de tiempo.** Cada perilla nueva del material duenio rompe al consumidor, en silencio, y el consumidor no tiene forma de saberlo. Si un objeto solo necesita una parte del material, **necesita su propio material**, no una lista de apagados.

✅ **`M_RingFrame_SC`** (nuevo, `Core/Light/`): unlit · **Opaque** · two-sided · **un solo parametro, `FrameColor` (vector) → Emissive**. Nada mas.
💡 **De regalo, un ahorro de fill real:** el `Build` le empujaba `FrameColor` a **ColorTop, ColorBottom Y ColorMid** — o sea que la mezcla convexa de tres colores IDENTICOS daba un color plano, y para eso el aro estaba corriendo **6 muestras de simplex 4D por pixel**, el dither R2 y la cadena de tres modos. Ahora es una constante.
- `ContainerRing` (CDO) apunta a `M_RingFrame_SC` via `overrideMaterials`.
- `Build` pasa de **5 pushes a 1**: se borraron los dos `SetScalar` (BreathAmount/VeilAmount), dos de los tres `SetVector` y sus dos `ToVector(LinearColor)` huerfanos; el que quedo se renombro a `"FrameColor"`. Verificado releyendo el DSL.
- ⚠ `ContainerScale` y `FrameColor` siguen siendo las unicas perillas del marco. Sin cambios en el panel.

### 2. Los anillos vuelven a ser OPACOS
Pedido: *"vamos a quitar la transparencia al material de los anillos, para no seguir teniendo problemas con la superposicion de prioridad"*. `M_RingTunnel_SC`: `blendMode` **`BLEND_Translucent` → `BLEND_Opaque`**, y el `MP_Opacity` **desconectado**.
👉 Con esto **el problema de orden desaparece por construccion**: la profundidad ordena sola, por pixel, y no hay ninguna prioridad que mantener.
💡 El nacimiento no necesita el fade de opacidad: los anillos nacen coincidentes con el `ContainerRing`, que es **opaco y escribe profundidad**, asi que los tapa gratis (era el argumento original de la v1).

### 3. `FadeInTime` / `FadeOutTime` ahora modulan la SOMBRA
Pedido: *"en vez de ser para la opacidad, seran para aparecer o desvanecer el efecto de sombra al inicio y al final"*.
El `Custom` **`RingMask`** ya calculaba exactamente la envolvente que hacia falta, y no habia que escribir nada nuevo:
```
t  = frac(Phase + Time*Speed)              // 0 = nace, 1 = punto de fuga
fi = saturate(t / FadeInTime)
fo = saturate((1 - t) / FadeOutTime)
mask = fi * fo
```
✅ Un unico `Multiply_0` nuevo: `ShadowAmount × RingMask → RingPix.ShadowAmount`. La sombra **entra** en `FadeInTime` y **se va** en `FadeOutTime`; con cualquiera de los dos en ≤0 ese extremo queda sin fade (el `Custom` ya lo contempla). `ShadowSoft` no se toco.

### 🔴 Pendiente que dejo esto: `StepSort` quedo MUERTO
`StepSort` recalcula `TranslucencySortPriority` de los 16 anillos en cada tick del timer. **Con los materiales opacos esa propiedad no hace absolutamente nada** — es un bucle por tick que no produce ningun efecto. No se elimino: es logica del BP que Beltran esta usando, y la regla del proyecto es preguntar antes de sacar. **Sacarlo es: quitar el timer del EventGraph, la llamada al final del `ConstructionScript`, la funcion `StepSort` y la variable huerfana `WrapCount`.**
⚠ Si algun dia se vuelve a translucido, esto hay que revivirlo.

### Estado
Guardados: `M_RingFrame_SC` (nuevo), `M_RingTunnel_SC`, `BP_RingTunnel_SC`. **Sin verificar en viewport ni en visor** — el juicio queda en Beltran, que tiene el editor abierto. Hay 8 actores `BP_RingTunnel_SC` en `/Game/TestMeshes`; el cambio es del BP y del material, asi que aplica a todos.

### 🎨 2026-09-08 (v4b) — "los anillos se ven mas oscuros que el fondo con el mismo color"
Beltran queria que `ColorFar` = color del fondo para que los anillos **se desvanezcan** en el, y no le cerraba: *"veo que estan mas oscuros que el fondo a pesar de tener el mismo color"*. Tenia razon y hay dos causas, una en cada lado. **Medidas, no estimadas:**

**El anillo se oscurece** — `CFar` nunca llegaba a la pantalla, lo multiplicaban tres terminos:
| Termino | Formula | Con los defaults |
|---|---|---|
| banda | `1 + BandGlow*(vin − 0.3)` | `BandGlow 0.35` → **0,895** donde `vin=0` (el `−0.3` pone el punto neutro en vin=0,3, o sea que en buena parte del anillo **oscurece**) |
| sombra | `1 − ShadowAmount*sh` | `ShadowAmount 0.5` → hasta **0,5** |
| brillo | `* Brightness` | **1,2** |
Producto en la zona mas oscura: **0,54 × CFar**.

**Y el fondo se aclara** — la esfera Ganzfeld saca `color × Veil × sombra × Brightness`, con `Brightness 1,30` y `Veil ≥ 1`. O sea ~**1,3 ×** su color escrito.
👉 **Mismo valor tipeado → hasta 2,4× de diferencia en pantalla.**

✅ **Arreglo (una linea en `RingPix`):** el resultado converge **literalmente** a `CFar` despues del sombreado.
```
col = ...banda... ...sombra... * Brightness;
return lerp(col, CFar, far);        // far = saturate((t − 0.3333)*1.5)
```
`far` va de 0 (a un tercio del viaje) a 1 (punto de fuga), asi que el anillo **abandona progresivamente su propio sombreado** durante los ultimos dos tercios y en el extremo **es exactamente `CFar`**, sin ningun multiplicador. Es la definicion literal de desvanecerse. Sin perillas nuevas; si se quiere que empiece antes o despues, la palanca es el `0.3333`/`1.5` de esa linea.

🔴 **Lo que el arreglo NO puede resolver, y hay que decirlo:** el fondo **no es un color**, es la mezcla fluida de `ColorTop/Mid/Bottom` moviendose. El empate solo puede ser en promedio. En `GAL_3` el `ColorBottom` (0.21, 0, 0.27) es **mucho mas oscuro** que Top (0.16, 0.18, 0.77) y Mid (0.08, 0.05, 0.80) → con esa esfera no existe un `CFar` unico que empate. Para un desvanecido limpio: acercar los tres colores del cascaron entre si (que es lo que un Ganzfeld quiere igual), y poner su `Brightness` en **1** para que el color tipeado SEA el pixel.

🚩 **Regla general:** "igualar dos colores" entre dos materiales **no se hace igualando los parametros**, se hace igualando **la salida**. Antes de copiar un valor, recorrer que lo multiplica de ahi al emisivo — en los dos materiales.

## 🔲 2026-09-08 (v5) — `ShapeIndex`: rectangulo de cantos redondeados (superelipse)
Pedido de Beltran, con croquis: *"un cambio de shape, un nuevo index de shape. Es un rectangulo con cantos redondeados y un poco de curvatura. (...) Este shape aplica al contenedor y los anillos. El back debe cambiar de circulo a un rectangulo de las mismas proporciones."* Y: *"agrega un nuevo actor (...) ya que no quiero perder la composicion que ya tengo"*.

### 🔴 Por que NO hicieron falta mallas nuevas
Leyendo `RingWPO` primero: la forma del anillo **es circular por construccion**, no por la malla. Todo el desplazamiento es **radial** (`push = rdir * (...)`), y un empuje radial preserva la circunferencia. Entonces alcanza con **remapear el radio en funcion del angulo**, y eso sirve igual para anillos, contenedor y fondo — **con las mallas que ya hay**.

La funcion es una **superelipse**:
```
k(θ) = ( |cosθ|^n + |sinθ/a|^n ) ^ (−1/n)     con a = ShapeAspect, n = ShapeCorner
```
`n = 2` da una elipse · `n` grande da un rectangulo de cantos duros · **`n ≈ 4` es el rectangulo redondeado con los lados apenas curvados** del croquis. 💡 Y `k ≤ 1` siempre (para `a ≤ 1`), o sea que la forma **solo achica**: no hay que tocar bounds ni `boundsScale`.

### Las tres perillas nuevas (cat. `A - Forma`)
| Perilla | Rol | Default |
|---|---|---|
| **`ShapeIndex`** | **0 = circulo (lo de siempre) · 1 = rectangulo redondeado** | 0 |
| **`ShapeAspect`** | alto / ancho. 1 = cuadrado, 0,55 ≈ 1,8:1 apaisado | 0,55 |
| **`ShapeCorner`** | dureza del canto: 2 = elipse, 4 = redondeado, 8+ = casi recto | 4,0 |

⚠ `ShapeIndex` es **float** (no int) para no arrastrar un `Conv` en los tres sitios donde se empuja. Se lee 0/1 en el panel.

### Donde se implemento
| Material | Que se agrego |
|---|---|
| `M_RingTunnel_SC` (anillos) | **`Custom` nuevo `RingShape`** (entradas `WP/ObjPos/Off/Idx/Aspect/Corner`) que toma la posicion **ya desplazada por `RingWPO`** y devuelve el offset extra de la superelipse. `MP_WorldPositionOffset` pasa a ser `RingWPO + RingShape` via un `Add`. **El `RingWPO` original no se toco.** |
| `M_RingFrame_SC` (contenedor **y fondo**) | **`Custom` `FrameShape`** (igual pero sin `Off`) conectado directo a `MP_WorldPositionOffset`. El material no tenia WPO. |

🔴 **El fondo (`Backplate`) paso de `M_GalleryProp_SC` a `M_RingFrame_SC`**, y `Build` le empuja `FrameColor` (antes `PropColor`). Asi hereda la forma **con las mismas proporciones** que el contenedor sin ningun asset ni codigo extra — es el mismo material, con su propio MID por componente, asi que conserva su color propio (`BackColor`).

`Build` empuja las 3 perillas al `ContainerRing` **y** al `Backplate`; `SetupRing` las empuja a cada anillo.

### 🔴 Como agregarle un input a un `MaterialExpressionCustom` (receta confirmada)
`set_properties` **rechaza crecer el array y cambiar sus elementos en la misma llamada**: *"ArrayAdd: elements changed alongside the size change; insertion points are ambiguous"*. La receta que funciona, en **tres pasos**:
1. `set_properties` con el array del tamaño final, **todos los elementos copias identicas del existente** (`inputName: "None"`, `expression: "None"`).
2. `set_properties` otra vez, **solo renombrando** los `inputName` (mismo tamaño → permitido).
3. `connect_expressions` a cada input por nombre.
💡 Y el corolario: **para un `Custom` NUEVO conviene esto; para uno EXISTENTE con muchas entradas cableadas, mejor crear un `Custom` aparte y sumar su salida** — que es lo que se hizo con `RingShape` (el `RingWPO` tenia 17 entradas y re-serializarlas era el riesgo).

### El actor de pruebas
**`GAL_TEST_RingTunnel_Rect`** en `/Game/TestMeshes`, en **(330000, 100000, 127.7)** — fuera de la fila de estaciones, sin tocar nada de la composicion. Se le copiaron **todos** los valores autorados de `GAL_9_RingTunnel` (colores, velocidades, sombra, wobble, spiral, etc.) para que **lo unico distinto sea la forma**. `ShapeIndex = 1`, `ShapeAspect 0,55`, `ShapeCorner 4`.

✅ **Los 8 tuneles existentes quedan intactos**: verificado que `GAL_9_RingTunnel` tiene `ShapeIndex = 0`. Las variables nuevas nacen en 0 en las instancias — y aca eso juega **a favor**: 0 = circulo = comportamiento anterior. (`ShapeAspect`/`ShapeCorner` en 0 no importan porque el codigo hace `max(Corner, 2)` / `max(Aspect, 0.05)` y ademas solo corren con `Idx ≥ 0.5`.)

### ⚠ Limitacion heredada
El remapeo trabaja sobre **Y/Z de MUNDO**, igual que el `RingWPO` original (que usa `float3(0, cos, sin)`). O sea: **el actor tiene que estar con yaw 0**, como ya lo estaban todos. Si algun dia hay que rotar un tunel, hay que pasar los dos a espacio local del actor.

### 🔴🔴 CORRECCION (misma jornada): la superelipse NO era un rectangulo con corner radius
Beltran, con captura: *"el que hiciste ahora no es un rectangulo con corner radious, es un como un ovalo medio cuadrado"*. Exacto — **una superelipse es un squircle**: los "lados" nunca son rectos y las esquinas no tienen un radio definido, solo un exponente. Yo elegi la formula por barata, no por parecida al croquis.

✅ **Reemplazada por el SDF real de rounded-box**, resuelto analiticamente para el radio en cada direccion `d`:
```
q  = (a − r, b − r)                       // caja interior
tf = min(a/|d.x|, b/|d.y|)                // salida por un LADO RECTO
tc = d·q + sqrt((d·q)² − |q|² + r²)       // salida por el ARCO de la esquina
k  = (el punto de tf cae fuera de q en LOS DOS ejes) ? tc : tf
```
Ahora los lados **son rectos de verdad** y la esquina **es un arco de circulo de radio `r`**, que es lo que quiere decir "corner radius".
⚠ **`ShapeCorner` cambio de significado**: era el exponente de la superelipse (2–8), ahora es el **radio de esquina normalizado 0–1** (0 = angulo recto, 1 = totalmente redondeado / estadio). Default **0,35**. Se mantuvo el nombre a proposito para no re-cablear los 4 sitios donde se empuja.

### 🌗 Y la parte que yo no habia entendido: la forma es CURVA, no plana
El trazo suelto de arriba del croquis era la **vista superior**. La forma **envuelve** al espectador.

✅ Se agrego **`ShapeCurve`** (grados de arco, 0 = plano, default **40**), con **la misma formula del modo Cylinder de UE que ya usa el `Glass` de `BP_InstructionsPanel_SC`** (`BuildGlass`) — que es justo la que Beltran recordaba:
```
R = hw / (arc/2)          Apo = R·cos(arc/2)
ang = u · (arc/2)         con u = x normalizado en [−1, 1]
x  = R·sin(ang)           offsetDepth = Apo − R·cos(ang)
```
El arco se aplica **despues** del rounded-box, sobre el eje horizontal, y el desplazamiento en profundidad va al eje X (el del tunel). `u` se normaliza por el radio de cada vertice, asi que **el borde interior y el exterior del anillo se curvan juntos** y la banda conserva su ancho. Signo negativo = curva al reves.

### Perillas finales (cat. `A - Forma`)
| Perilla | Rol | Default |
|---|---|---|
| `ShapeIndex` | 0 = circulo · 1 = rectangulo redondeado curvo | 0 |
| `ShapeAspect` | alto / ancho | 0,55 |
| `ShapeCorner` | **radio de esquina 0–1** (0 = recto, 1 = estadio) | 0,35 |
| `ShapeCurve` | **grados de arco de la curvatura**. 0 = plano. 🔴 **El SIGNO es hacia donde envuelve** — Beltran lo pidio al reves del primer intento, asi que el default quedo en **−40** | −40 |

🚩 **Trampa de HLSL que costo un compile:** **`half` es un TIPO reservado** — `float half = arc*0.5;` genera `float float = ...` en el shader traducido y falla con *"cannot combine with previous 'float' declaration specifier"*. Renombrado a `ha`. Vale para cualquier `Custom`: evitar `half`, `min16float`, `matrix`, `sample`.

### TODO
- [ ] 🔴 **Sin ver.** No se pudo juzgar en el viewport (ver la nota del frame stale mas arriba). Beltran ajusta las 4 perillas mirando.
- [ ] Si el canto queda facetado, el limite es la malla del anillo (`SM_RingTunnel_SC`), no la formula.
- [ ] La curvatura mueve geometria en el eje X (el del tunel). Con `ShapeCurve` **negativo** (el sentido que pidio Beltran) los bordes vienen hacia el espectador. Si el aro fijo se hunde en el nacimiento de los anillos, compensar con `ContainerScale`.

### 🔴🔴 2026-09-08 (v5c) — la forma se rompia al ROTAR el actor. Arreglado
Beltran duplico el tunel y lo roto en el world: la copia rotada **perdio el rectangulo y colapso en una lente**. Era exactamente la limitacion que este tracker ya declaraba dos parrafos mas arriba — y que aparecio a las pocas horas.

🚩 **La leccion: una limitacion documentada no esta mitigada.** Escribir *"si algun dia hay que rotar, hay que pasar a espacio local"* no evito nada; lo unico que hizo fue que el diagnostico tardara cero. Cuando el costo de hacerlo bien de entrada es bajo, se hace de entrada.

**La causa:** la forma se calculaba sobre **Y/Z de MUNDO** (`float2 p = float2(rad.y, rad.z)`), asumiendo que el tunel mira hacia +X. Con el actor rotado, el plano del anillo deja de ser el plano YZ del mundo y el remapeo proyecta sobre ejes equivocados.

✅ **Arreglo: el material recibe el eje REAL del actor.**
- Parametro vectorial nuevo **`AxisRight`** en los dos materiales (default `(0,1,0)`).
- El BP lo empuja con **`GetActorRightVector`** al `ContainerRing`, al `Backplate` y a cada anillo (el Construction Script vuelve a correr al mover o rotar el actor, asi que se mantiene solo).
- Los dos `Custom` trabajan ahora en la base del actor:
```
axR = normalize(AxisRight)      axU = (0,0,1)      axF = cross(axR, axU)
p   = float2(dot(rad, axR), dot(rad, axU))     // plano del anillo
...rounded box + curvatura...
return (dx)*axR + (dy)*axU + (profundidad)*axF
```
💡 Se eligio **pasar el eje como parametro en vez de usar nodos `Transform` World→Local**: los `Transform` aplican la matriz completa del componente, **que incluye su escala** (los anillos tienen escala no uniforme y el `Backplate` es `(r, r, 0.02)`), y eso habria metido una distorsion nueva. Con dot/cross contra un vector unitario no hay escala en el medio.

⚠ **Lo que sigue sin ser rotacion-proof:** `RingWPO` (el original, no lo escribi yo) usa `u = float3(0, cos, sin)` para el eje de estiramiento — **tambien es mundo**. Con el tunel rotado, el `WidthVariation`/`WobbleAmount` empujan fuera del plano del anillo. Es mas sutil que el glitch de la forma, pero esta ahi. **Arreglarlo es pasarle `AxisRight` tambien a `RingWPO`** (2 pasos mas de la receta de inputs, 17→18). No se hizo en esta pasada para no tocar el nodo que mueve todo el tunel sin que Beltran lo vea antes.
⚠ Asume **actor upright** (arriba = Z de mundo). Pitch/roll seguirian rompiendo.

### 🔺 2026-09-08 (v5d) — "los corner estan muy geometricos": era la MALLA, no la formula
Beltran, con un primer plano de la esquina: *"deben ser mas suaves"*. **Medido antes de tocar nada:**
| Malla | verts | tris | segmentos |
|---|---|---|---|
| `SM_RingTunnel_SC` | 194 | 192 | **96** |
| `SM_RingFrame_SC` | — | 192 | **96** |
| `Backplate` | `/Engine/BasicShapes/Cylinder` | — | **32** (!) |

Con 96 segmentos, la esquina redondeada abarca ~28 % de un cuadrante → **unos 6 vertices por esquina**. Un arco de 90° con 6 tramos **es** un poligono. El SDF calcula el arco exacto; la malla no tiene con que dibujarlo.

🔴 **Por que la redistribucion angular no alcanzaba** (se evaluo y se descarto con numeros, no por intuicion): repartir los 96 vertices por longitud de arco en vez de por angulo lleva la esquina de 6,5 a ~9 vertices. Un 40 % mejor y sigue facetado. **La densidad era el unico lever real.**

✅ **Tres mallas nuevas a 256 segmentos** (512 tris, 514 verts c/u), con la geometria EXACTA de las originales (bounds verificados ±50, z=0):
| Nueva | Reemplaza a | Geometria |
|---|---|---|
| `SM_RingTunnel_HD_SC` | `SM_RingTunnel_SC` | anillo r 10→50 (el hueco lo abre el WPO) |
| `SM_RingFrame_HD_SC` | `SM_RingFrame_SC` | anillo r 25→50 (agujero horneado) |
| `SM_RingBack_HD_SC` | `Cylinder` del motor | **disco lleno** r 50 — el cilindro de fabrica tiene 32 lados y era el mas facetado de los tres |

💡 **La convencion de UV no se adivino: la dicta el shader.** `RingWPO` hace `isInner = step(0.5, UV.y)` y `RingPix` usa `1 − UV.y` para la sombra ⇒ **v = 0 en el borde EXTERIOR, v = 1 en el INTERIOR**. Se replico asi y el color/sombra siguen igual. 🚩 Regla general: antes de regenerar una malla que ya usa un material, **leer el material para deducir la convencion de UV** en vez de asumirla.

Se repuntaron los 18 componentes del CDO (`Ring0..Ring15`, `ContainerRing`, `Backplate`) — **assets nuevos, los viejos intactos**, asi que volver atras es cambiar la malla en el componente. (No se reimporto encima de los originales a proposito: `gotchas` ya tiene el caso de que **borrar+reimportar un asset mata los literales de pin** que lo referencian.)

⚠ **Costo:** los 8 tuneles circulares tambien pasan a la malla densa (los componentes viven en el CDO). Son ~46.000 triangulos extra en total repartidos en 9 actores — sin cambio visual para ellos (un circulo de 96 lados ya se veia redondo). Si algun dia molesta, el arreglo limpio es una variable `RingMesh` empujada por `SetupRing`.

### 🔴🔴 2026-09-08 (v5e) — el facetado NO era densidad: era DONDE caen los vertices
Con la malla ya en 256 segmentos, Beltran: *"SE SIGUEN VIENDO LOS VERTICES EN LOS CORNER"* y despues el dato que resolvio el caso en una frase: **"los circulos se ven bien. Son los cuadrados los que se ven mal"**.

🔴 **Misma malla, mismos 256 vertices, y el circulo sale liso.** Eso descarta la densidad de una y apunta a la unica otra variable: **la distribucion angular**.

**La cuenta** (con `Aspect 0,55` · `Corner 0,35` ⇒ `r = 0,1925`, `q = (0,8075 · 0,3575)`):
| Tramo del cuadrante | Angulo | Vertices (de 64/cuadrante) |
|---|---|---|
| lado recto derecho | 0° → 19,7° | ~14 |
| **esquina redondeada** | 19,7° → 34,3° = **14,6°** | **~10** |
| lado recto superior | 34,3° → 90° | ~40 |
👉 La esquina —lo unico curvo— se queda con **10 vertices**, y los lados rectos se llevan 54 **sin usarlos** (una recta necesita 2 puntos). El circulo se ve bien porque reparte los 256 parejo: 1,4° por faceta.

🚩 **La leccion de diagnostico, que es la que importa:** yo mire "esquina facetada" y salte a "faltan poligonos" — y agregue 3 mallas y repunte 18 componentes **sin que eso fuera la causa**. El dato que lo resolvio no fue una medicion mia sino **la comparacion que hizo Beltran**: mismo asset, un caso bien y el otro mal ⇒ la variable no es el asset. **Ante "esta facetado", la primera pregunta no es cuantos vertices hay, sino como estan repartidos** — y si algo con la MISMA malla se ve bien, la densidad ya quedo descartada.

✅ **Arreglo: warp angular por tramos antes de resolver el SDF.** Se calculan los dos angulos frontera (`ph1 = atan2(q.y, a)`, `ph2 = atan2(b, q.x)`) y se remapea el angulo de entrada para que **el 70 % del rango caiga en la esquina**, repartiendo el 30 % restante entre los dos rectos en proporcion a su largo:
```
ph < c1  → recto 1     c1 = (1 − 0,70) · q.y/(q.x + q.y)
ph < c2  → ESQUINA     c2 = c1 + 0,70
resto    → recto 2
```
Resultado: **~45 vertices por esquina** (2° por faceta) y 6 y 13 en los rectos, que sobran. Coste: unas 10 instrucciones ALU, cero mallas nuevas.
⚠ El warp usa el MISMO angulo para el borde interior y el exterior del anillo, asi que la banda no se retuerce y conserva su ancho.
⚠ Guarda para `Corner = 0` (esquina viva): con `r ≈ 0` la ventana de la esquina es de ancho cero, asi que `cs` pasa a 0 y el reparto vuelve a ser proporcional a los rectos. Sin esa guarda, el 70 % de los vertices colapsaba en un punto.

💡 **Las mallas HD siguen siendo utiles** (el cilindro del fondo tenia 32 lados y era el peor), pero **no eran la causa**. Con el warp, incluso las de 96 segmentos darian ~17 vertices por esquina.


## 🌬️ 2026-09-17 — TAMAÑO y VELOCIDAD con la respiración ([[BP_BreathManager_SC]])
Pedido de Beltrán: *"tamaño al inhalar, y velocidad baja. Luego, velocidad y tamaño al exhalar"* → **inhala: el portal crece y el viaje frena · exhala: el viaje fluye y el portal se achica.**

🔴 **La velocidad NO se puede tocar**: `RingPix`, `RingWPO` y `RingMask` calculan `t = frac(Phase + Time·Speed)`; cambiar `Speed` en caliente hace saltar todos los anillos (con Time = 600 s, un Δ de 0,02 son 12 ciclos).

- **Material `M_RingTunnel_SC`**:
  - `Custom` **`BreathPhase`** = `Phase + Speed·(GIn·FlowIn + GOut·FlowOut)` → entra al `Phase` de **los tres** `Custom` (color, forma y fade siguen la misma fase). La velocidad efectiva queda `Speed·(1 + In·max(S,0) + Out·max(−S,0))`, sin saltos, y en reposo no cambia nada.
  - `Custom` **`BreathSize`** (`WP`, `ObjPos`, `Off`=`RingWPO`, `TimeIn`, `Phase`, `Speed`, `CurveExp`, `VPt`, `S`, `GIn`, `GOut`):
```
m   = 1 + max(S,0)·GIn + max(−S,0)·GOut
lam = 1 − exp(−max(CurveExp,0.01)·frac(Phase + TimeIn·Speed))
return Off + (m−1)·((WP−ObjPos)·(1−lam) + (Off − (VPt−WP)·lam))
```
    = escala cada anillo sobre su centro en proporción a `(1−λ)`: **en la boca crece entero, en el punto de fuga no cambia**. Alimenta `RingShape.Off` y `Add_0.A` (la forma rectangular se calcula sobre la posición ya escalada).
    🔴 **Duplica la ley `λ = 1 − e^(−K·t)` de `RingWPO`**: si esa ley cambia, cambiarla también acá.
- **Material `M_RingFrame_SC`**: `Custom` **`BreathFrame`** = `(m−1)·(WP−ObjPos) + m·FrameShape` → WPO. El marco crece igual que los anillos en la boca (`FrameShape` es homogénea de grado 1, por eso `m·Shape` es exacto, rectángulo y curvatura incluidos). El `Backplate` usa el mismo material pero **no recibe** las perillas → no se mueve.
- **BP**: perillas `BreathSizeIn/Out` · `BreathSpeedIn/Out` + `ApplyBreath` al final del Construction Script: `ContainerRing` (tamaño) + bucle `GetComponentsByTag(StaticMeshComponent, "TUNRING")` → cast → 4 parámetros por anillo.
  🔴 **Trampa pagada**: el DSL **perdió los dos literales** de `GetComponentsByTag` (quedó `ActorComponent` + tag `None` = bucle vacío, **compilando en verde**): el primer argumento posicional se lo comió el pin `self`. Corregido con `set_pin_value` y verificado leyendo el nodo.
- **Instancias** `GAL_9` (8 túneles) y `GAL_10` (3 rect): `SizeIn 0,2` · `SizeOut −0,15` · `SpeedIn −0,75` (×0,25) · `SpeedOut 0,8` (×1,8). La `Speed` negativa (el Rect que va al revés) se respeta.
- ✅ Verificado en los MIDs: anillos (circular y rect) con las 4, marco con las 2, fondo sin ninguna.
- 💡 El tamaño va en el shader y no escalando el actor: 8 túneles × 18 componentes serían 144 transformadas por frame en el CPU del Quest.


### 🌬️ 2026-09-17 (2ª pasada) — curva SUAVE y rango exagerado
Beltrán tras probar: *"llegó muy duro a los valores máximos y mínimos, no suave como con la esfera"* y *"un poco más exagerados"*.
- **Causa (en el manager, no acá):** `BreathSigned` era `clamp(gain·y)` → con ganancia 1,5 una respiración normal chocaba contra ±1 y quedaba plana. Ahora es `k·y/(1+(k−1)|y|)` (techo suave, `SignedGain` 2).
- **Mapeo nuevo del consumidor** (sin quiebre en 0 aunque las ganancias sean asimétricas): `m = 1 + S·lerp(−Out, In, smoothstep((S+1)/2))`. `In` = fracción a inhalación plena, `Out` = a exhalación plena, igual que antes.
- `BreathSize` y `BreathFrame` con la curva suave (`BreathPhase` ya usaba los flujos, ahora suaves desde el manager).
- **Valores (11 túneles)**: `SizeIn 0,35` · `SizeOut −0,25` · `SpeedIn −0,9` (×0,1) · `SpeedOut 1,5` (×2,5).


### 🌬️ 2026-09-17 (3ª pasada) — acompañar la respiración lenta, suavidad de resorte, más exagerado
Beltrán: *"si hago una respiración lenta deben demorarse más en llegar al máximo o mínimo, acompañando mi movimiento"* · *"sigo sintiendo que está un poco duro"* · *"los valores más exagerados, menos el metaball"*.
- **Causa (en el manager):** (1) `HorizTau` 3 s: la base del band-pass alcanzaba a una respiración lenta a mitad de la inhalación → el pico llegaba ANTES del final; (2) dos saturaciones encadenadas (`x/(1+|x|)` del nivel y el techo suave de `SignedGain`) = una sola muy comprimida: casi todo el recorrido quedaba pegado al máximo.
- **Arreglo (manager):** `HorizTau` **6**; `S` sale del band-pass CRUDO en cm (`x = (HFast−HSlow)·SignedGain`, `SignedGain` 1 = 1 cm) con codo suave `x/(1+|x|³)^(1/3)` (lineal hasta ~0,7) y pasa por un **resorte críticamente amortiguado** (`SmoothFreq` 6): velocidad continua, sin rebote.
- ✅ Medido en PIE con respiración de prueba de 10 s: el máximo llega al final de la media onda (no antes), la velocidad de `S` sube y baja suave.
- **Pedido**: *"al exhalar debiera aumentar la rotación de los círculos, así se ve como un espiral"*.
- **Círculos (GAL_9)**: un círculo girando no se ve; lo que se ve es su estiramiento. `Custom` **`BreathStretch`** → `RingWPO.WidthVar` = `WidthVar + GSt·e` (e = parte exhalada suave de S) y `Custom` **`BreathRandOff`** → `RingWPO.RandOff` = `RandOff + GSp·FlowOut/2π`: el eje del estiramiento (que ya se tuerce 49 rad con la profundidad) **gira mientras se exhala** → espiral.
- **Rectángulos (GAL_10)**: `Custom` **`RingShapeTwist`** reemplaza a `RingShape` (mismo código, con los ejes del plano rotados `θ = GTw·e·t`): en la boca θ = 0 (calza con el marco fijo) y crece hacia el fondo → el pasillo se tuerce en espiral al exhalar y se destuerce al inhalar. Con `GTw` 0 es el `RingShape` de antes.
- Perillas nuevas `BreathStretchOut` · `BreathSpinOut` (rad/s a exhalación plena) · `BreathTwistOut` (rad al fondo). `ApplyBreath` ahora pasa `self` explícito a `GetComponentsByTag` → los literales ya no se pierden.
- **Valores**: GAL_9 `SizeIn 0,55` · `SizeOut −0,35` · `SpeedIn −0,85` · `SpeedOut 2,5` · `StretchOut 0,35` · `SpinOut 1,2` · GAL_10 igual en tamaño y velocidad + `TwistOut 3,0`.
