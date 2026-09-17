# 📦 Mecánicas portables — cómo se empaqueta y se transplanta cada una

> **Documento canónico** (creado 2026-09-04, auditoría con Unreal abierto: dependencias medidas con `AssetTools.get_dependencies`, detalle extraído de los trackers de `blueprints/`). Es la página de arquitectura que salió del mandato de Beltrán (2026-09-03): *"Si no logramos armar sistemas que sean exportables, es trabajo perdido el del último mes."*
>
> **Para qué sirve:** cuando se pida "traer X a un nivel nuevo", se abre la ficha de X, se copia su paquete, se sigue su receta y se verifica su checklist. Sin releer trackers, sin redescubrir el enchufe.
>
> **Qué no es:** no reemplaza a los trackers (`.claude/skills/unreal-vr/blueprints/`) — ahí vive el detalle por grafo. Esto es el mapa de empaque y transplante.

---

## 1. El contrato de arquitectura (las reglas que hacen portable una mecánica)

### 1.1 Las tres capas
Toda mecánica se piensa en tres capas. Solo las dos primeras viajan:

| Capa | Qué es | Regla |
|---|---|---|
| **MOTOR** | Recibe datos, produce el efecto. No sabe de manos, input ni etapas. | Viaja intacto. Ej.: `BP_DrawCanvas` recibe puntos de mundo y hace cinta. |
| **MANAGER** (herramienta/driver) | Ciclo de vida, filtro, dueño del motor. Publica señales (variables públicas + dispatchers). | Viaja. **Un manager, N controles**: no sabe qué consumidores existen. |
| **ETAPA** | Práctica, metas, disolución, firma, avisos al director. | **No viaja nunca.** |

### 1.2 El esquema Manager/Control (Beltrán, 2026-09-03)
> Controller: conecta los controles al pawn y sus manos. · Breath: Manager + Control (elemento reactivo). · Heart: Manager + Control. · Mind: Manager (OSC de calm) + Control. · Attracting: Manager (beam + selector) + Control (secuenciador + seleccionables). · Drawing: Manager (dibujo anclado a pawn y controller).

Las dos reglas que lo sostienen:
1. **El Manager publica; el Control consume.** Precedente funcionando: `BP_Elevator_SC` consume `OnBeatPulse` del sensor.
2. **Solo el Controller conoce al pawn.** El contrato actual es `FindHand` por nombre de componente (`HandRight`/`HandLeft`), sin cast de clase. Cambiar de pawn = ajustar un solo BP.

### 1.3 Las reglas duras (todas pagadas con jornadas enteras)
- 🔴 **Una mecánica portable NUNCA es dueña del input.** Expone verbos (`Press()` / `Release()` / `SetTip(comp)`) y el anfitrión decide con qué gatillo los llama. Cero assets de input dentro del módulo.
- 🔴 **El módulo se inicializa tarde a propósito**: reintenta hasta tener lo que necesita (el `BeginPlay` de un actor del nivel corre **antes** de que exista el PlayerController — `EnableInput` ahí es no-op silencioso).
- 🔴 **La posición se autora con el TRANSFORM ENTERO del TargetPoint** (posición + rotación + escala), nunca con coordenadas en un Blueprint. Excepción acordada: un objeto **uno-por-sala, estático y autorado** (el timbre) se coloca a mano en el sublevel — se streamea con su sala gratis.
- 🔴 **El spawn/kill es el árbitro del input**: los listeners van en los actores de la etapa, nunca en el pawn (una binding en el pawn no se mata nunca).

---

## 2. La matriz de dependencias MEDIDA (2026-09-04, `get_dependencies`)

Qué referencia de verdad cada BP (solo lo relevante de `/Game/`; se omiten engine/scripts). **Leyenda:** 🟢 portable ya · 🟡 portable con pasos extra · 🔴 arrastra la obra entera.

