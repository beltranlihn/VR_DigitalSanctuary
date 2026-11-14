# Análisis del levantamiento de calibración — zona segura del umbral (2026-08-24)

**Fuente:** 14 sesiones `CalibUser_*.sav` extraídas de la Quest por adb (`/sdcard/Android/data/com.YourCompany.VR_Test/files/UnrealGame/VR_Test/VR_Test/Saved/SaveGames/`), levantadas con el nivel `L_Calibration` (labels por prompt-timing de máquina, 7 segmentos, ~72 Hz, 18 columnas).
**Objetivo:** definir la **zona segura absoluta** (sin calibración por usuario) que acepta el sensor EN el estómago y rechaza el resto — *"evitar que el usuario entre en el umbral cuando no tiene la mano en el estómago"*.
**Scripts:** `parse_inventory.py` / `analyze.py` / `analyze2.py` (scratchpad de la sesión; método abajo para reproducir).

## Método
1. Parseo del bloque ASCII de cada `.sav`, filas `CROW` (t, seg, ls, as, amp, …, dist, horiz, vdrop), banda de guarda de 1 s al inicio de cada segmento.
2. Clases: **ESTÓMAGO** = EST + APNEA + NAT + RAPIDA + GUIADA (~7.900 filas/usuario) · **FUERA** = PIERNA (~1.000) · MOV aparte (lo mata la compuerta de quietud).
3. **Validación de sesión** (criterio objetivo por usuario): gap `horiz` entre pierna-P5 y estómago-P95 > 3 cm **y** movimiento real en MOV (`ls` mediana > 10). 
4. Umbrales por **envolvente entre usuarios** (max P97.5 / min P2.5 del set limpio + 10 % de margen), validados con **leave-one-user-out**.

## Hallazgos

### 1. Margen de error de los usuarios: 3/14 sesiones anómalas (21 %)
U1, U2 y U3 tienen estómago ≈ pierna (gap negativo) y **MOV sin movimiento** (`ls` mediana 0.2-0.3 — el sensor ni se movió en el ejercicio de movimiento): son sesiones de prueba viejas o protocolo no ejecutado, no participantes reales siguiendo las instrucciones. **Quedan excluidas del umbral y son la medida del error de protocolo esperable.** Importante: con la zona final, U1 y U3 quedan **100 % rechazadas** (fail-safe: un usuario que no sigue el protocolo no entra al umbral por accidente; la etapa cierra igual por tiempo — cero callejones sin salida).

### 2. En los 11 usuarios válidos, `horiz` separa PERFECTO — y con gap
- Estómago: `horiz` entre **3.1 y 20.1 cm** (envolvente P2.5–P97.5 de los 11).
- Pierna: `horiz` mínimo P5 = **26.0 cm**.
- **Gap limpio de 20.1 → 26.0 cm entre clases, sin solaparse en ningún usuario.** Es la confirmación multi-usuario del hallazgo de julio (`horiz` es EL discriminador). `dist` separa casi igual (AUC 0.95) pero es redundante teniendo `horiz`+`vdrop`; `vdrop` solo NO separa pierna (53-61 pisa el estómago de los más altos).

### 3. Zona segura final (aplicada a `BP_Sensor_Soul`, CDO + instancia)
| Perilla | Antes | **Ahora** | Base |
|---|---|---|---|
| `SafeHorizMax` | 28 | **23** | max P97.5 estómago 20.1 + margen; cae dentro del gap 20→26 |
| `SafeVDropMin` | 24 | **33** | min P2.5 estómago 38.0 − margen (rechaza mano alta/pecho/aire) |
| `SafeVDropMax` | 62 | **63** | max P97.5 estómago 59.1 + margen |
| `ActivateDelay` | 0.5 s | **1.5 s** | el reclamo "reconoció demasiado rápido": la entrada al umbral ahora pide 1.5 s sostenidos dentro de la zona (el estómago aguanta quieto de sobra; una mano al aire de paso, no). La salida sigue en 0.5 s |

**Resultado sobre los 11 válidos:** cobertura del estómago mediana 100 %, peor caso 99.7 % (U12) · **rechazo de la pierna 100 % en los 11**.

### 4. El margen de error entre usuarios (LOSO, el número honesto)
Dejando a cada usuario fuera y derivando el umbral con los otros 10: mediana de cobertura 100 %, **peor caso 66 % (U12)** — U12 es quien define el borde de la envolvente (estómago más alto/lejos: vdrop 59, horiz 20). Traducción: **un usuario futuro más "extremo" que los 14 medidos puede perder cobertura parcial** — el margen del 10 % lo amortigua, y más datos encogen ese riesgo. El rechazo de pierna en LOSO fue 100 % en todos.

