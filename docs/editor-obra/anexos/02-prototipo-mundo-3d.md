> Anexo de la auditoría del 2026-10-01 (informe: mundo 3D del prototipo). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md); donde este anexo lo contradiga, gana el plan.

# Auditoría del mundo 3D del prototipo web (`world.js`)

## 1. Arquitectura de la escena

**Carga y acoplamiento.** `index.html:347-352` carga cinco scripts clásicos que comparten variables globales, en este orden: three r128, `GLTFLoader` (examples/js), `world.js`, `ensayo.js`, `timeline.js` y `guion.js`. No usa módulos. `world.js` define `S`, `scene`, `camera` y todos los objetos. `timeline.js` define `W`, `evaluate` y el bucle. `guion.js` define posiciones y closures que mutan objetos de `world.js`. Por eso hoy ninguna de las tres piezas funciona sola.

**Render.** Hay un solo `WebGLRenderer` con antialias y pixelRatio de hasta 2. La cámara de 72° vive dentro de `rig` (el pawn), con los ojos a `EYE = 1.2` (`world.js:29,43-50`). `hud` es hija de la cámara. La escena no tiene luces: todo es `MeshBasicMaterial` o `ShaderMaterial` con iluminación falsa escrita a mano. El color se gestiona a mano con `col()` (`convertLinearToSRGB`, `world.js:9`), sin `outputEncoding`.

**Registro de objetos.** No existe. Cada objeto es una constante global: `alma`, `bell`, `sensor`, `container`, `ringG`, `hudPanel`, `cands`, `tiles`, `doors`, `envs[i].userData.{blob,pacer,heart,cell,orbs,worm,table,strokes}`, `RES`, `FISH`, `SHARE_G`… `MODELS` (`world.js:435`) solo guarda referencias a los GLB ya cargados.

**Patrón `install…()`.** Primero se construye un provisorio procedural. Después `loadGLB` (`world.js:437-443`) baja `modelos/<SM>.glb.json`, decodifica el base64 byte a byte con `atob` y lo pasa a `GLTFLoader.parse`. Hay 7 GLB:
- anillo (`:480`)
- mando (`:737`)
- paleta (`:1035`)
- sensor bio (`:1075`)
- HUD (`:1124`)
- SHARE (`:1323`)
- cuadro de resultados (`:1558`)

Cada `install` **reemplaza los materiales** por shaders propios, eligiéndolos por el nombre del slot (`/Light/`, `/Rim|Frame/`, `/Glass/`, `/Pulse/`…; ver `installRing:467-468` e `installHud:1104-1113`). De Blender/Unreal solo viajan la geometría y los nombres de los slots; el material no viaja.

**Shaders.** `world.js` crea 37 `new THREE.ShaderMaterial`, con GLSL escrito en template strings:
- `NOISE` se interpola como texto (`:160-164`).
- `groundMat` inyecta fragmentos de vértice y de fragmento por etapa (`:537-542`).
- Los objetos de uniforms se comparten por referencia: `hallU` en Hall, puertas y baldosas; `envU[i]` en cielo, suelo y motas de cada etapa.

**Cámara y navegación.** Solo existe la cámara del usuario:
- Arrastrar con clic derecho gira la mirada (`world.js:743-748`).
- El mouse es la mano: un rayo a 0,6 m (`timeline.js:1000`).
- Hay un FOV ajustable y un "camBack" que retrocede la cámara sobre su eje de mirada (`timeline.js:1169-1176`, `:996`).
- El rig lo mueven los clips `walk` (`timeline.js:42-49`) y `baseWorld → rigTo(PS0)` (`:169`).
- No hay cámara libre, ni planta, ni OrbitControls.

**Bucle.** `frame()` está en `timeline.js:983-1081`, no en `world.js`. El orden de cada cuadro es:
1. `S.t += dt`, con dt recortado a 0,05 s (`:984-987`).
2. `tickGates`.
3. `evaluate(S.t)`.
4. Los ticks interactivos (respiración, dibujo, orbes, paleta, resultados, aparición).
5. `renderer.render` (`:1072`).
6. La actualización del DOM.

