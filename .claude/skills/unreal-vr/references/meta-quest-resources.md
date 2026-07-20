# Recursos oficiales de Meta para Quest + Unreal — curado para Soul Charger

Research 2026-07-20. Filtrado para **Unreal + Quest 3 standalone** (se descartó lo que es solo Unity). Ordenado por relevancia a lo que se está construyendo (hápticos de latido/respiración, sensor agarrable, UMG world-space, performance móvil).

Portales base:
- Downloads (SDKs/tools): https://developers.meta.com/horizon/downloads/
- Code samples (30 son de Unreal, empiezan con `Unreal-`): https://developers.meta.com/horizon/code-samples/
- Org de GitHub con todos los samples: https://github.com/oculus-samples

---

## 🥇 Tier 1 — aplica directo a las mecánicas actuales

### Meta XR Haptics SDK for Unreal + Haptics Studio  ⭐ el más relevante
Reemplaza el háptico plano actual (`SetHapticsByValue` freq 0 + amplitud, ver `blueprints/BP_BreathSensor_V2.md` §Hápticos) por **clips hápticos diseñados** en Haptics Studio (waveforms tipo audio: ataque/cuerpo/cola) que el SDK **reproduce y modula en runtime** (amplitud + frecuencia). Ideal para el latido (modular por BPM) y la inhalación (modular por la señal de respiración). El sample **Phanto** muestra modulación de amplitud/frecuencia con input del mando.
- Docs get-started: https://developers.meta.com/horizon/documentation/unreal/unreal-haptics-sdk-get-started/
- Descarga SDK: https://developers.meta.com/horizon/downloads/package/meta-xr-haptics-sdk-for-unreal/
- Ejemplo de uso (haptics + modulación): https://github.com/oculus-samples/Unreal-Phanto

### Performance Settings (sample Unreal) + RenderDoc (fork de Meta)
Para cerrar nitidez/rendimiento en standalone (pixel density / FFR / MSAA — ver [[quest-nitidez-antialiasing]]). El sample muestra el impacto CPU/GPU de cada setting; RenderDoc-fork es el debugger gráfico oficial para perfilar frame a frame en device (soporta Unreal).
- RenderDoc + tools: https://developers.meta.com/horizon/downloads/
- Sample "Performance Settings": en el listado Unreal de code-samples.

### Unreal-MetaXRAudioSDK — audio espacial de Meta
Espacialización + acústica de sala para Quest. Aplica a `Umbral`/`Inhale`/`Exhale`/`HeartBeat` (audio del stage) si se quiere posicionar el latido "en el pecho" o hacer el ambiente reactivo.
- https://github.com/oculus-samples/Unreal-MetaXRAudioSDK

---

## 🥈 Tier 2 — muy útil en el corto plazo

### Unreal-InteractionSDK-Sample (Meta XR Interaction SDK)
Sistema oficial de grab / poke / ray e **interacción con UI world-space**. Alternativa robusta al auto-attach por proximidad casero del sensor y a los botones de las páginas de instrucciones (UMG world-space, ver [[instructions-widget]] y `references/widgets-vr.md`).
- https://github.com/oculus-samples/Unreal-InteractionSDK-Sample
- Docs overview: https://developers.meta.com/horizon/documentation/unreal/unreal-isdk-overview/

### MetaXR plugin (UE5 Integration) + Matriz de compatibilidad
El plugin base. 🔴 **OJO puntual:** el proyecto está en **UE 5.8** (muy nuevo); Meta publica una matriz de qué versión del plugin soporta qué versión de Unreal y qué features. **Verificar que el plugin MetaXR matchee 5.8 antes de adoptar cualquiera de estos SDKs** (features nuevas suelen ir detrás de las versiones bleeding-edge de UE). Última ~81.0.0 (oct 2025).
- Matriz de compatibilidad: https://developers.meta.com/horizon/documentation/unreal/unreal-compatibility-matrix/
- Paquete GitHub: https://developers.meta.com/horizon/downloads/package/unreal-engine-5-integration-github/

---

## 🥉 Tier 3 — según hacia dónde vaya la obra

- **Unreal-Movement** — Body / Eye / Face tracking (Quest 3/Pro). Para presencia corporal o mecánicas por mirada (gaze). https://github.com/oculus-samples/Unreal-Movement
- **Unreal-PassthroughSample** + **MRUtilityKit** + **Phanto** — passthrough y entendimiento de escena (mixed reality). Hoy la obra es VR inmersivo; útil si se ancla algún momento a la sala real (inicio/salida, seguridad). https://github.com/oculus-samples/Unreal-PassthroughSample
- **Unreal-CoLocationHS** — multiplayer colocalizado (varias personas misma sala). Solo si escala a experiencia compartida. https://github.com/oculus-samples/Unreal-CoLocationHS
- **Otros tools en downloads**: Oculus ADB Drivers, Meta Horizon OS UI Set (Unity/Figma — solo referencia de diseño), Spatial SDK/Editor (framework Android nativo de MR, no Unreal).

---

## Recomendación (una línea)
Lo que mueve la aguja **ya** = **Haptics SDK + Haptics Studio** (encaja con el corazón de la obra: pulsos de latido/respiración). Segundo, **Performance sample + RenderDoc** para nitidez/rendimiento en standalone. Antes de integrar cualquiera: chequear la matriz de compatibilidad vs UE 5.8.

Nota de licencia: los samples `oculus-samples` están bajo licencia propietaria de Oculus/Meta (OK para aprender y para usar con los SDK de Meta).
