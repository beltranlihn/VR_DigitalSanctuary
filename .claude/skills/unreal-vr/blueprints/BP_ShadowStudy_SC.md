# BP_ShadowStudy_SC + M_FakeShadow_SC + M_ShadowSphere_SC — la sombra falsa (Core/Light/)

> Creado 2026-09-04. Efecto 1.7 del [plan de la galeria](../../../../docs/PLAN-GALERIA-EFECTOS.md), el ultimo de la mitad de Beltran.
> **Estado: 🟡 armado y juzgado en el viewport, colocado como estacion 6 de la galeria (`GAL_6_ShadowStudy`, en 180000/100000/0). Falta el visor.**

## Que es, y por que importa mas de lo que parece
Una esfera mate sobre un fondo palido, con una **sombra larga y suave que barre**. Sale del video que trajo Beltran.

🔴 **Abre un registro visual que la obra hoy NO puede hacer: oscuridad sobre claro.** Todo lo demas del toolkit —haces, nube, niebla, ganzfeld, puntos, lineas— es **luz sobre negro**. Este es el unico que trabaja al reves, y por eso vale aunque sea el mas simple de todos.

## Como se hace una sombra sin una sola luz
En Quest no hay sombras dinamicas (todo horneado, renderer movil). La sombra es un **test rayo-esfera por pixel** dentro del material del suelo:
```
L   = normalize(dir de la luz ficticia)      // yaw/pitch, + Time x SpinSpeed
w   = CasterPos − P                          // P = el punto del suelo
t   = dot(w, L)                              // que tan "hacia la luz" esta la esfera
d   = |w − L·t|                              // distancia del centro de la esfera al rayo
pen = R × (1 + t × Penumbra)                 // la sombra se ENSANCHA con la distancia
s   = 1 − smoothstep(pen × Hard, pen, d)
s   = s × step(0, t) × e^(−t × Falloff)      // se desvanece a lo lejos
Suelo = GroundColor × lerp(1, 1 − ShadowStrength, s)
```
Son ~12 instrucciones y **cero luces**. La esfera lleva su propio material (`M_ShadowSphere_SC`) con un **lambert envuelto** (`dot(N,L)·0.5+0.5`) contra la MISMA direccion — sin eso se veria como un disco plano, no como una esfera.

🔴 **Autocontenido a proposito:** la esfera y el suelo son componentes del MISMO Blueprint, asi que el Construction Script sabe donde esta la esfera y le empuja `CasterPos` y `CasterRadius` al material del suelo. Sin colecciones de parametros y sin cañeria entre actores.

⚠ **La direccion de la luz se calcula DOS VECES, una en cada material** (misma formula yaw/pitch/spin). Es a proposito: asi el giro se anima **en el material**, se ve en el editor sin darle Play, y no hace falta un Tick que sincronice a los dos.

## 🔴 La CUPULA — sin ella hay linea de horizonte, y eso mata lo eterio
Pedido de Beltran apenas lo vio: *"armalo en un lugar completamente blanco, un lugar completamente abstracto; no quiero ver una linea de corte de horizonte"*.

El problema es geometrico y obvio una vez dicho: **un plano termina**, y donde termina se ve el negro del vacio. Esa arista es una linea de horizonte, y una linea de horizonte **ancla la escena** — deja de ser un espacio abstracto y pasa a ser "un piso en una habitacion".

✅ Un tercer componente **`Sky`**: el mismo `SM_GanzShell` con `M_VoidBack_SC` (unlit, two-sided, color plano), envolviendo todo. Con **`SkyColor` igual a `GroundColor`** el borde del suelo **desaparece**: los dos son colores planos unlit identicos, asi que la transicion no existe. Queda un blanco infinito donde la unica informacion es la esfera y su sombra.

💡 **Es la receta para cualquier estacion "clara" de la obra**, no solo para esta: si el efecto vive sobre claro, necesita su propia cupula. Las estaciones oscuras no la necesitan porque el vacio ya es negro.
⚠ `SkyRadius` 9.000 y `GroundSize` 16.000 por default: **el suelo tiene que ser mas grande que la cupula** en su plano, o se ve el borde del plano por dentro de la esfera.

## Perillas
`A - Forma` (SphereRadius 70, SphereHeight 110, GroundSize 5000) · `B - Color` (GroundColor, SphereColor, AmbientFloor 0,45, Brightness) · `C - Sombra` (ShadowStrength 0,72, Penumbra 0,007, Hard 0,25, Falloff 0,00035) · `D - Luz` (LightYaw, **LightPitch 11**, SpinSpeed 5).

