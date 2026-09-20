# Plan — el nivel DEFINITIVO (`L_SoulCharger_V3`), 2026-09-21

> Pedido de Beltrán (noche del 2026-09-20): *"Vamos a crear un level nuevo. Que será el definitivo. En este vamos a integrar cosas de ambos level."* — la narrativa y las mecánicas de `MapsV2/L_SoulCharger` con la estética probada en `TestMeshes`.
> Y, a mitad del plan: *"Piensa en construirlo de una manera que siempre esté bien optimizado para el apk."*

**Nivel:** `/Game/SoulCharger/MapsV3/L_SoulCharger_V3` (duplicado de `MapsV2/L_SoulCharger`).
**El viejo no se toca.** `MapsV2/L_SoulCharger` y sus 6 sublevels quedan intactos como referencia.

---

## 1. Qué cambia respecto de V2

| | V2 (hoy) | V3 (el definitivo) |
|---|---|---|
| **Recorrido** | el pawn camina entre las 6 salas (paradas 3→8 del spline) | camina **hasta la parada 4 (Entering, x = 1500) y ahí se queda**. Las 5 etapas ocurren en el mismo lugar |
| **El espacio** | cilindro de piso + cilindro de muro por sala (`Asset/RoomBase`) | **una esfera de color** (`BP_Ganzfeld_SC`), como las esferas de contexto de la galería |
| **Transición** | fundido a negro + descarga/carga de sublevel + caminata | **la esfera vira de color** del actual al siguiente, gradual y sin negro |
| **Recepción (Hall)** | sublevel con su arquitectura | **igual, no se toca** (único que mantiene el mesh actual) |
| **Entering** | `BP_BreathOrb_SC` (una esfera) | **el metaball** (`BP_MetaBlob_SC`, modo CURL, movido por la respiración) |
| **Recognizing** | `BP_Elevator_SC` (los elementos bajan) | **las ondas circulares** (`BP_PulseField_SC`) |
| **Loving** | `NS_NeuralWeb_SC` | **el metaball en modo GROUP** (`BlobMode = 3`) |
| **Attracting** | secuenciador con esferas | secuenciador **+ el metaball pulsando cada blob según su slot** |
| **Surrounding** | dibujo 3D | **igual** |
| **Final** | la sala se cierra | **igual: vacío, y la esfera desaparece** |

### Los colores de la esfera
| Etapa | Color |
|---|---|
| 1 Entering (Breath) | **azul** |
| 2 Recognizing (Heart) | **rojo** |
| 3 Loving (Mind) | **morado** |
| 4 Attracting | **naranja** |
| 5 Surrounding (Dibujo) | **verde** |
| Final | sin esfera |

---

## 2. 🔴 La arquitectura, y por qué es la MÁS optimizada para el APK

**Decisión: cero streaming durante la experiencia.** Las 5 etapas viven en el **nivel persistente**, en el mismo sitio (x = 1500), y se prenden/apagan por tag. El Hall sigue siendo el único sublevel (ya se precarga en negro).

Esto no es una simplificación: es la opción más barata en el device, y cada punto está **medido**, no supuesto.

