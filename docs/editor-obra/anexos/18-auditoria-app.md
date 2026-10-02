# Anexo 18 · Auditoría de la app del editor (2026-10-02)

**Pregunta de Beltrán:** ¿está bien construida, es fácil de usar, o terminaremos rompiendo constantemente la experiencia?

**Método.** Un workflow de 8 agentes:
- **Cuatro auditores:** código y datos, integridad, usabilidad para el socio, y arquitectura y camino a Unreal.
- **Un verificador adversarial por auditor:** intentó refutar cada hallazgo con experimentos en node contra la partitura real y, en usabilidad, en el navegador.
- **Resultado:** 54 hallazgos, de los que 36 se confirmaron, 18 se confirmaron en parte y ninguno se refutó. Los verificadores sumaron 13 que se habían escapado.
- **Comprobación propia:** reproduje el más grave (A1). Al borrar PASO, el momento 2.7b pasa de 2:36 a 0:00 y el total baja de 16:58 a 14:21.

## Veredicto

**El núcleo está bien construido:**
- El motor de tiempos es puro y está verificado (665/665).
- Toda edición pasa por un solo `commit()`, con deshacer y rehacer.
- El servidor es prudente: escribe con .tmp, guarda historial y valida los WAV.
- El conocimiento de Unreal vive fuera del código, en `contract.json`.
- La interfaz se siente como un NLE: imán, fantasma rojo, ayuda contextual y el chrome de ISP.

**Así como está, sí terminaría rompiendo la obra.** Hay cuatro motivos:

1. **Borrar con "Proceed and repair" corrompe la partitura.** Afecta a 20 de los 73 momentos: los que están anclados a un elemento. Si se borra ese elemento, el momento cae a 0:00 y arrastra al resto de la obra. "Delete them too" puede borrar hasta el 62 % de la obra. El 10-02 dije que la reparación "conserva los tiempos exactos": es cierto para los elementos, **falso para los momentos**.
2. **Se puede perder trabajo entre dos personas:**
   - al guardar gana el último;
   - el borrador local se restaura o se descarta solo por número de revisión;
   - la pestaña 3D deja editar, pero lo que se edita ahí se pierde.
3. **La integridad está mal calibrada: grita donde no importa y calla donde importa.**
   - **Grita:** cualquier VO abre la tarjeta con un empujón de 0,1 s, y además aparecen bloqueos falsos.
   - **Calla:**
     - el 58 % de los elementos no tiene contrato;
     - recortar, mover un momento o editar el texto de una VO corre la obra entera sin aviso;
     - la regla de los 15:00 está muerta desde el arranque porque la huella no lleva el valor.
   - **Consecuencia esperable:** el socio aprende a aceptar con Enter sin leer.
4. **La vista previa no muestra lo editado:**
   - el 3D sigue el horario del prototipo;
   - no hay audio;
   - la duración de las VO es una estimación por palabras rotulada "final mix".

**Facilidad de uso.** Se entiende rápido, pero:
- el modelo es "magnético": mover un clip que cierra su momento corre todo lo posterior, y eso no se ve;
- faltan verbos de NLE: J/K/L, I/O, multiselección, copiar/pegar y cambiar el ancla;
- las tarjetas hablan en jerga de Unreal;
- a 1:1 el 94 % de los títulos de clip aparece cortado.

**Camino a Unreal.** La partitura todavía es una foto del prototipo y no un documento compilable:
- no tiene capa de enlace (marca, acción, target, asset);
- re-extraer pisa las ediciones;
- los ciclos de 2.R4 y 5.R4 hacen que 387 tiempos dependan del orden de evaluación;
- las ramas SHARE / DON'T SHARE se perdieron;
- las esperas elásticas no se comportan como las de Unreal.

**Todo es arreglable.** Casi todo el lote 1 es de esfuerzo S/M y está en `app.js`, `integrity.js` y `serve_editor.py`.

## Plan de arreglos por lotes

### Lote 1 · Que no se pierda ni se corrompa nada (antes de dárselo al socio)
- **Borrar** (A1, C1, B3, +B1, +C1):
  - re-anclar también los momentos;
  - que "Delete them too" no cruce momentos y diga cuántos borra de verdad;
  - calcular los tiempos con el usuario típico;
  - postcondición: sin anclas colgando y tiempos de los hijos ±1 ms; si no se cumple, abortar.
- **Guardar** (A2, B11, C7, D3):
  - el PUT lleva la revisión base y un hash;
  - el servidor responde 409 si el disco cambió, y el cliente ofrece recargar, guardar como copia o sobrescribir;
  - el borrador guarda el hash del disco;
  - el estado queda limpio solo si no hubo ediciones durante el guardado;
  - la pestaña 3D no edita (+D4).
- **Servidor** (A3): copiar (no mover) a `history/` con nombres únicos, para que nunca falte `score.json`.
- **Tarjeta abierta** (A4): el teclado no edita mientras está la tarjeta.
- **Validación:**
  - números (A8, B13);
  - Import (A9, D12, +B3);
  - candado en todos los caminos y guardado (A10, B10, +C2);
  - nombres de WAV: únicos, sin pisar el inbox y sin tomar un asset real (A11, B12, D9).
- **Usuario simulado** (+A1, C12, +D3): un recorte o un alta nunca deben escribir valores medidos con otro usuario simulado que no sea Typical.
- **Ctrl "solo"** (A7, +B4): que de verdad no mueva al resto.
- **Solapes de la familia** (+A2): al arrastrar con familia, revisar las pistas de todos los anclados, no solo la del arrastrado.

### Lote 2 · Integridad calibrada (que los avisos se lean)
- **Ripple visible** (C2, A5, +D1): toda edición que corre el resto de la obra lo dice ("+3,2 s a todo lo que sigue, total 17:01") en la tarjeta o, si no rompe nada, en la barra de estado.
- **Huella con valor** (A6, B5, +D2): así revive la regla de los 15:00, y lo aceptado cubre solo el valor que se aceptó.
- **VO** (B2, B8, C3):
  - mover una VO es un aviso informativo, salvo que cambie de orden o cruce su ancla en Unreal;
  - las VO nuevas no son "wired";
  - la tarjeta habla en lenguaje de montaje (qué va a pasar en el visor), con el código de regla en chico;
  - Enter nunca acepta.
- **Familia** (A5): sin momentos, para evitar bloqueos falsos.
- **Contrato ampliado** (B1): Alma, metaball, CHARGE, fantasmas, títulos y créditos, caminatas.
- **Ciclo de vida de "≠ APK"** (B6, C6, D11, +B2):
  - se marcan todos los elementos afectados;
  - reabrir deja rastro;
  - deshacer limpia.
- **Reglas C2 del anexo 17 que faltan** (B7): hoy están 2,5 de 10.
- **Ciclos de 2.R4 y 5.R4** (A12, D6): se arreglan en la partitura, con un mensaje claro. Es decisión de Beltrán.

### Lote 3 · Vista previa honesta
- **3D:** que el 3D se mueva con la partitura editada (alimentar el prototipo con sus tiempos) o, como mínimo, un aviso grande y fijo (B9, C5).
- **Audio:** reproducir las VO y los FX reales; el prototipo ya tiene 116 audios (C4).
- **Duraciones de VO:** las reales, desde la mezcla, en vez de la estimación (D5, B4).
- **Play:** que no se congele al final del prototipo (+C3).

### Lote 4 · UX de NLE
- **Verbos de NLE:** J/K/L, I/O, multiselección, copiar/pegar y cambiar el ancla (C9, C10).
- **Marcadores y notas:** que se puedan editar (C13).
- **Títulos legibles:** que no se corten a 1:1 (C11).
- **Problems con acciones** (C8).
- **Foco y "unsaved":** quitar las trampas de foco y que "unsaved" no engañe (C14).

### Lote 5 · Antes de que la partitura mande en Unreal (F3/F4)
- **Re-extracción** (D2, A13): decidir la fuente de verdad e importar sin pisar ediciones, con IDs congelados.
- **Capa de enlace** (D1): schema 3 con marca, acción, target y asset.
- **Golden** (D4): sacarlo de la partitura viva.
- **Ramas SHARE** (D7).
- **Esperas** (D8): semántica real de Unreal.
- **Contrato por id y no por key** (D10).
- **Validación fuera del navegador** (D12).
- **Perillas legibles por máquina** (D13).

## Decisiones que necesito de Beltrán
1. **Ciclos de 2.R4 y 5.R4.** ¿Cuál es el ancla correcta de cada uno? Hoy empiezan junto con el momento anterior.
2. **Fuente de verdad.** ¿Desde ya manda `score.json` y `guion.js` queda solo de lectura, como dice el plan para cuando F1 esté en uso? Así re-extraer deja de ser un riesgo.
3. **Mover una VO.** Mi recomendación es que sea un aviso informativo, no una tarjeta, salvo que cambie el orden de las voces o cruce su ancla en Unreal.

---

## Apéndice · Hallazgos uno por uno

**Cómo leerlo:**
- La severidad es la que corrigió el verificador.
- El estado dice si el verificador confirmó el hallazgo o lo confirmó en parte.
- Los que llevan "+" los encontró el verificador.

### A · Código y datos

El núcleo está bien planteado: el motor es puro y reproduce el prototipo (665/665), toda edición pasa por commit() sobre una copia y el servidor valida nombres de audio y guarda historial. Aun así, hay caminos concretos, reproducidos en Node contra la partitura real, que rompen la partitura sin avisar. Borrar cualquiera de los 20 elementos de los que cuelga un momento manda ese momento y el resto de la obra a 0:00 (y "Delete them too" borra hasta el 62 % de la obra). Además, el guardado es "gana el último", con un borrador que se restaura o se descarta solo según el número de revisión. La tarjeta de impacto falla en los dos sentidos: con avisos de más (mover VO_15 1 s pide motivo por 3 bloqueos falsos y marca 7 elementos ajenos como ≠ APK) y de menos (un recorte que alarga la obra 5 min no dice nada). Además, lo aceptado se registra con una huella que no sigue la especificación. Con dos personas editando a diario, la experiencia se va a romper seguido si no se arreglan primero A1-A5; casi todos los arreglos son pequeños (S/M) y están localizados en app.js, integrity.js y serve_editor.py.

#### A1 · Borrar un elemento del que cuelga un momento manda ese momento y todo lo que sigue a 0:00; "Delete them too" borra hasta el 62 % de la obra
- **Severidad:** critical (el auditor puso critical)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** M

**Evidencia:** app.js:108 `const e = n.elements[k]; if (!e) continue;` salta los momentos (beats), que nunca se re-anclan. app.js:102 `family()` cruza los momentos (dependents() incluye beats, engine.js:71) y borra su contenido. engine.js:34: un beat con ref inexistente vale `0 + off`. integrity.js:92 suprime C1.ANCHOR.MISSING en los delete "porque la reparación los re-ancla". integrity.js:83 lista el id crudo ("bt_1j1fdq88a1"). En la partitura real, 20 de 73 momentos están anclados a un elemento: 2.7b-f←PASO, 2.R4←VO_15, 1.R3←VO_10, 2.R2/3.R2/4.R2/5.R2←VEIL_OPEN, 9.1b←FINAL, 1.6←WALK1, etc. Corrida dimA/a_del.js: borrar PASO (sin contrato con Unreal) muestra solo "1 element is anchored to it: bt_1j1fdq88a1" con la opción por defecto "Re-anchor… (they keep their times)". Resultado: el momento 2.7b pasa a 0:00, cambian de inicio 556 ítems y el total baja de 16:58 a 14:21, con lo que desaparece el aviso de 15:00. Borrar VO_15 con "Delete them too" deja 227 de 592 elementos y 9 momentos colgando en 0:00. Además app.js:99 usa App.sched del usuario simulado activo: con Idle, borrar G_CHOOSE re-ancla FX_PROTOSELECT a +30 s; con Typical, a +7 s (dimA/a_fp.js D).

**Escenario:** 1) El socio selecciona el primer PASO (2.7a) y pulsa Supr. 2) La tarjeta dice "1 element is anchored to it: bt_1j1fdq88a1" y propone "Re-anchor them to its parent (they keep their times)". 3) Hace clic en "Proceed and repair". 4) El momento 2.7b y toda la obra posterior saltan 2:37 hacia atrás y se superponen con el inicio. El total "mejora" a 14:21 y Problems solo muestra un C1.ANCHOR.MISSING con un id ilegible. Si no lo nota y guarda, score.json queda corrompido y solo se recupera desde history/. Con "Delete them too" desaparecen 365 elementos de 5 etapas.

**Arreglo:** En applyDeleteRepair, tratar los hijos que son momentos igual que los elementos: `const x = n.elements[k] || n.beats[k]` y `x.at = { ref: gone.at.ref, edge: gone.at.edge, off: t[k][0] - base }`. Calcular `t` con un `ScoreEngine.resolve(before, {persona:'typical'})` nuevo en vez de App.sched. En 'family', no atravesar momentos: se re-ancla el momento y no se borra su contenido. La tarjeta debe mostrar cuántos elementos borra de verdad (`family().size`) y nombrar los momentos por su key ("moment 2.R4"). Agregar una postcondición: después de reparar, `resolve(n).dangling` vacío y tiempos de los hijos iguales (±1 ms); si no se cumple, abortar con mensaje y no aplicar. Quitar la supresión de integrity.js:92 cuando quede algo colgando.

**Verificador:** Reproducido con el app.js real cargado en vm (verA/h.js + verA/a1.js). Se borra el PASO que ancla 2.7b. La tarjeta solo dice '1 element is anchored to it: bt_1j1fdq88a1' y trae marcada 'Re-anchor… (they keep their times)'. Al confirmar, 2.7b pasa de 2:36.5 a 0:00, cambian de inicio 556 ítems y el total baja de 16:58 a 14:21.5; en Problems solo aparece un C1.ANCHOR.MISSING con el id crudo. La causa es app.js:108 (`n.elements[k]`), que nunca re-ancla momentos, y engine.js:34, donde un beat con ancla colgando vale 0+off. Hay 20 de 73 momentos anclados a elementos, entre ellos VO_10, VO_15, VO_20, VO_26, VO_31, PASO, VEIL_OPEN y FINAL. Con verA/a1b.js: borrar VO_15 con 'Delete them too' deja 227 de 592 elementos, 9 colgando y un total de 6:06.7. G_CHOOSE re-ancla FX_PROTOSELECT con off 7 en Typical y 30 en Idle, porque usa App.sched. PLAN §8 afirma que la reparación 'conserva sus tiempos'. Ctrl+Z lo revierte en la sesión, pero es el camino por defecto, corrompe la partitura en silencio y la promesa del botón es falsa. Se mantiene critical.

#### A2 · Guardado "gana el último" y borrador validado solo por número de revisión: se pisan ediciones de otro, se restauran encima o se descartan en silencio
- **Severidad:** high (el auditor puso high)
- **Estado:** en parte
- **Rompe:** partitura
- **Esfuerzo:** M

**Evidencia:** app.js:339 `next.rev = (App.baseRev || 1) + 1` sin comprobar nada; serve_editor.py:77-96 no compara la revisión del disco. app.js:33 restaura el borrador solo si `d.baseRev === App.baseRev`. app.js:343-344 pone `dirty=false` y borra el borrador después del await, aunque haya habido ediciones durante el PUT. app.js:397 Ctrl+S no tiene guarda de "guardando" ni de e.repeat. app.js:380 y 336: la pestaña 3D acepta ediciones del teclado, escribe el borrador compartido y su edición nunca vuelve. Corridas: dimA/a_srv.py (1): dos PUT con rev 3 devuelven ambos 200 y queda solo el de B. dimA/a_draft.js caso 1: disco con la misma rev y otro contenido; se restaura el borrador encima y la nota del socio desaparece. Caso 2: disco rev+1; el borrador se ignora en silencio y la primera edición lo sobrescribe. dimA/a_save.js: con un marcador hecho durante el PUT quedan 2 en memoria y 1 en disco, dirty=false y sin borrador; 5 auto-repeticiones de Ctrl+S lanzan 5 PUT. dimA/a_tabs.js: M en la pestaña 3D muestra "Bookmark at 00:40.0" y el marcador se pierde. El PLAN (línea 114) ya señalaba "gana el último" como defecto del prototipo, y el editor lo repite.

**Escenario:** Beltrán y el socio parten del mismo score.json rev 2, en dos máquinas vía git o en dos ventanas. Cada uno guarda y ambos quedan en "rev 3": el último borra el trabajo del primero sin aviso, y en history/ solo queda la versión anterior. Variante: el navegador de Beltrán se cierra con trabajo sin guardar. Al volver, si el disco tiene la misma rev con otro contenido (git pull), el editor dice "Restored your unsaved changes" y el siguiente Ctrl+S borra lo del socio. Si la rev cambió, su trabajo se descarta sin decir nada.

**Arreglo:** Enviar `baseRev` y un hash del contenido base en el PUT. El servidor responde 409 si el disco no coincide (con quién y cuándo guardó), y el cliente ofrece "Reload / Save as copy / Overwrite". Guardar en el borrador el hash del score de disco al arrancar y, si al volver no coincide, preguntar (abrir el borrador como copia, o descartar) sin tocarlo hasta que se decida. En save(): ignorar si hay un guardado en vuelo o `e.repeat`; usar un contador de ediciones y poner `dirty=false` y borrar el borrador solo si no hubo ediciones desde que se envió. En `?view=3d`, que commit() no haga nada (o que reenvíe la edición a la pestaña timeline) y que nunca escriba LS_DRAFT.

**Verificador:** La mecánica está confirmada. verA/a2.js: dos pestañas timeline guardan las dos 'rev 3' y en disco solo queda la nota de B. Una edición hecha durante el PUT queda en memoria con dirty=false. El disparador realista es otro: doble clic en abrir-editor.bat con el editor ya abierto. serve_editor.py:137-145 arranca el Timer de webbrowser.open (que no es daemon) antes de detectar el puerto ocupado, así que abre otra pestaña timeline aunque haga sys.exit(0). Las pestañas timeline ignoran la partitura de la otra (app.js:380 solo la aplica con view=3d) y comparten LS_DRAFT, de modo que la segunda pestaña puede restaurar el borrador de la primera y después pisarse mutuamente al guardar. Exagerado: el escenario 'dos máquinas vía git'. obra/ no está versionado (git status: '?? obra/') y git marcaría conflicto en un JSON de texto, no lo pisaría en silencio. La ventana de edición durante el PUT es mínima (json.dump tarda unos 13 ms en localhost). El marcador perdido en la pestaña 3D es menor. Severidad alta por el caso de las dos pestañas.

#### A3 · La escritura del servidor no es atómica: hay una ventana sin score.json, PUT concurrentes fallan en Windows y el historial se pisa dentro del mismo segundo
- **Severidad:** medium (el auditor puso high)
- **Estado:** en parte
- **Rompe:** partitura
- **Esfuerzo:** S

**Evidencia:** serve_editor.py:88 `os.replace(SCORE, history/...)` mueve la única copia vigente antes de escribir la nueva (líneas 92-95). Si algo falla entre medio, no queda score.json. Línea 87: sello con resolución de 1 s, y os.replace sobrescribe una copia del mismo segundo. Línea 92: un único nombre `score.json.tmp` para todos los hilos de ThreadingHTTPServer (127-130), sin lock. Línea 82: valida solo `schema==2` y que `elements` sea dict. Corrida dimA/a_srv.py, que llama a Handler.do_PUT directamente sobre una copia temporal, sin servidor. (4): si el os.replace final lanza PermissionError (típico en Windows con Defender o el indexador) quedan "score.json exists: False" y GET 404. (3): de 6 PUT concurrentes, 4 lanzaron "PermissionError: [WinError 32] El proceso no tiene acceso al archivo". (2): con dos guardados en el mismo segundo se perdió la copia de rev 2. (5): `{"schema":2,"elements":{}}` se acepta y pasa a ser el score.json.

**Escenario:** El socio deja apretado Ctrl+S (hábito de NLE) o guarda desde dos ventanas. El servidor recibe varios PUT a la vez y los hilos escriben el mismo .tmp. Algunos responden con conexión cortada ("Could not save") y la copia de history/ de ese segundo se sobrescribe. Si el antivirus bloquea el rename final, score.json desaparece: al recargar, el editor dice "Could not load the score… Run python tools/editor/serve_editor.py" aunque el servidor esté corriendo, y la última versión solo queda en el .tmp.

**Arreglo:** Copiar a history/ (shutil.copy2) en vez de mover. Escribir a un temporal único del mismo directorio (tempfile.NamedTemporaryFile, delete=False), hacer flush+fsync y luego os.replace con reintentos ante PermissionError (3-5 intentos con 100 ms). Serializar los PUT con un threading.Lock. Nombrar el historial con rev y milisegundos (`score-r{rev}-%Y%m%d-%H%M%S-{ms}.json`) y no sobrescribir nunca. Validar en el servidor la integridad referencial mínima: acts con beats existentes, y elementos con beat/lane/group existentes.

**Verificador:** verA/a3.py llama a Handler.do_PUT con hilos reales sobre una copia temporal. Con 4 PUT concurrentes, en las 3 pruebas fallaron 2-3 con PermissionError WinError 32 por el .tmp compartido, pero siempre ganó uno y el score.json final era JSON válido: no se observó ni corrupción ni desaparición. Con 3 guardados en el mismo segundo, history/ quedó con una sola copia (rev 21) y se perdió la de rev 20. `{"schema":2,"elements":{}}` se acepta (200) y deja 0 elementos en disco. Que score.json desaparezca exige que falle el os.replace final (antivirus o bloqueo externo). La secuencia mover-antes-de-escribir (línea 88) lo permite, pero no se reprodujo por concurrencia. Aun así, el contenido queda en .tmp y en history/, y la pestaña abierta puede volver a guardar (isfile=False → escribe). El defecto es real, pero el riesgo de pérdida es bajo: medium.

#### A4 · Con la tarjeta de impacto abierta, el teclado sigue editando, y al confirmar la tarjeta se pisan esas ediciones y el deshacer
- **Severidad:** medium (el auditor puso high)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** S

**Evidencia:** app.js:65-66 captura `beforeStr` y `next` al llamar a commit(); app.js:72-76 `finish` hace push del `beforeStr` viejo y asigna `App.score = next` recién al confirmar. ui.js:452-468: la tarjeta solo bloquea el ratón (clic en el fondo = cancel); el foco queda en el botón "Proceed", así que document.keydown sigue llegando a onKey (app.js:393), con M (408), Alt+←/→ (413) y Ctrl+Z (400). applyDeleteRepair también lee App.sched al confirmar (app.js:99), no al abrir. Corrida dimA/a_reent.js: A) M durante "Delete · CANDS_IN" deja markers=1 y, al confirmar, markers=0. B) Ctrl+Z durante la tarjeta devuelve NEGRO a 3 s y, al confirmar, vuelve a 7 s con la pila de rehacer vacía. C) Alt+Shift+→ mueve NEGRO a +1 s y, al confirmar, vuelve a 0.

