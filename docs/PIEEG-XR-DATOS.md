# PiEEG XR: qué datos da y qué herramientas trae su software

> Investigación del 2026-11-07, según la documentación oficial (docs.pieeg.com) y la primera grabación con el casco puesto.
> El arranque (instalar, conectar, probar) está en [`PIEEG-XR-ARRANQUE.md`](PIEEG-XR-ARRANQUE.md).

---

## 1. Lo que entrega el sensor: solo la señal cruda

- **8 canales** en µV, a **~250 muestras/s** (medimos 247–248), en la frente y las sienes.
- No trae acelerómetro: el que tiene IMU es otro producto, el Aura VR. Tampoco está claro si manda la impedancia de los electrodos.
- **Todo lo demás se calcula** a partir de esas 8 ondas: con su software o con el nuestro.

---

## 2. Qué se puede extraer

| Qué | Cómo lo calculan | Dónde ya está hecho | ¿Qué tan confiable en el XR? |
|---|---|---|---|
| **Parpadeos** (evento + cuenta + amplitud) | `useBlink`: pico a pico en ventanas de 100 ms; umbral adaptativo (mediana + MAD de ~3 s, mínimo 25 µV); dura 60–600 ms; 300 ms de refractario | Panel y Cloud; Studio; juegos *Penalty Shooters* y *Blink Browser* | 🟢 **Alta.** Se vieron en la primera prueba (Ch1, Ch3, Ch8). La doc avisa que la mandíbula y los movimientos de cabeza dan falsos positivos |
| **Mirada izquierda / derecha** (EOG) | Diferencia entre lados (horizontal) y modo común (vertical), con regresión ridge y calibración de 5 puntos | Experiencia **Eye Track** (Cloud); gates de mirada en *Neural Maze Lock* y *Orb Control* | 🟡 **Media.** Deriva y necesita calibrar. Con electrodos en las sienes es mejor que solo con la frente. **El Quest 3 no tiene seguimiento ocular** |
| **Gestos faciales** (sonrisa, ceño, mandíbula…) (EMG) | **Face Trainer**: clasificador lineal (L2 + group-lasso) entrenado con tus repeticiones (3-2-1) | Cloud → Mini-Games → Face Trainer | 🟢 **Alta para gestos marcados.** Hay que entrenarlo con cada persona |
| **Bandas EEG** (delta, theta, alfa, beta, gamma: absolutas, relativas, frecuencia dominante) | FFT de 256 puntos (ventana de Hanning) | Todo: panel, server, Unity, OSC | 🟡 **Media.** Son frontales y se contaminan con ojos y músculos; hay que limpiarlas |
| **"Relajación"** 0–1 | `useRelax`: alfa relativa + theta/beta, con `calibrate()` por persona | Panel y Cloud | 🟠 **Baja-media.** Mide sobre todo el alfa de ojos cerrados, que es occipital. Esta máscara no llega ahí |
| **"Foco"** 0–1 | `useFocus`: (β+γ)/(α+θ+δ), calibrable | Panel y Cloud, Unity (`EEG_Focus_Ratio` = β/(α+θ)), *Neural Flight*, *MindCast* | 🔴 **Baja.** **Sube con la tensión de la cara.** La doc misma dice que no es atención |
| **Asimetría alfa frontal** (FAA = ln αder − ln αizq) | Compara el alfa de la frente izquierda con el de la derecha | Studio; experiencia *The Glitching Reality* | 🟡 Tenemos frente izquierda y derecha, así que se puede. Se asocia a valencia emocional, pero es un tema discutido |
| **Calidad de cada canal** | Panel: RMS con semáforo. Studio: desviación, pico a pico, % de red, curtosis, Hjorth, flags de plano o ruidoso | Panel y Studio | 🟢 Sirve para el `sensor_active` de la obra |
| **P300** (respuesta a un estímulo esperado) | LDA con acumulación bayesiana | *Mind Reader*, *P300 Mini-Game* | Necesita estímulos repetidos; no encaja con la obra |
| **Pulso** | No sale del EEG. Su *Optical Physiological Bench* lo saca de la **webcam** (rPPG) | Cloud | En nuestra prueba el pulso **apareció como artefacto** en los canales con mal contacto. Es una curiosidad, no un dato |

