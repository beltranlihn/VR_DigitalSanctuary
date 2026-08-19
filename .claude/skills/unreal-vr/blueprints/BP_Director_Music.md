# BP_Director_Music — el ambiente de la obra (Core/Audio/)

## Purpose
**Dirige el ambiente sonoro del recorrido**: un array de clips y un crossfade entre ellos, disparado por el avance de [[BP_Director_Movement]]. Vive en el nivel persistente **`L_SoulCharger`**.

Pedido de Beltrán (2026-08-17): *"un director de música que va a dirigir los ambientes de cada etapa … un array con los distintos clips para yo poder cambiarlos después … crossfade entre uno y otro, gatillados por el movimiento"*.

## 🔴 Decisión de audio: estéreo head-locked, sin espacializar
El ambiente **es el score de la obra, no un objeto de la sala**, así que suena en 2D y gira con la cabeza. Es lo correcto y además esquiva todo el problema de espacialización de este proyecto: **no hay spatializer de Meta para UE 5.8 y Unreal no trae HRTF propio** (`references/audio-quest.md`). La advertencia de Meta de *"evitar head-locked"* apunta al sonido diegético, no a la música.
⚠ Consecuencia práctica: los 9 clips son **estéreo y en loop** (112–180 s) y así deben quedarse. Si alguna vez algo tiene que sentirse *en un lugar de la sala*, ese sonido va aparte y en mono.

## Status
🟡 **Construido, compilando y con los 9 clips cargados. Falta colocarlo en el nivel y probarlo** — no se colocó porque tocar el world requiere pedido explícito de Beltrán (`gotchas.md` §114).

## Registro de variables

### A - Clips (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `AmbientClips` | 9 entradas (ver tabla) | 🔴 **La entrada *i* es el ambiente de la parada *i*.** Cambiar un clip = cambiar la entrada, cero código. Una entrada **vacía** = se mantiene el clip anterior. |

🔑 **Repetir un clip en entradas consecutivas = SOSTENERLO.** La comparación es **por clip, no por índice**: si la parada nueva pide el mismo sonido que ya está sonando, no hay cruce ni reinicio, sigue de largo. Es el idioma de autoría para que un ambiente abarque varias paradas, y evita el caso feo de un clip cruzando consigo mismo.

Mapeo actual (ajuste de Beltrán, 2026-08-17): el clip 2 **se sostiene entre las paradas 1 y 2**, y eso realinea todo — el clip "Hall" cae justo en la parada del Hall, y cada sala queda con el ambiente de su nombre.

| Parada | Clip | |
|---|---|---|
| 0 (inicio, X=−5000) | `1_-_Intro` | |
| 1 | `2_-_Start` | |
| 2 | `2_-_Start` | ← **se sostiene** |
| 3 (Hall, X=0) | `3_-_Hall` | |
| 4 (Entering, 1500) | `4_-_Breath` | |
| 5 (Recognizing, 3000) | `5_-_Heart` | |
| 6 (Loving, 4500) | `6_-_Mind` | |
| 7 (Attracting, 6000) | `7_-_Surrounding` | |
| 8 (Surrounding, 7500) | `8_-_Salida` | |

`9_-_Credits` queda libre para el cierre de la obra.
⚠ **El array se serializa en la instancia**: cambiarlo en el CDO **no** actualiza el actor ya colocado. Hay que escribir los dos (verificado 2026-08-17).

### B - Mezcla (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `CrossfadeTime` | 3.0 s | Duración del cruce. Gobierna **el fade in del nuevo, el fade out del viejo y cuándo se libera el viejo** — los tres son el mismo número, así que el cruce siempre cierra parejo. |
| `MasterVolume` | 1.0 | Volumen general. **Se aplica en vivo**: cambiarlo durante el play se oye al instante. |

### Z - Estado interno
`CurrentComp` / `PrevComp` (los AudioComponent en juego) · `CurrentIndex` (−1 al arrancar) · `LastVolume` (para no reescribir el volumen cada tick) · `MoverRef` · `bWasWalking`.

## Los beats del final: `NextTrack()` — y por qué NO se duplican puntos del spline
Al terminar el recorrido hay **dos beats más que sólo cambian la música**, sin avanzar, sin viñeta y sin pasos (pedido de Beltrán, 2026-08-17). Él planteó la alternativa de agregar dos puntos encimados al final del spline; **se descartó, y la razón importa**: un tramo de largo cero **igual corre toda la maquinaria de caminata** — haría el fade de la viñeta estando quieto (la viñeta sigue la **velocidad**, no `LegWalkIntensity`) y arrancaría la lógica de pasos. Habría que pelear contra las dos, y encima deja puntos invisibles encimados en la superficie de autoría del spline.

