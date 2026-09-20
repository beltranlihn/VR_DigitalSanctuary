# BP_MetaBlob_SC + M_MetaBlob_SC — los metaballs (Core/Light/)

> Creado 2026-09-07 (estacion 7 de la galeria, reemplaza los 3 orbes de Nico). Veredicto de Beltran: **"Super. Se ve bien"**.
> Tracker escrito el **2026-09-15** al medirlo en visor por primera vez.
> **Estado: 🟢 aprobado de aspecto · 🔴 es el efecto mas caro de la galeria.**

## Que es
Raymarch de un SDF de esferas con smooth-min, en un `MaterialExpressionCustom`. **Unlit, translucido, one-sided**,
sobre un proxy que es el **cubo de engine** (`/Engine/BasicShapes/Cube`) en el componente `Volume`
(`RelativeScale3D` 1,1,1 · `BoundsScale` 1 · ⚠ `CastShadow = true`, que en un raymarch translucido no sirve de nada).

El march arranca en la **camara** (`RayOrigin` = `CameraPositionWS` transformado a espacio local), no en la
superficie del proxy: **el proxy solo funciona como mascara de pixeles**, no acota el recorrido del rayo.

## 🔬 Medido en visor (Quest 3, 2026-09-15)
Estacion 7 = `BP_MetaBlob_SC` + `BP_Ganzfeld_SC_C_1`, **App = 30,3–38,9 ms** contra un presupuesto de 13,9 ms,
FPS 28–30, `GPU% = 0,97`. Restandole el cascaron (medido solo en la estacion 3: 24–27 ms),
**el metaball aporta ~6–12 ms**. Es el segundo efecto mas caro, no el primero.

## 🔴 Los valores REALES de la instancia (no los del CDO) y lo que implican
| | instancia `BP_MetaBlob_SC_C_0` | CDO |
|---|---|---|
| `Spread` | 19,46 | 26 |
| `BlobRadius` | 13,58 | 13 |
| `SizeVariation` | 0,45 | 0,45 |
| `CurlAmount` | 19,37 | 7 |
| `BlobCount` | 6,03 → el shader usa **6** | 7 |
| `Steps` | 86,68 → el shader usa **64** | 28 |

🔴 **`Steps` esta CLAMPEADO a 64 en el shader** (`clamp(ParB.z, 4.0, 64.0)`): todo lo que Beltran ponga por
encima de 64 **no hace nada**. La perilla miente en ese rango.

**Costo por pixel:** el march es `Steps x BlobCount` = **64 x 6 = 384** evaluaciones en el peor caso, mas
`4 x BlobCount = 24` de la normal por diferencias finitas. El march domina por completo.

## ❌ Dos optimizaciones propuestas que NO sobrevivieron a los numeros (2026-09-15)
### 1. Cambiar el proxy de cubo a esfera — **esta AL REVES**
Extension de la nube en unidades locales: `P[j] = C[j]*Spread*(1-Attract) + curl*CurlAmount`, con `|C[j]| <= 1`
y `|curl| <= sqrt(3)*CurlAmount = 33,5` (tipico ~23,7), mas `rmax = BlobRadius*(1+SizeVariation) = 19,69`.
→ **extension tipica ~53, peor caso ~73** unidades locales.
- El **cubo de engine** a escala 1 llega a **50** en las caras (86,6 en las diagonales).
- La **esfera de engine** a escala 1 llega a **50 en todas las direcciones** → recortaria MAS que el cubo.
- Una esfera que si contenga la nube necesita radio ~73, o sea escala 1,46 — pero **escalar el componente
  escala el espacio local y por lo tanto el SDF entero** (el blob se veria 1,46x mas grande), asi que habria
  que compensar dentro del shader.
- Y aun compensando: esa esfera proyecta `pi*73^2 ~ 16.700` contra los ~10.000 del cubo de frente.
  **La esfera que entra cubre ~1,7x MAS pantalla que el cubo.** La idea es contraproducente.

