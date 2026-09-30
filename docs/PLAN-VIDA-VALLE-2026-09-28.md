# PLAN — La CAPA DE VIDA del valle de Entering: polvo suspendido + ráfagas de viento · 2026-09-28 (rev. 2)

> **Estado:** todo lo que no necesita Unreal está **HECHO y VERIFICADO en disco** (§14). Lo que necesita el editor es la **receta de la §13**, paso a paso. Nada se tocó en Unreal ni en ningún `.uasset`; nada se commiteó. No se modificó ningún archivo de otra sesión (el valle, el aliento, `dsl_sim.py`, `dryrun_material_script.py`, `preview_breath_valley.py`: se importan, no se editan).
>
> **Viene de** la devolución de Beltrán sobre el valle + el aliento: *"está bastante lindo, pero siento que le falta algo para que se sienta un poco más vivo. No sé si como unas partículas muy pequeñas tipo polvo o ráfagas como un poco de viento… a ver qué se te ocurre."* La propuesta aceptada: **polvo suspendido** + **ráfagas que cruzan el valle** (el polvo se mueve con el viento, una franja de luz recorre el llano, un soplo que viaja de un lado al otro) y, porque suma, **el soplo**: de vez en cuando la ráfaga nace de la exhalación del usuario (idea fuerza *un solo aire*, `IDEAS-RESPIRACION-ENTORNO-2026-09-28.md` §1).
>
> **Rev. 2 (misma fecha):** corrige los problemas de la revisión (§16). Lo principal: el polvo sale del volumen del aliento y cambia de paleta (no se confunde con él); el default pasa a ser el juego **VISIBLE** (Beltrán pidió *más* vida: se baja desde lo visible, no se sube desde lo invisible; el juego sutil queda en la tabla 5.3); la ráfaga **se lleva** el polvo (deriva que después vuelve); el soplo suena **arriba** del tono del pacer; el botón de pánico corta también las ráfagas.
>
> **Números:** los que dicen *modelo* salen de `vida_model.py` (verificado igual al HLSL y al DSL, §14); los costos de GPU son **estimados** y se miden con el banco (§9). Las previsualizaciones NO son el visor (§10).

---

## 0. Resumen en un minuto

- **Qué se ve:**
  - **Polvo suspendido** (siempre): ~255 motas diminutas visibles en la vista (0,2-0,31°), de **1,3 m** a 26 m (nunca dentro del volumen del aliento), que **flotan** (un meandro de periodos 33-75 s, más amplio lejos para que ninguna quede congelada; sin corriente coherente) y **brillan doradas contra la luz baja** del valle (dispersión hacia adelante); las demás quedan como puntos blanco lavanda apenas más claros que el aire. Dejan libre el disco del metaball. Titilan muy lento.
  - **Ráfagas laterales** (cada ~40-70 s, irregulares): un frente de viento cruza el valle de un lado al otro en 28 s y **pasa por el usuario**. Se anuncia por el sonido (un soplo que viene de un lado), **una franja de luz** (+12 niveles) recorre el llano a los costados del metaball (de −3,4 a −1,8° de elevación), y el polvo **se enciende, hace un lazo y queda corrido a favor del viento** (hasta 0,7-1,5 m); en los ~25 s siguientes vuelve despacio a su lugar.
  - **Soplos** (con respiración detectada, uno de cada dos): la ráfaga espera un **inicio de exhalación** y sale **del usuario hacia adelante**: el polvo de adelante (1,3-5 m) se aleja con ella y una franja se va hacia el horizonte, con un siseo que se aleja. Un solo aire en tres escalas.
- **Arquitectura (decidida, §3):** un **actor nuevo `BP_ValleyLife_SC`** con **UN solo reloj de ráfagas**: el mismo estado (frente `s`, trayectoria, envolvente, deriva `Hold`) alimenta el polvo (su malla), la franja (5 parámetros nuevos en el material del valle) y la fuente de sonido (un `AudioComponent` que viaja con el frente). Lee `MPC_Breath` (para el soplo) y la cámara del rig (el punto ciclópeo). **No toca** el rig, el aliento, el metaball ni el BP del valle.
  - Polvo = malla de **2048 quads con HLSL propio** (la técnica del aliento y de Loving, gotcha 477): un draw call, cero CPU por mota.
  - Franja = **un Custom nuevo `GustLeanVS`** entre `ValleyGradVS` y el interpolador del gradiente (`V_VI0`) del valle: inclina la normal y aclara la "fracción de cima" **solo donde pasa el frente**, más allá de 25 m. **El HLSL del valle no cambia**; sin ráfaga (`GustK` = 0, el default) la rama se saltea: neutro exacto en el modelo, confirmado en el editor con el control negativo de M5.
- **Costo estimado:** polvo 0,03-0,09 ms de GPU (vértices) + < 0,005 ms (píxeles); franja 0,005-0,01 ms solo durante la ráfaga; audio 0 GPU; Blueprint 0,1-0,25 ms de CPU. **Total ≤ ~0,1 ms de GPU**, dentro del margen que queda (~2-3 ms) pero **se mide** (§9).
- **Confort (modelo, §8):** nada a menos de 1,2 m de un ojo; en calma el polvo se mueve p99 0,5°/s **sin flujo coherente** (0,02°/s); en la ráfaga el flujo coherente máximo es **1,0°/s** (transitorio, puntos dispersos, 0,2 % del campo); el mismo alfa en los dos ojos; la franja: contraste ≤ 12 niveles, flujo normal p50 0,4, p99 4,6°/s, **nunca a menos de 25 m** (el piso cercano queda quieto).
- **Sonido:** 4 WAV mono 48 kHz sintetizados con la envolvente del MISMO reloj (`SND_VidaGustA/B/C` 28 s, `SND_VidaSoplo` 18 s). El soplo va en 450-6000 Hz (91,5 % de su energía en 500-4000 Hz), +8 dB respecto de la rev. 1: no lo tapa el tono de exhalar del pacer (150-500 Hz).
- **Qué falta (editor, §13):** ~2 h 45 min de receta. Después: APK, banco y visor con Beltrán.
- **Decisiones para Beltrán (§15):** visible (default) o sutil (tabla 5.3); franja clara u oscura (`GustRuffle`); cuántas ráfagas; soplos sí/no.

---

## 1. Objetivo, alcance y reglas

**Objetivo:** que el valle se sienta vivo sin dejar de ser contemplativo: aire con cuerpo (profundidad, partículas en la luz) y, cada tanto, un acontecimiento lento (el viento que pasa y se lleva el polvo), con el usuario como parte del mismo aire.

**Reglas que el plan cumple por construcción:**
- **Una función nueva no degrada una aprobada.** Con `GustK` = 0 la rama de `GustLeanVS` se saltea y el valle es la v2 + capa viva: **exacto en el modelo** (`Vida_check.py`: 600 vértices al azar, el cielo y el suelo fuera del frente); en la GPU el shader del valle se recompila con un Custom más y no está demostrado que el compilador deje los mismos bits aguas arriba (FMA, reordenamiento): **se verifica en el editor con el control negativo del paso M5**. El único cambio del grafo del valle es la fuente de `V_VI0` (`vida_dryrun.py`). El aliento, el rig, el metaball, el pacer y el BP del valle no se tocan.
- **El polvo no compite con el aliento** (rev. 2): nada del polvo a menos de 1,2 m de los ojos (el aliento vive de 40 a 110 cm), paleta propia (dorado / blanco lavanda contra el azul frío / rosa tibio del aliento), y el soplo suena en otra banda que el pacer.
- **Capa autoral + capa viva:** el polvo y las ráfagas laterales son **autorales** (el valle respira solo); el soplo es **capa viva** (lo dispara la exhalación). Sin respiración detectada, solo laterales.
- **Nada salta:** el remolino de cada mota es un **lazo cerrado polinómico** (0 exacto antes y después del paso del frente); la **deriva** vuelve a 0 exacto con `Hold` (fase integrada); el frente arranca y termina con margen de 2W (§4.2); el meandro usa un número **entero** de vueltas por ventana de 1800 s (el BP envuelve su reloj sin salto); toda fase se integra en el BP (gotcha 329).
- **Confort:** nada a < 1,2 m de los ojos; nada de flujo coherente rápido de campo amplio; el piso cercano (< 25 m) quieto; lo que se mueve rápido en la vista se apaga (§8); lo que decide el alfa se calcula desde el punto ciclópeo (sin rivalidad binocular).
- **Sin arreglos ni índices dinámicos en los VS** (gotcha 399), sin bucles, sin half; ramas `[branch]` uniformes que llegan como `DontFlatten` al SPIR-V.

---

## 2. Qué se ve, momento a momento

| Momento | Polvo | Llano / horizonte | Sonido |
|---|---|---|---|
| **Calma** | ~255 motas visibles en la vista, de 1,3 a 26 m. Flotan (meandro de 7 cm cerca, hasta ~70 cm a 20-30 m: ~0,1-0,17°/s a toda distancia), **sin corriente** (flujo coherente 0,02°/s). Las que están contra el resplandor (azimut ~20°, un poco arriba del horizonte) brillan doradas; las demás, puntos blanco lavanda tenues. Titileo muy lento (0,08-0,25 Hz). El disco del metaball queda limpio | el valle como está (oleaje de luz, colinas que respiran, capa viva) | nada nuevo |
| **Llega una ráfaga lateral** (0-9 s) | el polvo levantado (512 motas cerca del piso, 1,5-36 m) empieza a encenderse bajo el frente, lejos | la **franja** aparece en el llano de un lado (a 25-70 m, de −3,4 a −1,8° de elevación) y avanza | el soplo empieza de ese lado, oscuro y lejano |
| **Pasa por el usuario** (9-19 s) | el frente cruza la nube: cada mota **se enciende** (×2,2), hace **un lazo** (sube o baja, vuelve) y **queda corrida a favor del viento** (p50 0,7 m, p90 1,5 m; menos cerca de los ojos); el meandro de todas se agita ×3 | la franja cruza el llano **a los costados del metaball** (+12 niveles) | el soplo al frente, más brillante (el pasto al lado), el máximo |
| **Se va** (19-28 s) | se apaga el polvo levantado; el resto sigue corrido | la franja se aleja hacia el otro lado y se desvanece | el soplo se va al otro lado |
| **Después** (hasta ~25 s) | el polvo **vuelve despacio a su lugar** (p99 1°/s, como el meandro) | como en calma | — |
| **Inhala** | nada propio (el aliento hace lo suyo) | la capa viva del valle | — |
| **Exhala, y toca un soplo** (con respiración detectada, una de cada 2 ráfagas, si pasó la calma) | ~1-2 s después del inicio de la exhalación, el polvo **de adelante** (1,3-5 m) se enciende y **se aleja** con el viento, continuando la pluma del aliento | la franja nace a ~25-30 m y **se aleja** hacia el horizonte (una línea horizontal que sube despacio: 0,2-0,4°/s) | un siseo tibio que nace cerca y se aleja al frente, **arriba** del tono de exhalar del pacer |
| **Sin respiración detectada** | igual | solo ráfagas laterales | — |
| **Gira la cabeza** | el polvo vive en el MUNDO: paralaje real (no "suciedad en el lente") | — | la fuente del soplo está en el mundo: se queda en su lugar |

Agenda (modelo, 15 min): **16 ráfagas** respirando (8 soplos), 16 sin respirar; entre comienzos 41-71 s (media 57 s); con el frente pasando el 41-48 % del tiempo (más la relajación de la deriva).

---

## 3. Arquitectura: un solo reloj

```
 MPC_Breath (Signed, On) ──────────────┐   (solo lectura: el detector de exhalación)
 BP_BreathRig_SC (CamRef) ─────────────┤   (solo lectura: el punto ciclópeo; y tickear DESPUÉS del rig)
                                       ▼
 BP_ValleyLife_SC  (NUEVO, colocado en los ojos: 0, 0, 120)
   VidaTick(DT):
     VidaMPC ─► VidaBreath (velocidad filtrada, histéresis, inicio de exhalación con latch; = el aliento)
            ─► VidaSchedule  ◄── EL RELOJ DE RÁFAGAS: el frente s avanza -> VidaEnd -> relajación de la deriva
                                 (VidaRelax) y la calma -> VidaMaybe -> VidaDue (lateral o soplo)
            ─► VidaState (actividad en el usuario -> ritmo del meandro integrado Tm; presencia Glob)
            ─► VidaPerf (banco)
            ─► VidaPushDust ──► DustMesh (SM_ValleyDust_SC + MI_ValleyDust_SC): 7 vectores (+ VidaPushCam, VidaPushSoul)
            ─► VidaPushValley ─► Entering_Valle.Ground (M_BreathValley_SC, GustLeanVS): 5 vectores
            ─► VidaAudio ─────► GustAudio (AudioComponent): viaja con el frente
            ─► VidaVisible
   componentes: DustMesh, GustAudio
```

