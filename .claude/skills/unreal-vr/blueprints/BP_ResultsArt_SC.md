# BP_ResultsArt_SC — el arte del CUADRO DE RESULTADOS, con su entrada "luz primero" por piezas

- **Ruta**: `/Game/SoulCharger/Mechanics/Results/BP_ResultsArt_SC`.
- **Estado**: 🟢 creado, compilado y guardado (2026-09-30, turno de Mesh 3D) · 🟢 Simulate en `Test_Results`: espera de 3 s → entrada → reposo exacto (AppearT 1, K* = 1, `WinCalm` en z 26 con escala 1), sin errores en el log · ⬜ muestreo de la entrada a mitad de camino (la latencia MCP supera los 2 s; las fórmulas son las de Blender) · ⬜ visor.
  - Diseño aprobado por Narrativa: marco, bisel, cascada de ventanas y la cajita que se abre al apuntar.
- **Es solo arte + aparición.** Los contenidos (título, gráficos de calma y latido, anillos de respiración, el gusano, los textos de la cajita), el láser y los sonidos de hover son de Narrativa (`BP_Obra_SC` / resultados).
- **Modelo**: `blender-3d/assets/results.md`.
  - Scripts del turno: `unreal-vr/scripts/results_entry_dsl.py` (DSL) y `plan_results_materials.py` (materiales).

## Componentes (StaticMesh sin sombra; cara del actor = **+X**, arriba = **+Z**, ancho en Y)
| Componente | Malla | Ubicación (cm) | Sort translúcido | Tag |
|---|---|---|---|---|
| `Glass` | `SM_ResultsGlass_SC` | 0 | 1 | |
| `WinCalm` | `SM_ResultsWin21_SC` | z +26 | 2 | |
| `WinHeart` | `SM_ResultsWin21_SC` | z +3 | 2 | |
| `WinBreath` | `SM_ResultsWin17_SC` | z −18 | 2 | |
| `WinMelody` | `SM_ResultsWin19_SC` | z −38 | 2 | |
| `Rim` | `SM_ResultsRim_SC` | 0 | 4 | `AppearBody` |
| `Tip` | `SM_ResultsTip_SC` | z +62,5 | 5 | |
| `Trace` | `SM_Results_Trace_SC` (slot → `M_AppearTrace_SC`) | 0 | 6 | `AppearTrace` |
| `Appear` | `BPC_AppearLuz_SC`: FaceAxis (1,0,0), PivotDepth 0, **Duration 2,0**, AppearSound `SBubbleHoverOn`, VanishSound `SBubbleHoverOut` (Narrativa: los de las cargas, SOLO en este componente) | | | |

- Los contenidos de Narrativa van con **sort 3** (entre las ventanas y el marco) y desde **x −0,15 cm** (delante del vidrio de la ventana).
- **Láser** (pedido de Narrativa): el rig de Secuencer usa `LineTraceForObjects` con Object Type **Destructible**.
  - Las 4 ventanas: **QueryOnly + `ECC_Destructible` + todas las respuestas en Ignore**.
  - `Glass`, `Rim`, `Tip` y `Trace`: **NoCollision**.
  - El actor lleva el tag **`Aimable`**: el punto del láser se pega al impacto.
  - Va en el template (`BodyInstance`) **y** en `BeginPlay` → `SetupCollision`, porque el `BodyInstance` serializado de una instancia le gana al del BP (gotcha 353).
  - Las mallas `SM_ResultsWin*_SC` llevan **un casco convexo** (`generate_convex_collisions`, 1 casco): el trazo por objetos es simple por defecto. Las demás mallas, sin colisión.
  - El impacto devuelve el componente: `WinCalm` = calm, `WinHeart` = heart, `WinBreath` = breath, `WinMelody` = melody.

## Materiales (`Results/` + maestros nuevos en `Appear/`)
- `M_SCPanel_SC` = `M_SCObjectTrans_SC` (hormigón translúcido, `Flash`, `Opacity`) y `M_SCPanelGlass_SC` = `M_SCGlass_SC`, pero **SIN el doblez del HUD y CON prueba de profundidad**.
  - El cuadro está en el mundo: con el doblez de `MPC_HUD_SC` se curvaría, y sin depth test taparía a Alma.
  - Los maestros del HUD no se tocan.