🚩 **Corolario que SI importa:** con extension tipica ~53 contra 50 de media-arista, **el cubo probablemente
ya esta recortando los blobs** cuando el curl los lleva lejos. Es un defecto de aspecto, no de rendimiento.
**Falta que Beltran lo mire.**

### 2. Normal analitica en vez de las 4 muestras — **marginal**
Se estimo "un tercio del costo" suponiendo `BlobCount = 16`. Con el valor real (**6**) la normal cuesta
`4 x 6 = 24` evaluaciones contra las hasta `384` del march: **~6%**. No justifica tocar el shader.

## ✅ La palanca que si queda, y es decision de aspecto
**`Steps`.** El march ya hace sphere tracing de verdad (`t += max(res, eps)`) y corta por impacto
(`res < eps`) y por distancia (`t > maxT`, con `maxT = Spread*4 + rmax*6 = 196`). Los rayos que queman los 64
pasos son los **rasantes de la silueta**. Bajarlo erosiona un poco el borde. **No tocar sin que Beltran lo juzgue.**

Otras, menores: **`CastShadow = false`** en el componente `Volume` (gratis), y los arrays locales `P[16]`/`R[16]`
con indexado dinamico, que en Adreno presionan registros aunque `BlobCount` sea 6.


## 🌬️ 2026-09-17 — la respiración REEMPLAZA el reloj de la atracción ([[BP_BreathManager_SC]])
Pedido de Beltrán: *"Metaball, puede ser el spread o curl"*.

🔑 **El hallazgo del cableado que decidió todo:** `Attract = lerp(AttractMin, AttractMax, sin(Time·AttractSpeed))` → `P = C·Spread·(1−Attract)`. **El metaball ya respiraba solo, por reloj**: se funde y se separa. La respiración no suma otra animación: **toma ese ciclo**.

- **Material `M_MetaBlob_SC`**: `Custom` **`BreathAttract`** (`Sin`=`Sine_0`, `S`=`Signed`, `On`=`On` del MPC, `G`=`BreathAttract`) → `LinearInterpolate_0.Alpha`: `lerp(Sin, −S, saturate(On·G))`.
  - Inhala (S = +1) → alpha −1 → **máxima separación** del rango que ya recorría el reloj · exhala → `AttractMax` → **se funde en una masa** · reposo (S = 0) → `AttractMin` → el spread autorado.
  - **Sin umbral (`On` = 0) sigue el reloj de siempre**; al entrar al umbral pasa al usuario con un fundido de ~1 s.
- **BP**: perilla `BreathAttract` (0..1, cat. *R - Respiracion*) + `ApplyBreath` (a `Volume`) al final del Construction Script. Instancia `GAL_7_MetaBlob`: **1**. Verificado en el MID.
- 💡 No agrega extensión ni costo al raymarch: el rango es el mismo que ya recorría el reloj.


### 🌬️ 2026-09-17 (2ª pasada) — curva SUAVE y rango exagerado
Beltrán tras probar: *"llegó muy duro a los valores máximos y mínimos, no suave como con la esfera"* y *"un poco más exagerados"*.
- **Causa (en el manager, no acá):** `BreathSigned` era `clamp(gain·y)` → con ganancia 1,5 una respiración normal chocaba contra ±1 y quedaba plana. Ahora es `k·y/(1+(k−1)|y|)` (techo suave, `SignedGain` 2).
- **Mapeo nuevo del consumidor** (sin quiebre en 0 aunque las ganancias sean asimétricas): `m = 1 + S·lerp(−Out, In, smoothstep((S+1)/2))`. `In` = fracción a inhalación plena, `Out` = a exhalación plena, igual que antes.
- **Pedido: "el spread y el curl muy bajos en la exhalación"**. Con la versión 1 al exhalar el attract llegaba a `AttractMax`, pero el **curl (19,4, tan grande como el spread) seguía separando las gotas**: nunca se fundían.
- `Custom` **`BreathAttractSpread`** (reemplaza a `BreathAttract` y al `LinearInterpolate_0` del reloj, borrados): `lerp(lerp(AttractMin, AttractMax, sin), 1 − mSpread, saturate(On·BreathAttract))` → `AppendVector_0.B`. Con umbral, la respiración maneja el spread directo: `mSpread = 1 + S·lerp(−SpreadOut, SpreadIn, smoothstep)`.
- `Custom` **`BreathCurl`** = `CurlAmount·lerp(1, mCurl, saturate(On·BreathAttract))` → `AppendVector_3.A`.
- Perillas nuevas **`BreathSpreadIn/Out`** · **`BreathCurlIn/Out`**; `BreathAttract` queda como "cuánto toma el control la respiración" (0..1).
- **Valores**: `SpreadIn 0,6` · `SpreadOut −0,97` (×0,03: una sola masa) · `CurlIn 0,5` · `CurlOut −0,95` (×0,05: quieta) · `BreathAttract 1`.


