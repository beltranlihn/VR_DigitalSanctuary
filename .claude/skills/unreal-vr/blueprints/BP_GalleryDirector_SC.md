# BP_GalleryDirector_SC — el recorrido de la galeria de efectos (Gallery/)

> Creado 2026-09-04, pedido de Beltran: *"Puedes armar el sistema ordenado en el world, donde yo pueda ir avanzando entre los distintos efectos? Ahora se me hace dificil porque estan todas las cosas puestas en cualquier parte."*
> **Estado: 🟢 arranque verificado en PIE.** Medido con la galeria en la estacion 0: el pawn en su anchor, `GAL_0_LightShaft` VISIBLE y los otros nueve actores (incluidos los 4 cubos de la niebla) OCULTOS. ⬜ Falta apretar los botones — eso necesita manos, o sea visor / PIE con mandos.
> 🔴 **Si los botones no se ven, leer la seccion "por que se arman en el primer Tick"**: es el modo de fallo conocido de este BP.

## Donde vive: en `/Game/TestMeshes`, NO en un nivel nuevo
El plan decia "nivel nuevo `L_EffectGallery`". Se hizo **en el nivel de pruebas que ya se usa**, por dos razones:
1. **Un nivel nuevo hay que amueblarlo** (GameMode, PlayerStart, pawn). `TestMeshes` ya arranca con el pawn VR posesionado y probado.
2. 🔴 **Ordenar el nivel existente habria significado mover actores de Beltran**, que es justo lo que no se hace. La galeria se armo **lejos, en `y = 100000`**, sin tocar una sola cosa de lo que ya habia.

Todo lo de la galeria vive en la carpeta de outliner **`Galeria`** y sus labels empiezan con `GAL_`.

## La fila
Seis estaciones cada **300 m** sobre el eje X, en `y = 100000`. Cada una tiene un **`BP_Anchor`** (el punto de vista, a nivel de piso) y **un actor de efecto**:

| # | Anchor | Efecto | Nota de composicion |
|---|---|---|---|
| 0 | x = −700 | `BP_LightShaft_SC` | el oculo calido, a 7 m |
| 1 | x = 29.400 | `BP_CloudPlane_SC` | el mar de nubes **25 m abajo**, se mira desde arriba |
| 2 | x = 59.200 | `BP_FogSlab_SC` | vertical, con **4 cubos de referencia detras** a 3/12/24/41 m |
| 3 | x = 90.000 | `BP_Ganzfeld_SC` | el anchor va **adentro** del cascaron |
| 4 | x = 120.000 | `BP_VoidField_SC` | idem, adentro |
| 5 | x = 149.050 | `BP_LineField_SC` | la superficie 50 cm bajo el piso del anchor |
| 6 | x = 179.100 | `BP_ShadowStudy_SC` + `BP_ShadowShaft_SC` | la sombra falsa (oscuridad sobre claro) |
| 7 | x = 209.100 | **`BP_Orb_SC` ×3 (Nico)** | los 3 looks lado a lado a 2 m: volumen / iridiscente / matcap. 40 cm, a `y = ±70`, `z = 130` |
| 8 | x = 239.100 | **`BP_RimShape_SC` ×3 (Nico)** | cascaron entero / disuelto a 0,5 / cubo. 1 m, a `y = ±150`, `z = 110` |
| 9 | x = 269.100 | **`BP_LightPanel_SC` ×4 (Nico)** | los 4 modos en grilla 2×2 de 2 m (`y = ±110`, `z = 120/340`), **pitch 90** para que miren al usuario |

> ⚠ **2026-09-07: esta tabla quedó DESACTUALIZADA respecto de los arrays vivos del director** (al armar la estación del túnel, los arrays reales tenían 9 filas `GAL_0`..`GAL_8` — el panel de Nico no figuraba y la numeración corrió). **Creerle al nivel** (`get_properties` de `Anchors`/`StationTags`/`Names`), no a esta tabla. Fila agregada ese día: **tag `GAL_9`, "10  Ring Tunnel", anchor en x = 269.100** → [`BP_RingTunnel_SC`](BP_RingTunnel_SC.md). Dos lecciones de esa alta: los arrays de la instancia se crecen **replicando el último elemento y seteando la fila nueva en una segunda llamada**; y **el anchor NO se taguea** (`GalShow` des-esconde su marcador y aparece una esfera gris en la estación). ⚠ `StartAt` quedó en **9** para iterar el túnel — volver a 0 antes de empaquetar.

