# Investigación: un sinte, un arpa y un arpegiador para Attracting (2026-10-27)

> Pedido de Beltrán después de probar **Virtuoso** en el Quest: *"tiene que ser totalmente por ahí"*, sobre todo el **arpa**: *"muy sensible y reactiva, y el sinte o sonido es muy lindo. Además tiene efectos"*. Preguntó cómo está hecha, si se hace con MetaSounds, qué tan difícil es, cómo hacer un arpegiador y un sinte, y qué hay en Fab. **Solo investigación: no se tocó Unreal.**
> Base técnica que ya existía: [`references/audio-quest.md`](../../.claude/skills/unreal-vr/references/audio-quest.md) (MetaSounds, Quartz, espacialización y códecs en Quest, investigado el 07-17). Este documento no lo repite: lo usa.

---

## 1. Virtuoso: lo que se sabe y lo que no

**Se sabe:**
- Es de **Really Interactive** (Suecia), lo publica **Fast Travel Games**. Salió en Quest el 10 de marzo de 2022; antes pasó por SideQuest y App Lab.
- Sus instrumentos están hechos para la VR y **toman instrumentos reales como plantilla** (batería, arpa).
- **El sonido y los efectos se moldean con los mandos mientras se toca.** Tiene **escalas prefijadas** y **sincronía de tempo** (para no desafinar ni salirse del pulso), un **looper** y un micrófono con reverb.
- Nació como una demo para controlar un estudio por WiFi. Después le sumaron **"un sintetizador de código abierto"** para que funcionara sin equipos (Jonatan Crafoord, en el blog de Meta).

**No se sabe:** ni el motor ni qué sinte usan. No encontré charlas técnicas ni entrevistas que lo digan. Lo más probable es Unity con una librería de síntesis (Csound, libpd o similar), pero **es una suposición**.

## 2. Por qué un arpa así se siente "sensible y reactiva"

No es una sola cosa, son siete. Es la receta habitual de los instrumentos de VR que se sienten bien; no es el código de Virtuoso, que no está publicado.

1. **No se salta ninguna cuerda.** Cada cuadro se traza el segmento entre la punta del mando del cuadro anterior y la del actual, y se cruza contra todas las cuerdas. A 72 Hz, una mano rápida avanza 3-4 cm por cuadro: si solo se mira dónde está la punta ahora, un barrido rápido se come cuerdas.
2. **La velocidad es la dinámica.** La velocidad de la mano, perpendicular a la cuerda, es la *velocity* de la nota. Mueve el volumen **y el brillo** (el corte del filtro): lento suena suave y oscuro, rápido suena fuerte y brillante. Esto es lo que más se siente como "sensible".
3. **Suena en el acto.** Un instrumento que se toca no se cuantiza: la nota sale en el mismo cuadro en que se cruza la cuerda. El secuenciador y el arpegiador sí se cuantizan.
4. **No hay nota mala.** Cada cuerda es una nota de la escala.
5. **Tres respuestas en el mismo cuadro:** el sonido, un pulso háptico corto por cuerda y la cuerda que vibra a la vista (una onda en el WPO que se apaga).
6. **Lo "lindo" está en la cola y en los efectos**, más que en el oscilador: ataque rápido, cola larga, reverb grande y delay a tempo.
7. **Polifonía y latencia baja.** Cada cuerda suena sola, así que un rasgueo deja todas sonando. Y del gesto al oído pasan pocos milisegundos (ver §5: hoy el APK no cumple esto).

## 3. ¿Con MetaSounds? Sí, es la herramienta

MetaSounds es **Production Ready** desde 5.4. Viene encendido y compila para Android (detalle en `audio-quest.md`). Hoy el proyecto **no tiene ningún MetaSound en uso**: las esferas son samples (`M1S1..M1S20`) y un pad (`PadM1`). Los `MS_Synth`/`MS_Perc` de Touch quedaron archivados.

