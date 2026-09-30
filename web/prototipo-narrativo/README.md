# Prototipo narrativo web (Soul Charger)

La obra completa (guion V5) como línea de tiempo editable en el navegador. Se publica como Artifact privado de Beltrán:
https://claude.ai/artifact/1BGkcExUptjr3U9Snjy1xd — la sesión **Narrativa** es la dueña de estos archivos.

| Archivo | Qué es |
|---|---|
| `index.html` | La página: interfaz, estilos, paneles. |
| `world.js` | El mundo 3D (three.js r128): escena, objetos, materiales, sonidos de marcador, **modelos reales**. |
| `timeline.js` | El motor de la línea de tiempo y el editor (clips, anclas, esperas, locators, audio, estética, guardado). |
| `guion.js` | El guion como datos: actos → momentos → clips anclados. **No renombrar keys de clips o momentos**: son las llaves de los ajustes que Beltrán guarda. |
| `modelos/*.glb` + `*.glb.json` | Los modelos reales de la obra, exportados de sus `.blend`. Se publica el `.glb.json` (el GLB en base64): los artifacts no sirven `.glb`. |

Lo que Beltrán ajusta (tiempos, textos, locators, estética) y los audios viven en la base del Artifact
(`timeline/main`, `audio/<ID>`), no en estos archivos.

## 🎬 Ensayo de etapa (2026-09-30)
Cada nivel de test tiene un `BP_StageRunner_SC` (TestOnly + TOUR) que corre su etapa como la Obra, y cuatro TargetPoints `sc<K>_*` que Beltrán mueve a mano. La Obra los lee al arrancar (`ReadRunners`, antes de descartar los TestOnly). Para pasar a la web lo que se movió en Unreal: `ensayo_export.py` (execute_tool_script) → `python gen_ensayo_js.py` → publicar. Al revés (web → Unreal): cambiar el valor de la instancia del runner o del TargetPoint en su nivel de test y volver a exportar.

## 🔴 El prototipo sigue a Unreal
Si en Unreal cambia un **mesh** o una **interacción** que aparece en la obra, el prototipo se actualiza igual.

**Sesiones que modelan o cambian mecánicas:** al terminar, avisen a **Narrativa** (SendMessage) con:
1. el asset (`SM_...`) y la ruta del `.blend` (o del FBX);
2. qué objeto de la obra es y cualquier cambio de escala, pivote o materiales (nombres de slot);
3. si cambió la interacción: qué hace ahora el usuario y qué responde (en una o dos líneas).

**Narrativa**, para integrar un mesh:
```
blender -b <archivo.blend> --python .claude/skills/blender-3d/scripts/export_glb_web.py -- web/prototipo-narrativo/modelos/<SM_...>.glb [objetos]
```
El script no modifica el `.blend` y deja el GLB en `modelos/`; en `world.js` cada objeto tiene su `install…()`
(ver `installRing`), con el provisorio de respaldo si el GLB no carga. Después: recorrer la obra con `SC.seek`,
revisar `renderer.info.programs` sin diagnostics, y publicar.

