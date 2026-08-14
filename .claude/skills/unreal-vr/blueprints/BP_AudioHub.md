# BP_AudioHub + BP_HapticHub — el framework de audio y haptics (Core/Audio/)

## Purpose
El **punto 1.d del plan del guión**, que se había saltado: *"Audio + haptics framework (placeholders desde el día 1)"*. Hasta ahora cada pieza traía su propio array de clips y su propio log de "falta clip" — funcionaba, pero no compartía catálogo, y los tiempos del guión quedaban hardcodeados. Estos dos actores son **el único lugar donde vive el catálogo**; cada acto sólo pide por nombre o por índice.

Los dos se colocan **una vez en `L_Persistent`** y se buscan con `GetActorOfClass`, igual que [[BP_BioHub]].

## Status
🟢 Verificado por log (2026-08-15, `DebugStartStage=3`): el hub reporta su catálogo, Loving pide `SMind1/2/3` y los VO 15/16/17, la ceremonia pide el VO 18 y el SFX `SCharger`. Con el catálogo vacío **todo sigue corriendo** y cada falta se loguea. Cero `Accessed None`.
⬜ Falta cargarlo con los archivos reales (los 8 ambients, ~22 SFX y 30 VOs son insumo de Beltrán) y probar el crossfade con audio de verdad.

---

# BP_AudioHub

## Catálogo (todo instance-editable, se llena desde el detalle del actor)
| Variable | Tipo | Rol |
|---|---|---|
| `SfxMap` | **Map<String, SoundBase>** | El catálogo por nombre: `STitle`, `SBubble`, `SSelect`, `SPasos`, `SBell`, `STrigger`, `SDoor`, `SCharger`, `SPulse`, `SMind1-3`, `SDraw`… Entrada que falta = silencio + log. |
| `AmbientMap` | Map<String, SoundBase> | Los 8 ambients en loop, uno por tramo. |
| `VoClips` | Array<SoundBase> | Los 30 VOs, **por índice del guión** (0-based: el VO 16 del guión es el índice 15). |

💡 **El Map de String→SoundBase SÍ se puede crear por MCP**: `add_object_variable` con `container_type: "Map"` genera *Map of Strings to Sound Base Object References*. No hacen falta arrays paralelos.

## API
| Función | Qué hace |
|---|---|
| **`PlaySfx(SfxName)`** / **`PlaySfxAt(SfxName, Loc)`** | Busca en `SfxMap`. Falta → `AUDIO: falta SFX <nombre>`. |
| **`PlayVo(Index) → Seconds`** | 🔴 **Devuelve la DURACIÓN del clip, o −1 si no hay clip.** Es la pieza clave: el guión dice que *"los tiempos se cuelgan de la duración del clip, nunca hardcodeados"*. El llamador hace `espera = (dur > 0) ? dur : <su tiempo placeholder>`. |
| **`PlayAmbient(AmbName, FadeTime)`** | Crossfade real: `SwapAmbient` hace fade out del componente activo, `SetSound` en el otro y fade in, alternando `AmbA`/`AmbB` con `bUseA`. |
| **`StopAmbient(FadeTime)`** · `ReportCatalog` | Apagado y el log de arranque (`AUDIO HUB: SFX en catalogo = N | ambientes = N | VOs = N`). |

🔴 **`FadeIn`/`FadeOut` están DUPLICADOS**: el `type_id` `Audio|Components|Audio|FadeIn` existe para `AudioComponent` **y** para `SynthComponent`, y el DSL agarra el de Synth (se ve en el pin `self`: *Synth Component Object Reference*). Por eso viven en dos funciones mínimas, **`FadeCompIn`/`FadeCompOut`**, construidas por cirugía con `create_node` + **`declaring_class: /Script/Engine.AudioComponent`**. Es la trampa #3 de `dsl.md` en vivo.

---

# BP_HapticHub

Los **3 patrones reusables** que pide el plan, sin ningún asset: todo con `Game|Feedback|SetHapticsbyValue` sobre el Player Controller.

| Función | Default | Para qué |
|---|---|---|
| **`HapticHover(bRight)`** | amp 0.15 · freq 0.4 · 0.06 s | Pulso muy suave de entrada/salida. |
| **`HapticSelect(bRight)`** | amp 0.7 · freq 0.8 · 0.12 s | Pulso fuerte de confirmación. |
| **`HapticHold(bRight, bOn)`** | amp 0.35 · freq 0.25 | Vibración continua — la del umbral de Heart. `bOn=false` la corta. |
| `HapticPulse(bRight, Amp, Freq, Time)` · `HapticSet` · `HapticStop` · `StopPulseHand` | — | El motor. `bEnabled` apaga todo de una. |

