# BP_PulseField_SC + M_PulseField_SC — las ondas del latido (Core/Light/)

> Creado 2026-09-18 a pedido de Beltrán, con dibujo: **anillos concéntricos que nacen en un centro y se expanden**, y de perfil un tren de olas que levanta la superficie. Pensado para **Heart**: cada onda sale con el latido.
> Plan: [`docs/PLAN-MODOS-METABALL-Y-PULSO-2026-09-18.md`](../../../../docs/PLAN-MODOS-METABALL-Y-PULSO-2026-09-18.md).
> **Estado: 🟡 construido, compilando y colocado como estación 12 de la galería (`GAL_11_PulseField`, x=333.604). Sin visor y sin juicio de Beltrán.**

## Qué es
Un plano denso (`SM_CloudPlane`) cuyo **WPO** lo levanta con la suma de K anillos gaussianos que viajan hacia afuera desde el centro del actor. Unlit y **opaco** (fill barato: no suma translucidez a una galería que ya va justa).

🔴 **No es un duplicado de `BP_CloudPlane_SC`.** El océano sigue intacto en su estación; duplicarlo habría arrastrado decenas de perillas muertas (regla del proyecto). Este nace con 13 variables, todas vivas.

## Por qué NO hay buffer de eventos de latido
Se copió el patrón **ya probado en `BP_RingTunnel_SC`**: una fase continua y K anillos separados **una unidad de fase** (= un latido).
```hlsl
for (k = 0; k < Rings; k++) {
  float age = frac(Phase) + k;              // edad en latidos
  float x   = (r - age*RingSpeed) / RingWidth;
  h += exp(-x*x) * exp(-age*Decay);         // gaussiana que se desvanece con la edad
}
return h * Amp * m;                          // m = factor de respiración
```
Con `Rings` 4 son 4 evaluaciones por píxel. Sin arrays, sin spawn, sin estado por onda.

🔴 **La fase se INTEGRA en el Tick del BP** (`PulsePhase += (RateBPM/60)·DT`), **nunca `Time × Rate`**: cambiar el ritmo en caliente con `Time×Rate` saltaría la onda entera. Es el mismo gotcha que ya se pagó en los túneles.

## Cañería del material
- `D` = `WorldPosition − ObjectPositionWS` → `r = length(D.xy)`, o sea el radio medido desde el actor.
- `Custom` **`Ripple`** (4 entradas: `D`, `ParA`, `ParB`, `S`) con `ParA = (Phase, RingSpeed, RingWidth, Amp)` y `ParB = (Decay, Rings, BreathIn, BreathOut)`.
- **WPO** = `VertexNormalWS · h` → se levanta **a lo largo de la normal**, así que funciona aunque el actor esté rotado.
- **Emisivo** = `lerp(ColorLow, ColorHigh, saturate(h/Amp)) · Brightness` → las crestas se encienden.
- La respiración entra con el mapeo estándar de la casa (`m = 1 + S·lerp(−Out, In, smoothstep)`, neutro en reposo) leyendo `Signed` de `MPC_Breath`: **se ve con `PreviewBreath` sin dar Play.**

## Perillas
`A - Forma` (SizeCM 2000 · RingSpeed 300 · RingWidth 80 · Amp 60 · Decay 0,5 · Rings 4) · `B - Ritmo` (**RateBPM 60**) · `C - Color` (ColorLow · ColorHigh · Brightness) · `R - Respiracion` (BreathIn · BreathOut, en 0) · `Z - Estado` (PulsePhase, interna).

## 🔩 Dos trampas pagadas al construirlo
1. 🔴 **`CreateDynamicMaterialInstance` tiene DOS sobrecargas con el MISMO `type_id`** (`Rendering|Material|CreateDynamicMaterialInstance` aparece dos veces en `find_node_types`, más la de Decal). El DSL resolvió a la que tiene pin `Parent` y falló con *"Could not connect pin Surface to Parent"*. ✅ **No hace falta el nodo**: se le asigna el material al componente con `overrideMaterials` en el CDO y los `Set...ParameterValueOnMaterials` crean el MID solos.
2. ⚠ `add_to_scene_from_asset` **ignora el `xform`** (gotcha conocido): hay que escribir `relativeLocation` en el **root component** después de colocar. Verificado leyendo la transform.

