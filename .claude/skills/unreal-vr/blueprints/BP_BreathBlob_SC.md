# BP_BreathBlob_SC + M_BreathBlob_SC — el metaball de respiración (solo modo 0)

**Ruta:** `/SC_Breath/Blueprints/BP_BreathBlob_SC` + `M_BreathBlob_SC`
**Colocado en:** `/Game/SoulCharger/Mechanics/Breath/Maps/Test_Breath` como `Entering_Blob` (380, 0, 125)
**Nació:** 2026-09-27 · **duplicado de [[BP_MetaBlob_SC]] + `M_MetaBlob_SC`**, que quedan intactos.
**Estado:** 🟢 compila estricto, entrada/salida verificada en PIE y Simulate · ⬜ visor

## Por qué
Pedido de Beltrán: el metaball de la respiración, sin los modos que se agregaron después (SIMETRIC, ROUND, GROUP, LINE y el pulso del secuenciador), porque *"puede que se haya enredado"*.

## Qué se sacó
- **Material**: `Custom_0` reescrito **solo con el camino CURL**, conservando textual el código del modo 0 (`P[j] = C[j]·Spread·(1−Attract) + curl·CurlAmt`, `R[j] = max(Rad·(1+SizeVar·SF[j]), 0.5)`, `maxT = Spread·4 + rmax·6`, march y normal idénticos). Entradas del Custom: 7 → **5** (`RayOrigin, RayDir, ParA, ParB, ParC`); `ParC` = (SizeVariation, BlobCount) directo de `AppendVector_6`. Borrados por `delete_unused_expressions`: `BlobMode, GroupCount, Twist, GroupSpread, LocalScale, PlayPos, PulseAmt, PulseFall` + 6 appends. Quedan 24 parámetros, incluidos los 9 de respiración (leen `MPC_Breath`) y `ProxyStretch`.
- **BP**: borradas `ApplyMode, ApplyPulse, SeekSeq, TickPulse, PushPlay, FollowRow, FollowSlot` y sus 12 variables. El CS crea el MID desde `M_BreathBlob_SC`. `Volume.CastShadow = false` (no aporta nada en un raymarch translúcido).

## Estética = la de `Blob_Entering` (V3), sembrada en el CDO
Leída sin abrir `L_SoulCharger_V3` (`BP_MetaBlob_SC_C_0`, tags `STAGE_1`): SizeCM 220 · BlobRadius 13,58 · Smoothness 9 · Spread 19,46 · Attract 0,18 / 0,05 / 0,92 · Curl 19,37 / 0,42 · Steps 64 · Brightness 1,546 · ColorLight (0,92, 0,945, 1) · ColorShadow (0,026, 0,013, 0,12) · SizeVariation 0,45 · BlobCount 6 · BreathAttract 1 · Spread In/Out −0,97 / 0,6 · Curl −0,95 / 0,5 · Radius 0 / −0,45 · Bright 0 / −0,5. **Cualquier colocación nueva nace con esto.**

## Entrada / salida (`F - Entrada Salida`)
- `EnvT` (instance-editable, **1 en el editor** → se ve y se autora sin Play; scrubbeable como en el pacer) · `IntroTime` 2 s · `OutroTime` 2 s · `bAutoAppear` false (la etapa lo llama).
- `BlobApplyEnv`: quíntico de `EnvT` → `SetActorScale3D` con **piso 0,001** + `SetActorHiddenInGame(EnvT ≤ 0)`. 🔴 Escala 0 exacta degenera la transformada inversa del raymarch (cámara → espacio local).
- `BlobEnvStep(Dt)` en el Tick: avanza hacia `bShown` a `Dt/IntroTime` o `Dt/OutroTime`; al llegar a 0 saliendo, log `BLOB: salida terminada` + dispatcher **`OnBlobGone`**.
- `BlobAppear()` / `BlobDisappear()`. `BeginPlay` → `EnvT = 0` (oculto hasta que lo llamen).
- ⚠ El CS escribe la escala del actor: **el tamaño se autora con `SizeCM`, no escalando el actor**.

