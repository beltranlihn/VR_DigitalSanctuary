# Plan: el valle de la respiración (Entering), 2026-09-27 · **v2** (revisada el 2026-09-28)

> **Pedido de Beltrán (v1):** un entorno para la etapa de respiración. El metaball flota sobre un paisaje de colinas suaves que se van transformando lentamente. El material es mate y agradable. El usuario está sentado en un **valle central** con el metaball al frente, todo muy liso, y una **sombra falsa** hace sentir que el metaball flota. La estética de partida es la de la membrana del latido, que en la Quest *"funciona muy bien"*.
>
> **Condición:** no se toca ningún asset o archivo de Heart. De Heart se **lee** y se **copia la estructura** a archivos propios.
>
> **Este documento es la especificación única.** Tres implementaciones tienen que dar el mismo resultado: el material en Unreal (HLSL), un prototipo en three.js (GLSL) y el generador de la malla en Blender. Por eso trae el código de referencia completo y, en la §12, **valores de control** que cada implementación tiene que reproducir. El **modelo numpy de referencia** es `scripts/valley_model.py`.
>
> La v1 completa (spec, HLSL, scripts y `valley_build.json`) quedó respaldada en `VR_Test/Saved/ClaudeScripts/valle_v1_backup/`. La v2 **antes de la revisión** quedó en `VR_Test/Saved/ClaudeScripts/valle_v2_backup_pre_correccion/` (con sus previews).

## v2 (2026-09-27 noche): devolución de Beltrán

### El pedido, textual
> *"El valle debe ondular. No lo veo moverse. Y es muy chico, debe sentirse mucho más grande. Que las colinas estén lejanas, quizás algo de fog. Y se ve muy marcada la línea de donde se acaba el plano, debe ser más suave."*

### El diagnóstico (tres tareas en paralelo, con instrumento validado contra la §12 de la v1 y contra las capturas reales)
Las mediciones y los scripts están en `VR_Test/Saved/ClaudeScripts/valle_v2_diag_{movimiento,linea,escala}/`.

**1. "No lo veo moverse".** La v1 **sí** se movía, pero de una forma que el ojo no registra como ondulación. Fue una decisión de la v1 (solo amplitud, sin traslación, para evitar la vection):
- Era una **onda estacionaria**: cada loma crecía y se achicaba en su lugar. El 74-76 % del cambio de la silueta era el horizonte entero subiendo y bajando a la vez (*heave*). Se lee como una respiración global lenta, no como un oleaje.
- Era **lenta**: la silueta se movía a una mediana de 0,023°/s (≈ 1,4 arcmin/s, en el umbral de detección). Solo el 18 % de las muestras superaba 0,1°/s.
- Tenía **zonas muertas**: la transformación valía 0 hasta 8 m y solo era plena desde 30 m. El 29 % de los vértices de colina no se movía nada en 20 min.
- Además, **el viewport del editor sin *Realtime* no redibuja**: el tiempo avanza, pero la imagen queda congelada hasta que algo la invalida (código de UE 5.8: `LevelEditorViewport.h:693` y `EditorEngine.cpp:1958`). Las capturas del MCP son un solo cuadro. Eso puede explicar que en el editor no se viera nada, pero no es la causa de fondo: con *Realtime*, en PIE o en el visor, el movimiento de la v1 seguía en el umbral.

**2. "Es muy chico".** Todo el relieve caía en el "espacio de acción" (siluetas a 14-33 m). A esa distancia la disparidad estéreo (2,8-6,4 px en el Quest 3) y el paralaje de la cabeza **miden** el tamaño real: lomas de 4 m a 19 m, una maqueta. La base de las lomas estaba a 4,8-10,6° bajo el horizonte, lo que se lee como 6-14 m. La niebla en la silueta era de 0,05-0,22, así que casi no había perspectiva aérea. **Agrandar la v1 de forma uniforme no alcanza:** escalada ×4, la elevación de la silueta se mantiene o sube y el "cuenco" sigue ahí.

**3. "La línea donde se acaba el plano".** Es el borde de la elipse del piso (e = 1), no el borde de la malla. Es un **contorno cerrado de 360°** donde nacen a la vez el anillo y todas las dunas. Se marca por dos cosas, y hacen falta las dos:
- **Geometría:** la altura era C1, no C2. La curvatura salta de 0 a 4,8·10⁻³ cm⁻¹ (mediana) justo en el borde. La luminancia queda con un quiebre, y eso produce una **banda de Mach**.
- **Sombreado:** el brillo rasante `(1 − N·V)^4` tiene su ganancia máxima justo en el rasante. Los primeros grados de inclinación apagan ese brillo (−9 … −17 %/°).

La niebla no es la causa (aporta −2 % de la caída). Medido con G (rampa máxima de ln Y) y Q (quiebre), en %/°: la v1 da **G 116 y Q 112** en el borde, contra **G 4-5 y Q 1-2** de un piso plano infinito. Corregir solo una de las dos cosas no alcanza. Solo C2 baja G a 67, y solo el lóbulo nuevo sobre la geometría v1 empeora el resultado.

### Revisión de la v2 (2026-09-28): lo que estaba mal y cómo se corrigió
Una revisión en cuatro lentes (corrección, confort, imagen y costo; evidencia en `VR_Test/Saved/ClaudeScripts/valle_v2_verif_{correccion,confort,visual,costo}/`) encontró estos problemas en la v2 tal como se había escrito. Todos están corregidos en este documento, en los HLSL y en los scripts.

| Problema (severidad) | Qué pasaba | Corrección |
|---|---|---|
| **La línea no desapareció, cambió de forma** (alta) | El oleaje geométrico entraba entre 15 y 120 m. Sus valles se ocultaban a sí mismos a 40-100 m: bordes de oclusión rectos y horizontales a −1,5/−1,7° (tramos de 46-122° de azimut, escalón de ~6 niveles sRGB, en el 21-48 % de la vuelta). El G/Q de la v2 se había medido sobre el perfil de la superficie, sin oclusión, y no podía verlos | **El oleaje mueve la geometría solo en la capa lejana** (desde `SwellIn` = 280 m, sobre la ladera del anillo, que mira al usuario). En el llano el oleaje queda **solo en el sombreado** (`SwellShade`): la luz ondula y la geometría no, así que no hay bordes de oclusión en el llano. Medido con el instrumento de la revisión: 0 % de bordes en la franja de −1,74°; los que quedan son crestas de colinas medias, curvas (§3.8) |
| **El llano casi no se movía** (media) | El movimiento visible quedaba en la franja lejana; el llano cambiaba menos que en la v1 | El sombreado del oleaje (`SwellShade` 1000, desde 15 m, pleno a 50 m). En 5 s cambia ≥ 3 niveles el 16 % de los píxeles del llano (v2: 5 %, v1: 8 %) y ≥ 1 nivel el 46 % (v2: 17 %, v1: 41 %) |
| **Velocidad vertical > 0,5°/s** (media) | Oleaje + respiración de las colinas llegaban a 0,52°/s (cota rigurosa 0,675); el chequeo por muestreo al azar no podía probar un máximo | El oleaje y la respiración ya no se superponen: la respiración queda solo en las colinas medias (las lejanas se mueven con el oleaje). **Cota rigurosa 0,451°/s** (con los dos términos); `Valley_check.py` la calcula y además **busca** el máximo (200.000 muestras + optimización local, confirmado en el HLSL): 0,451 |
| **Acantilado con `HillEnd < HillFade`** (media) | La rama de las colinas cortaba en `HillEnd` aunque la capa no valiera 0 | `HE = max(HillEnd, HillFade + 1)` en la rama y en la rampa, igual que el modelo. Chequeado con perillas invertidas y con un control negativo |
| **Velocidad lateral subestimada** (media) | La spec daba la velocidad de fase de una onda; los picos de la suma de 4 ondas viajan 2-7 veces más rápido | §3.8 y §11 reescritos con la velocidad de los **rasgos** (picos seguidos en planta y flujo óptico en la imagen). Regla nueva para `LookTo`: `SwellScale·SwellSpeed ≤ 2,5` |
| **Capa viva sin cota** (media) | Modular `SwellAmp` o `MorphAmt` con la respiración (0,1-0,25 Hz) lleva el movimiento a la banda que más marea | §14.3: la capa viva modula el **sombreado** (`SwellShade`), la niebla o el color, no la geometría; o con filtro lento (τ ≥ 20-30 s) |
| **El cielo se dibuja antes que el suelo** (media) | El orden del pase base móvil pone primero la esfera del cielo: el suelo podía pagar también el PS del cielo (+0,3-0,5 ms) | `Sky` con **Treat as Background for Occlusion** (§9, §13) |
| **Lectura del banco** (media) | Píxeles = m1 − m3 cambia la cobertura y subestima | Píxeles = **m0 − m2**, vértices = **m2 − m3** (§8) |
| Menores | Cabecera `SwellScale 2`; límites (bounds) solo válidos con defaults; margen del horizonte optimista; dither subescalado; texto de precisión; ramas sin pista; sobre-sombreado del horizonte; `MorphSpeed` también salta; heave medido en 360° | Cabeceras corregidas y **chequeadas contra la tabla 7.1**; bounds que cubren los rangos (§2); margen ≥ 1,88° en 30 min; `DitherAmt` 1,5; §4.1 corregido; `[branch]` en todas las ramas (llega al SPIR-V como `DontFlatten`); la sombra falsa se calcula solo cerca del metaball; advertencia extendida a `MorphSpeed`; heave en ventanas de 90° |

### Las decisiones (integrando los tres diagnósticos y la revisión)

| Qué | v1 | v2 (revisada) | Por qué |
|---|---|---|---|
| **Escala** | Siluetas a 14-33 m, de 2,7-8,6 m de alto, a 4,8-22,5° de elevación | **Siluetas a 88-517 m (mediana 424 m), a 3,0-10,9° (mediana 6,1°)**. Malla hasta 640 m | Es la composición angular del diagnóstico de escala (su candidato P2). Tiene colinas bajas en ángulo, lejanas, en dos capas y con perspectiva aérea. La disparidad en la silueta baja a 0,18-1,05 px, así que se lee como "vista", no como "acción" |
| **Piso** | Elipse de 19 × 12 m, que termina en un contorno cerrado | **Piso quieto circular, z = 0 exacto hasta 45 m** (las colinas medias empiezan a 45 m y el oleaje geométrico a 280 m). **Normal fija (+Z) hasta 15 m**: ahí no cambia ni el sombreado | Ya no hay ningún contorno donde "empiece" el relieve. Todas las rampas son S5 (C2). Se eliminaron la elipse, el anillo que nacía en e = 1 y el asiento |
| **Movimiento** | La amplitud respira en su lugar (períodos de 41-83 s) | **Oleaje viajero** (4 ondas planas de 100-225 m, períodos de 31-46 s) en dos papeles: **(a) geometría** en la capa lejana, desde 280 m, con **amplitud angular constante** desde 400 m (`A = SwellAmp·S5·r/SwellFar`: 22 m a 470 m); **(b) sombreado** desde 15 m (`SwellShade`: la normal ondula, la geometría no). Las **colinas medias respiran** en su lugar (`MorphAmt` 0,15); las lejanas no | La traslación es lo que el ojo lee como oleaje. En el llano, una ondulación geométrica se ve solo por el sombreado y, además, se oculta a sí misma (bordes rectos): se deja solo el sombreado. En la capa lejana la ladera del anillo mira al usuario y absorbe el oleaje sin bordes rectos. La silueta lejana se mueve igual que en la v2 |
| **Línea** | C1, contorno cerrado, `(1 − N·V)^4` | Altura **C2 en todas partes** (S5). **Sin contorno ni bordes de oclusión rectos**. **Brillo rasante con lóbulo de tope plano** `exp(−(N·V/SheenW)^4)` que **se apaga con la niebla**. El sombreado del oleaje **no** incluye la derivada de su rampa (no dibuja un anillo) | Las tres correcciones del diagnóstico de la línea, más la revisión: la línea nueva de la v2 era de oclusión, no de sombreado |
| **Niebla** | Por distancia: 0,05-0,22 en la silueta | **Por distancia + de altura, integrada a lo largo del rayo** (Quilez). Da 0,14 en el piso a 60 m, 0,36 a 150 m y 0,74 a 470 m; **0,19-0,70 en la silueta (mediana 0,60)** | Es la perspectiva aérea que pide "quizás algo de fog". Los valles lejanos quedan más brumosos que las cimas |
| **Malla** | 79 anillos, 192 sectores, 44 m, 15.169 vértices | **150 anillos, 144 sectores, 640 m, 21.601 vértices** (43.056 triángulos), sin cambios en la revisión. Anillos **densos en radio** en la zona lejana (aspecto 0,6) | El error de silueta lo pone el paso **radial**, porque la mirada es radial. Con esta malla el error queda en p99 **3,3 px** del Quest y las facetas tiemblan p99 0,95 px/s |
| **Cielo** | Esfera de 200 m | **Esfera de 1000 m** (escala 2000), **tratada como fondo** para el orden de dibujo | La de 200 m quedaría **adentro** del terreno y taparía las colinas. Como fondo se dibuja después del suelo |

**Lo que se descartó y por qué:**
- **Agrandar la v1 ×4-5:** se probó en el editor (escala del actor 4) y en los tres diagnósticos. Conserva la composición angular, así que sigue viéndose como un cuenco.
- **La propuesta de oleaje con amplitud plana:** medida, deja la silueta lejana casi quieta.
- **El oleaje geométrico en el llano (la v2 antes de la revisión):** medido, genera bordes de oclusión rectos a −1,5/−1,7°. Para que no se oculte a sí mismo, su amplitud tendría que *bajar* con la distancia (≲ `ez/(k·r)`: 50 cm a 60 m, 20 cm a 150 m), y a esa amplitud solo se ve por el sombreado. Una base que suba bajo el oleaje (otra propuesta de la revisión) lo permitiría, pero vuelve a armar el "cuenco".
- **El sombreado del oleaje con la derivada de su rampa** (gradiente exacto de una superficie virtual): la rampa dibujaba un anillo oscuro a ~40 m.
- **Más amplitud de sombreado** (`SwellShade` > 1000): las respuestas no lineales (oscurecimiento por pendiente, lóbulo rasante) empiezan a oscurecer el llano en promedio; con 1000 el sesgo medio es ≤ 0,7 niveles y el perfil sigue siendo monótono (sin banda oscura).
- **Montar las colinas medias sobre el oleaje** (`h1·(1 + k·s)`): suma poco a la silueta (0,083 → 0,089°/s) y agrega 4 `sin` por vértice en `ValleyHeightVS`.
- **Más sectores sin tocar el paso radial:** medido, no mejora las facetas.

### Qué hay que hacer en Unreal (resumen; el detalle está en la §13)
- **Reimportar la malla** (nuevo FBX; la geometría es la de la v2) con `PositiveBoundsExtension (0, 0, 19000)` y `NegativeBoundsExtension (0, 0, 4000)`.
- **Rearmar los tres Custom** desde `valley_build.json` (71 parámetros: `ValleyHeightVS` 29 entradas, `ValleyGradVS` 31, `ValleyPS` 44).
- `Sky` pasa a **escala 2000** y **Treat as Background for Occlusion**.
- **Revertir el adelanto temporal** del tracker: escala del actor 4 → 1 y `ShadowRadius` del CDO 21,25 → 85. Los defaults del material quedan pisados solos por el rearmado.
- Para juzgar el movimiento en el editor hay que tener **Realtime encendido** (Ctrl+R) o usar PIE/Simulate. Las capturas del MCP son de un solo cuadro.

### Verificado (sin Unreal)
- **Compilación:** `ValleyHeightVS`, `ValleyGradVS` y `ValleyPS` compilan con `dxc` SM6 `-WX`, con `fxc` SM5 (sin advertencias) y con `glslc` HLSL → SPIR-V + `spirv-val`. Las 9 ramas `[branch]` llegan al SPIR-V como `SelectionControl DontFlatten`.
- **HLSL = modelo:** los tres, traducidos mecánicamente, dan lo mismo que el modelo numpy: altura ±6·10⁻⁴ cm, gradiente ±4·10⁻⁷, color ±5·10⁻⁹. Con los defaults, con perillas no default y con las rampas invertidas (`HillEnd < HillFade`, `FarBack < FarCrest`, `SwellIn < SwellNear`).
- **Cabeceras = tabla 7.1:** el default escrito en cada `ScalarParameter` de las tres cabeceras coincide con la tabla.
- **Control negativo:** 8 mutaciones del código fallan, como tienen que fallar.
- **Gradiente analítico** contra diferencias finitas (sin el término de sombreado): 1,5·10⁻⁹. El término de sombreado es exactamente `back·Av·∇s` y no toca `h` ni `hf`.
- **Piso quieto:** h y ∇h valen **0 exacto** a ≤ 10 m del usuario y del metaball durante 1 h; la geometría del oleaje vale 0 exacto a menos de 280 m.
- **Movimiento** (§3.8): silueta con mediana 0,082°/s; en 5 s cambia ≥ 3 niveles el 16 % del llano y el 46 % de la franja de horizonte y colinas.
- **Confort:** cota rigurosa de la velocidad vertical **0,451°/s**; máximo buscado 0,451. Flujo óptico en la imagen: componente normal p99 0,67°/s.
- **Bordes de oclusión bajo el horizonte:** 10-14 % de los azimuts (v2: 21-48 %), todos crestas de colinas, ninguno en la franja recta de la v2.
- **Horizonte:** margen del borde de la malla ≥ **1,88°** en 30 min, con los ojos de 1,0 a 2,1 m.
- **Previews** (Blender headless, malla real) con el sufijo `_v2` en `VR_Test/Saved/ClaudeScripts/`: la vista del usuario en t = 0 y t = 5 s, la diferencia `|t5 − t0|`, la vista lateral equivalente a `cap_exhala_lado.png`, la vuelta de 360°, la planta (entera y ±120 m), las mismas con el actor en Z −90,4 (`_v2_z90`) y `preview_valle_bordes_antes_despues_v2.png` (bordes de oclusión marcados, antes y después de la revisión).

