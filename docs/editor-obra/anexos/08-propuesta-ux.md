> Anexo de la auditoría del 2026-10-01 (propuesta de UX (antes de la crítica y de los pedidos de Beltrán: inglés, sin mute/solo, sin herramientas de ISP)). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md); donde este anexo lo contradiga, gana el plan.

# Editor de gameplay y narrativa de Soul Charger: diseño de UX/UI sobre el código de Immersive Studio Pro

**Regla general:** el editor nuevo usa el CSS y los componentes de Immersive Studio Pro (en adelante ISP; hoy VEATION), copiados o adaptados. No se inventa otra estética. Las rutas `ISP/…` son relativas a `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/Immersive Studio Pro/`.

ISP es vanilla JS sin paso de compilación, con binding manual del estado a la pantalla (`ISP/ARCHITECTURE.md:21`, `:108`). El editor web hereda las dos cosas:
- **Sin bundler.** Va un `<script>` por dominio, que es la "evolución posible" que prevé `ISP/docs/adr/adr-0001-sin-build-step.md`.
- **La misma disciplina de repintado.** Las funciones se llaman igual que en ISP: `renderTimeline()`, `scheduleTimeline()` y `renderInspector()`.

En el punto 9 hay una tabla que dice, componente por componente, qué se toma tal cual, qué se adapta y qué es nuevo.

---

## 1. Layouts

### 1.1 Medidas que no cambian (salen de ISP)

**Barras y paneles**

| Pieza | Medida y estilo | Fuente en ISP |
|---|---|---|
| Barra superior | 28 px, `--s1` | `index.html:123` |
| Menús | Botones de 20 px y 12 px/500 | `index.html:972` |
| Barra del visor | 28 px; grupos tipo *well* de 22 px con botones de 16 px | `index.html:223-228` |
| Cabecera de panel | 28 px, `--s0` | `index.html:139` |
| Biblioteca (columna izquierda) | 292 px | `index.html:1227` |
| Inspector | 300 px en ISP | `index.html:1338` |
| Divisores | 5 px, arrastrables de 180 a 560 px | `index.html:146`; `gutter()` en `app.js:16308` |
| Panel plegado | Riel de 34 px con rótulo vertical | `index.html:1139-1144` |
| Barra de estado | 22 px, texto de 10,5 px | `index.html:792` |

**Inspector a 320 px.** Las etiquetas en español ("Cortafuegos", "Fundido de salida") no caben en los 60 px de `.prow .lab` (`index.html:327`). Por eso la etiqueta sube a 84 px y el inspector a 320 px. Es la única desviación de medida. Todo lo demás de `.prow` se mantiene igual (`index.html:321-349`):
- fila de 24 px;
- fader de 3 px pintado con el color del parámetro;
- recuadro de valor de 42×16 px sobre `--s0`;
- rombo de 20×20 px.

**Transporte y timeline**

| Pieza | Medida y estilo | Fuente en ISP |
|---|---|---|
| Transporte | 28 px sobre `--bar #242424`, la única barra con ese color | `index.html:356` |
| Botones del transporte | Play de 30×22 px, demás botones de 22 px | `index.html:358-361` |
| Caja de timecode | 22 px; dígitos de 12,5 px/500 | `index.html:363-364` |
| Timeline (alto por defecto) | 402 px; asa de 5 px; alto acotado entre 170 px y el 78 % de la ventana | `index.html:412-413`; `hResize` en `app.js:16323` |
| Riel de herramientas | 34 px, botones de 24 px | `index.html:416-417` |
| Cabeceras de pista | 168 px | `index.html:419` |
| Regla | 24 px | `RULER_H`; `index.html:564` |
| Barras de zoom horizontal y vertical | 12 px cada una | `index.html:543-563` |

### 1.2 Modo todo en uno (1920×1080)

El inspector va a la derecha y ocupa toda la altura, igual que en `02-workspace-dome.png`.

