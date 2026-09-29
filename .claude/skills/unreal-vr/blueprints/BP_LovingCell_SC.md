# BP_LovingCell_SC — la célula de Loving (Mechanics/Loving/)

> Creado el 2026-09-27. Efecto de la etapa **Loving**: una constelación orgánica — núcleo tipo
> ameba + 4-6 grupos de 2-3 bolas fundidas + una **membrana translúcida** que envuelve cada grupo
> y lo une al núcleo con hebras de tensión superficial. Un escalar **`State` 0→1** la lleva de
> SEPARADA (actividad neuronal alta: hebras largas y finas) a CONECTADA (actividad baja: el núcleo
> crece, los grupos se acercan, cuellos gruesos y puentes entre grupos vecinos).
> **Estado: 🟢 construido, compila, la forma se ve en el viewport del BP (S = 0,3).**
> **2026-09-27 (tarde): el núcleo también va envuelto en membrana** (`CentreFilm`, pedido de Beltrán).
> 🟢 **Vista junto al resto en el viewport del BP** (Beltrán reabrió la pestaña): cáscara con borde como las
> envolturas, brazos que nacen de ella con filetes continuos, una sola capa en las uniones.
> 🟢 **2026-09-27 (noche): FASE 1 de la VIDA construida** (el núcleo flota, cada grupo con su vaivén, resortes
> viscosos, actitud de toda la figura, temperamento con la calma) + los **arreglos de la revisión adversarial**
> (6 confirmados) y de la **crítica del plan** (5 bloqueantes). Compila con `warnings_as_errors`, guardado.
> ⬜ Movimiento sin ver: reabrir la pestaña del BP y activar **Simulation** (o colocar una instancia).
> ⬜ Barrido de estados sin verificar (el preview no se refresca por MCP — ver trampas) ·
> ⬜ sin PIE · ⬜ sin visor · ⬜ sin medir · ⬜ sin commitear.

## 🔴 BUG CONOCIDO (hallado 2026-09-29 en Test_Recorrido): divide by zero en `LifeApply`
PIE de Narrativa: miles de `Script Msg: Divide by zero: Divide_DoubleDouble` por cuadro desde `BP_LovingCell_SC_C_0`.
Causa (volcado `Saved/ClaudeScripts/Loving/bpdump/lifeapply.txt`): en `_thc = 2·Asin(Min(1, (24·Max(GroupSize,0,05)+2) /
(2,0 × _r1c)))` el pin B del Multiply quedó SIN conectar (0), así que la división es por 0. Corre para 6 grupos en cada Tick y en el CS, sin compuerta.
Como es un nodo puro, se reevalúa en cada uso. Visualmente es nulo (UE devuelve 0 → `_thc` = 0, el look aprobado); el costo es el LOG
en Development. Arreglo neutro: B = 1e9 (mismo resultado, sin mensajes). Arreglo de diseño: conectar `_r1c` (cambia apenas la
separación angular → decide Beltrán). **APLICADO por Narrativa (2026-09-29, madrugada):** `LifeApply.K2Node_PromotableOperator_114`
(2,0 × B) → B = 1e9 con `set_pin_value`; BP compilado y guardado (hubo que FORZAR el guardado: `set_pin_value` no marca el paquete como modificado, gotcha 498) ·
✅ 0 mensajes en PIE (Narrativa) ·
⬜ opción de diseño (conectar `_r1c`) mañana con Beltrán: al hacerlo, quitar el 1e9.

## 🟡 V4e (2026-09-28, noche) — PROPUESTA "NOCHE PERLA" (Turrell × Six N. Five), solo en la instancia de `Test_Fluid`
Pedido: *"una estética tipo James Turrell, pero más visualmente como lo que hace Six N. Five"*. Workflow de investigación +
3 propuestas + juez (`wf_c3631e33-68a`): gana **Noche perla** = el agua C que eligió Beltrán, sin el azul eléctrico: luna
crema desde arriba (óculo sin fuente), campo casi gris, la célula como ÚNICO objeto claro, sombras azul suave.
**Aplicado SOLO en las instancias de `Test_Fluid`** (el CDO no se tocó; esperando su juicio). Célula: `AmoebaColor1`
(0,888 0,863 0,823) · `AmoebaColor2` (0,271 0,361 0,540) · `ShadowColor` (0,034 0,056 0,102, 0,5) · `MembraneColor`
(0,665 0,731 0,823, 0,06) · `MembraneRim` (0,347 0,423 0,552, 0,18) · `DustColor` (0,672 0,638 0,571) · `DustOpacity` 0,4 ·
`OuterColor` (0,429 0,485 0,578) · `WaterLight` 0,5 · `WaterLightShell` 0. **Sin cambio** (decisión de Beltrán): forma y
opacidad de la envoltura, `OuterLook`, `OuterSh`, `LightDir`. Fluido: ver `BP_FluidMedium_SC.md` "Noche perla".
Para volver atrás: `Saved/ClaudeScripts/Fluid/paletas.json` → `antes_noche_perla`. Capturas: `shots/np_*.png`.
⬜ Pendiente del juez: leer `FilmSky`/`FilmGnd` (brazos, puentes, película del núcleo) y, si son lila, pasarlos a gris azulado.

## 🟡 V4d (2026-09-28, noche) — ESTÉTICA: menos sci-fi (paleta "perla + tinta") y envoltura CIRCULAR
Beltrán: *"un poquito sci-fi… el azul está demasiado saturado… el material de las esferas y amebas es rosado como piel,
debería ser como el metaball, blanco con azul más suave"* · *"la membrana contenedora de todo sigue muy deforme, debe ser un
poco más circular"* · de tres aguas mostradas eligió la **C (tinta)**: *"me gustó bastante, quizás por ahí"*.
- **Diagnóstico:** el tono "piel" venía de sombras VIOLETAS con R > G (AmoebaColor2 0,42/0,36/0,85, ShadowColor, OuterColor
  0,62/0,52/0,86 y el default de material `OuterSh` 0,20/0,14/0,36): sobre azul se leía rosado.
- **Aplicado en la instancia de `Test_Fluid` (guardado):** perla = AmoebaColor1 (0,966 0,977 1) · AmoebaColor2 (0,342 0,448 0,674) ·
  ShadowColor (0,033 0,051 0,095, a 0,45) · OuterColor (0,711 0,787 0,933) · MembraneColor (0,86 0,9 1, a 0,06) · DustColor
  (0,848 0,89 1) · **OuterOpacity 0,01** + default de material **`OuterLook` = (0,06 0,035 0,55 0,95)** (reflejo 0,35 → 0,06, alfa
  del borde 0,25 → 0,035; afecta a todos los niveles). Beltrán: *"más translúcida, que apenas se note"*. Antes 0,03 (Beltrán: *"esa contenedora más translúcida"*; sobre el agua TINTA cualquier luz lineal
  chica se ve fuerte por la codificación sRGB: con 0,09 la envoltura sumaba todavía ~+75 niveles; con ≤ 0,05 la dibuja el borde). Default de material **`OuterSh` = (0,147 0,196 0,296, a 0,6)**
  en `M_LovingOuter_SC` (antes violeta; afecta a todos los niveles). Valores sRGB de partida en `Saved/ClaudeScripts/Fluid/paletas.json`.
- **Envoltura circular (CDO + instancia, guardado):** `OuterSoftness` 0,8 → **1,0** · `OuterWobble` 1 → **0,2** · `EnvelopeHug`
  0,8 → **0** · `OuterBody` 8 → **60** (barrido mostrado: 30 aún con muesca, 45 canto rodado, 60 casi esfera). Solo agrega
  material: la contención verificada sigue valiendo. Costo: la envoltura cubre más pantalla (relleno translúcido), a medir en F6.
- ⬜ Propuesta estética completa (Turrell × Six N. Five) en curso (workflow); ⬜ CDO de colores (hoy solo la instancia).

## 🟢 V4c (2026-09-28, noche) — LUZ DEL AGUA (F5 del fluido): las cáusticas del fluido sobre la célula
Pedido de Beltrán: *"¿la cáustica está puesta?"* (en las amebas medias del fluido casi no se leía). Diseño elegido por un
workflow (2 diseños independientes + juez, todo verificado sin editor): **diseño A** con injertos del B.
- **Qué hace:** la MISMA red de cáusticas que las células medias del fluido (`Caustic`, copia literal de `FluidLib`: el
  portón `check_loving_hlsl.py` FALLA si se separan), mismo tamaño (`Caus.y`), misma fase (`Phase.y` en juego, `T × Caus.z`
  en el editor), anclada al MUNDO (`WorldPosition` del píxel: la célula flota por debajo de la luz) y solo en lo que mira
  hacia arriba. Sobre núcleo, bolas y envoltura. Se suma con **`WaterGain`**: comprime el aumento contra el margen del canal
  mayor (sin tonemapper `c(1+x)` quemaba a blanco arriba del núcleo): tono exacto, canal mayor < 1, sin meseta.
- **Perillas (categoría `8-Agua`, viajan en `LV5.z`/`LV5.w`, que `PushGlobals` ya empujaba):** `WaterLight` (default **0** =
  apagada, el píxel aprobado BIT A BIT — DXIL idéntico, verificado plegada y como uniform; **SIEMPRE 0 en niveles sin
  fluido**; 1 = la cantidad de las medias; 0-3) · `WaterLightShell` (default 1: la parte que cae en la envoltura; 0 = solo
  núcleo y bolas). `Test_Fluid`: 1 / 1.
- **Editor (aplicado y guardado):** `M_LovingCentre_SC` + VectorParameter `LV5` (default del de las bolas), CP `Caus`/`Phase`
  de `MPC_Fluid_SC`, `WorldPosition`, PS con 12 entradas · `M_LovingBalls_SC` + CP + `WorldPosition`, PS 18 · `M_LovingOuter_SC`
  + CP + `WorldPosition` (usa su `LV5`), PS 10. BP: 2 variables + 2 getters al `MakeColor` de `LifeExtra` (cirugía; espejo en
  `scripts/loving_life_phase3.dsl`). Compila con `warnings_as_errors`.
