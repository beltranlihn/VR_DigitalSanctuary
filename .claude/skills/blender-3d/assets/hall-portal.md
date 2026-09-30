# SM_HallShell_SC — el pabellón-portal del Hall de entrada

## Propósito
La arquitectura del **hall de entrada**: un pabellón circular flotando en el vacío negro, con **dos puertas circulares enfrentadas** de vidrio esmerilado y un **óculo** en la cima. Por dentro: hormigón muy fino y cálido, luz tipo Turrell. Por fuera: **negro total**, solo brilla lo iluminado (el portal). Planos de Beltrán en el Escritorio (`Planta/Corte/Elevacionl/Puerta.pdf`, cotas en cm) + refes generadas con ChatGPT (2026-09-29).

## Estado
🟡 **En Unreal, nivel `/Game/SoulCharger/Mechanics/Hall/Test_Hall`, explorando la estética con Beltrán (2026-09-29).** Sin visor, sin commit.

## Assets (`/Game/SoulCharger/Mechanics/Hall/`)
| Asset | Qué |
|---|---|
| `SM_HallShell_SC` | Cáscara + las dos "pieles negras" de las puertas. 66k tris, **sin colisión** (un casco convexo encerraría al pawn). Slots `M_Hall_Interior` / `M_Hall_Exterior` |
| `SM_HallDoorLeaf_R_SC` / `_L_SC` | Hojas de la puerta Este; **pivote en el eje del edificio** → abrir = girar en Z (~16,5°). La puerta Oeste usa las MISMAS mallas giradas 180° |
| `M_/MI_Hall_Interior_SC` | Unlit: **luz horneada de Cycles** (UV2/UV3) × albedo con grano de granito (ruido 3D en el shader, se apaga con la distancia) + manchado. `MFPM_Full_MaterialExpressionOnly`. HLSL: `unreal-vr/scripts/hlsl/HallInteriorPS.hlsl` |
| `M_Hall_Exterior_SC` | Unlit negro |
| `M_/MI_Hall_Glass_SC` | Vidrio esmerilado Quest (la idea guardada): translúcido unlit, **`DepthFade` = lechosidad por distancia** → opacidad y emisión. `GlassColor · GlassGlow · MilkDistance · OpacityMin` |
| `M_Hall_Sky_SC` | Cielo del óculo (disco emisivo encima): `SkyColor · SkyGlow` |
| `Test_Hall` | Nivel: plantilla vacía del motor, GameMode `BP_XRGameMode` (pawn `BP_VRPawn_SC`), PlayerStart adentro mirando a la puerta Este, `BP_LightShaft_SC` como haz del óculo (cilindro, Roll 180, z 325, escala 2,3/2,3/5,9, cálido) |

## Construcción (`blender-3d/scripts/gen_hall_portal.py`, headless, todo analítico y en quads, SIN booleanos)
- Un perfil (r, z) revolucionado (192 columnas): piso → cove 0,25 → muro 7,0 m → cove 1,0 → bóveda esférica rebajada (cima 6,5 m exterior) → labio semicircular del óculo (Ø 2,4) → exterior = interior desplazado 30 cm.
- **Vanos: "círculo dentro de un rectángulo"**: se reemplazan las celdas del muro por anillos del borde del rectángulo al círculo, el redondeo del canto (12 cm interior / 5 cm exterior) y el vano. Proyección horizontal sobre el cilindro → círculo perfecto en elevación. Puerta Ø 3,5, centro z 2,45 (borde a 40 cm del piso interior).
- **Hojas**: media luna curva sobre el cilindro exterior (R 1,85 = 10 cm más que el vano), vidrio 3 cm.
- 🆕 **Piel negra** (idea de Beltrán): una segunda piel negra con el agujero circular por fuera de las hojas → corren EN UN BOLSILLO; desde afuera solo se ve el círculo, cerrado o abierto.
- UV0 por zonas en metros (piso/bóveda polar, muro cilíndrico, vanos), islas sin solapar.