💡 **`LightPitch` es la perilla que decide todo el caracter.** Alto (30°+) da una sombra corta y pegada al objeto; **bajo (10-15°) da la sombra larga del video**. Y `Falloff` decide hasta donde llega antes de disolverse: bajarlo alarga, subirlo la corta.

## 🔜 VARIOS CASTERS — la mitad hecha, y por que quedo a medias
Observacion de Beltran, y es la correcta: *"no seria como una version adaptada de los haces de luz? quizas ahi podemos poner varios"*. **Es exactamente la misma arquitectura** que ya existe para que el haz bañe meshes — `MPC_LightShaft` + `M_BeamReceiver_SC` — y la MPC hasta usa el prefijo **`Beam0`**, o sea nacio pensada para varias ranuras.

✅ **Hecho:** la MPC gano `Caster1Pos/Radius` y `Caster2Pos/Radius`, y **`M_FakeShadow_SC` ya las lee**: calcula la sombra de las dos ranuras y la combina con la local por `max` (las sombras no se suman, se solapan). Una ranura con radio 0 no aporta nada. **Total: 3 sombras.**

⬜ **Falta:** que un BP publique su posicion en su ranura. El obstaculo es concreto y esta identificado: **`Rendering|Material|SetVectorParameterValue` existe DOS veces** — la version de `MaterialParameterCollection` y la de `MaterialInstanceDynamic` — y `write_graph_dsl` resolvio a la de MID, que exige un target y no compila. `BP_LightShaft_SC:PushMPC` **usa la buena**, asi que la salida es cirugia con `create_node` pasando **`declaring_class`** para desambiguar, copiando los pines de ese grafo. Son ~10 nodos.

## Limite honesto
Hoy, **una esfera, una sombra** (mas dos ranuras listas del lado del material). El costo es lineal por caster, asi que esto **no es un sistema de sombras**: es *una* sombra bien hecha. Si alguna vez hace falta que varios objetos proyecten, ahi si conviene una Material Parameter Collection con la lista de casters — y ahi el costo empieza a importar.

## TODO
- [ ] Juicio de Beltran y prueba en visor.
- [ ] Rangos de slider a mano: SphereRadius 10-200 · SphereHeight 0-300 · GroundSize 500-8000 · ShadowStrength 0-1 · Penumbra 0-0,02 · Hard 0-1 · Falloff 0-0,005 · LightPitch 5-60 · SpinSpeed 0-30.
- [ ] Si gusta el registro, probar con otras formas (un cilindro, un plano flotante): el material del suelo solo sabe de esferas, un caster de otra forma pide otra cuenta.


## 🔴🔴 EL PEDIDO REAL NO ERA UNA SOMBRA EN EL PISO — es un HAZ NEGRO en el aire
Malentendido de fondo, mio, que costo varias pasadas. Beltran lo dijo tres veces y yo lo lei mal las tres:
1. *"¿no seria como una version adaptada de los haces de luz?"* — lo tome como arquitectura (la MPC), no como la FORMA.
2. *"pero es un haz de luz, no una sombra en el plano"*.
3. *"es un lightshaft negro sobre blanco en el fondo"* · *"no tiene que haber una superficie plana tampoco, esto es tridimensional"*.

**Lo que quiere es un volumen conico oscuro en el aire** — el mismo `BP_LightShaft_SC` pero oscureciendo en vez de iluminar — con la esfera en su boca. **No** una mancha pintada sobre un plano. Y el barrido tambien es conico: *"la rotacion tambien es conica, partiendo desde la esfera pero siempre con una diagonal, no solo en un eje"* — o sea la direccion orbita alrededor de un eje **inclinado**, no alrededor de la vertical.

### Lo que quedo construido y sirve
- ✅ **`M_ShaftDark_SC`** — duplicado de `M_LightShaft` con **`BLEND_Translucent`**, emisivo = `DarkColor` y opacidad = la luminancia del haz original × `DarkStrength`. Es el haz, en negro, con todas sus perillas (spread, wobble, gradiente, tip soft).
- ✅ **`M_ShadowCone_SC`** — version minima propia (Fresnel + caida por largo), tambien translucida oscura.
- ✅ El **vacio blanco** (cupula) y la esfera mate.
- ✅ La sombra proyectada sobre el suelo (modelo de **luz puntual**: apice en la luz, cono tangente a la esfera). Sirve si algun dia se quiere el piso; hoy Beltran lo descarto.

### 🔴 Los dos obstaculos concretos, para retomarlo sin volver a tantear
1. **`BLEND_Modulate` NO se dibuja en el renderer movil.** Fue el primer intento y no renderiza nada. Con translucido oscuro si funciona.
2. **`BP_LightShaft_SC` crea su propio MID de `M_LightShaft` en el Construction Script**, asi que **pisa cualquier `overrideMaterials` que se le ponga a la instancia**. Para usarlo en version oscura hace falta darle una variable de material (como ya tiene `Mesh`) y asignarla ANTES de los pushes de parametros. Es un cambio chico a un asset compartido.
3. Para el barrido conico: `Math|Vector|RotateVectorAroundAxis` con un eje inclinado autorable, no yaw sobre la vertical.