### 🌬️ 2026-09-18 — al inhalar BAJA el brillo y ACHICA las gotas
Beltrán: *"En metaball, inhalación baja las intensidades, pero además achica tamaño de blobs"*.

- Dos `Custom` nuevos en `M_MetaBlob_SC`, **calcados de `BreathCurl`** (mismo código de 3 líneas, mismas 6 entradas `Val/S/On/G/CIn/COut`):
  - **`BreathRadius`** (`Custom_1`) → intercalado entre `ScalarParameter_3` (`BlobRadius`) y `AppendVector_1.B`.
  - **`BreathBright`** (`Custom_4`) → intercalado entre `ScalarParameter_9` (`Brightness`) y `Multiply_3.B`, que es el que multiplica el color ya lerpeado (`ColorShadow`↔`ColorLight`) antes del emisivo.
- Parámetros nuevos del material: `BreathRadiusIn/Out` · `BreathBrightIn/Out`, todos **default 0** → el material queda idéntico para quien no los prenda.
- BP: 4 variables nuevas (cat. *R - Respiracion*, instance-editable) + 4 pushes al final de `ApplyBreath`, que ahora empuja 9 parámetros.
- **Valores en `GAL_7_MetaBlob`**: `BreathRadiusIn −0,45` (13,58 → 7,47) · `BreathBrightIn −0,5` (×0,5) · **los dos `Out` en 0**: al exhalar vuelve a lo autorado, porque Beltrán solo pidió la inhalación. Si quiere el ciclo completo (exhalar más brillante/más gordo), son esas dos perillas.
- **Lectura resultante**: inhalar **dispersa y apaga** (spread ×1,6, curl ×1,5, gotas a la mitad, brillo a la mitad) · exhalar **funde y enciende** (spread ×0,03, curl ×0,05, tamaño y brillo autorados).
- ⚠ Gotas más chicas Y más separadas: el smooth-min puede dejar de fundirlas y verse 6 esferitas sueltas en la inhalación. Es decisión de aspecto; la perilla es `BreathRadiusIn`.
- ⚠ El raymarch con gotas más chicas no abarata: el `Spread` grande ya alarga el recorrido. No se midió.
- 🔩 Trampa pagada de nuevo (gotcha 141): `set_properties` **no puede crear las entradas de un `Custom` de una sola vez** (*"ArrayAdd: elements changed alongside the size change"*). Hay que **crecer el array replicando el elemento existente TAL CUAL** (leerlo y repetirlo, no un dict abreviado) y **después** renombrar con el tamaño ya correcto.
- ⬜ Sin visor. Se previsualiza en el viewport con `PreviewBreath` del manager (es todo material).


### 🔄 2026-09-18 (2a) — INVERTIDO respecto de inhalación/exhalación
Beltrán, tras verlo: *"en metaball, hagámoslo al revés respecto a inhalación exhalación"*.

