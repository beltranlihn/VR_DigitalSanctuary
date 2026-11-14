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

---

## 🔬 2026-09-26 — La caza del "en PC si, en la Quest no"

`M_BlobMesh_SC` sobre `SM_BlobTube_SC` se ve en el editor (Beltran trabaja **en Vulkan Mobile
Preview**, asi que el shader movil ya se compila y dibuja bien en PC) y **no se ve en la Quest**.
Sin error de compilacion, sin advertencia en el log del device.

### Descartado de escritorio, sin visor
- **Opacidad**: `ChainTransparency` default 0 → opacidad 1.
- **El gate del banco**: `BenchGate` apaga la opacidad solo en `PerfMode` 3 o 5, y el MPC
  `MPC_Perf_SC` tiene `PerfMode` con default **0**.
- **La malla y el cook**: el intercambio material/malla ya habia probado que el tubo dibuja.

### 🔴 La tanda de CUBOS fue un test invalido (ver gotcha 397)
A (plano) se veia, B (+WPO) **solo por un ojo**, C (+normal por interpolador) se veia, D no.
Parecia el WPO. **No lo era**: un cubo tiene 8 vertices, el WPO los manda a la superficie de la
cadena y queda una lasca degenerada; con el material a una cara, se ve desde un ojo y se descarta
por backface culling desde el otro. Lo unico que esa tanda dejo en firme: **el setup del material
y `Custom_1` con el `VertexInterpolator` dibujan bien en la Quest**.

### Escalera 1 — sobre la MALLA REAL (medida en visor)
| | material | resultado |
|---|---|---|
| T1 | plano, sin WPO | 🟢 se ve |
| T2 | WPO **constante** (sube 300 uu locales) | 🟢 se ve |
| T3 | WPO desde un Custom que usa `TransformPosition(WorldPosition→Local)` | 🟢 se ve |
| T4 | el material real | 🔴 no se ve |
| T5 | el real con nodo `LocalPosition` + sin el MPC en el vertex shader | 🔴 no se ve |

**Conclusiones firmes:** el WPO funciona en el visor; un Custom en el vertex shader que usa la
posicion local funciona; el ida y vuelta por coordenadas de mundo **no** es el problema (T3 lo usa);
el MPC en el vertex shader **no** es el problema (T5 no lo tiene). Queda el **cuerpo del Custom grande**.

### Escalera 2 — dentro del Custom grande (empaquetada 2026-09-26, pendiente de visor)
Todas con **color plano** (o sea `Custom_1` NO entra al vertex shader) salvo T4.
| | material | que aisla |
|---|---|---|
| T1 | `M_DIAG_A_plano` | ancla |
| T5 | `M_T5_solowpo` — el cuerpo original tal cual | `Custom_0` **solo**, sin `Custom_1` en el mismo VS |
| T6 | `M_T6_sintiempo` — idem con `Tt = 0.0` | cierra la familia `ResolvedView` / multi-view |
| T4 | `M_BlobMesh_SC` | control, el real |
| T7 | `M_T7_reescrito` — cuerpo **reescrito** | topes de bucle constantes, cero indexado dinamico |

🔴 **Y las tres nuevas llevan un tope FISICO al desplazamiento** (400 uu) en lugar del guardia viejo
de 1e12 sobre el cuadrado (= un millon de uu). El guardia viejo dejaba pasar cualquier basura finita
y la malla se iba fuera de cuadro: el sintoma era **"no se ve"** cuando en realidad era **"calcula
mal"**. Con el tope fisico los dos casos se distinguen a ojo.

