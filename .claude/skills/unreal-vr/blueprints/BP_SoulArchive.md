# BP_SoulArchive + BP_Constellation — la persistencia multi-usuario (Core/Flow/)

## Purpose
El destino de la obra (§Acto 8, VO 28): *"constelación de amebas de usuarios anteriores aparece · la proto viaja como estrella fugaz a su lugar"*. **Persistencia multi-usuario en device**: cada persona que termina deja su ameba guardada, y la siguiente la ve.

Pedido de Beltrán (2026-08-15): *"me interesa mañana poder hacer una prueba de principio a fin hasta llegar incluso a compartir mi ameba cargada con el resto de la constelación"*. Esto es la mitad de abajo de ese camino: **el archivo y la constelación**. Falta el tramo del medio (carga final → exterior → decisión del corazón), que es lo que sigue.

## Status
🟢 **Round-trip de disco verificado** (2026-08-15): corrida 1 crea el archivo vacío y guarda 1; **corrida 2 lo lee del disco con 1 y guarda 2**. Los 6 arrays quedan alineados (`1|1|1`, `2|2|2`). La constelación encuentra los 12 TargetPoints y spawnea las amebas guardadas **en sus transforms**. Cero `Accessed None`.
⬜ Nadie lo llama todavía desde la obra: falta `BP_Finale` (el tramo que decide *cuándo* se hace el append).

---

# BP_SoulArchive (+ SG_Constellation)

`SG_Constellation` es un **SaveGame con 6 arrays paralelos**, uno por campo, con **una entrada por usuario**: `Variants` (int) · `Colors` (LinearColor) · `Rings` (int) · `CalmAvg` (float) · `HeartAvg` (float) · `Melodies` (string).

🔴 **Por qué arrays paralelos y no un struct**: `F_SoulPortrait` existe pero está **vacío** (sólo un miembro placeholder `tBD`), y **el MCP no puede agregar miembros a un UserDefinedStruct** — no hay toolset de structs. La melodía va como **string** (CSV de IDs de clip), que es el mismo criterio que ya usa el proyecto para la firma sonora (*"se persiste como DATOS, no como asset"*, `audio-quest.md`).
📌 **Deuda de diseño consciente, anotada con Beltrán (2026-08-15)**: si él **llena `F_SoulPortrait` a mano en el editor** (variante int · color LinearColor · anillos int · calma float · ritmo float · melodía string), **hay que migrar** a un solo array de ese struct — más elegante y sin riesgo de desalineado. Está agendado en el §4 del plan como insumo suyo; no bloquea nada.
⚠ El precio de los arrays paralelos es que se pueden desalinear. Mitigación: **`AppendMe` escribe los 6 en la misma función**, y `ReportArchive` loguea las tres longitudes principales para que un desalineado se vea al instante.

## API
| Función | Qué hace |
|---|---|
| `LoadArchive()` | Si el slot existe lo carga; si no, `EnsureData` crea uno vacío. Corre en `BeginPlay`. |
| **`AppendMe(Variant, Rings, CalmA, HeartA, Melody, Col)`** | Agrega **mi** ameba al final, guarda `MyIndex`, y persiste. |
| `SaveArchive()` · `ReportArchive()` · `EnsureData()` | Guardado, log de estado y creación perezosa. |
| `MaybeClearArchive()` | 🧪 Gated por `bDebugClearOnPlay`: **borra el slot** para arrancar de cero. Es la palanca para resetear la constelación entre pruebas. |
| `DebugAppendFake()` | 🧪 Gated por `bDebugAppendOnPlay`: mete una entrada falsa. Es lo que probó el round-trip; **ambos flags quedan en `false`**. |

| Variable | Default | Rol |
|---|---|---|
| `SlotName` | `SoulConstellation` | El slot en disco (`VR_Test/Saved/SaveGames/<slot>.sav`). |
| `MaxEntries` | 60 | Tope del archivo. `TrimArchive` saca las más viejas por el frente. |
| `MyIndex` | −1 | Dónde quedó **mi** ameba — la que después tiene que viajar como estrella fugaz a su lugar. |