## Luz: horneado en Blender → Unreal unlit (`blender-3d/scripts/bake_export_hall.py` + `render_hall.py`)
- Escena de Cycles: esfera cálida interior (invisible a cámara) + disco-cielo emisivo sobre el óculo. Se hornea **DIFFUSE directo+indirecto** en vértices (4096 muestras) + **suavizado laplaciano 12 pasadas** (sin él: manchas de ruido por vértice).
- Normalización: percentil 80 de lo iluminado = 1 (el exterior queda en 0; el labio del óculo recibe ~30× y pasa de 1 sin recorte).
- 🔴 **Va en UV2 = (R,G) y UV3 = (B,0), no en color de vértice**: el importador de Unreal descartó los colores de vértice (medido: pared uniforme; control `LightScale` 1 vs 0,3 cambió todo el cuadro por igual). UV1 = copia de UV0 (Unreal lo pisa con el lightmap). Unreal invierte la V: G llega como 1−G (el shader lo deshace).

## Pendientes / ideas para explorar
- [ ] Veredicto de Beltrán en el editor y en visor (el preview de PC tiene tonemapper; la Quest no — `r.MobileHDR=False`).
- [ ] Haces que salgan por las puertas hacia afuera (en Blender se ven con bruma; en Unreal falta).
- [ ] Niebla interior (velo `M_FogVeil_SC`) si hace falta más aire.
- [ ] Mecánica de apertura de las puertas (girar hojas en Z) — Blueprint.
- [ ] Optimizar: 66k tris (la cara exterior es negra: podría ser mucho más rala).

## Ronda de estética 2 (2026-09-29, con Beltrán mirando en preview Android)
- **Interior** (`HallInteriorPS` v3 + `HallGroovesPS` v4): hombro suave `Knee` (sin blancos quemados), bruma cálida por distancia (`HazeColor/Density/Amount`, solo en este material: el exterior no la recibe), `LightScale` 0,62 / `LightGamma` 1,3 en la MI.
- **Hendiduras** (grupo "B - Hendiduras"): anillos de alfombra (`CarpetRingR` 290), piso (`FloorRingR` 620), remate en el cove de la bóveda (`TopRingZ` 525: a 440 cruzaba el tope del anillo de la puerta), óculo, puertas (`DoorRingR` 205: sigue la superficie hasta el cove) + 5 meridianos cortados por los anillos de puerta. Todo SDF continuo. Sutil: `GrooveCore` 0,6 / `GrooveGlow` 0,14.
- **Exterior** (`HallExteriorPS` v4): línea de luz alrededor del marco (`RingR` 186, halo 6 cm). 🔴 El halo tiene que CABER en la piel negra (z 40..450): recortarlo por altura se leía como corte recto → alcance máximo = 205 − RingR.
- **Vidrio**: `MilkMax` (tope de lechosidad → se ve el interior desde afuera), color ámbar medio; **desde adentro** (`HallGlassInsidePS`, cámara a < 720 cm del eje) pasa a `InsideColor/InsideGlow/InsideOpacity` → `InsideColor` es el que la narrativa animará al color de la próxima etapa.
- **Haz**: cono abriendo hacia abajo = escala XY 4,0 + `Spread` −21 (el Spread abre el extremo de la FUENTE); hundido 50 cm bajo el piso (la tapa del cilindro en z 30 hacía z-fighting = rayos en estrella); `FloorGlow` apagado.
- **Polvo**: `NS_HallDust_SC` (duplicado de `NS_VoidDust`: caja 9×9×5 m, 40/s, 8-12 s, motas 0,6-1,4 cm, alfa 0,35, viento lento) ×2: todo el hall + uno angosto dentro del haz.
- **Baldosas** `SM_HallTiles_SC` (`scripts/gen_bake_hall_tiles.py`, sobre `SM_HallShell_SC_baked.blend`): 5 sectores de anillo R 1,0-2,5 m, juntas de 22 cm sobre los meridianos, filete 20 cm, asoman 5 mm, canto redondeado 1,5 cm; anillos ANALÍTICOS (mismo contorno desplazado → quads). Luz COPIADA del piso horneado de abajo (KDTree). Material `M_Hall_Tile_SC` = el mismo hormigón del muro teñido (`Tint` 0,45) + `MI_Hall_Tile_<Etapa>_SC`. La junta oscura la dibuja el piso (`HallGroovesPS`, constantes compartidas). Entering en 180° (la más cercana a la entrada Oeste), el resto antihorario visto desde arriba.
- **Baldosas v3 (2026-09-30, encargo de Narrativa + medidas de la sesión Hall)**: las baldosas SUBEN hasta 3 cm para anunciar su etapa (WPO `Lift` del material, un slot = una baldosa; `Glow` en su color). Beltrán: *"al subir no deben verse cantos rectos"*.
  - **Bisel redondo de 3,5 cm** (= `TILE_UP` 0,5 + `Lift` 3) en 7 tramos.
  - Faldón `TILE_T` 0,035 → **0,070**: el fondo queda a −6,5 cm y al subir 3 cm sigue hundido.
  - `TOP_RINGS` (0,07, 0,14, 0,24, 0,36).
  - Sin cambios: contorno `TILE_*`, slots y su orden, origen, luz copiada del piso.
  - 10.740 tris; sin tangentes degeneradas. **Importada en sitio el 2026-09-30**: bounds z 23,5..30,5 cm, XY igual, 5 MI en su orden, `StaticMeshActor_7` repuntado, `Test_Hall` guardado.
  - ⚠ En reposo el canto corta el piso **1,7 cm adentro** del contorno (v2: 0,4). Con Lift 1 cm corta a 0,6; con 2 cm, a 0,15; con 3 cm, justo en el contorno. La sesión Hall corre el arranque de la junta de `HallGroovesPS` a −1,7 cm.
  - El perfil elíptico más empinado se descartó: "la pared es justo lo que Beltrán no quiere ver".
  - Control: `scripts/render_hall_tiles_check.py`, con el canto en reposo y subido y la comparación v2/v3 en `Saved/ClaudeScripts/Hall/check_tiles_zoom.png`. v2 respaldada en `SM_HallTiles_SC_v2bevel15.fbx/.blend`.
  - Ángulos en el espacio LOCAL de Unreal: Entering 180°, Recognizing 108°, Loving 36°, Attracting 324°, Surrounding 252°, centro a r 175 cm. Los números de `STAGES` YA son de Unreal; el script arma cada baldosa en Blender a −a.