## 🔭 2026-09-27 (2ª) — las gotas ya no desaparecen al separarse
Beltrán en visor: *"cuando exhalo los blobs se separan, súper bien, pero llegan a un punto donde desaparecen"*. Dos causas, las dos crecían al exhalar:
1. **El rayo se cortaba antes de llegar** (gotcha 431): `maxT = Spread·4 + rmax·6` se medía desde el ojo; a 3,8 m (173 u) con las gotas achicadas daba ~143. **Shader**: el march ahora recorre solo la esfera envolvente real `bR = max(|P[j]| + R[j]) + Smth` (test rayo-esfera → `t` arranca en la entrada, `maxT` = la salida; si no la toca, sale sin marchar). Forma, gotas y normal sin cambios; además los 64 pasos se gastan solo donde hay algo.
2. **El proxy (cubo de 50 u) recortaba la nube**, que al exhalar llega a ~110 u. **`ApplyProxy` se ajusta solo** al peor caso de las perillas: `ext = Spread·max(1−AttractMin, 1+SpreadOut, 1+SpreadIn) + √3·CurlAmount·max(1, 1+CurlOut, 1+CurlIn) + BlobRadius·(1+SizeVariation)·max(1, 1+RadiusOut, 1+RadiusIn) + Smoothness`; `fit = ext/50·1,08`; la escala del proxy y el `ProxyStretch` se multiplican por `fit` (el SDF conserva su tamaño en el mundo). `ProxyTrim` sigue como recorte manual por eje.
- **El proxy pasó de cubo a ESFERA** (`/Engine/BasicShapes/Sphere`, radio 50 = el semilado del cubo): lo que tiene que contener es una esfera, y la esfera cubre menos pantalla que el cubo del mismo tamaño.
- Valores actuales: `ext` 110 u → `fit` 2,38 → proxy de ~2,45 m de radio (escala 5,23). ⚠ **Si el metaball queda a menos de ~2,5 m del usuario, la cámara entra en el proxy y deja de verse** (material one-sided). Con perillas de separación más chicas el proxy se achica solo.
- Verificado: capturas del viewport con `PreviewBreath` −1 / 0 / +1 (6 gotas separadas y enteras al exhalar, una masa al inhalar); PIE sin errores.

## 2026-09-27 (3ª) — gotas más grandes al exhalar + por delante del pacer
- *"Al exhalar… se están haciendo muy chicos"* → `BreathRadiusOut` **−0,45 → −0,15** (×0,85 en vez de ×0,55), CDO e instancia. `BreathBrightOut` sigue en −0,5 (al exhalar baja el brillo a la mitad: si todavía se leen chicas, esa es la otra perilla).
- *"El raymarch debe verse por frente del pacer"* → `Volume.TranslucencySortPriority` = **10** (el panel del pacer está en 0): se pinta después, así queda encima aunque el pacer esté más cerca. Es orden de translúcidos, no profundidad.

## 🌀 2026-09-27 (4ª) — el degradado se anima al inhalar/exhalar, quieto al sostener
Beltrán: *"cuando estemos inhalando, que el degradado se anime, como si estuviera activado; al exhalar también, en los aguantar no; entrada y salida suave"*.
- **BP `BlobMotionStep(Dt)`** (Tick, tras `BlobEnvStep`): lee `MPC_Breath` (`Signed`, `On`) vía dos puentes **`MPCSigned`/`MPCOn`** (el DSL agarra el `GetScalarParameterValue` de MID; el de colección se creó con `create_node` + `declaring_class KismetMaterialLibrary`). `Motion = FInterpTo(clamp(|dS/dt|·MotionGain)·On, MotionFollow)` → ~1 respirando, 0 sosteniendo, entrada/salida suave. `GradPhase` (en vueltas, `Fraction`) avanza `Motion·GradSpeed·dt` → se congela en los sostener, nunca salta.
- **Material:** `ParC` pasó a float4 (+ `Motion`, `GradPhase`); en el raymarch, tras la normal: rotación alrededor de X local (el eje de mirada) por `GradPhase` + onda `sin(dot(pos,(0,.71,.71))·0,12 − 2·GradPhase)` de amplitud `Motion·GradWave`. Con `Motion` 0 y fase quieta = el look de siempre.
- Perillas `G - Movimiento`: `MotionGain` 2 · `MotionFollow` 2,5 · `GradSpeed` 0,6 rad/s · `GradWave` 0,35. Medido: `Motion` ~0,95 moviéndose, ~0,05 en los extremos.
- Sin referencia al rig: solo el MPC (portable).