| Estado / parámetro | Lo produce | Lo leen |
|---|---|---|
| Frente `s`, trayectoria (`OrgW`, `DirW`), envolvente (`E0`, `E1`, `Ramp`), ancho `GW`, largo del frente (`Lf0`, `Lf1`), `Amp`, deriva (`Hold`, `HoldV`) | `VidaSchedule` / `VidaStartLat` / `VidaStartBreath` / `VidaRelaxStep` | el polvo (`VidaG/S/E/F`), la franja (`GustP/Q/R/K`, solo mientras el frente pasa), la fuente de sonido (`VidaAudio`) y el meandro (`VidaState`) — **el mismo estado, el mismo cuadro** (gotcha 465) |
| `Tm`, `Rate` (meandro integrado), `Glob` (presencia) | `VidaState` | el polvo (`VidaT`) |
| centro y escala del metaball | `BP_BreathBlob_SC` (se lee, no se toca) | el polvo (`VidaSoul`) |
| la cámara del pawn (punto ciclópeo) | `BP_BreathRig_SC.CamRef` (se lee, no se toca) | el polvo (`VidaC`) |

**Las funciones de la ráfaga son las mismas en todas partes** (`vida_model.py`): para un punto `p` del plano, `x = (p − O)·d` (a lo largo del camino), `η = |(p − O)·d⊥|` (a lo largo del frente):
- `A(x) = S5((x − e0)/rampa)·(1 − S5((x − (e1 − rampa))/rampa))` — dónde existe la ráfaga;
- `h(η) = 1 − S5((η − Lf0)/(Lf1 − Lf0))` — el frente es finito;
- `u = (s − x)/W`, `t = sat((u + 2)/4)`, `P = S5(t)` (fracción del paso), `bell = 16t²(1 − t)²` (actividad).

Todo es invariante a traslaciones y giros en yaw: `s`, `e0`, `e1`, `W`, `Lf0`, `Lf1` valen igual en el espacio del polvo, del valle y del mundo; el BP solo convierte `O` y `d`.

### 3.1 Decisiones

| Decisión | Opciones | Elegida y por qué |
|---|---|---|
| **Dónde vive** | dentro del aliento / del valle / actor propio | ✅ **actor propio**: nada aprobado se toca; los grafos se escriben con DSL en vacío (nada nace pelado, gotcha 478); rollback = ocultar el actor. Portátil: sin valle, sin metaball o sin rig sigue andando (IsValid) |
| **Cómo se ve la ráfaga lejos** | (a) una banda en `ValleyPS` (por píxel); (b) planos translúcidos de polvo; (c) **la normal y la fracción de cima por vértice** | ✅ **(c)**: 0,005-0,01 ms (vértices del valle) contra 0,05-0,15 ms por píxel de (a) en una escena limitada por relleno, y sin el costo/bordes de (b). Es el truco que el valle ya usa para su oleaje |
| **Tocar el HLSL del valle o no** | modificar `ValleyGradVS` por el circuito del valle / **un Custom aparte** | ✅ **Custom aparte** (`GustLeanVS`): `ValleyGradVS.hlsl`, `valley_model.py`, `Valley_check.py` (90/90), `valley_build.json` y la §7.2 del plan del valle quedan **intactos**; el grafo solo cambia la fuente de `V_VI0`. Contra: si alguien vuelve a pegar `apply_valley_material_B.py`, la franja se apaga (neutro, sin error) y hay que volver a pegar `apply_vida_gust_valley.py` (probado en `vida_dryrun.py`) |
| **Cómo mueve el viento al polvo** (rev. 2) | solo un lazo cerrado (rev. 1: se leía como una ola de brillo, "motas atadas con elástico") / **lazo + deriva neta que se relaja** | ✅ **lazo + deriva**: la mota queda corrida a favor del viento (`DriftCm` 40 × (0,5-1,5) × la distancia, hasta ×3 lejos) y vuelve en `DriftRelax` s (25, o la calma si es más corta: la agenda no se atrasa). Sin estado: `Hold` es una fase más que integra el BP. Cuesta flujo coherente (0,74 → 1,0°/s en la ráfaga, §8): es justamente lo que se lee como viento |
| **El alfa en estéreo** (rev. 2) | con la cámara de cada ojo (rev. 1: hasta 1,0 de diferencia relativa en el borde del metaball) / **desde el punto ciclópeo** | ✅ **ciclópeo** (`VidaC`, la cámara del rig): el alfa de cada mota es idéntico en los dos ojos (verificado); el sprite sigue por ojo. Sin rig (editor), cada ojo usa la suya |
| **La bruma que "se mueve un poco"** | cambiar la niebla del valle con la ráfaga | ❌ en esta tanda: la niebla vive en `ValleyPS` (por píxel) o en parámetros que ya escriben `ApplyLook` y `PushLive` (dos escritores). Lo que se mueve en su lugar: el polvo levantado y la franja. Tanda 2 si Beltrán lo pide |
| **Los tiempos** | un `Timeline`/timers / **integrar en el Tick** | ✅ Tick: una sola fuente de tiempo (el `DT`), fases integradas, nada de `Delay` (y el soplo espera un evento del cuerpo) |
| **Sonido** | loop con volumen/filtro dinámico / **one-shots con la envolvente del reloj** | ✅ one-shots (mejor timbre: el espectro evoluciona dentro del archivo) + la fuente que viaja; el pitch estira el archivo a `GustLife` (0,75-1,33): **cambia también el timbre**, así que si `GustLife` cambia más de ~15 % se regenera el WAV (§7) |
| **Espacialización** | HRTF (no hay en 5.8) / paneo por defecto | ✅ `AudioComponent` mono con **atenuación propia**: espacializado sí, atenuación por distancia no; el paneo va de un lado al otro (`audio-quest.md`) |

---

## 4. Las ráfagas

### 4.1 Lateral (la autoral)

- Dirección: `yaw + 90°·signo + jitter` (signo y jitter por secuencias de baja discrepancia sobre el índice de la ráfaga, gotcha 355).
- La trayectoria pasa por `O = asiento + adelante·m`, con `m` entre `OffsetMin` y `OffsetMax` (15-40 m): el frente (una línea a lo largo del eje adelante) está centrado a `m` delante → la franja se ve en el llano de enfrente, **a los costados del metaball** (que tapa ±17° alrededor del centro), y el usuario queda dentro del frente (el polvo cercano responde).
- Envolvente a lo largo del camino: `e0 = −PathHalf` … `e1 = +PathHalf` (**±40 m**, rev. 2: con ±22 m la ráfaga se apagaba justo cuando la franja salía de detrás del metaball), rampa 15 m; ancho del frente `W` = 9 m (el paso por un punto dura ~9 s).
- Velocidad = `(e1 − e0 + 4W)/GustLife` = 116 m / 28 s = **4,1 m/s** (una brisa).

### 4.2 Sin saltos: el margen de 2W, el lazo cerrado y la deriva que vuelve

- El frente arranca en `s0 = e0 − 2W` y termina en `s1 = e1 + 2W`: en el primer cuadro todo punto con `A > 0` tiene `P = 0` y en el último `P = 1`. El remolino es `R·A·h·(lx(P)·e1 + ly(P)·e2)` con `lx = 0,6·6√3·P(1−P)(1−2P)`, `ly = 32P²(1−P)²`: **0 exacto** en `P = 0` y `P = 1`.
- La **deriva** es `Rd·A·h·P·Hold·e1` (a favor del viento, horizontal): `Hold` = 1 mientras el frente pasa; cuando termina (`VidaEnd`), `Hold = 1 − S5(fase)` con la fase integrada a `1/min(DriftRelax, calma)` por segundo → vuelve a **0 exacto**; recién ahí `Amp` = 0 y la rama del VS se apaga. Si hay un `GustNow` pendiente, la fase corre a ≥ 1/3 por segundo (continua, sin salto).
- Verificado: al empezar la ráfaga y al terminar la relajación, desplazamiento **0,0** exacto (HLSL traducido y BP simulado); al terminar el frente queda **solo** la deriva (horizontal, a favor del viento, 3e-14 cm fuera de la dirección); ninguna mota **salta** (lo que la velocidad no explica, `|dP − V·dt|`, ≤ 1,3e-3 cm por cuadro); la velocidad analítica `V` (la que apaga lo rápido) = la derivada numérica, también en la relajación. Controles negativos: sin el margen de 2W las motas saltan 13,6 cm; con `Amp` a 0 al terminar el frente (la rev. 1) la deriva salta 169 cm.
- `e1` es la dirección de avance; `e2` = arriba girado ±60° hacia el costado, con **signo al azar por mota** (la mitad sube, la mitad baja: sin flujo neto vertical).

### 4.3 El soplo (un solo aire)

- Con respiración detectada (`On` > 0,5), la ráfaga que toca en los turnos impares (`BreathEvery` 2) **espera un inicio de exhalación** (el mismo detector del aliento: velocidad de `Signed` filtrada 0,15 s, histéresis 0,10/0,04, latch de 0,6 s de inhalación) hasta `BreathWait` **15 s** (rev. 2: con 8 s y un ciclo de 14 s la mitad de los soplos se perdían y salía una lateral); si no llega, sale una lateral.
- Geometría: sale del usuario hacia adelante (±15°): `O` = asiento, `e0 = 0`, `e1 = 60 m`, `W = 4 m` (el polvo cercano responde en ~1-2 s: sigue a la pluma del aliento), 18 s.
- Verificado en el DSL simulado: los 3 soplos de 6 min arrancan en la fase 7,31 s del ciclo 4-3-4-3 (el comienzo de la exhalación es 7,4 s). Control negativo: si se pisa `Flow` antes de leer el inicio, no hay soplos.
- El `BP_ValleyLife_SC` tickea **después del rig** (`AddTickPrerequisiteActor` en `BeginPlay`, como el aliento): lee `MPC_Breath` del mismo cuadro, así que el detector es el mismo que el del aliento, sin un cuadro de retraso.

### 4.4 La agenda

`Wait = GapMin + (GapMax − GapMin)·frac(k·0,618 + 0,5)` después de cada ráfaga (20-40 s de calma, durante la cual se relaja la deriva) + `FirstGap` 14 s al empezar. Una ráfaga nueva sale cuando: la deriva ya volvió, se cumplió la calma, **`bVida` y `VidaAmount` > 0** (rev. 2: el pánico corta también las ráfagas), `bGusts`, y no es el banco sin ráfagas (`PerfMode` 3). **`ke * GustNow`** (rev. 2) pide una lateral: en calma sale en el cuadro siguiente; con una en curso, al terminar ella (+ ≤ 3 s de relajación acelerada); esperando un soplo, sale una lateral en seguida (antes: se perdía o alargaba la espera).

---

## 5. El polvo

### 5.1 Malla `SM_ValleyDust_SC`

- **2048 quads reales de 0,4 cm, CADA UNO EN SU LUGAR** (la malla es la nube; 8192 vértices, 4096 triángulos): **1536 de base** (radio log-uniforme **1,3 m**-36 m, la primera octava a la mitad; por encima del piso; lejos de 3 m no más de 50° de elevación; fuera del metaball) y **512 de ráfaga** (1,5-36 m, hasta 6 m sobre el piso: el polvo que levanta el frente).
- **Semillas invariantes a la V invertida del importador FBX y a las UV en fp16** (una StaticMesh guarda las UV en half: enteros exactos hasta 2048):
  - posición = `LocalPosition` − la esquina (fp32 exacto; la esquina `k` 0..3 va en la **U** de UV0, así los 4 vértices recuperan el MISMO centro aunque la V se invierta);
  - UV1 = (`n` 0..1023 juego de frecuencias, fase 1) · UV2 = (bits: 1 solo-ráfaga, 2 sentido del remolino; fase 2) · UV3 = (`b` brillo/tamaño/radio, fase 3). Lo asimétrico (enteros, `b`) en U; en V solo fases uniformes.
  - `Vida_check.py` §6: con las UV en half y la V invertida, posiciones exactas y las mismas estadísticas; control negativo: con la esquina y los bits en V la V invertida corre los centros 0,4 cm (quads rotos) y cambia 724 motas de corriente.
- Generada headless: `blender --background --factory-startup --python scripts/gen_valley_dust.py` → `VR_Test/Saved/ClaudeScripts/vida/SM_ValleyDust_SC.fbx`. Reimportada y verificada: 8192 v / 2048 polígonos / 4 capas de UV / |UV − codificada| ≤ 3e-8 / centro recuperado = semilla ≤ 1,8e-4 cm / caja X −3157…3214, Y −3491…3423, Z −195…2612 cm.

### 5.2 Material `M_ValleyDust_SC` (+ `MI_ValleyDust_SC`)