Se intercambiaron las **cuatro parejas** `In`↔`Out` de la instancia `GAL_7_MetaBlob`. Como el mapeo es `m = 1 + S·lerp(−Out, In, smoothstep)`, swapear la pareja intercambia exactamente los dos extremos y **deja el reposo en 1**; no hizo falta tocar ni el material ni el BP.

| | antes | ahora |
|---|---|---|
| `BreathSpreadIn` / `Out` | 0,6 / −0,97 | **−0,97 / 0,6** |
| `BreathCurlIn` / `Out` | 0,5 / −0,95 | **−0,95 / 0,5** |
| `BreathRadiusIn` / `Out` | −0,45 / 0 | **0 / −0,45** |
| `BreathBrightIn` / `Out` | −0,5 / 0 | **0 / −0,5** |

`BreathAttract` queda en **1**: no es dirección, es cuánto le saca el control al reloj del material.

**Lectura nueva**: **inhalar reúne** (spread ×0,03, curl ×0,05 → una sola masa, con el tamaño y el brillo autorados) · **exhalar dispersa** (spread ×1,6, curl ×1,5, gotas a ×0,55 y brillo a ×0,5). El lado "muerto" pasó a ser la inhalación, que ahora es el reposo autorado + fusión.
- 👁️ Se previsualiza entero en el viewport con `PreviewBreath` del manager: es todo material.
- ⬜ Sin visor.


## 🧬 2026-09-18 — CUATRO MODOS DE DEFORMACIÓN (`BlobMode`)
Pedido de Beltrán con dibujo (CURL · SIMETRIC · ROUND · GROUP), para poder **explorar formas** y usar el mismo efecto en Breath, Mind y Heart. Plan: [`docs/PLAN-MODOS-METABALL-Y-PULSO-2026-09-18.md`](../../../../docs/PLAN-MODOS-METABALL-Y-PULSO-2026-09-18.md).

### Dónde entra, y por qué es barato
Las posiciones se calculan **una vez por píxel, ANTES del march**, en un bucle de 3 líneas. El march (`NSteps × N`) es lo caro. 👉 **Cambiar la ley de `P[j]` no cuesta casi nada; lo que cuesta es `BlobCount`.**

El bucle quedó con una forma única para los 4 modos:
```hlsl
P[j] = base*Spread + D*Spread*(1.0 - Attract) + curl*CurlAmt*curlG;
```
`base` = lo que NO colapsa con `Attract` (solo GROUP lo usa) · `D` = lo que sí colapsa · `curlG` = cuánto curl aporta ese modo.

| `BlobMode` | Modo | `D` | `curlG` | Lectura |
|---|---|---|---|---|
| **0** | **CURL** | `C[j]` (la tabla de siempre) | 1,0 | 🔴 **idéntico byte a byte a lo anterior** — es el default |
| **1** | **SIMETRIC** | gota 0 al centro; el resto en anillo XY `a = 2π(j−1)/(N−1)` | 0,15 | nacen unidas y se abren radialmente (la flor) |
| **2** | **ROUND** | igual + `a += Twist·(1−Attract)`, radio `1+0,35·SF[j]`, z `0,25·SF[j]` | 0,25 | **se abren girando**, y al cerrarse se desenroscan |
| **3** | **GROUP** | `base` = centro del grupo `g = j mod GroupCount` × `GroupSpread` · `D = C[j]·LocalScale` | 0,5 | `Attract` junta cada gota a SU grupo → quedan racimos |

### Cañería
- `ParC` pasó de float2 a **float4** = `(SizeVariation, BlobCount, BlobMode, GroupCount)`; entrada nueva **`ParD`** = `(Twist, GroupSpread, LocalScale)`. El `Custom` quedó en **6 entradas** (el tope conocido antes de que falle a compilar sin explicar es bastante más alto, pero 6 está probado).
- `maxT` del march ahora suma la extensión de los grupos, si no el rayo cortaba antes de llegar a los racimos lejanos.
- **Perillas del BP** (cat. *B - Modo*): `BlobMode` (int 0-3) · `GroupCount` (int) · `Twist` · `GroupSpread` · `LocalScale`, empujadas por la función nueva **`ApplyMode`** al final del Construction Script.
- ⚠ **El MCP no crea enums**: `BlobMode` es un entero. Si Beltrán crea a mano `E_BlobMode`, se migra y queda desplegable con nombres.