- **Verificado en el editor:** neutralidad visual con la perilla en 0 (solo difiere la animación); A/B ajustado 0 → 3 → 0:
  bandas SOLO positivas en la parte de arriba de envoltura, núcleo y bolas (+1,45 de media contra −0,5 del control); la red se
  lee como 2-3 bandas anchas sobre la célula (líneas de 6-11 cm, separadas 35-106 cm). Con 1 es SUTIL (la célula ya está cerca
  del tope y `WaterGain` no deja quemar); con 2-3 se lee.
- ⚠ **Dependencia nueva:** los 3 materiales referencian `MPC_Fluid_SC` (llevarla al trasplantar; `docs/MECANICAS-PORTABLES.md` §4.10).
- ⚠ **Precisión:** núcleo y envoltura reciben la fase en half: en juego la red avanza a saltos de ~19 Hz (≤ 2,5 niveles en lo
  oscuro). Si se nota en el visor: que `BP_FluidMedium_SC` envuelva `CausticPhase` en [−10π, 10π) (salto a la mitad). Las bolas
  (full) no tienen esto.
- ⬜ **Decisiones de Beltrán (mirando en `Test_Fluid`):** intensidad (`WaterLight` 1 sutil / 2-3 se lee) · ¿también en la envoltura?
  (`WaterLightShell` 1/0) · tamaño de la red (bajar `CausticScale` del fluido afina también la de las medias) · ¿la célula se tiñe
  hacia el azul del medio como las amebas (absorción ~16-18 % a 1,7 m; diseñada, en espera) o conserva su color? · las medias
  queman a blanco arriba (`c(1+x)`): ¿más suaves como la célula?
- ⬜ Control de la fase por MPC en PIE: con `CausticSpeed` del fluido en 0 la red de la célula tiene que congelarse (gotcha 416).

## 🟢 V4b (2026-09-28, tarde) — AMEBA de verdad + volumen como el metaball (aplicado, guardado, en `Test_Fluid`)
Pedidos de Beltrán mirando la célula dentro del fluido: *"la esfera del centro y las de los grupos se ven muy esfera, les falta
un material con sombreado como el del Metaball o el gusano del secuenciador, se ven muy planas"* · *"le falta deformación a la
esfera central. Está como una pelota. Debería ser como una ameba"*.
**Diagnóstico (medido en la captura):** el modelo de luz YA era el del secuenciador (`SeqShade`); lo que aplanaba era (1) la luz
casi cenital `(−0,15 0,30 0,94)`: vista de frente, la cara que mira al usuario queda toda en el mismo tono; (2) la envoltura
exterior con alfa 0,5 encima de todo (sort 40) comía la mitad del contraste; (3) luz y sombra de tonos parecidos
(bolas: rgb 127-201 en todo el disco).
| Cambio | Dónde |
|---|---|
| `LightDir` = **(−0,551 −0,401 0,732)** en MUNDO: arriba-izquierda-adelante vista desde el usuario (mira +X) | default del parámetro en `M_LovingCentre_SC`, `M_LovingBalls_SC`, `M_LovingOuter_SC` |
| `AmoebaColor1` (luz) = (0,97 0,95 1,0) · `AmoebaColor2` (sombra) = (0,42 0,36 0,85): los colores del metaball | CDO + instancia de `Test_Fluid` |
| `BallContrast` 0,444 → **0,6** (`CoreContrast` sigue 0,70) · `OuterOpacity` 0,5 → **0,32** | CDO + instancia |
| **Ameba**: `CoreWob` A = `min(0,75·NA·(1+0,4Ag)·lerp(1;0,5;Calm), 0,85)` (antes 0,26, sin tope). Elegida mirando 0,5 / 0,75 / 1,0 en el editor: 0,5 se leía "huevo"; 0,75 trilobulada. r_max/r_min mediana 1,13 → **2,27**. El TOPE lo pone la curvatura (radios mínimos medidos ×Rc: A 0,75 → convexo 0,28 / cóncavo 0,12; 0,85 → 0,25 / 0,09; 1,05 → 0,21 / 0,06 = un pliegue de 1 cm) | `LovingLib.ush` (`CoreWob`, `Shape.WobA`) → 8 Custom reinyectados |
| BP: `LifeStep` → `RMin` literal 0,26 → **0,75** (`K2Node_CallFunction_132`, `MakeLiteralFloat`; sin el tope: queda CONSERVADOR, los grupos nunca más cerca de lo debido) | BP · `scripts/loving_life_phase1.dsl` |
| **Ancla del ensanche**: con lóbulos de +75 % la curvatura convexa supera a la de la esfera `rAx` y el borde de la hebra asomaba 0,6-1,0 cm (criterio 0,25). Descenso de segundo orden con PISO: `rEnd·max(rEnd/rAx, 2,7·A·rEnd/Rc)`; `OuterEnv` (`Win.x`) usa el mismo piso sobre su mínimo | `ArmSetup`, `OuterEnv` · espejo `loving_outer/lvport.py` |
**Verificación (Python sobre los ports literales, con las constantes nuevas):** `verify_flare.py` TODO OK (pared máx 0,08 cm;
control sin inclinar 3,3-4,9 cm) · `verify_outer.py` EXIT 0 (300 configuraciones: nada afuera; hueco menos margen núcleo
0,07 · brazo 1,27 · bolas 2,15 · polvo 0,81 cm) · `verify_amoeba.py` TODO OK: cotas certificadas intactas (la forma normalizada no cambió), `RMin` del BP conservador,
umbrales de curvatura **relajados a propósito** con criterio de malla: punta ≥ 0,2 Rc (5 aristas) · valle ≥ 0,076 Rc
(2 aristas de la icoesfera de 10242; medido 0,0896 Rc = 1,43 cm). Estudio del piso: `h` (altura normalizada del eje) no
alcanzaba (la pared máxima no está en las puntas); piso fijo 2,0 → 0,04 cm; proporcional a A → 0,08 cm.
**Capturas:** `VR_Test/Saved/ClaudeScripts/Fluid/shots/celula_antes_ahora.png`, `lv_close.png`, `lv_g1.png` (la final).
⚠ Visto de pasada, NO cambiado: la envoltura exterior tiene un pliegue marcado donde se juntan dos lóbulos (arriba al centro
en las capturas); ya estaba en V4.
⬜ juicio de Beltrán · ⬜ visor · ⬜ medir (la amplitud no cambia el costo: las mismas cuentas).

## 🟡 V4 (2026-09-28) — núcleo más ameba, hebras suaves, ameba translúcida EXTERIOR, sombreado del secuenciador
Pedidos de Beltrán mirando V3: *"que la ameba central sea más ameba, con un poco más de deformación, menos esfera"* ·
*"evitaría que las ondulaciones de las tiras sean tan pequeñas, que sean más suaves"* · *"envuelve toda la célula en una
ameba translúcida también, con deformación. Bastante opacidad"* · *"siempre pensando que corra en un APK"* · *"esa sombra de
la ameba del grupo es media rara. Debe ser como las que ya habíamos construido en el mesh del sequencer"*.
**Estado: 🟢 código integrado en el repo (`LovingLib.ush` + wrappers), compila (DXC → DXIL: TODO COMPILA; `glslc` del NDK →
SPIR-V validado) y verificado en Python · 🟢 **revisión adversarial aplicada** (3 lentes, ver abajo) · 🟢 **APLICADO EN EL EDITOR
(2026-09-28)**: 7 materiales (incluido el nuevo `M_LovingOuter_SC`), componente `OuterShell`, variables, `PushOuter`, `PushLook`,
literales de `RMin` (0,26 / 0,5); compila con `warnings_as_errors`, log sin errores, todo guardado; capturas en
`VR_Test/Saved/ClaudeScripts/Loving/v4/` · ⬜ juicio de Beltrán · ⬜ visor · ⬜ medir.** Se diseñó en 4 frentes en
paralelo y se integró con un merge a 3 vías bloque por bloque.

### Aplicado en el editor (2026-09-28) — lo que no estaba en el plan
- **Fondo = GRADIENTE, no Ganzfeld fluido** (Beltrán: *"ya se probó que el ganzfield pesa mucho en quest"*): la instancia
  `Loving_Ganzfeld` de `Test_Loving` pasó a `ShellMaterial = M_GanzSolid_SC` + `Mesh = SM_GanzShell` (9k tris). Colores en la
  instancia (`ColorTop`/`ColorBottom`). El BP del Ganzfeld no se tocó (lo usan Entering y la galería).
- **Perillas de COLOR** (Beltrán: *"color 1 y 2 de ameba, color de malla, color de partículas, etc."*), categoría `7-Color`:
  `AmoebaColor1` → `ShadeHigh` (luz; alfa = brillo, rgb×alfa ≤ 1) · `AmoebaColor2` → `ShadeLow` (sombra; su alfa lo pone
  `CoreContrast` 0,70 en el núcleo y `BallContrast` 0,444 en las bolas) · `ShadowColor` → `ShadowFill` (alfa = tinte 0,52) ·
  `MembraneColor` → `FilmCol` (alfa = densidad 0,06) · `MembraneRim` → `FilmRim` en membrana del núcleo, brazos y puentes.
  `DustColor` (5-Particulas) y `OuterColor` (6-Envoltura) ya existían. Las empuja **`PushLook`** (75 asignaciones), que corre
  al final del **Construction Script y de BeginPlay** (no en Tick: se autoran en el editor y cambiar una perilla re-corre el CS).
  Verificado con control: `AmoebaColor1` rojo + `MembraneColor` verde → la captura sale roja/verde (restaurado).
- `PushLook` termina con `SetTranslucentSortPriority(OuterShell, 40)` + `SetBoundsScale(OuterShell, 5)` (red para instancias
  viejas; ver la trampa de abajo).
- 🔴 **La instancia colocada NO heredó la plantilla del componente nuevo `OuterShell`** (malla None, sort 0, bounds ×1: la envoltura
  no se veía) ni las variables nuevas (todas en 0 → envoltura apagada y colores negros). Arreglado escribiendo en la instancia:
  las 13 variables con los defaults del CDO, y en el componente la malla y **cada propiedad en su propia llamada**
  (`translucencySortPriority` y `boundsScale` juntas con `staticMesh` en un solo `set_properties` NO se aplicaron y el CS las
  restauraba; de a una, sí, y sobreviven al CS).