### Por que el reescrito
El cuerpo original tiene los topes de bucle en variables (`ND`, `NP`, `NA`, derivadas de `NBlobs`)
y lee `P[]`, `R[]`, `TG[]`, `ACC[]` con indice dinamico. Eso impide desenrollar y manda los arreglos
a *indexable temp*; en el vertex shader de un Adreno es terreno de bugs de driver, y el Vulkan de
escritorio no lo acusa. El reescrito deja **todos** los topes constantes (8 o 9) y decide quien
participa con un **peso `A[j]` de 0 o 1** — el blend del smin con peso 0 es la identidad exacta,
asi que el resultado es el mismo. Silueta verificada contra el original en el viewport.

### ✅ Escalera 2 — resultado y CAUSA RAIZ (2026-09-26)
| | material | visor |
|---|---|---|
| T1 | plano, sin WPO | 🟢 los dos ojos |
| T5 | `Custom_0` original **solo** | 🟡 **un solo ojo** |
| T6 | idem con `Tt = 0.0` | 🟡 **un solo ojo** (igual que T5 → el reloj queda descartado) |
| T4 | el real (los dos Custom en el mismo VS) | 🔴 ningun ojo |
| T7 | el cuerpo **reescrito** | 🟢 **los dos ojos, sin problemas** |

🔴 **CAUSA: arreglos locales con INDICE DINAMICO en el vertex shader del Adreno** (gotcha 399).
Los topes de bucle eran variables (`ND`/`NP`/`NA`, derivadas de `NBlobs`), asi que el compilador
no podia desenrollar y `P[]`/`R[]`/`TG[]`/`ACC[]` caian en *indexable temp*. El Vulkan de escritorio
lo resuelve; el Adreno no. Y como el vertex shader corre **por vista** bajo multi-view, la corrupcion
toca una vista y la otra no → **el sintoma es un ojo**. La gravedad escala con el tamaño del shader:
un Custom = un ojo, dos Custom = los dos.

**Aplicado a `M_BlobMesh_SC`**: `Custom_0` (desplazamiento) y `Custom_1` (normal) reescritos con
topes constantes y peso `A[j]`, mas el tope fisico de 400 uu. Silueta verificada contra el cuerpo
original en el viewport (mismo instante, misma camara relativa). Empaquetado e instalado 22:12.

### 📊 Medicion 2026-09-26 22:36 — `-Modos 0,5,3` (CSVs en `perf/malla-2026-09-26/`)
Escena: la cadena raymarch **fuera** de la escena, los 5 tubos de prueba bajados 1.000 m,
en la estacion solo `BlobTubeTest` (malla con `MI_BlobMesh_SC`).

| modo | que dibuja | ms (promedio de 2 pasadas) |
|---|---|---|
| 0 | esferas + **malla** | **14,00** |
| 5 | solo esferas | 14,23 |
| 3 | nada | 13,90 |

🔴 **El instrumento esta SATURADO y por eso no hay un numero para la malla.** Los tres modos
caen en una franja de 0,33 ms pegada al cap de 72 Hz, y hay una **inversion**: el modo 5, que
dibuja MENOS, mide MAS que el modo 0. Eso es fisicamente imposible → lo que separa a los modos
es ruido. ⚠ Y la "resolucion del instrumento" que imprime el resumen (0,02 ms) es la
**repetibilidad de una pasada**, no la incertidumbre de la comparacion: creerle habria hecho
pasar los 0,10 ms por un costo medido. El resumen ahora detecta este caso y lo dice
(guardia de saturacion en `resumen_modos.py`).

✅ **Lo que si queda afirmado:** el cuadro entero entra en presupuesto **en todos los modos**;
la estacion corre a 72 Hz. Contra el 2026-09-25 con el raymarch: modo 0 daba **22,8 ms** y la
cadena sola **17,02**. La malla baja la estacion de 22,8 a 14,0 → **~8,8 ms recuperados**, que
era exactamente el agujero. Coincide con lo que reporto Beltran a ojo ("performance excelente").

⬜ Para ponerle numero al margen que sobra hay que **salir del cap**: subir la carga por igual en
las dos fases (`vr.PixelDensity 1.4`) y repetir el mismo A/B. Una sesion de 2 minutos.
