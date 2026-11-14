# El robot: la demo en Windows siguiendo al visor

Un PC muestra en pantalla lo que vive la persona con el Quest, **sin streaming**: el Quest manda por OSC (wifi, router local) su cabeza, sus mandos, sus botones y el estado de la experiencia, y el PC corre **la misma demo** moviendo la cámara y los mandos del VR Pawn con esos datos. Las mecánicas corren solas en el PC, por eso se ve igual.

## Cómo está armado
- Actor `BP_MirrorLink_SC` en los 3 niveles de la demo (tracker: `.claude/skills/unreal-vr/blueprints/BP_MirrorLink_SC.md`).
- Con visor → **emisor**. Sin visor → **receptor** (el robot se lanza forzado: `-nohmd -unattended -MirrorRole=2`).
- Mensajes (UDP **9000**): `/sc/pose` (cabeza + 4 mandos), `/sc/in` (gatillos, grips, botones, sticks), `/sc/st` (9 floats: fase y elección del menú; fase del director de la experiencia y mano elegida; slot 4 = índice de calma % del Quest, −999 sin índice; slot 5 = 2.0, marca de protocolo; slots 7-8 = actividad neuronal y BPM del Muse del Quest, −1 sin Muse), `/sc/lvl` (nivel).
- 🔴 **Gatillos del Quest** (19-10): en el visor las teclas XR no llegan a `IsInputKeyDown`/`GetInputAnalogKeyState`, así que el emisor toma los gatillos de los eventos **`IA_Shoot_Left/Right`** (`AutoReceiveInput` Player0): `TrigL` → canales 0 y 13, `TrigR` → 1 y 14 de `/sc/in`. Grips, botones y sticks siguen por el camino viejo (en el visor llegan en 0; el robot no los necesita para la demo). ⬜ verificar en el visor que el robot dibuje.
- **Muse en el robot** (19-10): el Muse le llega solo al Quest; el Quest manda calma y BPM en `/sc/st` y el robot se los pasa a su `BioHub` con `Ingest` (HUD y resultados del robot con datos).
- El robot:
  - **mueve** cámara y mandos del pawn e **inyecta** gatillos y grips (dibujo, presión, animación del mando);
  - **sigue el estado**: si se atrasó o perdió un clic, aprieta lo que falta en el menú; en las experiencias (guion v2, `BP_DemoFlow_SC`) toma el sensor o el mando con la misma mano que el visor, pasa las páginas, aprieta START, corta el trazo de práctica y pide el cierre cuando el visor ya lo hizo;
  - **cambia de nivel cuando el visor cambia**: ni el menú (fase 10) ni el director de la experiencia (fin) abren niveles en el robot; los abre `LevelStep` cuando el Quest aterriza. Si el Quest no llega en 30 s después del negro del menú, el robot vuelve a su menú;
  - **espera la pose** al entrar a una experiencia: `BP_DemoFlow_SC` no corre su reloj hasta tener la primera pose del Quest (el Quest todavía carga el nivel);
  - **respiración**: abre el umbral con la pose recibida (`bIgnoreTracking` en runtime, solo en el robot);
  - **pantalla**: cámara de espectador suavizada, sin rolido, FOV 90 (la cámara del pawn queda exacta para las mecánicas).

## Estado de la conexión en pantalla (2026-10-20 noche)
Pedido de Beltrán: que el robot diga si el Quest y el PC están conectados. `BP_MirrorLink_SC` (solo con `-MirrorRole=2` explícito, o sea `Robot.bat` y el arnés) pone un cartel (`WBP_MirrorStatus_SC`) sobre la ventana:
- **Todo bien**: una línea verde chica arriba a la izquierda: `LINK OK  178 msg/s  Quest 192.168.x.x  [Tab] details`.
- **Sin datos del Quest**: la línea dice `QUEST: no data for N s`; a los **8 s** (`WarnAfter`) sale un **recuadro rojo** al centro: `WAITING FOR THE QUEST` (nunca llegó nada) o `QUEST LINK LOST`, con **la IP de este PC que hay que darle al Quest** y el puerto (UDP 9000). Una carga de nivel del Quest (unos segundos sin mensajes) no alcanza a encenderlo.
- **Tab** (con la ventana del robot enfocada: un clic en ella; Alt+Tab para recuperar el mouse): compacto → detalle (PC, QUEST con IP / mensajes por segundo / último mensaje, STATE = nivel y fases del visor, BIO = calma y BPM que manda el Quest) → oculto.
- La IP de este PC la calcula `Robot.bat` (`mi_ip.ps1`: el primer adaptador activo con puerta de enlace) y se la pasa al robot con `-MirrorMyIP=`. Si dice `unknown` (router sin internet), escribirla a mano en el `.bat` (`set MYIP=192.168.x.x`). Si el PC tiene cable y wifi a la vez puede mostrar la del otro adaptador: la buena es la de la misma red que el Quest (la línea QUEST muestra la IP del Quest para comparar).
- **Vigía de enlace**: sin mensajes por 3 s (`LinkTimeout`), el robot suelta gatillos y grips (deja de dibujar); vuelve solo con el próximo mensaje. El delta está acotado a 0,1 s por cuadro: un tirón del robot no la dispara.
- Fuente: `VR_Test/Saved/ClaudeScripts/Demo2/mirror_status_dsl.py` (+ `mirror_status_wbp_dsl.py`), diseñado y verificado por un workflow de agentes de solo lectura.

