# BP_SlotChain_SC + M_SlotChain_SC — el metaball del secuenciador (Core/Attracting/)

> Creado el 2026-09-21 (commit `2256ce8`, "metaball en fila: una gota por slot"). **Tracker escrito el 2026-09-23**, tras una jornada entera de iteración en vivo con Beltrán.
> **Estado: 🟢 aprobado paso a paso por Beltrán en el editor.** ⬜ Sin visor con la mecánica corriendo · 🔴 sin commitear y el nivel sin guardar.

## Qué es
Una gota de metaball **por slot** del secuenciador de Attracting. Raymarch de 8 esferas con smooth-min en un `MaterialExpressionCustom` (mismo linaje que [[BP_MetaBlob_SC]]), sobre el proxy propio **`SM_ChainProxy_SC`** (caja recortada, ver gotchas §350-351). Vive en la estación **`GAL_12`** de `/Game/TestMeshes` como `GAL_12_SlotChain`.

**Lo que el BP le da al material cada frame:** el centro de cada gota (`C0..C7` = posición del slot menos la suya), el radio (`Rad0/1/2`) y el pulso (`Pulse0/1/2`).

## Estructura
| Grafo | Qué hace |
|---|---|
| `UserConstructionScript` | `ApplyAll` → `SetCollisionEnabled(Volume, NoCollision)` |
| `EventBeginPlay` | timer 0,6 s → `BootChain` · **`SetActorEnableCollision(false)`** |
| `EventTick` | si `bBooted`: **`PushCenters` → `PushRadii`** (en ese orden, ver trampa 2) |
| `BootChain` | `ApplyAll` + `bBooted = true` + print |
| `ApplyAll` | `GatherSlots` + empuja **todas** las perillas al material + `PushCenters` |
| `PushCenters` | escribe `C0..C7` (posición del slot − la del chain) y **siembra `Rad0/1/2` planos** |
| `PushRadii` | por bloque de 3 gotas: `VInterpTo` del radio y del pulso → `Rad0/1/2` y `Pulse0/1/2` |

## Las perillas (todas `0-Config`, instance-editable)
| Perilla | Qué hace | Valor en `GAL_12_SlotChain` |
|---|---|---|
| `BlobRadius` `Smooth` `Steps` `ChainBrightness` `PulseAmount` `ColorLow` `ColorHigh` | las originales | 12,1 · 15,2 · 32 · 1,54 · 0,66 |
| 🆕 **`PulseSmooth`** | inercia del pulso: el radio y el tinte persiguen su objetivo con `VInterpTo`. **0 = salto instantáneo (como nació)** | 6 |
| 🆕 **`ColorPulse`** | el tercer color: tiñe la gota por la que pasa el playhead | azul (0 · 0,21 · 1) |
| 🆕 **`TintSpread`** | cuánto se derrama el tinte a las vecinas (multiplica `Smooth` en el kernel) | 2,05 |
| 🆕 **`TintGain`** | intensidad del tinte antes del `saturate` | 2,5 |
| 🆕 **`SizeVariation`** | personalidad fija de cada gota (secuencia áurea, no hash) | 0,47 |
| 🆕 **`MinScale`** | 🔴 **piso del multiplicador de radio**: ninguna gota baja de ese % | 0,5 |
| 🆕 **`EndBoost`** | engorda las puntas (`u²`) para compensar el sesgo del smooth-min hacia el centro | 0,1 |
| 🆕 **`FloatAmount` / `FloatSpeed` / `FloatAlong`** | deriva por gota (cm), su ritmo, y qué parte va **a lo largo** de la cadena | 3 · 0,6 · 0,35 |
| 🆕 **`SwellAmount` / `SwellSpeed` / `SwellWaves`** | la onda que mueve la zona de unión (dos ondas contrapropagantes, **sin dirección**) | 0,3 · 0,12 · 1 |