### 🆕 2026-09-04 — las 3 estaciones de los efectos de Nico (7, 8, 9)
Se sumaron tras mergear `fx/nico-efectos`. **No hizo falta tocar una sola linea del director**: solo colocar los actores con `GALSTATION` + `GAL_<n>`, un `BP_Anchor` por estacion y tres filas en `Anchors`/`StationTags`/`Names`. Es exactamente lo que el diseño por tags prometia.

Valores de instancia elegidos (los defaults del CDO de Nico ya son buenos; solo se varia el selector):
- **Orbe**: `Look` 0/1/2, `SizeCM` 40, y el matcap 2 (vidrio frio) en la tercera.
- **Rim**: la 2ª con `DissolveThreshold` 0,5 (para que se vea el filo encendido), la 3ª con `Mesh` = Cube.
- **Panel**: `Mode` 0/1/2/3, `PanelSizeX/Y` 200. 🔴 El modo 3 (cercania) lleva **`TouchRadius` 500** en vez de 180: con el panel a 3,5 m del anchor, la esfera de 180 cm no llega y el panel no se enciende nunca. Es el mismo ajuste que hizo Nico para su captura.

### 🔴 2026-09-04 (tarde) — el criterio que fijo Beltran: LOS ENTORNOS ENVUELVEN
Juzgo las tres estaciones de Nico y fue tajante: *"las encuentro bastante fomes… **tenemos que lograr que estos entornos nos envuelvan. No que sean solo frente. Y si hay uno que debe ser solo frente, que igual este envuelto en alguna esfera con color**"*. El diagnostico de fondo: sus efectos (Ganzfeld, VoidField, oceano) son **espacio**; los de Nico eran **props que se miran de frente**. Y parte de la culpa era de la composicion: el panel viene con 20 m de default y se habia achicado a 2 m para que entrara en la estacion — convertido en un cuadrito.

**Las tres reglas que quedan para armar CUALQUIER estacion de aca en mas:**
1. **Nada se compone solo al frente.** Si el efecto es direccional, se lo rodea igual.
2. **Cada estacion lleva su `BP_Ganzfeld_SC` de color** como cascaron — es el "envuelto en una esfera con color" que pidio, y ya existia en la biblioteca (no se construyo nada nuevo).
3. **Escala de sala, no de objeto.** Un panel de 2 m es un cuadro; a 10 m es una pared.

**Como quedaron reorganizadas:**
| # | Antes | Ahora |
|---|---|---|
| 7 Orbe | 3 orbes al frente | los 3 orbes + **cascaron violeta** (`shellRadius` 1400) |
| 8 Rim | 3 formas al frente | las 3 de muestra en el centro + **[[BP_RimField_SC]]: 48 siluetas en anillo de 14 m** que nacen al acercarse + **cascaron verde-azul** (2400) |
| 9 Panel | pared frontal de 25 m | **sala cerrada**: 4 paneles de 10 m a 5 m del centro, uno por lado (yaw 0/90/180/270, `pitch 90`) + **cascaron ambar** (1600) |

⚠ El `TouchRadius` del modo cercania volvio a 400: dentro de una sala de 5 m, los 900 que se habian puesto para la pared frontal encendian todo.

✅ **Verificado en PIE con `StartAt = 7`**: el pawn aparece en `x = 209.100` (el anchor de la 7), el orbe de esa estacion **visible** y el panel de la 9 y la sombra de la 6 **ocultos**. El recogido por tags tomo los actores nuevos sin tocar el BP.
⚠ **Los Construction Scripts NO se re-ejecutan al escribir valores de instancia por MCP** — hay que **recargar el nivel** (`load_level` del mismo nivel) o los MID quedan con los valores viejos. Se hizo, y se verifico despues que los MID existen y las escalas se aplicaron (orbe a 0,4).