```
┌─28─ File  Edit  Obra  Ventana ········· Soul Charger · Obra   rev 44 · típico 17:09   [● Unreal al día ▾] ┐
├──────────────────┬──────────────────────────────────────────────────────────────┬─────────────────────┤
│ OBRA        292  │28 [POV|Libre|Planta] [⚓ ◉ ⧉ ◠ ♪] [Editar|Jugar]    100%  Salida▾│ [Inspector|Notas] 320│
│[Escenas|Elementos│                                                              │█ franja 4 px (color)│
│ |Audio|Notas]    │                 VISOR 3D  ≈1308×572                          │ ◼ Timbre · aparece  │
│ chips de filtro  │  «Activo ahora» (arriba a la izq.)    ◇ anclas con rótulo     │ OBJETO · 1,5 S  [Unreal▸]
│ ▸ 0 Arranque     │                                                              │ ▾ Tiempo            │
│ ▾ 1 Inicio       │          gizmo en el marco de la parada                      │ ▾ Aparición         │
│   1.8 Timbre     │                                                              │ ▾ Lugar             │
│   ...            │                                                              │ ▸ Avanzado          │
├──────────────────┴──────────────────────────────────────────────────────────────┤                     │
│28 [Obra|Entering·mec ×][+] [Rápido|Típico|Lento|Ausente]  [ ⇤ ▶ ⇥ ] 06:24.3│+4,2 s G_BREATH [Obra|Momento] ⟳ ⚑  [Anclas|Lógica|Fit] −＋ │
├──┬───────────────┬─────────────────────────────────────────────────────────────────────────┬──┤
│34│ 168           │ Actos 18  ▕ 1 Inicio ▕ 2 Hall ▕ 3 ▕ 4 Entering ▕ ...                   │12│
│  │               │ Regla 24  (TC arriba · notas y locators abajo)                         │  │
│  │               │ Momentos 16  ⎸1.8 ⎸1.9 ⎸2.1 ...                                        │  │
│ V│ ▾ Narrativa  +L M S│▒▒▒▒▒ fila de grupo 24 (s1) ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│  │
│ H│    1 Alma     │ [VO_11 ∿∿∿ "Just below your ribs…"] [VO_12 ∿∿∿ …]                       │  │
│ T│    2 Ayudas   │          ┆VO_11h┆                                                    │  │
│ B│ ▾ Interacción │ [G_BREATH ///////]┄┄┄┄┄┄┄ cola ┄┄┄┄┄┄┄▌25                              │  │
│ Z│ ▸ Objetos (6) │ ▬▬ ▬ ▬▬▬ ▬  (plegado: sólo títulos)                                     │  │
│  │ ▾ Sonido (tinte)│ ◆FX_BELLRING   ◆FX_…                                                │  │
├──┴───────────────┴──────────────────────── zoom H 12 ──────────────────────────────────┴──┤
│ [cajón Lógica, 220 px, opcional, punto 3]                                                    │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│22 Listo · Seleccionar (V) — … │ típico 17:09 · meta 15:00 (+2:09) │ 3 notas │ Unreal rev 41 · partitura 44 │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Columna izquierda, "Obra".** Es el panel Media de ISP, con su cabecera, sus filtros tipo *well* y su lista de filas (`.mitem/.mthumb/.mname/.mmeta`, `index.html:182-216`). Tiene cuatro pestañas:

- **Escenas:** árbol actos → momentos → elementos. Un clic lleva el cabezal a ese punto y aplica el zoom de `zoomToClip`.
- **Elementos:** las entidades, con su tag de Unreal y la cantidad de clips de cada una.
- **Audio:** los 116 audios, con forma de onda y estado ("cableado", "huérfano"). Arrastrar uno al timeline crea su clip.
- **Notas:** ver el punto 7.

### 1.3 Modo de dos pestañas

Una pestaña muestra la vista 3D y la otra el timeline. Es la misma idea que la **ventana solo-visor** de ISP, que siempre muestra la vista complementaria a la del editor: el código está en `openViewerWindow`/`viewerPump` (`app.js:2486`, `:2583`), descrito en `COMPONENTS.md:2174-2189`.

```
PESTAÑA «VISTA 3D»                                  PESTAÑA «TIMELINE»
┌28 barra superior (igual)               [● sync]┐  ┌28 barra superior (igual)                 [● sync]┐
├28 barra del visor (cámaras, superposiciones,   │  ├28 TRANSPORTE completo (persona, TC, edición)    │
│   persona, Editar|Jugar)                    │34 │  ├────────┬─────────────────────────────┬─────────┤
│                                             │rie│  │ OBRA   │ TIMELINE a toda la altura    │INSPECTOR│
│        VISOR ≈ 1586×950                     │ l │  │ 292    │ (≈24 sub-pistas visibles)    │ 320     │
│  Activo ahora · anclas · gizmo · cono       │ i │  │        │                             │         │
│                                             │ n │  │        ├─────────────────────────────┤         │
│                                             │ s │  │        │ cajón LÓGICA 260 (abierto)   │         │
├28 transporte compacto (sin el grupo de edición)│  ├────────┴─────────────────────────────┴─────────┤
├24 MAPA de la obra: actos + cabezal (clic = ir)  │  │22 barra de estado                               │
├22 barra de estado                               │  └──────────────────────────────────────────────────┘
└─────────────────────────────────────────────────┘
```

En la pestaña 3D, el inspector arranca plegado en su riel de 34 px. Al abrirlo muestra el mismo componente que la otra pestaña.

La pestaña de timeline puede mostrar un **monitor flotante** opcional: el monitor de origen de ISP (`#srcMon`, `index.html:751-785`) con el punto de vista del usuario a 320×180 px. Sirve para trabajar con una sola pantalla.

**Qué pasa en cada pestaña**

| Evento | Pestaña timeline (dueña del reloj) | Pestaña 3D |
|---|---|---|
| Reproducir o mover el cabezal | Lleva el reloj y el único audio. Emite `{playing, t0, wall0, speed}` **una vez por evento**, no por cuadro (informe web-world §4). | Calcula t con el reloj de pared, se reevalúa y mueve el cabezal de su mapa. El transporte muestra "♪ suena en Timeline". |
| Arrastrar el cabezal en el mapa 3D | Recibe la búsqueda y redibuja. | Envía `seek` a la dueña. |
| Seleccionar un clip en el timeline | Selección plena. | Resalta la entidad, con contorno y rótulo, sin mover la cámara POV. En cámara Libre, **F** encuadra. |
| Seleccionar una entidad en 3D | Hace scroll vertical a su sub-pista y horizontal solo si el clip está fuera de vista. Muestra la selección en modo **standby**. | Selección plena. |

**Selección en dos niveles.** ISP ya distingue el panel que tiene el foco de los demás, con `body.fp-*` (`index.html:443-444`, `:600-602`, `:636-637`): la selección del panel enfocado se dibuja en `--ink` y la de los otros en `--ink-3`. Con dos pestañas eso se vuelve "la pestaña con foco" contra "la otra". Así queda claro sobre qué actúan el teclado y el próximo comando.

---

## 2. Timeline

### 2.1 Grupos y sub-pistas

Las pistas pasan a agruparse por **sujeto**, no por tipo de medio (informe web-timeline §2). Los grupos por defecto, de arriba abajo, van primero lo visual, después la interacción y abajo el sonido, como el audio al final de la columna única de ISP (R148, `COMPONENTS.md:660`):

| Grupo | Sub-pistas iniciales | Tono del clip (`CLIP_HUE`, `app.js:100`) |
|---|---|---|
| Narrativa (VO) | Alma · Ayudas · Omnipresente | audio `#398559` |
| Instrucción | Títulos · Texto · Fantasmas | text `#7F7936` |
| Alma | Estado (en mosaico) · Aura | ndi `#8468BE` |
| Objetos | una por entidad: Timbre, Sensor, Anillo, HUD, Candidatas… | video `#4E78B3` |
| Entorno / Look | Velo · Niebla · Cielo · Suelo | sequence `#9A6E42` |
| FX visuales | Apariciones · Halos | adjust `#B75686` |
| Interacción | Esperas · Mecánicas · Estados (manos y herramienta, quién manda la música) | nest `#777777` |
| Recorrido | Tramos · Paradas | `CLIP_FALLBACK #5E6570` |
| Sonido | por familia | audio `#398559` |
| Música / ambiente | AMB A · AMB B (para alternar en los cruces) | audio `#398559` |
| Háptica | Mano dominante · La otra | image `#B34FB3` |