**Estado del mundo = función del tiempo, a medias.** `evaluate(t)` (`timeline.js:286-311`) hace `resetW()` + `baseWorld()` y aplica en orden cada clip con `s ≤ t`; los clips terminados se aplican con k = 1. Después `applyW` (`:171-209`) traduce `W` a los objetos. Por eso el cabezal es "scrubbable". Tiene tres límites:
- **El estado está en código, no en datos.** `guion.js` tiene 123 closures `apply`, 18 `during` y 10 `gate`.
- **Hay dos estilos mezclados.** `guion.js` hace 135 escrituras a `W`, pero también 51 mutaciones directas de transform. Ejemplos: `almaAt` (`guion.js:34`) escribe `alma.position`, y `contTo` (`guion.js:41`) escribe `container.position`. Los subsistemas nuevos (APPEAR, POP, HALO, STAGE_RINGS, FISH: `world.js:1130,1198,1219,1239,1250`) ya siguen el patrón bueno: "los clips ponen `W.x`, un tick dibuja".
- **Parte del mundo no depende de t:**
  - Trazos, melodía y orbes son estado de interacción (`world.js:815-838, 900-918`).
  - La animación ambiente usa el reloj de pared `S.clock` (`timeline.js:991`).
  - El polvo nace de `Math.random` (`world.js:186`).

**API.** `window.SC` existe solo con `?debug` (`timeline.js:1188`). Expone `seek`, `setPlaying`, `evaluate`, `computeSchedule`, `W`, `S`, `EDITS`, `GL`… No hay una API del mundo: no se pueden listar entidades, leer o escribir una pose, ni seleccionar.

**Coordenadas.** Metros con Y arriba, y una maqueta propia que **no es el layout de Unreal**:
- Hall en el origen.
- Llegada en x = −40.
- `CENTER = (24,0,0)`, con los cinco entornos superpuestos en el mismo punto (`world.js:530-531`).
- Paradas del pawn (`PS0…PF3`) y posiciones fijas (`BELL_POS`, `SENSOR_POS`, `CONT_HALL`, `ALMA_HALL/SIDE/ST/ST2`, `CAND_POS`…) en `guion.js:11-24`.

Lo único compartido con Unreal es el **marco relativo a la parada**: `front(pose, fwd, up, side)` (`world.js:757`) más `ensDelta` (`ensayo.js:288`), que aplica en cm el *desplazamiento* de los TargetPoints `sc<K>_*` respecto de su base (`guion.js:21-23`).

---

## 2. Inventario