**Escenario:** El socio borra un clip con dependientes y aparece la tarjeta "Proceed and repair". Mientras la lee, por reflejo de montador, pulsa M para marcar un punto o Ctrl+Z porque duda. El editor aplica el marcador (toast "Bookmark at…") o el deshacer. Luego hace clic en "Proceed and repair": el marcador desaparece, o el deshacer se revierte en silencio y la pila de rehacer queda vacía.

**Arreglo:** Mientras haya una tarjeta pendiente (`App.pending`), commit/undo/redo/importScore deben rechazar con el toast "Finish the open decision first", y onKey debe ignorar todo salvo Escape, Enter y la escritura en el motivo. Como defensa extra, en finish() comprobar `JSON.stringify(App.score) === beforeStr`; si cambió, re-ejecutar mutate sobre el estado actual y re-evaluar la tarjeta en vez de asignar el `next` viejo.

**Verificador:** verA/a4.js, con la tarjeta de 'Delete · CANDS_IN' abierta. Solo tiene un ítem inv y no tiene campo de motivo, así que el foco queda en .pri (ui.js:464). Pulsar M agrega un marcador; al confirmar, markers vuelve a 0. Ctrl+Z durante la tarjeta devuelve NEGRO a 0; al confirmar, vuelve a 3 s con redo vacío y el estado original fuera de la pila de deshacer. Matiz: si la tarjeta tiene un warn o block, el foco está en #rsn y onKey lo trata como escritura (app.js:398). Ahí el atajo no pasa, salvo que el usuario haga clic en el texto de la tarjeta. Solo se pierde la acción hecha mientras la tarjeta está abierta, no la partitura: medium.

#### A5 · La tarjeta de impacto mide mal el alcance: bloqueos falsos al mover un elemento que ancla un momento y silencio total al recortar o mover momentos
- **Severidad:** high (el auditor puso high)
- **Estado:** confirmado
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** M

**Evidencia:** integrity.js:61-64: en move/offset, `touched` = toda la familia, y la familia atraviesa momentos (los 73 beats tienen `at` encadenado y 20 cuelgan de elementos). En trim, text y move-beat solo se revisan op.ids (línea 60, y el comentario de la línea 58 lo asume). app.js:86-90 marca ≠ APK al primer elemento de cada regla. Corrida dimA/a_move.js: arrastrar VO_15 +1 s abre una tarjeta con 3 BLOCK "Hardwired in Unreal" (AMB_06/PAD_M1…, VEIL_CLOSE/VEIL_OPEN, T_IN/T_OUT de etapas posteriores) que exige motivo de 12+ caracteres. Al seguir, 7 elementos ajenos quedan ≠ APK: VO_15, G_HEART, AMB_06, VEIL_CLOSE, T_IN, G_GRAB, G_SAVE4. Mover el momento 2.R4 +1 s, que desplaza exactamente lo mismo, solo da 2 warn. dimA/a_fp.js A: recortar DISCLAIMER de 20 a 320 s corre toda la obra +5 min sin tarjeta ni toast.

**Escenario:** El socio corre VO_15 un segundo. El editor le dice que "rompe" títulos, velo y ambientes de las etapas 3-5 (que solo se trasladan con su momento) y le exige un motivo. Escribe cualquier cosa para seguir. Así se acostumbra a ignorar la tarjeta, y el registro de "rupturas aceptadas", que según 17-integridad.md:46 será el manifiesto "Ship with N known divergences" del APK, se llena de falsos ≠ APK. A la vez, un recorte que de verdad desplaza 5 min todos los cues cableados pasa sin aviso.

**Arreglo:** Calcular el impacto igual para todos los verbos: resolver antes y después y quedarse con los elementos cuyo tiempo relativo a su propio momento cambió (Δelemento ≠ Δmomento), más los momentos cuya duración cambió. Correr contractFor solo sobre ese conjunto, y marcar ≠ APK solo a los que cambian de verdad. Así un traslado en bloque no rompe literales relativos a la etapa, y un recorte o un cambio de texto que estira la obra sí se revisa.

**Verificador:** verA/a5.js y a5b.js. Mover VO_15 +1 s abre una tarjeta con 3 block (C3.AMB.PICK, C3.VEIL, C3.TITLE.STAGE) más warns, con motivo obligatorio. Al aceptar quedan 7 elementos ≠ APK, y 6 de ellos tienen Δ = 0 respecto de su propio momento: solo se trasladan con él. Mover el momento 2.R4 +1 s, que desplaza lo mismo, da solo 2 warn. Recortar DISCLAIMER de 20 a 320 s no muestra tarjeta ni toast, y el total pasa de 16:58 a 21:58. Además (verA/m4.js), un empujón de 0,1 s abre tarjeta en 146 de 592 elementos (61 con motivo obligatorio). La tarjeta vuelve en cada empujón aunque ya se haya aceptado, porque opItems no consulta score.accepted. Es el mecanismo central de seguridad y falla en los dos sentidos.

#### A6 · Huella de lo aceptado sin parámetro: lo aceptado queda aceptado aunque empeore, se pierde el segundo motivo y las entradas de elementos borrados no se limpian nunca
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** M

**Evidencia:** integrity.js:21 y app.js:87: `fp = rule + '|' + el`. La especificación (17-integridad.md:51) pide "regla + ids + parámetro clave" y reabrir cuando cambie. app.js:88 `if (!n.accepted.some(a => a.fp === fp))` descarta las aceptaciones posteriores. integrity.js:47-49 conserva para siempre las entradas cuyo el ya no existe. C2.TOTAL.GOAL usa fp 'C2.TOTAL.GOAL|' y ya está abierto al cargar (16:58 > 15:00), así que opItems (integrity.js:90-92) nunca lo ve como nuevo. Corrida dimA/a_fp.js: A) +5 min sin aviso. B) VO_02 aceptado dos veces ("first: half a second…" y "second: moved 30 s…") guarda solo el primer motivo. C) tras borrar VO_02 queda 'C3.VO.WIRED|el_1f574ux1qq' apuntando a un elemento inexistente.

**Escenario:** El socio acepta "VO_02 +0,5 s: respirar". Una semana después la mueve 30 s a otra etapa y vuelve a aceptar con otro motivo. Problems sigue mostrando "half a second to breathe", y cuando en F4 se revise qué divergencias se aceptaron, el registro miente. Del mismo modo, como la obra ya pasa de 15:00, ningún cambio que la alargue vuelve a avisar del objetivo.

**Arreglo:** Incluir en la huella un parámetro estable por regla: para C3 de mover, el nuevo offset o Δ redondeado; para TOTAL.GOAL, el exceso en tramos de 10 s; para HELP.LATE, el par ayuda/espera. Si la huella cambia, se reabre. Guardar las aceptaciones como lista de eventos (quién, motivo, fecha, verbo, valor) en vez de deduplicar. En compute(), marcar o podar las aceptadas cuyo `el` ya no existe. Para problemas preexistentes, comparar el parámetro (total antes/después) y mostrar en la tarjeta "Total 16:58 → 21:58 (+5:00)".

**Verificador:** La huella es `rule|el` (integrity.js:21, app.js:87), mientras que 17-integridad.md:51 pide regla + ids + parámetro clave. verA/a6.js: se acepta VO_02 +0,5 s ('half a second to breathe') y luego se borra VO_02 con otra razón. El registro conserva solo 'C3.VO.WIRED|el_1f574ux1qq' con el motivo del movimiento, descarta el del borrado y la entrada sigue en Problems apuntando a un elemento inexistente (integrity.js:47-49). verA/m5.js: C2.TOTAL.GOAL ya está abierto al cargar con las 4 personas, así que nunca cuenta como 'nuevo' (confirmado también con el recorte de +5 min de A5).

#### A7 · Ctrl+arrastrar ("mover solo") mueve igual el resto de la obra, y mover un clip "until" lo recorta mientras el fantasma muestra otra cosa
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** S

**Evidencia:** app.js:137: keepKids compensa solo `n.elements[k]` con `at.ref === id`. Ignora los momentos anclados al elemento y los hijos por `end.ref`, y compensa por igual a los hijos anclados al borde 'end' de un clip "until", cuyo fin no se mueve (engine.js:44). ui.js:595-598 dibuja el fantasma con `drag.dur` fijo. Corrida dimA/a_move.js: Ctrl+arrastrar VO_15 +2 s mueve 397 ítems (el momento 2.R4 y todo lo posterior). Ctrl+arrastrar BIO (2.R4) +3 s mueve SENSOR_OUT3, anclado al fin de BIO, −3 s aunque ese fin no se movió. Arrastrar BIO +10 s cambia su duración de 42,17 a 32,17 s mientras el fantasma mostraba 42,17.

**Escenario:** El socio quiere correr solo VO_15. La barra de estado dice "Ctrl+drag moves it alone", así que arrastra con Ctrl, pero los momentos 2.R4-9.7 se corren 2 s. O arrastra el clip BIO para retrasar su entrada: el fantasma muestra el clip entero desplazado, pero al soltar el clip se acorta 10 s y un elemento vecino salta 3 s hacia atrás.

**Arreglo:** En keepKids, compensar también `n.beats[k]` y los hijos por `end.ref`, y solo en los bordes que realmente se mueven: si el clip es "until", solo se mueve su inicio, así que solo se compensan los hijos anclados a 'start'. Para mover un "until" sin recortarlo, desplazar también `end.off` en dt, o dibujar en el fantasma la duración resultante con la leyenda "trims start". Como postcondición, "alone" debe cambiar el tiempo de exactamente un elemento.

**Verificador:** verA/a7.js y a7b.js. Ctrl+arrastrar VO_15 +2 s mueve 397 ítems (2.R4 y todo lo posterior), porque keepKids (app.js:137) no compensa beats. Ctrl+arrastrar el BIO de 2.R4 (la key BIO está duplicada; el de 1.R4 es otro) +3 s mueve SENSOR_OUT3 y FX_SENSORVANISH −3 s, aunque el fin de BIO no se movió, y BIO pasa de 42,17 a 39,17 s. Un arrastre normal de +10 s deja BIO en 32,17 s sin mover a nadie más, mientras ui.js:596 dibuja el fantasma con drag.dur fijo.

#### A8 · Los campos numéricos aceptan vacío, negativos y valores absurdos: un clip pasa a ser instantáneo sin poder editarse, hay elementos antes de 0:00 y la regla se cuelga
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** S

**Evidencia:** ui.js:744 `Act.trim(id, parseFloat(v))` y ui.js:750 (beatoff) no comprueban isFinite; setOffset y setGate sí (app.js:159, 163). app.js:155: `Math.max(.1, NaN)` = NaN se guarda en memoria y se escribe como null en disco. ui.js:367: un elemento con valor no positivo cuenta como instantáneo (isInstant) y el inspector deja de mostrar el campo Duration. app.js:163-165 acepta fw negativo, y app.js:158-161 acepta cualquier offset sin laneBusy (el invariante de solape de 17-integridad.md:36 solo se aplica al arrastrar, ui.js:591). ui.js:155 recorre todo el total al dibujar la regla. Corrida dimA/a_nan.js: con Duration vacío, DISCLAIMER queda en NaN en memoria y null en disco, dura 0 s y el total baja 20 s, sin tarjeta ni toast. Con el offset del momento 2.1 vacío, el momento vuelve a 0. Offset −500 en NEGRO: empieza en −8:00 y no hay ningún problema. fw −10 en G_SENSOR: el usuario Idle dura −10 s. Offset 1e6: unas 500.000 iteraciones de la regla. dimA/a_overlap.js: offset −10 crea un solape.

**Escenario:** El socio borra el contenido de Duration de DISCLAIMER para escribir otro valor y hace clic en el timeline antes de teclear. El clip queda reducido a un punto, la obra se corre 20 s y el inspector ya no muestra el campo para devolverle el largo: solo lo recupera Ctrl+Z, si se da cuenta. Si escribe un offset negativo grande, el clip desaparece a la izquierda de 0:00 y no se puede volver a agarrar.

**Arreglo:** Agregar una guarda única en el handler de cambios del inspector: si `!Number.isFinite(v)`, se hace renderInspector() y no se aplica nada. Acotar valores: duración ≥ 0,1, inicio resultante ≥ 0 (o un problema C1 "starts before 0:00"), fw ≥ expected + 0,1 y |offset| ≤ 3600 s, pidiendo confirmación por encima. Pasar setOffset y trim por laneBusy, igual que el arrastre. Limitar el bucle de la regla al rango visible.

**Verificador:** verA/a8.js. Con Duration vacío (input type=number, ui.js:298, entrega '' al borrar y salir), DISCLAIMER queda con dur.value NaN en memoria y null en JSON, dura 0 s y pasa a isInstant (ui.js:22). El inspector deja de mostrar el campo (ui.js:367) y el total baja 20 s, sin tarjeta ni toast. Con offset −500, NEGRO empieza en −480 s y no aparece ningún problema. Matices: fw −10 sí abre tarjeta con 3 warn (C2.WAIT.FW, C2.HELP.LATE, C3.WAIT.HALL.SENSOR), así que no es silencioso. El beatoff vacío en 2.1 no cambia nada visible porque su off ya era 0, aunque sí resetea los momentos con off distinto de 0.

#### A9 · Importar un JSON incompleto envenena App.score y el borrador: tras recargar, el editor no arranca, y con Ctrl+S el mismo JSON pasa a disco
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** S

**Evidencia:** app.js:351: el orden es `App.score = s; markDirty(); compute()`. compute() lanza la excepción después de asignar, y el borrador se escribe 400 ms después (app.js:336). La única comprobación es `schema === 2 && elements`. boot() no envuelve compute() ni renderAll() (app.js:37). serve_editor.py:82 aceptaría el mismo objeto. Corrida dimA/a_import.js con un JSON sin `acts`: toast "Could not import: score.acts is not iterable", pero App.score ya es el objeto roto, la pila de deshacer tiene 1 entrada y el borrador quedó escrito con baseRev 2 (= disco). En el próximo boot, compute() lanza antes de UI.renderAll(): no hay menús ni "Reload from disk".

**Escenario:** El socio importa una exportación vieja o editada a mano. Ve "Could not import", cree que no pasó nada y recarga la página. La app queda en blanco cada vez que la abre, porque el borrador roto se restaura al arrancar, y la única salida es borrar el localStorage desde DevTools. Si antes de recargar pulsó Ctrl+S, score.json en disco también queda roto para Beltrán.

**Arreglo:** Validar antes de asignar: dentro de un try, comprobar la estructura (acts/beats/groups/lanes con referencias coherentes) y correr `ScoreEngine.resolve` y `Integrity.staticProblems` sobre el objeto importado; solo después hacer push al deshacer y asignar. En boot(), envolver el arranque con un borrador: si falla, guardar el borrador con otra clave, arrancar desde disco y avisar. En el servidor, la misma validación referencial (ver A3).

**Verificador:** verA/a9.js: importar un JSON sin acts muestra el toast 'Could not import: score.acts is not iterable', pero App.score ya quedó roto. La pila de deshacer tiene 1 entrada y el borrador se escribió con baseRev 2 (igual al disco). Al volver a ejecutar boot() con ese localStorage salta 'score.acts is not iterable' antes de UI.renderAll. Es poco probable (solo pasa con un JSON que no salió de Export), pero para un usuario no técnico el editor queda inutilizable: medium.

#### A10 · El candado de grupo solo protege del ratón: Supr/Backspace, Alt+flechas y el inspector editan y borran elementos bloqueados, y el candado no se guarda
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** S

**Evidencia:** ui.js:551: un clic en un clip bloqueado igual lo selecciona; el bloqueo solo frena el arrastre, y el menú contextual desactiva Delete (ui.js:626). Pero app.js:410 (Delete/Backspace) y app.js:413 (Alt+←/→) no miran App.locked, ni tampoco los inputs del inspector (ui.js:741-751) ni los verbos Act. App.locked no está en savePref (app.js:60) ni en la partitura. Corrida dimA/a_lock.js con el grupo world bloqueado: Alt+→ deja el off de NEGRO en 0,1 y Backspace lo borra (true). Prefs guardadas: [].

**Escenario:** Beltrán bloquea el grupo World para que el socio no toque el negro inicial ("Lock group: protects it from edits"). El socio hace clic en NEGRO, recibe el toast "World is locked" y, como sigue seleccionado, pulsa Backspace por costumbre: el clip se borra. Al recargar, ningún grupo está bloqueado.

**Arreglo:** Aplicar el bloqueo dentro de commit(): si algún op.ids (o su familia, en move) pertenece a un grupo bloqueado, rechazar con un toast. Eso cubre a la vez teclado, inspector, menús y arrastre. Persistir `locked` en la partitura si es una protección entre personas, o en prefs si es personal.

**Verificador:** verA/a10.js, con el grupo world bloqueado y NEGRO seleccionado. Alt+→ deja off en 0.1 y Backspace lo borra; LS_PREF no guarda `locked`. El toast de ui.js:543 promete 'nothing in it can be moved or deleted'. Tampoco frenan el botón Delete del inspector (ui.js:736) ni el arrastre de un elemento no bloqueado cuya familia incluye elementos bloqueados. Se recupera con Ctrl+Z: medium.

#### A11 · Cargar un WAV no valida el nombre: dos sonidos nuevos pisan el mismo archivo del inbox, uno nuevo puede llamarse como un asset real de Unreal, y renombrar y luego deshacer desincroniza el disco
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** S

**Evidencia:** app.js:364 `name = cleanId(file.name)` sin uniqueKey; en cambio, rename sí comprueba (app.js:220). serve_editor.py:121-123 sobrescribe `<name>.wav` sin comprobar si ya existe. app.js:223-226 renombra en disco fuera de commit/undo. Corrida dimA/a_wav.js: dos sonidos vacíos con bell.wav quedan ambos como FX_bell, el segundo upload sobrescribe el primero y los dos apuntan a obra/audio/inbox/FX_bell.wav. Cargar FX_DISCLAIMER.wav en un sonido nuevo deja 2 elementos FX_DISCLAIMER (el real y uno NEW). Rename a FX_BELL_HALL seguido de Ctrl+Z deja la partitura apuntando a FX_bell.wav, que ya no existe en disco.

**Escenario:** El socio crea dos sonidos vacíos y les carga "bell.wav" de dos carpetas distintas: el inbox conserva solo el segundo y ambos cues sonarán igual. O carga "FX_DISCLAIMER.wav" corregido: en el import de F4 ese WAV choca con el asset real Obra/Audio/FX/FX_DISCLAIMER, que 17-integridad.md:108 marca como BLOQUEA. Si renombra un sonido y deshace, el siguiente rename falla con "not in the inbox".

**Arreglo:** En loadWav, pasar el nombre por uniqueKey contra todas las keys y contra los sonidos reales conocidos (soundIndex sin isNew y roles.json), y preguntar antes de reutilizarlo. En el servidor, responder 409 si el WAV existe, salvo `overwrite=1`. Hacer el rename de disco deshacible (registrar from/to y que undo lo invierta), o nombrar el archivo del inbox por el id inmutable (el_xxx.wav) y aplicar la key recién en el import.

**Verificador:** verA/a11.js con loadWav real: dos sonidos vacíos (FX_NEW_SOUND y FX_NEW_SOUND_2) a los que se carga bell.wav. Los dos pasan a FX_bell, hay dos POST a /api/audio?name=FX_bell (serve_editor.py:121-123 sobrescribe) y ambos apuntan a obra/audio/inbox/FX_bell.wav. Cargar FX_DISCLAIMER.wav deja 2 elementos FX_DISCLAIMER: el real y uno isNew. El rename fuera de undo se ve en el código (app.js:223-226: el fetch de renombre no pasa por commit).