**Por qué esos colores.** `CLIP_HUE` es una paleta **de luminosidad constante** ("ningún tipo grita más que otro", `app.js:96-99`). Se toma tal cual y solo se reasigna el significado de cada tono.

**Tinte de los grupos de sonido.** La cabecera y la fila de los grupos de sonido llevan el tinte `--audio-tint`, como el audio en ISP (`index.html:432`, `:573`). El color de la cabecera lo fija la función, nunca el usuario (R231, `COMPONENTS.md:727-734`).

**Fila de grupo (24 px, igual que `LANE_COLLAPSED_H`, `app.js:188`)**
- Fondo `--s1`, sobre el campo de pistas en `--s0`.
- Barra de color de 3 px (`.lanehdr .bar`, `index.html:445`).
- Chevron `.lcol` de 16 px.
- Nombre en 11 px/600, Title Case como `.sechead .t` (`index.html:317`).
- Contador `.countbadge` (`index.html:142`).
- A la derecha: `+`, **L**, **M** y **S** en botones `.ms` de 16×16 px (`index.html:448-450`).

Es la evolución de `.trackdivider.hdr` (`index.html:579-584`), sin la mayúscula espaciada.

**Fila de sub-pista**
- Alto por defecto de 34 px: 4 px de margen superior, 16 px de banda de título y 13 px de cuerpo.
- La sub-pista de VO usa 57 px (`LANE_DEF_H`), porque muestra la onda y el texto.
- El alto mínimo es 26 px (`LANE_MIN_H`).
- El alto se escala para **todas** las pistas a la vez con la barra vertical o con Alt+rueda, como en ISP (`renderVZoom` en `app.js:16248`, `wheelResizeLanes` en `:7764`, R156).
- La cabecera va sangrada 22 px, igual que `.autohdr` (`index.html:524`).
- Lleva una etiqueta de 18 px con el número de la sub-pista y el nombre en 11 px/500 `--ink-2`. El nombre se edita con doble clic (`inlineEdit`, `app.js:6765`).

**Las líneas que pidió Beltrán.** Cada sub-pista termina en `border-bottom:.5px solid var(--line-soft)`, que es exactamente `.lane` (`index.html:570`), y las filas pares llevan un 2 % de blanco (`:571`). Entre grupos no hace falta otra línea: el separador es la propia fila de grupo en `--s1`.

**Crear, borrar y ordenar sub-pistas**
- **Crear:**
  - con el `+` de la cabecera del grupo;
  - con **Ctrl+T** (el ⌘T de `addLane`, `app.js:5619`);
  - o soltando un clip en la **ranura de 16 px** que aparece bajo la última sub-pista del grupo mientras arrastras. La ranura tiene borde discontinuo como `.folderdrop` (`index.html:1131`) y dice "+ Nueva sub-pista". Recibe el nombre de la entidad del clip, por ejemplo "Timbre", o "VO 3" si no tiene entidad.
- **Borrar:** solo si está vacía. La × aparece al pasar el mouse, con el patrón `.folderhdr .fdel` (`index.html:1130`).
- **Reordenar:** arrastrando la cabecera, siempre dentro del grupo (`startLaneDrag`, `app.js:6820`, con el destino limitado al grupo).
- **Altura nueva:** una sub-pista nueva nace con la mediana del alto de las existentes (`laneAltaActual`, R352).

**Nunca hay superposición, y lo que movés se queda donde lo dejaste.**
1. Cada clip guarda su `subId`. El reparto automático de `computeLanes` (`timeline.js:591-607`) desaparece, y con él los carriles que saltaban de lugar.
2. Al arrastrar se usa el gesto de ISP: el original queda quieto y un fantasma muestra el destino (`showMoveGhosts`/`onTLMove`/`onTLUp`, `app.js:7282`, `:7318`, `:7433`). El arrastre arranca recién a los 6 px (`TL_UMBRAL`, `:7317`).
3. Si el destino choca con otro clip, el fantasma se dibuja con contorno `--danger` y la barra de estado dice "→ nueva sub-pista Timbre 2". Al soltar, el clip va a la primera sub-pista libre del grupo o, si no hay, a una nueva. Es la colisión vertical de FCP.
4. **Se invierte `cutOverlapsOnDrop`** (`app.js:7409`): en ISP el clip que se mueve recorta al que está quieto. Aquí **nunca corta**.
5. "Ordenar sub-pistas" es un **comando explícito** (en la paleta y en el menú del grupo) que compacta los carriles. Nunca se ejecuta solo.

**Plegar.** Un grupo plegado queda en **una fila de resumen de 24 px** donde los clips se ven solo como banda de título. Es lo mismo que ya hace ISP con `.lane.collapsed .clip .tt{height:100%}` (`index.html:454`). Alt+clic en el chevron pliega todos los grupos menos ese.

**Bloquear, silenciar y solo**
- **L (bloquear):** los clips no aceptan gestos. Si intentas uno, la barra de estado explica por qué, en ámbar, con el patrón `statinfo.why` (`index.html:1199`).
- **M (silenciar):** en grupos de sonido corta el audio de la vista previa. En grupos visuales **oculta la entidad en la vista 3D**. El clip silenciado se ve como `.clip.muted` (`index.html:610`).
- **S (solo):** aísla el grupo en 3D y en el audio.

### 2.2 Regla, actos, momentos y marcadores

El encabezado fijo mide 58 px en total:

1. **Actos (18 px).** Bloques en `--s2` y `--s1` alternados, con el nombre en 10 px/600 `--ink-2`.
   - Clic en un acto: zoom a ese acto.
   - **Ctrl+arrastrar el borde entre dos actos:** estira o comprime el acto. Es el warp de los locators actuales (`timeline.js:122-131`), que se muda aquí y deja libres los locators.
   - Los velos se marcan en el borde con un glifo de corte.
2. **Regla (24 px).** Es la regla de ISP (`drawRuler`, `app.js:5383`): timecode en la mitad de arriba, locators y notas en la de abajo (R223).
   - Un cabezal en forma de escudo (`#phTri`, `index.html:666`) y una línea de 2 px (`:664`).
   - Una línea discontinua `--ink-3` en **15:00** marca la meta del usuario típico.
