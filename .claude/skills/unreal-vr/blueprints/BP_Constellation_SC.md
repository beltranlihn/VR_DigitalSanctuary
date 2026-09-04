# BP_Constellation_SC — el cielo de los que pasaron antes (Core/Flow/)

> Versión limpia (`_SC`) del viejo [[BP_Constellation]] + [[BP_ConstExplorer]] **fusionados en un solo actor**.
> Nace del plan [`docs/PLAN-CIERRE-2026-08-27.md`](../../../../docs/PLAN-CIERRE-2026-08-27.md), **fases F4 y F5**.

- **refPath**: `/Game/SoulCharger/Core/Flow/BP_Constellation_SC.BP_Constellation_SC` · **parent**: Actor
- **En el nivel**: sí, `BP_Constellation_SC_C_0` en `L_SoulCharger` (persistente), en el origen.
- **Los puntos**: 20 `TargetPoint` con el tag **`ConstSpot`**, etiquetados `TP_const_00` … `TP_const_19`.

## Status
🟢 **F4 verificada en PIE (2026-08-27)** — dos caminos:
- Aislada (`bDebugBuildOnPlay`): `banco de mallas = 5` · `guardadas = 20 | puntos = 20` ·
  `cielo completo, estrellas = 20`, con los anillos leídos del archivo (4,5,3,4,5,… y la última en **0**,
  que es justo la entrada real de la corrida de F3).
- **Por el guión real** (autotest, final completo): `mi ameba ya viajo sola - salteo su entrada` →
  **`cielo completo, estrellas = 19`**. Las 19 guardadas + la propia = 20 almas en el cielo. ✅

🟢 **F5 verificada en PIE (2026-08-27)** con `bDebugCycle`: 12 vecinos seguidos, cada uno con **su**
melodía (`0:4,2:9,4:15,7:7` → `0:5,2:10,…`) y **sus** series (`180/180/4`, `180/180/5`, `180/180/6`,
`180/180/7`…). Cero `Accessed None`, y las esferas de la melodía anterior se destruyen solas
(`BP_SoundOrb_SC.UpdateVisual` hace `DestroyActor` cuando `bDying` y `RevealT < 0.05`).

🟢 **El final completo corrió punta a punta** (autotest, 2026-08-27), con cada perilla clavada:
```
15:43:36  paso 6  retrato        (PortraitHold 6)
15:43:42  paso 7  compartir      +6,0 s
15:43:44  paso 8  llegada
15:43:48  paso 9  CONSTELACION   (ConstHold 10)
15:43:58  paso 10 EXPLORACION    +10,0 s   (ExploreSeconds 25)
15:44:23  paso 11 VO 33 + apagado +25,0 s
15:44:33  paso 12 step time
15:44:53  STORY: FIN del guion   +20,0 s (StepTimes[5])
```
⬜ Falta **visor**: apuntar de verdad con la mano (en PIE los mandos no están trackeados, por eso existe
`bDebugCycle`).

## Por qué UN solo actor y no dos
El viejo par `BP_Constellation` + `BP_ConstExplorer` se partía en dos porque el explorador sólo necesitaba
`Spawned`. Acá la exploración necesita además **`Indices`** (qué entrada del archivo es cada estrella),
que es estado del constructor. Partirlo obligaría a exponer dos arrays paralelos entre actores.
👉 Un actor, dos grupos de funciones. **El BEAM sí vive en el sensor** (directiva de Beltrán:
toda la interacción en [[BP_Sensor_Soul]]).

## F4 — construir el cielo

```
Build()  → CacheRefs · CollectSpots · ClearStars · BuildLoop
BuildLoop: Total = Archivo.Count() · timer LOOP StarGap → GradualStep
GradualStep: si Cursor<Total Y SpotCursor<len(Spots) → GradualOne ; si no → GradualDone
GradualOne:  si bSkipMine Y Cursor==Archivo.MyIndex → sólo avanza Cursor (mi ameba ya viajó sola)
             si no → SpawnStar(Cursor, SpotCursor) y avanza los dos
SpawnStar:   spawn de BP_ProtoSoul_SC en el transform del TargetPoint → DressStar
DressStar:   SeedRings(Rings[i]) · EnableHover(false) · MoveToActor(spot) · push a Spawned/Indices · DressLook
DressLook:   Configure(MeshBank[Variants[i]], Colors[i])   (si la variante no está en el banco, deja la malla por defecto)
```

**`MeshBank`** se llena en `BeginPlay + 0,6 s` (`CacheMeshes` → `BankLoop`) leyendo
`Picker.Souls[i].Mesh` — **antes** de que `ForceChoose` destruya a las 4 perdedoras (que ocurre a 1,0 s).
Es la única forma de resolver `Variant → malla` sin duplicar el catálogo a mano.