## ⬜ Lo que falta
- [ ] **Juicio de Beltrán** sobre la forma de la onda, y ajuste de `RingSpeed`/`RingWidth`/`Decay` mirando.
- [ ] **BPM real**: `BP_BioHub` ya trae el latido por OSC y tiene **`bFakeSignal` + `FakeHz` para simularlo sin sensor** (inyecta por el mismo camino que el OSC real → `HeartSmooth`). Falta (a) colocar un BioHub en la galería, (b) que este BP lo busque con `GetActorOfClass` + cast (como hace `BP_SoulHUD_SC`) y use `HeartSmooth` como `RateBPM`, con una perilla `bUseBioHub`.
- [ ] **Resync al latido**: con el BPM ya se emite a la frecuencia correcta, pero la onda no sale *en* el latido. La salida es empujar suave `PulsePhase` al entero más cercano en cada `OnBeatPulse` (el aviso por latido que ya publica `BP_Sensor_Soul` en modo 2).
- [ ] Medir fill en visor: es un plano grande, pero **opaco y unlit**, así que debería ser barato.


## 💧 2026-09-18 (misma jornada) — LA GOTA en el centro + la onda que crece o decrece
Beltrán, tras verlo (*"se ve super"*), con un tercer dibujo: dos perfiles de una gota que se funde con la superficie por un **cuello**. Pedido: *"¿es posible mezclarlo con el efecto del metaball, que el lugar donde inicie la onda sea como una gota?"* · *"agregale una perilla para decidir que a medida que se aleja la onda, la altura suba o disminuya"* · *"cuando inicia un pulso, la gota flotante al centro también se agranda, y se mezclará un poco con la ola"*.

### La gota: **el mismo operador del metaball**, no una malla
No hace falta un raymarch: el dibujo es un **perfil de altura**, y lo que hace el cuello es el **smooth-max**, que es literalmente el smooth-min del metaball con el signo dado vuelta.
```hlsl
float swell = 1.0 + DropBeat * exp(-ph * DropFall);        // se infla en cada latido
float drop  = DropHeight * swell * exp(-(r*r)/(DropRadius*DropRadius)) * m;
float tg = saturate(0.5 + 0.5*(drop - h)/DropSmooth);
return lerp(h, drop, tg) + DropSmooth*tg*(1.0 - tg);       // smooth-MAX = el cuello
```
- `DropSmooth` **es el cuello**: en 0 la gota se apoya y se corta; grande, se derrite sobre la superficie.
- 🔑 **El latido cae en el mismo lugar que la gota**: el anillo nuevo nace en `age = frac(Phase) ≈ 0`, o sea en `r ≈ 0`. Por eso, al inflarse la gota justo en el latido, el cuello con el anillo recién nacido **se engorda solo** — la onda se ve *salir* de la gota. No hubo que sincronizar nada: ya estaban en fase por construcción.
- `swell` usa `exp(-ph·DropFall)`: salto instantáneo en el latido y relajación suave. `DropBeat 0` = gota quieta.

### `AmpGrow` — que la ola crezca o decrezca al alejarse
```hlsl
float env = exp(-age*Decay) * max(1.0 + AmpGrow*age, 0.0);
```
`AmpGrow` **0** = como estaba (solo decae por `Decay`) · **positivo** = la cresta sube a medida que se aleja · **negativo** = se apaga antes. El `max(...,0)` evita que se dé vuelta. Sigue acotado por `Decay`, así que no se dispara.

### Perillas nuevas
`A - Forma`: **`AmpGrow`** (0) · `D - Gota`: **`DropHeight`** (80) · **`DropRadius`** (150) · **`DropSmooth`** (40) · **`DropBeat`** (0,6) · **`DropFall`** (3).
El `Custom` quedó en **6 entradas** (`D`, `ParA`, `ParB`, `S`, `ParC`, `ParD`).

⚠ **Las 6 variables nuevas nacieron en CERO en la instancia ya colocada** (el clásico del proyecto). Se sembraron explícitamente las 18 de `GAL_11_PulseField`; con `DropRadius` o `DropSmooth` en 0 la gota no se ve.


