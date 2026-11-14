# Investigación: el cielo y el océano de Heart como entorno de Entering (2026-09-27)

Pedido de Beltrán, **solo investigar, sin decidir**: la sesión de Heart armó un horizonte con cielo y un océano (malla deformada con pulsos circulares) que *"se ve brutal en la Quest"*. ¿Se puede llevar a `Test_Entering` como un **oleaje que se pierde en el infinito**, sin romper los FPS del metaball? Workflow de 3 investigadores + síntesis + 2 verificadores (los dos corrigieron partes de la síntesis; abajo va la versión corregida).

## Qué hizo Heart (`/Game/SoulCharger/Mechanics/Heart/Scape/`, nivel `/Game/Test_Heart`, sin commitear)
- Un actor `BP_HeartScape_SC` con componentes Membrane (el mar), Heart (esfera), Sky (esfera de motor a 700 m) y Echoes (24 esferas, fase 4). Un solo material `M_HeartScape_SC` (opaco, unlit, two-sided, precisión completa) que elige la parte con `Part`; 5 Custom HLSL (fuente en `.claude/skills/unreal-vr/scripts/hlsl/Heart*.hlsl`). Sin texturas ni ruido: senos y gaussianas.
- **El mar**: disco polar plano de Blender (`gen_heart_membrane.py`), radios en progresión geométrica (densidad ∝ 1/r = LOD continuo), 32.641 vértices hasta 60 m + faldón de anillos hasta 600 m. Relieve por WPO: 8 ondas circulares por latido (ring buffer) + hoyuelo bajo la esfera + un "Swell" de 6 cm casi invisible. La "textura" es luz sobre una **normal analítica** (wrap, sheen, valles, línea de cresta por onda con `fwidth`, dither).
- **El horizonte "infinito"** no es geometría: cielo analítico (degradado + resplandor) y la membrana se funde con **ese mismo color de cielo** por niebla de distancia real (62 % a 60 m, 97 % a 200 m).
- Medido en la Quest (sin metaball): v3/v4 **72-73 fps, App ≈ 10,4-10,6 ms**, reloj de GPU **no registrado**. Banco v2: el modo "todo barato" (cielo completo + mar plano sin olas) dio **10,23 ms** → **la BASE es lo caro, no las olas**.

## Lo que dicen los números (corregidos por los verificadores)
- Nuestra etapa sin fondo: 9,61 ms a 456 MHz (6,85 normalizado a 640). Presupuesto 13,9 ms.
- La base de Heart sobre el piso negro vale **6,1-9,0 ms a 640 MHz** (8,5-12,7 a 456). Las partes no se suman: m1 − m3 = 0,29 ms muestra que interactúan.

| Opción | Qué es | Costo estimado (sin medir) | ¿Entra con el metaball? |
|---|---|---|---|
| A | Heart duplicado, solo parámetros (sin latido, Swell subido) | 5,8-9,4 ms a 640 | **No** (12,7-16,2). Además solo parámetros no da oleaje: el Swell sin fundido por distancia se dentea en el horizonte, y en el editor los anillos siguen (`PreviewIntensity`). |
| **B** | **Fork adaptado**: cielo + niebla-al-cielo + sombreado de Heart; malla polar centrada en el usuario (~13-20k vért.); 3-4 ondas direccionales que se alejan y se apagan con la distancia | ~6-9 ms a 640 sobre el piso | **Dudoso aun con la GPU al máximo** (12,9-15,9 a 640); a 456 no entra |
| C | Mar casi plano, olas solo en la normal por píxel | parecido a B (la base domina) | Parecido a B |
| D | Solo el cielo de Heart sobre nuestro cascarón (sin mar) | ≈ fondo liso + 0-0,3 ms | Sí, si el fondo liso entra. No da horizonte de mar |

Reglas técnicas para B si se hace: cada onda se apaga a r_fade ≈ λ·S/(2π·N) (N 8-16) y el WPO vale exactamente 0 antes del faldón; conservar la esfera de cielo completa; ~16 segmentos por longitud de onda o el horizonte sale dentado; bucles con tope constante (gotcha 399); comodidad: oleaje lento y de poca amplitud bajo alguien sentado.

## Antes de decidir: medir (sin builds nuevos primero)
0. **Costo real del fondo liso** de Entering (nunca se midió): `quest_entering_perf.ps1 -Modos 0,4`. Es la pieza que un mar reemplazaría. ~2 min.
1. **De dónde sale la base de Heart** (cielo vs mar): su `PerfMode` NO toca el cielo (`HeartScapePS.hlsl:41-42`), así que hacen falta modos que OCULTEN componentes (solo Sky / solo Membrane) con los MHz registrados. Es su APK y su banco: coordinarlo con la sesión de Heart.

## Coordinación con Heart
No tocar `Mechanics/Heart/Scape/` ni `Test_Heart` (en plena iteración). Si se avanza: **duplicar** a carpeta propia (p. ej. `Mechanics/Breath/Sea/`) y copiar los `.hlsl`/generador a archivos nuevos; no referenciar su master. Serializar empaquetados (ambos tocan `DefaultEngine.ini` temporalmente) y el uso de la Quest. No commitear sus archivos.

## Preguntas abiertas para Beltrán
1. ¿El mar es solo para `Test_Entering` o cambia la obra final (hoy cada etapa es "una esfera de color")?
2. Dirección y ritmo del oleaje (¿se aleja hacia el horizonte?, ¿acompaña la respiración vía `MPC_Breath`?).
3. Paleta: la de Heart es pálida (le quita contraste al metaball blanco).
4. ¿Se acepta que la etapa necesite la GPU a 640 MHz sostenido 15 min (calor, batería)?
5. ¿Prueba de look primero en el navegador (copia del prototipo three.js de Heart con oleaje direccional) antes de tocar Unreal?
6. ¿Se autoriza escribirle a la sesión de Heart para pedirle los MHz de v3/v4 y pactar turnos?
