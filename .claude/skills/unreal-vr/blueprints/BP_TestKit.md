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

## 🔴 El PULSO: la línea de estado cada 12 segundos
`BeginPlay` arranca un timer (`PulsePeriod` = 12 s) sobre **`PulseTick`**, que llama a siete reporteros. Cada uno busca **el actor que realmente tiene el progreso** de su etapa (`GetActorOfClass` + cast + `IsValid`) y **no escribe nada si ese actor no existe** — así no hay switch por etapa y no hay ruido: sólo habla la mecánica que está viva.

| Función | De dónde saca los números | Línea |
|---|---|---|
| `PulseHead` | `BP_StageDirector` | `PULSE\|t=36.4 \| etapa=0` |
| `PulseHall` | `BP_SoulChoice` | candidatas · hover · inputListo · armado |
| `PulseEntering` | `BP_BreathPacer` | ciclo n/N · corriendo · listo |
| **`PulseHeart`** | `BP_HeartSensor` | **latidos n/15 · enMano · umbral · cuenta** |
| `PulseLoving` | `BP_Stage_Loving` | pregunta n/N |
| `PulseAttracting` | `BP_AttractDirector` | step n/8 · burbujas · arrancado |
| `PulseSurrounding` | `BP_DrawCanvas` | metros · dibujando · puntos |

Verificado en PIE (2026-08-15), y la primera corrida ya sirvió para dos cosas a la vez:
```
PULSE|t=12.416943 | etapa=0
PULSE|Heart| latidos=0/15 | enMano=true | umbral=false | cuenta=true
```
👉 **Esa segunda línea es exactamente la que faltaba** el día que Beltrán quedó atascado en Recognizing: dice de un vistazo que el conteo está habilitado (`cuenta=true` — antes del arreglo era `false`) y que lo que falta es el umbral de quietud. Un diagnóstico que costó una hora ahora es una línea de log.

🔑 **El dato que hizo posible leer los bools:** desde OTRA clase, las variables con prefijo `b` **sí se leen**, y el getter va **sin la `b`** — `GetBreathing`, `GetAttached`, `GetCountingEnabled`, `GetChosen`, `GetDrawing`, `GetDone`. Es la contraparte del §67 (los setters) y levanta la limitación del §74, que sólo aplica **dentro** de la propia clase.

## 📸 Cómo llegan las imágenes — y qué NO funciona
- ✅ **`HighResShot` → archivo → `Read`**: el camino que funciona. Barato en tokens (una imagen).
- ❌ **`CaptureEditorImage`**: probado con PIE corriendo → *"Failed to capture any editor windows"*. No sirve como vista en vivo.
- ⚠ **`CaptureViewport`**: funciona, pero devuelve el PNG **en base64 dentro de la respuesta** (651.000 caracteres en la prueba) → inviable por tokens. Sólo para un caso puntual, nunca de rutina.

👉 Conclusión operativa: **las capturas salen de los MARK de Beltrán**, no de que yo mire cuando quiera.

## TODO
- [ ] 🔴 Visor: confirmar que el botón ≡ entrega el input (si no, quedan `IA_Menu_Toggle_Right`, `IA_Move` e `IA_Turn` libres).
- [ ] Volcado de estado en la marca: hoy la marca dice etapa y tiempo; el detalle lo da el pulso de los 12 s. Si hiciera falta, `DoMark` puede llamar a `PulseTick`.
- [ ] Los reporteros de Hall / Entering / Loving / Attracting / Surrounding **compilan pero no se han visto imprimir** (sus actores no existen sin manos en PIE). Confirmar en la primera corrida de visor.

## Relacionados
- [[BP_StageDirector]] (de dónde sale la etapa) · [[BP_SelfTest]] (la otra pata: aserciones sin humano) · `references/assets-existentes.md` §input
