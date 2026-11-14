# Investigación: cómo suena un hang / handpan y cómo sintetizarlo (2026-10-28)

Pedido de Beltrán: *"El sonido no sonaba ni por si acaso a hang pan. Era un sinte más. El hang es metálico, con mucho rango dinámico."*
Se aplica al **sonido 3** de `BP_Harp_SC` (ver su ficha, 15.ª vuelta).

## 1. Lo que dicen las mediciones

### Parciales (los tres "afinados")
- Cada nota tiene **3 parciales afinados en 1 : 2 : 3**: fundamental, octava y la quinta de la octava (Morrison y Rossing 2007; Alon y Murphy 2015).
- **No son exactos.**
  - Nota central G3 de un Hang: 189 / 390 / 593 Hz, o sea **1 : 2,063 : 3,138** (Morrison y Rossing).
  - Handpan medido por Alon: octavas entre ×1,96 y ×1,99, quintas entre ×2,94 y ×2,99.
- **La octava suele ser el parcial más fuerte.** En 4 de las 8 notas de un handpan, el parcial de mayor magnitud es la octava, no la fundamental (Alon, tabla 2).
- **Golpe suave:** se oyen casi solo dos componentes, fundamental y octava (Wessel y otros 2008).

### Lo "metálico": modos altos inarmónicos
- Por encima de los tres afinados hay modos con dos diámetros nodales que **no están afinados**. En la G3: **1418 y 1543 Hz = ×7,50 y ×8,16** (Morrison y Rossing).
- **Golpe fuerte:** aparecen componentes inarmónicos respecto de la fundamental, más batido (Wessel y otros).
- En los steelpans, un golpe más fuerte no solo sube el volumen: **excita componentes nuevos** porque el acero es no lineal (Hansen y Rossing).

### Caída
- **PD60** (tiempo en caer 60 dB), promedio de cuatro handpans: **2,9 s** (rango 0,9 a 5,9 s). Graves 3,2 s, medios 3,0 s, agudos 2,5 s (Alon, tabla 3).
- **Una nota fuerte suena más largo que una suave** (Wessel y otros).
- **Contacto largo del dedo = nota más apagada.** El dedo amortigua (Wessel y otros).

### El batido (la firma del sonido)
- Muchos parciales tienen **modulación de amplitud a 3–9 Hz**. Medido: 3,3 / 8,6 / 3,9 / 3,1 / 3,3 Hz (Alon, tabla 4).
- **Origen:** las **otras notas vibran por simpatía** y sus parciales están **levemente desafinados** respecto de los de la nota tocada. Con las otras notas tapadas con imanes, el batido casi desaparece (Alon).
  - Ejemplo: un parcial de 662 Hz se resintetizó con un segundo oscilador a 665,3 Hz y dio el batido de 3,3 Hz.
- **Simpatía concreta:** la D3 excita la D4 (su octava). En el espectro de la D3 sin tapar, el tercer parcial más fuerte pasa a ser la doble octava (Alon).
- Morrison y Rossing muestran que, a amplitud grande, **se acoplan más notas vecinas**.

### El cuerpo (Helmholtz)
- La cavidad con el agujero de abajo (Gu) es un resonador de Helmholtz. En el Hang aparece un pico a **~85 Hz** (cerca de Fa2).
- Se acopla sobre todo con la **nota central** (Morrison y Rossing; Wessel y otros).

### El ataque
- El sonido tiene dos etapas: un **transitorio de banda ancha** (los primeros ~4–10 ms) y después una caída casi sinusoidal (Alon).
- Alon grabó el transitorio golpeando el acero **entre dos notas**, con todo tapado: 10 ms. Lo **convolucionó** con los parciales sintetizados, y eso sonó mejor que sumarlo.

## 2. Cómo lo sintetizaron los que lo midieron
- **Alon y Murphy (2015):**
  - Síntesis aditiva con senos que caen exponencialmente, más el transitorio convolucionado, más un oscilador extra por parcial para el batido.
  - En la prueba de escucha, lo mejor puntuado fue **4–7 parciales + el batido**. Con el batido, la similitud mediana subió de 5,1 a 6,75 sobre 10.
  - Tampoco llegaron a "indistinguible": ellos mismos dejan el ataque como trabajo futuro.
- **Wessel, Morrison y Rossing (2008, CNMAT):**
  - **Un filtro resonante por componente**, excitado por impulsos, con ganancias y caídas sacadas del análisis.
  - Clave para los redobles: que los filtros **sigan sonando libres** entre golpes. Si se reinician en cada golpe, se pierde la variación de timbre de golpe a golpe. Repetir una muestra tampoco la reproduce.

## 3. Por qué el sonido 3 actual suena a sinte

| Hoy (15.ª vuelta) | Lo medido |
|---|---|
| Batido por proporción: ×1,0016 (≈0,2 Hz en la D3) y ×2,0035 (≈1 Hz). **Demasiado lento: suena a phaser.** | **3–9 Hz**, en Hz y no en proporción, y viene de las notas vecinas |
| `SndChorus[3]` 0,35 | Un hang no tiene chorus: el "brillo que se mueve" es el batido. **El chorus es justo lo que lo vuelve sinte** |
| Cada golpe reinicia la envolvente (Seno × AD) | El acero sigue vibrando y el golpe nuevo le suma energía |
| Un solo modo inarmónico (×4,37, 0,08) | Modos ×7,5 y ×8,2 que aparecen con el golpe fuerte |
| La dinámica es volumen + paso bajo (~20 dB) | La dinámica es **timbre**: suave = fundamental + octava, corta; fuerte = inarmónicos, notas vecinas, más larga |
| Fundamental siempre la más fuerte | La octava muchas veces igual o más fuerte |
| Parciales exactos (×2, ×3) | Levemente fuera: ×1,96–2,06 y ×2,94–3,14 |
| Golpe = ruido blanco de 8 ms | "Knock" del acero, de ~10 ms |
| Sin cuerpo | ~85 Hz en la nota central |

