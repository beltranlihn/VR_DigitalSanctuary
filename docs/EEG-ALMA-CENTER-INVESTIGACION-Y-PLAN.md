# EEG Alma Center: investigación y plan

> 2026-11-14. Investigación profunda de PiEEG (web, documentación, GitHub, Discord, correos de Ildar y Youssef) para decidir qué construir con el prototipo PiEEG XR que nos prestaron por un mes, y el plan de la app **EEG Alma Center**.
> Lo anterior: [`PIEEG-XR-ARRANQUE.md`](PIEEG-XR-ARRANQUE.md) (cómo conectarlo) y [`PIEEG-XR-DATOS.md`](PIEEG-XR-DATOS.md) (qué datos da).

---

## 1. Resumen en diez líneas

1. **El sensor entrega solo 8 ondas crudas** (µV, 250 Hz) de la frente y las sienes. Todo lo demás se calcula, y **PiEEG publica todo ese cálculo en TypeScript con licencia MIT**: detectores, calibración, juegos, montaje 3D. Es código que podemos leer, portar y mejorar.
2. **Lo que sale bien de esta máscara:** parpadeos, mirada izquierda/derecha/arriba/abajo (EOG), tensión y gestos de la cara (EMG), bandas espectrales frontales, asimetría alfa frontal. Lo que **no** sale: alfa occipital de ojos cerrados, pulso, "emociones" directas.
3. **Lo que ellos mismos admiten:** "foco" y "relajación" son razones de bandas, no estados mentales; el foco sube con la tensión de la cara; nada de esto generaliza entre sesiones ni personas sin calibrar.
4. **Su mejor método es la calibración por persona**: 20 s de REST + 20 s de ACTIVE, ranking de (canal × banda) por Cohen's d, umbral entre reposo y pico con histéresis. Es lo que hay que copiar.
5. **Sus pruebas de campo** (MoguLive en Tokio, 2 meses; BeFootball en Madrid, porteros en VR) confirman: Face Trainer funciona muy bien, el control por "foco" es inconsistente y con lag, Mind Reader (P300) falló 4 de 4. El equipo pesa.
6. **La comunidad es chica** (Discord ≈ el equipo + unos pocos usuarios). No hay proyectos de terceros que nos sirvan. Lo útil está todo en el repo de PiEEG y en lo que pide su hackathon starter.
7. **Sus herramientas son potentes pero dispersas**: Cloud, Server, Studio, Buddy, Local Bridge, Chrome, Agent, Unity, BodyPress. Ninguna centraliza, ninguna tiene un mapeo libre de señal → salida, y la estética es la de un dashboard de desarrollador.
8. **Propuesta: EEG Alma Center**, app de escritorio en **Electron** (la misma base que VEATION, con sus tokens de diseño), que **recibe** (PiEEG XR, y después Muse y Polar), **limpia**, **calcula**, **calibra por persona**, **muestra** (ondas, espectro, cabeza 3D, sesiones) y **envía** lo que elijamos a donde elijamos (OSC, WebSocket, grabación), con un router de mapeos configurable.
9. **Fases en el mes del préstamo**: F0 conectar y ver (2-3 días) · F1 limpiar, bandas y cabeza (3-4 días) · F2 detectores y calibración (1 semana) · F3 router de salidas y contrato del BioHub (3-4 días) · F4 protocolos de experimento y comparación de sesiones (1 semana). GITEX es del 4 al 12 de diciembre.
10. **Decisiones que necesito de Beltrán**: están en §9.

---

## 2. Qué se puede medir (y con cuánta confianza)

Sale de leer el código fuente de `PiEEG-server/dashboard/src` (hooks `useBlink`, `useFocus`, `useRelax`, `useBandPowers`; experiencias `eye-track`, `face-trainer`, `avatar-foundation`, `orb-control`, `neural-maze-lock`, `glitching-reality`, `premeditatio-malorum`) y de la doc.

