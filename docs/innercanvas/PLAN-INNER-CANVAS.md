# Inner Canvas — guion y plan (2026-11-11)

> Experiencia de dibujo **de pie** para un evento corporativo. **8 visores Pico 4 Enterprise**, cada uno con su APK y su experiencia (no es multiusuario), más **un PC con Windows** que muestra en vivo los 8 dibujos en pantalla dividida.
> Base: la demo de Barcelona Design Week (`L_Demo_Draw` + su director). Todo lo nuevo vive en **`/Game/InnerCanvas`**: lo de Soul Charger y de la demo no se toca.
> Pedido y decisiones de Beltrán: notas de voz del 2026-11-11 (memoria `brief-pico-experiencia-2026-11-11`).

---

## 1. Guion (vigente desde el 2026-11-12: sin panel de instrucciones ni trazo de práctica)
Nota de Beltrán con dibujo (paleta con COLOR / BRUSH / SIZE / UNDO / REDO, mando con DRAW): primero se explica todo, después el
dibujo es libre. Director: `BP_ICFlow_IC` escrito desde `ic_flow2_dsl.py`. Tutorial: `BP_ICTutor_IC` (`ic_tutor_dsl.py`).

| Fase | Qué pasa | Voz / texto (EN · ES) |
|---|---|---|
| 0 | El mar verde de Draw. Título **INNER CANVAS** y logo. Botones **ENGLISH / ESPAÑOL** a 42 cm al frente y 24 cm bajo los ojos, **se tocan con la mano** (sin láser ni gatillo: todavía no se explicó el mando). Solo manos | Pista: *Touch a button with your hand · Toca un botón con la mano* |
| 1 | Al tocar uno: se van título y botones | — |
| 2-3 | El **mando flota al frente** con el texto *"Toca el control con tu mano hábil"* | `IC_01` bienvenida (5 minutos) · `IC_04` *Touch the controller in front of you with your dominant hand* + pista `HINT_TOUCH` (vuelve cuando termina la voz) |
| 3→4 | Al tocarlo, el mando **queda en esa mano** y aparece el **teclado** (apuntar + gatillo; A-Z, Ñ en español, ESPACIO, BORRAR, OK) | `IC_13` *Now write your name. Point at each letter and press the trigger* + pista `HINT_NAME` |
| 5 | **Tutorial**: la paleta y un mando aparecen al frente, de cara a la persona. Con cada frase, una línea y su etiqueta (dos columnas ordenadas): COLOR, PINCEL, TAMAÑO, DESHACER, REHACER, GATILLO (el gatillo late de color). Después las etiquetas se van y el mando **toca un color, toca un pincel y dibuja un trazo corto** (a la derecha). La paleta **se desarma** y el mando se va. Tiempos: `TutAt` del director (0,8 · 4,4 · 6,7 · 9,2 · 11,9 · 14,7 · 17 · 20,6 · 28,6 · 30,2 s). Los subtítulos se apagan durante el tutorial (las etiquetas dicen lo mismo) | `IC_14` *This is your palette, and this is your brush* · `IC_15` color · `IC_16` pincel · `IC_17` tamaño · `IC_18` deshacer · `IC_19` rehacer · `IC_20` *To draw, press and hold the trigger* · `IC_21` *Touch the palette with the tip of the brush to choose. Then hold the trigger, and draw* |
| 5→6 | La paleta y el pincel **aparecen en las manos** (paleta en la otra mano) | `IC_22` *Now they are in your hands* |
| 6 | Se marca el espacio: **solo el piso**; cada pared aparece cuando la persona se acerca | `IC_02` *This is your drawing space…* |
| 7 | — | `IC_03` *There's nothing to get right…* |
| 8 | HUD (nombre, reloj **5:00**, círculo de tinta) y arranca el dibujo libre. Tinta `InkM` 200 m para 5 minutos | `IC_06` *You have five minutes, or until your ink runs out…* |
| 9 | Dibujo libre | A 30 s: `IC_07`. Poca tinta: `IC_08` |
| 10 | Fin por tiempo o tinta: el dibujo se des-dibuja y **vuelve a su tamaño, girando alrededor de la persona**; da **dos vueltas** (`HoldTime` 26 del `BP_TBDirector_NC`) y **se des-dibuja** | `IC_09`/`IC_10` · `IC_11` *Come back to the center…* |
| 11 | Cuando el dibujo terminó de irse: **mensaje grande al frente** en el estilo del título (Michroma, `MI_TourTitle_ENDES`/`ENDEN` sobre el plano `Title`, que va por encima del velo), a 3 m y a la altura de los ojos, y el velo se cierra a **niebla blanca** (2-5 s). El mensaje aparece a 1-2,6 s y **se va a 15-17 s**: la persona siguiente ve solo niebla. Queda así hasta la **orden del PC** | `IC_12` *Thank you. You can take off your headset now* (subtítulo) |
| — | **Orden del PC** (botones por visor en la pantalla del PC, puerto UDP **9301**): **RESET** = recentra (`ResetOrientationAndPosition`: la posición y la mirada del visor en ese momento pasan a ser el centro y el frente del espacio) y reinicia desde la niebla, en el título; **REINICIAR** = solo reinicia. Sirve en cualquier fase. Sin recarga de nivel | — |