3. **Momentos (16 px).** Cada momento tiene una pequeña chapa con su id ("1.8") al inicio y una línea `--line-soft` a toda la altura.
   - Clic en la chapa: selecciona todos los clips del momento, dibujados como selección derivada con contorno discontinuo (`.clip.gsel`, `index.html:1153`).

**Zoom.** Con Ctrl+rueda (`tlZoomAt`, `app.js:7671`) o con los extremos de la barra horizontal (`renderZoomBar` y los arrastres de la barra, `:7678-7690`), entre 0,1 y 2400 px/s (`app.js:204`).

### 2.3 Cómo se ve cada tipo de clip

Todos parten del `.clip` de ISP (`index.html:593-668`):
- banda de título de 16 px, 11 px/600, con el tono del tipo;
- cuerpo del mismo tono, más oscuro;
- asas de recorte de 8 px;
- fundidos como cuadraditos de 6×6 px en las esquinas superiores.

| Tipo | Forma |
|---|---|
| **VO** | Cuerpo: onda (`redrawAudioWaves`) al 40 % más las primeras palabras en 11 px `--ink-2`. **No tiene asa derecha**: dura lo que su audio, y al pasar el mouse por el borde aparece "Dura lo que su audio (regla)". |
| **Ayuda (`_h`)** | Igual que la VO, con borde punteado y al 70 %. |
| **FX sonoro instantáneo** | Rombo de 7 px (`.kfd`, `index.html:662`) con el nombre a la derecha en 10 px. La cola natural del WAV se dibuja punteada en `--ink-3`, sin efecto en el tiempo. |
| **AMB** | Barra larga con onda tenue. Las marcas de bucle van en la banda de título y los cruces llevan la X de `.xfade` (`index.html:658`). |
| **Háptica** | Un pulso es un trazo vertical cuya altura es la amplitud. Una háptica continua es un bloque que **necesita final**: sin final lleva un triángulo ámbar. |
| **Alma (estado)** | Bloques contiguos, **en mosaico** (aparece · al frente · al costado · sale): no admite huecos ni solapes. El borde entre dos estados se mueve con *roll*. |
| **Objeto** | Bloque con la envolvente de fundido (`.fadeenv`). |
| **Velo / look** | El cuerpo es un degradado del color de origen al de destino. |
| **Fantasma** | Banda de texto, más una muesca por cada ciclo de 4 a 6 s. |
| **Mecánica** | Bloque `nest` con doble borde. Doble clic lo abre como pestaña de secuencia (ver §3). |

**Esperas elásticas**

```
Interacción ─ Esperas
 ┌G_BREATH · sensor al estómago┐┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄▌25 s
 │/////////////////////////////│ (cola elástica: contorno cian discontinuo)
 └─────────────────────────────┘          ▲ ayuda +12 s
 ←───── esperado (6 s) ──────→←───────── hasta el tope ──────────→
```

- **Parte sólida:** banda de título en `nest #777`. El cuerpo tiene un rayado diagonal **claro** (`rgba(255,255,255,.06)`), para no confundirlo con el rayado oscuro de un clip deshabilitado (`.clip.off`, `index.html:606-608`).
- **Cola:** va desde el valor esperado hasta el cortafuegos, con contorno discontinuo de 1 px en `--auto-live`. Cian significa "vivo": esa parte la decide el usuario.
- **Cortafuegos:** un trazo de 2 px en `--danger` con la cifra en 10 px.
- **Ayuda anclada:** se ve como su clip punteado más un rombo sobre el borde de la espera.
- **El selector de persona** (en el transporte, §6) mueve el final de la parte sólida:
  - Rápido: cerca del mínimo, y la voz que estaba sonando se corta en 0,3 s;
  - Típico: el valor esperado;
  - Lento: pasa la ayuda;
  - Ausente: llega al cortafuegos.

  Todo lo anclado después se desplaza con ella, y el total de la barra de estado se recalcula.
- **Todo timecode posterior a una espera** se muestra con "≈", porque es una estimación (informe isp-nle C.6).

**Bucles (pacer, fantasma, melodía).** Una muesca por ciclo en la banda de título y "×5" junto al nombre. Si el bucle es elástico (por ejemplo, un fantasma que se repite hasta que el usuario hace el gesto), las muescas se apagan de a poco hacia el final de su espera.

**Ramas.** Ejemplo: SHARE / DON'T SHARE.
- Cada clip de rama lleva en la banda de título una chapa `.cnc` (`index.html:627`) que dice "SHARE" o "NO".
- La espera de la elección lleva un selector de 16 px **[Compartir | No | Ambas]**:
  - la rama activa se dibuja normal;
  - la inactiva se pliega a una franja de 6 px;
  - con "Ambas", la inactiva se ve como `.clip.off`.
- **El final del momento sigue a la rama elegida.** Esto corrige que hoy las dos ramas ocupen el mismo horario (`timeline.js:115`).

**Anclas.** Son curvas de 1 px en `--ink-2` que van del borde del padre al inicio del hijo, con un punto de 3 px en cada extremo y el desfase escrito a mitad de camino ("+0,3 s", 10 px tnum).
- Por defecto solo se ven las del clip seleccionado y las del clip bajo el mouse.
- **A** las muestra todas al 30 %.
- Los hijos de la selección se dibujan con contorno discontinuo (`.gsel`): así **la familia que se va a mover se ve antes de soltar**.
- Los **disparos del usuario** (una salida de una espera hacia un clip) son curvas **cian**: el tiempo autoral va en tinta y el tiempo vivo en cian.

**Traza real.** Cuando hay una traza importada de PIE o del APK, aparece una franja de 3 px en cian bajo cada clip con "lo que pasó de verdad". Usa el mismo lugar y la misma forma que `.cpxbar` (`index.html:630`).

---

## 3. Capa de nodos

**Principio:** el grafo es **otra vista del mismo dato**. Una arista es un ancla o un disparo. Si editas en un lado, cambia el otro (informe hibridos-sync §A, síntesis).

