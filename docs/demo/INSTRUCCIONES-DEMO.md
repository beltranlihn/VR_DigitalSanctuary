# Instrucciones de la demo — ENTERING y SURROUNDING (Barcelona Design Week, 2026-10-21)

Textos finales del panel de instrucciones (widget con páginas) de las dos experiencias de la demo. **Todo lo que está en bloque de cita es texto in-headset, en inglés, listo para pegar.** El resto del documento es contexto en español.

- Se avanza **apuntando con el láser y apretando el gatillo**; la última página invita a empezar con ese mismo gesto.
- Cada página tiene **≤ 30 palabras contando el pie** (el pie es la ayuda fija de "cómo avanzar"; en la última página no hay pie porque la invitación va dentro del texto). Conteo verificado con script (§5).
- Tono: el de Alma en el guion V5 (*"lento, claro, profundo"*), segunda persona, frases cortas. Nada de números de ciclos ni de segundos: los trackers y las docs se contradicen (4 vs 5 ciclos) y la duración real la manda el Director.
- "Gatillo" se explica **una sola vez por experiencia**, en el pie de la página 1 (*"under your index finger"*); después, solo *trigger*.
- Sin mano derecha/izquierda: dicen *"your other hand"*, así sirven para diestros y zurdos.

---

## 1. ENTERING — respiración (azul) · 3 páginas

| Pág | Texto (pegar) | Pie (ayuda fija) | Ícono / imagen sugerida |
|---|---|---|---|
| 1 | > Settle in. For the next few minutes, your breath leads. Light, air and space will move with you. | > Point and press the trigger under your index finger to continue. | Una esfera de luz azul que se infla y se desinfla despacio (la del metaball). |
| 2 | > Rest the sensor just below your ribs, flat side against your belly. Stay still and breathe slowly. Feel it rise and fall with you. | > Press the trigger to continue. | Silueta de perfil, sentada, con el cilindro apoyado de plano bajo las costillas; flechita suave arriba/abajo (es lo que hace el fantasma `GHOST_BREATH`). |
| 3 | > Soft rings of light will guide your rhythm. There is nothing to get right — just breathe. Point at this panel and press the trigger to begin. | — | Aros concéntricos luminosos, uno abriéndose (los aros del pacer). |

### Variante corta (2 páginas)

| Pág | Texto (pegar) | Pie |
|---|---|---|
| 1 | > Your breath leads here. Rest the sensor below your ribs, flat side against your belly, and breathe slowly. | > Point and press the trigger under your index finger to continue. |
| 2 | > Soft rings of light will guide your rhythm. Point at this panel and press the trigger to begin. | — |

---

## 2. SURROUNDING — dibujo 3D (verde) · 3 páginas

| Pág | Texto (pegar) | Pie (ayuda fija) | Ícono / imagen sugerida |
|---|---|---|---|
| 1 | > The air around you is your canvas. For the next few minutes, draw what you carry inside — with light. | > Point and press the trigger under your index finger to continue. | Un trazo de luz curvo suspendido en la oscuridad (verde/ámbar). |
| 2 | > Your brush is the glowing tip of your controller. Touch a color or brush on the palette floating at your other hand to choose it. | > Press the trigger to continue. | Mando con la punta brillante tocando una tecla de la paleta circular (la paleta de hormigón con 4 colores + 4 pinceles). |
| 3 | > Hold the trigger and move your hand to draw — the harder you press, the bolder the line. Point at this panel and press the trigger to begin. | — | Mano con el gatillo apretado y un trazo que engrosa. |

### Variante corta (2 páginas)

| Pág | Texto (pegar) | Pie |
|---|---|---|
| 1 | > The air is your canvas. Touch a color on the palette with the glowing tip of your controller. | > Point and press the trigger under your index finger to continue. |
| 2 | > Hold the trigger and move your hand to draw. Point at this panel and press the trigger to begin. | — |

### Línea opcional (solo si la tinta cierra la experiencia)

Si el Director usa el medidor de tinta (`InkMeters`) para cerrar el dibujo, se puede sumar a la **página 2** como una línea más (o a una página extra):

> The green arc on the palette shows your ink. When it runs out, your drawing is saved.

Si la demo se corta por reloj en vez de por tinta, **no usarla**: avisaría de un final que no es el real.