- ⚠ **El actor de la célula está en y = −67,5** (antes 0): lo movieron en el editor; no se tocó. Las cámaras de captura usan esa Y.
- En el viewport, con sort 40 la envoltura vela todo el interior (lectura de "gelatina"); con sort 0 las bolsas y hebras se
  veían nítidas encima. Si Beltrán prefiere lo segundo, es el `40` de `PushLook` y de la plantilla.

| Qué | Dónde |
|---|---|
| **Núcleo más ameba**: `CentreR` = 4 pseudópodos (`AmPod`: 2q¹⁰−q⁵, con cuello suave) de un lado + 2 masas anchas (`AmBody`: q⁶) del otro, en 3 PARES de alturas complementarias (cuando uno sale su pareja se retrae: nunca vuelve a la esfera); el marco gira 0,0503 rad/s (los pseudópodos derivan, ~2 min por vuelta). `CoreWob` cambia de semántica: `(A, WMIN, 0, 0)`, A = 0,26·NoiseAmount·(1+0,4 Ag)·lerp(1; 0,5; Calm), WMIN = −0,4374 (cota CERTIFICADA por ramificación y poda). r_max/r_min 1,13 → **1,35** (S = 0), 1,51 con Agitation, 1,16 en calma; radio de curvatura ≥ 0,39 Rc (sin picos ni pliegues). `ArmSetup`: `Rcm = Rc(1 + A·WMIN) + 0,3 gC` y el ancla del ensanche sobre la ameba REAL, **inclinada** con su pendiente (revisión: `AP2.xyz = gAx·rEnd/rAx`, `zCs(n) = AP5.x + AP2.xyz·n`, `AP5.x = CentreR(eje) − rEnd²/rAx + gC + 0,8 MoundH`; con el ancla fija asomaba un muñón de hasta 2,6 cm y con el ancla solo en el eje, 1,5 cm del lado que baja) | lib · scripts `loving_amoeba/`, `loving_outer/verify_flare.py` |
| 🔴 **BP, junto con el shader**: `LifeStep` → `SetRMin`: literal `0.0675` → `0.26` y `(1 − 0.4·Coh)` → `(1 − 0.5·Coh)` (solo ese 0,4). Sin esto, en calma los grupos pueden tocar los pseudópodos | BP · `loving_life_phase1.dsl` l.55 |
| **Hebras suaves**: `StrandCurl` v4 (misma firma): ventana sin²(π zt) (0 y pendiente 0 en las puntas) × UNA comba viajera k = π en un plano cercano al de la figura (sesgo por hebra ± deriva lenta, ≤ 0,8 rad) + arco lento perpendicular 0,55; amplitud 0,10·Lw; tempo `0,6·swr` (revisión: con 0,42 la hebra separada se movía a la mitad de la velocidad lateral de V3). Radio de curvatura mínimo 4,75 → **12,5 cm**, giro entre anillos del lienzo 25° → 10°. Partículas de la hebra: se DESLIZAN por el eje (±1,5·DustDrift) antes del curl, deriva 3D ×0,15, manga `rm + 0,35·off` (desvío rms 0,42 → 0,06 cm) | lib · `LovingDustVS` |
| **Ameba translúcida exterior** (`OuterShell`: `SM_LovingIco_SC` + `M_LovingOuter_SC`, sort 40, bounds ×5): forma radial cerrada `r(u) = [rB^p + Σ (w P e^{(u·q−1)/σ})^p]^{1/p}·(1 + Aw W)`. Cuerpo = membrana del núcleo EXACTA (+ margen + `OuterBody`) → sigue sola a la ameba V4; un pseudópodo gaussiano por grupo que contiene la bolsa (cota cerrada, sin `BallsLayout`) y la lente de la hebra con su curl (`CurlEnv`); unión por norma p (solo agrega material: sin picos); deformación POSITIVA (estiramiento por grupo + ondulación). Cero iteraciones, normal analítica por vértice. **UNA capa** (solo caras de frente): la pared de atrás duplicaría el relleno y lavaría la célula. PS `OuterFilm`: alfa de frente = `OuterOpacity`, sube sola en la silueta; tope por el canal mayor (sin tonemapper el borde llegaba a 1,25 y viraba a blanco) | lib (`CurlEnv`, `OuterEnv`, `OuterLobe`, `OuterWob`, `OuterFilm`) · `LovingOuterVS/PS` · BP (`PushOuter`, `loving_life_phase4.dsl`) · scripts `loving_outer/` |
| **Sombreado del secuenciador** (bolas Y núcleo): `SeqShade` = la cadena de `M_BlobOrb_SC` (half-lambert con contraste 0,444, bicolor, piso 0,036, relleno de sombra que SUMA con tinte 0,52; sin especular ni borde) reemplaza a `Clay`. Diagnóstico medido sobre la captura: el punto blanco era el Blinn^40 sumado sobre un albedo que ya pasaba de 1 (sin tonemapper: 44,5 % del núcleo recortado); la bola gris, el borde (1−N·V)³ + el ambiente; la fusión rara, el AO gris del pliegue y el borde encendido DENTRO del pliegue. La normal analítica por píxel de las bolas SE QUEDA (exacta; los 4 taps del secuenciador erran 0,7-1,9° en fp32 y hasta 8° en half): lo que se portó es el modelo de LUZ. `Balls3` arranca con la bola 0 (el centinela 1e5 era `inf` en half → NaN). Parámetros renombrados en los dos materiales: `ShadeHigh` (0,82 0,72 0,98 1) · `ShadeLow` (0,42 0,36 0,82 0,444; **el núcleo 0,70**: con 0,444 los pseudópodos solo se leían en la silueta) · `ShadowFill` (0,10 0,06 0,34 0,52) · `ShadeFloorRim` (0,036 0 2,5 0; variante suave: piso 0,20) · `ShadeAO` (0,20 1 0 0) · `LightDir` (−0,15 0,30 0,94) en MUNDO | lib · `LovingBallsPS`, `LovingCentrePS` · `M_LovingBalls_SC`, `M_LovingCentre_SC` |

Perillas nuevas `6-Envoltura` (instance editable): `OuterOpacity` 0,5 (**0 = componente oculto, costo cero: A/B exacto para medir**) ·
`OuterMargin` 3 cm · `OuterBody` 8 cm · `OuterSoftness` **0,8** (p 8 → 3; 0,8 = p 4. Revisión: con 16 → 4 y 0,65 era una estrella de muescas
en V) · `OuterWobble` 1 · `OuterColor` (0,62 0,52 0,86).
El BP empuja `OuterK = (OuterMargin + DustOffset + 1,8·DustDrift + 2·DustSize, OuterBody, OuterSoftness, OuterWobble)` (así la
nube de partículas también queda adentro) y `OuterCol = (OuterColor, OuterOpacity)`.

**Costo (corregido en la revisión; regla de conteo de Heart: op-eq por vértice y vista = 2·WPO + interpoladores, calibrada con
78.849 vértices × 4416 → 5,4 ms (3,8 ms en la medición baja); proxy, no medición):**
| Vértices por cuadro | V3 | V4 integrado | **V4 revisado** |
|---|---|---|---|
| 5 grupos | 3,84 ms (2,70) | 4,32 ms (3,04) | **4,14 ms (2,91)** |
| 10 grupos | 6,76 ms (4,76) | 7,38 ms (5,19) | **7,42 ms (5,22)** |

op-eq por vértice y vista (V3 → V4 revisado, con 5 grupos): `LovingCentreVS` 1200 → 1118 (10242 v) · `LovingCentreFilmVS` 2120 → 2187
(10242 v) · `LovingArmVS` 7687 → 8150 (3744 v × N; sin puentes) · `LovingDustVS` 2642 → 3064 (9600 v) · `LovingBallsVS` 3457 → 3429 ·
**`LovingOuterVS` 2694** (2562 v; 4179 con 10 grupos) ≈ 0,11 ms, ~⅓ de la membrana del núcleo (no ¼). Las ramas por grupo ausente
devuelven ~0,32 ms con 5 grupos; el ancla inclinada cuesta ~0,14 ms (gradiente de `CentreR` en el eje). **La célula sola ya es
0,8-1,4× el costo de vértices de Heart v2** (que midió 3,8-5,4 ms): el fluido del Ganzfeld (7,5-13 ms) no entra junto sin
`M_GanzSolid_SC`. Palanca mayor pendiente: el lienzo del brazo (104×36 = 55-64 % del costo; candidato 64×24, ⬜ ver silueta).
**Envoltura, píxeles** (rasterizada desde el asiento, FOV por ojo del Quest 3 aprox.; `OuterSoftness` 0,8): cubre **16,6 %** del ojo con los
defaults (máx. 18,5), 18,7 % a S = 0, **29,6 %** con 10 grupos a S = 0, **45-49 %** en los extremos (10 grupos, SV 1, curl 2, Agitation 1;
máx. 60). Siempre UNA capa (0 % de píxeles con 2). `OuterPS` ~140 op-eq/px → ~0,10-0,13 ms con defaults, ≤ 0,4 ms en el extremo.
(Las cifras anteriores, 8-12 % / 25 % y "¼ de la membrana", estaban cortas.) ⬜ Medir en visor (plan de A/B por componente).

**Verificación (2026-09-28, sin editor):** compose + `check_loving_hlsl.py` → TODO COMPILA (control negativo: un identificador
inventado en `LovingOuterVS` FALLA). Bloques integrados idénticos byte a byte a los verificados por cada frente, salvo los ajustes de integración de abajo.
`loving_amoeba/verify_amoeba.py` → TODO OK (gradiente vs diferencias finitas 2,9e-6, cotas certificadas, curvaturas, RMin del BP
≥ la excursión real). `loving_outer/verify_outer.py` sobre el port INTEGRADO (ameba V4 + ancla + curl v4 + partículas nuevas +
`Win.x` mínimo): 700 configuraciones al azar (400 + 300: estado, tiempo, Agitation, NoiseAmount 0-2, StrandCurl 0-2, SizeVariation 0-1, 1-10 grupos, perillas de la envoltura), con los vértices REALES del brazo y las 4 esquinas de cada partícula: **ningún punto afuera**; hueco menos el margen prometido ≥ 0,18 cm (núcleo) · 1,25 (brazo) · 1,94 (bolas) · 0,71 (partículas); error de cuerda de la malla de 2562 ≤ 1,0 cm; radio 18-179 cm (p95 del máximo 136). Controles del instrumento: lóbulos muy angostos o la cota de la bolsa a la mitad → asoman hebra, bolsa y partículas (−0,8 a −5,5 cm); con la cota vieja de `Win.x` (ancla fija en Rc) también cumple en 150 configuraciones (la corrección es la cota correcta, no el arreglo de un escape medido). Normal por vértice del núcleo con la ameba V4: error ≤ 0,13° → ≤ 0,15 niveles sRGB en `SeqShade`.
`SeqShade` nunca pasa de 0,98 (cota por construcción) y en half erra ≤ 0,5 niveles de 8 bits.

