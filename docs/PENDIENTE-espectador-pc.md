# 🖥️ Espectador en PC — decidido, POSPUESTO al final de la obra

> Investigado y decidido el **2026-08-21**. Decisión de Beltrán: **"lo haría al final, cuando ya tengamos la experiencia armada"**.
> Este archivo existe para que al retomarlo no haya que volver a investigar nada.

## Qué se quería
Ver en tiempo real, en una PC de la misma red WiFi, lo que está haciendo el usuario con el visor — **con interfaz propia**, sin depender del cast de Meta Quest Developer Hub. El receptor sería un empaquetado de Windows del mismo proyecto.

---

## 🔴 Por qué NO se hace mandando video desde el Quest (verificado en el motor, no asumido)

**UE 5.8 no tiene encoder de video para Android.** Los backends de codec que trae son:

| Plugin | Qué es | Plataformas |
|---|---|---|
| `NVCodecs` | NVENC (NVIDIA) | Win64, Linux |
| `AMFCodecs` | AMD | Windows |
| `WMFCodecs` | Windows Media Foundation | Windows |
| `VTCodecs` | VideoToolbox | Apple |
| `LibVpxCodecs` | VP8/VP9 **por software** | — |

`Engine/Plugins/Experimental/AVCodecs/AVCodecsCore` trae el framework y las *configuraciones* (H264/H265/VP8/VP9/AV1) pero **ningún backend de Android**: `grep MediaCodec` sobre todo el plugin da **cero**. O sea que en Quest la única vía sería **VP8 por software en la CPU**.

⚠ **Ojo con el falso positivo:** `PixelStreaming2.uplugin` **sí lista `Android`** en su `PlatformAllowList` (a diferencia del `PixelStreaming` v1, que es Win64/Linux/Mac). Eso significa que el módulo **compila** en Android, no que haya con qué codificar. No confundir una cosa con la otra.

Y hay un segundo costo, independiente del encoder: **una cámara extra a 1920×1080 es un render de escena COMPLETO adicional**, sobre una obra que ya es fill-rate bound a 72 Hz.

👉 **Por eso existe el cast de Meta**: usa el encoder de hardware del sistema, que Unreal no expone.

---

## ✅ La arquitectura elegida: transmitir ESTADO, no píxeles

El receptor de Windows es **este mismo proyecto empaquetado para Win64**, corriendo en modo espectador. El Quest le manda un paquete chico por UDP.

**Lo que hace viable esta obra en particular:** es un **secuenciador lineal** y ya existe un valor canónico de "en qué punto vamos" — `Room` y `Sub` de [`BP_Director_Story`](../.claude/skills/unreal-vr/blueprints/BP_Director_Story.md). Entonces **el mismo guión corre de los dos lados** y basta con sincronizar el índice:

| Se manda | Por qué |
|---|---|
| Pose de cabeza + las dos manos | Es lo impredecible, lo que de verdad hace el usuario |
| `Room` / `Sub` | La señal de sincronía: los directores corren localmente y se mantienen en paso |
| Elecciones del usuario (alma, malla, color) | No se deducen del guión |
| Lo que dependa del gesto continuo | El dibujo de Surrounding, las burbujas de Attracting, la ameba cuando se lleva en la mano |

🔴 **La gran ventaja de este diseño:** las mecánicas nuevas que sean **parte del guión vienen gratis**, porque el mismo director las ejecuta en las dos máquinas. Solo hay que replicar explícitamente lo que sale del gesto del usuario.

**Transporte:** ya existe en el proyecto — `BP_OSCReceiver` y el BioHub ya hacen OSC sobre UDP.

**Empezar por lo mínimo:** cabeza, manos, paso del guión y alma elegida. Eso ya da el ~80% del valor y se prueba en una tarde.

---

## ⚖️ Los límites, dichos claro
- ✅ **Sirve** para observar visitantes y para grabar documentación: imagen a calidad de PC sin compresión, costo ~0 en el visor, y **cámara libre** (no quedás pegado a la nuca del usuario).
- ❌ **NO sirve para depurar lo que el usuario VE.** Es una **reconstrucción**, no un espejo: la PC renderiza con otro renderer y otra config. Un artefacto visual del visor no va a aparecer ahí.
- 💸 **Costo permanente:** cada mecánica que dependa del gesto hay que sumarla al paquete, o el espectador se desincroniza. Por eso se pospone: **conviene pagarlo cuando el guión deje de moverse**, no mientras se agregan mecánicas a diario.

## Si algún día hace falta la imagen LITERAL del visor
No pasa por Unreal: **`adb` sobre WiFi con captura de pantalla** (tipo `scrcpy`) usa el encoder de hardware del sistema — el mismo que usa el cast de Meta, costo bajo — y permite construir la interfaz propia alrededor de esa ventana, sin el Developer Hub.