---

## 3. Notas para quien pega los textos (Director)

1. **"Sensor" vs "controller" en ENTERING.** Los textos aprobados de la obra (VO_11, fantasma `GHOST_BREATH`, panel 2026-08-24) dicen *sensor*, y en Entering el mando se convierte en sensor (`ToSensor`, +1,5 s tras `StageIntro`). Si el panel aparece **antes** de esa transformación, la persona todavía ve un mando: cambiar *"Rest the sensor"* por *"Rest the controller"* en las páginas 2 de ENTERING (texto y variante). Todo lo demás queda igual.
2. **La paleta tiene que estar visible mientras se lee SURROUNDING 2.** La paleta nace con un retardo de `AppearDelay` 3 s tras activarse (`BP_DrawPalette_SC.md` v6b). Si el panel se lee antes de que aparezca, *"the palette floating at your other hand"* no tiene referente: o se muestra el panel después de ese retardo, o se baja `AppearDelay`.
3. **El gatillo de "Begin" y el primer trazo son el mismo botón.** Conviene que el gesto que cierra el panel no deje un trazo en el aire (esperar a soltar el gatillo antes de habilitar el dibujo, o un par de décimas de gracia).
4. **Duración.** Los textos dicen *"the next few minutes"* a propósito (más contemplativo). Si se prefiere fijar la expectativa en la feria: *"For the next three minutes"* funciona en ambos (ENTERING 1 y SURROUNDING 1) sin cambiar el conteo en más de una palabra.
5. **Paleta: "color", no "rueda".** El guion V5 todavía habla de "rueda de color", pero la paleta vigente (`BP_DrawPalette_SC` integrada y cerrada por Beltrán el 2026-09-30) tiene **4 teclas de color + 4 pinceles + slider de grosor + undo/redo**. El texto dice *"a color or brush"*, que vale para cualquiera de las dos.
6. **Lo que NO se menciona a propósito:** número de ciclos del pacer (4 vs 5 según el doc), el slider de grosor y el undo (la paleta los muestra con íconos; si se quiere, línea opcional: *"Slide the thickness, or undo a stroke, the same way."*), el vaivén de los trazos, la zona de la paleta donde no se puede empezar a dibujar, y el disco/mesa azul translúcido frente a la persona (`BP_TBTable`), que es el ancla del dibujo guardado y no una superficie para dibujar.
7. **Zurdos:** los textos son neutros. La paleta espejada de Draw (`MaskFlip`) sigue sin probarse en visor.

---

## 4. Gestos descritos y de dónde salen

Rutas relativas a la raíz del repo. `BP_*.md` = trackers en `.claude/skills/unreal-vr/blueprints/`.

### ENTERING

| Gesto / hecho que dice el texto | Confirmado en |
|---|---|
| La respiración se lee del **mando** apoyado en el cuerpo, no de un sensor externo (*"la respiración viene del mando, no del BioHub"*) | `docs/MECANICAS-PORTABLES.md` §4.7 ("Lo que sigue valiendo…") · `docs/OBRA-SOUL-CHARGER.md` (tabla de etapas: "Respiración con el mando en el estómago") |
| En Entering el mando se vuelve el **sensor** (cilindro) en la mano | `BP_UserTool_SC.md` (tabla "Quién llama qué", `ToSensor`) · `docs/GUION-V5-2026-09-29.md` §7.1 R4 |
| Apoyarlo **bajo las costillas, cara plana contra la panza**; al revés o hacia el frente no cuenta | `BP_BreathRig_SC.md` ("El sensor tiene que APUNTAR al estómago", validado en visor 2026-09-27) · GUION V5 §7.1, `VO_11h` *"Just below your ribs… flat side toward you."* |
| **Quedarse quieto** y respirar lento | `BP_BreathRig_SC.md` (zona geométrica + quietud + `FacingOK`; "la mecánica es posición + quietud + háptica") |
| **No hay botones** durante la respiración | `BP_BreathRig_SC.md` ("sin IMC propio… no hay botones") |
| "Sentir cómo sube y baja contigo" | GUION V5 §7.1 `VO_11`: *"Feel how it rises and falls with you."* |
| La luz, el aire y el espacio **se mueven con la respiración** | GUION V5 §7.1 "Qué modula qué" · `VO_11b` · `docs/OBRA-SOUL-CHARGER.md` ("Entering: estático, y respira la sala entera") |
| **Aros de luz** que guían el ritmo; la voz no cuenta | GUION V5 §7.1 R5 ("cuentan los aros del pacer") · `docs/OBRA-SOUL-CHARGER.md` (§Entering: la voz no cuenta en voz alta) |
| "Nada que acertar" (tono; no hay fallo posible) | `docs/OBRA-SOUL-CHARGER.md` ("Nadie falla, nadie se traba") |
| Apuntar al panel + gatillo para avanzar y empezar | Encargo de la sesión Director; estilo y largo previos aprobados en `BP_InstructionsPanel_SC.md` §2026-08-24 (Entering) y §2026-08-26 (Attracting: *"Point your beam… hold the trigger"*) |

