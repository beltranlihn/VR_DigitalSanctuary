> Anexo de la auditoría del 2026-10-01 (informe: taxonomía de la obra para el editor). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md); donde este anexo lo contradiga, gana el plan.

# Taxonomía de Soul Charger para el editor de gameplay y narrativa

Saqué esto de los documentos de la obra. El guion V5 es la estructura de base, pero varios valores ya no coinciden con lo que corre hoy en Unreal y en la web, así que marco esas diferencias donde importan.

## 1. Tipos de elemento

Las pistas de la web hoy son: `vo`, `fx`, `amb`, `hap`, `pawn`, `world`, `obj`, `ui`, `int` (`web/prototipo-narrativo/timeline.js:11-21`). Esa lista es la semilla de los grupos. Lo que falta modelar como tipo propio está en las filas marcadas con ★.

| Tipo | Qué edita el autor | Duración | Qué lo dispara |
|---|---|---|---|
| **VO** (`VO_nn` + letra; `_h` = ayuda) | texto en inglés, audio, volumen, fundidos, si sale de Alma (3D, `SayClip`) o en 2D ("omnipresente" después de que Alma se va), aire antes y después (`VODelayIn/Out`; en la Obra `AlmaSpeak` espera 1,5 s) | **la del audio**: es la única excepción a la regla de tiempos | un ancla, el fin de otro VO (`OnVOFinished`, `GUION-V5:952`), un evento del usuario, un temporizador de ayuda, un contador ("tercera esfera", `GUION-V5:639`) o una rama |
| **FX** (`FX_NOMBRE`) | asset, volumen (hoy ×0,6, `PLAN-CORRECCIONES:18`), fundidos, si es único o loop, comportamiento al redisparar (el timbre "vuelve a empezar desde el principio", `NOTAS-BELTRAN:8`), parámetro que lo modula (volumen según la velocidad de la mano en `FX_DUSTSWIRL`, `GUION-V5:169`; tono según la carga en `FX_CARGABELL`, `:237`) | **la del timeline, nunca la del WAV** | un ancla o un evento de interacción |
| **AMB / música** (`AMB_01..09`) | volumen (0,38), duración del crossfade, loop, a qué tramo pertenece, quién manda la música (en Attracting manda el secuenciador: el ambiente baja a 0 en 4 s, `GUION-V5:654`) | elástica: llega hasta el siguiente ambiente | cambio de lugar o de etapa |
| **HAP** (`HAP_NOMBRE`) | amplitud, duración, mano (dominante, otra o ambas), pulso o continuo, señal que lo modula (`BeatEnv`, presión del gatillo) | fija si es pulso; si es continuo necesita **un final explícito** | un ancla, el fin de una espera, una señal |
| **VFX y animación de objeto** | curva, duración, sobreimpulso, parámetros de material (`Lift`, `Glow` de las baldosas, `GUION-V5:375-378`) | fija | un ancla |
| **Entorno / look** (valle, membrana, fluido, salar, océano, niebla, `RoomLight`, paletas `CTops/CHors`, piso `Floor`) | color, brillo, tiempo de encendido, perillas de cada etapa | fija | un ancla de etapa |
| ★ **Velo** (el único "corte") | variante (suave, tono o plano), colores de origen y destino, tiempos de cierre y apertura (0-4 s cierra, 4,5-8 s título, 6-10 s abre, `GUION-V5:726-734`) | fija | despedida de la etapa (R8) |
| **Objetos** (timbre, sensor, candidatas, anillo, HUD, metaball, pacer, gusano, 68 esferas, mesa, paleta, cuadro, constelación, puertas, baldosas) | ciclo de vida (nace → aparece → vive → sale → se destruye); **transform completo** desde un TargetPoint, escala incluida (`NOTAS-BELTRAN:12,23`); padre (el anillo contiene a la ameba, `GUION-V5:113-115`); escalonado (candidatas cada 0,4 s, esferas de a 4 por cuadro) | fija; la salida es la aparición al revés | un ancla |
| **Títulos y textos** (título de etapa, subtítulo, línea de instrucción, aviso, créditos) | texto **en inglés**, material líquido o blanco, entrada, permanencia y salida, posición fija en el mundo (`sc<K>_title`), color de la etapa | fija, con un **mínimo legible** (~3 s, `INFORME-NOCHE:155`) | un ancla |
| ★ **Alma** (actor persistente con estados) | aparecer (1,2 s), hablar, correrse al costado (TP lateral, escala 0,6), moverse, salir, perillas del aura | encadenada a sus VO | un ancla o el fin de un VO |
| **Pawn** | tramos (duración, aceleración, si suenan los pasos, balanceo y viñeta), paradas, teletransporte **bajo negro** | fija | un ancla |
| ★ **Fantasma demostrativo** (`GHOST_*`) | grabación `DA_Ghost_<ID>`, color, distancia, poses por segundo (11), cantidad de ecos (4-5), línea de texto de 3 a 8 palabras, botón que brilla | **elástica**: bucles de 4-6 s + 1 s de pausa, termina con el gesto | la espera a la que pertenece (`guion.js:139`: dura lo que dura `G_BELL`) |
| ★ **Espera / interacción** (`G_*`) | gesto (apoyar y sostener, tomar, apuntar + gatillo, sostener SAVE 3 s, entrar al umbral de la panza o del pecho), duración esperada, tiempo de ayuda, **tiempo de cortafuegos** y qué hace el cortafuegos | **elástica** | el usuario; la web ya lo modela como `gate(key, label, expected, fw)` (`timeline.js:50`) |
| ★ **Mecánica con condición biométrica** | Entering: exploración de 12 s + cuenta + 5 ciclos 4-3-4-3 (~70 s). Recognizing: 38 latidos en zona. Loving: 60 s por reloj. Attracting: juego libre → SAVE. Surrounding: tinta de 30 m → SAVE | elástica, con tope | el cuerpo o el reloj, más un cortafuegos |
| ★ **Carga (R6)** | índice de etapa, color, tiempo (hoy **4/4/4/4/6 s**, `BP_Obra_SC.md:42`; el guion dice 3·5·7·10·12, `GUION-V5:445`), tiempo quieta al final (2 s), giro, halo, sonido y háptica | fija | fin de la mecánica |
| ★ **Rama** | SHARE / DON'T SHARE: clips condicionados con `when` (`guion.js:589-604`); el cortafuegos elige la opción por defecto | por rama | elección del usuario |
| ★ **Modulación (capa viva)** | señal → parámetro con rango (calma → remolino de 1,8× a 0,5×, `GUION-V5:606`; respiración → metaball; latido ÷2) | no ocupa tiempo | señal continua |
| ★ **Operador / OSC** | `/soulcharger/start`, `stage n`, `reset`, `bAutoStart` (`GUION-V5:183-185`) | — | externo |
| ★ **Datos que pasan de una parte a otra** | melodía, dibujo, ciclos de respiración, mano dominante (`bRightHanded`) → la carta y los rigs | — | quien los produce y quien los consume |

