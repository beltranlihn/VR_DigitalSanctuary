# Plan — el secuenciador como mecánica PORTABLE (2026-09-27)

> Pedido de Beltrán: *"que los blueprints que aplican al sequencer sean todos migrables y que si yo lo arrastro a cualquier otro proyecto con un VR Pawn reconozcan instantáneamente el VR Pawn y funcione toda la mecánica"* + un sensor **propio de esta etapa** (line trace, selección, interacción con esferas y secuenciador) + el botón de guardado con **animación de salida**, **reaparición animada en un target point** (transform completo) que suena, da vueltas y desaparece, y **la data guardada** para poder volver a ver ese secuenciador en otra etapa.

---

## 1. Diagnóstico medido (no de memoria)

`get_dependencies` corrido hoy sobre el cluster. Lo que **arrastra otras etapas**:

| Blueprint | Dependencias que sobran |
|---|---|
| `BP_Sequencer_SC` | **`BP_Sensor_Soul`**, **`BP_Director_Story`**, **`BP_InstructionsPanel_SC`** |
| `BP_SoundOrb_SC` | **`BP_Sensor_Soul`**, `BP_SlotChain_SC` (el raymarch viejo, parkeado) |
| `BP_SaveMelody_SC` | **`BP_Sensor_Soul`** |
| `BP_SeqSlot_SC` | `BP_SlotChain_SC` |
| `BP_OrbDirector_SC` | `BP_Anchor` (las anclas, ya sin uso con el domo) |

`BP_Sensor_Soul` es **el nudo del proyecto**: 90 funciones, 5 mecánicas (toma del alma, respiración, latido, dibujo, beam), y conoce por clase al pawn de la obra y al director. Migrar el secuenciador hoy se lleva media obra.

Del sensor, el secuenciador usa **solo** esto (validado en visor):
- el **puntero estilo Quest** (`BuildPointer`, `SetupPtrComp`, `DrawBeamR/L`, `ShowPointer` + `M_Pointer_SC` / `M_PointerDot_SC`),
- el **trace por mano** (`TickBeamR/L`) y lo que publica (`BeamStart`, `BeamHitLoc`, `BeamHitActor`, `BeamDir`… ×2 manos),
- el **agarre y el botón** (`BeamPress/Release`, `BeamGrabTry`, `GrabTryL`, `BeamBtnTry`, `BtnTryL`, `DropOrb*`, `DropBtn`, `HeldEndR/L`),
- el **input** (`EnsureInput`/`MaybeInput`) y el háptico (`Pulse`).

⚠ **El input de hoy no viaja**: llega por `IA_Shoot_*` gracias a `IMC_Weapon_*` declarados en `Config/DefaultInput.ini` **de este proyecto**. En otro proyecto no existen.

---

## 2. La arquitectura propuesta

Modelo: **`BP_TBDrawRig`** (el dibujo de Neural Canvas, validado en visor el 2026-09-26): *un actor que se coloca en el nivel y nada más*; busca los mandos solo, trae su propio input y no toca el pawn.

```
┌─ BP_SeqRig_SC ── "el sensor de la etapa" (NUEVO) ──────────────────────┐
│  • encuentra el pawn poseído y sus MotionControllers por MotionSource    │
│    (RightAim/LeftAim, respaldo Right/Left) → sirve para BP_XRPawn,       │
│    BP_VRPawn_SC o el VRPawn del template de Epic, sin castear a nadie    │
│  • trae SU input: IA_SeqTrigger_L/R + IMC_Seq (en el paquete),           │
│    registrado con EnableInput + AddMappingContext, reintentando en Tick  │
│  • puntero ×2, trace, hover, agarre, botón, háptico directo al PC        │
│  • API: Activate() / Deactivate() / Press(bRight) / Release(bRight)     │
└──────────────────────────────────────────────────────────────────────────┘
        │ publica BeamStart/HitLoc/HitActor por mano (mismos nombres de hoy)
        ▼
 BP_Sequencer_SC ── BP_SoundOrb_SC ── BP_SeqSlot_SC ── BP_SaveMelody_SC
 BP_OrbDirector_SC (domo + look + sonidos) ── BP_BlobChain_SC (el gusano)
        │
        │ al guardar: SG_Melody_SC  (SaveGame NUEVO)
        ▼
 BP_MelodyReplay_SC (NUEVO) ── reconstruye la melodía desde la data,
   en el transform de un TargetPoint: aparece, suena, gira, desaparece.
   El MISMO actor sirve después, en cualquier otra etapa, para volver a verla.
        │
        └─ dispatcher OnMelodyFinished  ← lo escucha la ETAPA (no viaja)
```

**Qué NO viaja** (capa de etapa, queda en Soul Charger): avisarle a `BP_Director_Story`, el panel de instrucciones de la obra, `BP_SoulArchive_SC` (el retrato de toda la experiencia — se mantiene funcionando como hoy).

🔄 **Cambia una regla vieja del proyecto:** *"una mecánica portable nunca es dueña del input"* (2026-09-04). Tu pedido de hoy — arrastrar y que funcione — es el contrato del rig de dibujo, que **sí** trae su input. Propuesta: el rig trae input por defecto **y** expone `Press`/`Release` públicos con una perilla `bOwnInput` para que un anfitrión pueda manejarlo con otro gatillo.

---

## 3. Las fases (cada una termina verificada antes de seguir)

### Fase 0 — Punto de guardado
🔴 **Todo lo de hoy está sin commitear** (base `8605ecb`): sombreado, domo, agarre, sonidos en el director. Antes de un refactor de este tamaño, **commit** para tener a dónde volver.