**Integración (decisiones que no estaban en ningún frente):**
- `OuterEnv` usa `Win.x` = zW0 **mínimo** = `rAm − rEm²/rAm + gC + 0,8 MoundH + kC + lam + 1` (`rAm = Rc(1 + A·WMIN)`, `rEm` = rEnd
  del grupo más grande posible; el descuento es el del ancla inclinada de la revisión): con el ancla del ensanche en la ameba real,
  zW0 varía por brazo; con el mínimo el tramo libre sale lo más largo (curl mayor) y la lente lo más cerca del núcleo.
- `CurlEnv` se deja en la cota de la v3 (0,140) con la v4 integrada (0,114): holgura 1,23×. Invariante anotado en los dos lados.
- `OuterFilm` con tope por el canal mayor (la lección del sombreado: sin tonemapper, recortar por canal vira a blanco).
- Componente `OuterShell` (no `Outer`: evita chocar con `GetOuter` de UObject en el DSL).
- `PushOuter` con un `Get(acopy)` por centroide (bind) en vez de tres.

### 🔎 Revisión adversarial de V4 (2026-09-28, 3 lentes: matemática, APK, intención) — aplicada en el repo
| Hallazgo | Resultado |
|---|---|
| 🔴 **alto** — `GroupScale` salía de `Hash` (caótico, ×43758). `LovingOuterVS` pasa el índice LITERAL (el compilador lo pliega en el host) y las bolsas lo evalúan en el GPU desde `GI.w`: diferían hasta 0,96 en GroupScale (SV 1) → partículas hasta 2,9 cm AFUERA con `OuterMargin` 0, bolsa −0,55 cm en 1 de 50 configuraciones | ✅ `GroupScale = 1 + SV·(1,2·frac(0,41421356·idx + 0,33) − 0,4)` (razón de plata): < 1e-6 entre doble/fp32/FMA/ulp, < 1,3e-3 en half (`loving_outer/check_groupscale.py`, con control del Hash viejo: 0,94). ⚠ Cambia QUÉ grupo es grande (5 grupos, SV 0,5: 1,00 · 1,25 · 0,90 · 1,14 · 1,39); antes cada GPU (PC / Quest) sorteaba distinto, ahora es el mismo patrón en todos lados. Correlación 0,21 con el `_g` del BP (el tamaño no queda atado al ritmo). `Hash` lleva un 🔴 de por qué no sirve para nada que deba coincidir entre plegado, GPU y BP |
| 🟡 **medio** — el ancla del ensanche solo miraba el EJE: el borde del cilindro (a rEnd) asomaba 1,1-1,5 cm del lado que baja; el comentario decía "siempre bajo la membrana" | ✅ ancla **inclinada**: `AP2.xyz = gAx·rEnd/rAx` (la normal del plano pasa a leerse de `LV4.xyz` en `ArmVS`/`DustVS`), `zCs(n) = AP5.x + AP2.xyz·n` en `ArmVS` y `ArmField3`, `AP5.x` − rEnd²/rAx, `ArmWindow` arranca después de \|AP2.xyz\|, `Win.x` con el descuento. Pared ≤ 0,11 cm con defaults (control con el ancla en el eje: 1,51), ≤ 0,21 con Agitation, 0,75 en NoiseAmount 2 + Agitation 1 (antes 3,66); el ensanche que queda en la unión ~0,84 del pleno. La propuesta de la revisión (bajarlo PAREJO por la pendiente) perdía más ensanche (0,72, mín. 0,36) al mismo costo (`loving_outer/verify_flare.py`, TODO OK) |
| (pedido de la misma lente: "revisar BallsVS ↔ BallsPS") — la disposición de las bolas se REHACE con el `Hash` caótico en `BallsPS` (normal por píxel), en el brazo y en las partículas (la envoltura de la bolsa): un mul+add fusionado (FMA) en una etapa o shader y separado en otro lo mueve hasta 0,67 para idx ≥ 4 → normal de otra bola (¿la "bola gris"?) o bolas que asoman de su bolsa | ✅ `precise` en `Hash` (NoContraction en SPIR-V: 45 decoraciones en `BallsVS` y en `BallsPS`): el mismo redondeo en todas las etapas; costo ~0. No se puede medir sin el visor; ⚠ la disposición de los grupos 4-9 puede verse distinta a las capturas de V3 en PC (entre PC y Quest ya no estaba garantizada) |
| bajo (latente) — una presencia fraccional achica el lóbulo pero no la bolsa (a M.w 0,5 la bolsa queda 30 cm afuera) | ✅ documentado 🔴 en la lib: presencia BINARIA; un fundido escala bolsa, brazo y lóbulo JUNTOS |
| 🔴 **alto** — la A/B de `OuterOpacity` solo ve ~⅓ del costo agregado de V4; cobertura y "¼" subestimados | ✅ cifras corregidas arriba; plan de A/B POR COMPONENTE (paso 14 del plan de editor); los compuestos de V3 quedan en `VR_Test/Saved/ClaudeScripts/Loving/composed_v3/` (local, no versionado) para reinyectar los VS y medir V3 contra V4 |
| 🟡 medio — los grupos ausentes pagaban trabajo completo en `Outer/Centre/CentreFilm/DustVS` | ✅ `[branch] if (Mk.w > 0.0)` (k = 1-9; uniforme por dibujo, sin arreglos), resultado idéntico; en `CentreFilmVS` una rama por slot hace abultamiento + candidato. SPIR-V: 9 ramas `DontFlatten` por shader |
| 🟡 medio — sort 40 vela las manos (translúcidas, sort 0) y el HUD (`M_HudWidget_SC`, sin depth test) donde se superponen con la célula | ⬜ **DIFERIDO**: el arreglo es subir a 100 la `TranslucencySortPriority` de las manos del pawn y del `WidgetComponent` del HUD (como `PtrSort` y la viñeta), pero vive en `Core/` (compartido) → coordinar con Beltrán. Check en visor en el paso 14 |
| bajo — núcleo sobre-teselado: pasar `Centre` a `SM_LovingIco_SC` | ⬜ **DIFERIDO a A/B de visor**: con el contraste 0,7 del núcleo el sombreado erraría p99 1,2 / máx. 3,6 niveles sRGB (10242: 0,3 / 1,5); ahorra ~0,14 ms. Cambio de malla, sin código |
| bajo — con los puentes apagados `ArmVS` igual corría 2 `BridgeSetup` + 2 `BridgeSDF` por vértice | ✅ `[branch] if (BPr.x + BPr.y > 0.0)`; `FilmPS` solo mira si `Misc.z` pasa de 1e3 → idéntico |
| 🟡 medio — la envoltura con `OuterSoftness` 0,65 (p 8,2) era una estrella de 5 brazos con muescas en V (radio 1,4 cm) y costuras que la icoesfera de 2562 no resuelve (hasta 7-9 px) | ✅ `p = lerp(8, 3, OuterSoftness)`, default **0,8 (p 4)**: muesca 5,3 cm (4,1 a S = 0), base del pseudópodo 15,5 cm; 1,0 (p 3) = 8,8 / 24,8 cm. Cobertura 15,5 → 16,6 %. Si la silueta se ve facetada: `SM_LovingCentre_SC` en `OuterShell` |
| 🟡 medio — el núcleo heredó el contraste 0,444 de las bolas: el relieve de los pseudópodos cae 40 % (rms de luma 0,047 → 0,028) | ✅ `ShadeLow.a` = **0,70 solo en `M_LovingCentre_SC`** (0,045 ≈ V3; sin especular: no vuelve el punto blanco) |
| bajo — hebras separadas a la MITAD de velocidad lateral que V3 (0,46 contra 0,92 cm/s) | ✅ tempo `0,42 → 0,6·swr` (el de la onda principal de V3): 0,64 cm/s; curvatura y `CurlEnv` sin cambios. Perilla de gusto: 0,42 = la versión más lenta |
| bajo — en calma los grupos quedan ~1,8 cm más lejos que en V3 (−9 % del acercamiento: 21,2 → 19,4 cm) | ⬜ **DIFERIDO (gusto)**: es el costo de la ameba más grande. Receta si molesta: `CoreWob` `lerp(1.0, 0.5, Calm)` → `lerp(1.0, 0.3, Calm)` y el literal del BP `(1 − 0,5·Coh)` → `(1 − 0,7·Coh)` en el MISMO lote (la ameba en calma queda más quieta) |
| bajo — V3 nunca se midió; solo había A/B de la envoltura | ✅ plan: A/B por componente + reinyección de los VS de V3 |

**Verificación de la revisión (2026-09-28, sin editor):** compose + `check_loving_hlsl.py` → TODO COMPILA; los 17 arneses también a
**SPIR-V** con `glslc` del NDK 27.2 + `spirv-val` (vulkan1.1): 17 ok (el camino del Quest que el DXC del SDK no cubre). Entre el integrado y
el revisado solo cambia `code` (entradas y salidas idénticas). `verify_outer.py` con el port revisado (GroupScale nuevo, ancla inclinada,
p 8 → 3, tempo 0,6): 400 (semilla 23) + 300 (semilla 7) configuraciones, **ningún punto afuera**; hueco menos el margen prometido ≥ 0,18 cm
(núcleo) · 1,40 (brazo) · 2,81 (bolas) · 0,71 (partículas); cuerda de la malla de 2562 ≤ 0,94 cm; radio 18-184 cm (p95 del máximo 137).
Controles: lóbulos muy angostos → brazo −3,75, partículas −2,94; cota de la bolsa a la mitad → bolas −1,01, brazo −4,59 (el instrumento
ve los escapes). `verify_amoeba.py` → TODO OK. `verify_flare.py` → TODO OK. `check_groupscale.py` → 5,6e-7.