| Palanca | Por qué | Evidencia |
|---|---|---|
| **1. Ningún `LoadStreamLevel` entre etapas** | las transiciones de sala costaban **604 ms repartidos en 42 frames** (y el Hall 94 ms en 3 frames = ~31 ms/frame). Con las etapas en el persistente, **ese tirón desaparece entero**: cinco veces por obra | `BP_Director_Rooms.md`, medición en device 2026-08-21 |
| **2. Una sola esfera, con `M_GanzSolid_SC` (fondo liso)** | el cascarón en modo fluido cuesta **~12 ms de los 13,9** del presupuesto. En liso cuesta ~4 y deja lugar para el efecto que va adelante | `BP_Ganzfeld_SC.md`, visor 2026-09-16: metaball + cascarón liso = **9,4–11,4 ms, 72–73 fps** |
| **3. Solo la etapa activa VISIBLE y TICKEANDO** | `SetActorHiddenInGame` **no apaga el Tick**: se midieron **101 actores tickeando escondidos** en la galería. El patrón por tags (`GalHideAll`/`GalShow` + `SetActorTickEnabled`) ya está probado | `BP_GalleryDirector_SC.md`, 2026-09-08 |
| **4. UN solo metaball, reusado por las etapas 1, 3 y 4** | el raymarch es `Steps × BlobCount` = hasta 384 evaluaciones por píxel. Tres actores serían tres proxies y tres MID; nunca puede haber dos a la vez | `BP_MetaBlob_SC.md`, 2026-09-15 |
| **5. Nunca dos volúmenes raymarch simultáneos** | el metaball aporta 6–12 ms él solo. La gota raymarcheada de `BP_PulseField_SC` (`bRaymarchDrop`) y el metaball **no coinciden nunca**, porque están en etapas distintas | — |
| **6. Se borran 4 arquitecturas de sala y 4 puertas** | cuatro pares cilindro-piso/cilindro-muro con sus MI, y cuatro `BP_Door_SC` con su widget UMG, dejan de existir | — |
| **7. `CastShadow = false` en los proxies de raymarch** | gratis: una sombra de un translúcido raymarcheado no hace nada | `BP_MetaBlob_SC.md` |

**Presupuesto por etapa (13,9 ms):** cascarón liso ~4 ms + un efecto. Las etapas 1, 3 y 4 son las de riesgo (metaball); 2 y 5 son baratas (plano opaco unlit / ribbons).
🔬 **Lo que falta y solo se cierra en gafas:** el costo real de la etapa 4 (metaball + 20 esferas + 8 slots juntos) y del modo GROUP con su `BlobCount`. Se mide con `CAPTURAR_RENDIMIENTO.bat`.

---

## 3. Orden de construcción

### P0 — Cimientos
1. ✅ Duplicar el nivel a `MapsV3/L_SoulCharger_V3`.
2. Mover al sitio de Entering (x ≈ 1500) los `TargetPoint` de las salas 2-5 (`alma_*_appear`, `alma_*_move`, `soul_pick_*`) — ya viven en el persistente.
3. **`BP_StageShell_SC`** (nuevo): la esfera de color + visibilidad/tick por tag + el viraje gradual.
4. Colocar la esfera y cargar la tabla de 5 colores.

### P1 — El flujo
5. `BP_Director_Story`: las salas 1-4 avanzan **por la esfera**, no por puerta + caminata.
6. `BP_Director_Rooms`: `RoomLevels` = solo el Hall; la salida del Hall es `CloseRoom()`.

### P2 — Las mecánicas, una por etapa
7. **Entering**: metaball (respiración) en lugar de `BP_BreathOrb_SC`; se mantiene `BP_BreathRing_SC`.
8. **Recognizing**: `BP_PulseField_SC` en lugar de `BP_Elevator_SC`.
9. **Loving**: el mismo metaball en modo GROUP.
10. **Attracting**: secuenciador + el metaball pulsando por slot.
11. **Surrounding**: el dibujo, igual.
12. Los paneles de instrucciones, uno por etapa, en el mismo sitio.

### P3 — Verificación sin gafas
13. Rutinas del robot (`BP_Robot`) + pasadas de PIE leyendo el log, incluido `Accessed None`.

---

## 4. Riesgos conocidos y su mitigación

