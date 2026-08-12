# BP_Walker — la caminata (Core/Movement/)

## Purpose
Mueve el pawn por un spline con el efecto de caminata: rampa de aceleración, **bob vertical + giro acoplados a la cadencia del paso** y viñeta dinámica. Vive en el **nivel persistente** (no en un sublevel) y lo dispara `BP_StageDirector`.

Es el mayor riesgo de comodidad de la obra. Todo es parámetro ajustable **incluido a cero**, porque la susceptibilidad al mareo varía muchísimo entre personas (`docs/OBRA-SOUL-CHARGER.md` §9.2).

## Status
🟡 **Construido y compilando. Falta el test en visor — y acá el visor es el único juez.** Creado 2026-08-11 (rama `core/esqueleto`).

## Componentes
- **`Path`** (`SplineComponent`) — el camino. El **Construction Script lo construye recto** desde `PathHalfLength`: dos puntos, en `X = -PathHalfLength` y `X = +PathHalfLength`. Con el default de 500 queda un spline de **10 m de largo**.

## 🔴 El mapa de distancias del spline — leer esto antes de tocar el director
El spline **no es "de la sala A a la sala B"**: es el camino de UNA sala, y las dos salas comparten origen. Convención:

| Distancia | Punto |
|---|---|
| **0** | El umbral de **entrada** de la sala (en X = −500) |
| **500** | El **centro** de la sala (el origen del mundo) |
| **1000** | El umbral de **salida** de la sala (en X = +500) |

Cada tramo de caminata usa medio spline:
- **Salir de una sala** → `StartWalk(500, 1000, RampIn=true,  RampOut=false)`
- **Entrar a la sala nueva** → `StartWalk(0, 500, RampIn=false, RampOut=true)`

Los dos tramos suman **10 m ≈ 5,7 s a 175 cm/s**, que es el largo de beat que pide §9.2. El pawn salta de X=+500 a X=−500 en el momento del negro; eso es exactamente el "vuelve al centro sin que se note".

🔴 **`RampIn=false` en el segundo tramo es obligatorio**, y `Phase` **no se reinicia** en `StartWalk`: si el segundo tramo volviera a acelerar desde cero, el usuario sentiría un frenazo y un arranque en medio de la transición, que es justo lo que la aceleración suave viene a evitar. El paso tiene que seguir su ritmo por debajo del negro.

## Registro de variables

### Comodidad — instance-editable, todas se pueden poner en 0
| Variable | Default | Qué ajusta |
|---|---|---|
| `Speed` | 175 cm/s | Velocidad de crucero. §9.2 pide 1,5–2 m/s; 175 es el medio. |
| `AccelTime` | 1.0 s | Duración de la rampa. **Es la palanca #1 de comodidad: la aceleración es lo que marea, no la velocidad.** |
| `BobHeight` | 1.75 cm | Amplitud vertical. Rango del doc: 1,5–2 cm. **A 0 = sin bob vertical.** |
| `BobRollDeg` | 1.5 ° | Amplitud del giro (roll). Rango del doc: 1–2 °. **A 0 = sin giro.** |
| `StepsPerSecond` | 1.8 | Cadencia de pisadas (≈108 por minuto, marcha tranquila). Define la frecuencia de todo el bob. |
| `VignetteMax` | 0.55 | Opacidad de la viñeta a velocidad plena. **A 0 = sin viñeta.** |
| `PathHalfLength` | 500 cm | Medio spline. Cambiarlo reconstruye el camino en el Construction Script. |

### Estado de la caminata
| Variable | Rol |
|---|---|
| `bWalking` | Gatea el Tick. `StartWalk` lo prende; `UpdateWalk` lo apaga al llegar. |
| `Dist` | Distancia actual sobre el spline. |
| `ToDist` | Distancia de destino del tramo en curso. |
| `bRampIn` / `bRampOut` | Si este tramo acelera al empezar / frena al terminar. |
| `Elapsed` | Segundos desde el inicio del tramo. Alimenta **solo** la rampa de entrada. |
| `Phase` | Fase del paso **en grados**, acumulada. **No se reinicia entre tramos** (ver arriba). |
| `BaseRot` | Rotación del pawn al empezar. El roll se suma **sobre** esta base para no pisar su yaw. |
| `PawnRef` | El pawn (`GetPlayerPawn 0`, cacheado en `StartWalk`). |
| `VignetteRef` | El `BP_Vignette` del nivel. Si no está, se camina sin viñeta y se avisa por log. |

### Dispatcher
- **`OnWalkFinished`** — lo consume el director para encadenar el tramo siguiente o la transición.

## Estructura de grafos

**`ConstructionScript`** — construye el spline recto.
⚠ Se escribe `(fn ConstructionScript ...)`, **no** `UserConstructionScript` (ver `references/dsl.md`).
Si algún día se quiere un camino curvo dibujado a mano, hay que **sacar esta lógica**, porque reconstruye el spline en cada recompilación.

**`StartWalk(FromDist, NewToDist, RampIn, RampOut)`** — cachea pawn y `BaseRot`, fija el rango y los flags, `Elapsed = 0`, `bWalking = true`, y **al final** busca el `BP_Vignette`.
⚠ La búsqueda del vignette va **última** porque el `CastTo` es multi-exec y el parser del DSL no deja poner statements después de una rama.

