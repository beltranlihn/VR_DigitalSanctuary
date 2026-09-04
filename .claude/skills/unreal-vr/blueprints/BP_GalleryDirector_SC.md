# BP_GalleryDirector_SC — el recorrido de la galeria de efectos (Gallery/)

> Creado 2026-09-04, pedido de Beltran: *"Puedes armar el sistema ordenado en el world, donde yo pueda ir avanzando entre los distintos efectos? Ahora se me hace dificil porque estan todas las cosas puestas en cualquier parte."*
> **Estado: 🟢 arranque verificado en PIE.** Medido con la galeria en la estacion 0: el pawn en su anchor, `GAL_0_LightShaft` VISIBLE y los otros nueve actores (incluidos los 4 cubos de la niebla) OCULTOS. ⬜ Falta apretar los botones — eso necesita manos, o sea visor / PIE con mandos.

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

🔴 **Los efectos 0, 1 y 2 son instancias NUEVAS, no las de la composicion de Beltran** — las suyas quedaron intactas donde estaban. Y como una instancia nueva nace con los **defaults del CDO**, se le copiaron los valores autorados de las suyas (el haz salia azul y chiquito, y el oceano invisible porque el suyo esta en **escala 65**). Es la misma leccion de siempre: **lo de la instancia le gana al Blueprint**.

💡 **La niebla necesita algo detras o no se lee.** Sin los cubos era una pared blanca lisa. Con ellos se ve lo que hace: el cercano nitido, el segundo lechoso, los lejanos comidos. Para eso se creo `M_GalleryProp_SC` (unlit emisivo, `PropColor` + `Brightness`), porque en esta obra **no hay luces** y un cubo con material de fabrica sale negro.

## Como funciona — 🔴 POR TAGS, para no reprogramar nada
Pedido explicito de Beltran: *"hazlo con tags para cada etapa, asi yo puedo agregar o duplicar elementos para armar cada espacio y no tenemos que volver a programar cada una"*.

**Cada actor de una estacion lleva dos tags de actor: `GALSTATION` y `GAL_<n>`.** Eso es todo lo que hace falta para que pertenezca a esa estacion — una estacion puede tener **un actor o veinte**, y sumar uno es duplicarlo y ponerle los dos tags. No se toca ni el Blueprint ni ningun array de actores.

Tres arrays instance-editable en `GAL_DIRECTOR` (categoria *A - Galeria*), en el mismo orden: **`Anchors`** (el punto de vista de cada estacion), **`StationTags`** (`GAL_0` … `GAL_5`) y **`Names`** (el rotulo). El cuarto array, `Stations`, **se llena solo en `BeginPlay`** con todo lo tagueado `GALSTATION` — no se autora.

**Agregar una estacion:** colocar sus actores con los tags `GALSTATION` + `GAL_6`, colocar un `BP_Anchor`, y sumar una fila a `Anchors` / `StationTags` / `Names`.

⚠ **Un actor sin el tag `GALSTATION` no se apaga nunca** — es la unica forma de que algo quede visible en todas las estaciones (util para un piso comun, si alguna vez hace falta).

- **`BeginPlay`** → `IsValid(BtnNext)` → **`Boot`** (marca listo, **`GalCollect`** recoge por tag todos los actores de estacion, y llama `GoTo(0)`). Si los botones no estan asignados, imprime *"GALERIA: los botones no estan asignados en la instancia"* en vez de fallar en silencio.
- **`GoTo(Idx)`** — guarda el indice, **`GalHideAll`** esconde TODO lo tagueado `GALSTATION`, **`GalShow(Idx)`** prende todo lo que tenga el tag de esa estacion, y mueve **al director Y al pawn** al transform del anchor (`bTeleport = true`). Despues pone el nombre en el rotulo y llama `ReArm`.
- **`GalStep(Dir)`** — suma y **envuelve con modulo**, asi la ultima vuelve a la primera.
- **`Tick`** → `Poll`: mira el `bDone` de cada boton. **No usa el dispatcher `OnPressed`.**

### Por que se poleé el boton en vez de bindear su dispatcher
`Default|AssignOnPressed` existe, pero el nodo **auto-genera un evento custom** cuyo cuerpo no se puede escribir en la misma pasada de `write_graph_dsl`. Leer `bDone` una vez por frame es una comparacion de bool, cuesta nada, y **se auto-recupera**: si algo queda a medias, el siguiente frame lo corrige. `ReArm` pone `bDone = false` y llama `Arm` en los dos botones — hace falta porque **`BP_MenuButton` se desarma solo al dispararse** y si no, anda una sola vez.

### Los botones viajan solos
`GAL_BTN_NEXT` y `GAL_BTN_BACK` estan **emparentados al director** (spawneados con el `parent` de `add_to_scene_from_asset`), a 48 cm adelante, ±24 cm a los lados y 100 cm de alto, con **yaw 180** para que el texto mire al usuario. Al mover el director, los botones y el rotulo van con el. **Cero codigo de posicionamiento.**

⚠ **Trampa que costo tres intentos:** con el actor ya emparentado, escribir `relativeLocation` por `set_properties` **aplica X y Z pero NO Y** (se recalcula desde la posicion de mundo). La via que si funciona es **`ActorTools.set_actor_transform` con el transform de MUNDO**: el relativo sale bien solo.

## Limitaciones conocidas
- **El rig de botones no rota con el anchor.** Los anchors de la galeria estan todos en yaw 0. Si alguna estacion necesitara otra orientacion, el pawn si rota (usa el transform entero del anchor) pero el offset de los botones esta pensado para yaw 0.
- El rotulo dice **"Text"** en el editor: los nombres se aplican en `GoTo`, o sea recien al dar Play.

## TODO
- [ ] Apretar los botones en visor (es lo unico sin verificar del recorrido).
- [ ] Sumar las estaciones que faltan: el estudio de sombra y los tres de Nico → colocar, anclar y agregar la fila a los tres arrays.
- [ ] Afinar la composicion de cada estacion (es trabajo de autor, de Beltran): distancias, tamanos y paleta.
