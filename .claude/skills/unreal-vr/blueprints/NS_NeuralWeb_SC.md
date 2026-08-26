# NS_NeuralWeb_SC + BP_NeuralWeb_SC — la red neuronal de Loving (Core/VFX/)

## Purpose
El efecto central del Acto 6 (Loving): una **red neuronal viva** — puntos unidos por líneas que se deforman con curl noise, con conexiones que nacen y mueren reconfigurando la malla. Referencia de Beltrán: mallas tipo "plexus" azules sobre fondo oscuro.

## Status
🟡 **Efecto terminado y verificado en PIE + editor.** Compila sin errores, cero `Accessed None`. ⬜ **Falta el enganche al director** (ver §Integración pendiente) y el juicio de look en visor.

Colocado: **`NeuralWeb_Loving`** en `L_Loving_SC`. Los valores de instancia los está ajustando Beltrán a mano — **no pisarlos**.

## 🔴 Arquitectura (y por qué NO es el plexus clásico)
El plexus canónico usa **Particle Attribute Reader dentro de un Scratch Pad**, y el MCP **no puede crear ni editar Scratch Pads**. Además hace trabajo O(N²) por frame. Esta versión da el mismo resultado con costo casi nulo:

1. **El BP calcula la topología UNA vez** (`BuildWeb`, en Construction Script y BeginPlay): posiciones de reposo (`Rest`) y pares de vecinos filtrados por distancia (`PairsA`/`PairsB`), con seed determinística. `PushWeb` los empuja a Niagara como arrays + todos los escalares.
2. **Niagara solo COLOCA** (2 emitters CPU, sin fuerzas):
   - **Nodes**: burst de `NodeCount`, sprites. Posición = `NodeHomes[Particles.NodeIdx]`, releída en **Particle Update**. Tamaño aleatorio entre `DotMin`/`DotMax` × `DotScale`, escalado por `Reveal` vía `ScaleSpriteSize`.
   - **Links**: **spawn continuo** (`LinkRate`) con **vida finita** (`LifeMin`–`LifeMax`) → cada línea nueva toma un **par al azar** (`Particles.PairIdx` = `RandomRangeInt(0, LinkCount-1)`) → la red se reconfigura sola. Mesh renderer: cubo escalado (largo = distancia real) orientado con **`OrientMeshToVector`**. Fade in/out por `RampInOut(NormalizedAge)` en modo 2.
3. **El movimiento vive en el MATERIAL** (WPO, mismo Custom HLSL en ambos): curl noise de senos + respiración + **reveal**. Como las líneas son geometría, el noise se evalúa **por vértice** y el extremo del cubo —que está sobre el nodo— recibe el mismo desplazamiento: **no se pueden despegar**. Y al vivir en el shader, **se anima en el viewport sin Play** (requisito de Beltrán: autorar mirando).
4. **`MPC_NeuralWeb`** es el canal BP→shader: `NW_NoiseAmp` (= `lerp(AgitatedAmp, CalmAmp, Calm)`), `NW_NoiseFreq`, `NW_NoiseSpeed`, `NW_Pulse`, `NW_Reveal`, y el **vector `NW_Center`** (ver gotcha §227).

