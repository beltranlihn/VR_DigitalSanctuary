# BP_BreathRig_SC — el controller PORTABLE de la respiración (Entering)

**Ruta:** `/Game/SoulCharger/Mechanics/Breath/BP_BreathRig_SC` · material `M_BreathCtrl_SC` (duplicado de `M_SeqCtrl_SC`)
**Colocado en:** `/Game/Test_Entering` como `Entering_BreathRig` (carpeta `Entering`)
**Nació:** 2026-09-27 · pedido de Beltrán: *"un controller que sea solo para la respiración, que se active solo en esta etapa, en un blueprint que podamos mover de un lado a otro"*.
**Estado:** 🟢 **validado en visor** (2026-09-27): umbral en la panza con orientación del sensor, vibración, reacción del metaball, seguidor con frenada física. ⬜ mano izquierda en visor

## Qué es
**Duplicado de [[BP_BreathManager_SC]]** (el motor de umbral + señal + háptica ya extraído de `BP_Sensor_Soul`, con los valores afinados en visor) **+ la capa visual del rig** (mandos y sensores montados en las manos, como `BP_SeqRig_SC`). El motor no se reescribió: `Acquire, SenseHand, UpdateLevel, BreathThreshold, BreathHaptic, PickHand, Publish, StepFlows, PushMPC, TickBreathGated, BreathSleep` son los del manager, byte a byte. El manager queda para la galería de `TestMeshes`.
🔴 **No colocar el manager y el rig en el mismo nivel**: los dos escriben `MPC_Breath`.

## Contrato con el pawn (el mismo del manager y de `BP_ControllerRig`)
El pawn tiene una `CameraComponent` y dos componentes llamados **`HandRight`/`HandLeft` hijos de su MotionController Grip** (lo cumplen `BP_VRPawn_SC` y `BP_XRPawn`). Sin cast al pawn, sin director, **sin IMC propio**: la mecánica es posición + quietud + háptica, no hay botones (y por gotcha 426 un IMC propio no llegaría igual).

## Lo visual (nuevo)
- Componentes: `GroupR`(Y +25) → `CtrlR` (`/Game/ControllerR`), `SensR` (`/Game/BreathR`, **el cilindro que importó Beltrán**), `HandGhostR` (`SKM_MannyXR_right`, oculto en juego); `GroupL`(Y −25) igual con L.
- **Offsets respecto de la mano = los de `BP_ControllerRig`, validados en visor** (2026-09-03): der Controller `(2.791, 9.5, −4.296)` / Breath `(2.791, 9.5, −3.5)`, rot `(P−90, Y−10)`; izq `x`, pitch y yaw invertidos. Se autoran moviendo el componente contra la mano fantasma en el viewport: `AttachComponentToComponent` con `KeepRelative` conserva esa transform relativa.
- `MountRig` (reintenta cada tick hasta encontrar pawn + manos): attach de los 4 meshes a `HandRight/HandLeft`, `PaintRig`, `bMounted`. Log `BREATHRIG: mandos y sensores montados…`.
- `RigVisualStep(Dt)` en el Tick **antes** de `TickBreathGated`, corre siempre: `RevealT` → `FInterpToConstant` hacia `(bMounted ∧ bEnabled)` a `1/RevealTime` → `ApplyReveal` (quíntico → escala de los meshes, visibilidad) → esconde las manos del pawn mientras `RevealT > 0` y **las devuelve al terminar el retiro** (`HandsHide`, `SetHiddenInGame` sin propagar: los meshes cuelgan de la mano).
- `PreviewRig` en el Construction Script: color y visibilidad en el viewport sin Play.

