# Sonidos de la demo (BDW) · listado por etapa, con la duración de cada animación

2026-10-21. Duraciones sacadas de las perillas de cada pieza y medidas en el log del visor de la prueba de Beltrán de hoy (11:56-12:15).
**Regla de la obra: el tiempo lo manda la animación, no el sonido** (los sonidos son de un disparo; ninguna animación espera a que termine su sonido). Por eso la columna "dura" es el largo de la animación: el sonido puede ser igual o más corto, con cola.

Estado: ✅ ya está bien (Beltrán) · 🟡 suena uno provisorio (el asset de hoy) · ⬜ no suena nada.
Dónde: **2D** = en la cabeza (interfaz) · **3D** = sale del objeto (con atenuación `ATT_Objeto_SC`).

---

## 0. Comunes (los usan el menú y las tres experiencias)
| # | Sonido | Cuándo | Dura la animación | Tipo | Estado (asset de hoy) |
|---|---|---|---|---|---|
| 0.1 | Hover de botón | el láser entra en un botón | 0,12 s (sube 0,1 cm) · al salir 0,18 s | 3D, corto | ✅ `VR_click1` |
| 0.2 | Click / confirmar | gatillo sobre un botón | 0,45 s (se hunde y confirma) | 3D | ✅ `ProtoSelect` |
| 0.3 | **Entrada de botón** | aparece START, BACK, los 3 cuadros del menú, el botón START de Breath | 1,5 s (luz primero, después la forma) | 3D | 🟡 `SBubbleHoverOn` |
| 0.4 | **Salida de botón** | se va un botón (después del click o al cambiar de paso) | 1,5 s (la misma curva al revés) | 3D | 🟡 `SBubbleHoverOut` |
| 0.5 | **Entrada del panel de instrucciones** | al empezar cada experiencia (~10 s después de cargar el nivel, medido) | 1,5 s (luz primero) | 3D | 🟡 `SBubbleHoverOn` |
| 0.6 | **Pasar página** | cambia la página del panel (Breath 4 páginas, Draw 2, Heart 2) | instantáneo (la imagen cambia en un cuadro) → sonido corto, 0,2-0,5 s | 3D | ⬜ |
| 0.7 | **Salida del panel de instrucciones** | termina la última página | 1,5 s | 3D | 🟡 `SBubbleHoverOut` |
| 0.8 | **Aparece el objeto que flota** (sensor en Breath/Heart, mando-pincel en Draw) | con el panel | 1,5 s (luz primero) | 3D | ⬜ |
| 0.9 | Objeto flotando (opcional, loop suave) | mientras espera que lo tomen: gira 40°, se inclina 28°, sube y baja 2,5 cm | hasta que lo toman (tope 25 s) | 3D, loop | ⬜ |
| 0.10 | **Tomar el objeto** | lo toma una mano: desaparece el que flota y aparece en la mano | 0,8 s (crece en la mano) | 3D, en la mano | 🟡 `Tomado` |
| 0.11 | HUD aparece | entra el HUD (en el menú, con la onda de luz) | onda 1,6 s; el EEG nace 1 s después | 2D | ✅ |
| 0.12 | HUD sale | al final de cada experiencia: tiembla y se va con un "pop" | 0,9 s de temblor + pop | 2D | ✅ |
| 0.13 | Música / ambient | cada nivel, en bucle; fundido de entrada 3 s, de salida 3 s | — | 2D, loop | ✅ |

