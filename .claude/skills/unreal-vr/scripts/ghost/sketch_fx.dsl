;; sketch_fx.dsl - el dibujo aparece y se va en el cuadro de resultados con la animacion de su etapa.
;; Encargo de Beltran via Narrativa (2026-09-30). Va en BP_TBDirector_NC (/Game/NeuralCanvas/TB/).
;; Uso desde la Obra: PlaceSketch(Xf, Size) -> SketchAppear() en ResultsShow; SketchVanish() en la salida de resultados.
;;
;; Verificado en el editor (turno 2026-09-30):
;;   - BPC_TBTool_NC.SketchReveal(R): SetReveal(R) + SetTaper en cada trazo del SketchSet. SketchShow la llama con
;;     smoothstep(SketchT / CfgShowTime); SketchWait toca ShowSound con PlaySound2D(Sound, Vol), sin IsValid.
;;   - SketchArchive (al final de SketchOut) -> ArchiveOne: SetActorHiddenInGame(S, true) + saca S de StrokeHistory.
;;     Los trazos SIGUEN en SketchSet, ocultos y con Reveal 0. PlaceSketch NO los muestra: lo hace SketchAppear.
;;   - Director: 03SKETCH ShowTime/HideTime, 04AUDIO ShowSound/HideSound/SfxVol; Class|BPCTBToolNC|GetSketchSet;
;;     Utilities|Time|Set/ClearTimerbyFunctionName, GetWorldDeltaSeconds.
;; Reloj PROPIO (timer), no el Tick del director: en la Obra la celda del dibujo esta dormida durante los resultados y
;; despertar su Tick correria la logica de la etapa.
;; Variables nuevas (Z-SketchFx): FxT float · FxDir int · bFxBusy bool.
;; Interrumpir: Vanish a mitad de Appear (o al reves) sigue desde el punto actual. smoothstep es simetrico,
;; s(1-t) = 1 - s(t), asi que FxT -> 1 - FxT da el mismo Reveal (sin salto).

(fn SketchAppear ()
  (bind _self self)
  (Variables|Z-SketchFx|SetFxT (select (Variables|Z-SketchFx|GetFxBusy) (select (< (Variables|Z-SketchFx|GetFxDir) 0) (- 1.0 (Variables|Z-SketchFx|GetFxT)) (Variables|Z-SketchFx|GetFxT)) 0.0))
  (Variables|Z-SketchFx|SetFxDir 1)
  (Variables|Z-SketchFx|SetFxBusy true)
  (CallFunction|SketchFxApply _self)
  (CallFunction|SketchVis _self true)
  (Audio|PlaySound2D (Variables|04AUDIO|GetShowSound) (Variables|04AUDIO|GetSfxVol))
  (Utilities|Time|SetTimerbyFunctionName self "SketchFxTick" 0.0139 true))

(fn SketchVanish ()
  (bind _self self)
  (Variables|Z-SketchFx|SetFxT (select (Variables|Z-SketchFx|GetFxBusy) (select (> (Variables|Z-SketchFx|GetFxDir) 0) (- 1.0 (Variables|Z-SketchFx|GetFxT)) (Variables|Z-SketchFx|GetFxT)) 0.0))
  (Variables|Z-SketchFx|SetFxDir -1)
  (Variables|Z-SketchFx|SetFxBusy true)
  (CallFunction|SketchFxApply _self)
  (Audio|PlaySound2D (Variables|04AUDIO|GetHideSound) (Variables|04AUDIO|GetSfxVol))
  (Utilities|Time|SetTimerbyFunctionName self "SketchFxTick" 0.0139 true))

;; Reveal = smoothstep(FxT) al aparecer, 1 - smoothstep(FxT) al irse (como SketchShow/SketchOut).
(fn SketchFxApply ()
  (bind _t (Variables|Z-SketchFx|GetFxT))
  (bind _s (* (* _t _t) (- 3.0 (* 2.0 _t))))
  (Class|BPCTBToolNC|SketchReveal (Variables|Default|GetTBTool) (select (> (Variables|Z-SketchFx|GetFxDir) 0) _s (- 1.0 _s))))

;; Avanza con el delta del mundo (tope 0,0333 como la regla 4); al terminar: timer fuera y, si se fue, trazos ocultos.
(fn SketchFxTick ()
  (bind _self self)
  (bind _dur (Math|Float|Max(Float) 0.05 (select (> (Variables|Z-SketchFx|GetFxDir) 0) (Variables|03SKETCH|GetShowTime) (Variables|03SKETCH|GetHideTime))))
  (Variables|Z-SketchFx|SetFxT (Math|Float|Min(Float) 1.0 (+ (Variables|Z-SketchFx|GetFxT) (/ (Math|Float|Min(Float) (Utilities|Time|GetWorldDeltaSeconds) 0.0333) _dur))))
  (CallFunction|SketchFxApply _self)
  (if (>= (Variables|Z-SketchFx|GetFxT) 1.0)
    (Utilities|Time|ClearTimerbyFunctionName self "SketchFxTick")
    (Variables|Z-SketchFx|SetFxBusy false)
    (if (< (Variables|Z-SketchFx|GetFxDir) 0)
      (CallFunction|SketchVis _self false))))

;; SketchVis(On): SetActorHiddenInGame(not On) en cada trazo del SketchSet de la herramienta (como ArchiveOne).
(fn SketchVis (On)
  (for _s (Class|BPCTBToolNC|GetSketchSet (Variables|Default|GetTBTool))
    (Rendering|SetActorHiddenInGame _s (not On))))