## API
| Verbo | Qué hace |
|---|---|
| `SetRigActive(bOn)` | usa el `bEnabled` del motor. Apagar: `BreathSleep` (corta háptica) + `PushMPC(0,0,…)` → nada queda "respirando" |
| `Retire()` | `SetRigActive(false)`; los meshes se achican y las manos vuelven |
Publica lo mismo que el manager: `bBreathing`, `BreathLevel`, `BreathDrive`, `BreathSigned`, `BreathOn` y `MPC_Breath` (`Signed`, `On`, `FlowIn`, `FlowOut`).

## ✋ Mano elegida — solo existe el control en ESA mano (2026-09-27, Beltrán)
*"La experiencia decidirá en una etapa previa si el usuario es diestro o zurdo… en la izquierda no debe haber mesh de motion controller ni tampoco mecánica."*
- `bAutoHand` = **false** (CDO e instancia): `PickHand` ya no salta a la otra mano, el umbral y la háptica son solo de `bRightHand` (derecha por defecto).
- `ApplyReveal` escala y muestra **solo** `CtrlR/SensR` o `CtrlL/SensL` según `bRightHand`; la otra mano queda en escala 0 e invisible. Las manos del pawn se esconden las dos (igual que en el secuenciador).
- `PreviewRig` muestra en el viewport solo la mano elegida (mando, sensor y mano fantasma).
- **API nueva `SetHandedness(bRightSide)`**: la etapa previa se la pasa. Corta la háptica (`BreathSleep`) y fija `bRightHand` + la mano activa. 
- Verificado en PIE: `CtrlR/SensR` escala 1 visibles, `CtrlL/SensL` escala 0 invisibles, `bRight` true, cero `Accessed None`.

## 📈 Rango normalizado — cualquier panza llega a los extremos (2026-09-27)
Beltrán: *"una persona con estómago más pequeño nunca alcanza los máximos o mínimos del metaball… mientras exhalemos, siempre se llegue al máximo, lo mismo al inhalar. Suave."* La ganancia automática (`AmpEMA`) escala por la amplitud PROMEDIO y la saturación suave deja una respiración normal en ~0,8: la chica no llega.
- **`NormRange(S, DT)`** (entre `StepFlows` y `PushMPC` en `Publish`): pico/valle `RPeak`/`RValley` que siguen a `S` al instante y se relajan hacia `S` con `RangeTau`; `n = clamp((S − medio)/(max(rango, RangeFloor)/2))` → el tope de cada inhalación da +1 y el fondo de cada exhalación −1; llegada suave `n·(2−|n|)` (pendiente 0 en ±1); en reposo 0. **Al MPC `Signed` va el normalizado**; publica `BreathNorm` (`BreathSigned` sigue crudo).
- Perillas `D - Salida`: `RangeNorm` 1 (0 = como antes) · `RangeTau` 6 s (más alto = exige respiraciones parecidas a las anteriores) · `RangeFloor` 0,25 (no amplifica ruido).
- Medido en PIE con respiración sintética de 0,2 cm: cruda ±0,57 → normalizada **−1 ↔ +1** en cada ciclo.

## 🐢 Seguidor suave — 3-4 s para llegar al extremo (2026-09-27, tras la primera sesión en visor)
Beltrán: *"el cambio entre inhalar, sostener y exhalar hacia los máximos funciona, pero se va demasiado rápido; debería tomar unos 3-4 segundos llegar al máximo"*. Medido en PIE con respiración sintética de 14 s: **`NormRange` salta de 0,36 a 1 en ~1,2 s y después queda plano en el tope** (la normalización estira la señal: cualquier movimiento temprano de la panza ya es "el máximo").
- **`FollowBreath(S, DT) → Out`** entre `NormRange` y `PushMPC` en `Publish`: dos `FInterpTo` en cascada (`BreathF1` → `BreathF2`, `Z - Estado`) con velocidad `4,74 / BreathFollowTime` = sistema de 2º orden críticamente amortiguado: **arranca suave, llega suave, sin rebote**, y alcanza el 95% del salto en `BreathFollowTime` segundos. Al MPC va `BreathF2`.
- Perilla **`BreathFollowTime` = 3,0 s** (`D - Salida`; **0 = sin seguidor**, `FInterpTo` con velocidad 0 devuelve el destino). Con 3,5 el total medido fue ~4,3 s (hay que sumarle el segundo que tarda la propia entrada); con 3,0 queda en ~3,5-4 s, dentro de los 4 s de la inhalación del pacer.
- Como el MPC lleva la señal seguida, el `Motion` del metaball (que sale de `|dS/dt|`) también quedó más suave.

