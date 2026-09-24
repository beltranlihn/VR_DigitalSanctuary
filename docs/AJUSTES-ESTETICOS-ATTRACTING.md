# Ajustes estéticos — Attracting / estación 12 (secuenciador + metaball)

> Escrito el **2026-09-23**. Es el mapa de **todo lo que se puede tocar sin programar** en la estación `GAL_12` de `/Game/TestMeshes`.
> Cada perilla dice **dónde está**, **qué hace** y su **valor actual**. Todas son instance-editable: se ven en el panel de detalles del actor, en la categoría `0-Config`.
>
> 🔴 Regla del proyecto: **las perillas nuevas nacen en CERO en un actor ya colocado**. Si una no hace nada, mirá primero si está en 0.

---

## 1. El metaball — actor `GAL_12_SlotChain`

### Color
| Perilla | Qué hace | Hoy |
|---|---|---|
| `ColorLow` / `ColorHigh` | El degradé del cuerpo de las gotas: `Low` en las zonas que miran de canto, `High` en las que dan de frente. No es luz: es un sombreado falso | tierra / oliva |
| `ChainBrightness` | Brillo general de todo el metaball | 1,54 |
| `ChainTransparency` | **0** = como antes (opaco) · **0,35** = se ve lo que hay adentro · **1** = invisible | 0,35 |
| `ColorPulse` | 🔵 **El color base del tinte**: el que se usa cuando el paso que suena está **vacío** | (lo que pongas) |
| `ColorSpeed` | Velocidad del crossfade cuando el tinte cambia de color entre un paso y el siguiente | 6 |
| `TintSpread` | Cuánto se derrama el tinte hacia las gotas vecinas | 2,05 |
| `TintGain` | Fuerza del tinte. 1 = tímido · 2,5 = pleno · 5 = casi binario | 2,5 |

### Forma
| Perilla | Qué hace | Hoy |
|---|---|---|
| `BlobRadius` | Tamaño base de cada gota | 12,1 |
| `Smooth` | Cuánto se funden entre sí. Alto = una masa; bajo = bolitas separadas | 15,2 |
| `SizeVariation` | Cada gota tiene su tamaño propio, fijo (secuencia áurea, no azar) | 0,47 |
| `MinScale` | 🔴 **Piso de tamaño de gota.** Es la perilla para que las chicas no queden tan chicas: sube el suelo sin tocar las grandes. ⚠ también limita cuánto puede adelgazar la onda `Swell` | 0,8 |
| `EndBoost` | Engorda las gotas de las puntas para compensar que el centro se une más por construcción | 0,1 |
| `Steps` | Calidad del raymarch. **Es la perilla de costo**: sube el precio en la Quest | 32 |
| 🆕 `OrbFuse` | 🎯 **Cuánto se funde la esfera que traés en la mano con la gota cercana.** 0 = no funde · 0,6 = asoma un cuello · 1 = se comporta como una gota más del metaball | 0,6 |
| 🆕 `FuseFade` | Qué tan rápido se despega al alejarla | 8 |
| 🆕 `CoreColor` | 🎯 **El color del núcleo de cada gota** — la esferita translúcida del centro. Blanco por defecto | blanco |
| 🆕 `CoreScale` | Tamaño del núcleo, como **fracción de su gota**. 0,35 = un tercio · 0 = sin núcleo | 0,35 |
| 🆕 `CoreOpacity` | Cuánto se ve. 1 = sólido · 0 = invisible | 0,45 |
| 🆕 `OrbFit` | 🎯 **Qué fracción de su gota ocupa la esfera anclada.** 0,9 = casi la llena · 1 = toca la pared · **>1 se sale**. La esfera anclada **sigue el centro y el tamaño vivos de su gota**: el flotar, el pulso y el cambio de slot se ven en tiempo real | 0,9 |

### Movimiento
| Perilla | Qué hace | Hoy |
|---|---|---|
| `PulseAmount` | Cuánto crece la gota cuando el playhead pasa por ella | 0,66 |
| `PulseSmooth` | Inercia del pulso **y del color**. 0 = golpe seco · 6 = redondeado · 12 = casi instantáneo | 6 |
| `FloatAmount` | Deriva de cada gota, en cm. 0 = quietas | 3 |
| `FloatSpeed` | Ritmo de esa deriva | 0,6 |
| `FloatAlong` | Qué parte del movimiento va **a lo largo** de la fila. Bajo = las gotas no se separan entre sí | 0,35 |
| `SwellAmount` | La onda que engorda unas gotas y adelgaza otras, moviendo la zona donde se unen | 0,3 |
| `SwellSpeed` | Ritmo de esa onda | 0,12 |
| `SwellWaves` | Tamaño de los grupos que se unen. 1 = un grupo · 2 = dos | 1 |

