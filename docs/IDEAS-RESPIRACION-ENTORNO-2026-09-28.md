# Ideas — la respiración maneja el entorno de Entering (2026-09-28)

> **Estado:** propuesta, **nada construido**. No se tocó Unreal ni ningún asset. Este documento sintetiza tres investigaciones (referencias, inventario del proyecto, costo en Quest) y tres juegos de propuestas (lentes poética, de biofeedback y técnica), bajo la **directiva ya decidida por Beltrán**: el efecto primario es **el aliento visible** (motas que entran a la boca al inhalar y salen de la boca al exhalar, ancladas a la cabeza).
>
> **Números:** los que dicen *medido en el modelo* salen de un modelo en Python del efecto (`VR_Test/Saved/ClaudeScripts/ideas_respiracion/air_model.py` + `sim_air.py`), no de la Quest. Los costos de GPU son **estimados** con la calibración del proyecto (1 ms ≈ 130-170 op-eq/px a pantalla completa; 0,0055-0,011 ms por millón de op-eq de vértice) y **se miden** antes de dar nada por bueno.

---

## 0. Resumen en un minuto

- **Idea fuerza: UN SOLO AIRE.** El aire que el usuario respira es el aire del valle, visto en tres escalas a la vez: la **boca** (las motas, a 20-110 cm), el **alma** (el metaball y su sombra, a 3,8 m) y el **horizonte** (la bruma y el resplandor, a 60-600 m). Al inhalar, el usuario *toma* el aire frío del valle: las motas le entran a la boca y la bruma lejana se aclara, como si se la hubiera llevado. Al exhalar, *devuelve* el aire tibio: una pluma sale de su boca y el valle se entibia y se empaña. En las pausas, el aire queda suspendido. El cuerpo manda y el mundo le hace eco.
- **Primera tanda (4 efectos, uno primario):**
  1. 🔴 **Aliento visible** (primario): 2048 quads de malla con HLSL propio, un solo draw call, colgados de la cámara del pawn desde `BP_BreathRig_SC`.
  2. **La bruma respira**: niebla del valle más abierta al inhalar, más cerrada y tibia al exhalar.
  3. **El resplandor inhala**: el brillo rosa detrás del metaball sube y se afina al inhalar.
  4. **La sombra de Tanguy respira**: la sombra del metaball se recoge al inhalar y se abre al exhalar, junto con las gotas.
- **Costo total estimado:** ≈ **0,03-0,06 ms de GPU** (≤ 0,1 ms con margen) y < 0,1 ms de CPU. Las capas del valle se empujan desde el BP: **0 ms de GPU** (leer el MPC en el material costaría ALU por píxel; ver §3.3).
- **Antes de construir:** medir el valle en `PerfValley` (todo el margen depende de ese número).
- **Decisiones abiertas** (§8): dónde vive el aliento (recomendado: dentro del rig, como los mandos); qué pasa si no se detecta la respiración; a dónde apunta la pluma; si las capas del valle entran de a una.

---

## 1. La idea fuerza: un solo aire

### 1.1 Qué se ve

| Momento | La boca (motas) | El alma (metaball y sombra) | El horizonte (valle) |
|---|---|---|---|
| **Inhala** | Motas diminutas y frías (lavanda muy clara) se encienden en el aire de adelante, en la parte baja de la vista, y fluyen hacia la boca. Se apagan antes de llegar | El metaball se reúne (ya lo hace); su sombra se recoge, más densa y nítida | La bruma retrocede, las colinas lejanas se recortan un poco más, el resplandor rosa sube y se afina |
| **Retiene** | Las motas quedan **suspendidas** donde estaban y se apagan despacio (τ 2,5 s) | Quieto | Quieto (segunda tanda: el oleaje de luz también se detiene) |
| **Exhala** | Una pluma tibia (durazno pálido) **sale de la boca**, frena, se abre, sube apenas y se apaga hacia 1,1 m, en dirección al pie del metaball | El metaball se dispersa y baja su brillo (ya lo hace); su sombra se abre, se ablanda y se entibia | La bruma se cierra un poco y toma el tinte tibio del aliento; el resplandor baja y se abre a lo ancho |
| **Pausa** | La pluma queda suspendida y se desvanece | Quieto | Quieto |

### 1.2 Por qué une en vez de sumar efectos

- **Una física, no un catálogo.** Lo que entra a la boca tiene el color del aire del valle; lo que sale tiene el color que después toma la bruma. Un solo par de colores (**frío entra, tibio sale**) ata las tres escalas. El aire exhalado es de verdad más tibio, así que se lee sin explicación.
- **Jerarquía clara.** La boca es el canal **inmediato** (latencia de ~0,3 s en el modelo) y el más legible: enseña el vínculo en la primera respiración (Prpa 2018: no saber que uno controla genera malestar). El alma ya está validada. El horizonte es el **eco** lento y sutil (Wen 2019: el vínculo causal aguanta demoras de segundos).
- **Tesis de la obra (OBRA §6):** nada empuja al usuario hacia adelante; el espacio alrededor cambia porque respira. El valle no se mueve (su geometría queda quieta), solo cambia su aire.
- **Reglas de la casa:**
  - Capa A + capa B: el valle y el metaball ya tienen su vida autoral. El aire es capa B pura, multiplicada por `On`. La capa A del aire queda como decisión (§8).
  - No se premia la amplitud: todo sale de `Signed`, que está normalizado (NormRange).
  - Sin HUD ni puntaje.
  - Ninguna geometría del valle respira: la regla de confort §14.3 del plan del valle queda intacta.

---

## 2. Síntesis de las tres lentes

Las tres lentes coinciden en lo esencial: modular luz, color y niebla (no geometría), sombra que respira, pausas quietas, sonido como palanca de costo cero, motas diminutas en lugar de humo. Los conceptos equivalentes se fusionaron. Puntajes de 1 a 5 (5 = mejor); el costo es GPU estimado.

