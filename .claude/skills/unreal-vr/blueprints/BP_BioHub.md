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

## 🆕 2026-08-14 — las 3 señales REALES del server de Beltrán + la señal de sensor
Beltrán tiene su server OSC probado y enviará **3 señales** (él define las direcciones finales; hoy son variables):
1. **int 0/1** → sensor conectado (dirección `AddrSensorOn`, default `/sensor`) → **`bSensorOn`**.
2. **float 0–1 a 60 Hz** → estado de calma **EEG** (dirección `AddrCalm`) → `Calm`/`CalmSmooth`. De esta misma señal salen los promedios del gráfico final.
3. **float = número de BPM** (70, 70.5, 60…) — NO pulsos (dirección `AddrHeart`) → `Heart`/`HeartSmooth`.

**Camino de enteros nuevo**: `HandleOsc`, si el mensaje no trae float, cae al else → **`HandleOscInt`** (`GetOSCMessageIntegeratIndex`) → **`IngestInt(Addr,V)`**: si es `AddrSensorOn` resetea watchdog + `bSensorOn = V > 0`. ⚠ Si el server mandara `/sensor` como float, hoy NO se procesa (la rama float no conoce esa dirección) — el contrato es int.

**El fake también emite la señal de conexión**: `FakeTick` cierra con `IngestInt(AddrSensorOn, 1)` — ejercita el camino real. `bFakeSignal` está **true en la instancia** del persistente (la simulación LFO que pidió Beltrán: calma = seno 0.1–0.9 a `FakeHz` 0.08 ≈ ciclo de 12,5 s; BPM = 68±9). **Cuando llegue el server real: `bFakeSignal = false` en la instancia y listo.**

Consumidor nuevo: [[BP_SoulHUD]] (lee `CalmSmooth`, `HeartSmooth`, `bConnected AND bSensorOn`).

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

## 🔴🔴 GOTCHA GRANDE: el nodo `Assign` REPRODUCE eventos vacíos en cada compile hasta que se GUARDA
Diagnosticado y **resuelto** acá el 2026-08-11. Vale para cualquier `Assign<Delegate>`, no solo el de OSC.

**El síntoma:** cada `compile_blueprint` agrega **un custom event vacío más**. Llegué a tener **seis** (`OnOscMessageReceived_Event`, `_1` … `_5`) antes de darme cuenta. La lógica seguía intacta —el que tenía el handler seguía cableado— pero el grafo crecía sin techo.

⚠ **Mi primera conclusión fue equivocada y la dejo escrita como advertencia:** dije *"no es runaway, siempre queda uno"* porque al borrarlos y recompilar reusaba el nombre liberado. **Falso.** Reusa nombres libres, pero si no hay ninguno libre **sigue sumando**. Una sola observación no alcanzaba.

**Lo que NO era la causa:** pensé que era por haberle pasado un evento con nombre explícito desde el DSL. Reconstruí el nodo `Assign` desde cero con `create_node` —que genera y **posee** su propio evento, exactamente como manda `nodes.md`— y **seguía duplicando en cada compile.**

🔴 **La causa real: el asset sin guardar.** El `K2Node_AssignDelegate` no reencuentra su evento generado hasta que el paquete se **serializa**. Verificado en vivo:
| Acción | Resultado |
|---|---|
| compile, compile, compile… | +1 evento vacío cada vez |
| **`save_assets`** → compile | **estable, sigue habiendo uno solo** |
| compile otra vez | **sigue uno solo** |

✅ **LA REGLA: después de cablear un `Assign<Delegate>`, `save_assets` ANTES de volver a compilar.** Por eso `BP_OSCReceiver` nunca tuvo el problema: se guardó hace meses.

⚠ **`clean_orphans.py` NO limpia esto**: los custom events son tipo ENTRY y el script no los toca nunca (y hace bien — borrarlos automáticamente sería peligrosísimo). Hay que borrarlos a mano con `delete_node`.
⚠ **Y `auto_layout.py` lo delata:** su chequeo `identical` dio **false** en este EventGraph, que fue lo que me hizo mirar. El script hizo bien su trabajo; la diferencia no era de layout, era un evento nuevo aparecido en el medio.

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
## ✅ Modo fake y verificación de la acumulación (2026-08-11)
`bFakeSignal` + `FakeHz` (instance-editable) hacen que el Tick genere dos senos y los meta **por el mismo `Ingest`** que va a usar la fuente real. 🔴 **Esa es la decisión de método:** el fake no escribe `Calm`/`Heart` directo — entra por la puerta de verdad, así que ejercita `Ingest → AccumCalm → arrays`. Un fake que escribiera las variables finales no probaría nada de lo que importa.

**Resultado, leído del actor en PIE:**
```
bConnected  true
Calm        0.100      <- crudo, en un valle del seno (rango 0.1..0.9)
CalmSmooth  0.210      <- REZAGADO respecto del crudo: el EMA filtra
Heart       60.8   HeartSmooth 62.3
BinCalmCount [17,15,17,15,15,17,15,1,0,0,0, ... 0]
```
🔴 **La forma de ese array es la prueba que importaba:** casillas 0-6 llenas, la 7 en curso, y **de la 8 en adelante exactamente 0**. El hueco es *explícito*, no un cero que parece dato. Y `CalmSmooth` yendo detrás del crudo prueba el filtro sin necesidad de graficar nada.

⚠ Los ~16 samples por casilla de 5 s son ~3 Hz, y **no es un bug**: Unreal **estrangula el PIE cuando la ventana no tiene foco**. El reloj de casillas va por delta time, así que avanza bien igual. Ojo con esto al medir cualquier tasa desde PIE por MCP.

## Getters para el consumidor (el panel)
| Función | Devuelve |
|---|---|
| `BinHasCalm(i)` / `BinHasHeart(i)` | bool — **hay que preguntar esto ANTES** de leer el promedio |
| `GetCalmBinAvg(i)` / `GetHeartBinAvg(i)` | `Sum / Count`, y **0 si no hay muestras** |
| `LogBin(i)` | debug: loguea índice, n y promedio de una casilla |

🔴 **El par "Has + Avg" es deliberado y no se debe colapsar en una sola función.** Si `GetAvg` devolviera un centinela, el panel dibujaría ese centinela como si fuera dato. §5 pide que los huecos se vean **tenues, no rotos**: *"un hueco roto parece falla, uno callado parece un pasaje"*. El consumidor **tiene** que consultar `BinHas*` y decidir. Con dos funciones, olvidarse es imposible de ignorar; con una, es el default.

## TODO
- [ ] Probar con una fuente OSC real (Muse). Hasta entonces, la ingesta está **construida pero no ejercitada**.
- [ ] Un `BP_BioHub_Fake` para poder trabajar sin EEG. Ya existen `BP_SignalProvider` / `BP_SignalProvider_Fake` en `Core/Signals/` (⚪ sin auditar): **revisarlos antes de construir**, puede que el mock ya esté hecho.
- [ ] Decidir qué pasa con **`BP_OSCReceiver`**: el BioHub lo reemplaza para la obra, pero sigue en uso en los niveles de test de Heart. Dos servidores en el mismo puerto UDP **no pueden coexistir** → no poner los dos en el mismo nivel.
- [ ] `Respiración` no entra por acá: viene del mando y solo durante *Entering* (§5). No mezclarla en el BioHub.

## Relacionados
- `BP_OSCReceiver` (el patrón del delegate, y el bloqueador del switch) · `BP_ProtoSoul` y `BP_Sensor` (sin construir) · [[BP_StageDirector]] (le va a pasar la etapa como int)