- **Unlit, Translucent `BLEND_AlphaComposite` (premultiplicado), Two Sided, sin niebla de translúcidos.** Componente con `TranslucencySortPriority` **5** (después del pacer 0; antes del metaball 10 y del aliento 20; el disco del metaball queda despejado por el VS, así el orden con él no importa).
- Grafo (lo arma `apply_vida_dust_material.py`, el mismo patrón que el aliento): `LocalPosition`, `TexCoord 0-3`, `CameraPositionWS → TransformPosition (World→Local)` → `DustVS` (**38 entradas**) → `Transform (vector, Local→World)` → WPO; `DustVS.DustV → VertexInterpolator → DustPS` → Emissive / Opacity.
- Por mota, en el VS: meandro (3 senos, un número entero de vueltas por 1800 s; amplitud × `clamp(d/3 m, 1, MeanderFar)`), remolino y deriva (§4.2), luz (Henyey-Greenstein normalizado: `SunBase + (1 − SunBase)·HG(μ)/HG(1)`), brillo por mota, titileo lento, caída con la distancia, confort (§8). **Todo lo que decide el alfa desde el punto ciclópeo `VidaC`**; el sprite y su tamaño con la cámara de cada ojo. Tamaño angular `DustSizeDeg·(1 ± SizeVar)` con piso de 0,2°. Alfa < 0,002 → tamaño 0 (no cuesta píxeles). En el editor (`Live` 0) el meandro anima con `View.GameTime`.

| Grupo | Parámetro | Tipo | Default | Rango sugerido | Qué hace |
|---|---|---|---|---|---|
| `1 - Polvo` | `DustAlpha` | escalar | 1 | 0,5 … 1 | Opacidad de las motas. Primera palanca si en el visor 'ensucia' (bajar a 0,7 = el juego sutil) |
| `1 - Polvo` | `DustSizeDeg` | escalar | 0,24 | 0,2 … 0,35 | Tamaño angular (grados). Piso fijo 0,2 (debajo centellea). Más = menos 'polvo', más 'nieve' |
| `1 - Polvo` | `SizeVar` | escalar | 0,3 | 0 … 0,5 | Variación del tamaño entre motas (±) |
| `1 - Polvo` | `DistTilt` | escalar | 0,3 | 0 … 1 | Cuánto más tenues las lejanas: brillo × (1 m / d)^DistTilt. 0 = todas iguales |
| `1 - Polvo` | `MeanderCm` | escalar | 7 | 0 … 15 | Amplitud del meandro de cada mota hasta 3 m (cm). Periodos de 33-75 s: flota, no viaja |
| `1 - Polvo` | `MeanderFar` | escalar | 10 | 1 … 12 | Más allá de 3 m la amplitud crece con la distancia hasta × MeanderFar (ninguna mota queda 'congelada': ~0,1-0,17°/s a toda distancia) |
| `1 - Polvo` | `Twinkle` | escalar | 0,35 | 0 … 0,7 | Titileo lento (0,08-0,25 Hz, sin parpadeo). 0 = ninguno |
| `2 - Luz` | `SunAz` | escalar | 20 | −180 … 180 | Azimut de la luz contra la que brillan (grados; 20 = el resplandor del valle) |
| `2 - Luz` | `SunEl` | escalar | 10 | 0 … 40 | Elevación de esa luz (grados) |
| `2 - Luz` | `SunG` | escalar | 0,55 | 0 … 0,9 | Dispersión hacia adelante (Henyey-Greenstein): más = halo más angosto alrededor de la luz |
| `2 - Luz` | `SunBase` | escalar | 0,5 | 0 … 1 | Brillo de las motas que NO están contra la luz (1 = todas iguales) |
| `3 - Rafaga` | `EddyCm` | escalar | 10 | 0 … 20 | Radio del lazo al paso del frente (cm) |
| `3 - Rafaga` | `EddyNear` | escalar | 250 | 100 … 400 | cm: más cerca de los ojos el lazo y la deriva se achican (hasta ×0,3) |
| `3 - Rafaga` | `Lift` | escalar | 1,2 | 0 … 3 | Cuánto se encienden las motas cuando el frente les pasa por encima |
| `3 - Rafaga` | `GustDustAlpha` | escalar | 0,6 | 0 … 1 | Opacidad del polvo que SOLO levanta la ráfaga (512 motas cerca del piso, 1,5-36 m) |
| `3 - Rafaga` | `DriftCm` | escalar | 40 | 0 … 80 | Cuánto se lleva el viento cada mota (cm a EddyNear; × 0,5-1,5 por mota). Primera palanca si la ráfaga 'empuja' demasiado; 0 = solo el lazo (la rev. 1) |
| `3 - Rafaga` | `DriftFar` | escalar | 3 | 1 … 5 | Lejos la deriva crece con la distancia hasta × DriftFar (para que se vea a 10-30 m) |
| `4 - Confort` | `NearMin` | escalar | 120 | 110 … 150 | 🔴 cm a los ojos: invisible debajo. **No bajar de 110**: el volumen del aliento (inhalar 40-95 cm, pluma hasta 110) es SUYO |
| `4 - Confort` | `NearFull` | escalar | 180 | NearMin + 30 … 250 | cm: plena desde acá |
| `4 - Confort` | `FarFade0` | escalar | 8000 | 1500 … 10000 | cm: las lejanas empiezan a apagarse (rev. 3: 2600 → 8000) |
| `4 - Confort` | `FarFade1` | escalar | 11000 | FarFade0 + 500 … 11000 | cm: apagadas (rev. 3: la nube llega a 110 m; antes 36 m) |
| `4 - Confort` | `SpeedFade0` | escalar | 6 | 4 … 10 | grados/s en la vista: desde acá lo que se mueve rápido se apaga |
| `4 - Confort` | `SpeedFade1` | escalar | 12 | SpeedFade0 + 3 … 20 | grados/s: apagado del todo |
| `4 - Confort` | `SoulMargin0` | escalar | 2 | 0 … 6 | grados alrededor del disco del metaball sin polvo |
| `4 - Confort` | `SoulMargin1` | escalar | 8 | SoulMargin0 + 2 … 15 | grados: pleno desde acá |
| `5 - Color` | `ColLit` | vector | (1, 0,93, 0,74) | — | Color de la mota contra la luz (lineal; dorado, distinto del rosa tibio del aliento) |
| `5 - Color` | `ColDim` | vector | (0,92, 0,9, 0,96) | — | Color de la mota en sombra (lineal; blanco lavanda apagado, sin el azul del aliento; más claro que el aire para que se lea) |
| `9 - Interno` | `VidaT` | vector | (0, 1, 0, 0) | — | Lo escribe el BP: (Tm, ritmo del meandro, Glob, Live). Glob 0 = nada dibujado; Live 0 = el editor anima con su reloj |
| `9 - Interno` | `VidaG` | vector | (0, 0, 0, 1) | — | Lo escribe el BP: (Ox, Oy, dx, dy) la trayectoria de la ráfaga en el espacio del actor |
| `9 - Interno` | `VidaS` | vector | (0, 800, 0, 0) | — | Lo escribe el BP: (s frente, W, velocidad del frente, Amp). Amp 0 = sin ráfaga (la rama no se calcula) |
| `9 - Interno` | `VidaE` | vector | (0, 0, 1000, 0) | — | Lo escribe el BP: (e0, e1, rampa, Hold) la envolvente; Hold = la deriva (1 en la ráfaga, vuelve a 0) |
| `9 - Interno` | `VidaF` | vector | (3000, 5500, 0, 0) | — | Lo escribe el BP: (Lf0, Lf1, dHold/dt, −) el largo del frente |
| `9 - Interno` | `VidaSoul` | vector | (380, 0, 5, 0) | — | Lo escribe el BP: (centro del metaball en local, radio). Radio 0 = sin despeje |
| `9 - Interno` | `VidaC` | vector | (0, 0, 0, 0) | — | Lo escribe el BP: (punto ciclópeo en local, válido). w 0 = cada ojo usa su cámara (editor, sin rig) |

### 5.3 Los dos juegos: VISIBLE (default) y SUTIL

Beltrán pidió **más vida**; en las fotos de la rev. 1 el polvo casi no se veía y la franja daba +8 niveles en una lámina delgada. El default es ahora el juego **visible**; el **sutil** (la rev. 1) queda para **bajar mirando** si en el visor ensucia o tira del cuerpo. Se cambian en la MI (material) y en la instancia `Entering_Vida` (BP); `vida_model.PRESET_SUTIL` y `PRESET_SUTIL_BP` son la referencia.

| Dónde | Perilla | Visible (default) | Sutil (rev. 1) |
|---|---|---|---|
| MI | `DustAlpha` | 1 | 0,7 |
| MI | `DustSizeDeg` | 0,24 | 0,22 |
| MI | `DistTilt` | 0,3 | 0,35 |
| MI | `SunBase` | 0,5 | 0,35 |
| MI | `ColDim` | (0,92, 0,9, 0,96) | (0,8, 0,78, 0,86) |
| MI | `GustDustAlpha` | 0,6 | 0,5 |
| MI | `DriftCm` | 40 | 20 |
| BP | `GustLight` | 2,8 | 1,6 |
| BP | `GustLean` | 0,12 | 0,08 |
| BP | `GustW` | 900 | 700 |
| BP | `OffsetMin` / `OffsetMax` | 1500 / 4000 | 500 / 3000 |
| BP | `FrontHalf0` / `FrontHalf1` | 4000 / 7000 | 3000 / 5500 |

### 5.4 Perillas del Blueprint (instance-editable)