| # | Concepto (fusionado) | Viene de | Inmersión / surreal | Claridad del biofeedback | Estética minimal | Costo | Riesgo de confort | Esfuerzo | Veredicto |
|---|---|---|---|---|---|---|---|---|---|
| A | **Aliento visible** (boca) | directiva de Beltrán; "polvo" de las 3 lentes | 5 | **5** | 4 | 0,03-0,06 ms | medio → **bajo** con las reglas de §3.2.4 | 14-20 h | 🔴 **Tanda 1, primario** |
| B | **La bruma respira** (profundidad del aire + tinte tibio) | poética 1, bio 1, técnica 1 | 4 | 3 | 5 | 0 (BP) | bajo | 3-4 h | **Tanda 1** |
| C | **El resplandor inhala** | técnica 3, poética 5, bio 1 | 3 | 3 | 5 | 0 (BP) | bajo (banda ≤ 1°) | 1 h sobre B | **Tanda 1** |
| D | **La sombra de Tanguy respira** | poética 4, bio 6, técnica 5 | 4 | 4 | 5 | 0 (BP) | bajo | 1-3 h | **Tanda 1** |
| E | El mundo contiene el aire (pausas: el oleaje de luz se detiene) | las 3 | 5 | 3 | 5 | ~0 | mejora | 4-6 h (toca los VS del valle) | Tanda 2 (1°) |
| F | El aire suena (pasabajos, hálito al exhalar, silencio en las pausas) | poética 7, bio 7 | 5 | 4 | 5 | 0 GPU | nulo | 6-12 h + Config compartida | Tanda 2 (1°) |
| G | El eco llega al horizonte (anillo de luz a ≥ 45 m al exhalar) | poética 2, bio 2 | 4 | 4 | 4 | 0,04-0,1 ms | bajo-medio (expansión) | 8-12 h | Tanda 2 |
| H | Coherencia con el pacer → la paleta vira y el aire se aclara | bio 3, técnica 3, poética 5 | 4 | 3 | 5 | 0 | nulo | 5-8 h | Tanda 2 |
| I | La luna se llena (medidor sin números) | bio 4, técnica 4 | 3 | 2 | 5 | 0 | nulo | 1-2 h sobre H | Tanda 2 |
| J | El valle emerge de la bruma a lo largo de la etapa (revelación lenta) | técnica 1 (lento) | 4 | 2 | 5 | 0 | bajo | 3-4 h | Tanda 2 |
| K | El aire lejano: motas de 2-12 m reveladas por el resplandor | poética 3, bio 6, técnica 7 | 4 | 3 | 3 | 0,05-0,12 ms | medio | 6-8 h (reusa A) | Tanda 2, condicional |
| L | El llano exhala luz (`SwellShade`/`Sheen` más fuertes al exhalar) | técnica 2 | 3 | 2 | 4 | 0 | bajo-medio | 1,5-2 h | Tanda 2, alternativa barata a G |
| M | Háptica al completar una exhalación larga | bio 7 | 2 | 3 | 5 | 0 | nulo | 1-2 h | Tanda 2, a probar |
| N | Vaho: pocos sprites grandes y casi transparentes dentro de la pluma | nuevo | 3 | 3 | 3 | 0,02-0,05 ms | medio (mancha cerca del ojo) | 3-4 h | Tanda 2, a probar |
| — | Jirones de humo pintados en `ValleyPS` | poética 1, bio 3 | 3 | 2 | 3 | 0,1-0,3 ms | bajo | 6-10 h | Descartado por ahora (§5) |

---

## 3. Primera tanda

### 3.1 Jerarquía y entrada en la etapa

| Momento de la etapa (GUION V4, acto 5) | Qué está encendido |
|---|---|
| `StagePrepare` (el velo baja) | nada de la capa viva: el valle y el metaball autorales |
| `StagePractice` (instrucciones, el rig ya responde) | **A — aliento visible**. Es el mejor maestro del gesto: la primera exhalación con el sensor bien puesto hace salir aire de la boca |
| Ciclo 1 del pacer | A + **D** (la sombra: extiende lo que el metaball ya enseñó) |
| Ciclo 2 | + **B** y **C** (la bruma y el resplandor) |
| Ciclos 3-5 | todo, a ganancia plena |
| Salida del pacer / `Retire` del rig | el aire se apaga con el rig (`RevealT`); el valle vuelve a lo autoral con `On` → 0 |

La entrada por ciclos la maneja `BP_BreathStage_SC` (ya conoce el ciclo del pacer) con una sola llamada `Valley.SetLiveAmount(x)`. Es una recomendación (decisión 4 de §8): también se puede todo junto desde `StagePractice`.

### 3.2 A — El aliento visible (primario)

#### 3.2.1 Arquitectura: quién conoce a quién

- **El pawn no se toca.** `BP_BreathRig_SC` ya encuentra la `CameraComponent` del pawn (`CamRef` en `Acquire`) y ya engancha mallas a las manos en `MountRig`. El aliento se engancha igual, **a la cámara**.
- **Recomendado: el aliento es parte de la capa visual del rig** (como los mandos y el sensor), en su propia categoría **`G - Aliento`**, con funciones propias:
  - componente **`Air`**: StaticMesh `SM_BreathAir_SC` con `M_BreathAir_SC`;
  - **`MountAir`**: dentro de `MountRig`, adjunta `Air` a `CamRef` (sin offset);
  - **`AirStep(Dt)`**: en el Tick, **después** de `TickBreathGated`, para leer el `BreathFollowVel` de este cuadro;
  - **`PushAir`**: escribe todo lo del cuadro al MID, en una sola función (gotcha 465);
  - **`PreviewAir`**: en el Construction Script, junto a `PreviewRig`.
- **Por qué en el rig y no en un actor aparte:**
  - El rig ya tiene las cuatro cosas que el aliento necesita: la cámara, la señal cruda de este cuadro (`BreathFollowVel`, `BreathFollow`, `BreathOn`), el ciclo de vida (`SetRigActive`, `Retire`, `RevealT`) y la vista previa en el viewport.
  - Sigue la regla del proyecto: solo el controller de la mecánica conoce al pawn.
  - Queda portable: cualquier nivel que use el rig trae el aliento, apagable con `bAir`.
- **Alternativa**, si se prefiere un rig más liviano: un actor `BP_BreathAir_SC` colocado en el nivel. El rig lo encuentra y le pasa `CamRef` y una referencia a sí mismo (`Air.Bind(Rig, Cam)`). Cuesta una indirección más y no cambia nada visible (decisión 1).
- ⚠ **Gotchas a cumplir:**
  - **239:** todo lo que viaja pegado a la cámara nace `NoCollision`, en la plantilla.
  - **478:** un componente nuevo no llega bien a la instancia ya colocada en `Test_Entering`. Diffear la instancia contra la plantilla y escribir cada propiedad en su propia llamada.
  - **420/435:** las variables nuevas nacen en 0 en la instancia.

#### 3.2.2 La técnica: malla de quads con HLSL propio (gotcha 477), no Niagara