🔑 **`MoveToActor` (verbo nuevo en [[BP_ProtoSoul_SC]])** = `MoveTo` sin `FindPoint` y sin `bArriveArmed`:
setea `TargetRef` + `bFound` y llama a `StartTravel`. Con eso la estrella queda **anclada por ATTACH**
al TargetPoint y **toma su ESCALA** (`AnchorStep` escribe `Size` desde el `Scale3D` del punto) —
o sea que Beltrán autora posición **y** tamaño moviendo el TargetPoint en el viewport, incluso en PIE.

## F5 — recorrer el cielo

```
StartExploring() → CacheExplore · FindFocus · IsValid(FocusPoint) → ExploreGo
ExploreGo:  bExploring=true · timer LOOP PollTime → PollHover · MaybeCycle · Sensor.ExploreOn(true)
EventTick   → BeamTick → (si bExploring) BeamNow → Sensor.AimBeams()      ← el láser, por frame
PollHover:  BestDot=-2 · BestIdx=-1 · IsValid(PawnRef) → PollBody
PollBody:   PickAim(derecha) · ScanSouls · PickAim(izquierda) · ScanSouls · Resolve
ScanOne:    dot(AimDir, dir(AimOrigin→estrella)) > BestDot → se queda
Resolve:    si BestDot > cos(AimConeDeg) Y BestIdx != HoverIdx → Unfocus · HoverIdx=Best · Focus
Unfocus:    la anterior vuelve a SU estrella (MoveToActor(Spots[HoverIdx]))
Focus:      la nueva baja al atril (MoveToActor(FocusPoint))
            + DrawNeighbour → Canvas.RebuildFrom(Draw[i]) + Sensor.ShowSignature()
            + Retrato.ShowIndex(Indices[HoverIdx], soul)
StopExploring() → limpia timers · ExploreOff → Retrato.Hide() · Sensor.ExploreOn(false)
```

🔑 **El "atril" es el mismo punto del retrato propio**: `FocusTag` = **`portrait_soul`**. El vecino baja
a donde el usuario acaba de leer su propio retrato, con el panel ya ahí. Cero TargetPoints nuevos.
🔑 **La selección es por ÁNGULO, no por line trace** — igual que el viejo [[BP_ConstExplorer]] y que el
gesto de F3: las amebas no tienen colisión y dársela arriesga romper el agarre y el dibujo.
El **beam sí es visible** (§9 del plan), pero es puramente decorativo: no traza nada.

## Registro de variables

### `A - Constelacion` (instance-editable — las palancas de Beltrán)
| Variable | Default | Rol |
|---|---|---|
| `SpotTag` | `ConstSpot` | Tag de los TargetPoints del cielo. |
| `StarGap` | 0,35 s | Cada cuánto aparece una estrella. 20 × 0,35 = **7 s** de aparición. |
| `bSkipMine` | true | No spawnear una copia de MI entrada: mi ameba real ya viajó a `soul_pick_6`. |
| `FadeTime` | 2,0 | (reservado para el apagado) |
| `AimConeDeg` | 9° | Cuán fino hay que apuntar. **La palanca de comodidad.** |
| `PollTime` | 0,12 s | Cada cuánto se rastrea. No hace falta por frame. |
| `FocusTag` | `portrait_soul` | Dónde baja el vecino apuntado. |

### `D - Test` — **todas quedan en `false`**
`bDebugBuildOnPlay` + `DebugBuildDelay` (3 s) · `bDebugExploreOnPlay` + `DebugExploreDelay` (2 s) ·
**`bDebugCycle`** + `DebugCycleTime` (4 s) = recorre los vecinos **solo**, sin manos. 🔴 Es la única
forma de probar F5 en PIE: los mandos no están trackeados sin visor.

### Estado (interno)
`ArchRef` · `PickRef` · `MeshBank` (StaticMesh[]) · `Spots` (Actor[]) · **`Spawned`** (ProtoSoul[]) ·
**`Indices`** (int[], paralelo a `Spawned`: qué entrada del archivo es cada estrella) · `Cursor` ·
`SpotCursor` · `Total` · `bBuilt` · `bExploring` · `HoverIdx`/`HoverRef` · `BestDot`/`BestIdx`/`BestRef` ·
`AimOrigin`/`AimDir` · `FocusPoint` · `PawnRef`/`SensRef`/`PortRef`/`CanvasRef`.

⚠ **`Spawned[i]` ↔ `Spots[i]`**: `SpotCursor` y el push a `Spawned` avanzan **juntos**, sólo en la rama
que spawnea. Por eso `Unfocus` puede mandar la estrella de vuelta con `Spots[HoverIdx]`.

## 🔴 Las trampas que se pagaron acá