⚠ **El componente `Cone` del BP quedo agregado pero SIN configurar** (su funcion `ApplyCone` se borro cuando fallo el nodo de rotator). Esta oculto para que no moleste. Al retomar: o se completa esa funcion, o se elimina el componente y se va por la via del haz.


## 🔴🔴 2026-09-07 — EL CONO DE SOMBRA SE FUSIONO ADENTRO: un solo actor, un solo panel
Pedido de Beltran, dos veces, y tenia razon las dos: *"junta la esfera y el cono en el BP; quiero controlar el efecto y todos sus parametros desde el mismo lugar"*. `BP_ShadowShaft_SC` ya NO se usa aca: el cono es ahora el componente **`Cone`** (SM_ShaftCone + M_ShaftDark_SC) de ESTE Blueprint, fiel al principio que este BP ya declaraba ("autocontenido a proposito").

### La arquitectura
CS: `ApplyShadow → ApplySky → ApplyLightDist → ApplyCone → AimCone`. Tick: `StepSweep(DT) → AimCone`.
- **`ApplyCone`** — escala del cono + TODOS los params de material, incluidos los neutralizadores de lo heredado del haz: `SmokeAmount 0`, `WobbleAmount 0`, y 🔴 **`LaserFloorZ = −100000`** (el material madre corta el haz en el piso; sin ese push, el default Z=0 rebana la sombra en horizontal — "como si hubiera un piso blanco").
- **`AimCone`** — TODO derivado de variables propias, sin cast ni referencias externas:
```
k       = 100·SphereRadius / ((50 + ConeSpread) · ConeScaleXY)   // Spread SUMA al radio base del WPO: radio efectivo = 50+Spread
punta   = esfera − u·(k·ConeScaleZ)                              // tangencia automatica
corte   = plano de MUNDO por el centro de la esfera, normal u    // params CutPlanePos/CutPlaneDir de M_ShaftDark_SC
```
Cambia `ConeSpread`, `ConeScaleXY/Z` o `SphereRadius` y colocacion+corte se reacomodan solos. Era EL requisito.

### Perillas (cat. *I - Cono*)
`ConeScaleXY` 3 · `ConeScaleZ` 9 · `ConeSpread` 56 · `ConeIntensity` 2,6 · `ConeEdgeSoft` 0,55 · `ConeLengthFade` 1,59 · `ConeTipSoft` 0. `DepthFadeDist` quedo horneada en 55,5 (literal en ApplyCone).

### Las 3 mordidas del COMPONENTE NUEVO en un BP con instancia colocada (gotcha §320)
1. La instancia lo recibe **sin malla** (§164 clasico) → escribirle staticMesh directo.
2. Nace **`bVisible = false`** → "no se ve ningun haz" con todo lo demas perfecto.
3. El material madre trae **terminos que OTRO BP neutralizaba** (piso, humo, wobble) → al migrar, empujar los neutralizadores explicitos.

### Limpieza (pedido: "el BP esta lleno de variables muertas")
Fuera: `Shaft`, `ShaftSpread`, `ShaftHalf`, la funcion `AimShaft`, el actor `BP_ShadowShaft_SC_C_0` del nivel, el componente huerfano `StaticMesh`, y 7 variables sin consumidor: `ConeLength/ConeWidth/ConeStrength/ConeColor/bShowCone` (un cono ANTERIOR abandonado — el `ApplyCone` vacio era suyo) y **`CasterSlot`/`bDriveMPC`** (la mitad hecha de "varios casters"; el plan sigue en la seccion de arriba, las perillas se recrean cuando se retome). Quedan **30 variables, todas consumidas**.
⚠ El asset `BP_ShadowShaft_SC` sigue en disco sin uso — preguntar a Beltran si se borra. `SetCut`/`SetCutPlane` en el son vestigios.
🟡 Sin visor. `castShadow` de la instancia se resiste a false (inocuo en unlit translucido, anotado).


## 2026-09-07 (cierre) — fuera el GROUND: la estacion es esfera + cono + cupula, nada mas
Beltran: *"elimina el ground ademas del BP, no sirve"*. Con `ShadowStrength` ya en 0 y la cupula igualada al suelo, el plano no aportaba nada. **Se fue: el componente `Ground`, la funcion `ApplyLightDist` entera, y 7 variables** (`GroundSize`, `GroundColor`, `ShadowStrength`, `Penumbra`, `Hard`, `Falloff`, `LightDist`) — o sea TODO el test rayo-esfera del suelo, que era la seccion "Como se hace una sombra sin una sola luz" de arriba. 🔴 Esa receta queda documentada aca por si vuelve, pero **ya no esta en el BP**; `M_FakeShadow_SC` queda como asset sin uso (preguntar si se borra, junto con `BP_ShadowShaft_SC`).