| Grupo | Perilla | Tipo | Default | Rango sugerido | Qué hace |
|---|---|---|---|---|---|
| `A-Vida` | `bVida` | bool | true | — | Apaga toda la capa: el polvo se va con GlobTau y **no sale ninguna ráfaga nueva** (la que está en curso termina) |
| `A-Vida` | `VidaAmount` | escalar | 1 | 0 … 1 | Presencia del polvo. **0 = apagado entero** (botón de pánico, A/B): sin polvo y sin ráfagas nuevas |
| `A-Vida` | `MeanderRate` | escalar | 1 | 0 … 2 | Ritmo del meandro (se integra: cambiarlo en vivo no salta) |
| `A-Vida` | `GlobTau` | escalar | 1 | 0,3 … 3 | s: cómo aparece y se va el polvo |
| `A-Vida` | `SoulR` | escalar | 150 | 100 … 250 | cm: radio del despeje alrededor del metaball (× su escala) |
| `B-Rafagas` | `bGusts` | bool | true | — | Sin ráfagas nuevas (la que está en curso termina: nada salta) |
| `B-Rafagas` | `GustAmount` | escalar | 1 | 0 … 1 | Intensidad de las ráfagas (polvo y franja) |
| `B-Rafagas` | `FirstGap` | escalar | 14 | 5 … 60 | s hasta la primera ráfaga |
| `B-Rafagas` | `GapMin` | escalar | 20 | 10 … 60 | s: la calma mínima entre el final de una ráfaga y la siguiente |
| `B-Rafagas` | `GapMax` | escalar | 40 | GapMin … 120 | s: la calma máxima (irregular: secuencia de baja discrepancia) |
| `B-Rafagas` | `GustLife` | escalar | 28 | 20 … 40 | s que dura la ráfaga lateral. Más = más lenta en la vista. 🔴 Si cambia más de ~15 %, regenerar los WAV (§7) |
| `B-Rafagas` | `PathHalf` | escalar | 4000 | 2000 … 5000 | cm: media longitud del tramo donde la ráfaga existe |
| `B-Rafagas` | `GustW` | escalar | 900 | 400 … 1200 | cm: ancho del frente (más = paso más suave y largo) |
| `B-Rafagas` | `GustRamp` | escalar | 1500 | 300 … 2000 | cm: cómo nace y muere a lo largo del camino |
| `B-Rafagas` | `FrontHalf0` | escalar | 4000 | 1500 … 6000 | cm: medio largo pleno del frente |
| `B-Rafagas` | `FrontHalf1` | escalar | 7000 | FrontHalf0 + 500 … 9000 | cm: el frente se apaga hasta acá |
| `B-Rafagas` | `OffsetMin` | escalar | 1500 | 0 … 3000 | cm: dónde se centra la franja delante del usuario (mínimo) |
| `B-Rafagas` | `OffsetMax` | escalar | 4000 | OffsetMin … 6000 | cm: idem (máximo) |
| `B-Rafagas` | `JitterDeg` | escalar | 25 | 0 … 40 | grados de variación de la dirección de cada ráfaga |
| `B-Rafagas` | `GustStir` | escalar | 2 | 0 … 4 | Cuánto se agita el meandro cuando la ráfaga pasa por el usuario (×(1 + GustStir)) |
| `B-Rafagas` | `DriftRelax` | escalar | 25 | 10 … 60 | s en que el polvo vuelve a su lugar después del paso (o la calma, si es más corta). Más = vuelve más lento |
| `B-Rafagas` | `GustLight` | escalar | 2,8 | 0 … 3 | La franja: cuánto se aclara el llano (vía CrestLight del valle). Primera palanca de la franja |
| `B-Rafagas` | `GustLean` | escalar | 0,12 | 0 … 0,2 | La franja: inclinación de la normal hacia la luz (el pasto peinado agarra luz) |
| `B-Rafagas` | `LeanAz` | escalar | 20 | −180 … 180 | grados: hacia dónde se inclina (20 = la luz del valle: siempre aclara) |
| `B-Rafagas` | `GustRuffle` | escalar | 0 | 0 … 0,15 | Alternativa: inclinación hacia el usuario = rompe el brillo rasante -> franja OSCURA (como el viento en el agua) |
| `B-Rafagas` | `GustNear` | escalar | 2500 | 1500 … 3000 | 🔴 cm: la franja no toca el piso más cerca que esto (plena desde el doble). 25 m: el piso cercano queda quieto y la franja sube a −3,4/−1,8° |
| `C-Soplo` | `bBreathGusts` | bool | true | — | Un solo aire: una de cada BreathEvery ráfagas espera una exhalación y sale del usuario |
| `C-Soplo` | `BreathEvery` | escalar | 2 | 1 … 4 | Cada cuántas ráfagas una es soplo (con respiración detectada) |
| `C-Soplo` | `BreathWait` | escalar | 15 | 8 … 20 | s que espera la exhalación (≥ un ciclo de respiración); si no llega, sale una lateral |
| `C-Soplo` | `BreathLife` | escalar | 18 | 12 … 30 | s que dura el soplo. 🔴 Si cambia más de ~15 %, regenerar `SND_VidaSoplo` |
| `C-Soplo` | `BreathLen` | escalar | 6000 | 3000 … 8000 | cm: hasta dónde llega |
| `C-Soplo` | `BreathW` | escalar | 400 | 200 … 800 | cm: ancho del frente (chico = el polvo cercano responde rápido a la exhalación) |
| `C-Soplo` | `BreathRamp` | escalar | 300 | 100 … 1000 | cm |
| `C-Soplo` | `BreathHalf0` | escalar | 2500 | 1500 … 4000 | cm: medio largo pleno del frente del soplo |
| `C-Soplo` | `BreathHalf1` | escalar | 4500 | BreathHalf0 + 500 … 6000 | cm |
| `C-Soplo` | `BreathJitter` | escalar | 15 | 0 … 30 | grados de variación alrededor de adelante |
| `D-Sonido` | `GustVolume` | escalar | 0,8 | 0 … 1 | Volumen de los soplos (0 = mudo) |
| `D-Sonido` | `SndLen` | escalar | 28 | — | s del WAV de la ráfaga lateral: el pitch lo estira a GustLife (0,75-1,33) |
| `D-Sonido` | `BreathSndLen` | escalar | 18 | — | s del WAV del soplo |
| `D-Sonido` | `SndFwd` | escalar | 800 | 300 … 2000 | cm delante del usuario por donde viaja la fuente de la ráfaga lateral |
| `E-Prueba` | `PreviewGust` | escalar | 0 | 0 … 1 | Vista previa sin Play: 0 = calma; > 0 = una ráfaga CONGELADA en esa fracción del camino (0,5 = pasando por el usuario) |
| `E-Prueba` | `PreviewKind` | escalar | 0 | 0 / 1 | 0 lateral, 1 soplo |
| `E-Prueba` | `PreviewDir` | escalar | 1 | −1 / 1 | de izquierda a derecha (1) o al revés |
| `D-Sonido` | `GustSounds` | sonidos (array SoundBase) | SND_VidaGustA, B, C | — | Las variantes de la ráfaga lateral (se alternan). Vacío = mudo + un aviso en el log |
| `D-Sonido` | `BreathSounds` | sonidos (array SoundBase) | SND_VidaSoplo | — | El soplo |

### 5.5 Estado y componentes de `BP_ValleyLife_SC`

**Componentes** (en el CDO, ANTES de colocar el actor; en la plantilla `<Comp>_GEN_VARIABLE`, **una propiedad por `set_properties`**, gotcha 478):

| Componente | Clase | Propiedades |
|---|---|---|
| `DefaultSceneRoot` | el del BP | el actor va en los ojos del usuario sentado (0, 0, 120), sin rotar (solo yaw permitido) |
| `DustMesh` | StaticMeshComponent: `SM_ValleyDust_SC` + `MI_ValleyDust_SC` | `BodyInstance` `{"collisionEnabled":"NoCollision","collisionProfileName":"NoCollision"}` · `castShadow` false · `translucencySortPriority` 5 · `bReceivesDecals` false |
| `GustAudio` | AudioComponent | `bAutoActivate` false · `bOverrideAttenuation` true · `AttenuationOverrides` (texto) `"(bAttenuate=False,bSpatialize=True)"` · `bAllowSpatialization` true (cada `false` en su propia llamada) |

**Variables de estado** (categoría `Z-Vida`, NO instance-editable): `Clock`, `Wait`, `GustIdx`, `GustKind`, `Front`, `Front0`, `Front1`, `FrontV`, `GW`, `E0`, `E1`, `Ramp`, `Lf0`, `Lf1`, `Life`, `SndMin`, `Amp`, `Hold`, `HoldPh`, `HoldV`, `HoldRate`, `Tm`, `Rate`, `GlobBase`, `Glob`, `ActUser`, `VSig`, `VGate`, `Sprev`, `Vel`, `VelF`, `Flow`, `InhHold` (float) · `bGusting`, `bPrimed`, `bExhOnset`, `bSndWarned`, `bForce` (bool) · `OrgW`, `DirW`, `SndOffW` (Vector) · `PerfMode` (int) · `Valley` (objeto `BP_BreathValley_SC_C`, `add_object_variable`) · `Blob` (objeto `BP_BreathBlob_SC_C`) · `Rig` (objeto `BP_BreathRig_SC_C`).

Nombres elegidos para el DSL: categorías sin espacios (gotcha 466); **`bGusting`** y no `bGustOn` (el nombre visible pasa "On" a minúscula: el getter sería `GetGuston`); `bForce` → `GetForce`.

### 5.6 Grafos (texto exacto: `scripts/vida.dsl`)

37 funciones + `ConstructionScript` + `EventGraph`.

| Grafo | Parámetros | Qué hace |
|---|---|---|
| `VidaMPC` | — | puente a `MPC_Breath` (esqueleto por DSL + 2 nodos por cirugía, como `AirMPC`) |
| `VidaBreath` | `DT` | detector de exhalación |
| `VidaGap`, `VidaGo` | — | la próxima espera; lo común al arrancar una ráfaga (incluye `Hold` 1 y borrar `bForce`) |
| `VidaStartLat` | `Sign` | geometría de una lateral (0 = el signo que toque) |
| `VidaStartBreath` | — | geometría del soplo |
| `VidaSnd` | `Snd` (SoundBase, `add_object_function_param`), `Pitch` | sonido + pitch + volumen + ubicar + Play: **se arma por cirugía** (B12), el bloque DSL es la especificación |
| `VidaNoSnd`, `VidaPlayG`, `VidaPlayB` | —, `Pitch`, `Pitch` | elegir la variante (índice mod cantidad) o avisar una vez |
| `VidaLaunchLat`, `VidaLaunchBreath` | — | geometría + sonido + índice |
| `VidaDue`, `VidaMaybe`, `VidaEnd`, `VidaRelaxStep`, `VidaRelax`, `VidaSchedule` | —, —, —, `DT`, `DT`, `DT` | EL RELOJ (con la relajación de la deriva) |
| `VidaState` | `DT` | actividad en el usuario, meandro integrado, presencia |
| `VidaPerf` | — | banco |
| `VidaPushSoul`, `VidaNoCam`, `VidaCamC`, `VidaCamRig`, `VidaPushCam`, `VidaPushDust` | —, —, —, —, `Live`, `Live` | los 7 vectores del polvo (el punto ciclópeo sale de `Rig.CamRef`) |
| `VidaPushValley` | — | los 5 vectores de la franja (si hay valle; `GustK` = 0 fuera del paso del frente) |
| `VidaAudio`, `VidaVisible` | — | la fuente del soplo; ocultar sin presencia |
| `VidaFind`, `VidaAfterRig`, `VidaZero`, `VidaReset`, `VidaTick` | —, —, —, —, `DT` | arranque (valle, metaball, rig; tickear después del rig) y Tick |
| `VidaPreGeo`, `VidaPreview`, `VidaBenchFull` | — | vista previa sin Play; banco |
| `ConstructionScript` | — | sort 5 (red de seguridad) + `VidaPreview` |
| `EventGraph` | — | `BeginPlay` → `VidaReset`; `Tick` → `VidaTick`; `PerfE0..E4` (modo 3: sin ráfagas), `PerfE5/E6`, `PerfEEnd` (normal), `PerfV0/1/2` (ecos `VIDA PERF modo N`), `GustNow`, `VidaDbg` |

---

## 6. La franja en el valle

### 6.1 Qué hace

`GustLeanVS` recibe la salida de `ValleyGradVS` (dh/dx, dh/dy, h, hf) y, donde pasa el frente (`A·h·bell`) y más allá de `GustNear` del usuario (rampa quíntica de 25 a 50 m):
- inclina la normal **hacia la luz** (`GustLean` 0,12 hacia `LeanAz` 20°): el pasto peinado agarra luz;
- aclara la **fracción de cima**: `hf' = √(hf² + a·GustLight)` → el PS mezcla hacia `ColLit` con `CrestLight·hf'²` (con `GustLight` 2,8 y `CrestLight` 0,2 del valle: hasta 0,76; nunca pasa de 1 con los rangos de la tabla);
- opcional, `GustRuffle`: inclina hacia el usuario → rompe el brillo rasante → **franja oscura**. Default 0.

`h` y la geometría **no cambian** (sin bordes de oclusión, sin vección por relieve). Durante la relajación de la deriva el BP empuja `GustK` = 0 (el frente ya pasó): la rama se saltea.

### 6.2 Cableado

`ValleyGradVS ──► GustLeanVS.G` · `V_LP.XYZ ──► GustLeanVS.LP` · `Part`, `GustP/Q/R/K/S (RGBA)` ──► sus entradas · **`GustLeanVS ──► V_VI0.VS`** (antes: `ValleyGradVS ──► V_VI0.VS`). Nada más cambia (verificado en el editor simulado comparando TODAS las conexiones antes y después).

### 6.3 Parámetros nuevos de `M_BreathValley_SC`

| Grupo | Parámetro | Tipo | Default | Rango sugerido | Qué hace |
|---|---|---|---|---|---|
| `10 - Rafaga` | `GustP` | vector | (0, 0, 0, 1) | — | Lo escribe el BP: (Ox, Oy, dx, dy): la trayectoria en el espacio del valle |
| `10 - Rafaga` | `GustQ` | vector | (0, 800, 0, 0) | — | Lo escribe el BP: (s frente, W, e0, e1) |
| `10 - Rafaga` | `GustR` | vector | (1000, 3000, 5500, 1500) | — | Lo escribe el BP: (rampa, Lf0, Lf1, GustNear) |
| `10 - Rafaga` | `GustK` | vector | (0, 0, 0, 0) | — | Lo escribe el BP: (luz, inclinación x, inclinación y, erizado) × Amp. **(0,0,0,0) = NEUTRO: la rama no se calcula** |
| `10 - Rafaga` | `GustS` | vector | (0, 0, 0, 0) | — | Lo escribe el BP: (usuario x, usuario y, −, −) en el espacio del valle |

- Los defaults son **neutros**: `GustK` = 0 → la rama uniforme se saltea y `GustLeanVS` devuelve `G` sin tocar (exacto en el modelo; en la GPU, control negativo de M5). Con una ráfaga activa, los vértices fuera del frente también devuelven `G` sin cambios (`x − 0·k = x`).
- 🔴 `apply_valley_material_A.py` los va a listar como `sobrantes` si alguien re-aplica el valle: **no borrarlos** (son de la capa de vida). `apply_valley_material_B.py` reconecta `ValleyGradVS → V_VI0`: la franja se apaga (neutro); volver a pegar `apply_vida_gust_valley.py`.
- 🔴 **MIDs viejos:** los MIDs de `Ground` de `Entering_Valle` existen desde antes de que el material tenga los `Gust*` → recargar el nivel después de aplicar el material (paso M6).

### 6.4 Medido (modelo del valle con el look actual, ojos a 2,10 m del piso; lo que tapa el metaball NO cuenta)

