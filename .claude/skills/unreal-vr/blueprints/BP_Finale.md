# BP_Finale — la carga final, el gesto al corazón y el viaje a la constelación (Core/Flow/)

## Purpose
El tramo que faltaba entero: desde que termina la última etapa hasta que **mi ameba se comparte con la constelación**. Es lo que Beltrán pidió poder recorrer de punta a punta (*"llegar incluso a compartir mi ameba cargada con el resto de la constelación"*).

Antes de esto la obra **terminaba en `FinishObra`** del director: se disolvía la sala, se encendían las partículas del exterior, y ahí se cortaba.

## Status
🟡 **Cadena verificada por log** (2026-08-15): la secuencia corre completa con sus tiempos (anillo+hold 4,0 s · viaje 2,8 s), el input queda listo (`FINAL: input listo - hover + gatillo`) y el grab se arma (`ya se puede tomar la ameba con la mano`). Cero `Accessed None` tras cerrar los guards.
🔴 **El hover y el grab NO se pueden verificar en PIE**: sin visor **no hay motion controllers**, así que `HandL`/`HandR` son nulos y la distancia nunca se evalúa. Es un límite del banco de pruebas, no del código — **necesita el casco de Beltrán**.

## Cómo arranca — dependencia invertida, como la ceremonia
El director **no conoce el final**: `FinishObra` sólo pone su bool **`bFinaleOpen`**, y `BP_Finale` (actor colocado en `L_Persistent`) lo poll-ea cada 0,2 s con `WatchFinale` → `PollFinale` → `TakeFinale`. Copiado tal cual de [[BP_Ceremony]], por la misma razón: **si el final no existe, la obra igual cierra**.

```
FinishObra (director) → bFinaleOpen = true
RunFinale:      CacheFinaleRefs · SChargerFinal + VO 25 · SetCharge(1.0) · DrawRing(4)
   ↓ RingTime + HoldTime
FinaleAfterRing: DissolveHud · LeaveHud · FindHandSpot · TravelToPoint
   ↓ TravelTime + 0,4
FinaleReady:    ArmGrab (cachea manos + AddMappingContext) · arma el cortafuegos
   ↓ el usuario acerca la mano y aprieta el gatillo
TryGrabSoul → GrabSoulNow: attach a la mano + HapticSelect
   ↓ la lleva al pecho
CheckChest → ChestHit → CommitToHeart: SProtoHeart + VO 28 · AppendMe · BuildConstellation · StarTravel
```

## 🔴 El gesto: hover + gatillo, sin tocar un solo IMC
Decisión de Beltrán: *"ya intentamos una vez cambiar los IMC y era supercomplicado… hagámoslo funcionar con el trigger que ya tenemos"*. Y: *"quizás simplemente es hacer attach a la mano, y es más simple de lo que pensamos"*.

Lo que se hizo, **replicando [[BP_SoulChoice]]** (que ya resuelve hover+trigger para elegir la ameba del Hall):
- **`EnsureFinaleInput`** = copia de su `EnsureInput`: `EnableInput(self, PC)` + `AddMappingContext(sub, IMCRef, 1000, "(bIgnoreAllPressedKeysUntilRelease=False,bForceImmediately=True,bNotifyUserSettings=False)")`. 🔴 **Esa configuración es la que funciona; los defaults suprimen el input.**
- **`IMCRef` es un DATO** (instance-editable), apuntando al **`IMC_MenuTrigger` que ya existe**. No se creó ni se editó ningún IMC.
- **El evento es `IA_Continue`** (`Started` → tomar · `Completed` → soltar), que es el gatillo que ya mueve botones y páginas en toda la obra.
- **Hover = proximidad de la mano**, no láser: `HoverHit` compara la distancia al cuadrado contra `PickRadius`. Las manos salen del pawn con `GetMotionControllerRightGrip`/`LeftGrip`, igual que `PickHands` de BP_SoulChoice.
- **El "grab" es un attach**: `AttachActorToComponent(soul, mano, KeepWorld)`. Nada más — es lo que hace el `TryGrab` del template.
- 🔴 **El listener vive ACÁ, no en el pawn.** Principio de Beltrán: el spawn/kill de etapas es el árbitro del input. **Lo que se pone en el pawn no se mata nunca** y quedaría vivo toda la obra.