**Estado final:** CS = `ApplyShadow` (solo la esfera) → `ApplySky` → `ApplyCone` → `AimCone`. **23 variables, todas vivas**: A-Forma (SphereRadius/Height) · B-Color (SphereColor/Brightness/AmbientFloor/SkyColor) · A-Forma (SkyRadius) · D-Luz (LightYaw/Pitch/SpinSpeed — el lambert de la esfera) · H-Barrido (SweepAngle/Speed/Phase/AxisPitch/AxisYaw/bSweep) · I-Cono (las 7 del cono).
⚠ Quedaron getters huerfanos sueltos en ApplyShadow (no compilan, costo cero) — pasar `clean_orphans.py` en alguna sesion tranquila, no ahora.

## 🎨 2026-09-08 — `ConeColor` (el color de la sombra) + la esfera SIEMPRE por encima
Beltran: *"no tengo ninguna variable para seleccionar el color del shadow"* y *"a la esfera dale prioridad principal para que se vea siempre por encima del shadow"*.

### 1. `ConeColor` — la perilla que faltaba
El material **`M_ShaftDark_SC` YA tenia `DarkColor`** (y `DarkStrength`); lo que faltaba era que el BP los empujara. `ApplyCone` no tocaba ninguno de los dos, asi que el cono usaba el **default del material**.
✅ Variable **`ConeColor`** (LinearColor, cat. *I - Cono*) → `SetVectorParameterValueOnMaterials Cone "DarkColor"` al final de `ApplyCone`.
💡 **Sembrada en NEGRO (0,0,0) a proposito**: se leyo el default del material antes de tocar nada (`get_property_input(MP_EmissiveColor)` → `VectorParameter_2` → `defaultValue`) y era **exactamente negro**, asi que exponer la perilla **no cambio nada de lo que se veia**. 🚩 Regla: al exponer un parametro que hasta ahora corria con el default del material, **leer ese default y sembrar la variable con el** — si no, exponer la perilla es un cambio visual disfrazado.
⚠ `DarkStrength` (cuanto oscurece, o sea la opacidad) **sigue sin perilla**. Es un nodo mas si se quiere; no se agrego porque no se pidio y su default no se verifico.

### 2. 🔴 La esfera por encima: `TranslucencySortPriority` SOLA no alcanzaba
La esfera era **`BLEND_Opaque`** y el cono **`BLEND_Translucent`**. `TranslucencySortPriority` **solo ordena translucidos entre si** — sobre un objeto opaco no hace absolutamente nada. El orden entre los dos lo decidia la profundidad, y como el cono nace en la esfera, la mitad del cono queda geometricamente delante y la tapaba.

✅ **Para que la esfera participe de esa ordenacion hay que meterla en la pasada translucida:**
1. `M_ShadowSphere_SC` → **`BLEND_Translucent`** con **`MP_Opacity` = Constante 1** (conectada explicita, para no depender del default del compilador).
2. Componente `Sphere` → **`TranslucencySortPriority = 100`** (el cono queda en 0). Mas alto = se dibuja despues = va encima.

Con opacidad 1 y unlit, se ve **igual** que opaca; lo unico que se pierde es la escritura de profundidad, que aca no la necesita nadie (el `Sky` y el `Backdrop` son opacos y estan detras).
🚩 **La regla general, que ya mordio con la losa de niebla:** *"que se vea encima"* se resuelve con `TranslucencySortPriority` **solo si los dos objetos son translucidos**. Si uno es opaco, primero hay que decidir en que pasada vive.

⬜ **Sin verificar en viewport** — juicio de Beltran.

### 🔴 Correccion (misma jornada): el cambio en el CDO NO llego al actor ya colocado
Tras poner `TranslucencySortPriority = 100` en el componente `Sphere` del **CDO**, el cono seguia tapando la esfera. La causa, **leida del actor y no supuesta**: `BP_ShadowStudy_SC_C_0.Sphere` seguia en **`translucencySortPriority = 0`**. Un actor que ya estaba en el nivel tiene sus componentes **serializados**, y tocar la plantilla del CDO no reescribe esos valores.
✅ Hubo que escribirlo **tambien en la instancia** (`.../BP_ShadowStudy_SC_C_0.Sphere`). Estado verificado al cierre: instancia 100 · `Cone` 0 · material `BLEND_Translucent` con `MP_Opacity` = Constante 1.
⚠ El corte del cono por el plano **no era un bug**: Beltran confirmo que era un error suyo de composicion. `CutPlanePos/Dir/Radius` siguen sin empujarse desde el BP y corren con los defaults del material (`CutPlaneDir` = (0,0,1), `CutRadius` = 0, `CutSharp` = 0,6) — **funciona asi**, no tocar sin motivo.
💡 Alternativa mas "correcta" que quedo sin usar, por si el sphere translucido molesta algun dia: el material tiene **`CutRadius`** con un test `saturate((distancia − CutRadius) · CutSharp)`, o sea que empujando `CutRadius = SphereRadius` el cono se **recorta** dentro de la esfera en vez de reordenarse. Quita el solape en vez de taparlo.