- **Junta v5** (`HallGroovesPS`): distancia EXACTA a la baldosa = dist(sector de esquinas vivas encogido 20 cm) − 20. La intersección redondeada de dos SDF (v4) solo es exacta a 90° y la junta se afinaba y desaparecía en las esquinas. Más clara (0,45) y pareja (−0,4 a 1,4 cm: el canto corta el piso 4 mm adentro). Baldosas más rugosas: `GrainAmount` 0,2 / `GrainScale` 0,5 / `MottleAmount` 0,6 / `MottleScale` 35.

## Ronda 3 (2026-09-29): encendido + cielo
- **Cielo del óculo**: `StaticMeshActor_6` pasó de cilindro a **plano de una cara mirando hacia ABAJO** (Plane, Roll 180, escala 3,2, z 655; `M_Hall_Sky_SC` no es two-sided) → desde afuera/arriba no se ve.
- **Encendido**: `BP_HallLights_SC` + `MPC_Hall_SC` (`HallLight`, `FrameLight`, `DoorColor`) — ver `unreal-vr/blueprints/BP_HallLights_SC.md`. Todos los materiales del hall multiplican por la MPC; el polvo tiene su material propio `M_HallDust_SC` (sprite aditivo, disco suave × color × alfa × HallLight).

## Ronda 4 (2026-09-30, noche): baldosas biseladas + director
- **Baldosas v3** (Mesh 3D): bisel redondo 3,5 cm × 7, faldón a −6,5 cm, 10.740 tris; mismos slots/contorno/luz. Para que al subir 3 cm no se vea canto recto.
- **`HallGroovesPS` v6**: la junta arranca en −1,7 cm (el bisel corta el piso 1,7 cm adentro del contorno en reposo).
- **`M_Hall_Tile_SC`**: + `Lift` (WPO en Z, cm) y + `TileGlow` (`TileColor × TileGlow` sumado DESPUÉS del `× HallLight`); defaults 0 = el look de antes. Los anima `BP_HallDirector_SC` por MID de slot.
- Hojas de puerta `Movable` + tag `hall_leaf`; baldosas tag `hall_tiles` (así las encuentra el director también dentro de la Obra).

## Log
- **2026-09-29** — modelado headless, render Cycles (5 vistas), piel negra por pedido de Beltrán, horneado de luz, import, materiales, nivel Test_Hall con haz y cielo del óculo.
