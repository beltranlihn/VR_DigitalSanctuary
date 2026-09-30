# El HUD como objeto 3D, en piezas: `SM_HUDRim_SC` · `SM_HUDBezel_SC` · `SM_HUDCup_SC` (×2) · `SM_HUDGlass_SC` · `SM_HUDPulse_SC`

**Encargo de Narrativa, aprobado por Beltrán (2026-09-30).** El HUD deja de ser el cuadro translúcido de 77 × 43 cm y pasa a ser **una píldora horizontal** con tres cosas:
- a la izquierda, la ameba que late;
- al centro, el gráfico EEG;
- a la derecha, el anillo `SM_ChargeRing_SC` con el alma adentro.

Formato aprobado: marco, base translúcida y un segundo marco para el EEG.

Estado: 🟡 v4 · 🟢 **en Unreal (2026-09-30, pedido de Beltrán para probar ubicación y tamaño en el Hall)**:
- `/Game/SoulCharger/Mechanics/HUD/` con las mallas sin colisión, las MI `MI_HUD_Rim/Frame_SC` (sobre `M_SCObjectTrans_SC`, translúcidas, Opacity 0,45), `MI_HUD_Seat_SC` (opaca) y `MI_HUD_Glass_SC` (sobre `M_SCGlass_SC`, Opacity 0,30);
- `BP_HUDArt_SC`: Rim/Bezel/Glass en el origen; Nest y RingDock en (+10,11, 0, 0); Seat y SisterDock en (−10,11, 0, 0); EEGWindow en el origen con pitch 90 (su +X = la cara, hacia el usuario). Cara del HUD = +Z del actor.
- Lo coloca Narrativa. ⚠ El anillo tiene que ir a escala ≈ 0,098 (45 mm): con 0,115 mide 52,9 mm y no entra en la abertura de 47 mm.
- ⬜ Visor · 🟢 GLB actualizado en `web/prototipo-narrativo/modelos/SM_HUD_SC.glb`.

## 🔴 Cambio de diseño (2026-09-30, Beltrán vía Narrativa): el pulso NO es la ameba rosada
- El pulso del latido es una **HERMANA del alma del usuario**: la **misma malla y el mismo material** que la ameba de `BP_ProtoSoul_SC`.
- Mide **~30 mm**, más grande que la del anillo, y late a la mitad del ritmo en el asiento izquierdo.
- **Se ancla cuando el alma llega al HUD por primera vez.** Ya está en la web (v37).
- **`SM_HUDPulse_SC` queda SIN USO.** No se importa; queda en el `.blend` y los FBX solo como referencia.
- El asiento no cambia (abertura r 23,5 mm). A 1,2× la ameba de 30 mm llega a r 18, así que quedan **5,5 mm de aire**.

## Vueltas de Beltrán
- **v1**: píldora de 12 mm de espesor, marco de una sola pieza y opaco.
- **v2**: *"muy grueso, debe ser mucho más plano"* → **5 mm** (z −2,5 a +2,5); la ameba también más chata (0,36 → 0,20).
- **v3**: *"el borde también debe ser un poco translúcido; piénsalo en piezas para poder animar su transformación de entrada"*.
  - Se separó en piezas, cada una con su origen.
  - Borde translúcido. Por eso **nada puede quedar escondido adentro de él**: la lámina llega justo a su pared interna y el collar de cada nido termina a 0,2 mm del borde, concéntrico.
- **v4**: *"el borde y contornos más delgados incluso, y que tenga transparencia"*.
  - Borde de 3 a **1,8 mm**, marco del EEG de 3 a **1,6**, collares de 2,3 a **1,4**.
  - Todos translúcidos (opacidad 0,45 en la vista previa); los fondos de los nidos siguen opacos.
  - Como los contornos son translúcidos, la lámina ya no se mete debajo de ellos: llega a su pared.

## Medidas (mm)
| | Valor | Nota |
|---|---|---|
| Píldora | **256 × 54,8 × 5** | Extremos semicirculares r 26,9 |
| Borde | 1,8 de ancho, z ±2,5, canto delantero r 0,8 | Translúcido |
| Ventana del EEG | **120 × 30 exacta (4:1)**, esquinas r 1,5, centrada | Marco de 1,6 de ancho, z ±1,5, translúcido. Abertura **vacía**: ahí va el widget (`GraphArea` 4:1) |
| Nido del anillo / asiento de la ameba | centros en **(±101,1, 0)**; abertura r 23,5 | Anillo de 45 mm + 1 de aire / ameba de 35 que late a 1,2× + 2,5 de aire. Collar de 1,4 translúcido + fondo opaco en z −2 |
| Lámina | una cara hacia +Z en z −1,2 | El interior del borde con 3 agujeros: la ventana y los dos nidos |
| Ameba | 36,7 × 35,5 × 7,2 | En el asiento, en **(−101,1, 0, 1,9)** |