| Blueprint | Depende de | Veredicto |
|---|---|---|
| **BP_HapticHub** | — (nada de /Game) | 🟢 puro |
| **BP_AudioHub** | solo assets de audio | 🟢 |
| **BP_BioHub** | `BP_OSCReceiver`, plugin OSC | 🟢 |
| **BP_DrawCanvas** | `M_Spray` + mesh de `/Game/Drawing/`, **`BP_AudioHub`**, **`BP_HapticHub`** | 🟢 (hubs = acople blando; ver ficha) |
| **BP_ControllerRig** | `BP_DrawCanvas`, `M_Emissive_Inst`, `IA_Shoot_L/R`, `IMC_MenuTrigger`, meshes `ControllerL/R` `BreathL/R`, `SKM_MannyXR_*` | 🟢 **el modelo a imitar: cero pawn, cero director** |
| **BP_BreathSensor_V2** | `BP_VRPawn_SC`, `IA_Shoot_L/R`, audio `Umbral` | 🟡 (pawn) |
| **BP_MenuButton** | `BP_VRPawn_SC`, `BP_AudioHub`, `BP_HapticHub`, `M_SoulRing`/`M_TextUnlit`/`M_Plate`, `IA_Shoot`+`IMC_MenuTrigger` | 🟡 (pawn + 2 hubs colocados) |
| **BP_InstructionsPanel_SC** | **`BP_Director_Movement`** ⚠, `WBP_Instructions`, `M_InstrGlass` | 🟡 ⚠ la referencia al director es un resto a podar: la arquitectura dice que el panel no conoce a ningún director |
| **BP_Bell** | `BP_VRPawn_SC`, `BP_MannequinsXR`, **`BP_Director_Movement`**, **`BP_Door_SC`**, `WBP_BellRing`, `MI_Bell`, 3 sonidos, `GrabHapticEffect` | 🔴 (es EL timbre de la obra; la variante portable es `BP_InstrButton_SC`) |
| **BP_SoulHUD_SC** | `BP_BioHub`, **`BP_Director_Story`**, `BP_FaceAnchor_SC`, `WBP_SoulHUD_SC`, `M_HudWidget_SC` | 🟡 |
| **BP_Elevator_SC** | `BP_Sensor_Soul`, **`BP_Director_Story`** | 🟡 (patrón consumidor correcto; el cierre apunta al director) |
| **BP_BreathOrb_SC** | `BP_Sensor_Soul`, `MI_Sensor` | 🟡 |
| 🆕 **BP_BreathManager_SC** (2026-09-17) | `MPC_Breath`, `/Game/XRFramework/Haptics/GrabHapticEffect` — **nada más de /Game** | 🟢 **medido: cero pawn, cero director** (cumple el criterio de "listo" de §5) |
| **BP_Sensor_Soul** | **`BP_VRPawn_SC`**, **`BP_Director_Story`**, `BP_ProtoSoul_SC`, `BP_BioHub`, `BP_SoundOrb_SC`, `BP_SaveMelody_SC`, `BP_BrushPalette`, `BP_DrawCanvas`, `MPC_Draw`, `MI_Sensor`, Niagara `LineTrace`, `HeartBeat`/`Trigger_Select`, `IA_Shoot`+`IMC_MenuTrigger` | 🔴 **el nudo del proyecto**: contiene 5 mecánicas y conoce al pawn Y al director por clase |
| **BP_Sequencer_SC** | **`BP_Sensor_Soul`**, **`BP_Director_Story`**, `BP_InstructionsPanel_SC`, orb/slot/save, `PadM1` + 20 clips | 🔴 (vía sensor y director) |
| **BP_SoundOrb_SC** / **BP_SaveMelody_SC** / **BP_SeqSlot_SC** | el cluster de Attracting + `BP_Sensor_Soul` | 🟡 (motores limpios; el acople al sensor es del diseño del beam) |

**Cómo leer esto según el destino:**
- **Nivel nuevo en ESTE proyecto**: las referencias de clase no rompen nada por sí solas; lo que importa es el **enchufe runtime** (qué actores tienen que estar colocados, qué pawn, si hay director). Eso es lo que lista cada ficha en "Enchufe".
- **Proyecto NUEVO**: `Migrate` arrastra la cadena transitiva entera. Migrar `BP_Sensor_Soul` hoy se lleva el director, el pawn, la ameba y medio Attracting. Por eso el plan de extracción (§5).

---

## 3. Las 7 trampas universales de todo transplante

Estas muerden en CUALQUIER mecánica; van antes que cualquier ficha:

1. 🔴🔴 **Los knobs instance-editable NACEN EN CERO en una instancia ya colocada**, aunque el CDO tenga valores (§212). Tras colocar o reponer un actor: **escribir a mano todas las perillas en la instancia y releerlas**. Es la causa #1 de "lo copié y no funciona".
2. 🔴🔴 **Los overrides del CDO no llegan a instancias ya colocadas**, y un componente agregado a un BP con instancias colocadas llega **pelado** (`Asset=None`, `OverrideMaterials=[]`, `widgetClass` vacío) (§240/§294). Después de tocar el CDO: diffear la instancia contra él.
3. 🔴 **El input que funciona en actores es UNO solo: eventos `IA_Shoot_Left/Right`** (pin `Started`/`Completed`, nunca `Triggered`), que llegan gratis por los `IMC_Weapon_*` de `DefaultMappingContexts` en `Config/DefaultInput.ini`. La receta de registro (por si acaso, y para `IA_Continue`) es **`BP_Sensor_Soul.EnsureInput`** (7 nodos, probada en gafas): `EnableInput(self, pc)` con el PC en SU pin (no en `self`) + `AddMappingContext(IMC, 1000, bIgnoreAllPressedKeysUntilRelease=False, bForceImmediately=True)` + autoverificación con `HasMappingContext` — **llamada desde el Tick con reintento**, nunca solo en BeginPlay. `IA_Attract_*` en un actor **jamás disparó**: no gastar otra jornada ahí.
4. 🔴 **Nada pegado al pawn/cámara puede tener colisión** (viñeta, HUD, ameba, anillos, beams, visualizadores): rompe todos los line traces. Y el diagnóstico correcto de un beam corto es el **print con nombre**, no hipótesis por turno.
5. 🔴 **`GetAllActorsOfClassWithTag` busca en TODO el mundo.** Hoy salva que las salas no coexisten; en un nivel nuevo con más de una zona cargada, **un tag distinto por par** (`bell_hall`, `instr_entering`…).
6. 🔴 **El hover que se calla no está roto: le falta un hub.** Los BPs que cachean `BP_AudioHub`/`BP_HapticHub`/`BP_BioHub` con `GetActorOfClass` **fallan en silencio** si el actor no está colocado (las ramas van envueltas en `IsValid`). Primer chequeo en PIE: que `AudioRef`/`HapticRef`/`BioRef`/`HandL`/`HandR` no sean nulos.
7. 🔴 **Un módulo ausente nunca se ve como error**: el patrón del proyecto es fallback silencioso + línea de log (`AUDIO: falta clip X`). Al montar en un nivel nuevo, **leer el log de arranque** es parte de la instalación.

