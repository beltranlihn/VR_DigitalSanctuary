# BP_DrawLimit — la esfera límite del dibujo de Surrounding (Stages/Movement/)

## Purpose
El guión, Acto 8: *"mecánica de dibujo alrededor con **esfera traslúcida de límite** — invadirla afina la línea en punta y la corta"*. Es lo que convierte el dibujo libre en **dibujar ALREDEDOR de la ameba**: la esfera marca dónde no se puede entrar, y entrar tiene una consecuencia clara y sin castigo.

## Status
🟡 **Construido y compilando**; ⬜ **falta el `DrawSpot` en la sala y el visor**. Ver "Lo que falta de tu lado" abajo.

## 🔴 Cómo corta el trazo: reusando el camino que ya existe
No hay lógica nueva de corte. `BP_DrawCanvas` **ya sabe terminar un trazo en punta**: tiene `TaperOut`, `CollapseRing` y `EndStroke`, y los usa cuando se suelta el gatillo. Entonces lo único que hace la esfera es **fingir que se soltó el gatillo**:

```
WatchTip (timer, cada PollTime)
  distancia(pincel, centro) < LimitRadius  y  no estábamos adentro
      → CutStroke:  BP_BrushTool.bTrigHeld = false   ← el trazo termina por el camino de siempre, afinándose
                    + háptico de selección + log
  al salir → se rearma
```
👉 Efecto para el usuario: **la línea se afina hasta desaparecer al tocar la burbuja, y hay que volver a apretar para seguir dibujando.** Que es exactamente lo que pide el guión, sin tocar el pipeline de geometría (que es frágil y está probado).

🔑 **El dato que lo hizo posible**: desde OTRA clase, el setter de un bool con prefijo `b` **sí existe y sí se puede escribir** — se llama **sin la `b`** (`Class|BPBrushTool|SetTrigHeld`) y va con keywords: `(Class|BPBrushTool|SetTrigHeld :self _b :bTrigHeld false)`. Es la vuelta al problema de que los setters `b` **propios** no se pueden escribir por DSL (gotcha §62).

| Variable | Default | Rol |
|---|---|---|
| `LimitRadius` | 45 cm | El radio de la zona prohibida. **La palanca**: define cuánto "aire" queda entre la ameba y el dibujo. |
| `PollTime` | 0,06 s | Cada cuánto se mide. Bajo a propósito: si es lento, el trazo se mete adentro antes de cortarse. |
| `InsideFlag` | 0/1 | Para cortar **una vez** por entrada, no cada tick. Es un `int` y no un bool **a propósito** (§62). |
| `CutCount` | — | Cuántas veces se cortó. Sale en el log; sirve para saber si el radio molesta. |

La burbuja es una esfera del motor con **`MI_Ghost`** (el material fantasma que ya usaban las columnas de Recognizing), sin sombra y sin colisión.

## Lo que arma la etapa
`BP_Stage_Surrounding.SurrRunBody` ahora hace `SurrCanvasSetup` **antes** de soltar el pincel:
- busca el TargetPoint con tag **`DrawSpot`**;
- **`PlaceSoulForDraw`** → la proto ameba se desprende del HUD (`LeaveHud`), se **agranda** a `DrawSoulScale` (1.8) y **viaja** hasta ese punto en `DrawTravelTime` (2,2 s) — *"algo más grande que un balón"*;
- **`SpawnDrawLimit`** → nace la esfera ahí mismo y se enciende.
`CleanupSurr` la destruye junto con el pincel y el lienzo: **cero residuos**, que es la regla de la obra.

## ⬜ Lo que falta de tu lado (Beltrán)
🔴 **Poner un `BP_Anchor` con tag `DrawSpot` en `L_Room_Surrounding`**, igual que ya está el `BrushSpawn`. Ahí es donde se planta la ameba y nace la esfera — o sea, **con arrastrarlo se decide toda la composición del dibujo**: a qué distancia, a qué altura, qué tan cerca del cuerpo.
Si no está, la etapa **no se rompe**: loguea `SURROUNDING: FALTA el TargetPoint DrawSpot en la sala - se dibuja sin lienzo` y el dibujo sigue funcionando como hasta ahora.

## TODO
- [ ] 🔴 Visor: si 45 cm de radio es cómodo, si el corte se siente justo o castigador, y si la ameba a escala 1.8 tapa demasiado.
- [ ] El `SDraw` mientras se dibuja (falta cablear en `BP_BrushTool`).
- [ ] Arte de la burbuja: hoy es `MI_Ghost`. El guión la quiere **traslúcida**, quizá con un pulso al tocarla.

## Relacionados
- [[BP_BrushTool]] (a quien le "suelta el gatillo") · [[BP_DrawCanvas]] (`TaperOut`/`EndStroke`, el afinado que ya existía) · [[BP_ProtoSoul]] (`LeaveHud`/`TravelToPoint`) · [[BP_Stage_Subclases]] §Surrounding