### 🔴 `BackdropOffset` — el Construction Script le pisaba la posicion al telon
Beltran: *"el backdrop plane lo estoy tratando de mover (...) lo pongo en −20,0,0, pero al poner play vuelve a 0,0,0. Entonces nunca veo mi arreglo"*.
**Causa:** `AimCone` (que corre en el CS) hacia `SetRelativeLocation(Backdrop, MakeVector(0, 0, SphereHeight))` — o sea **reescribia X/Y en 0 en cada construccion**. Mover el actor a mano no servia de nada.

✅ Variable **`BackdropOffset`** (Vector, cat. *J - Telon*, default 0,0,0). Ahora:
```
SetRelativeLocation(Backdrop, MakeVector(Offset.X, Offset.Y, SphereHeight))
```
⚠ **La Z del offset se ignora a proposito**: el telon tiene que quedarse a la altura de la esfera (`SphereHeight`), que es lo que lo alinea con el corte. Si algun dia hace falta moverlo en Z, es sumarle otra variable a ese pin.
⚠ El offset es **relativo al actor y previo a la rotacion**, asi que "−20 en X" es lo mismo que Beltran estaba escribiendo a mano.

🚩 **El patron, que en este proyecto ya mordio con `FloorZ` de `BP_LightShaft_SC`:** si el Construction Script **escribe** una transform, esa transform **no se puede autorar con el gizmo** — el CS gana siempre y en silencio. La salida es la misma de aquella vez: **el CS calcula, y una variable aparte guarda lo que el humano quiere**; nunca los dos sobre el mismo valor.
💡 Sintoma que lo delata: *"lo muevo y al dar Play vuelve"*. No es un bug de Unreal ni del gizmo: es que alguien lo esta escribiendo.

⚠ 🔩 **Trampa del MCP encontrada de paso:** `create_node` **no puede crear operadores promotables** (`Math|Vector|vector+vector` y compañia) — devuelve *"does not exist"* aunque `get_node_infos` sobre uno existente reporte exactamente ese `type_id`, e incluso pasando `declaring_class`. Salida: armar la cuenta con funciones normales (`Math|Vector|BreakVector` + `Math|Vector|MakeVector`), que si se crean. `find_node_types` con un filtro es la forma de confirmar que un id es creable **antes** de intentarlo.

### ✅ El corte del cono, ahora en el SHADER y siguiendo al telon
Beltran: *"le puse play y se ve toda la parte de atras"* → *"lo que haga que se vea el haz girando y que no se vea la parte de atras del cono"*.

**Diagnostico (con evidencia, no con hipotesis):**
```
EventTick → StepSweep(DT):  if (bSweep) SweepPhase += SweepSpeed*DT;  AimCone()
```
Con `bSweep = true` y `SweepSpeed = 19,97`/s, **en Play el cono GIRA**. Pero en `AimCone` cada cosa se orientaba con algo distinto:
| | Se orientaba con |
|---|---|
| Cono | el vector barrido — incluye `SweepAngle` **y `SweepPhase`** → **gira** |
| Telon | `MakeRotFromZ(forward de SweepAxisYaw)` → **estatico** |
👉 En el editor la fase esta congelada y el telon tapaba bien **en esa fase**; al dar Play el cono se le escapaba. Por eso *"nunca veo mi arreglo"*: el arreglo era correcto para un solo instante.

✅ **Solucion: no rotar el telon (le giraria la pared al espectador) sino CORTAR el cono en el shader con el plano del telon** — usando los parametros `CutPlanePos`/`CutPlaneDir` que el material **ya tenia y nadie empujaba**. `AimCone` ahora termina con:
```
SetVectorParameterValueOnMaterials(Cone, "CutPlanePos", Backdrop.GetWorldLocation())
SetVectorParameterValueOnMaterials(Cone, "CutPlaneDir", -forward(SweepAxisYaw))
```
Como `AimCone` corre en cada Tick, **el corte sigue al telon siempre**: el telon queda fijo, el haz gira, y lo que cruza detras del plano deja de dibujarse. Cero mallas, cero rotacion extra.