| Objeto | Web | Unreal | Estado web |
|---|---|---|---|
| Niebla del inicio/final + polvo que sigue a la mano | `voidSky`, `dust` `:179-202` | entorno oscuro de la Obra | shader |
| Títulos líquidos | `titleMesh` `:218-237`, `HALL_T` `:330-335` | `BP_StageTitle_SC`, `BP_IntroTitle_SC` (inferido por nombre) | canvas + shader |
| Hall (cáscara, óculo, haz, piso) | `hallG` `:240-283` | `SM_HallShell_SC` **pendiente**; `BP_HallDirector_SC`, `BP_LightShaft_SC` | procedural (lathe) |
| Puertas | `doors` `:294-305` | `BP_Door_SC` | procedural |
| Baldosas | `tiles` `:307-325` | Hall (actor exacto no confirmado) | extrude + shader |
| Alma (guía) + cáscara de partículas | `alma` `:350`, `ALMA_SHELL` `:356` | `BP_Alma_SC`, `BP_AlmaAura_SC` | blob shader |
| Timbre | `bell` `:383-393` | `BP_BellArt_SC` | **provisorio** (cilindro + toro) |
| Mando / sensor | `sensor` `:396-406` + `installController` `:730` | `SM_QuestCtrl_SC`, `BP_QuestCtrl_SC`, `BP_UserTool_SC` | GLB real |
| Orbe del sensor | `sensorOrb` `:408` | `BP_SensorOrb_SC` | shader |
| Candidatas | `cands` `:419-420` | `BP_SoulPicker_SC` / `BP_ProtoSoul_SC` | blob |
| Alma propia + anillo + cavidades | `container`, `soul`, `ringG` `:421-431`, `installRing` `:462` | `SM_ChargeRing_SC`, `BP_SoulRing_SC`, `BP_ChargeFx_SC` | GLB real, mismo contrato U = etapa + t |
| HUD píldora + hermana | `hudPanel` `:484`, `installHud` `:1102` | `SM_HUD_SC`, `BP_SoulHUD3D_SC` | GLB real |
| Velo de etapa | `veil` `:495-510` | velo de `BP_StageRunner_SC` / `BP_Obra_SC` | shader |
| Aliento (Entering) | `aliento` `:515-527` | `BP_BreathAir_SC` (inferido por nombre) | puntos |
| E1 valle, metaball, pacer, progreso | `:543-570`, `PACER_PROG` `:1343` | `BP_BreathValley_SC`, `BP_BreathBlob_SC`, `BP_Pacer_SC` | proxy |
| E2 membrana del latido | `:571-582` | `BP_HeartScape_SC`, `BP_HeartDust_SC` | proxy |
| E3 fluido + célula | `:583-604` | `BP_FluidMedium_SC`, `BP_LovingCell_SC` | proxy |
| E4 salar, gusano, 68 esferas + halos | `:605-638`, `tickAttract` `:815` | `BP_ChladniFloor_SC`, `BP_Orb_SC`, `BP_SlotChain_SC`, `BP_Sequencer_SC` | proxy + interacción |
| E5 océano, mesa, trazos | `:639-650`, `tickDraw` `:900` | `BP_DrawSea_SC` + rig TB | proxy + interacción |
| Paleta 3D | `PAL3` `:920-1035` | `SM_DrawPalette_SC`, `BP_DrawPalette_SC` | GLB real |
| Sensor bio + ondas | `BIO` `:1043-1075` | `SM_BioSensor_SC`, `BP_BioSensorArt_SC` | GLB real |
| Fantasmas de instrucción | `GESTURES`, `drawGhost` `:653-692` | `BP_GhostPlayer_SC` | keyframes en JS |
| Aparición "luz primero" | `APPEAR` `:1132-1192` | `BPC_AppearLuz_SC` | determinista |
| Teletransporte, halo de carga, anillos de etapa | `POP` `:1199`, `HALO` `:1220`, `STAGE_RINGS` `:1240` | `BP_ChargeFx_SC` (StageRing0..4) | determinista |
| Ameba-pez (cometa) | `FISH` `:1252-1287` | TargetPoints `final_fish_door/away` (`BP_Obra_SC.md:184`) | determinista |
| SHARE / DON'T SHARE | `SHARE_G` `:1288-1336` | `SM_ShareButton_SC`, `BP_ShareButton_SC` | GLB real |
| Cuadro de resultados | `RES` `:1378-1597` | `SM_Results_SC`, `BP_ResultsArt_SC`, `BP_JourneyContent_SC` | GLB + canvas |
| Constelación | `buildConstellation` `:782` | `BP_Constellation_SC` | esferas |
| Aviso SIMULATED PROTOTYPE | `DISC` `:1360` | horneado `hornear/aviso.html` | texto |

---

## 3. Vista 3D editable: qué existe y qué falta

**Ya existe:**
- Raycaster (`pick`, `world.js:749`).
- Marco de parada (`pose`/`front`).
- `ensDelta` (Unreal → web, solo 4 anclas por etapa).
- `W` como resumen de lo que está activo.
- Overlays de cues: SONIDO/HÁPTICA/EFECTO (`world.js:142-150`), `#vo` y `#hint`.
- Subsistemas deterministas que se ven igual al mover el cabezal.

**Falta, en orden de dependencia:**