**Dónde se ve.** En el **cajón "Lógica"**. Es el `.curvedrawer` de ISP (`index.html:392-398`): una lista de 194 px a la izquierda y un lienzo a la derecha, bajo las pistas.
- Se abre con el botón **Lógica** del grupo de edición del transporte o con la tecla **G**. Ocupa el lugar de "Auto" en ISP.
- Mide 220 px en el modo todo en uno y 260 px en la pestaña de timeline, y su alto se ajusta con `hResize`.
- **Lista:** las interacciones y los disparadores del momento que contiene la selección. Son filas de 24 px con una muestra de color de 9 px (`.curveparams button`, `:394-396`).
- **Lienzo:** fondo `--s0` con una retícula de puntos en `--line-soft`. Muestra el grafo del momento, de izquierda a derecha en orden temporal.

**Anatomía de un nodo** (168 px de ancho, el mismo de una cabecera de pista). Es la tarjeta de efecto de ISP: `.fxcard/.fxhdr/.fxsec/.prow.fxrow` (`index.html:296-315`).
- **Cabecera** de 22 px en `--s2`: muestra de color de 6 px, nombre en 11/600 y desfase a la derecha.
- **Cuerpo:** filas `.prow` de 24 px.
- **Puertos:** círculos de 7 px; las entradas a la izquierda y las salidas a la derecha, con su nombre.
- **El nodo de espera** tiene tres salidas, cada una con su color: **Hecho** (cian), **Tarde → ayuda** (`--ink-2`) y **Tope** (`--danger`). Es el patrón de Flow Graph.

**Cómo se edita una condición sin programar.** Se arma una frase con desplegables de 18 px (`.selsel`, `index.html:352`), siempre de un vocabulario cerrado:

> Cuando **[el sensor ▾] [está en la zona ▾] [estómago ▾]** durante **[3 s]**

Las opciones vienen del contrato de cada mecánica. No se escribe código.

**Línea de lectura.** Arriba del cajón hay una frase generada en cian. Es el patrón de `.modpan .mpformula`, que "contesta por qué está así, ahora mismo" (`index.html:489-490`). Ejemplo:

> En 4.R5, cuando el sensor llega al estómago (o a los 25 s), suena VO_12 y empieza la cuenta.

Tu socio la lee como una hoja de cues.

**Crear "esto dispara aquello".** Hay tres formas, y las tres escriben el mismo ancla:
1. **En el timeline:** al pasar el mouse por un clip aparece un puerto de 6 px en el extremo derecho de su banda de título. Lo arrastras hasta otro clip. El imán deja el desfase en 0 si sueltas a menos de 9 px (`applySnap`, `app.js:7072`). Si el origen es una espera, sale un menú de tres ítems de 26 px: Hecho / Tarde / Tope.
2. **En el cajón:** arrastras de un puerto a otro.
3. **En el inspector:** el campo "Entra" ofrece cualquier clip de la obra con búsqueda, no solo los del mismo momento. Hoy el prototipo limita esa lista al momento (`timeline.js:772-780`).

**Mecánicas.** Con doble clic, un bloque de mecánica se abre como **pestaña de secuencia** en el transporte. Es el *nest* de ISP: `renderSeqBar` (`app.js:14195`) y la apertura con doble clic.
- Adentro hay pistas propias: por ejemplo, las VO de Attracting a 20 y 75 s, o la tinta por encima de 0,3.
- El inspector del bloque solo expone sus perillas. El grafo interno de Unreal nunca se ve.

---

## 4. Inspector

**Estructura** (es la de ISP, `index.html:286-353`; ver `05b-inspector-clip.png`):
- **Pestañas** tipo *well*: **Inspector | Notas**.
- **Franja de color** de 4 px con el tono del tipo.
- **Cabecera** (`.selhead`, `index.html:288-291`):
  - miniatura de 44×29 px: el ícono de la entidad, o la onda si es una VO;
  - nombre en 13 px/600;
  - metadatos en 10 px en mayúsculas ("OBJETO · 1,5 S · 1.8");
  - a la derecha, el botón **"Unreal ▸"**, en el lugar del "Source" de ISP.
- **Secciones** plegables `.sechead` de 24 px. El estado de plegado persiste (`wireSecHeads`/`applySecCollapse`, `app.js:15993-15997`).

**Secciones por tipo.** "Tiempo" siempre va primera y abierta; "Avanzado" siempre va plegada.

| Tipo | Secciones |
|---|---|
| Todos | **Tiempo:** Entra (chip de ancla "al terminar VO_01b" + desfase) · Dura · Sale · Fundido de entrada · Fundido de salida · Sub-pista |
| VO | **Voz:** texto (área en `--s0`) · audio (nombre, duración, ▶, Reemplazar) · "Dura lo que su audio" (fijo, con el motivo) · Desde **[Alma 3D \| Omnipresente]** · Volumen · Aire antes (1,5 s) |
| Espera | **Espera:** Qué espera (la frase de §3) · Esperado · Ayuda a los · Cortafuegos · Al tope **[igual que el final real]** (fijo) · Si actúa antes: cortar la voz (interruptor `.iosw`, `index.html:1121`). Debajo, una fila de solo lectura con las cuatro duraciones: Rápido 1,2 · Típico 6 · Lento 14 · Ausente 25. |
| Objeto / Alma | **Aparición:** estilo (luz primero) · sonido · háptica. **Lugar:** Parada · Al frente · Lado · Altura · Giro · Escala, con faders que reusan los colores por parámetro: `--p-az`, `--p-el`, `--p-op`, `--p-rot`, `--p-size` (`index.html:79-81`). |
| Mecánica | **Perillas** expuestas, en lenguaje de sala ("cuánto tarda en aparecer", no `FadeInTime`). |
| Avanzado | uid estable · key visible · mapeo a Unreal (`BP_Obra_SC.ChargeTimes[2]`, instancia o CDO, actor y tag) · origen · el JSON en crudo. |

**De dónde viene cada valor.** Se ve en el recuadro del valor:
- **Sin marca:** igual a Unreal.
- **Número en ámbar:** editado aquí y distinto de Unreal. Es el ámbar de "anulado" de ISP (`.abt.ovr`, `index.html:534`).
- **Candado de 9 px:** valor final aprobado de un nivel de test. Editarlo pide un motivo (`appPrompt`, `app.js:5677`), que queda registrado como nota.

