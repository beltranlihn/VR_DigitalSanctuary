# PLAN DE IMPLEMENTACIÓN — La respiración maneja el entorno de Entering (primera tanda) · 2026-09-28 · rev. 2

> **Estado:** plan listo para el editor. **Todo lo que no necesita Unreal está HECHO y VERIFICADO en disco** (§13). Lo que necesita el editor es la **receta de la §11**, paso a paso, con la verificación de cada paso. Nada se tocó en Unreal ni en ningún `.uasset`; nada se commiteó.
>
> **Viene de:** [`IDEAS-RESPIRACION-ENTORNO-2026-09-28.md`](IDEAS-RESPIRACION-ENTORNO-2026-09-28.md) (la síntesis de la propuesta) y la **directiva de Beltrán**: el efecto primario es **el aliento visible**, *"cuando inhalas entren partículas muy pequeñitas y suaves y cuando exhales que salgan partículas de tu boca… attached a la cabeza del pawn para que si muevo la cabeza sigan entrando a mi boca"*.
>
> **Rev. 2 (misma tarde):** corrige lo que encontraron las dos revisiones (código; costo y confort). Lo más importante: las semillas de la malla ahora resisten la V invertida del importador FBX; el aire distingue inhalar/exhalar/pausa con **histéresis** y un filtro, así la pausa queda quieta con el ruido real del sensor; el ritmo se mide bien (latch); nada salta cuando el rig se retira; el aire se apaga mientras la cabeza gira; la inhalación converge hacia un **foco visible** y ya no se lee como algo que cae; la pluma pasa por debajo del metaball; la sombra del metaball respira **en densidad**, sin mover el piso; el valle se midió con el **look actual** (las perillas de `ApplyLook`). La tabla completa de qué cambió está en la §15.
>
> **Números:** los que dicen *modelo* salen de la simulación de la cadena completa (rig → `MPC_Breath` → Blueprint → vertex shader), no de la Quest. Los costos de GPU son **estimados** y se miden (§8).

---

## 0. Resumen en un minuto

- **Qué se construye (tanda 1):**
  - 🔴 **A — El aliento visible** (primario): al inhalar, motas diminutas y frías aparecen en el aire de adelante, en la parte baja de la vista, **se juntan de costado hacia un foco** a ~40 cm y desde ahí bajan a la boca, apagándose antes de llegar. Al exhalar, una pluma tibia sale de la boca, frena, se abre y se apaga hacia 1,1 m, **por debajo del metaball**. En las pausas todo queda suspendido y se desvanece, **quieto aunque el sensor tenga ruido**. Anclado a la cámara del pawn: lo inhalado entra siempre a la boca **actual**. Si la cabeza gira, el aire se apaga y reaparece en su lugar en ~1 s.
  - **B, C, D — La capa viva del valle** (sutiles): la bruma se abre al inhalar y se cierra y entibia al exhalar; el resplandor rosa sube al inhalar y baja al exhalar; la sombra del metaball se hace más densa al inhalar y se ablanda al exhalar **sin moverse**. **Ninguna geometría respira**, tampoco el borde de la sombra ni la altura del resplandor.
- **Arquitectura (decidida, §2):**
  - Aliento = **actor nuevo `BP_BreathAir_SC`** que toma la cámara de `BP_BreathRig_SC.CamRef` y lee solo `MPC_Breath`. **El rig (validado en visor) no se toca.** Malla de 2048 quads + HLSL propio (receta de Loving): un draw call, cero CPU por mota.
  - Valle = el material recibe 9 entradas por **preshader** (`Mul`/`Mix`/`Tint` de parámetros: 0 por píxel) y el BP empuja 9 multiplicadores `Live*` desde `MPC_Breath`, **suavizados**. **El HLSL del valle no cambia**; con los `Live*` neutros el valle es la v2 **bit a bit** (y con el look actual, 0 píxeles distintos).
- **Costo estimado:** aliento 0,025-0,05 ms de GPU (≤ 0,1 si Unreal duplica el VS); valle 0 (≤ 0,1 si el preshader no pliega). CPU (Blueprint) 0,15-0,3 ms, sin medir (el banco reporta una señal gruesa).
- **Hecho y verificado en disco:** HLSL del aliento (compila dxc/fxc/SPIR-V, = modelo, V invertida probada), malla FBX regenerada, planes de armado de los dos materiales + scripts de aplicación (probados contra un editor simulado, también el rollback), DSL de todos los grafos nuevos (ejecutado por un intérprete, = modelo en 5184 cuadros y con ruido real), extensión del circuito del valle (`Valley_check.py` 90/90), previsualizaciones del valle con el look actual y del aliento.
- **Qué falta (editor, §11):** ~2 h 15 min de receta. Después: APK, banco (`quest_entering_perf.ps1 -Modos 0,4,5,6`) y visor con Beltrán (incluye medir el ruido real de la señal con `ke * AirDbg`).
- **Decisiones para Beltrán (§14):** el aliento como actor propio (recomendado) o dentro del rig; sin detección, nada (recomendado); la pluma por debajo del metaball (nuevo default) o hacia él; si las capas del valle entran de a una; cuánto sigue el aire a la mirada hacia abajo.

---

## 1. Objetivo, alcance y reglas

**Objetivo:** que el biofeedback se sienta en el cuerpo y en el espacio, no solo en el metaball: *un solo aire* en tres escalas (la boca, el alma, el horizonte), con el cuerpo mandando y el mundo haciendo eco.

**Tanda 1 (este plan):** A (aliento visible) + B/C/D (capa viva del valle). **Tanda 2** (opcional, §12).

**Reglas que el plan cumple por construcción:**
- **Una función nueva no degrada una aprobada.** El rig no se toca. El valle con los parámetros nuevos en su neutro es la v2 exacta (verificado: `Valley_check.py`; render neutro con el look actual = 0 píxeles distintos; script de armado simulado). El metaball, el pacer, la etapa y la instancia `Entering_Valle` no se tocan.
- **Capa autoral + capa viva:** el aire y los `Live*` son capa viva pura: con `On` = 0 (sin respiración detectada) todo vuelve, suave, a lo autoral.
- **Confort (verificador del valle):** nada de geometría a la frecuencia de la respiración; el piso cercano quieto (el borde de la sombra se mueve ≤ 0,45°/s); las motas nunca delante de los ojos (§4.3).
- **No se premia la amplitud:** todo sale de `Signed` normalizado por el rig; respirar rápido **apaga** un poco el aire (`RateCalm`), sin castigar la respiración lenta con retenciones (§4.5).
- **Sin HUD ni puntaje.**
- **Nada salta de un cuadro a otro** (memoria del chispazo de la membrana): un escalón de la señal (el `Retire` del rig) se filtra en el aire (`GlobTau`, tope de velocidad) y en el valle (`LiveTau`).

---

## 2. Arquitectura: quién lee cada señal y quién escribe cada parámetro

```
 BP_BreathRig_SC  (SIN CAMBIOS)
   motor de umbral + NormRange + FollowBreath (frenada física, 3 s)
   ├── escribe MPC_Breath.Signed  (−1 exhalado … +1 inhalado, ya seguido)      ┐
   ├── escribe MPC_Breath.On      (0 … 1, detección con debounce)               │  lo único que cruza
   └── CamRef = la CameraComponent del pawn (lo encuentra en Acquire)          │  entre actores
                                                                                ┘
 BP_BreathAir_SC  (NUEVO, colocado)                  BP_BreathValley_SC  (+4 funciones, +2 nodos)
   AirMount: GetActorOfClass(rig) → CamRef             StepLive (Tick, después de StepShadow)
     → AirMesh.AttachComponentToComponent(CamRef,        LiveMPC: lee Signed, On
       SnapToTarget) + AddTickPrerequisite(rig)          S = seguidor(τ LiveTau) de clamp(Signed)·clamp(On·LiveAmount)
   AirTick (cada cuadro):                                PushLive(S): 9 Live* al suelo, 3 al cielo
     AirMPC: lee Signed, On                            PreviewLive (CS, al final, después de ApplyLook)
     AirStep: v filtrada, modo con histéresis,         ApplyLook (de OTRA sesión, 16:00): 36 perillas de look
              transporte, envolventes, ritmo (latch),      instance-editable → MIDs (FogDist, GlowAmt, SkyHorizon…)
              marco con retardo, apagado por giro,     M_BreathValley_SC
              presencia suavizada                        9 entradas de ValleyPS = Mul / Mix / Tint de
     PushAir: 8 vectores en local de la cámara           parámetro × Live* (PRESHADER: en la CPU), el HLSL no cambia
   M_BreathAir_SC
     BreathAirVS: cada mota sin estado
     BreathAirPS: punto suave premultiplicado
```

| Señal / parámetro | La produce | La lee | Dónde |
|---|---|---|---|
| `MPC_Breath.Signed`, `On` | rig (`PushMPC`, sin cambios) | aire (`AirMPC`), valle (`LiveMPC`), metaball (ya) | colección de material |
| `CamRef` | rig (`Acquire`) | aire (`AirMountCam`), una vez | variable del rig (`Class\|BPBreathRigSC\|GetCamRef`) |
| `AirT`, `AirE`, `MouthL`, `LagM`, `LagA`, `LagR`, `LagU`, `UpL` | aire (`PushAir`, una función, el mismo cuadro: gotcha 465) | `BreathAirVS` | MID de `AirMesh` |
| look del valle (`FogDist`, `GlowAmt`, `SkyHorizon`…) | valle (`ApplyLook`, perillas instance-editable de la instancia) | preshader | MIDs de `Ground` y `Sky` |
| `Live*` (9) | valle (`PushLive`: 9 al suelo, 3 al cielo, misma función) | preshader de `M_BreathValley_SC` | MIDs de `Ground` y `Sky` |

### 2.1 Decisión: el valle respira por PRESHADER + multiplicadores empujados por el BP

| Opción | GPU | Claridad / riesgo | Veredicto |
|---|---|---|---|
| El material lee `MPC_Breath` y calcula las curvas | ~0,2-0,4 ms estimados: la lectura de una colección compila como **código de shader** (`HLSLMaterialTranslator.cpp:5056-5076`), no como preshader; ~9 curvas por píxel | cero BP, pero toca el HLSL y todo el circuito del valle; las curvas no se ven en el BP | ❌ |
| El BP lee los valores base y empuja los valores absolutos | 0 | hay que leer las bases (hoy vienen de `ApplyLook` o de la MI según el parámetro), quedan viejas si Beltrán mueve una perilla en PIE, y compite con `ApplyLook` por los mismos parámetros | posible, más frágil |
| ✅ **El material multiplica/mezcla/tiñe por `Live*`; el BP solo empuja los `Live*`** | **0** (Mul/Add/Sub de uniformes = `FMaterialUniformExpressionFoldedMath`, se evalúa en la CPU) | **el look lo sigue poniendo quien lo pone hoy** (las perillas del BP vía `ApplyLook`; lo que `ApplyLook` no empuja, la MI); los `Live*` son parámetros **distintos**, así que `ApplyLook` y `PushLive` no se pisan y el orden no importa; con `Live*` neutros el valle es la v2 bit a bit; el HLSL no cambia (solo 9 fuentes en la cabecera) | ✅ **elegida** |

- Si el preshader NO plegara (no esperado), serían ~15 ALU por píxel ≈ 0,05-0,1 ms: se detecta en el banco (§8) y en las estadísticas del material (paso V3).
- Las curvas (`In`/`Out` por parámetro) quedan en el BP, en **una** función (`PushLive`), con 4 perillas de familia (`FogBreath`, `GlowBreath`, `ShadowBreath`, `WarmBreath`).
- El tibio del horizonte es un **tinte relativo** (`Tint`: `SkyHorizon × (1 + (BreathTint − 1) × LiveWarm)`), no un color fijo: `SkyHorizon` ahora es una perilla del BP y el tibio la sigue si Beltrán la cambia.

### 2.2 Decisión: el aliento es un actor propio, no una parte del rig

| | Dentro del rig (propuesta original) | ✅ Actor propio `BP_BreathAir_SC` |
|---|---|---|
| Riesgo sobre lo aprobado | toca el rig validado en visor: componente nuevo (gotcha 478: llega pelado a la instancia colocada), cirugía en su Tick y su CS, variables en categorías con espacios (gotcha 466) | **el rig no se toca** |
| Construcción | cirugía de grafos existentes | BP nuevo: **todos los grafos se escriben con DSL en vacío**, se coloca después de crear variables y componentes (nada nace pelado) |
| Quién conoce al pawn | el rig | sigue siendo **solo el rig**: el aire le pide `CamRef` |
| Portabilidad | viaja con el rig | un actor más en el nivel (queda en `MECANICAS-PORTABLES.md`) |
| Rollback | revertir el rig | ocultar o borrar un actor |

- Si Beltrán prefiere que viva dentro del rig, las funciones se trasladan tal cual (decisión 1, §14).

### 2.3 El aire en el espacio de la cámara

- `AirMesh` cuelga de la cámara con `SnapToTarget`: su local **es** el de la cámara (X adelante, Z arriba de la cabeza). La boca exacta es una constante local (`MouthFwd`, 0, −`MouthDown`) y el late update del visor la mueve junto con la vista.
- **Qué vive en la cabeza y qué en el mundo:**

| Parte | Marco | Por qué |
|---|---|---|
| Destino de lo inhalado, origen de la pluma | **boca exacta** (cabeza) | lo inhalado **siempre** entra a la boca actual; la pluma siempre sale de la boca |
| Origen del volumen de inhalar, el foco, destino de la pluma | **marco con retardo** (mundo): posición τ 0,3 s, giro τ 0,8 s (×3 en las pausas; ×0,25 mientras el aire está apagado por un giro), cabeceo × 0,75 | los movimientos chicos dejan el aire quieto en el mundo (no parece suciedad en el lente) |
| Todo el aire mientras la cabeza gira | se **apaga** con la velocidad angular de la cabeza (y del marco que la alcanza): 6 → 20°/s | el aire no se arrastra por el mundo: la revisión midió 24-72°/s de arrastre sin esto; ahora el arrastre es ≤ 6,6°/s por encima del movimiento propio (§4.3) |
| Motas ya emitidas | sin estado: se recalculan cada cuadro | no hay arreglos ni índices dinámicos en el VS (en Quest rompen la malla) |

### 2.4 Por qué el aire toma la velocidad de `MPC_Breath` y no de una variable del rig

- `v = dS/dt` de `Signed` **es** `BreathFollowVel` (salvo en el tope, donde el seguidor se clava), y es la señal que ve el metaball: aire y alma se mueven juntos.
- Robusto: si el rig deja de tickear (`SetRigActive(false)`), `Signed` y `On` quedan en 0 → el aire se apaga solo (suave: `GlobTau`), y la velocidad no se calcula sin detección (`On` < 0,05), así el escalón del `Retire` no mueve la cinta.
- `AddTickPrerequisiteActor(rig)`: el aire tickea después del rig y lee el `Signed` de este cuadro.

