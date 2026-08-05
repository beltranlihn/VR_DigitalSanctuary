# BP_SeqSlot — progress tracker

Un slot del secuenciador del stage Touch (Fase 4). Data holder: sabe su paso y qué burbuja tiene encima.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_SeqSlot.BP_SeqSlot`  ·  **parent**: Actor  ·  **in level**: 5 en `L_Touch`, fila a `X=55, Z=75`, `Y = −60/−30/0/+30/+60` (120cm de ancho = alcance de brazo sentado). `StepIndex` 0-4 verificado y **coincidente con el orden espacial izquierda→derecha**, así la melodía suena en el mismo orden en que se ve. (Posiciones aplicadas el 2026-08-03: estaban las 5 apiladas en el origen.)
- **Status**: 🟢 Fase 4 lista y probada. 🟡 **El pulso de escala en el beat es nuevo (2026-08-05) y falta test en visor.**

## 🆕 Pulso de escala en el beat (2026-08-05)
El slot **marca con un pulso de escala que el playhead está en su paso**, esté ocupado o no: así la mesa entera comunica el ritmo y dónde va la secuencia, no solo las burbujas colocadas.
- **`Pulse()`** — `PulseT = 1.0`. Lo llama `BP_AttractDirector.OnBeat` sobre el slot del paso actual.
- **`UpdatePulse(Delta)`** (Tick) — `PulseT` decae a razón de `PulseDecay` con clamp en 0, y `Marker.RelativeScale3D = BaseScale × (1 + PulseT × PulseAmount)`.
- **`CacheBase()`** (BeginPlay) — guarda la escala **autoral** del `Marker`.
- Vars nuevas: `PulseT` · `PulseAmount = 0.35` · `PulseDecay = 3.0` (ambas **instance-editable**) · `BaseScale : Vector`.
- 🔴 **La escala del `Marker` es NO uniforme (0.2, 0.2, 0.04)** → `BaseScale` es un **Vector** y se multiplica por un factor escalar. Un `MakeVector(s,s,s)` uniforme devolvería el mesh a su tamaño base — es el gotcha que ya hizo aparecer el botón gigante en el visor. Ver `gotchas.md`.

### 🔴 Solo pulsa DESPUÉS de las instrucciones
El reloj de Quartz arranca en BeginPlay, pero la mesa **no debe latir mientras el usuario lee las instrucciones**.
- `BP_AttractDirector` gana **`bExperienceStarted`** (default false) y **`StartExperience()`**.
- `OnBeat` pulsa el slot **solo si `bExperienceStarted`**; el resto de la cadena (log + `PulseOnBeat` de la burbuja ocupante) queda igual. Se insertó por cirugía justo después de `SetCurrentStep`.
- Lo enciende **`BP_TouchInstrPanel.Finish()`**, que cachea el director en `DirectorRef`.
- 👉 Ese flag es el **enganche natural para R6/R8**: lo que deba arrancar "cuando empieza la experiencia" se cuelga ahí en vez de inventar otro canal.

### ⚠ Trampas de construcción
- **`create_node` con nombres colisionantes**: `UpdatePulse` existe también en `BP_SoundBubble`. Pasar **`declaring_class`** y verificar con `get_node_infos` que el `type_id` sea `|UpdatePulse` con pin `self` propio. ⚠ El read muestra `Class|BPSoundBubble|UpdatePulse` aunque esté bien — etiqueta lossy, no el nodo.
- **En un nodo `Class|Algo|Funcion` el pin de entrada 0 es `execute` y el 1 es `self`** (el target). Conectarlo al 0 falla con *"Could not connect pin X to execute"*.

## Componentes
- `DefaultSceneRoot` · `Marker` (cilindro chato radio 10 alto 4, placeholder del slot).

## Variables
- `StepIndex` : int — su paso 0-4 en el secuenciador · **instance-editable** (seteado por instancia en el nivel).
- `Occupant` : BP_SoundBubble ref — la burbuja colocada, o inválido si vacío. Público (lo leen/escriben la burbuja y el Director por accesor cross-class).

## Grafos
- Ninguno (data holder). La burbuja escribe `Occupant` al colocarse (`TryPlace`), el Director lo lee en `OnBeat`.

## TODO / next
- **`BP_SeqTable`**: mesa visual bajo los slots (aún NO construida — los slots funcionan sin ella). Podría spawnear/posicionar los 5 slots en vez de colocarlos a mano.
- Material unlit emisivo para el `Marker` (Quest). Highlight cuando está apuntado/ocupado (opcional).
- **Fase 7 (swap):** cuando llega una burbuja a un slot ocupado → la vieja vuelve a su `HomeLocation`. Falta `HomeLocation` en la burbuja + lógica de swap.
- Función `ClearOccupant()` (set Occupant null) para liberar el slot al re-agarrar (ver pendiente en `BP_SoundBubble.md`).

## Session log
- 2026-07-30: creado (Marker + StepIndex + Occupant). 5 colocados en `L_Touch` con StepIndex 0-4. La colocación la maneja `BP_SoundBubble.TryPlace` (busca el primer slot vacío dentro de `PlaceRadius` y setea `Occupant`).