- **`SM_BreathAir_SC`**: 2048 quads reales de 0,4 cm (768 para inhalar y 1280 para exhalar), con sus números al azar en las UV:
  - UV0 = esquina;
  - UV1 = (desfase en la cinta *e*, profundidad *u*);
  - UV2 = punto en el disco unitario (*a*, *b*);
  - UV3 = (fase *φ*, corriente 0/1).
  - Se genera headless con un script `gen_breath_air.py`, como las mallas del valle y de Loving.
  - Los límites se agrandan para cubrir ±2 m alrededor de la cámara, porque el WPO mueve los quads.
- **`M_BreathAir_SC`**:
  - Unlit, Translucent **AlphaComposite (premultiplicado)**, two-sided, sin escribir profundidad (la receta de `M_LovingDust_SC`).
  - VS Custom `BreathAirVS`: calcula el centro de la mota, hace billboard contra `CameraPositionWS` y colapsa a tamaño 0 los quads con alfa ≈ 0, así no cuestan píxeles.
  - PS `BreathAirPS`: disco gaussiano.
  - Sin arreglos ni índices dinámicos en el VS (en Quest rompen la malla) y sin bucles (gotcha 399).
  - Las dos corrientes se separan con un `[branch]` por la bandera de UV3. Como los vértices van ordenados, casi no hay divergencia.
- **`TranslucencySortPriority` 20**: se dibuja después del pacer (0) y del metaball (10). El aire siempre está más cerca que ellos: la pluma termina a ~1,1 m y el proxy del metaball empieza a ~1,35 m del ojo.
- **Por qué no Niagara.** Niagara daría partículas con estado en el mundo, que es su única ventaja real aquí. En contra:
  - No se previsualiza con `PreviewBreath` sin simular.
  - En el proyecto no hay ningún Niagara validado en visor.
  - Arrastra las trampas de Android (`QualityLevel` capado en [0,1] y el prefijo `User.` sin resolver).
  - La receta de quads ya está probada en Loving, cuesta cero CPU y es determinista.
  - **Niagara queda como plan B** si en el visor el marco con retardo (§3.2.3) no convence.

#### 3.2.3 Anclado a la cabeza: qué vive en el espacio de la cabeza y qué en el del mundo

La malla no tiene estado: cada mota se calcula en el VS a partir de su semilla y de lo que el BP empuja. Para que **lo inhalado siempre entre a la boca actual** sin que el aire se vea pegado a la cara, cada camino une **dos marcos**:

| Marco | Qué es | Quién lo usa |
|---|---|---|
| **Boca exacta** `M` | cámara + 6 cm adelante − 9 cm abajo (ejes de la cabeza; `MouthFwd`, `MouthDown`) | el **destino** de lo inhalado y el **origen** de lo exhalado |
| **Marco del aire** (con retardo) | la posición de la boca seguida con τ 0,3 s; el yaw de la cabeza seguido con τ 0,8 s (×3 durante las pausas); el pitch de la cabeza × 0,5, recortado a [−35°, +10°] | el **origen** de lo inhalado (el volumen de adelante) y el **destino** de lo exhalado (la pluma) |

**Cómo se ve con la cabeza en movimiento:**
- Los movimientos rápidos y chicos (el balanceo natural) dejan al aire **quieto en el mundo**, así que no parece suciedad pegada al lente.
- Un giro deliberado arrastra la nube detrás de la cabeza en ~1 s, y el aire vuelve a quedar adelante.
- Mientras tanto, las motas inhaladas siguen entrando a la boca **actual**, por construcción.
- En el modelo, un giro de 30° en 0,6 s deja el marco del aire **hasta 24° atrás** (ver `geometria_aliento.png`, panel derecho).

**Por qué no todo en el mundo:** la malla no guarda dónde nació cada mota. Lo exhalado podría quedar realmente fijo en el mundo guardando la pose de la boca de las dos últimas bocanadas (2 juegos de uniformes, sin arreglos). Queda como mejora si en el visor la pluma "sigue" demasiado a la cabeza.

**Por qué el pitch se atenúa:** si el usuario mira el cielo, el aire no sube a cruzarle la vista; si mira el sensor en el estómago, la pluma baja con él.

#### 3.2.4 Confort visual: son objetos muy cerca de los ojos

| Regla | Valor por defecto | Cómo se cumple | Medido en el modelo (5 ciclos, giro de 30°, mirada al sensor, inclinación de 8 cm) |
|---|---|---|---|
| Nada cerca de los ojos | invisible a < 22 cm de la cámara, plena desde 36 cm (`NearMin`/`NearFull`) | alfa × smoothstep por distancia, con la cámara de **cada ojo** (`CameraPositionWS` en multiview) | mota visible más cercana a cualquiera de los dos ojos: **22,5 cm** (plano cercano ~10 cm) |
| Solo en la banda baja, nunca delante de los ojos | invisible por encima de −4° de la mirada, plena por debajo de −10° (`ElevMax`/`ElevSoft`) | alfa × smoothstep por elevación, con los ejes de la cabeza | elevación máxima de una mota visible: **−4,7°** |
| Diminutas | 0,22 cm (inhalar) y 0,28 cm creciendo ×1,8 (exhalar), con un **tope angular** de 0,40° / 0,55° (`MaxDeg`) | tamaño = clamp(tamaño físico, dist·ángulo mín., dist·ángulo máx.): lo cercano no se agranda | cobertura de pantalla: media **0,77 %**, máx. **1,45 %** |
| Suaves y de bajo contraste | alfa pico 0,45 / 0,50, disco gaussiano, colores cerca del tono del aire | en `MI_BreathAir_SC` | — |
| Sin destellos rápidos | lo que se mueve rápido se apaga (`SpeedFade` de 20 a 40°/s) | velocidad angular transversal **analítica** (tangente del camino × tasa que empuja el BP), sin estado | velocidad de las motas con alfa > 0,1, con la cabeza quieta: p50 0,7°/s, p90 5,8°/s, p99 **17,3°/s**. Las más rápidas (~45-50°/s) son pocas, salen de la boca y quedan con alfa ~0,1 |
| Sin saltos | cinta con fase integrada; el salto de la cinta ocurre con alfa 0 | frac(*e* + T) con T integrado en el BP | salto máx. de una mota visible entre cuadros: 2,2 cm (es el chorro al salir) |
| Sin vección | campo angosto (inhalar ±30° H, ±12° V; pluma de ±16°), solo en la banda baja, sin flujo radial que llene la periferia | geometría de los caminos | — |
| Que no parezca suciedad en el lente | el aire no está fijo a la vista: tiene retardo, se mueve con la respiración y se apaga en las pausas | §3.2.3 | retraso del marco en un giro rápido: hasta 24° |