🔴 **Los efectos 0, 1 y 2 son instancias NUEVAS, no las de la composicion de Beltran** — las suyas quedaron intactas donde estaban. Y como una instancia nueva nace con los **defaults del CDO**, se le copiaron los valores autorados de las suyas (el haz salia azul y chiquito, y el oceano invisible porque el suyo esta en **escala 65**). Es la misma leccion de siempre: **lo de la instancia le gana al Blueprint**.

💡 **La niebla necesita algo detras o no se lee.** Sin los cubos era una pared blanca lisa. Con ellos se ve lo que hace: el cercano nitido, el segundo lechoso, los lejanos comidos. Para eso se creo `M_GalleryProp_SC` (unlit emisivo, `PropColor` + `Brightness`), porque en esta obra **no hay luces** y un cubo con material de fabrica sale negro.

## Como funciona — 🔴 POR TAGS, para no reprogramar nada
Pedido explicito de Beltran: *"hazlo con tags para cada etapa, asi yo puedo agregar o duplicar elementos para armar cada espacio y no tenemos que volver a programar cada una"*.

**Cada actor de una estacion lleva dos tags de actor: `GALSTATION` y `GAL_<n>`.** Eso es todo lo que hace falta para que pertenezca a esa estacion — una estacion puede tener **un actor o veinte**, y sumar uno es duplicarlo y ponerle los dos tags. No se toca ni el Blueprint ni ningun array de actores.

Tres arrays instance-editable en `GAL_DIRECTOR` (categoria *A - Galeria*), en el mismo orden: **`Anchors`** (el punto de vista de cada estacion), **`StationTags`** (`GAL_0` … `GAL_5`) y **`Names`** (el rotulo). El cuarto array, `Stations`, **se llena solo en `BeginPlay`** con todo lo tagueado `GALSTATION` — no se autora.

**Agregar una estacion:** colocar sus actores con los tags `GALSTATION` + `GAL_6`, colocar un `BP_Anchor`, y sumar una fila a `Anchors` / `StationTags` / `Names`.

⚠ **Un actor sin el tag `GALSTATION` no se apaga nunca** — es la unica forma de que algo quede visible en todas las estaciones (util para un piso comun, si alguna vez hace falta).

- **`BeginPlay`** → `IsValid(BtnNext)` → **`Boot`** (marca listo, **`GalCollect`** recoge por tag todos los actores de estacion, y llama `GoTo(StartAt)`). **`StartAt`** (cat. *A - Galeria*, instance-editable, default 0) es la perilla para **arrancar directo en una estacion** mientras se afina — el equivalente al `DebugStartRoom` del director de la obra. Dejarla en 0. Si los botones no estan asignados, imprime *"GALERIA: los botones no estan asignados en la instancia"* en vez de fallar en silencio.
- **`GoTo(Idx)`** — guarda el indice, **`GalHideAll`** esconde TODO lo tagueado `GALSTATION`, **`GalShow(Idx)`** prende todo lo que tenga el tag de esa estacion, y mueve **al director Y al pawn** al transform del anchor (`bTeleport = true`). Despues pone el nombre en el rotulo y llama `ReArm`.
- **`GalStep(Dir)`** — suma y **envuelve con modulo**, asi la ultima vuelve a la primera.
- **`Tick`** → `Poll`, que es una maquina de dos estados sobre `bWaitRelease`. **No usa el dispatcher `OnPressed`.**

### 🔴🔴🔴 Un paso por apretada: `bWaitRelease`
Sintoma reportado por Beltran: *"si mantengo el trigger sobre el boton cambio infinito de lugares y queda la cagada"*. Y tenia razon, era un bug de diseño mio.

Con `HoldTime = 0` el boton dispara **el primer frame en que hay gatillo + mano cerca**. El `ReArm` limpiaba `bDone` y rearmaba en el mismo frame, asi que con el gatillo sostenido volvia a disparar al frame siguiente, y al siguiente: **una estacion por frame**.