### 🔁 2ª versión (misma tarde, tras la 2ª sesión en visor): FRENADA FÍSICA en vez de filtro
Beltrán: *"el tiempo en llegar a cada máximo me parece súper, pero el INICIO del cambio se demora mucho: si empiezo a inhalar rápido, toma una curva muy lenta; debiera sentirse más instantáneo"*. Es la firma del 2º orden: **pendiente cero al arrancar**. Mismo criterio que [[movimiento-frenada-fisica-no-exponencial]]:
- `FollowBreath` ahora es **velocidad ∝ √distancia**: `v* = sign(d)·k·√|d|`, con `k = 2√2 / BreathFollowTime` (recorre el salto completo −1→+1 desde quieto en exactamente `BreathFollowTime` s); `BreathFollowVel = FInterpTo(v, v*, 1/BreathFollowAttack)`; `BreathFollow += v·DT`, **sin pasarse** (si cruzaría la meta, queda en la meta). Arranca a velocidad plena y frena con desaceleración constante: llega exacto, sin cola exponencial.
- Perillas `D - Salida`: `BreathFollowTime` **3,0** (0 = sin seguidor) · **`BreathFollowAttack` 0,12 s** (cuánto tarda en tomar velocidad; 0 = instantáneo, subirlo suaviza el arranque).
- Estado `Z - Estado`: `BreathFollow` (lo que va al MPC) y `BreathFollowVel`. `BreathF1/F2` (los del filtro) **se borraron** (el cuerpo de la función se vació conservando entrada y retorno, así la llamada de `Publish` no se tocó).
- **Medido en PIE** (respiración sintética de 14 s, muestras cada 0,37 s): el seguidor se mueve **junto con** la señal desde el primer instante (−0,99 → −0,97 → −0,93 mientras la entrada va −0,99 → −0,96 → −0,89; antes quedaba clavado ~1,5 s) y llega a +0,99 ~4 s después del inicio del cambio.