#### A12 · La partitura real arranca con 2 "bloqueos" de ciclo de anclas que el mensaje describe mal: 2.R5 y 5.R5 empiezan junto con el momento anterior
- **Severidad:** low (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** confusión
- **Esfuerzo:** S

**Evidencia:** integrity.js:22 dice "falls back to 0", pero engine.js:50 devuelve `tStart(id)`. Traza dimA/t1.js: el ciclo es 2.R4 (fin) → SENSOR_OUT3 → BIO (until 2.R5x) → 2.R5x → 2.R5 → fin de 2.R4. El otro es 5.R4 → PAL_OUT → PALETTE (until G_SAVE5) → G_SAVE5 → 5.R5 → 5.R4. dimA/t2.js: 2.R5 = [373.09, 415.26], igual que 2.R4, cuando debería empezar en 415.26; 5.R5 (la espera G_SAVE5) empieza en 731.01, junto con 5.R4. La prueba dorada da 665/665 porque el prototipo usa el mismo atajo (timeline.js: console.warn('Ciclo de anclas')). 17-integridad.md:36 define el ciclo como invariante ("el gesto no se aplica"); dimA/t0.js muestra 'block C1.ANCHOR.CYCLE': 2 abiertos al cargar.

**Escenario:** El socio abre el editor y la barra de estado ya muestra "2 blocking", con un mensaje que no se cumple ("falls back to 0"). Aprende que "blocking" no significa nada. Además, cualquier edición en 2.R4/2.R5 o 5.R4/5.R5 hereda el atajo: su resultado depende del orden en que el motor recorre el grafo, y en F4 el compilador tendría que copiar ese atajo o el APK no coincidirá.

**Arreglo:** Corregir el dato en una sola tanda, con la decisión de Beltrán: anclar SENSOR_OUT3 y PAL_OUT al momento (2.R4 / 5.R4) con un offset fijo en vez de al fin de BIO/PALETTE, o excluirlos del fin del momento como se hace con los crossSpan. Corregir el mensaje ("falls back to the start of moment X") y tratar C1.ANCHOR.CYCLE como invariante: rechazar cualquier ciclo nuevo y mostrar los existentes como tarea de datos, no como bloqueo permanente.

**Verificador:** verA/a12.js: 2.R5 = 373,09–415,26 s, igual que 2.R4, cuando debería empezar en 415,26; 5.R5 empieza en 731,01, igual que 5.R4. Hay 2 C1.ANCHOR.CYCLE 'block' abiertos al cargar, y el mensaje 'falls back to 0' es falso: engine.js:50 devuelve tStart. Pero el prototipo hace exactamente lo mismo (timeline.js:113: `return tStart(n)`), así que la partitura y la vista 3D coinciden y no se pierde ni corrompe nada. Hoy el efecto es confusión (un 'blocking' permanente que el usuario no puede resolver) y una decisión de datos pendiente. Se baja a low.

#### A13 · La prueba dorada lee la partitura viva y falla con la primera edición; el "arreglo" obvio (re-correr extract_v1) borra todas las ediciones sin respaldo
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** S

**Evidencia:** golden_test.mjs:10 lee obra/score/score.json, que es editable, mientras PLAN:327 pedía un fixture. Corrida dimA/a_golden.js: recortar DISCLAIMER 1 s deja golden en 1/665 y el test sale con 1. extract_v1.mjs:121 hace `fs.writeFileSync(OUT, …)` directo sobre score.json, sin copia a history/; el README solo advierte "Ojo: pisa las ediciones". history/ guarda solo versiones anteriores (serve_editor.py:88), así que la última versión guardada existe únicamente en score.json, y obra/ no está en git (`git status`: '?? obra/').

**Escenario:** Tras una semana de edición, Beltrán toca engine.js y corre la prueba dorada para ver si rompió algo. Sale 1/665 rojo, pero por las ediciones, no por su cambio. Pensando que la partitura quedó desfasada, corre `node tools/score/extract_v1.mjs` para regenerarla: score.json vuelve al prototipo y la última versión guardada del socio se pierde (no está en history ni en git). Y mientras el test esté rojo, las regresiones reales del motor pasan sin verse.

**Arreglo:** Hacer que extract_v1 escriba un fixture congelado (obra/score/fixtures/score-v1-golden.json) y que golden_test lea ese fixture. Que extract_v1 se niegue a escribir score.json salvo con --force y, en ese caso, copie antes la versión actual a history/. Commitear obra/score/score.json, y no history/, para tener una copia canónica.

**Verificador:** verA/a13.js: recortar DISCLAIMER 1 s deja la prueba dorada en 1/665. golden_test.mjs:10 lee el score.json vivo y lo compara contra score.golden, que está congelado. extract_v1.mjs:121 hace writeFileSync directo, sin copia previa. obra/ no está versionado (git status '?? obra/') y history/ solo guarda la versión anterior a cada guardado (serve_editor.py:88), así que la última guardada vive únicamente en score.json.

#### A14 · Cada edición reconstruye todo el timeline y guarda 80 copias completas: hoy anda, pero no se hizo el "render por ventana visible desde el día 1" del plan
- **Severidad:** low (el auditor puso low)
- **Estado:** en parte
- **Rompe:** fricción
- **Esfuerzo:** M

**Evidencia:** app.js:75 llama a UI.renderAll() en cada commit, y ui.js:148-188 regenera el innerHTML de todo el timeline (todas las pistas, toda la regla). ui.js:378 hace 4 resolve() por cada render del inspector de una espera. app.js:73 guarda 80 snapshots JSON completos. PLAN:384 fijaba como mitigación de F1 "render por ventana visible desde el día 1". Corrida dimA/a_perf.js (solo JS, sin el parseo ni el layout del navegador): con 592 elementos, 14,9 ms por commit, 328 KB de HTML por render y deshacer de 23 MB; con 1776, 36,3 ms, 860 KB y 62 MB; con 2960, 63 ms, 1,4 MB y 103 MB.

**Escenario:** Cuando la partitura crezca con F5 (ramas, cues, lógica) a 1500-3000 elementos, cada arrastre soltado reconstruirá entre 0,9 y 1,4 MB de DOM más el layout, y además escribirá el borrador en localStorage y lo enviará por BroadcastChannel. La edición fina con Alt+→ repetido se volverá lenta, y la pestaña acumulará cerca de 100 MB solo en deshacer.

**Arreglo:** Virtualizar el timeline (pintar solo las pistas y el rango de tiempo visibles) y, en cada commit, re-renderizar solo las pistas tocadas (diff de ids cuyo tiempo cambió). Cachear en compute() los 4 resolve por usuario simulado. Guardar en deshacer parches (diff por id) en vez del documento entero.

**Verificador:** verA/a14.js: un commit sin DOM tarda unos 8,7 ms con 592 elementos, y 50 entradas de deshacer ocupan 15 MB. Hoy funciona. Es cierto que no se hizo el render por ventana que pedía PLAN:384, pero el costo con 1500-3000 elementos es una proyección, no algo medido en el navegador. Se mantiene low como deuda.

#### +A1 · Recortar una espera o agregar en el cabezal con un usuario simulado distinto de Typical escribe valores medidos en esa línea de tiempo: arrastrar a la izquierda alarga la espera y la obra típica crece sin aviso
- **Severidad:** medium
- **Rompe:** partitura

**Evidencia:** ui.js:550/554/578 toman drag.s/en de App.sched, que corresponde a la persona activa, y ui.js:612 pasa a Act.trim la duración mostrada. app.js:154 la escribe en gate.expected, que es el valor Typical. app.js:201 calcula `off = t - bs` también con el App.sched de la persona activa. verA/m1.js con G_CHOOSE (expected 7, fw 30), arrastrando el borde 5 s a la izquierda: en Slow se ve 18,5 s; al soltar en 13,5, expected pasa a 13,5 y el clip muestra 21,8 s (se ALARGA). En Idle se ve 30 s; al soltar en 25, expected pasa a 25, el clip sigue en 30 s y el total típico sube de 16:58 a 17:07,5. En ningún caso hay tarjeta ni toast. verA/m3.js: en Idle, con el cabezal 1 s antes del fin de 2.5, Shift+A → voz da off 29 s. En Typical, el momento 2.5 pasa de terminar en 2:18,9 a terminar en 2:34,8 y el total típico de 16:58 a 17:13,8, sin aviso, porque 'add' es QUIET y C2.TOTAL.GOAL ya estaba abierto. Además, verA/m5.js muestra que en Idle el problema dice 'Typical total 19:36', porque integrity.js:24 usa el total de la persona activa.

**Escenario:** 1) El socio elige 'Slow' para ver la obra como la vive alguien lento. 2) Una espera le parece larga y arrastra su borde derecho 5 s a la izquierda. 3) Al soltar, el clip queda 3 s más largo que antes. 4) Lo prueba en Idle: arrastra, el clip vuelve a su largo y parece que no pasó nada. En realidad cambió el valor típico y la obra típica creció 9,5 s. Como el aviso de 15:00 ya estaba abierto, nada lo dice.

**Arreglo:** En Act.trim de una espera, convertir la duración soltada a `expected` invirtiendo la fórmula de la persona activa (Slow: expected = 2·d − fw; Fast: d / 0,3). En Idle, no permitir el recorte y mostrar el toast 'In Idle a wait lasts its timeout: edit Timeout or switch to Typical'. La versión más simple es habilitar el recorte de esperas solo en Typical. En Act.add, calcular el offset con `ScoreEngine.resolve(App.score, {persona:'typical'})` o anclar al elemento anterior más cercano, y avisar si el elemento queda después del fin típico del momento. Hacer que staticProblems reciba siempre el horario Typical para C2.TOTAL.GOAL.

#### +A2 · Arrastrar un elemento con su familia solo revisa la pista del elemento arrastrado: los anclados caen encima de otros clips en sus pistas y nadie avisa
- **Severidad:** medium
- **Rompe:** confusión

**Evidencia:** ui.js:591 `laneBusy(target, ns, ns + Math.max(drag.dur,.05), drag.fam)` solo revisa la pista destino del clip arrastrado y además excluye a toda la familia. Los hijos se mueven al cambiar at.off del padre (app.js:134) sin que nadie revise sus pistas. staticProblems no tiene regla de solape, y laneBusy (app.js:254) usa el horario de la persona activa. PLAN:24 dice 'Solape: nunca se monta ni recorta' y 17-integridad.md:36 lo define como invariante ('solape en Típico'). verA/m2.js parte de 0 solapes al cargar y busca arrastres que la UI acepta (verifica laneBusy igual que ui.js). HALL_OFF −2 s deja WALK4 (3:15,3–3:18,3) encima de WALK3 (3:14,3–3:17,3) en ln_pawn_1. TO_HUD −2 s deja SISTER_IN encima de HUD_IN en ln_obj_1. G_BELL +5 s deja FX_BELLVANISH encima de FX_GHOSTOUT. GHOST_BELL +5 s y WALK2 −2 s también solapan. Ninguno abre tarjeta ni toast.

**Escenario:** 1) El socio adelanta HALL_OFF 2 s. El fantasma sale verde porque su propia pista está libre. 2) Al soltar, WALK4 (anclado a HALL_OFF) queda encima de WALK3 en la misma sub-pista y la tapa durante 2 s. 3) WALK3 deja de verse entero. El siguiente arrastre a esa zona se rechaza con 'occupied' sin que se vea por qué, y Problems no muestra nada.

**Arreglo:** Pasar la regla a commit() en vez de dejarla en ui.js. Después de mutate, resolver en Typical y buscar solapes por pista entre los elementos cuyo tiempo cambió. Si aparece uno nuevo, mover ese hijo a la pista libre más cercana de su grupo (freeLane/addLane, como laneLibreCerca de ISP) o rechazar como INV nombrando el par. Agregar C1.LANE.OVERLAP a staticProblems para que se vean los solapes existentes, y calcular siempre laneBusy con el horario Typical.

### B · Integridad

El sistema de integridad tiene una buena base (un solo punto de entrada commit(), motor puro verificado 665/665, contrato con severidad por verbo y candado), pero hoy no evita que la obra se rompa sin aviso y, a la vez, avisa demasiado donde no hace falta. En los experimentos en node con la partitura real, mover cualquiera de los 592 elementos no avisa nada en 347 casos (58,6 %), entre ellos ALMA_IN, BLOB_IN, CHARGE, los GHOST_*, DISCLAIMER, las caminatas y los créditos. Editar el texto de una VO corre cientos de elementos sin aviso. En cambio, el 100 % de las VO abre una tarjeta en cada empujón, y Enter acepta con el motivo vacío. A eso se suman fallas de fondo: la reparación del borrado se aplica después de la verificación y puede correr 509 elementos 36 s; las huellas sin parámetro dejan muerta la regla de los 15:00 desde el arranque; y "Reopen" borra sin rastro el registro de una divergencia C3. De las 10 reglas MVP del anexo 17 están implementadas unas 2,5, aunque el plan dice que F1 las incluye. Con este equilibrio, lo más probable es que el socio aprenda a cerrar las tarjetas sin leerlas mientras los cambios peligrosos de verdad pasan sin ninguna.

#### B1 · El contrato C3 cubre 107 de 592 elementos: la mayoría de lo que Unreal tiene cableado se mueve, recorta o borra sin aviso
- **Severidad:** high (el auditor puso critical)
- **Estado:** en parte
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** M

**Evidencia:** obra/unreal/contract.json tiene 12 entradas (líneas 5-37) contra las 27 filas del catálogo v0 en docs/editor-obra/anexos/17-integridad.md:148-177. Faltan alma.speak, disc, intro, charge.last/hold, cues.34, hall.exit/bell/cut, share.def, ghost.take, stage.k, pacer.baked y sync.inhale/charge1. En node (scratchpad/audit/exp_move.js), mover +1 s cada elemento da 347/592 sin aviso; borrar da 298 sin aviso y 138 con solo la tarjeta de anclados. Se mueven sin aviso: ALMA_IN (×6), BLOB_IN, CHARGE (×5), GHOST_BELL…GHOST_DRAW, DISCLAIMER, TITLE_IN/OUT, WALK3-6, TELEPORT y CR1_IN…CR6_OUT. Ya hay desfases que nadie reporta: DISCLAIMER dura 20 s contra DiscTime 19 (anexo 11:191); BLOB_IN dura 4,0 contra IntroTime 2,5 (anexo 11:23,112); VO_11h está en G_BREATH.start+12 contra HelpAfter 4 s después de VO_11b, y VO_16h/27h/32h en +14 contra 15/20/15 (anexo 11:64); PACER está en VO_12c+3 contra InhaleCueAt 3,48 (anexo 11:147); G_SAVE4/G_SAVE5 tienen fw 120 contra 240 en RunObra (BP_Obra_SC.md:501 'select (== _stage 1) 180 (select (== _stage 2) 120 240)'). fw.stage es kind 'literal' sin valor, y la deriva solo se calcula para 'knob' (integrity.js:38). Borrar G_BELL o G_SHARE (2 de las 4 esperas bloqueantes reales) solo dice 'N elements are anchored to it' con el botón primario 'Proceed and repair', porque wait.* no tiene 'delete' (contract.json:18-25). El inspector muestra 'No contract entry yet: …preview' (ui.js:401).

**Escenario:** 1) El socio selecciona GHOST_BELL, que en Unreal es la única ayuda del timbre (anexo 17:74). 2) Pulsa Supr. 3) La tarjeta solo dice '2 elements are anchored to it' y el foco queda en 'Proceed and repair'. 4) Pulsa Enter y la ayuda del timbre desaparece de la partitura sin ninguna mención a Unreal. Otro caso: mueve ALMA_IN de Entering +3 s, o recorta DISCLAIMER a 15 s, y no aparece nada. Cuando llegue F4, esos cambios serán imposibles de compilar o se convertirán en divergencias silenciosas en el APK.

**Arreglo:** Completar contract.json con las 15 filas que faltan del anexo 17 §3.1, con su match por clave y su severidad por verbo (move, trim y delete). Agregar 'value' a los literales (fw.stage por etapa: 180/120/240; disc 19; BLOB 2,5; HelpAfter, etc.) para que C3.DRIFT corra también sobre literales. Agregar 'delete' a wait.* y fw.stage. A los elementos sin entrada, ponerles una marca visible 'not in contract' en el clip, en lugar de no mostrar nada, y mostrar en la barra un contador de cobertura ('107/592 checked').

**Verificador:** Lo central se sostiene. Lo comprobé cargando el app.js real en node, en vB_integ/b1.js. Al mover +1 s cada uno de los 592 elementos salen 347 sin ninguna tarjeta ni toast, 99 con solo un toast informativo, 85 tarjetas de un clic y 61 con motivo. Al borrar salen 357 sin tarjeta (298 + 59 toasts háptico), 138 con solo C1.ORPHANS y 97 con motivo. contract.json tiene 12 entradas contra las 28 filas del catálogo del anexo 17 §3.1, y C3.DRIFT solo corre para kind 'knob' (integrity.js:38). Las derivas citadas son reales. DISCLAIMER dura 20 contra DiscTime 19 (anexo 11:191). BLOB_IN dura 4 contra IntroTime 2,5. VO_16h/27h/32h están a +14 contra 15/20/15. G_SAVE4/5 tienen fw 120, pero en Unreal Attracting y Drawing van por la rama 240. Borrar G_BELL, G_SHARE o GHOST_BELL solo da la tarjeta 'N elements are anchored'. Hay tres matices. (1) Algunos ejemplos están mal: ALMA_IN abre tarjeta con motivo en 5 de sus 6 apariciones, aunque solo por la familia, y CHARGE abre tarjeta en 1 de 5. (2) La cita 'BP_Obra_SC.md:501' es en realidad VR_Test/Saved/ClaudeScripts/obra/dump/obra_all_now.txt:501. (3) La UI sí declara el alcance: C3.SCOPE '0 of 592 reach Unreal', 'No contract entry yet… preview' (ui.js:401) y contract.json se presenta como 'v0'. Como hoy nada llega a Unreal y la partitura no se corrompe, no es crítico.

#### B2 · Fatiga de alertas: toda VO abre tarjeta en cada empujón, la familia infla las tarjetas y Enter acepta con el motivo vacío
- **Severidad:** high (el auditor puso critical)
- **Estado:** en parte
- **Rompe:** fricción
- **Esfuerzo:** M

**Evidencia:** En node, mover cada uno de los 592 elementos abre 146 tarjetas (24,7 %), 61 de ellas con motivo obligatorio. Las VO abren tarjeta 70 de 70 veces (62 de un clic y 8 con motivo). Un segundo movimiento de VO_10 vuelve a preguntar, porque los ítems C3 no se filtran por los aceptados (integrity.js:65-77). Alt+←/→ mueve de a 0,1 s y cada paso es un commit propio (app.js:411-413). En ui.js:463, pulsar Enter en el campo de motivo ejecuta any.click() si el botón está habilitado; app.js:88 guarda reason '' en las tarjetas que solo avisan. Esto contradice el anexo 17:236 ('Nunca Proceed anyway'). integrity.js:61-64 suma Engine.family transitiva a todo 'move' e ignora Ctrl/keepKids (app.js:137). Un Ctrl+move de ALMA_IN (1.R2) +10 s mueve un solo elemento, pero la tarjeta lista 51 VO, 6 ambientes, VEIL y T_IN, y exige motivo (block). Hay 43 tarjetas que salen solo por la familia (26 con motivo), y una sola tarjeta llega a listar 91 claves. Mover un momento solo revisa sus propios elementos (integrity.js:58): 14 de 73 momentos se mueven +60 s sin aviso, aunque el efecto es idéntico. Además hay una base permanente: 2 bloqueos (C1.ANCHOR.CYCLE en 2.R4 y 5.R4; el mensaje 'falls back to 0' es falso, porque los tiempos sí se calculan) y 7 avisos abiertos desde el arranque. No existe un verbo para asignar ayuda ni para re-anclar, ni 'Accept' en Problems (ui.js:289 solo ofrece reopen).

**Escenario:** 1) El socio ajusta 20 VO en una tarde con Alt+→, como haría en Avid. 2) Recibe unas 200 tarjetas modales. 3) Hacia la décima ya pulsa Enter de reflejo, y cada Enter guarda una 'ruptura aceptada' con motivo vacío. 4) El día que aparece un bloqueo real (por ejemplo AMB_04 o T_IN), escribe 'aaaaaaaaaaaa' y sigue. La barra de estado nunca baja de '2 blocking · 7 warnings', así que el contador deja de significar algo.

**Arreglo:** (1) Si un elemento ya tiene aceptada una entrada C3, los movimientos siguientes solo actualizan el delta registrado y se ven en la barra de estado, sin modal. (2) Agrupar los empujones de teclado en una sola operación (debounce de ~800 ms). (3) Pasar keepKids en op y revisar solo los elementos cuyo sched.t cambió de verdad respecto de su etapa, comparando el antes y el después, en lugar de la familia transitiva; usar ese mismo criterio para mover un elemento y para mover un momento. (4) Que Enter en el campo de motivo no ejecute 'Proceed anyway' y que el foco por defecto vaya a Cancel. (5) Arreglar el falso ciclo, o bajarlo a info, y permitir 'Accept…' desde Problems para la base inicial.

**Verificador:** Confirmado en node. Las 70 VO abren tarjeta al moverlas (62 de un clic y 8 con motivo). Cada Alt+flecha es un commit propio: 30 empujones de VO_11 abrieron 30 tarjetas (b7.js). En una tarjeta que solo avisa, el foco va al campo de motivo y Enter ejecuta any.click() (ui.js:463), así que se acepta con motivo ''. Eso contradice el anexo 17:236 ('Nunca Proceed anyway'). opItems suma la familia aunque se use Ctrl (integrity.js:61-64, porque op no lleva keepKids). Un Ctrl+move de ALMA_IN@1.R2 +10 s mueve 1 elemento, pero la tarjeta lista 72 claves y exige motivo. Hay 43 tarjetas que salen solo por la familia (26 con motivo), y la que más lista tiene 91 claves (WALK1). Los dos C1.ANCHOR.CYCLE de base son reales en el grafo, pero los tiempos coinciden con golden, y el mensaje 'falls back to 0' es falso: cae al inicio del momento. Dos ajustes. Son 23 los momentos que se mueven +60 s en silencio, no 14. Y que el segundo movimiento de VO_10 vuelva a preguntar es coherente con el diseño ('huella = regla + ids + parámetro': si cambia el delta, se reabre). Es fricción y confusión, no pérdida de datos, así que no es crítico.

#### B3 · 'Proceed and repair' y 'Delete them too' se aplican después de la verificación y no conservan los tiempos que prometen
- **Severidad:** high (el auditor puso high)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** M

**Evidencia:** En app.js:68-71 la tarjeta se calcula sobre `next` sin reparar, y la reparación recién se aplica en finish() (app.js:82-83). Sin embargo, integrity.js:84 dice 'Re-anchor them to its parent (they keep their times)'. En node, borrar TO_HUD muestra '4 elements are anchored to it' con un total previsto de 16:52. Pero la reparación convierte el `end` de RING_HIDDEN en duración fija (app.js:114), así que deja de ser crossSpan (engine.js:26,52). El momento 2.6 se alarga y 509 elementos (59 VO) se corren +36,3 s: el total real queda en 17:34. Con G_SAVE5 se mueven 123 elementos y el total llega a 18:13. En todo el corpus hay 16 dependientes que se mueven, y el peor 75 s. En 'Delete them too', la tarjeta cuenta solo los hijos directos (integrity.js:81), pero se borra la familia transitiva (app.js:102). Con WALK1 la tarjeta dice '2 elements are anchored to it' y se borran 572 de 592 (67 VO): el total queda en 1:10, sin ningún ítem C3, porque el contrato solo se revisa sobre op.ids (integrity.js:60-64).

**Escenario:** 1) Se selecciona TO_HUD y se pulsa Supr. 2) La tarjeta ofrece 'Proceed and repair (they keep their times)' con el foco. 3) Al pulsar Enter, toda la segunda mitad de la obra se corre 36 s sin ninguna tarjeta ni aviso del total. Otro caso: con 'Delete them too' sobre WALK1, creyendo que son 2 elementos, desaparece casi toda la obra. Se puede deshacer, pero la tarjeta mintió.

**Arreglo:** Simular cada opción de reparación dentro de mutate y correr opItems/staticProblems sobre la partitura ya reparada. Mostrar por opción 'N elements move · total Δ'. Si algún dependiente se mueve más de 1 ms, cambiar la etiqueta. Al convertir end→fixed, conservar la semántica de crossSpan (por ejemplo, con una bandera spansBeat). En 'Delete them too', mostrar el conteo transitivo y la lista de elementos con contrato, y correr C3 sobre todo el conjunto.

**Verificador:** Reproducido con el commit()/applyDeleteRepair reales (b3.js). En app.js:68-71 la tarjeta se calcula antes de la reparación, que recién se aplica en finish(). Al borrar TO_HUD con re-anclaje, RING_HIDDEN pasa de end a fixed (app.js:114), deja de ser crossSpan, se mueven 565 nodos (59 VO) hasta 36,3 s y el total va de 16:58 a 17:34, sin aviso. Con G_SAVE5 el total llega a 18:13. Con WALK1 y 'Delete them too', la tarjeta dice '2 elements are anchored', pero se borran 572 elementos, el total queda en 1:09,6 y quedan 20 anclas colgando. Es aún peor de lo que dice el hallazgo: la reparación ni siquiera toca los momentos anclados al elemento borrado (lo reporto aparte como faltante).

