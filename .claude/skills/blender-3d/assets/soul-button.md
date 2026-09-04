# SM_Button — el botón VR (base + cap clickeable)

## Propósito
Botón físico de la obra (referencia: render beige tipo almohadón con ranura de luz). **Dos mallas separadas** porque el centro es clickeable en VR y se mueve:
- **`SM_Button_Base`** — disco inferior + aro superior con la ranura de luz entre ambos y el piso del hueco. Estático.
- **`SM_Button_Cap`** — el puck central con grabado concéntrico. Se anima hacia abajo al presionar. Emparentado a la base, origen en su centro-base.

## Estado
🟢 **Modelado y validado contra la referencia por Beltrán en viewport (2026-09-01).** Sin exportar aún; el `.blend` quedó SIN guardar (escena nueva del proyecto abierto — guarda Beltrán).

## Parámetros (las perillas)
| Perilla | Valor | Nota |
|---|---|---|
| Diámetro total | **0.30 m** | pedido explícito de Beltrán |
| Altura total (con cap) | 0.093 m | ~0.31 × diámetro, medido de la referencia |
| Disco inferior / ranura / aro | 33 / 8.5 / 28 mm | 🔴 el disco es MÁS ALTO que el aro (medido en px de la foto lateral) |
| Cap: radio / sobresale del aro | 0.088 m / 27 mm | pared vertical (zona knurl) visible sobre el aro |
| Cap: posición de reposo | z = 0.046 | flota 6 mm sobre el piso del hueco (z=0.040) → recorrido de press ~6 mm antes de intersecar (la intersección queda oculta, no es problema) |
| Revolución | 56 segmentos | 2.800 + 2.128 tris = ~4.9k el conjunto (prop protagonista) |
| Grabado concéntrico | 3 anillos, r 0.010–0.028 | ~27% del cap, como la foto |
| Tapa del cap | **cóncava** (hendidura ~2 mm al centro) con rim definido en r 0.070 | corrección de Beltrán: no es domo |

## Lenguaje de forma (lección de Beltrán, 2026-09-01)
**"Son más esquinas con bevel que un toroide"** — paredes exteriores VERTICALES con filetes definidos en los cantos; la ranura con paredes netas; hombro redondeado generoso solo en el lomo del aro. La primera pasada (perfiles toroidales inflados) se descartó por eso.

**Y los cantos NO son todos iguales**: los "mecánicos" van duros (bocas de la ranura, borde interno del aro, rim del cap) y los almohadones blandos (canto inferior de la base, hombros). La dureza se controla con la densidad de puntos del perfil + el umbral del auto smooth (50°).

**La ranura NO es un recorte con ganchos** (corrección de Beltrán, 2ª pasada): las dos caras que miran a la luz son **planos rectos que se afinan hasta un labio delgado**, con boca de ~9.6 mm. Y las paredes exteriores **no son verticales**: la **panza de cada almohadón queda PEGADA a la ranura** y de ahí una sola curva continua — larga hacia el apoyo en el disco, sobre el hombro hasta el lomo en el aro. Las dos mallas se conectan por una columna interior en r=0.083.

**Hallazgos de la 3ª pasada** (medidos en px sobre la lateral de la referencia):
- **El aro SOBRESALE del disco**: aro R=0.150 con labio en r=0.1465; disco R=0.144 con labio en r=0.140.
- **El cap es un ALMOHADÓN, no un cilindro con tapa**: pared inclinada hacia adentro, corona continua hasta el plato.
- El disco se afina fuerte hacia el apoyo: contacto en r=0.095.

**Hallazgo de la 6ª pasada — la ranura de luz corta casi AL RAS** (corrección de Beltrán: "la luz quedó de diámetro mucho menor"): la boca de la ranura llega al **97% del diámetro** — labio del disco en r=0.1455 (disco R=0.147), labio del aro en r=0.148 (aro R=0.150). El disco es apenas 3 mm más angosto que el aro, no 6.

**Hallazgo de la 7ª pasada — 🔴 la ranura es POCO PROFUNDA, y eso define cómo se LEE**: con la ranura como cañón profundo (pared interior en r=0.083, la columna), de frente la franja abierta solo se veía en el 55% del ancho — la vista se escapa hacia el interior y los labios la pellizcan. La referencia llena el ancho porque **la superficie emisora está cerca de la boca**: canal de ~1 cm con la **pared de luz en r=0.136** → la franja se lee en el 93.5% del ancho, y esa pared es la que lleva el emisivo en Unreal. Regla general: la lectura de una ranura iluminada la manda el radio de su pared interior, no el de sus labios.

**Hallazgos de la 4ª pasada — las PROPORCIONES anti-Michelin** (medidas en px sobre la vista superior; "se ve como hamburguesa" = el diagnóstico de Beltrán):
- 🔴 **El aro es una banda ANGOSTA: ~38 mm de ancho** (borde interno en r≈0.110, exterior 0.150). Con el aro de 57 mm el objeto entero se leía como ruedas apiladas.
- 🔴 **El cap es GRANDE: r≈0.0965 (63% del diámetro total)** — domina la composición.
- **El grabado concéntrico: ~62 mm de diámetro** (motivo en r hasta 0.031), no 56.
- Foso de luz cap-aro: r 0.0965 → 0.110.

**Método definitivo (pedido de Beltrán: "objeto de diseño, geometría perfectamente diseñada")**: los perfiles se generan con **segmentos Bézier cúbicos encadenados con continuidad tangente** (función `bez()` en el script), muestreados a 8 puntos por segmento; los únicos quiebres G0 son los cantos diseñados (labios de la ranura, rim del plato). Nada de puntos a ojo.

⚠ Con Bézier + 56 segmentos el conjunto quedó en **~11.4k tris** — alto para Quest. Cuando Beltrán apruebe la forma: bajar muestreo/segmentos o decimar al exportar (~5-6k objetivo). La forma primero, la optimización después.

## Construcción
Perfiles de revolución `(r, z)` con `bmesh.ops.spin` (56 pasos, `use_merge`), `remove_doubles`, `recalc_face_normals`, smooth por ángulo 50°. **Los perfiles exactos están en el historial del script** — para retocar: editar la lista de puntos y regenerar la malla con el mismo nombre (borrar objeto+mesh viejos primero). El knurl del cap y la tela van por MATERIAL en Unreal, no por polígonos.

## Materiales (slots placeholder — los reales van en Unreal)
- `M_Button_Body` (slot 0 en ambas) — beige.
- `M_Button_Glow` (slot 1 de la base) — asignado por centro de cara a la ranura + piso del hueco (`0.032 < z < 0.0435, r < 0.132`). En Unreal: emisivo cálido.

## Pendientes
- [ ] Guardar el `.blend` (Beltrán) y decidir su carpeta en `Modelos 3D\`.
- [ ] UVs (canal 0 + canal 1 lightmap) — antes del export.
- [ ] Export FBX con el checklist de `references/export-unreal.md` (dos mallas → dos Static Mesh).
- [ ] Materiales reales en Unreal (knurl/tela + emisivo de la ranura).

## Log
- **2026-09-01** — modelado inicial en 4 iteraciones del bucle (toroide → cantos con bevel → alturas medidas de la foto → grabado más chico). Validación por screenshots de viewport en Front ortho y 3/4.