Voces generadas (Soul Charger Woman, receta de la demo): `tools/innercanvas/vo_ic.json` → `python tools/innercanvas/gen_vo_ic.py` → `Content/InnerCanvas/Audio/VO/IC_xx(_ES)`. Subtítulos: `tools/innercanvas/subs_ic_ue.json`.

**Operador:** cuando la persona se quitó el visor (niebla blanca), se le pone a la persona siguiente, se la para en el punto físico de la sala mirando al frente y se aprieta **RESET** en el cuadro de ese visor en la pantalla del PC (dos clics: el primero arma, "¿SEGURO?", el segundo antes de 3 s envía). El cuadro dice **ESPERANDO RESET** mientras el visor está en la niebla. **REINICIAR** vuelve al título sin recentrar. La orden va a la IP de la que llega cada visor (no hay que configurar nada más que `-ICWall=` en el visor). De emergencia, desde el visor: Menú/Y ×5 (`BP_DemoExit_SC`, recarga el nivel con `OpenLevel`; en el Pico los cambios de nivel de la demo quedaron colgados, así que usarlo solo si algo se traba). Sin nadie, la app espera en el título.

## 2. La pantalla del PC (build de Windows)
- 8 cuadros (4 × 2). Cada uno: el espacio de dibujo completo visto por una **cámara fija**, el dibujo en vivo, y el **nombre, el tiempo y la tinta**.
- Al terminar, el dibujo de ese cuadro **se des-dibuja y vuelve a dibujarse centrado en su cuadro, a su tamaño, girando** (solo se achica si girando no cabe), y **queda girando** hasta que en ese visor empieza una sesión nueva (cuando la persona siguiente confirma su nombre). Ahí el cuadro se limpia y arranca de nuevo. No se guardan imágenes.
- **Pantalla completa en 4K** (pedido de Beltrán 2026-11-12): `InnerCanvas_Pantalla.bat` abre en la resolución física de la segunda pantalla (3840 × 2160 en una 4K; lee el monitor sin el escalado de Windows). Cada cuadro mide 960 × 1080 y su cámara dibuja a esa resolución. El texto del HUD escala con el alto de la pantalla.
- Colores: el mismo **mar verde y blanco** del visor (los 27 valores de color y clima del `BP_DrawSea_SC` de `L_InnerCanvas` copiados a las 8 celdas; hasta el 2026-11-12 13:17 las celdas tenían los valores por defecto, azules), **más oscuros en el PC para que el dibujo resalte** (Beltrán 2026-11-12: agua, cresta, resplandor y polvo × 0,55; cielo y niebla, `Zenith`/`HorizonColor`, × 0,3, porque el cielo está en la zona alta del tonemapper y × 0,55 casi no se notaba; valores en `ClaudeScripts/InnerCanvas/sea_pc_oscuro.json`). El visor no cambia. Número, nombre y tiempo van sobre franjas oscuras translúcidas.
- Texto del PC con **`F_ICWall_IC`** (Quicksand a tamaño 64): la fuente de la obra es tamaño 9 y Canvas la rasteriza a ese tamaño y la estira, así que en 4K se pixelaba.
- **Banner arriba** (92 px de 1080): INNER CANVAS · ALMA DIGITAL STUDIO y la **señal de cada visor**: verde **OK** (último estado hace < 3 s; el visor lo manda 5 veces por segundo), ámbar **débil** (< 15 s), rojo **sin señal** (más, o nunca llegó). Los 8 cuadros van debajo (en 4K, 960 × 988 = el RT de cada cámara).
- **Sin el contorno del espacio** en la pantalla: los `BP_ICSpace_IC` del PC quedan ocultos (`WallBoot` ya no llama `SpaceReveal`).
- Cada visor tiene un número fijo del 1 al 8 (se carga al instalar, por `UECommandLine.txt`). Router propio con IP fija para el PC.