---

## 2. 🎨 EL DIRECTOR DE LAS AMEBAS — actor `GAL_12_OrbDirector`
> **Es el actor desde el que se autora la composición entera de esferas.** Todo lo que toques acá se
> ve **en el viewport, sin darle play**: el director dibuja una **vista previa** de cada esfera sobre
> su ancla (`orb_attracting`), con la malla, el material, el color y el tamaño reales.
>
> Y no es sólo una vista previa: **las esferas de verdad leen las mismas perillas** al arrancar la
> mecánica (`BP_SoundOrb_SC` le pide el look al director). Lo que ves es lo que suena.

| Perilla | Qué hace | Hoy |
|---|---|---|
| `Color1` `Color2` `Color3` `Color4` | 🎨 **Los 4 colores.** Cada uno es un selector de color: apretás el cuadradito y elegíslo. Las esferas toman uno **al azar** | rojo · ámbar · turquesa · azul |
| `Seed` | **Vuelve a sortear.** Mismos 4 colores, otro reparto entre las esferas | 0 |
| `ScaleMin` / `ScaleMax` | Rango de tamaños. Cada esfera saca el suyo, fijo (no parpadea) | 0,12 / 0,26 |
| `FloatAmpMin` / `FloatAmpMax` | Cuánto flota cada esfera, en cm. Distinto por esfera | 0,8 / 2,5 |
| `FloatSpeedMin` / `FloatSpeedMax` | El ritmo de ese flotar, también distinto por esfera | 0,4 / 1 |
| 🆕 `ShadeColor` | 🎯 **El segundo color del degradé, igual para todas.** El color propio de cada esfera vive en el centro; éste en el canto y en los hundidos | (lo que pongas) |
| 🆕 `ReliefAmount` | 🎯 **Cuánto marca la deformación.** 0 = bola lisa con canto oscuro · alto = los salientes y hundidos del wobble se ven como relieve. **Negativo invierte** qué lado queda en sombra | 0,6 |
| 🆕 `ShadeSharp` | Qué tan cerrado es el degradé hacia el canto (va al `FresnelPower`) | 2 |
| `WobbleAmount` | 🫧 **Cuánto se deforma la ameba** (fracción del radio, así no depende del tamaño). 0 = esfera lisa | 0,12 |
| 🆕 `WobbleFreq` | **La escala del ruido de la deformación.** Bajo = pocas ondas, grandes y blandas · alto = muchas arrugas chicas | 0,06 |
| 🆕 `WobbleSpeed` | A qué velocidad se mueve esa deformación. 0 = ameba congelada | 0,8 |
| `Brightness` | Brillo general de las esferas | 1 |
| `FloatScale` | Multiplica el flotar **después** del tamaño. Bajalo si una esfera chica se despega de su punto | 1 |
| 🆕 `AnchorScale` | 🎯 El tamaño **mientras la llevás en la mano**: uno solo para todas, absoluto. Desde que la agarrás, la esfera **viaja achicándose hacia él**. Al anclarse, el tamaño pasa a mandarlo la gota (`OrbFit` del metaball) | 0,13 |
| `PreviewMesh` / `PreviewMaterial` | La malla y el material de TODAS las esferas | `SM_AlmaSphere` / `MI_OrbBlob_SC` |
| `bShowPreview` | Apaga la vista previa del editor (las esferas de juego no se tocan) | true |
| 🆕 `bShowAnchors` | **false = esconde la esfera verde y el texto** de los `BP_Anchor` que hacen de ancla. Solo afecta a los de este director | false |
| `AnchorTag` | El tag de los actores que hacen de ancla | `orb_attracting` |
| 🆕 `SeedSpread` | 🎯 **La semilla que hace distinta a cada esfera**: su forma, su ondulacion y su flotar salen de aca. Muevela y se resortea todo. **En 0 quedan todas iguales** | 10 |
| 🆕 `WobbleAmp` / `WobbleFreq` / `WobbleSpeed` | El wobble del material nuevo (el de los blobs): cuanto se deforma, de que tamano son las ondas y a que velocidad viajan | 0,09 / 4 / 0,35 |
| 🆕 `OrbSort` | 🎯 **Quien se dibuja por delante.** Mas alto = la esfera va encima del metaball en vez de lavarse debajo. La pila es **0 = la cadena · 10 = las bolitas blancas del centro · 20 = las esferas**. Ponlo en 0 y vuelven a quedar tapadas | 20 |
| 🆕 `SpinSlow` / `SpinFast` | 🔄 **Cuanto gira cada esfera sobre si misma**, en grados por segundo. `SpinSlow` es el giro suave de siempre; `SpinFast` el de **mientras la tienes agarrada**. Al anclarla vuelve sola a `SpinSlow`. Cada esfera gira sobre **su propio eje al azar** | 22 / 150 |
| 🆕 `SpinAccel` | Que tan rapido cambia de una velocidad a la otra. Bajo = acelera y frena con pereza · alto = cambia de golpe | 4 |