- MI:
  - `MI_Results_Rim_SC`: Opacity 0,55.
  - `MI_Results_Frame_SC`: contornos de las ventanas, 0,45.
  - `MI_Results_TipFrame_SC`: 0,55.
  - `MI_Results_Glass_SC`: lámina ahumada, Color (0,55; 0,60; 0,85), Base 0,10, Rim 0,12, Opacity 0,55.
  - `MI_Results_Pane_SC`: vidrio de la ventana, SOBRE la lámina, 0,30.
  - `MI_Results_TipGlass_SC`: 0,74.

## API (para `BP_Obra_SC` / Narrativa)
| | |
|---|---|
| Eventos | `ResultsAppear` · `ResultsVanish` (cierra la cajita y sale al revés) · `ResultsHideNow` (oculto al instante, listo para `ResultsAppear`) · `TipShow` · `TipHide` |
| Reloj | `Appear.AppearT` (0 oculto … 1 entero); dispatchers `Appear.OnAppeared` / `OnVanished` |
| Para fundir contenidos | `KTitle`, `KCalm`, `KHeart`, `KBreath`, `KMelody` (0..1, smoothstep, en su momento de la entrada) y `KTip` (= apertura de la cajita) |
| Prueba suelta | `AppearOnPlay` (default **false**, regla 3 del plan de la noche) + `AppearDelay` (3 s), instance-editable. En la Obra lo dispara el director |

## Grafos
- **`PoseResults(T)`** (generado por `results_entry_dsl.py`, mismos tiempos que `render_results.py`):
  - **lámina** 0,42-0,66: escala Z 0 → 1, ease in-out;
  - **ventanas en cascada** 0,48 / 0,54 / 0,60 / 0,66, 0,22 cada una: escala Y (ancho) con ease out cúbico, Z (alto) de 0,15 a 1 desde el 30 % de su tramo, `Flash` 0,6·sen(πu);
  - **cajita** = `TipK` × S(0,80..0,95);
  - escribe los `K*`.
  - Todo es relativo al reposo capturado en BeginPlay (`Rest*`).
- **`TickWait(Dt)`**: la espera de prueba, igual que el HUD.
- **`TickTip(Dt)`**: `TipK` → `TipTarget` en 0,35 s.
- **EventGraph**:
  - `BeginPlay` llama a `SetupCollision`, captura `Rest*` y, con `AppearOnPlay`, hace `Prepare` + `PoseResults(0)` y la espera.
  - `Tick` usa **Dt = min(DeltaSeconds, 1/30)** (regla de carga del plan) y re-posa solo cuando cambian `AppearT` o `TipK`.
  - Además los eventos de la API.

## Nivel de prueba `/Game/SoulCharger/Mechanics/Results/Test_Results` (pedido de Narrativa)
- Es una copia de `Test_Appear`: oscuro, sin luces, `BP_XRGameMode`.
- Vacío salvo el PlayerStart y `BP_ResultsArt_SC` a 2 m al frente, mirándolo. El centro queda a ~122 cm sobre el piso: ojos sentados ~120 (tracking Stage) + 2 cm, como `front(p, 2, .02)` de la web.
- En la instancia: `AppearOnPlay` true + 3 s (flag de test).
- Ahí prueban Drawing (el contenido), Secuencer (el gusano y el láser) y Narrativa (el armado).

## Trampas de la construcción (2026-09-30)
- Los enums del DSL van entre comillas: `(Collision|SetCollisionEnabled comp "NoCollision")`. Sin comillas da *"Undefined variable"*. El write fallido no deja nodos.
- 🔴 Editar el actor en caliente (Simulate) re-corre su construction script y deja los `Rest*` en identidad: las ventanas se apilan en el centro (gotcha 521). No es un bug de juego.
- `TipTarget` (no instance-editable) no se puede escribir en la instancia de PIE, y el error tumba el script entero (gotcha 520).

## Pendientes
- [x] Turno (2026-09-30): import, materiales, BP, 5 grafos por DSL, compilado y guardado, `Test_Results`.
- [x] Simulate: entrada completa y reposo exacto.
- [ ] Cajita en juego (`TipShow`/`TipHide`): la lógica es la de las ventanas; `TipTarget` no es editable en la instancia, así que se prueba con el láser de Secuencer.
- [ ] Contenidos de Narrativa/Drawing/Secuencer encima (sort 3, desde x −0,15).
- [ ] Visor: que el párpado de un panel de 1 m (el borde de abajo avanza ~50 cm a mitad de camino) no incomode; si molesta, bajar el ángulo inicial.
