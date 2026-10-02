# Partitura de la Obra · `DA_Partitura_Obra`

> Generado por `tools/unreal/gen_partitura_doc.py` desde `tools/unreal/partitura_def.py`. No editar a mano.

**Qué es:** el único lugar donde viven los tiempos narrativos de la Obra (cuándo entra Alma, cuánto duran
las instrucciones, cuándo se le pide a una etapa que cierre, el final, los créditos...). La Obra
(`BP_Obra_SC`) y los ensayos de cada etapa (`BP_StageRunner_SC`) la leen al arrancar.

**Cómo se ajusta:** en el editor, abrir `/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra` (doble clic),
cambiar el número, **guardar**. No hace falta tocar ningún Blueprint. Después: `python tools/unreal/smoke_obra.py`
y probar en el visor. Las variables de la categoría *Partitura* dentro de `BP_Obra_SC` son **copias de trabajo**:
se pisan al arrancar con lo que dice el DA. No se editan.

**Unidades:** segundos del reloj del director. `PT` = tiempo dentro de la fase actual; `T` = tiempo de la etapa
(en la fase 0 el reloj de la etapa salta a 9 cuando entra Alma). Las perillas *por etapa* son 5 números en orden:
Entering, Recognizing, Loving, Attracting, Surrounding.

## 1 Inicio y Hall

| Perilla | Valor inicial | Qué hace |
|---|---|---|
| `Aviso_Dur` | 19 | Duración del aviso de prototipo (fase 16), si bDisclaimer. |
| `Titulo_Aparece` | 2,5 | Cuando se coloca el título SOUL CHARGER en el Hall (PT de la fase 9). |
| `Titulo_RevelaIni` | 3 | El título empieza a revelarse. |
| `Titulo_RevelaFin` | 6,5 | El título termina de revelarse. |
| `Bajada_RevelaIni` | 5 | La bajada (subtítulo) empieza a revelarse. |
| `Bajada_RevelaFin` | 7,5 | La bajada termina de revelarse. |
| `Logos_RevelaIni` | 6 | Los logos empiezan a revelarse (JHU +0,3 s, IDEAS +0,6 s). |
| `Logos_RevelaFin` | 8 | Los logos terminan de revelarse. |
| `Titulo_SaleIni` | 17 | Título, bajada y logos empiezan a irse. |
| `Titulo_SaleFin` | 19,5 | Título, bajada y logos terminan de irse. |
| `Titulo_Fin` | 20 | Se oculta el actor del título. |
| `Hall_VeloAbreIni` | 3,5 | El velo negro empieza a abrir a la niebla del Hall. |
| `Hall_VeloAbreFin` | 5,5 | El velo termina de abrir en el Hall. |
| `Hall_IntroA` | 3 | Cuando la Obra le dice al Hall que arranque (HallIntro). |
| `HUD_EEGRetardo` | 1 | Cuánto después de nacer el HUD nace la línea del EEG. |

## 2 Cada etapa

| Perilla | Valor inicial | Qué hace |
|---|---|---|
| `Etapa_VeloAbreIni` | 1 | El velo de color empieza a abrir la etapa (T). |
| `Etapa_VeloAbreFin` | 4 | El velo termina de abrir la etapa. |
| `Etapa_TituloRevelaIni` | 0,5 | El título de la etapa empieza a revelarse. |
| `Etapa_TituloRevelaFin` | 1,8 | El título de la etapa termina de revelarse. |
| `Etapa_TituloSaleIni` | 4,6 | El título de la etapa empieza a irse. |
| `Etapa_TituloSaleFin` | 5,6 | El título de la etapa termina de irse. |
| `Etapa_TituloOculto` | 5,7 | Desde aca el título de la etapa queda oculto. |
| `Alma_Entra` | 5,5 | Cuando entra Alma (fin de la fase 0; el reloj de la etapa salta a 9 en ese momento). |
| `Alma_VozRetardo` | 1,5 | Cuánto espera Alma para empezar a hablar al llegar. |
| `Alma_TrasVoz` | 3 | Cuánto queda Alma después de su voz antes de las instrucciones. |
| `Instr_Dur` | [8,5, 6, 6, 6, 0,6] | Tiempo de instrucciones antes de StageBegin, por etapa. |
| `Instr_EsperaMax` | 20 | Attracting: tope de espera a las voces de la consigna antes de empezar. |
| `Etapa_Tope` | [240, 180, 120, 240, 205] | A los N s de mecánica la Obra le PIDE a la etapa que cierre por su propio camino (Attracting guarda la melodía, Surrounding presenta el dibujo). |
| `Corte_Espera` | 30 | Si la etapa no cerro N s después del pedido, se cierra igual (tope de seguridad). |
| `Salida_Dur` | [2,5, 2,5, 2,5, 2,5, 2,5] | Salida de la etapa (StageOutro) antes de la carga; nunca menos que la voz + Salida_TrasVoz. |
| `Salida_TrasVoz` | 0,6 | Margen después de la voz de felicitacion antes de la carga. |
| `Carga_Dur` | [4, 4, 4, 4, 6] | Duración de la carga del anillo por etapa (la ultima es la carga final). |
| `Carga_Minima` | 1 | Mínimo de la fase de carga antes de poder cerrarla. |
| `Despedida_Retardo` | 0,9 | Cuánto espera Alma para invitar a la siguiente etapa. |
| `Despedida_TrasVoz` | 1,3 | Cuánto queda Alma después de la invitación antes de irse. |
| `Velo_CierreDur` | 2,5 | Cuánto tarda el velo en cerrar la etapa antes de pasar a la siguiente. |