## Las decisiones que importan (y por qué)
1. 🔴 **El tinte se pondera por MÁXIMO, no por promedio.** Con promedio, las 8 gotas dividen el peso: con los valores reales de Beltrán el alfa del color quedaba en ~0,15 y el azul no se veía. `pw = max(w_j · pulso_j)` con `w_j = exp(−dist_a_esa_gota / (Smooth·TintSpread))` → 1 sobre la gota que pulsa y degradé suave hacia las vecinas.
2. 🔴 **Nada de hashes para repartir 8 cosas.** Las fases del flotado salían de `frac(sin(j·k))` y por azar unas gotas se acompañaban y otras iban en contrafase (síntoma: *"las del medio se unen, las de los extremos nunca"*). Ahora **ángulo áureo** (137,5°) para fases y tamaños: 8 valores repartidos parejo, sin agrupamientos. Mismo criterio para la velocidad de cada gota (no depende de su posición en la fila: eso leía como un barrido).
3. 🔴 **El adorno no puede apagar una gota.** `MinScale` acota el **multiplicador**, no el radio final: una gota que la mecánica apaga de verdad (`RevealT = 0`) sigue desapareciendo.
4. 🔴 **Ninguna animación debe tener dirección**, o compite con el avance del playhead. Por eso la onda de `Swell` son dos ondas en sentidos opuestos con frecuencias inconmensurables.
5. **Determinismo por VR**: todo sale del índice de la gota, nunca del píxel ni del frame — si no, cada ojo vería algo distinto.

## Trampas (pagadas)
1. 🔴🔴 **El Construction Script NO es el lugar para apagar colisión de un actor ya colocado.** No se re-ejecuta en runtime para actores del mapa, ni al mover el actor por MCP. El `BodyInstance` serializado gana. ✅ `SetActorEnableCollision(false)` en **BeginPlay**. Ver gotcha §353.
2. 🔴 **`PushCenters` va ANTES de `PushRadii` en el Tick.** `PushCenters` termina sembrando `Rad0/1/2` planos (para que el metaball se vea en el viewport, donde no hay Tick); si corriera después, pisaría los radios animados y las gotas quedarían todas iguales y quietas.
3. ⚠ **Al mover el arco hay que mover el chain con él.** El proxy es una caja fija centrada en el actor: si el arco se corre, las gotas de las puntas se cortan contra la pared. Medir con `get_actor_bounds` del chain contra las posiciones de los slots.
4. ⚠ Las perillas nuevas **nacen en 0 en la instancia ya colocada** (el clásico [[instance-editable-nace-en-cero]]). Con `PulseSmooth = 0` o `TintGain = 0` el efecto simplemente no existe y parece que el cambio no funcionó.

## Cómo se verifica (sin visor)
- **Qué recibió el material**: `overrideMaterials` del componente `Volume` → el `MID_M_SlotChain_SC_0` → `get_properties(['vectorParameterValues'])`. Ahí están los `C0..C7` reales, que además revelan la geometría del arco.
- **Si algo bloquea un trace**: `SceneTools.trace_world` + **test de identidad** (mover el actor sospechoso y ver si el impacto se mueve con él). 🔴 `get_properties` de `bodyInstance` **miente**: devuelve el valor serializado, no el vivo.

## El arco (2026-09-23)
La fila no es recta: los 8 slots están sobre una circunferencia. Estado final: **radio 70 cm**, centro **30 cm delante del pawn**, arco de **126° (±63°)**, paso 18°, slots centrales a 1,00 m del usuario, z = 80. El chain acompaña en x = 362780.
👉 **Se autora moviendo los slots**: el Construction Script de [[BP_SeqSlot_SC]] busca el chain (`GetActorOfClass` + cast, envuelto por el propio cast) y le llama `ApplyAll`, así el metaball se reacomoda al arrastrar un slot en el viewport. En `L_Attracting_SC` no hay chain: el cast falla y no hace nada.

## Lo que cambió en los vecinos (con default conservador, la obra intacta)
- **[[BP_SeqSlot_SC]]**: `bHideInGame` (bool, **false** por defecto) → `SetHiddenInGame(Marker, …)` en BeginPlay. En true en los 8 slots de la galería: el mesh del slot no se ve en play y queda sólo la gota. Verificado que el Marker no deja colisión fantasma.
- **[[BP_Sequencer_SC]]**: `OrbZOffset` (float, **12** por defecto = como estaba) → el `Setup` de cada esfera lo copia a su `SlotZOffset`. En **0** en la galería: la esfera se ancla en el **centro exacto del blob** (los centros del metaball son la posición del slot, sin offset).