1. 🔴🔴 **`bind` de un getter de variable NO es una foto: el getter se RE-LEE en cada consumidor.**
   `GradualOne` hacía `(bind _c (GetCursor))` → `SetCursor(_c+1)` → `SpawnStar(_c, …)`, y `SpawnStar`
   recibía **el valor nuevo**: se salteó la entrada 0 y pidió la 20 (que no existe).
   El compilador **copia el bytecode del nodo puro por CADA consumidor** (`bp-lean-construction` §g),
   y un getter de variable es un nodo puro. **Regla: nunca pongas un `Set` entre dos consumidores
   de un mismo `bind`; hacé primero la llamada que lo lee y después el `Set`.**
   👉 La firma del bug en el log: `Attempted to access index 20 from array 'Variants' of length 20`
   y una serie de datos corrida un lugar (los anillos arrancaban en la entrada 1).
2. ⚠ **Los `b` con prefijo no se escriben como los imprime el `read`.** El `read` muestra `(|SetbSkipMine)`;
   el **write** necesita **`Variables|<Categoria>|SetSkipMine`** (sin la `b`, y con la categoría real).
   `bDebugBuildOnPlay` → `SetDebugBuildonPlay` (**la `O` de "On" queda minúscula**).
3. ⚠ **Cambiar la CATEGORÍA de una variable cambia su path en el DSL.** Poner `AimConeDeg` en
   `A - Constelacion` hizo que `Variables|Default|GetAimConeDeg` dejara de existir. **Escribí los grafos
   primero y categorizá después**, o usá la categoría final desde el principio.
4. 🔴 **Las instance-editable nuevas nacen en CERO en el actor ya colocado.** Pasó dos veces en esta
   jornada (`AimConeDeg`=0, `PollTime`=0, `FocusTag`=None; y `ConstHold`=0, `ExploreSeconds`=0 en el
   director). **Después de agregar una variable de autor, escribirla también en la INSTANCIA.**
   Si el actor se coloca *después* de fijar el CDO, hereda bien — por eso el orden importa.
5. ⚠ **`add_to_scene_from_asset` no sirve para un TargetPoint** (no es un asset): es
   **`add_to_scene_from_class`** con `/Script/Engine.TargetPoint`. Y el transform **no se aplica**:
   hay que setearlo después en el `rootComponent` (`relativeLocation` + `relativeScale3D`).
6. ⚠ **`Math|Vector|vector+vector` / `vector*vector` es sólo cómo lo IMPRIME el read.** Para escribir:
   los operadores del DSL, `(+ a b)` y `(* v f)`.
7. ⚠ **`CallFunction|X` con parámetros necesita KEYWORDS.** Posicional, el primer argumento se va al pin
   `self` (*"Could not connect pin VOEnd1 to self"*). Y el keyword es el **nombre real del pin**:
   `Rearm` lo llama `NewTag`, no `ChosenTag` — el error lo lista.
8. ⚠ **`remove_function_graph` → `add_function_graph` sin `compile_blueprint` en el medio devuelve `Nombre_0`.**
   Y el compile intermedio **falla** (los llamadores no encuentran la función): ese error es esperado y
   hay que dejarlo pasar. Al re-agregar con el nombre bueno, los llamadores **se re-resuelven solos**.

## Dónde se lo llama
[[BP_Director_Story]] `RunEnding`: **sub 9** `ShowConstellation` → `Build()` (espera `ConstHold`),
**sub 10** `StartExplore` → `StartExploring()` (espera `ExploreSeconds`), **sub 11**
`StopExplore` → `StopExploring()` + `FadeOut()` junto con el VO 33.

## TODO
- [ ] 🔴 **Visor**: si 9° es cómodo para apuntar estrellas a ~6,5 m, y si el beam se ve bien.
- [ ] 🔴 **Mover `TP_signature_spot`**: hoy sigue al lado de `soul_pick_6` (arriba, en el cielo). Ahora
      es el atril del dibujo — tanto del propio (durante el retrato) como del vecino (durante la
      exploración), así que va **junto al panel**, no arriba.
- [ ] Crossfade corto de melodía al cambiar de vecino (hoy corta y arranca).
- [ ] Feedback visual en la estrella apuntada antes de que baje (hoy sólo baja).
- [ ] Medir en APK: 20 amebas + hasta 100 anillos procedurales a la vez es lo único simultáneo pesado.
- [ ] La **posición y escala de los 20 TargetPoints** las autora Beltrán (hoy: arco de 72° en dos filas,
      elevaciones 17° y 30°, radio ~646 cm desde (7500,0,150), escala 1,2).

## Relacionados
[[BP_SoulArchive_SC]] (de dónde salen los datos) · [[BP_ProtoSoul_SC]] (`MoveToActor`, `Configure`, `SeedRings`) ·
[[BP_Portrait_SC]] (`ShowIndex`) · [[BP_Sensor_Soul]] (`ExploreOn`/`AimBeams`) · [[BP_DrawCanvas]] (`RebuildFrom`) ·
[[BP_Director_Story]] · [[BP_Constellation]] / [[BP_ConstExplorer]] (los viejos, de referencia)


---