#### B4 · Editar el texto de una VO es silencioso, corre la obra entera y la UI presenta como 'final mix' lo que es una estimación
- **Severidad:** medium (el auditor puso high)
- **Estado:** en parte
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** S

**Evidencia:** En app.js:167-170, setText recalcula dur con voDur(text). El tipo 'text' no está en el mapa de verbos (integrity.js:59) y ninguna entrada del contrato tiene on.text, así que el cambio solo pasa por el filtro de C2 nuevos. En node (exp_verbs.js), alargar el texto de VO_10 (+8,4 s estimados) no avisa, corre 441 elementos y lleva el total de 16:58 a 17:06. Reescribir VO_10 en español tampoco avisa, y la regla dice que los textos in-headset van en inglés (CLAUDE.md §3; anexo 17:38). En Unreal, la VO es un asset grabado que se llama por ruta (contract.json:14-17): si cambia el texto, el APK sigue diciendo el audio viejo. Además, las duraciones 'audio' se muestran con candado ('A voice lasts as long as its audio file', ui.js:368) y como 'final mix' (ui.js:389), pero son estimaciones por texto: VO_10 da 6,92 contra 8,50 de la mezcla real, VO_11h 4,83 contra 3,40 y VO_11 6,83 contra 5,84 (anexo 11:131-138).

**Escenario:** 1) El socio saca dos palabras de VO_11 para ajustar el ritmo. 2) No aparece ninguna tarjeta, y todo lo que viene después se adelanta 0,8 s según la estimación. 3) El socio cree que el tiempo está atado al audio real, porque ve el candado y 'final mix'. 4) En el APK, Alma dice la frase completa con la duración real, y los tiempos que el socio ajustó no corresponden a nada.

**Arreglo:** Tratar 'text' como verbo C3 para las VO cableadas: un aviso que diga 'needs re-recording; the APK plays the old audio' y que marque ≠ APK. No cambiar la duración de una VO cuyo asset ya existe. Sembrar audio.dur desde duraciones_mezcla.txt y rotular las demás como 'estimate', sin candado. Agregar una regla C2 de idioma (inglés) como aviso.

**Verificador:** Confirmado en node (b4.js). setText no tiene verbo C3 ni tarjeta. Alargar VO_10 mueve 486 nodos y lleva el total de 16:58 a 17:03,8 sin aviso, y reescribirla en español tampoco avisa. Ninguna VO tiene audio.dur: las 70 duraciones son estimaciones, por ejemplo VO_10 6,92 contra 8,50 de la mezcla real. Pero el mismo panel Voice muestra 'Changing the text re-estimates the length until the real audio exists' (ui.js:392), así que la estimación está declarada justo donde se edita el texto. Lo engañoso es la contradicción con 'final mix' (ui.js:389) y el candado 'A voice lasts as long as its audio file' (ui.js:368). Hoy no llega a Unreal: es una severidad media.

#### B5 · La huella no lleva parámetro: la regla de los 15:00 está muerta desde el arranque y lo aceptado tapa versiones peores del mismo problema
- **Severidad:** medium (el auditor puso high)
- **Estado:** confirmado
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** S

**Evidencia:** En integrity.js:21 la huella es rule|el, y en :24 TOTAL.GOAL no tiene elemento, así que queda 'C2.TOTAL.GOAL|'. Al arrancar, el total típico es 16:58, ya por encima de 15:00, y opItems solo muestra problemas cuya huella no estaba antes (integrity.js:90-92). En node, mover el momento 1.R2 +60 s lleva el total a 17:58 y la tarjeta solo trae C3.VO.WIRED. Subir G_SHARE.expected a 200 lleva el total a 20:12 y la tarjeta solo trae C2.WAIT.FW. Ninguna edición vuelve a mencionar el total. El anexo 17:51 exige 'regla + ids + parámetro clave… si cambia, se reabre'. Además, el mensaje dice 'Typical total', pero se calcula con la persona activa (app.js:51-53): con Fast muestra 'Typical total 16:29'. HELP.LATE aceptado para VO_11h con el motivo 'aaaaaaaaaaaa' sigue tapando ese problema aunque después cambie el timeout de G_BREATH, porque la huella es la misma.

**Escenario:** Durante una semana, el socio alarga la obra de 16:58 a 19 min en pasos de 10-20 s. El editor nunca lo marca como problema nuevo: solo cambia una cifra en la barra de estado. Si alguien acepta el TOTAL una vez, queda aceptado para siempre, sea cual sea el total.

**Arreglo:** Agregar el parámetro clave a la huella: TOTAL en tramos de 30 s o el valor, HELP.LATE con gate+fw, DRIFT con el valor de la perilla. Calcular TOTAL siempre con la persona Typical. Cuando el total crece por encima de un umbral, mostrar en la tarjeta 'Total 16:58 → 17:58 (+1:00)' aunque ya estuviera excedido.

**Verificador:** La huella de C2.TOTAL.GOAL es 'C2.TOTAL.GOAL|' (integrity.js:21,24). Como el total ya es 16:58 al arrancar, ninguna edición la vuelve a mostrar. Lo probé en b5.js. Mover el momento 1.R2 +60 s lleva el total a 17:58 y la tarjeta solo trae C3.VO.WIRED. Subir expected de G_SHARE a 200 lo lleva a 20:12 y solo sale C2.WAIT.FW. Con la persona Fast el mensaje dice 'Typical total 16:29'. Lo bajo a media porque la barra de estado muestra siempre 'total X · goal 15:00' (ui.js:441): el exceso se ve, aunque nunca genere tarjeta.

#### B6 · El ciclo de vida de '≠ APK' es incoherente: 'reopen' borra el registro, volver al lugar no lo limpia y lo borrado deja aceptados huérfanos
- **Severidad:** medium (el auditor puso high)
- **Estado:** confirmado
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** M

**Evidencia:** Los ítems C3 aceptados se guardan con la huella 'C3.VO.WIRED|id' (app.js:87), que staticProblems nunca genera; integrity.js:49 solo los vuelve a sumar como aceptados. En node (exp_accept.js): mover VO_05 +5 s y luego Proceed anyway lo deja aceptado y con neAPK. Con Reopen (app.js:228-233), VO_05 queda sin ningún problema y con neAPK=false, pero sigue corrida +5,0 s. Si VO_10 se mueve y después se devuelve a su tiempo exacto, neAPK sigue en true. De los motivos solo queda el primero (app.js:88): después de dos movimientos el registro es [""]. Si se borra VO_05, la fila aceptada sigue apuntando a un id que ya no existe. El motivo solo se valida por largo (≥ 12, ui.js:463) y es opcional para los avisos.

**Escenario:** 1) El socio mueve VO_05 +5 s y acepta. 2) Beltrán abre Problems y pulsa 'reopen' para revisarlo. 3) La fila desaparece y el clip pierde la marca ≠ APK. 4) En F4 no queda ningún rastro de que VO_05 diverge del grafo AlmaSpeak, y el APK sale con VO_05 donde estaba.

**Arreglo:** Que ≠ APK sea un estado derivado y no guardado: comparar el tiempo y la duración de cada elemento con una línea de base del APK (score.golden ahora, la cosecha en F3) y emitir un problema estático C3.DIVERGE por elemento. 'Reopen' lo deja Open y no lo borra. Guardar un historial de motivos con su delta. Al borrar un elemento que divergía, pasar su aceptación a un registro 'deleted while diverged'.

**Verificador:** Verificado en b6.js. Si se mueve VO_05 y se acepta, queda neAPK con la fila aceptada. Con Act.reopen la fila y neAPK desaparecen, VO_05 no conserva ningún problema y sigue corrida 7,0 s. Como C3.VO.WIRED no es un problema estático, nada lo vuelve a marcar. Un segundo movimiento con otro motivo conserva solo el primero (app.js:88). Si VO_10 se mueve +2 y después −2, queda en su tiempo original con neAPK=true. Si VO_10 se borra, la fila 'C3.VO.WIRED|el_…' apunta a un elemento que ya no existe. Es pérdida de metadatos de divergencia, no de tiempos, y se puede deshacer: severidad media.

#### B7 · Faltan casi todas las reglas C2/C4 del plan, aunque el plan dice que F1 las incluye
- **Severidad:** medium (el auditor puso high)
- **Estado:** en parte
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** L

**Evidencia:** PLAN-EDITOR-OBRA-2026-10-01.md:425 dice 'F1 ya incluye las 10 reglas MVP', y :463 'una tarjeta de impacto en cada edición que rompe algo'. integrity.js:22-45 solo implementa CYCLE, MISSING, TOTAL, NOHELP, HELP.LATE, FW≤expected, DRIFT y NOTBLOCKING. Del anexo 17:317-328 faltan las reglas 2, 4, 6, 8 y 9, y la 1, la 5 y la 7 están a medias. En node: un Ctrl+move de ALMA_IN +10 s deja a VO_10 (207,2) sonando 8,8 s antes de que Alma aparezca (216,0), y no sale ningún ítem de esa regla. Un Ctrl+drag de VO_11 −8 s la superpone 4,0 s a VO_10 y solo sale la tarjeta genérica de VO. El arrastre se rechaza únicamente si las dos están en la misma pista visual (laneBusy, app.js:253-257); el campo Offset y Alt+flechas ni siquiera revisan eso. Agregar una espera en 3.R3 (Loving), 4.R5 o 9.3 solo produce un toast QUIET '1 new warning', aunque las esperas bloqueantes solo existen en el Hall y en SHARE (PLAN:46-47). Recortar TITLE_IN a 0,2 s no avisa, y el título debe durar ≥ 3 s (anexo 17:89). Borrar HAP_BREATH_HUM solo produce un toast info (anexo 17:76). Desde el arranque ya hay 8 solapes entre VO que no son ayuda y nadie los reporta.

**Escenario:** El socio adelanta el momento en que habla Alma en Entering, o la saca de cuadro, y el editor deja que hable antes de aparecer. O pone dos frases encimadas en pistas distintas de Voice, y la tarjeta solo dice 'Wired in Unreal', que no es el problema. Después, Beltrán confía en que 'Problems' revisó las reglas de la obra.

**Arreglo:** Implementar, con los umbrales en obra/score/rules.json: que Alma hable a partir de su aparición + 1,5 s; que el título no coincida con Alma; dos VO que no son ayuda nunca a la vez; un timeout mayor que la VO del paso + BellHold; nada en el mismo cuadro (±1/72 s) y ninguna aparición de menos de 0,3 s; háptico con final y música sin huecos de más de 1 s, para las 4 personas; esperas bloqueantes solo en el Hall y en SHARE; ningún fantasma en Loving, Save ni Share. Corregir el §8 del plan para que diga qué reglas existen de verdad.

**Verificador:** El código solo implementa CYCLE, MISSING, TOTAL, NOHELP, HELP.LATE, WAIT.FW, DRIFT y NOTBLOCKING (integrity.js:22-45). Verificado: después de un Ctrl+move de ALMA_IN +10 s, VO_10 (207,2) suena antes de que aparezca Alma (216,0) sin ninguna regla. Treinta Alt+← sobre VO_11 la encima a VO_10 en la MISMA pista, porque Act.move y setOffset no llaman a laneBusy, y solo sale C3.VO.WIRED. Al arrancar hay 8 solapes entre VO que no son ayuda, todos en pistas distintas. Matices: algunos de esos solapes pueden ser variantes intencionales (VO_17a/17b, VO_35b/35c), no lo verifiqué. Y 'F1 ya incluye las 10 reglas MVP' (PLAN:425) es una corrección de alcance, aunque el §8 marca F1 como hecho. Hoy no llega a Unreal y los solapes se ven en el timeline: severidad media.

#### B8 · 'Wired in Unreal' se aplica a toda VO: hay falsos bloqueos en las voces creadas en el editor y en VO_01h/VO_03h
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** confusión
- **Esfuerzo:** S

**Evidencia:** contract.json:14 usa match {group:'vo'}, y contractFor (integrity.js:9-16) no excluye las nuevas; Act.add('vo') (app.js:203) no marca isNew. Según el anexo 11:64,193, VO_01h y VO_03h no están cableadas: el Hall no tiene ayuda por voz. En node: después de agregar VO_NEW, moverla abre una tarjeta 'Wired in Unreal — This voice is called by an Unreal graph'. Borrarla exige motivo con el texto 'Deleting the voice here won't silence it in the APK: the graph still calls it'. Borrar VO_01h da el mismo bloqueo falso. El clip muestra el glifo de cable (ui.js:203-205).

**Escenario:** 1) El socio escribe una línea provisoria con Shift+A → Alma voice line. 2) Se arrepiente y la borra. 3) El editor le exige 12 caracteres de justificación y afirma que el APK la seguirá diciendo, cuando la línea nunca existió en Unreal. 4) El socio aprende que las tarjetas mienten, y eso agrava el punto B2.

**Arreglo:** Hacer que vo.wired coincida con una lista explícita de ids (los de DUMP:966-976,1696 y HDSL:33-68). Marcar isNew/created en las VO creadas en el editor y excluirlas del contrato. Pasar VO_01h y VO_03h a kind 'not-in-unreal' (ayuda planeada) hasta que se cableen.

**Verificador:** Verificado en b8.js. Act.add('vo') no marca isNew, y vo.wired coincide por {group:'vo'}. Mover VO_NEW abre 'Wired in Unreal'. Borrarla exige motivo con el texto 'Deleting the voice here won't silence it in the APK: the graph still calls it'. Borrar VO_01h también exige motivo (block C3.VO.WIRED), aunque el anexo 11:64 dice que el Hall no tiene ayuda por voz cableada.

#### B9 · Ilusión de control: la vista 3D y la reproducción ignoran las ediciones, y el aviso es pequeño y a veces desaparece
- **Severidad:** medium (el auditor puso high)
- **Estado:** en parte
- **Rompe:** confusión
- **Esfuerzo:** M

**Evidencia:** app.js:300: durante la reproducción, el cabezal sigue a App.SC.S.t, el reloj del prototipo. El iframe reproduce su propio horario y, en el mismo origen, además carga sus propios EDITS desde localStorage 'sc-timeline-v1' (timeline.js:894,925-930,1206). protoDiff compara la partitura contra score.golden, no contra el iframe en vivo (app.js:55-58). El mensaje vmsg mide 10,5 px y está abajo a la izquierda (editor.css:15). Cuando la persona no es Typical, el mensaje de persona lo reemplaza (ui.js:129-130). La marca ≠ APK solo puede aparecer en los 107 elementos con contrato, así que los 347 que se movieron sin aviso no muestran ninguna marca de 'editado / no está en el APK'. El inspector usa el presente: 'This voice is called by an Unreal graph'.

**Escenario:** 1) El editor de cine mueve VO_10 +2 s. 2) Pulsa Espacio. 3) Escucha y ve la escena en el tiempo viejo mientras el clip del timeline está en la posición nueva. 4) O concluye que el editor no funciona, o juzga el ritmo de oído sobre la versión vieja y sigue ajustando en falso. Como solo algunos clips tienen ≠ APK, supone que los que no lo tienen ya coinciden con el APK.

**Arreglo:** Pasar los tiempos de la partitura al iframe por su capa EDITS (SC expone EDITS y computeSchedule; usar legacy.uid → edit(uid).at/.d) para que el 3D reproduzca la partitura. Mientras tanto, poner una franja fija en el visor 'Preview = prototype timing, not your edits' y una marca 'edited' en cada clip que difiera de golden. Calcular el diff contra SC.BYUID en vivo y no ocultarlo con el mensaje de persona.

**Verificador:** El mecanismo es real. Durante la reproducción el cabezal toma App.SC.S.t (app.js:300). El iframe reproduce su propio horario. protoDiff compara contra score.golden (app.js:55-58). vmsg mide 10,5 px (editor.css:15) y el mensaje de persona lo reemplaza (ui.js:129-130). Pero es una limitación conocida y documentada en el PLAN §8 ('Pendiente: …muestra el timing del prototipo, no el de la partitura editada'), y la UI la avisa en ámbar. Que el iframe cargue EDITS de 'sc-timeline-v1' solo pasa si alguien usó el prototipo en el mismo origen (localhost:8767): es condicional, no lo general. Es confusión, no rotura: media.

#### B10 · El candado de grupo no protege: Supr, el inspector y Alt+flechas lo ignoran
- **Severidad:** low (el auditor puso medium)
- **Estado:** en parte
- **Rompe:** partitura
- **Esfuerzo:** S

**Evidencia:** ui.js:543 avisa 'Group locked: nothing in it can be moved or deleted', pero el candado solo se revisa al arrastrar (ui.js:550) y en el menú contextual (ui.js:626). Supr llama a Act.remove sin revisarlo (app.js:410), igual que Alt+←/→ con Act.move (app.js:413), el botón Delete del inspector (ui.js:736) y los campos Offset/Duration/Timeout del inspector (ui.js:741-751). Ni Act.* ni commit() consultan App.locked, y el candado no se guarda (savePref, app.js:60): al recargar se pierde.

**Escenario:** 1) Beltrán bloquea 'Voice' para que el socio no toque las VO. 2) El socio hace clic en VO_10, que la selecciona aunque el grupo esté bloqueado, y la mueve con Alt+→, o escribe un Offset en el inspector, o pulsa Supr. 3) La edición se aplica igual. Al día siguiente el candado ya no existe.

**Arreglo:** Hacer cumplir el candado dentro de commit(): rechazar cualquier operación cuyos ids, o los elementos que realmente se mueven, caigan en un grupo bloqueado. Guardar los candados en la partitura, firmados por quien los puso, y mostrarlos en el inspector.

**Verificador:** El código lo confirma. App.locked solo se revisa al arrastrar (ui.js:551), en el recorte (ui.js:210) y en el menú (ui.js:626). Supr (app.js:410), Alt+flechas (app.js:413), el botón Delete (ui.js:736) y los campos del inspector (ui.js:741-751) no lo revisan, y savePref no guarda los candados. Pero el escenario es imposible tal como está planteado: el candado vive en la memoria de la pestaña y no se guarda ni se comparte, así que Beltrán nunca podría bloquear algo 'para el socio'. Además, en VO y ambientes el borrado igual abre una tarjeta con motivo, y todo se deshace con Ctrl+Z. Lo que queda es una promesa falsa del toast 'nothing in it can be moved or deleted': baja.

#### B11 · Dos pestañas de edición se pisan en silencio: guardar no controla la revisión y el borrador es compartido
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** S

**Evidencia:** serve_editor.py:77-96: el PUT /api/score escribe lo que llega, sin comparar baseRev. app.js:339 asigna rev = baseRev+1 sin verificar. Por BroadcastChannel solo la vista 3D adopta la partitura (app.js:380), así que dos pestañas de timeline divergen. LS_DRAFT es una única clave compartida (app.js:9,336). app.js:33 descarta en silencio el borrador si baseRev cambió, y la siguiente edición lo sobrescribe. serve_editor.py:137-145 abre el navegador aunque el servidor ya esté corriendo: un segundo doble clic en abrir-editor.bat da otra pestaña de edición completa.

**Escenario:** 1) Beltrán abre el editor dos veces con el .bat. 2) En la pestaña A ajusta VO y en la B ambientes. 3) A guarda la rev 3 y después B guarda otra rev 3: las ediciones de A desaparecen de score.json sin ningún aviso (quedan solo en history/). Mientras tanto, cada pestaña sobrescribe el borrador de la otra.

**Arreglo:** PUT con If-Match: baseRev → 409 y un diff cuando la base es vieja. Un aviso de 'edición en curso' por BroadcastChannel que deje en solo lectura la segunda pestaña de timeline. Clave de borrador por pestaña, y ofrecer la recuperación de un borrador con base vieja en lugar de descartarlo.

**Verificador:** serve_editor.py:77-96 escribe el PUT sin comparar la revisión, y app.js:339 calcula rev = baseRev+1 a ciegas. El BroadcastChannel solo adopta la partitura en view=3d (app.js:380). LS_DRAFT es una sola clave compartida (app.js:9,336), y el borrador con otra base se ignora en silencio (app.js:33). En el arranque, el Timer de webbrowser.open se dispara antes de que falle el bind, y el comentario 'the browser still opens on it' confirma que un segundo .bat abre otra pestaña de edición completa. El PLAN:114 describía justo este 'gana el último' como un problema del prototipo viejo, y el editor nuevo lo repite. La copia sobrevive en history/, por eso es media.

#### B12 · Cargar un WAV puede duplicar una clave existente y pisar otro WAV de la bandeja sin aviso
- **Severidad:** medium (el auditor puso medium)
- **Estado:** en parte
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** S

**Evidencia:** app.js:364 deriva el nombre con cleanId(file.name) en los sonidos FX_NEW_SOUND. app.js:367 fija x.key = name sin la verificación de unicidad que sí tiene rename (app.js:220). 'audio' es QUIET (app.js:63). serve_editor.py:121-123 sobrescribe inbox/<name>.wav, mientras que rename sí devuelve 409 (:108-109). En node: 'VO_10.wav' queda como VO_10, 'AMB_04.wav' como AMB_04 y 'FX_DISCLAIMER.wav' como FX_DISCLAIMER, y las tres chocan con claves existentes. El anexo 17:108 pide BLOQUEAR por el nombre del asset de una VO, porque importar_mezcla.py busca por nombre.

**Escenario:** 1) El socio crea un 'Empty sound'. 2) Arrastra una toma suya que se llama VO_10.wav. 3) Sin ninguna tarjeta, el sonido FX pasa a llamarse VO_10 y queda en obra/audio/inbox/VO_10.wav, que en la importación chocará con la voz real de Alma. Si ya había otro WAV nuevo con ese nombre en la bandeja, se pierde.

**Arreglo:** Aplicar uniqueKey() al nombre derivado, y que el servidor devuelva 409 si el archivo ya existe en la bandeja. No derivar prefijos VO_/AMB_ para un sonido FX vacío. Pasar 'audio' por la verificación C3 de renombrado.

**Verificador:** Comprobado: cleanId('VO_10.wav') da 'VO_10', 'AMB_04.wav' da 'AMB_04' y 'FX_DISCLAIMER.wav' da 'FX_DISCLAIMER' (b12.js). loadWav no verifica unicidad (app.js:364-367) y 'audio' es QUIET. El POST /api/audio sobrescribe inbox/<name>.wav, mientras que rename sí devuelve 409 (serve_editor.py:108-109 contra :121-123). Pero el planteo de 'duplicar una clave' no se sostiene: las claves no son únicas por diseño, y al arrancar hay 55 repetidas (FX_GHOSTAPPEAR×9, ALMA_IN×6…). El riesgo real es otro. Un WAV nuevo en la bandeja con el nombre de un asset real (VO_10) chocará en la importación por nombre. Y dos sonidos nuevos con el mismo nombre derivado se pisan el archivo en la bandeja sin aviso.

