# Workflow de equipo — trabajar en paralelo sin pisarnos

Dos (o más) devs trabajando el mismo proyecto Unreal, cada uno en **su stage**. El enemigo #1 son los **`.uasset`/`.umap` binarios**: git **no los puede mergear**. Si dos personas editan el mismo asset, uno de los dos pierde su trabajo. Todo lo de acá existe para que eso no pase.

> **Desde el reordenamiento del 2026-10-02**, lo que se ajusta día a día está en [GUIA-DE-DIRECCION.md](GUIA-DE-DIRECCION.md) y las reglas que evitan romper cosas en [REGLAS-DE-ORO.md](REGLAS-DE-ORO.md). Este documento cubre git, el reparto del trabajo y el empaquetado.

## El circuito de cada cambio (2026-10-02)
1. **Ajustar** en el lugar que corresponde (guía §2): tiempos → `DA_Partitura_Obra`; perillas de una mecánica → su nivel de test; lugares → actores del nivel.
2. **Ensayar la etapa sola** en su nivel de test (los ensayos leen la misma Partitura que la Obra), o `python tools/unreal/probar_nivel.py Test_Heart --segundos 120` sin abrir el visor.
3. **Prueba de humo de la Obra entera:** `python tools/unreal/smoke_obra.py` (≈9 min a velocidad 4; con `--speed 1 --traza` deja además la traza para el editor web). OK = todas las marcas en orden y 0 errores de Blueprint.
4. **Commit del hito** (Save All antes).
5. **APK cuando haga falta verlo en el visor:** `python tools/unreal/empaquetar_obra.py` (deja el build en `Recursos/Soul Charger - Escritorio 2026-10/APK/`) y `powershell -File tools/unreal/instalar_quest.ps1` (instala, sube el OBB con reintento, abre la app y confirma que llega al Hall). Para un build de público: la checklist de la guía §6.

## Decisiones pendientes (para Beltrán)
- **Llevar `core/esqueleto` a `main`.** `main` está 314 commits atrás y no tiene nada propio, así que el merge es un avance directo, sin conflictos. Mientras no se haga, la rama de trabajo real es `core/esqueleto` y quien clone `main` recibe un proyecto viejo.
- **Git LFS + locks.** Hoy no hay LFS, y el repo pesa por los WAV y PSD de `Recursos/`, no por los `.uasset`. Con más personas tocando el proyecto, LFS permite *locks* (`git lfs lock <asset>`), que es lo único que impide de verdad que dos personas editen el mismo `.uasset`. El costo es la cuota de LFS de GitHub (1 GB de almacenamiento y 1 GB de banda al mes en el plan gratis; los packs de datos se pagan aparte) y migrar el historial (`git lfs migrate`) reescribe los commits, así que cada clon tiene que volver a clonar. Recomendación: activar LFS **solo para lo nuevo** (`*.uasset`, `*.umap`, `*.wav`, `*.psd`) sin migrar el historial, y usar locks en los assets compartidos (`BP_Obra_SC`, `DA_Partitura_Obra`, el nivel de la Obra, el pawn).

---

## 0. El modelo mental: git sube CAMBIOS, no tu carpeta (leer esto primero)
La duda más común al empezar en equipo: *"si yo subo Breath actualizado y Nico sube Touch desde una copia con Breath viejo, ¿me pisa el Breath?"* **No.** Y entender por qué evita el 90% de los problemas.

**Git no sube "tu carpeta entera". Sube los cambios específicos que hiciste** (qué archivos tocaste y qué parte cambió). Un commit es una lista de *diferencias*, no una foto completa que reemplaza lo del otro.

Ejemplo concreto:
- Vos tocás archivos de **Breath** → tu commit dice "cambié estos archivos de Breath".
- Nico toca archivos de **Touch** → su commit dice "cambié estos de Touch".
- Aunque Nico tenga en su copia un Breath **viejo**, su commit **no incluye ningún cambio de Breath** (no los tocó) → al subir **no puede pisar tu Breath**.

**El paso que lo hace seguro: `pull` antes de `push`.** Paso a paso:
1. Vos avanzás Breath → `push`. `main` ya tiene tu Breath nuevo.
2. Nico trabaja Touch en su copia (con el Breath viejo).
3. Nico intenta `push` → **git se lo RECHAZA** ("estás atrasado, traé los cambios primero"). Git no te deja pisar lo del otro por accidente.
4. Nico hace `pull` → git **fusiona** tu Breath nuevo en su copia. Como él no tocó Breath, **entra sin conflicto**; su Touch queda intacto.
5. Ahora su copia tiene **tu Breath + su Touch** → `push` → `main` queda con las dos cosas. Nadie perdió nada. ✅