### 🔩 Dos trampas pagadas acá
1. 🔴 **`ApplyMode` colide con 4 funciones más.** `find_node_types(graph, "ApplyMode")` devuelve `Animation|SetApplyMode`, `Animation|GetApplyMode`, `Class|BPSensor|ApplyModeMesh`, `Class|BPSensor|ApplyModeMat` y `CallFunction|ApplyMode`. `create_node` tomó **la de animación** (un nodo con pin *by ref* sin cablear) y el Blueprint **no compiló**. ✅ Elegir el `type_id` **exacto** de la lista, nunca el `[0]`. (Familia del gotcha "colisión de nombres de función en el DSL", pero acá se ve a la primera porque rompe la compilación.)
2. 🔴 **Las 5 variables nuevas nacieron en 0 en la instancia ya colocada**, no con el default del CDO (`GroupCount` 4 → 0, etc.). Con `GroupCount = 0` el shader clampea a 1 grupo y GROUP no se lee. ✅ Sembradas explícitamente en `GAL_7_MetaBlob`.

### Rendimiento — el único riesgo real
| Gotas | Evaluaciones (`NSteps × N`) | vs. hoy |
|---|---|---|
| 6 (hoy) | 384 | ×1,0 |
| 9 (SIMETRIC del dibujo: centro + 8) | 576 | ×1,5 |
| 16 (GROUP holgado) | 1024 | ×2,7 |

El metaball ya aporta **~6-12 ms** de un presupuesto de 13,9 ms. **GROUP hay que medirlo en visor** con el `BlobCount` que de verdad se lea como racimos, antes de darlo por bueno.
⬜ Sin visor y sin juicio de Beltrán sobre las formas.


### 📐 2026-09-19 — los modos pasan al PLANO VERTICAL, y GROUP reparte parejo
Beltrán tras verlos: *"se están moviendo en horizontal, como el del mandala y el de twist y group. Deben quedar de frente al usuario, sino no veo la transformación"* y *"en el de group debemos respetar los tamaños de los blobs; cuando pongo todos iguales sin variación de tamaño, igual hay unos que se ven enormes y otros pequeños"*.

Se descartó el **billboard** (se probó a construirlo y se deshizo): *"es incómodo el face camera, que esté fijo mejor, pero rotado 90"*. 👉 **Cero perillas nuevas**: no hay `FaceCamera` ni en el material ni en el BP. Todo es el mismo `Custom_0`.

#### 1. El plano: de XY (horizontal) a YZ (vertical)
Los anillos de SIMETRIC / ROUND / GROUP estaban en el plano local **XY**, que en Unreal es el suelo → desde la altura de los ojos se veían **de canto**. Ahora viven en el plano local **YZ**, o sea mirando al **+X del actor** (su "adelante"):

| | antes | ahora |
|---|---|---|
| SIMETRIC (1) | `float3(cos a, sin a, 0)` | `float3(0, cos a, sin a)` |
| ROUND (2) | `float3(cos a·rr, sin a·rr, 0,25·SF)` | `float3(0,25·SF, cos a·rr, sin a·rr)` |
| GROUP (3), centro de grupo | `float3(cos ga, sin ga, 0,30·sin(ga·1,7))·GrpSpread` | `float3(0, cos ga, sin ga)·GrpSpread` |