#### B13 · Entradas numéricas sin validar: vaciar un campo pone una duración en 0 sin tarjeta
- **Severidad:** low (el auditor puso low)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** S

**Evidencia:** ui.js:744 llama a Act.trim(id, parseFloat('')) → NaN, y app.js:155 no tiene isFinite (setGate y setOffset sí, en app.js:159,163); engine.js:46 resuelve `e.dur.value || 0` como 0. En node, vaciar la duración de DISCLAIMER no avisa y el total baja de 16:58 a 16:38. Un setGate con expected −10 tampoco avisa. Un fw menor que expected solo da un aviso de un clic (C2.WAIT.FW), y con Enter queda aceptado.

**Escenario:** El socio borra el valor del campo Duration de DISCLAIMER para escribir otro, hace clic afuera, y el elemento queda en 0 s: toda la obra se adelanta 20 s. El valor se guarda como null en score.json.

**Arreglo:** Validar con isFinite y rangos en Act.trim y Act.setGate (expected ≥ 0,5; fw > expected; duración ≥ 0,1), como invariantes que rechazan el gesto sin 'Proceed anyway'. Si el valor no es válido, devolver el input al valor anterior.

**Verificador:** Verificado en b13.js. Act.trim(DISCLAIMER, NaN) no abre tarjeta, deja dur.value NaN (null en el JSON) y el total pasa de 16:58 a 16:38. Además, setGate(G_BELL,'expected',−10) no abre tarjeta y deja G_BELL en [69, 59], una duración negativa que adelanta 15 s a sus 6 anclados. Se ve en el timeline y se deshace: baja.

#### +B1 · 'Proceed and repair' no re-ancla los momentos: borrar uno de 18 elementos manda un momento entero a 0:00
- **Severidad:** high
- **Rompe:** partitura

**Evidencia:** Hay 20 momentos anclados a elementos: WALK1>1.6, CANDS_IN>2.5, VO_06a>2.7a, PASO>2.7b…2.7f, ENV1_IN>1.R2, VO_10>1.R3, VEIL_OPEN>2.R2/3.R2/4.R2/5.R2, VO_15>2.R4, VO_20>3.R3, VO_26>4.R3, VO_31>5.R3, FINAL>9.1b y SHARE_PRESS>9.5b. applyDeleteRepair solo recorre n.elements (app.js:107-108) e ignora n.beats. En engine.js:34, la caída de un ancla colgada usa E[self], que es undefined para un momento, así que devuelve 0. En integrity.js:92 la tarjeta de borrado oculta C1.ANCHOR.MISSING ('its repair re-anchors them'), y la reparación ofrecida dice 'they keep their times' (integrity.js:84). Medido en node (vB_integ/m1.js): al borrar PASO con la reparación por defecto, el momento 2.7b pasa de 156,5 s a 0,0 s y el total de 16:58 a 14:21. Al borrar VEIL_OPEN de Recognizing, después de dar motivo, 2.R2 pasa de 363,7 s a 0 y el total queda en 10:54. Al borrar VO_10, 1.R3 pasa de 214,1 a 0. Después, el problema estático dice 'falls back to the start of its moment', y eso es falso para un momento.

**Escenario:** 1) El socio selecciona PASO (una pieza de 4,5 s en el Hall) y pulsa Supr. 2) La tarjeta dice '1 element is anchored to it' y el foco queda en 'Proceed and repair (they keep their times)'. 3) Pulsa Enter. 4) El momento 2.7b y todo lo que se encadena después salta a 0:00 y se superpone al inicio de la obra, sin ninguna tarjeta que lo diga. Solo aparece un '3 blocking' en la barra. Si guarda con Ctrl+S, score.json queda con la segunda mitad de la obra apilada en el arranque.

**Arreglo:** En applyDeleteRepair, recorrer también n.beats. Si b.at.ref es el elemento borrado, copiar su ancla con off = t[b][0] − base, igual que con los elementos. En el motor, que un momento con ancla colgada caiga al final del momento anterior (prevBeat) y no a 0. Después correr staticProblems sobre la partitura ya reparada y bloquear el gesto si reaparece C1.ANCHOR.MISSING o si algún tiempo cambia más de 1 ms.

#### +B2 · Aceptar una tarjeta marca '≠ APK' y registra la aceptación solo en el primer elemento de cada entrada del contrato
- **Severidad:** medium
- **Rompe:** experiencia en Unreal

**Evidencia:** opItems agrupa todos los elementos de una misma entrada en un solo ítem (clave c.id|sv) y solo agrega sus nombres a 'keys'; el.el queda en el primero (integrity.js:71). En app.js:86-89, la huella aceptada y neAPK usan solo it.el. Medido en node (vB_integ/m2.js). Al mover ALMA_IN@1.R2 +3 s y aceptar con motivo, se mueven 80 elementos con contrato, la tarjeta lista 67 y solo 7 quedan con ≠ APK: VO_10, G_BREATH, AMB_05, VEIL_CLOSE, T_IN, G_GRAB y G_SAVE4. Problems recibe 7 filas. VO_11 a VO_37, AMB_06-09, VEIL_OPEN y T_OUT se movieron sin ninguna marca. Al mover el momento 2.R4 +10 s se mueven 64 elementos con contrato y solo VO_16 y G_HEART quedan marcados.

**Escenario:** 1) Beltrán ajusta la entrada de Alma en Entering y acepta la tarjeta, que lista 51 voces. 2) En el timeline, solo VO_10 lleva el borde ámbar de ≠ APK, y 'Affects APK' en Problems muestra 7 filas. 3) En F4, la lista de divergencias que tiene que pasar a Unreal omite las otras 50 voces que también cambiaron respecto de AlmaSpeak/StageCues. El APK sale con esas VO donde estaban, y nada lo señala.

**Arreglo:** Al aceptar, iterar it.keys o guardar en cada ítem la lista de ids, no solo su key. Crear una fila aceptada y marcar neAPK por cada elemento cuyo tiempo cambió de verdad, comparando sched antes y después. Mejor aún: derivar ≠ APK como estado calculado contra la línea de base (golden ahora, la cosecha en F3), como propone B6.

#### +B3 · 'Import score…' reemplaza la partitura entera sin pasar por la integridad, y un archivo mal formado deja el editor en blanco al recargar
- **Severidad:** medium
- **Rompe:** partitura

**Evidencia:** importScore (app.js:350-353) no usa commit(). Solo valida schema===2 y elements, pone App.score = s, llama a markDirty() y recién después a compute(). No muestra tarjeta ni diff, confía en el 'accepted' del archivo tal cual y no actualiza baseRev. Medido en node (vB_integ/m3.js). Importar una exportación anterior descarta en silencio las ediciones hechas después: solo sale el toast 'Imported score-rev2.json', y la siguiente vez que se guarda, el archivo queda como rev base+1. Con un JSON {schema:2, elements:{}}, compute lanza 'score.acts is not iterable', pero App.score ya quedó reemplazada y markDirty guarda ese borrador roto 400 ms después. En la recarga, boot (app.js:32-37) restaura el borrador porque coincide baseRev y llama a compute() fuera de todo try: la app queda en blanco y no se llega a 'Reload from disk'.

**Escenario:** 1) El servidor solo escucha en 127.0.0.1, así que el socio le manda a Beltrán su score exportado. 2) Beltrán usa File ▸ Import score…. 3) Todas las ediciones que hizo desde la base del socio desaparecen sin aviso, y las aceptaciones del archivo ajeno pasan a ser las suyas. Otro caso: el archivo está incompleto, la pantalla queda rota y Beltrán recarga. El editor no vuelve a abrir hasta que alguien borra 'sc-editor-draft-v1' desde las herramientas del navegador.

**Arreglo:** Pasar la importación por commit() con op 'import'. Mostrar una tarjeta con el diff (N elementos movidos, Δ del total, problemas nuevos) y la opción Cancel. Validar el esquema completo (acts, beats, lanes, groups) y correr resolve() ANTES de reemplazar App.score. No llamar a markDirty si compute falla. En boot, envolver la restauración del borrador en try/catch y descartarlo con un aviso si no calcula.

#### +B4 · 'Ctrl: alone' no deja quieto al resto cuando un momento está anclado al elemento: VO_10 con Ctrl mueve 485 nodos
- **Severidad:** medium
- **Rompe:** confusión

**Evidencia:** keepKids solo compensa n.elements[k] con at.ref===id (app.js:137). Los momentos anclados al final del elemento (20 casos: VO_10>1.R3, VO_15>2.R4, VO_20>3.R3, VO_26>4.R3, VO_31>5.R3, VEIL_OPEN×4, PASO×5, WALK1, FINAL, SHARE_PRESS…) no se compensan. Los anclados por 'end' tampoco. La UI promete lo contrario: 'Ctrl+drag moves it alone' (ui.js:437-438) y '· Ctrl: alone' durante el arrastre (ui.js:600). Medido en node (vB_integ/b6b.js). Un Ctrl+move de VO_10 +2 s mueve 485 elementos, es decir, toda la obra desde Entering, y suma 2 s al total. En cambio, un Ctrl+move de ALMA_IN mueve solo 1 elemento. Así, la misma tecla tiene dos efectos opuestos según cómo esté anclado el clip, y eso no se ve.

**Escenario:** 1) El editor de cine quiere correr la frase VO_10 2 s sin tocar nada más, como un slip en Avid, y la arrastra con Ctrl. 2) El estado dice 'Ctrl: alone'. 3) Al soltar, todo Entering y las etapas siguientes se corren 2 s. La tarjeta lista 51 VO, que en este caso sí se movieron, pero el socio ya aprendió con B2 que esa lista es ruido inflado por la familia. Acepta, y el resto de la obra queda desplazado sin que lo haya querido.

**Arreglo:** En keepKids, compensar también los momentos con at.ref===id y los dependientes por 'end' (convertir a ancla equivalente). Pasar keepKids en op para que opItems revise solo lo que de verdad se movió (sched antes contra después). Si el elemento ancla un momento, mostrar durante el arrastre 'moment X follows' en lugar de 'Ctrl: alone'.

### C · Usabilidad

El editor parece y se siente como un NLE profesional: tiene el chrome de ISP, imán con línea de snap, fantasma rojo cuando el carril está ocupado, pistas en la barra de estado y deshacer completo. El problema es que su modelo de tiempo es una cadena "magnética": mover, recortar o borrar un clip que cierra su momento corre el resto de la obra, y la interfaz no lo dice. En el peor caso, Supr seguido de Enter (Proceed and repair) manda un momento a 0:00 y baja el total de 16:57 a 14:21, mientras la tarjeta promete que los dependientes conservan sus tiempos. La previsualización no muestra lo editado: no hay audio, las ondas son decorativas y el visor 3D reproduce los tiempos del prototipo. Los avisos de integridad hablan en jerga de Unreal y saltan demasiado: 146 de 592 elementos abren la tarjeta con un toque de 0,1 s, y al arrancar hay 2 "blocking" falsos. Al mismo tiempo, el 72 % de los elementos (426 de 592) no deja ninguna señal al editarlos, así que el socio aprenderá a aceptar con Enter sin leer. A un editor de Premiere/Avid le faltan J/K/L, I/O, multiselección, copiar/pegar y la posibilidad de re-anclar, y Alt y Ctrl hacen cosas distintas de las que espera.

#### C1 · Borrar con 'Proceed and repair' manda el momento siguiente a 0:00 y acorta la obra, mientras la tarjeta promete lo contrario
- **Severidad:** critical (el auditor puso critical)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** S

**Evidencia:** Navegador (pestaña propia, deshecho después): seleccioné PASO (2.7a) y pulsé Supr. La tarjeta dijo 'Needs a decision · 1 element is anchored to it — They would lose their anchor: bt_1j1fdq88a1.' con la opción marcada '◉ Re-anchor them to its parent (they keep their times)' y el foco en 'Proceed and repair' (ui.js:464). Al hacer clic: toast 'Done', App.sched.t['bt_1j1fdq88a1'] = [0, 4.5] (antes 156.5 s), total 16:57 → 14:21 y la barra pasó a '3 blocking · 6 warnings' (desapareció C2.TOTAL.GOAL). Causas: app.js:107-108 `const e = n.elements[k]; if (!e) continue;` salta los dependientes que son momentos; engine.js:34 un ancla colgante de un momento cae a 0 porque E[self] no existe; integrity.js:83 imprime el id crudo `(E[k]||{}).key || k`; integrity.js:23 dice 'falls back to the start of its moment', falso para un momento. Barrido en node (scratchpad/audit/del.js): 20 elementos tienen un momento encadenado y borrar 65 elementos con la reparación por defecto cambia el total en más de 0,5 s (un VEIL_OPEN −462 s, VO_20 −455 s, VO_15 −373 s).

**Escenario:** 1) El socio selecciona PASO y pulsa Supr. 2) Pulsa Enter, porque el foco está en el botón primario. 3) El momento 2.7b y lo que cuelga de él saltan a 0:00 y el total baja a 14:21. 4) El aviso 'over the 15:00 goal' desaparece y cree que acortó la obra. 5) Si guarda, score.json queda con un momento colgado del principio.

**Arreglo:** En applyDeleteRepair, re-anclar también los momentos: n.beats[k].at = {ref: gone.at.ref, edge: gone.at.edge, off: t[k][0] − base}. Usar keyOf() para nombrar momentos en la tarjeta y en C1.ANCHOR.MISSING ('2.7b', no 'bt_…'). Mostrar en la tarjeta el delta del total ('La obra pasa de 16:57 a 14:21') y poner el foco en Cancel cuando el total cambie más de 1 s.

**Verificador:** Lo reproduje en node con el engine y la integridad reales, replicando commit() y applyDeleteRepair() (scratchpad/audit/zz_verifC_usab_7q3/c1.js). Al borrar PASO (el_1ijygavs89, 152.03-156.53 s), la tarjeta muestra un solo ítem 'inv' con el id crudo: 'They would lose their anchor: bt_1j1fdq88a1'. Por defecto queda marcado 'Re-anchor them…'. Como no hay ítems warn ni block, ui.js:458 y 464 ponen el foco en 'Proceed and repair'. Al aceptar, 2.7b pasa a [0, 4.5], su at sigue apuntando a el_1ijygavs89 (colgado), el total baja de 1018.0 a 861.5 s y aparece C1.ANCHOR.MISSING (block). La causa es la que se describe: app.js:108 salta los dependientes que no son elementos y engine.js:34 devuelve 0 para un momento. El barrido coincide con el auditor: 65 borrados cambian el total más de 0,5 s, y en 20 elementos la reparación deja un momento colgado. Además, el plan §8 afirma que la reparación 're-ancla a los dependientes conservando sus tiempos', lo que este caso desmiente. Mantengo 'critical' porque el camino por defecto, con Enter, corrompe la partitura (ancla colgada y unos 500 ítems re-cronometrados) y la tarjeta promete lo contrario. Ctrl+Z lo recupera mientras no se guarde.

#### C2 · El ripple es invisible e inconsistente: mover, recortar o borrar un clip que cierra su momento corre toda la obra sin aviso
- **Severidad:** high (el auditor puso high)
- **Estado:** en parte
- **Rompe:** confusión
- **Esfuerzo:** M

**Evidencia:** Navegador: Act.trim(PASO, 9.5), lo mismo que soltar el borde derecho, llevó el total de 1018.0 a 1023.0 y 2.7b de 156.5 a 161.5 sin tarjeta ni toast (app.js:79 `if (!shown.length) { finish(); … }`; integrity.js:60-64 solo amplía `touched` con la familia en move/offset, no en trim). Node, hidden.js: en 144 de 592 elementos, mover 1 s corre ítems fuera de la familia que muestra el hint (DISCLAIMER: 661). Node, ctrl.js: Ctrl+arrastrar VO_02 +2 s, que la barra rotula '· Ctrl: alone' (ui.js:600), corre igual 603 ítems porque app.js:137 solo compensa hijos que son elementos. ui.js:257 `const y = El(k); if (!y) continue;` no dibuja la curva hacia un momento dependiente. Node, beatsilent.js: en 23 de 73 momentos, arrastrar el chip 3 px o más (ui.js:540, 569) mueve hasta 665 ítems sin tarjeta. En cambio, mover PASO +5 s (familia explícita) abre una tarjeta con 7 ítems y 3 'Breaks'.

**Escenario:** El socio viene de Premiere, donde se sobrescribe y se hace lift por defecto y el ripple es una herramienta aparte. Alarga PASO 5 s para dar aire. Todo lo posterior se corre 5 s, incluidos títulos y velos que en Unreal son literales, y el total sube a 17:03 sin explicación. O hace clic en un chip de momento para navegar, se le va 4 px y corre 650 ítems en silencio.

**Arreglo:** Mostrar siempre el efecto aguas abajo en el fantasma y la barra de estado ('+5.0 s · 556 ítems posteriores se corren · total 17:03'). Calcular los ítems de la tarjeta sobre el diff real de tiempos (todo lo que se movió), no sobre op.ids o la familia. Que Ctrl aísle de verdad (re-anclar el momento siguiente a su tiempo actual) o cambiar el texto. Exigir un umbral mayor (6 px o más) o Alt para arrastrar chips de momento. Dibujar la curva hacia los momentos dependientes.

**Verificador:** Lo central se confirma en node (c2.js). Act.trim(PASO, 9.5) es silencioso, mueve 559 entradas y lleva el total de 1018.0 a 1023.0 s. Mover PASO +5 s abre una tarjeta con 7 ítems visibles y 3 block. Mover cualquier elemento 1 s corre ítems fuera de la familia mostrada en 144 de 592 casos, 94 de ellos sin tarjeta. ui.js:257 no dibuja curvas hacia momentos. Arrastrar el chip es silencioso en 23 de 73 momentos. Hay tres correcciones. (1) VO_02 no tiene dependientes (kids = []), así que la causa no es que app.js:137 compense solo elementos: el ripple viene de la cadena implícita de momentos (el momento termina con su último elemento, engine.js:29 y 52, y el siguiente se encadena a ese final). El texto 'Ctrl: alone' engaña igual. (2) Al arrastrar un chip de momento, la barra sí dice 'everything after it moves too' (ui.js:574 y 439), así que ahí el ripple no es invisible. (3) El deslizamiento necesario no es siempre 3 px: el imán devuelve el chip a su propio inicio y solo 11 de los 23 momentos se mueven con 3-3,5 px; el resto necesita 5,5-6 px. Agrego evidencia que el auditor no vio: las operaciones QUIET también corren la obra en silencio. 'Add ▸ Wait' a 1 s del momento siguiente alarga el total en 47 de 72 momentos (hasta 5 s) y el único aviso es el toast '1 new warning' por C2.WAIT.NOHELP (add.js). Editar el texto de una VO también re-estima su duración sin pasar por el contrato, que no tiene verbo 'text'.

#### C3 · La tarjeta de impacto habla en jerga de Unreal y salta en cada toque: entrena a aceptar con Enter
- **Severidad:** high (el auditor puso high)
- **Estado:** confirmado
- **Rompe:** confusión
- **Esfuerzo:** M

**Evidencia:** Navegador: Alt+→ (0,1 s) sobre VO_02 abre una tarjeta modal: 'Move · VO_02 · 1 to review / Changes · Wired in Unreal — This voice is called by an Unreal graph (by asset path, or by array index in the Hall). Its timing there is decided by AlmaSpeak, StageCues, StepStageVO or HallSay. / BP_Obra_SC · stage BPs · HallDirector › …'. El foco cae en el motivo, y Enter pulsa 'Proceed anyway' (ui.js:463). Node, card.js: 146 de 592 elementos abren tarjeta con un toque de 0,1 s, y después de aceptar el siguiente toque vuelve a preguntar (opItems, integrity.js:56-78, no consulta score.accepted). Mover PASO lista 57 VO, 8 ambientes, velos y títulos que el usuario no tocó. Vocabulario: ui.js:451 'Changes'/'Breaks'/'Needs a decision'; ui.js:12 'Wired' frente a 'Hardwired'. Falta la línea 'In the APK today: …' que piden el plan (§0.b, línea 89) y el anexo 17 (línea 57).

**Escenario:** El socio ajusta una VO con diez toques de Alt+→ y recibe diez tarjetas con nombres de grafos. A la tercera pulsa Enter sin leer. Cuando aparezca un 'Breaks' real (un velo literal), también lo acepta con Enter.

**Arreglo:** Abrir la tarjeta con una frase de consecuencia en lenguaje de montaje, con tiempos: 'En el visor de hoy VO_02 sigue empezando en 1:27.8 (lo decide Unreal); este cambio queda solo en la partitura'. Plegar los nombres técnicos en 'Details'. Recordar la aceptación por elemento y regla hasta el próximo guardado y no volver a preguntar en nudges. Resumir lo arrastrado aguas abajo en una línea ('también corre 88 cosas que Unreal cronometra solo'). Explicar Wired y Hardwired en un tooltip.

**Verificador:** c3.js: un toque de 0,1 s abre tarjeta en 146 de 592 elementos (vo 70, world 23, obj 22, int 18, amb 11, pawn 2). En 85 basta un clic o Enter, porque ui.js:463 hace que Enter en el motivo pulse 'Proceed anyway' cuando el motivo es opcional. Los otros 61 exigen escribir 12 caracteres en cada toque. Tras aceptar VO_02, el siguiente toque vuelve a abrir la tarjeta: opItems (integrity.js:56-78) nunca consulta score.accepted, aunque el anexo 17 §1.2 dice que lo aceptado 'sigue aceptado mientras la huella no cambie'. El texto de la tarjeta es el citado ('…decided by AlmaSpeak, StageCues, StepStageVO or HallSay', con dueño 'BP_Obra_SC · stage BPs · HallDirector › …'). Ni 'In the APK today' ni 'Check piece' existen en el JS (grep vacío), aunque el plan §0.b (líneas 86-93) y el anexo 17 §1.3 los piden.

#### C4 · La previsualización no se puede escuchar: no hay audio, las ondas son decorativas y la duración estimada de la VO se rotula 'final mix'
- **Severidad:** high (el auditor puso high)
- **Estado:** confirmado
- **Rompe:** confusión
- **Esfuerzo:** M

