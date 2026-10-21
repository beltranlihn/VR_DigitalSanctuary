# El cuadro de resultados de la DEMO: `SM_DemoResults_{Base,Sheet,WinEEG,WinPulse,WinBreath,WinCalm,Trace}_SC`

**Encargo de la sesión Director (2026-10-19), con el guion nuevo de Beltrán para la Barcelona Design Week (mié 2026-10-21).** Cada experiencia (Breath, Draw) termina con este cuadro: **gráfico de actividad neuronal (EEG), gráfico de pulso, círculos por ciclo de respiración y un índice de calma grande a la derecha.** 1000 × 560 mm, visto a ~1,6 m. **v2 (2026-10-19, pedido de Beltrán): curvo hacia el usuario, como el panel de instrucciones ([instr-card2.md](instr-card2.md)), y las 4 ventanas como mallas separadas ya en su lugar.**
- Misma familia que el cuadro de resultados de la Obra ([results.md](results.md)): **lámina entera** + **el vidrio de cada ventana apoyado encima** + **ventanas enmarcadas** (4 mm hacia adentro, como la del EEG del HUD). El marco es el de la familia **"marco con cinta de luz"** (los cuadros de la demo y el SHARE): borde + canal con la cinta + labio, en vez del biselado de la Obra.
- Distinto del de la Obra: no hay franja de título ni cajita de texto; hay **3 ventanas anchas a la izquierda y 1 alta a la derecha**.
- 🔴 **El contenido se dibuja DENTRO del material del vidrio (`Pane`) con un render target**: por eso la UV0 del `Pane` es **0..1 sobre la abertura, calculada ANTES de doblar** (ver más abajo).

**Estado:** 🟢 modelado curvo + 4 ventanas separadas + UV del vidrio verificada + hoja de vista previa · ⬜ Unreal (Director) · ⬜ visor.

## Medidas (mm; FBX = el marco de Unreal)
| | |
|---|---|
| Contorno exterior | **1000 × 560** (semiejes A 500, B 280), esquinas **r 60** |
| Sección del marco | la de la familia: borde de 15 mm (canto r 3,5 / 3,0), pared de 4,8, canal de 5,4 con la cinta (piso z 6, pared lit hasta z 10), y un **labio interior** de 2,4 mm a z 12,5. Ancho total **12,6 mm** |
| Lámina | una cara entera a **z 9,0** (3,5 mm bajo el labio); llega a la pared interior del marco (semiejes ≈ 487,4 × 267,4). UV 0..1 sobre la lámina |
| Ventanas | esquinas **r 20**; contorno de **4 mm hacia ADENTRO** (z 9,0 … 13,0, filete 1,2 al frente); el vidrio de la abertura a **z 9,5** (0,5 mm sobre la lámina) |
| Trazo | cinta de ±6,5 mm sobre el borde y la boca del canal (z 15), centro a 7 mm del contorno |

En construcción (mm desde el centro de la cara, +x derecha del espectador, +y arriba): **EEG, pulso y respiración** de 600 × 150, x −460 … +140 (centro −160), centros y **+170 · 0 · −170**; **calma** de 280 × 490, x +180 … +460 (centro +320), centro y 0.

### 🔴 La curva (`CURVE_R`, en `gen_demo_results.py`; **default 1600 mm**, 0 = plano; también `--curve R` en la línea de comandos)
**Todo** (Base, Sheet, las 4 ventanas, Trace) está **doblado alrededor del eje vertical (Z de Unreal), con los extremos hacia el usuario (+X)**.
- `R` es el radio de la **superficie del vidrio** (z 9,5 mm): `r = R + 9,5 − z` · `x' = r·sin(x/R)` · `z' = (R + 9,5) − r·cos(x/R)`. **El origen (centro de la espalda) no se mueve**; la sección se dobla entera (cara y espalda paralelas) y las normales se giran con la misma transformación (sombreado exacto).
- **Centro de la curva = el ojo**: en **X = 160,95 cm (R + 0,95), Y = 0, Z = 0** (a la altura del centro del cuadro). El vidrio de **todas** las ventanas queda a **160 cm del ojo** en todo el ancho; el borde del marco (z 15), a 159,45 cm.
- **Las UV se calcularon ANTES de doblar**, sobre el cuadro plano, por posición: el arco conserva el largo sobre el vidrio (las aberturas miden en el arco lo mismo que planas: 592 mm las anchas, 272 la alta), así el contenido no se estira.
- Los tramos rectos horizontales se subdividen para seguir la curva (base y marcos de las ventanas: tramos de ≈ 90 mm; trazo: ≈ 45 mm; la lámina y los vidrios se cortan con planos cada ≈ 64 mm): desvío de la curva ≤ 0,7 mm. Los verticales no se subdividen (son generatrices del cilindro).