---

## 3. Qué hace cada herramienta de ellos

### PiEEG Cloud (navegador: https://cloud.pieeg.com)
- Todo corre **dentro del navegador**: la onda cruda no sale del PC salvo que la compartas. Es gratis con los equipos PiEEG.
- Ofrece:
  - panel en vivo, espectrograma y mapa de la cabeza con montaje **"XR Face"**;
  - los detectores de §2;
  - **36 experiencias** (Face Trainer, Eye Track, *Northern Lights*, *Neural Sonification*…);
  - **Live Lab**: un pipeline programable en JavaScript a 15 Hz, para probar ideas de detección sin instalar nada;
  - **Buddy**, un asistente de IA que solo recibe resúmenes numéricos, nunca la onda;
  - **Local Bridge**, que reenvía a OSC.

### PiEEG Server (ya instalado en este PC, v0.52.0)
- **WebSocket** en `:1616`: un JSON por muestra (`t`, `n`, `channels` en µV).
- **Filtros:** pasa-banda (1–40 Hz por defecto, con `--filter`) y **Hampel** contra picos (activo por defecto).
- **Grabación** a CSV.
- **OSC:** las **5 bandas** normalizadas de 0 a 1, cada 0,25 s, o **por región** (`EEG_{Region}_{Band}`) agrupando canales.
- **LSL**, para OpenViBE, MNE, etc.
- **Webhooks:** disparan cuando una banda, una amplitud o una razón de bandas cruza un umbral. Se evalúan cada 1 s, con enfriamiento.
- ⚠ Los detectores de parpadeo, relajación y foco viven en el **panel del navegador** (son hooks de React). El OSC del server manda **solo bandas**.

### PiEEG Studio (análisis offline, MNE-Python)
- Se instala con `pip install "pieeg-server[studio]"` y se abre en `127.0.0.1:1618`. Es **la mesa de análisis** para nuestras grabaciones.
- **Limpieza:** offset y deriva, Hampel, **notch automático** con armónicos, pasa-banda FIR o IIR, re-referencia, **ICA con sugerencia de componentes oculares**.
- **Detección:** parpadeos y segmentos con músculo (`BAD_muscle`) o picos (`BAD_peak`).
- **Análisis:**
  - espectro;
  - bandas y razones (θ/β, α/θ, β/(α+θ));
  - frecuencia alfa individual, entropía espectral, pendiente 1/f;
  - **FAA**;
  - conectividad;
  - ERP;
  - calidad por canal.
- **Exporta** xlsx, fif, edf, informe html, **script `.py` o notebook** que reproduce todo, y **json de features** para aprendizaje automático.

### BodyPress (app de Quest y Android; código en github.com/the-governor-hq/bodyPress-flutter, MIT)
- Es una **app**, no un plugin. Está hecha en Flutter y se conecta por Bluetooth **directo** al PiEEG XR desde el Quest. Muestra la onda, el espectro, la decodificación y la calidad de señal.
- Tiene un "sistema de plugins", pero es **para sumar sensores a BodyPress** (`BleSourceProvider`), no para sacar datos.
- **No manda datos a otras apps**: según la doc y el README, no hay OSC, UDP, WebSocket ni LSL.
- Sirve como **referencia de código (MIT)**: prueba que el Bluetooth del PiEEG funciona dentro de Android/Quest.

### Plugin de Unity (`com.pieeg.unity`, MIT)
- Lee el WebSocket del server. Expone las bandas y `EEG_Focus_Ratio`, normalizadas de 0 a 1 con el máximo móvil de 10 s.
- No hay nada para Unreal, pero su matemática (FFT → bandas → normalización móvil) es la referencia para hacer lo mismo.

### pieeg-core (Rust)
- Solo acelera la decodificación, el filtro y el Hampel.
- ⚠ Licencia **AGPL-3.0**: no meterlo dentro de la obra sin revisar la licencia. El server y el plugin de Unity son MIT.

---