### 🔧 2026-09-18 (2a) — "no veo la gota" + altura inicial y final
Beltrán, con captura del viewport: los anillos andaban bien, la gota no se leía.

**Las dos causas, las dos reales:**
1. 🔑 **Un gaussiano es una COLINA, no una bola.** `exp(-r²/R²)` tiene tangente horizontal en el borde: por más alto que se ponga, se lee como montículo. ✅ Cambiado a **casquete esférico** `sqrt(saturate(1 − r²/R²))`, que tiene tangente **vertical** en el borde — ese es el perfil que el ojo lee como gota.
2. **El anillo recién nacido está en `r ≈ 0` a amplitud completa** y se comía la gota justo donde nace. Con `HeightStart` chico el centro queda calmo y la gota tiene lugar.

**`AmpGrow` se fue; ahora son dos alturas** (pedido textual: *"debemos poder manejar la altura inicial y la altura final"*):
```hlsl
float u    = saturate(age / Rings);        // 0 recién nacido … 1 fin de su vida
float amp  = lerp(HeightStart, HeightEnd, u);
float fade = 1.0 - smoothstep(RingFade, 1.0, u);
```
- **`HeightStart`** (20) = altura del anillo al nacer · **`HeightEnd`** (200) = altura al final. Con `End > Start`, **cuanto más grande el anillo, más alta la ola**, que es lo pedido. Invertidos, al revés.
- **`RingFade`** (0,75) = en qué fracción de su vida empieza a apagarse, para que no desaparezca de golpe en el borde.
- 🧹 **Se borraron `Amp`, `Decay` y `AmpGrow`** del BP y del material: las dos alturas las subsumen y quedarían como perillas muertas. El emisivo ahora normaliza por `max(HeightStart, HeightEnd)`.

**Defaults nuevos de la gota**: `DropHeight` 200 · `DropRadius` 200 · `DropSmooth` 60.

⚠ **Límite honesto del enfoque:** esto es un **campo de altura**, y un campo de altura **no puede colgar**. La gota puede tener perfil de bola y un cuello, pero nunca un cuello más angosto que su parte más ancha, ni flotar despegada. Si en algún momento se quiere la gota **realmente flotando** (el dibujo de la izquierda), eso pide una **esfera de verdad** como componente y que la superficie suba a encontrarla — el cuello seguiría saliendo del smooth-max de abajo.


### 🔮 2026-09-18 (3a) — LA GOTA ES UNA ESFERA DE VERDAD
Beltrán: *"quiero que en verdad se vea como una esfera flotando, y cuando se agranda se empieza a unir. Tal como lo tenemos en el metaball"*.

🔴 **Un campo de altura NO puede colgar** — es `h(x,y)`, de un solo valor: no hay forma de que una bola quede despegada con un cuello más angosto que su ecuador. Se probó con gaussiano (colina) y con casquete esférico (mejor perfil, pero igual pegado). **El enfoque tenía que cambiar, no los números.**

### La arquitectura nueva: geometría real + la superficie que la busca
| pieza | qué es |
|---|---|
| **`Drop`** | componente nuevo: la **esfera de engine** con `M_DropBall_SC` (unlit, wrap-lambert de 3 líneas contra una luz fija, mismos `ColorLow/ColorHigh/Brightness` que la superficie para que peguen) |
| **`DropPull`** | parámetro del material de la superficie: **cuánto sube el bulto** para alcanzar a la esfera. Lo calcula el BP por frame, ya no es una forma dibujada |
| **`StepDrop`** | función llamada desde el **Construction Script Y el Tick**: coloca y escala la esfera, y calcula `DropPull`. Por eso se ve bien en el viewport sin dar Play |