✅ **La maquina correcta:**
```
Poll:        si bWaitRelease -> GalRelease     si no -> GalPoll
GalPoll:     si BtnNext.bDone -> GalStep(+1)   elif BtnPrev.bDone -> GalStep(-1)
GalStep:     bWaitRelease = true ; DESARMA los dos botones ; GoTo(...)
GalRelease:  si NINGUN gatillo esta sostenido -> bWaitRelease = false ; ReArm
```
O sea: **despues de una apretada no se vuelve a armar hasta que el gatillo se suelta.** `Boot` arranca con `bWaitRelease = true`, asi que tambien cubre el caso de empezar la sesion con el gatillo apretado — y de paso reemplaza al viejo one-shot de `bArmedOnce`, que existia solo por el problema de orden de BeginPlay.

🔴 **Por que se puede confiar en `bTrigHeld` aunque el boton este desarmado:** se verifico leyendo el grafo de `BP_MenuButton` — los eventos de input lo escriben **directo** (`IA_Shoot_*` `Started` → `true`, `Completed` → `false`), sin pasar por `bArmed`. Si pasara por `bArmed`, desarmar dejaria `bTrigHeld` congelado en true y la galeria quedaria **trabada para siempre** despues de la primera apretada. Valia la pena mirarlo antes.

### 🔴🔴 Por que los botones NO se arman en BeginPlay
Sintoma reportado por Beltran: *"puse play, aparezco en el lugar 1, pero no veo los botones"*. Medido en PIE: `bArmed = true` pero **`bHidden = true`**.

La causa esta en `BP_MenuButton`: **su propio `EventBeginPlay` termina con `SetActorHiddenInGame true`** — se esconde a proposito, porque en la obra el boton no existe hasta que la intro lo arma. El `ReArm` del director corria dentro del BeginPlay del director, o sea **antes** del BeginPlay del boton, y el boton se volvia a esconder despues.

✅ La solucion: el armado vive en `Poll`, o sea en el **Tick**, cuando todos los `BeginPlay` ya corrieron. No depende de un `Delay` ni del orden de inicializacion entre actores. (Hoy lo hace `GalRelease`; al principio fue un one-shot con `bArmedOnce`, que quedo absorbido por la maquina de `bWaitRelease`.)
🚩 **La forma general de la trampa:** *cualquier* cosa que el director le haga a otro actor desde su `BeginPlay` puede ser pisada por el `BeginPlay` de ese otro actor. Si el efecto tiene que sobrevivir, va en el primer Tick.

### Por que se poleé el boton en vez de bindear su dispatcher
`Default|AssignOnPressed` existe, pero el nodo **auto-genera un evento custom** cuyo cuerpo no se puede escribir en la misma pasada de `write_graph_dsl`. Leer `bDone` una vez por frame es una comparacion de bool, cuesta nada, y **se auto-recupera**: si algo queda a medias, el siguiente frame lo corrige. `ReArm` pone `bDone = false` y llama `Arm` en los dos botones — hace falta porque **`BP_MenuButton` se desarma solo al dispararse** y si no, anda una sola vez.

### Los botones viajan solos
`GAL_BTN_NEXT` y `GAL_BTN_BACK` estan **emparentados al director** (spawneados con el `parent` de `add_to_scene_from_asset`), a 48 cm adelante, ±24 cm a los lados y 100 cm de alto, con **yaw 180** para que el texto mire al usuario. Al mover el director, los botones y el rotulo van con el. **Cero codigo de posicionamiento.**

✅ **Verificado en PIE que viajan** (2026-09-04, con `StartAt = 3`): pawn en `x = 90.000`, botones en `x = 90.048` con `y = ±24` — se movieron los 90 metros con el director, visibles y armados, y con solo `GAL_3_Ganzfeld` prendido. El test anterior no probaba nada porque la estacion 0 **es** el lugar donde estaba puesto el director.

