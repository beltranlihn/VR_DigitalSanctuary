# NS_LovingField1/2/3 — los 3 campos de luz de Loving (Core/VFX/)

## Purpose
El arte de los 3 Niagaras del Acto 6, pedido por Beltrán (2026-08-15): *"crea 3 niagara de hanging particle pero cámbiales el shape a una esfera. Agrega un curl noise y mapea el float de calm a la intensidad del curl noise. Los 3 niagara de distinto color para diferenciarlos"*.

## Status
🟢 **Los tres compilan sin errores ni warnings** y la calma llega al sistema **en vivo**: medido en PIE, tras escribir se lee `Calm = 0.811109`, que es el valor del LFO del [[BP_BioHub]] en ese instante. ⬜ Falta verlos en visor y afinar el look.

## Cómo están hechos
Los tres son **duplicados de `NS_VoidDust`** (el emitter `HangingParticulates`, que ya estaba probado en el proyecto), con tres cambios:

| Cambio | Detalle |
|---|---|
| **Shape → Esfera** | `ShapeLocation.Shape Primitive` = `ENiagara_LocationShapes::NewEnumerator0` (**NewEnumerator0 = Sphere**, confirmado por el `displayName` que devuelve el setter). `Sphere Radius` = **300 cm**. |
| **Curl Noise** | Módulo `/Niagara/Modules/Update/Forces/V2/CurlNoiseForce` agregado al `ParticleUpdateScript`. |
| **La calma modula la intensidad** | `Noise Strength` no es un número: es el dynamic input **`ScaleAndBiasFloat`** con `Float` = **`User.Calm`**, `Scale` = 260 y `Bias` = 60. O sea **`fuerza = Calm × 260 + 60`**. El bias es deliberado: con calma 0 el campo **sigue moviéndose apenas**, igual que el `MinFactor` de [[BP_LovingField]]. |
| **Color por sistema** | `ScaleColor.ScaleRGB` activado + `Scale RGB`: **1 = rosa** (0.85, 0.35, 0.55) · **2 = violeta** (0.55, 0.35, 0.95) · **3 = ámbar** (0.95, 0.70, 0.40). |

**El user parameter es `User.Calm`** (float, default 0.5). Lo escribe `BP_LovingField.WriteCalm` **por frame** con la calma cruda del EEG — o sea, exactamente el mapeo que pidió Beltrán, a los 60 Hz que él fijó.

Asignados a los 3 `BP_LovingField` colocados en `L_Room_Loving`, por `FieldIndex`: 0→1, 1→2, 2→3.

## 🔴🔴 Lo que costó, y que corrigió DOS cosas del proyecto
El camino no fue directo, y de ahí salieron dos correcciones que valen más que los sistemas:

1. **`bIsValid` de `GetNiagaraVariable` daba `false` para `User.Calm`, que existe.** Lee el **store de overrides del componente**, que arranca vacío. Pasa a `true` **recién después de escribir**. Toda la detección `bHasIntensity`/`bHasColor`/`bHasCalm` de [[BP_LovingField]] estaba **gateando las escrituras con un probe que siempre daba false** → nunca escribía nada. **Se quitaron los gates: ahora escribe siempre.** Un nombre inexistente sólo crea un parámetro fantasma, que es inofensivo.
2. **El prefijo `User.` NO va en el setter.** Con `"Calm"` la escritura llega; el parámetro se llama `User.Calm` en el store pero el nodo agrega el namespace solo. Esto **zanja la contradicción** que arrastraba `assets-existentes.md` — y de paso explica por qué Beltrán no veía el beam de Attracting: `BP_AimBeam` escribía `"User.BeamStart"`/`"User.BeamEnd"`, o sea **parámetros fantasma**. Corregido a `"BeamStart"`/`"BeamEnd"`.

⚠ Y el probe hay que hacerlo **con el componente ya activado**: con `bAutoActivate=false` el store ni siquiera está inicializado. Por eso `ProbeParams` se movió de `BeginPlay` a `FieldAppear`, después del `Activate`.

## TODO
- [ ] 🔴 **Visor**: cómo se lee la esfera de 3 m alrededor del usuario, si el curl noise se nota, y si el rango `Calm × 260 + 60` es el correcto. Todo eso se afina en el editor sin tocar Blueprint.
- [ ] ⚠ `niagara-quest.md`: verificar en APK que la **Scalability** del emitter no lo apague (`fx.Niagara.QualityLevel` está clampeado en Android) y medir el overdraw de 3 sistemas de sprites superpuestos.
- [ ] El `SpawnRate` sigue en el 80 heredado de `NS_VoidDust`; para una esfera de 3 m puede ser mucho o poco.

## Relacionados
- [[BP_LovingField]] (quien los escribe) · [[BP_Stage_Subclases]] §Loving · `NS_VoidDust` (el original) · `references/niagara-quest.md`