### 2.1 Cómo está hecha (2026-11-11)
| Pieza | Qué hace |
|---|---|
| `Maps/L_InnerCanvas_Wall` | El nivel del PC. GameMode `BP_ICWallGM_IC` (HUD `BP_ICWallHUD_IC`, pawn espectador). **Celda k en x = k × 1 km**: cada una con su espacio (`BP_ICSpace_IC`, sin `AutoPlace`, `BaseAlpha` 0,35), su mar y cielo (`BP_DrawSea_SC` a z −120) y su cámara **frontal** (`SceneCapture2D` en (−751, 0, 180), pitch −2,5°, FOV 30, `FinalColorLDR`: detrás de la persona, mirando lo mismo que ella; la caja de 3 × 3 m llena el cuadro y el dibujo ocupa ~75 % del ancho. Cálculo: `scratchpad cam_frontal.py`, decisión de Beltrán 2026-11-12). A 1 km, el cielo de 300 m de cada mar tapa a las demás celdas: ninguna cámara ve el dibujo de otro visor |
| `BP_ICWall_IC` | Recibe OSC/UDP en el puerto 9300 (`-ICPort=`). Por visor: sesión, nombre, fase, tiempo, tinta, trazo actual. Reconstruye cada trazo con `BP_TBStroke` (mismo `StartStroke`/`UpdatePosition` que el visor) colgado del pivote de su celda. `/ic/pr` arranca `PresStep`: des-dibuja (`Reveal` 1→0 en `PresHideT` 2 s, como el visor), `Relocate` centra el pivote en la caja de los trazos y la pone al centro de la celda a su misma altura (escala ≤ 1: `PresFit` 290 cm), vuelve a dibujar (0→1 en `PresShowT` 2,5 s) y gira (`SpinDeg` 20°/s). Una sesión mayor limpia la celda. Cada cámara dibuja en un RT de 960 × 1080 (4K / 4 × 2) |
| `BP_ICWallHUD_IC` | Dibuja los 8 RT en 4 × 2 con el número, el nombre, el tiempo (m:ss) y la barra de tinta (fases 4-13; en la presentación se ocultan) |
| Nombres | El OSC de Unreal escribe un byte por letra y al leer **extiende el signo**: la Ñ llega como U+FFD1. `OnName` devuelve Ñ y ñ (el teclado no tiene otras letras fuera de A-Z) |
| Probar sin visores | `python tools/innercanvas/simular_visores.py` (8 visores falsos; `--nueva 3` = sesión nueva en el 3) contra `probar_nivel.py /Game/InnerCanvas/Maps/L_InnerCanvas_Wall` o contra el `.exe` |
| Empaquetar | `python tools/innercanvas/empaquetar_pantalla.py` (Win64, renderer de escritorio, ~2 min) → `VR_Test/Saved/Packaged/Win64_InnerCanvas` + copia en `Recursos/Inner Canvas/Pantalla/`. `InnerCanvas_Pantalla.bat` = pantalla completa en la segunda pantalla y muestra la IP de este PC. **Primera vez: permitir el firewall en red privada** (UDP 9300) |

Probado el 2026-11-11: 8 visores falsos en `-game` y en el `.exe` empaquetado: 8 sesiones, nombres con Ñ, tiempo y tinta, trazos en vivo, presentación girando, sesión nueva en un visor que limpia solo su cuadro; 0 errores de Blueprint.

