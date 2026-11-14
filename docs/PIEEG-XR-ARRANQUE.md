# PiEEG XR: guía de arranque

> Investigación del 2026-11-07, el día que llegó el prototipo que mandó Ildar Rakhmatulin.
> El objetivo de esta etapa es **hacerlo funcionar, ver la señal, medirla y explorar qué se puede extraer**.
> La integración en Soul Charger viene después (§8).

---

## 1. Qué es lo que llegó

- **Máscara facial** que reemplaza la interfaz de cara del Quest 3. Tiene **10 electrodos secos de Ag/AgCl**: 8 canales, una referencia y un bias, todos en la frente y las sienes.
- **Caja BCI** (la redonda gris impresa en 3D), que va en la correa. Se conecta a la máscara por un cable.
  - Adentro hay un **TI ADS1299** (24 bits, **250 muestras/s**, ruido de 1 µV pico a pico) y un **STM32WB** que transmite por **Bluetooth LE 5**. La doc dice que se anuncia como `PiEEG XR`; **nuestro prototipo se anuncia como `PiEEG_XR`**, con guion bajo (dirección `00:80:E1:26:6F:C3`).
- **No necesita SDK propietario.** Usa el mismo protocolo Bluetooth que el IronBCI (§6).
- **Es un prototipo hecho a mano.** La máscara de la foto parece una pieza rígida impresa con discos metálicos; la de serie es de silicona. Ildar avisó que puede haber problemas de alimentación.
- Es un equipo **de investigación**, no un dispositivo médico.

### Mapa de electrodos

| Posición en la máscara | Canal | Qué capta mejor |
|---|---|---|
| Sien izquierda (abajo, arriba) | Ch1, Ch2 | Movimiento de ojos, mandíbula, músculos de la sien |
| Frente izquierda | Ch3, Ch4 | EEG frontal, parpadeos |
| Centro de la frente | Ref (centro izq.), Bias (centro der.) | Punto de 0 µV y cancelación de ruido de la red |
| Frente derecha | Ch5, Ch6 | EEG frontal, parpadeos |
| Sien derecha (arriba, abajo) | Ch7, Ch8 | Movimiento de ojos, mandíbula, músculos de la sien |

🔴 **Todo está adelante.** Sirve muy bien para parpadeos, movimiento de ojos, gestos faciales y EEG frontal. **El alfa con ojos cerrados (occipital) no se mide**: necesita electrodos en la nuca, y eso solo lo trae la versión académica.

---

## 2. Energía: lo primero que puede fallar

- **Lo que recomienda Ildar para este prototipo:** alimentarla **desde el Quest**, con un **cable USB solo de carga** (sin líneas de datos).
- **Lo que dice la doc de serie:** 5 V por USB-C desde un power bank o una correa con batería, con un cable **USB-A → USB-C**. Algunas fuentes USB-C → USB-C no la encienden.
- 🔴 **Nunca** usar un cargador de pared ni un PC enchufado a la red mientras alguien la tiene puesta: no tiene aislamiento.
- **Señal de vida:** un LED dentro de la caja. Si no se ve en el Bluetooth, casi siempre es la alimentación: probar otro cable u otra batería, o desenchufar y volver a enchufar.
- Si se alimenta desde el Quest, descarga la batería del visor.

**Probado el 2026-11-07:**
- Con un cable USB-C a USB-C desde el Quest **no encendió**.
- Enchufada al USB del PC, **sí encendió** (sin nadie que la tuviera puesta).
- Probablemente el prototipo no tiene las resistencias que le piden a una fuente USB-C que entregue energía.
- Para llevarla puesta hay dos opciones:
  - **power bank + cable USB-A → USB-C**, o
  - desde el Quest con un **adaptador OTG (USB-C macho → USB-A hembra) + cable USB-A → USB-C**. El adaptador es el que hace que el Quest entregue energía. Falta probarlo.

---

