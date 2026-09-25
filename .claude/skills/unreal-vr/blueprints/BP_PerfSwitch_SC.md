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
| `Custom|Perf4` | 🆕 2026-09-25: print + `PerfMode = 4` — **solo cadena** (las 20 esferas no dibujan) |
| `Custom|Perf5` | 🆕 2026-09-25: print + `PerfMode = 5` — **solo esferas** (la cadena no dibuja) |

Sin variables. Sin Tick. Cada evento son dos nodos: el `PrintString` y la escritura de la colección.

**Los modos 4/5 son EL SPLIT** de los 12,28 ms medidos: parten el costo entre cadena y esferas.
El discriminante vive en el shader: `WobAFS.x > 0.001` = esfera (`MI_OrbBlob_SC` trae 0,09),
`= 0` = cadena (el MID del `Volume` usa el default 0 del master). Verificado por preview de asset
en los dos caminos (`perf_shots/SPLIT45_*`): modo 4 vacía el preview del MI y deja el del master;
modo 5 al revés; modo 0 restaura ambos. Se corre con `quest_perfmodes.ps1 -Modos 0,4,5,3` y
`resumen_modos.py` imprime la cuenta (piso derivado `m4+m5-m0`, que esquiva el cap del vsync).

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

4. 🆕 2026-09-25 (al agregar Perf4/Perf5): **dos errores de VALIDACIÓN de argumentos escaparon del
   `try/except BaseException` del script y NO dispararon Undo** (log `LogEditorTransaction` vacío,
   y el `set_properties` previo del mismo script sobrevivió). O sea: la excepción que escapa por
   argumento inválido parece ser pre-transacción. **No relaja la regla §60** (2 muestras contra un
   incidente real): seguir con la plantilla y el canario, pero ante un escape así, verificar el
   estado real antes de asumir pérdida.

## TODO
- [x] Correr la medición del split (2026-09-25 14:47). **Veredicto: LA CADENA DOMINA — ≥8,93 ms
      (≥61%) vs 5,81 ms exactos de las 20 esferas; solo-esferas clava 72 fps.** El modo 4 pasa a
      ser el A/B directo para iterar la cadena (`-Modos 0,4`). Detalle y plan reordenado en
      `docs/PLAN-PERF-ATTRACTING.md`.
- [x] Correr la medición (`quest_perfmodes.ps1`) — hecha el 2026-09-25 (mañana), resultado en el plan.
- [ ] Cuando la decisión esté tomada: decidir si el banco se queda (útil para futuras estaciones) o
      se saca. 🔴 Sacar actores **se pregunta** — regla del proyecto.