Nota: la respiración sintética del modelo exhala con un pico de 2,3/s de velocidad de `S`. El seguidor real del rig (frenada física, `BreathFollowTime` 3 s) llega como máximo a ~1,33/s. Las velocidades medidas son **pesimistas**.

#### 3.2.5 Señales y mapeo exacto

Todo lo lee y lo integra el rig en `AirStep`, en el mismo cuadro. **Ninguna velocidad se modula en caliente:** se integran transportes (gotcha 329).

| Señal (rig) | Operación en el BP | Parámetro → material | Rango / curva | Filtro |
|---|---|---|---|---|
| `BreathFollowVel` = v (la derivada exacta de `Signed`, + inhala) | `Tin += TravelIn/2 · max(v, 0) · Dt` (frac) | fase de la cinta de inhalar | una inhalación completa (−1 → +1) avanza `TravelIn` = 0,9 caminos, **sea rápida o lenta**: el aire se mueve exactamente lo que se movió la respiración | ya viene del seguidor (≤ 3 s) |
| v | `Tout += TravelOut/2 · max(−v, 0) · Dt` (frac) | fase de la pluma | `TravelOut` 0,8 | idem |
| v | `Fout += FrontLead · ΔTout`; vuelve a 0 **solo cuando la pluma ya es invisible** (`Eout` < 0,01) | frente de la pluma: una mota se ve solo si su *s* < `Fout` (borde suave 0,08) | `FrontLead` 1,6: la pluma se despliega desde la boca un poco más rápido que sus motas | — |
| v, umbral `VOn` 0,05/s | envolventes `Ein`, `Eout` | alfa de cada corriente | inhala: `Ein` → 1 (τ 0,3 s). Quieto: → 0 (τ 2,5 s: **suspendidas**). Exhala: → 0 (τ 0,5 s). `Eout`, al revés | exponencial por cuadro |
| `BreathOn` | × todo | alfa global | 0-1 | el del rig (τ 0,5 s) |
| `CamRef` (pose) | boca exacta + marco con retardo | posiciones y ejes | §3.2.3 | τ 0,3 s (posición), τ 0,8 s (giro) |
| ritmo (período entre inicios de exhalación, EMA) | `RateCalm = lerp(FastFloor, 1, 1 − smoothstep(10, 16 resp/min, ritmo))` | × alfa global | `FastFloor` 0,5 | EMA de 2 ciclos |

**El `RateCalm`, medido en el modelo:** sin esta regla, respirar rápido da algo **más** aire visible. La suma media de alfa sube de 303 a 5 resp/min a 339 a 15 resp/min, porque la pluma se forma entera más seguido. Con la regla, lo rápido se ve más tenue: se premia la lentitud, no la amplitud ni la velocidad. Queda sin verificar en el visor.

**En el VS, por mota:**
- **Inhalar:** `s = frac(e + Tin)`; origen en el marco con retardo, sobre un eje 18° bajo la cabeza (`InTilt`), a 30-85 cm de la boca. Se reparte en una elipse de ±30° en horizontal y ±12° en vertical, con un leve remolino de 35° hasta llegar.
  - Posición = `lerp(origen, M + jitter, s^1,35)`: lento lejos, acelera al llegar, como un sumidero.
  - Alfa = entrada suave en s < 0,2 × reglas de confort × `Ein`.
- **Exhalar:** `s = frac(e + Tout)`; x(s) = 15 + 95·(1 − (1 − s)^1,8) cm, sobre un eje 12° bajo la cabeza (`OutTilt`). Es un chorro que frena: la condensación se ve desde ~15 cm de la boca, como el vaho real.
  - Radio del cono = 1,5 + x·tan 16°, aplanado ×0,6 en vertical.
  - Subida tibia de 10 cm·s²; turbulencia de 3 cm·s con fases de T. **En las pausas T no avanza, así que la turbulencia también se detiene.**
  - Alfa = frente × aparición (s 0,02-0,12) × salida (s 0,5-1) × reglas × `Eout`; tamaño ×(1 + 0,8·s).
- Colores: `InColor` lineal (0,80, 0,85, 1,00), frío, casi el tono de `SkyHorizon`. `OutColor` (1,00, 0,84, 0,80), tibio, el mismo tinte que toma la bruma en la exhalación (B).

#### 3.2.6 Perillas (dónde las ajusta Beltrán)

| Dónde | Perilla | Default | Qué cambia |
|---|---|---|---|
| Rig, `G - Aliento` | `bAir` / `AirAmount` | true / 1 | encendido / intensidad global (0 = apagado exacto, para el A/B del banco) |
| | `MouthDown` / `MouthFwd` | 9 / 6 cm | dónde está la boca respecto de la cámara |
| | `TravelIn` / `TravelOut` / `FrontLead` | 0,9 / 0,8 / 1,6 | cuánto viaja el aire por respiración; qué tan rápido se despliega la pluma |
| | `InTilt` / `OutTilt` | 18° / 12° | cuánto por debajo de la mirada va cada corriente (`OutTilt` más alto = la pluma pasa más abajo del metaball) |
| | `LagPos` / `LagRot` / `HoldLagMul` / `PitchFollow` | 0,3 s / 0,8 s / ×3 / 0,5 | cuánto "pesa" el aire al mover la cabeza |
| | `RiseTau` / `HoldTau` / `CrossTau` / `VOn` | 0,3 / 2,5 / 0,5 s / 0,05 | cómo aparece, cuánto queda suspendido, cómo se cruza inhalar con exhalar |
| | `FastFloor` | 0,5 | cuánto se apaga el aire con la respiración rápida |
| | `PreviewAirT` / `bPreviewAirCycle` | 0 / false | vista previa (§3.2.7) |
| `MI_BreathAir_SC` | `InSizeCm` / `OutSizeCm` / `OutGrow` / `MaxDeg` / `MaxDegOut` | 0,22 / 0,28 / 0,8 / 0,40° / 0,55° | tamaño |
| | `InAlpha` / `OutAlpha` / `InColor` / `OutColor` | 0,45 / 0,50 / frío / tibio | presencia y color |
| | `InNear` / `InFar` / `InSpreadH` / `InSpreadV` / `InAccel` / `InSwirl` | 30 / 85 cm / 30° / 12° / 1,35 / 35° | forma del volumen de la inhalación |
| | `PlumeLen` / `OutStart` / `OutDecel` / `OutSpread` / `OutFlat` / `Buoy` / `Turb` | 110 / 15 cm / 1,8 / 16° / 0,6 / 10 / 3 cm | forma de la pluma |
| | `NearMin` / `NearFull` / `ElevMax` / `ElevSoft` / `SpeedFade0` / `SpeedFade1` | 22 / 36 cm / −4° / 6° / 20 / 40°/s | **confort: no bajar sin probar en el visor** |