## TODO
- [ ] 🔴 **Visor** con la mecánica corriendo (hoy todo se juzgó en el editor).
- [ ] 🔴 **Guardar el nivel** (las ~15 perillas de la instancia y las posiciones de 9 actores) y commitear.
- [ ] **Las esferas de sonido** (lo que sigue): ⚠ el proxy translúcido hace depth-test en su cara delantera (§351) y la esfera ahora está **dentro** de la caja → se pinta por encima del metaball en vez de quedar envuelta por la gota.
- [ ] Medir el costo en Quest: el march es `Steps × BlobCount` = 32 × 8 y el proxy es grande en pantalla.

## 🆕 2026-09-23 (tarde) — la esfera anclada adopta el tamaño de SU gota
Pedido: *"al anclarse, cada esfera adopta un tamaño según el blob, que siempre esté contenida al
centro, que nunca quede más grande, adaptándose a que los blobs van cambiando de tamaño"*.

Tres funciones nuevas, y el Tick pasa a `PushCenters → PushRadii → PushOrbSizes`:

```
GetBlobRad (Index) → float
  switch int sobre los 8 índices; devuelve la componente que toca de RadS0/RadS1/RadS2
  (el radio VIVO e interpolado que PushRadii ya calcula: BlobRadius · RevealT · (1 + PulseT·PulseAmount))

GetBlobFitScale (Index) → float
  fac = max(1 + SizeVariation·sin(j·2.39996) + EndBoost·u² − SwellAmount, clamp(MinScale,0,1))   u = |2·(j/7) − 1|
  🔴 el clamp NO es decorativo: el HLSL hace max(fac, **saturate**(MinScl)). Sin saturar,
     un MinScale autorado en 1,51 ponía un piso de 1,51 en el BP contra 1,0 en el shader
     → la esfera anclada salía ~50% más grande que su gota (2026-09-24).
  return GetBlobRad(j) · fac · 0.02        ← 0.02 = 1/50, el radio de SM_AlmaSphere

PushOrbSizes ()   (en el Tick)
  for j in 0..min(len(Slots),8)-1
     occ = Slots[j].Occupant ; if IsValid(occ) → occ.AnchorSize = GetBlobFitScale(j) · OrbFit
```

🔴 **Por qué `fac` se replica en Blueprint:** el radio que el BP empuja (`RadS`) es sólo la base con
el pulso; **el shader vuelve a multiplicarlo** por la variación de tamaños, el `EndBoost` y la onda
`Swell`. Si la esfera se dimensiona contra `RadS` a secas, en la gota que el shader achica se sale.
El `− SwellAmount` (en vez de seguir la onda en vivo) es deliberado: toma el **mínimo** que esa gota
puede llegar a medir, así la contención se cumple en todo momento sin replicar senos por frame.

⚠ Si algún día cambian `SizeVariation`, `EndBoost`, `SwellAmount` o `MinScale` **en el HLSL**, hay
que tocar `GetBlobFitScale` también — es la única fórmula duplicada entre el material y el BP.

| Perilla nueva | Default | Qué hace |
|---|---|---|
| `OrbFit` (0-Config) | 0,8 | fracción de la gota que ocupa la esfera anclada. 1 = toca la pared, >1 se sale |

💡 El puente con la esfera es **`AnchorSize` de [[BP_SoundOrb_SC]]**: el chain se lo escribe por
frame mientras esté ocupada, y el orbe ya interpolaba su escala hacia esa variable. Cero cirugía en
el Tick del orbe. En la obra no pasa nada porque ahí `bUseAnchor` es false y `AnchorSize` no se lee.