---

## 3. Señales

| Señal | Fórmula | Filtro / latencia | Dónde se calcula |
|---|---|---|---|
| `S` = `MPC_Breath.Signed` | `NormRange` → `FollowBreath` del rig (velocidad ∝ √distancia, ataque 0,12 s, 3 s de extremo a extremo) | el seguidor; arranca en ~0,15 s | rig (existe) |
| `On` | umbral con debounce 1,5 s / 0,2 s, suavizado τ 0,5 s (el `Retire` lo manda a 0 en un cuadro) | — | rig (existe) |
| **`Vel`** (nueva) | `clamp((S − Sprev)/dt, ±VelMax)` si `On` > 0,05; si no, 0 | tope `VelMax` 2/s | `AirStep` |
| **`VelF`** | `VelF += (Vel − VelF)(1 − e^(−dt/VelTau))` | `VelTau` 0,15 s | `AirStep` |
| **`Flow`** (modo) | **histéresis**: entra a inhalar/exhalar con `|VelF|` > `VelEnter` (0,10/s) y sigue mientras `|VelF|` > `VelStay` (0,04/s); si no, 0 (pausa). +1 / −1 / 0 | — | `AirStep` |
| **`Tin`, `Tout`** (fases integradas) | `Tin = frac(Tin + ½·InTravel·max(VelF,0)·dt)` **solo en modo inhalar**; `Tout` igual con `max(−VelF,0)` solo en modo exhalar | transporte integrado: nunca una velocidad en caliente (gotcha 329); en la pausa la cinta no avanza | `AirStep` |
| **`Fout`** (frente de la pluma) | `min(Fout + FrontLead·OutRate·dt, 1,5)`; vuelve a 0 solo cuando la pluma ya es invisible (`Eout` < 0,01 y no se exhala) | — | `AirStep` |
| **`Ein`, `Eout`** (envolventes) | la corriente activa → 1 con τ `RiseTau` 0,3 s; la otra → 0 con τ `CrossTau` 0,5 s; en las pausas → 0 con τ `HoldTau` 2,5 s (suspendidas) | exponencial por cuadro | `AirStep` |
| **`RateBpm` → `RateCalm`** | período entre inicios de exhalación (2-30 s), EMA de ~2 ciclos. **Un inicio cuenta solo si antes hubo ≥ `InhMin` 0,6 s de inhalación sostenida** (latch: el reingreso al final de la exhalación o el ruido de una pausa no lo duplican). `RateCalm = FastFloor + (1 − FastFloor)·(1 − smoothstep(10, 16 resp/min, RateBpm))` | EMA | `AirStep` |
| **`TurnRate`** | `max(|Δyaw|, |Δpitch| de la cabeza; |Δyaw|, |Δpitch|·PitchFollow del marco que la alcanza) / dt` (°/s) | — | `AirStep` |
| **`MoveFade`** | objetivo `1 − smoothstep(TurnFade0 6, TurnFade1 20, TurnRate)`; **baja en el mismo cuadro**, vuelve con τ `TurnBack` 0,6 s | — | `AirStep` |
| **`Glob`** | `GlobBase · MoveFade`; `GlobBase` sigue a `clamp(On)·AirAmount·RateCalm·montado` con τ `GlobTau` 0,5 s | suave: el `Retire` no apaga el aire en un cuadro | `AirStep` |
| **`LiveS`** (valle) | sigue a `clamp(Signed, −1, 1)·clamp(On·LiveAmount, 0, 1)` con τ `LiveTau` 1 s | el `Retire` no salta el horizonte | `StepLive` |
| *Coherencia con el pacer* (tanda 2) | `Sync = EMA_τ[P·S] / √(EMA_τ[P²]·EMA_τ[S²])`, `P` = pulmón del pacer en [−1, 1], τ = 1 ciclo | EMA τ = 1 ciclo | `BP_BreathStage_SC`. **No se construye en la tanda 1** |

- `FlowIn`/`FlowOut` de `MPC_Breath` no se usan: el aire integra su propia fase desde `Signed` (la misma señal del metaball), con su propio recorrido por respiración (`InTravel`, `OutTravel`).
- **Calibración del ruido (modelo):** con la señal real simulada (ruido OU del mando τ 0,4 s + deriva del sostenido), el p99 de `|VelF|` en la segunda mitad de una pausa es 0,075/s con ruido 0,03, 0,085 con 0,05, **0,100 con 0,06** y 0,152 con 0,08: la pausa queda quieta mientras ese p99 esté por debajo de `VelEnter`. **Regla para el visor (paso S3):** `VelEnter` ≥ 3 × std(`VelF` en la pausa real), `VelStay` ≈ 0,4 × `VelEnter`.

---

## 4. A — El aliento visible

### 4.1 Qué se ve

| Momento | Qué pasa |
|---|---|
| **Inhala** | motas diminutas y frías (lavanda muy clara) aparecen en el aire de adelante, en la parte baja de la vista, y **se juntan de costado** hacia un foco a ~40 cm del ojo y ~25° debajo de la mirada, acercándose (se ve en estéreo); pasado el foco bajan a la boca y ya se apagaron por la cercanía. La mitad gira hacia cada lado: se lee como aire que se junta, sin rotación del campo |
| **Retiene** | quedan suspendidas donde estaban y se apagan en ~2,5 s; nada se mueve (la turbulencia también se detiene: su fase es la de la pluma). **Con el ruido real del sensor también** (histéresis) |
| **Exhala** | la pluma tibia (durazno pálido) aparece a ~40 cm (la condensación, como el vaho real), frena, se abre, sube apenas y se apaga hacia 1,1 m, **por debajo del metaball** (5 % de su alfa se superpone con el disco del metaball) |
| **Pausa** | la pluma queda suspendida y se desvanece |
| **Sin detección** (`On` 0) | nada (capa viva pura; decisión 2). Si el rig se retira a mitad de una respiración, el aire se apaga en ~1-2 s, sin saltar |
| **Respiración rápida** | más tenue (`RateCalm` hasta ×0,5 desde 16 resp/min). La lenta con retenciones **no** se atenúa (el ritmo se mide bien) |
| **Gira la cabeza** | el aire se apaga mientras gira (desde 6°/s, del todo a 20°/s) y reaparece en su lugar ~1,1 s después de un giro de 30° (1,3 s de 90°); lo inhalado sigue entrando a la boca actual. El balanceo de una persona sentada (hasta ~4°/s) no lo apaga |
| **Mira hacia abajo** (al sensor, a la panza) | el aire acompaña la mirada: con `PitchFollow` 0,75 la pluma conserva el 90 % a −35° (con 0,5 perdía el 81 %) |

### 4.2 Mapeo exacto

| Entrada | Operación (BP) | Parámetro del material | Efecto en el VS |
|---|---|---|---|
| modo inhalar (histéresis sobre `VelF`) | `Tin` avanza `½·InTravel·VelF·dt`; `Ein` → 1 | `AirT.x`, `AirE.x`, `AirE.z` (= `InRate`) | `s = frac(e + Tin)`, `w = s^InAccel`; posición = **Bézier** `(1−w)²·st + 2w(1−w)·cp + w²·en`: `st` en el volumen (marco con retardo), `en` = boca exacta + jitter, `cp` = lerp(punto medio, **foco**, `InFocus`); alfa × `smoothstep(0, 0,2, s)` × `Ein` |
| modo exhalar | `Tout` avanza `½·OutTravel·(−VelF)·dt`; `Fout` avanza; `Eout` → 1 | `AirT.y`, `AirT.z`, `AirE.y`, `AirE.w` | `s = frac(e + Tout)`; `x(s) = OutStart + (PlumeLen − OutStart)(1 − (1 − s)^OutDecel)`; cono `OutSpread`; subida `Buoy·s²` (arriba del MUNDO); turbulencia `Turb·s` con fase de `Tout`; visible si `s < Fout` |
| pausa (modo 0) | envolventes → 0 con `HoldTau`; `Tin`/`Tout` **quietos** | — | todo suspendido |
| pose de la cámara | boca exacta (constante local) + marco con retardo (mundo → local) | `MouthL`, `LagM`, `LagA/R/U`, `UpL` | `InTilt` 24° / `FocusTilt` 16° / `OutTilt` 18° bajo el marco |
| `On`, `AirAmount`, `RateCalm`, montado, giro | producto suavizado × `MoveFade` | `AirT.w` (= `Glob`) | alfa × `Glob`; `Glob` 0 = nada dibujado |

Una inhalación completa (−1 → +1) mueve la cinta ~`InTravel` = 0,9 caminos, **sea rápida o lenta**: el aire se mueve lo que se movió la respiración.

### 4.3 Confort visual (medido en el modelo; 5 ciclos 4-3-4-3, giro de 30°, mirada al sensor a −35°, inclinación de 8 cm)

| Regla | Cómo se cumple (por mota, en el VS, con la cámara de CADA ojo) | Medido |
|---|---|---|
| Nada cerca de los ojos (plano cercano ~10 cm) | alfa × `smoothstep(NearMin 22, NearFull 45 cm, distancia al ojo)` | mota visible más cercana: **24,9 cm**; alfa visible de inhalar a < 50 cm: **40 %** (era 52 %), mediana **54 cm**; de exhalar 12 %, mediana 83 cm |
| Solo en la banda baja, nunca delante de los ojos | alfa × (1 − `smoothstep` en el seno de la elevación, de −10° a `ElevMax` −4°) | elevación máxima de una mota visible: **−4,74°** |
| Diminutas y sin centelleo | tamaño = `clamp(físico, dist·tan 0,2°, dist·tan MaxDeg)`; lo que se agranda hasta 0,2° baja de alfa por (físico/dibujado)² (energía constante) | ancho a media altura: mediana 2,5 px (20 px/°) / 3,1 px (25 px/°), **ninguna mota por debajo de 2 px** (antes 17 % del alfa de inhalar); cobertura por ojo: media **0,71 %**, máx. **1,36 %** |
| Suaves, bajo contraste | punto `(1 − r²)²`, alfa pico 0,45 / 0,5, colores cerca del tono del aire | — |
| Sin destellos rápidos | alfa × (1 − `smoothstep(20, 40 °/s, velocidad angular analítica)`) | cabeza quieta, todo el ciclo: p50 0,6 · p90 5,6 · p99 **11,7** · máx. 20,4 °/s. **En plena corriente:** inhalar p50 3,5 · p90 6,8 · p99 9,9; exhalar p50 3,7 · p90 6,8 · p99 10,5 °/s |
| Sin arrastre al girar la cabeza | `MoveFade` (6 → 20°/s) × `Glob`; el marco alcanza más rápido mientras está apagado | p90 de la velocidad respecto del MUNDO de las motas visibles, contra su movimiento propio antes del giro: exhalando 13,9 → 13,6 (30° y 90°); inhalando 3,4 → 9,5 (30°) y 10,0 (90°). La revisión había medido 24-27 °/s (30°) y 69-77 °/s (90°) sin esto |
| Sin saltos | fases integradas; la cinta salta con alfa 0 (verificado en el HLSL); el escalón del `Retire` no mueve la cinta | salto máx. de una mota visible: **0,72 cm** por cuadro; con el `Retire`: la presencia baja ≤ 2,7 % por cuadro y la cinta ≤ 0,004 caminos por cuadro |
| Sin vección | campo angosto y bajo; remolino mitad y mitad (sin giro neto); flujo vertical lento (inhalar −1,15 °/s mediana) | — |
| No "suciedad en el lente" | marco con retardo; apagado por giro; se mueve con la respiración y se apaga en las pausas | retraso máx. del marco en el giro de 30°: **16°** (con el aire apagado) |

**Latencia (modelo):** 20 motas visibles a los **0,54 s** de empezar a inhalar y a los **0,64 s** de empezar a exhalar (la pluma recorre su frente y aparece a ~40 cm). `Ein` > 0,5 a los 0,67 s (el filtro `VelTau` suma ~0,13 s a cambio de pausas quietas). El vínculo causal aguanta segundos (Wen 2019).

### 4.4 La señal real: ruido del sensor y deriva de la pausa (modelo, 4-3-4-3, 8 ciclos, 3 semillas)

| Caso | Pausa quieta (2.ª mitad) | Pluma con el aire retenido arriba (`Eout` máx.) | Cambios de modo por pausa | Ritmo medido (real 4,29) | `Ein` > 0,5 / `Eout` > 0,5 |
|---|---|---|---|---|---|
| ideal | 100 % | 0,00 | 0,50 | 4,30 | 0,67 / 0,35 s |
| ruido 0,03 + deriva 0,2 | 100 % | 0,00 | 0,50 | 4,30 | 0,78 / 0,37 s |
| ruido 0,05 + deriva 0,15 | 100 % | 0,00 | 0,50 | 4,30 | 0,70 / 0,36 s |
| ruido 0,06 + deriva 0,15 | 99,1 % | 0,00 | 0,61 | 4,30 | 0,69 / 0,36 s |
| ruido 0,08 + deriva 0,2 | 87,7 % ❌ | 0,67 ❌ | 1,83 | 4,66 | 0,49 / 0,30 s |

- Metas: quieta ≥ 98 %, `Eout` < 0,1, < 2 cambios, ritmo ± 1. **Se cumplen hasta ruido 0,06.** La revisión había medido, con el BP de la rev. 1 y ruido 0,03-0,04: 19-27 % de la pausa "respirando", la pluma apareciendo con el aire retenido (0,49-0,66) y ~8-10 alternancias por pausa.
- Si en el visor el ruido real es mayor (paso S3 lo mide con `ke * AirDbg`): subir `VelEnter` (y `VelStay` ≈ 0,4×) o `VelTau` a 0,25 s, en la instancia, sin tocar código.
- Lo que falta probar en el visor: el usuario **balanceándose o inclinándose sin respirar** (la señal es la distancia horizontal cámara-sensor: el balanceo entra directo).

### 4.5 Ritmo (modelo, suma de alfa visible)

| resp/min | 4,3 (4-3-4-3) | 6 | 10 | 15 | 20 |
|---|---|---|---|---|---|
| con `RateCalm` | 227 | 282 | 273 | **207** | **181** |
| sin `RateCalm` | 227 | 282 | 273 | 349 | 362 |
| `RateBpm` medido | 4,3 | 6,0 | 9,9 | 15,0 | 20,0 |

- Respirar rápido ya no da más aire: da menos. La respiración lenta con retenciones **no** se atenúa (antes el BP medía ~12 resp/min para 4,3 por el doble conteo y la apagaba 12-34 %); lo que baja en 4,3 es solo el tiempo en pausa (el aire se apaga en las retenciones, a propósito).

### 4.6 Costo