⚠ **Trampa que costo tres intentos:** con el actor ya emparentado, escribir `relativeLocation` por `set_properties` **aplica X y Z pero NO Y** (se recalcula desde la posicion de mundo). La via que si funciona es **`ActorTools.set_actor_transform` con el transform de MUNDO**: el relativo sale bien solo.

## 🔴 La mecanica de DIBUJO esta apagada en este nivel, a proposito
`ControllerRig_L` y `ControllerRig_R` (`BP_ControllerRig`) viven en `/Game/TestMeshes` desde la jornada del rig de mandos. Comparten el **mismo gatillo** que los botones, asi que cada apretada de NEXT tambien **empezaba un trazo** — y como el pawn se teletransporta 300 m en medio del trazo, la cinta se estiraba de una estacion a la otra y se veia como **un laser azul saliendo por detras del boton**.

✅ Apagada con **`bCanDraw = false`** en las dos instancias. No se borro nada: `bShowHand` sigue en true (las manos se ven) y alcanza con volver a marcar la casilla para recuperar el dibujo.

🚩 **La leccion, que es la misma de siempre:** dos mecanicas que comparten el gatillo **se disparan juntas**. Antes de traer una mecanica a un nivel donde ya hay otra, mirar quien mas escucha ese input.

## Lo que el nivel de la galeria tiene que tener para que los botones anden
`GAL_AudioHub` y `GAL_HapticHub` (instancias de `BP_AudioHub` y `BP_HapticHub`) estan colocadas en `x = -1200, y = 100000`. **No son decorado: sin ellas el boton no hace haptica ni suena, y no avisa** — ver la tabla de requisitos en [`BP_MenuButton.md`](BP_MenuButton.md). Y los dos botones tienen **`Ring.bVisible = false`** porque el aro es el indicador del modo timbre y estos son de gatillo.

## Limitaciones conocidas
- **El rig de botones no rota con el anchor.** Los anchors de la galeria estan todos en yaw 0. Si alguna estacion necesitara otra orientacion, el pawn si rota (usa el transform entero del anchor) pero el offset de los botones esta pensado para yaw 0.
- El rotulo dice **"Text"** en el editor: los nombres se aplican en `GoTo`, o sea recien al dar Play.

## TODO
- [ ] Apretar los botones en visor (es lo unico sin verificar del recorrido).
- [ ] Sumar las estaciones que faltan: el estudio de sombra y los tres de Nico → colocar, anclar y agregar la fila a los tres arrays.
- [ ] Afinar la composicion de cada estacion (es trabajo de autor, de Beltran): distancias, tamanos y paleta.

## 🔴 2026-09-08 — "avanzo con el boton y no llego a la estacion nueva": los TRES arrays tienen que crecer juntos
Beltran taguo los actores nuevos con `GALSTATION` + `GAL_10`, coloco `GAL_10_Anchor`, y aun asi el boton no llegaba. **Nada de lo que hizo estaba mal.** Lo que faltaba estaba en la instancia del director:

| Array | Filas antes |
|---|---|
| `StationTags` | **11** ✅ (la agrego el) |
| `Anchors` | **10** ❌ |
| `Names` | **10** ❌ |

👉 **Sin `Anchors[10]` el director no tiene a donde llevar al pawn**, asi que la estacion existe como tag pero es inalcanzable. Arreglado: los tres arrays quedaron en 11, con la fila 10 = tag `GAL_10` · anchor `GAL_10_Anchor` (`BP_Anchor_C_9`, x = 303.604) · nombre `"11  Ring Tunnel Rect"`.

🚩 **La regla, que este tracker prometia pero no gritaba:** *"agregar una estacion"* son **cuatro** cosas, no tres — tags en los actores, el `BP_Anchor`, **y una fila en CADA UNO de los tres arrays**. Los tres son paralelos por indice; si quedan de largos distintos **no hay error, no hay log, simplemente esa estacion no se puede alcanzar**. Es el modo de fallo mas facil de repetir de este BP.
💡 **Diagnostico de 10 segundos:** `get_properties` de `Anchors`/`StationTags`/`Names` y **contar**. Si los tres no miden lo mismo, ese es el bug — no hay que mirar ni tags ni botones.
- [ ] Candidato de robustez (no hecho, decide Beltran): que `Boot` compare los tres largos y, si no coinciden, imprima *"GALERIA: Anchors/StationTags/Names tienen largos distintos (N/M/K)"*. Convierte un fallo mudo en un mensaje.