## 🔴 Rectángulos exactos (cm, marco de Unreal, ya DOBLADOS, sobre la superficie del vidrio; origen = centro de la espalda de la `Base`)
⚠ **Unreal espeja la Y**: `Y_UE = −(derecha del espectador)`. **La columna de las 3 ventanas largas queda a la IZQUIERDA del espectador, o sea en Y_UE POSITIVA**; la ventana alta, a la derecha, en Y_UE negativa. Control de un vistazo al importar: las tres ventanas largas se ven a la izquierda mirando el cuadro de frente.

**Centro de cada abertura, y X/Y de su borde izquierdo y derecho DEL ESPECTADOR (a media altura)** — la abertura es la ventana menos 4 mm por lado (donde va el contenido; esquinas r 16 mm):
| Ventana | Mesh | Centro (X ; Y_UE ; Z) cm | Borde **izquierdo** del espectador (X ; Y_UE) | Borde **derecho** del espectador (X ; Y_UE) | Z (cm) | Tamaño plano (cm) |
|---|---|---|---|---|---|---|
| **EEG** (arriba izq.) | `WinEEG` | **(1,749 ; +15,973 ; +17,0)** | (7,404 ; +44,985) | (1,528 ; −13,584) | +9,9 … +24,1 | 59,2 × 14,2 |
| **Pulso** (medio izq.) | `WinPulse` | **(1,749 ; +15,973 ; 0)** | (7,404 ; +44,985) | (1,528 ; −13,584) | −7,1 … +7,1 | 59,2 × 14,2 |
| **Respiración** (abajo izq.) | `WinBreath` | **(1,749 ; +15,973 ; −17,0)** | (7,404 ; +44,985) | (1,528 ; −13,584) | −24,1 … −9,9 | 59,2 × 14,2 |
| **Calma** (alta der.) | `WinCalm` | **(4,139 ; −31,787 ; 0)** | (2,007 ; −18,359) | (7,404 ; −44,985) | −24,1 … +24,1 | 27,2 × 48,2 |

- Contorno COMPLETO de las ventanas (arriba de su marco, a z 13 mm): izq./der. del espectador = (7,853 ; +45,27) / (1,911 ; −13,952) las tres largas; (2,309 ; −17,923) / (7,853 ; −45,27) la alta. Z de las ventanas: ±7,5 cm cada larga alrededor de su centro (9,5 … 24,5 · −7,5 … 7,5 · −24,5 … −9,5) y ±24,5 la alta.
- Separaciones (planas): 2,0 cm entre las filas de la columna izquierda, 4,0 cm entre las dos columnas y 2,2 cm (arriba y abajo) / 2,7 cm (a los lados) hasta la pared interior del marco.
- **X** es la profundidad del vidrio en cada punto (z 9,5 mm doblado): 0,95 cm en el centro del cuadro, 1,75 en el centro de las ventanas largas, 4,14 en el centro de la alta y 7,40 en el borde izquierdo de las largas (el extremo del cuadro).

### 🔴 UV0 del `Pane` (para el render target)
**0..1 sobre la abertura**, calculada por posición sobre la ventana **plana** (antes de doblar): **u = 0 en el borde izquierdo DEL ESPECTADOR, u = 1 en el derecho; v = 0 abajo, v = 1 arriba** (+v arriba, la misma convención que `TextUV`): un PNG guardado sin voltear se lee derecho en Unreal (gotcha 34). Rango leído de vuelta del FBX: −0,0001 … 1,0004 (el vidrio entra 0,05 mm bajo el contorno para no dejar rendija). **Verificado**: un render con las texturas de muestra aplicadas por la UV0 del `Pane` las muestra derechas y llenando exactamente la abertura sobre la malla ya doblada.
- La `Sheet` también lleva UV0 0..1 sobre su cara; `Base` y `Frame` llevan la UV de barrido (sin uso previsto).