| | Lateral | Soplo |
|---|---|---|
| Contraste máximo visible (fuera del disco del metaball) | **+11,7 niveles** (8 bits) | +11,7 niveles |
| Dónde (lo que cambia ≥ 3 niveles, p10-p90 de elevación) | **−3,4 a −1,8°**: el llano de 25 a 70 m, a los costados del metaball | −3,4 a −2,1°: una línea horizontal que sube hacia el horizonte |
| Flujo normal del patrón de luz (ponderado por cuánto cambia) | p50 0,4 · p90 1,9 · p99 4,6 °/s | p50 0,3 · p90 0,9 · p99 5,5 °/s |
| La cresta visible (seguida por anillo / por columna, refinada) | en azimut: mediana 1,2 · p90 6,5 °/s | en elevación: mediana 0,2 · p90 0,4 °/s |

Rev. 1 contra rev. 2: el contraste de la rev. 1 (+8) incluía la parte tapada por el metaball y la franja vivía a −3/−5°; el "p90 26,7°/s" del soplo era un artefacto del centroide (la franja crecía desde los costados): ahora se sigue la cresta. Referencia: el oleaje de luz del propio valle mueve el llano a ≤ 5,2°/s y su animación cambia hasta ~30 niveles en 13 s en algunos puntos; la franja es un evento local y transitorio (no un campo): §8.

---

## 7. Sonido

| Archivo | Duración | Pico | RMS máx (50 ms) | Bandas | Qué es |
|---|---|---|---|---|---|
| `SND_VidaGustA/B/C.wav` | 28 s | −16 dBFS | −26,4 / −26,7 / −26,7 dBFS | < 200 Hz 18 %; brillo cerca ~1,5 kHz / lejos ~0,55 kHz | la ráfaga lateral: se acerca de un lado, el máximo cuando pasa por el usuario, se va |
| `SND_VidaSoplo.wav` | 18 s | −10,5 dBFS | −20,8 dBFS | **91,5 % en 500-4000 Hz**, 4,8 % en 150-500, 0 % < 200; brillo cerca 2,4 kHz / lejos 1,0 kHz | el soplo: un siseo que nace cerca (máximo a ~2,4 s) y se aleja oscureciéndose y bajando (a 60 m, ~0,3) |

- **Síntesis** (`scripts/make_vida_sounds.py`, numpy + scipy): ruido filtrado en cuatro capas mezcladas por la envolvente del **mismo reloj** (`vida_model`: cerca = la actividad del frente 2 m delante del usuario; lejos = la ráfaga en el llano), con soplos lentos adentro (0,4 y 1,3 Hz). Mono 48 kHz 16 bit. **Sin clics:** las puntas valen 0, fundidos coseno de 0,3 s, pasaaltos 30 Hz (DC ~1e-9). Espectrogramas: `vida/audio/sonidos_rafaga.png`; informe: `vida/audio/informe_sonidos.txt` (rev. 2: el brillo "lejos" ya no da NaN).
- **El soplo contra el pacer (rev. 2):** el soplo sale, por diseño, al empezar la exhalación, justo cuando suena `SND_PacerExhale` (un tono de 4 s, RMS −20,5 dBFS, 93 % de su energía en 150-500 Hz). En la rev. 1 el soplo tenía −35,3 dBFS en esos 4 s y la mitad de su energía en la misma banda: probablemente no se oía. Ahora: **cuerpo 450-1400 Hz, siseo 900-3500, susurro 2,6-6,2 kHz**, normalizado a **RMS −27 dBFS en los primeros 4 s** (+8 dB) con el pico tope en −9 (queda −10,5); su pico llega a ~2,4 s, y después baja con la distancia del frente (la fuente no tiene atenuación: la trae el archivo), después del ataque del tono. En la banda de 500-4000 Hz el pacer no tiene energía: no lo enmascara (y es la zona más sensible del oído y la que mejor dan los parlantes de la Quest). **Se valida escuchando en el visor con el pacer sonando** (S3).
- **Laterales:** el cuerpo empieza en 120 Hz (antes 45: un 30 % de su energía estaba debajo de 200 Hz, donde los parlantes de la Quest no dan); ~13 dB debajo del pacer en RMS: un viento de fondo.
- **Importar** (paso A1-A3, gotcha 434): copiar los 4 `.wav` a `VR_Test/Content/SoulCharger/Mechanics/Breath/Life/Audio/` con el editor abierto → en ~3 s aparecen los `SoundWave` (auto-import). Después, en cada uno (`set_properties`, una propiedad por llamada): `bLooping` false, compresión ADPCM.
- **Reproducir:** el `AudioComponent` `GustAudio` del actor, con atenuación propia **espacializada sin atenuación por distancia**; `VidaSnd` hace `SetSound → SetPitchMultiplier → SetVolumeMultiplier → ubicar → Play`, y `VidaAudio` lo mueve cada cuadro con el frente: lateral, por una línea paralela a la trayectoria a `SndFwd` 8 m delante (el paneo cruza de un lado al otro); soplo, sobre la trayectoria desde 1,5 m (se aleja al frente).
- 🔴 **El pitch cambia el timbre:** `pitch = SndLen/GustLife` (recortado a 0,75-1,33). Con la palanca de confort `GustLife` 36 el pitch baja a 0,78 (~4 semitonos más grave: el viento se oscurece) y con 40 queda en 0,75 y el sonido termina ~2,7 s antes que la ráfaga. **Si `GustLife`/`BreathLife` cambian más de ~15 %, regenerar**: cambiar `BP` en `vida_model.py` (con `SndLen`/`BreathSndLen` iguales a la duración nueva) y correr `python scripts/make_vida_sounds.py <carpeta de Content>/Audio` (Unreal los reimporta solo).

---

## 8. Confort (modelo, los dos ojos, IPD 6,4 cm)

| Regla | Cómo se cumple | Medido |
|---|---|---|
| Nada cerca de los ojos; el volumen del aliento es suyo | alfa × `smoothstep(NearMin 120, NearFull 180 cm, distancia al punto ciclópeo)` + la nube empieza en 1,3 m | mota visible más cercana: **123-126 cm**; **0** motas visibles a < 110 cm de un ojo (calma, ráfaga, soplo, relajación) |
| Nada de flujo coherente de campo amplio | en calma solo meandro (incoherente); en la ráfaga el lazo es cerrado y el sentido vertical al azar; la **deriva** sí es coherente (es el viento) | **flujo coherente** (media vectorial ponderada de la velocidad en la imagen): calma **0,02°/s**; ráfaga lateral ≤ **1,04°/s** (transitorio, ~10 s); relajación 0,42°/s; soplo ≤ 0,55°/s. Cobertura del ojo: **0,15-0,20 %** (puntos dispersos) |
| Lo rápido se apaga | alfa × (1 − `smoothstep(6, 12°/s, velocidad angular analítica)`) | calma p99 0,5°/s; ráfaga p99 3,0-3,9, máx 4,7°/s; soplo p99 4,7, máx 7,5°/s (ya apagándose); relajación p99 1,0°/s |
| Nada congelado | el meandro crece con la distancia (`MeanderFar`) | velocidad propia en calma, p50: 1,3-3 m 0,17 · 3-10 m 0,13 · 10-20 m 0,15 · 20-40 m 0,11 °/s (rev. 1: 0,08 / 0,03 / 0,02 lejos) |
| Sin rivalidad binocular | todo lo que decide el alfa, desde el punto ciclópeo | diferencia de alfa entre ojos: **0** (rev. 1: p99 0,44, máx 1,0 en el borde del metaball) |
| Sin vección por la franja | solo luz (sin relieve), contraste ≤ 12 niveles, un evento local; nada a < 25 m (`GustNear`): el piso cercano, el metaball y el cielo quedan quietos (el marco estable) | flujo normal p50 0,4 · p99 4,6°/s (lateral); cresta p90 6,5°/s en azimut |
| El metaball limpio | alfa × `smoothstep(radio angular + 2°, + 8°, ángulo a su centro)`, radio = `SoulR`·escala | 0 motas visibles dentro del disco + 2° |
| No "suciedad en el lente" | el polvo vive en el MUNDO (paralaje), nada cuelga de la cabeza | — |
| Sin centelleo | tamaño ≥ 0,2°; titileo ≤ 0,25 Hz | — |
| Sin saltos | lazo cerrado y deriva con retorno exactos; fases integradas | ningún salto (`|dP − V·dt|` ≤ 1,3e-3 cm por cuadro) |

**Lo que el modelo no puede decir:** si ~255-350 puntos en estéreo se leen como "polvo en la luz" o como "nieve" (`DustAlpha`, `VidaAmount`, el juego sutil), si la deriva coherente de ~1°/s durante ~10 s se siente como viento o tira del cuerpo, y si la franja cruzando a ~1-6°/s en los costados tira. **Se juzga en el visor, en el orden de la §13 S3, empezando por el juego visible y bajando.**

---

## 9. Costo

| Parte | Cuenta | Estimado |
|---|---|---|
| `DustVS` | ~510 op-eq por vértice con la rama de la ráfaga (~350 sin ella) × 8192 vértices × 3 (dos ojos + binning, gotcha 454) ≈ 12,5 M op-eq | **0,03-0,09 ms** (el aliento, 4,6 M op-eq, se estimó 0,025-0,05) |
| `DustPS` | cobertura ≤ 0,20 % del ojo × ~12 op-eq × 3 (quads chicos) | < 0,005 ms |
| `GustLeanVS` | 21.601 vértices del valle × 2-3 × ~45 op-eq, **solo mientras el frente pasa** (rama uniforme) | 0,005-0,01 ms |
| Sonido | una voz ADPCM | 0 GPU; CPU de audio despreciable |
| Blueprint | `VidaTick` ~300-400 nodos + 12 vectores a dos MIDs | 0,1-0,25 ms de hilo de juego, sin medir (Entering está limitada por GPU) |
| **Total GPU** | | **≤ ~0,1 ms** (0 con `VidaAmount` 0: el componente se oculta) |

Contexto honesto: la etapa mide ~9,4 ms + el valle 1,2-2,5 (estimado, sin medir) + el aliento ~0,05 → quedan ~1,9-3,2 ms de 13,9. La vida entra holgada **si** el valle entra; el número que decide todo sigue siendo `FONDO = m0 − m4`.

**Banco** (`quest_entering_perf.ps1 -Modos 0,4,5,6`, sin modificarlo; rev. 2): `PerfE0..E4` ponen la vida en **modo 3** (el polvo normal y **ninguna ráfaga**): `FONDO = m0 − m4` ya no tiene la franja al azar en unas ventanas sí y en otras no; `PerfE5`/`PerfE6` llenan / ocultan la vida (en esa sesión **`AIRE (m5 − m6)` pasa a ser AIRE + VIDA**); el `PerfEEnd` del cierre del script la devuelve a normal. Para aislar la vida: `ke * PerfV1` (sin vida) / `PerfV2` (llena) / `PerfV0` (normal) por adb, y comparar `App=` de VrApi. 🔴 **Antes de un banco aislado del valle (`PerfValley1/3`)**, mandar `ke * PerfV1` (la franja apagada: con `ValleyGradVS` en 0, `GustLeanVS` le sumaría la franja igual) y `PerfV0` después. Si la vida pasa de 0,15 ms: regenerar la malla con menos motas (`N_BASE`); la palanca real es la cantidad.

---

## 10. Previsualizaciones sin Unreal y crítica honesta

Carpeta `VR_Test/Saved/ClaudeScripts/vida/` (las hacen `sim_vida.py linea` → `render_vida_valle.py` (Blender) → `sim_vida.py componer`): el valle del modelo con el **look actual** (FogStart 800, FogDist 20000, FogMax 0,93, HFogDist 15000, HFogFall 2500, MorphAmt 0,3, valle en Z −90,4) y la franja por vértice; el polvo dibujado con el modelo, **con su tamaño angular real**, compuesto en lineal (como el Quest). Todo con el juego **visible** (los defaults).

| Archivo | Qué muestra |
|---|---|
| `vida_rafaga.gif` / `vida_rafaga.mp4` | 38 s desde los ojos (70°, 900×660): calma 2,5 s → una ráfaga lateral entera → los primeros 8 s de la relajación; 5 cuadros/s del modelo, **se reproduce ×2** |
| `vida_cuadros_clave.png` | 4 cuadros rotulados a 90°: calma · entra · pasa por el usuario · se va (con el polvo corrido) |
| `vida_soplo.png` | el soplo en 3 momentos (frente a 4, 30 y 50 m) |
| `vida_franja.png` | la franja sola: \|ráfaga − calma\| ×8 |
| `vida_polvo_detalle.png` | recortes ×3 del polvo (junto al resplandor y en el llano cercano), en calma y en el pico |
| `audio/sonidos_rafaga.png` | envolventes y espectrogramas de los 4 soplos |

**Crítica (mirándolos):** en la §17, junto con los resultados de la última corrida.

