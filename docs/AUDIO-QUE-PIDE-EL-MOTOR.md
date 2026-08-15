# 🎧 El audio que el motor ya está pidiendo — lista de entrega

> Generado el **2026-08-15** leyendo los valores efectivos de los Blueprints, no la documentación. Cada nombre e índice de esta lista es **literalmente el que el código busca hoy**.
>
> **Cómo se entrega:** todo entra por el actor **`BP_AudioHub`** que está en `L_Persistent` — se seleccionan sus propiedades en el editor y se arrastran los assets. **No hace falta tocar ningún Blueprint.** Hoy los tres contenedores están **vacíos**, y por eso el log dice cosas como `AUDIO: falta SFX SBubble`: no es un error, es el hueco esperándote.

---

## 1. `SfxMap` — mapa `nombre → SoundBase`

La **clave tiene que ser exactamente** este texto. El valor es el sonido.

| Clave | Cuándo suena | Quién lo pide |
|---|---|---|
| `SBubble` | Hover sobre cualquier botón de menú | `BP_MenuButton` |
| `SSelect` | Se confirma un botón | `BP_MenuButton` |
| `SBell` | Arranca el sostenido del timbre (mientras se mantiene) | `BP_MenuButton` |
| `SProtoHover` | Hover sobre una proto ameba elegible en el Hall | `BP_SoulChoice` |
| `SProtoselect` | Se elige la ameba del Hall ⚠ **la "s" minúscula es parte de la clave** | `BP_SoulChoice` |
| `SCharger` | La ceremonia de carga al cerrar cada etapa | `BP_Ceremony` |
| `SPulse` | Cada latido reconocido en Recognizing | `BP_Stage_Recognizing` |
| `SMind1` · `SMind2` · `SMind3` | Las tres preguntas de Loving | `BP_Stage_Loving` |
| `SChargerFinal` | La carga final, cuando la barra llega a 100 | `BP_Finale` |
| `SProtoHeart` | La ameba entra al corazón | `BP_Finale` |
| `SCredits` | Los créditos | `BP_Finale` |

## 2. `AmbientMap` — mapa `nombre → SoundBase`

El director hace **crossfade de 3 s** entre ambientes al cruzar cada puerta. Las claves que pide, **en orden de recorrido**:

| Clave | Sala |
|---|---|
| `Ambient3` | Hall |
| `Ambient4` | Entering |
| `Ambient5` | Recognizing |
| `Ambient6` | Loving |
| `AttractingBase` | Attracting (la base sobre la que se arma la melodía) |
| `Ambient7` | Surrounding |

🔴 **Faltan tres del guión y no están cableados todavía**: **Ambient 1** y **Ambient 2** (la aparición y el corredor, antes del Hall) y **Ambient 8** (el exterior, después de que la ameba viaja a la constelación). Cuando existan los archivos se agregan al mapa y se enganchan — es una línea cada uno.

## 3. `VoClips` — array de `SoundBase`, **indexado por posición**

🔴 **El índice es 0-based, así que el "VO 25" del guión es la posición 24.** El array tiene que llegar hasta el 29 aunque haya huecos: los lugares vacíos se dejan vacíos y el motor loguea y sigue.

| Posición | VO del guión | Momento | Quién lo pide |
|---|---|---|---|
| 10 · 13 · 18 · 22 · 25 | VO 11 · 14 · 19 · 23 · 26 | Ceremonia de carga al cerrar cada etapa | `BP_Ceremony.VoIndexByStage` |
| 15 · 16 · 17 | VO 16 · 17 · 18 | Las tres preguntas de Loving | `BP_Stage_Loving.VoIndex` |
| 21 | VO 22 | Coda de Attracting | `BP_Stage_Attracting` |
| 24 | VO 25 | La carga final | `BP_Finale.VoFinalIndex` |
| 25 | VO 26 | **El gráfico de resultados** | `BP_Finale.VoResultsIndex` |
| 27 | VO 28 | Decidir llevarla al corazón | `BP_Finale.VoHeartIndex` |
| 29 | VO 30 | Gracias, sobre los créditos | `BP_Finale.VoThanksIndex` |

⚠ `BP_Ceremony.VoIndexByStage` empieza con **−1** a propósito: la etapa 0 (Hall) no tiene VO de ceremonia.

## 4. `MelodyClips` — array de `SoundBase`, las **notas**

Es el banco con el que suena una melodía guardada cuando se apunta una ameba de la constelación, y el que va a usar Attracting cuando tenga audio real. Hoy tiene los dos MetaSounds de prueba (`MS_Synth`, `MS_Perc`).
**El id de nota es la posición en este array.** `MelodyStep` (0,32 s) es el tiempo entre notas.

🔴 **Deuda conocida, para que no sorprenda:** lo que hoy se guarda como "melodía" son los **índices de paso** del secuenciador, no los ids de nota — o sea todas las melodías guardadas salen iguales. Se arregla cuando `BP_SoundBubble` tenga un id de clip (es parte del audio real de Attracting). La cadena de reproducción ya funciona; sólo cambia qué significan los números.

## 5. Dos cosas que quedaron sin sonido asignado
- **`BP_BreathPacer`**: `CountSfx` (el pulso del ritmo guiado 4/4/4) y `VoClip` están en `None`. Son referencias directas a un `SoundBase`, no claves de mapa: se arrastran en la instancia.
- **`SDraw`**, el sonido de dibujar en Surrounding, **todavía no está cableado** en `BP_BrushTool`.

---

## Cómo verificar que quedó bien, sin visor
`BP_AudioHub.ReportCatalog` loguea lo que tiene cargado. Y cualquier hueco se delata solo: al correr la obra, el log dice `AUDIO: falta SFX <clave>` con el nombre exacto. **Si no aparece ningún "falta", está completo.**
