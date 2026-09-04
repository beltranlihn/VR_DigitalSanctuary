# PLAN — `BP_Card`: la carta física de resultados (2026-09-02)

> **Pedido de Beltrán:** *"Creo que la parte mas debil de la experiencia es al final, con las cartas
> que muestran los graficos y resultados. Intentamos asociarlos al BP de la ameba, pero creo que no
> funciona. Nos conviene armar un BP especifico de la carta de resultados, literalmente que sea una
> carta fisica."*
>
> **La tarjeta deja de ser un panel colgado de la ameba y pasa a ser un OBJETO** — un mesh con seis
> huecos, y cada elemento de la obra encajado dentro del suyo.

---

## 1. Por qué lo de hoy no funciona (el diagnóstico, antes de proponer nada)

Hoy el "retrato" está repartido entre **tres** Blueprints, y ninguno es dueño del conjunto:

| Pieza | Dónde vive hoy | El problema |
|---|---|---|
| Los 3 gráficos | `WidgetComponent` **dentro de** `BP_ProtoSoul_SC` (`Card`) | La ameba, que es *contenido*, es la dueña del *contenedor*. |
| Las esferas de melodía | `BP_Portrait_SC` las spawnea, attacheadas al `OrbAnchor` de la ameba | Dos dueños para una sola fila; ya costó el bug de "las esferas se quedan en el world". |
| El dibujo / firma | `BP_Sensor_Soul.ShowSignature()` sobre `TP_signature_spot`, que `BP_Constellation_SC` **mueve en runtime** | Un TargetPoint autoral usado como variable temporal: la posición de autor y la de runtime se pisan. |
| El panel viejo | `BP_Portrait_SC` (1600×900) | Quedó como "director de melodía" sin panel: un actor a medio vaciar. |

**La raíz es una sola: no hay ninguna entidad que represente "la carta".** Cada elemento se coloca por
su cuenta, con su propio offset relativo a la ameba, y por eso cada vez que algo se mueve hay que
re-derivar cuatro offsets. La deuda ya está anotada en dos trackers ("lo que NO viaja todavía").

👉 **La corrección es invertir la dependencia:** la carta es el contenedor, y la ameba pasa a ser uno
de sus seis contenidos, igual que el dibujo o las curvas.

---

## 2. Lo que ya está en disco (medido hoy, no supuesto)

**Mesh `/Game/Card`** — 122 vértices · bounds **200 × 178 × 10 cm** (acostado en el asset).
**`/Game/BP_Card`** — `DefaultSceneRoot` → `Card` (StaticMeshComponent, **roll 90** → la carta queda
**de pie**: 200 cm de ancho en X, 178 cm de alto en Z, 10 cm de espesor en Y) → y colgando de él, los
**6 `TextRender`** que Beltrán puso como marcadores: *Ameba · Dibujo · Grafico Calm · Grafico Heart ·
Grafico Breath · Melody*.

🔑 **Esos 6 TextRender son el mapa de huecos**, y por eso el plan no necesita adivinar nada. Como son
hijos de `Card` (que lleva el roll), en el espacio del **actor** vale: `X_actor = X_local` y
**`Z_actor = −Y_local`**.

### El mapa de huecos

Centro de cada hueco y su tamaño útil, en cm, respecto del centro de la carta:

| Hueco | X (horizontal) | Z (vertical) | Ancho | Alto |
|---|---|---|---|---|
| **Ameba** (arriba izq.) | −57,7 | +48,5 | ~71 | ~67 |
| **Dibujo** (arriba der.) | +38,3 | +48,5 | ~110 | ~67 |
| **Calm** | −2,4 | 0 | ~185 | ~22 |
| **Heart** | −2,4 | −25 | ~185 | ~22 |
| **Breath** | −2,4 | −50 | ~185 | ~22 |
| **Melody** | −2,4 | −75 | ~185 | ~22 |

⚠ **Los centros salen de tus TextRender (exactos); los anchos y altos salen de la proporción de tu
captura (±2 cm).** No se hardcodean: el plan los convierte en **anclas que se arrastran** (§4, F1), así
el número final lo define Beltrán mirando. Dos observaciones de la medición que conviene tener presentes:
el hueco del **dibujo es notablemente más ancho que el de la ameba** (110 vs 71 cm), y los cuatro
huecos de abajo son **la misma ranura repetida cada ~24,5 cm**.