**Nodos que existen en 5.8**, verificados en el código del motor: osciladores (seno, sierra, cuadrada, triangular y *super oscillator*), ruido, envolventes **AD** y **ADSR**, filtros (ladder, state variable, biquad y one-pole en `MetasoundBasicFilters`, más el filtro dinámico), **Delay con Feedback**, **Stereo Delay**, **Plate Reverb**, Flanger, Grain Delay, Bitcrusher, Ring Mod, Wave Shaper, **MIDI To Frequency**, **MIDI Note Quantizer**, **Scale to Note Array**, **Trigger Repeat**, **Trigger Counter**, Sample & Hold y LFO de ruido. **No hay chorus** (el flanger lo puede reemplazar).

### Una voz de "pluck" (la cuerda), tres caminos
| Camino | Cómo | Pro | Contra |
|---|---|---|---|
| **A. Samples + MetaSound** | El sample de cada esfera entra a un Wave Player → filtro → salida; la velocity mueve el volumen y el corte | Lo más rápido; conserva el timbre que ya existe | Menos expresivo que sintetizar |
| **B. Sustractivo** | Sierra o triangular × ADSR corto → ladder filter con el corte subiendo por velocity y envolvente | El pluck clásico de sinte, muy controlable | Suena "sinte", no cuerda |
| **C. Karplus-Strong aproximado** | Ráfaga de ruido de 5-10 ms → Delay con tiempo = 1/frecuencia y feedback alto (0,98-0,995) → filtro después | Suena a cuerda pulsada de verdad | MetaSounds no permite ciclos en el grafo: el filtro no puede ir dentro del lazo, así que el brillo se apaga con una envolvente afuera. Aproximado, hay que probarlo de oído |

**Entradas de la voz:** `Play` (trigger), `Note` (MIDI en float), `Velocity` (0-1), `Brightness`, `Decay`. Desde el Blueprint: `Set Float Parameter` + `Execute Trigger Parameter`, junto con la háptica y la vibración de la cuerda.

**Polifonía:** un AudioComponent por cuerda (8 a 12, lo más simple), o un grupo de N componentes que rota.
**Efectos:** 🔴 **una sola vez**, en un submix de música (reverb y delay), **no por voz**: en el Quest, una reverb por voz multiplica el costo de CPU por la cantidad de cuerdas. Lo que el cuerpo mueve (filtro, cantidad de delay) va como parámetro.

## 4. El arpegiador

