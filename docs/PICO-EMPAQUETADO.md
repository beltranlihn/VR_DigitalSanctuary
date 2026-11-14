# PICO — plugin, empaquetado y rendimiento (revisión del 2026-11-11)

> Estado: **revisado.** Lo único aplicado es la variante de empaquetado `innercanvas` (§4.b). El plugin sigue activo en todos los builds (propuesta §4 sin aplicar).
> Visor de referencia: el logcat lo reporta como **PICO 4 Ultra Enterprise** (runtime `Pico XRRuntime() 110.1344.985117803`, perfil de mandos `pico4_controller`). Son visores de una empresa local: no se cambian sus ajustes de sistema.

---

## 0. Resumen en cinco líneas
1. El plugin **PICO OpenXR 1.6.1** (UE 5.8) está en `VR_Test/Plugins/Marketplace/PICOOpenXR`. Como es un plugin de proyecto, **queda activo en todos los builds, también en el APK de Quest**.
2. 🔴 **Cada vez que arranca el editor, reescribe el `DefaultEngine.ini` compartido**: borra todos los comentarios y agrega ajustes propios (§2).
3. Lo más valioso que aporta es que **la app puede pedir 72 Hz por su cuenta**, sin tocar los visores. El cuadro pasa de 11,1 ms a 13,9 ms, que es el presupuesto para el que está hecho el proyecto (§3).
4. La PICO CLI **no contempla Unreal**. No se instaló (§5).
5. Propuesta: plugin apagado por defecto y encendido solo al cocinar una variante `pico` (§4).

---

## 1. Punto de partida: la demo sin plugin (medido el 2026-11-11)
El APK bilingüe de la demo (`com.almadigital.soulchargerdemobi`) corrió sin cambios en el Pico 4 Enterprise. Usó el OpenXR del motor y el plugin de mandos PICO del motor (`PICOController`, `XR_BD_controller_interaction`).

| Momento | FPS | GPU por cuadro |
|---|---|---|
| Menú | 75 de 90 (mínimo 57) | 13,0 ms |
| Final de Draw | 55 de 90 (caídas a 16) | 13,8 ms (picos de 20) |

Causas: el Pico corre a **90 Hz** (11,1 ms) y la demo está hecha para 72 Hz (13,9 ms). Además, la GPU iba a 456-599 MHz, la resolución quedó alta (120 % en el menú y 115 % en Draw, valores del Quest) y AppSW estaba apagado.
Las mediciones salen de las líneas `PxrMetric` del logcat (`adb logcat -s PxrMetric`).

---

## 2. 🔴 Lo que el plugin le hace al proyecto
### 2.1 Reescribe `VR_Test/Config/DefaultEngine.ini` en cada arranque del editor
| Qué | Dónde (código del plugin) | Efecto |
|---|---|---|
| Guarda su sección `[/Script/PICOOpenXRRuntimeSettings...]` y **reescribe el archivo sin comentarios** | `Source/PICOOpenXRRuntimeSettings/Private/PICOOpenXRRuntimeSettings.cpp:93` | Se pierden todos los avisos del ini (FFR/Link, GC, streaming, DPI, redirecciones) |
| Agrega `ExtraActivitySettings=<meta-data android:name="pvr.app.type" android:value="vr" />` | mismo archivo, 97-139 | Va al manifiesto de **todos** los APK |
| `r.AllowOcclusionQueries=False` (porque `bDisableOcclusionCulling=True` por defecto) | mismo archivo, 143 y 170-175 | Apaga el occlusion culling en **todos** los builds |
| `bIsFBFoveationEnabled=True` en `[/Script/OpenXRHMD.OpenXRHMDSettings]` | `Source/PICOOpenXREditor/Private/PICOOpenXREditor.cpp:413` | Vuelve a la config compartida un ajuste que se había mudado a `Config/Android/AndroidEngine.ini` por los crashes de Link (2026-08-12) |

La primera reescritura fue el 2026-11-11 a las 18:26, un minuto después de instalar el plugin. **El commit `98e99ba` tiene el ini limpio.** La diferencia actual es solo esto: restaurar desde git no pierde nada. Pero mientras el plugin esté activo en el editor, lo vuelve a escribir en el próximo arranque. Por eso, primero se apaga el plugin y después se restaura (§4, paso 1).

### 2.2 En tiempo de ejecución (APK)
- **Sus cvars solo se aplican si el runtime es PICO**. Usa el nombre del runtime ("pico") en `PICO_HMD.cpp:637-639`. En Quest no corren.
- **Excepción: `DisableRHIThread=True` apaga el hilo RHI en Android aunque el visor no sea PICO** (`PICO_HMD.cpp:811`, en `OnCreateSession`). Con el plugin activo, el APK de Quest también perdería el hilo RHI.
- El `PICOMobile_APL.xml` agrega `pvr.sdk.version` al manifiesto y copia `libopenxr_loader_pico.so` en el APK.
- La frecuencia pedida (`DisplayRefreshRate`) se lee del ini y se solicita al iniciar la sesión (`PICO_HMD.cpp:915-916`). No necesita nodos de Blueprint.

