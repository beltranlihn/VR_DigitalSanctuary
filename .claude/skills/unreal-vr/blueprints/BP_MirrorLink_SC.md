# BP_MirrorLink_SC — el enlace visor → robot de Windows (OSC)

- **refPath**: `/Game/SoulCharger/Demo/Blueprints/BP_MirrorLink_SC` · parent Actor (+ `SpecCam`, CameraComponent) · creado 2026-10-16 (sesión Director, pedido de Beltrán: "el clon/robot que corre en Windows").
- **Colocado en**: `L_Demo_Menu`, `L_Demo_Breath`, `L_Demo_Draw` (label `MirrorLink`, en el origen).
- **Estado (2026-10-16)**: 🟢 robot empaquetado (Win64, renderer móvil ES3.1) verificado con un **Quest falso** (`tools/demo/mirror_test_send.py`, escenas `menu`, `sync_menu`, `sesion_draw`, `sesion_breath`) y con el **emisor real** corriendo en un proceso sin visor (`-MirrorRole=1`); 0 errores de Blueprint en todas. ⬜ emisor desde el Quest real (falta visor) · ⬜ costo en el Quest.

## Idea
El robot es **el mismo build de la demo en Win64**. No hay otro pawn: el receptor **mueve la cámara y los 4 MotionController del VR Pawn** con lo que manda el visor, **inyecta el input** (Enhanced Input `InjectInputVectorForAction`) y **sigue el estado** del visor (menú, panel, reloj del ensayo). Las mecánicas leen el pawn y su input, así que en Windows corren iguales sin tocarlas.

## Rol (`Boot`)
`MirrorRole` 0 = automático (`IsHeadMountedDisplayEnabled` → 1 emisor, si no → 2 receptor) · 1 emisor · 2 receptor · −1 apagado. Línea de comandos: `-MirrorRole=N` y `-MirrorIP=x.x.x.x` pisan las perillas. El robot se lanza con `-nohmd -unattended -MirrorRole=2` (`Robot.bat`). En el Quest la IP se pasa sin recocinar con `tools/demo/quest_ip_espejo.ps1` (⬜ verificar en el visor).

## Mensajes OSC (UDP, `Port` 9000) — todos los manda el emisor cada `1/SendHz` (60 Hz) salvo `/sc/lvl`
| Dirección | Contenido |
|---|---|
| `/sc/pose` | 30 floats: cámara, grip L, grip R, aim L, aim R → `x y z pitch yaw roll` en MUNDO |
| `/sc/in` | un float por cada `Keys` (15): `max(GetInputAnalogKeyState, IsInputKeyDown)` |
| `/sc/st` | 9 floats (desde 19-10): `Phase` y `Choice` del menú · `Phase` del director (`BP_DemoFlow_SC`) y mano (1 derecha, 0 izquierda) · 4-6 sin uso (eran el ensayo viejo) · calma y BPM del Muse del Quest (−1 si no hay) |
| `/sc/lvl` | string `GetCurrentLevelName`, cada 0,25 s |

`Keys`: 0 trig L · 1 trig R · 2 grip L · 3 grip R · 4 X · 5 Y · 6 A · 7 B · 8 menú L · 9-10 stick L · 11-12 stick R · 13 clic trig L · 14 clic trig R.
Inyección (`InjActions` / `InjChan` / `InjBool`): `IA_Shoot_Right/Left` ← 14/13 (bool) · `IA_Hand_IndexCurl_R/L` ← 1/0 · `IA_TB_Pressure_R/L` ← 1/0 · `IA_Hand_Grasp_R/L` ← 3/2.