# 🔄 2026-08-27 (2ª tanda) — **la tarjeta pasó a vivir DENTRO de la ameba**

> Cambio de arquitectura pedido por Beltrán mirando el PIE: *"cada ameba tiene su propio cuadro […]
> ¿no será más lógico poner el blueprint del gráfico dentro del blueprint de la protoameba?"*.
> Tenía razón: el dato es **de** cada usuario, y que todas viajaran al mismo atril se leía enredado.
> Lo de abajo **reemplaza** el modelo de "atril compartido" descrito más arriba.

## Cómo quedó

```
Focus()
  PullAnchor()        el ancla se coloca sobre la recta estrella→ojo, a FocusPull de la estrella
                      y gira SÓLO EN YAW (mirando desde el ojo) para que la tarjeta quede derecha
  HoverRef.MoveToActor(ancla)     la estrella se acerca POR SU PROPIO RUMBO, no a un punto común
  CardFrom(ArchIdx)   → HoverRef.ShowCard(calma, ritmo, respiración, CardTitle)
  DrawNeighbour()     → Canvas.RebuildFrom(dibujo) → PlaceSign() → Sensor.ShowSignature()
  PortRef.FeedMelody(ArchIdx)     sólo la melodía; el panel viejo ya no se enciende
Unfocus() → SendHome() → HoverRef.HideCard() + MoveToActor(su estrella)
```

**La composición viaja entera**: ameba al centro, **tarjeta 155 cm abajo**, **dibujo 220 cm al costado**
(`SignSide`). Nada queda en un lugar fijo.

`PlaceSign()` mueve el `TargetPoint` `signature_spot` **en runtime** al costado del ancla y recién ahí
llama a `ShowSignature()` — así se reusa entero el colocador del sensor sin tocarlo. ⚠ El movimiento es
sólo de runtime (no persiste), pero **la posición autorada de ese punto sigue importando** para el
momento del retrato PROPIO, que ocurre antes.

## 🔴 El límite que decidió el diseño: 20 paneles no entran en Quest

Beltrán supuso que con una sola visible no se paga. **No es así: esconder un `WidgetComponent`
(`SetVisibility(false)`) NO libera su render target.** 20 tarjetas de 1600×900 = **115 MB** de render
targets más 20 pasadas de `OnPaint` con `DrawLines`.

✅ **La salida**: el componente existe en las 20 con **`WidgetClass = None`**; al enfocar se crea el
widget (`CreateWidget` + `SetWidget`) y al desenfocar se libera (`SetWidget(None)`). **Un solo render
target vivo, garantizado** — verificado en el log: un `WBP_Portrait_SC_C_N` nuevo por vecino.
Y se quedó en UMG (no mallas) porque **el render target se paga cuando se REDIBUJA, no por existir**, y
porque irse a mallas costaría el Designer, que es donde Beltrán autora mirando.

## 🔴 Dos números que estaban mal, medidos y corregidos

1. **El usuario NO está en (7500, 0, 150).** Medido con
   `GetActorLocation(GetPlayerCameraManager(0))`: **X = 7151,7 · Y = 0 · Z = 0** (en PIE; con visor el
   ojo sube a ~120). Eran **3,5 m** de error, y por eso todo se veía chico y lejos.
   👉 La geometría se rehízo alrededor del ojo real, con **R = 983 cm** — la misma profundidad a la que
   está `TP_soul_pick_6_final`, o sea la ameba propia.
2. **La escala se aplicaba dos veces.** `SpawnActorFromClass` con el transform completo del TargetPoint
   metía la escala en el ACTOR, y después `AnchorStep` la volvía a aplicar vía `Size` sobre el `Body`:
   0,35 pedido → **0,1225** real; 1,2 pedido → **1,44**. Ahora se spawnea con
   `MakeTransform(location, rotation, VectorOne)` y `Size` es el único dueño del tamaño.
   ✅ La aserción de `Report` lo confirma: `escala del cuerpo = 0.35`, clavada al TargetPoint.

## 📐 La disposición actual (y la fórmula para cambiarla)

**5 filas × 4 columnas, sin columna central** — el hueco del medio es para la ameba propia.

| | |
|---|---|
| Ojo del usuario | (7151,7 · 0 · 120) |
| Radio | 983 cm |
| Azimuts | −33° · −11° · +11° · +33° |
| Elevaciones | 1° · 8° · 15° · 22° · **29°** (la más alta; 34° se sentía mucho para mirar sentado) |
| Escala de cada punto | 0,5 |
| Separación mínima | **120 cm** |
| Diámetro del anillo | **83 cm** → 37 cm de aire |
| Distancia a `soul_pick_6` | 173 cm |

🔑 **La fórmula que hay que tener a mano antes de repartir amebas en el espacio:**
```
radio visible de una ameba  =  RingRadius × (escala / RingSizeRef)  =  83 cm × escala
```
No sirve mirar el diámetro del cuerpo: **manda el halo de anillos**. Con escala 1,2 son anillos de 2 m;
con 80 cm de separación, un muro (fue exactamente lo que pasó en la 1ª tanda).