## 1. Menú
| # | Sonido | Cuándo | Dura la animación | Tipo | Estado |
|---|---|---|---|---|---|
| 1.1 | Aparece el título SOUL CHARGER + START | al abrir el menú (START visible a los ~4 s) | 1,5 s (START) | 3D | 🟡 0.3 |
| 1.2 | **Sale el título** | al apretar START | 2 s | 2D o 3D | ⬜ |
| 1.3 | Entran BACK y los 3 cuadros | 2,2 s después del START | 1,5 s | 3D | 🟡 0.3 |
| 1.4 | Hover / click en un cuadro | elegir experiencia | 0,12 s / 0,45 s | 3D | ✅ |
| 1.5 | Se van los botones y los láseres | al elegir | 1,5 s | 3D | 🟡 0.4 |
| 1.6 | **Viaje por el espacio azul** (whoosh de arranque + aire en loop) | al elegir: acelera 4 s y sigue sin frenar hasta el cambio de nivel | arranque 4 s · el viaje entero ~38 s (medido: elegir → HUD 17 s → negro 15 s → nivel 6 s) | 2D, arranque + loop | ⬜ (hoy solo pasa de Ambient 1 a Ambient 2) |
| 1.7 | HUD se instala | a los ~16 s del viaje | 1,6 s | 2D | ✅ 0.11 |
| 1.8 | **Cierre al color de la experiencia** (transición) | ~15 s después del HUD, al terminar la voz | 6 s (el velo cierra) y el nivel abre a los 6,5 s | 2D | ⬜ (la música funde 3 s) |

## 2. Entrada a cada experiencia (igual en las tres)
| # | Sonido | Cuándo | Dura la animación | Tipo | Estado |
|---|---|---|---|---|---|
| 2.1 | **Apertura del velo** | al cargar el nivel | 3 s (de 1 a 4 s) | 2D | ⬜ |
| 2.2 | **Título de la etapa** (ENTERING / RECOGNIZING / SURROUNDING) | junto con el velo | ~5 s (de 0,5 a 5,7 s) | 2D | ⬜ |
| 2.3 | Panel + objeto | a los ~10 s | ver 0.5 y 0.8 | | |

## 3. Breath (ENTERING)
| # | Sonido | Cuándo | Dura la animación | Tipo | Estado |
|---|---|---|---|---|---|
| 3.1 | Tomar el sensor | 0.10 | 0,8 s | 3D | 🟡 `Tomado` |
| 3.2 | **Sensor en la panza: entra al umbral** | se enciende el disco del HUD (la página 2 avanza tras 1,5 s seguidos dentro) | encendido inmediato | 2D (HUD) | ⬜ |
| 3.3 | **Sensor sale del umbral** | se apaga el disco | inmediato | 2D (HUD) | ⬜ |
| 3.4 | **Nace la metaball** | se va el panel → 2 s después | 4 s (morfeo de entrada) | 3D | 🟡 `VR_shep_scale_up_01` |
| 3.5 | **El mando se convierte en el sensor** | 0,8 s después de la metaball | 1,5 s (el mando se achica, el sensor nace con luz) | 3D, en la mano | 🟡 `ProtoSelect` |
| 3.6 | Exploración libre | 12 s antes de la cuenta | — (ambiente + ráfagas de "vida") | 3D | 🟡 `SND_VidaGustA/B/C`, `SND_VidaSoplo` |
| 3.7 | Cuenta "three, two, one" | voz de Alma | 2,83 s | 2D | ✅ voz |
| 3.8 | **Aparece el pacer** (la guía) | con la cuenta | 0,6 s | 3D | ⬜ |
| 3.9 | **Inhalación** | fase inhala del pacer | **4 s** (el aro crece) | 3D/2D, una vez por ciclo | 🟡 `SND_PacerInhale` (+ `Pad` y `Pluck`) |
| 3.10 | **Sostén** | después de inhalar | **3 s** | idem | 🟡 `SND_PacerHold` |
| 3.11 | **Exhalación** | fase exhala | **4 s** (el aro se cierra) | idem | 🟡 `SND_PacerExhale` |
| 3.12 | **Sostén** | después de exhalar | **3 s** | idem | 🟡 `SND_PacerHold` |
| 3.13 | **Pluck de respiración** (marca el cambio de fase) | en cada cambio de fase (4 por ciclo) | instantáneo → 0,3-1 s con cola | 3D | 🟡 `SND_PacerPluckInhale/Hold/Exhale` |
| 3.14 | (opcional) Pulso/metrónomo | cada 1 s o solo en el cambio de fase | — | | 🟡 `SND_PacerPulse` |
| — | El ciclo completo | 4 + 3 + 4 + 3 = **14 s**, **10 ciclos = 140 s** (medido: 142 s) | | | |
| 3.15 | **Se va el pacer** | terminan los ciclos | 0,6 s | 3D | ⬜ |
| 3.16 | **Se va la metaball** | después del pacer | 2,5 s | 3D | 🟡 `VR_shep_scale_down_02` |
| 3.17 | Se va el sensor de la mano / vuelven las manos | final | 1,6 s | 3D | 🟡 `VR_shep_scale_down_02` |