---

## 4. Fichas de empaque por mecánica

> Formato fijo: **Paquete** (qué se copia) · **Enchufe** (qué necesita el nivel/pawn) · **API** (verbos y señales) · **Receta** (pasos) · **Estado** · **Deuda** (qué falta para que sea instantáneo). Detalle profundo: el tracker de cada BP.

---

### 4.1 🟢 Señal biológica — `BP_BioHub` (calm EEG + BPM por OSC)
**El modelo de mecánica bien separada**: motor/manager limpios, la etapa entra como un `int` opaco (`SetCurrentStage`), y la fuente real ya se verificó en vivo (2026-08-28).

- **Paquete:** `Core/Signals/BP_BioHub` + plugin OSC habilitado. Nada más (sin materiales, widgets ni audio).
- **Enchufe:** UNA instancia colocada **en el nivel persistente** (es un Actor: server en BeginPlay, emulador en Tick). Sin pawn, sin input, sin tags. ⚠ No puede convivir con otro server OSC en el mismo puerto (`BP_OSCReceiver` fuera del nivel).
- **API:** lee `CalmSmooth` / `HeartSmooth` (nunca el crudo) + `bConnected AND bSensorOn`. Registro: `BinHasCalm/Heart(i)` **antes** de `GetCalmBinAvg/GetHeartBinAvg(i)`; export con `Series(bHeart)`. Config por instancia: `Port` **10000**, `ListenIP` `0.0.0.0`, `AddrCalm` `/muse/calm`, `AddrHeart` `/muse/heart_rate`, `AddrSensorOn` `/muse/sensor_active`. Sin dispatchers: los consumidores poll-ean.
- **Receta:** copiar el BP → colocar en el persistente → escribir la config **en la instancia** → elegir modo (`bFakeSignal=true` sin hardware; el fake entra por el mismo `Ingest`) → consumidores con `GetActorOfClass` + cast cacheado → verificar `LogOSC: OSCServer 'BioHub' started` en PIE.
- **Estado:** 🟢 PIE + emisor real en vivo verificados. ⬜ Falta la misma prueba contra el APK en el visor (ahí cambia la red).
- **Deuda:** `bFakeSignal` es de instancia y **le gana al CDO** (ya pisó señal real una vez — verificar la instancia viva, no el papel). `Ingest` no es reescribible por DSL (solo cirugía). Promedios por etapa sin construir.

---

### 4.2 🟢/🟡 Dibujo 3D — `BP_DrawCanvas` (motor) + `BP_ControllerRig` (herramienta portable)
**El examen de portabilidad ya rendido**: el rig se montó en `L_XRTemplate` y en `TestMeshes` con dos pawns distintos y **dibuja en visor** (validado 2026-09-03).

- **Paquete mínimo:** `Stages/Movement/BP_DrawCanvas` (motor, viaja INTACTO) + `/Game/BP_ControllerRig` + material del pincel (`/Game/Drawing/Material/M_Emissive_Inst`; alternativa: `M_Brush_Light` + `MI_Brush_Veil/Neon` en `Stages/Movement/Materials/` — dos familias conviven, elegir una) + meshes `/Game/ControllerL|R`, `/Game/BreathL|R`, `SKM_MannyXR_left|right`. Requisito de proyecto: plugin **ProceduralMeshComponent** activo. Opcional: `BP_BrushPalette` (paleta 3×3) y `MPC_Draw` (el fade de etapa).
- **Enchufe:** el pawn solo necesita SceneComponents llamados exactamente **`HandRight`/`HandLeft`** (`FindHand` sin cast — cumplen `BP_XRPawn` y `BP_VRPawn_SC`). 💡 Y como esas manos son **hijas de su MotionController Grip**, el mismo contrato alcanza para conseguir la señal del mando (velocidad → calma): `GetAttachParent` + cast, sin tocar la clase del pawn. Input: eventos `IA_Shoot_L/R` (gratis por `IMC_Weapon_*`). El canvas SIEMPRE en **transform identidad** (el rig lo spawnea así). ⚠ El motor referencia `BP_AudioHub`/`BP_HapticHub` (acople blando: sin ellos no suena/vibra, no rompe).
- **API del motor:** `BeginStroke(BrushId, StartLoc, ControllerUp, BaseColor, **Mat**)` — 🔴 **5 parámetros; sin el Mat el trazo sale gris o invisible** · `AddPoint(NewLoc, ControllerUp, Width, Calm)` · `EndStroke()` · `RebuildFrom(CSV)` / `SerializeDraw()` (persistencia). Perillas del rig por instancia: `DrawWidth` 1.8 · `DrawColor` · `DrawMat` · `bCanDraw` · `HapticAmp` 0.25 · `bRightHand` · `bShow*`.
- **Receta (la probada):** copiar paquete → verificar contrato del pawn → arrastrar 2 rigs (posición del actor da igual: se re-anclan a la mano en BeginPlay) → `bRightHand=false` en uno → 🔴 escribir TODAS las perillas en las DOS instancias (nacen en cero) → verificar `IMC_Weapon_*` en `DefaultInput.ini` del proyecto destino → PIE: `RIGDRAW INIT` una vez por rig → visor.
- **Estado:** 🟢 rig dibujando + háptica validados en visor con dos pawns. 🟡 cinta plana + port Neural Canvas sin pasada de visor específica; fill del aditivo sin medir en APK.
- **✅ Hecho el 2026-09-04 (pasos 1 y 2):** se extrajo **`BPC_DrawTool`** (componente) del modo 5 del sensor **moviendo lo probado, no reescribiendo** — el componente no llama `EnableInput` ni registra contextos: recibe `Setup()`/`Press()`/`Release()` del anfitrión. Ya trae el One-Euro y la **calma real** (que el rig no tenía). Y **`BP_BrushPalette` quedó desatada del pawn**: `AcquireControllers` usa `PalGrip(Right)` en vez de castear a `BP_VRPawn_SC`.
- **Deuda restante:** el componente todavía **no lee la paleta** (color/ancho/material son fijos por `Setup`; falta el equivalente de `CurColor`/`CurWidth`/`CurBrushMat` + la supresión por `bOver`). Y la persistencia/reconstrucción (`RecordPoint`, `RebuildFrom`) sigue siendo capa obra dentro del motor: inofensiva, pero viaja como peso muerto.