## 2. Relaciones

1. **Ancla temporal.** Hay tres formas: segundos desde el inicio del momento, `['KEY','end',+n]`, o una referencia a otro momento (`guion.js:1-6`). Ejemplos: `VO_01c` termina cuando se enciende el portal (`GUION-V5:203`). Cada clip `VO_06b..f` "al empezar dispara" su baldosa, su título y su cavidad del anillo (`GUION-V5:360-370`).
2. **Cadena de VO.** `VO_27` → `VO_27d` 0,5 s después (`VO-AUDITORIA:151`). La cuenta de Entering espera a que termine `VO_12` + 0,3 s (`:128`).
3. **Durar hasta.** El fantasma dura lo que dura la espera (`guion.js:139`).
4. **Disparo por evento.**
   - El fin de `G_BELL` dispara `HAP_PULSE_STRONG` y `FX_BELLRING` (`guion.js:144`).
   - El primer latido en zona dispara `VO_17a`, y la membrana no empieza a latir hasta que esa VO termina (`GUION-V5:573-576`).
   - La tercera esfera colocada dispara `VO_27b`.
5. **Ayuda por inactividad.** `VO_01h` a `G_BELL.start + 8` (`guion.js:141`). En las demostraciones, la ayuda llega después de 2 bucles del fantasma. `VO_27h` suena a los 20 s sin esferas (`PLAN-CORRECCIONES:14`).
6. **Cortafuegos.** La tabla completa está en `GUION-V5:126-137` (timbre 25 s, sensor 15 s, elegir 30 s, R4 25 s, Entering 110 s, Recognizing 90 s, Attracting y Surrounding 120 s). El cortafuegos llama **al mismo verbo que el final real** (`GUION-V5:140`; `OBRA:436-444`).
7. **Interrupción.** Si el usuario actúa antes de que termine la voz, la voz se funde en 0,3 s y la obra sigue (`GUION-V5:1015`; `AUDITORIA-09-30:23`).
8. **Rama.** `VO_34b` → 25 s para explorar → `VO_36b` → botones + `VO_36p` → elección, con cortafuegos de 30 s = no compartir. Con SHARE suena `VO_35b`; en las dos ramas siguen `VO_35a` y `VO_37` (`VO-SOUL-CHARGER:113`).
9. **Bucles.** Ciclos del pacer, bucle del fantasma, 2 pasadas de la melodía (`GUION-V5:664`), ambiente que vuelve a entrar en crossfade (A1), secuenciador de 8 pasos a 90 BPM.
10. **Capas de aparición.** Entorno → Alma → elementos → herramienta (`GUION-V5:34`, `439-448`), con la regla de rendimiento: "nunca aparecen dos cosas nuevas en el mismo instante" (`:33`).
11. **Contrato de etapa.** Es el esqueleto real de Unreal (`BP_Obra_SC.md:21-28`):
    - 0: velo y título;
    - 4: Alma recibe (`AlmaTime` = largo de la VO + 3);
    - 5: instrucciones (`InstrTime`);
    - 6: la mecánica, que termina con `bStageDone` o por tiempo;
    - 7: salida;
    - 8: carga, y despedida (`FlowBye`).

    Las llamadas son `StageIntro`, `StageBegin`, `StageOutro` y `bStageDone` (`:38`). El editor tiene que mostrar ese molde como la plantilla R1-R9 de cada etapa (`GUION-V5:437-448`), con Loving como excepción declarada: no tiene R4.