## Cajas en el marco de Unreal (cm, ya dobladas; X = profundidad / cara, Y_UE = −derecha, Z = alto)
| Malla | X | Y_UE | Z |
|---|---|---|---|
| `Base` | 0 … 9,16 | ±49,40 | ±28,00 |
| `Sheet` | 0,90 … 8,27 | ±48,01 | ±26,75 |
| `WinEEG` | 0,92 … 7,82 | −13,98 … +45,38 | +9,5 … +24,5 |
| `WinPulse` | 0,92 … 7,82 | −13,98 … +45,38 | −7,5 … +7,5 |
| `WinBreath` | 0,92 … 7,82 | −13,98 … +45,38 | −24,5 … −9,5 |
| `WinCalm` | 1,92 … 7,82 | −45,38 … −17,94 | ±24,5 |
| `Trace` | 1,50 … 9,21 | ±48,97 | ±27,95 |

- **Para el `Hit`** (el láser sobre el cuadro; caja de todo el cuadro + 0,2 cm): centro **(4,60 ; 0 ; 0)**, extensión **(4,80 ; 49,60 ; 28,20) cm**. (Caja total: X 0 … 9,21, Y_UE ±49,40, Z ±28,00.)
- **Colocación**: las 7 mallas se importan **en el mismo origen** (X 0, Y 0, Z 0): las 4 ventanas ya vienen en su lugar y dobladas, con el origen del cuadro (centro de la espalda de la `Base`). **No hay que mover ni duplicar ninguna.**
- `AppearLuz` (el trazo): FaceAxis (1,0,0), PivotDepth 1,5, Duration 1,5 como el SHARE (o la entrada por cascada del cuadro de la Obra: trazo → marco → lámina → ventanas de arriba abajo). El trazo ya viene doblado (su centro en X = 1,5 cm).

## Partes, slots y triángulos
| Malla | Slots (en orden) | Tris |
|---|---|---|
| `SM_DemoResults_Base_SC` | 0 `Body` · 1 `Ring` (fondo y pared baja del canal: la luz). **Anillo cerrado**, sin tapas | 3.472 |
| `SM_DemoResults_Sheet_SC` | 0 `Sheet` | 188 |
| `SM_DemoResults_WinEEG_SC` / `_WinPulse_SC` / `_WinBreath_SC` | 0 `Frame` (contorno de 4 mm) · 1 `Pane` (vidrio de la abertura) | 1.264 c/u |
| `SM_DemoResults_WinCalm_SC` | 0 `Frame` · 1 `Pane` | 1.056 |
| `SM_DemoResults_Trace_SC` | 0 `Trace` (cinta abierta a propósito; UV0.x = fracción del contorno desde arriba, antihorario visto de frente) | 312 |
| **Total** (cada malla va una vez) | | **8.820** (presupuesto ≤ 10.000) |

