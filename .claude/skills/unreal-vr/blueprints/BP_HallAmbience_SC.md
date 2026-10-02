# BP_HallAmbience_SC — lo que se ve del Hall según el paso del director (Hall/)

> Creado 2026-09-30 (turno INICIO). Una instancia en `Test_Hall` (`HallAmbience`, en el origen), que la Obra carga como celda 5.
> **No toca al director**: lee `Mode`/`Step` de `BP_HallDirector_SC` y `Amount` de `BP_HallFog_SC` en el Tick.

## Qué hace
1. **Arquitectura oculta hasta el negro** (pedido de Beltrán vía Narrativa: *"ese mesh debe cargarse recién cuando vamos a mitad de camino y está todo negro"*).
   `ArchSet(FogA)`: oculta = `Mode == 1` **y** `Step ≤ ArchLastStep` (3) **y** (`Step ≤ 1` **o** niebla > 0).
   Es decir: HallIntro pasos 0-1 oculta; pasos 2-3 hasta que la niebla (FadeOut 12 s desde t 12) llega a **0**; desde el paso 4 (se enciende el portal), siempre visible.
   Solo actúa en el CAMBIO (`bArchHidden`): `GetAllActorsWithTag("hall_arch")` → `SetActorHiddenInGame` + print `HALL: arquitectura OCULTA/VISIBLE`.
   En Mode 0, 2 (regreso) y 3 (salida): visible (el regreso aparece bajo el velo negro de la Obra).
2. **`MPC_Hall_SC.GrooveFront`** = `Front × FrontMax`: la onda de las líneas de luz. **Ya la lee `M_Hall_Interior_SC`** (T4):
   Custom `HallGrooveRevealPS` entre HallGroovesPS y HallInteriorPS.G.
   Control positivo: MPC 2000 = look de siempre; MPC 0 = líneas del domo apagadas.
3. **`MPC_Hall_SC.DustLight`** = ease(`Dust`): tampoco lo lee nadie hoy (las motas del espacio quedaron siempre encendidas, ver abajo).

## Tag `hall_arch` (en Test_Hall)
`Hall_Shell` (SMA_1) · hojas `SMA_2..5` (también `hall_leaf`) · `Hall_OculusSky` (SMA_6) · `Hall_Tiles` (SMA_7, también `hall_tiles`) ·
`Hall_OculusShaft` (BP_LightShaft) · `Hall_Dust` / `Hall_DustShaft` (Niagara interiores) · `HallTitle_West/East` · `HallGlow_Exit`.
**NO** llevan el tag: la niebla, las motas del espacio (`SpaceDust_0..2`), las luces, el director, Alma, las almas, los TargetPoints.
Para agregar una pieza nueva de arquitectura: ponerle el tag `hall_arch`, nada más.

## Variables
| Variable | Default | Qué hace |
|---|---|---|
| `ArchLastStep` ✎ | 3 | Último paso de HallIntro en que la arquitectura puede seguir oculta |
| `EnterStepIntro` / `LeaveStepIntro` ✎ | 9 / 27 | Ventana de la onda de líneas en HallIntro |
| `EnterStepReturn` ✎ | 3 | La onda se enciende en HallReturn |
| `LeaveStepExit` ✎ | 1 | La onda se apaga en HallExit |
| `DustLastStep` / `DustExitStep` ✎ | 5 / 2 | Ventana de `DustLight` |
| `InTime` / `OutTime` ✎ | 6 / 4 | s de la onda al encender / apagar |
| `DustIn` / `DustOut` ✎ | 2 / 3 | s de `DustLight` |
| `FrontMax` ✎ | 2000 | cm; el óculo queda a ~1805 |
| `Director`, `Fog`, `Front`, `Dust`, `bArchHidden` | — | estado interno |

## Motas del espacio (mismo turno)
`NS_SpaceDust_SC` (duplicado de `NS_HallDust_SC`, renderer → `M_SpaceDust_SC`) · `M_SpaceDust_SC` (duplicado de `M_HallDust_SC`):
el Custom ya **no multiplica por HallLight** (la entrada `HL` quedó conectada pero sin usar) → siempre encendidas, luminancia de la
partícula × tinte frío (0,70; 0,80; 1,00). Tres actores `SpaceDust_0..2` en (−3300 / −2450 / −1600, 0, 200), a lo largo del camino
StopStart (−3600) → StopDoor (−980); la salida (StopExit −1500) también pasa por ellas.
⚠ Por qué no `DustLight`: una `CollectionParameter` reapuntada por MCP puede devolver **0 en silencio** (gotchas §416) → motas invisibles sin error.

## Onda verificada (T4, 2026-09-30)
La `CollectionParameter` nueva (Collection + ParameterName por MCP, sin tocar ParameterId) RESUELVE.
Probado con tres capturas del interior (`Saved/ClaudeScripts/Hall/caps/`):
- sin empalme;
- MPC 2000;
- MPC 0 (sin líneas en el domo).
El diff de píxeles de la imagen entera NO sirvió (las almas y el polvo se mueven: base≈g2000 daba 3,2); lo decidió mirar las capturas.
**Ensayo**: el snap de arranque vale también en `Step == TestFromStep` con `bTestIntro` (getter `GetTestfromStep`).

[[BP_HallDirector_SC]] · [[BP_HallFog_SC]] · [[BP_HallLights_SC]]
