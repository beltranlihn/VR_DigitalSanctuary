# Plan de optimización — estación Attracting (`GAL_12`) · propuesta de enfoques (2026-09-24)

> Continúa [`PERF-ATTRACTING-2026-09-24.md`](PERF-ATTRACTING-2026-09-24.md) (la medición). Esto es la
> **propuesta de enfoques con sus trade-offs**, para que Beltrán decida.

## ⚡ ESTADO (2026-09-25) — **la cirugía se REVIRTIÓ. El material está como estaba y guardado.**

Se implementaron A1+A2+A3 el 24 y **A1 hace desaparecer el metaball de la cadena**. Lo detectó
Beltrán en su viewport; mi verificación había dado un falso OK (ver gotcha §378: comparé el cuadro
entero en vez del elemento). Restaurado byte a byte desde el backup, nodos agregados borrados,
`RayOrigin`/`MaxT` originales, guardado en disco y **verificado por recorte ampliado del arco**.

| fase | veredicto |
|---|---|
| **A1** rayo desde el píxel + `MaxT` acotado | 🔴 **RECHAZADA**: mata la cadena (los orbes sobrevivían). **Mecanismo sin identificar** — no reintentar sin una hipótesis medida |
| **A2** decoración `j<min(NA,8)` | 🟢 inocente y **probado por lectura**: master `ROrb`=0 → `NA=N=8` → `ND=8` = el bucle original. Revertida solo por venir en el mismo `code` |
| **A3** wobble por bandas | 🟢 inocente igual: master `WobbleAFS`=(0,4,0.35) → `WobA=0` en la cadena → `mW=0` → rama idéntica al original. **Es la que vale para los orbes**, que son los únicos con wobble y son 20 en pantalla |

### ✅ A2+A3 RE-APLICADAS y verificadas (2026-09-25) — listo para probar en visor

Re-aplicadas **solas**, sin tocar `RayOrigin` ni `MaxT` (siguen en el original: `TransformPosition_2`
/ 900 / 40000), 33 inputs, canario 152→152, guardado en disco.

**Verificación, esta vez con el método de §378:**
| superficie | resultado |
|---|---|
| Cadena (recorte del arco ×2, original vs A2+A3) | 🟢 el tubo crema **está en las dos** — `perf_shots/VERIF_A2A3_cadena.png` |
| Orbe (preview del `MI_OrbBlob_SC` ×3) | 🟢 mismo tamaño, mismo bulto ondulado, mismo degradado — `perf_shots/VERIF_A2A3_orbe.png` |
| PIE | 🟢 `esferas=20`, `pad ON, paso 0 alineado`, cero `Accessed None` |
| Log de shaders | 🟢 sin `error X` ni `Failed to compile` de este material |

**Qué trabajo se eliminó, por píxel de orbe** (los orbes son 20 en pantalla y los únicos con wobble):
- **A2**: la decoración pasa de 8 gotas a `NA` (1 sin lóbulo, 2 con él) → ~6 iteraciones de ~7 senos
  cada una que se pagaban y se descartaban.
- **A3**: los 5 senos por gota **por paso** dejan de correr en todo el march y solo corren en la
  banda `mW = rmax·WobA·1,31` pegada a la superficie; fuera de ella el paso vuelve a ser entero
  (antes era 0,7 global por seguridad, o sea ~43 % de pasos de más).
- La cadena **no cambia en nada**: con `WobA=0` y `NA=8` el código recorre exactamente las mismas
  ramas que el original.

⬜ **Falta el número.** Estimar aquí sería repetir el error del 24: el veredicto es la medición en device.

### 📦 APK con A2+A3 YA INSTALADO en la Quest (2026-09-25 12:18)
`BUILD SUCCESSFUL` en 67 s con la receta de `WORKFLOW-EQUIPO.md` (editor abierto, cook completo de
1032 paquetes). APK 115,7 MB + OBB 120,3 MB, instalados a mano (el `Install_*.bat` de Epic falla en
el OBB y borra la carpeta compartida). **OBB verificado byte a byte: 126.104.150 = 126.104.150.**
- `PackageName=com.almadigital.TESTMESHES` puesto a mano para el build y **`DefaultEngine.ini`
  restaurado a HEAD** después (`git status` de `Config/` limpio).
- ✅ **`BP_GalleryDirector_SC.startAt = 12` → la app arranca directo en `GAL_12` Attracting**, que es
  justo la estación a medir. No hubo que tocar nada.