## 🆕 2026-09-23 (cierre) — la esfera anclada ES la gota: centro y tamaño en vivo
Pedido final: *"debe tomar el centro del blob, actualizándose real time según como se mueve y flota
· tamaño al 90% del blob, actualizándose según se va agrandando · si muevo de un snap a otro, el
ajuste de tamaño y posición también sucede en tiempo real"*.

🔴 **El flotar de las gotas SE MUDO del shader al Blueprint.** Antes lo calculaba el HLSL sobre
`P[j]`, así que el Blueprint no sabía dónde estaba realmente dibujada cada gota y la esfera no podía
seguirla. Ahora:

```
GetBlobOffset (Index) → Vector     la deriva de la gota j (las 3 senoidales del shader,
                                   menos su componente a lo largo de la cadena según FloatAlong)
GetBlobCenter (Index) → Vector     Slots[j].location + GetBlobOffset(j)   ← el centro REAL
PushCenters                        empuja C0..C7 = GetBlobCenter(j) − actorLoc
                                   y **`FloatAmount = 0` al material** para que el shader no lo sume dos veces
PushOrbSizes                       por slot ocupado: AnchorSize = GetBlobFitScale(j)·OrbFit
                                   TargetLoc = GetBlobCenter(j)
                                   y si el orbe NO está Moving ni Grabbed → SetActorLocation(centro)
```

💡 **La razón de mudarlo en vez de replicarlo:** replicar el seno en BP obliga a que el `Time` del
material y el del juego coincidan, y si no coinciden la esfera deriva **en contrafase** con su gota
— peor que no flotar. Con el cálculo en un solo lado la coincidencia es exacta por construcción.
Es el mismo aprendizaje que el Ganzfeld: *¿quién más escribe este output?*

⚠ En el **editor** la gota sigue flotando por el shader (el Tick no corre, `ApplyAll` empuja el
`FloatAmount` autorado). El `= 0` sólo pisa en juego. Si algún día el actor del chain se **rota**,
la deriva habría que rotarla también: hoy se asume rotación identidad.

⚠ La esfera anclada ya **no usa** el `OrbZOffset` del secuenciador: va al centro exacto de la gota.

## 🆕 2026-09-24 — la esfera agarrada FUNDE con el metaball (novena gota)

Pedido: *"¿es posible que al acercarlos al metaball se atraigan un poco con el blob cercano? como si
fueran parte del metaball… hablo de atraerse con la deformación smooth"*. O sea **fusión visual por
smooth-min**, no atracción de posición.

### El shader: de 8 gotas a 9
`M_SlotChain_SC` → `MaterialExpressionCustom_0`. **Dos entradas nuevas**, `COrb` (float3, LOCAL al
actor) y `ROrb` (float), y cinco líneas de cambio:

```
float3 P[8] → P[9] ;  R[8] → R[9] ;  PU[8] → PU[9]
// después del bucle de adorno (que sigue siendo j<8, la gota 9 NO se decora):
P[8] = COrb ;  R[8] = max(ROrb, 0.001) ;  PU[8] = 0.0
int NA = (ROrb > 0.001) ? (N + 1) : N
// y los DOS bucles del raymarch (superficie y normal/tinte) pasan de j<N a j<NA
```

💡 **Sale gratis en diseño:** al entrar al mismo `smin` que las otras, la novena gota forma
cuello, hereda la normal y el tinte por construcción — no hubo que inventar nada de mezcla.
🔴 **La gota 9 queda FUERA del bucle de adorno** (`fac`, `Swell`, deriva): es un objeto real con su
posición y su tamaño, no un elemento decorativo de la cadena.

### Cómo agregar entradas a un nodo Custom por MCP
No hay tool dedicada: hay que **reenviar el array `inputs` COMPLETO** con `ObjectTools.set_properties`
(30 entradas en este caso) agregando las nuevas al final. El JSON que devuelve `get_properties` es
round-trippable tal cual; las entradas float3 llevan `mask:1, maskR/G/B:1, maskA:0` y las escalares
`mask:0`. Antes hay que crear los `VectorParameter`/`ScalarParameter` y referenciarlos por refPath.