## 📏 2026-09-27 (5ª) — medido en la Quest + bordes, ameba y degradado en los sostener
**Medición** (`quest_entering_perf.ps1`, sesión `perf/entering_20260927_190458`, resolución 0,18 ms): el metaball cuesta **7,09 ms de GPU por cuadro** (m0 − m1; 7,67 por m2 − m3) = **75% de la etapa** (9,43 ms) y 51% del presupuesto de 72 Hz. La etapa **entra en 72 fps con 4,47 ms de sobra**, y con la GPU en nivel 2 (456 MHz): el margen real es mayor. Beltrán: *"nunca sentí baja de frame rate, se veía súper fluido, se puede forzar un poco más"*.

Sus pedidos tras verlo en visor:
1. *"Los bordes se ven un poco cuadriculados, pixelados"* → **el shader devolvía `hit` binario (0/1) como opacidad**: cada píxel del borde era todo o nada, y el MSAA 4x no lo toca (solo alisa bordes de geometría; el borde de un raymarch está dentro del shader). **Cobertura por distancia mínima en píxeles**: `pixA = length(fwidth(rd))` (calculado arriba de todo, antes de cualquier rama, para que las derivadas valgan); en cada paso `rr = res / (t·pixA)` y se guarda el mínimo y su posición `bpos`; al final `cov = hit ? 1 : 1 − smoothstep(0, 1, minR)` → el píxel que el rayo rozó a menos de un píxel del borde queda parcialmente opaco. La normal de esos píxeles se calcula en `bpos` (si no, el borde saldría del color de la normal por defecto). Sale `float4(nrm, cov)`. Costo: una división y una comparación por paso. De paso tapa los agujeros de rayos rasantes que agotaban los 64 pasos sin tocar.
2. *"En inhalar queda en un círculo perfecto sin nada de movimiento; debería verse con un poco de deformación tipo ameba"* → a inhalación plena el spread quedaba ×0,03 y el curl ×0,05: una esfera quieta. **`BreathSpreadIn` −0,97 → −0,85 (×0,15) y `BreathCurlIn` −0,95 → −0,7 (×0,3)** (CDO e instancia): la masa sigue reunida, pero las gotas se siguen moviendo 6-10 u dentro de ella y el contorno se deforma y respira. Más negativo = más redondo y quieto. Captura del viewport: el círculo pasó a una masa ovalada; el reposo, sin cambios.
3. *"La animación de textura que siga en los sostener, pero lenta y suave"* → perilla **`MotionIdle` 0,25** (`G - Movimiento`): `Motion = FInterpTo(max(|dS/dt|·gain·On, MotionIdle))`. En los sostener el degradado gira a un cuarto de velocidad y la onda queda en 0,25·`GradWave`. Medido en PIE: `Motion` 0,95 en las transiciones, 0,25 exacto en los extremos.
4. *"Se va demasiado rápido a cada extremo, debería tomar 3-4 s"* → se resolvió en el rig ([[BP_BreathRig_SC]], `FollowBreath`), no acá: el metaball lee `MPC_Breath` directo.