1. **Registro de entidades** `ENT[id] = { obj, label, kind, unrealTag, anchors }`. El id debería ser el tag del actor en Unreal. En Test_Hall ya se migró a objetos reales leídos por tag (`TituloInicio`, `Timbre`, `Sensor`; `BP_AuthorMark_SC.md:3`), así que la convención ya está.

2. **Modo Editar vs modo Jugar.** Hoy el clic izquierdo es la mano del usuario y dispara interacciones (`world.js:747`, `tickAttract:825`). Hace falta un conmutador, como Editor/PIE en Unreal.

3. **Anclas como datos: el gizmo edita la marca, no el objeto.** Mover el objeto directamente no sirve por dos razones:
   - `evaluate` reescribe todas las poses en cada cuadro.
   - `tickAppear` toma `matrixAutoUpdate = false` y pisa la matriz (`world.js:1170`).

   Las constantes de `guion.js:11-24` y las 51 mutaciones directas tienen que pasar a una tabla `anchors[id] = { stop, fwd, side, up (cm), yaw (°), scale }`, y los clips deben leer de ahí. Las anclas se ven como marcas fantasma con etiqueta. Al seleccionar Alma en medio de `ALMA_SIDE`, se editan sus dos anclas (origen y destino), no la interpolación.

4. **Gizmo.** `TransformControls` y `OrbitControls` de r128 existen en examples/js en jsdelivr, igual que el `GLTFLoader` que ya se usa (`index.html:348`). Para el editor de cine, el gizmo debería mostrar valores en el marco del pawn ("2,20 m al frente · 30 cm a la izquierda · +5 cm sobre los ojos"), con encastre en cm y grados, no en xyz del mundo.

5. **Separar la cabeza de la cámara de render.** Cinco cosas cuelgan de `camera`:
   - `hud` (`:50`)
   - aliento (`:526`)
   - fantasmas (`:656`)
   - paleta (`:943`)
   - fantasmas bio (`:1073`)

   Además hay efectos que leen la cámara: la aparición se pone de canto al ojo (`:1172-1174`), y el polvo, el cielo y el velo la siguen (`timeline.js:1014-1016`). Con una cámara libre, todo eso la seguiría a ella. Hace falta un `head` (Object3D) del pawn y tres cámaras de render:
   - **POV**: la del visitante, con HUD.
   - **Libre**: orbit.
   - **Planta**: ortográfica cenital, con el cono de mirada y anillos de distancia de 0,5, 1, 2 y 3 m.

   Los materiales con `depthTest:false` (anillo, HUD, títulos, velo, `world.js:430,489,506`) se dibujan a través de todo en la vista libre. Hay que darles un modo "rayos X" opcional.

6. **Marcas de Unreal.** Hoy solo viajan `sc<K>_alma_in/_alma_side/_charge/_title` y como delta. No viajan `ObraChargeTarget`, `final_sketch`, `final_alma`, `final_fish_door` ni `final_fish_away` (`BP_Obra_SC.md:41,184`), ni los objetos con tag de Test_Hall. Hace falta un exportador general: todos los actores con tag `sc_*`/`final_*`/`mark_*`, en el marco de su parada.

7. **Qué está activo en el cabezal.** Lista "en escena ahora" con los clips de `ORDER` tales que `s ≤ t < e`, cruzada con `W` y con resaltado mutuo entre lista y viewport. Requiere que cada clip declare su `target`; hoy los `apply` son opacos. Los sonidos se pueden mostrar como íconos en su emisor, aunque la web los toque en 2D, sin panner.

---

## 4. Vista 3D en otra pestaña o ventana

**Hoy no se puede sin cargar todo dos veces.** `baseWorld` y `applyW` (`timeline.js:159-209`) y las closures de `guion.js` tocan objetos three directamente.

**Fase rápida (misma página, dos roles).**
- `?view=timeline` oculta `#stage`, **no renderiza**, pero sigue evaluando: las closures necesitan los objetos.
- `?view=3d` oculta `#bar`.
- El costo es cargar dos veces unos 360 KB de JS y 3,9 MB de `.glb.json`, decodificados en el hilo principal (`world.js:440`), más unos 40 programas de shader. Es aceptable en escritorio. Si las dos pestañas renderizan, cada una se queda con la mitad de la GPU.