**En una línea:** GitHub *integra* el trabajo de los dos, no lo reemplaza; cada push sube solo tus cambios; y git te obliga a traer lo del otro antes de subir. Lo tuyo nunca se pierde… **salvo que ambos editen el mismo `.uasset`** (binario, no se fusiona) — que es justo lo que evita la regla de "un stage cada uno" (§1).

**Rutina diaria mínima:** al empezar → `git pull` (o `git pull --rebase`). Al terminar un hito → `commit` + `push`. Si el push se rechaza → `pull` y volvé a `push`.

## 1. Regla de oro
> **Un dev = un stage = una rama. Nunca dos personas editan el mismo `.uasset` a la vez.**

Como cada mecánica vive en su propia carpeta (`Content/SoulCharger/Mechanics/<Mecánica>/`, con su nivel `Test_<X>`), si cada uno se queda en la suya no hay colisión. Los choques solo pasan en lo **compartido** (ver §4).

## 2. Ramas
- Rama base: **`main`** (siempre estable, empaquetable).
- Cada stage en su rama: **`stage/heart`**, **`stage/movement`**, etc. Una herramienta/experimento: `tool/<nombre>`.
- Trabajás y commiteás en tu rama. Cuando cerrás un **hito** (una mecánica anda en el visor), abrís un **Pull Request a `main`**.
- Antes de empezar el día: `git checkout tu-rama && git pull origin main --rebase` (traés lo último de main sin romper lo tuyo). Si el rebase toca un `.uasset` que ambos cambiaron → ver §5.

## 3. Commits y push
- **Save All en Unreal ANTES de commitear** (git ve el archivo en disco, no lo que está sin guardar en el editor). Mini-skill `/commit` lo recuerda.
- **Commiteá HITOS, no micro-cambios.** Los `.uasset` son binarios y pesan; un commit por cada nodo llena el repo. Un commit = "la mecánica X quedó armada y compila".
- Mensajes claros en presente ("Heart: sensor de latido lee OSC y pulsa la esfera"). No "cambios varios".
- Push a tu rama seguido (respaldo). Merge a `main` solo por PR de hitos.

## 4. Assets compartidos — coordinar SIEMPRE
Estos los tocan todos, así que **avisá al otro antes** y serializá (uno a la vez):
- `Content/SoulCharger/Core/` — el **pawn VR**, fades, UI compartida.
- `VR_Test/Config/` — `DefaultEngine.ini`, `DefaultGame.ini`, `DefaultInput.ini` (project settings, mapas a cocinar, packaging).
- **La Obra**: `Content/SoulCharger/Obra/` — el director `BP_Obra_SC`, el nivel `L_SoulCharger_Obra` y sobre todo **`DA_Partitura_Obra`** (todos los tiempos de la obra: lo tocan dirección y quien ajuste cualquier etapa).
- `MapsToCook` y ajustes de packaging.

Regla: si tu cambio toca algo de acá, decilo por el canal del equipo, hacelo rápido, commiteá y avisá que quedó libre. **No metas lógica de tu stage en el pawn** — cada mecánica en su propio BP (el pawn liviano es regla del proyecto).

## 5. Si igual hay conflicto en un `.uasset`
Git no lo mergea. Opciones:
1. **Prevención:** no debería pasar si respetaste §1/§4.
2. Si pasó: **decidan quién gana** ese asset. El que pierde hace `git checkout --theirs <asset>` (o `--ours`) para quedarse con una versión, y **re-aplica sus cambios a mano** en el editor. No hay merge automático posible.
3. Para reducir riesgo: hitos chicos y frecuentes a `main` → menos ventana de divergencia.

## 6. Deploy (empaquetar APK)
- **Cuándo:** cuando una mecánica está lista para probar en el device real (no en cada cambio).
- **Cómo:** empaquetar en **Development** (no Shipping) para trabajo y captura de datos — Shipping recorta logs y cambia rutas de guardado. Ver `skills/unreal-vr/references/packaging-pso.md` y las memorias de packaging.
- Antes de empaquetar: que el stage compile limpio y que el nivel esté en `MapsToCook` (`DefaultGame.ini`).
- El build final de la obra (Shipping) es un paso aparte, coordinado.

