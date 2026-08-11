# BP_SoulState — el GameInstance que sobrevive a los cambios de nivel (Core/Flow/)

## Purpose
§9.3 pide que **la malla y el color del Proto Soul del usuario vivan en el GameInstance**. Este es ese GameInstance: el único objeto de la obra que **no se destruye al cambiar de nivel**, y por lo tanto el único lugar donde una elección hecha en el Hall puede sobrevivir hasta la sala final.

## Status
🟢 **Construido y compilando** (2026-08-11). ⬜ Sin ejercitar en runtime todavía (la elección que lo escribe tiene un bug pendiente, ver [[BP_SoulChoice]]).

## 🔴 Hay que registrarlo en la config, o no existe
Crear el Blueprint **no alcanza**: Unreal instancia la clase que dice el ini. Se agregó a `VR_Test/Config/DefaultEngine.ini`:
```ini
[/Script/EngineSettings.GameMapsSettings]
GameInstanceClass=/Game/SoulCharger/Core/Flow/BP_SoulState.BP_SoulState_C
```
⚠ **`VR_Test/Config/` es config COMPARTIDA** (regla §7 del `CLAUDE.md`): avisar antes de tocarla. Es una línea sola y no choca con el trabajo de un stage, pero el cambio es global.
💡 Cómo se verifica que quedó: el `CastToBP_SoulState` de `GetGameInstance` tiene que dar válido en runtime. Si el ini no está, el cast falla en silencio y la elección **no se guarda sin decir nada**.

## Registro de variables
| Variable | Rol |
|---|---|
| `ChosenVariantId` | Qué variante eligió el usuario. |
| `ChosenMesh` / `ChosenMaterial` | Su malla y su material (§9.3). Pueden ser nulos: el placeholder es la esfera. |
| `ChosenColor` | Su color. |
| `bHasChosen` | 🔴 El flag que distingue *"eligió el negro"* de *"todavía no eligió"*. Sin él, un color en cero se leería como una elección válida. |

## Estructura de grafos
- **`SetChoice(NewId, NewMesh, NewMat, NewColor)`** — la única API de escritura. Guarda los 4 valores, prende `bHasChosen` y loguea.
- La lectura la hace el consumidor: `BP_ProtoSoul.AdoptFromState` castea el GameInstance y, **si `bHasChosen`**, se configura con esos valores.

💡 **Los getters de otro Blueprint se pueden leer directo desde el DSL** (`Class|BPSoulState|GetChosenVariantId`), no hace falta escribir accesores. Lo que **sí** hace falta es que el objetivo llegue por un pin: el `self` de esos nodos.

## TODO
- [ ] Ejercitarlo de verdad: elegir en runtime y confirmar que `bHasChosen` queda en true y que el HUD adopta.
- [ ] **Persistir a disco** cuando corresponda. El GameInstance sobrevive a los cambios de **nivel**, no a cerrar la app. Si la elección tiene que durar entre sesiones, va un SaveGame (patrón ya resuelto en `Calibration/`, ver `references/assets-existentes.md`).
- [ ] Es el candidato natural para el resto del **retrato del usuario**: el struct `F_SoulPortrait` (`Core/Amoeba/`) existe y todavía no lo usa nadie.
- [ ] Higiene de nodos (`clean_orphans.py` + `auto_layout.py`).

## Relacionados
- [[BP_SoulChoice]] (quien lo escribe) · [[BP_ProtoSoul]] (quien lo lee) · `F_SoulPortrait` (UserDefinedStruct, sin usar)
