# Audio en Quest 3 standalone — UE 5.8

> **[DOC]** oficial Epic/Meta · **[SRC]** código de UE 5.8 en `C:\Program Files\Epic Games\UE_5.8` · **[FOLCLORE]** sin fuente. Investigado 17/07/2026.
> **Contexto:** una etapa entera de la obra ES música (el visitante atrae elementos y compone una melodía que queda como su "firma sonora": key + banco de instrumentos de la sesión). Además: latido háptico+audio, drones ambientales, y audio que responde a un float 0–1 de respiración y a EEG por OSC.

---

# 🔴 BUG REAL EN EL CONFIG DEL PROYECTO — los ajustes de audio no se leen
`DefaultEngine.ini` — **verificado leyendo el archivo**:
```
55: [/Script/AndroidRuntimeSettings.AndroidRuntimeSettings]   ← el APK lee ACÁ
63: [/Script/WindowsTargetPlatform.WindowsTargetSettings]     ← y los audios están ACÁ ↓
71: AudioSampleRate=48000
72: AudioCallbackBufferFrameSize=1024
73: AudioNumBuffersToEnqueue=1
74: AudioMaxChannels=0
75: AudioNumSourceWorkers=4
76: SpatializationPlugin=
```
**Todos los ajustes de audio están bajo `WindowsTargetSettings`. En un APK Android NUNCA se leen.**
> [SRC] `AndroidRuntimeSettings.h:608-640` declara propiedades **con el mismo nombre pero en otra clase**: `AudioSampleRate`, `AudioCallbackBufferFrameSize`, `AudioNumBuffersToEnqueue`, `AudioMaxChannels`, `AudioNumSourceWorkers`, `SpatializationPlugin`, `ReverbPlugin`, `OcclusionPlugin`.
`Config/Android/AndroidEngine.ini` **no tiene ningún ajuste de audio** (verificado).

**FIX:** mover el bloque a `[/Script/AndroidRuntimeSettings.AndroidRuntimeSettings]`, o setearlo en Project Settings → Platforms → **Android** → Audio.

**Y dos valores están mal igual, una vez que se lean:**
- `AudioNumBuffersToEnqueue=1` → [SRC] `AudioMixerPlatformAndroid.cpp:226` `NumBuffers = FMath::Max(OpenStreamParams.NumBuffers, 4);` **el backend lo clampea a 4.** La UI también: [SRC] `AndroidRuntimeSettings.h:615` `ClampMin="2"`. **El 1 es inalcanzable por dos vías.**
- `AudioMaxChannels=0` → 🔴 **la doc de Epic MIENTE.** [DOC Android Settings] dice *"If this is set to 0, Unreal Engine will use all the channels available"*. [SRC] `AudioMixerTypes.h:85` `MaxChannels(0) // This needs to be 0 to indicate it's not overridden`; `AudioMixerDevice.cpp:2109` resuelve `(Settings.MaxChannels > 0) ? Settings.MaxChannels : DefaultMaxChannels` con [SRC] `AudioSettings.h:93` default **`MaxChannels(32)`**. → **0 significa "usá el global (32 voces)", NO ilimitado.** Setearlo explícito.

---

# 🔴 MetaSounds: Production Ready, y la ruta correcta para la etapa de música
> [DOC] "**MetaSounds** are now **Production Ready** in 5.4." — [UE 5.4 release notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5.4-release-notes?application_version=5.4)
> [SRC] `Metasound.uplugin`: `"EnabledByDefault": true, "IsBetaVersion": false`.
⚠ **La [Quick Start de 5.8](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-quick-start) SIGUE mostrando "Learn to use this Beta feature" — es metadata podrida.** Confiar en los flags del plugin y en las release notes.
⚠ **Todo consejo que recomiende Sound Cue es de UE4.** > [DOC] "MetaSounds … serve as a **replacement** for Unreal Engine's default audio objects".