### 2.3 Otras notas
- Trae binarios precompilados del editor (Win64). Git ignora `Binaries/` (620 MB de PDB) y versiona el resto. Quien clone el repo sin esos binarios tiene que compilar o instalar el plugin desde Fab.
- El **Portal de PICO** (la ventana que se abre en el editor) le manda a PICO datos de uso: versión del motor y del SDK, y cada vez que se abre (`Source/PICOOpenXRPortal/Private/PICO_AppLog.cpp`).
- No hace falta C++. Según PICO, un proyecto de Blueprints con el motor del launcher no necesita Visual Studio. Para Android, UBT compila el plugin con el NDK que ya usamos. **Confirmado el 2026-11-11**: el APK de Inner Canvas compiló el plugin con el NDK sin Visual Studio.

---

## 3. Lo que el plugin aporta para PICO
| Perilla | Dónde | Para qué / costo |
|---|---|---|
| **Frecuencia de pantalla** `DisplayRefreshRate` = Default / Rate72 / Rate90 / Rate120 | Project Settings → Plugins → PICO OpenXR → *Setup Device Display Refresh Rate* | La app la pide al arrancar y el visor vuelve a lo suyo al salir. El Pico 4 Enterprise está en la lista de soportados. **A 72 Hz el presupuesto vuelve a 13,9 ms.** Decisión pendiente: 72 Hz o 90 Hz optimizado |
| Formato de imagen R8G8B8A8_SRGB | automático con el plugin | Según PICO, sin el plugin el formato por defecto del motor (B8G8R8A8) cuesta 2-4 ms en Pico 4 Ultra y puede crashear en Pico 4 / Neo3 |
| Hilo RHI apagado | `DisableRHIThread` (por defecto True) | Recomendación oficial de PICO para UE ≥ 5.6 |
| Espera de cuadro | automático | Desactiva la doble espera de cuadro del motor; la sincronización la maneja el runtime de PICO |
| **Resolución adaptativa** | `MinimumDynamicResolutionScale` (0,6) + `AdaptiveResolutionSetting` (HighQuality / Balanced / PowerSaving) | Escala entre el mínimo y 1 según la carga de la GPU. Manual: `r.PICO.DynamicResolution.PixelDensity 0.8` (0 = automático) |
| Resolución fija | `xr.SecondaryScreenPercentage.HMDRenderTarget` | Recrea el render target: no cambiarla seguido |
| **AppSW** (renderiza a la mitad y el visor sintetiza los cuadros) | En UE ≥ 5.7 es del motor: `xr.OpenXRFrameSynthesis=1` (+ `xr.PreferFBSpaceWarp=1`), con Mobile Multi-View y *Support Mobile Application Space Warp* | Solo forward + Vulkan, sin TAA (nuestro MSAA sirve). En `PxrMetric` aparece `AppSW=on`. Artefactos con fondos de líneas rectas o grillas y con objetos que giran rápido. Apagarlo mientras compila los PSO la primera vez |
| **FFR** | `xr.OpenXRFBFoveationLevel` 0-3 + `xr.OpenXRFBFoveationDynamic` (extensión `XR_FB_foveation`, la misma del Quest) | Sistema 5.11.0 o más nuevo. ETFR (con seguimiento de ojos) pide la rama de motor de PICO: descartado |
| Nitidez / superresolución | `r.Mobile.PICO.SharpeningSetting`, `r.Mobile.PICO.EnableSuperResolution` (son excluyentes) | Probar en el visor |

**Riesgos que hay que cerrar en el visor**
- La documentación es de la **1.6.0 (UE 5.6/5.7)**. Dice textual *"UE 5.7 does not support PICO 4 series devices"* y pide **un sistema 5.13.0 o más nuevo**. Nuestro plugin es la 1.6.1 para 5.8.
- La demo con 5.8 corrió en el Enterprise **sin** plugin. **Con** plugin todavía no se probó.
- Falta leer la versión del sistema del visor: `adb shell getprop ro.build.display.id`.

---

