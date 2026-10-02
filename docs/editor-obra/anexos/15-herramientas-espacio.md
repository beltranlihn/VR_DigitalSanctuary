> Anexo de la auditoría de herramientas del 2026-10-01 (revisión: espacio y vista 3D). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md).

## Veredicto por herramienta

Rutas relativas a `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/`. `OBRA` = `VR_Test/Saved/ClaudeScripts/obra/`. `TRK` = `.claude/skills/unreal-vr/blueprints/`. `MOCK` = `web/editor-obra/mockup/src-body.html`.

| Herramienta | Estado | Evidencia (archivo:línea) | Qué cambiar |
|---|---|---|---|
| **Nombres y nivel de los TP de etapa.** `TP_sc<K>_alma_in/_alma_side/_charge/_title`, con tag igual al nombre sin `TP_`, en cada nivel de test (subnivel de la Obra) | OK | `TRK/BP_StageRunner_SC.md:4`; `OBRA/ensayo_place.py:94-105`; `docs/MAPA-DE-AJUSTES.md:23-25,126`; la Obra los lee en `OBRA/dump/obra_all_now.txt:1437-1487` | Nada en la convención. En la maqueta, cambiar "Stop · sc0 · Entering" (`MOCK:471`) por "PlayerStart · Test_Entering". El origen del marco es ese PlayerStart (`obra_all_now.txt:34-35,124`). |
| **Marco del gizmo en las etapas.** fwd / side (+ = derecha) / up sobre los ojos, en cm | OK | `OBRA/ensayo_export.py:2-4,59`. Las fórmulas `fwd=dx·c+dy·s` y `side=−dx·s+dy·c` son las correctas para el eje derecho de UE. Altura = TP.z − (PlayerStart.z + 120), igual que en la Obra (`obra_all_now.txt:1442,1478,1487`) | Unificar la convención. El gizmo dice "0.90 m left" (`MOCK:560`) y el inspector "Side −0.90" (`MOCK:471`): usar una sola. El rótulo debe decir "sobre los ojos (autor 1,20 m)" y no solo "Height". |
| **Valores de ejemplo del gizmo, de Plan y de POV en la maqueta** | Corregir | La maqueta pone sc0_alma_side en 2.20 / −0.90 / +0.05 (`MOCK:542-543,560`). La última exportación da alma_side 140 / −300 / +20, alma_in 220 / 0 / +5, charge 253 / 0 / +37 ×2,115 y title 300 / 0 / 0 (`OBRA/ensayo_export.json:13-40`). Plan dibuja la carga a 1,4 m, más cerca que alma_in (`MOCK:543`) | Cargar los valores reales en la maqueta. Así Beltrán diseña sobre la geometría verdadera: Alma al costado queda a **65° a la izquierda y 3,3 m**, fuera de ±60°. |
| **Escala del TP de carga = tamaño del anillo** | OK (con matiz) | `ChargeTP` copia la escala (`obra_all_now.txt:1479`) y el anillo la toma de `TargetRef` (`OBRA/dump/chargefx_all.txt:49`). La rotación del TP se ignora porque el anillo mira a la cámara (`chargefx_all.txt:25`) | En el gizmo de la carga, no ofrecer rotación. Mostrar "escala 2,115" y, si se cosecha `BigScale` y la caja de la malla, el diámetro en cm. La escala no es un tamaño en cm. |
| **Escala y rotación del resto de las anclas** | Corregir | Alma toma la escala del TP (`obra_all_now.txt:1443,1454`); el TP lateral está en 0,6 (`TRK/BP_Obra_SC.md:232`). Del TP del título solo cuenta el yaw (`obra_all_now.txt:1487`). `final_sketch`: escala X × 55 cm (`MAPA:83`). `TP_hall_soul_present`: escala = `Size` (`MAPA:70`) | Hace falta un esquema por ancla: `{scaleMeaning, usedRotation}`. El inspector "Place" (`MOCK:471`) no tiene yaw y pone "Scale ×" igual para todo. |
| **Altura "+0.05 m"** | Corregir / Verificar en vivo | Hay tres modos de altura. (1) Corregida con la cámara: etapas, objetos del Hall y final (`obra_all_now.txt:1442,1665`; `OBRA/dump/hall.txt:366,388,560`). (2) Absoluta: Alma en el Hall va por `AppearAt/MoveTo` sin corrección (`hall.txt:129,136,172,486-496`; `TRK/BP_Alma_SC.md:87-88`). (3) Pegada a la cabeza: fantasmas de Breath y Heart (`TRK/BP_GhostPlayer_SC.md:24-27`) | Cada ancla lleva un campo `heightMode`. La vista debe advertir que un PIE de escritorio sale 120 cm más abajo (`gotchas.md:750`; `MAPA:7`). |
| **Paradas `Stop*`** (ArrowComponent del `HallDirector`) | Falta (en la maqueta y en el plan) + Riesgo | `TRK/BP_HallDirector_SC.md:29-30`; `MAPA:54`. Son componentes, no actores: la cosecha del plan solo nombra "TargetPoints y actores con tag" (`PLAN:282-286`). Hay literales que dependen de ellas: `HallExitEarly` en x ≥ 760 (`TRK/BP_Obra_SC.md:230`) y el sonido de las puertas, que se calcula desde las paradas (`TRK/BP_HallDirector_SC.md:169`) | Cosechar las paradas por componente. Mostrarlas con candado (son estructurales). Toda propuesta sobre una parada lleva revisión de esos literales. |
| **Anclas del Hall y del final** (`TP_hall_*`, `Timbre`/`Sensor`/`TituloInicio` por tag, `HallSoul_*`, `Final_*`, `final_*`, `CreditStar_*`) | Corregir | `StopCard` y `StopExit` tienen yaw 180 (`TRK/BP_HallDirector_SC.md:30`). `Final_BotonShare` en Y +15 queda a la **izquierda** del usuario (`TRK/BP_Obra_SC.md:178-184`) | Marco por ancla: `{stop}` explícito (StopCard para el final, StopExit para los créditos, StopInside o `TP_hall_pawn` para el Hall). Nunca usar la Y del mundo como "lado". Hacer pruebas doradas (abajo). |
| **Cosecha** (`ensayo_export.py`, que pasa a ser `harvest_score.py`) | Corregir | Hace `load_level` en el editor compartido (`ensayo_export.py:37,61`) y no comprueba que haya funcionado. `load_level` falla si hay cambios sin guardar (`gotchas.md:68`). Toma `ps[0]` de "PlayerStart" (`:38-39`), y con la Obra abierta hay más de uno (`OBRA/dump/editor_actors_now.json`: 2 × `PlayerStart_0`). Calcula el seno y el coseno por serie (`:47-49`). Solo trae 4 TP y no incluye Test_Hall (`:10,51`). Toma `EyeRef` del runner (`:45`) mientras que la Obra usa 120 literal | Detalle en el hallazgo 3. |
| **Propuesta espacial web → Unreal** | Corregir | El anexo dice aplicar un parche con `set_actor_transform` (`anexos/03-unreal-orquestacion.md:189`). Esa tool **devuelve true y no mueve nada** (`.claude/skills/unreal-vr/references/toolsets.md:121`) | Usar la receta probada de `OBRA/ensayo_place.py:27-39,51,107-112`. Detalle en el hallazgo 2. |
| **"Appear here" con marca nueva** | Falta en Unreal | `PLAN:128` | Un TP nuevo no tiene quien lo lea: la Obra solo busca sus tags fijos (`obra_all_now.txt:1439,1450,1473,1485`). Va con la insignia *preview only* hasta F4 (`BP_ScorePlayer_SC`). |
| **Acciones "Move to mark" y "Walk"** | Falta en Unreal / Corregir | `MOCK:330,284`. Solo Alma tiene `MoveTo(Tag)` (`TRK/BP_Alma_SC.md:88`). La llegada a una etapa es un **teleport** bajo el velo (`obra_all_now.txt:124`), no una caminata. Caminar solo existe en el Hall, entre las paradas | "Arrives at stop sc0" debe decir "Teleport to PlayerStart · Test_Entering". "Move to mark" queda restringido a Alma. |
| **Cámara POV** | Corregir | La web usa 72° vertical y el ancho depende del panel (`web/prototipo-narrativo/world.js:48`), y tiene un `camBack` que aleja la cámara (`timeline.js:1172-1176`) | Encajar el cuadro al campo del Quest 3: unos 110° × 96° (dato externo de Meta, no está en el repo). Sin `camBack` en POV. Ojo del autor a 1,20 m. |
| **Cámaras Free y Plan** | Riesgo | Cinco cosas cuelgan de la cámara y los materiales sin prueba de profundidad se dibujan a través de todo (`anexos/02-prototipo-mundo-3d.md:124-136`) | Separar la cabeza de la cámara de render. Modo rayos X opcional. Una chapa que avise "POV en negro (velo cerrado)" cuando corresponda. |
| **Campo visual ±30° / ±60°** | Corregir | En la maqueta las elipses son decorativas, a 33 % y 62 % del ancho (`MOCK:555`). En Plan el cono es fijo de ±30° (`MOCK:540`) | Proyectarlas desde la cámara. En Plan, mostrar el azimut real de cada ancla. |
| **Live now** | Riesgo | `MOCK:350-352`. Hay voces que dependen del usuario (`CueAttract`/`CueDraw`, con umbrales de tinta y de esferas: `TRK/BP_Obra_SC.md:224`) y un modo `bSimulated`/`SimCut` de 90 s (`:123`) | Cada fila con su procedencia: exacto / simulado / aproximado / no representado. |
| **Modo Play** (el mouse es la mano) | Riesgo | En la web, la mano es un punto a 0,6 m sobre el rayo del mouse (`timeline.js:1000`). `G_BREATH` exige zona en la panza y orientación del sensor (`TRK/BP_BreathRig_SC.md:57-62`). El timbre tiene `TouchRadius` 14 (`TRK/BP_HallDirector_SC.md:56`) | Las esperas biométricas se resuelven solo con "Complete ⏎" (`MOCK:353`). Lo que se resuelva por proximidad lleva la marca *proxy*. |
| **Coordenadas de `world.js`** (la vista 3D de F1) | Riesgo alto | F1 lleva "la vista 3D actual, sin cambios" (`anexos/09-critica.md:122`; `PLAN:314`). Las bases propias de la web no coinciden con las de Unreal (`guion.js:20-24,267`) | Detalle en el hallazgo 1. |
| **Perillas espaciales de los roles** | Corregir (menor) | `BellPressDepth` vive en `BP_HallDirector_SC` (`TRK/BP_HallDirector_SC.md:107`), y la maqueta lo atribuye al rol de `BP_BellArt_SC` (`MOCK:241-242`). Falta `TouchRadius` 14. "Size 1.0" de Alma (`MOCK:248`) no es el tamaño efectivo | Atribuir cada perilla a su BP. Mostrar el tamaño efectivo = `Size` × escala del punto. |
| **Anclas que se mueven en runtime y actores TestOnly** | Riesgo | `ObraAlmaA/B` y `ObraChargeTarget` (carpeta `Obra/Puntos`) se reescriben en cada etapa (`obra_all_now.txt:1441,1474`; `MAPA:29`). `Alma_Ensayo`, `Entering_UserTool` y `StageRunner` se destruyen al arrancar la Obra (`MAPA:117`) | La cosecha los marca *runtime* (solo lectura) y excluye TestOnly al resolver roles: en la Obra, el sensor es `UserTool_Obra` (`MAPA:192`). |