## Receptor, en orden (Tick)
1. `ApplyStep`: pose a cámara y mandos; `bPoseReady` = `RxCount > 30`; `Inject` (con `UiGate`).
2. `LevelStep`: cambia de nivel **cuando el nivel del visor CAMBIA** (`LastRemote`), no por cualquier diferencia → el robot no rebota si carga un nivel una fracción antes que el Quest.
3. `RxLog`: "mensajes recibidos N" cada 2 s.
4. `FollowStep` (`bFollow`): **sincronización de estado** (el robot se corrige si se atrasó o perdió un clic)
   - `FollowMenu`: local 2 y visor ≥ 3 → `Choose(0)` (START) · local 4 y visor ≥ 6 → `Choose(Choice)` · local 4 y visor 5 o 2 → `Choose(0)` (BACK).
   - `FollowInstr`: panel local en `St` 1 y el visor con página mayor o ya terminado → `Press` + `St` 2 (la misma ruta que un clic).
   - `FollowRunnerRT/PT`: misma fase y |ΔRT| > 0,5 → `RT` del visor; fases 0-1 atrasadas → `RT`; misma fase ≥ 3 y |ΔPT| > 0,5 → `PT`; local en 3 y el visor ya en ≥ 4 → `PT = TimeoutS` (la etapa cierra con él).
5. `SpecStep` (`bSpectator`): **cámara de espectador** `SpecCam`, view target del robot: sigue la cabeza con `VInterpTo`/`RInterpTo` (`SpecLag` 5, `SpecRotLag` 4), **sin rolido**, FOV `SpecFOV` 90. La cámara del pawn queda exacta (la usan las mecánicas).

`EnsureRig` → `FindRig` (cámara, mandos por `MotionSource`, `MenuRef`/`InstrRef`/`RunnerRef`) → `RobotSetup` (solo receptor): `RobotRunner` (`Loop` false: el ensayo del robot NO vuelve al menú solo, espera al visor) y `RobotBreath` (`BP_BreathRig_SC.bIgnoreTracking` true: el umbral de respiración abre con la pose recibida; sin esto los mandos del robot figuran "no trackeados" y nunca abre).

## `UiGate`: en menú y panel los clics los decide el ESTADO
Mientras hay menú o el panel no terminó (`St` < 3), los `InjBool` (`IA_Shoot`) se inyectan en 0. Si no, un clic llegaba dos veces (por estado y por gatillo) y el robot saltaba una página. Después del panel vuelve a inyectarse: el dibujo lo necesita.

## Pruebas (2026-10-16, robot empaquetado)
| Prueba | Resultado |
|---|---|
| emisor real (`probar_robot.py --emisor juego`) | ~170 mensajes/s; el robot ubicó el menú con la altura de la cabeza recibida |
| `sync_menu` (ningún clic, solo estado) | START y SURROUNDING elegidos por `FollowMenu` → Draw |
| `sesion_draw` | panel por `FollowInstr` (3 páginas), dibujo inyectado; el robot se quedó sin tinta antes que el Quest falso, volvió solo al menú (eso ya no pasa: `RobotRunner`), lo trajo de vuelta la sincronización y cerró a los 150 s "se guarda el dibujo y se presenta" |
| `sesion_breath` | `UMBRAL IN` 1,6 s después de StageBegin, puntaje 0,96 en el primer ciclo (los siguientes bajan porque el seno del guion no sigue a la guía) |

## Trampas de la construcción
- `Role` choca con `AActor::Role` → la perilla se llama `MirrorRole`.
- `==` no compara strings en el DSL: `Utilities|String|EqualExactly(String)` / `NotEqualExactly(String)`. `MakeArray` no acepta N literales: armar con `Clear` + `for` + `Add`.
- El evento del `Assign` se crea con el `write`; su cuerpo se conecta por cirugía (`HandleOsc`). Un `write` fallido deja un evento viejo sin parámetros: borrarlo.
- `read_graph_dsl` etiqueta mal llamadas propias y setters de otras clases (`Class|BPAlmaSC|Boot`, `BlendSpacePlayer|SetLoop`, `BPSoulPickerSC|Choose`): verificar con `get_node_infos` (tipo del pin `self`).
- Literales en nodos aparte (`MakeLiteralFloat`): para cambiar un número por cirugía, seguir el cable del pin B.
- El `.exe` empaquetado es un lanzador que abre otro proceso: para cerrarlo, `taskkill /T` o por nombre. Con `MSYS_NO_PATHCONV=1` en Git Bash, `taskkill //IM` deja de funcionar (por eso el arnés es Python).
- El robot muestra un "Handled ensure" de PSO precache (renderer móvil en PC) al arrancar: es inofensivo, pero sin `-unattended` una vez quedó colgado en el diálogo.
- Multicast/broadcast no sirven para no configurar IP: el cliente OSC no habilita broadcast y el servidor hace `Bind` a la dirección multicast, que Windows rechaza.