## 4. Heart (RECOGNIZING)
| # | Sonido | Cuándo | Dura la animación | Tipo | Estado |
|---|---|---|---|---|---|
| 4.1 | Tomar el sensor | 0.10 | 0,8 s | 3D | 🟡 `Tomado` |
| 4.2 | **El sensor se tiñe de rojo** | al tomarlo (empieza la etapa) | 1,2 s | 3D | ⬜ |
| 4.3 | **Mano en el pecho: entra al umbral** | el sensor reconoce el pecho (entra lento, sale rápido) | 1,5 s para entrar · 0,3 s para salir | 3D | ⬜ |
| 4.4 | **Pulso del corazón** | cada latido, solo dentro del umbral; también el anillo que late en la página 2 del panel | un latido cada 60/BPM s (a 65 bpm, **0,92 s**): el sonido tiene que caber en ~0,6 s | 3D, en la mano | 🟡 `HeartBeat` |
| 4.5 | **Se va el panel** | a los 3 latidos | 1,5 s | 3D | 🟡 0.7 |
| 4.6 | **Sube la esfera** | después del panel (el latido en pausa) | **3 s** (medido 12:10:45 → 12:10:48) | 3D | ⬜ |
| 4.7 | (opcional) El mar gira y vuelve | durante la etapa, muy lento | ~100 s ida, vuelve al final | 3D, loop/textura | ⬜ |
| 4.8 | Se va el sensor | fin de la etapa (medido: 100-135 s después de que sube la esfera) | 1,6 s | 3D | 🟡 `VR_shep_scale_down_02` |