## Modelos integrados
| Objeto | Asset | Estado |
|---|---|---|
| Anillo contenedor | `SM_ChargeRing_SC` | ✅ 2026-09-29 · mismo contrato de carga que en Unreal (U = etapa + t) |
| Paleta de dibujo | `SM_DrawPalette_*_SC` (`DrawPalette/SM_DrawPalette_SC.blend`) | ✅ 2026-09-29 · en la mano izquierda a escala 0,6; todo por proximidad (mouse encima): 4 colores, 4 pinceles, casquete = color, deshacer/rehacer al 65 % pegados al borde, slider en arco (grosor + tamaño del disco). Ángulos de BP_DrawPalette_SC.md. Sin íconos todavía |
| Mando (sensor) | `SM_QuestCtrl_Body/Trigger_R/L_SC` (`QuestCtrl_SC.blend`) | ✅ 2026-09-29 · aprobado por Beltrán; sensor en la mano (gatillo +14° al apretar) y los fantasmas de las instrucciones (R = a, L = b); tapa por UV1 CapMask |
| Sensor bio (ENTERING y RECOGNIZING) | `SM_BioSensor_SC` + `SM_BioSensorWaves_SC` (`BioSensor/SM_BioSensor_SC.blend`) | ✅ 2026-09-30 · reemplaza al mando en la mano y en el fantasma de esas dos etapas; aros aditivos que salen hacia la panza cuando está apoyado |
| HUD (desde 2.8 hasta 9.1) | `SM_HUDFrame_SC` + `SM_HUDGlass_SC` + `SM_HUDPulse_SC` (`SM_HUD_SC.glb`, Mesh 3D) | ✅ 2026-09-30 · píldora de 256 × 56 mm a 55 cm y 30° bajo el horizonte; ameba rosada que late a la mitad del ritmo; EEG alto en la ventana 4:1; el anillo en el nido de la derecha (escala 0,115, Ø 45 mm) |
| Hall | `SM_HallShell_SC` + puertas | ⬜ pendiente (hoy: forma provisoria con las mismas medidas) |