## 7. Conocimiento compartido — que no se pierda
El aprendizaje del equipo vive en el **repo**, no en la cabeza ni en la memoria local de Claude de cada uno:
- **Técnica reusable** (un gotcha, un patrón de nodos, cómo se hace X en Quest) → PR a `.claude/skills/unreal-vr/` (a `references/` o `gotchas.md`).
- **Estructura de un Blueprint** (qué hace cada variable, orden del grafo, qué palanca ajusta qué) → su tracker en `skills/unreal-vr/blueprints/<BP>.md`. 🔴 **Leelo antes de tocar el BP; actualizalo después.** Y actualizá su fila en el **índice maestro** `skills/unreal-vr/blueprints/_INDEX.md` (el mapa de todos los BPs: qué es, dónde, estado).
- **Narrativa / diseño / concepto** → [`OBRA-SOUL-CHARGER.md`](OBRA-SOUL-CHARGER.md) y el guion vigente ([`GUION-V5-2026-09-29.md`](GUION-V5-2026-09-29.md)). `Soul-Charger-Design.md` (raíz) quedó superado.
- **Tiempos de la obra** → `DA_Partitura_Obra` + [`PARTITURA.md`](PARTITURA.md) (generado desde `tools/unreal/partitura_def.py`).
- **Estado general** → `CLAUDE.md` §3 (`ESTADO-STAGES.md` es de septiembre).
- **Memoria local de Claude Code** (`~/.claude/...`) = tus notas personales de sesión. NO es conocimiento de equipo (el otro no la ve). Si algo sirve al equipo, subilo al repo.

## 8. Checklist de fin de sesión
1. Save All en Unreal.
2. Actualizaste el/los tracker(s) de los BPs que tocaste.
3. Si tocaste algo que entra en la Obra → `smoke_obra.py` OK.
4. `/commit` (o commit + push manual a tu rama).
5. ¿Hito cerrado? Abrí/actualizá el PR a `main`.

## 9. Nota sobre el repo
- URL: `github.com/beltranlihn/VR_DigitalSanctuary` (fue renombrado desde `VR_Digital`; si tenés un clon viejo: `git remote set-url origin https://github.com/beltranlihn/VR_DigitalSanctuary.git`).
- `.gitignore` (raíz) ignora lo regenerable: `Binaries/`, `Intermediate/`, `Saved/`, DDC, `Build/`. No los versiones.
- Sin Git LFS por ahora (ningún asset >50 MB). Ver "Decisiones pendientes" arriba.
- Lo archivado del proyecto (`_Deprecated/`, fuera de `VR_Test/`) **no se versiona**; git lo conserva en el tag `respaldo-pre-reorden-2026-10-02`.

### 📦 Receta que FUNCIONA para empaquetar el APK desde la terminal (2026-08-19, con el editor abierto)
```
"C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun -project="<ruta>\VR_Test\VR_Test.uproject" -unrealexe="C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" -skipbuildeditor -nocompileeditor -platform=Android -cookflavor=ASTC -clientconfig=Development -cook -AdditionalCookerOptions="-ini:EditorPerProjectUserSettings:[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:bAutoStartServer=False" -build -stage -pak -iostore -compressed -package -archive -archivedirectory="<ruta>\VR_Test\Saved\Packaged\Android_Development" -prereqs -utf8output -nop4
```
Salida: `VR_Test/Saved/Packaged/Android_Development/VR_Test-arm64.apk` + `main.1.com.YourCompany.Demonstration.obb` + `Install_VR_Test-arm64.bat` (instala APK+OBB por adb). Tres cosas que hubo que aprender:
1. **Proyecto sin código**: sin `-unrealexe=...UnrealEditor-Cmd.exe` + `-skipbuildeditor`, UAT busca `Binaries/Win64/VR_TestEditor.target` y muere (`DirectoryNotFoundException`).
2. **GameFeatures está ON** (lo arrastra el plugin `GameFeaturesToolset` del MCP) → hace falta la regla `PrimaryAssetTypesToScan` de `GameFeatureData` en `DefaultGame.ini` (ya está). Sin ella: `Error: Asset manager settings do not include a rule for GameFeatureData` y el cook sale con 1.
3. **Con el editor abierto, el cook intenta abrir el puerto 8000 del MCP** → `Error: HttpListener unable to bind` y el cook sale con 1. El `-AdditionalCookerOptions="-ini:...bAutoStartServer=False"` lo apaga **sólo para el commandlet**; el MCP del editor sigue vivo.
El mapa de arranque del APK es `GameDefaultMap` en `DefaultEngine.ini` (hoy `/Game/SoulCharger/Obra/L_SoulCharger_Obra`). 🟢 **Desde 2026-10-02 todo esto lo hace `tools/unreal/empaquetar_obra.py`** (cambia y restaura el ini, corre UAT por PowerShell, repone `bAutoStartServer` del MCP y copia el build a Recursos); la receta queda como referencia.

