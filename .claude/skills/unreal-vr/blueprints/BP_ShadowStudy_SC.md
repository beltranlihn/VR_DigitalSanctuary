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

## Perillas
`A - Forma` (SphereRadius 70, SphereHeight 110, GroundSize 5000) · `B - Color` (GroundColor, SphereColor, AmbientFloor 0,45, Brightness) · `C - Sombra` (ShadowStrength 0,72, Penumbra 0,007, Hard 0,25, Falloff 0,00035) · `D - Luz` (LightYaw, **LightPitch 11**, SpinSpeed 5).

💡 **`LightPitch` es la perilla que decide todo el caracter.** Alto (30°+) da una sombra corta y pegada al objeto; **bajo (10-15°) da la sombra larga del video**. Y `Falloff` decide hasta donde llega antes de disolverse: bajarlo alarga, subirlo la corta.

## Limite honesto
**Una esfera, una sombra.** El costo es lineal por caster, asi que esto **no es un sistema de sombras**: es *una* sombra bien hecha. Si alguna vez hace falta que varios objetos proyecten, ahi si conviene una Material Parameter Collection con la lista de casters — y ahi el costo empieza a importar.

## TODO
- [ ] Juicio de Beltran y prueba en visor.
- [ ] Rangos de slider a mano: SphereRadius 10-200 · SphereHeight 0-300 · GroundSize 500-8000 · ShadowStrength 0-1 · Penumbra 0-0,02 · Hard 0-1 · Falloff 0-0,005 · LightPitch 5-60 · SpinSpeed 0-30.
- [ ] Si gusta el registro, probar con otras formas (un cilindro, un plano flotante): el material del suelo solo sabe de esferas, un caster de otra forma pide otra cuenta.