### El puente Blueprint
```
BP_SoundOrb_SC.PushFuse()     ← lo llama SnapApply, o sea sólo cuando la esfera agarrada
                                 está dentro de la SnapZone de algún slot
   SnapSlot.ChainRef.SetFuseOrb( GetActorLocation(), ScaleMul · 50 )

BP_SlotChain_SC.PushOrbFuse() ← en el Tick, al final
   FuseR = FInterpTo(FuseR, 0, dt, FuseFade)      ← se apaga solo si nadie lo refresca
   COrb = FuseLoc − actorLoc  (a local)
   ROrb = FuseR · OrbFuse
```

💡 **El decaimiento evita tener que avisar cuando la esfera se va.** El orbe sólo empuja mientras
está cerca; el chain baja `FuseR` a 0 solo. Nadie tiene que acordarse de limpiar.

| Perilla nueva | Default | Qué hace |
|---|---|---|
| `OrbFuse` | 0,6 | cuánto "pesa" la esfera en el campo. 0 = no funde · 1 = como una gota más |
| `FuseFade` | 8 | qué tan rápido se despega al alejarla |

⚠ La esfera **sigue dibujando su propia malla**: lo que se ve es la gota estirándose hacia ella y
formando cuello de un lado. Para fusión de los dos lados habría que dejar de dibujar la malla y que
la esfera exista sólo como parte del campo — pierde su material y su wobble propios.
⚠ Costo: una esfera más por paso de raymarch en los dos bucles. Medir en la Quest.

## 🆕 2026-09-24 — las esferas usan el MISMO shader (MI_OrbBlob_SC)

En vez de un material propio, **una Material Instance del master del metaball** con `BlobCount = 1`:
cada esfera es un raymarch de una sola gota, con la misma SDF, la misma normal y el mismo sombreado
`ChainColorLow`/`ChainColorHigh`. Comparten master, asi que un cambio al shader les llega a las dos.

- `ChainColorHigh` ← el color de paleta de cada esfera (lo empuja `ApplyLook`)
- `ChainColorLow`  ← el `ShadeColor` global
- **`Rad0` = 42 en espacio LOCAL**: como el raymarch corre en local, donde `SM_AlmaSphere` siempre mide
  50 sin importar la escala del actor, un radio fijo funciona en todos los tamaños sin empujar nada.
- **El segundo lobulo sale gratis del input `COrb`/`ROrb`** que se habia agregado para la fusion:
  `ROrb` 38 + `COrb` = `LookLobe(Index)` (±`LobeOffset`, del mismo hash que reparte colores) → cada
  esfera es un smooth-min de dos bolas, asimetrica y distinta de las demas. ⚠ `LobeOffset + ROrb`
  no puede pasar de 50 o el lobulo se sale de la malla proxy y se corta.
- 🔴 **`MaxT` = 40.000**, no 140 — ver gotcha 367: el rayo arranca en la camara y `MaxT` esta en
  unidades locales, asi que en una malla a escala 0,4 un `MaxT` de 140 son 57 cm de alcance real.

## 🔴 2026-09-24 — el "breath" sincronizado de las esferas era `SwellAmount`
Reporte: *"hay como un movimiento de breath, que las agranda y las achica, y esta sucediendo a la misma vez
en todas, no de forma aleatoria"*.

**Causa, medida antes de tocar:** `MI_OrbBlob_SC` tenia **`SwellAmount` 0,3** y **`SwellSpeed` 0,12**
heredados del master. La onda de union del shader es
`sw1 = sin(2*PI*(pn*SwellWv - T*SwellSpd))`, y **`pn = fj/lastF`**. En la cadena `pn` reparte fase a lo largo
de la fila, pero en una esfera suelta **`BlobCount = 1` → `lastF = 1` → `pn = 0`**: la onda queda como
**funcion pura del tiempo**, identica en las 20 esferas. Multiplica el radio via `fac`, o sea las agranda y
achica a todas al unisono cada ~8 s.