## 4. Caminos

**A. Corregir la síntesis modal (recomendado primero, casi todo es datos de la receta):**
1. **Batido en Hz:** segundo oscilador de cada parcial afinado a **+3 a +8 Hz**, distinto por nota y por parcial, con amplitud 0,3–0,6. Necesita una ficha nueva de frecuencia "en Hz".
2. **Simpatía:** al tocar un pad, sumar suave (×0,1–0,3, ataque de ~50–150 ms) los parciales de los pads que coinciden. En Re Kurd:
   - La D3 despierta la D4 (294) y la La4 (440).
   - La La3 despierta la La4.
   - La D4 despierta la La4 (880 = su quinta de octava).
   - Esos parciales van desafinados unos Hz, así sale el batido real.
3. **Inarmónicos con la fuerza:** ×7,5 y ×8,2 (más uno ×5,4 opcional), caída 0,3–0,8 s, amplitud ∝ **vel³**. Suave = casi nada; fuerte = metal.
4. **Caída según fuerza:** T60 de la fundamental ~2,5 s suave → ~4 s fuerte; agudos más cortos.
5. **Pesos:** octava ≈ fundamental (0,8–1,0); quinta de octava 0,3. Desafinar levemente (×2,01 y ×2,99, por ejemplo).
6. **Knock:** ruido filtrado en banda (~1–3 kHz), más un "tump" grave corto (~150 Hz, 15 ms), con nivel según fuerza.
7. **Cuerpo:** en la D3, un seno a ~85 Hz con caída de ~1 s y amplitud según fuerza.
8. **Chorus del sonido 3 a 0** y la reverb como está.
9. **No reiniciar:** que el golpe sobre una nota que suena sume, en vez de arrancar la envolvente de cero. Hay que ver cómo se comporta el AD Envelope de MetaSounds al redisparar.

**B. Muestras reales:** one-shots de un handpan en Re Kurd, con 2–3 capas de fuerza, reproducidos con Wave Player.
- **A favor:** lo más realista y lo más barato en CPU del Quest.
- **En contra:** hay que conseguirlas con licencia que sirva para una obra expuesta (CC0 o compradas) o grabarlas.
- **Contra lo que mide Wessel:** repetir la misma muestra no reproduce la variación de un redoble.

**C. Banco de filtros resonantes** excitado por el knock: lo más fiel según Wessel, pero no está claro que el Biquad de MetaSounds acepte el Q que hace falta (Q ≈ 200 para 3 s a 150 Hz). Hay que probarlo.

**Híbrido posible:** A con un knock **grabado** (10 ms de golpe sobre acero) como excitación, que es lo que hizo Alon.

## 5. Lo que se armó (17.ª vuelta, mismo día)
Al final fue el **camino C** (resonadores), que resuelve de una vez la caída exponencial, el redoble que suma energía y la fuerza aplicada solo al golpe. Lleva parte de A: gemelas para el batido, inarmónicos con la fuerza, cuerpo, casco y chorus en 0. La receta y el código están en la ficha de `BP_Harp_SC` (17.ª vuelta). El script que escribe la receta es `.claude/skills/unreal-vr/scripts/harp/recipe_snd3_reson.py`.

Medido en `.wav` (Simulate, mano de prueba):

| | Medido | Referencia |
|---|---|---|
| Parciales | ×1,997 · ×2,985 · ×7,50 · ×8,16 | 1 : 1,96–2,06 : 2,94–3,14 · ×7,50 / ×8,16 |
| T60 de la fundamental | 3,0 s (mediana de 7 notas) | 2,9 s promedio (0,9–5,9) |
| Batido de la octava | 2,7 Hz (Re3) a 8,3 Hz (La4) | 3–9 Hz |
| Suave → pleno (mano de prueba) | +16 dB de nivel; quinta −13 → −8 dB; ×7,5 −25 → −17 dB | golpe fuerte = más componentes inarmónicos |

Perillas para afinar de oído (4-Hang): `HangMetal`, `HangShimmer`, `HangDecay`, `HangT60Tilt`, `HangBodyOther`. Falta el juicio de Beltrán en el visor.

## Fuentes
- Alon, E. y Murphy, D. T. (2015). *Analysis and Resynthesis of the Handpan Sound*. SMC 2015. https://zenodo.org/records/851153
- Alon, E. (2015). Tesis de MSc, University of York. https://etheses.whiterose.ac.uk/12260/
- Morrison, A. y Rossing, T. D. (2007). *Modes of Vibration and Sound Radiation from the HANG*. Archives of Acoustics 32(3). https://acoustics.ippt.pan.pl/index.php/aa/article/download/709/627
- Wessel, D., Morrison, A. y Rossing, T. D. (2008). *Sound of the Hang* (ASA). https://acoustics.org/pressroom/httpdocs/155th/wessel.htm
- Rossing, T. D. y otros. *The extraordinary sound of the hang*. Physics Today. https://physicstoday.aip.org/quick-study/the-extraordinary-sound-of-the-hang
- Hansen, U. y Rossing, T. D. *The Caribbean steelpan and some offsprings*. https://www.hangblog.org/pdf/hansen_rossing_the-caribbean-steelpan-and-some-offsprings.pdf
- Monteil, Touzé y Thomas (2015). *Identification of mode couplings in nonlinear vibrations of the steelpan*. https://hal.archives-ouvertes.fr/hal-01084240
