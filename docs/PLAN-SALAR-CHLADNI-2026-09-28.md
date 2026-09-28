# Plan: el salar de Chladni (entorno de Attracting) — 2026-09-28

**Qué es:** el piso y el cielo de la etapa del secuenciador. Un salar de Uyuni pastel al ocaso (estética Six N. Five) con polígonos de sal y granito. Al empezar cada vuelta del secuenciador, lo que se agregó o sacó en la mesa entra al patrón de una vez: la membrana hace UNA ola con la forma de las figuras de Chladni (la curva de Heart) y deja el mandala en relieve, como las ondas de Heart.

**Cómo se llegó (pedidos de Beltrán, mismo día):** placa de Chladni elegida entre tres ideas → v1 oscura "fea representada" → v2 pastel + Uyuni + Six N. Five + granos de Niagara → v3 arena con física ("mucha info") → v4 sin partículas, membrana como Heart → v5 cambio **por vuelta** del secuenciador, relieve como Heart, granito → v6 centro calmo (sin puntas hacia el centro) + deformación orgánica. Prototipo: `docs/prototipos/placa-chladni.html` · https://claude.ai/artifact/EUUZzbNmfxfHsZhrcE1C2P

**En Unreal:** `BP_ChladniFloor_SC` (tracker: `.claude/skills/unreal-vr/blueprints/BP_ChladniFloor_SC.md`), `M_ChladniFloor_SC`, `T_SaltCells_SC`, en `/Game/SoulCharger/Mechanics/Sequencer/Chladni/`; colocado en `/Game/Test_Sequencer` como `GAL_12_ChladniFloor`. En ese nivel el `BP_Ganzfeld_SC` quedó oculto (editor y juego).

**Cómo se regenera el material:** `python .claude/skills/unreal-vr/scripts/gen_chladni_material.py` (HLSL + `chladni_build.json` + esta tabla) → `apply_chladni_material.py` por `execute_tool_script` (idempotente; ver gotcha 489). Los polígonos: `gen_salt_cells.py` → `T_SaltCells_SC`.

**Estado (fin del 2026-09-28):** Chladni ONDULADO (`Geo` 0) con crestas finas de ancho uniforme (3 cm) y filo; dentro del mandala solo el ondulado sobre arena (`T_SandGrain_SC`), los polígonos del salar solo afuera; el patrón cambia al empezar cada vuelta. Paleta pastel aplicada a esferas y gusano en `Test_Sequencer`, y las esferas ya no se ven grises (`OwnShade` del director). Historia completa de las pasadas en el tracker `BP_ChladniFloor_SC.md`.

**Pendiente:** probar con esferas reales · medir en la Quest · integrar esferas y gusano al desierto (ideas en conversación).