✅ Se le sumo la semilla por esfera a la fase (`+ ps*2.7` / `+ ps*4.1`) y un jitter de ritmo
`sJit = 1 + solo*(frac(ps*0.137+0.31)-0.5)*0.5`. De paso se corrigio el **mismo olvido en `wm`**, el termino
viajero del wobble, que tampoco llevaba `ps` — era el residuo del arreglo del 2026-09-23, donde la parte
estatica `ws` si lo recibio y la movil no.

🔒 **La cadena no se toca, y esta verificado, no supuesto:** todo lo nuevo esta multiplicado por `ps` o
por `solo`, que valen 0 cuando `WobbleAFS.x == 0`. El MID del `Volume` del chain **no tiene override de
`WobbleAFS`**, asi que usa el default del master `(0, 4, 0.35)` → `solo = 0` → `ps = 0` y `sJit = 1`, o sea
las expresiones quedan identicas a las de antes.

🚩 **La forma general, que ya aparecio dos veces en esta estacion:** un parametro pensado para
**repartir fase a lo largo de una fila** (`pn`, indice normalizado) **degenera a una constante cuando la fila
tiene un solo elemento**, y lo que era variedad se vuelve sincronia perfecta. Al reusar un shader de
conjunto para un objeto solitario, revisar TODO lo que dependa del indice.

## ⛔ 2026-09-25 — LA CIRUGÍA DE ABAJO SE REVIRTIÓ ENTERA. El material está como estaba.

**Qué pasó:** la fase **A1 (rayo desde el píxel del proxy) HACE DESAPARECER el metaball de la cadena.**
Lo detectó Beltrán mirando su viewport (*"ya no se ve el metaball del sequencer"*), no mi verificación.
Probado con recortes de la misma cámara en tres estados: el tubo crema está **antes**, **no está** con
la cirugía, y **vuelve** al restaurar (`perf_shots/COMPARA_metaball_3estados.png`).

**Estado actual (guardado en disco):** `code` restaurado byte a byte desde el backup ·
`RayOrigin` ← `MaterialExpressionTransformPosition_2` (cámara, el original) · master `MaxT` 900 ·
`MI_OrbBlob_SC.MaxT` 40000 · los dos nodos que agregué (`WorldPosition_0`, `TransformPosition_0`)
**borrados** · 33 inputs en el Custom, como al principio · canario 152→152.

🔬 **Mecanismo NO identificado** — es lo que falta antes de volver a intentarlo. Los orbes seguían
viéndose con A1 puesto; solo murió la cadena. Diferencias candidatas: proxy caja grande
(256×340×256) con gotas chicas (R≈7,3) y dispersas adentro, contra el proxy esfera del orbe donde la
gota lo llena casi entero. **No volver a tocar `RayOrigin` sin una hipótesis medida.**

### ✅ 2026-09-25 (misma jornada) — A2+A3 RE-APLICADAS solas, verificadas y guardadas
Sin tocar `RayOrigin` ni `MaxT`. Verificado por recorte ×2 (cadena: el tubo crema está en las dos;
orbe: mismo bulto en el preview del MI), PIE `esferas=20` + `pad ON` + cero `Accessed None`, y log
de shaders limpio. Capturas en `VR_Test/Saved/perf_shots/VERIF_A2A3_*.png`.
⬜ **Sin medir en device** — el A/B con `quest_ab.ps1` es el que dice cuánto se ganó. No estimar.

🟢 **A2 y A3 son inocentes, y está probado por lectura, no por opinión:** el master tiene
`WobbleAFS` default **(0, 4, 0.35)** → `WobA = 0` para la cadena → `mW = 0` → la rama else de A3 es
idéntica al original (que ya usaba `stepK = 1.0` con `WobA=0`); y `ROrb` default **0** → `NA = N = 8`
→ `ND = min(8,8) = 8`, el mismo bucle de decoración. Se revirtieron igual, por venir en el mismo
`code`. **Son las dos que valen para los orbes** (20 en pantalla, los únicos con wobble) y se pueden
re-aplicar solas, con la verificación por recorte de §378.

<details><summary>Lo que se había hecho (histórico, NO está aplicado)</summary>

## 🚀 2026-09-24 (noche) — CIRUGÍA DE PERFORMANCE del march (fases A1+A2+A3 del plan)