| Parte | Cuenta | Estimado |
|---|---|---|
| VS | 2048 quads × 4 vértices × 2 vistas × ~280 op-eq ≈ 4,6 M op-eq (+ binning) | **0,025-0,050 ms**; ×2 si Unreal compila el Custom dos veces (WPO + interpolador) |
| PS | cobertura media 0,71 % × ~12 op-eq × 3 (quads chicos) | **≈ 0,002 ms** |
| CPU (Blueprint) | `AirTick` (~300 evaluaciones de nodos por cuadro; `GetWorldTransform` una vez en `CamXf`) + 8 vectores a un MID; `StepLive` + 12 escalares a dos MIDs | **0,15-0,3 ms de hilo de juego, sin medir** (la revisión estimó 0,2-0,4 antes de los recortes). El MID no encola nada si el valor no cambia (`MaterialInstance.cpp` de 5.8). Entering está limitada por GPU: no se esperan fps perdidos; el banco imprime el CPU del peor núcleo como señal gruesa |
| Sin aire (`Glob` 0) | el componente se oculta (`SetVisibility`) | **0** |

### 4.7 Vista previa en el editor (Beltrán autora mirando)

- El actor colocado **es la cabeza**: se pone a la altura de los ojos del usuario sentado, mirando al metaball. `HeadGhost` (esfera) y `MouthGhost` (punto en la boca) son solo de editor (ocultos en juego).
- `PreviewBreath` (−1 … 1): > 0 muestra la inhalación con esa envolvente; < 0 la pluma. **0 = no dibuja nada.** `PreviewAirT` arrastra la cinta (como la `T` del pacer).
- Para ver lo que ve el usuario: `CaptureViewport` con `captureTransform` = la transform del actor (receta E14).
- En PIE: `bFakeBreath` del rig (en la instancia de PIE) mueve toda la cadena.

### 4.8 Previsualizaciones sin Unreal y crítica

Carpeta `VR_Test/Saved/ClaudeScripts/aliento/` (las hace `scripts/sim_breath_air.py` con el modelo verificado contra el HLSL, sobre el valle **con el look actual** y la capa viva):

| Imagen | Qué muestra |
|---|---|
| `aliento_primera_persona.png` | vista del usuario (ojos a 120 cm, pitch −2°, HFOV 90) en inhalar / retener / exhalar / pausa, con el valle de la capa viva de fondo; abajo, la banda baja ×2 |
| `aliento_estelas.png` | 1,2 s de movimiento en un cuadro (cada mota en 12 instantes): hacia dónde va el aire |
| `aliento_lateral.png` | costado con una cabeza de referencia, los límites de 22/45 cm y el tope de −4° |
| `aliento_geometria.png` | caminos de lado (con el foco), en planta y durante un giro de 30° |
| `aliento_ciclo.gif` | un ciclo 4-3-4-3 (14 s): primera persona + costado |
| `valle_capa_viva_comparacion.png` | el valle en reposo (= look actual exacto), inhalado, exhalado y el mapa de cambio ×10 |

**Crítica honesta:**
- ✅ **La exhalación se lee sola**: la pluma nace abajo, sube abriéndose y pasa por debajo del metaball; de costado sale de la boca y se apaga a ~1,1 m.
- ✅/⚠ **La inhalación ahora converge**: con el foco, el movimiento lateral hacia el centro domina (mediana −2,6 °/s hacia el centro contra −1,15 °/s hacia abajo; cociente vertical/lateral **0,4**, era 4,2 con el 98 % de las motas bajando; ahora baja el 75 %). Sigue siendo más tenue que la pluma (alfa total ~155 contra ~340: 768 motas contra 1280, y alfa pico 0,45): **se juzga en el visor**. Palancas sin tocar código: `InAlpha` 0,45 → 0,6; más `InFocus` (hasta 1); más `InTilt` (24-28) = menos vertical; menos `FocusTilt` (10-12) = foco más alto, menos caída. (La rev. 1 decía lo contrario sobre `InTilt`: estaba mal.)
- ✅ **La pluma no compite con el metaball**: 5 % de su alfa dentro del disco angular del metaball (radio 16,8°), era 22 %. Para que "vaya hacia el alma", `OutTilt` 12 (decisión 3).
- ✅ **Molestia a la vista**: nada por encima de −4,74° ni a menos de 24,9 cm; cobertura < 1,4 %; nada rápido visible; no se arrastra al girar. El punto a mirar en el visor es la **pluma recién nacida** (la más cercana) y la inhalación a 40-50 cm (vergencia).
- ⚠ **El valle cambia poco a propósito** (§6.5): horizonte y colinas 1,9 niveles medios (p90 4,3) entre inhalar y exhalar; el piso cercano casi nada (0,5). **Es posible que no se perciba**: se suben las familias (`FogBreath`, `GlowBreath`, `WarmBreath`) sin tocar código.
- ❌ **Lo que NO muestran**: el metaball real (la esfera es la de referencia), el estéreo, el tamaño en el visor, la mirada libre.

---

## 5. El aliento: assets, parámetros y Blueprint

### 5.1 Malla `SM_BreathAir_SC`

- 2048 quads reales de 0,4 cm (8192 vértices, 4096 triángulos): 768 de inhalar y 1280 de exhalar, **en ese orden** (los `[branch]` del VS casi no divergen).
- **Semillas invariantes a la V invertida** (gotcha 302: el importador FBX de Unreal entrega V como 1 − V): lo asimétrico va en U; en V solo números uniformes o `(b + 1)/2` de algo simétrico. UV0 = esquina · UV1 = (`e` desfase estratificado, `u` profundidad) · **UV2 = (`a`, `(b + 1)/2`)**, el VS decodifica `b = 2v − 1` · **UV3 = (corriente 0/1, `ph` fase)**. `breath_air_model.encode_uv()` escribe, `decode_uv()` es la cuenta del VS. **Con la V invertida las estadísticas no cambian** (alfa total 154,9 → 154,2 al inhalar, 343,49 → 343,47 en la pluma, elevación media igual); con la codificación de la rev. 1 se intercambiaban las corrientes (768 → 1280) y la pluma perdía el 50 % del alfa (`BreathAir_check.py` §6 prueba las dos).
- Las posiciones solo definen los **bounds**: los quads se reparten en la caja X −40…170, Y ±150, Z −130…60 cm (local de la cámara), que cubre todo lo que el VS puede dibujar visible.
- Generada headless: `blender --background --factory-startup --python scripts/gen_breath_air.py` → `VR_Test/Saved/ClaudeScripts/aliento/SM_BreathAir_SC.fbx`. Reimportada y verificada: 8192 v / 2048 polígonos / 4 capas de UV / |UV − codificada| ≤ 3e-8 / caja exacta. (Blender no invierte la V: la reimportación verifica lo escrito; la inversión de Unreal la cubre la codificación.)

### 5.2 Material `M_BreathAir_SC` (+ `MI_BreathAir_SC` para autoría)

- **Unlit, Translucent `BLEND_AlphaComposite` (premultiplicado), Two Sided, sin niebla de translúcidos** (`bUseTranslucencyVertexFog` false). No escribe profundidad.
- Grafo (lo arma `apply_breath_air_material.py`):

```
 LocalPosition (XYZ) ─────────────┐
 TexCoord 0 / 1 / 2 / 3 ──────────┤
 CameraPositionWS → TransformPosition (World→Local) ── CamL ──► Custom BreathAirVS (F3) ── return ──► Transform (vector, Local→World) ──► WPO
 8 VectorParameter (9 - Interno) + 31 ScalarParameter ────────►        └── AirV (F4) ──► VertexInterpolator ──┐
                                                                                                              ▼
                                                       InColor, OutColor ──► Custom BreathAirPS (F3) ── return ──► Emissive
                                                                                                    └── Alpha ───► Opacity
```

- El VS colapsa a tamaño 0 los quads con alfa < 0,002 (no cuestan píxeles). Sin bucles, sin arreglos, sin índices dinámicos (regla Adreno). En el componente: `TranslucencySortPriority` **20** (después del pacer 0 y del metaball 10; el aire siempre está más cerca que ellos).

### 5.3 Parámetros del material `M_BreathAir_SC`

| Grupo | Parámetro | Tipo | Default | Rango sugerido | Qué hace |
|---|---|---|---|---|---|
| `1 - Inhalar` | `InTilt` | escalar | 24 | 18 … 30 | Grados bajo el marco del aire donde nace el volumen de la inhalación. **Más = menos vertical** en la vista (las motas ya nacen abajo y caen menos) |
| `1 - Inhalar` | `InNear` | escalar | 40 | 30 … 55 | Lo más cerca que nace una mota de inhalar (cm desde la boca con retardo) |
| `1 - Inhalar` | `InFar` | escalar | 95 | 60 … 120 | Lo más lejos (cm) |
| `1 - Inhalar` | `InSpreadH` | escalar | 30 | 15 … 40 | Ancho del volumen (± grados). Más de ~35 empieza a llenar la periferia (vección) |
| `1 - Inhalar` | `InSpreadV` | escalar | 12 | 6 … 20 | Alto del volumen (± grados) |
| `1 - Inhalar` | `InAccel` | escalar | 1,35 | 1 … 2 | Forma del viaje: > 1 = lento lejos y acelera al llegar (sumidero) |
| `1 - Inhalar` | `InSwirl` | escalar | 35 | 0 … 60 | Grados de remolino hasta la boca (0 = recto). La mitad de las motas gira hacia cada lado: el campo no rota en conjunto |
| `1 - Inhalar` | `InAlpha` | escalar | 0,45 | 0,2 … 0,7 | Opacidad pico de las motas de inhalar |
| `1 - Inhalar` | `InSizeCm` | escalar | 0,22 | 0,12 … 0,4 | Diámetro físico de la mota (cm); lo limitan `MaxDeg` y el piso de 0,2° |
| `1 - Inhalar` | `InFocus` | escalar | 0,8 | 0 … 1 | Cuánto pasa el camino por el foco: 0 = recta a la boca (se lee como caída); 1 = se juntan de costado antes de bajar |
| `1 - Inhalar` | `FocusDist` | escalar | 34 | 25 … 45 | Distancia del foco a la boca con retardo (cm): ~40 cm del ojo |
| `1 - Inhalar` | `FocusTilt` | escalar | 16 | 8 … 24 | Grados del foco bajo el marco del aire (~25° bajo la mirada). Menos = foco más alto, menos caída |
| `2 - Exhalar` | `OutTilt` | escalar | 18 | 8 … 24 | Grados bajo el marco del aire del eje de la pluma. 18-20 = por debajo del metaball; 12 = hacia su pie (decisión 3) |
| `2 - Exhalar` | `PlumeLen` | escalar | 110 | 70 … 140 | Dónde termina la pluma (cm desde la boca) |
| `2 - Exhalar` | `OutStart` | escalar | 15 | 10 … 25 | Dónde empieza (cm): la condensación, como el vaho real |
| `2 - Exhalar` | `OutDecel` | escalar | 1,8 | 1 … 3 | > 1 = chorro que frena al alejarse |
| `2 - Exhalar` | `OutSpread` | escalar | 16 | 8 … 24 | Apertura del cono (grados) |
| `2 - Exhalar` | `OutFlat` | escalar | 0,6 | 0,3 … 1 | Aplastamiento vertical del cono (1 = redondo) |
| `2 - Exhalar` | `Buoy` | escalar | 10 | 0 … 20 | Subida tibia al final de la pluma (cm) |
| `2 - Exhalar` | `Turb` | escalar | 3 | 0 … 6 | Turbulencia (cm). Se detiene en las pausas (su fase es la de la pluma) |
| `2 - Exhalar` | `OutAlpha` | escalar | 0,5 | 0,2 … 0,7 | Opacidad pico de la pluma |
| `2 - Exhalar` | `OutSizeCm` | escalar | 0,28 | 0,15 … 0,45 | Diámetro al salir (cm) |
| `2 - Exhalar` | `OutGrow` | escalar | 0,8 | 0 … 1,5 | Crecimiento hasta el final de la pluma (0,8 = ×1,8) |
| `3 - Confort` | `NearMin` | escalar | 22 | 18 … 30 | 🔴 Invisible a menos de esto de CADA ojo (cm). No bajar sin probar en el visor |
| `3 - Confort` | `NearFull` | escalar | 45 | NearMin + 8 … 55 | Plena desde acá (cm). 45 corre la masa del aire más allá de 50 cm (vergencia-acomodación) |
| `3 - Confort` | `ElevMax` | escalar | −4 | −10 … −2 | 🔴 Invisible por encima de esta elevación respecto de la mirada (grados) |
| `3 - Confort` | `ElevSoft` | escalar | 6 | 3 … 10 | Fundido por debajo de `ElevMax` (grados) |
| `3 - Confort` | `MaxDeg` | escalar | 0,4 | 0,25 … 0,6 | Tope de tamaño angular de las motas de inhalar (grados): lo cercano no se agranda |
| `3 - Confort` | `MaxDegOut` | escalar | 0,55 | 0,3 … 0,8 | Tope de tamaño angular de la pluma (grados) |
| `3 - Confort` | `SpeedFade0` | escalar | 20 | 10 … 30 | Grados/s en la vista desde donde lo rápido se apaga |
| `3 - Confort` | `SpeedFade1` | escalar | 40 | SpeedFade0 + 10 … 60 | Apagado del todo (grados/s) |
| `4 - Color` | `InColor` | vector | (0,80, 0,85, 1,00) | — | Color de las motas de inhalar (lineal; frío, casi el tono del aire del valle) |
| `4 - Color` | `OutColor` | vector | (1,00, 0,84, 0,80) | — | Color de la pluma (lineal; tibio, el tinte que toma la bruma al exhalar) |
| `9 - Interno` | `AirT` | vector | (0, 0, 0, 0) | — | Lo escribe el BP: (Tin, Tout, Fout, Glob). Con Glob 0 no se dibuja nada |
| `9 - Interno` | `AirE` | vector | (0, 0, 0, 0) | — | Lo escribe el BP: (Ein, Eout, InRate, OutRate) |
| `9 - Interno` | `MouthL` | vector | (6, 0, −9) | — | Lo escribe el BP: la boca exacta en local de la cámara (cm) |
| `9 - Interno` | `LagM` | vector | (6, 0, −9) | — | Lo escribe el BP: la boca con retardo, en local |
| `9 - Interno` | `LagA` | vector | (1, 0, 0) | — | Lo escribe el BP: eje adelante del marco con retardo, en local |
| `9 - Interno` | `LagR` | vector | (0, 1, 0) | — | Lo escribe el BP: eje derecha del marco con retardo |
| `9 - Interno` | `LagU` | vector | (0, 0, 1) | — | Lo escribe el BP: eje arriba del marco con retardo |
| `9 - Interno` | `UpL` | vector | (0, 0, 1) | — | Lo escribe el BP: el arriba del MUNDO en local (la subida tibia) |

Constantes del HLSL (no perillas): piso de tamaño **0,2°** (antes 0,12°, con la compensación de alfa), radio inicial de la pluma 1,5 cm, frente 0,08, emergencia 0,02-0,12, fundidos 0,2 / 0,5, profundidad `u^0,8`, corte de alfa 0,002.

