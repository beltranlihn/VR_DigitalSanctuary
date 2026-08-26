# Surrounding V2 — el dibujo libre integrado a L_SoulCharger (plan 2026-08-26)

> Reemplaza el flujo de `movement-surrounding.md` en lo que toca a la OBRA (el detalle
> del motor de geometría de ese doc sigue vigente). Decisiones de Beltrán, 2026-08-26:
> **sin lápiz** (se dibuja directo desde la mano hábil, que ya sostiene el sensor),
> **sin dibujar sobre la ameba** (dibujo libre en el aire), **cierre por metros lineales**,
> **sin botón** de instrucciones (una sola página), y la firma al final junto a la ameba.

## La mecánica (guión de la etapa)
1. Entramos a Surrounding. Aparecen las instrucciones (1 página) → se activa el
   **modo dibujo** y la **paleta 3×3** en la mano contraria.
2. **Práctica**: dibujar 1 metro lineal → las instrucciones terminan solas
   (`panel.Finish()`, patrón Attracting), el trazo de práctica **se borra**.
3. **Libre**: dibujar **10 metros lineales** → el dibujo se guarda (en memoria),
   **se disuelve** (fade), y la etapa cierra (`StepTimeDone`, patrón BreathRing).
4. Sigue el flujo existente: VO → **5º anillo (la carga)** → `CloseRoomNow`
   (desaparece la arquitectura) → final.
5. **La firma**: cuando la ganadora llega a `soul_pick_6`, el dibujo reaparece
   (fade-in) **a la derecha de la ameba**, reposicionado y escalado al TargetPoint
   nuevo **`TP_signature_spot`** (lo coloca Beltrán en el viewport).

## Arquitectura
- **Toda la LÓGICA en `BP_Sensor_Soul`, modo 5** (directiva de Beltrán): gatillo de la
  mano hábil (eventos `IA_Shoot_*` ya cableados), punta = el propio sensor + One-Euro,
  `ComputeCalm` (trasplantes de `BP_BrushTool`, que muere), spawn y control de la
  paleta y del canvas, conteo de metros, práctica y cierre.
- **La GEOMETRÍA sigue en `BP_DrawCanvas`** (actor mudo, spawneado por el sensor en el
  persistente): 🔴 el PMC exige transform **identidad mientras se dibuja** y el sensor
  viaja pegado a la mano — no puede ser componente suyo. Moverlo DESPUÉS de dibujar es
  legal (así se recoloca la firma).
- **`BP_BrushPalette` se reusa tal cual** (validada en visor): `AttachToHand(!bTookRight)`.
- Lo que NO se usa en V2: `BP_BrushTool`, `BP_DrawLimit`, `BP_Stage_Surrounding`
  (esqueleto viejo, queda de referencia).

## Fases
- **F0** — test de visor pendiente de la cinta PLANA (cambio 2026-08-03 sin probar) —
  se pliega a la primera pasada de visor de Beltrán con todo integrado.
- **F1** — modo 5 del sensor: input, punta+One-Euro, calma, spawn canvas+paleta,
  dibujo end-to-end con `DebugStartRoom=5`.
- **F2** — `TotalArc` + `ResetCanvas()` en el canvas · director: `ArmDraw()` (else de
  `ArmBeam`) + `TickDrawPractice` (1 m → `Finish()`) · borrar práctica en `StartStepTime` ·
  panel de `L_Surrounding_SC` a UNA página (`StartIndex=EndIndex=9`) · sacar el botón.
- **F3** — cierre por `TargetMeters` (10 m) → fade del dibujo (param en la familia
  `M_Brush_*` vía MPC, sin MIDs) + `StepTimeDone` · `StepTimes[5]=300` (cortafuegos).
- **F4** — la firma: `ShowSignature()` (mover+escalar el canvas a `TP_signature_spot`,
  fade-in) disparada al `arrived` de `soul_pick_6`.
- **F5** — polish: materiales 4.4 de la paleta, háptica/audio por trazo, persistencia
  a disco de la firma (los arrays `Pt*` ya son el formato — decisión pendiente).

## Decisiones tomadas con Beltrán (2026-08-26)
- Botón de instrucciones de Surrounding: **se elimina** (cierre por mecánica).
- Firma: **vive la corrida** (se recrea al final y muere con el reload); persistir a
  disco queda para F5.
- Paleta 3×3 (colores/grosores/pinceles): **queda tal cual**.

## Estado (2026-08-26, noche)
✅ **F1–F4 construidas y verificadas con el ROBOT dibujando de verdad** (rutina 3 de
`BP_Robot`, 2 corridas limpias): práctica de 1 m cierra las instrucciones por mecánica,
10 m cierran la etapa (~20 s), disolución, 5º anillo, cierre de sala, y la firma
reaparece junto al alma **con el dibujo real** y sobrevive al paso final. Cero
`Accessed None`. Tres bugs cazados y arreglados en el camino (detalle en el tracker
de `BP_Sensor_Soul`). ⬜ Pendiente: **visor** (look del trazo = F0, paleta en mano,
sensación) y F5 (materiales 4.4, háptica/audio, persistencia a disco).

## Riesgos anotados
- La cinta plana sin test de visor (F0) — si se ve mal, las 2 cartas están en el
  tracker de `BP_DrawCanvas` (§RETOMAR ACÁ).
- Editar `M_Brush_Light` por MCP NO recompila el shader (gotcha §221) — forzar con un
  cambio real de propiedad.
- El fade por MPC debe definirse en el material ANTES del cierre (declarado ≠ aplicado).
- Autotest: la práctica y los 10 m no se pueden "dibujar" solos → el cortafuegos
  `StepTimes[5]` y el `Poke` del panel cubren el ciclo sin manos.