#### 3.2.7 Vista previa en el editor (Beltrán autora mirando)

- **Cabeza de referencia:** componente **`HeadGhost`** del rig, solo de editor, en los ojos del usuario sentado. Opcional: con una `CameraComponent` *editor-only* adentro; al seleccionar el rig, el recuadro de vista previa de la cámara muestra lo que ve el usuario. Verificar que no robe la vista en PIE.
  - Sin pawn montado, `PreviewAir` usa `HeadGhost` como cámara y como boca.
- **Congelado:**
  - `PreviewBreath` del rig (el mismo que ya mueve al metaball) elige la corriente: > 0 muestra la inhalación con `Ein = PreviewBreath`; < 0, la pluma con `Eout = −PreviewBreath`.
  - `PreviewAirT` (0-1) arrastra la cinta y el frente, como se arrastra el `T` del pacer.
- **Ciclo animado (fase 2, opcional):** con `bPreviewAirCycle` y Realtime, el VS calcula una respiración sintética 4-3-4-3 en forma cerrada desde `View.GameTime`. Es una rama uniforme apagada en juego, ~30 op por vértice solo cuando está encendida.
- **PIE:** `bFakeBreath` del rig (ya existe). Para probar el giro sin visor se puede rotar la cámara del pawn por `set_properties`, como la receta de la gotcha 469 con los grips.

#### 3.2.8 Costo

| Parte | Cuenta | Estimado |
|---|---|---|
| VS | 2048 quads × 4 vértices × 2 vistas × ~250 op-eq = 4,1 M op-eq | **0,023-0,045 ms** |
| PS | cobertura media 0,77 % (máx. 1,45 %) × ~20 op-eq × 2 (translúcido) × ~3 (ineficiencia de quads chicos) | **≤ 0,01 ms** |
| CPU | `AirStep` (unas 40 operaciones) + `PushAir` (7 vectores a un MID) | < 0,05 ms |
| Triángulos | 4096 por vista | ~0,3 % de la guía de Meta |

**Medición:**
- `AirAmount` 0 y el componente oculto dan el A/B exacto para el banco (un modo nuevo en `BP_PerfEntering_SC`), ida y vuelta, dos pasadas, normalizado por MHz.
- Si aprieta, la primera palanca es bajar a 1024 quads.

#### 3.2.9 Riesgos del aliento

| Riesgo | Mitigación |
|---|---|
| Se ve como "partículas de videojuego" y no como aire | Tamaño y contraste bajos por defecto. La prueba de verdad es el visor: primero con alfa 0,3 y después subir |
| Tapa o ensucia el panel de instrucciones en `StagePractice` (sort 20 > HUD 0) | El panel está a la altura de los ojos y el aire por debajo de −4°: no deberían cruzarse. Verificar en el visor; si pasa, bajar `AirAmount` mientras el panel está abierto |
| La pluma compite con el metaball (llega a su pie, ver la imagen) | `OutTilt` 16-20° la baja; `PlumeLen` 90 la acorta |
| El umbral de detección parpadea (`On` entra y sale) y el aire con él | `On` ya viene suavizado (τ 0,5 s) y el umbral tiene debounce de 1,5 s / 0,2 s |
| Mareo por las motas cercanas | Las reglas de §3.2.4 y un botón de pánico: `AirAmount` en la instancia |
| La instancia colocada no hereda el componente | Gotcha 478: diff instancia contra plantilla; sort y límites también desde el CS |

### 3.3 B, C, D — Las capas sutiles del valle

#### 3.3.1 Una sola tubería, cero GPU: el BP empuja, el material no cambia

- **Recomendado:** una función **`StepLive`** en `BP_BreathValley_SC`, en el Tick, junto a `StepShadow`. Hace tres cosas:
  1. Lee `MPC_Breath.Signed` y `On` con `GetScalarParameterValue` de colección (gotcha 291).
  2. Calcula `S = Signed · saturate(On · LiveAmount)`.
  3. Escribe **Ground y Sky en la misma función y el mismo cuadro**, porque la niebla del suelo usa los `Sky*`/`Glow*` del cielo (gotcha 465, costura del horizonte).
- **Base:**
  - Los valores base se leen de la MI al arrancar, y la respiración multiplica encima: no pisa lo que autoró Beltrán.
  - Todas las ganancias nuevas nacen en 0: con 0, el valle queda idéntico.
  - Van en el CDO **y** en la instancia (gotchas 420, 435, 478).
- **Vista previa:** una perilla propia `PreviewBreath` en el valle (−1 a +1). Su Construction Script empuja los valores modulados, así el valle respira en el viewport sin Play. Con 0 no empuja nada y la MI se ve tal cual.
- **Por qué no leer el MPC dentro de `M_BreathValley_SC`:**
  - Verificado en el código del motor: `HLSLMaterialTranslator.cpp:5056-5076` compila la lectura de una colección como **código del shader** (`MaterialCollection%u.Vectors[%u]`), no como uniforme de *preshader*.
  - Las ~9 modulaciones correrían en cada píxel del valle: ~30-55 op-eq a pantalla completa, **~0,2-0,4 ms** estimados.
  - Obligarían además a pasar por el circuito entero del HLSL (`plan_valley_material.py` → apply → `Valley_check.py` → three.js).
  - El empuje desde el BP cuesta 0 de GPU y no toca el HLSL.
- **Curva de la casa:** `m(S) = 1 + S·lerp(−Out, In, smoothstep((S+1)/2))`. Con S = +1, m = 1 + In; con S = −1, m = 1 + Out.

#### 3.3.2 Mapeo

