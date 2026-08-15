# BP_TestKit — el botón MARK de las sesiones de test (Core/Debug/)

## Purpose
Cerrar el circuito entre **lo que Beltrán ve en el visor** y **lo que yo puedo consultar**. Cuando algo se ve mal, un botón deja tres cosas al mismo tiempo: una línea en el log con número y etapa, una **captura de pantalla del momento exacto**, y el ancla temporal que me permite encontrar esa ventana del log después.

Nace del método de test acordado el 2026-08-15: el cuello de botella no es la cantidad de bugs, es **la evidencia que viaja con cada uno**.

## Status
🟢 **Instrumento validado antes de usarlo** (2026-08-15). Corrida de control con `DoMark` colgado temporalmente de `BeginPlay`:
```
[BP_TestKit_C_0] TESTKIT: listo | boton MENU izquierdo = MARK
[BP_TestKit_C_0] MARK #1 | etapa=0 | t=3.083334
→ VR_Test/Saved/Screenshots/WindowsEditor/HighresScreenshot00000.png  (la apertura: negro con estrellas)
```
El control positivo se quitó después; hoy `BeginPlay` sólo anuncia que está listo.
⬜ Falta el visor: **que el botón ≡ del mando izquierdo entregue el input** (en Quest el botón equivalente del mando derecho lo reserva el sistema, por eso va el izquierdo).

## 🔴 El botón: por qué éste y no un gesto
La primera idea fue un gesto (dos gatillos, o juntar los mandos). **Descartada por Beltrán, y tenía razón**: en Attracting las dos manos son juego legítimo, y sobre todo — el pawn **ya tiene 16 acciones de Enhanced Input cableadas**, cuatro de ellas con el cuerpo **vacío** porque él las desconectó del menú del VR Template:

| Acción libre en `BP_VRPawn_SC` | Botón |
|---|---|
| **`IA_Menu_Toggle_Left`** ← la que usamos | ≡ del mando izquierdo |
| `IA_Menu_Toggle_Right` | reservado por el sistema en Quest |
| `IA_Move` · `IA_Turn` | sticks (obra sentada, sin locomoción) |

👉 **No hace falta crear ni editar ningún IMC** — que es la regla del proyecto y la fuente de las horas perdidas en Touch. Quedan **tres acciones más libres** para lo que haga falta después.

## Anatomía
```
BP_TestKit (actor en L_Persistent, carpeta 02 Hubs)
  DoMark()    MarkCount++ · CacheDir · MarkShot · log "MARK #n | etapa=i | t=s"
  CacheDir()  cachea el BP_StageDirector la primera vez (IsValid → rama Is Not Valid)
  MarkShot()  si ShotOn > 0 → ExecuteConsoleCommand(ShotCmd)
```
El pawn aporta **tres nodos y nada de lógica** (regla del pawn liviano): `IA_Menu_Toggle_Left.Started → GetActorOfClass(BP_TestKit_C) → Cast → DoMark`.

| Variable | Default | Rol |
|---|---|---|
| `ShotOn` | 1 | 0 apaga las capturas sin tocar el grafo. |
| `ShotCmd` | `HighResShot 1920x1080` | Qué comando dispara. Subir la resolución es cambiar este texto. |
| `MarkCount` | 0 | El número que aparece en el log y ordena los archivos. |
| `DirRef` | — | El director, para saber en qué etapa estaba la marca. |

## Cómo se leen los resultados
- **Log**: `GetLogEntries(pattern:"MARK #")` → número, etapa y segundo de cada marca.
- **Capturas**: `VR_Test/Saved/Screenshots/WindowsEditor/HighresScreenshotNNNNN.png`, numeradas en orden. ⚠ **El número del archivo NO es el número de marca** (la numeración sigue entre corridas): correlacionar **por orden de modificación**, no por nombre.

## 💡 Y además: `CaptureEditorImage` funciona durante PIE
Hallazgo del mismo día: `EditorToolset.EditorAppToolset.CaptureEditorImage` devuelve una imagen del editor tal como se ve — **y funciona con PIE corriendo**. O sea que durante una sesión por Link puedo mirar el espejo del visor **cuando quiera**, sin que Beltrán haga nada. Los dos mecanismos se complementan: el MARK congela **su** instante, `CaptureEditorImage` me deja mirar **ahora**.

## TODO
- [ ] 🔴 Visor: confirmar que el botón ≡ entrega el input (si no, quedan `IA_Move`/`IA_Turn` libres).
- [ ] Volcado de estado más rico en la marca: qué actor está en hover, qué compuertas de la etapa están abiertas.
- [ ] Anclas automáticas (captura en cada entrada/salida de etapa) y el reportero de atascos.

## Relacionados
- [[BP_StageDirector]] (de dónde sale la etapa) · [[BP_SelfTest]] (la otra pata: aserciones sin humano) · `references/assets-existentes.md` §input