**Epic publica un tutorial que ES casi nuestra etapa:** [Creating Procedural Music with MetaSounds](https://dev.epicgames.com/documentation/unreal-engine/creating-procedural-music-with-metasounds) — *"Build the Melody Generation section to produce a random melody in a specified scale."* Esqueleto: BPM To Seconds → Trigger Repeat → Trigger Counter → Random Get → **Scale to Note Array** → **MIDI To Frequency** → AD Envelope → Ladder Filter → Stereo Delay.

## 🔴 Nadie ha documentado MetaSounds en Android/Quest. Ni Epic ni Meta.
Ni lista de plataformas, ni limitaciones, ni números de CPU. **El silencio ES el hallazgo.** Pero:
> [SRC] `Metasound.uplugin` **no tiene `PlatformAllowList`/`PlatformDenyList`** en ningún módulo → **compila para Android**. (Comparar con Resonance, que SÍ lista plataformas explícitamente → la ausencia acá es significativa, no un descuido.)
**El presupuesto de voces hay que medirlo en dispositivo. Ningún documento lo va a dar.**

## Las 30 escalas ya están en el motor — es nuestra "firma sonora" hecha
> [SRC] `SignalProcessing/Public/DSP/MidiNoteQuantizer.h:13-62` `enum Scale`: Major · Minor_Dorian · Phrygian · Lydian · Dominant7th_Mixolydian · NaturalMinor_Aeolian · HalfDiminished_Locrian · Chromatic · WholeTone · DiminishedWholeTone · MajorPentatonic · MinorPentatonic · Blues · Bebop_Major · Bebop_Minor · Bebop_Dominant · HarmonicMajor · HarmonicMinor · MelodicMinor · LydianAugmented · LydianDominant · Augmented · Diminished · Spanish_or_Jewish · Hindu … (default Major).

**Nodos clave** [SRC]:
- **MIDI Note Quantizer** (`MetasoundMidiNoteQuantizerNode.cpp:125`): entradas `Note In`, `Root Note` ("0.0 = C, 1.0 = Db/C#…"), `Scale Degrees`, `Scale Range In`, `Note Out`.
- **Scale to Note Array** (`MetasoundMidiScaleToArrayNode.cpp:71`) — tiene un pin que la doc no menciona: **`Chord Tones Only`** = *"will only return a subset of the scale represeting chord tones (i.e. scale degrees 1,3,5,7)"*. → **Con eso, todo lo que el visitante "atraiga" cae consonante siempre.**
- **Trigger Repeat** (`:29-33`): `Start`, `Stop`, `Period`, `Num Repeats` ("0 = repite indefinidamente"), `RepeatOut`.
- **16 nodos de trigger**: TriggerAccumulator, Any, **Coin** (ornamentación probabilística), Compare, Control, Counter, Delay, **OnThreshold** (← el puente respiración→evento), OnValueChange, Once, Pipe, Repeat, Route, Select, Sequence, Toggle.
- **Wave Player** (`MetasoundWavePlayerNode.cpp:26-46`): **`On Nearly Finished`** = *"Allows time for logic to trigger different variations to play seamlessly"* → así se encadenan los drones sin corte. Además `Loop Start`/`Loop Duration`, `Playback Location` (0-1), `Maintain Audio Sync`.
- Categorías registradas [SRC] `MetasoundStandardNodesCategories.cpp:20-31`: Music, Trigger, RandomUtils, Envelopes, Generators, **Spatialization**, Filters, **Reverbs**, WaveTables, Mix, Math, Delays, Dynamics, Io, Debug.

## 🔴 La restricción de diseño: la firma sonora tiene que ser DATOS, no un asset
> [DOC] [Builder API](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasound-builder-api-in-unreal-engine) (**Beta**): *"Due to requiring the MetaSound Editor Subsystem, you can only modify **serialized MetaSound assets in editor builds**."*
**→ NO se puede hornear un MetaSound nuevo en el dispositivo.** Un solo grafo parametrizado + datos. **La "firma sonora" se guarda como `key int + scale enum + bank index + array de notas`, y se reproduce por un grafo fijo.** Diseñarlo así desde ahora.

## MIDI = Harmonix = Experimental hace 2 años → SALTAR
> [SRC] `Harmonix.uplugin`: `"IsExperimentalVersion": true, "EnabledByDefault": false`. Depende de `MusicEnvironment`, que también es Beta+Experimental.
40 nodos (MidiPlayer, StepSequencePlayer, FusionSampler, MidiQuantizeTrigger…), compila para Android, pero es una cadena Experimental doble. **Nuestra melodía se GENERA de la interacción, no se importa de un .mid → no lo necesitamos.**

## `au.MetaSound.BlockRate` — la palanca que no está documentada
> [SRC] `MetasoundAssetBase.cpp:146` `"Sets block rate (blocks per second) of MetaSounds. Default: 100.0f, Min: 1.0f, Max: 1000.0f"`
> [SRC] `MetasoundSettings.h:148` es un **`FPerPlatformFloat`** → **se puede bajar SOLO en Android sin tocar escritorio.**
**Bajar a 50 Hz = ~2x menos trabajo de nodos a control rate, gratis, para una obra meditativa.**

---

# Manejar MetaSounds desde Blueprint
> [DOC] El caso "float por frame" **es el ejemplo publicado**: la [Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-quick-start) maneja velocidad del pawn → `Map Range Clamped` → **`Set Float Parameter`** llamado `"PawnSpeed"`, continuamente.
> [SRC] `AudioParameterControllerInterface.h:64` `UFUNCTION(BlueprintCallable, DisplayName="Set Float Parameter")`. Hermanos `:53-61`: `SetIntParameter`, **`SetBoolArrayParameter`, `SetIntArrayParameter`** → **los arrays se setean desde BP** = así se empuja la melodía entera de una.

**¿Setear la respiración cada frame? Sí, es seguro y es el patrón documentado.** Y hay razón: [SRC] el block rate default es **100 Hz** y Quest corre a 72–90 → **estamos por debajo del block rate**; el grafo no puede consumir más rápido de lo que tickea. Más rápido que Tick es trabajo descartado.
⚠ **Epic no publica ningún costo por frame de setear parámetros.** Ni advertencia ni bendición.

**Dos cosas que vale usar:**
- **Parameter Packs** ([DOC](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/MetaSoundParameterPack)) si mandamos varios params por frame (respiración + EEG + latido): los batchea, y *"if the AudioComponent is virtualized the parameter pack will be **sent again** when/if the AudioComponent is 'unvirtualized'"* → robustez real en 15 min.
- 🔴 **`WatchOutput`** [SRC] `MetasoundOutputSubsystem.h:35` `UFUNCTION(BlueprintCallable) bool WatchOutput(UAudioComponent*, FName OutputName, ...)` — *"Provides access to a playing Metasound generator's outputs"*. **Es el puente música→visuales**: que el grafo sea dueño del beat y **empuje eventos hacia Blueprint**, en vez de que Blueprint adivine el timing. Apenas documentado.

**Constructor pins**: [DOC] *"read-only values which can improve the performance … by not dynamically updating at runtime"* → set-before-play. **Usar para el banco de instrumentos de la sesión. NO para la respiración.**

---

# 🔴 Quartz — la columna vertebral de la etapa de música
> [DOC] "Quartz is a **Blueprint-exposed** scheduling system that solves timing issues between the game, audio logic, and audio rendering threads to provide **sample-accurate** audio playback." — [Overview of Quartz](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-quartz-in-unreal-engine)
> BP API: Create New Clock · **Play Quantized** · Subscribe to Quantization Event · Get Handle for Clock.

**¿Corre en Quest? Las docs NO lo dicen. El código sí:**
> [SRC] **Quartz NO es un plugin** — vive en el motor core: `Runtime/AudioMixer/Public/Quartz/` (`QuartzSubsystem.h`, `QuartzMetronome.h`, `AudioMixerClock.h`) + `Engine/Classes/Sound/QuartzQuantizationUtilities.h`. **Sin descriptor de plugin → sin gating de plataforma → está en Android por construcción.**

> [SRC] `QuartzQuantizationUtilities.h:45-74` `enum class EQuartzCommandQuantization`: Bar · Beat · 1/32 · 1/16 · 1/8 · 1/4 · Half · Whole · las punteadas · los tresillos · Tick · **None** ("Execute as soon as possible").

**Por qué importa para la obra:** cuando el visitante "atrae" un elemento musical, **no queremos que suene en el instante en que lo agarra — queremos que caiga EN EL BEAT.** `Play Quantized` con boundary `Beat` o `1/8` es exactamente eso, y **es la diferencia entre ruido y música.**
⚠ Hay **dos relojes musicales** en 5.8: Quartz (producción, core) y el Music Clock de Harmonix (Experimental, plugin). **Epic no publica guía de cuál elegir. Para nosotros: Quartz.**

---

# 🔴 Audio espacial: la mala noticia
> [DOC Meta] Meta XR Audio SDK **v85.0, "Unreal Engine: 5.6"** · *"no further updates are planned"* · *"cannot guarantee compatibility with future versions"*. — [downloads](https://developers.meta.com/horizon/downloads/package/meta-xr-audio-unreal/85.0/?view=full_width)
**Estamos en 5.8. NO hay spatializer de Meta soportado para nosotros.**
> [DOC Meta] El viejo Oculus Spatializer *"has been replaced … and is now in **end-of-life** stage. We strongly discourage its use."* ⚠ **Todo tutorial que diga "activá Oculus Audio" está muerto.**
> [SRC] Verificado: **ningún .uplugin de Meta/Oculus/OVR viene en UE 5.8**. Y `VR_Test.uproject` no usa el Meta XR plugin (usa OpenXR, OpenXREyeTracker, OpenXRHandTracking, PICOController, OSC).

**Qué tenemos:**
- 🔴 **NO hay HRTF built-in.** [DOC] *"Binaural … uses **whatever binaural plugin you have enabled**"* → **poner attenuation en "Binaural" sin plugin es un no-op.** Trampa real.
- **Resonance Audio** viene en el motor y **sí permite Android**: [SRC] `ResonanceAudio.uplugin` `"EnabledByDefault": true, "IsBetaVersion": true`, runtime `"PlatformAllowList": ["Android","IOS","Linux","Mac","Win64"]`. Es de Google, es Beta, Google lo archivó — pero está y funciona.
- 🔴 **`ITD Panner` — el hallazgo que la doc niega.** [SRC] `MetasoundITDPannerNode.cpp:269` `DisplayName = "ITD Panner"`, *"Pans an input audio signal using an inter-aural time delay method."* Entradas `:27-32`: `Angle` ("90 degrees is in front, 0 is to the right, 270 is behind"), `Distance Factor`, `Head Width` ("in centimeters"), `Out Left`/`Out Right`.
  → **Es un panner binaural real DENTRO del grafo de MetaSound, sin plugin, que cuesta una línea de delay.** Para una obra sentada donde los elementos musicales orbitan al oyente, **puede ser toda la espacialización que necesitamos** — y esquiva el problema de versión del SDK de Meta entero.

**Recomendación:** `SpatializationPlugin` **vacío** (paneo default) + **ITD Panner en el grafo** para lo que deba sentirse posicionado. Resonance (Beta) solo si hace falta HRTF de verdad en drones. **No construir sobre el Meta XR Audio SDK en 5.8.**

## ⚠ Dos trampas de espacialización
> [DOC Meta] *"Due to Unreal's plugin setup, audio files with **more than one channel, such as stereo, do not get processed by the spatializer plugin**."* → **las fuentes espacializadas TIENEN que ser mono.** El MetaSound debe sacar mono ([SRC] `Out Mono` en Wave Player) y dejar que el panner la ubique.
> [DOC Meta] *"only use the Meta XR Audio SDK distance attenuation **or** the audio engine's distance attenuation and disable the other"* → **elegir UNA autoridad de atenuación.**

## `Non-Spatialized Radius` — el ajuste crítico de VR
> [DOC] *"defines the distance threshold below which the sound will **start to transition from being spatialized to non-spatialized** (becoming a 2D sound)"* — [Sound Attenuation](https://dev.epicgames.com/documentation/unreal-engine/sound-attenuation-in-unreal-engine?lang=en-US)
**Sin esto, una fuente cerca de la cabeza salta violentamente por el campo estéreo al girar.** Para una obra donde los elementos se atraen HACIA el usuario, **no es opcional.**

---

# Performance de audio
🔴 **Ni Epic ni Meta publican NINGÚN presupuesto de audio para Quest en Unreal.** Sin voces máximas, sin CPU, sin nada. (El profiler de audio de Meta: *"Analytics are only available for Unity, Wwise, FMOD, and Native OSP"* — **no Unreal**.) **Todo "valor recomendado de audio para Quest" que circule es FOLCLORE.**

**Los números que SÍ gobiernan el build** [SRC]:
- **Salida siempre estéreo, siempre Int16**: `AudioMixerPlatformAndroid.cpp:196` `OutInfo.NumChannels = 2; // Android doesn't support surround sound`.
- 🔴 **El backend es OpenSL ES, NO AAudio**: `:16` `#include <SLES/OpenSLES.h>`; `:289` `OpenSLBufferQueueCallback`. → **El consejo de Meta de usar `AAUDIO_PERFORMANCE_MODE_LOW_LATENCY` es para apps nativas y NO APLICA a UE.** Trampa cruzada entre docs.
- **El buffer se redondea**: `:96-113` `while (BufferSizeToUse < RenderCallbackSize) BufferSizeToUse += MinFramesPerBuffer;` → **pedir 1024 no garantiza 1024**; se sube al siguiente múltiplo del frames-per-buffer nativo del device.
- `AudioNumSourceWorkers=4` [SRC] `AudioMixerTypes.h:76` *"The number of workers to use to compute source audio"*. **En un SoC de 6 cores compartido con el render thread, 4 es agresivo para una obra sentada. Medir 2 vs 4.**
- [DOC Meta] hardware: 48000 Hz, buffer de 192 samples ([Horizon OS Audio](https://developers.meta.com/horizon/documentation/android-apps/platform-audio/)). **48000 está bien, mantenerlo.**
- 🔴 [DOC Meta] **Masterizar a −16 LUFS** — [Loudness Meter](https://developers.meta.com/horizon/documentation/unity/audio-loudness-meter-overview/).

**Medir con:** **Audio Insights** (Production Ready en 5.8, *"enabled by default"*) · `au.LogRenderTimes` · `au.Debug.AudioMemReport` · `au.DumpActiveSounds`.

---

# Códecs en Android
> [SRC] `AudioMixerTypes.h:51-59` — comentario de Epic: `// Supported on all platforms:` **BINKA, ADPCM, PCM, OPUS, RADA**; y aparte `// Not yet supported on all platforms … NAME_OGG`.
> **→ Bink SÍ está soportado en Android.** Contradice el folclore de que es solo consolas.
> 🔴 [SRC] `Engine/Config/Android/AndroidEngine.ini:12` `[Audio] PlatformFormat=OGG` → **`PLATFORM_SPECIFIC` en Android = Vorbis**, y [DOC] Vorbis/PLATFORM_SPECIFIC *"does not currently support **seeking**"* → **rompe `Start Time` y loop points del Wave Player.**

| Codec | [DOC] | Para qué acá |
|---|---|---|
| **ADPCM** | "fixed-sized quality, ~4x compression, **relatively cheap to decode**" | 🎯 **latido, notas, one-shots del banco** — seekeable, y la etapa de música los va a machacar |
| **BINK_AUDIO** | "Perceptual-based codec … all features across all platforms", hasta 10:1, "Low memory usage" | 🎯 **drones largos** |
| PLATFORM_SPECIFIC (=OGG) | ❌ **no seekea**, y es el decode más caro | **evitar** |

⚠ **Ni Epic ni Meta recomiendan un codec para Android.** Ambos negativos verificados.
**Streaming** [DOC]: *"Ideally, sounds are always in memory by the time they play"* → los one-shots musicales **inline/in-memory** (un cache miss = una nota tarde, audible). Streamear solo los drones.

---

# Audio → háptico (la etapa del corazón)
> [SRC] `HapticFeedbackEffect_SoundWave.h` — la clase existe, **sin `UE_DEPRECATED`**. Y el comentario confirma lo del estéreo: *"If true on a vr controller the **left and right stereo channels would be applied to the left and right controller**, respectively."* (`bUseStereo`).

🔴 **PERO OpenXR no reproduce la forma de onda.** [SRC] `OpenXRInput.cpp:1482-1553` `SetHapticFeedbackValues()` arma **un solo `XrHapticVibration` por frame** (`duration = DeltaTime`, `frequency`, `amplitude`); el `HapticBuffer` solo se pasa a un **delegate de extension-plugin**, y **ningún plugin lo implementa en 5.8 stock**. `GetHapticFrequencyRange()` devuelve `XR_FREQUENCY_UNSPECIFIED`.
→ **En nuestro setup (OpenXR sin Meta XR plugin), `HapticFeedbackEffect_SoundWave` degrada a una envolvente de amplitud/frecuencia por frame (~72–90 Hz), no a háptica de waveform.**
→ **Para un latido eso está bien, incluso mejor**: un latido ES una envolvente de amplitud de baja frecuencia (tum-tum), que es exactamente lo que una envolvente a 72–90 Hz expresa bien. **No perdemos nada que necesitemos.**

**Recomendación:** manejar el mando desde nuestro propio reloj de latido en BP — **el mismo reloj Quartz que maneja la música** — llamando `Set Haptics by Value` junto al one-shot de audio. **Controlamos la fase exacta**, que es lo que importa para un latido sentido, y esquivamos tanto la limitación de OpenXR como el problema de versión del SDK de Meta.
⚠ Si algún día se agrega el Meta XR plugin: [DOC Meta] *"In UE5, sound waves used for haptics must have **`LoadingBehavior` set to 'Force Inline'**"* ← muerde en silencio. Y *"Quest 3/3S controllers support **hand-level haptics only**"*.

---

# Reverb / oclusión
> [SRC] Categoría **`Reverbs`** registrada; `MetasoundPlateReverbNode.cpp` viene en los standard nodes. También `MetasoundDiffuserNode`, `MetasoundStereoDelayNode`, `MetasoundGrainDelayNode`.
**Recomendación: un Plate Reverb DENTRO del grafo**, por voz o en un bus de música. Para una obra sentada sin sala que vender, es mucho más barato que la acústica de sala de un spatializer, no necesita plugin, y da el "espacio sonoro" que una obra de arte quiere.
**Saltar Audio Volumes y oclusión enteros** — un usuario sentado sin geometría entre él y la música no tiene nada que ocluir. `OcclusionPlugin` **vacío**.
⚠ [DOC] `GrainDelay`: *"Max Grain Count input is **CPU intensive**"* — tentador para arte, presupuestarlo con cuidado.

# Diseño de audio VR (Meta, agnóstico de motor y directamente útil)
> [DOC] "Loudness is the most obvious distance cue, but it can be **misleading**."
> [DOC] "The more listeners hear a **direct sound in comparison to the late reverberations**, the closer they will assume it is." → **el dry/wet del reverb ES el control de distancia.**
> [DOC] "**High frequencies attenuate faster** than low frequencies" → un lowpass por distancia vende profundidad barato.
> [DOC] 🔴 **"Head-locked audio should generally be avoided when possible."**
> [DOC] "Create soundscapes that are **neither too dense nor too sparse**." · "Use suitable volume levels comfortable for **long-term listening**." ← 15 min sentado.
> [DOC] "It is important to use **headphones** when performing spatialization" → ⚠ **los parlantes abiertos del Quest 3 NO son headphones. Mezclar con auriculares, verificar en los parlantes.**

# ✅ ACCIONES
1. 🔴 **Mover el bloque de audio** de `WindowsTargetSettings` a `AndroidRuntimeSettings`. Hoy es código muerto.
2. `AudioNumBuffersToEnqueue=4` (el 1 se clampea igual) · `AudioMaxChannels` **explícito** (0 ≠ ilimitado, significa 32) · medir `AudioNumSourceWorkers` 2 vs 4.
3. **No activar nada**: MetaSounds ya está on, **Quartz no necesita plugin**.
4. Prototipo de la etapa de música: **Quartz clock → `Play Quantized` → MetaSound con `Scale to Note Array` + `MIDI Note Quantizer` + `Trigger Repeat`**; respiración por `Set Float Parameter`; **beat→visuales por `WatchOutput`**.
5. **La firma sonora se persiste como DATOS** (key/scale/bank/notas), nunca como asset generado.
6. `au.MetaSound.BlockRate=50` en Android si el profiling lo pide (es `FPerPlatformFloat`).
7. Codecs: **ADPCM** para one-shots, **Bink** para drones. **Nunca PLATFORM_SPECIFIC** en algo que se seekee.
8. **Medir con Audio Insights en dispositivo.** Ningún documento va a dar el presupuesto.