### 5.4 Perillas del Blueprint `BP_BreathAir_SC`

| Grupo | Perilla | Tipo | Default | Rango sugerido | Qué hace |
|---|---|---|---|---|---|
| `A-Aliento` | `bAir` | bool | true | — | Apaga el aliento entero (Glob 0) |
| `A-Aliento` | `AirAmount` | escalar | 1 | 0 … 1 | Intensidad global. 0 = apagado (A/B del banco, botón de pánico) |
| `A-Aliento` | `MouthFwd` | escalar | 6 | 3 … 10 | Boca: cm delante de la cámara |
| `A-Aliento` | `MouthDown` | escalar | 9 | 6 … 12 | Boca: cm debajo de la cámara |
| `A-Aliento` | `InTravel` | escalar | 0,9 | 0,5 … 1,2 | Cuánto del camino recorre una inhalación completa (−1 → +1), sea rápida o lenta |
| `A-Aliento` | `OutTravel` | escalar | 0,8 | 0,5 … 1,2 | Idem para la pluma |
| `A-Aliento` | `FrontLead` | escalar | 1,6 | 1 … 2,5 | Qué tan rápido se despliega la pluma desde la boca respecto de sus motas |
| `A-Aliento` | `LagPos` | escalar | 0,3 | 0,1 … 0,8 | Retardo de la posición del marco del aire (s) |
| `A-Aliento` | `LagRot` | escalar | 0,8 | 0,3 … 2 | Retardo del giro del marco del aire (s) |
| `A-Aliento` | `HoldLagMul` | escalar | 3 | 1 … 5 | En las pausas el marco sigue a la cabeza este múltiplo más lento |
| `A-Aliento` | `PitchFollow` | escalar | 0,75 | 0,5 … 1 | Cuánto sigue el aire al cabeceo. 0,75 = mirando la panza el aire sigue visible; 0,5 = el aire se queda más en el mundo y al mirar abajo se esconde (decisión 7) |
| `A-Aliento` | `PitchMin` | escalar | −35 | −50 … −10 | Tope del cabeceo seguido hacia abajo (grados) |
| `A-Aliento` | `PitchMax` | escalar | 10 | 0 … 20 | Tope del cabeceo seguido hacia arriba (grados): mirar al cielo no sube el aire a la vista |
| `A-Aliento` | `RiseTau` | escalar | 0,3 | 0,1 … 0,6 | Cómo aparece la corriente activa (s) |
| `A-Aliento` | `HoldTau` | escalar | 2,5 | 1 … 5 | Cuánto quedan suspendidas en las pausas (s) |
| `A-Aliento` | `CrossTau` | escalar | 0,5 | 0,2 … 1 | Cómo se apaga una corriente cuando empieza la otra (s) |
| `A-Aliento` | `VelTau` | escalar | 0,15 | 0,05 … 0,3 | Pasabajos de la velocidad de la respiración (s): más = pausas más quietas con ruido, más latencia |
| `A-Aliento` | `VelEnter` | escalar | 0,1 | 0,06 … 0,2 | Velocidad (1/s de `Signed` filtrada) desde la que EMPIEZA a contar como inhalar o exhalar. ≥ 3 × el ruido medido en una pausa |
| `A-Aliento` | `VelStay` | escalar | 0,04 | 0,02 … 0,08 | Velocidad hasta la que SIGUE contando (histéresis) |
| `A-Aliento` | `VelMax` | escalar | 2 | 1 … 4 | Tope de la velocidad (1/s): un escalón de la señal no dispara la cinta |
| `A-Aliento` | `InhMin` | escalar | 0,6 | 0,3 … 1,5 | s de inhalación sostenida para que el próximo inicio de exhalación cuente en el ritmo |
| `A-Aliento` | `FastFloor` | escalar | 0,5 | 0 … 1 | Presencia del aire con la respiración rápida (1 = sin atenuar) |
| `A-Aliento` | `CalmRate` | escalar | 10 | 6 … 12 | Respiraciones/min hasta donde el aire está pleno |
| `A-Aliento` | `FastRate` | escalar | 16 | CalmRate + 3 … 24 | Respiraciones/min desde donde queda en `FastFloor` |
| `A-Aliento` | `GlobTau` | escalar | 0,5 | 0,2 … 1,5 | Cómo sigue la presencia a la detección y al ritmo (s): el `Retire` no apaga el aire en un cuadro |
| `A-Aliento` | `TurnFade0` | escalar | 6 | 3 … 10 | °/s de giro de cabeza desde donde el aire empieza a apagarse |
| `A-Aliento` | `TurnFade1` | escalar | 20 | TurnFade0 + 5 … 40 | °/s de giro desde donde el aire está apagado del todo |
| `A-Aliento` | `TurnBack` | escalar | 0,6 | 0,2 … 1,5 | Cómo reaparece después del giro (s) |
| `A-Aliento` | `TurnCatch` | escalar | 0,25 | 0,1 … 1 | Mientras está apagado por el giro, el marco alcanza a la cabeza este múltiplo más rápido (1 = igual) |
| `B-Prueba` | `PreviewBreath` | escalar | 0 | −1 … 1 | Vista previa en el viewport, sin Play: > 0 inhalar, < 0 la pluma. 0 = no dibuja nada |
| `B-Prueba` | `PreviewAirT` | escalar | 0,35 | 0 … 1 | Arrastra la cinta en la vista previa (como la `T` del pacer) |

### 5.5 Estado y componentes de `BP_BreathAir_SC`

**Componentes** (en el CDO, ANTES de colocar el actor; en la plantilla `<Comp>_GEN_VARIABLE`, una propiedad por llamada, gotcha 478):

| Componente | Clase / asset | Transform relativo | Propiedades |
|---|---|---|---|
| `DefaultSceneRoot` | (el del BP) | — | — |
| `AirMesh` | StaticMesh `SM_BreathAir_SC`, material `MI_BreathAir_SC` | identidad | `BodyInstance` `{collisionEnabled: NoCollision, collisionProfileName: NoCollision}` (gotcha 239: los dos) · `castShadow` false · `translucencySortPriority` 20 · `bReceivesDecals` false |
| `HeadGhost` | StaticMesh `/Engine/BasicShapes/Sphere` | (−8,5, 0, 2,5), escala (0,21, 0,19, 0,23) | `bHiddenInGame` true · sin colisión · sin sombra. Una cara: desde adentro no tapa la captura. 🔴 **NO** `bIsEditorOnly`: en el APK el componente no existiría y `AirReset` (que lo oculta y le saca la colisión) tiraría `Accessed None` |
| `MouthGhost` | StaticMesh `/Engine/BasicShapes/Sphere` | (6, 0, −9), escala 0,02 | idem (marca la boca por defecto; si se cambian `MouthFwd`/`MouthDown`, moverla a mano) |

**Variables de estado** (categoría `Z-Aliento`, NO instance-editable):

| Variable | Tipo | Qué |
|---|---|---|
| `Tin`, `Tout`, `Fout` | float | fases integradas de las dos cintas y frente de la pluma |
| `Ein`, `Eout` | float | envolventes de las dos corrientes |
| `InRate`, `OutRate` | float | tasas del cuadro (para el apagado por velocidad del VS) |
| `Vel`, `VelF`, `Sprev`, `bPrimed` | float, float, float, bool | velocidad cruda con tope, filtrada, y su memoria |
| `Flow`, `InhHold` | float, float | modo (+1 / −1 / 0) y s de inhalación sostenida (latch del ritmo) |
| `Clock`, `bOnset`, `Per`, `LastOnset`, `RateBpm`, `RateCalm` | float/bool | ritmo |
| `MouthW` | Vector | boca con retardo, en el MUNDO |
| `YawLag`, `PitchLag`, `YawPrev`, `PitchPrev`, `bLagInit` | float ×4, bool | giro con retardo y la cabeza del cuadro anterior |
| `TurnRate`, `MoveFade` | float | velocidad de giro (°/s) y apagado por giro |
| `GlobBase`, `Glob` | float | presencia suavizada y final (`AirT.w`) |
| `CamXf` | Transform | la transform de `AirMesh` del cuadro (se lee una vez: un bind de `GetWorldTransform` se re-evaluaría en cada uso) |
| `bMounted`, `Rig` | bool, objeto `BP_BreathRig_SC_C` (`add_object_variable`) | montaje |
| `PerfMode` | int | banco: 0 normal · 1 oculto · 2 lleno |
| `AirSig`, `AirGate` | float | lo que se leyó de `MPC_Breath` (`Signed`, `On`) este cuadro |

Nombres elegidos para el DSL: categorías sin espacios (gotcha 466) y **sin palabras que Unreal pasa a minúscula en el nombre visible** (`In`, `On`, `To`, `Of`, `At`… salvo como primera palabra: `RateIn` daría el getter `GetRatein`, `GateOn` daría `GetGateon`; por eso `VelEnter`/`VelStay`).

### 5.6 Grafos de `BP_BreathAir_SC` (texto exacto: `scripts/breath_air.dsl`)

| Grafo | Tipo | Responsabilidad | Lo llama |
|---|---|---|---|
| `AirMPC` | función | puente a `MPC_Breath` → `AirSig`, `AirGate` (esqueleto por DSL + 2 nodos por cirugía, §11 E11) | `AirTick` |
| `PushAir` | función | los 8 vectores del cuadro, en local de la cámara | `AirReset`, `AirTick`, `PreviewAir` |
| `AirReset` | función | estado inicial, oculto, sin colisión, cabeza de referencia oculta | `BeginPlay` |
| `AirStep(DT)` | función | = `AirBP.step` del modelo (velocidad, modo, ritmo, transporte, envolventes, marco, giro, presencia) | `AirTick` |
| `AirPerf` | función | modo 2 del banco: corrientes llenas | `AirTick` |
| `AirVisible` | función | oculta el componente si no hay aire (0 costo) o en el modo 1 | `AirTick` |
| `AirMountCam` | función | `CamRef` del rig → `AttachComponentToComponent` (Snap) + `AddTickPrerequisiteActor` | `AirMount` |
| `AirMount` | función | `bind` de `GetActorOfClass(BP_BreathRig_SC)` → `SetRig` → `AirMountCam` (**nunca inline**: la función es impura) | `AirTick` (hasta montar) |
| `AirTick(DT)` | función | MPC → paso → banco → empuje → visibilidad → montaje | `EventTick` |
| `PreviewAir` | función | vista previa sin Play (`PreviewBreath`, `PreviewAirT`) | CS |
| `ConstructionScript` | CS | sort 20 (red de seguridad) + `PreviewAir` | — |
| `EventGraph` | eventos | `BeginPlay` → `AirReset`; `Tick` → `AirTick`; `PerfE0`/`PerfE5`/`PerfE6` (ecos `PERF: entering modo N`); `PerfE1..4` → normal, sin eco; `AirDbg` (una línea `AIRE DBG v … modo … S …`, para medir el ruido en el visor) | — |

---

## 6. B, C, D — La capa viva del valle

### 6.1 Qué se ve

| Efecto | Inhala (S +1) | Exhala (S −1) |
|---|---|---|
| **B — la bruma respira** | la niebla se abre (las colinas lejanas se recortan un poco más) | se cierra, la bruma baja sube y el horizonte toma el tinte tibio del aliento (`BreathTint`, relativo a `SkyHorizon`, **misma luma**: entibia sin aclarar) |
| **C — el resplandor inhala** | el brillo rosa detrás del metaball sube y se afina hacia los costados | baja y se abre |
| **D — la sombra respira en densidad** | se recoge: más oscura en el centro, un poco más angosta | se ablanda: más clara, un poco más ancha y apenas tibia. **El borde no se mueve** (≤ 0,45°/s) |

En las pausas todo queda quieto en el valor de la fase (el valle "retiene" con el usuario). Sin respiración detectada (`On` 0) vuelve, suave (τ 1 s), a lo autoral.

### 6.2 Mapeo (curva de la casa, en `PushLive`)

`m(S) = 1 + g·S·lerp(−Out, In, smoothstep((S + 1)/2))`: con S = +1 da `1 + In`, con S = −1 da `1 + Out`, con S = 0 exactamente 1 y **sin quiebre en 0**. `g` = la perilla de la familia. S es `LiveS` (ya suavizada, §3).

**Bases = el look actual** (defaults del CDO según el tracker: las perillas de `ApplyLook`, 2026-09-28 16:03; el paso V5 los relee y, si difieren, se re-mide §6.5):

| Efecto | `Live*` → multiplica a | In (S = +1) | Out (S = −1) | Resultado inhala / base / exhala | Va a | Familia |
|---|---|---|---|---|---|---|
| B | `LiveFogDist` → `FogDist` | +0,20 | −0,15 | 24000 / 20000 / 17000 cm | suelo | `FogBreath` |
| B | `LiveHFogDist` → `HFogDist` | +0,20 | −0,15 | 18000 / 15000 / 12750 cm | suelo | `FogBreath` |
| B | `LiveHFogFall` → `HFogFall` | −0,10 | +0,35 | 2250 / 2500 / 3375 cm | suelo | `FogBreath` |
| B | `LiveWarm` → `SkyHorizon × (1 + (BreathTint − 1)·LiveWarm)` | 0 | 0,25 | con `SkyHorizon` (0,597, 0,624, 0,839): → (0,649, 0,611, 0,808) al exhalar | suelo y cielo | `WarmBreath` |
| C | `LiveGlowAmt` → `GlowAmt` | +0,15 | −0,25 | 0,92 / 0,80 / 0,60 | suelo y cielo | `GlowBreath` |
| C | `LiveGlowPow` → `GlowPow` | +0,15 | −0,25 | 2,3 / 2,0 / 1,5 | suelo y cielo | `GlowBreath` |
| D | `LiveShadowSoft` → `ShadowSoft` | −0,05 | +0,05 | 0,76 / 0,80 / 0,84 | suelo | `ShadowBreath` |
| D | `LiveShadowStrength` → `ShadowStrength` (sobre lo que ya empuja `StepShadow`) | +0,12 | −0,12 | 1,68 / 1,5 / 1,32 | suelo | `ShadowBreath` |
| D | `LiveShadowWarm` → mezcla `ShadowTint` → `ShadowWarm` | 0 | 0,35 | (0,305, 0,352, 0,68) → (0,39, 0,38, 0,62) | suelo | `ShadowBreath` |

- **Fijos:** `FogMax` (contraste del metaball), `FogStart` (mueve una rama: 0,06-0,4 ms), `ShadowRadius` (la rev. 1 lo respiraba a contrafase de `StepShadow`, que ya escala la sombra con el metaball, y el borde de la sombra viajaba 4,4°/s por el piso cercano), `GlowHeight` (la rev. 1 lo respiraba: la banda del resplandor subía y bajaba) y toda la geometría (`SwellAmp`, `MorphAmt`, `HillAmp`…). `Swell*`/`Morph*Speed` jamás en caliente (gotcha 329).
- **Al cielo van solo 3** (`LiveWarm`, `LiveGlowAmt`, `LiveGlowPow`): su rama no usa niebla ni sombra (la rev. 1 le empujaba 11).
- Las constantes `In`/`Out` viven en `PushLive` (literales, documentadas acá); lo que Beltrán ajusta son las 4 familias y `LiveTau`.