- ✅ **Prueba de humo en el device** (sin visor): la app arranca, llega a la estación y loguea
  `SEQ: esferas=20` + `SEQ: pad ON, paso 0 alineado`, **cero errores fatales** en logcat.

### 📉 MEDIDO en visor (2026-09-25 12:22, 60 s, 2601 cuadros): **sin mejora medible**

| captura | config | mediana |
|---|---|---|
| `base.csv` (24) | sin optimizar | **24,85 ms** |
| `A_normal.csv` (24) | sin optimizar | **21,65 ms** |
| `Profile(20260925_122245).csv` | **con A2+A3** | **24,30 ms** |

El número de hoy cae **dentro del rango que la config SIN optimizar ya daba**. A2+A3 no movió la aguja
de forma detectable.

## 🔴 El hallazgo que importa más: **el instrumento no resuelve este tamaño de cambio**
Dos capturas del **build idéntico sin optimizar** dieron **21,65** y **24,85 ms** — **3,2 ms de
diferencia, ~15 %**. La nota vieja de "el ruido es ~4 %" **subestimaba**: con este protocolo,
cualquier cambio menor a ~15 % es invisible.

**La causa es el protocolo, no el dispositivo:** la captura es de *juego libre*, y lo que domina el
coste es **cuánta pantalla cubren las gotas** — o sea hacia dónde mirás y cuántas esferas tenés
cerca. Eso cambia por completo entre pasadas. Se suma el estado térmico, que difiere entre sesiones.

⚠ **Ignorar el "VEREDICTO: CPU BOUND" que imprime `read_csv_perf.py`** al comparar estos dos
archivos: la herramienta asume que el segundo es la fase B de baja resolución, y acá los dos son de
resolución normal. El diagnóstico fill-rate del 24 (hecho con el control de `RenderTargetPoolSize`)
sigue en pie.

### ✅ Próximo paso: **arreglar el instrumento antes de seguir optimizando**
A/B **dentro de UNA sola sesión**, alternando el camino viejo y el nuevo cada ~20 s:
1. En el HLSL, envolver el camino nuevo en `if (FastPath > 0.5)` con el viejo en el `else` (parámetro
   **escalar**, no static switch: tiene que poder cambiar en runtime).
2. Un Blueprint lee una cvar propia (`GetConsoleVariableFloatValue`) y la empuja a los MIDs.
3. `quest_phases.ps1` alterna `FastPath 0` / `FastPath 1` por fase vía broadcast de adb.

Así las dos mediciones comparten **escena, pose y estado térmico**, que es exactamente lo que hoy
contamina el número. Sin esto, cualquier optimización por debajo del 15 % es incomprobable.

💡 **A2+A3 se quedan igual**: están verificadas como visualmente idénticas y hacen estrictamente
menos trabajo. No se puede reclamar una ganancia, pero tampoco cuestan nada.
>
> **La ambigüedad del masked quedó resuelta por Beltrán (2026-09-24):** el diente de sierra se ve
> de verdad en los bordes de esferas y metaball a resolución completa — no era la fase B del test.
> Consecuencias: el 12,9 % del masked **no** está gratis, y **el borde suave del translúcido es un
> requisito del look**, no un accidente.

---

## 1. El diagnóstico fino: no es "translucidez apilada", es un shader ALU-monstruo

Se leyó el HLSL completo del `MaterialExpressionCustom_0` de `M_SlotChain_SC` (el master que
comparten cadena y esferas) y los parámetros reales de `MI_OrbBlob_SC`. La cuenta por píxel cubierto:

**Una esfera** (`Steps` 28, wobble activo `WobbleAFS.x=0.09`, `NA=2` gotas por el lóbulo):
| bloque | costo |
|---|---|
| decoración | bucle **hardcodeado a 8 gotas** aunque `BlobCount=1` → ~50 senos |
| march | 28 pasos × 2 gotas × (length + smooth-min + **5 senos del wobble**) ≈ **280 senos** |
| normal + tinte | 4 taps × 2 gotas × 5 senos ≈ 40 senos |
| **total** | **~370 transcendentales + ~60 `length()` por píxel, por ojo** |

**La cadena** (`Steps` 32, 8-9 gotas, sin wobble): 32 × 9 ≈ **~290 length+smin por píxel** + decoración + normal (36 evaluaciones).

Por eso el masked rindió solo 12,9 %: masked no evita que el raymarch corra — el costo está en el
**ALU por píxel**, no en el blending. Y por eso bajar la resolución rinde lineal: menos píxeles
ejecutando el monstruo.