| Señal | Cómo la calculan ellos (constantes reales) | Confianza con el XR | Para qué nos sirve |
|---|---|---|---|
| **Parpadeo** (evento, cuenta, amplitud) | Pico a pico en ventana de 100 ms, evaluado a ~40 Hz; línea base = mediana + MAD de ~3 s; umbral = máx(25 µV, base + máx(5σ, 8 µV)); dura 60–600 ms; refractario 300 ms; calentamiento 0,8 s. Canales 0 y 1 (frente) promediados | 🟢 Alta. Lo vimos en nuestra primera grabación | Evento limpio: confirmar, marcar, "soltar". Frecuencia de parpadeo baja con la calma |
| **Mirada** (EOG, posición X/Y) | Horizontal = Fp2 − Fp1; vertical = (Fp1 + Fp2)/2. Media sobre 120 ms. Regresión ridge polinómica de grado 2 ([1, h, v, h², hv, v²], λ = 0,01). Calibración de 5 puntos (2,5 s cada uno) y **aprendizaje en línea** mientras se usa. Precisión "a nivel de cuadrante" | 🟡 Media. Deriva; sirve para izquierda/derecha/centro, no para un punto exacto. Con las sienes (Ch1-2, Ch7-8) puede mejorar lo que ellos hacen solo con la frente | **El Quest 3 no sigue los ojos.** Para Loving: "mirar" sin mover la cabeza |
| **Gestos de la cara** (sonrisa, mandíbula, cejas, ceño, guiño, beso) | Face Trainer: referencia promedio común (CAR), ventanas de 200 ms, 5 rasgos por canal (log RMS, log varianza, log longitud de línea, cambios de signo de pendiente, log RMS de alta frecuencia) = 40-D a 12 Hz; un clasificador logístico L2 + group-lasso por gesto (λ2 = 1, λg = 0,3); 6 repeticiones de 2 s; validación leave-one-rep-out; listo si ≥ 0,85. **Muestra qué electrodos importan** para cada gesto | 🟢 Alta para gestos marcados. Lo mejor valorado por MoguLive y UploadVR | Sonrisa suave, "soltar la cara", mandíbula como relajación medible |
| **Envolvente de artefactos** (mandíbula, cejas, ojos, cualquier músculo) | Ventana de 64 muestras (256 ms) → quitar media → quitar tendencia → rectificar → media móvil de 20 muestras (80 ms) = envolvente a 60 Hz. Umbral = base + 0,6·(pico − base), histéresis al 0,3; calibración: 5 s de base + 10 repeticiones + ranking de canales por SNR × consistencia × tasa de detección | 🟢 Alta. Es simple, rápido y robusto | La **tensión facial** continua (no solo el gesto): el ingrediente que le falta a la "calma" |
| **Bandas** δ θ α β γ (absolutas, relativas, dominante) | FFT 256 puntos, Hanning, ~12 Hz, por canal o promedio; log10(p + 1e-9) para que sea gaussiano | 🟡 Media. Frontales y contaminadas por ojos y músculos | Materia prima de todo índice lento |
| **"Relajación"** 0–1 | α relativa + θ/β, EMA, `calibrate()` por persona | 🟠 Baja-media sin occipital | Solo como ingrediente, nunca solo |
| **"Foco"** 0–1 | (β+γ)/(α+θ+δ) (otros lugares: β/(α+θ), β/(β+θ)) | 🔴 Baja: **sube con el músculo** | Descartar como "atención". Sirve para detectar esfuerzo/tensión |
| **Asimetría alfa frontal** (FAA) | ln(α der) − ln(α izq); relativo al propio promedio; ±0,05 como umbral heurístico | 🟡 Tenemos frente izq. (Ch3-4) y der. (Ch5-6) | Valencia aproximada (acercamiento vs retirada). Discutida en la literatura |
| **Pico de beta y recuperación** | β normalizada contra base móvil de ~30 s; "snap" cuando cae > 35 % en un tick | 🟡 | Medir cuánto tarda alguien en volver a la calma tras un estresor: **un dato de resultado honesto** para la obra |
| **Calma** α/(α+β) | EMA 0,18 a 10 Hz; base capturada en calibración (0 = base, 1 = doble) | 🟡 | Parecido al `/muse/calm` actual |
| **Calidad de cada electrodo** | RMS con semáforo; "LINE" (50/60 Hz) y SNR en dB; estados Good/Fair/Poor/Railed/No contact. **El chip no mide impedancia**; se juzga por señal | 🟢 | `sensor_active`, y guiar al público al ponérselo |
| **P300** | LDA con shrinkage + acumulación bayesiana sobre estímulos repetidos | 🔴 En campo: 0/4 | No encaja con una obra contemplativa |
| **Pulso** | No sale del EEG. Ellos lo sacan de la **webcam** (rPPG: POS, CHROM, GREEN; SDNN, RMSSD) | — | Para Recognizing seguir con Muse o una banda Polar H10; o la webcam si hay PC con cámara |