⚠ **`TP_soul_pick_6_final` está en escala 1,5** → la ameba propia tiene un halo de **250 cm de diámetro**
y la estrella más cercana está a 173 cm: se le mete ~9 cm encima. Es un valor de autor de Beltrán, no se
tocó. Para que despeje tendría que estar en **≤ 0,9**.

## Variables nuevas de esta tanda

| Variable | Categoría | Default | Rol |
|---|---|---|---|
| `FocusPull` | A - Constelacion | 400 cm | Cuánto se acerca la estrella apuntada. De 983 → **583 cm**. |
| `CardTitle` | A - Constelacion | `SOMEONE WHO WAS HERE` | El título de la tarjeta del vecino (el retrato propio sigue diciendo `YOUR TRACE`). |
| `SignSide` | A - Constelacion | 220 cm | A qué costado del ancla se coloca el dibujo. |
| `FocusPoint` | interna | — | `TP_const_anchor` (tag `const_anchor`), el **ancla móvil**. Su ESCALA es el tamaño de la estrella enfocada. |

## Lo que se verificó
- **12 vecinos seguidos** con series distintas (`180/180/4` → `/5` → `/6` → `/7`), melodías distintas y
  su dibujo (`firma del vecino reconstruida` + `la firma aparece junto al alma`, 10/10).
- `escala del cuerpo = 0.35` (y después 0,5) — las estrellas **se ven**, no es un conteo de actores.
- Título `SOMEONE WHO WAS HERE` leído en captura.
- Cero `Accessed None` en todas las corridas.

## ⚠ Lo que NO viaja todavía
Las **esferas de la melodía** siguen naciendo relativas al transform de [[BP_Portrait_SC]], o sea en el
atril viejo, mientras la ameba, su tarjeta y su dibujo están en otro lado.


---

## 2026-09-02 — la tarjeta del vecino pasó a la CARTA física

El panel por-ameba (`ShowCard`/`HideCard` dentro de [[BP_ProtoSoul_SC]]) se reemplazó por **una sola
carta física** [[BP_Card]], que se re-alimenta con la entrada del archivo de cada vecino.

| Función | Antes | Ahora |
|---|---|---|
| `CardFrom(ArchIdx, Soul)` | `Soul.ShowCard(calma, ritmo, respiración, `CardTitle`)` | **`Card.ShowFor(Soul, ArchIdx)`** |
| `DrawNeighbour(ArchIdx)` | `DrawNow` reconstruía el dibujo y `PlaceSign` lo ponía al lado de la ameba | **vaciada** — el dibujo va al hueco de la carta |
| (en `Focus`) `PortRef.FeedMelody` | sembraba las esferas del vecino | **vaciada en `BP_Portrait_SC`** — las siembra la carta |

🔑 **`Focus` NO se tocó.** Su cuerpo tiene un `AI|Navigation|MovetoActor` que **puede ser un rótulo
equivocado del read** (el `MoveToActor` de la ameba colisiona de nombre con el de IA — verificado ese
mismo día en otro Blueprint, donde el DSL sí cableó el de IA en silencio). Reescribir `Focus` desde el
`read` habría cambiado esa llamada. La cirugía se hizo en las tres funciones hoja.

✅ **Verificado en PIE (Simulate)**: 12 vecinos sembrados (`bDebugSeedFakes`), **19 estrellas**
construidas, y con `bDebugCycle` la carta recorre `vecino 0 → 1 → 2 → 3 → 4 → 5…` re-alimentando curvas,
ameba, dibujo y melodía en cada salto.

⬜ **Composición pendiente**: la carta queda **dentro de la nube de estrellas** (ella en X=7640, las
estrellas a radio 983 del ojo en 7151), así que varias amebas se cruzan por delante del panel.

🧹 Barrido de huérfanos: 90 nodos borrados en este BP (`SpawnStar`, `DressStar`, `ForceHover`,
`DrawNow`, `CardFrom`, `DrawNeighbour`) con `identical: true` — la lógica viva quedó intacta.


---

## 2026-09-02 (tarde) — el hover, hecho SIMPLE de una vez

Beltrán: *"cada vez que apunto a una ameba se agranda más y más y más. Incluso una se empezó a mover.
Esa mecánica debe ser super simple: hover → se agranda y muestra tarjeta; no hover → vuelve a su tamaño
normal, no muestra tarjeta."*

