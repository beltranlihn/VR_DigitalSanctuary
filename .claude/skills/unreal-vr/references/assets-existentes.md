# 🗺️ Inventario de lo que YA EXISTE y es reusable

> **Leé esto ANTES de construir cualquier interacción, efecto o sonido.** El `_INDEX.md` mapea los Blueprints; este archivo mapea **assets** (input, audio, VFX, materiales, accesores del pawn). Se creó el 2026-08-03 después de perder horas construyendo desde cero cosas que ya estaban resueltas y **probadas en visor** en otra parte del proyecto.
>
> **Mantenerlo vivo:** cuando descubras un asset reusable o valides algo en visor, agregalo acá.

## 🎮 Input — trigger sostenido (PROBADO EN VISOR)

**`IA_Continue` + `IMC_Continue`** (`Stages/Breath/Input/`) — el trigger que usan Breath, Heart y Calibration para avanzar páginas.
- `IA_Continue`: `ValueType=Boolean`, trigger **`InputTriggerDown`** → `Triggered` cada frame mientras se sostiene, `Completed` al soltar.
- `IMC_Continue`: 4 mapeos → `OculusTouch_{Left,Right}_Trigger_Click` **y** `_Trigger_Axis` (las dos variantes, click digital y eje analógico).

🔴 **La configuración del `AddMappingContext` importa MÁS que el asset.** Así lo agrega Breath (`BP_Instructions.InitRefs`) y **funciona**:
```
AddMappingContext(IMC, Priority = 1000,
                  bIgnoreAllPressedKeysUntilRelease = False,
                  bForceImmediately = True)
```
⚠ **Con los DEFAULTS no funciona**: `bIgnoreAllPressedKeysUntilRelease` viene en **True** y suprime el input hasta soltar y volver a apretar; `bForceImmediately` viene en False. Costó horas en Touch el 2026-08-03.

⚠ **`IMC_Default` e `IMC_Weapon_*` (XRFramework) tienen la lista de mapeos VACÍA** en este proyecto. `IA_Shoot_*`, `IA_Grab_*` etc. existen como assets pero **no están mapeadas a ninguna tecla**. No asumas que funcionan por venir del framework.

**Para un stage nuevo:** duplicar `IA_Continue`/`IMC_Continue` a `Stages/<Stage>/Input/` (así se hizo `IA_Attract_{Left,Right}` + `IMC_Touch`), y **copiar la config de arriba**.

## 🔊 Audio

| Dónde | Qué hay | Estado |
|---|---|---|
| `Calibration/Audio/` | 11 SoundWaves: `Pad` (68 s, **looping**, stereo), `Inhala`, `Exhala`, `Conteo`, `Trigger`, `Inicio`, `Termino`, `Tomado`, `Aparece`, `Aguanta1`, `Aguanta_2` | ✅ **probados en visor** |
| `Stages/Breath/Audio/` | `Inhale`, `Exhale`, `Umbral` | ✅ probados |
| `Stages/Touch/Audio/` | `MS_Synth`, `MS_Perc` — MetaSounds **procedurales** (sin dependencias externas) | ⚠ se llaman pero **no se comprobó que suenen** |
| `Stages/Touch/Ref/` | `BP_Sequencer`, `MS_Kick`, `MS_HiHats`, `M_ON`, `M_OFF` — migrados de terceros | 🔴 **4 referencias rotas**, riesgo de cook |
| `Recursos/Audio Calibration/` | 16 archivos fuente (`.wav` + proyecto de Ableton) | fuente, fuera de Content |

🔴 **Un `AudioComponent` reproduce SU propia propiedad `Sound`.** Tener el asset en una variable del BP **no alcanza** — hay que hacer `SetSound(componente, variable)`. Ver la regla "declarado ≠ aplicado" en `gotchas.md`.
⚠ En Quest, las fuentes espacializadas tienen que ser **mono** (`audio-quest.md`). `Pad` es stereo.

## ✨ VFX / Niagara

| Asset | Qué es | Cómo se maneja |
|---|---|---|
| `XRFramework/VFX/NS_MenuLaser` | **Pointer láser** del menú | `NiagaraSetVectorArrayValue` sobre **`User.PointArray`**: índice **0 = origen**, índice **1 = punta**. Duplicado a `Stages/Touch/VFX/NS_TouchBeam`. |
| `XRFramework/VFX/NS_TeleportTrace` / `NS_TeleportRing` | Arco y anillo de teleport | — |
| `XRFramework/VFX/NS_PlayAreaBounds` | Límites del área | — |
| `Stages/Breath/NS_BreathParticles` | Partículas de respiración | — |

⚠ **El pointer NO trae cursor de impacto.** `BP_Menu` lo resuelve con un `StaticMeshComponent` aparte (esfera + `XRFramework/Materials/M_VRCursor`). Si querés punta, va como componente.

## 🎨 Materiales reusables
- `XRFramework/Materials/M_VRCursor` — cursor del puntero.
- `Stages/Touch/Materials/M_TouchUnlit` — base **Unlit + Emissive** con parámetros `EmissiveColor` y `Brightness`; instancias `MI_Laser`, `MI_Bubble`, `MI_Slot`. Patrón correcto para Quest (ver `materials-vr.md`).
- `Stages/Movement/Materials/M_Brush_Light` — unlit + Fresnel, aditivo con borde suave (validado en visor dibujando).

## 🕹️ Pawn — accesores que ya existen (`BP_VRPawn_SC`)
`Class|BPVRPawnSC|GetMotionController{Left,Right}{Grip,Aim}` → devuelve el `MotionControllerComponent`. **Grip** = dónde está la mano · **Aim** = el rayo para punteros.

🔴 **NO pongas un `MotionControllerComponent` propio en un actor suelto del nivel**: solo consulta el tracking si su actor tiene *local net owner*, cosa que se cumple en el Pawn y no en un actor del nivel → `IsTracked()=false` y pose en cero, para siempre. **Leé el componente del pawn.** (Costó una tarde en Touch.)

## 💾 Persistencia
Patrón de SaveGame en `Calibration/` (`SG_CalibSession`). `bUseExternalFilesDir=True` ya está en `DefaultEngine.ini`.
⚠ El brief de Touch dice que `add_variable` por MCP no crea arrays — **es falso**: se crean pasando `container_type: "Array"`.