### 🏷️ Que el paquete se llame **SoulCharger** y no **VR_Test** (2026-08-28)
UAT nombra los artefactos con el **nombre del `.uproject`** (`VR_Test-arm64.apk`, `Install_VR_Test-arm64.bat`).
Renombrar el `.uproject` sería invasivo, así que el paso es **post-proceso del archive**:
```
VR_Test-arm64.apk                    ->  SoulCharger-arm64.apk
Install_VR_Test-arm64.bat            ->  Install_SoulCharger-arm64.bat   (+ parchear la línea "install <apk>")
Uninstall_VR_Test-arm64.bat          ->  Uninstall_SoulCharger-arm64.bat
SymbolizeCrashDump_VR_Test-arm64.bat ->  SymbolizeCrashDump_SoulCharger-arm64.bat
```
🔴 **Tres cosas que NO se tocan:**
1. **El `.obb`** — Android exige el nombre exacto `main.<versionCode>.<packageid>.obb`.
2. La línea `rm -r %STORAGE%/UnrealGame/VR_Test` de los `.bat` — es la carpeta REAL en el dispositivo,
   derivada del nombre del proyecto, no una etiqueta.
3. La carpeta `VR_Test_Symbols_v1` — la referencia el bat de symbolize por su nombre.

💡 **El nombre que ve el usuario en la biblioteca del visor NO es el del archivo**: sale de
`ApplicationDisplayName` en `DefaultEngine.ini` (hoy **`Soul Charger`**), y **qué app reemplaza** lo decide
`PackageName` (hoy **`com.almadigital.soulcharger`**). Verificable sobre el APK ya construido:
```
<sdk>\build-tools\<ver>\aapt2.exe dump badging <apk>
  package: name='com.almadigital.soulcharger'
  application-label:'Soul Charger'
```
⚠ Y el `Install_*.bat` empieza con un **`adb uninstall <packageid>`**: reemplaza la versión anterior de
ESE package id, y deja intactas las apps con otro id.

🔴🔴 **El renombrado hay que REHACERLO después de CADA build, y borrando el anterior primero.**
El build siguiente vuelve a escribir `VR_Test-arm64.apk` y sus `.bat` **al lado** de los que renombraste.
Si no limpiás, la carpeta queda con **dos juegos**: un APK viejo con el nombre bueno y un OBB nuevo — y el
`Install_SoulCharger-arm64.bat` instala esa combinación equivocada **sin dar ningún error**.
👉 Script listo: `.claude/skills/unreal-vr/scripts/rename_package.py <carpeta Android_ASTC>` — borra el
renombrado previo, renombra el fresco y parchea el `.bat`.

### 📲 Instalar el APK en la Quest (2026-09-04) — el `.bat` de Epic falla en el OBB
`Install_<proyecto>-arm64.bat` hace bien la primera mitad (desinstala, `adb install`, permisos) pero **el push del OBB falla**: usa `UnrealAndroidFileTool.exe`, que responde `Did not find package with activity` / `Unable to connect to <serial>` aunque el `pm list packages` justo arriba confirme que la app SÍ quedó instalada. El `.bat` corta ahí con "There was an error installing the game or the obb file" y **deja la app instalada pero sin datos** — arranca y muere.

✅ **El OBB se sube a mano con adb y funciona** (5 s a 24 MB/s):
```
adb shell mkdir -p /sdcard/Android/obb/<PACKAGE>
adb push main.1.<PACKAGE>.obb /sdcard/Android/obb/<PACKAGE>/main.1.<PACKAGE>.obb
adb shell ls -l /sdcard/Android/obb/<PACKAGE>/     # verificar el TAMAÑO exacto en bytes
```
`<PACKAGE>` sale del propio log de UAT (`GetPackageInfo ReturnValue: com.almadigital.TESTMESHES`). El `adb` de la máquina de Beltrán está en `%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe` (no está en el PATH).
⚠ `Failure [DELETE_FAILED_INTERNAL_ERROR]` en el `adb uninstall` del principio es **normal e ignorable** (no había versión previa).
🔴 **Desinstalación limpia (2026-10-01): si se borra `/sdcard/Android/obb/<PACKAGE>`, el push siguiente falla** con `remote secure_mkdirs failed: Operation not permitted` (Android 14 no deja que `shell` cree esa carpeta), y la app queda instalada sin datos: abre y se queda en negro. Arreglo probado: abrir la app una vez (el sistema crea la carpeta), `am force-stop` y repetir el push. **Verificar siempre el tamaño en bytes con `ls -l`** — el `Select-Object -Last 1` del script escondió el error y mostró "1 file pushed".

