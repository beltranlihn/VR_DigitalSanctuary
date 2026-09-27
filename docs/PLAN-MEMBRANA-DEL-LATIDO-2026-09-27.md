# Plan: la membrana del latido (Recognizing / Heart) — 2026-09-27

> Pedido de Beltrán: mejorar el océano de ondas del pulso y sumarle esferas y amebas que acompañen el latido, con un resultado onírico, elegante, surreal y minimalista. Trajo dos imágenes de referencia hechas con ChatGPT y un prompt, que está escrito sin contexto de la obra. Pidió investigar primero y armar un plan para ver si es posible. Condición: **nada se construye sobre el nivel abierto**, porque hay otro agente trabajando ahí.
>
> **Prototipo de lookdev (navegador):** https://claude.ai/artifact/En9CRj53wBDrJfGLcB4LBK. Usa las mismas fórmulas de este plan y valores en cm y s. El botón "Copiar valores" entrega el JSON que después pasa como default al material.

## 0. Veredicto

**Es posible, y sale más barato que lo que hay hoy.** Todo lo que muestran las referencias se hace con desplazamiento de vértices en el vertex shader (fp32) y sombreado mate unlit, sin raymarch. Lo caro en este proyecto fue el raymarch: las gotas midieron 12,28 ms en el visor (el 88 % del cuadro), y la gota raymarcheada del PulseField nunca se midió. Este diseño no usa ninguno de los dos.

## 1. Qué hay hoy y por qué no alcanza

`BP_PulseField_SC` + `M_PulseField_SC` (`/Game/SoulCharger/Core/Light/`), leído del asset y del tracker:

| Aspecto | Hoy | Consecuencia |
|---|---|---|
| Malla | `SM_CloudPlane`, 129×129 vértices, unos 15,6 cm por quad a 20 m | Densidad uniforme: sobra lejos y falta cerca del centro |
| Sombreado | Unlit opaco, **color solo por altura** (`lerp(ColorLow, ColorHigh, h)`), **sin normales** | La ola se lee como un degradado y no como relieve iluminado. Las referencias se leen justamente por la luz sobre la geometría |
| Ondas | Hasta 6 anillos gaussianos (`Rad0/Rad1` que empuja el BP), `HeightStart`/`HeightEnd`, `RingFade` | ✅ La base es buena y Beltrán aprobó los anillos (*"se ve super"*) |
| Gota central | Cuatro intentos: bulto gaussiano, casquete, malla + bulto (*"la unión es re fea"*) y raymarch con `smin` (unos 128 `exp` por píxel, sin medir) | Nunca quedó bien. Beltrán: *"quiero que en verdad se vea como una esfera flotando"* |
| Anillos que suben | `StepRise` con 511 nodos, lógica triplicada | Deuda |
| Visor | Solo se probó la mecánica. **El aspecto nunca se juzgó en el visor** | — |

**Lo que se reutiliza tal cual:** el ring buffer por **distancia integrada** (`RingBirth[]` + `WaveDist`, que admite cambios de velocidad sin saltos), el dispatcher `OnHeartBeat` de `BP_HeartManager_SC` (con el umbral del pecho), el latido falso de `BP_BioHub` y las perillas de alcance que Beltrán ya ajustó (`HeightStart`/`HeightEnd`/`RingFade`).

## 2. La referencia, traducida a mecanismos