**Lenguaje de cine.** Entra, sale, dura, fundido, desfase, anclado a, cola, tope. Nunca "uid", "apply" ni "fw" fuera de Avanzado.

**Botón "Unreal ▸".** Abre un menú `openMenu` (`app.js:16864`) con tres opciones:
- Copiar la ruta del actor o del TargetPoint (`TP_sc2_alma_side`).
- **Probar desde aquí**: muestra el código DebugStart, por ejemplo 23, y lo pone en la cola.
- Abrir el tracker del BP.

**Sin selección,** el inspector muestra `.insEmpty` (`index.html:353`) con un resumen del momento.

---

## 5. Vista 3D

**Barra del visor (28 px)**

| Grupo | Contenido |
|---|---|
| Cámara | [POV · Libre · Planta]. Es el *well* 2D/3D de ISP. |
| Superposiciones | Solo íconos (`.vseg.iconly`, `index.html:239`): **Anclas · Activo ahora · Rayos X · Campo visual · Sonidos** |
| Modo | [Editar · Jugar] |
| Derecha | Zoom en % y **Salida ▾**, con "Abrir en otra pestaña" y "Pantalla completa". Es el modo de rendimiento de ISP (`body.perfmode`, `index.html:268`). |

**Cámaras**
- **POV:** la cabeza del usuario sentado en la parada actual, con HUD.
- **Libre:** cámara orbital.
- **Planta:** cenital ortográfica, con el cono de mirada y anillos a 0,5, 1, 2 y 3 m.
- La cabeza se separa de la cámara de render, como pide el informe web-world §3.5.

**Campo visual.** En POV se dibujan dos anillos discontinuos, a ±30° y ±60°, con sus rótulos. Es la "zona segura" de ISP (R384, `COMPONENTS.md:69`) aplicada a la mirada.

**Anclas y TargetPoints**
- Rombos de 7 px en `--ink-2` con un rótulo de 10 px (`sc2_alma_side`).
- Un fantasma de alambre al 30 % muestra el objeto en esa posición.
- **El gizmo edita el ancla, no el objeto** (informe web-world §3.3). Tiene tres flechas en el marco de la parada (frente, lado, arriba) y un anillo para el giro.
- Mientras arrastras, un chip `.vslab` (`index.html:247-249`) muestra "2,20 m al frente · 0,30 m izq · +0,05 m". El imán va en pasos de 1 cm y 5°.

**Selección cruzada.** Un clic en una entidad selecciona su clip activo en el cabezal (o la entidad, si ninguno está activo) y lo sincroniza con el timeline como se describe en §1.3. Mover un ancla genera un **parche** de solo lectura hacia Unreal (§7); nunca se escribe directo en el `.umap`.

**Activo ahora.** Una tarjeta arriba a la izquierda en `--s1` al 80 %, como el patrón de la etiqueta "Preparando medios…" de ISP (R220).
- Lista hasta 8 elementos activos: punto de color de 7 px (`.mdot`), nombre y tiempo restante ("quedan 3,2 s").
- Pasar el mouse resalta en ambos sentidos entre la lista y la escena.
- **Avisos espaciales:** si dos apariciones caen en el mismo cono de 30° al mismo tiempo, aparece un triángulo ámbar en la escena y en los dos clips (informe guion §5).

**Rayos X.** Hace visibles a través del resto los materiales con `depthTest:false` (anillo, HUD, títulos y velo); fuera de este modo no se dibujan así.

**Simular al usuario.** La persona se elige en el transporte y vale para todo.

En **Jugar** (el equivalente de PIE):
- El mouse es la mano y las esperas se resuelven en vivo.
- Mientras hay una espera retenida, abajo al centro aparece una píldora: "Esperando: sensor al estómago · 8,2 s / tope 25 s **[Cumplir ⏎]**".
- **Esc** vuelve a Editar.

En **Editar**, el tiempo es determinista. Es el modo natural de tu socio.

---

## 6. Interacciones y atajos

Se mantienen las teclas de ISP para que tu socio y tú usen la misma gramática.

| Tecla | Acción | Origen |
|---|---|---|
| Espacio · Home · End | reproducir o pausar · ir al inicio · ir al final | ISP |
| **J / K / L** | retroceder, parar, avanzar (1, 2, 4, 8×); K con J o L va a ¼× | `app.js:10772-10795` |
| **I / O / X** | rango de trabajo: entrada, salida, borrar | `app.js:16590` |
| **M** | nota o locator en el cabezal, que entra directo a renombrar | `app.js:16584`; `addMarker` en `:6848` |
| `,` / `.` | locator anterior o siguiente | ISP |
| ← / → | mueven **solo el cabezal**, 0,1 s (con Shift, 1 s) | se corrige la ambigüedad de `timeline.js:1153-1156` |
| Alt+← / → | mueven la selección 0,1 s (con Shift, 1 s), junto con sus anclados | `nudgeSel`, `app.js:16483`, en décimas en lugar de cuadros |
| ↑ / ↓ | momento anterior o siguiente | adaptado de "corte en corte" |
| V H T B Z | herramientas; la ayuda de cada una sale en la barra de estado | `TOOL_HINTS`, `app.js:16297` |
| Ctrl+T | nueva sub-pista | `addLane` |
| Ctrl+D · Ctrl+C/V · Ctrl+R | duplicar · copiar y pegar · renombrar | ISP |
| Supr / **Shift+Supr** | borrar dejando el hueco / borrar y cerrar el hueco **solo dentro de la sub-pista y del momento** | `rippleDelete` en `app.js:16834`, con alcance acotado |
| Ctrl+Z / Ctrl+Shift+Z | deshacer y rehacer: incluye look, sub-pistas, ramas y notas | `pushUndo`/`snapshot`, `app.js:15654-15667`, ampliados |
| Ctrl+K | paleta de comandos | `openPalette`/`commandList`, `app.js:17185-17216` |
| A · G · F · 1-4 · Tab | todas las anclas · cajón Lógica · encuadrar · persona · alternar el foco entre timeline y 3D | nuevas |