**Dentro de un MetaSound es poco trabajo.** Epic publica un tutorial que es casi esto: [Creating Procedural Music with MetaSounds](https://dev.epicgames.com/documentation/unreal-engine/creating-procedural-music-with-metasounds).
```
reloj (Trigger Repeat, periodo = 60/BPM/subdivisión)
  → Trigger Counter (paso 0..N-1)
  → modo: arriba · abajo · ida y vuelta · al azar (aritmética del contador o Random Get)
  → Get (arreglo de notas) → MIDI To Frequency → la voz de pluck
```
- **El arreglo de notas se manda desde el Blueprint** (`SetIntArrayParameter` / arreglo de float): pueden ser las notas de los slots del gusano, un acorde o la escala de la sesión. Con `Scale to Note Array` en modo *Chord Tones Only*, siempre queda consonante.
- **Lo difícil es la sincronía, no el arpegio.** El gusano hoy lleva el paso desde el Blueprint (`StepBPM` 90 → `CalcStepDur`). Si el arpegiador tiene su propio reloj dentro del MetaSound, los dos se van a desfasar. Tiene que haber **un solo dueño del pulso**:
  - **Quartz** (el reloj del motor, preciso al sample) manda cada paso al gusano y al MetaSound; o
  - **el MetaSound es el reloj** y avisa cada paso al Blueprint con `WatchOutput`, y los visuales lo siguen.
  - En los dos casos el BPM sigue siendo una variable de autor o de la Partitura, no la duración de un sonido.
- **Harmonix no sirve acá:** busqué en el código de 5.8 y **no tiene nodo de arpegiador**. Además el plugin sigue siendo **Experimental** y está apagado por defecto.

## 5. Quest: los dos riesgos reales

### 🔴 Latencia: hoy el APK tarda en sonar
Los ajustes de audio del proyecto están bajo `[/Script/WindowsTargetPlatform.WindowsTargetSettings]` en `VR_Test/Config/DefaultEngine.ini`, **no en la sección de Android**. La skill ya lo había detectado el 07-17 y sigue igual. Entonces el APK usa los valores por defecto de Android, verificados en `AndroidRuntimeSettings.cpp:34-36`:
- **44.100 Hz** (el Quest es nativo a 48.000: se remuestrea);
- **1024 frames por buffer** (23 ms) × **4 buffers** en cola: **hasta ~90 ms** entre el gesto y el sonido. Es una estimación, no está medida.
- Para un arpa que se siente sensible hay que bajar de ~30-40 ms. El camino: mover el bloque a la sección de Android, 48.000 Hz, y un buffer chico en múltiplos de 192 (el tamaño nativo del Quest), por ejemplo 384. Después hay que medir los cortes de audio (underruns).
- ⚠ `Config/` es compartido: **hay que coordinarlo antes de tocarlo** (CLAUDE.md §7).

### CPU: nadie publica cuánto aguanta
Ni Epic ni Meta publican un presupuesto de MetaSounds en el Quest. **Lo primero que hay que hacer es un APK de estrés** (12 voces de pluck + reverb + delay en el submix) y medirlo con Audio Insights y `au.LogRenderTimes`. La palanca que hay si falta CPU: `au.MetaSound.BlockRate` se puede bajar solo en Android.

## 6. Fab y recursos

Revisado **en Fab, con la sesión de Beltrán en Chrome**, el 2026-10-27. Los precios están en **pesos chilenos** (así los muestra Fab). Regla para el Quest: un **paquete de MetaSounds** (contenido, solo nodos nativos) corre en Android aunque no lo liste. Un **plugin de código** corre en el Quest solo si lista Android.

**Ninguno trae un arpa, un pluck ni un arpegiador listos.** Sirven para estudiar cómo se arman y para partir de algo.

| Recurso | Tipo · UE · plataformas | Precio | Para nosotros |
|---|---|---|---|
| **Metasounds Game Example Pack** | paquete · 5.3-5.7 · lista Android | **gratis** | 🟢 **El primero que hay que bajar**: canciones procedurales y efectos 100 % sintetizados para usar, modificar y aprender |
| **MetaVolts Music Maker** (Shape Noise) | paquete · 5.0-5.6 · lista Android | $11.766 | 🟢 El más cercano en estética: música **ambiental de sinte** 100 % en MetaSounds, 20 módulos pensados como sinte modular. Es una versión temprana. ⚠ No lista 5.7 ni 5.8: probar que cargue |
| **Granular Toolkit (MetaSounds)** | paquete · 5.6-5.7 · Win/Mac (es solo nodos nativos, así que corre en Android) | **gratis** | 🟡 Síntesis granular sobre nuestros samples: texturas y pads. Medir CPU en el Quest |
| **Procedural SFX & Music Plugin** (Le Binh Son) | plugin C++ · 5.2-5.8 · **lista Android** | $47.100 | 🟡 Agrega nodos de síntesis por modelado físico. El único instrumento es un **piano**; el resto son efectos. Tiene demos jugables para Windows: probarlas antes de comprar |
| **MetaSound Templates** | proyecto completo · 5.1-5.8 · Windows | $29.433 | 🟡 Patches modulares para efectos y música procedural. Para estudiar |
| **TechAudioTools Content** (Epic) | plugin de editor · solo 5.7 · Win/Mac | gratis | ⚪ Herramientas de editor; no va al APK. ⚠ Lista solo 5.7 |
| **Expose MetaSound Parameters To Blueprint** | plugin · 5.1-5.8 · solo Windows | $15.299-36.500 | 🔴 No hace falta: el motor ya lo hace (`Set Float Parameter`, Parameter Packs). Y no lista Android |
| **HyperFocus: Metasound Nodes** | plugin · 5.7-5.8 · solo Windows · etiqueta *Experimental* | gratis-$24.722 | 🔴 Casi sin descripción y no lista Android |
| **Metasound Presets & Patches Pack** (Demute) | paquete · 5.5-5.7 | gratis | ⚪ Presets de efectos, no de música. El propio listing avisa que la versión de Fab tiene problemas de enlace |
| **Free Modular Magic SFX** | paquete · 5.6-5.8 | gratis | 🔴 Efectos de magia que **necesitan el plugin pago** para sonar |
| **Tutorial gratis de Matt Spendlove** | serie sobre MetaSounds y síntesis sustractiva (reseña en cdm.link) | gratis | 🟢 El curso para aprender a armar la voz |

De paso, sin revisar: **Procedural Heartbeat** (latido procedural en MetaSounds) podría servir para Recognizing.

## 7. Qué tan difícil es

Las horas son una estimación gruesa de prototipo en PC. El diseño sonoro se itera de oído con Beltrán, y eso no tiene horas fijas.

| Pieza | Dificultad | Prototipo | Riesgo |
|---|---|---|---|
| Voz de pluck con velocity → volumen y brillo | baja-media | 0,5-1 día | el timbre: se ajusta escuchando |
| Efectos (reverb y delay en submix, filtro por gesto) | baja | horas | CPU en el Quest |
| Arpa tocable (cuerdas, barrido por segmento, velocidad, háptica, vibración) | media | 1-2 días | sentirla en el visor |
| Arpegiador | baja en el MetaSound · media para sincronizarlo con el gusano y los visuales | 0,5-1 día | dos relojes |
| Latencia y CPU en el Quest | — | medio día de APK de estrés | 🔴 **el riesgo real: medir primero** |

⚠ **Sin confirmar:** si el MCP de Unreal puede editar grafos de MetaSound. Existe la *MetaSound Builder API* (Beta, solo en editor) para armarlos por script. Si no, el grafo se arma a mano en el editor de MetaSound, que es visual como un Blueprint y deja escuchar mientras se mueven las perillas. Eso calza con cómo trabaja Beltrán.

## 8. Orden sugerido (cuando se decida tocar Unreal)
1. **Medir antes de diseñar:** el APK de estrés (CPU) y la prueba de latencia (sección de Android en `Config/`, coordinado).
2. Una voz de pluck en un MetaSound, con perillas expuestas, en `Test_Sequencer`, para elegir el timbre de oído (caminos A, B o C del §3).
3. Decidir quién es el dueño del pulso (Quartz o el MetaSound) y recién ahí el arpegiador.
4. El arpa tocable, si entra en el diseño de la etapa.

## 9. ¿Lo construye Claude directamente? (documentación oficial + lo que permite el MCP)

### Lo que dice la documentación oficial (lo que importa para decidir)
- **Source, Patch y Preset.** Solo una *Source* suena sola. Un *Patch* es un grafo reutilizable dentro de otros, así que la voz de cuerda puede ser un Patch instanciado N veces dentro de una Source. Un *Preset* hereda el grafo y solo cambia los valores por defecto. ([Reference Guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-reference-guide-in-unreal-engine))
- **La interfaz `UE.Source.OneShot`** agrega *On Finished*; si nunca se dispara, el sonido no termina. Para un instrumento continuo o música se saca (así lo hace el tutorial de música).
- **Pines de constructor** (rombo): valores que se fijan antes de sonar y ahorran CPU. No pueden ser Trigger ni Audio.
- **Probar en el editor:** Play en la barra, botón para disparar los Trigger y perillas (dial) en los inputs Float **mientras suena**. Beltrán puede afinar el timbre de oído sin compilar nada. ([Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-quick-start))
- **Desde el Blueprint:** `Set Float Parameter` y `Execute Trigger Parameter` (con el nombre del input). Hacia el Blueprint: **Watch Output** (Float, Int32, Bool, Time, String, Trigger), que sirve para avisar el pulso a los visuales.
- **Tiempos:** los Trigger que salen de nodos de tiempo son precisos al sample; el resto corre a *block rate*.
- **Polifonía: la documentación no la menciona.** Hay que armarla: varias voces (Patch × N dentro de una Source, o varios AudioComponents).
- **Android y Quest: ni una línea.** Sin presupuesto de CPU ni notas de plataforma, como ya decía `audio-quest.md`. Se mide.
- **El tutorial de música procedural de Epic es monofónico** y es casi nuestro arpegiador: `Trigger Repeat` ← `BPM To Seconds` → `Trigger Counter` → `Random Get` ← `Scale to Note Array` → `Add` (+48) → `MIDI To Frequency` → `Sine`/`Saw` → `Crossfade` → `Ladder Filter` (corte por LFO) × `AD Envelope` → `Delay` → `Stereo Delay` (ping-pong). Expone BPM, Scale, NewMelody, Detune y Crossfade. ([tutorial](https://dev.epicgames.com/documentation/unreal-engine/creating-procedural-music-with-metasounds))
- **Builder API** (para armar MetaSounds por código): **Beta**. Se usa desde Blueprint y C++: `Create Source Builder` → `Add Node By Class Name` → `Connect Nodes` → `Build To Asset` (Editor Subsystem, solo en editor). No maneja variables. *Live Updates* está en beta desde 5.5. Los handles no se deben guardar. ([Builder API](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasound-builder-api-in-unreal-engine))

### Lo que permite el MCP (verificado hoy)
- **No hay toolset de MetaSounds**, ni siquiera después de que Beltrán activara `AllToolsets` y `TechAudioTools` (`list_toolsets`, 2026-10-27, con el editor reiniciado: aparecieron 30+ toolsets, ninguno de audio).
  - **`TechAudioTools`** (Experimental, Epic) son *view models* MVVM para armar paneles de editor que leen y editan los **inputs y la metadata** de un MetaSound. **No arma grafos.** Sirve para un panel de perillas a medida, no para construir la voz. ⚠ Dos de sus módulos son de tipo Runtime: vigilar que el próximo empaquetado para Android no se queje.
  - **`ConfigSettingsToolset`** sirve para el arreglo de latencia del §5.
  - **`SlateInspectorToolset`** maneja la interfaz del editor como Playwright (capturas, clics, teclas). En teoría podría armar el grafo a mano dentro del editor de MetaSound, pero es frágil: queda como último recurso.
- 🔴 **El Python del MCP no tiene el módulo `unreal`** (gotcha 441): la Builder API **no se puede llamar por script**.
- ✅ **Sí se puede llamar desde un Blueprint:** `MetasoundBuilderBase.h` tiene 81 funciones `BlueprintCallable` (`AddNodeByClassName`, `AddGraphInputNode`, `ConnectNodes`, `SetNodeInputDefault`, …), y yo armo Blueprints por el DSL. Haría falta un **Blueprint generador** que se corre una vez (en PIE) y guarda el asset.
- ✅ **Los nombres exactos de los nodos están en el código del motor**, por ejemplo `{UE, "Ladder Filter", Audio}` en `MetasoundBasicFilters.cpp:165`.
- ✅ **Existe el nodo `Wave Writer`**: el grafo puede grabar su salida a un `.wav` en disco. Con eso puedo **verificar sin oído** que suena, que la altura es la pedida, la envolvente y que no satura. Que suene **lindo** lo decide Beltrán.

### Veredicto
| Pieza | Quién y cómo | Por qué |
|---|---|---|
| **El grafo de la voz** (~20 nodos) | **Recomendado: a mano en el editor de MetaSound**, con la receta nodo por nodo que escribo yo (~1 h). Alternativa: un Blueprint generador mío (0,5-1 día, API en Beta) | El generador sería **más grande que el grafo que genera**. El timbre se decide escuchando y moviendo perillas, y eso solo se hace en el editor |
| **Todo lo demás:** cuerdas, barrido, velocidad, háptica, vibración, grupo de voces, arpegiador en Blueprint con Quartz, sincronía con el gusano, arreglo de latencia y APK de estrés | **Yo, directo** | Es Blueprint, config y medición: lo que el MCP hace bien. Si el arpegiador vive en el Blueprint (Quartz dispara la voz) y no dentro del MetaSound, el grafo queda mínimo y el pulso tiene un solo dueño |
| **Verificación objetiva** | Yo, con `Wave Writer` → `.wav` → análisis local | Control positivo antes de pedirle el oído a Beltrán |

## 10. Construido el mismo día: `BP_Harp_SC` (2026-10-27)
Beltrán aclaró el pedido: **un arpa que se toque con las manos**, con cuerdas que vibran y suenan, un par de efectos, háptica, las dos manos, polifónica y **estética elegante de Soul Charger** (nada de neón). Se construyó entero por MCP, sin hacer el grafo a mano:
- **El sinte lo arma el Blueprint en memoria**, con la Builder API. La receta de la voz está en arreglos de datos, así que el timbre se cambia sin tocar grafos. La voz es una cuerda pulsada Karplus-Strong (ruido → envolvente → filtro → delay con realimentación) y hay una por cuerda. Al final van Stereo Delay, Plate Reverb y limitadores.
- **Verificado sin visor:** se arma con `fails=0`, la mano de prueba detecta los toques en orden, y un `.wav` grabado con Wave Writer confirma que suena afinado (0 a ±2 cents en las cuerdas medidas limpias).
- **Ficha completa:** [`blueprints/BP_Harp_SC.md`](../../.claude/skills/unreal-vr/blueprints/BP_Harp_SC.md). Nivel: `/Game/SoulCharger/Mechanics/Harp/Maps/Test_Harp`.
- Con eso, el veredicto del §9 cambia: la Builder API desde Blueprint **sí** permite que Claude construya el sinte. El costo fue una biblioteca chica de funciones, más interpretar la receta como datos.

## Fuentes
- [Blog de Meta: Virtuoso (Crafoord, Really Interactive)](https://www.meta.com/blog/virtuoso-will-allow-anyone-to-create-their-own-music-in-vr-on-march-10/) · [Virtuoso como caja de arena musical](https://www.meta.com/blog/virtuoso-is-a-musical-sandbox-that-rethinks-music-for-vr-out-now-on-the-quest-platform/) · [MIXED: en Virtuoso aprendes instrumentos de VR](https://mixed-news.com/en/meta-quest-2-steamvr-in-virtuoso-you-learn-vr-instruments/) · [UploadVR](https://uploadvr.com/virtuoso-vr-tool-music-makers/) · [Fast Travel Games](https://fasttravelgames.com/games/virtuoso)
- [Plugin Harmonix (Epic)](https://dev.epicgames.com/documentation/en-us/unreal-engine/harmonix-plugin-in-unreal-engine) · [Creating Procedural Music with MetaSounds](https://dev.epicgames.com/documentation/unreal-engine/creating-procedural-music-with-metasounds)
- [Karplus-Strong explicado (demofox)](https://blog.demofox.org/2016/06/16/synthesizing-a-pluked-string-sound-with-the-karplus-strong-algorithm/)
- Fab: [Procedural SFX & Music Plugin](https://fab.com/listings/738ae468-a616-4051-ae03-853b53bc2de4) · [Free Modular Magic SFX](https://www.fab.com/listings/f0422e67-33d3-4c6e-b7a1-1059193960de) · [TechAudioTools Content](https://www.fab.com/listings/d44cbd49-7691-4f82-abdb-6428c78508f6) · [MetaVolts Music Maker](https://www.fab.com/listings/baad344c-43d0-40be-b2b3-90df382b378b) · [MidiEngine](https://www.unrealengine.com/marketplace/en-US/product/midi-engine-metasounds) · [MetaSound Templates](https://docs.unrealengine.com/marketplace/ko/product/metasound-templates) · [Tutorial de Matt Spendlove (cdm.link)](https://cdm.link/tag/procedural-audio/)
- Código de UE 5.8: `Plugins/Runtime/Metasound/Source/MetasoundStandardNodes/Private/` (lista de nodos; `MetasoundDelayNode.cpp:29` tiene Feedback) · `Plugins/Runtime/Harmonix/Harmonix.uplugin` (Experimental, sin arpegiador) · `Source/Runtime/Android/AndroidRuntimeSettings/Private/AndroidRuntimeSettings.cpp:34-36` (44.100 / 1024 / 4)