⬜ Pendientes: aplicar el plan de editor FINAL (`VR_Test/Saved/ClaudeScripts/Loving/editor_plan_v4.txt`, local: 7 materiales, componente,
6 variables, `PushOuter` + empalme al final de `PushMore`, 2 literales de `RMin`) · juicio de Beltrán (cantidad de deformación: `NoiseAmount` o la constante 0,26; piso de la sombra
`ShadeFloorRim.x`; contraste del núcleo `ShadeLow.a` 0,70; opacidad, tamaño y suavidad de la envoltura; tempo del curl 0,6; el nuevo
reparto de tamaños por grupo) · visor: A/B POR COMPONENTE (paso 14 del plan) · manos y HUD sobre la envoltura (sort, `Core/`) · si la
silueta de la envoltura se ve facetada, `SM_LovingCentre_SC` en `OuterShell` (sin cambios de código) · A/B del núcleo en 2562.

## 🟢 V3 (2026-09-28) — sin puentes, hebras finas, hasta 10 grupos, sombreado 3D, partículas, entorno
Feedback de Beltrán sobre la propuesta: *"la forma al unirse es bastante fea… no hagamos esa unión… cuando no está
aparecen unos picos feos… lo que los une siga siendo delgado… separadas: más curl, más lejos, no simétricas… los
grupos dentro de cada bolsa deformándose, agrandándose y achicándose"* + perillas de cantidad de brazos y
*size variation* + *"entorno etéreo… sombreado para que se sienta 3D… partículas muy pequeñas que tomen la forma
de todo este CELL, como una segunda membrana"*. Capturas: `VR_Test/Saved/ClaudeScripts/Loving/v3/`.
| Qué | Dónde |
|---|---|
| **Puentes APAGADOS** por defecto: `bBridges` (2-Forma, false). `BridgeGate` al final de `Simulate` pone `BridgeP/Q/V/L/Tm` en 0 → brazos sin recorte, `CalmStep` sin freno de puente. Prenderlo vuelve al sistema anterior desde cero | BP |
| **Hebra fina en calma**: `Shape` con `rMid = CS·(0,3+0,3S)`, `kN`/`kC`/`lam` chicos, núcleo crece solo +12 %, `MoundH` 0,08 → sin cuellos gruesos ni picos | `LovingLib.ush` |
| **Curl de la hebra** (`ArmWindow` + `StrandCurl`, funciones compartidas brazo/partículas): onda viajera en 2 ejes con ventana `64·q³` (0 en las raíces → no mueve costuras), amplitud `0,12·L·StrandCurl`, cae 75 % con la calma | `LovingLib.ush`, `LovingArmVS` |
| **Bolas vivas**: cada bola respira con su propio ritmo (desfasadas al estar separadas, en fase con la respiración en calma), el grupo precesa y rota; la envoltura las sigue porque sale de las mismas bolas | `BallsLayout` |
| **Más vida separada**: `Tempo` lerp(1,4→0,7), `AmpS` lerp(1,5→0,55); vaivén radial 0,3·Lf, tangencial 0,12·gap, profundidad 8 cm; asimetría fija mayor (ángulo `2,8/N`, ±14 % de radio, ±14 cm de profundidad) | `LifeStep`, `LifeApply`, `GroupTarget` (pines) |
| **`DistSeparated` 72 / `DistConnected` 48** (CDO): en calma solo "se acercan un poco" | CDO |
| **Hasta 10 grupos**: componentes `Cluster/Arm/Bridge 6-9`; todos los `Clamp(1,6)`→10, `Resize 6`→10, `ForLoop 0-5`→0-9 (30 pines); `PushMore` (grupos 6-9 + `M6..M9`); `M6..M9` en `M_LovingCentre_SC` y `M_LovingCentreFilm_SC` (10 abultamientos) | BP + materiales |
| **`SizeVariation`** (2-Forma, 0,5): `GroupScale(idx) = 1 + SV·(1,2·Hash(idx+0,93) − 0,4)` → 0,6×…1,8× con SV = 1. Viaja en `LV5.x`; `LifeExtra` agranda `RMin` con el grupo MÁS grande posible (+0,8·SV) y recalcula `RShift` con la misma fórmula | lib + `LifeExtra` |
| **`StrandCurl`** (4-Vida, 1) → `LV5.y` | `LifeExtra` |
| **Sombreado 3D** (`Clay` reescrita): wrap-diffuse suavizado + ambiente de 2 tonos + tinte de terminador (subsuperficie) + especular Blinn + borde. Defaults nuevos en `ClayAlb/Sky/Gnd/Side/Term` + `LightDir` de `M_LovingBalls_SC` y `M_LovingCentre_SC`. Bolas en `MFPM_Full_MaterialExpressionOnly` (el PS rehace la disposición: tiene que coincidir con el VS) | lib + materiales |
| **Segunda membrana de partículas** (`Dust`): ver abajo | `SM_LovingDust_SC` + `M_LovingDust_SC` |
| **Entorno**: instancia `Loving_Ganzfeld` de `BP_Ganzfeld_SC` en `Test_Loving` (0,0,120), fluido, `WaveShade 0` + `WaveAmount 0` (el relieve cuesta ~10 ms), pastel `ColorTop (0,30 0,36 0,95)` · `Mid (0,95 0,45 0,72)` · `Bottom (0,20 0,70 0,78)`, `Brightness 0,5`, `VeilAmount 0,25`. 🔴 El fluido son 3 simplex 4D a pantalla completa (~13 ms medidos en la galería): si no entra en presupuesto con la célula, `ShellMaterial = M_GanzSolid_SC` (degradado liso, casi gratis) | nivel |
Perillas nuevas: `5-Particulas`: `DustOpacity` 0,55 (0 = apagada) · `DustSize` 0,35 cm · `DustDrift` 0,6 cm · `DustOffset` 2 cm · `DustColor`.

### Las partículas: nube de sprites posicionada en el VERTEX SHADER (no Niagara)
`SM_LovingDust_SC` = 2400 quads de 0,4 cm (9600 vértices) con sus números al azar en las UV: UV0 = esquina, UV1 =
dirección en la esfera, UV2 = (a qué parte va, fase/tamaño). `LovingDustVS` calcula el CENTRO de cada partícula con
la MISMA librería que dibuja la célula: 34 % sobre la membrana del núcleo (ameba + 10 abultamientos + hueco), el resto
por grupo PRESENTE (índice entre los `Np` presentes, cadena de selects): 62 % sobre la envoltura (`RayExit` contra las
bolas infladas) y 38 % a lo largo de la hebra con el MISMO `StrandCurl`; si la hebra es corta (calma) van a la
envoltura (si no, se amontonan en el cuello). Deriva propia + titileo; billboard hacia `CamL` (cámara en espacio
local, `TransformPosition` World→Local). PS: punto suave premultiplicado (AlphaComposite, two-sided), sort 30.
**Por qué no Niagara**: la forma es procedural y vive en el GPU; un Niagara tendría que recalcularla en la CPU o
duplicar la librería en su VM. Así sigue la forma exacta, un draw call, cero CPU. ⚠ Costo: cada vértice del quad
repite el cálculo del centro (×4) — 9600 VS pesados (`ArmSetup` + curl). Medir; si aprieta, bajar a 1200 quads.

### Trampas nuevas de esta tanda
- El getter de un bool `bX` en el DSL de ESCRITURA es **`Variables|<cat>|GetX`** (sin la `b`); la lectura lo muestra
  como `(|GetbX)`. `Variables|2-Forma|GetbBridges` no existe → el `write_graph_dsl` aborta (el grafo queda con su entry).
- `AssetTools.write_file` solo acepta `.csv .html .json .md .py .txt` (`.dsl` falla, y el script entero sale con error).
- `CaptureViewport` devuelve `image.data` + `mimeType`, sin `width`.
- Captura inmediatamente después de reinyectar un material: el material todavía compila (async) y **no se dibuja**
  (primera captura sin partículas). Recapturar o esperar.
- `generateOverlapEvents` no se puede setear sobre la plantilla del componente (warning, el resto sí se aplica).
- Literales del BP: son nodos `MakeLiteralFloat` (pin `Value`); un literal repetido (0,25 en `LifeApply` ×2) se
  distingue por la OTRA entrada de su consumidor.

## 🌱 VIDA — fase 1 (2026-09-27 noche). Plan completo: 4 fases (panel de diseño + crítica)
Pedido de Beltrán: *"muy viva: la esfera central flotando, cada grupo flotando, a veces se acercan y a veces
se alejan suave… una entidad viva, casi como células o conexiones neuronales; elegante"*. Principio: **el
movimiento grande vive en el BP** (relojes integrados, resortes; costo 0 en GPU; todas las piezas leen los
mismos centroides empujados → costuras exactas); **la micro-vida en el shader** (fases 3-4, a medir antes).
- **Relojes integrados** (nunca `Clock·Speed`, gotcha 329): `Tau += DT·Tempo`, `Tempo = OrganicMotion·lerp(1,2 → 0,7, c)·(1+0,4·AgS)`,
  `c = smoothstep(0,2, 0,9, S)`. Amplitud `AmpS = FloatAmount·lerp(1 → 0,55, c)·(1+0,35·AgS)`. `AgS` = Agitation suavizada.
- **`LifeWander(T,P,Seed)`**: 3 senos a razones 1 : √2 : √5 con pesos 1 : 0,8 : 0,6 (no se realinea nunca; con
  1 : 0,5 : 0,25 el fundamental se leía como vaivén periódico — crítica).
- **Núcleo flotante** `CoreC` = AmpS·(2, 4, 6) cm × LifeWander (períodos 23,7 / 17,9 / 11,3 s) → `LV0.xyz` (`LifeLV`).
- **Cada grupo** (`LifeApply`, después de `GroupTarget`): radio ±0,25·(tramo libre), pulso ±4,5 %, vaivén
  tangencial ±0,085·hueco con **límite suave** `x/√(1+(x/thm)²)`, profundidad ±5 cm; períodos ×k_i
  (k_i por secuencia áurea: ningún par en fase). **Piso suave de radio** contra `RMin` (núcleo CRECIDO + membrana
  + abultamiento + alcance de las bolas + 1 cm): la crítica midió 0,15 cm de holgura a S = 1 sin esto.