### SURROUNDING

| Gesto / hecho que dice el texto | Confirmado en |
|---|---|
| El usuario dibuja **en el aire, en 3D**, con luz (trazos libres en el volumen; el disco/mesa translúcido frente a él es solo el ancla del dibujo guardado, el trazo no se apoya en él) | `CLAUDE.md` §1 ("dibujo 3D") · `BP_TBStroke.md` §5m ("LA MESA DE DIBUJO": *"el dibujo no traza"* sobre la mesa; es el ancla al guardar) · GUION V5 `VO_31` *"Use this space as a canvas"* |
| La **punta brillante** del mando es el pincel | `BP_TBStroke.md` §5ad ("el punto frente al control… más brillante", `TipGain`/`TipLift`) · GUION V5 §7.5 R4 |
| La **paleta flota en la otra mano** | `BP_TBStroke.md` §5u/§5w (`ArtAnchor` hijo del grip de la mano de la paleta) · GUION V5 §7.5 R4 |
| **Se elige tocando con la punta**, sin gatillo (4 colores, 4 pinceles; también grosor y undo/redo) | `BP_TBStroke.md` §5u ("por proximidad, sin gatillo") · `BP_DrawPalette_SC.md` (componentes `Color0..3`, `Brush0..3`, `Slider`, `Undo/Redo`) · GUION V5 `VO_32d` *"Bring your brush close to a color on your other hand to choose it…"* |
| **Mantener el gatillo y mover la mano** para dibujar | GUION V5 `VO_32d` (*"…then hold the trigger and move to draw"*) y §7.5 ("Gatillo + presión") · `BP_TBStroke.md` (el gatillo decide si el trazo vive) |
| **Más presión, trazo más grueso** | `BP_TBStroke.md` §5ad (gatillo analógico `IA_TB_Pressure_R/L`) y nota del pincel `TaperedMarker` ("su ancho es `BrushSize * presión`") · GUION V5 §7.5 (`HAP_DRAW_HUM` proporcional a la presión) |
| (Opcional) **Arco verde de tinta**; al acabarse, se guarda el dibujo | `BP_TBStroke.md` §5ad (TINTA: `InkMeters` 30 m → `SaveSketch`) · `BP_DrawPalette_SC.md` v5 (medidor en el arco libre) |
| Apuntar al panel + gatillo para avanzar y empezar | Encargo de la sesión Director (ver Entering) |

---

## 5. Conteo de palabras (cuerpo + pie, sin contar la raya "—")

| Página | Cuerpo | Pie | Total |
|---|---|---|---|
| ENTERING 1 | 18 | 11 | 29 |
| ENTERING 2 | 24 | 5 | 29 |
| ENTERING 3 | 26 | — | 26 |
| ENTERING corta 1 / 2 | 18 / 18 | 11 / — | 29 / 18 |
| SURROUNDING 1 | 19 | 11 | 30 |
| SURROUNDING 2 | 25 | 5 | 30 |
| SURROUNDING 3 | 27 | — | 27 |
| SURROUNDING corta 1 / 2 | 18 / 19 | 11 / — | 29 / 19 |
| Línea opcional de tinta | 17 | — | 17 |

No se probó en visor: son textos, no código. Lo que sí queda para el Director es mirar un par de páginas a ~1,5 m para confirmar que el tamaño de letra aguanta las 30 palabras.
