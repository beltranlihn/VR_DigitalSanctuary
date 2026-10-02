# BP_SoulHUD3D_SC — el HUD como objeto 3D (prueba de ubicación, 2026-09-30)

`/Game/SoulCharger/Shared/HUD/` · **hijo de [BP_SoulHUD_SC](BP_SoulHUD_SC.md)**: hereda el pegado a la cabeza (offset horneado contra `BP_FaceAnchor_SC` en el Construction Script), el widget del EEG en vivo (`WBP_SoulHUD_SC`, datos del `BP_BioHub`) y el nacimiento. Armado por Narrativa para que Beltrán pruebe **ubicación y tamaño** en el visor. La construcción completa (cargas, teletransporte, halo, borde que se enciende) es de la sesión "HUD y cargas".

## Dónde está colocado
`Test_Hall` (Mechanics/Hall): `SoulHUD3D_Test` + `FaceAnchor_HUDTest` (−390, 0, 122) + `BioHub_HUDTest` (`bFakeSignal` = true).
Pose = la del HUD del nivel completo `L_SoulCharger_V3`: offset contra el anchor **(40,65 · −10 · 0,95) cm, pitch −20**. Se autora moviendo el actor en el world, como el HUD original.

## Componentes (además de los heredados `HeadRef` y `Hud`)
| Componente | Qué es |
|---|---|
| `Art` (ChildActor → `BP_HUDArt_SC`, de Mesh 3D) | la píldora v4 (Rim, Bezel, Cup ×2, Glass). Rot (0, 90, **+90**): la cara +Z de la píldora mira al usuario (con −90 miraba hacia atrás: la lámina, de una sola cara, casi no se veía y la curva salía al revés; se detectó midiendo distancias al ojo). Ubicada para que la ventana del EEG rodee al gráfico del widget |
| `Ring` (hijo de `Art`) | `SM_ChargeRing_SC` en el nido (+10,11, 0, 0,05), pitch 90, escala 0,098 (Ø 45 mm) |
| `RingSoul` (ChildActor → `BP_HUDRingSoul_SC`, hijo de `Art`) | el alma dentro del anillo, 1,5 cm, sin latido |
| `Sister` (ChildActor → `BP_HUDSister_SC`, hijo de `Art`) | la HERMANA en el asiento (−10,11, 0, 0,19): 3 cm, late a la mitad del ritmo (u²·e^(2(1−u)), +20 %) |
| `Soul` | ⚠ sin uso (oculto): una malla con el material del alma, colgada del HUD, flotaba lejos (ver trampa 1) |

## Variables y funciones propias
- **`HudScale`** (instance-editable, 1): la perilla de escala. `ApplyHudScale` (llamada en el Construction Script después del padre) escala `Art` (píldora, anillo y amebas) y el widget `Hud` (0,0365 × S) y corre `Art` a (−0,2 · −0,29 · −13,65) × S para que el gráfico siga dentro de la ventana.
- **`HudCurve`** (instance-editable, cm LOCALES; 0 = plano; CON SIGNO: + = extremos hacia el usuario, − = alejándose; |R| < 1 = plano; en la prueba quedó en +30): la perilla de curvatura. `ApplyHudCurve` (Construction Script, después de `ApplyHudScale`) escribe `MPC_HUD_SC.CurveR` (el doblez por WPO lo hacen los materiales de Mesh 3D, alrededor del Y local del `BP_HUDArt_SC`, extremos hacia el usuario; radio en el mundo = CurveR × HudScale) y lleva el anillo, el alma y la hermana a la misma curva: x = ±R·sin(10,11/R), z = base + R·(1 − cos(10,11/R)); el anillo gira 10,11/R rad para mirar al centro. `BoundsScale` 2 en las mallas de `BP_HUDArt_SC` para que el culling no corte los extremos doblados.
- **`HideOldHud`** (después del `Parent:Tick`): colapsa `Bg`, `Bar`, `Dot`, `Dot_1` y esconde el contorno de `GraphArea` del widget viejo. El trazo del EEG se sigue dibujando (lo pinta el `OnPaint`).
- Defaults: `PulseMin`/`PulseKick` = 0 (el punto viejo no se ve), `bBirthOnStart` = true (el EEG nace solo a los 3 s).
- Materiales de las amebas: `MI_HUDSister_SC` (FloatScale 0,1) y `MI_HUDRingSoul_SC` (0,05), sobre `M_ProtoSoul_HUD`, con **los valores de la ameba 0 del nivel completo** (`L_SoulCharger_V3`, `BP_ProtoSoul_SC_C_0`). Los 5 juegos de valores están en `VR_Test/Saved/ClaudeScripts/protosoul_v3_values.json` (solo cambian CoreColor, GradColorA/B y EdgeColor).