## 3. Qué instalar: tres caminos, de menos a más

| Camino | Dónde corre | Qué hay que instalar | Para qué sirve |
|---|---|---|---|
| **A · PiEEG Cloud** | Chrome o Edge en el PC | **Nada** | Ver la señal en vivo, test de parpadeo y mandíbula, filtros, guardar datos, Face Trainer (gestos) |
| **B · BodyPress** | El Quest 3 (o un Android) | La app de la Meta Quest Store | Ver la señal **dentro del visor** sin PC: onda, espectro (FFT), estado neural, calidad de señal |
| **C · PiEEG Server** | El PC, en Python | `pip install "pieeg-server[ironbci]"` | **Medir en serio**: grabar CSV, recibir cada muestra por WebSocket, LSL, OSC, panel en `localhost:1617` |

**Este PC ya tiene todo lo necesario** (revisado el 2026-11-07): Python 3.12 (y 3.10), Bluetooth LE funcionando, Chrome, Edge y adb.

🔴 **Una sola conexión Bluetooth a la vez.** Si BodyPress está conectado, el PC no ve la caja, y al revés. Hay que cerrar uno para usar el otro.

### A · PiEEG Cloud (la primera prueba)
1. Abrir **https://cloud.pieeg.com** en Chrome o Edge (Firefox no tiene Web Bluetooth).
2. Ir a **Session Lobby**, pestaña **PiEEG Devices**, y elegir **PiEEG XR** (8 canales) o **PiEEG XR-16**.
3. En la ventana de Bluetooth del navegador, elegir `PiEEG XR`.
4. Extra: **Mini-Games → Face Trainer** prueba el reconocimiento de gestos.

### B · BodyPress en el Quest
1. Instalarla desde la Meta Quest Store: https://www.meta.com/experiences/bodypress/1271355469389420/ (no hace falta modo desarrollador).
2. Abrirla, ir a **Live Signal** y emparejar `PiEEG XR`.
3. Se puede fijar como ventana flotante para ver la señal al lado de otra app.

### C · PiEEG Server (en el PC)
Conviene un entorno aparte, fuera del repo:
```powershell
py -3.12 -m venv $HOME\pieeg-venv
& $HOME\pieeg-venv\Scripts\python.exe -m pip install "pieeg-server[ironbci,lsl]"
& $HOME\pieeg-venv\Scripts\pieeg-server.exe doctor        # diagnóstico
& $HOME\pieeg-venv\Scripts\pieeg-server.exe --mock        # panel con datos falsos, sin sensor
& $HOME\pieeg-venv\Scripts\pieeg-server.exe --device ironbci8 --ble-name "PiEEG_XR" --filter
```
Después se abre el panel en **http://localhost:1617**.

⚠ **Windows: el Bluetooth funciona.** La sonda con `bleak` conectó y recibió datos el 2026-11-07. **Falta probar el server.** La doc del XR y el tutorial de Quest dicen que el server corre en Windows con Bluetooth. El README del repo y PyPI dicen que en Windows **solo funciona `--mock`**. Hay que probarlo. Si falla, hay dos salidas:
- un script propio en Python con `bleak` (el protocolo está documentado, §6, y son pocas líneas), o
- correr el server en otro equipo con Linux o Mac.

El server lee **8 canales** (`ironbci8`). Si el prototipo resulta ser de 16, hay que usar el camino A.

### Sonda propia: `tools/pieeg/sonda_pieeg.py`
Es un diagnóstico rápido desde el PC que no depende del server. Usa el entorno `$HOME\pieeg-venv`, que tiene `bleak`.
```powershell
& $HOME\pieeg-venv\Scripts\python.exe tools\pieeg\sonda_pieeg.py              # ¿la caja está emitiendo?
& $HOME\pieeg-venv\Scripts\python.exe tools\pieeg\sonda_pieeg.py leer         # 10 s: muestras/s y contacto de cada canal
& $HOME\pieeg-venv\Scripts\python.exe tools\pieeg\sonda_pieeg.py leer --segundos 60 --csv   # graba en $HOME\pieeg-datos
```
- Muestra los servicios y características que anuncia la caja. Si el prototipo no usa el protocolo documentado, se ve ahí.
- Por canal da tres datos: el offset, la "variación" (la señal sin la deriva lenta) y un veredicto: plano, saturado, muy ruidoso o con señal.