⚠ El mesh usa hoy **`M_DoorSolid`**, que está gobernado por `MPC_Room.RoomLight` — el escalar del
fundido de salas. Tal como está, **la carta se apagaría con la sala**. Necesita material propio (F0).

---

## 3. Las cuatro decisiones de arquitectura

**D1 · La carta es el contenedor.** `BP_Card` es el único dueño de la composición. Su API pública es
**una sola puerta**: `Feed(Index)` — con el índice de una entrada de [[BP_SoulArchive_SC]], o `-1` para
"la corrida de ahora". Todo lo demás (dónde va la ameba, qué tamaño toma el dibujo, cuántas esferas
suenan) es asunto interno de la carta.

**D2 · Una sola carta en el mundo, que se re-alimenta.** No una carta por estrella. En la constelación
la carta viaja a la estrella enfocada y se le alimenta el índice del vecino; en el retrato propio se
alimenta con `-1`. Esto conserva el hallazgo que ya nos costó caro —*20 paneles no entran en Quest,
esconder un `WidgetComponent` no libera su render target*— pero de una forma más simple que
`WidgetClass=None`: **sólo existe un panel, siempre**.

**D3 · Los huecos se autoran arrastrando, no se calculan.** Cada hueco es un ancla visible en el
viewport (un plano con contorno, `bHiddenInGame`): se mueve y se escala hasta que encaje contra el
mesh, sin Play y sin tocar el grafo. Es la misma técnica de `BP_BreathRing_SC`, y es la que respeta que
**Beltrán autora mirando**.

**D4 · Cada contenido entra por su naturaleza, no todo por UMG.**

| Hueco | Qué se encaja | Cómo |
|---|---|---|
| Ameba | `BP_ProtoSoul_SC` **real** | `AttachActorToComponent(SnapToTarget)` al ancla + `Size` para que el halo entre |
| Dibujo | `BP_DrawCanvas` **real** | attach al ancla + escala normalizada al hueco |
| Calm / Heart / Breath | **un widget por ranura** | un `WidgetComponent` colgado de cada ancla |
| Melody | 8 `BP_SoundOrb_SC` **reales** | attach al ancla, paso 23 cm |

🔑 **Un widget por ranura, no uno solo que cubra la carta** (corrección del 2026-09-02, al construir las
anclas). La primera versión de este plan proponía un único lienzo de 1000×890 px con los tres gráficos
diagramados adentro; **eso ataba el layout interno a la geometría del mesh**: mover un ancla habría
obligado a re-diagramar el widget. Con un widget por ranura, cada uno **cuelga de su ancla y llena su
rectángulo**, así que mover o escalar el ancla mueve y redimensiona el gráfico sin tocar nada más — que
es justamente la promesa de D3.

Y sale más barato: tres lienzos de **925 × 110 px** (185 × 22 cm a 5 px/cm) son **1,2 MB** de render
target contra los 3,5 MB del lienzo único, y cada `OnPaint` dibuja **una** curva en vez de tres.

Los widgets van **detrás del mesh**: los huecos son pasantes, así que **el marco físico recorta el
dibujo** — da profundidad real y perdona un par de milímetros de desalineación.

---

## 4. Las fases

Cada fase termina con un **criterio de aceptación medible** (log o medición en PIE, no "compila"). El
orden está pensado para que **la carta sea verificable sola antes de tocar nada de la obra** — que es
justamente lo que faltó la vez pasada.

### F0 · Preparar el asset (barato, sin lógica)
1. **Mover** `/Game/BP_Card` y `/Game/Card` a `Core/Card/` (hoy están sueltos en la raíz de `Content/`).
2. **Material propio** `M_Card` (duplicado de `M_DoorSolid` **sin** el `RoomLight`), o el que definas —
   si no, la carta se apaga con el fundido de sala.