## 🧭 El sensor tiene que APUNTAR al estómago (2026-09-27, noche)
Beltrán en visor: *"aunque ponga el sensor al revés entra igual al umbral… si giro la mano y la apunto hacia el frente, igual toma el umbral. La parte plana del cilindro tiene que estar apoyada en el estómago."* **Ninguna versión anterior chequeaba orientación** (V2 → CalibProbe → Sensor_Soul → Manager → Rig: zona solo por POSICIÓN del grip + quietud). El levantamiento de calibración (14 usuarios, `docs/ANALISIS-CALIBRACION-2026-08-24.md`) tampoco registró orientación: define la zona (muslo rechazado 100% por `horiz` ≥ 26 cm) y la quietud, no la cara del sensor.
- **La cara plana del sensor mira hacia donde mira la PALMA.** Dos derivaciones independientes (bounds de `BreathR`/`BreathL` + offsets `P−90/Y−10` + rotación de `HandRight/HandLeft` del pawn; y la semántica del grip de OpenXR) dan lo mismo: cara = **`−RightVector(GripR)`** en la derecha y **`+RightVector(GripL)`** en la izquierda (el disco izquierdo está espejado).
- **`FacingOK()`** (nueva, llamada en `SenseHand` antes de `SetbZone`): `FacingDot = dot(RightVector(grip), Normalize2D(CameraForward)) · (bRight ? +1 : −1)` = dot(cara del sensor, dirección horizontal opuesta a donde mira el usuario). Devuelve `FacingDot ≥ FacingMin − (bBreathing ? FacingHyst : 0)` **OR `bIgnoreTracking`** (para la prueba de PIE). **`bZone = zona geométrica AND FacingOK`** → debounce, háptica, `BreathSleep` y `PickHand` heredan sin cambios.
- 🔴 **Objetivo = −CameraForward (horizontal), NO la dirección mano→cabeza**: en la panza la distancia horizontal cabeza-mano baja a 3 cm (calibración), y si el usuario se inclina y la cabeza pasa por delante de la mano esa dirección se INVIERTE (falso negativo con el sensor bien puesto). Falla solo con la cabeza girada > 70° respecto del cuerpo.
- Perillas `A - Umbral`: **`FacingMin` 0,34** (entra hasta ~70°) · **`FacingHyst` 0,25** (una vez adentro sale recién a ~85°: sin parpadeo en el borde; al revés, −1, nunca sobrevive). `FacingDot` en `Z - Estado`.
- **Verificado en PIE** moviendo y girando los grips del pawn (texto `"(Pitch=..,Yaw=..,Roll=..)"` en `RelativeRotation`; el JSON solo escribe la primera componente): derecha palma al cuerpo **+1 → bZone true** · al revés **−1 → false** · hacia el frente **0 → false** · inclinado (cabeza 5 cm delante de la mano) **+1 → true**; izquierda (con `bRightHand` false) palma al cuerpo **+1 → true** · al revés **−1 → false**. 0 errores.
- ✅ **VALIDADO EN VISOR (2026-09-27, APK 20:54, Beltrán: "Probado. Funciona")**: sensor apoyado en el estómago entra; al revés o con la mano hacia el frente no. El signo deducido era el correcto. ⚠ Si el montaje del sensor, su offset o la rotación de las manos del pawn cambian, la fórmula cambia. La mano izquierda solo se probó en PIE.

## Perillas `0 - Rig` (instance-editable)
`bStartActive` false (lo activa la etapa; true = standalone) · `bShowControllers` / `bShowSensors` / `bHideHands` true · `CtrlColor` (0.35, 0.8, 1) · `SensorColor` (0.886, 0.604, 0.447) · `CtrlBrightness` 1.5 · `RevealTime` 0.6 · `CtrlMat` `M_BreathCtrl_SC`. El resto (umbral, señal, háptica, prueba) = las categorías del manager, con sus valores.

## Verificado (2026-09-27)
- PIE: `CtrlR/SensR` hijos de `BP_VRPawn_SC.HandRight`, `CtrlL/SensL` de `HandLeft`, con los offsets exactos; `HandR/HandL` = los Grips; `BREATH: listo` una vez; con `bFakeBreath` publica `BreathSigned`/`BreathOn`; al retirarse `RevealT` 0, escala 0, manos devueltas.
- Simulate (sin pawn): cero `Accessed None` **tras el arreglo de abajo**.
- `get_dependencies`: meshes de mando/sensor, `SKM_MannyXR_*`, `GrabHapticEffect`, `MPC_Breath`, `M_BreathCtrl_SC`. Nada del pawn, del director ni de otras mecánicas.

## 🐛 Arreglo heredado del manager
`FindHandMC` hacía `GetAttachParent(FindHand(...))` sin validar: con un pawn **sin** `HandRight/HandLeft` (Simulate, otro proyecto) spameaba `Accessed None … CallFunc_FindHand_Hand` cada tick. Ahora hay un `IsValid` entre `FindHand` y el cast. ⚠ **`BP_BreathManager_SC` sigue con el bug** (no se tocó: es de la galería).

## TODO
- [ ] 🔴 Visor: sensor en la panza (derecha e izquierda), zumbido y pulso del umbral, reacción del metaball, retiro al final.
- [ ] Ajustar en visor el calce del sensor contra el mando si hace falta (gizmo sobre `SensR`/`SensL` contra la mano fantasma).