## 0. Resumen

| Pieza | Qué es |
|---|---|
| Forma | Un **piso quieto** (z = 0 exacto) hasta 45 m alrededor del usuario. Después, tres capas radiales: **colinas medias** (45-260 m, hasta 22 m de alto, dunas con umbral, así que hay llanos entre lomas), un **anillo lejano con colinas encima** (280-590 m, 26 m de base + hasta 55 m) que garantiza el horizonte, y el **retiro** detrás de la cresta (todo vale 0 desde 590 m; el borde de la malla, a 640 m, queda oculto) |
| Transformación | **Oleaje viajero**: 4 ondas planas en direcciones repartidas (deriva neta 0,5 %), λ 100-225 m, períodos 31-46 s. **Mueve la geometría de la capa lejana** (desde 280 m, amplitud angular constante desde 400 m) y **ondula el sombreado** desde 15 m (el llano y las colinas medias). Las **colinas medias respiran** un ±15 % en su lugar (períodos 41-83 s) |
| Sombreado | El de Heart: unlit opaco, normal analítica del VS (con el sombreado del oleaje), luz *wrap*, oscurecimiento por pendiente, aclarado de cimas, **lóbulo rasante de tope plano** que se apaga con la niebla, **niebla por distancia + de altura** hacia el color del cielo, y dither estático |
| Sombra | **Factor de forma de una esfera** sobre el plano: `R²/(R²+H²) · (1 + s²/(k·H)²)^(-3/2)`. Se debilita y se ensancha sola con la altura. El BP la mueve con el metaball (sin cambios respecto de la v1). El PS la calcula solo cerca del metaball |
| Cielo | Degradado horizonte → cénit, resplandor rosado cerca del horizonte y una luna grande y tenue con el borde encendido del lado del resplandor. Todo analítico, en una esfera de **1000 m** tratada como fondo |
| Costo | Estimado **1,2-2,5 ms** de GPU (§10), contra ~2,5 ms de presupuesto. **Se mide antes de darlo por bueno** |

## 1. Convenciones (valen para las tres implementaciones)

- **Unidades:** cm y s. Espacio **local** del actor, que va en el origen con escala 1 (se puede rotar en yaw y bajar en Z; ver §11).
- **Ejes (Unreal):** X adelante, Y derecha, Z arriba. El usuario está sentado en el origen con los ojos a ~120 cm (tracking de piso). El metaball está en (380, 0, 125).
- **Ángulos:** el azimut se mide en grados desde +X hacia +Y (0 = al frente, +90 = derecha, −90 = izquierda). La elevación es en grados sobre la horizontal. Dirección: `D(az, el) = (cos el · cos az, cos el · sin az, sin el)`.
- **`S5(a, b, x)`** (quíntica, **C2**) = `t³(t(6t − 15) + 10)` con `t = saturate((x − a)/(b − a))`. Su derivada es `S5'(a, b, x) = 30t²(1 − t)²/(b − a)`, que vale 0 fuera de [a, b] **y en sus extremos, igual que la segunda derivada**. La v2 usa S5 en **todas** las rampas de la altura (la v1 usaba `smoothstep`, que es C1: esa fue la mitad de la "línea"). El `smoothstep` solo queda en el cielo.
- **Color:** todo en **lineal**. En el APK no hay tonemapper (`r.MobileHDR=False`, gotchas 399 y 402): el valor lineal que sale del shader se codifica a sRGB en el hardware y **eso es lo que se ve**. Los valores sRGB de 8 bits entre paréntesis son solo referencia.
- **three.js** usa Y arriba y −Z adelante. Mapeo: `x_ue = −z_three`, `y_ue = x_three`, `z_ue = y_three`. El prototipo convierte a coordenadas UE **al entrar** y hace **toda** la cuenta en coordenadas UE.

## 2. Geometría: `SM_BreathValley_SC`

Es un disco **plano** (z = 0) en malla **polar**, centrado en el **usuario** (el origen), de **640 m de radio**. No tiene forma propia: todo el relieve lo pone el vertex shader, como en Heart. **La revisión no cambió la malla.**

**Anillos, en cuatro zonas:**
1. **Uniforme** (el piso quieto): un anillo cada `ΔA` = **60 cm** hasta 10,8 m (18 anillos). Es plano: la densidad aquí no cambia la imagen, porque la sombra y la distancia se calculan por píxel. Solo evita triángulos enormes bajo los pies.
2. **Geométrica de celdas cuadradas** hasta 60 m: `r ← r·q_B`, con `q_B = 1 + 2π/S`. El tamaño angular de cada celda visto desde el usuario es constante: un LOD continuo, como en Heart.
3. **Geométrica con aspecto 0,6** hasta `R_BACK` = 590 m: `r ← r·q_C`, con `q_C = 1 + 0,6·2π/S`. Las celdas son **más cortas en radio que en arco**, porque la mirada es radial y el error de la silueta lo pone el paso **radial** (la cresta de una loma o de una ola cae entre dos anillos).
4. **Detrás de la cresta:** 4 anillos parejos de 590 a 640 m. Ahí el terreno vale 0 y queda oculto.

```
S      = 144                     # sectores
ΔA     = 60 cm ; R_A = 1080 cm   # zona 1: anillos 60, 120, …, 1080
R_B    = 6000 cm                 # fin de la zona 2 (celdas cuadradas)
q_B    = 1 + 2π/S       = 1.0436332
q_C    = 1 + 0.6·2π/S   = 1.0261799
R_BACK = 59000 cm ; R_MAX = 64000 cm ; N_ATRAS = 4
radios = [ΔA·j  para j = 1..18]
r = radios[-1]
repetir: q = q_B si r < R_B si no q_C ; r' = r·q
         si r' ≥ R_BACK − 0.5·(r' − r): salir     # sin anillo astilla antes de R_BACK
         r = r' ; agregar r
agregar R_BACK ; agregar R_BACK + (R_MAX − R_BACK)·j/4  para j = 1..4
```

**Resultado: 150 anillos, 21.601 vértices, 43.056 triángulos.**
- El primer anillo geométrico está en 1127,12 cm.
- Los últimos son 55961,2 / 57426,2 / 59000 / 60250 / 61500 / 62750 / 64000 cm.
- Hay 25 anillos hasta 15 m, 58 hasta 60 m, 93 hasta 150 m, 119 hasta 300 m y 146 hasta 590 m.
- Paso radial: 2,6 m a 100 m y 12,2 m a 470 m. Arco por sector a 470 m: 20,5 m.

**Error de silueta de la malla** (triángulos reales contra la función continua, medido en `preview_breath_valley.py`), en px del Quest 3 (25 px/°):
- **p50 0,60 · p90 1,90 · p99 3,33 · máximo 4,3**.
- Temblor de las facetas en 1 s: p90 0,47 y p99 0,95 px.
- Alternativas medidas con el oleaje de la v2:

| Malla | Vértices | Error p99 | Temblor p99 |
|---|---|---|---|
| 160 sectores, aspecto 1,25 | 18.241 | 8,6 px | 2,1 px/s |
| 224 sectores, aspecto 1,75 | 29.569 | 8,0 px | — |
| 224 sectores, aspecto 1,0 | 37.409 | 3,2 px | — |
| **144 sectores, aspecto 0,6 (elegida)** | **21.601** | **3,2-3,3 px** | **0,9-1,0 px/s** |

**Topología (idéntica en Blender y three.js):**
- Vértice 0 = centro (0, 0, 0). Vértice `1 + i·S + s` = anillo `i`, sector `s`, en `(r_i cos(2πs/S), r_i sin(2πs/S), 0)`, con `s = 0` en +X y el ángulo creciendo hacia +Y.
- Abanico central: `(0, idx(0, s), idx(0, s+1))`.
- Entre anillos, **dos triángulos explícitos**: con `a = idx(i, s)`, `b = idx(i+1, s)`, `c = idx(i+1, s+1)` y `d = idx(i, s+1)`, van `(a, b, c)` y `(a, c, d)`. El sector se toma módulo S.
- Vistos desde +Z giran en sentido antihorario: la normal es +Z. El material es two-sided.
- **Normales:** +Z, suaves (el shader no las usa). **UV0:** planar, `u = x/(2R_MAX) + 0.5`, `v = y/(2R_MAX) + 0.5`, sin costura (el shader tampoco las usa).

**Generador Blender:** `scripts/gen_breath_valley.py`. Es headless, construye en **metros** y exporta FBX con `apply_unit_scale=True`, igual que Heart. Sale a `VR_Test/Saved/ClaudeScripts/SM_BreathValley_SC.fbx` e imprime `LISTO ... anillos=150 verts=21601 tris=43056`, el radio efectivo en Unreal (64000 cm) y la línea `BOUNDS`.

**Import en Unreal** (`/Game/SoulCharger/Mechanics/Breath/Valley/SM_BreathValley_SC`, **reimport sobre el mismo asset**):
- Sin colisión, sin UV de lightmap y sin Nanite.
- Verificar con `StaticMeshTools.get_bounds` que X e Y queden en ±64000 y que haya 21.601 vértices.
- 🔴 **Límites:** la malla es plana, así que el `BoundsScale` del componente no sirve (gotcha 134). En el asset van **`PositiveBoundsExtension = (0, 0, 19000)`** y **`NegativeBoundsExtension = (0, 0, 4000)`**.
  - Cubren el **tope de los rangos sugeridos** de la 7.1 (`HillAmp` 4000, `FarBase` 5000, `FarAmp` 8000, `FarBack` 63500, oleaje en su límite de confort) con 15 % de margen. Cota analítica conservadora: `h ≤ max(HillAmp, FarBase + FarAmp + SwellAmp·FarBack/SwellFar)` y `h ≥ −SwellAmp·FarBack/SwellFar` (sin descontar el anillo): +15.984 / −2.984 cm en el tope de los rangos; +10.873 / −2.773 cm con los defaults. La amplitud del oleaje sigue creciendo con r detrás de la cresta, por eso la cota usa `FarBack` y no `FarCrest`.
  - En los vértices, con los defaults y durante 30 min, se midió de −389 a +10.002 cm.
  - Con los defaults la cámara queda siempre adentro de la caja de ±640 m: no hay culling por frustum ni por oclusión aunque la extensión quedara corta. Es una garantía, no un ajuste fino; subirla no cuesta nada.
- En three.js: `mesh.frustumCulled = false`.

## 3. La altura h(x, y, t)

Posición local `p = (x, y)` en cm, `r = |p|` y tiempo `t` en s (`View.GameTime`). Todas las constantes y los parámetros con sus valores por defecto están en la §7.1. **Todo es radial en r** (no hay elipse): la zona quieta es un círculo alrededor del usuario.

### 3.1 Capa 1: colinas medias (banda de 45 a 260 m)
```
HE   = max(HillEnd, HillFade + 1)                                          # la rampa de apagado nunca se invierte
envH = S5(HillNear, HillFull, r) · (1 − S5(HillFade, HE, r))              # 0 → 1 de 45 a 120 m; 1 → 0 de 190 a 260 m
σH   = campo de dunas (§3.3) con escala HillScale y giro HillSeed, QUE RESPIRA
fH   = S5(DuneLow, DuneHigh, σH)                                           # umbral: llanos entre lomas, cimas redondas
h1   = HillAmp · envH · fH
```
- **`HE` (revisión):** con `HillEnd < HillFade`, la v2 cortaba la rama en `HillEnd` aunque la capa todavía no valiera 0 (un acantilado circular, justo una "línea"). Ahora la rama y la rampa usan `HE`, como el modelo.

### 3.2 Capa 2: anillo lejano + colinas lejanas (de 280 a 590 m)
```
ring = S5(FarIn, FarCrest, r)                 # 0 en 280 m → 1 en la cresta, 470 m
envF = S5(FarIn, FarFull, r)                  # colinas lejanas plenas desde 400 m
σF   = campo de dunas (§3.3) con escala FarScale y giro FarSeed, SIN respiración (las mueve el oleaje)
fF   = S5(−0.7, 1.2, σF)                      # umbral más bajo que el de las medias: colinas más anchas (constante del código)
h2   = FarBase · ring + FarAmp · envF · fF
```
El anillo es la **garantía del horizonte**: con `FarBase` = 26 m a 470 m, el horizonte queda tapado aunque σF caiga en un valle. Su ladera (pendiente media 0,14, hasta 0,26) **mira al usuario**: es la que absorbe el oleaje geométrico sin bordes de oclusión rectos.

### 3.3 El campo de dunas (las mismas 4 dunas de la v1, escaladas y giradas por capa)

| i | ángulo αᵢ (°) | longitud de onda λᵢ (cm) | peso aᵢ | fase φᵢ (rad) | período Tᵢ (s) | fase temporal ψᵢ (rad) |
|---|---|---|---|---|---|---|
| 0 | 18 | 3000 | 1,00 | 0,0 | 53 | 0,0 |
| 1 | 101 | 2200 | 0,75 | 1,7 | 67 | 2,1 |
| 2 | 143 | 1650 | 0,55 | 4,1 | 41 | 4,4 |
| 3 | 232 | 1250 | 0,35 | 2,9 | 83 | 1,3 |

```
kᵢ  = (2π / (λᵢ · Scale)) · (cos(αᵢ + Seed), sin(αᵢ + Seed))       # ángulos en grados; Scale/Seed = Hill… o Far…
mᵢ  = sin(2π · frac(MorphSpeed · t / Tᵢ) + ψᵢ)                      # uniforme por cuadro; fase reducida con frac
σH  = Σ aᵢ (1 + MorphAmt · mᵢ) sin(kᵢ · p + φᵢ) / 2,65             # colinas medias: respiran
σF  = Σ aᵢ sin(kᵢ · p + φᵢ) / 2,65                                  # colinas lejanas: no respiran
```
- Con `HillScale` 8 las colinas medias tienen λ de 100-240 m. Con `FarScale` 22 las lejanas tienen λ de 275-660 m.
- `HillSeed` y `FarSeed` giran cada campo: son las perillas para **elegir la composición** sin tocar la forma.
- **La respiración (`MorphAmt` 0,15)** es la transformación de la v1, ahora secundaria y **solo en las colinas medias**: cada duna crece y se achica ±15 % en su lugar. **Revisión:** las colinas lejanas ya no respiran. Así la respiración (colinas medias, hasta 260 m) y el oleaje geométrico (desde 280 m) no se superponen y la velocidad vertical queda por debajo de 0,5°/s con una cota rigurosa (§3.8). Además ahorra 4 `sin` por vértice lejano.
- **`MorphSpeed` es para fijar y dejar**, como `SwellSpeed`: multiplica a t, así que cambiarlo en vivo hace saltar la fase de la respiración.

### 3.4 Capa 3: el oleaje viajero (geometría lejos, sombreado cerca)

Son cuatro ondas planas, constantes del código, escritas una por una:

| j | dirección αⱼ (°) | λⱼ (cm, × `SwellScale`) | período Tⱼ (s) | peso wⱼ | fase cⱼ (vueltas) |
|---|---|---|---|---|---|
| 0 | 20 | 9000 | 42 | 1,00 | 0,00 |
| 1 | 175 | 7000 | 36 | 0,85 | 0,37 |
| 2 | 255 | 5500 | 31 | 0,70 | 0,73 |
| 3 | 95 | 4000 | 46 | 0,40 | 0,18 |

```
dⱼ  = (cos(αⱼ + SwellSeed), sin(αⱼ + SwellSeed))
gⱼ  = 2π · frac( (dⱼ · p) / (λⱼ · SwellScale) + cⱼ − frac(SwellSpeed · t / Tⱼ) )      # en vueltas, reducida ANTES del sin
s   = Σ wⱼ sin(gⱼ) / 2,95                                             # |s| ≤ 1
SI  = max(SwellIn, SwellNear)
A   = SwellAmp · S5(SI, SwellFar, r) · r / SwellFar                   # GEOMETRÍA: amplitud ANGULAR constante desde SwellFar
Av  = SwellShade · S5(SwellNear, SwellShadeFull, r)                   # SOMBREADO: solo en la normal
h3  = A · s                                                           # va a la altura
∇sombra = Av · ∇s                                                     # va solo al gradiente que usa el PS (§3.6)
```
- **Geometría: 0 exacto a menos de `SwellIn` (280 m)**, con derivada 0 y segunda derivada 0 en el borde. Empieza sobre la ladera del anillo lejano, que mira al usuario. **Amplitud:**

| Distancia | 280 m | 300 m | 340 m | 400 m | 470 m | 560 m |
|---|---|---|---|---|---|---|
| A (cm) | 0 | 51 | 800 | 1.880 | 2.209 | 2.632 (× retiro) |

  Desde 400 m, A/r = 0,047 rad (2,7°) cuando las 4 olas se alinean; lo típico es la mitad.