3. **Colisión off** en el `Card` por código en `BeginPlay` (`NoCollision`): un mesh sólido de 2 m se
   comería el beam de la exploración. 🔴 Ponerlo sólo en el CDO **no alcanza** — la instancia lo
   revierte (ya nos pasó con el panel del retrato).
4. Los 6 `TextRender` pasan a ser **etiquetas de debug** detrás de un `bShowSlotLabels` (default
   `false`), no se borran: son la referencia de la que salió el mapa.

**Aceptación:** la carta se ve en un nivel de prueba con su material propio, no se apaga con la sala y
un trace la atraviesa.

### F1 · El esqueleto: seis anclas arrastrables
Seis componentes ancla (`SlotAmoeba`, `SlotDraw`, `SlotCalm`, `SlotHeart`, `SlotBreath`, `SlotMelody`),
hijos de `Card`, en las posiciones de la tabla del §2. Cada uno es un **plano con contorno**, visible en
el viewport y **`bHiddenInGame`**. Convención de tamaño: **la escala del ancla ES el tamaño del hueco**
(`X = ancho/100`, `Z = alto/100`), así el contenido se ajusta solo cuando la arrastrás.

**Aceptación:** en el viewport del Blueprint, los seis rectángulos coinciden con los seis huecos del
mesh. Es una verificación **visual tuya**, no un log — y es el único momento del plan en que hace falta
tu ojo antes de seguir.

### F2 · Los tres gráficos
Tres `WidgetComponent` (925 × 110 px, escala 0,2), uno por ancla:
- **`WBP_CardCurve`** — una curva que llena el lienzo, por `OnPaint` + `DrawLines`. Se usa **dos veces**
  (calma y ritmo), con el color como variable. Un solo widget para dos ranuras.
- **`WBP_CardRings`** — la fila de anillos de respiración, repartida a lo ancho del lienzo.

**Se porta de `WBP_Portrait_SC`**, que ya tiene resuelto todo esto (`SetSeries`, `ParseSeries`,
`Normalize`, `BuildCurve`, `LayoutRings`) y ya cazó sus bugs — en particular la trampa de
`MinOfFloatArray`, que llegaba al DSL con salida entera, truncaba, y dejaba la curva plana pegada al
piso. **No se reescribe: se duplica.** Lo que se simplifica es la diagramación: al llenar cada widget su
propio lienzo, desaparecen los tres marcos y el `SlotAsCanvasSlot` que los seguía.

**Aceptación:** con `bFakeData`, el log de `Rebuild` da `p0/pmed/pfin` con **Y distintos** y dentro del
marco, y las tres curvas caen dentro de sus huecos vistas en PIE.

### F3 · La ameba encajada
`Feed` attachea la `BP_ProtoSoul_SC` correspondiente al `SlotAmoeba` y le fija el `Size`. El tamaño lo
manda **el halo de anillos, no el cuerpo**: `radio visible = 83 cm × Size`. Para un hueco de 67 cm de
alto → **`Size ≈ 0,78`**.
🔴 El tamaño va por `Size`, **nunca** por la escala del actor: la doble aplicación de escala ya nos dio
0,35 pedido → 0,1225 real.

**Aceptación:** medición en PIE de la posición mundial del `Body` contra la del ancla (delta < 1 cm) y
del diámetro del halo contra el alto del hueco.

### F4 · El dibujo encajado
El `BP_DrawCanvas` reconstruido se attachea al `SlotDraw` y se escala para que su bounding box entre en
110 × 67 cm (la normalización de tamaño ya existe, del paquete del 2026-08-28).
🔴 **Esto retira el uso de `TP_signature_spot` como variable de runtime.** El TargetPoint queda para lo
que era: la posición autoral de la firma en el momento del retrato.

**Aceptación:** `firma reconstruida` + bounding box medida dentro del hueco, con dos dibujos de tamaños
distintos (uno chico y uno que desborde) para probar la normalización.