| Riesgo | Mitigación |
|---|---|
| Un `execute_tool_script` que falla dispara un **Undo que se come actores del nivel** | plantilla `safe_script.py` + **canario de actores antes/después de cada tanda**, y `save_assets` solo con el canario en verde. Commit `a39f788` es el punto de retorno |
| Las variables nuevas **nacen en 0 en las instancias ya colocadas** (mordió 4 veces) | sembrar explícitamente cada perilla en la instancia, y **verificar leyendo**, no asumiendo |
| Un componente nuevo llega **sin malla** a la instancia (gotcha §320/341) | escribir `staticMesh` también en la instancia |
| `BP_BreathManager_SC` y `BP_HeartManager_SC` **pelean por el mismo mando** | tag por etapa: el manager de respiración solo tickea en la 1, el de latido solo en la 2 |
| Todo lo que viaja pegado a la cámara **bloquea los line traces** | HUD, viñeta, proto ameba y anillos ya están en `NoCollision`; verificar que sigan así |

---

## 5. Bitácora

### ✅ P0 — Cimientos (hecho)
- `MapsV3/L_SoulCharger_V3` duplicado de V2.
- **38 `TargetPoint`** de las salas 2-5 y del final movidos al sitio de Entering (canario 82→82, verificados releyendo).
- **`BP_StageShell_SC`** construido: 13 funciones, 26 variables, dispatcher `OnStageReady`. Tracker: [`BP_StageShell_SC.md`](../.claude/skills/unreal-vr/blueprints/BP_StageShell_SC.md).
- `Shell_Stages` (`BP_Ganzfeld_SC` + `M_GanzSolid_SC`, radio 1400) colocado **centrado en el usuario** (`x = 1151,7`) y `Director_Shell` con la tabla de 5 colores.

🔑 **El dato que ordenó todo:** el spline del recorrido es **local** y su actor está en `x = −348,3`, así que **el pawn para en world `x ≈ 1152`**, no en 1500. Con eso, las posiciones autoradas de los sublevels caen donde tienen que caer: el panel a 1,6 m, el botón a 0,7 m, el metaball a 2,1 m, Alma a 3,5 m.

### ✅ P1/P2 — Las 5 etapas en el sitio (hecho)
- **35 actores** colocados en sus posiciones autoradas (canario 94→129, cero fallos): metaball en Entering, `BP_PulseField_SC` en Recognizing, metaball GROUP en Loving, secuenciador completo (+8 slots, +22 anclas) en Attracting, y los 4 paneles de instrucciones con sus índices de página.
- **Las puertas entre etapas eliminadas del flujo:**
  - `BP_Director_Rooms.ExitToStage()` (nueva) = la salida del Hall: fundido + descarga + caminata, sin sala siguiente.
  - `BP_Director_Story`: `NextRoom` ahora llama a la esfera y espera **`"shell"`**; `RunRoomB` sub 8 ya no llama a `EndStage`; `RunHallB` sub 10 usa `ExitToStage`; `CloseRoomNow` apaga la esfera en el final.
  - `RoomLevels` del nivel = **solo `L_Hall_SC`**.
- **Antihielo:** `CheckShell` pone la esfera al día si quedó desfasada (cubre el salto de `DebugStartRoom`, que entra a una sala **sin** pasar por `NextRoom`).

### 🔬 Verificado por log en PIE
| Qué | Resultado |
|---|---|
| Ciclo de 5 etapas en modo automático | 🟢 tiempos exactos (3,0 s de viraje + 0,6 de sostén), 23 estaciones recogidas |
| Encadenado real del guión | 🟢 `sala 2 paso 0 espera: shell` → la esfera vira → sala 2 corre los pasos 1-7 |
| `Accessed None` | 🟢 **cero** en todas las corridas |

🐛 **El bug que cazó la primera pasada, y vale como regla:** `HideAll` apaga el **Tick** de las estaciones. Con la esfera en `Stage 0`, el panel de instrucciones quedaba con el Tick apagado y **su animación de salida nunca terminaba** → la obra se trababa esperando `"panel"`. No era el panel: era que nadie le había pedido la etapa 1 a la esfera.

