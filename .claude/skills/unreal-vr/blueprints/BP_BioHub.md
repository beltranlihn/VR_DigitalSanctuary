# BP_BioHub — la única fuente de verdad de la señal (Core/Signals/)

## Purpose
§9.3: **ingesta OSC → binning → suavizado**. Expone valor actual, promedio y flag de conexión. Vive en el **nivel persistente** y sobrevive a las transiciones.

🔴 **La regla que define todo el diseño (§9.3):** *el BioHub no sabe nada de etapas y las etapas no saben nada de OSC. Si se cambia de dispositivo, se toca un solo Blueprint.* En la práctica: las direcciones OSC son **variables de texto** (no strings hardcodeados en un switch), y la etapa entra como un **int opaco** — el BioHub nunca pregunta qué significa.

## Status
🟡 **Ingesta + suavizado + flag de conexión construidos y verificados en PIE** (2026-08-11). ⬜ **Falta el binning de las 180 casillas (§9.5).** Falta probar con una fuente OSC real.

## 🔴 Por qué NO usa SwitchOnString — es un bloqueador de API, no una preferencia
`BP_OSCReceiver` (el que ya andaba) despacha las direcciones con un `SwitchOnString`, y su tracker avisa: **los case strings se setean en el Details panel del editor, NO por API**; reescribir el switch por DSL lo duplica y le pierde el case. O sea que **por MCP no se puede agregar una dirección nueva a ese BP.**

→ Acá el despacho va con **`Utilities|String|EqualExactly(String)`** dentro de un `if/elif`. Es totalmente escribible por DSL, y encima deja las direcciones como **variables** (`AddrCalm`, `AddrHeart`), que es justo lo que §9.3 pide para poder cambiar de dispositivo tocando datos.
⚠ El operador `==` del DSL **no sirve para strings**: resuelve a igualdad numérica y falla con *"Could not connect pin Addr to A"*. Hay que nombrar el nodo de string explícitamente.

## Registro de variables

### Config — cambiar de dispositivo se hace acá
| Variable | Default | Rol |
|---|---|---|
| `ListenIP` | `0.0.0.0` | Cualquier interfaz. |
| `Port` | 8000 | ⚠ OSC es **UDP** 8000; el MCP usa **TCP** 8000. **No hay conflicto**, son protocolos distintos. |
| `AddrCalm` | `/calm` | Dirección OSC de la calma. |
| `AddrHeart` | `/hr` | Dirección OSC del ritmo. |
| `SmoothTau` | 1.5 s | Constante de tiempo del EMA. |
| `ConnTimeout` | 3.0 s | Sin mensajes por más de esto → `bConnected = false`. |

### Salida — lo que leen los consumidores
| Variable | Rol |
|---|---|
| `Calm` / `Heart` | Último valor crudo recibido. |
| `CalmSmooth` / `HeartSmooth` | Valor suavizado por EMA. **Es lo que debería leer la ameba**: el crudo tiembla. |
| `bConnected` | 🔴 **Solo true si llegó al menos un mensaje Y el último fue hace menos de `ConnTimeout`.** Que el servidor esté arriba **no** cuenta como conectado — la distinción importa cuando el EEG no está puesto. |

### Interno
`OSCServer` (guarda el server para que no lo junte el GC) · `SinceLastMsg` · `bHadFirstSample`.

## Estructura de grafos
- **`BeginPlay`** — `CreateOSCServer` con los valores de config → guarda el server → `AssignOnOscMessageReceived`.
- **`OnOscMessageReceived_Event_0`** (el generado por el Assign) → `HandleOsc(Message)`.
- **`HandleOsc(Message)`** — `GetOSCMessageAddress` → `ConvertOSCAddressToString` → `GetOSCMessageFloatAtIndex(0)`, y **solo si el pin de éxito es true** llama `Ingest`. Un mensaje sin float no ensucia el dato.
- **`Ingest(Addr, Value)`** — resetea el watchdog, marca `bHadFirstSample`, y despacha por comparación de string.
- **`UpdateSignals(Δt)`** (desde el Tick) — EMA de las dos señales + acumula `SinceLastMsg` + recalcula `bConnected`.

**EMA:** `v += (target − v) · clamp01(Δt / SmoothTau)`. El `clamp01` es lo que lo hace estable con hitches: sin él, un frame largo daría un factor > 1 y el filtro sobrepasaría.

## 🔴 Gotcha nuevo: el nodo `Assign` regenera un evento vacío en CADA compile
Medido acá el 2026-08-11. Pasarle un evento con nombre explícito desde el DSL —`(Audio|OSC|AssignOnOscMessageReceived _srv (AddEvent|Custom|OnOscMessageReceived_Event))`— crea **un custom event suelto**, y el `K2Node_AssignDelegate` **igual genera el suyo** al reconstruirse. Resultado: en cada compile aparece un evento vacío más, tomando el primer nombre libre.

