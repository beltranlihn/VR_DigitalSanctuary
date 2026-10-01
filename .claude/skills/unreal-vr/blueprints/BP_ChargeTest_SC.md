# BP_ChargeTest_SC — prueba de la carga del alma (teletransporte HUD ↔ frente)

`/Game/SoulCharger/Mechanics/HUD/` · 2026-09-30 · Narrativa. La coreografía aprobada por Beltrán en el prototipo web (función `teleport` de `web/prototipo-narrativo/guion.js`), llevada a Unreal para probarla en el visor. Colocado en `Test_Hall` como `ChargeTest`, con el punto de carga `ChargeTarget` (TargetPoint en (−315, 0, 112): ~75 cm al frente y 10 cm bajo la vista).

## Idea
Es un teletransporte, así que **no se mueve el mismo objeto**: el anillo del HUD hace "pum" y se achica a casi cero, y en el punto de carga nace un anillo grande propio (`Ring` + `Soul`); a la vuelta, al revés.

## Secuencia (t desde el arranque; `ChargeTime` C = 4)
| t | Qué pasa |
|---|---|
| 0–0,8 | **Aviso**: el anillo del HUD tiembla (0,3 cm locales), al final se encoge y se hincha ×1,25; el borde del HUD se enciende (`Flash` en `Rim`); háptico que crece 0,1 → 0,7; `WarnSound` |
| 0,8–0,92 | **¡Pum!** de salida: el anillo del HUD colapsa; destello chico en su lugar (`PopCore` + `PopWave`); golpe háptico; `PopOutSound` |
| 0,92–1,37 | Silencio |
| 1,37–2,47 | **¡Pum!** de llegada al frente: el anillo grande crece de 0,55 a 1 en el primer 30 %, gira 450° frenando; destello grande con onda; golpe háptico; `PopInSound` |
| 2,47–2,47+C | **Carga**: `Charge_Entering` del anillo grande 0 → 1 (smoothstep); **halo** detrás (`Halo`, color `StageColor`, solo por fuera del anillo, tiembla y se apaga al final de la carga); háptico 0,15 → 0,4; `ChargeSound` |
| +H (`HoldTime` 2) | **Quietud**: el anillo grande queda lleno y quieto, sin háptico ni halo (el reloj se congela: `StepAll` pasa T' = T − clamp(T − (2,47 + C), 0, H)) |
| +0,8 | Aviso de vuelta: tiembla el grande (1,2 cm) y se encoge/hincha; `WarnSound` |
| +0,12 / +0,45 | ¡Pum! de salida del grande + silencio |
| +0,6 | ¡Pum! en el nido del HUD: el anillo vuelve con sobrepaso (1,1 → 1) y ya con `Charge_Entering` = 1; destello chico; `PopInSound` |
| fin | `SettleSound` + toque háptico 0,5; `EndCharge` repone el anillo y el alma del HUD a su pose de reposo |

## Variables (instance-editable)
`HudRef` (el `BP_SoulHUD3D_SC`), `TargetRef` (el TargetPoint: se lee al arrancar; el actor se orienta con +X hacia la cámara), `AutoStart` (true), `StartAfter` (9,5 s = 3 de espera del HUD + 1,5 de su entrada + 5), `ChargeTime` (4), `HoldTime` (2, pedido de Beltrán: espera con la luz encendida antes de volver), `BigScale` (1 = anillo de 46 cm; se multiplica por la ESCALA del TargetPoint), `PopHudSize` (3 cm), `StageColor` (azul Entering), y los sonidos `WarnSound` (ProtoHover), `PopOutSound` (SBubbleHoverOut), `PopInSound` (SBubbleHoverOn), `ChargeSound` (Charge1), `SettleSound` (ProtoSelect), todos placeholder de `Core/Audio/Sounds`.

## Construcción
- Componentes: `Pivot` (escala y giro del grande) con `Ring` (`SM_ChargeRing_SC`, materiales normales) y `Soul` (ChildActor `BP_ChargeSoul_SC`: la ameba de 15 cm con `MI_ChargeSoul_SC` sobre `M_ProtoSoul`, valores de la ameba 0 de `L_SoulCharger_V3`, FloatScale 0,5); `Halo` (Plane, pitch −90, detrás a −15 cm × BigScale, escala 1,1); `PopRoot` con `PopCore` / `PopWave` (Plane, prioridad 210/211, mirando a la cámara cada cuadro).
- `M_ChargeHalo_SC`: aditivo, unlit, dos caras; un Custom (`ChargeHaloPS`) dibuja anillo gaussiano (`Radius`, `Width`) + relleno hacia afuera (`Fill`), máscara interior (`Inner`), temblor (`Flicker`) y `Amount`, `Color`. El mismo material sirve para halo, núcleo y onda (MIDs con distintos parámetros, puestos en `BeginCharge`).
- Grafos: `BeginPlay` → `HideAll` → `ResetRings` (las 5 cavidades en 0 en el anillo del HUD y en el grande: solo se enciende la que carga) → Delay(`StartAfter`) → `BeginCharge` → cadena de Delays con los sonidos (después de `ChargeTime`, otro Delay de `HoldTime`) → `EndCharge`. `Tick` → `StepAll`: calcula T (con la quietud), y si `Running` llama a `StepCharge` (anillo del HUD), `StepBig` (anillo grande, halo, llenado), `StepFx` (destellos y carga del anillo del HUD), `StepFeel` (brillo del borde y háptico con `SetHapticsByValue` en los dos mandos), y fija la escala de MUNDO de `PopRoot` (1 en el HUD, la del actor en el frente).
- `BeginCharge` termina con `SetActorScale3D` = escala del TargetPoint y un `StepAll`: así el primer cuadro ya sale con los destellos en 0. Antes, `BeginCharge` corría desde el Delay DESPUÉS del Tick de ese cuadro y los destellos se veían un cuadro con los valores por defecto del material (el "anillo de destello" que vio Beltrán antes de la llegada).

## Trampas
- En el DSL, `CallFunction|MiFuncion` con un argumento POSICIONAL lo conecta al `self`: los parámetros de funciones propias van con keyword (`:V`, `:A`, `:T`).
- `read_graph_dsl` rotula funciones propias con otra clase (`Class|BPIntroSequence|HideAll`); el nodo real es `|HideAll`. Verificar con `get_node_infos`, no con el read.
- Un `set_pin_value` por valor (0,55) toca TODOS los literales iguales del grafo: se cambió también el `Lerp` del tamaño de llegada; corregido.

## Estado
- 2026-09-30 (2ª vuelta, pedidos de Beltrán en visor): quietud de 2 s antes de volver, luz cargada encendida en los dos anillos (resto apagado), el TargetPoint manda posición Y tamaño, sin el destello de un cuadro al arrancar. Probado en PIE: actor en el objetivo con escala 2,115 mirando al ojo; el anillo del HUD vuelve con solo Entering encendido. ⬜ Visor.
🟡 Probado en PIE: el actor se ubica en el objetivo mirando al ojo, el anillo del HUD desaparece durante la carga y vuelve a su pose exacta; captura con carga larga: anillo grande + alma al frente. ⬜ Visor. ⚠ El halo casi no se ve sobre el fondo claro del Hall (aditivo sobre casi blanco); en las etapas oscuras sí. ⚠ El brillo del borde es un destello de todo el borde (la luz que da la vuelta necesita un parámetro nuevo en el material del HUD).

## 2026-10-01 — el halo de las cargas de la Obra, en ALPHA BLEND (Mesh 3D, pedido de Beltrán vía Narrativa)
- *"El halo de color de la carga casi no se notaba; que se note sin ensuciar"*: el aditivo no suma nada sobre fondos claros (Hall, Uyuni, Entering).
- **`M_ChargeHaloTint_SC`** (`Mechanics/HUD/`) = copia de `M_ChargeHalo_SC` en **Translucent**: el Custom original sigue igual y su salida entra a un Custom nuevo `ChargeHaloTintPS` (`scripts/hlsl/ChargeHaloTintPS.hlsl`): satura el color (`HaloSat` 1,6), alfa = intensidad × `HaloOpGain` 2 con smoothstep (sin borde duro), tope `HaloMaxOpacity` 0,6, `HaloGlow` 1,1.
- Solo el componente `Halo` de **`BP_ChargeFx_SC`** (Obra) lo usa; núcleo, onda y este BP de prueba siguen con el aditivo. La instancia de la Obra lo toma sola (verificado al recargar).
- Costo: el mismo plano; translúcido ≈ aditivo en fill-rate. ⬜ Visor.

## 2026-10-01 (11:00, Narrativa) — `BP_ChargeFx_SC` (la copia de la Obra): `FinalLook` arreglado + `TopSorts(On)`
- `FinalLook`: ahora sí pone `MI_ChargeRing_FrameHUD_SC` / `MI_ChargeRing_LightHUD_SC`, que antes estaban vacíos (§561). El sort del anillo pasa a 32610 y al final llama a `TopSorts(true)`.
- `TopSorts(On)` (función nueva): sorts sobre el velo de la Obra (halo 32606, alma 32608, destellos 32612/13, anillos de etapa 32614-18) y el alma con `MI_ChargeSoulTop_SC` (DDT). Con `false` vuelve a 0 / 210-216 y a `MI_ChargeSoul_SC`. `NormalLook` llama a `TopSorts(false)`.
- La Obra también maneja este actor en el Hall (`HallRing`, ver BP_Obra_SC.md): escribe `StartTime` desde afuera para acelerar o congelar la coreografía.