## Piezas (salida en `VR_Test/Saved/ClaudeScripts/HUD/`: FBX + `SM_HUD_SC.blend` armado)
| Malla | Tris | Slots | Origen / dónde va |
|---|---|---|---|
| `SM_HUDRim_SC` | 1.188 | `Rim` (translúcido) | centro de la píldora |
| `SM_HUDBezel_SC` | 720 | `Frame` (translúcido) | centro |
| `SM_HUDCup_SC` | 684 | `Frame` (collar, translúcido) · `Seat` (fondo, opaco) | **su centro**; va dos veces, en (+101,1, 0, 0) nido del anillo y en (−101,1, 0, 0) asiento de la ameba |
| `SM_HUDGlass_SC` | 198 | `Glass` | centro |
| ~~`SM_HUDPulse_SC`~~ | 1.280 | `Pulse` | **sin uso** desde el cambio de diseño: el pulso es la ameba del alma (`BP_ProtoSoul_SC`) a ~30 mm, en el asiento (−101,1, 0) |
| `SM_HUD_Trace_SC` | — | trazo de luz de la entrada (`M_AppearTrace_SC`, ver `aparicion-luz.md`) | centro |

- **Ejes**: acostada en XY con la **cara hacia +Z**, igual que el timbre y el SAVE; X a lo largo (ameba en −X, anillo en +X). ⚠ Unreal espeja la Y (simétrica: no cambia nada).
- **El anillo en el nido**: `SM_ChargeRing_SC` tiene el eje en X, así que va girado −90° en Y y −90° en Z, escalado a 45 mm de diámetro y centrado en el nido.
- Quest: son 4 superficies translúcidas (borde, marco, collares, lámina), pero delgadas; la lámina es la única de área grande. Opacos: fondos, ameba y anillo.

## La entrada por piezas (`scripts/anim_hud.py`, familia "luz primero"; t de 0 a 1 = 1,5 s; salida = reversa)
| t | Pieza | Qué hace |
|---|---|---|
| 0,00–0,30 | trazo | la luz dibuja el contorno de la píldora |
| 0,24–0,56 | borde | rendija de canto → párpado, se enfría (`Flash` 1,2 → 0) |
| 0,40–0,62 | marco del EEG | se abre a lo largo desde el centro, con destello |
| 0,48–0,74 | lámina | se extiende desde el centro hacia los extremos (escala X) |
| 0,50–0,78 | nidos | salen de las puntas del marco del EEG (escala 0,25) y viajan a su lugar con clac |
| 0,62–0,90 | anillo + alma | el anillo se da vuelta de canto a frente en su nido y sus cavidades se llenan; el alma crece adentro |
| 0,66–0,88 | EEG | la línea se enciende (el widget: opacidad) |
| 0,72–1,00 | ameba | cae en su asiento (+12 mm → 0, clac), crece de 0,3 a 1 y late una vez al final |

## Scripts
- `scripts/gen_hud.py`: genera las piezas (medidas arriba del script), los FBX y el `.blend` armado.
- `scripts/render_hud.py`: vista previa con el sombreado falso de la familia y los contornos translúcidos. Incluye el anillo con un alma celeste y un EEG **de muestra** (el real es el widget).
- `scripts/anim_hud.py`: la entrada; además exporta `SM_HUD_Trace_SC`.
- GLB: `export_glb_web.py` → `web/prototipo-narrativo/modelos/SM_HUD_SC.glb` (+ `.json`).

## Curvatura (2026-09-30, pedido de Beltrán: "como los widgets de instrucciones", con una perilla)
- **`/Game/SoulCharger/Mechanics/HUD/MPC_HUD_SC.CurveR`**: radio en cm **locales** del actor del HUD, **con signo** (v2, Beltrán: "para el otro lado"):
  - |R| < 1 = plano;
  - R > 0 = extremos hacia +Z (el usuario);
  - R < 0 = extremos hacia −Z, que es lo que eligió Beltrán (el BP escribe −30).
  - En el mundo, el radio es `CurveR × HudScale`.
- WPO `HUDBendVS` (`unreal-vr/scripts/hlsl/HUDBendVS.hlsl`), en `M_SCObjectTrans_SC` y `M_SCGlass_SC`:
  - toma el vértice relativo a `ActorPositionWS` y lo pasa a local;
  - dobla exacto alrededor del Y local (θ = x/R, x' = R·sinθ, z' = R·(1 − cosθ)), con los extremos hacia +Z (el usuario);
  - devuelve el offset a mundo.
  - Los nidos (Cup a ±10,11) se doblan con la misma curva, porque la cuenta usa la posición del actor.