## La app del sensor (Muse) y el robot en el mismo PC
- La app del sensor manda **solo al Quest** (IP del Quest, UDP 10000). **No hay que cambiarle nada** para el robot: el Quest le reenvía actividad neuronal, BPM (slots 7-8) e índice de calma (slot 4) dentro de `/sc/st` y el robot los mete en su BioHub.
- **Muse Integration 0.3** (20-10 noche): manda `/muse/alpha` (gráfico del HUD), `/muse/heart_rate`, `/muse/sensor_active` y el **índice de calma** `/muse/calm_index` (% con signo vs la calibración) + `/muse/calm_quality`. El cuadro de resultados del Quest y del robot muestra `CALM INDEX +N%`. Detalle del canal en el tracker de `BP_BioHub`.
- **No** sumar el PC como destino (localhost, la IP del PC o broadcast): el BioHub del robot también escucha UDP 10000 y recibiría el dato dos veces.
- Si la app del sensor **escucha** en algún puerto UDP de ese PC, que no sea 9000 ni 10000 (son los del robot).
- Reservar IP fija también para el **Quest** (la app del sensor apunta a ella) y poner la red del PC como **Privada** en Windows (o permitir el robot en redes públicas y privadas en el firewall): en una red "Pública" el permiso de redes privadas no aplica y el robot se queda en `WAITING FOR THE QUEST`.
- **Señal simulada = respaldo** (20-10 noche): el BioHub de los niveles demo simula solo cuando no llega el sensor real por 2 s (`FakeHold`); el robot nunca simula: muestra lo que manda el Quest (real o simulado allá). Prueba sin sensor: `python tools/demo/muse_falso.py --ip <IP del Quest>`.

## Armar el robot
```
python tools/unreal/empaquetar_robot.py
```
Deja `VR_Test/Saved/Packaged/Win64_Robot/Robot.bat` (ventana 1920×1080, renderer móvil como el Quest). `--escritorio` para el renderer de PC.

## ✅ Probado con el Quest real por el hotspot del laptop (2026-10-20, 23 h)
La wifi de invitados del lab (`BCN_XRLab_Guest`) **aísla a los equipos entre sí** (aislamiento de clientes: el Quest no resuelve al PC por ARP; 0 mensajes al robot). Solución de Beltrán: **el laptop comparte un hotspot de Windows y el Quest se conecta a él**. Así el laptop es el router y no dependemos de la red del lugar.
- PC (hotspot) `192.168.137.1` · Quest `192.168.137.165` (la asigna el hotspot; mirarla en la lista de dispositivos del hotspot o en la línea QUEST del robot).
- Resultado: `MIRROR: emisor -> 192.168.137.1` en el Quest; el robot "LINK OK, Quest 192.168.137.165", ~110-125 mensajes/s con el visor sin poner (puesto debería acercarse a 180), siguió el menú del visor; 0 errores de Blueprint.
- **Sensor por el mismo camino**: `muse_falso.py` desde el laptop a la IP del Quest (UDP 10000) → el Quest "BIO: Muse real (el simulado se apaga)" → el robot mostró "BIO from the Quest calm 37 bpm 71". La app del sensor real hace lo mismo: mandar a la IP del Quest en el hotspot.
- `mi_ip.ps1` (al lado del robot) prefiere la IP del hotspot (`192.168.137.x`) si existe: el recuadro rojo del robot muestra la IP correcta para el Quest.
- El Quest ya quedó con `-MirrorIP=192.168.137.1` (`UECommandLine.txt`): con el mismo laptop y su hotspot no hay que volver a configurarlo.