```
sw     = 1 + DropBeat · exp(−frac(Phase)·DropFall)      // la esfera se infla en el latido
rs     = DropRadius · sw
fondo  = DropZ − rs                                      // altura del fondo de la esfera
pull   = DropBumpMax · saturate(1 − fondo/DropReach)     // 0 si está lejos; crece al acercarse
```
- **Lejos → `pull` = 0**: superficie plana y la esfera **flota despegada**, que era el pedido.
- **Al inflarse en el latido, `fondo` baja** → el bulto sube a encontrarla → **se unen**. El `smooth-max` con la ola hace el cuello.
- El radio del bulto se empuja como `rs · 1.2`, así el bulto siempre es un poco más ancho que la esfera y el cuello abre hacia afuera.

### Perillas de `D - Gota` (reemplazan a `DropHeight`)
**`DropRadius`** 150 (radio de la esfera) · **`DropZ`** 320 (a qué altura flota) · **`DropReach`** 250 (a qué distancia la superficie empieza a estirarse hacia ella) · **`DropBumpMax`** 200 (cuánto puede subir el bulto) · **`DropSmooth`** 60 (el cuello) · **`DropBeat`** 0,6 / **`DropFall`** 3 (el inflado del latido).
Con esos valores: en reposo `fondo` = 170 y `pull` = 64 → **separados**; en el latido `rs` = 240, `fondo` = 80, `pull` = 136 → **fundidos**.

🧹 Se borraron del material `DropBeat`/`DropFall` (pasaron al BP) y el `Custom` volvió a **5 entradas**.
⚠ Beltrán ya estaba ajustando `HeightStart`/`HeightEnd` en paralelo (7,5 / 150,7): **no se pisaron**.
⬜ Sin visor.

#### 🔴 Por qué "no lograba separar la gota": el componente nuevo llegó SIN MALLA a la instancia
Beltrán movió todas las perillas sin conseguir que flotara. La causa, **leída y no supuesta**: `BP_PulseField_SC_C_0.Drop.staticMesh = **None**`. Es la mordida clásica (gotcha §320): **un componente agregado al CDO llega sin malla a los actores YA COLOCADOS**. Se le había puesto la esfera al Blueprint, pero no a la instancia.

👉 O sea que **lo que estaba ajustando no era la esfera: era el bulto de la superficie** (`DropPull`), que sí se veía. Por eso ninguna perilla lo separaba: no había esfera que separar.
✅ `staticMesh` escrito **también en la instancia**. `StepDrop` siempre había funcionado bien (la `relativeLocation` de la instancia ya seguía a `DropZ`).
🚩 La señal que lo delataba estaba en la captura: **se veía una semiesfera perfecta**, que es lo que se ve cuando una esfera está centrada en z = 0... salvo que acá no había esfera en absoluto, y la "media esfera" era el casquete del bulto. Dos causas distintas producen la misma imagen — por eso hubo que leer la propiedad.

#### La cuenta para autorar la separación
```
radio  = DropRadius · (1 + DropBeat)   ← en el latido;  DropRadius entre latidos
fondo  = DropZ − radio
bulto  = DropBumpMax · saturate(1 − fondo/DropReach)
separación = fondo − bulto        > 0 flota  ·  < 0 fundida
```
Valores dejados (con los de Beltrán, `DropZ` = 200): **entre latidos separación +51** (flota) · **en el latido −21** (se funden). Subir `DropZ` = más despegada siempre; subir `DropReach` o `DropBumpMax` = se funden antes.


## 🌀 2026-09-18 (4a) — MODO RAYMARCH (fusión de verdad) + BPM por OSC
Beltrán: *"la unión es re fea... si no se puede hacer tan smooth como en el metaball, dejá un botón"* → **se hicieron las dos**: el botón y la versión raymarcheada.

### Por qué la malla nunca iba a fundirse bien
Esfera de malla + bulto del campo de altura son **dos superficies distintas que se cruzan**: en el cruce hay una arista, y cada una se sombrea con su propia ley (la esfera por su normal, el campo por su altura). El metaball se ve liso porque es **UNA sola superficie implícita**. No es cuestión de perillas.
🔩 Además el perfil de casquete (`sqrt(1−r²/R²)`) llega al borde con **tangente vertical** y el plano no tiene vértices para representarlo → **dientes de sierra** en la falda. Cambiado a `q²`, que llega con pendiente 0.

