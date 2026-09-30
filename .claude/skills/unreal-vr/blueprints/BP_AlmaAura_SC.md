# BP_AlmaAura_SC — el aura de Alma (Core/Alma/)

## Purpose
Pedido de Beltrán (2026-09-30 noche, vía Narrativa): *"envolver a Alma en una esfera de partículas con curl noise, muy pequeñitas y muy translúcidas, que también estén vivas cuando Alma habla; que se diferencie de la protoameba"*.
Actor SEPARADO (no un componente nuevo de BP_Alma_SC: gotchas 402/478), spawneado por `BP_Alma_SC.Boot → BootAura()` con `Owner = Alma` y pegado al `Body` con SnapToTarget ×3 → hereda escala, aparición y deriva.

## Status
🟢 PIE (Test_Heart, 2026-09-30): spawneada, padre = `Body`, `AlmaRef` resuelto, 0 Accessed None. ⬜ Look sin ver (el MCP no captura PIE) → visor. Material compilado sin errores.

## Assets
| Asset | Qué es |
|---|---|
| `SM_AlmaAura_SC` | 900 quads (3600 verts, UV0 esquina, UV1/UV2 semillas) en un cascarón de radio 66-90 del espacio del Body (Alma = radio 50). `scripts/gen_alma_aura.py` (Blender headless). Sin colisión. |
| `M_AlmaAura_SC` / `MI_AlmaAura_SC` | Unlit · AlphaComposite (premultiplicado) · dos caras · sin niebla de translúcidos · precisión Full. Todo en el VS (`scripts/hlsl/AuraVS.hlsl`, 22 entradas) + PS (`AuraPS.hlsl`). Armado con `apply_alma_aura_material.py` desde `plan_alma_aura.py`. Modelo numpy: `alma_aura_model.py`. |

## Cómo se mueve (VS)
Giro lento del cascarón alrededor de un eje que deriva, **diferencial por mota** (se cizalla, nunca rígido) → **curl noise** = rotor de un potencial de senos (sin divergencia, como humo), dos octavas en relación no entera → titileo lento → tamaño ANGULAR con piso (no centellea) → sprite hacia la cámara de cada ojo. `View.GameTime` + `AuraPhase` (la integra el BP: acelera sin saltos).

## Perillas (MI_AlmaAura_SC)
| Grupo | Perillas |
|---|---|
| 1 - Nube | `AuraAlpha` 0,35 · `SizeDeg` 0,16 · `SizeMinDeg` 0,10 · `SizeVar` 0,35 · `Twinkle` 0,45 · `ShellScale` 1 · `Breath` 0,03 · `ColA` (1, 0,94, 0,86) · `ColB` (1, 0,80, 0,62) · `AuraGlow` 1 |
| 2 - Curl | `CurlAmp` 5,5 · `CurlFreq` 1,6 · `FlowSpeed` 0,35 · `SwirlSpeed` 0,08 |
| 3 - Voz | `SpeakCurl` 0,6 · `SpeakExpand` 0,05 · `SpeakGlow` 0,6 |
| 9 - Interno | `AuraSpeak` · `AuraPhase` · `AuraReveal` (los escribe el BP) |
BP (`1 - Aura`): `AuraSpeakRate` 1,2 (cuánto acelera el flujo al hablar) · `bPreviewOnly` (una aura colocada a mano para mirar en el editor se destruye al dar Play).

## Grafos
- `BeginPlay`: `bPreviewOnly` → `DestroyActor`; si no, `CastToBP_Alma_SC(GetOwner)` → `AlmaRef`.
- `Tick` → `AuraDrive(DT)`: `IsValid AlmaRef` → `s = clamp(VOEnvSmooth·VOReact)` → `AuraPhase += min(DT,1/30)·s·AuraSpeakRate` → `SetScalarParameterValueOnMaterials(Aura)` `AuraSpeak` s / `AuraPhase` / `AuraReveal` = `AppearT`.
- **2026-10-01 (Narrativa)**: rama `Is Not Valid` de `AuraDrive` → `DestroyActor` (self). **El aura muere con su Alma.** Antes, las 5 Almas de ensayo (TestOnly) que la Obra destruye al arrancar dejaban 5 auras huérfanas en las celdas. Además, `BP_Obra_SC.DestroyOrphans` las destruye en el mismo cuadro, antes de clasificar las celdas.
- 🔑 **El aura LEE a Alma**: Alma no tiene variables del aura ni toca `StepVOReact`.
- `Aura` (StaticMeshComponent): `translucencySortPriority` 1 (Body 0), `boundsScale` 1,3, sin sombra.