- Los fondos de los nidos pasaron a `MI_HUD_SeatOpaque_SC` (sobre `M_SCObjectTrans_SC`, Opacity 1) para no tocar `M_SCObject_SC`, que comparten timbre, SAVE y sensor.
- Verificado con la miniatura de `SM_HUDRim_SC` (CurveR 30 contra 0). Las normales no se doblan.
- El BP de Narrativa (`BP_SoulHUD3D_SC`) escribe CurveR, pone BoundsScale 2 y ubica anillo y hermana sobre la curva.

### v3 del doblez + por delante de todo (2026-09-30)
- **Bug de Beltrán en el visor**: al girar la cabeza la píldora se enrollaba "como un tubo" y se separaba del anillo.
  - La v1-v2 armaba la posición con `WorldPosition − ActorPositionWS`. `ActorPositionWS` no tiene versión del cuadro previo y puede llegar desfasado respecto de la transformada del primitivo, que es hijo de un ChildActor pegado a la cabeza.
  - **v3**: posición = `LocalPosition` (sin offsets) + (`PieceOffX`, 0, 0).
  - `PieceOffX` es un ScalarParameter con **Use Custom Primitive Data** (índice 0). En `BP_HUDArt_SC` vale +10,11 en Nest y −10,11 en Seat (`CustomPrimitiveData.Data[0]`).
  - Ya no depende del actor ni del cuadro previo.
- **Por delante de todo**, como el HUD viejo:
  - `bDisableDepthTest` en `M_SCObjectTrans_SC` y `M_SCGlass_SC`.
  - `TranslucencySortPriority`: Glass 200, Nest/Seat 201, Bezel 202, Rim 203; anillo 204, amebas 205 y gráfico 206 (los pone Narrativa).
- **Anillo en el HUD**: `M_ChargeRing_FrameHUD_SC` / `M_ChargeRing_LightHUD_SC` (duplicados, translúcidos, Opacity 1, sin depth test) + `MI_ChargeRing_FrameHUD_SC` / `MI_ChargeRing_LightHUD_SC`.
  - ⚠ Sin depth test el anillo no se ocluye a sí mismo. Si se ve raro, la salida es un pre-paso de profundidad o dejarlo opaco por delante.
- Dato: el nodo "Custom Primitive Data" **no es una clase** de expresión en 5.8: es un `ScalarParameter` con `bUseCustomPrimitiveData` + `PrimitiveDataIndex`.

## La entrada en Unreal (2026-09-30, pedido de Beltrán para verla en el visor)
- **`BP_HUDArt_SC`** tiene el componente **`Appear`** (`BPC_AppearLuz_SC`: FaceAxis (0,0,1), PivotDepth 0).
  - El borde lleva el tag `AppearBody` (rendija → párpado → enfriado con `Flash`).
  - El componente nuevo **`Trace`** (`SM_HUD_Trace_SC`, tag `AppearTrace`, sort 207) usa **`M_AppearTraceHUD_SC`**, una variante del trazo sin depth test y con el doblez del HUD.
- **`PoseHUD(T)`** posa marco del EEG, lámina y nidos con los tiempos de `anim_hud.py`, leyendo `Appear.AppearT` en el Tick; solo pinta cuando el reloj cambia.
  - Los nidos actualizan su `CustomPrimitiveData[0]` con su x mientras viajan, así el doblez los sigue.
  - Todo es relativo al reposo capturado en BeginPlay (`RestBezel/Glass/Nest/Seat`).
- **Espera**: `AppearOnPlay` + `AppearDelay` (3 s). Desde el 2026-09-30 `AppearOnPlay` es **false por defecto** (regla 3 de la noche: nada arranca en BeginPlay en la Obra). La plantilla del `Art` de `BP_SoulHUD3D_SC` (Narrativa) lo pisa con true + 3 s: verificado antes y después del cambio, no se movió. En BeginPlay: `Appear.Prepare()` (captura, AppearT 0, todo oculto) → a los N s, `Appear`.
- **API** para el BP de Narrativa: eventos `HUDHideNow` · `HUDAppear` · `HUDVanish`; reloj `Appear.AppearT`; dispatchers `Appear.OnAppeared/OnVanished`.
- Solo escribe `Flash` (borde, marco, collares) y `Sweep/Head/Glow` (trazo). **Nunca `Opacity`**, que es de Narrativa.
- Verificado en PIE: espera, entrada completa, reposo exacto, trazo apagado. Poses intermedias iguales a Blender (t 0,62: lámina 0,61, nido x 9,98, escala 0,86).
- 🔴 El ChildActor de `BP_SoulHUD3D_SC` **se recrea en runtime** (≥3 s después de empezar) y el nuevo sale de la PLANTILLA, donde las variables nuevas nacieron en false/0. Por eso la recomendación es que el BP de Narrativa mande: `HUDHideNow` en BeginPlay y `HUDAppear` después de su perilla.