### 7.1 Parámetros del material (defaults)
| Grupo | Parámetro | Tipo | Default | Rango sugerido | Qué hace |
|---|---|---|---|---|---|
| `1 - Figura` | `Sym` | escalar | 5 | 2 … 12 | Simetria radial (ejes). Todos los modos la comparten: la suma siempre es un mandala. 5 rima con Surrounding |
| `1 - Figura` | `Kr` | escalar | 3.5 | 1 … 10 | Anillos de la placa; los modos de cada slot son multiplos |
| `1 - Figura` | `BaseW` | escalar | 0.3 | 0 … 1,5 | Peso de los anillos base |
| `1 - Figura` | `PlateR` | escalar | 720 | 200 … 2000 | Radio del mandala (cm). Afuera, solo el salar |
| `1 - Figura` | `CenterX` | escalar | 0 | -300 … 400 | Centro del mandala hacia adelante (cm, local). 0 = debajo del usuario |
| `1 - Figura` | `Calm` | escalar | 160 | 0 … 500 | Radio del centro calmo (cm): adentro solo anillos, los petalos nacen afuera |
| `1 - Figura` | `Warp` | escalar | 0.4 | 0 … 2 | Irregularidad organica fija de la placa |
| `1 - Figura` | `Geo` | escalar | 0.0 | 0 … 1 | Que tan GEOMETRICAS son las figuras: 0 = ondas de placa redonda, 1 = lineas rectas en 5 direcciones (estrellas y pentagonos, como los poligonos del salar) |
| `1 - Figura` | `Round` | escalar | 0.12 | 0,02 … 0,9 | Esquinas de las lineas geometricas: chico = rectas con esquina viva (se ve pixelado), grande = curvas |
| `1 - Figura` | `GeoFreq` | escalar | 1.8 | 0,5 … 4 | Frecuencia de las lineas geometricas: mas alto = celdas mas chicas (1,8 = celdas de ~2,5 m, cerca de los poligonos del salar) |
| `1 - Figura` | `Sharp` | escalar | 1.6 | 1 … 4 | Filo de las crestas: 1 = loma triangular, mas = mas puntuda. Una cresta con filo parte la luz en dos (lado al sol / lado en sombra) y se lee como RELIEVE, no como pintura |
| `1 - Figura` | `ReliefH` | escalar | 4 | 0 … 15 | Relieve de las LINEAS del mandala (cm, por pixel): crestas finas de sal sobre las lineas nodales |
| `1 - Figura` | `ReliefW` | escalar | 3 | 0,5 … 15 | Medio ancho de cada cresta (cm). Se mide por DISTANCIA real a la linea nodal: todas las crestas tienen el mismo ancho (sin manchones donde la figura es plana) |
| `1 - Figura` | `SwellH` | escalar | 0.5 | 0 … 10 | Loma suave de GEOMETRIA bajo cada linea (cm). La linea fina va por pixel: con vertices saldria facetada |
| `1 - Figura` | `SwellW` | escalar | 0.3 | 0,1 … 0,8 | Ancho de la loma de geometria |
| `1 - Figura` | `EdgeIn` | escalar | 0.5 | 0,1 … 1 | Donde empieza a apagarse el mandala (fraccion del radio). Borde ancho e irregular: sin costura con los poligonos |
| `1 - Figura` | `VibAmp` | escalar | 8 | 0 … 30 | Altura de la ola al cambiar el patron (cm) |
| `2 - Salar` | `SaltLit` | vector | (1.0, 0.9047, 0.8228) |  | Sal al sol |
| `2 - Salar` | `SaltShade` | vector | (0.4735, 0.4342, 0.6308) |  | Sal en sombra |
| `2 - Salar` | `FlatTone` | escalar | 0.7 | 0 … 1 | Tono del piso plano entre sombra (0) y sol (1) |
| `2 - Salar` | `LightGain` | escalar | 2.2 | 0,3 … 4 | Contraste de la luz rasante sobre el relieve |
| `2 - Salar` | `PolyH` | escalar | 0.55 | 0 … 3 | Crestas de los poligonos del salar (0 = desierto liso) |
| `2 - Salar` | `PolyKeep` | escalar | 0.0 | 0 … 1 | Cuanto de los poligonos queda DENTRO del mandala (0 = los borra del todo) |
| `2 - Salar` | `PolyW` | escalar | 5 | 1 … 20 | Ancho de las crestas de los poligonos (cm) |
| `2 - Salar` | `CellSize` | escalar | 150 | 40 … 400 | Tamano de los poligonos (cm) |
| `2 - Salar` | `SaltNoise` | escalar | 0.3 | 0 … 1 | Manchas suaves de la costra |
| `2 - Salar` | `Wet` | escalar | 0.45 | 0 … 1 | Agua: refleja el cielo en angulo rasante |
| `3 - Grano` | `Grain` | escalar | 0.6 | 0 … 1.5 | Contraste de la arena (textura T_SandGrain_SC, con mipmaps: de lejos se funde sola) |
| `3 - Grano` | `GrainSize` | escalar | 80 | 20 … 200 | Tamano del parche de arena (cm): mas chico = grano mas grande |
| `3 - Grano` | `Granite` | escalar | 0.6 | 0 … 1.5 | Granos sueltos oscuros y claros de la arena |
| `4 - Cielo` | `SkyTop` | vector | (0.2705, 0.3663, 0.5972) |  | Cielo arriba |
| `4 - Cielo` | `SkyMid` | vector | (0.5972, 0.4508, 0.6038) |  | Cielo al medio |
| `4 - Cielo` | `SkyHor` | vector | (0.8879, 0.5972, 0.4452) |  | Horizonte |
| `4 - Cielo` | `SunCol` | vector | (1.0, 0.6724, 0.4342) |  | Sol |
| `4 - Cielo` | `SunAz` | escalar | -24 | -180 … 180 | Direccion del sol (grados; 0 = adelante, negativo = izquierda) |
| `4 - Cielo` | `SunEl` | escalar | 2.5 | -6 … 30 | Altura del sol (grados) |
| `4 - Cielo` | `SunSize` | escalar | 7 | 1 … 20 | Tamano del sol (grados) |
| `4 - Cielo` | `SunGlow` | escalar | 0.55 | 0 … 2 | Halo del sol |
| `4 - Cielo` | `Haze` | escalar | 0.55 | 0 … 1 | Bruma del horizonte |
| `4 - Cielo` | `FogDist` | escalar | 2600 | 300 … 8000 | Distancia de la bruma (cm) |
| `4 - Cielo` | `Dither` | escalar | 1.0 | 0 … 3 | Dither contra el banding (en 1/255) |
| `9 - Interno` | `Part` | escalar | 0 | 0 / 1 | 0 piso, 1 cielo (lo pone el Construction Script) |
| `9 - Interno` | `Order` | escalar | 0 | 0 … 1 | Cuanto mandala hay tallado (lo escribe el actor) |
| `9 - Interno` | `W0` | escalar | 0 | 0 … 1 | Cuanto esta tallada la figura del slot 0 (lo escribe el actor) |
| `9 - Interno` | `W1` | escalar | 0 | 0 … 1 | Cuanto esta tallada la figura del slot 1 (lo escribe el actor) |
| `9 - Interno` | `W2` | escalar | 0 | 0 … 1 | Cuanto esta tallada la figura del slot 2 (lo escribe el actor) |
| `9 - Interno` | `W3` | escalar | 0 | 0 … 1 | Cuanto esta tallada la figura del slot 3 (lo escribe el actor) |
| `9 - Interno` | `W4` | escalar | 0 | 0 … 1 | Cuanto esta tallada la figura del slot 4 (lo escribe el actor) |
| `9 - Interno` | `W5` | escalar | 0 | 0 … 1 | Cuanto esta tallada la figura del slot 5 (lo escribe el actor) |
| `9 - Interno` | `W6` | escalar | 0 | 0 … 1 | Cuanto esta tallada la figura del slot 6 (lo escribe el actor) |
| `9 - Interno` | `W7` | escalar | 0 | 0 … 1 | Cuanto esta tallada la figura del slot 7 (lo escribe el actor) |
| `9 - Interno` | `V0` | escalar | 0 | 0 … 1 | Ola de formacion del slot 0, curva de Heart (lo escribe el actor) |
| `9 - Interno` | `V1` | escalar | 0 | 0 … 1 | Ola de formacion del slot 1, curva de Heart (lo escribe el actor) |
| `9 - Interno` | `V2` | escalar | 0 | 0 … 1 | Ola de formacion del slot 2, curva de Heart (lo escribe el actor) |
| `9 - Interno` | `V3` | escalar | 0 | 0 … 1 | Ola de formacion del slot 3, curva de Heart (lo escribe el actor) |
| `9 - Interno` | `V4` | escalar | 0 | 0 … 1 | Ola de formacion del slot 4, curva de Heart (lo escribe el actor) |
| `9 - Interno` | `V5` | escalar | 0 | 0 … 1 | Ola de formacion del slot 5, curva de Heart (lo escribe el actor) |
| `9 - Interno` | `V6` | escalar | 0 | 0 … 1 | Ola de formacion del slot 6, curva de Heart (lo escribe el actor) |
| `9 - Interno` | `V7` | escalar | 0 | 0 … 1 | Ola de formacion del slot 7, curva de Heart (lo escribe el actor) |