**Evidencia:** Navegador: App.SC.S.sound = false y Object.keys(App.SC.AUDIO).length = 0. app.js:319 pone S.started = true sin startPiece(true). En el prototipo, timeline.js:412 (syncAudio) sale si !S.sound y timeline.js:509-511 (initAudio) retorna sin window.claude, que no existe en el servidor local. ui.js:220-224: wave() dibuja la onda con un LCG sembrado con la key. Node, votext.js: en las 70 VO, dur.value es exactamente voDur(text) (1 s + palabras ÷ 2.4), con error máximo 0.00, y ninguna tiene e.audio. Sin embargo, el inspector de VO_02 dice 'Duration 19.9 s · its audio' con candado (ui.js:368) y 'Audio VO_02 · final mix' (ui.js:389), y justo debajo una nota admite que es una estimación (ui.js:392).

**Escenario:** El socio alinea un FX con el final de la frase de VO_06c mirando la onda y el borde del clip. La onda es ruido inventado y el borde sale de contar palabras; en el visor, la mezcla real dura otra cosa. Pulsa Play para escuchar el corte y no suena nada.

**Arreglo:** Servir los WAV y la mezcla en local (obra/audio o un /_blob local) y decodificarlos tanto para Play como para dibujar ondas reales, con picos precalculados en JSON. Mientras no haya audio, rotular 'estimated from text' en el clip y en el inspector, quitar el candado y 'final mix', y no dibujar onda.

**Verificador:** c4.js: las 70 VO tienen dur.mode 'audio', su valor coincide exactamente con voDur(text) (error máximo 0) y ninguna tiene e.audio. En el prototipo, initAudio (timeline.js:509-511) sale si no hay window.claude, y syncAudio (timeline.js:410-412) sale si !S.sound. El editor pone S.started = true sin startPiece(true) (app.js:319), así que S.sound queda en false. wave() es un LCG sembrado con la key (ui.js:220-224). El inspector muestra 'its audio' con candado (ui.js:368) y 'final mix' (ui.js:389), y la nota de ui.js:392 lo contradice. Para un montajista, una onda falsa con candado lleva a decisiones de corte equivocadas, y Unreal cronometra las VO con el audio real.

#### C5 · El visor 3D nunca refleja la edición y el aviso casi no se ve
- **Severidad:** high (el auditor puso high)
- **Estado:** confirmado
- **Rompe:** confusión
- **Esfuerzo:** M

**Evidencia:** Navegador: tras borrar PASO, con el cabezal en 2:32, el timeline mostraba Etapa 2 · Recognizing y el visor seguía con el subtítulo de Entering ('Your journey has five stages.'). El único aviso es una píldora ámbar de 10,5 px abajo a la izquierda: '3D shows the prototype's own timing · 559 elements of your score differ' (ui.js:129-131, editor.css:15). Durante Play, el cabezal lo maneja el reloj del prototipo (app.js:300 `App.ph = App.SC.S.t`). Con un usuario simulado distinto de Typical, el visor sigue en Typical (ui.js:129). El plan §8 lo reconoce como pendiente.

**Escenario:** El socio corre VO_02 +2 s y pulsa Play para ver el resultado. El visor la muestra donde estaba, y el socio concluye que el cambio no hizo nada o, peor, aprueba el montaje mirando un monitor que muestra la versión vieja.

**Arreglo:** Inyectar en el prototipo la agenda resuelta de la partitura: sobrescribir c.s y c.e de SC.CLIPS por legacy.uid y llamar a computeSchedule, al menos para los elementos de tiempo puro. Mientras tanto, poner una banda ámbar visible arriba del visor ('Viewer: original timing · tus cambios no se ven aquí') y, en el inspector, 'In the 3D view: 1:27.8' por elemento.

**Verificador:** Se confirma en código y en mi pestaña. #vmsg mide 10.5px, está abajo a la izquierda y tiene pointer-events:none (editor.css:15). Durante Play, App.ph = App.SC.S.t (app.js:300). ui.js:129-131 muestra un solo mensaje, y con un usuario simulado distinto de Typical el aviso de diferencias (protoDiff) ni siquiera se ve. El plan §8 lo reconoce como pendiente ('muestra el timing del prototipo, no el de la partitura editada'), pero eso no le quita impacto: el monitor de programa no refleja la edición. Verifiqué además que el reloj del prototipo se detiene en su propio TOTAL (App.SC.seek(1050) → S.t = 1017.997), lo que agrava el problema (ver el hallazgo nuevo sobre Play).

#### C6 · El chip '≠ APK' no marca lo que divergió y no queda rastro de lo editado
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** M

**Evidencia:** Node, anyway.js: tras 'Proceed anyway' al mover PASO +5 s, solo 7 elementos reciben neAPK (VO_06c, SILENCIO, G_BREATH, VEIL_CLOSE, T_IN, G_GRAB, G_SAVE4), aunque se movieron 88 elementos con contrato. app.js:88-89 marca solo it.el, el primero de cada entrada de contrato. Node, nocontract.js: 426 de 592 elementos (fx 180, obj 135, world 68, int 24, ui 12, pawn 7) no tienen entrada de contrato, así que moverlos, recortarlos o borrarlos no da ni tarjeta ni chip. El ámbar 'editado aquí y todavía no en Unreal' del plan §2.4 (línea 247) no está construido y no hay una lista de cambios desde el último guardado.

**Escenario:** Antes de pasarle el trabajo a Beltrán, el socio busca qué tocó. Ve 7 chips '≠ APK' y supone que el resto coincide con el APK. En realidad nada llega a Unreal (0 of 592) y movió 88 cosas cableadas, además de decenas de objetos del Hall.

**Arreglo:** Marcar en ámbar todo elemento cuyo tiempo difiera de la última revisión guardada o de golden. Poner el chip a todas las keys del ítem aceptado. Agregar un filtro 'Changed' navegable en Problems y en la Library. Rebautizar el chip como 'accepted break' para no sugerir que lo demás coincide con el APK.

**Verificador:** c6.js: 'Proceed anyway' al mover PASO +5 s marca neAPK en solo 7 elementos (VO_06c, SILENCIO, G_BREATH, VEIL_CLOSE, T_IN, G_GRAB, G_SAVE4), aunque se movieron 88 elementos con contrato (sin contar not-in-unreal). La causa es app.js:89, que marca solo it.el. Hay 426 elementos sin entrada de contrato (fx 180, obj 135, world 68, int 24, ui 12, pawn 7). Ni el ámbar 'editado aquí' (plan línea 247) ni una lista de cambios existen en el JS. Es 'medium' porque hoy nada llega a Unreal; el daño aparece cuando F4 tenga que decidir qué divergió.

#### C7 · Dos pestañas: la pestaña 3D deja editar y pierde el trabajo, y dos pestañas de timeline se pisan en silencio
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** S

**Evidencia:** ui.js:36 dibuja el selector All-in-one | 3D view | Timeline también con ?view=3d. app.js:338: en esa pestaña, save() solo muestra 'Save from the timeline tab.'. app.js:380: la pestaña principal ignora d.score (solo lo aplica si App.view === '3d'). app.js:420: beforeunload no avisa en la pestaña 3D. app.js:336: todas las pestañas escriben la misma clave sc-editor-draft-v1. app.js:33: un borrador con otro baseRev se ignora sin aviso. serve_editor.py:77-96: el PUT no comprueba la revisión (gana el último).

**Escenario:** 1) El socio usa 'Window ▸ Open the 3D view in a new tab' y en esa pestaña pulsa 'Timeline', que está a la vista. 2) Corre tres VO y Ctrl+S responde 'Save from the timeline tab'. 3) En la pestaña principal sus cambios no están, y en cuanto edita algo ahí, el broadcast pisa también la pestaña 3D. Otro caso: con dos pestañas de timeline (Beltrán y el socio en la misma máquina), el segundo Ctrl+S borra lo que guardó el primero, y ambas siguen mostrando 'rev 2'.

**Arreglo:** Con ?view=3d, ocultar el selector de ventana y los verbos de edición (pestaña de solo lectura). Usar una clave de borrador por pestaña. Enviar baseRev en el PUT y responder 409 si el disco cambió, con un diálogo 'otra pestaña guardó la rev 3'. Avisar con un toast cuando se descarta un borrador por baseRev distinto.

**Verificador:** Se confirma por código. renderTop dibuja el selector All-in-one | 3D view | Timeline sin mirar App.view (ui.js:36), así que la pestaña 3D puede pasar a Timeline y editar. save() la rechaza (app.js:338). La pestaña principal ignora d.score (app.js:380). beforeunload no avisa con view=3d (app.js:420). Todas las pestañas escriben la misma clave de borrador (app.js:336). Un borrador con otro baseRev se descarta sin aviso (app.js:33). El PUT no compara revisiones (serve_editor.py:77-96): gana el último, y la copia anterior solo queda en obra/score/history. Una imprecisión menor: tras guardar, la pestaña que guardó muestra rev 3; las dos terminan escribiendo 'rev 3' y nadie detecta el choque.

#### C8 · Problems arranca con 2 'blocking' falsos y no ofrece ninguna acción
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** confusión
- **Esfuerzo:** S

**Evidencia:** Node (cyc.js) y navegador con F8, sobre la partitura sin tocar: 'C1.ANCHOR.CYCLE · Anchor cycle in moment 2.R4: its time can't be computed (falls back to 0).' y lo mismo para 5.R4. Pero 2.R4 empieza en 373.09 s (6:13) y protoDiff = 0. El ciclo real está en tEnd (2.R4 > SENSOR_OUT3 > BIO > 2.R5), y engine.js:50 devuelve tStart, no 0. Las columnas 'Layer C1/C2/C3', 'Rule C3.DRIFT' y 'Owner in Unreal: HallDirector · Test_Hall' (ui.js:288-289) son de desarrollador, y ninguna fila tiene un botón para resolver. El total aparece como 16:58 en Problems (integrity.js:7 redondea) y como 16:57 en la barra (ui.js:13 trunca). Falta el 'Check piece' del plan (línea 93).

**Escenario:** Primer día: el socio abre la app y ve '● 2 blocking' en rojo que él no causó. Abre F8, lee que algo 'cae a 0' cuando no es así, no puede arreglarlo y aprende que el rojo es ruido.

**Arreglo:** Corregir el mensaje y la severidad (warn: 'el final de 2.R4 depende de 2.R5', sin 'falls back to 0') o romper el ciclo en extract_v1. Agregar acciones por fila: 'Match Unreal (20 s)' para C3.DRIFT y 'Add help line' para C2.WAIT.NOHELP. Plegar Layer y Rule en 'Details'. Usar un solo formateador de tiempo.

**Verificador:** c8.js: con la partitura sin tocar hay 2 C1.ANCHOR.CYCLE con severidad block (2.R4 y 5.R4). Sus tiempos (373.09-415.26 y 731.01-806.01) coinciden con score.golden, y engine.js:50 devuelve tStart, no 0, así que el mensaje 'falls back to 0' (integrity.js:22) es falso. En la tabla, las filas solo tienen data-goto y, si están aceptadas, 'reopen'; ninguna ofrece una acción para resolver. Las columnas Layer, Rule y Owner in Unreal son de desarrollador (ui.js:288-289). El total sale 16:58 en Problems (integrity.js:7 redondea) y 16:57 en la barra (ui.js:13 trunca).

#### C9 · No hay forma de cambiar el ancla de un elemento
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** fricción
- **Esfuerzo:** M

**Evidencia:** ui.js:318-323: anchorChip solo tiene data-goto, que selecciona el ancla. Act (app.js:123-243) no tiene ningún verbo para re-anclar ni desanclar. Offset siempre es relativo al ancla (ui.js:372, 'Seconds after its anchor'). El menú del clip (ui.js:626) solo ofrece Go to its start, Select its anchor, Note y Delete. 'Add after / in parallel / Reaction' del plan §2.3 (línea 201) no está construido. En la partitura hay 360 elementos anclados a otro elemento (stats.js).

**Escenario:** El socio quiere que VO_05 arranque 2 s después de que se abren las puertas, no 'after VO_04'. No hay forma: Ctrl+arrastrar conserva el ancla, y borrar y crear una VO nueva pierde la key que Unreal llama por ruta.

**Arreglo:** Hacer editable el chip de ancla con 'Anchor to…' (eligiendo en el timeline), 'Detach: anchor to moment start (keeps time)' y el borde start/end. Implementarlo como un commit de tipo 'reanchor' que conserve el tiempo absoluto y pase por integridad.

**Verificador:** Act (app.js:123-243) no tiene ningún verbo para re-anclar ni desanclar. anchorChip solo navega (ui.js:318-323) y el menú del clip (ui.js:626) no ofrece re-anclar. Conté 360 elementos anclados a otro elemento. Esto también agrava C1: un momento que queda con el ancla colgada no puede re-anclarse desde la interfaz.

#### C10 · Faltan los verbos de un NLE y los modificadores significan otra cosa
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** fricción
- **Esfuerzo:** M

**Evidencia:** app.js:393-418: onKey no maneja J/K/L, I/O, ↑/↓, =/-, \ ni Ctrl+C/V/D, aunque el plan §2.7 promete ↑/↓ (línea 272) y J/K/L e I/O (línea 281). Solo hay selección única: ui.js:549 hace que Shift+clic reemplace la selección, y no hay marquesina ni selección por rango (plan, línea 222). ui.js:530: Alt desactiva el imán (en Premiere/Resolve, Alt+arrastrar duplica). Ctrl+arrastrar significa 'alone' (en Premiere es insert). app.js:407: 'A' alterna las curvas de anclas (en Premiere es Track Select Forward). app.js:410: Supr y Retroceso borran con ripple (en Premiere hacen lift).

**Escenario:** El socio pulsa L para reproducir y K para parar, y no pasa nada. Quiere correr tres FX juntos y tiene que hacerlo uno por uno. Hace Alt+arrastrar para duplicar un FX y mueve el original sin imán.

**Arreglo:** Implementar J/K/L (shuttle sobre seek/play), I/O como rango, ↑/↓ para momento anterior/siguiente, =/- para zoom y \ para Fit. Agregar multiselección (Ctrl+clic y marquesina) con Act.move y Act.remove sobre varios ids, y duplicar con Ctrl+D. Pasar el imán a S como alternancia, como en Premiere. Agregar Help ▸ Keyboard con las equivalencias de NLE.

**Verificador:** onKey (app.js:393-418) no maneja J/K/L, I/O, ↑/↓, Ctrl+C, Ctrl+V ni Ctrl+D. El plan §2.7 promete ↑/↓ (línea 272) y J/K/L e I/O (línea 281). Shift+clic reemplaza la selección (ui.js:549) y no hay selección múltiple. Alt apaga el imán (ui.js:530), 'A' alterna las anclas (app.js:407) y Supr/Retroceso borran, con ripple implícito (app.js:410).

#### C11 · A 1:1 casi nada se lee: el 94 % de los títulos de clip aparece cortado
- **Severidad:** low (el auditor puso medium)
- **Estado:** en parte
- **Rompe:** fricción
- **Esfuerzo:** M

**Evidencia:** Navegador a 1600×900 con el zoom por defecto de 8 px/s: 298 de 318 títulos de clip truncados, 225 clips de menos de 40 px, 170 de 274 etiquetas de instantáneos truncadas y 53 de 73 chips de momento truncados. Se ven 136 s de 1018, y los carriles miden 965 px de alto para 388 px visibles (Sound, Music y Haptics quedan fuera). Con Fit (1,03 px/s): 277 de 318 clips por debajo de 10 px y 73 de 73 momentos truncados. ui.js:211 pone primero la key técnica y después el label (HALL_LOAD antes de 'Recién en el negro aparece el Hall'), y la única ayuda es el tooltip nativo (title). Los idiomas se mezclan: 'Acto 2 · Hall' junto a 'Etapa 2 · Recognizing', y momentos y labels en español dentro de una interfaz en inglés.

**Escenario:** Para encontrar 'el momento en que se abren las puertas', el socio tiene que pasar el mouse clip por clip y esperar cada tooltip, o leer el panel Scenes y saltar.

**Arreglo:** Mostrar una tarjeta inmediata al pasar el mouse (label, inicio, duración, ancla). En los elementos que no son VO y tienen key técnica, poner el label primero. Hacer que doble clic en un chip de momento haga zoom a ese momento. Agregar presets de zoom (moment, act, piece), altura de carril compacta o expandida, y Ctrl+F para buscar, seleccionar y revelar en el timeline.

**Verificador:** Reproduje las cifras exactas en mi pestaña a 1600×900 y 8 px/s: 298 de 318 títulos truncados, 225 clips de menos de 40 px, 170 de 274 instantáneos y 53 de 73 chips; se ven 136 s y la altura es 388 de 965 px. Pero en un NLE es normal que los nombres se trunquen con el zoom por defecto, y ya existen el buscador de Scenes en la Library, el zoom y Fit. Lo que sí es real es menor: la key técnica va antes del label (ui.js:211), la única ayuda es el title nativo y los idiomas se mezclan. Lo bajo a 'low'.

#### C12 · Recortar una espera con otro usuario simulado deja el clip en otro lugar
- **Severidad:** low (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** confusión
- **Esfuerzo:** S

**Evidencia:** Node, persona.js (G_SENSOR con expected 8 y fw 15), arrastrando el borde a 10.0 s: con Typical queda en 10.00, con Slow en 12.50, con Idle en 15.00 (no cambia nada visible) y con Fast en 3.00. app.js:154: el recorte escribe gate.expected, un valor de simulación que según ui.js:380 'never reaches Unreal'. Mientras tanto, el fantasma muestra 'G_SENSOR · 10.0 s' (ui.js:580) y el tooltip dice 'Drag to change the duration' (ui.js:211).

**Escenario:** Con Slow activo, el socio acorta una espera a 10 s y al soltar queda en 12,5 s; vuelve a arrastrar. Con Idle, el gesto parece no hacer nada, pero el tiempo esperado sí cambió.

**Arreglo:** Deshabilitar el recorte de esperas fuera de Typical con un toast ('cambia a Typical para editar el tiempo esperado'), o aplicar la fórmula inversa de cada usuario simulado. Mostrar en el fantasma 'expected 8→10 s (simulation)'.

**Verificador:** dup.js: al recortar G_SENSOR (expected 8, fw 15) a 10 s, el clip queda en 3.00 s con Fast, 10.00 con Typical, 12.50 con Slow y 15.00 con Idle, y en todos los casos expected pasa a 10 sin tarjeta. Es exactamente lo descrito (app.js:154). Lo bajo a 'low' porque expected es un valor de simulación que no llega a Unreal; el efecto es solo de desconcierto.

#### C13 · Los marcadores y las notas no se pueden renombrar, mover ni borrar
- **Severidad:** low (el auditor puso low)
- **Estado:** confirmado
- **Rompe:** fricción
- **Esfuerzo:** S

**Evidencia:** app.js:239-241: bookmark() crea 'Bookmark n' en score.markers, y ningún otro código escribe markers (ui.js:158, 526 y 672 solo los leen). app.js:235-237: para las notas solo existe addNote, y notesHTML (ui.js:422-426) no ofrece editar ni borrar.

**Escenario:** El socio pulsa M por costumbre de Premiere, donde el marcador se edita con doble clic. 'Bookmark 7' queda para siempre en score.json salvo que haga Ctrl+Z en el momento, y una nota obsoleta no se puede marcar como resuelta.

**Arreglo:** Doble clic en un marcador para renombrarlo, arrastrar para moverlo y clic derecho para borrarlo. Notas con editar, resolver y borrar. Todo a través de commit.

**Verificador:** Por grep, solo bookmark() (app.js:240) y addNote() (app.js:237) escriben en markers y notes. ui.js:158 y 672 solo leen los marcadores, y notesHTML (ui.js:422-426) no tiene editar, resolver ni borrar.

#### C14 · Trampas de foco y un 'unsaved' engañoso
- **Severidad:** low (el auditor puso low)
- **Estado:** confirmado
- **Rompe:** confusión
- **Esfuerzo:** S

**Evidencia:** Navegador: con el <select> Lane del inspector enfocado, la tecla → movió VO_02 de Voice 1 a Voice 2 (lane ln_vo_2, undo 1) en lugar de mover el cabezal (app.js:398 ignora los atajos con un select enfocado; ui.js:747 change → setLane). Tras deshacer todo, con la partitura idéntica al disco, la barra seguía en 'unsaved · Ctrl+S' y beforeunload pedía confirmación (app.js:119: undo llama a markDirty).

**Escenario:** El socio cambia el carril desde el inspector y luego pulsa → para avanzar el cabezal: el clip salta de carril sin tarjeta. Al cerrar la pestaña después de deshacerlo todo, el navegador le advierte de cambios sin guardar que no existen.

**Arreglo:** Quitar el foco del select después del change. Calcular dirty comparando la partitura actual con la última guardada (hash) en lugar de marcarla sucia en cada undo o redo.

**Verificador:** Lo verifiqué en mi propia pestaña sin modificar la partitura: reemplacé temporalmente Act.setLane por un espía, enfoqué el select Lane de VO_02 y pulsé ArrowRight. Se llamó a setLane(el_1f574ux1qq, 'ln_vo_2') y el cabezal no se movió. La causa es app.js:398, que devuelve con un select enfocado, y Chrome en Windows cambia la opción con las flechas. Restauré setLane y verifiqué undo 0, sin borrador ni cambios en la preferencia. Que undo y redo llamen a markDirty sin comparar con lo guardado se ve en app.js:119-120.

#### +C1 · 'Delete them too' borra toda la descendencia transitiva (hasta 572 de 592 elementos) mientras la tarjeta dice '2 elements are anchored to it'
- **Severidad:** high
- **Rompe:** partitura

**Evidencia:** app.js:101-103: con rep === 'family' se ejecuta `for (const k of ScoreEngine.family(before, id, kids)) delete n.elements[k]`. family() es transitiva (engine.js:75-79) e incluye momentos, que no se borran porque no son elementos y quedan con el ancla colgada en 0:00. La tarjeta (integrity.js:83-85) solo cuenta y nombra los dependientes directos y ofrece la opción 'Delete them too' (integrity.js:85). Barrido en node (zz_verifC_usab_7q3/c1b.js y c1c.js) sobre los 179 elementos con dependientes: la opción borra en mediana 5 elementos más de los que nombra la tarjeta, y en 37 casos 50 o más. WALK1, con la tarjeta '2 elements are anchored to it', borra 572 de 592 elementos, deja 20 momentos colgados y el total pasa de 16:58 a 1:10. PASO borra 504. El único aviso es el toast 'Done' (app.js:93).

**Escenario:** 1) El socio selecciona WALK1 y pulsa Supr. 2) La tarjeta dice '2 elements are anchored to it' y él elige 'Delete them too' pensando en esos dos. 3) Al confirmar desaparecen 572 elementos de todos los actos y 20 momentos saltan a 0:00. 4) Si no hace Ctrl+Z antes de guardar, score.json queda casi vacío; la copia anterior solo está en obra/score/history y hay que importarla a mano con File ▸ Import.