### Los dos modos (`D - Gota`)
| perilla | qué hace |
|---|---|
| **`bShowDrop`** | prende/apaga la gota entera (esfera **y** bulto) |
| **`bRaymarchDrop`** | **✔ = blob raymarcheado** (fusión real) · **✘ = esfera de malla + bulto** (barato) |

`StepDrop` conmuta visibilidades y, en modo raymarch, pone `DropPull` en **0** (el cuello ya lo hace el `smin`, si no habría bulto doble).

### `M_DropBlob_SC` — la fusión real
Componente **`Blob`**: el cubo de engine como proxy (se escala solo a `max(rs·2,6, DropZ + rs·2)`), translúcido unlit, **el mismo patrón que `M_MetaBlob_SC`**.
```hlsl
dG = pos.z − alturaDeLaOla(pos.xy)      // la MISMA fórmula de anillos que la superficie
dS = length(pos − (0,0,DropZ)) − Rs     // la esfera
hh = saturate(0.5 + 0.5*(dG − dS)/Smooth);
d  = lerp(dG, dS, hh) − Smooth*hh*(1−hh);   // smooth-min: el cuello sale de acá
```
- **La costura con la malla del oleaje no se ve** porque el raymarch usa la **misma fórmula de olas** y el **mismo degradado por altura** (`lerp(ColorLow, ColorHigh, z/max(HeightStart,HeightEnd))`): en el borde del proxy los dos calculan el mismo valor.
- Ray desde la cara del proxy (`WorldPosition − ObjectPositionWS`), 32 pasos con factor 0,6 (el SDF del suelo sobreestima la distancia).
- `Smooth` = `DropSmooth`, la misma perilla del cuello que el modo malla.
- ⚠ **Sin medir en visor.** Son 32 pasos × 4 anillos = 128 `exp()` por píxel dentro del proxy. Si pesa: bajar `Rings`, achicar `DropRadius` (achica el proxy) o volver al modo malla con el tilde.

### BPM por OSC
- **`bUseBioHub`** (`B - Ritmo`). En `BeginPlay` busca `BP_BioHub` (`Actor|GetActorOfClass` + `CastToBP_BioHub`), lo cachea en `Bio` y marca `bBioOK`. `StepRate` (por Tick) hace `RateBPM = clamp(HeartSmooth, 30, 200)`.
- 🟢 **Se colocó `GAL_BioHub` en la galería** (`Galeria/_Sistema`) con **`bFakeSignal = true`**: genera latido simulado por el MISMO camino que el OSC real, así se prueba sin sensor. Para el sensor de verdad: apagar ese flag (puerto 10000, `/muse/heart_rate`).
- La fase se sigue integrando (`PulsePhase += RateBPM/60·DT`), así que cambiar el BPM en caliente **no salta la onda**.
- ⬜ **Falta el resync al latido**: hoy la onda sale a la frecuencia correcta pero no exactamente EN el latido. La salida es empujar suave `PulsePhase` al entero más cercano en `OnBeatPulse` de `BP_Sensor_Soul`.

✅ **Verificado en PIE**: arranca en 0,33 s, **cero errores, cero `Accessed None`, cero bucles infinitos**. ⬜ Sin visor y sin juicio de aspecto.


## 🌀 2026-09-19 — LOS ANILLOS QUE SE ELEVAN (`E - Elevacion`)
Beltrán, con dibujo (espiral en el plano + elipses apiladas subiendo): *"un ring que empieza a elevarse verticalmente desde el wave reach, y que nace cuando cada ola llega a desaparecer... dando el efecto de continuidad de que la ola se eleva hacia el cielo"*. Requisito explícito: **en el primer pulso no existe ningún anillo hasta que la primera ola llega al `WaveReach`**.

### 🔴 Pidió Niagara; se hizo con MALLAS. Las tres razones
1. **Se previsualiza en el viewport sin Play** — un emisor de Niagara solo vive en Play, y todo este BP está construido para autorarse mirando (`PreviewRadii`, `SeedRise`). Regla de la casa: preferir siempre la técnica previsualizable.
2. **La sincronía sale exacta por construcción**: el anillo nace leyendo el MISMO `RingBirth`/`WaveDist` que las olas, en el mismo tick. Con Niagara habría que emitir un evento y esperar al tick del sistema.
3. **El color es el mismo objeto**: el material toma `ColorHigh` del actor, así que sigue al de las olas solo.
👉 Si algún día se quiere look de partícula (estela, blur, muchos anillos finos), **mesh renderer** en Niagara; ribbon no (pide una cadena de partículas por anillo) y sprite tampoco (no lee de canto en VR).

