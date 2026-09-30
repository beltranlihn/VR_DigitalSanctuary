# El cuadro de resultados: `SM_ResultsRim_SC` · `SM_ResultsGlass_SC` · `SM_ResultsWin{21,19,17}_SC` · `SM_ResultsTip_SC` · `SM_Results_Trace_SC`

**Encargo de Narrativa (director de la noche, 2026-09-30).** La propuesta la aprobó Beltrán en la web (`world.js`, sección "RESULTADOS", paso 9.4).

Es *"una versión grande del HUD"*, que aparece al final, de vuelta en el Hall:
- marco biselado;
- base translúcida;
- ventanas enmarcadas, como la del EEG;
- una cajita arriba para el texto que explica lo que apunta el láser.

Los contenidos (gráficos, textos, el gusano) los pone Narrativa.

**Estado:** 🟢 modelado + vista previa + entrada (Blender) · 🟢 GLB en la web · ✅ en Unreal (2026-09-30): `BP_ResultsArt_SC` compilado y probado en Simulate en `Results/Test_Results` · ⬜ visor.

## Medidas (m, visto a 2 m; las de Narrativa)
| | Valor |
|---|---|
| Panel | 1,10 × 1,02, radio de esquina 0,06 |
| Franja del título | centro y +0,4325, alto 0,095. **Sin malla**: es texto de Narrativa sobre la lámina |
| Ventanas | ancho 1,03, radio 0,03 |
| · calma | centro y +0,26, alto 0,21 (`SM_ResultsWin21_SC`) |
| · latido | +0,03, alto 0,21 (la misma malla) |
| · respiración | −0,18, alto 0,17 (`SM_ResultsWin17_SC`) |
| · melodía | −0,38, alto 0,19 (`SM_ResultsWin19_SC`) |
| Cajita del texto | 0,92 × 0,17, radio 0,026 (el de la web), centro y +0,625 |

Entre filas quedan 2 cm, y 3-3,5 cm hasta el borde.

## Piezas y secciones (mm)
- **Marco `SM_ResultsRim_SC`** (1.472 tris, slot `Rim`). Huella de 11 mm (la de la web), z −6..+6. El perfil tiene:
  - pared exterior;
  - **labio redondeado** de 5 mm;
  - **chaflán a 45°** que baja 6 mm hacia la lámina (el bisel se lee con la luz falsa: claro abajo, oscuro arriba);
  - pared interna.
  - Translúcido 0,55.
- **Lámina `SM_ResultsGlass_SC`** (44 tris, slot `Glass`): una cara en z −2,5, ENTERA, que llega a la pared interna del marco. Ahumada, 0,55.
  - v1 tenía las ventanas caladas y en la entrada los huecos se veían como ranuras claras. Ver *Vueltas*.
- **Ventanas `SM_ResultsWin*_SC`** (1.024 tris, slots `Frame` + `Pane`):
  - contorno de 4 mm hacia ADENTRO del contorno exterior, z −2,5..+1,5, apoyado en la lámina, translúcido 0,45;
  - vidrio oscuro de la abertura en z −2,0, SOBRE la lámina, opacidad 0,30, UV 0..1 sobre la abertura;
  - abertura: 1.022 × (alto − 8), radio 26;
  - los contenidos de Narrativa van desde z −1,5.
- **Cajita `SM_ResultsTip_SC`** (1.252 tris, slots `TipFrame` + `TipGlass`): marco biselado chico (7 mm: labio 3 + chaflán 4, z ±4) y su vidrio en z −1,5, opacidad 0,74.
- **Trazo `SM_Results_Trace_SC`** (184 tris, slot `Trace` → `M_AppearTrace_SC`): cinta de ±16 mm sobre el labio del marco (z +6,5). Arranca arriba al centro.

## Ejes
- **Construcción**: acostado en XY, cara +Z, +Y = arriba del panel. Es el mismo marco que el HUD, así los helpers de `revolve_lib` sirven tal cual.
- **FBX para Unreal**: PARADO, cara hacia **+X**, arriba **+Z**, ancho en Y (Unreal espeja la Y, pero el panel es simétrico a lo ancho). La malla se gira con `mesh.transform()`, que en Blender 5.2 **sí gira las normales a medida** (verificado).
- **`.blend` y GLB**: parado, cara hacia −Y de Blender = **+Z de glTF**, arriba +Y de glTF. `world.js` lo usa **sin rotar**, a diferencia del HUD.