- **La mano se pasa como `bool bRight`, no como enum.** El pin `Hand` es un `EControllerHand`, y **un enum sólo entra como literal en el pin, nunca por cable**: `(select bRight "Right" "Left")` falla con *"Could not connect pin ReturnValue to Hand"*. Por eso `HapticSet` ramifica con un `if` y cada rama pone el literal.
- `StopPulseHand` **apaga las dos manos** a propósito: un pulso dura 60-120 ms y así el timer no necesita recordar cuál fue.

---

## Quién ya lo usa (y quién falta)
| Consumidor | Estado |
|---|---|
| [[BP_Stage_Subclases]] §Loving | ✅ **Retrofiteado**: `BeatAudio(i)` pide `PlaySfx(MindSfx[i])` y `PlayVo(VoIndex[i])`, y `ShowBeat` **espera la duración del VO** si existe, o `BeatTimes[i]` si no. Sus arrays propios `VoClips`/`MindClips` se borraron. |
| [[BP_Ceremony]] | ✅ **Retrofiteado**: `CeremonyVo(Index)` mapea etapa→VO global con `VoIndexByStage` ([-1,10,13,18,22,25]) y `PlayCharger` pide `PlaySfxAt("SCharger", SpotLoc)`. Sus `VoClips`/`ChargeSfx` se borraron, y de paso murió el homónimo `PlayVo`/`PlayVoAt` que colisionaba con el hub. |
| Breath · Heart · Attracting · Intro · Hall | ⬜ Siguen con sus clips locales. Migrarlos es mecánico: cachear el hub y cambiar la llamada. |
| Haptics | 🟡 **Cableado el primero (2026-08-15)**: `BP_Stage_Recognizing.FireJump` → **`BeatFeedback`** → `HapticSelect` + `PlaySfx("SPulse")`. Ataca el punto 3 del memo de visor (*"tampoco sentí el pulso haptic"*). 🔴 **No verificable en PIE**: el latido sólo dispara con el sensor en la zona del pecho, y sin visor no hay manos. ⬜ Faltan: hover del menú, hover de la elección del Hall, hold del umbral. |

## 🐛🐛 El bug que cazó la lectura del grafo: `(return (CallFunction|Impure …))` NO ejecuta la llamada
Escrito así, el DSL conecta el valor al `FunctionResult` **pero deja el nodo FUERA de la cadena de exec**:
```
Branch --then--> FunctionResult          ← el PlayVoClip cuelga solo, su "then" va a []
```
Compila en verde y devuelve el default del pin. Síntoma en el log: **la función nunca imprime nada**, y como el llamador tenía un fallback razonable (`BeatTimes`), el tiempo medido era idéntico al correcto — o sea, **el bug era invisible por temporización**. Lo delató que faltaba la línea `AUDIO: falta VO 15`.

**La forma correcta:** llamar como statement, bindear, y recién ahí devolver.
```
(bind _d (CallFunction|PlayVoClip :Index Index))
(return _d)
```
⚠ **Y el barrido de huérfanos NO limpia los restos**: `clean_orphans.py` trata cada `K2Node_FunctionResult` como **entrada**, así que los `FunctionResult` viejos de la reescritura quedan "vivos" y mantienen viva toda la isla muerta que los alimenta. Hay que **borrar a mano los `FunctionResult` sobrantes** antes de barrer. Es la primera vez que aparece: pasa sólo al reescribir funciones **con valor de retorno**.

## TODO
- [ ] Cargar el catálogo real cuando lleguen los archivos (Beltrán). Empezar por `SCharger`, `SMind1-3` y los VO de Loving/ceremonia, que ya están cableados.
- [ ] Migrar los consumidores que quedan (tabla de arriba).
- [ ] 🔴 **Cablear los haptics**: pulso de Heart (`PulseJump` → `HapticSelect`), hover del menú y de la elección del Hall, hold del umbral.
- [ ] Ambients: falta que alguien llame `PlayAmbient` en cada transición de puerta (el hook natural es el `WalkOut`/`EnterRoom` de [[BP_StageDirector]]).
- [ ] ⚠ `audio-quest.md`: el bloque de audio del `DefaultEngine.ini` está bajo `WindowsTargetSettings` → **el APK no lo lee**. Revisar antes de empaquetar. Fuentes espacializadas = **mono**.

## Relacionados
- [[BP_Ceremony]] · [[BP_Stage_Subclases]] (§Loving) · [[BP_BioHub]] (mismo patrón de hub único en el persistente) · `references/audio-quest.md`