### ⚠ Lanzar RunUAT: PowerShell con `--%`, NO la herramienta Bash
Desde la herramienta Bash, `"C:/Program Files/Epic Games/..."` se rompe con `"C:\Program" no se reconoce como un comando` — y **sale con código 0**, así que parece que empaquetó cuando en realidad murió en el primer segundo. La forma que funciona es PowerShell con el token de stop-parsing, que además protege los `[` `]` `:` del `-AdditionalCookerOptions`:
```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat" --% BuildCookRun -project="..." ...
```
Señal de que corrió de verdad: el log termina en `BUILD SUCCESSFUL` + `AutomationTool exiting with ExitCode=0` y la carpeta de archive tiene el `.apk` y el `.obb`.

### 📦 Empaquetar UN SOLO nivel (p. ej. Calibración) sin dejar tocada la config de la obra (2026-09-21)
1. **`-map=/Game/SoulCharger/Maps/Tests/L_Calibration`** en el `BuildCookRun` de arriba. UAT lo pasa al cook como `-Map=`, y el cooker, si recibe mapas por línea de comando, **ignora la lista `MapsToCook` de `DefaultGame.ini`** (verificado en el motor: `CookOnTheFlyServer.cpp`, `bFoundMapsToCook = CookMaps.Num() > 0`). Resultado medido: *FULL COOK* de 855 paquetes en 25 s, APK de 121 MB + OBB de 86 MB, `BUILD SUCCESSFUL` en 57 s.
2. **El mapa de arranque sigue saliendo de `GameDefaultMap`**, así que ese sí se cambia en `DefaultEngine.ini` **mientras corre UAT** (el paso de *package* lee la config al final). En el mismo momento se cambian `PackageName` y `ApplicationDisplayName`, para que la app conviva en la Quest con las demás.
3. **Al terminar: `git checkout -- VR_Test/Config/DefaultEngine.ini`** y confirmar con `git status` que la config quedó igual a HEAD.
4. Renombrar con `scripts/rename_package.py <carpeta> SoulCharger_Calibration`.

| Build | `PackageName` | Nombre en el visor | Dónde queda la data |
|---|---|---|---|
| Calibración | `com.almadigital.calibration` | Soul Charger Calibration | `/sdcard/Android/data/com.almadigital.calibration/files/UnrealGame/VR_Test/VR_Test/Saved/SaveGames/` |
| Entering (test de la etapa + banco de medición, 2026-09-27) | `com.almadigital.entering` | Soul Charger Entering | archive en `VR_Test/Saved/Packaged/Android_Entering/`; `-map=/Game/SoulCharger/Mechanics/Breath/Maps/Test_Breath`; medir con `scripts/quest_entering_perf.ps1` |
| Recorrido (5 etapas × 1 min, 2026-09-29) | `com.almadigital.recorrido` | Soul Charger Recorrido | archive en `VR_Test/Saved/Packaged/Android_Recorrido/`; `-map=/Game/Test_Recorrido+/Game/SoulCharger/Mechanics/Breath/Maps/Test_Breath+/Game/SoulCharger/Mechanics/Heart/Maps/Test_Heart+/Game/SoulCharger/Mechanics/Mind/Maps/Test_Mind+/Game/SoulCharger/Mechanics/Sequencer/Maps/Test_Sequencer+/Game/SoulCharger/Mechanics/Draw/Maps/Test_Draw` (los niveles cargados con LoadLevelInstance tienen que ir en el `-map=`); medir con `scripts/quest_recorrido_perf.ps1` |
| Sequencer / Attracting (salar de Chladni + banco de medición, 2026-09-29) | `com.almadigital.sequencer` | Soul Charger Sequencer | archive en `VR_Test/Saved/Packaged/Android_Sequencer/`; `-map=/Game/SoulCharger/Mechanics/Sequencer/Maps/Test_Sequencer` (el `GameDefaultMap` del ini ya es Test_Sequencer: solo cambian `PackageName`/`ApplicationDisplayName`); medir con `scripts/quest_chladni_perf.ps1`. ⚠ Desde Git Bash `adb push ... /sdcard/...` se rompe (MSYS convierte `/sdcard` en `C:/Program Files/Git/sdcard`): subir el OBB desde PowerShell |
| Heart (membrana del latido, 2026-09-27) | `com.almadigital.heart` | Soul Charger Heart | archive en `VR_Test/Saved/Packaged/Android_Heart/`; `-map=/Game/SoulCharger/Mechanics/Heart/Maps/Test_Heart`. ⚠ el `Install_*.bat` falló al copiar el OBB (`UnrealAndroidFileTool`: *"Did not find package with activity"*) con el APK ya instalado: se copió con `adb push <obb> /sdcard/Android/obb/com.almadigital.heart/` y arrancó bien |