## 4. Propuesta de empaquetado (no aplicada)
1. **Plugin apagado por defecto**: `{"Name": "PICOOpenXR", "Enabled": false}` en `VR_Test/VR_Test.uproject`. Con el editor reiniciado, restaurar el ini: `git checkout -- VR_Test/Config/DefaultEngine.ini`. Así Quest y el editor quedan como antes.
2. **Variante `pico` en `tools/unreal/empaquetar_obra.py`**, igual que las otras variantes: mientras cocina, enciende el plugin en el `.uproject` y reescribe el ini; al terminar, restaura los dos. Contenido:
   - Paquete y nombre propios (app aparte, no pisa nada instalado).
   - `bPackageForMetaQuest=False` y sin `com.oculus.supportedDevices` en `ExtraApplicationSettings`.
   - `ExtraActivitySettings` con `pvr.app.type=vr`.
   - Sección `[/Script/PICOOpenXRRuntimeSettings.PICOOpenXRRuntimeSettings]` con la frecuencia elegida.
   - Resolución al 100 %. FFR y AppSW como perillas.
3. **Nada de nodos de Blueprint de PICO** en la experiencia. Frecuencia, FFR y AppSW salen de la config, así el proyecto compila igual con el plugin apagado. Si un día hace falta un nodo PICO, se revisa esta decisión.
4. **Primera prueba en el visor**: versión del sistema; `PxrMetric` a 72 y a 90 Hz en la parte más pesada; después AppSW y FFR, de a uno.

Lo más barato para probar antes de recompilar, que sirve también sin plugin: la resolución al 100 % con `-DemoRenderPct=100`, vía `UECommandLine.txt` (`tools/demo/quest_ip_espejo.ps1 -Paquete`).

### 4.b Lo aplicado: variante `innercanvas` (2026-11-11)
`python tools/unreal/empaquetar_obra.py --variante innercanvas` → paquete `com.almadigital.innercanvas` ("Inner Canvas"), solo `/Game/InnerCanvas/Maps/L_InnerCanvas`. Mientras cocina, `ini_pico()` pone `bPackageForMetaQuest=False`, saca `com.oculus.supportedDevices`, agrega `pvr.app.type` y `DisplayRefreshRate=Rate72` en la sección del plugin; al terminar restaura el ini. Antes de cocinar corre `tools/innercanvas/verificar_perillas_ic.py`. Instalación en los visores: `tools/innercanvas/instalar_pico_ic.ps1`. Detalle de la experiencia: [`innercanvas/PLAN-INNER-CANVAS.md`](innercanvas/PLAN-INNER-CANVAS.md).

### 4.c Poses de los mandos en PICO
El láser apunta más arriba, el mando y la paleta quedan ~2 cm más abajo y la punta del pincel queda pegada al mando: el runtime de PICO entrega otra pose aim y otro origen de grip que el de Meta, y el plugin no los corrige (`PICO_HMD.cpp:2137-2190`). Inner Canvas lo corrige solo en PICO, con perillas en la línea de comandos y un modo de medición (`-PoseDump`): ver PLAN-INNER-CANVAS §5. Si la Obra o la demo van a PICO, la misma idea tendría que pasar a una pieza de `SC_Base`.

---

## 5. PICO CLI
- Paquete: `@picoxr/pico-cli` (npm, oficial de PICO), versión 0.7.0 al 2026-11-11. Guía: <https://sf16-va.tiktokcdn.com/obj/eden-va2/bvonuhmlkbps/other/pico-cli-installation-guide.md>.
- Es una herramienta para agentes de IA. El paso de configuración (`pico-cli setup`) **solo acepta `--platform spatial|unity`: no hay Unreal**. Además instala en Claude Code hooks, un servidor MCP, una base de conocimiento local y **Java 21** (no está instalado; Node 25 y npm sí).
- **No se instaló**: modifica la configuración de Claude Code y su parte principal no sirve para Unreal.
- Lo aprovechable son los comandos `device:*`, `adb:*` y `perf:*` (diagnóstico y trazas de rendimiento en el visor). Se pueden usar con `npm install -g @picoxr/pico-cli`, **sin** correr `setup`.

---

## 6. Fuentes
- PICO Unreal OpenXR — Quick start: <https://developer.picoxr.com/document/unreal-openxr/ue-openxr-quickstart/>
- Display refresh rate: <https://developer.picoxr.com/document/unreal-openxr/display-refresh-rate/>
- Display resolution: <https://developer.picoxr.com/document/unreal-openxr/change-display-resolution/>
- Foveated Rendering: <https://developer.picoxr.com/document/unreal-openxr/fixed-foveated-rendering/>
- Application SpaceWarp: <https://developer.picoxr.com/document/unreal-openxr/appsw/>
- Release notes (1.6.0 y anteriores): <https://developer.picoxr.com/document/updates-unreal-openxr/>
- Optimización (guía general, SDK anterior): <https://developer.picoxr.com/document/unreal/optimize-pico-apps/>
- Ficha en Fab: <https://www.fab.com/listings/a7eb0f28-d7f1-4b30-8d2d-49d12eeb1d62>