### Las 4 ineficiencias concretas encontradas en el código
1. **El rayo arranca en la CÁMARA** (`RayOrigin`) con `MaxT=40000` (gotcha §367). Se queman pasos
   cruzando aire vacío antes de llegar a la gota, y los píxeles que no pegan caminan lejos antes de
   salir. Lo estándar es arrancar el rayo **en el píxel del proxy** y cortarlo en la **salida
   analítica** del proxy (una esfera local r=50 en los orbes: un cuadrático).
2. **La decoración corre 8 gotas siempre** (`for j<8`, no `j<N`). Las 20 esferas (`BlobCount=1`)
   pagan 8× la decoración que usan. Cortar a `j<N` es **bit-idéntico** en resultado.
3. **El wobble se evalúa 5 senos por gota POR PASO**, y además fuerza `stepK=0.7` (+43 % de pasos
   por seguridad). El wobble es una modulación de ±12 % del radio: no necesita evaluarse a tasa
   completa durante todo el march — solo cerca de la superficie.
4. Los píxeles **rozantes** (el anillo alrededor de cada silueta) avanzan con paso mínimo
   `eps=0.8` y queman los 28 pasos enteros sin pegar: el anillo alrededor de cada gota es lo más
   caro de toda la pantalla.

El early-out de hit **sí existe** (punto 4 de la lista de palancas del doc de medición: ya está).

⚠ Nota al margen detectada en la lectura: con `Rad0=38`, swell 0,3 y wobble 0,09, el radio pico
teórico ≈ 55 + deriva 7 > el proxy de 50. Si nunca se vio un corte, es porque los picos no
coinciden; revisar el margen real al implementar A1.

---

## 2. Los enfoques, con su trade-off de calidad explícito

### A — Cirugía del HLSL conservando el look EXACTO 🟢 (recomendado primero)
Mismo material, mismas fórmulas de superficie y sombreado; solo se elimina trabajo que no aporta.

| # | Qué | Ganancia estimada | Costo visual |
|---|---|---|---|
| A1 | Rayo desde el píxel del proxy + `tExit` analítico (esfera local en orbes, caja en cadena) en vez de cámara + `MaxT` 40000 | −20-35 % del costo del efecto | **Cero** (misma isosuperficie) |
| A2 | Decoración `j<N` en vez de `j<8` | los orbes pagan 1/8 de decoración | **Cero** (bit-idéntico) |
| A3 | Wobble en dos fases: march con la SDF lisa (+margen), refinar 4-6 pasos con wobble al final; `stepK` vuelve a 1.0 | −50-70 % del ALU del march de orbes | Sub-píxel; riesgo bajo, calibrable |
| A4 | Cadena: poda por gota (test punto-recta 1× por píxel; marchar solo las ≤4 gotas relevantes) | inner loop 9→~3-4 | Cero con margen ≥ `Smooth`+swell |
| A5 | Recién entonces, re-tunear `Steps` (28→16-18 orbes, 32→22 cadena): con A1+A3 cada paso rinde más | proporcional | A ojo en visor (riesgo: banding) |

**Estimación honesta combinada: −40-60 % del GPU del efecto**, que domina el frame. Puede alcanzar
el presupuesto solo o quedar a un paso. Reversible por git; se verifica primero en editor
(screenshots antes/después con la misma cámara) y PIE, después device.
Riesgo real: bugs de shader durante la cirugía (mitigado por verificación en editor + rollback).