- **Sombreado: desde `SwellNear` (15 m)**, pleno desde `SwellShadeFull` (50 m). Suma `Av·∇s` a la pendiente con que el PS arma la normal; **no mueve la geometría**, así que en el llano no hay bordes de oclusión. Con `SwellShade` 1000 la pendiente de sombreado es de 0,14 (rms) y hasta 0,39: la luz del llano ondula ±6 niveles sRGB y viaja. Es la amplitud equivalente de unas olas de 10 m, pero sin relieve.
  - **No incluye `Av'·s`** (la derivada de su rampa). Con ese término, la rampa dibujaba un anillo oscuro a ~40 m.
  - El sesgo medio del llano por las respuestas no lineales del sombreado (oscurecimiento por pendiente, lóbulo rasante) es ≤ 0,7 niveles, y el perfil medio de luminancia sigue creciendo con la distancia: no hay banda.
- **Cada onda viaja** en +dⱼ a `cⱼ = λⱼ·SwellScale·SwellSpeed/Tⱼ` = 5,4 / 4,9 / 4,4 / 2,2 m/s (velocidad de **fase**; los picos de la suma viajan más rápido, ver §3.8).
  - Las direcciones están repartidas: la suma de wⱼ·cⱼ·dⱼ da una **deriva neta del 0,5 %**, así que no simula que el usuario se traslade.
  - Como son ondas planas, no hay giro neto.
- **Frecuencia en cada punto:** 0,022-0,032 Hz. Es 6-18 veces menos que el pico de mareo visual (0,2-0,4 Hz; Diels y Howarth 2013).
- **`SwellSpeed` y `MorphSpeed` son para fijar y dejar:** cambiarlos en vivo hace saltar la fase, porque multiplican a t. Si hace falta animarlos (capa viva), la fase se integra en el BP.

### 3.5 Total y retiro
```
back = 1 − S5(FarCrest, FarBack, r)            # 1 hasta la cresta, 0 desde 590 m: el borde de la malla queda oculto
h    = back · (h1 + h2 + h3)
hf   = saturate(back · (envH·fH + envF·fF))    # "fracción de loma" 0..1, va al PS (aclarado de cimas)
```

**Ramas por radio (costo).** Cada capa va en un `if [branch]` por r (la pista `[branch]` llega al SPIR-V como `DontFlatten`: el compilador del driver no aplana las ramas):
- Colinas medias: `HillNear < r < HE`.
- Lejos: `FarIn < r < FarBack`.
- Oleaje: en `ValleyHeightVS`, `SI < r < FarBack` (solo la geometría); en `ValleyGradVS`, `SwellNear < r < FarBack` (la geometría y el sombreado).

Fuera de su banda, cada capa vale **0 exacto con derivada 0** (la quíntica es plana en sus extremos), así que saltearla no cambia nada. La respiración (`mᵢ`) también se calcula adentro de la rama de colinas. Como la malla va anillo por anillo, las ramas son coherentes dentro de cada grupo de vértices. Con los defaults:

| Vértices | `ValleyHeightVS` evalúa | `ValleyGradVS` evalúa |
|---|---|---|
| 17 % (hasta 15 m) | nada | nada |
| 22 % (de 15 a 45 m y de 260 a 280 m) | nada | el oleaje (sombreado) |
| 42 % (colinas medias, 45-260 m) | las colinas | las colinas + el oleaje (sombreado) |
| 19 % (capa lejana, 280-590 m) | lejos + el oleaje | lejos + el oleaje |

### 3.6 El gradiente (lo que devuelve `ValleyGradVS`)
Es el **gradiente exacto de h más el término de sombreado del oleaje**. Todas las envolventes son radiales, así que su derivada es `(d/dr)·p/r`:
```
∇h1 = HillAmp · [ (envH)' · fH · p/r  +  envH · S5'(DuneLow, DuneHigh, σH) · ∇σH ]
∇h2 = [ FarBase · ring' + FarAmp · envF' · fF ] · p/r  +  FarAmp · envF · S5'(−0.7, 1.2, σF) · ∇σF
∇h3 = A' · s · p/r  +  A · ∇s ,   A' = SwellAmp · (S5'·r + S5) / SwellFar
∇σ  = Σ aᵢ (1 + MorphAmt·mᵢ) cos(kᵢ·p + φᵢ) kᵢ / 2,65          (sin el factor de respiración en σF)
∇s  = Σ wⱼ cos(gⱼ) · 2π dⱼ / (λⱼ · SwellScale) / 2,95
grad = back · (∇h1 + ∇h2 + ∇h3 + Av · ∇s)  +  back' · (h1 + h2 + h3) · p/r ,  back' = −S5'(FarCrest, FarBack, r)
```
Con `SwellShade` 0 el gradiente es exactamente ∇h (así lo verifica `Valley_check.py` contra diferencias finitas).

Guardas numéricas:
- `r` se toma como `max(r, 1)` en `p/r`. Donde actúa, el término que multiplica vale 0.
- Los anchos de cada rampa se toman como `max(b − a, 1 cm)` (`max(DuneHigh − DuneLow, 0,01)` en el umbral).
- `HE = max(HillEnd, HillFade + 1)`, `FarCrest ≥ FarIn + 1`, `FarBack ≥ FarCrest + 1`, `SI = max(SwellIn, SwellNear)` y `SwellFar ≥ SI + 1`.

### 3.7 Por qué así
- **Radial y en capas, no una elipse.** La "línea" de la v1 era un contorno cerrado donde todo nacía a la vez. En la v2 cada capa entra con su propia rampa ancha, a distinta distancia. Se cumple la ley de anchos del diagnóstico de la línea: `Π = A·d²/(He·W²) ≤ 0,3`.
- **El llano no se oculta a sí mismo (revisión).** Un punto del llano se ve si el ángulo `(h − ez)/r` crece a lo largo de cada rayo. Para una ondulación de amplitud A y número de onda k eso exige `A ≲ ez/(k·r)`: unos 50 cm a 60 m y 20 cm a 150 m. Más amplitud produce bordes de oclusión, y como la rampa de entrada es radial, esos bordes salen **rectos y horizontales** (la "línea" nueva de la v2). A la amplitud permitida, una ondulación en el llano solo se ve por el sombreado; por eso el llano ondula **en la luz** y la geometría del oleaje empieza donde hay una ladera que mira al usuario (el anillo lejano).
- **Traslación en lugar de amplitud.** Un patrón que viaja activa los detectores de movimiento; un cambio gradual en el lugar no (ceguera al cambio). Para no tener vection hacen falta tres cosas, y el oleaje las cumple:
  - Deriva neta ~0: las 4 direcciones se compensan.
  - Nada se mueve cerca: hasta 15 m no cambia ni el sombreado, y la geometría está quieta hasta 45 m (las colinas medias, que solo respiran) y hasta 280 m (el oleaje).
  - Un marco quieto: el piso, el metaball y el cielo con la luna.
- **Amplitud angular constante.** El límite de confort es angular (°/s). Con `A ∝ r`, todas las distancias usan el mismo margen, y la silueta lejana (el 61 % de los azimuts, a más de 400 m) se mueve tanto como la cercana.
- **Costo por vértice.** Sin bucles ni arreglos (gotcha 399). Las fases se reducen con `frac` antes del `sin`, así que el argumento queda acotado en Adreno aunque la sesión dure horas.

### 3.8 Propiedades verificadas (con los defaults)

Mediciones con el modelo (`valley_model.py`), el render por píxel del verificador visual (25 px/°, oclusión exacta) y el flujo óptico por bloques del verificador de confort. Scripts de la revisión en `VR_Test/Saved/ClaudeScripts/valle_v2_revision/`.

| Propiedad | Valor | Regla para no romperla al tocar perillas |
|---|---|---|
| Silueta | Elevación de 3,0 a 10,9° (mediana 6,1°); distancia de 88 a 517 m (mediana 424 m). El 25 % de los azimuts tiene la silueta en una colina media (< 280 m), el 15 % entre 280 y 400 m y el 61 % a más de 400 m | — |
| Borde de la malla oculto | Margen ≥ **1,88°** en 30 min (cada 30 s, 360 azimuts, ojos de 1,0 a 2,1 m; el peor, t = 1410 s con los ojos a 2,1 m). No hay cielo bajo el horizonte ni terreno visible a más de 517 m. Cota analítica: > 0,4° aunque las 4 olas se alineen en la cresta | `FarBase − SwellAmp·FarCrest/SwellFar ≥ 150` cm y `FarBack ≤ 63500` (R_MAX − 5 m). Hoy 2600 − 2209 = 391 ✔ |
| Piso quieto | h y ∇h = **0 exacto** a r < 15 m (≥ 10 m alrededor del usuario y del metaball); h = 0 exacto hasta 45 m (no hay colinas) y la geometría del oleaje vale 0 hasta 280 m | `SwellNear ≥ 1400`; `HillNear`, `FarIn` y `SwellIn` > `SwellNear` |
| Disparidad estéreo en la silueta | De 0,18 a 1,05 px (la v1, de 2,8 a 6,4 px). Medido antes de la revisión, que no cambió la forma de las siluetas | — |
| Niebla en la silueta | De 0,19 a 0,70 (mediana 0,60). Medido antes de la revisión, que no cambió la niebla ni las siluetas | §4.1 |
| Velocidad de la silueta | Mediana **0,082°/s**, p90 0,24, máximo 0,44; supera 0,1°/s en el 43 % de las muestras (v1: 0,023 y 18 %; v2 antes de la revisión: 0,115 y 56 %, con el oleaje geométrico en las colinas medias) | — |
| Cambio de la imagen en 5 s (frente, ±60°, render por píxel) | Llano (−3 a −0,4°): ≥ 1 nivel el **46 %**, ≥ 3 niveles el **16 %** (v1: 41 y 8 %; v2 antes: 17 y 5 %). Horizonte y colinas (≥ −0,4°): ≥ 1 nivel el 71 %, ≥ 3 niveles el **46 %** (v1: 24 % con ≥ 3; v2 antes: 38 %). Piso cercano (< −3°): 0 % | `SwellShade` y `SwellShadeFull` (§7.1) |
| Sube y baja coherente de la silueta (*heave*, \|media\| / media de \|cambio\|) | 0,09 en la vuelta entera; **0,22-0,24 (mediana) en ventanas de 90°**, lo que entra en el campo visual. El verificador de confort midió en la v2, en ventanas de 90°, hasta 0,48 (a yaw 45°) y una inclinación de la silueta de hasta 5° en 20 s (≤ 0,56°/s) entre los bordes del campo; la capa lejana no cambió con la revisión, así que esos números siguen valiendo como orden de magnitud. En el visor, mirar hacia yaw ~45° y ~180° | — |
| Velocidad **vertical** angular | **Cota rigurosa 0,451°/s** (oleaje a 400 m: 0,451; respiración de las colinas medias a ~120 m: 0,232; no se superponen). El máximo **buscado** (200.000 muestras de área × tiempo + optimización local desde las 12 mejores, confirmado en el HLSL) es 0,451: la cota es ajustada | **Límite de diseño 0,5°/s**. Oleaje: `SwellAmp·SwellSpeed/SwellFar ≤ 0,047`. Respiración: `MorphAmt·MorphSpeed ≤ 0,3`. Y `SwellIn ≥ HillEnd`: si se superponen, las cotas se suman (`vm.cota_vel_vertical_deg` lo calcula) |
| Velocidad **lateral** de los rasgos (picos del oleaje geométrico seguidos en planta, 16 instantes, 0,5 s) | La suma de 4 ondas tiene picos que viajan mucho más rápido que las ondas: en planta, mediana 2,9-3,6 m/s, p90 16,5-18 m/s, máximo ~30 m/s (las fases van a 2,2-5,4 m/s). Vistos desde los ojos (componente tangencial): **280-400 m: mediana 0,35°/s, p90 1,64, máximo 3,7** (7,5 % > 2,5°/s); **400-590 m: mediana 0,26, p90 1,37, máximo 3,5** (2,7 % > 2,5°/s). Son picos raros y de bajo contraste, en la franja lejana | `SwellScale·SwellSpeed ≤ 2,5` (el valor actual): la velocidad de todos los rasgos escala con ese producto. Si en el visor se ve "agitado": `SwellSpeed` 0,7 (−30 %) |
| Movimiento en la imagen (flujo óptico por bloques, 4 vistas × 3 instantes, método del verificador de confort) | Componente normal: mediana 0,036°/s, p90 0,23, p99 0,67, máximo 2,8 (0,01 % de los bloques > 2,5°/s). Donde el bloque permite medir el vector 2D: mediana 0,33°/s, p90 1,9, máximo 5,2 (v2 antes: p90 1,0 y máximo 3,1). El aumento es el sombreado del llano, que viaja; su contraste por bloque es de 1,4-2,9 niveles | `SwellShade` más bajo o `SwellShadeFull` más lejos bajan el movimiento del llano |
| Bordes de oclusión bajo el horizonte (la "línea" nueva de la v2; métrica del verificador visual) | Azimuts con borde de escalón ≥ 3 niveles: **10 / 13 / 14 %** en t = 0 / 20 / 40 s (v2 antes: 39 / 21 / 48 %). En la franja recta de la v2 (−1,74°): **0 %**. En el frente (\|az\| 17-60°, 5 min): instantes con ≥ 10° de borde 48 % (v2: 92 %), mediana 9,5° de 86° (v2: 34°). Todos los que quedan son **crestas de colinas medias** a 70-210 m, a −0,5/+0,4°: curvas (0,5-0,9° de rango de elevación en tramos de 12-20°). Ningún tramo recto (≥ 5° con < 0,3° de rango). Con el actor en Z −90,4: 57 % de los instantes (v2: 97 %) y un tramo recto de 6,5° | Las colinas medias empiezan en `HillNear`: acercarlas agrega crestas bajo el horizonte |
| Línea del piso (métrica G del verificador visual, %/°, banda de −8 a −0,25°) | Por píxel (0,04°): mediana 12-16, p90 46-116, máximo 127-338 (v2 antes: p90 173-313, máximo 332-417; los máximos que quedan son las crestas de las colinas). Sobre 0,2°: máximo 49-94 (v2 antes: 72-89; v1: 122). El G/Q de la v2 (G 3,4 entre 8 y 60 m) se había medido sin oclusión: **no alcanza para declarar que no hay línea** | Todas las rampas son S5; lóbulo rasante `SheenW` ≥ 0,25 |

## 4. Sombreado mate del suelo (PS, `Part` 0)

Entradas interpoladas: `VI1 = (gx, gy, h, hf)` desde el VS (el gradiente de la §3.6, **con el sombreado del oleaje**) y `LPi` (posición local). `V = normalize(CamL)` apunta del píxel a la cámara y `dv = −V` es la dirección de la mirada.
```
N     = normalize(−VI1.x, −VI1.y, 1)
wrap  = saturate((N·LightDir + Wrap) / (1 + Wrap))
k     = lerp(ShadeFloor, 1, wrap) · saturate(1 − SlopeDark · (1 − N.z))    # pendiente = más oscuro, desde cualquier lado
col   = lerp(ColShadow, ColLit, k)
col   = lerp(col, ColLit, CrestLight · hf²)                                # cimas un poco más claras
fres  = exp(−(saturate(N·V) / SheenW)^4)                                    # LÓBULO DE TOPE PLANO: pendiente 0 en el rasante
fwd   = saturate(0.5 + 0.5 · dv·LightDir)                                  # el brillo rasante es más fuerte a contraluz
col   = lerp(col, ColSheen, saturate(Sheen · fres · lerp(SheenBack, 1, fwd) · (1 − fog)))   # se apaga con la niebla
col  *= 1 − O · (1 − ShadowTint)                                           # sombra del metaball (§5), solo cerca de él
col   = lerp(col, cielo(dv) sin luna, fog) + dither                         # niebla (§4.1)
```
- **El lóbulo (v2)** reemplaza a `(1 − N·V)^SheenPow`, cuya ganancia era máxima justo en el rasante (dfres/d(N·V) ≈ −3 a 12,5 m). Con `SheenW` 0,3, el lóbulo:
  - Vale ~1 en todo el piso lejano: en el piso, N·V ≈ 1,2 m / d.
  - Baja entre 3 y 5 m.
  - Tiene ganancia ~0 en el rasante, unas 7 veces menos que la v1.
  - `Sheen` baja de 0,4 a **0,28** para conservar el tono del piso entre 5 y 60 m (±5 niveles sRGB, medido).
- **`· (1 − fog)`** (v2) apaga el brillo rasante donde hay niebla. Sin eso, el llano rasante lejano armaba una franja más clara que el cielo justo bajo el horizonte: luminancia 0,51 contra 0,37.
- **El sombreado del oleaje** (revisión) entra por la normal: la luz *wrap* lo muestra (±6 niveles con `SwellShade` 1000); el lóbulo rasante casi no responde (es plano cerca del rasante), y el oscurecimiento por pendiente responde en segundo orden (≤ 0,7 niveles de sesgo medio).
- **Luz:** `LightAz = 20°`, `LightEl = 25°`, del lado del resplandor. Las caras que miran al usuario quedan en la sombra lavanda-azul y las cimas y los rasantes se encienden en rosado.
- **Colores por defecto** (sin cambios): `ColLit` (0,434, 0,527, 0,855) = sRGB (176, 192, 238) · `ColShadow` (0,061, 0,117, 0,352) = (70, 96, 160) · `ColSheen` (0,855, 0,761, 0,913) = (238, 226, 245).
- **Dither estático:** el mismo hash de `HeartScapePS` sobre `SvPosition`, `DitherAmt · (hash − 0,5)/255` sumado en **lineal**. **Revisión:** `DitherAmt` pasa de 1 a **1,5**. El hardware codifica en sRGB: ±0,5/255 en lineal son solo ±0,29-0,38 LSB de sRGB en los tonos del piso (p-p < 1 LSB); con 1,5 quedan en ±0,44-0,57. El degradado del piso bajo el horizonte es de 0,35 niveles/° (un escalón cada ~70 px del Quest): es el punto débil del banding. Mirarlo en el visor de 2 a 10° bajo el horizonte.

