# BP_AttractStreams_SC: los chorros de partículas de Attracting (la ameba te envía el sonido)

**Ruta:** `/Game/SoulCharger/Mechanics/Harp/Blueprints/BP_AttractStreams_SC`
**Colocado en:** `/Game/SoulCharger/Mechanics/Harp/Maps/Test_AttractingHang` como `AttractStreams` (`BP_AttractStreams_SC_C_0`). Está en el PlayerStart (362700, 100000, 0), con yaw 0 y escala 1. La ameba es una `BP_ProtoSoul_SC` con etiqueta `Amoeba`, en (363350, 100000, 150), o sea 6,5 m al frente y 1,5 m de alto.
**Nació:** 2026-11-04, con un boceto de Beltrán: una burbuja que envuelve el hang y al usuario, con un chorro fino que llega desde una ameba lejana.
**Pedido de Beltrán:**
- *"Una amoeba tipo Alma o proto ameba, varios metros frente a nosotros."*
- *"Cada vez que toquemos notas, empezará a emitir partículas que se acercan suavemente hacia nosotros. Son pequeñas, y salen de un solo punto."*
- *"No chocan con nosotros, sino que nos envuelven, como si tuviéramos un campo de fuerza protector."*
- *"Mientras más tocamos, más partículas hay; se nota que con cada nota sale un nuevo chorro que se mantiene constante."*

**⏸️ 2026-11-04: APAGADO.** Beltrán: *"Está interesante. Pero se ve muy sucio"*. En `Test_AttractingHang` la instancia quedó con `MaxStreams` 0: no crea chorros, y para volver a verlo basta con ponerlo en 16. Lo reemplaza la llamada y respuesta de [BP_AttractCall_SC](BP_AttractCall_SC.md). El material y la malla quedan como receta reusable.

**Estado:**
- 🟢 Compila.
- 🟢 PIE con `bDebugNotes`: cada 2,5 s se enciende un chorro, hubo 5-6 en 11-14 s, sin `Accessed None` ni errores de script. Encuentra el hang y lee sus 17 voces (`Seen`).
- 🟢 Vista previa en el editor con 3 chorros, verificada con capturas: el chorro sale del borde de la ameba, cada uno se curva por su lado y se abre en burbuja alrededor del jugador.
- ⬜ Visor: tamaño y legibilidad de las partículas, radio de la burbuja, si se siente "protector", el ritmo.
- ⬜ Tocar notas reales del hang (en PIE solo se probó la nota automática).
- ⬜ Costo en el Quest.
- ⬜ Sin commit.

---

## Cómo funciona (una idea)
**Todo el movimiento lo calcula el material, no hay simulación.** Cada chorro es un `StaticMeshComponent` con:
- la malla `SM_AttractMotes_SC`: 256 cuadraditos apilados; el quad k tiene x = k y las esquinas en ±1 en Y y Z;
- el material `M_AttractMote_SC`.

En el vértice, la partícula k de un chorro nace en `T0 + k/rate`, renace cada `Life` (rate = `Count`/`Life`) y queda donde la pone una fórmula cerrada. El BP no mueve nada: escribe 8 vectores de **Custom Primitive Data** por chorro y nada más. Sin MIDs y sin Niagara. Se ve en el editor sin Play.

**El camino de una partícula**, en polares alrededor del centro de la burbuja `C` (= ojo − `CenterDrop`):
1. **Viaje (`Travel` s, smoothstep):** el radio baja de |E − C| a `Radius` (E = el punto de emisión). Sale lento, acelera y frena al llegar: "se acercan suavemente".
2. **La curva propia:** la dirección gira hasta `Bend` rad alrededor de un eje del chorro, sorteado por su `Seed`. Así cada chorro se curva en su propio plano y llega a la burbuja por otro lado. Todos salen del mismo punto, pero se distinguen.
3. **Envolver:** cerca del final del viaje (70 %) empieza un giro sobre la burbuja. La rampa es un softplus, así la velocidad no salta. Cada partícula gira alrededor de su propio eje (el del chorro ± `Spread`), lo que abre el chorro en abanico sobre la esfera. La velocidad tangencial es `Swirl` cm/s y el sentido sale de la semilla.
4. **Vida orgánica:**
   - `Wobble` cm de ondulación lateral: es coherente por tiempo de emisión, así el chorro se ve como una manguera que se mueve, no como ruido;
   - `Jitter` cm por partícula, que crece desde 0 en la boca;
   - `ShellNoise` cm de espesor de la burbuja;
   - `Squash`, que achata la burbuja en vertical para no pasar por el piso.
