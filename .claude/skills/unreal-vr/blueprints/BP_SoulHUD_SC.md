# BP_SoulHUD_SC — el HUD de la versión limpia (Core/HUD/)

## Purpose
El HUD que acompaña toda la experiencia, pegado a la cabeza. Rehecho limpio en `MapsV2` (2026-08-24).
Tres elementos: **barra de carga**, **gráfico EEG** y **punto pulsante de ritmo cardíaco**.

## Assets
| Asset | Qué es |
|---|---|
| `Core/HUD/BP_SoulHUD_SC` | el actor |
| `Core/HUD/WBP_SoulHUD_SC` | **el widget único** con los tres elementos |
| `Core/HUD/M_HudWidget_SC` | 🔴 el material "por encima de todo" para widgets |

## 🔁 Historia de la forma (importa para no volver atrás)
1. **Primera versión: tres `WidgetComponent` separados**, uno por elemento, para poder moverlos con el
   gizmo en 3D. Funcionó y se verificó en PIE.
2. **Pedido de Beltrán: "hacelo como un solo widget y no 3 separados, así les puedo poner el geometry
   cilíndrico"** → se fusionaron en `WBP_SoulHUD_SC` + **un** `WidgetComponent` (`Hud`). El `GeometryMode`
   vive en el componente, así que con tres componentes había tres cilindros distintos: sólo tiene sentido
   con uno.

