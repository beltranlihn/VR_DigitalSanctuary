# Las esferas de sonido, con la técnica de malla del gusano

> 2026-09-27. Pedido de Beltrán tras validar el gusano en visor: *"esta técnica de mesh se ve mucho
> mejor que el raymarch en términos de calidad… ¿podemos hacer que las esferas con sonidos sean con
> la misma técnica? Manteniendo todo el sistema de colores y paletas y distribución y sonidos."*
> **Diseño cerrado, sin construir** (el MCP estaba caído al escribirlo).

## Qué son hoy las esferas
`SM_AlmaSphere` + **`MI_OrbBlob_SC`, que es una instancia del MISMO master del raymarch**
(`M_SlotChain_SC`) con `BlobCount = 1`. O sea: cada esfera es un raymarch de **dos bolas**:
- la principal, `Rad0` = **42** en espacio LOCAL (el proxy mide 50 sin importar la escala del actor),
- un segundo lóbulo de `ROrb` **38** en `COrb` = `LookLobe(Index)`, que la hace asimétrica y distinta
  de las demás. ⚠ `LobeOffset + ROrb` no puede pasar de 50 o el lóbulo se sale del proxy.

Más el **wobble** (`WobbleAFS` = amplitud/frecuencia/velocidad) con semilla por esfera `ps`, y los
colores `ChainColorHigh` (color de paleta, lo empuja `ApplyLook`) y `ChainColorLow` (ShadeColor).
Detalle en [[BP_SlotChain_SC]], sección del 2026-09-24.

## Por qué la malla va a verse mejor, y por qué es MÁS fácil que el gusano
El raymarch resuelve la superficie por pasos: el borde es un hit binario y el sombreado hereda el
paso. La malla da silueta exacta y normal analítica — que es justo lo que a Beltrán le gustó del gusano.

Y acá es **más simple que el gusano**: no hay polilínea, ni tangentes, ni tapas. La esfera es
**estrellada respecto de su origen** (con el lóbulo a ≤12 del centro y radio 38, ningún rayo desde el
origen cruza la superficie dos veces), así que alcanza con:
```
rdir    = normalize(LocalPos)            // la dirección radial del vértice
r       = biseccion sobre smin(2 bolas + wobble) a lo largo de rdir
destino = rdir * r
```
🔴 **La condición estrellada es la que hace válido todo esto.** Si algún día el lóbulo se aleja más
que el radio de la bola principal, un rayo radial puede cortar dos veces y la malla se deforma.
Es la primera cosa a revisar si aparece un artefacto raro.

## El contrato: los NOMBRES de parámetro, otra vez
Igual que con el gusano, **no se toca el Blueprint**. El master nuevo expone **los mismos nombres**
que hoy usa `MI_OrbBlob_SC` (`ChainColorLow`, `ChainColorHigh`, `Rad0`, `ROrb`, `COrb`, `WobbleAFS`,
`SwellAmount`/`Speed`/`Waves`, `ChainBrightness`, `ChainTransparency`), y con eso `ApplyLook` y todo
el sistema de paletas, distribución y sonido siguen funcionando sin un solo cambio.
Los que sobran del raymarch (`Steps`, `MaxT`) se empujan igual y son no-ops inofensivos.

## Piezas
1. **`SM_BlobOrb_SC`** — icoesfera de **radio 50 local** (misma convención que `SM_AlmaSphere`, así
   `Rad0` = 42 sigue valiendo), subdivisión 3 = 642 verts / 1.280 tris. Generada con Blender headless,
   script versionado al lado de `gen_blob_tube.py`. Con `WobbleAFS.y` = 4, 642 verts resuelven la onda
   de sobra. 20 esferas × 1.280 tris = 25k tris, que en este proyecto es ruido (somos fill-rate bound).
2. **`M_BlobOrb_SC`** — misma familia que `M_BlobMesh_SC`: desplazamiento por bisección en el vertex
   shader, normal analítica por gradiente de 4 taps del MISMO campo, y la cadena de sombreado + tinte
   + `RevealFade` que ya está construida. Reusa el wobble tal cual está en el master del raymarch,
   **con la semilla `ps`** (si no, las 20 respiran al unísono — ese error ya se pagó una vez).
3. **`MI_BlobOrb_SC`** — con los mismos valores que tiene hoy `MI_OrbBlob_SC`.
4. **El swap**: malla + material en `BP_SoundOrb_SC`. Nada más.

## 🔴 La pregunta abierta: la FUSIÓN con el gusano
Hoy, cuando agarrás una esfera, **funde** con la cadena porque las dos son el mismo campo raymarch.
Con la esfera hecha malla, el gusano sigue creciendo su lóbulo hacia ella (tiene `COrb`/`ROrb`), pero
la esfera sería una superficie cerrada aparte: en vez de fundirse, **se intersecan**.

Dos caminos:
- **(a)** Construir y **mirar**. Puede que la intersección lea bien, sobre todo con las dos
  translúcidas y del mismo color.
- **(b)** Que el campo de la esfera agarrada incluya también las gotas de la cadena (`C0..C7`), así
  las dos superficies coinciden en la zona de fusión. Es el mismo shader, sale barato en vértices.

Propuesta: **(a) primero**, porque decide el ojo y es gratis; **(b)** si no convence.

## Verificación, en este orden
1. Una esfera de malla **al lado** de una de raymarch, misma paleta, sobre fondo negro y **aisladas**
   (la lección de anoche: si hay dos cosas en cuadro, el diagnóstico es falso).
2. VR Preview con el secuenciador corriendo: colores, distribución, sonido, y la fusión al agarrar.
3. Medir con el banco. Las esferas ya tienen su modo propio: **`-Modos 0,4,5,3`**, donde
   `esferas = m5 − piso`. Referencia a batir: **5,81 ms** medidos el 2026-09-25.

## Riesgos anotados
- **Silueta facetada** si la subdivisión queda corta: se ve en el paso 1 y se sube a subdiv 4.
- **Coste de vértices** ×20 objetos: si molesta, baja subdiv o se poda el campo a 1 bola cuando la
  esfera está lejos de la cadena.
- ⚠ **Ediciones estructurales del BP con instancias colocadas** (gotcha 402): acá no hace falta tocar
  el BP, y esa es justamente la razón de mantener los nombres de parámetro.