### B — Masked + Alpha-to-Coverage ⚪ (deprioritizado con datos)
El masked pelado quedó **descartado a ojo** (diente de sierra confirmado). La variante A2C
(la máscara mapea al coverage del MSAA 4x y el borde gana 4 niveles intermedios) tiene **soporte
sin confirmar en el renderer móvil de UE** ([hilo sin respuesta en Epic](https://forums.unrealengine.com/t/is-alpha-to-coverage-supported-on-mobile-forward-renderer/425404),
[pedidos similares en el foro de Meta](https://communityforums.atmeta.com/t5/Unreal-VR-Development/Alpha-to-coverage-how/td-p/771376));
aun funcionando, 4 niveles < la rampa suave actual, y el techo medido es 12,9 %.
**Veredicto: solo como spike de 30 min si todo lo demás se queda corto.**

### C — Cambiar la técnica de las 20 esferas: malla desplazada, material barato 🟡 (el techo más alto)
La observación estructural: **la esfera de sonido NO es un metaball real**. Es 1 gota + 1 lóbulo +
wobble radial = una superficie estrella-forma que se puede representar **exacta** como una esfera
teselada (~1-2k vértices) desplazada por vértice (WPO) con **las mismas fórmulas** (smooth-min de
2 esferas + los senos del wobble), y el mismo sombreado (normal → degradé `ColorLow`/`ColorHigh`).
El costo por píxel cae de ~2.000+ ALU a ~30.

- **C1 (borde idéntico):** material translúcido barato con la misma rampa de alpha → el borde suave
  actual se conserva EXACTO. Sigue siendo translúcido, pero un translúcido trivial (como el resto
  de la obra, que corre a 72).
- **C2 (máxima ganancia):** opaco con depth-write → early-Z mata todo lo que quede detrás de cada
  esfera (cadena incluida). El borde pasa a ser **geométrico con MSAA 4x real** — NO es el diente
  de sierra del masked (el masked pixela porque la máscara se evalúa por píxel sin coverage; una
  silueta geométrica sí recibe los 4 samples).
- **La cadena queda como está** (ella sí es metaball de verdad, 8-9 gotas fundiéndose), y la fusión
  esfera-cadena al acercarla **ya la dibuja la cadena** (la gota 9, `COrb`/`ROrb`): la esfera sigue
  siendo su propia malla, igual que hoy.

**Costo visual:** silueta poligonal (imperceptible con 1-2k verts a ≥1 m); riesgo de matices al
portar fórmulas → se calibra A/B en el editor con las dos versiones lado a lado.
**Costo de trabajo:** el más alto (material nuevo + puente de parámetros por esfera + validación).
**Cuándo:** si A no alcanza, o como inversión definitiva — las 20 esferas son la mayor superficie
de pantalla de la estación.

### D — Palancas de sistema (se apilan con todo lo anterior; cada una exige reempaquetar)
| | Palanca | Ganancia | Trade-off | Veredicto |
|---|---|---|---|---|
| D1 | **FFR hardware 1→3** (`xr.OpenXRFBFoveationLevel 3` + probar la variante dinámica del plugin OpenXR Foveation) | La palanca #1 de Meta para fill-bound | Periferia a menor resolución; en degradés oscuros el tiling puede notarse — a ojo | 🟢 probar; OVR Metrics muestra el nivel ACTIVO (la columna de control que al VRS le faltó) |
| D2 | **AppSW / Frame Synthesis** (presupuesto pasaría a 27,8 ms) | enorme | 🔴 **Descartado con fuente**: Meta — [AppSW no soporta objetos transparentes](https://developer.oculus.com/documentation/unreal/unreal-asw/) (asume 1 dirección de movimiento por píxel); escena 100 % translúcida + esfera rápida cerca de la cara = el caso peor documentado | 🔴 no gastar un build |
| D3 | Resolución 85 % (+25,1 % ya medido) | grande | choca de frente con "que no se vea pixelado"; nunca se juzgó A OJO aislada | ⚪ reserva; una fase sola de 85 % para mirarla, nada más |

### Micro-palancas (mencionadas por completitud)
Los 8 núcleos `M_BlobCore_SC` (overdraw chico pero puro — un toggle-test los mide), `half` en el
HLSL (⚠ riesgo fp16 conocido del proyecto: "movimiento cortado", memoria de degradados), y el tap
k==0 del pase de normal que re-evalúa la superficie ya conocida del march.

---

## 3. Medición de precisión (opcional, barata, recomendada antes de C)
- **RenderDoc Meta Fork**, 1 captura → **costo por draw real** (¿cuánto es orbes vs cadena vs
  núcleos?). Convierte las estimaciones de arriba en números y dimensiona el premio de C.
- **OVR Metrics Tool** instalado en el visor → GPU time real (la columna que el CSV nunca llenó) +
  foveation level activo para D1.

---

## 4. El plan propuesto (orden concreto)

1. **Cirugía A1+A2** (cero riesgo visual) **+A3** en `M_SlotChain_SC` — verificación en editor
   (mismas cámaras, antes/después) + PIE. Sin visor todavía.
2. **Un build Development con perilla de debug de `Steps`** (un botón sin uso cicla perfiles
   28/20/16/12 orbes · 32/24/18 cadena sobre los MIDs, con print del perfil activo):
   **una** sesión de visor mide A y elige el `Steps` mínimo que se ve bien (~70 s por perfil,
   con el instrumental ya armado).
3. Si falta para 13,9: **A4** (poda de cadena) + **D1** (FFR 3) en el build siguiente — juicio a
   ojo de la periferia + OVR Metrics confirmando el nivel.
4. Si aún falta o se quiere margen definitivo: **C** (esferas → malla WPO), con A/B en editor antes
   del visor.
5. Reserva: D3 (85 %).

Criterio de éxito (del doc de medición): mediana ≤13,9 ms con el ruido de ±4 % en mente — solo
contar ganancias ≥8 %.

## 5. Lo que decide Beltrán
1. ¿OK arrancar por la cirugía del HLSL del master (git antes; reversible)?
2. ¿El orden A → FFR → C cierra, o preferís ir directo a C (la reconstrucción de las esferas)?
3. FFR 3: ¿dispuesto a juzgar la periferia a ojo?

---

# 🧪 EL BANCO DE MEDICIÓN (2026-09-25) — para decidir si la técnica se usa o no

> Nació porque el instrumento anterior no servía: dos capturas del **mismo build sin optimizar**
> dieron 21,65 y 24,85 ms (~15 % de ruido). Con eso, ninguna optimización razonable es comprobable.
> Gotcha §379.

## Qué contesta
La cuenta que decide es **`(modo 0) − (modo 3)` = lo que cuesta TODA la técnica de blobs**:
- si ese número es chico → el coste está en otro lado y no vale la pena seguir tocando este material;
- si es grande → dice exactamente **cuánto presupuesto libera** cambiar de técnica, y por lo tanto
  cuánto puede costar el reemplazo (enfoque C) para que entremos en 13,9 ms.

## Las piezas
| pieza | dónde | qué hace |
|---|---|---|
| **`MPC_Perf_SC`** | `Core/Debug/` | colección de parámetros con el escalar **`PerfMode`**, default **0** |
| **`M_SlotChain_SC`** | `Core/Attracting/` | lee `PerfMode` por un `CollectionParameter` → entrada `PerfMode` del Custom |
| **`BP_PerfSwitch_SC`** | `Core/Debug/` | eventos `Perf0..Perf3` que escriben la colección + `PrintString` |
| actor **`PerfSwitch`** | `TestMeshes` | la instancia que recibe los eventos |
| **`quest_perfmodes.ps1`** | `scripts/` | corre las 8 fases en UNA sesión y trae los CSV |
| **`resumen_modos.py`** | `scripts/` | promedia, calcula la resolución del instrumento y da el veredicto |

## Los modos
| modo | qué hace | para qué sirve |
|---|---|---|
| **0** | el material tal como está autorado | la referencia (**es el default: la obra no cambia**) |
| **1** | `Steps` a la mitad | cuánto rinde bajar pasos |
| **2** | SDF lisa, sin wobble ni decoración | cuánto cuestan los adornos del shader |
| **3** | el material sale al instante sin dibujar | **el piso**: el cuadro sin los blobs |

## Por qué así, y no de otra manera
- **Las 8 fases van en UNA sola sesión** (4 modos de ida + los mismos 4 de vuelta), así comparten
  escena, pose y estado térmico — que es justo lo que contaminaba la comparación entre sesiones. El
  orden invertido en la segunda vuelta evita que una deriva térmica progresiva se le cargue entera a
  la última fase.
- **La separación entre las dos pasadas del mismo modo ES la resolución del instrumento**, y el
  resumen la imprime: cualquier diferencia entre modos menor que eso no significa nada.
- **La conmutación es por `ke * PerfN`** (`KISMETEVENT`). Verificado en el código del motor: vive en
  `UEngine::Exec_Dev`, bajo `#if !UE_BUILD_SHIPPING` → **funciona en Development**, que es nuestro build.
- **Se usa una Material Parameter Collection y no un parámetro por material** porque llega a la
  cadena y a las 20 esferas de una sola escritura, sin tocar ningún Blueprint de la mecánica.
- 🔴 **El parámetro es ESCALAR, no un static switch**: un static switch es de tiempo de compilación y
  no se puede alternar en runtime. La rama es uniforme, así que en modo 0 el costo extra es nulo.

## Verificado (2026-09-25, sin visor)
- **El material lee la colección de verdad**: forzando el modo 3 desde el asset, el metaball
  **desaparece**; en 0 y 2 está. Capturas: `VR_Test/Saved/perf_shots/BANCO_modos.png`.
- **Modo 0 idéntico** a como estaba antes de montar el banco (recorte ×2 del arco).
- **En el device**: `BUILD SUCCESSFUL`, instalado, y los cuatro `ke * PerfN` contestan en logcat
  (`PERF: modo N ...`). El script hace esa misma prueba como **control positivo y aborta si falla** —
  sin eso, las fases no cambiarían nada y la medición sería basura sin avisar.

## Cómo se corre
```
powershell -ExecutionPolicy Bypass -File "<repo>/.claude/skills/unreal-vr/scripts/quest_perfmodes.ps1"
python "<repo>/.claude/skills/unreal-vr/scripts/resumen_modos.py" "<repo>/perf"
```
~4 minutos con el visor puesto. **Jugar parecido durante todas las fases** (agarrar esferas,
colocarlas, mirar la fila de gotas): lo que se compara entre fases es el mismo tipo de vista.
⚠ En algunas fases las gotas se ven distintas o no se ven: es la medición, no un bug.

---

# 🏁 RESULTADO DE LA MEDICIÓN (2026-09-25, 8 fases en una sesión) — **la técnica es el problema**

| modo | qué es | mediana | separación entre sus 2 pasadas |
|---|---|---|---|
| **0 actual** | el material como está autorado | **26,19 ms** (38 fps) | 1,92 ms |
| 1 Steps/2 | la mitad de pasos | 19,02 ms ⚠ | **8,43 ms — no usable** |
| **2 SDF lisa** | sin wobble ni decoración | **20,77 ms** (48 fps) | 0,11 ms |
| **3 gratis** | el material no dibuja | **13,91 ms = 72 fps** | **0,00 ms** |

**Resolución del instrumento: ~1 ms** (mediana de las separaciones). Modo 2 y modo 3 repitieron con
0,11 y 0,00 ms de diferencia entre pasadas: el banco es preciso. El 8,43 del modo 1 **no es ruido del
instrumento** — en la fase 2 el 25 % de los cuadros quedó pegado al cap, señal de que se miró otra
cosa; **ese modo hay que volver a medirlo**.

## La cuenta
```
material de blobs tal como está :  26,19 ms
el mismo cuadro sin dibujarlos  :  13,91 ms   <- 72 fps, 46-47% de cuadros en el cap
-------------------------------------------
cuesta TODA la técnica          :  12,28 ms
presupuesto para 72 Hz          :  13,90 ms
```

🔴 **Al leer el 13,91 del modo 3: ESE ES EL CAP de 72 Hz, no un costo.** Casi la mitad de los cuadros
caen en la banda del vsync, así que el costo real de la escena sin blobs es **ese o menor** — el
vsync no deja ver cuánto menos. (El script llegó a imprimir el veredicto opuesto — "0,01 ms por
encima del presupuesto" — por comparar contra 13,90 sin mirar la distribución. Corregido.)

## Lo que decide
1. **Sin los blobs, la estación clava 72 fps.** El resto de la escena no es el problema.
2. **La técnica de raymarch cuesta 12,28 ms ella sola** — el 88 % del presupuesto entero del cuadro.
3. 🔴 **Ni siquiera su versión más barata alcanza:** el modo 2, que ya sacrifica el wobble, la
   variación de tamaños y el swell — o sea buena parte de lo que hace linda la gota — se queda en
   **20,77 ms (48 fps)**, un 50 % por encima del presupuesto. **No hay ajuste de este shader que lo
   meta en 13,9 ms.**
4. Bajar `Steps` a la mitad rinde **menos** que sacar el wobble (≈23 vs 20,8 ms en sus pasadas
   fiables): **el costo dominante son las transcendentales, no el número de pasos.**

## Consecuencias para el plan
- **A4 y A5 quedan sin sentido**: son ajustes de este shader, y el techo del shader ya se midió.
- **El enfoque C (las 20 esferas como malla desplazada) pasa a ser el camino**, y ahora tiene un
  presupuesto medido: el reemplazo tiene que costar **menos de 12,28 ms**, y cuanto más cerca de 0
  mejor. Una malla teselada con el mismo sombreado cuesta ~1-2 órdenes de magnitud menos por píxel.
- **La cadena puede quedarse como raymarch**: es 1 objeto contra 20, y su parte del costo es la
  menor. El banco permite medirlo por separado si hace falta.
- ⚠ **Pendiente de una segunda pasada**: repetir el modo 1 mirando lo mismo que en las demás fases.
  No cambia la decisión, pero cierra el número.

---

# 🔀 EL SPLIT (2026-09-25, 2ª pasada) — construido y verificado, falta correrlo

La medición de arriba dice que la técnica entera cuesta 12,28 ms, pero no dice **cuánto es de la
cadena y cuánto de las 20 esferas** — y esa cifra dimensiona el enfoque C: si la cadena es chica,
C sobre las esferas alcanza solo; si es grande, la cadena necesita trabajo propio (proxy ajustado /
poda por gota / también C).

**Piezas nuevas, ya verificadas en editor (sin visor):**
- `M_SlotChain_SC`: **modo 4 = solo cadena** (apaga todo píxel con `WobbleAFS.x > 0`, o sea las
  esferas) y **modo 5 = solo esferas**. Tres líneas tras el early-out del modo 3; en modo 0 no
  cambia nada (verificado por preview de asset en los DOS caminos, `perf_shots/SPLIT45_*`).
- `BP_PerfSwitch_SC`: eventos `Perf4`/`Perf5` (mismo patrón que 0-3).
- `quest_perfmodes.ps1 -Modos 0,4,5,3` corre el split; `resumen_modos.py` imprime la cuenta,
  incluido el **piso derivado = m4 + m5 − m0** (la aditividad esquiva el cap de 72 Hz que tapa al
  modo 3) y el veredicto (¿alcanza C sobre las esferas solo?). Control positivo con CSVs
  sintéticos: recupera exactamente piso/cadena/esferas sembrados.
- **FFR de hardware 1→3 A PRUEBA** en `Config/Android/AndroidEngine.ini` (D1 del plan): entra en
  el mismo build. El split queda internamente válido (FFR constante en las 8 fases); el número
  absoluto vs sesiones anteriores sale sucio (~15% entre sesiones) — lo que vale de D1 en esta
  corrida es el **juicio a ojo de la periferia**. Si degrada, revertir a 1 (línea comentada al lado).

**Cómo se corre (cuando Beltrán esté con el visor):**
1. Empaquetar Development (receta `WORKFLOW-EQUIPO.md`; `PackageName=com.almadigital.TESTMESHES`
   a mano, restaurar `DefaultEngine.ini` después).
2. `powershell -ExecutionPolicy Bypass -File .claude/skills/unreal-vr/scripts/quest_perfmodes.ps1 -Modos 0,4,5,3`
3. `python .claude/skills/unreal-vr/scripts/resumen_modos.py perf`
4. En la misma sesión: mirar la periferia (FFR 3) y decir si se banca.

## 🏁 RESULTADO DEL SPLIT (2026-09-25 14:47, 8 fases, FFR 3 activo) — **LA CADENA DOMINA**

| modo | mediana | separación | cap |
|---|---|---|---|
| 0 actual | **22,83 ms** | 0,97 | — |
| 4 solo cadena | **17,02 ms** | 0,45 | — |
| 5 solo esferas | **13,90 ms** | 0,01 | 🔴 34-37% en el cap |
| 3 gratis | 13,89 ms | 0,04 | 🔴 en el cap |

Resolución del instrumento: 0,25 ms. CSVs en `perf/split-2026-09-25/`.

```
las 20 ESFERAS cuestan :    5,81 ms   (EXACTO: m0 − m4, sin cap de por medio)
la CADENA cuesta       : ≥  8,93 ms   (COTA INFERIOR: m5 quedó pegado al cap)
reparto                :  esferas 39% / cadena ≥61%
```

**Las tres lecturas que cambian el plan:**
1. 🔴 **La sorpresa: el costo dominante es LA CADENA (1 objeto), no las 20 esferas.** La
   expectativa previa era la inversa. Su caja proxy (`SM_ChainProxy_SC`, diagonal ~500 para
   gotas de ~40) y el inner loop de 9 gotas × 32 pasos por píxel cobran más que 20 esferas
   con wobble.
2. **Solo esferas = 72 fps clavado** (modo 5 en el cap con separación 0,01): el piso + las 20
   esferas raymarcheadas TAL COMO ESTÁN entran en presupuesto — aunque al ras: la mediana en el
   cap con ~36% de cuadros en la banda dice que hay poco o ningún margen escondido.
3. **Matar solo las esferas no alcanza** (modo 4 = 17,02 > 13,9): la cadena necesita trabajo
   **sí o sí**, y es el primer objetivo, no C.

**Nota FFR:** esta sesión corrió con FFR 3 (verificado en boot: `Set CVar xr.OpenXRFBFoveationLevel:3`).
El modo 0 dio 22,83 vs 26,19 de ayer con FFR 1 (−13%), pero es comparación entre sesiones (~15% de
ruido) → **no es un número reclamable**; el juicio que vale es el de la periferia a ojo.

### El plan reordenado
1. **Cadena, palancas sin costo visual, iterando con `-Modos 0,4` (el modo 4 es el A/B directo
   del costo de la cadena):**
   a. **Proxy ajustado** — ✅ **HECHO (2026-09-25, 3ª pasada):** `SM_ChainProxyTube_SC`, tubo de
      102 verts siguiendo el arco real (radio 26), reemplaza la caja de 120×340×120 en template
      + instancia. Verificado sin visor (bold + modo 4, dos fases del swell, sin cortes; PIE
      verde). Detalle en el tracker de `BP_SlotChain_SC`. **Criterio de éxito de la próxima
      medición: modo 4 pegado al cap de 72 Hz.** ⚠ Ojo de Beltrán pendiente: la fusión al
      acercar una esfera al slot (la gota 9 puede asomar fuera del tubo).
   b. **A4 poda por gota** — test punto-recta 1× por píxel, marchar solo las ≤4 gotas
      relevantes (inner loop 9 → ~3-4). Siguiente si el tubo no alcanza.
2. **C sobre las esferas** (premio exacto: 5,81 ms) — sigue valiendo porque el punto 2 de arriba
   dice que piso+esferas queda AL RAS del cap: sin margen para picos, calor ni estaciones más
   cargadas. La incógnita del lóbulo (P[1] vs P[8], leer `ApplyLook`) sigue vigente.
3. FFR 3 queda si Beltrán lo aprueba a ojo; si no, revertir la línea en `AndroidEngine.ini`.

## 🏆 RESULTADO DEL TUBO (2026-09-25 15:23, 8 fases, FFR 3) — **LA CADENA ENTRÓ EN PRESUPUESTO**

| modo | con la CAJA (mañana) | con el TUBO |
|---|---|---|
| 0 — todo | 22,83 ms | **15,57 ms** (pasada estable 14,73, 25% en cap) |
| 4 — solo cadena | 17,02 ms | **13,93 ms — EN EL CAP** ✅ criterio cumplido |
| 5 — solo esferas | 13,90 (cap) | 13,93 (cap) |
| 3 — piso | 13,89 (cap) | 13,88 (cap) |

Resolución del instrumento: 0,07 ms. CSVs en `perf/tubo-2026-09-25/`. Beltrán en visor: *"todo
mucho más fluido, nunca sentí bajo frame rate"*. **El proxy ceñido le sacó ~7 ms al cuadro.**
⚠ La fase 1 del modo 0 midió 16,41 (arranque de la estación en cámara); la estable es 14,73.
⚠ El costo marginal de las esferas midió 1,64 hoy vs 5,81 a la mañana: el fill de las esferas
depende de CÓMO se juega (qué tan cerca de la cara se sostienen) — entre sesiones no es comparable.
**A4 (poda) y C (esferas por malla) pasan de rescate a MARGEN.** Queda ~0,8-1,7 ms para clavar
72 sostenido en el juego pesado; C sobre las esferas sigue siendo la inversión correcta si se
quiere margen para calor + estaciones cargadas, pero ya no bloquea.

### Y el bug que la fluidez destapó: el TRABADO del reloj (fp16)
Con el frame rate liso, Beltrán vio las animaciones DEL MATERIAL (wobble/metaball) trabarse
progresivamente con los minutos de sesión — manos fluidas, material a saltos, editor impecable.
Diagnóstico: el reloj del shader en half (gotcha 382, pariente de la cura de los degradados).
**Fix aplicado en el master:** `View.GameTime` (fp32) leído dentro del Custom, costo cero.
**⛔ La verificación por modos 6/7 FALLÓ como instrumento (probada en device el mismo día):**
Beltrán no pudo distinguir el modo 6 del 7. A T≈1024 el ulp de un half es 1,0 s — el modo 6 debía
verse congelado a saltos de un segundo. Que no se notara prueba que **el `half` explícito no compiló
a fp16 real** en este target, no que el fix funcione. Por lo tanto: **fix aplicado pero NO
verificado, y el diagnóstico original (fp16) queda en duda**. El test decisivo que queda es gratis:
**una sesión larga (15-20 min) con el build actual** — si el trabado no vuelve, sirvió.
🔴 **Deuda proyecto-ancha:** todos los materiales animados por Time de la obra (15 min) comparten
el bug latente. Barrido pendiente con la receta de la gotcha 382.