**Dueño del reloj: la pestaña de timeline.** Lleva el transporte, el audio y el guardado.
- No conviene mandar el cabezal cuadro a cuadro. Se emite un mensaje por evento: `{ playing, t0, wall0, speed, rev }`, y el seguidor calcula `t = t0 + (ahora − wall0)·speed`, usando `performance.timeOrigin + now()` porque `performance.now()` difiere entre pestañas.
- Hoy `S.t` se integra por cuadro con tope de 0,05 s. Eso tiene dos fallas: en una pestaña de fondo `requestAnimationFrame` se detiene y el reloj se para, y por debajo de 20 fps el tiempo se atrasa respecto del audio. Conviene anclarlo a `AudioContext.currentTime` o al reloj de pared, también en el modo todo-en-uno.

**Esperas en vivo.** El `tick` de las esperas lee la entrada del usuario (`S.down`, `S.mouse`, `S.stillness`; `guion.js:404`), que vive en la pestaña 3D. Hay dos caminos:
- La 3D resuelve la espera y emite `{ uid, dur, how }`, y la de timeline lo aplica a `GL` y recalcula el horario.
- El modo de dos pestañas trabaja en "simulado" por defecto (`timeline.js:1096`), que es determinista y no necesita entrada. Es el modo natural del editor de cine.

**Canal de sincronización.**
- **BroadcastChannel** es lo simple, pero con el particionado de almacenamiento de Chrome dos pestañas solo lo comparten si están bajo el mismo sitio de nivel superior: las dos dentro de claude.ai, o las dos abiertas directo. **Hay que probarlo en el host real antes de diseñar encima.**
- **`window.open` + `postMessage`** sirve si el sandbox permite popups.
- **SharedWorker** no aporta nada frente a BroadcastChannel: tiene el mismo problema de partición y además necesita una URL de script publicada (no `blob:`).
- **La base del artifact con `onSnapshot`**, ya usada para el audio (`timeline.js:515`), sirve como canal lento para el *documento* y para varios dispositivos.

**Documento.** El guardado hace un `set` del documento entero `timeline/main` (`timeline.js:920`). Dos pestañas o dos personas se pisan. Hay que partirlo en documentos (clips, anclas, look) y guardar con `update`, merge y número de revisión.

**Audio y overlays.**
- Suena una sola pestaña. Los cues de interacción que nacen en la 3D (`world.js:826,907`) viajan por el canal.
- `#vo`, `#hint`, `#cues` y `#lefthand`/SAVE (`world.js:794-804`) van con la vista 3D.

**Fase buena.** Separar en tres capas:
- **doc**: datos.
- **engine**: horario más `evaluate(t) → W`, sin three.
- **view**: `applyW` más ticks.

Así la pestaña de timeline queda liviana, sin three ni GLB, y en las dos pestañas sale el mismo `W`.

---

## 5. Problemas

**Rendimiento**
- `tickDraw` regenera el `TubeGeometry` del trazo entero con cada punto nuevo (`world.js:909-915`). Es O(n²), con un tanque de 30 m.
- `setBellFill` recrea la geometría mientras carga (`:393`).
- Los shaders compilan la primera vez que se ven, así que hay tirones al entrar a cada etapa. De ahí la regla de recorrer toda la obra con `SC.seek` (README).
- `document.querySelector` se llama en cada cuadro (`timeline.js:1068`).
- Planos de suelo de 160² a 220² segmentos (`:546,574,608,642`). Solo uno está visible a la vez, así que pasa.

**Tamaño**
- `world.js` es un monolito de 158 KB y 1597 líneas.
- Los modelos pesan 3,9 MB en base64 (+33 %). Solo `SM_QuestCtrl_SC.glb.json` pesa 1,35 MB.