---

### 4.3 🟡 Botones físicos — dos linajes, no mezclar
**Linaje A — `BP_MenuButton`** (contacto+gatillo, hold opcional): motor limpio. **Linaje B — `BP_Bell` → `BP_InstrButton_SC`** (contacto+hold sin gatillo, anillo, aparición por cercanía, tope de mano): `BP_Bell` es EL timbre de la obra (llama `OpenDoors` + `GotoNext` — 🔴 no portable); **`BP_InstrButton_SC` es la variante ya podada** y es la que viaja.

- **Paquete A:** `Core/UI/BP_MenuButton` + `M_Plate` + `M_TextUnlit` + `M_SoulRing` + `IMC_MenuTrigger`.
  **Paquete B:** `Core/UI/BP_InstrButton_SC` + `WBP_BellRing` + `MI_Bell` (maestro `M_RoomInterior` → obedece `MPC_Room.RoomLight`) + sonidos `SBubbleHoverOn`/`Charge1`/`SBubbleHoverOut` + `GrabHapticEffect`.
- **Enchufe A:** pawn `BP_VRPawn_SC` (cast en `CacheHands`) + 🔴 **`BP_AudioHub` Y `BP_HapticHub` colocados en el nivel** (sin ellos: silencio total, cero warnings) + un TargetPoint con tag por botón (spawn por orquestador).
  **Enchufe B:** pawn `BP_VRPawn_SC` (grips). **NO necesita hubs** (usa `PlayHapticEffect` directo al PC — la decisión correcta para actores portables). Se **coloca a mano** en el sublevel, mismo actor tag que su panel.
- **API A:** `Arm()` / `Disarm()` / dispatcher **`OnPressed`** / `SetButtonLabel(Text)`. Perillas: `LabelText`, `HoverRadius` 18, `HoldTime` (0=gatillo, >0=sostener), `bHoldByHover` (true=timbre). 🔴 nace con `bArmed=false`.
  **API B:** `Leave()`. Perillas clave por instancia: `TouchRadius` 10 / `TouchShape` (1,1,1) / `TouchOffset` — 🔴 la caja de toque **nace (0,0,0) = botón muerto** · `HoldDuration` · `AppearDistance` 700 · `OnlyOnPage` −1 · `bFinishButton` · `bStopHand`/`HandStopBias`.
- **Receta:** ver §3 (trampas 1, 2, 6). En A, si `HoldTime=0`: apagar `Ring.bVisible` en la instancia (de costado se ve como línea). En B, ajustar el gizmo `TouchGizmoBox` en el viewport (sin Play) y verificar en la instancia que `RingW` tenga `widgetClass=WBP_BellRing`, DrawSize 800×800, escala 0.05, `Transparent`, NoCollision.
- **Estado:** A 🟢 PIE end-to-end + gatillo en visor; anillo del timbre nunca mirado en escena. B (`BP_InstrButton_SC`) 🟢 hold + caja + tope de mano en visor; `HandStopBias` fino pendiente.
- **Deuda:** unificar los linajes (o al menos documentar cuál se usa cuándo — esta ficha). La simplificación acordada de `BP_Bell` (22 funciones → 11) sigue pendiente. El latch `ReArm` (una apretada por contacto: se re-arma SOLO al soltar) es obligatorio en cualquier variante nueva.

---

### 4.4 🟡 Panel de instrucciones — `BP_InstructionsPanel_SC` + `WBP_Instructions`
Manager limpio (no conoce directores por clase… en el diseño — ver deuda), motor = un `WidgetSwitcher` con TODAS las páginas de la obra.