12. **Estados exclusivos.** Hay cosas que no son eventos sino estados que duran:
    - quién ocupa las manos: manos, sensor o mando (`PLAN-CORRECCIONES:25`);
    - quién manda la música;
    - si Alma está al frente o al costado;
    - el HUD presente o ausente.

## 3. Estructura

- **Partes:**
  - Acto 0: arranque en negro, más el aviso.
  - Acto 1: inicio (niebla, título, viaje, portal, timbre, entrada).
  - Acto 2: Hall (sensor, elección, baldosas, HUD, salida).
  - Acto 3: llegada al Centro.
  - Actos 4-8: las 5 etapas, separadas por 4 velos.
  - Acto 9: final (última carga, negro, regreso al Hall, cuadro, compartir, salida, constelación y créditos).
- **Duraciones:** el presupuesto del guion es ~14:15 (`GUION-V5:63-78`). Lo real es más largo:
  - la web suma 1018 s ≈ **17 min** (`AUDITORIA-09-30:24`);
  - el APK tardó **17 min** del lanzamiento a los créditos (`INFORME-NOCHE:69`).
  - El peor caso, con todos los cortafuegos, es ~16:30 según el guion.
- **Volumen en la web hoy:** 10 actos, 52 momentos y ~350 clips (`guion.js`):
  - 49 de VO, 84 de FX, 20 de HAP, 10 esperas, 9 fantasmas;
  - 77 en la pista de objetos y 51 en la de mundo;
  - 9 ambientes.