---

## 11. Riesgos

| Riesgo | Probabilidad | Mitigación / detección |
|---|---|---|
| El polvo ensucia o se lee como "nieve" (el default es ahora el visible) | media | el juego sutil (tabla 5.3): `DustAlpha` 0,7, `SunBase` 0,35; o `VidaAmount` 0,5 (BP) |
| El polvo no se percibe | baja-media | `DustSizeDeg` 0,28, `SunBase` 0,6 |
| La deriva "empuja" o tira del cuerpo (flujo coherente ~1°/s ~10 s) | baja-media | `DriftCm` 20 (sutil) o 0 (solo el lazo, la rev. 1); `DriftRelax` 40 (vuelve más lento) |
| La franja no se lee | baja-media | `GustLight` 3, la franja oscura (`GustRuffle` 0,1), `OffsetMin/Max` |
| La franja cruzando tira del cuerpo (vección) | baja | `GustLife` 36 (más lenta; regenerar los WAV), `GustLight` bajo; `bGusts` false = sin ráfagas |
| El soplo no se oye con el pacer | baja | ya separado en banda (+8 dB, 500-4000 Hz); si no: `GustVolume` 1, o subir `SOPLO_RMS4_DBFS` y regenerar |
| Soplos que llegan tarde o no llegan (el detector con el ruido real) | media | es el detector del aliento con sus defaults (los umbrales son **literales** del DSL, 0,10/0,04). Si en S3 el aliento necesita `VelEnter` más alto, cambiar los dos literales en `VidaBreath` (cirugía de 2 pines) |
| Demasiadas ráfagas | media | `GapMin/GapMax` 40/90 |
| Alguien re-aplica el valle y la franja se apaga / borra los `Gust*` "sobrantes" | media | §6.3; `vida_dryrun.py` lo prueba; nota en el tracker del valle y en `Valley_CABLEADO.md` (paso T9) |
| Los 4 nodos de audio agarran el homónimo de `SynthComponent` | **seguro** (documentado en `BP_Sequencer_SC.md`) | B12: `VidaSnd` se arma **directamente** por cirugía con `declaring_class /Script/Engine.AudioComponent` |
| `AttenuationOverrides` como texto no se escribe | media | verificar con `get_properties`; si no: `AdjustAttenuation` en `VidaReset` (B14) |
| El rig no tiene `CamRef` todavía cuando arranca la vida | baja | `VidaCamC` pregunta `IsValid` cada cuadro: mientras tanto `VidaC.w` = 0 (cada ojo usa su cámara, como la rev. 1) |
| Sonido muy fuerte o fatigante en 15 min | baja-media | `GustVolume` 0,5; mezclar con auriculares y escuchar en los parlantes del visor |
| Un `type_id` del DSL no existe con ese nombre | media | B9: `find_node_types` ANTES de escribir; corregir el `.dsl`, re-correr `vida_dsl_sim.py` |
| El Construction Script escribe en el valle desde el editor | baja | protegido con `IsValid`; si el CS del valle corre después, la franja de la vista previa desaparece hasta tocar una perilla del actor de vida |
| Costo mayor al estimado | baja | §9: banco aislado con `PerfV0/1/2` |

---

## 12. Rollback

| Qué | Cómo |
|---|---|
| Apagar la vida sin tocar nada | `bVida` false **o** `VidaAmount` 0 en la instancia `Entering_Vida`: el polvo se va en ~3 s y no sale ninguna ráfaga nueva (la que está en curso termina, con su sonido). Solo las ráfagas: `bGusts` false o `GustAmount` 0 + `GustVolume` 0 |
| Quitar la franja del valle | pegar `scripts/rollback_vida_gust_valley.py` (reconecta `ValleyGradVS → V_VI0`) → `recompile`: **el valle compilado vuelve a ser el de antes; en el grafo quedan 6 expresiones sueltas** (`GustLeanVS` y los 5 `Gust*`, sin compilarse) hasta borrarlas: (opcional, en llamadas SUELTAS y después del recompile, gotcha 401) `delete_expression` de lo que lista en `para_borrar` → `recompile` |
| Quitar el actor | ocultarlo; borrarlo lo hace Beltrán o se pregunta (sacar actores se pregunta) |
| Todo | con el editor cerrado, restaurar los `.uasset` del respaldo del paso P4 (`capa_vida_backup/`). 🔴 Git no sirve: `Test_Entering.umap` y `Mechanics/Breath/Valley/` están sin versionar; lo nuevo (`Mechanics/Breath/Life/`) también nace sin versionar |

---

## 13. RECETA PARA EL EDITOR (paso a paso)

**Reglas de la sesión** (las del aliento, §11 de su plan): `toolset_name` con el path completo; todo `execute_tool_script` con la plantilla `scripts/safe_script.py` (try/except `BaseException`); **canario** (cantidad de actores de `Test_Entering`) antes y después de cada tanda; **nunca** compilar con PIE corriendo; guardar **con rutas explícitas** (nunca `save_assets([])`: hay otros agentes); **un script puede correr dos veces** (todos los de acá son idempotentes); `set_properties` con `values` como **texto JSON** (gotcha 483) y vectores/rotaciones en **formato texto** `"(X=..,Y=..,Z=..)"`; verificar SIEMPRE releyendo.

### P — Preparación (15 min)
- **P1.** `SceneTools.get_current_level` → `/Game/Test_Entering`. Si es otro y está sucio, NO cambiar de nivel (es de otro agente).
- **P2.** `EditorAppToolset.IsPIERunning` → false.
- **P3.** Canario: contar los actores de `Test_Entering` (tras el aliento: 16; anotar el real).
- **P4.** Respaldo (PowerShell): copiar `VR_Test/Content/SoulCharger/Mechanics/Breath/Valley/M_BreathValley_SC.uasset` y `VR_Test/Content/Test_Entering.umap` a `VR_Test/Saved/ClaudeScripts/capa_vida_backup/`.
- **P5.** En disco (desde `.claude/skills/unreal-vr/scripts/`): `python plan_vida_materials.py`, `python hlsl/Vida_check.py`, `python vida_dryrun.py`, `python vida_dsl_sim.py` (~10 min), `python hlsl/Valley_check.py` → todos **TODO OK**.
- **P6. Coordinación (obligatorio):** preguntar a Beltrán si alguna sesión está editando `M_BreathValley_SC` o `Test_Entering`. Si sí, esperar. Avisar que durante M3/M5 el log puede mostrar errores transitorios (gotchas 471/479).

### M — Materiales (35 min)
- **M1.** `AssetTools.create_folder("/Game/SoulCharger/Mechanics/Breath/Life")`.
- **M2. Malla:** `StaticMeshTools.import_file({folder_path:"/Game/SoulCharger/Mechanics/Breath/Life", asset_name:"SM_ValleyDust_SC", source_file:"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/vida/SM_ValleyDust_SC.fbx", import_materials:false, import_textures:false})` → `get_vertex_count` **8192**, `get_triangle_count` **4096**, `get_bounds` ≈ X −3157…3214, Y −3491…3423, Z −195…2612 → `is_nanite_enabled` false → `remove_collisions` → `ObjectTools.get_properties(SM, ["LightMapCoordinateIndex"])` **≥ 4** (si no: desactivar `bGenerateLightmapUVs` y reimportar).
- **M3. Material del polvo:** pegar **entero** `scripts/apply_vida_dust_material.py` → esperado: `flags` Unlit/AlphaComposite/two-sided/sin niebla; `params.total` **34**, `sobrantes` []; `customs` `DustVS` **38/38** y `DustPS` 3/3; `internas_y_salidas_ok` "5 de 5"; `mi_creada` true; `log` []. Canario. Si `AdditionalOutputs` no se escribió: la clave `additionalOutputs` (gotcha 446) y re-pegar. Si `connect_to_output` con `return` falla: `""` (gotchas 447/482). → `MaterialTools.recompile` de `M_ValleyDust_SC` → grepear el log SOLO después de la línea del `recompile` (gotcha 479): nada de `M_ValleyDust_SC`.
- **M4.** `StaticMeshTools.get_material_slots(SM)` → `set_material(SM, <slot>, MI_ValleyDust_SC)`. Guardar SM, M, MI (rutas explícitas).
- **M5. La franja en el valle:** captura de control ANTES (`captureTransform` (0, 0, 120), pitch −2; dos, separadas unos segundos, para medir el ruido del oleaje; una descartable antes, gotcha 476) → pegar **entero** `scripts/apply_vida_gust_valley.py` → esperado: `params.gust` los 5, `custom` 8/8 sin fallos, `vi0_a_gust` true, `log` []. Si devuelve `err`: no tocó nada; leer el mensaje. Canario. `recompile` de `M_BreathValley_SC` y el log después del `recompile`: nada de `M_BreathValley_SC`. **Control negativo (es la verificación del neutro en la GPU):** la captura desde el ojo **igual** a la de antes en el cielo y el piso cercano (el llano lejano cambia solo con el oleaje: compararlo contra el ruido de las dos capturas de control). Guardar `M_BreathValley_SC` (ruta explícita).
- **M6. Recargar el nivel** (MIDs viejos): `AssetTools.is_dirty("/Game/Test_Entering")` → si está sucio, preguntar; si no, `SceneTools.load_level("/Game/Test_Entering")` → canario igual que P3.

### A — Audio (10 min)
- **A1.** PowerShell: copiar `VR_Test/Saved/ClaudeScripts/vida/audio/SND_Vida*.wav` a `VR_Test/Content/SoulCharger/Mechanics/Breath/Life/Audio/` (crear la carpeta). Esperar ~3-5 s: `AssetTools.find_assets("/Game/SoulCharger/Mechanics/Breath/Life/Audio", "SND_Vida")` → 4 `SoundWave`.
- **A2.** En cada uno, `get_properties(["bLooping","Duration","NumChannels"])`: `bLooping` false, **28/28/28/18 s**, 1 canal. `set_properties({"SoundAssetCompressionType":"ADPCM"})` (una llamada; verificar). Guardar los 4.