---

## 4. Primera prueba, en orden

1. **Encender** (cable desde el Quest o power bank) y buscar el LED.
2. **Limpiar** la frente y las sienes con alcohol, dejar secar y limpiar los electrodos.
3. **Colocar** la máscara y apretar la correa firme y parejo: el contacto es lo que más pesa en la calidad.
4. **Conectar:** con BodyPress si estás solo en el visor, o con PiEEG Cloud si alguien mira la pantalla del PC.
5. **Quedarse quieto 5 a 10 s**, con la cara relajada, mientras se asienta el filtro.
6. **Checklist de señal:**
   - **Todos los canales se mueven suave.** Una línea **plana** = ese electrodo no toca.
   - **Parpadear fuerte 3 a 5 veces** → picos grandes, más fuertes en la frente (Ch3 a Ch6).
   - **Mirar a la izquierda y después a la derecha** → ondas lentas en sentidos opuestos en las sienes (Ch1-2 contra Ch7-8).
   - **Apretar la mandíbula** → ráfaga de alta frecuencia que se corta al soltar.

### Diagnóstico rápido

| Síntoma | Causa | Qué hacer |
|---|---|---|
| Un canal plano | Ese electrodo no toca | Reacomodar la máscara, apretar, un poco de gel o suero |
| Todo pegado arriba o abajo | La **referencia** (centro de la frente) perdió contacto | Reacomodar la máscara |
| Todos los canales iguales | Problema de referencia o bias | Revisar los dos contactos del centro |
| Banda gruesa y peluda en todos | Zumbido de la red eléctrica (50 o 60 Hz) | Solo batería, alejarse de cargadores, activar el filtro notch |
| Los parpadeos no aparecen | La frente no toca | Limpiar la piel y ajustar la máscara |
| Se ve pero no conecta o no llegan datos | Firmware | §7 |
| Se corta la conexión | Distancia u otra app Bluetooth | Acercarse (≈5 m como máximo) y cerrar otras apps |

### Para bajar el ruido (de la guía de ruido)
- Solo batería. Lejos de PCs, routers, teléfonos y zapatillas eléctricas.
- No tocar los electrodos con los dedos durante la prueba (mete zumbido).
- Pies aislados del piso; no sentarse en una banqueta metálica.
- Gel o suero bajan la impedancia de los electrodos secos.
- Quieto: el movimiento genera artefactos.
- Exportar a planilla y cruzar los picos con lo que pasó (te moviste, tocaste el cable).

---

## 5. Medir y grabar (camino C)

| Qué | Cómo |
|---|---|
| **Grabar** | `pieeg-server record sesion.csv --device ironbci8 --ble-name "PiEEG_XR" --duration 120` → CSV con `timestamp, ch1 … ch8` en µV |
| **Cada muestra en vivo** | WebSocket `ws://localhost:1616`: un JSON por muestra, a 250 Hz: `{"t": 1711234567.123, "n": 42, "channels": [ …8 valores en µV… ]}` |
| **Bandas por OSC** | `--osc --osc-host <IP> --osc-port <puerto>` → 5 floats de 0 a 1 cada 0,25 s: `/avatar/parameters/EEG_Delta`, `_Theta`, `_Alpha`, `_Beta`, `_Gamma` |
| **LSL** | `--lsl` → stream `PiEEG` (para OpenViBE, MNE, etc.) |
| **Análisis offline** | `pip install "pieeg-server[studio]"` y después `pieeg-server studio sesion.csv` (MNE-Python en el puerto 1618) |
| **Datos de ejemplo** | `Datasets/` del repo de hardware: test de parpadeo 4-3-2-1, crudo y filtrado 1-40 Hz |