## 2026-10-19 — el robot sigue al director nuevo (`BP_DemoFlow_SC`)
- Fuente: `VR_Test/Saved/ClaudeScripts/Demo2/mirror_dsl.py`. Variable nueva `FlowRef`; funciones `FindFlow`, `StFlow`, `UiFlow`; reescritas `GatherState` (+ `StFlow`) y `UiGate`.
- `/sc/st` slot 2 = `Phase` del director, slot 3 = mano (1 derecha). El robot NO escribe en el director (el catálogo no ve sus variables nuevas): **el director lee `RStF`** (`BP_DemoFlow_SC.RemoteSync`) y avanza cuando el visor ya avanzó.
- `UiGate`: clics bloqueados en el menú y en la página START de Breath (`Exp` 0, fase 5); en Draw el gatillo pasa (el trazo de práctica se dibuja en el robot).
- `StInstr`/`StRunner`/`FollowInstr`/`FollowRunner*` quedan pero no hacen nada (ya no hay panel viejo ni ensayo en los niveles).
- Quest falso: guiones nuevos `flujo_breath` y `flujo_draw` (`tools/demo/mirror_test_send.py`). Probado con el receptor en `-game` (`--extra="-MirrorRole=2"`): Breath toma → páginas → START → StageIntro → StageBegin → pacer; Draw toma → práctica dibujada por el gatillo inyectado → reloj. 0 errores.

## 2026-10-19 (noche): gatillos del Quest, Muse y limpieza
- 🔴 **El emisor leía los botones con `IsInputKeyDown`/`GetInputAnalogKeyState`**, que en el visor dan 0 para las teclas XR (assets-existentes.md): el robot no habría dibujado. Ahora los eventos **`IA_Shoot_Left/Right`** (creados por cirugía, Triggered → `ShootXOn`, Completed → `ShootXOff`) llenan `TrigL`/`TrigR`, y `BuildInput` los suma a los canales 0/13 y 1/14. CDO `AutoReceiveInput` = **Player0**. Fuente: `Demo2/mirror_input_dsl.py`. (Enhanced Input no consume la acción entre componentes: `bShouldCheckForLegacyKeyConsumption` es false por defecto, verificado en el motor 5.8.)
- **Muse**: `/sc/st` de 9 floats (7 = calma, 8 = BPM del BioHub del Quest; −1 sin Muse). El receptor los pasa a su BioHub con `Ingest` (`RelayBio`). Fuente: `Demo2/mirror_bio_dsl.py`.
- **Limpieza** (cargaba media Obra en cada nivel): fuera `InstrRef`/`RunnerRef` y los cuerpos de `StInstr`, `StRunner`, `FollowInstr`, `FollowRunnerRT/PT`, `RobotRunner` (quedan como funciones vacías); `FindRig` ya no busca el panel viejo ni el ensayo. Ningún asset de la demo referencia `BP_StageRunner_SC`/`BP_DemoInstr_SC`/`BP_Obra_SC`.
- Pendiente: vigía de enlace (si el Quest deja de emitir, el robot conserva el último gatillo/pose).
- `SendStep` (fuente `Demo2/mirror_send_dsl.py`): resta el período en vez de poner `SendT` en 0 → manda a `SendHz` (60) y no a 36 Hz a 72 fps; tope de un período para no acumular atraso.
- **Orden de las fuentes** para reconstruir el enlace: `mirror_dsl.py` (FindFlow, StFlow, UiFlow) → `mirror_bio_dsl.py` (GatherState y UiGate vivas, con el Muse) → `mirror_input_dsl.py` → `mirror_send_dsl.py`; los eventos `IA_Shoot_*` se crean por cirugía.
- Perillas que la guardia revisa en los 3 niveles: `MirrorRole` 0 y `bLevelSync` true.