## 3 Simulado

| Perilla | Valor inicial | Qué hace |
|---|---|---|
| `Sim_EtapaMax` | 90 | Con bSimulated: a Attracting y Surrounding se les pide cerrar a los N s (en vez de Etapa_Tope). |

## 4 Final

| Perilla | Valor inicial | Qué hace |
|---|---|---|
| `Final_NegroRampa` | 2 | En la carga final, cuánto dura la rampa a negro (termina con la carga). |
| `Regreso_HallA` | 0,3 | Cuando, ya en negro, se salta al Hall para el regreso. |
| `Regreso_VeloIni` | 0,2 | Regreso: el velo empieza a abrir. |
| `Regreso_VeloFin` | 1,4 | Regreso: el velo termina de abrir. |
| `Regreso_PezA` | 1,6 | Regreso: cuando el alma sale como pez y el Hall la sigue. |
| `Res_AlmaA` | 0,5 | Resultados: cuando llega Alma y empieza su lectura (VO_34b). |
| `Res_PezMin` | 1,8 | Resultados: mínimo antes de que el alma se asiente en su anillo. |
| `Res_PezMax` | 3,4 | Resultados: el alma se asienta a mas tardar a los N s. |
| `Res_GusanoA` | 2 | Resultados: cuando suena la melodía (gusano). |
| `Res_Explorar` | 25 | Resultados: tiempo para explorar después de la lectura de Alma. |
| `Res_InvitaRecorte` | 1,2 | Los botones aparecen N s antes de que termine la invitación a compartir. |
| `Res_BotonesVoz` | 1,8 | Cuánto después de aparecer los botones habla Alma (VO_36p). |
| `Res_SalidaRetardo` | 0,5 | Cuánto después de elegir se va el cuadro. |
| `Res_Cortafuegos` | 30 | Si nadie elige SHARE/DON'T SHARE en N s, se elige solo. |
| `Res_Tope` | 150 | Cortafuegos de toda la fase de resultados. |
| `Comp_Nado` | 4 | SHARE: cuánto nada el alma hasta la puerta. |
| `Comp_Lejos` | 3 | SHARE: cuánto tarda el alma en irse por la puerta. |
| `Salida_HallA` | 0,5 | Cuando arranca la salida del Hall hacia la constelación. |
| `Const_AlmaLlega` | 5 | Constelación: cuando aparece tu alma (si compartiste). |
| `Const_Voz35` | 8 | Constelación: cuando suena VO_35b. |
| `Const_Voz37TrasVoz` | 0,6 | Constelación: margen entre VO_35b y VO_37. |
| `Creditos_Dur` | 60 | Duración de la constelación con créditos. |
| `Fundido_Dur` | 3,5 | Fundido final antes de reiniciar la obra. |

## Lo que NO está en la Partitura (y dónde vive)

- **Dónde pasa cada cosa** (Alma, la carga, el título de cada etapa): los TargetPoints `sc<K>_alma_in`, `sc<K>_alma_side`,
  `sc<K>_charge`, `sc<K>_title` en el nivel de test de cada etapa. Se mueven en el viewport.
- **El color del velo de cada etapa** (`CTop`/`CHor`): en el `BP_StageRunner_SC` del nivel de test de la etapa.
- **Cómo se ve y se siente cada mecánica**: sus perillas, en su Blueprint o en la instancia de su nivel de test. Ver `docs/PERILLAS.md`.
- **Coreografías internas** (la carga del anillo, el nado del alma en SHARE, la presentación del dibujo): sus Blueprints.
- **Tiempos acoplados a la animación de la carga final** (`ReadCharge` 5,6 + carga, `FlowVeil` 5,5 + carga): quedan en el grafo,
  pero ya son relativos a `Carga_Dur[4]`: si se cambia la carga final, se mueven solos.