### 6.3 Material: 11 parámetros nuevos y 9 cadenas de preshader

- Tabla 7.1 del plan del valle (actualizada): `ShadowWarm` (`5 - Sombra`), `BreathTint` (`8 - Niebla`, cociente con la luma de `SkyHorizon`: (1,35, 0,92, 0,853)) y los 9 `Live*` (`9 - Interno`, "lo escribe el BP"). **82 parámetros** (71 escalares + 11 vectores).
- La cabecera de `ValleyPS.hlsl` cambia la **fuente** de 9 entradas a `preshader Mul(A, B)` (7), `preshader Mix(A, B, T)` (`ShadowTint`) y `preshader Tint(A, B, T)` (`SkyHorizon`); el código no cambia. `plan_valley_material.py` entiende las tres; `apply_valley_material_A.py` crea los helpers (`M_<Entrada>`; `X_<Entrada>_d/_m`, `X_<Entrada>`; `T_<Entrada>_d/_m/_o`, `T_<Entrada>` con `ConstB` 1) y `_B.py` cablea. Expresiones: 108 → 133. Detalle: `scripts/hlsl/Valley_CABLEADO.md` §10.

### 6.4 Blueprint `BP_BreathValley_SC` (texto exacto: `scripts/valley_live.dsl`)

| Variable (categoría `L-Respira`, **ninguna instance-editable**) | Tipo | Default | Qué |
|---|---|---|---|
| `bLive` | bool | true | apaga la capa viva (el valle vuelve suave a los neutros) |
| `LiveAmount` | float | 1 | intensidad global (multiplica a `On`) |
| `FogBreath` / `GlowBreath` / `ShadowBreath` / `WarmBreath` | float | 1 | intensidad de cada familia (0 = esa familia quieta; 2 = doble) |
| `LiveTau` | float | 1 | s: cómo sigue el valle a la respiración (el `Retire` no salta el horizonte) |
| `PreviewBreath` | float | 0 | vista previa sin Play (−1 … +1), en el CDO |
| `LiveS`, `LiveSig`, `LiveGate` | float | 0 | estado: la S del valle y lo leído de `MPC_Breath` |

- **Estas no son instance-editable, a diferencia de las 36 perillas de look** que otra sesión agregó hoy (`ApplyLook`, instance-editable, ajustadas en la instancia): el Construction Script resetea al CDO las no editables (gotcha 472), así la instancia `Entering_Valle` (puesta por Beltrán) **no se toca** y nada "nace en 0". Si Beltrán quiere las familias en la instancia, se marcan editables y se copian los valores a la instancia (con su permiso).
- Funciones nuevas: `LiveMPC` (puente), `PushLive(S)`, `StepLive` (el DT sale de `GetWorldDeltaSeconds`: la cirugía del Tick es un solo nodo de exec), `PreviewLive`. Cirugías de un nodo: `StepLive` después de `StepShadow` en el Tick; `PreviewLive` **al final** del CS (después de `ApplyLook`).

### 6.5 Medido (look actual, valle en Z −90,4; renders `preview_breath_valley.py respira=S` + el modelo)

**Renders** (vista del usuario, 1052×862; `render_valle_live.py` con `FogStart=800 FogDist=20000 FogMax=0.93 HFogDist=15000 HFogFall=2500 MorphAmt=0.3 valleZ=-90.4`):

| Región | Cambio medio inhala ↔ exhala (8 bits) | p90 | Luma inhala − exhala | R−B exhala − inhala |
|---|---|---|---|---|
| Cielo alto | 1,8 | 3,0 | +0,7 | +3,5 |
| Horizonte y colinas | 1,9 | 4,3 | −1,4 | +2,6 (exhalado más tibio) |
| Piso medio | 0,3 | 0,7 | −0,3 | +0,5 |
| Piso cercano (la sombra) | **0,5** | 1,0 | −0,6 | +1,0 |

- **Control:** el render con `respira=0` es **idéntico píxel a píxel** al render sin capa viva, con el look actual (0 de 906.824 píxeles distintos).
- **La sombra (modelo, a lo largo del eje al metaball):** contorno a media altura (O = 0,10): −41,0° / −40,3° / −39,2° (inhala / reposo / exhala) → **0,45°/s** en una exhalación de 4 s; contorno O = 0,02: −76,3° / −76,6° / −76,1° → **0,06°/s**. Pico 0,226 / 0,202 / 0,178 (densa al inhalar, clara al exhalar); área casi constante (157 / 146 / 134). La rev. 1 movía el borde 4,4°/s y el pico era MÁS oscuro al exhalar (0,249), al revés de su descripción.
- **El resplandor (modelo, cielo en el azimut del resplandor):** las isoluminancias se corren mediana **0,64°** (0,16°/s); entre 10 y 16° de elevación, donde el gradiente es 1,2-2,5 niveles/°, hasta **6,2°** (~1,5°/s en una inhalación): es el brillo de una luz difusa, sin borde, que cambia 3-5 niveles. La rev. 1 decía "≤ 1°": estaba mal (con `GlowHeight` respirando la mediana era 1,7°). Si en el visor se lee como una banda que sube y baja: `GlowBreath` 0,5.
- **El llano** (modelo, azimut 40-80°, lejos de la sombra): 0,2 niveles a 10 m, 1,5 a 30 m, 2,8 a 100 m, 1,1 a 300 m; horizonte y colinas (80-500 m): 2,0 medio, p90 3,9.

### 6.6 Vista previa y dónde se ajusta

- `PreviewBreath` del CDO del valle (−1 … +1) → compilar → la instancia re-corre el CS y el valle respira en el viewport. Con 0 empuja los neutros (el look tal cual).
- 🔴 **Gotcha de los MIDs viejos** (gotchas.md, "Un MID creado ANTES de que su material ganara un parámetro NUNCA lo honra"): los MIDs de `Ground`/`Sky` de `Entering_Valle` existen desde antes de que el material tenga los `Live*`: **después de aplicar el material hay que recargar el nivel** (paso V12b) o la vista previa no va a cambiar nada aunque el BP empuje bien. En PIE y en el APK los MIDs se crean de nuevo: no hace falta.
- **El look se ajusta donde ya se ajusta:** las 36 perillas del BP (`ApplyLook`, en la instancia) y la MI para lo que `ApplyLook` no empuja. **Los `Live*` no se tocan en la MI** (el BP los pisa en los MIDs). Las curvas de la capa viva: las 4 familias + `LiveTau`, en el CDO.

---

## 7. Fases de construcción y verificación

| Fase | Qué | Verificación (control positivo / negativo) | Si falla |
|---|---|---|---|
| **F0** en disco | regenerar planes y correr los 4 verificadores | `Valley_check.py` 90/90 · `BreathAir_check.py` 40/40 · `dsl_sim.py` 35/35 · `dryrun_material_script.py` 29/29 | no seguir |
| **F1** material del valle | pasos V1-V4 | **negativo:** captura desde el ojo antes/después = igual (el cambio de material es neutro). **Positivo:** compila sin `Failed to compile` después de la línea del `recompile` | re-aplicar el material con el rollback (§10) |
| **F2** BP del valle | pasos V5-V13 | **positivo:** después de recargar el nivel, `PreviewBreath` −1 → horizonte más tibio y brumoso, resplandor más bajo, sombra más clara (borde igual); +1 → horizonte más recortado, resplandor más intenso, sombra más densa. **Negativo:** `PreviewBreath` 0 → captura = F1; `bLive` false con `PreviewBreath` −1 → captura = F1 | `bLive` false en el CDO |
| **F3** assets del aire | pasos E1-E4 | malla 8192 v / 4096 tri / bounds de la caja / `LightMapCoordinateIndex` ≥ 4 · material compila · 45/45 y 3/3 entradas | borrar los assets nuevos (nada los referencia) |
| **F4** `BP_BreathAir_SC` | pasos E5-E12 | compila con `warnings_as_errors`; `read_graph_dsl` de cada función = el `.dsl`; `get_node_infos` en cada llamada propia con argumentos y en el `SetRig` (pin de valor conectado) | re-escribir SOLO la función rota (grafo propio, nuevo) |
| **F5** vista previa | paso E14 | **positivo:** `PreviewBreath` 0,8 → motas en la banda baja, a los dos lados, juntándose hacia el centro; −0,8 → la pluma centrada bajo el eje de la vista, por debajo del metaball (compararlas con `aliento_primera_persona.png`). **Negativo:** `PreviewBreath` 0 → captura = captura con el actor oculto | revisar `PushAir` / el sort / los bounds / las capas UV |
| **F6** PIE | pasos T1-T9 | log `AIRE: montado` una vez; `bMounted` true; con `bFakeBreath` `Flow` alterna +1/0/−1/0, `Tin` avanza al inhalar y queda quieto al retener; `RateBpm` ≈ el ritmo falso; `LiveS` del valle oscila; cámara PIE girada 30° → `MoveFade` baja a ~0 y vuelve en ~1-1,5 s. **Simulate:** sin pawn → no monta, oculto, cero `Accessed None` | apagar `bAir` en la instancia |
| **F7** guardar | S1 | canario igual; `is_dirty` false de cada asset; sin PIE | no guardar si el canario bajó |
| **F8** APK + banco | S2 (con Beltrán) | `quest_entering_perf.ps1 -Modos 0,4,5,6`: el eco de cada modo; **AIRE = m5 − m6** ≤ 0,1 ms (dentro de la resolución); **FONDO = m0 − m4** en 1,2-2,5 ms; el CPU del peor núcleo igual entre modos | §9 |
| **F9** visor | S3 | ruido real (`AirDbg`), balanceo sin respirar, y capa por capa (§8) | perillas |

---

## 8. Medición en la Quest y orden en el visor

- **Banco:** `scripts/quest_entering_perf.ps1 -Modos 0,4,5,6` (acepta 5 y 6; el resumen agrega la fila `AIRE (m5 - m6)` y el CPU del peor núcleo por modo). Una sola sesión, ida y vuelta (0 4 5 6 6 5 4 0), 28 s por fase:
  - **FONDO = m0 − m4** = el valle **con** la capa viva (el prerrequisito de la propuesta: el margen depende de este número; estimado 1,2-2,5 ms, **es el único número válido del valle**: la estimación es anterior a `FogStart` 800, que agranda la rama de niebla).
  - **AIRE = m5 − m6**: las dos corrientes llenas (`PerfE5`) contra el componente oculto (`PerfE6`). 🔴 `BP_PerfEntering_SC` **no tiene** `PerfE5`/`PerfE6`: en esas fases el fondo queda como lo dejó el modo anterior, y en esta ida y vuelta el 5 y el 6 siempre vienen después del 4 → **el aire se mide con el valle oculto** (la resta sigue valiendo: misma escena en las dos fases). Con `-Modos 0,5,6` el valle quedaría visible: no mezclar sesiones. Esperado ≤ 0,05 ms: **dentro de la resolución** del instrumento (~0,18 ms). Si se distingue del ruido y pasa de 0,2 ms: bajar a 1024 quads (regenerar la malla con `N_IN`/`N_OUT` a la mitad) o `MaxDeg`.
  - `PerfE1..4` dejan el aire en normal, así los modos del metaball, el pacer y el fondo no se contaminan.
  - **CPU:** la línea VrApi trae `CPU%=..(W..)`; el resumen imprime el peor núcleo por modo. Es una señal gruesa del hilo de juego (el Blueprint del aire corre igual en 5 y 6), no un tiempo: si sube de ~0,8 en algún modo, medir con `stat unit` en PIE o un CSV del profiler.
  - Normalizar por MHz si la GPU cambia de reloj entre modos (el resumen lo hace).
- Si FONDO sale alto (> 2,5 ms), separar píxeles y vértices del valle con su banco propio (`ke * PerfValley0..3`; lectura v2: píxeles = m0 − m2, vértices = m2 − m3; tracker del valle). Se mandan a mano por `adb shell am broadcast -a android.intent.action.RUN -e cmd 'ke * PerfValley2'`, como hace `quest_entering_perf.ps1`.
- **La capa viva del valle cuesta 0 si el preshader pliega.** Control barato: FONDO de esta sesión contra la del APK anterior sin capa viva (si existe); o en el editor, las estadísticas del material (paso V3).
- **Ruido real y balanceo (primero, paso S3):** con el visor puesto y el sensor en la panza, Beltrán retiene 10 s mientras la PC manda 40 veces `ke * AirDbg` (cada 0,25 s); después se balancea e inclina sin respirar 10 s, con otros 40. De las líneas `AIRE DBG v …` del logcat: std y p99 de `v` en cada tramo. **Si std(v) > 0,033/s** (el p99 pasaría de `VelEnter`): `VelEnter` = 3 × std, `VelStay` = 0,4 × `VelEnter` (en la instancia).
- **Orden en el visor con Beltrán:** (1) el aliento solo (`bLive` false en el CDO del valle) con `AirAmount` 0,3, después 1; (2) la sombra (`FogBreath`/`GlowBreath`/`WarmBreath` en 0, `ShadowBreath` 1); (3) la bruma y el resplandor. Una capa entra cuando la anterior se lee viva sin distraer. (Cada cambio de CDO pide re-empaquetar: si se quiere iterar en el visor sin re-empaquetar, la tanda 2 puede sumar eventos `ke` para las familias.)

---

## 9. Riesgos

