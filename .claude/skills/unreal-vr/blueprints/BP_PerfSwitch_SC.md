# BP_PerfSwitch_SC — el conmutador del banco de medición (Core/Debug/)

> Creado el 2026-09-25. **Herramienta de medición, no es parte de la obra.**
> Estado: 🟢 **verificado en el device** (los 4 modos contestan por logcat).

## Qué es
Un actor sin componentes cuyo único trabajo es **recibir un comando de consola y escribir el escalar
`PerfMode` de la colección [[MPC_Perf_SC]]**, que es la que el shader de blobs lee para cambiar de
modo. Vive en `TestMeshes` como el actor **`PerfSwitch`**.

Contexto completo del banco (qué decide, por qué está armado así):
[`docs/PLAN-PERF-ATTRACTING.md`](../../../../docs/PLAN-PERF-ATTRACTING.md), sección "EL BANCO DE MEDICIÓN".

## Estructura — todo el grafo
| Evento | Qué hace |
|---|---|
| `EventBeginPlay` | print `PERF: banco listo` + `PerfMode = 0` (cada arranque parte de la obra) |
| `Custom|Perf0` | print + `PerfMode = 0` — el material tal como está autorado |
| `Custom|Perf1` | print + `PerfMode = 1` — `Steps` a la mitad |
| `Custom|Perf2` | print + `PerfMode = 2` — SDF lisa, sin wobble ni decoración |
| `Custom|Perf3` | print + `PerfMode = 3` — el material sale sin dibujar (el piso) |

Sin variables. Sin Tick. Cada evento son dos nodos: el `PrintString` y la escritura de la colección.

## Cómo se dispara
```
adb shell "am broadcast -a android.intent.action.RUN -e cmd 'ke * Perf3'"
```
`ke` = `KISMETEVENT`. 🔴 Vive en `UEngine::Exec_Dev` bajo `#if !UE_BUILD_SHIPPING`
(`UnrealEngine.cpp:5838`) → **anda en Development, NO en Shipping.** Si algún día se mide sobre un
build Shipping, este mecanismo no existe y hay que cambiarlo por una cvar.

## Trampas pagadas al construirlo
1. 🔴 **El nodo que escribe la colección colisiona por nombre.** `find_node_types` devuelve
   `Rendering|Material|SetScalarParameterValue` **dos veces**, y el DSL agarra el de
   **MaterialInstanceDynamic** (su pin `self` es un MID, no sirve). El bueno se crea por cirugía con
   **`declaring_class = /Script/Engine.KismetMaterialLibrary`**; se reconoce porque la clase queda
   `K2Node_CallMaterialParameterCollectionFunction` y sus pines son `Collection`/`ParameterName`/
   `ParameterValue`. Ver gotcha §380.
2. ⚠ **`parameterId` del `CollectionParameter` NO es escribible ni legible** — el `set_properties`
   falla con "could not be set" y la excepción **escapa del script** (dispara Undo). Se setean solo
   `collection` y `parameterName`; el id lo deriva el motor. El canario del nivel salvó la pasada.
3. 💡 El print de cada evento **es el control positivo** del instrumento: el script de medición
   dispara un modo y **aborta si no ve el eco en logcat**. Sin eso, las fases no cambiarían nada y
   la medición saldría plausible y falsa.

## TODO
- [ ] Correr la medición (`quest_perfmodes.ps1`) y anotar acá el veredicto.
- [ ] Cuando la decisión esté tomada: decidir si el banco se queda (útil para futuras estaciones) o
      se saca. 🔴 Sacar actores **se pregunta** — regla del proyecto.