- `ApplyHudCurve` también corre en `BeginPlay`: en un build cocinado el Construction Script de un actor colocado no vuelve a correr y el MPC quedaría en 0 (plano).

## 🔴 Trampas de esta prueba
1. **`M_ProtoSoul` mueve los vértices respecto de la POSICIÓN DEL ACTOR** (flotación/rotación por WPO). Una malla con ese material colgada de otro actor (el HUD) flota respecto del centro del HUD y se va lejos. ✅ Cada ameba es **su propio actor** (ChildActor) con la malla como raíz, y el `FloatScale` baja con el tamaño (0,03 → 0,1).
2. Un script que falla hace Undo y se lleva los cambios anteriores del mismo script: los defaults de `BP_HUDSister_SC` quedaron en 0 (tamaño 0 = hermana invisible). Se repusieron.
3. Agregar un componente a un BP con instancia colocada → la instancia queda con defaults del motor (`childActorClass` None, `HudScale` 0). Se borró y se recolocó la instancia.
4. En `WBP_SoulHUD_SC` el gráfico real está en `GraphArea` (792, 884) 320×60, no donde decía el tracker viejo: el widget se rediseñó.

## Cambio en el widget compartido (`WBP_SoulHUD_SC.ApplyBox`)
Pedido de Beltrán: *"un gráfico EEG siempre nace desde la derecha y hacia la izquierda"*. El marco nacía desde el centro (`BoxPos.x + 0,5·(ancho − ancho·Birth01)`); el literal pasó a **1,0**, así que el borde derecho queda fijo y el trazo crece hacia la izquierda. Vale para todos los niveles que usan el widget.

## Pendiente
- ⬜ Visor: ubicación, tamaño y legibilidad (Beltrán).
- ✅ Curvatura con perilla (`HudCurve`). ⚠ El widget del EEG sigue plano (12 cm: la flecha de la curva ahí es chica). ⚠ En el viewport del editor se ven la barra y el fondo viejos del widget: `HideOldHud` corre en el Tick, o sea solo en Play.
- ⬜ Cargas, teletransporte, halo y borde que se enciende → sesión "HUD y cargas".