| Lo que se ve | Mecanismo |
|---|---|
| Superficie mate que se lee por la luz | Normal **analítica** del campo, calculada en el vertex shader y sombreada por píxel con wrap / half-lambert + brillo rasante |
| La cresta no es un anillo perfecto: tiene "colinas" | Amplitud modulada en ángulo con frecuencias **enteras** (sin costura) y una fase por latido: cada latido pone sus colinas en otro lugar |
| La esfera se asienta en un hoyuelo con borde | **Pozo Ricker invertido** `h = −D·(1−ρ²)·e^(−ρ²/2)`: un solo perfil da el hoyuelo y el borde (en ρ=√3, con altura 0,446·D). Al latir, D crece: el corazón **empuja** la membrana y la onda nace en ese borde |
| Luz azulada bajo la esfera | Charco emisivo analítico + **la esfera como luz puntual** sobre las crestas cercanas. Sin luces reales y sin bloom (con `MobileHDR=False` no hay posproceso) |
| Anillos lejanos como líneas finas de luz (imagen 2) | Línea emisiva en la cresta, **antialiasada con `fwidth`**: donde sería más fina que un píxel, se ensancha y se atenúa en vez de titilar |
| Esferas flotando a distintas alturas | Pool fijo de esferas. Cada latido suelta una **cuando la cresta llega a su punto** (`retardo = r / velocidad`). La membrana hace un bulto, la esfera sale a través de ella y sube |
| Profundidad, horizonte que se disuelve | Niebla **dentro del shader**, que tiende al color del cielo en esa dirección. El borde de la malla desaparece |

## 3. El campo: una sola definición

Una función que usan la membrana (forma y normal), las esferas (empujón y brillo cuando pasa la onda) y el corazón. Se copia **tal cual** del prototipo (GLSL → HLSL es casi literal). Unidades: cm y s. `p` = posición local respecto del centro.

```hlsl
// perfil de un anillo: cresta adelante, valle y eco atrás
float ringProfile(float x){                    // x = distancia a la cresta / ancho
  float behind = step(x, 0.0);
  float a = 1.0 + Tail * behind;
  float g = exp(-(x*x)/(a*a));
  float m = RingMix * behind;
  return g * (1.0 - m + m * cos(Ringing * x));
}
// onda k: d = WaveDist - Birth_k (distancia recorrida), I = intensidad, s = semilla
u    = saturate(d / Reach);
W    = Width * (1 + Spread * u);                         // se ensancha al viajar
x    = (r - (1.732*WellR + d) + warp(θ,s)*W) / W;         // nace en el borde del pozo
amp  = I * lerp(HStart, HEnd, u) * (1 - smoothstep(Fade,1,u)) * smoothstep(0,Birth,d) * hills(θ,s);
h   += amp * ringProfile(x);
// pozo + oleaje de fondo + bultos de nacimiento
h   += -(Depth + WellBeat*Pulse) * (1 - ρ²) * exp(-ρ²/2)   // ρ = r / WellR
     + Swell * sumaDe3Senos(p/SwellScale, t)              // lento, apagado cerca del pozo
     + Σ_j BumpAmp * R_j * campana(edad_j) * exp(-|p-q_j|²/(1.8 R_j)²);
```

- **Colinas y deformación del anillo:** en el prototipo se usa `atan2` con frecuencias enteras. En Unreal conviene la variante sin `atan2`: se rota la dirección por la semilla y se usan polinomios de Chebyshev (`cos2θ = x²−y²`, `cos3θ = x(4x²−3)`). Es más barata y tampoco tiene costura.
- **Lub-dub:** `Pulse = I·(env(t) + Dub·env(t − DubDelay))`, con `env` = ataque smoothstep y caída exponencial. Mueve el tamaño del corazón, su hundimiento, el pozo, el charco y el halo.
- **Opcional, si se busca más "agua":** separar velocidad de grupo y de fase (crestas que nacen atrás del paquete y mueren adelante). No está en el prototipo porque la referencia pide una cresta clara, no un paquete de crestas.

Todas las perillas, con sus defaults, están en el prototipo, agrupadas igual que van a quedar en el BP: `Latido`, `Onda`, `Esfera central`, `Superficie`, `Esferas que emergen`, `Luz, niebla y horizonte`.

## 4. Arquitectura en Unreal

Carpeta nueva **`/Game/SoulCharger/Mechanics/Heart/Scape/`**. No se modifica ningún asset existente: `BP_PulseField_SC` queda parqueado como referencia, igual que el raymarch de la cadena.