| Efecto | Parámetro | In (S = +1) | Out (S = −1) | Resultado (inhala / base / exhala) |
|---|---|---|---|---|
| **B — la bruma respira** | `FogDist` × m | +0,20 | −0,15 | 54000 / 45000 / 38250 |
| | `HFogDist` × m | +0,20 | −0,15 | 72000 / 60000 / 51000 |
| | `HFogFall` × m (la bruma baja sube al exhalar) | −0,10 | +0,35 | 1350 / 1500 / 2025 |
| | `SkyHorizon` → lerp hacia `BreathWarm`, `WarmAmt`·saturate(−S) | — | `WarmAmt` 0,25 | `BreathWarm` = (0,80, 0,57, 0,71) lineal, **misma luma** que `SkyHorizon`: calienta sin aclarar |
| **C — el resplandor inhala** | `GlowAmt` × m | +0,15 | −0,25 | 0,92 / 0,80 / 0,60 |
| | `GlowPow` × m (más angosto al inhalar) | +0,15 | −0,25 | 2,3 / 2,0 / 1,5 |
| | `GlowHeight` × m (la banda se mueve ≤ 1°) | +0,05 | −0,05 | 0,47 / 0,45 / 0,43 |
| **D — la sombra respira** | `ShadowRadius` × m (sobre lo que ya empuja `StepShadow`) | −0,10 | +0,35 | 76 / 85 / 115 cm |
| | `ShadowSoft` × m | −0,20 | +0,45 | 0,64 / 0,80 / 1,16 |
| | `ShadowStrength` × m | +0,07 | −0,25 | 1,61 / 1,50 / 1,13 |
| | `ShadowTint` → lerp hacia un tinte tibio, 0,5·saturate(−S) | — | 0,5 | (0,43, 0,39, 0,59) al exhalar |

- **Fijos:**
  - `FogMax` no se toca (≤ 0,9, contraste del metaball).
  - `FogStart` no se toca: mueve una rama y cuesta 0,06-0,4 ms.
  - Nada de geometría.
- **Filtro:** ninguno extra. `Signed` ya viene del seguidor (arranca en ~0,15 s y llega en ≤ 3 s).

**Medido en los renders** (vista del usuario, del pico de la inhalación al de la exhalación; niveles de 8 bits):

| Región | Cambio medio | p90 |
|---|---|---|
| Horizonte y colinas | 5,8 | 11,7 |
| Tinte R−B | +4 hacia lo tibio | — |
| Cielo alto | 2 | — |
| Piso medio | 0,6 | — |
| Piso cercano | 3 | — (es la sombra) |

- La luma del horizonte sube solo 3 niveles al exhalar, así que no lava al metaball.
- Es **sutil a propósito**: el canal legible es el aliento. Si en el visor no se percibe, se suben las ganancias. Blum 2020 muestra que un cambio de color del entorno alcanza.

### 3.4 Comportamiento de la primera tanda por situación

| Situación | Aliento (A) | Bruma y resplandor (B, C) | Sombra (D) |
|---|---|---|---|
| **Inhala** | motas frías fluyen hacia la boca; aceleran al llegar y se apagan antes | se abre / sube y se afina | se recoge, más densa |
| **Retiene** (3 s en 4-3-4-3) | suspendidas, se apagan en ~2,5 s; nada se mueve | quieto en el valor de la inhalación | quieta |
| **Exhala** | la pluma tibia sale de la boca en ~0,3 s, frena, se abre, sube apenas, se apaga hacia 1,1 m | se cierra y entibia / baja y se abre | se abre, ablanda y entibia |
| **Pausa** | la pluma suspendida se desvanece | quieto | quieta |
| **Sin detección** (`On` → 0) | apagado (capa A: decisión 2) | vuelve a lo autoral | vuelve a lo autoral |
| **Respiración rápida** (> 10-16 resp/min) | más tenue (`RateCalm`), las motas rápidas se apagan | igual, con menos tiempo por fase | igual |
| **Gira la cabeza** | lo inhalado sigue entrando a la boca actual; la nube de adelante llega ~1 s después | — | — |
| **Mira el sensor** (pitch −35°) | el aire baja con la mirada (×0,5); nada sube a la vista | — | — |

### 3.5 Costo total de la primera tanda

| Pieza | GPU | CPU |
|---|---|---|
| A — aliento | 0,03-0,06 ms | < 0,05 ms |
| B + C + D — empuje desde el BP | 0 | < 0,05 ms (~12 parámetros × 2 MIDs) |
| **Total** | **≈ 0,03-0,06 ms** (≤ 0,1 con margen) | **< 0,1 ms** |

Contra el margen: la etapa mide 9,43 ms sin fondo. El valle se estima en 1,2-2,5 ms **sin medir**, así que quedan ~1-3 ms. La primera tanda cabe incluso en el peor caso del valle, pero **se mide el valle primero**.

### 3.6 Orden de construcción y verificación

1. **Medir el valle** (`PerfValley0..3`, ida y vuelta, dos pasadas). Es un prerrequisito, no forma parte de esta propuesta.
2. **D (sombra) + la tubería `StepLive`** (1-3 h). Es lo más barato y lo más legible, y valida la lectura del MPC y el empuje a Ground/Sky.
   - PIE con `bFakeBreath`.
   - Captura del **recorte de la sombra**, no del cuadro, en tres estados.
3. **B + C** sobre la misma tubería (2-3 h). Controlar que con `PreviewBreath` 0 el valle quede idéntico, y buscar costura en el horizonte.
4. **A — aliento** (14-20 h):
   1. Portar `air_model.py` a HLSL y agregar un chequeo numérico, como `Valley_check.py`: valores de control del modelo contra el shader.
   2. Generar la malla y el material.
   3. Componente, `MountAir`, `AirStep`, `PushAir` y `PreviewAir` en el rig. Leer el tracker del rig antes y actualizarlo después.
   4. Viewport con `PreviewAirT` y `HeadGhost`.
   5. PIE con `bFakeBreath` y la cámara girada por `set_properties`.
   6. **Controles:** positivo, `AirAmount` 1 se ve; negativo, `AirAmount` 0 no dibuja nada y el banco da la misma cifra que sin componente.
5. **Banco:** modo nuevo `PerfAir` en `BP_PerfEntering_SC`.
6. **Visor con Beltrán, capa por capa:** primero solo el aliento, después la sombra, después la bruma y el resplandor. Una capa entra cuando la anterior se lee viva sin distraer.

---

## 4. Segunda tanda (opcional, en este orden)