- **Paquete:** `Core/UI/BP_InstructionsPanel_SC` + `WBP_Instructions` + `BP_InstrButton_SC` (ficha 4.3) + `M_InstrGlass` + las 5 `MI_InstrGlass_*`.
- **Enchufe:** panel y botón **en el sublevel de su sala**, con el MISMO actor tag (`instr_<sala>`); el enlace es un tag y dos búsquedas por clase. El rango de páginas vive **en la instancia** (`StartIndex`/`EndIndex`). Alguien tiene que llamar `Show()` y bindearse a **`OnFinished`** (hoy: `BP_Director_Story.ShowPanel`).
- **API:** `Apply(Index)` / `Step(Delta)` / `Advance()` / `Finish()` / `Show()` / `SetGlassVisible(On)` / `SetPractice(S)` / `SetHeartFx(S,O)` + dispatcher **`OnFinished`** (se emite AL EMPEZAR la salida, a propósito).
- **Receta:** copiar paquete → páginas nuevas = duplicar un Canvas en el `WidgetSwitcher` (cero código) → 🔴 una vez por asset en el Designer: `Fill Screen → Custom → 1920×1200` (no "Custom on Screen"; no se puede por MCP) → colocar par panel+botón en el sublevel con su tag → escribir rango, `GlassMaterial`, `ArcAngle`, `GlassOffset` en la instancia → WidgetComponent: `World` space, colisión apagada en LOS DOS campos → bindear `OnFinished`.
- **Estado:** 🟢 vidrio, colores, aparición, círculo de práctica y botón validados en visor. ⬜ textos reales en inglés (insumo de Beltrán).
- **Deuda:** ⚠ **la auditoría midió que el asset referencia `BP_Director_Movement`** — contradice el diseño ("el panel no conoce a ningún director"); hay un resto por podar antes de llamarlo portable. El widget único compartido arrastra las páginas de TODA la obra a cualquier proyecto destino (o se poda el switcher al migrar). `SetPractice`/`SetHeartFx` los empuja el director por tick: en otro nivel, ese empuje hay que replicarlo.

---

### 4.5 🔴 Beam de apuntado + far-grab — modo 4 de `BP_Sensor_Soul`
El beam en sí (trace + Niagara + publicación por mano) es motor limpio y **validado en visor**; el problema es dónde vive.

- **Paquete:** `Core/Sensor/` (BP + `M_Beam_SC` + `MI_Sensor`) + Niagara **`Stages/Touch/VFX/LineTrace`** (🔴 el beam ES este Niagara; los mesh-beams se eliminaron por decisión). Pero copiar `BP_Sensor_Soul` arrastra HOY: `BP_VRPawn_SC`, `BP_Director_Story`, `BP_ProtoSoul_SC`, `BP_BioHub`, el cluster Attracting, `BP_BrushPalette`, `BP_DrawCanvas`, `MPC_Draw`.
- **Enchufe:** pawn `BP_VRPawn_SC` obligatorio (lee los Aim por accesor) · una instancia del sensor · nivel sin colisiones fantasma (§3 trampa 4; muros con `CTF_UseComplexAsSimple`).
- **API:** `SetStage(4)` enciende / `SetStage(-1)` apaga (activación Y visibilidad de `BeamFxR/L` — `Deactivate` solo no basta: el ribbon queda congelado) · `ExploreOn(On)` / `AimBeams()` (beam sin trace) · publica por mano: `BeamStart(L)`, `BeamHitLoc(L)`, `BeamHitActor(L)`, `bBeamHit`/`BeamHitL`, `HeldOrb(L)`, `BeamEndR/L` (fin visual) · el hover es **polling** (`BeamHitActor == self`), el grab lo maneja el sensor (`BeamPress` → cast → `GrabStart` del objetivo). Knobs: `TraceDistance` 800 · `BeamRadius` 0.6.
- **Estado:** 🟢 dos beams, hover, far-grab y háptico por mano validados en visor (2026-08-26).
- **Deuda (por qué es 🔴):** (a) vive dentro del BP que contiene las 5 mecánicas; (b) **conoce por clase a `BP_SoundOrb_SC` y `BP_SaveMelody_SC`** en los casts del grab — portarlo exige reescribirlos (interfaz o tag); (c) `TickMech` es una cadena de ifs delicada. La extracción del beam como Manager propio es parte del plan (§5). Niagara: `SetNiagaraVariable` **sin** prefijo `User.` (con prefijo = no-op silencioso); `Beam_Start/End` son `NiagaraPosition`, no Vector3.

---

### 4.6 🟡 Attracting — secuenciador musical + esferas (`Core/Attracting/`)
Los motores (`BP_SoundOrb_SC`, `BP_SeqSlot_SC`, `BP_SaveMelody_SC`) están limpios; el manager (`BP_Sequencer_SC`) conoce al director, al sensor y al panel por llamada dura.

- **Paquete:** la carpeta `Core/Attracting/` completa (4 BPs + `MI_AttractSlot/Orb/Button`, maestro `M_Beam_SC`) + `Core/Audio/AttractingSounds/Module1/` (`PadM1` looping 5.333 s + los 20 clips; ojo: `M1S10v3` y `M1S18v2` reemplazan a los originales borrados) + el paquete del beam (ficha 4.5) + el panel (ficha 4.4) si se quiere la intro.
- **Enchufe:** `BP_Sensor_Soul` en modo 4 (cuatro puntos de acople: `SetStage(4)`, polling de `BeamHitActor/L`, `GrabStart` desde `BeamPress`, `SetStage(-1)` en `BeamOff`) · anclas `BP_Anchor` por tag: 20× `orb_attracting`, 1× `orb_intro_attracting`, 1× `seq_final_attracting` · 8 `BP_SeqSlot_SC` con `StepIndex` 0..7 **por instancia** y `ZoneRadius` (nace en 0) · el cierre llama `Director_Story.StepTimeDone()` — sin director hay que reapuntarlo.
- **API:** `SeqIntro()` (el arranque) · `SaveMelody()` · `NotifyPlaced(Orb)` · `SerializeMelody()` → `"paso:clip,…"`. Config por instancia: `ModuleSounds` (los 20), `PadSound`, `NumSteps` 8, `FinalPasses` 2, los 4 tags. La alineación pad↔pasos es **por construcción** (`StepDur = Duration(Pad)/NumSteps`): no se ajusta a mano; `PadM1` necesita `bLooping=true`.
- **Receta:** copiar paquetes → colocar secuenciador + 8 slots + botón + 22 anclas → escribir arrays/tags/StepIndex por instancia → disparar con `Sensor.SetStage(4)` + `MaybeInput()` + `Seq.SeqIntro()` → cierre: reapuntar `StepTimeDone` si no hay director → PIE: `SEQ: boot slots=8` → `esferas=20` → `StepDur = 0.66666`.
- **Estado:** 🟢 **mecánica completa validada en visor** (2026-08-26, iteración en vivo). ⬜ prints de diagnóstico por apagar; guarda anti-doble-grab pendiente (la 2ª mano puede robar una esfera agarrada).
- **Deuda:** los tres acoples del manager (director / sensor / panel) van por llamada dura, sin interfaz — al portarlo, esos tres puntos son lo único que se toca. La zona de snap ES la `SnapZone` visible del slot (`GetScaledSphereRadius`); `PlaceRadius` del orb está dormido.