**Gestos**
- **Arrastrar** mueve el clip con su familia; los anclados se ven con contorno discontinuo y con su propio fantasma.
- **Ctrl+arrastrar** mueve solo ese clip. Los hijos se quedan donde están y su desfase se recalcula.
- **Alt+arrastrar** copia (`app.js:7433`).
- **El imán** siempre está activo, hacia bordes, cabezal, locators, notas e inicios de momento (`snapTargets`, `app.js:7048`). Alt lo suspende en los recortes.
- **Multiselección:** Shift+clic, marquesina (`startMarquee`, `:7706`) y clic en la chapa de un momento.
- **Ripple:** solo con la herramienta T. Va en el ámbar de Avid y se limita al momento.
- **Roll:** solo entre bloques contiguos de la misma sub-pista, como en un cruce de ambientes o en los estados de Alma.

**Qué no se adopta**
- **El timeline magnético global de FCP:** desordena todo lo que está sincronizado.
- **El "solape = corte" de ISP.**
- **Slip y slide fuera del audio,** y la cuchilla sobre esperas u objetos: no tienen material de origen.
- **Numerar pistas V1…Vn como identidad:** las pistas tienen nombre; los números son solo de las sub-pistas.
- **Cuadros, el conmutador TC/Frames y el timecode absoluto como verdad.**
- **El monitor de fuente con edición de tres puntos.**

---

## 7. Sincronización, versiones y notas

**Píldora de sincronización** en la barra superior: 22 px, con el estilo `.ddbtn` (`index.html:168`). Tiene cinco estados:

| Estado | Cómo se ve |
|---|---|
| Sin puente | ○ en `--ink-dim` |
| **Al día** | ● en `--ink-2`, con el texto "al día" |
| **N diferencias** | ● en ámbar |
| **Conflicto** | ● en `--danger` |
| **PIE en vivo** | ● cian con pulso (`recpulse`, como `#outputBtn.on`, `index.html:244`) |

**Panel de sincronización.** Al hacer clic se abre un panel flotante de 360 px, el `.modpan` de ISP (`index.html:465-490`):
- **Una fila por diferencia:** elemento · campo · valor en Unreal · valor en la partitura · **[Usar Unreal] [Mantener]**.
- **Pie del panel:**
  - "Unreal rev 41 · partitura rev 44 · APK rev 39";
  - **"Pedir turno y aplicar"**, que pasa por la cola del editor compartido: nunca escribe en directo;
  - el interruptor "Traza de PIE".

**En cada clip.** Un punto de 5 px en la esquina derecha de la banda de título: ámbar si está editado y todavía no está en Unreal, `--danger` si hay conflicto. El conteo total aparece en la barra de estado.

**Versiones**
- **Guardar versión** (Ctrl+Shift+S) le pone nombre y fecha, por ejemplo "Corte del socio 03-oct".
- **Comparar** superpone la versión anterior: los clips cambiados llevan contorno ámbar y su posición vieja se ve como fantasma discontinuo.
- **Presencia:** un chip con iniciales en la barra superior ("S · Acto 2"). El acto que otra persona está editando lleva sus iniciales en la banda de actos, como bloqueo suave.

**Notas para tu socio**
- **M** crea la nota en el cabezal. Se ve como banderín en la mitad baja de la regla, con la inicial del autor ("B" o "S").
- **Notas de clip:** un glifo de globo en la banda de título del clip.
- **Pestaña Notas:** lista con autor, hora, salto al punto y "resuelta" (interruptor `.iosw`).
- La barra de estado muestra cuántas notas siguen abiertas.

---

## 8. Estética

**Paleta.** Se copia `:root` de ISP **literalmente**, incluidos los comentarios que justifican cada valor (`index.html:28-83`):
- tres superficies: `--s0 #111`, `--s1 #1B1B1B`, `--s2 #262626`;
- cuatro tintas;
- tres alfas de línea;
- `--state-on` y `--state-hover`;
- la paleta cerrada de espaciado, de `--sp-2` a `--sp-32`.

La regla de *affordance* se mantiene: un botón va en `--s2` y un campo editable en `--s0`.

**Presupuesto de acentos: dos.** El comentario del `:root` se reescribe con el significado nuevo:
- **Cian `--auto-live` = vivo.** Lo decide el usuario o viene en vivo de Unreal: colas elásticas, disparos, la traza, PIE, la línea de lectura.
- **Ámbar `--auto-ovr` = anulado.** Un valor editado aquí que pisa al de Unreal, una divergencia, un aviso.

Además:
- `--danger` se usa para cortafuegos y conflictos.
- `--toggle-on` (verde) se usa solo para interruptores.
- Los tipos de clip usan `CLIP_HUE` de luminosidad constante (`app.js:100`).

**Tipografía**
- Geist con números tabulares (`.tnum`).
- Base de 11 px (`index.html:86-88`).
- 12,5 px solo en el timecode y 13 px solo en el nombre del inspector.
- Mayúsculas únicamente en metadatos de 10 px. Todo lo demás en Title Case.

**Densidad.** Alturas de 28, 22 y 16 px; filas de 24 px; menús con ítems de 26 px (`index.html:1115`); bordes de 0,5 px.

**Movimiento**
- Solo transiciones de 0,12 s en fondo y color, y la entrada de los modales en 0,14 s (`index.html:116`).
- Al arrastrar se usa el fantasma; nada se anima de forma decorativa.
- Se respeta `rm-on` (`index.html:1124`).

**Íconos.** El catálogo `ICO()` (`index.html:1458`): 13 px con trazo de 1,8. Se agregan con ese mismo trazo: espera (reloj de arena), rama, ancla, háptica, persona y globo.

**Cómo se logra "elegante" sin recargar**
- **Restricción:** nada está saturado salvo el tono de los clips y los dos acentos.
- **Lo secundario aparece solo al pasar el mouse:** anclas, puertos, × de borrar.
- **Explicación instantánea en la barra de estado,** con la Info View (`index.html:1191-1199`). Por ejemplo, al pasar sobre una espera: "Espera G_BREATH — dura lo que tarde el usuario · ayuda a los 12 s · tope 25 s".

