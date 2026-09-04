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