### Fase 1 — `BP_SeqRig_SC`, el sensor de la etapa
- Se construye **nuevo**, copiando función por función el código **probado en visor** del sensor (leer → escribir en grafos nuevos → verificar pines con `get_node_infos`). No se re-inventa.
- Lo que cambia respecto del sensor: **encontrar las manos** (por `MotionSource`, no por el accesor de `BP_VRPawn_SC`) e **input propio** (duplicando `IA_Shoot_*` → `IA_SeqTrigger_*` y un `IMC_Seq` dentro del paquete).
- Háptico: `PlayHapticEffect` directo al PlayerController (el patrón portable ya decidido; no depende de hubs colocados) con su efecto copiado al paquete.
- ✅ Aceptación: en `Test_Sequencer`, con el rig en lugar del sensor, hover + agarre + botón idénticos a hoy (PIE + visor).

### Fase 2 — Desatar el cluster
- `SoundOrb`, `SaveMelody`, `Sequencer`: la referencia `SensorRef` (clase `BP_Sensor_Soul`) pasa a `RigRef` (clase `BP_SeqRig_SC`). Mismas variables publicadas → el cambio es **de clase**, no de lógica. Se cuentan todos los nodos `Class|BPSensorSoul|…` antes y se verifica que queden en cero.
- `TellDirector` → dispatcher **`OnMelodyFinished`** (la obra se engancha desde afuera).
- Panel de instrucciones → sale de la mecánica. Hoy ya funciona sin panel ("*el panel se fue sin confirmar - completo la intro*"); queda un verbo público `ConfirmIntro()` + dispatcher `OnIntroShown` para la etapa que quiera panel.
- Podar `BP_SlotChain_SC` de `SoundOrb`/`SeqSlot` y `BP_Anchor` del director (legado sin uso).
- ✅ Aceptación: `get_dependencies` de los 6 BPs **no lista** `Sensor_Soul`, `Director_Story`, `InstructionsPanel`, `VRPawn_SC`, `SlotChain`, `Anchor`.

### Fase 3 — La data guardada: `SG_Melody_SC`
Guarda **lo que hace falta para reconstruir la melodía en cualquier lado**, no números de clip:
- por paso: **el sonido** (referencia al asset), **el color**, **el tamaño**, ocupado sí/no, **la posición del slot relativa al secuenciador** (para que la forma sea la misma);
- global: `PadSound`, `NumSteps`, duración del paso, fecha.
- Perilla `SaveSlotName` (default `SC_Melody`). API: `SaveMelodyData()` en el secuenciador, `LoadMelody(Slot)` en el replay.
- ✅ Aceptación: guardar en PIE → cerrar PIE → otro PIE carga los mismos sonidos y colores (round-trip de disco).

### Fase 4 — El cierre animado
Al presionar **Save Melody** (o terminar la melodía):
1. las esferas sueltas desaparecen (ya existe);
2. **se guarda la data**;
3. **animación de salida** de la mesa con sus esferas y el gusano (encoge + se desvanece en su lugar, el pad se apaga);
4. aparece **`BP_MelodyReplay_SC` en el target point** `seq_final_attracting` con **su transform completo** (posición, rotación **y escala**) — hoy el cierre solo usa la posición;
5. el replay **crece**, **suena** las pasadas (`FinalPasses`), **gira** (`SpinTurns`, `SpinSpeed`), **encoge y desaparece**;
6. dispara `OnMelodyFinished`.
- Perillas del replay: tiempos de entrada/salida, vueltas, velocidad de giro, pasadas, `bAutoPlay` y `bLoop` (para usarlo como "vitrina" en otra etapa).
- ✅ Aceptación: la secuencia completa en PIE y en visor; el replay colocado solo en otro nivel carga y suena la melodía guardada.

### Fase 5 — Prueba de portabilidad real
- Nivel virgen `L_SeqPortableTest` con **`BP_XRPawn`** (el pawn genérico del XRFramework, que no sabe nada de Soul Charger), sin director, sin sensor, sin hubs. Colocar el kit → PIE → funciona.
- `get_dependencies` transitivo del kit: lista cerrada y documentada.
- Ficha 4.6 de `docs/MECANICAS-PORTABLES.md` reescrita como receta de "arrastrar y usar"; trackers al día.
- (Opcional) mover el kit a `Content/SoulCharger/Mechanics/Sequencer/`, como `Mechanics/Breath/`, con redirectores. Para `Migrate` no hace falta (arrastra por dependencias, no por carpeta), pero ordena.

### Fase 6 — Volver a enchufarlo a la obra
En `L_SoulCharger_V3` la etapa usa el rig en vez del modo 4 del sensor, y el director de la obra escucha `OnMelodyFinished`. El modo 4 del sensor se apaga para el secuenciador (no se borra: la obra tiene otras cosas que dependen del sensor).

---

## 4. Riesgos conocidos
- **Portar grafos por MCP**: el `read_graph_dsl` es lossy en algunos pines (gotcha "DSL read oculta pines") y confunde nombres entre clases (gotcha 422). Mitigación: portar función por función, verificar cada pin crítico con `get_node_infos`, y probar en PIE después de cada bloque.
- **Scripts que fallan deshacen trabajo** (gotcha 418): transacción de sacrificio + llamadas directas para leer/guardar.
- **Perillas que nacen en cero** en instancias colocadas: cada actor nuevo se verifica leyendo la instancia.
- **El input en otro proyecto**: un IMC con prioridad baja puede ser tapado por el del template; se registra con prioridad alta y se autoverifica con `HasMappingContext` (receta probada del sensor).
