# Aparición "luz primero" — cómo nacen (y se van) los objetos de la familia

**Pedido de Beltrán (2026-09-30):**
- *"En general estamos usando el súper aburrido escala de 0 a 1… una animación cul de aparición, como los Transformers… 1,5 segundos hasta tomar la forma. Animación que se utilice en reversa para la salida."*
- Se probaron tres propuestas sobre la paleta: luz primero, ensamblaje y despiece. **Eligió "luz primero"**: *"el primero me gusta, arma algo similar para el timbre, el botón de save y el sensor de breath"*, y después *"arma una para el anillo"*.

Estado: 🟢 aprobada en Blender (paleta, timbre, SAVE MELODY, sensor, anillo de carga) · ⬜ Unreal · ⬜ visor.

## La coreografía (t de 0 a 1 = 1,5 s; la SALIDA es exactamente la misma con t de 1 a 0)
| t | Qué pasa | Cómo |
|---|---|---|
| 0,00–0,05 | Nace una semilla de luz arriba del contorno | trazo: `Head` 0 → 3,2 |
| 0,02–0,30 | La cabeza dibuja el contorno de la ranura en el aire (antihorario visto desde la cara) | trazo: `Sweep` 0 → 1 (ease in-out cúbica); `Head` se apaga entre 0,28 y 0,38 |
| 0,26–0,42 | El círculo cerrado destella suave | trazo: `Glow` × (1 + 0,5·seno) |
| 0,24–0,34 | El cuerpo nace como RENDIJA de luz, de canto a la vista, y se alarga desde el centro | escala sobre el eje X' 0 → 1 (ease out cúbica) |
| 0,30–0,54 | La rendija se abre como un párpado hasta quedar de frente | giro alrededor de X' de θ → 0 (ease in-out cúbica) |
| 0,36–0,56 | Toma espesor | escala sobre la normal 0,05 → 1 |
| 0,30–0,60 | La luz se enfría en hormigón | `Flash` del cuerpo 1 → 0 |
| 0,42–0,56 / 0,46–0,60 | Relevo: se enciende la ranura real y se apaga el trazo | luz `Glow` 0 → reposo · trazo `Glow` → 0 |
| 0,52–0,80 | La pieza móvil ASOMA desde adentro con un clac | traslación en el eje de la cara, `ease_out_back(1,2)`; `Flash` 0,35 → 0 (0,60–0,86) |
| 0,70–0,95 | Luces propias | SAVE: el texto destella (`InkGlow` +0,9·seno) · sensor: la punta se enciende (+1,6·seno) y las ondas suben (`Active` 0 → 1, 0,80–1,00) · anillo: las cavidades se llenan en orden hasta su carga (0,52–0,90, con frente brillante) |
| 0,86–1,00 | La ranura exhala una vez | `Glow` × (1 + 0,25·seno²) |

**El párpado (el único cálculo "inteligente").** Al arrancar se lee la cámara del jugador en el marco de cara del objeto: normal n y pivote en el plano de la ranura.
- `X'` = el "derecha" de la cámara proyectado sobre el plano de la cara. Con eso la rendija queda **horizontal en la vista**.
- `n'` = X' × (ojo − pivote), del lado de n.
- `θ` = ángulo de n a n' alrededor de X'. Con ese giro el plano queda de canto para el ojo.
- La escala va en la base (X', n × X', n): el plano escala **parejo** (X' e Y' con el mismo `sx`), así nace de un punto que, de canto, se ve como una línea que se alarga; y la normal con `sz`. Si solo se escalaba X', la franja a lo largo de Y' se veía corta en perspectiva desde el primer cuadro.

Esta forma sirve desde cualquier ángulo. La cuenta de la paleta (psi = atan2(cx, −cy)) solo andaba con la cámara abajo-adelante: con el anillo la rendija salía en diagonal.

