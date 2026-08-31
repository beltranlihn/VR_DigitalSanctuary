# BP_VRPawn_SC — el pawn VR de la obra

`/Game/SoulCharger/Core/Pawn/BP_VRPawn_SC` · 🔴 **Asset COMPARTIDO** (`Core/`): coordinar antes de tocarlo.
Anatomía general y recetas VR: [`references/vr-pawn.md`](../references/vr-pawn.md).

## Lo que hace su `Event BeginPlay` (cadena verificada, 2026-08-28)
```
BeginPlay -> Branch -> Sequence -> SetTrackingOrigin(Stage) -> ExecuteConsoleCommand
          -> AddMappingContext -> AddMappingContext -> ArmRecenter   (nuevo)
```
⚠ **No hay `Event Possessed`** — el input se arma en BeginPlay, contra la recomendación de `vr-pawn.md`.
Funciona hoy; anotado por si aparece un bug de input que no se explique.

---

## 2026-08-28 — recentrado automático al arrancar

**Reporte de Beltrán:** *"cuando se reseteó la experiencia, aparecí en cualquier lugar. Debe caer
exactamente en el player start. Quizás fue percepción mía, pero recíbelo."*

**No era percepción.** El pawn hace `SetTrackingOrigin(**Stage**)` — el origen es el centro del Guardian —
y **nunca llamaba a `ResetOrientationAndPosition`**. El nodo existía en el proyecto, pero **colgado de un
botón del menú** (`WBP_Menu.ResetOrientationButton`): o sea que Beltrán ya había necesitado recentrar a
mano alguna vez. Con origen Stage, la cámara queda donde esté el cuerpo del usuario dentro de su espacio
de juego; al recargar el nivel el pawn vuelve al PlayerStart pero **el usuario sigue físicamente donde
estaba**, y después de 15 minutos sentado eso puede ser medio metro.

### El arreglo
| Función | Qué hace |
|---|---|
| **`ArmRecenter()`** | Enganchada al final del `BeginPlay`. Arma un timer de `RecenterDelay`. |
| **`RecenterSeated()`** | `ResetOrientationAndPosition(Yaw 0, OrientationAndPosition)` si `RecenterOnStart`. |

**El retardo no es un lujo**: en el frame del `BeginPlay` la pose del HMD todavía puede no ser válida —
es la receta "Stage + Recenter con Delay" de `vr-pawn.md`.

| Perilla | Valor | Nota |
|---|---|---|
| `RecenterOnStart` | `true` | Sin prefijo `b` **a propósito**: los bools con `b` no se pueden escribir por DSL (§62). |
| `RecenterDelay` | 0,5 s | |

💡 El pawn **se spawnea** (0 colocados en el nivel), así que los valores del CDO mandan — por una vez no
hubo que escribir nada en la instancia.

⬜ **Sin verificar**: esto sólo se juzga con las gafas puestas. Si al recentrar la obra queda girada
respecto de la sala, la perilla a mirar es el `Yaw` del nodo (hoy 0) o pasar el `Options` a sólo `Position`.