### Paso a paso para la feria
1. En el laptop: Configuración → Red → Zona con cobertura inalámbrica móvil (hotspot) → activar.
2. En el Quest: conectarse a la red del hotspot.
3. Si es otro laptop o el hotspot no es `192.168.137.1`: `powershell -File tools/demo/quest_ip_espejo.ps1 -IP <IP que muestra el robot>` (Quest por USB).
4. App del sensor → IP del Quest en el hotspot, UDP 10000.
5. `Robot.bat` en el laptop (si Windows pregunta por el firewall: permitir) y la demo en el Quest. El robot pasa a verde.

## Router "Alma Digital" (2026-10-21, red local sin internet)
- Quest `MetaQuestAlma` **192.168.0.139** · laptop `BeltranLaptop` **192.168.0.190** (lista de dispositivos inalámbricos del router). Conviene **reservar las dos IP** en el router: si cambian, el Quest manda a una IP vieja.
- El Quest quedó con `-MirrorIP=192.168.0.190` (`quest_ip_espejo.ps1 -IP 192.168.0.190`, por USB; queda guardado sin cable).
- `mi_ip.ps1` prefiere ahora la `192.168.0.x` (activa), después el hotspot `192.168.137.x`, después el adaptador con puerta de enlace: abrir `Robot.bat` **después** de conectar el laptop a esa wifi.
- La app del sensor (Muse Integration 0.3.2) manda a `192.168.0.139:10000` (`settings.json`, usuario 1). Su puerto de control es 9000 pero solo en `127.0.0.1`: no choca con el robot (que escucha 9000 en `0.0.0.0`).
- El firewall de Windows está apagado en los tres perfiles: no bloquea al robot.
- Abrir la app del Quest **con el visor puesto**: si arranca sin cabeza, el menú queda 120 cm abajo (`DEMO: menu ubicado, dz = -120`).

## Conectar el Quest con el robot
1. PC y Quest en el mismo router. **Fijar la IP del PC** (reserva DHCP en el router). La primera vez que se abre `Robot.bat`, Windows pregunta por la red: **permitir en redes privadas** (UDP 9000).
2. Decirle al Quest la IP del PC, sin recocinar (visor conectado por USB una vez):
   ```
   powershell -File tools/demo/quest_ip_espejo.ps1 -IP 192.168.x.x
   ```
   Queda guardada en el visor (archivo `UECommandLine.txt` del juego). `-Lanzar` además abre la demo. `-Borrar` la quita. ✅ Verificado en el visor (20-10 noche): abriendo la app normalmente, el logcat dice `Override Commandline: ... -MirrorIP=<IP>` y `MIRROR: emisor -> <IP>`, y llega al menú. (`-Lanzar` usaba `SplashActivity`, que no existe en este APK: ahora `GameActivity`.)
   Alternativa: perilla `TargetIP` de `MirrorLink` en los 3 niveles y reempaquetar el APK.
3. Abrir `Robot.bat` en el PC y la demo en el Quest. El robot sigue al visor de nivel en nivel.

## Probar sin visor
```
python tools/demo/probar_robot.py --emisor guion --guion cierre_draw --segundos 150
```
Escenas del Quest falso (`tools/demo/mirror_test_send.py`): `menu` (solo clics), **`sync_menu`** (solo estado, ningún clic; el visor abre Draw a los 54 s: el robot tiene que esperar en negro sin abrir nada), **`flujo_breath`** / **`flujo_draw`** (ya en la experiencia: las fases del director nuevo; en Draw, un trazo de práctica con el gatillo), **`flujo_draw_izq`** (lo mismo con la mano izquierda), **`cierre_draw`** (Draw entero: práctica, dibujo con el gatillo en la sesión, el visor termina, resultados, y el visor vuelve al menú a los 128 s: el robot espera al visor). `sesion_draw` y `sesion_breath` son del panel viejo (antes del 19-10): ya no sirven.
Sin robot empaquetado, el receptor también se prueba como proceso del juego:
```
python tools/demo/mirror_test_send.py --guion flujo_breath --segundos 60 --retardo 11
python tools/unreal/probar_nivel.py /Game/SoulCharger/Demo/Maps/L_Demo_Breath --segundos 78 --extra="-MirrorRole=2" --filtro "DEMOFLOW|MIRROR"
``` `--emisor juego` prueba el código del EMISOR real (un proceso del juego forzado a emitir). El arnés lanza el robot empaquetado, corre el guion, resume los logs y cierra todo. Tiene que dar `errores de Blueprint: 0`.