### F5 · La melodía encajada
Las 8 `BP_SoundOrb_SC` se attachean al `SlotMelody` (paso 23 cm, diámetro ≤ 20 cm). Se porta de
`BP_Portrait_SC` el motor que ya funciona: `BuildMelody` / `PairOrb` / `OneOrb` / `SwapMelody` y el
**tempo derivado del pad** (`PadSound.Duration / 8` = 0,667 s), que es lo que hace que suene al mismo
compás al que el usuario la armó.
🔴 Dos trampas ya documentadas que se heredan tal cual: `MelodySounds`/`MelodySteps` son
**instance-editable y nacen en cero** en el actor colocado (hay que llenarlas en la instancia, no sólo
en el CDO), y `Class|SoundBase|GetDuration` tiene 16 homónimos.

**Aceptación:** `esferas reales sembradas = N` con N = las notas del CSV, centro de la fila coincidente
con el ancla, y la fila **se mueve con la carta** (medir después de mover el actor).

### F6 · Enganche y retiro de lo viejo
1. **Retrato propio** (`BP_Director_Story.RunEnding` sub 6): `ShowPortrait()` pasa a llamar
   `Card.Feed(-1)` + `Card.Show()`.
2. **Constelación**: `Focus()` → la carta viaja al ancla y `Feed(ArchIdx)`; `Unfocus()` → `Hide()`.
   Desaparecen `ShowCard`/`HideCard`/`FeedMelody`.
3. **Se retiran** (con tu visto bueno, no antes): el `Card` WidgetComponent y el `OrbAnchor` de
   `BP_ProtoSoul_SC`, y `BP_Portrait_SC` entero.
   🔴 Retirarlos **es parte del plan, no una limpieza opcional**: dejar los dos sistemas conviviendo es
   exactamente cómo quedaron "varias cosas rotas" la vez pasada.

**Aceptación:** una corrida completa del final en PIE, **cero `Accessed None`**, y 12 vecinos seguidos
con series y melodías distintas (la misma prueba que pasó la constelación el 2026-08-27).

### F7 · Visor
Lo que se mide se cierra por log; **el tamaño, la distancia y la legibilidad de una carta de 2 m sólo se
juzgan con las gafas puestas.** Iteramos en vivo como el 2026-08-26.

---

## 5. Riesgos, con su mitigación (no como advertencia suelta)

| Riesgo | Mitigación, dentro del plan |
|---|---|
| Una carta de **2 × 1,78 m** puede ser enorme frente a la cara | La distancia y la escala son knobs de instancia desde F1; se decide en F7 con el visor. Si hay que achicarla, se achica el **actor**, y todo lo demás la sigue por attach. |
| El widget detrás del mesh **no coincide** con los huecos | Cada widget cuelga de su ancla y llena su rectángulo: coincide por construcción, y se corrige arrastrando el ancla. |
| El mesh cambia y se rompe el mapa | Las anclas son componentes arrastrables (D3): re-encajar es mover seis rectángulos, sin tocar código. |
| Perder trabajo del nivel por un script que falla | Regla estándar: `try/except BaseException` + canario de actores antes y después de cada tanda, y **commit antes de empezar** (hoy hay ~30 archivos modificados sin commitear). |

---

## 6. Lo que hace falta del lado de Beltrán

1. 🔵 **F1 es tu ojo, y es lo único que bloquea el resto**: las seis anclas ya están puestas en
   `BP_Card`. Abrirlo, mirarlas y arrastrarlas/escalarlas hasta que cada rectángulo tape su hueco.
2. ✅ **Resuelto (2026-09-02): el frente es la cara +Y.** *"Si miro de frente la carta, veo la ameba
   arriba a la izquierda"* — ver el razonamiento en el tracker [[BP_Card]].
3. **El material de la carta** — si prefieres algo distinto de una copia de `M_DoorSolid` sin `RoomLight`.
4. **Los 4 huecos de abajo son idénticos en tamaño**; hoy el orden es Calm · Heart · Breath · Melody.
   Si prefieres otro orden, este es el momento (es reordenar anclas, no lógica).

---

## Relacionados
[[BP_Portrait_SC]] (de donde se porta el widget y la melodía) · [[BP_Constellation_SC]] (el consumidor
del final) · [[BP_ProtoSoul_SC]] (pierde el `Card` y el `OrbAnchor`) · [[BP_SoulArchive_SC]] (la única
fuente de datos) · [[BP_SoundOrb_SC]] · `docs/PLAN-CIERRE-2026-08-27.md` (el plan del que sale este)