## Hallazgos importantes

1. **La vista 3D de F1 va a mostrar posiciones que no son las de Unreal.** La web aplica solo el desplazamiento de cada TP respecto de una base (`web/prototipo-narrativo/ensayo.js:4,288-292`), y esa base se suma a posiciones propias de la web que no son la base de Unreal (`guion.js:20-24`). Con los TP en su base (que es como están, `OBRA/ensayo_export.json`), la diferencia es:

   | Ancla | Web | Unreal | Diferencia |
   |---|---|---|---|
   | alma_in | `front(PSC,2.2,.15,−.8)`: 0,80 m a la izquierda, +15 cm | 0 lateral, +5 cm | 0,80 m de lado y 10 cm de alto |
   | alma_side | 2,6 / −1,6 / +0,3 (31,6°) | 1,4 / −3,0 / +0,2 (65°) | 1,2 m al frente y 1,4 m de lado |
   | carga | 0,75 m (`CONT_C`) | 2,53 m, +37 cm | 1,8 m |
   | título | 5 m, +0,5 (`guion.js:267`) | 3 m, 0 | 2 m y 0,5 m |

   El mundo tampoco coincide. En la web, el Hall está en el origen, las etapas en x = 24 y la salida en −50 m (`guion.js:11-16`; `world.js:530`). En Unreal, las 6 celdas se superponen en el origen (`MAPA:24`), Sequencer está en (362700, 100000) y TBTest en z 106 (`ensayo_export.json`), y `StopExit` está en −15 m.

   *Corrección:* antes de F1, reemplazar `ALMA_ST`, `ALMA_ST2`, `CONT_C` y los títulos por `front(PSC, base/100…)` con `ENSAYO.base`. Es un cambio chico que hace que desplazamiento 0 = posición idéntica. Hasta entonces, la vista 3D lleva la etiqueta "previs, not Unreal positions" y no muestra números en el gizmo.