| Asset | Qué es |
|---|---|
| `SM_HeartMembrane_SC` | Disco **polar con espaciado geométrico**, generado con Blender headless (`scripts/gen_heart_membrane.py`, versionado como `gen_blob_tube.py`). 256 sectores, `r_j = r_min·q^j` con `q = 1 + 2π/256` (celdas casi cuadradas, triángulos "gordos" como pide Meta para GPUs por tiles), de 2 cm a ~60 m, más un faldón bajo hasta donde la niebla es total. Unos 75k vértices y 150k triángulos: el 10 % del presupuesto de Meta para Quest 3 (1,5 M). La densidad cae como 1/r, al mismo ritmo que se ensanchan las ondas: funciona como un LOD continuo |
| `MPC_Heart_SC` | El estado compartido: `Wave0..Wave7` (vector: distancia recorrida, intensidad, semilla), `Pulse`, `Now`, `bLive`, `Bump0..Bump3`. **Una escritura llega a la membrana, al corazón y a las esferas** (el mismo criterio que `MPC_Perf_SC`) |
| `M_HeartMembrane_SC` | Unlit **opaco**. El **vertex shader** calcula `h` y el gradiente ∇h en coordenadas locales (fp32) y los pasa por `VertexInterpolator` (3 de los 16 escalares disponibles). El **pixel shader** solo normaliza, ilumina, pone niebla, línea de cresta y dither. **Reloj de preview:** con `bLive = 0` (default del MPC), el material genera sus propias ondas periódicas desde `View.GameTime` → **se ve animado en el viewport sin Play**, para autorar mirando. El BP pone `bLive = 1` al empezar |
| `M_HeartOrb_SC` | Master del corazón y de las esferas: unlit **opaco**. Parte de una **copia** del código ya probado de `M_BlobOrb_SC` (normal por píxel, wobble de ameba), no de una referencia, porque ese asset es del secuenciador y está en uso. Instancias `MI_HeartCore_SC` y `MI_HeartEcho_SC` |
| `BP_HeartScape_SC` | **Un solo actor.** Componentes: `Membrane`, `Heart`, `Echoes` (**ISM** de 32 instancias con `PerInstanceCustomData`: posición, momento de salida, tamaño, semilla, ameba sí/no) y `Halo` (plano aditivo chico, opcional). **Cuatro funciones, una por responsabilidad:** `TriggerHeartbeat(Intensity)` (pública, el evento), `StepField(DT)` (integra `WaveDist` y el pulso y escribe el MPC), `SpawnEcho(I)` (siguiente slot del pool, escribe su custom data **una sola vez**) y `ApplyLook` (perillas → MPC/MIDs, también desde el Construction Script) |

**Fuentes de latido** (capa autoral + capa viva, §2.1 de la obra): `bDemo` + `DemoBPM` (reloj propio, para autorar y probar); referencia a `BP_HeartManager_SC` → `OnHeartBeat` (real, gateado por el mando en el pecho); y el BPM de `BP_BioHub` para el ritmo base. La mecánica no toca el input (mandato de mecánicas exportables).

**Por qué ISM y no Niagara ni actores:** el ISM cuesta una draw call para 32 esferas; `PerInstanceCustomData` corre en el renderer móvil (verificado en el código del motor: `MaterialTemplate.ush:1500`, con `r.Mobile.SupportGPUScene = 1` por defecto en 5.8); toda la vida de cada esfera vive en el material (subida, deriva, emerger, empujón de la onda, ameba). Niagara no se previsualiza sin Play, y el perfil de Quest apaga las partículas por GPU. Las esferas van **opacas**, porque las instancias de un ISM no se ordenan entre sí.

## 5. Presupuesto (estimado; se mide antes de darlo por bueno)