### ✅ Pasada COMPLETA desde el arranque real (`DebugStartRoom = −1`)
La verificación que importaba, porque ejercita la única caminata que queda:
```
menu -> caminata (29 s) -> timbre -> Hall (pasos 0-9, con la explicacion de las etapas)
     -> ExitToStage: negro + descarga del Hall + caminata
     -> sala 1 paso 0 espera: shell  ->  la esfera sube AZUL
     -> salas 1..5 encadenadas por el viraje de color, cada una con sus pasos 1-7
```
Medido en la instancia de PIE al llegar: **pawn en (1151, 0, 115)** = la parada de Entering · `LegIndex 4` · caminata terminada · **esfera visible** · `Stage 1`. Cero `Accessed None`.

### 🐛 Dos bugs que solo aparecieron corriendo la obra entera
**1. 🔴 Ocultar un actor NO apaga su colisión.** El log lo cantó con nombre y apellido: `BEAM R/L corto contra: PulseField_Heart`. El plano de las ondas del latido (etapa 2) seguía **bloqueando el line-trace del beam** durante Attracting, aunque estuviera invisible y sin Tick. Es la misma familia que la saga de colisionadores fantasma (viñeta → ameba → HUD), por una puerta nueva: **al juntar las 5 etapas en el mismo sitio, lo oculto de una estorba a la otra**.
✅ `HideAll`/`ShowStage` ahora también hacen **`SetActorEnableCollision`**. Verificado: en la corrida siguiente el beam se arma y **no hay ni una línea de choque**.
👉 **Regla para este nivel:** una estación se apaga en **tres** canales — visibilidad, Tick y **colisión**.

**2. 🔴 El salto de debug entra a una sala SIN pasar por `NextRoom`**, así que nadie le pedía la etapa a la esfera. Como `HideAll` apaga el Tick, el panel de instrucciones quedaba con el Tick muerto y **su animación de salida nunca terminaba** → la obra se trababa esperando `"panel"`. ✅ `CheckShell` pone la esfera al día sola.

### 🔗 Compatibilidad: el nivel V2 sigue vivo
Los directores son **compartidos**, así que la cirugía habría dejado `MapsV2/L_SoulCharger` trabado esperando una esfera que ahí no existe. Se le puso **repliegue automático**: si no hay `BP_StageShell_SC` en el nivel, `ExitHall` y `GoShell` vuelven al camino viejo (`EndStage` + espera `"door"`). **Un solo código sirve a los dos niveles.**
Los otros cambios ya eran aditivos: `ExitToStage` es una función nueva, y el pulso del metaball queda inerte con `PulseAmt = 0` (que es lo que heredan las instancias viejas de la galería).

### ⬜ Lo que falta
- [x] ✅ **Valores autorados de los metaballs sembrados** (incluida la respiración del de Entering, copiada de `GAL_7_MetaBlob`).
- [x] ✅ **Attracting: el metaball pulsa por slot** — aditivo, con `PulseAmt = 0` la galería queda byte a byte igual. Medido en PIE.
- [x] ✅ **`StepTimes` restaurado** a `[0, 90, 240, 0, 300, 300]`; robot en `RobotOn = 0`; sin auto-demo.
- [ ] 🔴 **VISOR** — es lo único que decide: los 5 colores, `FadeTime` (hoy 3 s), el aspecto del GROUP en Loving, cuánto pulso en Attracting (`PulseAmt` 0,6) y **el costo real en device** de las etapas 3 y 4.
- [ ] **Surrounding no cierra sin alguien que dibuje.** Es una limitación **ya conocida de V2** (la práctica de dibujo cierra el panel por mecánica), no algo que haya traído V3. Se destraba con el robot en `Routine = 3` o con las manos puestas.
- [ ] **Rutinas del robot para Entering / Recognizing / Attracting**: las de V2 estaban atadas al director viejo. ⚠ Y hay un techo real: la respiración y el latido **dependen de los bits de validez del tracking**, que en PIE no existen — eso solo se prueba en gafas.
- [ ] Decidir si el Hall (`L_Hall_SC`) se duplica a `MapsV3` o se sigue compartiendo con V2 (hoy compartido y **sin tocar**).