| Riesgo | Probabilidad | Mitigación / detección |
|---|---|---|
| El ruido real del sensor es mayor que el modelado (> 0,06) y la pausa "respira" | media | S3 lo mide con `AirDbg`; `VelEnter`/`VelStay`/`VelTau` en la instancia (regla de la §3) |
| El balanceo postural (la señal es la distancia cámara-sensor) se lee como respiración | media | S3: balanceo sin respirar; mismas perillas; si no alcanza, tanda 2: descontar la velocidad de la cabeza |
| La inhalación sigue leyéndose débil o como polvo | media-baja (el foco la mejoró en el modelo) | §4.8: `InAlpha`, `InFocus`, `InTilt`, `FocusTilt` en la MI; estéreo en el visor. Si no alcanza: estela corta en el PS (tanda 2) |
| Las motas se leen como "partículas de videojuego" | media | tamaño y contraste bajos por defecto; primera prueba con `AirAmount` 0,3 |
| El aire se apaga demasiado con movimientos de cabeza normales | baja | balanceo sentado de ±2° (hasta ~4°/s) no lo toca; `TurnFade0`/`TurnFade1` en la instancia |
| Mareo o incomodidad por motas cercanas (vergencia a 40-55 cm) | baja | reglas de §4.3 medidas; `NearFull` 45; botón de pánico `AirAmount` 0 / `bAir` false en la instancia |
| La capa viva del valle no se percibe | media | es sutil a propósito (§6.5); familias a 2 sin tocar código |
| El brillo del resplandor se lee como una banda que sube y baja | baja-media | `GlowBreath` 0,5 (§6.5) |
| El aire tapa el panel de instrucciones (sort 20 > HUD 0) | baja | el aire vive debajo de −4°, el panel a la altura de los ojos; verificar en el visor |
| El preshader no pliega (costo por píxel) | baja | V3 (estadísticas) y banco; costo acotado a ~0,1 ms |
| `AdditionalOutputs` / `Inputs` del Custom no se escriben con esa capitalización | baja | el script devuelve el error en `log`; probar `additionalOutputs` (gotcha 446) |
| Un `type_id` del DSL no existe con ese nombre (`NormalizeAxis`, `GetForward/Right/UpVector` de Rotator, `TransformLocation`/`InverseTransformDirection`, `GetWorldTransform`, `AttachComponentToComponent`, `Actor\|Tick\|AddTickPrerequisiteActor`, `SetHiddenInGame`, `SetCollisionEnabled`, `GetWorldDeltaSeconds`, `ToString(Float)`, `Append`, `Set…ParameterValueonMaterials`) | media | `find_node_types` ANTES de escribir (V7, E9); el `write` aborta sin dejar nodos a medias; corregir el nombre en el `.dsl`, re-correr `dsl_sim.py` y re-escribir esa función (vacía) |
| Una función impura inline como argumento de datos (pin desconectado sin error) | baja (el lint de `dsl_sim.py` lo prohíbe; el `SetRig` de la rev. 1 lo tenía) | E10: `get_node_infos` del `SetRig` y de cada llamada propia con argumentos |
| Una llamada propia con argumento cae en el pin `self` | media (conocida) | todas por keyword; `get_node_infos` después (gotchas 461, 654) |
| El lightmap UV pisa una capa de semillas al importar | baja | `LightMapCoordinateIndex` ≥ 4 (E2); si no, desactivar `bGenerateLightmapUVs` y reimportar |
| La vista previa del valle no cambia nada en el editor (MIDs viejos) | alta si se saltea V12b | recargar el nivel (V12b) |
| La vista previa del CS aparece en PIE | nula | `AirReset` en `BeginPlay` pone todo en 0 y oculta (gotcha 358); `PreviewBreath` del valle en 0 antes de empaquetar |
| El aire queda colgado en el nivel sin rig (galería) | nula | sin rig no se monta y no dibuja (verificado en `dsl_sim.py`) |
| Dos sesiones editan `BP_BreathValley_SC` a la vez (hoy ya pasó: `ApplyLook`) | media | P6: confirmar antes de V5; regla §8 de `CLAUDE.md` |
| Otra sesión ve errores transitorios de compilación del material mientras se recablea | alta, inocua | gotchas 471/479: avisar; juzgar solo el log después del `recompile` |

---

## 10. Rollback a la v2

| Qué | Cómo |
|---|---|
| Apagar la capa viva del valle sin tocar el material | `bLive` false en el CDO de `BP_BreathValley_SC` → en ~5 s (`LiveTau`) empuja los neutros exactos → la v2 (con el look actual) |
| Volver el material del valle a la v2 | pegar `VR_Test/Saved/ClaudeScripts/aliento/rollback_valle_v2/apply_valley_material_A_v2.py` y después `_B_v2.py` (son los scripts actuales con el plan del **respaldo** `valle_v2_aplicada_backup/valley_build.json`; probados en `dryrun_material_script.py rollback`: cada entrada del PS vuelve a la v2 exacta aunque los `Live*` sigan respirando) → `recompile` → borrar con `delete_expression` lo que el A lista en `sobrantes` (los 11 parámetros) y en `helpers_sobrantes` (los 14 helpers `M_*`, `X_*`, `T_*`). 🔴 **No** usar los `apply_valley_material_A/B.py` que están DENTRO de `valle_v2_aplicada_backup/`: leen la ruta viva de `valley_build.json`, que ya tiene la capa viva. O restaurar el `.uasset` del respaldo P4 con el editor cerrado |
| Quitar las funciones del valle | borrar los 2 nodos de cirugía (Tick y CS) **primero**, después las 4 funciones (gotcha: borrar una función con llamadores puede colgar el editor), compilar |
| Apagar el aliento | `AirAmount` 0 o `bAir` false en la instancia; ocultar el actor; o borrarlo (lo hace Beltrán o se pregunta: sacar actores se pregunta) |
| Todo | restaurar con el editor cerrado: los `.uasset` de P4 (`capa_viva_backup/`, el valle **antes** de la capa viva) o los de `capa_viva_backup/post_valle/` (el valle **con** la capa viva + `Test_Entering.umap`, copiados después de la fase V, antes de E/T). 🔴 **Git NO sirve de rollback acá:** `VR_Test/Content/Test_Entering.umap` y toda la carpeta `Mechanics/Breath/Valley/` están **sin versionar** (`git status` = `??`, verificado el 2026-09-28); `git checkout` no los recupera. El `.umap` de **antes** de la fase V no tiene respaldo propio: lo único es el autoguardado `Test_Entering_Auto6.umap` de las 15:54 (copiado como `capa_viva_backup/Test_Entering_Auto6_pre_fase_15-54.umap`). Lo que cree la fase E (`Mechanics/Breath/Air/`) también nace sin versionar: su rollback es borrar la carpeta y el actor (sacar actores se pregunta). Si Beltrán quiere git como red, que commitee el valle y el nivel antes de E |

---

## 11. RECETA PARA EL EDITOR (paso a paso)

**Reglas de la sesión:** `toolset_name` con el path completo (`editor_toolset.toolsets.blueprint.BlueprintTools`, …; `EditorToolset.EditorAppToolset`, `EditorToolset.LogsToolset`). Todo `execute_tool_script` con la plantilla `scripts/safe_script.py` (try/except `BaseException`, nunca levanta). **Canario** antes y después de cada tanda de scripts. **Nunca** compilar con PIE corriendo. Guardar **con rutas explícitas** (nunca `save_assets([])`: hay otros agentes). Rutas de disco absolutas: `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/...`.

### P — Preparación (15 min)
- **P1.** `SceneTools.get_current_level` → `/Game/Test_Entering`. Si es otro: `AssetTools.is_dirty` del abierto; si está sucio, NO cambiar de nivel (es de otro agente).
- **P2.** `EditorToolset.EditorAppToolset.IsPIERunning` → false.
- **P3.** Canario: script con `SceneTools.find_actors({name:"", tag:"", collision_channels:[]})` que cuente los `refPath` con `Test_Entering.Test_Entering:PersistentLevel.` (el tracker del valle dice 15 actores; anotar el número real). Repetirlo al final de cada tanda.
- **P4.** Respaldo (PowerShell, no MCP): copiar `VR_Test/Content/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC.uasset`, `MI_BreathValley_SC.uasset` y `BP_BreathValley_SC.uasset` a `VR_Test/Saved/ClaudeScripts/capa_viva_backup/`, **y también `VR_Test/Content/Test_Entering.umap`** (el nivel no usa actores externos: el `.umap` es todo). 🔴 Este respaldo es la **única** red: el nivel y la carpeta del valle están sin versionar en git (§10).
- **P5.** En disco (desde `.claude/skills/unreal-vr/scripts/`): `python plan_valley_material.py`, `python plan_breath_air_material.py`, `python hlsl/Valley_check.py`, `python hlsl/BreathAir_check.py`, `python dsl_sim.py`, `python dryrun_material_script.py` → todos **TODO OK**.
- **P6. Coordinación (obligatorio).** Otra sesión agregó hoy (16:00-16:03) `ApplyLook` y 36 perillas a `BP_BreathValley_SC` y vació los overrides de `MI_BreathValley_SC`. Antes de V2: preguntar a Beltrán si alguna sesión sigue editando `BP_BreathValley_SC`, `M_BreathValley_SC` o `MI_BreathValley_SC` (regla §8 de `CLAUDE.md`: nunca dos a la vez sobre el mismo `.uasset`). Si sí, esperar.

### V — El valle respira (45 min)
- **V1. Captura de control ANTES.** Script: `EditorAppToolset.CaptureViewport({captureTransform:{location:{x:0,y:0,z:120}, rotation:{pitch:-2,yaw:0,roll:0}, scale:{x:1,y:1,z:1}}, annotations:[], bShowUI:false})` (ajustar al ojo real: la posición del `PlayerStart` + 120 cm) → volcar `image.data` con `AssetTools.write_file` a `VR_Test/Saved/ClaudeScripts/capa_viva/v1_antes.txt` (base64) → decodificar en disco. Dos capturas separadas unos segundos: su diferencia es el ruido del oleaje (el cielo y el piso cercano deben dar 0).
- **V2.** Avisar a las otras sesiones (gotcha 471: el recableado deja errores transitorios en el log). Pegar **entero** `scripts/apply_valley_material_A.py` como `script` de `ProgrammaticToolset.execute_tool_script`. Esperado: `params_creados` 11, `params_total` 82, `sobrantes` [], `helpers_sobrantes` [], `vivas` = las 9 entradas (`FogDist`, `GlowAmt`, `GlowPow`, `HFogDist`, `HFogFall`, `ShadowSoft`, `ShadowStrength`, `ShadowTint`, `SkyHorizon`), `log` []. Después **entero** `apply_valley_material_B.py`: `ValleyPS` 44/44, `ValleyHeightVS` 29/29, `ValleyGradVS` 31/31, `internas_ok` 3, `log` []. Si el log dice que `ConstB` no se pudo escribir en un `T_*`: ver el nombre real con `get_properties` del helper y re-pegar (idempotente). Canario.
- **V3.** Anotar las líneas del log (`wc -l VR_Test/Saved/Logs/VR_Test.log`), `MaterialTools.recompile({material_or_function:{refPath:"/Game/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC.M_BreathValley_SC"}})`, y grepear SOLO lo nuevo después de la línea `Dispatching toolset tool: '...MaterialTools.recompile'` por `Failed to compile|missing input|error` → nada de `M_BreathValley_SC` (gotcha 479). Opcional (Beltrán, UI): *Stats* del material: las instrucciones del pixel shader iguales a antes (el preshader plegó).
- **V4.** Una captura descartable (gotcha 476) y la captura **DESPUÉS** con el mismo `captureTransform`. Control negativo: cielo y piso cercano **idénticos**; el resto dentro del ruido de V1.
- **V5. BP del valle — leer antes de tocar:** `BlueprintTools.list_variables` + `read_graph_dsl` de `:EventGraph` y `:UserConstructionScript`. Anotar: el nodo `StepShadow` del Tick y a qué va su `then`; la cadena del CS (`… → PushShadow → ApplyLook`) y si `ApplyLook.then` está libre. Leer del CDO (`Default__BP_BreathValley_SC_C`) `FogStart`, `FogDist`, `FogMax`, `HFogDist`, `HFogFall`, `MorphAmt`, `GlowAmt`, `SkyHorizon`: si difieren de la §6.2, re-correr en disco `render_valle_live.py` (con esos valores) y `comparar_valle_live.py`, y anotar los números nuevos en la §6.5.
- **V6. Variables:** `add_variable` ×11 (`bLive` bool; `LiveAmount`, `FogBreath`, `GlowBreath`, `ShadowBreath`, `WarmBreath`, `LiveTau`, `PreviewBreath`, `LiveS`, `LiveSig`, `LiveGate` float) → `set_variable_category` `L-Respira` a cada una → `compile_blueprint` → `ObjectTools.set_properties` en el CDO: `bLive` true, `LiveAmount` 1, las 4 familias 1, `LiveTau` 1 → `get_properties` para verificar → `compile_blueprint`. **No** marcarlas instance-editable.
- **V7. Funciones:** `add_function_graph` `LiveMPC`, `PushLive`, `StepLive`, `PreviewLive`; `add_function_param({graph: <PushLive>, param_name:"S", param_type:"float", input_param:true})` → compilar. `find_node_types` en `PushLive`/`StepLive` para `Variables|L-Respira|GetLive` (bool sin la b), `Math|Float|Lerp`, `Rendering|Material|SetScalarParameterValueonMaterials` (el de MeshComponent, "on" minúscula: gotchas 460, 2258) y `Utilities|Time|GetWorldDeltaSeconds`.
- **V8.** `write_graph_dsl` de cada bloque de `scripts/valley_live.dsl`, en orden: `LiveMPC`, `PushLive`, `StepLive`, `PreviewLive`. Después de cada uno: `read_graph_dsl` (que el cuerpo esté entero; que los literales negativos de los `Lerp` sigan negativos) y, en `StepLive`/`PreviewLive`, `get_node_infos` del `CallFunction|PushLive`: `self` = *Self Object Reference* y `S` conectado.
- **V9. Puente `LiveMPC`** (gotcha 291; el getter de colección es IMPURO): en el grafo `LiveMPC`, dos `create_node({graph, type_id:"Rendering|Material|GetScalarParameterValue", pos, declaring_class:{refPath:"/Script/Engine.KismetMaterialLibrary"}})` → la clase del nodo tiene que ser `K2Node_CallMaterialParameterCollectionFunction` (pines `Collection`/`ParameterName`/`ReturnValue`). `set_pin_value`: `Collection` = `/Game/SoulCharger/Mechanics/Breath/MPC_Breath.MPC_Breath`; `ParameterName` = `Signed` y `On`. Exec: `break_pins` entrada→`SetLiveSig`; entrada → Get(Signed) → Get(On) → `SetLiveSig` → `SetLiveGate`. Datos: `ReturnValue` de cada Get → el pin de valor de su Set (reemplaza el literal 0). Verificar con `get_node_infos`.
- **V10. Cirugía del Tick:** `create_node` `CallFunction|StepLive` en `:EventGraph` → `connect_pins` `StepShadow.then` → `StepLive.execute`; si `StepShadow.then` iba a otro nodo X, `break_pins` y `StepLive.then` → X (gotcha 338: el exec de entrada acepta varias conexiones). `get_node_infos` del nodo nuevo.
- **V11. Cirugía del CS:** `create_node` `CallFunction|PreviewLive` en `:UserConstructionScript` → `connect_pins` **`ApplyLook.then`** → `PreviewLive.execute` (el final de la cadena; `PushLive` y `ApplyLook` escriben parámetros distintos: el orden no cambia el resultado). Si `ApplyLook.then` iba a algo, insertarlo en el medio con `break_pins`. Ojo: `read_graph_dsl` rotula el nodo de `ApplyLook` como `Class|BPOrbDirectorSC|ApplyLook` (colisión de nombres, tracker del valle): es el propio.
- **V12.** `compile_blueprint({warnings_as_errors:true})` → 0 errores. Canario. `AssetTools.save_assets(["/Game/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC", "/Game/SoulCharger/Mechanics/Breath/Valley/BP_BreathValley_SC"])` → `is_dirty` false de los dos.
- **V12b. Recargar el nivel** (MIDs viejos, §6.6): `AssetTools.is_dirty("/Game/Test_Entering")` → si está sucio, NO (preguntar); si no, `SceneTools.load_level("/Game/Test_Entering")` → canario igual que en P3.
- **V13. Vista previa:** CDO `PreviewBreath` −1 → compilar → captura desde el ojo (horizonte más tibio y brumoso, resplandor más bajo, sombra más clara con el borde en el mismo lugar); +1 → captura (colinas más recortadas, resplandor más intenso, sombra más densa); **0** → captura = V4. Dejar `PreviewBreath` en 0, compilar, guardar.