5. **Tamaño:** `Size` cm de diámetro, con un mínimo aparente de `MinAngle` rad visto desde el ojo, para que el chorro lejano no desaparezca bajo el píxel. Cada quad mira al ojo, no a la cámara de cada ojo (sin diferencias en estéreo).
6. **Luz:** **translúcido (alpha)**, sin luz. Emisivo = color^`ColorPow` × `Brightness`. Opacidad = punto suave (1 − r²)², con fundido de entrada `FadeIn` y de salida `FadeOut`.
   - 🔴 **Aditivo NO.** El salar es claro y lo aditivo se lavaba a blanco: casi no se leía (capturas `as_pov*.png` del 11-04).

**Las notas:** no se toca el grafo del hang.
- Cada cuadro se lee `BP_Harp_SC.LastPluck` (un tiempo por voz).
- Una voz con un valor más nuevo que el visto (`Seen`) es una nota: se abre el próximo chorro libre, con `NoteColor(voz)` del hang como color.
- Hasta `MaxStreams` (16). Después, las notas suenan pero no abren chorros nuevos.

**La burbuja sigue a la cabeza:**
- `Eye` = la cámara del jugador, suavizada con `Follow` (1/s);
- si salta más de 3 m (primer cuadro o recentrado), va directo.

## Custom Primitive Data (el contrato BP ↔ material)
| Índice | Vector | x | y | z | w |
|---|---|---|---|---|---|
| 0 | `SA` | T0 (reloj del mundo = `View.GameTime`) | Seed | – | – |
| 4 | `SC` | color R | G | B | `ColorPow` |
| 8 | `CE` | ojo local X | Y | Z | `Radius` |
| 12 | `EM` | emisión local X | Y | Z | `Squash` |
| 16 | `K1` | `Life` | `Count` | `Travel` | `Bend` |
| 20 | `K2` | `Spread` | `Swirl` | `Wobble` | `WobbleHz` |
| 24 | `K3` | `Jitter` | `ShellNoise` | `CenterDrop` | `FadeIn` |
| 28 | `K4` | `Size` | `MinAngle` | `FadeOut` | `Brightness` |
Son 32 floats; el tope de Unreal es 36. Las posiciones van en el **espacio local del actor**: el material las pasa a mundo con un Transform Local→World del WPO. Así no hay coordenadas de 362.000 cm dentro del shader.

## Registro de variables (Details del actor)
- **0-Enlace:**
  - `Harp`: el hang. Vacío = lo busca por clase en `AsBoot`.
  - `Amoeba`: la ameba que emite. Vacía = `NoAmoebaAt`.
- **1-Chorros:**
  - `MaxStreams` 16.
  - `Count` 160: partículas por chorro, ≤ 256.
  - `Life` 16 s: vida de cada partícula.
  - `Travel` 7 s: de la ameba a la burbuja.
  - `Bend` 0,5 rad: curva propia de cada chorro.
  - `Wobble` 8 cm, a `WobbleHz` 0,12.
  - `Jitter` 2 cm.
- **2-Envoltura:**
  - `Radius` 115 cm, alrededor del ojo.
  - `Squash` 0,75: vertical.
  - `CenterDrop` 20 cm: el centro, debajo del ojo.
  - `Swirl` 20 cm/s: giro sobre la burbuja.
  - `Spread` 0,6: abanico.
  - `ShellNoise` 8 cm: espesor.
  - `Follow` 1,5 1/s.
- **3-Luz:**
  - `Size` 0,45 cm, cerca del 0,35 que pidió para Focus.
  - `MinAngle` 0,0025 rad: unos 3,5 px en el Quest.
  - `FadeIn` 0,6 s y `FadeOut` 3 s.
  - `Brightness` 1,3.
  - `ColorPow` 2: satura el pastel de la nota.
  - `MoteMesh` = `SM_AttractMotes_SC` y `MoteMat` = `M_AttractMote_SC`.