- **Resortes viscosos**: `ω_i = 1,25·(0,85+0,3·g_i)`, ζ = 0,72 (antes ω 1,8 fijo): el núcleo arrastra a los grupos
  ~1 s tarde. **Con calma el arrastre se vuelve rígido** (`Pos += CoreD·Kappa`, `Kappa = smoothstep(0,7, 0,95, S)`):
  sin movimiento relativo hacia adentro cuando la holgura es mínima.
- **Actitud** de toda la figura: yaw ±4°, pitch ±2,5°, roll ±6° (53/41/67 s) sobre los OBJETIVOS (los grupos la
  siguen por el resorte) y sobre el plano empujado `LV4` (`PlaneN`).
- **Orden de dibujo con histéresis** (`SortArm`): un brazo que se inclina hacia atrás se dibuja ANTES que la
  membrana del núcleo (prioridad 1+i) y vuelve (10+i) con histéresis −0,10/−0,05; solo al cambiar.
- **`PreviewTime`** (4-Vida): en el Construction Script la coreografía se posa en ese instante; Play arranca de esa pose.

### Variables nuevas
**4-Vida** (editables): `FloatAmount` (1; 0 = la pose estática de antes) · `PreviewTime` (0 s).
**Z-Interno**: `Tau` `AgS` `Tempo`(1) `AmpS`(1) `Coh`(0; la escribe la fase 2) `Kappa` `RMin` · `CoreC` `CoreD` `PlaneN`
(Vector) · `FigRot` (Rotator) · `SprW2`(3,24) `SprD`(2,88) · `LifeBooted` (bool) · `LifeP` `LifeGather` `LifeTurn` `ArmBack` (float[]).
`RShift` (corrimiento uniforme en calma). **Fase 2** (aplicada 2026-09-27): 4-Vida `Reach` (1) · Z-Interno `Psi` `PairA` `BridgeL` `BridgeTm` `BridgeV` `BridgeQ` (float[]) · `ScrL` `ScrTm` `ScrV` `ScrP` · `NPrev` (int). Funciones `CalmStep`, `BridgeStep` (DSL: `scripts/loving_life_phase2.dsl`); empalmes: LifeStep → **CalmStep** → ForLoop(StepGroup) · ForLoop(rampa vieja).Completed → **BridgeStep**.
### Funciones nuevas (grafos nuevos, escritos enteros) y empalmes (cirugía)
`LifeWander` · `LifeStep(DT,Snap)` · `LifeApply(Index)` · `LifeLV()` · `SortArm(Index,Arm)` · `SortArms()`.
Empalmes: `Simulate`: SetPhase → **LifeStep** → ForLoop(StepGroup) · `StepGroup`: GroupTarget → **LifeApply** →
SetArrayElem; los literales 3,24/2,88 → `SprW2`/`SprD` · `PushAll`: SetLV4 → **LifeLV** → PushGlobals(Centre).
El DSL fuente de las 6 funciones está versionado en `scripts/loving_life_phase1.dsl`.
### Verificación de la fase 1 (2026-09-27, simulación en Python del DSL + auditoría de trampas)
Porte línea a línea (con la semántica "bind no es asignación") de Simulate/StepGroup/GroupTarget + la vida,
72 Hz, 300 s por caso. ✅ 0 NaN (5 escenarios + 60 perillas al azar) · sin saltos entre cuadros · la pose del
Construction Script y la de BeginPlay coinciden EXACTO (PreviewTime 0/37/120) · `PlaneN` idéntico a (cos15,0,sin15)
con FloatAmount 0 · arrastre rígido en calma (ganancia 1,04) · holgura REAL bola↔membrana siempre > 0.
A S = 0: núcleo pico a pico 4/8/12 cm; grupos radial 19-27 cm, tangencial 18-25°, profundidad 13-15 cm;
velocidad máx. 7,9 cm/s. 🔴 3 defectos, corregidos en `scripts/loving_life_phase1.dsl` Y APLICADOS en el BP (las 4 funciones vaciadas y reescritas; compila sin advertencias; literales de las llamadas verificados):
1. El piso suave contra `RMin` (peor caso) FIJABA la pose en calma: a S = 1 los 5 grupos en un anillo de 39,5 cm,
   vaivén radial 0,3 cm. Y la pose VIEJA a S = 1 chocaba con la membrana (holgura −1,4 cm; −5 cm con Agitation).
   → **`RShift`**: corrimiento UNIFORME hacia afuera = max(0, RMin + 1 − 0,94·distancia nominal) (conserva la
   dispersión entre grupos; vaivén 2-3 cm) y `RMin` con la ondulación REAL (CoreWob con AgS y Coh), no el peor caso.
   FloatAmount 0 = la pose de antes SOLO para S ≤ 0,6; arriba se corre afuera (la de antes chocaba).
2. Prioridad "atrás" `1+Index` empataba con la membrana del núcleo (5) → **4 fijo**.
3. `SortArms` corría en LifeStep, ANTES de mover los grupos (en el editor, contra Pos = 0) → **al final de `LifeLV`**.
+ `GroupSize` negativo → NaN por Asin → acotado a 0,05.
⚠ En el editor, `ResetPropertiesForConstruction` pone en su default (CDO) TODAS las variables no editables
(Z-Interno) antes de cada Construction Script: `LifeBooted`, `ArmBack`, `Pos`… arrancan de cero en cada rerun.

### Fases siguientes (plan con la crítica aplicada)
- **Fase 2** (BP; la parte de shader YA está inyectada: `NeckBreath`, `Calm`, `BridgeSetup` alcanzar/cerrar):
  calma = sincronía (PLL de los pulsos a la respiración), llegada escalonada, puentes con MEMORIA (histéresis
  0,12 + 2,5 s) que primero ALCANZAN (dedos) y después cierran. 🔴 El integrador de los puentes necesita su
  PROPIO estado (`BridgeQ`): la rampa vieja pisa `BridgeP` cada cuadro (crítica).
- **Fase 3** (shader): bolas que ruedan dentro de la envoltura. **Fase 4**: hebras que se mecen + abultamientos
  que viajan. 🔴 Antes: medir la célula en el visor (lección de Heart: vértices).

## Por qué esta técnica (decisión con investigación, 2026-09-27)
Panel de investigación (4 frentes web + 3 arquitectos + juez adversarial). Veredicto:
**todo procedural por MALLA con vértices desplazados** ("enfoque C", la técnica del gusano del
secuenciador que corre a 72 Hz en el APK). Descartado con datos:
- **Raymarch** por píxel: medido 12,28 ms en esta obra; escala con la cobertura, y la figura es grande.
- **Niagara Fluids / Grid3D / Particle Surfacing** ("metaballs desde partículas"): compilan solo en SM5,
  nunca para `VULKAN_ES3_1_ANDROID`. Ribbons = look de cable, sin menisco.
- **Refracción / DepthFade / SceneColor**: no existen con `MobileHDR=False`. Todo es analítico.
- **Geometry Script / marching cubes** por cuadro: decenas-cientos de ms en la CPU del Quest.
- **VAT horneado** (OpenVAT): congela GroupCount/vecinos/cuellos. Beltrán eligió "todo procedural".

## Arquitectura: el BP integra el TIEMPO, la librería HLSL calcula la FORMA
- **BP** (este): suaviza el estado, fase de respiración, reloj, **resortes de los 6 centroides**,
  progreso de los puentes, y empuja **5 vectores globales + el centroide de cada grupo**.
- **HLSL** (`VR_Test/Shaders/Loving/LovingLib.ush`, fuente única): TODO lo demás es función pura
  del estado — radios, cuellos, filetes, la disposición de las bolas de cada grupo (desde su
  ÍNDICE), envolturas, puentes. Racimo, brazo y puente usan **la misma cuenta** → las costuras
  coinciden. Afinar el look = editar texto y reinyectar (sin cirugía de nodos).

### Los vectores que viajan (todos `LinearColor`, 4 canales, por `SetColorParameterValueOnMaterials`)
| Param | Contenido | Lo usan |
|---|---|---|
| `LV0` | (centro del núcleo, radio base `CentreRadius`) | todos |
| `LV1` | (**S** 0-1, fase de respiración [0,2π), Agitation, ColorTemp) | todos |
| `LV2` | (GroupSize, GroupSpread, CenterAttraction, ConnectionStrength) | todos |
| `LV3` | (MembraneThickness, MembraneOpacity, NoiseAmount, OrganicMotion) | todos |
| `LV4` | (normal del plano de la figura, EnvelopeHug) | todos |
| `GI` | (centroide del grupo, **índice entero** del grupo) | racimo, brazo |
| `GP`/`GN` | centroide + índice del vecino anterior / siguiente | brazo |
| `BPr` | brazo: (progreso puente prev, progreso puente next) · puente: (progreso) | brazo, puente |
| `GA`/`GB` | extremos del puente (centroide + índice) | puente |
| `M0..M5` | (centroide del grupo i, presencia 0/1) → abultamientos del núcleo | núcleo, membrana del núcleo |

🔴 El índice va en `.w` como ENTERO a propósito: el pixel shader recibe los inputs en `half`, y un
hash de una semilla fraccionaria daría otra disposición de bolas que el vertex shader.

## Componentes (33 StaticMesh desde V3: + `Cluster/Arm/Bridge 6-9` (sort 16-19 / 26-29) y `Dust` (SM_LovingDust_SC, bounds ×3, sort 30); todos en transform relativo IDENTIDAD)
> V4 (⬜ por aplicar): + `OuterShell` (SM_LovingIco_SC + `M_LovingOuter_SC`, sort 40, bounds ×5, sin sombra, `NoCollision` en la plantilla).
> 🔴 sort 40 queda por ENCIMA de las manos y del HUD (sort 0): subirlos a 100 en `Core/` (coordinar) — ver la revisión de V4.
> `Centre` sigue en SM_LovingCentre_SC (10242): pasarlo a SM_LovingIco_SC es un A/B de visor (ahorra ~0,14 ms; ver la revisión).
`Centre` (SM_LovingCentre_SC, bounds ×3) · `CentreFilm` (SM_LovingCentre_SC + `M_LovingCentreFilm_SC`,
bounds ×3, sort 5, colisión `NoCollision` en la PLANTILLA — no en el CS) · `Cluster0..5` (SM_LovingIco_SC, bounds ×5) ·
`Arm0..5` (SM_LovingLimb_SC, bounds ×3, sort 10-15) · `Bridge0..5` (SM_LovingWeb_SC, bounds ×3,
sort 20-25). Sombra apagada. Colisión `NoCollision` en el Construction Script.
🔴 **Identidad obligatoria**: el material usa `LocalPosition` = espacio del actor.

