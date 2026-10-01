# BP_IntroTitle_SC — el título SOUL CHARGER del inicio

**Ruta:** `/Game/SoulCharger/Obra/BP_IntroTitle_SC` · **Creado:** 2026-10-01 (Narrativa) · **Estado:** 🟢 PIE (ensayo del Hall) · ⬜ visor

## Qué es
El título del inicio como **objeto real** que Beltrán mueve y escala en el editor. Reemplaza a la marca `Mark_TituloInicio` (retirada) y deja de compartir los planos con `BP_Credits_SC`.

## Componentes
| Componente | Malla / material | Relativo | Notas |
|---|---|---|---|
| `DefaultSceneRoot` | — | — | el transform del actor mueve todo el título |
| `TitleP` | `Plane` · `MI_Credit_Title` | (350, 0, 55) · rot (0, 90, 90) · escala (4,8; 1,2; 1,5) | sort 110, sin sombra, sin colisión |
| `SubP` | `Plane` · `MI_Credit_Sub` | (350, 0, 8) · rot (0, 90, 90) · escala (4,4; 1,1; 2) | igual |

Los valores de los planos son los que Beltrán dejó en la marca.

## Grafos
- **Construction:** `Reveal` 1 y `Out` 0 en los dos planos → en el editor se ve encendido.
- **BeginPlay:** `SetActorHiddenInGame true` + `Reveal` 0 → nace oculto en el juego.
- Sin variables propias ni Tick. La animación la hace quien lo encuentra por el tag `hall_intro_title`:
  - `BP_Obra_SC.IntroTitle` (fase 9, PT ≥ 2,5) y `BP_HallRunner_SC.HRTitle` (RT ≥ 2,5): suben/bajan el actor `cam.z − (pawn.z + 120)` una sola vez, lo muestran (`TitleSt` 1), y por cada `StaticMeshComponent` escriben `LT`, `Reveal` (SubP 5→7,5 s, el resto 3→6,5 s) y `Out` (10→12,5 s). A los 13 s lo ocultan (`TitleSt` 2).
  - Si no hay actor con el tag, los dos caen al código viejo (planos de `BP_Credits_SC` frente a la cámara).

## Colocado
- Test_Hall: `TituloInicio`, carpeta `Ajustes`, en (−3600, 0, 151,97) = 45 cm bajo los ojos de autor (196,97) sobre `StopStart`.
- ✅ PIE 2026-10-01: visible a los 2,5 s en (−3600, 0, 31,97) (escritorio: cámara en el piso del pawn → −120).