---

### 4.7 🟢 Respiración — `BP_BreathManager_SC` + `MPC_Breath` (extraído 2026-09-17)
**El manager portable ya existe** ([tracker](../.claude/skills/unreal-vr/blueprints/BP_BreathManager_SC.md)): el motor de señal + umbral + háptica del modo 1 de `BP_Sensor_Soul`, con los valores del CDO afinado en visor, sin cast al pawn, sin directores y sin input. Primer consumidor: la galería de `/Game/TestMeshes` (7 efectos). Plan y mapeo por estación: [`PLAN-GALERIA-RESPIRACION-2026-09-17.md`](PLAN-GALERIA-RESPIRACION-2026-09-17.md).

- **Paquete:** la carpeta `Mechanics/Breath/` (manager + `MPC_Breath`) + `GrabHapticEffect` (perilla `HapticEffect`, reemplazable).
- **Enchufe:** una instancia en el nivel persistente · pawn con `CameraComponent` y SceneComponents **`HandRight`/`HandLeft` hijos de su MotionController Grip**. Nada más: no necesita hubs, input ni tags.
- **API:** variables `bBreathing` · `BreathLevel` (0..1) · `BreathDrive` (0..1, 0,5 en reposo, con el seguimiento de la esfera) · `BreathSigned` (−1..+1) · `BreathOn` · y el **`MPC_Breath`** (`Signed`, `On`, `FlowIn`, `FlowOut`) para materiales y BPs que no quieran conocer la clase. Convención de consumo (2ª pasada, suave): `valor·(1 + S·lerp(−Out, In, smoothstep((S+1)/2)))`; las velocidades se modulan sumando `Speed·(In·FlowIn + Out·FlowOut)` a la fase, **nunca** multiplicando un `Time·Speed`. 🔴 Nada de clamps duros ni funciones por tramos: el biofeedback "corta duro" (lección de Beltrán en la galería).
- **Receta:** copiar la carpeta → colocar una instancia → PIE: `BREATH: listo (camara + manos del pawn)` una vez → consumidores leen el MPC. Autoría sin gafas: `PreviewBreath` (viewport) y `bFakeBreath` (PIE).
- **Estado:** 🟢 compila estricto, dependencias medidas limpias, PIE (manos resueltas sin cast, respiración de prueba publicando, cero `Accessed None`), y consumidor de CPU medido de punta a punta. ⬜ **visor** (umbral, háptica, cambio automático de mano).
- **Deuda:** `BP_Sensor_Soul` (la obra) todavía usa su copia — migrarlo a consumidor después del visor. El resolvedor de manos va por su 4ª copia (falta `BPFL_XRHands`).

**Lo que sigue valiendo para la obra (el sensor de Entering, sin migrar):** motor+manager+etapa+háptica comparten BP con las otras 4 mecánicas, y **los ~25 valores afinados en visor viven en la INSTANCIA del nivel**, no en el CDO.

- **Paquete:** `BP_Sensor_Soul` + `MI_Sensor` (con todo lo que arrastra, ver §2) + consumidores opcionales: `BP_BreathOrb_SC` (esfera), `BP_BreathRing_SC` + `WBP_BreathRing_SC` + `M_SoulRing` + `M_BreathDot_SC` + `M_BreathWord_SC` + `MI_Word_*` + `T_Word_*` (el reloj). El sensor histórico `Stages/Breath/BP_BreathSensor_V2` es un **segundo motor divergente** (señal por inclinación, no `GeomHoriz`): decidir cuál viaja; su `Step` es NO-reescribible (solo cirugía).
- **Enchufe:** pawn con cámara + grips accesibles (`CacheHandRef`) · la mecánica arranca recién con `Take(Right)`/toma + `SetStage(1)` · la práctica la enciende el director (`SetPractice`) · el cierre NO lo hace la mecánica (lo hace el director por `StepTimes[1]` o el anillo por `BRingEnd`; `OnMechDone` está dormido). Sin OSC: **la respiración viene del mando, no del BioHub** (decisión explícita).
- **API (lo que lee un consumidor):** `BreathLevel` (0-1 continuo, 0.5 neutro) · `bBreathing` (umbral confirmado) · `Mode == 1` · `bPractice` · `bQuiet`/`bZonePre`. Consumo modelo: `BP_BreathOrb_SC` (lazy `GetActorOfClass` + cast en Tick, todo bajo `IsValid`).
- **Receta:** ficha larga — seguir los 10 pasos del tracker-extracto, con el paso crítico: 🔴 **recargar los ~25 knobs en la instancia** (los efectivos: `SafeHorizMax` 23 · `SafeVDropMin/Max` 33/63 · `ActivateDelay` 1.5 · `DeactivateDelay` 0.2 · `StillLin` 14 · `StillAng` 45 · `MinHAmp` 0.02 · `HorizTau` 3 · `TauFast` 0.4 · `HoldSlow` 0.25 · `HoldMovK` 1.0 · `TauSlow` **20** (no el 90 del papel viejo) · etc.). Copiar los números del **CDO vivo**, nunca de un doc.
- **Estado:** 🟢 el control por respiración validado en visor en varias pasadas; 🟡 el sostenido (`HoldSlow`) y el anillo completo pendientes de visor.
- **Deuda:** extraer `Breath_Manager` (2º de la fila, tras Drawing): motor de señal (`HeadGeom`+`UpdateLevel`+`BreathThreshold`) + publicación (`BreathLevel`/`bBreathing`) sin metas ni práctica ni háptica. Subir los valores de instancia al CDO del módulo al extraer. La calibración dormida (`BreathGate` la puentea) viaja como peso muerto.