## Registro de variables
**1-Estado** (instance editable)
- `GlobalState` (0,3) — el estado autoral/EEG 0 = separado · 1 = conectado. Lo escribe la etapa.
- `bFakeSignal` (false) / `FakePeriod` (40 s) — señal de prueba `0,5−0,5·cos(2πt/T)` en vez de `GlobalState`.
- `StateSmoothing` (1,2) — velocidad del `FInterpTo` del estado (≈ respuesta de 1-2 s).
- `Agitation` (0) / `ColorTemp` (0) — capa B del EEG: más ruido y respiración más rápida / albedo más cálido.

**2-Forma**
- `GroupCount` (5, se recorta a 1-6) — grupos visibles; los puentes existen solo con ≥ 3.
- `GroupSize` (1) — radio de bola = 3,4 cm × GroupSize.
- `GroupSpread` (1) — multiplica la distancia núcleo-grupo.
- `CenterAttraction` (1) — cuánto se acercan, cuánto crece el núcleo, abultamientos y deformación hacia el centro.
- `ConnectionStrength` (1) — grosor literal de hebras y puentes.
- `CentreRadius` (16 cm) — radio base del núcleo (crece hasta +25 % conectado).
- `DistSeparated` (62) / `DistConnected` (34) — distancia de los grupos en los extremos.
- `FigureTilt` (15°) — inclinación del plano de la figura hacia atrás. **El +X del actor mira al usuario.**

**3-Membrana**: `MembraneThickness` (1, inflado de la envoltura) · `MembraneOpacity` (1, sigma de la
película) · `EnvelopeHug` (0,8; 0 = envoltura cápsula, 1 = sigue el contorno de las bolas).

**4-Vida**: `NoiseAmount` (1, deriva de los grupos + ameba del núcleo) · `OrganicMotion` (1, vaivén
de las bolas y velocidad de la ameba) · `PulseSpeed` (1, respiración de 7 s).

**Z-Interno**: `S` (estado suavizado) · `Phase` · `Clock` · `Pos`/`Vel` (6 vectores, resortes) ·
`BridgeP` (6 floats). **Default** (internas): `Tgt` (salida de `GroupTarget`) · `LV0..LV4`.

## Grafos (orden del pipeline)
- **Construction Script**: `SetCollisionEnabled(NoCollision)` ×19 → `Simulate(DT 0, Snap true)` → `PushAll`.
- **BeginPlay**: `Simulate(0, true)` → `PushAll`. **Tick**: `Simulate(DeltaSeconds, false)` → `PushAll`.
- `Simulate(DT, Snap)`: resize de arrays a 6 · dt ≤ 0,05 · `Clock += dt` · `S` = estado (snap) o
  `FInterpTo` · `Phase` integrada (nunca `Time·Speed`) · `StepGroup(i)` ×6 · `BridgeP[b] =
  MapRangeClamped(S, 0,54+0,04b, 0,74+0,04b)` (los puentes nacen de a uno entre S≈0,55 y 0,95).
- `StepGroup(Index, DT, Snap)`: `GroupTarget` → resorte `ω² = 3,24`, `2ζω = 2,88` (Euler simpléctico)
  o salto directo al objetivo si `Snap`.
- `GroupTarget(Index)` → `Tgt`: ángulo `π/2 + 2πi/N` + asimetría por hash · distancia
  `lerp(DistSeparated, DistConnected·(1,15−0,15·CA), smoothstep(S/0,8))·Spread·(±6 %)` · profundidad
  ±10 cm · ruido lento (3 senos) de amplitud `Noise·OM·(0,6+0,8·Agit)·1,5·(1−0,5S)`.
- `PushAll`: arma `LV0..LV4` → `PushGlobals(Centre)` → `M0..M5` → `PushGroup` ×6 → `PushCentreFilm`.
- `PushCentreFilm()`: `PushGlobals(CentreFilm)` + los mismos `M0..M5` que el núcleo.
- `PushGroup(Index, Cluster, Arm, Bridge)`: `PushGlobals` ×3 · `GI/GP/GN/BPr/GA/GB` · visibilidad
  (grupo visible si `i < N`; puente si además `N ≥ 3` y progreso > 0,002).
- `PushGlobals(Comp)`: los 5 `LV`.

## Materiales (todos Unlit; HLSL inyectado desde el repo)
| Material | Blend | VS | PS | Normal |
|---|---|---|---|---|
| `M_LovingCentre_SC` | Opaque | ameba cerrada + 6 abultamientos, 0 iteraciones | arcilla | analítica **por vértice** (10k verts) |
| `M_LovingBalls_SC` | Opaque | bisección radial (6 + secante) sobre el smin de 2-3 bolas | arcilla + pliegue AO | analítica **por píxel**, UNA evaluación |
| `M_LovingArm_SC` | **AlphaComposite** | brazo: tubo con zonas hebra/cuello/tapa, bisección (7 + secante) sobre el campo sin pliegues | película | 4 taps del campo 3D, por vértice |
| `M_LovingBridge_SC` | AlphaComposite | puente de forma cerrada (reloj de arena con cintura con signo) | película | superficie de revolución |
| `M_LovingCentreFilm_SC` | AlphaComposite | la MISMA ameba del núcleo + abultamientos, inflada `CentreGap`; forma cerrada | película | analítica por vértice |
| `M_LovingOuter_SC` (V4, ⬜ por aplicar) | AlphaComposite, **una cara** | envoltura exterior: cuerpo (membrana del núcleo + margen) ∪ un pseudópodo gaussiano por grupo (norma p) × ondulación positiva; forma cerrada | `OuterFilm` (dos tonos + Schlick + borde, tope de canal) | analítica por vértice |

- **Arcilla** (V3; en V4 la reemplaza `SeqShade`, ver la sección V4): half-lambert AL CUADRADO + cubo ambiente de 3 colores + tinte del terminador + brillo rasante.
  Colores en los parámetros `ClayAlb/Sky/Gnd/Side/Term` + `LightDir` (mundo) de cada material.
- **Película**: opacidad Beer-Lambert racional sobre el camino por la cáscara (clara de frente, visible
  en la silueta, más densa en las junturas) + Schlick + reflejo analítico + borde geométrico + línea de
  Plateau/menisco + dither R2. Parámetros `FilmCol/K/Sky/Gnd/Rim/Fade` (defaults del material).
- **Sin pliegues** (prueba del juez): cada primitiva del brazo es monótona sobre su rayo o convexa y
  contiene el origen. Se rompe con pesos fraccionarios: apagar una primitiva achicando radio Y k.
- **Recorte mutuo brazo↔puente**: cada película evalúa el sólido exacto del otro y se apaga adentro
  → una sola capa en las uniones, sin doble opacidad.
- **Revisión adversarial 2026-09-27 (12 hallazgos, 0 refutados) — aplicada:**
  - La membrana del núcleo recorta contra el **`ArmField3` del grupo presente más cercano** (cadena de selects,
    sin arreglos), no contra una raíz simplificada: a S ≥ 0,55 el hueco quedaba hasta 2 cm chico (doble capa +
    dos líneas de Plateau). `ArmRootField` se borró. Entrada nueva `LV4` en `M_LovingCentreFilm_SC`.
    Su densidad de juntura `Misc.x` = la `J` del brazo en ese punto (antes una constante 0,6: salto de densidad).
  - Los **puentes** calculan su distancia con signo a la membrana del núcleo (`Misc2.x`) y se apagan adentro: a S = 1
    se hundían hasta 6 cm (2 cm dentro del núcleo opaco).
  - El `dC` del brazo suma los abultamientos de sus **dos vecinos** (con 6 grupos erraba hasta 1,5 cm).
  - **La fase de la ameba ya no depende de datos vivos**: velocidades FIJAS en `CoreWob`; Agitation, NoiseAmount y la
    calma van a la AMPLITUD. La ondulación se arma DENTRO de `CentreR` (una sola fuente para núcleo, membrana,
    brazo y puente). `Rcm` usa la MISMA amplitud (margen bajo la membrana incondicional).
  - PS de película: la línea de contacto `pb` va × `keepC` (collar brillante adentro; costura 1,5× más brillante).
  - Puente: el muñón nace desde radio 0 (`rE × smoothstep(0, 0,15, p)`) y un solo umbral (0,002 = el del BP).
  - `FilmFade.x` = 0,5 en brazo y puente (relevo simétrico), `FilmFade.w` = 0,5 en la membrana del núcleo.
- **Membrana del núcleo** (`CentreGap` = Rc·(0,12+0,06S)·max(MembraneThickness,0,3), respira con la fase):
  la esfera de raíz de cada brazo pasa a `Rcm = Rc·(1−1,35·WobA) + 0,3·gC` (justo DEBAJO de la membrana),
  así el filete del brazo la cruza. Recorte mutuo: la membrana del núcleo se apaga dentro de la raíz de
  cada brazo (`ArmRootField`, `Misc.z`) y la del brazo se apaga dentro de la del núcleo (`AP6.x = Rc + gC`,
  `Misc2.x`). Línea de Plateau en la unión. El núcleo opaco flota adentro.

## Cómo iterar el look (sin tocar el BP)
0. 🆕 **Compositor con dependencias**: `compose_loving.py` cierra transitivamente `@uses` y ordena
   topológicamente (cada función DESPUÉS de las que llama); avisa lo que agrega. **Chequeo sin editor**:
   `python .claude/skills/unreal-vr/scripts/check_loving_hlsl.py` envuelve cada Custom como Unreal (entradas,
   salidas `inout`, `ResolvedView`, `Parameters.SvPosition`) y compila con el DXC del Windows SDK (DXIL; los PS
   también con entradas en half). Control positivo hecho (un identificador inventado → FAIL). SPIR-V: ese DXC no lo trae.