🔑 **La orientación se autora con el gizmo del actor** (yaw), no con una perilla — se previsualiza en el viewport y no hay variable que se pudra. Los dos metaballs de la galería tienen **yaw = 0** y la galería corre sobre X, así que quedan de frente sin tocar nada.
- Se quitó el bamboleo en Z de los centros de grupo (`0,30·sin(ga·1,7)`): metía a los racimos a distintas profundidades y **eso solo ya hacía que unos se vieran más grandes que otros por perspectiva**.
- 🔴 **Modo 0 (CURL) sigue byte a byte igual**: `base`=0, `D`=`C[j]`, `curlG`=1, misma semilla de curl, mismo `maxT`. Lo aprobado en la estación 7 no se movió.

#### 2. GROUP: por qué se veían unos enormes y otros chicos
> ⚠ El diagnóstico de abajo sigue valiendo, pero **la solución que describe (racimos en anillo simétrico) quedó superada el mismo día** — ver §2.bis.
Con `SizeVariation = 0` los radios **ya eran todos iguales** (`R[j] = BlobRadius`). La desigualdad era **geométrica**, por tres causas encadenadas, medidas sobre los valores reales de `GAL_7_MetaBlob` (`BlobCount` 12,3 → 12 · `GroupCount` 10 · `Spread` 22 · `GrpSpread` 2,12 · `LocalScale` 0,59 · `BlobRadius` 1,28 · `Smoothness` 26,9):

1. 🔴 **`GroupCount` estaba CLAMPEADO a 8 en el shader** (`clamp(ParC.w+0.5, 1, 8)`) — la perilla en 10 mentía, igual que `Steps` arriba de 64. Con 8 grupos y 12 gotas, `g = j mod 8` daba **4 grupos de 2 gotas y 4 de 1**: los de 2 se funden por el smooth-min y se leen **al doble de tamaño**. Esa era la causa dominante.
2. Dentro de un grupo, `D = C[j]·LocalScale` usaba la tabla fija `C[]`, cuyos vectores **no son unitarios** (de 0,48 a 1,0) → las gotas de un mismo racimo caían a distancias muy distintas del centro: unas encimadas (bulto) y otras sueltas.
3. El curl era **por gota** (`±CurlAmt·0,5`), así que además rompía los racimos de forma distinta en cada uno.

**Lo que se hizo:**
- `GroupCount` ahora clampea a **[1, 16]** y además a **≤ BlobCount**. La perilla dejó de mentir.
- **Reparto parejo**: `M = floor(N / GroupCount)` gotas por grupo y, **solo en modo GROUP**, `N` se redondea a `GroupCount × M`. Todos los racimos tienen exactamente la misma cantidad de gotas. ⚠ **Consecuencia autoral: en GROUP, `BlobCount` se redondea para abajo al múltiplo de `GroupCount`.** Con 12 y 10 → **10 gotas** (y 2 que no se dibujan, lo cual además abarata el march). Para racimos de verdad conviene un divisor: 12 con `GroupCount` 4 → **4 racimos de 3**; con 3 → 3 racimos de 4.
- **Dentro del grupo, anillo regular** en el mismo plano vertical: `D = float3(0, cos ka, sin ka)·LocalScale` con `ka = 2π·k/M` → todas las gotas del racimo **equidistantes** de su centro. Con `M = 1`, `D = 0` y `LocalScale` no hace nada (es correcto: una gota no tiene arreglo interno).
- **El curl pasa a ser POR RACIMO** (`fs = g` en vez de `fs = j`): el racimo se mueve entero y **conserva su forma y su tamaño**. Antes cada gota vagaba por su cuenta y fundía distinto.

#### 3. Verificado
Captura del viewport desde el punto de vista del usuario (cámara a 620 cm delante, yaw 0): **10 gotas en un anillo vertical, del mismo tamaño**. Antes eran 8 grupos en una línea horizontal con 4 bultos dobles.
- ⚠ Queda una diferencia de **brillo** entre las gotas de arriba y las de abajo: es el lerp `ColorShadow`↔`ColorLight` por normal, que es intencional. Si molesta como "tamaño", la perilla es acercar `ColorShadow` a `ColorLight`.
- 💡 **`Smoothness` (26,9) es 21× `BlobRadius` (1,28)**: lo que se ve como "el tamaño de la gota" lo fija el smooth-min, no el radio. Si alguna vez se quieren gotas nítidas y separadas, la perilla es `Smoothness`, no `BlobRadius`.
- ⬜ Sin visor. `M_MetaBlob_SC` guardado; **el BP no se tocó** (ninguna variable nueva).