## Registro de variables (BP, todas instance-editable salvo las de estado)
| Categoría | Variable | Default | Rol |
|---|---|---|---|
| Forma | `Shape` | 0 | **0 = esfera · 1 = toroide.** El toroide usa `Radius` (radio mayor) + `TubeRadius`. |
| | `Radius` / `TubeRadius` | 140 / 45 | Tamaño de la nube / grosor del tubo del toroide. |
| | `NodeCount` | 120 | Cantidad de nodos. |
| | `MaxLinkDist` | 64 | Distancia máx. para conectar. **La palanca #1 del look de malla.** |
| | `LinkBudget` | 420 | Tope de conexiones del catálogo. |
| | `Seed` | 7 | Semilla; misma red siempre. |
| Ciclo de vida | `LifeMin`/`LifeMax` | 3 / 7 | Vida de cada conexión (s). `PushWeb` deriva `LinkRate = LinkCount / vida media`. |
| Look | `DotMin`/`DotMax` | 1.2 / 6.5 | Rango de tamaño de los puntos (variabilidad). |
| | `DotScale`, `DotColor`, `DotIntensity` | 1 / blanco / 2.5 | Multiplicador y color HDR de los puntos. |
| | `LineWidth`, `LinkColor`, `LinkIntensity` | 0.55 / celeste / 0.7 | Sección y color de las líneas. |
| Movimiento | `NoiseFreq` / `NoiseSpeed` | 0.012 / 0.35 | 🔴 **`NoiseFreq` es la palanca crítica**: si la longitud de onda es menor que la red, vecinos reciben empujones opuestos y las líneas se estiran hasta romper el look (fue el "se ve feo" del 2026-08-26). |
| | `CalmAmp`/`AgitatedAmp` | 5 / 16 | Amplitud del noise con calma 1 / 0. |
| | `BreathAmp`/`BreathPeriod` | 0.05 / 7 | Respiración radial. |
| | `RotSpeed` | 1.5 | Yaw °/s (solo en Play). |
| | `Calm` | 0.6 | La señal del EEG. |
| Aparición | `Reveal` / `RevealTime` | 0→1 / 3 | 0 = colapsada en el centro y puntos a tamaño 0; 1 = forma plena. Ease-out cúbico en el shader. |
| | `bStartHidden` / `AppearDelay` | — | Si nace invisible, y cuántos segundos espera la etapa antes de llamarla. |

**API para la obra:** `WebIn()` (nace desde el centro) · `WebOut()` (se va suave; al dejar de verse **se destruye sola** y avisa) · dispatcher **`OnWebGone`**.
**Funciones:** `BuildWeb` (topología) · `PushWeb` (empuja todo a Niagara) · `WebShow(Target)` (interpola `Reveal` y escribe `User.Reveal` + `NW_Reveal` + `NW_Center`) · `AnimateWeb` (⚠ **inerte**: quedó de la variante que animaba por CPU; sirve si alguna vez se quieren conexiones recalculadas por distancia real).

## 🔴 2026-08-26 (noche) — "el Niagara no aparece": recompilado, PERO quedó una intermitencia SIN causa
El síntoma: Alma habla el VO 21 (`habla`/`termino` en el log) y `WatchAlma` corre sin un solo error… pero nunca arma `PendingT` → la red muere invisible al cierre del step time (`se fue, destruyo` **sin** `nace` antes = la firma en el log). Todo lo estático sano: actor colocado, `TriggerVO=21`, `bStartHidden=true`, defaults limpios, grafo correcto.

**Lo que se hizo:** `compile_blueprint` de `BP_Alma_SC` + `BP_NeuralWeb_SC` (cero cambios de grafo; `BP_Alma_SC` se había recompilado a las 15:16 por la limpieza de duplicados y el consumidor podía tener bytecode viejo), ambos guardados. Tras eso: 3 corridas PIE-viewport ✓ y la corrida final de Beltrán en VR Preview ✓ (verificado por él en visor).

🟡 **PERO la explicación "bytecode viejo" NO cierra del todo:** la corrida VR de las 18:47 (log 16:47), YA con ambos recompilados, volvió a fallar — y la siguiente (18:52) funcionó. En la fallida la igualdad `CurrentVO==21` fue falsa durante ~18 s de ticks seguidos, sin ningún `Accessed None` (o sea `AlmaRef` era válido). **Eso no es una carrera de un frame: esa corrida entera leyó otra cosa.** Hipótesis descartadas con evidencia: segunda `BP_Alma_SC` en un sublevel (grep sobre `MapsV2/`: solo el persistente la referencia), `AlmaRef` nulo (cero Accessed None), defaults sucios (CDO e instancia leídos limpios).

**Estado de la evidencia por corrida (todas del 2026-08-26):** viewport 16:27/16:32/16:35 ✓✓✓ · VR 16:15 ✗ · VR 16:47 ✗ · VR 16:52 ✓ · VR ~16:56 ✓ (la de cierre de Beltrán). El modo NO discrimina (VR falló y funcionó); la intermitencia es real y **va a volver a aparecer en visor o APK**.