## La entrada (familia "luz primero"; t 0..1 = `Duration` del componente, propuesta 2,0 s; la salida es la misma al revés)
| t | Pieza | Qué hace | Quién |
|---|---|---|---|
| 0,00-0,30 | trazo | la luz dibuja el contorno del panel | `BPC_AppearLuz_SC` (`AppearTrace`) |
| 0,24-0,56 | marco | rendija de canto → párpado, se enfría (`Flash`) | `BPC_AppearLuz_SC` (`AppearBody`) |
| 0,42-0,66 | lámina | se abre desde el centro hacia arriba y abajo (ease in-out cúbica) | `PoseResults` |
| 0,48-0,88 | ventanas | en CASCADA de arriba abajo (0,48 · 0,54 · 0,60 · 0,66; 0,22 cada una). Se abren a lo ancho desde el centro y el alto sube de 0,15 a 1, con destello en el contorno | `PoseResults` |
| 0,56-0,80 | título | se funde (`KTitle`) | Narrativa |
| fin de su ventana − 0,06, durante 0,14 | cada contenido | se funde (`KCalm`…`KMelody`) | Narrativa |
| — | cajita | NO entra con el panel: se abre al apuntar (`TipShow`/`TipHide`, 0,35 s, como una ventana) y solo con el panel entero | `PoseResults` + `TickTip` |

- El marco de 1 m que se abre como párpado barre hacia el usuario (el borde de abajo avanza hasta ~50 cm a mitad de camino). En la vista previa se lee como un panel que se despliega; **verificar en visor** que no incomode.
- Control automático (`compose_anim.py`): el último cuadro es igual al reposo (media 0,000).

## Vueltas
- **v1 → v2 (antes de mostrar)**: con la lámina calada, en la entrada los huecos de las ventanas se leían como ranuras claras antes de que llegaran las ventanas.
  - Ahora la lámina es ENTERA y cada ventana apoya su vidrio encima (0,30), como la web (lámina .55 + vidrio .3). El oscuro final de las ventanas es el mismo.
  - Costo: una capa translúcida más sobre las ventanas; es la pantalla final, sin mecánica corriendo.

## Scripts
- `scripts/gen_results.py`: las piezas, los FBX (girados a los ejes de Unreal) y `SM_Results_SC.blend`, armado parado en la orientación de la web.
- `scripts/make_results_sample_tex.py` (Python del sistema, PIL): los contenidos DE MUESTRA para la vista previa (título, 2 gráficos, anillos, gusano y el texto de la cajita).
- `scripts/render_results.py -- <dir> stills|anim`: la vista previa sobre un fondo tipo Hall y la entrada en cuadros. Después, `compose_anim.py` arma el GIF y la hoja.
- `scripts/export_results_glb.py`: el GLB de la web, con la rotación horneada (los nodos solo llevan traslación).
- Salida: `VR_Test/Saved/ClaudeScripts/Results/` (FBX, `.blend`, `stills/`, `anim/`, `tex/`, `results_materials_build.json`).

## Unreal (hecho el 2026-09-30; ver `unreal-vr/blueprints/BP_ResultsArt_SC.md`)
- `/Game/SoulCharger/Mechanics/Results/`: las 7 mallas sin colisión, 6 MI y `BP_ResultsArt_SC`.
- Maestros **nuevos** en `Appear/`: `M_SCPanel_SC` (hormigón translúcido) y `M_SCPanelGlass_SC` (lámina).
  - Son los del HUD **sin el doblez y con prueba de profundidad**: el cuadro está en el mundo. Si llevara el doblez de `MPC_HUD_SC`, se curvaría; sin depth test, taparía a Alma.
  - Plan: `unreal-vr/scripts/plan_results_materials.py`.
- Web: `web/prototipo-narrativo/modelos/SM_Results_SC.glb` (+ `.json`). Nodos `Rim`, `Glass`, `WinCalm/WinHeart/WinBreath/WinMelody` (en su y), `Tip` (y 0,625).
