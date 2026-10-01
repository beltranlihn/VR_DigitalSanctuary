# BP_AuthorMark_SC — marca de autor (ver y mover en el editor lo que el código coloca)

> ⚫ **RETIRADA 2026-10-01.** En Test_Hall ya no hay marcas: el título, el timbre y el sensor son objetos reales (`TituloInicio`, `Timbre`, `Sensor`, carpeta `Ajustes`). Lo de abajo queda como historia.

- **refPath**: `/Game/SoulCharger/Obra/BP_AuthorMark_SC.BP_AuthorMark_SC` · parent Actor · creado 2026-10-01 (Narrativa). Pedido de Beltrán: "todo lo que requiera mi decisión de dónde va, tamaños, etc. quiero tener acceso".
- **Idea**: la marca muestra EN EL EDITOR hasta dos piezas del objeto real (malla + material + offset/giro/escala) y en el juego es invisible (`P0`/`P1` con `bHiddenInGame`, sin colisión ni sombra). El código la busca **por tag** y usa **su transformación de actor**: posición, rotación y escala.
- **Altura**: la marca se autora para ojos a **120 cm sobre el piso del pawn** (z de las paradas = 76,97 en Test_Hall). En runtime: `z + (cámara.z − (pawn.z + 120))` → se corrige sola con la altura real del usuario.
- Fuente: `Saved/ClaudeScripts/Obra/authormark.json` (construction script).

## Variables (categoría **Marca**)
`Mesh0`/`Mat0`/`Off0`/`Rot0`/`Scl0` y `Mesh1`/`Mat1`/`Off1`/`Rot1`/`Scl1` (solo vista previa) · `Nota` (texto para el autor). El construction script aplica malla, material y transform relativos, y pone `Reveal` 1 / `Out` 0 (los títulos se ven encendidos).

## Marcas colocadas (Test_Hall, carpeta `Marcas` del outliner)
| Marca | Tag | La lee | Qué toma |
|---|---|---|---|
| `Mark_Timbre` (−932, 0, 168,97; pitch 59,7) | `mark_hall_bell` | `BP_HallDirector_SC.HallSpawnBell` | posición, giro y escala del timbre |
| `Mark_Sensor` (−252, 0, 168,97; pitch −59,7) | `mark_hall_sensor` | `HallSpawnSensor` | posición, giro y escala del sensor |
| `Mark_Alma0..4` | `mark_hall_soul_0..4` | `HallPickStart` | solo la posición de cada candidata (0 = centro; el tamaño es `Size` en su HallSoul) |
| `Mark_TituloInicio` (−3600, 0, 151,97) | `mark_hall_title` | `BP_Obra_SC.IntroTitle` y `BP_HallRunner_SC.HRTitle` | pose y escala del actor de créditos (el título está 4,5 m al frente); al terminar el título la escala vuelve a 1 (el mismo actor hace los créditos) |
Colocadas exactamente donde el código las ponía antes (`HallReach` 48 / 28, arco de 19 cm, cámara −45 cm): nada cambia hasta que se muevan. Sin marca, cada función vuelve a su cálculo de siempre.

## 🔴 Regla: lo que se ve en la marca es lo que se juega (2026-10-01, tras el reclamo de Beltrán)
La 1ª versión solo leía la transform del ACTOR: Beltrán cambió `Off0`/`Scl0` (lo que se ve) y en el Play no pasaba nada. Además, escalar el actor del título agranda y aleja por igual → en el visor se ve del mismo tamaño angular.
Ahora:
- **Timbre / sensor / almas**: el objeto va donde está la **pieza `P0`** (posición, giro y escala de mundo de `P0`).
- **Título**: el actor de créditos toma la pose y escala del actor-marca; `TitleP` copia la transform relativa de `P0` y `SubP` la de `P1`. A los 13 s se devuelven a los valores del BP (450/55 y 450/8; escalas 3,2×0,8 y 2,2×0,55), porque los créditos del final usan los mismos planos.
- Las piezas se encuentran por `GetComponentsByClass(StaticMeshComponent)` + `GetObjectName` que contenga "P0"/"P1" (sin leer variables de la marca: ver trampa).
- ✅ Verificado leyendo el mundo de PIE (`/Game/.../UEDPIE_0_Test_Hall.Test_Hall:PersistentLevel.BP_Credits_SC_C_0.TitleP`): `TitleP` quedó con los valores de Beltrán (350/55, 4,8×1,2×1,5). El timbre salió en la pose de su marca. En PIE de escritorio queda 120 cm más abajo, porque la cámara está en el piso del pawn; al cálculo viejo le pasaba igual.

## 🔴 Trampa
Las variables de un BP creado EN ESTA SESIÓN no se pueden leer desde otro BP hasta reiniciar el editor (gotchas: el registro de nodos no las ve). Por eso los consumidores usan solo `Actor|GetAllActorswithTag` + transform de actor, y el 120 es literal. Se quitaron `EyeRef` y `Slot` de la marca para que no confundan.