👉 **Plan pendiente (quedó diseñado, sin ejecutar):** sembrar UN print de armado en `WatchAlma` — Branch colgado del `then` libre de `Set bSeenVO` (`K2Node_VariableSet_32`, exec-out desconectado), condición = el `AND` del armado (`K2Node_CommutativeAssociativeBinaryOperator_23`, que ya alimenta el `Select_11`), True → PrintString `"NEURALWEB: veo el VO objetivo, armo el timer"`. Se dispara UNA vez por corrida. Con eso, toda corrida fallida se auto-documenta: sin print y sin Accessed None = la igualdad leyó mal → mirar QUÉ lee (`GetCurrentVO`) en vivo. Los refs de nodos de arriba ya están verificados con `get_node_infos`.

👉 Regla que sí queda: si un BP que LEE variables de otro deja de reaccionar sin errores después de que el otro se recompiló/limpió, **recompilar el consumidor antes de teorizar** — y la firma "destruyo sin nace" en el log es el detector barato de este fallo.

## 🔴🔴 Los gotchas que costaron la sesión (todos en gotchas.md §221-228)
1. **Un material editado por MCP no recompila** → queda con el shader ANTERIOR. Si el grafo estaba vacío, es un aditivo negro invisible **sin ningún error**. Peor: si el HLSL tiene error, Unreal usa el **Default Material** (gris opaco) y solo el log lo dice. Forzar con `set_properties` de una propiedad que **cambie de valor** (poner el mismo valor NO recompila).
2. **`ReturnExecIndex` no sirve en Particle Update** — devuelve lo mismo para todas y los 120 nodos colapsan en un punto. Guardar el índice en un atributo (`Particles.NodeIdx`) durante el Spawn.
3. **`ObjectPositionWS` significa cosas distintas según el renderer**: en **sprites** = el componente (centro de la red ✓); en **meshes** = la instancia (¡la propia línea!). Por eso el reveal encogía los puntos pero no las líneas. Solución: pasar el centro explícito por `NW_Center` (vector del MPC).
4. **El orden de módulos importa y `AddSetParametersModule` siempre agrega al final** → "read before being set". Hubo que borrar y recrear el spawn de Links en orden: PairIdx → Idx → Pos → derivados.
5. **`SpriteAlignment` escrito a mano NO lo aplica el sprite renderer.** Existe el módulo oficial `/Niagara/Modules/Debug/SpriteBasedLine` que resuelve la línea entera (start/end) — **usarlo si alguna vez se vuelve a sprites**; me habría ahorrado la sesión.

## 🎁 Lo que se rescató del Content Examples (`/Game/ExampleContent`)
- **`NeighborGrid3D/Plexus`** = el plexus de Epic (GPU, NeighborGrid3D, esferas + líneas, curl+vortex+attraction). 🔴 **NO compila en este proyecto**: su módulo `Collision` usa **Distance Fields**, que no existen en mobile (`niagara-quest.md` ya tenía verificado que la query GPU exige SM5+ y Quest es ES3.1). Duplicado a `Core/VFX/NS_Plexus_SC` y con Collision apagado **sigue colgando el compilador** → descartado, pero su receta (esferas + líneas orientadas + fuerzas) es la que se implementó.
- Módulos de librería útiles y **sin Scratch Pad**: `Debug/SpriteBasedLine`, `NeighborQuery/*`, `Update/Neighbor/{CalculateNeighbors,SampleNeighbors}`.

## 🔌 Integración con la obra
### ✅ Aparición — HECHA y verificada (2026-08-26)
**La red nace oculta (`bStartHidden=true`) y aparece cuando TERMINA el VO 21**, que es el **segundo VO de Loving** (`VOMove[3]`).

🔴 **Por qué no se hizo desde el director:** en Loving `bPanel` es ✘, así que el Sub 2 dispara `VOMove` y **salta directo a `StartStepTime`** — el director pone `WaitFor="time"` y por eso **ignora el `OnVOFinished` del VO 21**. Engancharse ahí no servía.

**Cómo está resuelto — sin tocar el director** (dependencia invertida, el patrón del proyecto): `WatchAlma(Dt)` corre en el Tick, cachea `AlmaRef` (`GetActorOfClass`, con reintento en la rama *Is Not Valid*) y **detecta el flanco de SUBIDA** de `Alma.CurrentVO == TriggerVO`: cuando Alma EMPIEZA el VO 21, espera `VODelayIn + AppearDelay` y nace **mientras el VO suena** (pedido explícito de Beltrán: *"que inicie con el voice over, no cuando termina"*). Sin ramas de ejecución (usa `select` para los valores), un solo multi-exec al final.
Perillas: **`TriggerVO`** (21, instance-editable — cambiando el número se ancla a cualquier otro VO) y **`AppearDelay`** (0 s; subirlo retrasa el nacimiento respecto al inicio del VO).