**Cómo se mueven los elementos ahora:** en el Designer de `WBP_SoulHUD_SC`, arrastrando en un lienzo de
**1000×400 px** (= 40 × 16 cm) que es a propósito mucho más grande que el contenido, para que nada quede
cerca del borde ni se recorte (la queja del HUD viejo era exactamente eso, gotcha #15a). **1 px = 1 mm.**

## Componentes
| Componente | Relativa (cm) | Escala | Qué es |
|---|---|---|---|
| `HeadRef` | (0,0,0) | 1.5 | **La referencia de la cabeza**: `GenericHMD` del VREditor, `bHiddenInGame`. El doble del HMD (mismo truco que [[BP_FaceAnchor_SC]]) para autorar mirando. En la instancia del nivel está oculto porque el `BP_FaceAnchor_SC` ya dibuja uno ahí. |
| `Hud` | (0, 0, 0) · yaw 180 | 0.04 | el widget entero |

## 🎯 La pose se autora MOVIENDO EL ACTOR EN EL WORLD
🔴 **El offset del HUD respecto de la cabeza es la pose del actor RELATIVA a `BP_FaceAnchor_SC`** — el doble
del HMD que ya está colocado en el nivel. Se arrastra y se rota el actor en el viewport, mirando el anchor,
y eso es exactamente lo que se ve en el visor. Pedido de Beltrán: *"la gracia era yo poder ajustar desde ahí"*.

Cómo funciona: **`ReadHeadOffset()` corre en el CONSTRUCTION SCRIPT** — busca el `BP_FaceAnchor_SC` por
clase y guarda `HeadOffsetLoc` / `HeadOffsetRot` = la transform del actor **invertida contra la del anchor**
(`InverseTransformLocation` / `InverseTransformRotation`). Después, en runtime, `AttachHead()` se attachea a
la `CameraComponent` con `SnapToTarget` y **aplica ese offset ya horneado** con `SetActorRelativeLocation` /
`SetActorRelativeRotation`.

🔴🔴 **Por qué el Construction Script y no BeginPlay: en Play el `BP_FaceAnchor_SC` YA NO ESTÁ en su pose
de editor** — cuelga del pawn y se mueve con él. Medir contra él en runtime daba basura: el offset salía
`Z = 104,458`, que es la **Z del mundo** del actor (o sea, el anchor aportaba 0). Lo delató un `PrintString`
del offset. Horneado en el Construction Script el mismo cálculo da `(34,9 · 0 · −15,5)`, que es exactamente
la diferencia entre las dos poses de editor, y en PIE llega ese mismo número. **Verificado por log.**

🚩 **Por qué antes NO andaba:** `AttachHead` hacía sólo el `AttachActorToComponent` con `SnapToTarget`,
que **pisa la transform del actor con la de la cámara**. O sea que lo que se autoraba en el world se
descartaba en el primer frame, y la única pose real era la del componente. Por eso el componente `Hud`
ahora está en **(0,0,0)**: si tuviera offset propio se sumaría al del world y habría dos controles
peleando por lo mismo. **Un solo control: el actor.**
⚠ Si no hay `BP_FaceAnchor_SC` en el nivel, el offset queda en cero y el HUD aparece pegado al ojo.

## 🌀 `Geometry Mode = Cylinder` — probado, y NO sirve a esta escala
Medido el 2026-08-24, aislando una variable por vez sobre la misma instancia y el mismo widget:

| Config | ¿Dibuja? |
|---|---|
| `Plane`, escala 0.04 | ✅ sí |
| `Cylinder`, escala 0.04, material propio | ❌ nada |
| `Cylinder`, escala 0.04, **sin** material propio (el del motor) | ❌ nada |
| `Cylinder`, **escala 1** | ✅ sí (lejos y chiquito) |

👉 **El cilindro funciona; lo que no funciona es el cilindro con la escala 0.04 del componente.** El radio
del arco lo deriva el motor de `DrawSize` y `CylinderArcAngle` (R = ancho / arco en radianes), y a escala
chica la malla degenera y no se dibuja. Se nota también en los bounds: en modo `Cylinder` el actor reporta
un volumen de ~2,5 m en vez de los 40 cm reales.
⚠ El corolario incómodo: con escala 1 (1 px = 1 cm) un radio de 30 cm exige un `DrawSize` de ~40 px de
ancho — resolución inservible. **Cilindro y HUD a 30 cm del ojo son incompatibles por ahora.**
🔧 **Quedó en `Plane`.** Cambiarlo es un desplegable en el componente `Hud`, por si querés volver a probarlo
(en el visor el renderer no es el mismo que el preview del editor).

## 🪟 El material que queda por encima de todo — `M_HudWidget_SC`
Lo mismo que se hizo con la ameba (`M_ProtoSoul_HUD`, gotcha §197): **Disable Depth Test**, que en el
renderer móvil pone el test en `Always` ⇒ las manos y la geometría nunca lo tapan.
- 🔴 Un `WidgetComponent` no acepta el truco por instancia de material: lleva material propio en
  **`overrideMaterials[0]`**.
- 🔴 **Los nombres de los parámetros NO son libres**: `UWidgetComponent::UpdateMaterialInstanceParameters`
  escribe **`SlateUI`** (Texture2D = el render target), **`TintColorAndOpacity`** (Vector) y
  **`OpacityFromTexture`** (Scalar). El material replica el passthrough del motor:
  `Emissive = SlateUI.RGB * Tint.RGB`, `Opacity = lerp(1, SlateUI.A, OpacityFromTexture) * Tint.A`.
  Flags: `BLEND_Translucent` · `MSM_Unlit` · `twoSided` · **`bDisableDepthTest`**.

## 〰️ El widget — `WBP_SoulHUD_SC`
Tres hijos de un `CanvasPanel`. 🔴 **Los tres están anclados ARRIBA-IZQUIERDA (anchors 0,0 · alignment 0,0)**,
no al centro — ver la nota de abajo, es lo que hace que el trazo del EEG caiga donde debe.

| Widget | Posición (px desde arriba-izquierda) | Tamaño | Qué es |
|---|---|---|---|
| `GraphArea` (Image, contorno alpha 0,35) | (800, 520) | 320×80 | 🔴 **el marco del gráfico**: define dónde va la onda y es lo que se arrastra |
| `Bar` (ProgressBar, BottomToTop) | (1076, 387) | 48×256 | la carga |
| `Dot` (Image círculo) | (857, 532) | 56×56 | el latido |

⚠ Con anclaje arriba-izquierda, si cambiás el `DrawSize` del componente **los elementos NO se recentran**:
mantienen su posición absoluta en píxeles. Es a propósito (predecible), pero hay que saberlo.

🔴 **El trazo del EEG sigue a `GraphArea`.** `SyncBox()` lee el SLOT del marco
(`SlotAsCanvasSlot` → `GetPosition` / `GetSize`) y recalcula `RightX` / `StepX` / `BaseY` / `SpanY` en cada
`Rebuild`. **Consecuencia: arrastrás o redimensionás `GraphArea` en el Designer y la onda se acomoda sola**
— es lo que conserva la edición libre después de fusionar todo en un widget. Guard: si el ancho es < 4 px
no toca nada y quedan los defaults.

🚩 **Dos versiones anteriores de `SyncBox` estaban MAL — no volver a ellas:**
1. **Por geometría cacheada** (`GetCachedGeometry` + `LocalToAbsolute`/`AbsoluteToLocal`): daba
   esquina-superior-izquierda (el `_tl` salía (0,0)) y la onda se dibujaba en el rincón del lienzo, tanto en
   el Designer como en Play. La geometría no está resuelta cuando se llama.
2. **Por slot pero con el centro del lienzo** (`CanvasSize/2 + pos`): correcto sólo mientras `DrawSize`
   valiera exactamente lo que decía la variable. Beltrán cambió el `DrawSize` a 1920×1080 y la onda se fue
   de nuevo al rincón.
✅ **La versión buena no necesita saber el tamaño del lienzo**: con anclaje arriba-izquierda, `GetPosition`
**ya es** la coordenada del marco dentro del canvas. `RightX = pos.x + size.x − Pad`, `BaseY = pos.y + size.y − Pad`.
Por eso los tres elementos están anclados a (0,0).
🔴 **`GraphArea` tiene un contorno finito visible (outline alpha 0,35, sin relleno) A PROPÓSITO**: con alpha 0
no había nada que agarrar en el Designer y el gráfico no se podía mover — se lo comentó Beltrán el mismo día.
**Para que desaparezca del todo: `GraphArea` → Appearance → Brush → Outline Settings → Color → alpha a 0.**
Un solo número, y sigue siendo seleccionable desde el panel Hierarchy.
⚠ Se intentó la versión "elegante" (marco visible sólo en design time, apagado por `PreConstruct` según
`IsDesignTime`) y **no funciona**: `SetRenderOpacity` desde `PreConstruct` no se sostiene — el marco quedó
visible en PIE con las dos órdenes del `select`. Ver gotcha §201. No reintentarlo.

- Palancas en los defaults del widget: `MaxSamples` 48 · `Pad` 14 · `LineColor` · `LineWidth` 2.5 ·
  `bSeedDemo`. (`RightX`/`StepX`/`BaseY`/`SpanY` los pisa `SyncBox`, no hace falta tocarlos.)
- API: `PushCalm(Sample)` · `SetCharge(P)` · `SetPulse(S)` · `SeedDemo()`.
- 🔴 `add_event("OnPaint")` FALLA (*"inherited function-shape override"*) → **`add_function_graph("OnPaint")`**
  lo crea ya con su param `Context` y su `(return)`.

## 🌱 El nacimiento animado (2026-08-24)
El HUD **arranca invisible y nace animado durante la calibración del Hall**, junto con el **VO 5** (pedido de Beltrán).

**Todo cuelga de UNA variable del widget: `Birth01` (0→1).** `SetBirth(V)` la escribe y reparte:

| Elemento | Qué hace de 0 a 1 |
|---|---|
| **`Root`** (el CanvasPanel raíz) | render opacity 0 → 1 — **funde el ÁRBOL ENTERO de una vez**: fondo, barra, marco y puntos |
| `Dot` y `Dot_1` | ademas, render scale 0 → 1 |
| **El trazo del EEG** | **se extiende desde el CENTRO hacia los lados**, y su color se multiplica por `Birth01` (si no, a ancho 0 quedaría una raya vertical visible en el medio) |

🔴 **Se funde el `Root`, NO elemento por elemento.** La primera versión listaba `Bg`, `Bar` y `GraphArea` uno por uno y **el marco del `GraphArea` se veía igual al arrancar** (lo reportó Beltrán). En vez de perseguir por qué, se movió el fundido al padre: la opacidad de render **se hereda multiplicativamente** hacia abajo, así que con `Root` en 0 no hay ningún camino por el que un hijo dibuje. **Y no hay que acordarse de agregar cada elemento nuevo a la lista** — cualquier cosa que Beltrán sume al lienzo nace apagada sola.
⚠ La única excepción es el trazo del EEG, que **no es hijo de `Root`**: lo dibuja el `OnPaint` del UserWidget. Por eso su alfa se multiplica aparte.

🔴🔴 **Y hay una segunda excepción, que costó dos intentos: el CONTORNO de un brush `RoundedBox` NO respeta la opacidad de render.** El marco del `GraphArea` seguía viéndose — una línea fina de esquinas redondeadas — con `Root` al 0 y también con la opacidad puesta sobre el propio `GraphArea`. El contorno se dibuja con su `OutlineSettings.Color`, por un camino distinto al del tinte del brush. Ver gotcha §207.

### 🖼 El marco NO se funde: CRECE (decisión de Beltrán, le gusta y se queda en la obra)
Como el contorno no se puede fundir, **se anima el ancho del slot**: el marco nace con ancho 0 en el centro y **se abre hacia los lados**, junto con la onda. Es además más fiel a lo que Beltrán pidió para el gráfico (*"apareciendo en 0 horizontal y extendiéndose desde el medio hasta los lados"*): el marco y el trazo son ahora **la misma animación**.

- **`CaptureBox`** guarda **una sola vez** la posición y el tamaño que autoraste (`BoxPos`/`BoxSize`), en la primera llamada a `SetBirth` — o sea antes de que nada los toque. Si movés el `GraphArea` en el Designer, al re-jugar se recaptura solo.
- **`ApplyBox`** escribe cada cuadro `ancho = BoxSize.x × Birth01` y corre la posición para **mantener el centro fijo**.
- **`SyncBox` ya no aplica `Birth01`**: lee el slot vivo, que ya viene encogido. Aplicarlo dos veces era el error obvio a evitar.
- **`GuardFrame`** pone el `GraphArea` en `Hidden` por debajo de `Birth01 = 0.02`, para que no quede una astilla vertical de contorno al arrancar. `Hidden` conserva el layout, así que el slot que lee `SyncBox` sigue siendo válido.
- **`Rebuild` no construye puntos por debajo de ese mismo 0.02**: limpia `PointsW` y sale. Así el trazo **no existe** mientras el marco está cerrado, en vez de existir y depender de que sea invisible.

🚩 **El bug del trazo NEGRO en la esquina (2026-08-24) — dos causas encadenadas, y ninguna era obvia:**
1. Para fundir el trazo se hacía `(* LineColor Birth01)`. **El operador `*` de LinearColor × float promueve el float a `(v,v,v,1)`: multiplica RGB pero deja el ALFA en 1.** Con `Birth01 = 0` eso da `(0,0,0,1)` — **negro OPACO**, no transparente.
2. Y se dibujaba **arriba a la izquierda** porque con el marco a ancho 0 el guard de `SyncBox` no entra, y `RightX`/`StepX`/`BaseY`/`SpanY` se quedan con **los defaults del CDO** (306 / 6,2 / 246 / 52), que en un lienzo de 1920×1080 caen en esa esquina.
✅ Se resolvió quitando el multiply (el `OnPaint` usa `LineColor` tal cual) y **no generando puntos** mientras el marco está cerrado. Menos nodos y sin depender de la aritmética de color.
⚠ **Regla que se lleva de acá: para fundir un color en el DSL no alcanza con multiplicarlo por un escalar.** Hay que tocar el alfa explícitamente, o — mejor — no dibujar.

La extensión horizontal vive en `SyncBox`: el semiancho es `(size.x/2 − Pad) × Birth01` medido desde el centro del marco, y `StepX` se recalcula para que las 48 muestras entren siempre en ese ancho.

🔴 **`SetPulse` multiplica por `Birth01`.** Si no, el latido escribiría la escala del `Dot` cada frame y pisaría la animación de nacimiento.

🔴 **El default de `Birth01` en el widget es 1, no 0.** Con 0 el Designer se vería vacío y no se podría autorar. Quien apaga el HUD es el ACTOR: `CacheWidgets` llama a `PushBirth` apenas cachea el widget, y eso lo deja en 0.

### El disparo
`CheckBirthCue` (en `EnsureRefs`, cada tick) mira al [[BP_Director_Story]] y nace cuando:
```
Room > 0   (arranque por salto de debug: si empezás a mitad de obra, el HUD ya existe)
o  Sub >= BirthCueSub   (5 = el paso del Hall donde suena el VO 5, justo después de tomar el sensor)
```
🔴 **No se tocó `BP_Director_Story`.** El HUD ya consultaba su `Room` para la carga; consultar también `Sub` sale gratis y evita meter mano en el BP del director. Es el mismo criterio declarativo que la carga por etapa.

⚠ **Ojo con la numeración de VO:** en el director, **VO 5 es `VOTaken`** (la línea que suena recién tomado el sensor), no la de elegir la ameba. Los índices reales son `VOStart=1`, `VOAppear[0]=2`, `VOMove[0]=3`, `VOStep[0]=4`, `VOTaken=5`, `VOChoose=7`. El plan del guión decía otra cosa; manda el director.

### Palancas
| Variable (actor) | Default | Qué hace |
|---|---|---|
| `BirthTime` | 2.5 s | cuánto dura el nacimiento |
| `BirthCueSub` | 5 | en qué paso del Hall nace |
| `bBirthOnStart` + `BirthDelay` | false · 3 s | andamio para probarlo suelto, sin el director |
| `bBorn` | false | se pone en true al disparar; el cue es de una sola vez |

La curva es un **ease-out** (`1 − (1−t)²`): entra rápido y se asienta.

✅ Verificado en PIE: `HUD: nace, animado` una sola vez, cero `Accessed None`. ⚠ **La rama del `Sub >= 5` no se pudo probar en PIE** porque el Hall espera a que el usuario tome el sensor y sin visor no hay manos; lo verificado es la rama `Room > 0` del salto de debug, que corre exactamente el mismo código.

## De dónde salen las señales
🔴 **La oscilación NO se simula adentro del HUD: viene del Blueprint de OSC** (pedido de Beltrán:
*"envía una variable oscilante desde el blueprint de OSC, que funcione como un emulador de lo que estaría
enviando el sensor"*). El HUD encuentra el **[[BP_BioHub]]** por clase y lee `CalmSmooth` y `HeartSmooth`.

🔴 **`BP_BioHub` TIENE que estar colocado en el world**: es un Actor y toda su vida está en `BeginPlay`
(levanta el servidor OSC) y en el `Tick` (`MaybeFake` → `UpdateSignals`). Colocado en `L_SoulCharger` como
**`BioHub_SC`** en (−5355, 200, 120), con **`bFakeSignal = true`** y `FakeHz = 0.08` — su `FakeTick` ya era
el emulador. Cuando llegue el sensor real, se apaga `bFakeSignal` y no se toca nada más.

## La carga: +20 % por etapa terminada
No hay evento: la carga es **derivada**. El HUD encuentra el [[BP_Director_Story]] y calcula
`Charge01 = ChargeStep × (Room − 1)`, con `RoomNames = [hall, entering, recognizing, loving, attracting, surrounding]`.
- Hall (`Room`=0) → 0 %. Entrando a `recognizing` (`Room`=2) → 20 %. Después de `surrounding` (`Room`=6) → 100 %.
- Declarativo a propósito: **sobrevive al salto de debug** y no se pierde ningún aviso. Se apaga con
  `bChargeFromStory = false`, y ahí manda `SetCharge(P)` a mano. `StageComplete()` existe igual como API.

## Registro de variables (el actor)
| Variable | Default | Rol |
|---|---|---|
| `bAttachToCamera` | true | pegarse a la cámara del pawn en cuanto haya pawn |
| `bStartHidden` | false | nacer invisible (para que el Hall lo encienda con `SetVisible`) |
| `bChargeFromStory` | true | la carga sale del `Room` del director |
| `ChargeStep` | 0.2 | cuánto suma cada etapa |
| `GraphRate` | 8 (Hz) | muestreo del gráfico (48 muestras ≈ 6 s de ventana) |
| `BPM` | 72 | ritmo actual (lo pisa `HeartSmooth` cuando supera 30) |
| `PulseMin` / `PulseKick` / `PulseDecay` | 1.0 / 0.55 / 6.0 | escala base del punto, cuánto salta, con qué velocidad vuelve |
| `Charge01` / `Calm01` | 0 / 0.5 | estado de las señales |
| `BeatPhase` / `PulseNow` / `GraphT` | — | estado interno |
| `HudW` + `bCached` | — | el widget, cacheado con un cast |
| `Bio` + `bBioFound` · `Story` + `bStoryFound` | — | los dos actores que consulta |
| `bAttached` | false | ya se colgó de la cámara |

## Estructura de grafos
- **BeginPlay** — `SetVisible(!bStartHidden)`. Nada más: el resto se resuelve solo en el Tick.
- **Tick** — `EnsureRefs` · `StepSignals` · `StepCharge` · `StepBeat(Δ)` · `StepGraph(Δ)`.
- **`EnsureRefs`** — llama a `EnsureWidgets` / `EnsureAttach` / `EnsureBio` / `EnsureStory`, cada uno
  guardado por su bool. 🔴 Son funciones separadas a propósito: en el DSL un `if` termina la lista de
  statements, así que un guard en el medio hay que extraerlo.
- **`CacheWidgets`** — cast del `GetUserWidgetObject` del componente; al cachear **re-aplica
  `SetCharge(Charge01)`** por si la carga llegó antes que el widget.
- **`AttachHead`** — `CastToPawn(GetPlayerPawn)` (el cast **es** el guard de nulo, sin `IsValid`) →
  `GetComponentByClass(CameraComponent)` → `AttachActorToComponent(self, cam, Snap/Snap/Snap)`.
- **`StepBeat`** — el punto decae con `FInterpTo` hacia `PulseMin` y salta a `PulseMin+PulseKick` cada vez
  que `BeatPhase` (que avanza `Δ·BPM/60`) pasa 1.
- **`StepGraph`** — acumula `Δ` y cada `1/GraphRate` empuja `Calm01` al widget.
- **`PreviewGraph`** (Construction Script) — siembra la onda de demo **para verla en el editor**.

## ⚠ Trampas pagadas al construirlo (2026-08-24)
1. 🔴🔴 **`PreConstruct` NO corre en el preview de editor de un `WidgetComponent` — sí en PIE.** Media hora
   de diagnóstico falso: la onda no aparecía en el viewport y la hipótesis obvia (*"`DrawLines` no dibuja"*)
   era **falsa**; simplemente no había puntos porque el seed nunca se ejecutaba. Medido con `PrintString`.
   👉 Lo que tenga que verse en el editor se siembra desde el **Construction Script del actor**.
2. 🔴🔴 **Al AGREGAR un componente a un BP que ya tiene instancias colocadas, la instancia se queda con los
   defaults del MOTOR** (`widgetClass = None`, `drawSize 500×500`, escala 1) y `set_properties` sobre esa
   instancia **devuelve `true` sin aplicar**. Otra cara de "lo de la instancia le gana al Blueprint". El
   síntoma fue "el cilindro no renderiza" — y no era el cilindro: era que la instancia no tenía widget.
   ✅ **La salida limpia es borrar la instancia y volver a colocarla** desde el asset, que la reconstruye
   del CDO. Verificar SIEMPRE con `get_properties` sobre el componente **de la instancia**, no del CDO.
3. ⚠ **En una instancia, `set_properties` con varias propiedades aplica sólo la primera.** Hubo que mandar
   `geometryMode`, `relativeScale3D`, `relativeLocation` y `overrideMaterials` en **llamadas separadas**.
4. 📸 **Para ver píxeles de PIE, `CaptureViewport` no sirve** (captura el viewport del editor, con los
   actores en su pose autoral): la que sirve es **`EditorAppToolset.CaptureEditorImage()`**.

## Status
🟡 **Construido, compilando y verificado en PIE (2026-08-24)**: el widget dibuja, la onda corre con datos
vivos del BioHub, el actor se cuelga de la cámara del pawn. ⬜ **Falta visor** — y la diagramación fina
(tamaños y posiciones dentro del lienzo) es juicio de Beltrán con el casco puesto.

## Sin fondo — decisión de Beltrán
*"el widget no debería tener fondo, solo debería tener los gráficos flotando en el espacio"*. No hay fondo
en el gráfico (`GraphArea` está en alpha 0) y el riel de la barra quedó en **alpha 0**.
⚠ **Consecuencia**: con la carga en 0 la barra es invisible. Si querés el riel de vuelta es **un número**:
`WBP_SoulHUD_SC` → `Bar` → Style → Background Image → Tint → alpha.

## TODO
- [ ] 🔴 **Visor**: tamaños, distancia, legibilidad, comodidad del attach rígido.
- [ ] Diagramación fina dentro del lienzo (arrastrar en el Designer).
- [ ] Nacimiento animado elemento por elemento y muerte en la carga final.
- [ ] Arte real de los tres elementos.
- [ ] Cuando llegue el sensor: apagar `bFakeSignal` del `BioHub_SC`.

## Relacionados
[[BP_SoulHUD]] (el viejo, referencia) · [[BP_BioHub]] (la señal) · [[BP_Director_Story]] (el `Room` que da la carga) ·
[[BP_ProtoSoul_SC]] (el mismo truco de Disable Depth Test) · [[BP_FaceAnchor_SC]] (el doble del HMD)