**Arreglo:** Calcular en opItems la familia completa e indicarla en la etiqueta ('Delete them and everything that hangs from them: 503 elements in 17 moments'). Por encima de un umbral (por ejemplo 5), exigir un motivo o una confirmación escrita. Re-anclar a su tiempo actual los momentos de la familia en lugar de dejarlos colgados, o limitar la opción a los dependientes directos.

#### +C2 · El candado de grupo no protege: Supr, Alt+←/→, el inspector y Edit ▸ Delete se lo saltan, y se pierde al recargar
- **Severidad:** medium
- **Rompe:** confusión

**Evidencia:** El toast promete 'Group locked: nothing in it can be moved or deleted' (ui.js:543), pero el candado solo se respeta en tres lugares: al apretar el mouse sobre el clip (ui.js:551), en el tirador de recorte (ui.js:210) y en el Delete del menú contextual (ui.js:626). Ningún verbo de Act (app.js:124-182) lo consulta. Sin control: Supr/Retroceso → Act.remove (app.js:410), Alt+←/→ → Act.move (app.js:413), Edit ▸ Delete selection (ui.js:51), el botón Delete del inspector (ui.js:736) y los campos Offset, Duration, Lane y Text (ui.js:741-750). Además, App.locked solo vive en memoria (app.js:16): savePref (app.js:60) no lo guarda, así que se pierde al recargar y no se comparte con la otra pestaña.

**Escenario:** 1) El socio bloquea el grupo Objects para no tocar el Hall. 2) Hace clic en un objeto para leerlo; se selecciona y aparece el toast 'Objects is locked'. 3) Pulsa Alt+→ o Supr: el objeto se mueve o se borra sin tarjeta, porque obj no tiene contrato. 4) Al día siguiente recarga y el candado ya no está.

**Arreglo:** Comprobar App.locked[e.group] en Act.move, trim, remove, setOffset, setLane y setText (y en onKey) y responder con el toast de bloqueo. Deshabilitar los campos del inspector y el botón Delete de un elemento bloqueado. Persistir los candados en la preferencia o en la partitura.

#### +C3 · Play se congela en el final del prototipo (16:58) cuando la partitura dura más: con Slow o Idle, o tras alargar la obra
- **Severidad:** medium
- **Rompe:** confusión

**Evidencia:** Durante Play, el cabezal lo maneja el reloj del prototipo: App.ph = App.SC.S.t (app.js:300), y el editor solo se detiene en App.sched.total (app.js:302). El prototipo limita su tiempo a su propio TOTAL (timeline.js:526 `t = clamp(t, 0, TOTAL)`, :987 `S.t = Math.min(TOTAL, …)`) y se detiene ahí (:998). Lo verifiqué en mi pestaña: App.SC.seek(1050) deja S.t = 1017.997, que es App.SC.TOTAL. En node, los totales por usuario simulado son: Fast 988.8, Typical 1018.0, Slow 1085.3 e Idle 1176.3 s. Basta un recorte de +5 s (C2) para que el total sea 1023.

**Escenario:** 1) El socio elige Slow para revisar el cierre y busca 17:30. 2) Pulsa Espacio. 3) El cabezal salta a 16:58 y queda quieto mientras el botón sigue en pausa, porque App.playing sigue en true. 4) Los últimos 87 s (Slow) o 158 s (Idle) no se pueden reproducir, y tampoco los segundos que agregó al alargar un clip. Parece que la app se colgó.

**Arreglo:** Cuando App.ph supera App.SC.TOTAL, que el editor avance con su propio reloj (la rama `App.ph += dt` de app.js:300) y muestre en el visor '3D: past the prototype's end'. Si no, detener Play con un toast que lo explique.

### D · Arquitectura y camino a Unreal

La base sirve para F1: el motor es puro y está verificado (665/665), todas las ediciones pasan por commit() y el servidor es mínimo, con historial. Pero la partitura todavía es una foto del prototipo y no un documento compilable. No tiene marcas de Unreal ni acción, target o asset por elemento. Las duraciones de voz son estimaciones por palabras. Hay dos ciclos de anclas que hacen que 387 tiempos dependan del orden de evaluación. Las ramas SHARE/DON'T SHARE se perdieron, y las esperas que en Unreal no bloquean empujan toda la línea de tiempo. Hoy lo que más amenaza con romper la obra de forma continua es la persistencia: re-extraer pisa todas las ediciones con IDs que no son estables, guardar es "gana el último" y el rev no sirve como base de reconciliación. Antes de que la partitura mande en Unreal hay que decidir qué fuente gana (guion.js, score.json o Unreal), congelar los ids, importar sin pisar y agregar una capa de enlace (schema 3), con un compilador que rechace lo que no resuelve en lugar de adivinar.

#### D1 · La partitura no tiene capa de enlace con Unreal: no se puede compilar a {Mark, Offset, Action, Target, Asset}
- **Severidad:** medium (el auditor puso critical)
- **Estado:** en parte
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** L

**Evidencia:** Script C:\Users\beltr\AppData\Local\Temp\claude\C--Users-beltr-Desktop-Alma-Digital-Studio-Projects-VR-Unreal\c5fe4ce1-f688-4688-b3d0-60d97942b228\scratchpad\audit\compile.js sobre obra/score/score.json:
- "any field naming an Unreal mark/asset/actor/target/action? []".
- Los 73 momentos usan claves del prototipo ('1.R4', 'V1', '2.7a'), no las marcas S<K>.OPEN/ALMA/INTRO/BEGIN/OUTRO/CHARGE/BYE (anexo 11:302-313).
- 20 momentos están anclados al fin de un elemento (1.6←WALK1.end, 2.7b←PASO.end…).
- 245 elementos tienen legacy.behavior=true: su comportamiento solo existe en closures del prototipo.
- Hay 164 sound ids distintos (78 FX). Según el anexo 11:86, Unreal tiene unos 10 FX_* y FX_BELLRING no existe; idmap.json tampoco existe.
- PLAN:308-321 prometía `target`, `action` y ULID; extract_v1.mjs:83-92 no los genera.
- El contrato cubre 166 de 592 elementos.

**Escenario:** 1) En F4, compile.mjs recibe FX_BELLRING (momento '1.8', at G_BELL.end).
2) Ningún dato asocia '1.8' a una marca que la Obra emita, y no hay asset (Unreal suena con Core/Audio/Sounds/Bell), ni target, ni acción.
3) Si el compilador adivina (por ejemplo, un offset desde S0.OPEN con la persona típica), el cue suena en el APK a destiempo del timbre real. Si lo descarta, el socio cree que su edición llegó.
4) Como 20 momentos se encadenan al fin de un elemento, el error se propaga a todo lo que viene después.

**Arreglo:** Antes de F4, pasar a schema 3:
1) `beats[id].mark` con el vocabulario v0 del anexo 11 (null = preview only).
2) Por elemento: `action` (catálogo MVP de 10), `target` (rol o tag) y `asset` resuelto con un `obra/unreal/idmap.json` versionado.
3) `reach` calculado: un elemento llega a Unreal solo si resuelven marca, acción y asset.
4) compile.mjs rechaza lo que no resuelve, sin adivinar, y lo lista en el manifiesto como preview only.
Empezar solo por la familia elegida (VO de Entering).

**Verificador:** Las cifras se sostienen: lo comprobé con node sobre score.json. Hay 166 de 592 elementos con entrada de contrato, 245 con legacy.behavior, 20 momentos anclados al fin de un elemento, 164 sound ids (78 FX) y 45 uids con '#'. También es cierto que el schema 2 construido no trae los target/action/ULID/marcas que PLAN §3.2 (líneas 308-321) prometía para schema 2, y PLAN §8 da F0 por hecho sin decirlo. Pero no es crítico. Es la fase F3/F4, que no está construida, y la app lo declara: la barra de estado dice '0 of N reach Unreal', la píldora 'Unreal: not connected' (ui.js:38,441) y C3.SCOPE aparece en Problems (integrity.js:45). Hoy no corrompe ni pierde la partitura. El escenario del compilador que adivina es hipotético, porque compile.mjs no existe. Queda como una deuda de diseño que hay que saldar antes de F4: medium.

#### D2 · Re-extraer pisa todas las ediciones, y los IDs 'estables' cambian o pasan a nombrar otro clip
- **Severidad:** critical (el auditor puso critical)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** M

**Evidencia:** - extract_v1.mjs:114 escribe `schema: 2, rev: 1` y :121 hace writeFileSync sin leer el score existente.
- ID = hash(uid) (extract_v1.mjs:65-66), con uid = '<número de momento>/<key>[#n]' (timeline.js:33-34). 45 uids llevan '#n'.
- scratchpad/audit/ids.js corrió extract_v1 sobre copias modificadas de guion.js:
  - renumerar '1.7'→'1.7a' pierde 3 ids (1.7, FX_BELLAPPEAR, BELL_IN);
  - renombrar VO_11h pierde su id;
  - agregar un FX_GHOSTAPPEAR al inicio de 1.8 hace que el_yjvsq81bml pase a nombrar el clip nuevo (at 1.8 start+2, nota 'extra cue') en lugar del de GHOST_BELL.
- La regla de memoria 'prototipo-web-sigue-a-unreal' obliga a Narrativa a seguir editando guion.js y timeline.js (timeline.js está modificado en el árbol hoy).
- El README dice: 'Ojo: pisa las ediciones'.

**Escenario:** 1) El socio ajusta 30 tiempos y guarda (rev 5).
2) Narrativa integra en guion.js un cambio de Unreal (un momento nuevo o un clip repetido).
3) Para verlo en el editor, alguien corre extract_v1.mjs. score.json vuelve a rev 1 con los tiempos del prototipo: se pierden ediciones, notas, marcadores y aceptaciones, que solo quedan en history/ hasta que roten 40 guardados.
4) Si después se escribe un merge por id, el id reasignado aplica la edición de GHOST_BELL al FX nuevo sin avisar.

**Arreglo:** - Tratar guion.js como fuente de importación, no de verdad: extract escribe `score.extracted.json` más un informe de diferencias, nunca score.json.
- Guardar el mapa uid→id dentro del score y reutilizarlo; los ids nuevos se generan con ULID.
- Si un uid con '#n' cambia de destino (otro at, otra nota o etiqueta), tratarlo como clip nuevo y marcar el viejo 'removed in guion'.
- Ejecutar el Corte del MVP (PLAN:391): los tiempos solo se cambian en la partitura.

**Verificador:** Es peor de lo que describe el auditor. extract_v1.mjs:121 escribe con fs.writeFileSync sin pasar por el servidor, así que no copia nada a history/. Ahí solo están las revisiones anteriores, que el PUT mueve (serve_editor.py:86-88). La última revisión guardada vive solo en score.json, y obra/ está sin seguimiento en git ('?? obra/'). Una re-extracción la pierde sin recuperación posible. Para medir el riesgo extraje en el scratch, sin tocar el repo. Con guion.js tal como está, la extracción da 665/665 iguales. Insertando fx('FX_GHOSTAPPEAR', 2, 'extra cue') antes de ghostSpan en 1.8, el_yjvsq81bml pasa de at.off 0 con nota 'GHOST_BELL' a at.off 2 con nota 'extra cue', y el clip original queda con un id nuevo ('1.8/FX_GHOSTAPPEAR#2'). El uid es '<momento>/<key>[#n]' (timeline.js:33-34). El disparador es plausible: la regla de que el prototipo sigue a Unreal y la falta de cualquier otra vía de importación.

#### D3 · Guardar es 'gana el último' y `rev` no sirve como base para reconciliar con Unreal
- **Severidad:** high (el auditor puso high)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** M

**Evidencia:** - serve_editor.py:77-96: el PUT no compara rev ni hash.
- app.js:339: `next.rev = baseRev + 1`.
- app.js:33: el borrador solo se restaura si `d.baseRev === App.baseRev`; en otro caso se descarta sin aviso.
- app.js:380: BroadcastChannel solo actualiza las pestañas ?view=3d.
- serve_editor.py:87-88: el sello del historial va por segundo; dos guardados en el mismo segundo pisan la copia.
- obra/ está sin seguimiento en git ('?? obra/').
- scratchpad/audit/drafts.js reproduce las reglas de app.js:
  - A) re-extracción rev 1 + borrador viejo rev 1: el borrador se restaura encima y Ctrl+S escribe rev 2 sin el clip nuevo de guion.js;
  - B) dos pestañas en rev 2 guardan las dos 'rev 3' y se pierde la primera;
  - C) borrador sobre rev 2 con el disco en rev 3: se descarta en silencio.

**Escenario:** Caso 1: Beltrán deja el editor abierto (rev 2) y el socio usa otra pestaña de timeline. Los dos guardan, los dos ven 'Saved · rev 3' y solo queda la última.
Caso 2: una sesión de Claude escribe en score.json (hoy una re-extracción, en F3 la cosecha). Beltrán aprieta Ctrl+S y su copia en memoria borra lo escrito.
En F4, si `ImportedRev` es este rev, dos versiones distintas comparten número y la reconciliación compara contra la base equivocada.

**Arreglo:** - PUT con If-Match (baseRev + hash del contenido). El servidor responde 409 si el disco cambió y la app ofrece recargar, fusionar o exportar.
- El servidor asigna un rev monótono (máximo del historial + 1) y un revId único.
- Sello de historial con milisegundos.
- Borrador ligado al revId, con aviso y 'Export draft' cuando se descarta.
- Un candado de escritor (archivo lock con pestaña y autor) hasta F2.
- Commitear obra/score en cada hito.

**Verificador:** El código lo confirma:
- el PUT no valida rev ni hash (serve_editor.py:77-96);
- el rev se calcula como baseRev+1 en el cliente (app.js:339);
- el borrador solo se compara por número de rev (app.js:33);
- BroadcastChannel solo aplica d.score en ?view=3d (app.js:380);
- el sello va por segundo y os.replace pisa en Windows (serve_editor.py:87-88).
Hay un camino realista hoy: abrir-editor.bat usa --open, que abre una pestaña nueva aunque el servidor ya esté corriendo (serve_editor.py:137-145). Así se tienen dos pestañas de timeline sin darse cuenta, y además comparten la única clave LS_DRAFT (app.js:9,336). Atenuante: la versión pisada queda en history/, porque el PUT mueve la anterior, y se puede rescatar a mano hasta que roten 40 copias o choquen en el mismo segundo. No hay UI para restaurarla y el usuario ve 'Saved · rev N' en las dos pestañas.

#### D4 · El 'golden' vive dentro de la partitura viva: el único test se rompe con la primera edición y el aviso de diferencias no ve los cambios de guion.js
- **Severidad:** medium (el auditor puso high)
- **Estado:** confirmado
- **Rompe:** fricción
- **Esfuerzo:** S

**Evidencia:** - extract_v1.mjs:118 guarda `golden` dentro de score.json.
- golden_test.mjs:9-20 lee el score vivo.
- app.js:55-58 calcula protoDiff contra score.golden.
- scratchpad/audit/golden_after_edit.js: una edición normal (+2 s al momento 1.3) deja golden en 12/665, así que golden_test.mjs saldría con código 1 para siempre (el contador ámbar marcaría 653).
- Los 17 edits de timeline/main v78 (PLAN:112) no se importan: extract corre con EDITS = {} (timeline.js:84) y AUDIO: {} (extract_v1.mjs:50).

**Escenario:** 1) Una sesión de Claude toca engine.js para F2 y corre golden_test, como indica el README.
2) Ve MISMATCH y no puede saber si rompió el motor o si Beltrán editó la partitura. La salida obvia es re-extraer, que pisa las ediciones (D2).
3) En paralelo, Narrativa cambia tiempos en guion.js. El iframe 3D los muestra, pero el contador ámbar sigue comparando contra el golden de F0: el socio ve cifras que no corresponden a lo que mira.

**Arreglo:** - Mover el golden a un fixture congelado (tools/score/fixtures/f0-score.json + f0-golden.json) que use golden_test, y quitar `golden` del score vivo.
- Calcular el contador del 3D contra una extracción en vivo de guion.js, o rotularlo 'vs F0 snapshot'.
- Dejar por escrito qué fuente gana para cada dato: tiempos en la partitura, mallas e interacción en guion.js, perillas en Unreal.
- Decidir qué se hace con los 17 edits de v78.

**Verificador:** golden_test.mjs:10-20 compara contra score.golden del archivo vivo: la primera edición de tiempo lo hace salir con 1 para siempre. Re-extraje en el scratch y hoy da 665/665 contra el golden, así que el contador ámbar (app.js:55-58) todavía es correcto. Deja de serlo apenas Narrativa cambie tiempos en guion.js. Los 17 edits de v78 viven en la base del artifact: el tramo SCHED copiado incluye `let EDITS = {}` (timeline.js:84). PLAN:326 pedía aplicarlos y PLAN §8 no menciona que falten. Es fricción de verificación y de flujo, no pérdida de datos: medium.

#### D5 · Las duraciones de VO son una estimación por palabras, no el audio real
- **Severidad:** high (el auditor puso high)
- **Estado:** confirmado
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** S

**Evidencia:** - extract_v1.mjs:50 pasa `AUDIO: {}`, así que expectedDur cae a voDur(text) (timeline.js:101-103).
- app.js:8 y :169: setText vuelve a calcular la duración con voDur.
- scratchpad/audit/vodur.js contra VR_Test/Saved/ClaudeScripts/vo_final/duraciones_mezcla.txt:
  - 70 VO en modo 'audio', 57 con duración de mezcla;
  - diferencia media 1,79 s; la peor, VO_02, −12,6 s;
  - VO_10: 6,92 en la partitura contra 8,5 en la mezcla; VO_11: 6,83 contra 5,84;
  - con las duraciones reales, 544 elementos se corren más de 1 s y el total típico pasa de 1018,0 a 992,1 s.
- No se cumplen PLAN:302 ('La duración de la VO es de Unreal (GetDuration)') ni PLAN:327 (golden 'con la duración real de los audios').

**Escenario:** - El socio hace que VO_11 termine justo antes del pacer. En el editor dura 6,83 s; en Unreal, 5,84 s: queda alrededor de 1 s de aire muerto.
- Con VO_10 (6,92 contra 8,5 s), lo anclado a su fin se pisa con la voz.
- Las reglas C2 (ayuda tardía, total contra 15:00) también se calculan sobre la estimación.
- Si F4 aplana offsets a través del fin de una VO, el error queda horneado en el APK.

**Arreglo:** - Cargar ya duraciones_mezcla.txt (y después la cosecha) en `audio.dur`, con `audio.src: 'mix' | 'estimate'`.
- El motor usa audio.dur cuando existe.
- Problems avisa 'duración estimada' en cada VO que la tenga.
- compile.mjs no aplana a través del fin de una VO estimada: usa la marca VO.<clip>.start más la duración real del asset.

**Verificador:** Lo reproduje (v/vod.js) contra duraciones_mezcla.txt:
- 70 VO en modo 'audio', 57 con duración de mezcla, diferencia media 1,79 s;
- VO_02: 19,92 contra 7,33; VO_10: 6,92 contra 8,5; VO_11: 6,83 contra 5,84;
- con la mezcla, el total típico baja de 1018,0 a unos 984 s.
Mis cifras difieren un poco de las del auditor por el criterio de cruce, pero el orden de magnitud se sostiene. Agravante que el auditor no menciona: el inspector rotula esa duración 'its audio' con candado y 'final mix' (ui.js:368,389). Le dice al socio que es el audio real cuando es la estimación por palabras. Ojo: duraciones_mezcla.txt está en VR_Test/Saved/ (ignorado por git), así que solo existe en la máquina de Beltrán.

#### D6 · Dos ciclos de anclas ya presentes hacen que 387 tiempos dependan del orden de evaluación
- **Severidad:** high (el auditor puso high)
- **Estado:** confirmado
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** S

**Evidencia:** - golden_test.mjs imprime `cycles ["bt_1biqo7b1ib","bt_1wpzo78f07"]` (2.R4 y 5.R4) y sale con 0: la línea 20 ignora los ciclos.
- extract_v1 imprime 'Ciclo de anclas en 2.R4 / 5.R4' y escribe igual.
- Causa: SENSOR_OUT3 está anclado a BIO.end −1,5; BIO dura 'until' el inicio de un momento posterior, y SENSOR_OUT3 cuenta para el fin de 2.R4.
- engine.js:39-40 y :50 cortan el ciclo devolviendo 0 o tStart según qué nodo se evalúe primero.
- scratchpad/audit/cycle.js usa una copia del motor que evalúa los elementos antes que los momentos: 387 ids cambian de tiempo, el total pasa de 1018,0 a 966,6 s y 2.R4 termina en 379,59 en lugar de 415,26.

**Escenario:** 1) En F4, compile.mjs recorre por etapa o por marca, en otro orden que el motor.
2) Los cues de Recognizing y Surrounding salen corridos de 36 a 51 s respecto de lo que muestra el editor.
3) El golden 665/665 no lo detecta, porque los dos motores comparten el mismo orden.

**Arreglo:** - Romper el ciclo en la partitura: anclar SENSOR_OUT3 a la marca de salida del momento, o excluir del fin de momento lo que depende de un elemento crossSpan.
- Convertir el ciclo en invariante: extract y golden_test terminan con código distinto de 0, y el compilador se niega a emitir si hay ciclos.

**Verificador:** Lo reproduje con una copia del motor que evalúa los elementos antes que los momentos: cambian 387 ids (en mi variante el total pasa a 1041,6; el valor concreto depende del orden). El daño ya se ve hoy en el editor:
- 2.R5 empieza en 373,09, que es el inicio de 2.R4 y no su fin (415,26): los dos momentos se superponen enteros.
- El ripple está roto en esa zona. Llevar VO_16 a 60 s hace terminar 2.R4 en 433,1, pero 2.R5x, 2.R6 y el total no se mueven (v/cyc_v3.js).
- +10 s en el expected de G_HEART mueven 2 elementos y 0 s el total, y en G_DRAW 1 y 0. En G_BREATH son 470.
En Problems figura desde la carga como 2 BLOCK 'C1.ANCHOR.CYCLE', sin explicación. golden_test sale con 0 aunque haya ciclos (línea 20).

#### D7 · Las ramas SHARE / DON'T SHARE se perdieron en la extracción
- **Severidad:** medium (el auditor puso high)
- **Estado:** confirmado
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** S