### Piezas
| pieza | qué es |
|---|---|
| **`SM_PulseRing_SC`** | toro nativo **R mayor 100 / tubo 2** (2 % del radio), 96×12 = **2.304 tris**. Generado por OBJ con verificación numérica: 2.304 caras hacia afuera, 0 invertidas |
| **`M_PulseRing_SC`** | unlit, opaco, **TwoSided** (seguro ante el flip de bobinado del import). Emisivo = `RingColor × RingGlow`. Sin fundido (ver abajo) |
| **`Rise0..Rise5`** | 6 StaticMeshComponents del BP. El componente `k` muestra el anillo del slot `k` de `RiseBirth` |

### La promoción: sin cola de eventos, sin tocar `StepWave`
La ola del latido `i` está en `RingBirth[p]` con `p = LastBeat − LastRise − 1`. Cuando esa ola recorrió `WaveReach`, se promueve:
```
_lr = Max(LastRise, LastBeat − 6)          ; si nos atrasamos más de 6 nacimientos, se engancha
_p  = LastBeat − _lr − 1                   ; −1 = todavía no nació ninguna → NO hay anillo (el pedido)
if (_p in [0,5]) and (WaveDist − RingBirth[_p] >= WaveReach):
    LastRise += 1 ;  Insert RiseBirth[0] = RiseDist ;  RemoveIndex 6
```
`RiseDist` es un acumulador propio (`+= RiseSpeed·DT`), así la **altura = `RiseDist − RiseBirth[k]`** sin conversiones ni razón de velocidades.

### 🔴🔴 Dos trampas pagadas acá
1. **`SetVisibility` NO sirve para apagar un componente desde el Construction Script.** Un `bVisible = true` **se graba como override de la instancia** (difiere del template, que está en `false`) y el editor lo **reaplica DESPUÉS** del CS → el anillo muerto seguía visible. Síntoma delator: la muerte funcionaba con sobrepaso grande (u=32) y fallaba con sobrepaso chico (u=1,07), porque solo los que alguna vez estuvieron vivos tenían el override. ✅ **La muerte se hace con `RelativeScale3D = 0`**: la transform sí se reaplica en cada pasada del CS. Es otra cara de *"lo de la instancia le gana al Blueprint"*.
2. **Un fundido a negro NO es un fundido.** El material es unlit opaco: multiplicar el emisivo por `Fade` lo lleva a **negro**, y contra un fondo claro el anillo moribundo se lee como una banda NEGRA (lo cazó Beltrán en el viewport). Se borró `RiseFade` y el `Fade` del material: **el anillo vive a color pleno y desaparece de golpe**; la desaparición la va a hacer él con el **fog slab**.

### Perillas de `E - Elevacion`
**`bShowRise`** (true) · **`RiseSpeed`** 800 cm/s (igual que `RingSpeed` = continuidad perfecta) · **`RiseHeight`** 6000 cm (a qué altura muere) · **`RiseThick`** 1,0 (achata el tubo en Z; 0,3 = cinta) · **`RiseGlow`** 1,0.
Estado (`Z - Estado`): `RiseDist`, `RiseBirth` (6), `LastRise`.

### Cableado
`EventTick` → … → `StepWave` → **`StepRise(DT)`** · `EventBeginPlay` → … → **`ResetRise`** (deja `RiseBirth` en −1.000.000 → ningún anillo hasta la primera llegada) · **Construction Script** → `PreviewRadii` → **`SeedRise`** (siembra 6 alturas separadas `RiseSpeed × BeatsPerWave × 60/BPM` para verlo sin Play, y empuja color y glow a los 6 componentes).