2. **La vía del parche espacial no funciona.** `set_actor_transform` devuelve true y no mueve nada (`toolsets.md:121`), y la forma JSON de `relativeLocation` escribe solo la X (`toolsets.md:123-133`). La receta correcta:
   - `get_root_component` + `set_properties(root, '{"relativeLocation":"(X=..,Y=..,Z=..)"}')`, lo mismo para `relativeRotation` y `relativeScale3D`, y releer con `get_actor_transform` (`toolsets.md:141`);
   - para las paradas y los planos de título, escribir en el componente de la instancia (`<Nivel>:PersistentLevel.<Actor>.<Comp>`, `gotchas.md:733`);
   - todo dentro de `try/except BaseException`;
   - canario de actores por nivel, y `save_assets` solo del paquete del subnivel tocado, sin PIE corriendo (`gotchas.md:688-702`; `CLAUDE.md` §2.b; `MAPA:11,25`).

   Además, la propuesta guarda el valor relativo junto con la pose de la parada y la pose del actor cosechadas. Se aplica solo si la pose actual sigue igual a la cosechada; si no, es un conflicto (la misma reconciliación de tres vías que las perillas). Un TP nuevo creado con `add_to_scene_from_class` cae en el "nivel actual" del editor (`MAPA:26`), no necesariamente en el nivel de test.

