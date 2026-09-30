# Sensor de respiración y latido: `SM_BioSensor_SC` + `SM_BioSensorWaves_SC`

**Pedido de Beltrán (2026-09-29):**
- Rehacer "el controller que se usa en breath y heart": su `/Game/BreathR|L`, cuyo fuente `ControlV2.fbx` ya no está en disco.
- Con bevel, normales bien hechas y un material como el de la paleta, con variables por parte.
- Un **aro luminoso al centro de la cara que va hacia la panza**.
- **Reemplaza al mando** en Entering (respiración) y Recognizing (latido).
- Visible sin luces: algo de emisión y sombreado 3D.
- **Ondas** que salen de la cara hacia la panza: anillos suaves que indican hacia dónde apuntar el sensor.

Estado: 🟡 v5 según su boceto (ver abajo), esperando OK · ⬜ Unreal · ⬜ BP · ⬜ rigs.

## Medido del sensor de Beltrán (en Unreal, 2026-09-29)

- `BreathR`: 15.356 tris, 1 slot.
- Caja: x −0,79..4,16 · y ±6,55 · z −5,62..7,48 cm → **disco Ø 13,1 cm**, eje X, espesor total ~5 cm.
- Forma: plato fino (~8 mm), **domo del lado de la palma**, **anillo en relieve con hueco** al centro de la otra cara y una ranura concéntrica cerca del borde.
- En el rig de respiración, respecto de la mano: Controller `(2.791, 9.5, −4.296)` · Breath `(2.791, 9.5, −3.5)`, rotación `(P−90, Y−10)`.
- La cara plana mira hacia la palma y se apoya en la panza.

## Modelo (`scripts/gen_bio_sensor.py`, headless)

- **Perfil que gira** (eje Z; la cara de contacto mira a −Z):
  - plato R 65,5 · espesor 8, cantos con filete 3,2;
  - domo de la palma R 44 × 30, con perfil "piedra" (`DOME_P` 0,62) y filete cóncavo 7;
  - anillo R 12,5..21 que asoma 9 mm hacia la panza, filetes 2,6;
  - lente oscuro en el hueco;
  - ranura en R 58.
- **Normales exactas**: cada vértice sale de un punto del perfil y lleva su normal girada.
- 🔴 El abanico del polo de ARRANQUE va en orden inverso al de los quads (`A0, B[j2], B[j]`). Si no, queda un anillo de caras dadas vuelta.
- Filetes con pasos proporcionales al radio. **11.088 tris**, cerrado, 0 degeneradas.
- **Slots**: 0 Body (canto, dorso, domo) · 1 Face (cara de contacto) · 2 Lens · 3 Ring (el aro luminoso).
- **Ondas**: `SM_BioSensorWaves_SC`, un cono abierto de 18 cm desde el anillo (R 17 → 62 mm), con V a lo largo.
  - El material dibuja bandas gaussianas que viajan hacia afuera y se apagan con la distancia.
  - Material animado y no Niagara: más barato en Quest, se ve en el viewport, parámetros simples.
  - El rig las apagaría con `bZone` (sensor en posición) y las prendería al buscar.

## Vista previa

`scripts/render_bio_sensor_unlit.py`: mismo sombreado falso de la paleta, fondo negro, sin luces. Vistas: dorso, cara, lado con ondas y desde el usuario.

## v2-v5 según el BOCETO de Beltrán (2026-09-29/30)

Beltrán mandó un boceto: *"más como la paleta: un borde, un anillo como hendidura que es una cinta de luz, un plano y un botón que sobresale; atrás una media esfera para agarrarlo; el anterior era una nave espacial en sombrero"*.

1. **Medición del boceto**: workflow `medir-boceto-sensor` con 3 lecturas independientes en píxeles, combinadas por mediana → las fracciones del diámetro en `K`. Las 3 coincidieron al píxel en casi todo.
2. **Grosor**. *"Está muy grueso; con 18-20 cm de diámetro, no más de 5 de profundidad"*.
   - Se leyó como: todo el objeto ≤ 5 cm.
   - Quedó **D 190 mm**, con las alturas achicadas (`body_t` 0,116, `rim_up` y `groove_d` 0,032).
   - Los radiales siguen siendo los del boceto.
3. **Media esfera**: *"debe tener otro material"* → slot propio `Grip`. En la vista previa es grafito, como el mando negro. Mide 6 × 2,2 cm, para que se lea como media esfera y no como disco.
4. **Centro**: *"la parte central y ese sacado, que salgan más: que se sienta que hay que incrustarla en el estómago"*.
   - Loma central (`plat_h` 0,047 D, con pendiente 0 en la base del botón).
   - Botón (`btn_h` 0,08 D) → el centro queda ~2 cm por delante del borde.
   - Total: 6,2 cm (lo que sale es el botón; el cuerpo sigue siendo delgado).
5. **Revisión crítica** (workflow `critica-sensor-vs-boceto`: 3 lentes + un verificador que intenta refutar cada ajuste). Sobrevivieron 5 de 16:
   - **aros al revés**: con `v^0,7` se separaban. Ahora `u = v^2`: frenan y se juntan como en el boceto. El ancho se compensa con du/dv para que no nazcan como una manga gruesa, y el fade es `(1-v)^1` → HLSL v2 con `Squeeze`.
   - **cinta de luz**: pintaba también la pared del labio (se veía el doble de ancha). El punto `(go, 0, "Body")` deja la luz solo en la hendidura.
   - **gráfico del corte**: dibujaba los aros desde `wave_start`, pero la malla arranca en el plano. Se corrigió y se borró `wave_start`.
   - Refutados: faldón de la media esfera (el filete real es más chico), botón como "baliza", contraste de la cinta, pose de los renders, grosor de los aros.
- **Herramientas**:
  - `scripts/plot_bio_sensor_section.py` dibuja el CORTE real (perfil del generador, cara de la panza arriba) para compararlo lado a lado con el boceto.
  - `render_bio_sensor_unlit.py` pone el corte con la panza arriba.
- Estado v5: D 190, centro saliente, grip grafito.
6. **v6 (2026-09-30, Beltrán)**:
   - *"Mover todo el centro hacia afuera: el vértice que baja hacia el aro de luz, a la altura del borde"*. La loma arranca en `rim_up`, la hendidura del frente queda de 12 mm y la luz sigue solo en su fondo.
   - *"Un aro de luz atrás, en hendidura, alrededor de la media esfera"* → slot `BackRing`: 4 mm de separación, 7 de ancho y 5 de fondo.
   - *"Un círculo de luz al centro de la punta"* → slot `TipLight`: disco hundido 1 mm, de 0,62 del radio del tope.
   - Los aros salen de la boca de la hendidura.
   - **7 slots**: Body, Face, Button, Ring, Grip, BackRing, TipLight.
   - 13.104 tris; total ~6,8 cm (lo que suma es el centro saliente).
   - Estado: 🟢 v6 APROBADA ("Super") · ⬜ Unreal (turno pedido).
7. **Aros sin pulso (2026-09-30, Beltrán)**: *"no deben nacer como pulso; siempre constante: desde opacidad 0 hasta tomar el color y luego desvanecerse"*.
   - Antes: `saturate(v·25)` los hacía nacer al máximo pegados a la cinta, como un destello.
   - Ahora, envolvente suave: `smoothstep(0, FadeIn 0,35, v) · (1 − smoothstep(FadeOut 0,45, 1, v))` → HLSL v3.
   - Vista previa animada: `render_bio_sensor_unlit.py -- <dir> <salida> 0 <cuadros>` renderiza un ciclo, que después se arma como GIF.