💡 **`GetWorldLocation` del propio componente evito toda la cuenta**: `CutPlanePos` tiene que ser MUNDO (el material lo resta de `WorldPosition`), y sumar `ActorLocation + offset` habria necesitado un `vector+vector`, **que `create_node` no puede crear** (ver la trampa de los operadores promotables). Preguntarle su posicion al componente **despues** de moverlo es exacto y es un nodo.
⚠ **El signo se dedujo de la geometria, no se adivino**: el anchor de la estacion esta en `x = 179.100` y el actor en `x = 179.833`, o sea **la camara mira desde −X**, y el plano tiene normal ~+X → hay que **negar** para conservar el lado visible. Si se ve al reves (desaparece la mitad de adelante), el arreglo es quitar el `NegateVector`: un nodo.
⚠ `CutSharp` sigue en su default 0,6; como el `dot` esta en cm, el corte es duro (transicion de ~1,7 cm). Si se quiere un borde suave, esa es la perilla — hoy sin exponer.

### ✂️ `ConeCutRadius` — la "cola" que asomaba detras de la esfera
Beltran: *"sigo viendo esa cola justo atras"*. No era el angulo de rotacion: era el **segundo termino de corte** del material, que tambien estaba sin usar.

`M_ShaftDark_SC` multiplica la opacidad por **DOS** cortes, y los dos comparten `CutPlanePos`:
```
plano  : saturate( dot(WP − CutPlanePos, CutPlaneDir) · CutSharp )   ← ya conectado (v anterior)
esfera : saturate( (distance(WP, CutPlanePos) − CutRadius) · CutSharp )  ← estaba en CutRadius = 0 → inactivo
```
El segundo **carva una esfera** alrededor de `CutPlanePos`: es exactamente el corte por tangencia que hace que el cono nazca en la superficie de la esfera y no la desborde. Con `CutRadius = 0` no hacia nada, y por eso el vertice del cono asomaba por el borde.

✅ Variable **`ConeCutRadius`** (float, cat. *I - Cono*) → `SetScalarParameterValueOnMaterials(Cone, "CutRadius", ...)` en `ApplyCone`. Default del CDO **0** (= comportamiento anterior); en la instancia se sembro en **66,37**, que es su `SphereRadius`.
⚠ **Los dos cortes comparten el centro**, y `CutPlanePos` es la posicion del TELON (esfera + `BackdropOffset`). Con el offset actual de −14,5 cm el carve queda descentrado esa misma cantidad respecto de la esfera. Con radio 66 no se nota, pero **si sube mucho el `BackdropOffset` la cola puede volver de un lado**: ahi la salida es subir un poco `ConeCutRadius`, o separar los dos centros (hoy es un solo parametro en el material).

### 🔴🔴 La causa de fondo de la "cola": los DOS cortes compartian un solo centro
Beltran, despues de tres arreglos parciales: *"sigue apareciendo por detras jajaja. Porque sera tan dificil?"*. **Porque yo estaba tratando sintomas sin mirar el acoplamiento.**

`M_ShaftDark_SC` usaba **`CutPlanePos` para las dos cosas**:
```
plano  : dot(WP − CutPlanePos, CutPlaneDir)          ← tiene que estar en el TELON
esfera : distance(WP, CutPlanePos) − CutRadius       ← tiene que estar en la ESFERA
```
Con `BackdropOffset = (−14,5 · 0 · 0)` el centro del carve quedaba **14,5 cm corrido** de la esfera: del lado corto llegaba a `66,37 − 14,5 = 51,9` cm contra una esfera de `66,37` → **una banda de 14,5 cm de cono sin cortar**. Exactamente la cola de la captura. Cada arreglo previo era correcto **y parcial**, porque el error no estaba en el valor sino en que **un parametro servia a dos geometrias distintas**.

✅ **Se separaron:** parametro vectorial nuevo **`CutSpherePos`** en el material (el `Distance` ahora mide contra el, no contra `CutPlanePos`), y `AimCone` empuja:
```
CutPlanePos  = Backdrop.GetWorldLocation()   (sigue el BackdropOffset)
CutSpherePos = Sphere.GetWorldLocation()     (el carve, siempre centrado en la esfera)
```
Ahora `ConeCutRadius = SphereRadius` corta **exacto y simetrico**, y mover el telon ya no descentra el carve.

🚩 **La leccion (y la respuesta a "por que era tan dificil"):** cuando un arreglo correcto deja un residuo, y el siguiente tambien, **el problema no es el valor: es que dos requisitos distintos estan atados al mismo parametro**. Sintoma tipico: "lo arreglo de un lado y aparece del otro". Antes del tercer intento hay que ir a mirar **quien mas usa ese parametro**. Es la misma familia que gotchas §324 (material compartido) y §316b (el pulso que venia de otro subsistema).