### E — El aliento visible (75 min)
- **E1.** `AssetTools.create_folder("/Game/SoulCharger/Mechanics/Breath/Air")`.
- **E2. Malla:** `StaticMeshTools.import_file({folder_path:"/Game/SoulCharger/Mechanics/Breath/Air", asset_name:"SM_BreathAir_SC", source_file:"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/aliento/SM_BreathAir_SC.fbx", import_materials:false, import_textures:false})` → `get_vertex_count` **8192**, `get_triangle_count` **4096**, `get_bounds` ≈ X −40…170, Y −150…150, Z −130…60 cm → `is_nanite_enabled` false (si no, `set_nanite_enabled` false) → `remove_collisions` → `ObjectTools.get_properties(SM, ["LightMapCoordinateIndex"])` **≥ 4** (el lightmap no pisa UV1-UV3). La V invertida no importa (semillas invariantes, §5.1).
- **E3. Material:** pegar **entero** `scripts/apply_breath_air_material.py` → esperado: `flags` = Unlit / AlphaComposite / two-sided / sin niebla; `params.creados` 41; `customs` `BreathAirVS` 45/45 y `BreathAirPS` 3/3; `internas_y_salidas_ok` "5 de 5"; `mi_creada` true; `log` []. Canario. Si el `log` dice que `AdditionalOutputs` no se pudo escribir, cambiar la clave a `additionalOutputs` (gotcha 446) y re-pegar (es idempotente). `recompile` + log como en V3 (nada de `M_BreathAir_SC`).
- **E4.** `StaticMeshTools.get_material_slots(SM)` → `set_material(SM, <slot>, MI_BreathAir_SC)`. Guardar SM, M, MI (rutas explícitas).
- **E5. BP:** `BlueprintTools.create({folder_path:"/Game/SoulCharger/Mechanics/Breath/Air", asset_name:"BP_BreathAir_SC", asset_type:{refPath:"/Script/Engine.Actor"}})`.
- **E6. Componentes** (tabla §5.5): `get_default_object` → `ActorTools.add_component` ×3 (`/Script/Engine.StaticMeshComponent`: `AirMesh`, `HeadGhost`, `MouthGhost`) → en cada plantilla `<Comp>_GEN_VARIABLE`, **una propiedad por `set_properties`** (gotcha 478): `staticMesh`, `overrideMaterials` `[{"refPath":".../MI_BreathAir_SC.MI_BreathAir_SC"}]`, `BodyInstance` `{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}`, `castShadow` false, `translucencySortPriority` 20; en los fantasmas `relativeLocation`/`relativeScale3D` **como texto** `"(X=-8.5,Y=0,Z=2.5)"` (el JSON escribe solo la primera componente, gotchas.md línea 2261), `bHiddenInGame` true (**no** `bIsEditorOnly`: `AirReset` los usa en el APK). Verificar con `get_properties`.
- **E7. Variables:** las de la tabla 5.4 (`A-Aliento`, `B-Prueba`; instance-editable con `set_variable_instance_editable({variable_name, instance_editable:true})`) y las de la tabla 5.5 (`Z-Aliento`, no editables; `MouthW` tipo Vector, `CamXf` tipo Transform, `PerfMode` int, `Rig` con `add_object_variable(bp, "Rig", "/Game/SoulCharger/Mechanics/Breath/BP_BreathRig_SC.BP_BreathRig_SC_C")`). `compile_blueprint` → defaults del CDO según la tabla 5.4 (`bAir` true, `AirAmount` 1, …, `PreviewAirT` 0,35) → verificar → compilar.
- **E8. Funciones:** `add_function_graph` `AirMPC`, `PushAir`, `AirReset`, `AirStep`, `AirPerf`, `AirVisible`, `AirMountCam`, `AirMount`, `AirTick`, `PreviewAir`; `add_function_param` `DT` (float, entrada) en `AirStep` y `AirTick` → compilar.
- **E9. `type_id` a confirmar con `find_node_types`** (en `AirStep` o `PushAir`) ANTES de escribir: `Math|Rotator|NormalizeAxis`, `Math|Rotator|MakeRotator` (pines Roll/Pitch/Yaw por keyword, gotcha 297), `Math|Vector|GetForwardVector`/`GetRightVector`/`GetUpVector` (los de Rotator), `Math|Transform|TransformLocation`, `InverseTransformLocation`, `InverseTransformDirection`, `Transformation|GetWorldTransform`, `Transformation|AttachComponentToComponent`, **`Actor|Tick|AddTickPrerequisiteActor`** (si no aparece, probar `Actor|AddTickPrerequisiteActor`), `Rendering|SetHiddenInGame`, `Collision|SetCollisionEnabled`, `Math|Color|MakeColor`, `Rendering|Material|SetColorParameterValueonMaterials`, `Rendering|Material|SetVectorParameterValueonMaterials` ("on" minúscula), `Utilities|String|Append`, `Utilities|String|ToString(Float)`, `Class|BPBreathRigSC|GetCamRef`, y los getters de bools sin la `b` (`Variables|A-Aliento|GetAir`, `Variables|Z-Aliento|GetMounted`, `GetPrimed`, `GetOnset`, `GetLagInit`). Si un nombre difiere, corregirlo en el `.dsl`, re-correr `dsl_sim.py` (si el nombre cambia, agregarlo a `NATIVOS`) y recién ahí escribir.
- **E10. Escribir** cada bloque de `scripts/breath_air.dsl` en el orden del archivo (`AirMPC` → … → `PreviewAir` → `ConstructionScript` en `:UserConstructionScript` → `EventGraph`). En el `EventGraph` de un BP nuevo, **borrar antes los 3 eventos fantasma** (`find_nodes({graph, title:"", entry_points_only:true})` → `delete_node`). Después de cada `write`: `read_graph_dsl`; en cada `CallFunction|X` con argumentos (`AirStep :DT`, `AirTick :DT`), `get_node_infos`: `self` = *Self Object Reference*, `DT` conectado. En `AirMount`, **`get_node_infos` del `SetRig`: el pin de valor tiene que tener `connected_pins` no vacío** (viene del `GetActorOfClass`). En `AirMountCam`, `get_node_infos` del `AttachComponentToComponent`: el `self` alimentado por `AirMesh`, `Parent` por la cámara (gotchas.md línea 2522).
- **E11. Puente `AirMPC`:** igual que V9, con `SetAirSig` (`Signed`) y `SetAirGate` (`On`).
- **E12.** `compile_blueprint({warnings_as_errors:true})` → 0 errores. Canario. Guardar el BP.
- **E13. Colocar** (colocar actores sí; sacarlos se pregunta): `SceneTools.add_to_scene_from_asset("/Game/SoulCharger/Mechanics/Breath/Air/BP_BreathAir_SC", "Entering_Aire", <xform>)` → **el transform no se aplica al colocar**: `ActorTools.set_actor_transform` con la ubicación de los ojos del usuario sentado (`PlayerStart` X/Y, Z ≈ 120; leer el `PlayerStart` con `find_actors` + `get_actor_transform`) y el yaw del `PlayerStart` → `SceneTools.set_actor_folder(actor, "Entering")`. Diff instancia vs plantilla (gotcha 478) en `AirMesh` de la instancia: `staticMesh`, `overrideMaterials`, `translucencySortPriority` 20, colisión. Canario (+1 actor). Guardar el nivel con ruta explícita (`/Game/Test_Entering`).
- **E14. Vista previa desde el ojo:** en la instancia `PreviewBreath` 0,8 (re-corre el CS) → `CaptureViewport` con `captureTransform` = la transform del actor → **positivo:** motas en la banda baja, repartidas a los dos lados y juntándose hacia el centro (como en `aliento_primera_persona.png`). `PreviewBreath` −0,8 → **la pluma centrada bajo el eje de la vista** (simétrica izquierda/derecha), por debajo del metaball. Si la pluma sale corrida hacia arriba o de costado, o el volumen de inhalar sale con otra densidad: revisar las capas UV de `SM_BreathAir_SC` (orden UV0-UV3, lightmap). **Negativo:** `PreviewBreath` 0 → captura igual a la del actor oculto. Volver `PreviewBreath` a 0.

### T — PIE (20 min)
- **T1.** `save_assets` (rutas explícitas) → `StartPIE({bSimulate:false, playMode:"PlayMode_InViewPort", warmupSeconds:16})`.
- **T2.** `LogsToolset.GetLogEntries({pattern:"AIRE:"})` → `AIRE: listo…` y, cuando el rig tenga la cámara, `AIRE: montado…` (una vez). `GetLogEntries({pattern:"Accessed None"})` → nada de `BP_BreathAir_SC` ni `BP_BreathValley_SC`.
- **T3.** Respiración falsa **en la instancia de PIE** (no en la del editor): `find_actors` en el mundo de PIE → `set_properties` en `…/UEDPIE_0_Test_Entering.Test_Entering:PersistentLevel.<rig>`: `bFakeBreath` true (y `bEnabled` true si la etapa todavía no activó el rig).
- **T4.** Seis lecturas cada ~2 s de la instancia PIE del aire (`bMounted`, `Glob`, `GlobBase`, `MoveFade`, `Flow`, `VelF`, `Ein`, `Eout`, `Tin`, `Tout`, `RateBpm`, `YawLag`) y del valle (`LiveS`). Esperado: `bMounted` true, `Glob` ≈ 1, `Flow` alterna +1/0/−1/0 con la respiración falsa, `Tin` avanza al inhalar y queda quieto al retener, `RateBpm` ≈ el ritmo de `bFakeBreath`, `LiveS` oscila entre ~−1 y +1 (con un retraso de ~1 s).
- **T5. Lo que ve el juego:** el FOV vertical de PIE es ~41° y las motas viven de −4° a −40°: bajar la cámara 20° (`set_properties` de la `Camera` del pawn de PIE, `RelativeRotation` como texto `"(Pitch=-20,Yaw=0,Roll=0)"`, gotcha 469) → `CaptureEditorImage` (receta de captura del juego) en una inhalación y en una exhalación → motas en la mitad baja. Después `"(Pitch=-20,Yaw=30,Roll=0)"` → leer `MoveFade` en seguida (≈ 0: el aire se apagó por el giro) y a los ~1,5 s (≈ 1) → captura: lo inhalado sigue entrando abajo al centro.
  - 🔴 **Corrección de la fase T (2026-09-28):** `set_properties` sobre la `Camera` del pawn de PIE re-corre el Construction Script del pawn y **despega `AirMesh`** de la cámara (gotcha 488). Girar con **`ActorTools.set_actor_transform` sobre el pawn** de PIE, y medir con una traza por cuadro dentro de un `execute_tool_script` (cada llamada = un cuadro). Resultados en el tracker `BP_BreathAir_SC.md`.
- **T6. Banco en PIE:** `set_properties` de la instancia PIE del aire: `PerfMode` 1 → `AirMesh` invisible; 2 → las dos corrientes llenas; 0 → normal. En la consola de PIE, `ke * AirDbg` → una línea `AIRE DBG v … modo … S …` en el log.
  - 🔴 **Corrección de la fase T:** `PerfMode` no es instance-editable y `set_properties` lo rechaza en PIE (*"could not be set"*); el MCP tampoco manda comandos de consola (gotcha 441). T6 quedó sin correr: `PerfE5/E6/E0` y `AirDbg` se prueban en la Quest (S2/S3). Sustituto parcial hecho: `bAir` false → `AirMesh` oculto a los 3,8 s (el camino de costo 0 de `AirVisible`).
- **T7.** `StopPIE`. **Simulate:** `StartPIE({bSimulate:true, playMode:"PlayMode_Simulate", warmupSeconds:8})` → sin pawn: no aparece `AIRE: montado`, cero `Accessed None` → `StopPIE`.
- **T8.** Canario; `is_dirty` de lo tocado; guardar con rutas explícitas.
- **T9.** Actualizar trackers (`BP_BreathAir_SC.md`, `BP_BreathValley_SC.md`, `_INDEX.md`), `references/assets-existentes.md` (el aliento como mecánica reusable) y `docs/MECANICAS-PORTABLES.md` (una ficha: el aire necesita el rig en el nivel). **No commitear sin pedido.**

### S — Paquete, banco y visor (con Beltrán)
- **S1.** Antes del cook (gotcha 474): `PreviewBreath` 0 en el CDO del valle y en la instancia del aire; `save_assets` con las rutas tocadas, `is_dirty` false, mtime de cada `.uasset` anterior al cook. Empaquetar Development (receta UAT de `docs/WORKFLOW-EQUIPO.md`).
- **S2.** `scripts/quest_entering_perf.ps1 -Modos 0,4,5,6` → `resumen.txt`: FONDO, AIRE y CPU del peor núcleo (§8).
- **S3.** Visor. **Primero el ruido real** (§8): con la app abierta y el casco puesto, desde PowerShell: `1..40 | % { & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell "am broadcast -a android.intent.action.RUN -e cmd 'ke * AirDbg'"; Start-Sleep -Milliseconds 250 }` mientras Beltrán retiene; otra vez mientras se balancea sin respirar; `adb logcat -d | findstr "AIRE DBG"` → std de `v` por tramo → ajustar `VelEnter`/`VelStay` si hace falta. **Después**, capa por capa (§8). Primeras perillas si algo no se lee: §4.8 (inhalación), `FogBreath`/`GlowBreath`/`WarmBreath` (valle).

---

## 12. Segunda tanda (opcional, en este orden)

