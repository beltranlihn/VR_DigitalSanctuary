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
