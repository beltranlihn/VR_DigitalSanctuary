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

## 5. Estado

Se va actualizando a medida que avanza la construcción. Ver la bitácora al final.