## Cambios de mecánicas integrados
| Fecha | Etapa | Cambio | De |
|---|---|---|---|
| 2026-09-29 | ENTERING | aliento en cono ±18°×±8° de 40 a 95 cm (inhalar = hacia la boca, exhalar = espejo); polvo del valle 6144 motas de 1,3 a 110 m; colinas medias respiran (20-40 s, ±45 %), oleaje lejano 15-23 s y 50 % más alto | Breath |
| 2026-09-29 | LOVING | FluidTop (0,0125 0,0324 0,0648) | Mind |
| 2026-09-30 | SURROUNDING | punta del trazo: 4 cm fijos junto a la mano que se afinan (antes crecía con el trazo) | Drawing |
| 2026-09-30 | SURROUNDING | paleta "A · niebla y agua": hueso, celadón, celeste y petróleo, cada uno con degradado punta → cola; teclas de color con ganancia 1,0; aro de la ranura verde agua apagado (0,342; 0,571; 0,456 lineal = #9EC7B4); el marcador con vetas a lo largo del trazo (±5 % de brillo) | Drawing |
| 2026-09-30 | SURROUNDING | punta del pincel: estela de preview (poses de los últimos 0,12 s, tope 16, largo ideal 6 cm, cabeza 0,7 × el grosor, solo sin dibujar y 0,25 s después de soltar) + halo aditivo de 3× la punta (TipHaloPS: resplandor, 3 anillos a 0,35 ciclos/s, pulso 0,4 Hz; dibujando ×1,8 y tiempo ×2,5) | Drawing |
| 2026-09-30 | SURROUNDING | deshacer/rehacer agrandados sin superponerse: SideScale 1,40, cada tecla escala desde el centro de la paleta y gira a 180 ± SideHalf (atan2d(0,2079·S, 1−0,0219·S)+2° = 18,7°), corrida 19,6·(S−1) cm hacia adentro; zona de toque centrada en 180 ∓ SideHalf | Drawing |
| 2026-09-30 | HUD | el HUD pasa a ser la píldora 3D (reemplaza la línea y el punto blanco); el anillo viaja y se desprende girando hacia la inclinación del HUD | Mesh 3D + Narrativa |
| 2026-09-30 | TODAS | aparición "luz primero" (1,5 s; salida = la misma al revés) en timbre, paleta, sensor bio, anillo (sin trazo) y HUD (sin trazo), cada una con su clip de sonido: FX_BELLAPPEAR/VANISH, FX_PALETTEAPPEAR/VANISH, FX_SENSORAPPEAR (Recognizing; en Entering suena FX_TOOLAPPEAR_BREATH)/VANISH, FX_RINGAPPEAR, FX_HUDBIRTH/VANISH. HUD v4: borde y contornos translúcidos, 5 mm | Mesh 3D + Narrativa |
| 2026-09-30 | SURROUNDING | arco de TINTA en la paleta (InkArcPS: r 21,40–22,06 cm, z −1,6, de 319,9° a 180−2·SideHalf+2−6, se vacía hacia el slider; lleno alfa 0,85 × Glow 1,4, gastado alfa 0,06, cabeza 0,9); 30 m de trazo = tanque; al vaciarse guarda solo (resuelve G_SAVE5); el PUNTO de la punta (SM_Tip) = color del pincel × 1,5 + 0,06; el trazo no cambia | Drawing |
| 2026-09-30 | CARGAS (R6) | PROPUESTA de Beltrán en prueba: el alma se TELETRANSPORTA del HUD a la carga y de vuelta (aviso 0,8 s con temblor + háptico que crece → ¡pum! 0,12 s → silencio 0,45 s → ¡pum! de llegada 0,6 s con onda de luz); sonidos FX_SOULDETACH / FX_SOULWARN_BACK, FX_SOULPOP_OUT, FX_SOULPOP_IN, FX_SOULSETTLE; chispa opcional entre lugares (Estética). Reemplaza el vuelo de 1,5 s | Narrativa |
| 2026-09-30 | CARGAS (R6) | complementos de Beltrán: durante el aviso el BORDE DEL HUD se enciende con una luz que le da la vuelta (desde el nido) hasta soltar el alma; la llegada al frente usa la aparición luz primero del anillo girando 1¼ vueltas y frenando (1,1 s); mientras carga, un HALO del color de la etapa vibra detrás del anillo | Narrativa |
| 2026-09-30 | CARGAS (R6) | Beltrán: fuera la luz que viajaba al anillo ("la pelota"): la carga empieza al llegar; el halo va solo POR FUERA del anillo y el alma, más tenue y 15 cm atrás, para que no compita | Narrativa |
| 2026-09-30 | CARGAS (R6) | probado en Unreal (`BP_ChargeTest_SC`): al terminar de cargar, el anillo se queda quieto CHARGE_HOLD = 2 s con la luz encendida antes de volver al HUD; la luz cargada queda encendida en el anillo grande y en el del HUD (las otras cavidades, apagadas) | Beltrán |
| 2026-09-30 | HUD | el pulso del latido es una HERMANA de tu alma (misma malla y material que la del anillo, ~30 mm, late a la mitad del ritmo); se ancla en el asiento izquierdo cuando tu alma llega al HUD por primera vez (SISTER_IN + FX_SISTERAPPEAR); la ameba rosada SM_HUDPulse_SC queda sin uso | Beltrán |
| 2026-09-30 | ATTRACTING | = Test_Sequencer de Secuencer: cielo Uyuni desaturado (arriba #efe0d0, horizonte #fce9c6), sal lisa #fffaf2 sin patrón, esferas Color1-4 (#f6e2b8 · #f3d0ac · #fbeedb · #eec6a0), gusano #e5c6a3 (también en el cuadro de resultados). ⬜ Falta el arte 3D del SAVE (15×6 cm en la mano no dominante, siempre de frente): hoy sigue el botón de pantalla | Secuencer |
| 2026-09-30 | LOVING | = Test_Fluid de Mind: fluido morado poco saturado (arriba #362E3E, medio #241E2A), motas #DDCAE6, célula lila (membrana #E8D8F0, borde #BFA2D5) centrada al frente a 2 m (antes 3,6 m) | Mind |
| 2026-09-30 | INICIO + FINAL | Beltrán: el entorno del inicio y del final es OSCURO, como en Unreal → niebla `voidSky` de celeste claro (arriba .30/.40/.72, horizonte .62/.70/.92) a azul noche casi negro (arriba .006/.009/.022, horizonte .028/.042/.095); el polvo y los títulos blancos ahora leen con contraste | Beltrán |
| 2026-09-30 | FINAL (9.7) | créditos oficiales dictados por Beltrán, como tarjetas de cine debajo del título (rol chico arriba, nombre grande abajo; entra 1,5 s · queda 4 s · sale 1,5 s; las seis en 42 s dentro del minuto): Created and produced by Alma Digital Studio · Written and directed by Vicente Manzano · Music by Vicente Manzano · Development director: Beltrán Lihn · Development assistant: Nicolás Perilli · In collaboration with the Johns Hopkins Berman Institute of Bioethics. Sale "by Alma Digital". Las mismas tarjetas horneadas para Unreal con `hornear/creditos.html` (Michroma, R nítida / G difusa) | Beltrán + Narrativa |
| 2026-09-30 | CARGAS (R6) | tiempos de carga = los del nivel final de Unreal (`BP_Obra_SC.ChargeTimes`): 4 / 5 / 6 / 7 / 10 s (antes 3 / 5 / 7 / 10 / 12) | Narrativa |
| 2026-09-30 | CARGAS (R6) | Beltrán: la carga común dura 4 s y la final 6 s ("un par de segundos más") → 4 / 4 / 4 / 4 / 6. En Unreal la final lleva tres explosiones (1,8 · 3,6 · 5,4 s: destello blanco + onda que recorre los cinco colores, vuelta completa del anillo, vibración y háptico en los dos mandos) | Beltrán |
| 2026-09-30 | LOVING | Beltrán: "cuando la actividad activa la ameba, que las partículas del mundo se muevan más rápido: sentir que todo el world se activa" → las motas del fluido van hasta 4,5× (antes 1,8×) en actividad y vuelven a 0,5× en calma (Mind lo hace en Unreal con `ActiveBoost`) | Beltrán + Mind |
| 2026-09-30 | ENTERING | Beltrán: "las lomas siempre ondulando; al exhalar la ondulación más rápida; en los otros pasos vuelve a su velocidad normal" → el valle usa un tiempo propio del oleaje (`uSwellT`) que avanza ×3 mientras se exhala (respiración que baja o pacer en exhalación) y vuelve suave a ×1 (Breath lo hace en Unreal con `SwellTimeOfs`) | Beltrán + Breath |
| 2026-09-30 | ANILLO | Beltrán: "el material del anillo está muy oscuro; debe ser de la onda de los otros botones" → el cuerpo pasa del metal oscuro al hormigón claro de la familia (#b9b2a7, como timbre, SAVE y sensor); sigue dibujándose por encima de todo | Beltrán + Mesh 3D |
| 2026-09-30 | FINAL | Beltrán: "mientras sucede la última carga nos empezamos a ir a negro; cuando la protoameba se desprende del anillo ya está apareciendo el Center" → el océano funde a negro durante la carga (`ENV_DARK`); en negro el pawn salta afuera de la puerta Este (`TELEPORT`); el anillo se va animado (`RING_OUT`) y la ameba sale nadando (`FISH_OUT`) mientras la puerta del Center ya se enciende (9.3 anclado a 9.1b) | Beltrán |
| 2026-09-30 | HALL → BREATH | Beltrán: "lo que se ve por la ventana de la puerta de salida transiciona suave a un blanco azulado medio; al salir ya debe estar esa transición hacia Breath" → el vidrio Este pasa a blanco azulado en 3 s desde la invitación (`DOOR_E_COOL`), el afuera por la puerta pasa al mismo tono (`OUTSIDE_BLUE`, = HallGlow_Exit de Unreal), caminatas de 3 s, y Entering se abre desde su velo del mismo color (`VEIL1_IN` + `ENV1_IN` 4,5 s) sin pasar por negro | Beltrán |
| 2026-09-30 | AMEBA-PEZ | Beltrán: "que se vaya como una especie de cometa, no tan blanco ni tan brillante, más sutil y más elegante" → estela de 48 chispas chicas y tenues del color del alma (mezcla normal: no se queman a blanco), cabeza que entra suave, cola fina de 1,1 s; el brillo de la carga final (.8) baja a .12 mientras nada | Beltrán |
| 2026-09-30 | CANDIDATAS | Beltrán: "quitarle saturación a las protoamebas para que encajen en la paleta" → los Core desaturados del Hall de Unreal (S×0,55; la verde a 150°): #caecff #ffd2e5 #e5d2ff #ffe6c1 #b1edd2 | Beltrán |
| 2026-09-30 | FINAL · COMPARTIR | Beltrán: después de explorar el cuadro, Alma invita a compartir la experiencia → `EXPLORA` 25 s (el cuadro se queda) · VO_36 + **VO_36b** (invitación) · botones **SHARE / DON'T SHARE** bajo el cuadro, familia del SAVE de Mesh 3D (láser + gatillo, gate `G_SHARE`, cortafuegos 30 s = no compartir) · **VO_36p** (instrucción). Ramas con `clip.when` (nuevo en el motor): SHARE = se va el frente, el anillo se va y el alma sale nadando como cometa con **campanitas** por la puerta del comienzo, que se abre sola (`FISH_DOOR`/`FISH_AWAY`, **VO_36c**); en la constelación está **sin anillo, más brillante y con halo** (`SOUL_UP`, VO_35b). DON'T SHARE = el alma se desvanece con lo demás (`SOUL_VANISH`, **VO_36d**) y no está en la constelación (**VO_35c**) | Beltrán |
| 2026-09-30 | ALMA | Beltrán: Alma se va al terminar el último Hall y no vuelve (desde ahí las voces son omnipresentes; `ALMA_GONE` en 9.6; se quitó VO_35a) · audiorreactiva **suave** (envolvente con ataque 0,12 s / relajación 0,35 s, rodilla y tope: wobble, color más luminoso y cálido, +5 % de tamaño) · envuelta en una **esfera de partículas diminutas con curl noise** que se aviva cuando habla | Beltrán |
| 2026-09-30 | INICIO | Beltrán: 20 s en negro con el aviso **SIMULATED PROTOTYPE** (el build de la postulación corre sin sensor: los datos biométricos son simulados y arranca solo) antes del negro de precalentamiento | Beltrán |
| 2026-09-30 | RESULTADOS | Beltrán: el dibujo del cuadro se construye trazo a trazo (`DRAW_GROW`, 4 s) y se deshace al irse, como en su etapa | Beltrán |
| 2026-09-30 | SONIDOS PROVISORIOS | Beltrán: "mientras no tenga todos los sonidos" → sintetizados para lo nuevo: `FX_SOULSWIM` (campanitas), `FX_SHAREAPPEAR`, `FX_SHAREHOVER`, `FX_SHARESELECT`, `FX_SOULVANISH`, `FX_SOULJOIN`, `FX_RINGVANISH`, `FX_DISCLAIMER`. Se reemplazan soltando el audio sobre el clip | Beltrán |
| 2026-09-30 | ATTRACTING · ENTERING · LOVING | Secuencer: el hover de las esferas es solo visual (sin sonido ni háptico) · Breath: el pacer muestra el avance (pista fina en el aro chico, un punto por ciclo desde las 12, arco horario) · Mind: amebas medias = membrana lila translúcida con núcleo perla | Sesiones |
| 2026-09-30 | ATTRACTING · HALO | Beltrán (vía Secuencer): cada esfera flotante con una cáscara de partículas muy chicas y translúcidas de su color, a 1,3× su radio, con curl noise suave; al agarrarla se empujan y se apagan en 0,9 s; al volver a casa reaparecen en 1,6 s; en el gusano no tiene halo · cometa del alma: chispas aún más pequeñas | Beltrán |
| 2026-09-30 | PALETAS · VELOS | Beltrán: niveles de test, Obra y web con las mismas paletas → el velo de cada etapa = su cielo real: Recognizing (arriba .40/.30/.31, horizonte .95/.85/.83 = SkyColorHorizon de Test_Heart), Loving (#362E3E / #241E2A del fluido de Mind), Attracting (#efe0d0 / #fce9c6 Uyuni de Test_Sequencer); antes quedaban los azules del recorrido del 09-29. Entering abre desde el blanco azulado del Hall. INICIO como Unreal: quietos con el título, la niebla azul a negro a mitad del viaje, el Hall aparece recién en el negro, pasos al final | Beltrán |
| 2026-09-30 | TODAS (ENSAYO) | `ensayo.js` = GENERADO desde Unreal (`ensayo_export.py` → `gen_ensayo_js.py`): los TargetPoints `sc<K>_alma_in / _alma_side / _charge / _title` de cada nivel de test y los valores del `BP_StageRunner_SC` (AlmaTime, InstrTime, OutroTime, ChargeTime, velo). La web aplica el DESPLAZAMIENTO respecto de la base (lo que se mueve en Unreal se mueve igual acá), el velo y CHARGE_T | Narrativa |
| 2026-09-30 | TODAS (R2/R5x/R8) | como la Obra: Alma se corre al costado AlmaTime − largo de la VO después de que termina la bienvenida (≈2 s); se va con la salida de la etapa (R5x, 0,6 s); en R8 vuelve AL FRENTE (1,2 s), dice la luz encendida a los 0,9 s (VO_13/18/24/29, antes sonaba en R6), la invitación 0,5 s después y se va 0,4 s más tarde | Narrativa |
| 2026-09-30 | RECOGNIZING | termina con la MITAD de los latidos: StageBeats 75 → 38 (~0:45 a 50 bpm) | Heart |
| 2026-09-30 | ATTRACTING | el reloj de pasos es de autor: StepBPM 90 (0,667 s por paso), ya no sale del largo del pad | Secuencer |
| 2026-09-30 | HALL | el timbre se hunde 1,0 cm en 0,12 s mientras la mano lo aprieta (BellPressDepth / BellPressTime) | Hall |
| 2026-09-30 | LOVING | viaje: las partículas del medio fluyen hacia el usuario a 25 cm/s desde Begin (entrada ease 4 s, frenado 2 s en el outro); pawn y neurona quietos | Mind |
| 2026-09-30 | HALL (2.2/2.6/2.8/1.10) | = Hall T4: tu alma elegida va al CENTRO del Hall bajo el óculo (0,0,160; Ø 50 cm a 3 m; 4 s smootherstep) y SIN anillo; se desvanece al nacer el HUD, donde renace con su anillo · orbe blanco azulado (r 14 cm, núcleo 0,06 / borde 0,55) envuelve al mando y estalla al tomarlo (0,45 s, ×1,7, FX_PROTOSELECT) · las hendiduras del domo se encienden en onda al entrar (6 s) | Hall |
| 2026-09-30 | ALMA | look de la maqueta (Heart): durazno tibio (Core 1/0,585/0,426 lineal), ~1 m (Size 0,6 → 1), Brightness 1,5; al hablar se entibia hacia (1; 0,72; 0,5), +5 % de tamaño, ataque 0,12 s / relajación 0,35 s (SayClip) | Heart |
| 2026-09-30 | ENTERING | = Breath: exploración libre 12 s (ExploreTime 20 → 12); el pacer aparece con la cuenta y arranca 3 s después (LeadIn); 5 ciclos 4-3-4-3 (70 s); progreso del pacer: un punto por ciclo desde las 12 en sentido del reloj + arco con la etapa completa (0,38 → 0,95 al alcanzarse) | Breath |
| 2026-09-30 | MANDO | el gatillo del mando se aprieta con el valor real (−14° sobre la bisagra + Pressed en el material; BP_UserTool_SC.ToolTrigger) — la web ya lo hacía (+14° al apretar) | Mesh 3D |
| 2026-09-30 | ATTRACTING | el rig usa el mando de la obra (BP_QuestCtrl_SC en el grip, gatillo por IA_Hand_IndexCurl) en vez del cian emisivo; bQuestCtrl en la instancia de Test_Sequencer (false = el cian de antes). La web ya usaba el mando de la obra en toda la experiencia | Secuencer |