## 🔴 La trampa que casi pasa: `Array|Add` sobre el array de OTRO objeto opera sobre una COPIA
`(Utilities|Array|Add (Class|SGConstellation|GetVariants _d) X)` **compila y no acumula nada**: el getter de una variable de otro objeto devuelve el array **por valor**, así que el `Add` modifica una copia que se descarta. (Con una variable **propia** sí funciona — es lo que hace `CollectRings` de [[BP_ProtoSoul]], y por eso la confusión es fácil.)
**El patrón correcto es leer → agregar → volver a escribir:**
```
(bind _v (Class|SGConstellation|GetVariants _d))
(Utilities|Array|Add _v Variant)
(Class|SGConstellation|SetVariants :self _d :Variants _v)
```
⚠ Y el `Set` de una variable de otro objeto **necesita keywords**: con posicionales el target se va al pin de valor (*"Could not connect pin Data to Variants"*).

---

# BP_Constellation

Colocado en `L_Persistent` en el último tramo (X≈6000). Al llamar **`BuildConstellation()`**: cachea el archivo, junta los TargetPoints, limpia lo anterior y spawnea una `BP_ProtoSoul` por entrada guardada.

🎛️ **Las posiciones son TargetPoints, no matemática** (pedido explícito de Beltrán: *"así yo también puedo mover a mano dónde quiero que aparezcan"*). Tag **`ConstSpot`**, y se usa el **transform COMPLETO** de cada punto — verificado: las amebas nacieron con la **escala 0.6** del TargetPoint, así que cada una se dimensiona y se rota a mano.
- Hay **12 puntos colocados** como punto de partida, en arco delante del usuario. Agregar más = arrastrar más TargetPoints con ese tag.
- 🔴 **Si hay más amebas guardadas que TargetPoints, lo LOGUEA**: `CONSTELACION: FALTAN TargetPoints - quedan sin mostrar N`. Nada de truncar en silencio.
- Cada ameba se configura con el color y la variante guardados (`SetSoulColorOverride` + `bUseColorOverride` + `ApplyVariantColor`) y con **sus anillos** (`SeedRings`), así se ve cuánto cargó esa persona.
- `bDebugBuildOnPlay` (hoy `false`) la arma sola 1 s después del BeginPlay, para probarla sin recorrer la obra.

## TODO — lo que falta para el end-to-end
- [ ] 🔴 **`BP_Finale`**: carga final al 100 % + disolución del HUD → la ameba se desprende, crece y se aleja → exterior. Es el tramo que hoy no existe: la obra termina en `FinishObra` (disuelve la sala y enciende las partículas del exterior) y ahí se corta.
- [ ] 🔴 **La decisión del corazón** (VO 28). 🆕 **Beltrán definió el gesto (2026-08-15)**: *"nuestra protoameba tiene que estar **frente a nosotros al alcance de la mano**, y tenemos que **tomarla con hover + trigger**, y ahí podemos moverla hasta nuestro corazón"*.
  - **Hover = proximidad de la mano, no láser** (está a distancia de brazo). Reusar el **attach por cercanía de `BP_BrushTool`**, que está **probado en visor** (*"acercar cualquiera de las dos manos → se pega"*), como detector de hover.
  - **Trigger**: usar la config que SÍ funciona (`IA_Continue` + `IMC_Continue`, `Priority=1000` + `bIgnoreAllPressedKeysUntilRelease=False` + `bForceImmediately=True`). ⚠ `IA_Grab_*` del XRFramework **existen pero están sin mapear**, y `C_GrabComponent` es un patrón de `Recursos/` **no integrado** — no asumir que andan.
  - Al soltar en el pecho: detección de zona reusando la de `BP_HeartSensor` → `SProtoHeart` + explosión Niagara → `AppendMe` → **viaje como estrella fugaz** a su TargetPoint (`TravelToPoint` de [[BP_ProtoSoul]] ya existe y está probado).
- [ ] Los promedios reales: `CalmA`/`HeartA` tienen que salir del registro por bins de [[BP_BioHub]] (`GetCalmBinAvg`), no de números fijos.
- [ ] La melodía: serializar los IDs de `SG_Melody` al string `Melodies[i]`.
- [ ] Exploración con beam: hover sobre una ameba = suena SU melodía (el beam ya existe en Attracting).
- [ ] Créditos + reload del nivel.

## Relacionados
- [[BP_ProtoSoul]] (`ConfigureVariant`, `SeedRings`, `TravelToPoint`) · [[BP_BioHub]] (los promedios) · [[BP_AudioHub]] (SProtoHeart, SCredits) · `SG_Melody` (la melodía de Attracting)
