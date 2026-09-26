# BP_BlobChain_SC + M_BlobMesh_SC — el gusano por MALLA (Core/AttractingC/)

> Creado el 2026-09-26. **Es la misma mecánica que [[BP_SlotChain_SC]]**, con otro motor de dibujo:
> en vez de raymarch sobre un proxy, **desplazamiento de vértices** sobre `SM_BlobTube_SC`.
> Nació como **duplicado del BP del raymarch**, a propósito: la lógica ya estaba probada y aprobada,
> y reescribirla habría sido reintroducir bugs resueltos.
> **Estado: 🟢 construido, empujando y verificado en el editor (forma, pulso y tinte).**
> ⬜ Sin visor con el secuenciador corriendo · ⬜ sin medir el costo.

## Qué es
Una gota de metaball **por slot** del secuenciador, igual que el raymarch, pero la superficie la
resuelve el **vertex shader**: cada vértice del tubo se manda por bisección a la superficie del
mismo `smin` de 9 esferas. Vive en `GAL_12` de `/Game/TestMeshes` como **`GAL_12_BlobChain`**.
Por qué existe: el raymarch costaba ≥8,93 ms; la malla baja la estación de 22,8 a 14,0 ms
(ver `docs/PLAN-ENFOQUE-C-MALLA.md`).

## 🔴 Cómo se hizo compatible: los NOMBRES de parámetro, no la lógica
El BP empuja al material por **nombre**. En vez de tocar el BP se le agregaron a `M_BlobMesh_SC`
los cuatro parámetros que le faltaban — **`Pulse0/1/2`, `ChainColorPulse`, `TintSpread`, `TintGain`** —
y con eso el duplicado maneja la malla sin un solo cambio en sus grafos. Los que el material de
malla no tiene (`Steps`, `MaxT`, `WobbleAFS`) se empujan igual y son no-ops inofensivos.

🔴 **La trampa que sí había que arreglar: `BlobRadius`.** En `M_SlotChain_SC` **no multiplica**
(`R[j] = Rad0.x` crudo; es una perilla del BP, que la usa para sembrar `Rad0..2`). Mi versión de
malla lo tenía como multiplicador global con default 1.0. Si se dejaba así, el BP le empujaba
**5,91** y las gotas salían seis veces más grandes. Igualado al master.

## Lo que viaja del BP al material
`C0..C7` (centro de cada gota = posición del slot − la del chain) · `Rad0/1/2` (radio por gota,
3 por vector) · `Pulse0/1/2` (pulso por gota, ídem) · `COrb`/`ROrb` (la novena gota: la esfera
agarrada) · y las ~20 perillas de estética. **El pulso por gota llega por dos caminos a la vez:**
el tamaño ya viene dentro de `Rad` (el BP lo calcula con `PulseAmount` + `VInterpTo`), y el color
por `Pulse`, que el shader convierte en tinte.

## El TINTE, dentro de `Custom_1`
Se calcula **por vértice**, en el mismo Custom que ya resuelve la normal, porque ahí ya existen
`destino`, `P[]`, `R[]` y `A[]`: un tercer Custom costaría el cuerpo entero otra vez.
`pw = max_j( exp(-|destino - P_j| / (Smooth·TintSpread)) · Pulse_j )`, y el `saturate(pw·TintGain)`
vive en el grafo para poder escrubearlo.
🔴 **Ponderado por MÁXIMO, no por promedio** — es la lección ya pagada en el raymarch: con promedio
las 8 gotas se reparten el alfa y el color del pulso no se ve.

**`Custom_1` devuelve `float3(shade, pw, 0)`**: el lambert se resuelve adentro y viajan **dos
escalares**, no la normal entera. Un canal menos por vértice y ningún canal que confundir.

## Estructura (heredada del raymarch, sin cambios)
`UserConstructionScript` → `ApplyAll` · `EventBeginPlay` → timer 0,6 s → `BootChain` ·
`EventTick` → **`PushCenters` → `PushRadii`** (en ese orden) · más los 8 "cores"
(`M_BlobCore_SC`) que el BP crea como componentes. Detalle en [[BP_SlotChain_SC]].

## Cómo se verifica sin visor
1. `overrideMaterials` del componente `Volume` → el `MID_M_BlobMesh_SC_0` →
   `get_properties(['scalarParameterValues','vectorParameterValues'])`. Ahí están los `C0..C7`
   reales (revelan el arco), los `Rad`, el pulso y los colores.
2. 🔴 **Para mirar la forma hay que SACARLO de la estación**: el viewport del editor tapa la cadena
   con los billboards de los 8 slots y las esferas rojas de alcance de audio. Se le copian los
   parámetros a `MI_BlobMesh_SC` y se mira el actor de prueba sobre fondo negro.
3. ⚠ **Y hay que mirarlo SOLO.** El 2026-09-26 el actor de prueba y el raymarch estaban parkeados
   en las MISMAS coordenadas: lo que parecía "el tinte pinta solo el filo" eran **dos cadenas
   superpuestas**, la pálida del raymarch tapando la teñida de la malla. Costó dos cirugías al
   material que no arreglaron nada. **Antes de diagnosticar, contar cuántas cosas hay en cuadro.**

## Lo que se ve en el editor, y por qué NO es un bug
La cadena aparece **partida en islas**. Es correcto: sin Tick, `PushCenters` siembra los radios
**planos** en `BlobRadius` = 5,91 contra slots separados 21,4, y el `smin` con `Smooth` 15,24 no
llega a unirlos (`smin(a,a,k) = a − k/4` = 4,79 − 3,81 > 0). El `smin` de los dos materiales es la
**misma línea de código**, así que el raymarch en el editor se parte igual. En play los une
`PushRadii`. Si hiciera falta que se vea unido también en el editor, la perilla es `BlobRadius`.

## TODO
- [ ] 🔴 **Visor** con el secuenciador corriendo: que las esferas insertadas pulsen y tiñan.
- [ ] Medir el costo con el banco (`-Modos 0,5,3`) — ⚠ la última medición quedó **saturada** contra
      el cap de 72 Hz; para un número hay que subir la carga (`vr.PixelDensity 1.4`) en las dos fases.
- [ ] La novena gota (`COrb`/`ROrb`, la esfera agarrada) sin probar en la malla.
- [ ] Decidir qué pasa con el raymarch: hoy queda **intacto y parkeado** en z+100000 con sus tags.