✅ **`NextTrack()`** — avanza un ambiente y nada más: `PlayIndex(CurrentIndex + 1)`. Con eso el array deja de ser "parada *i*" y pasa a ser **"beat *i*"**, que es el modelo honesto: los dos últimos no son paradas.
- Entradas **0..8** = las 9 paradas del recorrido · entrada **9** = `9_-_Credits`, el primer beat extra · **la entrada 10 hay que agregarla** cuando exista el clip del segundo beat (hoy el array tiene 10 entradas; pedir el índice 10 loguea *"no hay clip"* y sostiene lo que suene).
- 🧪 **Tecla `2`** avanza un track a mano (`bDebugKey`, categoría E - Test), igual que la tecla `1` avanza un tramo en el director de movimiento. ⚠ **Sin probar por mí** — no puedo presionar teclas; probarlo en el editor.
- Cuando exista la lógica de cierre de la obra, es ella la que debe llamar a `NextTrack()`.

## Cómo se dispara — y por qué así
El crossfade arranca **cuando empieza el movimiento**, no al llegar (pedido explícito). El director de música **observa** al de movimiento: detecta el flanco de `bWalking` (false→true) y pide el clip de la parada **destino** (`LegIndex + 1`).

- 🔴 **Se eligió polling del flanco y no el dispatcher.** `BP_Director_Movement` **sí expone `OnLegStarted`** (se agregó y se emite en `WalkLeg`), pero atarlo por MCP requiere cirugía de un `CreateEvent` + `BindEvent`, con varias formas de fallar en silencio. El flanco de `bWalking` da **el mismo instante** con 6 nodos y sin riesgo. Un frame de diferencia es irrelevante para un cruce de 3 s.
- 👉 **Si algún día se quiere el dispatcher, ya está publicado**: `OnLegStarted` se emite en cada tramo y no cuesta nada tenerlo.
- El arranque (parada inicial) no depende del movimiento: `Boot` pide directamente el clip de `StartIndex` del mover, así que el clip 1 suena desde el principio aunque nunca se camine.

## Estructura de grafos
- **`EventGraph`** — `BeginPlay` → timer 0,35 s → `Boot` (el retraso es por el `Possess`, misma razón que en el director de movimiento). `Tick` → `CheckLeg` + `ApplyVolume`.
- **`Boot()`** — `GetActorOfClass(BP_Director_Movement)` → `MoverRef`, `CurrentIndex = −1`, y `PlayIndex(StartIndex del mover)`. Loguea si no encuentra el director.
- **`CheckLeg()` / `CheckLegInner()`** — el guard de `IsValid` y el flanco de `bWalking`, partidos en dos porque un `IsValid` corta la lista de statements del DSL.
- **`PlayIndex(Index)`** — 🔴 **el único punto de entrada.** Ignora el pedido si el índice es el que ya suena o si está fuera del array (y lo loguea). Es la función a llamar desde afuera si algún día otra cosa quiere cambiar el ambiente.
- **`DoSwap(Index)`** — `FadeOutCurrent()` → spawnea el clip nuevo (`SpawnSound2D`, `bAutoDestroy`) → `FadeIn(CrossfadeTime)`. El nuevo entra mientras el viejo sale: **es un cruce real, no un corte**.
- **`FadeOutCurrent()`** — pasa el actual a `PrevComp`, le hace `FadeOut(CrossfadeTime)` y agenda `KillPrev` a ese mismo tiempo.
- **`KillPrev()`** — destruye el componente viejo **cuando el fade terminó**. Mismo criterio que los pasos: no se arrastra memoria y no hay corte duro.
- **`ApplyVolume()` / `PushVolume(V)`** — el volumen se escribe **solo cuando cambia** (compara contra `LastVolume`), así el Tick no hace trabajo por gusto.

## TODO
- [ ] 🔴 **Colocarlo en `L_SoulCharger`** (pedir a Beltrán) y probar el recorrido completo con la tecla 1.
- [ ] Ajustar `CrossfadeTime` en visor: 3 s es un punto de partida, no una medición.
- [ ] Los clips son **estéreo y largos** → codec **Bink** para drones largos, nunca `PLATFORM_SPECIFIC` (=OGG, que no seekea). Ver `audio-quest.md`.
- [ ] Masterizar a −16 LUFS (recomendación de Meta) y **verificar la mezcla con auriculares**, no con los parlantes del visor.

## Relacionados
- [[BP_Director_Movement]] — la fuente del disparo (`bWalking`, `LegIndex`, `OnLegStarted`).
- `references/audio-quest.md` — por qué head-locked, los codecs y las trampas del config de audio en Android.