- ✅ **No es runaway**: siempre queda **uno** suelto, porque reusa el nombre que se liberó.
- ✅ **El cableado real está bien**: se verificó con `get_node_infos` que el `OutputDelegate` del evento con el handler va al `K2Node_AssignDelegate_0`.
- ⚠ **`clean_orphans.py` NO lo va a borrar**: los custom events son tipo ENTRY y el script nunca los toca (y hace bien).
- 👉 **Lo correcto es lo que dice `nodes.md`**: crear el nodo `Assign` **sin** pasarle un evento y escribir el cuerpo en el que él genera. Acá quedó al revés por haberlo nombrado; funciona, pero deja ese vacío. **Si se reconstruye este BP, hacerlo del modo correcto.**

⚠ `LogOSC: Warning: Outer object not set. OSCServer may be garbage collected if not referenced.` es esperable y está cubierto: el server se guarda en la variable `OSCServer`, que es la mitigación que documenta `nodes.md`. Se puede silenciar pasándole el pin `Outer`.

## Verificado en PIE (2026-08-11)
- `LogOSC: Display: OSCServer 'BioHub' started` → el server levanta en el puerto configurado.
- Sin fuente OSC: `bConnected = false`, `bHadFirstSample = false`, `SinceLastMsg` acumulando. **El watchdog funciona.**

## ✅ Las 180 casillas de §9.5 (construido 2026-08-11)
9 arrays de 180: `BinCalm{Sum,Count,Min,Max}`, `BinHeart{Sum,Count,Min,Max}` y `BinStage`. `InitBins` los redimensiona en `BeginPlay`; `AdvanceBin` (desde el Tick) corre el índice cada `BinSeconds` y lo **clampea** al último para que la obra pueda pasarse de largo sin desbordar.

🔴 **La acumulación va en `Ingest`, o sea POR MUESTRA RECIBIDA, no por frame.** Es la decisión que hace que el dato signifique algo: si acumulara por tick, `Count` contaría *frames* y una casilla sin señal quedaría con muchas muestras de un valor viejo. Acumulando por mensaje, **`Count == 0` es un hueco de verdad** — y de eso depende que el panel dibuje huecos *tenues* y no *rotos* (§5), que es la diferencia entre "un pasaje" y "una falla".

💡 **Min/max sin necesidad de pre-llenar con infinito:** la rama `Count <= 0` (primera muestra de la casilla) fija min **y** max al valor; de ahí en adelante compara. Así los arrays se inicializan en 0 sin que eso contamine el mínimo.

**`SetCurrentStage(StageId)`** es la única superficie por donde entra el concepto de etapa, y entra como **int opaco**: el BioHub lo guarda en `BinStage` sin preguntar qué significa. Es lo que cumple la regla de §9.3.

⚠ **Los getters de promedio por casilla todavía no existen.** El consumidor (el panel) va a necesitar algo tipo `GetBinAverage(i)` = `Sum / Count` con `Count == 0` → devolver el flag de hueco, no 0.

**Verificado en PIE:** `InitBins` loguea, y tras ~30 s `CurrentBin = 6` con `BinElapsed = 0.33` — el reloj de casillas corre exacto a 5 s. `CurrentStage = -1` mientras nadie lo setea.
🔴 **Lo que NO está verificado: la acumulación.** Sin fuente OSC no entró ni una muestra, así que `AccumCalm`/`AccumHeart` **compilan pero nunca corrieron**. Es justo el tipo de cosa que parece andar.

## TODO
- [ ] Probar con una fuente OSC real (Muse). Hasta entonces, la ingesta está **construida pero no ejercitada**.
- [ ] Un `BP_BioHub_Fake` para poder trabajar sin EEG. Ya existen `BP_SignalProvider` / `BP_SignalProvider_Fake` en `Core/Signals/` (⚪ sin auditar): **revisarlos antes de construir**, puede que el mock ya esté hecho.
- [ ] Decidir qué pasa con **`BP_OSCReceiver`**: el BioHub lo reemplaza para la obra, pero sigue en uso en los niveles de test de Heart. Dos servidores en el mismo puerto UDP **no pueden coexistir** → no poner los dos en el mismo nivel.
- [ ] `Respiración` no entra por acá: viene del mando y solo durante *Entering* (§5). No mezclarla en el BioHub.

## Relacionados
- `BP_OSCReceiver` (el patrón del delegate, y el bloqueador del switch) · `BP_ProtoSoul` y `BP_Sensor` (sin construir) · [[BP_StageDirector]] (le va a pasar la etapa como int)