## 5. Draw (SURROUNDING)
| # | Sonido | Cuándo | Dura la animación | Tipo | Estado |
|---|---|---|---|---|---|
| 5.1 | Tomar el mando-pincel | 0.10 | 0,8 s | 3D | 🟡 `Tomado` |
| 5.2 | **Aparece la paleta** (en la otra mano) | al tomar el pincel | 1,5 s (luz primero) | 3D, en la mano | ⬜ |
| 5.3 | **Pincel 1 · Marcador** (TaperedMarker) | mientras se aprieta el gatillo y se mueve la mano | lo que dure el trazo | 3D, **loop** que sigue la velocidad y la presión | 🟡 3 loops viejos del dibujo (`ESM_..._Fire_Loop_01`, `FF_OHT_124_texture_loop`, `UZ_fx_..._bubbles`) |
| 5.4 | **Pincel 2 · Óleo** (OilPaint) | idem | idem | loop | ⬜ |
| 5.5 | **Pincel 3 · Luz** (Light) | idem | idem | loop | ⬜ |
| 5.6 | **Pincel 4 · Pintura húmeda** (WetPaint) | idem | idem | loop | ⬜ |
| 5.7 | (opcional) Inicio y fin de trazo | al apretar / soltar el gatillo | instantáneo → 0,1-0,3 s | 3D | ⬜ |
| 5.8 | **Selección de pincel** | tecla de pincel en la paleta | 0,35 s (la tecla sube 0,9 cm y brilla) | 3D, en la paleta | ⬜ |
| 5.9 | **Selección de color** (4: terracota, ocre, salvia, azul) | tecla de color | 0,35 s | 3D | ⬜ |
| 5.10 | **Tamaño del pincel** | deslizador de grosor (la perilla escala de 0,5 a 1,6) | continuo mientras se arrastra → tick por paso o tono que sube/baja | 3D | ⬜ |
| 5.11 | Hover sobre una tecla de la paleta | la punta entra en una tecla | 0,35 s (sube 0,35 cm) | 3D, muy suave | ⬜ |
| 5.12 | Deshacer / rehacer (si se usan) | teclas de la paleta | 0,35 s (la tecla se hunde 0,8 cm) | 3D | ⬜ |
| 5.13 | **Se borra el trazo de práctica** | al terminar la práctica | 0,8 s (los trazos se achican) | 3D | ⬜ |
| 5.14 | **Arranca el reloj** | con la voz `VO_DD1` | instantáneo (el reloj del HUD empieza en 2:30) | 2D | ⬜ |
| 5.15 | (opcional) Últimos 10 s | el reloj llega a 0:10 | 10 s | 2D, tick | ⬜ |
| 5.16 | **Se acaba el tiempo / la tinta** | a los 150 s o sin tinta | instantáneo | 2D | ⬜ |
| 5.17 | **Se guarda y se presenta el dibujo** | el dibujo gira frente a la persona | **12 s** de giro (2 vueltas a 60°/s); medido del guardado al corrimiento: 14-15 s | 3D, loop corto o textura | ⬜ |
| 5.18 | **El dibujo se corre a la derecha** | a la vez que se va el HUD y llegan los resultados | **1,5 s** (160 cm, con freno suave) | 3D, whoosh | ⬜ |
| 5.19 | **Se van la paleta y el pincel** | final | 1,5 s | 3D | ⬜ |

## 6. Final (igual en las tres)
| # | Sonido | Cuándo | Dura la animación | Tipo | Estado |
|---|---|---|---|---|---|
| 6.1 | HUD sale | 0.12 | 0,9 s + pop | 2D | ✅ |
| 6.2 | **Aparece el cuadro de resultados** | con la salida del HUD | ~1,5 s (luz primero; los gráficos se encienden en el último 40 %) | 3D | 🟡 (la aparición de luz de los botones) |
| 6.3 | (opcional) El número del índice de calma | al encenderse los gráficos | — (hoy aparece de una vez) | 2D | ⬜ |
| 6.4 | **Se va el cuadro** | a los 35 s | ~1,5 s | 3D | 🟡 |
| 6.5 | **Cierre a negro** | después del cuadro | 2,5 s (la música funde 3 s) | 2D | ⬜ |
| 6.6 | Vuelta al menú | a los 4 s del negro | — (el menú abre con su música) | 2D | ✅ |

---

### Lo que más falta (prioridad para la demo)
1. **Breath**: pluck, inhalación y exhalación nuevas (3.9-3.13) · umbral in/out (3.2-3.3) · metaball entra/sale (3.4, 3.16).
2. **Heart**: pulso del corazón (4.4) · umbral del pecho (4.3) · sube la esfera (4.6).
3. **Draw**: un loop por pincel (5.3-5.6) · selección de pincel y color (5.8-5.9) · tamaño (5.10) · se acaba el tiempo (5.16) · presentación y corrimiento (5.17-5.18).
4. **Botones e instrucciones**: entrada/salida (0.3-0.5, 0.7) · pasar página (0.6) · aparece el objeto (0.8).
5. **Transiciones**: viaje del menú (1.6) · cierre al color (1.8) · velo + título (2.1-2.2) · resultados entra/sale (6.2, 6.4) · negro (6.5).

### Para entregar los archivos
WAV 48 kHz, 24 bits, mono para lo 3D (sale del objeto), estéreo para lo 2D. Loops con el principio y el final empalmados. Sin silencio al principio: el sonido arranca con la animación.