### 4.1 Niebla: por distancia + de altura, integrada a lo largo del rayo
La densidad es `1/FogDist + exp(−z/HFogFall)/HFogDist`. Integrada exactamente a lo largo del rayo recto entre la cámara (altura `z0`) y el píxel (altura `z1`):
```
z1  = max(VI1.z, 0) ;  z0 = max(VI1.z + V.z · Dist, 0)        # alturas en local; z0 = la cámara
F   = |z1 − z0| > 1 ?  HFogFall · (e^(−z0/HFogFall) − e^(−z1/HFogFall)) / (z1 − z0)  :  e^(−z0/HFogFall)
τ   = (Dist − FogStart) · (1/FogDist + F/HFogDist)            # solo si Dist > FogStart; si no, fog = 0
fog = FogMax · (1 − e^(−τ))
```
- **Valores**, con `FogStart` 15 m, `FogDist` 450 m, `FogMax` 0,9, `HFogDist` 600 m y `HFogFall` 15 m:

| Distancia (piso) | 20 m | 30 m | 60 m | 100 m | 150 m | 300 m | 470 m | 600 m |
|---|---|---|---|---|---|---|---|---|
| Niebla | 0,017 | 0,050 | 0,142 | 0,250 | 0,363 | 0,597 | 0,742 | 0,804 |

  En las cimas: 0,22 en una de 15 m a 100 m, 0,31 en una de 20 m a 150 m y 0,63 en una de 60 m a 470 m. Los valles lejanos quedan más brumosos que las cimas: la perspectiva aérea que hace leer la distancia (contraste ∝ e^(−σd); O'Shea et al. 1994).
- **Se probó más fuerte** en el diagnóstico de escala (`FogDist` 300 m, `FogMax` 0,92): la silueta lejana quedaba a 0,78, demasiado lavada.
- **Rama dinámica (`[branch]`):** el piso a menos de `FogStart` (la zona quieta, casi medio campo visual) no calcula ni la niebla ni el cielo.
- **Precisión (revisión):** `Dist` llega a ~100.000 cm en la esfera del cielo, por encima del máximo de half (65.504), y `1 − cosA` en el borde de la luna vale ~0,012. En fp16 la niebla y la luna se rompen. Hoy todo es fp32: con `MFPM_Full_MaterialExpressionOnly` el motor define `FORCE_MATERIAL_FLOAT_FULL_PRECISION` (`MaterialShared.cpp:2894`), así que `MaterialFloat` es `float`; `CameraVector` y los interpoladores también son float. **No se puede salir de `MFPM_Full_MaterialExpressionOnly`.**

## 5. La sombra falsa del metaball

**Sin cambios de modelo en la v2.** La sombra asume el piso en z = 0 bajo el metaball, y la v2 lo garantiza a r < 45 m (y la normal +Z a r < 15 m).

**Modelo.** Es la oclusión de la luz de cielo que produce una esfera de radio R a una altura H sobre el suelo:
```
Hs   = max(ShadowCenter.z − h, 1)                 # altura del centro del metaball sobre ESTE punto del suelo
w    = max(ShadowSoft · Hs, 1)                     # ancho de la penumbra: crece solo con la altura
d²   = |LPi.xy − ShadowCenter.xy|²
si d² < 144 · w²:                                  # (revisión) solo a menos de 12 anchos de penumbra
  peak = ShadowStrength · Rs² / (Rs² + Hs²)        # intensidad en el centro: baja sola con la altura
  q    = 1 + d² / w²
  O    = min(saturate(peak · q^(−3/2)), ShadowMax) # q^(−3/2) = rsqrt(q)³, sin pow
  col *= 1 − O · (1 − ShadowTint)                  # tinte multiplicativo azulado, no gris
```
- **La rama (revisión)** ahorra la sombra al resto del suelo: afuera `q^(−3/2)` < 6·10⁻⁴, así que O < 9·10⁻⁴ (menos de 0,1 nivel). Con el metaball actual el radio de la rama es de ~12 m. Ahorra un 7-9 % del PS del suelo (~0,1 ms).
- **Valores para el metaball actual** (centro a 125 cm, `ShadowRadius` 85, `ShadowStrength` 1,5, `ShadowSoft` 0,8): O = **0,47** en el centro, 0,17 a 1 m y 0,04 a 2 m. El piso bajo el metaball queda en sRGB (128, 141, 197).
- **Parámetros que escribe el BP** (grupo `9 - Interno`): `ShadowCenter` (local, cm), `ShadowRadius` y `ShadowStrength`. Siguen al metaball y a su escala (tracker del BP: `ShadowScaleRef` 1,0).

## 6. El cielo (`Part` 1, esfera de **1000 m**)

**Sin cambios de fórmula.** Se evalúa **solo con la dirección de la mirada** `dv` y **sale temprano**:
```
cielo = lerp(SkyHorizon, SkyZenith, smoothstep(0, SkyGradTop, dv.z))
hz    = normalize(dv.xy) ;  gh = normalize(GlowDir.xy)
gaz   = max(hz·gh, 1e-6)^GlowPow
gel   = 1 − smoothstep(0, GlowHeight, |dv.z − GlowDir.z|)
cielo = lerp(cielo, SkyGlow, saturate(GlowAmt · gaz · gel))
cosA  = dv·MoonDir ;  ρ = sqrt(max(1 − cosA, 0) / (1 − MoonCosR))
si ρ < 1 + MoonEdge:
  disco = 1 − smoothstep(1 − MoonEdge, 1 + MoonEdge, ρ)
  o     = dv − MoonDir·cosA ;  gm = GlowDir − MoonDir·(GlowDir·MoonDir)
  lado  = 0.5 + 0.5 · (o·gm)/(|o|·|gm|)
  borde = smoothstep(0.6, 1, ρ) · lado²
  cielo = lerp(cielo, MoonColor, saturate(MoonOpacity · disco · (MoonFill + MoonRim · borde)))
salida = cielo + dither
```
- 🔴 **La esfera pasa de 200 m a 1000 m de radio** (`/Engine/BasicShapes/Sphere` con **escala 2000**). El terreno llega a 640 m: la esfera de 200 m quedaría adentro y taparía las colinas. A 1000 m su disparidad es de 0,09 px (infinito de verdad). La profundidad es *reverse-Z* con far infinito y near de 10 cm (Config no los cambia): a 1 km el escalón de D24 es de 0,6 m, sin z-fighting.
- 🔴 **Orden de dibujo (revisión):** el pase base móvil ordena por la distancia del origen de los límites a la cámara, en cubetas log2. Con la extensión de límites del suelo, su centro sube a decenas de metros de la cámara; el centro de la esfera del cielo está en el actor, a 1-2 m. Así el cielo se dibuja **antes** que el suelo, y si el LRZ del Adreno no descarta esos fragmentos, el ~62 % de píxeles que son suelo paga además el PS del cielo (+0,3-0,5 ms). La corrección: en el componente `Sky`, **`Treat as Background for Occlusion`** (`bTreatAsBackgroundForOcclusion = true`); según la lectura del código del motor en la verificación de costo, las primitivas de fondo se dibujan al final (`MobileBasePass.cpp:937`) y el bit de fondo pesa más que la distancia en la clave de orden.
- **Defaults** (sin cambios): cénit (0,216, 0,328, 0,597), horizonte (0,597, 0,624, 0,839) y resplandor (0,831, 0,68, 0,855) en az 20° y el 2°. Luna en az −40° y el 7°, de radio 9°.
- **Precisión:** `1 − cosA` en el borde de la luna vale ~0,012. En fp32 sobra y en fp16 se rompe: por eso el material va en `MFPM_Full_MaterialExpressionOnly` (§4.1).

## 7. Interfaz del material: `M_BreathValley_SC`

**Ajustes** (sin cambios):
- Dominio Surface, **Opaque**, **Unlit**, **Two Sided**, `floatPrecisionMode = MFPM_Full_MaterialExpressionOnly`.
- Emissive ← `ValleyPS`. WPO ← `ValleyHeightVS` → `Transform` (vector, Local → World).
- Un solo master con `Part`: 0 = suelo, 1 = cielo. La MI de autoría es `MI_BreathValley_SC`.

**Nodos del grafo** (un Custom por salida, gotcha 454):

| Nodo | Shader | Entradas | Salida → destino |
|---|---|---|---|
| `LocalPosition` | VS | — | → `LP` de los dos Custom VS y → `VertexInterpolator_1` → **`LPi`** |
| Custom **`ValleyHeightVS`** (CMOT_Float3) | VS | **29** | → `Transform` (vector, Local → World) → **WPO** |
| Custom **`ValleyGradVS`** (CMOT_Float4) | VS | las mismas 29 **+ 2** (`SwellShade`, `SwellShadeFull`) = **31** | → `VertexInterpolator_0` → **`VI1`** |
| `CameraVector` → `Transform` (vector, World → Local) | PS | — | → **`CamL`** |
| `Distance(AbsoluteWorldPosition, CameraPositionWS)` | PS | — | → **`Dist`** |
| Cadenas de **preshader** para `LightDir`, `GlowDir`, `MoonDir` y `MoonCosR` | uniforme | az, el | `Cosine`/`Sine` con **`Period = 360`**. Cero costo por píxel |
| Custom **`ValleyPS`** (CMOT_Float3) | PS | **44** | → **Emissive** |

- **Interpoladores:** `VI1` (4) + `LPi` (3) = 7 escalares de 16.
- **Entradas de `ValleyHeightVS`** (29, en este orden): `LP, Part, PerfMode, HillAmp, HillScale, HillSeed, HillNear, HillFull, HillFade, HillEnd, DuneLow, DuneHigh, FarBase, FarAmp, FarScale, FarSeed, FarIn, FarFull, FarCrest, FarBack, SwellAmp, SwellNear, SwellIn, SwellFar, SwellScale, SwellSpeed, SwellSeed, MorphAmt, MorphSpeed`. El tiempo **no** es una entrada: se lee `View.GameTime` adentro.
- **Entradas de `ValleyGradVS`** (31): las 29 de `ValleyHeightVS`, en el mismo orden, y al final `SwellShade, SwellShadeFull`.
- **Entradas de `ValleyPS`** (44): `VI1, LPi, CamL, Dist, Part, PerfMode, LightDir, Wrap, ShadeFloor, SlopeDark, ColLit, ColShadow, ColSheen, Sheen, SheenW, SheenBack, CrestLight, ShadowCenter, ShadowRadius, ShadowStrength, ShadowSoft, ShadowTint, ShadowMax, SkyZenith, SkyHorizon, SkyGlow, SkyGradTop, GlowDir, GlowPow, GlowHeight, GlowAmt, MoonDir, MoonCosR, MoonEdge, MoonColor, MoonOpacity, MoonFill, MoonRim, FogStart, FogDist, FogMax, HFogDist, HFogFall, DitherAmt`.
- **Cambios de interfaz respecto de la v1** (lo que hoy está en Unreal):
  - **Salen 17:** `ValleyX`, `ValleyA`, `ValleyB`, `SeatIn`, `SeatOut`, `RimHeight`, `RimCrest`, `RimBack`, `DuneAmp`, `DuneRise`, `DuneScale`, `DuneSeed`, `DuneShiftX`, `DuneShiftY`, `MorphNear`, `MorphFar` y `SheenPow`.
  - **Entran 27:** `HillAmp`, `HillScale`, `HillSeed`, `HillNear`, `HillFull`, `HillFade`, `HillEnd`, `FarBase`, `FarAmp`, `FarScale`, `FarSeed`, `FarIn`, `FarFull`, `FarCrest`, `FarBack`, `SwellAmp`, `SwellNear`, `SwellIn`, `SwellFar`, `SwellScale`, `SwellSpeed`, `SwellSeed`, `SwellShade`, `SwellShadeFull`, `SheenW`, `HFogDist` y `HFogFall`.
  - **Cambian de default 6:** `MorphAmt` 0,45 → 0,15, `Sheen` 0,4 → 0,28, `FogStart` 1000 → 1500, `FogDist` 5000 → 45000, `FogMax` 0,6 → 0,9 y `DitherAmt` 1 → 1,5.
  - **Por qué se renombra en vez de reusar** (`HillAmp` y no `DuneAmp`, `FarBase` y no `RimHeight`, `SheenW` y no `SheenPow`): el significado o la unidad cambian (`RimCrest` estaba en unidades de la elipse; `SheenPow` era un exponente y `SheenW` es un ancho). Un override viejo en la MI o un valor empujado por el BP con el mismo nombre pisaría el valor nuevo sin avisar. Con otro nombre, el valor viejo no hace nada.
  - **Respecto de la v2 antes de la revisión** (nunca llegó a Unreal): entran `SwellIn`, `SwellShade` y `SwellShadeFull`; `SwellAmp` 560 → 1880 y `SwellFar` 12000 → 40000 (el oleaje geométrico ahora vive en la capa lejana; la pendiente angular `SwellAmp/SwellFar` = 0,047 es la misma).
- **Receta de carga por MCP** (sin cambios; gotchas 446, 447, 453 y 458): vaciar `inputs` y cargarlos ya cableados en un solo `set_properties`. `connect_to_output` de la salida principal va con `output_name: ""`. Hacer `recompile` y buscar `Failed to compile` en el log. El plan de armado sale de `scripts/plan_valley_material.py` → `Saved/ClaudeScripts/valley_build.json`.

### 7.1 Parámetros (defaults = la estética verificada)

| Grupo | Parámetro | Tipo | Default | Rango sugerido | Qué hace |
|---|---|---|---|---|---|
| `1 - Colinas` | `HillAmp` | escalar | 2200 | 0 … 4000 | Alto de las colinas medias (cm) |
| `1 - Colinas` | `HillScale` | escalar | 8 | 4 … 14 | Tamaño de las colinas medias (multiplica las longitudes de onda de las dunas: 100-240 m con 8) |
| `1 - Colinas` | `HillSeed` | escalar | 63 | 0 … 360 | Gira el campo de colinas medias (°): elige la composición |
| `1 - Colinas` | `HillNear` | escalar | 4500 | 2000 … 10000 | Distancia donde empiezan las colinas medias (cm). Tiene que ser > `SwellNear`. Más cerca agrega crestas bajo el horizonte |
| `1 - Colinas` | `HillFull` | escalar | 12000 | HillNear + 3000 … 20000 | Colinas medias plenas desde aquí (cm). Rampa ancha = pies suaves |
| `1 - Colinas` | `HillFade` | escalar | 19000 | 12000 … 30000 | Las colinas medias empiezan a apagarse (cm) |
| `1 - Colinas` | `HillEnd` | escalar | 26000 | HillFade + 3000 … FarIn | Colinas medias apagadas (cm). El código usa `max(HillEnd, HillFade + 1)`: con menos, la rampa se estira hasta ahí |
| `1 - Colinas` | `DuneLow` | escalar | −0,35 | −1 … 0,5 | Umbral de la loma: por debajo, llano. Más alto = más llanos entre lomas |
| `1 - Colinas` | `DuneHigh` | escalar | 1,2 | 0,6 … 1,6 | Umbral superior: más bajo = cimas más anchas (≤ 1 empieza a hacer mesetas) |
| `2 - Lejos` | `FarBase` | escalar | 2600 | 1000 … 5000 | Alto del anillo lejano, la garantía del horizonte (cm). Regla §3.8: `FarBase − SwellAmp·FarCrest/SwellFar ≥ 150` |
| `2 - Lejos` | `FarAmp` | escalar | 5500 | 0 … 8000 | Alto de las colinas lejanas sobre el anillo (cm) |
| `2 - Lejos` | `FarScale` | escalar | 22 | 12 … 40 | Tamaño de las colinas lejanas (275-660 m con 22). Menos de ~16 facetea la silueta |
| `2 - Lejos` | `FarSeed` | escalar | 151 | 0 … 360 | Gira el campo lejano (°) |
| `2 - Lejos` | `FarIn` | escalar | 28000 | HillEnd … 40000 | Empieza la capa lejana (cm) |
| `2 - Lejos` | `FarFull` | escalar | 40000 | FarIn + 5000 … FarCrest | Colinas lejanas plenas desde aquí (cm) |
| `2 - Lejos` | `FarCrest` | escalar | 47000 | FarFull … FarBack − 5000 | Cresta del anillo (cm) |
| `2 - Lejos` | `FarBack` | escalar | 59000 | FarCrest + 5000 … 63500 | Todo vale 0 desde aquí (cm): el borde de la malla (64000) queda oculto |
| `3 - Movimiento` | `SwellAmp` | escalar | 1880 | 0 … 1880 | Oleaje geométrico: amplitud a la distancia `SwellFar` (cm); más lejos crece con r (ángulo constante). Límite de confort: `SwellAmp·SwellSpeed/SwellFar ≤ 0,047` |
| `3 - Movimiento` | `SwellNear` | escalar | 1500 | 1400 … 4000 | A menos de esto no cambia nada, ni la geometría ni el sombreado (cm): el piso quieto |
| `3 - Movimiento` | `SwellIn` | escalar | 28000 | HillEnd … FarFull | El oleaje **geométrico** empieza aquí (cm), sobre la ladera del anillo. Más cerca vuelven los bordes de oclusión en el llano (la "línea" de la v2) y se suma a la respiración |
| `3 - Movimiento` | `SwellFar` | escalar | 40000 | SwellIn + 5000 … FarCrest | Desde aquí el oleaje geométrico tiene amplitud angular constante `SwellAmp/SwellFar` (cm) |
| `3 - Movimiento` | `SwellScale` | escalar | 2,5 | 2,5 … 3 | Tamaño de las olas (λ 100-225 m con 2,5). Menos de 2,5 facetea la silueta lejana; más, ondas más largas y **más rápidas**: `SwellScale·SwellSpeed ≤ 2,5` |
| `3 - Movimiento` | `SwellSpeed` | escalar | 1 | 0 … 1 | Velocidad del oleaje (períodos de 31-46 s con 1). **Fijar y dejar**: cambiarlo en vivo hace saltar la fase. 0,7 lo calma un 30 % |
| `3 - Movimiento` | `SwellSeed` | escalar | 0 | 0 … 360 | Gira las 4 direcciones del oleaje (°) |
| `3 - Movimiento` | `SwellShade` | escalar | 1000 | 0 … 1200 | Oleaje **solo en el sombreado** del llano y de las colinas: amplitud equivalente (cm) en la normal. Es la ondulación de la luz del llano. Más de ~1200 oscurece el llano en promedio (respuesta no lineal) |
| `3 - Movimiento` | `SwellShadeFull` | escalar | 5000 | SwellNear + 1000 … 12000 | El sombreado del oleaje entra de `SwellNear` a aquí (cm). Más lejos = el llano cercano más quieto |
| `3 - Movimiento` | `MorphAmt` | escalar | 0,15 | 0 … 0,3 | Respiración de cada colina media en su lugar (0 = sin respiración). Límite: `MorphAmt·MorphSpeed ≤ 0,3` |
| `3 - Movimiento` | `MorphSpeed` | escalar | 1 | 0 … 2 | Velocidad de la respiración (períodos de 41-83 s con 1). **Fijar y dejar**, como `SwellSpeed` |
| `4 - Luz y superficie` | `LightAz` | escalar | 20 | −180 … 180 | Azimut de la luz (°) |
| `4 - Luz y superficie` | `LightEl` | escalar | 25 | 0 … 90 | Elevación de la luz (°) |
| `4 - Luz y superficie` | `Wrap` | escalar | 0,3 | 0 … 1 | Luz envolvente: más alto = sombras más suaves |
| `4 - Luz y superficie` | `ShadeFloor` | escalar | 0 | 0 … 1 | Piso del sombreado (0 = la sombra llega a ColShadow) |
| `4 - Luz y superficie` | `SlopeDark` | escalar | 1,2 | 0 … 3 | Oscurecimiento por pendiente (da forma desde cualquier lado) |
| `4 - Luz y superficie` | `ColLit` | vector | (0,434, 0,527, 0,855) = sRGB (176, 192, 238) | — | Color iluminado (lineal) |
| `4 - Luz y superficie` | `ColShadow` | vector | (0,061, 0,117, 0,352) = sRGB (70, 96, 160) | — | Color en sombra (lineal) |
| `4 - Luz y superficie` | `ColSheen` | vector | (0,855, 0,761, 0,913) = sRGB (238, 226, 245) | — | Brillo rasante (lineal) |
| `4 - Luz y superficie` | `Sheen` | escalar | 0,28 | 0 … 1 | Intensidad del brillo rasante (se apaga con la niebla) |
| `4 - Luz y superficie` | `SheenW` | escalar | 0,3 | 0,2 … 0,4 | Ancho del lóbulo rasante en N·V (reemplaza a `SheenPow`). Menos de 0,25 vuelve a marcar los pies de las colinas |
| `4 - Luz y superficie` | `SheenBack` | escalar | 0,35 | 0 … 1 | Rasante de espaldas a la luz (1 = igual que a contraluz) |
| `4 - Luz y superficie` | `CrestLight` | escalar | 0,2 | 0 … 1 | Aclarado de las cimas hacia ColLit |
| `5 - Sombra` | `ShadowSoft` | escalar | 0,8 | 0,3 … 2 | Ancho de la penumbra por cm de altura (1 = física exacta) |
| `5 - Sombra` | `ShadowTint` | vector | (0,305, 0,352, 0,68) | — | Color por el que multiplica la sombra (lineal; azulado, no gris) |
| `5 - Sombra` | `ShadowMax` | escalar | 0,8 | 0 … 1 | Tope de la sombra |
| `5 - Sombra` | `ShadowWarm` | vector | (0,555, 0,428, 0,50) | — | 🆕 capa viva: tinte tibio hacia el que va `ShadowTint` al exhalar (con `LiveShadowWarm` 0,35 da (0,39, 0,38, 0,62)). Lineal |
| `6 - Cielo` | `SkyZenith` | vector | (0,216, 0,328, 0,597) = sRGB (128, 155, 203) | — | Cénit (lineal) |
| `6 - Cielo` | `SkyHorizon` | vector | (0,597, 0,624, 0,839) = sRGB (203, 207, 236) | — | Horizonte (lineal). También es la base del color de la niebla |
| `6 - Cielo` | `SkyGlow` | vector | (0,831, 0,68, 0,855) = sRGB (235, 215, 238) | — | Resplandor (lineal) |
| `6 - Cielo` | `SkyGradTop` | escalar | 0,7 | 0,1 … 1 | Seno de la elevación donde ya es todo cénit |
| `6 - Cielo` | `GlowAz` | escalar | 20 | −180 … 180 | Azimut del resplandor (°) |
| `6 - Cielo` | `GlowEl` | escalar | 2 | −10 … 30 | Elevación del centro del resplandor (°) |
| `6 - Cielo` | `GlowPow` | escalar | 2 | 0,5 … 8 | Ancho en azimut (más alto = más angosto) |
| `6 - Cielo` | `GlowHeight` | escalar | 0,45 | 0,05 … 1 | Alto de la banda, en seno de la elevación |
| `6 - Cielo` | `GlowAmt` | escalar | 0,8 | 0 … 1 | Intensidad del resplandor |
| `7 - Luna` | `MoonAz` | escalar | −40 | −180 … 180 | Azimut de la luna (°) |
| `7 - Luna` | `MoonEl` | escalar | 7 | −5 … 60 | Elevación del centro (°) |
| `7 - Luna` | `MoonRadius` | escalar | 9 | 1 … 20 | Radio angular (°) |
| `7 - Luna` | `MoonEdge` | escalar | 0,03 | 0,005 … 0,3 | Suavidad del borde (fracción del radio) |
| `7 - Luna` | `MoonColor` | vector | (0,73, 0,644, 0,839) = sRGB (222, 210, 236) | — | Color de la luna (lineal) |
| `7 - Luna` | `MoonOpacity` | escalar | 0,55 | 0 … 1 | Opacidad total |
| `7 - Luna` | `MoonFill` | escalar | 0,2 | 0 … 1 | Relleno del disco |
| `7 - Luna` | `MoonRim` | escalar | 1 | 0 … 2 | Borde encendido del lado del resplandor |
| `8 - Niebla` | `FogStart` | escalar | 1500 | 0 … 3000 | Distancia donde empieza la niebla (cm). A menos de esto, el píxel no la paga |
| `8 - Niebla` | `FogDist` | escalar | 45000 | 20000 … 100000 | Escala de la niebla por distancia (cm) |
| `8 - Niebla` | `FogMax` | escalar | 0,9 | 0 … 1 | Tope de la niebla |
| `8 - Niebla` | `HFogDist` | escalar | 60000 | 20000 … 200000 | Escala de la niebla de altura a z = 0 (cm). Más bajo = valles más brumosos |
| `8 - Niebla` | `HFogFall` | escalar | 1500 | 300 … 5000 | La niebla de altura cae a 1/e cada esto (cm) |
| `8 - Niebla` | `DitherAmt` | escalar | 1,5 | 0 … 3 | Dither en LSB (1 = ±0,5/255 en lineal; 1,5 ≈ ±0,5 LSB de sRGB en los tonos del piso) |
| `8 - Niebla` | `BreathTint` | vector | (1,35, 0,92, 0,853) | — | 🆕 capa viva (rev. 2): tinte **relativo** del aliento: el horizonte y la niebla van hacia `SkyHorizon × BreathTint` al exhalar. Es un cociente con la luma de `SkyHorizon` (entibia sin aclarar) y **sigue a `SkyHorizon`** aunque se cambie en las perillas del BP (`ApplyLook`) |
| `9 - Interno` | `Part` | escalar | 0 | 0 / 1 | 0 suelo, 1 cielo (lo pone el Construction Script) |
| `9 - Interno` | `PerfMode` | escalar | 0 | 0 … 3 | Banco (§8) |
| `9 - Interno` | `ShadowCenter` | vector | (380, 0, 125) | — | Centro del metaball en local (cm). Lo escribe el BP |
| `9 - Interno` | `ShadowRadius` | escalar | 85 | — | Radio efectivo (cm). Lo escribe el BP |
| `9 - Interno` | `ShadowStrength` | escalar | 1,5 | — | Intensidad efectiva. Lo escribe el BP (0 = sin sombra) |
| `9 - Interno` | `SwellTimeOfs` | escalar | 0 | — | 🆕 2026-09-30 (pedido de Beltrán: "al exhalar la ondulación más rápida"). **Lo escribe el BP** (`StepSwell`): segundos EXTRA del reloj del oleaje, de su sombreado y de la respiración de las colinas (`Tt = View.GameTime + SwellTimeOfs`). Crece solo al exhalar (`(k − 1)·dt`), así la ondulación se acelera sin saltar de fase. 0 = la v2 exacta |
| `9 - Interno` | `LiveFogDist` | escalar | 1 | — | 🆕 capa viva. **Lo escribe el BP** (`PushLive`; neutro = 1 = la v2 exacta). × `FogDist` (la bruma respira: 1,2 inhalado, 0,85 exhalado) |
| `9 - Interno` | `LiveHFogDist` | escalar | 1 | — | 🆕 capa viva. **Lo escribe el BP** (`PushLive`; neutro = 1 = la v2 exacta). × `HFogDist` |
| `9 - Interno` | `LiveHFogFall` | escalar | 1 | — | 🆕 capa viva. **Lo escribe el BP** (`PushLive`; neutro = 1 = la v2 exacta). × `HFogFall` (la bruma baja sube al exhalar: 1,35) |
| `9 - Interno` | `LiveWarm` | escalar | 0 | — | 🆕 capa viva. **Lo escribe el BP** (`PushLive`; neutro = 0 = la v2 exacta). `SkyHorizon × (1 + (BreathTint − 1) × LiveWarm)` (hasta 0,25 exhalado) |
| `9 - Interno` | `LiveGlowAmt` | escalar | 1 | — | 🆕 capa viva. **Lo escribe el BP** (`PushLive`; neutro = 1 = la v2 exacta). × `GlowAmt` (el resplandor inhala: 1,15 / 0,75) |
| `9 - Interno` | `LiveGlowPow` | escalar | 1 | — | 🆕 capa viva. **Lo escribe el BP** (`PushLive`; neutro = 1 = la v2 exacta). × `GlowPow` (más angosto al inhalar) |
| `9 - Interno` | `LiveShadowSoft` | escalar | 1 | — | 🆕 capa viva. **Lo escribe el BP** (`PushLive`; neutro = 1 = la v2 exacta). × `ShadowSoft` (0,95 inhalado / 1,05 exhalado: se abre al exhalar) |
| `9 - Interno` | `LiveShadowStrength` | escalar | 1 | — | 🆕 capa viva. **Lo escribe el BP** (`PushLive`; neutro = 1 = la v2 exacta). × `ShadowStrength` (1,12 inhalado, más densa / 0,88 exhalado) |
| `9 - Interno` | `LiveShadowWarm` | escalar | 0 | — | 🆕 capa viva. **Lo escribe el BP** (`PushLive`; neutro = 0 = la v2 exacta). `ShadowTint` → `ShadowWarm` en esta fracción (hasta 0,35 exhalado) |

**82 parámetros: 71 escalares y 11 vectores** (los 71 de la v2 + 11 de la **capa viva**, 2026-09-28 rev. 2: `ShadowWarm`, `BreathTint` y los 9 `Live*`). Los vectores de color y `ShadowCenter` se leen por el pin RGB.

> 🫁 **Capa viva (2026-09-28 rev. 2, [`PLAN-RESPIRACION-ENTORNO-2026-09-28.md`](PLAN-RESPIRACION-ENTORNO-2026-09-28.md)):** 9 entradas de `ValleyPS` (`FogDist`, `HFogDist`, `HFogFall`, `SkyHorizon`, `GlowAmt`, `GlowPow`, `ShadowSoft`, `ShadowStrength`, `ShadowTint`) ya no llegan directo del parámetro: llegan por una cadena de **preshader** (`Mul` = A × `Live*`; `Mix` = A + (B − A) × `Live*`; `Tint` = A × (1 + (B − 1) × `Live*`)), cuentas de uniformes que Unreal resuelve en la CPU. `ShadowRadius` y `GlowHeight` **no respiran** (la rev. 1 los movía: contrafase con `StepShadow` y una banda del cielo que subía y bajaba). **El código HLSL no cambia**, ninguna geometría respira (§14.3 intacta) y con los `Live*` en su neutro cada entrada vale exactamente lo de la v2 (lo verifica `Valley_check.py`). Los `Live*` los escribe `BP_BreathValley_SC.PushLive` desde `MPC_Breath`; **no se tocan en la MI**.

Restricciones que el código ya protege con `max()`:
- Cada rampa tiene un ancho ≥ 1 cm; `HE = max(HillEnd, HillFade + 1)`.
- `DuneHigh − DuneLow ≥ 0,01`, `FarCrest ≥ FarIn + 1`, `FarBack ≥ FarCrest + 1`, `SI = max(SwellIn, SwellNear)` y `SwellFar ≥ SI + 1`.
- `HillScale`, `FarScale` y `SwellScale` ≥ 0,05.
- `MoonEdge > 0` y `SheenW ≥ 0,05`.

Reglas que el código **no** protege (van en `LookTo`, §9): confort vertical y lateral, horizonte tapado y `FarBack ≤ 63500`.

### 7.2 Código de referencia (verificado: compila con `dxc` SM6, `fxc` SM5 y `glslc` → SPIR-V, y es numéricamente igual al modelo)

Es el **cuerpo** de cada Custom. En los `.hlsl` va además la cabecera de interfaz (entre las dos líneas de guiones). `Valley_check.py` verifica que el código sea idéntico línea a línea y que los defaults escritos en la cabecera coincidan con la tabla 7.1.

**`ValleyHeightVS`** (salida float3 → Transform Local→World → WPO):
```hlsl
// ValleyHeightVS - M_BreathValley_SC, VERTEX SHADER -> Transform (Local->World, vector) -> WPO.  v2 (revision 2026-09-28)
// Plan: docs/PLAN-VALLE-ENTERING-2026-09-27.md. Solo la ALTURA h (una evaluacion). Espacio LOCAL, cm.
// Tres capas radiales (colinas medias que respiran, anillo + colinas lejanas, oleaje viajero) con rampas QUINTICAS (C2).
// El oleaje mueve la GEOMETRIA solo en la capa lejana (desde SwellIn): en el llano no hay bordes de oclusion.
// Sin bucles ni arreglos (gotcha 399): las 4 dunas y las 4 olas van escritas una por una.
float pm = floor(PerfMode + 0.5);
if (Part > 0.5 || pm == 1.0 || pm == 3.0) { return float3(0.0, 0.0, 0.0); }
float Tt = View.GameTime + SwellTimeOfs;
float x = LP.x;
float y = LP.y;
float r = sqrt(x * x + y * y);
float h = 0.0;
float FC = max(FarCrest, FarIn + 1.0);
float FB = max(FarBack, FC + 1.0);
float HE = max(HillEnd, HillFade + 1.0);
float SI = max(SwellIn, SwellNear);
// ---- capa 1: colinas medias (banda polar HillNear..HE), dunas con umbral: llanos entre lomas. La amplitud de cada
// duna respira con su periodo (uniforme por cuadro); se calcula DENTRO de la rama, con la fase reducida con frac.
[branch]
if (r > HillNear && r < HE)
{
  float m0 = 1.00 * (1.0 + MorphAmt * sin(6.2831853 * frac(MorphSpeed * Tt / 53.0) + 0.0));
  float m1 = 0.75 * (1.0 + MorphAmt * sin(6.2831853 * frac(MorphSpeed * Tt / 67.0) + 2.1));
  float m2 = 0.55 * (1.0 + MorphAmt * sin(6.2831853 * frac(MorphSpeed * Tt / 41.0) + 4.4));
  float m3 = 0.35 * (1.0 + MorphAmt * sin(6.2831853 * frac(MorphSpeed * Tt / 83.0) + 1.3));
  float sH, cH;
  sincos(radians(HillSeed), sH, cH);
  float kh = 6.2831853 / max(HillScale, 0.05);
  float ax0 = kh / 3000.0 * (0.95105652 * cH - 0.30901699 * sH);
  float ay0 = kh / 3000.0 * (0.95105652 * sH + 0.30901699 * cH);
  float ax1 = kh / 2200.0 * (-0.19080900 * cH - 0.98162718 * sH);
  float ay1 = kh / 2200.0 * (-0.19080900 * sH + 0.98162718 * cH);
  float ax2 = kh / 1650.0 * (-0.79863551 * cH - 0.60181502 * sH);
  float ay2 = kh / 1650.0 * (-0.79863551 * sH + 0.60181502 * cH);
  float ax3 = kh / 1250.0 * (-0.61566148 * cH + 0.78801075 * sH);
  float ay3 = kh / 1250.0 * (-0.61566148 * sH - 0.78801075 * cH);
  float sig = (m0 * sin(ax0 * x + ay0 * y + 0.0) + m1 * sin(ax1 * x + ay1 * y + 1.7) + m2 * sin(ax2 * x + ay2 * y + 4.1) + m3 * sin(ax3 * x + ay3 * y + 2.9)) / 2.65;
  float tf = saturate((sig - DuneLow) / max(DuneHigh - DuneLow, 0.01));
  float ta = saturate((r - HillNear) / max(HillFull - HillNear, 1.0));
  float tb = saturate((r - HillFade) / (HE - HillFade));
  float ea = ta * ta * ta * (ta * (6.0 * ta - 15.0) + 10.0);
  float eb = 1.0 - tb * tb * tb * (tb * (6.0 * tb - 15.0) + 10.0);
  h += HillAmp * ea * eb * tf * tf * tf * (tf * (6.0 * tf - 15.0) + 10.0);
}
// ---- capa 2: anillo lejano (tapa el horizonte) + colinas lejanas encima (no respiran: las mueve el oleaje)
[branch]
if (r > FarIn && r < FB)
{
  float sF, cF;
  sincos(radians(FarSeed), sF, cF);
  float kf = 6.2831853 / max(FarScale, 0.05);
  float bx0 = kf / 3000.0 * (0.95105652 * cF - 0.30901699 * sF);
  float by0 = kf / 3000.0 * (0.95105652 * sF + 0.30901699 * cF);
  float bx1 = kf / 2200.0 * (-0.19080900 * cF - 0.98162718 * sF);
  float by1 = kf / 2200.0 * (-0.19080900 * sF + 0.98162718 * cF);
  float bx2 = kf / 1650.0 * (-0.79863551 * cF - 0.60181502 * sF);
  float by2 = kf / 1650.0 * (-0.79863551 * sF + 0.60181502 * cF);
  float bx3 = kf / 1250.0 * (-0.61566148 * cF + 0.78801075 * sF);
  float by3 = kf / 1250.0 * (-0.61566148 * sF - 0.78801075 * cF);
  float sgF = (1.00 * sin(bx0 * x + by0 * y + 0.0) + 0.75 * sin(bx1 * x + by1 * y + 1.7) + 0.55 * sin(bx2 * x + by2 * y + 4.1) + 0.35 * sin(bx3 * x + by3 * y + 2.9)) / 2.65;
  float tl = saturate((sgF + 0.7) / 1.9);
  float tr = saturate((r - FarIn) / (FC - FarIn));
  float te = saturate((r - FarIn) / max(FarFull - FarIn, 1.0));
  float er = tr * tr * tr * (tr * (6.0 * tr - 15.0) + 10.0);
  float ee = te * te * te * (te * (6.0 * te - 15.0) + 10.0);
  h += FarBase * er + FarAmp * ee * tl * tl * tl * (tl * (6.0 * tl - 15.0) + 10.0);
}
// ---- capa 3: oleaje viajero (4 ondas planas). GEOMETRIA solo desde SI = max(SwellIn, SwellNear), sobre el anillo
// lejano; amplitud angular constante desde SwellFar. (El sombreado del oleaje en el llano va solo en ValleyGradVS.)
[branch]
if (r > SI && r < FB)
{
  float SF = max(SwellFar, SI + 1.0);
  float tq = saturate((r - SI) / (SF - SI));
  float A = SwellAmp * tq * tq * tq * (tq * (6.0 * tq - 15.0) + 10.0) * r / SF;
  float oS, oC;
  sincos(radians(SwellSeed), oS, oC);
  float iq = 1.0 / max(SwellScale, 0.05);
  float d0x = 0.93969262 * oC - 0.34202014 * oS;
  float d0y = 0.93969262 * oS + 0.34202014 * oC;
  float d1x = -0.99619470 * oC - 0.08715574 * oS;
  float d1y = -0.99619470 * oS + 0.08715574 * oC;
  float d2x = -0.25881905 * oC + 0.96592583 * oS;
  float d2y = -0.25881905 * oS - 0.96592583 * oC;
  float d3x = -0.08715574 * oC - 0.99619470 * oS;
  float d3y = -0.08715574 * oS + 0.99619470 * oC;
  float o0 = 6.2831853 * frac((d0x * x + d0y * y) * iq / 9000.0 + 0.00 - frac(SwellSpeed * Tt / 42.0));
  float o1 = 6.2831853 * frac((d1x * x + d1y * y) * iq / 7000.0 + 0.37 - frac(SwellSpeed * Tt / 36.0));
  float o2 = 6.2831853 * frac((d2x * x + d2y * y) * iq / 5500.0 + 0.73 - frac(SwellSpeed * Tt / 31.0));
  float o3 = 6.2831853 * frac((d3x * x + d3y * y) * iq / 4000.0 + 0.18 - frac(SwellSpeed * Tt / 46.0));
  h += A * (1.00 * sin(o0) + 0.85 * sin(o1) + 0.70 * sin(o2) + 0.40 * sin(o3)) / 2.95;
}
// retiro detras de la cresta: todo vale 0 desde FarBack (el borde de la malla queda oculto)
float tk = saturate((r - FC) / (FB - FC));
h *= 1.0 - tk * tk * tk * (tk * (6.0 * tk - 15.0) + 10.0);
return float3(0.0, 0.0, h);
```

**`ValleyGradVS`** (salida float4 → VertexInterpolator_0 → `VI1`):
```hlsl
// ValleyGradVS - M_BreathValley_SC, VERTEX SHADER -> VertexInterpolator_0 -> VI1 del PS.  v2 (revision 2026-09-28)
// Devuelve (dh/dx, dh/dy, h, hf) en una pasada. hf = fraccion de loma (0..1).
// Misma cuenta que ValleyHeightVS (h identica); las derivadas de cada quintica van escritas a mano:
//   S5(t) = t^3 (t (6 t - 15) + 10),  dS5/dx = 30 t^2 (1 - t)^2 / (b - a).
// El GRADIENTE es el exacto de h MAS el termino de SOMBREADO del oleaje, Av grad(s), con Av = SwellShade * S5(SwellNear,
// SwellShadeFull, r): el llano ondula en la luz sin mover la geometria (sin bordes de oclusion). No incluye Av' s.
float pm = floor(PerfMode + 0.5);
if (Part > 0.5 || pm == 1.0 || pm == 3.0) { return float4(0.0, 0.0, 0.0, 0.0); }
float Tt = View.GameTime + SwellTimeOfs;
float x = LP.x;
float y = LP.y;
float r = sqrt(x * x + y * y);
float rs = max(r, 1.0);
float h = 0.0;
float gr = 0.0;
float gx = 0.0;
float gy = 0.0;
float hf = 0.0;
// h, gr (d/dr de las envolventes radiales: se multiplica por p/r al final), gx/gy (el resto) y hf, antes del retiro
float FC = max(FarCrest, FarIn + 1.0);
float FB = max(FarBack, FC + 1.0);
float HE = max(HillEnd, HillFade + 1.0);
// ---- capa 1: colinas medias; la respiracion (uniforme por cuadro) se calcula DENTRO de la rama, fase con frac
[branch]
if (r > HillNear && r < HE)
{
  float m0 = 1.00 * (1.0 + MorphAmt * sin(6.2831853 * frac(MorphSpeed * Tt / 53.0) + 0.0));
  float m1 = 0.75 * (1.0 + MorphAmt * sin(6.2831853 * frac(MorphSpeed * Tt / 67.0) + 2.1));
  float m2 = 0.55 * (1.0 + MorphAmt * sin(6.2831853 * frac(MorphSpeed * Tt / 41.0) + 4.4));
  float m3 = 0.35 * (1.0 + MorphAmt * sin(6.2831853 * frac(MorphSpeed * Tt / 83.0) + 1.3));
  float sH, cH;
  sincos(radians(HillSeed), sH, cH);
  float kh = 6.2831853 / max(HillScale, 0.05);
  float ax0 = kh / 3000.0 * (0.95105652 * cH - 0.30901699 * sH);
  float ay0 = kh / 3000.0 * (0.95105652 * sH + 0.30901699 * cH);
  float ax1 = kh / 2200.0 * (-0.19080900 * cH - 0.98162718 * sH);
  float ay1 = kh / 2200.0 * (-0.19080900 * sH + 0.98162718 * cH);
  float ax2 = kh / 1650.0 * (-0.79863551 * cH - 0.60181502 * sH);
  float ay2 = kh / 1650.0 * (-0.79863551 * sH + 0.60181502 * cH);
  float ax3 = kh / 1250.0 * (-0.61566148 * cH + 0.78801075 * sH);
  float ay3 = kh / 1250.0 * (-0.61566148 * sH - 0.78801075 * cH);
  float s0, c0, s1, c1, s2, c2, s3, c3;
  sincos(ax0 * x + ay0 * y + 0.0, s0, c0);
  sincos(ax1 * x + ay1 * y + 1.7, s1, c1);
  sincos(ax2 * x + ay2 * y + 4.1, s2, c2);
  sincos(ax3 * x + ay3 * y + 2.9, s3, c3);
  float sig = (m0 * s0 + m1 * s1 + m2 * s2 + m3 * s3) / 2.65;
  float gsx = (m0 * c0 * ax0 + m1 * c1 * ax1 + m2 * c2 * ax2 + m3 * c3 * ax3) / 2.65;
  float gsy = (m0 * c0 * ay0 + m1 * c1 * ay1 + m2 * c2 * ay2 + m3 * c3 * ay3) / 2.65;
  float DW = max(DuneHigh - DuneLow, 0.01);
  float tf = saturate((sig - DuneLow) / DW);
  float f = tf * tf * tf * (tf * (6.0 * tf - 15.0) + 10.0);
  float df = 30.0 * tf * tf * (1.0 - tf) * (1.0 - tf) / DW;
  float HW = max(HillFull - HillNear, 1.0);
  float ta = saturate((r - HillNear) / HW);
  float ea = ta * ta * ta * (ta * (6.0 * ta - 15.0) + 10.0);
  float dea = 30.0 * ta * ta * (1.0 - ta) * (1.0 - ta) / HW;
  float EW = HE - HillFade;
  float tb = saturate((r - HillFade) / EW);
  float eb = 1.0 - tb * tb * tb * (tb * (6.0 * tb - 15.0) + 10.0);
  float deb = -30.0 * tb * tb * (1.0 - tb) * (1.0 - tb) / EW;
  float env = ea * eb;
  h += HillAmp * env * f;
  gr += HillAmp * (dea * eb + ea * deb) * f;
  gx += HillAmp * env * df * gsx;
  gy += HillAmp * env * df * gsy;
  hf += env * f;
}
// ---- capa 2: anillo lejano + colinas lejanas (no respiran)
[branch]
if (r > FarIn && r < FB)
{
  float sF, cF;
  sincos(radians(FarSeed), sF, cF);
  float kf = 6.2831853 / max(FarScale, 0.05);
  float bx0 = kf / 3000.0 * (0.95105652 * cF - 0.30901699 * sF);
  float by0 = kf / 3000.0 * (0.95105652 * sF + 0.30901699 * cF);
  float bx1 = kf / 2200.0 * (-0.19080900 * cF - 0.98162718 * sF);
  float by1 = kf / 2200.0 * (-0.19080900 * sF + 0.98162718 * cF);
  float bx2 = kf / 1650.0 * (-0.79863551 * cF - 0.60181502 * sF);
  float by2 = kf / 1650.0 * (-0.79863551 * sF + 0.60181502 * cF);
  float bx3 = kf / 1250.0 * (-0.61566148 * cF + 0.78801075 * sF);
  float by3 = kf / 1250.0 * (-0.61566148 * sF - 0.78801075 * cF);
  float u0, v0, u1, v1, u2, v2, u3, v3;
  sincos(bx0 * x + by0 * y + 0.0, u0, v0);
  sincos(bx1 * x + by1 * y + 1.7, u1, v1);
  sincos(bx2 * x + by2 * y + 4.1, u2, v2);
  sincos(bx3 * x + by3 * y + 2.9, u3, v3);
  float sgF = (1.00 * u0 + 0.75 * u1 + 0.55 * u2 + 0.35 * u3) / 2.65;
  float gfx = (1.00 * v0 * bx0 + 0.75 * v1 * bx1 + 0.55 * v2 * bx2 + 0.35 * v3 * bx3) / 2.65;
  float gfy = (1.00 * v0 * by0 + 0.75 * v1 * by1 + 0.55 * v2 * by2 + 0.35 * v3 * by3) / 2.65;
  float tl = saturate((sgF + 0.7) / 1.9);
  float fl = tl * tl * tl * (tl * (6.0 * tl - 15.0) + 10.0);
  float dfl = 30.0 * tl * tl * (1.0 - tl) * (1.0 - tl) / 1.9;
  float RW = FC - FarIn;
  float tr = saturate((r - FarIn) / RW);
  float er = tr * tr * tr * (tr * (6.0 * tr - 15.0) + 10.0);
  float der = 30.0 * tr * tr * (1.0 - tr) * (1.0 - tr) / RW;
  float FW = max(FarFull - FarIn, 1.0);
  float te = saturate((r - FarIn) / FW);
  float ee = te * te * te * (te * (6.0 * te - 15.0) + 10.0);
  float dee = 30.0 * te * te * (1.0 - te) * (1.0 - te) / FW;
  h += FarBase * er + FarAmp * ee * fl;
  gr += FarBase * der + FarAmp * dee * fl;
  gx += FarAmp * ee * dfl * gfx;
  gy += FarAmp * ee * dfl * gfy;
  hf += ee * fl;
}
// ---- capa 3: oleaje viajero. Geometria A = SwellAmp * S5(SI, SwellFar, r) * r / SwellFar (0 exacto hasta SI);
// sombreado Av = SwellShade * S5(SwellNear, SwellShadeFull, r), que solo suma Av * grad(s) a la normal
[branch]
if (r > SwellNear && r < FB)
{
  float SI = max(SwellIn, SwellNear);
  float SF = max(SwellFar, SI + 1.0);
  float QW = SF - SI;
  float tq = saturate((r - SI) / QW);
  float eq = tq * tq * tq * (tq * (6.0 * tq - 15.0) + 10.0);
  float A = SwellAmp * eq * r / SF;
  float dA = SwellAmp * (30.0 * tq * tq * (1.0 - tq) * (1.0 - tq) / QW * r + eq) / SF;
  float tv = saturate((r - SwellNear) / max(SwellShadeFull - SwellNear, 1.0));
  float Av = SwellShade * tv * tv * tv * (tv * (6.0 * tv - 15.0) + 10.0);
  float oS, oC;
  sincos(radians(SwellSeed), oS, oC);
  float iq = 1.0 / max(SwellScale, 0.05);
  float d0x = 0.93969262 * oC - 0.34202014 * oS;
  float d0y = 0.93969262 * oS + 0.34202014 * oC;
  float d1x = -0.99619470 * oC - 0.08715574 * oS;
  float d1y = -0.99619470 * oS + 0.08715574 * oC;
  float d2x = -0.25881905 * oC + 0.96592583 * oS;
  float d2y = -0.25881905 * oS - 0.96592583 * oC;
  float d3x = -0.08715574 * oC - 0.99619470 * oS;
  float d3y = -0.08715574 * oS + 0.99619470 * oC;
  float z0, k0, z1, k1, z2, k2, z3, k3;
  sincos(6.2831853 * frac((d0x * x + d0y * y) * iq / 9000.0 + 0.00 - frac(SwellSpeed * Tt / 42.0)), z0, k0);
  sincos(6.2831853 * frac((d1x * x + d1y * y) * iq / 7000.0 + 0.37 - frac(SwellSpeed * Tt / 36.0)), z1, k1);
  sincos(6.2831853 * frac((d2x * x + d2y * y) * iq / 5500.0 + 0.73 - frac(SwellSpeed * Tt / 31.0)), z2, k2);
  sincos(6.2831853 * frac((d3x * x + d3y * y) * iq / 4000.0 + 0.18 - frac(SwellSpeed * Tt / 46.0)), z3, k3);
  float s = (1.00 * z0 + 0.85 * z1 + 0.70 * z2 + 0.40 * z3) / 2.95;
  float kq = 6.2831853 * iq / 2.95;
  float sx = kq * (1.00 * k0 * d0x / 9000.0 + 0.85 * k1 * d1x / 7000.0 + 0.70 * k2 * d2x / 5500.0 + 0.40 * k3 * d3x / 4000.0);
  float sy = kq * (1.00 * k0 * d0y / 9000.0 + 0.85 * k1 * d1y / 7000.0 + 0.70 * k2 * d2y / 5500.0 + 0.40 * k3 * d3y / 4000.0);
  h += A * s;
  gr += dA * s;
  gx += (A + Av) * sx;
  gy += (A + Av) * sy;
}
// retiro detras de la cresta: bk = 1 - S5(FC, FB, r); gradiente de bk * h (mas bk * sombreado del oleaje)
float BW = FB - FC;
float tk = saturate((r - FC) / BW);
float bk = 1.0 - tk * tk * tk * (tk * (6.0 * tk - 15.0) + 10.0);
float dbk = -30.0 * tk * tk * (1.0 - tk) * (1.0 - tk) / BW;
float gxo = bk * (gx + gr * x / rs) + dbk * h * x / rs;
float gyo = bk * (gy + gr * y / rs) + dbk * h * y / rs;
return float4(gxo, gyo, bk * h, saturate(bk * hf));
```

**`ValleyPS`** (salida float3 → Emissive):
```hlsl
// ValleyPS - M_BreathValley_SC, PIXEL SHADER -> Emissive. Unlit mate en espacio LOCAL. Part 0 suelo, 1 cielo.  v2 (revision 2026-09-28)
// VI1 = ValleyGradVS (dh/dx, dh/dy, h, hf). LPi = posicion local interpolada. CamL = CameraVector en local.
// Dist = distancia REAL a la camara. LightDir/GlowDir/MoonDir/MoonCosR llegan ya calculados (preshader).
// Sin tonemapper en el APK: lo que se escribe es lo que se ve (el hardware solo codifica sRGB).
// v2: brillo rasante con LOBULO DE TOPE PLANO exp(-(N.V/SheenW)^4) (sin ganancia en el rasante: era la linea del
//     piso) que se apaga con la niebla; niebla por distancia + niebla de ALTURA integrada a lo largo del rayo.
// Revision: el gradiente de VI1 trae ademas el SOMBREADO del oleaje (el llano ondula en la luz); ramas con [branch]
//     (no aplanar: el piso cercano no paga niebla ni cielo); la sombra falsa solo a menos de 12 anchos de penumbra.
float pm = floor(PerfMode + 0.5);
// dither estatico contra el banding (mismo hash que HeartScapePS)
float3 p3 = frac(float3(Parameters.SvPosition.xyx) * 0.1031);
p3 += dot(p3, p3.yzx + 33.33);
float dith = DitherAmt * (frac((p3.x + p3.y) * p3.z) - 0.5) / 255.0;
// banco: PerfMode 2/3 = pixeles baratos DE VERDAD, antes de cualquier cuenta (asi m0 - m2 mide el pixel entero)
if (pm >= 2.0 && Part > 0.5) { return SkyHorizon + dith; }
if (pm >= 2.0) { return ColLit + dith; }
float3 V = normalize(CamL);
float3 dv = -V;
// niebla del suelo: por distancia + de altura exponencial integrada a lo largo del rayo (densidad
// 1/FogDist + exp(-z/HFogFall)/HFogDist). z0 = camara y z1 = pixel, en local. Rama dinamica: el piso a menos
// de FogStart (la zona quieta, casi medio campo visual) no la paga.
float fog = 0.0;
[branch]
if (Part < 0.5 && Dist > FogStart)
{
  float Hf = max(HFogFall, 1.0);
  float z1 = max(VI1.z, 0.0);
  float z0 = max(VI1.z + V.z * Dist, 0.0);
  float e0 = exp(-z0 / Hf);
  float dz = z1 - z0;
  float Fh = e0;
  if (abs(dz) > 1.0)
  {
    Fh = Hf * (e0 - exp(-z1 / Hf)) / dz;
  }
  fog = FogMax * (1.0 - exp(-(Dist - FogStart) * (1.0 / max(FogDist, 1.0) + Fh / max(HFogDist, 1.0))));
}
// cielo en la direccion de la mirada: el color del cielo y el color al que tiende la niebla del suelo.
// Rama dinamica: el suelo SIN niebla no lo paga; lerp(col, sky, 0) = col exacto.
float3 sky = SkyHorizon;
[branch]
if (Part > 0.5 || fog > 0.0)
{
  sky = lerp(SkyHorizon, SkyZenith, smoothstep(0.0, max(SkyGradTop, 0.01), dv.z));
  float2 hz = dv.xy * rsqrt(max(dot(dv.xy, dv.xy), 1e-8));
  float2 gh = GlowDir.xy * rsqrt(max(dot(GlowDir.xy, GlowDir.xy), 1e-8));
  float gaz = pow(max(dot(hz, gh), 1e-6), max(GlowPow, 0.1));
  float gel = 1.0 - smoothstep(0.0, max(GlowHeight, 0.001), abs(dv.z - GlowDir.z));
  sky = lerp(sky, SkyGlow, saturate(GlowAmt * gaz * gel));
}
if (Part > 0.5)
{
  // luna: disco suave con el borde encendido del lado del resplandor
  float cosA = dot(dv, MoonDir);
  float rho = sqrt(max(1.0 - cosA, 0.0) / max(1.0 - MoonCosR, 1e-6));
  float me = max(MoonEdge, 0.001);
  if (rho < 1.0 + me)
  {
    float disc = 1.0 - smoothstep(1.0 - me, 1.0 + me, rho);
    float3 o = dv - MoonDir * cosA;
    float3 gm = GlowDir - MoonDir * dot(GlowDir, MoonDir);
    float side = 0.5 + 0.5 * dot(o, gm) * rsqrt(max(dot(o, o), 1e-10)) * rsqrt(max(dot(gm, gm), 1e-10));
    float rim = smoothstep(0.6, 1.0, rho) * side * side;
    sky = lerp(sky, MoonColor, saturate(MoonOpacity * disc * (MoonFill + MoonRim * rim)));
  }
  return sky + dith;
}
// ---- suelo ----
float3 N = normalize(float3(-VI1.x, -VI1.y, 1.0));
float wrap = saturate((dot(N, LightDir) + Wrap) / (1.0 + Wrap));
float k = lerp(ShadeFloor, 1.0, wrap) * saturate(1.0 - SlopeDark * (1.0 - N.z));
float3 col = lerp(ColShadow, ColLit, k);
col = lerp(col, ColLit, CrestLight * VI1.w * VI1.w);
// brillo rasante: lobulo de tope plano (pendiente 0 en N.V = 0); se apaga con la niebla (sin franja en el horizonte)
float xs = saturate(dot(N, V)) / max(SheenW, 0.05);
float x2 = xs * xs;
float fres = exp(-x2 * x2);
float fwd = saturate(0.5 + 0.5 * dot(dv, LightDir));
col = lerp(col, ColSheen, saturate(Sheen * fres * lerp(SheenBack, 1.0, fwd) * (1.0 - fog)));
// sombra falsa del metaball: factor de forma de una esfera de radio Rs a altura Hs sobre el suelo. Rama: solo a
// menos de 12 anchos de penumbra (q^-3/2 < 6e-4 afuera: O < 9e-4, menos de 0,1 nivel); el resto del suelo no la paga
float Hs = max(ShadowCenter.z - VI1.z, 1.0);
float ws = max(ShadowSoft * Hs, 1.0);
float2 ds = LPi.xy - ShadowCenter.xy;
float d2 = dot(ds, ds);
[branch]
if (d2 < 144.0 * ws * ws)
{
  float Rs = max(ShadowRadius, 1.0);
  float peak = ShadowStrength * Rs * Rs / (Rs * Rs + Hs * Hs);
  float qs = 1.0 + d2 / (ws * ws);
  float rq = rsqrt(qs);
  float O = min(saturate(peak * rq * rq * rq), ShadowMax);
  col *= 1.0 - O * (1.0 - ShadowTint);
}
// niebla hacia el color del cielo en esa direccion
return lerp(col, sky, fog) + dith;
```

### 7.3 Port a GLSL (three.js)

Sustituciones textuales:
- `float2/3/4` → `vec2/3/4`, `lerp` → `mix`, `frac` → `fract`, `saturate(x)` → `clamp(x, 0.0, 1.0)`, `rsqrt` → `inversesqrt`.
- `sincos(a, s, c)` → `s = sin(a); c = cos(a);`.
- `[branch]` → se borra (GLSL no tiene esa pista).
- `View.GameTime` → `uniform float uTime` (s).
- `Parameters.SvPosition.xyx` → `gl_FragCoord.xyx`.
- Los `return X;` de los Custom VS → funciones `vec3 valleyHeight(vec2 p)` y `vec4 valleyGrad(vec2 p)`. Las variables declaradas adentro de un `if` quedan en su bloque, igual que en HLSL.

Prototipo:
- **Vértice:** `vec2 p = vec2(-position.z, position.x)`; `vec3 pos = position; pos.y += valleyHeight(p).z`; `vVI1 = valleyGrad(p)`; `vLP = vec3(p, 0.0)`; `vWorldUE = vec3(-pos.z, pos.x, pos.y)`.
- **Píxel:** `camUE = vec3(-cameraPosition.z, cameraPosition.x, cameraPosition.y)`; `CamL = normalize(camUE − vWorldUE)`; `Dist = length(camUE − vWorldUE)`.
- **Cámara** en three `(0, 120, 0)` mirando hacia −Z, con near 10 y **far 200000**. Cielo: esfera de radio **100000** con `side: DoubleSide`. `mesh.frustumCulled = false`.
- **Salida:** `gl_FragColor = vec4(linearToSRGB(col), 1.0)`, con `NoToneMapping` y sin `colorspace_fragment`.

## 8. `PerfMode` (banco de medición)

Sin cambios de semántica:

| Modo | Vértices | Píxeles |
|---|---|---|
| 0 | normal | normal |
| 1 | **baratos**: WPO = 0 y `VI1` = 0 (disco plano) | normal |
| 2 | normal | **baratos**: color plano (`ColLit` el suelo, `SkyHorizon` el cielo) + dither |
| 3 | baratos | baratos |

⚠ **Lectura (revisión).** El modo 1 cambia la cobertura: el disco plano deja ver más cielo (más barato) y achica el suelo lejano (el camino más caro: del 10,4 % al 4,1 % de los píxeles, medido con el rasterizador). En Heart pasó lo mismo: su banco dio m1 − m3 = 0,3 ms y m0 − m2 = 1,9 ms. Por eso:
- **Costo de píxeles = m0 − m2** (la geometría real en los dos; solo cambia el PS).
- **Costo de vértices = m2 − m3** (en los dos, los píxeles son planos).
- m1 − m3 queda solo como cota inferior de los píxeles.

Hay que medir ida y vuelta, en dos pasadas, y leer el `App=` de VrApi normalizado por MHz si el reloj cambia.

## 9. `BP_BreathValley_SC`

El BP ya existe (tracker `blueprints/BP_BreathValley_SC.md`). **La v2 no cambia sus grafos**: la sombra, el banco y el Construction Script siguen igual. Cambian estas cosas:

1. **`Sky`: escala 400 → 2000** (radio de 1000 m). Es obligatorio (§6).
2. **`Sky`: `Treat as Background for Occlusion` = true** (`bTreatAsBackgroundForOcclusion`). Así se dibuja después del suelo (§6). Si se quiere confirmar en el banco: `PerfMode` 2 aplicado **solo** al MID del `Sky`; con la corrección, m0 tiene que cambiar ~0,1 ms o menos.
3. **Revertir el adelanto temporal** que quedó puesto (tracker, "ADELANTO TEMPORAL"):
   - Escala del actor `Entering_Valle` 4 → **1**: el shader asume cm locales.
   - `ShadowRadius` del CDO 21,25 → **85**.
   - Los defaults del material (`MorphSpeed` 4, `MorphAmt` 0,9, `FogMax` 0,85) quedan pisados por el rearmado desde `valley_build.json`. Hay que verificar que la MI no tenga overrides de esos nombres.
   - 🔴 **La Z del actor (−90,4)** la puso Beltrán en el editor: **se pregunta antes de tocarla**. La v2 la tolera: la zona quieta, la sombra (que se calcula en local), la niebla (que usa la altura real de la cámara en local) y el margen del horizonte (≥ 1,88°) siguen valiendo. El metaball queda 90 cm más alto sobre el piso, así que su sombra se ve más débil y más ancha; y aparecen algo más de crestas bajo el horizonte (§3.8).
4. **Perillas en el BP (opcional, pendiente desde la v1).** Hoy el look vive en la MI. Si Beltrán las quiere en el actor, esta es la propuesta para la v2 (`LookTo` las copia a los parámetros):

| Categoría | Perilla (default) → parámetro |
|---|---|
| `1 - Colinas` | `HillHeight` (2200) → `HillAmp` · `HillSize` (8) → `HillScale` · `HillSeed` (63) → `HillSeed` · `HillNear` (4500) → `HillNear` |
| `2 - Lejos` | `FarHeight` (5500) → `FarAmp` · `HorizonHeight` (2600) → `FarBase` · `FarSeed` (151) → `FarSeed` |
| `3 - Movimiento` | `SwellAmount` (1880) → `SwellAmp` · `SwellSize` (2,5) → `SwellScale` · `SwellSpeed` (1) → `SwellSpeed` · `SwellLight` (1000) → `SwellShade` · `MorphAmount` (0,15) → `MorphAmt` |
| `4 - Luz y color` | `LightAzimuth` (20) · `LightElevation` (25) · `Sheen` (0,28) · `SlopeShade` (1,2) → `SlopeDark` |
| `7 - Niebla` | `FogStart` (1500) · `FogDistance` (45000) → `FogDist` · `FogMax` (0,9) · `HeightFogDistance` (60000) → `HFogDist` |

- **Reglas que `LookTo` tiene que imponer** (en lugar de la de la elipse de la v1):
  - `FarBack_ef = min(FarBack, 63500)`.
  - `SwellAmp_ef = min(SwellAmp, 0,047·SwellFar/SwellSpeed)`: confort vertical del oleaje.
  - `MorphAmt_ef = min(MorphAmt, 0,3/MorphSpeed)`: confort vertical de la respiración.
  - `SwellScale_ef = min(SwellScale, 2,5/SwellSpeed)` (y ≥ 2,5 si se puede: menos facetea la silueta): confort **lateral**. Si `SwellSpeed` > 1, preferir bajar `SwellSpeed`.
  - `SwellIn_ef = max(SwellIn, HillEnd)`: el oleaje geométrico no entra en el llano ni se suma a la respiración.
  - `FarBase_ef = max(FarBase, SwellAmp_ef·FarCrest/SwellFar + 150)`, para que el horizonte quede tapado.
- **`SwellSpeed` y `MorphSpeed` se fijan, no se animan** (la fase salta). Si la capa viva los anima, la fase se integra en el BP.
- ⚠ Las perillas **instance-editable nacen en cero** en la instancia colocada (gotchas 146, 420 y 435): hay que escribir los defaults en el CDO **y** en la instancia.

## 10. Costo estimado (honesto: se mide)

| Pieza | Cuenta | Estimado |
|---|---|---|
| Vértices | 21.601 vértices × 2 vistas × (`Height` + `Grad`), más el binning, que vuelve a ejecutar `Height`. **Revisión:** `ValleyHeightVS` evalúa el oleaje solo en la capa lejana (19 % de los vértices, antes 80 %) y las colinas lejanas ya no respiran. Trascendentes por vértice y vista (`sin`/`cos` = 1, `sincos` = 2), con las ramas: `Height` 6,4 y `Grad` 15,7, **28,6 en total** (2 × `Height` + `Grad`), contra 38,2 de la v2 antes de la revisión (−25 %). Escalado desde la medición de Heart v2 (79k vértices y ~5× más trabajo = 5,4 ms) | **0,25-0,55 ms** |
| Píxeles, suelo | El piso a menos de 15 m (≈ media vista) no paga ni la niebla ni el cielo, y la sombra falsa solo se calcula cerca del metaball (−7-9 % del PS del suelo). El suelo lejano (~10 % del *eye buffer*) suma 2 `exp` y 1 división por la niebla de altura. La franja del horizonte se sombrea a 1,6-1,7 lanes por píxel (cuadrantes 2×2 sobre triángulos rasantes, MSAA 4x): +0,15-0,22 ms ya incluidos. Las ramas llevan `[branch]`: el driver no las aplana (si las aplanara, el piso cercano pagaría ~100 op-eq más por píxel, +0,35-0,5 ms) | 0,75-1,4 ms |
| Píxeles, cielo | Sin cambios | 0,2-0,5 ms |
| Sobredibujo | Con `Sky` como fondo, el cielo se dibuja después del suelo. Sin eso: +0,3-0,5 ms | ~0 |
| **Total** | Contra ~2,5 ms de presupuesto (la etapa sin fondo mide 9,43 ms a 456 MHz, de 13,9) | **~1,2-2,5 ms** (sin el `Sky` como fondo, hasta ~3 ms) |

**Palancas si no entra** (de más a menos efecto):
1. Verificar el orden del cielo (§9, paso 2) antes que nada.
2. Malla de 128 sectores con aspecto 0,6: 17.409 vértices (−20 % de VS), pero la silueta queda en p99 5,6 px.
3. Sacar la respiración del código (no alcanza con `MorphAmt` 0: el `sin` se calcula igual). Ahorra 4 `sin` por vértice de colinas medias.
4. Pasar al preshader lo uniforme que no depende del tiempo: los `sincos` de las semillas y las rotaciones de las direcciones (más nodos en el material).
5. `DitherAmt` 0 (ahorra poco).

## 11. Riesgos

| Riesgo | Detalle | Mitigación |
|---|---|---|
| **Comodidad / vection** | El terreno lejano se traslada (oleaje) y la luz del llano viaja alrededor de un usuario quieto | Nada cambia a menos de 15 m; la geometría está quieta hasta 45 m y el oleaje geométrico empieza a 280 m. Deriva neta 0,5 %, sin giro. Velocidad vertical ≤ **0,451°/s** (cota rigurosa) y frecuencia por punto ≤ 0,032 Hz. **Velocidad lateral de los rasgos** (no la de fase): picos del oleaje lejano p90 1,4-1,6°/s, máximo ~3,7°/s (3-8 % > 2,5°/s, raros y de bajo contraste); en la imagen, flujo normal p99 0,67°/s y vector 2D p90 1,9°/s, máximo 5,2°/s (el sombreado del llano, de 1,4-2,9 niveles de contraste). El tope de 2,5°/s del diagnóstico de movimiento es heurístico, no un umbral de la literatura: la vection necesita flujo amplio y coherente (Brandt et al. 1973), y aquí el flujo es angosto e incoherente. **Se juzga en el visor**, mirando a propósito la franja de 100-300 m junto al horizonte y hacia yaw ~45° y ~180°. Si molesta: `SwellSpeed` 0,7 (−30 % en todo) o `SwellShade` más bajo |
| **El llano ondula solo en la luz** | La normal del llano sugiere olas de ~10 m que la geometría no tiene: sin oclusión ni paralaje | A 15-280 m la disparidad y el paralaje no resuelven esas alturas; la sombra de relieve es la señal dominante. Juzgarlo en el visor. Si se lee "pintado", bajar `SwellShade` |
| **No se ve moverse en el editor** | El viewport sin *Realtime* no redibuja, y las capturas del MCP son de un solo cuadro | Juzgar con Realtime (Ctrl+R), en PIE o en Simulate. **Control positivo** (solo en el viewport del editor, **nunca con el visor puesto**): `SwellSpeed` 5 durante 20 s y después volver a 1. Si con eso no se mueve nada, el reloj no corre |
| **Crestas de colinas bajo el horizonte** | Quedan bordes de oclusión en las crestas de las colinas medias (70-210 m, 10-14 % de los azimuts): curvos, siguen la forma de la loma | Es una colina delante de un llano más lejano. Si en el visor se leen como "línea": `HillNear` más lejos o `DuneLow` más alto (menos lomas bajas) |
| **Facetas de la silueta** | Con la malla de la v1 o con más sectores, el oleaje lejano se ve poligonal y las facetas "caminan" | Malla de 144 sectores con aspecto 0,6 (§2): p99 de 3,3 px y temblor ≤ 1 px/s. Si se baja `SwellScale` o `FarScale`, vuelve: medirlo con `preview_breath_valley.py` (línea `PREVIEW malla`) |
| **Culling** | Malla plana con WPO de −4 a +100 m (defaults) | `PositiveBoundsExtension (0, 0, 19000)` y `NegativeBoundsExtension (0, 0, 4000)` en el asset, que cubren los rangos sugeridos; en three.js, `frustumCulled = false` |
| **El cielo tapa el terreno o se dibuja primero** | La esfera de 200 m quedaría adentro de la malla de 640 m; la de 1000 m, sin marcar como fondo, se dibuja antes que el suelo | `Sky` con **escala 2000** y **Treat as Background for Occlusion** (§6, §9) |
| **Precisión** | Distancias de hasta 1000 m (el cielo) | El VS es siempre fp32. El PS va en `MFPM_Full_MaterialExpressionOnly`: no se puede volver a Default (en half, `Dist` del cielo sería inf y la luna se rompe; §4.1). Las fases se reducen con `frac` antes de cada `sin` (espacio y tiempo). El reloj `View.GameTime` crece desde que se carga el nivel: solo con ~18 h de mundo cargado en el editor (ULP de 7,8 ms) las crestas de 60-125 m temblarían ±0,5 px; si el editor queda abierto días, recargar el nivel. El APK no llega a eso |
| **Contraste del metaball** | Detrás de su mitad inferior está la bruma del horizonte (luma p50 ~182) y no lomas oscuras: los tonos medios del metaball real (165-172) quedan a ~10-15 niveles del fondo; lo separan los brillos y las sombras moradas | Verificarlo en el visor con el metaball real. Si se pierde la figura: `FogMax` 0,8, `SkyHorizon` apenas más oscuro, `ColLit` un poco más oscuro en el llano lejano, o `GlowAz` 30-40°. No hace falta tocar la geometría |
| **Banding** | Degradados grandes (cielo, niebla, piso bajo el horizonte) en 8 bits | Dither estático con `DitherAmt` **1,5**; mirar el piso de 2 a 10° bajo el horizonte. Nada baja de 13/255 |
| **Gotas contra el piso** | Al exhalar, la gota más baja queda a ~45 cm del piso (medido en el editor; tracker) | El piso bajo el metaball sigue en z = 0 exacto (r < 45 m). Si el actor queda en Z −90,4, hay 90 cm más de margen |
| **Adreno** | Índice dinámico en el VS, reloj en half, ramas aplanadas | Sin arreglos ni bucles (4 dunas y 4 olas escritas una por una), `View.GameTime` adentro del Custom, `MFPM_Full` (gotchas 399, 382 y 185) y `[branch]` en todas las ramas por radio y de la niebla, el cielo y la sombra |
| **Costo** | Estimado de 1,2 a 2,5 ms contra 2,5 ms | Se mide con `PerfValley0..3`, ida y vuelta, dos pasadas; píxeles = m0 − m2 (§8). Palancas en la §10 |

## 12. Valores de control (con TODOS los defaults de la §7.1)

Cada implementación tiene que reproducir estos números: ±0,002 cm en alturas, ±2·10⁻⁶ en gradiente y `hf`, y ±0,001 en color lineal, sin dither. Salen de `scripts/valley_model.py`. El HLSL traducido da lo mismo; la diferencia máxima es 6·10⁻⁴ cm, por las constantes de dirección de 8 cifras. Van con punto decimal para copiarlos directo a un test. El gradiente incluye el sombreado del oleaje (§3.6).

**Altura y gradiente** (`ValleyGradVS`; `ValleyHeightVS` devuelve la misma h):

| (x, y) cm | t (s) | h (cm) | dh/dx | dh/dy | hf | qué prueba |
|---|---|---|---|---|---|---|
| (0, 0) | 0 | 0.000 | 0.000000 | 0.000000 | 0.000000 | usuario |
| (380, 0) | 0 | 0.000 | 0.000000 | 0.000000 | 0.000000 | metaball |
| (1300, -700) | 30 | 0.000 | 0.000000 | 0.000000 | 0.000000 | borde de la zona quieta (14,8 m) |
| (3000, 1200) | 0 | 0.000 | 0.025176 | 0.048426 | 0.000000 | sombreado del oleaje sin geometría (32 m) |
| (6000, -2500) | 20 | 4.966 | 0.089937 | -0.151754 | 0.002257 | pie de las colinas + sombreado (65 m) |
| (-9000, 6000) | 45.5 | 374.301 | -0.345389 | 0.087435 | 0.170137 | colinas medias + sombreado (108 m) |
| (15000, 5000) | 90 | 497.366 | 0.099869 | -0.040502 | 0.226075 | colinas medias + sombreado (158 m) |
| (21000, -12000) | 120 | 0.000 | 0.033414 | 0.085065 | 0.000000 | llano a 242 m: sin oleaje geométrico |
| (26400, 23800) | 120 | -124.940 | 0.030688 | 0.014694 | 0.007105 | valle del oleaje sobre el anillo, h < 0 (355 m) |
| (-30000, -20000) | 300 | 2001.182 | -0.201757 | -0.451845 | 0.177124 | anillo + colinas lejanas + oleaje (361 m) |
| (46000, 9000) | 600 | 3524.110 | -0.008876 | -0.579483 | 0.324981 | cresta (469 m) |
| (0, 56000) | 30 | 786.380 | -0.004620 | -0.654901 | 0.100584 | retiro (560 m) |
| (60000, 10000) | 0 | 0.000 | 0.000000 | 0.000000 | 0.000000 | detrás del retiro (608 m) |

**Color del suelo** (`ValleyPS`, `Part` 0, cámara en (0, 0, 120), sombra en (380, 0, 125) con los defaults, `DitherAmt` 0):

| punto (x, y) | t | color lineal | sRGB 8 bits | O (sombra) | niebla |
|---|---|---|---|---|---|
| (380, 0) | 0 | (0.2157, 0.2651, 0.5575) | (128, 141, 197) | 0.4743 | 0 |
| (250, -150) | 0 | (0.2698, 0.3420, 0.6275) | (142, 158, 208) | 0.0432 | 0 |
| (3000, 1200) | 0 | (0.4296, 0.4542, 0.7010) | (175, 180, 218) | 0 (sin calcular) | 0.0577 |
| (-9000, 6000) | 45.5 | (0.4044, 0.4663, 0.7386) | (170, 182, 223) | 0 (sin calcular) | 0.2588 |
| (15000, 5000) | 90 | (0.5085, 0.4959, 0.7275) | (189, 187, 222) | 0 (sin calcular) | 0.3611 |
| (46000, 9000) | 600 | (0.6155, 0.5655, 0.7810) | (206, 198, 229) | 0 (sin calcular) | 0.6517 |

**Color del cielo** (`ValleyPS`, `Part` 1, dirección de mirada `D(az, el)`, `DitherAmt` 0; sin cambios respecto de la v1):

| az (°) | el (°) | color lineal | sRGB 8 bits |
|---|---|---|---|
| 0 | 0 | (0.7595, 0.6629, 0.8501) | (226, 213, 237) |
| 0 | 45 | (0.2160, 0.3280, 0.5970) | (128, 155, 203) |
| 20 | 3 | (0.7821, 0.6676, 0.8510) | (229, 213, 238) |
| 180 | 10 | (0.5383, 0.5784, 0.8017) | (194, 200, 231) |
| -40 | 7 | (0.6269, 0.6178, 0.8274) | (207, 206, 235) · centro de la luna |
| -33 | 12 | (0.6578, 0.6158, 0.8209) | (212, 206, 234) · borde derecho de la luna |
| 0 | 90 | (0.2160, 0.3280, 0.5970) | (128, 155, 203) |

**Malla:** 150 anillos · 21.601 vértices · 43.056 triángulos · radios 60, 120 … 1080, 1127,12 … 57426,2, 59000, 60250, 61500, 62750, 64000 cm.

**Direcciones derivadas** (§7): `LightDir` = (0,851651, 0,309976, 0,422618) · `GlowDir` = (0,939120, 0,341812, 0,034899) · `MoonDir` = (0,760334, −0,637996, 0,121869) · `MoonCosR` = 0,987688.

**Confort:** `cota_vel_vertical_deg` = 0,451°/s en r = 400 m (oleaje 0,451; respiración 0,232). `deriva_neta` = 0,5 %.

## 13. Orden de construcción (aplicar la v2)

Cada paso termina con una verificación concreta. Antes de empezar: contar los actores del nivel y guardar con rutas explícitas (reglas de la etapa).

1. **Sin Unreal (hecho):**
   - `python scripts/hlsl/Valley_check.py` → `RESULTADO: TODO OK`.
   - `python scripts/plan_valley_material.py` → `valley_build.json` (71 parámetros).
   - `gen_breath_valley.py` en Blender headless → `LISTO … verts=21601` y la línea `BOUNDS`.
2. **Malla:**
   - Reimportar `SM_BreathValley_SC` **sobre el mismo asset** desde `Saved/ClaudeScripts/SM_BreathValley_SC.fbx`.
   - `get_bounds` ±64000 y 21.601 vértices.
   - `PositiveBoundsExtension (0, 0, 19000)` y `NegativeBoundsExtension (0, 0, 4000)`.
3. **Material:**
   - Rearmar los tres Custom desde `valley_build.json`: código + entradas ya cableadas (29, 31 y 44).
   - Crear los 27 parámetros nuevos (respecto de la v1) y **borrar los 17 nodos de parámetro que quedan huérfanos** (§7).
   - Revisar la MI: sin overrides de los nombres que salieron, ni de `MorphAmt`, `MorphSpeed`, `Sheen`, `FogStart`, `FogDist`, `FogMax` o `DitherAmt` con valores viejos.
   - `recompile`: nada de `Failed to compile` en el log (PC y ES31).
   - `CaptureAssetImage` (gotcha 452).
   - Control positivo: `PerfMode` 1 contra 0.
4. **BP:**
   - `Sky` con escala 2000 y `Treat as Background for Occlusion`.
   - Revertir el adelanto temporal: escala del actor 1 y `ShadowRadius` 85 (§9).
   - **Preguntarle a Beltrán por la Z −90,4** antes de tocarla.
5. **En el nivel:**
   - Con **Realtime** encendido, mirar desde (0, 0, 120): las crestas lejanas tienen que cambiar de forma en ~5 s (comparar con `preview_valle_dif_v2.png`) y la luz del llano, junto al horizonte, tiene que viajar.
   - Control positivo del reloj: `SwellSpeed` 5 durante 20 s y volver a 1, **solo en el viewport del editor, nunca con el visor puesto** (el salto de fase al volver es un golpe visual).
   - PIE: `VALLE: sombra sigue a Entering_Blob`.
   - Capturas equivalentes a las de las previews (`preview_valle_t0_v2.png`, `preview_valle_lado_v2.png`).
6. **APK + banco** (`PerfValley0..3`, ida y vuelta, dos pasadas; píxeles = m0 − m2, vértices = m2 − m3) + **juicio de Beltrán en el visor** (comodidad del oleaje, escala, línea, crestas bajo el horizonte, contraste del metaball, banding del piso).

**No se toca:** `/Game/Test_Heart`, `Mechanics/Heart/Scape/*`, `scripts/hlsl/Heart*.hlsl`, `gen_heart_membrane.py`, `BP_BreathBlob_SC`, `Core/` ni `Config/`.

## 14. Decisiones abiertas (de Beltrán)

1. **El piso:** z = 0 exacto o bajar el actor (hoy está en Z −90,4, puesto por él). La v2 funciona en los dos casos.
2. **Cuánto se mueve:** `SwellShade` es la luz que viaja por el llano, `SwellAmp` el movimiento de las siluetas lejanas y `MorphAmt` la respiración de las colinas medias. `SwellSpeed` 0,7 calma todo el oleaje.
3. **Capa viva:** que la sombra respire con el metaball y que el valle siga la respiración del usuario. 🔴 **Cota (revisión):** la regla de 0,5°/s se derivó para períodos de 31-83 s. Modular la **geometría** a la frecuencia de la respiración (0,1-0,25 Hz) la rompe y hace coherente el sube y baja de la silueta, justo en la banda de más mareo (0,2-0,4 Hz, Diels y Howarth 2013). Medido por el verificador de confort con `SwellAmp·(1 + prof·sin 2πft)`: sin modular 0,48°/s; 0,1 Hz y prof 0,5 → 0,94°/s (0,32 coherente); 0,2 Hz y prof 0,5 → 1,71°/s; 0,25 Hz y prof 1 → 4,13°/s. Por eso:
   - La capa viva modula **`SwellShade`** (la luz del llano), la niebla o el color: nada de eso mueve la geometría.
   - Si se liga la geometría (`SwellAmp`, `MorphAmt`), que sea con un filtro lento (τ ≥ 20-30 s) o con profundidad ≤ 0,2 a 0,1 Hz, y **medido** con la misma herramienta (`vm.cota_vel_vertical_deg` y el script de capa viva del verificador de confort) antes de ponerlo en el visor.
   - Si se anima `SwellSpeed` o `MorphSpeed`, la fase se integra en el BP.
4. **Dónde va el resplandor:** detrás del metaball, como en la referencia, o corrido para ganar contraste.
5. **Qué pasa con `Entering_Fondo`** (la esfera lisa): sigue oculta, de respaldo.

## Fuentes

- **Leídos:**
  - `scripts/hlsl/HeartHeightVS.hlsl`, `HeartGradVS.hlsl`, `HeartScapePS.hlsl` y `scripts/gen_heart_membrane.py`.
  - `blueprints/BP_BreathValley_SC.md` y `BP_BreathBlob_SC.md`.
  - Gotchas 134, 146, 185, 382, 399, 402, 420, 435, 446-467.
- **Diagnósticos de la v2** (con sus fuentes de percepción citadas: Cutting y Vishton 1995; Ooi, Wu y He 2001; Sinai, Ooi y He 1998; O'Shea, Blackburn y Ono 1994; Diels y Howarth 2013; Brandt, Dichgans y Koenig 1973; Prothero et al. 1999; Quilez, niebla de altura): `VR_Test/Saved/ClaudeScripts/valle_v2_diag_movimiento/`, `valle_v2_diag_linea/` y `valle_v2_diag_escala/`.
- **Revisión de la v2** (2026-09-28): `VR_Test/Saved/ClaudeScripts/valle_v2_verif_correccion/`, `valle_v2_verif_confort/`, `valle_v2_verif_visual/` y `valle_v2_verif_costo/`; las mediciones de la corrección, en `valle_v2_revision/`.
- **Herramientas de verificación:**
  - `dxc` y `fxc` del Windows SDK 10.0.26100.
  - `glslc`, `spirv-val` y `spirv-dis` del Android NDK 27.
  - El modelo numpy `scripts/valley_model.py`.
  - Blender 5.2 headless para la malla y las previews.