**Evidencia:** - extract_v1.mjs:90 guarda `c.when.name`. Por eso VO_35b y VO_35c (guion.js:633-634, una por rama) quedan las dos con `when: 'when'`.
- VO_36c y VO_36d quedan con 'yes' y 'no', nombres de closures (guion.js:588).
- VO_37 está anclada a VO_35b.end (guion.js:635), que solo existe en SHARE.
- engine.js ignora `when` y programa las dos ramas a la vez, igual que el prototipo.

**Escenario:** 1) Al compilar la familia del final, nada en el dato dice que VO_35b es SHARE y VO_35c es DON'T SHARE.
2) El APK reproduce las dos voces seguidas, o ninguna.
3) En DON'T SHARE, VO_37 espera el fin de una voz que nunca suena (una marca que no se emite): silencio o un final sin cierre.

**Arreglo:** - Campo explícito `branch: { on: 'share', value: true | false }`, cargado a mano en los 15 elementos que tienen `when`, y mapeado a las marcas SHARE.<estado>.
- Regla C1: un elemento solo puede anclarse a otro de su misma rama, o tener un ancla por rama.
- El motor muestra una rama a la vez (PLAN:191).

**Verificador:** En score.json, VO_35b, VO_35c, FX_DOOROPEN (9.6) y FX_SOULJOIN quedan con when='when' (el nombre de la propiedad de la función flecha), y VO_36c/VO_36d con 'yes'/'no'. El motor ignora `when`: VO_35b y VO_35c arrancan las dos en 953,0 s, y 9.5b dura el máximo de ambas ramas. VO_37 está anclada a VO_35b.end. La UI nunca muestra `when` (grep en ui.js/app.js sin uso). Hoy la rama solo se recupera vía legacy.uid → guion.js:633-634, y eso deja de valer con el 'Corte del MVP'. Es una zona acotada (unos 16 elementos del final) y F5 ya prevé ramas: medium.

#### D8 · Las esperas elásticas no se comportan como en Unreal, y la cadena de anclas de Entering es otra
- **Severidad:** medium (el auditor puso high)
- **Estado:** en parte
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** M

**Evidencia:** - scratchpad/audit/gates.js: hay 10 esperas. Solo 4 bloquean en Unreal (G_BELL, G_SENSOR, G_CHOOSE, G_SHARE, según contract.json); 4 son not-blocking (G_BREATH, G_HEART, G_GRAB, G_DRAW) y 2 no tienen contrato (G_SAVE4/5).
- Aun así, con el usuario Idle, G_BREATH empuja 427 elementos (+18,2 s) y G_GRAB 203 (+9,5 s).
- 560 de 592 inicios dependen de la persona simulada (compile.js).
- VO_11h está en `G_BREATH.start + 12` (momento 1.R4). En Unreal es `VO_11b + HelpAfter 4 s`, y VO_11b está en un momento posterior (1.R5a) (anexo 14:30, PLAN:42-43).
- 18 elementos se anclan al fin de una espera, pero no existen marcas GATE.* (anexo 11:299).

**Escenario:** - El socio prueba la persona Slow y ajusta Entering para que no quede aire muerto. En el APK, Entering corre por reloj y esos 18 s no existen: sus ajustes desacomodan la etapa.
- En la primera familia de F4 (cadena de VO de Entering, PLAN:426), el offset '12 s desde G_BREATH' no corresponde a ninguna perilla, porque HelpAfter cuenta desde VO_11b. El compilador no puede traducirlo.

**Arreglo:** - Agregar a cada espera `blocking` y `cond` (vocabulario v0 del anexo 11).
- Que el motor no empuje la línea de tiempo con esperas que no bloquean: solo deciden si suena la ayuda.
- Antes de compilar Entering, re-anclar la cadena como en Unreal (VO_11h → VO_11b.end + HelpAfter), con un enlace explícito entre ancla y perilla (`at.knob: 'Entering_Stage.HelpAfter'`).

**Verificador:** El subclaim de que G_SAVE4/5 no tienen contrato es falso. contract.json tiene 'fw.stage' (literal, on.gate=block, on.move=warn) y contractFor los cubre. Lo demás se sostiene (v/gates):
- +10 s en el expected de G_BREATH mueven 470 elementos y +9,2 s el total; en G_GRAB, 223;
- hay 18 anclas a fin de espera, y 560 de 592 inicios cambian entre Fast e Idle;
- VO_11h está en G_BREATH.start+12, mientras el anexo 14:30 da HelpAfter desde VO_11b.
Mitigación existente: C3.NOTBLOCKING (info) en Problems y warn en la tarjeta para gate y move de esas esperas. Pero cambiar el expected es op 'sim', que es silencioso, y la simulación Slow/Idle de Entering no corresponde a Unreal.

#### D9 · Cargar un WAV puede pisar otro WAV o tomar el nombre de una voz real
- **Severidad:** medium (el auditor puso medium)
- **Estado:** confirmado
- **Rompe:** partitura
- **Esfuerzo:** S

**Evidencia:** - app.js:364 hace `name = cleanId(file.name)` sin uniqueKey; renombrar sí valida (app.js:220).
- serve_editor.py:121-123: /api/audio escribe sin comprobar si el archivo existe, a diferencia del rename (:108-109 → 409).
- Prueba de cleanId en node:
  - 'VO_10.wav' → 'VO_10', que choca con una clave y un sound existentes;
  - 'vo_12c.wav' → 'VO_12c';
  - 'take 1.wav' y 'take-1.wav' → los dos 'FX_take_1'.
- app.js:366 sube el WAV antes del commit y del guardado. Deshacer o Reload from disk dejan el archivo en inbox ('imported into Unreal on the next push', app.js:368).

**Escenario:** - El socio suelta 'take 1.wav' y 'take-1.wav' en dos sonidos vacíos. Los dos pasan a llamarse FX_take_1, el segundo WAV reemplaza al primero en obra/audio/inbox y el primer elemento conserva la duración del archivo viejo.
- O suelta 'VO_10.wav', una toma nueva: el elemento pasa a llamarse VO_10 dentro de Sound, y en F4 el import crea o pisa un asset VO_10 junto al real (importar_mezcla.py busca por nombre; anexo 17:108,116).

**Arreglo:** - loadWav usa uniqueKey y rechaza los prefijos VO_ y AMB_ en sonidos nuevos, o pide confirmación.
- /api/audio responde 409 si el archivo existe, con una opción explícita para reemplazarlo.
- Registrar los WAV como 'pendientes' ligados al revId (o subirlos al guardar), para que deshacer y recargar no dejen huérfanos.

**Verificador:** Probé cleanId en node: 'take 1.wav' y 'take-1.wav' dan los dos FX_take_1; 'VO_10.wav' da VO_10 y 'vo_12c.wav' da VO_12c. loadWav (app.js:364-367) no llama a uniqueKey; rename sí lo controla (app.js:220). /api/audio escribe sin devolver 409 (serve_editor.py:121-123), a diferencia del rename (:108-109). El WAV se sube antes del commit (app.js:366), así que deshacer lo deja en inbox/. Atenuantes: el original del socio sigue en su disco y el import a Unreal todavía no existe. Medium.

#### D10 · El contrato con Unreal se ata a `key` (editable y repetida), no al id
- **Severidad:** low (el auditor puso medium)
- **Estado:** en parte
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** S

**Evidencia:** - integrity.js:9-17: contractFor compara por regex contra el.key.
- app.js:63 trata 'rename' como QUIET; ver también app.js:221.
- scratchpad/audit/integ.js:
  - mover T_IN +2 s abre la tarjeta 'block:C3.TITLE.STAGE';
  - tras Act.rename a T_INTRO (sin tarjeta), mover y borrar ya no abren tarjeta;
  - renombrar G_BELL y subir el timeout de 25 a 60 tampoco abre tarjeta, y C3.DRIFT desaparece.
- Hay 55 keys repetidas (T_IN×4, FX_GHOSTAPPEAR×9, HAP_PULSE_STRONG×29).
- Hoy la UI solo permite renombrar sonidos nuevos (ui.js:395,414), pero PLAN:321 dice que la key será editable.

**Escenario:** Cuando se habilite renombrar, o una sesión llame a Act.rename, un título de etapa cableado (literal en RunObra) se puede mover o borrar sin ninguna advertencia. El socio lo ve moverse en el editor, el APK no cambia y no queda marcado como '≠ APK'.

**Arreglo:** - Usar `contract.entries[].binds` con ids de elemento (generados una vez desde el regex y versionados), o `hw` por elemento, como propone el anexo 17 §3.2.
- Renombrar deja de ser QUIET y corre C3 contra la key vieja y la nueva.

**Verificador:** El mecanismo es real: contractFor compara por regex contra key (integrity.js:9-17) y 'rename' es QUIET (app.js:63). Pero hoy no hay camino en la UI. Solo los sonidos nuevos tienen campo de nombre (ui.js:395,749), y ese nombre pasa por cleanId, que fuerza el prefijo FX_/VO_/AMB_: cleanId('T_IN') da 'FX_T_IN' y cleanId('G_BELL') da 'FX_G_BELL'. Los elementos existentes no se pueden renombrar. Queda latente hasta que la key sea editable (PLAN:321).

#### D11 · Una ruptura aceptada queda aceptada para siempre, y '≠ APK' no tiene datos para cerrarse
- **Severidad:** low (el auditor puso medium)
- **Estado:** en parte
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** M

**Evidencia:** - integrity.js:21 arma `fp: rule + '|' + el`, sin el valor. El anexo 17:51 pide 'regla + ids + parámetro clave' y reabrir si cambia. Ver también integrity.js:47-49.
- scratchpad/audit/integ.js:
  - una deriva aceptada con timeout 30 sigue 'accepted' con 300;
  - C2.TOTAL.GOAL aceptado sigue aceptado con un total de 46:58.
- app.js:88-89 guarda texto (`msg`) y `neAPK: true`, sin el valor del editor ni el de Unreal.
- ui.js:691: el autor es un conmutador B/S en preferencias locales, así que cualquiera puede firmar como Beltrán.

**Escenario:** 1) El socio acepta 'G_BELL 30 s' con un motivo.
2) Semanas después lo lleva a 300 s y nadie vuelve a ver la advertencia.
3) En F4, la compuerta del APK ('C3 aceptados sin conectar requieren la firma de Beltrán', anexo 17:312) se calcula sobre aceptaciones viejas y una firma que no identifica a nadie.
4) La cosecha no puede cerrar '≠ APK' porque no sabe qué valor esperar.

**Arreglo:** - Registro estructurado: `{fp: rule|el|param, value, unrealValue, family, revAccepted, who}`.
- Reabrir cuando cambie value.
- '≠ APK' se calcula (familia no migrada y valor distinto de la cosecha) en vez de guardarse como bandera.
- El autor lo da el servidor (usuario del sistema o git config), no un botón.

**Verificador:** El escenario principal no se cumple. Probé aceptar la deriva de G_BELL en 30 s y después llevarlo a 300 s: la tarjeta vuelve a salir con motivo obligatorio, porque opItems no consulta score.accepted (integrity.js:65-77). Lo que sí pasa:
- en Problems, C3.DRIFT sigue 'accepted' con el mensaje nuevo (300 s) y el motivo viejo;
- no se guarda el valor aceptado;
- `who` es un conmutador local B/S (ui.js:691).
El problema serio de huellas sin valor está en lo que ya está abierto al cargar, no en lo aceptado (ver el faltante sobre C2.TOTAL.GOAL).

#### D12 · La integridad y la política de commit no corren fuera del navegador, y ni el servidor ni Import validan
- **Severidad:** low (el auditor puso medium)
- **Estado:** en parte
- **Rompe:** partitura
- **Esfuerzo:** M

**Evidencia:** - `node -e "require('./web/editor-obra/app/js/integrity.js')"` da ReferenceError: window is not defined (integrity.js:98 `})(window)`).
- La decisión de la tarjeta (QUIET, filtros, escritura de accepted) vive en app.js:63-96, mezclada con UI.impactCard y toast.
- ui.js usa unas 17 funciones globales de app.js (esc, seek, select, toast, beatAt, laneBusy, loadWav…).
- serve_editor.py:82 solo valida schema==2 y que elements sea un dict.
- importScore (app.js:350-353) reemplaza la partitura entera sin pasar por commit ni por la integridad, y conserva su `accepted`.
- El único test es el golden del motor.

**Escenario:** - Para F4 hay que bloquear el push si hay un BLOQUEA abierto (anexo 17:307). compile.mjs tendría que reimplementar staticProblems y la política, y con dos mantenedores (Beltrán y las sesiones) las dos copias se separan.
- Hoy mismo, importar un JSON con un ancla colgante, o con un `accepted` que lo cubre todo, y apretar Ctrl+S lo deja en disco como fuente de verdad.

**Arreglo:** - integrity.js en UMD, como engine.js.
- Extraer un policy.js puro (operación → ítems → decisión).
- Crear tools/score/check.mjs con los invariantes (sin ciclos, sin anclas colgantes, ids únicos, contrato resuelto). El servidor lo corre en cada PUT y rechaza las violaciones; compile.mjs lo reutiliza.
- Import pasa a ser un verbo de commit, con tarjeta.
- Tests de regresión con los escenarios de este informe (rename, aceptación, ciclos, borrador).

**Verificador:** Los hechos son ciertos:
- integrity.js:98 `})(window)` da ReferenceError en Node, aunque con `global.window = global` corre (así lo usamos los dos auditores);
- la política está en app.js:63-96, mezclada con la UI;
- el servidor solo valida schema y elements (serve_editor.py:82);
- importScore no pasa por la integridad y conserva accepted (app.js:350-353).
Pero importar es una acción explícita de menú y deshacible (empuja a undo). compute() reporta las anclas colgantes como C1.ANCHOR.MISSING en Problems, y el escenario de compile.mjs es hipotético. Es deuda para F4, no una rotura de hoy.

#### D13 · Perillas sin enlace que una máquina pueda leer, y con la decisión de reconciliación contradicha entre plan y anexo
- **Severidad:** low (el auditor puso medium)
- **Estado:** en parte
- **Rompe:** experiencia en Unreal
- **Esfuerzo:** S

**Evidencia:** - roles.json guarda filas de presentación `[label, "12", unit, fader%, color, "ExploreTime · minimum; …", lock]`: valores como texto, la variable dentro de texto libre, sin id de elemento ni de actor.
- contract.json solo tiene `knob {name, value, lock}` para 4 esperas.
- La partitura no guarda base ni ImportedRev por perilla.
- PLAN:344 y :398 piden tres vías en runtime con ScoreApply; el anexo 11:223 dice 'la decisión 1 queda propuesta aplicada en el editor, no tres vías en runtime'.
- El anexo 11:212 y PLAN:67 eligen DataAsset; PLAN:333,387 siguen diciendo DataTable.
- PLAN:10 dice que gana el plan, o sea la versión vieja.

**Escenario:** 1) Se aplica la primera propuesta, por ejemplo HelpAfter de 4 a 5.
2) No hay forma automática de saber a qué ancla de la partitura corresponde, cuál era el valor base cosechado, ni si Beltrán lo cambió en Details después.
3) Resultado: se pisa un valor final aprobado (memoria 'valores-de-test-son-finales') o se descarta la edición del socio.

**Arreglo:** - Escribir un ADR corto antes de F4 que fije el formato (DataAsset) y quién aplica (propuesta en el turno de la cola).
- Definir el esquema `knobs: {id: {owner actorPath, var, scope, base, baseRev, value, lock}}` en obra/unreal/harvest.json, más el enlace ancla↔perilla en la partitura.
- Corregir PLAN §3.3, §4 y §6 para que no contradigan a los anexos.

**Verificador:** La contradicción está dentro del propio PLAN. La línea 67 da el DataAsset como preferido y la 333 la DataTable; las líneas 344, 387, 398 y 412 piden tres vías, contra el anexo 11:223; y PLAN:10 hace ganar al plan. roles.json son filas de presentación con la variable en texto, como dice su propia nota. Pero es documentación de una fase que no empezó: hoy nada se rompe. Hay que corregirla antes de F4.

#### +D1 · Recortar no evalúa el contrato de lo que arrastra: mover una VO cableada pide tarjeta, pero recortar el elemento al que está anclada la mueve en silencio
- **Severidad:** high
- **Rompe:** experiencia en Unreal

**Evidencia:** - integrity.js:60-64 agrega la familia de dependientes a `touched` solo para 'move' y 'offset'; con 'trim', touched = op.ids (app.js:150-156).
- v/trimcmp.js: VO_04 está anclada a CANDS_IN.end. Recortar CANDS_IN +3 s da 'silent' y VO_04 pasa de 123,45 a 126,45. Mover VO_04 +3 s directo abre la tarjeta con warn C3.VO.WIRED.
- v/trimrel.js: 27 elementos de duración fija cuyo recorte de +3 s desplaza una VO cableada dentro de su propio momento sin ninguna tarjeta. Ejemplos: WALK2→VO_02 (5,0→8,0 s en 1.11), SOUL_FRONT→VO_05, CALIB/HUD_IN/TO_HUD→VO_07.

**Escenario:** 1) El socio alarga CANDS_IN 3 s arrastrando el borde derecho, el gesto de NLE más común.
2) VO_04 se corre 3 s dentro del momento 2.4, sin tarjeta, sin toast y sin marca '≠ APK'.
3) En el APK, VO_04 sigue sonando donde la llama HallSay.
El editor muestra una obra que Unreal no reproduce, no queda nada en Problems y se incumple la promesa central: nunca romper en silencio.

**Arreglo:** - En opItems, calcular `touched` por efecto y no por verbo: comparar before y after y tomar todo elemento cuyo inicio relativo a su momento cambió.
- O, como mínimo, para 'trim' agregar Engine.family del elemento (dependientes anclados a su fin).
- Agregar un test de regresión con CANDS_IN/VO_04.

#### +D2 · La regla de los 15:00 está saturada desde la carga: alargar la obra 5 minutos no abre tarjeta ni toast
- **Severidad:** medium
- **Rompe:** confusión

**Evidencia:** - El total típico es 1018,0 s (16:58) > 900, así que C2.TOTAL.GOAL ya está abierto al cargar (integrity.js:24).
- Su huella es 'C2.TOTAL.GOAL|', sin valor (integrity.js:21), y opItems solo agrega los problemas cuya huella no estaba antes (integrity.js:90-93).
- v/sat.js: mover +300 s 23 de los 73 momentos (0, 1.2, 1.3, 1.6, 1.7…) da 'silent' con el total en 22:00. Mover +300 s 386 elementos sin contrato tampoco abre tarjeta.
- Al cargar ya hay abiertos 4 C2.WAIT.NOHELP, 2 C3.DRIFT y 2 C1.ANCHOR.CYCLE, que tampoco vuelven a avisar si empeoran.

**Escenario:** 1) El socio agrega aire en varias escenas, una por una.
2) El total pasa de 16:58 a 22:00 sin tarjeta ni toast: solo cambia el número de la barra de estado.
3) La tarjeta de impacto, que es la garantía del editor, calla porque el problema 'ya existía'. Lo mismo pasa con cualquier regla que ya estaba abierta al cargar.

**Arreglo:** - Incluir el parámetro clave en la huella (total por minuto, valor del timeout, distancia de la ayuda).
- En opItems, avisar cuando un problema existente empeora más allá de un umbral (por ejemplo, el total crece más de 10 s respecto del before).
- Que el baseline de la tarjeta sea la última revisión guardada, no 'lo que ya había'.

#### +D3 · 'Proceed and repair' guarda offsets que dependen de la persona elegida en pantalla
- **Severidad:** medium
- **Rompe:** partitura

**Evidencia:** - applyDeleteRepair (app.js:99-116) usa App.sched.t, que se calcula con App.persona (app.js:51), y lo hornea como at.off o como duración fija.
- v/delrep.js, copia literal de la función:
  - al borrar G_BELL, FX_BELLRING queda en at.off 1,5 (Fast), 5 (Typical) o 25 (Idle), y GHOST_BELL pasa a duración fija de 1,5, 5 o 25 s;
  - al borrar G_BREATH, BIO_ON y HAP_PULSE_SOFT quedan en 1,8, 6 o 25;
  - el total típico posterior cambia: 1021,3 contra 1035,2.
- La tarjeta promete 'they keep their times' (integrity.js:84).

**Escenario:** 1) Beltrán revisa con la persona Idle para ver los timeouts y borra una espera aceptando la reparación.
2) Los 25 s del timeout quedan horneados como offset fijo de sus dependientes.
3) El socio, en Typical, ve 20 s de aire muerto que nadie puso, sin rastro en Problems.
El mismo borrado produce partituras distintas según una preferencia de la vista.

**Arreglo:** - Calcular la reparación siempre con ScoreEngine.resolve(before, {persona: 'typical'}), o con una persona fija documentada.
- Si el elemento borrado es una espera (elástica), avisar en la tarjeta que sus dependientes pierden la elasticidad, u ofrecer re-anclarlos al fin de la espera anterior.

#### +D4 · La pestaña 3D acepta ediciones (marcadores, notas, agregar) que nunca se guardan y se pisan con la siguiente edición del timeline
- **Severidad:** medium
- **Rompe:** partitura

**Evidencia:** Lo verifiqué leyendo el código, no en el navegador:
- initKeys() corre en todas las vistas (app.js:37,392-418), así que en ?view=3d funcionan M (Act.bookmark), Shift+A y Shift+M. noteBox además pasa la pestaña 3D a modo 'all' (ui.js:517).
- save() se niega en la vista 3D (app.js:338) y beforeunload no avisa ahí (app.js:420).
- Las pestañas de timeline ignoran d.score (app.js:380), y la pestaña 3D reemplaza su App.score con cada edición que llega del timeline (app.js:380).
- Su markDirty escribe la clave compartida LS_DRAFT con el baseRev que tenía al arrancar (app.js:336).

**Escenario:** 1) El socio sigue la reproducción en la pestaña 3D, en el segundo monitor, y por costumbre de NLE aprieta M: ve 'Bookmark at 03:12.4'. O escribe una nota con Shift+M.
2) En cuanto Beltrán edita algo en la pestaña de timeline, la pestaña 3D recibe la partitura y la marca o la nota desaparecen. Nunca llegaron a disco.
3) Si el timeline guardó después de que se abrió la pestaña 3D, el borrador que esta escribió lleva un baseRev viejo. Al recargar el timeline se descarta en silencio (app.js:33).

**Arreglo:** - En ?view=3d, desactivar los verbos de edición, o reenviarlos por BroadcastChannel como {op} a la pestaña dueña para que los aplique con commit().
- Usar una clave LS_DRAFT propia de la pestaña dueña.
- Mostrar en la pestaña 3D 'read-only view'.