---

### 4.8 🔴/🟢 Latido — modo 2 de `BP_Sensor_Soul` + `BP_Elevator_SC`
El motor está enterrado igual que breath (🔴), pero el **patrón consumidor es el mejor del proyecto** (🟢): `BP_Elevator_SC` escucha un dispatcher y nada más.

- **Paquete:** `BP_Sensor_Soul` + `BP_BioHub` (la fuente del BPM — el sensor NO detecta latido: detecta la mano en el pecho y le pone reloj a `HeartSmooth`) + `Core/Audio/Sounds/HeartBeat` + consumidor (`Core/Rooms/BP_Elevator_SC` como modelo).
- **Enchufe:** BioHub colocado en el persistente (sin él `bBioOk=false` y no hay beats) · sensor tomado + `SetStage(2)` · para el ascensor: meshes tagueados `rise` + marcadores `rise_top`/`rise_bottom` (el bottom lleva también `rise`), `ElvArm()` desde el director, cierre a `StepTimeDone()`.
- **API:** dispatcher **`OnBeatPulse`** (cada medio latido, `BeatDiv` 2) — 🔴 el bind del pin Delegate va **por cirugía** (el DSL no puede) · `bHeartZone` (bool del umbral) · `BeatEnv` (envelope 1→0, decae a `BeatEnvDecay` 2.5). Zona de pecho: `HeartHorizMax` 25 / `HeartVDropMin` 10 / `HeartVDropMax` 45 — ⚠ puestos A OJO, sin respaldo de datos. Knobs del consumidor: `PulseKick` 110 · `CoastSpeed` 20 · `LandRate` 6 (frenada √distancia — la exponencial "no llega nunca", rechazada en visor).
- **Receta:** colocar BioHub → sensor con knobs de heart en la instancia → `SetStage(2)` → consumidor: cachear sensor por cast con timer de arranque (0.5 s: el sensor puede no existir en BeginPlay) + bind a `OnBeatPulse` → taguear meshes → `ElvArm()` → PIE con `HeartVDropMin=0` en la instancia (en escritorio la mano queda a la altura de la cámara y la zona real nunca abre).
- **Estado:** 🟢 cadena completa beats→kicks→subida→cierre verificada en PIE; frenada validada en visor. ⬜ la zona de pecho y el feedback (zumbido+pulso+audio) nunca validados en visor.
- **Deuda:** extraer `Heart_Manager` (3º de la fila, junto a Mind — ambos son "OSC + zona"). La salida de zona es instantánea (sin debounce — si parpadea en visor, copiar el `DeactivateDelay` de breath). Si el intervalo real del OSC difiere del fake, revisar `PulseKick` (la subida está calibrada a ~90 s).

---

### 4.9 🟢 Hubs de soporte — `BP_AudioHub` / `BP_HapticHub`
Motores puros; el único acople es que **son actores que hay que colocar** — y esa es la decisión a documentar.

- **Paquete:** `Core/Audio/BP_AudioHub` + `BP_HapticHub` + las carpetas de audio que se usen.
- **Enchufe:** una instancia de cada uno en el persistente; consumidores con `GetActorOfClass` cacheado.
- **API AudioHub:** `PlaySfx(Name)` / `PlaySfxAt(Name, Loc)` / **`PlayVo(Index) → Seconds`** (devuelve la duración o −1: los tiempos del guión cuelgan del clip) / `PlayAmbient(Name, FadeTime)` con crossfade real. Catálogo por instancia: `SfxMap` (Map String→SoundBase), `AmbientMap`, `VoClips`. Vacío = todo corre + log de la falta.
  **API HapticHub:** `HapticHover` (0.15/0.06 s) · `HapticSelect` (0.7/0.12 s) · `HapticHold(bRight, bOn)` (0.35 continuo) · `bEnabled` global. La mano viaja como `bool bRight` (un enum no entra por cable).
- **🔴 La decisión de diseño (Beltrán, y tenía razón):** el HapticHub sirve para consumidores que YA viven en el persistente; para **actores de sublevel o portables, el patrón correcto es `PlayHapticEffect` directo al PlayerController** (no depende de nada colocado). Así migró el timbre — y por eso vibra en cualquier nivel.
- **Estado:** 🟢 verificado por log con catálogo vacío y con Loving/ceremonia cableados. ⬜ nunca en visor; catálogo real por cargar (insumo de Beltrán).
- **Deuda:** consumidores sin migrar (Breath, Heart, Attracting, Intro, Hall siguen con clips locales). `SetHapticsByValue` continuo PISA los pulsos (mismo canal): el pulso viaja EN el zumbido (`lerp(amp, 1.0, BeatEnv)`), no en canal aparte.