### 🔴 El crecimiento infinito: escala RELATIVA en vez de ABSOLUTA
`GrowHovered` hacía `nueva = escala_actual_del_spot × HoverGrow`. Al re-entrar el hover sobre la misma
ameba, leía la escala **ya agrandada** y volvía a multiplicar → **1,35 → 1,82 → 2,46 → …** sin techo.
✅ **Arreglo: nunca leer la escala viva.** `SpotScales` (array de float) guarda la escala **original** de
cada spot **una sola vez** (`EnsureSpotScales`, llenado perezoso en el primer hover, cuando todos están
todavía en su valor autorado). A partir de ahí:
```
hover    →  spot.Scale = SpotScales[i] × HoverGrow      (absoluto, nunca acumula)
sin hover→  spot.Scale = SpotScales[i]                  (RestoreSpot)
```
`GrownIdx` (int) reemplaza al `GrownSpot` (Actor): se guarda **el índice**, no el actor, para poder
restaurar siempre por la tabla.
👉 **Regla: un efecto reversible (hover, énfasis, selección) se calcula SIEMPRE desde un valor base
guardado, jamás leyendo el estado actual — si no, cada repetición se compone sobre la anterior.**

### La que "se empezó a mover": `SendHome` usaba el índice EQUIVOCADO
`SendHome` hacía `MoveToActor(HoverRef, Spots[HoverIdx])` leyendo **`HoverIdx` en el momento de salir**,
que para entonces **ya podía ser el de otra ameba** → mandaba la que se estaba soltando al spot de la
nueva.
✅ Como en la mecánica nueva **ninguna ameba viaja nunca**, `SendHome` quedó reducida a `ShrinkPrev()`.
Sumado a que en `Focus` ya se había borrado el `MoveToActor` y a `FocusPull = 0`, **no queda un solo
nodo que mueva una estrella**.

### El contrato, ahora en una línea
| Evento | Qué pasa |
|---|---|
| **Hover** | `GrowHovered` (escala base × 1,35, en su sitio) + `CardFrom` → `Card.ShowCopyFor(...)` |
| **Sin hover** | `ShrinkPrev` (vuelve a la base) + `HideCardPanel` → `Card.Hide()` |
Nada se mueve, nada se acumula, y sirve igual para las 20.


---

## 2026-09-02 (noche) — el hover, por fin correcto

Dos fallos que quedaban: *"al quitar el hover nunca vuelven a su tamaño; se quedan todas agrandadas"* y
*"el radio de hover está muy grande, debe ser sólo el contorno del mesh"*.

### 🔴 No restauraban: restauraba por ÍNDICE, y los índices no están alineados
`ShrinkPrev` hacía `Spots[GrownIdx].Scale = SpotScales[GrownIdx]`. Pero **`Spots` tiene los 20
TargetPoints y `Spawned` sólo las estrellas creadas (19, porque `bSkipMine` saltea la propia)**: el índice
del hover no indexa la misma cosa en las dos listas, así que se agrandaba una y se "restauraba" otra —
o ninguna.
✅ **Arreglo: restaurar POR REFERENCIA, nunca por índice.** El spot se le pide **a la propia ameba**
(`GetTargetRef(HoverRef)`), se guarda esa referencia en `GrownSpotRef` junto con su escala en
`GrownBase`, y `ShrinkPrev` restaura exactamente ese actor. Sin tablas paralelas que puedan desalinearse.
🗑 Se borraron `SpotScales`, `GrownIdx`, `GrownSpot`, `GrownScale` y las funciones `EnsureSpotScales`,
`RestoreSpot`, `ApplyGrow` — el andamiaje del intento por índice.

👉 **Regla: cuando dos listas describen "lo mismo" pero se llenan en momentos o con filtros distintos,
no se pueden indexar cruzado.** Si hay una referencia directa al objeto, usarla.

### 🔴 El radio: la INSTANCIA tenía 14°, no los 9° del Blueprint
A los ~9,8 m de radio de la constelación, **14° son 2,4 m de radio de enganche** — de ahí que
"cualquier lado" activara el hover. (Y otra vez: el valor de la instancia le ganaba al del Blueprint.)
✅ **`AimConeDeg = 6°`** en CDO **e instancia** → ~1,0 m a esa distancia, del orden del tamaño de la
ameba. Es la perilla si hay que afinarlo: menos grados = más preciso.
⚠ La detección es **por ángulo**, no por trace contra el mesh (las amebas no tienen colisión, por eso se
eligió así). "El contorno exacto del mesh" requeriría darles colisión; 6° es la aproximación fiel.

### El contrato, ya sin excepciones
| Evento | Qué pasa |
|---|---|
| **Hover** | esa ameba crece **en su sitio** (`base × 1,35`) + aparece su carta |
| **Sin hover** | vuelve a su base exacta + se va la carta |
Ninguna se mueve, ninguna acumula, y vale igual para las 20.


---

## 2026-09-02 (cierre) — por qué el arreglo anterior NO podía funcionar