3. **La cosecha actual puede fallar sin avisar.** Si `load_level` falla (`gotchas.md:68`), el script sigue leyendo la Obra abierta y toma `ps[0]` entre varios PlayerStart (`ensayo_export.py:38-39`): el marco queda mal y no hay error. *Corrección para `harvest_score.py`:*
   - no usar `load_level`;
   - filtrar cada PlayerStart, TP y actor por el prefijo del paquete en su `refPath`;
   - abortar con un mensaje si falta alguno de los 6 subniveles (a las 12:44 solo estaba cargado Test_Sequencer: `editor_actors_now.json`);
   - usar 120 fijo y avisar si `EyeRef` ≠ 120;
   - leer escala XYZ y normalizar el yaw relativo.

4. **La serie de Taylor rompe los marcos con yaw 180.** En `ensayo_export.py:47-49`, a 180° el coseno da −0,976: `final_alma` sale a 226 / −215 en vez de 230 / −222, y el cuadro a 185,4 en vez de 190. A 270° el coseno da 1,27, inválido. Hoy no muerde porque los niveles de test tienen yaw 0, pero el final y los créditos usan `StopCard`/`StopExit` a 180°. *Corrección:* llevar el ángulo a [−45°, 45°] más el cuadrante, o usar una tabla para los múltiplos de 90°. Pruebas doradas, si la parada está donde dice el tracker:
   - `Final_BotonShare` → "1.90 m front · 0.15 m left · −0.59 m";
   - `AnilloCarga` → "1.90 · 1.12 left · +0.05";
   - `final_sketch` → "1.00 m right".