### B — `BP_ValleyLife_SC` (80 min)
> ✅ **Hecho el 2026-09-29** (tras perder la primera construcción en un crash de GPU sin guardar): la secuencia que funcionó, con los scripts, está en `VR_Test/Saved/ClaudeScripts/vida/receta_bp_rapida.md`. Desvíos: 4 grafos por componentes y `VidaDue` con un solo `elif` (gotcha 490); B14 no hizo falta. **Guardar el BP después de cada tanda**, no solo en B13.
- **B1.** `BlueprintTools.create({folder_path:"/Game/SoulCharger/Mechanics/Breath/Life", asset_name:"BP_ValleyLife_SC", asset_type:{refPath:"/Script/Engine.Actor"}})`.
- **B2. Componentes** (tabla 5.5): `get_default_object` → `ActorTools.add_component` `/Script/Engine.StaticMeshComponent` (`DustMesh`) y `/Script/Engine.AudioComponent` (`GustAudio`) → en cada plantilla `<Comp>_GEN_VARIABLE`, **una propiedad por llamada**: `staticMesh`, `overrideMaterials` `[{"refPath":"/Game/SoulCharger/Mechanics/Breath/Life/MI_ValleyDust_SC.MI_ValleyDust_SC"}]`, `BodyInstance` (los dos campos, gotcha 239), `castShadow` false, `translucencySortPriority` 5, `bReceivesDecals` false; en `GustAudio`: `bAutoActivate` false, `bOverrideAttenuation` true, `AttenuationOverrides` `"(bAttenuate=False,bSpatialize=True)"` (texto). Verificar todo con `get_properties`.
- **B3. Variables:** tabla 5.4 (`add_variable`, categorías `A-Vida`, `B-Rafagas`, `C-Soplo`, `D-Sonido`, `E-Prueba`; `set_variable_instance_editable` true) + los dos arrays `GustSounds`/`BreathSounds` (`add_object_variable` de `SoundBase` con `container_type: "Array"`) + tabla 5.5 (`Z-Vida`, no editables; `OrgW`/`DirW`/`SndOffW` Vector, `PerfMode` int, `Valley`, `Blob` y `Rig` con `add_object_variable` a `/Game/SoulCharger/Mechanics/Breath/Valley/BP_BreathValley_SC.BP_BreathValley_SC_C`, `/Game/SoulCharger/Mechanics/Breath/BP_BreathBlob_SC.BP_BreathBlob_SC_C` y `/Game/SoulCharger/Mechanics/Breath/BP_BreathRig_SC.BP_BreathRig_SC_C`). `compile_blueprint` → defaults del CDO según la tabla 5.4 (bools y escalares) y los arrays con los 4 sonidos → verificar → compilar.
- **B4. Funciones:** `add_function_graph` de las **37 funciones** de la tabla 5.6 (todas las `fn` de `vida.dsl` menos `ConstructionScript`); `add_function_param` float de entrada: `DT` (`VidaBreath`, `VidaRelaxStep`, `VidaRelax`, `VidaSchedule`, `VidaState`, `VidaTick`), `Sign` (`VidaStartLat`), `Pitch` (`VidaSnd`, `VidaPlayG`, `VidaPlayB`), `Live` (`VidaPushCam`, `VidaPushDust`); `add_object_function_param` `Snd` (SoundBase) en `VidaSnd` → compilar.
- **B5. Colisión de nombres:** `find_node_types(<grafo>, "CallFunction|Vida")` → cada `CallFunction|Vida*` tiene que resolver a ESTE BP (verificar pines con `get_node_infos` tras escribir; gotchas 456/462).
- **B9. `type_id` a confirmar con `find_node_types` ANTES de escribir**: `Math|Trig|Cos(Degrees)`, `Math|Trig|Sin(Degrees)`, `Math|Float|Absolute(Float)`, `Math|Float|Truncate`, `Math|Integer|%(Integer)` (gotcha 450), `Math|Float|Fraction`, `Utilities|Array|Length`, `Utilities|Array|Get(acopy)`, `Transformation|GetActorRotation`, `Transformation|GetActorLocation`, `Transformation|GetActorTransform`, `Transformation|GetActorScale3D`, `Transformation|GetWorldTransform`, `Transformation|SetWorldLocation`, `Class|BPBreathValleySC|GetGround`, `Class|BPBreathRigSC|GetCamRef` (el del aliento), `Actor|Tick|AddTickPrerequisiteActor` (el del aliento), `Rendering|Material|SetColorParameterValueonMaterials` ("on" minúscula), `Development|PrintString` (pin `bPrintToScreen`), y los getters de bools sin la `b` (`Variables|A-Vida|GetVida`, `Variables|B-Rafagas|GetGusts`, `Variables|C-Soplo|GetBreathGusts`, `Variables|Z-Vida|GetGusting`, `GetPrimed`, `GetExhOnset`, `GetSndWarned`, `GetForce`). Si un nombre difiere: corregir el `.dsl`, registrar el nombre nuevo en `vida_dsl_sim.py`, re-correrlo, recién ahí escribir.
- **B10. Escribir** cada bloque de `scripts/vida.dsl` en el orden del archivo (`VidaMPC` → … → `VidaBenchFull` → `ConstructionScript` en `:UserConstructionScript` → `EventGraph`, borrando antes los 3 eventos fantasma), **salvo `VidaSnd` (B12)**. Después de cada `write`: `read_graph_dsl` (ensucia el BP: gotcha 487, normal) y, en cada `CallFunction|X` con argumentos, `get_node_infos`: `self` = *Self Object Reference* y el argumento conectado (gotcha 461). En `VidaFind`: los `SetValley`/`SetBlob`/`SetRig` con el pin de valor conectado. En `VidaPushValley`: el `GetGround` con `self` alimentado por la variable `Valley`. En `VidaCamC`: el `GetCamRef` con `self` = `Rig`. Si un `write` falla, no deja nodos (gotcha 450): corregir y reescribir el grafo vacío.
- **B11. Puente `VidaMPC`:** igual que `AirMPC` (receta E11 del aliento): dos `create_node("Rendering|Material|GetScalarParameterValue", declaring_class "/Script/Engine.KismetMaterialLibrary")` → clase `K2Node_CallMaterialParameterCollectionFunction`; `Collection` = `/Game/SoulCharger/Mechanics/Breath/MPC_Breath.MPC_Breath`, `ParameterName` `Signed` / `On`; exec entrada → Get(Signed) → Get(On) → `SetVSig` → `SetVGate`; sus `ReturnValue` a los pines de valor.
- **B12. `VidaSnd` DIRECTAMENTE por cirugía** (no con `write_graph_dsl`: los nodos de audio resuelven al homónimo de `SynthComponent`, documentado en `BP_Sequencer_SC.md`): 4 `create_node` con `declaring_class /Script/Engine.AudioComponent` (`SetSound`, `SetPitchMultiplier`, `SetVolumeMultiplier`, `Play`) + `create_node` `CallFunction|VidaAudio` entre el volumen y el `Play`; exec: entrada → SetSound → SetPitch → SetVolume → VidaAudio → Play; `self` de los 4 = un `GetGustAudio`; `NewSound` = `Snd`, `NewPitchMultiplier` = `Pitch`, `NewVolumeMultiplier` = `GetGustVolume`, `StartTime` 0. Verificar pines con `get_node_infos`.
- **B13.** `compile_blueprint({warnings_as_errors:true})` → 0 errores. Canario. Guardar el BP (ruta explícita).
- **B14. Si `AttenuationOverrides` no quedó escrito** (B2): en `VidaReset`, cirugía de un `AdjustAttenuation` (`declaring_class /Script/Engine.AudioComponent`) sobre `GustAudio` con un `MakeSoundAttenuationSettings` (`bAttenuate` false, `bSpatialize` true), como `BP_Door_SC.ApplyAudio`.

### C — Colocar y vista previa (15 min)
- **C1. Colocar** (colocar sí; sacar se pregunta): `SceneTools.add_to_scene_from_asset("/Game/SoulCharger/Mechanics/Breath/Life/BP_ValleyLife_SC", "Entering_Vida", <xform>)` → **el transform no se aplica al colocar**: `set_properties` del root con `relativeLocation` `"(X=0.000000,Y=0.000000,Z=120.000000)"` y sin rotar → verificar con `get_actor_transform` → `set_actor_folder(actor, "Entering")`. **Diff instancia vs plantilla** (gotcha 478) en `DustMesh` y `GustAudio` de la instancia; y las variables de la instancia = CDO (si algo nació en 0, escribirlo en la instancia). Canario (+1). Guardar el nivel (`/Game/Test_Entering`).
- **C2. Vista previa desde el ojo:** con el viewport en tiempo real, `CaptureViewport` con `captureTransform` = (0, 0, 120), pitch −2 → **positivo:** puntitos dorados/blanco lavanda en el aire, más del lado del resplandor (derecha), nada sobre el metaball ni a menos de ~1,2 m (comparar con `vida/vida_cuadros_clave.png` "Calma" y `vida_polvo_detalle.png`). En la instancia, `PreviewGust` 0,5 → captura: la franja en el llano a los costados del metaball y el polvo encendido (como "Pasa por el usuario"); `PreviewKind` 1, `PreviewGust` 0,4 → la línea del soplo. **Negativo:** `PreviewGust` 0 → el valle igual a la captura de M5. Dejar `PreviewGust` 0.

### T — PIE (25 min)
- **T1.** Guardar (rutas explícitas) → `StartPIE({bSimulate:false, playMode:"PlayMode_InViewPort", warmupSeconds:16})`.
- **T2.** `GetLogEntries({pattern:"VIDA"})` → `VIDA: lista…` una vez; `Accessed None` → nada de `BP_ValleyLife_SC`.
- **T3.** En la instancia de PIE: leer `Wait`, `bGusting`, `Front`, `Glob`, `Hold` cada ~2 s: `Glob` → 1 en ~3 s; a los 14 s `bGusting` true, `Front` avanza de −58 a +58 m en 28 s; al terminar, `Hold` baja de 1 a 0 en ~20-25 s y recién ahí `Amp` 0. Traza por cuadro con un `execute_tool_script` (cada `execute_tool` = un cuadro, gotcha 488) de `Front`, `ActUser`, `Rate`, `Hold`: `ActUser` sube a ~1 hacia la mitad de la ráfaga y `Rate` a 3.
- **T4.** Soplo: en el rig de PIE, `bFakeBreath` true (y `Cycles` 0 en el pacer). Leer `Flow`, `bExhOnset`, `GustKind`: en el turno impar (`GustIdx` 1) la ráfaga espera y sale con `GustKind` 1 al empezar una exhalación.
- **T5. Lo que ve el juego:** `CaptureEditorImage` del viewport de PIE durante una ráfaga (cámara ~20° abajo, **girando el pawn con `set_actor_transform`**, nunca `set_properties` sobre la `Camera`: gotcha 488). En el material del polvo de la instancia, `VidaC.w` = 1 (el punto ciclópeo llegó del rig).
- **T6.** Sonido: `GustAudio` de la instancia PIE → `get_properties(["Sound","PitchMultiplier","VolumeMultiplier"])` en una ráfaga y su `RelativeLocation` viajando.
- **T7.** `GustNow` y pánico: con `VidaAmount` 0 en la instancia de PIE, esperar > 60 s: ninguna ráfaga (`GustIdx` quieto). Volver a 1.
- **T8.** `StopPIE`. **Simulate** (sin pawn, sin respiración): sin errores; solo laterales; `VidaC.w` 0.
- **T9.** Canario; `is_dirty`; guardar con rutas explícitas.
- **T10.** Trackers: `blueprints/BP_ValleyLife_SC.md` (de planificado a construido), `_INDEX.md`, `BP_BreathValley_SC.md` (la franja: el cableado nuevo de `V_VI0` y "no borrar los Gust*"), `scripts/hlsl/Valley_CABLEADO.md` (idem), `references/assets-existentes.md`, `docs/MECANICAS-PORTABLES.md`. **No commitear sin pedido.**

### S — Paquete, banco y visor (con Beltrán)
- **S1.** Antes del cook (gotcha 474): `PreviewGust` 0 en el CDO y en la instancia; guardar lo tocado; `is_dirty` false; mtime anterior al cook. Development.
- **S2.** `quest_entering_perf.ps1 -Modos 0,4,5,6` → FONDO = m0 − m4 (con la vida en modo 3: el polvo normal y sin ráfagas en las dos) y AIRE+VIDA = m5 − m6. Aislado: `ke * PerfV1/PerfV2/PerfV0` por adb (§9). 🔴 Antes de un `PerfValley1/3`: `ke * PerfV1`; después `PerfV0`.
- **S3. Visor, en este orden:** (1) calma: ¿se ve el polvo? ¿es polvo en la luz o es nieve? ¿se confunde con el aliento? → bajar hacia el juego sutil (tabla 5.3) si ensucia; (2) `ke * GustNow` **en calma** (con una ráfaga en curso sale al terminar ella, hasta ~30 s después): ¿se lee la ráfaga (sonido + polvo que se va con el viento + franja a los costados)? ¿tira del cuerpo? → `DriftCm`, `GustLight`, `GustLife`; (3) respirando: ¿el soplo sale con la exhalación, se oye encima del pacer y se lee como "mi aire"?; (4) 15 min: ¿demasiadas ráfagas? → `GapMin/GapMax`; ¿fatiga el sonido? → `GustVolume`. Cada cambio de CDO pide re-empaquetar; los de la MI y la instancia también.

---

## 14. Lo hecho en disco y los chequeos corridos (2026-09-28, rev. 2)

**Archivos nuevos** (nada de otras sesiones modificado):

| Archivo | Qué |
|---|---|
| `docs/PLAN-VIDA-VALLE-2026-09-28.md` | este plan (las tablas 5.2, 5.4 y 6.3 las verifica `Vida_check.py` contra el modelo) |
| `.claude/skills/unreal-vr/scripts/vida_model.py` | modelo de referencia: semillas, codificación de la malla, `dust_vs`/`dust_ps`, `gust_lean_vs`, `VidaBP` (el reloj, la deriva, el soplo, empujes, sonido, vista previa, banco), los juegos sutiles |
| `scripts/hlsl/DustVS.hlsl`, `DustPS.hlsl`, `GustLeanVS.hlsl` | los tres Custom |
| `scripts/hlsl/Vida_check.py` | verificador: estático, compilación, HLSL = modelo, controles, mutaciones, V invertida + fp16 |
| `scripts/gen_valley_dust.py` | malla (Blender headless) → `vida/SM_ValleyDust_SC.fbx` + verificación por reimportación |
| `scripts/plan_vida_materials.py` | plan de armado → `vida/vida_build.json` |
| `scripts/apply_vida_dust_material.py`, `apply_vida_gust_valley.py`, `rollback_vida_gust_valley.py` | los scripts para pegar en Unreal (idempotentes) |
| `scripts/vida_dryrun.py` | corre esos scripts contra el editor simulado de `dryrun_material_script.py` (importado, no modificado) |
| `scripts/vida.dsl` | los grafos del BP |
| `scripts/vida_dsl_sim.py` | ejecuta el DSL con el intérprete de `dsl_sim.py` (importado, no modificado) y lo compara con el modelo |
| `scripts/make_vida_sounds.py` | los 4 WAV + informe + espectrogramas |
| `scripts/sim_vida.py`, `scripts/render_vida_valle.py` | mediciones y previsualizaciones (el render importa `preview_breath_valley.py` sin modificarlo) |
| `blueprints/BP_ValleyLife_SC.md` | tracker (planificado) |
| `VR_Test/Saved/ClaudeScripts/vida/` | FBX, `vida_build.json`, `audio/` (4 WAV, informe, PNG), `preview/`, GIF, MP4, cuadros clave, `medidas.txt`, logs de los chequeos |