| Pieza | Costo esperado | Por qué |
|---|---|---|
| Membrana, vertex shader | Bajo | ~75k vértices × 2 vistas × 8 anillos. Evaluar en el VS sale unas 30–50 veces más barato que por píxel |
| Membrana, pixel shader | Bajo a medio | Una sola capa opaca que cubre ~60 % de la pantalla. La **línea de cresta** es lo único que recorre los 8 anillos por píxel → es la primera perilla si pesa (se puede pasar al VS y aceptarla más gruesa) |
| Esferas (ISM) + corazón | Bajo | Opacas y chicas en pantalla |
| Halo | Muy bajo | Un plano aditivo chico |
| Niebla | Cero extra | Dentro del shader. `ExponentialHeightFog` en móvil es un pase de pantalla completa aparte (`MobileFogRendering.cpp`) |

Se mide con el banco que ya existe (`MPC_Perf_SC` + eventos `ke * PerfN` + `quest_perfmodes.ps1`), con modos 0 = todo · 1 = sin membrana · 2 = sin esferas · 3 = nada, en dos pasadas. Hay que recordar la trampa del instrumento saturado: si todo queda pegado al tope de 72 Hz, las restas no dicen nada.

## 6. Riesgos conocidos y su mitigación

| Riesgo | Gotcha | Mitigación |
|---|---|---|
| Índice dinámico en el vertex shader de Adreno (un ojo o ninguno) | 399 | Topes constantes; las 8 ondas se leen como 8 vectores con nombre, desenrollados. Nada de arreglos locales con índice variable |
| fp16 en el pixel shader (tiempo y coordenadas grandes) | 185, 382 | El campo se calcula en el VS (fp32), en coordenadas locales. El tiempo se lee con `View.GameTime` dentro del Custom. El PS solo recibe `h` y ∇h |
| `TransformPosition(WorldPosition)` en el VS móvil con el nivel lejos del origen | 398 | Usar el nodo `LocalPosition` |
| Culling por WPO | 134 | `BoundsScale` de la membrana y de las esferas (suben hasta `RiseH`) |
| Línea de cresta que titila de lejos | — | Ensanchado con `fwidth` y energía conservada (ya probado en el prototipo) |
| Instancia que nace en cero | 146, 420, 435 | Defaults en el CDO y **leer la instancia colocada** antes de declarar algo verificado |
| MPC con `ParameterId` sin resolver devuelve 0 en silencio | 416 | Control positivo: con `bLive = 1` y un latido forzado, la membrana tiene que cambiar |
| Script fallido que dispara Undo sobre el nivel del otro agente | 60, 418 | Llamadas directas, sin `execute_tool_script`. No abrir niveles. `save_assets` con rutas explícitas |
| Comodidad: ondas que pasan por debajo de un usuario sentado | — | Perilla para apagar la amplitud cerca del usuario. **Se juzga en el visor** |

## 7. Fases de construcción

Cada fase termina con una verificación concreta. Las fases 1 a 4 se pueden hacer **sin abrir ningún nivel**: la membrana y el BP se ven en la preview del asset y en el viewport del editor de Blueprints.

0. ✅ **Lookdev en navegador** (hecho): Beltrán ajusta forma, ritmo y color y copia los valores.
1. **Malla polar**: script de Blender en el repo, import a la carpeta nueva. Verificar la cantidad de vértices y el radio.
2. **`M_HeartMembrane_SC` + `MPC_Heart_SC`** con reloj de preview. Verificar con `CaptureAssetImage` (esperar a que termine la compilación de shaders, gotcha 377) y buscar `Failed to compile` en el log de archivo.
3. **`BP_HeartScape_SC`**: corazón, `TriggerHeartbeat`, demo, `ApplyLook`. Verificar en el viewport del BP.
4. **Esferas que emergen** (ISM, bulto de salida, ameba).
5. **Nivel de prueba `/Game/Test_Heart`**: se crea **cuando el editor esté libre**, porque crear o abrir un nivel cambia el mundo del editor que usa el otro agente. PIE con aserciones por log, las dos variantes (normal y Simulate).
6. **APK + banco de medición.**
7. **Integración**: `BP_HeartManager_SC` (mando en el pecho) y lugar en la obra (¿reemplaza a `PulseField_Heart` en `L_SoulCharger_V3`?). Lo decide Beltrán.

