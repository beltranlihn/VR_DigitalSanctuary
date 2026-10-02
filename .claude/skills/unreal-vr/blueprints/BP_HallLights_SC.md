# BP_HallLights_SC — "se prende la luz del hall" (Hall/)

## Purpose
Pedido de Beltrán (2026-09-29): en la narrativa estamos **afuera del edificio y se ve todo negro**; en un momento **se ilumina como si se prendiera la luz del interior** y ahí aparece el portal. Este actor es ese interruptor, listo para que la narrativa lo llame.

## Status
🟢 **Compila y funciona en simulación** (medido: `Light` 0,486 → curva 0,479 → haz `Intensity` 0,1925 = 0,4 × 0,479 y `SourceGlowIntensity` 0,337 = 0,7 × 0,481). Capturas en editor con `Light` 0 / 0,5 / 1: afuera negro absoluto → marco + puerta a medias → encendido. ⬜ Visor.

## Cómo se usa (API)
- **`LightsOn`** / **`LightsOff`** (custom events): fijan el objetivo; el Tick funde en `FadeSeconds` con curva smoothstep.
- **`DoorColor`** en `MPC_Hall_SC` (vector): el color del vidrio visto desde ADENTRO. La narrativa lo lleva al color de la etapa a la que se sale (escribir la MPC directo con `SetVectorParameterValue` de colección).
- Instancia en `Test_Hall`: `BP_HallLights_SC_C_0`, con `Shaft` = el haz del óculo. **`AutoOnDelay` −1 desde el 2026-09-30** (antes 2: se prendía sola en el viaje del inicio; ahora la prende solo el director en el paso 4).

## Variables (cat. *Hall Lights*)
| Var | Default | Qué |
|---|---|---|
| `Light` ✎ | 1 | Nivel actual 0..1. En el EDITOR se previsualiza (el Construction Script escribe la MPC) |
| `FadeSeconds` ✎ | 3 | Duración del fundido |
| `bStartDark` ✎ | true | En BeginPlay arranca en 0 (negro) |
| `AutoOnDelay` ✎ | 2 | ≥0: se prende solo a los N s (para probar en PIE). **Poner −1 cuando lo maneje la narrativa** |
| `Shaft` ✎ | (ref) | `BP_LightShaft_SC` a escalar (opcional) |
| `Target` | — | Objetivo interno (0/1) |
| `BaseIntensity` / `BaseSourceGlow` | — | Valores autorados del haz, cacheados en BeginPlay (`CacheShaft`) |

## Grafos
- **UCS:** `PushMPC(smoothstep(clamp(Light)))` → preview en editor (NO toca el haz: en editor su base no está cacheada).
- **BeginPlay:** `CacheShaft` → `Target = Light = bStartDark ? 0 : 1` → `PushMPC` + `PushShaft` → si `AutoOnDelay ≥ 0`: `Delay` → `Target = 1`.
- **Tick:** si `Light ≠ Target`: `Light = FInterpToConstant(Light, Target, dt, 1/FadeSeconds)` → `s = smoothstep(Light)` → `PushMPC(s)` + `PushShaft(s)`.
  🔴 La curva lee la salida del nodo `SetLight`, NO el `FInterp` (un nodo puro se re-evalúa por consumidor: después del Set daba un paso doble — [[bind-del-dsl-no-es-asignacion]]). Arreglado por cirugía.
- **`PushMPC(S)`:** `MPC_Hall_SC.HallLight = S`, `FrameLight = S`.
- **`PushShaft(S)`:** `Shaft.Intensity = BaseIntensity·S`, `SourceGlowIntensity = BaseSourceGlow·S`, y llama a sus funciones `ApplyLook` + `ApplySourceGlow` (el haz no expone material: su UCS siempre crea el MID desde `M_LightShaft`, así que un override de material en la instancia se pierde).

## Qué responde a `MPC_Hall_SC`
`HallLight` × emisivo de: `M_Hall_Interior_SC`, `M_Hall_Tile_SC`, `M_Hall_Sky_SC`, `M_Hall_Glass_SC`, `M_HallDust_SC` (el polvo). `FrameLight` × `M_Hall_Exterior_SC` (la línea del marco). `DoorColor` → vidrio desde adentro.

## ⚠ Trampas
- Cambiar una variable de la instancia con `set_properties` **durante PIE** re-corre el Construction Script y resetea las no editables (`Base*` = 0) → el haz queda en 0. Es artefacto del instrumento; con `LightsOn`/`LightsOff` no pasa.
- En el editor el haz NO se apaga con `Light` = 0 (solo lo maneja el runtime): visto por la puerta parece que "sigue prendido".

## Relacionados
[[BP_LightShaft_SC]] · `blender-3d/assets/hall-portal.md` · `MPC_Hall_SC`
