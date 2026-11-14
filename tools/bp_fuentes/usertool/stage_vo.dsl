;; stage_vo.dsl - BP_BreathStage_SC: las VO de adentro de Entering (auditoria 2026-10-01). Solo con bContract (flujo de la Obra/runner).
;;   VO_11  (VOInstr)   fase 10 (o 11 si StageBegin llego antes: Speed alto), a ToolDelay + VOAfterTool: "Rest the sensor on your belly..."
;;   VO_11b (VOExplore) fase 11, apenas queda libre (fin de la VO anterior + VOGap): "Take a moment to explore..."
;;   VO_11h (VOHelp)    fase 11, HelpAfter s despues de VO_11b, SOLO si el rig no detecta zona (sensor fuera de la panza)
;;   VO_12  (VOReady)   fase 11, a ExploreTime - dur(VO_12) - 0,4 (nunca antes de quedar libre); la cuenta ESPERA a que termine (+0,3)
;; StageSay(Clip): Alma.SayClip si hay Alma visible (sino 2D), y VOEndAt = ahora + duracion del clip (la VO dura lo que su audio).
;; Placeholders a resolver en el turno copiando de BP_Obra_SC:ObraSay: __NOW__ (tiempo de juego), __DUR__ x (duracion de un SoundBase),
;; __ALMA__ (GetActorOfClass de BP_Alma_SC), __SAY__ alma clip (SayClip), __VISIBLE__ alma (Alma visible).
;; Variables nuevas en Default al escribir; bools sin la b.

;; ===== GRAFO: StageSay (Clip SoundBase)
(fn StageSay (Clip)
  (Variables|Default|SetVOEndAt (+ __NOW__ (__DUR__ (Variables|GetClip))))
  (bind _alma (Actor|GetActorOfClass "/Game/SoulCharger/Core/Alma/BP_Alma_SC.BP_Alma_SC_C"))
  (Utilities|IsValid _alma
    (:"Is Valid"
      (if (and (> (Class|BPAlmaSC|GetAppearT _alma) 0.5) (not (Class|BPAlmaSC|GetLeaving _alma)))
          (Class|BPAlmaSC|SayClip _alma :Clip (Variables|GetClip))
          (else (Audio|PlaySound2D (Variables|GetClip)))))
    (:"Is Not Valid"
      (Audio|PlaySound2D (Variables|GetClip)))))

;; ===== GRAFO: StepStageVO (DT float) -- en el Tick ANTES de ContractStep (para frenar la cuenta a tiempo)
(fn StepStageVO (DT)
  (bind _ph (Variables|Z-Estado|GetPhase))
  (bind _now __NOW__)
  (bind _free (>= _now (+ (Variables|Default|GetVOEndAt) (Variables|Default|GetVOGap))))
  (if (and (== _ph 10) (>= (Variables|Default|GetVOStep) 4))
      (Variables|Default|SetVOStep 0))
  (if (Variables|Default|GetContract)
      (if (and (or (== _ph 10) (== _ph 11)) (and (== (Variables|Default|GetVOStep) 0) (>= (Variables|Z-Estado|GetContractTimer) (+ (Variables|0-Contrato|GetToolDelay) (Variables|Default|GetVOAfterTool)))))
          (Variables|Default|SetVOStep 1)
          (CallFunction|StageSay :Clip (Variables|Default|GetVOInstr))
          (elif (and (== _ph 11) (and (== (Variables|Default|GetVOStep) 1) _free))
            (Variables|Default|SetVOStep 2)
            (CallFunction|StageSay :Clip (Variables|Default|GetVOExplore))
            (elif (and (== _ph 11) (and (and (== (Variables|Default|GetVOStep) 2) _free) (>= _now (+ (Variables|Default|GetVOEndAt) (Variables|Default|GetHelpAfter)))))
              (Variables|Default|SetVOStep 3)
              (if (not (Class|BPBreathRigSC|GetZone (Variables|Z-Estado|GetRig)))
                  (CallFunction|StageSay :Clip (Variables|Default|GetVOHelp)))
              (elif (and (== _ph 11) (and (and (>= (Variables|Default|GetVOStep) 2) _free) (>= (Variables|Z-Estado|GetContractTimer) (- (Variables|0-Contrato|GetExploreTime) (+ (__DUR__ (Variables|Default|GetVOReady)) 0.4)))))
                (Variables|Default|SetVOStep 4)
                (CallFunction|StageSay :Clip (Variables|Default|GetVOReady)))))))
  (if (and (Variables|Default|GetContract) (and (== _ph 11) (or (< (Variables|Default|GetVOStep) 4) (< _now (+ (Variables|Default|GetVOEndAt) 0.3)))))
      (Variables|Z-Estado|SetContractTimer (Math|Float|Min(Float) (Variables|Z-Estado|GetContractTimer) (- (Variables|0-Contrato|GetExploreTime) 0.05)))))