---

## 9. MVP priorizado y mapa de reutilización

**P0: el núcleo para que tu socio empiece a montar**

1. **Chrome de ISP:** `:root`, botones, *wells*, paneles, divisores, rieles, menús, diálogos y barra de estado. Se usa con el layout todo en uno.
2. **Timeline con grupos y sub-pistas persistentes:**
   - plegar, L, M y S;
   - mover con familia y sin solapes;
   - recortes, imán y zoom en los dos ejes;
   - bandas de actos y momentos, y regla con locators y notas.
3. **Clips por tipo,** con la onda en la VO.
4. **Esperas elásticas, selector de persona** y total contra la meta de 15:00.
5. **Transporte con J/K/L, I/O y M,** y timecode relativo.
6. **Inspector** con Tiempo, Voz, Espera y Avanzado, más el origen de cada valor y los valores finales con candado.
7. **Píldora de sincronización en solo lectura** (instantánea de Unreal → diferencias) y versiones con nombre.

**P1**

8. Vista 3D: cámaras, anclas con gizmo en el marco de la parada, Activo ahora y selección cruzada.
9. Modo de dos pestañas: canal entre pestañas con pestaña dueña del reloj y del audio, mapa de la obra y selección en standby.
10. Notas con autor y presencia.
11. Ramas con el selector de rama.

**P2**

12. Cajón Lógica con nodos y frases.
13. Mecánicas abiertas como pestañas de secuencia.
14. Traza de PIE superpuesta.
15. Look animable como sub-pistas de automatización. Es la automatización de ISP: `.autolane`, `evalP` y color por parámetro (`index.html:522-533`).
16. Vista de lista de cues.
17. Recorrido guiado para tu socio (`tourSteps`, `COMPONENTS.md:361`).

### Qué se toma, qué se adapta y qué es nuevo

| Componente | Origen en ISP | Acción |
|---|---|---|
| Tokens y base | `index.html:28-133` | **Tal cual.** Solo cambia el comentario de los acentos. |
| *Wells*, segmentados y botones | `index.html:125-131`, `143`, `150-158`, `168`, `225-228`, `350`, `369-371`, `1121-1123`, `1201` | Tal cual |
| Paneles, divisores y riel | `index.html:138-147`, `1139-1144`; `gutter`/`setPaneCollapsed`/`hResize`/`saveWorkspace` en `app.js:16308`, `15964`, `16323`, `16470` | Tal cual |
| Biblioteca | `.mitem`/`.mthumb`/`.mmeta`, `index.html:182-216`; `renderMedia` en `app.js:4782` | **Se adapta:** árbol de escenas y entidades |
| Transporte | `index.html:356-365`, `405-409`, `670-717`; `positionPlayhead` `6862`, `play` `10760`, avance J/K/L `10772`, `renderSeqBar` `14195` | **Se adapta:** persona, TC relativo, grupo de edición Anclas · Lógica · Fit |
| Timeline (estructura, regla, zoom) | `index.html:412-454`, `543-577`; `renderTimeline` `5452`, `positionClips` `7383`, `drawRuler` `5383`, `tlZoomAt` `7671`, `renderZoomBar` `7678`, `renderVZoom` `16248`, `wheelResizeLanes` `7764` | **Se adapta:** grupos, sub-pistas y bandas de actos y momentos |
| Clip | `index.html:593-668`; `clipTint`/`CLIP_HUE` en `app.js:100-111` | **Se adapta:** formas por tipo y espera elástica |
| Gestos | `onTLMove`/`onTLUp`/`showMoveGhosts` `7282-7433`, `trimItem` `7364`, `startFadeDrag` `7498`, `applySnap` `7072`, `startMarquee` `7706`, `startLaneDrag` `6820` | **Se adapta:** familia de anclados; `cutOverlapsOnDrop` (`7409`) **se invierte** |
| Herramientas | `#toolRail` en `index.html:1413`; `setTool` `16305`, `TOOL_HINTS` `16297` | Tal cual; el trim contextual solo aplica al audio |
| Locators | `addMarker`/`jumpMarker`/`renameLocatorInline`, `app.js:6848-7745` | **Se adapta:** notas con autor; el warp pasa a la banda de actos |
| Inspector | `index.html:286-353`; `buildRows` `8982`, `startValDrag` `9086`, `editNumberBox` `9030`, `refreshInspector` `9058`, `wireSecHeads` `15997` | **Se adapta:** etiqueta de 84 px, secciones por tipo y origen del valor |
| Selección en dos niveles | `index.html:443-444`, `600-602`, `636-637`, `1153` | Tal cual; se aplica también entre pestañas |
| Cajón Lógica | `.curvedrawer`, `index.html:392-398` | **Se adapta** |
| Nodo | `.fxcard`, `index.html:296-315` | **Se adapta** |
| Panel de sincronización y línea de lectura | `.modpan`/`.mpformula`, `index.html:465-490` | **Se adapta** |
| Pestaña 3D | `openViewerWindow`/`viewerPump`, `app.js:2486`, `2583` | **Se adapta:** canal entre pestañas en lugar de `window.open` |
| Monitor flotante | `#srcMon`, `index.html:751-785` | Se adapta |
| Menús, paleta y diálogos | `openMenu` `16864`, `openPalette` `17216`, `_dialogBase`/`appPrompt`/`appConfirm` `5677-5750`, `inlineEdit` `6765` | Tal cual; reemplazan los `prompt`/`confirm`/`alert` del prototipo (`timeline.js:674`, `810`, `962`, `1111`) |
| Barra de estado y Info View | `index.html:792`, `1189-1199`; `flashStatus` `15781` | Tal cual |
| Deshacer | `snapshot`/`pushUndo`/`restore`, `app.js:15654-15667` | **Se adapta:** cubre también look, sub-pistas y notas |
| **Nuevo** | — | Esperas elásticas y cortafuegos · persona · bandas de actos y momentos · ranura de sub-pista nueva · curvas de ancla y de disparo · selector de rama · cámaras POV, Libre y Planta, con gizmo en el marco de la parada · Activo ahora · píldora de sincronización · valores finales con candado · meta de 15:00 |