Contexto y enfoques: [`docs/PLAN-PERF-ATTRACTING.md`](../../../../docs/PLAN-PERF-ATTRACTING.md)
(medición base: [`docs/PERF-ATTRACTING-2026-09-24.md`](../../../../docs/PERF-ATTRACTING-2026-09-24.md)).
🔒 **Backup EXACTO del HLSL anterior:** `scripts/hlsl_backups/M_SlotChain_Custom0_2026-09-24_pre-cirugia.hlsl`
(restaurar = `set_properties` de `code` sobre `MaterialExpressionCustom_0` + `recompile`).

**Los 3 cambios, mismo look por construcción:**
1. **A1 — el rayo arranca en el PÍXEL del proxy**, no en la cámara: `RayOrigin` ← `WorldPosition` →
   `TransformPosition(World→Local)` (nuevo `TransformPosition_0`; la cadena vieja
   `CameraPositionWS_2→TransformPosition_2` quedó huérfana e inofensiva). Con eso **`MaxT` pasa a
   significar "cuánto recorre el rayo DENTRO del proxy"**: `MI_OrbBlob_SC` 40000→**120** (cuerda máx.
   de `SM_AlmaSphere` r50 = 100), default del master 900→**600** (diagonal del box de la cadena ≈ 500).
   💀 La gotcha §367 (MaxT vs escala del actor) muere de raíz: desde la superficie, en local, las
   distancias son ≤ el diámetro del proxy a cualquier escala.
2. **A2 — decoración `j < min(NA,8)`** en vez de `j < 8`: bit-idéntico para todo lo que se marcha
   (la cadena decora sus 8; la gota 9 sigue sin decorarse), y las esferas dejan de pagar 8 gotas de
   senos por una que usan.
3. **A3 — wobble por BANDAS:** el march evalúa primero la SDF **lisa** (sin senos); solo si
   `res < mW + 2·eps` (con `mW = rmax·WobA·1.31`, cota exacta: `smin(a−m,b−m) = smin(a,b)−m` en este
   smin polinómico) evalúa la SDF completa con los 5 senos y el paso 0.7. Fuera de banda avanza
   `res − mW` con paso ENTERO (mejor que el 0.7 global de antes). Con `WobA=0` (la cadena) el camino
   es EXACTAMENTE el original. La isosuperficie la decide siempre la SDF completa → mismo borde.

**Verificación (sin visor — Beltrán fuera de oficina):** capturas con cámaras idénticas antes/después
de cada fase (`VR_Test/Saved/perf_shots/`): idénticas salvo la pose animada. Preview del MI intacto
(⚠ una captura salió NEGRA justo tras el recompile = shader asíncrono en vuelo, gotcha §377).
PIE: `SEQ boot → esferas=20 → pad ON alineado`, **cero `Accessed None`**. Guardado con rutas
explícitas (`M_SlotChain_SC` + `MI_OrbBlob_SC`); **el nivel NO se tocó ni se guardó**.

⬜ **PENDIENTE:** medición A/B en device (`quest_ab.ps1`) cuando Beltrán vuelva a la oficina — el
número decide si hacen falta **A4** (poda por gota en la cadena) y **A5** (re-tunear `Steps` con una
perilla de debug) y el FFR 3 del plan. 🔴 Sin commitear (como todo el día del 24).

⚠ **Incógnita anotada para el enfoque C (malla):** dónde vive el lóbulo de la esfera en runtime —
si `ApplyLook` empuja `COrb`/`ROrb` (P[8], que con N=1 y NA=2 el march NO alcanza) o si va por `C1`.
La cirugía es neutral ante ambas lecturas (min(NA,8) decora exactamente lo que se marcha), pero al
retomar C hay que resolverla leyendo `ApplyLook` del orbe/director.

⚠ **Y la verificación de arriba ("capturas idénticas antes/después") era FALSA** — ver §378 de
gotchas: se comparó el cuadro entero y la cadena es un lavado pálido de bajo contraste, así que su
desaparición total pasó inadvertida.

</details>