🔴🔴 **Dos caminos que NO funcionan, y por qué** (probados y descartados 2026-08-26):
1. **Detectar el flanco de BAJADA de `CurrentVO`** → `VODone` **NO limpia `CurrentVO`**: se queda con el índice del VO que terminó hasta que arranca el siguiente. El flanco recién ocurre al empezar el VO 22, mucho después.
2. **Preguntar `VOComp.IsPlaying`** → **`VOComp` es null / pending-kill**: Alma crea el AudioComponent dinámicamente. Además de no funcionar, spamea cientos de `Accessed None` por frame.
👉 Lo que sí sirve: `CurrentVO` **para saber QUÉ VO es**, y para el timing o bien el flanco de subida (ahora) o bien la **duración real del clip** (`VOClips[i]` → `Class|SoundBase|GetDuration`) si alguna vez se quiere anclar al final.

✅ **Verificado por log en corrida real** (`bAutoTest` temporal, flags restauradas después): `12:28:34` arranca el VO 21 → `12:28:35` **NEURALWEB: nace** → `12:28:39` termina el VO 21 (la red ya estaba). Vive 20 s.

### ✅ Salida + cierre de etapa — HECHA y verificada (2026-08-26)
🔴 **Cirugía en `BP_Director_Story`** (mínima, por nodos): en `StepTimeDone` se reemplazó el `Next()` final por **`CallFunction|CloseStageFX`** (función nueva). `CloseStageFX` busca la red (`GetActorOfClass`), si existe llama **`WebOut()`** y programa `Next` con `SetTimerbyFunctionName(self,"Next", WebOutTime)`; **si no existe, llama `Next()` directo** — por eso las otras 5 salas siguen igual sin condicionar por índice.
Variable nueva del director: **`WebOutTime`** (4 s, categoría *C - Tiempos y tags*). ⚠ Nació en **0** en el actor colocado (la trampa de siempre) → hay que setearla en la instancia.

**Secuencia verificada por log, con timestamps reales:**
```
11:52:44  STORY: sala 3 paso 3 espera: time   ← arranca el step time (18 s)
11:52:52  NEURALWEB: nace                     ← 3,5 s después de terminar el VO 21
11:53:02  STORY: la red se va, espero          ← 18 s exactos
11:53:05  NEURALWEB: se fue, destruyo          ← fade completo + DestroyActor
11:53:06  STORY: sala 3 paso 4                 ← desprendimiento de la proto ameba
11:53:16  STORY: sala 3 paso 5 (ring)          ← la carga
```
La red vive **12,7 s**. ⚠ Con el `StepGameTime` viejo de 10 s vivía **1,7 s** (nacía casi cuando ya cerraba) → por eso se subió a **18**. 🔴 **`StepGameTime` es GLOBAL**, no por sala: subirlo alarga el cortafuegos de las 5 salas. Es inocuo en Entering y Recognizing (cierran por su mecánica: el anillo de respiración y el ascensor), pero **si se quiere un tiempo propio de Loving hay que convertirlo en array por sala**.

## TODO
- [ ] 🔴 El enganche al director (arriba).
- [ ] Look en visor. El **fondo lila de la sala mata el contraste**; la referencia es azul sobre negro.
- [ ] **Fade por distancia** en las líneas (las largas más tenues) — es lo que más acerca a la elegancia de la referencia.
- [ ] Probar `Shape = 1` (toroide) y ajustar `Radius`/`TubeRadius`.
- [ ] Medir en APK. Y decidir CPU vs GPU: **GPU sim funciona en Quest 3** pero exige declarar `quest3` en el metadata del APK (si no, corre en modo compatibilidad Quest 2 y no anda). Ver `niagara-quest.md`.

## Relacionados
[[NS_LovingField]] (el patrón `User.Calm`) · [[BP_Director_Story]] (§Loving) · `references/niagara-quest.md` · `references/gotchas.md` §221-228
