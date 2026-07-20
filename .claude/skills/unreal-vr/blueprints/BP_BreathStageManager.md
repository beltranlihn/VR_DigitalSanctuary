# BP_BreathStageManager — progress tracker

- **refPath**: `/Game/SoulCharger/Stages/Breath/BP_BreathStageManager.BP_BreathStageManager`  ·  **parent**: Actor  ·  **en nivel**: sí, `L_Test_Breath` (`BP_BreathStageManager_C_0`, colocado una vez, permanente — como `BP_IntroFade`)
- **Propósito**: orquestador de fin de etapa. Reacciona a que `BP_BreathSensor_V2.bStageComplete` se vuelva true: hace que `Box_Breath` se vaya a escala 0, funde a negro y reinicia el nivel. Nace 2026-07-20 junto con el sistema de conteo de `BP_BreathSensor_V2`.
- **Estado**: 🟢 compila y corre sin errores en smoke-test (PIE Simulate). Pendiente: validar el ciclo completo con el usuario en el visor (requiere completar las 5 respiraciones de verdad).

## Por qué es un BP aparte (no vive en el sensor ni en BP_Instructions)
- El **sensor** (`BP_BreathSensor_V2`) es responsable de sí mismo (detectar, contar, ocultarse) — no de orquestar fade/nivel. Mezclar eso ahí habría arriesgado tocar el `Step` frágil (26 tests de calibración encima) para cambios de flujo que no tienen nada que ver con la señal.
- **`BP_Instructions`** se autodestruye apenas terminan las 5 páginas (`UpdateFade` → `SpawnBox` → `DestroyActor(self)`) — no puede sobrevivir para escuchar un evento que ocurre minutos después, cuando el usuario complete las 5 respiraciones.
- Por eso: un actor nuevo, chico, permanente, que solo mira al sensor y actúa una vez.

## Variables
- `Sensor` (object ref a `BP_BreathSensor_V2`, se adquiere solo en `EventTick` — lazy, porque el sensor no existe hasta que `BP_Instructions` lo spawnea en su página 2).
- `bHandled` (bool) — evita disparar la secuencia de cierre más de una vez.
- `FadeDuration` (float, **instance-editable**, default **2.0**) — duración del fundido a negro.

## Grafo (`EventGraph`, escrito con `write_graph_dsl` en grafo vacío — sin cirugía, BP nuevo)
- **`EventBeginPlay`**: `bHandled = false`.
- **`EventTick(DeltaSeconds)`**: `IsValid(Sensor)` → si NO es válido, `GetActorOfClass(BP_BreathSensor_V2)` + cast + cachea en `Sensor` (patrón de re-intento por frame, igual al que ya usa `BP_Instructions.InitRefs`). Si es válido: si `Sensor.bStageComplete AND NOT bHandled` → llama al evento `OnStageComplete`.
- **`Custom|OnStageComplete`**: `bHandled = true` → spawnea `BP_FadeSphere` en la transform de sí mismo → `StartFade(1.0, FadeDuration, Negro)` (funde A negro; `BP_FadeSphere` ya existía, usado por `BP_IntroFade` para fundir DESDE negro — mismo asset, dirección opuesta) → `Delay(FadeDuration)` → `GetCurrentLevelName` → `OpenLevel(byName)` sobre ese mismo nombre = **reinicio del nivel actual**.

## Decisión de diseño: polling, no Event Dispatcher
El plan original (aprobado por el usuario) proponía un Event Dispatcher en el sensor. Se cambió a **polling de `bStageComplete` en `EventTick`** porque es el patrón que YA usan `Box_Breath` y `BP_Instructions` en todo este proyecto para leer estado de otro actor — cero mecanismo nuevo que probar. Costo real: ninguno (es un chequeo de un bool por frame sobre un actor).

## Gotchas de esta sesión
- **`type_id` con paréntesis (`Game|OpenLevel(byName)`) rompe el parser de `write_graph_dsl`** si se escribe inline como cabeza de una llamada — los paréntesis son delimitadores de S-expression. Solución: ese nodo puntual (y su cadena `GetCurrentLevelName`→`StringToName`→`OpenLevel`) se armó con cirugía de nodos (`create_node`+`connect_pins`) DESPUÉS de escribir el resto del grafo por DSL, no dentro del texto DSL.
- El orden de declaración importa: un `(event Custom|X ...)` tiene que aparecer ANTES en el texto que cualquier `(CallFunction|X)` que lo invoque (gotcha ya conocida, confirmada de nuevo: el primer intento con `EventTick` antes de `Custom|OnStageComplete` falló con "CallFunction|OnStageComplete does not exist").

## Session log
- 2026-07-20: creado desde cero. Ver `BP_BreathSensor_V2.md` para el sistema de conteo que dispara esto, y `Box_Breath.md` (actualizar) para el lado de la escala a 0.