⚠ `StartAt` esta en **6** (perilla de debug de Beltran, no se toca). Para caer directo en la estacion nueva, ponerlo en **10**.

## 🗂️ 2026-09-08 — el outliner ordenado por estacion
Pedido de Beltran: *"puedes ordenarme el outliner en carpetas, con lo que va en cada estacion, para poder trabajar mas limpio"*.

**12 carpetas bajo `Galeria`**, con prefijo de dos digitos **igual al numero de tag** (asi `StartAt = 6` corresponde literal a la carpeta `06`):
```
Galeria/00 - Light Shaft        2 actores + anchor
Galeria/01 - Cloud Ocean        6
Galeria/02 - Fog Slab          19
Galeria/03 - Ganzfeld           2
Galeria/04 - Void Field         1
Galeria/05 - Line Field         5
Galeria/06 - Sombra falsa       1
Galeria/07 - Orbe Nico          2
Galeria/08 - Burbujas Nico      6
Galeria/09 - Ring Tunnel        9
Galeria/10 - Ring Tunnel Rect   4
Galeria/_Sistema                director + AudioHub + HapticHub + 2 MenuButton
```
**Como se armo (y por que es re-ejecutable):** el reparto sale del **tag `GAL_<n>`**, que es la misma fuente de verdad que usa el director — no de una lista escrita a mano. Si Beltran duplica un actor y le pone los tags, vuelve a correr y cae solo en su carpeta.
🔴 **Los anchors NO estan tagueados** (a proposito, ver la nota de arriba: taguearlos hace aparecer su marcador). Se repartieron **leyendo el array `Anchors` del director por indice**, que es el mapeo exacto. De paso quedo documentado que **el nombre no es uniforme**: las estaciones 0-6 usan `GAL_ANCHOR_<n>` y las 7-10 `GAL_<n>_Anchor`. Buscar por label habria dejado 7 anchors afuera — y de hecho el primer intento los dejo.

⚠ **Verificacion de seguridad:** los dos scripts corrieron con la plantilla `safe_script.py` (try/except BaseException + canario). **Canario 84 → 84 actores en las dos tandas, cero errores.** Nada se perdio.
💡 Mover carpetas del outliner **no toca transforms ni referencias**: es puramente organizativo y reversible arrastrando.
⚠ El nivel quedo **sin guardar** (lo guarda Beltran).

## 📉 2026-09-08 — PRIMERA MEDICION EN EL VISOR, y el Tick que no se apagaba
Primer APK de la galeria instalado en la Quest 3. Beltran: *"hay varias partes donde dropeó frames"*. Se saco el log del dispositivo y se reconstruyo la curva de fps.

### Como se lee el rendimiento sin OVR Metrics (receta reusable)
El build **Development** escribe el log en el dispositivo, en **almacenamiento privado de la app** (no en `/sdcard/UnrealGame/`, que es donde uno lo busca):
```
/sdcard/Android/data/<PACKAGE>/files/UnrealGame/<Proyecto>/<Proyecto>/Saved/Logs/<Proyecto>.log
```
🔴 **Desde la herramienta Bash de Git, `adb pull /sdcard/...` se rompe**: Git Bash convierte la ruta a `C:/Program Files/Git/sdcard/...`. Va con **`export MSYS_NO_PATHCONV=1`** y **el destino en ruta Windows**.

💡 **El numero entre corchetes de cada linea del log es el contador de frames** — y con eso se saca fps sin ninguna herramienta: `Δframes / Δtiempo` entre dos lineas. 🔴 **Va modulo 1000**: hay que desenrollarlo (si baja de golpe, sumar 1000) o el promedio sale absurdo (dio "8 fps" sobre una sesion que corria a 70).
💡 **Y los `PrintString` sirven de marcadores temporales**: los `BOTON apretado: NEXT` del menu marcan cada cambio de estacion, asi que la curva de fps se puede **cortar por estacion** sin instrumentar nada.

