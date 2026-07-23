# 🗺️ Mapa de Blueprints del proyecto Soul Charger

Índice de **todos los Blueprints que existen** en el proyecto: qué es cada uno, dónde está, para qué sirve y su estado. El **detalle profundo** (variables por categoría, estructura de grafos, qué palanca ajusta qué) vive en el **tracker por-BP** de esta misma carpeta (`blueprints/<BP>.md`); este archivo es el **índice que los mapea**.

> 🔴 **REGLA (mantener vivo):** cada vez que crees o modifiques un Blueprint, **actualizá su fila acá** (estado, propósito) **y su tracker** (`blueprints/<BP>.md`). Si un BP no tiene tracker y lo vas a tocar, crealo (modelo: `BP_BreathSensor_V2.md`, plantilla: `_TEMPLATE.md`). Así, al retomar un BP viejo, sabés su estado sin releer el grafo.
>
> **Leyenda estado:** 🟢 funcional/validado · 🟡 en progreso · 🧩 stub/scaffold vacío · ⚪ existe pero sin auditar (completar al tocarlo) · 🗑️ deprecado.
> **Tracker:** ✓ = tiene tracker detallado · — = todavía no.

---

## Core — infraestructura compartida (`Content/SoulCharger/Core/`)
> ⚠️ Estos son **compartidos entre stages** → coordinar antes de tocar (ver `docs/WORKFLOW-EQUIPO.md`). Varios están **sin auditar en detalle** — auditar y documentar al primer trabajo sobre ellos.

| Blueprint | Ruta | Qué hace | Estado | Tracker |
|---|---|---|---|---|
| **BP_VRPawn_SC** | `Core/Pawn/` | El pawn VR de la obra (derivado del VR template; obra sentada). | ⚪ | — |
| **BP_SoulChargerGameMode** | `Core/Flow/` | GameMode; `DefaultPawnClass = BP_VRPawn_SC`. | ⚪ | — |
| **BP_FlowDirector** | `Core/Flow/` | Orquestador maestro del flujo entre stages (level streaming del persistente). | ⚪ por auditar | — |
| **BP_SignalProvider** | `Core/Signals/` | Abstracción de la señal biométrica (respiración/latido/EEG) que consumen los stages. | ⚪ por auditar | — |
| **BP_SignalProvider_Fake** | `Core/Signals/` | Mock de señal para testear sin sensor real. | ⚪ por auditar | — |
| **BP_FadeSphere** | `Core/UI/` | Esfera de fade a negro (transiciones). Compartida por los stages. | 🟢 | — |
| **BP_IntroFade** | `Core/UI/` | Fade de entrada al stage + spawnea el widget de instrucciones en su TargetPoint. | 🟢 | — |

## Stage Breath 🟢 (`Content/SoulCharger/Stages/Breath/`) — plantilla de la obra
| Blueprint | Ruta | Qué hace | Estado | Tracker |
|---|---|---|---|---|
| **BP_BreathSensor_V2** | `Stages/Breath/` | Sensor agarrable + detector de respiración + calibración/zona segura + conteo + hápticos, fusionado. Corazón del stage. `Step` frágil (no reescribir). | 🟢 | ✓ |
| **Box_Breath** | `Stages/Breath/` | La esfera visual; consumidor tonto que lee el sensor y anima escala + material emisivo + Niagara. | 🟢 | ✓ |
| **BP_Instructions** | `Stages/Breath/` | Máquina de 5 páginas (driver del widget world-space): `GotoPage/InitRefs/UpdateFade` + spawnea sensor/esfera. | 🟢 | — (ver memoria instructions-widget) |
| **WBP_BreathInstructions** | `Stages/Breath/Widget/` | El widget UMG de 5 páginas (visual). | 🟢 | — |
| **BP_BreathStageManager** | `Stages/Breath/` | Orquesta el cierre: fin de conteo → esfera a 0 → fade → reinicia. | 🟢 | ✓ |
| **BP_BreathProbe** | `Stages/Breath/Deprecated/` | Bitácora de los 26 tests que descubrieron el modelo de señal (ZigZag). Conceptualmente heredado por V2. | 🗑️ | ✓ |
| **BP_BreathSensor** | `Stages/Breath/Deprecated/` | Versión previa a la fusión en V2. | 🗑️ | — |