## 🌬️ 2026-09-17 — la sombra RESPIRA (`StepBreath`, [[BP_BreathManager_SC]])
Decisión delegada por Beltrán (*"séptima decide tú"*): **inhala → la sombra se alarga y el barrido se suspende · exhala → se recoge hacia la esfera y el barrido fluye.** Es el mismo idioma que los túneles (velocidad baja al inhalar), más un mapeo de posición (el largo), que es el que da la sensación de espejo.

- **Perillas** (cat. *R - Respiracion*, 0 = apagado): `BreathLengthIn` / `BreathLengthOut` (fracción sobre el exponente `ConeLengthFade`: negativo = sombra más larga) · `BreathSweepIn` / `BreathSweepOut` (fracción de `SweepSpeed`).
- **EventTick**: `StepSweep(DT)` → `GetScalarParameterValue(MPC_Breath, "Signed")` → `StepBreath(S, DT)`.
- **`StepBreath`**: `"LengthFade"` = `max(ConeLengthFade·(1 + max(S,0)·LenIn + max(−S,0)·LenOut), 0,05)` al `Cone` cada tick (con ganancias en 0 empuja el valor autorado: idéntico) · si `bSweep` y hay ganancia de barrido: `SweepPhase += SweepSpeed·DT·(max(S,0)·In + max(−S,0)·Out)`. La fase ya se integraba en el BP → **cambiar la velocidad no produce saltos**.
- **Instancia `GAL_6_ShadowStudy`**: `LenIn −0,5` (exponente ×0,5 → más larga) · `LenOut 1,2` (×2,2 → se recoge) · `SweepIn −0,7` (×0,3) · `SweepOut 0,5` (×1,5; con +0,7 llegaba a 34°/s, brusco para un cono tan grande).
- 🟡 Compila estricto; sin PIE específico (la estación no es la de arranque). Es el mismo patrón que los haces, que sí se midió en PIE. El largo es un exponente: **ajustarlo mirando**, no es lineal.


### 🌬️ 2026-09-17 (2ª pasada) — curva SUAVE y rango exagerado
Beltrán tras probar: *"llegó muy duro a los valores máximos y mínimos, no suave como con la esfera"* y *"un poco más exagerados"*.
- **Causa (en el manager, no acá):** `BreathSigned` era `clamp(gain·y)` → con ganancia 1,5 una respiración normal chocaba contra ±1 y quedaba plana. Ahora es `k·y/(1+(k−1)|y|)` (techo suave, `SignedGain` 2).
- **Mapeo nuevo del consumidor** (sin quiebre en 0 aunque las ganancias sean asimétricas): `m = 1 + S·lerp(−Out, In, smoothstep((S+1)/2))`. `In` = fracción a inhalación plena, `Out` = a exhalación plena, igual que antes.
- `StepBreath` reescrita con la curva suave (largo y barrido).
- **Valores**: `LengthIn −0,65` (exponente ×0,35 → muy larga) · `LengthOut 2,0` (×3 → se recoge) · `SweepIn −0,9` (×0,1, casi quieta) · `SweepOut 0,7` (×1,7).


### 🌬️ 2026-09-17 (3ª pasada) — acompañar la respiración lenta, suavidad de resorte, más exagerado
Beltrán: *"si hago una respiración lenta deben demorarse más en llegar al máximo o mínimo, acompañando mi movimiento"* · *"sigo sintiendo que está un poco duro"* · *"los valores más exagerados, menos el metaball"*.
- **Causa (en el manager):** (1) `HorizTau` 3 s: la base del band-pass alcanzaba a una respiración lenta a mitad de la inhalación → el pico llegaba ANTES del final; (2) dos saturaciones encadenadas (`x/(1+|x|)` del nivel y el techo suave de `SignedGain`) = una sola muy comprimida: casi todo el recorrido quedaba pegado al máximo.
- **Arreglo (manager):** `HorizTau` **6**; `S` sale del band-pass CRUDO en cm (`x = (HFast−HSlow)·SignedGain`, `SignedGain` 1 = 1 cm) con codo suave `x/(1+|x|³)^(1/3)` (lineal hasta ~0,7) y pasa por un **resorte críticamente amortiguado** (`SmoothFreq` 6): velocidad continua, sin rebote.
- ✅ Medido en PIE con respiración de prueba de 10 s: el máximo llega al final de la media onda (no antes), la velocidad de `S` sube y baja suave.
- **Valores**: `LengthIn −0,8` (×0,2) · `LengthOut 3,0` (×4) · `SweepIn −0,5` (sigue girando al inhalar) · `SweepOut 1,2` (×2,2).


