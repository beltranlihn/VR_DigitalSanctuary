# Performance de la estación Attracting (`GAL_12` de `TestMeshes`) — medición del 2026-09-24

> **Para quien retome esto:** la estación corre a **~40 fps donde necesita 72**, y ya está
> **medido en device** de dónde viene. Este documento trae los números, el método, lo que se
> probó y falló, y las palancas que quedan sin probar. No hace falta re-medir la línea de base:
> está acá y el instrumental quedó armado.

---

## 1. El problema, en un número

| | valor |
|---|---|
| Presupuesto para 72 Hz | **13,9 ms** |
| Frame time medido (mediana) | **24,85 ms** |
| fps equivalente | **40,2** |
| Cuadros por encima del presupuesto | **100 %** |

Hace falta recortar **~44 %** del tiempo de cuadro.

## 2. 🔴 Veredicto: **FILL-RATE BOUND**, confirmado por el test oficial de Meta

El test ([Meta, Performance Optimization for Mobile](https://developers.meta.com/horizon/documentation/unreal/po-perf-opt-mobile/),
ver `references/profiling-quest.md` §2-3): bajar el render scale a algo mínimo. Si mejora, el cuello
son los fragmentos.

| | Frame | fps |
|---|---|---|
| A — resolución normal | 23,91 ms | 41,8 |
| B — resolución al 30 % | **13,89 ms** | **72,0** |

**+42 %**, y clava exactamente el cap de 72 Hz. El cuello son **los píxeles**.

**Control del experimento:** `RenderTargetPoolSize` cambió entre las dos fases (197,1 → 213,6 MB),
lo que prueba que la palanca de resolución realmente reconstruyó el render target. Sin ese control,
un "B no mejoró" sería ambiguo entre *no es fill-rate* y *la cvar no hizo nada*.

### La CPU NO es el problema, aunque `stat unit` lo sugiera
El desglose del GameThread parecía acusar a la CPU: `GameThreadTime` pegado al `FrameTime` (24,87 de
24,85) y un `WorldTickMisc` de 18 ms. **Es una trampa de lectura:** al bajar la resolución,
`WorldTickMisc` se desplomó a **7,08 ms**. Era el GameThread **bloqueado esperando a la GPU**, no
trabajo.

| | A (normal) | B (30 %) | ¿qué es? |
|---|---|---|---|
| `WorldTickMisc` | 18,05 ms | 7,08 ms | **espera por GPU** |
| `TickActors` | 2,98 ms | 3,54 ms | CPU real (ticks de BP) |
| `RenderThreadTime` | 3,40 ms | 3,82 ms | CPU real de render |

El trabajo de CPU de verdad son ~3,5 ms de `TickActors` (20 esferas × 6 funciones por cuadro + la
cadena + el sensor) y ~3,5 ms de RenderThread. **Ninguno de los dos es el cuello.** Optimizar
Blueprints acá no sirve.

## 3. Lo que se probó, y cuánto rindió

Todo medido con el mismo instrumental, en sesiones de ~70-105 s con el visor puesto.

| palanca | Frame | ganancia | veredicto |
|---|---|---|---|
| línea de base | 24,85 ms | — | |
| `xr.VRS.FoveationLevel 3` | 22,96 ms | +7,6 % | ⚠ poco, y cerca del ruido |
| `xr.SecondaryScreenPercentage.HMDRenderTarget 85` | 18,62 ms | **+25,1 %** | sólido, pero no alcanza |
| VRS 3 + resolución 85 % | 18,48 ms | +25,6 % | **no se suman** |
| **Blend mode Masked** (en vez de Translucent) | 21,65 ms | **+12,9 %** | 🔴 **RECHAZADO por look** |

### ⚠ El ruido entre corridas es ~4 %
La misma configuración base midió **23,91** y **24,85 ms** en dos pasadas distintas. Cualquier
ganancia por debajo de ~8 % hay que tomarla con pinzas. Es por esto que el 7,6 % de VRS no se
considera concluyente.

### La foveation por VRS y la de hardware son cosas distintas
- `xr.VRS.FoveationLevel` — el camino propio de Unreal. **Se puede cambiar en vivo.** Dio 7,6 %.
  ⚠ No hay columna que pruebe que se aplicó, así que un resultado nulo sería ambiguo.
- `xr.OpenXRFBFoveationLevel` — **la foveation de hardware de la Quest**, la buena. Hoy está en
  **1 de 3**, puesta desde `SystemSettingsIni`. Es **read-only en runtime**: solo se fija al
  arrancar, así que probar el nivel 3 **exige reempaquetar**. ⬜ **Sin probar.**

### 🔴 Masked: la hipótesis correcta con el resultado equivocado
Idea de Beltrán, y el razonamiento era bueno: *"estamos trabajando casi todo mate, podríamos sacar
los translúcidos"*. Al abrir el material apareció un dato que lo respaldaba:

> **`ChainTransparency` en `MI_OrbBlob_SC` estaba en 0.** Las esferas ya eran 100 % opacas donde el
> rayo pega, pero pagaban el costo completo del pipeline translúcido a cambio de nada.

Se pasó `M_SlotChain_SC` a `BLEND_Masked` con la máscara de impacto del raymarch en `Opacity Mask`.
**Rindió solo 12,9 %**, porque *masked no evita que el raymarch corra* — la ganancia viene únicamente
de poder descartar las gotas tapadas, y el solapamiento en pantalla resultó moderado.

**Se revirtió** (`BLEND_Translucent`, `OpacityMask` desconectado, `Opacity` ← `Multiply_0`): Beltrán
reportó que *"se ve bastante pixelado"*. Masked da silueta dura, sin medio tono, y en gotas
raymarcheadas eso se lee como bordes escalonados.

✅ **RESUELTA (2026-09-24, mismo día):** Beltrán confirmó que el diente de sierra se ve **de verdad**
en los bordes de las esferas y del metaball a resolución completa — no era la fase B del test.
El masked pelado queda **descartado en firme** y el 12,9 % no está gratis. Además fija un requisito
de look: **el borde suave del translúcido es parte de la estética**, cualquier alternativa tiene que
conservarlo. Los enfoques siguientes: [`PLAN-PERF-ATTRACTING.md`](PLAN-PERF-ATTRACTING.md).

## 4. La escena: qué hay y cuánto cuesta cada cosa

| pieza | cantidad | detalle |
|---|---|---|
| Esferas de sonido | 20 | SDF raymarcheada, `MI_OrbBlob_SC`, **`Steps` 28**, `BlobCount` 1, `MaxT` 40000 |
| Cadena metaball | 1 | `BP_SlotChain_SC`, **`Steps` 32**, `ChainTransparency` 0,156 en la instancia |
| Núcleos blancos | 8 | `M_BlobCore_SC`, translúcido real (`CoreOpacity` 0,258, `CoreScale` 0,27) |
| Puntero | 4 componentes | 2 materiales, uno con `bDisableDepthTest` |
| Partículas attract | 1 sistema | sprites translúcidos, solo mientras sostenés una esfera |

Todo eso es **translúcido apilado** sobre un renderer móvil que es fill-rate bound: el overdraw se
suma capa por capa. Pila de orden de dibujo: cadena 0 · núcleos 10 · esferas 20 · puntero 100.

## 5. ⬜ Palancas sin probar, por orden de expectativa

1. **🔴 `Steps` del raymarch (32 en cadena / 28 en esferas).** Es **el** número: son las iteraciones
   por píxel cubierto, y multiplican todo lo demás. A diferencia de masked, no depende del
   solapamiento. Bajar a la mitad (16/14) es la prueba obvia. **Riesgo:** menos pasos = el rayo se
   queda corto = banding o bordes blandos en las gotas. Plan sugerido: probar 16/14, mirar, y si se
   ve mal subir a 20/18.
2. **FFR de hardware de 1 a 3** (`xr.OpenXRFBFoveationLevel` en la config). Gratis visualmente en el
   centro de la vista. Requiere reempaquetar.
3. **Achicar el proxy de las esferas.** El raymarch corre por **píxel cubierto por la malla proxy**,
   no por píxel de la gota. Si el proxy es una esfera holgada alrededor de una gota chica, se están
   pagando píxeles que terminan descartados. Vale medir qué tan ajustado está.
4. **Early-out en el HLSL.** Revisar si el bucle del raymarch corta cuando el rayo se aleja o cuando
   ya convergió. Si no lo hace, es ganancia sin costo visual.
5. **Los 8 núcleos translúcidos.** Chicos, pero son overdraw puro en el centro de cada gota.
6. **Menos esferas visibles a la vez**, o más chicas. Es decisión de obra, no técnica.

## 6. ⬜ Lo que todavía no sabemos medir

- **`GPUTime` nunca se llenó** en los CSV, ni siquiera con `r.GPUStatsEnabled 1` +
  `r.GPUCsvStatsEnabled 1` (la cvar se acepta, la columna queda vacía). Todo el diagnóstico de GPU es
  **por inferencia** desde el test de resolución. **El número duro de GPU time lo da OVR Metrics
  Tool**, que no está instalado en el visor (`references/profiling-quest.md` §1).
- **Overdraw real por draw call** solo lo da **RenderDoc Meta Fork**. No hay view mode de overdraw en
  device: está gateado a SM5 y Quest corre `VULKAN_ES3_1_ANDROID`.

## 7. El instrumental, que quedó armado y probado

| script | para qué |
|---|---|
| `scripts/quest_perf.ps1` | `stats` (números en pantalla dentro del visor) · `start`/`stop`/`pull` · `measure` |
| `scripts/quest_ab.ps1` | el test A/B de Meta en una sola sesión de 70 s |
| `scripts/quest_phases.ps1` | N fases con cvars distintas en una sola sesión |
| `scripts/read_csv_perf.py` | resume un CSV o compara dos, con veredicto |

Build usado: **Development**, package `com.almadigital.TESTMESHES`, mapa `/Game/TestMeshes`.
Receta de empaquetado en `docs/WORKFLOW-EQUIPO.md`.

## 8. 🪤 Trampas que ya se pagaron — no repetirlas

1. **`MaxFrameTime` es constante (33,33 ms) y NO dice si el visor estaba puesto.** Se construyó un
   filtro sobre esa premisa falsa y rechazó una captura perfectamente válida. **No existe ninguna
   columna que indique "casco puesto"** — la ventana válida la garantiza el script, que empieza a
   grabar después de una cuenta regresiva.
2. **Una captura con el visor en la mesa da números creíbles y falsos:** la Quest baja los clocks y
   capa a 30 fps. La primera medición dio 24,67 ms y sugería "CPU bound"; era el casco apoyado.
3. **PowerShell 5.1, dos veces:** (a) `$ErrorActionPreference='Stop'` + un exe nativo = cualquier
   línea de stderr mata el script; `adb` escribe ahí cosas inocuas. (b) los `.ps1` se leen como ANSI,
   así que **un acento o una raya larga rompe el parser**. Los scripts están en ASCII a propósito.
4. **El CsvProfiler nombra los archivos `Profile(2026...).csv`** y esos paréntesis rompen el `pull`.
   Se renombran en el device antes de traerlos.
5. **Renombrar los artefactos después de CADA build, borrando el anterior primero** — si no, queda un
   APK viejo con nombre bueno junto a un OBB nuevo y se instala la combinación equivocada sin error.
6. **`DefaultEngine.ini` se toca para empaquetar y se restaura después** (`git checkout --`).
   ⚠ Ojo: en HEAD tiene `PackageName=com.almadigital.CALIBRATION` pero `GameDefaultMap` y
   `ApplicationDisplayName` apuntando a TestMeshes. Es una **inconsistencia commiteada**: para
   empaquetar TestMeshes hay que poner el `PackageName` a mano cada vez.