## Registro de variables (todas instance-editable menos el estado)
| Variable | Default | Rol |
|---|---|---|
| `RingTime` / `HoldTime` | 2,6 / 1,4 s | El último anillo y su pausa. |
| `DissolveTime` | 3,0 s | Cuánto tarda el HUD en disolverse (`DissolveHud` de [[BP_SoulHUD]], nuevo). |
| `TravelTime` | 2,4 s | Viaje de la ameba al `SoulHandSpot` y después a la constelación. |
| `HandSpotTag` | `SoulHandSpot` | TargetPoint donde queda **al alcance del brazo**. Colocado en (6045, 0, 128). |
| `PickRadius` | 26 cm | Radio de hover de la mano. |
| `ChestRadius` / `ChestDrop` | 26 / 38 cm | La zona del pecho = cámara menos 38 cm en Z. ⚠ Es una **aproximación**; el `BP_HeartSensor` tiene una zona más afinada y conviene unificarlas cuando se pruebe en visor. |
| `VoFinalIndex` / `VoHeartIndex` | 24 / 27 | VO 25 y VO 28 del guión (0-based). |
| `FinalSfxName` / `HeartSfxName` | SChargerFinal / SProtoHeart | Por nombre en el catálogo de [[BP_AudioHub]]. |
| `FinaleTimeout` | 120 s | 🔴 Cortafuegos: si nadie la toma, `FinaleForce` cierra igual. Cero callejones sin salida. |

## 🐛 Dos trampas nuevas que costaron varias corridas
1. 🔴🔴 **Recompilar un Blueprint REINSTANCIA su actor colocado y se pierden los overrides de instancia** — y en un caso el actor **desapareció del nivel**. El `refPath` cacheado queda apuntando a un `REINST_BP_Finale_C_58` y `set_properties` falla con *"the following properties could not be set"*. **Después de cada compile hay que volver a buscar el actor**, y para probar conviene poner los flags de debug en el **CDO**, que sí sobrevive.
2. 🔴 **Un guard que falta en una función de Tick inunda el log**: `CheckHoverHand` leía `SoulRef` sin `IsValid` y generó **miles** de `Accessed None` en segundos, tapando todo lo demás. En funciones que corren por frame, **el guard no es opcional**.
3. ⚠ **Agregar un parámetro a una función que ya tiene llamadores rompe el compile** (*"Could not find a pin for the parameter S"*), y como el script de `execute_tool_script` falla, **se revierten los `add_function_graph` del mismo script**. Salida limpia: **no tocar firmas en uso** — meter el guard en una función nueva encadenada.

## TODO
- [ ] 🔴 **Visor**: el hover, el agarre, el traslado al pecho y el radio de la zona. Nada de eso es verificable sin manos.
- [ ] Unificar la zona del pecho con la de `BP_HeartSensor` en vez de la aproximación por cámara.
- [ ] Los promedios reales en `AppendMe` (hoy 0.5 / 70.0 fijos) — salen de los bins de [[BP_BioHub]].
- [ ] La melodía al archivo (serializar `SG_Melody` al string).
- [ ] Lo que sigue al viaje: gráficos de resultados, exploración con beam, créditos y reload.

## Relacionados
- [[BP_SoulArchive]] (el `AppendMe` y la constelación) · [[BP_SoulChoice]] (**el patrón de hover+trigger que se replicó**) · [[BP_Ceremony]] (el patrón de polling) · [[BP_ProtoSoul]] (`LeaveHud`/`TravelToPoint`/`DrawRing`) · [[BP_SoulHUD]] (`SetCharge`/`DissolveHud`) · [[BP_AudioHub]] · [[BP_HapticHub]]