## Probado (2026-10-16)
Menú por clics y por estado; Draw completo (el robot guardó y presentó el dibujo a los 150 s); Breath (umbral abierto, puntaje 0,96 en el primer ciclo); emisor real a ~170 mensajes/s. Todo con 0 errores.

## Probado (2026-10-19, guion v2)
Receptor en `-game` con `flujo_breath`: toma con la derecha → páginas → START → StageIntro → StageBegin → pacer. Con `flujo_draw`: toma → trazo de práctica dibujado por el gatillo inyectado → corte → reloj. 0 errores. Robot reempaquetado el 19-10.

## Probado (2026-10-19, noche)
Receptor en `-game` con el Quest falso: `cierre_draw` (toma, práctica, **dibujo en la sesión con el gatillo inyectado** — antes no dibujaba, ver el candado de la práctica en la ficha de `BP_DemoFlow_SC` —, presentación, corrimiento a la derecha, resultados con 14 casillas del Muse retransmitido, vuelve al menú siguiendo al visor), `flujo_draw_izq` (toma y trazo con la izquierda), `flujo_breath` (hasta el pacer), `sync_menu` (el robot llega al negro, espera 16 s y entra a Draw cuando el visor cambia de nivel, sin rebote). Todo con 0 errores de Blueprint.
**Robot empaquetado (19:01)** con `probar_robot.py --emisor guion --guion cierre_draw`: dibuja en la sesión, presenta, se corre, negro, `DEMOFLOW: robot espera al visor (no abre el menu)` y 18 s después sigue al visor al menú. **Emisor real** (`--emisor juego`): ~185 mensajes/s = 60 Hz. 0 errores.

## Pendiente
- Prueba con el Quest real (emisor) y medir el costo en el visor. Lo primero a mirar: que el robot dibuje (gatillos por `IA_Shoot`).
- La presión del gatillo llega al robot como 0/1 (el eje analógico no viaja por `IA_Shoot`): en la pantalla los trazos salen a presión plena.
- El emisor manda a `SendHz` (60) desde el 19-10 (antes 36 Hz: reiniciaba el acumulador).
- Vigía de enlace (20-10 noche): a los 3 s sin mensajes suelta gatillos y grips; la pose queda congelada y el director del robot sigue su reloj hasta el próximo cambio de nivel del Quest.
- Reempaquetar **los dos juntos** (APK y robot): `/sc/st` pasó de 7 a 9 floats el 19-10.
- Verificar `quest_ip_espejo.ps1` en el visor.
- ✅ (20-10 noche) El HUD en el robot cuelga de `SpecCam` (antes de la cámara del pawn: se salía de cuadro al mover el casco) y el mesh del visor del pawn queda oculto.
- Los puntajes y resultados se calculan en el robot con la pose recibida: pueden diferir un poco de los del Quest. Si importa, mandar los puntajes del Quest en `/sc/st`.

## Pantalla completa en la segunda pantalla (2026-10-22, feria)
- `Robot.bat` abre el robot **a pantalla completa sin bordes en la segunda pantalla** (`-fullscreen` + `-WinX/-WinY/-ResX/-ResY` del monitor que no es el principal, que calcula `pantalla.ps1`; con una sola pantalla usa la principal). `Robot_ventana.bat` = el de antes (ventana 1920×1080 con borde). Lo genera `tools/unreal/empaquetar_robot.py`.
- Copia lista para usar en el escritorio: `Soul Charger Demo - Windows` (doble clic en `Robot.bat`).
- 🔴 **Abrirlo con doble clic, no desde Claude**: un proceso lanzado desde la terminal de Claude es hijo de la app y se cierra si la app se actualiza o reinicia (22-10, 13:53: el robot se cerró en medio de Heart justo cuando se actualizó Claude).
- El robot escucha en todas las redes (UDP 9000): si se cambia de wifi con el robot abierto, sigue recibiendo; solo el cartel de conexión muestra la IP vieja.