#### 2.bis GROUP son GALAXIAS, no un patrón regular (corrección del mismo día)
Beltrán, al ver el anillo de racimos: *"acordate que son agrupaciones repartidas **aleatoriamente**. Es distinto a los simétricos. Debe ser como si existieran pequeñas galaxias de 2 o 3 blobs cada uno **que se atraen entre sí, aparte de la atracción central general**"*.

🔑 **La lección:** se pidió "GROUP" y yo construí *SIMETRIC con racimos* — regular, todos los grupos iguales y equiespaciados. La palabra que decide el modo es **aleatorio**, y el error se ve a la primera en una captura. El reparto parejo que yo había puesto para arreglar los tamaños **era justo lo contrario del modo**.

**Cómo quedó:**
- **Reparto 2-o-3, sin descartar gotas.** `GroupCount` clampea a **`[1, BlobCount/2]`** (nunca galaxias de 1 gota, que es lo que producía los bultos dobles junto a gotas sueltas). `M = N/GN`, `REM = N − M·GN`: las primeras `REM` galaxias llevan `M+1` gotas y el resto `M` → con 12 gotas y 5 galaxias salen **2 de 3 y 3 de 2**. Ya **no se redondea `BlobCount`**: se usan todas.
- **Centros repartidos, sin amontonarse.** Primer intento: `base = C[g]` (la tabla del CURL) → **tres galaxias cayeron encimadas** y se fundieron en un bulto grande al lado de gotas sueltas (el defecto de siempre, por otra puerta). Ahora es un **anillo con jitter** en el plano vertical: ángulo `2π(g + hash·0,7 − 0,35)/GN` (separación angular garantizada), **radio aleatorio** `0,55…1,0` y **profundidad aleatoria** `±0,25`, todo × `GroupSpread`. Se lee aleatorio pero dos galaxias nunca ocupan el mismo lugar.
- **Dos atracciones, no una** (el pedido literal):
  - **local**, gotas → su galaxia: `aD = min(Attract·1,6, 1)`;
  - **central**, galaxias → el centro: `aB = Attract` ← **esto no existía**: antes `base` no colapsaba nunca, así que la atracción general no se sentía en GROUP.
  - `P[j] = base·Spread·(1−aB) + D·Spread·(1−aD) + curl·CurlAmt·curlG`.
  - ⚠ **Con `Attract` negativo los dos pasan a lineales sin clamp**, porque la respiración extrapola por debajo de `AttractMin` para la "máxima separación" y saturar ahí mataría ese rango.
  - 🔩 Primer intento: `aD = min(2·A,1)` y `aB = max(2·A−1,0)`. Con `AttractMin 0,05 / AttractMax 0,92`, `aB` trepaba a 0,84 y **el ciclo pasaba casi todo colapsado en un punto** — la captura salió negra. Al escalonar dos fuerzas hay que mirar **el rango real de la señal**, no el [0,1] teórico.
- Dentro de la galaxia: anillo regular de `msz` gotas (equidistantes → mismo tamaño) con **fase aleatoria por galaxia**, en el plano vertical. Curl **por galaxia** (`fs = g`): el grupo se mueve entero y conserva su forma.

**🔴 Lo que queda y es decisión suya:** con `Smoothness 26,9` contra `BlobRadius 1,28` y una separación interna de `LocalScale·Spread = 13` unidades, **las 2 gotas de una galaxia se funden en una sola**: se ven manís, no dos blobs. Para que se lean 2 o 3 blobs distintos hay que **bajar `Smoothness`** (a ~6-8) o **subir `LocalScale`** (a ~1,5). Es lo mismo que §343: el "tamaño" lo fija el smooth-min, no el radio.