## 4. Lo que esto sugiere para Soul Charger (para conversar, nada decidido)

- **Lo fuerte de este sensor no es la "calma" EEG pura**, sino:
  - los **parpadeos**;
  - la **mirada izquierda/derecha**;
  - la **tensión de la cara**.
  Las tres señales son grandes, claras y salen bien con electrodos en la frente.
- **Una "calma" compuesta sería más honesta** que copiar `useRelax`:
  - cara suelta (poco EMG en las sienes);
  - parpadeo lento;
  - alfa/theta frontal relativa;
  - todo calibrado por persona en los primeros segundos, como hace su `calibrate()`.
- **La mirada por EOG** podría alimentar Loving ("observar para activar") en un visor sin seguimiento ocular.
- **Camino técnico:** server o script propio → OSC al `BP_BioHub`, igual que el Muse. Los dos son MIT.

## 5. ¿Se puede armar uno propio? (investigado el 2026-11-07)

**Qué hay dentro de la caja:** casi seguro una placa **IronBCI**, también de PiEEG: TI ADS1299 + STM32 + Bluetooth LE. El XR usa "el mismo protocolo que el IronBCI", y el server la lee como `--device ironbci8`.

| Opción | Precio aprox. | Qué es | Pros | Contras |
|---|---|---|---|---|
| **IronBCI** (PiEEG) | **US$299** el kit (placa + caja + cable + fuente + 8 electrodos secos) según PiEEG; **US$420** en Elecrow, sin batería ni electrodos | La misma placa del XR, suelta | Mismo protocolo: **nuestra sonda y su software funcionan igual**. Batería LiPo propia, electrodos por header de 2,54 mm | Los archivos de hardware (esquema, PCB) y el código del firmware **no están publicados**: solo el software, la app y el SDK |
| **OpenBCI Cyton** | US$999–1.249 (el precio varía según la página de la tienda) | El estándar abierto de investigación, también con ADS1299 | **Hardware abierto de verdad** (esquemas publicados), maduro y con mucha comunidad | Caro; usa un dongle USB al PC, no habla Bluetooth directo con el Quest |
| **Cerelog ESP-EEG** | ~US$350 en oferta (lista US$650, agosto 2026) | ADS1299 + ESP32, firmware y esquemas en GitHub | Barato y abierto | A mayo de 2026 **solo USB** (sin aislamiento: no se puede llevar puesto conectado al PC) y sin Bluetooth; el esquema sería solo para uso no comercial |
| **Placa propia** con ADS1299 | El chip cuesta decenas de dólares | Diseñar el PCB y el firmware | Control total | Meses de trabajo: diseño analógico de bajo ruido, seguridad eléctrica, firmware. No conviene |

**Electrodos secos de Ag/AgCl:**
- desde ~US$1 cada uno (discos descartables en packs de 50)
- hasta US$10–30 cada uno (reutilizables)
- PiEEG también vende electrodos y gorros.

**Lo que concluimos:**
- **"Open source" en PiEEG quiere decir, sobre todo, el software y el protocolo** (MIT). No están los planos de la placa.
- Para Soul Charger tampoco hacen falta los planos. El camino realista es:
  - **placa IronBCI** (comprada a PiEEG);
  - **una máscara propia para el Quest 3**, diseñada en Blender e impresa, con electrodos secos y un cable corto;
  - **nuestro software** (la sonda, y después el cálculo de la calma).
- Lo ideal es conversarlo con Ildar: venta de placas sueltas, versión para Quest 3, o codesarrollo.
- 🔴 Sea cual sea la opción: **con batería mientras alguien la tiene puesta**. Ninguna de estas placas tiene aislamiento eléctrico, y ninguna es un dispositivo médico. Con público en una feria, eso es responsabilidad nuestra.

## 6. Lo que no sabemos todavía

- Si los detectores pueden salir por WebSocket u OSC, o solo viven en el panel.
- Si la caja manda impedancia o electrodo suelto.
- Si el orden de los canales del prototipo es el de la doc.
- El paper del PiEEG XR (preprints.org) no se pudo leer: el sitio devuelve 403.