### El resultado (sesion de 65 s, 11 estaciones, `StartAt = 0`)
| # | Estacion | fps |
|---|---|---|
| 0 | Light Shaft (20 haces) | ~62 |
| 1 | Cloud Ocean | ~66 |
| 2 | Fog Slab | ~69 |
| **3** | **Ganzfeld** | **~30** 🔴 |
| 4 | Void Field | ~70 |
| 5 | Line Field | ~59-70 |
| 6 | Sombra falsa | ~72 |
| **7** | **Orbe (Nico)** | **~26** 🔴 |
| **8** | **Burbujas (Nico)** | **~33** 🔴 |
| 9 | Ring Tunnel | ~67 |
| 10 | Ring Tunnel Rect | ~72 |

✅ **El Ganzfeld se midio DOS veces** (Beltran dio la vuelta completa y volvio a pasar): ~30 fps las dos. No es ruido.
⚠ Ademas hay un **paron de ~0,7 s al entrar a una estacion** (2 frames en 0,69 s), junto con `LogRenderer: Forcing update for all mesh draw commands`.

### 🔴 La hipotesis de Beltran, confirmada con numeros
> *"a mi me tinca que los elementos si estan gastando recursos aunque no sean de la estación activa. Porque son tags del actor de mundo."*

**Tenia razon.** `GalHideAll` y `GalShow` solo llamaban **`SetActorHiddenInGame`**, que saca el dibujo pero **NO apaga el Tick**. Medido en el nivel: **101 actores con Tick activo**, entre ellos `BP_LightShaft_SC` ×23, `BP_VoidField_SC` ×11, `BP_RingTunnel_SC` ×11, `BP_FogSlab_SC` ×10, `BP_Ganzfeld_SC` ×3 — todos tickeando siempre, en todas las estaciones. El `StepPulse` que se le agrego al haz ese mismo dia corria en 23 actores invisibles.

**Arreglo (cirugia de 2 nodos, uno por funcion):**
```
GalHideAll: ... (Rendering|SetActorHiddenInGame el true)  (Actor|Tick|SetActorTickEnabled el)        <- false
GalShow   : ... (Rendering|SetActorHiddenInGame el)       (Actor|Tick|SetActorTickEnabled el true)
```
⚠ Solo toca los actores **tagueados `GALSTATION`** — el director, los botones, los rigs y los anchors no se tagean, asi que siguen tickeando.
⚠ `SetActorTickEnabled` apaga el tick **del actor**, no el de sus componentes (Niagara, movimiento). Si algo sigue costando escondido, ese es el siguiente sospechoso.

### 🔴 Pero son DOS causas distintas, no una
El Tick de los escondidos es un **impuesto constante** — identico en las 11 estaciones. Por lo tanto **no explica** que la 3, la 7 y la 8 caigan a 26-33 mientras la 6 y la 10 dan 72. Eso es **coste de la estacion visible** (fill rate). Quedan pendientes por separado:
- **Ganzfeld**: 6 muestras de simplex 4D por pixel sobre un cascaron que llena la pantalla. El doble desde que se le agregaron las olas (el loop paso de `k<3` a `k<6`).
- **Orbe / Burbujas (Nico)**: sin diagnosticar.

### ⚠ Lo que NO se pudo medir, y como evitarlo la proxima
El log de Unreal da fps, **no dice si el cuello es CPU o GPU**. Eso lo da `VrApi` por `adb logcat` (`App=x.xx ms`, `GPU%`, `CPU%`), **pero el buffer de logcat ya habia rotado** cuando se fue a buscar. 👉 Hay que capturarlo **durante** la pasada. Script listo al lado del APK: **`CAPTURAR_RENDIMIENTO.bat`** (hace `logcat -c` y vuelca `VrApi:I` a `perf_quest.log` hasta que se corta con Ctrl+C).