- **Hojas de producción:** ~60 IDs de FX, 8 patrones HAP, 60 clips de VO en la mezcla final (`VO-AUDITORIA:17-78`) y ~15 VFX nuevos.
- **Zonas fijas de autor:** 0, 1.1-1.6, 1.9-2.2, 2.6-2.9, 3, R1-R3, R5b-R9 de cada etapa, Loving entera, los velos, y 9.1-9.4, 9.6-9.7.
- **Zonas elásticas:**
  - 1.3, el play del operador (sin tope);
  - 1.8 timbre, 2.3 sensor, 2.5 elección;
  - el R4 de 4 etapas;
  - el R5 de Entering, Recognizing, Attracting y Surrounding;
  - la elección de compartir.

  En total son ~11 esperas, y concentran casi toda la variación entre usuarios.

## 4. Qué decide aquí un editor de cine

- **Ritmo y respiración:**
  - los silencios: los ~12 s entre frases de Loving; los 3 s después de la pregunta;
  - cuánto dura un título legible;
  - cuánto aire hay entre que Alma aparece y que habla;
  - la duración del velo, que es el único corte;
  - el crecimiento de las cargas.
- **Solapamientos:**
  - crossfades de ambiente, que funcionan como cortes J/L de sonido;
  - una VO que monta sobre una caminata;
  - cuándo un FX anticipa la imagen.
- **Orden de revelación:** qué aparece primero dentro de cada capa y el escalonado de los grupos (las candidatas, las baldosas).
- **Encuadre sin cámara.** El usuario mira donde quiere, en 360°. El "plano" es **dónde** aparece cada cosa respecto del frente del usuario sentado: los TargetPoints. Por eso la vista 3D no es opcional, es la mitad del montaje.
- **Cómo explicar lo no lineal a alguien que piensa en película:**
  - **Tiempo elástico.** Una espera es un "congelado que espera al actor". Se dibuja como un bloque rayado con un mínimo, un valor esperado y un máximo (el cortafuegos). Todo lo anclado después se corre con ella, como un ripple.
  - **Usuarios simulados.** Un selector de persona recalcula toda la línea y la duración total con la meta de 15:00:
    - **Rápido:** actúa enseguida y corta la voz.
    - **Típico:** el valor `expected` de cada espera.
    - **Lento:** llega a la ayuda.
    - **Ausente:** recorre todos los cortafuegos.

    Es el "robot" que Beltrán pidió el 09-30 y todavía no se usó (`AUDITORIA-09-30:22`).
  - **Ramas** como tomas alternativas: se ve una a la vez y existe un "ver ambas".
  - **Capa viva** como automatización: modula, pero no mueve tiempos.
  - **Analogía útil:** la hoja de cues de teatro, donde cada cue entra con la acción del actor o con un reloj.

## 5. Lecciones de las correcciones del 10-01