5. **Las anclas no comparten una semántica única** de altura, escala y rotación (ver la tabla). Si el editor trata todo como "posición + escala ×", miente sobre el tamaño de Alma (0,6 al costado, 0,5 en `hall_alma_side`: `TRK/BP_Obra_SC.md:232,360`), sobre la orientación del título (solo el yaw) y sobre la carga (sin rotación). *Corrección:* el registro de anclas lleva `{level, label, tag|component, frameStop, heightMode, scaleMeaning, usedRotation, authorable|runtime}`.

6. **Los trackers se contradicen en posiciones.** `StopInside` figura en −300 (`TRK/BP_HallDirector_SC.md:30`) y en −450,5 (`TRK/BP_Obra_SC.md:219`). `StopCard` figura en 300 y en 396,45 (`TRK/BP_Obra_SC.md:178`). Alma en resultados aparece con `final_alma` (`obra_all_now.txt:1660-1666`, volcado de las 13:07) y con `ResAlmaLeft`/`ResAlmaScale` (`TRK/BP_Obra_SC.md:293`). El editor solo puede tomar posiciones de la cosecha en vivo, nunca de los trackers (`gotchas.md:107`).

7. **Lo exportado está viejo.** `ensayo_export.json` es del 2026-09-30 18:07, con alma_side a escala 1,0; hoy es 0,6 (`TRK/BP_Obra_SC.md:232`). Además, `gen_ensayo_js.py` vive en el scratchpad de otra sesión (`anexos/03-unreal-orquestacion.md:102-104`). La web muestra la antigüedad de la cosecha (`PLAN:316`) y no da un valor por bueno si es anterior al último commit de los `.umap`.

8. **Hay literales espaciales cableados que no siguen a las anclas:** `HallExitEarly` en x ≥ 760, `DoorLeadDist` 620, `HallTickLead` a z = pawn + 110 y el sonido de las puertas, que se calcula con las paradas (`TRK/BP_Obra_SC.md:230`; `TRK/BP_HallDirector_SC.md:69,121,169`). Mover una parada desde la web rompe la salida del Hall. Las paradas van con candado.

9. **Live now y Play: qué es fiel y qué no.**
   - **Fiel**, si se cosecha: tiempos, poses de anclas en su marco, visibilidad y fase de aparición, qué voz suena, qué espera y su cortafuegos.
   - **Simulable solo como caja o proxy:** respiración (zona + orientación + `NormRange`), latido (BioHub; Unreal ya tiene `bFakeSignal`), esferas de Attracting y tinta de Drawing. De estas últimas dependen voces (`TRK/BP_Obra_SC.md:224`), así que el usuario simulado tiene que modelar "tinta y esferas en el tiempo", o esas voces se muestran como "depende del usuario".
   - **No se representa:** Niagara y aura (900 motas), luz horneada, audio espacial (`ATT_Objeto_SC`), orden de dibujo y velo. Un ejemplo de por qué importa: el velo tapa siempre a los materiales opacos del anillo (`TRK/BP_Obra_SC.md:234`).
   - **Lo que depende de la cabeza** (HUD, `FinalRing` a 2,53 m, `LeadActor`, fantasmas de Breath y Heart) lleva la insignia "follows head". El HUD no es ajustable (`MAPA:109`).

10. **Choca la palabra "marca".** Se usa para el tiempo (`OnMark`, `S<K>.P<n>`, `PLAN:249`) y para el espacio ("Appear here con una marca nueva", "el gizmo edita la marca", `PLAN:128,192`). Además, en el Hall y el final el objeto es su propia marca: las marcas de autor se retiraron (`TRK/BP_AuthorMark_SC.md:3`; `MAPA:66-67,79-89`). En la interfaz en inglés: "Point" para lo espacial y "Mark" para lo temporal. "El gizmo edita la marca" vale solo para los TP.