### 5. Lo que los datos confirman de los valores actuales (sin tocar)
- **`StillLin` 8**: estómago P99 = 7.8 (calza exacto) y MOV P5 = 20.5 → separa. ✓
- **`StillAng` 25**: estómago P99 = 23.2 < 25 < MOV P5 = 25.4 — justo en la frontera. ✓
- **`MinAmplitude` 0.003** ≈ P5 de la amplitud respirando. ✓ Y la amplitud **no** distingue respirar de reposo (mediana 0.013 vs 0.016) — sigue siendo cierto que inhala/exhala necesita normalización por usuario (hallazgo de julio, pendiente para cuando se retome).

### 6. Límite del estudio (honesto)
"Mano en el aire" **no está en el dataset** (no hubo segmento de mano suspendida). La defensa contra ese caso es indirecta: la zona 3D es ahora mucho más chica (≤23 cm del eje de la cabeza, 33-63 cm bajo los ojos), la entrada pide 1.5 s sostenidos y quietos, y una mano sin apoyo suele fallar la quietud. **Si en visor sigue entrando con la mano al aire, el próximo levantamiento debería agregar un segmento "mano suspendida frente al torso"** para medirlo directo.

## Reproducir
`adb pull .../SaveGames/` → parsear bloque ASCII mayor de cada `.sav`, filas por `\n` literal, header `CCOLS`. Los tres scripts del análisis quedaron en el scratchpad de la sesión (recrearlos desde este doc es directo: percentiles + envolventes + LOSO, sin dependencias).

---

# Parte 2 — la SEÑAL de respiración y el mapeo del control (misma tarde)

**Pregunta de Beltrán:** un control reactivo, orgánico, sin rango por usuario (juego libre), que no se enrede con micro-movimientos. **Método:** los 7 ejercicios como ground-truth — GUIADA tiene fases cronometradas por máquina (ciclo 13 s: sostén 0-5 · inhala 5-8 · sostén 8-10 · exhala 10-13) y EST/APNEA son **sostenes en los dos extremos** (abajo exhalado / arriba con aire). Scripts `analyze3-6.py`.

## Hallazgos sobre la señal (`bv`, la inclinación band-passeada)
1. **El signo varía por usuario incluso con el prop de agarre fijo**: 5-6 de 11 invertidos. No es el agarre del mando de nuestra versión: es anatomía/colocación. **Ningún estimador pasivo lo recupera**: torneo contra el patrón-oro (signo = mediana APNEA − mediana EST): corr con horiz 4/11 · con −vdrop 5/11 · con dist 7/11 · asimetría de velocidad 5/11 · skew 5/11. Moneda al aire.
2. **No existe umbral binario universal de inhala/exhala** (confirma julio con 11 usuarios): las distribuciones por fase cronometrada se solapan casi por completo (medianas 0.0075 / 0.0087 / 0.0088). El ZigZag global nunca iba a andar.
3. **La amplitud varía 5-8× entre usuarios** (NAT P90: 0.012-0.055, mediana 0.036) → mapeo lineal fijo imposible, pero **sigmoide fijo** viable.
4. **Los sostenes en extremos separan**: con el signo correcto y K=0.012, sostener-abajo lee nivel ~0.27 y sostener-arriba ~0.72 (mediana); retención del sostén ~0.66 tras 10 s (decae suave con el τ20 — orgánico).
5. **Micro-movimiento en sostenes** ~0.023 (comparable a la señal) → pre-suavizado τ 0.6 s antes del mapeo.

## El mapeo implementado (v4, en `BP_Sensor_Soul.UpdateLevel`)
```
S      = EMA(bv, τ 0.6)                        ← mata el jiggle, respeta la respiración (0.1-0.3 Hz)
signo  = sembrado por UX (ver abajo), fallback manual (mano + bFlipSign)
x      = S·signo / GainK   (GainK = 0.012, de los datos)
nivel  = 0.5 + 0.5·x/(1+|x|)                   ← sigmoide racional: sin techo duro, sin "deuda"
BreathLevel = FInterpTo(nivel, LevelFollow 5)   ← el easing final
```
- Usuario mediano recorre **0.13 ↔ 0.87**; el más suave llega a ~0.71 (respirar más hondo = más recorrido: agencia real); el más fuerte ~0.93 sin clavarse. Respiración rápida sigue visible (reactividad).
- **El signo se siembra con la instrucción**: la página de práctica ahora dice *"take a slow, deep breath in"* — la **primera excursión sostenida** (>0.008 por >0.8 s, dentro del umbral) define la dirección de inhalar. Un aprendizaje invisible por sesión; `bFlipSign` como fallback.
- Descartadas por los datos: normalización AGC (asimetría infla/deflacta), envolvente por rango (mapea corto y hondo igual → sin agencia), correlación con horiz (4/11).

## Recomendaciones a futuro
- 🔴 **La solución definitiva del signo es FÍSICA**: cuando exista el arte del sensor real, que el prop defina la orientación del agarre (como el mesh del CalibProbe) + imagen en la instrucción. El seed por UX es el puente.
- El próximo levantamiento: agregar segmento **"mano suspendida frente al torso"** (el caso aire no está en el dataset) y quizá un prompt "inhala YA" para validar el seed.

