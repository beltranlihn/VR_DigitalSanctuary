# BP_SeqSlot — progress tracker

Un slot del secuenciador del stage Touch (Fase 4). Data holder: sabe su paso y qué burbuja tiene encima.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_SeqSlot.BP_SeqSlot`  ·  **parent**: Actor  ·  **in level**: 5 en `L_Touch` (`SeqSlot_0..4`, fila a `X=55, Z=75`, StepIndex 0-4).
- **Status**: 🟢 Fase 4 lista y compila (solo estructura de datos, sin lógica propia).

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