## 2026-10-20 — Heart en el robot
- `RobotHeart` (en `RobotSetup`, receptor): `HMRef` = el `BP_HeartManager_SC` del nivel → `bIgnoreTracking` true. Sin esto, en Windows el umbral del pecho no abre (el manager exige tracking válido) y el robot solo latía con el respaldo de 30 s. Fuente `Demo2/mirror_heart_dsl.py`.
- Quest falso: guion `flujo_heart` (mano derecha quieta en el pecho desde la página 1). Probado: `UMBRAL IN h=8,9 v=30` apenas el `StageBegin`, latidos, voces, cierre, manos de vuelta, resultados; 0 errores.

## 2026-10-20 (noche) — estado de la conexión en pantalla, vigía de enlace y Muse del robot
- Pedido de Beltrán: "algún visor que nos diga que tanto la Quest como el proyecto del computador están conectados". Diseño y verificación: workflow `robot-link-and-review` (agentes de solo lectura); fuente `Demo2/mirror_status_dsl.py`.
- Widget nuevo **`WBP_MirrorStatus_SC`** (Demo/Blueprints): `BoxOk`/`TxtOk` (línea verde arriba a la izquierda), `BoxInfo` (`TxtPC`, `TxtQuest`, `TxtState`, `TxtMuse`), `BoxWarn` (rojo al centro: `TxtHead`, `TxtBody1`, `TxtBody2`). Función **`Show(WarnA, OkA, InfoA, Ok, Head, B1, B2, PC, Quest, State, Muse)`** (fuente `mirror_status_wbp_dsl.py`): el enlace la llama con todo armado (las variables de los hijos de otra clase no se ven en el catálogo; las funciones nuevas sí, una vez que existe una variable de ese tipo: `StW`).
- Variables nuevas (Default): `StW`, `SenderIP`, `MyIP` ("?"), `RxAge` (0), `RxRate`, `RxPrev`, `RateT`, `StT` (1), `bLinkLost` (true), `LinkTimeout` 3 · `WarnAfter` 8 · `StatusView` 0 (editables), `StStr`, `MuStr`.
- Funciones nuevas: `NoteRx(Ip)` (insertada **por cirugía** en el EventGraph: `OnOscMessageReceived_Event_0 → NoteRx(IPAddress) → HandleOsc`), `ZeroInput`, `LinkStep`, `AddStatus`, `EnsureStatus` (lee `-MirrorMyIP=`, crea el widget una vez por nivel), `DrawState` (lee `/sc/st` solo con 9 floats: sin "Attempted to access"), `DrawStatus`, `StatusStep` (Tab cicla compacto/detalle/oculto; refresco cada 0,25 s). `RxLog` (rama Mode 2 del Tick) llama `LinkStep` siempre y `StatusStep` solo con **`MirrorRole` == 2 explícito** (en PIE de escritorio / `probar_nivel` sin visor el Mode 2 es automático y no aparece el cartel).
- Vigía: `RxAge` crece con el delta acotado a 0,1 s; > `LinkTimeout` → `bLinkLost` + `ZeroInput` (InF = 15 ceros: el robot suelta gatillos/grips) y `MIRROR: sin enlace con el Quest ...`; vuelve con `MIRROR: enlace con el Quest desde <IP>`.
- `RelayBioOne` (fuente `mirror_bio_dsl.py`): además apaga `bFakeSignal` del BioHub del robot (`Class|BPBioHub|SetFakeSignal`) en cuanto llega `/sc/st` de 9 floats: el robot muestra solo lo del Quest. No va en `RobotSetup`: ese corre también en PIE de escritorio (Mode 2 automático) y apagaría el simulado ahí.
- Probado (editor `-game`, Quest falso `cierre_draw` con `--pausa 30:36`): cartel creado en cada nivel con la IP 127.0.0.1, ~178 msg/s, vigía a los 3 s de pausa y reenganche, el dibujo termina y se presenta; 0 errores de Blueprint.
- Herramientas: `Robot.bat` pasa `-MirrorMyIP=%MYIP%` (`mi_ip.ps1` al lado del .exe); `probar_robot.py` pasa `-MirrorMyIP=127.0.0.1`; `mirror_test_send.py --pausa INI:FIN`.