## Por objeto
| Objeto | Trazo (malla) | Plano / pivote | Pieza que asoma | Luces |
|---|---|---|---|---|
| Paleta | anillo en la ranura (`anim_palette_luz.py`) | z = piso de la ranura | cuñas como pétalos, casquete, undo/redo, disco del slider (ver el script) | ranura, slider |
| Timbre | `SM_Bell_Trace_SC` (círculo r 116,5 mm, h 44,1) | cara, +Z | `SM_Bell_Button_SC`: −19 mm → 0 (arranca hundido; el bolsillo destella para taparlo) | `Ring` 0,7 |
| SAVE MELODY | `SM_SaveMelody_Trace_SC` (contorno redondeado, canal, h 15) | cara, +Z | `SM_SaveMelody_Plate_SC`: −12 mm → 0 (arranca bajo el piso del canal) | `Ring` 0,7 + texto |
| Sensor | `SM_BioSensor_Trace_SC` (círculo r 62,2 mm en la boca de la cinta, h −6,1) | cara de la panza, **−Z** | **`SM_BioSensor_Button_SC`** (malla nueva: el botón separado del cuerpo, que ahora tiene una tapa escondida): +17 mm → 0 | `Ring` 1 · `BackRing` 0,9 · `TipLight` 1 · ondas |
| Anillo de carga | **sin trazo** (Beltrán: *"este lo haría sin aro de luz, porque no tiene"*): nace como un punto de luz que se estira en rendija. Tiempos corridos: rendija 0–0,20 · párpado 0,12–0,46 · espesor 0,18–0,48 · enfriado 0,14–0,56 (`Flash` 1,6) · vidrio 0,34–0,50 · llenado 0,40–0,86 | eje **X** (marco de cara (x, y, z) → (z, x, y)); pivote en el plano medio | — | vidrio `Glow` + llenado de las 5 cavidades hasta la carga actual |

Los trazos son cintas planas: UV0.x es la fracción del contorno, desde arriba y antihorario visto desde la cara; UV0.y va de 0 a 1 a lo ancho. Se generan junto a las mallas de cada objeto, en `VR_Test/Saved/ClaudeScripts/<Objeto>/`; el anillo va en la raíz de `ClaudeScripts/`.

## Para Unreal (lo que falta construir)
- **`M_AppearTrace_SC`**: aditivo, unlit, dos caras. Parámetros `Sweep`, `Soft` 0,05, `Head`, `Glow`, `Halo` 0,3.
  - Perfil a lo ancho: `gauss((v−0,5)/0,09) + Halo·gauss((v−0,5)/0,28)`.
  - Encendido: `saturate((Sweep·(1+Soft) − u)/Soft)`.
  - Cabeza: `gauss(dd/0,028)`, con `dd` la distancia envuelta de u al frente.
  - Color: `LIGHT (1, 0,72, 0,45)`.
- **`Flash`** (suma luz cálida) en los materiales de cuerpo y **`Glow`** en los de luz. El anillo necesita además un parámetro de llenado de aparición: cada etapa muestra min(`Charge_j`, `AppearFill − j`).
- **Un componente portable** (`BPC_AppearLuz_SC`) con el reloj y la coreografía de la tabla de arriba:
  - reloj: `Play(entrada/salida)`, 1,5 s, tickea solo mientras anima, y al terminar dispara `OnAppeared` / `OnVanished`;
  - variables por objeto: trazo, cuerpo(s), pieza móvil y cuánto se esconde, eje de cara (Z, −Z o X), altura del pivote, nombres de los parámetros de luz y su valor de reposo.
- ⚠ Quest: solo transformaciones de componentes y escalares de material; nada de fundidos de opacidad en piezas opacas. El trazo es el único aditivo y vive medio segundo.

## Scripts
- `scripts/anim_palette_base.py`: base de la paleta (piezas, sombreado falso y API de poses).
- `scripts/compose_anim.py`: GIF de entrada → reposo → salida, hoja de contacto y control de reposo exacto.
- `scripts/anim_luz_objects.py -- <bell|save|sensor|ring> <dir> [cuadros]`: la coreografía de los cuatro objetos; exporta sus trazos.
- `scripts/anim_palette_luz.py`: la coreografía de la paleta (la aprobada).
