# Mando de la obra: `SM_QuestCtrl_{Body,Trigger}_{R,L}_SC`

**Pedido de Beltrán (2026-09-29):**
- Reemplazar el mando que se usa hoy (`/Game/ControllerR|L`, "horrible modelado y el botón no es móvil").
- Como el Meta Quest (Touch Plus), de dos colores e **invertido**: cuerpo NEGRO y tapa GRIS-BLANCA.
- **Sin botones**: solo el gatillo, que se mueve y cambia de material al apretar.
- Cáscara **continua**, sin las aberturas de los botones.
- Debe leerse en niveles **sin luz direccional**, con algo de sombra.
- El izquierdo es el derecho espejado.

Estado: 🟢 forma aprobada ("Fff ahí sí. Se ve hermoso") · 🟢 en Unreal: `/Game/SoulCharger/Mechanics/QuestController/` (mallas, `M_QuestCtrl_SC` + 2 MI, `BP_QuestCtrl_SC`, `Test_QuestCtrl`), verificado con capturas · ⬜ visor. FBX con `mesh_smooth_type='FACE'` (sin él, Unreal avisa "No smoothing group information").

## 🔴 El enfoque que funcionó: superficie de subdivisión CALCULADA sobre el modelo oficial

**La forma orgánica primero, y después el vacío para el botón.** Nunca al revés: no tapar agujeros. Beltrán: *"lo construyeron, la forma quedó súper orgánica, y después le agregaron botones. Nosotros hacíamos lo contrario, tapar un hoyo"*.

1. El mando es una **superficie Catmull-Clark** con una jaula de ~1.900 puntos de control (quads de QuadriFlow).
   - Es lisa por construcción: no puede tener ranuras ni botones, que son más chicos que la jaula.
2. La **posición de cada punto de control se calcula** para que la superficie pase por los puntos medidos del modelo oficial de Meta.
   - Ese modelo es el "plano" más preciso: el paquete de arte, cuya licencia permite representar el producto en la experiencia VR.
   - Su geometría no se usa como malla: solo como instrumento de medida.
3. Datos del ajuste: los paneles del cuerpo muestreados como superficie curva, con Phong y las normales del artista. Se excluye:
   - botones, tiras oscuras de las juntas y piezas internas
   - el bolsillo del gatillo y la pieza del botón de grip
   - **1,2 mm de borde de cada pieza** (ahí se curvan hacia las ranuras)
   - Los pozos de A/B/Meta/stick se reemplazan por una cuádrica ajustada a su corona, en posición y pendiente.
4. **Ajuste**: ICP punto-plano contra la superficie subdividida (nivel 3), más suavidad de la jaula (laplaciano uniforme, `LAM` 0,02) y amortiguación (`MU` 0,002).
   - Mínimos cuadrados dispersos, 12 iteraciones, unos 30 s.
   - Resultado: **desvío 0,017 mm medio, p95 0,044, p99 0,09 mm** contra los datos. El gatillo da lo mismo.
5. **Malla final**: la topología del nivel 1 (quads limpios), con cada vértice en su **posición límite** y la **normal de la superficie límite**, ambas tomadas del nivel 3.
   - Cuerpo: 15.336 triángulos. Gatillo: 2.416.
   - 0 aristas abiertas y 0 caras degeneradas.
6. **Vacío del gatillo**: `qc_carve.py` resta el volumen que barre el gatillo al apretarlo, más holgura.
   - **No hizo falta.** La superficie calculada ya deja un hueco natural detrás del gatillo: holgura mínima 0,75 mm en todo el recorrido (0 a 14°), medida.
   - El script queda por si cambia el gatillo.
7. **Izquierdo = espejo en X.** Contra el izquierdo oficial: mediana **0,18 mm** en sus vértices (lo grande está donde sacamos botones y juntas).

### Pipeline (en orden; todo headless, salida en `VR_Test/Saved/ClaudeScripts/QuestController/`)