## 3. Decisiones técnicas
| Tema | Decisión | Por qué |
|---|---|---|
| Carpeta | `/Game/InnerCanvas/{Maps,Blueprints,Materials,Textures,Audio,Data}`; sufijo `_IC` | Pedido de Beltrán: no desordenar Soul Charger |
| Qué se duplica | Nivel (`L_InnerCanvas` = copia de `L_Demo_Draw`), director nuevo (`BP_ICFlow_IC`), HUD de la demo (`BP_ICHudKit_IC`), voz (`BP_ICVoice_IC`), música (`BP_ICAmb_IC`), título | Son las piezas que cambian |
| Qué NO se duplica | El sistema de dibujo (`TBDirector`, herramienta, trazos, paleta), el HUD de la Obra, el láser (`BP_SeqRig_SC`), los botones (`BP_ShareButton_SC`), el pawn | Son sistemas grandes que se referencian entre sí: duplicarlos rompe sus referencias internas. Si hace falta cambiarles algo, se agrega una **perilla nueva cuyo valor por defecto deja Soul Charger igual**, y Inner Canvas la cambia en su nivel |
| De pie | Origen de seguimiento **Stage** (centro del límite del visor), sin recentrar | El espacio 3 × 3 queda alineado con el límite físico de cada visor. Verificado en `OpenXRHMD.cpp:893`: con Stage el recentrado deja Z en el piso |
| Reinicio | **En el mismo nivel**, sin `OpenLevel` | En el Pico, los cambios de nivel de la demo quedaron colgados en un glitch de colores (nota 1 de Beltrán). Así además el recambio es inmediato |
| Frecuencia | 72 Hz pedidos por la app con el plugin PICO (`docs/PICO-EMPAQUETADO.md`) en la variante de empaquetado de Inner Canvas | Vuelve el presupuesto de 13,9 ms para el que está hecho Draw |
| Poses del Pico | Corrección del láser, del mando y de la punta del pincel solo en Pico (detección en runtime), con perillas en la línea de comandos | Ver §5 |
| Mensajes al PC | OSC/UDP, todo en floats salvo el nombre; los trazos van nudo por nudo (≤ 24 por cuadro) con posición relativa al centro del espacio | El PC reconstruye el mismo `BP_TBStroke`: el dibujo se ve igual que en el visor |

## 4. Etapas de desarrollo
Estado 2026-11-11 noche: **1.1 a 1.8 y 2 hechos y probados sin visor**; falta 3 (visor). APK: `python tools/unreal/empaquetar_obra.py --variante innercanvas` → `powershell -File tools/innercanvas/instalar_pico_ic.ps1 -Slot N -Wall <IP del PC> -Lanzar`.

1. **APK Pico** (primero)
   1. Nivel y piezas duplicadas; título y logo; botones de idioma.
   2. Teclado (`BP_ICKeyboard_IC`) y el nombre en textura.
   3. Director `BP_ICFlow_IC` (fases del guion), HUD con nombre, reloj y tinta.
   4. Espacio 3 × 3 con paredes que se encienden al acercarse.
   5. Presentación final agrandada y girando; reinicio en el mismo nivel.
   6. Envío OSC al PC (estado y trazos).
   7. Correcciones de pose del Pico.
   8. Variante de empaquetado `innercanvas` (Pico, 72 Hz, sin Meta) y prueba sin visor (`probar_nivel.py`).
2. **Build de Windows**: nivel `L_InnerCanvas_Wall` con los 8 cuadros, receptor OSC, reconstrucción de trazos, giro 360° y datos por cuadro. Prueba con 8 visores falsos (script Python).
3. Visor: Beltrán prueba en el Pico (pose, alturas, 72 Hz, legibilidad).

## 5. Poses del Pico (láser más arriba, mando y paleta ~2 cm más abajo, punta pegada al mando)
**Causa (una sola para los tres síntomas):** el láser y la punta del pincel cuelgan de la pose **Aim** del mando; la malla del mando y la paleta, de la pose **Grip**. Todos los offsets se ajustaron contra el runtime de Meta. OpenXR deja que cada runtime defina dónde y cómo apunta el aim y dónde está el origen del grip, y Unreal las entrega tal cual (`OpenXRInput.cpp:494-507`); el plugin PICO tampoco las corrige (`PICO_HMD.cpp:2137-2190`). El visor de la prueba es un **PICO 4 Ultra Enterprise** con perfil `pico4_controller`. No hay números publicados del desfase de PICO (solo reportes sueltos), así que los valores se ajustan en el visor.