## 🔍 2026-09-27 (6ª) — los bordes seguían pixelados: la rampa estaba MUERTA
Beltrán en visor, con la 5ª instalada: *"el metaball todavía se le ven los bordes pixelados… el pacer se ve detalladísimo"*. Diagnóstico con un workflow (investigadores de motor, grafo y config + 3 escépticos que no pudieron refutarlo; gotcha 444):
- `eps = Rad·0,02` ≈ 0,27 u es **del tamaño de un píxel** en la silueta (`t·pixA` ≈ 0,21-0,26 u con el eye buffer real 1680×1760). Todo rayo a menos de ~1 px del borde ya contaba como `hit` → la rampa de la 5ª casi nunca actuaba (simulación 2D con el Custom real: 0,11-0,36 píxeles parciales por píxel de silueta).
- **Arreglo**: `rr = (res − eps) / (t·pixA)` (la rampa arranca en el umbral, continua con el hit) y ancho `smoothstep(0, EdgeW, minR)` con **`EdgeAA` = 1,5** (parámetro nuevo del material, grupo `E - Calidad`, sexta entrada `Edge` del Custom). Simulado: ~2 píxeles parciales por píxel de silueta en reposo, attract y exhalación. Mismo march (6,9 pasos medios en los dos), costo < 0,1 ms, sin parpadeo (el mínimo muestreado difiere del denso en 0,001 de mediana).
- **Descartado**: precisión (el material YA es `MFPM_Full_MaterialExpressionOnly`, como su padre y los hermanos), foveación, pasos, empaquetado (el cambio anterior sí había llegado al APK: FULL COOK con el shadermap recompilado).
- ⚠ **Lo que NO cubre**: los contornos de oclusión INTERNOS (donde un lóbulo tapa a otro) siguen siendo binarios: el rayo del borde del lóbulo de adelante termina como hit en el de atrás y el color salta por la normal. Según la pose son 0-34% de la "energía de escalón"; la silueta contra el negro es el 66-100%. Si Beltrán sigue viendo escalera DENTRO de la masa, es esto.
- **Prueba en vivo**: `BP_PerfEntering_SC` ganó `PerfEdge0/1/2` (EdgeAA 0,01 / 1,5 / 5) y `scripts/quest_borde.ps1 0|1|2|-Ciclo` los manda por adb con confirmación del eco. 0 = control negativo (tiene que verse como antes), 2 = control positivo (difuso; si no se distingue de 0, el parámetro no llega).

## 🎨 2026-09-27 (7ª) — el azul ya no queda fijo en la esquina
Beltrán tras el ciclo de bordes (*"se veía mucho mejor"*; el modo 2 difuso confirmó que el parámetro llega): *"todos los blobs tienen un punto azul fijo; el color entre blanco y azul debiera mezclarse más orgánicamente al inhalar y exhalar, no quedarse quieto en la esquina"*.
- **Causa:** el color es `Lerp(ColorShadow, ColorLight, saturate(dot(nrm, L)·0,5 + 0,5))` con **`L` constante** (`Constant3Vector_0` = (0,42, −0,57, 0,71)): una luz direccional fija → todas las gotas tienen el azul abajo a la derecha. La animación de la 4ª solo giraba la normal alrededor del eje de mirada: el azul se paseaba por el BORDE, nunca entraba a la superficie.
- **Shader (solo en píxeles que tocan, costo despreciable):** (1) la luz además **se balancea** ±40° alrededor de Z (`0,7·sin(GPh·0,375)`) → el lado oscuro barre la cara; (2) **campo de flujo**: 3 senos 3D con dominio deformado sobre la posición local (`q = np·FlowScale`), desplazados por `GPh`, empujan la normal con fuerza `FlowAmt + Mot` → manchas blancas/azules que recorren el cuerpo y se mueven con la respiración (lentas en los sostener por `MotionIdle`). Reemplaza la onda plana de la 4ª.
- **Parámetros nuevos del material** (grupo `G - Movimiento`, entrada `Flow` del Custom = Append): **`FlowAmt` 0,6** (fuerza de las manchas; más alto = más mezcla y menos volumen) · **`FlowScale` 0,12** (tamaño: más alto = manchas más chicas).
- 🔴 **La fase ahora da la vuelta cada 16π** (los dos literales 2π de `BlobMotionStep` → 50,2654825): con ritmos no enteros de `GPh`, la vuelta a 0 cada 2π habría producido un **salto visible** cada ~7-10 s. Regla: **todo multiplicador de `GPh` en el shader tiene que ser múltiplo de 1/8.**
- `GradSpeed` 0,6 → **0,9** (CDO e instancia): más mezcla mientras se respira.
- **Perillas en el BP** (pedido de Beltrán, misma tarde): **`FlowAmt` 0,6 y `FlowScale` 0,12** en `G - Movimiento`, instance-editable. Las empuja al MID la función nueva **`ApplyFlow`**, llamada al final del Construction Script (después de `BlobApplyEnv`) → se ven en el viewport y se re-aplican si se editan en el actor de PIE. Verificado: aparecen como overrides en `MID_M_BreathBlob_SC_0` (0,6 / 0,12). Los defaults del material quedan como respaldo.
- Captura del editor: reposo con el azul en manchas distintas por lóbulo; inhalación con vetas que cruzan la masa. PIE: 0 errores; `GradPhase` avanza lento sin respiración.

