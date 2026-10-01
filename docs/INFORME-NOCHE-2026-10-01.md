# Informe de la noche 2026-10-01: correcciones de la prueba + APK

Para Beltrán, al despertar. Las notas originales están en `docs/NOTAS-BELTRAN-2026-10-01-correcciones.md` y el plan con el estado de cada punto en `docs/PLAN-CORRECCIONES-2026-10-01.md`.

## En una línea
**El APK está instalado en el Quest** como "Soul Charger" (`com.almadigital.soulcharger`, 10:01). La obra entera corrió en el visor de principio a fin con 0 errores, y al terminar vuelve a empezar sola.
- Copia del APK y su OBB: `Escritorio/Soul Charger Obra APK`.
- Lo primero que hay que mirar puesto: el aviso del inicio, el timbre y las manos en el Hall, Attracting con la paleta nueva, y el final.

## Cómo se trabajó
Narrativa dirigió y llevó el editor por turnos. Breath, Heart, Mind, Mesh 3D y Fantasmas hicieron lo de sus etapas, cada uno en su turno. Nadie guardó nada mientras se cocinaba el APK.

## Lo que cambió, por momento de la obra

**Inicio.**
- Aviso en inglés sobre el negro inicial (9 s): "This experience uses sensors that read your heart rate and neural activity. Their signals shape the light, sound and rhythm of your journey. In this build, the sensor data is simulated."
- Entra de 0,5 a 2 s y sale de 7,6 a 8,7 s.

**Hall.**
- El título queda 2,5 s más.
- El timbre suena al tocarlo, se apaga con fade al soltar y vuelve a partir al retocar.
- El anillo radial del timbre desaparece al completarse.
- El sensor gira suave dentro del orb mientras espera.
- Las manos se van al tomar el sensor.
- La protoameba toma la escala de su TargetPoint.
- Alma tiene perillas para su aura (`J - Aura`).
- Al cruzar la puerta (x ≥ 760) la salida termina antes, y el título de ENTERING entra enseguida.

**Etapas.**
- Título legible unos 3 s; Alma aparece y recién 1,5 s después habla.
- Alma al costado es más chica (TP a 0,6) y su escala la manda el TP.
- La fase de inicio de cada etapa espera a que termine la voz de instrucciones.
- Ambientes en crossfade sin huecos y más bajos (0,38).
- Efectos ×0,6. Las voces y las cargas no se tocaron.
- Recognizing (Heart):
  - frases de Alma entre medio (VO_16/16h/17a/17c);
  - pulso a la mitad;
  - la mano ya no queda pegada en el umbral.
- Loving (Mind): la neurona aparece cuando Alma ya está a 2,4 m; VO_22/VO_23; dura 60 s.
- Attracting:
  - nueva paleta (cielo malva, gusano naranja, esferas oro/coral/perla);
  - sin el texto "SAVE MELODY";
  - frases de Alma según lo que haga el usuario (VO_27h si no coloca nada, VO_27b con 3 colocadas, VO_27c, VO_28).
- Drawing: frases según la tinta usada (VO_32h si no dibuja, VO_32b, VO_32c).
- Manos y sensor, una sola regla para toda la obra:
  - Hall: manos hasta tomar el sensor.
  - Entering y Recognizing: sensor.
  - Loving: manos.
  - Attracting, Drawing y final: sensor.
- Mano más transparente.

**Final.**
- La última carga termina antes del negro (ChargeFinal en el instante 0 de la carga).
- El háptico se corta en el final.
- En la vuelta al Hall el velo abre en 1,2 s y recién ahí el anillo se va y el alma nada adelante.
- Al compartir se funde todo el cuadro (gráficos y dibujos).
- La salida no tiene pasos y espera menos (7 s).
- Las estrellas de la constelación crecen animadas.
- Halo de la carga más visible; EEG un poco más grueso y brillante; baldosas en reposo más tenues.

## Probado
**PIE por tramos, en la Obra, 0 errores en los cuatro:**
- inicio (−1): el aviso dura 9 s y el Hall llega hasta el sensor;
- Entering (10): bienvenida → VO_11 → VO_11b → VO_12 → cuenta y pacer, sin voces encimadas;
- Attracting (40): Alma habla 1,5 s después de aparecer, la etapa espera las instrucciones y VO_27h sale a los 20 s sin esferas;
- final (60): carga → negro → Hall → resultados → compartir → salida de 8,5 s sin pasos → créditos.

**APK en el Quest, la obra entera sin nadie puesto (09:19-09:37), con el registro del visor:**
- 17 min del lanzamiento a los créditos, 0 errores de Blueprint y 0 cierres.
- Al terminar los créditos la obra vuelve a empezar sola (probado).
- Todo en orden y en tiempo: aviso → Hall → Entering → carga → Recognizing → Loving (60 s, VO_22 a 15 s y VO_23 a 42 s) → Attracting → Drawing → carga final → Hall → resultados → compartir → salida → créditos.
- Los ambientes vuelven a entrar en crossfade (se vio "ambiente en bucle" en el visor).
- En modo simulado, Attracting y Drawing cierran por `SimStageMax`, como en el APK anterior.

**Rendimiento (fps del visor):**

| Tramo | fps |
|---|---|
| Entering | 72 |
| Recognizing | 69 |
| Loving | 69 |
| Attracting | 63 (con bajones a 51) |
| Drawing | 72 |
| Créditos | 72 |
| Hall, adentro (recepción y resultados) | **42** antes de los arreglos |

Lo del Hall lo encontré y lo arreglé. Los detalles están en la sección siguiente.