## Lo que hay que verificar en vivo en Unreal

Para una sesión en su turno de la cola: solo lectura, con `L_SoulCharger_Obra` abierto y sin `load_level`.

1. **Panel Levels de `L_SoulCharger_Obra`:**
   - qué subniveles están cargados (los 6);
   - su Level Transform (posición y rotación = 0; si no, el editor muestra otra cosa que el juego, que usa `LoadLevelInstance` con desplazamiento 0, `TRK/BP_StageTour_SC.md:7`);
   - cuál es el nivel actual (en negrita).
2. **`find_actors(name='PlayerStart')`:** cantidad y `refPath` de cada uno. Anotar la posición y el yaw del de cada nivel de test y del de Test_Hall (z 76,97).
3. **En los 5 niveles de test:** `get_actor_transform` de `TP_sc<K>_alma_in/_alma_side/_charge/_title`. Interesa la posición, el yaw, la escala XYZ y **las claves del dict `rotation`**, para confirmar que `r.get('yaw')` de `ensayo_export.py:24-26` lee de verdad (`gotchas.md:599`). Confirmar alma_side en escala 0,6.
4. **Test_Hall, `HallDirector` (`BP_HallDirector_SC_C_0`):** `relativeLocation` y `relativeRotation` de los componentes `StopStart`, `StopDoor`, `StopInside`, `StopFar`, `StopReturn`, `StopCard` y `StopExit`. Resolver −300 / −450,5 y 300 / 396,45.
5. **Test_Hall, puntos y objetos:** transform de `TP_hall_alma_center/side/exit`, `TP_hall_pawn` y `TP_hall_soul_present` (escala 0,7). También de los actores con tag `hall_bell` (`Timbre`), `hall_sensor` (`Sensor`) y `hall_intro_title` (`TituloInicio`, con sus componentes `TitleP`, `SubP`, `LogoADS`, `LogoJHU` y `LogoIDEAS`), de `HallSoul_0..4` y de `Ghost_BELL/TAKE/PICK`.
6. **Grafos `HallAlmaAppear`/`HallAlmaMove` de `BP_HallDirector_SC` y `AppearAt`/`MoveTo` de `BP_Alma_SC`:** confirmar que Alma en el Hall sigue **sin** corrección de altura. El volcado es de las 07:52 (`hall.txt:486-496`).
7. **`L_SoulCharger_Obra`, carpeta `Final`:**
   - transform de `Final_Cuadro`, `Final_BotonShare` y `Final_BotonDontShare` (pitch 15), `AnilloCarga` (1,9), `Final_AlmaPez` (2,115) y `Final_Creditos` (con `TitleP`, `SubP`, `Card0..5` y `Logo*`);
   - transform de `final_sketch`, `final_alma`, `final_fish_door` y `final_fish_away`;
   - `CreditStar_00..29`: que sean 30, y sus escalas.
8. **Grafo `AlmaResults` de `BP_Obra_SC`:** ¿lee `final_alma` o `ResAlmaLeft`/`ResAlmaScale`? Valores de esas dos perillas en la instancia `BP_Obra_SC_C_0`.
9. **Grafo `HallExitEarly` de `BP_Obra_SC`:** literal 760 frente a la posición real de la puerta Este, que depende de `StopReturn` y `StopCard`.
10. **`BP_ChargeFx_SC_C_0.BigScale`** y la caja de `SM_ChargeRing_SC`, para dar el diámetro del anillo en cm.
11. **Carpeta `Obra/Puntos`:** labels y tags de los TargetPoints (`ObraAlmaA`, `ObraAlmaB`, `ObraChargeTarget`) para marcarlos *runtime* en la cosecha.
12. **Prueba en seco de la vuelta**, sin escribir: calcular `Final_BotonShare` relativo a `StopCard` con la parada leída en vivo y compararlo con "1.90 · 0.15 left · −0.59". Confirmar también que `save_assets(['/Game/Test_Entering'])` guarda solo ese subnivel con la Obra abierta. Hacerlo **en un turno sin cambios pendientes**, porque guarda.