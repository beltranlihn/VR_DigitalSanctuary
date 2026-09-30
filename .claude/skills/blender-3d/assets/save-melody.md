# El botón SAVE MELODY del secuenciador: `SM_SaveMelody_{Base,Plate,Slider}_SC`

**Pedido de Beltrán (2026-09-30):**
- *"Hay que crear el botón para guardar melodía en el sequencer. Que va en la mano. Quizás hacerlo de esta misma onda"* (la del timbre, [bell.md](bell.md)).
- *"Se apuntará con el line trace. Se debe activar con hover, y con trigger se empieza a cargar."*
- *"Más rectangular con bordes curvos, para poder tener el texto save melody"*; *"como 15 cm de largo"*.
- *"El aro de carga debiera dar toda la vuelta al rectángulo para llegar al 100%."*

Estado: 🟡 v2 enviada · ⬜ OK final · ⬜ Unreal. Pregunta abierta: al completar, ¿el texto cambia a SAVED o solo destella y se apaga? (por ahora: destello, como el `BP_SaveMelody_SC` actual).

## Forma (rectángulo redondeado 150 × 60 mm, esquinas r 19)

- **Base**: borde de 15 mm de alto y 4,8 mm de ancho con el canto redondeado; adentro, un **canal** de 5,4 mm alrededor de la placa cuyo fondo (h 6) y paredes hasta h 10 son la **cinta de luz** (slot `Ring`).
- **Placa-botón**: contorno desplazado 10,2 mm hacia adentro, tope a h 17,7 (asoma 2,7 mm sobre el borde), canto r 2,5. Lleva el texto. **Recorrido 4 mm** con el gatillo; con el hover sube 1 mm.
- **Slider**: aro plano TRANSPARENTE al ras de la espalda, de 5 a 9 mm afuera del contorno, 3 mm de espesor (como el timbre: "margen inferior").
  - UV0.x = fracción del **perímetro** en sentido horario desde arriba al centro, visto de frente → con `Progress` 0-1 da **la vuelta completa** al rectángulo.
- **Texto**: `T_SaveMelody_Text.png` (2048 × 626, Avenir Book, blanco sobre negro, altura de mayúscula 9,5 mm, espaciado +6 %) como máscara sobre UV1 `TextUV` (planar sobre el tope; el resto de la placa en −1).
  - El PNG va **sin voltear**: Blender pone su fila de arriba en V=1 y el FBX invierte V al pasar a Unreal, donde V=0 es la fila de arriba. La v1 lo volteaba y salió cabeza abajo.

## Estados (la vista previa ya los simula; el BP en Unreal usa los mismos números)

| Estado | Placa | Cinta (`Glow`) | Texto (`TextGlow`) | Slider |
|---|---|---|---|---|
| Disponible | 0 | 0,7 | 0 (blanco hueso) | nada |
| Hover (láser encima) | +1 mm | 1,0 | 1 (luz cálida) | nada |
| Gatillo sostenido | −4 mm | 0,7 + 1,0 · Press | 1 | se llena con `Progress` |

- **Slider sin costura**: progreso efectivo = `Progress · (1 + 2e)` con borde suave `smoothstep(0, 2e, pe − UV.x)`, e = 0,004. Así en 0 no asoma la marquita de arriba y en 1 la costura del perímetro (x = 0/1) queda cerrada. Copiar tal cual al material de Unreal.

## Mallas (`scripts/gen_save_melody.py`, usa `rrect_outline` + `sweep_rrect` de `scripts/revolve_lib.py`)

- Mismo origen para las tres: centro de la espalda, frente hacia +Z. El BP mueve la placa en Z.
- `SM_SaveMelody_Base_SC`: 5.180 tris, slots Body · Ring.
- `SM_SaveMelody_Plate_SC`: 2.588 tris, slots PlateSide · PlateTop (UV1 `TextUV`).
- `SM_SaveMelody_Slider_SC`: 3.672 tris, slot Slider.
- Todas cerradas, 0 degeneradas, 0 dadas vuelta. Salida: `VR_Test/Saved/ClaudeScripts/SaveMelody/` (FBX + `SM_SaveMelody_SC.blend`).
- `sweep_rrect` barre un perfil 2D (desplazamiento, altura) a lo largo del contorno del rectángulo redondeado con normales exactas. El contorno va en sentido horario → las caras laterales se arman `(A[j], B[j], B[j2], A[j2])`, si no salen todas dadas vuelta.
- La textura del texto la hace `scripts/gen_save_melody_text.py` con el Python del sistema: el de Blender no trae PIL.
- Vista previa: `scripts/render_save_melody_unlit.py -- <dir> <salida> [progress] [cuadros_anim]`. Vistas frente / hover / apretado / canto; la animación hace disponible → hover → gatillo y carga → completo.