| Problema que apareció en la prueba | Función del editor que lo habría evitado o detectado |
|---|---|
| Huecos de silencio entre ambientes; "la obra se sintió parada" (`NOTAS-BELTRAN:19,50`) | La pista de música exige cobertura continua y marca huecos de más de 1 s para cada persona simulada |
| 21 VO grabadas que no sonaban, y 4 eliminadas que seguían cableadas (`VO-AUDITORIA:84,108-115`) | Vista de cobertura: cada clip con su estado en Unreal (cableado, huérfano, eliminado) desde el reporte de sincronización |
| Alma habla antes de aparecer (`NOTAS-BELTRAN:22`) | Regla: toda VO de Alma va anclada a ≥ fin de su aparición + 1,5 s |
| Alma "dice hola y se queda callada" en Heart (`:25`) | Medidor de **aire muerto**: tiempo sin voz, instrucción ni respuesta dentro de una espera, con umbral |
| El título ENTERING casi no se vio (`:20`) | Mínimo de legibilidad por tipo y ancla al cruce de la puerta, no al fin de la caminata |
| La neurona aparece con Alma todavía al frente (`:43`) | Conflictos espaciales: dos objetos en la misma zona del campo visual al mismo tiempo, visibles en la vista 3D en el instante t |
| Manos duplicadas; sensor y manos a la vez (`:9,32,42`) | Pista de **estado exclusivo** "manos/herramienta" para toda la obra, una sola fuente |
| Háptico pegado en el final (`:41`) | Regla: todo loop o háptico continuo necesita un final explícito |
| La última carga se fue a negro antes de terminar (`:38`) | Ancla de orden ("negro del ENTORNO a fin de carga + 1 s") y fundidos que apuntan a un **grupo**, no a todo |
| Al compartir solo se fue el marco (`:45`) | Objetos compuestos: la salida se aplica al grupo con todos sus hijos |
| Pasos al salir (`:46`) | Los pasos son una propiedad de cada tramo del pawn |
| Las estrellas pasaron de 0 a 1 de golpe (`:47`) | Regla: nada aparece sin animación de entrada |
| TargetPoints que no mandaban la escala, y el TP lateral repetido "nivel tras nivel" (`:12,44`) | Gizmo de transform completo y **posición compartida entre etapas**, con excepciones visibles |
| Pulso "rapidísimo" (`:26`) | Simulación de señales a ritmo real (50-70 bpm) y divisor `BeatDiv` a la vista |
| La voz no prevalecía (`:24`) | Buses de mezcla VO > FX > AMB con ducking bajo la voz |
| Guion, web y Unreal se separaron (cargas 3·5·7·10·12 frente a 4/4/4/4/6; Recognizing de 18 a 38 latidos, `AUDITORIA-09-30:121`; Loving de 80 a 60 s) | Una sola fuente de verdad, o un indicador de divergencia por valor |
| Arrays de VO indexados desde 0 ("VO 25 = posición 24", `AUDIO-QUE-PIDE-EL-MOTOR:44`) | Todo referenciado por ID, nunca por posición |

## 6. Reglas que el editor debe hacer cumplir

1. **Tiempos por timeline; solo la VO dura su audio.** Si se cambia un WAV, la coreografía no se mueve (memoria `tiempos-por-timeline-no-por-sonido`; `AUDITORIA-09-30:53`).
2. **Toda espera tiene ayuda y cortafuegos**, y el cortafuegos sigue el mismo camino que el final real (`GUION-V5:121-142`).
3. **Nada del usuario se cierra con un timer, y lo autoral no espera al usuario** (`OBRA:45`).
4. **Toda demostración va con voz**, más una línea de 3-8 palabras y el botón real que brilla; termina con el gesto (`GUION-V5:469-474,1015`).
5. **La VO es interrumpible**: se funde en 0,3 s si el usuario actúa.
6. **Textos in-headset en inglés** (`GUION-V5:110`). La voz no cuenta respiraciones ni latidos, y nada es un puntaje (`:108-109`; `OBRA:82-85`).
7. **IDs con prefijo** `AMB_nn`, `FX_`, `VO_nn[a-z|h]`, `HAP_`, `VFX_`, `GHOST_`, `G_`. Las keys de clips y momentos no se renombran, porque son las llaves de los ajustes guardados (`README:12`).
8. **Alma aparece antes de hablar** (+1,5 s) y no ocupa el frente cuando nace el elemento central.
9. **Nada aparece de golpe**: sonido + VFX, y háptica si lo toca la mano (`GUION-V5:31`), con aparición "luz primero" de 1,5 s.
10. **Nunca dos apariciones en el mismo instante** (rendimiento, `GUION-V5:33`), y revelación por capas.
11. **Todo botón tiene animación de presión** (memoria `botones-siempre-con-animacion`).
12. **Música continua**, con la mezcla en el orden VO > FX > AMB.
13. **Cada cosa nace cuando se necesita y se destruye al terminar**; nada de cargar y esconder (`OBRA:326-328`; memoria `cargar-por-etapa`).
14. **La posición es un TargetPoint con transform completo.**
15. **Toda rama lleva a un final construido** (`OBRA:137`). Loving es la única etapa sin R4.
16. **Meta ≤ 15:00 con el usuario típico**, a la vista siempre.
17. **La sincronización no pisa en silencio los valores de instancia de Beltrán.** Los valores de los niveles de test son finales.
18. **Los créditos son los oficiales** y no se editan sin su dictado.