- **4-Fuente:**
  - `EmitOffset` 30 cm: desde el centro de la ameba hacia el ojo, o sea su borde (`Size` 0,6).
  - `PreviewEye` (0, 0, 115): el ojo, local, para la vista previa.
  - `NoAmoebaAt` (650, 0, 150).
- **5-Prueba:**
  - `PreviewStreams` 3: chorros que se ven en el editor.
  - `bDebugNotes`: una nota de color al azar cada `DebugEvery` (2,5 s), para PIE sin visor. Prenderla en la instancia ANTES del Play y apagarla después.
- **Z-Estado:**
  - `Streams`: los componentes.
  - `Seen`: el último `LastPluck` visto por voz.
  - `Used`: chorros encendidos.
  - `Eye`: ojo suavizado, en mundo.
  - `EmitW`: punto de emisión, en mundo.
  - `NextDebug`.

## Grafos (una función por responsabilidad)
- **ConstructionScript** → `AsBuild`.
  - Crea `MaxStreams` componentes (malla, material, sin colisión ni sombra).
  - `AsLook` en cada uno.
  - Los primeros `PreviewStreams` quedan visibles y "ya formados": T0 = ahora − 600 s, color HSV con tono 20 + 47·i y **semilla fija = ese tono**, así la vista previa no se vuelve a sortear al tocar perillas.
- **BeginPlay** → `AsBoot`:
  - `Used` en 0;
  - perillas a todos y todos ocultos;
  - `Seen` = el `LastPluck` del hang, o busca el hang si falta.
- **Tick** → `AsTick(min(Dt, 0,05))` → `AsDebug` → `AsFollow` → `AsSenseHarp` (si hay hang).
- `AsLook(Comp)`: K1..K4.
- `AsStart(Comp, T0, Col, Seed)`: SA, SC y lo hace visible.
- `AsPlace(Comp, EyeL, EmitL)`: CE y EM.
- `AsEmitUpdate()`: `EmitW` = ameba + dirección al ojo × `EmitOffset`.
- `AsSenseHarp()`: compara `LastPluck` con `Seen` y llama `AsAdd(NoteColor(i))`.
- `AsAdd(Col)`: el próximo chorro libre con `AsStart` (semilla al azar) + `AsPlace`, y `Used++`.
- `AsFollow(Dt)`: si hay cámara, `Eye` suavizado, `AsEmitUpdate` y `AsPlace` de los chorros encendidos.
- `AsDebug()`.

**Fuente:** `scripts/attract/`.
- `streams_src.dsl` + `gen_streams_dsl.py` (→ `streams_dsl.json`) y `build_streams.py`: variables y funciones. Copia del pipeline de `feed/`.
- `gen_mote_material.py` (HLSL + plan) + `apply_attract_material.py`: arma el material. Copia de `apply_chladni_material.py`; se puede repetir.
- `gen_motes_obj.py`: la malla.
- El HLSL va en `.txt` porque `read_file` no acepta `.hlsl` (gotcha 525).

## Costo esperado
- Un draw call translúcido por chorro encendido, 16 como máximo.
- Cada uno tiene 1024 vértices con dos Custom de vértice (WPO y alfa) que repiten el mismo cálculo, y quads diminutos.
- El fill es despreciable.
- CPU: 2 escrituras de CPD por chorro y por cuadro.
- ⬜ Medir en el Quest.

## Session log
- **2026-11-04:** construido entero.
  - Las capturas de forma se sacaron con `Size` 3 cm y `MinAngle` 0 en la instancia, y después se devolvieron a los valores del CDO.
  - El primer material era aditivo; se pasó a translúcido porque no se leía sobre el salar.
  - Se sacó la atenuación por distancia, que dejaba al chorro lejano invisible.
  - Se le agregó el parámetro `Seed` a `AsStart`. Tenía llamadores, así que rompió el compile (gotcha 333): se recrearon los dos nodos de llamada por cirugía.

## TODO
- [ ] Visor con Beltrán: tamaño, `MinAngle`, `Radius`, `Swirl`, `Travel`, si se siente "protector".
- [ ] Qué pasa con la nota 17 en adelante: ¿reciclar el chorro más viejo con fundido?
- [ ] ¿La ameba reacciona al emitir (pulso, brillo)? Hoy no se toca.
- [ ] El salar sigue quieto. ¿Le llega algo de los chorros?
- [ ] Medir en el Quest.