1. Editar `VR_Test/Shaders/Loving/LovingLib.ush` o un wrapper de `VR_Test/Shaders/Loving/wrappers/`.
2. `python .claude/skills/unreal-vr/scripts/compose_loving.py` → `VR_Test/Saved/ClaudeScripts/Loving/composed/<Custom>.values.json`.
3. `ObjectTools.set_properties` del `MaterialExpressionCustom` con ese string (si cambian `inputs`
   o `additionalOutputs`: **vaciar el array y cargarlo en una segunda llamada**) → `recompile`.
Nodos: en cada material `Custom_0` = VS, `Custom_1` = PS.

## 🔴 Trampas de esta construcción
- **`get_node_type_pins` CREA nodos temporales** en el grafo que le pasás (los borra, pero deja el BP *dirty*).
  Pasarle un grafo que no importe. Y **vaciar las `inputs` de un Custom dispara una compilación en segundo plano
  que falla** (identificadores sin declarar) hasta que se recargan: es transitorio, pero OTRA sesión lo ve en el
  log — avisar antes.
- **La línea de Plateau contra el núcleo va con `abs(dC)`, no `max(dC,0)`.** Con la membrana del núcleo,
  la raíz del brazo asoma entre el núcleo opaco y esa membrana; con `max` todo ese tramo valía `pb = 1` y
  se veía un parche blanco sobre el núcleo (capturado y corregido).
- **Un componente agregado por MCP tampoco aparece en el preview del BP** (mismo mecanismo que el CS de
  abajo). Probado con control: película en rojo sólido y hasta con la malla sin deformar → 0 píxeles rojos.
  **Cerrar y reabrir la pestaña del BP lo arregla** (lo hizo Beltrán; por MCP no se puede).
- **Unión brazo ↔ membrana del núcleo**: el `dC` del brazo usa la ameba EXACTA (`CentreR` con su ondulación,
  `AP6.w = Rc`) y `keepC` es SIMÉTRICO (`smoothstep(-x, x, dC)`, `FilmFade.x` = 0,5 en el brazo; 0,5 también
  en `FilmFade.w` de la membrana del núcleo) → los dos se pasan el relevo en el mismo punto. Con el fundido
  viejo (0 → 2 cm, sin ondulación) quedaba una franja medio vacía de hasta 2 cm. Para ver una película sola: poner defaults realistas en SUS parámetros y `CaptureAssetImage`
  del material (se ve chica, 256 px: recortar y ampliar). `M_LovingCentreFilm_SC` quedó con esos defaults
  (S 0,3, 5 grupos a 53 cm en el plano YZ); en juego el BP los pisa todos.
- **El viewport del editor del BP NO re-corre el Construction Script tras un `compile_blueprint` por
  MCP**: el barrido 0 / 0,55 / 0,75 / 1 salió idéntico a la primera apertura (S = 0,3). Para ver
  estados hay que usar una **instancia colocada** (escribir su variable SÍ re-corre el CS) o reabrir el editor.
- `read_graph_dsl` rotula mi función `Simulate` como `ProceduralFoliageSimulation|Simulate` (colisión de
  nombres) — los pines (`DT`, `Snap`) prueban que es la propia. Verificar con `get_node_infos` antes de "arreglar".
- Con PIE corriendo (de OTRO agente), `save_assets` responde **"Asset does not exist"** para todo: no es
  pérdida, es el bloqueo del EditorAssetLibrary en PIE. Guardar al terminar el PIE. No compilar con PIE vivo.
- `CaptureAssetImage` no soporta Blueprints; `CaptureEditorImage` saca todas las ventanas (1280 px de ancho total).

## Lecciones de Heart que aplican acá (`BP_HeartScape_SC.md`, gotcha 454 de Heart — leído 2026-09-27)
- 🔴🔴 **Riesgo de costo de VÉRTICES.** La membrana del latido (79k vértices, trigonometría por vértice) costaba
  **5,4 ms solo en vértices** en la Quest: el VS corre **por ojo** (multiview) y el binning vuelve a ejecutar la
  posición; y **un Custom conectado al WPO y a `VertexInterpolator` se ejecuta DOS veces** (Unreal los compila en
  funciones separadas). La célula tiene **~69k vértices** (núcleo 10.242 + membrana 10.242 + 6×2.562 + 6×3.744 +
  6×1.792) con un VS MUCHO más pesado por vértice (brazo: 9 evaluaciones del rayo + 4 taps del campo). **Medir en
  el visor ANTES de sumar vida al shader**, con un `PerfMode` de "vértices baratos" (receta de Heart).
- Lo que a Heart SÍ le rindió: **densidad donde se ve** (−59 % de vértices) y **cortar trabajo dentro del VS**.
  Candidatos acá: núcleo y membrana 10.242 → 2.562; brazos 104×36 → ~64×24; bolas 2.562 → 642 (su normal es por
  píxel). Lo que NO rindió solo: separar el Custom por salida.
- 💡 **El look que se ve "rico"**: sombreado mate de dos tonos con *wrap* (`lerp(Sombra, Luz, lerp(Piso, 1, wrap))`),
  **núcleo luminoso de frente** (`pow(N·V, 2,2)`) + borde (`pow(1−N·V, 2,5)`) que laten con el pulso, y la esfera
  **como luz** sobre lo cercano. Para la célula: el núcleo con luz interior que respira e ilumina las raíces de
  los brazos (el `dC` del brazo ya es esa distancia: gratis en el PS).
- 💡 **"La instancia anima sola" en el editor** (reloj de preview en el material, `Live` = 0): la vida de la
  figura puede ir en el SHADER como función cerrada del tiempo (una `Drift(índice, T)` de la librería aplicada en
  TODOS los materiales que usan un centroide) → se ve viva en el viewport sin Play, que es como autora Beltrán.

## Nivel de prueba `/Game/Test_Loving` (2026-09-28, pedido de Beltrán: "crea un nivel y me muestras la propuesta")
Copia de `Test_Heart` (GameMode VR + PlayerStart en el origen mirando a +X) sin `BP_HeartScape_SC`. La célula en
**(170, 0, 115), yaw 180** (su +X mira al usuario sentado; 1,7 m al frente, a la altura de los ojos). Fondo negro.
- ⚠ **El `BillboardComponent` del actor (ícono del editor, en el ORIGEN = centro del núcleo) tiene tamaño CONSTANTE en
  pantalla**: de cerca queda dentro del núcleo, desde ≥ 2 m asoma como un disco gris y un anillo cortado que PARECEN
  un defecto de la membrana. Es solo del editor; oculto en esta instancia (`bVisible` false). Diagnóstico: capturas
  lejos/cerca/costado, sin LODs (1 por malla), después ocultando el billboard.
- Poses del recorrido 0 → 1 (`GlobalState` en la instancia re-corre el CS; la captura en el MISMO script ya lo refleja):
  0-0,35 elegante (hebras finas que engordan); **0,5 los brotes se leen como ESPINAS oscuras**; 0,65-0,8 filamentos
  oscuros de los puentes cerrándose; **1,0 anillo de puentes gruesos que se lee "molecular"** + núcleo con lóbulos.
  Imágenes: `VR_Test/Saved/ClaudeScripts/Loving/propuesta_estados.png` y `propuesta_flota_x4.gif` (`PreviewTime` 0-30 s).

## TODO
- [ ] 🔴 **V3: juicio de Beltrán** mirando `Test_Loving` (en el viewport anima solo con la respiración/curl; el
      flotar de los grupos necesita `PreviewTime` o PIE con `bFakeSignal`). Colores del Ganzfeld y de las partículas = punto de partida mío.
- [ ] 🔴 **Medir V3 en el visor**: célula + partículas (9600 VS pesados) + Ganzfeld fluido. Con 10 grupos son ~2× vértices de brazo.
- [ ] Con 10 grupos y `SizeVariation` alto, en calma los grupos grandes quedan casi tocándose (48 cm de radio): subir
      `GroupSpread` o escalar `DistConnected` con N si se usa así.
- [x] ~~🔴 Estética de la fase 2 según Beltrán: brotes, puentes cerrándose, anillo a S = 1.~~ → descartado: sin puentes (V3).
- [ ] 🔴 **Ver la fase 1**: reabrir la pestaña del BP → **Simulation** (o instancia colocada / PIE). Mirar:
      núcleo flotando, cada grupo por su lado, hebras que se estiran detrás del núcleo, sin tirones ni bucle
      visible; más lento y quieto al subir `GlobalState`. Control: `FloatAmount` 0 = la pose de antes.
- [x] Fase 2 aplicada (`CalmStep` + `BridgeStep` con `BridgeQ`, reset al cambiar `GroupCount`, `prox` NOMINAL). ⬜ sin simular: portarla a Python como la fase 1 antes de verla.
- [ ] 🔴 Medir en el visor ANTES de las fases 3-4 (y antes de cerrar la 2: los puentes-brote se dibujan desde S≈0,1).
- [ ] 🔴 Con un nivel libre: colocar el actor (+X hacia el usuario, ~1,5-2 m, a la altura de los ojos
      sentado) y verificar el **barrido 0 → 1 → 0** (grupos se acercan, cuellos engordan, puentes nacen
      como muñones y se fusionan, reversibilidad) — por instancia y en PIE con `bFakeSignal`.
- [x] Guardar los últimos ajustes (menisco 0,18/0,6 en arm+bridge; `GlobalState` 0,3 restaurado) — guardado y releído al terminar el PIE.
- [ ] APK Development: verificar en los DOS ojos (gotcha 399) material por material; medir con el banco
      de visibilidad (sin puentes / sin película / sin cuerpos).
- [ ] Afinar colores en el visor (LDR sin tonemapper). Paleta de la etapa: familia violeta.
- [ ] Capa A: 3 presets de forma (una por pregunta) · API `SetState/SetAgitation/SetColorTemp` para la etapa.
- [ ] Borrar `Dev/M_LovingProbe_SC` (material de prueba del struct HLSL) cuando ya no sirva.
- [x] Ver la membrana del núcleo junto al resto — ✅ 2026-09-27 (reabriendo la pestaña del BP).
- [ ] Unión de un brazo que va hacia el fondo: la línea de Plateau de atrás se ve a través de la membrana
      (coherente, como una pompa); atenuarla solo si molesta en visor.