💡 **Para ver un cambio**: tocá la perilla y el Construction Script redibuja la previa al instante.
💡 **Para mover una esfera**: movés su ancla en el viewport, no la previa.

---

## 3. Las esferas de sonido — Blueprint `BP_SoundOrb_SC`
⚠ **No existen en el editor**: las spawnea el secuenciador al arrancar la mecánica, una por ancla `orb_attracting`. Lo estético sale del **director** (§2); acá quedan sólo las perillas de comportamiento.

| Perilla | Qué hace | Hoy |
|---|---|---|
| `ActiveBoost` | Cuánto **brilla** la esfera al agarrarla o colocarla. **Ya no cambia de color**: mantiene el suyo y sube la intensidad | 1,7 |
| `HoverScale` / `HoverSpeed` | Cuánto crece al apuntarla y qué tan rápido | 1,15 |
| `PulseAmount` / `PulseDecay` | El latido de la esfera cuando suena en el paso | 0,35 / 5 |
| `RevealSpeed` | Velocidad con la que nace | |
| 🆕 `ScaleSpeed` | Qué tan rápido se achica/agranda al agarrarla o soltarla. **Bajo = el encogido se ve durante todo el viaje a la mano** | 3 |
| `GrabSpeed` `TravelSpeed` `ReturnSpeed` | Velocidades de agarre, viaje y vuelta a casa | |
| `PlaceRadius` / `SnapRadius` / `SnapSpeed` | Distancia a la que engancha en un slot y cuánto se pega | 40 |
| ~~`ColorFree` / `ColorActive`~~ | 🔴 **Sin efecto desde el 2026-09-23**: el color de la esfera es `OrbColor`, que sale de la paleta del director | — |

---

## 4. El secuenciador — actor `Sequencer_Attracting`
| Perilla | Qué hace | Hoy |
|---|---|---|
| `OrbColors` | Paleta **de respaldo**: sólo se usa en un nivel **sin director** (la obra). En la galería manda `Palette` del director | 4 colores repetidos para llenar 8 |
| `OrbZOffset` | Altura de la esfera sobre el slot. **0** = centro exacto del blob · 12 = flotando encima (la obra) | 0 |
| `PadDelay` | Retraso del pad para que el paso 0 no suene con la mesa invisible | 0,9 |
| `NumSteps` / `FinalPasses` | Pasos del loop y pasadas del cierre | 8 / 2 |

---

## 5. Los slots — los 8 `BP_SeqSlot_SC` del nivel
| Perilla | Qué hace | Hoy |
|---|---|---|
| `bHideInGame` | **true** = el disco del slot no se ve en juego (queda sólo la gota) | true |
| `ZoneRadius` | Radio de la zona de enganche | 30 |
| `StepIndex` | 🔴 Qué paso del loop es. **No tocar**: define el orden musical | 0..7 |

👉 **La forma del secuenciador se autora moviendo los slots**: arrastrás uno en el viewport y el metaball se reacomoda solo. Hoy están sobre una circunferencia de **radio 70 cm** centrada 30 cm delante del pawn, cubriendo 126°.

---

## 🔒 La obra no cambia
`L_Attracting_SC` **no tiene director**. El `Cast` de `Setup` falla, no se aplica nada y la esfera
queda con su malla, su material y su color de siempre. Todo lo de §2 vive sólo donde haya un
`BP_OrbDirector_SC` colocado.

## Lo que NO es perilla (hay que pedirlo)
- Que las esferas sueltas **dejen de flotar al agarrarlas** y **adopten el movimiento de su gota** al anclarse.
- Que la previa del editor y la esfera real usen **el mismo índice** (hoy la previa indexa por posición del ancla y la esfera por su `ClipId`).