El log de Beltrán tiene una **ausencia** que vale más que cualquier mensaje:
```
CONSTELACION: miro al vecino 0 → 8 → 16 → 3 → 2      (Focus corre, y mucho)
...y NUNCA aparece "CONST: hover fuera, tamano restaurado"
```
Ese print vive **dentro** del `IsValid` de `ShrinkPrev`. Que no salga ni una vez prueba que la referencia
guardada **siempre fue inválida** — o sea que mis dos intentos (por índice y por referencia al spot)
**nunca tocaron nada**: agrandaban y restauraban un objeto que no existía.

### La causa de fondo: le estaba escribiendo al objeto equivocado
Los dos intentos escalaban **el `TargetPoint`** de la estrella. Pero `GetTargetRef(HoverRef)` devuelve
**null** para las estrellas de la constelación: se colocan y dimensionan **en el spawn**
(`CONSTELACION: estrellas = 19 | escala del cuerpo = 0.5`), no siguiendo un ancla. Sin `TargetRef` no hay
`AnchorStep`, y escalar el spot no mueve ni una aguja.
✅ **Arreglo: escribirle el tamaño A LA AMEBA.** `GrowHovered` guarda `GrownSoul` (la ameba, no el spot)
y su `GrownBase = GetSize(alma)`, y aplica `SetSize(base × HoverGrow)`. `ShrinkPrev` hace
`SetSize(base)` sobre esa misma referencia. Verificado que ambos nodos apuntan a
**`BP Proto Soul SC Object Reference`** (el `read` los rotula mal como `Widget|SetSize` / `SharedImage|GetSize`).
🔑 Y es seguro que persista: en la constelación **nada pisa `Size`**, porque el único que lo haría
(`AnchorStep`) está detrás del guard `IsValid(TargetRef)` que aquí nunca pasa.

### 🔴 La lección de método (tres intentos fallidos seguidos)
Los tres arreglos partieron de **suponer** por dónde se controla el tamaño, sin medir. La medición que lo
resolvió fue **mirar qué print NO aparecía** — una ausencia en el log vale tanto como una presencia.
👉 **Antes de escribir el arreglo: un print que confirme que la rama se ejecuta y con qué valores.**
Ahora los hay en las dos funciones (`CONST: hover, de X` / `CONST: hover fuera, vuelve a X`), así que la
próxima corrida dice el número en vez de dejarnos adivinar.


---

## 2026-09-02 (final) — el hover como ESTADO, no como pulso

Beltrán: *"mientras el hover está activo debe mantenerse en la escala grande. Ahora hace un pulso rápido
y vuelve. Apuntarla es como que la tuviera seleccionada, esa es la idea."*

### 🔴 `Resolve` no tenía caso "dejé de apuntar"
```
if (BestDot > cos(cone)) AND (BestIdx != HoverIdx):   → Unfocus + timer a Focus
```
**Sólo actuaba al CAMBIAR de ameba.** Si dejabas de apuntar, `BestDot` no superaba el umbral, la condición
fallaba y **no pasaba nada**: `HoverIdx` seguía apuntando a la última y nadie la achicaba. Eso explica
*"quedan todas agrandadas"*. Y el achicado que sí se veía venía del `Unfocus` **del cambio**, que
restauraba antes de que el timer volviera a agrandar → **el pulso**.

### ✅ Ahora es una máquina de dos estados
| | |
|---|---|
| **`ResolveHit`** (hay algo apuntado) | sólo si `BestIdx != HoverIdx`: fija el nuevo índice y arma `FocusDelayed`. **No achica nada** — de eso se encarga `GrowNow` en el mismo frame en que agranda, así **no hay instante en tamaño chico**. |
| **`ResolveMiss`** (no hay nada apuntado) | **este caso no existía**: suelta el hover — `ShrinkPrev` + `HideCardPanel` + `HoverIdx = -1`. |

Y **`GrowHovered` es idempotente**: `if (HoverRef != GrownSoul) → GrowNow`. Aunque `Focus` se dispare de
más, la ameba ya seleccionada **no se vuelve a tocar**. Se agranda una vez y **se queda**.

🗑 `FadeDrawOut` volvió a su única tarea (apagar el dibujo) y `SendHome` quedó como traza. Ninguna de las
dos toca la escala ni la carta: el cambio de vecino ya no apaga y prende nada.

👉 **La lección (la dijo Beltrán y es de manual): un hover es un ESTADO con entrada y salida**, no un
efecto que se re-aplica. Si el código sólo sabe reaccionar al *cambio*, le falta justamente la mitad —
el momento en que el estado se **suelta**.


---

## 2026-09-02 (cierre real) — el pulso era el SCAN, y el hover ya estaba hecho

Beltrán, después de tres intentos míos: *"es el mismo estado que al principio, cuando el usuario elige su
ameba: mientras está en hover está más grande y si la suelta vuelve. Esa lógica es super simple."*
**Tenía razón en las dos cosas** — el diagnóstico y la solución.