| Orden | Efecto | Qué hace | Mapeo y técnica | Costo | Nota |
|---|---|---|---|---|---|
| 1 | **E — el mundo contiene el aire** | en las pausas se detienen también la luz que viaja por el llano y el oleaje lejano; retoman con la inhalación | reloj del valle integrado: `ValleyLag += Dt·(1 − Rate)`, con `Rate` ≤ 1 (0,15 en las pausas, rampa τ ~1 s); `View.GameTime − ValleyLag` en los dos VS. **Frenar nunca acelera**: la cota de 0,451°/s se mantiene | ~0 | Toca la firma de los Custom: circuito completo del plan del valle. Solo se ve en PIE y en el visor |
| 1 | **F — el aire suena** | pasabajos del ambiente (se cierra al exhalar), hálito de viento durante la exhalación (ganancia por **duración**, no por amplitud), casi silencio en las pausas | MetaSound con `Set Float Parameter` por cuadro | 0 GPU | Mover el bloque de audio de `DefaultEngine.ini` a `[AndroidRuntimeSettings]` toca Config compartida: coordinar. Convivir con los `SND_Pacer*` |
| 2 | **G — el eco llega al horizonte** | al exhalar, una franja de luz tenue nace a 45 m y viaja hacia las colinas mientras dure la exhalación. Continúa la pluma: *el aliento llega al horizonte* | gaussiana radial en la rama lejana de `ValleyPS`, radio a velocidad **angular** constante ≤ 0,45°/s; 2 franjas como uniformes sueltos, sin arreglos | 0,04-0,1 ms | Verificar la velocidad angular con el script de confort antes del visor |
| 3 | **H + I — coherencia, paleta y luna** | respirar con el pacer aclara el aire y lleva la paleta de lavanda a rosa-fucsia en minutos (Aten Reign); la luna se llena y nunca retrocede | `Sync` = correlación exponencial (τ 1 ciclo) entre el pulmón del pacer y `BreathNorm`, calculada en `BP_BreathStage_SC` (el único que ve rig y pacer); se validan en PIE los casos en fase, en antifase y a otro ritmo | 0 | Premia ritmo, no amplitud; nunca castiga. Resolver antes el ritmo real de Entering en la instancia (4-3-4-3 según GUION V4; 6-0-6-0 según el tracker de la etapa) |
| 4 | **J — el valle emerge** | a lo largo de la etapa, la bruma de base se aclara: arranca cerca del Ganzfeld (el color del velo) y termina con el valle entero | `Charge` monótono en el BP, con piso autoral por tiempo | 0 | Encaja con la transición del velo (GUION V4 §6) |
| 5 | **K — el aire lejano** | motas de 2-12 m que solo se ven dentro del resplandor; dan el paralaje que pide OBRA §6.b | **tercera corriente de la MISMA malla** del aliento (no un sistema nuevo); deriva lenta, brillo por la exhalación | 0,05-0,12 ms | Solo si el aliento funciona y falta profundidad. Nada de flujo radial coherente |
| — | M, N, L | háptica al final de una exhalación larga · vaho de pocos sprites grandes en la pluma · `SwellShade`/`Sheen` más fuertes al exhalar | ver la tabla de §2 | ~0-0,05 ms | Probar en el visor. El vaho arriesga "mancha en el lente" |
| — | Capa A del aliento | sin respiración detectada, el aire sigue al pacer, tenue (0,3) | `lerp(pacer, usuario, saturate(On·G))`; `BreathStage` pasa el pulmón del pacer al rig | ~0 | Decisión 2 |

---

## 5. Descartados, y por qué

| Descartado | Por qué |
|---|---|
| Humo con ruido fbm, a pantalla completa | 1,2-7 ms. El precedente medido, el fondo líquido, costó 14 ms y se rechazó |
| Planos translúcidos, `FogSlab`, losas de niebla apiladas | 0,15-0,7 ms por capa + sobredibujo en una GPU fill-rate bound; `DepthFade` sin validar en el APK y ciego al metaball (gotchas 276/283) |
| Ganzfeld fluido | Medido: 14-17 ms en Entering |
| Local Fog Volumes | Sin medir en móvil; queda para una prueba aislada, no para esta tanda |
| Geometría del valle al ritmo de la respiración (`SwellAmp`, `MorphAmt`, `HillAmp`) | Medido por el verificador de confort: 0,94-4,13°/s contra una cota de 0,5°/s, en la banda de más mareo (0,2-0,4 Hz) |
| `SwellSpeed` / `MorphSpeed` en caliente | Saltos de fase (gotcha 329) |
| `FogStart` variable | Mueve una rama (0,06-0,4 ms) y un borde de luminancia sobre el piso cercano |
| Post-proceso (viñeta, bloom, LUT) | No existe en el APK con `MobileHDR=False`; encenderlo cambia el color de toda la obra |
| El horizonte se acerca / escala del mundo | Flujo de expansión de campo completo: vección adelante-atrás |
| Túnel (`RingTunnel`) | OBRA §6: Entering es estático, nada de túnel |
| Campos aditivos a pantalla completa (`VoidField`, `LineField`) y campos que giran | Fill-rate, titileo y vección por giro |
| Motas que se aspiran desde todo el campo (flujo radial coherente) | Vección. El aliento lo evita con un campo angosto y bajo |
| Partículas fijas a la vista (head-locked, sin retardo) | Se leen como suciedad en el lente. Por eso el marco con retardo |
| Chorro de luz continuo desde la boca (cinta, tipo TRIPP) | Demasiado literal; una cinta cerca de la cara es un objeto grande en estéreo y se lee como láser o HUD |
| El aliento que viaja 3,8 m y "entra" al metaball | Cruzaría el proxy del metaball (orden de translúcidos: se pintaría encima de su cuerpo aunque esté "adentro") y sería un flujo coherente en el centro de la vista. La pluma **apunta** al pie del alma y se apaga antes |
| Niagara para el aliento | Posible (plan B), pero sin vista previa con `PreviewBreath`, sin nada validado en el visor y con trampas en Android. La malla de quads está probada (Loving) |
| Jirones de humo pintados en `ValleyPS` | 0,1-0,3 ms; el aliento ya responde al pedido de "humo o partículas"; se leen "pintados" cerca. Por ahora no |
| Premiar la amplitud, puntajes, castigos (desenfocar si se pierde el ritmo) | Empuja a sobre-respirar y a jugar la mecánica (Lehrer; Prpa, participantes 13 y 15). Life Tree: el desenfoque se lee como castigo |
| Leer `MPC_Breath` dentro del material del valle | Es ALU por píxel (ver §3.3.1), ~0,2-0,4 ms estimados; el empuje desde el BP da lo mismo por 0 ms |
| Agregar escalares a `MPC_Breath` en esta tanda | Es compartido y recompila todo lo que lo usa; la primera tanda no lo necesita |

---

## 6. Previsualizaciones (sin Unreal)

Carpeta: `VR_Test/Saved/ClaudeScripts/ideas_respiracion/`.