## 🎵 2026-09-21 — CADA BLOB PULSA SEGÚN SU SLOT (`S - Secuenciador`)
Pedido de Beltrán para el nivel definitivo: *"Attracting tendrá ese metaball en el secuenciador, pulsando cada blop según su slot."*

### La ley: fase continua, sin cola de eventos
Es el mismo patrón ya probado en `BP_RingTunnel_SC` y `BP_PulseField_SC`. No hay buffer de "qué blob late ahora": cada blob calcula **cuánto hace que le tocó** a partir de una sola fase continua.
```hlsl
if (ParE.y > 0.0001)            // ParE = (PlayPos, PulseAmt, PulseFall)
{
  float na  = (float)N;
  float age = ParE.x - f;                    // f = índice del blob
  age = age - na * floor(age / na);          // envuelve en [0, N)
  R[j] = R[j] * (1.0 + ParE.y * exp(-age * max(ParE.z, 0.01)));
}
```
- `age = 0` justo cuando el playhead pasa por ese blob → **pulso pleno**, y decae con `PulseFall`.
- Con **N = NumSteps** el mapeo blob↔slot es 1:1 exacto y envuelve solo.
- 🔴 **`PulseAmt = 0` deja el shader byte a byte como estaba** → el metaball de la galería no cambia en nada. Las instancias viejas heredan 0 (las variables nacieron después), así que ni hubo que tocarlas.
- Coste: **un `exp` por blob**, fuera del march. El march (`Steps × BlobCount`) no se mueve.

### Cañería
- **Material**: 3 `ScalarParameter` nuevos (`PlayPos`, `PulseAmt`, `PulseFall`, grupo *S - Secuenciador*) → dos `AppendVector` → **`ParE`, la 7ª entrada del `Custom_0`**. ✅ Compila (el tope de 6 entradas era conservador; 7 anda).
- **BP**: `PulseAmt` · `PulseFall` · `bFollowSeq` (*S - Secuenciador*, instance-editable) + `PlayPos`/`SeqRef` (*Z - Estado*).
  - `ApplyPulse` colgado al final del Construction Script (después de `ApplyMode`) → se previsualiza en el viewport.
  - **`EventTick` → `TickPulse` → `SeekSeq` → `PushPlay`**: busca `BP_Sequencer_SC` con `GetActorOfClass` y cachea; `PlayPos = CurrentStep + StepTimer / max(StepDur, 0.001)`.
- **Instancia `Blob_Attracting`** (`MapsV3/L_SoulCharger_V3`): `BlobMode 0` · `BlobCount 8` (= los 8 slots) · `bFollowSeq ✔` · `PulseAmt 0,6` · `PulseFall 1,2`.

### 🔩 La trampa que cazó el read-back
El DSL resolvió `(+ CurrentStep (StepTimer/StepDur))` como una **suma ENTERA** (el primer operando es int) y **truncaba la parte fraccionaria**: `PlayPos` habría saltado de entero en entero y el pulso habría salido cuantizado. ✅ Arreglo: convertir explícito primero — `(bind _step (Math|Conversions|ToFloat(Integer) …))` y sumar en float.
👉 **Regla:** al mezclar int y float en el DSL, **convertir a mano y releer el grafo**. Compila igual de las dos formas.

### ✅ Verificado en PIE (medido, no supuesto)
Con la sala 4 corriendo y el secuenciador en fase 2:
| `CurrentStep` | `StepTimer` | `PlayPos` esperado | `PlayPos` medido |
|---|---|---|---|
| 3 | 0,217 | 3,33 | **3,40** |
| 4 | 0,434 | 4,65 | **4,73** |
| (tras el 7) | — | envuelve | **0,08** |
Cero `Accessed None`. ⬜ **Sin visor**: cuánto pulso (`PulseAmt`) y cuánta cola (`PulseFall`) son decisión de aspecto, y si conviene que los blobs estén en anillo (`BlobMode 1`) en vez de nube.