---

## 5. El plan de extracción (el camino a "instantáneo")

Orden acordado con Beltrán (*"Vamos uno a uno. Probamos, y resolvemos"*): **Drawing → Breath → Heart/Mind**. Regla de método: **mover el código probado en visor, no reescribirlo.**

| # | Paso | Qué produce | Estado |
|---|---|---|---|
| 1 | **`BPC_DrawTool`** extraído del modo 5 del sensor; `BP_ControllerRig` como primer consumidor | Drawing = Manager real: One-Euro + calma + paleta, sin input propio (`Press`/`Release`/`SetTip`) | 🟢 **construido y verificado en PIE (2026-09-04)** — componente `Stages/Movement/BPC_DrawTool` (Setup/Press/Release/ToolTick + One-Euro + calma real), rig migrado como consumidor, ambos compilan estricto. Aserción sobre valores efectivos: `TipRef`, `HandMC`, `CanvasRef` (uno por herramienta) y la config llegan bien a las dos instancias. ⬜ **falta VISOR**. Deuda menor: la paleta sigue fija por `Setup` |
| 2 | Desatar `BP_BrushPalette` del pawn (`FindHand` en vez del cast a `BP_VRPawn_SC`) | paleta portable | 🟢 **hecho 2026-09-04**: `AcquireControllers` ya no castea al pawn — usa `PalGrip(Right)` (mismo patrón que `FindHandMC`). 🔴 **Medido con `get_dependencies`: `BP_VRPawn_SC` DESAPARECIÓ de las dependencias de la paleta.** ⬜ falta ejercitarla (no hay paleta colocada en TestMeshes; la spawnea el sensor en la obra) |
| 3 | **`Breath_Manager`**: motor de señal + `BreathLevel`/`bBreathing` publicados; valores de instancia subidos al CDO del módulo | Breath portable; el sensor de la obra pasa a ser un consumidor más | 🟢 **construido 2026-09-17** como `Mechanics/Breath/BP_BreathManager_SC` + `MPC_Breath` (señal, umbral, háptica, mano automática, vista previa y respiración de prueba), verificado en PIE y con `get_dependencies` limpio. ⬜ visor · ⬜ migrar `BP_Sensor_Soul` a consumidor |
| 4 | **`Heart_Manager`** (zona + reloj sobre `BioHub.HeartSmooth`, publica `OnBeatPulse`/`BeatEnv`) y **Mind** (BioHub ya lo es) | Heart/Mind portables | ⬜ |
| 5 | El beam como Manager propio; los casts a orb/botón reemplazados por interfaz o tag | Attracting deja de necesitar al sensor completo | ⬜ |
| 6 | Podar la referencia de `BP_InstructionsPanel_SC` a `BP_Director_Movement` (medida hoy, contradice el diseño) | panel realmente limpio | ⬜ |
| 7 | Cada extracción cierra con: tracker actualizado + fila en §2 re-medida (`get_dependencies`) + esta página al día | el doc no se pudre | regla |

**El criterio de "listo":** una mecánica está empaquetada cuando su ficha de §4 se puede ejecutar de punta a punta en un nivel virgen sin abrir ningún tracker, y `get_dependencies` de su Manager no lista ni al pawn de la obra ni a ningún director.

### 🖐️ El resolvedor de manos — la pieza compartida que falta (decidido 2026-09-04)
Todos los managers portables necesitan lo mismo: **"dame la mano / el MotionController de este lado, sin castear al pawn de la obra"**. Hoy esa lógica está **una vez en `BP_ControllerRig`** (`FindHand` + `FindHandMC`, ambas probadas) y **duplicada como cast duro en `BP_BrushPalette.AcquireControllers`** (que castea a `BP_VRPawn_SC` y usa sus accesores). Breath y Heart la van a necesitar igual.

**La decisión:** extraerla a una **Blueprint Function Library** (`Core/Pawn/BPFL_XRHands`) con dos funciones estáticas, y que todos la llamen:
- `FindHandComp(bRight) → SceneComponent` — recorre `GetComponentsByClass(pawn, SceneComponent)` y devuelve aquel cuyo **`GetObjectName`** sea `HandRight`/`HandLeft` (nunca `GetDisplayName`, que viene decorado).
- `FindHandGrip(bRight) → MotionControllerComponent` — el **`GetAttachParent`** del anterior, casteado. Funciona porque las manos son hijas de su Grip; verificado en PIE el 2026-09-04.

Con eso, el contrato del Controller (§1.2, "solo el Controller conoce al pawn") pasa a vivir en **un solo archivo** y cambiar de pawn deja de tocar N Blueprints.

⚠ **Estado: sin construir.** El intento del 2026-09-04 dejó el editor con el servidor MCP bloqueado (`create` de un `BlueprintFunctionLibrary` no devolvió nunca; el proceso seguía vivo y respondiendo, el puerto abierto, pero sin responder HTTP). **No quedó ningún asset a medias.** Al retomar: crear la library, migrar `BP_BrushPalette.AcquireControllers` a `FindHandGrip`, y **recién después del visor** migrar también el rig a la library (hoy tiene su copia local, que es la probada — no tocarla antes del test).