## Stage Heart 🟡 (`Content/SoulCharger/Stages/Heart/`)
| Blueprint | Ruta | Qué hace | Estado | Tracker |
|---|---|---|---|---|
| **BP_HeartSensor** | `Stages/Heart/` | Beat desde OSC + visualizador de zona segura (debug). 🟡 la esfera de debug queda fija en el mundo (pendiente que siga la cabeza). | 🟡 | ✓ |
| **Ball_Heart** | `Stages/Heart/` | Pulso de escala por latido (consumidor visual). | 🟡 | ✓ (`Ball.md`) |
| **BP_HeartInstructions** | `Stages/Heart/` | Driver del widget de instrucciones (duplicado de Breath). | 🟡 | — |
| **WBP_HeartInstructions** | `Stages/Heart/Widget/` | Widget UMG (duplicado de Breath). | 🟡 | — |
| **BP_HeartIntroFade** | `Stages/Heart/` | Fade + spawn del widget (duplicado). | 🟡 | — |
| **BP_HeartStageManager** | `Stages/Heart/` | Cierre del stage (duplicado de Breath). | 🟡 | — |

## Stage Touch = "Attracting" 🧩 (`Content/SoulCharger/Stages/Touch/`) — scaffold
> Plan completo: `docs/stages/touch-attracting.md`. Los stubs están vacíos, listos para construir por fase.

| Blueprint | Ruta | Qué hace (previsto) | Estado | Tracker |
|---|---|---|---|---|
| **BP_AttractDirector** | `Stages/Touch/` | Cerebro: flujo + reloj Quartz + step sequencer de 5 pasos. | 🧩 stub | — |
| **BP_SoundBubble** | `Stages/Touch/` | Burbuja sonora: preview con fade, far-grab con interp, audioreactivo. | 🧩 stub | — |
| **BP_SeqTable** / **BP_SeqSlot** | `Stages/Touch/` | Mesa con 5 slots (cada slot = un step del secuenciador). | 🧩 stub | — |
| **BP_AimBeam** | `Stages/Touch/` | Láser de apuntado + hover + trigger (line-trace desde pose aim). | 🧩 stub | — |
| **BP_SaveButton** | `Stages/Touch/` | Botón "Guardar melodía" (gateado por 5 slots llenos). | 🧩 stub | — |
| **BP_TouchInstructions** | `Stages/Touch/` | Driver de instrucciones (duplicado de Breath; **sin wirear** — ver plan). | 🧩 | — |
| **WBP_TouchInstructions** | `Stages/Touch/Widget/` | Widget de instrucciones (fondo naranja). **Textos por definir.** | 🧩 | — |
| **SG_Melody** | `Stages/Touch/` | SaveGame de la melodía (array de 5 clip-IDs). **Falta el array.** | 🧩 stub | — |

## Herramienta Calibration 🟢 (`Content/SoulCharger/Calibration/`) — no es stage
| Blueprint | Ruta | Qué hace | Estado | Tracker |
|---|---|---|---|---|
| **BP_CalibDirector** | `Calibration/` | Máquina de estados de 7 segmentos guiados + persistencia por usuario. | 🟢 (falta test visor) | ✓ (cubre el sistema) |
| **BP_CalibProbe** | `Calibration/` | Sensor duplicado de V2 + `RecOn/RecOff`; calcula features para la captura. | 🟢 | ✓ (en `BP_CalibDirector.md`) |
| **SG_CalibSession** / **SG_CalibIndex** | `Calibration/` | Persistencia: un `.sav` por usuario + contador. | 🟢 | ✓ (en `BP_CalibDirector.md`) |
| **WBP_CalibInstructions** | `Calibration/Widget/` | Widget de instrucciones world-space (duplicado de Breath, Mode 1 icono+texto). Lo maneja el Director (`InstrPanel` component). | 🟢 (falta test visor + íconos) | ✓ (en `BP_CalibDirector.md`) |

## Externo
| Blueprint | Ruta | Qué hace | Estado | Tracker |
|---|---|---|---|---|
| **BP_OSCReceiver** | `/Game/OSC/` | Recepción de datos por OSC (única referencia funcionando del cableado del delegate). | 🟢 | ✓ |

---

## Por clasificar (revisar qué son al tocarlos)
`Core/Amoeba/F_SoulPortrait`, `Core/Flow/F_Beat`, `Core/Signals/F_Signal` — prefijo `F_` (¿function library / struct / material function?). `Stages/Breath/Widget/Deprecated/Widget_1` (🗑️). Auditar y mover a la tabla que corresponda cuando se trabajen.

> Assets que NO son Blueprints (materiales `M_`/`W_`, Niagara `NS_`, audio, input `IA_`/`IMC_`, fuentes) no van en este mapa — se referencian desde el tracker del BP que los usa.