**Lo que esto cambia para Soul Charger:** la "calma" honesta con este sensor es **compuesta**: cara suelta (envolvente EMG baja en sienes y frente) + parpadeo lento + α/(α+β) frontal, cada ingrediente normalizado contra la base de esa persona en los primeros 20–30 s. Y la **mirada por EOG** abre una interacción que el Quest 3 no tiene.

---

## 3. Qué se puede optimizar

**Señal (lo que más pesa, según su propia guía de grabación en movimiento):**
- Máscara firme y pareja; referencia y bias (centro de la frente) con contacto. Es el factor número uno. Nuestro prototipo es para Quest 3S y calza mal en el Quest 3: Ch2, Ch4 y Ch6 salieron flojos.
- Alcohol en la piel; gel o suero "es lo más efectivo contra artefactos de movimiento".
- Cable corto y fijo a la correa; solo batería; lejos de cargadores.
- Pasa-banda 1–40 Hz + notch 50 Hz + Hampel (ventana 5, 3σ) en tiempo real. Rechazar las ventanas de movimientos grandes, no "rescatarlas".
- Esperar a que el filtro se asiente (2–3 s) y grabar 20–30 s de base quieto.

**Algoritmos:**
- **Calibrar siempre por persona**: su calibración de dos estados (REST 20 s / ACTIVE 20 s, Cohen's d) y su normalización contra base móvil (5 min para OSC, 10 s en Unity, 10 min en Agent). Nunca umbrales fijos.
- **Usar las sienes** (Ch1-2, Ch7-8) para el EOG horizontal, que ellos calculan solo con Fp1/Fp2. Debería dar más amplitud.
- **Referencia promedio común (CAR)** antes de clasificar gestos: cancela zumbido, movimiento y deriva de referencia.
- **Separar canales en grupos** (su `lsl_groups`: EEG frontal vs EOG/EMG sienes) y calcular bandas solo sobre los limpios.
- **Marcar eventos** (parpadeo, mandíbula) y excluir ±300 ms del cálculo de bandas: es la contaminación que ellos reconocen y no corrigen.

**Operación con público:**
- Un semáforo de contacto antes de empezar (su Contact Calibration tarda "unos segundos").
- Una calibración guiada de 40 s integrada a la narrativa (Hall).
- Un solo receptor BLE: la app es dueña del sensor; BodyPress y Cloud quedan fuera mientras corre.

---

## 4. Sus experimentos y pruebas de campo (referencia)

| Experimento | Qué hicieron | Qué aprendemos |
|---|---|---|
| **MoguLive, Tokio** (2 meses, noviembre 2026) | Probaron Spoon Bend, Neural Flight, Mind Reader, Face Trainer con el prototipo gris | Face Trainer "funcionó muy bien", incluso la boca. Spoon Bend funcionó "sin forzar". Neural Flight con lag y falsos. Mind Reader 0/4. "Pesado para sesiones largas." |
| **BeFootball, Madrid** | Señales neurales y fisiológicas de porteros entrenando en VR | Objetivo: integridad de señal con movimiento rápido de cabeza y cuerpo. Sin resultados publicados. Hay video en el Discord |
| **Avatar Foundation** (su estudio de neurofeedback) | Tres pipelines paralelos: espectral (12 Hz, 1 s), artefacto (60 Hz, 256 ms) e híbrido (AND, OR, MAX, secuencial). Cualquier electrodo → cualquier expresión, con "Links" entrenados | **Es la arquitectura que quiero para el Center**: fuentes × sinks con mapeos entrenados, y una tabla de "qué electrodo sirve para qué" descubierta en vez de prescrita |
| **Face Trainer v1/v2** | 8 gestos, 6 reps, LORO-CV, importancia por canal | Protocolo de entrenamiento de 1 minuto por gesto que podemos copiar tal cual |
| **Eye Track** | Ridge polinómico + aprendizaje en línea; guarda el modelo en localStorage | Calibración de 5 puntos (≈15 s) y el modelo sigue aprendiendo |
| **Glitching Reality** | Inestabilidad = (1 − calma) + 0,6·pico β − 0,15·FAA; aritmética mental como estresor adaptativo | Un estresor controlado y la **recuperación** como métrica |
| **Premeditatio Malorum** | Score = recuperación del pico β a la base tras escenas 360° | Idem: el resultado es "cuánto tardas en volver", no "qué tan calmado estás" |
| **Neural Maze Lock / Orb Control** | Compuertas: foco > 0,6 por 2 s, calma > 0,6 por 2 s, parpadeo confirma; miden **falsos disparos** | Métrica de confiabilidad de una interacción: falsos positivos por minuto. Y la regla: la mirada nunca dispara nada irreversible; el parpadeo confirma |
| **Aura (muñeca EMG)** | Concurso en Kaggle: gestos de mano sin calibrar, 120 equipos | No es nuestro sensor, pero muestra cómo arman un dataset público |

---

## 5. Sus juegos (36 experiencias) agrupados por lo que explotan

- **Parpadeo:** Penalty Shooters, Blink Browser, octoCaptcha (prueba de vida con conteo y coherencia espacial), marcas en BioPose.
- **Mirada EOG:** Eye Track, Orb Control, Neural Maze Lock.
- **Gestos EMG:** Face Trainer v1/v2, Hand Trainer (Aura), Silent Speech (vocabulario cerrado), octoAuth.
- **Bandas y calma:** Spoon Bend, Neural Flight, MindCast (velocidad de podcast), Room Buddy, Northern Lights (auroras δ/α/γ con sonido), Neural Sonification (bandas → capas musicales con escala, tonalidad, reverb), Neural Wave Space (VR), Premeditatio Malorum, Glitching Reality (FAA).
- **P300 / SSVEP:** Mind Reader, P300 Mini-Game.
- **Herramientas disfrazadas de juego:** Signal Lab (curso de DSP), Avatar Neurofeedback Studio, BioPose Recorder, benches de pupila y rPPG, Webhook Wizard, VRChat OSC.

**Patrón que se repite en todos:** calibrar primero, normalizar contra la propia base, suavizar con EMA (0,15–0,25), y **que siempre pase algo** (normalización por máximo móvil). Por eso sus demos "siempre funcionan" y por eso no distinguen cerebro de músculo. Nuestro Center tiene que mostrar las dos cosas por separado.

---

## 6. Comunidad

- **Discord** (≈ 1.000 miembros declarados; en la práctica Ildar, Youssef y pocos usuarios activos). Canales: `#pieeg-xr` (empezó el 25-09; precio y Kickstarter, video de porteros), `#virtual-reality` (BodyPress funciona con IronBCI y Octopus; "integración directa con la tienda de Meta, sin capa intermedia, pronto"), `#software` (releases: v0.52.0 el 3-11 con MOABB), `#signal-processing`, `#noise`, `#machine-learning`, `#llm-ai-agent`. **Youssef acepta PRs** a `dashboard/src/experiences`.
- **Terceros:** un usuario (eegGOD) hizo una "brain voice app" web que muestra una palabra cada 2 s. Nada más de la comunidad que nos sirva. Las 36 experiencias son del equipo.
- **Para nosotros:** el Discord es el canal de soporte, no una fuente. Si publicamos una experiencia en su galería, tenemos visibilidad en su Kickstarter.

---

## 7. Sus herramientas: qué reutilizar y qué no

| Pieza | Qué es | Licencia | Reutilizar |
|---|---|---|---|
| `PiEEG-server` (Python + dashboard React) | Adquisición (SPI/BLE/mock), pub-sub a WebSocket, CSV, OSC, LSL, webhooks; dashboard con todo | **MIT** | **Sí, como referencia**: `ironbci.py` (BLE), `osc_vrchat.py` (normalizador), `hooks/detectors/*`, `experiences/*`, `lib/montage.ts`, `components/TopoMap.tsx` |
| `pieeg.js` | SDK de navegador: Web Bluetooth, filtros (Hampel, pasa-banda, notch), FFT, bandas, índices | MIT | **Sí**: 1.300 líneas sin dependencias; base de nuestra capa de lectura |
| PiEEG Cloud | Lo mismo en la nube, sin instalar, más Live Lab, Buddy, Studio | Gratis con el equipo | Como laboratorio para probar ideas; no como base |
| Live Lab (Bio-Pen) | Pipeline JS a 15 Hz con `car`, `bandpower`, `lda`, `loroCV`, `check()` | — | Copiar la idea: un sandbox de script dentro del Center |
| PiEEG Studio | MNE-Python en el navegador: ICA, notch auto, FAA, conectividad, exporta `.py`/`.ipynb`/`.fif` | MIT (parte del server) | **Sí, para análisis offline**: el Center exporta en su formato y lo abre |
| Local Bridge (Rust) | Cloud → OSC con direcciones `/pieeg/*` | MIT | No hace falta: el Center emite OSC directo |
| PiEEG-agent / Buddy | LLM que lee resúmenes (nunca la onda) a 1 Hz; entrena patrones por conversación | MIT | Más adelante: un "Alma analista" sobre las sesiones |
| Plugin Unity | WebSocket → bandas normalizadas con máximo móvil de 10 s | MIT | Solo como referencia de contrato |
| BodyPress | App Flutter para Quest/Android; BLE directo; no exporta | MIT | Referencia de BLE en Android si algún día va dentro del APK |
| `pieeg-core` | Acelerador Rust | **AGPL-3.0** | **No** dentro de nuestra app |
| Hardware | Planos no publicados; firmware solo `.hex` | — | Comprar IronBCI; máscara propia |

---

## 8. Plan: EEG Alma Center

### 8.1 Por qué construirlo (y no usar lo de ellos)
- Lo de ellos está repartido en 8 apps y ninguna hace lo que necesitamos: **una fuente de verdad** para recibir, calibrar, ver, grabar y enviar, con un **router libre** de señal → salida.
- Su OSC solo manda bandas; sus detectores viven en React dentro del navegador y no salen por ningún puerto.
- Queremos otra estética (la de VEATION), otro idioma de uso (una persona con público, no un desarrollador) y nuestros índices.
- Y queremos centralizar **más de un sensor**: PiEEG hoy, Muse (calma, pulso) y una banda de pecho mañana.

### 8.2 Qué es
Una app de escritorio (Windows primero) con cinco capas:

```
FUENTES          →  MOTOR                 →  VISTAS                →  SALIDAS
PiEEG XR (BLE)      filtros (Hampel,          osciloscopio 8 ch         OSC (N destinos, mapeo libre)
Muse (OSC/LSL)      pasa-banda, notch)        espectro + bandas         WebSocket JSON
Polar H10 (BLE HR)  bandas, EOG, EMG,         cabeza 3D (XR Face)       grabación CSV/JSON + marcas
simulador           parpadeo, calma           calidad de contacto       export a Studio/MNE
                    calibración por persona   sesiones y comparación    (LSL opcional)
                    router de mapeos          protocolos guiados
```

### 8.3 Stack recomendado
- **Electron** (igual que VEATION; el equipo ya lo empaqueta) + **TypeScript**.
- **Bluetooth en el renderer con Web Bluetooth** (Chromium lo trae; Electron solo necesita el handler `select-bluetooth-device`). El protocolo es el documentado y lo probamos con `bleak`.
- **DSP en un Web Worker** en TypeScript, portando `pieeg.js` y los hooks MIT. Un solo lenguaje, sin Python en el paquete.
- **OSC, UDP, WebSocket y archivos en el proceso principal** (Node `dgram`, `ws`, `fs`).
- **Vistas en Canvas 2D** (ondas a 60 fps, como ellos) y **Three.js** para la cabeza.
- **Diseño:** `tokens.css` del sistema VEATION (gris `#111111`, Geist 400/600, ámbar `#E5B567` solo como punto, líneas de 1 px, nada de tarjetas redondeadas ni iconos genéricos). Textos en inglés, como VEATION.
- **Plan B** si Web Bluetooth en Electron diera problemas en Windows: la sonda Python que ya tenemos como servicio local por WebSocket. Costaría empaquetar dos runtimes.

### 8.4 Fases (dentro del mes del préstamo)

| Fase | Días | Entrega | Criterio de hecho |
|---|---|---|---|
| **F0 · Ver** | 2–3 | Esqueleto Electron con tokens VEATION; conectar al `PiEEG_XR`; osciloscopio de 8 canales; semáforo de contacto por canal; grabar CSV con marcas (tecla M) | Veo la señal en la app con la máscara puesta, con los colores de VEATION |
| **F1 · Limpiar y entender** | 3–4 | Hampel + pasa-banda + notch en vivo; espectro y barras de bandas; **cabeza 3D con el montaje XR Face** (8 electrodos + ref + bias) coloreada por calidad o por banda; simulador para trabajar sin sensor; lista de sesiones y reproducción | Comparo en vivo crudo vs limpio; la cabeza muestra qué electrodo falla |
| **F2 · Detectar y calibrar** | 5–7 | Parpadeo (umbral adaptativo), mirada EOG (ridge + 5 puntos), envolvente EMG por canal, calma compuesta; **calibración guiada de 40 s** por persona (REST/ACTIVE, Cohen's d) con informe de qué electrodo sirve; evento vs continuo separados | Con tres personas distintas: parpadeo > 95 %, mirada izq/der > 90 %, mandíbula > 95 %, sin falsos por minuto en reposo |
| **F3 · Enviar** | 3–4 | **Router de mapeos**: cualquier señal → dirección OSC, rango, suavizado, host:puerto; perfiles guardados (BioHub con el contrato Muse `/muse/*`, TouchDesigner `/pieeg/*`, VRChat, Ableton/Max); WebSocket JSON; test "enviar valor de prueba" | El `BP_BioHub` del APK recibe calma, `sensor_active` y mirada sin tocar Unreal |
| **F4 · Experimentar** | 5–7 | Protocolos guiados con marcas automáticas: ojos abiertos/cerrados ×3, parpadeos 4-3-2-1, mirada, mandíbula, aritmética mental/descanso; **comparación de sesiones** (Cohen's d, recuperación del pico β); export `.csv` + `.json` de features y abrir en PiEEG Studio | Puedo responder con datos "¿qué mide de verdad este sensor en esta persona?" |
| **F5 · Centralizar** | después | Muse por OSC/LSL como segunda fuente; Polar H10 por BLE (estándar Heart Rate); un solo reloj y una sola grabación | Recognizing con pulso real y Loving con mirada, desde la misma app |

### 8.5 Lo que NO hago al principio
- Nada de LLM/agente hasta tener datos.
- Nada de P300/SSVEP.
- Nada dentro del APK: la app vive en el PC, el Quest recibe OSC. El Bluetooth dentro de Unreal queda para cuando los índices estén validados.
- Nada de acelerador Rust (AGPL).

### 8.6 Riesgos
- **Web Bluetooth en Electron/Windows**: probar el día 1; si no, plan B.
- **La máscara del 3S en el Quest 3**: tres canales flojos. Pedir la de Quest 3 a Ildar; mientras, gel.
- **Una sola conexión BLE**: la app tiene que soltar el sensor limpiamente al cerrar.
- **Red en feria**: router propio, IP fija para el Quest.
- **Datos de público**: definir desde el día 1 qué se guarda (sesiones anónimas, sin nombres) y dónde.

---

## 9. Preguntas para Beltrán

1. **Stack:** ¿Electron solo (TypeScript, Web Bluetooth) o Python de fondo + Electron de cara? Recomiendo Electron solo; el plan B es la sonda Python.
2. **Fuentes desde el inicio:** ¿solo PiEEG, o Muse (que ya manda OSC) también en F0 para que la app sea el centro desde el día uno?
3. **Destinos prioritarios además de Unreal:** ¿TouchDesigner, Ableton/Max, Resolume, web, otro? Cambia qué perfiles OSC vienen de fábrica.
4. **Fecha objetivo:** ¿GITEX (4–12 dic) con PiEEG en el stand, o el Center es para el laboratorio y GITEX va con Muse?
5. **Dónde vive el código:** ¿repo propio `EEG-Alma-Center` (recomendado: es una herramienta, no es la obra) o carpeta dentro de `VR Unreal`?
6. **Idioma de la interfaz:** inglés como VEATION, ¿sí?
7. **Público:** ¿grabamos sesiones de visitantes? Si sí, anónimas y con un aviso; define qué se guarda.
8. **Contribuir a PiEEG:** si una experiencia nuestra queda bien, ¿la publicamos en su galería (visibilidad en su Kickstarter) o la guardamos?

---

## 10. Fuentes

- Doc: https://docs.pieeg.com (PiEEG XR: setup, connections, software, Specification, Service, FQA, examples, Application; software: features/detectors, dashboard, experiences, studio, biopose; api/javascript-sdk, websocket, data-format; integrations: vrchat-osc, lsl, unity, pieeg-chrome, pieeg-agent, notebooks, pieeg-core; cloud: live-lab, buddy, local-bridge; hardware/signal-quality: noise-elimination, Calibration; software/reference/architecture)
- Web: pieeg.com/news (pieeg-xr-launch, pieeg-xr-kickstarter-november-23-launch, pieeg-xr-mogulive-independent-review, hello-world-octopus-16, pieeg-xr-pico-compatibility), pieeg.com/tutorials (run-pieeg-xr-meta-quest, brain-reactive-vrchat-avatar, neural-stream-touchdesigner-osc, ble-quest-chromium-pieeg-xr), xr.pieeg.com
- GitHub pieeg-club: PiEEG-server (código leído: hooks/detectors, experiences/*, lib/montage.ts, lib/ironbciBle.ts, pieeg_server/ironbci.py, osc_vrchat.py, pieeg.js), PiEEG_XR_Hardware, ironbci, bioIDE, PiEEG-unity, PiEEG-chrome, PiEEG-agent, PiEEG-local-bridge, hello_world_octopus_16, bodyPress-flutter
- Prensa: MoguLive (moguravr.com/pieeg-xr-review), UploadVR, Road to VR, Hackaday.io 205794
- Discord PiEEG: #pieeg-xr, #virtual-reality, #software (leídos el 2026-11-14)
- Correos de Ildar (07-10, 07-11, 10-11): doc XR, noise-elimination, MoguLive
- Diseño: `Immersive Studio Pro/docs/lanzamiento/DISENO.md` y `sistema-diseno/` (tokens.css, README)