| Orden | Efecto | Qué hace | Cómo (sobre lo de la tanda 1) | Costo |
|---|---|---|---|---|
| 1 | **E — el mundo contiene el aire** | en las pausas se detienen la luz que viaja por el llano y el oleaje lejano | reloj del valle integrado `ValleyT += Dt·Rate` (Rate ≤ 1, 0,15 en las pausas, rampa τ ~1 s) como **entrada nueva** de los dos VS en lugar de `View.GameTime`: circuito completo del valle (HLSL + `Valley_check.py` + cota de velocidad ≤ 0,451°/s: frenar nunca acelera). Puede leer el `Flow` del aire | ~0 |
| 1 | **F — el aire suena** | pasabajos del ambiente, hálito al exhalar (ganancia por duración), casi silencio en las pausas | MetaSound con `Set Float Parameter` desde `AirStep` (ya tiene `VelF`, `Flow`, `Ein`, `Eout`) | 0 GPU; toca Config compartida (coordinar) |
| 2 | **G — el eco llega al horizonte** | una franja de luz tenue nace a 45 m al exhalar y viaja a velocidad angular ≤ 0,45°/s | gaussiana radial en la rama lejana de `ValleyPS` (circuito completo) | 0,04-0,1 ms |
| 3 | **H + I — coherencia, paleta y luna** | respirar con el pacer aclara el aire y lleva la paleta hacia el rosa en minutos; la luna se llena y nunca retrocede | `Sync` (§3) en `BP_BreathStage_SC`; `Live*` nuevos (`LiveHue`, `LiveMoon`) por el mismo camino de preshader | 0 |
| 4 | **J — el valle emerge** | la bruma de base se aclara a lo largo de la etapa | `Charge` monótono → `LiveFogDist` base | 0 |
| 5 | **K — el aire lejano** | motas de 2-12 m visibles solo dentro del resplandor | tercera corriente de la MISMA malla (UV3.x = 2) | 0,05-0,12 ms |
| — | **Capa A del aire** | sin respiración detectada, el aire sigue al pacer, tenue | `AirSig` = lerp(pulmón del pacer, `Signed`, `On`) — el stage pasa el pacer | ~0 |
| — | **Descontar el balanceo** | si S3 muestra que el balanceo postural se lee como respiración | restar de `Vel` la parte correlacionada con la velocidad de la cabeza (el aire ya la calcula: `TurnRate`) | ~0 |
| — | **Iterar en el visor sin re-empaquetar** | perillas del aire y del valle por consola | eventos `ke` (`AirAmt0..3`, `LiveFam…`) como los del banco | 0 |

---

## 13. Lo hecho en disco y los chequeos corridos (2026-09-28, rev. 2)

**Archivos nuevos:**

| Archivo | Qué |
|---|---|
| `docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md` | este plan (las tablas 5.3 y 5.4 las leen el planificador y el verificador) |
| `.claude/skills/unreal-vr/scripts/breath_air_model.py` | modelo de referencia del aliento (VS con foco, PS, BP con histéresis/latch/giro/presencia suave, preview, seguidor del rig, `encode_uv`/`decode_uv`/`flip_v`, `BellyNoisy` = la señal real) |
| `.claude/skills/unreal-vr/scripts/hlsl/BreathAirVS.hlsl`, `BreathAirPS.hlsl` | los dos Custom del material del aire (VS: 45 entradas) |
| `.claude/skills/unreal-vr/scripts/hlsl/BreathAir_check.py` | verificador: estático, dxc/fxc/SPIR-V, HLSL = modelo (con las UV codificadas), controles, 13 mutaciones, V invertida (+ control negativo) |
| `.claude/skills/unreal-vr/scripts/gen_breath_air.py` | malla (Blender headless) con las semillas codificadas + verificación por reimportación |
| `.claude/skills/unreal-vr/scripts/plan_breath_air_material.py` | plan de armado del material del aire → `breath_air_build.json` |
| `.claude/skills/unreal-vr/scripts/apply_breath_air_material.py` | script de Unreal que arma `M_BreathAir_SC` + `MI_BreathAir_SC` (idempotente) |
| `.claude/skills/unreal-vr/scripts/breath_air.dsl`, `valley_live.dsl` | los grafos nuevos, listos para pegar |
| `.claude/skills/unreal-vr/scripts/dsl_sim.py` | intérprete del DSL: ejecuta los `.dsl`, los compara con los modelos (también con ruido real y con el `Retire`) y tiene un **lint** de funciones impuras inline |
| `.claude/skills/unreal-vr/scripts/dryrun_material_script.py` | corre los scripts de armado de material contra un editor simulado (también el rollback) |
| `.claude/skills/unreal-vr/scripts/sim_breath_air.py` | confort, señal real, ritmo, giro, legibilidad, distancias, pluma/metaball, mirada abajo, píxeles, costo y previsualizaciones |
| `.claude/skills/unreal-vr/blueprints/BP_BreathAir_SC.md` | tracker (planificado) |
| `VR_Test/Saved/ClaudeScripts/aliento/` | `SM_BreathAir_SC.fbx` (rev. 2), `breath_air_build.json`, renders del valle con el look actual (`respira` −1/0/+1 y sin capa viva), comparación, previsualizaciones del aliento, GIF, `sim_aliento_resultados.txt`, envoltorios, `rollback_valle_v2/` (los dos scripts de rollback) |

**Archivos modificados (aditivos; con los `Live*` neutros todo es la v2):**

| Archivo | Cambio |
|---|---|
| `scripts/hlsl/ValleyPS.hlsl` | solo la cabecera: 9 fuentes `preshader Mul/Mix/Tint` + nota (el código es el mismo; `ShadowRadius` y `GlowHeight` como en la v2) |
| `scripts/valley_model.py` | 11 parámetros nuevos (neutros), `efectivos()` (con `Tint`), `live_desde_S()`, `live_paso()`, `LIVE_CIELO` |
| `scripts/plan_valley_material.py` | fuentes `preshader Mul(A, B)`, `Mix(A, B, T)`, `Tint(A, B, T)` |
| `scripts/apply_valley_material_A.py` / `_B.py` | helpers y cableado de `mul`/`mix`/`tint`; el A lista `helpers_sobrantes` |
| `scripts/hlsl/Valley_check.py` | sección 3e "capa viva" (6 chequeos) |
| `scripts/preview_breath_valley.py` | opciones `respira=S` y `carpeta=` |
| `scripts/quest_entering_perf.ps1`, `resumen_entering.py` | modos 5 y 6 (con la nota del fondo), la fila `AIRE (m5 - m6)` y el CPU del peor núcleo; los defaults no cambian |
| `docs/PLAN-VALLE-ENTERING-2026-09-27.md` | tabla 7.1: 11 filas nuevas (82 parámetros) + nota de la capa viva |
| `scripts/hlsl/Valley_CABLEADO.md` §10, `blueprints/BP_BreathValley_SC.md` | la capa viva (planificada) |
| `VR_Test/Saved/ClaudeScripts/valley_build.json` | regenerado (82 parámetros, 9 fuentes nuevas). El respaldo `valle_v2_aplicada_backup/` no se tocó |

**Chequeos (todos TODO OK):**

| Chequeo | Resultado |
|---|---|
| `hlsl/BreathAir_check.py` | **40/40**: cabeceras = modelo = tablas 5.3/5.4; dxc SM6 -WX, fxc SM5, glslc → SPIR-V + spirv-val, PS en half; `[branch]` → DontFlatten; HLSL traducido (con las UV codificadas) = modelo (offset 2,8e-14 cm, 12 estados girados, perillas no default); PS = modelo; neutro = 0 píxeles; confort (≥ 25,5 cm, ≤ −9,1° en la muestra); lo inhalado llega a la boca exacta con el marco girado 30°; la pluma nace a `OutStart`; la cinta salta con alfa 0; **13/13 mutaciones detectadas**; **V invertida: mismas estadísticas**, y la codificación de la rev. 1 invertida sí falla (control negativo) |
| `hlsl/Valley_check.py` | **90/90** (los 84 de la v2 + 6 de la capa viva: ninguna fuente viva en los VS, `ShadowRadius`/`GlowHeight` fuera; neutro bit a bit; respirando = modelo; el plan de armado = respaldo + 11 parámetros + 9 fuentes) |
| `dsl_sim.py` | **35/35**: lint (y su control negativo con la forma de la rev. 1); CS = `preview_push`; `EventTick` = `AirBP` en **5184 cuadros** (giro, mirada al sensor, inclinación) con error 0; con ruido 0,03/0,05 + deriva: = modelo en 8064 cuadros, pausa quieta 100 % / 98,6 %, ritmo 4,30; ritmo 5/6/10 resp/min ± 0,06; escalón del `Retire` sin saltos; banco; `AirDbg`; sin rig; valle: `PushLive`/`StepLive`/`PreviewLive` = `live_desde_S`/`live_paso` en 600 casos, suelo 9 / cielo 3, `Retire` ≤ 0,5 % por cuadro; 4 controles negativos detectados |
| `dryrun_material_script.py` | **29/29**: valle desde vacío y desde la v2 (2 vueltas: idempotente, +25 expresiones, 44/44 entradas, neutro = v2 exacto, respirando = `efectivos()` con `Tint`); rollback (lee el respaldo, v2 exacta con los `Live*` respirando, lista 11 + 14 para borrar); aire (45/45 + 3/3, salidas, TexCoord 0-3, `CamL`, defaults, `Glob` 0, MI) |
| `gen_breath_air.py` | VERIF OK: 8192 v, 2048 polígonos, 4 capas de UV, UV = codificadas (3e-8), caja exacta |
| `preview_breath_valley.py` (look actual) | `respira=0` = sin capa viva: **0 píxeles distintos**; regiones de la §6.5 |
| `sim_breath_air.py` | los números de §4.3-§4.6 |

---

## 14. Decisiones para Beltrán

1. **¿Dónde vive el aliento?** Recomendado: **actor propio `BP_BreathAir_SC`** (el rig aprobado no se toca; §2.2). Alternativa: dentro del rig (las funciones se mudan tal cual).
2. **Sin respiración detectada:** recomendado **nada** (capa viva pura). Alternativa: el aire sigue al pacer, tenue (tanda 2).
3. **La pluma:** nuevo default **por debajo del metaball** (`OutTilt` 18: 5 % de superposición, sin imágenes dobles sobre el objeto que se mira). Variante "tu aliento va hacia el alma": `OutTilt` 12 (22 % encima del metaball, con ~2,7° de disparidad).
4. **Capas del valle:** todas desde que se detecta la respiración (lo construido) o de a una por ciclo (`LiveAmount` desde `BP_BreathStage_SC`, tanda 2).
5. **Colores:** frío entra / tibio sale (propuesto) o uno solo (`OutColor` = `InColor` en la MI).
6. **Si la inhalación no se lee como "entra"** en el visor: primero las perillas de §4.8; si no alcanza, una estela corta en el PS (tanda 2).
7. **Mirar hacia abajo:** con `PitchFollow` 0,75 el aire acompaña cuando el usuario se mira la panza (la pluma conserva el 90 % a −35°). Con 0,5 el aire "se queda en el mundo" y al mirar abajo se esconde (−81 %).
8. **La sombra que respira (D):** ahora solo en densidad (el borde quieto). Si igual distrae: `ShadowBreath` 0.

---

## 15. Qué cambió en la rev. 2 (revisiones de código y de costo/confort)

| Hallazgo (severidad) | Arreglo | Dónde |
|---|---|---|
| Las semillas no resistían la V invertida del importador FBX (alta) | codificación invariante (bandera en U, `(b + 1)/2`), el VS decodifica; FBX regenerado; chequeo con la V invertida + control negativo | §5.1; `breath_air_model.encode_uv`, `BreathAirVS.hlsl`, `gen_breath_air.py`, `BreathAir_check.py` §6 |
| Las pausas se rompían con ruido y deriva realistas (alta) | histéresis `VelEnter`/`VelStay` sobre `VelF` (pasabajos 0,15 s); transporte solo en su modo; señal real simulada (`BellyNoisy`) en el sim, en `dsl_sim.py` y en la calibración | §3, §4.4; `AirStep` |
| El ritmo contaba dos inicios por ciclo y castigaba la respiración lenta (media ×2) | latch `InhMin`: un inicio de exhalación cuenta solo después de ≥ 0,6 s de inhalación | §3, §4.5 |
| El `Retire` del rig hacía saltar el valle y el aire en un cuadro (media) | `LiveTau` en `StepLive`; `GlobTau`, tope `VelMax` y velocidad solo con `On` en el aire; pruebas de escalón en `dsl_sim.py` (+ control negativo) | §3; `valley_live.dsl`, `breath_air.dsl` |
| El plan no registraba `ApplyLook` y sus perillas; bases viejas (media + baja) | bases de la §6.2 del look actual; renders y medidas re-hechos; `PreviewLive` al final del CS (después de `ApplyLook`); P6 coordinación; tinte relativo `BreathTint` | §2, §6, §11 V5/V11 |
| `SetRig` con `GetActorOfClass` inline (media) | `bind` y después `SetRig`; lint en `dsl_sim.py`; `get_node_infos` del `SetRig` en E10 | §5.6, E10 |
| El aire se arrastraba por el mundo al girar la cabeza (media) | `MoveFade` por la velocidad de la cabeza y del marco (6 → 20°/s), baja en el cuadro, vuelve en 0,6 s; el marco alcanza 4× más rápido mientras está apagado | §2.3, §4.3 |
| La pluma se dibujaba sobre el metaball con disparidad (media) | `OutTilt` 12 → 18 (22 % → 5 %) | §5.3, decisión 3 |
| La inhalación se leía como caída y la palanca iba al revés (media) | foco de convergencia (Bézier, `InFocus`/`FocusDist`/`FocusTilt`); `InTilt` 24; palanca corregida (más `InTilt` = menos vertical) | §4.2, §4.8 |
| La sombra que respiraba movía el piso cercano y contradecía su descripción (media) | sin radio; solo densidad y suavidad (±12 % / ±5 %): borde ≤ 0,45°/s, pico más oscuro al inhalar | §6.1-§6.5 |
| `On` mayúscula en `Set…ParameterValueonMaterials`; categoría de `AddTickPrerequisiteActor` (baja) | "on" minúscula en los dos DSL y en `NATIVOS`; `Actor|Tick|AddTickPrerequisiteActor` (+ alternativa en E9) | `.dsl`, E9 |
| Rollback inexacto; scripts del respaldo leían la ruta viva (baja) | `helpers_sobrantes` en el script A; copias `rollback_valle_v2/` con la ruta del respaldo, probadas | §10 |
| Mirar hacia abajo apagaba la pluma (baja) | `PitchFollow` 0,5 → 0,75 (documentado, decisión 7) | §4.1, §5.4 |
| El banco medía el aire con el valle oculto sin decirlo (baja) | documentado en el `.ps1`, el resumen y la §8 | §8 |
| CPU subestimada (baja) | `CamXf` una vez por cuadro; al cielo 3 parámetros en vez de 11; estimación corregida; CPU del peor núcleo en el resumen | §4.6, §8 |
| Centelleo sub-píxel (baja) | piso de tamaño 0,12° → 0,2° con alfa × (físico/dibujado)²: ninguna mota < 2 px | §4.3, §5.3 |
| Vergencia-acomodación (baja) | `NearFull` 36 → 45, `InNear` 30 → 40: alfa de inhalar a < 50 cm 52 % → 40 %; velocidades en plena corriente reportadas | §4.3 |
| La cifra del resplandor (≤ 1°) era falsa (baja) | `GlowHeight` fuera de la capa viva; cifra medida y corregida (mediana 0,64°, hasta 6,2° en el gradiente suave) | §6.2, §6.5 |