**`UpdateWalk(DeltaSeconds)`** — el corazón. Orden del pipeline:
1. **Rampa.** `tUp = RampIn ? clamp(Elapsed / AccelTime) : 1`; `tDown = RampOut ? clamp((ToDist − Dist) / (Speed·AccelTime)) : 1`; `t = min(tUp, tDown)`.
2. **Suavizado.** `ramp = t²·(3 − 2t)` — smoothstep, no lineal. Da aceleración continua (sin tirón de derivada) en los dos extremos.
3. **Avance.** `Dist = min(Dist + Speed·ramp·Δt, ToDist)`.
4. **Fase del paso.** `Phase += Δt · StepsPerSecond · ramp · 360`. **La cadencia sigue a la velocidad real**, no corre por su cuenta.
5. **Bob.** `vert = sin(Phase) · BobHeight · ramp` · `roll = sin(Phase / 2) · BobRollDeg · ramp`.
   🔴 **El vertical va al doble de frecuencia que el giro** (`Phase` vs `Phase/2`): una bajada por pisada, un vaivén por zancada. Es la relación real de la marcha humana, y es lo que hace que el cerebro lo lea como locomoción en vez de como una oscilación arbitraria. **Las dos amplitudes multiplican por `ramp`**, así entran y salen con la velocidad.
6. **Aplicar.** `SetActorLocation(pawn, spline(Dist) + (0,0,vert))` y `SetActorRotation(pawn, BaseRot con roll sumado)`.
   🔴 **La yaw del pawn NO se toca.** Girar el mundo alrededor del usuario es un disparador fuerte de mareo, y el camino es recto: no hace falta.
7. **Viñeta** vía `ApplyVignette`, y si llegó: `bWalking = false` + `OnWalkFinished`.

**`ApplyVignette(Amount)`** — existe **solo** porque el `IsValid` del vignette es multi-exec y cortaría la lista de statements de `UpdateWalk`. Es el patrón "extraer a función" de `dsl.md` §4.

**`EventGraph`** — `Tick`: si `bWalking`, `UpdateWalk(Δt)`.

## Session log
- **2026-08-11** — creado. Defaults verificados efectivos en el CDO con `get_properties`. Rediseñado a mitad de camino para tomar rango explícito (`FromDist`/`ToDist`/flags) al notar que una caminata de un solo tramo da solo ~2,9 s, la mitad del beat que pide el doc.

## 🔴 Falta la caminata de la INTRO, que es OTRA caminata (§3, aclarado 2026-08-11)
El mapa de distancias de arriba describe la caminata **entre salas**. Pero §3 tiene otra, antes de todo: al apretar **Start** en el menú, el pawn avanza por la oscuridad hasta la puerta del Center. Y no se parece:

| | Entre salas | **Intro** |
|---|---|---|
| Duración | ~5,7 s (dos tramos de 5 m) | **~45 s**, con **30–40 s de avance estable** |
| Largo | 10 m | **52–70 m** a 175 cm/s |
| Forma | centro → umbral, negro, umbral → centro | **un solo avance continuo** hacia la puerta |
| Entorno | dentro de una sala iluminada | **oscuridad**, sin sala cargada |

🔴 **Por qué los 30–40 s no son negociables:** §3 dice que *"la caminata de la intro tiene dos trabajos: instala el mood **y es donde se toma el baseline**"* (§5). Si se acorta, la medición no tiene de dónde promediar. **Es un requisito de la instrumentación, no de ritmo.**

**Consecuencia práctica:** `PathHalfLength` (500 cm) sirve para las transiciones y **no** para la intro. Opciones: una segunda instancia de `BP_Walker` con su propio `PathHalfLength` largo, o hacer el camino un parámetro por llamada. Decidir cuando se construya la intro; **no forzar el mismo spline para las dos cosas.**

⚠ Y hay que verificar que el bob y la viñeta **aguanten 40 s seguidos** sin cansar. Todo lo probado hasta ahora son tramos de ~6 s; 40 s de oscilación continua es un régimen distinto y puede necesitar amplitudes más bajas que las de las transiciones.

## TODO
- [ ] 🔴 **La caminata de la intro** (arriba): camino largo propio + validar 40 s continuos en visor.
- [ ] 🔴 **Test en visor, y con gente ajena al equipo** (§9.2 lo pide explícitamente). El orden de ajuste sugerido: primero `AccelTime`, después `VignetteMax`, y recién al final las amplitudes del bob.
- [ ] Probar el caso `BobHeight = BobRollDeg = VignetteMax = 0` — tiene que quedar una traslación lisa y usable, es el modo accesible.
- [ ] Medir el costo de la viñeta en device (es translúcida y llena pantalla; ver el TODO de `BP_Vignette`).
- [x] ~~`Recognizing` necesita otra personalidad de movimiento~~ → ✅ **DECIDIDO 2026-08-12: en Recognizing el pawn NO se mueve — el entorno desciende** (la columna/anillos bajan alrededor; ilusión de ascenso). No es un walker hermano ni un flag de este BP: es un BP propio de esa sala, se construye con la etapa.

## Open questions
- ¿1,8 pisadas/s es la cadencia correcta para 175 cm/s? Físicamente una marcha a 1,75 m/s va más cerca de 2 Hz. Si el bob se siente "lento para lo rápido que avanzo", subir `StepsPerSecond` antes que tocar la amplitud.
- El roll rota el espacio de tracking entero. Habría que confirmar en visor que a 1,5° no se percibe como que el suelo se inclina.

## Relacionados
- [[BP_Vignette]] · [[BP_Room]] · `BP_StageDirector` (todavía sin construir)
