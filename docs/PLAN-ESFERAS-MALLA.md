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

## 🔴 PASO 0 — leer `MI_OrbBlob_SC` ANTES de escribir shader
Leyendo el codigo real del master (no el tracker) aparecio una incoherencia que hay que
resolver primero, porque decide de donde sale la **segunda bola**:

```
P[8] = COrb;  R[8] = max(ROrb, 0.001);
int NA = (ROrb > 0.001) ? (N + 1) : N;
for (j = 0; j < NA; j++) ...
```
El orbe vive en el indice **8**, y ese indice solo se alcanza cuando `NA = 9`, o sea con
`BlobCount = 8` (la cadena). Con **`BlobCount = 1`** el bucle llega hasta el indice **1**,
que es `C1` / `Rad0.y` — **no** el orbe. O sea que, tal como esta el codigo hoy, una esfera
NO puede recibir su lobulo por `COrb`/`ROrb`.

Dos explicaciones posibles, y **no hay que adivinar**:
- **(a)** `MI_OrbBlob_SC` pone el lobulo en `C1` + `Rad0.y`, y la nota del tracker (2026-09-24)
  quedo desactualizada.
- **(b)** El lobulo se **perdio** cuando se agrego la poda A4 (2026-09-25), que reescribio el
  bucle. Seria una regresion silenciosa: las esferas quedarian como bolas simetricas.

👉 **Primer comando al volver el MCP**: leer los overrides de `MI_OrbBlob_SC`
(`MaterialInstanceTools` / `get_properties` de `scalarParameterValues` + `vectorParameterValues`)
y mirar si `C1`/`Rad0.y` estan seteados. Eso decide si el port copia dos bolas o una, y de paso
dice si hay una regresion que arreglar en el raymarch.
⚠ Tambien explica el `ps`: la semilla por esfera sale de `COrb` (`ps = COrb·(0,11 · 0,17 · 0,23)`),
asi que `COrb` **si** esta seteado aunque el lobulo no se use — mirar los dos.

## El wobble, copiado del codigo real
```hlsl
float WobA = WobAFS.x;  float WobF = WobAFS.y;  float WobS = WobAFS.z;
float solo = (WobA > 0.001) ? 1.0 : 0.0;
float ps   = solo * (COrb.x*0.11 + COrb.y*0.17 + COrb.z*0.23);
float sJit = 1.0 + solo * (frac(ps*0.137 + 0.31) - 0.5) * 0.5;
// por gota, con dn = direccion desde el centro de la gota al punto:
float ws = sin(dn.x*WobF + ps*1.7) + sin(dn.y*WobF*1.31 + ps*3.1) + sin(dn.z*WobF*0.77 + ps*5.3);
float wm = sin(dn.x*WobF*1.9 + Tt*WobS + ps*2.3) * sin(dn.y*WobF*1.3 - Tt*WobS*0.83 + ps*1.9);
float rr = R[j] * (1.0 + WobA * (ws*0.25 + wm*0.55));
```
El radio maximo con wobble es `R * (1 + 1.31*WobA)` — el mismo margen que usa la poda del master,
y el que hay que usar como cota superior de la biseccion.
🔴 **El `ps` va en TODO**: sin el, las 20 esferas respiran al unisono. Ya se pago una vez.

## Piezas
1. **`SM_BlobOrb_SC`** — 🟢 generador ya escrito: `scripts/gen_blob_orb.py`. Icoesfera de **radio 50 local** (misma convención que `SM_AlmaSphere`, así
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


---

# ✅ CONSTRUIDO (2026-09-27)

## Lo que decia el PASO 0, resuelto con datos
- **`MI_OrbBlob_SC`** (instancia del master del raymarch): `BlobCount` 1 · **`ROrb` 0** ·
  `Rad0` (38,38,38) · `Smooth` 18 · `SizeVariation` 0 · `EndBoost` 0 · **`MinScale` 1** ·
  `SwellAmount` (default del master, 0,3) · `FloatAmount` 7 / `Speed` 0,4 / **`Along` 1** ·
  `ChainTransparency` 0 · `TintGain` 0 · `WobbleAFS` (0,09 · 4 · 0,35).
- 🔴 **`ROrb` = 0 y nadie lo empuja → NA = 1: cada esfera es UNA sola bola.** El segundo
  lobulo que describe el tracker del 2026-09-24 **no esta activo**. Queda como decision
  aparte si se revive (empujar `ROrb` desde `ApplyLook` alcanzaria).
- ⚠ **Me equivoque una vez en el camino**: afirme que tampoco se empujaba `COrb`, barriendo
  los 27 grafos de `BP_SoundOrb_SC`. **`ApplyLook` no vive ahi, vive en `BP_OrbDirector_SC`**,
  y si empuja `COrb`, `WobbleAFS`, `FloatSpeed`, `ChainColorHigh` y `ChainColorLow`. O sea que
  **la semilla por esfera (`ps`, que sale de `COrb`) esta VIVA** y las 20 no respiran al unisono.
  Barrer el Blueprint equivocado da un negativo que parece un hallazgo.

## No hizo falta malla nueva
**`SM_AlmaSphere` ya es una icoesfera de 2.665 verts / 5.120 tris con radio exactamente 50**,
que es el lienzo ideal. El generador `scripts/gen_blob_orb.py` queda escrito por si mas adelante
conviene una version de menos vertices (20 esferas x 2.665 verts es el unico costo a vigilar).

## Y no hizo falta biseccion
Con UNA bola, la superficie es cerrada y se escribe directo: `destino = centro(t) + u·radio(u,t)`,
donde `u` es la direccion del vertice. **Cero iteraciones por vertice**, contra los 28 pasos de
raymarch POR PIXEL de antes. El wobble, el swell y el flotar son las formulas del master, copiadas
del codigo real.
🔴 Si algun dia se revive el segundo lobulo, esto deja de valer y hay que volver a la biseccion
del gusano: dos bolas fundidas ya no son radiales desde un centro.

## Las piezas
- **`M_BlobOrb_SC`** — duplicado de `M_BlobMesh_SC` (asi hereda el sombreado, el tinte y el
  `RevealFade` ya hechos), con los dos Custom reemplazados y un input nuevo `WobAFS`.
  🔴 **El gate del banco esta INVERTIDO respecto del gusano**: la esfera apaga en los modos
  **3 y 4** (el 4 es "solo cadena"), el gusano en 3 y 5. Si no, el banco mide al reves.
- **`MI_BlobOrb_SC`** — con los mismos valores que `MI_OrbBlob_SC`.
- **El swap**: `PreviewMaterial` en la instancia **`BP_OrbDirector_SC_C_0`**. Ese era el punto,
  no el template de `BP_SoundOrb_SC` (que tiene `Sphere` + `MI_AttractOrb`, o sea esta viejo).
  El CDO del director sigue apuntando al raymarch, asi que la version vieja se recupera sola.

## Verificado
- Las dos esferas lado a lado, aisladas sobre negro: **mismo tamano, mismo color, mismo wobble**.
- **En PIE**: los 20 orbes tienen su MID con padre `MI_BlobOrb_SC`.
- ⬜ Falta el ojo de Beltran en VR Preview, y medir (`-Modos 0,4,5,3`; referencia: 5,81 ms).
- ⚠ A vigilar: facetado de la silueta (la icoesfera es lineal entre vertices y el wobble la
  curva) y el coste de vertices x20 objetos.
