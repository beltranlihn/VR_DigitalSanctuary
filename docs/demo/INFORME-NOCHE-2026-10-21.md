# Informe de la noche 2026-10-21 → mañana 10-22 (Director)

Los 14 arreglos de las notas de voz, integrados y probados en Unreal sin visor (`-game` con renderer móvil, capturas y log). Detalle de cada uno: [ARREGLOS-2026-10-21.md](ARREGLOS-2026-10-21.md).

## Qué probar primero en el visor (lo que no se pudo ver sin él)
1. **Breath** entero: la respiración nueva (explicación, cuenta, 5 ciclos de 5-3-8, exhalación larga, pulmones vacíos, suspiro, vuelta a lo natural). ¿Se entiende? ¿Los tiempos se sienten bien? ¿Las voces llegan a tiempo en cada fase?
2. **Menú**: el entorno de Mind. ¿Se ve bien y anda fluido? (fps: ver abajo).
3. **Heart**: el polvo nuevo cuando la vuelta sube (y fps: el polvo tiene el doble de motas). Los dos poemas a los 60 y 100 s de la etapa.
4. **FINISH** en los tres cuadros de resultados: láser + gatillo → negro → menú.
5. Las **manos** más transparentes; el **reloj** de Draw; **paneles** y **resultados** translúcidos del color de cada experiencia.
6. **Nitidez**: menú al 120 % y Draw al 115 % (antes todo al 100 %). Si hay tirones, ver "Resolución" abajo.

## Resolución del visor (arreglo 2)
- El pawn de la obra pone la resolución al **100 %** al arrancar cada nivel (gotcha 445), por eso todo se veía blando en el visor. Las texturas ya estaban en 2048 px sin compresión: el límite era la resolución.
- Ahora cada nivel pone la suya 1 s después: **menú 120 %, Draw 115 %, Breath 100 %, Heart 100 %**. Breath y Heart no tenían margen (GPU máx 0,94 y 0,92 medido ayer en el visor).
- **Sin recompilar**, para probar otro valor en los cuatro niveles (con el visor por USB):
  `powershell -File tools/demo/quest_ip_espejo.ps1 -IP <IP del PC> -Extra "-DemoRenderPct=100"`
  (100 = como estaba ayer; 120 = todo más nítido, más caro). Sin `-Extra`, cada nivel usa su valor.

## Red (sin cambios desde ayer)
- El `UECommandLine.txt` del visor dice `-MirrorIP=192.168.137.1` (hotspot). Para el router "Alma Digital" hay que reescribirlo **con el visor por USB**: `powershell -File tools/demo/quest_ip_espejo.ps1 -IP 192.168.0.190`. `instalar_quest.ps1` instala con `adb install -r` (conserva los datos de la app, así que el archivo queda); si se desinstala la app, hay que volver a correr el script.
- La app del Muse tiene que mandar a la IP del visor en esa red (router: 192.168.0.139).

## Empaquetado (listo, sin instalar: el visor estaba desconectado)
- **APK `Demo_BDW`** 2026-10-21 21:52 (121 MB, cocinado completo de 1189 paquetes, sin errores de shaders): `VR_Test/Saved/Packaged/Android_Demo/VR_Test-arm64.apk` y copia en `Recursos/Soul Charger - Escritorio 2026-10/APK/Demo_BDW APK 2026-10-21 2152`. Instalar: `powershell -File tools/unreal/instalar_quest.ps1 -Variante demo`.
- **Robot de Windows** 2026-10-21 21:54: `VR_Test/Saved/Packaged/Win64_Robot/Robot.bat`. Probado el cocinado abriendo el menú: entorno de Mind, título, logos, START y la pista; 0 errores.
- Antes: guardia de perillas OK (valores de público, timing final de la muestra: Breath 7 ciclos / tope 170 s, Heart tope 150 s, Draw 150 s) y prueba de humo de la Obra OK (507 s, 0 errores).
- **Después de instalar**: una corrida por experiencia para calentar la caché de shaders (la primera vez el cuadro de resultados congela ~0,5 s).

## Pruebas sin visor (`-game`, renderer móvil)
- Heart completo: polvo nuevo, poemas, cuadro + FINISH, vuelta al menú. 0 errores.
- Breath completo: 149,5 s de etapa, las 13 voces en orden con subtítulo, cuadro + FINISH. 0 errores.
- Draw completo: reloj en textura, cuadro + FINISH, vuelta al menú (que aplica su 120 %). 0 errores.
- Menú: entorno de Mind, pista con START. 0 errores.
- FINISH apretado de verdad (láser + gatillo) no se pudo probar sin mandos: queda para el visor.

## Cierre de Unreal (22:00)
- Todo lo de la noche quedó **guardado**. Al cerrar, Unreal pidió guardar solo `BP_BreathStage_SC` y `BP_Pacer_SC`, que quedaron "sucios" por LEER sus grafos (no los modifiqué): la respuesta correcta es **Don't Save**.
- No pude apretarlo: el panel de entrada de Windows (TextInputHost) quedó adelante y la herramienta de control de pantalla no deja hacer clic con una app no autorizada al frente. Unreal quedó **parado en ese diálogo** (sin renderizar el visor: casi no usa GPU).
- El apagado de la noche (`shutdown /s /t 120`) cierra las apps a la fuerza. **Al abrir Unreal mañana, si ofrece "Restore" de paquetes, elegir "Skip Restore"** (lo único pendiente son esas dos lecturas; "Restore" pisaría los `.uasset`).

## Sin commit
Todo está guardado en disco, sin commit (no lo pediste para esta tanda). Cuando lo pruebes y te guste: `/commit`.