**three r128 (2021)**
- Actualizar implica pasar a módulos: examples/js desapareció en r148.
- El ColorManagement activo por defecto (r152) alteraría todos los colores calibrados contra Unreal con `col()` y hex.
- El cambio `uv2` → `uv1` (r151) rompe `world.js:701` y `:1313`.
- Recomendación: **quedarse en r128** mientras no se reescriba con bundle. Lo que hace falta para el editor (TransformControls, OrbitControls) existe en r128.

**Shaders frágiles**
- Un uniform sin declarar deja el material muerto sin error (memoria `web-shader-uniform-sin-declarar`).
- El GLSL está en strings sin lint, con uniforms compartidos por referencia e inyección de fragmentos.
- Mitigación: precompilar al arrancar (forzando visibles todos los entornos) y mostrar **en la UI** un aviso si `renderer.info.programs` tiene `diagnostics` con `!runnable`, no solo revisarlo antes de publicar.

**Duplicación con Unreal**
- Cada mecánica está reimplementada: aliento, oleaje, latido, célula, Chladni, secuenciador, dibujo, paleta, HUD, anillo, resultados.
- Las constantes se copian a mano:
  - `CHARGE_T` (`:25`) = `BP_Obra_SC.ChargeTimes`
  - `BELL_PRESS_*` (`:391`)
  - `PAL_SIDE_SCALE` (`:930`)
  - `TRAVEL_*` (`:532`)
  - el paso del secuenciador `5.333/8`, repetido en `:834`, `:840` y `:1579` (= StepBPM 90)
- La tabla del README registra unos 40 cambios integrados en dos días (09-29 y 09-30). Solo `ensayo.js` es generado.

**Fidelidad**
- Los entornos transmiten el clima de cada etapa, no son réplicas.
- El Hall es procedural; `SM_HallShell_SC` está pendiente.
- El timbre es provisorio aunque `BP_BellArt_SC` existe.
- Los materiales de Unreal se sustituyen.
- No hay luz horneada, ni Niagara, ni audio espacial.

---

## 6. Recomendación: hasta dónde llega la fidelidad

**Regla: previs representativa. La web es la verdad del tiempo y del espacio; Unreal es la verdad del look.**

**Contrato fiel (tiene que coincidir con Unreal):**
- Cada tiempo.
- Cada ancla, en cm y grados en el marco de la parada.
- Tamaños.
- Visibilidad y fase de aparición o desaparición.
- La paleta de cada etapa: cielo, velo y tinte del suelo.
- Qué suena y desde dónde.
- Qué espera al usuario y su cortafuegos.

**Representativo:**
- Piezas héroe con su GLB real y el material "de familia" (hormigón claro).
- Entornos como proxys de color y forma.
- Alma y el alma propia como blobs.

**No replicar:**
- Partículas finas, raymarch, Niagara, post, rendimiento.
- Mecánicas completas. Las interactivas ya hechas se **congelan**. Las nuevas entran como "caja": duración simulada con un parámetro ("el usuario tarda X s") y una miniatura o clip de referencia capturado en Unreal y adjunto a la etapa.

**Generar en lugar de copiar:**
- Extender `ensayo_export.py` a un **manifiesto de la obra**: constantes de `BP_Obra_SC`, todas las anclas con tag y los colores de cielo y velo.
- La web lo lee y lo devuelve editado, para que Unreal lo aplique por tag.
- Para el look exacto: un botón "ver desde aquí en Unreal" que arranque la Obra en ese beat con su DebugStart, en vez de perseguir paridad visual.

**Orden sugerido (cada paso no rompe el anterior):**
1. Registro de entidades + `clip.target` + lista "en escena ahora".
2. Pasar las 51 mutaciones directas a `W` (patrón FISH/POP/APPEAR) y `guion.js:11-24` a la tabla de anclas.
3. Cabeza separada de la cámara de render, vistas POV/libre/planta, y gizmo sobre anclas en el marco del pawn.
4. Reloj anclado al de pared o audio, bus de sincronización, `?view=` y prueba del canal en el host real.
5. Separar engine y view, para que la pestaña de timeline quede sin three.