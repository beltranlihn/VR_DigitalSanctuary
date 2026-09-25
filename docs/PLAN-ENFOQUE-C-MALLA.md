# Enfoque C — las gotas como MALLA DESPLAZADA (plan de construcción)

> 2026-09-25. Decisión de Beltrán: probar la técnica nueva **en un nivel y BPs nuevos**, sin tocar
> nada de lo que ya está armado y aprobado, para poder tomarlo como está si la versión nueva no gana.

## 1. Por qué — el número que lo obliga
Medido hoy en visor (`perf/steps-2026-09-25/`, resolución del instrumento **0,05 ms**, FFR 0):

| | ms | lectura |
|---|---|---|
| modo 0 — la estación como está | **18,72** | 0 % de cuadros a 72 Hz |
| modo 1 — `Steps` a la mitad | **15,78** | sigue 1,9 ms sobre presupuesto |
| modo 3 — el piso, sin blobs | **13,87** | pegado al cap; 22 % igual pasa de 14,4 |
| presupuesto 72 Hz | 13,90 | |

Despeje (asumiendo que el march escala con `Steps`, que es el bucle dominante):
- **march = (18,72 − 15,78) × 2 = 5,88 ms**
- piso real + costo **FIJO** de los blobs = 12,84 ms → **margen real: 1,06 ms**

**Conclusión:** para entrar, el march tendría que bajar 82 % (`Steps` 32 → ~6), que destruye la
superficie. La técnica de raymarch **no entra en el presupuesto**. `Steps` quedó descartado con datos,
no por opinión. Y el FFR también quedó descartado, por Beltrán: baja demasiado la calidad percibida.

**Presupuesto que tiene que respetar el reemplazo: menos de 5,88 ms, idealmente ~1.**

## 2. La observación estructural
Ni la esfera ni la cadena necesitan un raymarch para verse como se ven:
- **La esfera de sonido no es un metaball real**: es 1 gota + 1 lóbulo + wobble radial. Eso es una
  superficie estrella-forma que una esfera teselada **desplazada por vértice** representa exacta.
- **La cadena sí es un metaball de verdad** (8-9 gotas fundiéndose), pero sus gotas están **sobre un
  eje**. Un tubo cuya sección varía por vértice —- radio = el mismo smooth-min de las 9 gotas
  evaluado en la posición axial de ese anillo -— da la silueta de cuentas fundiéndose.

El costo por píxel pasa de ~2.000 operaciones a ~30. El trabajo se muda al **vertex shader**, que
con ~2.000 vértices evalúa 9 gotas por vértice: irrelevante contra la pantalla que hoy se paga.

Y el borde **no se pierde**: hoy es un *hit binario* del raymarch (sin gradiente de cobertura). Una
silueta geométrica recibe los 4 samples del MSAA 4x, así que es **igual o mejor** que lo actual.
Esto ya estaba medido antes de hoy.

## 3. Arquitectura — el linaje que ya funciona en el proyecto
No se inventa nada: es el patrón de **`BP_SoulRing_SC` + `M_SoulRibbon_SC`**, que ya corre.
- **Malla generada UNA vez** en el Construction Script con `ProceduralMeshComponent` → se ve y se
  regenera en el viewport **sin Play** (Beltrán autora mirando).
- **Toda la animación en el MATERIAL, por WPO** (respiración, flotar, wobble, el crecimiento).
  Nada de reconstruir la malla por cuadro: es justo lo que Open Brush nunca hace y nosotros sí
  hacíamos.
- **El canal de normal guarda la dirección del ancho**, no la normal (el material es unlit, así que
  la normal queda libre como almacenamiento). Es lo que permite que el grosor viva en el shader.
- Sombreado idéntico al actual: normal → degradado `ChainColorLow`/`ChainColorHigh` + tinte de pulso.

🔴 **Y una ganancia que el despeje de hoy destapó, que va en el diseño desde el día 1:** el shader
actual calcula, **por píxel**, la respiración y el flotar de las 9 gotas: 5 senos por gota =
**45 transcendentales por píxel** para datos que son idénticos en todos los píxeles (son por gota, no
por píxel). En la versión de malla eso se evalúa **por vértice** (o se empuja ya animado desde el BP),
que es donde corresponde. Es parte del costo FIJO que `Steps` no tocaba.

## 4. Qué se crea, qué se copia, qué NO se toca
**Nuevo** (carpeta propia `Content/SoulCharger/Core/AttractingC/`):
- `M_BlobMesh_SC` — master unlit · translúcido · one-sided · WPO. Un switch `Shape` (0 = esfera,
  1 = cadena) resuelto por parámetro, no por rama por píxel.
- `BP_BlobSphere_SC` — la esfera de sonido: icoesfera ~640 verts + lóbulo + wobble por WPO.
- `BP_BlobChain_SC` — la cadena: tubo procedural (~64 anillos × 16 lados = 1.024 verts) con perfil
  de radio por smooth-min de 9 gotas y centro desplazable.
- `L_BlobMeshTest` — nivel nuevo, aislado.

**Se copia (lectura, no edición):** las fórmulas exactas del `MaterialExpressionCustom_0` de
`M_SlotChain_SC` (swell, float, wobble, el smooth-min y sus constantes) y la paleta. Backup fiel en
`scripts/hlsl_backups/M_SlotChain_Custom0_2026-09-25_pre-A4.hlsl`.

**NO se toca:** `M_SlotChain_SC`, `BP_SlotChain_SC`, `MI_OrbBlob_SC`, `BP_OrbDirector_SC`,
`SM_ChainProxyTube_SC`, ni la estación `GAL_12` de `/Game/TestMeshes`. La versión actual queda
intacta y usable tal como está.

## 5. La comparación lado a lado (es la verificación, y es gratis)
En `L_BlobMeshTest` van **las dos versiones juntas**, a la misma escala y con los mismos valores: la
estación actual **colocada** (instanciar un BP no lo modifica) y la nueva al lado. Así Beltrán compara
la estética directamente en el visor en vez de contra el recuerdo. Y el A/B de rendimiento sale de
mirar una y después la otra en la misma sesión.

## 6. Orden de construcción
1. **La cadena primero**, no la esfera: hoy quedó medido que es la que cubre pantalla y domina el
   costo. La esfera sola ya clavaba 72 Hz.
2. Tubo procedural en el Construction Script → verificar la silueta en el viewport (fotos).
3. Perfil de radio por smooth-min → que se vean las cuentas fundiéndose, no un caño.
4. Animación por WPO (swell + float) → comparar contra la actual al lado.
5. Sombreado (degradado por normal + pulso) → acá se juega el parecido estético.
6. La esfera con el mismo material.
7. Medir en visor con el banco.

## 7. La pregunta de diseño abierta (necesita el ojo de Beltrán)
La cadena actual **estira una gota hacia la esfera que sostenés** (`COrb`/`ROrb`, la gota 9): es la
fusión esfera-slot, y es parte de la mecánica aprobada. Un tubo sobre un eje no llega fuera del eje.
Tres salidas, en orden de lo que yo elegiría:
1. **Anillos del tubo atraídos hacia el orbe** por WPO (los cercanos se estiran): conserva la
   continuidad, es una fórmula más en el vertex shader, y no agrega geometría.
2. Una **malla puente** aparte que nace cuando la esfera se acerca.
3. Dejar la fusión como raymarch **solo ahí** (superficie chica = costo chico) y la cadena por malla.
Se decide mirando el paso 4.