- Materiales en el FBX: `M_DemoResults_{Body,Ring,Sheet,Frame,Pane,Trace}` (uno por nombre: las 4 ventanas comparten `Frame` y `Pane`).
- **Sugerencia de materiales** (los del cuadro de la Obra, [results.md](results.md#unreal-hecho-el-2026-09-30)): `Sheet` → la lámina ahumada (translúcida ~0,55), `Frame` → hormigón translúcido (~0,45), `Pane` → vidrio oscuro (0,30) **con el contenido dibujado por el render target**, `Body`/`Ring` → los del cuadro de experiencia (`Ring` emisivo, con su `Glow`). Ninguna lámina se mete debajo de un contorno translúcido (la lámina llega a la pared del marco; el vidrio solo 0,05 mm bajo el contorno de su ventana).
- Controles (leyendo los FBX de vuelta en otro Blender): **0 abiertas** salvo las que son por diseño (lámina 74 aristas de borde; vidrio de cada ventana 54 las largas y 46 la alta; cinta del trazo 160), **0 degeneradas**, **0 dadas vuelta**, volumen con signo > 0 en las partes cerradas (base; contorno de cada ventana), **0 astillas < 0,01 mm²** (área mínima: 2,09 mm² la base, 0,41 la lámina, 0,36 las ventanas, 23,6 el trazo).
- 10 tramos por esquina del contorno y 8 en las ventanas.

## Ejes y origen
- **Construcción**: acostado en XY, cara +Z, +Y = arriba, +X = derecha del espectador.
- **FBX**: PARADO, cara hacia **+X**, arriba **+Z**, ancho por **Y**; escala 1, metros. Las 7 mallas con el mismo origen (centro de la espalda de la `Base`, en el centro del cuadro).
- **`.blend`**: parado (cara −Y de Blender = +Z de glTF), objetos `Base`, `Sheet`, `WinEEG`, `WinPulse`, `WinBreath`, `WinCalm`, `Trace`, todos en su lugar.
- ⚠ Los FBX **`SM_DemoResults_WinWide_SC` y `_WinTall_SC`** que quedan en la carpeta son de la **v1 plana** (ventana con origen en su centro, para instanciar): **obsoletos**, no se regeneran.

## Vista previa y regenerar (scripts en `blender-3d/scripts/`; todo en `gen_demo_results.py`)
```
# 1) mallas, 7 FBX y .blend (headless)
blender --background --python gen_demo_results.py -- <dir_salida> build
# 2) control: lee los 7 FBX de vuelta
blender --background --python gen_demo_results.py -- <dir_salida> qc
# 3) contenidos DE MUESTRA (solo la vista previa; PIL) y vistas: de frente desde el ojo, oblicua, desde arriba y sin contenidos
python gen_demo_results.py --tex <dir_temp>/tex
blender --background <dir>/SM_DemoResults_SC.blend --python gen_demo_results.py -- <dir> render <dir_temp>/dr <dir_temp>/tex
python gen_demo_results.py --sheet <dir_temp>/dr <dir>/demo_results_sheet.png
```
- Salida: `VR_Test/Saved/ClaudeScripts/Demo2/Modelos/` (`SM_DemoResults_*_SC.fbx`, `SM_DemoResults_SC.blend`, `demo_results_sheet.png`). Para la versión plana: `... -- <dir> build --curve 0` (las ventanas siguen saliendo en su lugar).
- La hoja muestra: de frente desde el ojo a 1,6 m, oblicua, **desde arriba (el arco)** y sin contenidos. Los contenidos de la hoja (EEG violeta, pulso rojo, círculos por ciclo, "82") son **de muestra**, dibujados con la misma curva para ver la proporción y el aire de cada ventana; los reales los pone el Director.
- Perillas: `CURVE_R`, `CURVE_Z`, `A, B, RC`, `WIN_RC`, `WIN_FW`, `SHEET_Z`, `Z_LIP`, `WIDE`, `TALL`, `COLS` (nombres y centros de las ventanas), `STEP_X`, `N_ARC`, `N_ARC_WIN`.

## Notas de construcción
- La lámina y los vidrios son **islas** (no comparten aristas con otra malla del mismo bmesh): se cortan con planos `x = const` (`bisect_plane` solo sobre sus caras) para que la cara plana siga la curva sin dejar T. Las normales exactas viajan en una capa de vértices que `bisect_plane` interpola; se doblan con la inversa transpuesta del jacobiano de la curva.
- Un volumen con signo de una malla con caras abiertas depende del origen: se mide solo sobre las partes cerradas (el contorno de cada ventana, la base).
- `materials.clear()` en un mesh **reinicia los índices de material de las caras** (lo aprendí probando la UV del vidrio): para cambiar materiales se asigna por índice (`me.materials[i] = m`).

## Pendientes
- [ ] Unreal: importar los 7 FBX en el mismo origen, armar `BP_DemoResults_SC` y los materiales; el render target dentro del `Pane` (Director).
- [ ] Visor: la curva a 1,6 m, la legibilidad del índice de calma y de los gráficos.