## El Hall estaba a 42 fps (encontrado y arreglado esta mañana)
**Diagnóstico en el visor.** Apagué partes del render con comandos de consola mandados por adb.
- Sin las mallas estáticas, el Hall volvía a 72 fps. Sin las transparencias subía apenas a 47.
- El culpable era el material de la piel del Hall, `M_Hall_Interior_SC`, que llena toda la vista. Calculaba por píxel 4 octavas de ruido 3D por hash. Además, la junta de las baldosas (un lazo con `atan2`, `cos` y `sin`) se calculaba también en los muros y la bóveda.

**Arreglos.** Ninguno cambia el diseño, y el ruido tiene el mismo carácter:
1. Junta de las baldosas solo en el piso cerca de las baldosas. Meridianos con una rotación fija en vez de `cos`/`sin` por meridiano.
2. Ruido leído de una textura (`T_HallNoiseRG_SC`): un muestreo por octava en vez de 8 hashes.
3. Lo mismo en las baldosas (`M_Hall_Tile_SC`).

**Medido en el visor, adentro del Hall:**

| Versión | fps | GPU |
|---|---|---|
| Antes | 42 | 21,8 ms |
| Junta y meridianos | 51 | 17,8 ms |
| Ruido por textura | 61 | 14,7 ms |
| + baldosas (lo que está instalado) | **62,5** | ~14 ms |

**Lo que falta para 72 en el Hall (~1 ms).** Apagando las transparencias, el Hall llega a 72-73 fps (11,7 ms). Las partículas no pesan, así que el costo está en el **haz de luz del óculo** (`BP_LightShaft_SC`): un cilindro aditivo de dos caras, de 4 m, con 176 nodos, alrededor de donde estás parado. No lo toqué porque es un look que aprobaste. Las opciones son:
- bajarle la precisión a half (riesgo de bandas);
- una cara sola;
- simplificar el material contigo mirando.
- Respaldo del código anterior: `VR_Test/Saved/ClaudeScripts/Obra/dump/code_*_respaldo.hlsl`.
- El procedimiento quedó en la skill (`references/materials-vr.md`).

## Sin probar en el visor con alguien puesto
La corrida del Quest fue sin nadie puesto y con datos simulados: prueba el flujo, los tiempos y que no haya errores, pero no se vio ni se sintió nada. Falta mirar puesto:
- el aviso (render y legibilidad);
- el timbre (suena al tocar, fade al soltar);
- el sensor girando;
- las manos que se van al tomar el sensor;
- Alma más chica al costado;
- las perillas del aura;
- el halo de la carga (`HaloMaxOpacity` si hace falta);
- las baldosas en reposo (`RestDim`);
- la mano más transparente;
- la paleta de Attracting;
- las estrellas que crecen;
- el fundido del cuadro al compartir;
- el háptico apagado en el final.

El APK final (10:01) solo cambia, respecto del que corrió completo, los dos materiales del Hall. Esos se probaron dos veces adentro del Hall en el visor, sin errores.

## Pendiente / no se hizo
- **E1, la última carga y el negro.** Hecho a las 11:00, después de tu pedido:
  - la carga se llena (8,5 s) y queda 1 s llena;
  - el ENTORNO se va a negro en 2 s, pero el anillo y el alma siguen visibles encima;
  - medio segundo después aparece el Hall alrededor del anillo, el alma se desprende como el pez y el anillo se va.

  De paso apareció un bug viejo: el "look del final" del anillo tenía los materiales vacíos y nunca se había aplicado. Probado en PIE sin errores. **En el APK de las 12:33.**
- **D1, fundido del inicio del Hall más lento.** No se tocó: hay que verlo contigo para no tapar el nacimiento del Hall.
- **Attracting va a 63 fps de promedio, con bajones a 51.** Medido en el visor esta mañana. No lo investigué: el Hall era más urgente.
- **D7/D8, anillo de la protoameba y su animación hacia el HUD.** Hecho a las 10:40, después de tu "dale", con el anillo de carga y su animación de vuelta:
  - el anillo nace alrededor de la protoameba cuando llega a su punto;
  - sus luces siguen a las baldosas;
  - al nacer el HUD vuelve al nido en 1,3 s (antes, la vuelta de la carga tardaba unos 2 s, más 2 s de espera).

  Probado en PIE sin errores. Perillas en `Obra_Director → Hall - Anillo`. **En el APK de las 12:33.**
- **Fantasmas (instrucciones animadas).** En pausa, como pediste.

## Decisiones que tomé por ti
- El aviso inicial dura **9 s** (no 5): el párrafo no se alcanza a leer en 5. Perilla: `Obra_Director → DiscTime`. El texto entra de 0,5 a 2 s y sale de 7,6 a 8,7 s (`BP_Disclaimer_SC.DiscStep`).
- Loving dura **60 s** (antes 80): después de VO_23 quedaban ~35 s de silencio.
- Recognizing: tiempo límite **180 s** (antes 150), porque el pulso ahora va a la mitad.
- Ambientes: volumen **0,38** (antes 0,6) en `Obra_Director → Ambientes → AmbVolumes`.
- Título de cada etapa: legible ~3 s (entra 0,5→1,8 s, sale 4,6→5,6 s) y Alma entra a los 5,8 s.
- Alma espera **1,5 s** después de aparecer antes de hablar.
- Efectos a **×0,6** (lista exacta en `VR_Test/Saved/ClaudeScripts/Obra/dump/sfx_vol_out.json`, con el volumen anterior de cada uno para volver atrás).
- Alma al costado a **0,6** en todas las etapas, como habías dejado las primeras.
- Nada quedó commiteado: lo decides tú al probarlo.