### 🔴 El pulso: yo soltaba al PRIMER frame sin detección
El log lo muestra sin ambigüedad:
```
miro al vecino 12  →  CONST: SELECCIONADA  →  CONST: sin hover - se suelta   ← el mismo suspiro
```
`PollHover` corre **cada frame** y reinicia `BestDot = -2`. Con el cono en 6°, **un temblor de mano basta
para no superar el umbral en un frame**, y mi `ResolveMiss` soltaba de inmediato. Al frame siguiente
volvía a enganchar → **parpadeo**. No era un problema de escala: era el **scan sin histéresis**.

✅ **Histéresis, la solución de manual**: se **entra** con `AimConeDeg` (7°) y sólo se **sale** con
`AimConeOut` (14°, blindado con `Max(10,…)`). Entre los dos umbrales **no se toca nada** y el hover
**se mantiene**. Un cono de entrada preciso, uno de salida indulgente.

### 🔴 Y la escala ya estaba resuelta en el proyecto
`BP_ProtoSoul_SC` **ya tiene su hover nativo**, el mismo que usa la elección del alma:
`bHovering` → `StepHover` interpola `HoverT` (con `HoverTime` 0,25 s) → `ApplyHoverScale` aplica
`Size × (1 + (HoverScale−1) × HoverT)` con **`HoverScale` 1,425 ya autorada**.
✅ **La constelación ahora sólo dice `SetHovering(true/false)`.** Nada de tocar `Size`, ni guardar
escalas base, ni restaurar a mano: el suavizado, la escala y la reversibilidad **ya existían**.

🗑 Se fue todo lo que había construido de más: `SetSize` manual, `GrownBase`, `GrowTmp`, escalado de
spots, tablas de escalas y funciones auxiliares.

### 👉 La lección, que es la regla #1 de este repo y me la salté cuatro veces
**Antes de construir una interacción, buscar si ya existe y está probada.** El hover con escala llevaba
meses funcionando a dos Blueprints de distancia. Construí tres versiones propias —por índice, por spot,
por `Size`— y las tres eran peores que llamar a **una función de una línea**. El síntoma de que estaba
en el camino equivocado estuvo desde el principio: **cada arreglo necesitaba más andamiaje que el
anterior**.


---

## 2026-09-02 (definitivo) — ADIÓS CONO: el hover es el BEAM, el mismo de Attracting

Beltrán, después de que yo hiciera **cuatro** versiones propias del hover:
> *"Olvidate del cono. Estamos usando el beam, es el mismo sistema que en Attracting.
> Para qué inventamos cosas. Todo esto está construido, llevamos 1 mes armándolo.
> Las mecánicas siempre se repiten, no es nada tan complejo."*

**Tenía razón en todo.** El mecanismo ya existía, probado en visor, y es de dos líneas.

### El sistema real (`BP_Sensor_Soul` + `BP_SoundOrb_SC`)
```
Sensor.TickBeamR/L :  LineTraceByChannel desde el Aim  →  BeamHitActor / BeamHitActorL
Orbe.RefreshHover  :  Hovered = (BeamHitActor == self) OR (BeamHitActorL == self)
```
Eso es **todo**. El objeto pregunta *"¿el beam me apunta a mí?"* — sin conos, sin dot products, sin
histéresis, sin umbrales de entrada y salida.

### Lo que quedó en la constelación
| Función | Ahora |
|---|---|
| `ScanOne(Idx)` | `if (BeamHitActor == estrella) OR (BeamHitActorL == estrella) → BestIdx = Idx` |
| `Resolve` | `if BestIdx != -1 → ResolveHit ; else → ResolveMiss`. **Sin conos.** |
| `GrowNow` / `ShrinkPrev` | `SetHovering(true/false)` — el **hover nativo de la ameba**, con su `HoverScale` 1,425 y su suavizado de 0,25 s, el mismo que en la elección del alma |
| `MakeHittable(Soul)` (nueva, la llama `DressStar`) | le da colisión al `Body` de cada estrella (`BlockAll` + `QueryOnly`) para que el `LineTrace` la golpee — **exactamente lo que tienen las esferas de Attracting** (`QueryAndPhysics` + `BlockAll`) y le faltaba a la ameba (`NoCollision`) |

🗑 Se borró todo lo que había inventado: escaneo por ángulo, `AimConeDeg`/`AimConeOut`, `BestDot`,
`SetSize` manual, `GrownBase`, tablas de escalas base, escalado de spots.

### 🔴🔴 La lección, que es la REGLA #1 del repo y la ignoré cinco veces seguidas
**Antes de construir una interacción: buscar si ya existe y está probada** (`assets-existentes.md`,
`_INDEX.md`). El hover con beam llevaba un mes andando en Attracting y el hover con escala en la
elección del alma. Yo hice cuatro implementaciones propias, cada una con **más andamiaje que la
anterior** — y ese crecimiento era, en sí mismo, la señal de que iba por el camino equivocado.
👉 **Si un arreglo necesita más piezas que el anterior, parar y buscar el que ya existe.**