## 2026-10-20 (noche, 4.ª tanda) — índice de calma al robot, HUD en la cámara de espectador, visor del pawn oculto
- **`/sc/st` slot 4 = índice de calma** del Quest (−999 = sin índice) y **slot 5 = 2.0** (marca de protocolo: un APK viejo manda −1 ahí y el robot lo ignora). `ResetSt`: 9 × −1, slot 4 −999, slot 5 2.0. `StBio` (emisor): slot 4 = `select(GetCalmIdxSeen, GetCalmIdx, −999)`. `RelayBioOne` (robot): con slot 5 ≥ 1,5 y slot 4 > −500 → `SetCalmIndex(slot4)` del BioHub del robot, si no `ClearCalmIndex`. Fuente `mirror_bio_dsl.py`.
- `DrawState`: la línea BIO del detalle dice `BIO from the Quest neural N bpm N calm index ±N%` ("--" sin índice).
- **HUD en el robot** (Beltrán: "si muevo el casco el HUD a veces se ve, a veces no"): el HUD cuelga de la cámara del pawn (pose exacta del visor) y la pantalla usa `SpecCam` suavizada. `RobotHud` (rama del robot de `RxLog`, con la vista de espectador encendida) busca `BP_SoulHUD3D_SC` y `RobotHudGo` lo re-cuelga de `SpecCam` conservando su transform relativo a la cámara del pawn, más `HudUp` (7°, editable) de cabeceo hacia arriba. Variables nuevas `HudRef`, `bHudSpec`, `HudUp`.
- **Visor del pawn oculto** (Beltrán: "se ven pedazos del mesh del visor"): `HideHmd` oculta en juego los `StaticMeshComponent` del pawn cuyo nombre contiene `HeadMountedDisplay`. Log: `MIRROR: HUD en la camara de espectador y visor del pawn oculto`.
- Fuente: `mirror_status_dsl.py` (`RobotHud`, `RobotHudGo`, `HideHmd`, `RxLog`, `DrawState`). Quest falso: `mirror_test_send.py` manda slot 4/5 en los guiones de Heart y flujo.

## 2026-10-21 (tarde) — manos suavizadas en el robot
- Beltrán, con el router "Alma Digital": la cabeza se ve fluida pero las manos "entrecortadas, se nota mucho en el dibujo". Causa: la cabeza que se ve es `SpecCam` (`SpecStep`, `VInterpTo`/`RInterpTo`); los mandos (`MCLG`/`MCRG`/`MCLA`/`MCRA`) se ponían en la pose del último paquete cada cuadro, y por wifi los paquetes llegan a ráfagas.
- `ApplyStep` (fuente `Demo2/mirror_smooth_dsl.py`, respaldo de la versión anterior en `Demo2/readback_mirror_apply.txt`): la cámara del pawn sigue exacta; cada mando sigue a la pose recibida con `VInterpTo`/`RInterpTo` a **`HandLag`** (variable nueva, categoría `Spectator`, editable, 14/s ≈ 70 ms) y salta directo si la diferencia pasa de 60 cm (primer paquete, cambio de nivel). El dibujo del robot sale de esos mandos: también queda suave.
- Probado con el Quest falso (`probar_robot.py --guion sesion_draw --extra="--ip 192.168.137.1"`): 178 msg/s, toma con la derecha, trazo de práctica (2 trazos), arranca el reloj; 0 errores.
- 🔴 Prueba local: con Muse Integration abierta (su puerto de control es 9000 en `127.0.0.1`), lo que se manda a `127.0.0.1:9000` le llega a la app, no al robot (0 mensajes). Mandar el Quest falso a una IP de red del PC (`--extra="--ip <IP>"`). El Quest real manda a la IP de red y llega bien.
