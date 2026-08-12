# BP_StageBase — el ciclo de etapa (Core/Stages/)

## Purpose
El §9.4 del documento maestro: la clase base de TODAS las etapas. En la fase de esqueleto (paso 3 del §10) es un **placeholder por prints** que recorre el ritual completo — *instrucciones → ejercicio → carga → aviso al director* — y le devuelve al director el control del cierre **por el camino real** (`ForceComplete`), no por timer.

🔴 **Quién cierra la sala cambió con este BP:** antes el director cerraba por timer (`EndStage` a `CurDuration`); ahora **la etapa pide su propio cierre** y el timer del director quedó degradado a **cortafuegos de inactividad** (§2.2 / §9.9): dispara a `CurDuration + TimeoutMargin` (6 s) solo si la etapa nunca avisó. `ForceComplete` limpia ese timer, así que no hay doble cierre.

## Ciclo de vida (spawn/kill, regla §9.1.b)
```
DIRECTOR EnterRoom → SpawnStage:
    spawn BP_StageBase en el origen · StageRef = · BeginStage(CurDuration, StageNames[StageIndex])
BeginStage → cachea el director · print "instrucciones placeholder" · timer RunStage a InstructionsTime
RunStage   → print "ejercicio placeholder" · timer StageDone a StageSeconds
StageDone  → print "carga del anillo placeholder" · timer FinishStage a ChargeTime
FinishStage→ print "completa" · DirectorRef.ForceComplete()   ← 🔴 SIN DestroyActor(self): ForceComplete→EndStage→KillStage nos destruye SINCRÓNICAMENTE; el self-destroy posterior era un "pending kill" por etapa (visto en visor 2026-08-12). La destrucción es SIEMPRE del director.
DIRECTOR EndStage → KillStage (DestroyIfValid StageRef — cubre el caso del cortafuegos, donde la etapa sigue viva)
```
`StageSeconds = max(TotalSeconds − InstructionsTime − ChargeTime, 1)` — el total que manda el director se reparte entre las tres fases.

## Registro de variables
| Variable | Default | Rol |
|---|---|---|
| `InstructionsTime` | 1.5 s | Placeholder del widget de instrucciones. En paso 4, Entering/Recognizing/Attracting/Surrounding lo reemplazan por el widget real; **Loving lo salta** (la ruptura del patrón, §2.4). |
| `ChargeTime` | 2.0 s | Placeholder de la animación de carga del anillo. El crescendo (anillo 1 ≈ 4 s → anillo 5 ≈ 20 s) será dato por etapa. |
| `StageSeconds` | calculado | El "ejercicio". **Es lo que `RunStage` de cada subclase reemplaza en paso 4** — lo único que cada etapa sobreescribe (§9.4). |
| `StageLabel` | — | El nombre para los logs (viene de `StageNames` del director). |
| `DirectorRef` | — | Cacheado en `BeginStage` con `GetActorOfClass` + cast. |

## Paso 4 (cuando toque)
- Crear las subclases (`BP_Stage_Entering`, …) con `RunStage` sobreescrito por la mecánica real; el director elegirá la clase por sala (hoy spawnea siempre la base).
- `ForceComplete(bFastCharge)` del §9.9 llega cuando exista la animación de carga real.
- El widget de instrucciones y la configuración del sensor (`SetMode`) van en `BeginStage`.

## Verificado por log (2026-08-12)
Recorrido completo con el ciclo activo: cada sala imprime la cadena `instrucciones → ejercicio → carga → completa - aviso al director por el camino real`, el director cierra vía `ForceComplete` y la obra termina en la disolución. Cero `Accessed None`, cero dobles cierres.

## Relacionados
- [[BP_StageDirector]] (`SpawnStage`/`KillStage`/`ForceComplete`, `TimeoutMargin`) · `docs/OBRA-SOUL-CHARGER.md` §9.4/§10