### 🌬️ 2026-09-18 — la APERTURA del cono y el BRILLO de la esfera
Beltrán: *"Inhalación agranda apertura de cono, baja velocidad de rotación y aumenta brillo. Exhalación aumenta velocidad, achica el cono y baja intensidad de luz, sin que esta desaparezca."*
La rotación y el largo **ya estaban** (`BreathSweepIn/Out` −0,5 / 1,2 y `BreathLengthIn/Out` −0,8 / 3,0) y quedaron igual: ya hacían "inhalar = más lento y más largo". Se agregaron los dos mapeos que faltaban.

#### 1. Apertura — va por CPU, porque mueve la punta del cono
🔴 **`AimCone` calcula la tangencia con `ConeSpread`** (`k = 100·SphereRadius / ((50 + ConeSpread)·ConeScaleXY)`). Si se modulara el `Spread` solo en el shader, el cono **se despegaría de la esfera**: con los valores de la instancia, pasar de 56 a 90 mueve la colocación ~33 cm. Por eso:
- Variable interna **`ConeSpreadNow`** (cat. *I - Cono*, **no** instance-editable). `ApplyCone` la siembra con `ConeSpread` al final; como el CS corre `ApplyCone → AimCone`, en el editor todo queda idéntico.
- **`AimCone` ahora lee `ConeSpreadNow`** en vez de `ConeSpread` (el getter viejo se borró).
- Función nueva **`StepAperture(S)`**: `ConeSpreadNow = ConeSpread · (1 + S·lerp(−AperOut, AperIn, smoothstep))` y push de `"Spread"` al `Cone`. La llama `StepBreath` justo después del push de `LengthFade`, antes del branch del barrido.
- 🔴 **El Tick se reordenó**, para que `AimCone` use la apertura de ESTE frame y no la del anterior. La cadena tiene **4 nodos de exec**, no 3 (`GetScalarParameterValue` del MPC es IMPURO y vive en la cadena):
```
antes:  Tick -> StepSweep (->AimCone) -> GetScalarParameterValue -> StepBreath
ahora:  Tick -> GetScalarParameterValue -> StepBreath (->StepAperture) -> StepSweep (->AimCone)
```
- 🔴🔴 **Costó un crash (gotcha 338).** Al reordenar conecté las dos puntas nuevas dando por hecho que los enlaces viejos se iban: **un pin de exec de ENTRADA acepta varias conexiones**, así que quedó `… -> StepSweep -> GetScalarParameterValue -> StepBreath -> …` en **bucle infinito**. Compiló sin error y el `read_graph_dsl` lo imprimió LINEAL; en PIE el visor quedó congelado y el editor se cayó. Para reordenar exec: **`break_pins` explícito** y verificar con `get_node_infos` que cada entrada tenga UNA sola fuente.
- 🔩 **Por qué una función nueva y no nodos sueltos**: `create_node` **no puede crear operadores promotables**, y `Math|Float|float*float` / `float+float` lo son (no aparecen en `find_node_types`). La salida barata es un grafo NUEVO escrito con `write_graph_dsl` (que sí los crea) y llamarlo. Es la misma trampa ya anotada acá para los operadores de Vector.

#### 2. Brillo — en el material, para que se previsualice con el slider
- `M_ShadowSphere_SC` gana un `Custom` **`BreathBright`** (4 entradas `Val/S/BIn/BOut`) intercalado entre `ScalarParameter_4` (`Brightness`) y `Multiply_7.B`, que es lo que alimenta `MP_EmissiveColor`. Lee `Signed` de `MPC_Breath` con un `CollectionParameter` propio.
- **Sin gate `On`** (a diferencia del metaball): con `S = 0` el factor da ×1 exacto, así que en reposo es idéntico y no hace falta.
- Parámetros nuevos `BreathBrightIn/Out` (default 0) + 2 pushes al final de `ApplyShadow`.

**Valores en `GAL_6_ShadowStudy`**: `BreathApertureIn 0,6` (56,05 → 89,7) · `BreathApertureOut −0,5` (→ 28,0) · `BreathBrightIn 0,8` (1 → 1,8) · `BreathBrightOut −0,6` (→ 0,4: baja pero **no se apaga**, que era el pedido explícito).

⚠ **Fill-rate**: el cono es translúcido y a ×1,6 de apertura cubre bastante más pantalla. Si la estación se cae de 72 fps en visor, la perilla es `BreathApertureIn`.
⚠ **Apertura y largo son CPU (Tick)**: NO se ven con `PreviewBreath` en el viewport, solo en Play/visor. El brillo sí se ve con el slider.
⬜ Compila estricto; sin visor.