Bandas del server: delta 0,5–4 · theta 4–8 · alfa 8–13 · beta 13–30 · gamma 30–100 Hz (FFT de 256 puntos, ventana de Hanning).

---

## 6. El protocolo Bluetooth (para el plan B y para el futuro)

- Nombre: `PiEEG XR` según la doc; **`PiEEG_XR` en nuestro prototipo**. **No hace falta emparejar**: se conecta y se suscribe a las notificaciones.
- Característica de datos (notify): `0000fe42-8e22-4541-9d4c-21edae82ed19`.
- **Comprobado en el prototipo (2026-11-07):**
  - servicio `0000fe40-cc7a-482a-984a-7f2ed5b3e58f` (distinto del que figura en la doc del IronBCI), con dos características:
    - `…fe42…` · notify: los datos;
    - `0000fe41-8e22-4541-9d4c-21edae82ed19` · write-without-response y read: ¿comandos? Hay que preguntarle a Ildar.
  - Notificaciones de **120 bytes = 5 muestras**: 500 notificaciones en 10 s, **247 muestras/s**.
  - Llegan sin mandar ningún comando.
- **24 bytes por muestra**: 8 canales × 3 bytes, enteros de 24 bits big-endian en complemento a 2. Una notificación puede traer una o varias muestras seguidas.
- Conversión a µV:
  ```python
  raw = (b[0] << 16) | (b[1] << 8) | b[2]
  if raw & 0x800000:
      raw -= 1 << 24          # la página del IronBCI dice 16777214: es un error
  uV = raw * 4.5 / 16777215 * 1e6   # ≈ 0,268 µV por cuenta
  ```
- Lo crudo trae un **offset de DC grande** (miles de µV) por el contacto. Es normal: se filtra con un pasa-banda (1–40 Hz) antes de analizar.

---

## 7. Firmware (solo si no conecta)

- El kit trae un **ST-Link V2** con cables. Se instala **STM32CubeProgrammer** (gratis, de ST) y se baja el último `.hex` de `PiEEG_XR_Hardware/Firmware/hex`.
- Se abre la caja y se conecta el header SWD de 4 pines: GND, RST, SWDIO, SWCLK. En el programa: **ST-LINK → Connect**, se abre el `.hex`, **Download**, y se desenchufa la alimentación unos segundos.
- 🔴 **Con la máscara fuera de la cara.** Y **no tocar el panel FUS** (stack Bluetooth) salvo que lo pida soporte: una dirección equivocada deja la radio inservible.
- Video: https://youtu.be/zU82j_DZxko

---

## 8. Qué se puede extraer (para explorar, nada decidido)

> El detalle completo, con lo que trae su software para filtrar y extraer cada cosa, está en [`PIEEG-XR-DATOS.md`](PIEEG-XR-DATOS.md).

| Señal | De dónde | Idea para Soul Charger |
|---|---|---|
| **Parpadeos** (EOG) | Frente, Ch3–6 | Evento claro y confiable. La frecuencia de parpadeo baja con la calma |
| **Ojos a izquierda o derecha** (EOG) | Sienes, Ch1-2 contra Ch7-8 | El Quest 3 **no tiene seguimiento ocular**: esto daría una dirección aproximada de la mirada. Interesante para Loving ("observar para activar") |
| **Tensión facial**: mandíbula, ceño, sonrisa (EMG, alta frecuencia) | Sienes y frente | "Soltar la cara" es una relajación medible y difícil de fingir |
| **Bandas EEG frontales** (alfa, theta, beta) | Frente, Ch3–6 | Índice de calma o atención, parecido al `/muse/calm` de hoy |
| **Gestos** (Face Trainer) | Toda la máscara | Sonrisa y otras expresiones |