---

# Parte 3 — 🔴 LA SEÑAL ERA LA EQUIVOCADA (medición con label de gatillo)

**El experimento de Beltrán:** correr la etapa apretando el gatillo mientras inhala y soltándolo al exhalar → **verdad-terreno del usuario real**, en la pose real, con el sensor real (esfera pegada al grip). 51 s, 3.808 muestras a 72 Hz, 18 fases de gatillo. Scripts `analyze_label.py` / `analyze_transform.py` / `analyze_geom.py` / `analyze_gain.py`.

## El veredicto de esa corrida
| Pregunta | AUC | Lectura |
|---|---|---|
| ¿La inclinación del mando (`bv`, lo que usábamos) distingue inhalar de exhalar? | **0.587** | **casi azar** |
| ¿El nivel seguía al gatillo? | 0.413 | invertido/azar |
| ¿La esfera seguía al nivel? | (r=0.955 en la corrida previa) | la cadena visual siempre estuvo sana |
| Fases con el nivel en la dirección correcta | **5/18** | azar puro |

👉 **No era el mapeo, ni el signo, ni la deriva: era la SEÑAL.** Todo lo construido encima (sigmoide, envolvente, seed de signo, anti-deriva) era refinamiento sobre una entrada que no contenía la información.

## Qué SÍ contiene la respiración (barrido de transformaciones, banda de guarda 0.6 s por el lag del gatillo)
| Transformación | AUC |
|---|---|
| **`horiz` band-pass 4 s** (distancia horizontal cabeza→sensor) | **0.837** |
| `vdrop` band-pass 4 s | 0.178 (= 0.822 invertido) |
| pendiente suavizada de la inclinación | 0.744 |
| band-pass corto de la inclinación | 0.70-0.71 |
| `bv` crudo (lo que usábamos) | 0.623 |

**Físicamente obvio en retrospectiva:** al inhalar, la panza se expande y **empuja el sensor hacia afuera**; al exhalar vuelve. Eso es un **desplazamiento**, no una inclinación. El prop de la calibración se apoyaba con orientación fija (por eso la inclinación rendía 0.756 ahí); **nuestra esfera pegada al grip tiene orientación arbitraria según el agarre → la inclinación es ruido, pero el desplazamiento sigue a la panza igual**.

## ✅ Validación multi-usuario (11 usuarios, fases cronometradas de GUIADA)
| Señal | AUC mediana | Mismo signo | Buenos (>0.7) |
|---|---|---|---|
| **`horiz` band-pass** | **0.990** | **10/11 suben al inhalar** | 9/11 |
| combo horiz−vdrop | 0.979 | 10/11 | 9/11 |
| `bv` (inclinación) | 0.756 | 10/11 | 9/11 |

🔴 **El signo es UNIVERSAL** (la panza empuja hacia afuera en todos): **muere el problema del signo** — no hace falta seed por UX, ni auto-detección, ni `bFlipSign` (queda como escape). El único usuario fuera de patrón es U11.

## Los parámetros, elegidos con los datos
- **`HorizTau` = 3 s** (band-pass `EMA(horiz,0.4) − EMA(horiz,3)`): AUC mediana 0.997, 9/11 buenos. Barrido 2-8 s; 3 s equilibra sensibilidad y sostenes. 🔴 **Y mata la deriva postural por construcción** → se elimina toda la maquinaria anti-deriva (`Baseline`/`PinT`/`PinTau`).
- **`GainK` = 0.5 cm** (el sigmoide ahora vive en centímetros de desplazamiento): en respiración natural el usuario mediano recorre **0.18 ↔ 0.81**, el más suave 0.70, ninguno se clava. Amplitud medida: recorrido 0.5-4.0 cm entre usuarios, mediana ~2 cm.

## `UpdateLevel` v6 (vigente)
```
S      = EMA(GeomHoriz, 0.4) − EMA(GeomHoriz, HorizTau 3)   ← reseed si no hay quietud
nivel  = 0.5 + 0.5·x/(1+|x|)   con x = S/GainK 0.5
BreathLevel = FInterpTo(nivel, LevelFollow 5)
```
Sin signo aprendido (fijo +1), sin baseline, sin envolvente, sin AGC. **Dormidas**: `SeedTheSign`/`SeedSign`/`bSignSeeded`, `Baseline`/`PinT`, `EnvHi`/`EnvLo`, `NormK`, `SigTau`, `SignAcc`. `bv` y el ZigZag quedan solo para el conteo por log.

## Lección de método
Tres iteraciones (envolvente, sigmoide, anti-deriva) se gastaron **afinando el mapeo de una señal que no discriminaba**. Lo que lo destrabó fue **un label de verdad-terreno del usuario real** (el gatillo) — el mismo principio del nivel de calibración, aplicado a la mecánica en su contexto real. 👉 **Ante "no se siente conectado", medir primero si la ENTRADA contiene la información, antes de tocar la transformación.**