| Imagen | Qué muestra |
|---|---|
| **`concepto_inhala_exhala.png`** | Fila 1: reposo · inhala (2,6 s de 4) · exhala (3,2 s de 4) · mapa de dónde cambia el valle entre inhalar y exhalar (×10). Fila 2: recortes ×2 de la banda baja con las motas (inhalar y exhalar) |
| **`ciclo_aliento_8_instantes.png`** | La banda baja en 8 instantes de un ciclo 4-3-4-3: inhala 1,0 / 2,5 s, fin de la inhalación, retiene 2 s, exhala 1,0 / 2,5 s, fin de la exhalación, pausa 2 s. Cada cuadro trae S, `Ein`, `Eout` y el frente |
| **`geometria_aliento.png`** | De lado y en planta (cm): los caminos de inhalar (azul) y exhalar (rojo), en trazo grueso la parte visible. Los límites de confort: 22 y 36 cm, −4° y −10° de elevación, borde del campo. Tercer panel: un giro de 30° de la cabeza, con el marco del aire atrasado y las motas que igual llegan a la boca |

**Cómo se hicieron:**
- El valle es el render de Blender headless de `preview_breath_valley.py`, a través del envoltorio `render_valle_respira.py`, que no modifica el original.
  - Actor en Z −90,4, como en el nivel.
  - Las perillas de la tabla de §3.3.2 en sus extremos: inhala = S +1, exhala = S −1.
- Las motas las dibuja `sim_air.py` con el modelo `air_model.py`: se proyectan con la cámara exacta del render, en su tamaño angular real, compuestas en lineal y premultiplicadas.

**Qué NO muestran:**
- El metaball real: la esfera blanca es la de referencia del preview. No se reúne ni se dispersa.
- El movimiento: son cuadros quietos, así que la convergencia hacia la boca y la pluma que sale se leen mucho mejor en movimiento.
- El estéreo ni el tamaño en el visor: el render tiene ~9 px/° y la Quest ~20-25.
- La pausa de la segunda tanda (el valle quieto).
- **El juicio fino es del visor.**

**Otros archivos de la carpeta:**
- `sim_air_resultados.txt`: los números de §3.2.4.
- `preview_valle_t0_{neutro,inhala,exhala}.png`: los renders del valle sin motas.

---

## 7. Números medidos en el modelo (no en la Quest)

5 ciclos 4-3-4-3 a 72 Hz, con balanceo natural de la cabeza, un giro de 30° en 0,6 s en plena inhalación, una mirada al sensor (pitch −35°) en plena exhalación y una inclinación de 8 cm hacia adelante.

| Medida | Valor |
|---|---|
| Mota visible (alfa > 0,02) más cercana a un ojo | 22,5 cm |
| Elevación máxima de una mota visible | −4,7° de la mirada |
| Motas visibles en el campo | media 839, máx. 1612 (inhalar ≤ 626, exhalar ≤ 1160) |
| Cobertura de pantalla (25 px/°) | media 0,77 %, máx. 1,45 % |
| Velocidad angular de las motas visibles (cabeza quieta) | p50 0,6 · p90 5,6 · p99 17,7 · máx. 49,7 °/s (las más rápidas con alfa ~0,1) |
| Latencia inhalar: 20 motas con alfa > 0,1 | 0,36 s desde el inicio de la inhalación del usuario |
| Latencia exhalar: 20 / 150 motas con alfa > 0,1 | 0,29 / 0,35 s |
| Retraso máximo del marco del aire en el giro | 23,9° |
| Salto máximo de una mota visible entre cuadros | 2,2 cm |
| Suma de alfa visible: 5 / 4,3 / 10 / 15 / 20 resp/min (sin `RateCalm`) | 303 / 230 / 318 / 339 / 343 |

---

## 8. Decisiones para Beltrán

1. **¿Dónde vive el aliento?**
   - Recomendado: **dentro de `BP_BreathRig_SC`**, como los mandos (§3.2.1).
   - Alternativa: un actor `BP_BreathAir_SC` que el rig engancha.
2. **¿Qué pasa si no se detecta la respiración?**
   - Recomendado para la primera prueba: **nada** (el aire es solo capa viva).
   - Alternativa: capa A, el aire sigue al pacer, tenue.
3. **¿A dónde apunta la pluma?**
   - Hoy llega al pie del metaball ("tu aliento va hacia el alma").
   - Alternativa: más baja, sin tocarlo (`OutTilt` 16-20°).
4. **¿Las capas del valle entran de a una** (sombra en el ciclo 1, bruma y resplandor en el 2) **o todas desde `StagePractice`?**
5. **Colores:** frío entra / tibio sale (propuesto), o un solo color.
6. **Orden de la segunda tanda:** propuesto pausas y sonido primero; el sonido requiere coordinar Config compartida.

---

## Fuentes principales

- Blum, Rockstroh y Göritz 2020 (N = 72): color del entorno atado a la exhalación, sin HUD: de 11 a 8 resp/min. https://link.springer.com/article/10.1007/s10484-020-09468-x
- Prpa et al. 2018, *Attending to Breath* (DIS): descubrir el control quita la ansiedad; el movimiento vertical marea; estímulos de a uno. https://doi.org/10.1145/3196709.3196765
- Patibanda et al. 2017, *Life Tree* (CHI PLAY): feedback imitativo, minimal, sin métricas; el desenfoque se lee como castigo.
- Chittaro 2024 (IJHCS): el biofeedback real le gana al placebo en relajación y presencia. https://www.sciencedirect.com/science/article/pii/S1071581924000594
- Char Davies, *Osmose* (1995): 15 min, flotar con la respiración, premio a la suavidad. https://www.immersence.com/osmose/
- Marshmallow Laser Feast, *We Live in an Ocean of Air* (2019): la exhalación hecha visible.
- Wen 2019: el juicio causal aguanta demoras de segundos. https://pubmed.ncbi.nlm.nih.gov/31173998/
- Diels y Howarth 2013: pico de mareo visual entre 0,2 y 0,4 Hz. https://journals.sagepub.com/doi/10.1177/0018720812469046
- Bernardi 2006: las pausas de silencio relajan más que la música lenta. https://pubmed.ncbi.nlm.nih.gov/16199412/
- Proyecto:
  - `docs/OBRA-SOUL-CHARGER.md` §2.1 y §6; `docs/GUION-V4-2026-09-28.md` (acto 5); `docs/PLAN-VALLE-ENTERING-2026-09-27.md` (§7.1, §11, §14.3).
  - Trackers `BP_BreathRig_SC`, `BP_BreathValley_SC`, `BP_BreathBlob_SC`, `BP_Pacer_SC`, `BP_LovingCell_SC`.
  - Gotchas 239, 291, 329, 399, 465, 469, 477 y 478; `references/niagara-quest.md`, `references/vr-pawn.md`.
  - Motor: `HLSLMaterialTranslator.cpp:5056-5076` (UE 5.8).