⚠ Los ojos, la boca y la mandíbula **contaminan** las bandas EEG: hay que marcarlos o sacarlos antes de calcular una calma. El movimiento de cabeza en VR también mete artefactos (página *Recording During Activity* de la doc).

### Cómo llegaría a la obra (más adelante, no ahora)
El `BP_BioHub` escucha OSC en **UDP 10000** con las direcciones en variables: `/muse/calm`, `/muse/heart_rate`, `/muse/sensor_active`.
1. **PC al lado:** pieeg-server o un script propio calcula la calma y la manda por OSC a la IP del Quest, como hoy con el Muse. Es lo más rápido, pero necesita un PC.
2. **Bluetooth directo en el APK:** el protocolo es una sola característica, así que es factible y no necesita PC. Pero hace falta un plugin BLE para Android en Unreal. Es más trabajo y es lo más limpio para una feria.
3. **PiEEG Cloud + Local Bridge → OSC:** el handshake pasa por la nube, así que necesita internet.

---

## 9. Preguntas para Ildar (por Discord)

1. ¿El prototipo es de **8 o de 16** canales?
2. ¿Qué **versión de firmware** tiene? ¿Hay que actualizarla?
3. Alimentación desde el Quest: ¿qué cable o adaptador exacto, cuánta corriente consume y cuánto dura?
4. ¿pieeg-server con Bluetooth **funciona en Windows**? El README dice que solo `--mock`.
5. ¿Hay un **SDK para Android o Unity** (en el repo dice "coming soon")? ¿Algo para **Unreal**?
6. ¿BodyPress **graba o exporta** (CSV) o reenvía datos (OSC)?
7. ¿La caja manda **detección de electrodo suelto** (lead-off del ADS1299) por Bluetooth? Serviría para el `sensor_active` de la obra.
8. Para este prototipo, ¿recomienda electrodos secos, con gel o con suero?
9. Desde el Quest con USB-C a USB-C no enciende y desde el USB del PC sí. ¿Qué cable o adaptador usa él para alimentarla desde el visor?
10. ¿Para qué sirve la característica `fe41` (write y read)? ¿Acepta comandos: start/stop, ganancia, prueba de impedancia?
11. **Pulso:** el XR no lo mide. La obra usa el ritmo cardíaco en la etapa del latido. ¿Se podría dedicar un canal a ECG (con un clip en la oreja) o sumar un sensor PPG a la caja?

---

## 10. Enlaces

- Doc del PiEEG XR: https://docs.pieeg.com/hardware/devices/PiEEG_XR/ (páginas: setup, connections, software, Specification, Service, FQA, examples, Application)
- Ruido y calidad de señal: https://docs.pieeg.com/hardware/signal-quality/noise-elimination/
- PiEEG Cloud: https://cloud.pieeg.com
- Repo de hardware (firmware, datasets, manual de VRChat): https://github.com/pieeg-club/PiEEG_XR_Hardware
- PiEEG Server (MIT, v0.52.0 del 2026-11-03): https://github.com/pieeg-club/PiEEG-server · https://pypi.org/project/pieeg-server/
- Local Bridge: https://github.com/pieeg-club/PiEEG-local-bridge/releases/latest
- Tutorial de Quest: https://www.pieeg.com/tutorials/run-pieeg-xr-meta-quest
- Videos: prueba rápida y calidad https://www.youtube.com/watch?v=khi54mGcJUk · en Quest https://www.youtube.com/watch?v=ycL2kZpIdvM · Face Trainer https://www.youtube.com/watch?v=g-XgVWwQzwE
- Paper: El Abbassi y Rakhmatulin, *PiEEG XR*, Preprints 2026, https://doi.org/10.20944/preprints202606.0016.v1
- Soporte: canal de Discord con Ildar · pieeg@pieeg.com