### 7.b Lo construido el 2026-09-27 (fases 1 a 3, paleta azul) y lo que cambió respecto de este plan
Detalle completo en el tracker [`BP_HeartScape_SC.md`](../.claude/skills/unreal-vr/blueprints/BP_HeartScape_SC.md).
- ✅ **Fase 1**: `SM_HeartMembrane_SC`, 78.849 vértices, 600 m con el faldón.
- ✅ **Fase 2**: `M_HeartScape_SC` compila sin errores (PC y ES31); miniaturas del disco de prueba y de la esfera correctas.
- 🟡 **Fase 3**: `BP_HeartScape_SC` compila sin errores; **falta PIE**, que necesita un nivel libre.
- **Un solo master con `Part`** (0 membrana, 1 esfera, 2 cielo; 3 quedará para las esferas de la fase 4) en vez de `M_HeartMembrane_SC` + `M_HeartOrb_SC`: así hay **una sola superficie de autoría**.
- **La autoría vive en `MI_HeartScape_SC`**, con grupos, rangos y descripción por perilla, y **anima sola en el editor**. El actor solo tiene `LookMI` y `bDemo`.
- **MIDs por componente en vez de `MPC_Heart_SC`**: no es global y esquiva la gotcha 416. Los datos del latido van en `Beat` y `Wave0..7` de cada MID.
- El pulso lub-dub se calcula **en el shader** desde `Beat`; el BP no tiene envolvente.

## 8. Decisiones abiertas (de Beltrán)

1. **Color.** En la obra, Recognizing es **rojo**; la referencia es azul. El prototipo trae tres paletas (azul de la referencia, lavanda y una cálida para Recognizing).
2. **Dónde está el usuario.** Afuera, mirando el centro desde arriba (como la referencia), o dentro del campo, con las ondas pasando por debajo.
3. **La subida del guion.** *"Siempre subes, siempre llegas"*: una membrana que desciende despacio vende el ascenso. Pero las esferas que suben lo contrarían en parte (se verían bajar si el usuario sube más rápido que ellas).
4. **Amebas.** Propuesta: las esferas nacen como gota perfecta y **se vuelven ameba mientras suben** (perillas `Proporción de amebas` y `Deformación`), y el corazón con una deformación leve que crece con el latido.
5. **Fuera del umbral.** Hoy, sin el mando en el pecho no hay latido y el campo queda quieto. ¿Queda así, o el paisaje respira al ritmo base del BioHub, más tenue? (§2.2, cero callejones sin salida).

## 9. Qué no se toca

El nivel abierto (`/Game/Test_Entering`), `/Game/Test_Sequencer`, `BP_PulseField_SC` y sus materiales, `M_BlobOrb_SC` (se copia su código, no se referencia), `Core/` y `Config/`.

## Fuentes principales

- Meta, presupuesto de Quest 3 (menos de 200 draw calls y menos de 1,5 M triángulos) y GPUs por tiles: https://developers.meta.com/horizon/resources/device-optimization-comparison/ · https://developers.meta.com/horizon/documentation/unity/gpu-impaired-algorithms/
- UE, Custom Primitive Data (36 floats en 5.8: `SceneTypes.h:38`) y MPC (2 por material: `ParameterCollection.h:18`).
- GPU Gems, cap. 1 (ondas circulares con normales analíticas). Vlachos, *Advanced VR Rendering* (GDC 2015): dither y filtrado de normales contra el aliasing especular.
- Código de UE 5.8 local: `MobileFogRendering.cpp`, `MobileBasePassRendering.cpp:31`, `MaterialTemplate.ush:1500`, `PostProcessing.cpp:287`, `HLSLMaterialTranslator.cpp:1853`, `BaseDeviceProfiles.ini:1480`.
