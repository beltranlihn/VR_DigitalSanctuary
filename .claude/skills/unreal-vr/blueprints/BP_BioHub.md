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

### 🆕 2026-08-15 — la simulación ahora también le da de comer al sensor de latido
Había **dos fuentes de referencia distintas** y sólo una estaba simulada: el HUD y el gráfico leían el BioHub (LFO vivo), pero [[BP_HeartSensor]] lee **`BP_OSCReceiver.HeartRate`** — un valor **fijo 75.5** de otro Blueprint. Resultado: la etapa Recognizing dependía de un actor que ni siquiera estaba en el nivel.

**Puente nuevo**: `FakeTick` calcula el BPM **una sola vez** (`_bpm`), lo manda al `Ingest` de siempre **y** cierra con **`PushFakeHeart(Bpm)`**, que cachea el `BP_OSCReceiver` del nivel (`OSCOut`, con `GetActorOfClass` + cast en la rama `Is Not Valid`) y le escribe `SetHeartRate(Bpm)`. Verificado en PIE: `BIO: latido simulado conectado al receptor` (se loguea **una sola vez**, al cachear).
👉 Con esto **el latido del corazón late al ritmo simulado (68 ± 9 bpm, ciclo lento)** en vez de a un número fijo, y se prueba la obra entera sin hardware.
⚠ Sólo corre bajo `bFakeSignal` (vive dentro de `FakeTick`): **cuando llegue el server OSC real, `bFakeSignal = false` y el puente se apaga solo** — no compite con la señal verdadera.

🔴 **Trampa de DSL que costó tres intentos acá**: en `CallFunction`, los argumentos **posicionales empiezan por `self`**, así que `(CallFunction|Ingest X Y)` intenta conectar `X` a `self` y falla con *"Could not connect pin … to self"*. **Siempre keywords** (`:Addr`, `:Value`, `:N`, `:Bpm`) — y ojo que el pin de `IngestInt` se llama **`V`**, no `Value`.

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


## 🆕 2026-08-27 — `Series(bHeart)` : las casillas como CSV (F1 del plan de cierre)
El consumidor del retrato (plan `docs/PLAN-CIERRE-2026-08-27.md`) no quiere las casillas de a una:
quiere **la serie entera como texto** para meterla en el `.sav`. Eso es **`Series(bHeart) -> CSV`**,
la única función nueva de este BP.

- Recorre las casillas **0 .. `CurrentBin`** (clampeado a `BinCountMax`), o sea **sólo lo transcurrido**;
  no escribe las 180 si la obra duró 3 minutos.
- Por casilla emite `Sum / Count` redondeado con `SnapToGrid` (**0.001** para la calma, **0.1** para el
  ritmo) y **`-1` cuando `Count == 0`** — el hueco explícito, no un cero que parece dato.
- Junta todo con `JoinStringArray` sobre la variable de andamio **`Tmp`** (String[]).
- ⚠ **Divide por `Max(Count, 1)`**, no por `Count`: el `select` de Blueprint **evalúa las dos ramas**,
  así que sin el `Max` cada casilla vacía dispararía un divide-by-zero y ensuciaría el log.
- Lo usa [[BP_SoulArchive_SC]] (`TakeBio`), que llama `Series(false)` para la calma y `Series(true)`
  para el ritmo. Verificado en PIE: a los 12 s devolvió 3 valores reales.

⚠ **Deuda pre-existente detectada de paso**: el EventGraph tiene **6** `OnOscMessageReceived_Event*`
(uno con el handler, cinco vacíos) — es el gotcha del `Assign<Delegate>` documentado más arriba.
No los borré para no tocar la cadena OSC en medio de otra tarea; hay que barrerlos con `delete_node`
y **guardar antes de volver a compilar**.


---

## 2026-08-28 — OSC real conectado: puerto 10000 y direcciones `/muse/*`

Beltrán pidió dejar la cadena lista para probar con el sensor de verdad. Es el momento que él mismo había
agendado el 2026-08-14 (*"OSC se integra AL FINAL, con toda la mecánica lista"*).

| Perilla | Antes | Ahora |
|---|---|---|
| `Port` | **8000** | **10000** |
| `AddrCalm` | `/calm` | **`/muse/calm`** (float 0–1) |
| `AddrHeart` | `/hr` | **`/muse/heart_rate`** (float, bpm) |
| `AddrSensorOn` | `/sensor` | **`/muse/sensor_active`** (int 0/1) |
| `bFakeSignal` | **true en la INSTANCIA** | **false** |
| `ListenIP` | `0.0.0.0` | igual (escucha en todas las interfaces) |

🔴 **Dos cosas que había que corregir, no sólo escribir:**
1. **El puerto era el 8000 — el mismo del servidor MCP del editor.** En PIE eso es una colisión directa.
2. **`bFakeSignal` estaba en `true` en la instancia del nivel** (y en `false` en el CDO): el LFO de
   simulación pisaba la señal real. Es la §"lo de la instancia le gana al Blueprint" otra vez.

`Port`, `ListenIP` y `AddrSensorOn` **no eran instance-editable** (`set_properties` sobre el actor fallaba
con *"the following properties could not be set"*). Se marcaron editables para poder ajustarlas desde el
nivel sin recompilar.

### 🛡 `IngestFloat`: tolerar que `sensor_active` llegue como float
`HandleOsc` probaba primero `GetOSCMessageFloatAtIndex` y sólo caía a la rama entera si eso fallaba. Con un
emisor que mande `sensor_active` como **1.0** en vez de **1** (lo hace medio mundo: python-osc, Max, TD),
el mensaje entraba por la rama float, no coincidía con `AddrCalm` ni `AddrHeart` y **se perdía en silencio**.
```
(fn IngestFloat (Addr Value)
  (CallFunction|Ingest Addr Value)                       ; calma / ritmo + el watchdog de conexión
  (if (== Addr AddrSensorOn) (SetbSensorOn (> Value 0.5))))
```
`HandleOsc` ahora llama a `IngestFloat` en vez de a `Ingest`. **`Ingest` quedó intacta** — no se puede
reescribir por DSL porque contiene setters de bools con prefijo `b` (§62), y de paso no había motivo para
tocar lo que ya andaba.

✅ **VERIFICADO CON EL EMISOR REAL** (2026-08-28, Beltrán transmitiendo en vivo). Seis muestras seguidas leídas del BioHub **dentro de PIE**:
```
Calm   0.344 -> 0.364 -> 0.383 -> 0.395 -> 0.409 -> 0.445
Heart  74.5  -> 76.3  -> 77.2  -> 76.9  -> 76.9  -> 76.0   bpm
bSensorOn = true · bConnected = true · SinceLastMsg = 0 (mensajes cada frame)
```
Las tres direcciones llegan y los valores **se mueven** — no es un dato pegado.

⬜ Lo que sigue sin probarse: el mismo emisor contra el **APK en el visor** (ahí cambia la red: el Quest tiene que alcanzar al emisor, o el emisor al Quest).

**Nota histórica**: no se había probado con un emisor real al escribir esto. Lo que sí está comprobado es la forma del grafo y que
el servidor se crea con `ListenIP` + `Port` en `BeginPlay` (`CreateOSCServer` → `AssignOnOscMessageReceived`
→ `HandleOsc`). Si no llega nada, el orden de sospecha es: firewall de Windows / red del Quest → puerto →
tipo del argumento → dirección exacta.