**Chequeos:** la tabla con los resultados de la última corrida está en la §17.

---

## 15. Decisiones para Beltrán

1. **El nivel:** visible (default, tabla 5.3) → bajar hacia el sutil mirando si ensucia, se confunde con el aliento o tira del cuerpo.
2. **La franja:** clara (default: el pasto agarra luz, +12 niveles a los costados del metaball) u **oscura** (`GustRuffle` 0,1, `GustLight` 0: el viento rompe el brillo rasante, lectura de "viento en el agua"). O las dos suaves.
3. **El viento que se lleva el polvo:** con deriva (default, `DriftCm` 40: el polvo queda corrido y vuelve en ~25 s) / más suave (20) / solo el lazo (0, la rev. 1).
4. **Cuántas ráfagas:** hoy una por minuto aprox. ¿Más calma? `GapMin/GapMax` 40/90.
5. **El soplo (un solo aire):** sí (una de cada dos, con la exhalación) / solo laterales (`bBreathGusts` false) / todas soplos (`BreathEvery` 1).
6. **Tanda 2 si suma:** que la bruma se abra al paso de la ráfaga; eventos `ke` para ajustar perillas en el visor sin re-empaquetar; que las ráfagas se calmen con la coherencia de la respiración.

---

## 16. Revisión 2: los problemas de la revisión y cómo quedaron

| Sev. | Problema | Arreglo | Verificación |
|---|---|---|---|
| alta | El polvo cercano competía con el aliento y se confundía con él (mismo perfil, paleta, tamaño y profundidad; ~24 motas quietas a < 95 cm en las pausas) | `NearMin/NearFull` 45/80 → **120/180** y la nube de base empieza en **1,3 m** (antes 0,55): el soplo sigue andando (su polvo "de adelante" es de 1,3-5 m). **Paleta propia**: `ColLit` dorado (1, 0,93, 0,74), `ColDim` blanco lavanda (0,92, 0,9, 0,96), sin el azul del aliento | `Vida_check.py`: 0 motas visibles a < 110 cm de un ojo en calma, ráfaga, soplo y relajación; `sim_vida medir`: la más cercana a 123 cm |
| media | El soplo quedaba enmascarado por el tono de exhalar del pacer (15-17 dB debajo, en la misma banda) | el soplo en **450-6000 Hz** (91,5 % en 500-4000, 4,8 % en 150-500) y **+8 dB** (RMS −27 dBFS en los primeros 4 s, pico −10,5), y baja al alejarse; su pico a ~2,5 s, después del ataque del tono. Las laterales, sin energía inútil debajo de 120 Hz | `informe_sonidos.txt` (bandas y RMS 0-4 s); **se confirma escuchando en el visor** |
| media | La legibilidad de toda la capa no alcanzaba para "más vida" | el default es el juego **visible** (tabla 5.3) y el sutil queda para bajar mirando; la franja **más alta** (−3,4/−1,8° en vez de −3/−5: `GustNear` 25 m, `OffsetMin/Max` 15-40 m, `FrontHalf` 40/70 m, `PathHalf` ±40 m), más clara (`GustLight` 2,8) y **a los costados del metaball** (el contraste se mide ahora fuera de su disco: +11,7) | `sim_vida medir` §6.4; previews §10 |
| media | La ráfaga no movía el polvo como viento (lazo que vuelve exacto: "ola de brillo") | **deriva neta a favor del viento** (p50 0,7 m, p90 1,5 m) que se relaja en `DriftRelax` s con una fase integrada (`Hold`); sin estado en el VS | `Vida_check.py`: al terminar el frente queda solo la deriva; con Hold 0, cero exacto; sin saltos; V analítica = derivada numérica. `vida_dsl_sim.py`: relajación y relevo sin saltos; control negativo (la rev. 1 con deriva salta 169 cm) |
| media | `bVida` / `VidaAmount` 0 no apagaban las ráfagas (el pánico seguía sonando) | `VidaMaybe` exige `bVida` y `VidaAmount` > 0 (modelo y DSL) | `vida_dsl_sim.py`: 150 s con cada uno, ni una ráfaga; control negativo sin la condición |
| baja | Rivalidad binocular en el borde del metaball (alfa por ojo) | todo lo que decide el alfa desde el punto **ciclópeo** `VidaC` (la cámara del rig) | `Vida_check.py`: alfa idéntico en los dos ojos (control sin él: 0,12); `sim_vida medir`: 0 |
| baja | La mitad del polvo casi congelada (0,02-0,08°/s lejos) | el meandro crece con la distancia (`MeanderFar` 10) | calma p50 0,11-0,17°/s a toda distancia |
| baja | Instrumentos: el centroide del soplo daba "p90 26,7"; NaN en el informe; el pitch cambia el timbre | se sigue la **cresta** (refinada) en vez del centroide y no cuenta lo que tapa el metaball; el brillo "lejos" ponderado por energía (sin NaN); el acople pitch/timbre documentado (§7) y los WAV regenerados a 28/18 s | `medidas.txt`, `informe_sonidos.txt` |
| baja | B12 presentado como condicional (falla seguro); "28 funciones" | `VidaSnd` se arma **directamente** por cirugía; ahora son 37 funciones (la cuenta sale de `vida.dsl`) | receta B4/B12 |
| baja | Sin orden de tick contra el rig | `VidaAfterRig` (`AddTickPrerequisiteActor(rig)` en `BeginPlay`, como el aliento) | `vida_dsl_sim.py`: un prerrequisito, el rig; ninguno en el Construction Script |
| baja | `ke * GustNow` se perdía con una ráfaga en curso y alargaba la espera del soplo | `GustNow` pone `bForce`: sale apenas se puede (acelera la relajación a ≤ 3 s, no espera el soplo, pasa por encima de `bGusts`) | `vida_dsl_sim.py`: en calma (1 cuadro), con una en curso (al terminar + ≤ 3 s), esperando un soplo (1 cuadro) |
| baja | El banco se contaminaba (ráfagas al azar en m0/m4; la franja encima de `PerfValley1/3`) | `PerfE0..E4` = modo 3 (sin ráfagas), `PerfEEnd` = normal; la receta manda `PerfV1` antes de un banco del valle | `vida_dsl_sim.py`: 120 s sin ráfagas con `PerfE0`; `PerfEEnd` la devuelve |
| baja | "Neutro bit a bit" redactado de más | "exacto en el modelo; en la GPU se verifica con el control negativo de M5"; el rollback deja 6 expresiones sueltas hasta borrarlas | §1, §6.3, §12, cabeceras de `GustLeanVS.hlsl` y `apply_vida_gust_valley.py` |
| extra | Con `BreathWait` 8 y un ciclo de 14 s, la mitad de los soplos se perdían | `BreathWait` 15 (≥ un ciclo) | 15 min respirando: 8 soplos de 16 (antes 5) |

---

## 17. Resultados de la última corrida y crítica de las previsualizaciones

**Chequeos (todos TODO OK, rev. 2; logs en `VR_Test/Saved/ClaudeScripts/vida/log_*.txt`):**

| Chequeo | Resultado |
|---|---|
| `hlsl/Vida_check.py` | **69/69**: cabeceras = modelo = tablas 5.2/5.4/6.3; dxc SM6 -WX, fxc SM5, glslc → SPIR-V + spirv-val (y el PS en half); `[branch]` → DontFlatten; `DustVS` traducido = modelo (14 estados, con deriva, relajación y punto ciclópeo; offset ≤ 4e-7 cm), `DustPS` y `GustLeanVS` exactos; valle neutro exacto en el modelo (600 vértices), cielo y suelo fuera del frente sin cambios, la franja nunca a < `GustNear`; sin presencia 0 píxeles; el polvo de ráfaga no existe en calma; confort (≥ 120 cm, disco del metaball libre, ≥ 0,2°); **0 motas visibles a < 110 cm de un ojo** (calma, ráfaga, soplo, relajación); **alfa idéntico en los dos ojos** con el ciclópeo (control sin él: 0,12); lazo cerrado exacto al empezar y con la deriva relajada; al terminar el frente queda solo la deriva; continuidad con el BP del modelo (sin saltos: `|dP − V·dt|` ≤ 1,3e-3 cm por cuadro); V analítica = derivada numérica (p99 0,6 %); **22/22 mutaciones detectadas** (5 nuevas: deriva sin Hold, deriva en contra, sin ciclópeo, meandro sin crecer, confort con la cámara del ojo); V invertida + fp16 y su control negativo |
| `vida_dryrun.py` | **27/27**: el polvo desde vacío (2 vueltas, idempotente, 38 + 3 entradas, 34 parámetros); la franja sobre el valle de hoy: el único cambio del grafo es `V_VI0.VS`; re-aplicar el valle la apaga y lista los `Gust*` como sobrantes; volver a pegar la repone; el rollback deja el resto del grafo igual y lista las 6 expresiones sueltas; sobre un valle incompleto aborta sin crear nada |
| `vida_dsl_sim.py` | **36/36**: lint (+ control); CS = `preview` (40 casos, error 0; sin ciclópeo ni prerrequisito en el editor); `EventTick` = `VidaBP` 360 s respirando (error ≤ 9e-16, 4 laterales + 3 soplos, sonidos idénticos); tickea después del rig; `VidaC` = la cámara del rig (y w 0 sin rig o sin `CamRef`); actor y valle girados; sin respiración; sin valle ni metaball; escala del metaball; sin sonidos; **pánico** (`bVida` false / `VidaAmount` 0: ninguna ráfaga en 150 s); **`GustNow`** en calma, con una en curso y esperando un soplo; **banco** (`PerfE0` sin ráfagas 120 s, `PerfEEnd` la devuelve); deriva: cierre exacto, sin saltos en la relajación ni en el arranque siguiente, y se ve (> 20 cm a mitad); 4 controles negativos detectados (Flow antes del inicio, sin el margen de 2W, `Amp` a 0 al terminar el frente, `VidaMaybe` sin `bVida`) |
| `gen_valley_dust.py` (Blender 5.2 headless) | VERIF OK: 8192 v, 2048 polígonos, 4 capas de UV (3e-8), centro = semilla (1,8e-4 cm) |
| `make_vida_sounds.py` | 4 WAV mono 48 kHz (28/28/28/18 s), puntas 0, DC ~1e-9; el soplo 91,5 % en 500-4000 Hz, RMS −27 dBFS en 0-4 s |
| `hlsl/Valley_check.py` (el del valle, intacto) | 90/90 |
| `sim_vida.py medir` | los números de §2, §6.4, §8 y §9 (`vida/medidas.txt`) |
| `vida_legibilidad.py` | motas que se distinguen en la foto de la calma (≥ 10 niveles): visible **91**, sutil 18, la rev. 1 15 (`vida/legibilidad.txt`) |

**Crítica de las previsualizaciones (mirándolas):**
- ✅ **El polvo ya no se confunde con el aliento:** no hay nada a menos de 1,2 m, y los puntos son dorados del lado del resplandor y blanco lavanda en el resto; ninguno cerca de la cara.
- ⚠ **¿Se siente más vivo? Más que en la rev. 1, y todavía una foto no alcanza.** En el recorte ×3 se ven puntos finos, más del lado de la luz; en la foto de la calma se distinguen 91 motas con ≥ 10 niveles (la rev. 1: 15). A 11,7 px/° una mota de 0,24° mide ~2,8 px: en el visor (16 px/°, estéreo, paralaje, el meandro y la deriva en movimiento) se leen más, **pero eso se confirma en S3**. Si todavía es poco: `DustSizeDeg` 0,28 y `SunBase` 0,6.
- ✅ **La franja se lee como un evento lateral:** en "entra" y "se va" es una lámina de luz clara pegada al horizonte, a un costado del metaball, más ancha y más alta que en la rev. 1 (+12 niveles fuera del disco). En "pasa" queda casi toda detrás de la esfera (es inevitable con el frente cruzando por delante: el evento está en los costados). En el GIF se ve entrar por la izquierda, desaparecer detrás del metaball y salir por la derecha.
- ✅ **El soplo** se lee como una línea clara que se va hacia el horizonte, a los dos lados de la esfera.
- ⚠ **La deriva** es de 0,7-1,5 m en motas de 5-30 m: en la foto casi no se nota (grados), en el GIF se nota poco (5 cuadros/s, 11,7 px/°): es de lo que más depende del visor. Si "empuja": `DriftCm` 20.
- ❌ **Lo que no muestran:** el metaball real (la esfera es de referencia), el estéreo, la velocidad real (el GIF va ×2), el sonido junto con la imagen, la capa viva respirando.