## 🩶 2026-09-29 — ya no se pone gris al respirar
Beltrán en visor: *"siento que al respirar el metaball se pone gris"*. Era `BreathBrightOut` −0,5 (al exhalar el brillo caía a la mitad). → **0** en el CDO (la instancia `Entering_Blob` hereda, sin override). Rollback: `VR_Test/Saved/ClaudeScripts/vida/ajustes_0929/rollback_valores_antes.md`.
## 🌱 2026-09-30 (noche) — entrada y salida por MORFEO (pedido de Beltrán: "no de escala 0 a 1 con la misma forma: los blobs crecen y se mezclan")
Sin tocar el shader del raymarch. `BlobApplyEnv` (vaciada y reescrita) + función nueva **`BlobMorph`**: empuja al MID del `Volume` las perillas de forma × una curva de `EnvT` (quíntica `q`); en `q` = 1 todo vale EXACTAMENTE la perilla autorada.
- `BlobRadius` × lerp(`MorphRadius` 0,08, 1, q) · `SizeVariation` lerp(`MorphSizeVar` 1,6 → la perilla): con 1,6 las gotas de SF negativo quedan en el piso del shader mientras las otras crecen → **nacen escalonadas** · `Spread` × lerp(`MorphSpread` 1,9 entrando / `MorphSpreadOut` 2,3 saliendo, 1, q) (según `bShown`) · `Smoothness` × lerp(`MorphSmooth` 0,2) · `Brightness` × lerp(`MorphBright` 1,35) · `CurlAmount` × lerp(`MorphCurl` 1,3).
- Escala del actor = smoothstep(0, 0,2, EnvT) × lerp(`MorphScale` 0,5, 1, q) (nace de tamaño cero, sin puntos que salten el primer cuadro). La sombra del valle la sigue igual.
- `IntroTime` 2 → **4** s, `OutroTime` 2 → **2,5** s (CDO; en la instancia de Test_Breath eran 2/2 heredados, no autorados: se escribieron 4/2,5).
- Perillas en `F - Entrada Salida` (instance-editable). Paso del Tick limitado: `min(DeltaSeconds, 1/30)` antes de `BlobEnvStep` y `BlobMotionStep` (cirugía en el EventGraph; regla de la obra).
- Verificado: capturas desde los ojos a `EnvT` 0,1 / 0,25 / 0,4 / 0,6 / 0,8 / 1 (`Saved/ClaudeScripts/usertool/morfeo_ojo.png`): puntos → gotas chicas dispersas de tamaños distintos → crecen y se acercan → el metaball autorado. PIE: `BLOB: entra` → `sale` → `salida terminada` 2,5 s.
- ⚠ Capturar a menos de ~2,5 m del metaball deja la cámara dentro del proxy (one-sided): desaparece en la foto, no en el juego.
## Conexión con la respiración
Ninguna referencia de clase: lee **`MPC_Breath`** (lo escribe [[BP_BreathRig_SC]]). Sin umbral (`On` = 0) sigue su reloj de atracción; con umbral la respiración toma el spread, el curl, el radio y el brillo (mapeo `m = 1 + S·lerp(−Out, In, smoothstep)`, ver el tracker del original).
- **2026-09-30 (tarde):** `IntroTime` 4 → **2,5** s (agilidad, decisión de Narrativa; CDO e instancia de Test_Breath).