⚠ **La malla llegó en `None` a la instancia ya colocada** (gotcha §320/341, otra vez): hubo que escribir `staticMesh` en los 6 componentes de `BP_PulseField_SC_C_0`, no solo en el CDO.
⬜ Sin visor. El nivel quedó **sin guardar**; los tres assets (`SM_PulseRing_SC`, `M_PulseRing_SC`, `BP_PulseField_SC`) sí están guardados.


### 🔍 2026-09-19 (2a) — por qué "no estaba la mecánica del latido" (y sí estaba)
Beltrán: *"No está funcionando el umbral de ritmo cardiaco. No está la mecánica. Solo está el umbral de respiración, que hay que sacarlo en esta estación."*

**Medido en PIE, no supuesto** (`StartPIE` → `LogsToolset.GetLogEntries` → `StopPIE`):
- `HEART: listo` **sí** salía → el manager corría y resolvía cámara y manos.
- Con un **control positivo** (zona abierta a lo bestia: `HorizMax` 500, `VDrop` ±500) apareció `HEART: UMBRAL IN h=4,6 v=-4,6` y la instancia de PIE mostró `bHeartZone=true`, `BeatCount=25`, `BPM=61,9`, `RingBirth` con 6 nacimientos reales a ~1600 cm, `RiseBirth` lleno. **La cadena completa funciona.** Cero `Accessed None`.
- 👉 Los números `h=4,6 v=-4,6` explican todo: **en escritorio la mano queda PEGADA a la cámara** (4,5 cm por encima), así que la zona real del pecho (`VDropMin` 10) no abre nunca.

🔴 **Lo que sí estaba mal, y era otra cosa:** el `BP_BreathManager_SC` seguía corriendo en esta estación y **peleaba por el mismo mando** (`SetHapticsByValue` continuo). Sus zonas además **se solapan**: pecho (`VDrop` 10-45) vs panza (`SafeVDrop` 33-63) comparten 33-45.

✅ **El arreglo usa el mecanismo que el director ya tenía, sin código nuevo:** los actores de estación llevan `GALSTATION` + `GAL_<n>` y `GalHideAll`/`GalShow` les prenden y apagan el **tick** por estación.
- `GAL_HeartManager` → tags **`GALSTATION` + `GAL_11`** (la mecánica del latido existe SOLO en esta estación, que era el pedido).
- `GAL_BreathManager` → tags **`GALSTATION` + `GAL_0`…`GAL_10`** (todas menos la 11).
Verificado en PIE: en la estación 11 sale `HEART: listo` y **ya no sale `BREATH: listo`**.
⚠ Borde conocido: si el tick se apaga con el zumbido encendido, queda pegado. En la práctica no pasa (para cambiar de estación hay que sacar el mando del pecho, y eso cierra la zona). El `HeartZoneFx` del latido además **escribe 0 en cada tick** fuera de zona, así que limpia cualquier zumbido que haya quedado de otra mecánica.

**Instrumento para afinar en gafas:** `bDebug` en el manager imprime `HEART dbg h=… v=… zona=…` cada 0,25 s, y el flanco del umbral loguea las medidas exactas. Los valores de zona vienen de `BP_Sensor_Soul` y **nunca se validaron en visor** — se afinan con estos números, no a ojo.

### 🎨 2026-09-19 (3a) — el anillo nace con el color base y madura al de la ola
Pedido: *"donde el anillo nace, que tome el color base, y que gradualmente pasen a tomar el color de la ola cuando se vayan elevando... quizás el segundo o tercero hacia arriba ya alcanzó"*.
`M_PulseRing_SC` ahora tiene **`RingColorLow`** (vector) + **`RingMix`** (escalar): emisivo = `lerp(RingColorLow, RingColor, RingMix) · RingGlow`. El CS empuja `ColorLow`/`ColorHigh` del actor a los 6 anillos; `StepRise` escribe `RingMix` por anillo.
**`RiseColorRings`** (`E - Elevacion`, **2**) = en cuántos espaciados de anillo se completa el viraje, así que **se autoajusta al BPM**: `cden = RiseColorRings · RiseSpeed · BeatsPerWave · 60/BPM`, y `mix = smoothstep(h/cden)`. Con 2: el que nace es base puro, el de arriba va por la mitad, el tercero ya es el color de la ola.