**Corrección (solo en Inner Canvas, sin tocar los sistemas compartidos):** en `BP_ICFlow_IC`:
- `PicoBoot` detecta PICO (`GetVersionString` contiene "pico"; `-PicoFix=0/1` lo fuerza) y lee las perillas de la línea de comandos.
- `PicoAim`: `AimFixR/L` son MotionController **sin fuente de seguimiento** (no se mueven solos) colgados del aim real con `(PicoAimFwd, 0, 0)` cm y pitch `PicoAimPitch`. El láser (`BP_SeqRig_SC.AimR/L`) pasa a leer esos.
- `PicoTB` (mientras se dibuja): la punta (`BP_TBDirector_NC.RightAim` + `InstallTip`) cuelga del aim corregido de la mano que dibuja (el trazo sale de la punta, así que el dibujo también se corrige), y las mallas de los mandos suben `PicoGripUp`. La paleta sube lo mismo (`PaletteOffset` al arrancar).
- Valores de partida: **pitch −15°, adelante 5 cm, arriba 2 cm**. Se cambian sin reinstalar: `instalar_pico_ic.ps1 -Slot N -Wall <IP> -SoloLinea -Extra "-PicoAimPitch=-10 -PicoGripUp=1.5"`.
- **Medir en vez de adivinar:** `-Extra "-PoseDump"` imprime cada segundo `SCPOSE R/L` = el aim respecto del grip. Medido en el Quest y en el Pico (`adb logcat -s UE | findstr SCPOSE`), la diferencia da el pitch y el adelanto exactos.
- Probado sin visor (`-PicoFix=1`): dos sesiones completas, láser y punta corregidos, 0 errores. En Quest no corre nada nuevo.

## 5.b Ajustes del 2026-11-12 (Beltrán)
- **Sin mesa redonda:** se dibuja en el espacio libre. La mesa de Draw (`BP_TBTable`) sigue en el nivel porque el sistema de dibujo la usa como ancla al guardar, pero su `Disc` tiene `bHiddenInGame` en la instancia de `L_InnerCanvas`: no se ve nunca (el sistema de dibujo solo oculta y muestra el actor, y eso no la enciende). El anillo de 24 cm del piso no es la mesa: es la marca del centro del espacio (`M_ICSpace_IC`).
- **Espacio en el visor:** solo se ve la delimitación del PISO (borde y centro), también cuando la voz lo presenta. Las paredes no se ven (`BaseAlpha` 0 en la instancia; `SpaceTick` ya no les suma el pulso de la presentación) y cada una aparece solo cuando la cabeza o una mano se le acerca (`NearCm` 70).
- **HUD más arriba** (el Pico ve menos hacia abajo): `BP_SoulHUD3D_SC` de `L_InnerCanvas` pasó de (32,9 · 0 · −11) pitch −29,6 a **(32,9 · 0 · −7) pitch −23** respecto de `BP_FaceAnchor_SC` (≈ 12° bajo la vista en vez de 18,5°). Se autora moviendo el actor: el Construction Script recalcula `HeadOffsetLoc/Rot` al cargar.
- Final del visor y pantalla del PC: ver §1 filas 11-12 y §2.
- Probado sin visor: el visor en `-game` dos sesiones seguidas (presentación → 32,9 s → cierre → reinicio, 0 errores); la pantalla en `-game` y en el `.exe` con 8 visores falsos y sesión nueva en uno (0 errores).

## 6. Pendientes
- **En el visor (Beltrán):** ajustar las tres perillas de pose; 72 Hz; legibilidad del teclado y del HUD; altura del espacio y de la presentación.
- Numerar los 8 visores (`tools/innercanvas/visores_ic.json` = serie → número) y fijar la IP del PC en el router.
- En el evento: el PC y los visores en el mismo router; `InnerCanvas_Pantalla.bat` muestra la IP que va en `-Wall`.
