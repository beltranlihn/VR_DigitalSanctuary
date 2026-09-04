# BP_BreathOrb_SC — la esfera que se controla con la respiración (Core/Sensor/)

> `/Game/SoulCharger/Core/Sensor/BP_BreathOrb_SC` · creado 2026-08-24 · **una instancia** en `MapsV2/RoomsV2/L_Entering_SC` (`BreathOrb_Entering`, en **1380/−40/125**, carpeta `3 Escena`) — viaja con el streaming de la sala.
> **Estado: 🟡 ciclo completo verificado en PIE por log y por medición directa (`ORB: true` → 10 s → `ORB: false`, `RevealT` 0→1 medido en la instancia PIE); el control por respiración real necesita visor.**

## Qué es
El **consumidor visual** de la mecánica de respiración de Entering: la esfera que el usuario controla con su respiración durante la etapa (el `Box_Breath` de la versión limpia). **Tonta a propósito** — sólo LEE el estado público de [[BP_Sensor_Soul]]. Esfera del motor con `MI_Sensor`, NoCollision, sin sombra.

## Cuándo aparece (decisión de Beltrán 2026-08-24)
- **Durante las instrucciones NO** — ahí el usuario practica con el **círculo del widget** (fase `bPractice` del sensor).
- **Aparece cuando terminan las instrucciones** (el `SetStage(1)` de `StartStepTime` apaga la práctica) y **se va cuando la etapa cierra por tiempo** (`SetStage(-1)`).
- Condición viva: `active = Sensor.Mode == 1 && !Sensor.bMechDone && !Sensor.bPractice` → `RevealT` sube/baja con `FInterptoConstant` (`RevealTime` 0.8 s).

## Cómo respira (v2, 2026-08-24 noche)
`CurScale` interpola hacia **`lerp(BaseScale, InhaleScale, nivel)`** donde nivel = **`Sensor.BreathLevel`** (la señal continua 0-1, con auto-signo) si `bBreathing`, o 0.5 (neutro 0.35) si no. Ya **no** usa el `bInhaling` binario — se acabó el "baja solo al sostener". Escala final = `CurScale × RevealT`. Log de flanco `ORB: true/false`.

🆕 **2026-09-01 — el sostenido**: Beltran validó el control en visor (*"funciona super"*) pero la esfera **se achicaba sola al sostener el aire arriba**. No se toco nada de este BP: la causa y el arreglo viven en la senal ([[BP_Sensor_Soul]] §`HoldSlow`/`HoldMovK`) — la linea de base del band-pass ahora se frena **cuando el sensor deja de moverse**, asi el nivel (y con el la escala) aguanta el sostenido sin perder la sensibilidad mientras se respira.

🆕 **2026-09-01 (2ª) — el reenganche**: al volver a entrar al umbral la esfera saltaba a otro tamaño. Tampoco se tocó este BP: el `select(bBreathing, BreathLevel, 0.5)` de `TickOrb` está bien — el problema era que `BreathLevel` seguía evolucionando a ciegas mientras el umbral estaba cerrado. Ahora el sensor **resiembra la señal y pone el nivel en 0.5 en el flanco IN**, que es el mismo valor que este BP ya usaba como neutro → salto cero por construcción. ⚠ Si alguna vez se cambia ese `0.5` literal del `select`, hay que cambiar el del sensor también: **los dos numeros tienen que ser el mismo**.

## Registro de variables
| Cat | Variable | Default | Rol |
|---|---|---|---|
| A - Orbe (instance-editable) | `BaseScale` **0.15** · `InhaleScale` **1.30** · `BreathFollow` **4.0** · `RevealTime` 0.8 | | rango **15↔130 cm** (ampliado dos veces el 2026-08-24; la última tras validar la señal nueva). ⚠ escritos en CDO **y en la instancia** del sublevel (§212) |
| Z - Estado | `SensorRef` · `bSensorOk` · `RevealT` · `CurScale` · `bWasActive` | | |

## Grafos
`BeginPlay → InitOrb` (CurScale=BaseScale, Body a 0) · `Tick → EnsureSensor` (lazy `GetActorOfClass`+cast, guarda `bSensorOk`) `→ TickOrb(DT)` (todo dentro de `IsValid(SensorRef)`).
🔴 El flanco del log usa el patrón de **§213**: `(if (xor _active (GetWasActive)) (SetWasActive _active) (print))` — el `SetWasActive` va DENTRO del flanco. La primera versión bindeaba el getter antes del Set y el flanco no disparaba nunca (un bind de puro no es snapshot).

## TODO
- [ ] 🔴 Visor: crecer al inhalar / encoger al exhalar con el sensor en la panza; ajustar escalas, `BreathFollow` y la **posición** (dato de autor — moverla en el sublevel).
- [ ] Arte (hoy esferita `MI_Sensor`); candidata a acompañar con emisivo.

## Relacionados
[[BP_Sensor_Soul]] · [[BP_Director_Story]] (arma la práctica y el paso) · [[BP_InstructionsPanel_SC]] (el círculo de práctica del widget)