⚠ **En la línea del `--%` no va NADA después de los argumentos de UAT** (ni `> log`, ni `; otra cosa`): con el stop-parsing todo eso le llega a cmd/UAT. Pasó el 2026-09-27: el build salió bien y UAT igual terminó con `ExitCode=1` por el `;` que le llegó como comando (gotcha 438).

🔴 **El `Install_*.bat` de Epic hace `rm -r %STORAGE%/UnrealGame/VR_Test`**, y esa carpeta es **compartida por todos los builds de VR_Test**. Instalando a mano no hace falta: `adb install -r <apk>` + el push del OBB de la sección de arriba. El `adb` que usa Meta Quest Developer Hub es el mismo del SDK (`%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe`), así que no hay choque de versiones.
⚪ **Ruido conocido en logcat:** `LogIoDispatcher: Error: OpenMappedEx failed on: ...ucas` (decenas de veces al arrancar). El motor no puede mapear en memoria datos que están dentro del OBB y los lee de la forma normal. El flujo de Calibración corrió completo igual. Si alguna vez falta un sonido o una imagen, es el primer sospechoso.

### 🎥 Grabar la experiencia en video (casting de Meta Quest Developer Hub, 2026-10-01)
- **Cómo:** Device manager → *Cast Device* abre la ventana **Meta Casting**; el botón de cámara de video de su barra inferior graba. **La grabación la hace el visor**, no el PC: queda en `/sdcard/Documents/Casting_Video_<epoch ms>.mp4` (el número es la hora UTC de inicio, en milisegundos) y se baja con `adb pull`.
- **Ajustes (engranaje, sección Recording):** bitrate 60 Mbps, formato MÁX, 60 FPS, y en Transmisión **"Pause when recording" ON** (el visor codifica un solo video; el PC muestra "En pausa"). Resultado medido: **2560×1440 a 60 fps**, ~6-46 Mbps según la escena, audio AAC estéreo.
- **Audio:** graba la mezcla del sistema (el audio de la experiencia). El micrófono no entra: el único que lo usa es `com.oculus.xrstreamingclient` (Quest Link), visto en `dumpsys audio`.
- **Costo en el visor:** el Hall da 72 fps grabando y 72 sin grabar; el aviso inicial da ~35-55 en las dos pasadas (es la carga de las celdas, no la grabación).
- **Fotos sin costo:** se sacan del video después, cruzando la hora del logcat (o la del dictado) con la hora de inicio del nombre del archivo.
- 🔴 **El audio sale "roto" para Premiere (y para YouTube, por las dudas):** el grabador mete como primer paquete de audio los 2 bytes de configuración del AAC, y rellena los demás paquetes a 1536 bytes. ffmpeg y Ableton lo leen; Premiere descarta la pista entera. **Arreglo obligatorio antes de editar o subir:** recodificar solo el audio (el video va tal cual; es todo cuadros clave, así que el corte es exacto):
  `ffmpeg -ss <ini> -to <fin> -i Casting_Video_X.mp4 -map 0:v:0 -map 0:a:0 -c:v copy -c:a aac -b:a 384k -ar 48000 -ac 2 -af aresample=async=1:first_pts=0 -movflags +faststart salida.mp4`
- ❌ `metavr capture video start/stop` (CLI de MQDH) no grabó nada y se trajo un video viejo de `VideoShots`. Los videos de 24 fps / 8 Mbps del 09-27 eran de antes de subir los ajustes.
