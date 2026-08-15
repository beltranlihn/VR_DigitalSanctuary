# BP_Credits + WBP_Credits — los créditos del cierre (Core/UI/)

## Purpose
El último plano de la obra: *"negro · VO 30 gracias · SCredits + **créditos frente a nosotros** · reload"*. Cierra el ciclo antes de que la obra vuelva a empezar para el próximo usuario.

## Status
🟢 **Verificado por log** (2026-08-15): nace oculto, el final lo muestra en su momento (`CREDITOS: creditos a la vista` justo después de `FINAL: gracias y creditos`) y muere con el reload. Cero `Accessed None`.
⬜ Falta visor: **la distancia es la incógnita** (ver abajo) y los textos son placeholder — los escribe Beltrán.

## 🔴 Por qué están a 20 cm de la cara
Los créditos salen **después del fundido a negro**, y ese negro es `BP_FadeSphere`: una esfera **pegada a la cámara**, escala 0.6 sobre la esfera del motor → **radio 30 cm**. Todo lo que esté más lejos de 30 cm **queda tapado por el negro**.
👉 Por eso el panel se **attachea a la cámara** a `Distance` = **20 cm**, adentro de la esfera. Es la misma vecindad en la que ya vive [[BP_SoulHUD]] (verificado a 30 cm), así que no es un invento: es la distancia de trabajo de la UI física de esta obra.
⚠ 20 cm es **cerca**. Si en visor incomoda, hay dos palancas y ninguna toca el grafo: subir `Distance` (hasta que la esfera lo tape) o **agrandar la esfera del fade**. Está anotado como la primera pregunta del test.

## Anatomía
```
BP_Credits (actor en L_Persistent)
└─ Panel  WidgetComponent · WBP_Credits · Space=World · DrawSize 760×520
          escala 0.028 → 21 cm de ancho · blendMode Transparent
```
`ShowCredits()` → `CreditsAttach` (busca el pawn, se cuelga de la cámara, se pone en `+X · Distance` con yaw 180) y se deja de ocultar. `HideCredits()` lo vuelve a esconder.
Lo llama **`BP_Finale.FinaleCredits` → `ShowFinalCredits`**, en el mismo latido que el VO 30 y el SFX de créditos.

| Variable | Default | Rol |
|---|---|---|
| `Distance` | 20 cm | A qué distancia de los ojos. **La palanca del visor.** |

## WBP_Credits — el texto es de Beltrán
`Root`(CanvasPanel) → `Lines`(VerticalBox) → `Title` · `Sub` · `Gap1` · `L1` · `L2` · `Gap2` · `Thanks`, todos centrados, blancos, con `letterSpacing` 120.
Los textos actuales son **placeholder en inglés** (SOUL CHARGER / a work of immersive healing / created by Alma Digital Studio / your soul now lives in the constellation / thank you for breathing with us). **Se editan en el widget, sin tocar Blueprint** — que es justo lo que se quiere para un texto autoral.
Los `Gap` son TextBlocks vacíos con alpha 0: separadores baratos, sin agregar Spacers.

## TODO
- [ ] 🔴 **Visor**: la distancia de 20 cm, si el texto se lee, y si conviene agrandar la esfera del fade en vez de acercar el panel.
- [ ] Los textos reales (Beltrán).
- [ ] Aparición gradual línea por línea, como el gráfico de resultados — hoy aparecen todas juntas.

## Relacionados
- [[BP_Finale]] (`FinaleCredits` → `ShowFinalCredits`) · `BP_FadeSphere` (**el que define la distancia máxima**) · [[BP_SoulHUD]] (el otro panel pegado a la cámara) · [[BP_ResultsPanel]] (el mismo patrón de widget world-space) · `references/widgets-vr.md`