## 2026-09-30 (tarde, después del cierre de Unreal)
- **Perillas de opacidad** `FrameOpacity` (0,45) y `GlassOpacity` (0,30), instance-editable. `ApplyHudOpacity` (Construction Script + BeginPlay): castea el ChildActor a `BP_HUDArt_SC` y escribe `Opacity` en Rim/Bezel/Glass con `SetScalarParameterValueOnMaterials`, y en Nest/Seat con un MID por slot (0 = marco, 1 = fondo). 🔴 En el DSL, `Rendering|Material|SetScalarParameterValue` elige la versión de **MPC**: el set sobre el MID se creó por nodo con `declaring_class` `/Script/Engine.MaterialInstanceDynamic`.
- **Los nidos no se doblaban** ("los anillos que envuelven al anillo y la ameba quedan más atrás"): el `CustomPrimitiveData` del template de `BP_HUDArt_SC` no llega a los componentes del ChildActor (vivos: `data []`). ✅ `BP_HUDArt_SC` tiene un Construction Script con `SetCustomPrimitiveDataFloat(Nest, 0, 10,11)` y `(Seat, 0, −10,11)`. Visto en PIE: los círculos abrazan al anillo y a la hermana.
- **Fondos de los círculos transparentes como el cuerpo**: el slot `M_HUD_Seat` de `SM_HUDCup_SC` usa `MI_HUD_Glass_SC`.
- **Adiós al HUD viejo**: `Bg`, `Bar`, `Dot`, `Dot_1` quedaron `Collapsed` en el diseñador de `WBP_SoulHUD_SC` (ya no se ven ni en el editor).
- Materiales del anillo por delante de todo: `ApplyHudMats` (Construction Script) pone `MI_ChargeRing_FrameHUD_SC` / `MI_ChargeRing_LightHUD_SC` en los slots 0/1 (el set por propiedad en la instancia solo tomaba el primero).
- ⚠ En PIE aparece un segundo `BP_HUDArt_SC_C_0` en el mismo lugar que el del ChildActor (en el editor hay uno solo). Pendiente de investigar: dibuja el marco dos veces.
- ✅ La **entrada** del HUD (coreografía de `anim_hud.py`) la armó Mesh 3D en `BP_HUDArt_SC` (`Appear` = `BPC_AppearLuz_SC`, `AppearOnPlay`, `AppearDelay`, eventos `HUDHideNow` / `HUDAppear` / `HUDVanish`). En el template del componente `Art` quedaron `AppearOnPlay` = true y `AppearDelay` = 3.
- **`SyncEntrance`** (en el Tick, después de `HideOldHud`): lee `Appear.AppearT` del ChildActor y enciende lo que no es de Mesh 3D en su momento: `Ring` desde t ≥ 0,62, `RingSoul` desde 0,62 y `Sister` desde 0,72. Visto en PIE: oculto los primeros 3 s, entrada de 1,5 s.
- 🔴 **El widget `Hud` ya NO se esconde** (2026-09-30): escondido desde el arranque, el `WidgetComponent` no volvía a dibujar el EEG nunca (gotchas §513; Beltrán: *"ya no aparece el gráfico"*). Ahora el EEG entra con su propio nacimiento: `BirthDelay` = 4 s en este hijo (la píldora está al 66 % de su entrada) y el marco crece desde la derecha en 2,5 s.
- La **carga** (teletransporte del anillo al frente y vuelta) se prueba con [BP_ChargeTest_SC](BP_ChargeTest_SC.md), que maneja `Ring` y `RingSoul` de este HUD desde afuera.

## 2026-09-30 noche (Mesh 3D) — la hermana no se veía en la Obra
- 🔴 **El template del ChildActor `Sister` en el BP tenía `SizeCm` 0, `BPM` 0, `Amp` 0** (el CDO de `BP_HUDSister_SC` dice 3 / 72 / 0,2) → escala 0 = hermana invisible en TODOS los niveles con este HUD. Es la trampa 2 de arriba, que volvió. Medido en PIE de la Obra: `Sister.Body` escala (0,0,0) con `AppearT` 1.
- ✅ Template corregido a 3 / 72 / 0,2 (la instancia de la Obra usa el template del BP). Obra re-construida y guardada: en PIE la hermana late a 3 cm. ⚠ **El BP quedó SIN GUARDAR**: ya estaba dirty con cambios de otra sesión antes del arreglo.
- EEG en la Obra (PIE, 8 s después del nacimiento): `Hud` visible, `Birth01` 1, `bBioFound` true, 48 puntos dentro del marco, `LineColor` α 0,64 → los datos están vivos; no se pudo ver la línea en captura (la del editor sale a 1280 px para dos monitores). `GraphArea` en Hidden es de `HideOldHud` (a propósito). Nada en la Obra esconde el HUD al arrancar (solo `FinalStart`).

## 2026-10-01 — el EEG fluido, nítido y más visible (Mesh 3D, pedido de Beltrán: "se ve gris, pixelado y más lento")
- Lento: el widget se repintaba a 20 Hz (`Hud.RedrawTime` 0,05) y los datos avanzaban a saltos de 8/s. ✅ `GraphRate` 8 → **30** (CDO; la instancia de la Obra lo tomó) · `MaxSamples` 48 → **180** (misma ventana de 6 s, 4× más fina) · `RedrawTime` → **0** (plantilla del componente + la instancia de la Obra, que tenía el suyo).
- Pixelado / gris: `LineWidth` 2,4 → **3,2** (AA ya activo) · `LineColor` blanco cálido (1, 0,93, 0,82, α 1).
- **Halo**: `OnPaint` dibuja primero un `DrawLines` ancho y tenue (`GlowColor` (1, 0,62, 0,32, 0,22) · `GlowWidth` 11, A-GraficoEEG, instance-editable) y encima el trazo.
- ⬜ Visor: fluidez y costo del repintado por cuadro (RT 1920×1080). Si baja de 72 fps: `RedrawTime` 0,0278 (36 Hz) en el `Hud` de la Obra.