| Paso | Script | Qué hace |
|---|---|---|
| 1 | `touchplus_extract.py` (Blender) | Del FBX oficial: paneles triangulados + normales por esquina + componente, agujeros a tapar, contorno de la tapa, hueso del gatillo → `tp_src.npz/json` |
| 2 | `touchplus_sdf.py` (Python) | Superficie cerrada **aproximada** (Poisson por FFT) → `tp_body_R.obj`, `tp_trigger_R.obj`. **Solo sirve de punto de partida de la jaula**; tiene defectos de juntas y no importa |
| 3 | `qc_cage.py` (Blender) | Jaula en quads con QuadriFlow (1.917 cuerpo / 302 gatillo) → `qc_cage_*_R.obj` |
| 4 | `qc_fit.py` (Python) | **El ajuste** → `qc_*_R_final.obj` + normales + máscara de la tapa (y niveles 1-2 para inspección) |
| 5 | `gen_quest_controller3.py` (Blender) | Normales propias, UV0, UV1 `CapMask`, pivote del gatillo en la bisagra, espejo L, FBX + `QuestCtrl_SC.blend` |
| 6 | `render_quest_controller_unlit.py` (Blender) | Vista previa **como en la obra**: sin luces, fondo negro, sombreado del material; lee los FBX (los valida) |

Scripts superados (quedan de referencia; NO usar):
- `gen_quest_controller.py`: remallado por voxeles del oficial. Quedaba deformado.
- `sdf_quest_controller.py` + `gen_quest_controller2.py` + `render_quest_controller.py`: modelado a mano por SDF, "un primo feo".

## Datos para Unreal

- **Marco**: el del Touch Plus oficial, el mismo que `/Game/NeuralCanvas/Mesh/Controller`. En cm, `(x, y, z)` de Blender pasa a `(x, −y, z)` en Unreal.
- **Máscara de la tapa**: `UV1.x`, en mm, es la altura sobre la línea de la tapa del original; > 0 es tapa.
  - La línea NO es plana (rms 1,3 mm), por eso se mide contra la curva real y no contra un plano.
  - El material hace el borde con `smoothstep(±fwidth)`: nítido a cualquier distancia.
- **Gatillo**: origen en su bisagra, que es la cabeza del hueso `right_b_trigger_front` del FBX oficial.

| | Blender R | Unreal R |
|---|---|---|
| Pivote (cm) | (1.565, −2.432, −0.145) | (1.565, 2.432, −0.145) |
| Eje | (0.976, 0.218, −0.008) | (0.976, −0.218, −0.008) |

  - Apretar en Blender es **+14°** sobre ese eje (mano derecha). En Unreal el sentido se verifica en el editor, porque el paso de mano derecha a izquierda invierte el signo.
  - Izquierdo: pivote con x negado; eje (−0.976, 0.218, −0.008) y signo invertido.
- **Material** `M_QuestCtrl_SC` (HLSL en `unreal-vr/scripts/hlsl/QuestCtrlShadePS.hlsl`): unlit, con el sombreado falso de la paleta, borde de luz (fresnel), rodilla suave y `Pressed` 0..1 para el gatillo.
  - Valores de la vista previa aprobada:
    - Luz: Ambient 0,30 · Diffuse 0,55 · Wrap 0,4 · Fill 0,25 · SelfGlow 0,10
    - Colores: Body (0,035, 0,035, 0,038) · Cap (0,78, 0,77, 0,74) · Pressed (1, 0,72, 0,45) con PressedGlow 0,35 (color provisorio)
    - Borde: Rim 0,10 con RimPow 3
  - Instancia del gatillo: `CapBias −100` y `BodyColor` = su color.

## Lo que NO funcionó (para no repetirlo)

La malla oficial son **25 paneles separados** (845 aristas de borde que no se sueldan ni a 0,01 mm) más piezas internas, low-poly (5.609 tris). Su suavidad viene de un mapa de normales. Todo intento de **arreglar esa malla** dejó juntas, escalones o parches:
- Remallado por voxeles + suavizado: deformado.
- Campo de distancia sobre los paneles: las juntas, cuyos bordes se curvan hacia adentro, dejan ranuras. Las bandas cortas fugan y las largas dejan filos.
- Poisson sin datos en huecos grandes: se hunde como una membrana.
- Parches polinómicos sobre el botón de grip: el mango ahí es demasiado curvo.
- Alisado bilaplaciano local: costuras.

La SDF "a mano" con primitivas (cilindro, tubo de Bézier, elipsoide) no se parecía: las proporciones adivinadas no son las del Quest. **Medir y ajustar una superficie lisa a los datos** resolvió todo de una vez.
